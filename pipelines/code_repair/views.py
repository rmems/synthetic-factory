#!/usr/bin/env python3
"""The SFT view: a projection of an explicit public allowlist, never of the record.

The prompt is a pure function of a :class:`PublicView` -- the task statement,
the broken module text and the bounded failure evidence -- and nothing else in
a record can reach it; the completion is the verified corrected module, raw,
with its trailing newline and no fences, so it is byte-equal to the text the
harness executed. Only an accepted, validated, curation-eligible record yields
a row. :func:`view_findings` re-derives a row from its record and reports every
divergence with a declared code; an export aborts on any.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from . import catalog as cat
from . import verify
from . import record_validation as validation
from . import vocabulary as cv
from ._contract import bind_import_twin, contains_hidden_reasoning_key, oc

VIEW_KEYS = frozenset({"prompt", "completion"})
PROMPT_TEMPLATE = (
    "{task}\n\n### Module: program.py\n```python\n{program}```\n\n"
    "### Failing doctest examples\n{evidence}\n\n### Instructions\n{instructions}\n"
)

__all__ = [
    "PROMPT_TEMPLATE", "PublicView", "VIEW_KEYS", "agoge_row", "completion_of", "is_positive",
    "public_view", "render_prompt", "sft_row", "view_findings", "evidence_findings",
]


@dataclass(frozen=True)
class PublicView:
    """The only fields a prompt is rendered from."""

    task_specification: str
    program_text: str
    evidence_text: str


def public_view(record: dict[str, Any]) -> PublicView:
    """The allowlisted projection: three reads, nothing else."""

    scenario, result = record["scenario"], record["result"]
    evidence = verify.render_evidence(
        list(result["public_failure_evidence"]), int(result["public_failure_omitted"])
    )
    return PublicView(
        str(scenario["task_specification"]),
        str(scenario["broken_program"]["files"][cv.PROGRAM_FILENAME]),
        evidence,
    )


def render_prompt(view: PublicView) -> str:
    return PROMPT_TEMPLATE.format(
        task=view.task_specification, program=view.program_text, evidence=view.evidence_text,
        instructions=cv.PROMPT_INSTRUCTIONS,
    )


def completion_of(record: dict[str, Any]) -> str:
    return str(record["candidate_prediction"]["predicted_repair"]["files"][cv.PROGRAM_FILENAME])


def is_positive(record: dict[str, Any]) -> bool:
    """Accepted, validated, and eligible under the shared curation gate with no findings."""

    try:
        validation.validate_shape(record)
        if not validation.verdict_matches(record):
            return False
    except (cv.RepairRefusal, KeyError, TypeError, ValueError, AttributeError):
        return False
    result = record.get("result") if isinstance(record.get("result"), dict) else {}
    if result.get("outcome") != cv.OUTCOME_ACCEPTED:
        return False
    if result.get("oracle_status") != cv.STATUS_VALIDATED:
        return False
    where = str(record.get("id", "record"))
    findings = oc.check_envelope(record, where) + oc.check_oracle_label_leak(record, where)
    eligible, _reasons = oc.curation_eligible(record, findings)
    return eligible


def sft_row(record: dict[str, Any]) -> dict[str, str]:
    """``{"prompt", "completion"}`` for a positive record; refused otherwise."""

    cv.refuse_when(
        not is_positive(record), cv.FINDING_RECORD_NOT_A_POSITIVE_EXAMPLE,
        f"record {cv.shown(record.get('id'))} is not an accepted, validated, eligible example",
    )
    row = {"prompt": render_prompt(public_view(record)), "completion": completion_of(record)}
    findings = view_findings(record, row)
    cv.refuse_when(bool(findings), cv.FINDING_RECORD_MALFORMED,
                   "record fails public view validation: " + ", ".join(findings))
    return row


def agoge_row(record: dict[str, Any]) -> dict[str, Any]:
    """The consumer's frozen-split row: identity fields and one pre-rendered text."""

    row = sft_row(record)
    lineage = record["provenance"]["split_lineage"]
    return {
        "canonical_id": record["id"], "lineage_id": lineage["lineage_id"],
        "group_id": lineage["group_id"], "split": lineage["split"],
        "text": row["prompt"] + cv.AGOGE_SEPARATOR + row["completion"],
        "completion_start_char": len(row["prompt"] + cv.AGOGE_SEPARATOR),
    }


def evidence_findings(record: dict[str, Any]) -> list[str]:
    """The stored evidence must be the bounded rendering of the mutant's failing rows."""

    try:
        scenario, result = record["scenario"], record["result"]
        examples = cat.examples_of(scenario["broken_program"]["files"][cv.PROGRAM_FILENAME],
                                   scenario["source"]["upstream"]["function"])
        expected_examples = [{"example_id": e.example_id, "source": e.source, "want": e.want}
                             for e in examples]
        phases = verify.phases_from_blocks(result["phases"])
        entries, omitted = verify.public_evidence(phases.mutant, examples)
        consistent = (expected_examples == scenario["public_tests"]["examples"]
                      and entries == result["public_failure_evidence"]
                      and omitted == result["public_failure_omitted"])
    except (KeyError, TypeError, ValueError, AttributeError):
        consistent = False
    return [] if consistent else [cv.LEAK_PUBLIC_EVIDENCE_NOT_FROM_ROWS]


def _completion_findings(record: dict[str, Any], row: dict[str, Any]) -> list[str]:
    findings = []
    completion = row.get("completion")
    predicted = record["candidate_prediction"]["predicted_repair"]["sha256"]
    digest = cat.sha256_text(completion) if isinstance(completion, str) else None
    verified = (
        digest is not None and is_positive(record)
        and digest == record["result"]["repaired_sha256"] == predicted
    )
    if not verified:
        findings.append(cv.LEAK_COMPLETION_NOT_VERIFIED)
    if completion == record["scenario"]["broken_program"]["files"][cv.PROGRAM_FILENAME]:
        findings.append(cv.LEAK_COMPLETION_EQUALS_BROKEN)
    return findings


def view_findings(record: dict[str, Any], row: dict[str, Any]) -> list[str]:
    """Every declared leak code the row violates against its record."""

    findings = []
    if set(row) != VIEW_KEYS:
        findings.append(cv.LEAK_VIEW_EXTRA_KEYS)
    view = public_view(record)
    if row.get("prompt") != render_prompt(view):
        findings.append(cv.LEAK_PROMPT_NOT_RENDERED_FROM_PUBLIC_VIEW)
    broken = record["scenario"]["broken_program"]["files"][cv.PROGRAM_FILENAME]
    if f"```python\n{broken}```" not in str(row.get("prompt", "")):
        findings.append(cv.LEAK_PROMPT_PROGRAM_NOT_BROKEN_TEXT)
    findings += evidence_findings(record)
    findings += _completion_findings(record, row)
    sections = [record.get(key) for key in ("scenario", "intervention", "candidate_prediction")]
    if contains_hidden_reasoning_key(row) or contains_hidden_reasoning_key(sections):
        findings.append(cv.LEAK_HIDDEN_REASONING_KEY)
    return findings


bind_import_twin(__name__)
