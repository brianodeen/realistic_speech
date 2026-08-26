"""
Organic Viscoelastic Mucosal Glottal Model.
Simulates soft fleshy vocal fold collision (LF model with Ta return phase),
1/f biomechanical jitter & shimmer, mucosal vortex turbulence, and fleshy spectral tilt.
"""

import numpy as np
from scipy import signal
from typing import Optional


def lf_glottal_derivative(
    phase: np.ndarray,
    open_quotient: float = 0.65,
    return_quotient: float = 0.12,
    fleshiness: float = 0.70,
) -> np.ndarray:
    """
    Computes organic Liljencrants-Fant (LF) inspired glottal volume velocity derivative.
    return_quotient (Ta/T0): models the viscoelastic soft tissue collision duration.
    Higher fleshiness increases Ta, rolling off metallic high frequencies into warm body tone.
    """
    t = phase % 1.0
    pulse = np.zeros_like(t, dtype=np.float64)

    # Effective parameters scaled by fleshiness
    # More fleshiness -> longer soft return phase and smoother mucosal opening
    t_e = max(0.40, min(0.85, open_quotient))  # Point of maximum glottal closure rate
    t_p = t_e * 0.65                           # Peak flow moment
    t_a = max(0.04, return_quotient * (0.6 + 0.8 * fleshiness))  # Return phase length

    # 1. Opening Phase (0 <= t < t_e): Exponentially growing sinusoidal flow derivative
    mask_open = (t < t_e)
    if np.any(mask_open):
        t_o = t[mask_open]
        # Smooth mucosal opening curve (E0 * e^(alpha * t) * sin(omega * t))
        alpha = 1.2 * (1.0 - 0.5 * fleshiness)
        omega = np.pi / t_e
        pulse[mask_open] = -np.exp(alpha * (t_o / t_e)) * np.sin(omega * t_o)

    # 2. Return / Mucosal Flattening Phase (t_e <= t < t_e + t_a * 3): Exponential damping
    mask_return = (t >= t_e)
    if np.any(mask_return):
        t_r = t[mask_return] - t_e
        # Exponential recovery back to baseline as folds press together
        decay_rate = 1.0 / t_a
        # Match continuity at t_e: pulse[t_e] = -e^alpha * sin(pi) -> 0
        peak_closing_rate = -np.exp(1.2 * (1.0 - 0.5 * fleshiness))
        pulse[mask_return] = peak_closing_rate * np.exp(-decay_rate * t_r) * (1.0 - np.exp(-t_r * 40.0))

    return pulse


