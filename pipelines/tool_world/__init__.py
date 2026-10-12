"""Tool-world families: tool-calling, MCP, browser, and delegation episodes.

``synthetic-factory -> tool-world families -> training-candidate episodes``.
One deterministic, stdlib-only environment executes every tool call a solver
proposes, so an observation is measured by the environment rather than
authored by the solver, success is a predicate over environment state, and a
record replays byte-for-byte from ``(pack, seed, actions)``. The design is
``docs/tool-world-families-design.md``; this package is its generator,
environment, and replay oracle. It writes candidate runs outside
``outputs/raw/`` and never publishes a round or claims training readiness.
Every module ends with ``bind_import_twin(__name__)`` so both import spellings
are one object.
"""

__all__ = [
    "_contract",
    "catalog",
    "cli",
    "env",
    "faults",
    "generate",
    "pack",
    "policies",
    "predicates",
    "records",
    "replay",
    "schema_lite",
    "surfaces",
    "vocabulary",
]

from ._contract import bind_import_twin

bind_import_twin(__name__)
