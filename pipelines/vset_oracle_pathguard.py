"""Fail closed when a grade changes a module the parent can import.

The worker is the same user as the grader. A candidate can write a new
``.py`` inside a package, or rewrite a helper and put its modification
time back. Snapshot every code file under ``sys.path`` before the suite
runs. A new bytecode file is harmless only when its source was already
there and did not change.
"""

from __future__ import annotations

import importlib.machinery
import sys
from pathlib import Path

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle_pathguard")
    from . import vset_oracle_pathsnap as pathsnap
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle_pathguard"
    )
    import vset_oracle_pathsnap as pathsnap


Stamp = pathsnap.Stamp
_resolved = pathsnap._resolved
_stamp = pathsnap._stamp
_files = pathsnap._files
_note = pathsnap._note
snapshot = pathsnap.snapshot


def _fresh(path: str, stamp: Stamp, seen: dict[str, Stamp]) -> bool:
    if path not in seen:
        return True
    return seen[path] != stamp


def _anchor(path: Path) -> Path | None:
    try:
        resolved = path.resolve()
    except OSError:
        return None
    parent = resolved.parent
    if parent.name == "__pycache__":
        return parent.parent
    return parent


def _parents(path: Path) -> list[Path]:
    anchor = _anchor(path)
    if anchor is None:
        return []
    return [anchor, *anchor.parents]


def _matching_root(parents: list[Path]) -> Path | None:
    for raw in sys.path:
        root = _resolved(raw)
        if root is None:
            continue
        if root in parents:
            return root
    return None


def _root_of(path: Path) -> Path | None:
    return _matching_root(_parents(path))


def _key(path: Path) -> str | None:
    try:
        return str(path.resolve())
    except OSError:
        return None


def _py_for_pyc(path: Path) -> Path | None:
    if path.parent.name != "__pycache__":
        return None
    if path.suffix != ".pyc":
        return None
    stem = path.name.split(".", 1)[0]
    return path.parent.parent / f"{stem}.py"


def _same_source(path: Path, seen: dict[str, Stamp]) -> bool:
    source = _py_for_pyc(path)
    if source is None:
        return False
    stamp = _stamp(source)
    if stamp is None:
        return False
    key = _key(source)
    if key is None:
        return False
    return seen.get(key) == stamp


def _changed(path: Path, seen: dict[str, Stamp]) -> bool:
    key = _key(path)
    if key is None:
        return False
    stamp = _stamp(path)
    if stamp is None:
        return False
    if not _fresh(key, stamp, seen):
        return False
    return not _same_source(path, seen)


def drift(seen: dict[str, Stamp]) -> str:
    """Return one changed path, or an empty string when the snapshot holds."""

    after = snapshot()
    for path, stamp in after.items():
        if not _fresh(path, stamp, seen):
            continue
        if _same_source(Path(path), seen):
            continue
        return path
    return ""


def _origin_path(origin: object) -> Path | None:
    if not isinstance(origin, str):
        return None
    if origin == "built-in":
        return None
    if origin == "frozen":
        return None
    try:
        return Path(origin).resolve()
    except OSError:
        return None


class PathGuard:
    """Reject an import whose file was not in the grade snapshot."""

    def __init__(self, seen: dict[str, Stamp]) -> None:
        self._seen = seen

    def find_spec(
        self,
        fullname: str,
        path: object = None,
        target: object = None,
    ) -> None:
        spec = importlib.machinery.PathFinder.find_spec(fullname, path)
        if spec is None:
            return None
        origin = _origin_path(spec.origin)
        if origin is None:
            return None
        if _changed(origin, self._seen):
            raise ImportError("oracle import path changed")
        return None


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
