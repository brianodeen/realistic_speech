"""
Continuous Time-Varying Vocal Tract Formant Filter & Cursive Coarticulation Engine.
Implements C2-continuous Hermite 'Smootherstep' formant trajectory interpolation (w(t) = 6t^5 - 15t^4 + 10t^3),
direct-form R-theta normalized biquad resonators with crystal-clear wideband presence,
and natural acoustic chest body warmth.
"""

import numpy as np
from scipy import signal
from typing import List, Tuple, Dict, Any, Optional

from .articulatory import VOWEL_TABLE, CONSONANT_TABLE, CREATURE_TABLE


def smootherstep(t: np.ndarray) -> np.ndarray:
    """
    5th-order Hermite interpolation polynomial (C2-continuous).
    w(t) = 6t^5 - 15t^4 + 10t^3
    Ensures first derivative (velocity) and second derivative (acceleration)
    are exactly zero at both endpoints (t=0 and t=1), eliminating jerk and acoustic clicks.
    """
    t_clamped = np.clip(t, 0.0, 1.0)
    return t_clamped * t_clamped * t_clamped * (t_clamped * (t_clamped * 6.0 - 15.0) + 10.0)


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
    trajectories using C2-continuous Hermite Smootherstep transitions between phonemes.
    """
    total_samples = sum(p["num_samples"] for p in phoneme_sequence)
    if total_samples <= 0:
        return np.zeros((5, 0), dtype=np.float32), np.zeros((5, 0), dtype=np.float32), np.zeros(0, dtype=np.float32)

    formant_matrix = np.zeros((5, total_samples), dtype=np.float64)
    bw_matrix = np.zeros((5, total_samples), dtype=np.float64)
    nasal_envelope = np.zeros(total_samples, dtype=np.float64)

    # 1. First pass: establish steady-state targets and boundary transition intervals
    current_sample = 0
    seg_starts = []
    seg_targets = []

    for seg in phoneme_sequence:
        sym = seg["symbol"]
        n_samp = seg["num_samples"]
        fmts, bws, is_nasal = get_phoneme_formant_target(sym, vocal_tract_scale)

        seg_starts.append((current_sample, current_sample + n_samp))
        seg_targets.append({
            "formants": fmts,
            "bandwidths": bws,
            "nasal": 1.0 if is_nasal else 0.0,
            "symbol": sym,
            "is_glottal_stop": (sym in ["glottal_stop", "ʔ", "q_glottal"])
        })
        current_sample += n_samp

    # 2. Second pass: render steady states
    num_segs = len(seg_starts)

    for i in range(num_segs):
        start_idx, end_idx = seg_starts[i]
        tgt = seg_targets[i]

        for f_idx in range(5):
            formant_matrix[f_idx, start_idx:end_idx] = tgt["formants"][f_idx]
            bw_matrix[f_idx, start_idx:end_idx] = tgt["bandwidths"][f_idx]
        nasal_envelope[start_idx:end_idx] = tgt["nasal"]

    # 3. Apply C2-continuous Hermite Smootherstep transitions between consecutive segments
    for i in range(num_segs - 1):
        _, curr_end = seg_starts[i]
        next_start, next_end = seg_starts[i + 1]

        curr_tgt = seg_targets[i]
        next_tgt = seg_targets[i + 1]

        # If there's an explicit glottal stop, do NOT blend across the boundary!
        if curr_tgt["is_glottal_stop"] or next_tgt["is_glottal_stop"]:
            continue

        curr_len = curr_end - seg_starts[i][0]
        next_len = next_end - next_start
        max_trans = min(curr_len // 2, next_len // 2, int(0.090 * sample_rate))
        trans_samples = max(2, int(max_trans * cursive_blend_ratio))

        if trans_samples < 2:
            continue

        trans_start = curr_end - (trans_samples // 2)
        trans_end = curr_end + (trans_samples // 2)
        trans_len = trans_end - trans_start

        # C2-Continuous Hermite Smootherstep Curve
        t = np.linspace(0.0, 1.0, trans_len)
        alpha = smootherstep(t)

        for f_idx in range(5):
            f_from = curr_tgt["formants"][f_idx]
            f_to = next_tgt["formants"][f_idx]
            bw_from = curr_tgt["bandwidths"][f_idx]
            bw_to = next_tgt["bandwidths"][f_idx]

            formant_matrix[f_idx, trans_start:trans_end] = f_from + (f_to - f_from) * alpha
            bw_matrix[f_idx, trans_start:trans_end] = bw_from + (bw_to - bw_from) * alpha

        # Blend nasality smoothly
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
    Applies continuous time-varying formant filtering using direct-form R-theta
    normalized biquad resonators with crystal-clear wideband speech presence:
    R = exp(-pi * Bw / Fs), theta = 2*pi * Fc / Fs
    y[n] = 2*R*cos(theta)*y[n-1] - R^2*y[n-2] + (1 - R)*x[n]
    """
    num_samples = len(excitation_audio)
    if num_samples == 0:
        return excitation_audio

    # Filter evaluation chunk size (~1.08ms at 44.1kHz for continuous glide)
    hop_size = 48
    
    # Crisp, open acoustic formant gains for full-range vocal intelligibility
    formant_gains = [1.0, 0.80, 0.58, 0.36, 0.20]

    filtered_output = np.zeros(num_samples, dtype=np.float64)

    # State variables for 5 direct-form resonators
    zi_states = [np.zeros(2, dtype=np.float64) for _ in range(5)]
    zi_nasal = np.zeros(2, dtype=np.float64)

    nyquist = sample_rate / 2.0

    for i in range(0, num_samples, hop_size):
        chunk_len = min(hop_size, num_samples - i)
        exc_chunk = excitation_audio[i : i + chunk_len]

        mid_idx = min(num_samples - 1, i + chunk_len // 2)
        chunk_out = np.zeros(chunk_len, dtype=np.float64)

        for f_idx in range(5):
            f_res = max(50.0, min(formant_matrix[f_idx, mid_idx], nyquist - 150.0))
            bw = max(35.0, min(bw_matrix[f_idx, mid_idx], nyquist / 2.5))

            # Direct Form R-Theta Formulation
            r = np.exp(-np.pi * bw / sample_rate)
            theta = 2.0 * np.pi * f_res / sample_rate

            a = np.array([1.0, -2.0 * r * np.cos(theta), r * r], dtype=np.float64)
            b = np.array([1.0 - r, 0.0, 0.0], dtype=np.float64)

            f_wave, zi_states[f_idx] = signal.lfilter(b, a, exc_chunk, zi=zi_states[f_idx])
            chunk_out += f_wave * formant_gains[f_idx]

        # Apply Nasal Resonance if velic port is open
        nasal_val = nasal_envelope[mid_idx]
        if nasal_val > 0.01:
            r_n = np.exp(-np.pi * 95.0 / sample_rate)
            theta_n = 2.0 * np.pi * 270.0 / sample_rate
            a_n = np.array([1.0, -2.0 * r_n * np.cos(theta_n), r_n * r_n], dtype=np.float64)
            b_n = np.array([1.0 - r_n, 0.0, 0.0], dtype=np.float64)

            n_wave, zi_nasal = signal.lfilter(b_n, a_n, exc_chunk, zi=zi_nasal)
            chunk_out = chunk_out * (1.0 - 0.25 * nasal_val) + n_wave * (0.40 * nasal_val)

        filtered_output[i : i + chunk_len] = chunk_out

    # 4. Lip Radiation Impedance Model (+6dB/octave high-frequency acoustic presence)
    b_rad = np.array([1.0, -0.92], dtype=np.float64)
    a_rad = np.array([1.0], dtype=np.float64)
    radiated = signal.lfilter(b_rad, a_rad, filtered_output)

    # 5. Natural Chest Body Warmth & Analog Saturation (without high-frequency muffling)
    if warmth > 0.0:
        b_warmth, a_warmth = signal.butter(2, [min(120.0 / nyquist, 0.8), min(280.0 / nyquist, 0.9)], btype="band")
        chest_body = signal.lfilter(b_warmth, a_warmth, radiated)

        # Soft-knee tube saturation adds body harmonics without cutting presence
        drive = 1.0 + warmth * 1.2
        saturated = np.tanh(radiated * drive) / drive

        radiated = saturated * 0.85 + chest_body * (warmth * 0.25)

    return radiated.astype(np.float32)
