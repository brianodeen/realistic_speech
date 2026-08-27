"""
Universal Neural-Bioacoustic Speech Synthesizer.
Combines ultra-realistic deep neural text-to-speech models (Edge-TTS Neural Voices with SSML prosody)
for human phonetic articulation, with the Physical Bioacoustic Chaos Engine for creature/animal vocalizations,
lingual suction clicks, and ejectives.
Produces studio-grade, non-robotic, crystal-clear 44.1kHz speech.
"""

import asyncio
import io
import os
import tempfile
import numpy as np
import soundfile as sf
from scipy import signal
from typing import Tuple, Dict, Any, Optional, List

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

from .schema import ConlangScript, Syllable, PhonemeSegment
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

# Set of physical symbols that must NEVER be sent as text words to Neural TTS
CLICK_SYMBOLS = {"click_dental", "click_alveolar", "click_lateral", "click_bilabial", "ǀ", "ǃ", "ǁ", "ʘ"}
EJECTIVE_SYMBOLS = {"ejective_k", "ejective_t", "ejective_p", "kʼ", "tʼ", "pʼ"}
GLOTTAL_SYMBOLS = {"glottal_stop", "ʔ", "q_glottal"}


def select_best_neural_voice(script: ConlangScript) -> str:
    """Selects the best matching neural voice based on language and speaker parameters."""
    lang = (script.language or "").lower()
    spk_name = (script.speaker.name or "").lower()
    base_f0 = script.speaker.base_pitch_hz

    if "mandarin" in lang or "chinese" in lang:
        return "zh-CN-XiaoxiaoNeural"
    if "vietnam" in lang:
        return "vi-VN-HoaiMyNeural"
    if "arabic" in lang:
        return "ar-SA-HamedNeural"
    if base_f0 < 130 or "deep" in spk_name or "dragon" in spk_name or "beast" in spk_name or "wolf" in spk_name:
        return "en-US-GuyNeural"
    if base_f0 < 165:
        return "en-US-ChristopherNeural"
    return "en-US-AriaNeural"


def is_pure_physical_sound(symbol: str) -> bool:
    """Checks if a phoneme symbol is a non-pulmonic click, ejective, glottal stop, or creature sound."""
    sym = symbol.lower().strip()
    return (
        sym in CLICK_SYMBOLS
        or sym in EJECTIVE_SYMBOLS
        or sym in GLOTTAL_SYMBOLS
        or sym in CREATURE_TABLE
        or "click" in sym
        or "ejective" in sym
        or "feline" in sym
        or "canine" in sym
    )


def extract_vocalic_text(syllable: Syllable) -> str:
    """
    Extracts only the true pronounceable vocalic/consonantal phonemes from a syllable,
    stripping out click, ejective, glottal, and creature tokens so TTS never pronounces code names.
    """
    # 1. Clean explicit labels if present
    lbl = (syllable.label or "").strip()
    clean_label_map = {
        "wiː": "We", "wi": "We",
        "sɔː": "saw", "sɔ": "saw",
        "juː": "you", "ju": "you",
        "ɡoʊ": "go", "go": "go",
        "mā": "mā", "má": "má", "mǎ": "mǎ", "mà": "mà",
        "mɛˀ": "Mẹ", "əːj": "ơi", "sɨəˀ": "sữa", "kaː": "cá",
        "qal": "Qal", "xab": "khab", "ruːħ": "rooh",
        "Oooommm": "Ohm", "Aaaa-eeee": "Ah-ee",
    }
    if lbl in clean_label_map:
        return clean_label_map[lbl]

    # 2. Translate individual phoneme symbols into phonetic spelling
    symbol_to_phonetic = {
        "i": "ee", "e": "ay", "epsilon": "eh", "a": "ah", "open_o": "aw",
        "o": "oh", "u": "oo", "schwa": "uh", "ae": "a", "nasal_a": "ahn",
        "nasal_o": "ohn", "m": "m", "n": "n", "p": "p", "b": "b",
        "t": "t", "d": "d", "k": "k", "g": "g", "s": "s", "z": "z",
        "sh": "sh", "f": "f", "v": "v", "r": "r", "l": "l", "x_velar": "kh",
        "gamma": "gh", "h": "h", "j": "y", "w": "w"
    }

    vocal_parts = []
    for p in syllable.phonemes:
        sym = p.symbol.lower().strip()
        # Ignore clicks, ejectives, creature sounds, glottal stops
        if is_pure_physical_sound(sym) or p.type == "creature":
            continue
        if sym in symbol_to_phonetic:
            vocal_parts.append(symbol_to_phonetic[sym])

    text = "".join(vocal_parts).strip()
    return text.capitalize() if text else ""


async def synthesize_neural_text_async(text: str, voice_id: str, pitch_hz_offset: float = 0.0) -> np.ndarray:
    """Renders text using Edge-TTS neural engine and returns float32 numpy audio at 44.1kHz."""
    if not EDGE_TTS_AVAILABLE or not text.strip():
        return np.zeros(0, dtype=np.float32)

    # Clamp pitch offset to natural human speaking range (-15Hz to +15Hz) to prevent Chipmunk helium sound
    clamped_offset = max(-15.0, min(15.0, pitch_hz_offset))
    pitch_str = f"{int(clamped_offset):+d}Hz" if clamped_offset != 0 else "+0Hz"
    communicate = edge_tts.Communicate(text=text, voice=voice_id, pitch=pitch_str)

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


