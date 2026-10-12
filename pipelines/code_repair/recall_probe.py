"""The offline recall probe: prompts out, completions scored, no model called here.

Every repair target is verbatim TheAlgorithms/Python code that code models
have seen in pretraining, which the export records as the evaluation
limitation ``POSSIBLE_UPSTREAM_CODE_RECALL``: a model may recall the upstream
module rather than repair the broken one. The probe measures that in two
steps the repository runs without a model. ``emit`` writes two deterministic
prompt variants per positive record -- ``no_evidence`` (the broken module with
the SFT task sentence and instruction, without the failing-doctest evidence)
and ``docstring_only`` (the target function's decorators and ``def`` through
its docstring, body elided) -- rendered from three public reads of the record,
so neither variant can carry the repaired module or the restored span; a
record whose rendering would carry either is refused. ``score`` reads completions produced
elsewhere, binds the prompts back to the run byte for byte, and compares each
completion to the record's verified repair exactly (SHA-256 of the text) and
structurally (the canonical AST digest of :mod:`.lineage`). Nothing is
executed: a completion is hashed and parsed, never imported or run. High
exact recall under ``docstring_only`` is memorised upstream code, not repair.
"""

from __future__ import annotations

import ast
import hashlib
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, NoReturn

from . import catalog as cat
from . import generate, lineage, views
from . import vocabulary as cv
from ._contract import (
    bind_import_twin,
    contains_hidden_reasoning_key,
    dumps_exact_json,
    is_under_raw,
    oc,
)
from .candidate_io import load_candidate_records
from .mutate_span import line_offsets

PROMPTS_FILENAME = "prompts.jsonl"
REPORT_FORMAT = "code-repair-recall-probe/1"
PROMPT_KEYS = frozenset({"id", "variant", "prompt", "lineage_id", "group_id", "split", "family"})
COMPLETION_KEYS = frozenset({"id", "variant", "completion"})
BODY_PLACEHOLDER = "..."
EVIDENCE_SECTION = "### Failing doctest examples\n{evidence}\n\n"
NO_EVIDENCE_TEMPLATE = views.PROMPT_TEMPLATE.replace(EVIDENCE_SECTION, "")  # the SFT prompt, less it
DOCSTRING_ONLY_TEMPLATE = (
    "{task}\n\n### Module: program.py (body elided)\n```python\n{stub}```\n\n"
    "### Instructions\n{instructions}\n"
)
SCORING = (
    "exact: the SHA-256 of the completion text equals result.repaired_sha256; structural: the "
    "canonical AST digest of the completion equals the repaired module's; rates are over the "
    "completions received; no completion was executed"
)

__all__ = [
    "BODY_PLACEHOLDER", "COMPLETION_KEYS", "DOCSTRING_ONLY_TEMPLATE", "EVIDENCE_SECTION",
    "NO_EVIDENCE_TEMPLATE",
    "PROMPTS_FILENAME", "PROMPT_KEYS", "REPORT_FORMAT", "SCORING", "EmitRequest", "ProbeView",
    "ScoreRequest", "docstring_stub", "emit", "probe_view", "prompt_findings", "prompt_rows",
    "render_docstring_only", "render_no_evidence", "score", "score_completion",
]


# --- the public reads and the two renderings ----------------------------------------------


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


@dataclass(frozen=True)
class _Header:
    """The target's decorators and ``def`` through its docstring, verbatim from the LF-framed
    broken module, the body's indentation, and the byte span the header occupies."""

    text: str
    indent: str
    start_byte: int
    end_byte: int

    @property
    def stub(self) -> str:
        return f"{self.text}{self.indent}{BODY_PLACEHOLDER}\n"


def _not_renderable(function: str, why: str) -> NoReturn:
    cv.refuse(cv.FINDING_RECALL_TARGET_NOT_RENDERABLE,
              f"function {cv.shown(function)} of the broken module {why}")


def _parsed_target(program_text: str, function: str) -> ast.FunctionDef | None:
    """The module-level ``def`` (parse only), or None when the text is not a module."""

    try:
        return cat.function_node(program_text, function)
    except (SyntaxError, ValueError, RecursionError):
        return None


def _documented_target(program_text: str, function: str) -> ast.FunctionDef:
    node = _parsed_target(program_text, function)
    if node is None:
        _not_renderable(function, "is not a parseable module-level def")
    if ast.get_docstring(node, clean=False) is None:
        _not_renderable(function, "has no docstring")
    if len(node.body) < 2:
        _not_renderable(function, "has no body after its docstring to elide")
    return node


