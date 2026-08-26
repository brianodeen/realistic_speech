"""
Time-Varying Vocal Tract Formant Filter Engine.
Implements digital resonator filter cascades (F1 to F5), nasal antiresonance poles/zeros,
and vocal tract scaling (human vs feline vs canine muzzle elongation).
"""

import numpy as np
from scipy import signal
from typing import List, Tuple, Optional


def compute_biquad_resonator(f_res: float, bandwidth: float, sample_rate: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Computes digital 2nd-order IIR biquad bandpass resonator coefficients (b, a)
    centered at resonant frequency f_res with specified -3dB bandwidth.
    """
    nyquist = sample_rate / 2.0
    f_res = max(40.0, min(f_res, nyquist - 100.0))
    bandwidth = max(20.0, min(bandwidth, nyquist / 2.0))
    
    omega = 2.0 * np.pi * f_res / sample_rate
    # Radius r based on bandwidth: r = exp(-pi * BW / Fs)
    r = np.exp(-np.pi * bandwidth / sample_rate)
    
    # Denominator: 1 - 2*r*cos(omega)*z^-1 + r^2*z^-2
    a1 = -2.0 * r * np.cos(omega)
    a2 = r * r
    a = np.array([1.0, a1, a2], dtype=np.float64)
    
    # Numerator normalized for 0dB gain at resonant center
    # Gain factor = (1 - r) * sqrt(1 - 2*r*cos(2*omega) + r^2)
    b0 = (1.0 - r) * np.sin(omega)
    b = np.array([b0, 0.0, -b0], dtype=np.float64)
    
    return b, a


def apply_formant_cascade(
    excitation_audio: np.ndarray,
    formants: List[float],
    bandwidths: List[float],
    sample_rate: int,
    vocal_tract_scale: float = 1.0,
    nasal: bool = False,
) -> np.ndarray:
    """
    Filters excitation audio through a parallel/cascade bank of 5 formant resonators.
    vocal_tract_scale: < 1.0 increases formant frequencies (smaller/feline head),
                       > 1.0 decreases formant frequencies (longer canine muzzle/chest).
    """
    if len(excitation_audio) == 0 or len(formants) == 0:
        return excitation_audio

    # Scale formants inversely with vocal tract length: F_scaled = F / scale
    effective_scale = max(0.5, min(2.0, vocal_tract_scale))
    scaled_formants = [f / effective_scale for f in formants]
    scaled_bandwidths = [bw for bw in bandwidths]

    # Formant relative gains (F1 strongest, rolling off ~ -6dB per formant)
    formant_gains = [1.0, 0.65, 0.35, 0.18, 0.08]

    filtered_output = np.zeros_like(excitation_audio, dtype=np.float64)

    for i, (f_res, bw) in enumerate(zip(scaled_formants, scaled_bandwidths)):
        if i >= len(formant_gains):
            break
        b, a = compute_biquad_resonator(f_res, bw, sample_rate)
        # Filter excitation through this formant resonator
        formant_wave = signal.lfilter(b, a, excitation_audio)
        filtered_output += formant_wave * formant_gains[i]

    # If nasalized, add low nasal murmur resonance (~250Hz) and antiresonance dip (~800Hz)
    if nasal:
        b_nasal, a_nasal = compute_biquad_resonator(260.0 / effective_scale, 80.0, sample_rate)
        nasal_wave = signal.lfilter(b_nasal, a_nasal, excitation_audio)
        filtered_output = filtered_output * 0.7 + nasal_wave * 0.5

    # Lip radiation impedance model: highpass filter +6dB/octave (or 1st order zero)
    # Radiates into open 3D air
    b_rad = np.array([1.0, -0.92], dtype=np.float64)
    a_rad = np.array([1.0], dtype=np.float64)
    radiated_audio = signal.lfilter(b_rad, a_rad, filtered_output)

    return radiated_audio.astype(np.float32)


def smooth_formant_trajectory(
    formant_start: List[float],
    formant_end: List[float],
    duration_samples: int,
) -> np.ndarray:
    """
    Generates a smoothly interpolated matrix of formants (5 x duration_samples) for coarticulation.
    """
    t = np.linspace(0.0, 1.0, duration_samples)
    traj = np.zeros((5, duration_samples), dtype=np.float32)
    for i in range(5):
        f_s = formant_start[i] if i < len(formant_start) else 3500.0
        f_e = formant_end[i] if i < len(formant_end) else 3500.0
        # Cosine s-curve interpolation
        traj[i, :] = f_s + (f_e - f_s) * 0.5 * (1.0 - np.cos(np.pi * t))
    return traj
