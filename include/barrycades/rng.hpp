
#ifndef BARRYCADES_RNG_HPP_
#define BARRYCADES_RNG_HPP_

#include <cstdint>

namespace barrycades {

// Xorshift64
class RNG {
 public:
  explicit RNG(uint64_t seed) : state_(seed ? seed : 0x9e3779b97f4a7c15ULL) {}

  uint64_t next() {
    state_ ^= state_ << 13;
    state_ ^= state_ >> 7;
    state_ ^= state_ << 17;
    return state_;
  }

  // Uniform in [0, n)
  uint32_t below(uint32_t n) {
    return static_cast<uint32_t>((static_cast<uint64_t>(static_cast<uint32_t>(next())) * n) >> 32);
  }

  // Uniform in [0, 1)
  double unit() { return (next() & ((1ULL << 53) - 1)) * (1.0 / (1ULL << 53)); }

 private:
  uint64_t state_;
};

}  // namespace barrycades

#endif  // BARRYCADES_RNG_HPP_
