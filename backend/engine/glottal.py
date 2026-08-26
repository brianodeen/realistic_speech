"""
Glottal Excitation and Phonation Source Engine.
Generates glottal volume velocity waveforms using the Rosenberg/LF model,
vocal fry / creak subharmonics, breathiness turbulence, and whisper sources.
"""

import numpy as np
from scipy import signal
from typing import Optional


def rosenberg_pulse(phase: np.ndarray, open_quotient: float = 0.6, speed_quotient: float = 1.6) -> np.ndarray:
    """
    Computes Rosenberg trigonometric glottal pulse waveform over normalized phase [0.0, 1.0).
    Phase: 0 to open_quotient is open phase; open_quotient to 1.0 is closed phase.
    """
    pulse = np.zeros_like(phase, dtype=np.float64)
    
    # Opening phase: 0 <= t < t_p
    # Closing phase: t_p <= t < t_e (where t_e = open_quotient)
    # Closed phase: t_e <= t < 1.0
    t_p = open_quotient / (1.0 + (1.0 / speed_quotient))
    
    # Mask 1: Opening
    mask_open = (phase < t_p)
    if np.any(mask_open):
        pulse[mask_open] = 0.5 * (1.0 - np.cos(np.pi * phase[mask_open] / t_p))
        
    # Mask 2: Closing
    mask_close = (phase >= t_p) & (phase < open_quotient)
    if np.any(mask_close):
        pulse[mask_close] = np.cos(0.5 * np.pi * (phase[mask_close] - t_p) / (open_quotient - t_p))
        
    # Closed phase is zero
    return pulse


def generate_glottal_source(
    f0_curve: np.ndarray,
    sample_rate: int,
    phonation: str = "modal",
    breathiness: float = 0.05,
    vocal_fry: float = 0.0,
    growl_roughness: float = 0.0,
) -> np.ndarray:
    """
    Generates time-domain glottal excitation audio array driven by time-varying f0_curve.
    """
    num_samples = len(f0_curve)
    if num_samples == 0:
        return np.array([], dtype=np.float32)

    # 1. Pure Whisper Mode (no periodic vocal fold vibration)
    if phonation == "whisper":
        white_noise = np.random.randn(num_samples)
        # Apply pink/aspiration filter (gentle lowpass at 4 kHz)
        b, a = signal.butter(2, min(4000.0 / (sample_rate / 2.0), 0.95), btype="low")
        whisper_audio = signal.lfilter(b, a, white_noise)
        return (whisper_audio / (np.max(np.abs(whisper_audio)) + 1e-6)).astype(np.float32)

    # 2. Phase accumulation for continuous variable F0
    # Phase increments delta_phi = f0(t) / Fs
    phase_increments = f0_curve / float(sample_rate)
    
    # Add subtle pitch jitter (0.5% natural micro-fluctuations)
    jitter = 1.0 + (np.random.randn(num_samples) * 0.005)
    accumulated_phase = np.cumsum(phase_increments * jitter) % 1.0

    # Phonation-dependent open quotient and characteristics
    if phonation == "breathy":
        open_q = 0.82
        aspiration_mix = max(0.25, breathiness)
    elif phonation == "creaky" or vocal_fry > 0.3:
        open_q = 0.35
        aspiration_mix = 0.02
    elif phonation == "falsetto":
        open_q = 0.75
        aspiration_mix = 0.04
    elif phonation == "ventricular_growl" or growl_roughness > 0.2:
        open_q = 0.55
        aspiration_mix = 0.15
    else:  # modal
        open_q = 0.60
        aspiration_mix = breathiness

    # Compute base glottal pulses
    glottal_pulses = rosenberg_pulse(accumulated_phase, open_quotient=open_q)

    # 3. Handle Vocal Fry / Creak Subharmonics
    if phonation == "creaky" or vocal_fry > 0.0:
        fry_amount = 0.8 if phonation == "creaky" else vocal_fry
        # Subharmonic pulse at half frequency (F0 / 2)
        subharmonic_phase = (np.cumsum(0.5 * phase_increments) % 1.0)
        sub_pulse = rosenberg_pulse(subharmonic_phase, open_quotient=0.3)
        # Alternate amplitude attenuation every other cycle
        cycle_indexer = np.floor(np.cumsum(phase_increments)).astype(int) % 2
        glottal_pulses = glottal_pulses * (1.0 - fry_amount * 0.5 * cycle_indexer) + (sub_pulse * fry_amount * 0.4)

    # 4. Handle Ventricular Growl (False Vocal Cord Oscillation)
    if phonation == "ventricular_growl" or growl_roughness > 0.0:
        growl_intensity = 0.85 if phonation == "ventricular_growl" else growl_roughness
        # Ventricular false cord phase at F0 / 2 + subharmonic F0 / 3
        v_phase_1 = (np.cumsum(0.5 * phase_increments) % 1.0)
        v_phase_2 = (np.cumsum(0.333 * phase_increments) % 1.0)
        
        # False cord pulse is squarish and turbulent
        v_pulse = (np.sin(2.0 * np.pi * v_phase_1) * 0.6) + (np.sin(2.0 * np.pi * v_phase_2) * 0.4)
        v_pulse = np.clip(v_pulse * 1.5, -1.0, 1.0)
        
        # Invert and modulate glottal flow
        glottal_pulses = glottal_pulses * (1.0 + v_pulse * growl_intensity * 0.6)

    # 5. Differentiate to get Glottal Volume Velocity Derivative (standard speech acoustics)
    # Derivative adds +6dB/octave high-frequency boost, typical of natural glottal radiation
    glottal_deriv = np.diff(glottal_pulses, prepend=glottal_pulses[0])

    # 6. Inject Aspiration Turbulence / Breathy Noise
    if aspiration_mix > 0.0:
        noise = np.random.randn(num_samples)
        # Highpass noise above 1.5 kHz for natural glottal aspiration
        b_noise, a_noise = signal.butter(2, min(1500.0 / (sample_rate / 2.0), 0.9), btype="high")
        filtered_noise = signal.lfilter(b_noise, a_noise, noise)
        
        # Amplitude-modulate noise with open phase of glottal pulse
        noise_mod = filtered_noise * (0.5 + 0.5 * glottal_pulses) * aspiration_mix * 0.8
        source_audio = glottal_deriv + noise_mod
    else:
        source_audio = glottal_deriv

    # Normalize source
    max_val = np.max(np.abs(source_audio)) + 1e-6
    return (source_audio / max_val).astype(np.float32)
