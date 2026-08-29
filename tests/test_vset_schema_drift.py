#!/usr/bin/env python3
"""The VSET schemas must not drift from the validator that gates them.

A consumer that validates only the JSON Schema, and a consumer that runs
``pipelines/validate_vset.py``, must not disagree about which documents
are acceptable. Every check here is a review finding on #159: a record or
manifest that one side accepts and the other rejects is the bug.

Stdlib only -- CI installs no JSON Schema implementation, so these walk
the schema documents directly.
"""

from __future__ import annotations

import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from vset_testutil import (  # noqa: E402
    ACCEPT,
    MANIFEST,
    REJECT,
    REPO,
    codes as _codes,
    load_record as _load,
    vset,
)

sys.path.insert(0, str(REPO / "pipelines"))
sys.path.insert(0, str(REPO / "scripts"))
import refresh_vset_fixture_pins as pins  # noqa: E402
from vset_constants import (  # noqa: E402
    KIND_PAYLOAD_KEYS,
    RECORD_KINDS,
    REVIEW_REQUIRED_KINDS,
)

SCHEMAS = REPO / "schemas"
RECORD_SCHEMA = SCHEMAS / "vset-record-v1.schema.json"
MANIFEST_SCHEMA = SCHEMAS / "vset-release-manifest-v1.schema.json"
REFRESH = "python3 scripts/refresh_vset_fixture_pins.py"


