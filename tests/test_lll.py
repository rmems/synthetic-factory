#!/usr/bin/env python3
"""Leftover leftover leftover mill package: pins, AST extract, generate, no mills."""

from __future__ import annotations

import ast
import contextlib
import hashlib
import io
import json
import shutil
import subprocess  # nosec B404 -- git show of pinned legacy-mill-lane blobs only.
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
    "catalog_ast.py",
    "cli.py",
    "generate.py",
)

sys.path.insert(0, str(REPO / "pipelines"))

from pipelines.lll import catalog, cli, generate
from pipelines.lll._contract import (
    FACTORY,
    FAMILY,
    FINDING_DESTINATION_EXISTS,
    FINDING_DESTINATION_UNDER_RAW,
    FINDING_USAGE,
    FINDING_VENDOR_PATH,
    GENERATOR,
    RECORD_PREFIX,
    REVIEWED_HOME,
    SOURCE_MILLS,
    LllRefusal,
    refuse_vendor_paths,
)


def invoke(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.run(argv)
    return code, out.getvalue(), err.getvalue()


def _scratch_catalog(
    scratch: Path,
    *,
    header: dict | None = None,
    plants_lines: list[str] | None = None,
) -> Path:
    dest = scratch / "catalog"
    dest.mkdir(parents=True, exist_ok=True)
    source_header = json.loads((COMMITTED / "CATALOG.json").read_text())
    if header is not None:
        source_header.update(header)
    plants_bytes = (COMMITTED / "plants.jsonl").read_bytes()
    if plants_lines is not None:
        plants_bytes = ("\n".join(plants_lines) + "\n").encode()
        source_header["plants_sha256"] = hashlib.sha256(plants_bytes).hexdigest()
    (dest / "CATALOG.json").write_text(json.dumps(source_header, indent=2))
    (dest / "plants.jsonl").write_bytes(plants_bytes)
    return dest


def _git_show(path: str) -> str | None:
    try:
        proc = subprocess.run(  # nosec B603 B607 -- pinned git show of legacy ref blobs only.
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
    def test_family_home_is_the_cleaned_modules(self):
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
        self.assertEqual(
            catalog.render_plants_jsonl(loaded.plants),
            (COMMITTED / "plants.jsonl").read_bytes(),
        )
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

            with mock.patch.object(Path, "write_text", boom), self.assertRaises(KeyboardInterrupt):
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

    def test_plant_lookup_refuses_an_unknown_id(self):
        loaded = catalog.load_catalog(COMMITTED)
        with self.assertRaises(LllRefusal) as caught:
            loaded.plant("lhc-mill-lll-lang-r4750:not-a-real-plant")
        self.assertIn("PLANT_NOT_FOUND", str(caught.exception))
        with self.assertRaises(LllRefusal):
            loaded.mill_plants("lhc-mill-lll-r-not")

    def test_load_catalog_refuses_drifted_files(self):
        scratch = Path(tempfile.mkdtemp(prefix="lll-badcat-"))
        try:
            dest = _scratch_catalog(scratch / "missing-header")
            (dest / "CATALOG.json").unlink()
            with self.assertRaises(LllRefusal) as caught:
                catalog.load_catalog(dest)
            self.assertIn("CATALOG_FILE_MISSING", str(caught.exception))
            self.assertEqual(len(catalog.catalog_check(dest)), 1)

            dest = _scratch_catalog(scratch / "bad-header")
            (dest / "CATALOG.json").write_text("{")
            with self.assertRaises(LllRefusal) as caught:
                catalog.load_catalog(dest)
            self.assertIn("CATALOG_FIELD_INVALID", str(caught.exception))

            dest = _scratch_catalog(scratch / "list-header")
            (dest / "CATALOG.json").write_text("[]")
            with self.assertRaises(LllRefusal):
                catalog.load_catalog(dest)

            dest = _scratch_catalog(scratch / "sha")
            (dest / "plants.jsonl").write_bytes(b"drift\n")
            with self.assertRaises(LllRefusal) as caught:
                catalog.load_catalog(dest)
            self.assertIn("PLANTS_SHA_MISMATCH", str(caught.exception))

            dest = _scratch_catalog(scratch / "bad-line", plants_lines=["{"])
            with self.assertRaises(LllRefusal) as caught:
                catalog.load_catalog(dest)
            self.assertIn("PLANT_FIELD_INVALID", str(caught.exception))

            dest = _scratch_catalog(scratch / "list-line", plants_lines=["[]"])
            with self.assertRaises(LllRefusal):
                catalog.load_catalog(dest)

            lines = (COMMITTED / "plants.jsonl").read_text().splitlines()
            dest = _scratch_catalog(
                scratch / "dup", plants_lines=[lines[0], lines[0]]
            )
            with self.assertRaises(LllRefusal) as caught:
                catalog.load_catalog(dest)
            self.assertIn("PLANT_DUPLICATE", str(caught.exception))

            dest = _scratch_catalog(scratch / "no-plants")
            (dest / "plants.jsonl").unlink()
            with self.assertRaises(LllRefusal) as caught:
                catalog.load_catalog(dest)
            self.assertIn("CATALOG_FILE_MISSING", str(caught.exception))

            dest = _scratch_catalog(scratch / "factory", header={"factory": "nope"})
            with self.assertRaises(LllRefusal) as caught:
                catalog.load_catalog(dest)
            self.assertIn("CATALOG_FIELD_INVALID", str(caught.exception))
        finally:
            shutil.rmtree(scratch)

    def test_catalog_check_reports_meta_mill_and_source_drift(self):
        scratch = Path(tempfile.mkdtemp(prefix="lll-drift-"))
        try:
            header = json.loads((COMMITTED / "CATALOG.json").read_text())
            header["pair_count"] = 0
            header["plant_count"] = 0
            header["generator"] = "rogue"
            header["catalog_id"] = "wrong"
            header["mills"][0]["blob_sha"] = "deadbeef"
            header["mills"].append(
                {
                    "mill_id": "rogue-mill",
                    "base_round": 1,
                    "blob_sha": "x",
                    "pair_count": 0,
                    "plant_count": 0,
                    "source": "experiments/rogue.py",
                }
            )
            header["source"]["ref"] = "other-ref"
            header["source"]["method"] = "exec"
            header["source"]["scripts"] = []
            header["source"]["not_executed"] = []
            dest = _scratch_catalog(scratch / "drift", header=header)
            findings = catalog.catalog_check(dest)
            self.assertGreaterEqual(len(findings), 5)
            joined = "\n".join(findings)
            for needle in ("pair_count", "plant_count", "generator", "drifted", "rogue-mill"):
                self.assertIn(needle, joined)

            header = json.loads((COMMITTED / "CATALOG.json").read_text())
            header["mills"][0]["pair_count"] = 99
            header["mills"][0]["plant_count"] = 0
            dest = _scratch_catalog(scratch / "counts", header=header)
            findings = catalog.catalog_check(dest)
            self.assertTrue(any("counts drifted" in item for item in findings))

            lines = (COMMITTED / "plants.jsonl").read_text().splitlines()
            row = json.loads(lines[0])
            row["base_round"] = 1
            row["index"] = 9
            lines[0] = json.dumps(row)
            dest = _scratch_catalog(scratch / "coords", plants_lines=lines)
            findings = catalog.catalog_check(dest)
            self.assertTrue(any("coordinates drifted" in item for item in findings))
            self.assertTrue(any("index drifted" in item for item in findings))
        finally:
            shutil.rmtree(scratch)

    def test_plants_from_source_refuses_malformed_sources(self):
        with self.assertRaises(LllRefusal) as caught:
            catalog.plants_from_source(
                "def broken(:", mill_id="m", path="x.py", base_round=1
            )
        self.assertIn("SOURCE_NOT_PARSEABLE", str(caught.exception))
        with self.assertRaises(LllRefusal):
            catalog.plants_from_source(
                "PAIRS = []\nPAIRS.append(('t', a, b))\n",
                mill_id="m",
                path="x.py",
                base_round=1,
            )
        with self.assertRaises(LllRefusal):
            catalog.plants_from_source(
                "PAIRS = []\nfa, fb = fn_pair('a', 'b', 'c', 'd', 'e', 'f')\n",
                mill_id="m",
                path="x.py",
                base_round=1,
            )

    def test_generate_cli_mill_and_refusal_json(self):
        scratch = Path(tempfile.mkdtemp(prefix="lll-cli2-"))
        try:
            dest = scratch / "mill-out"
            code, out, err = invoke(
                [
                    "generate",
                    "--mill",
                    "lhc-mill-lll-lang-r4750",
                    "--out",
                    str(dest),
                    "--json",
                ]
            )
            self.assertEqual(code, 0, err)
            self.assertEqual(json.loads(out)["records"], 16)
            code, out, err = invoke(
                ["generate", "--mill", "nope", "--round", "3", "--out", str(scratch / "x"), "--json"]
            )
            self.assertEqual(code, 2)
            self.assertEqual(json.loads(out)["status"], "refusal")
            code, out, err = invoke(
                ["generate", "--mill", "nope", "--round", "3", "--out", str(scratch / "y")]
            )
            self.assertEqual(code, 2)
            self.assertIn("USAGE", err)
            code, out, err = invoke(["catalog"])
            self.assertEqual(code, 0, err)
            self.assertIn(FIRST_PLANT, out)
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
