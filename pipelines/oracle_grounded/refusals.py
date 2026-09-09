#!/usr/bin/env python3
"""Coded contract refusals shared by every family under the contract.

A family declares its finding codes as constants, collects them in a frozenset,
and subclasses :class:`CodedRefusal` with that set as ``CODES``; :func:`helpers`
then hands it the three refusal primitives bound to its type. ``str(exc)`` is
always ``"CODE: prose"``, the exception is a ``ContractError`` (so every
``except ContractError`` still catches it under both import spellings), and an
undeclared code is a programming error that raises ``LookupError`` instead.
Lifted from the fault-recovery family so the code-repair family does not carry
a second copy of the same forty lines.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any, NoReturn

from . import envelope
from .import_twins import bind_import_twin

__all__ = ["CodedRefusal", "code_of", "helpers", "shown"]


class CodedRefusal(envelope.ContractError):
    """A coded contract refusal; subclasses set ``CODES`` to their declared finding codes."""

    CODES: frozenset[str] = frozenset()

    def __init__(self, code: str, message: str) -> None:
        if code not in self.CODES:
            raise LookupError(f"undeclared finding code: {code!r}")
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


def helpers(
    refusal_type: type[CodedRefusal],
) -> tuple[
    Callable[[str, str], NoReturn],
    Callable[[bool, str, str], None],
    Callable[[Iterable[tuple[bool, str, str]]], None],
]:
    """``(refuse, refuse_when, refuse_first)`` bound to one refusal type."""

    def refuse(code: str, message: str) -> NoReturn:
        raise refusal_type(code, message)

    def refuse_when(holds: bool, code: str, message: str) -> None:
        """Raise the coded refusal when ``holds``; the single-check primitive."""
        if holds:
            raise refusal_type(code, message)

    def refuse_first(problems: Iterable[tuple[bool, str, str]]) -> None:
        """Raise for the first ``(holds, code, message)`` that holds; lazy over the iterable."""
        for holds, code, message in problems:
            refuse_when(holds, code, message)

    return refuse, refuse_when, refuse_first


def shown(value: Any) -> str:
    """``repr`` of a value, or its width when Python refuses to print it (an
    integer past the string-conversion limit, alone or inside a container), so
    a finding about an absurd value is still a coded refusal."""
    try:
        return repr(value)
    except ValueError:
        width = f" of {value.bit_length()} bits" if isinstance(value, int) else ""
        return f"an unprintable {type(value).__name__}{width}"


def code_of(text: Any, codes: frozenset[str]) -> str | None:
    """The declared code before the first ``": "`` of a finding string, or None."""
    head = str(text).split(": ", 1)[0]
    return head if head in codes else None


bind_import_twin(__name__)
