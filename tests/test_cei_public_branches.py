"""CEI public surface: catalog load refusals, AST extract refusals, generate selection.

Every catalog case loads a mutated two-plant cut of ``config/cei`` (one
``_ok``/``_bad`` plant from r81 and one leftover3 ``S()`` plant from r48) out of
a temp dir; every extract case feeds an in-memory mill source to
:func:`cei.catalog.plants_from_source`.
"""

from __future__ import annotations

import functools
import json
import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from mill_catalog_public_support import (
    DELETE,
    PIPELINES,
    REPO,
    assert_each_refused,
    deep_negation,
    edited,
    jsonl_bytes,
    read_jsonl,
    recounted_mills,
    refusal,
    scratch_dir,
    setter,
    sha256_hex,
    write_tree,
)

sys.path.insert(0, str(PIPELINES))

from cei import catalog, generate
from cei._contract import CeiRefusal

COMMITTED = REPO / "config" / "cei"
FIXTURE = REPO / "tests" / "fixtures" / "cei"
COMMITTED_META = json.loads((COMMITTED / "CATALOG.json").read_text(encoding="utf-8"))
COMMITTED_ROWS = read_jsonl(COMMITTED / "plants.jsonl")
OK_BAD_ROW = next((row for row in COMMITTED_ROWS if "shape" not in row), None)
L3_ROW = next((row for row in COMMITTED_ROWS if row.get("shape") == "leftover3-s"), None)
BASE_ROWS = (OK_BAD_ROW, L3_ROW)
BANNED_L3_SLUG = "xlsx-slicercache-vs-used"

CAT_INVALID = "cei.catalog_field_invalid"
CAT_MISSING = "cei.catalog_field_missing"
DUPLICATE = "cei.plant_duplicate_id"
PLANT_INVALID = "cei.plant_field_invalid"
PLANT_MISSING = "cei.plant_field_missing"
NOT_PARSEABLE = "cei.source_not_parseable"
LEFTOVER3_EXEC = "cei.leftover3_exec"
USAGE = "cei.usage"
GOAL_INVALID = "cei.goal_invalid"
ROUND_INVALID = "cei.round_invalid"
MILL_NOT_FOUND = "cei.mill_not_found"
WRONG_TYPE = "has the wrong type"
STRIPPED = "must be a non-empty stripped string"

OK_ARGS = {
    "slug": "tiny-csv-sniffer",
    "goal": "Honor csv.Sniffer dialect.",
    "mod": "csvsni",
    "stack": "csv.Sniffer dialect",
    "docs": "https://docs.python.org/3/library/csv.html",
    "first_old": "return {'header': True}",
    "first_new": "    return {'header': False}",
    "fix_new": "    return {'kind': 'csvsni'}",
}
BAD_ARGS = {
    "slug": "tiny-dbase-handoff",
    "goal": "Hand off dBase memo.",
    "mod": "dbfmem",
    "stack": "dBase memo .dbt",
    "docs": "https://example.test/dbt",
    "first_old": "return {'rows': True}",
    "first_new": "    return {'rows': False}",
    "ticket": "DBF-TINY-7",
}


def _side_call(name: str, side: dict) -> str:
    args = ", ".join(f"{key}={value!r}" for key, value in side.items())
    return f"{name}({args})"


def _s_args(side: dict) -> dict:
    return {key: value for key, value in side.items() if key != "wrong"}


def _ok_bad_source(ok: str = _side_call("_ok", OK_ARGS), head: str = "") -> str:
    return f"{head}PAIRS = [({ok}, {_side_call('_bad', BAD_ARGS)})]\n"


def _s_pair(ok: dict) -> str:
    return f"({_side_call('S', ok)}, {_side_call('S', _s_args(L3_ROW['bad']))})"


def _dict_pair(ok: dict) -> str:
    return f"({_s_args(ok)!r}, {_s_args(L3_ROW['bad'])!r})"


def _extract(text, mill_id="cei_r0007"):
    return catalog.plants_from_source(text, mill_id=mill_id, source="s.py")


