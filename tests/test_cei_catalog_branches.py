"""Branch coverage for the CEI catalog loader and AST extractor refusals."""

from __future__ import annotations

import copy
import functools
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "tests" / "fixtures" / "cei"
COMMITTED = REPO / "config" / "cei"

sys.path.insert(0, str(REPO / "pipelines"))

from cei import _contract as contract
from cei import catalog

CeiRefusal = contract.CeiRefusal
CAT_INVALID = contract.FINDING_CATALOG_FIELD_INVALID
CAT_MISSING = contract.FINDING_CATALOG_FIELD_MISSING
FILE_MISSING = contract.FINDING_CATALOG_FILE_MISSING
NOT_REGISTERED = contract.FINDING_FACTORY_NOT_REGISTERED
DUPLICATE = contract.FINDING_PLANT_DUPLICATE_ID
PLANT_INVALID = contract.FINDING_PLANT_FIELD_INVALID
PLANT_MISSING = contract.FINDING_PLANT_FIELD_MISSING
NOT_PARSEABLE = contract.FINDING_SOURCE_NOT_PARSEABLE
LEFTOVER3_SHAPE = contract.LEFTOVER3_SHAPE

FIXTURE_META = json.loads((FIXTURE / "CATALOG.json").read_text(encoding="utf-8"))
OK_BAD_ROW = json.loads((FIXTURE / "plants.jsonl").read_text(encoding="utf-8"))


def _first_leftover3_row() -> dict:
    for line in (COMMITTED / "plants.jsonl").read_text(encoding="utf-8").splitlines():
        if f'"shape":"{LEFTOVER3_SHAPE}"' in line:
            return json.loads(line)
    raise AssertionError("the committed CEI catalog has no leftover3 plant")


LEFTOVER3_ROW = _first_leftover3_row()


def encode_rows(rows) -> bytes:
    return "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows).encode("utf-8")


def meta_for(rows, payload: bytes, mills_from=None) -> dict:
    meta = copy.deepcopy(FIXTURE_META)
    counts: dict[tuple[str, int], int] = {}
    for row in mills_from or rows:
        key = (row["mill_id"], row["base_round"])
        counts[key] = counts.get(key, 0) + 1
    meta["mills"] = [
        {"mill_id": mill, "base_round": base, "plant_count": n, "source": "fixture"}
        for (mill, base), n in counts.items()
    ]
    meta["plant_count"] = len(rows)
    meta["plants_sha256"] = hashlib.sha256(payload).hexdigest()
    return meta


def mutated(row, path, value):
    """Copy ``row`` and set (or delete, for ``...``) the dotted ``path``."""

    row = copy.deepcopy(row)
    *parents, leaf = path.split(".")
    target = row
    for key in parents:
        target = target[key]
    if value is ...:
        del target[leaf]
    else:
        target[leaf] = value
    return row


class CatalogDirMixin:
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.count = 0

    def write(self, rows, meta_edit=None, **options):
        self.count += 1
        dest = self.root / f"c{self.count}"
        dest.mkdir()
        payload = options.get("payload") or encode_rows(rows)
        meta = meta_for(rows, payload, options.get("mills_from"))
        if meta_edit is not None:
            meta = meta_edit(meta)
        (dest / "CATALOG.json").write_text(json.dumps(meta), encoding="utf-8")
        (dest / "plants.jsonl").write_bytes(payload)
        return dest

    def assertRefused(self, code, func, *args):
        with self.assertRaises(CeiRefusal) as caught:
            func(*args)
        self.assertEqual(caught.exception.code, code)
        return caught.exception


def setter(key, value):
    def edit(meta):
        meta[key] = value
        return meta

    return edit


def mill_setter(key, value):
    def edit(meta):
        meta["mills"][0][key] = value
        return meta

    return edit


