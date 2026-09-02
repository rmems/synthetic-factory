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


def _assert_direct_sibling(name: str) -> None:
    """Require any already-loaded direct-name twin of ``name`` to be this package's sibling.

    Every sibling module calls this from its package-mode prelude so the direct
    CLI copy (``import name``) and the package copy (``pipelines.name``) can never
    silently diverge into two module objects.
    """

    direct = _local_sibling_module(name, allow_initializing=True)
    if direct is not None:
        _require_local_sibling(direct, name)


def _canonical_sibling_binding(name: str, bound):
    """Prefer a fully initialized local module over an abandoned import object."""

    for module_key in (name, f"{__name__}.{name}"):
        candidate = _local_module(name, module_key)
        if candidate is not None:
            return candidate
    return bound


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


def _load_compose_curated_calibration():
    from . import compose_curated_calibration

    return compose_curated_calibration


def _load_compose_curated_calibration_lookup():
    from . import compose_curated_calibration_lookup

    return compose_curated_calibration_lookup


def _load_compose_contract():
    from . import compose_contract

    return compose_contract


def _load_compose_curated():
    from . import compose_curated

    return compose_curated


def _load_compose_curated_coding():
    from . import compose_curated_coding

    return compose_curated_coding


def _load_compose_curated_context():
    from . import compose_curated_context

    return compose_curated_context


def _load_compose_curated_identity():
    from . import compose_curated_identity

    return compose_curated_identity


def _load_compose_curated_identity_repairs():
    from . import compose_curated_identity_repairs

    return compose_curated_identity_repairs


def _load_compose_curated_identity_deferral():
    from . import compose_curated_identity_deferral

    return compose_curated_identity_deferral


def _load_compose_curated_identity_facade():
    from . import compose_curated_identity_facade

    return compose_curated_identity_facade


def _load_compose_curated_identity_facade_binding():
    from . import compose_curated_identity_facade_binding

    return compose_curated_identity_facade_binding


def _load_compose_curated_identity_facade_lanes():
    from . import compose_curated_identity_facade_lanes

    return compose_curated_identity_facade_lanes


def _load_compose_curated_identity_facade_semantics():
    from . import compose_curated_identity_facade_semantics

    return compose_curated_identity_facade_semantics


def _load_compose_curated_preferences():
    from . import compose_curated_preferences

    return compose_curated_preferences


def _load_compose_curated_record():
    from . import compose_curated_record

    return compose_curated_record


def _load_compose_curated_record_facade():
    from . import compose_curated_record_facade

    return compose_curated_record_facade


def _load_compose_curated_run():
    from . import compose_curated_run

    return compose_curated_run


def _load_compose_curated_run_context():
    from . import compose_curated_run_context

    return compose_curated_run_context


def _load_compose_curated_run_lines():
    from . import compose_curated_run_lines

    return compose_curated_run_lines


def _load_compose_curated_run_artifacts():
    from . import compose_curated_run_artifacts

    return compose_curated_run_artifacts


def _load_compose_curated_source():
    from . import compose_curated_source

    return compose_curated_source


def _load_compose_curated_source_pointers():
    from . import compose_curated_source_pointers

    return compose_curated_source_pointers


def _load_compose_curated_source_semantics():
    from . import compose_curated_source_semantics

    return compose_curated_source_semantics


def _load_compose_destination():
    from . import compose_destination

    return compose_destination


def _load_compose_destination_binding():
    from . import compose_destination_binding

    return compose_destination_binding


def _load_compose_destination_creation():
    from . import compose_destination_creation

    return compose_destination_creation


def _load_compose_destination_writer():
    from . import compose_destination_writer

    return compose_destination_writer


def _load_compose_destination_directory():
    from . import compose_destination_directory

    return compose_destination_directory


def _load_compose_destination_rename():
    from . import compose_destination_rename

    return compose_destination_rename


def _load_compose_destination_tree():
    from . import compose_destination_tree

    return compose_destination_tree


def _load_compose_source_snapshot():
    from . import compose_source_snapshot

    return compose_source_snapshot


def _load_compose_source_snapshot_members():
    from . import compose_source_snapshot_members

    return compose_source_snapshot_members


def _load_compose_source_snapshot_visibility():
    from . import compose_source_snapshot_visibility

    return compose_source_snapshot_visibility


def _load_compose_trajectory_gate():
    from . import compose_trajectory_gate

    return compose_trajectory_gate


def _load_compose_trajectory_goals():
    from . import compose_trajectory_goals

    return compose_trajectory_goals


