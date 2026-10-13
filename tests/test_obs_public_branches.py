"""OBS public surface: catalog load refusals, AST extract refusals, generate selection.

Every catalog case loads a mutated three-plant cut of ``config/obs`` (one hop
plant, one leftover3 pair, one leftover spec) out of a temp dir; every extract
case feeds an in-memory mill source to :func:`obs.catalog.plants_from_source`.
"""

from __future__ import annotations

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

from obs import catalog, generate
from obs._contract import ObsRefusal

COMMITTED = REPO / "config" / "obs"
FIXTURE = REPO / "tests" / "fixtures" / "obs" / "catalog"
COMMITTED_META = json.loads((COMMITTED / "CATALOG.json").read_text(encoding="utf-8"))
MEMBERS = (
    ("hop-plants.jsonl", "hop_plants_sha256"),
    ("leftover3-pairs.jsonl", "leftover3_pairs_sha256"),
    ("leftover-specs.jsonl", "leftover_specs_sha256"),
)
FIRST_ROWS = tuple(read_jsonl(COMMITTED / name)[0] for name, _ in MEMBERS)
HOP_ROW, L3_ROW, SPEC_ROW = FIRST_ROWS
SPEC_INDEX_KIND = "obs-leftover-spec-index/1"

CAT_INVALID = "obs.catalog_field_invalid"
CAT_MISSING = "obs.catalog_field_missing"
FILE_MISSING = "obs.catalog_file_missing"
DUPLICATE = "obs.plant_duplicate_id"
PLANT_INVALID = "obs.plant_field_invalid"
PLANT_MISSING = "obs.plant_field_missing"
NOT_PARSEABLE = "obs.source_not_parseable"
USAGE = "obs.usage"
ROUND_INVALID = "obs.round_invalid"
SHAPE_UNSUPPORTED = "obs.shape_unsupported"
MILL_NOT_FOUND = "obs.mill_not_found"
WRONG_TYPE = "has the wrong type"
NON_EMPTY = "must be a non-empty string"
R401_TAIL = (
    "'tiny-r401', 'tiny-r401-left', 'svc-a', 'lsvc-b', 'dash', 'ldash', '.yq', 'fail line',"
    " 'fix line', 'fv', 'xv', '.false.yq', 'false lead', 'fo', 'fn', 'fp', 'f2o', 'f2n',"
    " 'f2p', 'lie', 'llie', 'new_vs', 73"
)


def _hop_literal() -> str:
    row = {key: "x" for key in catalog.HOP_REQUIRED}
    row["slug"] = "tiny-hop"
    return repr(row)


class CatalogTree(unittest.TestCase):
    """Writes a mutated cut of the committed catalog into a temp dir."""

    def write(self, members=None, meta_edit=None) -> Path:
        members = [[row] for row in FIRST_ROWS] if members is None else members
        files = {}
        digests = {}
        for (name, digest_key), rows in zip(MEMBERS, members, strict=True):
            files[name] = jsonl_bytes(rows)
            digests[digest_key] = sha256_hex(files[name])
        all_rows = [row for rows in members for row in rows]
        meta = dict(COMMITTED_META, digests=digests, plant_count=len(all_rows))
        meta["mills"] = recounted_mills(COMMITTED_META["mills"], all_rows)
        if meta_edit is not None:
            meta = meta_edit(meta)
        files["CATALOG.json"] = json.dumps(meta, indent=2)
        return write_tree(self, files)

    def assert_loads_refused(self, cases) -> None:
        """Each ``(meta_edit, fragment, code)`` case refuses on load."""

        built = [(self.write(meta_edit=edit), fragment, code) for edit, fragment, code in cases]
        assert_each_refused(self, ObsRefusal, catalog.load_catalog, built)


