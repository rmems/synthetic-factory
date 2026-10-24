"""Resolve a candidate exception to the real standard-library class.

Kept apart from ``vset_oracle_exc`` so that module stays under the complexity
gate. Only modules named by ``sys.stdlib_module_names`` are imported.
"""

from __future__ import annotations

import importlib
import sys

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle_exc_lookup")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle_exc_lookup"
    )


def _stdlib_module(module_name: object) -> bool:
    if not isinstance(module_name, str) or not module_name:
        return False
    return module_name.split(".", 1)[0] in sys.stdlib_module_names


def _names(info: dict[str, object]) -> tuple[str, str] | None:
    module_name = info.get("module")
    qualname = info.get("qualname")
    if isinstance(module_name, str) and isinstance(qualname, str):
        return module_name, qualname
    return None


def _import_name(module_name: str, qualname: str) -> object | None:
    if not _stdlib_module(module_name):
        return None
    try:
        found: object = importlib.import_module(module_name)
    except ImportError:
        return None
    for part in qualname.split("."):
        found = getattr(found, part, None)
        if found is None:
            return None
    return found


def stdlib_exception(info: dict[str, object]) -> type[Exception] | None:
    """Return the real exception class described by a child payload."""

    names = _names(info)
    if names is None:
        return None
    found = _import_name(names[0], names[1])
    if isinstance(found, type) and issubclass(found, Exception):
        return found
    return None


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
