#pragma once

#include "vocalis/types.hpp"
#include <string>
#include <string_view>
#include <array>
#include <unordered_map>

namespace vocalis::extipa {

enum class ArticulationType : uint8_t {
    Vowel,
    StopPlosive,
    Fricative,
    Nasal,
    Affricate,
    Approximant,
    Click,
    Ejective,
    Implosive,
    CreaturePurr,
    CreatureGrowl,
    CreatureSnarl,
    CreatureHiss,
    GlottalStop,
    Silence
};

struct PhonemeTarget {
    std::string symbol;
    ArticulationType type{ArticulationType::Vowel};
    SampleReal f1{500.0};
    SampleReal f2{1500.0};
    SampleReal f3{2500.0};
    SampleReal f4{3500.0};
    SampleReal f5{4500.0};

    SampleReal voicingRatio{1.0};       // 1.0 = voiced, 0.0 = unvoiced
    SampleReal velicAperture{0.0};      // 1.0 = full nasal
    SampleReal constrictionAperture{50.0}; // mm2 (narrow < 15 for fricatives)
    SampleReal noiseCenterFreq{5000.0};
    SampleReal noiseBandwidth{2000.0};
    SampleReal baseDurationMs{120.0};
    SampleReal lipRoundingCm{0.0};

    // Creature features
    bool ingressive{false};
    bool purrActive{false};
    bool growlActive{false};
    bool snarlActive{false};
    SampleReal clickFrequencyHz{0.0};
};

class PhonemeDatabase {
public:
    static const PhonemeDatabase& instance();

    [[nodiscard]] const PhonemeTarget* find(std::string_view symbol) const noexcept;
    [[nodiscard]] const PhonemeTarget& getOrDefault(std::string_view symbol) const noexcept;

private:
    PhonemeDatabase();
    void registerTarget(PhonemeTarget target);

    std::unordered_map<std::string, PhonemeTarget> map_;
    PhonemeTarget defaultVowel_{};
    PhonemeTarget silence_{};
};

} // namespace vocalis::extipa
