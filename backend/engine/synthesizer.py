"""
Master Synthesis Pipeline for the Universal Phonetic Speech Engine.
Coordinates schema parsing, prosody spline generation, glottal excitation,
bioacoustic module synthesis, time-varying formant filtering, and 44.1kHz WAV encoding.
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
from .tract import apply_formant_cascade
from .bioacoustics import (
    synthesize_feline_purr,
    synthesize_feline_growl,
    synthesize_feline_hiss,
    synthesize_canine_snarl,
    synthesize_canine_bark,
    synthesize_canine_whine,
)


SAMPLE_RATE = 44100


def synthesize_phoneme_segment(
    phoneme: PhonemeSegment,
    f0_segment: np.ndarray,
    sample_rate: int,
    vocal_tract_scale: float,
    global_breathiness: float,
    global_vocal_fry: float,
    global_growl_roughness: float,
    syllable_phonation: str,
) -> np.ndarray:
    """
    Synthesizes audio for a single phoneme or creature segment.
    """
    sym = phoneme.symbol.lower().strip()
    duration_samples = max(1, int((phoneme.duration_ms / 1000.0) * sample_rate))

    # 1. Creature Vocalizations
    if phoneme.type == "creature" or sym in CREATURE_TABLE:
        category = phoneme.category or sym
        if category == "feline_purr" or sym == "feline_purr":
            rate = phoneme.rate_hz or 24.5
            depth = phoneme.intensity or 0.85
            return synthesize_feline_purr(duration_samples, sample_rate, rate_hz=rate, depth=depth)
        elif category == "feline_growl" or sym == "feline_growl":
            base_f0 = float(np.mean(f0_segment)) if len(f0_segment) > 0 else 110.0
            return synthesize_feline_growl(
                duration_samples, sample_rate, base_f0=base_f0,
                intensity=phoneme.intensity or 0.85,
                subharmonic_depth=phoneme.subharmonic_depth or 0.75
            )
        elif category == "feline_hiss" or sym == "feline_hiss":
            return synthesize_feline_hiss(duration_samples, sample_rate, intensity=phoneme.intensity or 0.9)
        elif category == "canine_snarl" or sym == "canine_snarl":
            base_f0 = float(np.mean(f0_segment)) if len(f0_segment) > 0 else 130.0
            return synthesize_canine_snarl(
                duration_samples, sample_rate, base_f0=base_f0,
                flutter_hz=phoneme.rate_hz or 48.0, roughness=phoneme.intensity or 0.85
            )
        elif category == "canine_bark" or sym == "canine_bark":
            base_f0 = float(np.mean(f0_segment)) if len(f0_segment) > 0 else 240.0
            return synthesize_canine_bark(duration_samples, sample_rate, base_f0=base_f0)
        elif category == "canine_whine" or sym == "canine_whine":
            base_f0 = float(np.mean(f0_segment)) if len(f0_segment) > 0 else 1400.0
            return synthesize_canine_whine(duration_samples, sample_rate, base_f0=base_f0)

    # 2. Clicks (Non-pulmonic)
    if "click" in sym or (phoneme.manner == "click"):
        click_info = CONSONANT_TABLE.get(sym, CONSONANT_TABLE["click_alveolar"])
        peak_hz = click_info.get("click_peak_hz", 2000)
        click_samples = min(duration_samples, int((click_info.get("click_duration_ms", 12) / 1000.0) * sample_rate))
        
        # Suction impulse + resonance
        impulse = np.zeros(duration_samples, dtype=np.float32)
        noise_burst = np.random.randn(click_samples) * np.linspace(1.0, 0.0, click_samples)
        
        # Bandpass filter around click resonant cavity
        nyquist = sample_rate / 2.0
        low_f = max(100.0, peak_hz - 600.0) / nyquist
        high_f = min(nyquist - 200.0, peak_hz + 800.0) / nyquist
        b, a = signal.butter(2, [low_f, high_f], btype="band")
        click_filtered = signal.lfilter(b, a, noise_burst)
        impulse[:click_samples] = click_filtered
        return impulse.astype(np.float32)

    # 3. Ejectives
    if "ejective" in sym or (phoneme.manner == "ejective"):
        burst_info = CONSONANT_TABLE.get(sym, CONSONANT_TABLE["ejective_k"])
        burst_hz = burst_info.get("burst_freq", 2500)
        burst_dur = int((burst_info.get("burst_duration_ms", 20) / 1000.0) * sample_rate)
        
        audio = np.zeros(duration_samples, dtype=np.float32)
        burst = np.random.randn(min(burst_dur, duration_samples)) * np.linspace(1.0, 0.0, min(burst_dur, duration_samples))
        
        # Resonate burst
        b, a = signal.butter(2, [max(100.0, burst_hz - 500) / (sample_rate / 2), min(sample_rate / 2 - 100, burst_hz + 1000) / (sample_rate / 2)], btype="band")
        burst_res = signal.lfilter(b, a, burst)
        audio[:len(burst_res)] = burst_res * 1.5
        # The remainder is glottal closure (silence)
        return audio

    # 4. Consonants (Plosives, Fricatives, Nasals, Trills)
    if sym in CONSONANT_TABLE:
        c_info = CONSONANT_TABLE[sym]
        manner = c_info.get("manner")
        voiced = c_info.get("voiced", False)
        
        # Fricatives
        if manner == "fricative":
            noise_center = c_info.get("noise_center", 3500)
            noise_bw = c_info.get("noise_bandwidth", 2000)
            noise = np.random.randn(duration_samples)
            
            nyquist = sample_rate / 2.0
            low_f = max(80.0, noise_center - noise_bw / 2) / nyquist
            high_f = min(nyquist - 100.0, noise_center + noise_bw / 2) / nyquist
            b, a = signal.butter(2, [low_f, high_f], btype="band")
            fric_noise = signal.lfilter(b, a, noise) * 0.6
            
            if voiced:
                # Add voiced glottal bar
                glottal = generate_glottal_source(
                    f0_segment, sample_rate, phonation=syllable_phonation,
                    breathiness=global_breathiness, vocal_fry=global_vocal_fry,
                    growl_roughness=global_growl_roughness
                )
                formants = c_info.get("formants", [300, 1500, 2500, 3500, 4200])
                bws = [80, 120, 160, 200, 250]
                voiced_bar = apply_formant_cascade(glottal, formants, bws, sample_rate, vocal_tract_scale)
                return (fric_noise * 0.6 + voiced_bar * 0.4).astype(np.float32)
            else:
                return fric_noise.astype(np.float32)

        # Plosives
        elif manner == "plosive":
            burst_freq = c_info.get("burst_freq", 2000)
            burst_samples = min(duration_samples, int((c_info.get("burst_duration_ms", 15) / 1000.0) * sample_rate))
            audio = np.zeros(duration_samples, dtype=np.float32)
            
            if burst_freq > 0 and burst_samples > 0:
                burst_noise = np.random.randn(burst_samples) * np.linspace(1.0, 0.0, burst_samples)
                b, a = signal.butter(2, [max(80.0, burst_freq - 400) / (sample_rate / 2), min(sample_rate / 2 - 100, burst_freq + 800) / (sample_rate / 2)], btype="band")
                audio[:burst_samples] = signal.lfilter(b, a, burst_noise) * 0.9

            if voiced:
                glottal = generate_glottal_source(
                    f0_segment, sample_rate, phonation="modal",
                    breathiness=0.0, vocal_fry=0.0, growl_roughness=0.0
                )
                # Low voice bar (< 250Hz)
                b_vb, a_vb = signal.butter(2, min(250.0 / (sample_rate / 2), 0.9), btype="low")
                vbar = signal.lfilter(b_vb, a_vb, glottal) * 0.5
                audio += vbar[:duration_samples]

            return audio.astype(np.float32)

        # Nasals & Trills
        elif manner in ["nasal", "approximant", "tap", "trill"]:
            glottal = generate_glottal_source(
                f0_segment, sample_rate, phonation=syllable_phonation,
                breathiness=global_breathiness, vocal_fry=global_vocal_fry,
                growl_roughness=global_growl_roughness
            )
            formants = c_info.get("formants", [300, 1400, 2400, 3400, 4200])
            bws = c_info.get("bandwidths", [90, 140, 200, 250, 300])
            filtered = apply_formant_cascade(
                glottal, formants, bws, sample_rate, vocal_tract_scale,
                nasal=(manner == "nasal")
            )
            if manner == "trill":
                t = np.arange(duration_samples) / float(sample_rate)
                trill_mod = 0.5 * (1.0 + np.sin(2.0 * np.pi * 26.0 * t))
                filtered = filtered * (0.2 + 0.8 * trill_mod)
            return filtered.astype(np.float32)

    # 5. Vowels (Standard & Conlang Resonances)
    v_info = VOWEL_TABLE.get(sym, VOWEL_TABLE["a"])
    formants = v_info["formants"]
    bws = v_info["bandwidths"]
    is_nasal = v_info.get("nasal", False) or phoneme.nasal

    # Generate glottal source driven by exact syllable F0 curve
    glottal_source = generate_glottal_source(
        f0_segment, sample_rate, phonation=syllable_phonation,
        breathiness=global_breathiness, vocal_fry=global_vocal_fry,
        growl_roughness=global_growl_roughness
    )

    # Filter through vocal tract formant cascade
    vowel_audio = apply_formant_cascade(
        glottal_source, formants, bws, sample_rate,
        vocal_tract_scale=vocal_tract_scale, nasal=is_nasal
    )
    return vowel_audio.astype(np.float32)


def synthesize_syllable(
    syllable: Syllable,
    speaker: Any,
    sample_rate: int = SAMPLE_RATE,
) -> np.ndarray:
    """
    Synthesizes a single syllable by sequencing phonemes and applying prosody.
    """
    if not syllable.phonemes:
        return np.zeros(int(0.1 * sample_rate), dtype=np.float32)

    # Compute phoneme sample durations
    phoneme_samples = []
    for p in syllable.phonemes:
        n_samp = max(1, int((p.duration_ms / 1000.0) * sample_rate))
        phoneme_samples.append(n_samp)

    total_syllable_samples = sum(phoneme_samples)
    if total_syllable_samples <= 0:
        return np.array([], dtype=np.float32)

    # 1. Generate Syllable-Level F0 Pitch Contour
    f0_contour = generate_f0_contour(
        duration_samples=total_syllable_samples,
        sample_rate=sample_rate,
        base_f0=speaker.base_pitch_hz,
        pitch_range_semitones=speaker.pitch_range_semitones,
        chao_tone=syllable.prosody.chao_tone,
        pitch_curve=syllable.prosody.pitch_curve,
        vibrato_rate_hz=syllable.prosody.vibrato_rate_hz or 0.0,
        vibrato_depth_semitones=syllable.prosody.vibrato_depth_semitones or 0.0,
    )

    # 2. Generate Syllable-Level Volume Dynamics Envelope
    vol_envelope = generate_volume_envelope(
        duration_samples=total_syllable_samples,
        sample_rate=sample_rate,
        volume_envelope_pts=syllable.prosody.volume_envelope,
        default_volume_db=speaker.default_volume_db,
    )

    # 3. Synthesize individual phoneme segments
    syllable_audio_parts = []
    current_idx = 0

    phonation_mode = syllable.prosody.phonation or speaker.voice_quality or "modal"

    for i, p in enumerate(syllable.phonemes):
        n_samp = phoneme_samples[i]
        f0_seg = f0_contour[current_idx : current_idx + n_samp]
        
        p_audio = synthesize_phoneme_segment(
            phoneme=p,
            f0_segment=f0_seg,
            sample_rate=sample_rate,
            vocal_tract_scale=speaker.vocal_tract_scale,
            global_breathiness=speaker.breathiness,
            global_vocal_fry=speaker.vocal_fry,
            global_growl_roughness=speaker.growl_roughness,
            syllable_phonation=phonation_mode,
        )
        syllable_audio_parts.append(p_audio)
        current_idx += n_samp

    # Concatenate phonemes
    combined_audio = np.concatenate(syllable_audio_parts)

    # 4. Smooth coarticulation between internal phoneme boundaries
    fade_len = int(0.005 * sample_rate)  # 5ms crossfade
    if len(combined_audio) > len(f0_contour):
        combined_audio = combined_audio[:len(f0_contour)]

    # 5. Apply Syllable Volume Envelope
    modulated_audio = combined_audio * vol_envelope[:len(combined_audio)]

    # 6. Apply Global Feline Purr Modulation if enabled
    if speaker.purr_depth > 0.0 or phonation_mode == "feline_purr":
        purr_depth = speaker.purr_depth if speaker.purr_depth > 0 else 0.8
        t = np.arange(len(modulated_audio)) / float(sample_rate)
        purr_gate = 0.5 * (1.0 - np.cos(2.0 * np.pi * 24.5 * t))
        modulated_audio *= (1.0 - purr_depth + purr_depth * purr_gate)

    return modulated_audio.astype(np.float32)


def synthesize_script(script: ConlangScript, sample_rate: int = SAMPLE_RATE) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Main entry point: Synthesizes a complete ConlangScript into 44.1kHz audio and telemetry data.
    """
    if not script.utterance:
        return np.zeros(int(0.2 * sample_rate), dtype=np.float32), {"duration_sec": 0.2, "f0_timeline": []}

    syllable_audios = []
    pause_samples = int(0.04 * sample_rate)  # 40ms inter-syllable coarticulation gap/pause

    f0_telemetry = []
    current_time_ms = 0.0

    for s in script.utterance:
        s_audio = synthesize_syllable(s, script.speaker, sample_rate=sample_rate)
        syllable_audios.append(s_audio)
        
        # Telemetry for visualizer
        s_dur_ms = (len(s_audio) / sample_rate) * 1000.0
        f0_telemetry.append({
            "syllable": s.label or "syl",
            "start_ms": current_time_ms,
            "duration_ms": s_dur_ms,
            "tone": s.prosody.chao_tone or "flat",
            "phonation": s.prosody.phonation or "modal",
        })
        current_time_ms += s_dur_ms + (pause_samples / sample_rate * 1000.0)
        
        # Add micro-pause
        syllable_audios.append(np.zeros(pause_samples, dtype=np.float32))

    # Concatenate all syllables
    full_audio = np.concatenate(syllable_audios)

    # Master Normalization (-1dB peak headroom)
    max_peak = np.max(np.abs(full_audio)) + 1e-6
    target_peak = 0.89  # -1 dBFS
    if max_peak > 0.01:
        full_audio = (full_audio / max_peak) * target_peak

    telemetry = {
        "duration_sec": float(len(full_audio) / sample_rate),
        "sample_rate": sample_rate,
        "syllables": f0_telemetry,
    }

    return full_audio, telemetry


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
