#!/usr/bin/env python3
"""Replay authentication: prove the published compose artifacts reproduce.

Split out of ``export_replay.py`` by responsibility. These checks compare a
replayed source snapshot against what was published: manifest documents,
reward sidecars, curated output declarations and payloads, COMPOSE.json
counts, and the calibration evidence identity observed across the replay.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

import compose_curated  # noqa: E402
import compose_curated_rights  # noqa: E402
from compose_contract import default_units_migration_path  # noqa: E402
from export_calibration import _authenticated_calibration  # noqa: E402
from export_contract import CuratedFile, ExportError  # noqa: E402
from export_members import _stable_file_identity  # noqa: E402


@dataclass(frozen=True)
class _PublishedReplay:
    """Published artifacts that one source replay must authenticate."""

    summary: dict[str, Any]
    actual_outputs: dict[str, CuratedFile]
    manifest_documents: Sequence[Any]
    sidecar_documents: Sequence[Any]


def _require_replayed_documents(
    snapshot,
    manifest_documents: Sequence[Any],
    sidecar_documents: Sequence[Any],
) -> None:
    """The published manifest and sidecars must replay row for row."""

    if list(manifest_documents) != snapshot.expected_manifest:
        raise ExportError(
            "compose manifest does not reproduce from the authenticated current source snapshot"
        )
    if list(sidecar_documents) != snapshot.expected_sidecars:
        raise ExportError(
            "reward sidecars do not reproduce from the authenticated current source snapshot"
        )


def _require_replayed_outputs(
    snapshot,
    summary: dict[str, Any],
    actual_outputs: dict[str, CuratedFile],
) -> None:
    """The declared and emitted curated outputs must replay byte for byte."""

    if summary.get("outputs") != snapshot.expected_outputs:
        raise ExportError("COMPOSE.json: output declarations do not reproduce from source")
    if set(actual_outputs) != set(snapshot.expected_payloads):
        raise ExportError("curated output paths do not reproduce from the source snapshot")
    for output_path, payload in snapshot.expected_payloads.items():
        if actual_outputs[output_path].payload != payload:
            raise ExportError(f"curated output bytes do not reproduce: {output_path}")


def _require_replayed_counts(snapshot, summary: dict[str, Any]) -> None:
    """Every published aggregate must replay under the same transforms."""

    expected = {
        "counts": {
            "source_files": snapshot.counts["source_files"],
            "source_records": snapshot.counts["source_records"],
            "blank_lines": snapshot.counts["blank_lines"],
            "retained": snapshot.counts["retained"],
            "excluded": snapshot.counts["excluded"],
            "output_files": snapshot.counts["output_files"],
            "reward_sidecars": snapshot.counts["reward_sidecars"],
        },
        "lane_actions": {
            lane: dict(sorted(actions.items())) for lane, actions in snapshot.lane_actions.items()
        },
        "exclusions": dict(sorted(snapshot.exclusions.items())),
        "transforms": compose_curated.transform_contract(),
        "rights": compose_curated_rights.rights_summary(snapshot),
    }
    failures = {
        "counts": "COMPOSE.json: source/output counts do not reproduce",
        "lane_actions": "COMPOSE.json: lane action counts do not reproduce",
        "exclusions": "COMPOSE.json: exclusions do not reproduce",
        "transforms": "COMPOSE.json: transform declarations do not match this contract",
        "rights": "COMPOSE.json: rights summary does not reproduce",
    }
    for field_name, expected_value in expected.items():
        if summary.get(field_name) != expected_value:
            raise ExportError(failures[field_name])


def _verify_replay_matches_context(
    snapshot,
    published: _PublishedReplay,
) -> None:
    """Raise ``ExportError`` unless every declared artifact reproduces from ``snapshot``."""

    _require_replayed_documents(snapshot, published.manifest_documents, published.sidecar_documents)
    _require_replayed_outputs(snapshot, published.summary, published.actual_outputs)
    _require_replayed_counts(snapshot, published.summary)


def _verify_replay_matches(
    snapshot,
    **published: Any,
) -> None:
    """Adapt the historical keyword-only artifacts to published context."""

    _verify_replay_matches_context(
        snapshot,
        _PublishedReplay(**published),
    )


def _require_calibration_state_unchanged(
    expected: tuple[Any, ...], current: tuple[Any, ...]
) -> None:
    """Refuse a source replay that crossed calibration evidence states."""

    if current != expected:
        raise ExportError("calibration evidence changed during source replay")


def _calibration_evidence_identity(
    descriptor: dict[str, Any], source_root: Path
) -> tuple[Any, ...]:
    """Identity token for already-authenticated calibration evidence."""

    if descriptor["mode"] == "none":
        return "none", str(default_units_migration_path(source_root))
    path = Path(descriptor["path"])
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise ExportError("calibration evidence changed during source replay") from exc
    return "file", str(path), *_stable_file_identity(metadata)


def _authenticated_calibration_state(
    summary: dict[str, Any], source_root: Path
) -> tuple[dict[str, Any], dict[str, Any], tuple[Any, ...]]:
    """Return catalog, descriptor, and its post-authentication identity token."""

    catalog, descriptor = _authenticated_calibration(summary, source_root)
    return catalog, descriptor, _calibration_evidence_identity(descriptor, source_root)
