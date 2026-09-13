#include "vocalis/dsp/spline_interpolator.hpp"
#include <algorithm>

namespace vocalis::dsp {

Point2D evaluateCubicBezier(Point2D p0, Point2D p1, Point2D p2, Point2D p3, SampleReal t) noexcept {
    t = std::clamp(t, 0.0, 1.0);
    SampleReal u = 1.0 - t;
    SampleReal tt = t * t;
    SampleReal uu = u * u;
    SampleReal uuu = uu * u;
    SampleReal ttt = tt * t;

    Point2D p;
    p.x = uuu * p0.x + 3.0 * uu * t * p1.x + 3.0 * u * tt * p2.x + ttt * p3.x;
    p.y = uuu * p0.y + 3.0 * uu * t * p1.y + 3.0 * u * tt * p2.y + ttt * p3.y;
    return p;
}

SampleReal evaluateBezierPitch(SampleReal fStart, SampleReal fControl1, SampleReal fControl2, SampleReal fEnd, SampleReal t) noexcept {
    Point2D p0{0.0, fStart};
    Point2D p1{0.33, fControl1};
    Point2D p2{0.67, fControl2};
    Point2D p3{1.0, fEnd};
    return evaluateCubicBezier(p0, p1, p2, p3, t).y;
}

} // namespace vocalis::dsp
