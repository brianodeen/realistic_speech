# Parametric Spectral & Formant Synthesis: Mathematical Foundations and Architecture

## Executive Summary & Overview

This document formalizes the theory, mathematics, and architectural implementation of a modular, parameter-driven acoustic synthesis engine. By decomposing acoustic sounds, musical instruments, human speech, and biological animal vocalizations into fundamental mathematical building blocks—deterministic harmonic partials, stochastic residual noise, dynamic resonant filter banks (formants), and non-linear chaotic perturbations—we can represent complex audio phenomena compactly via structured parameter files (e.g., JSON) and reconstruct them with high physical and perceptual fidelity.

---

## 1. Mathematical Basis: Acoustic Instruments & Fourier Analysis

### 1.1 Short-Time Fourier Transform (STFT)
While a standard Fourier Transform decomposes a continuous signal into static frequency components across infinite time, real acoustic instruments are inherently time-varying. The Short-Time Fourier Transform (STFT) segments audio using a sliding window function $w(t)$:

$$X(	au, \omega) = \int_{-\infty}^{\infty} x(t) w(t - 	au) e^{-j \omega t} \, dt$$

This time-frequency representation forms the foundation of **Spectral Modeling Synthesis (SMS)**.

```
                      [ Raw Instrument Audio ]
                                 │
                                 ▼
                     Short-Time Fourier Transform (STFT)
                                 │
                 ┌───────────────┴───────────────┐
                 ▼                               ▼
       Deterministic Component          Stochastic Residual
     (Harmonic Sines & Overtones)      (Attack Transient / Noise)
                 │                               │
                 └───────────────┬───────────────┘
                                 ▼
                  [ Dynamic Resonator / Filter ]
                    (Instrument Body / Formants)
```

### 1.2 Deterministic Harmonic Component
For pitched musical instruments (strings, brass, woodwinds), the deterministic sound consists of an integer (or near-integer) series of harmonic partials based on a fundamental frequency $f_0(t)$:

$$y_{	ext{harmonic}}(t) = \sum_{k=1}^{N} A_k(t) \sin\left(2\pi \int_0^t f_k(	au)\,d	au + \phi_kight)$$

* **$A_k(t)$ (Amplitude Envelopes):** Time-varying amplitude of the $k$-th partial. In plucked strings, higher partials exhibit faster exponential decay rates ($lpha_k > lpha_{k-1}$).
* **$f_k(t)$ (Frequency Partials & Inharmonicity):** In stiff strings (pianos, heavy guitar strings), physical stiffness causes partials to deviate from pure integers according to the inharmonicity coefficient $B$:
  $$f_k pprox k f_0 \sqrt{1 + B k^2}$$

### 1.3 Stochastic Residual Noise Component
Acoustic instruments produce non-periodic energy that cannot be practically represented by discrete sinusoidal partials:
* The pick strike or fingertip friction on a string.
* Turbulent breath noise in a flute or woodwind.
* Bow scrape and stick-slip friction in bowed instruments.

The residual $e(t)$ is extracted by subtracting the synthesized deterministic component from the original signal:

$$e(t) = x(t) - y_{	ext{harmonic}}(t)$$

The residual is modeled statistically as time-varying white noise filtered through an envelope-controlled spectral curve:

$$y_{	ext{residual}}(t) = \mathcal{F}^{-1}\{H_{	ext{noise}}(\omega, t) \cdot \mathcal{F}\{\eta(t)\}\}$$

where $\eta(t) \sim \mathcal{N}(0, \sigma^2)$ represents Gaussian white noise.

### 1.4 Instrument Comparative Acoustics

| Instrument Family | Harmonic Structure | Transient / Residual Character | Basis Representation |
| :--- | :--- | :--- | :--- |
| **Plucked String (Guitar, Harp)** | Quasi-harmonic with stiffness inharmonicity ($f_k pprox k f_0 \sqrt{1 + B k^2}$) | Sharp, broad-spectrum initial burst ($< 15\,\text{ms}$) | Rapidly decaying high-order sinusoids + attack impulse |
| **Bowed String (Violin, Cello)** | Strictly integer harmonics sustained by stick-slip friction | Continuous broad-spectrum friction noise | Dynamic sawtooth pulse train + body cavity transfer function |
| **Woodwind (Clarinet)** | Predominantly odd harmonics ($1f_0, 3f_0, 5f_0$) due to closed cylindrical bore | Continuous airflow turbulence | Odd-harmonic pulse generator + dynamic formant filters |
| **Membranophones (Drums)** | Non-integer harmonic modes governed by Bessel function roots | Dominant impulse transient dominating total energy | Exponentially decaying non-harmonic sinusoids |

