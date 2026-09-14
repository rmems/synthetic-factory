#!/usr/bin/env python3
"""Forensically recover Grok-created temporary Python sources without executing them.

All session content is untrusted input.  This program only parses JSON/text,
materializes recorded source strings inside RECOVERY_ROOT, and performs static
AST inspection.  It never imports, executes, or invokes recovered modules.
"""

from __future__ import annotations

import argparse
import ast
import dataclasses
import datetime as dt
import fnmatch
import hashlib
import io
import json
import os
import re
import shlex
import stat
import tokenize
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, Sequence


PARENT_SESSION_ID = "01a06111-1b84-7250-aec4-9d120db6c1a4"
SESSION_BASE = Path(
    "/home/raulmc/.grok/sessions/"
    "%2Fhome%2Fraulmc%2Frmems%2Fsynthetic-factory"
)
RECOVERY_ROOT = Path(__file__).resolve().parent.parent
EXPECTED_WORKTREE = Path(
    "/home/raulmc/.codex/recovery-worktrees/"
    "synthetic-factory-grok-01a06111"
)
ACTIVE_CHECKOUT = Path("/home/raulmc/rmems/synthetic-factory")
RECOVERY_BRANCH = "codex/recover-grok-01a06111"
BASE_COMMIT = "88a150c56210278499d31595f5ab6cea6553f0ac"
SCHEMA_VERSION = "grok-temp-python-recovery-v1"

UUID_LIKE_RE = re.compile(r"^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$")
TMP_PY_RE = re.compile(r"/tmp/[A-Za-z0-9_./*?{}\[\]-]+\.py")
LITERAL_TMP_PY_RE = re.compile(r"^/tmp/[A-Za-z0-9_./-]+\.py$")
JSONL_RE = re.compile(r"(?:/tmp/)?[A-Za-z0-9_./{}*?\[\]-]+\.jsonl")
SECRET_LIKE_NAME_RE = re.compile(
    r"(?i)(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|passwd|secret)"
)

STRUCTURED_TOOLS = {
    "write",
    "write_file",
    "search_replace",
    "edit",
    "edit_file",
    "apply_patch",
}


class RecoveryError(RuntimeError):
    """Raised when a recovery invariant fails closed."""


@dataclasses.dataclass(frozen=True)
class SessionNode:
    session_id: str
    parent_session_id: str | None
    depth: int
    status: str
    metadata_path: str | None
    metadata: Mapping[str, Any]


