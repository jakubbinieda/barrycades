#include "barrycades/state.hpp"

#include <algorithm>
#include <numeric>
#include <set>

namespace barrycades {
namespace {

constexpr int kMaxSpan = 4;
constexpr int kReversePercent = 30;

}  // namespace

PrefixSumState::PrefixSumState(int n, int height, RNG& rng)
    : n_(n),
      height_(height),
      max_sum_(n * (n + 1) / 2 - 1),
      perms_(height, std::vector<int>(n)),
      pref_sums_(height, std::vector<int>(n - 1)),
      sum_count_(max_sum_ + 1, 0),
      collisions_(0) {
  randomize(rng);
}

void PrefixSumState::refresh(int p, int a, int b) {
  const int limit = std::min(b, n_ - 1);
  for (int j = a; j < limit; j++) {
    drop(pref_sums_[p][j]);
  }

  int sum = (a > 0) ? pref_sums_[p][a - 1] : 0;
  for (int j = a; j < limit; j++) {
    sum += perms_[p][j];
    pref_sums_[p][j] = sum;
    bump(sum);
  }
}

void PrefixSumState::rebuild(int p) {
  int sum = 0;
  for (int j = 0; j < n_ - 1; j++) {
    sum += perms_[p][j];
    pref_sums_[p][j] = sum;
    bump(sum);
  }
}

void PrefixSumState::randomize(RNG& rng) {
  std::fill(sum_count_.begin(), sum_count_.end(), 0);
  collisions_ = 0;

  for (int i = 0; i < height_; i++) {
    std::iota(perms_[i].begin(), perms_[i].end(), 1);
    for (int j = n_ - 1; j > 0; j--) {
      std::swap(perms_[i][j], perms_[i][rng.below(j + 1)]);
    }
    rebuild(i);
  }
}

void PrefixSumState::reset_to(const std::vector<std::vector<int>>& perms) {
  perms_ = perms;
  std::fill(sum_count_.begin(), sum_count_.end(), 0);
  collisions_ = 0;
  for (int i = 0; i < height_; i++) {
    rebuild(i);
  }
}

Move PrefixSumState::propose(RNG& rng) const {
  Move m;
  m.row = static_cast<int>(rng.below(height_));
  m.a = static_cast<int>(rng.below(n_ - 1));

  const int room = n_ - 1 - m.a;
  const int cap = std::min(room, 1 + static_cast<int>(rng.below(kMaxSpan)));
  m.b = m.a + 1 + static_cast<int>(rng.below(cap));

  m.reverse = static_cast<int>(rng.below(100)) < kReversePercent;
  return m;
}

int PrefixSumState::apply(const Move& m) {
  const int before = collisions_;

  auto& row = perms_[m.row];
  if (m.reverse) {
    std::reverse(row.begin() + m.a, row.begin() + m.b + 1);
  } else {
    std::swap(row[m.a], row[m.b]);
  }

  refresh(m.row, m.a, m.b);

  return collisions_ - before;
}

bool PrefixSumState::verify() const {
  std::set<int> seen;

  for (int i = 0; i < height_; i++) {
    std::vector<int> sorted = perms_[i];
    std::sort(sorted.begin(), sorted.end());

    for (int j = 0; j < n_; j++) {
      if (sorted[j] != j + 1) return false;
    }

    int sum = 0;
    for (int j = 0; j < n_ - 1; j++) {
      sum += perms_[i][j];
      if (!seen.insert(sum).second) {
        return false;
      }
    }
  }

  return true;
}

}  // namespace barrycades
