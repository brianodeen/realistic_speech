"""
Universal Neural-Bioacoustic ExtIPA Speech Synthesizer.
Combines ultra-realistic deep neural text-to-speech vocoders (Edge-TTS Neural Voices with SSML prosody)
with ExtIPA Cursive Liaison Parsing (‿, ͡), African velaric suction clicks (ǀ, ǃ, ǁ), glottal stops (ʔ),
and Physical Bioacoustic Chaos Modulations (growls, purrs, snarls, barks, whines).
Produces studio-grade, non-robotic, crystal-clear 44.1kHz human-pronounceable speech.
"""

import asyncio
import io
import os
import tempfile
import numpy as np
import soundfile as sf
from scipy import signal
from typing import Tuple, Dict, Any, Optional, List, Union

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

from .schema import ConlangScript, Syllable, PhonemeSegment, ExtIPAPhraseItem
from .extipa_parser import parse_extipa_string, ExtIPAPhrase
from .bioacoustics import (
    synthesize_feline_purr,
    synthesize_feline_growl,
    synthesize_feline_hiss,
    synthesize_canine_snarl,
    synthesize_canine_bark,
    synthesize_canine_whine,
    synthesize_click_burst,
    synthesize_ejective_burst,
)
from .articulatory import CONSONANT_TABLE, CREATURE_TABLE

SAMPLE_RATE = 44100


def select_best_neural_voice(script: ConlangScript) -> str:
    """Selects the best matching neural voice based on language and speaker parameters."""
    lang = (script.language or "").lower()
    spk_name = (script.speaker.name or "").lower()
    vtype = (getattr(script.speaker, "voice_type", "") or "").lower()
    base_f0 = script.speaker.base_pitch_hz

    if "mandarin" in lang or "chinese" in lang:
        return "zh-CN-XiaoxiaoNeural"
    if "vietnam" in lang:
        return "vi-VN-HoaiMyNeural"
    if "arabic" in lang:
        return "ar-SA-HamedNeural"
    
    if "female" in vtype or "soprano" in vtype:
        return "en-US-AriaNeural"
    if "baritone" in vtype or "deep" in vtype or base_f0 < 130 or "beast" in spk_name or "wolf" in spk_name:
        return "en-US-GuyNeural"
    if base_f0 < 165 or "male" in vtype:
        return "en-US-ChristopherNeural"
    return "en-US-AriaNeural"


