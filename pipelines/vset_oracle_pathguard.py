"""Fail closed when a grade changes a module the parent can import.

The worker is the same user as the grader. A candidate can write a new
``.py`` or ``.pyc`` onto ``sys.path`` and the next parent import will run
it. Snapshot the code files before the suite runs, refuse a changed
top-level file, and treat a new bytecode file as harmless only when its
source was already there and did not change.
"""

from __future__ import annotations

import importlib.machinery
import sys
from pathlib import Path

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle_pathguard")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle_pathguard"
    )


_CODE = frozenset({".py", ".pyc", ".so"})


def _resolved(raw: str) -> Path | None:
    if raw:
        path = Path(raw)
    else:
        path = Path.cwd()
    try:
        if path.is_dir():
            return path.resolve()
    except OSError:
        return None
    return None


def _stamp(path: Path) -> tuple[int, int] | None:
    try:
        info = path.stat()
    except OSError:
        return None
    return info.st_size, info.st_mtime_ns


def _code(path: Path) -> bool:
    return path.suffix in _CODE


def _files(root: Path, found: list[Path]) -> None:
    try:
        entries = list(root.iterdir())
    except OSError:
        return
    for path in entries:
        if path.is_file():
            if _code(path):
                found.append(path)
            continue
        if path.name != "__pycache__":
            continue
        _cache(path, found)


def _cache(root: Path, found: list[Path]) -> None:
    try:
        entries = list(root.iterdir())
    except OSError:
        return
    for path in entries:
        if path.is_file():
            if _code(path):
                found.append(path)


def _note(found: dict[str, tuple[int, int]], path: Path) -> None:
    stamp = _stamp(path)
    if stamp is None:
        return
    try:
        found[str(path.resolve())] = stamp
    except OSError:
        return


def snapshot() -> dict[str, tuple[int, int]]:
    """Code files currently visible on ``sys.path``, including bytecode."""

    found: dict[str, tuple[int, int]] = {}
    for raw in sys.path:
        root = _resolved(raw)
        if root is None:
            continue
        paths: list[Path] = []
        _files(root, paths)
        for path in paths:
            _note(found, path)
    return found


def _py_for_pyc(path: Path) -> Path | None:
    if path.parent.name != "__pycache__":
        return None
    if path.suffix != ".pyc":
        return None
    stem = path.name.split(".", 1)[0]
    return path.parent.parent / f"{stem}.py"


def _same_source(path: Path, seen: dict[str, tuple[int, int]]) -> bool:
    source = _py_for_pyc(path)
    if source is None:
        return False
    stamp = _stamp(source)
    if stamp is None:
        return False
    try:
        key = str(source.resolve())
    except OSError:
        return False
    return seen.get(key) == stamp


def _fresh(path: str, stamp: tuple[int, int], seen: dict[str, tuple[int, int]]) -> bool:
    if path not in seen:
        return True
    return seen[path] != stamp


def _root_of(path: Path) -> Path | None:
    parent = path.parent
    if parent.name == "__pycache__":
        parent = parent.parent
    try:
        resolved = parent.resolve()
    except OSError:
        return None
    for raw in sys.path:
        root = _resolved(raw)
        if root == resolved:
            return root
    return None


def _changed(path: Path, seen: dict[str, tuple[int, int]]) -> bool:
    if _root_of(path) is None:
        return False
    stamp = _stamp(path)
    if stamp is None:
        return False
    if not _fresh(str(path), stamp, seen):
        return False
    return not _same_source(path, seen)


def drift(seen: dict[str, tuple[int, int]]) -> str:
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
    """Reject a top-level import whose file was not in the grade snapshot."""

    def __init__(self, seen: dict[str, tuple[int, int]]) -> None:
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
