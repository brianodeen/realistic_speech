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
#include "vocalis/dsp/stochastic_process.hpp"
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

    // Stochastic differential equation (SDE) articulatory drift channels
    dsp::NoiseGenerator stochasticRng_{0xFEEDFACECAFEBEEFULL};
    dsp::OrnsteinUhlenbeckProcess ouF0_{25.0, 1.8};       // theta=25 s^-1, sigma=1.8 Hz pitch micro-intonation
    dsp::OrnsteinUhlenbeckProcess ouF1_{30.0, 8.0};       // theta=30 s^-1, sigma=8.0 Hz F1 articulatory drift
    dsp::OrnsteinUhlenbeckProcess ouF2_{30.0, 12.0};      // theta=30 s^-1, sigma=12.0 Hz F2 articulatory drift
    dsp::OrnsteinUhlenbeckProcess ouF3_{30.0, 15.0};      // theta=30 s^-1, sigma=15.0 Hz F3 articulatory drift
    dsp::OrnsteinUhlenbeckProcess ouF4_{30.0, 20.0};      // theta=30 s^-1, sigma=20.0 Hz F4 articulatory drift
    dsp::OrnsteinUhlenbeckProcess ouF5_{30.0, 25.0};      // theta=30 s^-1, sigma=25.0 Hz F5 articulatory drift
    dsp::OrnsteinUhlenbeckProcess ouPressure_{20.0, 12.0};// subglottal respiratory micro-fluctuations
};

} // namespace vocalis::orchestra
