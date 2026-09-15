#!/usr/bin/env python3
"""CRP leftover3 mill: AST extract, noun on every catalog row, generate gates."""

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
sys.path.insert(0, str(PIPELINES))

from crp import catalog as cat  # noqa: E402
from crp import cli, generate  # noqa: E402
from crp._contract import (  # noqa: E402
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_FIELD_MISSING,
    FINDING_NOUN_MISSING,
    FINDING_ROUND_OUT_OF_DOMAIN,
    CrpRefusal,
)
from record_kind import classify_kind  # noqa: E402

PACKAGE = PIPELINES / "crp"
SNIPPET = """
def P(family, slug, noun, title, core, boot, test, line, nit, defect, reach, missing, fix, needles, notfam):
    return locals()

PLANTS = [
    P("fam-a", "slug-a", "keel801", "feat: a", "a.py", "b.py", "t.py", 11, "n",
      "defect a", "reach a", "missing a", "fix a", "a|b", "other plant"),
    P("fam-b", "slug-b", noun="spar804", title="feat: b", core="c.py", boot="d.py",
      test="u.py", line=22, nit="m", defect="defect b", reach="reach b",
      missing="missing b", fix="fix b", needles="c|d", notfam="prior plant"),
]
"""


def invoke(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.run(argv)
    return code, out.getvalue(), err.getvalue()


class PackageShape(unittest.TestCase):
    def test_the_package_does_not_vendor_crp_mill_scripts(self):
        names = {path.name for path in PACKAGE.glob("*.py")}
        self.assertEqual(
            names,
            {"__init__.py", "_contract.py", "catalog.py", "generate.py", "cli.py"},
        )
        self.assertEqual(list(PACKAGE.glob("crp-mill*.py")), [])
        self.assertEqual([p.name for p in PACKAGE.glob("*mill*.py")], [])

    def test_both_import_spellings_are_one_object(self):
        if str(REPO) not in sys.path:
            sys.path.append(str(REPO))
        from pipelines.crp import catalog as packaged

        self.assertIs(packaged, cat)
        self.assertIs(sys.modules["crp.catalog"], sys.modules["pipelines.crp.catalog"])


class AstExtract(unittest.TestCase):
    def test_plants_from_source_adds_noun_to_every_row(self):
        plants = cat.plants_from_source(SNIPPET)
        self.assertEqual([plant.noun for plant in plants], ["keel801", "spar804"])
        self.assertEqual(plants[0].repo, "plant/keel801-slug-a")
        self.assertEqual(plants[1].as_mapping()["noun"], "spar804")

    def test_a_p_call_without_noun_is_refused(self):
        with self.assertRaises(CrpRefusal) as ctx:
            cat.plants_from_source(
                'P("fam", "slug", title="feat: x", core="a.py", boot="b.py", '
                'test="t.py", line=1, nit="n", defect="d", reach="r", '
                'missing="m", fix="f", needles="x", notfam="y")\n'
            )
        self.assertEqual(ctx.exception.code, FINDING_FIELD_MISSING)
        self.assertIn("noun", ctx.exception.message)

    def test_an_empty_noun_is_refused(self):
        with self.assertRaises(CrpRefusal) as ctx:
            cat.plant_from_mapping(
                {
                    "family": "fam", "slug": "slug", "noun": "", "title": "feat: x",
                    "core": "a.py", "boot": "b.py", "test": "t.py", "line": 1,
                    "nit": "n", "defect": "d", "reach": "r", "missing": "m",
                    "fix": "f", "needles": "x", "notfam": "y",
                }
            )
        self.assertEqual(ctx.exception.code, FINDING_NOUN_MISSING)


class CommittedCatalog(unittest.TestCase):
    def test_every_extracted_row_carries_noun(self):
        loaded = cat.load_catalog()
        report = cat.catalog_check()
        self.assertEqual(loaded.catalog_id, "crp-leftover3-v1")
        self.assertEqual(len(loaded.plants), 48)
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["plants"], 48)
        self.assertEqual(report["triples"], 16)
        self.assertEqual(report["first_round"], 729)
        self.assertEqual(report["last_round"], 744)
        nouns = [plant.noun for plant in loaded.plants]
        self.assertTrue(all(isinstance(noun, str) and noun for noun in nouns))
        self.assertEqual(len(set(nouns)), 48)
        self.assertEqual(nouns[0], "keel801")
        self.assertEqual(loaded.plants[0].repo, "plant/keel801-terraform-target-orphan-sku")

    def test_leftover3_source_reextracts_the_committed_rows(self):
        source = Path("/tmp/crp-mills/code_review_preference_mill_leftover3.py")
        if not source.is_file():
            self.skipTest("legacy leftover3 mill is not in this environment")
        extracted = cat.plants_from_source(source.read_text(encoding="utf-8"))
        committed = cat.load_catalog().plants
        self.assertEqual(len(extracted), 48)
        self.assertEqual(
            [(p.slug, p.noun, p.family) for p in extracted],
            [(p.slug, p.noun, p.family) for p in committed],
        )


