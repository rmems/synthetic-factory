"""Choose src names the child may load.

The pristine pack is always routed. A name the patch adds is routed only
when the parent cannot already import it. A stem that is not an identifier,
or a lookup that raises, stays with the parent so one record cannot stop
the batch.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle_route")
    from .vset_oracle_layout import src_names
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle_route"
    )
    from vset_oracle_layout import src_names


class _Unreadable:
    origin = None


def routed_names(pack_dir: Path, work: Path) -> frozenset[str]:
    """Pack modules, plus patch-added names the parent cannot already import."""

    original = src_names(pack_dir)
    added = src_names(work) - original
    return original | _added_application_modules(added, work)


def _added_application_modules(names: frozenset[str], work: Path) -> frozenset[str]:
    kept: set[str] = set()
    for name in names:
        if not _importable_stem(name):
            continue
        if _parent_module(name, work):
            continue
        kept.add(name)
    return frozenset(kept)


def _importable_stem(name: str) -> bool:
    if "." in name:
        return False
    return name.isidentifier()


def _parent_module(name: str, work: Path) -> bool:
    if name in sys.stdlib_module_names:
        return True
    spec = _safe_spec(name)
    if spec is None:
        return False
    return _spec_is_outside(spec.origin, work)


def _safe_spec(name: str) -> object | None:
    try:
        return importlib.util.find_spec(name)
    except (ImportError, ValueError):
        return _Unreadable()


def _spec_is_outside(origin: object, work: Path) -> bool:
    located = _origin_path(origin)
    if located is None:
        return True
    return _outside_root(located, work.resolve())


def _origin_path(origin: object) -> Path | None:
    if not isinstance(origin, str):
        return None
    if origin in {"built-in", "frozen"}:
        return None
    return Path(origin).resolve()


def _outside_root(located: Path, root: Path) -> bool:
    if located == root:
        return False
    return root not in located.parents


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
