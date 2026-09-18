"""Shared contracts and constants for oracle-grounded family definitions."""

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


class FamilySpec:
    """Everything the pipeline needs to know about one dataset family."""

    def __init__(
        self,
        name,
        runtimes,
        oracle_type,
        units,
        propose,
        build_request,
        build_oracle,
        checks,
        score,
    ):
        self.name = name
        self.runtimes = tuple(runtimes)
        self.oracle_type = oracle_type
        self.units = units
        self.propose = propose
        self.build_request = build_request
        self._build_oracle = build_oracle
        self.checks = checks
        self.score = score

    def oracle(self, environ=None):
        return self._build_oracle(environ)

