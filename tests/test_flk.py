#!/usr/bin/env python3
"""FLK mill package: catalog pins, AST extract, generate, CLI, no leftover mills."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
FIXTURE = REPO / "tests" / "fixtures" / "flk"
COMMITTED = REPO / "config" / "flk"

sys.path.insert(0, str(PIPELINES))

from flk import catalog, cli, generate  # noqa: E402
from flk._contract import (  # noqa: E402
    FACTORY,
    FINDING_CATALOG_SHA256_MISMATCH,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_PLANT_NOT_FOUND,
    FINDING_SOURCE_NOT_PARSEABLE,
    FINDING_USAGE,
    FlkRefusal,
    GENERATOR,
)
from record_kind import classify_kind  # noqa: E402
from validate_run import check_episode  # noqa: E402

TINY_SOURCE = """
from pathlib import Path
HOP = [Path("/tmp/other-factory")]
BASE = 7
PLANTS = [
    {
        "slug": "tiny-clock-leftover",
        "runner": "pytest",
        "drop": "drop -n auto",
        "cause": "clock",
        "cmd": "pytest -n 2 t.py",
        "drop_cmd": "pytest t.py",
        "file": "t.py",
        "src": "src.py",
        "mut": "test_mut",
        "ok": "test_ok",
        "leftover": "clock leftover",
        "assign": "time.time = lambda: 0",
        "isolate": "freeze_time",
        "naive": "skip",
        "ci": "ci.yml",
        "ticket": "FLK-TINY",
    }
]
"""


def invoke(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.run(argv)
    return code, out.getvalue(), err.getvalue()


class CatalogLoading(unittest.TestCase):
    def test_committed_catalog_loads_eighty_ast_extracted_plants(self):
        loaded = catalog.load_catalog(COMMITTED)
        self.assertEqual(loaded.catalog_id, "flk-plants-v1")
        self.assertEqual(loaded.factory, FACTORY)
        self.assertEqual(len(loaded.plants), 80)
        self.assertEqual(len(loaded.mills), 5)
        self.assertEqual(len({plant.plant_id for plant in loaded.plants}), 80)
        self.assertEqual(loaded.meta["source"]["method"], "git-show+ast.parse")
        self.assertEqual(
            loaded.meta["source"]["commit"],
            "813f93f1969c1c4421e5663492e9663739efa642",
        )
        self.assertEqual(
            [mill.mill_id for mill in loaded.mills],
            ["flk_r1489", "flk_r1505", "flk_r1521", "flk_r1544", "flk_r1560"],
        )

    def test_fixture_catalog_is_one_plant(self):
        loaded = catalog.load_catalog(FIXTURE)
        self.assertEqual(loaded.catalog_id, "flk-fixture-v1")
        self.assertEqual(len(loaded.plants), 1)
        self.assertEqual(loaded.plants[0].plant_id, "flk_r0001:pytest-clock-leftover")

    def test_pin_mismatch_is_a_coded_refusal(self):
        root = Path(tempfile.mkdtemp(prefix="flk-pin-"))
        self.addCleanup(shutil.rmtree, root, True)
        dest = root / "catalog"
        shutil.copytree(FIXTURE, dest)
        meta_path = dest / catalog.CATALOG_FILENAME
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["plants_sha256"] = "0" * 64
        meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        with self.assertRaises(FlkRefusal) as caught:
            catalog.load_catalog(dest)
        self.assertEqual(caught.exception.code, FINDING_CATALOG_SHA256_MISMATCH)

    def test_unknown_plant_is_a_coded_refusal(self):
        loaded = catalog.load_catalog(FIXTURE)
        with self.assertRaises(FlkRefusal) as caught:
            loaded.plant("flk_r0001:missing")
        self.assertEqual(caught.exception.code, FINDING_PLANT_NOT_FOUND)


class AstExtract(unittest.TestCase):
    def test_plants_from_source_reads_literals_and_skips_hop(self):
        rows = catalog.plants_from_source(
            TINY_SOURCE, mill_id="flk_r0007", source="tiny_source.py"
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["plant_id"], "flk_r0007:tiny-clock-leftover")
        self.assertEqual(rows[0]["base_round"], 7)
        self.assertEqual(rows[0]["ticket"], "FLK-TINY")
        self.assertNotIn("HOP", rows[0])

    def test_plants_from_source_refuses_a_call_in_plants(self):
        source = "PLANTS = [dict(slug='x')]\n"
        with self.assertRaises(FlkRefusal) as caught:
            catalog.plants_from_source(source, mill_id="flk_r0001", source="bad.py")
        self.assertEqual(caught.exception.code, FINDING_SOURCE_NOT_PARSEABLE)

    def test_package_tree_has_no_leftover_mill_scripts(self):
        hits = list((PIPELINES / "flk").rglob("*leftover*_mill.py"))
        self.assertEqual(hits, [])
        self.assertEqual(list((REPO / "config" / "flk").rglob("*leftover*_mill.py")), [])


class GeneratePairs(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="flk-gen-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_fixture_pair_is_an_episode_and_not_hosted_grok(self):
        dest = self.root / "out"
        request = generate.GenerateRequest(
            FIXTURE, dest, plant_id="flk_r0001:pytest-clock-leftover", round=3
        )
        summary = generate.run(request)
        self.assertEqual(summary["records"], 2)
        self.assertEqual(summary["pairs"], 1)
        self.assertEqual(summary["generator"], GENERATOR)
        lines = (dest / generate.RECORDS_FILENAME).read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2)
        ok, bad = [json.loads(line) for line in lines]
        self.assertEqual(ok["id"], "flk-r0003-pytest-clock-leftover-q")
        self.assertEqual(bad["id"], "flk-r0003-pytest-clock-leftover-handoff")
        self.assertEqual(classify_kind(ok), "episode")
        self.assertEqual(classify_kind(bad), "episode")
        self.assertEqual(check_episode(ok, "ok"), [])
        self.assertEqual(check_episode(bad, "bad"), [])
        self.assertEqual(ok["meta"]["factory"], FACTORY)
        self.assertEqual(ok["meta"]["generator"], GENERATOR)
        self.assertNotEqual(ok["meta"]["generator"], "grok-4.6")
        self.assertTrue(ok["reward"]["success"])
        self.assertEqual(ok["reward"]["skip_rejected"], 1)
        self.assertFalse(bad["reward"]["success"])
        self.assertEqual(bad["reward"]["handoff"], 1)
        notes = (dest / generate.NOTES_FILENAME).read_text(encoding="utf-8")
        self.assertIn("Novel coverage: 91%", notes)

    def test_existing_destination_is_refused(self):
        dest = self.root / "exists"
        dest.mkdir()
        with self.assertRaises(FlkRefusal) as caught:
            generate.run(generate.GenerateRequest(FIXTURE, dest, all_plants=True))
        self.assertEqual(caught.exception.code, FINDING_DESTINATION_EXISTS)

    def test_destination_under_raw_is_refused(self):
        dest = self.root / "outputs" / "raw" / "flk-out"
        with self.assertRaises(FlkRefusal) as caught:
            generate.run(generate.GenerateRequest(FIXTURE, dest, all_plants=True))
        self.assertEqual(caught.exception.code, FINDING_DESTINATION_UNDER_RAW)
        self.assertFalse(dest.exists())

    def test_generate_requires_exactly_one_selector(self):
        dest = self.root / "none"
        with self.assertRaises(FlkRefusal) as caught:
            generate.run(generate.GenerateRequest(FIXTURE, dest))
        self.assertEqual(caught.exception.code, FINDING_USAGE)

    def test_call_style_assign_without_equals_emits_handoff(self):
        loaded = catalog.load_catalog(COMMITTED)
        plant = loaded.plant("flk_r1489:junit-fsorder-leftover")
        self.assertNotIn("=", plant.assign)
        dest = self.root / "call-style"
        summary = generate.run(
            generate.GenerateRequest(COMMITTED, dest, plant_id=plant.plant_id)
        )
        self.assertEqual(summary["records"], 2)
        lines = (dest / generate.RECORDS_FILENAME).read_text(encoding="utf-8").splitlines()
        bad = json.loads(lines[1])
        self.assertEqual(classify_kind(bad), "episode")
        self.assertEqual(check_episode(bad, "bad"), [])
        pattern = bad["steps"][8]["tool_call"]["args"]["pattern"]
        self.assertTrue(pattern.startswith("Files.list"))

    def test_records_digest_matches_on_disk_bytes_when_linesep_is_crlf(self):
        dest = self.root / "lf-records"
        with patch("os.linesep", "\r\n"):
            summary = generate.run(
                generate.GenerateRequest(
                    FIXTURE, dest, plant_id="flk_r0001:pytest-clock-leftover"
                )
            )
        payload = (dest / generate.RECORDS_FILENAME).read_bytes()
        self.assertNotIn(b"\r\n", payload)
        self.assertEqual(hashlib.sha256(payload).hexdigest(), summary["records_sha256"])


class CliSurface(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="flk-cli-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_catalog_check_json_on_the_fixture(self):
        code, out, err = invoke(["catalog-check", "--catalog", str(FIXTURE), "--json"])
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["plants"], 1)
        self.assertEqual(payload["findings"], [])

    def test_generate_json_writes_the_pair(self):
        dest = self.root / "cli-out"
        code, out, err = invoke([
            "generate", "--catalog", str(FIXTURE), "--out", str(dest),
            "--plant", "flk_r0001:pytest-clock-leftover", "--json",
        ])
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["summary"]["records"], 2)
        self.assertTrue((dest / generate.RECORDS_FILENAME).is_file())

    def test_missing_catalog_is_exit_two_and_json_on_stdout(self):
        code, out, err = invoke(["catalog-check", "--catalog", "/nonexistent/flk", "--json"])
        self.assertEqual((code, err), (2, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "refused")
        self.assertTrue(payload["code"].startswith("flk."))


class ImportTwins(unittest.TestCase):
    def test_flat_and_package_catalog_are_one_object(self):
        if str(REPO) not in sys.path:
            sys.path.insert(0, str(REPO))
        import pipelines.flk.catalog as packaged

        self.assertIs(packaged, catalog)


if __name__ == "__main__":
    unittest.main()
