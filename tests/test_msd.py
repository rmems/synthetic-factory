#!/usr/bin/env python3
"""MSD mill package: catalog pins, AST extract, generate, CLI, no leftover mills."""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
FIXTURE = REPO / "tests" / "fixtures" / "msd"
COMMITTED = REPO / "config" / "msd"

sys.path.insert(0, str(PIPELINES))

from msd import catalog, cli, generate  # noqa: E402
from msd._contract import (  # noqa: E402
    FACTORY,
    FINDING_CATALOG_SHA256_MISMATCH,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_PLANT_NOT_FOUND,
    FINDING_SOURCE_NOT_PARSEABLE,
    FINDING_USAGE,
    GENERATOR,
    MsdRefusal,
)
from record_kind import classify_kind  # noqa: E402
from validate_run import check_episode  # noqa: E402

TINY_R430 = """
OWN_FAMILIES = ("http-202-notify",)
START = 7
PAIRS = [
    (
        P(
            slug="tiny-http-202",
            repo="repo-mcp",
            method="notifications/initialized",
            leftover="POST 200 empty {}",
            spec="202 Accepted empty body",
            keep="method",
            deadend="return 204",
            extra="Retry-After",
            freeze_still="host still 200 {}",
            not_r="r388 clone",
            adapt_cmd="Return 202",
            canon="CanonH2n",
            pfx="h2n",
            grep="202 Accepted",
            ticket="CT-TINY-202",
            family="http-202-notify",
            schema_note="# 202 notify",
        ),
        P(
            slug="tiny-get-405",
            repo="llm-mcp",
            method="GET /mcp",
            leftover="GET /mcp 404",
            spec="405 Method Not Allowed",
            keep="Allow POST",
            deadend="return 200 SSE",
            extra="Retry-After",
            freeze_still="host still GET 404",
            not_r="r404 clone",
            adapt_cmd="Return 405",
            canon="CanonG405",
            pfx="g405",
            grep="405 Method",
            ticket="CT-TINY-405",
            family="http-202-notify",
            schema_note="# GET 405",
        ),
    )
]
"""

TINY_R747 = """
START = 9
PAIRS = [
    dict(
        slug="tiny-tools-list",
        old="tools/list omitted outputSchema",
        new="tools/list Tool.outputSchema required",
        keep="name",
        dead="ignore outputSchema",
        residual="extra annotations",
        extra="annotations",
        freeze="host still content[] only",
        family="tools/list vs tools/call",
        reject="do not ignore outputSchema",
        method="tools/list",
        peer="tools/call",
        ticket="CT-TINY-747",
        canon="CanonW800",
        wid="w800",
        test_ok="test_w800_ok",
        falseg="test_extra_annotations_allowed",
        map_fn="m.setdefault('outputSchema', {'type':'object'})",
        success=True,
    )
]
"""


