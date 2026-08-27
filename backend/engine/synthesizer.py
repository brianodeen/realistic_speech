"""
Master Synthesis Pipeline for the Universal Phonetic Speech Engine.
Coordinates Cursive Coarticulation, Continuous Formant Trajectories,
Glottal Excitation, Bioacoustic creature modulation, and 44.1kHz WAV encoding.
"""

import io
import wave
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from scipy import signal

from .schema import ConlangScript, Syllable, PhonemeSegment
from .articulatory import VOWEL_TABLE, CONSONANT_TABLE, CREATURE_TABLE
from .prosody import generate_f0_contour, generate_volume_envelope
from .glottal import generate_glottal_source
from .tract import compute_continuous_formant_trajectories, apply_continuous_formant_filter
from .bioacoustics import (
    synthesize_feline_purr,
    synthesize_feline_growl,
    synthesize_feline_hiss,
    synthesize_canine_snarl,
    synthesize_canine_bark,
    synthesize_canine_whine,
)


SAMPLE_RATE = 44100


def synthesize_script(script: ConlangScript, sample_rate: int = SAMPLE_RATE) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Main entry point: Synthesizes a complete ConlangScript using continuous
    cursive coarticulation, time-varying formant trajectories, and bioacoustic modulation.
    """
    if not script.utterance:
        return np.zeros(int(0.2 * sample_rate), dtype=np.float32), {"duration_sec": 0.2, "syllables": []}

    speaker = script.speaker
    cursive_flow = getattr(speaker, "cursive_flow", 0.85)
    acoustic_warmth = getattr(speaker, "acoustic_warmth", 0.40)
    fleshiness = getattr(speaker, "fleshiness", 0.70)

    # 1. Flatten utterance into a continuous phoneme timeline
    phoneme_sequence = []
    syllable_telemetry = []
    current_time_ms = 0.0

    # Inter-syllable boundary gap: 0ms if cursive_flow > 0.5 (legato), else subtle 15ms pause
    inter_syl_gap_ms = 0.0 if cursive_flow >= 0.5 else (1.0 - cursive_flow) * 30.0
    inter_syl_gap_samples = int((inter_syl_gap_ms / 1000.0) * sample_rate)

    for s_idx, syl in enumerate(script.utterance):
        syl_start_ms = current_time_ms
        syl_phonemes = syl.phonemes or [PhonemeSegment(symbol="a", type="vowel", duration_ms=200.0)]
        syl_samples = 0

        for p in syl_phonemes:
            n_samp = max(1, int((p.duration_ms / 1000.0) * sample_rate))
            phoneme_sequence.append({
                "symbol": p.symbol.lower().strip(),
                "num_samples": n_samp,
                "phoneme_obj": p,
                "syllable_obj": syl,
                "s_idx": s_idx,
            })
            syl_samples += n_samp
            current_time_ms += (n_samp / sample_rate) * 1000.0

        # Record telemetry
        syl_dur_ms = (syl_samples / sample_rate) * 1000.0
        syllable_telemetry.append({
            "syllable": syl.label or f"syl_{s_idx + 1}",
            "start_ms": syl_start_ms,
            "duration_ms": syl_dur_ms,
            "tone": syl.prosody.chao_tone or "custom",
            "phonation": syl.prosody.phonation or "modal",
        })

        # Add inter-syllable gap if non-legato
        if inter_syl_gap_samples > 0 and s_idx < len(script.utterance) - 1:
            phoneme_sequence.append({
                "symbol": "pause",
                "num_samples": inter_syl_gap_samples,
                "phoneme_obj": PhonemeSegment(symbol="pause", type="pause", duration_ms=inter_syl_gap_ms),
                "syllable_obj": syl,
                "s_idx": s_idx,
            })
            current_time_ms += inter_syl_gap_ms

    total_samples = sum(p["num_samples"] for p in phoneme_sequence)
    if total_samples <= 0:
        return np.zeros(int(0.2 * sample_rate), dtype=np.float32), {"duration_sec": 0.2, "syllables": []}

    # 2. Compute Unified Continuous F0 Pitch Trajectory Across the Utterance
    full_f0_curve = np.full(total_samples, speaker.base_pitch_hz, dtype=np.float32)
    full_vol_envelope = np.ones(total_samples, dtype=np.float32)

    # Populate per-syllable F0 and Volume Curves
    curr_idx = 0
    for s_idx, syl in enumerate(script.utterance):
        # Calculate sample length for this syllable
        syl_segs = [p for p in phoneme_sequence if p["s_idx"] == s_idx and p["symbol"] != "pause"]
        syl_n_samp = sum(p["num_samples"] for p in syl_segs)
        if syl_n_samp <= 0:
            continue

        syl_f0 = generate_f0_contour(
            duration_samples=syl_n_samp,
            sample_rate=sample_rate,
            base_f0=speaker.base_pitch_hz,
            pitch_range_semitones=speaker.pitch_range_semitones,
            chao_tone=syl.prosody.chao_tone,
            pitch_curve=syl.prosody.pitch_curve,
            vibrato_rate_hz=syl.prosody.vibrato_rate_hz or 0.0,
            vibrato_depth_semitones=syl.prosody.vibrato_depth_semitones or 0.0,
        )

        syl_vol = generate_volume_envelope(
            duration_samples=syl_n_samp,
            sample_rate=sample_rate,
            volume_envelope_pts=syl.prosody.volume_envelope,
            default_volume_db=speaker.default_volume_db,
        )

        end_idx = min(total_samples, curr_idx + syl_n_samp)
        actual_len = end_idx - curr_idx
        full_f0_curve[curr_idx:end_idx] = syl_f0[:actual_len]
        full_vol_envelope[curr_idx:end_idx] = syl_vol[:actual_len]

        curr_idx += actual_len
        # Skip pause if any
        if inter_syl_gap_samples > 0:
            curr_idx += inter_syl_gap_samples

    # Smooth F0 boundary transitions (cursive pitch gliding between syllables)
    if cursive_flow > 0.0:
        win_size = max(3, int(0.025 * sample_rate * cursive_flow))
        if win_size % 2 == 0:
            win_size += 1
        # Gentle box/hanning smoothing of pitch contour
        b_smooth = np.hanning(win_size) / np.sum(np.hanning(win_size))
        full_f0_curve = signal.convolve(full_f0_curve, b_smooth, mode="same")

    # 3. Generate Continuous Formant Matrix (F1-F5) with Cursive S-Curve Transitions
    formant_matrix, bw_matrix, nasal_env = compute_continuous_formant_trajectories(
        phoneme_sequence=phoneme_sequence,
        sample_rate=sample_rate,
        vocal_tract_scale=speaker.vocal_tract_scale,
        cursive_blend_ratio=cursive_flow,
        fleshiness=fleshiness,
    )

    # 4. Generate Continuous Glottal Source Waveform (Preserves Continuous Phase!)
    # Determine dominant phonation across syllables
    dominant_phonation = script.utterance[0].prosody.phonation or "modal"
    raw_glottal_source = generate_glottal_source(
        f0_curve=full_f0_curve,
        sample_rate=sample_rate,
        phonation=dominant_phonation,
        breathiness=speaker.breathiness,
        vocal_fry=speaker.vocal_fry,
        growl_roughness=speaker.growl_roughness,
        fleshiness=fleshiness,
    )

    # 5. Composite Multi-Track Excitation (Injects unvoiced bursts, clicks, frication, and creature modulations)
    composite_excitation = np.copy(raw_glottal_source)
    curr_samp = 0

    for seg in phoneme_sequence:
        sym = seg["symbol"]
        n_samp = seg["num_samples"]
        p_obj = seg["phoneme_obj"]
        s_obj = seg["syllable_obj"]
        seg_end = min(total_samples, curr_samp + n_samp)
        actual_dur = seg_end - curr_samp

        # --- A. Clicks ---
        if "click" in sym or (p_obj.manner == "click"):
            click_info = CONSONANT_TABLE.get(sym, CONSONANT_TABLE["click_alveolar"])
            peak_hz = click_info.get("click_peak_hz", 2200)
            click_samples = min(actual_dur, int((click_info.get("click_duration_ms", 12) / 1000.0) * sample_rate))

            impulse = np.random.randn(click_samples) * np.linspace(1.0, 0.0, click_samples)
            b, a = signal.butter(2, [max(100.0, peak_hz - 500) / (sample_rate / 2), min(sample_rate / 2 - 100, peak_hz + 800) / (sample_rate / 2)], btype="band")
            click_res = signal.lfilter(b, a, impulse)
            # Suppress glottal source during click suction and inject click burst
            composite_excitation[curr_samp:curr_samp + click_samples] = click_res * 2.0

        # --- B. Ejectives & Plosives ---
        elif "ejective" in sym or (p_obj.manner in ["ejective", "plosive"]):
            c_info = CONSONANT_TABLE.get(sym, {})
            burst_hz = c_info.get("burst_freq", 2200)
            burst_dur = min(actual_dur, int((c_info.get("burst_duration_ms", 16) / 1000.0) * sample_rate))
            is_voiced = c_info.get("voiced", False)

            if burst_hz > 0 and burst_dur > 0:
                burst_noise = np.random.randn(burst_dur) * np.linspace(1.0, 0.0, burst_dur)
                b, a = signal.butter(2, [max(80.0, burst_hz - 400) / (sample_rate / 2), min(sample_rate / 2 - 100, burst_hz + 800) / (sample_rate / 2)], btype="band")
                burst_filtered = signal.lfilter(b, a, burst_noise) * 1.4

                if not is_voiced:
                    # Silence closure then burst
                    composite_excitation[curr_samp:seg_end] *= 0.05
                    composite_excitation[curr_samp:curr_samp + burst_dur] += burst_filtered
                else:
                    composite_excitation[curr_samp:curr_samp + burst_dur] += burst_filtered * 0.7

        # --- C. Fricatives ---
        elif p_obj.manner == "fricative" or (sym in CONSONANT_TABLE and CONSONANT_TABLE[sym].get("manner") == "fricative"):
            c_info = CONSONANT_TABLE[sym]
            noise_center = c_info.get("noise_center", 3800)
            noise_bw = c_info.get("noise_bandwidth", 2200)
            is_voiced = c_info.get("voiced", False)

            noise = np.random.randn(actual_dur)
            b, a = signal.butter(2, [max(80.0, noise_center - noise_bw / 2) / (sample_rate / 2), min(sample_rate / 2 - 100, noise_center + noise_bw / 2) / (sample_rate / 2)], btype="band")
            fric_noise = signal.lfilter(b, a, noise) * 0.75

            if not is_voiced:
                composite_excitation[curr_samp:seg_end] = fric_noise
            else:
                composite_excitation[curr_samp:seg_end] = composite_excitation[curr_samp:seg_end] * 0.4 + fric_noise * 0.6

        # --- D. Creature Vocalizations (Seamlessly Layered) ---
        elif p_obj.type == "creature" or sym in CREATURE_TABLE:
            cat = p_obj.category or sym
            if cat == "feline_purr" or sym == "feline_purr":
                purr_audio = synthesize_feline_purr(actual_dur, sample_rate, rate_hz=p_obj.rate_hz or 24.5, depth=p_obj.intensity or 0.85)
                composite_excitation[curr_samp:seg_end] = composite_excitation[curr_samp:seg_end] * 0.3 + purr_audio * 0.85
            elif cat == "feline_growl" or sym == "feline_growl":
                base_f0 = float(np.mean(full_f0_curve[curr_samp:seg_end]))
                growl_audio = synthesize_feline_growl(actual_dur, sample_rate, base_f0=base_f0, intensity=p_obj.intensity or 0.85, subharmonic_depth=p_obj.subharmonic_depth or 0.75)
                composite_excitation[curr_samp:seg_end] = composite_excitation[curr_samp:seg_end] * 0.25 + growl_audio * 0.90
            elif cat == "feline_hiss" or sym == "feline_hiss":
                hiss_audio = synthesize_feline_hiss(actual_dur, sample_rate, intensity=p_obj.intensity or 0.90)
                composite_excitation[curr_samp:seg_end] = hiss_audio
            elif cat == "canine_snarl" or sym == "canine_snarl":
                base_f0 = float(np.mean(full_f0_curve[curr_samp:seg_end]))
                snarl_audio = synthesize_canine_snarl(actual_dur, sample_rate, base_f0=base_f0, flutter_hz=p_obj.rate_hz or 48.0, roughness=p_obj.intensity or 0.85)
                composite_excitation[curr_samp:seg_end] = composite_excitation[curr_samp:seg_end] * 0.3 + snarl_audio * 0.85
            elif cat == "canine_bark" or sym == "canine_bark":
                base_f0 = float(np.mean(full_f0_curve[curr_samp:seg_end]))
                bark_audio = synthesize_canine_bark(actual_dur, sample_rate, base_f0=base_f0)
                composite_excitation[curr_samp:seg_end] = bark_audio
            elif cat == "canine_whine" or sym == "canine_whine":
                base_f0 = float(np.mean(full_f0_curve[curr_samp:seg_end]))
                whine_audio = synthesize_canine_whine(actual_dur, sample_rate, base_f0=base_f0)
                composite_excitation[curr_samp:seg_end] = whine_audio

        # --- E. Glottal Stop (/ʔ/) with Vocal Snap Transient (Section 4.2) ---
        elif sym in ["glottal_stop", "ʔ", "q_glottal"]:
            # 1. Zero-energy occlusion
            composite_excitation[curr_samp:seg_end] *= 0.0
            
            # 2. Vocal snap transient explosion at release moment (subglottal pressure burst)
            snap_len = min(int(0.008 * sample_rate), actual_dur)
            if snap_len > 0:
                t_snap = np.linspace(0.0, 1.0, snap_len)
                # Asymmetric pressure spike: sharp rise at t=0, rapid exponential decay
                snap_impulse = np.exp(-t_snap * 18.0) * np.sin(2.0 * np.pi * 180.0 * (t_snap * snap_len / sample_rate))
                composite_excitation[curr_samp:curr_samp + snap_len] += snap_impulse * 1.6

        curr_samp += actual_dur

    # 6. Apply Continuous Formant Filter with Smooth State Memory & Acoustic Warmth
    speech_waveform = apply_continuous_formant_filter(
        excitation_audio=composite_excitation,
        formant_matrix=formant_matrix,
        bw_matrix=bw_matrix,
        nasal_envelope=nasal_env,
        sample_rate=sample_rate,
        warmth=acoustic_warmth,
        fleshiness=fleshiness,
    )

    # 7. Apply Dynamic Volume Envelope
    modulated_audio = speech_waveform * full_vol_envelope

    # 8. Apply Global Purr Gating if speaker purr_depth > 0
    if speaker.purr_depth > 0.0:
        t = np.arange(len(modulated_audio)) / float(sample_rate)
        purr_gate = 0.5 * (1.0 - np.cos(2.0 * np.pi * 24.5 * t))
        modulated_audio *= (1.0 - speaker.purr_depth + speaker.purr_depth * purr_gate)

    # 9. Master Normalization (-1dB peak headroom)
    max_peak = np.max(np.abs(modulated_audio)) + 1e-6
    target_peak = 0.89  # -1 dBFS
    if max_peak > 0.01:
        normalized_audio = (modulated_audio / max_peak) * target_peak
    else:
        normalized_audio = modulated_audio

    telemetry = {
        "duration_sec": float(len(normalized_audio) / sample_rate),
        "sample_rate": sample_rate,
        "syllables": syllable_telemetry,
    }

    return normalized_audio.astype(np.float32), telemetry


def audio_to_wav_bytes(audio_data: np.ndarray, sample_rate: int = SAMPLE_RATE) -> bytes:
    """Converts float32 numpy audio array to 16-bit PCM WAV byte stream."""
    audio_int16 = np.clip(audio_data * 32767.0, -32768.0, 32767.0).astype(np.int16)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)       # Mono
        wav_file.setsampwidth(2)       # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_int16.tobytes())
    return buffer.getvalue()