---

## 2. Source-Filter Acoustics: Human Speech & Animal Vocalizations

Biological sound generation decouples sound production into two distinct physiological systems: the **excitation source** (vocal folds, syrinx, constrictions) and the **acoustic filter** (vocal tract, oral/nasal cavities, beak/throat).

```
                    [ Lungs / Airflow ]
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
   [ Periodic Glottal Buzz ]        [ Turbulent Aperiodic Noise ]
   (Vocal cords vibrating)          (Constrictions, hisses, clicks)
   • Vowels, Hum, Howl              • Unvoiced consonants (s, f, sh), Snarl
            │                                 │
            └────────────────┬────────────────┘
                             ▼
                 [ Vocal Tract Resonator ]
              (Pharynx, Mouth, Oral Cavity)
              • Dynamic Resonant Peaks: Formants (F1, F2, F3)
                             │
                             ▼
                     [ Radiated Sound ]
```

### 2.1 Human Speech Production
* **Voiced Phonemes (Vowels, Nasals: /a/, /i/, /u/, /m/):**
  The vocal folds oscillate periodically, creating an acoustic pulse train rich in harmonics. As articulators (tongue, jaw, lips) alter the vocal tract volume and length, they create resonant acoustic filter peaks called **formants**:
  * **$F_1$ (First Formant):** Corresponds to jaw opening / pharyngeal constriction ($250\,\text{Hz}$ for closed /i/ up to $850\,\text{Hz}$ for open /a/).
  * **$F_2$ (Second Formant):** Corresponds to tongue advancement / oral cavity shape ($800\,\text{Hz}$ for back vowels up to $2400\,\text{Hz}$ for front vowels).
  * **$F_3, F_4$:** Determine individual vocal timbre and speaker identity.
* **Unvoiced Phonemes (Fricatives, Plosives: /s/, /ʃ/, /t/, /k/):**
  Air is forced through turbulent constrictions without vocal fold oscillation (fricatives) or released after a complete occlusion (plosives).
* **Linear Predictive Coding (LPC):**
  Models the human vocal tract as an all-pole infinite impulse response (IIR) filter transfer function:
  $$H(z) = rac{G}{1 - \sum_{k=1}^{p} a_k z^{-k}}$$
  Exciting $H(z)$ with an impulse train generates voiced vowels; exciting it with white noise generates unvoiced consonants.

### 2.2 Animal Vocalizations & Acoustic Mechanisms

| Vocalization Type | Acoustic Mechanism | Mathematical Model |
| :--- | :--- | :--- |
| **Canine / Wolf Howl** | Sustained vocal fold oscillation with minimal formant modulation. High acoustic efficiency. | Smooth, continuous $f_0(t)$ frequency trajectory with tight integer harmonics and low residual noise. |
| **Growl / Snarl** | Low-frequency vocal fold vibration coupled with supraglottic tissue oscillation and vortex shedding. | **Subharmonic Bifurcation & Deterministic Chaos:** Injects subharmonic sidebands ($f_0/2, f_0/3$) and non-linear polynomial feedback. |
| **Feline Purr** | Active neural oscillator firing laryngeal muscles during alternating inhalation and exhalation. | Low-frequency pulse train ($20–30\,\text{Hz}$) modulated by a cyclic respiratory amplitude envelope. |
| **Avian Song (Syrinx)** | Dual sound-generating membranes at the bronchial bifurcation, independently controlled. | Two coupled, time-varying non-linear oscillators ($f_A(t)$ and $f_B(t)$) exhibiting rapid frequency sweeps and polyphonic ring modulation. |

---

## 3. Modular Parametric Synthesis Engine Architecture

The multi-stage parametric synthesis architecture translates structured parameter definitions into continuous, band-limited audio signals.

