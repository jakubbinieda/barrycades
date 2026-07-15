#include <chrono>
#include <cstdlib>
#include <iomanip>
#include <iostream>

#include "barrycades/annealer.hpp"
#include "barrycades/rng.hpp"
#include "barrycades/state.hpp"

namespace {

void print(const barrycades::PrefixSumState& state) {
  for (const auto& row : state.perms()) {
    for (size_t j = 0; j < row.size(); j++) {
      std::cout << row[j] << (j + 1 == row.size() ? '\n' : ' ');
    }
  }
}

}  // namespace

// usage: barrycades <n> [seconds-per-restart] [max-restarts]
// n is also read from stdin when no arguments are given.
int main(int argc, char* argv[]) {
  int n = 0;
  barrycades::AnnealConfig config;
  int max_restarts = 100;

  if (argc >= 2) {
    n = std::atoi(argv[1]);
  } else if (!(std::cin >> n)) {
    std::cerr << "usage: barrycades <n> [seconds-per-restart] [max-restarts]\n";
    return 2;
  }

  if (argc >= 3) {
    config.seconds = std::atof(argv[2]);
  }

  if (argc >= 4) {
    max_restarts = std::atoi(argv[3]);
  }

  if (n < 2) {
    std::cerr << "n must be at least 2\n";
    return 2;
  }

  const int height = n / 2 + 1;
  const uint64_t seed = std::chrono::steady_clock::now().time_since_epoch().count();

  barrycades::RNG rng(seed);
  barrycades::PrefixSumState state(n, height, rng);

  std::cerr << "n = " << n << ", height = " << height << ", " << config.seconds << "s x "
            << max_restarts << " restarts\n";

  for (int attempt = 1; attempt <= max_restarts; attempt++) {
    if (attempt > 1) {
      state.randomize(rng);
    }

    barrycades::Annealer annealer(state, rng, config);

    std::cerr << "\nAttempt " << attempt << ":\n"
              << "Initial collisions: " << state.collisions() << ", T " << std::fixed
              << std::setprecision(3) << annealer.temp_start() << " -> " << annealer.temp_end()
              << "\n";

    const barrycades::AnnealResult result = annealer.run();

    std::cerr << "Iterations: " << result.iterations << " (" << std::setprecision(2)
              << result.iterations / result.elapsed / 1e6
              << "M/s), best collisions: " << result.best_collisions << "\n";

    if (result.best_collisions == 0 && state.verify()) {
      print(state);
      std::cerr << "\nSolution verified!\n";
      return 0;
    }
  }

  std::cerr << "\nNo solution found.\n";
  return 1;
}
