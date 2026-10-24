#!/usr/bin/env python3
"""Names of the task gate: formats, verdicts, detail codes, limits and the coded refusal.

No logic beyond the refusal type. A verdict says which rule rejected a proposal first, in the
gate's evaluation order; a detail says why, in a short machine-readable code.
"""

from __future__ import annotations

from ._contract import bind_import_twin

GATE_FORMAT = "task-gate/1"
TASKS_FORMAT = "task-gate-tasks/1"
SUMMARY_FORMAT = "task-gate-summary/1"
INDEX_FORMAT = "task-gate-dedup-index/2"
KEY_FORMAT = "task-gate-key/3"
HARNESS_PROTOCOL = "task-gate-harness/1"

# Sources a proposal may record. Anything else is the proposer's own label.
SOURCE_UNSPECIFIED = "unspecified"
SOURCE_MODEL = "model"
SOURCE_PROCEDURAL = "procedural"
ACCEPTED_SOURCES = frozenset({SOURCE_UNSPECIFIED, SOURCE_MODEL, SOURCE_PROCEDURAL})

TASKS_FILENAME = "tasks.jsonl"
SUMMARY_FILENAME = "summary.json"
INDEX_FILENAME = "dedup-index.jsonl"

VERDICT_KEPT = "kept"
VERDICT_PARSE_ERROR = "parse_error"
VERDICT_ORIGINAL_FAILS = "original_fails"
VERDICT_MUTANT_PASSES = "mutant_passes"
VERDICT_TIMEOUT = "timeout"
VERDICT_DUPLICATE = "duplicate"
VERDICT_DENYLISTED = "denylisted"
VERDICTS = (
    VERDICT_KEPT, VERDICT_PARSE_ERROR, VERDICT_ORIGINAL_FAILS, VERDICT_MUTANT_PASSES,
    VERDICT_TIMEOUT, VERDICT_DUPLICATE, VERDICT_DENYLISTED,
)

# Harness outcomes (what one child run observed).
OUTCOME_PASSED = "passed"
OUTCOME_FAILED = "failed"
OUTCOME_LOAD_ERROR = "load_error"
OUTCOME_TIMEOUT = "timeout"
OUTCOME_CRASHED = "crashed"
OUTCOMES = (OUTCOME_PASSED, OUTCOME_FAILED, OUTCOME_LOAD_ERROR, OUTCOME_TIMEOUT, OUTCOME_CRASHED)

# Details attached to a verdict.
DETAIL_MALFORMED_ROW = "malformed_row"
DETAIL_UNKNOWN_PROGRAM = "unknown_program"
DETAIL_SPAN_OUT_OF_RANGE = "span_out_of_range"
DETAIL_SPAN_NOT_ON_BOUNDARY = "span_not_on_char_boundary"
DETAIL_SPAN_TEXT_MISMATCH = "span_text_mismatch"
DETAIL_SPAN_NOT_FOUND = "span_not_found"
DETAIL_SPAN_AMBIGUOUS = "span_ambiguous"
DETAIL_SPAN_OUTSIDE_BODY = "span_outside_target_body"
DETAIL_SPAN_TOUCHES_DOCSTRING = "span_touches_docstring"
DETAIL_MUTANT_SYNTAX_ERROR = "mutant_syntax_error"
DETAIL_MUTANT_ESCAPES_BODY = "mutant_escapes_target_body"
DETAIL_MUTANT_LOAD_ERROR = "mutant_load_error"
DETAIL_MUTANT_CRASHED = "mutant_crashed"
DETAIL_NO_DOCTESTS = "no_doctests"
DETAIL_ORIGINAL_FAILED = "original_failed_doctests"
DETAIL_ORIGINAL_LOAD_ERROR = "original_load_error"
DETAIL_ORIGINAL_TIMEOUT = "original_timeout"
DETAIL_ORIGINAL_CRASHED = "original_crashed"
DETAIL_MUTANT_FAILED_DOCTESTS = "mutant_failed_doctests"
DETAIL_MUTANT_PASSED_ALL = "mutant_passed_all_doctests"
DETAIL_MUTANT_TIMEOUT = "mutant_timeout"
DETAIL_MUTANT_EQUIVALENT = "mutant_equivalent_stdout"
DETAIL_PRIOR_RUN = "kept_in_prior_run"
DETAIL_THIS_RUN = "kept_earlier_in_this_run"
DETAIL_ON_DENYLIST = "program_id_on_eval_denylist"
DETAIL_CONTENT_ON_DENYLIST = "program_text_on_eval_denylist"
# Harness detail: every doctest miss is extra stdout around the expected value.
DETAIL_STDOUT_EQUIVALENT = "stdout_equivalent"

DEFAULT_TIMEOUT_S = 10.0
MAX_TIMEOUT_S = 600.0
MAX_PROGRAM_BYTES = 1 << 20
MAX_DENYLIST_BYTES = 16 << 20
MAX_INDEX_BYTES = 256 << 20
MAX_PROPOSALS_BYTES = 256 << 20

# Refusal codes: the run stops and writes nothing.
REFUSE_DENYLIST_MISSING = "TASK_GATE_DENYLIST_MISSING"
REFUSE_DENYLIST_MALFORMED = "TASK_GATE_DENYLIST_MALFORMED"
REFUSE_INDEX_UNREADABLE = "TASK_GATE_INDEX_UNREADABLE"
REFUSE_INDEX_MALFORMED = "TASK_GATE_INDEX_MALFORMED"
REFUSE_PROGRAM_INVALID = "TASK_GATE_PROGRAM_INVALID"
REFUSE_PROPOSALS_INVALID = "TASK_GATE_PROPOSALS_INVALID"
REFUSE_DESTINATION_EXISTS = "TASK_GATE_DESTINATION_EXISTS"
REFUSE_DESTINATION_UNDER_RAW = "TASK_GATE_DESTINATION_UNDER_RAW"
REFUSE_TIMEOUT_DOMAIN = "TASK_GATE_TIMEOUT_OUT_OF_DOMAIN"
REFUSE_HARNESS_UNAVAILABLE = "TASK_GATE_HARNESS_UNAVAILABLE"
REFUSE_NO_PROPOSALS = "TASK_GATE_NO_PROPOSALS"
REFUSE_INPUT_INVALID = "TASK_GATE_INPUT_INVALID"


class GateRefusal(Exception):
    """A coded refusal: the run does not start (or stops) and writes nothing."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def refuse_when(condition: bool, code: str, detail: str) -> None:
    if condition:
        raise GateRefusal(code, detail)


bind_import_twin(__name__)
