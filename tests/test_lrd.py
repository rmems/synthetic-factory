#!/usr/bin/env python3
"""LRD mill package: catalog pins, AST extract, generate, CLI, no leftover mills."""

from __future__ import annotations

import ast
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
FIXTURE = REPO / "tests" / "fixtures" / "lrd"
COMMITTED = REPO / "config" / "lrd"

sys.path.insert(0, str(PIPELINES))

from mill_family import REVIEWED_MILL_PREFIX_HOMES, mill_prefix  # noqa: E402
from record_kind import classify_kind  # noqa: E402
from lrd import catalog, cli, generate  # noqa: E402
from lrd._contract import (  # noqa: E402
    CATALOG_ID,
    CATALOG_SLICE,
    EXTRACT_METHOD,
    FACTORY,
    FINDING_CATALOG_SHA256_MISMATCH,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_HOPPER_REFUSED,
    FINDING_LOOP_REFUSED,
    FINDING_PLANT_NOT_FOUND,
    FINDING_SOURCE_NOT_PARSEABLE,
    FINDING_USAGE,
    FULL_MILL_COUNTS,
    FULL_PLANT_COUNT,
    GENERATOR,
    LrdRefusal,
    PREFIX,
    SHAPE_LEGACY,
    SHAPE_LEFTOVER3,
    SOURCE_COMMIT,
    SOURCE_MILLS,
    SOURCE_MILL_ID,
    SOURCE_PATH,
    SOURCE_ROUND,
)

EXPECTED_SLUGS = (
    "otel-session-jwt",
    "vector-vrl-access-token",
    "fluentd-refresh-token",
    "promtail-password",
    "datadog-bearer",
    "newrelic-apikey-field",
    "splunk-hec-tokenfield",
    "grafana-agent-accesstoken",
    "cw-xamz-security-token",
    "es-ingest-refresh",
    "os-ingest-idtoken",
    "logstash-session-jwt",
    "rsyslog-authorization",
    "syslogng-session-token",
    "telegraf-cookie",
    "collectd-secret",
)

TINY_SOURCE = """
PAIRS = [
    dict(
        mod="otelsjwt",
        drop="otelstrace",
        stack="otel",
        field="session_jwt",
        naive="drop traces",
        conf="processor.yaml",
        conf2="pipeline.yaml",
        oldc="attributes: [http.url]",
        newc="attributes: []",
        old2="processors: [batch]",
        new2="processors: []",
        test="test_redact.py",
        ticket="OTEL-L6",
        slug="otel-session-jwt",
        fail="otel-drop-traces-handoff",
        domain="otel-leftover-session-jwt-vs-drop-traces",
    )
]
"""

HOPPER_SOURCE = """
def mill_and_publish():
    return None

def main():
    mill_and_publish()
"""