class Generate(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="crp-gen-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_pair_is_a_preference_record_with_noun(self):
        plant = cat.load_catalog().plants[0]
        rec = generate.pair(plant, 729, 0)
        self.assertEqual(rec["id"], "crp-r729-terraform-target-orphan-sku")
        self.assertEqual(classify_kind(rec), "preference")
        self.assertEqual(rec["meta"]["noun"], "keel801")
        self.assertEqual(rec["meta"]["factory"], "code-review-preference-factory")
        self.assertEqual(len(rec["chosen"]["steps"]), 13)
        self.assertEqual(len(rec["rejected"]["steps"]), 12)
        self.assertEqual(
            [step["tool_call"] for step in rec["chosen"]["steps"][:7]],
            [step["tool_call"] for step in rec["rejected"]["steps"][:7]],
        )
        self.assertNotEqual(
            rec["chosen"]["steps"][7]["tool_call"],
            rec["rejected"]["steps"][7]["tool_call"],
        )

    def test_round_729_writes_three_records_and_refuses_clobber_or_raw(self):
        out = self.root / "run"
        summary = generate.run(generate.RunRequest(729, out))
        self.assertEqual(summary["records"], 3)
        self.assertEqual(summary["nouns"], ["keel801", "keel802", "keel803"])
        batch = (out / "batch-r729.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(batch), 3)
        first = json.loads(batch[0])
        self.assertEqual(first["meta"]["noun"], "keel801")
        notes = (out / "NOTES-r729.md").read_text(encoding="utf-8")
        self.assertIn("noun=`keel801`", notes)
        with self.assertRaises(CrpRefusal) as exists:
            generate.run(generate.RunRequest(729, out))
        self.assertEqual(exists.exception.code, FINDING_DESTINATION_EXISTS)
        raw = self.root / "outputs" / "raw" / "x"
        with self.assertRaises(CrpRefusal) as under_raw:
            generate.run(generate.RunRequest(729, raw))
        self.assertEqual(under_raw.exception.code, FINDING_DESTINATION_UNDER_RAW)
        self.assertFalse(raw.exists())

    def test_a_round_outside_the_leftover3_wave_is_refused(self):
        with self.assertRaises(CrpRefusal) as ctx:
            cat.plants_for_round(728)
        self.assertEqual(ctx.exception.code, FINDING_ROUND_OUT_OF_DOMAIN)


class Cli(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="crp-cli-"))
        self.addCleanup(shutil.rmtree, self.root, True)

    def test_catalog_check_json_reports_nouns(self):
        code, out, err = invoke(["catalog-check", "--json"])
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["plants"], 48)
        self.assertEqual(payload["nouns"], 48)

    def test_generate_json_and_a_raw_refusal(self):
        out = self.root / "dest"
        code, stdout, err = invoke(["generate", "--round", "729", "--out", str(out), "--json"])
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(stdout)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["summary"]["nouns"], ["keel801", "keel802", "keel803"])
        code, stdout, _err = invoke(
            ["generate", "--round", "729", "--out", str(self.root / "outputs" / "raw" / "x"), "--json"]
        )
        self.assertEqual(code, 2)
        refused = json.loads(stdout)
        self.assertEqual(refused["status"], "refused")
        self.assertEqual(refused["code"], FINDING_DESTINATION_UNDER_RAW)


if __name__ == "__main__":
    unittest.main()
