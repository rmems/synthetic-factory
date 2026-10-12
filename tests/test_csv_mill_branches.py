"""Fail-closed branches of the CSV mill catalog, extractor, generator and CLI.

Catalog cases copy the committed catalog into a temporary directory, apply one
edit, re-pin ``plants_sha256`` to the edited bytes, and pin the exact coded
refusal the loader raises today. Extraction cases build small literal sources from
the committed first pair; nothing is executed and nothing is written under
``outputs/raw/``.
"""

import copy
import fcntl
import json
import tempfile
import unittest
from functools import partial
from io import StringIO
from pathlib import Path
from unittest import mock

from pipelines.csv_mill import catalog, catalog_validation, cli, generate, generate_io
from pipelines.csv_mill._contract import (
    FACTORY,
    PAIR_KEYS,
    RECORD_PREFIX,
    CsvRefusal,
    refuse_vendor_paths,
)

COMMITTED = Path(__file__).resolve().parents[1] / "config" / "csv"
META = json.loads((COMMITTED / "CATALOG.json").read_text(encoding="utf-8"))
ROWS = tuple(
    json.loads(line)
    for line in (COMMITTED / "plants.jsonl").read_text(encoding="utf-8").splitlines()
)
FIRST_PLANT = ROWS[0]["plant_id"]
PAIR = {key: ROWS[0][key] for key in PAIR_KEYS}
INVALID = "CATALOG_FIELD_INVALID"
PLANT_INVALID = "PLANT_FIELD_INVALID"
DUPLICATE = "PLANT_DUPLICATE"
UNPARSEABLE = "SOURCE_NOT_PARSEABLE"
SOURCE = "literal.py"
MILL = "csv_r114"
SECOND_MILL = "csv_r115"


def _payload(rows):
    return "".join(json.dumps(row, separators=(",", ":")) + "\n" for row in rows).encode()


def _write_catalog(dest, meta, payload):
    dest.mkdir()
    pinned = {**meta, "plants_sha256": catalog.sha256_bytes(payload)}
    (dest / "CATALOG.json").write_text(json.dumps(pinned), encoding="utf-8")
    (dest / "plants.jsonl").write_bytes(payload)


def _edited_catalog(dest, edit):
    meta, rows = copy.deepcopy(META), copy.deepcopy(list(ROWS))
    edit(meta, rows)
    _write_catalog(dest, meta, _payload(rows))


def _meta_value(key, value):
    def edit(meta, _rows):
        meta[key] = value

    return edit


def _drop_meta(key):
    def edit(meta, _rows):
        del meta[key]

    return edit


def _mill_value(key, value):
    def edit(meta, _rows):
        meta["mills"][0][key] = value

    return edit


def _plant_value(key, value):
    def edit(_meta, rows):
        rows[0][key] = value

    return edit


def _renamed_mill(meta, _rows):
    meta["mills"][0].update(mill_id=SECOND_MILL, base_round=115)


def _copied_plant(_meta, rows):
    rows[1] = {**rows[0], "source": "experiments/copy.py"}


def _two_overlapping_mills(meta, rows):
    for offset, row in enumerate(rows[8:]):
        row.update(mill_id=SECOND_MILL, base_round=115, index=offset,
                   plant_id=f"{SECOND_MILL}:{row['slug']}")
    second = {**meta["mills"][0], "mill_id": SECOND_MILL, "base_round": 115, "plant_count": 8}
    meta["mills"] = [{**meta["mills"][0], "plant_count": 8}, second]


# (label, edit(meta, rows), refusal code, exact refusal prose)
CATALOG_CASES = (
    ("catalog id missing", _drop_meta("catalog_id"), "CATALOG_FIELD_MISSING",
     "CATALOG.json.catalog_id is missing"),
    ("quota pin", _meta_value("quota_per_round", 3), INVALID,
     "CATALOG.json.quota_per_round must be 2"),
    ("declared plant count", _meta_value("plant_count", 15), INVALID,
     "CATALOG.json.plant_count is 15, file has 16"),
    ("plant mill id syntax", _plant_value("mill_id", "csv_x"), PLANT_INVALID,
     "plants.jsonl:1.mill_id is not csv_rNNN"),
    ("plant id binding", _plant_value("plant_id", "csv_r114:other"), PLANT_INVALID,
     f"plants.jsonl:1.plant_id must be {FIRST_PLANT!r}"),
    ("mill id syntax", _mill_value("mill_id", "csv-114"), INVALID,
     "CATALOG.json.mills[0].mill_id is not csv_rNNN"),
    ("mill base round", _mill_value("base_round", 0), INVALID,
     "CATALOG.json.mills[0].base_round must be a positive int"),
    ("mill plant count floor", _mill_value("plant_count", 0), INVALID,
     "CATALOG.json.mills[0].plant_count must be a positive int"),
    ("mill set", _renamed_mill, INVALID, "catalog mills do not match plant mill_id values"),
    ("mill plant count", _mill_value("plant_count", 15), INVALID,
     "csv_r114 plant_count 15 != 16"),
    ("plant base round", _plant_value("base_round", 115), INVALID,
     f"{FIRST_PLANT} base_round != mill base_round"),
    ("duplicate plant id", _copied_plant, DUPLICATE, f"duplicate plant_id {FIRST_PLANT}"),
    ("overlapping mills", _two_overlapping_mills, DUPLICATE, "overlapping catalog round 115"),
)

