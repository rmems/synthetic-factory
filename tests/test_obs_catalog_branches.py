"""Branch coverage for pipelines/obs/catalog.py: coded refusals and AST extraction paths."""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "tests" / "fixtures" / "obs" / "catalog"

sys.path.insert(0, str(REPO / "pipelines"))

from obs import _contract as contract
from obs import catalog
from obs._contract import (
    CATALOG_FILENAME,
    FINDING_CATALOG_FILE_MISSING,
    FINDING_FACTORY_NOT_REGISTERED,
    FINDING_MILL_NOT_FOUND,
    FINDING_PLANT_DUPLICATE_ID,
    HOP_FILENAME,
    LEFTOVER_SPECS_FILENAME,
    ObsRefusal,
)

FIELD_INVALID = contract.FINDING_CATALOG_FIELD_INVALID
FIELD_MISSING = contract.FINDING_CATALOG_FIELD_MISSING
PLANT_INVALID = contract.FINDING_PLANT_FIELD_INVALID
PLANT_MISSING = contract.FINDING_PLANT_FIELD_MISSING
NOT_PARSEABLE = contract.FINDING_SOURCE_NOT_PARSEABLE

DIGEST_KEYS = {
    "hop-plants.jsonl": "hop_plants_sha256",
    "leftover3-pairs.jsonl": "leftover3_pairs_sha256",
    "leftover-specs.jsonl": "leftover_specs_sha256",
}
SPEC_INDEX = {
    "kind": catalog.SPEC_INDEX_KIND,
    "total": 1,
    "mills": [{"mill_id": "obs_leftover9", "count": 1, "first": "a", "last": "b"}],
}


def _rows(filename: str) -> list:
    text = (FIXTURE / filename).read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines()]


def _set(path: tuple, value) -> callable:
    def edit(doc):
        for key in path[:-1]:
            doc = doc[key]
        doc[path[-1]] = value
    return edit


def _drop(path: tuple) -> callable:
    def edit(doc):
        for key in path[:-1]:
            doc = doc[key]
        del doc[path[-1]]
    return edit


def _spec_index_meta(meta):
    meta["plant_count"] = 2


class CatalogTreeMixin:
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="obs-cat-")
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.count = 0

    def build(self, meta_edit=None, rows=None, row_edit=None) -> Path:
        self.count += 1
        dest = self.root / f"c{self.count}"
        dest.mkdir()
        meta = json.loads((FIXTURE / CATALOG_FILENAME).read_text(encoding="utf-8"))
        members = {name: _rows(name) for name in DIGEST_KEYS}
        members.update(rows or {})
        if row_edit:
            row_edit(members[HOP_FILENAME])
        for name, items in members.items():
            payload = "".join(json.dumps(item) + "\n" for item in items).encode()
            (dest / name).write_bytes(payload)
            meta["digests"][DIGEST_KEYS[name]] = hashlib.sha256(payload).hexdigest()
        if meta_edit:
            meta_edit(meta)
        (dest / CATALOG_FILENAME).write_text(json.dumps(meta), encoding="utf-8")
        return dest

    def assertRefuses(self, code, directory):
        with self.assertRaises(ObsRefusal) as caught:
            catalog.load_catalog(directory)
        self.assertEqual(caught.exception.code, code, caught.exception.message)


