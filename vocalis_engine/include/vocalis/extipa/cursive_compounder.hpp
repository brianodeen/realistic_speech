#pragma once

#include "vocalis/types.hpp"
#include "vocalis/extipa/parser.hpp"
#include <vector>

namespace vocalis::extipa {

struct ArticulatoryTrajectoryPoint {
    SampleReal timeSec{0.0};
    SampleReal f0{120.0};
    SampleReal f1{500.0};
    SampleReal f2{1500.0};
    SampleReal f3{2500.0};
    SampleReal f4{3500.0};
    SampleReal f5{4500.0};
    SampleReal lungPressurePa{800.0};
    SampleReal constrictionAperture{50.0};
    SampleReal noiseCenterFreq{5000.0};
    SampleReal noiseBandwidth{2000.0};
    SampleReal velicAperture{0.0};
    SampleReal voicingRatio{1.0};
    SampleReal lipRoundingCm{0.0};
    bool isGlottalStop{false};
    bool purrActive{false};
    bool growlActive{false};
    bool snarlActive{false};
    SampleReal clickFrequencyHz{0.0};
};

class CursiveCompounder {
public:
    CursiveCompounder() = default;

    /// @brief Compounds a sequence of ExtIPA tokens into continuous physical trajectory points
    /// using Section 5.1 C2 Hermite smootherstep coarticulation
    [[nodiscard]] std::vector<ArticulatoryTrajectoryPoint> compound(
        const std::vector<ExtIPAToken>& tokens,
        SampleReal baseF0 = 120.0,
        SampleReal transitionDurationMs = 35.0
    ) const;
};

} // namespace vocalis::extipa
