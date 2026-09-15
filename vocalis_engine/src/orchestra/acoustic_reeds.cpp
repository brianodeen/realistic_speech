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
    // Continuous, bandlimited Liljencrants-Fant glottal flow derivative model
    // phaseNormalized in [0.0, 1.0)
    SampleReal Oq = std::clamp(params_.openQuotient + oqOffset_, 0.35, 0.85);
    SampleReal Sq = std::clamp(params_.speedQuotient + sqOffset_, 1.2, 3.5);

    SampleReal Te = Oq;
    SampleReal Tp = Te * (Sq / (Sq + 1.0)); // Peak flow velocity instant

    if (phaseNormalized < Tp) {
        // Phase 1: Opening acceleration (0 <= t < Tp)
        // Smooth raised-cosine rise: zero derivative at t=0 and t=Tp
        SampleReal u = phaseNormalized / Tp;
        return 0.5 * (1.0 - std::cos(PI * u));
    } else if (phaseNormalized < Te) {
        // Phase 2: Closing deceleration (Tp <= t < Te)
        // Transitions continuously from +1.0 down to -Ee at Te
        SampleReal u = (phaseNormalized - Tp) / (Te - Tp);
        SampleReal Ee = 1.0;
        return std::cos(HALF_PI * u) - Ee * std::sin(HALF_PI * u);
    } else {
        // Phase 3: Return relaxation phase (Te <= t < 1.0)
        // Recovers smoothly from -Ee back to exactly 0.0 at t=1.0 with zero discontinuity
        SampleReal v = (phaseNormalized - Te) / (1.0 - Te);
        SampleReal Ee = 1.0;
        return -Ee * std::cos(HALF_PI * v) * std::exp(-3.5 * v);
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

    // Synchronous glottal aspiration noise (turbulent breathiness during open phase)
    SampleReal Oq = std::clamp(params_.openQuotient, 0.35, 0.85);
    SampleReal aspirationMultiplier = (phase_ < Oq) ? std::sin(PI * (phase_ / Oq)) : 0.0;
    if (params_.aspirationGain > 0.0001) {
        SampleReal breathNoise = noiseGen_.nextGaussian() * (params_.aspirationGain * 0.08);
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
