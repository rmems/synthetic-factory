#!/usr/bin/env python3
"""The one place the sandboxed gate harness reaches ``code_repair``'s isolation primitives.

Kept apart from ``_contract.py`` so that importing the task gate does not load ``code_repair``
(and its sealed source policy) unless a sandboxed harness is asked for. Both import forms work,
as in ``_contract.py``.
"""

from __future__ import annotations

if __name__.startswith("pipelines."):
    from ..code_repair import _sandbox as landlock
    from ..code_repair import harness_report, sandbox
    from ..code_repair.vocabulary import RepairRefusal
else:
    from code_repair import _sandbox as landlock
    from code_repair import harness_report, sandbox
    from code_repair.vocabulary import RepairRefusal

from ._contract import bind_import_twin

__all__ = ["RepairRefusal", "harness_report", "landlock", "sandbox"]

bind_import_twin(__name__)