def generate_glottal_source(
    f0_curve: np.ndarray,
    sample_rate: int,
    phonation: str = "modal",
    breathiness: float = 0.05,
    vocal_fry: float = 0.0,
    growl_roughness: float = 0.0,
    fleshiness: float = 0.70,
) -> np.ndarray:
    """
    Generates an organic, warm glottal excitation waveform with soft tissue physics,
    1/f micro-perturbations (jitter/shimmer), and anti-metallic spectral roll-off.
    """
    num_samples = len(f0_curve)
    if num_samples == 0:
        return np.array([], dtype=np.float32)

    # 1. Pure Whisper Mode
    if phonation == "whisper":
        white_noise = np.random.randn(num_samples)
        # Soft vocal tract acoustic noise shaping
        b, a = signal.butter(2, min(3200.0 / (sample_rate / 2.0), 0.90), btype="low")
        whisper_audio = signal.lfilter(b, a, white_noise)
        return (whisper_audio / (np.max(np.abs(whisper_audio)) + 1e-6)).astype(np.float32)

    # 2. Continuous Phase Accumulation with Pink/1f Biomechanical Micro-Jitter
    phase_increments = f0_curve / float(sample_rate)

    # Generate smooth 1/f chaotic micro-jitter (natural vocal fold oscillation drift)
    raw_jitter_noise = np.random.randn(num_samples)
    b_j, a_j = signal.butter(1, min(30.0 / (sample_rate / 2.0), 0.5), btype="low")
    smooth_jitter = signal.lfilter(b_j, a_j, raw_jitter_noise)
    jitter_factor = 1.0 + (smooth_jitter * 0.012 * (1.0 + 0.5 * fleshiness))

    accumulated_phase = np.cumsum(phase_increments * jitter_factor) % 1.0

    # 3. Phonation Mode Open Quotients & Soft Tissue Parameters
    if phonation == "breathy":
        open_q = 0.80
        ret_q = 0.18
        aspiration_mix = max(0.20, breathiness)
    elif phonation == "creaky" or vocal_fry > 0.2:
        open_q = 0.38
        ret_q = 0.08
        aspiration_mix = 0.03
    elif phonation == "falsetto":
        open_q = 0.72
        ret_q = 0.22
        aspiration_mix = 0.04
    elif phonation == "ventricular_growl" or growl_roughness > 0.2:
        open_q = 0.58
        ret_q = 0.14
        aspiration_mix = 0.14
    else:  # modal
        open_q = 0.65
        ret_q = 0.12
        aspiration_mix = max(0.04, breathiness)

    # 4. Generate LF Glottal Velocity Derivative Waveform
    glottal_pulses = lf_glottal_derivative(
        phase=accumulated_phase,
        open_quotient=open_q,
        return_quotient=ret_q,
        fleshiness=fleshiness,
    )

    # 5. Apply Natural Vocal Fold Shimmer (Cycle-to-Cycle Amplitude Modulation)
    raw_shimmer = np.random.randn(num_samples)
    b_s, a_s = signal.butter(1, min(25.0 / (sample_rate / 2.0), 0.5), btype="low")
    smooth_shimmer = signal.lfilter(b_s, a_s, raw_shimmer)
    shimmer_factor = 1.0 + (smooth_shimmer * 0.03)
    glottal_pulses *= shimmer_factor

    # 6. Handle Vocal Fry / Subharmonic Creak
    if phonation == "creaky" or vocal_fry > 0.0:
        fry_amount = 0.85 if phonation == "creaky" else vocal_fry
        sub_phase = (np.cumsum(0.5 * phase_increments) % 1.0)
        sub_pulse = lf_glottal_derivative(sub_phase, open_quotient=0.35, return_quotient=0.08, fleshiness=fleshiness)
        cycle_idx = np.floor(np.cumsum(phase_increments)).astype(int) % 2
        glottal_pulses = glottal_pulses * (1.0 - fry_amount * 0.45 * cycle_idx) + (sub_pulse * fry_amount * 0.4)

    # 7. Handle Ventricular Growl (False Vocal Cord Oscillation)
    if phonation == "ventricular_growl" or growl_roughness > 0.0:
        growl_int = 0.85 if phonation == "ventricular_growl" else growl_roughness
        v_phase_1 = (np.cumsum(0.5 * phase_increments) % 1.0)
        v_phase_2 = (np.cumsum(0.333 * phase_increments) % 1.0)
        v_pulse = (np.sin(2.0 * np.pi * v_phase_1) * 0.6) + (np.sin(2.0 * np.pi * v_phase_2) * 0.4)
        v_pulse = np.tanh(v_pulse * 1.8)
        glottal_pulses = glottal_pulses * (1.0 + v_pulse * growl_int * 0.65)

    # 8. Transglottal Vortex Turbulence (Mucosal Wetness & Air Flow)
    if aspiration_mix > 0.0:
        noise = np.random.randn(num_samples)
        # Shaped transglottal turbulent noise (concentrated 1.2kHz - 4.5kHz)
        nyq = sample_rate / 2.0
        b_turb, a_turb = signal.butter(2, [min(1000.0 / nyq, 0.8), min(4500.0 / nyq, 0.95)], btype="band")
        vortex_noise = signal.lfilter(b_turb, a_turb, noise)

        # Modulate turbulence with glottal opening phase
        open_mask = np.clip(-glottal_pulses, 0.0, 1.0)
        vortex_noise *= (0.3 + 0.7 * open_mask) * aspiration_mix * 0.5
        source_audio = glottal_pulses + vortex_noise
    else:
        source_audio = glottal_pulses

    # 9. Fleshy Spectral Tilt (Roll off metallic high harmonics)
    if fleshiness > 0.1:
        # 1st order soft-tissue damping lowpass shelf at 2.8kHz - 4.2kHz
        tilt_cutoff = 1800.0 + (1.0 - fleshiness) * 2800.0
        b_tilt, a_tilt = signal.butter(1, min(tilt_cutoff / (sample_rate / 2.0), 0.95), btype="low")
        source_audio = signal.lfilter(b_tilt, a_tilt, source_audio)

    # Normalize source
    max_val = np.max(np.abs(source_audio)) + 1e-6
    return (source_audio / max_val).astype(np.float32)
