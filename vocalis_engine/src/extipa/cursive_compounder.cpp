#include "vocalis/extipa/cursive_compounder.hpp"
#include <algorithm>
#include <cmath>

namespace vocalis::extipa {

std::vector<ArticulatoryTrajectoryPoint> CursiveCompounder::compound(
    const std::vector<ExtIPAToken>& tokens,
    SampleReal baseF0,
    SampleReal transitionDurationMs
) const {
    std::vector<ArticulatoryTrajectoryPoint> trajectory;
    if (tokens.empty()) {
        return trajectory;
    }

    // First pass: Calculate total duration of the utterance
    SampleReal totalUtteranceSec = 0.0;
    for (const auto& tok : tokens) {
        totalUtteranceSec += std::max(0.04, tok.durationMs * 0.001);
    }
    if (totalUtteranceSec < 0.1) totalUtteranceSec = 0.1;

    SampleReal currentTimeSec = 0.0;

    for (size_t i = 0; i < tokens.size(); ++i) {
        const auto& tok = tokens[i];
        const auto& tgt = tok.target;

        SampleReal durSec = std::max(0.04, tok.durationMs * 0.001);
        SampleReal transSec = std::min(0.030, durSec * 0.28);

        // Compute natural sentence-level intonation contour:
        // 1. Natural declarative declination: starts at +6% and gently falls to -15%
        SampleReal normTime = std::clamp((currentTimeSec + durSec * 0.5) / totalUtteranceSec, 0.0, 1.0);
        SampleReal declination = 1.06 - 0.22 * normTime;

        // 2. Word / syllable stress pitch accents:
        // Peak intonation on middle syllables (e.g. "saw" around 30-50% progress)
        SampleReal accent = 0.08 * std::sin(PI * normTime);

        // 3. User / token pitch multiplier (or Chao tone)
        SampleReal tokenPitchMultiplier = tok.pitchScale;

        SampleReal targetF0 = baseF0 * (declination + accent) * tokenPitchMultiplier;

        // Determine aerodynamic subglottal lung pressure
        SampleReal lungPres = 850.0;
        if (tgt.type == ArticulationType::Silence) {
            lungPres = 0.0;
        } else if (tok.isGlottalStop) {
            lungPres = 0.0;
        } else if (tgt.voicingRatio < 0.2) {
            lungPres = 950.0; // Higher aerodynamic head for turbulent fricatives
        }

        bool isStop = (tgt.type == ArticulationType::StopPlosive);

        if (isStop) {
            // Stop plosive:
            // Phase A: Silent or low-voiced occlusion closure (first 65% of duration)
            ArticulatoryTrajectoryPoint ptClosure;
            ptClosure.timeSec = currentTimeSec;
            ptClosure.f0 = targetF0;
            ptClosure.f1 = tgt.f1;
            ptClosure.f2 = tgt.f2;
            ptClosure.f3 = tgt.f3;
            ptClosure.f4 = tgt.f4;
            ptClosure.f5 = tgt.f5;
            ptClosure.lungPressurePa = (tgt.voicingRatio > 0.3) ? 400.0 : 0.0;
            ptClosure.constrictionAperture = 0.0; // Closed occlusion
            ptClosure.noiseCenterFreq = tgt.noiseCenterFreq;
            ptClosure.noiseBandwidth = tgt.noiseBandwidth;
            ptClosure.velicAperture = 0.0;
            ptClosure.voicingRatio = (tgt.voicingRatio > 0.3) ? 0.3 : 0.0;
            ptClosure.lipRoundingCm = tgt.lipRoundingCm;
            ptClosure.clickFrequencyHz = 0.0;
            trajectory.push_back(ptClosure);

            // Phase B: Transient release burst at 65% mark
            SampleReal releaseTime = currentTimeSec + durSec * 0.65;
            ArticulatoryTrajectoryPoint ptBurst = ptClosure;
            ptBurst.timeSec = releaseTime;
            ptBurst.lungPressurePa = 900.0;
            ptBurst.constrictionAperture = 25.0; // Rapid opening release
            ptBurst.clickFrequencyHz = tgt.noiseCenterFreq; // Triggers plosive transient pop
            trajectory.push_back(ptBurst);

            // Phase C: Transition to following vowel
            ArticulatoryTrajectoryPoint ptEnd = ptBurst;
            ptEnd.timeSec = currentTimeSec + durSec;
            ptEnd.clickFrequencyHz = 0.0;
            trajectory.push_back(ptEnd);

        } else {
            // Vowels, Approximants, and Fricatives:
            // Point 1: Reaches steady-state target posture at start of hold
            ArticulatoryTrajectoryPoint ptHoldStart;
            ptHoldStart.timeSec = currentTimeSec + transSec;
            ptHoldStart.f0 = targetF0;
            ptHoldStart.f1 = tgt.f1;
            ptHoldStart.f2 = tgt.f2;
            ptHoldStart.f3 = tgt.f3;
            ptHoldStart.f4 = tgt.f4;
            ptHoldStart.f5 = tgt.f5;
            ptHoldStart.lungPressurePa = lungPres;
            ptHoldStart.constrictionAperture = tgt.constrictionAperture;
            ptHoldStart.noiseCenterFreq = tgt.noiseCenterFreq;
            ptHoldStart.noiseBandwidth = tgt.noiseBandwidth;
            ptHoldStart.velicAperture = tgt.velicAperture;
            ptHoldStart.voicingRatio = tgt.voicingRatio;
            ptHoldStart.lipRoundingCm = tgt.lipRoundingCm;
            ptHoldStart.isGlottalStop = tok.isGlottalStop;
            ptHoldStart.purrActive = tgt.purrActive;
            ptHoldStart.growlActive = tgt.growlActive;
            ptHoldStart.snarlActive = tgt.snarlActive;
            ptHoldStart.clickFrequencyHz = tgt.clickFrequencyHz;

            // Point 2: Holds steady-state target posture until end of hold
            ArticulatoryTrajectoryPoint ptHoldEnd = ptHoldStart;
            ptHoldEnd.timeSec = currentTimeSec + durSec - transSec;

            // If this is the very first phone, add initial point at t=0
            if (trajectory.empty() && ptHoldStart.timeSec > 0.0) {
                ArticulatoryTrajectoryPoint ptInitial = ptHoldStart;
                ptInitial.timeSec = 0.0;
                trajectory.push_back(ptInitial);
            }

            trajectory.push_back(ptHoldStart);
            trajectory.push_back(ptHoldEnd);
        }

        currentTimeSec += durSec;
    }

    // Trailing closure point
    if (!trajectory.empty()) {
        ArticulatoryTrajectoryPoint endPt = trajectory.back();
        endPt.timeSec = currentTimeSec + (transitionDurationMs * 0.001);
        endPt.lungPressurePa = 0.0;
        endPt.voicingRatio = 0.0;
        trajectory.push_back(endPt);
    }

    return trajectory;
}

} // namespace vocalis::extipa
