#include "vocalis/orchestra/friction_nozzles.hpp"
#include <cmath>
#include <algorithm>

namespace vocalis::orchestra {

FrictionNozzles::FrictionNozzles(uint32_t sampleRate) noexcept
    : sampleRate_(sampleRate > 0 ? sampleRate : DEFAULT_SAMPLE_RATE) {
    reset();
    setParams(params_);
}

void FrictionNozzles::reset() noexcept {
    burstDecay_ = 0.0;
    lastAperture_ = 50.0;
    bandpassFilter_.reset();
    raspFilter_.reset();
}

void FrictionNozzles::setParams(const ConstrictionParams& params) noexcept {
    params_ = params;
    bandpassFilter_.setBandPass(params_.centerFreqHz, params_.bandwidthHz, sampleRate_);
    raspFilter_.setBandPass(std::max(100.0, params_.centerFreqHz * 0.4), params_.bandwidthHz * 0.5, sampleRate_);
}

void FrictionNozzles::triggerPlosiveBurst(SampleReal burstEnergy) noexcept {
    burstDecay_ = std::clamp(burstEnergy, 0.0, 3.0);
}

Sample FrictionNozzles::step(SampleReal airflowDrive) noexcept {
    lastAperture_ = params_.apertureMm2;

    SampleReal turbulence = 0.0;

    // Constriction produces turbulence when aperture is narrow (0.1 to 20 mm^2)
    if (params_.apertureMm2 < 25.0 && params_.apertureMm2 > 0.05 && airflowDrive > 0.01) {
        // Narrower aperture generates faster flow velocity: velocity ~ flow / area
        SampleReal effectiveArea = std::max(0.2, params_.apertureMm2);
        SampleReal flowVelocity = std::min(5.0, airflowDrive / (effectiveArea * 0.1));

        Sample rawNoise = noiseGen_.nextWhite();
        Sample filteredNoise = bandpassFilter_.process(rawNoise);

        // Reynolds vortex shedding (mucosal flutter / rasping modulation)
        if (params_.vortexSheddingRate > 0.01) {
            Sample raspNoise = raspFilter_.process(noiseGen_.nextWhite());
            filteredNoise = filteredNoise * 0.8f + raspNoise * static_cast<Sample>(params_.vortexSheddingRate * 0.3);
        }

        SampleReal apertureGain = (25.0 - params_.apertureMm2) / 25.0;
        turbulence = filteredNoise * flowVelocity * apertureGain * 0.4;
    }

    // Process plosive release transient burst
    if (burstDecay_ > 0.001) {
        Sample burstSample = noiseGen_.nextWhite() * static_cast<Sample>(burstDecay_);
        turbulence += burstSample * 0.6;
        // Fast exponential decay (~5-15 ms burst duration)
        SampleReal decayFactor = std::exp(-500.0 / static_cast<SampleReal>(sampleRate_));
        burstDecay_ *= decayFactor;
    }

    return static_cast<Sample>(turbulence);
}

} // namespace vocalis::orchestra
