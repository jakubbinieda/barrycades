#include "barrycades/state.hpp"

#include <algorithm>
#include <numeric>
#include <set>

namespace barrycades {
namespace {

constexpr int kMaxSpan = 4;
constexpr int kReversePercent = 30;
constexpr int kLongPercent = 10;

}  // namespace

State::State(int order, int height, bool closed, bool balanced, RNG& rng)
    : order_(order),
      height_(height),
      width_(order * (order + 1) / 2),
      closed_(closed),
      balanced_(balanced),
      counted_(closed ? order : order - 1),
      perms_(height, std::vector<int>(order)),
      shifts_(height, 0),
      sums_(height, std::vector<int>(counted_)),
      sum_count_(width_, 0),
      block_count_(balanced ? height * counted_ : 0, 0),
      collisions_(0),
      imbalance_(0) {
  if (closed_) {
    for (int i = 0; i < height_; i++) {
      shifts_[i] = i % width_;
    }
  }
  randomize(rng);
}

void State::refresh(int p, int a, int b) {
  const int limit = std::min(b, counted_);
  for (int j = a; j < limit; j++) {
    drop(p, sums_[p][j]);
  }

  int sum = (a > 0) ? sums_[p][a - 1] : shifts_[p];
  for (int j = a; j < limit; j++) {
    sum += perms_[p][j];
    if (sum >= width_) sum -= width_;
    sums_[p][j] = sum;
    bump(p, sum);
  }
}

void State::rebuild(int p) {
  int sum = shifts_[p];
  for (int j = 0; j < counted_; j++) {
    sum += perms_[p][j];
    if (sum >= width_) sum -= width_;
    sums_[p][j] = sum;
    bump(p, sum);
  }
}

void State::reset() {
  std::fill(sum_count_.begin(), sum_count_.end(), 0);
  std::fill(block_count_.begin(), block_count_.end(), 0);
  collisions_ = 0;
  imbalance_ = 0;
}

void State::randomize(RNG& rng) {
  reset();

  for (int i = 0; i < height_; i++) {
    std::iota(perms_[i].begin(), perms_[i].end(), 1);
    for (int j = order_ - 1; j > 0; j--) {
      std::swap(perms_[i][j], perms_[i][rng.below(j + 1)]);
    }
    rebuild(i);
  }
}

void State::restore(const Snapshot& perms) {
  perms_ = perms;
  reset();
  for (int i = 0; i < height_; i++) {
    rebuild(i);
  }
}

Move State::propose(RNG& rng) const {
  Move m;
  m.row = static_cast<int>(rng.below(height_));
  m.a = static_cast<int>(rng.below(order_ - 1));

  const int room = order_ - 1 - m.a;
  const int span = (static_cast<int>(rng.below(100)) < kLongPercent)
                       ? room
                       : std::min(room, kMaxSpan);
  m.b = m.a + 1 + static_cast<int>(rng.below(span));

  m.reverse = static_cast<int>(rng.below(100)) < kReversePercent;
  return m;
}

int State::apply(const Move& m) {
  const int before = score();

  auto& row = perms_[m.row];
  if (m.reverse) {
    std::reverse(row.begin() + m.a, row.begin() + m.b + 1);
  } else {
    std::swap(row[m.a], row[m.b]);
  }

  refresh(m.row, m.a, m.b);

  return score() - before;
}

}  // namespace barrycades