```
  [ Sound Definition (JSON) ]
               │
               ▼
  ┌─────────────────────────┐
  │  Stage 1: Trajectory    │ ◄── Interpolate parameter curves (F0, formants, noise mix)
  │          Generator      │
  └────────────┬────────────┘
               │ Dynamic Control Buffers (evaluated at control/sample rate)
               ▼
  ┌─────────────────────────┐
  │  Stage 2: Excitation    │ ◄── Glottal pulse / String oscillator + Stochastic noise
  │          Engine         │
  └────────────┬────────────┘
               │ Raw Source Waveform
               ▼
  ┌─────────────────────────┐
  │  Stage 3: Resonator &   │ ◄── Cascaded/Parallel 2nd-order Biquad filters (Formants)
  │      Filter Bank        │
  └────────────┬────────────┘
               │ Resonated Audio
               ▼
  ┌─────────────────────────┐
  │  Stage 4: Post-FX &     │ ◄── Waveshaping, subharmonic chaos (for growls), body resonance
  │          Body           │
  └────────────┬────────────┘
               │
               ▼
  ┌─────────────────────────┐
  │  Stage 5: Coarticulation│ ◄── Crossfade / Formant trajectory morph / Glottal boundary
  │      & Sequencer        │
  └─────────────────────────┘
```

### 3.1 Stage-by-Stage Processing Details

#### Stage 1: Trajectory Generator
* Converts piecewise keyframes into continuous control signals evaluated at control rate ($k_{\text{rate}} = 1000\,\text{Hz}$) or audio rate ($f_s = 44100\,\text{Hz}$).
* Computes pitch vibrato/flutter:
  $$f_{0,\text{inst}}(t) = f_0(t) \cdot 2^{rac{\text{depth}(t) \cdot \sin(2\pi f_{\text{lfo}} t)}{1200}}$$

#### Stage 2: Excitation Engine
* **Voiced Excitation (Rosenberg Glottal Pulse Model):**
  $$g(t) = \begin{cases} 3\left(\frac{t}{T_p}\right)^2 - 2\left(\frac{t}{T_p}\right)^3 & 0 \le t \le T_p \\ 1 - \left(\frac{t - T_p}{T_n}\right)^2 & T_p < t \le T_p + T_n \\ 0 & T_p + T_n < t \le T_0 \end{cases}$$
* **Band-Limited Step/Impulse Generation (BLEP/BLIT):** Eliminates Nyquist foldover aliasing during synthesis.
* **Growl Chaos Generator:**
  $$s_{\text{source}}[n] = (1 - \beta) \cdot s_{\text{pulse}}[n] + \beta \cdot \left( s_{\text{pulse}}[n] + \alpha \cdot s_{\text{pulse}}[n - D] \cdot |s_{\text{pulse}}[n]| \right)$$

#### Stage 3: Resonator Filter Bank (Formants)
Second-order IIR band-pass filters (Biquads) placed in series (vowel acoustics) or parallel (nasals/fricatives).
For a formant with center frequency $F_c$ and bandwidth $B_w$ at sample rate $f_s$:

$$R = e^{-\pi B_w / f_s}, \quad \theta = 2\pi F_c / f_s$$
$$y[n] = 2 R \cos(\theta) y[n-1] - R^2 y[n-2] + (1 - R) x[n]$$

#### Stage 4: Post-Processing & Acoustic Body
* Soft-saturation waveshaping: $f(x) = \tanh(\gamma x)$.
* Convolution or feedback delay networks (FDN) simulating physical enclosure acoustics.

---

## 4. Sequential Sound Transitions: Coarticulation vs. Glottal Stops

Connecting two sequential acoustic segments ($S_A \to S_B$) requires managing boundary physical states.

```
[ Segment A ] ────► [ Boundary Processing ] ────► [ Segment B ]
                            │
            ┌───────────────┴───────────────┐
            ▼                               ▼
  Continuous Coarticulation           Glottal Stop
  • Blend formant targets             • Zero-energy gap (10–40ms)
  • Smooth F0 glide                   • Vocal fold snap transient
  • No phase cancellation             • Hard energy reset
```