class CatalogMetaRefusals(CatalogDirMixin, unittest.TestCase):
    def test_meta_field_refusals(self):
        cases = (
            ("not-object", lambda meta: [meta], CAT_INVALID),
            ("missing", lambda meta: {k: v for k, v in meta.items() if k != "format"}, CAT_MISSING),
            ("bool-id", setter("catalog_id", True), CAT_INVALID),
            ("format", setter("format", "cei-catalog/2"), CAT_INVALID),
            ("factory", setter("factory", "other-factory"), CAT_INVALID),
            ("prefix", setter("mill_prefix", "hop"), CAT_INVALID),
            ("kind", setter("record_kind", "preference"), CAT_INVALID),
            ("quota", setter("quota_per_round", 3), CAT_INVALID),
            ("plant-count", setter("plant_count", 2), CAT_INVALID),
            ("mill-not-object", setter("mills", ["cei_r0001"]), CAT_INVALID),
            ("mill-id", mill_setter("mill_id", "hop_r1"), CAT_INVALID),
            ("mill-base", mill_setter("base_round", 0), CAT_INVALID),
            ("mill-count", mill_setter("plant_count", 0), CAT_INVALID),
            ("mill-count-drift", mill_setter("plant_count", 2), CAT_INVALID),
            ("mill-base-drift", mill_setter("base_round", 2), CAT_INVALID),
            ("mill-set", mill_setter("mill_id", "cei_r0002"), CAT_INVALID),
        )
        for name, edit, code in cases:
            with self.subTest(name):
                self.assertRefused(code, catalog.load_catalog, self.write([OK_BAD_ROW], edit))

    def test_unreadable_meta_and_plants_files(self):
        dest = self.write([OK_BAD_ROW])
        (dest / "plants.jsonl").unlink()
        self.assertRefused(FILE_MISSING, catalog.load_catalog, dest)
        (dest / "CATALOG.json").write_text("{'not': strict}", encoding="utf-8")
        self.assertRefused(CAT_INVALID, catalog.load_catalog, dest)

    def test_jsonl_framing_refusals(self):
        line = json.dumps(OK_BAD_ROW, sort_keys=True)
        cases = (
            ("no-final-lf", line.encode()),
            ("blank-line", (line + "\n\n").encode()),
            ("not-strict", b"{'a': 1}\n"),
        )
        for name, payload in cases:
            with self.subTest(name):
                dest = self.write([OK_BAD_ROW], payload=payload)
                self.assertRefused(CAT_INVALID, catalog.load_catalog, dest)

    def test_read_jsonl_refuses_a_missing_file(self):
        self.assertRefused(FILE_MISSING, catalog._read_jsonl, self.root / "absent.jsonl")


class RegistryRefusals(CatalogDirMixin, unittest.TestCase):
    def test_registry_must_be_readable_and_list_the_factory(self):
        cases = (
            ("unreadable", None),
            ("not-json", "{nope"),
            ("no-factories", json.dumps({"factories": {}})),
            ("unregistered", json.dumps({"factories": [{"path_id": "elsewhere"}, 3]})),
        )
        dest = self.write([OK_BAD_ROW])
        for name, text in cases:
            with self.subTest(name), tempfile.TemporaryDirectory() as fake:
                if text is not None:
                    (Path(fake) / "config").mkdir()
                    (Path(fake) / "config" / "FACTORY-REGISTRY.json").write_text(text)
                with mock.patch.object(catalog, "repo_root", return_value=Path(fake)):
                    self.assertEqual(catalog.default_catalog_dir(), Path(fake) / "config" / "cei")
                    self.assertRefused(NOT_REGISTERED, catalog.load_catalog, dest)

    def test_catalog_check_reports_an_empty_catalog(self):
        empty = catalog.load_catalog(FIXTURE).__class__(
            "x", FIXTURE, "f", "0", plants=(), mills=(), meta={}
        )
        with mock.patch.object(catalog, "load_catalog", return_value=empty):
            self.assertEqual(catalog.catalog_check(FIXTURE)[0]["code"], CAT_INVALID)
        self.assertEqual(catalog.catalog_check(FIXTURE), [])


