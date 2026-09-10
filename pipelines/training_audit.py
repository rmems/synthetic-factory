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
import hashlib
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Mapping

if __package__:
    from . import distillation_audit as _distillation_audit
    from . import training_audit_record as _record_audit
    from . import training_audit_snapshot as _snapshot
    from .census import factory_for_path
    from .check_records import (
        ALLOWED_PROVENANCE,
        canonical_record_id,
        check_record,
        expected_states,
        reject_json_constant,
        root_record_id,
        shape_check,
        walk_key,
    )
    from .distillation_audit import DistillationAudit
    from .exact_json import (
        parse_finite_json_float as _parse_exact_json_float,
    )
    from .round_txn import TransactionError
    from .training_audit_bridge import event_stream_status as _event_stream_status
    from .training_audit_mill import index_mill_quarantine
    from .training_audit_report import (
        build_report,
        percentile as _percentile,
        render_markdown as _render_markdown,
    )
    from .strict_jsonl import StrictJsonlError, strict_lf_jsonl_records
    from .tag_jsonutil import reject_duplicate_object_keys
    from .validate_run import check_episode, episode_like
else:
    import distillation_audit as _distillation_audit
    import training_audit_record as _record_audit
    import training_audit_snapshot as _snapshot
    from census import factory_for_path
    from check_records import (
        ALLOWED_PROVENANCE,
        canonical_record_id,
        check_record,
        expected_states,
        reject_json_constant,
        root_record_id,
        shape_check,
        walk_key,
    )
    from distillation_audit import DistillationAudit
    from exact_json import (
        parse_finite_json_float as _parse_exact_json_float,
    )
    from round_txn import TransactionError
    from training_audit_bridge import event_stream_status as _event_stream_status
    from training_audit_mill import index_mill_quarantine
    from training_audit_report import (
        build_report,
        percentile as _percentile,
        render_markdown as _render_markdown,
    )
    from strict_jsonl import StrictJsonlError, strict_lf_jsonl_records
    from tag_jsonutil import reject_duplicate_object_keys
    from validate_run import check_episode, episode_like

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


