#include "vocalis/orchestra/conductor.hpp"
#include <cmath>
#include <algorithm>

namespace vocalis::orchestra {

Conductor::Conductor(uint32_t sampleRate) noexcept
    : sampleRate_(sampleRate > 0 ? sampleRate : DEFAULT_SAMPLE_RATE),
      profile_(voice::SpeakerProfile::createHumanMale()),
      reeds_(sampleRate_),
      nozzles_(sampleRate_),
      bioacoustics_(sampleRate_),
      chambers_(sampleRate_),
      bell_(sampleRate_) {
    setSpeakerProfile(profile_);
}

void Conductor::setSampleRate(uint32_t sampleRate) noexcept {
    sampleRate_ = sampleRate > 0 ? sampleRate : DEFAULT_SAMPLE_RATE;
    reeds_.setSampleRate(sampleRate_);
    nozzles_.setSampleRate(sampleRate_);
    bioacoustics_.setSampleRate(sampleRate_);
    chambers_.setSampleRate(sampleRate_);
    bell_.setSampleRate(sampleRate_);
    setSpeakerProfile(profile_);
}

void Conductor::setSpeakerProfile(const voice::SpeakerProfile& profile) noexcept {
    profile_ = profile;
    bellows_.setParams(profile_.bellows);
    reeds_.setParams(profile_.reeds);
    nozzles_.setParams(profile_.nozzles);
    bioacoustics_.setParams(profile_.bioacoustics);
    chambers_.setParams(profile_.tract);
    bell_.setParams(profile_.radiation);
}

AudioBuffer Conductor::synthesizeExtIPA(std::string_view extIpaString) {
    auto tokens = parser_.parse(extIpaString);
    return synthesize(tokens);
}

AudioBuffer Conductor::synthesize(const std::vector<extipa::ExtIPAToken>& tokens) {
    auto trajectory = compounder_.compound(tokens, profile_.reeds.f0Hz);
    return synthesizeTrajectory(trajectory);
}

AudioBuffer Conductor::synthesizeTrajectory(const std::vector<extipa::ArticulatoryTrajectoryPoint>& trajectory) {
    if (trajectory.empty()) {
        return AudioBuffer(0, sampleRate_);
    }

    SampleReal totalDurationSec = trajectory.back().timeSec;
    size_t totalSamples = static_cast<size_t>(std::ceil(totalDurationSec * static_cast<SampleReal>(sampleRate_)));
    if (totalSamples == 0) totalSamples = sampleRate_ / 10;

    AudioBuffer output(totalSamples, sampleRate_);

    // Control rate sub-buffer size (1 ms = sampleRate / 1000)
    size_t controlBlockSize = std::max(size_t{1}, static_cast<size_t>(sampleRate_ / CONTROL_RATE_HZ));
    SampleReal dt = 1.0 / static_cast<SampleReal>(sampleRate_);

    size_t trajIdx = 0;
    size_t sampleIndex = 0;
    int lastPlosiveTrajIdx = -1;

    bellows_.reset();
    reeds_.reset();
    nozzles_.reset();
    bioacoustics_.reset();
    chambers_.reset();
    bell_.reset();

    if (!trajectory.empty()) {
        const auto& pInit = trajectory.front();
        ouF0_.reset(pInit.f0);
        ouF1_.reset(pInit.f1);
        ouF2_.reset(pInit.f2);
        ouF3_.reset(pInit.f3);
        ouF4_.reset(pInit.f4);
        ouF5_.reset(pInit.f5);
        ouPressure_.reset(pInit.lungPressurePa);
    }

    while (sampleIndex < totalSamples) {
        size_t blockEnd = std::min(totalSamples, sampleIndex + controlBlockSize);
        SampleReal blockCurrentTime = static_cast<SampleReal>(sampleIndex) * dt;

        // Advance trajectory keyframe index
        while (trajIdx + 1 < trajectory.size() && trajectory[trajIdx + 1].timeSec <= blockCurrentTime) {
            ++trajIdx;
        }

        const auto& p0 = trajectory[trajIdx];
        const auto& p1 = (trajIdx + 1 < trajectory.size()) ? trajectory[trajIdx + 1] : p0;

        SampleReal segDuration = std::max(0.001, p1.timeSec - p0.timeSec);
        SampleReal tNorm = std::clamp((blockCurrentTime - p0.timeSec) / segDuration, 0.0, 1.0);
        SampleReal w = smootherstep(tNorm);

        // Control-rate parameter interpolation (w is already Hermite C2 smootherstep)
        SampleReal targetF0 = lerp(p0.f0, p1.f0, w);
        SampleReal targetF1 = lerp(p0.f1, p1.f1, w);
        SampleReal targetF2 = lerp(p0.f2, p1.f2, w);
        SampleReal targetF3 = lerp(p0.f3, p1.f3, w);
        SampleReal targetF4 = lerp(p0.f4, p1.f4, w);
        SampleReal targetF5 = lerp(p0.f5, p1.f5, w);
        SampleReal targetPressure = lerp(p0.lungPressurePa, p1.lungPressurePa, w);

        SampleReal blockDt = static_cast<SampleReal>(blockEnd - sampleIndex) * dt;

        // Continuous stochastic Ornstein-Uhlenbeck (OU) SDE integration
        SampleReal currentF0 = ouF0_.step(targetF0, blockDt, stochasticRng_);
        SampleReal currentF1 = ouF1_.step(targetF1, blockDt, stochasticRng_);
        SampleReal currentF2 = ouF2_.step(targetF2, blockDt, stochasticRng_);
        SampleReal currentF3 = ouF3_.step(targetF3, blockDt, stochasticRng_);
        SampleReal currentF4 = ouF4_.step(targetF4, blockDt, stochasticRng_);
        SampleReal currentF5 = ouF5_.step(targetF5, blockDt, stochasticRng_);
        SampleReal currentPressure = ouPressure_.step(targetPressure, blockDt, stochasticRng_);

        SampleReal currentAperture = lerp(p0.constrictionAperture, p1.constrictionAperture, w);
        SampleReal currentVelic = lerp(p0.velicAperture, p1.velicAperture, w);
        SampleReal currentVoicing = lerp(p0.voicingRatio, p1.voicingRatio, w);
        SampleReal currentLipRound = lerp(p0.lipRoundingCm, p1.lipRoundingCm, w);

        // Update Instrument 1: Air Bellows
        bellows_.setLungPressure(currentPressure);

        // Update Instrument 2: Acoustic Reeds with subtle organic micro-vibrato (4.8 Hz, 1.0 Hz depth)
        SampleReal vibrato = 1.0 * std::sin(TWO_PI * 4.8 * blockCurrentTime);
        reeds_.setF0(currentF0 + vibrato);

        // Update Instrument 3: Friction Nozzles
        ConstrictionParams cParams = nozzles_.params();
        cParams.apertureMm2 = currentAperture;
        cParams.centerFreqHz = lerp(p0.noiseCenterFreq, p1.noiseCenterFreq, w);
        cParams.bandwidthHz = lerp(p0.noiseBandwidth, p1.noiseBandwidth, w);
        nozzles_.setParams(cParams);

        // Check plosive / click release trigger (triggers strictly ONCE per keyframe boundary)
        if (p0.clickFrequencyHz > 100.0 && static_cast<int>(trajIdx) != lastPlosiveTrajIdx) {
            nozzles_.triggerPlosiveBurst(0.8);
            lastPlosiveTrajIdx = static_cast<int>(trajIdx);
        }

        // Update Instrument 4: Bioacoustic Modulator
        BioacousticParams bioParams = bioacoustics_.params();
        bioParams.purrActive = p0.purrActive || p1.purrActive || profile_.bioacoustics.purrActive;
        bioParams.growlChaosActive = p0.growlActive || p1.growlActive || profile_.bioacoustics.growlChaosActive;
        bioParams.snarlActive = p0.snarlActive || p1.snarlActive || profile_.bioacoustics.snarlActive;
        bioParams.nominalF0Hz = currentF0;
        bioacoustics_.setParams(bioParams);

        // Update Instrument 5: Resonating Chambers (Klatt Cascade Series Resonators)
        chambers_.setFormant(0, currentF1, 70.0, 1.0);
        chambers_.setFormant(1, currentF2, 110.0, 1.0);
        chambers_.setFormant(2, currentF3, 160.0, 1.0);
        chambers_.setFormant(3, currentF4, 240.0, 1.0);
        chambers_.setFormant(4, currentF5, 320.0, 1.0);
        chambers_.setVelicAperture(currentVelic);

        // Update Instrument 6: Radiation Bell
        bell_.setLipRounding(currentLipRound);

        // Audio-rate processing block
        for (size_t s = sampleIndex; s < blockEnd; ++s) {
            // 1. Subglottal airflow driving force
            SampleReal drive = bellows_.step(dt);

            // 2. Bioacoustic neural purr / snarl amplitude gating
            SampleReal bioGating = bioacoustics_.computeGatingMultiplier(dt);
            SampleReal effectiveDrive = drive * bioGating;

            // 3. Acoustic Reeds (LF glottal flow + PolyBLEP anti-aliasing)
            Sample glottalSig = reeds_.step(effectiveDrive);

            // 4. Friction Nozzles (turbulence + plosive bursts)
            Sample turbSig = nozzles_.step(effectiveDrive);

            // 5. Source excitation for pharyngeal vocal tract
            Sample excitation = static_cast<Sample>(
                glottalSig * currentVoicing +
                turbSig * 0.15f * static_cast<Sample>(1.0 - currentVoicing)
            );

            // 6. Bioacoustic non-linear delay chaos (predator growl)
            Sample chaotic = bioacoustics_.processChaos(excitation);

            // 7. Resonant Chambers (vocal tract formant filter bank for voiced speech)
            Sample resonated = chambers_.process(chaotic);

            // 8. Radiation & Coupling Bell (spherical high-pass radiation for glottal voice)
            Sample radiated = bell_.process(resonated);

            // 9. Anterior turbulence bypass: fricatives & bursts radiate directly into open air
            // Bypasses the boundary differentiator to prevent 6x noise spike amplification
            Sample anteriorTurb = static_cast<Sample>(turbSig * (1.0 - currentVoicing * 0.7) * 0.15f);

            output[s] = radiated + anteriorTurb;
        }

        sampleIndex = blockEnd;
    }

    // Master speech level calibration & peak normalization (-1.5 dB peak)
    Sample peak = 0.0f;
    for (size_t i = 0; i < totalSamples; ++i) {
        Sample absVal = std::abs(output[i]);
        if (absVal > peak) peak = absVal;
    }
    if (peak > 1e-4f) {
        Sample targetPeak = 0.82f;
        Sample normGain = targetPeak / peak;
        if (normGain > 200.0f) normGain = 200.0f;
        for (size_t i = 0; i < totalSamples; ++i) {
            output[i] *= normGain;
        }
    }

    return output;
}

} // namespace vocalis::orchestra
