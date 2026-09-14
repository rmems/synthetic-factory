#!/usr/bin/env python3
"""Corpus record iteration for the curation gate.

Split out of ``curate_gate.py`` (CodeScene: Lines of Code in a Single File) by
responsibility; every name is re-exported from ``curate_gate`` so existing
``curate_gate.X`` call sites resolve unchanged.

One leaf: walking a cleaned or curated tree's JSONL files and yielding every
non-blank line as ``(relative_path, line_number, parsed_record)``. A line that
does not parse yields ``None`` rather than raising, because the gates that
consume it report an invalid row as a finding instead of aborting the run.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Iterable

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_gate_records")
    from . import curate_gate_digest as _digest
    from .check_records import reject_json_constant
    from .exact_json import parse_finite_json_float
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_gate_records"
    )
    _PIPELINES = Path(__file__).resolve().parent
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    import curate_gate_digest as _digest
    from check_records import reject_json_constant
    from exact_json import parse_finite_json_float

jsonl_paths = _digest.jsonl_paths
_lf_lines = _digest._lf_lines


def iter_records(root: Path) -> Iterable[tuple[str, int, Any]]:
    """Yield ``(relative_path, line_number, parsed_record)`` for the corpus."""
    for path in jsonl_paths(root):
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        for number, line in enumerate(_lf_lines(text), 1):
            if not line.strip():
                continue
            try:
                obj = json.loads(
                    line,
                    parse_constant=reject_json_constant,
                    parse_float=parse_finite_json_float,
                )
            except ValueError:
                yield rel, number, None
                continue
            yield rel, number, obj


if __package__:
    _expose_package_sibling(__name__)
