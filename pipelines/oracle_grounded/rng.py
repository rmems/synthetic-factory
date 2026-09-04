"""Deterministic RNG for scenario generation.

`random.Random` is stable in practice but its stream is an implementation
detail of CPython. Oracle-grounded records must be byte-reproducible from a
seed on any interpreter, so this module implements SplitMix64 explicitly:
64-bit integer arithmetic only, no floating-point state, no global state.
"""

MASK64 = (1 << 64) - 1
_GAMMA = 0x9E3779B97F4A7C15
_MIX_A = 0xBF58476D1CE4E5B9
_MIX_B = 0x94D049BB133111EB
_FNV_OFFSET = 0xCBF29CE484222325
_FNV_PRIME = 0x100000001B3


def seed_from_label(seed, label):
    """Derive a stable 64-bit sub-seed from an integer seed and a text label."""
    digest = _FNV_OFFSET
    for byte in str(label).encode("utf-8"):
        digest = ((digest ^ byte) * _FNV_PRIME) & MASK64
    return (digest ^ (int(seed) & MASK64)) & MASK64


class Rng:
    """SplitMix64. Identical stream on every platform and Python version."""

    __slots__ = ("_state",)

    def __init__(self, seed):
        self._state = int(seed) & MASK64

    def derive(self, label):
        """A fresh independent stream, stable for this (seed, label) pair."""
        return Rng(seed_from_label(self._state, label))

    def next_u64(self):
        self._state = (self._state + _GAMMA) & MASK64
        z = self._state
        z = ((z ^ (z >> 30)) * _MIX_A) & MASK64
        z = ((z ^ (z >> 27)) * _MIX_B) & MASK64
        return (z ^ (z >> 31)) & MASK64

    def random(self):
        """Uniform float in [0, 1) built from 53 mantissa bits."""
        return (self.next_u64() >> 11) * (2.0**-53)

    def uniform(self, low, high):
        return low + (high - low) * self.random()

    def randint(self, low, high):
        """Inclusive on both ends; ``low`` must not exceed ``high``."""
        if high < low:
            raise ValueError(f"randint range is empty: [{low}, {high}]")
        span = high - low + 1
        return low + int(self.next_u64() % span)

    def choice(self, seq):
        items = list(seq)
        if not items:
            raise ValueError("choice from an empty sequence")
        return items[self.randint(0, len(items) - 1)]

    def sample(self, seq, count):
        """``count`` distinct items, order stable for a given stream."""
        items = list(seq)
        if count > len(items):
            raise ValueError(f"cannot sample {count} of {len(items)}")
        picked = []
        for _ in range(count):
            index = self.randint(0, len(items) - 1)
            picked.append(items.pop(index))
        return picked

    def symmetric_noise(self):
        """Zero-mean noise in (-1, 1) from two uniforms (triangular)."""
        return self.random() + self.random() - 1.0