class PlantRowRefusals(CatalogDirMixin, unittest.TestCase):
    def test_ok_bad_row_refusals(self):
        cases = (
            ("mill-id", mutated(OK_BAD_ROW, "mill_id", "cei_x"), PLANT_INVALID),
            ("shape", mutated(OK_BAD_ROW, "shape", "triple"), PLANT_INVALID),
            ("plant-id", mutated(OK_BAD_ROW, "plant_id", "cei_r0001:other"), PLANT_INVALID),
            ("base-round", mutated(OK_BAD_ROW, "base_round", True), PLANT_INVALID),
            ("index", mutated(OK_BAD_ROW, "index", -1), PLANT_INVALID),
            ("side-object", mutated(OK_BAD_ROW, "ok", []), PLANT_INVALID),
            ("side-missing", mutated(OK_BAD_ROW, "ok.goal", ...), PLANT_MISSING),
            ("side-extra", mutated(OK_BAD_ROW, "ok.thought", "x"), PLANT_INVALID),
            ("coverage", mutated(OK_BAD_ROW, "bad.coverage", 0), PLANT_INVALID),
            ("payload-cr", mutated(OK_BAD_ROW, "ok.goal", "a\r\nb"), PLANT_INVALID),
            ("slug", mutated(OK_BAD_ROW, "bad.slug", "-handoff"), PLANT_INVALID),
            ("banned", mutated(OK_BAD_ROW, "bad.domain", "prism-handoff"), PLANT_INVALID),
            ("first-old", mutated(OK_BAD_ROW, "bad.first_old", "absent"), PLANT_INVALID),
        )
        self.assert_row_refusals(cases, OK_BAD_ROW)

    def test_leftover3_row_refusals(self):
        cases = (
            ("side-object", mutated(LEFTOVER3_ROW, "bad", "x"), PLANT_INVALID),
            ("side-missing", mutated(LEFTOVER3_ROW, "ok.chg", ...), PLANT_MISSING),
            ("side-extra", mutated(LEFTOVER3_ROW, "ok.ticket", "T-1"), PLANT_INVALID),
            ("slug", mutated(LEFTOVER3_ROW, "bad.slug", "bad slug"), PLANT_INVALID),
            ("banned", mutated(LEFTOVER3_ROW, "bad.slug", "lo-lock-vs-drop"), PLANT_INVALID),
            ("wrong", mutated(LEFTOVER3_ROW, "ok.wrong", "os.unlink(p)"), PLANT_INVALID),
        )
        self.assert_row_refusals(cases, LEFTOVER3_ROW)

    def assert_row_refusals(self, cases, base):
        for name, row, code in cases:
            with self.subTest(name):
                dest = self.write([row], mills_from=[base])
                self.assertRefused(code, catalog.load_catalog, dest)
        dest = self.write([[]], payload=b"[]\n", mills_from=[base])
        self.assertRefused(PLANT_INVALID, catalog.load_catalog, dest)

    def test_duplicate_plant_id_and_slug_are_refused(self):
        twin = mutated(OK_BAD_ROW, "index", 1)
        self.assertRefused(DUPLICATE, catalog.load_catalog, self.write([OK_BAD_ROW, twin]))
        other = mutated(OK_BAD_ROW, "ok.slug", "csv-other")
        other["plant_id"] = "cei_r0001:csv-other"
        self.assertRefused(DUPLICATE, catalog.load_catalog, self.write([OK_BAD_ROW, other]))

    def test_mixed_catalog_round_trips_sides_and_mill_lookup(self):
        loaded = catalog.load_catalog(self.write([OK_BAD_ROW, LEFTOVER3_ROW]))
        ok_bad, left = loaded.plants
        self.assertEqual(ok_bad.bad.as_mapping()["ticket_why"], OK_BAD_ROW["bad"]["ticket_why"])
        self.assertNotIn("ticket", ok_bad.ok.as_mapping())
        self.assertEqual(left.ok.as_mapping(), LEFTOVER3_ROW["ok"])
        self.assertEqual(left.bad.as_mapping(), LEFTOVER3_ROW["bad"])
        self.assertEqual(loaded.mill_plants("cei_r48"), (left,))
        self.assertRefused(contract.FINDING_MILL_NOT_FOUND, loaded.mill_plants, "cei_r9")


