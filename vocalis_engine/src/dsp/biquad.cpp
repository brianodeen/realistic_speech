#include "vocalis/dsp/biquad.hpp"
#include <algorithm>

namespace vocalis::dsp {

void Biquad::setResonator(SampleReal centerFreqHz, SampleReal bandwidthHz, uint32_t sampleRate) noexcept {
    if (sampleRate == 0) return;
    SampleReal fs = static_cast<SampleReal>(sampleRate);
    SampleReal nyquist = fs * 0.499;
    centerFreqHz = std::clamp(centerFreqHz, 10.0, nyquist);
    bandwidthHz = std::clamp(bandwidthHz, 10.0, fs * 0.5);

    SampleReal R = std::exp(-PI * bandwidthHz / fs);
    SampleReal theta = TWO_PI * centerFreqHz / fs;

    // Unit-gain peak normalization:
    // The denominator magnitude at resonance omega = theta is (1 - R) * sqrt(1 - 2*R*cos(2*theta) + R*R)
    // Setting b0 = (1 - R) * sqrt(1 - 2*R*cos(2*theta) + R*R) guarantees peak gain |H(e^j*theta)| == 1.0 (0 dB)
    // across all formant frequencies, eliminating the 23 dB low-frequency bass boost and muffling.
    SampleReal denom = std::sqrt(1.0 - 2.0 * R * std::cos(2.0 * theta) + R * R);
    coeffs_.b0 = (1.0 - R) * denom;
    coeffs_.b1 = 0.0;
    coeffs_.b2 = 0.0;
    coeffs_.a1 = -2.0 * R * std::cos(theta);
    coeffs_.a2 = R * R;
}

void Biquad::setCascadeResonator(SampleReal centerFreqHz, SampleReal bandwidthHz, uint32_t sampleRate) noexcept {
    if (sampleRate == 0) return;
    SampleReal fs = static_cast<SampleReal>(sampleRate);
    SampleReal nyquist = fs * 0.499;
    centerFreqHz = std::clamp(centerFreqHz, 10.0, nyquist);
    bandwidthHz = std::clamp(bandwidthHz, 10.0, fs * 0.5);

    SampleReal R = std::exp(-PI * bandwidthHz / fs);
    SampleReal theta = TWO_PI * centerFreqHz / fs;

    coeffs_.a1 = -2.0 * R * std::cos(theta);
    coeffs_.a2 = R * R;
    coeffs_.b0 = 1.0 + coeffs_.a1 + coeffs_.a2; // Klatt unity DC normalization: H(1) = 1.0
    coeffs_.b1 = 0.0;
    coeffs_.b2 = 0.0;
}

void Biquad::setAntiResonator(SampleReal zeroFreqHz, SampleReal bandwidthHz, uint32_t sampleRate) noexcept {
    if (sampleRate == 0) return;
    SampleReal fs = static_cast<SampleReal>(sampleRate);
    SampleReal nyquist = fs * 0.499;
    zeroFreqHz = std::clamp(zeroFreqHz, 10.0, nyquist);
    bandwidthHz = std::clamp(bandwidthHz, 10.0, fs * 0.5);

    SampleReal R = std::exp(-PI * bandwidthHz / fs);
    SampleReal theta = TWO_PI * zeroFreqHz / fs;

    // Zero filter: inverse of resonator normalized so DC gain is approx 1
    // H(z) = (1 - 2*R*cos(theta)*z^-1 + R^2*z^-2) / (1 - R)
    SampleReal norm = 1.0 / (1.0 - R);
    coeffs_.b0 = norm;
    coeffs_.b1 = -2.0 * R * std::cos(theta) * norm;
    coeffs_.b2 = (R * R) * norm;
    coeffs_.a1 = 0.0;
    coeffs_.a2 = 0.0;
}

void Biquad::setHighPass(SampleReal cutoffHz, SampleReal q, uint32_t sampleRate) noexcept {
    if (sampleRate == 0) return;
    SampleReal fs = static_cast<SampleReal>(sampleRate);
    cutoffHz = std::clamp(cutoffHz, 10.0, fs * 0.49);
    q = std::clamp(q, 0.1, 20.0);

    SampleReal w0 = TWO_PI * cutoffHz / fs;
    SampleReal cosw0 = std::cos(w0);
    SampleReal alpha = std::sin(w0) / (2.0 * q);

    SampleReal b0 = (1.0 + cosw0) / 2.0;
    SampleReal b1 = -(1.0 + cosw0);
    SampleReal b2 = (1.0 + cosw0) / 2.0;
    SampleReal a0 = 1.0 + alpha;
    SampleReal a1 = -2.0 * cosw0;
    SampleReal a2 = 1.0 - alpha;

    coeffs_.b0 = b0 / a0;
    coeffs_.b1 = b1 / a0;
    coeffs_.b2 = b2 / a0;
    coeffs_.a1 = a1 / a0;
    coeffs_.a2 = a2 / a0;
}

void Biquad::setLowPass(SampleReal cutoffHz, SampleReal q, uint32_t sampleRate) noexcept {
    if (sampleRate == 0) return;
    SampleReal fs = static_cast<SampleReal>(sampleRate);
    cutoffHz = std::clamp(cutoffHz, 10.0, fs * 0.49);
    q = std::clamp(q, 0.1, 20.0);

    SampleReal w0 = TWO_PI * cutoffHz / fs;
    SampleReal cosw0 = std::cos(w0);
    SampleReal alpha = std::sin(w0) / (2.0 * q);

    SampleReal b0 = (1.0 - cosw0) / 2.0;
    SampleReal b1 = 1.0 - cosw0;
    SampleReal b2 = (1.0 - cosw0) / 2.0;
    SampleReal a0 = 1.0 + alpha;
    SampleReal a1 = -2.0 * cosw0;
    SampleReal a2 = 1.0 - alpha;

    coeffs_.b0 = b0 / a0;
    coeffs_.b1 = b1 / a0;
    coeffs_.b2 = b2 / a0;
    coeffs_.a1 = a1 / a0;
    coeffs_.a2 = a2 / a0;
}

void Biquad::setBandPass(SampleReal centerFreqHz, SampleReal bandwidthHz, uint32_t sampleRate) noexcept {
    if (sampleRate == 0) return;
    SampleReal fs = static_cast<SampleReal>(sampleRate);
    centerFreqHz = std::clamp(centerFreqHz, 10.0, fs * 0.49);
    bandwidthHz = std::clamp(bandwidthHz, 10.0, fs * 0.5);

    SampleReal q = centerFreqHz / bandwidthHz;
    q = std::clamp(q, 0.1, 50.0);

    SampleReal w0 = TWO_PI * centerFreqHz / fs;
    SampleReal sinw0 = std::sin(w0);
    SampleReal cosw0 = std::cos(w0);
    SampleReal alpha = sinw0 / (2.0 * q);

    SampleReal b0 = alpha;
    SampleReal b1 = 0.0;
    SampleReal b2 = -alpha;
    SampleReal a0 = 1.0 + alpha;
    SampleReal a1 = -2.0 * cosw0;
    SampleReal a2 = 1.0 - alpha;

    coeffs_.b0 = b0 / a0;
    coeffs_.b1 = b1 / a0;
    coeffs_.b2 = b2 / a0;
    coeffs_.a1 = a1 / a0;
    coeffs_.a2 = a2 / a0;
}

} // namespace vocalis::dsp
