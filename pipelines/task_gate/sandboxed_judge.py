#!/usr/bin/env python3
"""The parent's half of a sandboxed run: open the child's records and judge each example.

The child only reports what each example produced (``_sandboxed_child.py``). Here every record
is opened with the run key, and each observation is compared with the expected output the
parent kept (``sandboxed_plan.py``), using ``doctest.OutputChecker`` and the example's own
option flags as ``DocTestRunner`` does. A report that is not exactly ``observed`` records
followed by one ``end`` or ``load_error`` record, every one sealed in order, is ``crashed``.
"""

from __future__ import annotations

import doctest
from typing import NamedTuple

from . import _sandboxed_record as record
from . import vocabulary as cv
from ._contract import bind_import_twin
from .harness import HarnessResult

__all__ = ["judged", "report_limit"]


class _Observation(NamedTuple):
    branch: str
    text: str
    cut: bool


def report_limit(examples: int) -> int:
    """The most report bytes a run of ``examples`` examples can honestly produce."""

    return (examples + 2) * record.RECORD_LIMIT


def _crashed(detail: str) -> HarnessResult:
    return HarnessResult(cv.OUTCOME_CRASHED, detail=detail)


def _bodies(report: bytes, key: bytes) -> list[object] | None:
    lines = report.split(b"\n")
    if lines[-1] != b"":  # every record ends with a newline
        return None
    bodies = [record.opened(key, line, seq) for seq, line in enumerate(lines[:-1])]
    return None if any(body is None for body in bodies) else bodies


def _kind(body: object) -> object:
    return body.get("kind") if isinstance(body, dict) else None


def _observation(body: object) -> _Observation | None:
    if _kind(body) != record.KIND_OBSERVED or set(body) != {"kind", "branch", "text", "cut"}:
        return None
    branch, text, cut = body["branch"], body["text"], body["cut"]
    shaped = branch in (record.BRANCH_OUTPUT, record.BRANCH_EXCEPTION)
    if not shaped or not isinstance(text, str) or not isinstance(cut, bool):
        return None
    return _Observation(branch, text, cut)


def _load_error_detail(body: object) -> str | None:
    if _kind(body) != record.KIND_LOAD_ERROR or not isinstance(body.get("detail"), str):
        return None
    return body["detail"]


def _ends_after(body: object, count: int) -> bool:
    if _kind(body) != record.KIND_END:
        return False
    recorded = body.get("count")
    return type(recorded) is int and recorded == count


def _flags(example: doctest.Example) -> int:
    """The option flags ``DocTestRunner`` applies to ``example`` when its base flags are 0."""

    flags = 0
    for flag, enabled in example.options.items():
        flags = flags | flag if enabled else flags & ~flag
    return flags


def _exception_name(message: str) -> str:
    """``doctest``'s IGNORE_EXCEPTION_DETAIL reduction: the bare exception name.

    Mirrors ``doctest._strip_exception_details``: the first line, up to the first colon, after
    the last dot.
    """

    newline = message.find("\n")
    end = newline if newline >= 0 else len(message)
    colon = message.find(":", 0, end)
    end = colon if colon >= 0 else end
    return message[message.rfind(".", 0, end) + 1:end]


def _exception_matches(example: doctest.Example, text: str, flags: int) -> bool:
    checker = doctest.OutputChecker()
    if example.exc_msg is None:  # an exception nobody expected
        return False
    if checker.check_output(example.exc_msg, text, flags):
        return True
    return bool(flags & doctest.IGNORE_EXCEPTION_DETAIL) and checker.check_output(
        _exception_name(example.exc_msg), _exception_name(text), flags,
    )


def _passes(example: doctest.Example, seen: _Observation) -> bool:
    if seen.cut:  # truncated output never matches
        return False
    flags = _flags(example)
    if seen.branch == record.BRANCH_OUTPUT:
        return doctest.OutputChecker().check_output(example.want, seen.text, flags)
    return _exception_matches(example, seen.text, flags)


def _verdict(examples: tuple[doctest.Example, ...], seen: list[_Observation]) -> HarnessResult:
    failed = sum(not _passes(example, item) for example, item in zip(examples, seen, strict=True))
    outcome = cv.OUTCOME_FAILED if failed else cv.OUTCOME_PASSED
    return HarnessResult(outcome, len(examples), failed)


def judged(examples: tuple[doctest.Example, ...], report: bytes, key: bytes) -> HarnessResult:
    """The verdict the sealed ``report`` stands for; anything malformed is ``crashed``."""

    bodies = _bodies(report, key)
    if bodies is None:
        return _crashed("report_seal")
    if not bodies:
        return _crashed("report_missing")
    *observed, terminal = bodies
    seen = [_observation(body) for body in observed]
    if any(item is None for item in seen) or len(seen) > len(examples):
        return _crashed("report_shape")
    detail = _load_error_detail(terminal)
    if detail is not None:
        return HarnessResult(cv.OUTCOME_LOAD_ERROR, detail=detail)
    if len(seen) != len(examples) or not _ends_after(terminal, len(seen)):
        return _crashed("report_shape")
    return _verdict(examples, seen)


bind_import_twin(__name__)
