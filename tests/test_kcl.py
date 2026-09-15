#!/usr/bin/env python3
"""AST-extracted kcl leftover family under ``pipelines/kcl``."""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
KCL_DIR = PIPELINES / "kcl"
COMMITTED = REPO / "config" / "kcl"
FIXTURE = REPO / "tests" / "fixtures" / "kcl"
PACKAGE_FILES = ("__init__.py", "_contract.py", "catalog.py", "cli.py", "generate.py")

sys.path.insert(0, str(PIPELINES))

from hopper.plants import pairs_by_factory  # noqa: E402
from kcl import catalog, cli, generate  # noqa: E402
from kcl._contract import (  # noqa: E402
    EXTRACT_METHOD,
    FACTORY,
    FAMILY_PREFIX,
    FINDING_CATALOG_SHA256_MISMATCH,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_PLANT_NOT_FOUND,
    FINDING_UNKNOWN_WAVE,
    GENERATOR,
    HANDOFF_STEPS,
    HOPPER_WAVE,
    KclRefusal,
    LEGACY_COMMIT,
    SOURCE_MILLS,
    SUCCESS_STEPS,
)
from mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES  # noqa: E402
from raw_tree_guard import DEFAULT_RAW_OUTPUT_ROOT  # noqa: E402
from record_kind import classify_kind  # noqa: E402


def invoke(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.run(argv)
    return code, out.getvalue(), err.getvalue()


def _legacy_source(relpath: str) -> str | None:
    for spec in (f"{LEGACY_COMMIT}:{relpath}", f"origin/legacy-mill-lane:{relpath}"):
        try:
            return subprocess.check_output(["git", "show", spec], text=True, cwd=REPO)
        except subprocess.CalledProcessError:
            continue
    return None


class KclFamilyLayoutTests(unittest.TestCase):
    def test_package_is_exactly_the_cleaned_modules(self):
        names = tuple(sorted(path.name for path in KCL_DIR.glob("*.py")))
        self.assertEqual(names, tuple(sorted(PACKAGE_FILES)))

    def test_leftover_mill_scripts_are_not_vendored(self):
        leftover = (
            tuple(KCL_DIR.glob("kcl-mill*.py"))
            + tuple(KCL_DIR.glob("kcl-loop*.py"))
            + tuple(KCL_DIR.glob("kcl-hop-mill*.py"))
            + tuple(KCL_DIR.glob("hopper_mill_g46c.py"))
        )
        self.assertEqual(leftover, ())

    def test_catalog_modules_never_exec(self):
        text = (KCL_DIR / "catalog.py").read_text(encoding="utf-8")
        self.assertNotIn("exec(", text)
        self.assertNotIn("exec_module", text)
        self.assertIn("ast.parse", text)


class KclCatalogTests(unittest.TestCase):
    def test_reviewed_prefix_maps_to_factory(self):
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES[FAMILY_PREFIX], FACTORY)

    def test_committed_catalog_loads_ast_extracted_plants(self):
        loaded = catalog.catalog_check(root=REPO)
        self.assertEqual(loaded.catalog_id, "kcl-plants-v1")
        self.assertEqual(loaded.factory, FACTORY)
        self.assertEqual(len(loaded.plants), 705)
        self.assertEqual(len(loaded.mills), 11)
        self.assertEqual(len({plant.plant_id for plant in loaded.plants}), 705)
        self.assertEqual(loaded.meta["source"]["method"], EXTRACT_METHOD)
        self.assertEqual(loaded.meta["source"]["commit"], LEGACY_COMMIT)
        self.assertEqual([mill.mill_id for mill in loaded.mills], [item[0] for item in SOURCE_MILLS])
        pair = sum(1 for plant in loaded.plants if plant.shape == "pair")
        row = sum(1 for plant in loaded.plants if plant.shape == "row")
        self.assertEqual((pair, row), (478, 227))

    def test_fixture_catalog_is_one_plant(self):
        loaded = catalog.load_catalog(FIXTURE)
        self.assertEqual(loaded.catalog_id, "kcl-fixture-v1")
        self.assertEqual(len(loaded.plants), 1)
        self.assertEqual(loaded.plants[0].plant_id, "kcl_r0001:fixture-leftover-field")

    def test_pin_mismatch_is_a_coded_refusal(self):
        root = Path(tempfile.mkdtemp(prefix="kcl-pin-"))
        self.addCleanup(shutil.rmtree, root, True)
        dest = root / "catalog"
        shutil.copytree(FIXTURE, dest)
        meta_path = dest / catalog.CATALOG_FILENAME
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["plants_sha256"] = "0" * 64
        meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        with self.assertRaises(KclRefusal) as caught:
            catalog.load_catalog(dest)
        self.assertEqual(caught.exception.code, FINDING_CATALOG_SHA256_MISMATCH)

    def test_unknown_plant_is_a_coded_refusal(self):
        loaded = catalog.load_catalog(FIXTURE)
        with self.assertRaises(KclRefusal) as caught:
            loaded.plant("kcl_r0001:missing")
        self.assertEqual(caught.exception.code, FINDING_PLANT_NOT_FOUND)

    def test_catalog_matches_legacy_ast_extract(self):
        loaded = catalog.catalog_check(root=REPO)
        compared = 0
        for mill_id, base_round, rel, shape in SOURCE_MILLS:
            source = _legacy_source(rel)
            if source is None:
                self.skipTest("legacy-mill-lane kcl sources are not available")
            extracted = catalog.ast_extract_plants(
                source, mill_id=mill_id, path=rel, base_round=base_round, shape=shape
            )
            committed = loaded.mill_plants(mill_id)
            self.assertEqual(len(extracted), len(committed), mill_id)
            self.assertEqual(extracted[0]["slug"], committed[0].slug, mill_id)
            self.assertEqual(
                extracted[0]["payload"]["field"], committed[0].payload["field"], mill_id
            )
            compared += 1
        self.assertEqual(compared, len(SOURCE_MILLS))

    def test_tiny_source_ast_extract_skips_non_literal_pair(self):
        text = (FIXTURE / "tiny_source.py").read_text(encoding="utf-8")
        rows = catalog.ast_extract_plants(
            text,
            mill_id="kcl_r0001",
            path="tiny_source.py",
            base_round=1,
            shape="pair",
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["plant_id"], "kcl_r0001:fixture-leftover-field")
        self.assertNotIn("non-literal-skipped", [row["slug"] for row in rows])


