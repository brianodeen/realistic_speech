"""
Bioacoustic Physical Synthesis Engine for Animal and Creature Vocalizations.
Simulates feline (purrs, growls, hisses, chitters) and canine (snarls, barks, whines, howls) mechanics.
"""

import numpy as np
from scipy import signal
from typing import Dict, Any, Optional, Tuple


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
    both egressive (exhale) and ingressive (inhale) airflows.
    """
    t = np.arange(duration_samples) / float(sample_rate)
    
    # 1. Purr twitch modulation oscillator (24 Hz) with slight natural jitter
    jitter = 1.0 + 0.03 * np.sin(2.0 * np.pi * 1.5 * t)
    twitch_phase = (2.0 * np.pi * rate_hz * jitter * t)
    
    # Asymmetric twitch pulse (rapid opening, slower damping)
    twitch_envelope = 0.5 * (1.0 - np.cos(twitch_phase)) ** 2
    
    # 2. Respiration cycle (alternating inhale/exhale every ~1.2 seconds)
    resp_rate = 0.8  # Hz
    resp_cycle = np.sin(2.0 * np.pi * resp_rate * t)
    is_inhale = resp_cycle < 0.0
    
    # Inhale has slightly higher harmonic frequency and more turbulence
    inhale_mod = np.where(is_inhale, 1.15, 1.0)
    
    # 3. Acoustic core: Glottal rumble source + low turbulent noise
    f0_rumble = base_resonance_hz * inhale_mod
    rumble_harmonics = (
        np.sin(2.0 * np.pi * (f0_rumble * 0.25) * t) * 0.8 +
        np.sin(2.0 * np.pi * (f0_rumble * 0.5) * t) * 0.6 +
        np.sin(2.0 * np.pi * f0_rumble * t) * 0.4
    )
    
    # Low-frequency chest noise
    noise = np.random.randn(duration_samples)
    b_lp, a_lp = signal.butter(2, min(800.0 / (sample_rate / 2.0), 0.9), btype="low")
    filtered_noise = signal.lfilter(b_lp, a_lp, noise)
    
    # Combine rumble and noise, gated by the 24Hz twitch envelope
    purr_audio = (rumble_harmonics * 0.6 + filtered_noise * 0.4) * (1.0 - depth + depth * twitch_envelope)
    
    # Resonance bandpass filter at cat chest cavity (~180-450 Hz)
    b_bp, a_bp = signal.butter(2, [120.0 / (sample_rate / 2.0), min(600.0 / (sample_rate / 2.0), 0.95)], btype="band")
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
    Synthesizes a deep feline guttural throat growl.
    Combines low vocal fold vibration with strong false vocal cord (ventricular) modulation,
    pharyngeal friction, and subharmonics at F0/2 and F0/3.
    """
    t = np.arange(duration_samples) / float(sample_rate)
    
    # Low pitch with slow menacing frequency rise and fall
    f0_envelope = base_f0 * (1.0 + 0.15 * np.sin(2.0 * np.pi * (1.2 / (duration_samples / sample_rate)) * t))
    phase = np.cumsum(f0_envelope / sample_rate)
    
    # Fundamental + subharmonic F0/2 (octave below) + F0/3
    sub1_phase = 0.5 * phase
    sub2_phase = 0.333 * phase
    
    # Saturated vocal cords (clipping gives harsh guttural texture)
    cords = (
        np.sin(2.0 * np.pi * phase) * 0.6 +
        np.sin(2.0 * np.pi * sub1_phase) * subharmonic_depth * 0.7 +
        np.sin(2.0 * np.pi * sub2_phase) * subharmonic_depth * 0.4
    )
    cords_saturated = np.tanh(cords * (2.0 + 3.0 * intensity))
    
    # Pharyngeal turbulence noise
    noise = np.random.randn(duration_samples)
    b_hp, a_hp = signal.butter(2, min(900.0 / (sample_rate / 2.0), 0.9), btype="high")
    throat_friction = signal.lfilter(b_hp, a_hp, noise) * 0.35 * intensity
    
    # Modulate throat friction with subharmonic pulse
    throat_friction *= (0.5 + 0.5 * np.abs(cords_saturated))
    
    combined = cords_saturated + throat_friction
    
    # Resonant filter for feline pharyngeal throat chamber (resonances at 350, 950, 2200 Hz)
    b_reso, a_reso = signal.butter(2, [200.0 / (sample_rate / 2.0), min(2800.0 / (sample_rate / 2.0), 0.95)], btype="band")
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
    
    # Attack and release envelope: fast sharp rise, sustained plateau, decay
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
    Synthesizes an aggressive canine snarl.
    Upper lip retraction brightens formants; laryngeal/palatal flutter creates rapid roughness.
    """
    t = np.arange(duration_samples) / float(sample_rate)
    
    # Rapid mucosal flutter (45-55 Hz amplitude and frequency modulation)
    flutter = 0.5 * (1.0 + np.sin(2.0 * np.pi * flutter_hz * t))
    
    # Pitch modulation with flutter
    f0_track = base_f0 * (1.0 + 0.25 * (flutter - 0.5))
    phase = np.cumsum(f0_track / sample_rate)
    
    # Rich harmonic spectrum
    harmonics = (
        np.sin(2.0 * np.pi * phase) * 1.0 +
        np.sin(2.0 * np.pi * 2.0 * phase) * 0.7 +
        np.sin(2.0 * np.pi * 3.0 * phase) * 0.5 +
        np.sin(2.0 * np.pi * 4.0 * phase) * 0.3
    )
    
    # Canine muzzle lip-curl resonance (brightens upper mids 1.5 - 3.5 kHz)
    noise = np.random.randn(duration_samples)
    b_curl, a_curl = signal.butter(2, [min(1400.0 / (sample_rate / 2.0), 0.85), min(3800.0 / (sample_rate / 2.0), 0.95)], btype="band")
    curl_noise = signal.lfilter(b_curl, a_curl, noise) * 0.4
    
    snarl_raw = (harmonics * (1.0 - roughness * 0.5 + roughness * flutter) + curl_noise)
    
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
    
    # Dynamic arching pitch contour
    f0_track = base_f0 * (1.0 + (glide_slope - 1.0) * np.sin(np.pi * time_ratio))
    
    # Subtle micro-jitter (submissive trembling)
    tremble = 1.0 + 0.02 * np.sin(2.0 * np.pi * 8.5 * t)
    phase = np.cumsum((f0_track * tremble) / sample_rate)
    
    # Pure falsetto harmonic series
    whine_audio = (
        np.sin(2.0 * np.pi * phase) * 0.8 +
        np.sin(2.0 * np.pi * 2.0 * phase) * 0.35 +
        np.sin(2.0 * np.pi * 3.0 * phase) * 0.15
    )
    
    max_val = np.max(np.abs(whine_audio)) + 1e-6
    return (whine_audio / max_val).astype(np.float32)