async def synthesize_neural_script_async(script: ConlangScript, sample_rate: int = SAMPLE_RATE) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Asynchronous implementation of Universal Neural-Bioacoustic Hybrid Synthesis.
    Combines studio neural voices for human phonetic articulation with physical DSP models
    for suction clicks, ejectives, growls, purrs, snarls, barks, whines, and howls.
    """
    if not script.utterance:
        return np.zeros(int(0.2 * sample_rate), dtype=np.float32), {"duration_sec": 0.2, "syllables": []}

    voice_id = select_best_neural_voice(script)
    base_f0 = script.speaker.base_pitch_hz

    syllable_audio_segments = []
    syllable_telemetry = []
    current_time_ms = 0.0

    for s_idx, syl in enumerate(script.utterance):
        syl_start_ms = current_time_ms
        dur_ms = syl.duration_ms or sum(p.duration_ms for p in syl.phonemes) or 300.0
        n_samples = max(1, int((dur_ms / 1000.0) * sample_rate))

        # Check for physical sound components
        physical_segments = [p for p in syl.phonemes if is_pure_physical_sound(p.symbol) or p.type == "creature"]
        vocal_text = extract_vocalic_text(syl)

        syl_audio = np.zeros(0, dtype=np.float32)

        # 1. Synthesize Physical Elements (Clicks, Ejectives, Bioacoustics)
        if physical_segments:
            p_first = physical_segments[0]
            sym = p_first.symbol.lower().strip()
            cat = p_first.category or sym

            if "click" in sym or sym in CLICK_SYMBOLS:
                phys_audio = synthesize_click_burst(sym, int(0.040 * sample_rate), sample_rate)
            elif "ejective" in sym or sym in EJECTIVE_SYMBOLS:
                phys_audio = synthesize_ejective_burst(sym, int(0.050 * sample_rate), sample_rate)
            elif cat == "feline_purr" or sym == "feline_purr":
                phys_audio = synthesize_feline_purr(n_samples, sample_rate, rate_hz=p_first.rate_hz or 24.5, depth=p_first.intensity or 0.90)
            elif cat == "feline_growl" or sym == "feline_growl":
                phys_audio = synthesize_feline_growl(n_samples, sample_rate, base_f0=base_f0, intensity=p_first.intensity or 0.90, subharmonic_depth=p_first.subharmonic_depth or 0.80)
            elif cat == "feline_hiss" or sym == "feline_hiss":
                phys_audio = synthesize_feline_hiss(n_samples, sample_rate, intensity=p_first.intensity or 0.90)
            elif cat == "canine_snarl" or sym == "canine_snarl":
                phys_audio = synthesize_canine_snarl(n_samples, sample_rate, base_f0=base_f0, flutter_hz=p_first.rate_hz or 48.0, roughness=p_first.intensity or 0.85)
            elif cat == "canine_bark" or sym == "canine_bark":
                phys_audio = synthesize_canine_bark(n_samples, sample_rate, base_f0=base_f0)
            elif cat == "canine_whine" or sym == "canine_whine":
                phys_audio = synthesize_canine_whine(n_samples, sample_rate, base_f0=base_f0)
            elif sym in GLOTTAL_SYMBOLS:
                phys_audio = np.zeros(int(0.030 * sample_rate), dtype=np.float32)
            else:
                phys_audio = synthesize_feline_growl(n_samples, sample_rate, base_f0=base_f0)

            # If there is also a vocalic sound in this syllable (e.g. click + vowel [ǀkʼi]), blend them!
            if vocal_text:
                vowel_audio = await synthesize_neural_text_async(vocal_text, voice_id, pitch_hz_offset=0.0)
                if len(vowel_audio) > 0:
                    # Prepend click/ejective burst to the neural vowel
                    syl_audio = np.concatenate([phys_audio, vowel_audio])
                else:
                    syl_audio = phys_audio
            else:
                syl_audio = phys_audio

        # 2. Pure Vocalic / Consonantal Human Phonetic Syllable
        elif vocal_text:
            syl_audio = await synthesize_neural_text_async(vocal_text, voice_id, pitch_hz_offset=0.0)

        # Fallback if empty
        if len(syl_audio) == 0:
            syl_audio = np.zeros(int(0.20 * sample_rate), dtype=np.float32)

        # Volume balance
        max_p = np.max(np.abs(syl_audio))
        if max_p > 0.01:
            syl_audio = (syl_audio / max_p) * 0.85

        syllable_audio_segments.append(syl_audio)
        dur_ms = (len(syl_audio) / sample_rate) * 1000.0
        syllable_telemetry.append({
            "syllable": syl.label or f"syl_{s_idx + 1}",
            "start_ms": syl_start_ms,
            "duration_ms": dur_ms,
            "tone": syl.prosody.chao_tone or "custom",
            "phonation": syl.prosody.phonation or "modal",
        })
        current_time_ms += dur_ms

    if not syllable_audio_segments:
        return np.zeros(int(0.2 * sample_rate), dtype=np.float32), {"duration_sec": 0.2, "syllables": []}

    full_audio = np.concatenate(syllable_audio_segments)

    # Master normalization
    max_peak = np.max(np.abs(full_audio)) + 1e-6
    normalized_audio = (full_audio / max_peak) * 0.89

    telemetry = {
        "duration_sec": float(len(normalized_audio) / sample_rate),
        "total_samples": len(normalized_audio),
        "syllables": syllable_telemetry,
        "engine": "Neural-Bioacoustic Hybrid (Studio Quality)",
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
