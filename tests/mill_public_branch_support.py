"""Shared helpers for the ``test_<pkg>_public_branches`` mill modules.

Every helper drives a mill package through its public surface only: a
mutated temp copy of a committed catalog handed to ``load_catalog``, small
in-memory sources handed to an extractor, or ``generate`` into a temp
destination. Nothing here writes under ``outputs/raw/`` or edits a
committed catalog.
"""

from __future__ import annotations

import ast
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"
if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

CATALOG_JSON = "CATALOG.json"
PLANTS_JSONL = "plants.jsonl"
ENCODING = "utf-8"
DELETE = object()

# CATALOG.json and plants.jsonl field names the sibling loaders read.
MILLS, MILL_ID, PLANT_ID, COUNT = "mills", "mill_id", "plant_id", "plant_count"
SOURCE, BASE, CATALOG_ID, FACTORY = "source", "base_round", "catalog_id", "factory"
ROW_IDENTITY = frozenset({PLANT_ID, MILL_ID, SOURCE, BASE})
FIELD_INVALID = "catalog_field_invalid"
MILL0 = "CATALOG.json.mills[0]"
FIRST_MILL = (MILLS, 0)


def refusal(error_type: type[BaseException], call, *args, **kwargs) -> tuple[str, str] | None:
    """``(code, message)`` of the coded refusal ``call`` raises, or ``None`` if it returns."""

    try:
        call(*args, **kwargs)
    except error_type as exc:
        return exc.code, exc.message
    return None


def error_text(error_type: type[BaseException], call, *args, **kwargs) -> str | None:
    """``str`` of the ``error_type`` that ``call`` raises, or ``None`` if it returns."""

    try:
        call(*args, **kwargs)
    except error_type as exc:
        return str(exc)
    return None


def temp_dir(case) -> Path:
    """A fresh temp directory that ``case`` removes on cleanup."""

    path = Path(tempfile.mkdtemp(prefix="mill-public-"))
    case.addCleanup(shutil.rmtree, path, True)
    return path


def sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def compact_jsonl(rows: list[Any]) -> bytes:
    """One compact, key-sorted JSON value per LF-terminated line."""

    lines = (json.dumps(row, separators=(",", ":"), sort_keys=True) for row in rows)
    return "".join(line + "\n" for line in lines).encode(ENCODING)


def mutated(document: Any, path: tuple[Any, ...], value: Any) -> Any:
    """Set (or, with ``DELETE``, remove) the item at ``path`` inside ``document``."""

    *parents, last = path
    target = document
    for key in parents:
        target = target[key]
    if value is DELETE:
        del target[last]
    else:
        target[last] = value
    return document


def first_row(committed: Path) -> dict[str, Any]:
    return json.loads((committed / PLANTS_JSONL).read_bytes().splitlines()[0])


class CatalogCopy:
    """A temp copy of selected files from a committed catalog directory."""

    def __init__(self, case, source: Path, names: tuple[str, ...]) -> None:
        self.directory = temp_dir(case) / "catalog"
        self.directory.mkdir()
        for name in names:
            shutil.copyfile(source / name, self.directory / name)

    def path(self, name: str) -> Path:
        return self.directory / name

    def read_json(self, name: str = CATALOG_JSON) -> Any:
        return json.loads(self.path(name).read_text(encoding=ENCODING))

    def write_json(self, document: Any, name: str = CATALOG_JSON) -> Path:
        text = json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        self.path(name).write_text(text, encoding=ENCODING)
        return self.path(name)

    def write_bytes(self, payload: bytes, name: str = PLANTS_JSONL) -> str:
        """Write ``payload`` to ``name`` and return its sha256 hex digest."""

        self.path(name).write_bytes(payload)
        return sha256_hex(payload)


def source_plant(committed: Path, **overrides: str) -> dict[str, str]:
    """A mill-source plant literal with every field the committed rows carry, as placeholders."""

    row = first_row(committed)
    return {key: f"{key}-value" for key in row if key not in ROW_IDENTITY} | overrides