# (label, plants.jsonl bytes, exact refusal prose); every code is CATALOG_FIELD_INVALID
FRAMING_CASES = (
    ("empty plants", b"", "plants.jsonl must be LF-framed jsonl"),
    ("CRLF plants", _payload(ROWS).replace(b"\n", b"\r\n"),
     "plants.jsonl: LF-only JSONL cannot contain carriage returns"),
)


def _source(pair=None, *, prefix=RECORD_PREFIX, before=""):
    args = ", ".join(f"{key}={value!r}" for key, value in (pair or PAIR).items())
    return f"FAC = {FACTORY!r}\nPREFIX = {prefix!r}\n{before}PAIRS = [dict({args})]\n"


# (label, source text, mill_id, refusal code, exact refusal prose)
EXTRACT_CASES = (
    ("non-constant value", _source().replace(f"mod={PAIR['mod']!r}", "mod=unbound"), MILL,
     UNPARSEABLE, "plant source is not a constant (Name)"),
    ("keyword unpacking",
     _source(before="BASE = dict(slug='x')\n").split("PAIRS = ")[0] + "PAIRS = [dict(**BASE)]\n",
     MILL, UNPARSEABLE, "literal catalog uses keyword unpacking"),
    ("prefix pin", _source(prefix="other"), MILL, UNPARSEABLE,
     f"{SOURCE} PREFIX must be {RECORD_PREFIX}"),
    ("empty pairs", _source().split("PAIRS = ")[0] + "PAIRS = []\n", MILL, UNPARSEABLE,
     f"{SOURCE} has no PAIRS list"),
    ("mill id syntax", _source(), "csv_x", PLANT_INVALID, "mill_id 'csv_x' is not csv_rNNN"),
    ("missing pair key", _source({k: v for k, v in PAIR.items() if k != "mod"}), MILL,
     UNPARSEABLE, f"{SOURCE} PAIRS[0] missing mod"),
    ("extra pair key", _source({**PAIR, "zzz": "extra"}), MILL, UNPARSEABLE,
     f"{SOURCE} PAIRS[0] has extra zzz"),
    ("subscript annotation", _source(before="X: list[int] = [1]\n"), MILL, UNPARSEABLE,
     "unproven definition-time annotation in literal catalog"),
)


def _request(out_dir, **selectors):
    return generate.GenerateRequest(catalog_dir=COMMITTED, out_dir=out_dir, **selectors)


# (label, request selectors, refusal code, exact refusal prose)
GENERATE_CASES = (
    ("round floor", {"plant_id": FIRST_PLANT, "round": 0}, "ROUND_INVALID",
     "round must be a positive integer"),
    ("round ceiling", {"plant_id": FIRST_PLANT, "round": 10**4096}, "ROUND_INVALID",
     "round exceeds the exact-JSON integer domain"),
    ("round without plant", {"mill_id": MILL, "round": 120}, "USAGE",
     "round applies only with plant_id"),
    ("unknown mill", {"mill_id": "csv_r999"}, "MILL_NOT_FOUND",
     "no mill 'csv_r999' in the catalog"),
)


_REAL_FLOCK = fcntl.flock


def _flock_unlock_fails(descriptor, operation):
    if operation == fcntl.LOCK_UN:
        raise OSError("injected unlock failure")
    return _REAL_FLOCK(descriptor, operation)


class RefusalAssertions:
    """Mixin: one call per ``assertRaises`` block, then the exact code and prose."""

    def assert_refusal(self, call, code, message):
        with self.assertRaises(CsvRefusal) as caught:
            call()
        refusal = caught.exception
        self.assertEqual((refusal.code, str(refusal)), (code, f"{code}: {message}"))


