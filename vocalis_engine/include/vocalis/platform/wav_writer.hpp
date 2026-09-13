#pragma once

#include "vocalis/types.hpp"
#include <fstream>
#include <string>
#include <cstring>
#include <stdexcept>
#include <algorithm>

namespace vocalis::platform {

enum class WavFormat : uint16_t {
    Pcm16 = 1,
    IeeeFloat = 3
};

class WavWriter {
public:
    static bool writeFloat(const std::string& filePath, const AudioBuffer& buffer) {
        return write(filePath, buffer, WavFormat::IeeeFloat);
    }

    static bool writePcm16(const std::string& filePath, const AudioBuffer& buffer) {
        return write(filePath, buffer, WavFormat::Pcm16);
    }

    static bool write(const std::string& filePath, const AudioBuffer& buffer, WavFormat format = WavFormat::Pcm16) {
        std::ofstream file(filePath, std::ios::binary);
        if (!file.is_open()) {
            return false;
        }

        uint32_t sampleRate = buffer.sampleRate;
        uint16_t numChannels = buffer.channels;
        uint16_t bitsPerSample = (format == WavFormat::IeeeFloat) ? 32 : 16;
        uint16_t audioFormat = static_cast<uint16_t>(format);
        uint16_t blockAlign = numChannels * (bitsPerSample / 8);
        uint32_t byteRate = sampleRate * blockAlign;
        uint32_t numSamples = static_cast<uint32_t>(buffer.size());
        uint32_t dataBytes = numSamples * (bitsPerSample / 8);
        uint32_t chunkSize = 36 + dataBytes;

        // RIFF Header
        file.write("RIFF", 4);
        file.write(reinterpret_cast<const char*>(&chunkSize), 4);
        file.write("WAVE", 4);

        // Sub-chunk 1: fmt 
        file.write("fmt ", 4);
        uint32_t subchunk1Size = 16;
        file.write(reinterpret_cast<const char*>(&subchunk1Size), 4);
        file.write(reinterpret_cast<const char*>(&audioFormat), 2);
        file.write(reinterpret_cast<const char*>(&numChannels), 2);
        file.write(reinterpret_cast<const char*>(&sampleRate), 4);
        file.write(reinterpret_cast<const char*>(&byteRate), 4);
        file.write(reinterpret_cast<const char*>(&blockAlign), 2);
        file.write(reinterpret_cast<const char*>(&bitsPerSample), 2);

        // Sub-chunk 2: data
        file.write("data", 4);
        file.write(reinterpret_cast<const char*>(&dataBytes), 4);

        if (format == WavFormat::IeeeFloat) {
            file.write(reinterpret_cast<const char*>(buffer.samples()), dataBytes);
        } else {
            // Convert float (-1.0f to 1.0f) to signed 16-bit PCM (-32768 to 32767)
            std::vector<int16_t> pcmData(numSamples);
            for (size_t i = 0; i < numSamples; ++i) {
                float val = std::clamp(buffer[i], -1.0f, 1.0f);
                pcmData[i] = static_cast<int16_t>(std::round(val * 32767.0f));
            }
            file.write(reinterpret_cast<const char*>(pcmData.data()), dataBytes);
        }

        return file.good();
    }
};

} // namespace vocalis::platform
