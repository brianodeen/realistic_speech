#include "vocalis/orchestra/bioacoustics.hpp"
#include <cmath>
#include <algorithm>

namespace vocalis::orchestra {

BioacousticModulator::BioacousticModulator(uint32_t sampleRate) noexcept
    : sampleRate_(sampleRate > 0 ? sampleRate : DEFAULT_SAMPLE_RATE) {
    // Allocate 100ms circular delay buffer
    delayBuffer_.resize(sampleRate_ / 10, 0.0f);
    reset();
    setParams(params_);
}

void BioacousticModulator::reset() noexcept {
    purrPhase_ = 0.0;
    snarlPhase_ = 0.0;
    std::fill(delayBuffer_.begin(), delayBuffer_.end(), 0.0f);
    delayWriteIndex_ = 0;
}

void BioacousticModulator::setSampleRate(uint32_t sampleRate) noexcept {
    sampleRate_ = sampleRate > 0 ? sampleRate : DEFAULT_SAMPLE_RATE;
    delayBuffer_.resize(sampleRate_ / 10, 0.0f);
    reset();
    setParams(params_);
}

void BioacousticModulator::setParams(const BioacousticParams& params) noexcept {
    params_ = params;
    // Compute delay samples D = round(fs / (2 * f0))
    SampleReal f0 = std::max(20.0, params_.nominalF0Hz);
    SampleReal fs = static_cast<SampleReal>(sampleRate_);
    size_t d = static_cast<size_t>(std::round(fs / (2.0 * f0)));
    delayLengthSamples_ = std::clamp(d, size_t{1}, delayBuffer_.size() - 1);
}

SampleReal BioacousticModulator::computeGatingMultiplier(SampleReal dt) noexcept {
    SampleReal multiplier = 1.0;

    // Feline 20-30 Hz neural purr gating
    if (params_.purrActive) {
        purrPhase_ += params_.purrTwitchRateHz * dt;
        if (purrPhase_ >= 1.0) purrPhase_ -= 1.0;

        // Purr is an asymmetric pulse wave (neural burst followed by relaxation)
        SampleReal twitch = 0.5 * (1.0 + std::sin(TWO_PI * purrPhase_));
        twitch = std::pow(twitch, 1.8); // Sharpen twitch pulses
        SampleReal purrMod = 1.0 - params_.purrDepth * (1.0 - twitch);
        multiplier *= purrMod;
    }

    // Canine 40-55 Hz mucosal snarl tremor
    if (params_.snarlActive) {
        snarlPhase_ += params_.snarlFlutterHz * dt;
        if (snarlPhase_ >= 1.0) snarlPhase_ -= 1.0;

        SampleReal flutter = 0.5 * (1.0 + std::sin(TWO_PI * snarlPhase_));
        SampleReal snarlMod = 1.0 - params_.snarlFlutterDepth * (1.0 - flutter);
        multiplier *= snarlMod;
    }

    return multiplier;
}

Sample BioacousticModulator::processChaos(Sample input) noexcept {
    if (!params_.growlChaosActive || delayBuffer_.empty()) {
        return input;
    }

    SampleReal sin = static_cast<SampleReal>(input);

    // Read delayed sample s_in[n - D]
    size_t readIdx = (delayWriteIndex_ + delayBuffer_.size() - delayLengthSamples_) % delayBuffer_.size();
    SampleReal sDelay = static_cast<SampleReal>(delayBuffer_[readIdx]);

    // Delay-differential chaos growl equation (Section 2.1):
    // s_out[n] = (1 - beta) * s_in[n] + beta * (s_in[n] + alpha * s_in[n - D] * |s_in[n]|)
    SampleReal chaoticTerm = sin + params_.growlAlpha * sDelay * std::abs(sin);
    SampleReal sout = (1.0 - params_.growlBeta) * sin + params_.growlBeta * chaoticTerm;

    // Soft saturate to avoid unbounded feedback explosion
    sout = std::tanh(sout);

    // Store in circular buffer
    delayBuffer_[delayWriteIndex_] = input;
    delayWriteIndex_ = (delayWriteIndex_ + 1) % delayBuffer_.size();

    return static_cast<Sample>(sout);
}

} // namespace vocalis::orchestra