class CatalogTree:
    """Mixin: writes a mutated cut of the committed catalog into a temp dir."""

    def write(self, rows=BASE_ROWS, meta_edit=None, payload: bytes | None = None) -> Path:
        payload = jsonl_bytes(rows) if payload is None else payload
        meta = dict(
            COMMITTED_META,
            mills=recounted_mills(COMMITTED_META["mills"], rows),
            plant_count=len(rows),
        )
        meta["plants_sha256"] = sha256_hex(payload)
        if meta_edit is not None:
            meta = meta_edit(meta)
        return write_tree(
            self, {"CATALOG.json": json.dumps(meta, indent=2), "plants.jsonl": payload}
        )

    def assert_loads_refused(self, cases) -> None:
        """Each ``(directory, fragment, code)`` case refuses on load."""

        assert_each_refused(self, CeiRefusal, catalog.load_catalog, cases)

    def refuse_meta(self, cases) -> None:
        self.assert_loads_refused([(self.write(meta_edit=edit), *rest) for edit, *rest in cases])

    def refuse_row(self, index, cases) -> None:
        built = []
        for path, value, fragment, code in cases:
            rows = list(BASE_ROWS)
            rows[index] = edited(rows[index], path, value)
            built.append((self.write(rows=rows), fragment, code))
        self.assert_loads_refused(built)


class CatalogHeaderRefusals(CatalogTree, unittest.TestCase):
    def test_header_fields_refuse_each_defect(self):
        self.refuse_meta(
            (
                (lambda meta: [meta], "CATALOG.json must be an object", CAT_INVALID),
                (setter("catalog_id", DELETE), "CATALOG.json.catalog_id is missing", CAT_MISSING),
                (setter("catalog_id", True), f"CATALOG.json.catalog_id {WRONG_TYPE}", CAT_INVALID),
                (setter("catalog_id", 7), f"CATALOG.json.catalog_id {WRONG_TYPE}", CAT_INVALID),
                (setter("catalog_id", " cei "), f"CATALOG.json.catalog_id {STRIPPED}", CAT_INVALID),
                (setter("catalog_id", ""), f"CATALOG.json.catalog_id {STRIPPED}", CAT_INVALID),
                (
                    setter("factory", "other"),
                    "CATALOG.json.factory must be csv-excel-ingest-factory",
                    CAT_INVALID,
                ),
                (setter("mill_prefix", "hop"), "CATALOG.json.mill_prefix must be cei", CAT_INVALID),
                (
                    setter("record_kind", "preference"),
                    "CATALOG.json.record_kind must be episode",
                    CAT_INVALID,
                ),
                (
                    setter("quota_per_round", 3),
                    "CATALOG.json.quota_per_round must be 2",
                    CAT_INVALID,
                ),
                (
                    setter("quota_per_round", True),
                    f"CATALOG.json.quota_per_round {WRONG_TYPE}",
                    CAT_INVALID,
                ),
                (setter("mills", {}), f"CATALOG.json.mills {WRONG_TYPE}", CAT_INVALID),
            )
        )

    def test_mill_rows_refuse_each_defect(self):
        where = "CATALOG.json.mills[0]"
        self.refuse_meta(
            (
                (setter("mills", ["cei_r81"]), f"{where} must be an object", CAT_INVALID),
                (
                    setter("mills", 0, "mill_id", "hop_r1"),
                    f"{where}.mill_id is not cei_rNNN",
                    CAT_INVALID,
                ),
                (
                    setter("mills", 0, "base_round", 0),
                    f"{where}.base_round must be a positive int",
                    CAT_INVALID,
                ),
                (
                    setter("mills", 0, "base_round", True),
                    f"{where}.base_round {WRONG_TYPE}",
                    CAT_INVALID,
                ),
                (
                    setter("mills", 0, "plant_count", 0),
                    f"{where}.plant_count must be a positive int",
                    CAT_INVALID,
                ),
                (setter("mills", 0, "source", ""), f"{where}.source {STRIPPED}", CAT_INVALID),
                (setter("mills", 0, "plant_count", 2), "cei_r81 plant_count 2 != 1", CAT_INVALID),
                (
                    setter("mills", 0, "mill_id", "cei_r9999"),
                    "catalog mills do not match plant mill_id values",
                    CAT_INVALID,
                ),
            )
        )

    def test_catalog_json_that_is_not_strict_json_is_refused(self):
        directory = self.write()
        (directory / "CATALOG.json").write_text("{", encoding="utf-8")
        self.assert_loads_refused(((directory, "CATALOG.json is not strict JSON", CAT_INVALID),))


