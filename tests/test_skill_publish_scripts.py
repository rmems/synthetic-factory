"""Fail-closed checks in the publish-hub-research-run and land-stacked-prs harness scripts.

The scripts are not a package: each is loaded by path with importlib under a temporary
``$HOME`` holding the work files they read at import. Nothing here reaches the network,
runs ``hf`` / ``huggingface-cli`` / ``gh`` / ``git push``, or writes outside a
TemporaryDirectory: ``subprocess.run`` and the Hub pull-request lookup are stubbed, the
module roots are patched to scratch trees, and pyarrow is replaced by a stand-in that
decodes with the repo's own viewer reader (pyarrow is not a CI dependency).
"""

import contextlib
import importlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / ".claude" / "skills" / "publish-hub-research-run"
LAND = REPO / ".claude" / "skills" / "land-stacked-prs"
sys.path.insert(0, str(REPO / "pipelines"))

export_viewer = importlib.import_module("export_viewer")
rights_document = importlib.import_module("rights_document")
strict_jsonl = importlib.import_module("strict_jsonl")

COLUMNS = ("source_file", "source_line", "record_json")
FACTORY = "thalamic-trajectory-factory"
NAME = "thalamic-relay-trajectories-grok46"
REPO_ID = f"rmems/{NAME}"
SIBLING_NAME = "thalamic-relay-trajectories"
RUN_LABEL = "2026-09-02-final-heavy"
REPO_IDS = (
    REPO_ID,
    "rmems/neuromorphic-event-language-bridge-grok46",
    "rmems/multi-agent-ouroboros-swarm-grok46",
    "rmems/failure-as-fuel-preference-cascade-grok46",
    "rmems/agentic-coding-trajectories-grok46",
)
STATUS_KEYS = (
    "schema_version", "dataset_id", "release_stage", "visibility", "payload_published",
    "training_ready", "strict_audit", "license", "next_gate", "updated_at", "intended_use",
    "project_training_policy", "rights_record",
)
RESEARCH_LICENSE = (
    "license: other\nlicense_name: synthetic-factory-research-only\nlicense_link: LICENSE\n"
)

SCRIPTS: dict[str, types.ModuleType] = {}
_HOME: tempfile.TemporaryDirectory | None = None


# --- a pyarrow stand-in -------------------------------------------------------------------


class _Column:
    def __init__(self, values):
        self._values = list(values)

    def to_pylist(self):
        return list(self._values)


class _Field:
    def __init__(self, name, type_name):
        self.name = name
        self.type = type_name


class _Schema:
    def __init__(self, names, line_type):
        self._fields = [_Field(n, line_type if n == "source_line" else "string") for n in names]

    def __iter__(self):
        return iter(self._fields)

    def field(self, name):
        return next(f for f in self._fields if f.name == name)


class _Table:
    def __init__(self, columns, num_rows, names, line_type):
        self._columns = columns
        self.num_rows = num_rows
        self.schema = _Schema(names, line_type)

    def column(self, name):
        return _Column(self._columns[name])


def fake_pyarrow(**defect):
    """(pyarrow, pyarrow.parquet) stand-ins; ``defect`` overrides what read_table reports."""

    def read_table(buffer):
        rows = export_viewer.read_viewer_parquet(buffer.read())
        columns = {name: [getattr(r, name) for r in rows] for name in COLUMNS}
        columns.update(defect.get("columns", {}))
        return _Table(
            columns,
            defect.get("num_rows", len(rows)),
            defect.get("names", COLUMNS),
            defect.get("line_type", "int64"),
        )

    parquet = types.ModuleType("pyarrow.parquet")
    parquet.read_table = read_table
    package = types.ModuleType("pyarrow")
    package.parquet = parquet
    return package, parquet


@contextlib.contextmanager
def installed_pyarrow(package, parquet):
    """Serve the stand-in to ``import pyarrow.parquet`` and restore sys.modules after."""
    saved = {key: sys.modules.get(key) for key in ("pyarrow", "pyarrow.parquet")}
    sys.modules["pyarrow"] = package
    sys.modules["pyarrow.parquet"] = parquet
    try:
        yield
    finally:
        for key, module in saved.items():
            if module is None:
                sys.modules.pop(key, None)
            else:
                sys.modules[key] = module


# --- loading the scripts ------------------------------------------------------------------


def _write_work_files(home: Path) -> None:
    work = home / "tmp" / "publish-0902" / "work"
    work.mkdir(parents=True)
    (work / "LICENSE-cc-by-nc-4.0.txt").write_bytes(b"fixture license\n")
    (work / "repos.json").write_text(json.dumps({r: {"sha": "0" * 40} for r in REPO_IDS}))
    for summaries in ("bundle_summaries.json", "fix_summaries.json"):
        (work / summaries).write_text(json.dumps([{"repo": r} for r in REPO_IDS]))