class CatalogHeaderRefusals(CatalogTree):
    def test_header_fields_refuse_each_defect(self):
        self.assert_loads_refused(
            (
                (lambda meta: [meta], "CATALOG.json must be an object", CAT_INVALID),
                (setter("catalog_id", DELETE), "CATALOG.json.catalog_id is missing", CAT_MISSING),
                (setter("catalog_id", True), f"CATALOG.json.catalog_id {WRONG_TYPE}", CAT_INVALID),
                (setter("catalog_id", 7), f"CATALOG.json.catalog_id {WRONG_TYPE}", CAT_INVALID),
                (setter("catalog_id", ""), f"CATALOG.json.catalog_id {NON_EMPTY}", CAT_INVALID),
                (
                    setter("catalog_id", " obs "),
                    "CATALOG.json.catalog_id must be a stripped string",
                    CAT_INVALID,
                ),
                (
                    setter("factory", "other"),
                    "CATALOG.json.factory must be observability-debug-factory",
                    CAT_INVALID,
                ),
                (setter("mill_prefix", "hop"), "CATALOG.json.mill_prefix must be obs", CAT_INVALID),
                (
                    setter("record_kind", "preference"),
                    "CATALOG.json.record_kind must be episode",
                    CAT_INVALID,
                ),
                (
                    setter("plant_count", 4),
                    "CATALOG.json.plant_count is 4, files have 3",
                    CAT_INVALID,
                ),
            )
        )

    def test_member_pins_refuse_each_defect(self):
        self.assert_loads_refused(
            (
                (setter("files", {}), "CATALOG.json.files.hop_plants is missing", CAT_MISSING),
                (
                    setter("files", "hop_plants", "other.jsonl"),
                    "CATALOG.json.files.hop_plants must be hop-plants.jsonl",
                    CAT_INVALID,
                ),
                (
                    setter("digests", "hop_plants_sha256", DELETE),
                    "CATALOG.json.digests.hop_plants_sha256 is missing",
                    CAT_MISSING,
                ),
            )
        )

    def test_mill_rows_refuse_each_defect(self):
        where = "CATALOG.json.mills[0]"
        self.assert_loads_refused(
            (
                (setter("mills", ["obs_r245"]), f"{where} must be an object", CAT_INVALID),
                (
                    setter("mills", 0, "mill_id", "hop_r1"),
                    f"{where}.mill_id is not obs_*",
                    CAT_INVALID,
                ),
                (
                    setter("mills", 0, "base_round", 0),
                    f"{where}.base_round must be a positive int",
                    CAT_INVALID,
                ),
                (
                    setter("mills", 0, "plant_count", 0),
                    f"{where}.plant_count must be a positive int",
                    CAT_INVALID,
                ),
                (setter("mills", 0, "shape", ""), f"{where}.shape {NON_EMPTY}", CAT_INVALID),
                (setter("mills", 0, "plant_count", 2), "obs_r245 plant_count 2 != 1", CAT_INVALID),
            )
        )


class MemberFileRefusals(CatalogTree):
    def test_a_missing_member_file_is_refused(self):
        directory = self.write()
        (directory / "leftover3-pairs.jsonl").unlink()
        with refusal(self, ObsRefusal, "leftover3-pairs.jsonl is missing", FILE_MISSING):
            catalog.load_catalog(directory)

    def test_a_duplicated_row_is_refused_by_plant_id(self):
        directory = self.write(members=[[HOP_ROW, HOP_ROW], [L3_ROW], [SPEC_ROW]])
        with refusal(self, ObsRefusal, f"duplicate plant_id {HOP_ROW['plant_id']}", DUPLICATE):
            catalog.load_catalog(directory)

    def test_a_spec_index_total_must_match_the_pair_counts_pin(self):
        index = {
            "kind": SPEC_INDEX_KIND,
            "total": 2,
            "mills": [{"mill_id": SPEC_ROW["mill_id"], "count": 1, "first": "a", "last": "b"}],
        }

        def pin_counts(meta):
            mills = recounted_mills(COMMITTED_META["mills"], FIRST_ROWS)
            return dict(meta, mills=mills, plant_count=2, pair_counts={"leftover_specs": 1})

        directory = self.write(members=[[HOP_ROW], [L3_ROW], [index]], meta_edit=pin_counts)
        message = "CATALOG.json.pair_counts.leftover_specs is 1, index total is 2"
        with refusal(self, ObsRefusal, message, CAT_INVALID):
            catalog.load_catalog(directory)


class PlantRowRefusals(CatalogTree):
    def _refuse_rows(self, member, cases):
        built = []
        for path, value, fragment, code in cases:
            members = [[row] for row in FIRST_ROWS]
            members[member] = [edited(FIRST_ROWS[member], path, value) if path else value]
            built.append((self.write(members=members), fragment, code))
        assert_each_refused(self, ObsRefusal, catalog.load_catalog, built)

    def test_hop_rows_refuse_each_identity_defect(self):
        self._refuse_rows(
            0,
            (
                ((), "row", "plants:1 must be an object", PLANT_INVALID),
                (("mill_id",), "obs-1", "plants:1.mill_id is not obs_*", PLANT_INVALID),
                (("slug",), "-x", "plants:1.slug is not a plant slug", PLANT_INVALID),
                (
                    ("plant_id",),
                    "obs_r245:other",
                    f"plants:1.plant_id must be 'obs_r245:{HOP_ROW['slug']}'",
                    PLANT_INVALID,
                ),
                (("base_round",), 0, "plants:1.base_round must be an int >= 1", PLANT_INVALID),
                (("shape",), DELETE, f"plants:1.shape {NON_EMPTY}", PLANT_INVALID),
                (("source",), DELETE, f"plants:1.source {NON_EMPTY}", PLANT_MISSING),
            ),
        )

    def test_spec_rows_refuse_a_missing_spec_key(self):
        self._refuse_rows(2, ((("knob",), DELETE, "plants:3 missing knob", PLANT_MISSING),))