def _is_stub_of(stub: str, function: str, original: ast.FunctionDef) -> bool:
    """The stub parses to the target with the original docstring and the placeholder alone
    after it: nothing of the body survived and nothing of the header was cut."""

    node = _parsed_target(stub, function)
    if node is None or len(node.body) != 2:
        return False
    placeholder = node.body[1]
    return (
        ast.get_docstring(node, clean=False) == ast.get_docstring(original, clean=False)
        and isinstance(placeholder, ast.Expr) and isinstance(placeholder.value, ast.Constant)
        and placeholder.value.value is Ellipsis
    )


def _header(program_text: str, function: str) -> _Header:
    node = _documented_target(program_text, function)
    docstring = node.body[0]
    lines = program_text.split("\n")
    indent = lines[docstring.lineno - 1].encode("utf-8")[:docstring.col_offset]
    if indent.strip(b" \t"):
        _not_renderable(function, "does not open its docstring on a line of its own")
    first = min([node.lineno, *(decorator.lineno for decorator in node.decorator_list)])
    text = "\n".join(lines[first - 1:docstring.end_lineno]) + "\n"
    start = line_offsets(program_text)[first - 1]
    header = _Header(text, indent.decode("ascii"), start, start + len(text.encode("utf-8")))
    if not _is_stub_of(header.stub, function, node):
        _not_renderable(function, "does not end its docstring on a line of its own")
    return header


def docstring_stub(program_text: str, function: str) -> str:
    """The header followed by one ``...`` statement in the body's own indentation."""

    return _header(program_text, function).stub


def render_docstring_only(view: ProbeView) -> str:
    """Signature and docstring only; the model is asked for the complete module."""

    return DOCSTRING_ONLY_TEMPLATE.format(
        task=cv.DOCSTRING_ONLY_TASK, stub=docstring_stub(view.program_text, view.function),
        instructions=cv.DOCSTRING_ONLY_INSTRUCTIONS,
    )


def _renderers() -> dict[str, Callable[[ProbeView], str]]:
    """Each variant's renderer, read through the live module namespace (a test seam)."""

    return {
        cv.RECALL_VARIANT_NO_EVIDENCE: render_no_evidence,
        cv.RECALL_VARIANT_DOCSTRING_ONLY: render_docstring_only,
    }


def _shown_code(view: ProbeView, variant: Any) -> str | None:
    """The code block the variant shows: the broken module, or the stub cut from it."""

    if variant == cv.RECALL_VARIANT_NO_EVIDENCE:
        return view.program_text
    if variant == cv.RECALL_VARIANT_DOCSTRING_ONLY:
        return docstring_stub(view.program_text, view.function)
    return None


# --- rows and their leak check ----------------------------------------------------------------


def _identity(record: dict[str, Any]) -> dict[str, Any]:
    split_lineage = record["provenance"]["split_lineage"]
    return {
        "id": record["id"], "lineage_id": split_lineage["lineage_id"],
        "group_id": split_lineage["group_id"], "split": split_lineage["split"],
        "family": record["scenario"]["source"]["family"],
    }


def _restored_span_hidden(record: dict[str, Any], view: ProbeView, variant: str) -> bool:
    """The mutated span appears only as the mutant's replacement (``no_evidence``) or not at
    all (``docstring_only``: it lies in the elided body, outside the header)."""

    site = record["intervention"]["site"]
    start = int(site["start_byte"])
    replacement = str(site["replacement_text"]).encode("utf-8")
    end = start + len(replacement)
    if variant == cv.RECALL_VARIANT_NO_EVIDENCE:
        return view.program_text.encode("utf-8")[start:end] == replacement
    header = _header(view.program_text, view.function)
    return end <= header.start_byte or start >= header.end_byte


def _rendering_findings(view: ProbeView, variant: Any, prompt: str) -> list[str]:
    findings = []
    renderer = _renderers().get(variant) if isinstance(variant, str) else None
    shown = _shown_code(view, variant)
    if renderer is None or prompt != renderer(view):
        findings.append(cv.LEAK_PROMPT_NOT_RENDERED_FROM_PUBLIC_VIEW)
    if shown is None or f"```python\n{shown}```" not in prompt:
        findings.append(cv.LEAK_PROMPT_PROGRAM_NOT_BROKEN_TEXT)
    return findings