def one_plant_copy(case, committed: Path, **changes: Any) -> CatalogCopy:
    """A pinned catalog copy holding only the first committed plant, with ``changes``."""

    copy = CatalogCopy(case, committed, (CATALOG_JSON,))
    row = first_row(committed) | changes
    document = copy.read_json()
    document["plants_sha256"] = copy.write_bytes(compact_jsonl([row]))
    document[COUNT] = 1
    mills = [mill for mill in document[MILLS] if mill[MILL_ID] == row[MILL_ID]]
    document[MILLS] = [mills[0] | {COUNT: 1}]
    copy.write_json(document)
    return copy


def generated_records(case, generate, catalog_dir: Path) -> list[dict[str, Any]]:
    """Run ``generate`` over every plant of ``catalog_dir`` and return its records."""

    out = temp_dir(case) / "out"
    generate.run(generate.GenerateRequest(catalog_dir, out, all_plants=True))
    text = (out / generate.RECORDS_FILENAME).read_text(encoding=ENCODING)
    return [json.loads(line) for line in text.splitlines()]


# (label, CATALOG.json path, new value, message) refused as ``<prefix>.catalog_field_invalid``.
# ``{format}`` and the other fields are filled from the committed CATALOG.json, which
# the loader accepts, so they equal the pins it compares against.
_META_CASES = (
    ("id bool", (CATALOG_ID,), True, "CATALOG.json.catalog_id has the wrong type"),
    ("id int", (CATALOG_ID,), 7, "CATALOG.json.catalog_id has the wrong type"),
    ("id padded", (CATALOG_ID,), " x",
     "CATALOG.json.catalog_id must be a non-empty stripped string"),
    ("format", ("format",), "other/1", "CATALOG.json.format must be {format}"),
    ("factory pin", (FACTORY,), "other-factory", "CATALOG.json.factory must be {factory}"),
    ("prefix", ("mill_prefix",), "zzz", "CATALOG.json.mill_prefix must be {mill_prefix}"),
    ("kind", ("record_kind",), "other", "CATALOG.json.record_kind must be {record_kind}"),
    ("quota", ("quota_per_round",), 3,
     "CATALOG.json.quota_per_round must be {quota_per_round}"),
    ("mills text", (MILLS,), "x", "CATALOG.json.mills has the wrong type"),
    ("mill row text", FIRST_MILL, "x", f"{MILL0} must be an object"),
    ("mill id", (*FIRST_MILL, MILL_ID), "x_r1", f"{MILL0}.mill_id is not {{mill_prefix}}_rNNN"),
    ("mill round", (*FIRST_MILL, BASE), 0, f"{MILL0}.base_round must be a positive int"),
    ("mill count", (*FIRST_MILL, COUNT), 0, f"{MILL0}.plant_count must be a positive int"),
    ("mill source", (*FIRST_MILL, SOURCE), "",
     f"{MILL0}.source must be a non-empty stripped string"),
)