def ok_call(slug="tiny-a", mod="moda", extra=""):
    return (
        f'_ok("{slug}", "goal", "{mod}", "stack", "https://x.test", "return 1",'
        f' "    return 2", "    return 3"{extra})'
    )


def bad_call(slug="tiny-b", mod="modb", ticket="T-1"):
    return (
        f'_bad("{slug}", "goal", "{mod}", "stack", "https://x.test", "return 1",'
        f' "    return 2", "{ticket}")'
    )


def s_args(slug, mod, ticket=None):
    args = {name: f"{name} text" for name in contract.S_OK_ARG_NAMES}
    args.update(slug=slug, mod=mod)
    if ticket is not None:
        args["ticket"] = ticket
    return args


def s_call(slug, mod, ticket=None):
    values = list(s_args(slug, mod).values()) + ([ticket] if ticket else [])
    return "S(" + ", ".join(repr(v) for v in values) + ")"


def s_pair(slug, mod, ticket):
    return s_call(slug, mod), s_call(slug + "-b", mod + "b", ticket)


def pairs(*items, prelude=""):
    return prelude + "PAIRS = [" + ", ".join(f"({a}, {b})" for a, b in items) + "]\n"


OK_BAD = (ok_call(), bad_call())
S_PAIR = (s_call("s-a", "sa"), s_call("s-b", "sb", "T-9"))
DICT_PAIR = (repr(s_args("d-a", "da")), repr(s_args("d-b", "db", "T-8")))


def extract(text, mill_id="cei_r0007", source="tiny.py"):
    return catalog.plants_from_source(text, mill_id=mill_id, source=source)


