"""The recall probe's two prompt variants and their leak check.

``no_evidence`` is the SFT prompt without its failing-doctest section;
``docstring_only`` is the target function's decorators and ``def`` through its
docstring (cut by :mod:`.recall_stub`), body elided, asking for the whole
module. Both are rendered from three public reads of a record, so neither can
carry the repaired module or the restored span, and :func:`prompt_rows`
refuses a record whose rendering would carry either.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from . import recall_stub, views
from . import vocabulary as cv
from ._contract import bind_import_twin, contains_hidden_reasoning_key

PROMPT_KEYS = frozenset({"id", "variant", "prompt", "lineage_id", "group_id", "split", "family"})
EVIDENCE_SECTION = "### Failing doctest examples\n{evidence}\n\n"
NO_EVIDENCE_TEMPLATE = views.PROMPT_TEMPLATE.replace(EVIDENCE_SECTION, "")  # the SFT prompt, less it
DOCSTRING_ONLY_TEMPLATE = (
    "{task}\n\n### Module: program.py (body elided)\n```python\n{stub}```\n\n"
    "### Instructions\n{instructions}\n"
)

__all__ = [
    "DOCSTRING_ONLY_TEMPLATE", "EVIDENCE_SECTION", "NO_EVIDENCE_TEMPLATE", "PROMPT_KEYS",
    "ProbeView", "probe_view", "prompt_findings", "prompt_rows", "render_docstring_only",
    "render_no_evidence",
]


@dataclass(frozen=True)
class ProbeView:
    """The only fields a probe prompt is rendered from: the SFT view's task statement and
    broken module (its evidence is not read) and the target's name, which is public as the
    ``def`` in that module."""

    task_specification: str
    program_text: str
    function: str


def probe_view(record: dict[str, Any]) -> ProbeView:
    """Three reads, nothing else."""

    scenario = record["scenario"]
    return ProbeView(
        str(scenario["task_specification"]),
        str(scenario["broken_program"]["files"][cv.PROGRAM_FILENAME]),
        str(scenario["source"]["upstream"]["function"]),
    )


def render_no_evidence(view: ProbeView) -> str:
    """The SFT prompt without its ``### Failing doctest examples`` section."""

    return NO_EVIDENCE_TEMPLATE.format(
        task=view.task_specification, program=view.program_text,
        instructions=cv.PROMPT_INSTRUCTIONS,
    )


def render_docstring_only(view: ProbeView) -> str:
    """Signature and docstring only; the model is asked for the complete module."""

    return DOCSTRING_ONLY_TEMPLATE.format(
        task=cv.DOCSTRING_ONLY_TASK,
        stub=recall_stub.docstring_stub(view.program_text, view.function),
        instructions=cv.DOCSTRING_ONLY_INSTRUCTIONS,
    )


def _renderers() -> dict[str, Callable[[ProbeView], str]]:
    """Each variant's renderer, read through the live module namespace (a test seam)."""

    return {
        cv.RECALL_VARIANT_NO_EVIDENCE: render_no_evidence,
        cv.RECALL_VARIANT_DOCSTRING_ONLY: render_docstring_only,
    }


def _known_variant(variant: Any) -> str | None:
    return variant if isinstance(variant, str) and variant in cv.RECALL_VARIANTS else None


def _shown_code(view: ProbeView, variant: str) -> str:
    """The code block the variant shows: the broken module, or the stub cut from it.

    Raises ``RepairRefusal`` (``RECALL_TARGET_NOT_RENDERABLE``) through
    :func:`.recall_stub.docstring_stub` when the target's header cannot be cut.
    """

    if variant == cv.RECALL_VARIANT_NO_EVIDENCE:
        return view.program_text
    return recall_stub.docstring_stub(view.program_text, view.function)


