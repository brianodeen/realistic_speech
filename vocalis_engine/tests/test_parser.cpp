#include "vocalis/vocalis.hpp"
#include <iostream>
#include <cassert>

using namespace vocalis;

void testStandardPhonemes() {
    std::cout << "[TEST] Running testStandardPhonemes...\n";
    extipa::ExtIPAParser parser;
    auto tokens = parser.parse("m-a-m-a");
    assert(tokens.size() == 4);
    assert(tokens[0].symbol == "m");
    assert(tokens[1].symbol == "a");
    assert(tokens[2].symbol == "m");
    assert(tokens[3].symbol == "a");
    assert(tokens[0].target.type == extipa::ArticulationType::Nasal);
    assert(tokens[1].target.type == extipa::ArticulationType::Vowel);
    std::cout << "  -> PASS: Standard phonemes correctly parsed.\n";
}

void testClicksAndEjectives() {
    std::cout << "[TEST] Running testClicksAndEjectives...\n";
    extipa::ExtIPAParser parser;
    auto tokens = parser.parse("[ǀ] [ǃ] [ǁ] [ʘ]");
    assert(tokens.size() == 4);
    assert(tokens[0].target.type == extipa::ArticulationType::Click);
    assert(tokens[1].target.type == extipa::ArticulationType::Click);
    assert(tokens[2].target.type == extipa::ArticulationType::Click);
    assert(tokens[3].target.type == extipa::ArticulationType::Click);
    assert(tokens[0].target.clickFrequencyHz == 4800.0);
    assert(tokens[1].target.clickFrequencyHz == 1800.0);
    std::cout << "  -> PASS: ExtIPA African non-pulmonic clicks correctly recognized.\n";
}

void testCreatureExtensions() {
    std::cout << "[TEST] Running testCreatureExtensions...\n";
    extipa::ExtIPAParser parser;
    auto tokens = parser.parse("ʬ̃ ʭ f͌ ʩ");
    assert(tokens.size() == 4);
    assert(tokens[0].target.purrActive == true);
    assert(tokens[1].target.growlActive == true);
    assert(tokens[2].target.snarlActive == true);
    assert(tokens[3].target.type == extipa::ArticulationType::CreatureHiss);
    std::cout << "  -> PASS: ExtIPA creature glyphs (purr, growl, snarl, hiss) correctly mapped.\n";
}

void testTonesAndLength() {
    std::cout << "[TEST] Running testTonesAndLength...\n";
    extipa::ExtIPAParser parser;
    auto tokens = parser.parse("a55 uː");
    assert(tokens.size() == 2);
    assert(tokens[0].chaoToneLevel == 55);
    assert(tokens[0].pitchScale > 1.2);
    assert(tokens[1].durationMs > tokens[1].target.baseDurationMs * 1.4);
    std::cout << "  -> PASS: Chao tones and vowel length modifiers correctly applied.\n";
}

int main() {
    std::cout << "=== VocalisEngine ExtIPA Parser Test Suite ===\n";
    testStandardPhonemes();
    testClicksAndEjectives();
    testCreatureExtensions();
    testTonesAndLength();
    std::cout << "=== All ExtIPA Parser Tests PASSED! ===\n";
    return 0;
}
