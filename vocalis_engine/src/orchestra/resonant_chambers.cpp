#include "vocalis/orchestra/resonant_chambers.hpp"
#include <cmath>
#include <algorithm>

namespace vocalis::orchestra {

ResonantChambers::ResonantChambers(uint32_t sampleRate) noexcept
    : sampleRate_(sampleRate > 0 ? sampleRate : DEFAULT_SAMPLE_RATE) {
    reset();
    updateFilters();
}

void ResonantChambers::reset() noexcept {
    for (auto& f : formantFilters_) {
        f.reset();
    }
    nasalPoleFilter_.reset();
    nasalZeroFilter_.reset();
    fleshinessFilter_.reset();
}

void ResonantChambers::setSampleRate(uint32_t sampleRate) noexcept {
    sampleRate_ = sampleRate > 0 ? sampleRate : DEFAULT_SAMPLE_RATE;
    reset();
    updateFilters();
}

void ResonantChambers::setParams(const VocalTractParams& params) noexcept {
    params_ = params;
    updateFilters();
}

void ResonantChambers::setFormant(size_t index, SampleReal freqHz, SampleReal bandwidthHz, SampleReal gain) noexcept {
    if (index < MAX_FORMANTS) {
        params_.formants[index].frequencyHz = freqHz;
        params_.formants[index].bandwidthHz = bandwidthHz;
        params_.formants[index].gainLinear = gain;
        updateFilters();
    }
}

void ResonantChambers::setVelicAperture(SampleReal aperture) noexcept {
    params_.velicAperture = std::clamp(aperture, 0.0, 1.0);
    updateFilters();
}

void ResonantChambers::setFleshinessDamping(SampleReal damping) noexcept {
    params_.fleshinessDamping = std::clamp(damping, 0.0, 1.0);
    updateFilters();
}

void ResonantChambers::updateFilters() noexcept {
    SampleReal scale = std::clamp(params_.vocalTractLengthScale, 0.5, 2.5);

    // Fleshiness damping widens formant bandwidths and softens sharp resonances
    SampleReal bandwidthDampingFactor = 1.0 + params_.fleshinessDamping * 0.8;

    for (size_t i = 0; i < MAX_FORMANTS; ++i) {
        SampleReal targetFreq = params_.formants[i].frequencyHz / scale;
        SampleReal targetBw = params_.formants[i].bandwidthHz * bandwidthDampingFactor;
        formantFilters_[i].setCascadeResonator(targetFreq, targetBw, sampleRate_);
    }

    // Nasal side-branch filters
    if (params_.velicAperture > 0.01) {
        nasalPoleFilter_.setCascadeResonator(params_.nasalResonanceHz, 120.0 * bandwidthDampingFactor, sampleRate_);
        nasalZeroFilter_.setAntiResonator(params_.nasalZeroHz, 180.0, sampleRate_);
    }

    // Viscoelastic tissue absorption filter (soft low-pass above 5kHz based on fleshiness)
    SampleReal fleshCutoff = 8000.0 - params_.fleshinessDamping * 3500.0;
    fleshinessFilter_.setLowPass(fleshCutoff, 0.707, sampleRate_);
}

Sample ResonantChambers::process(Sample excitation) noexcept {
    Sample sig = excitation;

    // Klatt Cascade (Series) vocal tract filter bank:
    // Glottal excitation passes sequentially through pharyngeal, oral, and head cavities:
    // y[n] = R5(R4(R3(R2(R1(excitation)))))
    for (size_t i = 0; i < MAX_FORMANTS; ++i) {
        if (params_.formants[i].frequencyHz > 50.0) {
            sig = formantFilters_[i].process(sig);
        }
    }

    // Nasal branch modulation
    if (params_.velicAperture > 0.01) {
        Sample nasalSig = nasalZeroFilter_.process(excitation);
        nasalSig = nasalPoleFilter_.process(nasalSig);
        sig = static_cast<Sample>((1.0 - 0.5 * params_.velicAperture) * sig +
                                  params_.velicAperture * nasalSig * 0.8f);
    }

    // Viscoelastic tissue damping
    sig = fleshinessFilter_.process(sig);

    return sig;
}

void ResonantChambers::process(SampleSpan buffer) noexcept {
    for (auto& s : buffer) {
        s = process(s);
    }
}

} // namespace vocalis::orchestra
