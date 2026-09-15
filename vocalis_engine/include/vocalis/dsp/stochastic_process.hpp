#pragma once

#include "vocalis/types.hpp"
#include "vocalis/dsp/noise_generator.hpp"
#include <cmath>
#include <algorithm>

namespace vocalis::dsp {

/// @brief Ornstein-Uhlenbeck (OU) Mean-Reverting Stochastic Differential Equation (SDE):
/// dx(t) = theta * (mu(t) - x(t)) dt + sigma * dW(t)
/// Used for continuous neuromuscular articulatory drift (F1..F5) and pitch micro-intonation (F0).
class OrnsteinUhlenbeckProcess {
public:
    constexpr OrnsteinUhlenbeckProcess(SampleReal theta = 30.0, SampleReal sigma = 10.0, SampleReal initialVal = 0.0) noexcept
        : theta_(theta), sigma_(sigma), state_(initialVal) {}

    void setParams(SampleReal theta, SampleReal sigma) noexcept {
        theta_ = std::max(0.1, theta);
        sigma_ = std::max(0.0, sigma);
    }

    void reset(SampleReal val = 0.0) noexcept {
        state_ = val;
    }

    /// @brief Advances SDE by dt towards nominal target mu with Gaussian Wiener increment dW
    SampleReal step(SampleReal target, SampleReal dt, NoiseGenerator& rng) noexcept {
        if (dt <= 0.0) return state_;
        
        // Exact discrete solution for Ornstein-Uhlenbeck process:
        // x(t+dt) = mu + (x(t) - mu) * exp(-theta * dt) + sigma * sqrt((1 - exp(-2*theta*dt)) / (2*theta)) * Z
        SampleReal decay = std::exp(-theta_ * dt);
        SampleReal varianceFactor = std::sqrt(std::max(0.0, (1.0 - decay * decay) / (2.0 * theta_)));
        SampleReal noiseIncrement = sigma_ * varianceFactor * static_cast<SampleReal>(rng.nextGaussian() * 3.333); // unit stddev
        
        state_ = target + (state_ - target) * decay + noiseIncrement;
        return state_;
    }

    [[nodiscard]] SampleReal state() const noexcept { return state_; }

private:
    SampleReal theta_{30.0};  // Mean-reversion stiffness rate (s^-1)
    SampleReal sigma_{10.0};  // Volatility / biological diffusion coefficient
    SampleReal state_{0.0};   // Instantaneous state value
};

/// @brief Discrete Autoregressive AR(1) Brownian Pink Drift Generator:
/// y[k] = rho * y[k-1] + sqrt(1 - rho^2) * sigma_w * Z_k
/// Generates correlated 1/f noise for cycle-by-cycle glottal pulse morphing (Oq, Sq, shimmer).
class AutoregressiveDrift {
public:
    constexpr explicit AutoregressiveDrift(SampleReal rho = 0.85, SampleReal stdDev = 0.02) noexcept
        : rho_(rho), stdDev_(stdDev), state_(0.0) {}

    void setParams(SampleReal rho, SampleReal stdDev) noexcept {
        rho_ = std::clamp(rho, -0.999, 0.999);
        stdDev_ = std::max(0.0, stdDev);
    }

    void reset(SampleReal val = 0.0) noexcept {
        state_ = val;
    }

    SampleReal step(NoiseGenerator& rng) noexcept {
        SampleReal innovation = static_cast<SampleReal>(rng.nextGaussian() * 3.333);
        SampleReal scale = std::sqrt(std::max(0.0, 1.0 - rho_ * rho_)) * stdDev_;
        state_ = rho_ * state_ + scale * innovation;
        return state_;
    }

    [[nodiscard]] SampleReal state() const noexcept { return state_; }

private:
    SampleReal rho_{0.85};
    SampleReal stdDev_{0.02};
    SampleReal state_{0.0};
};

/// @brief Probabilistic Log-Normal Duration Perturbation:
/// D = meanDur * exp(sigma_dur * Z)
class LogNormalSampler {
public:
    static SampleReal sample(SampleReal meanDur, SampleReal sigmaLog, NoiseGenerator& rng) noexcept {
        if (sigmaLog <= 1e-6 || meanDur <= 0.0) return meanDur;
        SampleReal z = static_cast<SampleReal>(rng.nextGaussian() * 3.333);
        // Clamp perturbation to prevent extreme timing collapse
        SampleReal factor = std::clamp(std::exp(sigmaLog * z), 0.75, 1.35);
        return meanDur * factor;
    }
};

} // namespace vocalis::dsp