def _load_export_compose_manifest():
    from . import export_compose_manifest

    return export_compose_manifest


def _load_export_curated():
    from . import export_curated

    return export_curated


def _load_export_destination():
    from . import export_destination

    return export_destination


def _load_export_members_auth():
    from . import export_members_auth

    return export_members_auth


def _load_export_members_jsonl():
    from . import export_members_jsonl

    return export_members_jsonl


def _load_export_members_path():
    from . import export_members_path

    return export_members_path


def _load_export_members_read():
    from . import export_members_read

    return export_members_read


def _load_export_members():
    from . import export_members

    return export_members


def _load_export_protocol():
    from . import export_protocol

    return export_protocol


def _load_export_provenance():
    from . import export_provenance

    return export_provenance


def _load_export_split():
    from . import export_split

    return export_split


def _load_export_viewer():
    from . import export_viewer

    return export_viewer


def _load_export_viewer_codec():
    from . import export_viewer_codec

    return export_viewer_codec


def _load_export_viewer_reader():
    from . import export_viewer_reader

    return export_viewer_reader


def _load_export_viewer_writer():
    from . import export_viewer_writer

    return export_viewer_writer


def _load_strict_jsonl():
    from . import strict_jsonl

    return strict_jsonl


def _load_training_audit_snapshot():
    from . import training_audit_snapshot

    return training_audit_snapshot


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
    "compose_contract": _load_compose_contract,
    "compose_curated": _load_compose_curated,
    "compose_curated_calibration": _load_compose_curated_calibration,
    "compose_curated_calibration_lookup": _load_compose_curated_calibration_lookup,
    "compose_curated_coding": _load_compose_curated_coding,
    "compose_curated_context": _load_compose_curated_context,
    "compose_curated_identity": _load_compose_curated_identity,
    "compose_curated_identity_repairs": _load_compose_curated_identity_repairs,
    "compose_curated_identity_deferral": _load_compose_curated_identity_deferral,
    "compose_curated_identity_facade": _load_compose_curated_identity_facade,
    "compose_curated_identity_facade_binding": _load_compose_curated_identity_facade_binding,
    "compose_curated_identity_facade_lanes": _load_compose_curated_identity_facade_lanes,
    "compose_curated_identity_facade_semantics": _load_compose_curated_identity_facade_semantics,
    "compose_curated_preferences": _load_compose_curated_preferences,
    "compose_curated_record": _load_compose_curated_record,
    "compose_curated_record_facade": _load_compose_curated_record_facade,
    "compose_curated_run": _load_compose_curated_run,
    "compose_curated_run_context": _load_compose_curated_run_context,
    "compose_curated_run_lines": _load_compose_curated_run_lines,
    "compose_curated_run_artifacts": _load_compose_curated_run_artifacts,
    "compose_curated_source": _load_compose_curated_source,
    "compose_curated_source_pointers": _load_compose_curated_source_pointers,
    "compose_curated_source_semantics": _load_compose_curated_source_semantics,
    "compose_destination": _load_compose_destination,
    "compose_destination_binding": _load_compose_destination_binding,
    "compose_destination_creation": _load_compose_destination_creation,
    "compose_destination_writer": _load_compose_destination_writer,
    "compose_destination_directory": _load_compose_destination_directory,
    "compose_destination_rename": _load_compose_destination_rename,
    "compose_destination_tree": _load_compose_destination_tree,
    "compose_source_snapshot": _load_compose_source_snapshot,
    "compose_source_snapshot_members": _load_compose_source_snapshot_members,
    "compose_source_snapshot_visibility": _load_compose_source_snapshot_visibility,
    "compose_trajectory_gate": _load_compose_trajectory_gate,
    "compose_trajectory_goals": _load_compose_trajectory_goals,
    "export_compose_manifest": _load_export_compose_manifest,
    "export_curated": _load_export_curated,
    "export_destination": _load_export_destination,
    "export_members_auth": _load_export_members_auth,
    "export_members_jsonl": _load_export_members_jsonl,
    "export_members_path": _load_export_members_path,
    "export_members_read": _load_export_members_read,
    "export_members": _load_export_members,
    "export_protocol": _load_export_protocol,
    "export_provenance": _load_export_provenance,
    "export_split": _load_export_split,
    "export_viewer": _load_export_viewer,
    "export_viewer_codec": _load_export_viewer_codec,
    "export_viewer_reader": _load_export_viewer_reader,
    "export_viewer_writer": _load_export_viewer_writer,
    "strict_jsonl": _load_strict_jsonl,
    "training_audit_snapshot": _load_training_audit_snapshot,
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
