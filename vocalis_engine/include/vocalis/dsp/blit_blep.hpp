#pragma once

#include "vocalis/types.hpp"

namespace vocalis::dsp {

/// @brief PolyBLEP residual function for anti-aliasing step discontinuities
[[nodiscard]] inline SampleReal polyBlep(SampleReal t, SampleReal dt) noexcept {
    // 0 <= t < 1 is normalized phase
    if (t < dt) {
        t /= dt;
        return t + t - t * t - 1.0;
    }
    if (t > 1.0 - dt) {
        t = (t - 1.0) / dt;
        return t * t + t + t + 1.0;
    }
    return 0.0;
}

/// @brief PolyBLAMP residual function for anti-aliasing slope (derivative) discontinuities
[[nodiscard]] inline SampleReal polyBlamp(SampleReal t, SampleReal dt) noexcept {
    if (t < dt) {
        t /= dt;
        return -dt / 3.0 * (1.0 - t) * (1.0 - t) * (1.0 - t);
    }
    if (t > 1.0 - dt) {
        t = (t - 1.0) / dt;
        return dt / 3.0 * (1.0 + t) * (1.0 + t) * (1.0 + t);
    }
    return 0.0;
}

} // namespace vocalis::dsp
