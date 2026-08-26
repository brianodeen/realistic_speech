"""
Prosody, Tone and Intonation Engine.
Handles continuous pitch contour interpolation, Chao 5-level tone generation,
vibrato/micro-prosody, and dynamic volume envelopes.
"""

import numpy as np
from typing import List, Tuple, Optional
from scipy.interpolate import PchipInterpolator, interp1d


# Standard Chao 5-Level Tone pitch ratios (1 to 5 scale where 3 = 1.0 = base_f0)
# Level 1 = -6 semitones, Level 2 = -3 semitones, Level 3 = 0 st, Level 4 = +3 st, Level 5 = +6 st (tunable)
CHAO_LEVEL_SEMITONES = {
    "1": -6.0,
    "2": -3.0,
    "3": 0.0,
    "4": 3.0,
    "5": 6.0,
}

# Standard Chao Tone Presets
CHAO_PRESETS = {
    "55": [("5", 0.0), ("5", 1.0)],                  # High Level (Mandarin 1st)
    "35": [("3", 0.0), ("3.2", 0.3), ("5", 1.0)],    # High Rising (Mandarin 2nd)
    "214": [("2", 0.0), ("1", 0.4), ("4", 1.0)],     # Dipping / Low Falling-Rising (Mandarin 3rd)
    "51": [("5", 0.0), ("4", 0.2), ("1", 1.0)],      # High Falling (Mandarin 4th)
    "33": [("3", 0.0), ("3", 1.0)],                  # Mid Level (Cantonese 3rd)
    "21": [("2", 0.0), ("1", 1.0)],                  # Low Falling (Cantonese 4th)
    "11": [("1", 0.0), ("1", 1.0)],                  # Low Level
}


def chao_digit_to_semitones(digit_str: str) -> float:
    """Converts a single Chao tone digit or decimal (e.g. '3.5') to semitones relative to base_f0."""
    try:
        val = float(digit_str)
        # linear map: 1.0 -> -6.0 st, 5.0 -> +6.0 st => semitone = (val - 3.0) * 3.0
        return (val - 3.0) * 3.0
    except ValueError:
        return 0.0


def generate_f0_contour(
    duration_samples: int,
    sample_rate: int,
    base_f0: float,
    pitch_range_semitones: float = 12.0,
    chao_tone: Optional[str] = None,
    pitch_curve: Optional[List[Tuple[float, float]]] = None,
    vibrato_rate_hz: float = 0.0,
    vibrato_depth_semitones: float = 0.0,
) -> np.ndarray:
    """
    Generates a continuous F0 (fundamental frequency in Hz) trajectory over duration_samples.
    """
    if duration_samples <= 0:
        return np.array([], dtype=np.float32)

    time_ratios = np.linspace(0.0, 1.0, duration_samples, endpoint=True)
    f0_curve = np.full(duration_samples, base_f0, dtype=np.float64)

    # 1. Evaluate explicit pitch_curve if provided
    if pitch_curve and len(pitch_curve) >= 2:
        # Sort points by time ratio
        pts = sorted(pitch_curve, key=lambda p: p[0])
        x_pts = [max(0.0, min(1.0, float(p[0]))) for p in pts]
        y_pts = [float(p[1]) for p in pts]

        # Ensure endpoints at 0.0 and 1.0
        if x_pts[0] > 0.0:
            x_pts.insert(0, 0.0)
            y_pts.insert(0, y_pts[0])
        if x_pts[-1] < 1.0:
            x_pts.append(1.0)
            y_pts.append(y_pts[-1])

        # Remove duplicate x points
        unique_x, unique_indices = np.unique(x_pts, return_index=True)
        unique_y = [y_pts[i] for i in unique_indices]

        if len(unique_x) >= 3:
            # Monotonic cubic spline (PCHIP) prevents overshoot
            interpolator = PchipInterpolator(unique_x, unique_y)
        else:
            interpolator = interp1d(unique_x, unique_y, kind="linear", fill_value="extrapolate")

        interpolated_f0 = interpolator(time_ratios)
        # Check if values are absolute Hz (>30) or relative semitones (<=30)
        if np.all(interpolated_f0 < 40.0):
            # Treat as semitone offsets
            f0_curve = base_f0 * (2.0 ** (interpolated_f0 / 12.0))
        else:
            f0_curve = np.clip(interpolated_f0, 30.0, 2500.0)

    # 2. Evaluate Chao Tone Code if no explicit pitch_curve
    elif chao_tone:
        clean_tone = str(chao_tone).strip()
        
        # Look up preset or parse individual digits
        if clean_tone in CHAO_PRESETS:
            preset = CHAO_PRESETS[clean_tone]
            x_pts = [p[1] for p in preset]
            st_pts = [chao_digit_to_semitones(p[0]) for p in preset]
        else:
            # Parse digits e.g. "53" -> digit '5' at t=0, '3' at t=1
            digits = [c for c in clean_tone if c.isdigit()]
            if not digits:
                digits = ["3"]
            if len(digits) == 1:
                x_pts = [0.0, 1.0]
                st_pts = [chao_digit_to_semitones(digits[0]), chao_digit_to_semitones(digits[0])]
            else:
                x_pts = np.linspace(0.0, 1.0, len(digits)).tolist()
                st_pts = [chao_digit_to_semitones(d) for d in digits]

        # Scale semitones according to speaker's pitch_range_semitones (default 12st between 1 and 5)
        scale_factor = (pitch_range_semitones / 12.0)
        scaled_st_pts = [s * scale_factor for s in st_pts]

        if len(x_pts) >= 3:
            interpolator = PchipInterpolator(x_pts, scaled_st_pts)
        else:
            interpolator = interp1d(x_pts, scaled_st_pts, kind="linear", fill_value="extrapolate")

        semitone_contour = interpolator(time_ratios)
        f0_curve = base_f0 * (2.0 ** (semitone_contour / 12.0))

    # 3. Add Vibrato / LFO frequency modulation if specified
    if vibrato_rate_hz > 0.0 and vibrato_depth_semitones > 0.0:
        t_sec = np.arange(duration_samples) / sample_rate
        # Delay onset slightly for natural vibrato
        onset_envelope = np.clip((time_ratios - 0.2) / 0.3, 0.0, 1.0)
        vibrato_st = vibrato_depth_semitones * np.sin(2.0 * np.pi * vibrato_rate_hz * t_sec) * onset_envelope
        f0_curve = f0_curve * (2.0 ** (vibrato_st / 12.0))

    return np.clip(f0_curve, 30.0, 4000.0).astype(np.float32)