class CatalogLoadRefusals(CatalogTreeMixin, unittest.TestCase):
    def test_catalog_lookups_and_default_dir(self):
        loaded = catalog.load_catalog(self.build())
        self.assertEqual(len(loaded.mill_plants("obs_r0002")), 1)
        with self.assertRaises(ObsRefusal) as caught:
            loaded.mill_plants("obs_r9999")
        self.assertEqual(caught.exception.code, FINDING_MILL_NOT_FOUND)
        self.assertEqual(catalog.default_catalog_dir(), REPO / "config" / "obs")
        self.assertEqual(catalog.catalog_check(self.build()), [])

    def test_meta_field_refusals(self):
        cases = [
            ("catalog_id missing", _drop(("catalog_id",)), FIELD_MISSING),
            ("catalog_id blank", _set(("catalog_id",), " "), FIELD_INVALID),
            ("catalog_id unstripped", _set(("catalog_id",), "x "), FIELD_INVALID),
            ("format", _set(("format",), "obs-catalog/2"), FIELD_INVALID),
            ("factory", _set(("factory",), "other"), FIELD_INVALID),
            ("mill_prefix", _set(("mill_prefix",), "x"), FIELD_INVALID),
            ("record_kind", _set(("record_kind",), "preference"), FIELD_INVALID),
            ("quota bool", _set(("quota_per_round",), True), FIELD_INVALID),
            ("quota value", _set(("quota_per_round",), 3), FIELD_INVALID),
            ("plant_count", _set(("plant_count",), 4), FIELD_INVALID),
            ("files name", _set(("files", "hop_plants"), "x.jsonl"), FIELD_INVALID),
            ("mill not object", _set(("mills", 0), []), FIELD_INVALID),
            ("mill source missing", _drop(("mills", 0, "source")), FIELD_MISSING),
            ("mill shape type", _set(("mills", 0, "shape"), 5), FIELD_INVALID),
            ("mill base bool", _set(("mills", 0, "base_round"), True), FIELD_INVALID),
            ("mill id", _set(("mills", 0, "mill_id"), "bad"), FIELD_INVALID),
            ("mill base zero", _set(("mills", 0, "base_round"), 0), FIELD_INVALID),
            ("mill count zero", _set(("mills", 0, "plant_count"), 0), FIELD_INVALID),
            ("mill count wrong", _set(("mills", 0, "plant_count"), 2), FIELD_INVALID),
            ("mills mismatch", _drop(("mills", 2)), FIELD_INVALID),
        ]
        for label, edit, code in cases:
            with self.subTest(label):
                self.assertRefuses(code, self.build(meta_edit=edit))

    def test_plant_row_refusals(self):
        cases = [
            ("not object", _set((0,), []), PLANT_INVALID),
            ("mill_id blank", _set((0, "mill_id"), ""), PLANT_INVALID),
            ("mill_id form", _set((0, "mill_id"), "bad"), PLANT_INVALID),
            ("slug form", _set((0, "slug"), "-bad"), PLANT_INVALID),
            ("plant_id", _set((0, "plant_id"), "obs_r0002:other"), PLANT_INVALID),
            ("base_round", _set((0, "base_round"), 0), PLANT_INVALID),
            ("source missing", _drop((0, "source")), PLANT_MISSING),
            ("hop field missing", _drop((0, "lie")), PLANT_MISSING),
            ("spec field missing", _set((0, "shape"), "leftover_spec"), PLANT_MISSING),
            ("shape unknown", _set((0, "shape"), "weird"), PLANT_INVALID),
        ]
        for label, edit, code in cases:
            with self.subTest(label):
                self.assertRefuses(code, self.build(row_edit=edit))

    def test_duplicate_plant_id_is_refused(self):
        def edit(rows):
            rows.append(dict(rows[0]))
        self.assertRefuses(
            FINDING_PLANT_DUPLICATE_ID,
            self.build(meta_edit=_set(("plant_count",), 4), row_edit=edit),
        )

    def test_unreadable_files_are_refused(self):
        missing = self.build()
        (missing / HOP_FILENAME).unlink()
        self.assertRefuses(FINDING_CATALOG_FILE_MISSING, missing)
        broken = self.build()
        (broken / CATALOG_FILENAME).write_text("{", encoding="utf-8")
        self.assertRefuses(FIELD_INVALID, broken)
        listed = self.build()
        (listed / CATALOG_FILENAME).write_text("[]", encoding="utf-8")
        self.assertRefuses(FIELD_INVALID, listed)


class SpecIndexCatalog(CatalogTreeMixin, unittest.TestCase):
    def build_index(self, index_edit=None, meta_edit=None) -> Path:
        index = json.loads(json.dumps(SPEC_INDEX))
        if index_edit:
            index_edit(index)

        def edit(meta):
            _spec_index_meta(meta)
            if meta_edit:
                meta_edit(meta)
        return self.build(meta_edit=edit, rows={LEFTOVER_SPECS_FILENAME: [index]})

    def test_spec_index_replaces_spec_rows(self):
        loaded = catalog.load_catalog(self.build_index())
        self.assertEqual(loaded.leftover_spec_index["total"], 1)
        self.assertEqual(len(loaded.plants), 2)

    def test_spec_index_refusals(self):
        cases = [
            ("total", _set(("total",), 5), None, FIELD_INVALID),
            ("mills missing", _drop(("mills",)), None, FIELD_MISSING),
            ("mill id", _set(("mills", 0, "mill_id"), "obs_leftover8"), None, FIELD_INVALID),
            ("count", _set(("mills", 0, "count"), 2), None, FIELD_INVALID),
            ("hop count", None, _set(("mills", 0, "plant_count"), 2), FIELD_INVALID),
        ]
        for label, index_edit, meta_edit, code in cases:
            with self.subTest(label):
                self.assertRefuses(code, self.build_index(index_edit, meta_edit))


class RegistryRefusals(CatalogTreeMixin, unittest.TestCase):
    def with_registry(self, text: str) -> Path:
        directory = self.build()
        fake = self.root / "repo"
        (fake / "config").mkdir(parents=True, exist_ok=True)
        (fake / "config" / "FACTORY-REGISTRY.json").write_text(text, encoding="utf-8")
        self.enterContext(mock.patch.object(catalog, "repo_root", return_value=fake))
        return directory

    def test_registry_refusals(self):
        cases = [
            ("unparseable", "{"),
            ("not a list", '{"factories": {}}'),
            ("not registered", '{"factories": [{"path_id": "other"}, 3]}'),
        ]
        for label, text in cases:
            with self.subTest(label):
                self.assertRefuses(FINDING_FACTORY_NOT_REGISTERED, self.with_registry(text))


HOP_ROW = {key: f"v-{key}" for key in catalog.HOP_REQUIRED} | {"slug": "s1"}
SPEC_ROW = {key: f"v-{key}" for key in catalog.SPEC_REQUIRED} | {"ok_slug": "k1"}


