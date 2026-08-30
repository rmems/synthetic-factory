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

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from check_records import (  # noqa: E402
    ALLOWED_PROVENANCE,
    canonical_record_id,
    check_record,
    expected_states,
    reject_json_constant,
    root_record_id,
    shape_check,
    walk_key,
)
from census import (  # noqa: E402
    factory_for_path,
    visible_jsonl_paths,
)
from round_txn import TransactionError  # noqa: E402
from curate_coding import (  # noqa: E402
    HIDDEN_REASONING_KEYS,
    HIDDEN_REASONING_PREFIX,
    normalized_key_name,
)
from validate_run import (  # noqa: E402
    HIDDEN_THOUGHT_KEYS,
    _episode_like,
    check_episode,
)
from training_audit_bridge import event_stream_status as _event_stream_status  # noqa: E402
from distillation_audit import (  # noqa: E402
    BRIDGE_FACTORY_SLUG as BRIDGE_FACTORY_SLUG,
    THALAMIC_FACTORY_SLUG as THALAMIC_FACTORY_SLUG,
    DistillationAudit,
)
from training_audit_mill import index_mill_quarantine  # noqa: E402
from training_audit_report import (  # noqa: E402
    build_report,
    percentile as _percentile,
    render_markdown as _render_markdown,
)

# A curated training view may expose neither the scratch-pad vocabulary the
# structural validator already knows about, the coding-factory key
# ``reasoning``, nor the ``internal_reasoning*`` family that Thalamic wrap
# records publish on ``proposed_action``.
CURATED_FORBIDDEN_REASONING_KEYS = HIDDEN_THOUGHT_KEYS | HIDDEN_REASONING_KEYS


def event_stream_status(events, enclosing=None):
    """Compatibility facade for the extracted bridge audit classifier."""
    return _event_stream_status(events, enclosing)


def percentile(values, fraction):
    """Compatibility facade for the extracted report percentile helper."""
    return _percentile(values, fraction)


