#include "vocalis/vocalis.hpp"
#include <iostream>
#include <string>
#include <string_view>

using namespace vocalis;

void printUsage() {
    std::cout << "VocalisEngine CLI - Biomechanical ExtIPA Speech Synthesizer (C++20)\n\n"
              << "Usage: vocalis_cli [options]\n\n"
              << "Options:\n"
              << "  -i, --ipa <string>        ExtIPA phonetic input sequence (e.g. \"m-a-m-a\")\n"
              << "  -o, --output <file.wav>   Output WAV file path (default: output.wav)\n"
              << "  -p, --preset <name>       Speaker preset: male, female, feline, canine, avian, alien (default: male)\n"
              << "  -s, --samplerate <rate>   Sample rate: 44100 or 48000 (default: 44100)\n"
              << "  -h, --help                Show this help message\n\n"
              << "Examples:\n"
              << "  vocalis_cli -i \"m-a-m-a\" -o mama.wav\n"
              << "  vocalis_cli -i \"[ǀ] uː ʬ̃ ʭ\" -p feline -o beast.wav\n";
}

int main(int argc, char* argv[]) {
    std::string ipaString = "m-a-m-a";
    std::string outputPath = "output.wav";
    std::string presetName = "male";
    uint32_t sampleRate = 44100;

    for (int i = 1; i < argc; ++i) {
        std::string_view arg = argv[i];
        if (arg == "-h" || arg == "--help") {
            printUsage();
            return 0;
        } else if ((arg == "-i" || arg == "--ipa") && i + 1 < argc) {
            ipaString = argv[++i];
        } else if ((arg == "-o" || arg == "--output") && i + 1 < argc) {
            outputPath = argv[++i];
        } else if ((arg == "-p" || arg == "--preset") && i + 1 < argc) {
            presetName = argv[++i];
        } else if ((arg == "-s" || arg == "--samplerate") && i + 1 < argc) {
            sampleRate = static_cast<uint32_t>(std::stoul(argv[++i]));
        }
    }

    voice::SpeakerProfile profile = voice::SpeakerProfile::createHumanMale();
    if (presetName == "female") {
        profile = voice::SpeakerProfile::createHumanFemale();
    } else if (presetName == "feline") {
        profile = voice::SpeakerProfile::createFelinePredator();
    } else if (presetName == "canine") {
        profile = voice::SpeakerProfile::createCanineAlert();
    } else if (presetName == "avian") {
        profile = voice::SpeakerProfile::createAvianSyrinx();
    } else if (presetName == "alien") {
        profile = voice::SpeakerProfile::createAlienTonal();
    }

    std::cout << "[VocalisEngine] Initializing conductor at " << sampleRate << " Hz...\n";
    std::cout << "[VocalisEngine] Selected profile: " << profile.name << "\n";
    std::cout << "[VocalisEngine] Input ExtIPA:     " << ipaString << "\n";

    orchestra::Conductor conductor(sampleRate);
    conductor.setSpeakerProfile(profile);

    std::cout << "[VocalisEngine] Synthesizing acoustic stream...\n";
    AudioBuffer audio = conductor.synthesizeExtIPA(ipaString);

    std::cout << "[VocalisEngine] Exporting " << audio.durationSeconds() << "s audio to " << outputPath << "...\n";
    bool success = platform::WavWriter::writeFloat(outputPath, audio);

    if (success) {
        std::cout << "[VocalisEngine] Successfully generated " << outputPath << "!\n";
        return 0;
    } else {
        std::cerr << "[VocalisEngine] ERROR: Failed to write output file: " << outputPath << "\n";
        return 1;
    }
}
