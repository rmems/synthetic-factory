#!/usr/bin/env python3
"""The shared seeded draw stream: SHA-256 over ``"{seed}:{counter}"``.

Lifted from the fault-recovery family (F1 of #191) so every family under the
contract -- the neuromorphic simulators and the software lane's code-repair
generator alike -- draws from one primitive instead of a second copy or the
``random`` module. Every draw consumes one counter step and takes 64 bits of
the digest, so the same seed yields the same draws on every platform and
Python version, independent of any pseudo-random library's generator or its
selection internals. Seeds are genuine integers in ``[0, MAX_SEED]``; anything
else is refused with a :class:`envelope.ContractError` before a stream exists,
so no two accepted seeds share a stream and a seed is always one unambiguous
integer the stream can format. Families that own coded refusals wrap
:func:`check_seed` with their own codes (``fault_scenario.DrawStream``).

A second primitive, :class:`Rng`, follows it: SplitMix64, serving the float
draws (``random``, ``uniform``, ``symmetric_noise``) that :class:`DrawStream`
does not. The oracle-grounded scenario generators of #77 draw from it, and its
stream sits under every measured byte those families publish, so it stays a
distinct primitive here rather than being converged onto :class:`DrawStream`:
that conversion moves every measurement, not just a digest, and is its own
reviewed change.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from typing import Any, TypeVar

from . import distill_vocabulary as vocab
from . import envelope
from .import_twins import bind_import_twin

T = TypeVar("T")

# The seed domain: one 64-bit non-negative integer. ``random.Random(-n)`` and
# ``random.Random(n)`` share a state; this stream refuses the negative half.
MAX_SEED = 2**64 - 1

__all__ = ["MASK64", "MAX_SEED", "DrawStream", "Rng", "check_seed", "seed_from_label"]


def check_seed(seed: Any) -> None:
    """Refuse anything but a genuine integer in ``[0, MAX_SEED]``.

    The message never formats the offending value: a seed can be an integer
    too wide for ``repr`` to print, and a refusal must not raise a second,
    uncoded error on the way out.
    """

    if not vocab.is_genuine_int(seed):
        raise envelope.ContractError("seed must be a genuine integer (bool is refused)")
    if not 0 <= seed <= MAX_SEED:
        raise envelope.ContractError(f"seed must lie in [0, {MAX_SEED}] (a 64-bit integer)")


class DrawStream:
    """A deterministic draw stream: SHA-256 over ``"{seed}:{counter}"``, 64 bits per draw."""

    def __init__(self, seed: int) -> None:
        check_seed(seed)
        self._seed = seed
        self._counter = 0

    @property
    def seed(self) -> int:
        return self._seed

    @property
    def draws(self) -> int:
        """How many draws the stream has served so far."""
        return self._counter

    def bits(self) -> int:
        """The next 64-bit draw."""
        self._counter += 1
        digest = hashlib.sha256(f"{self._seed}:{self._counter}".encode("ascii")).digest()
        return int.from_bytes(digest[:8], "big")

    def choice(self, options: Sequence[T]) -> T:
        return options[self.bits() % len(options)]

    def randint(self, low: int, high: int) -> int:
        """An integer in ``[low, high]``."""
        return low + self.bits() % (high - low + 1)

    def sample(self, population: Sequence[T], count: int) -> list[T]:
        """``count`` distinct members, in draw order."""
        pool = list(population)
        return [pool.pop(self.bits() % len(pool)) for _ in range(count)]

    def chance(self, probability: float) -> bool:
        """True with the given probability."""
        return self.bits() < probability * 2**64


# --- SplitMix64: the oracle-grounded scenario stream (#77) -------------------
#
# `random.Random` is stable in practice but its stream is an implementation
# detail of CPython. Oracle-grounded records must be byte-reproducible from a
# seed on any interpreter, so this is SplitMix64 written out explicitly:
# 64-bit integer arithmetic only, no floating-point state, no global state.

MASK64 = (1 << 64) - 1
_GAMMA = 0x9E3779B97F4A7C15
_MIX_A = 0xBF58476D1CE4E5B9
_MIX_B = 0x94D049BB133111EB
_FNV_OFFSET = 0xCBF29CE484222325
_FNV_PRIME = 0x100000001B3


def seed_from_label(seed, label):
    """Derive a stable 64-bit sub-seed from an integer seed and a text label."""
    check_seed(seed)
    digest = _FNV_OFFSET
    for byte in str(label).encode("utf-8"):
        digest = ((digest ^ byte) * _FNV_PRIME) & MASK64
    return (digest ^ seed) & MASK64


class Rng:
    """SplitMix64. Identical stream on every platform and Python version."""

    __slots__ = ("_state",)

    def __init__(self, seed):
        check_seed(seed)
        self._state = seed

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


bind_import_twin(__name__)
