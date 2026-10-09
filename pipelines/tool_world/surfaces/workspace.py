#!/usr/bin/env python3
"""The workspace surface: a virtual file tree, search, anchored edits, declared tests.

Files live in memory, seeded from the pack's ``files/`` members; nothing
touches the host filesystem. ``run_tests`` evaluates a declared suite's cases
against the current tree, so an edit changes the outcome and the outcome is
computed, never scripted. Declared suites and the faults that name this surface
are checked when the environment is built: a malformed suite, or a fault whose
symptom no observation could show, is a coded refusal at load, not a surprise
at run time.
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
_TIMEOUT_FAILURE = "ETIMEDOUT after 30s (environment)"
_CHECK_FIELDS: Mapping[str, tuple[str, ...]] = {
    "file_exists": ("path",),
    "file_contains": ("path", "text"),
    "file_not_contains": ("path", "text"),
    "file_sha256": ("path", "sha256"),
}


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
        for name, spec in self.suites.items():
            _check_suite(name, spec, f"{pack.pack_id}/tests/{name}.json")
        for spec in task.faults:
            if spec.surface == self.NAME:
                self.check_fault(spec)

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
        if fault is not None and fault.spec.kind == FAULT_TRANSIENT:
            target = args.get("path", args.get("suite", ""))
            return error_text(f"EAGAIN temporary failure on {name} {target}; retry")
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
            return (
                f"{path} ({len(text)} chars):\n{head}\n"
                f"[output truncated at {_TRUNCATE_AT} chars; read again with offset]"
            )
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
            spec is None,
            cv.FINDING_PACK_FIELD_INVALID,
            f"suite {suite!r} is not declared by the pack; a tests/{suite}.json member must "
            f"declare a cases list; known: {sorted(self.suites)}",
        )
        failures = []
        for case in spec["cases"]:
            if case["id"] == flaky_case:
                message: str | None = _TIMEOUT_FAILURE
            else:
                message = self._case_failure(case["check"])
            if message is not None:
                failures.append(f"FAIL {case['id']}: {message}")
        passed = len(spec["cases"]) - len(failures)
        return {"passed": passed, "failed": len(failures), "failures": failures}

    def _case_failure(self, check: Mapping[str, Any]) -> str | None:
        text = self.files.get(check["path"])
        if text is None:
            return f"{check['path']} does not exist"
        return _CHECKS[check["kind"]](text, check)

    def state_view(self) -> Any:
        return {"files": dict(sorted(self.files.items())), "test_runs": list(self.test_runs)}


def _contains(text: str, check: Mapping[str, Any]) -> str | None:
    return None if check["text"] in text else f"{check['path']} lacks {check['text']!r}"


def _not_contains(text: str, check: Mapping[str, Any]) -> str | None:
    if check["text"] not in text:
        return None
    return f"{check['path']} still contains {check['text']!r}"


def _sha256_matches(text: str, check: Mapping[str, Any]) -> str | None:
    if sha256_bytes(text.encode("utf-8")) == check["sha256"]:
        return None
    return f"{check['path']} content differs"


_CHECKS = {
    "file_exists": lambda text, check: None,
    "file_contains": _contains,
    "file_not_contains": _not_contains,
    "file_sha256": _sha256_matches,
}


def _check_case(case: Any, where: str) -> str:
    """Refuse a case the suite evaluator could not run; return its id."""
    cv.refuse_when(
        not isinstance(case, Mapping) or not isinstance(case.get("id"), str) or not case["id"],
        cv.FINDING_PACK_FIELD_INVALID,
        f"{where}: a case must be an object with a nonempty string id",
    )
    check = case.get("check")
    cv.refuse_when(
        not isinstance(check, Mapping) or check.get("kind") not in _CHECK_FIELDS,
        cv.FINDING_PACK_FIELD_INVALID,
        f"{where}: case {case['id']!r} needs a check whose kind is one of {list(_CHECK_FIELDS)}",
    )
    fields = _CHECK_FIELDS[check["kind"]]
    cv.refuse_when(
        set(check) != {"kind", *fields} or any(not isinstance(check[key], str) for key in fields),
        cv.FINDING_PACK_FIELD_INVALID,
        f"{where}: a {check['kind']} check carries exactly the string fields {list(fields)}",
    )
    return case["id"]


def _check_suite(name: str, spec: Any, where: str) -> None:
    """Refuse a declared suite at load so ``suite_result`` never meets an unexpected shape."""
    cv.refuse_when(
        not isinstance(spec, Mapping)
        or spec.get("suite") != name
        or not isinstance(spec.get("cases"), list)
        or not spec["cases"],
        cv.FINDING_PACK_FIELD_INVALID,
        f"{where}: a suite must declare suite == {name!r} and a nonempty cases list",
    )
    ids = [_check_case(case, f"{where}.cases[{index}]") for index, case in enumerate(spec["cases"])]
    cv.refuse_when(
        len(set(ids)) != len(ids), cv.FINDING_PACK_FIELD_INVALID, f"{where}: duplicate case ids"
    )


bind_import_twin(__name__)
