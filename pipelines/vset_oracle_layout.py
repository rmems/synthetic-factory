"""Pristine suite bytes and the src names a round is allowed to import."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle_layout")
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle_layout"
    )


def restore_suite_dir(pack_dir: Path, work: Path, relative: str) -> None:
    """Recopy suite modules from the pack and drop files the pack does not have."""

    folder = Path(relative).parent
    source_dir = pack_dir / folder
    dest_dir = work / folder
    if not source_dir.is_dir():
        return
    dest_dir.mkdir(parents=True, exist_ok=True)
    keep = {path.name for path in source_dir.glob("*.py")}
    cache = dest_dir / "__pycache__"
    if cache.is_dir():
        shutil.rmtree(cache)
    for path in dest_dir.glob("*.py"):
        if path.name not in keep:
            path.unlink()
    for path in source_dir.glob("*.py"):
        shutil.copyfile(path, dest_dir / path.name)


def pack_sources(pack_dir: Path, folder: str) -> dict[str, str]:
    """Suite text from the pristine pack, never from the candidate worktree."""

    source_dir = pack_dir / folder
    found: dict[str, str] = {}
    if not source_dir.is_dir():
        return found
    for path in sorted(source_dir.glob("*.py")):
        found[path.name] = path.read_text(encoding="utf-8")
    return found


_FROZEN: dict[str, str] = {}


def freeze_pack(pack_dir: Path) -> None:
    """Remember pack text before any candidate process can rewrite it."""

    frozen: dict[str, str] = {}
    for path in pack_dir.rglob("*.py"):
        frozen[path.relative_to(pack_dir).as_posix()] = path.read_text(encoding="utf-8")
    _FROZEN.clear()
    _FROZEN.update(frozen)


def clear_pack() -> None:
    _FROZEN.clear()


def frozen_text(relative: str) -> str:
    if relative not in _FROZEN:
        raise KeyError(relative)
    return _FROZEN[relative]


def frozen_folder(folder: str) -> dict[str, str]:
    prefix = "" if folder in {"", "."} else folder.strip("/") + "/"
    found: dict[str, str] = {}
    for rel, text in _FROZEN.items():
        if not rel.startswith(prefix):
            continue
        name = rel[len(prefix):]
        if "/" in name:
            continue
        if not name.endswith(".py"):
            continue
        found[name] = text
    return found


def src_names(pack_dir: Path) -> frozenset[str]:
    folder = pack_dir / "src"
    names: set[str] = set()
    if not folder.is_dir():
        return frozenset()
    for path in folder.glob("*.py"):
        names.add(path.stem)
    for path in folder.iterdir():
        if not path.is_dir():
            continue
        init = path / "__init__.py"
        if not init.is_file():
            continue
        names.add(path.name)
    return frozenset(names)


def _drop_added_modules(folder: Path, keep: frozenset[str]) -> None:
    for path in folder.glob("*.py"):
        if path.stem not in keep:
            path.unlink()


def _drop_added_packages(folder: Path, keep: frozenset[str]) -> None:
    for path in list(folder.iterdir()):
        if not path.is_dir():
            continue
        if path.name in keep:
            continue
        init = path / "__init__.py"
        if not init.is_file():
            continue
        shutil.rmtree(path)


def drop_added_src(work: Path, keep: frozenset[str]) -> None:
    folder = work / "src"
    if not folder.is_dir():
        return
    _drop_added_modules(folder, keep)
    _drop_added_packages(folder, keep)


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
