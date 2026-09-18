#!/usr/bin/env python3
"""Verify the reviewed simulator executable sources without importing them.

Oracle implementation pins come from 6ca641465bbf8ce8339de1dce6ce77f77186e34a.
The package initializer includes the reviewed import-identity repair from
f98dd3e8facd282744136ca91040ae595cfdc6b7. The worker pin seals this PR's
reviewed streaming adapter separately; it is not historical producer evidence.
``distill_vocabulary.py`` binds the reviewed #285 integer-count bytes; the
remaining producer pins are unchanged.
No source is executed to verify it.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from types import MappingProxyType

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_identity_registry_sources")
    from .curate_identity_json import IdentityCurationError
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_identity_registry_sources"
    )
    from curate_identity_json import IdentityCurationError


_REPO_ROOT = Path(__file__).resolve().parents[1]
SIMULATOR_SOURCE_PINS = MappingProxyType({
    "pipelines/curate_identity_simulator_worker.py": "7644045bb4d1e4673604154c6d8288cdc1ba168a3a7864e16c20d072f0f937d9",
    "pipelines/oracle_grounded/distill_blocks.py": "7dcbd942dfb8383370c6f68347e24c4332692b5016769014d2353f1c079eae69",
    "pipelines/oracle_grounded/distill_energy_claims.py": "16a1fe6aa0d50bc5e53439f29a6c57809588a88091b865ccd0ac686ac0cc70e2",
    "pipelines/oracle_grounded/distill_measurements.py": "dc2fd89567db0cb1a8ff0a9310f723ff8e80c5bf5e5f62149a788a55a707c2d2",
    "pipelines/oracle_grounded/fault_oracle.py": "a87611c2b25b91e72471190841227f207a41c2315edb7462634473ca57210828",
    "pipelines/oracle_grounded/fault_scenario.py": "4c81a14d479996b9cd76bb689782c0adaed62416154d906e14806d6421bc1fa5",
    "pipelines/oracle_grounded/rng.py": "3050e7c8b784f2ef0de79a2189f1944df516ea6d2f8af52ed52892e0635a8703",

    "pipelines/validate_run_provenance.py": "4bd36bc7c96336593eb4eaf330845db43add367b13772f7013aa4470fd2e1d28",
    "pipelines/validate_run_spikes.py": "6883519c0806996a6921116eadcb972fea07b6ee73e8db243c0a1c232e5f3a7f",
    "pipelines/exact_json.py": "ac923100a7bd857e2401355ce2cd05ef3ec6eeb835a3ab73f392392d80ec057d",
    "pipelines/exact_json_encoding.py": "56c8e47e70f2234ce68c26975279c5938d3c612c6d4fc79c98f0309c497b22ff",
    "schemas/thalamic-trajectory.schema.json": "b577363500cab5362825968647d40deed279d8e19e6b73b96ae9b1404e414acd",
    "pipelines/oracle_grounded/__init__.py": "d72f76b03de1cd7818b1be38dddce045e5e9d0af6298e9613102a311605e9408",
    "pipelines/oracle_grounded/fault_simulator.py": "be267e0720662cf1f8c79b24384bd335df9ec127fce8184459e2e64e31c8d3e4",
    "pipelines/oracle_grounded/fault_config.py": "815b535985057ea6e1ad2e4cb6c751612b21bdc153e284683e1dbba22c4292e4",
    "pipelines/oracle_grounded/fault_vocabulary.py": "066ebb41123e7fdf77fffbb77e70380348f549195f55963c7c64da6c0cfcffbe",
    "pipelines/oracle_grounded/distill_builders.py": "b2f44d38d4a73ce9466d141e030f2cf535b5dcd58ee846497e09d01a2242a7f0",
    "pipelines/oracle_grounded/distill_vocabulary.py": "87129b3817ef336264f00fb12a1343cc7930bb862c2b369442962555b6edb60e",
    "pipelines/oracle_grounded/distill_labels.py": "7c4e102138efdba933995cea57b3c96ba92ad20064245c225d1a7f9bdca5d64c",
    "pipelines/oracle_grounded/envelope.py": "0ea00575ba81f9264c65ac975a762407353951c7b8bf35002c147971444f801b",
    "pipelines/oracle_grounded/refusals.py": "ebbc9717871c02c00b3e764e7dc4961032ad8a44ca1a20c3a4386acac4d67e5b",
    "pipelines/oracle_grounded/import_twins.py": "0f28c2ed713360ad2a0f398ef15815fc6031eb9c79ea351171bb48eb368ed4f0",
})


def simulator_source_snapshot() -> dict[str, bytes]:
    """Capture exactly the authenticated bytes that a replay may execute."""
    snapshot = {}
    for relative, expected in SIMULATOR_SOURCE_PINS.items():
        try:
            payload = (_REPO_ROOT / relative).read_bytes()
            normalized = payload.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
        except (OSError, UnicodeError) as exc:
            raise IdentityCurationError(f"reviewed simulator source is unavailable: {relative}") from exc
        if hashlib.sha256(normalized.encode("utf-8")).hexdigest() != expected:
            raise IdentityCurationError(f"reviewed simulator source digest differs: {relative}")
        snapshot[relative] = normalized.encode("utf-8")
    return snapshot


def require_simulator_sources() -> None:
    """Refuse registry authority if any reviewed executable dependency changed."""
    simulator_source_snapshot()


if __package__:
    _expose_package_sibling(__name__)
