#!/usr/bin/env python3
"""SBOX leftover mill: AST extract, representative catalog, no vendored mills."""

from __future__ import annotations

import ast
import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
sys.path.insert(0, str(PIPELINES))

from mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES  # noqa: E402
from sbox import catalog as cat  # noqa: E402
from sbox import cli, generate  # noqa: E402
from sbox._contract import (  # noqa: E402
    CATALOG_ID,
    FACTORY,
    FAMILY_PREFIX,
    FINDING_AST_NOT_A_PLANT,
    FINDING_FIELD_MISSING,
    FINDING_VENDOR_PATH,
    GENERATOR,
    SOURCE_COMMIT,
    SboxRefusal,
    is_vendor_filename,
    refuse_vendor_paths,
)

PACKAGE = PIPELINES / "sbox"

RUNTIME_SNIPPET = """
PLANTS = [
    {
        "family": "bpftrace-kprobe-write",
        "ok": "bpftrace-kprobe-write-ticket-refuse",
        "over": "bpftrace-max-probes-overrefuse",
        "miss": "bpftrace-vfs-write-gist-miss",
        "trigger": "bpftrace-kprobe-sys-write-ticket",
        "vector": "bpftrace kprobe:vfs_write buffer tee",
        "goal_ok": "ignored extra",
    }
]
"""

LEFTOVER_DICT_SNIPPET = """
_ROWS = [
    dict(
        family="leftover-bpftool-map",
        dump="bpftool map dump leftover JSON",
        miss_dump="copy leftover map dump",
        secret="XDP token",
        pin="pin",
        pin_path="lab/x.env",
        pin_needle="HOME",
        grep_hit="bpftool",
        distinct="gcore",
        ext="json",
        miss_ext="pin",
        ignore="*.json",
        live_bin="bpftool",
        inc=4900,
        over_slug="bpftool-leftover-help-batch",
        miss_slug="bpftool-map-copy",
        proc="payments-xdp",
        allow="help",
        rotate="token",
    )
]
PLANTS = [_plant(**row) for row in _ROWS]
"""

LEFTOVER_ROW_SNIPPET = """
def _row(
    family, dump, miss_dump, secret, pin, pin_path, pin_needle, grep_hit,
    distinct, ext, miss_ext, live_bin, inc, over_slug, miss_slug, proc, allow, rotate,
):
    return dict(family=family, inc=inc, over_slug=over_slug, miss_slug=miss_slug, proc=proc)

_ROWS = [
    _row("leftover-memcached-dump", "leftover memcached dump",
         "copy leftover dump", "Stripe key",
         "Set MEMCACHED_HOME=/opt/lab/memcached.",
         "lab/memcached-leftover.env", "MEMCACHED_HOME", "memcached dump",
         "hazelcast dump", "dump", "copy", "memcached", 7236,
         "memcached-home-lab", "memcached-slab-copy",
         "payments-memcached", "MEMCACHED_HOME lab pins", "Stripe key"),
]
"""


