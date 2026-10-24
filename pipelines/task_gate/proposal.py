#!/usr/bin/env python3
"""Programs and proposals as the gate sees them, and the strict JSONL row parser.

A :class:`GateProgram` is one pinned module text and the function whose doctests specify it
(the shape of ``code_repair.catalog.Program``). A :class:`GateProposal` is one span edit of
that module: ``program_id`` plus ``replacement_text`` and either an explicit byte span
(``start_byte``/``end_byte``, the procedural ``Site`` shape) or the ``original_text`` to be
found exactly once (the search/replace shape a model emits). Procedural and model-backed
proposals are the same type. ``source`` is recorded only when it is one of the accepted
labels (``unspecified``, ``model``, ``procedural``); any other self-declared value is
``unspecified``.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass

from . import vocabulary as cv
from .checks import is_identifier, is_int, is_text
from ._contract import (
    StrictJsonlError, bind_import_twin, load_strict_json, strict_lf_jsonl_lines,
)

__all__ = [
    "GateProgram", "GateProposal", "MalformedProposal", "accepted_source", "parse_proposals",
    "proposal_from_row", "row_source",
]

_TEXT_KEYS = ("proposal_id", "source", "original_text")
_ROW_KEYS = frozenset({
    "proposal_id", "program_id", "source", "original_text", "replacement_text", "start_byte",
    "end_byte",
})


def _unusable(program_id: object, reason: str) -> cv.GateRefusal:
    return cv.GateRefusal(cv.REFUSE_PROGRAM_INVALID, f"{program_id}: {reason}")


def _has_control_byte(text: str) -> bool:
    return "\r" in text or "\x00" in text


def _is_lf_text(text: object) -> bool:
    return is_text(text) and not _has_control_byte(text)


def _parsed(program: GateProgram) -> ast.Module:
    """The program's tree; refuses text that is not LF-only, too large or does not parse."""

    text = program.text
    if not _is_lf_text(text):
        raise _unusable(program.program_id, "text must be LF-only str")
    try:
        size = len(text.encode("utf-8"))
        tree = ast.parse(text)
    except (SyntaxError, ValueError, RecursionError) as exc:
        raise _unusable(program.program_id, f"does not parse: {exc}") from exc
    if size > cv.MAX_PROGRAM_BYTES:
        raise _unusable(program.program_id, "text is too large")
    return tree


def _target_count(tree: ast.Module, function: str) -> int:
    return sum(
        isinstance(node, ast.FunctionDef) and node.name == function for node in tree.body
    )


def _has_identity(program: GateProgram) -> bool:
    return is_identifier(program.program_id) and is_identifier(program.function)


@dataclass(frozen=True)
class GateProgram:
    """One module text and its target function; refused at construction when unusable."""

    program_id: str
    text: str
    function: str

    def __post_init__(self) -> None:
        if not _has_identity(self):
            raise _unusable(self.program_id, "program id/function not usable")
        tree = _parsed(self)
        if _target_count(tree, self.function) != 1:
            raise _unusable(
                self.program_id, f"needs exactly one module-level def {self.function!r}",
            )


def accepted_source(declared: object) -> str:
    """``declared`` when it is an accepted label, otherwise ``unspecified``.

    The procedural mutator passes ``procedural`` to the constructor. A decoded row
    may not: see ``row_source``.
    """

    if isinstance(declared, str) and declared in cv.ACCEPTED_SOURCES:
        return declared
    return cv.SOURCE_UNSPECIFIED


_ROW_SOURCES = frozenset({cv.SOURCE_UNSPECIFIED, cv.SOURCE_MODEL})


def row_source(declared: object) -> str:
    """The source a JSON row may claim: ``unspecified`` or ``model``.

    ``procedural`` is not a row label. Only ``procedural.proposals_from_plan`` sets it,
    on the constructor, so a model file cannot call its own rows procedural.
    """

    if isinstance(declared, str) and declared in _ROW_SOURCES:
        return declared
    return cv.SOURCE_UNSPECIFIED


def _has_offsets(start: object, end: object) -> bool:
    return start is not None and end is not None


