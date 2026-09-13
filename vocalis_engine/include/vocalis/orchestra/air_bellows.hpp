#pragma once

#include "vocalis/types.hpp"

namespace vocalis::orchestra {

struct AirBellowsParams {
    SampleReal lungPressurePa{800.0};       // 400 - 3000 Pa (normal speech ~800 Pa)
    AirflowDirection direction{AirflowDirection::Egress};
    SampleReal vitalCapacityRatio{1.0};      // 1.0 down to 0.0
    SampleReal depletionRatePerSec{0.05};   // Breath capacity reduction per second
};

/// @brief Instrument 1: The Air Bellows (Lungs & Diaphragm)
/// Generates subglottal pressure and aerodynamic driving force for downstream sound sources.
class AirBellows {
public:
    AirBellows() noexcept = default;

    void reset() noexcept {
        vitalCapacity_ = 1.0;
    }

    void setParams(const AirBellowsParams& params) noexcept {
        params_ = params;
        vitalCapacity_ = std::clamp(params.vitalCapacityRatio, 0.0, 1.0);
    }

    void setLungPressure(SampleReal pa) noexcept {
        params_.lungPressurePa = std::clamp(pa, 0.0, 5000.0);
    }

    void setAirflowDirection(AirflowDirection dir) noexcept {
        params_.direction = dir;
    }

    /// @brief Computes aerodynamic flow and pressure output for the current time step
    /// @param dt Time step in seconds (1.0 / sampleRate)
    /// @return Effective aerodynamic driving amplitude multiplier (typically 0.0 to 1.5)
    [[nodiscard]] SampleReal step(SampleReal dt) noexcept;

    [[nodiscard]] SampleReal currentPressurePa() const noexcept { return params_.lungPressurePa; }
    [[nodiscard]] AirflowDirection direction() const noexcept { return params_.direction; }
    [[nodiscard]] SampleReal vitalCapacity() const noexcept { return vitalCapacity_; }

private:
    AirBellowsParams params_{};
    SampleReal vitalCapacity_{1.0};
};

} // namespace vocalis::orchestra
