#pragma once

#include "vocalis/types.hpp"
#include <vector>

namespace vocalis::dsp {

struct Point2D {
    SampleReal x{0.0};
    SampleReal y{0.0};
};

/// @brief Evaluates a cubic Bezier curve at parameter t in [0, 1]
[[nodiscard]] Point2D evaluateCubicBezier(Point2D p0, Point2D p1, Point2D p2, Point2D p3, SampleReal t) noexcept;

/// @brief Evaluates pitch along a Bezier pitch contour given normalized time t in [0, 1]
[[nodiscard]] SampleReal evaluateBezierPitch(SampleReal fStart, SampleReal fControl1, SampleReal fControl2, SampleReal fEnd, SampleReal t) noexcept;

/// @brief Smooth state transition tracker using C2 Hermite smootherstep
class SmootherstepTrajectory {
public:
    SmootherstepTrajectory() noexcept = default;
    SmootherstepTrajectory(SampleReal startValue, SampleReal targetValue, size_t transitionSamples) noexcept
        : startVal_(startValue), targetVal_(targetValue), currentVal_(startValue), totalSamples_(transitionSamples) {}

    void reset(SampleReal startValue, SampleReal targetValue, size_t transitionSamples) noexcept {
        startVal_ = startValue;
        targetVal_ = targetValue;
        currentVal_ = startValue;
        totalSamples_ = transitionSamples;
        currentSample_ = 0;
    }

    [[nodiscard]] SampleReal next() noexcept {
        if (totalSamples_ == 0 || currentSample_ >= totalSamples_) {
            currentVal_ = targetVal_;
            return currentVal_;
        }
        SampleReal t = static_cast<SampleReal>(currentSample_) / static_cast<SampleReal>(totalSamples_);
        currentVal_ = interpolate_smootherstep(startVal_, targetVal_, t);
        ++currentSample_;
        return currentVal_;
    }

    [[nodiscard]] SampleReal currentValue() const noexcept { return currentVal_; }
    [[nodiscard]] bool isFinished() const noexcept { return currentSample_ >= totalSamples_; }

private:
    SampleReal startVal_{0.0};
    SampleReal targetVal_{0.0};
    SampleReal currentVal_{0.0};
    size_t totalSamples_{0};
    size_t currentSample_{0};
};

} // namespace vocalis::dsp