def _repair_shown(record: dict[str, Any], view: ProbeView, variant: Any, prompt: str) -> bool:
    if views.completion_of(record) in prompt:
        return True
    known = isinstance(variant, str) and variant in cv.RECALL_VARIANTS
    return known and not _restored_span_hidden(record, view, variant)


def prompt_findings(record: dict[str, Any], row: dict[str, Any]) -> list[str]:
    """Every declared leak code the probe row violates against its record."""

    findings = [] if set(row) == PROMPT_KEYS else [cv.LEAK_VIEW_EXTRA_KEYS]
    view, variant, prompt = probe_view(record), row.get("variant"), str(row.get("prompt", ""))
    findings += _rendering_findings(view, variant, prompt)
    if _repair_shown(record, view, variant, prompt):
        findings.append(cv.LEAK_PROMPT_CONTAINS_REPAIR)
    if contains_hidden_reasoning_key(row):
        findings.append(cv.LEAK_HIDDEN_REASONING_KEY)
    return findings


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
        findings = prompt_findings(record, row)
        cv.refuse_when(
            bool(findings), cv.FINDING_RECALL_PROMPT_LEAK,
            f"record {cv.shown(record['id'])} variant {row['variant']} fails the leak check: "
            + ", ".join(findings),
        )
    return rows


# --- the run ----------------------------------------------------------------------------------


@dataclass(frozen=True)
class _Run:
    candidates_sha256: str
    records: list[dict[str, Any]]
    rows: list[dict[str, Any]]

    @property
    def positives(self) -> int:
        return len(self.rows) // len(cv.RECALL_VARIANTS)

    def as_json(self) -> dict[str, Any]:
        return {
            "candidates_sha256": self.candidates_sha256, "records": len(self.records),
            "positives": self.positives,
        }


def _load_run(run_dir: Path) -> _Run:
    path = Path(run_dir) / generate.CANDIDATES_FILENAME
    cv.refuse_when(not path.is_file(), cv.FINDING_RUN_FILE_MISSING, f"{cv.shown(path)} is missing")
    data = path.read_bytes()
    records = load_candidate_records(data)
    rows = [row for record in records if views.is_positive(record) for row in prompt_rows(record)]
    cv.refuse_when(
        not rows, cv.FINDING_RECALL_NO_POSITIVE_RECORDS,
        "the run has no accepted, validated, eligible record to probe",
    )
    return _Run(hashlib.sha256(data).hexdigest(), records, rows)


def _check_destination(destination: Path) -> None:
    cv.refuse_first((
        (is_under_raw(destination), cv.FINDING_DESTINATION_UNDER_RAW,
         f"{cv.shown(str(destination))} names or aliases the raw tree"),
        (destination.exists(), cv.FINDING_DESTINATION_EXISTS,
         f"{cv.shown(str(destination))} already exists"),
    ))


def _file_entry(path: Path, data: bytes, rows: int) -> dict[str, Any]:
    return {"path": str(path), "sha256": hashlib.sha256(data).hexdigest(), "rows": rows}


# --- emit -------------------------------------------------------------------------------------


@dataclass(frozen=True)
class EmitRequest:
    run_dir: Path
    out_dir: Path


def emit(request: EmitRequest) -> dict[str, Any]:
    """Write ``prompts.jsonl`` for every positive record into a brand-new directory."""

    out_dir = Path(request.out_dir)
    _check_destination(out_dir)
    run = _load_run(request.run_dir)
    out_dir.mkdir(parents=True, exist_ok=False)
    prompts = out_dir / PROMPTS_FILENAME
    oc.write_jsonl(prompts, run.rows)
    return {
        "format": REPORT_FORMAT, "command": "emit", "family": cv.FAMILY,
        "limitation": cv.LIMITATION_POSSIBLE_UPSTREAM_CODE_RECALL, "run": run.as_json(),
        "prompts": _file_entry(prompts, prompts.read_bytes(), len(run.rows)),
        "per_variant": dict(sorted(Counter(row["variant"] for row in run.rows).items())),
    }


# --- score ------------------------------------------------------------------------------------


@dataclass(frozen=True)
class ScoreRequest:
    prompts_path: Path
    completions_path: Path
    run_dir: Path
    out_path: Path


