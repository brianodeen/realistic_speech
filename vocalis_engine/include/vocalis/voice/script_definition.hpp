#pragma once

#include "vocalis/types.hpp"
#include <string>
#include <vector>

namespace vocalis::voice {

struct ScriptUtterance {
    std::string text;
    std::string extIpa;
    std::string speaker{"HumanMale"};
    SampleReal speedRate{1.0};
    SampleReal pitchMultiplier{1.0};
};

struct ConlangScript {
    std::string languageName{"UniversalPhonetic"};
    std::string version{"2.0"};
    std::vector<ScriptUtterance> utterances;
};

} // namespace vocalis::voice
