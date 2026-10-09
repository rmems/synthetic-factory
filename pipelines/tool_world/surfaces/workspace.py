#!/usr/bin/env python3
"""The workspace surface: a virtual file tree, search, anchored edits, declared tests.

Files live in memory, seeded from the pack's ``files/`` members; nothing
touches the host filesystem. ``run_tests`` evaluates a declared suite's cases
against the current tree (``workspace_suites``), so an edit changes the outcome
and the outcome is computed, never scripted. Declared suites and the faults
that name this surface are checked when the environment is built: a malformed
suite, or a fault whose symptom no observation could show, is a coded refusal
at load, not a surprise at run time.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

from .. import vocabulary as cv
from .._contract import bind_import_twin
from .base import Surface, ToolSpec, error_text
from .workspace_suites import check_suite, evaluate_suite

__all__ = ["WorkspaceSurface"]

FAULT_TRANSIENT = "transient_error"
FAULT_FLAKY_TEST = "flaky_test"
FAULT_TRUNCATED = "truncated_output"
_TRUNCATE_AT = 160
_MAX_MATCHES = 40
_STRING: Mapping[str, Any] = {"type": "string"}


def _schema(
    required: tuple[str, ...], properties: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    """A fresh object schema; no row is shared with the table, so a holder may keep it."""
    return {
        "type": "object",
        "required": list(required),
        "properties": {name: dict(row) for name, row in properties.items()},
        "additionalProperties": False,
    }


# Each tool as (name, description, required, properties, irreversible); ``tools`` binds the surface.
_TOOL_ROWS: tuple[tuple[str, str, tuple[str, ...], Mapping[str, Mapping[str, Any]], bool], ...] = (
    (
        "read_file",
        "Read a file. Optional offset/limit page through long files.",
        ("path",),
        {
            "path": _STRING,
            "offset": {"type": "integer", "minimum": 0},
            "limit": {"type": "integer", "minimum": 1},
        },
        False,
    ),
    (
        "write_file",
        "Create or replace a file with the given content.",
        ("path", "content"),
        {"path": _STRING, "content": _STRING},
        False,
    ),
    (
        "edit_file",
        "Replace the unique occurrence of old with new in a file.",
        ("path", "old", "new"),
        {"path": _STRING, "old": _STRING, "new": _STRING},
        False,
    ),
    (
        "search",
        "Regex search over the tree, optionally under one path.",
        ("pattern",),
        {"pattern": _STRING, "path": _STRING},
        False,
    ),
    ("list_dir", "List the entries under a directory.", (), {"path": _STRING}, False),
    (
        "run_tests",
        "Run a declared test suite against the current tree.",
        ("suite",),
        {"suite": _STRING},
        False,
    ),
    (
        "delete_file",
        "Delete a file. Irreversible: confirm first.",
        ("path",),
        {"path": _STRING},
        True,
    ),
)


# --- the fault firing on one call ------------------------------------------


def _kind_of(fault: Any) -> str | None:
    """The kind of the fault scheduled on this call, or None when none fires."""
    return None if fault is None else fault.spec.kind


def _truncates(fault: Any, limit: Any) -> bool:
    """A truncation fault shows on an unpaged read; paging with a limit is how a reader recovers."""
    return _kind_of(fault) == FAULT_TRUNCATED and limit is None


def _flaky_case(fault: Any) -> str | None:
    """The case a flaky-test fault times out on this run, or None when no such fault fires."""
    return fault.spec.params.get("case") if _kind_of(fault) == FAULT_FLAKY_TEST else None


# --- tree helpers ----------------------------------------------------------


def _parents_of(paths: Iterable[str]) -> set[str]:
    """Every directory on the way to each path, as a real file system would keep them."""
    parents: set[str] = set()
    for path in paths:
        parts = path.split("/")[:-1]
        parents.update("/".join(parts[: depth + 1]) for depth in range(len(parts)))
    return parents


def _child_entry(rest: str) -> str:
    """The first segment of a path relative to a directory, with a slash when more follows."""
    head, slash, _tail = rest.partition("/")
    return head + slash


def _missing(name: str, entries: set[str], dirs: set[str]) -> bool:
    """A named directory with no entries that no write ever created; the root always exists."""
    if not name or entries:
        return False
    return name not in dirs


def _grep(pattern: re.Pattern[str], path: str, text: str) -> list[str]:
    """``path:line: text`` for every line the pattern matches, in file order."""
    return [
        f"{path}:{number}: {line}"
        for number, line in enumerate(text.splitlines(), 1)
        if pattern.search(line)
    ]


def _match_report(matches: list[str]) -> str:
    """The first ``_MAX_MATCHES`` hits, with a count of what the cap hid."""
    shown = matches[:_MAX_MATCHES]
    hidden = len(matches) - len(shown)
    tail = f"\n[{hidden} more matches]" if hidden else ""
    return f"{len(matches)} matches:\n" + "\n".join(shown) + tail


class WorkspaceSurface(Surface):
    NAME = cv.SURFACE_WORKSPACE
    FAULT_KINDS = frozenset({FAULT_TRANSIENT, FAULT_FLAKY_TEST, FAULT_TRUNCATED})

    def __init__(self, pack: Any, task: Any, env: Any) -> None:
        super().__init__(pack, task, env)
        self.files: dict[str, str] = dict(pack.files)
        self.dirs: set[str] = _parents_of(self.files)
        self.suites: Mapping[str, Any] = pack.tests
        self.test_runs: list[dict[str, Any]] = []
        self.verification_events: list[int] = []
        for name, spec in self.suites.items():
            check_suite(name, spec, f"{pack.pack_id}/tests/{name}.json")
        for spec in task.faults:
            if spec.surface == self.NAME:
                self.check_fault(spec)

    def tools(self) -> tuple[ToolSpec, ...]:
        return tuple(
            ToolSpec(
                name,
                self.NAME,
                description,
                _schema(required, properties),
                irreversible=irreversible,
            )
            for name, description, required, properties, irreversible in _TOOL_ROWS
        )

    # --- declared faults ---------------------------------------------------

    def check_fault(self, spec: Any) -> None:
        """Refuse a fault whose symptom no observation of this surface could show."""
        self.check_fault_kind(spec.kind)
        registered = {tool.name for tool in self.tools()}
        cv.refuse_when(
            spec.tool not in registered,
            cv.FINDING_FAULT_UNKNOWN,
            f"fault {spec.fault_id} names tool {spec.tool!r}, which the {self.NAME} surface "
            f"does not register; known: {sorted(registered)}",
        )
        cv.refuse_when(
            spec.kind == FAULT_TRUNCATED and spec.tool != "read_file",
            cv.FINDING_FAULT_UNKNOWN,
            f"fault {spec.fault_id}: {FAULT_TRUNCATED} only shows on read_file",
        )
        if spec.kind == FAULT_FLAKY_TEST:
            self._check_flaky_fault(spec)

    def _check_flaky_fault(self, spec: Any) -> None:
        cv.refuse_when(
            spec.tool != "run_tests",
            cv.FINDING_FAULT_UNKNOWN,
            f"fault {spec.fault_id}: {FAULT_FLAKY_TEST} only shows on run_tests",
        )
        case = spec.params.get("case")
        cv.refuse_when(
            not isinstance(case, str),
            cv.FINDING_FAULT_UNKNOWN,
            f"fault {spec.fault_id}: {FAULT_FLAKY_TEST} needs params.case naming a case id",
        )
        picked = spec.selector.get("suite")
        cv.refuse_when(
            picked is not None and (not isinstance(picked, str) or picked not in self.suites),
            cv.FINDING_FAULT_UNKNOWN,
            f"fault {spec.fault_id}: selector names suite {picked!r}, which the pack does not "
            f"declare; known: {sorted(self.suites)}",
        )
        suites = sorted(self.suites) if picked is None else [picked]
        lacking = [name for name in suites if case not in self._case_ids(name)]
        cv.refuse_when(
            bool(lacking),
            cv.FINDING_FAULT_UNKNOWN,
            f"fault {spec.fault_id}: case {case!r} is not in suite(s) {lacking}, so the "
            "fault could fire without a symptom",
        )

    def _case_ids(self, suite: str) -> list[str]:
        return [case["id"] for case in self.suites[suite]["cases"]]

    # --- execution -----------------------------------------------------------

    def execute(self, name: str, args: Mapping[str, Any], fault: Any) -> str:
        if _kind_of(fault) == FAULT_TRANSIENT:
            target = args.get("path", args.get("suite", ""))
            return error_text(f"EAGAIN temporary failure on {name} {target}; retry")
        handlers = {
            "read_file": lambda: self._read_file(args, fault),
            "write_file": lambda: self._write_file(args),
            "edit_file": lambda: self._edit_file(args),
            "search": lambda: self._search(args),
            "list_dir": lambda: self._list_dir(args),
            "run_tests": lambda: self._run_tests(args, fault),
            "delete_file": lambda: self._delete_file(args),
        }
        return handlers[name]()

    def _read_file(self, args: Mapping[str, Any], fault: Any) -> str:
        path = args["path"]
        if path not in self.files:
            return error_text(f"ENOENT no such file: {path}")
        self.verification_events.append(len(self.env.events) + 1)
        text = self.files[path]
        offset, limit = args.get("offset", 0), args.get("limit")
        if _truncates(fault, limit):
            head = text[:_TRUNCATE_AT]
            return (
                f"{path} ({len(text)} chars):\n{head}\n"
                f"[output truncated at {_TRUNCATE_AT} chars; read again with offset]"
            )
        window = text[offset:] if limit is None else text[offset : offset + limit]
        return f"{path} ({len(text)} chars, offset {offset}):\n{window}"

    def _write_file(self, args: Mapping[str, Any]) -> str:
        self.files[args["path"]] = args["content"]
        self.dirs |= _parents_of((args["path"],))
        return f"wrote {args['path']} ({len(args['content'])} chars)"

    def _edit_file(self, args: Mapping[str, Any]) -> str:
        path = args["path"]
        if path not in self.files:
            return error_text(f"ENOENT no such file: {path}")
        count = self.files[path].count(args["old"])
        if count == 0:
            return error_text(
                f"anchor not found in {path}; read the current content before editing"
            )
        if count > 1:
            return error_text(f"anchor is ambiguous in {path} ({count} occurrences); widen it")
        self.files[path] = self.files[path].replace(args["old"], args["new"], 1)
        return (
            f"edited {path}: replaced 1 occurrence ({len(args['old'])} -> {len(args['new'])} chars)"
        )

    def _search(self, args: Mapping[str, Any]) -> str:
        try:
            pattern = re.compile(args["pattern"])
        except re.error as exc:
            return error_text(f"invalid regex: {exc}")
        prefix = args.get("path", "")
        matches: list[str] = []
        for path in sorted(self.files):
            if path.startswith(prefix):
                matches.extend(_grep(pattern, path, self.files[path]))
        if not matches:
            return f"no matches for {args['pattern']!r}"
        return _match_report(matches)

    def _list_dir(self, args: Mapping[str, Any]) -> str:
        """Entries of a directory; one that exists but is empty lists as empty, not ENOENT."""
        name = args.get("path", "").rstrip("/")
        prefix = f"{name}/" if name else ""
        entries = self._entries_under(prefix)
        if _missing(name, entries, self.dirs):
            return error_text(f"ENOENT no such directory: {prefix}")
        return f"{prefix or '.'}:\n" + ("\n".join(sorted(entries)) or "(empty)")

    def _entries_under(self, prefix: str) -> set[str]:
        """Immediate children of ``prefix``; subdirectories carry a trailing slash."""
        below = (path[len(prefix) :] for path in self.files if path.startswith(prefix))
        return {_child_entry(rest) for rest in below}

    def _run_tests(self, args: Mapping[str, Any], fault: Any) -> str:
        suite = args["suite"]
        if suite not in self.suites:
            return error_text(f"unknown suite {suite!r}; declared: {sorted(self.suites)}")
        self.verification_events.append(len(self.env.events) + 1)
        result = self.suite_result(suite, flaky_case=_flaky_case(fault))
        self.test_runs.append({"suite": suite, "failed": result["failed"]})
        lines = [f"{suite}: {result['passed']} passed, {result['failed']} failed"]
        lines.extend(result["failures"])
        return "\n".join(lines)

    def _delete_file(self, args: Mapping[str, Any]) -> str:
        path = args["path"]
        if path not in self.files:
            return error_text(f"ENOENT no such file: {path}")
        del self.files[path]
        return f"deleted {path}"

    # --- declared suites ---------------------------------------------------

    def suite_result(self, suite: str, flaky_case: str | None = None) -> dict[str, Any]:
        """Evaluate every case of a declared suite against the current tree."""
        spec = self.suites.get(suite)
        cv.refuse_when(
            spec is None,
            cv.FINDING_PACK_FIELD_INVALID,
            f"suite {suite!r} is not declared by the pack; a tests/{suite}.json member must "
            f"declare a cases list; known: {sorted(self.suites)}",
        )
        return evaluate_suite(self.files, spec, flaky_case)

    def state_view(self) -> Any:
        return {
            "files": dict(sorted(self.files.items())),
            "dirs": sorted(self.dirs),
            "test_runs": list(self.test_runs),
        }


bind_import_twin(__name__)
