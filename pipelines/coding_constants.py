"""Shared coding-observability constants.

Kept in a dedicated module so the verify siblings never import the CLI
script under a second module name.
"""

from __future__ import annotations

if __package__:
    from .validate_run import HIDDEN_THOUGHT_KEYS
else:
    from validate_run import HIDDEN_THOUGHT_KEYS


TRANSFORM_NAME = "coding_observability"
# Version 3 keeps the version-2 wrap support and additionally aligns the
# transform with the structural audit's complete hidden-thought vocabulary.
TRANSFORM_VERSION = "3"
MAX_DECISION_BASIS_CHARS = 240
RUN_MANIFEST_FILENAME = "manifest.jsonl"

# Exact key names that never reach a curated record, plus the
# ``internal_reasoning`` prefix that covers ``internal_reasoning_verbatim``,
# ``internal_reasoning_optimizer``, and every other published variant.
# ``reasoning`` is the coding-factory contract key
# (prompts/04-agentic-coding-trajectory-factory.md) and is an exact match
# only, so nearby names such as ``reasoning_flaw`` stay visible.
HIDDEN_REASONING_KEYS = HIDDEN_THOUGHT_KEYS | frozenset(
    {"internal_reasoning", "internal_reasoning_verbatim", "reasoning"}
)
HIDDEN_REASONING_PREFIX = "internal_reasoning"

WRAP_STEPS_PARENT = "executed_action"

REASON_HIDDEN_REASONING_REMOVED = "coding_hidden_reasoning_removed"
REASON_BASIS_CONCISED = "coding_basis_concised"
REASON_BASIS_FROM_PLAN = "coding_basis_from_plan"
REASON_BASIS_FROM_REFLECTION = "coding_basis_from_reflection"
REASON_BASIS_FROM_OBSERVATION = "coding_basis_from_observation"
REASON_BASIS_FROM_TOOL_CALL = "coding_basis_from_tool_call"
REASON_STEP_NOT_OBJECT = "coding_step_not_object"
REASON_NO_VISIBLE_EVIDENCE = "coding_no_visible_decision_evidence"
REASON_NO_RETAINABLE_STEPS = "coding_no_retainable_steps"
REASON_STEPS_MIGRATED = "coding_steps_migrated"
REASON_STEPS_EXCLUDED = "coding_steps_excluded"
REASON_WRAP_RECORD = "coding_wrap_record"
REASON_RECORD_NOT_OBJECT = "coding_record_not_object"
REASON_STEPS_NOT_ARRAY = "coding_steps_not_array"
REASON_INVALID_JSON = "coding_invalid_json"
REASON_INVALID_UTF8 = "coding_invalid_utf8"

_EVIDENCE_REASON = {
    "plan": REASON_BASIS_FROM_PLAN,
    "reflection": REASON_BASIS_FROM_REFLECTION,
    "observation": REASON_BASIS_FROM_OBSERVATION,
    "tool_call": REASON_BASIS_FROM_TOOL_CALL,
}

REASON_THOUGHT_REMOVED = "coding_thought_removed"

VISIBLE_BASIS_LABELS = ("Plan: ", "Reflection: ", "Observation: ", "Tool call: ")
EXCLUSION_REASONS = frozenset(
    {
        REASON_STEP_NOT_OBJECT,
        REASON_NO_VISIBLE_EVIDENCE,
        REASON_NO_RETAINABLE_STEPS,
        REASON_RECORD_NOT_OBJECT,
        REASON_STEPS_NOT_ARRAY,
        REASON_INVALID_JSON,
        REASON_INVALID_UTF8,
    }
)
STEP_EXCLUSION_REASONS = frozenset(
    {REASON_STEP_NOT_OBJECT, REASON_NO_VISIBLE_EVIDENCE}
)
PRE_STEP_EXCLUSION_REASONS = frozenset(
    {
        REASON_RECORD_NOT_OBJECT,
        REASON_STEPS_NOT_ARRAY,
        REASON_INVALID_JSON,
        REASON_INVALID_UTF8,
    }
)
STEP_EVIDENCE_REASONS = frozenset(_EVIDENCE_REASON.values())
STEP_RETAINED_REASONS = frozenset(
    {
        *STEP_EVIDENCE_REASONS,
        REASON_THOUGHT_REMOVED,
        REASON_HIDDEN_REASONING_REMOVED,
        REASON_BASIS_CONCISED,
    }
)
STEP_ALLOWED_REASONS = frozenset({*STEP_EXCLUSION_REASONS, *STEP_RETAINED_REASONS})
RECORD_TRANSFORMATION_REASONS = frozenset(
    {
        REASON_THOUGHT_REMOVED,
        REASON_HIDDEN_REASONING_REMOVED,
        REASON_STEPS_MIGRATED,
        REASON_STEPS_EXCLUDED,
    }
)
RECORD_STRUCTURAL_REASONS = frozenset({REASON_WRAP_RECORD})
