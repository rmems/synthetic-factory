#!/usr/bin/env python3
"""Read-only payload-kind audit for one published raw JSONL corpus.

A dataset slug names a *topic*; the records name a *shape*. When a Hub card
advertises one kind of record and the payload holds a mix, a consumer that
trusts the card writes a loader that crashes on the first record of the other
shape. This module measures the mix rather than asserting it: it walks one
corpus directory, classifies every record with the curation lane's own
:func:`curate_identity.record_kind`, and returns a deterministic audit.

It never writes to the corpus. The only output is JSON or Markdown on stdout.

Parse, Markdown, scan, expect/drift, and CLI helpers live in sibling modules
so each file's complexity stays under analyzer gates. Public callers still
``import payload_kind_audit``.

Usage::

    python3 pipelines/payload_kind_audit.py <corpus-dir> [--json|--markdown]
    python3 pipelines/payload_kind_audit.py <corpus-dir> --expect <audit.json>

``--expect`` re-derives the audit and exits non-zero naming each field that has
drifted from a published audit, so a committed audit cannot quietly go stale.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parent))

from curate_identity import LEGACY_ID_KEYS as LEGACY_ID_KEYS  # noqa: E402
from payload_kind_audit_cli import run_main  # noqa: E402
from payload_kind_audit_markdown import render_markdown  # noqa: E402
from payload_kind_audit_parse import (  # noqa: E402
    PayloadKindAuditError,
    _resolve_payload_paths,
    _validate_reported_name,
)
from payload_kind_audit_scan import (  # noqa: E402
    _AuditStats,
    _first_legacy_id as _first_legacy_id,
    _scan_payload_file,
)

SCHEMA_VERSION = "1.0.0"

__all__ = [
    "SCHEMA_VERSION",
    "LEGACY_ID_KEYS",
    "PayloadKindAuditError",
    "_first_legacy_id",
    "build_audit",
    "main",
    "render_markdown",
]


def build_audit(corpus: Path, payload_names: Iterable[str] | None = None) -> dict:
    """Return a deterministic audit of the whole corpus or one named snapshot."""
    corpus = Path(corpus)
    if corpus.is_symlink() or not corpus.is_dir():
        raise PayloadKindAuditError(f"not a readable corpus directory: {corpus}")
    # Validate before scanning so we never emit an audit ``--expect`` rejects.
    _validate_reported_name(corpus.name, kind="corpus directory name")

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


def main(argv: list[str] | None = None) -> int:
    return run_main(build_audit, __doc__.splitlines()[0], argv)


if __name__ == "__main__":
    raise SystemExit(main())
