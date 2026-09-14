#!/usr/bin/env python3
"""Round-file I/O shared by the hardware-parity and NIR-equivalence CLIs.

One reader and one writer, so the two families cannot drift on how a
``batch-rNN.jsonl`` line is framed, parsed, or serialized.
"""

from __future__ import annotations

import json
from pathlib import Path

from . import envelope
from .import_twins import bind_import_twin

try:
    from pipelines.exact_json import dumps_exact_json
except ImportError:  # pipelines/ on sys.path, the direct CLI form
    from exact_json import dumps_exact_json


def read_jsonl(path):
    """Parse a round file line by line; every unparseable line is one finding.

    Bytes, not ``read_text()``: universal-newline translation would turn a
    bare CR into a line break and frame one physical line as two records,
    where ``validate_run``'s byte reader rejects the extra value.
    """
    records = []
    errors = []
    source = Path(path)
    try:
        text = source.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return [], [f"{source}: cannot read file: {exc}"]
    for lineno, raw_line in enumerate(text.split("\n"), 1):
        line = raw_line[:-1] if raw_line.endswith("\r") else raw_line
        if not line.strip():
            continue
        try:
            records.append(
                json.loads(
                    line,
                    parse_constant=envelope.reject_json_constant,
                    parse_float=envelope.reject_nonfinite_float,
                )
            )
        # ValueError covers json.JSONDecodeError and the two parse hooks'
        # refusals; RecursionError makes an absurdly nested line a line-level
        # finding rather than a traceback that aborts the scan.
        except (ValueError, RecursionError) as exc:
            errors.append(f"{source.name}:{lineno}: JSON parse error: {exc}")
    return records, errors


def write_jsonl(path, records):
    """Write one round as JSONL, through the repository's exact encoder.

    `dumps_exact_json`, not `json.dumps`: a round file is evidence other
    tools digest, and `json.dumps` renders an `ExactJSONFloat` through
    `repr`, silently dropping the decimal token it was read with. Nothing in
    these families produces such a value today; this keeps the writer honest
    if one ever reaches it, and its compact form makes each written line the
    same text `canonical_json` hashes.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(
        dumps_exact_json(record, ensure_ascii=False, sort_keys=True) + "\n"
        for record in records
    )
    with path.open("x", encoding="utf-8") as handle:
        handle.write(payload)


bind_import_twin(__name__)
