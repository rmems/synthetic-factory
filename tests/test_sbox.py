#!/usr/bin/env python3
"""SBOX leftover mill: AST extract, representative catalog, no vendored mills."""

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
sys.path.insert(0, str(PIPELINES))

from mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES  # noqa: E402
from sbox import catalog as cat  # noqa: E402
from sbox import cli, generate  # noqa: E402
from sbox._contract import (  # noqa: E402
    CATALOG_ID,
    FACTORY,
    FAMILY_PREFIX,
    FINDING_AST_NOT_A_PLANT,
    FINDING_CATALOG_EMPTY,
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


_ROW_DEF = (
    "def _row(family, dump, miss_dump, secret, pin, pin_path, pin_needle, grep_hit, distinct,"
    " ext, miss_ext, live_bin, inc, over_slug, miss_slug, proc, allow, rotate):\n    return {}\n"
)
_ROW_ARGS = "'a', 'd', 'md', 's', 'p', 'pp', 'pn', 'g', 'di', 'e', 'me', 'l', 3, 'o', 'm', 'pr', 'al', 'ro'"
_TWO_DICT_ROWS = (
    "_ROWS = [dict(family='a', over_slug='o', miss_slug='m', inc=1, proc='p', note=f'{x}'),"
    " dict(family='b', over_slug='o2', miss_slug='m2', inc=-2, proc=f'p2')]\n"
)


def _families(source: str) -> list[str]:
    return [row["family"] for row in generate.plants_from_source(source)]


class AstExtractEdges(unittest.TestCase):
    """Literal shapes and the family-filter grammar on small in-memory sources."""

    def _refused(self, source: str, fragment: str) -> None:
        with self.assertRaises(SboxRefusal) as caught:
            generate.plants_from_source(source)
        self.assertEqual(caught.exception.code, FINDING_AST_NOT_A_PLANT)
        self.assertIn(fragment, str(caught.exception))

    def test_row_shapes_and_literal_forms(self):
        rows = generate.plants_from_source(_TWO_DICT_ROWS)
        self.assertEqual([(row["family"], row["inc"], row["proc"]) for row in rows],
                         [("a", 1, "p"), ("b", -2, "p2")])
        dict_rows = "_ROWS: list = [{'family': 'a', 'over_slug': 'o', 'miss_slug': 'm', 'inc': 1, 'proc': 'p', 9: 1}]\n"
        self.assertEqual(_families(dict_rows), ["a"])
        self.assertEqual(_families(_ROW_DEF + f"_ROWS = [_row({_ROW_ARGS}), other]\n"), ["a"])
        runtime = generate.plants_from_source(
            "PLANTS = [{'family': 'f', 'ok': 'o', 'over': 'v', 'miss': 'm', 'trigger': 't',"
            " 'vector': 'x', 'extra': [1, (2, -3)], 'more': dict(a=1)}]\n"
        )
        self.assertEqual(runtime[0]["vector"], "x")
        self.assertEqual(generate.plants_from_source("_ROWS = []\n"), ())

    def test_non_literal_rows_are_refused(self):
        self._refused(f"_ROWS = [_row({_ROW_ARGS})]\n", "no def _row is in the module")
        self._refused("_ROWS = ['a']\n", "_ROWS list shape is not")
        self._refused("_ROWS = [tuple(x)]\n", "_ROWS list shape is not")
        self._refused("PLANTS = [{**base}]\n", "dict unpacking")
        self._refused("PLANTS = [{'family': dict(**a)}]\n", "non-literal call (Call)")
        self._refused("PLANTS = [{'family': dict('a')}]\n", "non-literal call (Call)")
        self._refused("PLANTS = [{'family': f(a=1)}]\n", "non-literal call (Call)")
        self._refused("PLANTS = [{'family': x.y}]\n", "not a constant (Attribute)")
        self._refused("_ROWS = [dict(family=f'a{b}')]\n", "f-string plant field is not a constant")

    def test_a_deep_dict_and_negation_nest_evaluates_before_the_identity_check(self):
        # One stack frame per nesting level, as on main: 150 dicts around a 600-deep
        # negation evaluate, and the row is refused for its missing family.
        nest = "{'a': " * 150 + "-" * 600 + "1" + "}" * 150
        with self.assertRaises(SboxRefusal) as caught:
            generate.plants_from_source(f"PLANTS = [{nest}]\n")
        self.assertEqual(caught.exception.code, FINDING_FIELD_MISSING)
        self.assertIn("PLANTS[0] missing family", str(caught.exception))

    def test_a_rows_rebinding_of_another_shape_is_ignored(self):
        self.assertEqual(_families(_TWO_DICT_ROWS + "_ROWS = tuple(_ROWS)\n"), ["a", "b"])

    def test_only_a_literal_family_inequality_filters_rows(self):
        self.assertEqual(
            _families(_TWO_DICT_ROWS + "_ROWS = [r for r in _ROWS if r['family'] != 'a']\n"), ["b"]
        )
        for comprehension in (
            "[r for r in _ROWS if r['family'] == 'a']",
            "[r for r in _ROWS if r['kind'] != 'a']",
            "[r for r in _ROWS if q['family'] != 'a']",
            "[r for r in _ROWS if r['family'] != 1]",
            "[r for r in _ROWS if r['family'] != 'a' != 'b']",
            "[r for r in _ROWS if r['family'] != 'a' if r]",
            "[r for r in OTHER if r['family'] != 'a']",
            "[q for q in _ROWS if q['family'] != 'a']",
            "[r for x in _ROWS if r['family'] != 'a']",
            "[r for r in _ROWS for s in _ROWS if r['family'] != 'a']",
            "[r for r in _ROWS if r.family != 'a']",
        ):
            with self.subTest(comprehension=comprehension):
                self._refused(f"{_TWO_DICT_ROWS}_ROWS = {comprehension}\n", "not a supported family")
        self._refused("_ROWS = [r for r in _ROWS if r['family'] != 'a']\n" + _TWO_DICT_ROWS,
                      "not a supported family")


class CommittedCatalog(unittest.TestCase):
    def test_a_catalog_without_source_pins_is_refused(self):
        root = Path(tempfile.mkdtemp(prefix="sbox-pins-"))
        self.addCleanup(shutil.rmtree, root, True)
        for name in ("CATALOG.json", "plants.jsonl"):
            shutil.copy(cat.catalog_path().parent / name, root / name)
        meta_path = root / "CATALOG.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        for sources in ([], None):
            meta["sources"] = sources
            meta_path.write_text(json.dumps(meta), encoding="utf-8")
            with self.subTest(sources=sources), self.assertRaises(SboxRefusal) as caught:
                cat.load_catalog(meta_path)
            self.assertEqual(caught.exception.code, FINDING_CATALOG_EMPTY)

    def test_jsonl_slice_and_full_row_pins(self):
        loaded = cat.load_catalog()
        report = cat.catalog_check()
        self.assertEqual(loaded.catalog_id, CATALOG_ID)
        self.assertEqual(loaded.factory, FACTORY)
        self.assertEqual(len(loaded.plants), 2612)
        self.assertEqual(len(loaded.sources), 65)
        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["plants"], 2612)
        self.assertEqual(report["full_row_count"], 2678)
        self.assertEqual(report["deferred_row_count"], 66)
        self.assertEqual(report["catalog_files"], 57)
        self.assertFalse(report["exec"])
        self.assertEqual(loaded.plants[0].family, "bpftrace-kprobe-write")
        self.assertEqual(loaded.plants[0].ok, "bpftrace-kprobe-write-ticket-refuse")
        self.assertEqual(loaded.plants[16].family, "leftover-bpftool-map")
        self.assertEqual(loaded.plants[16].inc, 4900)
        self.assertEqual(loaded.plants[46].family, "leftover-memcached-dump")
        self.assertEqual(loaded.plants[46].inc, 7236)
        families = [f"{plant.source}:{plant.family}" for plant in loaded.plants]
        self.assertEqual(len(families), len(set(families)))

    def test_plants_jsonl_is_one_compact_object_per_line(self):
        payload = (PACKAGE / "plants.jsonl").read_text(encoding="utf-8")
        self.assertTrue(payload.endswith("\n"))
        self.assertNotIn("\r", payload)
        lines = payload.split("\n")
        if lines[-1] == "":
            lines = lines[:-1]
        self.assertEqual(len(lines), 2612)
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
        committed = [
            plant
            for plant in cat.load_catalog().plants
            if plant.source == "experiments/sbox-mill-r359.py"
        ]
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
        committed = cat.load_catalog().plants
        leftover_committed = [
            plant for plant in committed if plant.source == "experiments/sbox-mill-plants-leftover.py"
        ]
        twelve_committed = [
            plant
            for plant in committed
            if plant.source == "experiments/sbox-mill-plants-leftover12.py"
        ]
        self.assertEqual(
            [(row["family"], row["inc"]) for row in generate.plants_from_source(leftover)],
            [(plant.family, plant.inc) for plant in leftover_committed],
        )
        self.assertEqual(
            [(row["family"], row["inc"]) for row in generate.plants_from_source(leftover12)],
            [(plant.family, plant.inc) for plant in twelve_committed],
        )
        self.assertEqual(len(leftover_committed), 30)
        self.assertEqual(len(twelve_committed), 31)


class Cli(unittest.TestCase):
    def test_catalog_check_json_reports_the_slice(self):
        code, out, err = invoke(["catalog-check", "--json"])
        self.assertEqual((code, err), (0, ""))
        payload = json.loads(out)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["plants"], 2612)
        self.assertEqual(payload["full_row_count"], 2678)
        self.assertEqual(payload["deferred_row_count"], 66)

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