class SiblingCatalogContract:
    """Mixin: ``load_catalog`` refusals shared by the flk, msd, rag and saf catalogs.

    A subclass also inherits ``unittest.TestCase`` and sets ``catalog`` (the
    package's catalog module), ``error_type``, ``prefix`` (``"flk"``...) and
    ``committed`` (the committed catalog directory). Expected messages are
    built from the committed ``CATALOG.json`` values.
    """

    catalog: Any = None
    error_type: type[BaseException] = Exception
    prefix = ""
    committed = REPO
    pins_unregistered_factory = False

    def code(self, suffix: str) -> str:
        return f"{self.prefix}.{suffix}"

    def copy(self) -> CatalogCopy:
        return CatalogCopy(self, self.committed, (CATALOG_JSON, PLANTS_JSONL))

    def load(self, copy: CatalogCopy) -> tuple[str, str] | None:
        return refusal(self.error_type, self.catalog.load_catalog, copy.directory)

    def meta_refusal(self, path: tuple[Any, ...], value: Any) -> tuple[str, str] | None:
        copy = self.copy()
        copy.write_json(mutated(copy.read_json(), path, value))
        return self.load(copy)

    def rows_refusal(self, payload: bytes, plant_count: int | None = None):
        """Load a copy whose plants file is ``payload``, re-pinned past the digest check."""

        copy = self.copy()
        document = copy.read_json()
        document["plants_sha256"] = copy.write_bytes(payload)
        if plant_count is not None:
            document[COUNT] = plant_count
        copy.write_json(document)
        return self.load(copy)

    def committed_meta(self) -> dict[str, Any]:
        return json.loads((self.committed / CATALOG_JSON).read_text(encoding=ENCODING))

    def committed_lines(self) -> list[bytes]:
        return (self.committed / PLANTS_JSONL).read_bytes().splitlines(keepends=True)

    def test_catalog_json_mutations_refuse_at_the_first_failing_field(self):
        pinned = self.committed_meta()
        for label, path, value, message in _META_CASES:
            with self.subTest(label):
                expected = (self.code(FIELD_INVALID), message.format(**pinned))
                self.assertEqual(self.meta_refusal(path, value), expected)

    def test_a_missing_catalog_id_is_a_missing_field(self):
        expected = (self.code("catalog_field_missing"), "CATALOG.json.catalog_id is missing")
        self.assertEqual(self.meta_refusal((CATALOG_ID,), DELETE), expected)

    def test_catalog_json_that_is_not_a_strict_object_is_refused(self):
        not_strict = "CATALOG.json is not strict JSON"
        for label, text, message in (
            ("duplicate key", '{"a": 1, "a": 2}\n', not_strict),
            ("nan", '{"a": NaN}\n', not_strict),
            ("list", "[]\n", "CATALOG.json must be an object"),
        ):
            with self.subTest(label):
                copy = self.copy()
                copy.path(CATALOG_JSON).write_text(text, encoding=ENCODING)
                self.assertEqual(self.load(copy), (self.code(FIELD_INVALID), message))

    def test_a_missing_plants_file_is_refused(self):
        copy = self.copy()
        copy.path(PLANTS_JSONL).unlink()
        expected = (self.code("catalog_file_missing"), f"{copy.path(PLANTS_JSONL)} is missing")
        self.assertEqual(self.load(copy), expected)

    def test_plant_count_must_match_the_file(self):
        pinned = self.committed_meta()[COUNT]
        message = f"CATALOG.json.plant_count is {pinned + 1}, file has {pinned}"
        expected = (self.code(FIELD_INVALID), message)
        self.assertEqual(self.meta_refusal((COUNT,), pinned + 1), expected)

    def test_plants_file_framing_refusals(self):
        first = self.committed_lines()[0]
        for label, payload, message in (
            ("no final newline", first.rstrip(b"\n"), "plants.jsonl must be LF-framed jsonl"),
            ("blank line", first + b"\n", "plants.jsonl:2 is empty"),
            ("not json", b"{nope}\n", "plants.jsonl:1 is not strict JSON"),
        ):
            with self.subTest(label):
                self.assertEqual(self.rows_refusal(payload), (self.code(FIELD_INVALID), message))

    def test_a_plant_row_must_be_an_object(self):
        expected = (self.code("plant_field_invalid"), "plants.jsonl:1 must be an object")
        self.assertEqual(self.rows_refusal(compact_jsonl([[1]]), plant_count=1), expected)

    def test_a_plant_row_must_rebuild_its_identity(self):
        row = first_row(self.committed)
        for label, key, value, message in (
            ("plant id", PLANT_ID, f"{row[MILL_ID]}:other",
             f"plants.jsonl:1.plant_id must be {row[PLANT_ID]!r}"),
            ("round", BASE, 0, "plants.jsonl:1.base_round must be a positive int"),
        ):
            with self.subTest(label):
                payload = compact_jsonl([row | {key: value}])
                expected = (self.code("plant_field_invalid"), message)
                self.assertEqual(self.rows_refusal(payload, plant_count=1), expected)

    def test_a_plant_row_needs_its_source(self):
        row = mutated(first_row(self.committed), (SOURCE,), DELETE)
        message = "plants.jsonl:1.source must be a non-empty stripped string"
        expected = (self.code("plant_field_missing"), message)
        self.assertEqual(self.rows_refusal(compact_jsonl([row]), plant_count=1), expected)

    def test_a_repeated_plant_row_is_a_duplicate_id(self):
        lines = self.committed_lines()
        plant_id = json.loads(lines[0])[PLANT_ID]
        expected = (self.code("plant_duplicate_id"), f"duplicate plant_id {plant_id}")
        payload = b"".join(lines) + lines[0]
        self.assertEqual(self.rows_refusal(payload, plant_count=len(lines) + 1), expected)

    def test_mill_rows_must_match_the_plants(self):
        pinned = self.committed_meta()[MILLS][0]
        mill_id, count = pinned[MILL_ID], pinned[COUNT]
        extra = {MILL_ID: f"{self.prefix}_r9", BASE: 1, COUNT: 1, SOURCE: "x"}
        # ``mills[:0] = [extra]`` prepends one more mill row than the plants name.
        for label, path, value, message in (
            ("extra mill", (MILLS, slice(0, 0)), [extra],
             "catalog mills do not match plant mill_id values"),
            ("count drift", (*FIRST_MILL, COUNT), count + 1,
             f"{mill_id} plant_count {count + 1} != {count}"),
        ):
            with self.subTest(label):
                expected = (self.code(FIELD_INVALID), message)
                self.assertEqual(self.meta_refusal(path, value), expected)

    def registry_cases(self, registry: Path) -> list[tuple[str, str | None, str]]:
        unreadable = "factory registry is unreadable: "
        not_a_list = "factory registry factories is not a list"
        cases = [
            ("absent", None, f"{unreadable}[Errno 2] No such file or directory: '{registry}'"),
            ("empty", "", f"{unreadable}Expecting value: line 1 column 1 (char 0)"),
            ("factories object", '{"factories": {}}', not_a_list),
            ("top-level list", "[]", not_a_list),
        ]
        if self.pins_unregistered_factory:
            factory = self.committed_meta()[FACTORY]
            unlisted = '{"factories": [{"path_id": "x"}]}'
            cases.append(("unlisted", unlisted, f"{factory} is not a registry path_id"))
        return cases

    def test_registry_refusals(self):
        # Seam: ``<pkg>.catalog.repo_root`` (a public name the module imports from its
        # contract) is the only way to point the registry read at a temp tree.
        root = temp_dir(self)
        (root / "config").mkdir()
        registry = root / "config" / "FACTORY-REGISTRY.json"
        for label, text, message in self.registry_cases(registry):
            with self.subTest(label):
                registry.unlink(missing_ok=True)
                if text is not None:
                    registry.write_text(text, encoding=ENCODING)
                with mock.patch.object(self.catalog, "repo_root", return_value=root):
                    found = refusal(self.error_type, self.catalog.load_catalog, self.committed)
                self.assertEqual(found, (self.code("factory_not_registered"), message))

    def test_an_unknown_mill_is_a_coded_refusal(self):
        loaded = self.catalog.load_catalog(self.committed)
        expected = (self.code("mill_not_found"), "no mill 'nope' in the catalog")
        self.assertEqual(refusal(self.error_type, loaded.mill_plants, "nope"), expected)


