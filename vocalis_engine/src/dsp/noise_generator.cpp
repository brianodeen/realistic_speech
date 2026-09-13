#include "vocalis/dsp/noise_generator.hpp"
#include <cmath>

namespace vocalis::dsp {

static inline uint64_t rotl(const uint64_t x, int k) noexcept {
    return (x << k) | (x >> (64 - k));
}

void NoiseGenerator::setSeed(uint64_t seed) noexcept {
    // SplitMix64 initialization
    uint64_t z = seed;
    for (int i = 0; i < 4; ++i) {
        z += 0x9e3779b97f4a7c15ULL;
        z = (z ^ (z >> 30)) * 0xbf58476d1ce4e5b9ULL;
        z = (z ^ (z >> 27)) * 0x94d049bb133111ebULL;
        s_[i] = z ^ (z >> 31);
    }
}

uint64_t NoiseGenerator::nextU64() noexcept {
    const uint64_t result = rotl(s_[1] * 5, 7) * 9;
    const uint64_t t = s_[1] << 17;

    s_[2] ^= s_[0];
    s_[3] ^= s_[1];
    s_[1] ^= s_[2];
    s_[0] ^= s_[3];

    s_[2] ^= t;
    s_[3] = rotl(s_[3], 45);

    return result;
}

Sample NoiseGenerator::nextWhite() noexcept {
    // 53-bit double precision float in [-1.0, 1.0]
    uint64_t v = nextU64();
    double norm = static_cast<double>(v >> 11) * (1.0 / 9007199254740992.0); // [0, 1)
    return static_cast<Sample>(norm * 2.0 - 1.0);
}

Sample NoiseGenerator::nextGaussian() noexcept {
    // Central limit approximation using 4 uniform samples
    Sample sum = nextWhite() + nextWhite() + nextWhite() + nextWhite();
    return sum * 0.25f;
}

Sample NoiseGenerator::nextPink() noexcept {
    // Paul Kellet's filtered white noise algorithm (approx 3dB/octave falloff)
    Sample white = nextWhite();
    b0_ = 0.99886 * b0_ + white * 0.0555179;
    b1_ = 0.99332 * b1_ + white * 0.0750759;
    b2_ = 0.96900 * b2_ + white * 0.1538520;
    b3_ = 0.86650 * b3_ + white * 0.3104856;
    b4_ = 0.55000 * b4_ + white * 0.5329522;
    b5_ = -0.7616 * b5_ - white * 0.0168980;
    Sample pink = static_cast<Sample>(b0_ + b1_ + b2_ + b3_ + b4_ + b5_ + b6_ + white * 0.5362);
    b6_ = white * 0.115926;
    return pink * 0.11f;
}

Sample NoiseGenerator::nextTurbulent(SampleReal centerFreqHz, SampleReal bandwidthHz, uint32_t sampleRate) noexcept {
    if (centerFreqHz != lastCenterFreq_ || bandwidthHz != lastBandwidth_ || sampleRate != lastSampleRate_) {
        turbFilter_.setBandPass(centerFreqHz, bandwidthHz, sampleRate);
        lastCenterFreq_ = centerFreqHz;
        lastBandwidth_ = bandwidthHz;
        lastSampleRate_ = sampleRate;
    }
    Sample raw = nextWhite();
    return turbFilter_.process(raw);
}

void NoiseGenerator::fillWhite(SampleSpan buffer) noexcept {
    for (auto& s : buffer) {
        s = nextWhite();
    }
}

} // namespace vocalis::dsp
