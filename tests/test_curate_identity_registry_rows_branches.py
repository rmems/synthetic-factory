"""Pin how the factory registry loader refuses rows outside their reviewed route.

Each case loads a temporary copy of the committed registry with one row
changed, so the loader raises at load (CLAUDE.md: raise at load, exclude per
record). The committed registry itself is never written.
"""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
for entry in (TESTS, TESTS.parent / "pipelines"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

import curate_identity_registry as registry
from refusal_case_support import RefusalCaseAssertions

IdentityCurationError = registry.IdentityCurationError
_COMMITTED = json.loads(Path(registry.FACTORY_REGISTRY_PATH).read_text(encoding="utf-8"))
_RIGHTS_FIELDS = (
    "provider",
    "channel",
    "rights_profile_id",
    "intended_use",
    "project_training_policy",
)


def _first_row(source_type: str) -> int:
    rows = _COMMITTED["factories"]
    return next(
        (i for i, row in enumerate(rows) if row.get("source_type", "hosted") == source_type), -1
    )


_HOSTED = _first_row("hosted")
_MODEL_CHANNEL = _first_row("model_channel")


def _load(document: dict):
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp) / "FACTORY-REGISTRY.json"
        path.write_text(json.dumps(document), encoding="utf-8")
        return registry.load_registry(path)


def _document(mutate) -> dict:
    document = copy.deepcopy(_COMMITTED)
    mutate(document)
    return document


def _set_row(index: int, value):
    def mutate(document):
        document["factories"][index] = value

    return mutate


def _update_row(index: int, **changes):
    def mutate(document):
        document["factories"][index].update(changes)

    return mutate


def _single_row_registry(index: int, schema_version: str, *, strip_rights=False, **changes):
    def mutate(document):
        row = copy.deepcopy(document["factories"][index])
        for field_name in _RIGHTS_FIELDS if strip_rights else ():
            row.pop(field_name)
        row.update(changes)
        document.update(schema_version=schema_version, factories=[row])

    return mutate


_LEGACY = "factory-registry-v0.1"


_HOSTED_REFUSALS = (
    (
        "hosted row is not an object",
        _set_row(_HOSTED, "row"),
        f"factories[{_HOSTED}] must be an object",
    ),
    (
        "unknown source type on a standard row",
        _update_row(_HOSTED, source_type="hybrid"),
        f"factories[{_HOSTED}] source_type must be hosted or dedicated on a standard row",
    ),
    (
        "reviewed assignment that the policy does not authorize for this row",
        _update_row(
            _HOSTED,
            generator="procedural-attested",
            generator_version="1",
            provider="procedural",
            channel="local",
            rights_profile_id="procedural-local-attested-v1",
        ),
        f"factories[{_HOSTED}] rights fields drift from loaded policy",
    ),
)

_ROUTE_REFUSALS = (
    (
        "legacy row declares rights fields",
        _single_row_registry(_HOSTED, _LEGACY),
        (
            "factories[0] v0.1 rows must not declare rights fields: "
            "['provider', 'channel', 'rights_profile_id', 'intended_use', "
            "'project_training_policy']"
        ),
    ),
    (
        "legacy row is not an object",
        lambda document: document.update(schema_version=_LEGACY, factories=["row"]),
        "factories[0] must be an object",
    ),
    (
        "legacy row names a non-hosted generator",
        _single_row_registry(
            _HOSTED,
            _LEGACY,
            strip_rights=True,
            generator="deepseek-placeholder",
            generator_version="pending-terms",
        ),
        "factories[0] v0.1 rows cannot carry non-hosted rights profiles",
    ),
    (
        "model-channel row on a pre-v0.4 registry",
        _single_row_registry(_MODEL_CHANNEL, "factory-registry-v0.2"),
        "factories[0] model-channel fields require v0.3 route",
    ),
    (
        "model-channel row drifts from its sealed policy",
        _update_row(_MODEL_CHANNEL, generator_version="unreviewed"),
        (
            f"factories[{_MODEL_CHANNEL}]: model-channel registry row drifts from "
            "independently sealed policy"
        ),
    ),
)


class RegistryRowRefusals(RefusalCaseAssertions, unittest.TestCase):
    def test_fixture_rows_exist(self):
        self.assertGreaterEqual(_HOSTED, 0)
        self.assertGreaterEqual(_MODEL_CHANNEL, 0)

    def test_rows_outside_their_reviewed_route_are_refused_at_load(self):
        rows = (
            (label, _document(mutate), message)
            for label, mutate, message in (*_HOSTED_REFUSALS, *_ROUTE_REFUSALS)
        )
        self.assert_each_refuses(IdentityCurationError, _load, rows)

    def test_legacy_row_inherits_its_reviewed_hosted_rights(self):
        loaded = _load(_document(_single_row_registry(_HOSTED, _LEGACY, strip_rights=True)))
        hosted = _COMMITTED["factories"][_HOSTED]
        row = loaded.by_path_id[hosted["path_id"]]
        self.assertEqual(loaded.schema_version, _LEGACY)
        self.assertEqual(
            (row.provider, row.channel, row.rights_profile_id),
            (hosted["provider"], hosted["channel"], registry.HOSTED_FRONTIER_PROFILE_ID),
        )
        self.assertEqual(
            (row.intended_use, row.project_training_policy),
            (hosted["intended_use"], hosted["project_training_policy"]),
        )


if __name__ == "__main__":
    unittest.main()
