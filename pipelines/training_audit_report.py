#!/usr/bin/env python3
"""Stable report and blocker assembly for the training-readiness audit."""

import json
import math
import statistics

from check_records import ALLOWED_PROVENANCE
from distillation_audit import BRIDGE_FACTORY_SLUG, THALAMIC_FACTORY_SLUG


def _corpus_blockers(state):
    blockers = []
    if state["record_errors"]:
        blockers.append(f"{len(state['record_errors'])} record shape/invariant errors")
    if not state["eligible_records"]:
        message = (
            "0 eligible training records remain after foreign-mill quarantine"
            if state["quarantined_records"]
            else "corpus contains 0 eligible training records"
        )
        blockers.append(message)
    if state["unresolved_warnings"]:
        blockers.append(f"{len(state['unresolved_warnings'])} unresolved record-invariant warnings")
    if state["duplicate_ids"]:
        blockers.append(f"{len(state['duplicate_ids'])} duplicate canonical IDs")
    if state["missing_root_ids"]:
        blockers.append(f"{len(state['missing_root_ids'])} records missing canonical top-level IDs")
    if state["provenance_bad"]:
        blockers.append(
            f"{state['provenance_bad']}/{state['provenance_total']} expected states "
            "lack canonical provenance"
        )
    return blockers


def _bridge_blockers(bridge):
    blockers = []
    messages = (
        ("missing_pairs", "lack event streams"),
        ("invalid_pairs", "contain invalid events"),
        ("unsorted_pairs", "have invalid event ordering"),
    )
    for key, message in messages:
        count = bridge.get(key, 0)
        if count:
            blockers.append(f"{count}/{bridge['pairs']} bridge pairs {message}")
    return blockers


def _distillation_blockers(bridge):
    blockers = []
    denominator = bridge.get("distillation_records", 0)
    if bridge.get("wrong_kind_records"):
        blockers.append(
            f"{bridge['wrong_kind_records']} wrong-kind distillation records "
            f"(non-Bridge records in {BRIDGE_FACTORY_SLUG} batches, "
            f"non-Thalamic records in {THALAMIC_FACTORY_SLUG} batches)"
        )

    messages = (
        (
            "raster_missing_pairs",
            "NELB/TTF records lack a 20-50 ms raster excerpt sidecar",
        ),
        (
            "raster_routing_table_missing_pairs",
            "NELB/TTF rasters lack a routing table",
        ),
    )
    for key, message in messages:
        count = bridge.get(key, 0)
        if count:
            blockers.append(f"{count}/{denominator} {message}")

    defects = bridge.get("raster_defect_pairs", 0)
    if defects:
        codes = ", ".join(sorted(bridge.get("raster_defect_codes", {})))
        blockers.append(
            f"{defects}/{denominator} NELB/TTF records have raster or "
            f"spike-budget defects ({codes})"
        )

    missing_batches = bridge.get("gate_snn_missing_batches", 0)
    batch_count = bridge.get("gate_snn_batches", 0)
    if missing_batches:
        blockers.append(
            f"{missing_batches}/{batch_count} distillation batches do not carry "
            "a spike-implemented gate (gate_snn neuron/threshold spec)"
        )

    invalid_gates = bridge.get("gate_snn_records", 0) - bridge.get("gate_snn_valid_records", 0)
    if invalid_gates > 0:
        blockers.append(
            f"{invalid_gates}/{bridge.get('gate_snn_records', 0)} "
            "spike-implemented gate specs are invalid"
        )
    return blockers


def _preference_blockers(preference):
    impure = preference["pairs"] - preference["same_context"]
    if not impure:
        return []
    if preference["episode_pairs"]:
        message = (
            f"{impure}/{preference['pairs']} preference pairs violate their "
            "state/proposal or shared-goal context invariant"
        )
    else:
        message = f"{impure}/{preference['pairs']} preference pairs change state or proposal"
    return [message]


def _episode_blockers(exact_duplicates, episodes):
    blockers = []
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
    return blockers


def build_blockers(**state):
    """Return blockers in the established operator-facing order."""

    blockers = _corpus_blockers(state)
    blockers.extend(_bridge_blockers(state["bridge"]))
    blockers.extend(_distillation_blockers(state["bridge"]))
    blockers.extend(_preference_blockers(state["preference"]))
    blockers.extend(_episode_blockers(state["exact_duplicates"], state["episodes"]))
    return blockers


