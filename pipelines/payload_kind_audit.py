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
import math
import sys
from dataclasses import dataclass
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


# ``curate_identity._legacy_ids`` collects every ``LEGACY_ID_KEYS`` form from
# the owner, its ``meta``, and its ``state``. The audit searches the same three
# containers in the same order so it cannot render ``—`` for an identifier the
# curation lane would recognize.
_LEGACY_ID_CONTAINERS = ("meta", "state")


def _legacy_id_containers(record: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
    yield record
    for name in _LEGACY_ID_CONTAINERS:
        nested = record.get(name)
        if isinstance(nested, Mapping):
            yield nested


def _first_legacy_id(record: Mapping[str, Any]) -> Any:
    """Return the first present identifier supported by identity curation.

    Precedence is container-major then key-minor, matching
    ``curate_identity._legacy_ids``: every top-level alias outranks every
    ``meta`` alias, which outranks every ``state`` alias.
    """
    for container in _legacy_id_containers(record):
        for key in LEGACY_ID_KEYS:
            if key in container:
                return container[key]
    return None


@dataclass(frozen=True)
class _ParsedLine:
    """One classified JSONL record, ready to become a row and feed stats."""

    record: Mapping[str, Any]
    kind: str
    steps: list[Mapping[str, Any]]
    source_file: str
    line: int
    digest: str


def _thalamic_row_fields(parsed: _ParsedLine) -> dict:
    where = f"{parsed.source_file}:{parsed.line}"
    state = _required_mapping(parsed.record, "state", where)
    gate = _required_mapping(parsed.record, "safety_decision", where)
    # The schema's canonical, globally unique identifier is the top-level
    # ``id``. ``state.episode_id`` is a legacy fallback for records that
    # predate it.
    top_level_id = parsed.record.get("id")
    return {
        "id": top_level_id if top_level_id is not None else state.get("episode_id"),
        "domain": state.get("domain"),
        "supervisor_id": gate.get("supervisor_id"),
        "gate_decision": gate.get("decision"),
        "wraps_coding_episode": _is_episode_shaped(parsed.record.get("executed_action")),
        "coding_steps": len(parsed.steps),
    }


def _episode_row_fields(parsed: "_ParsedLine") -> dict:
    # The published episodes in this lane carry no top-level identifier, but
    # other episode corpora use legacy aliases. Report the first alias the
    # identity curation contract recognizes; never invent one.
    return {
        "id": _first_legacy_id(parsed.record),
        "domain": None,
        "wraps_coding_episode": False,
        "coding_steps": len(parsed.steps),
    }


# The row fields copied verbatim out of a record. Everything else on a row is
# derived here (a digest, a count, a coordinate) and cannot carry a corpus
# value out unchanged or otherwise.
_EMITTED_RECORD_FIELDS = ("id", "domain", "supervisor_id", "gate_decision")


def _reject_rounded_fields(fields: Mapping[str, Any], where: str) -> None:
    """Reject emitted metadata a binary float cannot carry back out unchanged.

    ``parse_float`` turns every JSON decimal into a Python float, so a literal
    like ``0.1234567890123456789`` would be reported — and pinned by
    ``--expect`` — as a different value than the corpus holds. That is true of
    every field this audit republishes, not just the identifier, and of a
    decimal nested inside a container-valued field, which is emitted just as
    verbatim. Integers and strings round-trip exactly, so only the decimal
    case fails closed.
    """
    for name in _EMITTED_RECORD_FIELDS:
        _reject_rounded_value(fields.get(name), name, where)


def _reject_rounded_value(value: Any, name: str, where: str) -> None:
    """Reject a decimal at ``name`` or anywhere inside a container it holds."""
    if isinstance(value, float):
        raise PayloadKindAuditError(
            f"{where}: record {name} is a JSON decimal this audit cannot "
            f"report exactly: {value!r}"
        )
    if isinstance(value, Mapping):
        for key, item in value.items():
            _reject_rounded_value(item, f"{name}.{key}", where)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_rounded_value(item, f"{name}[{index}]", where)


def _record_row(parsed: _ParsedLine) -> dict:
    row: dict[str, Any] = {
        "source_file": parsed.source_file,
        "source_line": parsed.line,
        "kind": parsed.kind,
        "sha256": parsed.digest,
    }
    fields = _thalamic_row_fields(parsed) if parsed.kind == "thalamic" else _episode_row_fields(parsed)
    _reject_rounded_fields(fields, f"{parsed.source_file}:{parsed.line}")
    row.update(fields)
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


def _parse_finite_float(value: str) -> float:
    """Parse one JSON number without accepting binary-float overflow."""
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError(f"JSON number is outside the finite float range: {value!r}")
    return parsed


def _reject_duplicate_object_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject repeated object keys at every depth instead of last-key-wins."""
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON object key {key!r}")
        value[key] = item
    return value


def _is_unpaired_surrogate(character: str) -> bool:
    return 0xD800 <= ord(character) <= 0xDFFF


def _reject_unpaired_surrogates_in_string(value: str) -> None:
    if any(_is_unpaired_surrogate(character) for character in value):
        raise ValueError("unpaired UTF-16 surrogate in JSON string")


def _reject_unpaired_surrogates_in_mapping(value: Mapping) -> None:
    for key, item in value.items():
        _reject_unpaired_surrogates(key)
        _reject_unpaired_surrogates(item)


def _reject_unpaired_surrogates_in_list(value: list) -> None:
    for item in value:
        _reject_unpaired_surrogates(item)


def _reject_unpaired_surrogates(value: Any) -> None:
    """Reject strings the UTF-8 stdout path cannot encode."""
    if isinstance(value, str):
        _reject_unpaired_surrogates_in_string(value)
    elif isinstance(value, Mapping):
        _reject_unpaired_surrogates_in_mapping(value)
    elif isinstance(value, list):
        _reject_unpaired_surrogates_in_list(value)


def _is_json_whitespace(value: str) -> bool:
    """Return whether non-empty text contains only RFC 8259 JSON whitespace."""
    return bool(value) and all(character in " \t\r\n" for character in value)


def _jsonl_lines(raw: bytes, source_file: str):
    """Yield LF-delimited UTF-8 records without splitting on Unicode separators."""
    segments = raw.split(b"\n")
    last_index = len(segments) - 1
    for line_number, line_bytes in enumerate(segments, 1):
        # CRLF is one record terminator, so neither byte belongs to the record
        # digest. Strip the paired CR only on segments that were actually
        # terminated by LF. A bare CR on the final unterminated segment stays
        # in the payload, matching the curation reader.
        lf_terminated = line_number - 1 != last_index
        if lf_terminated and line_bytes.endswith(b"\r"):
            line_bytes = line_bytes[:-1]
        try:
            line = line_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise PayloadKindAuditError(
                f"{source_file}:{line_number}: payload is not valid UTF-8: {exc}"
            ) from exc
        yield line_number, line_bytes, line


def _is_safe_jsonl_name(name: Any) -> bool:
    if not isinstance(name, str):
        return False
    if not name.endswith(".jsonl"):
        return False
    return Path(name).name == name


def _validate_payload_name(name: Any) -> None:
    """A snapshot payload name must be a bare ``*.jsonl`` filename, not a path."""
    if not _is_safe_jsonl_name(name):
        raise PayloadKindAuditError(f"unsafe snapshot payload name: {name!r}")


def _resolve_named_payload_paths(corpus: Path, payload_names: Iterable[str]) -> list[Path]:
    names = list(payload_names)
    for name in names:
        _validate_payload_name(name)
    if len(names) != len(set(names)):
        raise PayloadKindAuditError("snapshot payload names must be unique")
    return [corpus / name for name in sorted(names)]


def _resolve_payload_paths(corpus: Path, payload_names: Iterable[str] | None) -> list[Path]:
    """Return the sorted ``*.jsonl`` paths to scan, validating any explicit names."""
    if payload_names is None:
        payload_paths = sorted(corpus.glob("*.jsonl"))
    else:
        payload_paths = _resolve_named_payload_paths(corpus, payload_names)
    if not payload_paths:
        raise PayloadKindAuditError(f"corpus contains no *.jsonl payloads: {corpus}")
    return payload_paths


def _load_payload_bytes(path: Path) -> bytes:
    """Read one payload file after rejecting symlinks and non-files."""
    if path.is_symlink() or not path.is_file():
        raise PayloadKindAuditError(f"unsafe payload entry: {path}")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise PayloadKindAuditError(f"cannot read payload {path}: {exc}") from exc


def _parse_json_record(source_file: str, line_number: int, line: str) -> dict:
    """Parse one JSONL line into a JSON object, or raise PayloadKindAuditError."""
    try:
        record = json.loads(
            line,
            object_pairs_hook=_reject_duplicate_object_keys,
            parse_constant=_reject_json_constant,
            parse_float=_parse_finite_float,
        )
        _reject_unpaired_surrogates(record)
    except (json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise PayloadKindAuditError(f"{source_file}:{line_number}: {exc}") from exc
    if not isinstance(record, dict):
        raise PayloadKindAuditError(f"{source_file}:{line_number}: record must be a JSON object")
    return record


def _classify_record_kind(record: Mapping[str, Any], source_file: str, line_number: int) -> str:
    """Classify one record, or raise PayloadKindAuditError outside this audit's scope."""
    try:
        kind = record_kind(record)
    except IdentityCurationError as exc:
        raise PayloadKindAuditError(f"{source_file}:{line_number}: {exc}") from exc
    if kind not in SUPPORTED_RECORD_KINDS:
        raise PayloadKindAuditError(
            f"{source_file}:{line_number}: payload kind {kind!r} is outside this episode/thalamic audit"
        )
    return kind


def _parse_payload_line(
    source_file: str, line_number: int, line_bytes: bytes, line: str
) -> _ParsedLine:
    """Parse, validate, and classify one non-blank JSONL line."""
    record = _parse_json_record(source_file, line_number, line)
    digest = hashlib.sha256(line_bytes).hexdigest()
    kind = _classify_record_kind(record, source_file, line_number)
    steps = _coding_steps(record, kind, f"{source_file}:{line_number}")
    return _ParsedLine(record, kind, steps, source_file, line_number, digest)


class _AuditStats:
    """Corpus-wide totals accumulated one classified record at a time."""

    def __init__(self) -> None:
        self.kinds: dict[str, int] = {}
        self.factories: dict[str, int] = {}
        self.native_steps = 0
        self.embedded_steps = 0
        self.wrapping = 0
        self.reasoning = {field: 0 for field in REASONING_FIELDS}

    def add(self, parsed: _ParsedLine, row: Mapping[str, Any]) -> None:
        kind = row["kind"]
        self.kinds[kind] = self.kinds.get(kind, 0) + 1
        meta = parsed.record.get("meta")
        factory = meta.get("factory") if isinstance(meta, Mapping) else None
        if isinstance(factory, str):
            self.factories[factory] = self.factories.get(factory, 0) + 1
        if kind == "thalamic":
            self.embedded_steps += row["coding_steps"]
            if row["wraps_coding_episode"]:
                self.wrapping += 1
        else:
            self.native_steps += row["coding_steps"]
        for field, value in _reasoning_counts(parsed.steps).items():
            self.reasoning[field] += value

    def summary(self, *, files: int, records: int) -> dict:
        return {
            "files": files,
            "records": records,
            "kinds": dict(sorted(self.kinds.items())),
            "meta_factory_stamps": dict(sorted(self.factories.items())),
            "thalamic_records_wrapping_a_coding_episode": self.wrapping,
            "coding_episodes_reachable_at_top_level": self.kinds.get("episode", 0),
            "coding_episodes_including_wrapped": self.kinds.get("episode", 0) + self.wrapping,
            "coding_steps": {
                "native": self.native_steps,
                "wrapped": self.embedded_steps,
                "total": self.native_steps + self.embedded_steps,
            },
            "coding_steps_by_reasoning_field": dict(sorted(self.reasoning.items())),
        }


def _scan_payload_file(path: Path, stats: _AuditStats) -> tuple[list[dict], dict]:
    """Parse one payload file, feeding corpus-wide stats and returning its rows."""
    raw = _load_payload_bytes(path)
    rows: list[dict] = []
    file_kinds: dict[str, int] = {}
    for line_number, line_bytes, line in _jsonl_lines(raw, path.name):
        if not line or _is_json_whitespace(line):
            continue
        parsed = _parse_payload_line(path.name, line_number, line_bytes, line)
        row = _record_row(parsed)
        stats.add(parsed, row)
        file_kinds[row["kind"]] = file_kinds.get(row["kind"], 0) + 1
        rows.append(row)
    file_summary = {
        "path": path.name,
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "records": len(rows),
        "kinds": dict(sorted(file_kinds.items())),
    }
    return rows, file_summary


def build_audit(corpus: Path, payload_names: Iterable[str] | None = None) -> dict:
    """Return a deterministic audit of the whole corpus or one named snapshot."""
    corpus = Path(corpus)
    if corpus.is_symlink() or not corpus.is_dir():
        raise PayloadKindAuditError(f"not a readable corpus directory: {corpus}")

    payload_paths = _resolve_payload_paths(corpus, payload_names)

    files: list[dict] = []
    records: list[dict] = []
    stats = _AuditStats()
    for path in payload_paths:
        rows, file_summary = _scan_payload_file(path, stats)
        records.extend(rows)
        files.append(file_summary)

    if not records:
        raise PayloadKindAuditError(f"corpus contains no auditable records: {corpus}")

    return {
        "schema_version": SCHEMA_VERSION,
        "source": corpus.name,
        "summary": stats.summary(files=len(files), records=len(records)),
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
        supervisor_id = row.get("supervisor_id")
        gate = _markdown_cell(supervisor_id) if supervisor_id is not None else "—"
        decision = row.get("gate_decision")
        if decision is not None:
            gate = f"{gate} / {_markdown_cell(decision)}"
        record_id = _markdown_code(row["id"]) if row.get("id") is not None else "—"
        source = _markdown_code(f"{row['source_file']}:{row['source_line']}")
        lines.append(
            f"| {source} | {_markdown_cell(row['kind'])} | "
            f"{record_id} | {gate} | {'yes' if row['wraps_coding_episode'] else 'no'} | "
            f"{row['coding_steps']} |"
        )
    return "\n".join(lines) + "\n"


# ``json.loads`` decodes an escaped C0/C1 control such as ``\u001b`` into the
# raw byte, which neither ``html.escape`` nor the pipe/bracket escaping above
# neutralizes, so ``--markdown`` would write it straight to a terminal or a
# card. Render every remaining control as its visible ``\uXXXX`` source form.
# CR and LF are absent by the time this runs: they become ``<br>`` first.
_MARKDOWN_CONTROL_ESCAPES = {
    code: f"\\u{code:04x}"
    for code in (*range(0x00, 0x20), 0x7F, *range(0x80, 0xA0))
}


def _markdown_cell(value: Any) -> str:
    rendered = html.escape(str(value), quote=False)
    return (
        rendered.replace("|", "&#124;")
        # Escaped so a gate value like "![tracker](url)" renders as literal
        # text instead of an active Markdown image or link.
        .replace("[", "&#91;")
        .replace("]", "&#93;")
        .replace("\r\n", "<br>")
        .replace("\r", "<br>")
        .replace("\n", "<br>")
        .translate(_MARKDOWN_CONTROL_ESCAPES)
    )


def _markdown_code(value: Any) -> str:
    text = str(value)
    if not any(marker in text for marker in ("`", "|", "\r", "\n")):
        return f"`{_markdown_cell(text)}`"
    return f"<code>{_markdown_cell(text)}</code>"


def _json_equal(left: Any, right: Any) -> bool:
    """Compare JSON values without Python's bool/int/float equivalence."""
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            _json_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            _json_equal(first, second) for first, second in zip(left, right)
        )
    return left == right


def _drift(derived: Mapping[str, Any], published: Mapping[str, Any]) -> list[str]:
    problems = []
    for key, value in derived.items():
        if key not in published:
            problems.append(f"published audit is missing {key!r}")
        elif not _json_equal(published[key], value):
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


def _build_arg_parser() -> argparse.ArgumentParser:
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
    return parser


def _load_expected_audit(path: Path) -> tuple[dict, list[str]]:
    """Load and validate one ``--expect`` file, or raise ``PayloadKindAuditError``
    with the exact diagnostic ``main`` prints for each failure mode."""
    try:
        published = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_object_keys,
            parse_constant=_reject_json_constant,
            parse_float=_parse_finite_float,
        )
        # A published audit may carry supplementary fields ``_drift`` never
        # compares (``card_disclosure.markdown``, for one). Validate the whole
        # document so an unpaired surrogate the corpus parser would reject is
        # a controlled input error here too, rather than an exit 0 blessing
        # evidence this tool could not itself have emitted.
        _reject_unpaired_surrogates(published)
    except (OSError, UnicodeError, ValueError, RecursionError) as exc:
        raise PayloadKindAuditError(f"cannot read {path}: {exc}") from exc
    if not isinstance(published, dict):
        raise PayloadKindAuditError(f"{path} is not a JSON object")
    try:
        payload_names = _snapshot_payload_names(published)
    except PayloadKindAuditError as exc:
        raise PayloadKindAuditError(f"cannot use {path}: {exc}") from exc
    return published, payload_names


def _report_drift(audit: Mapping[str, Any], published: Mapping[str, Any], corpus: Path) -> int:
    problems = _drift(audit, published)
    if problems:
        for problem in problems:
            print(f"DRIFT  {problem}", file=sys.stderr)
        return 1
    print(f"published audit matches a fresh scan of {corpus}")
    return 0


def _emit_audit(audit: Mapping[str, Any], *, markdown: bool) -> None:
    if markdown:
        sys.stdout.write(render_markdown(audit))
    else:
        json.dump(audit, sys.stdout, indent=2, sort_keys=False, allow_nan=False)
        sys.stdout.write("\n")


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)

    published = None
    payload_names = None
    if args.expect is not None:
        try:
            published, payload_names = _load_expected_audit(args.expect)
        except PayloadKindAuditError as exc:
            print(str(exc), file=sys.stderr)
            return 2

    try:
        audit = build_audit(args.corpus, payload_names=payload_names)
    except PayloadKindAuditError as exc:
        print(f"payload-kind audit failed: {exc}", file=sys.stderr)
        return 2

    if published is not None:
        return _report_drift(audit, published, args.corpus)

    _emit_audit(audit, markdown=args.markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
