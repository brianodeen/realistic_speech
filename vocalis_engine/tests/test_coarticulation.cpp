#include "vocalis/vocalis.hpp"
#include <iostream>
#include <cassert>
#include <cmath>

using namespace vocalis;

void testC2Continuity() {
    std::cout << "[TEST] Running testC2Continuity...\n";

    extipa::ExtIPAParser parser;
    auto tokens = parser.parse("a‿i");
    assert(tokens.size() == 2);

    extipa::CursiveCompounder compounder;
    auto trajectory = compounder.compound(tokens, 120.0);
    assert(trajectory.size() >= 2);

    // Verify F1 transitions from a (~800Hz) to i (~280Hz)
    SampleReal f1_start = trajectory.front().f1;
    SampleReal f1_target = trajectory[1].f1;
    assert(f1_start > 700.0);
    assert(f1_target < 400.0);

    // Verify smooth interpolation across 100 sub-steps
    SampleReal lastF1 = f1_start;
    SampleReal maxDelta = 0.0;
    for (int step = 0; step <= 100; ++step) {
        SampleReal t = static_cast<SampleReal>(step) / 100.0;
        SampleReal currentF1 = interpolate_smootherstep(f1_start, f1_target, t);
        SampleReal delta = std::abs(currentF1 - lastF1);
        if (delta > maxDelta) maxDelta = delta;
        lastF1 = currentF1;
    }

    // With 100 steps over a ~520Hz range, smootherstep max derivative ~1.875 * mean_delta (~9.7 Hz)
    assert(maxDelta < 15.0);
    std::cout << "  -> PASS: C2 Hermite smootherstep transitions formants with maximum delta " << maxDelta << " Hz.\n";
}

void testConductorSynthesisPipeline() {
    std::cout << "[TEST] Running testConductorSynthesisPipeline...\n";
    orchestra::Conductor conductor(44100);
    AudioBuffer audio = conductor.synthesizeExtIPA("s-a-m");

    assert(!audio.empty());
    assert(audio.durationSeconds() > 0.1);

    // Ensure generated audio has non-zero energy and no NaNs or Infs
    bool hasNonZero = false;
    for (size_t i = 0; i < audio.size(); ++i) {
        Sample s = audio[i];
        assert(!std::isnan(s) && !std::isinf(s));
        if (std::abs(s) > 0.0001f) {
            hasNonZero = true;
        }
    }
    assert(hasNonZero);
    std::cout << "  -> PASS: Conductor successfully synthesized " << audio.durationSeconds() << "s of speech without numerical errors.\n";
}

int main() {
    std::cout << "=== VocalisEngine Coarticulation Test Suite ===\n";
    testC2Continuity();
    testConductorSynthesisPipeline();
    std::cout << "=== All Coarticulation Tests PASSED! ===\n";
    return 0;
}
