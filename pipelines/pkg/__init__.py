"""Package-release mill family (prefix ``pkg``).

AST-extracted from ``experiments/pkg-mill-r163.py`` on
``origin/legacy-mill-lane``. The family lives in this package as
``_contract``, ``catalog``, ``generate``, and ``cli``. Mill scripts,
loop drivers, and the demoted r98–r162 digest/lock-yank twins are not
vendored and are never executed.
"""

from ._contract import bind_import_twin

__all__ = ("_contract catalog generate cli").split()

bind_import_twin(__name__)