class SiblingGenerateContract:
    """Mixin: ``generate.run`` round refusals shared by flk, msd, rag and saf.

    A subclass sets ``generate`` (the package's generate module),
    ``error_type``, ``prefix`` and ``committed``.
    """

    generate: Any = None
    error_type: type[BaseException] = Exception
    prefix = ""
    committed = REPO

    def run_refusal(self, **selectors) -> tuple[tuple[str, str] | None, bool]:
        """The refusal ``run`` raises for ``selectors`` and whether it left a destination."""

        out = temp_dir(self) / "out"
        request = self.generate.GenerateRequest(self.committed, out, **selectors)
        return refusal(self.error_type, self.generate.run, request), out.exists()

    def test_a_round_must_be_a_positive_int(self):
        code = f"{self.prefix}.round_invalid"
        plant_id = first_row(self.committed)[PLANT_ID]
        for value in (0, True):
            with self.subTest(round=value):
                expected = ((code, f"round must be a positive int, got {value!r}"), False)
                self.assertEqual(self.run_refusal(plant_id=plant_id, round=value), expected)

    def test_a_round_applies_only_to_one_plant(self):
        expected = ((f"{self.prefix}.usage", "round applies only with plant_id"), False)
        self.assertEqual(self.run_refusal(all_plants=True, round=3), expected)


def parsed(expression: str) -> ast.expr:
    return ast.parse(expression, mode="eval").body


