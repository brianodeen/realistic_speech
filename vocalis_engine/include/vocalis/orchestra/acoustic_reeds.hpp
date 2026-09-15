#pragma once

#include "vocalis/types.hpp"
#include "vocalis/dsp/blit_blep.hpp"
#include "vocalis/dsp/noise_generator.hpp"
#include "vocalis/dsp/stochastic_process.hpp"

namespace vocalis::orchestra {

struct GlottalParams {
    SampleReal f0Hz{120.0};
    SampleReal openQuotient{0.66};      // Oq: 0.66 = relaxed, natural conversational modal voice
    SampleReal speedQuotient{1.8};      // Sq: 1.8 = relaxed vocal fold closure slope
    SampleReal jitterPercent{0.4};      // Micro pitch perturbation
    SampleReal shimmerPercent{0.8};     // Micro amplitude perturbation
    SampleReal aspirationGain{0.035};   // Glottal turbulent breathiness
    SampleReal returnPhaseTa{0.055};    // Normalized return phase time constant (Ta) for unstrained warm timbre

    // Ventricular / False folds
    SampleReal ventricularEngagement{0.0}; // 0.0 to 1.0
    SampleReal subharmonicRatio{2.0};      // 2.0 = f0/2, 3.0 = f0/3

    // Dual Syrinx (Avian mode)
    bool syrinxEnabled{false};
    SampleReal syrinxLeftF0Hz{1800.0};
    SampleReal syrinxRightF0Hz{2400.0};
    SampleReal syrinxBalance{0.5};      // 0.0 = left only, 1.0 = right only
};

/// @brief Instrument 2: The Acoustic Reeds (Vocal Folds & Glottal Excitation)
/// Implements Fant-Liljencrants (LF) glottal model, anti-aliased synthesis,
/// ventricular subharmonic folds, and dual syrinx avian polyphony.
class AcousticReeds {
public:
    explicit AcousticReeds(uint32_t sampleRate = DEFAULT_SAMPLE_RATE) noexcept;

    void reset() noexcept;

    void setSampleRate(uint32_t sampleRate) noexcept {
        sampleRate_ = (sampleRate > 0) ? sampleRate : DEFAULT_SAMPLE_RATE;
    }

    void setParams(const GlottalParams& params) noexcept {
        params_ = params;
    }

    void setF0(SampleReal f0Hz) noexcept {
        params_.f0Hz = std::max(10.0, f0Hz);
    }

    /// @brief Generate next glottal excitation sample
    /// @param subglottalDrive Dynamic drive from Instrument 1 (Air Bellows)
    [[nodiscard]] Sample step(SampleReal subglottalDrive) noexcept;

    /// @brief Fill an audio buffer with glottal excitation
    void process(SampleSpan output, SampleReal subglottalDrive) noexcept;

    [[nodiscard]] SampleReal phase() const noexcept { return phase_; }
    [[nodiscard]] const GlottalParams& params() const noexcept { return params_; }

private:
    [[nodiscard]] SampleReal evaluateLF(SampleReal phaseNormalized, SampleReal f0) noexcept;

    uint32_t sampleRate_{DEFAULT_SAMPLE_RATE};
    GlottalParams params_{};
    dsp::NoiseGenerator noiseGen_{};

    SampleReal phase_{0.0};             // Primary true vocal fold phase [0, 1)
    SampleReal ventricularPhase_{0.0};  // Subharmonic false vocal fold phase [0, 1)
    SampleReal syrinxLeftPhase_{0.0};   // Avian left syrinx phase [0, 1)
    SampleReal syrinxRightPhase_{0.0};  // Avian right syrinx phase [0, 1)

    // Stochastic Brownian pulse morphing and filter state
    dsp::AutoregressiveDrift oqDrift_{0.88, 0.025};
    dsp::AutoregressiveDrift sqDrift_{0.88, 0.08};
    SampleReal oqOffset_{0.0};
    SampleReal sqOffset_{0.0};
    SampleReal currentJitterOffset_{0.0};
    SampleReal currentShimmerFactor_{1.0};
    SampleReal tiltState_{0.0};
    size_t periodSampleCount_{0};
};

} // namespace vocalis::orchestra
