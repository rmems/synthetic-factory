"""Explicitly reviewed historical source/catalog identities for current replay.

The snapshots below were independently recomputed from Git source blobs at the
reviewed commits. The first immutable fixture bytes live under
tests/fixtures/parity-history/0bbeb5e6; later snapshots differ only in source stamps.
Every byte representation is pinned by raw SHA-256 in the tests.
Only provenance stamp comparison uses these values. Every current envelope,
scenario, measurement, availability, and complete-catalog check still runs.
"""

from __future__ import annotations

from .envelope import strict_json_equal
from .import_twins import bind_import_twin

REVIEWED_COMMITS = (
    "55cd425dc6aef6609e645fba60b3a89f72659274",
    "0bbeb5e6436f4e30208e5067ee17c5ad676c6003",
    "b2b5366fc94b2d17ea31309210141edf8dcbc696",
    "d4f7d53ad6a11d0fed21cde7d767177810e4c47c",
)
_POLICY = (
    ("mode", "frontier_session"),
    ("intended_use", "research_only"),
    ("project_training_policy", "blocked"),
)
_HARDWARE_GENERATOR = 'synthetic-factory.hardware_parity.scenario_catalog'
_HARDWARE_CATALOG_DIGEST = 'sha256:45574bf07b7e19892a4e507b896906320f7ecda938a7ea48df2038125985154e'
_HARDWARE_ATTESTATION = 'Hardware-parity scenario catalogs were authored in a frontier-model session; every resulting record is research-only.'
_NIR_GENERATOR = 'synthetic-factory.nir_equivalence.graph_catalog'
_NIR_CATALOG_DIGEST = 'sha256:526d256fb3c3ee21306feb5b81700f2f9befec0d28bf1dcd7e78a10e95400920'
_NIR_ATTESTATION = 'NIR cross-runtime graph catalogs were authored in a frontier-model session; every resulting record is research-only.'
_REVIEWED = (
    (
        _HARDWARE_GENERATOR,
        "sha256:3c960b490a83979b4fec2a48ffc9ca058f100c49ff68fe356d1dfe44598b74db",
        _HARDWARE_CATALOG_DIGEST,
        _HARDWARE_ATTESTATION,
    ),
    (
        _NIR_GENERATOR,
        "sha256:56d7b4d76105bbefb36e5af93104ca83dfd71a0d2383dbd9430414e812f08172",
        _NIR_CATALOG_DIGEST,
        _NIR_ATTESTATION,
    ),
    (
        _HARDWARE_GENERATOR,
        "sha256:86a54ae338155603aa1e5291f34f843ea2856f3fd7aa24be3fb770792a25f449",
        _HARDWARE_CATALOG_DIGEST,
        _HARDWARE_ATTESTATION,
    ),
    (
        _NIR_GENERATOR,
        "sha256:f8069de53c4955c474f3b15493c1e044a3444567d931773e6dfc664d7d2fa3d4",
        _NIR_CATALOG_DIGEST,
        _NIR_ATTESTATION,
    ),
    (_HARDWARE_GENERATOR,
     'sha256:13d02b4bb48c2a568d14099230020fb1cfc8caa67a1a868b304014bf6ff2cde6',
     _HARDWARE_CATALOG_DIGEST,
     _HARDWARE_ATTESTATION),
    (_NIR_GENERATOR,
     'sha256:033a6a90bbc65a34d5f306c36e25cb411d91bf8206105ab0fe3fb6b200a0cb62',
     _NIR_CATALOG_DIGEST,
     _NIR_ATTESTATION),
    (
        _HARDWARE_GENERATOR,
        "sha256:ebe175c583a73488c5fdc23fcacb51a60c3088743fdf0d788090b72a9168a600",
        _HARDWARE_CATALOG_DIGEST,
        _HARDWARE_ATTESTATION,
    ),
    (
        _NIR_GENERATOR,
        "sha256:1973de002f744fceeddff9c2e13bb4f8dcc9256ef2cdc2663d66cc6a03faa5f6",
        _NIR_CATALOG_DIGEST,
        _NIR_ATTESTATION,
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
