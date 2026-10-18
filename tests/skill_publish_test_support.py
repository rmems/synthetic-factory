"""Shared fixtures for the publish-hub-research-run harness tests.

The harness scripts are not a package: each is loaded by path with importlib under
a temporary ``$HOME`` holding the work files they read at import, once per process.
pyarrow is not a CI dependency, so a stand-in decodes the viewer parquet with the
repo's own reader. Used by test_skill_publish_bundles.py, test_skill_publish_fix.py,
test_skill_publish_upload.py and test_skill_scripts_runtime.py; not named
``test_*`` so it is not itself collected.
"""

import atexit
import contextlib
import functools
import importlib
import importlib.util
import json
import os
import shutil
import sys
import tempfile
import types
from pathlib import Path
from typing import NamedTuple
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
SCRIPT_NAMES = ("build_bundles", "build_fix", "upload_pr", "upload_fix")


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
        self._by_name = {f.name: f for f in self._fields}

    def __iter__(self):
        return iter(self._fields)

    def field(self, name):
        return self._by_name[name]


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


def write_work_files(home: Path) -> None:
    """The work files the scripts read at import, under a scratch ``$HOME``."""
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


class LoadedScripts(NamedTuple):
    home: tempfile.TemporaryDirectory
    modules: dict


@functools.cache
def loaded_scripts() -> LoadedScripts:
    """Load the four scripts once per process under a scratch ``$HOME`` removed at exit."""
    home = tempfile.TemporaryDirectory(prefix="skill-publish-home-")
    atexit.register(home.cleanup)
    write_work_files(Path(home.name))
    return LoadedScripts(home, {name: _load(name, Path(home.name)) for name in SCRIPT_NAMES})


def script(name: str) -> types.ModuleType:
    return loaded_scripts().modules[name]


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


def viewer_rows(*lines, source_file="data/raw/batch-r01.jsonl"):
    row = export_viewer.ViewerRow
    return [
        row(source_file=source_file, source_line=n, record_json=line)
        for n, line in enumerate(lines or ('{"id": "a"}',), 1)
    ]


class ScriptChecks:
    """setUp and helpers shared by the harness test cases; mixed into unittest.TestCase."""

    def setUp(self):
        super().setUp()
        self.tmp = Path(self.enterContext(tempfile.TemporaryDirectory()))

    def assert_refuses(self, error, message, call, *args):
        with self.assertRaises(error) as caught:
            call(*args)
        self.assertEqual(str(caught.exception), message)

    def write_source_tree(self) -> Path:
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

    def write_bundle_inputs(self, source: Path) -> Path:
        """The old-rule run selection (r01, r02c, notes) and the Fable sibling's sidecars."""
        run_dir = self.tmp / "run" / FACTORY
        run_dir.mkdir(parents=True)
        for name in ("batch-r01.jsonl", "batch-r02c.jsonl", "NOTES-r01.md"):
            shutil.copyfile(source / name, run_dir / name)
        sibling = self.tmp / "siblings" / SIBLING_NAME
        sibling.mkdir(parents=True)
        (sibling / "release-status.json").write_text(json.dumps(dict.fromkeys(STATUS_KEYS, "x")))
        (sibling / "provenance.json").write_text(json.dumps({"raw_evidence_policy": "fixture"}))
        return run_dir

    def bundle_roots(self) -> dict:
        return {
            "SOURCE": self.tmp / "source",
            "RUN": self.tmp / "run",
            "BUNDLES": self.tmp / "bundles",
            "SIBLINGS": self.tmp / "siblings",
        }


def assert_viewer_defects_refused(case, module, error, *, local_import):
    """Drive _verify_viewer_parquet through each of its seven refusals."""
    rows = viewer_rows('{"id": "a"}', '{"id": "b"}')
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
        with case.subTest(message=message), _pyarrow_patch(module, local_import, defect):
            case.assert_refuses(
                error, message, module._verify_viewer_parquet, parquet, expected_rows
            )
    with _pyarrow_patch(module, local_import, {}):
        module._verify_viewer_parquet(parquet, rows)  # a faithful projection passes


def _pyarrow_patch(module, local_import, defect):
    package, parquet_module = fake_pyarrow(**defect)
    if local_import:  # build_bundles imports pyarrow.parquet inside the check
        return installed_pyarrow(package, parquet_module)
    return mock.patch.object(module, "pq", parquet_module)


def assert_stamp_defects_refused(case, check, error):
    """Drive _check_record_stamps through each of its three refusals."""
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
            case.assert_refuses(error, message, check, [record("a"), bad], FACTORY)
