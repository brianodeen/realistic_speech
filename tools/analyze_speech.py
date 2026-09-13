#!/usr/bin/env python3
"""
Speech Synthesis Realism & Roboticness Audio Analyzer
=====================================================
Analyzes speech recordings and conlang audio for acoustic realism, roboticness,
formant definition, pitch naturalness, clicks/artifacts, and bioacoustic features.

Zero external GUI dependencies: uses standard numpy, scipy, and soundfile.
"""

import sys
import os
import argparse
import json
import math
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import scipy.signal as signal
import soundfile as sf


@dataclass
class PitchMetrics:
    mean_f0_hz: float
    std_f0_hz: float
    min_f0_hz: float
    max_f0_hz: float
    pitch_range_semitones: float
    voiced_fraction: float
    declination_slope_hz_per_sec: float
    declination_total_drop_hz: float
    micro_prosody_depth_hz: float
    pitch_jumps_count: int
    pitch_smoothness_score: float  # 0 to 100


@dataclass
class HarmonicMetrics:
    mean_hnr_db: float
    spectral_tilt_db_oct: float
    spectral_flatness: float
    local_jitter_percent: float
    local_shimmer_percent: float
    harmonic_buzz_index: float  # 0 to 100 (higher = unnaturally buzzy/monotone)


@dataclass
class FormantMetrics:
    peak_to_valley_contrast_db: float
    formant_definition_score: float  # 0 to 100
    spectral_flux: float
    f1_mean_hz: float
    f2_mean_hz: float


@dataclass
class TransientMetrics:
    max_sample_delta: float
    kurtosis_hf: float
    click_count: int
    artifact_cleanliness_score: float  # 0 to 100


@dataclass
class RhythmMetrics:
    pairwise_variability_index: float     # nPVI: >38 = natural stress-timed, <22 = robotic metronome
    syllables_detected: int
    speaking_rate_syllables_per_sec: float
    intra_vowel_pitch_dynamics_hz: float  # Dynamic pitch movement within vowel nuclei
    rhythm_naturalness_score: float       # 0 to 100


@dataclass
class BioacousticMetrics:
    purr_modulation_hz: Optional[float]
    purr_prominence: float
    snarl_tremor_hz: Optional[float]
    snarl_prominence: float
    growl_subharmonic_ratio: float
    velaric_click_count: int
    bioacoustic_score: float  # 0 to 100


@dataclass
class SpeechAnalysisReport:
    file_path: str
    duration_sec: float
    sample_rate: int
    peak_amplitude: float
    rms_amplitude: float
    crest_factor_db: float
    
    # Core scores (0-100)
    roboticness_index: float      # 0 = organic/natural, 100 = completely robotic
    naturalness_score: float     # 0 = unnatural/synthetic, 100 = human-grade
    cleanliness_score: float     # 0 = severe clicks/glitches, 100 = pristine
    bioacoustic_score: float     # 0 = none, 100 = rich animal bioacoustics
    
    pitch: PitchMetrics
    harmonics: HarmonicMetrics
    formants: FormantMetrics
    transients: TransientMetrics
    rhythm: RhythmMetrics
    bioacoustics: BioacousticMetrics
    
    diagnostics: List[str]
    warnings: List[str]
    passes: List[str]


