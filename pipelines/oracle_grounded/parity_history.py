"""Explicitly reviewed historical source/catalog identities for current replay.

The snapshots below were independently recomputed from Git source blobs at the
two reviewed commits. The first immutable fixture bytes live under
tests/fixtures/parity-history/0bbeb5e6; the second differs only in source stamps.
Both byte representations are pinned by raw SHA-256 in the tests.
Only provenance stamp comparison uses these values. Every current envelope,
scenario, measurement, availability, and complete-catalog check still runs.
"""

from __future__ import annotations

from .envelope import strict_json_equal
from .import_twins import bind_import_twin

REVIEWED_COMMITS = (
    "0bbeb5e6436f4e30208e5067ee17c5ad676c6003",
    "b2b5366fc94b2d17ea31309210141edf8dcbc696",
)
_POLICY = (
    ("mode", "frontier_session"),
    ("intended_use", "research_only"),
    ("project_training_policy", "blocked"),
)
_REVIEWED = (
    (
        "synthetic-factory.hardware_parity.scenario_catalog",
        "sha256:3c960b490a83979b4fec2a48ffc9ca058f100c49ff68fe356d1dfe44598b74db",
        "sha256:45574bf07b7e19892a4e507b896906320f7ecda938a7ea48df2038125985154e",
        "Hardware-parity scenario catalogs were authored in a frontier-model "
        "session; every resulting record is research-only.",
    ),
    (
        "synthetic-factory.nir_equivalence.graph_catalog",
        "sha256:56d7b4d76105bbefb36e5af93104ca83dfd71a0d2383dbd9430414e812f08172",
        "sha256:526d256fb3c3ee21306feb5b81700f2f9befec0d28bf1dcd7e78a10e95400920",
        "NIR cross-runtime graph catalogs were authored in a frontier-model "
        "session; every resulting record is research-only.",
    ),
    (
        "synthetic-factory.hardware_parity.scenario_catalog",
        "sha256:86a54ae338155603aa1e5291f34f843ea2856f3fd7aa24be3fb770792a25f449",
        "sha256:45574bf07b7e19892a4e507b896906320f7ecda938a7ea48df2038125985154e",
        "Hardware-parity scenario catalogs were authored in a frontier-model "
        "session; every resulting record is research-only.",
    ),
    (
        "synthetic-factory.nir_equivalence.graph_catalog",
        "sha256:f8069de53c4955c474f3b15493c1e044a3444567d931773e6dfc664d7d2fa3d4",
        "sha256:526d256fb3c3ee21306feb5b81700f2f9befec0d28bf1dcd7e78a10e95400920",
        "NIR cross-runtime graph catalogs were authored in a frontier-model "
        "session; every resulting record is research-only.",
    ),
)


def reviewed_catalog_stamps(recorded, current):
    """Select an entire independently pinned historical identity, never a hash alone."""
    if not isinstance(recorded, dict):
        return current
    for generator, version, catalog, attestation in _REVIEWED:
        if generator != current["generator"]:
            continue
        expected = {
            "generator": generator,
            "generator_version": version,
            "catalog_digest": catalog,
            "catalog_authorship": dict(_POLICY, attestation=attestation),
        }
        if all(strict_json_equal(recorded.get(key), value) for key, value in expected.items()):
            return expected
    return current


bind_import_twin(__name__)