def _load(name: str, home: Path) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(f"skill_publish_{name}", SKILL / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    saved_path = list(sys.path)
    try:
        with mock.patch.dict(os.environ, {"HOME": str(home)}), installed_pyarrow(*fake_pyarrow()):
            spec.loader.exec_module(module)
    finally:
        sys.path[:] = saved_path  # the build scripts prepend the owner's checkout path
    return module


def setUpModule():
    global _HOME
    _HOME = tempfile.TemporaryDirectory()
    home = Path(_HOME.name)
    _write_work_files(home)
    for name in ("build_bundles", "build_fix", "upload_pr", "upload_fix"):
        SCRIPTS[name] = _load(name, home)


def tearDownModule():
    if _HOME is not None:
        _HOME.cleanup()


# --- fixtures -----------------------------------------------------------------------------


def record(record_id, **fields):
    payload = {
        "id": record_id,
        "goal": "fixture goal",
        "meta": {
            "factory": FACTORY,
            "generator": "grok-4.6",
            "run_label": RUN_LABEL,
            "rights": {"generation_surface": "SuperGrok Heavy chat"},
        },
    }
    payload.update(fields)
    return payload


def jsonl(*records) -> bytes:
    return "".join(json.dumps(r) + "\n" for r in records).encode("utf-8")


def viewer_rows(source_file="data/raw/batch-r01.jsonl", *lines):
    row = export_viewer.ViewerRow
    return [
        row(source_file=source_file, source_line=n, record_json=line)
        for n, line in enumerate(lines or ('{"id": "a"}',), 1)
    ]


class ScriptTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(self.enterContext(tempfile.TemporaryDirectory()))

    def assertRefuses(self, error, message, call, *args):
        with self.assertRaises(error) as caught:
            call(*args)
        self.assertEqual(str(caught.exception), message)

    def source_tree(self) -> Path:
        """An immutable-tree stand-in: r01, a disjoint r02/r02c pair, and one notes file."""
        source = self.tmp / "source" / FACTORY
        source.mkdir(parents=True)
        files = {
            "batch-r01.jsonl": jsonl(
                record("t-r01-0", safety_decision={"decision": "ACCEPT"}),
                record("t-r01-1", extra_key=1),
            ),
            "batch-r02.jsonl": jsonl(record("t-r02-0")),
            "batch-r02c.jsonl": jsonl(record("t-r02c-0"), record("t-r02c-1")),
            "NOTES-r01.md": b"# r01\nNovel coverage: 12%\n",
        }
        for name, payload in files.items():
            (source / name).write_bytes(payload)
        return source


# --- build_bundles.py ---------------------------------------------------------------------


class BuildBundlesTests(ScriptTestCase):
    def setUp(self):
        super().setUp()
        self.bb = SCRIPTS["build_bundles"]
        self.error = self.bb.BundleCheckError
        self.source = self.source_tree()
        self.run_dir = self.tmp / "run" / FACTORY
        self.run_dir.mkdir(parents=True)
        for name in ("batch-r01.jsonl", "batch-r02c.jsonl", "NOTES-r01.md"):
            shutil.copyfile(self.source / name, self.run_dir / name)
        sibling = self.tmp / "siblings" / SIBLING_NAME
        sibling.mkdir(parents=True)
        (sibling / "release-status.json").write_text(json.dumps(dict.fromkeys(STATUS_KEYS, "x")))
        (sibling / "provenance.json").write_text(json.dumps({"raw_evidence_policy": "fixture"}))
        self.enterContext(mock.patch.multiple(
            self.bb,
            SOURCE=self.tmp / "source",
            RUN=self.tmp / "run",
            BUNDLES=self.tmp / "bundles",
            SIBLINGS=self.tmp / "siblings",
        ))
        self.enterContext(installed_pyarrow(*fake_pyarrow()))
        self.cfg = self.bb.FACTORIES[0]
        self.bundle = self.tmp / "bundles" / NAME

    def test_build_one_accepts_a_consistent_fixture(self):
        summary = self.bb.build_one(self.cfg)

        self.assertEqual(summary["rounds"], ["r01", "r02c"])
        self.assertEqual(summary["superseded"], ["batch-r02.jsonl"])
        self.assertEqual(summary["records"], 4)
        self.assertEqual(summary["decisions"], {"ACCEPT": 1})
        self.assertEqual(
            (self.bundle / "data/raw/batch-r02c.jsonl").read_bytes(),
            (self.source / "batch-r02c.jsonl").read_bytes(),
        )
        rights_document.load_rights_document_bytes((self.bundle / "rights.json").read_bytes())
        self.assertIn("indexes 4 rows.", (self.bundle / "README.md").read_text())

    def test_round_key_refuses_an_unparseable_name(self):
        self.assertRefuses(self.error, "batch-final.jsonl", self.bb.round_key, "batch-final.jsonl")

    def test_round_files_refuses_a_batch_name_outside_the_c_suffix_rule(self):
        (self.run_dir / "batch-r03b.jsonl").write_bytes(b"")
        self.assertRefuses(
            self.error,
            str(["batch-r01.jsonl", "batch-r02c.jsonl", "batch-r03b.jsonl"]),
            self.bb._round_files,
            self.run_dir,
        )

    def test_copy_batches_refuses_drift_from_the_immutable_source(self):
        (self.run_dir / "batch-r01.jsonl").write_bytes(jsonl(record("t-r01-0")))
        self.assertRefuses(
            self.error, "drift vs immutable source: batch-r01.jsonl", self.bb.build_one, self.cfg
        )

    def test_copy_batches_refuses_a_copy_that_does_not_read_back(self):
        self.bb._reset_bundle_dirs(self.bundle)
        with mock.patch.object(Path, "write_bytes", lambda path, data: path.write_text("x")):
            self.assertRefuses(
                self.error,
                "raw copy does not read back byte-identical: batch-r01.jsonl",
                self.bb._copy_batches, FACTORY, self.run_dir, self.bundle, ["batch-r01.jsonl"],
            )

    def test_copy_batches_refuses_a_lossy_line_split(self):
        self.bb._reset_bundle_dirs(self.bundle)
        first_line = jsonl(record("t-r01-0")).decode().rstrip("\n")
        with mock.patch.object(strict_jsonl, "strict_lf_jsonl_lines", return_value=[first_line]):
            self.assertRefuses(
                self.error, "batch-r01.jsonl", self.bb._copy_batches,
                FACTORY, self.run_dir, self.bundle, ["batch-r01.jsonl"],
            )

    def test_copy_notes_refuses_drift_from_the_immutable_source(self):
        self.bb._reset_bundle_dirs(self.bundle)
        (self.run_dir / "NOTES-r01.md").write_bytes(b"edited\n")
        self.assertRefuses(
            self.error, "drift vs immutable source: NOTES-r01.md", self.bb._copy_notes,
            FACTORY, self.run_dir, self.bundle, ["NOTES-r01.md"],
        )

    def test_viewer_checks_refuse_each_projection_defect(self):
        assert_viewer_defects_refused(self, self.bb, self.error, local_import=True)

    def test_census_refuses_repeated_or_non_string_ids(self):
        for records in ([record("a"), record("a")], [record(7)]):
            with self.subTest(records=records):
                self.assertRefuses(self.error, "ids not unique", self.bb._record_census, records)

    def test_stamp_checks_refuse_each_foreign_stamp(self):
        assert_stamp_defects_refused(self, self.bb._check_record_stamps, self.error)

    def test_superseded_base_must_exist_in_the_immutable_source(self):
        (self.source / "batch-r02.jsonl").unlink()
        self.assertRefuses(
            self.error, "batch-r02.jsonl", self.bb._superseded_bases, FACTORY, ["batch-r02c.jsonl"]
        )

    def test_release_status_refuses_a_sibling_key_order_drift(self):
        self.bb._reset_bundle_dirs(self.bundle)
        reordered = dict.fromkeys(reversed(STATUS_KEYS), "x")
        (self.tmp / "siblings" / SIBLING_NAME / "release-status.json").write_text(
            json.dumps(reordered)
        )
        self.assertRefuses(
            self.error,
            str((list(STATUS_KEYS), list(reordered))),
            self.bb._write_release_status, self.bundle, self.cfg,
        )


def assert_viewer_defects_refused(case, module, error, *, local_import):
    """Drive _verify_viewer_parquet through each of its seven refusals."""
    rows = viewer_rows("data/raw/batch-r01.jsonl", '{"id": "a"}', '{"id": "b"}')
    parquet = export_viewer.write_viewer_parquet(rows)
    defects = [
        ({}, rows[:1], "viewer parquet does not read back to the source rows"),
        ({"num_rows": 9}, rows, "viewer parquet row count differs from the source rows"),
        ({"columns": {"source_file": ["x", "y"]}}, rows,
         "viewer parquet column source_file differs from the source rows"),
        ({"columns": {"source_line": [2, 1]}}, rows,
         "viewer parquet column source_line differs from the source rows"),
        ({"columns": {"record_json": ["{}", "{}"]}}, rows,
         "viewer parquet column record_json differs from the source rows"),
        ({"names": ("source_file", "record_json", "source_line")}, rows,
         "viewer parquet columns are not source_file, source_line, record_json"),
        ({"line_type": "int32"}, rows, "viewer parquet source_line is not int64"),
    ]
    for defect, expected_rows, message in defects:
        with case.subTest(message=message):
            package, parquet_module = fake_pyarrow(**defect)
            if local_import:
                patch = installed_pyarrow(package, parquet_module)
            else:
                patch = mock.patch.object(module, "pq", parquet_module)
            with patch:
                case.assertRefuses(
                    error, message, module._verify_viewer_parquet, parquet, expected_rows
                )
    module_patch = (
        installed_pyarrow(*fake_pyarrow()) if local_import
        else mock.patch.object(module, "pq", fake_pyarrow()[1])
    )
    with module_patch:
        module._verify_viewer_parquet(parquet, rows)  # a faithful projection passes


def assert_stamp_defects_refused(case, check, error):
    defects = [
        ({"generator": "grok-4.5"}, "a record is not stamped meta.generator grok-4.6"),
        ({"factory": "other-factory"}, f"a record is not stamped meta.factory {FACTORY}"),
        ({"run_label": "2026-01-01"}, f"a record is not stamped meta.run_label {RUN_LABEL}"),
    ]
    check([record("a")], FACTORY)
    for meta_change, message in defects:
        with case.subTest(message=message):
            bad = record("b")
            bad["meta"].update(meta_change)
            case.assertRefuses(error, message, check, [record("a"), bad], FACTORY)


# --- build_fix.py -------------------------------------------------------------------------


class BuildFixPureChecksTests(ScriptTestCase):
    def setUp(self):
        super().setUp()
        self.bf = SCRIPTS["build_fix"]
        self.error = self.bf.FixBundleCheckError

    def test_round_key_refuses_an_unparseable_name(self):
        self.assertRefuses(self.error, "NOTES-x.md", self.bf.round_key, "NOTES-x.md")

    def test_census_refuses_repeated_or_non_string_ids(self):
        for records in ([record("a"), record("a")], [record(None)]):
            with self.subTest(records=records):
                self.assertRefuses(self.error, "ids not unique", self.bf.census, records)

    def test_sub_once_refuses_zero_or_several_matches(self):
        for text, count in (("abc", 0), ("zz", 2)):
            with self.subTest(text=text):
                self.assertRefuses(
                    self.error, str(("label", count)), self.bf.sub_once, text, "z", "y", "label"
                )

    def test_release_count_patch_refuses_a_card_without_the_sentence(self):
        old = {"records": 1, "file_count": 1}
        self.assertRefuses(
            self.error, "release contains", self.bf._patch_release_counts, "no card", old, old
        )

    def test_rounds_patch_refuses_rule_wording_drift(self):
        with mock.patch.object(self.bf, "RULE_MD", "a rule the card does not state"):
            self.assertRefuses(
                self.error, "rule wording drift", self.bf._patch_rounds_bullets, "card",
                ["batch-r01.jsonl"],
            )

    def test_front_matter_refuses_a_card_without_a_fence(self):
        self.assertRefuses(
            self.error, "README does not open with a front-matter fence",
            self.bf.front_matter, "# no front matter\n",
        )

    def test_viewer_checks_refuse_each_projection_defect(self):
        assert_viewer_defects_refused(self, self.bf, self.error, local_import=False)

    def test_stamp_checks_refuse_each_foreign_stamp(self):
        assert_stamp_defects_refused(self, self.bf._check_record_stamps, self.error)

    def test_old_snapshot_checks_refuse_each_mismatch(self):
        old = {"records": 2, "file_count": 1, "parquet_bytes": 10, "parquet_sha256": "ab"}
        good = {
            "selection_rule": self.bf.OLD_PROV_RULE,
            "records": 2,
            "files": [{}],
            "viewer": {"bytes": 10, "sha256": "ab"},
            "superseded_not_published": ["batch-r02.jsonl"],
        }
        self.bf._check_old_snapshot(good, old, ["batch-r02.jsonl"])
        defects = [
            ({"selection_rule": "other"},
             "provenance selection_rule is not the old supersede rule"),
            ({"records": 3}, "provenance record or file totals differ from the Hub files"),
            ({"files": []}, "provenance record or file totals differ from the Hub files"),
            ({"viewer": {"bytes": 11, "sha256": "ab"}},
             "provenance viewer size or digest differs from the Hub parquet"),
            ({"viewer": {"bytes": 10, "sha256": "cd"}},
             "provenance viewer size or digest differs from the Hub parquet"),
            ({"superseded_not_published": []},
             "provenance superseded_not_published differs from the derived omissions"),
        ]
        for change, message in defects:
            with self.subTest(change=change):
                self.assertRefuses(
                    self.error, message, self.bf._check_old_snapshot,
                    {**good, **change}, old, ["batch-r02.jsonl"],
                )

    def test_existing_file_entries_must_be_reproduced_exactly(self):
        entry = {"path": "data/raw/batch-r01.jsonl", "sha256": "ab", "records": 2}
        snap = {"files": [entry]}
        self.bf._check_existing_entries(snap, [entry, {"path": "data/raw/batch-r02.jsonl"}])
        self.assertRefuses(
            self.error, "data/raw/batch-r01.jsonl", self.bf._check_existing_entries,
            snap, [{**entry, "records": 3}],
        )

    def test_rewritten_snapshot_refuses_a_foreign_viewer_writer(self):
        snap = {"viewer": {"writer": "some other writer"}}
        self.assertRefuses(
            self.error, "provenance viewer writer is not the factory's export writer",
            self.bf._rewritten_snapshot, snap, {}, [],
        )

    def test_front_matter_delta_refuses_any_change_but_the_split_numbers(self):
        old = {"rows": 2, "parquet_bytes": 10}
        new = {"rows": 3, "parquet_bytes": 12}
        card = "---\na: 1\n    num_examples: {rows}\n    num_bytes: {parquet_bytes}\n---\nbody\n"
        self.bf._check_front_matter_delta(card.format(**old), card.format(**new), old, new)
        self.assertRefuses(
            self.error, "README front matter line count changed",
            self.bf._check_front_matter_delta,
            card.format(**old), card.format(**new).replace("a: 1\n", ""), old, new,
        )
        changed = card.format(**new).replace("a: 1", "a: 2")
        self.assertRefuses(
            self.error,
            str([
                ("a: 1", "a: 2"),
                ("    num_examples: 2", "    num_examples: 3"),
                ("    num_bytes: 10", "    num_bytes: 12"),
            ]),
            self.bf._check_front_matter_delta, card.format(**old), changed, old, new,
        )

    def test_card_wording_checks_refuse_each_stale_or_missing_statement(self):
        readme = "---\n" + RESEARCH_LICENSE + "---\n| `data/raw/batch-r02.jsonl` | 1 |\n"
        prov = {"raw_snapshot": {}}
        self.bf._check_card_wording(readme, "{}", prov, ["batch-r02.jsonl"])
        cases = [
            (readme.replace("license: other\n", ""), "{}", prov, [],
             "README front matter does not declare the research-only license"),
            (readme + "superseded\n", "{}", prov, [], "supersed"),
            (readme, '{"notes": "Supersession"}', prov, [], "Supersession"),
            (readme, "{}", {"note": "corrected re-emission"}, [], "corrected re-emission"),
            (readme, "{}", prov, ["batch-r03.jsonl"], "batch-r03.jsonl"),
        ]
        for card, rights_text, provenance, missing, message in cases:
            with self.subTest(message=message):
                self.assertRefuses(
                    self.error, message, self.bf._check_card_wording,
                    card, rights_text, provenance, missing,
                )

    def test_release_status_must_not_carry_a_count(self):
        cur = self.tmp / "cur"
        cur.mkdir()
        (cur / "release-status.json").write_text(json.dumps({"training_ready": False}))
        self.bf._check_release_status(cur)
        (cur / "release-status.json").write_text(json.dumps({"records": 4}))
        self.assertRefuses(
            self.error, "release-status.json carries a count", self.bf._check_release_status, cur
        )


class BuildFixTreeTests(ScriptTestCase):
    """Checks that read the immutable tree or the current Hub download."""

    def setUp(self):
        super().setUp()
        self.bf = SCRIPTS["build_fix"]
        self.error = self.bf.FixBundleCheckError
        self.source = self.source_tree()
        self.enterContext(mock.patch.multiple(
            self.bf,
            SOURCE=self.tmp / "source",
            CURRENT=self.tmp / "current",
            FIX=self.tmp / "fix",
            RUN_FIX=self.tmp / "run-fix",
        ))
        self.cur = self.tmp / "current" / NAME

    def test_derive_missing_accepts_a_disjoint_pair(self):
        self.assertEqual(
            self.bf.derive_missing(FACTORY, ["batch-r01.jsonl", "batch-r02c.jsonl"]),
            (["batch-r02.jsonl"], []),
        )

    def test_derive_missing_refuses_a_c_file_without_its_base(self):
        (self.source / "batch-r02.jsonl").unlink()
        self.assertRefuses(
            self.error, "batch-r02.jsonl", self.bf.derive_missing, FACTORY, ["batch-r02c.jsonl"]
        )

    def test_derive_missing_refuses_a_c_file_that_is_not_on_the_hub(self):
        self.assertRefuses(self.error, "batch-r02c.jsonl", self.bf.derive_missing, FACTORY, [])

    def test_derive_missing_refuses_a_base_file_already_on_the_hub(self):
        self.assertRefuses(
            self.error, "batch-r02.jsonl", self.bf.derive_missing,
            FACTORY, ["batch-r02.jsonl", "batch-r02c.jsonl"],
        )

    def test_derive_missing_refuses_repeated_ids_inside_a_file(self):
        (self.source / "batch-r02c.jsonl").write_bytes(jsonl(record("c"), record("c")))
        self.assertRefuses(
            self.error, "repeated record ids inside batch-r02c.jsonl or batch-r02.jsonl",
            self.bf.derive_missing, FACTORY, ["batch-r02c.jsonl"],
        )

    def test_derive_missing_refuses_a_partial_id_overlap(self):
        (self.source / "batch-r02c.jsonl").write_bytes(jsonl(record("t-r02-0"), record("new")))
        self.assertRefuses(
            self.error, str((FACTORY, "batch-r02.jsonl", {"t-r02-0"})),
            self.bf.derive_missing, FACTORY, ["batch-r02c.jsonl"],
        )

    def test_load_rows_refuses_a_lossy_line_split(self):
        first_line = jsonl(record("t-r01-0")).decode().rstrip("\n")
        with mock.patch.object(strict_jsonl, "strict_lf_jsonl_lines", return_value=[first_line]):
            self.assertRefuses(
                self.error, "batch-r01.jsonl", self.bf.load_rows, FACTORY, ["batch-r01.jsonl"]
            )

    def hub_raw(self, *names) -> Path:
        raw = self.cur / "data" / "raw"
        raw.mkdir(parents=True)
        for name in names:
            shutil.copyfile(self.source / name, raw / name)
        return raw

    def test_current_raw_names_refuses_a_name_outside_the_c_suffix_rule(self):
        raw = self.hub_raw("batch-r01.jsonl")
        (raw / "batch-r03b.jsonl").write_bytes(b"")
        self.assertRefuses(
            self.error, str(["batch-r01.jsonl", "batch-r03b.jsonl"]),
            self.bf._current_raw_names, FACTORY, self.cur,
        )

    def test_current_raw_names_refuses_a_hub_file_that_differs_from_the_source(self):
        raw = self.hub_raw("batch-r01.jsonl")
        (raw / "batch-r01.jsonl").write_bytes(jsonl(record("t-r01-0")))
        self.assertRefuses(
            self.error, "batch-r01.jsonl", self.bf._current_raw_names, FACTORY, self.cur
        )

    def test_current_raw_names_refuses_a_records_jsonl_viewer(self):
        self.hub_raw("batch-r01.jsonl")
        (self.cur / "data" / "viewer").mkdir()
        (self.cur / "data" / "viewer" / "records.jsonl").write_bytes(b"")
        self.assertRefuses(
            self.error, "unexpected records.jsonl", self.bf._current_raw_names, FACTORY, self.cur
        )

    def test_selection_refuses_unexpected_missing_or_duplicate_files(self):
        derived = (["batch-r02.jsonl"], [])
        with mock.patch.object(self.bf, "derive_missing", return_value=derived):
            self.assertRefuses(
                self.error, str((FACTORY, ["batch-r02.jsonl"], [])),
                self.bf._selection, FACTORY, [], [],
            )
        with mock.patch.object(self.bf, "derive_missing", return_value=([], ["batch-r09.jsonl"])):
            self.assertRefuses(
                self.error, str((FACTORY, ["batch-r09.jsonl"])),
                self.bf._selection, FACTORY, [], [],
            )

    def test_hub_viewer_must_be_reproduced_by_the_writer(self):
        self.hub_raw("batch-r01.jsonl")
        (self.cur / "data" / "viewer").mkdir()
        (self.cur / "data" / "viewer" / "records.parquet").write_bytes(b"not the writer's bytes")
        self.assertRefuses(
            self.error, "writer drift", self.bf._reproduce_hub_viewer,
            FACTORY, ["batch-r01.jsonl"], self.cur,
        )

    def test_copy_verbatim_refuses_a_copy_that_does_not_read_back(self):
        dest = self.tmp / "dest"
        dest.mkdir()
        with mock.patch.object(Path, "write_bytes", lambda path, data: path.write_text("x")):
            self.assertRefuses(
                self.error, "copy does not read back byte-identical: batch-r01.jsonl",
                self.bf._copy_verbatim, FACTORY, ["batch-r01.jsonl"], dest,
            )

    def test_current_provenance_refuses_a_non_canonical_serialization(self):
        self.cur.mkdir(parents=True)
        (self.cur / "provenance.json").write_text(json.dumps({"raw_snapshot": {}}))
        self.assertRefuses(
            self.error, "provenance serialization", self.bf._current_provenance, self.cur
        )

    def rights_target(self, text: str):
        self.cur.mkdir(parents=True)
        (self.tmp / "fix" / NAME).mkdir(parents=True)
        (self.cur / "rights.json").write_text(text)
        return self.bf._Target(FACTORY, REPO_ID, self.cur, self.tmp / "fix" / NAME, self.tmp)

    def test_rights_patch_refuses_a_record_without_the_old_sentence_once(self):
        target = self.rights_target(json.dumps({"notes": "no sentence here"}))
        self.assertRefuses(
            self.error, "rights.json does not carry the old c-file sentence exactly once",
            self.bf._write_rights, target,
        )

    def test_rights_patch_refuses_an_edit_outside_notes(self):
        sentence = self.bf.OLD_RIGHTS_SENTENCE
        target = self.rights_target(json.dumps({"notes": "n", "status_basis": sentence}))
        with mock.patch.object(rights_document, "load_rights_document_bytes"):
            self.assertRefuses(
                self.error, "rights.json changed outside notes", self.bf._write_rights, target
            )
        self.assertFalse((target.fix / "rights.json").exists())


class BuildFixEndToEndTests(ScriptTestCase):
    """build_bundles output, staged as the current Hub state, drives build_fix end to end."""

    def test_delta_bundle_adds_the_omitted_base_file(self):
        bb, bf = SCRIPTS["build_bundles"], SCRIPTS["build_fix"]
        source = self.source_tree()
        run_dir = self.tmp / "run" / FACTORY
        run_dir.mkdir(parents=True)
        for name in ("batch-r01.jsonl", "batch-r02c.jsonl", "NOTES-r01.md"):
            shutil.copyfile(source / name, run_dir / name)
        sibling = self.tmp / "siblings" / SIBLING_NAME
        sibling.mkdir(parents=True)
        (sibling / "release-status.json").write_text(json.dumps(dict.fromkeys(STATUS_KEYS, "x")))
        (sibling / "provenance.json").write_text(json.dumps({"raw_evidence_policy": "fixture"}))
        with mock.patch.multiple(
            bb, SOURCE=self.tmp / "source", RUN=self.tmp / "run",
            BUNDLES=self.tmp / "bundles", SIBLINGS=self.tmp / "siblings",
        ), installed_pyarrow(*fake_pyarrow()):
            bb.build_one(bb.FACTORIES[0])
        current = self.tmp / "current" / NAME
        shutil.copytree(self.tmp / "bundles" / NAME, current)
        card = (current / "README.md").read_text()
        research_card = card.replace("license: cc-by-nc-4.0\n", RESEARCH_LICENSE)
        (current / "README.md").write_text(research_card)

        with mock.patch.multiple(
            bf, SOURCE=self.tmp / "source", CURRENT=self.tmp / "current",
            FIX=self.tmp / "fix", RUN_FIX=self.tmp / "run-fix",
        ):
            summary = bf.build_one(FACTORY, REPO_ID, ["batch-r02.jsonl"])

        self.assertEqual(summary["added_files"], ["data/raw/batch-r02.jsonl"])
        self.assertEqual((summary["records_before"], summary["records_after"]), (4, 5))
        self.assertEqual(summary["rounds_after"], ["r01", "r02", "r02c"])
        self.assertEqual(
            summary["delta_files"],
            ["README.md", "data/raw/batch-r02.jsonl", "data/viewer/records.parquet",
             "provenance.json", "rights.json"],
        )
        self.assertEqual(
            sorted(p.name for p in (self.tmp / "run-fix" / FACTORY).iterdir()),
            ["batch-r01.jsonl", "batch-r02.jsonl", "batch-r02c.jsonl"],
        )


class OptimizedInterpreterTests(unittest.TestCase):
    """The checks are not asserts, so ``python -O`` still refuses."""

    PROBE = r"""
import importlib.util, json, sys, types
from pathlib import Path
repo = Path(sys.argv[1])
sys.path.insert(0, str(repo / "pipelines"))
parquet = types.ModuleType("pyarrow.parquet")
package = types.ModuleType("pyarrow")
package.parquet = parquet
sys.modules.update({"pyarrow": package, "pyarrow.parquet": parquet})

def load(name):
    path = repo / ".claude" / "skills" / "publish-hub-research-run" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

bb, bf = load("build_bundles"), load("build_fix")
probes = {
    "bare assert": lambda: exec("assert False"),
    "bb.round_key": lambda: bb.round_key("batch-final.jsonl"),
    "bb.census": lambda: bb._record_census([{"id": "a"}, {"id": "a"}]),
    "bf.census": lambda: bf.census([{"id": "a"}, {"id": "a"}]),
    "bf.sub_once": lambda: bf.sub_once("abc", "z", "y", "label"),
}
out = {"optimize": sys.flags.optimize}
for key, probe in probes.items():
    try:
        probe()
        out[key] = "accepted"
    except Exception as exc:
        out[key] = type(exc).__name__ + ": " + str(exc)
print(json.dumps(out))
"""

    def test_checks_refuse_under_python_dash_o(self):
        with tempfile.TemporaryDirectory() as home:
            _write_work_files(Path(home))
            env = {**os.environ, "HOME": home}
            completed = subprocess.run(
                [sys.executable, "-O", "-c", self.PROBE, str(REPO)],
                capture_output=True, text=True, env=env, cwd=home, check=False, timeout=120,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        out = json.loads(completed.stdout)
        self.assertEqual(out["optimize"], 1)
        self.assertEqual(out["bare assert"], "accepted")  # proves -O really stripped asserts
        self.assertEqual(out["bb.round_key"], "BundleCheckError: batch-final.jsonl")
        self.assertEqual(out["bb.census"], "BundleCheckError: ids not unique")
        self.assertEqual(out["bf.census"], "FixBundleCheckError: ids not unique")
        self.assertEqual(out["bf.sub_once"], "FixBundleCheckError: ('label', 0)")


# --- upload_pr.py / upload_fix.py ---------------------------------------------------------


def _pipelines_dataset_id_pattern() -> str:
    pattern = getattr(rights_document, "_DATASET_ID_RE", None)
    if pattern is None:  # the procedural rights route moves it to rights_document_support
        pattern = importlib.import_module("rights_document_support").DATASET_ID_RE
    return pattern.pattern


BAD_NAMES = (
    "", "../escape", "a/b", "-h", "--create-pr", "trailing-", ".hidden", "sp ace",
    "name\n", "name;rm", "$(id)",
)
BAD_SIBLINGS = (
    "thalamic-relay-trajectories", "rmems/../x", "rmems/a b", "-rmems/x", "rmems/x\n",
    "rmems/x/y", "/rmems", "rmems/",
)
PR_SUMMARY = {
    "repo": REPO_ID, "factory": FACTORY, "rounds": ["r01", "r02c"],
    "superseded": ["batch-r02.jsonl"], "notes": 1, "records": 4, "files": 2, "rows": 4,
    "parquet_bytes": 100,
}
FIX_SUMMARY = {
    "repo": REPO_ID, "factory": FACTORY, "added_files": ["data/raw/batch-r02.jsonl"],
    "added_records": 1, "omitted_duplicates": [], "rounds_after": ["r01", "r02", "r02c"],
    "files_after": 3, "parquet_rows_before": 4, "parquet_rows_after": 5,
    "parquet_bytes_before": 100, "parquet_bytes_after": 120, "records_after": 5,
}


class UploadScriptChecks:
    """Checks shared by both upload scripts; mixed into one TestCase per script."""

    script = ""
    root_attr = ""
    summary = None

    def setUp(self):
        super().setUp()
        self.up = SCRIPTS[self.script]
        self.root = self.tmp / "bundles"
        (self.root / NAME).mkdir(parents=True)
        (self.tmp / "work").mkdir()
        self.enterContext(mock.patch.multiple(
            self.up, BASE=self.tmp, SUMMARIES={REPO_ID: self.summary},
            **{self.root_attr: self.root},
        ))
        self.run = self.enterContext(mock.patch.object(self.up.subprocess, "run"))

    def test_hub_id_pattern_is_the_one_the_pipelines_enforce(self):
        self.assertEqual(self.up.HUB_DATASET_ID.pattern, _pipelines_dataset_id_pattern())

    def test_known_repo_refuses_ids_outside_the_strict_pattern(self):
        for name in BAD_NAMES:
            with self.subTest(name=name):
                self.assertRefuses(
                    self.up.UploadInputError, f"not an owner/name Hub id: {'rmems/' + name!r}",
                    self.up._known_repo, name,
                )

    def test_known_repo_refuses_a_repo_without_a_summary(self):
        with self.assertRaises(self.up.UploadInputError) as caught:
            self.up._known_repo("never-built-grok46")
        self.assertIn("summary for rmems/never-built-grok46", str(caught.exception))
        self.assertEqual(self.up._known_repo(NAME), REPO_ID)

    def test_bundle_dir_refuses_a_missing_directory_or_a_plain_file(self):
        self.assertRefuses(
            self.up.UploadInputError, f"no bundle directory at {self.root / 'absent'}",
            self.up._bundle_dir, self.root, "absent",
        )
        (self.root / "plain").write_text("not a directory")
        self.assertRefuses(
            self.up.UploadInputError, f"no bundle directory at {self.root / 'plain'}",
            self.up._bundle_dir, self.root, "plain",
        )
        self.assertEqual(self.up._bundle_dir(self.root, NAME), self.root / NAME)

    def test_bundle_dir_refuses_a_symlink_that_leaves_the_root(self):
        outside = self.tmp / "outside"
        outside.mkdir()
        (self.root / "escape").symlink_to(outside, target_is_directory=True)
        self.assertRefuses(
            self.up.UploadInputError, f"bundle path leaves {self.root}: {self.root / 'escape'}",
            self.up._bundle_dir, self.root, "escape",
        )

    def assert_refused_without_side_effects(self, argv, message):
        with mock.patch("sys.stderr", new_callable=io.StringIO) as stderr:
            self.assertEqual(self.up.main(argv), 2)
        self.assertEqual(stderr.getvalue(), f"refused: {message}\n")
        self.run.assert_not_called()
        self.assertEqual(list((self.tmp / "work").iterdir()), [])

    def stub_upload(self, returncode):
        url = f"https://huggingface.co/datasets/{REPO_ID}/discussions/1"
        self.run.return_value = subprocess.CompletedProcess(
            args=[], returncode=returncode, stdout=f"PR at {url}\n", stderr="",
        )
        return url

    def expected_argv(self, message, desc):
        return [
            self.up.HF, "upload", REPO_ID, str(self.root / NAME), ".", "--repo-type", "dataset",
            "--create-pr", "--commit-message", message, "--commit-description", desc,
        ]


class UploadPrTests(UploadScriptChecks, ScriptTestCase):
    script = "upload_pr"
    root_attr = "BUNDLES"
    summary = PR_SUMMARY

    def test_main_refuses_bad_arguments_before_writing_or_running(self):
        sibling = "rmems/thalamic-relay-trajectories"
        cases = [
            ([NAME], self.up.USAGE),
            ([NAME, sibling, "extra"], self.up.USAGE),
            (["../escape", sibling], "not an owner/name Hub id: 'rmems/../escape'"),
        ] + [
            ([NAME, bad], f"sibling is not an owner/name Hub id: {bad!r}") for bad in BAD_SIBLINGS
        ]
        for argv, message in cases:
            with self.subTest(argv=argv):
                self.assert_refused_without_side_effects(argv, message)

    def test_main_runs_hf_upload_with_a_fixed_argv(self):
        url = self.stub_upload(0)
        stdout = self.enterContext(mock.patch("sys.stdout", new_callable=io.StringIO))
        sibling = "rmems/thalamic-relay-trajectories"

        self.assertEqual(self.up.main([NAME, sibling]), 0)

        desc = self.up.description(PR_SUMMARY, sibling)
        self.run.assert_called_once_with(
            self.expected_argv(self.up.COMMIT_MESSAGE, desc),
            capture_output=True, text=True, check=False,
        )
        self.assertEqual((self.tmp / "work" / f"pr-description-{NAME}.md").read_text(), desc)
        self.assertEqual(json.loads(stdout.getvalue())["urls"], [url])


class UploadFixTests(UploadScriptChecks, ScriptTestCase):
    script = "upload_fix"
    root_attr = "FIX"
    summary = FIX_SUMMARY

    def setUp(self):
        super().setUp()
        self.lookup = self.enterContext(
            mock.patch.object(self.up, "_pull_requests", return_value=[{"num": 1}])
        )

    def test_main_refuses_bad_arguments_before_writing_or_running(self):
        cases = [([], self.up.USAGE), ([NAME, "extra"], self.up.USAGE)] + [
            ([bad], f"not an owner/name Hub id: {'rmems/' + bad!r}") for bad in BAD_NAMES
        ]
        for argv, message in cases:
            with self.subTest(argv=argv):
                self.assert_refused_without_side_effects(argv, message)
        self.lookup.assert_not_called()

    def test_main_runs_hf_upload_then_the_read_only_lookup(self):
        self.stub_upload(0)
        self.enterContext(mock.patch("sys.stdout", new_callable=io.StringIO))

        self.assertEqual(self.up.main([NAME]), 0)

        message = self.up._commit_message(1)
        self.assertEqual(
            message, "Add the 1 base-round batch omitted by the mistaken supersede rule"
        )
        self.run.assert_called_once_with(
            self.expected_argv(message, self.up.description(FIX_SUMMARY)),
            capture_output=True, text=True, check=False,
        )
        self.lookup.assert_called_once_with(REPO_ID, message)
        result = json.loads((self.tmp / "work" / f"fix-pr-{NAME}.json").read_text())
        self.assertEqual(result["pull_requests"], [{"num": 1}])

    def test_failed_upload_skips_the_lookup_and_returns_its_exit_code(self):
        self.stub_upload(1)
        self.enterContext(mock.patch("sys.stdout", new_callable=io.StringIO))
        self.enterContext(mock.patch("sys.stderr", new_callable=io.StringIO))

        self.assertEqual(self.up.main([NAME]), 1)

        self.lookup.assert_not_called()


# --- shell scripts ------------------------------------------------------------------------


class ShellScriptTests(unittest.TestCase):
    SCRIPTS = (
        SKILL / "upload_prs.sh",
        LAND / "sf_land_child.sh",
        LAND / "sf_wait_green.sh",
        LAND / "sf_stack_status.sh",
    )

    def test_shebang_is_the_first_line(self):
        for script in self.SCRIPTS:
            with self.subTest(script=script.name):
                first = script.read_text(encoding="utf-8").splitlines()[0]
                self.assertEqual(first, "#!/usr/bin/env bash")

    @unittest.skipUnless(shutil.which("bash"), "bash is not installed")
    def test_scripts_parse(self):
        for script in self.SCRIPTS:
            with self.subTest(script=script.name):
                parsed = subprocess.run(
                    ["bash", "-n", str(script)], capture_output=True, text=True, check=False
                )
                self.assertEqual(parsed.returncode, 0, parsed.stderr)


if __name__ == "__main__":
    unittest.main()
