#!/usr/bin/env python3
"""Live ``compose_curated`` facade binding shared by the identity adapters."""

from __future__ import annotations

import sys
from types import ModuleType
from typing import Any, Callable

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("compose_curated_identity_facade_binding")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "compose_curated_identity_facade_binding"
    )


_FACADE: ModuleType | None = None


def bind_facade(facade: ModuleType) -> None:
    """Bind this module instance to its matching live compatibility facade."""

    global _FACADE
    _FACADE = facade


def _facade() -> ModuleType:
    global _FACADE
    resolver: Callable[[str, Any], Any] | None = getattr(
        sys.modules.get("pipelines"), "_canonical_sibling_binding", None
    )
    if resolver is not None:
        _FACADE = resolver("compose_curated", _FACADE)
    if _FACADE is None:
        raise RuntimeError("compose_curated facade is not bound")
    return _FACADE


if __package__:
    _expose_package_sibling(__name__)
