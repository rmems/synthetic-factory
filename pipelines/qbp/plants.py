#!/usr/bin/env python3
"""Reconstructed leftover ``_ok`` / ``_bad`` constructors for the qbp catalog.

These match ``qbp-plants-leftover3.py`` on ``legacy-mill-lane`` so hopper
replay sees the same plant fields the mills built. The mill scripts are never
imported or executed.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ._contract import bind_import_twin

OK_ARG_NAMES = (
    "slug",
    "goal",
    "plan",
    "mod",
    "test_fn",
    "bound_key",
    "bound_val",
    "timeout_key",
    "timeout_old",
    "timeout_new",
    "docs_url",
    "docs_ok",
    "docs_url2",
    "docs_ok2",
    "domain",
    "stack",
    "residual",
)
BAD_ARG_NAMES = (
    "slug",
    "goal",
    "plan",
    "mod",
    "test_fn",
    "timeout_key",
    "timeout_old",
    "timeout_new",
    "drop_key",
    "docs_url",
    "docs_ok",
    "docs_url2",
    "docs_ok2",
    "domain",
    "stack",
    "residual",
    "ticket",
    "ticket_why",
)
DEFAULT_EXTRA_FIX = {"ack": True}

__all__ = [
    "BAD_ARG_NAMES",
    "DEFAULT_EXTRA_FIX",
    "OK_ARG_NAMES",
    "_bad",
    "_ok",
    "_p",
    "expand_bad",
    "expand_ok",
]


def _p(**kwargs: Any) -> dict[str, Any]:
    """Identity plant constructor kept for hopper replay."""

    return dict(kwargs)


def _ok(row: Mapping[str, Any]) -> dict[str, Any]:
    slug = row["slug"]
    goal = row["goal"]
    plan = row["plan"]
    mod = row["mod"]
    test_fn = row["test_fn"]
    bound_key = row["bound_key"]
    bound_val = row["bound_val"]
    timeout_key = row["timeout_key"]
    timeout_old = row["timeout_old"]
    timeout_new = row["timeout_new"]
    extra = row.get("extra_fix") or DEFAULT_EXTRA_FIX
    extra_lit = repr(extra)
    return _p(
        slug=slug,
        goal=goal,
        plan=plan,
        mod=mod,
        test_fn=test_fn,
        src_body=f"def tune(lag):\n    return {{{timeout_key!r}: {timeout_old}}} if lag else {{}}\n",
        test_body=(
            f"def {test_fn}():\n"
            f"    t = tune(True)\n"
            f"    assert t.get({bound_key!r}) == {bound_val!r} and {timeout_key!r} not in t\n"
        ),
        grep_pat=f"{timeout_key}|{bound_key}|leftover",
        grep_hit=f"src/{mod}.py:2: return {{{timeout_key!r}: {timeout_old}}} if lag else {{}}",
        fail_msg=f"AssertionError: leftover stretched {timeout_key}; {bound_key} unbounded",
        first_old=f"    return {{{timeout_key!r}: {timeout_old}}} if lag else {{}}",
        first_new=f"    return {{{timeout_key!r}: {timeout_new}}} if lag else {{}}",
        first_obs=f"patched {timeout_new} (still a timeout integer)",
        still_msg=f"AssertionError: timeout integer cannot bind leftover {bound_key}",
        reread_obs=f"leftover is {bound_key}={bound_val}; timeout is not the leftover bound",
        plan_change=(
            f"{bound_key}={bound_val} plus leftover bind. {timeout_key} is not a leftover bound."
        ),
        fix_new=f"    return {{{bound_key!r}: {bound_val!r}, **{extra_lit}}} if lag else {{}}",
        fix_obs=f"patched {bound_key}={bound_val}",
        docs_url=row["docs_url"],
        docs_ok=row["docs_ok"],
        docs_url2=row["docs_url2"],
        docs_ok2=row["docs_ok2"],
        outcome=f"{bound_key} {bound_val} bound leftover. Timeout unused (success).",
        domain=row["domain"],
        stack=row["stack"],
        seed=slug,
        residual=row["residual"],
        coverage=86,
    )


def _bad(row: Mapping[str, Any]) -> dict[str, Any]:
    slug = row["slug"]
    mod = row["mod"]
    test_fn = row["test_fn"]
    timeout_key = row["timeout_key"]
    timeout_old = row["timeout_old"]
    timeout_new = row["timeout_new"]
    drop_key = row["drop_key"]
    ticket = row["ticket"]
    return _p(
        slug=slug,
        goal=row["goal"],
        plan=row["plan"],
        mod=row["mod"],
        test_fn=row["test_fn"],
        src_body=(
            f"def tune(blocked):\n    return {{{timeout_key!r}: {timeout_old}}} if blocked else {{}}\n"
        ),
        test_body=(f"def {test_fn}():\n    assert {timeout_key!r} not in tune(True)\n"),
        grep_pat=f"{timeout_key}|{drop_key}|leftover",
        grep_hit=(
            f"src/{mod}.py:2: return {{{timeout_key!r}: {timeout_old}}} if blocked else {{}}"
        ),
        fail_msg=(
            f"AssertionError: leftover slept {timeout_key}; drop {drop_key} is not a leftover bind"
        ),
        first_old=f"    return {{{timeout_key!r}: {timeout_old}}} if blocked else {{}}",
        first_new=f"    return {{{timeout_key!r}: {timeout_new}}} if blocked else {{}}",
        first_obs=f"patched {timeout_new}s (still a timeout integer)",
        still_msg=f"AssertionError: timeout cannot mint leftover; dropping {drop_key} is not a bind",
        reread_obs=f"dropping {drop_key} destroys leftover; bind leftover is platform",
        plan_change=f"{drop_key} drop is platform. Handoff {ticket}.",
        fix_new=f"    return {{'handoff': {ticket!r}}} if blocked else {{}}",
        fix_obs="ticket filed. still timeout-classed",
        docs_url=row["docs_url"],
        docs_ok=row["docs_ok"],
        docs_url2=row["docs_url2"],
        docs_ok2=row["docs_ok2"],
        outcome=f"Still timeout-classed; leftover drop {drop_key} is platform — handoff {ticket}.",
        domain=row["domain"],
        stack=row["stack"],
        seed=slug,
        residual=row["residual"],
        ticket=ticket,
        ticket_why=row["ticket_why"],
        coverage=84,
    )


def expand_ok(row: Mapping[str, Any]) -> dict[str, Any]:
    kwargs = {name: row[name] for name in OK_ARG_NAMES}
    if "extra_fix" in row:
        kwargs["extra_fix"] = row["extra_fix"]
    return _ok(kwargs)


def expand_bad(row: Mapping[str, Any]) -> dict[str, Any]:
    return _bad({name: row[name] for name in BAD_ARG_NAMES})


bind_import_twin(__name__)
