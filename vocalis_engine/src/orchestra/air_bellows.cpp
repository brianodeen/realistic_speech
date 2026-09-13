#include "vocalis/orchestra/air_bellows.hpp"
#include <algorithm>
#include <cmath>

namespace vocalis::orchestra {

SampleReal AirBellows::step(SampleReal dt) noexcept {
    // Deplete vital capacity over time if pressure is active
    if (params_.lungPressurePa > 50.0) {
        vitalCapacity_ = std::max(0.0, vitalCapacity_ - params_.depletionRatePerSec * dt);
    } else {
        // Regenerate breath during silence/rest
        vitalCapacity_ = std::min(1.0, vitalCapacity_ + 0.2 * dt);
    }

    // Normalized pressure factor (800 Pa = 1.0 nominal baseline)
    SampleReal pressureFactor = params_.lungPressurePa / 800.0;

    // Declination factor: natural slight drop in vocal power when lungs are nearly empty
    SampleReal declination = 0.85 + 0.15 * smootherstep(vitalCapacity_);

    SampleReal drive = pressureFactor * declination;

    // Ingress airflow has a slightly different turbulent / aspirated aerodynamic character
    if (params_.direction == AirflowDirection::Ingress) {
        drive *= 0.8;
    }

    return drive;
}

} // namespace vocalis::orchestra
