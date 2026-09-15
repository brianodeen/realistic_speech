#include "vocalis/voice/speaker_profile.hpp"

namespace vocalis::voice {

SpeakerProfile SpeakerProfile::createHumanMale() {
    SpeakerProfile p;
    p.name = "HumanMale";
    p.bellows.lungPressurePa = 720.0; // Comfortable conversational subglottal pressure (unstrained)
    p.reeds.f0Hz = 135.0;
    p.reeds.openQuotient = 0.66;
    p.reeds.speedQuotient = 1.8;
    p.reeds.returnPhaseTa = 0.055;
    p.reeds.jitterPercent = 0.35;
    p.reeds.shimmerPercent = 0.7;
    p.reeds.aspirationGain = 0.035;
    p.tract.vocalTractLengthScale = 1.0;
    p.tract.fleshinessDamping = 0.30;
    return p;
}

SpeakerProfile SpeakerProfile::createHumanFemale() {
    SpeakerProfile p;
    p.name = "HumanFemale";
    p.bellows.lungPressurePa = 800.0;
    p.reeds.f0Hz = 220.0;
    p.reeds.openQuotient = 0.65;
    p.reeds.speedQuotient = 2.0;
    p.reeds.jitterPercent = 0.35;
    p.reeds.shimmerPercent = 0.7;
    p.tract.vocalTractLengthScale = 0.88; // Shorter female vocal tract
    p.tract.fleshinessDamping = 0.3;
    return p;
}

SpeakerProfile SpeakerProfile::createFelinePredator() {
    SpeakerProfile p;
    p.name = "FelinePredator";
    p.bellows.lungPressurePa = 1200.0;
    p.reeds.f0Hz = 85.0;
    p.reeds.ventricularEngagement = 0.75; // Deep false-cord vibration
    p.reeds.subharmonicRatio = 2.0;       // Period doubling
    p.bioacoustics.purrActive = false;
    p.bioacoustics.purrTwitchRateHz = 24.5;
    p.bioacoustics.growlChaosActive = true;
    p.bioacoustics.growlAlpha = 1.4;
    p.bioacoustics.growlBeta = 0.7;
    p.bioacoustics.nominalF0Hz = 85.0;
    p.tract.vocalTractLengthScale = 1.35;  // Extended predatory pharyngeal tube
    p.tract.fleshinessDamping = 0.55;
    return p;
}

SpeakerProfile SpeakerProfile::createCanineAlert() {
    SpeakerProfile p;
    p.name = "CanineAlert";
    p.bellows.lungPressurePa = 1400.0;
    p.reeds.f0Hz = 260.0;
    p.bioacoustics.snarlActive = true;
    p.bioacoustics.snarlFlutterHz = 48.0;
    p.bioacoustics.snarlFlutterDepth = 0.65;
    p.bioacoustics.lipCurlExposure = 0.7;
    p.tract.vocalTractLengthScale = 0.95;
    p.tract.fleshinessDamping = 0.4;
    return p;
}

SpeakerProfile SpeakerProfile::createAvianSyrinx() {
    SpeakerProfile p;
    p.name = "AvianSyrinx";
    p.bellows.lungPressurePa = 1100.0;
    p.reeds.syrinxEnabled = true;
    p.reeds.syrinxLeftF0Hz = 1950.0;
    p.reeds.syrinxRightF0Hz = 2600.0;
    p.reeds.syrinxBalance = 0.5;
    p.tract.vocalTractLengthScale = 0.45; // Tiny avian resonance tract
    p.tract.fleshinessDamping = 0.15;
    return p;
}

SpeakerProfile SpeakerProfile::createAlienTonal() {
    SpeakerProfile p;
    p.name = "AlienTonal";
    p.bellows.lungPressurePa = 950.0;
    p.reeds.f0Hz = 160.0;
    p.reeds.ventricularEngagement = 0.3;
    p.reeds.subharmonicRatio = 3.0;
    p.tract.vocalTractLengthScale = 1.15;
    p.tract.fleshinessDamping = 0.45;
    p.radiation.lipRoundingCm = 1.2;
    return p;
}

} // namespace vocalis::voice
