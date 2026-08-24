"""Oracle-grounded neuromorphic dataset families (issue #77, epic #76).

The governing rule of this package is that a *generator* proposes scenarios,
interventions, and non-authoritative candidate predictions, and an *oracle*
produces the authoritative measurement. Generator-authored fields and
oracle-authored fields live in disjoint parts of the record envelope and the
split is enforced by ``record.validate_record``.

Nothing here invents a measurement. Every number under ``result.measured`` is
produced by an oracle adapter that actually ran.
"""

__all__ = [
    "canon",
    "families",
    "generators",
    "oracles",
    "record",
    "rng",
    "sim",
]
