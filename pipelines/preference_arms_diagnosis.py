#!/usr/bin/env python3
"""The bounded diagnosis document contract and its artifact naming."""

from __future__ import annotations

import json
import math
import re
import unicodedata
from typing import Any, Sequence

import sys
from pathlib import Path

_PIPELINES = Path(__file__).resolve().parent
if str(_PIPELINES) not in sys.path:
    sys.path.insert(0, str(_PIPELINES))

from preference_arms_text import (  # noqa: E402
    PreferenceArmsError,
    _ENCODED_BLOB_RE,
    _is_rejected_trajectory_key,
    _text_contains_rejected_trajectory_mapping,
)


HANDOFF_RECEIPT_VERSION = 2


MAX_DIAGNOSIS_BYTES = 64 * 1024


MAX_DIAGNOSIS_NARRATIVE_CHARS = 4 * 1024


MAX_DIAGNOSIS_LINE_CHARS = 2 * 1024


MAX_DIAGNOSIS_DEPTH = 32


MAX_DIAGNOSIS_NODES = 10_000


MAX_DIAGNOSIS_COMPONENTS = 64


DIAGNOSIS_SECTIONS = (
    "Shared context",
    "Root cause",
    "Cascade effects",
    "Supervisor catch",
    "Repair sketch",
    "Target reward delta",
)


_COMPONENT_SLUG_RE = re.compile(r"[a-z][a-z0-9_]{0,63}\Z")


_POSITIVE_ROUND = r"(?:0[1-9]|[1-9][0-9]+)"


_DIAGNOSIS_NAME_RE = re.compile(
    rf"diagnosis-(?P<index>[0-9]{{2}})-r(?P<round>{_POSITIVE_ROUND})\.md\Z"
)


_STAGING_NAME_RE = re.compile(rf"r(?P<round>{_POSITIVE_ROUND})-(?P<token>[0-9a-f]{{32}})\Z")


_FACTORY_SLUG_RE = re.compile(r"[a-z0-9][a-z0-9-]*\Z")


def diagnosis_filenames(round_number: int, count: int) -> tuple[str, ...]:
    """Return the transaction-derived contiguous diagnosis allowlist."""

    if type(round_number) is not int or round_number < 1:
        raise PreferenceArmsError("diagnosis round must be a positive integer")
    if type(count) is not int or count < 1:
        raise PreferenceArmsError("diagnosis count must be a positive integer")
    round_text = f"{round_number:02d}"
    return tuple(f"diagnosis-{index:02d}-r{round_text}.md" for index in range(1, count + 1))


def diagnosis_receipt_filename(round_number: int) -> str:
    """Return the one canonical receipt basename for a round."""

    if type(round_number) is not int or round_number < 1:
        raise PreferenceArmsError("diagnosis receipt round must be a positive integer")
    return f"diagnosis-handoff-receipt-r{round_number:02d}.json"


def _decoded_utf8(payload: bytes, label: str) -> str:
    try:
        return payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PreferenceArmsError(f"{label} is not valid UTF-8: {exc}") from exc


def _unique_object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant {value}")


