#pragma once

#include "vocalis/types.hpp"
#include <vector>

namespace vocalis::orchestra {

struct BioacousticParams {
    // Feline Neural Purr Oscillator
    bool purrActive{false};
    SampleReal purrTwitchRateHz{25.0};     // 20 - 30 Hz
    SampleReal purrDepth{0.85};            // 0.0 - 1.0 amplitude gating

    // Canine Snarl / Mucosal Tremor
    bool snarlActive{false};
    SampleReal snarlFlutterHz{48.0};       // 40 - 55 Hz
    SampleReal snarlFlutterDepth{0.6};     // Tremor amplitude modulation
    SampleReal lipCurlExposure{0.0};       // 0.0 - 1.0 brightens upper formants

    // Non-linear Delay-Differential Chaos (Predator Growl)
    bool growlChaosActive{false};
    SampleReal growlAlpha{1.2};            // Chaos feedback gain
    SampleReal growlBeta{0.65};            // Chaos blend factor (0.0 = clean, 1.0 = fully chaotic)
    SampleReal nominalF0Hz{100.0};         // Used to tune delay length D = fs / (2 * f0)
};

/// @brief Instrument 4: The Bioacoustic Modulator (Specialized Creature Anatomy)
/// Implements 25 Hz neural feline purr gating, 48 Hz canine mucosal snarl,
/// and non-linear delay-differential chaos equations for deep predator growls.
class BioacousticModulator {
public:
    explicit BioacousticModulator(uint32_t sampleRate = DEFAULT_SAMPLE_RATE) noexcept;

    void reset() noexcept;

    void setSampleRate(uint32_t sampleRate) noexcept;

    void setParams(const BioacousticParams& params) noexcept;

    /// @brief Computes amplitude gating multiplier for respiration / glottis (purr / snarl)
    [[nodiscard]] SampleReal computeGatingMultiplier(SampleReal dt) noexcept;

    /// @brief Applies non-linear delay differential chaos equation to acoustic waveform
    /// s_out[n] = (1 - beta)*s_in[n] + beta*(s_in[n] + alpha * s_in[n - D] * |s_in[n]|)
    [[nodiscard]] Sample processChaos(Sample input) noexcept;

    [[nodiscard]] const BioacousticParams& params() const noexcept { return params_; }

private:
    uint32_t sampleRate_{DEFAULT_SAMPLE_RATE};
    BioacousticParams params_{};

    // Purr oscillator phase [0, 1)
    SampleReal purrPhase_{0.0};

    // Canine mucosal flutter phase [0, 1)
    SampleReal snarlPhase_{0.0};

    // Circular delay buffer for non-linear growl equation
    std::vector<Sample> delayBuffer_;
    size_t delayWriteIndex_{0};
    size_t delayLengthSamples_{220};
};

} // namespace vocalis::orchestra