class PlantsFileRefusals(CatalogTree, unittest.TestCase):
    def test_framing_refuses_each_malformed_file(self):
        first, second = (line.decode("utf-8") for line in jsonl_bytes(BASE_ROWS).splitlines())
        cases = (
            (f"{first}\n{second}", "plants.jsonl must be LF-framed jsonl"),
            (f"{first}\n\n{second}\n", "plants.jsonl:2 is empty"),
            (f"{first}\n{{nope\n", "plants.jsonl:2 is not strict JSON"),
        )
        built = [
            (self.write(payload=text.encode("utf-8")), fragment, CAT_INVALID)
            for text, fragment in cases
        ]
        self.assert_loads_refused(built)

    def test_duplicated_identities_are_refused(self):
        twin = edited(L3_ROW, ("bad", "slug"), OK_BAD_ROW["bad"]["slug"])
        self.assert_loads_refused(
            (
                (
                    self.write(rows=(OK_BAD_ROW, OK_BAD_ROW)),
                    f"duplicate plant_id {OK_BAD_ROW['plant_id']}",
                    DUPLICATE,
                ),
                (
                    self.write(rows=(OK_BAD_ROW, twin)),
                    f"duplicate slug {OK_BAD_ROW['bad']['slug']}",
                    DUPLICATE,
                ),
            )
        )


class PlantRowRefusals(CatalogTree, unittest.TestCase):
    def test_plant_identity_refuses_each_defect(self):
        where = "plants.jsonl:1"
        self.refuse_row(
            0,
            (
                (("mill_id",), DELETE, f"{where}.mill_id {STRIPPED}", PLANT_INVALID),
                (
                    ("plant_id",),
                    "cei_r81:other",
                    f"{where}.plant_id must be 'cei_r81:{OK_BAD_ROW['ok']['slug']}'",
                    PLANT_INVALID,
                ),
                (("source",), DELETE, f"{where}.source {STRIPPED}", PLANT_MISSING),
            ),
        )

    def test_ok_bad_sides_refuse_each_defect(self):
        where = "plants.jsonl:1.ok"
        self.refuse_row(
            0,
            (
                (("ok",), "side", f"{where} must be an object", PLANT_INVALID),
                (("ok", "goal"), DELETE, f"{where} missing goal", PLANT_MISSING),
                (("ok", "extra"), 1, f"{where} has extra extra", PLANT_INVALID),
                (("ok", "mod"), " csv", f"{where}.mod {STRIPPED}", PLANT_INVALID),
                (
                    ("ok", "goal"),
                    "a\r\nb",
                    f"{where}.goal must be a non-empty LF string",
                    PLANT_INVALID,
                ),
                (("ok", "slug"), "-csv", f"{where}.slug is not a plant slug", PLANT_INVALID),
                (("ok", "domain"), "prism-index", f"{where} carries banned 'prism'", PLANT_INVALID),
                (
                    ("ok", "first_old"),
                    "absent()",
                    f"{where}.first_old is not in src_body",
                    PLANT_INVALID,
                ),
            ),
        )

    def test_leftover3_sides_refuse_each_defect(self):
        where = "plants.jsonl:2.ok"
        self.refuse_row(
            1,
            (
                (("ok",), [], f"{where} must be an object", PLANT_INVALID),
                (("ok", "fix"), DELETE, f"{where} missing fix", PLANT_MISSING),
                (("ok", "extra"), 1, f"{where} has extra extra", PLANT_INVALID),
                (("ok", "slug"), "-x", f"{where}.slug is not a plant slug", PLANT_INVALID),
                (
                    ("ok", "slug"),
                    BANNED_L3_SLUG,
                    f"{where} slug is banned {BANNED_L3_SLUG!r}",
                    PLANT_INVALID,
                ),
                (
                    ("ok", "wrong"),
                    "unlink(path)",
                    f"{where}.wrong must be 'os.remove(path)'",
                    PLANT_INVALID,
                ),
            ),
        )


class CatalogSurface(CatalogTree, unittest.TestCase):
    def test_default_directory_loads_the_committed_catalog(self):
        loaded = catalog.load_catalog()
        self.assertEqual(loaded.directory, COMMITTED)
        self.assertEqual(len(loaded.plants), COMMITTED_META["plant_count"])

    def test_mill_plants_selects_one_mill_and_refuses_an_unknown_one(self):
        loaded = catalog.load_catalog(self.write())
        self.assertEqual([p.plant_id for p in loaded.mill_plants("cei_r48")], [L3_ROW["plant_id"]])
        with refusal(self, CeiRefusal, "no mill 'cei_r0' in the catalog", MILL_NOT_FOUND):
            loaded.mill_plants("cei_r0")

    def test_side_mappings_round_trip_the_committed_rows(self):
        ok_bad, leftover3 = catalog.load_catalog(self.write()).plants
        self.assertEqual(ok_bad.ok.as_mapping(), OK_BAD_ROW["ok"])
        self.assertEqual(ok_bad.bad.as_mapping(), OK_BAD_ROW["bad"])
        self.assertEqual(leftover3.ok.as_mapping(), L3_ROW["ok"])
        self.assertEqual(leftover3.bad.as_mapping(), L3_ROW["bad"])