@dataclass(frozen=True)
class _Input:
    """One input file, read once: its bytes are what is hashed and what is parsed."""

    path: Path
    data: bytes

    @classmethod
    def read(cls, path: Path, what: str) -> _Input:
        path = Path(path)
        cv.refuse_when(not path.is_file(), cv.FINDING_RECALL_INPUT_MISSING,
                       f"{what} file {cv.shown(str(path))} is missing")
        return cls(path, path.read_bytes())

    def lines(self):
        return oc.iter_jsonl_bytes(self.data)

    def entry(self, rows: int) -> dict[str, Any]:
        return _file_entry(self.path, self.data, rows)


@dataclass(frozen=True)
class _Target:
    """What one positive record is scored against; the repaired text itself is not kept."""

    repaired_sha256: str
    structure: str
    family: str


@dataclass
class _Bucket:
    prompts: int = 0
    completions: int = 0
    exact: int = 0
    structural: int = 0
    unparsable: int = 0

    def add(self, verdict: dict[str, bool]) -> None:
        self.completions += 1
        self.exact += int(verdict["exact"])
        self.structural += int(verdict["structural"])
        self.unparsable += int(verdict["unparsable"])

    def as_json(self) -> dict[str, Any]:
        def rate(count: int) -> float | None:
            return None if self.completions == 0 else round(count / self.completions, 4)

        return {
            "prompts": self.prompts, "completions": self.completions,
            "missing": self.prompts - self.completions, "exact": self.exact,
            "structural": self.structural, "unparsable": self.unparsable,
            "exact_rate": rate(self.exact), "structural_rate": rate(self.structural),
        }


@dataclass
class _Tally:
    per_variant: dict[str, _Bucket] = field(default_factory=dict)
    per_family: dict[str, dict[str, _Bucket]] = field(default_factory=dict)
    recalled: list[str] = field(default_factory=list)

    def buckets(self, family: str, variant: str) -> tuple[_Bucket, _Bucket]:
        by_variant = self.per_family.setdefault(family, {})
        return (self.per_variant.setdefault(variant, _Bucket()),
                by_variant.setdefault(variant, _Bucket()))

    def as_json(self) -> dict[str, Any]:
        return {
            "per_variant": {v: b.as_json() for v, b in sorted(self.per_variant.items())},
            "per_family": {
                family: {v: b.as_json() for v, b in sorted(buckets.items())}
                for family, buckets in sorted(self.per_family.items())
            },
            "docstring_only_exact_recall_ids": sorted(self.recalled),
        }


def _structure_digest(text: str) -> str | None:
    """The canonical AST digest, or None when the text is not a Python module (parse only)."""

    try:
        return lineage.structure_digest(text)
    except (SyntaxError, ValueError, RecursionError):
        return None


def score_completion(completion: str, repaired_sha256: str, structure: str) -> dict[str, bool]:
    """Exact (SHA-256 of the text) and structural (canonical AST) recall of the repair."""

    digest = _structure_digest(completion)
    return {
        "exact": cat.sha256_text(completion) == repaired_sha256,
        "structural": digest is not None and digest == structure,
        "unparsable": digest is None,
    }


def _targets(run: _Run) -> dict[str, _Target]:
    ids = {row["id"] for row in run.rows}
    return {
        record["id"]: _Target(
            record["result"]["repaired_sha256"],
            lineage.structure_digest(views.completion_of(record)),
            record["scenario"]["source"]["family"],
        )
        for record in run.records if record.get("id") in ids
    }


def _key(row: Any) -> tuple[str, str] | None:
    """``(id, variant)`` of a parsed line, or None unless both are strings."""

    if not isinstance(row, dict):
        return None
    key = (row.get("id"), row.get("variant"))
    return key if all(isinstance(part, str) for part in key) else None


def _bind_prompts(prompts: _Input, run: _Run) -> dict[tuple[str, str], dict[str, Any]]:
    """Every prompt row must be one the run re-renders byte for byte, once, and all of them."""

    expected = {(row["id"], row["variant"]): row for row in run.rows}
    seen: dict[tuple[str, str], dict[str, Any]] = {}
    where = prompts.path.name
    for lineno, row in prompts.lines():
        key = _key(row)
        cv.refuse_first((
            (key not in expected or expected[key] != row, cv.FINDING_RECALL_PROMPTS_MALFORMED,
             f"{where}:{lineno} is not a prompt the run re-renders"),
            (key in seen, cv.FINDING_RECALL_PROMPTS_MALFORMED,
             f"{where}:{lineno} repeats a prompt"),
        ))
        seen[key] = row
    cv.refuse_when(
        set(seen) != set(expected), cv.FINDING_RECALL_PROMPTS_MALFORMED,
        f"{where} does not carry both variants of every positive record of the run",
    )
    return seen


