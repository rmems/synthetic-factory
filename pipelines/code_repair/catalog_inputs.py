#!/usr/bin/env python3
"""Hidden inputs of a program: the literal doctest arguments and a seeded neighbourhood.

Policy ``doctest-literals+seeded-neighbourhood-v1``: every single-call doctest
example contributes its literal argument tuple; each argument is then varied
on its own (integers by one and around zero plus a few seeded draws, floats
by a half, strings by emptiness, reversal, doubling and case, sequences by
emptiness, prefix, reversal, sort, a duplicate and one seeded permutation).
The original program is executed on every candidate and only the cases it
answers with a value are kept, its repr pinned as the want. Deterministic for
a program id, so the builder's tests rebuild the fixture byte for byte.
"""

from __future__ import annotations

import ast
import hashlib
from typing import Any, NamedTuple

from . import catalog as cat
from . import executor as ex
from . import vocabulary as cv
from ._contract import bind_import_twin, rng

INPUT_POLICY = "doctest-literals+seeded-neighbourhood-v1"
NEIGHBOUR_DRAWS = 4

__all__ = [
    "INPUT_POLICY", "Subject", "candidate_args", "literal_args", "neighbours", "observed_cases",
]


class Subject(NamedTuple):
    """The program whose hidden cases are being observed."""

    text: str
    function: str
    program_id: str
    examples: tuple


def _single_call(source: str, function: str) -> ast.Call | None:
    """The one positional call of ``function`` the example source consists of, or None."""

    try:
        tree = ast.parse(source, mode="exec")
    except SyntaxError:
        return None
    if len(tree.body) != 1 or not isinstance(tree.body[0], ast.Expr):
        return None
    call = tree.body[0].value
    if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Name):
        return None
    return call if call.func.id == function and not call.keywords else None


def _unordered_literal(node: ast.AST) -> bool:
    if isinstance(node, ast.Call):
        return isinstance(node.func, ast.Name) and node.func.id == "set"
    return isinstance(node, ast.Set)


def literal_args(example: cat.Example, function: str) -> tuple | None:
    """The literal argument tuple of a single call example, or None."""

    call = _single_call(example.source, function)
    if call is None:
        return None
    if any(_unordered_literal(node) for arg in call.args for node in ast.walk(arg)):
        return None
    try:
        return tuple(ast.literal_eval(a) for a in call.args)
    except (ValueError, TypeError, SyntaxError):
        return None


def _sequence_neighbours(value: list | tuple, stream: rng.DrawStream) -> list:
    kind = type(value)
    out = [kind(), kind(value[:1]), kind(value[::-1])]
    try:
        out.append(kind(sorted(value)))
    except TypeError:
        pass
    out.append(kind(list(value) + list(value[:1])))
    if len(value) > 1:
        out.append(kind(stream.sample(list(value), len(value))))
    return out


def _int_neighbours(value: int, stream: rng.DrawStream) -> list:
    drawn = [stream.randint(-64, 64) for _ in range(NEIGHBOUR_DRAWS)]
    return [value - 1, value + 1, 0, 1, 2, -1] + drawn


# Checked in order: a bool is an int, so it comes first.
_NEIGHBOURHOODS = (
    (bool, lambda value, stream: [not value]),
    (int, _int_neighbours),
    (float, lambda value, stream: [0.0, 1.0, -1.0, value + 0.5, value - 0.5]),
    (str, lambda value, stream: ["", value[:1], value[::-1], value * 2, value.upper()]),
    ((list, tuple), _sequence_neighbours),
)


def neighbours(value: Any, stream: rng.DrawStream) -> list:
    """The seeded neighbourhood of one literal argument."""

    for kinds, variants in _NEIGHBOURHOODS:
        if isinstance(value, kinds):
            return variants(value, stream)
    return []


def candidate_args(
    examples: tuple[cat.Example, ...], function: str, stream: rng.DrawStream
) -> list:
    """Literal doctest inputs first, then one-argument variants of each, without repeats."""

    bases = [a for a in (literal_args(e, function) for e in examples) if a is not None]
    out: list[tuple] = []
    seen: set[str] = set()

    def add(args: tuple) -> None:
        key = repr(args)
        if key not in seen:
            seen.add(key)
            out.append(args)

    for base in bases:
        add(base)
    for base in bases:
        for position, value in enumerate(base):
            for variant in neighbours(value, stream):
                add(base[:position] + (variant,) + base[position + 1:])
    return out


def _stream_for(program_id: str) -> rng.DrawStream:
    return rng.DrawStream(int(hashlib.sha256(program_id.encode("utf-8")).hexdigest()[:8], 16))


def _probes(cases: list[dict]) -> tuple[dict, ...]:
    return tuple({"args": case["args"], "want": None} for case in cases)


def _observed_value(row: dict) -> bool:
    return row["status"] == cv.ROW_OBSERVED and not row.get("truncated")


def _stable_batch(executor: ex.Executor, subject: Subject, kept: list[dict], batch: list) -> list:
    probes = _probes(kept) + tuple({"args": repr(args), "want": None} for args in batch)
    first = _observe(executor, subject.text, subject.function, probes)
    second = _observe(executor, subject.text, subject.function, probes)
    paired = ((args, first.hidden[index], second.hidden[index])
              for index, args in enumerate(batch, len(kept)))
    return [{"args": repr(args), "want": row["got"]} for args, row, other in paired
            if _observed_value(row) and row == other]


def _retained_sequence_stable(executor: ex.Executor, subject: Subject, kept: list[dict]) -> bool:
    if not kept:
        return True
    final = _observe(executor, subject.text, subject.function, _probes(kept))
    return all(_observed_value(row) and row.get("got") == case["want"]
               for row, case in zip(final.hidden, kept))


def _observed_cases(executor: ex.Executor, subject: Subject) -> list[dict]:
    """The cases the original answers with a value, with its repr as the pinned want."""

    args_list = candidate_args(subject.examples, subject.function, _stream_for(subject.program_id))
    kept: list[dict] = []
    cursor = 0
    while cursor < len(args_list) and len(kept) < cv.MAX_HIDDEN_CASES:
        capacity = cv.MAX_HIDDEN_CASES - len(kept)
        batch = args_list[cursor:cursor + capacity]
        cursor += len(batch)
        kept.extend(_stable_batch(executor, subject, kept, batch))
    # Removing a failed probe must not change the state seen by a later input.
    return kept if _retained_sequence_stable(executor, subject, kept) else []


def _observe(executor: ex.Executor, text: str, function: str, probes: tuple) -> ex.PhaseReport:
    report = executor.run(ex.Job(f"observe:{function}", text, function, probes, True))
    cv.refuse_when(
        not report.ok, cv.FINDING_HARNESS_REPORT_MALFORMED,
        f"observing {function} failed: {report.detail}",
    )
    return report


def observe(executor: ex.Executor, subject: Subject) -> tuple[ex.PhaseReport | None, list[dict]]:
    reports = []

    class Capture:
        def run(self, job):
            report = executor.run(job)
            reports.append(report)
            return report

    try:
        cases = _observed_cases(Capture(), subject)
    except cv.RepairRefusal:
        if reports and not reports[-1].ok:
            return reports[-1], []
        raise
    return (reports[-1] if reports else None), cases


def observed_cases(executor: ex.Executor, subject: Subject) -> list[dict]:
    return _observed_cases(executor, subject)


bind_import_twin(__name__)
