#!/usr/bin/env python3
"""Raw-data-safety containment for the #78 distillation writers.

Every destination the distillation JSONL writer and the fixture builder
touch must pass through ``raw_tree_guard`` -- the one raw-path detector in
this repository, which also recognises another checkout's ``outputs/raw``,
symlink aliases and bind mounts of the raw root -- and the fixture builder
must never delete or overwrite an existing tree: a rebuild goes to a fresh
directory, so a failed build leaves the previous fixture exactly as it was.

Every test here fails against PR #138 at 75642831, where ``write_jsonl``
only checked ``destination.exists()``, ``_refuse_raw_tree`` compared against
this checkout's resolved raw root alone, and ``--force`` ran ``shutil.rmtree``
ahead of every generator. Destructive paths are exercised only inside
disposable temporary directories.
"""

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import raw_tree_guard  # noqa: E402
from oracle_grounded import distill_contract as oc  # noqa: E402

BUILDER = REPO / "scripts" / "build_distillation_fixture.py"
FAMILIES = ("fault-recovery", "energy-preferences", "moe-router")
RECORDS = [{"id": "r1", "value": 1}, {"id": "r2", "value": 2}]


def _load_builder(name: str):
    spec = importlib.util.spec_from_file_location(name, BUILDER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _tree_bytes(root: Path) -> dict[str, bytes]:
    """Every file below ``root`` with its exact bytes, nested files included."""

    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _write_evidence(batch: Path) -> None:
    batch.parent.mkdir(parents=True)
    batch.write_text('{"id": "published-evidence"}\n', encoding="utf-8")


def _fixture_shaped_run(out: Path, producer: str) -> None:
    """A run the builder itself wrote, plus nested files it did not write."""

    for family in FAMILIES:
        (out / family).mkdir(parents=True)
        (out / family / "batch-r01.jsonl").write_text(
            json.dumps({"id": family}) + "\n", encoding="utf-8"
        )
    (out / "MANIFEST.json").write_text(
        json.dumps({"generated_by": producer}) + "\n", encoding="utf-8"
    )
    (out / "moe-router" / "teacher-recording-r02.jsonl").write_text(
        '{"teacher": "recorded"}\n', encoding="utf-8"
    )
    (out / "fault-recovery" / "notes").mkdir()
    (out / "fault-recovery" / "notes" / "important.txt").write_text(
        "keep me\n", encoding="utf-8"
    )


def _generators_must_not_run(module):
    """Patch every family generator to fail loudly if a refused build reaches it."""

    return mock.patch.multiple(
        module,
        fault_recovery=mock.Mock(
            wraps=module.fault_recovery,
            build_records=mock.Mock(side_effect=AssertionError("fault generator ran")),
        ),
        energy_preferences=mock.Mock(
            wraps=module.energy_preferences,
            build_records=mock.Mock(side_effect=AssertionError("energy generator ran")),
            select_meter=mock.Mock(side_effect=AssertionError("meter probe ran")),
        ),
        moe_router=mock.Mock(
            wraps=module.moe_router,
            build_records=mock.Mock(side_effect=AssertionError("router generator ran")),
            oracles_report=mock.Mock(side_effect=AssertionError("router probe ran")),
        ),
    )


class DistillJsonlWriterRawTreeGuard(unittest.TestCase):
    """oracle_grounded.distill_jsonl.write_jsonl, through the contract facade."""

    def test_refuses_a_direct_outputs_raw_destination_before_creating_anything(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            destination = root / "outputs" / "raw" / "demo-run" / "fault-recovery"
            with self.assertRaises(oc.ContractError) as caught:
                oc.write_jsonl(destination / "batch-r01.jsonl", RECORDS)
            self.assertIn("immutable raw evidence", str(caught.exception))
            # The refusal happens before mkdir(parents=True), so not even the
            # factory directory appears inside the raw tree.
            self.assertFalse((root / "outputs").exists())

    def test_refuses_another_checkouts_outputs_raw_and_leaves_its_bytes_alone(self):
        with tempfile.TemporaryDirectory() as tmp:
            other = Path(tmp) / "other-checkout"
            raw = other / "outputs" / "raw"
            _write_evidence(raw / "run-a" / "factory" / "batch-r01.jsonl")
            before = _tree_bytes(other)
            for destination in (
                raw / "run-a" / "factory" / "batch-r02.jsonl",
                raw / "run-b" / "factory" / "batch-r01.jsonl",
            ):
                with self.subTest(destination=destination.relative_to(other)):
                    with self.assertRaises(oc.ContractError) as caught:
                        oc.write_jsonl(destination, RECORDS)
                    self.assertIn("immutable raw evidence", str(caught.exception))
            self.assertEqual(_tree_bytes(other), before)

    def test_refuses_an_alias_of_the_raw_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence_root = root / "evidence-root"
            evidence_root.mkdir()
            alias = root / "alias-raw"
            alias.symlink_to(evidence_root, target_is_directory=True)
            with mock.patch.object(raw_tree_guard, "DEFAULT_RAW_OUTPUT_ROOT", evidence_root):
                for destination in (
                    alias / "run" / "factory" / "batch-r01.jsonl",
                    evidence_root / "run" / "factory" / "batch-r01.jsonl",
                ):
                    with self.subTest(destination=destination.relative_to(root)):
                        with self.assertRaises(oc.ContractError) as caught:
                            oc.write_jsonl(destination, RECORDS)
                        self.assertIn("immutable raw evidence", str(caught.exception))
            self.assertEqual(list(evidence_root.iterdir()), [])

    def test_still_writes_outside_the_raw_tree_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "outputs" / "cleaned" / "run" / "batch-r01.jsonl"
            self.assertEqual(oc.write_jsonl(destination, RECORDS), 2)
            self.assertEqual(len(destination.read_text(encoding="utf-8").splitlines()), 2)
            with self.assertRaises(oc.ContractError) as caught:
                oc.write_jsonl(destination, RECORDS)
            self.assertIn("refusing to overwrite", str(caught.exception))


class FixtureBuilderRawTreeContainment(unittest.TestCase):
    """scripts/build_distillation_fixture.py"""

    def test_refuses_raw_destinations_before_any_generator_runs(self):
        module = _load_builder("bdf_containment_raw")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            other = root / "other-checkout"
            _write_evidence(other / "outputs" / "raw" / "run-a" / "factory" / "batch-r01.jsonl")
            before = _tree_bytes(other)
            targets = (
                root / "outputs" / "raw" / "distillation-run",
                other / "outputs" / "raw" / "distillation-run",
                other / "outputs" / "raw" / "run-a",
            )
            with _generators_must_not_run(module):
                for out in targets:
                    for force in (False, True):
                        with self.subTest(out=out.relative_to(root), force=force):
                            with self.assertRaises(SystemExit) as caught:
                                module.build(out, force=force)
                            self.assertIn("immutable evidence tree", str(caught.exception))
            self.assertFalse((root / "outputs").exists())
            self.assertEqual(_tree_bytes(other), before)

    def test_refuses_an_alias_of_the_raw_root_before_any_generator_runs(self):
        module = _load_builder("bdf_containment_alias")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence_root = root / "evidence-root"
            evidence_root.mkdir()
            alias = root / "alias-raw"
            alias.symlink_to(evidence_root, target_is_directory=True)
            with mock.patch.object(raw_tree_guard, "DEFAULT_RAW_OUTPUT_ROOT", evidence_root):
                with _generators_must_not_run(module):
                    for out in (alias / "distillation-run", evidence_root / "distillation-run"):
                        with self.subTest(out=out.relative_to(root)):
                            with self.assertRaises(SystemExit) as caught:
                                module.build(out, force=True)
                            self.assertIn("immutable evidence tree", str(caught.exception))
            self.assertEqual(list(evidence_root.iterdir()), [])

    def test_an_existing_run_is_refused_before_any_mutation_even_with_force(self):
        module = _load_builder("bdf_containment_force")
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "distillation-run"
            _fixture_shaped_run(out, module.MANIFEST_PRODUCER)
            before = _tree_bytes(out)
            self.assertIn("moe-router/teacher-recording-r02.jsonl", before)
            self.assertIn("fault-recovery/notes/important.txt", before)
            with _generators_must_not_run(module):
                for force in (True, False):
                    with self.subTest(force=force):
                        with self.assertRaises(SystemExit) as caught:
                            module.build(out, force=force)
                        self.assertIn("fresh", str(caught.exception))
                with self.subTest(entry="cli --force"):
                    with self.assertRaises(SystemExit):
                        module.main(["--out", str(out), "--force"])
            # Nothing was deleted, rewritten or added: the run the builder
            # wrote and the nested files it did not write are byte-identical.
            self.assertEqual(_tree_bytes(out), before)

    def test_an_empty_existing_directory_is_refused_too(self):
        module = _load_builder("bdf_containment_empty")
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "distillation-run"
            out.mkdir()
            with _generators_must_not_run(module):
                with self.assertRaises(SystemExit):
                    module.build(out, force=True)
            self.assertTrue(out.is_dir())
            self.assertEqual(list(out.iterdir()), [])

    def test_a_generator_failure_leaves_the_previous_fixture_untouched(self):
        module = _load_builder("bdf_containment_failure")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            previous = root / "distillation-run"
            _fixture_shaped_run(previous, module.MANIFEST_PRODUCER)
            before = _tree_bytes(previous)
            fresh = root / "distillation-run-next"
            with mock.patch.object(
                module.fault_recovery,
                "build_records",
                side_effect=RuntimeError("generator regression"),
            ):
                for force in (False, True):
                    with self.subTest(force=force):
                        with self.assertRaises(RuntimeError):
                            module.build(fresh, force=force)
            self.assertEqual(_tree_bytes(previous), before)
            # A failed build into a fresh directory leaves no partial tree.
            self.assertFalse(fresh.exists())


if __name__ == "__main__":
    unittest.main()