@dataclasses.dataclass
class ToolCall:
    session_id: str
    journal_path: str
    journal_line: int
    tool_call_id: str
    tool_name: str
    title: str
    timestamp_epoch: int | float | None
    timestamp_ms: int | None
    event_id: str | None
    raw_input: Mapping[str, Any]
    status: str | None = None
    exit_code: int | None = None
    result_error: bool = False
    result_content_summary: list[Mapping[str, Any]] = dataclasses.field(default_factory=list)
    raw_output_sha256: str | None = None
    raw_output_bytes: int | None = None
    raw_output_count_evidence: list[Mapping[str, Any]] = dataclasses.field(
        default_factory=list
    )

    @property
    def timestamp_utc(self) -> str | None:
        if self.timestamp_ms is not None:
            value = self.timestamp_ms / 1000
        elif isinstance(self.timestamp_epoch, (int, float)):
            value = float(self.timestamp_epoch)
        else:
            return None
        return (
            dt.datetime.fromtimestamp(value, tz=dt.timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z")
        )

    @property
    def order_key(self) -> tuple[int, str, int, str]:
        if self.timestamp_ms is not None:
            millis = self.timestamp_ms
        elif isinstance(self.timestamp_epoch, (int, float)):
            millis = int(float(self.timestamp_epoch) * 1000)
        else:
            millis = 0
        return (millis, self.session_id, self.journal_line, self.tool_call_id)

    @property
    def completed(self) -> bool:
        return self.status == "Completed" and not self.result_error

    @property
    def command_succeeded(self) -> bool:
        return self.completed and self.exit_code == 0


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_recovery_boundary() -> None:
    worktree = EXPECTED_WORKTREE.resolve()
    recovery = RECOVERY_ROOT.resolve()
    try:
        recovery.relative_to(worktree)
    except ValueError as exc:
        raise RecoveryError(
            f"recovery root {recovery} is outside isolated worktree {worktree}"
        ) from exc
    if recovery == worktree:
        raise RecoveryError("recovery root may not be the worktree root")
    if str(recovery).startswith("/tmp/") or recovery == Path("/tmp"):
        raise RecoveryError("recovery root may not be under /tmp")
    if not SESSION_BASE.is_dir():
        raise RecoveryError(f"session base is missing: {SESSION_BASE}")


def fresh_directory(path: Path) -> None:
    if path.exists():
        raise RecoveryError(f"refusing existing output directory: {path}")
    path.mkdir(parents=True, mode=0o700)


def write_text_fresh(path: Path, text: str, *, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open("x", encoding="utf-8", newline="") as handle:
        handle.write(text)
    path.chmod(mode)


def write_bytes_fresh(path: Path, value: bytes, *, mode: int = 0o400) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open("xb") as handle:
        handle.write(value)
    path.chmod(mode)


def write_json_fresh(path: Path, value: Any, *, mode: int = 0o600) -> None:
    write_text_fresh(
        path,
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        mode=mode,
    )


def write_jsonl_fresh(
    path: Path,
    values: Iterable[Mapping[str, Any]],
    *,
    mode: int = 0o600,
) -> int:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    count = 0
    with path.open("x", encoding="utf-8", newline="") as handle:
        for value in values:
            handle.write(
                json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            )
            handle.write("\n")
            count += 1
    path.chmod(mode)
    return count


def replace_json(path: Path, value: Any, *, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_name(path.name + ".new")
    if temporary.exists():
        raise RecoveryError(f"refusing stale temporary output: {temporary}")
    with temporary.open("x", encoding="utf-8", newline="") as handle:
        json.dump(value, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write("\n")
    temporary.chmod(mode)
    temporary.replace(path)


def replace_text(path: Path, value: str, *, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_name(path.name + ".new")
    if temporary.exists():
        raise RecoveryError(f"refusing stale temporary output: {temporary}")
    with temporary.open("x", encoding="utf-8", newline="") as handle:
        handle.write(value)
    temporary.chmod(mode)
    temporary.replace(path)


def replace_jsonl(
    path: Path,
    values: Iterable[Mapping[str, Any]],
    *,
    mode: int = 0o600,
) -> int:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = path.with_name(path.name + ".new")
    if temporary.exists():
        raise RecoveryError(f"refusing stale temporary output: {temporary}")
    count = 0
    with temporary.open("x", encoding="utf-8", newline="") as handle:
        for value in values:
            handle.write(
                json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            )
            handle.write("\n")
            count += 1
    temporary.chmod(mode)
    temporary.replace(path)
    return count


def read_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> Iterator[Mapping[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RecoveryError(f"invalid JSONL at {path}:{line_number}: {exc}") from exc
            if not isinstance(value, dict):
                raise RecoveryError(
                    f"expected JSON object at {path}:{line_number}, got {type(value).__name__}"
                )
            yield value


def safe_child_id(value: Any, fallback: str) -> str:
    candidate = value if isinstance(value, str) else fallback
    if not UUID_LIKE_RE.fullmatch(candidate):
        raise RecoveryError(f"invalid child session id in journal metadata: {candidate!r}")
    return candidate


def discover_session_graph() -> tuple[list[SessionNode], list[Mapping[str, Any]]]:
    queue: deque[tuple[str, str | None, int, str | None, Mapping[str, Any]]] = deque(
        [(PARENT_SESSION_ID, None, 0, None, {})]
    )
    nodes: list[SessionNode] = []
    edges: list[Mapping[str, Any]] = []
    seen: set[str] = set()

    while queue:
        session_id, parent_id, depth, metadata_path, metadata = queue.popleft()
        if session_id in seen:
            continue
        seen.add(session_id)
        session_dir = SESSION_BASE / session_id
        if not session_dir.is_dir():
            raise RecoveryError(f"declared session directory is missing: {session_dir}")
        status = "top_level" if depth == 0 else str(metadata.get("status", "unknown"))
        nodes.append(
            SessionNode(
                session_id=session_id,
                parent_session_id=parent_id,
                depth=depth,
                status=status,
                metadata_path=metadata_path,
                metadata=metadata,
            )
        )
        subagent_root = session_dir / "subagents"
        if not subagent_root.is_dir():
            continue
        for meta_path in sorted(subagent_root.glob("*/meta.json")):
            child_meta = read_json(meta_path)
            if not isinstance(child_meta, dict):
                raise RecoveryError(f"subagent metadata is not an object: {meta_path}")
            child_id = safe_child_id(
                child_meta.get("child_session_id") or child_meta.get("subagent_id"),
                meta_path.parent.name,
            )
            declared_parent = child_meta.get("parent_session_id")
            if declared_parent not in (None, session_id):
                raise RecoveryError(
                    f"parent mismatch for {child_id}: {declared_parent!r} != {session_id!r}"
                )
            edge = {
                "parent_session_id": session_id,
                "child_session_id": child_id,
                "metadata_path": str(meta_path),
                "status": child_meta.get("status"),
                "description": child_meta.get("description"),
                "subagent_type": child_meta.get("subagent_type"),
                "started_at": child_meta.get("started_at"),
                "completed_at": child_meta.get("completed_at"),
                "duration_ms": child_meta.get("duration_ms"),
                "tool_calls": child_meta.get("tool_calls"),
                "turns": child_meta.get("turns"),
                "child_cwd": child_meta.get("child_cwd"),
                "effective_model_id": child_meta.get("effective_model_id"),
                "prompt_sha256": sha256_text(str(child_meta.get("prompt", ""))),
                "prompt_bytes": len(str(child_meta.get("prompt", "")).encode("utf-8")),
            }
            edges.append(edge)
            queue.append((child_id, session_id, depth + 1, str(meta_path), child_meta))

    nodes.sort(key=lambda node: (node.depth, node.session_id))
    edges.sort(key=lambda edge: (str(edge["parent_session_id"]), str(edge["child_session_id"])))
    return nodes, edges


def iter_evidence_paths(nodes: Sequence[SessionNode]) -> Iterator[Mapping[str, Any]]:
    for node in nodes:
        session_dir = SESSION_BASE / node.session_id
        for dirpath, dirnames, filenames in os.walk(session_dir, followlinks=False):
            dirnames.sort()
            filenames.sort()
            directory = Path(dirpath)
            for filename in filenames:
                path = directory / filename
                info = path.lstat()
                common = {
                    "session_id": node.session_id,
                    "session_depth": node.depth,
                    "path": str(path),
                    "path_relative_to_session_base": str(path.relative_to(SESSION_BASE)),
                    "size": info.st_size,
                    "mode": stat.S_IMODE(info.st_mode),
                    "mtime_ns": info.st_mtime_ns,
                }
                if stat.S_ISREG(info.st_mode):
                    yield {**common, "type": "regular", "sha256": sha256_file(path)}
                elif stat.S_ISLNK(info.st_mode):
                    yield {
                        **common,
                        "type": "symlink_not_followed",
                        "link_target": os.readlink(path),
                        "sha256": None,
                    }
                else:
                    yield {**common, "type": "other_not_read", "sha256": None}


def summarize_diff_content(content: Any) -> list[Mapping[str, Any]]:
    if not isinstance(content, list):
        return []
    summary: list[Mapping[str, Any]] = []
    for item in content:
        if not isinstance(item, dict):
            continue
        old_text = item.get("oldText")
        new_text = item.get("newText")
        summary.append(
            {
                "type": item.get("type"),
                "path": item.get("path"),
                "old_text_bytes": (
                    len(old_text.encode("utf-8")) if isinstance(old_text, str) else None
                ),
                "old_text_sha256": sha256_text(old_text) if isinstance(old_text, str) else None,
                "new_text_bytes": (
                    len(new_text.encode("utf-8")) if isinstance(new_text, str) else None
                ),
                "new_text_sha256": sha256_text(new_text) if isinstance(new_text, str) else None,
                "new_line": item.get("new_line"),
            }
        )
    return summary


def raw_output_text(raw_output: Any) -> tuple[str | None, bool | None]:
    """Decode recorded terminal output bytes without interpreting or executing them."""

    if not isinstance(raw_output, dict):
        return None, None
    output = raw_output.get("output")
    if isinstance(output, str):
        return output, bool(raw_output.get("truncated"))
    if isinstance(output, list) and all(
        isinstance(value, int) and 0 <= value <= 255 for value in output
    ):
        return bytes(output).decode("utf-8", errors="replace"), bool(
            raw_output.get("truncated")
        )
    prompt_output = raw_output.get("output_for_prompt")
    if isinstance(prompt_output, str):
        return prompt_output, bool(raw_output.get("truncated"))
    if isinstance(prompt_output, list) and all(
        isinstance(value, int) and 0 <= value <= 255 for value in prompt_output
    ):
        return bytes(prompt_output).decode("utf-8", errors="replace"), bool(
            raw_output.get("truncated")
        )
    return None, bool(raw_output.get("truncated"))


def recorded_output_count_evidence(
    raw_output: Any, command: str | None = None
) -> list[Mapping[str, Any]]:
    """Extract tightly-scoped line-count claims from inert terminal output."""

    text, truncated = raw_output_text(raw_output)
    if text is None:
        return []
    # Strip ANSI control sequences so anchored count lines remain parseable.
    cleaned = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", text)
    wc_targets: set[str] = set()
    if isinstance(command, str):
        for segment in re.split(r"[;|\n]", command):
            if re.search(r"\bwc\b", segment) and re.search(
                r"(?:^|\s)(?:-[A-Za-z]*l[A-Za-z]*|--lines)(?:\s|$)", segment
            ):
                wc_targets.update(jsonl_expressions(segment))
    patterns = [
        (
            "journal_terminal_wrote_count",
            re.compile(
                r"(?im)\bwrote\s+(\d+)\s+(?:records?|lines?|pairs?|artifacts?)"
                r"(?:\s+(?:to|into)\s+['\"]?([^'\"\s]+\.jsonl))?"
            ),
        ),
        (
            "journal_terminal_labeled_count",
            re.compile(r"(?im)^\s*(?:records?|lines?|count)\s*[:=]\s*(\d+)\s*$"),
        ),
    ]
    if wc_targets:
        patterns.insert(
            0,
            (
                "journal_terminal_wc_l",
                re.compile(r"(?m)^\s*(\d+)\s+((?:/[^\s]+|[^\s]+)\.jsonl)\s*$"),
            ),
        )
    evidence: list[Mapping[str, Any]] = []
    for rule_id, pattern in patterns:
        for match in pattern.finditer(cleaned):
            output_jsonl = (
                match.group(2)
                if match.lastindex and match.lastindex >= 2
                else None
            )
            if rule_id == "journal_terminal_wc_l" and output_jsonl is not None:
                if not any(
                    output_jsonl == target
                    or fnmatch.fnmatch(output_jsonl, target)
                    or fnmatch.fnmatch(Path(output_jsonl).name, Path(target).name)
                    for target in wc_targets
                ):
                    continue
            evidence.append(
                {
                    "rule_id": rule_id,
                    "count": int(match.group(1)),
                    "output_jsonl": output_jsonl,
                    "terminal_output_sha256": sha256_text(text),
                    "terminal_output_bytes": len(text.encode("utf-8")),
                    "terminal_output_truncated": truncated,
                    "evidence_source": "recorded_journal_raw_output",
                }
            )
    unique: dict[tuple[Any, ...], Mapping[str, Any]] = {}
    for item in evidence:
        key = (item["rule_id"], item["count"], item["output_jsonl"])
        unique[key] = item
    return list(unique.values())


def iter_tool_calls(session_id: str) -> Iterator[ToolCall]:
    journal = SESSION_BASE / session_id / "updates.jsonl"
    if not journal.exists():
        return
    calls: dict[str, ToolCall] = {}
    results: dict[str, dict[str, Any]] = defaultdict(dict)
    with journal.open(encoding="utf-8", errors="strict") as handle:
        for line_number, line in enumerate(handle, 1):
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RecoveryError(f"invalid JSON at {journal}:{line_number}: {exc}") from exc
            params = entry.get("params") if isinstance(entry, dict) else None
            if not isinstance(params, dict):
                continue
            update = params.get("update")
            if not isinstance(update, dict):
                continue
            tool_call_id = update.get("toolCallId")
            if not isinstance(tool_call_id, str):
                continue
            update_kind = update.get("sessionUpdate")
            if update_kind == "tool_call":
                tool_meta = (update.get("_meta") or {}).get("x.ai/tool") or {}
                tool_name = tool_meta.get("name") or update.get("title") or "unknown"
                raw_input = update.get("rawInput")
                if not isinstance(raw_input, dict):
                    raw_input = {}
                event_meta = params.get("_meta") or {}
                calls[tool_call_id] = ToolCall(
                    session_id=session_id,
                    journal_path=str(journal),
                    journal_line=line_number,
                    tool_call_id=tool_call_id,
                    tool_name=str(tool_name),
                    title=str(update.get("title") or tool_name),
                    timestamp_epoch=entry.get("timestamp"),
                    timestamp_ms=(
                        event_meta.get("agentTimestampMs")
                        if isinstance(event_meta.get("agentTimestampMs"), int)
                        else None
                    ),
                    event_id=(
                        event_meta.get("eventId")
                        if isinstance(event_meta.get("eventId"), str)
                        else None
                    ),
                    raw_input=raw_input,
                )
            elif update_kind == "tool_call_update":
                result = results[tool_call_id]
                update_params = (params.get("_meta") or {}).get("updateParams") or {}
                status_value = update_params.get("status")
                if isinstance(status_value, str):
                    result["status"] = status_value
                raw_output = update.get("rawOutput")
                if raw_output is not None:
                    serialized = canonical_json_bytes(raw_output)
                    result["raw_output_sha256"] = sha256_bytes(serialized)
                    result["raw_output_bytes"] = len(serialized)
                    current_call = calls.get(tool_call_id)
                    command = (
                        current_call.raw_input.get("command")
                        if current_call is not None
                        else None
                    )
                    count_evidence = recorded_output_count_evidence(
                        raw_output,
                        command if isinstance(command, str) else None,
                    )
                    if count_evidence:
                        result["raw_output_count_evidence"] = count_evidence
                    if isinstance(raw_output, dict) and isinstance(
                        raw_output.get("exit_code"), int
                    ):
                        result["exit_code"] = raw_output["exit_code"]
                if update.get("error") is not None:
                    result["result_error"] = True
                diff_summary = summarize_diff_content(update.get("content"))
                if diff_summary:
                    result["result_content_summary"] = diff_summary

    for tool_call_id, call in calls.items():
        result = results.get(tool_call_id, {})
        call.status = result.get("status")
        call.exit_code = result.get("exit_code")
        call.result_error = bool(result.get("result_error", False))
        call.result_content_summary = list(result.get("result_content_summary", []))
        call.raw_output_sha256 = result.get("raw_output_sha256")
        call.raw_output_bytes = result.get("raw_output_bytes")
        call.raw_output_count_evidence = list(
            result.get("raw_output_count_evidence", [])
        )
        yield call


def target_path_from_structured_call(call: ToolCall) -> str | None:
    for key in ("file_path", "target_file", "path"):
        value = call.raw_input.get(key)
        if isinstance(value, str):
            return value
    return None


def string_field_digest(value: Any) -> Mapping[str, Any] | None:
    if not isinstance(value, str):
        return None
    encoded = value.encode("utf-8")
    return {"bytes": len(encoded), "sha256": sha256_bytes(encoded)}


def literal_tmp_py_paths(text: str) -> list[str]:
    return sorted({match for match in TMP_PY_RE.findall(text) if LITERAL_TMP_PY_RE.fullmatch(match)})


def all_tmp_py_expressions(text: str) -> list[str]:
    return sorted(set(TMP_PY_RE.findall(text)))


def jsonl_expressions(text: str) -> list[str]:
    return sorted(set(JSONL_RE.findall(text)))


def clean_jsonl_candidate(value: Any) -> str | None:
    """Return a conservative path/glob-shaped JSONL expression, else ``None``."""

    if not isinstance(value, str) or not value.endswith(".jsonl"):
        return None
    if len(value) > 512 or value == ".jsonl" or any(character.isspace() for character in value):
        return None
    if "://" in value or value.count("{") != value.count("}"):
        return None
    if value.count("[") != value.count("]"):
        return None
    if not re.fullmatch(r"[A-Za-z0-9_./*?{}\[\]-]+\.jsonl", value):
        return None
    return value


def terminal_log_paths(call: ToolCall) -> list[str]:
    terminal_dir = SESSION_BASE / call.session_id / "terminal"
    if not terminal_dir.is_dir():
        return []
    return [str(path) for path in sorted(terminal_dir.glob(f"{call.tool_call_id}-*.log"))]


def _heredoc_operations(
    command: str, *, include_content: bool = False
) -> list[Mapping[str, Any]]:
    path_pattern = r"(?P<path>/tmp/[A-Za-z0-9_./-]+\.py)"
    patterns = [
        re.compile(
            rf"cat\s*(?P<redir>>>?)\s*['\"]?{path_pattern}['\"]?\s*"
            r"(?P<dash><<-?)\s*(?P<quote>['\"]?)(?P<tag>[A-Za-z0-9_]+)(?P=quote)"
            r"[^\n]*\n(?P<body>.*?)(?:\n(?P=tag)(?=\n|$))",
            re.DOTALL,
        ),
        re.compile(
            r"cat\s*(?P<dash><<-?)\s*(?P<quote>['\"]?)(?P<tag>[A-Za-z0-9_]+)(?P=quote)"
            rf"\s*(?P<redir>>>?)\s*['\"]?{path_pattern}['\"]?"
            r"[^\n]*\n(?P<body>.*?)(?:\n(?P=tag)(?=\n|$))",
            re.DOTALL,
        ),
    ]
    operations: list[Mapping[str, Any]] = []
    occupied: list[tuple[int, int]] = []
    for pattern in patterns:
        for match in pattern.finditer(command):
            span = match.span()
            if any(not (span[1] <= start or span[0] >= end) for start, end in occupied):
                continue
            occupied.append(span)
            body = match.group("body") + "\n"
            quoted = bool(match.group("quote"))
            tab_stripping = match.group("dash") == "<<-"
            if tab_stripping:
                body = "\n".join(line.lstrip("\t") for line in body.split("\n"))
            operation: dict[str, Any] = {
                    "position": span[0],
                    "kind": (
                        "literal_heredoc_append"
                        if match.group("redir") == ">>"
                        else "literal_heredoc_write"
                    ),
                    "target": match.group("path"),
                    "content_sha256": sha256_text(body),
                    "content_bytes": len(body.encode("utf-8")),
                    "quoted_delimiter": quoted,
                    "tab_stripping": tab_stripping,
                    "replayability": "exact" if quoted else "ambiguous_shell_expansion",
                }
            if include_content:
                operation["_content"] = body
            operations.append(operation)
    return operations


def _simple_shell_operations(command: str) -> list[Mapping[str, Any]]:
    literal_path = r"/tmp/[A-Za-z0-9_./-]+\.py"
    operations: list[Mapping[str, Any]] = []

    concat_re = re.compile(
        rf"\bcat\s+(?P<sources>(?:['\"]?{literal_path}['\"]?\s+)+)"
        rf"(?P<redir>>>?)\s*['\"]?(?P<target>{literal_path})['\"]?"
    )
    for match in concat_re.finditer(command):
        sources = re.findall(literal_path, match.group("sources"))
        operations.append(
            {
                "position": match.start(),
                "kind": "concat_append" if match.group("redir") == ">>" else "concat_write",
                "sources": sources,
                "target": match.group("target"),
                "replayability": "exact_if_all_source_states_known",
            }
        )

    copy_move_re = re.compile(
        rf"\b(?P<kind>cp|mv)\s+(?:-[A-Za-z0-9_-]+\s+)*"
        rf"['\"]?(?P<source>{literal_path})['\"]?\s+"
        rf"['\"]?(?P<target>{literal_path})['\"]?"
    )
    for match in copy_move_re.finditer(command):
        operations.append(
            {
                "position": match.start(),
                "kind": "copy" if match.group("kind") == "cp" else "move",
                "source": match.group("source"),
                "target": match.group("target"),
                "replayability": "exact_if_source_state_known",
            }
        )

    remove_re = re.compile(rf"\brm\s+(?:-[A-Za-z0-9_-]+\s+)*(?P<paths>[^\n;]+)")
    for match in remove_re.finditer(command):
        for path in re.findall(literal_path, match.group("paths")):
            operations.append(
                {
                    "position": match.start(),
                    "kind": "delete",
                    "target": path,
                    "replayability": "exact_existence_change",
                }
            )

    sed_re = re.compile(
        rf"\bsed\b[^\n;]*(?:\s-i(?:\s|$)|--in-place)[^\n;]*(?P<target>{literal_path})",
        re.IGNORECASE,
    )
    for match in sed_re.finditer(command):
        operations.append(
            {
                "position": match.start(),
                "kind": "sed_in_place",
                "target": match.group("target"),
                "replayability": "ambiguous_transform_not_replayed",
            }
        )

    perl_re = re.compile(
        rf"\bperl\b[^\n;]*\s-pi(?:\S*)?[^\n;]*(?P<target>{literal_path})",
        re.IGNORECASE,
    )
    for match in perl_re.finditer(command):
        operations.append(
            {
                "position": match.start(),
                "kind": "perl_in_place",
                "target": match.group("target"),
                "replayability": "ambiguous_transform_not_replayed",
            }
        )

    redirect_re = re.compile(rf"(?P<redir>>>|(?<!>)>)\s*['\"]?(?P<target>{literal_path})['\"]?")
    known_redirect_positions = {
        (int(operation["position"]), str(operation.get("target")))
        for operation in operations
        if operation["kind"] in {"concat_write", "concat_append"}
    }
    for match in redirect_re.finditer(command):
        if any(
            target == match.group("target") and abs(position - match.start()) < 512
            for position, target in known_redirect_positions
        ):
            continue
        operations.append(
            {
                "position": match.start(),
                "kind": (
                    "unparsed_redirect_append"
                    if match.group("redir") == ">>"
                    else "unparsed_redirect_write"
                ),
                "target": match.group("target"),
                "replayability": "ambiguous_pipeline_not_replayed",
            }
        )

    return operations


def _python_heredoc_bodies(command: str) -> list[tuple[int, str]]:
    pattern = re.compile(
        r"\bpython(?:3(?:\.\d+)?)?\b[^\n]*?<<-?\s*"
        r"(?P<quote>['\"]?)(?P<tag>[A-Za-z0-9_]+)(?P=quote)[^\n]*\n"
        r"(?P<body>.*?)(?:\n(?P=tag)(?=\n|$))",
        re.DOTALL,
    )
    return [(match.start("body"), match.group("body")) for match in pattern.finditer(command)]


def _static_path_value(node: ast.AST, names: Mapping[str, str]) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        return names.get(node.id)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "Path":
        if len(node.args) == 1:
            return _static_path_value(node.args[0], names)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        left = _static_path_value(node.left, names)
        right = _static_path_value(node.right, names)
        if left is not None and right is not None:
            return str(Path(left) / right)
    return None


def _python_body_write_targets(body: str, base_position: int) -> list[Mapping[str, Any]]:
    try:
        tree = ast.parse(body, mode="exec")
    except SyntaxError:
        candidates = literal_tmp_py_paths(body)
        if not candidates:
            return []
        return [
            {
                "position": base_position,
                "kind": "inline_python_unparsed_mutation",
                "candidate_paths": candidates,
                "target": None,
                "replayability": "ambiguous_dynamic_mutation_not_replayed",
            }
        ]

    names: dict[str, str] = {}
    for statement in tree.body:
        if isinstance(statement, (ast.Assign, ast.AnnAssign)):
            value_node = statement.value
            value = _static_path_value(value_node, names) if value_node is not None else None
            if value is None:
                continue
            targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    names[target.id] = value

    operations: list[Mapping[str, Any]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        position = base_position + getattr(node, "lineno", 1)
        if isinstance(node.func, ast.Attribute):
            method = node.func.attr
            receiver = _static_path_value(node.func.value, names)
            if method in {"write_text", "write_bytes", "unlink"}:
                if receiver is not None and LITERAL_TMP_PY_RE.fullmatch(receiver):
                    operations.append(
                        {
                            "position": position,
                            "kind": f"inline_python_{method}",
                            "target": receiver,
                            "replayability": "ambiguous_dynamic_mutation_not_replayed",
                        }
                    )
                continue
            if method in {"rename", "replace"} and receiver is not None:
                destination = _static_path_value(node.args[0], names) if node.args else None
                if LITERAL_TMP_PY_RE.fullmatch(receiver) or (
                    destination is not None and LITERAL_TMP_PY_RE.fullmatch(destination)
                ):
                    operations.append(
                        {
                            "position": position,
                            "kind": f"inline_python_{method}",
                            "source": receiver,
                            "target": destination,
                            "replayability": "ambiguous_dynamic_mutation_not_replayed",
                        }
                    )
                continue
        if isinstance(node.func, ast.Name) and node.func.id == "open" and node.args:
            target = _static_path_value(node.args[0], names)
            mode = _static_path_value(node.args[1], names) if len(node.args) > 1 else "r"
            for keyword in node.keywords:
                if keyword.arg == "mode":
                    mode = _static_path_value(keyword.value, names)
            if (
                target is not None
                and LITERAL_TMP_PY_RE.fullmatch(target)
                and isinstance(mode, str)
                and any(flag in mode for flag in "wax+")
            ):
                operations.append(
                    {
                        "position": position,
                        "kind": "inline_python_open_write",
                        "target": target,
                        "mode": mode,
                        "replayability": "ambiguous_dynamic_mutation_not_replayed",
                    }
                )
    return operations


def _python_write_targets(command: str) -> list[Mapping[str, Any]]:
    operations: list[Mapping[str, Any]] = []
    if not re.search(
        r"\.(?:write_text|write_bytes|unlink|rename|replace)\s*\(|open\s*\(", command
    ):
        return operations
    bodies = _python_heredoc_bodies(command)
    for base_position, body in bodies:
        operations.extend(_python_body_write_targets(body, base_position))
    if bodies:
        return operations

    # One-line ``python -c`` commands are retained conservatively.  They are
    # never evaluated, and their exact target is used only when a literal
    # /tmp Python path appears in the same command.
    for path in literal_tmp_py_paths(command):
        operations.append(
            {
                "position": command.find(path),
                "kind": "inline_python_possible_mutation",
                "target": path,
                "replayability": "ambiguous_dynamic_mutation_not_replayed",
            }
        )
    return operations


def analyze_terminal_command(command: str) -> Mapping[str, Any]:
    references = all_tmp_py_expressions(command)
    literal_references = literal_tmp_py_paths(command)
    operations = _heredoc_operations(command)
    operations.extend(_simple_shell_operations(command))
    operations.extend(_python_write_targets(command))
    heredoc_targets = {
        str(operation.get("target"))
        for operation in operations
        if operation.get("kind") in {"literal_heredoc_write", "literal_heredoc_append"}
    }
    operations = [
        operation
        for operation in operations
        if not (
            operation.get("kind")
            in {"unparsed_redirect_write", "unparsed_redirect_append"}
            and str(operation.get("target")) in heredoc_targets
        )
    ]
    unique_operations: list[Mapping[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for operation in sorted(operations, key=lambda item: (int(item["position"]), str(item["kind"]))):
        key = (
            operation.get("position"),
            operation.get("kind"),
            operation.get("source"),
            operation.get("target"),
            tuple(operation.get("sources", [])),
        )
        if key in seen:
            continue
        seen.add(key)
        unique_operations.append(operation)
    mutating_kinds = {
        "literal_heredoc_write",
        "literal_heredoc_append",
        "concat_write",
        "concat_append",
        "copy",
        "move",
        "delete",
        "sed_in_place",
        "perl_in_place",
        "unparsed_redirect_write",
        "unparsed_redirect_append",
        "inline_python_possible_mutation",
    }
    mutation_operations = [
        operation
        for operation in unique_operations
        if operation["kind"] in mutating_kinds
        or str(operation["kind"]).startswith("inline_python_")
    ]
    ambiguous = any(
        str(operation.get("replayability", "")).startswith("ambiguous")
        for operation in mutation_operations
    )
    return {
        "python_path_expressions": references,
        "literal_python_paths": literal_references,
        "related_jsonl_expressions": jsonl_expressions(command),
        "operations": unique_operations,
        "source_mutation_candidate": bool(mutation_operations),
        "has_ambiguous_mutation": ambiguous,
        "classification": (
            "ambiguous_or_mixed_source_mutation"
            if ambiguous
            else "deterministic_source_mutation"
            if mutation_operations
            else "source_reference_without_detected_mutation"
        ),
    }


def call_common_record(call: ToolCall, session_meta: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "event_id": f"{call.session_id}:{call.tool_call_id}",
        "top_level_session_id": PARENT_SESSION_ID,
        "agent_id": call.session_id,
        "session_id": call.session_id,
        "parent_session_id": session_meta.get("parent_session_id"),
        "agent_description": session_meta.get("description"),
        "agent_status": session_meta.get("status"),
        "agent_type": session_meta.get("subagent_type"),
        "effective_model_id": session_meta.get("effective_model_id"),
        "journal_path": call.journal_path,
        "journal_line": call.journal_line,
        "tool_call_id": call.tool_call_id,
        "tool_name": call.tool_name,
        "tool_title": call.title,
        "timestamp_epoch": call.timestamp_epoch,
        "timestamp_ms": call.timestamp_ms,
        "timestamp_utc": call.timestamp_utc,
        "journal_event_id": call.event_id,
        "tool_status": call.status,
        "exit_code": call.exit_code,
        "result_error": call.result_error,
        "tool_completed": call.completed,
        "command_succeeded": call.command_succeeded if call.tool_name == "run_terminal_command" else None,
        "result_content_summary": call.result_content_summary,
        "raw_output_sha256": call.raw_output_sha256,
        "raw_output_bytes": call.raw_output_bytes,
    }


def structured_inventory_record(
    call: ToolCall, session_meta: Mapping[str, Any], target_path: str
) -> Mapping[str, Any]:
    record = call_common_record(call, session_meta)
    content = call.raw_input.get("content")
    old_string = call.raw_input.get("old_string")
    new_string = call.raw_input.get("new_string")
    raw_input_serialized = canonical_json_bytes(call.raw_input)
    record.update(
        {
            "mutation_channel": "structured",
            "mutation_kind": (
                "full_write"
                if call.tool_name in {"write", "write_file"}
                else "search_replace"
                if call.tool_name == "search_replace"
                else "other_structured_edit"
            ),
            "original_path": target_path,
            "path_is_literal_tmp_python": bool(LITERAL_TMP_PY_RE.fullmatch(target_path)),
            "raw_input_sha256": sha256_bytes(raw_input_serialized),
            "raw_input_bytes": len(raw_input_serialized),
            "content": string_field_digest(content),
            "old_string": string_field_digest(old_string),
            "new_string": string_field_digest(new_string),
            "related_jsonl_expressions": jsonl_expressions(
                "\n".join(
                    value
                    for value in (content, old_string, new_string)
                    if isinstance(value, str)
                )
            ),
            "eligible_for_replay": call.completed,
        }
    )
    return record


def terminal_inventory_record(
    call: ToolCall, session_meta: Mapping[str, Any], command: str
) -> Mapping[str, Any]:
    record = call_common_record(call, session_meta)
    analysis = analyze_terminal_command(command)
    encoded = command.encode("utf-8")
    record.update(
        {
            "mutation_channel": "terminal",
            "command": command,
            "command_sha256": sha256_bytes(encoded),
            "command_bytes": len(encoded),
            "terminal_logs": terminal_log_paths(call),
            "eligible_for_replay": call.command_succeeded,
            **analysis,
        }
    )
    return record


def prompt_summary(metadata: Mapping[str, Any]) -> Mapping[str, Any]:
    prompt = metadata.get("prompt")
    if not isinstance(prompt, str):
        prompt = ""
    return {
        "sha256": sha256_text(prompt),
        "bytes": len(prompt.encode("utf-8")),
        "factory_mentions": sorted(
            set(
                re.findall(
                    r"(?im)(?:factory\s*[`:=-]+\s*|factory\s+`)([a-z0-9][a-z0-9-]{2,})",
                    prompt,
                )
            )
        ),
        "run_label_mentions": sorted(
            set(re.findall(r"(?im)^\s*run\s+label\s*:\s*([^\n`]+)", prompt))
        ),
        "generator_mentions": sorted(
            set(re.findall(r"(?im)^\s*generator\s*:\s*([^\n`]+)", prompt))
        ),
        "round_mentions": sorted(
            set(re.findall(r"(?im)^\s*round(?:\s+n)?\s*:\s*(\d+)", prompt))
        ),
        "quota_mentions": sorted(
            set(re.findall(r"(?im)^\s*quota(?:\s+q)?\s*:\s*(\d+)", prompt))
        ),
        "jsonl_mentions": jsonl_expressions(prompt),
        "declares_research_only": "research_only" in prompt or "research-only" in prompt,
        "declares_training_blocked": bool(
            re.search(r"project_training_policy[^\n]{0,80}blocked", prompt, re.IGNORECASE)
        ),
        "mentions_rm_793": "RM-793" in prompt,
    }


def hunk_evidence_records() -> Iterator[Mapping[str, Any]]:
    path = SESSION_BASE / PARENT_SESSION_ID / "hunk_records.jsonl"
    if not path.exists():
        return
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RecoveryError(f"invalid hunk JSON at {path}:{line_number}: {exc}") from exc
            file_path = record.get("filePath") if isinstance(record, dict) else None
            if not isinstance(file_path, str) or not LITERAL_TMP_PY_RE.fullmatch(file_path):
                continue
            yield {
                "journal_path": str(path),
                "journal_line": line_number,
                **record,
            }


def inventory() -> None:
    ensure_recovery_boundary()
    inventory_dir = RECOVERY_ROOT / "inventory"
    fresh_directory(inventory_dir)

    nodes, edges = discover_session_graph()
    metadata_by_session = {
        node.session_id: {
            "parent_session_id": node.parent_session_id,
            "depth": node.depth,
            "status": node.status,
            "description": node.metadata.get("description"),
            "subagent_type": node.metadata.get("subagent_type"),
            "started_at": node.metadata.get("started_at"),
            "completed_at": node.metadata.get("completed_at"),
            "duration_ms": node.metadata.get("duration_ms"),
            "tool_calls": node.metadata.get("tool_calls"),
            "turns": node.metadata.get("turns"),
            "child_cwd": node.metadata.get("child_cwd"),
            "effective_model_id": node.metadata.get("effective_model_id"),
            "prompt": prompt_summary(node.metadata),
        }
        for node in nodes
    }
    missing_updates = [
        node.session_id
        for node in nodes
        if not (SESSION_BASE / node.session_id / "updates.jsonl").exists()
    ]
    session_graph = {
        "schema_version": SCHEMA_VERSION,
        "top_level_session_id": PARENT_SESSION_ID,
        "session_base": str(SESSION_BASE),
        "inventory_generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "session_count": len(nodes),
        "child_session_count": len(nodes) - 1,
        "max_depth": max(node.depth for node in nodes),
        "status_counts": dict(Counter(node.status for node in nodes)),
        "missing_updates_count": len(missing_updates),
        "missing_updates_session_ids": missing_updates,
        "nodes": [
            {
                "session_id": node.session_id,
                "parent_session_id": node.parent_session_id,
                "depth": node.depth,
                "status": node.status,
                "metadata_path": node.metadata_path,
                **metadata_by_session[node.session_id],
            }
            for node in nodes
        ],
        "edges": edges,
    }
    write_json_fresh(inventory_dir / "session-graph.json", session_graph)

    journal_hash_count = write_jsonl_fresh(
        inventory_dir / "journal-hashes.before.jsonl", iter_evidence_paths(nodes)
    )

    structured_records: list[Mapping[str, Any]] = []
    terminal_records: list[Mapping[str, Any]] = []
    all_tool_counts: Counter[str] = Counter()
    for node in nodes:
        session_meta = metadata_by_session[node.session_id]
        for call in iter_tool_calls(node.session_id):
            all_tool_counts[call.tool_name] += 1
            if call.tool_name in STRUCTURED_TOOLS:
                target = target_path_from_structured_call(call)
                if isinstance(target, str) and target.startswith("/tmp/") and target.endswith(".py"):
                    structured_records.append(structured_inventory_record(call, session_meta, target))
            if call.tool_name == "run_terminal_command":
                command = call.raw_input.get("command")
                if isinstance(command, str) and TMP_PY_RE.search(command):
                    terminal_records.append(terminal_inventory_record(call, session_meta, command))

    structured_records.sort(
        key=lambda record: (
            int(record.get("timestamp_ms") or 0),
            str(record["session_id"]),
            int(record["journal_line"]),
            str(record["tool_call_id"]),
        )
    )
    terminal_records.sort(
        key=lambda record: (
            int(record.get("timestamp_ms") or 0),
            str(record["session_id"]),
            int(record["journal_line"]),
            str(record["tool_call_id"]),
        )
    )
    write_jsonl_fresh(inventory_dir / "mutations.jsonl", structured_records)
    write_jsonl_fresh(inventory_dir / "terminal-mutations.jsonl", terminal_records)
    hunk_count = write_jsonl_fresh(
        inventory_dir / "hunk-evidence.jsonl", hunk_evidence_records()
    )

    structured_outcomes = Counter(
        (str(record["mutation_kind"]), str(record["tool_status"]))
        for record in structured_records
    )
    terminal_classes = Counter(str(record["classification"]) for record in terminal_records)
    summary = {
        "schema_version": SCHEMA_VERSION,
        "top_level_session_id": PARENT_SESSION_ID,
        "session_count": len(nodes),
        "child_session_count": len(nodes) - 1,
        "journal_files_hashed": journal_hash_count,
        "missing_updates_session_ids": missing_updates,
        "all_tool_counts": dict(all_tool_counts.most_common()),
        "structured_temp_python_event_count": len(structured_records),
        "structured_temp_python_unique_paths": len(
            {str(record["original_path"]) for record in structured_records}
        ),
        "structured_outcome_counts": {
            f"{kind}:{status}": count
            for (kind, status), count in sorted(structured_outcomes.items())
        },
        "terminal_calls_referencing_temp_python": len(terminal_records),
        "terminal_source_mutation_candidates": sum(
            bool(record["source_mutation_candidate"]) for record in terminal_records
        ),
        "terminal_ambiguous_mutation_candidates": sum(
            bool(record["has_ambiguous_mutation"]) for record in terminal_records
        ),
        "terminal_classification_counts": dict(terminal_classes),
        "hunk_evidence_record_count": hunk_count,
        "constraints": {
            "journals_read_only": True,
            "recovered_programs_executed": False,
            "dataset_paths_written": False,
            "active_checkout_written": False,
        },
    }
    write_json_fresh(inventory_dir / "inventory-summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))


@dataclasses.dataclass
class ReconstructedState:
    original_path: str
    text: str | None = None
    exists: bool | None = None
    certainty: str = "unrecoverable"
    versions: list[dict[str, Any]] = dataclasses.field(default_factory=list)
    events: list[dict[str, Any]] = dataclasses.field(default_factory=list)
    unresolved: list[dict[str, Any]] = dataclasses.field(default_factory=list)
    terminal_events: list[str] = dataclasses.field(default_factory=list)
    agent_ids: set[str] = dataclasses.field(default_factory=set)
    last_reset_event_id: str | None = None
    terminal_final_state_uncertain: bool = False


def path_key(original_path: str) -> str:
    parent = str(Path(original_path).parent)
    if parent.startswith("/tmp/"):
        parent = parent[len("/tmp/") :]
    elif parent == "/tmp":
        parent = "tmp-root"
    slug = re.sub(r"[^A-Za-z0-9._-]+", "__", parent).strip("._-") or "tmp-root"
    slug = slug[:80]
    return f"{slug}--{sha256_text(original_path)[:12]}"


def safe_original_basename(original_path: str) -> tuple[str, bool]:
    basename = Path(original_path).name
    if re.fullmatch(r"[A-Za-z0-9._-]+\.py", basename):
        return basename, True
    return f"unsafe-name-{sha256_text(original_path)[:16]}.py", False


def session_metadata_by_id(nodes: Sequence[SessionNode]) -> dict[str, Mapping[str, Any]]:
    return {
        node.session_id: {
            "parent_session_id": node.parent_session_id,
            "depth": node.depth,
            "status": node.status,
            "description": node.metadata.get("description"),
            "subagent_type": node.metadata.get("subagent_type"),
            "started_at": node.metadata.get("started_at"),
            "completed_at": node.metadata.get("completed_at"),
            "duration_ms": node.metadata.get("duration_ms"),
            "tool_calls": node.metadata.get("tool_calls"),
            "turns": node.metadata.get("turns"),
            "child_cwd": node.metadata.get("child_cwd"),
            "effective_model_id": node.metadata.get("effective_model_id"),
            "prompt": node.metadata.get("prompt") if isinstance(node.metadata.get("prompt"), str) else "",
        }
        for node in nodes
    }


def recovered_version_path(state: ReconstructedState, version_number: int) -> Path:
    basename, _ = safe_original_basename(state.original_path)
    return (
        RECOVERY_ROOT
        / "recovered_sources"
        / "by-original-path"
        / path_key(state.original_path)
        / "versions"
        / f"v{version_number:04d}"
        / basename
    )


def emit_recovered_version(
    state: ReconstructedState,
    *,
    event: ToolCall,
    source_channel: str,
    source_operation: str,
    classification: str,
    evidence: Sequence[str],
) -> dict[str, Any]:
    if state.text is None:
        raise RecoveryError(f"cannot emit unknown state for {state.original_path}")
    version_number = len(state.versions) + 1
    destination = recovered_version_path(state, version_number)
    encoded = state.text.encode("utf-8")
    write_bytes_fresh(destination, encoded, mode=0o400)
    _, basename_preserved = safe_original_basename(state.original_path)
    version = {
        "version": version_number,
        "version_id": f"{path_key(state.original_path)}:v{version_number:04d}",
        "original_path": state.original_path,
        "original_basename": Path(state.original_path).name,
        "basename_preserved": basename_preserved,
        "recovered_path": str(destination),
        "recovered_path_relative": str(destination.relative_to(RECOVERY_ROOT)),
        "sha256": sha256_bytes(encoded),
        "bytes": len(encoded),
        "classification": classification,
        "classification_evidence": list(evidence),
        "source_channel": source_channel,
        "source_operation": source_operation,
        "source_event_id": f"{event.session_id}:{event.tool_call_id}",
        "agent_id": event.session_id,
        "session_id": event.session_id,
        "timestamp_utc": event.timestamp_utc,
        "timestamp_ms": event.timestamp_ms,
        "journal_path": event.journal_path,
        "journal_line": event.journal_line,
        "tool_call_id": event.tool_call_id,
        "file_mode": "0400",
    }
    state.versions.append(version)
    return version


def fragment_directory(state: ReconstructedState, event: ToolCall) -> Path:
    event_slug = re.sub(r"[^A-Za-z0-9._-]+", "_", event.tool_call_id)
    return (
        RECOVERY_ROOT
        / "recovered_sources"
        / "by-original-path"
        / path_key(state.original_path)
        / "fragments"
        / event_slug
    )


def save_edit_fragments(
    state: ReconstructedState, event: ToolCall, old_string: Any, new_string: Any
) -> list[str]:
    directory = fragment_directory(state, event)
    basename, _ = safe_original_basename(state.original_path)
    paths: list[str] = []
    if isinstance(old_string, str):
        old_path = directory / f"{basename}.old.pyfrag"
        write_bytes_fresh(old_path, old_string.encode("utf-8"), mode=0o400)
        paths.append(str(old_path))
    if isinstance(new_string, str):
        new_path = directory / f"{basename}.new.pyfrag"
        write_bytes_fresh(new_path, new_string.encode("utf-8"), mode=0o400)
        paths.append(str(new_path))
    return paths


def public_operation(operation: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in operation.items() if not key.startswith("_")}


def terminal_operations_for_replay(command: str) -> list[Mapping[str, Any]]:
    analysis = analyze_terminal_command(command)
    operations = [dict(operation) for operation in analysis["operations"]]
    heredocs = _heredoc_operations(command, include_content=True)
    payloads = {
        (
            operation.get("position"),
            operation.get("kind"),
            operation.get("target"),
        ): operation.get("_content")
        for operation in heredocs
    }
    for operation in operations:
        key = (
            operation.get("position"),
            operation.get("kind"),
            operation.get("target"),
        )
        if key in payloads:
            operation["_content"] = payloads[key]
    return sorted(operations, key=lambda item: (int(item.get("position", 0)), str(item["kind"])))


def state_for(states: dict[str, ReconstructedState], original_path: str) -> ReconstructedState:
    if original_path not in states:
        states[original_path] = ReconstructedState(original_path=original_path)
    return states[original_path]


def mark_ambiguous_terminal(
    state: ReconstructedState,
    *,
    event: ToolCall,
    operation: Mapping[str, Any],
    reason: str,
) -> None:
    if state.text is not None:
        state.certainty = "partial"
    else:
        state.certainty = "unrecoverable"
    state.exists = None
    state.terminal_final_state_uncertain = True
    state.unresolved.append(
        {
            "event_id": f"{event.session_id}:{event.tool_call_id}",
            "channel": "terminal",
            "operation": operation.get("kind"),
            "timestamp_utc": event.timestamp_utc,
            "reason": reason,
            "journal_path": event.journal_path,
            "journal_line": event.journal_line,
        }
    )


def apply_terminal_operation(
    states: dict[str, ReconstructedState],
    event: ToolCall,
    operation: Mapping[str, Any],
) -> Mapping[str, Any]:
    kind = str(operation.get("kind"))
    target = operation.get("target")
    audit: dict[str, Any] = {
        **public_operation(operation),
        "applied": False,
        "application_result": None,
        "emitted_version_id": None,
    }
    if isinstance(target, str) and LITERAL_TMP_PY_RE.fullmatch(target):
        target_state = state_for(states, target)
        target_state.agent_ids.add(event.session_id)
    else:
        target_state = None

    if kind in {"literal_heredoc_write", "literal_heredoc_append"}:
        if target_state is None:
            audit["application_result"] = "unsafe_or_nonliteral_target"
            return audit
        content = operation.get("_content")
        if operation.get("replayability") != "exact" or not isinstance(content, str):
            mark_ambiguous_terminal(
                target_state,
                event=event,
                operation=operation,
                reason="unquoted or unparsable heredoc may undergo shell expansion",
            )
            audit["application_result"] = "not_replayed_shell_expansion"
            return audit
        if kind == "literal_heredoc_append":
            if target_state.text is None or target_state.exists is False:
                mark_ambiguous_terminal(
                    target_state,
                    event=event,
                    operation=operation,
                    reason="literal append has no known prior source state",
                )
                audit["application_result"] = "not_replayed_missing_append_base"
                return audit
            target_state.text += content
        else:
            target_state.text = content
        target_state.exists = True
        target_state.certainty = "high-confidence"
        target_state.last_reset_event_id = f"{event.session_id}:{event.tool_call_id}"
        target_state.terminal_final_state_uncertain = False
        version = emit_recovered_version(
            target_state,
            event=event,
            source_channel="terminal",
            source_operation=kind,
            classification="high-confidence",
            evidence=[
                "terminal call completed with exit code 0",
                "quoted literal heredoc content was present in the recorded command",
                "content was reconstructed by parsing shell text without executing it",
            ],
        )
        audit.update(
            {
                "applied": True,
                "application_result": "replayed_literal_heredoc",
                "emitted_version_id": version["version_id"],
            }
        )
        return audit

    if kind in {"copy", "move"}:
        source = operation.get("source")
        if (
            target_state is None
            or not isinstance(source, str)
            or not LITERAL_TMP_PY_RE.fullmatch(source)
        ):
            audit["application_result"] = "unsafe_or_nonliteral_copy_path"
            return audit
        source_state = state_for(states, source)
        source_state.agent_ids.add(event.session_id)
        if source_state.text is None or source_state.exists is False:
            mark_ambiguous_terminal(
                target_state,
                event=event,
                operation=operation,
                reason=f"{kind} source state was not reconstructable",
            )
            audit["application_result"] = "not_replayed_unknown_source_state"
            return audit
        target_state.text = source_state.text
        target_state.exists = True
        target_state.certainty = "high-confidence" if source_state.certainty != "partial" else "partial"
        target_state.last_reset_event_id = f"{event.session_id}:{event.tool_call_id}"
        target_state.terminal_final_state_uncertain = source_state.certainty == "partial"
        version = emit_recovered_version(
            target_state,
            event=event,
            source_channel="terminal",
            source_operation=kind,
            classification=target_state.certainty,
            evidence=[
                "terminal call completed with exit code 0",
                f"literal {kind} source and destination were recorded",
                f"source state classification was {source_state.certainty}",
            ],
        )
        if kind == "move":
            source_state.exists = False
            source_state.text = None
            source_state.events.append(
                {
                    "event_id": f"{event.session_id}:{event.tool_call_id}",
                    "channel": "terminal",
                    "operation": "move_source_removed",
                    "timestamp_utc": event.timestamp_utc,
                }
            )
        audit.update(
            {
                "applied": True,
                "application_result": f"replayed_{kind}",
                "emitted_version_id": version["version_id"],
            }
        )
        return audit

    if kind in {"concat_write", "concat_append"}:
        sources = operation.get("sources")
        if target_state is None or not isinstance(sources, list) or not sources:
            audit["application_result"] = "invalid_concat_paths"
            return audit
        source_states: list[ReconstructedState] = []
        for source in sources:
            if not isinstance(source, str) or not LITERAL_TMP_PY_RE.fullmatch(source):
                source_states = []
                break
            source_state = state_for(states, source)
            source_state.agent_ids.add(event.session_id)
            if source_state.text is None or source_state.exists is False:
                source_states = []
                break
            source_states.append(source_state)
        if not source_states:
            mark_ambiguous_terminal(
                target_state,
                event=event,
                operation=operation,
                reason="one or more concatenation source states were not reconstructable",
            )
            audit["application_result"] = "not_replayed_unknown_concat_source"
            return audit
        prefix = ""
        if kind == "concat_append":
            if target_state.text is None or target_state.exists is False:
                mark_ambiguous_terminal(
                    target_state,
                    event=event,
                    operation=operation,
                    reason="concatenation append has no known prior destination state",
                )
                audit["application_result"] = "not_replayed_missing_append_base"
                return audit
            prefix = target_state.text
        target_state.text = prefix + "".join(source.text or "" for source in source_states)
        target_state.exists = True
        target_state.certainty = (
            "partial" if any(source.certainty == "partial" for source in source_states) else "high-confidence"
        )
        target_state.last_reset_event_id = f"{event.session_id}:{event.tool_call_id}"
        target_state.terminal_final_state_uncertain = target_state.certainty == "partial"
        version = emit_recovered_version(
            target_state,
            event=event,
            source_channel="terminal",
            source_operation=kind,
            classification=target_state.certainty,
            evidence=[
                "terminal call completed with exit code 0",
                "literal cat source list and destination were recorded",
                "all source byte states were available without executing the command",
            ],
        )
        audit.update(
            {
                "applied": True,
                "application_result": "replayed_literal_concatenation",
                "emitted_version_id": version["version_id"],
            }
        )
        return audit

    if kind == "delete":
        if target_state is None:
            audit["application_result"] = "unsafe_or_nonliteral_delete_target"
            return audit
        target_state.exists = False
        target_state.text = None
        target_state.events.append(
            {
                "event_id": f"{event.session_id}:{event.tool_call_id}",
                "channel": "terminal",
                "operation": "delete",
                "timestamp_utc": event.timestamp_utc,
                "journal_path": event.journal_path,
                "journal_line": event.journal_line,
            }
        )
        audit.update(
            {
                "applied": True,
                "application_result": "recorded_deleted_state",
            }
        )
        return audit

    affected_paths: list[str] = []
    if target_state is not None:
        affected_paths.append(target_state.original_path)
    for candidate in operation.get("candidate_paths", []) or []:
        if isinstance(candidate, str) and LITERAL_TMP_PY_RE.fullmatch(candidate):
            affected_paths.append(candidate)
    for affected_path in sorted(set(affected_paths)):
        affected_state = state_for(states, affected_path)
        affected_state.agent_ids.add(event.session_id)
        mark_ambiguous_terminal(
            affected_state,
            event=event,
            operation=operation,
            reason=f"{kind} was recorded but is not conclusively reproducible without execution",
        )
    audit["application_result"] = (
        "not_replayed_ambiguous_terminal_mutation"
        if affected_paths
        else "no_literal_source_target"
    )
    return audit


def reconstruct() -> None:
    ensure_recovery_boundary()
    inventory_dir = RECOVERY_ROOT / "inventory"
    if not (inventory_dir / "inventory-summary.json").exists():
        raise RecoveryError("inventory phase must complete before reconstruction")
    sources_root = RECOVERY_ROOT / "recovered_sources"
    manifest_dir = RECOVERY_ROOT / "manifest"
    reports_dir = RECOVERY_ROOT / "reports"
    fresh_directory(sources_root)
    fresh_directory(manifest_dir)
    fresh_directory(reports_dir)

    nodes, _ = discover_session_graph()
    metadata_by_session = session_metadata_by_id(nodes)
    events: list[ToolCall] = []
    for node in nodes:
        for call in iter_tool_calls(node.session_id):
            if call.tool_name in STRUCTURED_TOOLS:
                target = target_path_from_structured_call(call)
                if isinstance(target, str) and target.startswith("/tmp/") and target.endswith(".py"):
                    events.append(call)
            elif call.tool_name == "run_terminal_command":
                command = call.raw_input.get("command")
                if isinstance(command, str) and TMP_PY_RE.search(command):
                    events.append(call)
    events.sort(key=lambda event: event.order_key)

    states: dict[str, ReconstructedState] = {}
    event_audit: list[dict[str, Any]] = []
    terminal_audit: list[dict[str, Any]] = []
    for event in events:
        event_id = f"{event.session_id}:{event.tool_call_id}"
        if event.tool_name in STRUCTURED_TOOLS:
            original_path = target_path_from_structured_call(event)
            if original_path is None:
                continue
            state = state_for(states, original_path)
            state.agent_ids.add(event.session_id)
            mutation_kind = (
                "full_write"
                if event.tool_name in {"write", "write_file"}
                else "search_replace"
                if event.tool_name == "search_replace"
                else "other_structured_edit"
            )
            audit = {
                "event_id": event_id,
                "channel": "structured",
                "operation": mutation_kind,
                "original_path": original_path,
                "agent_id": event.session_id,
                "agent_description": metadata_by_session[event.session_id].get("description"),
                "agent_status": metadata_by_session[event.session_id].get("status"),
                "timestamp_utc": event.timestamp_utc,
                "timestamp_ms": event.timestamp_ms,
                "journal_path": event.journal_path,
                "journal_line": event.journal_line,
                "tool_status": event.status,
                "applied": False,
                "application_result": None,
                "emitted_version_id": None,
            }
            if mutation_kind == "full_write":
                content = event.raw_input.get("content")
                if event.completed and isinstance(content, str):
                    state.text = content
                    state.exists = True
                    state.certainty = "exact"
                    state.unresolved = []
                    state.last_reset_event_id = event_id
                    state.terminal_final_state_uncertain = False
                    version = emit_recovered_version(
                        state,
                        event=event,
                        source_channel="structured",
                        source_operation="full_write",
                        classification="exact",
                        evidence=[
                            "full source string was recorded in structured write input",
                            "the structured write outcome was Completed",
                            "UTF-8 bytes preserve the recorded source string exactly",
                        ],
                    )
                    audit.update(
                        {
                            "applied": True,
                            "application_result": "replayed_full_write",
                            "emitted_version_id": version["version_id"],
                        }
                    )
                else:
                    reason = (
                        "full write did not complete"
                        if not event.completed
                        else "full write input lacks a string content field"
                    )
                    state.unresolved.append(
                        {
                            "event_id": event_id,
                            "channel": "structured",
                            "operation": "full_write",
                            "reason": reason,
                        }
                    )
                    audit["application_result"] = "not_replayed"
            elif mutation_kind == "search_replace":
                old_string = event.raw_input.get("old_string")
                new_string = event.raw_input.get("new_string")
                if not event.completed:
                    fragments = save_edit_fragments(state, event, old_string, new_string)
                    audit.update(
                        {
                            "application_result": "failed_edit_not_applied",
                            "fragment_paths": fragments,
                        }
                    )
                elif not isinstance(old_string, str) or not isinstance(new_string, str):
                    state.certainty = "partial" if state.text is not None else "unrecoverable"
                    state.unresolved.append(
                        {
                            "event_id": event_id,
                            "channel": "structured",
                            "operation": "search_replace",
                            "reason": "successful edit lacks string old/new fields",
                        }
                    )
                    audit["application_result"] = "not_replayed_missing_strings"
                elif state.text is None or state.exists is False:
                    fragments = save_edit_fragments(state, event, old_string, new_string)
                    state.certainty = "unrecoverable"
                    state.exists = True
                    state.unresolved.append(
                        {
                            "event_id": event_id,
                            "channel": "structured",
                            "operation": "search_replace",
                            "reason": "successful edit has no known full base state",
                            "fragment_paths": fragments,
                        }
                    )
                    audit.update(
                        {
                            "application_result": "not_replayed_missing_base",
                            "fragment_paths": fragments,
                        }
                    )
                else:
                    occurrences = state.text.count(old_string)
                    audit["old_string_occurrences_in_reconstruction"] = occurrences
                    if occurrences == 1:
                        state.text = state.text.replace(old_string, new_string, 1)
                        state.exists = True
                        classification = state.certainty
                        if classification not in {"exact", "high-confidence", "partial"}:
                            classification = "partial"
                            state.certainty = classification
                        version = emit_recovered_version(
                            state,
                            event=event,
                            source_channel="structured",
                            source_operation="search_replace",
                            classification=classification,
                            evidence=[
                                "structured search_replace outcome was Completed",
                                "recorded old_string occurred exactly once in the reconstructed prior state",
                                f"prior state classification was {classification}",
                            ],
                        )
                        audit.update(
                            {
                                "applied": True,
                                "application_result": "replayed_unique_search_replace",
                                "emitted_version_id": version["version_id"],
                            }
                        )
                    else:
                        fragments = save_edit_fragments(state, event, old_string, new_string)
                        state.certainty = "partial"
                        state.terminal_final_state_uncertain = True
                        state.unresolved.append(
                            {
                                "event_id": event_id,
                                "channel": "structured",
                                "operation": "search_replace",
                                "reason": (
                                    "recorded old_string occurrence count was "
                                    f"{occurrences}, so placement is not provable"
                                ),
                                "fragment_paths": fragments,
                            }
                        )
                        audit.update(
                            {
                                "application_result": "not_replayed_nonunique_or_missing_match",
                                "fragment_paths": fragments,
                            }
                        )
            else:
                state.certainty = "partial" if state.text is not None else "unrecoverable"
                state.unresolved.append(
                    {
                        "event_id": event_id,
                        "channel": "structured",
                        "operation": mutation_kind,
                        "reason": "structured edit tool is not supported by conservative replayer",
                    }
                )
                audit["application_result"] = "unsupported_structured_edit"
            state.events.append(audit)
            event_audit.append(audit)
            continue

        command = event.raw_input.get("command")
        if not isinstance(command, str):
            continue
        analysis = analyze_terminal_command(command)
        call_audit: dict[str, Any] = {
            "event_id": event_id,
            "channel": "terminal",
            "agent_id": event.session_id,
            "agent_description": metadata_by_session[event.session_id].get("description"),
            "agent_status": metadata_by_session[event.session_id].get("status"),
            "timestamp_utc": event.timestamp_utc,
            "timestamp_ms": event.timestamp_ms,
            "journal_path": event.journal_path,
            "journal_line": event.journal_line,
            "tool_status": event.status,
            "exit_code": event.exit_code,
            "command_sha256": sha256_text(command),
            "command_bytes": len(command.encode("utf-8")),
            "command_succeeded": event.command_succeeded,
            "python_path_expressions": analysis["python_path_expressions"],
            "literal_python_paths": analysis["literal_python_paths"],
            "related_jsonl_expressions": analysis["related_jsonl_expressions"],
            "classification": analysis["classification"],
            "operations": [],
        }
        for path in analysis["literal_python_paths"]:
            state_for(states, path).terminal_events.append(event_id)
        if event.command_succeeded:
            for operation in terminal_operations_for_replay(command):
                application = apply_terminal_operation(states, event, operation)
                call_audit["operations"].append(application)
        else:
            call_audit["operations"] = [
                {
                    **public_operation(operation),
                    "applied": False,
                    "application_result": "terminal_call_not_successful",
                }
                for operation in terminal_operations_for_replay(command)
            ]
        terminal_audit.append(call_audit)

    # Store a path-local metadata record beside every recovered lineage.
    hunk_counts: Counter[str] = Counter()
    hunk_path = inventory_dir / "hunk-evidence.jsonl"
    with hunk_path.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if isinstance(record.get("filePath"), str):
                hunk_counts[record["filePath"]] += 1

    reconstruction_entries: list[dict[str, Any]] = []
    for original_path, state in sorted(states.items()):
        if state.versions:
            classification = state.certainty
            if classification not in {"exact", "high-confidence", "partial"}:
                classification = "partial"
        else:
            classification = "unrecoverable"
        if state.terminal_final_state_uncertain and classification in {"exact", "high-confidence"}:
            classification = "partial"
        final_state = (
            "deleted"
            if state.exists is False
            else "present_reconstructed"
            if state.text is not None
            else "unknown"
        )
        evidence: list[str] = []
        if classification == "exact":
            evidence.append(
                "latest state derives from a completed full structured write and uniquely replayed completed structured edits"
            )
        elif classification == "high-confidence":
            evidence.append(
                "latest state includes a completed deterministic terminal write/copy/concatenation replayed statically"
            )
        elif classification == "partial":
            evidence.append(
                "at least one full version was recovered, but a later successful edit or terminal mutation could not be placed conclusively"
            )
        else:
            evidence.append(
                "no complete source state could be established from successful recorded full writes or deterministic terminal operations"
            )
        if final_state == "deleted":
            evidence.append("a successful recorded terminal delete or move removed the final in-/tmp state")
        if state.terminal_final_state_uncertain:
            evidence.append("one or more later terminal-driven mutations were not conclusively reproducible")
        entry = {
            "original_path": original_path,
            "path_key": path_key(original_path),
            "original_basename": Path(original_path).name,
            "classification": classification,
            "classification_evidence": evidence,
            "final_state": final_state,
            "terminal_final_state_uncertain": state.terminal_final_state_uncertain,
            "agent_ids": sorted(state.agent_ids),
            "hunk_evidence_count": hunk_counts[original_path],
            "version_count": len(state.versions),
            "versions": state.versions,
            "event_count": len(state.events),
            "unresolved_event_count": len(state.unresolved),
            "unresolved_events": state.unresolved,
            "terminal_event_ids": sorted(set(state.terminal_events)),
        }
        lineage_dir = sources_root / "by-original-path" / path_key(original_path)
        if lineage_dir.exists():
            write_json_fresh(lineage_dir / "path.json", entry, mode=0o400)
        reconstruction_entries.append(entry)

    terminal_audit_path = reports_dir / "terminal-mutation-audit.json"
    write_json_fresh(
        terminal_audit_path,
        {
            "schema_version": SCHEMA_VERSION,
            "top_level_session_id": PARENT_SESSION_ID,
            "policy": {
                "commands_executed": False,
                "replay_scope": [
                    "quoted literal heredoc writes/appends",
                    "literal file copies/moves",
                    "literal file concatenations",
                    "literal deletions as existence state",
                ],
                "not_replayed": [
                    "inline Python mutations",
                    "sed/perl in-place transforms",
                    "pipelines and unparsed redirections",
                    "variable-, glob-, or command-substitution-dependent operations",
                ],
            },
            "call_count": len(terminal_audit),
            "calls": terminal_audit,
        },
    )
    write_jsonl_fresh(reports_dir / "reconstruction-events.jsonl", event_audit)

    classification_counts = Counter(entry["classification"] for entry in reconstruction_entries)
    version_classification_counts = Counter(
        version["classification"]
        for entry in reconstruction_entries
        for version in entry["versions"]
    )
    reconstruction_manifest = {
        "schema_version": SCHEMA_VERSION,
        "top_level_session_id": PARENT_SESSION_ID,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "recovery_root": str(RECOVERY_ROOT),
        "session_base": str(SESSION_BASE),
        "safety": {
            "journal_content_treated_as_untrusted_data": True,
            "terminal_commands_executed": False,
            "recovered_programs_executed": False,
            "recovered_modules_imported": False,
            "dataset_paths_written": False,
        },
        "path_count": len(reconstruction_entries),
        "version_count": sum(entry["version_count"] for entry in reconstruction_entries),
        "classification_counts": dict(classification_counts),
        "version_classification_counts": dict(version_classification_counts),
        "terminal_uncertain_path_count": sum(
            bool(entry["terminal_final_state_uncertain"]) for entry in reconstruction_entries
        ),
        "entries": reconstruction_entries,
    }
    write_json_fresh(manifest_dir / "reconstruction-manifest.json", reconstruction_manifest)
    summary = {
        key: reconstruction_manifest[key]
        for key in (
            "path_count",
            "version_count",
            "classification_counts",
            "version_classification_counts",
            "terminal_uncertain_path_count",
        )
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


def qualified_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = qualified_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return None


def literal_string(node: ast.AST | None) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def simple_static_value(node: ast.AST, names: Mapping[str, Any]) -> Any:
    if isinstance(node, ast.Constant) and isinstance(node.value, (str, int, float, bool, type(None))):
        return node.value
    if isinstance(node, ast.Name):
        return names.get(node.id)
    if isinstance(node, ast.Call) and qualified_name(node.func) in {"Path", "pathlib.Path"}:
        if len(node.args) == 1:
            value = simple_static_value(node.args[0], names)
            return value if isinstance(value, str) else None
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        left = simple_static_value(node.left, names)
        right = simple_static_value(node.right, names)
        if isinstance(left, str) and isinstance(right, str):
            return str(Path(left) / right)
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value)
            elif isinstance(value, ast.FormattedValue):
                item = simple_static_value(value.value, names)
                if isinstance(item, (str, int, float)):
                    parts.append(str(item))
                else:
                    return None
            else:
                return None
        return "".join(parts)
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        values = [simple_static_value(item, names) for item in node.elts]
        return values if all(value is not None for value in values) else None
    if isinstance(node, ast.Dict):
        result: dict[Any, Any] = {}
        for key_node, value_node in zip(node.keys, node.values):
            if key_node is None:
                return None
            key = simple_static_value(key_node, names)
            value = simple_static_value(value_node, names)
            if key is None or value is None:
                return None
            result[key] = value
        return result
    return None


def collect_static_assignments(tree: ast.Module) -> dict[str, Any]:
    names: dict[str, Any] = {}
    for statement in tree.body:
        if isinstance(statement, ast.Assign):
            value = simple_static_value(statement.value, names)
            if value is None:
                continue
            for target in statement.targets:
                if isinstance(target, ast.Name):
                    names[target.id] = value
        elif isinstance(statement, ast.AnnAssign) and statement.value is not None:
            value = simple_static_value(statement.value, names)
            if isinstance(statement.target, ast.Name) and value is not None:
                names[statement.target.id] = value
    return names


SECRET_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("private_key_header", re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
    ("huggingface_token", re.compile(r"\bhf_[A-Za-z0-9]{20,}\b")),
    ("openai_style_key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    (
        "credential_assignment",
        re.compile(
            r"(?i)\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|password|passwd|secret)"
            r"\s*[:=]\s*['\"]([^'\"\n]{8,})['\"]"
        ),
    ),
    ("bearer_token", re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]{20,}={0,2}")),
    (
        "credential_url",
        re.compile(r"(?i)\b(?:https?|ssh)://[^\s/:@]+:[^\s/@]+@[^\s]+"),
    ),
)


def secret_findings(text: str, version: Mapping[str, Any]) -> Iterator[Mapping[str, Any]]:
    for line_number, line in enumerate(text.splitlines(), 1):
        for rule_id, pattern in SECRET_RULES:
            for match in pattern.finditer(line):
                candidate = match.group(1) if match.lastindex else match.group(0)
                yield {
                    "version_id": version["version_id"],
                    "original_path": version["original_path"],
                    "recovered_path": version["recovered_path"],
                    "rule_id": rule_id,
                    "line": line_number,
                    "candidate_length": len(candidate),
                    "candidate_sha256": sha256_text(candidate),
                    "candidate_redacted": True,
                }


DANGEROUS_CALLS: Mapping[str, tuple[str, str]] = {
    "eval": ("dynamic_execution", "high"),
    "exec": ("dynamic_execution", "high"),
    "compile": ("dynamic_compilation", "high"),
    "__import__": ("dynamic_import", "high"),
    "importlib.import_module": ("dynamic_import", "high"),
    "os.system": ("shell_execution", "high"),
    "os.popen": ("shell_execution", "high"),
    "subprocess.run": ("process_execution", "high"),
    "subprocess.call": ("process_execution", "high"),
    "subprocess.check_call": ("process_execution", "high"),
    "subprocess.check_output": ("process_execution", "high"),
    "subprocess.Popen": ("process_execution", "high"),
    "shutil.rmtree": ("recursive_delete", "critical"),
    "os.remove": ("delete", "high"),
    "os.unlink": ("delete", "high"),
    "os.rmdir": ("delete", "high"),
    "os.rename": ("move_or_replace", "medium"),
    "os.replace": ("move_or_replace", "medium"),
    "os.chmod": ("permission_change", "medium"),
    "os.chown": ("ownership_change", "high"),
    "socket.socket": ("network_access", "high"),
    "urllib.request.urlopen": ("network_access", "high"),
    "requests.get": ("network_access", "high"),
    "requests.post": ("network_access", "high"),
}


def static_path_strings(value: Any) -> Iterator[str]:
    """Yield path-shaped strings from a statically resolved value.

    This is deliberately structural: source strings passed to ``write_text``
    are data, not destinations, and must never be treated as paths merely
    because their content mentions ``outputs/raw``.
    """

    if isinstance(value, str):
        if "/" in value or value.endswith((".jsonl", ".py")):
            yield value
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            yield from static_path_strings(item)
    elif isinstance(value, dict):
        for item in value.values():
            yield from static_path_strings(item)


def call_literal_paths(node: ast.Call, names: Mapping[str, Any]) -> list[str]:
    values: list[str] = []
    for argument in node.args:
        values.extend(static_path_strings(simple_static_value(argument, names)))
    for keyword in node.keywords:
        values.extend(static_path_strings(simple_static_value(keyword.value, names)))
    return sorted(set(values))


def collect_static_path_names(tree: ast.Module) -> set[str]:
    """Identify module-level names whose expressions construct ``Path`` objects."""

    path_names: set[str] = set()

    def is_path_expression(node: ast.AST) -> bool:
        if isinstance(node, ast.Call):
            return qualified_name(node.func) in {"Path", "pathlib.Path"}
        if isinstance(node, ast.Name):
            return node.id in path_names
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            return is_path_expression(node.left)
        return False

    for statement in tree.body:
        if isinstance(statement, ast.Assign) and is_path_expression(statement.value):
            path_names.update(
                target.id for target in statement.targets if isinstance(target, ast.Name)
            )
        elif (
            isinstance(statement, ast.AnnAssign)
            and isinstance(statement.target, ast.Name)
            and statement.value is not None
            and is_path_expression(statement.value)
        ):
            path_names.add(statement.target.id)
    return path_names


def static_path_receiver(
    node: ast.AST, names: Mapping[str, Any], path_names: set[str]
) -> str | None:
    """Resolve a receiver only when the AST establishes that it is Path-like."""

    if isinstance(node, ast.Call) and qualified_name(node.func) in {"Path", "pathlib.Path"}:
        value = simple_static_value(node, names)
        return value if isinstance(value, str) else None
    if isinstance(node, ast.Name) and node.id in path_names:
        value = simple_static_value(node, names)
        return value if isinstance(value, str) else None
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        value = simple_static_value(node, names)
        return value if isinstance(value, str) else None
    return None


def dangerous_findings(
    tree: ast.Module, text: str, version: Mapping[str, Any]
) -> Iterator[Mapping[str, Any]]:
    names = collect_static_assignments(tree)
    path_names = collect_static_path_names(tree)
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
    for imported in sorted(imported_roots & {"subprocess", "socket", "requests", "urllib", "shutil"}):
        yield {
            "version_id": version["version_id"],
            "original_path": version["original_path"],
            "recovered_path": version["recovered_path"],
            "rule_id": "sensitive_import",
            "severity": "info",
            "line": 1,
            "symbol": imported,
            "literal_paths": [],
        }

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = qualified_name(node.func)
        paths = call_literal_paths(node, names)
        rule: tuple[str, str] | None = DANGEROUS_CALLS.get(name or "")
        if isinstance(node.func, ast.Attribute) and node.func.attr in {
            "write_text",
            "write_bytes",
            "unlink",
            "rmdir",
            "rename",
            "replace",
            "chmod",
        }:
            receiver = static_path_receiver(node.func.value, names, path_names)
            if node.func.attr in {"write_text", "write_bytes"}:
                rule = ("file_write", "medium")
                paths = [receiver] if receiver else []
            elif node.func.attr in {"unlink", "rmdir"}:
                rule = ("delete", "high")
                paths = [receiver] if receiver else []
            elif node.func.attr in {"rename", "replace"}:
                # ``str.replace`` is overwhelmingly common in generators and
                # is not a filesystem mutation.  Only Path-like receivers are
                # classified here.
                if receiver is None:
                    rule = None
                else:
                    rule = ("move_or_replace", "medium")
                    target = (
                        simple_static_value(node.args[0], names) if node.args else None
                    )
                    paths = sorted(
                        set([receiver] + list(static_path_strings(target)))
                    )
            else:
                rule = ("permission_change", "medium")
                paths = [receiver] if receiver else []
        if name == "open":
            mode = literal_string(node.args[1]) if len(node.args) > 1 else "r"
            for keyword in node.keywords:
                if keyword.arg == "mode":
                    mode = literal_string(keyword.value)
            if isinstance(mode, str) and any(flag in mode for flag in "wax+"):
                rule = ("file_write", "medium")
                target = simple_static_value(node.args[0], names) if node.args else None
                paths = sorted(set(static_path_strings(target)))
        if rule is None:
            continue
        rule_id, severity = rule
        if rule_id in {
            "file_write",
            "delete",
            "move_or_replace",
            "recursive_delete",
            "permission_change",
            "ownership_change",
        } and any("outputs/raw" in path for path in paths):
            rule_id = "raw_dataset_mutation"
            severity = "critical"
        yield {
            "version_id": version["version_id"],
            "original_path": version["original_path"],
            "recovered_path": version["recovered_path"],
            "rule_id": rule_id,
            "severity": severity,
            "line": getattr(node, "lineno", None),
            "symbol": name,
            "literal_paths": paths,
        }

    # These are references in source text, which may itself be emitted as a
    # training record.  They are provenance/review indicators, not evidence
    # that the recovered program invokes the command or mutates the path.
    shell_patterns = (
        ("shell_recursive_delete_reference", "info", re.compile(r"\brm\s+-[^\n]*r[^\n]*f")),
        ("git_remote_mutation_reference", "info", re.compile(r"\bgit\s+(?:push|fetch|pull|clone)\b")),
        ("network_command_reference", "info", re.compile(r"\b(?:curl|wget|ssh|scp|rsync)\b")),
        ("raw_dataset_path_reference", "info", re.compile(r"outputs/raw/")),
    )
    for rule_id, severity, pattern in shell_patterns:
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            yield {
                "version_id": version["version_id"],
                "original_path": version["original_path"],
                "recovered_path": version["recovered_path"],
                "rule_id": rule_id,
                "severity": severity,
                "line": line,
                "symbol": None,
                "literal_paths": [],
            }


def static_jsonl_write_destinations(tree: ast.Module) -> list[str]:
    """Resolve JSONL destinations of explicit write-capable AST calls."""

    names = collect_static_assignments(tree)
    path_names = collect_static_path_names(tree)
    destinations: set[str] = set()

    def add_value(value: Any) -> None:
        if isinstance(value, str):
            cleaned = clean_jsonl_candidate(value)
            if cleaned is not None:
                destinations.add(cleaned)

    def call_mode(node: ast.Call, positional_index: int = 1) -> str | None:
        mode = (
            simple_static_value(node.args[positional_index], names)
            if len(node.args) > positional_index
            else None
        )
        for keyword in node.keywords:
            if keyword.arg == "mode":
                mode = simple_static_value(keyword.value, names)
        return mode if isinstance(mode, str) else None

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = qualified_name(node.func) or ""
        if name in {"open", "io.open", "gzip.open", "bz2.open", "lzma.open"}:
            mode = call_mode(node)
            if isinstance(mode, str) and any(flag in mode for flag in "wax+"):
                if node.args:
                    add_value(simple_static_value(node.args[0], names))
            continue
        if name in {"shutil.copy", "shutil.copy2", "shutil.copyfile", "os.rename", "os.replace"}:
            if len(node.args) > 1:
                add_value(simple_static_value(node.args[1], names))
            continue
        if isinstance(node.func, ast.Name) and node.func.id in {
            "write_jsonl",
            "emit_jsonl",
            "save_jsonl",
        }:
            for argument in node.args[:2]:
                add_value(simple_static_value(argument, names))
        if not isinstance(node.func, ast.Attribute):
            continue
        receiver = static_path_receiver(node.func.value, names, path_names)
        if node.func.attr in {"write_text", "write_bytes", "touch"}:
            add_value(receiver)
        elif node.func.attr == "open":
            mode = call_mode(node, positional_index=0)
            if isinstance(mode, str) and any(flag in mode for flag in "wax+"):
                add_value(receiver)
        elif node.func.attr in {"rename", "replace"} and node.args:
            if receiver is not None:
                add_value(simple_static_value(node.args[0], names))
    return sorted(destinations)


FACTORY_PREFIXES: Mapping[str, str] = {
    "ttf": "thalamic-trajectory-factory",
    "nelb": "neuromorphic-event-language-bridge",
    "maos": "multi-agent-ouroboros-swarm",
    "ffpc": "failure-as-fuel-preference-cascade",
    "actf": "agentic-coding-trajectory-factory",
}

RECORD_ID_RE = re.compile(
    r"\b(?:ttf|nelb|maos|ffpc|actf)(?:[-_][A-Za-z0-9][A-Za-z0-9_.:-]*){1,8}\b",
    re.IGNORECASE,
)


def prompt_declarations(prompt: str) -> Mapping[str, Any]:
    factory_values = set(
        re.findall(
            r"(?im)(?:^|\s)factory\s*(?:[:=]|`)\s*`?([a-z0-9][a-z0-9-]{2,})",
            prompt,
        )
    )
    run_labels = set(re.findall(r"(?im)^\s*run\s+label\s*:\s*`?([^\n`]+)", prompt))
    generators = set(re.findall(r"(?im)^\s*generator\s*:\s*`?([^\n`]+)", prompt))
    rounds = set(re.findall(r"(?im)^\s*round(?:\s+n)?\s*:\s*(\d+)", prompt))
    quotas = set(re.findall(r"(?im)^\s*quota(?:\s+q)?\s*:\s*(\d+)", prompt))
    if not quotas:
        quotas.update(re.findall(r"(?im)\bexactly\s+(\d+)\s+(?:records|pairs|artifacts)", prompt))
    id_values = sorted(set(RECORD_ID_RE.findall(prompt)))
    return {
        "factory": sorted(value.strip() for value in factory_values),
        "run_label": sorted(value.strip() for value in run_labels),
        "generator": sorted(value.strip() for value in generators),
        "round": sorted(int(value) for value in rounds),
        "expected_output_count": sorted(int(value) for value in quotas),
        "record_identifiers": id_values,
        "jsonl_expressions": jsonl_expressions(prompt),
        "research_only": "research_only" in prompt or "research-only" in prompt,
        "project_training_policy_blocked": bool(
            re.search(r"project_training_policy[^\n]{0,80}blocked", prompt, re.IGNORECASE)
        ),
        "rm_793": "RM-793" in prompt,
    }


def infer_path_factory(original_path: str) -> str | None:
    lower = original_path.casefold()
    for prefix, factory in FACTORY_PREFIXES.items():
        if re.search(rf"(?:^|[/_-]){re.escape(prefix)}(?:[/_-]|r\d|$)", lower):
            return factory
    return None


def infer_source_role(
    original_path: str, tree: ast.Module | None, output_paths: Sequence[str]
) -> str:
    basename = Path(original_path).name.casefold()
    if any(token in basename for token in ("scan", "audit", "check", "verify", "probe")):
        return "audit_or_validator"
    if any(token in basename for token in ("patch", "splice", "xform")):
        return "patch_helper"
    if any(token in basename for token in ("record", "recs", "helper", "head", "tail", "prefix", "suffix", "mid")):
        return "source_fragment_or_helper"
    if any(token in basename for token in ("gen", "build", "assemble", "mill", "loop")):
        return "generator_or_assembler" if output_paths else "generator_helper"
    if tree is not None:
        function_names = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
        if "main" in function_names and output_paths:
            return "generator_or_assembler"
    return "unknown_python_utility"


def static_provenance(
    tree: ast.Module | None,
    text: str,
    version: Mapping[str, Any],
    agent_prompts: Sequence[Mapping[str, Any]],
) -> Mapping[str, Any]:
    strings: list[str] = []
    names: dict[str, Any] = {}
    dict_values: defaultdict[str, set[str]] = defaultdict(set)
    if tree is not None:
        names = collect_static_assignments(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                strings.append(node.value)
            elif isinstance(node, ast.Dict):
                for key_node, value_node in zip(node.keys, node.values):
                    key = literal_string(key_node)
                    value = literal_string(value_node)
                    if key is not None and value is not None:
                        dict_values[key.casefold()].add(value)
    else:
        strings = re.findall(r"['\"]([^'\"\n]{1,500})['\"]", text)

    assignment_values: defaultdict[str, set[str]] = defaultdict(set)
    for name, value in names.items():
        if isinstance(value, str):
            assignment_values[name.casefold()].add(value)
    output_paths = sorted(
        {
            value
            for value in list(strings) + [v for v in names.values() if isinstance(v, str)]
            if isinstance(value, str) and value.endswith(".jsonl")
        }
    )
    output_paths.extend(
        path
        for path in jsonl_expressions(text)
        if path not in output_paths
    )
    output_paths = sorted(set(output_paths))

    factory_values = set(dict_values.get("factory", set()))
    for key in ("factory", "factory_slug", "factory_name"):
        factory_values.update(assignment_values.get(key, set()))
    inferred_factory = infer_path_factory(str(version["original_path"]))
    if inferred_factory:
        factory_values.add(inferred_factory)
    run_labels = set(dict_values.get("run_label", set()))
    run_labels.update(assignment_values.get("run_label", set()))
    generators = set(dict_values.get("generator", set()))
    generators.update(assignment_values.get("generator", set()))
    intended_uses = set(dict_values.get("intended_use", set()))
    intended_uses.update(assignment_values.get("intended_use", set()))
    training_policies = set(dict_values.get("project_training_policy", set()))
    training_policies.update(assignment_values.get("project_training_policy", set()))

    prompt_factories: set[str] = set()
    prompt_run_labels: set[str] = set()
    prompt_generators: set[str] = set()
    prompt_counts: set[int] = set()
    prompt_ids: set[str] = set()
    prompt_jsonl: set[str] = set()
    prompt_research_only = False
    prompt_training_blocked = False
    prompt_rm_793 = False
    for declaration in agent_prompts:
        prompt_factories.update(declaration["factory"])
        prompt_run_labels.update(declaration["run_label"])
        prompt_generators.update(declaration["generator"])
        prompt_counts.update(declaration["expected_output_count"])
        prompt_ids.update(declaration["record_identifiers"])
        prompt_jsonl.update(declaration["jsonl_expressions"])
        prompt_research_only = prompt_research_only or bool(declaration["research_only"])
        prompt_training_blocked = prompt_training_blocked or bool(
            declaration["project_training_policy_blocked"]
        )
        prompt_rm_793 = prompt_rm_793 or bool(declaration["rm_793"])

    record_ids = sorted(set(RECORD_ID_RE.findall("\n".join(strings))))
    source_research_only = "research_only" in intended_uses or "research_only" in text
    source_training_blocked = "blocked" in training_policies or bool(
        re.search(r"project_training_policy[^\n]{0,160}['\"]blocked['\"]", text)
    )
    effective_policy = (
        "research_only_training_blocked"
        if (source_research_only or prompt_research_only)
        and (source_training_blocked or prompt_training_blocked)
        else "research_only_training_policy_unresolved"
        if source_research_only or prompt_research_only
        else "training_blocked_intended_use_unresolved"
        if source_training_blocked or prompt_training_blocked
        else "unknown"
    )
    return {
        "version_id": version["version_id"],
        "original_path": version["original_path"],
        "recovered_path": version["recovered_path"],
        "role": infer_source_role(str(version["original_path"]), tree, output_paths),
        "source": {
            "factory": sorted(factory_values),
            "run_label": sorted(run_labels),
            "generator": sorted(generators),
            "intended_use": sorted(intended_uses),
            "project_training_policy": sorted(training_policies),
            "output_jsonl": output_paths,
            "record_identifiers": record_ids,
            "record_identifier_count": len(record_ids),
        },
        "prompt": {
            "factory": sorted(prompt_factories),
            "run_label": sorted(prompt_run_labels),
            "generator": sorted(prompt_generators),
            "expected_output_count": sorted(prompt_counts),
            "jsonl": sorted(prompt_jsonl),
            "record_identifiers": sorted(prompt_ids),
            "research_only": prompt_research_only,
            "project_training_policy_blocked": prompt_training_blocked,
            "rm_793": prompt_rm_793,
        },
        "effective_policy_status": effective_policy,
        "policy_evidence": {
            "source_research_only": source_research_only,
            "source_training_blocked": source_training_blocked,
            "prompt_research_only": prompt_research_only,
            "prompt_training_blocked": prompt_training_blocked,
            "prompt_rm_793": prompt_rm_793,
        },
        "conflicts": {
            "factory": len(factory_values | prompt_factories) > 1,
            "run_label": len(run_labels | prompt_run_labels) > 1,
            "generator": len(generators | prompt_generators) > 1,
            "expected_output_count": len(prompt_counts) > 1,
        },
    }


def terminal_count_evidence(log_path: Path) -> list[Mapping[str, Any]]:
    if not log_path.is_file() or log_path.is_symlink():
        return []
    text = log_path.read_text(encoding="utf-8", errors="replace")
    evidence: list[Mapping[str, Any]] = []
    patterns = (
        (
            "wc_l",
            re.compile(r"(?m)^\s*(\d+)\s+(/tmp/[^\s]+\.jsonl)\s*$"),
        ),
        (
            "wrote_count",
            re.compile(
                r"(?im)\bwrote\b[^\n]{0,160}?\b(\d+)\s+(?:records?|lines?|pairs?|artifacts?)\b"
            ),
        ),
        (
            "records_count",
            re.compile(r"(?im)\b(?:records?|lines?)\s*[:=]\s*(\d+)\b"),
        ),
    )
    for rule_id, pattern in patterns:
        for match in pattern.finditer(text):
            count = int(match.group(1))
            output = match.group(2) if match.lastindex and match.lastindex >= 2 else None
            evidence.append(
                {
                    "rule_id": rule_id,
                    "count": count,
                    "output_jsonl": output,
                    "terminal_log_path": str(log_path),
                    "terminal_log_sha256": sha256_file(log_path),
                }
            )
    unique: dict[tuple[Any, ...], Mapping[str, Any]] = {}
    for item in evidence:
        key = (item["rule_id"], item["count"], item["output_jsonl"])
        unique[key] = item
    return list(unique.values())


def journal_terminal_output_evidence_index(
    nodes: Sequence[SessionNode],
) -> dict[str, list[Mapping[str, Any]]]:
    """Index count evidence embedded in terminal rawOutput journal records."""

    index: dict[str, list[Mapping[str, Any]]] = {}
    for node in nodes:
        for call in iter_tool_calls(node.session_id):
            if not call.raw_output_count_evidence:
                continue
            event_id = f"{call.session_id}:{call.tool_call_id}"
            index[event_id] = [
                {
                    **record,
                    "terminal_event_id": event_id,
                    "journal_path": call.journal_path,
                    "journal_line": call.journal_line,
                    "tool_status": call.status,
                    "exit_code": call.exit_code,
                    "command_succeeded": call.command_succeeded,
                    "raw_output_sha256": call.raw_output_sha256,
                }
                for record in call.raw_output_count_evidence
            ]
    return index


def build_generator_output_map(
    reconstruction: Mapping[str, Any],
    provenance_by_version: Mapping[str, Mapping[str, Any]],
    metadata_by_session: Mapping[str, Mapping[str, Any]],
    terminal_output_evidence: Mapping[str, Sequence[Mapping[str, Any]]] | None = None,
    write_destinations_by_version: Mapping[str, Sequence[str]] | None = None,
) -> list[Mapping[str, Any]]:
    if terminal_output_evidence is None:
        terminal_output_evidence = {}
    if write_destinations_by_version is None:
        write_destinations_by_version = {}
    terminal_by_source: defaultdict[str, list[Mapping[str, Any]]] = defaultdict(list)
    terminal_by_session: defaultdict[str, list[Mapping[str, Any]]] = defaultdict(list)
    terminal_inventory_path = RECOVERY_ROOT / "inventory" / "terminal-mutations.jsonl"
    with terminal_inventory_path.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            command = record.get("command")
            if not isinstance(command, str):
                continue
            terminal_by_session[str(record.get("session_id"))].append(record)
            for source in literal_tmp_py_paths(command):
                if re.search(
                    rf"\bpython(?:3(?:\.\d+)?)?\s+['\"]?{re.escape(source)}(?:['\"]|\s|$)",
                    command,
                ):
                    terminal_by_source[source].append(record)

    mappings: list[Mapping[str, Any]] = []
    for entry in reconstruction["entries"]:
        versions = entry.get("versions") or []
        if not versions:
            continue
        latest = versions[-1]
        provenance = provenance_by_version.get(latest["version_id"], {})
        role = provenance.get("role")
        if role not in {"generator_or_assembler", "generator_helper", "source_fragment_or_helper"}:
            continue
        original_path = str(entry["original_path"])
        terminal_records = terminal_by_source.get(original_path, [])
        terminal_jsonl: set[str] = set()
        observed_counts: list[Mapping[str, Any]] = []
        execution_event_ids: list[str] = []
        for terminal_record in terminal_records:
            terminal_event_id = str(terminal_record["event_id"])
            execution_event_ids.append(terminal_event_id)
            terminal_jsonl.update(terminal_record.get("related_jsonl_expressions") or [])
            observed_counts.extend(terminal_output_evidence.get(terminal_event_id, []))
            for log_name in terminal_record.get("terminal_logs") or []:
                observed_counts.extend(terminal_count_evidence(Path(log_name)))

        agent_prompts = []
        for agent_id in entry.get("agent_ids") or []:
            meta = metadata_by_session.get(agent_id, {})
            prompt = meta.get("prompt")
            if isinstance(prompt, str):
                agent_prompts.append(prompt_declarations(prompt))
        expected_counts = sorted(
            {
                count
                for declaration in agent_prompts
                for count in declaration["expected_output_count"]
            }
        )
        source_info = provenance.get("source") or {}
        prompt_info = provenance.get("prompt") or {}
        raw_source_outputs = set(source_info.get("output_jsonl") or [])
        source_write_outputs = set(
            write_destinations_by_version.get(str(latest["version_id"]), [])
        )
        raw_prompt_outputs = set(prompt_info.get("jsonl") or [])
        raw_observed_outputs = {
            str(item["output_jsonl"])
            for item in observed_counts
            if item.get("output_jsonl")
        }
        raw_output_candidates = (
            source_write_outputs
            | raw_prompt_outputs
            | terminal_jsonl
            | raw_observed_outputs
        )
        output_jsonl = sorted(
            {
                cleaned
                for value in raw_output_candidates
                if (cleaned := clean_jsonl_candidate(value)) is not None
            }
        )
        discarded_output_candidates = [
            {
                "sha256": sha256_text(str(value)),
                "bytes": len(str(value).encode("utf-8")),
                "reason": "not a conservative whitespace-free local JSONL path or glob",
            }
            for value in sorted(raw_output_candidates)
            if clean_jsonl_candidate(value) is None
        ]
        # A count check is often a separate terminal call after generator
        # execution.  Associate it only when a JSONL expression in that call
        # matches a source/prompt/output candidate exactly or by basename and
        # belongs to one of this lineage's child sessions.
        candidate_output_names = {Path(path).name for path in output_jsonl}
        for agent_id in entry.get("agent_ids") or []:
            for terminal_record in terminal_by_session.get(str(agent_id), []):
                if not terminal_record.get("command_succeeded"):
                    continue
                terminal_event_id = str(terminal_record.get("event_id"))
                event_evidence = terminal_output_evidence.get(terminal_event_id, [])
                if not event_evidence:
                    continue
                mentioned_paths = set(
                    cleaned
                    for path in terminal_record.get("related_jsonl_expressions") or []
                    if (cleaned := clean_jsonl_candidate(path)) is not None
                )
                mentioned_paths.update(
                    cleaned
                    for item in event_evidence
                    if item.get("output_jsonl")
                    and (
                        cleaned := clean_jsonl_candidate(item.get("output_jsonl"))
                    )
                    is not None
                )
                if not (
                    set(output_jsonl) & mentioned_paths
                    or candidate_output_names
                    & {Path(path).name for path in mentioned_paths}
                ):
                    continue
                observed_counts.extend(event_evidence)
                execution_event_ids.append(terminal_event_id)
        unique_observed_counts: dict[tuple[Any, ...], Mapping[str, Any]] = {}
        for item in observed_counts:
            key = (
                item.get("terminal_event_id"),
                item.get("rule_id"),
                item.get("count"),
                item.get("output_jsonl"),
            )
            unique_observed_counts[key] = item
        observed_counts = list(unique_observed_counts.values())
        record_ids = sorted(
            set(source_info.get("record_identifiers") or [])
            | set(prompt_info.get("record_identifiers") or [])
        )
        declared_factory_values = sorted(
            set(source_info.get("factory") or []) | set(prompt_info.get("factory") or [])
        )
        canonical_factory_values: set[str] = set()
        for declared in declared_factory_values:
            lowered_declared = str(declared).casefold()
            for prefix, canonical in FACTORY_PREFIXES.items():
                if lowered_declared == prefix or canonical in lowered_declared:
                    canonical_factory_values.add(canonical)
        inferred_factory = infer_path_factory(original_path)
        if inferred_factory:
            canonical_factory_values.add(inferred_factory)
        factory_values = sorted(canonical_factory_values)
        run_labels = sorted(
            set(source_info.get("run_label") or []) | set(prompt_info.get("run_label") or [])
        )
        generators = sorted(
            set(source_info.get("generator") or []) | set(prompt_info.get("generator") or [])
        )
        mapping_evidence = []
        if source_write_outputs:
            mapping_evidence.append("source_write_destination")
        if any(clean_jsonl_candidate(value) for value in raw_prompt_outputs):
            mapping_evidence.append("child_prompt")
        if any(clean_jsonl_candidate(value) for value in terminal_jsonl):
            mapping_evidence.append("terminal_command")
        if observed_counts:
            mapping_evidence.append("terminal_output")
        mappings.append(
            {
                "original_path": original_path,
                "path_key": entry["path_key"],
                "reconstruction_classification": entry["classification"],
                "latest_version_id": latest["version_id"],
                "latest_sha256": latest["sha256"],
                "role": role,
                "generator_family": factory_values,
                "dataset_category": factory_values,
                "declared_generator_family_values": declared_factory_values,
                "run_label": run_labels,
                "generator": generators,
                "agent_ids": entry.get("agent_ids") or [],
                "child_agent_provenance": [
                    {
                        "agent_id": agent_id,
                        "description": metadata_by_session.get(agent_id, {}).get("description"),
                        "status": metadata_by_session.get(agent_id, {}).get("status"),
                        "effective_model_id": metadata_by_session.get(agent_id, {}).get(
                            "effective_model_id"
                        ),
                    }
                    for agent_id in entry.get("agent_ids") or []
                ],
                "output_jsonl": output_jsonl,
                "source_jsonl_write_destinations": sorted(source_write_outputs),
                "source_jsonl_references": sorted(
                    {
                        cleaned
                        for value in raw_source_outputs
                        if (cleaned := clean_jsonl_candidate(value)) is not None
                    }
                ),
                "discarded_output_jsonl_candidate_count": len(
                    discarded_output_candidates
                ),
                "discarded_output_jsonl_candidates": discarded_output_candidates,
                "record_identifiers": record_ids,
                "record_identifier_count": len(record_ids),
                "expected_output_count": expected_counts,
                "observed_output_count_evidence": observed_counts,
                "execution_event_ids": sorted(set(execution_event_ids)),
                "mapping_evidence": mapping_evidence,
                "mapping_confidence": (
                    "corroborated"
                    if len(mapping_evidence) >= 2
                    else "single_source"
                    if mapping_evidence
                    else "unmapped"
                ),
                "research_or_training_policy_status": provenance.get(
                    "effective_policy_status", "unknown"
                ),
                "policy_evidence": provenance.get("policy_evidence", {}),
                "provenance_conflicts": provenance.get("conflicts", {}),
            }
        )
    return mappings


def validate() -> None:
    ensure_recovery_boundary()
    reconstruction_path = RECOVERY_ROOT / "manifest" / "reconstruction-manifest.json"
    if not reconstruction_path.exists():
        raise RecoveryError("reconstruction phase must complete before validation")
    reconstruction = read_json(reconstruction_path)
    nodes, _ = discover_session_graph()
    metadata_by_session = session_metadata_by_id(nodes)

    syntax_records: list[Mapping[str, Any]] = []
    secrets: list[Mapping[str, Any]] = []
    dangerous: list[Mapping[str, Any]] = []
    provenance_records: list[Mapping[str, Any]] = []
    provenance_by_version: dict[str, Mapping[str, Any]] = {}
    exact_groups: defaultdict[str, list[Mapping[str, Any]]] = defaultdict(list)
    ast_groups: defaultdict[str, list[Mapping[str, Any]]] = defaultdict(list)
    hash_lines: list[str] = []
    validation_index: dict[str, Mapping[str, Any]] = {}

    for entry in reconstruction["entries"]:
        agent_prompt_declarations = [
            prompt_declarations(str(metadata_by_session.get(agent_id, {}).get("prompt", "")))
            for agent_id in entry.get("agent_ids") or []
        ]
        for version in entry.get("versions") or []:
            recovered_path = Path(version["recovered_path"])
            data = recovered_path.read_bytes()
            digest = sha256_bytes(data)
            if digest != version["sha256"]:
                raise RecoveryError(
                    f"recovered source hash drift: {recovered_path}: {digest} != {version['sha256']}"
                )
            relative = str(recovered_path.relative_to(RECOVERY_ROOT))
            hash_lines.append(f"{digest}  {relative}")
            exact_groups[digest].append(
                {
                    "version_id": version["version_id"],
                    "original_path": version["original_path"],
                    "recovered_path": version["recovered_path"],
                }
            )
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError as exc:
                syntax_record = {
                    "version_id": version["version_id"],
                    "original_path": version["original_path"],
                    "recovered_path": version["recovered_path"],
                    "status": "decode_error",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "line": None,
                    "offset": None,
                }
                syntax_records.append(syntax_record)
                validation_index[version["version_id"]] = {
                    "syntax_status": "decode_error",
                    "secret_finding_count": 0,
                    "dangerous_finding_count": 0,
                    "normalized_ast_sha256": None,
                }
                continue

            tree: ast.Module | None
            try:
                tree = ast.parse(text, filename=str(recovered_path), mode="exec")
            except SyntaxError as exc:
                tree = None
                syntax_record = {
                    "version_id": version["version_id"],
                    "original_path": version["original_path"],
                    "recovered_path": version["recovered_path"],
                    "status": "syntax_error",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "line": exc.lineno,
                    "offset": exc.offset,
                }
                normalized_ast_sha256 = None
            else:
                normalized = ast.dump(tree, annotate_fields=True, include_attributes=False)
                normalized_ast_sha256 = sha256_text(normalized)
                ast_groups[normalized_ast_sha256].append(
                    {
                        "version_id": version["version_id"],
                        "original_path": version["original_path"],
                        "recovered_path": version["recovered_path"],
                    }
                )
                syntax_record = {
                    "version_id": version["version_id"],
                    "original_path": version["original_path"],
                    "recovered_path": version["recovered_path"],
                    "status": "parse_ok",
                    "error_type": None,
                    "error": None,
                    "line": None,
                    "offset": None,
                    "normalized_ast_sha256": normalized_ast_sha256,
                }
            syntax_records.append(syntax_record)
            version_secrets = list(secret_findings(text, version))
            version_dangerous = list(dangerous_findings(tree, text, version)) if tree else []
            secrets.extend(version_secrets)
            dangerous.extend(version_dangerous)
            provenance = static_provenance(
                tree,
                text,
                version,
                agent_prompt_declarations,
            )
            provenance_records.append(provenance)
            provenance_by_version[version["version_id"]] = provenance
            validation_index[version["version_id"]] = {
                "syntax_status": syntax_record["status"],
                "secret_finding_count": len(version_secrets),
                "dangerous_finding_count": len(version_dangerous),
                "dangerous_critical_count": sum(
                    finding["severity"] == "critical" for finding in version_dangerous
                ),
                "normalized_ast_sha256": normalized_ast_sha256,
            }

    reports_dir = RECOVERY_ROOT / "reports"
    manifest_dir = RECOVERY_ROOT / "manifest"
    write_jsonl_fresh(reports_dir / "syntax.jsonl", syntax_records)
    write_jsonl_fresh(reports_dir / "secrets.jsonl", secrets)
    write_jsonl_fresh(reports_dir / "dangerous-operations.jsonl", dangerous)
    write_jsonl_fresh(reports_dir / "provenance.jsonl", provenance_records)
    write_text_fresh(reports_dir / "hashes.sha256", "\n".join(sorted(hash_lines)) + "\n")

    duplicates = {
        "schema_version": SCHEMA_VERSION,
        "exact_duplicate_groups": [
            {"sha256": digest, "count": len(items), "members": items}
            for digest, items in sorted(exact_groups.items())
            if len(items) > 1
        ],
        "normalized_ast_duplicate_groups": [
            {"normalized_ast_sha256": digest, "count": len(items), "members": items}
            for digest, items in sorted(ast_groups.items())
            if len(items) > 1
        ],
    }
    write_json_fresh(reports_dir / "duplicates.json", duplicates)

    output_map = build_generator_output_map(
        reconstruction,
        provenance_by_version,
        metadata_by_session,
    )
    write_jsonl_fresh(reports_dir / "generator-output-map.jsonl", output_map)

    syntax_counts = Counter(record["status"] for record in syntax_records)
    danger_counts = Counter(record["severity"] for record in dangerous)
    policy_counts = Counter(
        record["research_or_training_policy_status"] for record in output_map
    )
    validation_manifest = {
        "schema_version": SCHEMA_VERSION,
        "top_level_session_id": PARENT_SESSION_ID,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "validation_policy": {
            "recovered_programs_executed": False,
            "recovered_modules_imported": False,
            "syntax_method": "ast.parse only",
            "secret_candidates_redacted": True,
            "duplicate_methods": ["exact_sha256", "normalized_ast_sha256"],
            "static_validation_is_not_training_admission": True,
        },
        "version_count": len(syntax_records),
        "syntax_counts": dict(syntax_counts),
        "secret_finding_count": len(secrets),
        "versions_with_secret_findings": len(
            {record["version_id"] for record in secrets}
        ),
        "dangerous_finding_count": len(dangerous),
        "dangerous_severity_counts": dict(danger_counts),
        "versions_with_dangerous_findings": len(
            {record["version_id"] for record in dangerous}
        ),
        "exact_duplicate_group_count": len(duplicates["exact_duplicate_groups"]),
        "normalized_ast_duplicate_group_count": len(
            duplicates["normalized_ast_duplicate_groups"]
        ),
        "generator_output_mapping_count": len(output_map),
        "generator_output_mapping_confidence_counts": dict(
            Counter(record["mapping_confidence"] for record in output_map)
        ),
        "generator_policy_status_counts": dict(policy_counts),
        "validation_index": validation_index,
    }
    write_json_fresh(manifest_dir / "validation-index.json", validation_manifest)
    summary = {
        key: validation_manifest[key]
        for key in (
            "version_count",
            "syntax_counts",
            "secret_finding_count",
            "versions_with_secret_findings",
            "dangerous_finding_count",
            "dangerous_severity_counts",
            "versions_with_dangerous_findings",
            "exact_duplicate_group_count",
            "normalized_ast_duplicate_group_count",
            "generator_output_mapping_count",
            "generator_output_mapping_confidence_counts",
            "generator_policy_status_counts",
        )
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


def refine_dangerous_validation() -> None:
    """Regenerate the operation scan with destination-aware AST classification.

    The original validation report is retained as an immutable first-pass,
    deliberately broad screen.  This pass separates Path destinations from
    source/data strings and records the refinement policy explicitly.
    """

    ensure_recovery_boundary()
    reconstruction_path = RECOVERY_ROOT / "manifest" / "reconstruction-manifest.json"
    validation_path = RECOVERY_ROOT / "manifest" / "validation-index.json"
    if not reconstruction_path.exists() or not validation_path.exists():
        raise RecoveryError("reconstruction and initial validation must precede refinement")
    reconstruction = read_json(reconstruction_path)
    initial_validation = read_json(validation_path)

    dangerous: list[Mapping[str, Any]] = []
    version_index: dict[str, Mapping[str, Any]] = {}
    parsed_version_count = 0
    skipped_syntax_version_count = 0
    for entry in reconstruction["entries"]:
        for version in entry.get("versions") or []:
            recovered_path = Path(version["recovered_path"])
            data = recovered_path.read_bytes()
            digest = sha256_bytes(data)
            if digest != version["sha256"]:
                raise RecoveryError(
                    f"recovered source hash drift: {recovered_path}: {digest} != {version['sha256']}"
                )
            try:
                text = data.decode("utf-8")
                tree = ast.parse(text, filename=str(recovered_path), mode="exec")
            except (UnicodeDecodeError, SyntaxError):
                skipped_syntax_version_count += 1
                version_findings: list[Mapping[str, Any]] = []
            else:
                parsed_version_count += 1
                version_findings = list(dangerous_findings(tree, text, version))
                dangerous.extend(version_findings)
            version_index[version["version_id"]] = {
                "finding_count": len(version_findings),
                "severity_counts": dict(
                    Counter(finding["severity"] for finding in version_findings)
                ),
                "rule_counts": dict(
                    Counter(finding["rule_id"] for finding in version_findings)
                ),
            }

    reports_dir = RECOVERY_ROOT / "reports"
    manifest_dir = RECOVERY_ROOT / "manifest"
    write_jsonl_fresh(reports_dir / "dangerous-operations.final.jsonl", dangerous)
    severity_counts = Counter(record["severity"] for record in dangerous)
    rule_counts = Counter(record["rule_id"] for record in dangerous)
    refined_manifest = {
        "schema_version": SCHEMA_VERSION,
        "top_level_session_id": PARENT_SESSION_ID,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "method": "destination-aware AST scan plus non-executing text references",
        "initial_report_retained": str(
            (reports_dir / "dangerous-operations.jsonl").relative_to(RECOVERY_ROOT)
        ),
        "refined_report": str(
            (reports_dir / "dangerous-operations.final.jsonl").relative_to(
                RECOVERY_ROOT
            )
        ),
        "refinement_notes": [
            "Path.write_text and Path.write_bytes content arguments are not destinations",
            "str.replace calls are excluded from filesystem move-or-replace findings",
            "raw dataset paths and command text occurring anywhere in source are informational references",
            "actual calls to execution, network, deletion, and write APIs retain action severity",
            "no recovered program was imported, compiled, or executed",
        ],
        "version_count": int(initial_validation["version_count"]),
        "parsed_version_count": parsed_version_count,
        "skipped_syntax_version_count": skipped_syntax_version_count,
        "finding_count": len(dangerous),
        "severity_counts": dict(severity_counts),
        "rule_counts": dict(rule_counts),
        "versions_with_findings": len(
            {record["version_id"] for record in dangerous}
        ),
        "versions_with_critical_findings": len(
            {
                record["version_id"]
                for record in dangerous
                if record["severity"] == "critical"
            }
        ),
        "versions_with_high_findings": len(
            {
                record["version_id"]
                for record in dangerous
                if record["severity"] == "high"
            }
        ),
        "version_index": version_index,
    }
    write_json_fresh(manifest_dir / "dangerous-validation-final.json", refined_manifest)
    print(
        json.dumps(
            {
                key: refined_manifest[key]
                for key in (
                    "version_count",
                    "parsed_version_count",
                    "skipped_syntax_version_count",
                    "finding_count",
                    "severity_counts",
                    "rule_counts",
                    "versions_with_critical_findings",
                    "versions_with_high_findings",
                )
            },
            indent=2,
            sort_keys=True,
        )
    )


def seal_journal_integrity() -> None:
    """Re-fingerprint the read-only evidence tree and compare it byte-for-byte."""

    ensure_recovery_boundary()
    inventory_dir = RECOVERY_ROOT / "inventory"
    before_path = inventory_dir / "journal-hashes.before.jsonl"
    if not before_path.exists():
        raise RecoveryError("inventory fingerprint is missing")
    nodes, _ = discover_session_graph()
    after_records = list(iter_evidence_paths(nodes))
    after_path = inventory_dir / "journal-hashes.after.jsonl"
    write_jsonl_fresh(after_path, after_records)

    before_records = list(read_jsonl(before_path))
    before_by_path = {
        str(record["path_relative_to_session_base"]): record
        for record in before_records
    }
    after_by_path = {
        str(record["path_relative_to_session_base"]): record
        for record in after_records
    }
    before_paths = set(before_by_path)
    after_paths = set(after_by_path)
    comparison_fields = (
        "session_id",
        "session_depth",
        "type",
        "size",
        "mode",
        "mtime_ns",
        "sha256",
        "link_target",
    )
    modified: list[Mapping[str, Any]] = []
    for relative_path in sorted(before_paths & after_paths):
        before = before_by_path[relative_path]
        after = after_by_path[relative_path]
        changes = {
            field: {"before": before.get(field), "after": after.get(field)}
            for field in comparison_fields
            if before.get(field) != after.get(field)
        }
        if changes:
            modified.append(
                {
                    "path_relative_to_session_base": relative_path,
                    "changes": changes,
                }
            )
    result = {
        "schema_version": SCHEMA_VERSION,
        "top_level_session_id": PARENT_SESSION_ID,
        "verified_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "comparison_fields": list(comparison_fields),
        "before_record_count": len(before_records),
        "after_record_count": len(after_records),
        "unchanged_record_count": len(before_paths & after_paths) - len(modified),
        "added_paths": sorted(after_paths - before_paths),
        "removed_paths": sorted(before_paths - after_paths),
        "modified_paths": modified,
        "added_path_count": len(after_paths - before_paths),
        "removed_path_count": len(before_paths - after_paths),
        "modified_path_count": len(modified),
        "all_evidence_unchanged": not (
            (after_paths - before_paths) or (before_paths - after_paths) or modified
        ),
        "recovery_process_wrote_session_base": False,
    }
    write_json_fresh(inventory_dir / "journal-integrity.json", result)
    print(json.dumps(result, indent=2, sort_keys=True))


def remap_generator_outputs() -> None:
    """Add output-count evidence from recorded terminal rawOutput bytes."""

    ensure_recovery_boundary()
    reconstruction = read_json(
        RECOVERY_ROOT / "manifest" / "reconstruction-manifest.json"
    )
    provenance_records = list(read_jsonl(RECOVERY_ROOT / "reports" / "provenance.jsonl"))
    provenance_by_version = {
        str(record["version_id"]): record for record in provenance_records
    }
    nodes, _ = discover_session_graph()
    metadata_by_session = session_metadata_by_id(nodes)
    output_evidence = journal_terminal_output_evidence_index(nodes)
    write_destinations_by_version: dict[str, list[str]] = {}
    for entry in reconstruction["entries"]:
        versions = entry.get("versions") or []
        if not versions:
            continue
        latest = versions[-1]
        recovered_path = Path(latest["recovered_path"])
        data = recovered_path.read_bytes()
        if sha256_bytes(data) != latest["sha256"]:
            raise RecoveryError(f"recovered source hash drift: {recovered_path}")
        try:
            tree = ast.parse(
                data.decode("utf-8"), filename=str(recovered_path), mode="exec"
            )
        except (UnicodeDecodeError, SyntaxError):
            continue
        write_destinations_by_version[str(latest["version_id"])] = (
            static_jsonl_write_destinations(tree)
        )
    mappings = build_generator_output_map(
        reconstruction,
        provenance_by_version,
        metadata_by_session,
        output_evidence,
        write_destinations_by_version,
    )
    target = RECOVERY_ROOT / "reports" / "generator-output-map.final.jsonl"
    if target.exists():
        replace_jsonl(target, mappings)
    else:
        write_jsonl_fresh(target, mappings)
    evidence_records = [
        item
        for mapping in mappings
        for item in mapping.get("observed_output_count_evidence") or []
    ]
    print(
        json.dumps(
            {
                "mapping_count": len(mappings),
                "terminal_events_with_count_evidence": len(output_evidence),
                "latest_versions_with_static_jsonl_write_destinations": sum(
                    bool(value) for value in write_destinations_by_version.values()
                ),
                "mappings_with_observed_output_count_evidence": sum(
                    bool(mapping.get("observed_output_count_evidence"))
                    for mapping in mappings
                ),
                "observed_output_count_evidence_records": len(evidence_records),
                "observed_count_values": dict(
                    Counter(str(item["count"]) for item in evidence_records)
                ),
                "target": str(target),
            },
            indent=2,
            sort_keys=True,
        )
    )


def markdown_cell(value: Any) -> str:
    """Render controlled evidence values safely inside a Markdown table cell."""

    return (
        str(value)
        .replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("\r", " ")
        .replace("\n", " ")
    )


def generator_candidate_path(original_path: str) -> bool:
    lowered = original_path.casefold()
    basename = Path(lowered).name
    return bool(
        any(marker in lowered for marker in FACTORY_PREFIXES)
        or re.search(
            r"(?:^|[_-])(?:gen(?:erator|erate)?|build|assemble|mill|emit|produce|write|make)(?:[_\-.]|$)",
            basename,
        )
    )


def write_final_deliverables(*, refresh: bool = False) -> None:
    """Create the review package without reading or executing dataset outputs."""

    ensure_recovery_boundary()
    inventory_dir = RECOVERY_ROOT / "inventory"
    manifest_dir = RECOVERY_ROOT / "manifest"
    reports_dir = RECOVERY_ROOT / "reports"
    write_json_output = replace_json if refresh else write_json_fresh
    write_jsonl_output = replace_jsonl if refresh else write_jsonl_fresh
    write_text_output = replace_text if refresh else write_text_fresh
    final_mapping_path = reports_dir / "generator-output-map.final.jsonl"

    required = {
        "inventory_summary": inventory_dir / "inventory-summary.json",
        "session_graph": inventory_dir / "session-graph.json",
        "journal_integrity": inventory_dir / "journal-integrity.json",
        "reconstruction": manifest_dir / "reconstruction-manifest.json",
        "validation": manifest_dir / "validation-index.json",
        "danger_final": manifest_dir / "dangerous-validation-final.json",
        "terminal_audit": reports_dir / "terminal-mutation-audit.json",
        "syntax": reports_dir / "syntax.jsonl",
        "secrets": reports_dir / "secrets.jsonl",
        "danger_findings": reports_dir / "dangerous-operations.final.jsonl",
        "provenance": reports_dir / "provenance.jsonl",
        "mappings": (
            final_mapping_path
            if final_mapping_path.exists()
            else reports_dir / "generator-output-map.jsonl"
        ),
        "duplicates": reports_dir / "duplicates.json",
        "reconstruction_events": reports_dir / "reconstruction-events.jsonl",
        "hashes": reports_dir / "hashes.sha256",
    }
    missing = [str(path) for path in required.values() if not path.exists()]
    if missing:
        raise RecoveryError(f"required recovery artifacts are missing: {missing}")

    inventory_summary = read_json(required["inventory_summary"])
    session_graph = read_json(required["session_graph"])
    journal_integrity = read_json(required["journal_integrity"])
    reconstruction = read_json(required["reconstruction"])
    validation = read_json(required["validation"])
    danger_final = read_json(required["danger_final"])
    terminal_audit = read_json(required["terminal_audit"])
    duplicates = read_json(required["duplicates"])
    syntax_records = list(read_jsonl(required["syntax"]))
    secret_records = list(read_jsonl(required["secrets"]))
    danger_records = list(read_jsonl(required["danger_findings"]))
    provenance_records = list(read_jsonl(required["provenance"]))
    output_mappings = list(read_jsonl(required["mappings"]))
    reconstruction_events = list(read_jsonl(required["reconstruction_events"]))

    if not journal_integrity.get("all_evidence_unchanged"):
        raise RecoveryError("journal evidence changed; refusing final recovery package")
    if len(syntax_records) != reconstruction["version_count"]:
        raise RecoveryError("syntax record count does not match recovered version count")

    syntax_by_version = {str(record["version_id"]): record for record in syntax_records}
    secrets_by_version: defaultdict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for record in secret_records:
        secrets_by_version[str(record["version_id"])].append(record)
    danger_by_version: defaultdict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for record in danger_records:
        danger_by_version[str(record["version_id"])].append(record)
    provenance_by_version = {
        str(record["version_id"]): record for record in provenance_records
    }
    mapping_by_path = {str(record["original_path"]): record for record in output_mappings}

    terminal_operation_counts: Counter[str] = Counter()
    terminal_application_counts: Counter[str] = Counter()
    for call in terminal_audit["calls"]:
        for operation in call.get("operations") or []:
            terminal_operation_counts[str(operation.get("kind"))] += 1
            terminal_application_counts[str(operation.get("application_result"))] += 1
    structured_application_counts = Counter(
        str(record.get("application_result")) for record in reconstruction_events
    )

    manual_records: list[Mapping[str, Any]] = []
    path_records: list[Mapping[str, Any]] = []
    manual_reason_counts: Counter[str] = Counter()
    manual_priority_counts: Counter[str] = Counter()
    blocking_reason_codes = {
        "unrecoverable_state",
        "partial_state",
        "terminal_final_state_uncertain",
        "syntax_invalid",
        "secret_candidate",
        "critical_operation",
        "training_policy_not_blocked",
    }

    for entry in reconstruction["entries"]:
        versions = entry.get("versions") or []
        latest = versions[-1] if versions else None
        latest_id = str(latest["version_id"]) if latest else None
        syntax = syntax_by_version.get(latest_id or "")
        version_secrets = secrets_by_version.get(latest_id or "", [])
        version_danger = danger_by_version.get(latest_id or "", [])
        danger_severity_counts = Counter(
            str(record["severity"]) for record in version_danger
        )
        danger_rule_counts = Counter(str(record["rule_id"]) for record in version_danger)
        all_syntax_issues = [
            syntax_by_version[str(version["version_id"])]
            for version in versions
            if syntax_by_version[str(version["version_id"])].get("status") != "parse_ok"
        ]
        all_version_secrets = [
            finding
            for version in versions
            for finding in secrets_by_version.get(str(version["version_id"]), [])
        ]
        all_version_danger = [
            finding
            for version in versions
            for finding in danger_by_version.get(str(version["version_id"]), [])
        ]
        all_danger_severity_counts = Counter(
            str(record["severity"]) for record in all_version_danger
        )
        all_danger_rule_counts = Counter(
            str(record["rule_id"]) for record in all_version_danger
        )
        provenance = provenance_by_version.get(latest_id or "")
        mapping = mapping_by_path.get(str(entry["original_path"]))
        reasons: list[Mapping[str, Any]] = []

        def add_reason(code: str, detail: str) -> None:
            if not any(reason["code"] == code for reason in reasons):
                reasons.append({"code": code, "detail": detail})

        classification = str(entry["classification"])
        if classification == "unrecoverable":
            add_reason(
                "unrecoverable_state",
                "No complete source state was established from successful recorded operations.",
            )
        elif classification == "partial":
            add_reason(
                "partial_state",
                "At least one version exists, but the final byte state is not conclusive.",
            )
        elif classification == "high-confidence":
            add_reason(
                "terminal_derived_state",
                "The state includes a statically replayed deterministic terminal operation.",
            )
        if entry.get("terminal_final_state_uncertain"):
            add_reason(
                "terminal_final_state_uncertain",
                "A later successful terminal mutation could not be replayed conclusively.",
            )
        if all_syntax_issues:
            add_reason(
                "syntax_invalid",
                f"The lineage contains {len(all_syntax_issues)} syntax-invalid recovered version(s): "
                + ", ".join(str(item["version_id"]) for item in all_syntax_issues),
            )
        if all_version_secrets:
            add_reason(
                "secret_candidate",
                f"The lineage contains {len(all_version_secrets)} redacted secret-pattern finding(s).",
            )
        if all_danger_severity_counts.get("critical", 0):
            add_reason(
                "critical_operation",
                "At least one recovered version contains an explicit raw-dataset mutation or recursive delete API call.",
            )
        if all_danger_severity_counts.get("high", 0):
            add_reason(
                "high_risk_operation",
                "At least one recovered version contains process execution, deletion, network, or dynamic-code API calls.",
            )
        if mapping:
            if mapping.get("mapping_confidence") == "unmapped":
                add_reason(
                    "output_mapping_unresolved",
                    "No journal/source/prompt evidence conclusively maps this source to an emitted JSONL.",
                )
            policy_status = str(mapping.get("research_or_training_policy_status", "unknown"))
            if policy_status != "research_only_training_blocked":
                add_reason(
                    "training_policy_not_blocked",
                    f"Static provenance status is {policy_status}; this is not training admission.",
                )
            conflicts = [
                key
                for key, value in (mapping.get("provenance_conflicts") or {}).items()
                if value
            ]
            if conflicts:
                add_reason(
                    "provenance_conflict",
                    "Conflicting static declarations: " + ", ".join(sorted(conflicts)),
                )
            observed_counts = sorted(
                {
                    int(item["count"])
                    for item in mapping.get("observed_output_count_evidence") or []
                    if isinstance(item.get("count"), int)
                }
            )
            if len(observed_counts) > 1:
                add_reason(
                    "observed_output_count_conflict",
                    "Terminal logs contain multiple observed output counts: "
                    + ", ".join(str(value) for value in observed_counts),
                )
        elif generator_candidate_path(str(entry["original_path"])):
            add_reason(
                "output_mapping_unavailable",
                "No recovered latest source was available for static generator/output mapping.",
            )

        priority = (
            "blocking"
            if any(reason["code"] in blocking_reason_codes for reason in reasons)
            else "review"
        )
        if reasons:
            for reason in reasons:
                manual_reason_counts[str(reason["code"])] += 1
            manual_priority_counts[priority] += 1
            manual_record = {
                "priority": priority,
                "original_path": entry["original_path"],
                "path_key": entry["path_key"],
                "classification": classification,
                "classification_evidence": entry["classification_evidence"],
                "final_state": entry["final_state"],
                "terminal_final_state_uncertain": entry["terminal_final_state_uncertain"],
                "agent_ids": entry["agent_ids"],
                "latest_version_id": latest_id,
                "latest_sha256": latest.get("sha256") if latest else None,
                "latest_recovered_path": latest.get("recovered_path") if latest else None,
                "role": mapping.get("role") if mapping else "unknown_temp_python_role",
                "output_jsonl": mapping.get("output_jsonl") if mapping else [],
                "mapping_confidence": mapping.get("mapping_confidence") if mapping else None,
                "research_or_training_policy_status": (
                    mapping.get("research_or_training_policy_status") if mapping else "unknown"
                ),
                "latest_syntax_status": syntax.get("status") if syntax else None,
                "latest_danger_severity_counts": dict(danger_severity_counts),
                "latest_danger_rule_counts": dict(danger_rule_counts),
                "all_version_syntax_issue_count": len(all_syntax_issues),
                "all_version_secret_finding_count": len(all_version_secrets),
                "all_version_danger_severity_counts": dict(
                    all_danger_severity_counts
                ),
                "all_version_danger_rule_counts": dict(all_danger_rule_counts),
                "reasons": reasons,
            }
            manual_records.append(manual_record)

        path_records.append(
            {
                "original_path": entry["original_path"],
                "path_key": entry["path_key"],
                "original_basename": entry["original_basename"],
                "classification": classification,
                "classification_evidence": entry["classification_evidence"],
                "final_state": entry["final_state"],
                "terminal_final_state_uncertain": entry[
                    "terminal_final_state_uncertain"
                ],
                "agent_ids": entry["agent_ids"],
                "event_count": entry["event_count"],
                "hunk_evidence_count": entry["hunk_evidence_count"],
                "unresolved_event_count": entry["unresolved_event_count"],
                "terminal_event_ids": entry["terminal_event_ids"],
                "versions": [
                    {
                        **{
                            key: version.get(key)
                            for key in (
                                "version",
                                "version_id",
                                "original_path",
                                "original_basename",
                                "basename_preserved",
                                "recovered_path",
                                "recovered_path_relative",
                                "sha256",
                                "bytes",
                                "classification",
                                "classification_evidence",
                                "source_channel",
                                "source_operation",
                                "source_event_id",
                                "agent_id",
                                "session_id",
                                "timestamp_utc",
                                "timestamp_ms",
                                "journal_path",
                                "journal_line",
                                "tool_call_id",
                                "file_mode",
                            )
                        },
                        "validation": {
                            "syntax": syntax_by_version.get(
                                str(version["version_id"])
                            ),
                            "secret_finding_count": len(
                                secrets_by_version.get(str(version["version_id"]), [])
                            ),
                            "danger_finding_count": len(
                                danger_by_version.get(str(version["version_id"]), [])
                            ),
                            "danger_severity_counts": dict(
                                Counter(
                                    str(item["severity"])
                                    for item in danger_by_version.get(
                                        str(version["version_id"]), []
                                    )
                                )
                            ),
                            "danger_rule_counts": dict(
                                Counter(
                                    str(item["rule_id"])
                                    for item in danger_by_version.get(
                                        str(version["version_id"]), []
                                    )
                                )
                            ),
                            "provenance": provenance_by_version.get(
                                str(version["version_id"])
                            ),
                        },
                    }
                    for version in versions
                ],
                "latest_validation": (
                    {
                        "syntax": syntax,
                        "secret_finding_count": len(version_secrets),
                        "danger_finding_count": len(version_danger),
                        "danger_severity_counts": dict(danger_severity_counts),
                        "danger_rule_counts": dict(danger_rule_counts),
                        "provenance": provenance,
                    }
                    if latest
                    else None
                ),
                "generator_output_mapping": mapping,
                "manual_inspection_priority": priority if reasons else None,
                "manual_inspection_reason_codes": [
                    reason["code"] for reason in reasons
                ],
            }
        )

    manual_records.sort(
        key=lambda record: (
            0 if record["priority"] == "blocking" else 1,
            str(record["original_path"]),
        )
    )
    write_jsonl_output(reports_dir / "manual-inspection.jsonl", manual_records)

    manual_lines = [
        "# Generators and temporary Python sources requiring manual inspection",
        "",
        f"Generated: {dt.datetime.now(dt.timezone.utc).isoformat()}",
        "",
        (
            f"This list contains {len(manual_records):,} path lineages: "
            f"{manual_priority_counts.get('blocking', 0):,} blocking and "
            f"{manual_priority_counts.get('review', 0):,} review-priority. "
            "It includes all non-exact reconstructions, all uncertain terminal final states, "
            "all lineages containing high/critical or syntax-invalid versions, and every mapped generator "
            "whose output or training-policy provenance remains unresolved."
        ),
        "",
        "No item in this list has been authorized for execution.",
        "",
        "## Reason totals",
        "",
        "| Reason | Lineages |",
        "|---|---:|",
    ]
    manual_lines.extend(
        f"| `{markdown_cell(code)}` | {count:,} |"
        for code, count in sorted(manual_reason_counts.items())
    )
    manual_lines.extend(
        [
            "",
            "## Lineages",
            "",
            "| Priority | Original path | Reconstruction | Latest version | Role | Reasons | Mapped outputs |",
            "|---|---|---|---|---|---|---:|",
        ]
    )
    for record in manual_records:
        manual_lines.append(
            "| {priority} | `{path}` | {classification} | `{version}` | {role} | {reasons} | {outputs} |".format(
                priority=markdown_cell(record["priority"]),
                path=markdown_cell(record["original_path"]),
                classification=markdown_cell(record["classification"]),
                version=markdown_cell(record["latest_version_id"] or "none"),
                role=markdown_cell(record["role"]),
                reasons=", ".join(
                    f"`{markdown_cell(reason['code'])}`" for reason in record["reasons"]
                ),
                outputs=len(record["output_jsonl"]),
            )
        )
    write_text_output(
        reports_dir / "manual-inspection.md", "\n".join(manual_lines) + "\n"
    )

    exact_groups = duplicates["exact_duplicate_groups"]
    ast_groups = duplicates["normalized_ast_duplicate_groups"]
    hash_report_lines = [
        "# Hash and duplicate report",
        "",
        f"Recovered versions hashed: {reconstruction['version_count']:,}",
        "",
        "Every emitted recovered version is listed in `hashes.sha256`. The digest in that file "
        "was recomputed from the read-only recovered bytes during static validation and matched "
        "the digest stored at reconstruction time.",
        "",
        f"Exact byte-duplicate groups: {len(exact_groups):,}",
        "",
        f"Normalized-AST duplicate groups: {len(ast_groups):,}",
        "",
        "Normalized AST grouping uses `ast.dump(..., include_attributes=False)` only for files "
        "that parsed successfully; it does not import or execute source.",
        "",
        "## Largest exact duplicate groups",
        "",
        "| SHA-256 | Members | Representative original paths |",
        "|---|---:|---|",
    ]
    for group in sorted(exact_groups, key=lambda item: (-int(item["count"]), item["sha256"]))[:20]:
        representatives = sorted(
            {str(item["original_path"]) for item in group["members"]}
        )[:3]
        hash_report_lines.append(
            f"| `{group['sha256']}` | {group['count']:,} | "
            + ", ".join(f"`{markdown_cell(path)}`" for path in representatives)
            + " |"
        )
    hash_report_lines.extend(
        [
            "",
            "The complete member lists are in `duplicates.json`. Duplicate membership is not "
            "evidence that a version is safe, correct, or training-admissible.",
        ]
    )
    write_text_output(
        reports_dir / "hash-and-duplicate-report.md",
        "\n".join(hash_report_lines) + "\n",
    )

    syntax_errors = [
        record for record in syntax_records if record.get("status") != "parse_ok"
    ]
    mapping_confidence_counts = Counter(
        str(record["mapping_confidence"]) for record in output_mappings
    )
    mapping_policy_counts = Counter(
        str(record["research_or_training_policy_status"])
        for record in output_mappings
    )
    mapping_role_counts = Counter(str(record["role"]) for record in output_mappings)
    mapping_family_counts: Counter[str] = Counter()
    for mapping in output_mappings:
        families = mapping.get("generator_family") or ["unknown"]
        mapping_family_counts.update(set(str(family) for family in families))
    mappings_with_observed_counts = sum(
        bool(record.get("observed_output_count_evidence")) for record in output_mappings
    )
    mappings_with_expected_counts = sum(
        bool(record.get("expected_output_count")) for record in output_mappings
    )
    final_state_counts = Counter(
        str(entry["final_state"]) for entry in reconstruction["entries"]
    )

    artifacts = {
        "machine_readable_recovery_manifest": "manifest/recovery-manifest.json",
        "detailed_reconstruction_manifest": "manifest/reconstruction-manifest.json",
        "validation_index": "manifest/validation-index.json",
        "final_danger_validation_index": "manifest/dangerous-validation-final.json",
        "session_graph": "inventory/session-graph.json",
        "structured_mutation_inventory": "inventory/mutations.jsonl",
        "terminal_mutation_inventory": "inventory/terminal-mutations.jsonl",
        "hunk_evidence_inventory": "inventory/hunk-evidence.jsonl",
        "journal_hashes_before": "inventory/journal-hashes.before.jsonl",
        "journal_hashes_after": "inventory/journal-hashes.after.jsonl",
        "journal_integrity": "inventory/journal-integrity.json",
        "recovered_source_tree": "recovered_sources/by-original-path/",
        "version_hashes": "reports/hashes.sha256",
        "artifact_hashes": "reports/artifact-hashes.sha256",
        "duplicates": "reports/duplicates.json",
        "hash_duplicate_report": "reports/hash-and-duplicate-report.md",
        "syntax": "reports/syntax.jsonl",
        "secrets": "reports/secrets.jsonl",
        "dangerous_operations_final": "reports/dangerous-operations.final.jsonl",
        "dangerous_operations_initial_conservative": "reports/dangerous-operations.jsonl",
        "provenance": "reports/provenance.jsonl",
        "generator_output_map": "reports/generator-output-map.final.jsonl",
        "generator_output_map_initial": "reports/generator-output-map.jsonl",
        "terminal_mutation_audit": "reports/terminal-mutation-audit.json",
        "reconstruction_event_log": "reports/reconstruction-events.jsonl",
        "manual_inspection_jsonl": "reports/manual-inspection.jsonl",
        "manual_inspection_report": "reports/manual-inspection.md",
        "human_recovery_report": "RECOVERY-REPORT.md",
        "safe_testing_proposal": "SAFE-TESTING-PROPOSAL.md",
        "trusted_recovery_tool": "tools/recover_grok_generators.py",
    }

    generated_at = dt.datetime.now(dt.timezone.utc).isoformat()
    recovery_manifest = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "top_level_session_id": PARENT_SESSION_ID,
        "source": {
            "session_base": str(SESSION_BASE),
            "session_count": session_graph["session_count"],
            "child_session_count": session_graph["child_session_count"],
            "max_depth": session_graph["max_depth"],
            "status_counts": session_graph["status_counts"],
            "missing_updates_session_ids": session_graph[
                "missing_updates_session_ids"
            ],
            "journal_integrity": journal_integrity,
        },
        "recovery_location": {
            "active_checkout": str(ACTIVE_CHECKOUT),
            "isolated_worktree": str(EXPECTED_WORKTREE),
            "recovery_root": str(RECOVERY_ROOT),
            "branch": RECOVERY_BRANCH,
            "base_commit": BASE_COMMIT,
            "recovered_sources_outside_tmp": True,
        },
        "safety": {
            "all_recovered_content_treated_as_untrusted_data": True,
            "recovered_programs_executed": False,
            "recovered_modules_imported": False,
            "recovered_sources_compiled": False,
            "syntax_validation_method": "ast.parse only",
            "terminal_commands_reexecuted": False,
            "dataset_repositories_modified": False,
            "active_checkout_tracked_files_modified_by_recovery": False,
            "active_checkout_untracked_tree_fingerprinted_before_recovery": False,
            "commits_created": False,
            "branch_pushed": False,
            "pull_request_opened": False,
            "merge_performed": False,
            "repository_baseline_test_exception": {
                "occurred": True,
                "description": (
                    "A repository baseline unit-test process, not recovered source, was "
                    "inadvertently started in the isolated worktree and terminated before "
                    "completion; it produced no accepted validation result."
                ),
                "terminated_pid": 2885213,
                "recovered_source_involved": False,
            },
            "static_validation_is_not_training_admission": True,
        },
        "inventory_summary": inventory_summary,
        "reconstruction_summary": {
            "path_count": reconstruction["path_count"],
            "version_count": reconstruction["version_count"],
            "classification_counts": reconstruction["classification_counts"],
            "version_classification_counts": reconstruction[
                "version_classification_counts"
            ],
            "final_state_counts": dict(final_state_counts),
            "terminal_uncertain_path_count": reconstruction[
                "terminal_uncertain_path_count"
            ],
            "structured_application_counts": dict(structured_application_counts),
            "terminal_operation_counts": dict(terminal_operation_counts),
            "terminal_application_counts": dict(terminal_application_counts),
        },
        "classification_definitions": {
            "exact": (
                "A completed structured full write established the bytes; every replayed "
                "structured edit matched exactly once; no unresolved later mutation controls "
                "the final state."
            ),
            "high-confidence": (
                "A completed terminal operation with literal, statically resolvable content "
                "or source paths was replayed without executing the command; no unresolved "
                "later mutation controls the final state."
            ),
            "partial": (
                "At least one full version was recovered, but a later successful structured "
                "or terminal mutation could not be placed or reproduced conclusively."
            ),
            "unrecoverable": (
                "No complete byte state could be established from a successful recorded full "
                "write or deterministic terminal operation; any available edit fragments are "
                "retained separately."
            ),
        },
        "static_validation_summary": {
            "version_count": validation["version_count"],
            "syntax_counts": validation["syntax_counts"],
            "secret_finding_count": validation["secret_finding_count"],
            "versions_with_secret_findings": validation[
                "versions_with_secret_findings"
            ],
            "danger_final": {
                key: danger_final[key]
                for key in (
                    "method",
                    "finding_count",
                    "severity_counts",
                    "rule_counts",
                    "versions_with_findings",
                    "versions_with_critical_findings",
                    "versions_with_high_findings",
                )
            },
            "exact_duplicate_group_count": validation[
                "exact_duplicate_group_count"
            ],
            "normalized_ast_duplicate_group_count": validation[
                "normalized_ast_duplicate_group_count"
            ],
        },
        "generator_output_mapping_summary": {
            "mapping_count": len(output_mappings),
            "confidence_counts": dict(mapping_confidence_counts),
            "role_counts": dict(mapping_role_counts),
            "family_membership_counts": dict(mapping_family_counts),
            "policy_status_counts": dict(mapping_policy_counts),
            "mappings_with_expected_output_count": mappings_with_expected_counts,
            "mappings_with_observed_output_count_evidence": mappings_with_observed_counts,
            "mapping_does_not_establish_dataset_integrity_or_training_admission": True,
        },
        "manual_inspection_summary": {
            "lineage_count": len(manual_records),
            "priority_counts": dict(manual_priority_counts),
            "reason_counts": dict(manual_reason_counts),
        },
        "artifacts": artifacts,
        "path_records": path_records,
        "stop_gate": {
            "status": "stopped_for_review",
            "recovered_generators_may_be_run_only_after_separate_explicit_authorization": True,
            "bulk_corpus_may_be_committed_only_after_separate_explicit_authorization": True,
            "dataset_mutation_may_occur_only_after_separate_explicit_authorization": True,
        },
    }
    write_json_output(manifest_dir / "recovery-manifest.json", recovery_manifest)

    report_lines = [
        "# Grok temporary Python generator recovery report",
        "",
        f"Session: `{PARENT_SESSION_ID}`",
        "",
        f"Recovery root: `{RECOVERY_ROOT}`",
        "",
        "## Outcome",
        "",
        (
            f"The parent session and all {session_graph['child_session_count']:,} discovered "
            f"child sessions were inventoried. The chronology contains "
            f"{inventory_summary['structured_temp_python_event_count']:,} explicit structured "
            f"temporary-Python mutation events across "
            f"{inventory_summary['structured_temp_python_unique_paths']:,} paths, plus "
            f"{inventory_summary['terminal_calls_referencing_temp_python']:,} terminal calls "
            "that referenced temporary Python sources."
        ),
        "",
        (
            f"Reconstruction produced {reconstruction['version_count']:,} preserved, read-only "
            f"source versions across {reconstruction['path_count']:,} collision-safe path "
            "lineages. Original basenames are retained inside version directories; each "
            "lineage key includes a SHA-256-derived suffix so identically named `/tmp` files "
            "cannot collide."
        ),
        "",
        (
            f"Final path classifications are: exact {reconstruction['classification_counts'].get('exact', 0):,}; "
            f"high-confidence {reconstruction['classification_counts'].get('high-confidence', 0):,}; "
            f"partial {reconstruction['classification_counts'].get('partial', 0):,}; and "
            f"unrecoverable {reconstruction['classification_counts'].get('unrecoverable', 0):,}."
        ),
        "",
        "This is a reconstruction and static-validation stopping point. No recovered generator "
        "was imported, compiled, or executed; no terminal command from a journal was rerun; no "
        "dataset repository was modified; and nothing was committed, pushed, proposed, or merged.",
        "",
        "## Chain of custody and journal integrity",
        "",
        (
            f"The evidence tree contained {journal_integrity['before_record_count']:,} files. "
            f"Before/after comparison found {journal_integrity['modified_path_count']} modified, "
            f"{journal_integrity['added_path_count']} added, and "
            f"{journal_integrity['removed_path_count']} removed paths. "
            f"`all_evidence_unchanged` is `{str(journal_integrity['all_evidence_unchanged']).lower()}`."
        ),
        "",
        (
            f"The session graph has depth {session_graph['max_depth']}; statuses are "
            + ", ".join(
                f"{key} {value:,}" for key, value in sorted(session_graph["status_counts"].items())
            )
            + "."
        ),
        "",
        (
            "One child session lacks `updates.jsonl`: `"
            + "`, `".join(session_graph["missing_updates_session_ids"])
            + "`. Its other available session evidence remains inventoried."
        ),
        "",
        "## Read-only inventory",
        "",
        "| Evidence class | Count |",
        "|---|---:|",
        f"| Sessions | {session_graph['session_count']:,} |",
        f"| Child sessions | {session_graph['child_session_count']:,} |",
        f"| Evidence files hashed | {inventory_summary['journal_files_hashed']:,} |",
        f"| Structured temp-Python events | {inventory_summary['structured_temp_python_event_count']:,} |",
        f"| Structured temp-Python paths | {inventory_summary['structured_temp_python_unique_paths']:,} |",
        f"| Completed full writes | {inventory_summary['structured_outcome_counts'].get('full_write:Completed', 0):,} |",
        f"| Completed structured replacements | {inventory_summary['structured_outcome_counts'].get('search_replace:Completed', 0):,} |",
        f"| Failed structured replacements | {inventory_summary['structured_outcome_counts'].get('search_replace:Failed', 0):,} |",
        f"| Terminal calls referencing temp Python | {inventory_summary['terminal_calls_referencing_temp_python']:,} |",
        f"| Terminal mutation candidates | {inventory_summary['terminal_source_mutation_candidates']:,} |",
        f"| Ambiguous terminal mutation candidates | {inventory_summary['terminal_ambiguous_mutation_candidates']:,} |",
        f"| Temp-Python hunk evidence records | {inventory_summary['hunk_evidence_record_count']:,} |",
        "",
        "`inventory/mutations.jsonl` and `inventory/terminal-mutations.jsonl` preserve the "
        "original path, child agent/session ID, timestamp, journal line, tool outcome, hashes of "
        "recorded inputs/outputs, related JSONL expressions, and—in the terminal inventory—the "
        "exact logged command. Structured edit strings are retained as content-addressed "
        "versions or read-only `.pyfrag` evidence when no full base could be established.",
        "",
        "## Chronological reconstruction",
        "",
        "Structured events were globally ordered by recorded millisecond timestamp, session ID, "
        "journal line, and tool-call ID. Only `Completed` full writes and replacements were eligible. "
        "A replacement was replayed only when its recorded old string occurred exactly once in the "
        "known prior state.",
        "",
        "| Structured replay outcome | Count |",
        "|---|---:|",
    ]
    report_lines.extend(
        f"| `{markdown_cell(key)}` | {value:,} |"
        for key, value in sorted(structured_application_counts.items())
    )
    report_lines.extend(
        [
            "",
            "Terminal commands were parsed as inert text. The only statically replayable forms were "
            "quoted literal heredoc writes/appends, literal copies/moves, literal concatenations "
            "whose sources were already known, and literal deletions as existence-state changes. "
            "Inline Python, shell expansion, pipelines, in-place tools, globs, variables, and unknown "
            "source bytes were never executed or guessed.",
            "",
            "| Terminal replay result | Count |",
            "|---|---:|",
        ]
    )
    report_lines.extend(
        f"| `{markdown_cell(key)}` | {value:,} |"
        for key, value in sorted(terminal_application_counts.items())
    )
    report_lines.extend(
        [
            "",
            f"{reconstruction['terminal_uncertain_path_count']:,} path lineages have a final state "
            "that may have been altered by a successful terminal mutation that could not be "
            "reproduced conclusively.",
            "",
            "### Classification meanings",
            "",
            "- **Exact:** completed structured full-write bytes plus a uniquely applicable chain "
            "of completed structured edits, with no unresolved later final-state mutation.",
            "",
            "- **High-confidence:** a literal deterministic terminal write/copy/concatenation was "
            "replayed statically from known content or known source states, with no unresolved later "
            "mutation. This is intentionally weaker than exact because the shell was not run.",
            "",
            "- **Partial:** at least one complete version was recovered, but a later successful edit "
            "or terminal operation could not be placed or reproduced conclusively.",
            "",
            "- **Unrecoverable:** no complete byte state was established. Available old/new edit "
            "fragments and event provenance are still retained.",
            "",
            "Each lineage and each recovered version carries its own evidence text in the machine "
            "manifests; classification is not inferred from syntax validity or generator quality.",
            "",
            "## Non-executing validation",
            "",
            (
                f"`ast.parse` accepted {validation['syntax_counts'].get('parse_ok', 0):,} of "
                f"{validation['version_count']:,} versions. "
                f"{validation['syntax_counts'].get('syntax_error', 0):,} versions have syntax errors."
            ),
            "",
            f"Secret-pattern scan findings: {validation['secret_finding_count']:,}.",
            "",
            (
                f"The destination-aware dangerous-operation scan produced "
                f"{danger_final['finding_count']:,} findings: "
                + ", ".join(
                    f"{key} {value:,}" for key, value in sorted(danger_final["severity_counts"].items())
                )
                + "."
            ),
            "",
            "The final scan labels a dataset-path or shell-command string as informational when it "
            "is merely present in source/data. It assigns action severity only to AST calls such as "
            "write/delete/process/network/dynamic-code APIs. This avoids treating generated training "
            "record text as if the recovery process had executed it.",
            "",
            "| Final static rule | Findings |",
            "|---|---:|",
        ]
    )
    report_lines.extend(
        f"| `{markdown_cell(key)}` | {value:,} |"
        for key, value in sorted(danger_final["rule_counts"].items())
    )
    report_lines.extend(
        [
            "",
            "### Syntax-invalid versions",
            "",
            "| Original path | Version | Line | Parser result |",
            "|---|---|---:|---|",
        ]
    )
    for record in syntax_errors:
        report_lines.append(
            f"| `{markdown_cell(record['original_path'])}` | `{markdown_cell(record['version_id'])}` | "
            f"{record.get('line') or ''} | {markdown_cell(record.get('error'))} |"
        )
    report_lines.extend(
        [
            "",
            "The secret scan is pattern-based and the operation scan is static; neither proves "
            "absence of secrets, safe behavior, semantic correctness, determinism, or policy "
            "admissibility.",
            "",
            "## Hashes and duplicates",
            "",
            (
                f"All {reconstruction['version_count']:,} recovered versions have a SHA-256 in "
                "`reports/hashes.sha256`. There are "
                f"{validation['exact_duplicate_group_count']:,} exact byte-duplicate groups and "
                f"{validation['normalized_ast_duplicate_group_count']:,} normalized-AST duplicate "
                "groups. Complete member lists are in `reports/duplicates.json`."
            ),
            "",
            "## Generator-to-output and policy mapping",
            "",
            (
                f"Static provenance produced {len(output_mappings):,} generator/helper mapping "
                "records. Confidence is "
                + ", ".join(
                    f"{key} {value:,}" for key, value in sorted(mapping_confidence_counts.items())
                )
                + "."
            ),
            "",
            (
                f"{mappings_with_expected_counts:,} mappings carry an expected output count from "
                f"a child prompt; {mappings_with_observed_counts:,} carry observed-count evidence "
                "from recorded terminal logs. Counts and emitted JSONL paths were not revalidated "
                "against dataset repositories."
            ),
            "",
            "| Static policy status | Mappings |",
            "|---|---:|",
        ]
    )
    report_lines.extend(
        f"| `{markdown_cell(key)}` | {value:,} |"
        for key, value in sorted(mapping_policy_counts.items())
    )
    report_lines.extend(
        [
            "",
            "`research_only_training_blocked` means both research-only intent and a blocked project "
            "training policy were found in source or child-prompt evidence. Every other status "
            "requires manual policy review. None of these statuses is training admission.",
            "",
            "The complete map preserves generator family, dataset category, run label, child-agent "
            "provenance, output path expressions, record identifiers, expected/observed counts, "
            "mapping evidence, confidence, policy evidence, and conflicts in "
            "`reports/generator-output-map.final.jsonl`. The unsuffixed file is retained as the "
            "initial, less destination-aware pass.",
            "",
            "## Manual-inspection gate",
            "",
            (
                f"{len(manual_records):,} lineages require manual inspection: "
                f"{manual_priority_counts.get('blocking', 0):,} blocking and "
                f"{manual_priority_counts.get('review', 0):,} review-priority. The exhaustive "
                "machine-readable list is `reports/manual-inspection.jsonl`; the tabular list is "
                "`reports/manual-inspection.md`."
            ),
            "",
            "## Scope exception",
            "",
            "A repository baseline unit-test process—not recovered source—was inadvertently started "
            "in the isolated worktree and terminated before completion (PID 2885213). It produced no "
            "accepted validation result and is excluded from this report's static-validation claims. "
            "No recovered source was involved. This disclosure is retained because the requested "
            "initial validation boundary was non-executing.",
            "",
            "## Review stop",
            "",
            "The recovery is stopped before generator execution, bulk commit, push, pull request, "
            "merge, or dataset mutation. `SAFE-TESTING-PROPOSAL.md` is a proposal only and requires "
            "separate explicit authorization before any selected source is run.",
            "",
            "## Artifact index",
            "",
        ]
    )
    report_lines.extend(
        f"- `{path}` — {name.replace('_', ' ')}"
        for name, path in sorted(artifacts.items())
    )
    write_text_output(RECOVERY_ROOT / "RECOVERY-REPORT.md", "\n".join(report_lines) + "\n")

    proposal = f"""# Proposal for safely testing selected recovered generators

Status: proposal only; no recovered generator is authorized to run.

Session: `{PARENT_SESSION_ID}`

## Objective

Test a deliberately small allowlist of reconstructed generators without granting them access to the active checkout, dataset repositories, credentials, network, or persistent output paths. Testing would establish runtime behavior and output determinism only; it would not establish factual quality or training admission.

## Entry gate

A candidate should enter runtime testing only after a reviewer explicitly names its `version_id` and SHA-256 and confirms all of the following:

1. Reconstruction is `exact`, or an explicitly accepted `high-confidence` terminal-derived state. `partial` and `unrecoverable` lineages remain excluded.
2. `ast.parse` status is `parse_ok`, secret-pattern count is zero, and all high/critical static findings have been read at the cited lines.
3. Any output path, subprocess, network, dynamic-code, deletion, rename, permission-change, or raw-dataset operation is understood and either removed from a disposable test copy or blocked by the sandbox.
4. The generator/output mapping has one intended family, dataset category, run label, output target, and expected count. Conflicts and unmapped outputs are resolved manually.
5. The intended-use and project-training-policy fields are reviewed independently. Only `research_only_training_blocked` may proceed as research-only output, and that status still does not admit records to training.

## Proposed isolation

1. Copy only the approved source version into a new disposable directory outside the repository and outside every dataset path. Keep the recovered original read-only and verify the copy against the approved SHA-256 before any review-only adaptation.
2. Run as a dedicated unprivileged user in a disposable user/mount/network namespace or rootless container. Disable network entirely; mount the repository and recovery artifacts read-only only if the source demonstrably needs them; do not mount `outputs/raw`, dataset repositories, `$HOME`, SSH material, cloud credentials, or agent journals.
3. Provide a fresh empty output directory on a size-limited temporary filesystem. If the source hard-codes an output path, modify only the disposable test copy and retain a patch plus before/after hashes. Never create a symlink that redirects a hard-coded dataset path.
4. Use an isolated Python interpreter (`-I`, no user site, no inherited `PYTHONPATH`) with a minimal allowlisted environment. Supply no tokens or credentials. Disable bytecode writes and cap wall time, CPU, memory, process count, open files, and output size.
5. Apply syscall controls where available: deny network syscalls, deny writes outside the designated output mount, and capture `openat`, `rename`, `unlink`, `execve`, and `connect` attempts. Treat any denied or unexpected operation as a hard stop.
6. Capture stdout, stderr, exit status, resource use, filesystem inventory, and SHA-256 for every produced file. Do not copy produced data into a repository during the test.

## Proposed staged execution

### Stage A: one-run containment proof

Run one low-volume exact candidate whose static scan has no process, network, delete, dynamic-code, or raw-dataset finding. Verify that all writes remain inside the designated output directory and that no denied syscall was attempted.

### Stage B: schema and policy checks

Parse produced JSONL as data in a separate validator process. Check UTF-8, one JSON object per line, required schema fields, unique record identifiers, declared generator family/category/run label, research-only intent, blocked training policy, and the approved maximum record count. Do not import the generator to validate output.

### Stage C: determinism check

Repeat the same approved version twice in fresh sandboxes with identical explicit inputs and environment. Compare file inventories, line counts, record identifiers, canonicalized-record hashes, and whole-file SHA-256. Any unexplained difference blocks further use.

### Stage D: bounded expansion

Only after reviewing Stage A-C evidence, authorize additional exact versions in small batches. Keep one execution evidence bundle per `version_id` and never infer safety for duplicate or related versions merely from family membership.

## Required evidence bundle

For each approved version, retain the approval record; original and disposable-copy hashes; any adaptation patch; sandbox policy; exact interpreter identity; environment allowlist; static finding disposition; stdout/stderr; syscall audit; resource metrics; produced-file hashes; JSONL validation report; two-run determinism comparison; and a final research/training-policy decision.

## Stop conditions

Stop immediately on any network attempt, write outside the output mount, access to credentials or journals, subprocess not explicitly reviewed, unexpected delete/rename, raw-dataset access, output-count excess, schema violation, nondeterministic record identity, or policy ambiguity. Do not promote, commit, upload, or merge generated data without a separate release decision.

## Suggested first review set

Choose at most three `exact` lineages with `parse_ok`, zero secrets, zero critical/high action findings, `corroborated` output mapping, and `research_only_training_blocked`. The reviewer should name exact `version_id` values from `manifest/recovery-manifest.json`; this proposal intentionally does not auto-select or run them.
"""
    write_text_output(RECOVERY_ROOT / "SAFE-TESTING-PROPOSAL.md", proposal)

    readme = f"""# Grok session temporary-source recovery

This directory is the stopped-for-review recovery package for Grok session `{PARENT_SESSION_ID}`.

- Start with `RECOVERY-REPORT.md`.
- Use `manifest/recovery-manifest.json` for the consolidated machine-readable inventory.
- Recovered versions are under `recovered_sources/by-original-path/`; every version is read-only and hashed in `reports/hashes.sha256`.
- Use `reports/manual-inspection.md` or `.jsonl` for review gates.
- `SAFE-TESTING-PROPOSAL.md` describes a future, separately authorized test process.

All recovered content is untrusted data. No recovered generator has been imported, compiled, or executed. No dataset has been modified, and no recovery corpus commit, push, pull request, or merge has been made.
"""
    write_text_output(RECOVERY_ROOT / "README.md", readme)

    # Hash all materialized recovery artifacts except this self-referential index.
    artifact_hash_path = reports_dir / "artifact-hashes.sha256"
    artifact_hash_lines: list[str] = []
    for path in sorted(RECOVERY_ROOT.rglob("*")):
        if path == artifact_hash_path:
            continue
        info = path.lstat()
        if stat.S_ISREG(info.st_mode):
            artifact_hash_lines.append(
                f"{sha256_file(path)}  {path.relative_to(RECOVERY_ROOT)}"
            )
    write_text_output(artifact_hash_path, "\n".join(artifact_hash_lines) + "\n")
    print(
        json.dumps(
            {
                "recovery_manifest_records": len(path_records),
                "manual_inspection_records": len(manual_records),
                "manual_priority_counts": dict(manual_priority_counts),
                "artifact_hash_count_excluding_index": len(artifact_hash_lines),
                "report": str(RECOVERY_ROOT / "RECOVERY-REPORT.md"),
                "testing_proposal": str(RECOVERY_ROOT / "SAFE-TESTING-PROPOSAL.md"),
            },
            indent=2,
            sort_keys=True,
        )
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=(
            "inventory",
            "reconstruct",
            "validate",
            "refine",
            "seal",
            "remap",
            "deliver",
            "refresh",
        ),
        help="recovery phase to run; phases refuse existing outputs",
    )
    return parser


def main() -> int:
    arguments = build_parser().parse_args()
    if arguments.command == "inventory":
        inventory()
    elif arguments.command == "reconstruct":
        reconstruct()
    elif arguments.command == "validate":
        validate()
    elif arguments.command == "refine":
        refine_dangerous_validation()
    elif arguments.command == "seal":
        seal_journal_integrity()
    elif arguments.command == "remap":
        remap_generator_outputs()
    elif arguments.command == "deliver":
        write_final_deliverables()
    elif arguments.command == "refresh":
        write_final_deliverables(refresh=True)
    else:
        raise RecoveryError(f"unsupported command: {arguments.command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
