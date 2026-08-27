"""
Bioacoustic Physical Synthesis Engine for Animal and Creature Vocalizations.
Implements non-linear polynomial delay-differential chaos equations for true biological
subharmonic bifurcation (predator growls, purrs, canine snarls, barks, whines, howls).
"""

import numpy as np
from scipy import signal
from typing import Dict, Any, Optional, Tuple


def apply_delay_differential_chaos(
    pulse_signal: np.ndarray,
    sample_rate: int,
    base_f0: float,
    alpha: float = 0.85,
    beta: float = 0.65,
) -> np.ndarray:
    """
    Implements Section 3.1 Non-Linear Polynomial Delay-Differential Chaos:
    s_source[n] = (1 - beta)*s_pulse[n] + beta*(s_pulse[n] + alpha * s_pulse[n - D] * |s_pulse[n]|)
    
    Where D = round(Fs / (2 * F0)) produces subharmonic bifurcation (f0/2, f0/3)
    and authentic physical mucosal vortex shedding.
    """
    n_samples = len(pulse_signal)
    if n_samples == 0:
        return pulse_signal

    # Subharmonic delay period (half fundamental cycle)
    delay_d = max(1, int(round(sample_rate / (2.0 * max(20.0, base_f0)))))
    output = np.zeros(n_samples, dtype=np.float64)

    delayed_pulse = np.zeros(n_samples, dtype=np.float64)
    if delay_d < n_samples:
        delayed_pulse[delay_d:] = pulse_signal[:-delay_d]

    # Non-linear quadratic coupling
    chaos_term = pulse_signal + alpha * delayed_pulse * np.abs(pulse_signal)
    output = (1.0 - beta) * pulse_signal + beta * chaos_term

    return np.tanh(output * 1.5).astype(np.float32)


def synthesize_feline_purr(
    duration_samples: int,
    sample_rate: int,
    rate_hz: float = 24.5,
    depth: float = 0.85,
    base_resonance_hz: float = 320.0,
) -> np.ndarray:
    """
    Synthesizes a feline rhythmic neural purr.
    Cats purr via a 20-30Hz laryngeal neural twitch oscillator that gates
    both egressive (exhale) and ingressive (inhale) airflows with subharmonic rumble.
    """
    t = np.arange(duration_samples) / float(sample_rate)
    
    # 1. Purr twitch modulation oscillator (24.5 Hz)
    twitch_phase = 2.0 * np.pi * rate_hz * t
    twitch_envelope = 0.5 * (1.0 - np.cos(twitch_phase)) ** 2
    
    # 2. Respiration cycle (alternating inhale/exhale every ~1.2 seconds)
    resp_rate = 0.8  # Hz
    resp_cycle = np.sin(2.0 * np.pi * resp_rate * t)
    is_inhale = resp_cycle < 0.0
    inhale_mod = np.where(is_inhale, 1.12, 1.0)
    
    # 3. Glottal rumble pulse train
    f0_rumble = base_resonance_hz * 0.25 * inhale_mod
    phase_r = np.cumsum(f0_rumble / sample_rate)
    raw_rumble = np.sin(2.0 * np.pi * phase_r)
    
    # Apply subharmonic chaos for low purr rumble
    rumble_chaos = apply_delay_differential_chaos(
        raw_rumble, sample_rate, base_f0=float(np.mean(f0_rumble)),
        alpha=0.70, beta=0.55
    )
    
    # Low-frequency chest noise
    noise = np.random.randn(duration_samples)
    b_lp, a_lp = signal.butter(2, min(750.0 / (sample_rate / 2.0), 0.9), btype="low")
    filtered_noise = signal.lfilter(b_lp, a_lp, noise)
    
    purr_audio = (rumble_chaos * 0.65 + filtered_noise * 0.35) * (1.0 - depth + depth * twitch_envelope)
    
    # Resonance bandpass filter at cat chest cavity (~160-480 Hz)
    b_bp, a_bp = signal.butter(2, [130.0 / (sample_rate / 2.0), min(550.0 / (sample_rate / 2.0), 0.95)], btype="band")
    purr_filtered = signal.lfilter(b_bp, a_bp, purr_audio)
    
    max_val = np.max(np.abs(purr_filtered)) + 1e-6
    return (purr_filtered / max_val).astype(np.float32)