class SourceExtraction(CatalogDirMixin, unittest.TestCase):
    def test_source_refusals(self):
        cases = (
            ("syntax", "PAIRS = [", NOT_PARSEABLE),
            ("no-pairs", "import os\na = b = 1\nX: int\n", NOT_PARSEABLE),
            ("negative-base", pairs(OK_BAD, prelude="CATALOG_FIRST = -1\n"), PLANT_INVALID),
            ("list-base", pairs(OK_BAD, prelude="CATALOG_FIRST = [1, (2,)]\n"), PLANT_INVALID),
            ("dict-base", pairs(OK_BAD, prelude="CATALOG_FIRST = {1: 2}\n"), PLANT_INVALID),
            ("unpack-base", pairs(OK_BAD, prelude="CATALOG_FIRST = {**{}}\n"), NOT_PARSEABLE),
            ("not-tuple", f"PAIRS = [({OK_BAD[0]}, {OK_BAD[1]}), 2]\n", NOT_PARSEABLE),
            ("ok-not-call", pairs(("1", "2")), NOT_PARSEABLE),
            ("bad-not-call", pairs((ok_call(), "2")), NOT_PARSEABLE),
            ("swapped", pairs((bad_call(), ok_call())), NOT_PARSEABLE),
            ("extra-positional", pairs((ok_call(extra=", 9"), bad_call())), NOT_PARSEABLE),
            ("star-kwargs", pairs((ok_call(extra=", **kw"), bad_call())), NOT_PARSEABLE),
            ("ok-missing", pairs(("_ok('a')", bad_call())), NOT_PARSEABLE),
            ("bad-missing", pairs((ok_call(), "_bad('b')")), NOT_PARSEABLE),
            ("src-body", pairs((ok_call(extra=", src_body='x'"), bad_call())), NOT_PARSEABLE),
            ("banned-slug", pairs((ok_call(slug="a-vs-drop"), bad_call())), PLANT_INVALID),
            ("dup-mod", pairs((ok_call(mod="m"), bad_call(mod="m"))), PLANT_INVALID),
        )
        self.assert_source_refusals(cases)

    def test_duplicate_refusals_across_pairs(self):
        second = (ok_call("tiny-c", "modc"), bad_call("tiny-d", "modd"))
        dict_bad = DICT_PAIR[1].replace("d-b", "x")
        cases = (
            ("slug", pairs(OK_BAD, (ok_call(), bad_call("x", "y", "T-2"))), DUPLICATE),
            ("ticket", pairs(OK_BAD, second), PLANT_INVALID),
            ("s-slug", pairs(S_PAIR, (S_PAIR[0], s_call("s-c", "sc", "T-2"))), DUPLICATE),
            ("s-mod", pairs(S_PAIR, s_pair("s-c", "sa", "T-2")), PLANT_INVALID),
            ("s-ticket", pairs(S_PAIR, s_pair("s-c", "sc", "T-9")), PLANT_INVALID),
            ("s-not-pair", pairs(S_PAIR, OK_BAD), NOT_PARSEABLE),
            ("s-banned", pairs((s_call("lo-lock-vs-drop", "x"), S_PAIR[1])), PLANT_INVALID),
            ("d-slug", pairs(DICT_PAIR, (DICT_PAIR[0], dict_bad)), DUPLICATE),
            ("d-mod", pairs(DICT_PAIR, self.dict_pair("d-c", "da", "T-2")), PLANT_INVALID),
            ("d-ticket", pairs(DICT_PAIR, self.dict_pair("d-c", "dc", "T-8")), PLANT_INVALID),
            ("d-not-pair", pairs(DICT_PAIR, S_PAIR), NOT_PARSEABLE),
        )
        self.assert_source_refusals(cases)

    @staticmethod
    def dict_pair(slug, mod, ticket):
        return repr(s_args(slug, mod)), repr(s_args(slug + "-b", mod + "b", ticket))

    def assert_source_refusals(self, cases):
        for name, text, code in cases:
            with self.subTest(name):
                self.assertRefused(code, extract, text)

    def test_mill_id_and_source_gates(self):
        self.assertRefused(PLANT_INVALID, extract, pairs(OK_BAD), "hop_r1")
        foreign = "from cei_r42_mill import S\n" + pairs(S_PAIR)
        self.assertRefused(contract.FINDING_LEFTOVER3_EXEC, extract, foreign)
        rows = extract(foreign, mill_id="cei_r42", source="experiments/cei_r42_mill.py")
        self.assertEqual(rows[0]["base_round"], 42)

    def test_s_pairs_keyword_args_and_annotated_pairs(self):
        text = "PAIRS: list = [(" + ok_call() + ", " + bad_call().replace('"T-1"', 'ticket="T-1"')
        rows = extract(text + ")]\n", mill_id="cei_r12")
        self.assertEqual((rows[0]["base_round"], rows[0]["bad"]["ticket"]), (12, "T-1"))
        s_rows = extract(pairs(S_PAIR), mill_id="cei_r48")
        self.assertEqual(s_rows[0]["shape"], LEFTOVER3_SHAPE)
        self.assertEqual(s_rows[0]["ok"]["wrong"], contract.LEFTOVER3_WRONG)

    def test_dict_leftover3_pairs_skip_banned_slugs(self):
        banned = (repr(s_args("ods-content-vs-drop", "od")), repr(s_args("z", "z", "T-0")))
        rows = extract(pairs(banned, DICT_PAIR), mill_id="cei_r65")
        self.assertEqual([(r["index"], r["plant_id"]) for r in rows], [(0, "cei_r65:d-a")])
        self.assertRefused(NOT_PARSEABLE, extract, pairs(banned))

    def test_expand_leftover3_ticket_contract(self):
        cases = (
            ({"slug": "x"}, False),
            (s_args("x", "y", ticket=1), True),
            (s_args("x", "y", ticket="T-1"), False),
        )
        for args, required in cases:
            with self.subTest(required=required, keys=len(args)):
                expand = functools.partial(catalog.expand_leftover3, ticket_required=required)
                self.assertRefused(NOT_PARSEABLE, expand, args)


if __name__ == "__main__":
    unittest.main()
