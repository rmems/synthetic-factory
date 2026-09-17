"""Oracle-grounded neuromorphic dataset families (issue #77, epic #76).

The governing rule of this package is that a *generator* proposes scenarios,
interventions, and non-authoritative candidate predictions, and an *oracle*
produces the authoritative measurement. Generator-authored fields and
oracle-authored fields live in disjoint parts of the record envelope and the
split is enforced by ``record.validate_record``.

Nothing here invents a measurement. Every number under ``result.measured`` is
produced by an oracle adapter that actually ran.
"""

# Only the submodules that exist. The six family modules -- canon,
# families, generators, oracles, record, sim -- landed with the
# oracle-grounded family stack and stay off the star surface by design:
# every consumer names them explicitly, and widening the star-import
# surface is a separate decision.
# Sixteen real siblings (envelope, import_twins, the distill_* and fault_*
# families) stay undeclared for the same reason.
__all__ = [
    "refusals",
    "rng",
]

from .import_twins import bind_import_twin

# The CLI name (``oracle_grounded``) and the package name
# (``pipelines.oracle_grounded``) stay one object. Declared submodules are
# not imported here, so a star import still loads them by name and an
# explicit sibling import is unchanged.
bind_import_twin(__name__)
