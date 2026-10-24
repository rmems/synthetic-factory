"""Stamp every code file under an import root.

A grade shares the grader's user, so a candidate can add a package or
rewrite a helper in place. ``os.utime`` can put the size and modification
time back. The stamp is the file's bytes, cached by ``st_ctime_ns``, which
that call cannot restore. The walk enters package directories.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle_pathsnap")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle_pathsnap"
    )


Stamp = tuple[int, int, str]
_CODE = frozenset({".py", ".pyc", ".so"})
_DIGESTS: dict[tuple[str, int, int, int], str] = {}


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


def _stat(path: Path):
    try:
        return path.stat()
    except OSError:
        return None


def _read_digest(path: Path) -> str | None:
    try:
        payload = path.read_bytes()
    except OSError:
        return None
    return hashlib.sha256(payload).hexdigest()


def _digest(path: Path, size: int, mtime_ns: int, ctime_ns: int) -> str | None:
    key = (str(path), size, mtime_ns, ctime_ns)
    cached = _DIGESTS.get(key)
    if cached is not None:
        return cached
    digest = _read_digest(path)
    if digest is not None:
        _DIGESTS[key] = digest
    return digest


def _stamp(path: Path) -> Stamp | None:
    info = _stat(path)
    if info is None:
        return None
    digest = _digest(path, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
    if digest is None:
        return None
    return info.st_size, info.st_ctime_ns, digest


def _keep(path: Path, found: list[Path]) -> None:
    if path.is_file():
        if path.suffix in _CODE:
            found.append(path)


def _descend(path: Path, found: list[Path], seen: set[tuple[int, int]]) -> None:
    if path.is_dir():
        _files(path, found, seen)
        return
    _keep(path, found)


def _files(root: Path, found: list[Path], seen: set[tuple[int, int]]) -> None:
    info = _stat(root)
    if info is None:
        return
    key = (info.st_dev, info.st_ino)
    if key in seen:
        return
    seen.add(key)
    try:
        entries = list(root.iterdir())
    except OSError:
        return
    for path in entries:
        _descend(path, found, seen)


def _note(found: dict[str, Stamp], path: Path) -> None:
    stamp = _stamp(path)
    if stamp is None:
        return
    try:
        found[str(path.resolve())] = stamp
    except OSError:
        return


def snapshot() -> dict[str, Stamp]:
    """Code files under every ``sys.path`` root, including package files."""

    found: dict[str, Stamp] = {}
    seen: set[tuple[int, int]] = set()
    for raw in sys.path:
        root = _resolved(raw)
        if root is None:
            continue
        paths: list[Path] = []
        _files(root, paths, seen)
        for path in paths:
            _note(found, path)
    return found


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
