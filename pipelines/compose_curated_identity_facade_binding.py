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


# One slot per module instance: the live facade it delegates to.
_BINDING: dict[str, ModuleType | None] = {"facade": None}


def bind_facade(facade: ModuleType) -> None:
    """Bind this module instance to its matching live compatibility facade."""

    _BINDING["facade"] = facade


def _facade() -> ModuleType:
    resolver: Callable[[str, Any], Any] | None = getattr(
        sys.modules.get("pipelines"), "_canonical_sibling_binding", None
    )
    if resolver is not None:
        _BINDING["facade"] = resolver("compose_curated", _BINDING["facade"])
    facade = _BINDING["facade"]
    if facade is None:
        raise RuntimeError("compose_curated facade is not bound")
    return facade


if __package__:
    _expose_package_sibling(__name__)