async def synthesize_neural_text_async(text: str, voice_id: str, pitch_hz_offset: float = 0.0, speed_rate: float = 1.0) -> np.ndarray:
    """Renders phonetic text using Edge-TTS neural engine and returns float32 numpy audio at 44.1kHz."""
    if not EDGE_TTS_AVAILABLE or not text.strip():
        return np.zeros(0, dtype=np.float32)

    # Pitch offset clamped to natural human speaking range (-15Hz to +15Hz) to prevent Chipmunk helium sound
    clamped_pitch = max(-15.0, min(15.0, pitch_hz_offset))
    pitch_str = f"{int(clamped_pitch):+d}Hz" if clamped_pitch != 0 else "+0Hz"

    # Speed rate offset
    rate_pct = int(round((speed_rate - 1.0) * 100))
    rate_str = f"{rate_pct:+d}%" if rate_pct != 0 else "+0%"

    communicate = edge_tts.Communicate(text=text, voice=voice_id, pitch=pitch_str, rate=rate_str)

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
        tmp_path = tmp_file.name

    try:
        await communicate.save(tmp_path)
        data, sr = sf.read(tmp_path, dtype="float32")
        if len(data.shape) > 1:
            data = data.mean(axis=1)

        # Resample to 44.1kHz if needed
        if sr != SAMPLE_RATE:
            num_target = int(len(data) * (SAMPLE_RATE / sr))
            data = signal.resample(data, num_target).astype(np.float32)

        return data
    except Exception as e:
        print(f"[NeuralTTS Warning] {e}")
        return np.zeros(0, dtype=np.float32)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def apply_bioacoustic_phonation_modifier(
    audio: np.ndarray,
    phonation: str,
    base_f0: float,
    sample_rate: int = SAMPLE_RATE
) -> np.ndarray:
    """
    Applies physical ExtIPA phonation modulations (ventricular growl, purr gating,
    velopharyngeal snarl, creak, or breathy whisper) directly to the neural audio stream.
    """
    if len(audio) == 0 or phonation in ["modal", "", None]:
        return audio

    n = len(audio)
    t = np.arange(n) / float(sample_rate)
    ph = phonation.lower().strip()

    # 1. Ventricular False-Fold Growl / Throat Singing (ʭ)
    if "growl" in ph or "ventricular" in ph or ph == "ʭ":
        sub_f0 = max(40.0, base_f0 * 0.5)
        sub_mod = 0.5 * (1.0 + np.sin(2.0 * np.pi * sub_f0 * t))
        noise = np.random.randn(n) * 0.15
        return (audio * (0.65 + 0.35 * sub_mod) + noise * np.abs(audio)).astype(np.float32)

    # 2. Feline Laryngeal Neural Purr Gating (ʬ̃ / ʙ)
    elif "purr" in ph or ph == "ʬ̃" or ph == "ʙ":
        purr_rate = 24.5  # Hz
        twitch = 0.5 * (1.0 - np.cos(2.0 * np.pi * purr_rate * t)) ** 2
        return (audio * (0.35 + 0.65 * twitch)).astype(np.float32)

    # 3. Velopharyngeal Snarl / Mucosal Friction (f͌ / v͌)
    elif "snarl" in ph or ph in ["f͌", "v͌"]:
        snarl_rate = 48.0 # Hz
        flutter = 0.5 * (1.0 + np.sin(2.0 * np.pi * snarl_rate * t))
        noise = np.random.randn(n) * 0.20
        return (audio * (0.55 + 0.45 * flutter) + noise * np.abs(audio)).astype(np.float32)

    # 4. Breathy Whisper
    elif "breathy" in ph or "whisper" in ph:
        noise = np.random.randn(n) * 0.25
        return (audio * 0.60 + noise * np.abs(audio)).astype(np.float32)

    # 5. Vocal Fry / Creaky Voice
    elif "creaky" in ph or "fry" in ph:
        fry_pulses = (np.sin(2.0 * np.pi * 32.0 * t) > 0.85).astype(np.float32)
        return (audio * (0.50 + 0.50 * fry_pulses)).astype(np.float32)

    return audio


