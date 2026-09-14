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

    // First pass: Calculate token durations with stress timing & pre-pausal lengthening
    std::vector<SampleReal> durations(tokens.size(), 0.0);
    SampleReal totalUtteranceSec = 0.0;

    for (size_t i = 0; i < tokens.size(); ++i) {
        const auto& tok = tokens[i];
        const auto& tgt = tok.target;
        SampleReal baseDur = std::max(0.035, tok.durationMs * 0.001);

        // Check if final token in the utterance (pre-pausal lengthening)
        bool isFinal = (i + 1 == tokens.size() || 
                       (i + 2 == tokens.size() && tokens.back().target.type == ArticulationType::Silence));

        // Stress timing rhythm hierarchy:
        // Long vowels, diphthongs, and tokens with pitchScale > 1.05 are stressed lexical targets
        bool isLong = (tok.symbol.find("ː") != std::string::npos ||
                       tok.symbol == "oʊ" || tok.symbol == "aɪ" || tok.symbol == "eɪ" ||
                       tok.symbol == "aʊ" || tok.symbol == "ɔɪ");
        bool isStressed = isLong || (tok.pitchScale > 1.05);
        bool isWeak = (!isStressed && (tgt.type == ArticulationType::Approximant || tgt.baseDurationMs < 95.0));

        SampleReal timingFactor = 1.0;
        if (isFinal) {
            timingFactor *= 1.35; // Universal pre-pausal lengthening
        } else if (isStressed) {
            timingFactor *= 1.25; // Stressed syllables are elongated
        } else if (isWeak) {
            timingFactor *= 0.72; // Reduced unstressed syllables
        }

        durations[i] = baseDur * timingFactor;
        totalUtteranceSec += durations[i];
    }
    if (totalUtteranceSec < 0.1) totalUtteranceSec = 0.1;

    SampleReal currentTimeSec = 0.0;

    for (size_t i = 0; i < tokens.size(); ++i) {
        const auto& tok = tokens[i];
        const auto& tgt = tok.target;

        SampleReal durSec = durations[i];
        SampleReal transSec = std::min(0.025, durSec * 0.25);

        bool isFinal = (i + 1 == tokens.size() || 
                       (i + 2 == tokens.size() && tokens.back().target.type == ArticulationType::Silence));

        // Compute natural sentence-level intonation contour:
        // Baseline declination slope from 1.0 down to 0.75 across the utterance
        SampleReal normTime = std::clamp((currentTimeSec + durSec * 0.5) / totalUtteranceSec, 0.0, 1.0);
        SampleReal declination = 1.0 - 0.25 * normTime;

        // Word / syllable stress pitch accents:
        bool hasPitchAccent = (tok.pitchScale > 1.05);
        SampleReal accent = hasPitchAccent ? (0.30 * (tok.pitchScale - 1.0) / 0.25) : 0.0;

        SampleReal targetF0 = baseF0 * (declination + accent);

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
        bool isVoicedVowel = (tgt.type == ArticulationType::Vowel && tgt.voicingRatio > 0.5);

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

        } else if (isVoicedVowel) {
            // Natural sentence intonation gesture
            SampleReal f0Onset, f0Peak, f0Offset;
            if (hasPitchAccent) {
                // Nuclear pitch accent crest & descent (e.g. "saw")
                f0Onset  = targetF0 * 1.08;
                f0Peak   = targetF0 * 1.04;
                f0Offset = targetF0 * 0.88; // Glides smoothly down into post-accent syllable
            } else if (isFinal) {
                // Sentence-final declarative cadence (e.g. "go")
                f0Onset  = targetF0 * 0.95;
                f0Peak   = targetF0 * 0.88;
                f0Offset = targetF0 * 0.72; // Drops down to low declarative floor
            } else if (currentTimeSec < totalUtteranceSec * 0.25) {
                // Unstressed sentence-initial syllable (e.g. "We")
                f0Onset  = targetF0 * 0.96;
                f0Peak   = targetF0 * 1.06;
                f0Offset = targetF0 * 0.98;
            } else {
                // Unstressed medial bridge (e.g. "you")
                f0Onset  = targetF0 * 0.92;
                f0Peak   = targetF0 * 0.90;
                f0Offset = targetF0 * 0.88;
            }

            // Dynamic diphthong formant transitions
            SampleReal f1Onset = tgt.f1;
            SampleReal f2Onset = tgt.f2;
            SampleReal f3Onset = tgt.f3;
            SampleReal lipOnset = tgt.lipRoundingCm;

            SampleReal f1Offset = tgt.f1;
            SampleReal f2Offset = tgt.f2;
            SampleReal f3Offset = tgt.f3;
            SampleReal lipOffset = tgt.lipRoundingCm;

            if (tok.symbol == "oʊ") {
                // [o] -> [ʊ] diphthong glide (e.g. "go")
                f1Onset = 480.0; f2Onset = 980.0;  f3Onset = 2300.0; lipOnset = 0.8;
                f1Offset = 400.0; f2Offset = 850.0; f3Offset = 2200.0; lipOffset = 1.6;
            } else if (tok.symbol == "aɪ") {
                // [a] -> [ɪ]
                f1Onset = 750.0; f2Onset = 1250.0; f3Onset = 2500.0;
                f1Offset = 360.0; f2Offset = 2100.0; f3Offset = 2800.0;
            } else if (tok.symbol == "eɪ") {
                // [e] -> [ɪ]
                f1Onset = 480.0; f2Onset = 1850.0; f3Onset = 2600.0;
                f1Offset = 360.0; f2Offset = 2200.0; f3Offset = 2800.0;
            } else if (tok.symbol == "aʊ") {
                // [a] -> [ʊ]
                f1Onset = 750.0; f2Onset = 1250.0; f3Onset = 2500.0; lipOnset = 0.0;
                f1Offset = 440.0; f2Offset = 880.0;  f3Offset = 2200.0; lipOffset = 1.5;
            } else if (tok.symbol == "ɔɪ") {
                // [ɔ] -> [ɪ]
                f1Onset = 550.0; f2Onset = 950.0;  f3Onset = 2400.0; lipOnset = 0.8;
                f1Offset = 360.0; f2Offset = 2000.0; f3Offset = 2700.0; lipOffset = 0.0;
            }

            // Point 1: Onset
            ArticulatoryTrajectoryPoint pt1;
            pt1.timeSec = currentTimeSec + transSec;
            pt1.f0 = f0Onset;
            pt1.f1 = f1Onset;
            pt1.f2 = f2Onset;
            pt1.f3 = f3Onset;
            pt1.f4 = tgt.f4;
            pt1.f5 = tgt.f5;
            pt1.lungPressurePa = lungPres;
            pt1.constrictionAperture = tgt.constrictionAperture;
            pt1.noiseCenterFreq = tgt.noiseCenterFreq;
            pt1.noiseBandwidth = tgt.noiseBandwidth;
            pt1.velicAperture = tgt.velicAperture;
            pt1.voicingRatio = tgt.voicingRatio;
            pt1.lipRoundingCm = lipOnset;
            pt1.isGlottalStop = tok.isGlottalStop;
            pt1.purrActive = tgt.purrActive;
            pt1.growlActive = tgt.growlActive;
            pt1.snarlActive = tgt.snarlActive;
            pt1.clickFrequencyHz = tgt.clickFrequencyHz;

            // Point 2: Nucleus Crest (~38% of vowel duration)
            ArticulatoryTrajectoryPoint pt2 = pt1;
            pt2.timeSec = currentTimeSec + durSec * 0.38;
            pt2.f0 = f0Peak;
            pt2.f1 = f1Onset * 0.6 + f1Offset * 0.4;
            pt2.f2 = f2Onset * 0.6 + f2Offset * 0.4;
            pt2.f3 = f3Onset * 0.6 + f3Offset * 0.4;
            pt2.lipRoundingCm = lipOnset * 0.6 + lipOffset * 0.4;

            // Point 3: Offset Glide (~85% of vowel duration)
            ArticulatoryTrajectoryPoint pt3 = pt1;
            pt3.timeSec = currentTimeSec + durSec - transSec;
            pt3.f0 = f0Offset;
            pt3.f1 = f1Offset;
            pt3.f2 = f2Offset;
            pt3.f3 = f3Offset;
            pt3.lipRoundingCm = lipOffset;

            // If initial phone, add t=0 anchor
            if (trajectory.empty() && pt1.timeSec > 0.0) {
                ArticulatoryTrajectoryPoint ptInitial = pt1;
                ptInitial.timeSec = 0.0;
                trajectory.push_back(ptInitial);
            }

            trajectory.push_back(pt1);
            trajectory.push_back(pt2);
            trajectory.push_back(pt3);

        } else {
            // Consonants, Approximants, and Fricatives:
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