class CsvCatalogRefusals(RefusalAssertions, unittest.TestCase):
    def test_each_catalog_edit_raises_its_exact_refusal(self):
        for label, edit, code, message in CATALOG_CASES:
            with self.subTest(label), tempfile.TemporaryDirectory() as temp:
                dest = Path(temp) / "catalog"
                _edited_catalog(dest, edit)
                self.assert_refusal(partial(catalog.load_catalog, dest), code, message)

    def test_plants_framing_is_refused_after_authentication(self):
        for label, payload, message in FRAMING_CASES:
            with self.subTest(label), tempfile.TemporaryDirectory() as temp:
                dest = Path(temp) / "catalog"
                _write_catalog(dest, META, payload)
                self.assert_refusal(partial(catalog.load_catalog, dest), INVALID, message)

    def test_unreadable_registry_is_a_factory_refusal(self):
        with (
            tempfile.TemporaryDirectory() as temp,
            mock.patch.object(catalog_validation, "repo_root", return_value=Path(temp)),
            self.assertRaises(CsvRefusal) as caught,
        ):
            catalog.load_catalog(COMMITTED)
        self.assertEqual(caught.exception.code, "FACTORY_NOT_REGISTERED")
        self.assertIn("factory registry is unreadable: ", str(caught.exception))


class CsvExtractRefusals(RefusalAssertions, unittest.TestCase):
    def test_each_source_raises_its_exact_refusal(self):
        for label, text, mill_id, code, message in EXTRACT_CASES:
            with self.subTest(label):
                call = partial(catalog.plants_from_source, text, mill_id=mill_id, source=SOURCE)
                self.assert_refusal(call, code, message)

    def test_annotated_pins_and_inert_statements_extract(self):
        text = _source(before="pass\nNOTE: str = 'inert'\n").replace("PREFIX =", "PREFIX: str =")
        rows = catalog.plants_from_source(text, mill_id=MILL, source=SOURCE)
        self.assertEqual([row["plant_id"] for row in rows], [FIRST_PLANT])


class CsvGenerateRefusals(RefusalAssertions, unittest.TestCase):
    def test_each_request_is_refused_before_anything_is_written(self):
        for label, selectors, code, message in GENERATE_CASES:
            with self.subTest(label), tempfile.TemporaryDirectory() as temp:
                out_dir = Path(temp) / "run"
                request = _request(out_dir, **selectors)
                self.assert_refusal(partial(generate.run, request), code, message)
                self.assertFalse(out_dir.exists())


class CsvStagedWrites(RefusalAssertions, unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)

    def test_a_write_without_progress_is_refused_and_the_stage_removed(self):
        destination = self.root / "run"
        with mock.patch.object(generate_io.os, "write", return_value=0):
            self.assert_refusal(
                partial(generate_io.write_run_files, destination, {"RUN.json": "{}\n"}),
                "DESTINATION_INVALID", "staged file write made no progress",
            )
        self.assertEqual(list(self.root.iterdir()), [])

    def test_unlock_failures_do_not_undo_a_publication(self):
        destination = self.root / "run"
        with mock.patch.object(generate_io.fcntl, "flock", side_effect=_flock_unlock_fails):
            published = generate_io.write_run_files(destination, {"RUN.json": "{}\n"})
        self.assertEqual(published.resolve(), destination.resolve())
        self.assertEqual((destination / "RUN.json").read_text(encoding="utf-8"), "{}\n")


class CsvVendorPaths(RefusalAssertions, unittest.TestCase):
    def test_mill_and_loop_scripts_are_refused_and_other_paths_pass(self):
        for name in ("csv_MILL_r114.py", "hop-loop-r9.py"):
            with self.subTest(name):
                call = partial(refuse_vendor_paths, [Path("experiments") / name])
                self.assert_refusal(call, "VENDOR_PATH", f"refusing to vendor {name}")
        self.assertIsNone(refuse_vendor_paths(["notes.py", "mill.md", "loop.py"]))


class CsvCliPaths(unittest.TestCase):
    def test_catalog_check_text_report(self):
        stdout = StringIO()
        with mock.patch("sys.stdout", stdout):
            code = cli.run(["catalog-check", "--catalog", str(COMMITTED)])
        self.assertEqual(code, 0)
        self.assertEqual(stdout.getvalue(), "catalog-check ok: csv-lll-v1 16 plants / 1 mills\n")

    def test_text_refusals_go_to_stderr(self):
        stderr = StringIO()
        with tempfile.TemporaryDirectory() as temp, mock.patch("sys.stderr", stderr):
            code = cli.run(["generate", "--out", str(Path(temp) / "run"), "--plant", "missing"])
        self.assertEqual(code, 2)
        self.assertEqual(stderr.getvalue(), "PLANT_NOT_FOUND: no plant 'missing' in the catalog\n")

    def test_main_exits_with_the_run_status(self):
        argv = ["pipelines.csv_mill.cli", "catalog-check", "--json"]
        with (
            mock.patch("sys.argv", argv),
            mock.patch("sys.stdout", StringIO()),
            self.assertRaises(SystemExit) as caught,
        ):
            cli.main()
        self.assertEqual(caught.exception.code, 0)


if __name__ == "__main__":
    unittest.main()
