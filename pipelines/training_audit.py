#!/usr/bin/env python3
"""Read-only training-readiness audit for a synthetic-factory run tree.

Unlike ``validate_run.py`` (record shape) and ``check_records.py`` (per-record
invariants), this audit measures corpus-level risks: identity/provenance
coverage, preference-pair purity, reward-schema entropy, tag reuse, duplicate
content, length distribution, and bridge event fidelity.

Usage: python3 pipelines/training_audit.py [--strict] [--markdown] <run_dir>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
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
from curate_coding import (  # noqa: E402
    HIDDEN_REASONING_KEYS,
    HIDDEN_REASONING_PREFIX,
    normalized_key_name,
)
from validate_run import (  # noqa: E402
    HIDDEN_THOUGHT_KEYS,
    _episode_like,
    check_episode,
    event_time,
)

# A curated training view may expose neither the scratch-pad vocabulary the
# structural validator already knows about, the coding-factory key
# ``reasoning``, nor the ``internal_reasoning*`` family that Thalamic wrap
# records publish on ``proposed_action``.
CURATED_FORBIDDEN_REASONING_KEYS = HIDDEN_THOUGHT_KEYS | HIDDEN_REASONING_KEYS


def percentile(values, fraction):
    if not values:
        return 0
    ordered = sorted(values)
    index = max(0, math.ceil(fraction * len(ordered)) - 1)
    return ordered[index]


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
        path = (
            "executed_action"
            if view_path == "record"
            else f"{view_path}.executed_action"
        )
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


def event_stream_status(events):
    """Classify presence, event validity, and global temporal order."""
    if not isinstance(events, list) or not events:
        return "missing"
    times = []
    for event in events:
        got = event_time(event)
        if got is None:
            return "invalid"
        times.append(got[1])
    if all(current >= previous for previous, current in zip(times, times[1:])):
        return "sorted"
    return "unsorted"


def preference_context_purity(obj, chosen, rejected):
    """Return the applicable DPO context invariant for a preference pair.

    Thalamic pairs must hold state and proposal constant. Episode-sided pairs
    deliberately do not carry those objects, so their corresponding invariant
    is one shared task goal. An outer pair goal may supply the shared context,
    but every side goal that is present must agree with it.
    """
    episode_pair = _episode_like(chosen) or _episode_like(rejected)
    if not episode_pair:
        valid_context = bool(chosen and rejected) and all(
            isinstance(side.get(key), dict)
            for side in (chosen, rejected)
            for key in ("state", "proposed_action")
        )
        same_state = valid_context and (
            canonical_blob(chosen["state"]) == canonical_blob(rejected["state"])
        )
        same_proposal = valid_context and (
            canonical_blob(chosen["proposed_action"])
            == canonical_blob(rejected["proposed_action"])
        )
        return {
            "episode_pair": False,
            "pure": same_state and same_proposal,
            "same_state": same_state,
            "same_proposal": same_proposal,
            "same_goal": None,
        }

    raw_goals = (
        obj.get("goal"),
        chosen.get("goal") if isinstance(chosen, dict) else None,
        rejected.get("goal") if isinstance(rejected, dict) else None,
    )
    normalized_goals = []
    for value in raw_goals:
        if value is None:
            continue
        if not isinstance(value, str) or not value.strip():
            normalized_goals = []
            break
        normalized_goals.append(" ".join(value.split()))
    outer_goal = raw_goals[0]
    if isinstance(outer_goal, str) and outer_goal.strip():
        # The pair supplies shared context; any explicit side goal must agree.
        same_goal = bool(normalized_goals) and len(set(normalized_goals)) == 1
    else:
        # Without an outer goal, both episode sides must state the same goal.
        same_goal = (
            len(normalized_goals) == 2 and len(set(normalized_goals)) == 1
        )
    return {
        "episode_pair": True,
        "pure": same_goal,
        "same_state": None,
        "same_proposal": None,
        "same_goal": same_goal,
    }


def agentic_turns(obj, kind):
    """Yield each observable decision turn used by agentic curation."""
    if kind == "episode":
        steps = obj.get("steps")
        if isinstance(steps, list):
            yield from steps
    elif kind == "preference":
        for side_name in ("chosen", "rejected"):
            side = dict_field(obj, side_name)
            if _episode_like(side):
                steps = side.get("steps")
                if isinstance(steps, list):
                    yield from steps
    elif kind == "safety_case":
        steps = obj.get("steps")
        if isinstance(steps, list):
            yield from steps
    elif kind == "multi_agent":
        transcript = obj.get("transcript")
        for turn in transcript if isinstance(transcript, list) else ():
            if isinstance(turn, dict) and "tool_call" in turn:
                yield turn
    for _path, episode in wrapped_agentic_episodes(obj, kind):
        steps = episode.get("steps")
        if isinstance(steps, list):
            yield from steps


def has_observable_decision_basis(turn):
    return isinstance(turn, dict) and isinstance(turn.get("decision_basis"), str) and bool(
        turn["decision_basis"].strip()
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


def audit_run(run_dir: Path):
    run_dir = Path(run_dir).resolve()
    files = sorted(run_dir.rglob("*.jsonl"))
    factories = defaultdict(
        lambda: {
            "files": 0,
            "records": 0,
            "bytes": 0,
            "approx_tokens": 0,
            "by_kind": Counter(),
            "record_tokens": [],
        }
    )
    totals = Counter()
    kinds = Counter()
    record_errors = []
    unresolved_record_warnings = []
    ids = {}
    root_ids = {}
    canonical_id_records = 0
    root_id_records = 0
    missing_ids = []
    missing_root_ids = []
    duplicate_ids = []
    content_seen = {}
    exact_duplicates = []
    provenance = Counter()
    provenance_examples = defaultdict(list)
    gate_by_role = defaultdict(Counter)
    gate_errors = Counter()
    gate_error_examples = []
    # Keep the historic preference-report keys present even for a corpus made
    # entirely of episode-sided pairs, which have no Thalamic state/proposal.
    preference = Counter(
        pairs=0,
        same_context=0,
        same_state=0,
        same_proposal=0,
        same_goal=0,
        episode_pairs=0,
        thalamic_pairs=0,
    )
    chosen_decisions = Counter()
    reward_keys = Counter()
    reward_shapes = Counter()
    tags = Counter()
    bridge = Counter()
    episodes = Counter()
    hidden_thought_examples = []

    for path in files:
        rel = path.relative_to(run_dir)
        factory = rel.parts[0] if len(rel.parts) > 1 else "_root"
        payload_bytes = path.stat().st_size
        bucket = factories[factory]
        bucket["files"] += 1
        bucket["bytes"] += payload_bytes
        totals["files"] += 1
        totals["bytes"] += payload_bytes

        raw_text = path.read_bytes()
        try:
            text = raw_text.decode("utf-8")
        except UnicodeDecodeError as exc:
            record_errors.append(f"{rel}: invalid UTF-8: {exc}")
            text = raw_text.decode("utf-8", errors="replace")
        # Split JSONL only at literal LF.  ``splitlines`` incorrectly treats
        # U+2028/U+2029 embedded in JSON strings as record boundaries.
        for line_number, line in enumerate(text.split("\n"), 1):
            if not line.strip():
                continue
            where = f"{rel}:{line_number}"
            totals["records"] += 1
            bucket["records"] += 1
            token_estimate = max(1, math.ceil(len(line.encode("utf-8")) / 4))
            totals["approx_tokens"] += token_estimate
            bucket["approx_tokens"] += token_estimate
            bucket["record_tokens"].append(token_estimate)
            try:
                obj = json.loads(line, parse_constant=reject_json_constant)
            except (json.JSONDecodeError, ValueError) as exc:
                record_errors.append(f"{where}: JSON parse error: {exc}")
                kinds["unknown"] += 1
                bucket["by_kind"]["unknown"] += 1
                continue

            strict_agentic = isinstance(obj, dict) and (
                ("case_type" in obj)
                or ("transcript" in obj and "agents" in obj)
                or ("steps" in obj and "outcome" in obj and "reward" in obj)
                or (
                    "chosen" in obj
                    and "rejected" in obj
                    and (
                        _episode_like(obj.get("chosen"))
                        or _episode_like(obj.get("rejected"))
                    )
                )
            )
            errors, warnings, kind, checked_id = check_record(
                obj, where, factory_staging=strict_agentic
            )
            kinds[kind] += 1
            bucket["by_kind"][kind] += 1
            record_errors.extend(errors)
            # The outer record routes as Thalamic, preference, or bridge data,
            # so its ordinary shape check cannot validate an embedded coding
            # episode. Validate that nested episode explicitly with the same
            # strict agentic contract used for top-level staged episodes.
            for embedded_path, embedded in wrapped_agentic_episodes(obj, kind):
                embedded_where = f"{where}.{embedded_path}"
                if "steps" in embedded:
                    embedded_errors, _embedded_kind = shape_check(
                        embedded,
                        embedded_where,
                        factory_staging=True,
                    )
                else:
                    embedded_errors = check_episode(
                        embedded,
                        embedded_where,
                        forbid_hidden_thought=True,
                        enforce_terminal_outcome=True,
                    )
                record_errors.extend(embedded_errors)
            unresolved_record_warnings.extend(
                warning
                for warning in warnings
                if not any(
                    marker in warning
                    for marker in (
                        "missing canonical record id",
                        "missing top-level id",
                        "missing sim_or_real",
                        "non-training provenance",
                        "uses legacy 'thought'",
                    )
                )
            )

            record_id = checked_id or canonical_record_id(obj)
            if record_id is None:
                missing_ids.append(where)
            else:
                canonical_id_records += 1
                if record_id in ids:
                    duplicate_ids.append({"id": record_id, "first": ids[record_id], "again": where})
                else:
                    ids[record_id] = where
            root_id = root_record_id(obj)
            if root_id is None:
                missing_root_ids.append(where)
            else:
                root_id_records += 1
                if root_id not in root_ids:
                    root_ids[root_id] = where

            digest = hashlib.sha256(canonical_blob(obj).encode("utf-8")).hexdigest()
            if digest in content_seen:
                exact_duplicates.append({"first": content_seen[digest], "again": where})
            else:
                content_seen[digest] = where

            for state_path, state in expected_states(obj, kind):
                value = state.get("sim_or_real") if isinstance(state, dict) else None
                if value is None:
                    label = "missing"
                elif value in ALLOWED_PROVENANCE:
                    label = str(value)
                else:
                    label = "non_training"
                provenance[label] += 1
                if len(provenance_examples[label]) < 5:
                    provenance_examples[label].append(f"{where}:{state_path}={value!r}")

            for role, trajectory in thalamic_views(obj, kind):
                sd = dict_field(trajectory, "safety_decision")
                decision = sd.get("decision")
                if isinstance(decision, str):
                    gate_by_role[role][decision] += 1
                # Factory-01 mandates 1-in-5 intentionally-incorrect gates,
                # marked via safety_decision.correctness="incorrect" and/or
                # meta.supervisor_error_type. Count them so deliberately
                # flawed rationales are visible (and excludable) instead of
                # blending into gold supervision data.
                error_type = dict_field(trajectory, "meta").get("supervisor_error_type")
                if sd.get("correctness") == "incorrect" or error_type:
                    gate_errors["marked"] += 1
                    gate_errors[str(error_type) if error_type else "unspecified"] += 1
                    if len(gate_error_examples) < 5:
                        gate_error_examples.append(f"{where}:{role}")

            if kind == "preference":
                preference["pairs"] += 1
                chosen = dict_field(obj, "chosen")
                rejected = dict_field(obj, "rejected")
                purity = preference_context_purity(obj, chosen, rejected)
                preference["episode_pairs"] += int(purity["episode_pair"])
                preference["thalamic_pairs"] += int(not purity["episode_pair"])
                preference["same_context"] += int(purity["pure"])
                if purity["same_state"] is not None:
                    preference["same_state"] += int(purity["same_state"])
                    preference["same_proposal"] += int(purity["same_proposal"])
                if purity["same_goal"] is not None:
                    preference["same_goal"] += int(purity["same_goal"])
                decision = dict_field(chosen, "safety_decision").get("decision")
                if isinstance(decision, str):
                    chosen_decisions[decision] += 1

            for _path, reward in walk_key(obj, "reward_components"):
                if isinstance(reward, dict):
                    reward_keys.update(reward.keys())
                reward_shapes[reward_shape(reward)] += 1

            for _path, values in walk_key(obj, "tags"):
                if isinstance(values, list):
                    tags.update(value for value in values if isinstance(value, str))

            if kind == "bridge_pair":
                bridge["pairs"] += 1
                events = obj.get("spike_events")
                if isinstance(events, list):
                    bridge["events"] += len(events)
                    bridge["pairs_48_plus"] += int(len(events) >= 48)
                status = event_stream_status(events)
                bridge[f"{status}_pairs"] += 1
            if kind == "episode":
                episodes["episodes"] += 1
            # Every kind is scanned, not only the agentic ones: Thalamic wrap
            # records publish `proposed_action.internal_reasoning` and embed a
            # coding episode with per-step `thought` under `executed_action`.
            for hidden_path in hidden_thought_paths(obj):
                episodes["hidden_thought_fields"] += 1
                if len(hidden_thought_examples) < 10:
                    hidden_thought_examples.append(f"{where}:{hidden_path}")
            for turn in agentic_turns(obj, kind):
                if not isinstance(turn, dict):
                    continue
                episodes["steps"] += 1
                episodes["decision_basis_steps"] += int(
                    has_observable_decision_basis(turn)
                )
                episodes["missing_decision_basis_steps"] += int(
                    not has_observable_decision_basis(turn)
                )
                episodes["legacy_thought_only_steps"] += int(
                    "thought" in turn and "decision_basis" not in turn
                )

    factory_output = {}
    for name, bucket in sorted(factories.items()):
        lengths = bucket.pop("record_tokens")
        bucket["by_kind"] = dict(sorted(bucket["by_kind"].items()))
        bucket["length_tokens"] = {
            "median": round(statistics.median(lengths), 1) if lengths else 0,
            "p95": percentile(lengths, 0.95),
            "max": max(lengths, default=0),
        }
        factory_output[name] = bucket

    total_records = totals["records"]
    provenance_total = sum(provenance.values())
    tag_uses = sum(tags.values())
    blockers = []
    if record_errors:
        blockers.append(f"{len(record_errors)} record shape/invariant errors")
    if unresolved_record_warnings:
        blockers.append(
            f"{len(unresolved_record_warnings)} unresolved record-invariant warnings"
        )
    if duplicate_ids:
        blockers.append(f"{len(duplicate_ids)} duplicate canonical IDs")
    if missing_root_ids:
        blockers.append(
            f"{len(missing_root_ids)} records missing canonical top-level IDs"
        )
    provenance_bad = provenance.get("missing", 0) + provenance.get("non_training", 0)
    if provenance_bad:
        blockers.append(f"{provenance_bad}/{provenance_total} expected states lack canonical provenance")
    missing_streams = bridge.get("missing_pairs", 0)
    invalid_streams = bridge.get("invalid_pairs", 0)
    unsorted_pairs = bridge.get("unsorted_pairs", 0)
    if missing_streams:
        blockers.append(f"{missing_streams}/{bridge['pairs']} bridge pairs lack event streams")
    if invalid_streams:
        blockers.append(
            f"{invalid_streams}/{bridge['pairs']} bridge pairs contain invalid events"
        )
    if unsorted_pairs:
        blockers.append(f"{unsorted_pairs}/{bridge['pairs']} bridge pairs have invalid event ordering")
    impure_pairs = preference["pairs"] - preference["same_context"]
    if impure_pairs:
        if preference["episode_pairs"]:
            blockers.append(
                f"{impure_pairs}/{preference['pairs']} preference pairs violate their "
                "state/proposal or shared-goal context invariant"
            )
        else:
            # Retain the established all-Thalamic diagnostic as a stable
            # operator-facing contract for existing corpus reports.
            blockers.append(
                f"{impure_pairs}/{preference['pairs']} preference pairs change state or proposal"
            )
    if exact_duplicates:
        blockers.append(f"{len(exact_duplicates)} exact duplicate records")
    if episodes["hidden_thought_fields"]:
        blockers.append(
            f"{episodes['hidden_thought_fields']} hidden-thought fields "
            "(thought / internal_reasoning*) appear in records"
        )
    if episodes["missing_decision_basis_steps"]:
        blockers.append(
            f"{episodes['missing_decision_basis_steps']} agentic turns lack a "
            "non-empty textual decision_basis"
        )

    report = {
        "run_dir": str(run_dir),
        "totals": {
            "files": totals["files"],
            "records": total_records,
            "bytes": totals["bytes"],
            "approx_tokens": totals["approx_tokens"],
            "by_kind": dict(sorted(kinds.items())),
        },
        "factories": factory_output,
        "identity": {
            "top_level_id_records": root_id_records,
            "unique_top_level_ids": len(root_ids),
            "coverage_pct": round(100 * root_id_records / total_records, 1) if total_records else 0,
            "legacy_meta_fallback_records": canonical_id_records - root_id_records,
            "missing_top_level": len(missing_root_ids),
            "missing_all_id_forms": len(missing_ids),
            "duplicates": duplicate_ids,
            "missing_examples": missing_root_ids[:10],
        },
        "provenance": {
            "expected_states": provenance_total,
            "counts": dict(sorted(provenance.items())),
            "canonical_pct": round(
                100
                * sum(provenance.get(key, 0) for key in ALLOWED_PROVENANCE)
                / provenance_total,
                1,
            ) if provenance_total else 0,
            "examples": dict(provenance_examples),
        },
        "gates": {role: dict(sorted(counts.items())) for role, counts in sorted(gate_by_role.items())},
        "gate_errors": {
            "marked": gate_errors.get("marked", 0),
            "by_type": {
                key: count
                for key, count in sorted(gate_errors.items())
                if key != "marked"
            },
            "examples": gate_error_examples,
        },
        "preferences": {
            **dict(preference),
            "context_purity_pct": round(
                100 * preference["same_context"] / preference["pairs"], 1
            ) if preference["pairs"] else 0,
            "chosen_decisions": dict(sorted(chosen_decisions.items())),
        },
        "rewards": {
            "unique_component_keys": len(reward_keys),
            "unique_shapes": len(reward_shapes),
            "top_component_keys": reward_keys.most_common(20),
            "top_shapes": reward_shapes.most_common(10),
        },
        "tags": {
            "uses": tag_uses,
            "unique": len(tags),
            "reused_uses": sum(count for count in tags.values() if count > 1),
            "top": tags.most_common(20),
        },
        "bridge": dict(bridge),
        "episodes": dict(episodes),
        "hidden_thought_examples": hidden_thought_examples,
        "exact_duplicates": exact_duplicates,
        "record_invariants": {
            "errors": len(record_errors),
            "warnings": len(unresolved_record_warnings),
            "error_examples": record_errors[:10],
            "warning_examples": unresolved_record_warnings[:10],
        },
        "blockers": blockers,
        "training_ready": not blockers,
    }
    return report


def render_markdown(report):
    totals = report["totals"]
    lines = [
        "# Synthetic-factory training audit",
        "",
        f"- **Scale:** {totals['files']} JSONL files, {totals['records']} records, "
        f"{totals['bytes']:,} bytes, approximately {totals['approx_tokens']:,} tokens",
        f"- **Kinds:** {json.dumps(totals['by_kind'], sort_keys=True)}",
        f"- **Training-ready:** {'yes' if report['training_ready'] else 'no'}",
        "",
        "## Per factory",
        "",
        "| Factory | Files | Records | Approx. tokens | Kinds |",
        "|---|---:|---:|---:|---|",
    ]
    for factory, data in report["factories"].items():
        lines.append(
            f"| {factory} | {data['files']} | {data['records']} | "
            f"{data['approx_tokens']:,} | `{json.dumps(data['by_kind'], sort_keys=True)}` |"
        )
    lines.extend(["", "## Training blockers", ""])
    if report["blockers"]:
        lines.extend(f"- {item}" for item in report["blockers"])
    else:
        lines.append("- None detected.")
    lines.extend(
        [
            "",
            "## Corpus observations",
            "",
            f"- Canonical ID coverage: {report['identity']['coverage_pct']}%.",
            f"- Canonical provenance coverage: {report['provenance']['canonical_pct']}%.",
            f"- Preference context purity: {report['preferences']['context_purity_pct']}%; "
            f"chosen decisions `{json.dumps(report['preferences']['chosen_decisions'], sort_keys=True)}`.",
            f"- Reward vocabulary: {report['rewards']['unique_component_keys']} component keys "
            f"across {report['rewards']['unique_shapes']} structural shapes.",
            f"- Tags: {report['tags']['uses']} uses / {report['tags']['unique']} unique.",
            f"- Bridge fidelity: {report['bridge'].get('sorted_pairs', 0)}/"
            f"{report['bridge'].get('pairs', 0)} pairs globally time-ordered; "
            f"{report['bridge'].get('pairs_48_plus', 0)} have at least 48 events.",
            f"- Intentional gate-error records (marked): {report['gate_errors']['marked']} "
            f"`{json.dumps(report['gate_errors']['by_type'], sort_keys=True)}` — "
            "exclude from gate-rationale supervision lanes.",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="exit 1 when blockers exist")
    parser.add_argument("--markdown", action="store_true", help="render concise Markdown")
    parser.add_argument("run_dir")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    report = audit_run(Path(args.run_dir))
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if args.strict and report["blockers"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
