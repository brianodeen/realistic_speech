#include "vocalis/vocalis.hpp"
#include <iostream>
#include <chrono>
#include <iomanip>

using namespace vocalis;

int main() {
    std::cout << "========================================================\n";
    std::cout << " VocalisEngine Real-Time Factor Synthesis Benchmark\n";
    std::cout << " Target: Synthesis Speed >= 50x Real-Time on 1 CPU Core\n";
    std::cout << "========================================================\n";

    orchestra::Conductor conductor(44100);

    // Utterance testing cursive transitions, vowels, fricatives, nasals, clicks
    std::string script = "m-a-m-a s-a-n [ǀ] uː ʬ̃ ʭ";

    // Warm-up run
    AudioBuffer warmup = conductor.synthesizeExtIPA(script);

    // Timed benchmark iterations
    const int iterations = 50;
    double totalAudioDurationSec = 0.0;
    double totalComputeTimeSec = 0.0;

    auto tStart = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < iterations; ++i) {
        AudioBuffer buf = conductor.synthesizeExtIPA(script);
        totalAudioDurationSec += buf.durationSeconds();
    }
    auto tEnd = std::chrono::high_resolution_clock::now();

    std::chrono::duration<double> elapsed = tEnd - tStart;
    totalComputeTimeSec = elapsed.count();

    double realTimeFactor = totalAudioDurationSec / totalComputeTimeSec;
    double msPerSecondAudio = (totalComputeTimeSec / totalAudioDurationSec) * 1000.0;

    std::cout << std::fixed << std::setprecision(2);
    std::cout << "Total Audio Synthesized: " << totalAudioDurationSec << " seconds\n";
    std::cout << "Total Computation Time:  " << totalComputeTimeSec * 1000.0 << " ms\n";
    std::cout << "Compute time per audio second: " << msPerSecondAudio << " ms/sec\n";
    std::cout << "Synthesis Real-Time Factor:    " << realTimeFactor << "x Real-Time\n";
    std::cout << "Benchmark Result: ";

    if (realTimeFactor >= 50.0) {
        std::cout << "[PASSED] Exceeds >= 50x real-time performance target!\n";
    } else {
        std::cout << "[NOTICE] Achieved " << realTimeFactor << "x real-time speed.\n";
    }

    return 0;
}