class PlantsFromSourceRefusals(unittest.TestCase):
    def test_annotated_pairs_are_read_and_an_unvalued_annotation_is_not(self):
        text = _ok_bad_source(head="obj.attr = 1\n").replace("PAIRS =", "PAIRS: list =")
        rows = _extract(text, mill_id="cei_r7")
        self.assertEqual([row["plant_id"] for row in rows], ["cei_r7:tiny-csv-sniffer"])
        with refusal(self, CeiRefusal, "s.py has no PAIRS list", NOT_PARSEABLE):
            _extract("PAIRS: list\n")

    def test_a_depth_600_negated_catalog_first_evaluates(self):
        rows = _extract(_ok_bad_source(head=f"CATALOG_FIRST = {deep_negation()}\n"))
        self.assertEqual(rows[0]["base_round"], 1)

    def test_source_level_refusals(self):
        nine = ", ".join(repr(str(n)) for n in range(9))
        banned = _side_call("_ok", dict(OK_ARGS, slug="prism-sniffer"))
        assert_each_refused(
            self,
            CeiRefusal,
            _extract,
            (
                ("PAIRS = [\n", "s.py does not parse", NOT_PARSEABLE),
                (
                    _ok_bad_source(head="CATALOG_FIRST = 0\n"),
                    "s.py CATALOG_FIRST must be a positive int",
                    PLANT_INVALID,
                ),
                (
                    _ok_bad_source(head="CATALOG_FIRST = True\n"),
                    "s.py CATALOG_FIRST must be a positive int",
                    PLANT_INVALID,
                ),
                (
                    _ok_bad_source(head="from cei_r48_mill import S\n"),
                    "s.py leftover leftover leftover leftover3 imports a foreign mill",
                    LEFTOVER3_EXEC,
                ),
                (
                    _ok_bad_source(ok=f"_ok({nine})"),
                    "s.py PAIRS[0].ok has extra positional args",
                    NOT_PARSEABLE,
                ),
                (
                    _ok_bad_source(ok="_ok(**kw)"),
                    "s.py PAIRS[0].ok uses star-kwargs",
                    NOT_PARSEABLE,
                ),
                (
                    _ok_bad_source(ok=banned),
                    "s.py PAIRS[0].ok carries banned 'prism'",
                    PLANT_INVALID,
                ),
            ),
        )

    def test_leftover3_pair_refusals(self):
        s_ok = _s_args(L3_ROW["ok"])
        banned = edited(L3_ROW["ok"], ("slug",), BANNED_L3_SLUG)
        extract = functools.partial(_extract, mill_id="cei_r48")
        assert_each_refused(
            self,
            CeiRefusal,
            extract,
            (
                (
                    f"PAIRS = [{_s_pair(s_ok)}, 1]\n",
                    "s.py PAIRS[1] is not an (S, S) leftover leftover leftover tuple",
                    NOT_PARSEABLE,
                ),
                (
                    f"PAIRS = [{_s_pair(_s_args(banned))}]\n",
                    f"s.py PAIRS[0].ok slug is banned {BANNED_L3_SLUG!r}",
                    PLANT_INVALID,
                ),
                (
                    f"PAIRS = [{_dict_pair(L3_ROW['ok'])}, 1]\n",
                    "s.py PAIRS[1] is not a leftover leftover leftover dict tuple",
                    NOT_PARSEABLE,
                ),
                (
                    f"PAIRS = [{_dict_pair(banned)}]\n",
                    "s.py has no committable leftover dict pairs",
                    NOT_PARSEABLE,
                ),
            ),
        )

    def test_dict_pairs_skip_a_banned_slug_and_keep_the_rest(self):
        banned = edited(L3_ROW["ok"], ("slug",), BANNED_L3_SLUG)
        rows = _extract(f"PAIRS = [{_dict_pair(banned)}, {_dict_pair(L3_ROW['ok'])}]\n", "cei_r42")
        self.assertEqual(
            [(row["index"], row["ok"]["slug"]) for row in rows], [(0, L3_ROW["ok"]["slug"])]
        )