class LiteralAstContract:
    """Mixin: the ``catalog_ast`` literal helpers that iac and mdb both expose.

    A subclass sets ``ast_module`` (``iac.catalog_ast`` or ``mdb.catalog_ast``).
    """

    ast_module: Any = None

    def value(self, expression: str, env: dict[str, Any] | None = None) -> Any:
        return self.ast_module.literal_value(parsed(expression), env)

    def test_unresolvable_containers_and_fstrings_are_unset(self):
        for expression in ("{**x}", "{'a': x}", "{x: 1}", "{1, x}", "f'{x}'", "f'{1.5}'"):
            with self.subTest(expression):
                self.assertIs(self.value(expression), self.ast_module.UNSET)

    def test_sets_and_bound_fstrings_resolve(self):
        found = (self.value("{1, 2}"), self.value("f'v{n}'", {"n": 3}))
        self.assertEqual(found, ({1, 2}, "v3"))

    def test_joined_paths_need_a_constant_tail(self):
        for expression, expected in (
            ("ROOT / 'experiments' / 'm.py'", "experiments/m.py"),
            ("'a' / x", None),
            ("ROOT / f()", None),
            ("'a' + 'b'", None),
        ):
            with self.subTest(expression):
                found = self.ast_module.joined_path_constant(parsed(expression))
                self.assertEqual(found, expected)

    def test_only_a_one_name_assignment_has_a_name(self):
        for statement, expected in (("a.b = 1", None), ("a = b = 1", None), ("x: int", "x")):
            with self.subTest(statement):
                node = ast.parse(statement).body[0]
                self.assertEqual(self.ast_module.assignment_of(node)[0], expected)


class ExtractNamingContract:
    """Mixin: ``catalog_first_from_name`` and ``write_catalog_document`` for iac and mdb."""

    extract: Any = None

    def test_catalog_first_comes_from_a_trailing_round_marker(self):
        for path, expected in (
            ("experiments/x-mill-r12.py", 12),
            ("experiments/x-mill.py", None),
            ("experiments/x-mill-rab.py", None),
        ):
            with self.subTest(path):
                self.assertEqual(self.extract.catalog_first_from_name(path), expected)

    def test_write_catalog_document_writes_the_dumped_text(self):
        document = {"schema": "s", MILLS: {}}
        path = temp_dir(self) / CATALOG_JSON
        written = self.extract.write_catalog_document(document, path)
        found = (written, path.read_text(encoding=ENCODING))
        self.assertEqual(found, (path, self.extract.dumps_catalog(document)))


class SourceBoundCatalogContract:
    """Mixin: iac/mdb ``load_catalog`` refusals for a catalog bound to ``sources.py``.

    A subclass sets ``catalog`` (module with ``load_catalog(path)``),
    ``catalog_dir``, ``sidecars`` (pinned files copied beside ``CATALOG.json``),
    ``slice_mill`` and ``slice_label`` (``"r609"``...).
    """

    catalog: Any = None
    catalog_dir = REPO
    sidecars: tuple[str, ...] = ()
    slice_mill = ""
    slice_label = ""

    def copy(self) -> CatalogCopy:
        return CatalogCopy(self, self.catalog_dir, (CATALOG_JSON, *self.sidecars))

    def load_error(self, path: tuple[Any, ...], value: Any) -> str | None:
        copy = self.copy()
        written = copy.write_json(mutated(copy.read_json(), path, value))
        return error_text(ValueError, self.catalog.load_catalog, written)

    def test_mill_rows_must_match_the_source_pins(self):
        first = min(self.copy().read_json()[MILLS])
        slice_pairs = (MILLS, self.slice_mill, "pairs", slice(0, 1))
        for label, path, value, message in (
            ("mill deleted", (MILLS, first), DELETE,
             f"catalog mills drifted from sources: extra=[] missing=[{first!r}]"),
            ("slice pair dropped", slice_pairs, [],
             f"{self.slice_label} slice n_rows does not match extracted pairs"),
            ("path drift", (MILLS, first, "path"), "experiments/x.py",
             f"{first} pin disagrees with sources.py"),
            ("pairs off the slice", (MILLS, first, "pairs"), [{"success_slug": "x"}],
             f"{first} is not the first slice and must omit pair rows"),
        ):
            with self.subTest(label):
                self.assertEqual(self.load_error(path, value), message)
