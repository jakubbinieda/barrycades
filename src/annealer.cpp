#include "barrycades/annealer.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <vector>

namespace barrycades {
namespace {

// How often to re-read the clock and recompute the temperature
constexpr long long kRetuneMask = 2047;
constexpr int kCalibrationSamples = 20000;

}  // namespace

Annealer::Annealer(PrefixSumState& state, RNG& rng, const AnnealConfig& config)
    : state_(state), rng_(rng), config_(config), temp_start_(1.0), temp_end_(0.05) {
  calibrate();
  retune(temp_start_);
}

void Annealer::calibrate() {
  std::vector<int> uphill;
  uphill.reserve(kCalibrationSamples / 2);

  for (int k = 0; k < kCalibrationSamples; k++) {
    const Move m = state_.propose(rng_);
    const int delta = state_.apply(m);

    if (delta > 0) {
      uphill.push_back(delta);
    }

    state_.apply(m);
  }

  if (uphill.empty()) {
    return;
  }

  std::sort(uphill.begin(), uphill.end());
  const double hot_delta = uphill[static_cast<size_t>(uphill.size() * 0.85)];
  const double cold_delta = uphill[static_cast<size_t>(uphill.size() * 0.50)];

  temp_start_ = -hot_delta / std::log(config_.accept_hot);
  temp_end_ = -cold_delta / std::log(config_.accept_cold);

  if (temp_end_ >= temp_start_) {
    temp_end_ = temp_start_ * 0.02;
  }
}

void Annealer::retune(double temp) {
  for (int d = 0; d <= kMaxDelta; d++) {
    accept_[d] = std::exp(-d / temp);
  }
}

AnnealResult Annealer::run() {
  const double log_ratio = std::log(temp_end_ / temp_start_);
  const auto start = std::chrono::steady_clock::now();

  int best = state_.collisions();
  auto best_perms = state_.perms();

  long long iterations = 0;
  double elapsed = 0.0;

  while (true) {
    if ((iterations & kRetuneMask) == 0) {
      elapsed = std::chrono::duration<double>(std::chrono::steady_clock::now() - start).count();

      if (elapsed > config_.seconds) {
        break;
      }

      retune(temp_start_ * std::exp(log_ratio * (elapsed / config_.seconds)));
    }

    iterations++;

    const Move m = state_.propose(rng_);
    const int delta = state_.apply(m);

    const bool accept = (delta <= 0) || (delta <= kMaxDelta && rng_.unit() < accept_[delta]);
    if (!accept) {
      state_.apply(m);
      continue;
    }

    if (state_.collisions() < best) {
      best = state_.collisions();
      best_perms = state_.perms();
      if (best == 0) {
        break;
      }
    }
  }

  state_.reset_to(best_perms);

  return AnnealResult{best, iterations, elapsed};
}

}  // namespace barrycades