class CatalogSurface(CatalogTree):
    def test_default_directory_loads_the_committed_catalog(self):
        loaded = catalog.load_catalog()
        self.assertEqual(loaded.directory, COMMITTED)
        self.assertEqual(len(loaded.plants), COMMITTED_META["plant_count"])

    def test_mill_plants_refuses_an_unknown_mill(self):
        loaded = catalog.load_catalog(self.write())
        with refusal(self, ObsRefusal, "no mill 'obs_r0' in the catalog", MILL_NOT_FOUND):
            loaded.mill_plants("obs_r0")


class PlantsFromSourceRefusals(unittest.TestCase):
    def _extract(self, text, mill_id="obs_r7"):
        return catalog.plants_from_source(text, mill_id=mill_id, source="s.py")

    def test_annotated_pairs_are_read_and_an_unvalued_annotation_is_not(self):
        rows = self._extract(f"obj.attr = 1\nPAIRS: list = [{_hop_literal()}]\n")
        self.assertEqual(
            [(row["plant_id"], row["base_round"]) for row in rows], [("obs_r7:tiny-hop", 7)]
        )
        with refusal(self, ObsRefusal, "s.py has no plant literal", NOT_PARSEABLE):
            self._extract("PAIRS: list\n")

    def test_a_depth_600_negated_plant_value_evaluates(self):
        literal = _hop_literal()[:-1] + f", 'novel': {deep_negation()}" + "}"
        (row,) = self._extract(f"PAIRS = [{literal}]\n")
        self.assertEqual(row["novel"], 1)

    def test_source_level_refusals(self):
        cases = (
            ("PAIRS = [\n", "s.py does not parse", NOT_PARSEABLE),
            ("PAIRS = []\n", "s.py plant literal is empty", NOT_PARSEABLE),
            ("PAIRS = [P('tempo', 'x')]\n", "r401 P() expected 24 args, got 2", NOT_PARSEABLE),
            (f"PAIRS = [P('zzz', {R401_TAIL})]\n", "unknown r401 kind 'zzz'", NOT_PARSEABLE),
        )
        assert_each_refused(self, ObsRefusal, self._extract, cases)

    def test_spec_identity_keys_win_over_the_literal(self):
        spec = {key: "x" for key in catalog.SPEC_REQUIRED}
        spec.update(ok_slug="tiny-spec", mill_id="obs_other", family="other")
        (row,) = self._extract(f"SPECS = [{spec!r}]\n", mill_id="obs_leftover9")
        self.assertEqual((row["mill_id"], row["family"]), ("obs_leftover9", "leftover9"))
        self.assertEqual(row["plant_id"], "obs_leftover9:tiny-spec")

    def test_kind_ns_and_catalog_first_assignments_drive_r401_rows(self):
        head = "KIND_NS = {'zzz': ('zns', 'zdeploy')}\nCATALOG_FIRST = 9\n"
        (row,) = self._extract(f"{head}PAIRS = [P('zzz', {R401_TAIL})]\n", mill_id="obs_r401")
        self.assertEqual((row["ns"], row["deploy"], row["base_round"]), ("zns", "zdeploy", 9))
        self.assertEqual(row["file"], "zzz/dash.yaml")


class GenerateSelection(unittest.TestCase):
    def _run(self, **selector):
        out = scratch_dir(self) / "out"
        return generate.run(generate.GenerateRequest(FIXTURE, out, **selector))

    def test_selector_refusals(self):
        plant_id = catalog.load_catalog(FIXTURE).mill_plants("obs_r0002")[0].plant_id
        cases = (
            ({"plant_id": plant_id, "round": 0}, "round 0 is not a positive int", ROUND_INVALID),
            ({"mill_id": "obs_r0002", "round": 3}, "--round is only valid with --plant", USAGE),
            ({"mill_id": "obs_leftover9"}, "selector matched no hop or leftover3 plants", USAGE),
        )
        assert_each_refused(self, ObsRefusal, lambda selector: self._run(**selector), cases)

    def test_episodes_refuse_a_leftover_spec_plant(self):
        (spec,) = catalog.load_catalog(FIXTURE).mill_plants("obs_leftover9")
        message = f"generate refuses leftover-spec plant {spec.plant_id}"
        with refusal(self, ObsRefusal, message, SHAPE_UNSUPPORTED):
            generate.success_episode(9, spec, "cid")

    def test_a_long_decision_basis_is_clipped_to_the_limit(self):
        hop = catalog.load_catalog(FIXTURE).mill_plants("obs_r0002")[0]
        wide = replace(hop, payload=dict(hop.payload, file="f" * 300))
        basis = generate.success_episode(2, wide, "cid")["steps"][0]["decision_basis"]
        self.assertEqual((len(basis), basis[-1]), (240, "…"))


if __name__ == "__main__":
    unittest.main()