def synthesize_feline_growl(
    duration_samples: int,
    sample_rate: int,
    base_f0: float = 110.0,
    intensity: float = 0.85,
    subharmonic_depth: float = 0.75,
) -> np.ndarray:
    """
    Synthesizes a deep feline guttural throat growl using non-linear
    polynomial delay-differential chaos and false-vocal-cord resonance.
    """
    t = np.arange(duration_samples) / float(sample_rate)
    
    # Menacing pitch rise and fall contour
    f0_envelope = base_f0 * (1.0 + 0.12 * np.sin(2.0 * np.pi * (1.0 / max(0.1, duration_samples / sample_rate)) * t))
    phase = np.cumsum(f0_envelope / sample_rate)
    
    # Primary vocal cord pulse
    primary_pulse = np.sin(2.0 * np.pi * phase)
    
    # Non-linear delay differential chaos (generates true physical subharmonic bifurcation)
    growl_chaos = apply_delay_differential_chaos(
        primary_pulse, sample_rate, base_f0=base_f0,
        alpha=0.90 * intensity, beta=0.75 * subharmonic_depth
    )
    
    # Pharyngeal turbulence noise
    noise = np.random.randn(duration_samples)
    b_hp, a_hp = signal.butter(2, min(950.0 / (sample_rate / 2.0), 0.9), btype="high")
    throat_friction = signal.lfilter(b_hp, a_hp, noise) * 0.35 * intensity
    
    # Modulate throat friction with chaotic pulses
    throat_friction *= (0.4 + 0.6 * np.abs(growl_chaos))
    
    combined = growl_chaos + throat_friction
    
    # Resonant filter for feline pharyngeal throat chamber (220 - 2600 Hz)
    b_reso, a_reso = signal.butter(2, [180.0 / (sample_rate / 2.0), min(2700.0 / (sample_rate / 2.0), 0.95)], btype="band")
    growl_audio = signal.lfilter(b_reso, a_reso, combined)
    
    max_val = np.max(np.abs(growl_audio)) + 1e-6
    return (growl_audio / max_val).astype(np.float32)


def synthesize_feline_hiss(
    duration_samples: int,
    sample_rate: int,
    intensity: float = 0.9,
) -> np.ndarray:
    """
    Synthesizes a sharp feline defensive hiss.
    Velic and pharyngeal turbulent jet with tongue arching and high-frequency resonance.
    """
    noise = np.random.randn(duration_samples)
    
    # Dual-peak bandpass filter (feline hiss concentrates energy around 3.5kHz - 7.5kHz)
    nyquist = sample_rate / 2.0
    b_hiss, a_hiss = signal.butter(3, [min(3200.0 / nyquist, 0.85), min(7800.0 / nyquist, 0.95)], btype="band")
    hiss_audio = signal.lfilter(b_hiss, a_hiss, noise)
    
    t_norm = np.linspace(0.0, 1.0, duration_samples)
    env = np.ones(duration_samples)
    attack_len = int(0.08 * duration_samples)
    decay_len = int(0.25 * duration_samples)
    if attack_len > 0:
        env[:attack_len] = np.sin(np.linspace(0, np.pi/2, attack_len))
    if decay_len > 0:
        env[-decay_len:] = np.cos(np.linspace(0, np.pi/2, decay_len))
        
    hiss_audio = hiss_audio * env * intensity
    max_val = np.max(np.abs(hiss_audio)) + 1e-6
    return (hiss_audio / max_val).astype(np.float32)


