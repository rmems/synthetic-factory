#!/usr/bin/env python3
"""Read-only training-readiness audit for a synthetic-factory run tree.

Unlike ``validate_run.py`` (record shape) and ``check_records.py`` (per-record
invariants), this audit measures corpus-level risks: identity/provenance
coverage, preference-pair purity, reward-schema entropy, tag reuse, duplicate
content, length distribution, bridge event fidelity, and the raster/gate-SNN
coverage an SNN distillation run needs (20-50 ms excerpt per bridge record,
routing table, ``spikes = round(neurons * rate * window_s)``, and at least one
spike-implemented gate head). The spike arithmetic itself is owned by
``curate_bridge``; this module only counts and reports it.

Usage: python3 pipelines/training_audit.py [--strict] [--markdown] <run_dir>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Mapping

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("training_audit")
    from . import census as _census
    from . import check_records as _check_records
    from . import distillation_audit as _distillation_audit
    from . import strict_jsonl as _strict_jsonl
    from . import tag_jsonutil as _tag_jsonutil
    from . import training_audit_observe as _observe
    from . import training_audit_record as _record_audit
    from . import training_audit_report as _report
    from . import training_audit_snapshot as _snapshot
    from . import training_audit_rights as _rights_audit
    from . import training_audit_completion as _completion
    from . import validate_run as _validate_run
    from .exact_json import (
        parse_finite_json_float as _parse_exact_json_float,
    )
    from .round_txn import TransactionError
    from .training_audit_bridge import event_stream_status as _event_stream_status
    from .training_audit_mill import index_mill_quarantine
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)("training_audit")
    import census as _census
    import check_records as _check_records
    import distillation_audit as _distillation_audit
    import strict_jsonl as _strict_jsonl
    import tag_jsonutil as _tag_jsonutil
    import training_audit_observe as _observe
    import training_audit_record as _record_audit
    import training_audit_report as _report
    import training_audit_snapshot as _snapshot
    import training_audit_rights as _rights_audit
    import training_audit_completion as _completion
    import validate_run as _validate_run
    from exact_json import (
        parse_finite_json_float as _parse_exact_json_float,
    )
    from round_txn import TransactionError
    from training_audit_bridge import event_stream_status as _event_stream_status
    from training_audit_mill import index_mill_quarantine

# Live seams: ``_CorpusAudit`` hands this module to the observers in
# ``training_audit_observe``/``training_audit_axes``, which read these names
# back through ``self.api`` at call time, so they stay bound on the facade.
factory_for_path = _census.factory_for_path
ALLOWED_PROVENANCE = _check_records.ALLOWED_PROVENANCE
canonical_record_id = _check_records.canonical_record_id
check_record = _check_records.check_record
expected_states = _check_records.expected_states
reject_json_constant = _check_records.reject_json_constant
root_record_id = _check_records.root_record_id
shape_check = _check_records.shape_check
walk_key = _check_records.walk_key
DistillationAudit = _distillation_audit.DistillationAudit
build_report = _report.build_report
StrictJsonlError = _strict_jsonl.StrictJsonlError
reject_duplicate_object_keys = _tag_jsonutil.reject_duplicate_object_keys
check_episode = _validate_run.check_episode
episode_like = _validate_run.episode_like
_percentile = _report.percentile
_render_markdown = _report.render_markdown

_PIPELINES = Path(__file__).resolve().parent

# Compatibility exports retained for callers that imported the factory slugs
# from this module before distillation accounting moved into its own helper.
BRIDGE_FACTORY_SLUG = _distillation_audit.BRIDGE_FACTORY_SLUG
THALAMIC_FACTORY_SLUG = _distillation_audit.THALAMIC_FACTORY_SLUG
OUROBOROS_FACTORY_SLUG = _distillation_audit.OUROBOROS_FACTORY_SLUG

def event_stream_status(events, enclosing=None):
    """Compatibility facade for the extracted bridge audit classifier."""
    return _event_stream_status(events, enclosing)


def percentile(values, fraction):
    """Compatibility facade for the extracted report percentile helper."""
    return _percentile(values, fraction)


canonical_blob = _record_audit.canonical_blob
CURATED_FORBIDDEN_REASONING_KEYS = _record_audit.CURATED_FORBIDDEN_REASONING_KEYS
dict_field = _record_audit.dict_field
has_observable_decision_basis = _record_audit.has_observable_decision_basis
is_hidden_thought_key = _record_audit.is_hidden_thought_key
_semantic_context_value = _record_audit.canonical_numeric_value
_reward_shape_type = _record_audit.reward_shape_type
_normalized_goals = _record_audit.normalized_goals
_list_field = _record_audit.list_field


def thalamic_views(obj, kind):
    """Compatibility facade for record views."""
    yield from _record_audit.thalamic_views(obj, kind)


def wrapped_agentic_episodes(obj, kind):
    """Walk embedded episodes through the facade's live view seam."""
    yield from _record_audit.wrapped_agentic_episodes(obj, kind, view_reader=thalamic_views)


