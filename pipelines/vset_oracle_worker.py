"""Candidate worker program text.

A fresh interpreter runs this with ``python -c``. It lives outside the grader
module so that file stays small, and nothing under the worktree can replace it.
"""

from __future__ import annotations

import sys

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle_worker")
    from .vset_oracle_worker_io import WORKER_IO as _WORKER_IO
    from .vset_oracle_worker_ops import WORKER_OPS as _WORKER_OPS
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle_worker"
    )
    from vset_oracle_worker_io import WORKER_IO as _WORKER_IO
    from vset_oracle_worker_ops import WORKER_OPS as _WORKER_OPS

WORKER_SOURCE = _WORKER_IO + _WORKER_OPS


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
