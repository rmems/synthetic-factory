#!/usr/bin/env python3
"""Shared imports and module exposure for compose-run adapters."""

from __future__ import annotations

import sys

if __package__:
    from . import _expose_package_sibling
    from .compose_curated_run import (
        CLI_DESCRIPTION,
        ComposeCliServices,
        ComposeRunContext,
        ComposeRunHooks,
        ComposeRunServices,
        DestinationServices,
        ReportServices,
        SourceServices,
        compose_run,
    )
else:
    from compose_curated_run import (
        CLI_DESCRIPTION,
        ComposeCliServices,
        ComposeRunContext,
        ComposeRunHooks,
        ComposeRunServices,
        DestinationServices,
        ReportServices,
        SourceServices,
        compose_run,
    )

__all__ = (
    "CLI_DESCRIPTION",
    "ComposeCliServices",
    "ComposeRunContext",
    "ComposeRunHooks",
    "ComposeRunServices",
    "DestinationServices",
    "ReportServices",
    "SourceServices",
    "compose_run",
    "expose_run_adapter",
)


def expose_run_adapter(module_name: str) -> None:
    """Give package-loaded adapters their supported direct module coordinate."""

    package = sys.modules.get("pipelines")
    expose = getattr(package, "_expose_package_sibling", None)
    if expose is not None:
        expose(module_name)


if __package__:
    _expose_package_sibling(__name__)
