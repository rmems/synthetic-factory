#!/usr/bin/env python3
"""Read-only payload-kind audit for one published raw JSONL corpus.

A dataset slug names a *topic*; the records name a *shape*. When a Hub card
advertises one kind of record and the payload holds a mix, a consumer that
trusts the card writes a loader that crashes on the first record of the other
shape. This module measures the mix rather than asserting it: it walks one
corpus directory, classifies every record with the curation lane's own
:func:`curate_identity.record_kind`, and returns a deterministic audit.

It never writes to the corpus. The only output is JSON or Markdown on stdout.

Usage::

    python3 pipelines/payload_kind_audit.py <corpus-dir> [--json|--markdown]
    python3 pipelines/payload_kind_audit.py <corpus-dir> --expect <audit.json>

``--expect`` re-derives the audit and exits non-zero naming each field that has
drifted from a published audit, so a committed audit cannot quietly go stale.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parent))

from curate_identity import (  # noqa: E402
    LEGACY_ID_KEYS,
    IdentityCurationError,
    record_kind,
)

SCHEMA_VERSION = "1.0.0"

# A coding episode is the ``goal`` + ``steps`` shape. A thalamic gate record may
# *wrap* one under ``executed_action``; that wrapped episode is real coding
# supervision, but it is not reachable by a loader that expects a top-level
# episode.
EPISODE_MARKERS = ("goal", "steps")

# Step-level reasoning fields. ``decision_basis`` is the observable form this
# factory's curation contract requires; ``thought`` is the legacy hidden form.
REASONING_FIELDS = ("thought", "decision_basis", "reflection")
SUPPORTED_RECORD_KINDS = frozenset({"episode", "thalamic"})


class PayloadKindAuditError(ValueError):
    """The corpus cannot be audited without guessing."""


def _is_episode_shaped(value: Any) -> bool:
    return isinstance(value, Mapping) and all(key in value for key in EPISODE_MARKERS)


def _required_mapping(record: Mapping[str, Any], key: str, where: str) -> Mapping[str, Any]:
    value = record.get(key)
    if not isinstance(value, Mapping):
        raise PayloadKindAuditError(f"{where}.{key} must be a JSON object")
    return value


def _steps(value: Mapping[str, Any], where: str) -> list[Mapping[str, Any]]:
    steps = value.get("steps")
    if not isinstance(steps, list):
        raise PayloadKindAuditError(f"{where}.steps must be a JSON array")
    for index, step in enumerate(steps):
        if not isinstance(step, Mapping):
            raise PayloadKindAuditError(f"{where}.steps[{index}] must be a JSON object")
    return steps


def _coding_steps(record: Mapping[str, Any], kind: str, where: str) -> list[Mapping[str, Any]]:
    if kind == "episode":
        return _steps(record, where)
    if kind == "thalamic":
        executed = record.get("executed_action")
        if not _is_episode_shaped(executed):
            return []
        return _steps(executed, f"{where}.executed_action")
    raise PayloadKindAuditError(
        f"{where}: payload kind {kind!r} is outside this episode/thalamic audit"
    )


def _first_legacy_id(record: Mapping[str, Any]) -> Any:
    """Return the first present identifier supported by identity curation."""
    for key in LEGACY_ID_KEYS:
        if key in record:
            return record[key]
    return None


def _record_row(
    record: Mapping[str, Any],
    kind: str,
    steps: list[Mapping[str, Any]],
    source_file: str,
    line: int,
    digest: str,
) -> dict:
    row: dict[str, Any] = {
        "source_file": source_file,
        "source_line": line,
        "kind": kind,
        "sha256": digest,
    }
    if kind == "thalamic":
        state = _required_mapping(record, "state", f"{source_file}:{line}")
        gate = _required_mapping(record, "safety_decision", f"{source_file}:{line}")
        executed = record.get("executed_action")
        row["id"] = state.get("episode_id")
        row["domain"] = state.get("domain")
        row["supervisor_id"] = gate.get("supervisor_id")
        row["gate_decision"] = gate.get("decision")
        row["wraps_coding_episode"] = _is_episode_shaped(executed)
        row["coding_steps"] = len(steps)
    else:
        # The published episodes in this lane carry no top-level identifier,
        # but other episode corpora use legacy aliases. Report the first alias
        # the identity curation contract recognizes; never invent one.
        row["id"] = _first_legacy_id(record)
        row["domain"] = None
        row["wraps_coding_episode"] = False
        row["coding_steps"] = len(steps)
    return row


def _reasoning_counts(steps: list[Mapping[str, Any]]) -> dict[str, int]:
    counts = {field: 0 for field in REASONING_FIELDS}
    for step in steps:
        for field in REASONING_FIELDS:
            if field in step:
                counts[field] += 1
    return counts


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant {value!r}")


def _jsonl_lines(raw: bytes, source_file: str):
    """Yield LF-delimited UTF-8 records without splitting on Unicode separators."""
    for line_number, line_bytes in enumerate(raw.split(b"\n"), 1):
        # CRLF is one record terminator, so neither byte belongs to the record
        # digest. A bare carriage return elsewhere remains part of the payload.
        if line_bytes.endswith(b"\r"):
            line_bytes = line_bytes[:-1]
        try:
            line = line_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise PayloadKindAuditError(
                f"{source_file}:{line_number}: payload is not valid UTF-8: {exc}"
            ) from exc
        yield line_number, line_bytes, line


def build_audit(corpus: Path, payload_names: Iterable[str] | None = None) -> dict:
    """Return a deterministic audit of the whole corpus or one named snapshot."""
    corpus = Path(corpus)
    if corpus.is_symlink() or not corpus.is_dir():
        raise PayloadKindAuditError(f"not a readable corpus directory: {corpus}")

    files: list[dict] = []
    records: list[dict] = []
    kinds: dict[str, int] = {}
    factories: dict[str, int] = {}
    native_steps = 0
    embedded_steps = 0
    reasoning = {field: 0 for field in REASONING_FIELDS}
    wrapping = 0

    if payload_names is None:
        payload_paths = sorted(corpus.glob("*.jsonl"))
    else:
        names = list(payload_names)
        for name in names:
            if not isinstance(name, str) or not name.endswith(".jsonl") or Path(name).name != name:
                raise PayloadKindAuditError(f"unsafe snapshot payload name: {name!r}")
        if len(names) != len(set(names)):
            raise PayloadKindAuditError("snapshot payload names must be unique")
        payload_paths = [corpus / name for name in sorted(names)]
    if not payload_paths:
        raise PayloadKindAuditError(f"corpus contains no *.jsonl payloads: {corpus}")

    for path in payload_paths:
        if path.is_symlink() or not path.is_file():
            raise PayloadKindAuditError(f"unsafe payload entry: {path}")
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise PayloadKindAuditError(f"cannot read payload {path}: {exc}") from exc
        file_kinds: dict[str, int] = {}
        count = 0
        for line_number, line_bytes, line in _jsonl_lines(raw, path.name):
            if not line.strip():
                continue
            try:
                record = json.loads(line, parse_constant=_reject_json_constant)
            except (json.JSONDecodeError, ValueError) as exc:
                raise PayloadKindAuditError(f"{path.name}:{line_number}: {exc}") from exc
            if not isinstance(record, dict):
                raise PayloadKindAuditError(
                    f"{path.name}:{line_number}: record must be a JSON object"
                )
            digest = hashlib.sha256(line_bytes).hexdigest()
            try:
                kind = record_kind(record)
            except IdentityCurationError as exc:
                raise PayloadKindAuditError(f"{path.name}:{line_number}: {exc}") from exc
            where = f"{path.name}:{line_number}"
            if kind not in SUPPORTED_RECORD_KINDS:
                raise PayloadKindAuditError(
                    f"{where}: payload kind {kind!r} is outside this episode/thalamic audit"
                )
            steps = _coding_steps(record, kind, where)
            row = _record_row(record, kind, steps, path.name, line_number, digest)
            count += 1
            kind = row["kind"]
            kinds[kind] = kinds.get(kind, 0) + 1
            file_kinds[kind] = file_kinds.get(kind, 0) + 1
            meta = record.get("meta") if isinstance(record.get("meta"), Mapping) else {}
            factory = meta.get("factory")
            if isinstance(factory, str):
                factories[factory] = factories.get(factory, 0) + 1
            if kind == "thalamic":
                embedded_steps += row["coding_steps"]
                if row["wraps_coding_episode"]:
                    wrapping += 1
            else:
                native_steps += row["coding_steps"]
            for field, value in _reasoning_counts(steps).items():
                reasoning[field] += value
            records.append(row)
        files.append(
            {
                "path": path.name,
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "records": count,
                "kinds": dict(sorted(file_kinds.items())),
            }
        )

    if not records:
        raise PayloadKindAuditError(f"corpus contains no auditable records: {corpus}")

    return {
        "schema_version": SCHEMA_VERSION,
        "source": corpus.name,
        "summary": {
            "files": len(files),
            "records": len(records),
            "kinds": dict(sorted(kinds.items())),
            "meta_factory_stamps": dict(sorted(factories.items())),
            "thalamic_records_wrapping_a_coding_episode": wrapping,
            "coding_episodes_reachable_at_top_level": kinds.get("episode", 0),
            "coding_episodes_including_wrapped": kinds.get("episode", 0) + wrapping,
            "coding_steps": {
                "native": native_steps,
                "wrapped": embedded_steps,
                "total": native_steps + embedded_steps,
            },
            "coding_steps_by_reasoning_field": dict(sorted(reasoning.items())),
        },
        "files": files,
        "records": records,
    }


def render_markdown(audit: Mapping[str, Any]) -> str:
    """Render the per-record table an operator can paste into a card."""
    lines = [
        "| Source | Kind | Record id | Gate | Wraps a coding episode | Coding steps |",
        "|---|---|---|---|---|---:|",
    ]
    for row in audit["records"]:
        gate = _markdown_cell(row.get("supervisor_id") or "—")
        decision = row.get("gate_decision")
        if decision:
            gate = f"{gate} / {_markdown_cell(decision)}"
        record_id = _markdown_code(row["id"]) if row.get("id") else "—"
        source = _markdown_code(f"{row['source_file']}:{row['source_line']}")
        lines.append(
            f"| {source} | {_markdown_cell(row['kind'])} | "
            f"{record_id} | {gate} | {'yes' if row['wraps_coding_episode'] else 'no'} | "
            f"{row['coding_steps']} |"
        )
    return "\n".join(lines) + "\n"


def _markdown_cell(value: Any) -> str:
    rendered = html.escape(str(value), quote=False)
    return (
        rendered.replace("|", "&#124;")
        .replace("\r\n", "<br>")
        .replace("\r", "<br>")
        .replace("\n", "<br>")
    )


def _markdown_code(value: Any) -> str:
    text = str(value)
    if not any(marker in text for marker in ("`", "|", "\r", "\n")):
        return f"`{_markdown_cell(text)}`"
    return f"<code>{_markdown_cell(text)}</code>"


def _drift(derived: Mapping[str, Any], published: Mapping[str, Any]) -> list[str]:
    problems = []
    for key, value in derived.items():
        if key not in published:
            problems.append(f"published audit is missing {key!r}")
        elif published[key] != value:
            problems.append(f"{key} differs from the published audit")
    return problems


def _snapshot_payload_names(published: Mapping[str, Any]) -> list[str]:
    files = published.get("files")
    if not isinstance(files, list) or not files:
        raise PayloadKindAuditError("published audit files must be a non-empty array")
    names = []
    for index, entry in enumerate(files):
        if not isinstance(entry, Mapping) or not isinstance(entry.get("path"), str):
            raise PayloadKindAuditError(f"published audit files[{index}].path must be a string")
        names.append(entry["path"])
    return names


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("corpus", type=Path, help="directory of published *.jsonl")
    output = parser.add_mutually_exclusive_group()
    output.add_argument("--json", action="store_true", help="emit the full JSON audit (default)")
    output.add_argument("--markdown", action="store_true", help="emit the record table")
    parser.add_argument(
        "--expect",
        type=Path,
        default=None,
        help="compare against a published audit JSON and fail on drift",
    )
    args = parser.parse_args(argv)

    published = None
    payload_names = None
    if args.expect is not None:
        try:
            published = json.loads(
                args.expect.read_text(encoding="utf-8"),
                parse_constant=_reject_json_constant,
            )
        except (OSError, UnicodeError, ValueError) as exc:
            print(f"cannot read {args.expect}: {exc}", file=sys.stderr)
            return 2
        if not isinstance(published, dict):
            print(f"{args.expect} is not a JSON object", file=sys.stderr)
            return 2
        try:
            payload_names = _snapshot_payload_names(published)
        except PayloadKindAuditError as exc:
            print(f"cannot use {args.expect}: {exc}", file=sys.stderr)
            return 2

    try:
        audit = build_audit(args.corpus, payload_names=payload_names)
    except PayloadKindAuditError as exc:
        print(f"payload-kind audit failed: {exc}", file=sys.stderr)
        return 2

    if published is not None:
        problems = _drift(audit, published)
        if problems:
            for problem in problems:
                print(f"DRIFT  {problem}", file=sys.stderr)
            return 1
        print(f"published audit matches a fresh scan of {args.corpus}")
        return 0

    if args.markdown:
        sys.stdout.write(render_markdown(audit))
    else:
        json.dump(audit, sys.stdout, indent=2, sort_keys=False)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
