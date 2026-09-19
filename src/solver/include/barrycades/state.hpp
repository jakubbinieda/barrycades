#ifndef BARRYCADES_STATE_HPP_
#define BARRYCADES_STATE_HPP_

#include <cstdint>
#include <vector>

#include "barrycades/rng.hpp"

namespace barrycades {

struct Move {
  int row;
  int a;
  int b;  // a < b
  bool reverse;
};

class State {
 public:
  State(int order, int height, bool closed, bool balanced, RNG& rng);

  int order() const { return order_; }
  int height() const { return height_; }
  int width() const { return width_; }
  bool closed() const { return closed_; }
  int collisions() const { return collisions_; }
  int imbalance() const { return imbalance_; }
  int score() const { return collisions_ + imbalance_; }

  const std::vector<std::vector<int>>& perms() const { return perms_; }
  const std::vector<int>& shifts() const { return shifts_; }

  using Snapshot = std::vector<std::vector<int>>;

  void randomize(RNG& rng);
  Move propose(RNG& rng) const;
  int apply(const Move& m);
  Snapshot snapshot() const { return perms_; }
  void restore(const Snapshot& perms);

 private:
  int order_;
  int height_;
  int width_;
  bool closed_;
  bool balanced_;
  int counted_;  // joints per row: order_ when closed, order_ - 1 otherwise

  std::vector<std::vector<int>> perms_;
  std::vector<int> shifts_;
  std::vector<std::vector<int>> sums_;
  std::vector<uint16_t> sum_count_;
  std::vector<uint16_t> block_count_;  // per row, how many sums fall in a block
  int collisions_;
  int imbalance_;

  void refresh(int p, int a, int b);
  void rebuild(int p);
  void reset();

  int block(int sum) const { return (closed_ ? sum : sum - 1) / height_; }

  void bump(int p, int sum) {
    collisions_ += sum_count_[sum]++;
    if (balanced_) imbalance_ += block_count_[p * counted_ + block(sum)]++;
  }

  void drop(int p, int sum) {
    collisions_ -= --sum_count_[sum];
    if (balanced_) imbalance_ -= --block_count_[p * counted_ + block(sum)];
  }
};

}  // namespace barrycades

#endif  // BARRYCADES_STATE_HPP_