class SpeechAnalyzer:
    """Acoustic analyzer measuring naturalness, roboticness, and artifacts."""

    def __init__(self, audio: np.ndarray, sample_rate: int):
        if audio.ndim > 1:
            audio = np.mean(audio, axis=1)  # convert to mono
        self.raw_audio = audio.astype(np.float64)
        self.sr = sample_rate
        self.duration = len(self.raw_audio) / self.sr

        # Normalize audio for metric consistency
        peak = np.max(np.abs(self.raw_audio))
        self.peak = float(peak) if peak > 0 else 1.0
        self.audio = self.raw_audio / (self.peak + 1e-12) if self.peak > 0 else self.raw_audio

    def analyze(self) -> SpeechAnalysisReport:
        rms = float(np.sqrt(np.mean(self.audio ** 2)))
        crest = float(20.0 * np.log10(1.0 / (rms + 1e-9)))

        # 1. Pitch & Prosody Tracking
        pitch_res = self._analyze_pitch()

        # 2. Harmonics, Buzz & Jitter
        harm_res = self._analyze_harmonics(pitch_res)

        # 3. Formants & Spectral Contrast
        formant_res = self._analyze_formants()

        # 4. Transients, Clicks & Kurtosis
        trans_res = self._analyze_transients()

        # 5. Rhythmic Pacing & Syllable Dynamics
        rhythm_res = self._analyze_rhythm(pitch_res)

        # 6. Bioacoustics (Purr, Growl, Snarl, Clicks)
        bio_res = self._analyze_bioacoustics(pitch_res)

        # 7. Composite Scoring
        roboticness, naturalness, cleanliness, diagnostics, warnings, passes = self._compute_composite_scores(
            pitch_res, harm_res, formant_res, trans_res, rhythm_res, bio_res
        )

        return SpeechAnalysisReport(
            file_path="",
            duration_sec=round(self.duration, 3),
            sample_rate=self.sr,
            peak_amplitude=round(self.peak, 4),
            rms_amplitude=round(rms, 4),
            crest_factor_db=round(crest, 2),
            roboticness_index=round(roboticness, 1),
            naturalness_score=round(naturalness, 1),
            cleanliness_score=round(cleanliness, 1),
            bioacoustic_score=round(bio_res.bioacoustic_score, 1),
            pitch=pitch_res,
            harmonics=harm_res,
            formants=formant_res,
            transients=trans_res,
            rhythm=rhythm_res,
            bioacoustics=bio_res,
            diagnostics=diagnostics,
            warnings=warnings,
            passes=passes,
        )

    def _analyze_pitch(self) -> PitchMetrics:
        """Autocorrelation-based F0 pitch extraction with parabolic interpolation."""
        frame_len = int(0.040 * self.sr)  # 40ms window
        hop_len = int(0.010 * self.sr)    # 10ms hop
        if frame_len >= len(self.audio):
            frame_len = len(self.audio)
            hop_len = max(1, frame_len // 2)

        min_lag = int(self.sr / 600.0)  # max F0 = 600 Hz
        max_lag = int(self.sr / 60.0)   # min F0 = 60 Hz

        f0_list = []
        voiced_frames = 0
        total_frames = 0

        # Hann window
        window = np.hanning(frame_len)

        for i in range(0, len(self.audio) - frame_len, hop_len):
            total_frames += 1
            frame = self.audio[i : i + frame_len] * window
            frame_rms = np.sqrt(np.mean(frame ** 2))

            if frame_rms < 0.01:
                f0_list.append(np.nan)
                continue

            # Normalized autocorrelation
            corr = np.correlate(frame, frame, mode="full")
            corr = corr[len(corr) // 2 :]
            denom = corr[0]
            if denom <= 1e-9:
                f0_list.append(np.nan)
                continue
            corr_norm = corr / denom

            # Search peak between min_lag and max_lag
            if max_lag >= len(corr_norm):
                search_corr = corr_norm[min_lag:]
            else:
                search_corr = corr_norm[min_lag:max_lag]

            if len(search_corr) < 3:
                f0_list.append(np.nan)
                continue

            peak_idx = np.argmax(search_corr) + min_lag
            peak_val = corr_norm[peak_idx]

            if peak_val > 0.38 and 0 < peak_idx < len(corr_norm) - 1:
                # Parabolic peak interpolation
                alpha = corr_norm[peak_idx - 1]
                beta = corr_norm[peak_idx]
                gamma = corr_norm[peak_idx + 1]
                delta = 0.5 * (alpha - gamma) / (alpha - 2 * beta + gamma + 1e-12)
                true_lag = peak_idx + delta
                f0 = self.sr / true_lag
                f0_list.append(f0)
                voiced_frames += 1
            else:
                f0_list.append(np.nan)

        f0_arr = np.array(f0_list)
        voiced_f0 = f0_arr[~np.isnan(f0_arr)]
        voiced_frac = float(voiced_frames / max(1, total_frames))

        if len(voiced_f0) < 5:
            return PitchMetrics(
                mean_f0_hz=0.0,
                std_f0_hz=0.0,
                min_f0_hz=0.0,
                max_f0_hz=0.0,
                pitch_range_semitones=0.0,
                voiced_fraction=voiced_frac,
                declination_slope_hz_per_sec=0.0,
                declination_total_drop_hz=0.0,
                micro_prosody_depth_hz=0.0,
                pitch_jumps_count=0,
                pitch_smoothness_score=50.0,
            )

        mean_f0 = float(np.mean(voiced_f0))
        std_f0 = float(np.std(voiced_f0))
        min_f0 = float(np.percentile(voiced_f0, 5))
        max_f0 = float(np.percentile(voiced_f0, 95))
        safe_min = max(1.0, min_f0)
        safe_max = max(safe_min, max_f0)
        range_semitones = float(12.0 * np.log2(safe_max / safe_min))

        # Declination slope via robust linear regression
        time_axis = np.where(~np.isnan(f0_arr))[0] * (hop_len / self.sr)
        if len(time_axis) > 10:
            p = np.polyfit(time_axis, voiced_f0, 1)
            slope = float(p[0])
            total_drop = float(-slope * (time_axis[-1] - time_axis[0]))
        else:
            slope = 0.0
            total_drop = 0.0

        # Pitch jumps (discontinuities > 3 semitones between contiguous adjacent voiced frames)
        jumps = 0
        jump_threshold_hz = mean_f0 * 0.189  # ~3 semitones
        for k in range(len(f0_arr) - 1):
            if not np.isnan(f0_arr[k]) and not np.isnan(f0_arr[k + 1]):
                if abs(f0_arr[k + 1] - f0_arr[k]) > jump_threshold_hz:
                    jumps += 1

        # Micro-prosody / vibrato: check residual fluctuations around moving trend
        smooth_f0 = signal.medfilt(voiced_f0, kernel_size=min(11, len(voiced_f0) if len(voiced_f0) % 2 == 1 else len(voiced_f0) - 1))
        residual = np.abs(voiced_f0 - smooth_f0)
        micro_depth = float(np.mean(residual))

        # Smoothness score: penalize excessive jumps and reward smooth continuous flow
        jump_penalty = min(50.0, jumps * 12.0)
        smoothness = max(0.0, 100.0 - jump_penalty)

        return PitchMetrics(
            mean_f0_hz=round(mean_f0, 1),
            std_f0_hz=round(std_f0, 2),
            min_f0_hz=round(min_f0, 1),
            max_f0_hz=round(max_f0, 1),
            pitch_range_semitones=round(range_semitones, 2),
            voiced_fraction=round(voiced_frac, 3),
            declination_slope_hz_per_sec=round(slope, 2),
            declination_total_drop_hz=round(total_drop, 1),
            micro_prosody_depth_hz=round(micro_depth, 2),
            pitch_jumps_count=jumps,
            pitch_smoothness_score=round(smoothness, 1),
        )

    def _analyze_harmonics(self, pitch: PitchMetrics) -> HarmonicMetrics:
        """Measures Harmonic-to-Noise Ratio (HNR), Spectral Tilt, and Jitter/Shimmer."""
        # 1. HNR estimation via autocorrelation
        frame_len = int(0.040 * self.sr)
        hop_len = int(0.020 * self.sr)
        hnr_vals = []

        for i in range(0, len(self.audio) - frame_len, hop_len):
            frame = self.audio[i : i + frame_len]
            if np.sqrt(np.mean(frame ** 2)) < 0.01:
                continue
            corr = np.correlate(frame, frame, mode="full")
            corr = corr[len(corr) // 2 :]
            if corr[0] <= 1e-9:
                continue
            corr_norm = corr / corr[0]
            # search harmonic peak
            min_lag = int(self.sr / 600.0)
            max_lag = int(self.sr / 60.0)
            if max_lag < len(corr_norm):
                peak_val = np.max(corr_norm[min_lag:max_lag])
                if 0.01 < peak_val < 0.999:
                    hnr = 10.0 * np.log10(peak_val / (1.0 - peak_val + 1e-12))
                    hnr_vals.append(hnr)

        mean_hnr = float(np.median(hnr_vals)) if hnr_vals else 15.0

        # 2. Spectral Tilt (dB / octave) between 200 Hz and 4000 Hz
        freqs, psd = signal.welch(self.audio, self.sr, nperseg=min(2048, len(self.audio)))
        band_mask = (freqs >= 200.0) & (freqs <= 4000.0)
        f_band = freqs[band_mask]
        p_band = psd[band_mask]

        if len(f_band) > 10 and np.all(p_band > 0):
            log_f = np.log2(f_band)
            db_p = 10.0 * np.log10(p_band + 1e-12)
            slope, _ = np.polyfit(log_f, db_p, 1)
            spectral_tilt = float(slope)
        else:
            spectral_tilt = -9.0

        # 3. Spectral Flatness (Wiener entropy)
        p_pos = p_band[p_band > 0]
        if len(p_pos) > 0:
            geom_mean = np.exp(np.mean(np.log(p_pos + 1e-18)))
            arith_mean = np.mean(p_pos)
            flatness = float(geom_mean / (arith_mean + 1e-18))
        else:
            flatness = 0.05

        # 4. Jitter & Shimmer approximation from waveform cycle peaks
        jitter_pct, shimmer_pct = self._estimate_jitter_shimmer(pitch.mean_f0_hz)

        # 5. Harmonic Buzz Index:
        # High buzziness occurs when HNR is unnaturally high (>28dB) combined with near-zero jitter (<0.1%)
        buzz = 0.0
        if mean_hnr > 25.0:
            buzz += (mean_hnr - 25.0) * 3.5
        if jitter_pct < 0.3:
            buzz += (0.3 - jitter_pct) * 100.0
        if shimmer_pct < 0.8:
            buzz += (0.8 - shimmer_pct) * 40.0
        buzz_index = float(np.clip(buzz, 0.0, 100.0))

        return HarmonicMetrics(
            mean_hnr_db=round(mean_hnr, 1),
            spectral_tilt_db_oct=round(spectral_tilt, 2),
            spectral_flatness=round(flatness, 4),
            local_jitter_percent=round(jitter_pct, 2),
            local_shimmer_percent=round(shimmer_pct, 2),
            harmonic_buzz_index=round(buzz_index, 1),
        )

    def _estimate_jitter_shimmer(self, f0: float) -> Tuple[float, float]:
        """Estimates cycle-to-cycle period (jitter) and amplitude (shimmer) fluctuations."""
        if f0 <= 50.0:
            return 0.8, 2.5

        period_samples = int(self.sr / f0)
        # Find positive zero crossings or peaks
        diff = np.diff(np.signbit(self.audio))
        zc = np.where(diff)[0]

        if len(zc) < 20:
            return 0.8, 2.5

        # Calculate periods between every other crossing
        periods = np.diff(zc[::2])
        valid_periods = periods[(periods > period_samples * 0.6) & (periods < period_samples * 1.5)]

        if len(valid_periods) < 10:
            return 0.8, 2.5

        period_diffs = np.abs(np.diff(valid_periods))
        jitter = 100.0 * float(np.mean(period_diffs) / (np.mean(valid_periods) + 1e-6))

        # Peak amplitudes per cycle
        peaks = []
        for p_start in zc[:-2:2]:
            window = np.abs(self.audio[p_start : p_start + period_samples])
            if len(window) > 0:
                peaks.append(np.max(window))

        if len(peaks) > 10:
            peak_diffs = np.abs(np.diff(peaks))
            shimmer = 100.0 * float(np.mean(peak_diffs) / (np.mean(peaks) + 1e-6))
        else:
            shimmer = 2.5

        return float(np.clip(jitter, 0.0, 15.0)), float(np.clip(shimmer, 0.0, 30.0))

    def _analyze_formants(self) -> FormantMetrics:
        """Measures formant peak-to-valley contrast and spectral flux."""
        # STFT
        f, t, zxx = signal.stft(self.audio, self.sr, nperseg=min(1024, len(self.audio)), noverlap=512)
        mag = np.abs(zxx)

        # Spectral contrast in human vowel formant range (300 Hz - 3500 Hz)
        band_mask = (f >= 300.0) & (f <= 3500.0)
        mag_band = mag[band_mask, :]

        contrasts = []
        f1_list, f2_list = [], []

        for col in range(mag_band.shape[1]):
            spectrum = mag_band[:, col]
            if np.max(spectrum) < 1e-4:
                continue
            db_spec = 20.0 * np.log10(spectrum + 1e-6)
            peaks, _ = signal.find_peaks(db_spec, distance=4, prominence=3.0)
            if len(peaks) >= 2:
                peak_vals = db_spec[peaks]
                contrast = float(np.mean(peak_vals) - np.min(db_spec))
                contrasts.append(contrast)
                # Map first two peaks to F1, F2
                f_actual = f[band_mask]
                f1_list.append(f_actual[peaks[0]])
                f2_list.append(f_actual[peaks[1]])

        mean_contrast = float(np.median(contrasts)) if contrasts else 12.0
        contrast_score = float(np.clip((mean_contrast / 24.0) * 100.0, 0.0, 100.0))

        # Spectral flux: rate of spectral change between frames
        diff_mag = np.diff(mag, axis=1)
        flux = float(np.mean(np.sqrt(np.sum(diff_mag ** 2, axis=0))))

        f1_mean = float(np.median(f1_list)) if f1_list else 550.0
        f2_mean = float(np.median(f2_list)) if f2_list else 1650.0

        return FormantMetrics(
            peak_to_valley_contrast_db=round(mean_contrast, 1),
            formant_definition_score=round(contrast_score, 1),
            spectral_flux=round(flux, 4),
            f1_mean_hz=round(f1_mean, 1),
            f2_mean_hz=round(f2_mean, 1),
        )

    def _analyze_transients(self) -> TransientMetrics:
        """Detects clicks, Dirac spikes, and sample derivative cliffs."""
        # 1. First sample difference |s[n] - s[n-1]|
        diff_audio = np.abs(np.diff(self.audio))
        max_delta = float(np.max(diff_audio)) if len(diff_audio) > 0 else 0.0

        # 2. High-pass filter (> 3500 Hz) to isolate click impulses
        b, a = signal.butter(4, 3500.0 / (self.sr / 2.0), btype="high")
        hf_audio = signal.filtfilt(b, a, self.audio)

        # Kurtosis of HF signal (normal Gaussian noise ~3.0; click spikes > 20)
        hf_sq = hf_audio ** 2
        var_hf = np.mean(hf_sq)
        if var_hf > 1e-12:
            kurtosis = float(np.mean(hf_audio ** 4) / (var_hf ** 2))
        else:
            kurtosis = 3.0

        # 3. Count impulsive clicks: peaks in HF envelope > 18x median HF energy
        hf_env = np.abs(signal.hilbert(hf_audio))
        med_env = np.median(hf_env)
        click_thresh = max(0.08, float(med_env * 18.0))
        peaks, _ = signal.find_peaks(hf_env, height=click_thresh, distance=int(0.005 * self.sr))
        click_count = len(peaks)

        # 4. Cleanliness score calculation:
        # Penalize high max_delta (>0.15) and click count
        delta_penalty = max(0.0, (max_delta - 0.12) * 200.0)
        click_penalty = min(70.0, click_count * 12.0)
        # Kurtosis penalty is mild if no isolated clicks were detected
        if click_count > 0:
            kurt_penalty = max(0.0, (kurtosis - 15.0) * 0.8)
        else:
            kurt_penalty = min(10.0, max(0.0, (kurtosis - 30.0) * 0.2))
        cleanliness = max(0.0, 100.0 - delta_penalty - click_penalty - kurt_penalty)

        return TransientMetrics(
            max_sample_delta=round(max_delta, 4),
            kurtosis_hf=round(kurtosis, 1),
            click_count=click_count,
            artifact_cleanliness_score=round(cleanliness, 1),
        )

    def _analyze_bioacoustics(self, pitch: PitchMetrics) -> BioacousticMetrics:
        """Detects feline 25Hz purr gating, 48Hz snarl tremor, and ventricular growl subharmonics."""
        # 1. Amplitude envelope for modulation analysis (Purr & Snarl)
        env = np.abs(signal.hilbert(self.audio))
        # Downsample envelope to ~500 Hz for low-frequency modulation spectrum
        decim_factor = max(1, self.sr // 500)
        env_sub = signal.decimate(env, decim_factor)
        sub_sr = self.sr / decim_factor

        # Welch PSD of envelope
        f_env, p_env = signal.welch(env_sub - np.mean(env_sub), sub_sr, nperseg=min(512, len(env_sub)))
        total_env_power = float(np.sum(p_env) + 1e-12)

        # A. Feline Purr Search (20 - 32 Hz)
        purr_mask = (f_env >= 20.0) & (f_env <= 32.0)
        purr_hz = None
        purr_prom = 0.0
        if np.any(purr_mask):
            purr_band_p = p_env[purr_mask]
            purr_band_f = f_env[purr_mask]
            max_idx = np.argmax(purr_band_p)
            baseline = np.median(p_env[(f_env >= 10.0) & (f_env <= 60.0)]) + 1e-12
            prominence = purr_band_p[max_idx] / baseline
            purr_power_ratio = float(np.sum(purr_band_p) / total_env_power)
            # Genuine purr gating requires concentrated envelope modulation (>3.5% power) and high prominence (>4x)
            if prominence > 4.0 and purr_power_ratio > 0.035:
                purr_hz = float(purr_band_f[max_idx])
                purr_prom = float(prominence)

        # B. Canine Snarl Tremor Search (40 - 55 Hz)
        snarl_mask = (f_env >= 40.0) & (f_env <= 55.0)
        snarl_hz = None
        snarl_prom = 0.0
        if np.any(snarl_mask):
            snarl_band_p = p_env[snarl_mask]
            snarl_band_f = f_env[snarl_mask]
            max_idx = np.argmax(snarl_band_p)
            baseline = np.median(p_env[(f_env >= 10.0) & (f_env <= 60.0)]) + 1e-12
            prominence = snarl_band_p[max_idx] / baseline
            snarl_power_ratio = float(np.sum(snarl_band_p) / total_env_power)
            if prominence > 4.0 and snarl_power_ratio > 0.035:
                snarl_hz = float(snarl_band_f[max_idx])
                snarl_prom = float(prominence)

        # C. Ventricular Growl Subharmonic (F0 / 2)
        subharm_ratio = 0.0
        if pitch.mean_f0_hz > 70.0:
            freqs, psd = signal.welch(self.audio, self.sr, nperseg=min(2048, len(self.audio)))
            f0 = pitch.mean_f0_hz
            f_sub = f0 * 0.5
            idx_sub = np.argmin(np.abs(freqs - f_sub))
            idx_f0 = np.argmin(np.abs(freqs - f0))
            if idx_sub < len(psd) and idx_f0 < len(psd) and psd[idx_f0] > 0:
                subharm_ratio = float(psd[idx_sub] / (psd[idx_f0] + 1e-12))

        # D. Velaric Click burst detection in 1500 - 4500 Hz range
        b, a = signal.butter(4, [1500.0 / (self.sr / 2.0), 4500.0 / (self.sr / 2.0)], btype="band")
        click_band = signal.filtfilt(b, a, self.audio)
        click_env = np.abs(signal.hilbert(click_band))
        # Velaric suction clicks are extremely fast transient spikes (<15ms half-width)
        max_width_samples = int(0.015 * self.sr)
        click_peaks, _ = signal.find_peaks(click_env, height=0.25, distance=int(0.040 * self.sr), width=(1, max_width_samples))
        velaric_clicks = len(click_peaks)

        # Composite Bioacoustic Score (0 - 100)
        bio_score = 0.0
        if purr_hz is not None:
            bio_score += min(50.0, purr_prom * 10.0)
        if snarl_hz is not None:
            bio_score += min(40.0, snarl_prom * 8.0)
        if subharm_ratio > 0.25:
            bio_score += min(40.0, subharm_ratio * 60.0)
        if velaric_clicks > 0:
            bio_score += min(30.0, velaric_clicks * 10.0)

        return BioacousticMetrics(
            purr_modulation_hz=round(purr_hz, 1) if purr_hz else None,
            purr_prominence=round(purr_prom, 2),
            snarl_tremor_hz=round(snarl_hz, 1) if snarl_hz else None,
            snarl_prominence=round(snarl_prom, 2),
            growl_subharmonic_ratio=round(subharm_ratio, 3),
            velaric_click_count=velaric_clicks,
            bioacoustic_score=round(min(100.0, bio_score), 1),
        )

    def _analyze_rhythm(self, pitch: PitchMetrics) -> RhythmMetrics:
        """Measures Pairwise Variability Index (nPVI) of syllable durations and intra-vowel pitch dynamics."""
        # 1. Syllable energy envelope (smoothed 15 Hz lowpass)
        env = np.abs(signal.hilbert(self.audio))
        b, a = signal.butter(2, 15.0 / (self.sr / 2.0), btype="low")
        smooth_env = signal.filtfilt(b, a, env)

        # 2. Find syllable crests (minimum distance 110ms)
        min_dist = int(0.11 * self.sr)
        height_thresh = max(0.04, float(np.max(smooth_env) * 0.12))
        peaks, _ = signal.find_peaks(smooth_env, distance=min_dist, height=height_thresh)

        # If too few syllables detected, fallback
        if len(peaks) < 2:
            return RhythmMetrics(
                pairwise_variability_index=45.0,
                syllables_detected=max(1, len(peaks)),
                speaking_rate_syllables_per_sec=round(len(peaks) / max(0.1, self.duration), 1),
                intra_vowel_pitch_dynamics_hz=round(pitch.std_f0_hz * 0.5, 1),
                rhythm_naturalness_score=75.0,
            )

        # 3. Inter-syllable interval durations
        intervals = np.diff(peaks) / float(self.sr)

        # Normalized Pairwise Variability Index (nPVI)
        diffs = np.abs(np.diff(intervals))
        means = (intervals[:-1] + intervals[1:]) / 2.0
        npvi = float(100.0 * np.mean(diffs / (means + 1e-9))) if len(diffs) > 0 else 45.0

        # 4. Intra-vowel pitch dynamics
        intra_dynamics = min(35.0, pitch.std_f0_hz * 0.55 + pitch.micro_prosody_depth_hz * 1.2)

        # Rhythm naturalness score: penalize extreme monotony (nPVI < 20)
        rhythm_score = 100.0
        if npvi < 20.0:
            rhythm_score -= (20.0 - npvi) * 3.0
        elif npvi > 90.0:
            rhythm_score -= (npvi - 90.0) * 1.5
        rhythm_score = float(np.clip(rhythm_score, 0.0, 100.0))

        return RhythmMetrics(
            pairwise_variability_index=round(npvi, 1),
            syllables_detected=len(peaks),
            speaking_rate_syllables_per_sec=round(len(peaks) / max(0.1, self.duration), 1),
            intra_vowel_pitch_dynamics_hz=round(intra_dynamics, 1),
            rhythm_naturalness_score=round(rhythm_score, 1),
        )

    def _compute_composite_scores(
        self,
        pitch: PitchMetrics,
        harm: HarmonicMetrics,
        form: FormantMetrics,
        trans: TransientMetrics,
        rhythm: RhythmMetrics,
        bio: BioacousticMetrics,
    ) -> Tuple[float, float, float, List[str], List[str], List[str]]:
        """Calculates roboticness index and compiles diagnostic alerts."""
        diagnostics = []
        warnings = []
        passes = []

        roboticness = 0.0

        # --- 1. Pitch & Prosody (0 to 35 pts) ---
        if pitch.voiced_fraction > 0.15:
            if pitch.std_f0_hz < 5.0:
                roboticness += 28.0
                warnings.append(f"Monotone Pitch: F0 std dev is only {pitch.std_f0_hz} Hz (< 5.0 Hz). Sounds flat & robotic.")
            elif pitch.std_f0_hz < 10.0:
                roboticness += 14.0
                warnings.append(f"Subdued Prosody: F0 std dev is {pitch.std_f0_hz} Hz (< 10.0 Hz).")
            else:
                passes.append(f"Natural Pitch Range: std dev {pitch.std_f0_hz} Hz, dynamic range {pitch.pitch_range_semitones} st.")

            if pitch.pitch_jumps_count > 3:
                roboticness += min(18.0, pitch.pitch_jumps_count * 4.0)
                warnings.append(f"Pitch Discontinuities: {pitch.pitch_jumps_count} unnatural pitch jumps detected (>3 semitones).")
            else:
                passes.append("Smooth Pitch Transitions: No abrupt step pitch cliffs.")

            if pitch.declination_total_drop_hz > 8.0:
                passes.append(f"Sentence Declination: Pitch naturally drops by {pitch.declination_total_drop_hz} Hz.")
            elif pitch.declination_total_drop_hz < -15.0:
                warnings.append(f"Unnatural Pitch Rise: Pitch rises steeply by {-pitch.declination_total_drop_hz} Hz.")
        else:
            diagnostics.append("Low voicing content (< 15% voiced). Mostly unvoiced/whisper.")

        # --- 2. Harmonics & Buzz (0 to 25 pts) ---
        if harm.harmonic_buzz_index > 40.0:
            roboticness += min(22.0, harm.harmonic_buzz_index * 0.25)
            warnings.append(f"Synthetic Buzz: High harmonic buzz index ({harm.harmonic_buzz_index}). Low natural jitter/shimmer.")
        else:
            passes.append(f"Acoustic Warmth: Natural harmonic jitter ({harm.local_jitter_percent}%) and shimmer ({harm.local_shimmer_percent}%).")

        # --- 3. Formant Definition (0 to 20 pts) ---
        if form.peak_to_valley_contrast_db < 7.0:
            roboticness += 16.0
            warnings.append(f"Formant Smearing: Low peak-to-valley contrast ({form.peak_to_valley_contrast_db} dB). Vowels lack clarity.")
        elif form.peak_to_valley_contrast_db >= 14.0:
            passes.append(f"Sharp Formants: Vowel contrast {form.peak_to_valley_contrast_db} dB (F1={form.f1_mean_hz}Hz, F2={form.f2_mean_hz}Hz).")

        # --- 4. Click & Transient Artifacts (0 to 20 pts) ---
        if trans.click_count > 0:
            roboticness += min(20.0, trans.click_count * 5.0)
            warnings.append(f"Clicks / Glitches: {trans.click_count} impulsive click artifacts detected.")
        if trans.max_sample_delta > 0.15:
            warnings.append(f"Sample Cliff: Max sample-to-sample jump is {trans.max_sample_delta} (> 0.15 limit).")
        if trans.click_count == 0 and trans.max_sample_delta <= 0.12:
            passes.append(f"Artifact Cleanliness: Clean waveform with max sample delta {trans.max_sample_delta}.")

        # --- 5. Rhythmic Pacing & Syllable Dynamics (0 to 25 pts) ---
        if rhythm.pairwise_variability_index < 22.0:
            roboticness += 22.0
            warnings.append(f"Metronomic Pacing: nPVI is {rhythm.pairwise_variability_index} (< 22.0). Syllables sound mechanically uniform.")
        elif rhythm.pairwise_variability_index >= 35.0:
            passes.append(f"Natural Stress-Timed Rhythm: nPVI is {rhythm.pairwise_variability_index} (speaking rate {rhythm.speaking_rate_syllables_per_sec} syl/s).")

        if rhythm.intra_vowel_pitch_dynamics_hz < 3.5:
            roboticness += 18.0
            warnings.append(f"Flat Pitch Holds: Vowel dynamics {rhythm.intra_vowel_pitch_dynamics_hz} Hz (< 3.5 Hz). Vowels sound like static synth notes.")
        elif rhythm.intra_vowel_pitch_dynamics_hz >= 5.0:
            passes.append(f"Dynamic Syllable Intonation: Intra-vowel pitch dynamic excursion is {rhythm.intra_vowel_pitch_dynamics_hz} Hz.")

        # --- 6. Bioacoustic Flags ---
        if bio.purr_modulation_hz is not None:
            passes.append(f"Feline Purr Verified: Strong {bio.purr_modulation_hz} Hz neural amplitude modulation detected.")
        if bio.snarl_tremor_hz is not None:
            passes.append(f"Canine Snarl Verified: {bio.snarl_tremor_hz} Hz aggressive tremor detected.")
        if bio.growl_subharmonic_ratio > 0.2:
            passes.append(f"Ventricular Growl Verified: F0/2 subharmonic energy ratio {bio.growl_subharmonic_ratio}.")

        roboticness_index = float(np.clip(roboticness, 0.0, 100.0))
        naturalness_score = float(np.clip(100.0 - (roboticness_index * 1.05), 0.0, 100.0))
        cleanliness_score = trans.artifact_cleanliness_score

        return roboticness_index, naturalness_score, cleanliness_score, diagnostics, warnings, passes


# =====================================================================
# Terminal Presentation & CLI Formatting
# =====================================================================

# Configure stdout/stderr for UTF-8 encoding safely on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def color(text: str, code: str) -> str:
    """Colorizes terminal output with ANSI escape codes."""
    if not sys.stdout.isatty():
        return text
    colors = {
        "green": "\033[92m",
        "red": "\033[91m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "cyan": "\033[96m",
        "magenta": "\033[95m",
        "bold": "\033[1m",
        "dim": "\033[2m",
        "reset": "\033[0m",
    }
    return f"{colors.get(code, '')}{text}{colors['reset']}"


def print_scorecard(report: SpeechAnalysisReport):
    """Renders a comprehensive terminal scorecard."""
    print()
    print(color("=" * 72, "cyan"))
    print(color("  VOCALIS SPEECH ACOUSTIC EVALUATOR & REALISM AUDIT", "bold"))
    print(color("=" * 72, "cyan"))
    print(f"  Target File : {color(report.file_path, 'bold')}")
    print(f"  Duration    : {report.duration_sec}s  |  Sample Rate: {report.sample_rate} Hz  |  Peak: {report.peak_amplitude}")
    print(color("-" * 72, "dim"))

    # Core Gauge Meter with UTF-8 / ASCII fallback
    def bar(score: float, width: int = 24, invert: bool = False) -> str:
        filled = int((score / 100.0) * width)
        empty = width - filled
        try:
            b = "█" * filled + "░" * empty
            b.encode(sys.stdout.encoding or "ascii")
        except Exception:
            b = "#" * filled + "-" * empty
        if invert:  # for roboticness (lower = green)
            c = "green" if score < 30 else ("yellow" if score < 60 else "red")
        else:       # for naturalness/cleanliness (higher = green)
            c = "green" if score >= 75 else ("yellow" if score >= 50 else "red")
        return color(f"[{b}] {score:5.1f}/100", c)

    print(f"  Roboticness Index   (lower is better) : {bar(report.roboticness_index, invert=True)}")
    print(f"  Human Naturalness   (higher is better): {bar(report.naturalness_score)}")
    print(f"  Artifact Cleanliness (100 = pristine) : {bar(report.cleanliness_score)}")
    if report.bioacoustics.bioacoustic_score > 5.0:
        print(f"  Bioacoustic Realism (animal features) : {bar(report.bioacoustic_score)}")

    print(color("-" * 72, "dim"))
    print(color("  [1] PITCH & PROSODY", "bold"))
    p = report.pitch
    print(f"      F0 Mean / Std Dev : {p.mean_f0_hz} Hz  (±{p.std_f0_hz} Hz)")
    print(f"      Pitch Range       : {p.min_f0_hz} Hz - {p.max_f0_hz} Hz ({p.pitch_range_semitones} semitones)")
    print(f"      Voiced Fraction   : {int(p.voiced_fraction * 100)}% of frames voiced")
    print(f"      Sentence Arc      : {p.declination_total_drop_hz} Hz net declination ({p.declination_slope_hz_per_sec} Hz/s)")
    print(f"      Discontinuities   : {p.pitch_jumps_count} abrupt jumps (Smoothness: {p.pitch_smoothness_score}/100)")

    print(color("  [2] TIMBRE & HARMONICS", "bold"))
    h = report.harmonics
    print(f"      Harmonic-to-Noise : {h.mean_hnr_db} dB HNR")
    print(f"      Spectral Tilt     : {h.spectral_tilt_db_oct} dB/octave (ideal: -6 to -12 dB/oct)")
    print(f"      Jitter / Shimmer  : Jitter {h.local_jitter_percent}%  |  Shimmer {h.local_shimmer_percent}%")
    print(f"      Synthetic Buzz    : Index {h.harmonic_buzz_index}/100")

    print(color("  [3] FORMANTS & ARTICULATION", "bold"))
    f = report.formants
    print(f"      Formant Contrast  : {f.peak_to_valley_contrast_db} dB peak-to-valley (Definition: {f.formant_definition_score}/100)")
    print(f"      Vowel Formants    : F1 ~ {f.f1_mean_hz} Hz  |  F2 ~ {f.f2_mean_hz} Hz")

    print(color("  [4] TRANSIENTS & CLICK DETECTION", "bold"))
    t = report.transients
    print(f"      Sample Delta Jump : {t.max_sample_delta}  (max sample-to-sample cliff)")
    print(f"      HF Kurtosis       : {t.kurtosis_hf}  (spike indicator)")
    print(f"      Clicks Detected   : {t.click_count} impulsive transient glitches")

    print(color("  [5] RHYTHMIC PACING & SYLLABLE DYNAMICS", "bold"))
    r = report.rhythm
    print(f"      Pairwise Variability : nPVI {r.pairwise_variability_index}  (>35 = stress-timed natural, <22 = metronomic)")
    print(f"      Speaking Rate        : {r.speaking_rate_syllables_per_sec} syl/sec  ({r.syllables_detected} syllables detected)")
    print(f"      Intra-Vowel Dynamics : {r.intra_vowel_pitch_dynamics_hz} Hz pitch gesture excursion (Score: {r.rhythm_naturalness_score}/100)")

    if report.bioacoustics.bioacoustic_score > 5.0:
        print(color("  [6] BIOACOUSTIC PHONETICS", "bold"))
        b = report.bioacoustics
        if b.purr_modulation_hz:
            print(f"      Feline Purr       : {b.purr_modulation_hz} Hz AM modulation (prominence: {b.purr_prominence}x)")
        if b.snarl_tremor_hz:
            print(f"      Canine Snarl      : {b.snarl_tremor_hz} Hz tremor (prominence: {b.snarl_prominence}x)")
        if b.growl_subharmonic_ratio > 0.1:
            print(f"      Growl Subharmonic : F0/2 ratio {b.growl_subharmonic_ratio}")
        if b.velaric_click_count > 0:
            print(f"      Velaric Clicks    : {b.velaric_click_count} sharp suction bursts")

    print(color("-" * 72, "dim"))
    # Passes & Warnings
    if report.passes:
        print(color("  VERIFIED NATURAL QUALITIES:", "green"))
        for p_msg in report.passes:
            print(f"    {color('[PASS]', 'green')} {p_msg}")

    if report.warnings:
        print(color("  ACOUSTIC FLAWS DETECTED:", "yellow"))
        for w_msg in report.warnings:
            print(f"    {color('[WARN]', 'yellow')} {w_msg}")

    print(color("=" * 72, "cyan"))
    print()


def compare_files(file1: str, file2: str):
    """Performs a side-by-side comparative analysis of two audio files."""
    data1, sr1 = sf.read(file1)
    data2, sr2 = sf.read(file2)
    rep1 = SpeechAnalyzer(data1, sr1).analyze()
    rep1.file_path = os.path.basename(file1)
    rep2 = SpeechAnalyzer(data2, sr2).analyze()
    rep2.file_path = os.path.basename(file2)

    print()
    print(color("=" * 80, "cyan"))
    print(color("  SIDE-BY-SIDE ACOUSTIC COMPARISON", "bold"))
    print(color("=" * 80, "cyan"))
    hdr = f"  {'Metric':<32} | {rep1.file_path:<20} | {rep2.file_path:<20}"
    print(color(hdr, "bold"))
    print(color("-" * 80, "dim"))

    def row(name: str, v1: Any, v2: Any, better_is_lower: bool = False):
        s1 = str(v1)
        s2 = str(v2)
        print(f"  {name:<32} | {s1:<20} | {s2:<20}")

    row("Roboticness Index (0-100)", rep1.roboticness_index, rep2.roboticness_index, better_is_lower=True)
    row("Human Naturalness (0-100)", rep1.naturalness_score, rep2.naturalness_score)
    row("Artifact Cleanliness (0-100)", rep1.cleanliness_score, rep2.cleanliness_score)
    row("Rhythm nPVI (>35 natural)", rep1.rhythm.pairwise_variability_index, rep2.rhythm.pairwise_variability_index)
    row("Speaking Rate (syl/s)", rep1.rhythm.speaking_rate_syllables_per_sec, rep2.rhythm.speaking_rate_syllables_per_sec)
    row("Intra-Vowel Pitch Dyn", f"{rep1.rhythm.intra_vowel_pitch_dynamics_hz} Hz", f"{rep2.rhythm.intra_vowel_pitch_dynamics_hz} Hz")
    row("Pitch F0 Mean / Std", f"{rep1.pitch.mean_f0_hz}Hz (±{rep1.pitch.std_f0_hz})", f"{rep2.pitch.mean_f0_hz}Hz (±{rep2.pitch.std_f0_hz})")
    row("Pitch Jumps / Glitches", rep1.pitch.pitch_jumps_count, rep2.pitch.pitch_jumps_count, better_is_lower=True)
    row("Sentence Declination", f"{rep1.pitch.declination_total_drop_hz} Hz", f"{rep2.pitch.declination_total_drop_hz} Hz")
    row("Formant Contrast", f"{rep1.formants.peak_to_valley_contrast_db} dB", f"{rep2.formants.peak_to_valley_contrast_db} dB")
    row("Clicks Detected", rep1.transients.click_count, rep2.transients.click_count, better_is_lower=True)
    row("Max Sample Delta Jump", rep1.transients.max_sample_delta, rep2.transients.max_sample_delta, better_is_lower=True)
    row("Harmonic Buzz Index", rep1.harmonics.harmonic_buzz_index, rep2.harmonics.harmonic_buzz_index, better_is_lower=True)
    row("Bioacoustic Score", rep1.bioacoustic_score, rep2.bioacoustic_score)
    print(color("=" * 80, "cyan"))
    print()


def batch_analyze(folder: str):
    """Scans and benchmarks all .wav files in a directory."""
    wavs = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(".wav")]
    if not wavs:
        print(f"No .wav files found in {folder}")
        return

    print()
    print(color("=" * 85, "cyan"))
    print(color(f"  BATCH AUDIT: {len(wavs)} files in {folder}", "bold"))
    print(color("=" * 85, "cyan"))
    hdr = f"  {'Filename':<32} | {'Robotic':<8} | {'Natural':<8} | {'Clean':<8} | {'Clicks':<6} | {'F0 (Hz)':<10}"
    print(color(hdr, "bold"))
    print(color("-" * 85, "dim"))

    tot_robot = 0.0
    tot_nat = 0.0
    tot_clean = 0.0
    tot_clicks = 0

    for w in sorted(wavs):
        try:
            audio, sr = sf.read(w)
            rep = SpeechAnalyzer(audio, sr).analyze()
            bname = os.path.basename(w)
            if len(bname) > 30:
                bname = bname[:27] + "..."
            print(f"  {bname:<32} | {rep.roboticness_index:<8.1f} | {rep.naturalness_score:<8.1f} | {rep.cleanliness_score:<8.1f} | {rep.transients.click_count:<6} | {rep.pitch.mean_f0_hz:<10.1f}")
            tot_robot += rep.roboticness_index
            tot_nat += rep.naturalness_score
            tot_clean += rep.cleanliness_score
            tot_clicks += rep.transients.click_count
        except Exception as e:
            print(f"  Error reading {w}: {e}")

    n = len(wavs)
    print(color("-" * 85, "dim"))
    print(color(f"  {'AVERAGE':<32} | {tot_robot/n:<8.1f} | {tot_nat/n:<8.1f} | {tot_clean/n:<8.1f} | {tot_clicks:<6} |", "bold"))
    print(color("=" * 85, "cyan"))
    print()


def main():
    parser = argparse.ArgumentParser(description="Speech Naturalness & Roboticness Audio Analyzer")
    parser.add_argument("audio_file", nargs="?", help="Path to input .wav file to analyze")
    parser.add_argument("--compare", nargs=2, metavar=("FILE1", "FILE2"), help="Compare two .wav files side-by-side")
    parser.add_argument("--batch", metavar="DIR", help="Batch analyze all .wav files in a directory")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON metrics")

    args = parser.parse_args()

    if args.compare:
        compare_files(args.compare[0], args.compare[1])
        return

    if args.batch:
        batch_analyze(args.batch)
        return

    if not args.audio_file:
        parser.print_help()
        sys.exit(1)

    if not os.path.exists(args.audio_file):
        print(f"Error: File not found: {args.audio_file}", file=sys.stderr)
        sys.exit(1)

    audio, sr = sf.read(args.audio_file)
    analyzer = SpeechAnalyzer(audio, sr)
    report = analyzer.analyze()
    report.file_path = os.path.abspath(args.audio_file)

    if args.json:
        # Serializer for dataclass with rounded floats
        data = asdict(report)
        print(json.dumps(data, indent=2))
    else:
        print_scorecard(report)


if __name__ == "__main__":
    main()
