#!/usr/bin/env python3
"""Bind the two import names of an ``oracle_grounded`` module to one object.

Every module in this package is importable as ``oracle_grounded.<name>`` (with
``pipelines/`` on ``sys.path``, the CLI convention) and as
``pipelines.oracle_grounded.<name>`` from the repository root. The envelope
(#172) arranges this for itself; the distillation contract and its siblings
call :func:`bind_import_twin` as their last statement, so whichever form loads
first serves both names -- a ``ContractError`` raised through one name is
caught through the other, and a digest computed by one is the digest the other
computes.
"""

from __future__ import annotations

import sys

_PACKAGE_PREFIX = "pipelines."


def import_twin_of(qualified_name: str) -> str:
    """The other supported import name of ``qualified_name``."""

    if qualified_name.startswith(_PACKAGE_PREFIX):
        return qualified_name[len(_PACKAGE_PREFIX) :]
    return f"{_PACKAGE_PREFIX}{qualified_name}"


def bind_import_twin(qualified_name: str) -> None:
    """Register the fully initialised module ``qualified_name`` under its twin.

    ``setdefault`` keeps an already-loaded twin in place, so the first form to
    finish importing is the one both names resolve to.
    """

    sys.modules.setdefault(import_twin_of(qualified_name), sys.modules[qualified_name])


bind_import_twin(__name__)
