"""Python function repair: the first family of the software/code lane.

``synthetic-factory -> software/code datasets -> LLM training -> Agoge-Forger``.
A pinned catalog of small, permissively licensed Python programs with doctests
is mutated one operator at a time; a sandboxed harness executes the original,
the mutant and the mechanically restored program; a pure decision table turns
the execution rows into a verdict; and every candidate, accepted or rejected,
becomes an oracle-grounded envelope record (family ``python-function-repair``)
on the shared contract in :mod:`oracle_grounded`. The SFT view is a separate
projection of an explicit public allowlist, never of the record itself.

The lane shares only the contract modules with the neuromorphic families; it
adds no vocabulary to the envelope and re-implements none of its primitives.
"""

__all__ = [
    "_contract", "vocabulary", "catalog", "catalog_check", "catalog_build", "catalog_inputs",
    "lineage", "mutate", "mutate_span", "mutate_literals", "mutate_sites", "executor",
    "verify", "records", "views", "generate", "replay", "cli",
]