### 4.1 Continuous Coarticulation (Smooth Articulation)
In biological vocal tracts, physical articulators smoothly transition between targets.
* **Formant Blending Function:** Over transition window $\Delta t_{\text{coart}}$, interpolate filter parameters using a Hermite $C^2$-continuous curve (Smootherstep):
  $$w(t) = 6t^5 - 15t^4 + 10t^3 \quad \text{where } t = \frac{\tau - t_{\text{start}}}{\Delta t_{\text{coart}}}$$
  $$F_k(\tau) = (1 - w(t)) \cdot F_{k,A}(\tau) + w(t) \cdot F_{k,B}(\tau)$$
* **Continuous Phase Tracking:** The oscillator phase accumulator $\phi(t)$ is preserved across the boundary without resetting:
  $$\phi(t + \Delta t) = \left( \phi(t) + 2\pi f_0(t) \Delta t \right) \pmod{2\pi}$$

### 4.2 Glottal Stop / Hard Boundary (/ʔ/)
Occurs when vocal folds tightly adduct, interrupting airflow completely before bursting open.
* **Amplitude Clamp:** Decay amplitude envelope to zero within $5–10\,\text{ms}$.
* **Inter-segment Silence:** Insert a $15–40\,\text{ms}$ acoustic gap; clear filter memory states ($y[n-1] = y[n-2] = 0$).
* **Transient Explosion:** Inject a high-amplitude asymmetric initial impulse ($t=0$) upon opening the glottis to reproduce the vocal snap, followed by a phase-reset oscillator.

---

## 5. Parameter Specification Schema (JSON)