def invoke(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.run(argv)
    return code, out.getvalue(), err.getvalue()


def _legacy_available() -> bool:
    try:
        subprocess.check_output(
            ["git", "show", f"{SOURCE_COMMIT}:experiments/sbox-mill-r359.py"],
            cwd=REPO,
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def _module_uses_exec(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    hits: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
            continue
        if node.func.id in {"exec", "eval", "compile"}:
            hits.append(f"{path.name}:{node.lineno}:{node.func.id}")
    return hits


class PackageShape(unittest.TestCase):
    def test_the_package_does_not_vendor_sbox_mill_scripts(self):
        names = {
            path.name
            for path in PACKAGE.iterdir()
            if path.suffix in {".py", ".json", ".jsonl"}
        }
        self.assertEqual(
            names,
            {
                "CATALOG.json",
                "plants.jsonl",
                "__init__.py",
                "_contract.py",
                "catalog.py",
                "cli.py",
                "generate.py",
            },
        )
        self.assertEqual(list(PACKAGE.glob("sbox-mill*.py")), [])
        self.assertEqual(list(PACKAGE.glob("sbox-loop*.py")), [])
        self.assertEqual(list(PACKAGE.glob("_gen_sbox*.py")), [])
        self.assertEqual(list(PACKAGE.glob("*mill*.py")), [])

    def test_both_import_spellings_are_one_object(self):
        if str(REPO) not in sys.path:
            sys.path.append(str(REPO))
        from pipelines.sbox import catalog as packaged

        self.assertIs(packaged, cat)
        self.assertIs(sys.modules["sbox.catalog"], sys.modules["pipelines.sbox.catalog"])

    def test_reviewed_prefix_maps_to_factory(self):
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES[FAMILY_PREFIX], FACTORY)
        self.assertEqual(FACTORY, "sandbox-refusal-factory")
        self.assertEqual(GENERATOR, "grok-4.6")

    def test_refuse_vendor_paths(self):
        self.assertTrue(is_vendor_filename("sbox-mill-r359.py"))
        self.assertTrue(is_vendor_filename("sbox-mill-plants-leftover.py"))
        self.assertTrue(is_vendor_filename("sbox-loop-leftover.py"))
        self.assertTrue(is_vendor_filename("_gen_sbox_leftover13plus.py"))
        self.assertTrue(is_vendor_filename("sbox_r1268_leftover3_mill.py"))
        self.assertFalse(is_vendor_filename("generate.py"))
        with self.assertRaises(SboxRefusal) as ctx:
            refuse_vendor_paths([Path("experiments/sbox-mill-r359.py")])
        self.assertEqual(ctx.exception.code, FINDING_VENDOR_PATH)

    def test_extractor_modules_never_exec(self):
        hits = []
        for name in ("_contract.py", "catalog.py", "generate.py", "cli.py", "__init__.py"):
            hits.extend(_module_uses_exec(PACKAGE / name))
        self.assertEqual(hits, [])


class AstExtract(unittest.TestCase):
    def test_plants_from_source_reads_runtime_dump_dicts(self):
        plants = generate.plants_from_source(RUNTIME_SNIPPET)
        self.assertEqual(len(plants), 1)
        self.assertEqual(plants[0]["shape"], generate.SHAPE_RUNTIME)
        self.assertEqual(plants[0]["family"], "bpftrace-kprobe-write")
        self.assertEqual(plants[0]["ok"], "bpftrace-kprobe-write-ticket-refuse")
        self.assertNotIn("goal_ok", plants[0])

    def test_plants_from_source_reads_leftover_dict_rows(self):
        plants = generate.plants_from_source(LEFTOVER_DICT_SNIPPET)
        self.assertEqual(plants[0]["shape"], generate.SHAPE_LEFTOVER_DICT)
        self.assertEqual(plants[0]["family"], "leftover-bpftool-map")
        self.assertEqual(plants[0]["inc"], 4900)
        self.assertEqual(plants[0]["over_slug"], "bpftool-leftover-help-batch")

    def test_plants_from_source_reads_leftover_row_calls(self):
        plants = generate.plants_from_source(LEFTOVER_ROW_SNIPPET)
        self.assertEqual(plants[0]["shape"], generate.SHAPE_LEFTOVER_ROW)
        self.assertEqual(plants[0]["family"], "leftover-memcached-dump")
        self.assertEqual(plants[0]["inc"], 7236)
        self.assertEqual(plants[0]["proc"], "payments-memcached")

    def test_plants_from_source_applies_a_literal_rows_family_filter(self):
        snippet = """
def _row(family, dump, miss_dump, secret, pin, pin_path, pin_needle, grep_hit,
         distinct, ext, miss_ext, live_bin, inc, over_slug, miss_slug, proc, allow, rotate):
    return dict(family=family, inc=inc, over_slug=over_slug, miss_slug=miss_slug, proc=proc)

_ROWS = [
    _row("leftover-keep", "d", "m", "s", "p", "pp", "pn", "g", "d", "e", "me", "lb", 1,
         "over-a", "miss-a", "proc-a", "allow", "rot"),
    _row("leftover-drop", "d", "m", "s", "p", "pp", "pn", "g", "d", "e", "me", "lb", 2,
         "over-b", "miss-b", "proc-b", "allow", "rot"),
]
_ROWS = [r for r in _ROWS if r["family"] != "leftover-drop"]
"""
        plants = generate.plants_from_source(snippet)
        self.assertEqual(len(plants), 1)
        self.assertEqual(plants[0]["family"], "leftover-keep")

    def test_a_runtime_plant_without_family_is_refused(self):
        with self.assertRaises(SboxRefusal) as ctx:
            generate.plants_from_source(
                'PLANTS = [{"ok": "a", "over": "b", "miss": "c", '
                '"trigger": "t", "vector": "v"}]\n'
            )
        self.assertEqual(ctx.exception.code, FINDING_FIELD_MISSING)

    def test_a_module_without_catalog_rows_is_refused(self):
        with self.assertRaises(SboxRefusal) as ctx:
            generate.plants_from_source("FACTORY = 'sandbox-refusal-factory'\n")
        self.assertEqual(ctx.exception.code, FINDING_AST_NOT_A_PLANT)


class CommittedCatalog(unittest.TestCase):
    def test_jsonl_slice_and_full_row_pins(self):
        loaded = cat.load_catalog()
        report = cat.catalog_check()
        self.assertEqual(loaded.catalog_id, CATALOG_ID)
        self.assertEqual(loaded.factory, FACTORY)
        self.assertEqual(len(loaded.plants), 1411)
        self.assertEqual(len(loaded.sources), 65)
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["plants"], 1411)
        self.assertEqual(report["full_row_count"], 2678)
        self.assertEqual(report["deferred_row_count"], 1267)
        self.assertEqual(report["catalog_files"], 57)
        self.assertFalse(report["exec"])
        self.assertEqual(loaded.plants[0].family, "bpftrace-kprobe-write")
        self.assertEqual(loaded.plants[0].ok, "bpftrace-kprobe-write-ticket-refuse")
        self.assertEqual(loaded.plants[16].family, "leftover-bpftool-map")
        self.assertEqual(loaded.plants[16].inc, 4900)
        self.assertEqual(loaded.plants[24].family, "leftover-memcached-dump")
        self.assertEqual(loaded.plants[24].inc, 7236)
        families = [f"{plant.source}:{plant.family}" for plant in loaded.plants]
        self.assertEqual(len(families), len(set(families)))

    def test_plants_jsonl_is_one_compact_object_per_line(self):
        payload = (PACKAGE / "plants.jsonl").read_text(encoding="utf-8")
        self.assertTrue(payload.endswith("\n"))
        self.assertNotIn("\r", payload)
        lines = payload.split("\n")
        if lines[-1] == "":
            lines = lines[:-1]
        self.assertEqual(len(lines), 1411)
        for index, line in enumerate(lines, 1):
            self.assertEqual(line, line.strip(), f"line {index} has leading whitespace")
            self.assertTrue(line.startswith("{"), f"line {index} is not an object")

    def test_r359_source_reextracts_the_committed_runtime_rows(self):
        if not _legacy_available():
            self.skipTest("legacy-mill-lane sbox mills are not in this environment")
        text = subprocess.check_output(
            ["git", "show", f"{SOURCE_COMMIT}:experiments/sbox-mill-r359.py"],
            cwd=REPO,
            text=True,
        )
        extracted = generate.plants_from_source(text)
        committed = [plant for plant in cat.load_catalog().plants if plant.shape == "runtime-dump"]
        self.assertEqual(len(extracted), 16)
        self.assertEqual(len(committed), 16)
        self.assertEqual(
            [(row["family"], row["ok"], row["over"], row["miss"]) for row in extracted],
            [(plant.family, plant.ok, plant.over, plant.miss) for plant in committed],
        )

    def test_leftover_sources_reextract_the_committed_identity_prefix(self):
        if not _legacy_available():
            self.skipTest("legacy-mill-lane sbox mills are not in this environment")
        leftover = subprocess.check_output(
            ["git", "show", f"{SOURCE_COMMIT}:experiments/sbox-mill-plants-leftover.py"],
            cwd=REPO,
            text=True,
        )
        leftover12 = subprocess.check_output(
            ["git", "show", f"{SOURCE_COMMIT}:experiments/sbox-mill-plants-leftover12.py"],
            cwd=REPO,
            text=True,
        )
        first_leftover = generate.plants_from_source(leftover)[:8]
        first_twelve = generate.plants_from_source(leftover12)[:8]
        committed = cat.load_catalog().plants
        self.assertEqual(
            [(row["family"], row["inc"]) for row in first_leftover],
            [(plant.family, plant.inc) for plant in committed[16:24]],
        )
        self.assertEqual(
            [(row["family"], row["inc"]) for row in first_twelve],
            [(plant.family, plant.inc) for plant in committed[24:32]],
        )
        self.assertEqual(len(generate.plants_from_source(leftover)), 30)
        self.assertEqual(len(generate.plants_from_source(leftover12)), 31)


class Cli(unittest.TestCase):
    def test_catalog_check_json_reports_the_slice(self):
        code, out, err = invoke(["catalog-check", "--json"])
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["plants"], 1411)
        self.assertEqual(payload["full_row_count"], 2678)
        self.assertEqual(payload["deferred_row_count"], 1267)

    def test_extract_json_from_a_runtime_snippet(self):
        handle = tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", suffix="-sbox-snippet.py", delete=False
        )
        handle.write(RUNTIME_SNIPPET)
        handle.close()
        snippet = Path(handle.name)
        self.addCleanup(snippet.unlink)
        code, out, err = invoke(["extract", "--source", str(snippet), "--json"])
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["plants"][0]["family"], "bpftrace-kprobe-write")


if __name__ == "__main__":
    unittest.main()
