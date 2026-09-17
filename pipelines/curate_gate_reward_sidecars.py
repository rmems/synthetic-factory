#!/usr/bin/env python3
"""Reward-source sidecar authentication for the curation gate.

Split out of ``curate_gate.py`` (CodeScene: Lines of Code in a Single File) by
responsibility; every name is re-exported from ``curate_gate`` so existing
``curate_gate.X`` call sites resolve unchanged. The semantics this module
checks against live in ``curate_gate_reward``.

A reward sidecar is the sealed record of what a reward *was* before the reward
lane touched it. This gate walks the sidecar artifacts copied into the cleaned
governance tree and proves three things about them, per record and fail-closed:

* every sidecar has one source identity, and no two sidecars claim the same one;
* every reward-annotated final row resolves to exactly one sidecar whose source
  path, line and record digest match the row's authenticated final-output
  binding, whose reward values still hash to the sealed bytes, and whose
  semantics survive the independent re-derivation in ``curate_gate_reward``;
* every *orphan* sidecar -- one no final row links -- belongs to a source
  record the lanes excluded or quarantined, with a matching source digest.

Anything that fails is reported as an invalid link with its reason rather than
raised, so one bad sidecar does not hide the rest of the corpus.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, NamedTuple, Sequence

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("curate_gate_reward_sidecars")
    from . import curate_gate_contract as _contract
    from . import curate_gate_digest as _digest
    from . import curate_gate_evidence as _evidence
    from . import curate_gate_paths as _paths
    from . import curate_gate_records as _records
    from . import curate_gate_reward as _reward
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "curate_gate_reward_sidecars"
    )
    _PIPELINES = Path(__file__).resolve().parent
    if str(_PIPELINES) not in sys.path:
        sys.path.insert(0, str(_PIPELINES))
    import curate_gate_contract as _contract
    import curate_gate_digest as _digest
    import curate_gate_evidence as _evidence
    import curate_gate_paths as _paths
    import curate_gate_records as _records
    import curate_gate_reward as _reward

GateError = _contract.GateError
GOVERNANCE_DIRNAME = _contract.GOVERNANCE_DIRNAME
REWARD_SIDECAR_DIRNAME = _contract.REWARD_SIDECAR_DIRNAME
EXCLUSION_ACTIONS = _contract.EXCLUSION_ACTIONS
QUARANTINE_ACTIONS = _contract.QUARANTINE_ACTIONS

record_sha256 = _digest.record_sha256
_normalized_sha256 = _digest._normalized_sha256
_load_reward_sidecars = _evidence._load_reward_sidecars
_logical_source_path = _paths._logical_source_path
iter_records = _records.iter_records
# The reward vocabulary is reached through the semantics sibling that already
# owns it, so this module declares one dependency rather than two.
curate_rewards = _reward.curate_rewards
_pointer_value = _reward._pointer_value
_authenticate_reward_semantics = _reward._authenticate_reward_semantics
_reward_calibration_catalog = _reward._reward_calibration_catalog

# Every sidecar names the source record it sealed; three checks share the refusal.
_SOURCE_NOT_AN_OBJECT = "sidecar source must be an object"


# ---------------------------------------------------------------------------
# loading the sealed sidecar artifacts
# ---------------------------------------------------------------------------


class _SidecarIndex(NamedTuple):
    """Every sidecar the governance tree holds, plus what refused to load."""

    sidecars: dict[str, dict[str, Any]]
    artifact_paths: list[Path]
    invalid: list[dict[str, str]]


def _registered_source_key(
    source: Any,
    sidecar_sources: dict[tuple[str, int], str],
) -> tuple[str, int]:
    if not isinstance(source, dict):
        raise GateError(_SOURCE_NOT_AN_OBJECT)
    source_key = (
        _logical_source_path(source.get("path"), "sidecar source.path"),
        source.get("line"),
    )
    line = source_key[1]
    if not isinstance(line, int) or isinstance(line, bool) or line < 1:
        raise GateError("sidecar source.line must be a positive integer")
    if source_key in sidecar_sources:
        raise GateError(f"sidecar source identity duplicates {sidecar_sources[source_key]}")
    return source_key


def _register_sidecar(
    document: dict[str, Any],
    label: str,
    index: _SidecarIndex,
    sidecar_sources: dict[tuple[str, int], str],
) -> None:
    sidecar_id = document["sidecar_id"]
    if sidecar_id in index.sidecars:
        index.invalid.append({"source": label, "error": f"duplicate sidecar_id {sidecar_id}"})
        return
    index.sidecars[sidecar_id] = document
    try:
        source_key = _registered_source_key(document.get("source"), sidecar_sources)
    except GateError as exc:
        index.invalid.append({"source": label, "error": str(exc)})
        return
    sidecar_sources[source_key] = sidecar_id


def _load_sidecar_index(cleaned: Path) -> _SidecarIndex:
    sidecar_root = cleaned / GOVERNANCE_DIRNAME / REWARD_SIDECAR_DIRNAME
    artifact_paths = (
        [path for path in sorted(sidecar_root.rglob("*")) if path.is_file()]
        if sidecar_root.is_dir()
        else []
    )
    index = _SidecarIndex({}, artifact_paths, [])
    sidecar_sources: dict[tuple[str, int], str] = {}
    for path in artifact_paths:
        label = path.relative_to(cleaned).as_posix()
        try:
            documents = _load_reward_sidecars(path)
        except GateError as exc:
            index.invalid.append({"source": label, "error": str(exc)})
            continue
        for document in documents:
            _register_sidecar(document, label, index, sidecar_sources)
    return index


# ---------------------------------------------------------------------------
# what the lanes say about each source record
# ---------------------------------------------------------------------------


class _LaneSources(NamedTuple):
    """Source-record facts the prepared lanes authenticated."""

    known_keys: set[tuple[str, int]]
    terminal_keys: set[tuple[str, int]]
    record_hashes: dict[tuple[str, int], str]
    records: dict[tuple[str, int], Any]


def _lane_sources(prepared_lanes: Sequence[dict[str, Any]]) -> _LaneSources:
    sources = _LaneSources(set(), set(), {}, {})
    for lane in prepared_lanes:
        for entry in lane["entries"]:
            source_key = entry["_source_key"]
            sources.known_keys.add(source_key)
            action = str(entry.get("action") or "").strip().lower()
            if action in EXCLUSION_ACTIONS | QUARANTINE_ACTIONS:
                sources.terminal_keys.add(source_key)
            source_record = entry.get("_source_record")
            if source_record is not None:
                sources.record_hashes[source_key] = record_sha256(source_record)
                sources.records[source_key] = source_record
    return sources


# ---------------------------------------------------------------------------
# per-record authentication
# ---------------------------------------------------------------------------


class _RecordLink(NamedTuple):
    """One reward-annotated final row and the sidecar it names."""

    record: dict[str, Any]
    annotation: dict[str, Any]
    sidecar: dict[str, Any]
    sidecar_id: Any
    key: tuple[str, int]

    @property
    def where(self) -> str:
        return f"{self.key[0]}:{self.key[1]}"


class _LinkState(NamedTuple):
    """Everything a link is authenticated against, plus the used-sidecar ledger."""

    bindings_by_output: dict[tuple[str, int], dict[str, Any]]
    lane_sources: _LaneSources
    calibration_catalog: dict[str, dict[str, Any]]
    used_sidecars: dict[str, str]


def _assert_sidecar_binding(
    sidecar: dict[str, Any],
    binding: dict[str, Any],
    where: str,
) -> None:
    source = sidecar.get("source")
    if not isinstance(source, dict):
        raise curate_rewards.RewardOntologyError(_SOURCE_NOT_AN_OBJECT)
    sidecar_source_path = _logical_source_path(source.get("path"), f"{where} sidecar source.path")
    sidecar_source_line = source.get("line")
    if (
        sidecar_source_path != binding["source_path"]
        or sidecar_source_line != binding["source_line"]
    ):
        raise curate_rewards.RewardOntologyError(
            "sidecar source identity mismatches final record binding"
        )
    source_record_sha256 = _normalized_sha256(
        source.get("record_sha256"), f"{where} sidecar source.record_sha256"
    )
    if source_record_sha256 != binding["source_record_sha256"]:
        raise curate_rewards.RewardOntologyError(
            "sidecar source record digest mismatches final record binding"
        )


def _assert_sidecar_rewards(
    record: dict[str, Any],
    sidecar: dict[str, Any],
    source_record: dict[str, Any] | None,
    where: str,
) -> None:
    for reward in sidecar["source_rewards"]:
        current = _pointer_value(record, reward.get("json_pointer"))
        expected_hash = _normalized_sha256(
            reward.get("value_sha256"), f"{where} sidecar reward value_sha256"
        )
        if record_sha256(reward.get("value")) != expected_hash:
            raise curate_rewards.RewardOntologyError("source reward sidecar value hash mismatch")
        if record_sha256(current) != expected_hash:
            raise curate_rewards.RewardOntologyError(
                f"record reward differs from sidecar at {reward.get('json_pointer')}"
            )
        if isinstance(source_record, dict):
            source_value = _pointer_value(source_record, reward.get("json_pointer"))
            if record_sha256(source_value) != record_sha256(reward.get("value")):
                raise curate_rewards.RewardOntologyError(
                    "sidecar reward does not match authenticated source at "
                    f"{reward.get('json_pointer')}"
                )


def _authenticate_link(link: _RecordLink, state: _LinkState) -> None:
    curate_rewards.validate_ontology_document(link.annotation)
    binding = state.bindings_by_output.get(link.key)
    if binding is None:
        raise curate_rewards.RewardOntologyError(
            "reward annotation has no authenticated final-output binding"
        )
    _assert_sidecar_binding(link.sidecar, binding, link.where)
    first_use = state.used_sidecars.get(link.sidecar_id)
    if first_use is not None:
        raise curate_rewards.RewardOntologyError(
            f"sidecar is linked by more than one final record (first {first_use})"
        )
    source_key = (binding["source_path"], binding["source_line"])
    candidate = state.lane_sources.records.get(source_key)
    source_record = candidate if isinstance(candidate, dict) else None
    _authenticate_reward_semantics(
        link.annotation,
        _reward.RewardSemanticsInputs(
            link.record,
            link.sidecar,
            state.calibration_catalog,
            source_record,
        ),
    )
    _assert_sidecar_rewards(link.record, link.sidecar, source_record, link.where)


def _link_sidecars(
    cleaned: Path,
    index: _SidecarIndex,
    state: _LinkState,
) -> tuple[int, list[str]]:
    """Bind every reward-annotated row to its sidecar; report, never raise."""
    linked = 0
    missing: list[str] = []
    for relative, line, record in iter_records(cleaned):
        if not isinstance(record, dict):
            continue
        annotation = record.get(curate_rewards.ANNOTATION_FIELD)
        if not isinstance(annotation, dict):
            continue
        where = f"{relative}:{line}"
        sidecar_id = annotation.get("source_sidecar_id")
        sidecar = index.sidecars.get(sidecar_id)
        if sidecar is None:
            missing.append(where)
            continue
        try:
            _authenticate_link(
                _RecordLink(record, annotation, sidecar, sidecar_id, (relative, line)),
                state,
            )
        except (curate_rewards.RewardOntologyError, GateError) as exc:
            index.invalid.append({"source": where, "error": str(exc)})
            continue
        state.used_sidecars[sidecar_id] = where
        linked += 1
    return linked, missing


# ---------------------------------------------------------------------------
# orphans: a sidecar no final row links must name a terminal source record
# ---------------------------------------------------------------------------


def _assert_terminal_sidecar(
    sidecar: dict[str, Any],
    lane_sources: _LaneSources,
    final_source_keys: set[tuple[str, int]],
) -> None:
    source = sidecar.get("source")
    if not isinstance(source, dict):
        raise GateError(_SOURCE_NOT_AN_OBJECT)
    source_key = (
        _logical_source_path(source.get("path"), "sidecar source.path"),
        source.get("line"),
    )
    if source_key not in lane_sources.known_keys:
        raise GateError("orphan sidecar source is absent from lane evidence")
    if source_key in final_source_keys or source_key not in lane_sources.terminal_keys:
        raise GateError("reward sidecar has no bound final or terminal source record")
    expected_source_record_hash = lane_sources.record_hashes.get(source_key)
    if (
        expected_source_record_hash is not None
        and _normalized_sha256(source.get("record_sha256"), "sidecar source.record_sha256")
        != expected_source_record_hash
    ):
        raise GateError("terminal sidecar source record digest mismatches source evidence")


def _count_terminal_sidecars(
    index: _SidecarIndex,
    orphan_ids: Sequence[str],
    lane_sources: _LaneSources,
    final_source_keys: set[tuple[str, int]],
) -> int:
    terminal_sidecars = 0
    for sidecar_id in orphan_ids:
        try:
            _assert_terminal_sidecar(index.sidecars[sidecar_id], lane_sources, final_source_keys)
            terminal_sidecars += 1
        except GateError as exc:
            index.invalid.append({"source": sidecar_id, "error": str(exc)})
    return terminal_sidecars


# ---------------------------------------------------------------------------
# the gate
# ---------------------------------------------------------------------------


class _SidecarTally(NamedTuple):
    """The counts the gate report is rendered from."""

    linked: int
    missing: list[str]
    orphan_ids: list[str]
    terminal_sidecars: int


def _sidecar_report(index: _SidecarIndex, tally: _SidecarTally) -> dict[str, Any]:
    return {
        "tool": "curate_rewards reward-source sidecar verifier",
        "passed": not tally.missing and not index.invalid,
        "artifact_files": len(index.artifact_paths),
        "sidecars": len(index.sidecars),
        "linked_records": tally.linked,
        "missing_sidecars": len(tally.missing),
        "orphan_sidecars": len(tally.orphan_ids),
        "terminal_sidecars": tally.terminal_sidecars,
        "invalid_links": len(index.invalid),
        "examples": [
            *(
                {"source": source, "error": "source_sidecar_id does not resolve"}
                for source in tally.missing[:5]
            ),
            *index.invalid[:5],
        ][:5],
    }


def _reward_sidecar_gate(
    cleaned: Path,
    bindings: Sequence[dict[str, Any]],
    prepared_lanes: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    index = _load_sidecar_index(cleaned)
    calibration_catalog = _reward_calibration_catalog(prepared_lanes)
    binding_by_output = {
        (binding["output_path"], binding["output_line"]): binding for binding in bindings
    }
    final_source_keys = {(binding["source_path"], binding["source_line"]) for binding in bindings}
    state = _LinkState(
        binding_by_output,
        _lane_sources(prepared_lanes),
        calibration_catalog,
        {},
    )
    linked, missing = _link_sidecars(cleaned, index, state)

    orphan_ids = sorted(set(index.sidecars) - set(state.used_sidecars))
    terminal_sidecars = _count_terminal_sidecars(
        index,
        orphan_ids,
        state.lane_sources,
        final_source_keys,
    )
    return _sidecar_report(
        index,
        _SidecarTally(linked, missing, orphan_ids, terminal_sidecars),
    )


if __package__:
    _expose_package_sibling(__name__)
