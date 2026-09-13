#include "vocalis/orchestra/radiation_bell.hpp"
#include <cmath>
#include <algorithm>

namespace vocalis::orchestra {

RadiationBell::RadiationBell(uint32_t sampleRate) noexcept
    : sampleRate_(sampleRate > 0 ? sampleRate : DEFAULT_SAMPLE_RATE) {
    reset();
    updateFilter();
}

void RadiationBell::reset() noexcept {
    lastInput_ = 0.0;
    radiationFilter_.reset();
}

void RadiationBell::updateFilter() noexcept {
    // 1st order differentiator filter: H(z) = 1 - alpha * z^-1
    // Acts as a high-pass boost of +6dB/octave above the boundary transition cutoff (~150-300 Hz)
    SampleReal cutoff = 200.0 / std::max(0.5, effectiveTractScale());
    radiationFilter_.setHighPass(cutoff, 0.707, sampleRate_);
}

Sample RadiationBell::process(Sample input) noexcept {
    SampleReal in = static_cast<SampleReal>(input);

    // First-order acoustic radiation boundary differentiation (+6 dB/octave):
    // y[n] = x[n] - alpha * x[n-1]
    SampleReal rad = in - params_.radiationDerivativeFactor * lastInput_;
    lastInput_ = in;

    // Dispersal gain calibration
    SampleReal output = rad * 6.0 * params_.sphericalRadiationGain;

    return static_cast<Sample>(output);
}

void RadiationBell::process(SampleSpan buffer) noexcept {
    for (auto& s : buffer) {
        s = process(s);
    }
}

} // namespace vocalis::orchestra
