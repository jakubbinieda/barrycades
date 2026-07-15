#ifndef BARRYCADES_ANNEALER_HPP_
#define BARRYCADES_ANNEALER_HPP_

#include "barrycades/rng.hpp"
#include "barrycades/state.hpp"

namespace barrycades {

struct AnnealConfig {
  double seconds = 60.0;
  double accept_hot = 0.60;
  double accept_cold = 1e-9;
};

struct AnnealResult {
  int best_collisions;
  long long iterations;
  double elapsed;
};

class Annealer {
 public:
  Annealer(PrefixSumState& state, RNG& rng, const AnnealConfig& config);

  AnnealResult run();

  double temp_start() const { return temp_start_; }
  double temp_end() const { return temp_end_; }

 private:
  static constexpr int kMaxDelta = 24;

  PrefixSumState& state_;
  RNG& rng_;
  AnnealConfig config_;

  double temp_start_;
  double temp_end_;
  double accept_[kMaxDelta + 1];

  void calibrate();
  void retune(double temp);
};

}  // namespace barrycades

#endif  // BARRYCADES_ANNEALER_HPP_