def _strict_json_object(payload: bytes, *, label: str) -> dict[str, Any]:
    """Decode one finite JSON object while rejecting duplicate keys."""

    text = _decoded_utf8(payload, label)
    try:
        value = json.loads(
            text,
            object_pairs_hook=_unique_object_pairs,
            parse_constant=_reject_json_constant,
        )
    except (json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise PreferenceArmsError(f"{label} is not strict JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise PreferenceArmsError(f"{label} must be a JSON object")
    return value


def _strip_blank_edges(lines: list[str]) -> None:
    """Drop leading and trailing blank lines in place."""

    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()


def _is_single_json_fence(lines: list[str]) -> bool:
    if len(lines) < 3:
        return False
    if lines[0] != "```json":
        return False
    return lines[-1] == "```"


def _diagnosis_fenced_object(lines: list[str], *, label: str) -> dict[str, Any]:
    """Decode a section that contains exactly one fenced JSON object."""

    _strip_blank_edges(lines)
    if not _is_single_json_fence(lines):
        raise PreferenceArmsError(f"{label} must contain exactly one fenced JSON object")
    if any(line.startswith("```") for line in lines[1:-1]):
        raise PreferenceArmsError(f"{label} contains an extra code fence")
    payload = "\n".join(lines[1:-1]).encode("utf-8")
    return _strict_json_object(payload, label=label)


def _has_encoded_marker(lowered: str) -> bool:
    """A ``data:`` or percent-encoded brace marker in casefolded text."""

    if "data:" in lowered:
        return True
    if "%7b" in lowered:
        return True
    return "%7d" in lowered


def _is_serialized_payload(text: str) -> bool:
    """Text that smuggles a serialized trajectory mapping or encoded blob."""

    # Compatibility spellings fold first, so a fullwidth delimiter reaches
    # every pattern below in the ASCII form each one recognizes.
    compatible = unicodedata.normalize("NFKC", text)
    if _text_contains_rejected_trajectory_mapping(compatible):
        return True
    if _ENCODED_BLOB_RE.search(compatible):
        return True
    return _has_encoded_marker(compatible.casefold())


def _check_context_budget(budget: list[int], depth: int, label: str) -> None:
    budget[0] += 1
    if budget[0] > MAX_DIAGNOSIS_NODES:
        raise PreferenceArmsError(f"{label} exceeds the shared-context node limit")
    if depth > MAX_DIAGNOSIS_DEPTH:
        raise PreferenceArmsError(f"{label} exceeds the shared-context depth limit")


def _reject_forbidden_context_keys(value: dict[str, Any], label: str) -> None:
    forbidden = sorted(key for key in value if _is_rejected_trajectory_key(key))
    if forbidden:
        raise PreferenceArmsError(
            f"{label} contains rejected-trajectory keys: " + ", ".join(forbidden)
        )


def _validate_context_children(items, *, label: str, depth: int, budget: list[int]) -> None:
    for item in items:
        _validate_shared_context_tree(item, label=label, depth=depth + 1, budget=budget)


def _validate_context_scalar(value: Any, label: str) -> None:
    if isinstance(value, str) and _is_serialized_payload(value):
        raise PreferenceArmsError(f"{label} contains an encoded or serialized payload string")
    if type(value) is float and not math.isfinite(value):
        raise PreferenceArmsError(f"{label} contains a non-finite number")


def _validate_shared_context_tree(
    value: Any,
    *,
    label: str,
    depth: int = 0,
    budget: list[int] | None = None,
) -> None:
    """Reject nested payload channels inside the two allowed context objects."""

    if budget is None:
        budget = [0]
    _check_context_budget(budget, depth, label)
    if isinstance(value, dict):
        _reject_forbidden_context_keys(value, label)
        _validate_context_children(value.values(), label=label, depth=depth, budget=budget)
        return
    if isinstance(value, list):
        _validate_context_children(value, label=label, depth=depth, budget=budget)
        return
    _validate_context_scalar(value, label)


def _has_control_character(text: str) -> bool:
    return any(unicodedata.category(char) == "Cc" and char not in "\t\n" for char in text)


def _decoded_diagnosis_text(payload: bytes, label: str) -> str:
    """The document's text, within budget and free of control characters."""

    if len(payload) > MAX_DIAGNOSIS_BYTES:
        raise PreferenceArmsError(f"{label} exceeds the {MAX_DIAGNOSIS_BYTES}-byte diagnosis limit")
    text = _decoded_utf8(payload, label).replace("\r\n", "\n")
    if "\r" in text:
        raise PreferenceArmsError(f"{label} contains an unsupported bare carriage return")
    if _has_control_character(text):
        raise PreferenceArmsError(f"{label} contains an unsupported control character")
    return text


def _validated_diagnosis_headings(lines: list[str], label: str) -> list[str]:
    """The exact heading skeleton, or the document is refused."""

    if not lines or lines[0] != "# Diagnosis":
        raise PreferenceArmsError(f"{label} must start with '# Diagnosis'")
    expected_headings = [f"## {name}" for name in DIAGNOSIS_SECTIONS]
    observed_headings = [line for line in lines[1:] if line.startswith("#")]
    if observed_headings != expected_headings:
        raise PreferenceArmsError(
            f"{label} headings must be exactly " + ", ".join(expected_headings)
        )
    return expected_headings


def _section_end(positions: list[int], index: int, line_count: int) -> int:
    if index + 1 < len(positions):
        return positions[index + 1]
    return line_count


def _diagnosis_sections(text: str, label: str) -> dict[str, list[str]]:
    """Split the document on its exact required heading skeleton."""

    lines = text.split("\n")
    _strip_blank_edges(lines)
    expected_headings = _validated_diagnosis_headings(lines, label)
    positions = [lines.index(heading) for heading in expected_headings]
    return {
        name: lines[start + 1 : _section_end(positions, index, len(lines))]
        for index, (name, start) in enumerate(zip(DIAGNOSIS_SECTIONS, positions, strict=True))
    }


def _context_values_are_objects(context: dict[str, Any]) -> bool:
    if not isinstance(context["state"], dict):
        return False
    return isinstance(context["proposed_action"], dict)


def _validated_shared_context(sections: dict[str, list[str]], label: str) -> dict[str, Any]:
    context = _diagnosis_fenced_object(
        list(sections["Shared context"]),
        label=f"{label} shared context",
    )
    if set(context) != {"state", "proposed_action"}:
        raise PreferenceArmsError(
            f"{label} shared context keys must be exactly state and proposed_action"
        )
    if not _context_values_are_objects(context):
        raise PreferenceArmsError(f"{label} shared context values must be JSON objects")
    _validate_shared_context_tree(context, label=f"{label} shared context")
    return context


def _has_oversized_line(narrative: str) -> bool:
    return any(len(line) > MAX_DIAGNOSIS_LINE_CHARS for line in narrative.splitlines())


def _contains_code_fence(narrative: str) -> bool:
    return "```" in narrative or "~~~" in narrative


def _contains_object_syntax(narrative: str) -> bool:
    return "{" in narrative or "}" in narrative


def _contains_raw_html(narrative: str) -> bool:
    if "<!--" in narrative:
        return True
    return re.search(r"</?[A-Za-z][^>]*>", narrative) is not None


def _contains_markdown_table(narrative: str) -> bool:
    return any(re.fullmatch(r"\s*\|.*\|\s*", line) is not None for line in narrative.splitlines())


def _is_serialized_narrative(narrative: str, lowered: str) -> bool:
    if _is_serialized_payload(narrative):
        return True
    return re.search(r"\bbase64\b", lowered) is not None


def _narrative_size_violation(narrative: str) -> str | None:
    if not narrative:
        return "is empty"
    if len(narrative) > MAX_DIAGNOSIS_NARRATIVE_CHARS:
        return "exceeds the narrative limit"
    if _has_oversized_line(narrative):
        return "has an oversized line"
    return None


def _narrative_syntax_violation(narrative: str, lowered: str) -> str | None:
    if _contains_code_fence(narrative):
        return "contains a code fence"
    if _contains_object_syntax(narrative):
        return "contains object syntax"
    if _contains_raw_html(narrative):
        return "contains raw HTML"
    if _contains_markdown_table(narrative):
        return "contains a Markdown table"
    if _is_serialized_narrative(narrative, lowered):
        return "contains an encoded or serialized payload"
    return None


def _narrative_violation(narrative: str) -> str | None:
    """The first bounded-prose rule this section breaks, as a message suffix."""

    size = _narrative_size_violation(narrative)
    if size is not None:
        return size
    # Size is measured on what Session A actually wrote; every syntax and
    # payload check then runs on the compatibility-folded text, so fullwidth
    # braces, colons, and backticks cannot spell a delimiter past a rule that
    # recognizes only its ASCII form.
    compatible = unicodedata.normalize("NFKC", narrative)
    return _narrative_syntax_violation(compatible, compatible.casefold())


def _validate_diagnosis_narratives(sections: dict[str, list[str]], label: str) -> None:
    for name in DIAGNOSIS_SECTIONS[1:-1]:
        narrative = "\n".join(sections[name]).strip()
        violation = _narrative_violation(narrative)
        if violation is not None:
            raise PreferenceArmsError(f"{label} section {name!r} {violation}")


def _is_reward_delta_shape(target: dict[str, Any]) -> bool:
    if set(target) != {"per_component", "total"}:
        return False
    return isinstance(target["per_component"], dict)


def _component_count_in_range(components: dict[str, Any]) -> bool:
    if not components:
        return False
    return len(components) <= MAX_DIAGNOSIS_COMPONENTS


def _is_finite_number(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if not isinstance(value, (int, float)):
        return False
    if type(value) is not float:
        return True
    return math.isfinite(value)


def _is_valid_component_key(key: Any) -> bool:
    if not isinstance(key, str):
        return False
    return _COMPONENT_SLUG_RE.fullmatch(key) is not None


def _validate_reward_components(components: dict[str, Any], label: str) -> None:
    for key, value in components.items():
        if not _is_valid_component_key(key):
            raise PreferenceArmsError(
                f"{label} target reward component {key!r} must be a finite number"
            )
        if not _is_finite_number(value):
            raise PreferenceArmsError(
                f"{label} target reward component {key!r} must be a finite number"
            )


def _both_finite(left: float, right: float) -> bool:
    if not math.isfinite(left):
        return False
    return math.isfinite(right)


def _reward_totals(total: Any, components: dict[str, Any], label: str) -> tuple[float, float]:
    """The declared total and the component sum, both finite and in range."""

    try:
        numeric_total = float(total)
        component_sum = math.fsum(float(value) for value in components.values())
    except OverflowError as exc:
        raise PreferenceArmsError(
            f"{label} target reward values exceed the supported numeric range"
        ) from exc
    if not _both_finite(numeric_total, component_sum):
        raise PreferenceArmsError(
            f"{label} target reward values exceed the supported numeric range"
        )
    return numeric_total, component_sum


def _reconcile_reward_total(total: Any, components: dict[str, Any], label: str) -> None:
    numeric_total, component_sum = _reward_totals(total, components, label)
    if numeric_total <= 0:
        raise PreferenceArmsError(f"{label} target reward total must be positive")
    if not math.isclose(numeric_total, component_sum, rel_tol=0.0, abs_tol=1e-6):
        raise PreferenceArmsError(f"{label} target reward total does not equal the component sum")


def _validated_target_reward_delta(sections: dict[str, list[str]], label: str) -> dict[str, Any]:
    target = _diagnosis_fenced_object(
        list(sections["Target reward delta"]),
        label=f"{label} target reward delta",
    )
    if not _is_reward_delta_shape(target):
        raise PreferenceArmsError(
            f"{label} target reward delta must contain per_component and total only"
        )
    components = target["per_component"]
    if not _component_count_in_range(components):
        raise PreferenceArmsError(
            f"{label} target reward delta must have 1-{MAX_DIAGNOSIS_COMPONENTS} components"
        )
    _validate_reward_components(components, label)
    if not _is_finite_number(target["total"]):
        raise PreferenceArmsError(f"{label} target reward total must be a finite number")
    _reconcile_reward_total(target["total"], components, label)
    return target


def validate_diagnosis_document(payload: bytes, *, label: str) -> dict[str, Any]:
    """Validate the bounded diagnosis bridge without returning its prose.

    The bridge may carry only one shared-context object, five bounded prose
    sections, and one target-delta object. It cannot carry another code block,
    heading, or serialized trajectory-key mapping that would expose Session B
    to the rejected gate, execution, outcome, or reward payload.
    """

    text = _decoded_diagnosis_text(payload, label)
    sections = _diagnosis_sections(text, label)
    context = _validated_shared_context(sections, label)
    _validate_diagnosis_narratives(sections, label)
    target = _validated_target_reward_delta(sections, label)
    return {"shared_context": context, "target_reward_delta": target}


def _session_b_outputs(names: Sequence[str], round_text: str) -> list[str]:
    forbidden_names = {
        f"batch-r{round_text}.jsonl",
        f"NOTES-r{round_text}.md",
    }
    chosen_re = re.compile(rf"chosen-[A-Za-z0-9._-]+-r{re.escape(round_text)}\.json\Z")
    return sorted(name for name in names if name in forbidden_names or chosen_re.fullmatch(name))
