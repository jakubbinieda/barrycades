#ifndef BARRYCADES_ANNEALER_HPP_
#define BARRYCADES_ANNEALER_HPP_

#include <cmath>

#include "barrycades/rng.hpp"
#include "barrycades/state.hpp"

namespace barrycades {

struct AnnealConfig {
  double seconds = 60.0;
  double accept_hot = 0.60;
  double accept_cold = 1e-9;
};

struct AnnealResult {
  int best_score;
  long long iterations;
  double elapsed;
};

class Annealer {
 public:
  Annealer(State& state, RNG& rng, const AnnealConfig& config);

  AnnealResult run();

  double temp_start() const { return temp_start_; }
  double temp_end() const { return temp_end_; }

 private:
  static constexpr int kMaxDelta = 24;

  State& state_;
  RNG& rng_;
  AnnealConfig config_;

  double temp_start_;
  double temp_end_;
  double temp_;
  double accept_[kMaxDelta + 1];

  double acceptance(int delta) const {
    return delta <= kMaxDelta ? accept_[delta] : std::exp(-delta / temp_);
  }

  void calibrate();
  void retune(double temp);
};

}  // namespace barrycades

#endif  // BARRYCADES_ANNEALER_HPP_
