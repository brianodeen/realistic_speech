#pragma once

#include "vocalis/types.hpp"
#include <cmath>

namespace vocalis::dsp {

enum class BiquadType : uint8_t {
    Resonator,       // Section 5.3 formant 2nd order peak resonator
    AntiResonator,   // Nasal anti-formant zero / notch
    LowPass,
    HighPass,
    BandPass
};

struct BiquadCoeffs {
    SampleReal b0{1.0};
    SampleReal b1{0.0};
    SampleReal b2{0.0};
    SampleReal a1{0.0};
    SampleReal a2{0.0};
};

class Biquad {
public:
    Biquad() noexcept = default;

    /// @brief Reset state memory
    void reset() noexcept {
        s1_ = 0.0;
        s2_ = 0.0;
    }

    /// @brief Set coefficients directly
    void setCoefficients(const BiquadCoeffs& coeffs) noexcept {
        coeffs_ = coeffs;
    }

    /// @brief Configure as a formant resonator per Section 5.3
    /// R = exp(-pi * B / fs), theta = 2 * pi * fr / fs
    /// y[n] = 2*R*cos(theta)*y[n-1] - R^2*y[n-2] + (1 - R)*x[n]
    void setResonator(SampleReal centerFreqHz, SampleReal bandwidthHz, uint32_t sampleRate) noexcept;

    /// @brief Configure as an anti-resonator (spectral zero / notch) for nasal side-branches
    void setAntiResonator(SampleReal zeroFreqHz, SampleReal bandwidthHz, uint32_t sampleRate) noexcept;

    /// @brief Configure as high-pass filter (e.g. lip radiation baffle +6dB/oct)
    void setHighPass(SampleReal cutoffHz, SampleReal q, uint32_t sampleRate) noexcept;

    /// @brief Configure as low-pass filter
    void setLowPass(SampleReal cutoffHz, SampleReal q, uint32_t sampleRate) noexcept;

    /// @brief Configure as band-pass filter (for fricative turbulence shaping)
    void setBandPass(SampleReal centerFreqHz, SampleReal bandwidthHz, uint32_t sampleRate) noexcept;

    /// @brief Process a single sample using Direct Form II Transposed
    [[nodiscard]] inline Sample process(Sample in) noexcept {
        SampleReal x = static_cast<SampleReal>(in);
        SampleReal y = coeffs_.b0 * x + s1_;
        s1_ = coeffs_.b1 * x - coeffs_.a1 * y + s2_;
        s2_ = coeffs_.b2 * x - coeffs_.a2 * y;
        return static_cast<Sample>(y);
    }

    /// @brief Process an audio span in-place
    void process(SampleSpan buffer) noexcept {
        for (auto& s : buffer) {
            s = process(s);
        }
    }

    [[nodiscard]] const BiquadCoeffs& coefficients() const noexcept { return coeffs_; }

private:
    BiquadCoeffs coeffs_{};
    SampleReal s1_{0.0};
    SampleReal s2_{0.0};
};

} // namespace vocalis::dsp
