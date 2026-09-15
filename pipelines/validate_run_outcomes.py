#!/usr/bin/env python3
"""Observable outcome-signal checks for the run validator."""

import re
import sys

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling
    _assert_direct_sibling("validate_run_outcomes")
else:
    # Join a qualified twin without importing pipelines during normal CLI use.
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "validate_run_outcomes"
    )


# Static outcome-signal vocabulary: completion and failure terms plus the
# negation, modifier, and suffix fragments that qualify them.
_COMPLETION_TERM = (
    r"(?:atomic|complet(?:e(?:d|s)?|ing)|correct|deploy\w*|fixed|green|healthy|"
    r"landed|merged|operational|pass(?:ed|es|ing)?|recovered|repaired|"
    r"resolved|safe(?:ly)?|shipped|succeed(?:ed|s|ing)?|"
    r"success(?:es|ful(?:ly)?)?|"
    r"verified|work(?:ed|ing|s)?)"
)
_FAILURE_TERM = (
    r"(?:blocked|broken|corrupt\w*|fail\w*|incomplete|partial\w*|pending|"
    r"unsafe|unsuccessful(?:ly)?|unresolved)"
)
_COMPLETION_MODIFIER_WORD = (
    r"(?!(?:although|and|but|except|however|nor|or|plus|then|though|while)\b)"
    r"\w+"
)
_COMPLETION_MODIFIER = rf"(?:{_COMPLETION_MODIFIER_WORD}[ -]+){{0,4}}"
_COMPLETION_SUFFIX = r"(?:\s+(?:fully|successfully|ultimately)){0,3}"
_PROGRESSIVE_COMPLETION_TERM = r"(?:completing|deploying|passing|succeeding|working)"
_NEGATION_PREFIX = (
    r"(?:(?:did|does|was|were|is|are|has|have|will|would|could|should)"
    r"(?: not|n['’]t)|cannot|can not|can['’]t|won['’]t|never|not|without)"
)
_NOMINAL_NEGATED_SUBJECT = (
    r"(?:(?:no|zero)\s+(?:\w+[ -]+){1,3}|"
    r"none\s+of\s+(?:the\s+)?(?:\w+[ -]+){1,3}|nothing\s+)"
)


def _negated_completion_spans(text):
    """Spans where a completion term is directly or nominally negated."""
    negated = [
        match.span()
        for match in re.finditer(
            rf"\b{_NEGATION_PREFIX} "
            rf"(?!only\b){_COMPLETION_MODIFIER}(?:(?:have )?been |be )?"
            rf"{_COMPLETION_MODIFIER}{_COMPLETION_TERM}{_COMPLETION_SUFFIX}\b",
            text,
        )
    ]
    nominal = [
        match.span()
        for match in re.finditer(
            rf"\b{_NOMINAL_NEGATED_SUBJECT}"
            r"(?:(?:has|have|is|are|was|were)\s+)?"
            r"(?:(?:currently|fully|quite|successfully|ultimately|yet)\s+){0,3}"
            rf"{_COMPLETION_TERM}{_COMPLETION_SUFFIX}\b",
            text,
        )
    ]
    return negated, nominal


def _unfinished_completion_spans(text):
    """Spans where completion failed, is deferred, or was stopped."""
    failed = [
        match.span()
        for match in re.finditer(
            rf"\b{_FAILURE_TERM}\s+to\s+{_COMPLETION_MODIFIER}{_COMPLETION_TERM}"
            rf"{_COMPLETION_SUFFIX}\b",
            text,
        )
    ]
    deferred = [
        match.span()
        for match in re.finditer(
            rf"\b(?:(?:has|have|is|are|was|were)\s+)?yet\s+to\s+"
            rf"{_COMPLETION_MODIFIER}{_COMPLETION_TERM}{_COMPLETION_SUFFIX}\b",
            text,
        )
    ]
    stopped = [
        match.span()
        for match in re.finditer(
            rf"\b(?:cease[ds]?|stop(?:ped|s)?)\s+{_COMPLETION_MODIFIER}"
            rf"{_PROGRESSIVE_COMPLETION_TERM}{_COMPLETION_SUFFIX}\b",
            text,
        )
    ]
    return failed, deferred, stopped


def _negated_failure_spans(text):
    """Spans where a failure term is itself negated (a success signal)."""
    return [
        match.span()
        for match in re.finditer(
            rf"\b(?:(?:no|zero)\s+(?:\w+\s+){{0,3}}{_FAILURE_TERM}|"
            rf"none\s+of\s+(?:the\s+)?(?:\w+\s+){{0,3}}{_FAILURE_TERM}|"
            rf"nothing\s+{_FAILURE_TERM}|"
            rf"{_NEGATION_PREFIX}\s+(?!only\b){_COMPLETION_MODIFIER}{_FAILURE_TERM})\b",
            text,
        )
    ]


def _collect_outcome_signals(text, suppressed, negated_failure):
    """Assemble (position, is_success) signals in resolution order."""
    signals = [
        (match.start(), True)
        for match in re.finditer(rf"\b{_COMPLETION_TERM}\b", text)
        if not any(start <= match.start() < end for start, end in suppressed)
    ]
    signals.extend(
        (match.start(), False)
        for match in re.finditer(
            rf"\b{_FAILURE_TERM}\b|"
            r"\b(?:error|failure|issue|problem|race|risk)s?\s+"
            r"(?:persist\w*|open|unresolved)\b|"
            r"\b(?:remain\w*|still)\s+"
            r"(?:blocked|broken|failing|incomplete|unsafe|unresolved)\b",
            text,
        )
        if not any(start <= match.start() < end for start, end in negated_failure)
    )
    return signals


def _extend_end_markers(signals, false_ends, true_ends):
    """Append span-end markers so a trailing negation outranks earlier prose."""
    signals.extend((end, False) for spans in false_ends for _, end in spans)
    signals.extend((end, True) for _, end in true_ends)
    return signals


def terminal_outcome_agrees(outcome, success):
    """Whether the final observable outcome signal agrees with a success label."""
    if not isinstance(outcome, str) or not isinstance(success, bool):
        return True
    text = outcome.casefold()
    negated, nominal = _negated_completion_spans(text)
    failed, deferred, stopped = _unfinished_completion_spans(text)
    negated_failure = _negated_failure_spans(text)
    suppressed = negated + nominal + failed + deferred + stopped
    signals = _collect_outcome_signals(text, suppressed, negated_failure)
    signals = _extend_end_markers(
        signals, (negated, nominal, deferred, stopped), negated_failure
    )
    # Non-empty outcomes are validated by the caller. Vocabulary that is
    # neither an explicit success nor an explicit failure is neutral rather
    # than contradictory; the schema does not prescribe exact prose.
    return not signals or max(signals)[1] is success


if __package__:
    _expose_package_sibling(__name__)
