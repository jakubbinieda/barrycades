#include <chrono>
#include <cstdlib>
#include <cstring>
#include <iomanip>
#include <iostream>
#include <vector>

#include "barrycades/annealer.hpp"
#include "barrycades/rng.hpp"
#include "barrycades/state.hpp"

namespace {

constexpr char kUsage[] =
    "usage: barrycades <corral|barrycade> <height> [seconds-per-restart] "
    "[max-restarts] [--balanced]\n";

void print_row(const std::vector<int>& row) {
  std::cout << '[';
  for (size_t j = 0; j < row.size(); j++) {
    if (j > 0) {
      std::cout << ", ";
    }
    std::cout << row[j];
  }
  std::cout << ']';
}

void print(const barrycades::State& state, const char* kind) {
  std::cout << kind << ":\n"
            << "  order: " << state.order() << '\n'
            << "  height: " << state.height() << '\n'
            << "  permutations:\n";
  for (const auto& row : state.perms()) {
    std::cout << "  - ";
    print_row(row);
    std::cout << '\n';
  }
  if (state.closed()) {
    std::cout << "  shifts: ";
    print_row(state.shifts());
    std::cout << '\n';
  }
}

}  // namespace

int main(int argc, char* argv[]) {
  bool balanced = false;
  std::vector<const char*> args;
  for (int i = 1; i < argc; i++) {
    if (std::strcmp(argv[i], "--balanced") == 0) {
      balanced = true;
    } else {
      args.push_back(argv[i]);
    }
  }

  if (args.empty()) {
    std::cerr << kUsage;
    return 2;
  }

  const char* kind = args[0];
  const bool closed = std::strcmp(kind, "corral") == 0;
  if (!closed && std::strcmp(kind, "barrycade") != 0) {
    std::cerr << kUsage;
    return 2;
  }

  if (args.size() < 2) {
    std::cerr << kUsage;
    return 2;
  }

  const int height = std::atoi(args[1]);
  barrycades::AnnealConfig config;
  int max_restarts = 100;

  if (args.size() >= 3) {
    config.seconds = std::atof(args[2]);
  }

  if (args.size() >= 4) {
    max_restarts = std::atoi(args[3]);
  }

  if (height < (closed ? 1 : 2)) {
    std::cerr << "height must be at least " << (closed ? 1 : 2) << "\n";
    return 2;
  }

  if (balanced && closed && height == 3) {
    std::cerr << "no balanced corral of height 3 exists (Nakamigawa)\n";
    return 2;
  }

  const int order = closed ? 2 * height - 1 : 2 * height - 2;

  const uint64_t seed = std::chrono::steady_clock::now().time_since_epoch().count();

  barrycades::RNG rng(seed);
  barrycades::State state(order, height, closed, balanced, rng);

  if (order < 2) {
    print(state, kind);
    return 0;
  }

  std::cerr << kind << ", height = " << height << ", order = " << order
            << (balanced ? ", balanced, " : ", ") << config.seconds << "s x " << max_restarts
            << " restarts\n";

  for (int attempt = 1; attempt <= max_restarts; attempt++) {
    if (attempt > 1) {
      state.randomize(rng);
    }

    barrycades::Annealer annealer(state, rng, config);

    std::cerr << "\nAttempt " << attempt << ":\n"
              << "Initial score: " << state.score() << ", T " << std::fixed
              << std::setprecision(3) << annealer.temp_start() << " -> " << annealer.temp_end()
              << "\n";

    const barrycades::AnnealResult result = annealer.run();

    std::cerr << "Iterations: " << result.iterations << " (" << std::setprecision(2)
              << result.iterations / result.elapsed / 1e6
              << "M/s), best: " << state.collisions() << " collisions";
    if (balanced) {
      std::cerr << ", " << state.imbalance() << " unbalanced";
    }
    std::cerr << "\n";

    if (result.best_score == 0) {
      std::cerr << "\n";
      print(state, kind);
      return 0;
    }
  }

  std::cerr << "\nNo solution found.\n";
  return 1;
}
