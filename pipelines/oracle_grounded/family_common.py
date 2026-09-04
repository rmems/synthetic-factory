"""Shared vocabulary of the five dataset families.

The family modules agree on three things that must not drift apart: the
canonical family names, the measurement units they stamp into records, and the
tolerance under which a stored number is compared with a value derived from
other stored numbers. ``FamilySpec`` is the wiring record that binds one
family's generator, oracle builder, checks, and scorer together.
"""

from collections.abc import Callable
from dataclasses import dataclass

from . import canon

ENCODER_FAMILY = "spike-encoder-equivalence-pairs"
NEURON_FAMILY = "neuron-dynamics-counterfactuals"
MESH_FAMILY = "synaptic-delay-causal-trajectories"
CREDIT_FAMILY = "neuromodulator-credit-assignment"
MEMORY_FAMILY = "temporal-memory-spike-challenges"

FAMILY_NAMES = (
    ENCODER_FAMILY,
    NEURON_FAMILY,
    MESH_FAMILY,
    CREDIT_FAMILY,
    MEMORY_FAMILY,
)

# Stored records are rounded to canon.PRECISION decimals, so an arithmetic
# identity between three stored numbers can be off by a few ulps of that
# rounding. Anything this package actually measures is orders of magnitude
# larger, so the identity checks stay meaningful at this tolerance.
ROUNDING_TOL = 5 * 10**-canon.PRECISION

TIME_UNITS = "millisecond"
ENERGY_UNITS = "picojoule"
RATE_UNITS = "hertz"
DIMENSIONLESS = "dimensionless"


def _measurement_matches(actual, expected):
    """Compare a stored scalar with a value derived from stored measurements."""
    if actual is None or expected is None:
        return actual is expected
    if isinstance(actual, bool) or isinstance(expected, bool):
        return actual is expected
    if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
        return abs(actual - expected) <= ROUNDING_TOL
    return actual == expected


@dataclass(frozen=True)
class FamilySpec:
    """Everything the pipeline needs to know about one dataset family."""

    name: str
    runtimes: tuple
    oracle_type: str
    units: dict
    propose: Callable
    build_request: Callable
    build_oracle: Callable
    checks: Callable
    score: Callable

    def oracle(self, environ=None):
        return self.build_oracle(environ)


def _guess(record, key):
    candidate = record.get("candidate_prediction")
    if not isinstance(candidate, dict):
        return None
    return candidate.get(key)


def _stage_is_reference(record, suffix):
    """Whether the named chain stage was run by the in-repo reference.

    Anything other than an explicit named-runtime claim is treated as the
    reference implementation, so a malformed stage list keeps the reference
    reruns (fail closed) rather than skipping them.
    """
    for stage in record["oracle"].get("stages") or ():
        if isinstance(stage, dict) and str(stage.get("stage", "")).endswith(f":{suffix}"):
            return stage.get("implementation") != "named-runtime"
    return True