class ExpandLeftover3Refusals(unittest.TestCase):
    def test_a_handoff_ticket_that_is_not_text_is_refused(self):
        args = dict(_s_args(L3_ROW["bad"]), ticket=1)
        with refusal(self, CeiRefusal, "S() handoff missing ticket", NOT_PARSEABLE):
            catalog.expand_leftover3(args, ticket_required=True)

    def test_a_success_side_carrying_a_ticket_is_refused(self):
        args = dict(_s_args(L3_ROW["ok"]), ticket="T-1")
        with refusal(self, CeiRefusal, "S() success side must omit ticket", NOT_PARSEABLE):
            catalog.expand_leftover3(args, ticket_required=False)


class GenerateSelection(CatalogTree, unittest.TestCase):
    def _run(self, directory, **selector):
        return generate.run(
            generate.GenerateRequest(directory, scratch_dir(self) / "out", **selector)
        )

    def test_mill_and_all_plant_selectors_emit_one_pair_per_plant(self):
        directory = self.write()
        by_mill = self._run(directory, mill_id="cei_r81")
        everything = self._run(directory, all_plants=True)
        self.assertEqual((by_mill["pairs"], by_mill["records"]), (1, 2))
        self.assertEqual((everything["pairs"], everything["records"]), (2, 4))

    def test_round_selector_refusals(self):
        plant_id = catalog.load_catalog(FIXTURE).plants[0].plant_id
        assert_each_refused(
            self,
            CeiRefusal,
            lambda selector: self._run(FIXTURE, **selector),
            (
                ({"mill_id": "cei_r0001", "round": 3}, "round applies only with plant_id", USAGE),
                (
                    {"plant_id": plant_id, "round": 0},
                    "round must be a positive int, got 0",
                    ROUND_INVALID,
                ),
            ),
        )

    def test_a_refused_pair_removes_the_new_destination(self):
        directory = self.write(rows=(edited(OK_BAD_ROW, ("ok", "goal"), "todo"),))
        out = scratch_dir(self) / "out"
        request = generate.GenerateRequest(directory, out, all_plants=True)
        with refusal(self, CeiRefusal, "placeholder goal: 'todo'", GOAL_INVALID):
            generate.run(request)
        self.assertFalse(out.exists())


class EpisodeBuilderRefusals(CatalogTree, unittest.TestCase):
    def setUp(self):
        self.ok_bad, self.leftover3 = catalog.load_catalog(self.write()).plants

    def test_success_builder_refuses_bad_goals_and_steps(self):
        side = self.ok_bad.ok
        build = functools.partial(generate.build_success, 81, catalog_id="cid", plant=self.ok_bad)
        assert_each_refused(
            self,
            CeiRefusal,
            build,
            (
                (
                    replace(side, goal="[variant 2] tidy"),
                    "variant stamp in goal: '[variant 2] tidy'",
                    GOAL_INVALID,
                ),
                (replace(side, mod="m" * 240), "step 1 decision_basis", USAGE),
                (replace(side, test_body="   "), "step 3 empty observation/reflection", USAGE),
            ),
        )

    def test_pair_records_refuse_sides_that_do_not_match_the_shape(self):
        twin_ids = replace(self.ok_bad, bad=replace(self.ok_bad.bad, slug=self.ok_bad.ok.slug))
        pair = functools.partial(generate.pair_records, 81, catalog_id="cid")
        assert_each_refused(
            self,
            CeiRefusal,
            pair,
            (
                (
                    replace(self.ok_bad, shape="leftover3-s"),
                    f"{self.ok_bad.plant_id} leftover leftover leftover sides",
                    USAGE,
                ),
                (
                    replace(self.leftover3, shape="ok-bad"),
                    f"{self.leftover3.plant_id} hop-mill sides",
                    USAGE,
                ),
                (twin_ids, "duplicate episode ids", USAGE),
            ),
        )

    def test_notes_refuse_sides_that_do_not_match_the_shape(self):
        records = generate.pair_records(81, self.ok_bad, "cid")
        notes = functools.partial(generate.notes_markdown, 81, records=records)
        assert_each_refused(
            self,
            CeiRefusal,
            notes,
            (
                (
                    replace(self.ok_bad, shape="leftover3-s"),
                    f"{self.ok_bad.plant_id} leftover leftover leftover notes",
                    USAGE,
                ),
                (
                    replace(self.leftover3, shape="ok-bad"),
                    f"{self.leftover3.plant_id} hop-mill notes",
                    USAGE,
                ),
            ),
        )


if __name__ == "__main__":
    unittest.main()
