#include "vocalis/extipa/parser.hpp"
#include <cctype>

namespace vocalis::extipa {

// Helper to extract next UTF-8 codepoint length
static size_t utf8CharLength(unsigned char lead) noexcept {
    if (lead < 0x80) return 1;
    if ((lead >> 5) == 0x06) return 2;
    if ((lead >> 4) == 0x0E) return 3;
    if ((lead >> 3) == 0x1E) return 4;
    return 1;
}

bool ExtIPAParser::isCursiveTie(std::string_view glyph) noexcept {
    return glyph == "‿" || glyph == "_";
}

bool ExtIPAParser::isLigature(std::string_view glyph) noexcept {
    return glyph == "͡";
}

bool ExtIPAParser::isGlottalStop(std::string_view glyph) noexcept {
    return glyph == "ʔ";
}

bool ExtIPAParser::isLengthMarker(std::string_view glyph) noexcept {
    return glyph == "ː" || glyph == ":" || glyph == "ːː";
}

std::vector<ExtIPAToken> ExtIPAParser::parse(std::string_view utf8Input) const {
    std::vector<ExtIPAToken> tokens;
    const auto& db = PhonemeDatabase::instance();

    size_t i = 0;
    while (i < utf8Input.size()) {
        char c = utf8Input[i];

        // Handle punctuation & delimiters
        if (c == '?' || c == '!' || c == '.' || c == ',' || c == ';' || c == ':' ||
            c == '[' || c == ']' || c == '/' || c == '-' || std::isspace(static_cast<unsigned char>(c))) {
            
            if (c == '?' && !tokens.empty()) {
                tokens.back().pitchScale = 1.25; // Interrogative rising cadence
            } else if (c == '!' && !tokens.empty()) {
                tokens.back().pitchScale = 1.15; // Exclamation emphasis
            } else if (c == '.' || c == ',' || c == ';' || std::isspace(static_cast<unsigned char>(c))) {
                if (!tokens.empty() && tokens.back().target.type != ArticulationType::Silence) {
                    ExtIPAToken pauseToken;
                    pauseToken.symbol = " ";
                    pauseToken.target = db.getOrDefault("_");
                    pauseToken.durationMs = (c == '.') ? 120.0 : ((c == ',' || c == ';') ? 60.0 : 40.0);
                    tokens.push_back(pauseToken);
                }
            }
            ++i;
            continue;
        }

        // Check for tone numbers (e.g. 55, 35, 214, 51, 33, 11)
        if (std::isdigit(static_cast<unsigned char>(c))) {
            size_t numStart = i;
            while (i < utf8Input.size() && std::isdigit(static_cast<unsigned char>(utf8Input[i]))) {
                ++i;
            }
            std::string toneStr(utf8Input.substr(numStart, i - numStart));
            int toneVal = std::stoi(toneStr);

            if (!tokens.empty()) {
                tokens.back().chaoToneLevel = toneVal;
                // Calculate pitch scale from Chao 5-level system (1 = low, 5 = high)
                if (toneVal == 55) tokens.back().pitchScale = 1.35;
                else if (toneVal == 35) tokens.back().pitchScale = 1.2;
                else if (toneVal == 214) tokens.back().pitchScale = 0.95;
                else if (toneVal == 51) tokens.back().pitchScale = 1.1;
                else if (toneVal == 33) tokens.back().pitchScale = 1.0;
                else if (toneVal == 11) tokens.back().pitchScale = 0.75;
            }
            continue;
        }

        // Extract UTF-8 character
        size_t len = utf8CharLength(static_cast<unsigned char>(c));
        len = std::min(len, utf8Input.size() - i);
        std::string_view glyph = utf8Input.substr(i, len);

        // Check for multi-char glyphs / diacritics attached to phoneme (e.g. ʬ̃, a᷽, f͌, v͌)
        // Check if next chars contain combining diacritics
        size_t extendedLen = len;
        while (i + extendedLen < utf8Input.size()) {
            unsigned char nextLead = static_cast<unsigned char>(utf8Input[i + extendedLen]);
            size_t nextCharLen = utf8CharLength(nextLead);
            std::string_view cand = utf8Input.substr(i, extendedLen + nextCharLen);
            if (db.find(cand) != nullptr) {
                extendedLen += nextCharLen;
            } else {
                break;
            }
        }
        if (extendedLen > len) {
            glyph = utf8Input.substr(i, extendedLen);
            len = extendedLen;
        }

        // Check modifiers
        if (isLengthMarker(glyph)) {
            if (!tokens.empty()) {
                tokens.back().durationMs *= 1.5;
            }
            i += len;
            continue;
        }

        if (isCursiveTie(glyph)) {
            if (!tokens.empty()) {
                tokens.back().cursiveTiedToNext = true;
            }
            i += len;
            continue;
        }

        if (isLigature(glyph)) {
            if (!tokens.empty()) {
                tokens.back().coarticulatedWithNext = true;
            }
            i += len;
            continue;
        }

        // Standard phoneme token or creature sound
        ExtIPAToken token;
        token.symbol = std::string(glyph);
        token.target = db.getOrDefault(glyph);
        token.durationMs = token.target.baseDurationMs;

        if (isGlottalStop(glyph)) {
            token.isGlottalStop = true;
            token.target.type = ArticulationType::GlottalStop;
        }

        tokens.push_back(token);
        i += len;
    }

    return tokens;
}

} // namespace vocalis::extipa
