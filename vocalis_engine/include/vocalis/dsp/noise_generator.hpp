#pragma once

#include "vocalis/types.hpp"
#include "vocalis/dsp/biquad.hpp"
#include <cstdint>

namespace vocalis::dsp {

/// @brief High-speed pseudo-random noise generator using Xoshiro256**
class NoiseGenerator {
public:
    explicit NoiseGenerator(uint64_t seed = 0x853c49e6748fea9bULL) noexcept {
        setSeed(seed);
    }

    void setSeed(uint64_t seed) noexcept;

    /// @brief Generate uniform white noise sample in [-1.0, 1.0]
    [[nodiscard]] Sample nextWhite() noexcept;

    /// @brief Generate Gaussian noise sample (mean 0, stddev ~0.3)
    [[nodiscard]] Sample nextGaussian() noexcept;

    /// @brief Generate pink noise sample (1/f spectral tilt)
    [[nodiscard]] Sample nextPink() noexcept;

    /// @brief Generate bandpassed turbulent noise sample around centerFreq
    [[nodiscard]] Sample nextTurbulent(SampleReal centerFreqHz, SampleReal bandwidthHz, uint32_t sampleRate) noexcept;

    /// @brief Fill buffer with white noise
    void fillWhite(SampleSpan buffer) noexcept;

private:
    [[nodiscard]] uint64_t nextU64() noexcept;

    uint64_t s_[4]{0x123456789ULL, 0x987654321ULL, 0xABCDEF012ULL, 0x3456789ABULL};

    // Pink noise Paul Kellet filter state
    SampleReal b0_{0.0}, b1_{0.0}, b2_{0.0}, b3_{0.0}, b4_{0.0}, b5_{0.0}, b6_{0.0};

    // Turbulent bandpass filter
    Biquad turbFilter_;
    SampleReal lastCenterFreq_{0.0};
    SampleReal lastBandwidth_{0.0};
    uint32_t lastSampleRate_{0};
};

} // namespace vocalis::dsp