@dataclass(frozen=True)
class GateProposal:
    """One unverified span edit. Exactly one of the two span forms must be present."""

    proposal_id: str
    program_id: str
    replacement_text: str
    source: str = cv.SOURCE_UNSPECIFIED
    original_text: str | None = None
    start_byte: int | None = None
    end_byte: int | None = None

    def __post_init__(self) -> None:
        source = accepted_source(self.source)
        if source != self.source:
            object.__setattr__(self, "source", source)
        if not (_has_offsets(self.start_byte, self.end_byte) or self.original_text):
            raise cv.GateRefusal(
                cv.REFUSE_PROPOSALS_INVALID,
                f"{self.proposal_id}: a span needs start_byte/end_byte or a non-empty original_text",
            )


@dataclass(frozen=True)
class MalformedProposal:
    """An input row that is not a proposal; it still gets a ``parse_error`` verdict row."""

    proposal_id: str
    program_id: str | None
    detail: str


def _unknown_keys(row: dict) -> bool:
    return not set(row) <= _ROW_KEYS


def _required_missing(row: dict) -> bool:
    return not is_identifier(row.get("program_id")) or not is_text(row.get("replacement_text"))


def _optional_not_text(row: dict) -> bool:
    return any(key in row and not is_text(row[key]) for key in _TEXT_KEYS)


def _offsets(row: dict) -> list[object]:
    return [row.get("start_byte"), row.get("end_byte")]


def _offsets_unpaired(row: dict) -> bool:
    given = [item is not None for item in _offsets(row)]
    return any(given) and not all(given)


def _offsets_not_int(row: dict) -> bool:
    offsets = _offsets(row)
    return all(item is not None for item in offsets) and not all(is_int(item) for item in offsets)


def _span_missing(row: dict) -> bool:
    return any(item is None for item in _offsets(row)) and not row.get("original_text")


_ROW_CHECKS = (
    (_unknown_keys, "unknown keys"),
    (_required_missing, "program_id and replacement_text are required strings"),
    (_optional_not_text, "proposal_id, source and original_text must be strings"),
    (_offsets_unpaired, "start_byte and end_byte come together"),
    (_offsets_not_int, "start_byte and end_byte must be integers"),
    (_span_missing, "a span needs start_byte/end_byte or a non-empty original_text"),
)


def _row_problem(row: dict) -> str | None:
    """Why a decoded row is not a proposal, or None when its shape is sound."""

    return next((reason for failed, reason in _ROW_CHECKS if failed(row)), None)


def proposal_from_row(row: object, fallback_id: str) -> GateProposal | MalformedProposal:
    """Decode one JSON object into a proposal, or say precisely why it is not one."""

    if not isinstance(row, dict):
        return MalformedProposal(fallback_id, None, cv.DETAIL_MALFORMED_ROW)
    problem = _row_problem(row)
    program_id = row.get("program_id") if is_identifier(row.get("program_id")) else None
    identity = row.get("proposal_id") if is_text(row.get("proposal_id")) else fallback_id
    if problem is not None:
        return MalformedProposal(str(identity), program_id, cv.DETAIL_MALFORMED_ROW)
    return GateProposal(
        proposal_id=str(identity), program_id=str(program_id),
        replacement_text=row["replacement_text"],
        source=row_source(row.get("source", cv.SOURCE_UNSPECIFIED)),
        original_text=row.get("original_text"), start_byte=row.get("start_byte"),
        end_byte=row.get("end_byte"),
    )


def parse_proposals(data: bytes, label: str) -> list[GateProposal | MalformedProposal]:
    """Strict JSONL in, one entry per line out. Framing faults refuse; a bad row is excluded."""

    if len(data) > cv.MAX_PROPOSALS_BYTES:
        raise cv.GateRefusal(cv.REFUSE_PROPOSALS_INVALID, f"{label}: too large")
    try:
        lines = strict_lf_jsonl_lines(data, label)
    except StrictJsonlError as exc:
        raise cv.GateRefusal(cv.REFUSE_PROPOSALS_INVALID, str(exc)) from exc
    parsed: list[GateProposal | MalformedProposal] = []
    for number, line in enumerate(lines, 1):
        fallback = f"line-{number:06d}"
        try:
            row = load_strict_json(line)
        except (ValueError, RecursionError):
            parsed.append(MalformedProposal(fallback, None, cv.DETAIL_MALFORMED_ROW))
            continue
        parsed.append(proposal_from_row(row, fallback))
    return parsed


bind_import_twin(__name__)
