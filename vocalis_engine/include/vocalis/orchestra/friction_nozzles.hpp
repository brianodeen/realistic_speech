#pragma once

#include "vocalis/types.hpp"
#include "vocalis/dsp/noise_generator.hpp"
#include "vocalis/dsp/biquad.hpp"

namespace vocalis::orchestra {

struct ConstrictionParams {
    SampleReal apertureMm2{50.0};           // Narrowing: < 15.0 mm2 generates turbulence, 0.0 = occlusion/stop
    SampleReal centerFreqHz{5000.0};        // [s] ~6500Hz, [ʃ] ~3500Hz, [x] ~1400Hz, [f] ~2500Hz
    SampleReal bandwidthHz{2000.0};         // Spectral spread
    SampleReal vortexSheddingRate{1.0};     // Mucosal rasp / turbulence irregularity
    SampleReal plosiveBurstEnergy{0.0};     // Transient release spike energy
};

/// @brief Instrument 3: The Friction Nozzles (Articulatory Constrictions)
/// Generates aerodynamic turbulent hiss, whistling jets, and plosive release bursts.
class FrictionNozzles {
public:
    explicit FrictionNozzles(uint32_t sampleRate = DEFAULT_SAMPLE_RATE) noexcept;

    void reset() noexcept;

    void setSampleRate(uint32_t sampleRate) noexcept {
        sampleRate_ = sampleRate > 0 ? sampleRate : DEFAULT_SAMPLE_RATE;
    }

    void setParams(const ConstrictionParams& params) noexcept;

    /// @brief Trigger a plosive release transient (e.g., [p], [t], [k], clicks)
    void triggerPlosiveBurst(SampleReal burstEnergy = 1.0) noexcept;

    /// @brief Generate turbulent acoustic noise sample
    /// @param airflowDrive Driving airflow from Air Bellows
    [[nodiscard]] Sample step(SampleReal airflowDrive) noexcept;

    [[nodiscard]] const ConstrictionParams& params() const noexcept { return params_; }

private:
    uint32_t sampleRate_{DEFAULT_SAMPLE_RATE};
    ConstrictionParams params_{};
    dsp::NoiseGenerator noiseGen_{};
    dsp::Biquad bandpassFilter_{};
    dsp::Biquad raspFilter_{};

    SampleReal burstDecay_{0.0};
    SampleReal lastAperture_{50.0};
};

} // namespace vocalis::orchestra
