"""Shared generator identity for oracle-grounded proposals."""

GENERATOR_NAME = "deterministic-scenario-generator"
GENERATOR_VERSION = "1.0.0"
SIGNAL_FAMILIES = ("baseline", "burst", "drift", "outlier", "periodic", "sparse_events")
PERTURBATIONS = ("none", "additive_noise", "dropout", "quantization", "gain_drift")


def generator_block(seed, label, model=None):
    """The provenance block for whoever proposed the scenario."""
    return {
        "name": model or GENERATOR_NAME,
        "version": GENERATOR_VERSION,
        "role": "proposes scenarios, interventions, and non-authoritative predictions",
        "authoritative": False,
        "seed": int(seed),
        "label": label,
    }
