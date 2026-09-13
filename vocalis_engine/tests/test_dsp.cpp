#include "vocalis/vocalis.hpp"
#include <iostream>
#include <cassert>
#include <cmath>

using namespace vocalis;

void testSmootherstep() {
    std::cout << "[TEST] Running testSmootherstep...\n";
    assert(std::abs(smootherstep(0.0) - 0.0) < 1e-6);
    assert(std::abs(smootherstep(1.0) - 1.0) < 1e-6);
    assert(std::abs(smootherstep(0.5) - 0.5) < 1e-6);

    // Monotonicity test
    SampleReal lastVal = 0.0;
    for (int i = 0; i <= 100; ++i) {
        SampleReal t = static_cast<SampleReal>(i) / 100.0;
        SampleReal val = smootherstep(t);
        assert(val >= lastVal - 1e-9);
        assert(val >= 0.0 && val <= 1.0);
        lastVal = val;
    }
    std::cout << "  -> PASS: Smootherstep is monotonic and properly bounded in [0, 1].\n";
}

void testBiquadStability() {
    std::cout << "[TEST] Running testBiquadStability...\n";
    dsp::Biquad biquad;
    uint32_t fs = 44100;
    biquad.setResonator(1000.0, 100.0, fs);

    // Feed impulse
    Sample impulse = 1.0f;
    Sample out0 = biquad.process(impulse);
    (void)out0;
    assert(!std::isnan(out0) && !std::isinf(out0));

    // Process 4410 samples (100 ms) and check decay
    Sample peakAfterDecay = 0.0f;
    for (int i = 0; i < 4410; ++i) {
        Sample out = biquad.process(0.0f);
        assert(!std::isnan(out) && !std::isinf(out));
        if (i > 2200 && std::abs(out) > peakAfterDecay) {
            peakAfterDecay = std::abs(out);
        }
    }
    // Formant resonator with 100 Hz bandwidth at 44.1kHz must decay to near zero after 50ms
    assert(peakAfterDecay < 0.05f);
    std::cout << "  -> PASS: Biquad resonator is stable and impulse response decays properly.\n";
}

void testPolyBlep() {
    std::cout << "[TEST] Running testPolyBlep...\n";
    SampleReal dt = 0.01;
    SampleReal blep0 = dsp::polyBlep(0.0, dt);
    (void)blep0;
    assert(blep0 < 0.0); // Correction at discontinuity is non-zero
    SampleReal blepFar = dsp::polyBlep(0.5, dt);
    (void)blepFar;
    assert(blepFar == 0.0); // Outside boundary zone, no correction
    std::cout << "  -> PASS: PolyBLEP anti-aliasing produces valid boundary corrections.\n";
}

void testNoiseGenerator() {
    std::cout << "[TEST] Running testNoiseGenerator...\n";
    dsp::NoiseGenerator noise(12345);
    double sum = 0.0;
    const int N = 10000;
    for (int i = 0; i < N; ++i) {
        Sample s = noise.nextWhite();
        assert(s >= -1.0f && s <= 1.0f);
        sum += s;
    }
    double mean = sum / N;
    (void)mean;
    // Mean of uniform white noise in [-1, 1] must be close to zero
    assert(std::abs(mean) < 0.05);
    std::cout << "  -> PASS: Noise generator outputs zero-mean uniform white noise.\n";
}

int main() {
    std::cout << "=== VocalisEngine DSP Test Suite ===\n";
    testSmootherstep();
    testBiquadStability();
    testPolyBlep();
    testNoiseGenerator();
    std::cout << "=== All DSP Tests PASSED! ===\n";
    return 0;
}
