#include "vocalis/extipa/phoneme_map.hpp"

namespace vocalis::extipa {

const PhonemeDatabase& PhonemeDatabase::instance() {
    static const PhonemeDatabase db;
    return db;
}

PhonemeDatabase::PhonemeDatabase() {
    // Default neutral vowel [ə]
    defaultVowel_.symbol = "ə";
    defaultVowel_.type = ArticulationType::Vowel;
    defaultVowel_.f1 = 500.0;
    defaultVowel_.f2 = 1500.0;
    defaultVowel_.f3 = 2500.0;
    defaultVowel_.f4 = 3500.0;
    defaultVowel_.f5 = 4500.0;
    defaultVowel_.voicingRatio = 1.0;
    defaultVowel_.constrictionAperture = 50.0;
    defaultVowel_.baseDurationMs = 120.0;

    // Silence
    silence_.symbol = "_";
    silence_.type = ArticulationType::Silence;
    silence_.voicingRatio = 0.0;
    silence_.constrictionAperture = 0.0;
    silence_.baseDurationMs = 100.0;

    registerTarget(defaultVowel_);
    registerTarget(silence_);

    // --- Human Vowels ---
    registerTarget({"a", ArticulationType::Vowel, 800.0, 1200.0, 2600.0, 3500.0, 4500.0, 1.0, 0.0, 60.0, 5000.0, 2000.0, 140.0, 0.0});
    registerTarget({"i", ArticulationType::Vowel, 280.0, 2300.0, 3000.0, 3600.0, 4600.0, 1.0, 0.0, 50.0, 5000.0, 2000.0, 130.0, 0.0});
    registerTarget({"u", ArticulationType::Vowel, 320.0, 800.0, 2200.0, 3400.0, 4400.0, 1.0, 0.0, 40.0, 5000.0, 2000.0, 140.0, 1.5});
    registerTarget({"e", ArticulationType::Vowel, 450.0, 1900.0, 2550.0, 3550.0, 4550.0, 1.0, 0.0, 55.0, 5000.0, 2000.0, 130.0, 0.0});
    registerTarget({"o", ArticulationType::Vowel, 500.0, 950.0, 2400.0, 3400.0, 4400.0, 1.0, 0.0, 45.0, 5000.0, 2000.0, 140.0, 1.2});
    registerTarget({"ɛ", ArticulationType::Vowel, 580.0, 1750.0, 2600.0, 3600.0, 4600.0, 1.0, 0.0, 55.0, 5000.0, 2000.0, 120.0, 0.0});
    registerTarget({"ɔ", ArticulationType::Vowel, 600.0, 1050.0, 2500.0, 3500.0, 4500.0, 1.0, 0.0, 50.0, 5000.0, 2000.0, 130.0, 0.8});
    registerTarget({"y", ArticulationType::Vowel, 300.0, 2100.0, 2800.0, 3500.0, 4500.0, 1.0, 0.0, 45.0, 5000.0, 2000.0, 130.0, 1.0});
    registerTarget({"ɯ", ArticulationType::Vowel, 320.0, 1350.0, 2350.0, 3450.0, 4450.0, 1.0, 0.0, 45.0, 5000.0, 2000.0, 130.0, 0.0});

    // Nasal Vowels
    registerTarget({"ã", ArticulationType::Vowel, 750.0, 1250.0, 2600.0, 3500.0, 4500.0, 1.0, 0.6, 55.0, 5000.0, 2000.0, 140.0, 0.0});
    registerTarget({"õ", ArticulationType::Vowel, 520.0, 1000.0, 2400.0, 3400.0, 4400.0, 1.0, 0.6, 45.0, 5000.0, 2000.0, 140.0, 1.0});

    // --- Nasal Consonants ---
    registerTarget({"m", ArticulationType::Nasal, 250.0, 1100.0, 2400.0, 3300.0, 4300.0, 1.0, 1.0, 0.0, 5000.0, 2000.0, 90.0, 0.0});
    registerTarget({"n", ArticulationType::Nasal, 280.0, 1600.0, 2700.0, 3500.0, 4500.0, 1.0, 1.0, 0.0, 5000.0, 2000.0, 85.0, 0.0});
    registerTarget({"ŋ", ArticulationType::Nasal, 300.0, 2000.0, 2800.0, 3600.0, 4600.0, 1.0, 1.0, 0.0, 5000.0, 2000.0, 95.0, 0.0});

    // --- Fricatives ---
    registerTarget({"s", ArticulationType::Fricative, 300.0, 1600.0, 2700.0, 3600.0, 4600.0, 0.0, 0.0, 5.0, 6500.0, 2500.0, 100.0, 0.0});
    registerTarget({"z", ArticulationType::Fricative, 320.0, 1650.0, 2750.0, 3600.0, 4600.0, 0.5, 0.0, 6.0, 6500.0, 2500.0, 100.0, 0.0});
    registerTarget({"ʃ", ArticulationType::Fricative, 350.0, 1800.0, 2800.0, 3700.0, 4700.0, 0.0, 0.0, 8.0, 3500.0, 1800.0, 110.0, 0.5});
    registerTarget({"ʒ", ArticulationType::Fricative, 370.0, 1850.0, 2850.0, 3700.0, 4700.0, 0.5, 0.0, 9.0, 3500.0, 1800.0, 110.0, 0.5});
    registerTarget({"f", ArticulationType::Fricative, 250.0, 1200.0, 2400.0, 3300.0, 4300.0, 0.0, 0.0, 7.0, 2500.0, 3000.0, 90.0, 0.0});
    registerTarget({"v", ArticulationType::Fricative, 280.0, 1250.0, 2450.0, 3300.0, 4300.0, 0.6, 0.0, 8.0, 2500.0, 3000.0, 90.0, 0.0});
    registerTarget({"x", ArticulationType::Fricative, 450.0, 1400.0, 2300.0, 3300.0, 4300.0, 0.0, 0.0, 10.0, 1400.0, 1200.0, 110.0, 0.0});
    registerTarget({"h", ArticulationType::Fricative, 500.0, 1500.0, 2500.0, 3500.0, 4500.0, 0.0, 0.0, 18.0, 1800.0, 4000.0, 80.0, 0.0});

    // --- Stop Plosives ---
    registerTarget({"p", ArticulationType::StopPlosive, 200.0, 900.0, 2300.0, 3300.0, 4300.0, 0.0, 0.0, 0.0, 1200.0, 1500.0, 70.0, 0.0});
    registerTarget({"b", ArticulationType::StopPlosive, 220.0, 950.0, 2350.0, 3300.0, 4300.0, 0.6, 0.0, 0.0, 1200.0, 1500.0, 70.0, 0.0});
    registerTarget({"t", ArticulationType::StopPlosive, 250.0, 1600.0, 2700.0, 3500.0, 4500.0, 0.0, 0.0, 0.0, 4500.0, 2000.0, 70.0, 0.0});
    registerTarget({"d", ArticulationType::StopPlosive, 270.0, 1650.0, 2750.0, 3500.0, 4500.0, 0.6, 0.0, 0.0, 4500.0, 2000.0, 70.0, 0.0});
    registerTarget({"k", ArticulationType::StopPlosive, 300.0, 1800.0, 2600.0, 3500.0, 4500.0, 0.0, 0.0, 0.0, 2400.0, 1800.0, 80.0, 0.0});
    registerTarget({"g", ArticulationType::StopPlosive, 320.0, 1850.0, 2650.0, 3500.0, 4500.0, 0.6, 0.0, 0.0, 2400.0, 1800.0, 80.0, 0.0});

    // --- Glottal Stop ---
    registerTarget({"ʔ", ArticulationType::GlottalStop, 150.0, 1200.0, 2400.0, 3400.0, 4400.0, 0.0, 0.0, 0.0, 1000.0, 1000.0, 40.0, 0.0});

    // --- Non-Pulmonic Clicks (Section 4.2) ---
    // Dental click [ǀ] (suction release at incisors; 4.8 kHz)
    {
        PhonemeTarget t{"ǀ", ArticulationType::Click, 400.0, 1800.0, 2800.0, 4800.0, 5200.0, 0.0, 0.0, 0.0, 4800.0, 1200.0, 35.0, 0.0};
        t.clickFrequencyHz = 4800.0;
        registerTarget(t);
    }
    // Alveolar click [ǃ] (suction release at alveolar ridge; cavitation pop at 1.8 kHz)
    {
        PhonemeTarget t{"ǃ", ArticulationType::Click, 350.0, 1400.0, 2400.0, 3500.0, 4500.0, 0.0, 0.0, 0.0, 1800.0, 900.0, 45.0, 0.0};
        t.clickFrequencyHz = 1800.0;
        registerTarget(t);
    }
    // Lateral click [ǁ] (side tongue release; broad resonance at 2.8 kHz)
    {
        PhonemeTarget t{"ǁ", ArticulationType::Click, 380.0, 1600.0, 2800.0, 3800.0, 4800.0, 0.0, 0.0, 0.0, 2800.0, 1500.0, 40.0, 0.0};
        t.clickFrequencyHz = 2800.0;
        registerTarget(t);
    }
    // Bilabial click [ʘ] (lip smack suction; 1.0 kHz)
    {
        PhonemeTarget t{"ʘ", ArticulationType::Click, 300.0, 900.0, 2200.0, 3300.0, 4300.0, 0.0, 0.0, 0.0, 1000.0, 800.0, 50.0, 0.8};
        t.clickFrequencyHz = 1000.0;
        registerTarget(t);
    }

    // --- ExtIPA Creature Extensions (Section 4.1) ---
    // Feline Purr [ʬ̃] / [ʙ]
    {
        PhonemeTarget t{"ʬ̃", ArticulationType::CreaturePurr, 220.0, 850.0, 2100.0, 3200.0, 4200.0, 0.8, 0.3, 20.0, 1200.0, 1000.0, 300.0, 0.0};
        t.purrActive = true;
        registerTarget(t);
    }
    registerTarget({"ʙ", ArticulationType::CreaturePurr, 220.0, 850.0, 2100.0, 3200.0, 4200.0, 0.8, 0.3, 20.0, 1200.0, 1000.0, 300.0, 0.0, false, true, false, false, 0.0});

    // Ventricular Growl [ʭ] / [a᷽]
    {
        PhonemeTarget t{"ʭ", ArticulationType::CreatureGrowl, 450.0, 950.0, 2200.0, 3200.0, 4200.0, 0.9, 0.0, 25.0, 1500.0, 1500.0, 250.0, 0.0};
        t.growlActive = true;
        registerTarget(t);
    }
    registerTarget({"a᷽", ArticulationType::CreatureGrowl, 550.0, 1100.0, 2400.0, 3300.0, 4300.0, 0.9, 0.0, 35.0, 1600.0, 1500.0, 250.0, 0.0, false, false, true, false, 0.0});

    // Velopharyngeal Snarl [f͌] / [v͌]
    {
        PhonemeTarget t{"f͌", ArticulationType::CreatureSnarl, 380.0, 1500.0, 2700.0, 3800.0, 4800.0, 0.2, 0.4, 8.0, 3800.0, 2200.0, 200.0, 0.0};
        t.snarlActive = true;
        registerTarget(t);
    }
    registerTarget({"v͌", ArticulationType::CreatureSnarl, 380.0, 1500.0, 2700.0, 3800.0, 4800.0, 0.7, 0.4, 9.0, 3800.0, 2200.0, 200.0, 0.0, false, false, false, true, 0.0});

    // Velic Hiss [ʩ]
    registerTarget({"ʩ", ArticulationType::CreatureHiss, 400.0, 1600.0, 3200.0, 4500.0, 5800.0, 0.0, 0.5, 6.0, 5800.0, 3000.0, 220.0, 0.0});

    // Ingressive airflow [↓]
    {
        PhonemeTarget t{"↓", ArticulationType::Vowel, 450.0, 1400.0, 2400.0, 3400.0, 4400.0, 0.6, 0.0, 35.0, 2500.0, 2000.0, 180.0, 0.0};
        t.ingressive = true;
        registerTarget(t);
    }
}

void PhonemeDatabase::registerTarget(PhonemeTarget target) {
    map_[target.symbol] = std::move(target);
}

const PhonemeTarget* PhonemeDatabase::find(std::string_view symbol) const noexcept {
    auto it = map_.find(std::string(symbol));
    if (it != map_.end()) {
        return &it->second;
    }
    return nullptr;
}

const PhonemeTarget& PhonemeDatabase::getOrDefault(std::string_view symbol) const noexcept {
    const auto* target = find(symbol);
    return target ? *target : defaultVowel_;
}

} // namespace vocalis::extipa
