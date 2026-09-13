#pragma once

#include <cstddef>
#include <cstdint>
#include <vector>
#include <span>
#include <cmath>
#include <numbers>
#include <string>
#include <string_view>
#include <algorithm>

namespace vocalis {

using Sample = float;
using SampleReal = double;

inline constexpr SampleReal PI = 3.14159265358979323846;
inline constexpr SampleReal TWO_PI = 2.0 * PI;
inline constexpr SampleReal HALF_PI = 0.5 * PI;
inline constexpr SampleReal SQRT_TWO = 1.41421356237309504880;

inline constexpr uint32_t DEFAULT_SAMPLE_RATE = 44100;
inline constexpr uint32_t HIGH_DEF_SAMPLE_RATE = 48000;
inline constexpr uint32_t CONTROL_RATE_HZ = 1000; // 1ms control sub-buffer rate

/// @brief Airflow direction for pulmonic and ingressive bioacoustics
enum class AirflowDirection : uint8_t {
    Egress, // Exhaling (Human speech default)
    Ingress // Inhaling (Animal whimpers, gasps, feline purr intake)
};

/// @brief Phonation excitation mode
enum class PhonationMode : uint8_t {
    Modal,
    Breathy,
    CreakyFry,
    VentricularGrowl,
    Whisper,
    Falsetto
};

/// @brief Continuous C2 Hermite Smootherstep polynomial: w(t) = 6t^5 - 15t^4 + 10t^3
/// Zero first and second derivatives at t=0 and t=1 guarantee smooth acceleration/deceleration.
[[nodiscard]] constexpr SampleReal smootherstep(SampleReal t) noexcept {
    if (t <= 0.0) return 0.0;
    if (t >= 1.0) return 1.0;
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0);
}

/// @brief Interpolates between a and b using smootherstep
[[nodiscard]] constexpr SampleReal interpolate_smootherstep(SampleReal a, SampleReal b, SampleReal t) noexcept {
    return a + smootherstep(t) * (b - a);
}

/// @brief Linear interpolation
[[nodiscard]] constexpr SampleReal lerp(SampleReal a, SampleReal b, SampleReal t) noexcept {
    return a + t * (b - a);
}

/// @brief Non-owning view over contiguous audio sample memory
using SampleSpan = std::span<Sample>;
using ConstSampleSpan = std::span<const Sample>;

/// @brief Contiguous mono/multi-channel audio sample buffer
struct AudioBuffer {
    std::vector<Sample> data;
    uint32_t sampleRate{DEFAULT_SAMPLE_RATE};
    uint16_t channels{1};

    AudioBuffer() = default;
    explicit AudioBuffer(size_t sampleCount, uint32_t sRate = DEFAULT_SAMPLE_RATE, uint16_t ch = 1)
        : data(sampleCount, 0.0f), sampleRate(sRate), channels(ch) {}

    [[nodiscard]] size_t size() const noexcept { return data.size(); }
    [[nodiscard]] bool empty() const noexcept { return data.empty(); }
    void clear() noexcept { data.clear(); }
    void resize(size_t count, Sample value = 0.0f) { data.resize(count, value); }

    [[nodiscard]] Sample* samples() noexcept { return data.data(); }
    [[nodiscard]] const Sample* samples() const noexcept { return data.data(); }

    [[nodiscard]] Sample& operator[](size_t idx) noexcept { return data[idx]; }
    [[nodiscard]] const Sample& operator[](size_t idx) const noexcept { return data[idx]; }

    [[nodiscard]] SampleSpan span() noexcept { return SampleSpan{data}; }
    [[nodiscard]] ConstSampleSpan span() const noexcept { return ConstSampleSpan{data}; }

    [[nodiscard]] double durationSeconds() const noexcept {
        if (sampleRate == 0 || channels == 0) return 0.0;
        return static_cast<double>(data.size()) / (static_cast<double>(sampleRate) * channels);
    }
};

} // namespace vocalis
