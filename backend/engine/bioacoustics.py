"""
Bioacoustic Physical Synthesis Engine for Animal, Creature, and Non-Pulmonic Vocalizations.
Implements non-linear polynomial delay-differential chaos equations for true biological
subharmonic bifurcation (predator growls, purrs, canine snarls, barks, whines, howls, suction clicks, ejectives).
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

    delay_d = max(1, int(round(sample_rate / (2.0 * max(20.0, base_f0)))))
    output = np.zeros(n_samples, dtype=np.float64)

    delayed_pulse = np.zeros(n_samples, dtype=np.float64)
    if delay_d < n_samples:
        delayed_pulse[delay_d:] = pulse_signal[:-delay_d]

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
    
    twitch_phase = 2.0 * np.pi * rate_hz * t
    twitch_envelope = 0.5 * (1.0 - np.cos(twitch_phase)) ** 2
    
    resp_rate = 0.8  # Hz
    resp_cycle = np.sin(2.0 * np.pi * resp_rate * t)
    is_inhale = resp_cycle < 0.0
    inhale_mod = np.where(is_inhale, 1.12, 1.0)
    
    f0_rumble = base_resonance_hz * 0.25 * inhale_mod
    phase_r = np.cumsum(f0_rumble / sample_rate)
    raw_rumble = np.sin(2.0 * np.pi * phase_r)
    
    rumble_chaos = apply_delay_differential_chaos(
        raw_rumble, sample_rate, base_f0=float(np.mean(f0_rumble)),
        alpha=0.70, beta=0.55
    )
    
    noise = np.random.randn(duration_samples)
    b_lp, a_lp = signal.butter(2, min(750.0 / (sample_rate / 2.0), 0.9), btype="low")
    filtered_noise = signal.lfilter(b_lp, a_lp, noise)
    
    purr_audio = (rumble_chaos * 0.65 + filtered_noise * 0.35) * (1.0 - depth + depth * twitch_envelope)
    
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
    
    f0_envelope = base_f0 * (1.0 + 0.12 * np.sin(2.0 * np.pi * (1.0 / max(0.1, duration_samples / sample_rate)) * t))
    phase = np.cumsum(f0_envelope / sample_rate)
    
    primary_pulse = np.sin(2.0 * np.pi * phase)
    
    growl_chaos = apply_delay_differential_chaos(
        primary_pulse, sample_rate, base_f0=base_f0,
        alpha=0.90 * intensity, beta=0.75 * subharmonic_depth
    )
    
    noise = np.random.randn(duration_samples)
    b_hp, a_hp = signal.butter(2, min(950.0 / (sample_rate / 2.0), 0.9), btype="high")
    throat_friction = signal.lfilter(b_hp, a_hp, noise) * 0.35 * intensity
    
    throat_friction *= (0.4 + 0.6 * np.abs(growl_chaos))
    
    combined = growl_chaos + throat_friction
    
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
    
    nyquist = sample_rate / 2.0
    b_hiss, a_hiss = signal.butter(3, [min(3200.0 / nyquist, 0.85), min(7800.0 / nyquist, 0.95)], btype="band")
    hiss_audio = signal.lfilter(b_hiss, a_hiss, noise)
    
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
    
    flutter = 0.5 * (1.0 + np.sin(2.0 * np.pi * flutter_hz * t))
    f0_track = base_f0 * (1.0 + 0.20 * (flutter - 0.5))
    phase = np.cumsum(f0_track / sample_rate)
    
    base_pulse = np.sin(2.0 * np.pi * phase)
    
    snarl_chaos = apply_delay_differential_chaos(
        base_pulse, sample_rate, base_f0=base_f0,
        alpha=0.85 * roughness, beta=0.65 * roughness
    )
    
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
    """
    t = np.arange(duration_samples) / float(sample_rate)
    
    pitch_decay = np.exp(-t * 22.0)
    f0_track = base_f0 * (0.6 + 1.2 * pitch_decay)
    phase = np.cumsum(f0_track / sample_rate)
    
    burst_len = min(int(0.015 * sample_rate), duration_samples)
    impulse = np.zeros(duration_samples)
    impulse[:burst_len] = np.random.randn(burst_len) * np.linspace(1.0, 0.0, burst_len)
    
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
    
    tremble = 1.0 + 0.02 * np.sin(2.0 * np.pi * 8.5 * t)
    phase = np.cumsum((f0_track * tremble) / sample_rate)
    
    whine_audio = (
        np.sin(2.0 * np.pi * phase) * 0.8 +
        np.sin(2.0 * np.pi * 2.0 * phase) * 0.35 +
        np.sin(2.0 * np.pi * 3.0 * phase) * 0.15
    )
    
    max_val = np.max(np.abs(whine_audio)) + 1e-6
    return (whine_audio / max_val).astype(np.float32)


