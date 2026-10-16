"""TUP fail-closed branches reached through the public surface only.

``load_catalog`` / ``catalog_check`` on small pinned temp catalogs, the
``catalog_extract`` extractors on in-memory sources, and ``generate.run`` into
temp destinations. The one ``legacy-mill-lane`` read skips when the ref is
not fetchable.
"""

from __future__ import annotations

import importlib
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
support = importlib.import_module("mill_public_branch_support")
catalog = importlib.import_module("tup.catalog")
extract = importlib.import_module("tup.catalog_extract")
generate = importlib.import_module("tup.generate")
TupRefusal = importlib.import_module("tup._contract").TupRefusal

COMMITTED = support.REPO / "config" / "tup"
UNPARSEABLE = "SOURCE_NOT_PARSEABLE"
FAMILY = {
    "bin": "htmlq", "keep": "/plant/htmlq/k.conf", "grep": "g",
    "cmds": [["text", "-t a", "rm -f p"]],
}
EXTRA_PLANT = {
    "bin": "b", "destroy": "d", "grep": "g", "keep": "k", "mill_id": "tup_r9", "slug": "x-1",
    "verify": "v", "wait": 3,
}


def family_row(binary: str) -> str:
    """One ``(bin, keep, grep, cmds)`` family tuple as mill source text."""

    return f"({binary!r}, 'k', 'g', [('s', 'v', 'd')])"


def tiny_catalog(case, family=None, extra: bytes = b"", **changes) -> Path:
    """A pinned one-family tup catalog copy; ``extra`` becomes its plants-extra file."""

    copy = support.CatalogCopy(case, COMMITTED, (support.CATALOG_JSON,))
    families = support.compact_jsonl([family or FAMILY])
    meta = copy.read_json()
    meta.update(
        families=1,
        families_sha256=copy.write_bytes(families, "families.jsonl"),
        mills=[{"shape": "plants"}, {"shape": "rounds"}],
        plants=1 + len([line for line in extra.splitlines() if line]),
        plants_extra_filename="extra.jsonl" if extra else "",
        plants_extra_sha256=copy.write_bytes(extra, "extra.jsonl"),
    )
    meta.update(changes)
    copy.write_json(meta)
    return copy.directory


def rows_from(text: str):
    return extract.plant_rows_from_source(text, mill_id="m")


def leftover_refusal(text: str) -> tuple[str, str] | None:
    return support.refusal(TupRefusal, extract.leftover_plants_from_source, text, mill_id="m")


class TupCatalogLoading(unittest.TestCase):
    def test_unknown_mill_shapes_and_blank_extra_lines_are_skipped(self):
        extra = support.compact_jsonl([EXTRA_PLANT]) + b"\n"
        loaded = catalog.load_catalog(tiny_catalog(self, extra=extra))
        found = [plant.plant_id for plant in loaded.plants]
        self.assertEqual(found, ["tup_r1349:htmlq-text", "tup_r9:x-1"])

    def test_catalog_check_reports_source_pin_drift(self):
        directory = tiny_catalog(self, source_sha256="0" * 64, source_path="experiments/x.py")
        self.assertEqual(catalog.catalog_check(directory), [
            "source_sha256 pin drifted from _contract", "source_path pin drifted from _contract",
        ])

    def test_expansion_skips_yq_eval_and_pacman_even_when_unbanned(self):
        yq_cmds = (("eval", "v", "d"), ("q", ".", "rm y"))
        families = [
            catalog.Family(bin="yq", keep="k", grep="g", cmds=yq_cmds),
            catalog.Family(bin="pacman", keep="k", grep="g", cmds=(("q", "-Q", "-R x"),)),
        ]
        plants = catalog.expand_families(families, banned_slugs=(), banned_prefix=())
        self.assertEqual([(plant.slug, plant.destroy) for plant in plants], [("yq-q", "rm y")])


