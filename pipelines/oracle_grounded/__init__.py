"""Oracle-grounded neuromorphic dataset families (issue #77, epic #76).

The governing rule of this package is that a *generator* proposes scenarios,
interventions, and non-authoritative candidate predictions, and an *oracle*
produces the authoritative measurement. Generator-authored fields and
oracle-authored fields live in disjoint parts of the record envelope and the
split is enforced by ``record.validate_record``.

Nothing here invents a measurement. Every number under ``result.measured`` is
produced by an oracle adapter that actually ran.
"""

# Only the submodules that exist. The six names dropped here -- canon,
# families, generators, oracles, record, sim -- were the layout of an
# abandoned branch and were never modules on this package, so
# ``from ... import *`` raised AttributeError on the first of them.
# Sixteen real siblings (envelope, import_twins, the distill_* and fault_*
# families) stay undeclared: every consumer names them explicitly, and
# widening the star-import surface is a separate decision.
__all__ = [
    "refusals",
    "rng",
]