def synthesize_click_burst(
    symbol: str,
    duration_samples: int,
    sample_rate: int,
) -> np.ndarray:
    """
    Physically synthesizes an authentic lingual suction click (dental [ǀ], alveolar [ǃ],
    lateral [ǁ], or bilabial [ʘ]) as an impulse suction pop and cavitation burst.
    """
    sym = symbol.lower().strip()
    peak_freq_map = {
        "click_dental": 4800.0, "ǀ": 4800.0,
        "click_alveolar": 1600.0, "ǃ": 1600.0,
        "click_lateral": 2800.0, "ǁ": 2800.0,
        "click_bilabial": 950.0, "ʘ": 950.0,
    }
    peak_hz = peak_freq_map.get(sym, 2200.0)
    burst_samples = min(duration_samples, int(0.018 * sample_rate))
    
    # Asymmetric suction impulse: rapid cavitation spike followed by dampening
    t_burst = np.linspace(0.0, 1.0, burst_samples)
    impulse = np.exp(-t_burst * 22.0) * np.sin(2.0 * np.pi * peak_hz * (t_burst * burst_samples / sample_rate))
    noise_burst = np.random.randn(burst_samples) * np.exp(-t_burst * 16.0)
    
    nyq = sample_rate / 2.0
    b_click, a_click = signal.butter(2, [max(120.0, peak_hz - 600) / nyq, min(nyq - 100, peak_hz + 900) / nyq], btype="band")
    filtered_click = signal.lfilter(b_click, a_click, impulse * 0.8 + noise_burst * 0.4)
    
    output = np.zeros(duration_samples, dtype=np.float32)
    output[:burst_samples] = filtered_click * 1.5
    return output


def synthesize_ejective_burst(
    symbol: str,
    duration_samples: int,
    sample_rate: int,
) -> np.ndarray:
    """
    Physically synthesizes a glottalized ejective burst ([kʼ], [tʼ], [pʼ]).
    """
    sym = symbol.lower().strip()
    freq_map = {
        "ejective_k": 2400.0, "kʼ": 2400.0,
        "ejective_t": 3900.0, "tʼ": 3900.0,
        "ejective_p": 1200.0, "pʼ": 1200.0,
    }
    burst_hz = freq_map.get(sym, 2400.0)
    burst_samples = min(duration_samples, int(0.022 * sample_rate))
    
    t_burst = np.linspace(0.0, 1.0, burst_samples)
    impulse = np.random.randn(burst_samples) * np.exp(-t_burst * 14.0)
    
    nyq = sample_rate / 2.0
    b_ej, a_ej = signal.butter(2, [max(100.0, burst_hz - 400) / nyq, min(nyq - 100, burst_hz + 800) / nyq], btype="band")
    filtered_burst = signal.lfilter(b_ej, a_ej, impulse) * 1.6
    
    output = np.zeros(duration_samples, dtype=np.float32)
    output[:burst_samples] = filtered_burst
    return output