def _schema(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _closed_branch(schema: dict[str, Any]) -> dict[str, Any]:
    """The vset-record-v1 branch that closes the top-level key set."""

    for branch in schema["allOf"]:
        if branch.get("additionalProperties") is False:
            return branch
    raise AssertionError("vset-record-v1 no longer closes its top-level properties")


def _conditional_kind(node: Any) -> str | None:
    """The ``record_kind`` an ``if``/``then`` branch keys on, when it is one."""

    if not isinstance(node, dict) or not isinstance(node.get("then"), dict):
        return None
    condition = node.get("if")
    if not isinstance(condition, dict):
        return None
    kind = condition.get("properties", {}).get("record_kind", {}).get("const")
    return kind if isinstance(kind, str) else None


def _children(node: Any) -> list[Any]:
    if isinstance(node, list):
        return list(node)
    if isinstance(node, dict):
        return list(node.values())
    return []


def _kind_conditionals(node: Any, found: dict[str, list[dict[str, Any]]]) -> None:
    """Collect every ``if record_kind == X then ...`` branch in the schema."""

    kind = _conditional_kind(node)
    if kind is not None:
        found.setdefault(kind, []).append(node["then"])
    for child in _children(node):
        _kind_conditionals(child, found)


def _conditionals() -> dict[str, list[dict[str, Any]]]:
    found: dict[str, list[dict[str, Any]]] = {}
    _kind_conditionals(_schema(RECORD_SCHEMA), found)
    return found


class RecordSchemaDriftTests(unittest.TestCase):
    def test_every_fixture_top_level_key_is_declared(self):
        """additionalProperties:false must not forbid a key the validator reads."""

        declared = set(_closed_branch(_schema(RECORD_SCHEMA))["properties"])
        for directory in (ACCEPT, REJECT):
            for path in sorted(directory.glob("*.json")):
                with self.subTest(fixture=path.name):
                    self.assertEqual(set(_load(path)) - declared, set())

    def test_prometheus_lineage_is_declared_because_the_validator_reads_it(self):
        """A top-level key the validator inspects cannot be schema-forbidden.

        ``_prometheus_identity_claimed`` scans ``record["prometheus_lineage"]``
        as well as the ``environment`` copy, so the closed top-level property
        set has to admit it.
        """

        declared = _closed_branch(_schema(RECORD_SCHEMA))["properties"]
        self.assertIn("prometheus_lineage", declared)
        record = _load(ACCEPT / "issue-patch-validated.json")
        self.assertEqual(_codes(vset.validate_record(record)), [])
        self.assertNotIn("prometheus_lineage", record["environment"])
        record["prometheus_lineage"] = "rmems/operation-prometheus#55"
        self.assertIn(
            "vset.source_kind_masquerade", _codes(vset.validate_record(record))
        )

    def test_payload_conditionals_match_kind_payload_keys(self):
        conditionals = _conditionals()
        self.assertEqual(set(conditionals), set(RECORD_KINDS))
        for kind, required in KIND_PAYLOAD_KEYS.items():
            with self.subTest(kind=kind):
                declared: set[str] = set()
                for branch in conditionals[kind]:
                    payload = branch.get("properties", {}).get("payload", {})
                    declared |= set(payload.get("required", []))
                self.assertEqual(declared, set(required))

    def test_review_required_kinds_demand_a_reviewer_object(self):
        conditionals = _conditionals()
        for kind in REVIEW_REQUIRED_KINDS:
            with self.subTest(kind=kind):
                branches = conditionals[kind]
                self.assertTrue(
                    any("reviewer" in branch.get("required", []) for branch in branches)
                )
                self.assertTrue(
                    any(
                        branch.get("properties", {}).get("reviewer", {}).get("type")
                        == "object"
                        for branch in branches
                    )
                )
        missing = _load(REJECT / "missing-reviewer-when-required.json")
        self.assertIn("vset.reviewer_required", _codes(vset.validate_record(missing)))

    def test_schema_names_the_authoritative_gate(self):
        """The recursive hidden-reasoning ban is not expressible here."""

        description = _schema(RECORD_SCHEMA)["description"]
        self.assertIn("pipelines/validate_vset.py", description)
        self.assertIn("authoritative", description)


class ManifestSchemaDriftTests(unittest.TestCase):
    def _actor_required(self, role: str) -> set[str]:
        entry = _schema(MANIFEST_SCHEMA)["$defs"]["entry"]["properties"][role]
        required = set()
        for branch in entry.get("allOf", [entry]):
            required |= set(branch.get("required", []))
        return required

    def test_task_author_requires_prompt_hash_on_both_sides(self):
        self.assertIn("prompt_hash", self._actor_required("task_author"))
        manifest = _load(MANIFEST)
        del manifest["entries"][0]["task_author"]["prompt_hash"]
        manifest["manifest_hash"] = vset.manifest_body_hash(manifest)
        self.assertIn(
            "vset.actor_fields_invalid", _codes(vset.validate_manifest(manifest))
        )

    def test_solver_requires_tool_policy_on_both_sides(self):
        self.assertIn("tool_policy", self._actor_required("solver"))
        manifest = _load(MANIFEST)
        del manifest["entries"][0]["solver"]["tool_policy"]
        manifest["manifest_hash"] = vset.manifest_body_hash(manifest)
        self.assertIn(
            "vset.actor_fields_invalid", _codes(vset.validate_manifest(manifest))
        )

    def test_by_record_kind_is_zero_filled_on_both_sides(self):
        declared = _schema(MANIFEST_SCHEMA)["properties"]["counts"]["properties"][
            "by_record_kind"
        ]
        self.assertEqual(set(declared["required"]), set(RECORD_KINDS))
        self.assertEqual(set(declared["properties"]), set(RECORD_KINDS))
        self.assertIs(declared["additionalProperties"], False)

    def test_zero_filled_tally_is_accepted_and_an_omitted_kind_is_not(self):
        manifest = _load(MANIFEST)
        self.assertEqual(set(manifest["counts"]["by_record_kind"]), set(RECORD_KINDS))
        self.assertEqual(_codes(vset.validate_manifest(manifest)), [])
        manifest["counts"]["by_record_kind"] = {
            kind: count
            for kind, count in manifest["counts"]["by_record_kind"].items()
            if count
        }
        manifest["manifest_hash"] = vset.manifest_body_hash(manifest)
        self.assertIn("vset.payload_invalid", _codes(vset.validate_manifest(manifest)))


class FixturePinFreshnessTests(unittest.TestCase):
    def test_fixture_pins_match_the_live_repository(self):
        """Registry and repo-pack edits have a stated regeneration step."""

        stale = [str(path.relative_to(REPO)) for path in pins.stale_fixtures()]
        self.assertEqual(stale, [], f"stale VSET fixture pins; run: {REFRESH}")

    def test_refresh_is_idempotent_and_check_agrees(self):
        with redirect_stdout(io.StringIO()):
            self.assertEqual(pins.main(["--check"]), 0)


if __name__ == "__main__":
    unittest.main()
