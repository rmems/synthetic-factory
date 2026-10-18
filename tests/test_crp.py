#!/usr/bin/env python3
"""CRP leftover3 mill: AST extract, noun on every catalog row, generate gates."""

from __future__ import annotations

import ast
import contextlib
import enum
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
sys.path.insert(0, str(PIPELINES))

from crp import catalog as cat  # noqa: E402
from crp import cli, generate, wave_catalog  # noqa: E402
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
            {
                "__init__.py",
                "_contract.py",
                "catalog.py",
                "cli.py",
                "generate.py",
                "leftover3_prior.py",
                "r432.py",
                "r538.py",
                "r729.py",
                "r817.py",
                "r995.py",
                "wave_catalog.py",
            },
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
        mills = Path(tempfile.gettempdir(), "crp-mills")
        source = mills / "code_review_preference_mill_leftover3.py"
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

    def test_an_interrupt_during_the_write_removes_the_destination(self):
        out = self.root / "run"

        def interrupt(*_args, **_kwargs):
            raise KeyboardInterrupt

        request = generate.RunRequest(729, out)
        interrupted = mock.patch.object(generate, "_fsync_destination", interrupt)
        with interrupted, self.assertRaises(KeyboardInterrupt):
            generate.run(request)
        self.assertFalse(out.exists())
        summary = generate.run(request)
        self.assertEqual(summary["records"], 3)

    def test_batch_jsonl_uses_literal_lf_record_boundaries(self):
        out = self.root / "run"
        generate.run(generate.RunRequest(729, out))
        payload = (out / "batch-r729.jsonl").read_bytes()
        self.assertNotIn(b"\r", payload)
        records = payload.split(b"\n")
        self.assertEqual(records[-1], b"")
        self.assertEqual(len(records) - 1, 3)

    def test_a_round_outside_the_leftover3_wave_is_refused(self):
        with self.assertRaises(CrpRefusal) as ctx:
            cat.plants_for_round(728)
        self.assertEqual(ctx.exception.code, FINDING_ROUND_OUT_OF_DOMAIN)


class RawEnumerateShapes(unittest.TestCase):
    """``_RAW`` + ``enumerate`` expansion only accepts the pinned literal shapes."""

    def test_raw_rows_must_be_a_nonempty_list_of_tuples(self):
        for source in ("obj.attr = 1\n", "_RAW = []\n", "_RAW = [('a',), ['b']]\n"):
            with self.subTest(source=source):
                self.assertIsNone(cat._raw_rows_from_tree(ast.parse(source)))
        tree = ast.parse("first = _RAW = [('fam', 1)]\n_RAW = [('later',)]\n")
        self.assertEqual(cat._raw_rows_from_tree(tree), [("later",)])
        tree = ast.parse("other: int = 3\n_RAW: list = [('fam', 1)]\n")
        self.assertEqual(cat._raw_rows_from_tree(tree), [("fam", 1)])

    def test_raw_rows_without_an_indexed_noun_loop_are_refused(self):
        with self.assertRaises(CrpRefusal) as ctx:
            cat.plants_from_source("P(**row)\n_RAW = [('fam',)]\n")
        self.assertEqual(
            ctx.exception.message, "_RAW expand loop has no indexed {{prefix}}{{base + i}} noun"
        )

    def test_the_noun_base_must_be_an_int_plus_i(self):
        for noun in ("f'keel{800 - i}'", "f'keel{x + i}'", "f'keel{800 + j}'"):
            with self.subTest(noun=noun):
                self.assertIsNone(cat._indexed_noun_base(ast.parse(noun, mode="eval").body))
        found = cat._indexed_noun_base(ast.parse("f'atoll{12 + i}'", mode="eval").body)
        self.assertEqual(found, ("atoll", 12))

    def test_a_missing_git_is_a_coded_refusal(self):
        no_git = mock.patch.object(wave_catalog.shutil, "which", return_value=None)
        with no_git, self.assertRaises(CrpRefusal) as ctx:
            wave_catalog._git_executable()
        self.assertEqual(ctx.exception.message, "git executable not found on PATH")

    def test_the_noun_loop_skips_every_non_plant_append(self):
        loop = (
            "for i in range(3):\n    PLANTS.append(P(a, b, f'keel{800 + i}'))\n"
            "for i, row in rows.enumerate():\n    PLANTS.append(P(a, b, f'keel{801 + i}'))\n"
            "for i, row in enumerate(_RAW):\n"
            "    PLANTS.extend(row)\n"
            "    OTHER.append(P(a, b, f'keel{802 + i}'))\n"
            "    PLANTS.append()\n"
            "    PLANTS.append(mod.P(a, b, f'keel{803 + i}'))\n"
            "    PLANTS.append(Q(a, b, f'keel{804 + i}'))\n"
            "    PLANTS.append(_p(a, b))\n"
        )
        self.assertIsNone(cat._raw_noun_base_from_tree(ast.parse(loop)))
        found = loop + "    PLANTS.append(_p(a, b, f'reef{805 + i}'))\n"
        self.assertEqual(cat._raw_noun_base_from_tree(ast.parse(found)), ("reef", 805))


class _Round(enum.IntEnum):
    R432 = 432


class WaveRouting(unittest.TestCase):
    def test_only_a_plain_int_round_reaches_a_wave(self):
        for round_n, shown in ((_Round.R432, "<_Round.R432: 432>"), (True, "True")):
            with self.subTest(round_n=round_n), tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / "run"
                request = generate.RunRequest(round_n, out)
                with self.assertRaises(CrpRefusal) as ctx:
                    generate.run(request)
                self.assertEqual(ctx.exception.code, FINDING_ROUND_OUT_OF_DOMAIN)
                self.assertEqual(ctx.exception.message, f"round must be an int, got {shown}")
                self.assertFalse(out.exists())

    def test_a_round_owned_by_no_wave_falls_through_to_the_leftover3_refusal(self):
        for round_n, message in (
            (4000, "round must lie in [729, 744], got 4000"),
            (True, "round must be an int, got True"),
            (729.0, "round must be an int, got 729.0"),
        ):
            with self.subTest(round_n=round_n):
                with self.assertRaises(CrpRefusal) as ctx:
                    generate._wave_for_round(round_n)
                self.assertEqual(ctx.exception.code, FINDING_ROUND_OUT_OF_DOMAIN)
                self.assertEqual(ctx.exception.message, message)


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
