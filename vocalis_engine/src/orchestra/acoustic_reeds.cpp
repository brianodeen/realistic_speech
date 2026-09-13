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
    currentJitterOffset_ = 0.0;
    currentShimmerFactor_ = 1.0;
    periodSampleCount_ = 0;
}

SampleReal AcousticReeds::evaluateLF(SampleReal phaseNormalized, SampleReal /*f0*/) noexcept {
    // Liljencrants-Fant (LF) parametric glottal flow derivative model
    // phaseNormalized in [0.0, 1.0)
    // Tp is peak flow instant, Te is excitation epoch instant (closing finish)
    SampleReal Oq = std::clamp(params_.openQuotient, 0.25, 0.9);
    SampleReal Sq = std::clamp(params_.speedQuotient, 1.1, 4.0);

    // Te occurs around Oq
    SampleReal Te = Oq;

    if (phaseNormalized < Te) {
        // Open phase (0 to Te): growing sinusoidal pulse with exponential growth
        SampleReal t = phaseNormalized / Te;
        SampleReal alpha = 1.5;
        SampleReal omega = PI * (1.0 + 0.1 * (Sq - 2.0));
        SampleReal flowDeriv = std::exp(alpha * t) * std::sin(omega * t);
        return flowDeriv;
    } else {
        // Return phase (Te to 1.0): exponential recovery to zero baseline
        SampleReal Ta = std::max(0.01, (1.0 - Te) * 0.25);
        SampleReal t = (phaseNormalized - Te);
        SampleReal epsilon = 1.0 / Ta;
        SampleReal Ee = 1.0; // Peak negative discontinuity magnitude
        SampleReal returnPhase = -Ee * std::exp(-epsilon * t);
        return returnPhase;
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

    // Evaluate LF flow derivative
    SampleReal pulse = evaluateLF(phase_, perturbedF0);

    // Apply PolyBLEP anti-aliasing around phase discontinuity (glottal epoch / wrap)
    pulse += dsp::polyBlep(phase_, dt);

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

    // Glottal aspiration noise (turbulent leakage across vocal folds)
    if (params_.aspirationGain > 0.001) {
        pulse += noiseGen_.nextGaussian() * params_.aspirationGain;
    }

    // Apply shimmer amplitude perturbation and subglottal driving force
    SampleReal output = pulse * currentShimmerFactor_ * subglottalDrive;

    // Advance phase
    phase_ += dt;
    if (phase_ >= 1.0) {
        phase_ -= 1.0;
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
