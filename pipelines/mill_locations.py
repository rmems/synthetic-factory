#!/usr/bin/env python3
"""Attribute one on-disk path to the factory whose directory encloses it.

This is the destination side of mill detection, and the only place in the
mill modules that reasons about filesystem layout rather than payload
content. It answers "which factory directory is this record published in,
and did we establish that independently of the directory's own name?" --
the ``factory``/``factory_verified`` pair every ``MillIndex.add`` call needs.

Split out of ``mill_family.py`` verbatim; re-exported from ``mill_family`` so
existing ``from mill_family import factory_identity_for_path`` call sites
resolve unchanged.
"""

from __future__ import annotations

import sys
from collections.abc import Iterable
from pathlib import Path

if __package__:
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("mill_locations")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "mill_locations"
    )


def factory_identity_for_path(
    run_dir: Path,
    path: Path,
    *,
    marker_root: Path | None = None,
    known_factories: Iterable[str] = (),
) -> tuple[str, bool]:
    """Return one shared factory identity and independent verification flag.

    Marker-mode roots are verified directly. A known outer factory root is
    also verified, while off-registry direct roots and standalone files remain
    unverified. Multi-factory runs attribute nested archive/work paths to the
    first enclosing factory-shaped component.
    """

    run_dir = Path(run_dir)
    path = Path(path)
    if marker_root is not None:
        return Path(marker_root).name, True
    if run_dir.is_file():
        return path.parent.name, False

    factories = frozenset(known_factories)
    relative = path.relative_to(run_dir)
    if run_dir.name in factories:
        return run_dir.name, True
    if run_dir.name.endswith("-factory"):
        if len(relative.parts) == 1:
            return run_dir.name, False
        nested_root = relative.parts[0]
        if nested_root not in factories and not nested_root.endswith("-factory"):
            return run_dir.name, False
    factory = relative.parts[0] if len(relative.parts) > 1 else run_dir.name
    return factory, factory in factories


if __package__:
    _expose_package_sibling(__name__)
