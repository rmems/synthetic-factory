"""Honest-stop episodes: infrastructure for ``agent-honest-stop-episode``.

The slice is schema, a deterministic local tool world, a subprocess acceptance
gate, and a dry-run generator plan. It writes no dataset records and does not
call a model or the Hugging Face Hub. Callers import a sibling by name.
"""

from ._contract import bind_import_twin

bind_import_twin(__name__)
