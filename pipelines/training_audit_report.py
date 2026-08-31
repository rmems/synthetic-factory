#!/usr/bin/env python3
"""Stable blocker-message assembly for the training-readiness audit."""


def _corpus_blockers(state):
    blockers = []
    if state["record_errors"]:
        blockers.append(
            f"{len(state['record_errors'])} record shape/invariant errors"
        )
    if not state["eligible_records"]:
        message = (
            "0 eligible training records remain after foreign-mill quarantine"
            if state["quarantined_records"]
            else "corpus contains 0 eligible training records"
        )
        blockers.append(message)
    if state["unresolved_warnings"]:
        blockers.append(
            f"{len(state['unresolved_warnings'])} unresolved record-invariant warnings"
        )
    if state["duplicate_ids"]:
        blockers.append(
            f"{len(state['duplicate_ids'])} duplicate canonical IDs"
        )
    if state["missing_root_ids"]:
        blockers.append(
            f"{len(state['missing_root_ids'])} records missing canonical top-level IDs"
        )
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
        message = (
            f"{impure}/{preference['pairs']} preference pairs change state or proposal"
        )
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
    blockers.extend(_preference_blockers(state["preference"]))
    blockers.extend(
        _episode_blockers(state["exact_duplicates"], state["episodes"])
    )
    return blockers