def percentile(values, fraction):
    """Return the nearest-rank percentile used by stable audit reports."""
    if not values:
        return 0
    ordered = sorted(values)
    index = max(0, math.ceil(fraction * len(ordered)) - 1)
    return ordered[index]


def _factory_report(factories):
    output = {}
    for name, source_bucket in sorted(factories.items()):
        bucket = dict(source_bucket)
        lengths = bucket.pop("record_tokens")
        bucket["by_kind"] = dict(sorted(bucket["by_kind"].items()))
        bucket["length_tokens"] = {
            "median": round(statistics.median(lengths), 1) if lengths else 0,
            "p95": percentile(lengths, 0.95),
            "max": max(lengths, default=0),
        }
        output[name] = bucket
    return output


def _identity_report(state, eligible_records):
    return {
        "top_level_id_records": state["root_id_records"],
        "unique_top_level_ids": len(state["root_ids"]),
        "coverage_pct": (
            round(100 * state["root_id_records"] / eligible_records, 1) if eligible_records else 0
        ),
        "legacy_meta_fallback_records": (state["canonical_id_records"] - state["root_id_records"]),
        "missing_top_level": len(state["missing_root_ids"]),
        "missing_all_id_forms": len(state["missing_ids"]),
        "duplicates": state["duplicate_ids"],
        "missing_examples": state["missing_root_ids"][:10],
    }


def _provenance_report(provenance, examples):
    total = sum(provenance.values())
    canonical = sum(provenance.get(key, 0) for key in ALLOWED_PROVENANCE)
    return {
        "expected_states": total,
        "counts": dict(sorted(provenance.items())),
        "canonical_pct": round(100 * canonical / total, 1) if total else 0,
        "examples": dict(examples),
    }


def _gate_report(state):
    gates = {
        role: dict(sorted(counts.items())) for role, counts in sorted(state["gate_by_role"].items())
    }
    gate_errors = state["gate_errors"]
    errors = {
        "marked": gate_errors.get("marked", 0),
        "by_type": {key: count for key, count in sorted(gate_errors.items()) if key != "marked"},
        "examples": state["gate_error_examples"],
    }
    return gates, errors


def _preference_report(preference, chosen_decisions):
    pairs = preference["pairs"]
    return {
        **dict(preference),
        "context_purity_pct": (round(100 * preference["same_context"] / pairs, 1) if pairs else 0),
        "chosen_decisions": dict(sorted(chosen_decisions.items())),
    }


def _reward_report(reward_keys, reward_shapes):
    return {
        "unique_component_keys": len(reward_keys),
        "unique_shapes": len(reward_shapes),
        "top_component_keys": reward_keys.most_common(20),
        "top_shapes": reward_shapes.most_common(10),
    }


def _tag_report(tags):
    return {
        "uses": sum(tags.values()),
        "unique": len(tags),
        "reused_uses": sum(count for count in tags.values() if count > 1),
        "top": tags.most_common(20),
    }


def _report_blockers(state, eligible_records, provenance_total):
    provenance = state["provenance"]
    return build_blockers(
        record_errors=state["record_errors"],
        eligible_records=eligible_records,
        quarantined_records=state["totals"]["quarantined"],
        unresolved_warnings=state["unresolved_record_warnings"],
        duplicate_ids=state["duplicate_ids"],
        missing_root_ids=state["missing_root_ids"],
        provenance_bad=(provenance.get("missing", 0) + provenance.get("non_training", 0)),
        provenance_total=provenance_total,
        bridge=state["bridge"],
        preference=state["preference"],
        exact_duplicates=state["exact_duplicates"],
        episodes=state["episodes"],
    )