def invoke(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.run(argv)
    return code, out.getvalue(), err.getvalue()


class CatalogLoading(unittest.TestCase):
    def test_committed_catalog_loads_ninety_two_ast_extracted_plants(self):
        loaded = catalog.load_catalog(COMMITTED)
        self.assertEqual(loaded.catalog_id, "msd-plants-v1")
        self.assertEqual(loaded.factory, FACTORY)
        self.assertEqual(len(loaded.plants), 92)
        self.assertEqual(len(loaded.mills), 2)
        self.assertEqual(len({plant.plant_id for plant in loaded.plants}), 92)
        self.assertEqual(loaded.meta["source"]["method"], "git-show+ast.parse")
        self.assertEqual(
            loaded.meta["source"]["commit"],
            "813f93f1969c1c4421e5663492e9663739efa642",
        )
        self.assertEqual(
            [mill.mill_id for mill in loaded.mills],
            ["msd_r430", "msd_r747"],
        )
        self.assertEqual(
            loaded.meta["source"]["scripts"],
            [
                "experiments/msd-leftover-mill-r430.py",
                "experiments/msd_r747_leftover3_mill.py",
            ],
        )

    def test_fixture_catalog_is_one_plant(self):
        loaded = catalog.load_catalog(FIXTURE)
        self.assertEqual(loaded.catalog_id, "msd-fixture-v1")
        self.assertEqual(len(loaded.plants), 1)
        self.assertEqual(loaded.plants[0].plant_id, "msd_r0001:http-notify-202-empty-body")

    def test_pin_mismatch_is_a_coded_refusal(self):
        root = Path(tempfile.mkdtemp(prefix="msd-pin-"))
        self.addCleanup(shutil.rmtree, root, True)
        dest = root / "catalog"
        shutil.copytree(FIXTURE, dest)
        meta_path = dest / catalog.CATALOG_FILENAME
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["plants_sha256"] = "0" * 64
        meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        with self.assertRaises(MsdRefusal) as caught:
            catalog.load_catalog(dest)
        self.assertEqual(caught.exception.code, FINDING_CATALOG_SHA256_MISMATCH)

    def test_unknown_plant_is_a_coded_refusal(self):
        loaded = catalog.load_catalog(FIXTURE)
        with self.assertRaises(MsdRefusal) as caught:
            loaded.plant("msd_r0001:missing")
        self.assertEqual(caught.exception.code, FINDING_PLANT_NOT_FOUND)


class AstExtract(unittest.TestCase):
    def test_plants_from_source_reads_p_call_pairs_and_skips_hop(self):
        rows = catalog.plants_from_source(
            TINY_R430, mill_id="msd_r0007", source="tiny_r430.py"
        )
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["plant_id"], "msd_r0007:tiny-http-202")
        self.assertEqual(rows[0]["base_round"], 7)
        self.assertEqual(rows[0]["ticket"], "CT-TINY-202")
        self.assertEqual(rows[1]["slug"], "tiny-get-405")
        self.assertNotIn("HOP", rows[0])

    def test_plants_from_source_reads_dict_calls(self):
        rows = catalog.plants_from_source(
            TINY_R747, mill_id="msd_r0009", source="tiny_r747.py"
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["plant_id"], "msd_r0009:tiny-tools-list")
        self.assertEqual(rows[0]["leftover"], "tools/list omitted outputSchema")
        self.assertEqual(rows[0]["spec"], "tools/list Tool.outputSchema required")
        self.assertEqual(rows[0]["pfx"], "w800")
        self.assertEqual(rows[0]["repo"], "repo-mcp")
        self.assertEqual(rows[0]["adapt_cmd"], "do not ignore outputSchema")

    def test_plants_from_source_refuses_a_call_in_plants(self):
        source = "PLANTS = [dict(slug='x')]\n"
        with self.assertRaises(MsdRefusal) as caught:
            catalog.plants_from_source(source, mill_id="msd_r0001", source="bad.py")
        self.assertEqual(caught.exception.code, FINDING_SOURCE_NOT_PARSEABLE)

    def test_loop_script_is_not_a_catalog_source(self):
        loop = (
            "HOP = 'graphql-nplusone-factory'\n"
            "def main():\n"
            "    import mill\n"
        )
        with self.assertRaises(MsdRefusal) as caught:
            catalog.plants_from_source(loop, mill_id="msd_r0430", source="loop.py")
        self.assertEqual(caught.exception.code, FINDING_SOURCE_NOT_PARSEABLE)

    def test_package_tree_has_no_leftover_mill_scripts(self):
        hits = list((PIPELINES / "msd").rglob("*leftover*_mill.py"))
        hits += list((PIPELINES / "msd").rglob("*leftover-loop*.py"))
        self.assertEqual(hits, [])
        self.assertEqual(list((REPO / "config" / "msd").rglob("*leftover*_mill.py")), [])


