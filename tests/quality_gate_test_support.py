"""Shared fixtures for the split quality-gate test modules."""

from gate_fixtures import REPO

EMBEDDING_FIXTURE = REPO / "tests" / "fixtures" / "embedding-dedup"

# Distinct enough that no pair is a near-duplicate, so a mix test blocks on the
# mix and nothing else.
DISTINCT_NOTES = [
    "the harbour crane lost hoist encoder agreement under a loaded spreader",
    "chlorine residual fell at the far zone sample point during full duty",
    "a feeder breaker tripped on instantaneous overcurrent mid reclose",
    "the vaccine freezer bank drifted upward after a defrost heater stuck",
    "turbine pitch bearing grease pressure spiked under yaw misalignment",
    "the milking robot logged a partial rinse against standing procedure",
]


def mix_records(synthetic, real):
    """Return distinct designed and unknown records for mix-policy tests."""
    kinds = ["designed"] * synthetic + ["unknown"] * real
    return [
        {"id": f"m-{index}", "state": {"sim_or_real": kind, "note": DISTINCT_NOTES[index]}}
        for index, kind in enumerate(kinds)
    ]
