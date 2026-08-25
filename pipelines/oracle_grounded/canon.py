"""Canonical JSON, float normalisation, and content hashing.

Two records that mean the same thing must hash the same, and a record must
hash the same after a JSON round trip. That requires (a) sorted keys and no
insignificant whitespace, (b) a fixed float precision so `0.1 + 0.2` and `0.3`
do not disagree in the eleventh decimal, and (c) a hard refusal of NaN/Inf,
which JSON cannot represent and which would silently poison a golden fixture.
"""

import hashlib
import json
import math
import os
from pathlib import Path

# Six decimals is finer than any measurement this package emits (times are in
# milliseconds, currents and voltages are order 1) and coarse enough that
# double-precision reassociation does not change the digest.
PRECISION = 6
HASH_PREFIX = "sha256:"


class NonFiniteNumber(ValueError):
    """A float that JSON cannot carry reached the canonicaliser."""


def normalize(value, precision=PRECISION):
    """Recursively round floats and normalise -0.0, rejecting NaN/Inf.

    Dict keys are left alone (they are always strings in these records) but
    are emitted sorted by ``canonical_json``.
    """
    if isinstance(value, bool) or value is None or isinstance(value, (str, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise NonFiniteNumber(f"non-finite number in record: {value!r}")
        rounded = round(value, precision)
        # round() can return -0.0; JSON keeps the sign and breaks equality.
        if rounded == 0.0:
            return 0.0
        return rounded
    if isinstance(value, dict):
        return {str(key): normalize(item, precision) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [normalize(item, precision) for item in value]
    raise TypeError(f"unsupported type in record: {type(value).__name__}")


def canonical_json(value, precision=PRECISION):
    """Deterministic JSON text: normalised floats, sorted keys, no padding."""
    return json.dumps(
        normalize(value, precision),
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
        ensure_ascii=True,
    )


def digest(value, precision=PRECISION):
    """``sha256:<hex>`` over the canonical JSON of ``value``."""
    payload = canonical_json(value, precision).encode("utf-8")
    return HASH_PREFIX + hashlib.sha256(payload).hexdigest()


def digest_files(paths):
    """``sha256:<hex>`` over a set of source files, order-independent.

    Used for ``oracle.module_digest``: the identity of the code that produced
    a measurement, independent of whether the tree happens to be committed or
    where the checkout lives. Source names are made relative to their common
    directory before hashing, so identical trees have identical digests.
    """
    resolved = [Path(item).resolve() for item in paths]
    if not resolved:
        return HASH_PREFIX + hashlib.sha256().hexdigest()
    common_parent = Path(os.path.commonpath([str(path.parent) for path in resolved]))
    named_paths = sorted(
        ((path.relative_to(common_parent).as_posix(), path) for path in resolved),
        key=lambda item: item[0],
    )
    accumulator = hashlib.sha256()
    for source_name, path in named_paths:
        with open(path, "rb") as handle:
            body = handle.read()
        accumulator.update(source_name.encode("utf-8"))
        accumulator.update(b"\0")
        accumulator.update(hashlib.sha256(body).hexdigest().encode("ascii"))
        accumulator.update(b"\n")
    return HASH_PREFIX + accumulator.hexdigest()


def dumps_record(record, precision=PRECISION):
    """One JSONL line: readable key order is not preserved, determinism is."""
    return canonical_json(record, precision)


def is_digest(value):
    return (
        isinstance(value, str)
        and value.startswith(HASH_PREFIX)
        and len(value) == len(HASH_PREFIX) + 64
        and all(char in "0123456789abcdef" for char in value[len(HASH_PREFIX):])
    )