def extract(text: str, mill_id: str = "obs_r0001", **kwargs) -> tuple:
    return catalog.plants_from_source(text, mill_id=mill_id, source="src.py", **kwargs)


def r401_source(kind: str, count: int = 24, prelude: str = "") -> str:
    args = dict.fromkeys(catalog.R401_ARG_NAMES, "x")
    args.update(kind=kind, svc="ab-svc", lsvc="cd-svc", false_yq="a.b", fail_val="9")
    values = list(args.values())[:count]
    return f"{prelude}PAIRS = [P({', '.join(repr(v) for v in values)})]\n"


class SourceExtraction(unittest.TestCase):
    def assertSourceRefuses(self, code, text, **kwargs):
        with self.assertRaises(ObsRefusal) as caught:
            extract(text, **kwargs)
        self.assertEqual(caught.exception.code, code, caught.exception.message)

    def test_literal_containers_and_assignment_forms(self):
        row = HOP_ROW | {"extra": [1, (2, 3), {4}, -5]}
        text = f"import os\nCATALOG_FIRST = 7\nOTHER = 1\na, b = 1, 2\nX: int\nPAIRS: list = [{row!r}]\n"
        (out,) = extract(text)
        self.assertEqual(out["extra"], [1, (2, 3), {4}, -5])
        self.assertEqual((out["base_round"], out["shape"]), (7, "hop"))

    def test_r401_positional_kinds_expand(self):
        for kind, (ns, _deploy) in catalog.DEFAULT_KIND_NS.items():
            with self.subTest(kind):
                (row,) = extract(r401_source(kind))
                self.assertEqual((row["ns"], row["kind"]), (ns, kind))
                self.assertEqual(row["false_obs"], "b healthy  # not the lie")
        prelude = "KIND_NS = {'zz': ('zz', 'dep')}\n"
        (row,) = extract(r401_source("zz", prelude=prelude))
        self.assertEqual((row["deploy"], row["exec_path"]), ("dep", "/api/v2/alerts"))

    def test_spec_literal_names_and_tuple_rows(self):
        spec = SPEC_ROW | {"slug": "ignored"}
        for number in (14, 15, 16):
            with self.subTest(number):
                (row,) = extract(f"L{number} = [{spec!r}]\n", mill_id=f"obs_leftover{number}")
                self.assertEqual((row["slug"], row["family"]), ("k1", f"leftover{number}"))
        values = tuple(SPEC_ROW[key] for key in catalog.SPEC_TUPLE_KEYS)
        (row,) = extract(f"SPECS = [{values!r}]\n", mill_id="obs_leftover9")
        self.assertEqual(row["plant_id"], "obs_leftover9:k1")

    def test_source_refusals(self):
        spec_missing = {k: v for k, v in SPEC_ROW.items() if k != "noun"}
        cases = [
            ("syntax", "PAIRS = [\n", {}, NOT_PARSEABLE),
            ("name element", "PAIRS = [other]\n", {}, NOT_PARSEABLE),
            ("mixed P call", "PAIRS = [P('a', kind='b')]\n", {}, NOT_PARSEABLE),
            ("no literal", "OTHER = []\n", {}, NOT_PARSEABLE),
            ("empty", "PAIRS = []\n", {}, NOT_PARSEABLE),
            ("not a list", "PAIRS = 3\n", {}, NOT_PARSEABLE),
            ("dict unpack", "PAIRS = [{**{}}]\n", {}, NOT_PARSEABLE),
            ("mill id", f"PAIRS = [{HOP_ROW!r}]\n", {"mill_id": "obs_x"}, PLANT_INVALID),
            ("base zero", f"PAIRS = [{HOP_ROW!r}]\n", {"base_round": 0}, PLANT_INVALID),
            ("hop tuple", "PAIRS = [(1, 2)]\n", {}, NOT_PARSEABLE),
            ("hop missing", "PAIRS = [{'slug': 's'}]\n", {}, PLANT_MISSING),
            ("hop slug", f"PAIRS = [{HOP_ROW | {'slug': '-x'}!r}]\n", {}, PLANT_INVALID),
            ("p kind blank", "PAIRS = [P(kind='', svc='s')]\n", {}, NOT_PARSEABLE),
            ("r401 arity", r401_source("tempo", count=3), {}, NOT_PARSEABLE),
            ("r401 kind", r401_source("nope"), {}, NOT_PARSEABLE),
        ]
        spec_cases = [
            ("spec tuple", "SPECS = [(1, 2)]\n", NOT_PARSEABLE),
            ("spec missing", f"SPECS = [{spec_missing!r}]\n", PLANT_MISSING),
            ("spec slug", f"SPECS = [{SPEC_ROW | {'ok_slug': '-x'}!r}]\n", PLANT_INVALID),
        ]
        cases += [(lbl, txt, {"mill_id": "obs_leftover9"}, code) for lbl, txt, code in spec_cases]
        for label, text, kwargs, code in cases:
            with self.subTest(label):
                self.assertSourceRefuses(code, text, **kwargs)


if __name__ == "__main__":
    unittest.main()