class TupRowExtract(unittest.TestCase):
    def test_eight_tuple_rows_fold_lists_and_negative_numbers(self):
        row = "('lo', 'slug-a', 'tool x', 'good', 'bad', 'src', ['v'], -4)"
        rows = rows_from(f"ROWS = None\nROWS = [{row}]\n")
        self.assertEqual(rows, [{
            "mill_id": "m", "slug": "slug-a", "bin": "tool", "verify": "good", "destroy": "bad",
            "keep": "/plant/slug-a/pay.conf", "wait": 3, "grep": "-4",
        }])

    def test_a_600_deep_minus_chain_folds_like_main(self):
        rows = rows_from("ROWS = [('lo', 's', 't', 'g', 'b', 'src', 'v', " + "-" * 600 + "1)]\n")
        self.assertEqual(rows[0]["grep"], "1")

    def test_malformed_rows_are_coded_refusals(self):
        for label, text, message in (
            ("name", "ROWS = [('a', b)]\n", "mill source is not a literal (Name)"),
            ("width five", "ROWS = [('a', 'b', 'c', 'd', 'e')]\n", "unsupported row width 5 in m"),
        ):
            with self.subTest(label):
                found = support.refusal(TupRefusal, rows_from, text)
                self.assertEqual(found, (UNPARSEABLE, message))

    def test_every_extractor_refuses_a_syntax_error(self):
        for extractor in (
            extract.plant_rows_from_source,
            extract.leftover_plants_from_source,
            extract.round_plants_from_source,
        ):
            with self.subTest(extractor.__name__):
                code, message = support.refusal(TupRefusal, extractor, "ROWS = [\n", mill_id="m")
                self.assertEqual(code, UNPARSEABLE)
                self.assertTrue(message.startswith("mill source is not parseable: "), message)


class TupLeftoverExtract(unittest.TestCase):
    def test_p_rows_take_grep_from_a_read_command(self):
        source = "PLANTS = [P(slug='a'), P(slug='b', read_cmd='grep -nE \"x|y\" f')]\n"
        rows = extract.leftover_plants_from_source(source, mill_id="m")
        found = [(row["slug"], row["bin"], row["grep"]) for row in rows]
        self.assertEqual(found, [("a", "", "pay|designed"), ("b", "", "x|y")])

    def test_an_unknown_builder_is_refused(self):
        expected = (UNPARSEABLE, "PLANTS[0] uses unsupported builder 'Q'")
        self.assertEqual(leftover_refusal("PLANTS = [Q()]\n"), expected)

    def test_the_widest_family_function_wins_even_when_it_comes_first(self):
        wide = f"def extra_v1():\n    families = [{family_row('a')}, {family_row('b')}]\n"
        narrow = f"def extra_v2():\n    families = [{family_row('c')}]\n"
        rows = extract.family_rows_from_source(wide + narrow)
        self.assertEqual([row["bin"] for row in rows], ["a", "b"])

    def test_sha256_bytes_is_the_hex_digest(self):
        self.assertEqual(extract.sha256_bytes(b"tup"), support.sha256_hex(b"tup"))

    def test_mill_sha256_matches_the_catalog_pin_when_the_legacy_ref_is_fetched(self):
        meta = json.loads((COMMITTED / support.CATALOG_JSON).read_text(encoding="utf-8"))
        if support.refusal(TupRefusal, extract.git_show_mill, meta["source_path"]) is not None:
            self.skipTest("legacy-mill-lane is not fetchable here")
        self.assertEqual(extract.mill_sha256(meta["source_path"]), meta["source_sha256"])


class TupGenerate(unittest.TestCase):
    def test_every_plant_runs_from_round_1349_and_long_bases_are_clipped(self):
        family = {**FAMILY, "keep": "/plant/" + "k" * 300}
        records = support.generated_records(self, generate, tiny_catalog(self, family=family))
        basis = records[0]["chosen"]["steps"][0]["decision_basis"]
        found = (records[0]["id"], len(basis), basis[-1])
        self.assertEqual(found, ("tup-r1349-htmlq-text", 240, "…"))

    def test_a_round_applies_only_to_one_plant(self):
        out = support.temp_dir(self) / "out"
        request = generate.GenerateRequest(COMMITTED, out, all_plants=True, round=1400)
        found = (support.refusal(TupRefusal, generate.run, request), out.exists())
        self.assertEqual(found, (("USAGE", "--round is only valid with --plant"), False))


if __name__ == "__main__":
    unittest.main()
