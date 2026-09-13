#pragma once

#include "vocalis/types.hpp"
#include "vocalis/dsp/biquad.hpp"

namespace vocalis::orchestra {

struct RadiationParams {
    SampleReal lipRoundingCm{0.0};             // Lip protrusion (0.0 to 2.5 cm)
    SampleReal sphericalRadiationGain{1.0};    // Spherical baffle scale
    SampleReal radiationDerivativeFactor{0.96};// 1st-order boundary differentiator factor (~0.95 - 0.98)
};

/// @brief Instrument 6: The Radiation & Coupling Bell (Lips & Nostrils)
/// Simulates 3D spherical soundfield radiation impedance with a +6 dB/octave high-pass derivative filter
/// and acoustic length extension from lip rounding and protrusion.
class RadiationBell {
public:
    explicit RadiationBell(uint32_t sampleRate = DEFAULT_SAMPLE_RATE) noexcept;

    void reset() noexcept;

    void setSampleRate(uint32_t sampleRate) noexcept {
        sampleRate_ = sampleRate > 0 ? sampleRate : DEFAULT_SAMPLE_RATE;
        updateFilter();
    }

    void setParams(const RadiationParams& params) noexcept {
        params_ = params;
        updateFilter();
    }

    void setLipRounding(SampleReal cm) noexcept {
        params_.lipRoundingCm = std::clamp(cm, 0.0, 5.0);
        updateFilter();
    }

    /// @brief Computes length scale multiplier induced by lip protrusion
    /// Standard human vocal tract ~17.5 cm. Protrusion extends this length.
    [[nodiscard]] SampleReal effectiveTractScale() const noexcept {
        SampleReal baseLengthCm = 17.5;
        return (baseLengthCm + params_.lipRoundingCm) / baseLengthCm;
    }

    /// @brief Process single sample through spherical radiation boundary
    [[nodiscard]] Sample process(Sample input) noexcept;

    /// @brief Process buffer in-place
    void process(SampleSpan buffer) noexcept;

    [[nodiscard]] const RadiationParams& params() const noexcept { return params_; }

private:
    void updateFilter() noexcept;

    uint32_t sampleRate_{DEFAULT_SAMPLE_RATE};
    RadiationParams params_{};
    dsp::Biquad radiationFilter_{};
    SampleReal lastInput_{0.0};
};

} // namespace vocalis::orchestra
