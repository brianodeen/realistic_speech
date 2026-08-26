"""
Continuous Time-Varying Vocal Tract Formant Filter & Cursive Coarticulation Engine.
Generates seamless formant trajectories (F1-F5) across phonemes and syllables (cursive blending),
preserving continuous filter states, soft-tissue wall damping, and acoustic body warmth.
"""

import numpy as np
from scipy import signal
from typing import List, Tuple, Dict, Any, Optional

from .articulatory import VOWEL_TABLE, CONSONANT_TABLE, CREATURE_TABLE


def get_phoneme_formant_target(symbol: str, vocal_tract_scale: float = 1.0) -> Tuple[List[float], List[float], bool]:
    """
    Returns (formants, bandwidths, is_nasal) for a given phoneme symbol,
    scaled by vocal_tract_scale.
    """
    sym = symbol.lower().strip()
    scale = max(0.5, min(2.0, vocal_tract_scale))

    if sym in VOWEL_TABLE:
        v = VOWEL_TABLE[sym]
        formants = [f / scale for f in v["formants"]]
        bws = v["bandwidths"]
        return formants, bws, v.get("nasal", False)

    if sym in CONSONANT_TABLE:
        c = CONSONANT_TABLE[sym]
        formants = [f / scale for f in c.get("formants", [300, 1500, 2500, 3500, 4200])]
        bws = c.get("bandwidths", [90, 130, 180, 220, 260])
        return formants, bws, (c.get("manner") == "nasal")

    if sym in CREATURE_TABLE:
        cr = CREATURE_TABLE[sym]
        reso = cr.get("throat_resonance_hz", [300, 1000, 2000, 3200])
        formants = [f / scale for f in reso] + [4200 / scale]
        bws = [100, 150, 200, 250, 300]
        return formants, bws, False

    # Default neutral schwa
    return [500 / scale, 1500 / scale, 2500 / scale, 3500 / scale, 4200 / scale], [80, 100, 150, 200, 250], False


