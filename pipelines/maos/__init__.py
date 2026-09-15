"""Multi-Agent Ouroboros Swarm (prefix ``maos``).

AST-extracted first slice from recovered ``/tmp/maos-r14``–``r16`` builders on
``origin/codex/recover-grok-01a06111``. The family lives in this package as
``_contract``, ``catalog``, ``generate``, and ``cli``. Recovered mill
scripts are not vendored and are never executed. ``experiments/maos*`` is
absent on both named archives.
"""

from ._contract import bind_import_twin

__all__ = ("_contract catalog generate cli").split()

bind_import_twin(__name__)
