#include "vocalis/extipa/cursive_compounder.hpp"
#include <algorithm>

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

    SampleReal currentTimeSec = 0.0;

    for (size_t i = 0; i < tokens.size(); ++i) {
        const auto& tok = tokens[i];
        const auto& tgt = tok.target;

        SampleReal durSec = std::max(0.02, tok.durationMs * 0.001);
        SampleReal targetF0 = baseF0 * tok.pitchScale;

        // Normal lung pressure for voiced, slightly lower for voiceless, zero for glottal stop / silence
        SampleReal lungPres = 800.0;
        if (tgt.type == ArticulationType::Silence) {
            lungPres = 0.0;
        } else if (tok.isGlottalStop) {
            lungPres = 0.0; // Complete vocal fold adduction
        } else if (tgt.voicingRatio < 0.2) {
            lungPres = 900.0; // Higher pressure for unvoiced fricatives
        }

        ArticulatoryTrajectoryPoint pt;
        pt.timeSec = currentTimeSec;
        pt.f0 = targetF0;
        pt.f1 = tgt.f1;
        pt.f2 = tgt.f2;
        pt.f3 = tgt.f3;
        pt.f4 = tgt.f4;
        pt.f5 = tgt.f5;
        pt.lungPressurePa = lungPres;
        pt.constrictionAperture = tgt.constrictionAperture;
        pt.noiseCenterFreq = tgt.noiseCenterFreq;
        pt.noiseBandwidth = tgt.noiseBandwidth;
        pt.velicAperture = tgt.velicAperture;
        pt.voicingRatio = tgt.voicingRatio;
        pt.lipRoundingCm = tgt.lipRoundingCm;
        pt.isGlottalStop = tok.isGlottalStop;
        pt.purrActive = tgt.purrActive;
        pt.growlActive = tgt.growlActive;
        pt.snarlActive = tgt.snarlActive;
        pt.clickFrequencyHz = tgt.clickFrequencyHz;

        trajectory.push_back(pt);

        // Advance timeline
        currentTimeSec += durSec;
    }

    // Add trailing point for envelope closure
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
