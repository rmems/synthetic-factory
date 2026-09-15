#!/usr/bin/env python3
"""Leftover leftover leftover mill package: pins, AST extract, generate, no mills."""

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
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
COMMITTED = REPO / "config" / "lll"
LEGACY_REF = "origin/legacy-mill-lane"
FIRST_MILL = "experiments/lhc-mill-lll-lang-r4750.py"
FIRST_SLUG = "rust-pin-vs-transmute-selfref"
FIRST_PLANT = f"lhc-mill-lll-lang-r4750:{FIRST_SLUG}"
PACKAGE_FILES = (
    "__init__.py",
    "_contract.py",
    "catalog.py",
    "cli.py",
    "generate.py",
)

sys.path.insert(0, str(REPO / "pipelines"))

from pipelines.lll import catalog, cli, generate  # noqa: E402
from pipelines.lll._contract import (  # noqa: E402
    FACTORY,
    FAMILY,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_USAGE,
    FINDING_VENDOR_PATH,
    GENERATOR,
    LllRefusal,
    RECORD_PREFIX,
    REVIEWED_HOME,
    SOURCE_MILLS,
    refuse_vendor_paths,
)


def invoke(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.run(argv)
    return code, out.getvalue(), err.getvalue()


def _git_show(path: str) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "show", f"{LEGACY_REF}:{path}"],
            cwd=REPO,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout


def _fn_pair_source(pairs: list[tuple[str, str, str, str, str]]) -> str:
    lines = ["PAIRS = []", ""]
    for success, fail, plant_a, plant_b, title in pairs:
        lines.append(
            f"fa, fb = fn_pair({success!r}, {fail!r}, {plant_a!r}, {plant_b!r}, 'what', 'what')"
        )
        lines.append(f"PAIRS.append(({title!r}, fa, fb))")
    return "\n".join(lines) + "\n"


