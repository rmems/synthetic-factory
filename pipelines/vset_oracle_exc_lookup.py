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


def _load_json() -> object:
    return importlib.import_module("json")


def _load_json_decoder() -> object:
    return importlib.import_module("json.decoder")


def _load_decimal() -> object:
    return importlib.import_module("decimal")


def _load_uuid() -> object:
    return importlib.import_module("uuid")


def _load_array() -> object:
    return importlib.import_module("array")


def _load_copyreg() -> object:
    return importlib.import_module("copyreg")


def _load_re() -> object:
    return importlib.import_module("re")


_LOADERS = {
    "json": _load_json,
    "json.decoder": _load_json_decoder,
    "decimal": _load_decimal,
    "uuid": _load_uuid,
    "array": _load_array,
    "copyreg": _load_copyreg,
    "re": _load_re,
}


def load_module(module_name: str) -> object | None:
    """Import one reviewed standard-library module, by a literal name."""

    loader = _LOADERS.get(module_name)
    if loader is None:
        return None
    try:
        return loader()
    except ImportError:
        return None


def _names(info: dict[str, object]) -> tuple[str, str] | None:
    module_name = info.get("module")
    qualname = info.get("qualname")
    if not isinstance(module_name, str):
        return None
    if not isinstance(qualname, str):
        return None
    return module_name, qualname


def _import_name(module_name: str, qualname: str) -> object | None:
    found = load_module(module_name)
    if found is None:
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
    if not isinstance(found, type):
        return None
    if not issubclass(found, Exception):
        return None
    return found


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
