#!/usr/bin/env python3
"""Tiny ACM plant-gen table used only as AST-extract input."""

from __future__ import annotations

SPEC = "https://spec.example/oas"

def P(a, b, field, old, new, code, f1, o1, f2, o2):
    return (a, b, field, old, new, code, f1, o1, f2, o2)


class _G:
    MILLS: dict = {}


g = _G()

MILLS = {
    2: [
        (
            "oas-type-boolean",
            "leftover-truthy-string",
            "type",
            "truthy leftover",
            "boolean strict",
            "400",
            f"{SPEC}#boolean",
            "boolean rejects leftover truthy strings.",
            f"{SPEC}#types",
            "Exclusive boolean.",
        ),
    ]
}
g.MILLS[3] = [
    P(
        "oas-host-required",
        "leftover-missing-host",
        "Host",
        "missing host leftover",
        "Host required",
        "400",
        f"{SPEC}#host",
        "Host is required.",
        f"{SPEC}#param",
        "Exclusive Host.",
    ),
]