Below is the standard JSON schema specification for encoding sound units and sequence transitions.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "AcousticSoundSegment",
  "type": "object",
  "properties": {
    "segment_id": { "type": "string" },
    "duration_ms": { "type": "number", "minimum": 10 },
    "boundary_transition": {
      "type": "object",
      "properties": {
        "mode": { "type": "string", "enum": ["coarticulate", "glottal_stop", "crossfade"] },
        "transition_duration_ms": { "type": "number" },
        "interpolation_curve": { "type": "string", "enum": ["linear", "smoothstep", "smootherstep"] },
        "glottal_silence_ms": { "type": "number" },
        "glottal_pop_intensity": { "type": "number" }
      },
      "required": ["mode", "transition_duration_ms"]
    },
    "source_excitation": {
      "type": "object",
      "properties": {
        "model": { "type": "string", "enum": ["rosenberg_pulse", "sawtooth_blit", "white_noise", "hybrid_growl"] },
        "f0_trajectory": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "time_ratio": { "type": "number", "minimum": 0, "maximum": 1 },
              "frequency_hz": { "type": "number" }
            },
            "required": ["time_ratio", "frequency_hz"]
          }
        },
        "vibrato_lfo": {
          "type": "object",
          "properties": {
            "rate_hz": { "type": "number" },
            "depth_cents": { "type": "number" }
          }
        },
        "noise_aspiration_gain": { "type": "number", "minimum": 0, "maximum": 1 },
        "subharmonic_chaos_gain": { "type": "number", "minimum": 0, "maximum": 1 }
      },
      "required": ["model", "f0_trajectory"]
    },
    "formant_filter_bank": {
      "type": "object",
      "properties": {
        "topology": { "type": "string", "enum": ["cascade", "parallel"] },
        "formants": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "id": { "type": "string" },
              "bandwidth_hz": { "type": "number" },
              "gain_db": { "type": "number" },
              "freq_trajectory": {
                "type": "array",
                "items": {
                  "type": "object",
                  "properties": {
                    "time_ratio": { "type": "number", "minimum": 0, "maximum": 1 },
                    "frequency_hz": { "type": "number" }
                  },
                  "required": ["time_ratio", "frequency_hz"]
                }
              }
            },
            "required": ["id", "bandwidth_hz", "freq_trajectory"]
          }
        }
      },
      "required": ["topology", "formants"]
    },
    "amplitude_envelope": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "time_ratio": { "type": "number", "minimum": 0, "maximum": 1 },
          "gain": { "type": "number", "minimum": 0, "maximum": 1 }
        },
        "required": ["time_ratio", "gain"]
      }
    }
  },
  "required": ["segment_id", "duration_ms", "boundary_transition", "source_excitation", "formant_filter_bank", "amplitude_envelope"]
}
```

---

## 6. End-to-End Sequence Example: Predator Growl to Wolf Howl

```json
{
  "sequence_name": "growl_to_howl_transition",
  "segments": [
    {
      "segment_id": "low_growl",
      "duration_ms": 1000,
      "boundary_transition": {
        "mode": "coarticulate",
        "transition_duration_ms": 180,
        "interpolation_curve": "smootherstep"
      },
      "source_excitation": {
        "model": "hybrid_growl",
        "f0_trajectory": [
          { "time_ratio": 0.0, "frequency_hz": 75.0 },
          { "time_ratio": 0.6, "frequency_hz": 82.0 },
          { "time_ratio": 1.0, "frequency_hz": 110.0 }
        ],
        "vibrato_lfo": { "rate_hz": 8.0, "depth_cents": 35.0 },
        "noise_aspiration_gain": 0.25,
        "subharmonic_chaos_gain": 0.65
      },
      "formant_filter_bank": {
        "topology": "cascade",
        "formants": [
          {
            "id": "F1",
            "bandwidth_hz": 80.0,
            "gain_db": 0.0,
            "freq_trajectory": [{ "time_ratio": 0.0, "frequency_hz": 320.0 }, { "time_ratio": 1.0, "frequency_hz": 400.0 }]
          },
          {
            "id": "F2",
            "bandwidth_hz": 110.0,
            "gain_db": -4.0,
            "freq_trajectory": [{ "time_ratio": 0.0, "frequency_hz": 850.0 }, { "time_ratio": 1.0, "frequency_hz": 1050.0 }]
          },
          {
            "id": "F3",
            "bandwidth_hz": 160.0,
            "gain_db": -12.0,
            "freq_trajectory": [{ "time_ratio": 0.0, "frequency_hz": 1800.0 }, { "time_ratio": 1.0, "frequency_hz": 2100.0 }]
          }
        ]
      },
      "amplitude_envelope": [
        { "time_ratio": 0.0, "gain": 0.0 },
        { "time_ratio": 0.15, "gain": 0.9 },
        { "time_ratio": 0.85, "gain": 0.95 },
        { "time_ratio": 1.0, "gain": 0.7 }
      ]
    },
    {
      "segment_id": "sustained_howl",
      "duration_ms": 2200,
      "boundary_transition": {
        "mode": "glottal_stop",
        "transition_duration_ms": 25,
        "glottal_silence_ms": 20,
        "glottal_pop_intensity": 0.4
      },
      "source_excitation": {
        "model": "rosenberg_pulse",
        "f0_trajectory": [
          { "time_ratio": 0.0, "frequency_hz": 220.0 },
          { "time_ratio": 0.3, "frequency_hz": 480.0 },
          { "time_ratio": 0.75, "frequency_hz": 450.0 },
          { "time_ratio": 1.0, "frequency_hz": 280.0 }
        ],
        "vibrato_lfo": { "rate_hz": 5.5, "depth_cents": 15.0 },
        "noise_aspiration_gain": 0.05,
        "subharmonic_chaos_gain": 0.0
      },
      "formant_filter_bank": {
        "topology": "cascade",
        "formants": [
          {
            "id": "F1",
            "bandwidth_hz": 60.0,
            "gain_db": 0.0,
            "freq_trajectory": [{ "time_ratio": 0.0, "frequency_hz": 420.0 }, { "time_ratio": 1.0, "frequency_hz": 380.0 }]
          },
          {
            "id": "F2",
            "bandwidth_hz": 90.0,
            "gain_db": -6.0,
            "freq_trajectory": [{ "time_ratio": 0.0, "frequency_hz": 1150.0 }, { "time_ratio": 1.0, "frequency_hz": 920.0 }]
          },
          {
            "id": "F3",
            "bandwidth_hz": 140.0,
            "gain_db": -16.0,
            "freq_trajectory": [{ "time_ratio": 0.0, "frequency_hz": 2350.0 }, { "time_ratio": 1.0, "frequency_hz": 2150.0 }]
          }
        ]
      },
      "amplitude_envelope": [
        { "time_ratio": 0.0, "gain": 0.7 },
        { "time_ratio": 0.2, "gain": 1.0 },
        { "time_ratio": 0.8, "gain": 0.8 },
        { "time_ratio": 1.0, "gain": 0.0 }
      ]
    }
  ]
}
```