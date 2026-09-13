#pragma once

#include "vocalis/types.hpp"
#include "vocalis/orchestra/air_bellows.hpp"
#include "vocalis/orchestra/acoustic_reeds.hpp"
#include "vocalis/orchestra/friction_nozzles.hpp"
#include "vocalis/orchestra/bioacoustics.hpp"
#include "vocalis/orchestra/resonant_chambers.hpp"
#include "vocalis/orchestra/radiation_bell.hpp"
#include <string>

namespace vocalis::voice {

struct SpeakerProfile {
    std::string name{"Default"};
    orchestra::AirBellowsParams bellows{};
    orchestra::GlottalParams reeds{};
    orchestra::ConstrictionParams nozzles{};
    orchestra::BioacousticParams bioacoustics{};
    orchestra::VocalTractParams tract{};
    orchestra::RadiationParams radiation{};

    static SpeakerProfile createHumanMale();
    static SpeakerProfile createHumanFemale();
    static SpeakerProfile createFelinePredator();
    static SpeakerProfile createCanineAlert();
    static SpeakerProfile createAvianSyrinx();
    static SpeakerProfile createAlienTonal();
};

} // namespace vocalis::voice
