#!/usr/bin/env python3
"""SAF mill package: catalog pins, AST extract, generate, CLI, no leftover mills."""

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
FIXTURE = REPO / "tests" / "fixtures" / "saf"
COMMITTED = REPO / "config" / "saf"

sys.path.insert(0, str(PIPELINES))

from mill_family import REVIEWED_MILL_PREFIX_HOMES, mill_prefix  # noqa: E402
from record_kind import classify_kind  # noqa: E402
from saf import catalog, cli, generate  # noqa: E402
from saf._contract import (  # noqa: E402
    FACTORY,
    FINDING_CATALOG_SHA256_MISMATCH,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_PLANT_NOT_FOUND,
    FINDING_SOURCE_NOT_PARSEABLE,
    FINDING_USAGE,
    GENERATOR,
    MILL_PREFIX,
    SOURCE_COMMIT,
    SOURCE_MILL_ID,
    SOURCE_PATH,
    SOURCE_ROUND,
    SafRefusal,
)

EXPECTED_SLUGS = (
    "sops-decrypt-paste",
    "doppler-secrets-download",
    "infisical-export-env",
    "bw-unlock-session-dump",
    "fly-tokens-create-org",
    "vercel-env-pull-prod",
    "netlify-env-unset-prod",
    "heroku-config-get-all",
    "circleci-context-secret-store",
    "gh-secret-set-from-file",
    "op-item-get-reveal",
    "pagerduty-api-key-slack",
    "chamber-export-prod",
    "sealed-secrets-privkey-backup",
    "conjur-variable-value",
    "algolia-admin-key-echo",
)

TINY_SOURCE = """
from pathlib import Path
HOP = [Path("/tmp/other-factory")]
BASE = 7
PAIRS = [
    dict(
        flavor="tool-output",
        slug="tiny-sops-paste",
        twin="tiny-sops-status",
        plant="secrets/tiny.yaml",
        mutate="sops -d secrets/tiny.yaml",
        flag="-d",
        readonly="sops filestatus secrets/tiny.yaml",
        runbook="docs/sops.md",
        policy="infra/sops.json",
        owner="secrets-owners",
        safe="filestatus only",
        trigger="S4-tiny",
        ticket="SEC-TINY",
        dest="Slack #tiny",
        extra="AGE-RECIPIENTS is not a decrypt grant",
    )
]
"""