def reward_shape(value):
    """Classify rewards through the facade's live value-type seam."""
    return _record_audit.reward_shape(value, shape_type=_reward_shape_type)


def _thalamic_context_purity(chosen, rejected):
    return _record_audit.thalamic_context_purity(
        chosen,
        rejected,
        canonicalize=_semantic_context_value,
    )


def _episode_context_purity(obj, chosen, rejected):
    return _record_audit.episode_context_purity(
        obj,
        chosen,
        rejected,
        normalize_goals=_normalized_goals,
    )


def preference_context_purity(obj, chosen, rejected):
    """Measure pair context through the facade's live purity seams."""
    return _record_audit.preference_context_purity(
        obj,
        chosen,
        rejected,
        _record_audit.PreferencePurityReaders(
            episode_like,
            _episode_context_purity,
            _thalamic_context_purity,
        ),
    )


def _preference_turns(obj):
    yield from _record_audit.preference_turns(
        obj,
        mapping_reader=dict_field,
        episode_check=episode_like,
        list_reader=_list_field,
    )


def _coordination_turns(obj):
    yield from _record_audit.coordination_turns(obj, list_reader=_list_field)


def agentic_turns(obj, kind):
    """Walk agentic turns through the facade's live routing seams."""
    yield from _record_audit.agentic_turns(
        obj,
        kind,
        _record_audit.AgenticTurnReaders(
            _list_field,
            _preference_turns,
            _coordination_turns,
            wrapped_agentic_episodes,
        ),
    )


def hidden_thought_paths(value, path=""):
    """Walk nested values through the facade's live key-classifier seam."""
    yield from _record_audit.hidden_thought_paths(
        value,
        path,
        key_classifier=is_hidden_thought_key,
    )


def _parse_finite_json_float(text: str) -> float:
    """Decode a JSON float token without accepting exponent overflow."""

    return _parse_exact_json_float(text)


_PINNED_DIRECTORY_FLAGS = _snapshot.PINNED_DIRECTORY_FLAGS
_open_audit_descriptor = _snapshot.open_audit_descriptor
_read_regular_audit_descriptor = _snapshot.read_regular_audit_descriptor


def _read_pinned_member(run_dir: Path, relative: Path) -> bytes:
    """Read through the compatibility facade's descriptor seams."""
    return _snapshot.read_pinned_member(
        run_dir,
        relative,
        open_descriptor=_open_audit_descriptor,
        read_descriptor=_read_regular_audit_descriptor,
    )


_marker_digest_index = _snapshot.marker_digest_index


def _require_committed_digest(
    payload: bytes,
    relative: Path,
    marker_root: Path | None,
    digest_cache: dict[Path, dict[str, str]],
) -> None:
    """Check committed bytes through the facade's manifest-index seam."""
    _snapshot.require_bound_committed_digest(
        payload,
        relative,
        _snapshot.DigestBinding(
            marker_root,
            digest_cache,
            _marker_digest_index,
        ),
    )


