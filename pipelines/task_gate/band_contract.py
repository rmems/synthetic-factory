#!/usr/bin/env python3
"""The experiment contract the band is read from: attempts per task and the pass-rate bounds.

Nothing here has a default. A missing, unreadable, oversized or malformed contract refuses the
run, so the bounds can never silently become "keep everything". The band is the closed
interval ``[pass_rate_min, pass_rate_max]`` with ``0 < min <= max < 1``: a task the student
always solves or never solves is outside the band by construction. Bounds are compared as
exact fractions, so ``successes/attempts == 0.1`` sits on the edge it names.
"""

from __future__ import annotations

import hashlib
import os
import stat
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

from . import band_vocabulary as bv
from . import vocabulary as cv
from ._contract import bind_import_twin, load_strict_json
from .checks import is_int

__all__ = ["BandContract", "load_contract"]

_KEYS = frozenset({"format", "attempts_per_task", "pass_rate_min", "pass_rate_max"})


@dataclass(frozen=True)
class BandContract:
    """The validated contract and the digest of the bytes it was read from."""

    attempts_per_task: int
    pass_rate_min: Fraction
    pass_rate_max: Fraction
    sha256: str

    def classify(self, successes: int, attempts: int) -> str:
        """The band verdict for ``successes`` out of ``attempts`` solver attempts."""

        rate = Fraction(successes, attempts)
        if successes == 0:
            return bv.BAND_SEED_NEEDED
        if rate < self.pass_rate_min:
            return bv.BAND_TOO_HARD
        return bv.BAND_TOO_EASY if rate > self.pass_rate_max else bv.BAND_KEPT


def _malformed(detail: str) -> cv.GateRefusal:
    return cv.GateRefusal(bv.REFUSE_CONTRACT_MALFORMED, detail)


def _bound(value: object, name: str) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise _malformed(f"{name} must be a JSON number")
    bound = Fraction(str(value))
    if not 0 < bound < 1:
        raise _malformed(f"{name} must lie strictly between 0 and 1")
    return bound


def _shape(document: object) -> dict:
    if not isinstance(document, dict) or set(document) != _KEYS:
        raise _malformed(f"contract must be an object with exactly {sorted(_KEYS)}")
    if document["format"] != bv.CONTRACT_FORMAT:
        raise _malformed(f"format must be {bv.CONTRACT_FORMAT}")
    return document


def _attempts(value: object) -> int:
    if not is_int(value) or not bv.MIN_ATTEMPTS <= value <= bv.MAX_ATTEMPTS:
        raise _malformed(f"attempts_per_task must be an integer in [{bv.MIN_ATTEMPTS}, {bv.MAX_ATTEMPTS}]")
    return value


def _validated(document: object, digest: str) -> BandContract:
    fields = _shape(document)
    attempts = _attempts(fields["attempts_per_task"])
    low, high = _bound(fields["pass_rate_min"], "pass_rate_min"), _bound(fields["pass_rate_max"], "pass_rate_max")
    if low > high:
        raise _malformed("pass_rate_min exceeds pass_rate_max")
    return BandContract(attempts, low, high, digest)


def _regular_file_head(path: Path | str) -> bytes:
    """Up to one byte past the size cap from ``path``, which must be a regular file."""

    try:
        if not stat.S_ISREG(os.stat(path).st_mode):
            raise cv.GateRefusal(bv.REFUSE_CONTRACT_MISSING, f"{path} is not a regular file")
        with Path(path).open("rb") as handle:
            return handle.read(bv.MAX_CONTRACT_BYTES + 1)
    except OSError as exc:
        raise cv.GateRefusal(bv.REFUSE_CONTRACT_MISSING, f"{path}: {exc}") from exc


def _read(path: Path | str | None) -> bytes:
    if path is None:
        raise cv.GateRefusal(bv.REFUSE_CONTRACT_MISSING, "the band needs an experiment contract")
    data = _regular_file_head(path)
    if len(data) > bv.MAX_CONTRACT_BYTES:
        raise _malformed(f"{path} is too large")
    return data


def load_contract(path: Path | str | None) -> BandContract:
    """Read and validate the contract; every defect is a coded refusal."""

    data = _read(path)
    try:
        document = load_strict_json(data.decode("utf-8"))
    except (ValueError, RecursionError) as exc:
        raise _malformed(f"{path}: {exc}") from exc
    return _validated(document, hashlib.sha256(data).hexdigest())


bind_import_twin(__name__)