def compute_continuous_formant_trajectories(
    phoneme_sequence: List[Dict[str, Any]],
    sample_rate: int,
    vocal_tract_scale: float = 1.0,
    cursive_blend_ratio: float = 0.45,
    fleshiness: float = 0.70,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Constructs continuous sample-by-sample formant (5 x N) and bandwidth (5 x N)
    trajectories using smooth S-curve (cosine) transitions between phonemes (Cursive Coarticulation).
    Fleshiness expands bandwidths to prevent metallic resonance ringing.
    """
    total_samples = sum(p["num_samples"] for p in phoneme_sequence)
    if total_samples <= 0:
        return np.zeros((5, 0), dtype=np.float32), np.zeros((5, 0), dtype=np.float32), np.zeros(0, dtype=np.float32)

    formant_matrix = np.zeros((5, total_samples), dtype=np.float64)
    bw_matrix = np.zeros((5, total_samples), dtype=np.float64)
    nasal_envelope = np.zeros(total_samples, dtype=np.float64)

    # Bandwidth damping multiplier based on soft tissue fleshiness
    bw_flesh_factor = 1.0 + (0.55 * fleshiness)

    # 1. First pass: establish steady-state targets and boundary transition intervals
    current_sample = 0
    seg_starts = []
    seg_targets = []

    for seg in phoneme_sequence:
        sym = seg["symbol"]
        n_samp = seg["num_samples"]
        fmts, bws, is_nasal = get_phoneme_formant_target(sym, vocal_tract_scale)
        damped_bws = [bw * bw_flesh_factor for bw in bws]

        seg_starts.append((current_sample, current_sample + n_samp))
        seg_targets.append({
            "formants": fmts,
            "bandwidths": damped_bws,
            "nasal": 1.0 if is_nasal else 0.0,
            "symbol": sym,
            "is_glottal_stop": (sym in ["glottal_stop", "ʔ", "q_glottal"])
        })
        current_sample += n_samp

    # 2. Second pass: render steady states and interpolate transitions smoothly
    num_segs = len(seg_starts)

    for i in range(num_segs):
        start_idx, end_idx = seg_starts[i]
        tgt = seg_targets[i]

        # Fill default steady state
        for f_idx in range(5):
            formant_matrix[f_idx, start_idx:end_idx] = tgt["formants"][f_idx]
            bw_matrix[f_idx, start_idx:end_idx] = tgt["bandwidths"][f_idx]
        nasal_envelope[start_idx:end_idx] = tgt["nasal"]

    # 3. Apply smooth cursive transitions between consecutive segments
    for i in range(num_segs - 1):
        _, curr_end = seg_starts[i]
        next_start, next_end = seg_starts[i + 1]

        curr_tgt = seg_targets[i]
        next_tgt = seg_targets[i + 1]

        # If there's an explicit glottal stop, do NOT blend across the boundary!
        if curr_tgt["is_glottal_stop"] or next_tgt["is_glottal_stop"]:
            continue

        # Transition duration based on cursive blend ratio (typical 30ms - 80ms)
        curr_len = curr_end - seg_starts[i][0]
        next_len = next_end - next_start
        max_trans = min(curr_len // 2, next_len // 2, int(0.085 * sample_rate))
        trans_samples = max(2, int(max_trans * cursive_blend_ratio))

        if trans_samples < 2:
            continue

        trans_start = curr_end - (trans_samples // 2)
        trans_end = curr_end + (trans_samples // 2)
        trans_len = trans_end - trans_start

        # Raised cosine S-curve transition from 0.0 to 1.0
        t = np.linspace(0.0, np.pi, trans_len)
        alpha = 0.5 * (1.0 - np.cos(t))

        for f_idx in range(5):
            f_from = curr_tgt["formants"][f_idx]
            f_to = next_tgt["formants"][f_idx]
            bw_from = curr_tgt["bandwidths"][f_idx]
            bw_to = next_tgt["bandwidths"][f_idx]

            formant_matrix[f_idx, trans_start:trans_end] = f_from + (f_to - f_from) * alpha
            bw_matrix[f_idx, trans_start:trans_end] = bw_from + (bw_to - bw_from) * alpha

        # Blend nasality
        nasal_envelope[trans_start:trans_end] = curr_tgt["nasal"] + (next_tgt["nasal"] - curr_tgt["nasal"]) * alpha

    return formant_matrix.astype(np.float32), bw_matrix.astype(np.float32), nasal_envelope.astype(np.float32)


def apply_continuous_formant_filter(
    excitation_audio: np.ndarray,
    formant_matrix: np.ndarray,
    bw_matrix: np.ndarray,
    nasal_envelope: np.ndarray,
    sample_rate: int,
    warmth: float = 0.40,
    fleshiness: float = 0.70,
) -> np.ndarray:
    """
    Applies continuous time-varying formant filtering with soft mucosal wall damping,
    anti-metallic de-ringing, subglottal tracheal coupling, and organic chest warmth.
    """
    num_samples = len(excitation_audio)
    if num_samples == 0:
        return excitation_audio

    # Filter parameters
    hop_size = 48  # ~1.08ms at 44.1kHz for ultra-smooth time variance
    
    # Formant relative gains (F1 strongest, smooth organic roll-off)
    flesh_tilt = 1.0 + 0.5 * fleshiness
    formant_gains = [1.0, 0.55 / flesh_tilt, 0.28 / (flesh_tilt**2), 0.12 / (flesh_tilt**3), 0.05 / (flesh_tilt**4)]

    filtered_output = np.zeros(num_samples, dtype=np.float64)

    # Initialize continuous state variables for 5 formant biquad resonators
    zi_states = [np.zeros(2, dtype=np.float64) for _ in range(5)]
    zi_nasal = np.zeros(2, dtype=np.float64)

    nyquist = sample_rate / 2.0

    for i in range(0, num_samples, hop_size):
        chunk_len = min(hop_size, num_samples - i)
        exc_chunk = excitation_audio[i : i + chunk_len]

        # Formant frequencies and bandwidths at midpoint of this chunk
        mid_idx = min(num_samples - 1, i + chunk_len // 2)
        chunk_out = np.zeros(chunk_len, dtype=np.float64)

        for f_idx in range(5):
            f_res = max(40.0, min(formant_matrix[f_idx, mid_idx], nyquist - 120.0))
            bw = max(30.0, min(bw_matrix[f_idx, mid_idx], nyquist / 2.0))

            # Compute biquad resonator coefficients
            omega = 2.0 * np.pi * f_res / sample_rate
            r = np.exp(-np.pi * bw / sample_rate)
            a = np.array([1.0, -2.0 * r * np.cos(omega), r * r], dtype=np.float64)
            b0 = (1.0 - r) * np.sin(omega)
            b = np.array([b0, 0.0, -b0], dtype=np.float64)

            # Filter with continuous state memory (prevents clicks!)
            f_wave, zi_states[f_idx] = signal.lfilter(b, a, exc_chunk, zi=zi_states[f_idx])
            chunk_out += f_wave * formant_gains[f_idx]

        # Apply Nasal Resonance if nasal envelope > 0
        nasal_val = nasal_envelope[mid_idx]
        if nasal_val > 0.01:
            omega_n = 2.0 * np.pi * 260.0 / sample_rate
            r_n = np.exp(-np.pi * 90.0 / sample_rate)
            a_n = np.array([1.0, -2.0 * r_n * np.cos(omega_n), r_n * r_n], dtype=np.float64)
            b0_n = (1.0 - r_n) * np.sin(omega_n)
            b_n = np.array([b0_n, 0.0, -b0_n], dtype=np.float64)

            n_wave, zi_nasal = signal.lfilter(b_n, a_n, exc_chunk, zi=zi_nasal)
            chunk_out = chunk_out * (1.0 - 0.3 * nasal_val) + n_wave * (0.45 * nasal_val)

        filtered_output[i : i + chunk_len] = chunk_out

    # 4. Lip Radiation Impedance Model
    b_rad = np.array([1.0, -0.88], dtype=np.float64)
    a_rad = np.array([1.0], dtype=np.float64)
    radiated = signal.lfilter(b_rad, a_rad, filtered_output)

    # 5. Anti-Metallic De-Ringing & Soft Tissue Loss Filter
    if fleshiness > 0.0:
        # Soft tissue 2nd-order Bessel lowpass filter (gentle phase, no metallic ringing)
        cut_freq = 2400.0 + (1.0 - fleshiness) * 3200.0
        b_soft, a_soft = signal.bessel(2, min(cut_freq / nyquist, 0.92), btype="low")
        radiated = signal.lfilter(b_soft, a_soft, radiated)

    # 6. Subglottal Coupling & Chest Body Warmth
    if warmth > 0.0:
        # Chest cavity sub-resonance (~130-240 Hz)
        b_warmth, a_warmth = signal.butter(2, [min(110.0 / nyquist, 0.8), min(250.0 / nyquist, 0.9)], btype="band")
        chest_body = signal.lfilter(b_warmth, a_warmth, radiated)

        # Soft-knee analog tube saturation for natural vocal fold warmth
        drive = 1.0 + warmth * 1.8
        saturated = np.tanh(radiated * drive) / drive

        radiated = saturated * (1.0 - warmth * 0.20) + chest_body * (warmth * 0.40)

    return radiated.astype(np.float32)
