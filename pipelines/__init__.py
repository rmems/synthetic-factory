"""Standard-library command modules for the bounded synthetic-data factory.

The CLIs also support direct execution from ``pipelines/``.  Exact JSON is
therefore reachable through both ``exact_json`` and ``pipelines.exact_json``;
bind those names to one module so contractual decimal tokens retain one class
identity when callers mix the two supported import modes.
"""

from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path


_package = sys.modules[__name__]
_package_dir = Path(__file__).resolve().parent


def _local_module(
    name: str,
    module_key: str,
    *,
    allow_initializing: bool = False,
    package_child: bool = False,
):
    """Return a loaded module only when it resolves to this package's own child.

    ``package_child`` selects a directory child (``<name>/__init__.py``) instead
    of a single-file sibling (``<name>.py``).
    """

    candidate = sys.modules.get(module_key)
    origin = getattr(candidate, "__file__", None)
    if origin is None:
        return None
    initializing = getattr(getattr(candidate, "__spec__", None), "_initializing", False)
    if initializing and not allow_initializing:
        return None
    relative = f"{name}/__init__.py" if package_child else f"{name}.py"
    try:
        is_local = Path(origin).resolve() == (_package_dir / relative).resolve()
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


# Package children that direct-mode CLIs also import by bare name. A sibling's
# prelude joins its own qualified import through ``_join_package_sibling`` so
# the direct copy and the package copy stay one module object; the load goes
# through importlib rather than ``from . import name`` so the import graph a
# static analyser sees carries no ``pipelines -> pipelines.<name>`` edge for it
# (pylint R0401 reads a function-body ``from . import`` as a module-level one).
_PACKAGE_SIBLING_NAMES = frozenset((
    "mill_script_inventory_schema",
    "mill_script_inventory_families",
    "mill_script_inventory_ignore",
    "mill_script_inventory_index",
    "mill_script_inventory_git",
    "mill_script_inventory",
    "exact_json_encoding",
    "exact_json",
    "curate_identity_output",
    "curate_identity_stages",
    "curate_bridge_events",
    "curate_bridge_gate",
    "curate_bridge_materialize",
    "curate_bridge_materialize_fs",
    "curate_bridge_raster",
    "curate_bridge_raster_numbers",
    "validate_run_spikes",
    "validate_run_provenance",
    "validate_run_rewards",
    "validate_run_reward_total",
    "validate_run_outcomes",
    "validate_run_thalamic",
    "validate_run_episode",
    "validate_run_episode_turns",
    "validate_run_multi_agent",
    "validate_run_multi_agent_roster",
    "validate_run_preference",
    "validate_run_preference_context",
    "validate_run_routes",
    "validate_run_cli",
    "compose_contract",
    "compose_curated",
    "compose_curated_calibration",
    "compose_curated_calibration_lookup",
    "compose_curated_coding",
    "compose_curated_context",
    "compose_curated_identity",
    "compose_curated_identity_repairs",
    "compose_curated_identity_deferral",
    "compose_curated_identity_facade",
    "compose_curated_identity_facade_binding",
    "compose_curated_identity_facade_lanes",
    "compose_curated_identity_facade_semantics",
    "compose_curated_preferences",
    "compose_curated_record",
    "compose_curated_record_facade",
    "compose_curated_run",
    "compose_curated_run_context",
    "compose_curated_run_lines",
    "compose_curated_run_artifacts",
    "compose_curated_source",
    "compose_curated_source_pointers",
    "compose_curated_source_semantics",
    "compose_destination",
    "compose_destination_binding",
    "compose_destination_creation",
    "compose_destination_writer",
    "compose_destination_directory",
    "compose_destination_rename",
    "compose_destination_tree",
    "compose_source_snapshot",
    "compose_source_snapshot_members",
    "compose_source_snapshot_visibility",
    "compose_trajectory_gate",
    "compose_trajectory_goals",
    "export_compose_manifest",
    "export_curated",
    "export_destination",
    "export_members_auth",
    "export_members_jsonl",
    "export_members_path",
    "export_members_read",
    "export_members",
    "export_protocol",
    "export_provenance",
    "export_split",
    "export_viewer",
    "export_viewer_codec",
    "export_viewer_reader",
    "export_viewer_writer",
    "strict_jsonl",
    "training_audit_record",
    "training_audit_reasoning",
    "training_audit_snapshot",
    "validate_run",
    "curate_bridge",
    "curate_gate",
    "curate_identity",
    "round_txn",
    "operator_paths",
    "curate_gate_contract",
    "curate_gate_digest",
    "curate_gate_paths",
    "curate_gate_plan",
    "curate_gate_merge",
    "curate_gate_lanes",
    "curate_gate_compose",
    "curate_gate_manifests",
    "curate_gate_evidence",
    "curate_gate_identity_gate",
    "curate_gate_evidence_verify",
    "curate_gate_bindings",
    "curate_gate_records",
    "curate_gate_identity_mapping",
    "curate_gate_review",
    "curate_gate_reward",
    "curate_gate_reward_sidecars",
    "curate_gate_gates",
    "curate_identity_json",
    "curate_identity_registry",
    "curate_identity_registry_fields",
    "curate_identity_registry_rows",
    "curate_gate_promotion",
    "round_txn_agentic",
    "round_txn_agentic_terms",
    "round_txn_agentic_types",
    "round_txn_agentic_cascade",
    "validate_run_safety",
    "reward_parse",
    "reward_parse_values",
    "reward_parse_patterns",
    "validate_run_episode",
    "validate_run_episode_turns",
    "validate_run_multi_agent",
    "validate_run_multi_agent_roster",
    "validate_run_preference",
    "validate_run_preference_context",
    "validate_run_routes",
    "validate_run_cli",
))


def _load_package_sibling(name: str):
    """Import ``pipelines.<name>`` through the import system's own machinery."""

    return importlib.import_module(f"{__name__}.{name}")


def _join_package_sibling(name: str) -> None:
    """Join a local qualified import lock and return that module to direct callers."""

    if _local_package_sibling(name, allow_initializing=True) is None:
        return
    if name not in _PACKAGE_SIBLING_NAMES:
        return
    _load_package_sibling(name)
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


def _alias_preloaded_package_children() -> None:
    """Bind already-loaded CLI-form package children into the package namespace.

    ``bind_import_twin`` registers ``pipelines.<child>`` in ``sys.modules`` when
    the CLI form (``import <child>`` with ``pipelines/`` on ``sys.path``) loads
    first, but CPython only sets the attribute on the parent package when it
    loads the child itself. A later ``import pipelines.<child>.<module>`` then
    finds the child already in ``sys.modules``, skips the load, and leaves
    ``pipelines.<child>`` unset, so the dotted attribute chain raises
    ``AttributeError``. This pass closes that gap without importing anything:
    the CLI entry points still never pull in the package.
    """

    for name, candidate in tuple(sys.modules.items()):
        if "." in name:
            continue
        if _local_module(name, name, package_child=True) is not candidate:
            continue
        qualified_name = f"{__name__}.{name}"
        sys.modules.setdefault(qualified_name, candidate)
        setattr(sys.modules[__name__], name, sys.modules[qualified_name])


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
        _bind_unloaded_direct_sibling(sibling_name, candidate)


def _bind_unloaded_direct_sibling(sibling_name: str, candidate: object) -> None:
    """Bind a package child under its direct CLI name when that name is free."""

    if isinstance(candidate, types.ModuleType):
        sys.modules.setdefault(sibling_name, candidate)


_alias_preloaded_direct_siblings()
_alias_preloaded_package_children()

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
