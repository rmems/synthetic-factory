#!/usr/bin/env python3
"""Tiny ACM pair catalog used only as AST-extract input."""

from __future__ import annotations

FACTORY_NAME = "api-contract-migration-factory"
GEN = "grok-4.6"
BANNED_SLUG_NEEDLES = ("w131", "422-vs-400")
BANNED_BLOB = ("thought", "scratch")
SPEC = "https://spec.example/oas"


def plant(**kw):
    return kw


def p(**kw):
    return plant(**kw)


PAIRS = [
    (
        p(
            slug="oas-info-title",
            domain="title-vs-missing",
            success=True,
            name="title",
            stack="OpenAPI + Go",
            field="title",
            old="missing title leftover",
            new="info title",
            fail_err="400: leftover missing title",
            plan="title-only",
            residual="drop after portal 4",
            vs="r0 missing title",
            fetch1=f"{SPEC}#info",
            fetch1_ok="title is required",
            fetch2=f"{SPEC}#fixed",
            fetch2_ok="exclusive title",
        ),
        p(
            slug="leftover-missing-title",
            domain="missing-vs-title",
            success=False,
            name="notitle",
            stack="OpenAPI + Java",
            field="info",
            old="info title",
            new="missing title leftover only",
            fail_err="400: leftover title",
            plan="missing-only",
            residual="handoff",
            vs="r0 title",
            fetch1=f"{SPEC}#fixed",
            fetch1_ok="missing is not title",
            fetch2=f"{SPEC}#info",
            fetch2_ok="exclusive missing",
        ),
    ),
]
