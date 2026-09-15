#!/usr/bin/env python3
"""Governance-evidence loading for the curation gate.

Split out of ``curate_gate.py`` (CodeScene: Lines of Code in a Single File) by
responsibility; every name is re-exported from ``curate_gate`` so existing
``curate_gate.X`` call sites resolve unchanged.

The reward lane pairs its outputs with a ``reward_source_sidecars`` JSONL
artifact. This module parses that artifact from captured bytes and validates
every document against the reward ontology before the lane is admitted.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_gate_evidence")
    from . import curate_gate_contract as _contract
    from . import curate_gate_digest as _digest
    from . import curate_rewards
    from .check_records import reject_json_constant
    from .exact_json import parse_finite_json_float
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_gate_evidence"
    )
    _PIPELINES = Path(__file__).resolve().parent
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    import curate_gate_contract as _contract
    import curate_gate_digest as _digest
    import curate_rewards
    from check_records import reject_json_constant
    from exact_json import parse_finite_json_float

GateError = _contract.GateError
_lf_lines = _digest._lf_lines
_read_regular_file_snapshot = _digest._read_regular_file_snapshot


def _load_reward_sidecars(
    path: Path,
    *,
    payload: bytes | None = None,
) -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []
    if payload is None:
        payload, _digest, _size = _read_regular_file_snapshot(path, "reward sidecars")
    try:
        text = payload.decode("utf-8")
    except UnicodeError as exc:
        raise GateError(f"cannot decode reward sidecars {path}: {exc}") from exc
    for line_number, line in enumerate(_lf_lines(text), 1):
        if not line.strip():
            continue
        try:
            document = json.loads(
                line,
                parse_constant=reject_json_constant,
                parse_float=parse_finite_json_float,
            )
        except ValueError as exc:
            raise GateError(f"{path}:{line_number}: invalid reward sidecar JSON: {exc}") from exc
        if (
            not isinstance(document, dict)
            or document.get("document_type") != "reward_source_sidecar"
        ):
            raise GateError(f"{path}:{line_number}: expected a reward_source_sidecar document")
        try:
            curate_rewards.validate_ontology_document(document)
        except curate_rewards.RewardOntologyError as exc:
            raise GateError(f"{path}:{line_number}: invalid reward sidecar: {exc}") from exc
        documents.append(document)
    if not documents:
        raise GateError(f"{path}: reward sidecar artifact is empty")
    ids = [document["sidecar_id"] for document in documents]
    if len(ids) != len(set(ids)):
        raise GateError(f"{path}: duplicate reward sidecar_id")
    return documents


if __package__:
    _expose_package_sibling(__name__)