def build_report(**state):
    """Assemble the stable public report from eligible-record counters."""

    totals = state["totals"]
    eligible_records = totals["eligible_records"]
    provenance_report = _provenance_report(
        state["provenance"],
        state["provenance_examples"],
    )
    blockers = _report_blockers(
        state,
        eligible_records,
        provenance_report["expected_states"],
    )
    gates, gate_errors = _gate_report(state)
    return {
        "run_dir": str(state["run_dir"]),
        "totals": {
            "files": totals["files"],
            "records": totals["records"],
            "eligible_records": eligible_records,
            "bytes": totals["bytes"],
            "approx_tokens": totals["approx_tokens"],
            "by_kind": dict(sorted(state["kinds"].items())),
        },
        "factories": _factory_report(state["factories"]),
        "mill_mix": state["mill_mix"],
        "identity": _identity_report(state, eligible_records),
        "provenance": provenance_report,
        "gates": gates,
        "gate_errors": gate_errors,
        "preferences": _preference_report(
            state["preference"],
            state["chosen_decisions"],
        ),
        "rewards": _reward_report(state["reward_keys"], state["reward_shapes"]),
        "tags": _tag_report(state["tags"]),
        "bridge": state["bridge"],
        "episodes": dict(state["episodes"]),
        "hidden_thought_examples": state["hidden_thought_examples"],
        "exact_duplicates": state["exact_duplicates"],
        "record_invariants": {
            "errors": len(state["record_errors"]),
            "warnings": len(state["unresolved_record_warnings"]),
            "error_examples": state["record_errors"][:10],
            "warning_examples": state["unresolved_record_warnings"][:10],
        },
        "blockers": blockers,
        "training_ready": not blockers,
    }


def _corpus_observation_lines(report):
    """Return the stable corpus-observation section of the Markdown report."""

    bridge = report["bridge"]
    distillation_records = bridge.get("distillation_records", bridge.get("pairs", 0))
    return [
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
        f"- Bridge fidelity: {bridge.get('sorted_pairs', 0)}/"
        f"{bridge.get('pairs', 0)} pairs globally time-ordered; "
        f"{bridge.get('pairs_48_plus', 0)} have at least 48 events.",
        f"- Distillation rasters: {bridge.get('raster_valid_pairs', 0)}/"
        f"{distillation_records} NELB/TTF records carry a valid 20-50 ms "
        f"excerpt ({bridge.get('raster_coverage_pct', 0)}%), "
        f"{bridge.get('raster_spikes', 0)} budgeted spikes, "
        f"{bridge.get('third_factor_pairs', 0)} third-factor routes, "
        f"{bridge.get('gate_snn_valid_records', 0)} valid spike-implemented "
        f"gate specs across {bridge.get('gate_snn_covered_batches', 0)}/"
        f"{bridge.get('gate_snn_batches', 0)} distillation batches.",
        f"- Intentional gate-error records (marked): {report['gate_errors']['marked']} "
        f"`{json.dumps(report['gate_errors']['by_type'], sort_keys=True)}` — "
        "exclude from gate-rationale supervision lanes.",
    ]


def render_markdown(report):
    """Render the concise operator-facing Markdown report."""

    totals = report["totals"]
    lines = [
        "# Synthetic-factory training audit",
        "",
        f"- **Scale:** {totals['files']} JSONL files, {totals['records']} records, "
        f"{totals['bytes']:,} bytes, approximately {totals['approx_tokens']:,} tokens",
        f"- **Kinds:** {json.dumps(totals['by_kind'], sort_keys=True)}",
        f"- **Eligible after foreign-mill quarantine:** {totals['eligible_records']} "
        f"({report['mill_mix']['records']} quarantined, "
        f"`{json.dumps(report['mill_mix']['reason_codes'], sort_keys=True)}`)",
        f"- **Training-ready:** {'yes' if report['training_ready'] else 'no'}",
        "",
        "## Per factory",
        "",
        "| Factory | Files | Records | Eligible | Approx. tokens | Kinds |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for factory, data in report["factories"].items():
        lines.append(
            f"| {factory} | {data['files']} | {data['records']} | "
            f"{data['eligible_records']} | {data['approx_tokens']:,} | "
            f"`{json.dumps(data['by_kind'], sort_keys=True)}` |"
        )
    lines.extend(["", "## Training blockers", ""])
    if report["blockers"]:
        lines.extend(f"- {item}" for item in report["blockers"])
    else:
        lines.append("- None detected.")
    lines.extend(_corpus_observation_lines(report))
    return "\n".join(lines) + "\n"
