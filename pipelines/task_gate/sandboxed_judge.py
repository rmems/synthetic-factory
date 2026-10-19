#!/usr/bin/env python3
"""The parent's half of a sandboxed run: open the child's records and judge each example.

The child only reports what each example produced (``_sandboxed_child.py``). Here every record
is opened with the run key, and each observation is compared with the expected output the
parent kept (``sandboxed_plan.py``), using ``doctest.OutputChecker`` and the example's own
option flags as ``DocTestRunner`` does. A report that is not exactly ``observed`` records
followed by one ``end`` or ``load_error`` record, every one sealed in order, is ``crashed``; so is
a run whose output outgrew the budget (``output_truncated``), since a prefix cannot be judged.
"""

from __future__ import annotations

import base64
import doctest
from typing import NamedTuple

from . import _sandboxed_record as record
from . import vocabulary as cv
from ._contract import bind_import_twin
from .checks import is_count
from .harness import HarnessResult

__all__ = ["judged", "report_limit"]


class _Observation(NamedTuple):
    branch: str
    text: str
    cut: bool


def report_limit(examples: int) -> int:
    """The most report bytes a run of ``examples`` examples can honestly produce."""

    return record.report_limit(examples)


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


_OBSERVATION_FIELDS = {"kind": str, "branch": str, "data": str, "cut": bool}
_BRANCHES = frozenset({record.BRANCH_OUTPUT, record.BRANCH_EXCEPTION})


def _text_of(data: str, cut: bool) -> str | None:
    """The recorded output as text; a cut prefix is never judged, so it is not decoded."""

    if cut:
        return ""
    try:
        return base64.b64decode(data.encode("ascii"), validate=True).decode("utf-8", "surrogatepass")
    except ValueError:  # binascii.Error and UnicodeError are both ValueErrors
        return None


def _observation(body: object) -> _Observation | None:
    if _kind(body) != record.KIND_OBSERVED or set(body) != set(_OBSERVATION_FIELDS):
        return None
    typed = all(isinstance(body[name], kind) for name, kind in _OBSERVATION_FIELDS.items())
    text = _text_of(body["data"], body["cut"]) if typed else None
    if text is None or body["branch"] not in _BRANCHES:
        return None
    return _Observation(body["branch"], text, body["cut"])


def _load_error_detail(body: object) -> str | None:
    if _kind(body) != record.KIND_LOAD_ERROR or not isinstance(body.get("detail"), str):
        return None
    return body["detail"]


def _ends_after(body: object, count: int) -> bool:
    if _kind(body) != record.KIND_END:
        return False
    recorded = body.get("count")
    return is_count(recorded) and recorded == count


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
    return _concluded(examples, seen, terminal)


def _concluded(
    examples: tuple[doctest.Example, ...], seen: list[_Observation], terminal: object,
) -> HarnessResult:
    """The result once the observations are well formed: what the terminal record says."""

    detail = _load_error_detail(terminal)
    if detail is not None:
        return HarnessResult(cv.OUTCOME_LOAD_ERROR, detail=detail)
    if len(seen) != len(examples) or not _ends_after(terminal, len(seen)):
        return _crashed("report_shape")
    if any(item.cut for item in seen):
        return _crashed("output_truncated")
    return _verdict(examples, seen)


bind_import_twin(__name__)