class _CorpusAudit:
    """Mutable counters for one read-only training-audit pass."""

    def __init__(self, run_dir, mill_findings_by_ref, mill_mix):
        self.run_dir = run_dir
        self.mill_findings_by_ref = mill_findings_by_ref
        self.mill_mix = mill_mix
        self.factories = defaultdict(
            lambda: {
                "files": 0,
                "records": 0,
                "eligible_records": 0,
                "bytes": 0,
                "approx_tokens": 0,
                "exact_json_contract_errors": 0,
                "by_kind": Counter(),
                "record_tokens": [],
            }
        )
        self.totals = Counter()
        self.code_repair = Counter()
        self.code_repair_reasons = Counter()
        self.kinds = Counter()
        self.record_errors = []
        self.unresolved_record_warnings = []
        self.ids = {}
        self.root_ids = {}
        self.canonical_id_records = 0
        self.root_id_records = 0
        self.missing_ids = []
        self.missing_root_ids = []
        self.duplicate_ids = []
        self.content_seen = {}
        self.exact_duplicates = []
        self.provenance = Counter()
        self.provenance_examples = defaultdict(list)
        self.gate_by_role = defaultdict(Counter)
        self.gate_errors = Counter()
        self.gate_error_examples = []
        # Keep historic keys present for an all-episode preference corpus.
        self.preference = Counter(
            pairs=0,
            same_context=0,
            same_state=0,
            same_proposal=0,
            same_goal=0,
            episode_pairs=0,
            thalamic_pairs=0,
        )
        self.chosen_decisions = Counter()
        self.reward_keys = Counter()
        self.reward_shapes = Counter()
        self.tags = Counter()
        self.distillation = DistillationAudit()
        self.episodes = Counter(
            episodes=0,
            steps=0,
            decision_basis_steps=0,
            missing_decision_basis_steps=0,
            legacy_thought_only_steps=0,
            hidden_thought_fields=0,
        )
        self.hidden_thought_examples = []

    def observe_file(self, relative, payload=None):
        if payload is None:
            path = Path(relative)
            rel = path.relative_to(self.run_dir)
            payload = path.read_bytes()
        else:
            rel = Path(relative)
        factory = factory_for_path(self.run_dir, self.run_dir / rel)
        bucket = self.factories[factory]
        bucket["files"] += 1
        bucket["bytes"] += len(payload)
        self.totals["files"] += 1
        self.totals["bytes"] += len(payload)

        try:
            raw_lines = strict_lf_jsonl_records(payload, rel.as_posix())
        except StrictJsonlError as exc:
            self.record_errors.append(str(exc))
            return
        for line_number, raw_line in enumerate(raw_lines, 1):
            self._observe_line(raw_line, line_number, rel, factory)

    def _observe_line(self, raw_line, line_number, rel, factory):
        if not raw_line.strip():
            return
        bucket = self.factories[factory]
        where = f"{rel}:{line_number}"
        try:
            line = raw_line.decode("utf-8")
        except UnicodeDecodeError as exc:
            self.record_errors.append(f"{where}: invalid UTF-8: {exc}")
            return

        self.totals["records"] += 1
        bucket["records"] += 1
        token_estimate = max(1, math.ceil(len(line.encode("utf-8")) / 4))
        try:
            obj = json.loads(
                line,
                object_pairs_hook=reject_duplicate_object_keys,
                parse_constant=reject_json_constant,
                parse_float=_parse_finite_json_float,
            )
        except (ValueError, RecursionError) as exc:
            self._record_parse_error(where, exc, token_estimate, bucket)
            return

        finding = self.mill_findings_by_ref.get((rel.as_posix(), line_number))
        procedural_route = self._registered_code_repair_route(obj, factory)
        if finding is not None and not procedural_route:
            # Foreign evidence is excluded before every training invariant,
            # including the exact-JSON serialization contract.
            self.totals["quarantined"] += 1
            return
        try:
            canonical_blob(obj)
        except (ValueError, RecursionError) as exc:
            self._record_exact_json_contract_error(where, exc, token_estimate, bucket)
            return

        self._account_tokens(token_estimate, bucket)
        self._observe_valid_record(obj, where, factory)

    @staticmethod
    def _registered_code_repair_route(obj, factory):
        """Return whether path-derived registry authority permits procedural validation."""
        if not isinstance(obj, dict) or obj.get("family") != "python-function-repair":
            return False
        if __package__:
            from .curate_identity import default_registry
        else:
            from curate_identity import default_registry
        row = default_registry().by_path_id.get(factory)
        return (
            row is not None
            and row.identity_authoritative
            and "code_repair" in row.record_kinds
        )

    def _observe_valid_record(self, obj, where, factory):
        bucket = self.factories[factory]
        if isinstance(obj, dict) and obj.get("family") == "python-function-repair":
            self._observe_code_repair(obj, where, factory, bucket)
            return
        self.totals["eligible_records"] += 1
        bucket["eligible_records"] += 1
        kind = self._observe_record(obj, where, factory)
        self.kinds[kind] += 1
        bucket["by_kind"][kind] += 1

    def _observe_code_repair(self, obj, where, factory, bucket):
        if __package__:
            from .curate_identity import default_registry
            from .code_repair.admission import natural_eligibility
            from .code_repair.source_policy import SourcePolicyError
        else:
            from curate_identity import default_registry
            from code_repair.admission import natural_eligibility
            from code_repair.source_policy import SourcePolicyError
        self.kinds["code_repair"] += 1
        bucket["by_kind"]["code_repair"] += 1
        self.code_repair["records"] += 1
        row = default_registry().by_path_id.get(factory)
        try:
            eligible, reasons = natural_eligibility(obj, row)
        except SourcePolicyError as exc:
            self.code_repair["invalid_records"] += 1
            self.record_errors.append(f"{where}: {exc}")
            return
        self._observe_identity(obj, obj["id"], where)
        self._observe_duplicate(obj, where)
        if not eligible:
            self.code_repair["evidence_only_records"] += 1
            self.code_repair_reasons.update(reasons)
            return
        self.code_repair["eligible_records"] += 1
        self.totals["eligible_records"] += 1
        bucket["eligible_records"] += 1

    def _record_parse_error(self, where, exc, token_estimate, bucket):
        self._account_tokens(token_estimate, bucket)
        self.record_errors.append(f"{where}: JSON parse error: {exc}")
        self.kinds["unknown"] += 1
        bucket["by_kind"]["unknown"] += 1

    def _record_exact_json_contract_error(self, where, exc, token_estimate, bucket):
        self._account_tokens(token_estimate, bucket)
        self.totals["exact_json_contract_errors"] += 1
        bucket["exact_json_contract_errors"] += 1
        self.record_errors.append(f"{where}: exact JSON contract error: {exc}")
        self.kinds["exact_json_contract_error"] += 1
        bucket["by_kind"]["exact_json_contract_error"] += 1

    def _account_tokens(self, token_estimate, bucket):
        self.totals["approx_tokens"] += token_estimate
        bucket["approx_tokens"] += token_estimate
        bucket["record_tokens"].append(token_estimate)

    def _observe_record(self, obj, where, factory):
        errors, warnings, kind, checked_id = check_record(
            obj,
            where,
            factory_staging=self._strict_agentic(obj),
        )
        self.record_errors.extend(errors)
        self._observe_embedded_episodes(obj, kind, where)
        self._observe_warnings(warnings)
        self._observe_identity(obj, checked_id, where)
        self._observe_duplicate(obj, where)
        self._observe_provenance(obj, kind, where)
        self._observe_gates(obj, kind, where)
        self._observe_preference(obj, kind)
        self._observe_vocabulary(obj)
        self.distillation.observe(
            factory=factory,
            where=where,
            kind=kind,
            record=obj,
        )
        self._observe_agentic(obj, kind, where)
        return kind

    @staticmethod
    def _strict_agentic(obj):
        if not isinstance(obj, dict):
            return False
        keys = obj.keys()
        direct = any(
            required <= keys
            for required in (
                {"case_type"},
                {"transcript", "agents"},
                {"steps", "outcome", "reward"},
            )
        )
        preference = {"chosen", "rejected"} <= keys and any(
            episode_like(obj.get(side)) for side in ("chosen", "rejected")
        )
        return direct or preference

    def _observe_embedded_episodes(self, obj, kind, where):
        for embedded_path, embedded in wrapped_agentic_episodes(obj, kind):
            embedded_where = f"{where}.{embedded_path}"
            if "steps" in embedded:
                errors, _kind = shape_check(
                    embedded,
                    embedded_where,
                    factory_staging=True,
                )
            else:
                errors = check_episode(
                    embedded,
                    embedded_where,
                    forbid_hidden_thought=True,
                    enforce_terminal_outcome=True,
                )
            self.record_errors.extend(errors)

    def _observe_warnings(self, warnings):
        ignored = (
            "missing canonical record id",
            "missing top-level id",
            "missing sim_or_real",
            "non-training provenance",
            "uses legacy 'thought'",
        )
        self.unresolved_record_warnings.extend(
            warning for warning in warnings if not any(item in warning for item in ignored)
        )

    def _observe_identity(self, obj, checked_id, where):
        record_id = checked_id or canonical_record_id(obj)
        if record_id is None:
            self.missing_ids.append(where)
        else:
            self.canonical_id_records += 1
            if record_id in self.ids:
                self.duplicate_ids.append(
                    {"id": record_id, "first": self.ids[record_id], "again": where}
                )
            else:
                self.ids[record_id] = where

        root_id = root_record_id(obj)
        if root_id is None:
            self.missing_root_ids.append(where)
        else:
            self.root_id_records += 1
            self.root_ids.setdefault(root_id, where)

    def _observe_duplicate(self, obj, where):
        digest = hashlib.sha256(canonical_blob(obj).encode("utf-8")).hexdigest()
        if digest in self.content_seen:
            self.exact_duplicates.append({"first": self.content_seen[digest], "again": where})
        else:
            self.content_seen[digest] = where

    def _observe_provenance(self, obj, kind, where):
        for state_path, state in expected_states(obj, kind):
            value = state.get("sim_or_real") if isinstance(state, dict) else None
            if value is None:
                label = "missing"
            elif value in ALLOWED_PROVENANCE:
                label = str(value)
            else:
                label = "non_training"
            self.provenance[label] += 1
            if len(self.provenance_examples[label]) < 5:
                self.provenance_examples[label].append(f"{where}:{state_path}={value!r}")

    def _observe_gates(self, obj, kind, where):
        for role, trajectory in thalamic_views(obj, kind):
            decision = dict_field(trajectory, "safety_decision")
            label = decision.get("decision")
            if isinstance(label, str):
                self.gate_by_role[role][label] += 1
            error_type = dict_field(trajectory, "meta").get("supervisor_error_type")
            if decision.get("correctness") == "incorrect" or error_type:
                self._observe_gate_error(error_type, where, role)

    def _observe_gate_error(self, error_type, where, role):
        self.gate_errors["marked"] += 1
        self.gate_errors[str(error_type) if error_type else "unspecified"] += 1
        if len(self.gate_error_examples) < 5:
            self.gate_error_examples.append(f"{where}:{role}")

    def _observe_preference(self, obj, kind):
        if kind != "preference":
            return
        self.preference["pairs"] += 1
        chosen = dict_field(obj, "chosen")
        rejected = dict_field(obj, "rejected")
        purity = preference_context_purity(obj, chosen, rejected)
        self.preference["episode_pairs"] += int(purity["episode_pair"])
        self.preference["thalamic_pairs"] += int(not purity["episode_pair"])
        self.preference["same_context"] += int(purity["pure"])
        if purity["same_state"] is not None:
            self.preference["same_state"] += int(purity["same_state"])
            self.preference["same_proposal"] += int(purity["same_proposal"])
        if purity["same_goal"] is not None:
            self.preference["same_goal"] += int(purity["same_goal"])
        decision = dict_field(chosen, "safety_decision").get("decision")
        if isinstance(decision, str):
            self.chosen_decisions[decision] += 1

    def _observe_vocabulary(self, obj):
        for _path, reward in walk_key(obj, "reward_components"):
            self._observe_reward(reward)
        for _path, values in walk_key(obj, "tags"):
            self._observe_tags(values)

    def _observe_reward(self, reward):
        if isinstance(reward, dict):
            self.reward_keys.update(reward.keys())
        self.reward_shapes[reward_shape(reward)] += 1

    def _observe_tags(self, values):
        if isinstance(values, list):
            self.tags.update(value for value in values if isinstance(value, str))

    def _observe_agentic(self, obj, kind, where):
        self.episodes["episodes"] += int(kind == "episode")
        for hidden_path in hidden_thought_paths(obj):
            self._observe_hidden_thought(hidden_path, where)
        for turn in agentic_turns(obj, kind):
            self._observe_agentic_turn(turn)

    def _observe_hidden_thought(self, hidden_path, where):
        self.episodes["hidden_thought_fields"] += 1
        if len(self.hidden_thought_examples) < 10:
            self.hidden_thought_examples.append(f"{where}:{hidden_path}")

    def _observe_agentic_turn(self, turn):
        if not isinstance(turn, dict):
            return
        has_basis = has_observable_decision_basis(turn)
        self.episodes["steps"] += 1
        self.episodes["decision_basis_steps"] += int(has_basis)
        self.episodes["missing_decision_basis_steps"] += int(not has_basis)
        self.episodes["legacy_thought_only_steps"] += int(
            "thought" in turn and "decision_basis" not in turn
        )

    def report(self):
        report = build_report(
            run_dir=self.run_dir,
            factories=self.factories,
            totals=self.totals,
            kinds=self.kinds,
            mill_mix=self.mill_mix,
            root_ids=self.root_ids,
            canonical_id_records=self.canonical_id_records,
            root_id_records=self.root_id_records,
            missing_ids=self.missing_ids,
            missing_root_ids=self.missing_root_ids,
            duplicate_ids=self.duplicate_ids,
            provenance=self.provenance,
            provenance_examples=self.provenance_examples,
            gate_by_role=self.gate_by_role,
            gate_errors=self.gate_errors,
            gate_error_examples=self.gate_error_examples,
            preference=self.preference,
            chosen_decisions=self.chosen_decisions,
            reward_keys=self.reward_keys,
            reward_shapes=self.reward_shapes,
            tags=self.tags,
            bridge=self.distillation.report(),
            episodes=self.episodes,
            hidden_thought_examples=self.hidden_thought_examples,
            exact_duplicates=self.exact_duplicates,
            record_errors=self.record_errors,
            unresolved_record_warnings=self.unresolved_record_warnings,
        )
        if self.code_repair:
            report["code_repair"] = {
                **{key: self.code_repair[key] for key in (
                    "records", "eligible_records", "evidence_only_records", "invalid_records",
                )},
                "ineligibility_reasons": dict(sorted(self.code_repair_reasons.items())),
                "validation_scope": "pure_inspection",
                "fresh_publication_gate_required": True,
            }
            report["blockers"].append("code_repair requires fresh replay and round completion gate")
            report["training_ready"] = False
        return report


def audit_run(
    run_dir: Path,
    *,
    snapshot: Mapping[str, bytes] | None = None,
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
    audit = _CorpusAudit(run_dir, mill_findings, mill_mix)
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


if __name__ == "__main__":
    raise SystemExit(main())
