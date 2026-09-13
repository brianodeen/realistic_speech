#pragma once

#include "vocalis/types.hpp"
#include "vocalis/dsp/biquad.hpp"
#include <array>

namespace vocalis::orchestra {

inline constexpr size_t MAX_FORMANTS = 6;

struct FormantConfig {
    SampleReal frequencyHz{500.0};
    SampleReal bandwidthHz{80.0};
    SampleReal gainLinear{1.0};
};

struct VocalTractParams {
    std::array<FormantConfig, MAX_FORMANTS> formants{
        FormantConfig{700.0, 90.0, 1.0},   // F1 (pharynx / vowel height)
        FormantConfig{1200.0, 110.0, 0.7}, // F2 (oral cavity / front-back)
        FormantConfig{2600.0, 160.0, 0.4}, // F3 (tongue tip / rhoticity)
        FormantConfig{3300.0, 200.0, 0.25},// F4 (head / speaker identity)
        FormantConfig{4200.0, 250.0, 0.15},// F5 (high anatomical cavity)
        FormantConfig{5500.0, 300.0, 0.1}  // F6 (sibilant coupling)
    };

    // Velic Port (Nasal coupling)
    SampleReal velicAperture{0.0};         // 0.0 = velum closed (oral vowel), 1.0 = fully lowered (nasal consonant)
    SampleReal nasalResonanceHz{250.0};    // Fixed low nasal murmur resonance
    SampleReal nasalZeroHz{750.0};         // Fixed nasal anti-resonance zero

    // Biological fleshiness absorption
    SampleReal fleshinessDamping{0.35};    // 0.0 = metallic/hard, 1.0 = maximum viscoelastic tissue absorption
    SampleReal vocalTractLengthScale{1.0}; // 1.0 = normal adult human, 0.85 = child/small creature, 1.3 = giant/beast
};

/// @brief Instrument 5: The Resonating Body Chambers (Pharynx, Oral, Nasal Cavities)
/// Dynamically filters glottal and turbulent sound sources through a cascade of 6 biquad resonators,
/// nasal velic branch, and viscoelastic mucous membrane damping.
class ResonantChambers {
public:
    explicit ResonantChambers(uint32_t sampleRate = DEFAULT_SAMPLE_RATE) noexcept;

    void reset() noexcept;

    void setSampleRate(uint32_t sampleRate) noexcept;

    void setParams(const VocalTractParams& params) noexcept;

    /// @brief Update individual formant target
    void setFormant(size_t index, SampleReal freqHz, SampleReal bandwidthHz, SampleReal gain) noexcept;

    /// @brief Update velic (nasal) aperture
    void setVelicAperture(SampleReal aperture) noexcept;

    /// @brief Update fleshiness damping
    void setFleshinessDamping(SampleReal damping) noexcept;

    /// @brief Process single sample through the vocal tract acoustic filter cascade
    [[nodiscard]] Sample process(Sample excitation) noexcept;

    /// @brief Process audio buffer in-place
    void process(SampleSpan buffer) noexcept;

    [[nodiscard]] const VocalTractParams& params() const noexcept { return params_; }

private:
    void updateFilters() noexcept;

    uint32_t sampleRate_{DEFAULT_SAMPLE_RATE};
    VocalTractParams params_{};

    std::array<dsp::Biquad, MAX_FORMANTS> formantFilters_{};
    dsp::Biquad nasalPoleFilter_{};
    dsp::Biquad nasalZeroFilter_{};
    dsp::Biquad fleshinessFilter_{}; // High-shelf / lowpass for viscoelastic tissue damping
};

} // namespace vocalis::orchestra