def generate_volume_envelope(
    duration_samples: int,
    sample_rate: int,
    volume_envelope_pts: Optional[List[Tuple[float, float]]] = None,
    default_volume_db: float = 0.0,
    attack_ms: float = 8.0,
    release_ms: float = 12.0,
) -> np.ndarray:
    """
    Generates a linear amplitude multiplier array (0.0 to 2.0) from dB envelope specifications.
    """
    if duration_samples <= 0:
        return np.array([], dtype=np.float32)

    time_ratios = np.linspace(0.0, 1.0, duration_samples, endpoint=True)
    
    # Base envelope in dB
    db_curve = np.full(duration_samples, default_volume_db, dtype=np.float64)

    if volume_envelope_pts and len(volume_envelope_pts) >= 2:
        pts = sorted(volume_envelope_pts, key=lambda p: p[0])
        x_pts = [max(0.0, min(1.0, float(p[0]))) for p in pts]
        y_pts = [float(p[1]) for p in pts]

        if x_pts[0] > 0.0:
            x_pts.insert(0, 0.0)
            y_pts.insert(0, y_pts[0])
        if x_pts[-1] < 1.0:
            x_pts.append(1.0)
            y_pts.append(y_pts[-1])

        unique_x, unique_indices = np.unique(x_pts, return_index=True)
        unique_y = [y_pts[i] for i in unique_indices]

        if len(unique_x) >= 3:
            interpolator = PchipInterpolator(unique_x, unique_y)
        else:
            interpolator = interp1d(unique_x, unique_y, kind="linear", fill_value="extrapolate")

        db_curve = interpolator(time_ratios) + default_volume_db

    # Convert dB to linear amplitude: gain = 10^(dB / 20)
    linear_gain = 10.0 ** (np.clip(db_curve, -60.0, 12.0) / 20.0)

    # Smooth attack and release edges to prevent audio clicks
    attack_samples = max(1, int((attack_ms / 1000.0) * sample_rate))
    release_samples = max(1, int((release_ms / 1000.0) * sample_rate))

    if attack_samples < duration_samples:
        attack_ramp = 0.5 * (1.0 - np.cos(np.linspace(0, np.pi, attack_samples)))
        linear_gain[:attack_samples] *= attack_ramp

    if release_samples < duration_samples:
        release_ramp = 0.5 * (1.0 + np.cos(np.linspace(0, np.pi, release_samples)))
        linear_gain[-release_samples:] *= release_ramp

    return linear_gain.astype(np.float32)