class KclGenerateTests(unittest.TestCase):
    def test_row_plant_from_committed_catalog_builds(self):
        loaded = catalog.catalog_check(root=REPO)
        row = next(plant for plant in loaded.plants if plant.shape == "row")
        built = generate.build_pair(row)
        self.assertEqual(len(built.ok["steps"]), SUCCESS_STEPS)
        self.assertEqual(len(built.bad["steps"]), HANDOFF_STEPS)
        self.assertTrue(built.ok["id"].startswith(f"{FAMILY_PREFIX}-r"))

    def test_pair_without_embedded_hide_old_still_builds(self):
        loaded = catalog.catalog_check(root=REPO)
        plant = loaded.plant("kcl_r1007:readinessgate-miss")
        spec = catalog.spec_for(plant)
        self.assertNotIn(spec["hide_old"], spec["values_fail"])
        built = generate.build_pair(plant)
        self.assertEqual(len(built.ok["steps"]), SUCCESS_STEPS)
        self.assertEqual(built.ok["meta"]["mill_id"], "kcl_r1007")

    def test_fixture_pair_is_sixteen_plus_eighteen(self):
        loaded = catalog.load_catalog(FIXTURE)
        built = generate.build_pair(loaded.plants[0])
        self.assertEqual(built.ok["id"], "kcl-r1-fixture-leftover-field")
        self.assertEqual(built.bad["id"], "kcl-r1-fixture-leftover-field-n2-handoff")
        self.assertEqual(len(built.ok["steps"]), SUCCESS_STEPS)
        self.assertEqual(len(built.bad["steps"]), HANDOFF_STEPS)
        self.assertTrue(built.ok["reward"]["success"])
        self.assertFalse(built.bad["reward"]["success"])
        self.assertEqual(built.ok["meta"]["generator"], GENERATOR)
        self.assertNotEqual(built.ok["meta"]["generator"], "grok-4.6")
        self.assertEqual(classify_kind(built.ok), "episode")
        self.assertIn("Novel coverage:", built.notes)

    def test_generate_writes_a_new_tree_and_refuses_clobber(self):
        loaded = catalog.load_catalog(FIXTURE)
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "kcl-out"
            written = generate.generate(dest, catalog=loaded, plant_id=loaded.plants[0].plant_id)
            self.assertEqual(len(written), 1)
            batch = dest / "batch-r01.jsonl"
            notes = dest / "NOTES-r01.md"
            self.assertTrue(batch.is_file())
            self.assertTrue(notes.is_file())
            lines = batch.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 2)
            self.assertEqual(json.loads(lines[0])["id"], written[0].ok["id"])
            with self.assertRaises(KclRefusal) as raised:
                generate.generate(dest, catalog=loaded, plant_id=loaded.plants[0].plant_id)
            self.assertEqual(raised.exception.code, FINDING_DESTINATION_EXISTS)

    def test_generate_refuses_the_raw_tree(self):
        loaded = catalog.load_catalog(FIXTURE)
        with self.assertRaises(KclRefusal) as raised:
            generate.generate(
                DEFAULT_RAW_OUTPUT_ROOT / "kcl-forbidden",
                catalog=loaded,
                plant_id=loaded.plants[0].plant_id,
            )
        self.assertEqual(raised.exception.code, FINDING_DESTINATION_UNDER_RAW)