class LllPackageTests(unittest.TestCase):
    def test_family_home_is_the_five_cleaned_modules(self):
        home = REPO / "pipelines" / "lll"
        self.assertEqual(sorted(path.name for path in home.glob("*.py")), sorted(PACKAGE_FILES))
        self.assertEqual(list(home.glob("lhc-mill-lll*.py")), [])
        banned = {"exec", "eval", "compile"}
        for path in home.glob("*.py"):
            tree = ast.parse(path.read_text(), filename=str(path))
            calls = [
                node.func.id
                for node in ast.walk(tree)
                if isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in banned
            ]
            self.assertEqual(calls, [], f"{path.name} calls {calls}")

    def test_both_import_spellings_are_one_object(self):
        import lll.catalog as flat

        self.assertIs(flat, catalog)

    def test_reviewed_home_stays_lhc(self):
        self.assertEqual(FAMILY, "lll")
        self.assertEqual(RECORD_PREFIX, "lhc")
        self.assertEqual(REVIEWED_HOME, FACTORY)
        self.assertEqual(FACTORY, "long-horizon-coding-factory")
        self.assertEqual(GENERATOR, "lll-mill")

    def test_vendor_paths_are_refused(self):
        with self.assertRaises(LllRefusal) as caught:
            refuse_vendor_paths(["lhc-mill-lll-r4654.py"])
        self.assertIn(FINDING_VENDOR_PATH, str(caught.exception))
        with self.assertRaises(LllRefusal):
            refuse_vendor_paths(["mill_leftover_leftover_leftover_r56.py"])
        with self.assertRaises(LllRefusal):
            refuse_vendor_paths(["lll-loop-r1.py"])

    def test_plants_from_source_reads_fn_pair(self):
        source = _fn_pair_source(
            [
                (
                    "ok-slug",
                    "fail-slug",
                    "ok-plant",
                    "fail-plant",
                    "ok leftover leftover leftover vs fail",
                ),
            ]
        )
        plants = catalog.plants_from_source(
            source, mill_id="lhc-mill-lll-r1", path="snippet.py", base_round=1
        )
        self.assertEqual(len(plants), 1)
        self.assertEqual(plants[0].success_slug, "ok-slug")
        self.assertEqual(plants[0].fail_slug, "fail-slug")
        self.assertEqual(plants[0].title, "ok leftover leftover leftover vs fail")

    def test_extract_does_not_exec(self):
        boom = "raise SystemExit('executed')\n" + _fn_pair_source(
            [
                (
                    "a-slug",
                    "b-slug",
                    "a-plant",
                    "b-plant",
                    "title leftover leftover leftover",
                )
            ]
        )
        plants = catalog.plants_from_source(
            boom, mill_id="lhc-mill-lll-r2", path="boom.py", base_round=2
        )
        self.assertEqual(plants[0].success_slug, "a-slug")
        with self.assertRaises(LllRefusal):
            catalog.plants_from_source(
                "PAIRS = []\n", mill_id="lhc-mill-lll-r0", path="empty.py", base_round=0
            )

    def test_committed_catalog_check_is_clean(self):
        self.assertEqual(catalog.catalog_check(COMMITTED), [])
        loaded = catalog.load_catalog(COMMITTED)
        self.assertEqual(len(loaded.plants), 48)
        self.assertEqual(len(loaded.mills), 3)
        self.assertEqual(loaded.plants[0].plant_id, FIRST_PLANT)
        self.assertEqual(loaded.plants[0].success_slug, FIRST_SLUG)
        self.assertEqual(loaded.plants[-1].success_slug, "swift-consume-operator-move")
        self.assertEqual(
            [mill.mill_id for mill in loaded.mills],
            [item[0] for item in SOURCE_MILLS],
        )

    def test_archive_extract_matches_committed_when_ref_is_present(self):
        source = _git_show(FIRST_MILL)
        if source is None:
            self.skipTest("origin/legacy-mill-lane is not available")
        extracted = catalog.plants_from_source(
            source,
            mill_id="lhc-mill-lll-lang-r4750",
            path=FIRST_MILL,
            base_round=4750,
        )
        loaded = catalog.load_catalog(COMMITTED).mill_plants("lhc-mill-lll-lang-r4750")
        self.assertEqual(
            [plant.pair_fields() for plant in extracted],
            [plant.pair_fields() for plant in loaded],
        )
        self.assertEqual(len(extracted), 16)
        tree = ast.parse(source)
        self.assertTrue(
            any(
                isinstance(node, ast.FunctionDef) and node.name == "fn_pair"
                for node in tree.body
            )
        )

    def test_record_is_a_compact_catalog_replay(self):
        plant = catalog.load_catalog(COMMITTED).plant(FIRST_PLANT)
        rec = generate.record(plant)
        self.assertEqual(rec["id"], f"lhc-r4750-{FIRST_SLUG}")
        self.assertEqual(rec["meta"]["kind"], "catalog_replay")
        self.assertEqual(rec["meta"]["factory"], FACTORY)
        self.assertEqual(rec["pair"]["fail_slug"], "rust-transmute-unpin-alias-leftover")
        self.assertNotIn("steps", rec)

    def test_generate_writes_one_plant_and_refuses_clobber_or_raw(self):
        scratch = Path(tempfile.mkdtemp(prefix="lll-gen-"))
        dest = scratch / "out"
        try:
            summary = generate.run(
                generate.GenerateRequest(catalog_dir=COMMITTED, out_dir=dest, plant_id=FIRST_PLANT)
            )
            self.assertEqual(summary["records"], 1)
            self.assertTrue((dest / "records.jsonl").is_file())
            self.assertTrue((dest / "NOTES.md").is_file())
            line = (dest / "records.jsonl").read_text().splitlines()[0]
            self.assertTrue(line.endswith("}") and not line.endswith("}\n"))
            with self.assertRaises(LllRefusal) as caught:
                generate.run(
                    generate.GenerateRequest(
                        catalog_dir=COMMITTED, out_dir=dest, plant_id=FIRST_PLANT
                    )
                )
            self.assertIn(FINDING_DESTINATION_EXISTS, str(caught.exception))
            raw = REPO / "outputs" / "raw" / "lll-should-refuse"
            with self.assertRaises(LllRefusal) as raw_caught:
                generate.run(
                    generate.GenerateRequest(
                        catalog_dir=COMMITTED, out_dir=raw, plant_id=FIRST_PLANT
                    )
                )
            self.assertIn(FINDING_DESTINATION_UNDER_RAW, str(raw_caught.exception))
            self.assertFalse(raw.exists())
        finally:
            shutil.rmtree(scratch)

    def test_an_interrupt_during_the_write_removes_the_destination(self):
        scratch = Path(tempfile.mkdtemp(prefix="lll-int-"))
        dest = scratch / "partial"
        try:
            real_write = Path.write_text

            def boom(self, *args, **kwargs):
                if self.name == "records.jsonl":
                    raise KeyboardInterrupt
                return real_write(self, *args, **kwargs)

            with mock.patch.object(Path, "write_text", boom):
                with self.assertRaises(KeyboardInterrupt):
                    generate.run(
                        generate.GenerateRequest(
                            catalog_dir=COMMITTED, out_dir=dest, plant_id=FIRST_PLANT
                        )
                    )
            self.assertFalse(dest.exists())
        finally:
            shutil.rmtree(scratch)

    def test_catalog_and_catalog_check_cli(self):
        code, out, err = invoke(["catalog-check", "--json"])
        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["pair_count"], 48)
        self.assertEqual(len(payload["mills"]), 3)
        code, out, err = invoke(["catalog", "--json"])
        self.assertEqual(code, 0, err)
        listing = json.loads(out)
        self.assertIn(FIRST_PLANT, listing["plants"])

    def test_generate_cli_and_usage(self):
        scratch = Path(tempfile.mkdtemp(prefix="lll-cli-"))
        dest = scratch / "cli-out"
        try:
            code, out, err = invoke(
                ["generate", "--plant", FIRST_PLANT, "--out", str(dest), "--json"]
            )
            self.assertEqual(code, 0, err)
            payload = json.loads(out)
            self.assertEqual(payload["records"], 1)
            code, out, err = invoke(["generate", "--out", str(scratch / "missing")])
            self.assertEqual(code, 2)
            self.assertIn(FINDING_USAGE, err)
        finally:
            shutil.rmtree(scratch)

    def test_package_does_not_vendor_leftover_mills(self):
        tree = [path.name for path in (REPO / "pipelines" / "lll").rglob("*")]
        tree.extend(path.name for path in COMMITTED.rglob("*"))
        for name in tree:
            self.assertFalse(name.endswith("_mill.py"))
            self.assertNotIn("lhc-mill-lll", name)


if __name__ == "__main__":
    unittest.main()
