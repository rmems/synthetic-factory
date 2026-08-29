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


def _strict_json_object(payload: bytes, *, label: str) -> dict[str, Any]:
    """Decode one finite JSON object while rejecting duplicate keys."""

    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PreferenceArmsError(f"{label} is not valid UTF-8: {exc}") from exc

    def object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key {key!r}")
            result[key] = value
        return result

    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON constant {value}")

    try:
        value = json.loads(
            text,
            object_pairs_hook=object_pairs,
            parse_constant=reject_constant,
        )
    except (json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise PreferenceArmsError(f"{label} is not strict JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise PreferenceArmsError(f"{label} must be a JSON object")
    return value


def _diagnosis_fenced_object(lines: list[str], *, label: str) -> dict[str, Any]:
    """Decode a section that contains exactly one fenced JSON object."""

    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    if len(lines) < 3 or lines[0] != "```json" or lines[-1] != "```":
        raise PreferenceArmsError(f"{label} must contain exactly one fenced JSON object")
    if any(line.startswith("```") for line in lines[1:-1]):
        raise PreferenceArmsError(f"{label} contains an extra code fence")
    payload = "\n".join(lines[1:-1]).encode("utf-8")
    return _strict_json_object(payload, label=label)


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
    budget[0] += 1
    if budget[0] > MAX_DIAGNOSIS_NODES:
        raise PreferenceArmsError(f"{label} exceeds the shared-context node limit")
    if depth > MAX_DIAGNOSIS_DEPTH:
        raise PreferenceArmsError(f"{label} exceeds the shared-context depth limit")
    if isinstance(value, dict):
        forbidden = sorted(key for key in value if _is_rejected_trajectory_key(key))
        if forbidden:
            raise PreferenceArmsError(
                f"{label} contains rejected-trajectory keys: " + ", ".join(forbidden)
            )
        for item in value.values():
            _validate_shared_context_tree(
                item,
                label=label,
                depth=depth + 1,
                budget=budget,
            )
    elif isinstance(value, list):
        for item in value:
            _validate_shared_context_tree(
                item,
                label=label,
                depth=depth + 1,
                budget=budget,
            )
    elif isinstance(value, str) and (
        _text_contains_rejected_trajectory_mapping(value)
        or _ENCODED_BLOB_RE.search(value)
        or "data:" in value.casefold()
        or "%7b" in value.casefold()
        or "%7d" in value.casefold()
    ):
        raise PreferenceArmsError(f"{label} contains an encoded or serialized payload string")
    elif type(value) is float and not math.isfinite(value):
        raise PreferenceArmsError(f"{label} contains a non-finite number")


def validate_diagnosis_document(payload: bytes, *, label: str) -> dict[str, Any]:
    """Validate the bounded diagnosis bridge without returning its prose.

    The bridge may carry only one shared-context object, five bounded prose
    sections, and one target-delta object. It cannot carry another code block,
    heading, or serialized trajectory-key mapping that would expose Session B
    to the rejected gate, execution, outcome, or reward payload.
    """

    if len(payload) > MAX_DIAGNOSIS_BYTES:
        raise PreferenceArmsError(f"{label} exceeds the {MAX_DIAGNOSIS_BYTES}-byte diagnosis limit")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PreferenceArmsError(f"{label} is not valid UTF-8: {exc}") from exc
    text = text.replace("\r\n", "\n")
    if "\r" in text:
        raise PreferenceArmsError(f"{label} contains an unsupported bare carriage return")
    if any(
        unicodedata.category(character) == "Cc" and character not in "\t\n" for character in text
    ):
        raise PreferenceArmsError(f"{label} contains an unsupported control character")
    lines = text.split("\n")
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines or lines[0] != "# Diagnosis":
        raise PreferenceArmsError(f"{label} must start with '# Diagnosis'")

    expected_headings = [f"## {name}" for name in DIAGNOSIS_SECTIONS]
    observed_headings = [line for line in lines[1:] if line.startswith("#")]
    if observed_headings != expected_headings:
        raise PreferenceArmsError(
            f"{label} headings must be exactly " + ", ".join(expected_headings)
        )
    positions = [lines.index(heading) for heading in expected_headings]
    sections = {
        name: lines[start + 1 : positions[index + 1] if index + 1 < len(positions) else len(lines)]
        for index, (name, start) in enumerate(zip(DIAGNOSIS_SECTIONS, positions, strict=True))
    }

    context = _diagnosis_fenced_object(
        list(sections["Shared context"]),
        label=f"{label} shared context",
    )
    if set(context) != {"state", "proposed_action"}:
        raise PreferenceArmsError(
            f"{label} shared context keys must be exactly state and proposed_action"
        )
    if not isinstance(context["state"], dict) or not isinstance(context["proposed_action"], dict):
        raise PreferenceArmsError(f"{label} shared context values must be JSON objects")
    _validate_shared_context_tree(context, label=f"{label} shared context")

    narratives: dict[str, str] = {}
    for name in DIAGNOSIS_SECTIONS[1:-1]:
        narrative = "\n".join(sections[name]).strip()
        if not narrative:
            raise PreferenceArmsError(f"{label} section {name!r} is empty")
        if len(narrative) > MAX_DIAGNOSIS_NARRATIVE_CHARS:
            raise PreferenceArmsError(f"{label} section {name!r} exceeds the narrative limit")
        if any(len(line) > MAX_DIAGNOSIS_LINE_CHARS for line in narrative.splitlines()):
            raise PreferenceArmsError(f"{label} section {name!r} has an oversized line")
        lowered = narrative.casefold()
        if "```" in narrative or "~~~" in narrative:
            raise PreferenceArmsError(f"{label} section {name!r} contains a code fence")
        if "{" in narrative or "}" in narrative:
            raise PreferenceArmsError(f"{label} section {name!r} contains object syntax")
        if "<!--" in narrative or re.search(r"</?[A-Za-z][^>]*>", narrative):
            raise PreferenceArmsError(f"{label} section {name!r} contains raw HTML")
        if any(re.fullmatch(r"\s*\|.*\|\s*", line) is not None for line in narrative.splitlines()):
            raise PreferenceArmsError(f"{label} section {name!r} contains a Markdown table")
        if (
            _text_contains_rejected_trajectory_mapping(narrative)
            or _ENCODED_BLOB_RE.search(narrative)
            or "data:" in lowered
            or "%7b" in lowered
            or "%7d" in lowered
            or re.search(r"\bbase64\b", lowered)
        ):
            raise PreferenceArmsError(
                f"{label} section {name!r} contains an encoded or serialized payload"
            )
        narratives[name] = narrative

    target = _diagnosis_fenced_object(
        list(sections["Target reward delta"]),
        label=f"{label} target reward delta",
    )
    if set(target) != {"per_component", "total"} or not isinstance(target["per_component"], dict):
        raise PreferenceArmsError(
            f"{label} target reward delta must contain per_component and total only"
        )
    components = target["per_component"]
    if not components or len(components) > MAX_DIAGNOSIS_COMPONENTS:
        raise PreferenceArmsError(
            f"{label} target reward delta must have 1-{MAX_DIAGNOSIS_COMPONENTS} components"
        )
    for key, value in components.items():
        if (
            not isinstance(key, str)
            or _COMPONENT_SLUG_RE.fullmatch(key) is None
            or isinstance(value, bool)
            or not isinstance(value, (int, float))
            or (type(value) is float and not math.isfinite(value))
        ):
            raise PreferenceArmsError(
                f"{label} target reward component {key!r} must be a finite number"
            )
    total = target["total"]
    if (
        isinstance(total, bool)
        or not isinstance(total, (int, float))
        or (type(total) is float and not math.isfinite(total))
    ):
        raise PreferenceArmsError(f"{label} target reward total must be a finite number")
    try:
        numeric_total = float(total)
        component_sum = math.fsum(float(value) for value in components.values())
    except OverflowError as exc:
        raise PreferenceArmsError(
            f"{label} target reward values exceed the supported numeric range"
        ) from exc
    if not math.isfinite(numeric_total) or not math.isfinite(component_sum):
        raise PreferenceArmsError(
            f"{label} target reward values exceed the supported numeric range"
        )
    if numeric_total <= 0:
        raise PreferenceArmsError(f"{label} target reward total must be positive")
    if not math.isclose(numeric_total, component_sum, rel_tol=0.0, abs_tol=1e-6):
        raise PreferenceArmsError(f"{label} target reward total does not equal the component sum")
    return {"shared_context": context, "target_reward_delta": target}


def _session_b_outputs(names: Sequence[str], round_text: str) -> list[str]:
    forbidden_names = {
        f"batch-r{round_text}.jsonl",
        f"NOTES-r{round_text}.md",
    }
    chosen_re = re.compile(rf"chosen-[A-Za-z0-9._-]+-r{re.escape(round_text)}\.json\Z")
    return sorted(name for name in names if name in forbidden_names or chosen_re.fullmatch(name))