def invoke(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.run(argv)
    return code, out.getvalue(), err.getvalue()


def _legacy_source(relpath: str) -> str | None:
    for spec in (f"{SOURCE_COMMIT}:{relpath}", f"origin/legacy-mill-lane:{relpath}"):
        try:
            return subprocess.check_output(["git", "show", spec], text=True, cwd=REPO)
        except subprocess.CalledProcessError:
            continue
    return None


class CatalogLoading(unittest.TestCase):
    def test_committed_catalog_loads_representative_slice(self):
        loaded = catalog.load_catalog(COMMITTED)
        self.assertEqual(loaded.catalog_id, CATALOG_ID)
        self.assertEqual(loaded.factory, FACTORY)
        self.assertEqual(FACTORY, REVIEWED_MILL_PREFIX_HOMES[PREFIX])
        self.assertEqual(loaded.meta["slice"], CATALOG_SLICE)
        self.assertEqual(loaded.meta["full_plant_count"], FULL_PLANT_COUNT)
        self.assertEqual(len(loaded.plants), 23)
        self.assertEqual(len(loaded.mills), 8)
        self.assertEqual(len({plant.plant_id for plant in loaded.plants}), 23)
        legacy = [plant for plant in loaded.plants if plant.shape == SHAPE_LEGACY]
        self.assertEqual(len(legacy), 16)
        self.assertEqual([plant.slug for plant in legacy], list(EXPECTED_SLUGS))
        self.assertEqual(loaded.meta["source"]["method"], EXTRACT_METHOD)
        self.assertEqual(loaded.meta["source"]["commit"], SOURCE_COMMIT)
        self.assertEqual(
            tuple((mill.mill_id, mill.plant_count) for mill in loaded.mills),
            FULL_MILL_COUNTS,
        )
        self.assertEqual({plant.mill_id for plant in loaded.plants}, {item[0] for item in SOURCE_MILLS})
        hoppers = str(loaded.meta["source"]["excluded"]["hoppers"])
        self.assertIn("dpr-lrd-hopper-leftover3.py", hoppers)

    def test_fixture_catalog_is_one_pair(self):
        loaded = catalog.load_catalog(FIXTURE)
        self.assertEqual(loaded.catalog_id, "lrd-fixture-v1")
        self.assertEqual(len(loaded.plants), 1)
        self.assertEqual(loaded.plants[0].plant_id, "lrd_r0001:otel-session-jwt")
        self.assertEqual(loaded.plants[0].field, "session_jwt")

    def test_pin_mismatch_is_a_coded_refusal(self):
        root = Path(tempfile.mkdtemp(prefix="lrd-pin-"))
        self.addCleanup(shutil.rmtree, root, True)
        dest = root / "catalog"
        shutil.copytree(FIXTURE, dest)
        meta_path = dest / catalog.CATALOG_FILENAME
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["plants_sha256"] = "0" * 64
        meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        with self.assertRaises(LrdRefusal) as caught:
            catalog.load_catalog(dest)
        self.assertEqual(caught.exception.code, FINDING_CATALOG_SHA256_MISMATCH)

    def test_unknown_plant_is_a_coded_refusal(self):
        loaded = catalog.load_catalog(FIXTURE)
        with self.assertRaises(LrdRefusal) as caught:
            loaded.plant("lrd_r0001:missing")
        self.assertEqual(caught.exception.code, FINDING_PLANT_NOT_FOUND)


class AstExtract(unittest.TestCase):
    def test_plants_from_source_reads_dict_calls(self):
        rows = catalog.plants_from_source(
            TINY_SOURCE, mill_id="lrd_r0007", source="tiny_source.py"
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["plant_id"], "lrd_r0007:otel-session-jwt")
        self.assertEqual(rows[0]["base_round"], 7)
        self.assertEqual(rows[0]["ticket"], "OTEL-L6")
        self.assertEqual(rows[0]["naive"], "drop traces")

    def test_plants_from_source_refuses_a_non_literal_call(self):
        source = "PAIRS = [dict(slug=other())]\n"
        with self.assertRaises(LrdRefusal) as caught:
            catalog.plants_from_source(source, mill_id="lrd_r0001", source="bad.py")
        self.assertEqual(caught.exception.code, FINDING_SOURCE_NOT_PARSEABLE)

    def test_plants_from_source_refuses_hopper_by_name(self):
        with self.assertRaises(LrdRefusal) as caught:
            catalog.plants_from_source(
                TINY_SOURCE,
                mill_id="lrd_r0001",
                source="experiments/dpr-lrd-hopper-leftover3.py",
            )
        self.assertEqual(caught.exception.code, FINDING_HOPPER_REFUSED)

    def test_plants_from_source_refuses_hopper_by_def(self):
        with self.assertRaises(LrdRefusal) as caught:
            catalog.plants_from_source(
                HOPPER_SOURCE, mill_id="lrd_r0001", source="experiments/custom.py"
            )
        self.assertEqual(caught.exception.code, FINDING_HOPPER_REFUSED)

    def test_plants_from_source_refuses_a_loop(self):
        with self.assertRaises(LrdRefusal) as caught:
            catalog.plants_from_source(
                TINY_SOURCE,
                mill_id="lrd_r0001",
                source="experiments/lrd-loop-r81.py",
            )
        self.assertEqual(caught.exception.code, FINDING_LOOP_REFUSED)

    def test_ast_extract_plants_refuses_a_loop_on_leftover3(self):
        source = "PAIRS = [(OK(slug='a'), FAIL(slug='b'))]\n"
        with self.assertRaises(LrdRefusal) as caught:
            catalog.ast_extract_plants(
                source,
                mill_id="lrd_r0081",
                path="experiments/lrd-loop-r81.py",
                base_round=81,
                shape=SHAPE_LEFTOVER3,
            )
        self.assertEqual(caught.exception.code, FINDING_LOOP_REFUSED)

    def test_ast_extract_plants_refuses_hopper_by_def(self):
        source = (
            "def mill_and_publish():\n"
            "    return None\n"
            "PAIRS = [(OK(slug='a'), FAIL(slug='b'))]\n"
        )
        with self.assertRaises(LrdRefusal) as caught:
            catalog.ast_extract_plants(
                source,
                mill_id="lrd_r0067",
                path="experiments/custom.py",
                base_round=67,
                shape=SHAPE_LEFTOVER3,
            )
        self.assertEqual(caught.exception.code, FINDING_HOPPER_REFUSED)

    def test_committed_catalog_matches_legacy_ast(self):
        text = _legacy_source(SOURCE_PATH)
        if text is None:
            self.skipTest("lrd preserve blob is not fetched")
        ast.parse(text)
        rows = catalog.plants_from_source(
            text, mill_id=SOURCE_MILL_ID, source=SOURCE_PATH, base_round=SOURCE_ROUND
        )
        loaded = catalog.load_catalog(COMMITTED)
        legacy = [plant for plant in loaded.plants if plant.shape == SHAPE_LEGACY]
        self.assertEqual(len(rows), 16)
        for row, plant in zip(rows, legacy, strict=True):
            self.assertEqual(row["slug"], plant.slug)
            self.assertEqual(row["field"], plant.field)
            self.assertEqual(row["fail"], plant.fail)
            self.assertEqual(row["naive"], plant.naive)
            self.assertEqual(row["domain"], plant.domain)

    def test_all_legacy_mills_match_live_ast_extract(self):
        loaded = catalog.load_catalog(COMMITTED)
        compared = 0
        for mill_id, base_round, rel, shape in SOURCE_MILLS:
            source = _legacy_source(rel)
            if source is None:
                self.skipTest("legacy-mill-lane lrd sources are not available")
            extracted = catalog.ast_extract_plants(
                source, mill_id=mill_id, path=rel, base_round=base_round, shape=shape
            )
            full = dict(FULL_MILL_COUNTS)[mill_id]
            self.assertEqual(len(extracted), full, rel)
            committed = [plant for plant in loaded.plants if plant.mill_id == mill_id]
            self.assertGreaterEqual(len(committed), 1)
            first = extracted[0]
            self.assertEqual(committed[-1 if mill_id != "lrd_r157" else 0].slug, first["slug"])
            if shape == SHAPE_LEGACY:
                self.assertEqual(committed[0].shape, SHAPE_LEGACY)
            else:
                self.assertEqual(committed[-1].shape, shape)
                self.assertIsInstance(committed[-1].payload, dict)
            compared += 1
        self.assertEqual(compared, len(SOURCE_MILLS))

    def test_leftover3_idtoken_expands_p_calls(self):
        source = _legacy_source("experiments/lrd-mill-leftover3-idtoken.py")
        if source is None:
            self.skipTest("idtoken blob is not fetched")
        rows = catalog.ast_extract_plants(
            source,
            mill_id="lrd_r123",
            path="experiments/lrd-mill-leftover3-idtoken.py",
            base_round=123,
            shape="p_idtoken",
        )
        self.assertEqual(len(rows), 16)
        self.assertEqual(rows[0]["shape"], "p_idtoken")
        self.assertIn("idtoken", rows[0]["slug"])

    def test_archive_hopper_blob_is_refused(self):
        try:
            text = subprocess.check_output(
                ["git", "show", "origin/legacy-mill-lane:experiments/dpr-lrd-hopper-leftover3.py"],
                cwd=REPO,
                text=True,
                stderr=subprocess.DEVNULL,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.skipTest("dpr-lrd-hopper blob is not fetched")
        ast.parse(text)
        with self.assertRaises(LrdRefusal) as caught:
            catalog.plants_from_source(
                text,
                mill_id="lrd_r0001",
                source="experiments/dpr-lrd-hopper-leftover3.py",
            )
        self.assertEqual(caught.exception.code, FINDING_HOPPER_REFUSED)

    def test_package_tree_has_no_vendored_mills_loops_or_hoppers(self):
        package = PIPELINES / "lrd"
        hits = list(package.rglob("*leftover*_mill.py"))
        self.assertEqual(hits, [])
        self.assertEqual(list((REPO / "config" / "lrd").rglob("*leftover*_mill.py")), [])
        self.assertEqual(list(package.rglob("*mill*.py")), [])
        self.assertEqual(list(package.rglob("*hopper*")), [])
        self.assertEqual(list(package.rglob("*loop*")), [])
        names = tuple(sorted(path.name for path in package.iterdir() if path.suffix == ".py"))
        self.assertEqual(
            names,
            ("__init__.py", "_contract.py", "catalog.py", "catalog_extract.py", "cli.py", "generate.py"),
        )


class GeneratePairs(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="lrd-gen-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_fixture_pair_is_an_episode_and_not_a_hopper(self):
        dest = self.root / "out"
        request = generate.GenerateRequest(
            FIXTURE, dest, plant_id="lrd_r0001:otel-session-jwt", round=3
        )
        summary = generate.run(request)
        self.assertEqual(summary["records"], 2)
        self.assertEqual(summary["pairs"], 1)
        self.assertEqual(summary["factory"], FACTORY)
        self.assertEqual(summary["generator"], GENERATOR)
        lines = (dest / generate.RECORDS_FILENAME).read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2)
        ok = json.loads(lines[0])
        fail = json.loads(lines[1])
        self.assertEqual(classify_kind(ok), "episode")
        self.assertEqual(classify_kind(fail), "episode")
        self.assertEqual(ok["id"], "lrd-r3-otel-session-jwt")
        self.assertEqual(fail["id"], "lrd-r3-otel-drop-traces-handoff")
        self.assertEqual(mill_prefix(ok), "lrd")
        self.assertEqual(len(ok["steps"]), 16)
        self.assertEqual(len(fail["steps"]), 17)
        self.assertTrue(ok["reward"]["success"])
        self.assertFalse(fail["reward"]["success"])
        self.assertEqual(ok["meta"]["factory"], FACTORY)

    def test_leftover3_plant_generate_is_refused(self):
        loaded = catalog.load_catalog(COMMITTED)
        sample = next(plant for plant in loaded.plants if plant.shape == SHAPE_LEFTOVER3)
        dest = self.root / "leftover3-out"
        with self.assertRaises(LrdRefusal) as caught:
            generate.run(
                generate.GenerateRequest(
                    COMMITTED, dest, plant_id=sample.plant_id, round=sample.base_round
                )
            )
        self.assertEqual(caught.exception.code, FINDING_USAGE)
        self.assertFalse(dest.exists())

    def test_destination_under_raw_is_refused(self):
        dest = REPO / "outputs" / "raw" / "lrd-must-not-write"
        with self.assertRaises(LrdRefusal) as caught:
            generate.run(generate.GenerateRequest(FIXTURE, dest, all_plants=True))
        self.assertEqual(caught.exception.code, FINDING_DESTINATION_UNDER_RAW)
        self.assertFalse(dest.exists())

    def test_existing_destination_is_refused(self):
        dest = self.root / "exists"
        dest.mkdir()
        with self.assertRaises(LrdRefusal) as caught:
            generate.run(
                generate.GenerateRequest(FIXTURE, dest, plant_id="lrd_r0001:otel-session-jwt")
            )
        self.assertEqual(caught.exception.code, FINDING_DESTINATION_EXISTS)

    def test_refuse_hopper_exec_seam(self):
        with self.assertRaises(LrdRefusal) as caught:
            generate.refuse_hopper_exec("dpr-lrd-hopper-leftover3")
        self.assertEqual(caught.exception.code, FINDING_HOPPER_REFUSED)


class Cli(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="lrd-cli-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_catalog_check_json_on_the_fixture(self):
        code, out, err = invoke(["catalog-check", "--catalog", str(FIXTURE), "--json"])
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["plants"], 1)
        self.assertEqual(payload["findings"], [])

    def test_audit_json_is_clean(self):
        code, out, err = invoke(["audit", "--catalog", str(FIXTURE), "--json"])
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["findings"], [])

    def test_generate_json_writes_the_pair(self):
        dest = self.root / "cli-out"
        code, out, err = invoke(
            [
                "generate",
                "--catalog",
                str(FIXTURE),
                "--out",
                str(dest),
                "--plant",
                "lrd_r0001:otel-session-jwt",
                "--json",
            ]
        )
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["summary"]["records"], 2)
        self.assertTrue((dest / generate.RECORDS_FILENAME).is_file())

    def test_missing_catalog_is_exit_two_and_json_on_stdout(self):
        code, out, err = invoke(["catalog-check", "--catalog", "/nonexistent/lrd", "--json"])
        self.assertEqual((code, err), (2, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "refused")
        self.assertEqual(payload["code"], "CATALOG_FILE_MISSING")


class ImportTwins(unittest.TestCase):
    def test_flat_and_package_catalog_are_one_object(self):
        if str(REPO) not in sys.path:
            sys.path.insert(0, str(REPO))
        import pipelines.lrd.catalog as packaged

        self.assertIs(packaged, catalog)


class PackageSurface(unittest.TestCase):
    def test_package_modules_do_not_import_subprocess_or_hopper(self):
        package = PIPELINES / "lrd"
        banned = {"subprocess", "hopper"}
        for path in sorted(package.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertNotIn(alias.name.split(".")[0], banned, path.name)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    self.assertNotIn(node.module.split(".")[0], banned, path.name)
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self.assertNotIn(node.name, {"txn", "mill_and_publish"}, path.name)


if __name__ == "__main__":
    unittest.main()
