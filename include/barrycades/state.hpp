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

class PrefixSumState {
 public:
  PrefixSumState(int n, int height, RNG& rng);

  int n() const { return n_; }
  int height() const { return height_; }
  int collisions() const { return collisions_; }

  const std::vector<std::vector<int>>& perms() const { return perms_; }

  void randomize(RNG& rng);
  Move propose(RNG& rng) const;
  int apply(const Move& m);
  void reset_to(const std::vector<std::vector<int>>& perms);
  bool verify() const;

 private:
  int n_;
  int height_;
  int max_sum_;

  std::vector<std::vector<int>> perms_;
  std::vector<std::vector<int>> pref_sums_;
  std::vector<uint16_t> sum_count_;
  int collisions_;

  void refresh(int p, int a, int b);
  void rebuild(int p);

  void bump(int sum) {
    if (sum_count_[sum]++ >= 1) collisions_++;
  }

  void drop(int sum) {
    if (--sum_count_[sum] >= 1) collisions_--;
  }
};

}  // namespace barrycades

#endif  // BARRYCADES_STATE_HPP_
