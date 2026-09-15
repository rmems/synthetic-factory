"""Failure-as-fuel preference cascade (prefix ``ffpc``).

AST-extracted from recovered Session-A builders on
``origin/codex/recover-grok-01a06111``. The family lives in this package as
``_contract``, ``catalog``, ``generate``, and ``cli``. Recovered mill
scripts are not vendored and are never executed.
"""

from ._contract import bind_import_twin

__all__ = ("_contract catalog generate cli").split()

bind_import_twin(__name__)
