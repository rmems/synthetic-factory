"""The task-verification gate: unverified mutation proposals in, verified tasks out (#496).

A proposal (procedural or model-backed) is one byte-span edit of a pinned program. The gate
keeps it only when it is denylist-clean, applies to exactly one span of the target function's
body, is new across every prior run, leaves the original passing its doctests and makes the
mutant fail at least one doctest in a scrubbed, time-boxed child interpreter. Every proposal
gets one verdict, so survival rate by reason is reportable.
"""

__all__ = (
    "_contract vocabulary denylist proposal mutation harness dedup_index gate report "
    "procedural runner cli"
).split()

from ._contract import bind_import_twin

bind_import_twin(__name__)
