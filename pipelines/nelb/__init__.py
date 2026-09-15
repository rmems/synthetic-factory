"""Neuromorphic event-language bridge (prefix ``nelb``).

AST-extracted plant identities from recovered Session-A builders on
``origin/codex/recover-grok-01a06111``, committed as compact JSONL beside
``CATALOG.json``. The family lives in this package as ``_contract``,
``catalog``, ``generate``, and ``cli``. Recovered mill scripts are not
vendored and are never executed.
"""

from ._contract import bind_import_twin

__all__ = ("_contract catalog generate cli").split()

bind_import_twin(__name__)
