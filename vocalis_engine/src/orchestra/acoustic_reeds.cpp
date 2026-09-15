#include "vocalis/orchestra/acoustic_reeds.hpp"
#include <cmath>
#include <algorithm>

namespace vocalis::orchestra {

AcousticReeds::AcousticReeds(uint32_t sampleRate) noexcept
    : sampleRate_(sampleRate > 0 ? sampleRate : DEFAULT_SAMPLE_RATE) {
    reset();
}

void AcousticReeds::reset() noexcept {
    phase_ = 0.0;
    ventricularPhase_ = 0.0;
    syrinxLeftPhase_ = 0.0;
    syrinxRightPhase_ = 0.0;
    oqDrift_.reset(0.0);
    sqDrift_.reset(0.0);
    oqOffset_ = 0.0;
    sqOffset_ = 0.0;
    currentJitterOffset_ = 0.0;
    currentShimmerFactor_ = 1.0;
    tiltState_ = 0.0;
    periodSampleCount_ = 0;
}

SampleReal AcousticReeds::evaluateLF(SampleReal phaseNormalized, SampleReal /*f0*/) noexcept {
    // True Fant (1985) Liljencrants-Fant glottal flow derivative model
    // phaseNormalized in [0.0, 1.0)
    SampleReal Oq = std::clamp(params_.openQuotient + oqOffset_, 0.40, 0.75);
    SampleReal Sq = std::clamp(params_.speedQuotient + sqOffset_, 1.5, 3.0);

    SampleReal Te = Oq;
    SampleReal Tp = Te * (Sq / (Sq + 1.0)); // Peak glottal flow instant
    SampleReal Ta = std::clamp(params_.returnPhaseTa, 0.015, 0.08); // Return phase time constant ratio

    if (phaseNormalized < Te) {
        // Phase 1: Open glottal acceleration and deceleration up to GCI (Glottal Closure Instant)
        // u'(t) = E0 * exp(alpha * t) * sin(omega_g * t)
        SampleReal wg = PI / Tp;
        SampleReal alpha = 0.85 / Tp;

        SampleReal valTe = std::exp(alpha * Te) * std::sin(wg * Te);
        SampleReal E0 = (std::abs(valTe) > 1e-5) ? (-1.0 / valTe) : -1.0;

        return E0 * std::exp(alpha * phaseNormalized) * std::sin(wg * phaseNormalized);
    } else {
        // Phase 2: Post-closure relaxation return phase
        // Exponential decay from -1.0 back towards zero with time constant Ta
        SampleReal delta = phaseNormalized - Te;
        SampleReal decay = std::exp(-delta / Ta);
        SampleReal endOffset = std::exp(-(1.0 - Te) / Ta);
        return -(decay - endOffset);
    }
}

Sample AcousticReeds::step(SampleReal subglottalDrive) noexcept {
    if (subglottalDrive <= 0.0001) {
        return 0.0f;
    }

    SampleReal fs = static_cast<SampleReal>(sampleRate_);

    // Check avian syrinx polyphony mode
    if (params_.syrinxEnabled) {
        SampleReal dtLeft = params_.syrinxLeftF0Hz / fs;
        SampleReal dtRight = params_.syrinxRightF0Hz / fs;

        syrinxLeftPhase_ += dtLeft;
        if (syrinxLeftPhase_ >= 1.0) syrinxLeftPhase_ -= 1.0;

        syrinxRightPhase_ += dtRight;
        if (syrinxRightPhase_ >= 1.0) syrinxRightPhase_ -= 1.0;

        // Syrinx acoustic pressure is dual tone with cross-membrane ring modulation
        SampleReal leftSine = std::sin(TWO_PI * syrinxLeftPhase_);
        SampleReal rightSine = std::sin(TWO_PI * syrinxRightPhase_);
        SampleReal intermod = leftSine * rightSine * 0.25;

        SampleReal syrinxSig = (1.0 - params_.syrinxBalance) * leftSine +
                               params_.syrinxBalance * rightSine +
                               intermod;

        return static_cast<Sample>(syrinxSig * subglottalDrive);
    }

    // Standard true vocal folds
    SampleReal perturbedF0 = params_.f0Hz * (1.0 + currentJitterOffset_);
    perturbedF0 = std::clamp(perturbedF0, 20.0, fs * 0.45);
    SampleReal dt = perturbedF0 / fs;

    // Evaluate smooth LF flow derivative
    SampleReal pulse = evaluateLF(phase_, perturbedF0);

    // Ventricular false vocal fold engagement (subharmonic period doubling/tripling)
    if (params_.ventricularEngagement > 0.01) {
        SampleReal ventF0 = perturbedF0 / std::max(1.0, params_.subharmonicRatio);
        SampleReal ventDt = ventF0 / fs;

        ventricularPhase_ += ventDt;
        if (ventricularPhase_ >= 1.0) ventricularPhase_ -= 1.0;

        // Subharmonic pulse is a heavy, asymmetrical low-frequency waveform
        SampleReal ventPulse = std::sin(TWO_PI * ventricularPhase_) - 0.5 * std::cos(4.0 * PI * ventricularPhase_);
        pulse = (1.0 - 0.4 * params_.ventricularEngagement) * pulse +
                params_.ventricularEngagement * ventPulse * 0.8;
    }

    // Glottal fry / creak when F0 descends below 95 Hz (sentence-final cadence)
    if (perturbedF0 < 95.0) {
        SampleReal fryDepth = (95.0 - perturbedF0) / 30.0;
        if (periodSampleCount_ % 2 == 1) {
            dt *= (1.0 + 0.35 * std::min(1.0, fryDepth));
        }
    }

    // Synchronous glottal aspiration noise (natural vocal warmth)
    SampleReal Oq = std::clamp(params_.openQuotient, 0.35, 0.85);
    SampleReal aspirationMultiplier = (phase_ < Oq) ? std::sin(PI * (phase_ / Oq)) : 0.04;
    if (params_.aspirationGain > 0.0001) {
        SampleReal breathNoise = noiseGen_.nextGaussian() * (params_.aspirationGain * 0.10);
        pulse += breathNoise * aspirationMultiplier;
    }

    // Natural glottal source has natural -12 dB/octave spectral rolloff from LF flow model;
    // do not apply extra 2200 Hz choke filter which muffles F2, F3, and consonant clarity.

    // Apply shimmer amplitude perturbation and subglottal driving force
    SampleReal output = pulse * currentShimmerFactor_ * subglottalDrive;

    // Advance phase
    phase_ += dt;
    if (phase_ >= 1.0) {
        phase_ -= 1.0;
        // Update cycle-by-cycle stochastic Brownian pulse morphing
        oqOffset_ = oqDrift_.step(noiseGen_);
        sqOffset_ = sqDrift_.step(noiseGen_);

        // Update cycle-by-cycle jitter & shimmer micro-perturbations
        SampleReal jitterStdDev = (params_.jitterPercent * 0.01);
        currentJitterOffset_ = noiseGen_.nextGaussian() * jitterStdDev;

        SampleReal shimmerStdDev = (params_.shimmerPercent * 0.01);
        currentShimmerFactor_ = 1.0 + noiseGen_.nextGaussian() * shimmerStdDev;
        currentShimmerFactor_ = std::clamp(currentShimmerFactor_, 0.5, 1.5);
    }

    return static_cast<Sample>(output);
}

void AcousticReeds::process(SampleSpan output, SampleReal subglottalDrive) noexcept {
    for (auto& s : output) {
        s = step(subglottalDrive);
    }
}

} // namespace vocalis::orchestra
