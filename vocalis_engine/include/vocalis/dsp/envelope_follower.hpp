#pragma once

#include "vocalis/types.hpp"
#include <cmath>
#include <algorithm>

namespace vocalis::dsp {

class EnvelopeFollower {
public:
    EnvelopeFollower() noexcept = default;
    EnvelopeFollower(SampleReal attackTimeMs, SampleReal releaseTimeMs, uint32_t sampleRate) noexcept {
        configure(attackTimeMs, releaseTimeMs, sampleRate);
    }

    void configure(SampleReal attackTimeMs, SampleReal releaseTimeMs, uint32_t sampleRate) noexcept {
        if (sampleRate == 0) return;
        SampleReal fs = static_cast<SampleReal>(sampleRate);
        attackCoeff_ = std::exp(-1.0 / (std::max(attackTimeMs, 0.1) * 0.001 * fs));
        releaseCoeff_ = std::exp(-1.0 / (std::max(releaseTimeMs, 0.1) * 0.001 * fs));
    }

    void reset() noexcept {
        envelope_ = 0.0;
    }

    [[nodiscard]] SampleReal process(Sample input) noexcept {
        SampleReal val = std::abs(static_cast<SampleReal>(input));
        if (val > envelope_) {
            envelope_ = attackCoeff_ * envelope_ + (1.0 - attackCoeff_) * val;
        } else {
            envelope_ = releaseCoeff_ * envelope_ + (1.0 - releaseCoeff_) * val;
        }
        return envelope_;
    }

    [[nodiscard]] SampleReal currentLevel() const noexcept { return envelope_; }

private:
    SampleReal attackCoeff_{0.0};
    SampleReal releaseCoeff_{0.0};
    SampleReal envelope_{0.0};
};

} // namespace vocalis::dsp