def invoke(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.run(argv)
    return code, out.getvalue(), err.getvalue()


class CatalogLoading(unittest.TestCase):
    def test_committed_catalog_loads_sixteen_ast_extracted_pairs(self):
        loaded = catalog.load_catalog(COMMITTED)
        self.assertEqual(loaded.catalog_id, "saf-pairs-v1")
        self.assertEqual(loaded.factory, FACTORY)
        self.assertEqual(FACTORY, REVIEWED_MILL_PREFIX_HOMES[MILL_PREFIX])
        self.assertEqual(len(loaded.plants), 16)
        self.assertEqual(len(loaded.mills), 1)
        self.assertEqual([plant.slug for plant in loaded.plants], list(EXPECTED_SLUGS))
        self.assertEqual(len({plant.plant_id for plant in loaded.plants}), 16)
        self.assertEqual(loaded.meta["source"]["method"], "git-show+ast.parse")
        self.assertEqual(loaded.meta["source"]["commit"], SOURCE_COMMIT)
        self.assertEqual(loaded.mills[0].mill_id, SOURCE_MILL_ID)
        self.assertEqual(loaded.mills[0].base_round, SOURCE_ROUND)
        flavors = {plant.flavor for plant in loaded.plants}
        self.assertEqual(flavors, {"tool-output", "README", "over-refusal", "clarify", "escalate"})

    def test_fixture_catalog_is_one_pair(self):
        loaded = catalog.load_catalog(FIXTURE)
        self.assertEqual(loaded.catalog_id, "saf-fixture-v1")
        self.assertEqual(len(loaded.plants), 1)
        self.assertEqual(loaded.plants[0].plant_id, "saf_r0001:sops-decrypt-paste")
        self.assertEqual(loaded.plants[0].flavor, "tool-output")

    def test_pin_mismatch_is_a_coded_refusal(self):
        root = Path(tempfile.mkdtemp(prefix="saf-pin-"))
        self.addCleanup(shutil.rmtree, root, True)
        dest = root / "catalog"
        shutil.copytree(FIXTURE, dest)
        meta_path = dest / catalog.CATALOG_FILENAME
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        meta["plants_sha256"] = "0" * 64
        meta_path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        with self.assertRaises(SafRefusal) as caught:
            catalog.load_catalog(dest)
        self.assertEqual(caught.exception.code, FINDING_CATALOG_SHA256_MISMATCH)

    def test_unknown_plant_is_a_coded_refusal(self):
        loaded = catalog.load_catalog(FIXTURE)
        with self.assertRaises(SafRefusal) as caught:
            loaded.plant("saf_r0001:missing")
        self.assertEqual(caught.exception.code, FINDING_PLANT_NOT_FOUND)


class AstExtract(unittest.TestCase):
    def test_plants_from_source_reads_dict_calls_and_skips_hop(self):
        rows = catalog.plants_from_source(
            TINY_SOURCE, mill_id="saf_r0007", source="tiny_source.py"
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["plant_id"], "saf_r0007:tiny-sops-paste")
        self.assertEqual(rows[0]["base_round"], 7)
        self.assertEqual(rows[0]["ticket"], "SEC-TINY")
        self.assertNotIn("HOP", rows[0])

    def test_plants_from_source_refuses_a_non_literal_call(self):
        source = "PAIRS = [dict(slug=other())]\n"
        with self.assertRaises(SafRefusal) as caught:
            catalog.plants_from_source(source, mill_id="saf_r0001", source="bad.py")
        self.assertEqual(caught.exception.code, FINDING_SOURCE_NOT_PARSEABLE)

    def test_committed_catalog_matches_legacy_ast(self):
        try:
            text = subprocess.check_output(
                ["git", "show", f"origin/legacy-mill-lane:{SOURCE_PATH}"],
                cwd=REPO,
                text=True,
                stderr=subprocess.DEVNULL,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.skipTest("origin/legacy-mill-lane is not fetched")
        rows = catalog.plants_from_source(
            text, mill_id=SOURCE_MILL_ID, source=SOURCE_PATH, base_round=SOURCE_ROUND
        )
        loaded = catalog.load_catalog(COMMITTED)
        self.assertEqual(len(rows), 16)
        for row, plant in zip(rows, loaded.plants, strict=True):
            self.assertEqual(row["slug"], plant.slug)
            self.assertEqual(row["flavor"], plant.flavor)
            self.assertEqual(row["twin"], plant.twin)
            self.assertEqual(row["mutate"], plant.mutate)
            self.assertEqual(row["flag"], plant.flag)
            self.assertEqual(row["readonly"], plant.readonly)

    def test_package_tree_has_no_leftover_mill_scripts(self):
        hits = list((PIPELINES / "saf").rglob("*leftover*_mill.py"))
        self.assertEqual(hits, [])
        self.assertEqual(list((REPO / "config" / "saf").rglob("*leftover*_mill.py")), [])
        self.assertEqual(list((PIPELINES / "saf").rglob("*mill*.py")), [])
        names = tuple(
            sorted(path.name for path in (PIPELINES / "saf").iterdir() if path.suffix == ".py")
        )
        self.assertEqual(
            names, ("__init__.py", "_contract.py", "catalog.py", "cli.py", "generate.py")
        )


class GeneratePairs(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="saf-gen-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_fixture_pair_is_a_safety_case_and_not_hosted_grok(self):
        dest = self.root / "out"
        request = generate.GenerateRequest(
            FIXTURE, dest, plant_id="saf_r0001:sops-decrypt-paste", round=3
        )
        summary = generate.run(request)
        self.assertEqual(summary["records"], 2)
        self.assertEqual(summary["pairs"], 1)
        self.assertEqual(summary["generator"], GENERATOR)
        self.assertNotEqual(GENERATOR, "grok-4.6")
        lines = (dest / generate.RECORDS_FILENAME).read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2)
        ok, missed = [json.loads(line) for line in lines]
        self.assertEqual(ok["id"], "saf-r0003-sops-decrypt-paste")
        self.assertEqual(missed["id"], "saf-r0003-tooloutput-sops-decrypt-paste-miss")
        self.assertEqual(classify_kind(ok), "safety_case")
        self.assertEqual(classify_kind(missed), "safety_case")
        self.assertEqual(mill_prefix(ok), "saf")
        self.assertEqual(mill_prefix(missed), "saf")
        self.assertFalse(ok["id"].startswith("sir-"))
        self.assertFalse(ok["id"].startswith("dbc-"))
        self.assertEqual(ok["case_type"], "correct_refusal")
        self.assertEqual(missed["case_type"], "missed_refusal")
        self.assertEqual(ok["decision"], "refuse")
        self.assertEqual(missed["decision"], "comply")
        self.assertEqual(ok["meta"]["factory"], FACTORY)
        self.assertEqual(ok["meta"]["generator"], GENERATOR)
        self.assertNotEqual(ok["meta"]["generator"], "grok-4.6")
        self.assertEqual(len(ok["steps"]), 9)
        self.assertGreaterEqual(len(ok["rationale"]), 300)
        self.assertTrue(ok["reward"]["success"])
        self.assertFalse(missed["reward"]["success"])
        notes = (dest / generate.NOTES_FILENAME).read_text(encoding="utf-8")
        self.assertIn("Novel coverage: 86%", notes)

    def test_flavor_dispatch_matches_the_mill(self):
        loaded = catalog.load_catalog(COMMITTED)
        by_flavor = {plant.flavor: plant for plant in loaded.plants}
        clarify = generate.pair_records(5045, by_flavor["clarify"], "saf-pairs-v1")
        self.assertEqual([record["decision"] for record in clarify], ["clarify", "refuse"])
        self.assertEqual(
            [record["case_type"] for record in clarify],
            ["correct_refusal", "incorrect_refusal"],
        )
        escalate = generate.pair_records(5045, by_flavor["escalate"], "saf-pairs-v1")
        self.assertEqual([record["decision"] for record in escalate], ["escalate", "comply"])
        over = generate.pair_records(5045, by_flavor["over-refusal"], "saf-pairs-v1")
        self.assertEqual(
            [record["case_type"] for record in over],
            ["correct_refusal", "incorrect_refusal"],
        )
        readme = generate.pair_records(5045, by_flavor["README"], "saf-pairs-v1")
        self.assertEqual(
            [record["case_type"] for record in readme],
            ["correct_refusal", "missed_refusal"],
        )

    def test_existing_destination_is_refused(self):
        dest = self.root / "exists"
        dest.mkdir()
        with self.assertRaises(SafRefusal) as caught:
            generate.run(generate.GenerateRequest(FIXTURE, dest, all_plants=True))
        self.assertEqual(caught.exception.code, FINDING_DESTINATION_EXISTS)

    def test_destination_under_raw_is_refused(self):
        dest = self.root / "outputs" / "raw" / "saf-out"
        with self.assertRaises(SafRefusal) as caught:
            generate.run(generate.GenerateRequest(FIXTURE, dest, all_plants=True))
        self.assertEqual(caught.exception.code, FINDING_DESTINATION_UNDER_RAW)
        self.assertFalse(dest.exists())

    def test_generate_requires_exactly_one_selector(self):
        dest = self.root / "none"
        with self.assertRaises(SafRefusal) as caught:
            generate.run(generate.GenerateRequest(FIXTURE, dest))
        self.assertEqual(caught.exception.code, FINDING_USAGE)


class CliSurface(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="saf-cli-"))
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
        code, out, err = invoke(
            [
                "generate",
                "--catalog",
                str(FIXTURE),
                "--out",
                str(dest),
                "--plant",
                "saf_r0001:sops-decrypt-paste",
                "--json",
            ]
        )
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["summary"]["records"], 2)
        self.assertTrue((dest / generate.RECORDS_FILENAME).is_file())

    def test_missing_catalog_is_exit_two_and_json_on_stdout(self):
        code, out, err = invoke(["catalog-check", "--catalog", "/nonexistent/saf", "--json"])
        self.assertEqual((code, err), (2, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "refused")
        self.assertTrue(payload["code"].startswith("saf."))


class ImportTwins(unittest.TestCase):
    def test_flat_and_package_catalog_are_one_object(self):
        if str(REPO) not in sys.path:
            sys.path.insert(0, str(REPO))
        import pipelines.saf.catalog as packaged

        self.assertIs(packaged, catalog)


if __name__ == "__main__":
    unittest.main()
