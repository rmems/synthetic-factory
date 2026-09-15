"""Multi-Agent Ouroboros Swarm (prefix ``maos``).

AST-extracted catalog slices from recovered ``/tmp/maos-r*`` ``build_r*.py``
builders on ``origin/codex/recover-grok-01a06111`` (rank-1 r14–r16, rank-2
r19–r21). The family lives in this package as
``_contract``, ``catalog``, ``generate``, and ``cli``. Recovered mill
scripts are not vendored and are never executed. ``experiments/maos*`` is
absent on both named archives.
"""

from ._contract import bind_import_twin

__all__ = ("_contract catalog generate cli").split()

bind_import_twin(__name__)