class KclHopperG46cTests(unittest.TestCase):
    def test_hop_replay_uses_hopper_g46c_api(self):
        table = pairs_by_factory(HOPPER_WAVE)
        factory = next(iter(table))
        slug = table[factory][0][0]["slug"]
        source = (KCL_DIR / "generate.py").read_text(encoding="utf-8")
        self.assertIn("start_by_factory", source)
        self.assertIn("pairs_by_factory", source)
        self.assertIn("emit_stage", source)
        self.assertNotIn("import hopper_mill", source)
        self.assertNotIn("from hopper_mill", source)
        self.assertNotIn("exec_module", source)
        self.assertNotIn("exec(", source)
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "hop-out"
            written = generate.hop_replay(dest, wave=HOPPER_WAVE, factory=factory, slug=slug)
            self.assertEqual(len(written), 1)
            self.assertEqual(written[0].factory, factory)
            batch = dest / factory / f"batch-r{written[0].round_n:02d}.jsonl"
            self.assertTrue(batch.is_file())
            first = json.loads(batch.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(first["id"], written[0].ids[0])
            self.assertEqual(first["meta"]["factory"], factory)

    def test_hop_replay_refuses_the_raw_tree(self):
        with self.assertRaises(KclRefusal) as raised:
            generate.hop_replay(DEFAULT_RAW_OUTPUT_ROOT / "kcl-hop-forbidden")
        self.assertEqual(raised.exception.code, FINDING_DESTINATION_UNDER_RAW)

    def test_hop_replay_refuses_an_unknown_wave(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "hop-bad-wave"
            with self.assertRaises(KclRefusal) as raised:
                generate.hop_replay(dest, wave="g46z")
            self.assertEqual(raised.exception.code, FINDING_UNKNOWN_WAVE)


class KclCliTests(unittest.TestCase):
    def test_catalog_check_cli(self):
        code, stdout, stderr = invoke(["catalog-check", "--json"])
        self.assertEqual(code, 0)
        payload = json.loads(stdout)
        self.assertEqual(payload["plants"], 705)
        self.assertEqual(payload["factory"], FACTORY)
        self.assertEqual(stderr, "")

    def test_generate_cli_one_plant(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "cli-out"
            code, stdout, _stderr = invoke(
                [
                    "generate",
                    "--catalog",
                    str(FIXTURE),
                    "--out",
                    str(dest),
                    "--plant",
                    "kcl_r0001:fixture-leftover-field",
                    "--json",
                ]
            )
            self.assertEqual(code, 0)
            payload = json.loads(stdout)
            self.assertEqual(payload["episodes"], 2)
            self.assertTrue((dest / "batch-r01.jsonl").is_file())

    def test_hop_replay_cli_one_g46c_slug(self):
        table = pairs_by_factory(HOPPER_WAVE)
        factory = next(iter(table))
        slug = table[factory][0][0]["slug"]
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "cli-hop"
            code, stdout, stderr = invoke(
                [
                    "hop-replay",
                    "--out",
                    str(dest),
                    "--wave",
                    HOPPER_WAVE,
                    "--factory",
                    factory,
                    "--slug",
                    slug,
                    "--json",
                ]
            )
            self.assertEqual(code, 0)
            self.assertEqual(stderr, "")
            payload = json.loads(stdout)
            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["wave"], HOPPER_WAVE)
            self.assertEqual(payload["pairs"], 1)


if __name__ == "__main__":
    unittest.main()