def synthesize_canine_snarl(
    duration_samples: int,
    sample_rate: int,
    base_f0: float = 130.0,
    flutter_hz: float = 48.0,
    roughness: float = 0.85,
) -> np.ndarray:
    """
    Synthesizes an aggressive canine snarl using mucosal flutter and delay chaos.
    """
    t = np.arange(duration_samples) / float(sample_rate)
    
    # Rapid mucosal flutter (45-55 Hz amplitude and frequency modulation)
    flutter = 0.5 * (1.0 + np.sin(2.0 * np.pi * flutter_hz * t))
    
    f0_track = base_f0 * (1.0 + 0.20 * (flutter - 0.5))
    phase = np.cumsum(f0_track / sample_rate)
    
    base_pulse = np.sin(2.0 * np.pi * phase)
    
    # Apply delay differential chaos
    snarl_chaos = apply_delay_differential_chaos(
        base_pulse, sample_rate, base_f0=base_f0,
        alpha=0.85 * roughness, beta=0.65 * roughness
    )
    
    # Canine muzzle lip-curl resonance (brightens upper mids 1.5 - 3.5 kHz)
    noise = np.random.randn(duration_samples)
    b_curl, a_curl = signal.butter(2, [min(1400.0 / (sample_rate / 2.0), 0.85), min(3800.0 / (sample_rate / 2.0), 0.95)], btype="band")
    curl_noise = signal.lfilter(b_curl, a_curl, noise) * 0.4
    
    snarl_raw = (snarl_chaos * (1.0 - roughness * 0.4 + roughness * flutter * 0.8) + curl_noise)
    
    max_val = np.max(np.abs(snarl_raw)) + 1e-6
    return (snarl_raw / max_val).astype(np.float32)


def synthesize_canine_bark(
    duration_samples: int,
    sample_rate: int,
    base_f0: float = 240.0,
) -> np.ndarray:
    """
    Synthesizes a short, punchy canine chest-impact warning bark.
    Sudden acoustic impulse followed by rapidly decaying pitch and formant resonance.
    """
    t = np.arange(duration_samples) / float(sample_rate)
    
    # Rapid downward pitch sweep (e.g. 380 Hz down to 120 Hz in 80ms)
    pitch_decay = np.exp(-t * 22.0)
    f0_track = base_f0 * (0.6 + 1.2 * pitch_decay)
    phase = np.cumsum(f0_track / sample_rate)
    
    # Impact transient at t=0
    burst_len = min(int(0.015 * sample_rate), duration_samples)
    impulse = np.zeros(duration_samples)
    impulse[:burst_len] = np.random.randn(burst_len) * np.linspace(1.0, 0.0, burst_len)
    
    # Resonant body decay
    body_decay = np.exp(-t * 14.0)
    body = np.sin(2.0 * np.pi * phase) * body_decay
    
    bark_audio = impulse * 0.6 + body * 0.8
    max_val = np.max(np.abs(bark_audio)) + 1e-6
    return (bark_audio / max_val).astype(np.float32)


def synthesize_canine_whine(
    duration_samples: int,
    sample_rate: int,
    base_f0: float = 1400.0,
    glide_slope: float = 1.3,
) -> np.ndarray:
    """
    Synthesizes a high-register canine whine / whimpering pitch glide.
    """
    t = np.arange(duration_samples) / float(sample_rate)
    time_ratio = t / (t[-1] + 1e-6)
    
    f0_track = base_f0 * (1.0 + (glide_slope - 1.0) * np.sin(np.pi * time_ratio))
    
    # Subtle micro-jitter (submissive trembling)
    tremble = 1.0 + 0.02 * np.sin(2.0 * np.pi * 8.5 * t)
    phase = np.cumsum((f0_track * tremble) / sample_rate)
    
    whine_audio = (
        np.sin(2.0 * np.pi * phase) * 0.8 +
        np.sin(2.0 * np.pi * 2.0 * phase) * 0.35 +
        np.sin(2.0 * np.pi * 3.0 * phase) * 0.15
    )
    
    max_val = np.max(np.abs(whine_audio)) + 1e-6
    return (whine_audio / max_val).astype(np.float32)