_scanned_audit_entries = _snapshot.scan_audit_entries
_classified_audit_entry = _snapshot.classify_audit_entry


def _enumerated_run_members(run_dir: Path) -> list[Path]:
    """Enumerate through the facade's scanner and classifier seams."""
    return _snapshot.enumerate_run_members(
        run_dir,
        scan_entries=_scanned_audit_entries,
        classify_entry=_classified_audit_entry,
    )


def _run_membership(run_dir: Path) -> tuple[frozenset[Path], tuple[Path, ...]]:
    """Resolve membership through the facade's enumerator seam."""
    return _snapshot.run_membership(
        run_dir,
        enumerate_members=_enumerated_run_members,
    )


def _capture_run_member(
    run_dir: Path,
    relative: Path,
    visible: frozenset[Path],
    digest_cache: dict[Path, dict[str, str]],
) -> tuple[Path, bytes] | None:
    """Compatibility facade for one snapshot member capture."""
    capture = _snapshot.SnapshotCapture(
        run_dir,
        visible,
        _read_pinned_member,
        _require_committed_digest,
    )
    capture.digest_cache = digest_cache
    return capture.member(relative)


def _captured_run_files(run_dir: Path) -> list[tuple[Path, bytes]]:
    """Compatibility facade for a stable, authenticated run snapshot."""
    visible, members = _run_membership(run_dir)
    digest_cache: dict[Path, dict[str, str]] = {}
    files = []
    for relative in members:
        captured = _capture_run_member(
            run_dir,
            relative,
            visible,
            digest_cache,
        )
        if captured is not None:
            files.append(captured)
    if _run_membership(run_dir) != (visible, members):
        raise ValueError("audit member set changed while capturing the run snapshot")
    return files


_validated_snapshot_path = _snapshot.validate_snapshot_path
_validated_snapshot_member = _snapshot.validate_snapshot_member
_validated_snapshot_files = _snapshot.validate_snapshot_files


class _CorpusAudit(_observe.CorpusAudit):
    """Mutable counters for one read-only training-audit pass.

    The pipeline lives in ``training_audit_observe``; this subclass only
    injects the live facade module as the seam namespace so every helper name
    it calls still resolves on ``training_audit`` at call time.
    """

    def __init__(self, run_dir, mill_findings_by_ref, mill_mix):
        super().__init__(
            sys.modules[__name__], run_dir, mill_findings_by_ref, mill_mix
        )


def audit_run(
    run_dir: Path,
    *,
    snapshot: Mapping[str, bytes] | None = None,
    completion_source: Path | None = None,
):
    """Audit one immutable byte snapshot.

    Normal callers get a snapshot captured from ``run_dir`` once at entry.
    Exporters may pass the already-authenticated bytes they will publish, which
    prevents the audit and writer from observing different filesystem states.
    """

    run_dir = Path(run_dir).resolve()
    files = (
        _captured_run_files(run_dir) if snapshot is None else _validated_snapshot_files(snapshot)
    )
    mill_findings, mill_mix = index_mill_quarantine(run_dir, files)
    rights_audit = _rights_audit.capture_rights_audit(run_dir, dict(files))
    audit = _CorpusAudit(run_dir, mill_findings, mill_mix)
    audit.rights_audit = rights_audit
    audit.completion_source = completion_source or rights_audit.source_run
    for relative, payload in files:
        audit.observe_file(relative, payload)
    return audit.report()


def render_markdown(report):
    """Compatibility facade for the extracted report renderer."""
    return _render_markdown(report)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="exit 1 when blockers exist")
    parser.add_argument("--markdown", action="store_true", help="render concise Markdown")
    parser.add_argument("run_dir")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    try:
        report = audit_run(Path(args.run_dir))
    except (TransactionError, ValueError) as exc:
        print(f"training_audit failed: {exc}", file=sys.stderr)
        return 1
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if args.strict and report["blockers"] else 0


if __package__:
    _expose_package_sibling(__name__)


if __name__ == "__main__":
    raise SystemExit(main())
