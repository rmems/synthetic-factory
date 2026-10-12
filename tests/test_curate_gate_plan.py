#!/usr/bin/env python3
"""Plan-loading tests for the curation gate (pipelines/curate_gate.py).

Integration-plan loading in the curation gate: the six lane contracts in
order, one version per transform, existing non-symlinked lane output
directories, .json/.jsonl lane manifests, repository-relative raw sources, and
plan fields and digest taken from one captured snapshot.
"""

import json
import sys
import unittest
from pathlib import Path
from unittest import mock

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from curate_gate_test_support import temp_root  # noqa: E402
from gate_fixture import (  # noqa: E402
    PIPELINES,
    GateFixture,
    _captured_main,
    _thalamic,
    _write_jsonl,
)

if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

import curate_gate  # noqa: E402
import curate_gate_plan  # noqa: E402


class PlanLoadingTests(unittest.TestCase):
    """Loading the integration plan pins its lane contracts, paths and digest."""

    def setUp(self):
        self.root = temp_root(self)

    def test_plan_rejects_ambiguous_lane_manifest_formats(self):
        for suffix in ("", ".txt"):
            with self.subTest(suffix=suffix or "extensionless"):
                fixture = GateFixture(self.root / (suffix.removeprefix(".") or "none"))
                ambiguous = fixture.lane_bridge / f"manifest{suffix}"
                fixture.manifest_paths[0].rename(ambiguous)
                plan = json.loads(fixture.plan_path.read_text())
                plan["lanes"][0]["manifest"] = ambiguous.relative_to(fixture.root).as_posix()
                fixture.plan_path.write_text(json.dumps(plan))

                code, _report, stderr = _captured_main(
                    [
                        "integrate",
                        "--plan",
                        str(fixture.plan_path),
                        "--cleaned-out",
                        str(fixture.cleaned),
                    ]
                )
                self.assertEqual(code, 2)
                self.assertIn("must end in .json or .jsonl", stderr)
                self.assertFalse(fixture.cleaned.exists())

    def test_repository_relative_raw_source_matches_documented_plan(self):
        project = self.root / "project"
        plan_dir = project / "outputs" / "curation"
        fixture = GateFixture(plan_dir)
        raw_root = project / "outputs" / "raw"
        production_source = raw_root / "2026-08-17"
        raw_root.mkdir(parents=True)
        fixture.source_run.rename(production_source)
        fixture.source_run = production_source
        plan = json.loads(fixture.plan_path.read_text())
        plan["source_run"] = "outputs/raw/2026-08-17"
        fixture.plan_path.write_text(json.dumps(plan, indent=2) + "\n")

        with (
            mock.patch.object(curate_gate, "_REPO", project.resolve()),
            mock.patch.object(curate_gate, "RAW_OUTPUT_ROOT", raw_root.resolve()),
        ):
            self.assertEqual(fixture.integrate(), 1)
        self.assertTrue((fixture.cleaned / curate_gate.MANIFEST_FILENAME).is_file())

    def test_plan_rejects_a_transform_declared_at_two_versions(self):
        fixture = GateFixture(self.root)
        plan = json.loads(fixture.plan_path.read_text())
        plan["lanes"][1]["transform"] = "bridge_event_time_order"
        plan["lanes"][1]["version"] = "9.9.9"
        fixture.plan_path.write_text(json.dumps(plan))
        with self.assertRaises(curate_gate.GateError) as ctx:
            curate_gate.load_plan(fixture.plan_path)
        self.assertIn("two versions", str(ctx.exception))

    def test_plan_rejects_a_missing_lane_output_directory(self):
        fixture = GateFixture(self.root)
        plan = json.loads(fixture.plan_path.read_text())
        plan["lanes"][0]["outputs"] = "lane-does-not-exist"
        fixture.plan_path.write_text(json.dumps(plan))
        with self.assertRaises(curate_gate.GateError):
            curate_gate.load_plan(fixture.plan_path)

    def test_plan_fields_and_digest_come_from_one_captured_snapshot(self):
        fixture = GateFixture(self.root)
        original = fixture.plan_path.read_bytes()
        original_digest = curate_gate.sha256_hex(original)
        real_resolve = curate_gate_plan._resolve_source_run_path
        changed = False

        def mutate_after_snapshot(*args, **kwargs):
            nonlocal changed
            resolved = real_resolve(*args, **kwargs)
            if not changed:
                changed = True
                fixture.plan_path.write_bytes(original + b"\n")
            return resolved

        with mock.patch.object(
            curate_gate_plan,
            "_resolve_source_run_path",
            side_effect=mutate_after_snapshot,
        ):
            loaded = curate_gate.load_plan(fixture.plan_path)

        self.assertTrue(changed)
        self.assertEqual(loaded["plan_sha256"], original_digest)
        self.assertNotEqual(
            loaded["plan_sha256"],
            curate_gate.file_sha256(fixture.plan_path),
        )

    def test_plan_rejects_a_symlinked_outputs_directory_before_resolving(self):
        fixture = GateFixture(self.root)
        outside = self.root / "outside-lane"
        _write_jsonl(outside / "factory" / "batch.jsonl", [_thalamic("outside")])
        linked = self.root / "linked-lane"
        try:
            linked.symlink_to(outside, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks are unavailable on this platform")
        plan = json.loads(fixture.plan_path.read_text())
        plan["lanes"][1]["outputs"] = linked.name
        fixture.plan_path.write_text(json.dumps(plan))

        self.assertEqual(fixture.integrate(), 2)
        self.assertFalse(fixture.cleaned.exists())

    def test_plan_requires_all_six_lane_contracts_in_order(self):
        fixture = GateFixture(self.root)
        plan = json.loads(fixture.plan_path.read_text())
        plan["lanes"].pop(3)
        fixture.plan_path.write_text(json.dumps(plan))

        with self.assertRaises(curate_gate.GateError) as ctx:
            curate_gate.load_plan(fixture.plan_path)
        self.assertIn("six required contracts in order", str(ctx.exception))


if __name__ == '__main__':
    unittest.main()