def _restored_span_hidden(record: dict[str, Any], view: ProbeView, variant: str) -> bool:
    """The mutated span appears only as the mutant's replacement (``no_evidence``) or not at
    all (``docstring_only``: it lies in the elided body, outside the header).

    Raises ``RepairRefusal`` (``RECALL_TARGET_NOT_RENDERABLE``) through
    :func:`.recall_stub.header` when the target's header cannot be cut; the leak check fails
    closed rather than report a span it cannot place.
    """

    site = record["intervention"]["site"]
    start = int(site["start_byte"])
    replacement = str(site["replacement_text"]).encode("utf-8")
    end = start + len(replacement)
    if variant == cv.RECALL_VARIANT_NO_EVIDENCE:
        return view.program_text.encode("utf-8")[start:end] == replacement
    header = recall_stub.header(view.program_text, view.function)
    return end <= header.start_byte or start >= header.end_byte


def _variant_findings(record: dict[str, Any], view: ProbeView, variant: str,
                      prompt: str) -> list[str]:
    """What a known variant's prompt must be: its rendering, showing its code block, with the
    mutated span shown only as the mutant's replacement or not at all."""

    findings = []
    if prompt != _renderers()[variant](view):
        findings.append(cv.LEAK_PROMPT_NOT_RENDERED_FROM_PUBLIC_VIEW)
    if f"```python\n{_shown_code(view, variant)}```" not in prompt:
        findings.append(cv.LEAK_PROMPT_PROGRAM_NOT_BROKEN_TEXT)
    if not _restored_span_hidden(record, view, variant):
        findings.append(cv.LEAK_PROMPT_CONTAINS_REPAIR)
    return findings


def _rendering_findings(record: dict[str, Any], view: ProbeView, row: dict[str, Any],
                        prompt: str) -> list[str]:
    variant = _known_variant(row.get("variant"))
    if variant is None:  # no rendering and no code block to compare against
        return [cv.LEAK_PROMPT_NOT_RENDERED_FROM_PUBLIC_VIEW,
                cv.LEAK_PROMPT_PROGRAM_NOT_BROKEN_TEXT]
    return _variant_findings(record, view, variant, prompt)


def prompt_findings(record: dict[str, Any], row: dict[str, Any]) -> list[str]:
    """Every declared leak code the probe row violates against its record.

    Raises ``RepairRefusal`` (``RECALL_TARGET_NOT_RENDERABLE``) when the record's target
    header cannot be cut, as rendering the ``docstring_only`` variant would.
    """

    findings = [] if set(row) == PROMPT_KEYS else [cv.LEAK_VIEW_EXTRA_KEYS]
    prompt = str(row.get("prompt", ""))
    findings += _rendering_findings(record, probe_view(record), row, prompt)
    if views.completion_of(record) in prompt:
        findings.append(cv.LEAK_PROMPT_CONTAINS_REPAIR)
    if contains_hidden_reasoning_key(row):
        findings.append(cv.LEAK_HIDDEN_REASONING_KEY)
    return list(dict.fromkeys(findings))


def _identity(record: dict[str, Any]) -> dict[str, Any]:
    split_lineage = record["provenance"]["split_lineage"]
    return {
        "id": record["id"], "lineage_id": split_lineage["lineage_id"],
        "group_id": split_lineage["group_id"], "split": split_lineage["split"],
        "family": record["scenario"]["source"]["family"],
    }


def _refuse_leaks(record: dict[str, Any], row: dict[str, Any]) -> None:
    findings = prompt_findings(record, row)
    cv.refuse_when(
        bool(findings), cv.FINDING_RECALL_PROMPT_LEAK,
        f"record {cv.shown(record['id'])} variant {row['variant']} fails the leak check: "
        + ", ".join(findings),
    )


def prompt_rows(record: dict[str, Any]) -> list[dict[str, Any]]:
    """Both variants of one positive record, in variant order; refused on any leak finding."""

    cv.refuse_when(
        not views.is_positive(record), cv.FINDING_RECORD_NOT_A_POSITIVE_EXAMPLE,
        f"record {cv.shown(record.get('id'))} is not an accepted, validated, eligible example",
    )
    view, identity = probe_view(record), _identity(record)
    rows = [
        {**identity, "variant": variant, "prompt": render(view)}
        for variant, render in _renderers().items()
    ]
    for row in rows:
        _refuse_leaks(record, row)
    return rows


bind_import_twin(__name__)