class GeneratePairs(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="msd-gen-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_fixture_pair_is_an_episode_and_not_hosted_grok(self):
        dest = self.root / "out"
        request = generate.GenerateRequest(
            FIXTURE, dest, plant_id="msd_r0001:http-notify-202-empty-body", round=3
        )
        summary = generate.run(request)
        self.assertEqual(summary["records"], 2)
        self.assertEqual(summary["pairs"], 1)
        self.assertEqual(summary["generator"], GENERATOR)
        lines = (dest / generate.RECORDS_FILENAME).read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2)
        ok, bad = [json.loads(line) for line in lines]
        self.assertEqual(ok["id"], "msd-r0003-http-notify-202-empty-body-q")
        self.assertEqual(bad["id"], "msd-r0003-http-notify-202-empty-body-handoff")
        self.assertEqual(classify_kind(ok), "episode")
        self.assertEqual(classify_kind(bad), "episode")
        self.assertEqual(check_episode(ok, "ok"), [])
        self.assertEqual(check_episode(bad, "bad"), [])
        self.assertEqual(ok["meta"]["factory"], FACTORY)
        self.assertEqual(ok["meta"]["generator"], GENERATOR)
        self.assertNotEqual(ok["meta"]["generator"], "grok-4.6")
        self.assertTrue(ok["reward"]["success"])
        self.assertEqual(ok["reward"]["deadend_rejected"], 1)
        self.assertFalse(bad["reward"]["success"])
        self.assertEqual(bad["reward"]["handoff"], 1)
        self.assertNotIn("thought", json.dumps(ok))
        notes = (dest / generate.NOTES_FILENAME).read_text(encoding="utf-8")
        self.assertIn("Novel coverage: 82%", notes)
        self.assertNotIn("graphql-nplusone-factory", json.dumps(ok))

    def test_committed_r430_plant_pair_is_an_episode(self):
        dest = self.root / "committed"
        request = generate.GenerateRequest(
            COMMITTED,
            dest,
            plant_id="msd_r430:http-notify-202-empty-body",
            round=430,
        )
        summary = generate.run(request)
        self.assertEqual(summary["records"], 2)
        ok, bad = [
            json.loads(line)
            for line in (dest / generate.RECORDS_FILENAME).read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(classify_kind(ok), "episode")
        self.assertEqual(check_episode(ok, "ok"), [])
        self.assertEqual(check_episode(bad, "bad"), [])
        self.assertEqual(ok["meta"]["generator"], GENERATOR)
        self.assertEqual(len(ok["steps"]), 16)
        self.assertEqual(len(bad["steps"]), 17)

    def test_existing_destination_is_refused(self):
        dest = self.root / "exists"
        dest.mkdir()
        with self.assertRaises(MsdRefusal) as caught:
            generate.run(generate.GenerateRequest(FIXTURE, dest, all_plants=True))
        self.assertEqual(caught.exception.code, FINDING_DESTINATION_EXISTS)

    def test_destination_under_raw_is_refused(self):
        dest = self.root / "outputs" / "raw" / "msd-out"
        with self.assertRaises(MsdRefusal) as caught:
            generate.run(generate.GenerateRequest(FIXTURE, dest, all_plants=True))
        self.assertEqual(caught.exception.code, FINDING_DESTINATION_UNDER_RAW)
        self.assertFalse(dest.exists())

    def test_generate_requires_exactly_one_selector(self):
        dest = self.root / "none"
        with self.assertRaises(MsdRefusal) as caught:
            generate.run(generate.GenerateRequest(FIXTURE, dest))
        self.assertEqual(caught.exception.code, FINDING_USAGE)


class CliSurface(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="msd-cli-"))
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
            "--plant", "msd_r0001:http-notify-202-empty-body", "--json",
        ])
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["summary"]["records"], 2)
        self.assertTrue((dest / generate.RECORDS_FILENAME).is_file())

    def test_missing_catalog_is_exit_two_and_json_on_stdout(self):
        code, out, err = invoke(["catalog-check", "--catalog", "/nonexistent/msd", "--json"])
        self.assertEqual((code, err), (2, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "refused")
        self.assertTrue(payload["code"].startswith("msd."))


class ImportTwins(unittest.TestCase):
    def test_flat_and_package_catalog_are_one_object(self):
        if str(REPO) not in sys.path:
            sys.path.insert(0, str(REPO))
        import pipelines.msd.catalog as packaged

        self.assertIs(packaged, catalog)


if __name__ == "__main__":
    unittest.main()