def _completion_row(where: str, lineno: int, row: Any) -> dict[str, str]:
    well_formed = (
        isinstance(row, dict) and set(row) == COMPLETION_KEYS
        and all(isinstance(value, str) for value in row.values())
    )
    cv.refuse_when(
        not well_formed, cv.FINDING_RECALL_COMPLETION_MALFORMED,
        f"{where}:{lineno} is not an object with exactly the string fields "
        f"{sorted(COMPLETION_KEYS)}",
    )
    return row


def _read_completions(
    completions: _Input, prompts: dict[tuple[str, str], dict[str, Any]]
) -> dict[tuple[str, str], str]:
    where = completions.path.name
    found: dict[tuple[str, str], str] = {}
    for lineno, parsed in completions.lines():
        row = _completion_row(where, lineno, parsed)
        key = (row["id"], row["variant"])
        cv.refuse_first((
            (key not in prompts, cv.FINDING_RECALL_COMPLETION_UNKNOWN,
             (f"{where}:{lineno} names no emitted prompt: id {cv.shown(row['id'])} "
              f"variant {cv.shown(row['variant'])}")),
            (key in found, cv.FINDING_RECALL_COMPLETION_DUPLICATE,
             f"{where}:{lineno} repeats id {cv.shown(row['id'])} variant {row['variant']}"),
        ))
        found[key] = row["completion"]
    cv.refuse_when(not found, cv.FINDING_RECALL_INPUT_MISSING,
                   f"completions file {cv.shown(str(completions.path))} carries no completion row")
    return found


def _tally(
    prompts: dict[tuple[str, str], dict[str, Any]], completions: dict[tuple[str, str], str],
    targets: dict[str, _Target],
) -> _Tally:
    tally = _Tally()
    for (_record_id, variant), row in prompts.items():
        for bucket in tally.buckets(row["family"], variant):
            bucket.prompts += 1
    for (record_id, variant), completion in sorted(completions.items()):
        target = targets[record_id]
        verdict = score_completion(completion, target.repaired_sha256, target.structure)
        for bucket in tally.buckets(target.family, variant):
            bucket.add(verdict)
        if verdict["exact"] and variant == cv.RECALL_VARIANT_DOCSTRING_ONLY:
            tally.recalled.append(record_id)
    return tally


def _write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "x", encoding="utf-8") as handle:
        handle.write(dumps_exact_json(report, ensure_ascii=True, indent=2, sort_keys=True) + "\n")


def score(request: ScoreRequest) -> dict[str, Any]:
    """Score completions produced elsewhere against the run's verified repairs; write the report
    to a brand-new file and return it. No completion is executed."""

    out_path = Path(request.out_path)
    _check_destination(out_path)
    run = _load_run(request.run_dir)
    prompts_input = _Input.read(request.prompts_path, "prompts")
    prompts = _bind_prompts(prompts_input, run)
    completions_input = _Input.read(request.completions_path, "completions")
    completions = _read_completions(completions_input, prompts)
    tally = _tally(prompts, completions, _targets(run))
    findings = [
        {"code": cv.RECALL_EXACT_UNDER_DOCSTRING_ONLY, "record_id": record_id,
         "family": prompts[(record_id, cv.RECALL_VARIANT_DOCSTRING_ONLY)]["family"]}
        for record_id in sorted(tally.recalled)
    ]
    report = {
        "format": REPORT_FORMAT, "command": "score", "family": cv.FAMILY,
        "limitation": cv.LIMITATION_POSSIBLE_UPSTREAM_CODE_RECALL, "scoring": SCORING,
        "run": run.as_json(),
        "inputs": {
            "prompts": prompts_input.entry(len(prompts)),
            "completions": completions_input.entry(len(completions)),
        },
        **tally.as_json(),
        "findings": findings, "status": "findings" if findings else "ok",
    }
    _write_report(out_path, report)
    return report


bind_import_twin(__name__)