def canonical_blob(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def dict_field(value, key):
    """Return a nested mapping, treating malformed values as absent."""
    if not isinstance(value, dict):
        return {}
    nested = value.get(key)
    return nested if isinstance(nested, dict) else {}


def thalamic_views(obj, kind):
    if kind == "thalamic":
        yield "record", obj
    elif kind == "preference":
        for side in ("chosen", "rejected"):
            value = obj.get(side)
            if isinstance(value, dict):
                yield side, value
    elif kind == "bridge_pair":
        view = obj.get("language_view")
        if isinstance(view, dict) and isinstance(view.get("trajectory"), dict):
            yield "language_view.trajectory", view["trajectory"]


def wrapped_agentic_episodes(obj, kind):
    """Yield coding episodes embedded in any supported Thalamic view."""
    for view_path, trajectory in thalamic_views(obj, kind):
        executed_action = trajectory.get("executed_action")
        if not isinstance(executed_action, dict):
            continue
        if "steps" not in executed_action and not all(
            key in executed_action for key in ("goal", "outcome", "reward")
        ):
            continue
        path = "executed_action" if view_path == "record" else f"{view_path}.executed_action"
        yield path, executed_action


def reward_shape(value):
    if not isinstance(value, dict):
        return type(value).__name__
    shape = []
    for key, item in sorted(value.items()):
        if isinstance(item, dict):
            subtype = "value-object" if isinstance(item.get("value"), (int, float)) else "object"
        elif isinstance(item, list):
            subtype = "array"
        else:
            subtype = type(item).__name__
        shape.append(f"{key}:{subtype}")
    return "|".join(shape)


def _thalamic_context_purity(chosen, rejected):
    valid_context = bool(chosen and rejected) and all(
        isinstance(side.get(key), dict)
        for side in (chosen, rejected)
        for key in ("state", "proposed_action")
    )
    same_state = valid_context and (
        canonical_blob(chosen["state"]) == canonical_blob(rejected["state"])
    )
    same_proposal = valid_context and (
        canonical_blob(chosen["proposed_action"]) == canonical_blob(rejected["proposed_action"])
    )
    return {
        "episode_pair": False,
        "pure": same_state and same_proposal,
        "same_state": same_state,
        "same_proposal": same_proposal,
        "same_goal": None,
    }


def _normalized_goals(raw_goals):
    normalized = []
    for value in raw_goals:
        if value is None:
            continue
        if not isinstance(value, str) or not value.strip():
            return []
        normalized.append(" ".join(value.split()))
    return normalized


def _episode_context_purity(obj, chosen, rejected):
    raw_goals = (
        obj.get("goal"),
        chosen.get("goal") if isinstance(chosen, dict) else None,
        rejected.get("goal") if isinstance(rejected, dict) else None,
    )
    normalized_goals = _normalized_goals(raw_goals)
    outer_goal = raw_goals[0]
    if isinstance(outer_goal, str) and outer_goal.strip():
        same_goal = bool(normalized_goals) and len(set(normalized_goals)) == 1
    else:
        same_goal = len(normalized_goals) == 2 and len(set(normalized_goals)) == 1
    return {
        "episode_pair": True,
        "pure": same_goal,
        "same_state": None,
        "same_proposal": None,
        "same_goal": same_goal,
    }


def preference_context_purity(obj, chosen, rejected):
    """Return the applicable DPO context invariant for a preference pair.

    Thalamic pairs hold state and proposal constant. Episode-sided pairs use
    one shared task goal, including an optional outer pair goal.
    """
    if _episode_like(chosen) or _episode_like(rejected):
        return _episode_context_purity(obj, chosen, rejected)
    return _thalamic_context_purity(chosen, rejected)


def _list_field(value, key):
    items = value.get(key) if isinstance(value, dict) else None
    return items if isinstance(items, list) else ()


def _preference_turns(obj):
    for side_name in ("chosen", "rejected"):
        side = dict_field(obj, side_name)
        if _episode_like(side):
            yield from _list_field(side, "steps")


def _coordination_turns(obj):
    for turn in _list_field(obj, "transcript"):
        if isinstance(turn, dict) and "tool_call" in turn:
            yield turn


def agentic_turns(obj, kind):
    """Yield each observable decision turn used by agentic curation."""
    if kind in {"episode", "safety_case"}:
        yield from _list_field(obj, "steps")
    elif kind == "preference":
        yield from _preference_turns(obj)
    elif kind == "multi_agent":
        yield from _coordination_turns(obj)
    for _path, episode in wrapped_agentic_episodes(obj, kind):
        yield from _list_field(episode, "steps")


def has_observable_decision_basis(turn):
    return (
        isinstance(turn, dict)
        and isinstance(turn.get("decision_basis"), str)
        and bool(turn["decision_basis"].strip())
    )


def is_hidden_thought_key(key):
    """Return whether a JSON key names model-private reasoning text.

    Covers the shared scratch-pad vocabulary from ``validate_run``, the
    exact coding-factory key ``reasoning``, and the whole
    ``internal_reasoning*`` family that Thalamic wrap records carry on
    ``proposed_action``. Raw evidence may keep these keys; a curated training
    view may not.
    """
    normalized = normalized_key_name(key)
    return normalized in CURATED_FORBIDDEN_REASONING_KEYS or normalized.startswith(
        HIDDEN_REASONING_PREFIX
    )


def hidden_thought_paths(value, path=""):
    """Yield every recursively hidden-reasoning field in one record."""
    if isinstance(value, dict):
        for key, item in value.items():
            child_path = f"{path}.{key}" if path else key
            if is_hidden_thought_key(key):
                yield child_path
            yield from hidden_thought_paths(item, child_path)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from hidden_thought_paths(item, f"{path}[{index}]")


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
                "by_kind": Counter(),
                "record_tokens": [],
            }
        )
        self.totals = Counter()
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
        self.episodes = Counter()
        self.hidden_thought_examples = []

    def observe_file(self, path):
        rel = path.relative_to(self.run_dir)
        factory = factory_for_path(self.run_dir, path)
        bucket = self.factories[factory]
        payload = path.read_bytes()
        bucket["files"] += 1
        bucket["bytes"] += len(payload)
        self.totals["files"] += 1
        self.totals["bytes"] += len(payload)

        # JSONL record boundaries are literal LF bytes. CRLF leaves JSON
        # whitespace at the end of a record, while a bare CR stays within one
        # physical record and is rejected as extra JSON data. Literal UTF-8
        # U+2028/U+2029 bytes remain ordinary JSON string content.
        for line_number, raw_line in enumerate(payload.split(b"\n"), 1):
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
            obj = json.loads(line, parse_constant=reject_json_constant)
        except (json.JSONDecodeError, ValueError) as exc:
            self._record_parse_error(where, exc, token_estimate, bucket)
            return

        finding = self.mill_findings_by_ref.get((rel.as_posix(), line_number))
        if finding is not None:
            # Raw evidence from another mill is not eligible training data.
            self.totals["quarantined"] += 1
            return

        self._account_tokens(token_estimate, bucket)
        self.totals["eligible_records"] += 1
        bucket["eligible_records"] += 1
        kind = self._observe_record(obj, where, factory, rel)
        self.kinds[kind] += 1
        bucket["by_kind"][kind] += 1

    def _record_parse_error(self, where, exc, token_estimate, bucket):
        self._account_tokens(token_estimate, bucket)
        self.record_errors.append(f"{where}: JSON parse error: {exc}")
        self.kinds["unknown"] += 1
        bucket["by_kind"]["unknown"] += 1

    def _account_tokens(self, token_estimate, bucket):
        self.totals["approx_tokens"] += token_estimate
        bucket["approx_tokens"] += token_estimate
        bucket["record_tokens"].append(token_estimate)

    def _observe_record(self, obj, where, factory, rel):
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
            _episode_like(obj.get(side)) for side in ("chosen", "rejected")
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
        return build_report(
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


def audit_run(run_dir: Path):
    run_dir = Path(run_dir).resolve()
    files = visible_jsonl_paths(run_dir)
    mill_findings, mill_mix = index_mill_quarantine(run_dir, files)
    audit = _CorpusAudit(run_dir, mill_findings, mill_mix)
    for path in files:
        audit.observe_file(path)
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
    except TransactionError as exc:
        print(f"training_audit failed: {exc}", file=sys.stderr)
        return 1
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if args.strict and report["blockers"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
