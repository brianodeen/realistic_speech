#pragma once

#include "vocalis/types.hpp"
#include "vocalis/voice/speaker_profile.hpp"
#include "vocalis/extipa/parser.hpp"
#include "vocalis/extipa/cursive_compounder.hpp"
#include "vocalis/orchestra/air_bellows.hpp"
#include "vocalis/orchestra/acoustic_reeds.hpp"
#include "vocalis/orchestra/friction_nozzles.hpp"
#include "vocalis/orchestra/bioacoustics.hpp"
#include "vocalis/orchestra/resonant_chambers.hpp"
#include "vocalis/orchestra/radiation_bell.hpp"
#include <vector>

namespace vocalis::orchestra {

class Conductor {
public:
    explicit Conductor(uint32_t sampleRate = DEFAULT_SAMPLE_RATE) noexcept;

    void setSampleRate(uint32_t sampleRate) noexcept;
    void setSpeakerProfile(const voice::SpeakerProfile& profile) noexcept;

    /// @brief Synthesizes an audio stream from an ExtIPA UTF-8 phonetic string
    [[nodiscard]] AudioBuffer synthesizeExtIPA(std::string_view extIpaString);

    /// @brief Synthesizes an audio stream from a list of ExtIPA tokens
    [[nodiscard]] AudioBuffer synthesize(const std::vector<extipa::ExtIPAToken>& tokens);

    /// @brief Synthesizes an audio stream from continuous trajectory points
    [[nodiscard]] AudioBuffer synthesizeTrajectory(const std::vector<extipa::ArticulatoryTrajectoryPoint>& trajectory);

    [[nodiscard]] const voice::SpeakerProfile& profile() const noexcept { return profile_; }

private:
    uint32_t sampleRate_{DEFAULT_SAMPLE_RATE};
    voice::SpeakerProfile profile_{};

    // The Ensemble of 6 Instruments
    AirBellows bellows_{};
    AcousticReeds reeds_{};
    FrictionNozzles nozzles_{};
    BioacousticModulator bioacoustics_{};
    ResonantChambers chambers_{};
    RadiationBell bell_{};

    extipa::ExtIPAParser parser_{};
    extipa::CursiveCompounder compounder_{};
};

} // namespace vocalis::orchestra
