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
import json
import sys
from pathlib import Path
from typing import Any, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parent))

from curate_identity import IdentityCurationError, record_kind  # noqa: E402

SCHEMA_VERSION = "1.0.0"

# A coding episode is the ``goal`` + ``steps`` shape. A thalamic gate record may
# *wrap* one under ``executed_action``; that wrapped episode is real coding
# supervision, but it is not reachable by a loader that expects a top-level
# episode.
EPISODE_MARKERS = ("goal", "steps")

# Step-level reasoning fields. ``decision_basis`` is the observable form this
# factory's curation contract requires; ``thought`` is the legacy hidden form.
REASONING_FIELDS = ("thought", "decision_basis", "reflection")


class PayloadKindAuditError(ValueError):
    """The corpus cannot be audited without guessing."""


def _is_episode_shaped(value: Any) -> bool:
    return isinstance(value, Mapping) and all(key in value for key in EPISODE_MARKERS)


def _steps(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Mapping):
        return []
    steps = value.get("steps")
    if not isinstance(steps, list):
        return []
    return [step for step in steps if isinstance(step, Mapping)]


def _record_row(record: Mapping[str, Any], source_file: str, line: int, digest: str) -> dict:
    kind = record_kind(record)
    row: dict[str, Any] = {
        "source_file": source_file,
        "source_line": line,
        "kind": kind,
        "sha256": digest,
    }
    if kind == "thalamic":
        state = record.get("state") if isinstance(record.get("state"), Mapping) else {}
        gate = (
            record.get("safety_decision")
            if isinstance(record.get("safety_decision"), Mapping)
            else {}
        )
        executed = record.get("executed_action")
        row["id"] = state.get("episode_id")
        row["domain"] = state.get("domain")
        row["supervisor_id"] = gate.get("supervisor_id")
        row["gate_decision"] = gate.get("decision")
        row["wraps_coding_episode"] = _is_episode_shaped(executed)
        row["coding_steps"] = len(_steps(executed))
    else:
        # Episode records in this lane carry no top-level identifier; they are
        # addressable only by ``source_file:source_line``. That is reported,
        # never invented.
        row["id"] = record.get("id")
        row["domain"] = None
        row["wraps_coding_episode"] = False
        row["coding_steps"] = len(_steps(record))
    return row


def _reasoning_counts(record: Mapping[str, Any], kind: str) -> dict[str, int]:
    owner = record.get("executed_action") if kind == "thalamic" else record
    counts = {field: 0 for field in REASONING_FIELDS}
    for step in _steps(owner):
        for field in REASONING_FIELDS:
            if field in step:
                counts[field] += 1
    return counts


def build_audit(corpus: Path) -> dict:
    """Return the deterministic payload-kind audit of one corpus directory."""
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

    for path in sorted(corpus.glob("*.jsonl")):
        if path.is_symlink() or not path.is_file():
            raise PayloadKindAuditError(f"unsafe payload entry: {path}")
        raw = path.read_bytes()
        file_kinds: dict[str, int] = {}
        count = 0
        for line_number, line in enumerate(raw.decode("utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise PayloadKindAuditError(f"{path.name}:{line_number}: {exc}") from exc
            if not isinstance(record, dict):
                raise PayloadKindAuditError(
                    f"{path.name}:{line_number}: record must be a JSON object"
                )
            digest = hashlib.sha256(line.encode("utf-8")).hexdigest()
            try:
                row = _record_row(record, path.name, line_number, digest)
            except IdentityCurationError as exc:
                raise PayloadKindAuditError(f"{path.name}:{line_number}: {exc}") from exc
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
            for field, value in _reasoning_counts(record, kind).items():
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
        gate = row.get("supervisor_id") or "—"
        decision = row.get("gate_decision")
        if decision:
            gate = f"{gate} / {decision}"
        record_id = f"`{row['id']}`" if row.get("id") else "—"
        lines.append(
            f"| `{row['source_file']}:{row['source_line']}` | {row['kind']} | "
            f"{record_id} | {gate} | {'yes' if row['wraps_coding_episode'] else 'no'} | "
            f"{row['coding_steps']} |"
        )
    return "\n".join(lines) + "\n"


def _drift(derived: Mapping[str, Any], published: Mapping[str, Any]) -> list[str]:
    problems = []
    for key, value in derived.items():
        if key not in published:
            problems.append(f"published audit is missing {key!r}")
        elif published[key] != value:
            problems.append(f"{key} differs from the published audit")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("corpus", type=Path, help="directory of published *.jsonl")
    parser.add_argument("--markdown", action="store_true", help="emit the record table")
    parser.add_argument(
        "--expect",
        type=Path,
        default=None,
        help="compare against a published audit JSON and fail on drift",
    )
    args = parser.parse_args(argv)

    try:
        audit = build_audit(args.corpus)
    except PayloadKindAuditError as exc:
        print(f"payload-kind audit failed: {exc}", file=sys.stderr)
        return 2

    if args.expect is not None:
        try:
            published = json.loads(args.expect.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            print(f"cannot read {args.expect}: {exc}", file=sys.stderr)
            return 2
        if not isinstance(published, dict):
            print(f"{args.expect} is not a JSON object", file=sys.stderr)
            return 2
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
