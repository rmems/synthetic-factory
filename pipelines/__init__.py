"""Standard-library command modules for the bounded synthetic-data factory.

The CLIs also support direct execution from ``pipelines/``.  Exact JSON is
therefore reachable through both ``exact_json`` and ``pipelines.exact_json``;
bind those names to one module so contractual decimal tokens retain one class
identity when callers mix the two supported import modes.
"""

from __future__ import annotations

import sys
from pathlib import Path


_package = sys.modules[__name__]
_package_dir = Path(__file__).resolve().parent


def _local_module(name: str, module_key: str, *, allow_initializing: bool = False):
    """Return a loaded module only when it resolves to this package's sibling."""

    candidate = sys.modules.get(module_key)
    origin = getattr(candidate, "__file__", None)
    if origin is None:
        return None
    initializing = getattr(getattr(candidate, "__spec__", None), "_initializing", False)
    if initializing and not allow_initializing:
        return None
    try:
        is_local = Path(origin).resolve() == (_package_dir / f"{name}.py").resolve()
    except OSError:
        return None
    return candidate if is_local else None


def _local_sibling_module(name: str, *, allow_initializing: bool = False):
    """Return a repository-local module loaded through its direct CLI name."""

    return _local_module(name, name, allow_initializing=allow_initializing)


def _require_local_sibling(module, name: str) -> None:
    """Require an imported direct-name module to be this package's sibling."""

    if _local_sibling_module(name, allow_initializing=True) is not module:
        raise ImportError(f"{name} did not resolve to the local pipeline sibling")


def _local_package_sibling(name: str, *, allow_initializing: bool = False):
    """Return a repository-local package child, optionally while it initializes."""

    return _local_module(
        name,
        f"{__name__}.{name}",
        allow_initializing=allow_initializing,
    )


def _load_exact_json_encoding():
    from . import exact_json_encoding

    return exact_json_encoding


def _load_exact_json():
    from . import exact_json

    return exact_json


def _load_curate_bridge_events():
    from . import curate_bridge_events

    return curate_bridge_events


def _load_curate_bridge_gate():
    from . import curate_bridge_gate

    return curate_bridge_gate


def _load_curate_bridge_materialize():
    from . import curate_bridge_materialize

    return curate_bridge_materialize


def _load_curate_bridge_materialize_fs():
    from . import curate_bridge_materialize_fs

    return curate_bridge_materialize_fs


def _load_curate_bridge_raster():
    from . import curate_bridge_raster

    return curate_bridge_raster


def _load_curate_bridge_raster_numbers():
    from . import curate_bridge_raster_numbers

    return curate_bridge_raster_numbers


def _load_validate_run_spikes():
    from . import validate_run_spikes

    return validate_run_spikes


def _load_validate_run_provenance():
    from . import validate_run_provenance

    return validate_run_provenance


def _load_validate_run():
    from . import validate_run

    return validate_run


def _load_curate_bridge():
    from . import curate_bridge

    return curate_bridge


_PACKAGE_SIBLING_LOADERS = {
    "exact_json_encoding": _load_exact_json_encoding,
    "exact_json": _load_exact_json,
    "curate_bridge_events": _load_curate_bridge_events,
    "curate_bridge_gate": _load_curate_bridge_gate,
    "curate_bridge_materialize": _load_curate_bridge_materialize,
    "curate_bridge_materialize_fs": _load_curate_bridge_materialize_fs,
    "curate_bridge_raster": _load_curate_bridge_raster,
    "curate_bridge_raster_numbers": _load_curate_bridge_raster_numbers,
    "validate_run_spikes": _load_validate_run_spikes,
    "validate_run_provenance": _load_validate_run_provenance,
    "validate_run": _load_validate_run,
    "curate_bridge": _load_curate_bridge,
}


def _join_package_sibling(name: str) -> None:
    """Join a local qualified import lock and return that module to direct callers."""

    if _local_package_sibling(name, allow_initializing=True) is None:
        return
    loader = _PACKAGE_SIBLING_LOADERS.get(name)
    if loader is None:
        return
    loader()
    candidate = _local_package_sibling(name)
    if candidate is not None:
        sys.modules[name] = candidate


def _alias_preloaded_direct_siblings() -> None:
    """Bind already-loaded local CLI modules into the package namespace."""

    for name, candidate in tuple(sys.modules.items()):
        if "." in name:
            continue
        if _local_sibling_module(name) is not candidate:
            continue
        if getattr(getattr(candidate, "__spec__", None), "_initializing", False):
            continue
        sys.modules.setdefault(f"{__name__}.{name}", candidate)
        setattr(sys.modules[__name__], name, candidate)


def _expose_package_sibling(qualified_name: str) -> None:
    """Expose one fully initialized local package child to direct CLI imports."""

    prefix = f"{__name__}."
    sibling_name = qualified_name.removeprefix(prefix)
    candidate = sys.modules.get(qualified_name)
    origin = getattr(candidate, "__file__", None)
    if not qualified_name.startswith(prefix):
        return
    if "." in sibling_name:
        return
    if origin is None:
        return
    try:
        is_local = Path(origin).resolve() == (_package_dir / f"{sibling_name}.py").resolve()
    except OSError:
        return
    if not is_local:
        return
    direct_candidate = _local_sibling_module(sibling_name)
    if direct_candidate is not None:
        sys.modules[qualified_name] = direct_candidate
    else:
        sys.modules.setdefault(sibling_name, candidate)


_alias_preloaded_direct_siblings()

_direct_encoding = _local_sibling_module("exact_json_encoding")
if _direct_encoding is None:
    _preloaded_encoding = _local_sibling_module(
        "exact_json_encoding",
        allow_initializing=True,
    )
    if _preloaded_encoding is not None:
        import exact_json_encoding as _direct_encoding

if _direct_encoding is not None:
    exact_json_encoding = _direct_encoding
    sys.modules[f"{__name__}.exact_json_encoding"] = exact_json_encoding
else:
    from . import exact_json_encoding as exact_json_encoding

    sys.modules.setdefault("exact_json_encoding", exact_json_encoding)

_direct_exact_json = _local_sibling_module("exact_json")
if _direct_exact_json is None:
    _preloaded_exact_json = _local_sibling_module(
        "exact_json",
        allow_initializing=True,
    )
    if _preloaded_exact_json is not None:
        import exact_json as _direct_exact_json

if _direct_exact_json is not None:
    exact_json = _direct_exact_json
    sys.modules[f"{__name__}.exact_json"] = exact_json
else:
    from . import exact_json as exact_json

    sys.modules.setdefault("exact_json", exact_json)

setattr(_package, "exact_json_encoding", exact_json_encoding)
setattr(_package, "exact_json", exact_json)

del _package
