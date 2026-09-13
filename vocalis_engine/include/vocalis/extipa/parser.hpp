#pragma once

#include "vocalis/types.hpp"
#include "vocalis/extipa/phoneme_map.hpp"
#include <string>
#include <string_view>
#include <vector>

namespace vocalis::extipa {

struct ExtIPAToken {
    std::string symbol;
    PhonemeTarget target;
    SampleReal durationMs{120.0};
    SampleReal pitchScale{1.0};           // Tone multiplier on base F0
    bool cursiveTiedToNext{false};        // '‿' tie bar
    bool coarticulatedWithNext{false};    // '͡' ligature bar
    bool isGlottalStop{false};            // 'ʔ'
    int chaoToneLevel{-1};                // Chao tone code e.g. 55, 35, 214, 51, 33, 11
};

class ExtIPAParser {
public:
    ExtIPAParser() = default;

    /// @brief Parse an ExtIPA UTF-8 string into a sequence of articulated phonetic tokens
    /// Handles phonemes, length markers (ː, ːː), tone marks, cursive ties (‿), and diacritics
    [[nodiscard]] std::vector<ExtIPAToken> parse(std::string_view utf8Input) const;

    /// @brief Check if symbol is a cursive tie or ligature
    [[nodiscard]] static bool isCursiveTie(std::string_view glyph) noexcept;
    [[nodiscard]] static bool isLigature(std::string_view glyph) noexcept;
    [[nodiscard]] static bool isGlottalStop(std::string_view glyph) noexcept;
    [[nodiscard]] static bool isLengthMarker(std::string_view glyph) noexcept;
};

} // namespace vocalis::extipa