async def synthesize_neural_script_async(script: ConlangScript, sample_rate: int = SAMPLE_RATE) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Asynchronous Master Pipeline for Cursive ExtIPA Neural Speech Synthesis.
    Parses ExtIPA cursive strings, glottal breaks, and tone contours,
    synthesizing studio-grade natural speech via Neural Vocoding with bioacoustic transfer functions.
    """
    voice_id = select_best_neural_voice(script)
    base_f0 = script.speaker.base_pitch_hz
    speed_rate = getattr(script.speaker, "speed_rate", 1.0) or 1.0

    # 1. Normalize Input to ExtIPAPhrase list
    extipa_phrases: List[ExtIPAPhrase] = []

    # Case A: Concise ExtIPA script string provided (e.g. "wiː‿sɔː juː‿ɡoʊ")
    if script.script:
        if isinstance(script.script, list):
            full_script_str = " ".join(script.script)
        else:
            full_script_str = str(script.script)
        extipa_phrases = parse_extipa_string(full_script_str)

    # Case B: Utterance list provided
    elif script.utterance:
        for u in script.utterance:
            # Utterance is an ExtIPAPhraseItem or dict with 'phrase' / 'break'
            if isinstance(u, ExtIPAPhraseItem) or (isinstance(u, dict) and ("phrase" in u or "break" in u)):
                u_dict = u if isinstance(u, dict) else u.model_dump(by_alias=True)
                brk = u_dict.get("break") or u_dict.get("break_type")
                if brk:
                    dur = 45.0 if "glottal" in brk else 100.0
                    extipa_phrases.append(ExtIPAPhrase(
                        raw_text=brk,
                        phonetic_text="",
                        is_break=True,
                        break_duration_ms=dur,
                        phonation="glottal_stop"
                    ))
                elif u_dict.get("phrase"):
                    p_tone = u_dict.get("tone")
                    p_phon = u_dict.get("phonation", "modal")
                    sub_parsed = parse_extipa_string(u_dict["phrase"], default_tone=p_tone, default_phonation=p_phon)
                    extipa_phrases.extend(sub_parsed)

            # Utterance is a classic Syllable object
            elif isinstance(u, Syllable) or (isinstance(u, dict) and "phonemes" in u):
                syl_obj = u if isinstance(u, Syllable) else Syllable(**u)
                label = syl_obj.label or "".join(p.symbol for p in syl_obj.phonemes)
                s_tone = syl_obj.prosody.chao_tone
                s_phon = syl_obj.prosody.phonation
                sub_parsed = parse_extipa_string(label, default_tone=s_tone, default_phonation=s_phon)
                extipa_phrases.extend(sub_parsed)

    if not extipa_phrases:
        return np.zeros(int(0.2 * sample_rate), dtype=np.float32), {"duration_sec": 0.2, "phrases": []}

    audio_segments = []
    telemetry_segments = []
    current_time_ms = 0.0

    # 2. Synthesize Each ExtIPA Phrase & Break Along the Cursive Timeline
    for p_idx, phrase in enumerate(extipa_phrases):
        seg_start_ms = current_time_ms

        # --- A. Glottal Stop / Phrase Break ("Lifting the pen") ---
        if phrase.is_break:
            silence_dur_s = phrase.break_duration_ms / 1000.0
            seg_audio = np.zeros(int(silence_dur_s * sample_rate), dtype=np.float32)
            dur_ms = phrase.break_duration_ms

        # --- B. Speech Phrase / Cursive Compound ---
        else:
            p_text = phrase.phonetic_text
            if not p_text:
                continue

            # Render phrase via Neural Vocoder
            seg_audio = await synthesize_neural_text_async(p_text, voice_id, pitch_hz_offset=0.0, speed_rate=speed_rate)

            # If phrase contains a click onset (e.g. kǀi, kǃa), overlay sharp velaric click shockwave at t=0
            if phrase.has_click and len(seg_audio) > 0:
                click_burst = synthesize_click_burst(phrase.click_type or "click_alveolar", int(0.025 * sample_rate), sample_rate)
                blend_len = min(len(click_burst), len(seg_audio))
                seg_audio[:blend_len] = seg_audio[:blend_len] * 0.35 + click_burst[:blend_len] * 1.25

            # Apply Bioacoustic ExtIPA Phonation Modifiers (Growl, Purr, Snarl, Whisper)
            if phrase.phonation and phrase.phonation != "modal":
                seg_audio = apply_bioacoustic_phonation_modifier(seg_audio, phrase.phonation, base_f0, sample_rate)

            # Gentle edge smoothing (3ms) to ensure continuous cursive flow without boundary clicks
            if len(seg_audio) > 128:
                fade_len = int(0.003 * sample_rate)
                seg_audio[:fade_len] *= np.linspace(0.0, 1.0, fade_len)
                seg_audio[-fade_len:] *= np.linspace(1.0, 0.0, fade_len)

            dur_ms = (len(seg_audio) / sample_rate) * 1000.0

        audio_segments.append(seg_audio)
        telemetry_segments.append({
            "phrase": phrase.raw_text,
            "phonetic": phrase.phonetic_text,
            "start_ms": seg_start_ms,
            "duration_ms": dur_ms,
            "phonation": phrase.phonation,
            "tone": phrase.chao_tone or "modal",
        })
        current_time_ms += dur_ms

    if not audio_segments:
        return np.zeros(int(0.2 * sample_rate), dtype=np.float32), {"duration_sec": 0.2, "phrases": []}

    full_audio = np.concatenate(audio_segments)

    # Master normalization
    max_peak = np.max(np.abs(full_audio)) + 1e-6
    normalized_audio = (full_audio / max_peak) * 0.89

    telemetry = {
        "duration_sec": float(len(normalized_audio) / sample_rate),
        "total_samples": len(normalized_audio),
        "phrases": telemetry_segments,
        "engine": "Universal ExtIPA Neural Vocoder (Studio Quality)",
        "neural_voice": voice_id,
    }

    return normalized_audio.astype(np.float32), telemetry


def synthesize_neural_script(script: ConlangScript, sample_rate: int = SAMPLE_RATE) -> Tuple[np.ndarray, Dict[str, Any]]:
    """Synchronous wrapper for synthesize_neural_script_async."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, synthesize_neural_script_async(script, sample_rate))
                return future.result()
        else:
            return loop.run_until_complete(synthesize_neural_script_async(script, sample_rate))
    except RuntimeError:
        return asyncio.run(synthesize_neural_script_async(script, sample_rate))
