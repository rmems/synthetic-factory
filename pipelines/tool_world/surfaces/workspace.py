#!/usr/bin/env python3
"""The workspace surface: a virtual file tree, search, anchored edits, declared tests.

Files live in memory, seeded from the pack's ``files/`` members; nothing
touches the host filesystem. ``run_tests`` evaluates a declared suite's cases
against the current tree, so an edit changes the outcome and the outcome is
computed, never scripted.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from .. import vocabulary as cv
from .._contract import bind_import_twin, sha256_bytes
from .base import Surface, ToolSpec, error_text

__all__ = ["WorkspaceSurface"]

FAULT_TRANSIENT = "transient_error"
FAULT_FLAKY_TEST = "flaky_test"
FAULT_TRUNCATED = "truncated_output"
_TRUNCATE_AT = 160
_MAX_MATCHES = 40


def _string(name: str, description: str = "") -> dict[str, Any]:
    row: dict[str, Any] = {"type": "string"}
    if description:
        row["description"] = description
    return row


def _schema(required: tuple[str, ...], properties: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "type": "object",
        "required": list(required),
        "properties": dict(properties),
        "additionalProperties": False,
    }


class WorkspaceSurface(Surface):
    NAME = cv.SURFACE_WORKSPACE
    FAULT_KINDS = frozenset({FAULT_TRANSIENT, FAULT_FLAKY_TEST, FAULT_TRUNCATED})

    def __init__(self, pack: Any, task: Any, env: Any) -> None:
        super().__init__(pack, task, env)
        self.files: dict[str, str] = dict(pack.files)
        self.suites: Mapping[str, Any] = pack.tests
        self.test_runs: list[dict[str, Any]] = []
        self.verification_events: list[int] = []

    def tools(self) -> tuple[ToolSpec, ...]:
        return (
            ToolSpec(
                "read_file",
                self.NAME,
                "Read a file. Optional offset/limit page through long files.",
                _schema(
                    ("path",),
                    {
                        "path": _string("path"),
                        "offset": {"type": "integer", "minimum": 0},
                        "limit": {"type": "integer", "minimum": 1},
                    },
                ),
            ),
            ToolSpec(
                "write_file",
                self.NAME,
                "Create or replace a file with the given content.",
                _schema(
                    ("path", "content"), {"path": _string("path"), "content": _string("content")}
                ),
            ),
            ToolSpec(
                "edit_file",
                self.NAME,
                "Replace the unique occurrence of old with new in a file.",
                _schema(
                    ("path", "old", "new"),
                    {"path": _string("path"), "old": _string("old"), "new": _string("new")},
                ),
            ),
            ToolSpec(
                "search",
                self.NAME,
                "Regex search over the tree, optionally under one path.",
                _schema(("pattern",), {"pattern": _string("pattern"), "path": _string("path")}),
            ),
            ToolSpec(
                "list_dir",
                self.NAME,
                "List the entries under a directory.",
                _schema((), {"path": _string("path")}),
            ),
            ToolSpec(
                "run_tests",
                self.NAME,
                "Run a declared test suite against the current tree.",
                _schema(("suite",), {"suite": _string("suite")}),
            ),
            ToolSpec(
                "delete_file",
                self.NAME,
                "Delete a file. Irreversible: confirm first.",
                _schema(("path",), {"path": _string("path")}),
                irreversible=True,
            ),
        )

    # --- execution -----------------------------------------------------------

    def execute(self, name: str, args: Mapping[str, Any], fault: Any) -> str:
        if fault is not None and fault.spec.kind == FAULT_TRANSIENT:
            return error_text(
                f"EAGAIN temporary failure on {name} {args.get('path', args.get('suite', ''))}; retry"
            )
        handler = getattr(self, f"_{name}")
        return handler(args, fault)

    def _read_file(self, args: Mapping[str, Any], fault: Any) -> str:
        path = args["path"]
        if path not in self.files:
            return error_text(f"ENOENT no such file: {path}")
        self.verification_events.append(len(self.env.events) + 1)
        text = self.files[path]
        offset, limit = args.get("offset", 0), args.get("limit")
        if fault is not None and fault.spec.kind == FAULT_TRUNCATED and limit is None:
            head = text[:_TRUNCATE_AT]
            return f"{path} ({len(text)} chars):\n{head}\n[output truncated at {_TRUNCATE_AT} chars; read again with offset]"
        window = text[offset:] if limit is None else text[offset : offset + limit]
        return f"{path} ({len(text)} chars, offset {offset}):\n{window}"

    def _write_file(self, args: Mapping[str, Any], fault: Any) -> str:
        self.files[args["path"]] = args["content"]
        return f"wrote {args['path']} ({len(args['content'])} chars)"

    def _edit_file(self, args: Mapping[str, Any], fault: Any) -> str:
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

    def _search(self, args: Mapping[str, Any], fault: Any) -> str:
        try:
            pattern = re.compile(args["pattern"])
        except re.error as exc:
            return error_text(f"invalid regex: {exc}")
        prefix = args.get("path", "")
        matches = []
        for path in sorted(self.files):
            if not path.startswith(prefix):
                continue
            for number, line in enumerate(self.files[path].splitlines(), 1):
                if pattern.search(line):
                    matches.append(f"{path}:{number}: {line}")
        if not matches:
            return f"no matches for {args['pattern']!r}"
        shown = matches[:_MAX_MATCHES]
        tail = (
            ""
            if len(matches) <= _MAX_MATCHES
            else f"\n[{len(matches) - _MAX_MATCHES} more matches]"
        )
        return f"{len(matches)} matches:\n" + "\n".join(shown) + tail

    def _list_dir(self, args: Mapping[str, Any], fault: Any) -> str:
        prefix = args.get("path", "").rstrip("/")
        prefix = f"{prefix}/" if prefix else ""
        entries = set()
        for path in self.files:
            if path.startswith(prefix):
                rest = path[len(prefix) :]
                entries.add(rest.split("/", 1)[0] + ("/" if "/" in rest else ""))
        if not entries:
            return error_text(f"ENOENT no such directory: {prefix or '.'}")
        return f"{prefix or '.'}:\n" + "\n".join(sorted(entries))

    def _run_tests(self, args: Mapping[str, Any], fault: Any) -> str:
        suite = args["suite"]
        if suite not in self.suites:
            return error_text(f"unknown suite {suite!r}; declared: {sorted(self.suites)}")
        self.verification_events.append(len(self.env.events) + 1)
        flaky = (
            fault.spec.params.get("case")
            if fault is not None and fault.spec.kind == FAULT_FLAKY_TEST
            else None
        )
        result = self.suite_result(suite, flaky_case=flaky)
        self.test_runs.append({"suite": suite, "failed": result["failed"]})
        lines = [f"{suite}: {result['passed']} passed, {result['failed']} failed"]
        lines.extend(result["failures"])
        return "\n".join(lines)

    def _delete_file(self, args: Mapping[str, Any], fault: Any) -> str:
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
            not isinstance(spec, Mapping) or not isinstance(spec.get("cases"), list),
            cv.FINDING_PACK_FIELD_INVALID,
            f"suite {suite!r} must declare a cases list",
        )
        failures = []
        for case in spec["cases"]:
            case_id = case.get("id", "?")
            if case_id == flaky_case:
                failures.append(f"FAIL {case_id}: ETIMEDOUT after 30s (environment)")
                continue
            message = self._case_failure(case)
            if message is not None:
                failures.append(f"FAIL {case_id}: {message}")
        passed = len(spec["cases"]) - len(failures)
        return {"passed": passed, "failed": len(failures), "failures": failures}

    def _case_failure(self, case: Mapping[str, Any]) -> str | None:
        check = case.get("check") or {}
        kind, path = check.get("kind"), check.get("path", "")
        text = self.files.get(path)
        if kind == "file_exists":
            return None if text is not None else f"{path} does not exist"
        if text is None:
            return f"{path} does not exist"
        if kind == "file_contains":
            return None if check.get("text", "") in text else f"{path} lacks {check.get('text')!r}"
        if kind == "file_not_contains":
            return (
                None
                if check.get("text", "") not in text
                else f"{path} still contains {check.get('text')!r}"
            )
        if kind == "file_sha256":
            return (
                None
                if sha256_bytes(text.encode("utf-8")) == check.get("sha256")
                else f"{path} content differs"
            )
        cv.refuse(cv.FINDING_PACK_FIELD_INVALID, f"unknown test check kind {kind!r}")

    def state_view(self) -> Any:
        return {"files": dict(sorted(self.files.items())), "test_runs": list(self.test_runs)}


bind_import_twin(__name__)
