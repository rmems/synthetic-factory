"""Fail-closed literal-bound imports for package/direct compatibility tests."""

from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

if __package__:
    from .pipeline_import_catalog_compose import (
        DIRECT_LOADERS as COMPOSE_DIRECT_LOADERS,
    )
    from .pipeline_import_catalog_compose import (
        PACKAGE_LOADERS as COMPOSE_PACKAGE_LOADERS,
    )
    from .pipeline_import_catalog_export import (
        DIRECT_LOADERS as EXPORT_DIRECT_LOADERS,
    )
    from .pipeline_import_catalog_export import (
        PACKAGE_LOADERS as EXPORT_PACKAGE_LOADERS,
    )
    from .pipeline_import_catalog_foundation import (
        DIRECT_LOADERS as FOUNDATION_DIRECT_LOADERS,
    )
    from .pipeline_import_catalog_foundation import (
        PACKAGE_LOADERS as FOUNDATION_PACKAGE_LOADERS,
    )
else:
    from pipeline_import_catalog_compose import DIRECT_LOADERS as COMPOSE_DIRECT_LOADERS
    from pipeline_import_catalog_compose import PACKAGE_LOADERS as COMPOSE_PACKAGE_LOADERS
    from pipeline_import_catalog_export import DIRECT_LOADERS as EXPORT_DIRECT_LOADERS
    from pipeline_import_catalog_export import PACKAGE_LOADERS as EXPORT_PACKAGE_LOADERS
    from pipeline_import_catalog_foundation import (
        DIRECT_LOADERS as FOUNDATION_DIRECT_LOADERS,
    )
    from pipeline_import_catalog_foundation import (
        PACKAGE_LOADERS as FOUNDATION_PACKAGE_LOADERS,
    )


DIRECT_LOADERS = {
    **COMPOSE_DIRECT_LOADERS,
    **EXPORT_DIRECT_LOADERS,
    **FOUNDATION_DIRECT_LOADERS,
}
PACKAGE_LOADERS = {
    **COMPOSE_PACKAGE_LOADERS,
    **EXPORT_PACKAGE_LOADERS,
    **FOUNDATION_PACKAGE_LOADERS,
}


def _load(catalog, name: str) -> ModuleType:
    try:
        loader = catalog[name]
    except KeyError as exc:
        raise ValueError(f"{name!r} is not in the pipeline import catalog") from exc
    return loader()


def load_direct(name: str) -> ModuleType:
    """Load one allowlisted pipeline module in direct-script mode."""

    return _load(DIRECT_LOADERS, name)


def load_package(name: str) -> ModuleType:
    """Load one allowlisted pipeline module through ``pipelines``."""

    return _load(PACKAGE_LOADERS, name)
