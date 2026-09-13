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

__all__ = ["MAX_SEED", "DrawStream", "check_seed"]


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


bind_import_twin(__name__)
