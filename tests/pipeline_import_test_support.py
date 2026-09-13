"""Isolation helpers for package/direct pipeline import tests."""

from __future__ import annotations

import sys
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType
from typing import Iterator


REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"


def repository_pipeline_module(module: ModuleType) -> bool:
    """Return whether ``module`` originates in this repository's pipelines."""

    origin = getattr(module, "__file__", None)
    if origin is None:
        return False
    try:
        return Path(origin).resolve().is_relative_to(PIPELINES)
    except OSError:
        return False


def repository_pipeline_modules() -> dict[str, ModuleType]:
    """Snapshot every currently loaded repository pipeline module."""

    return {
        name: module
        for name, module in tuple(sys.modules.items())
        if repository_pipeline_module(module)
    }


def remove_modules(names) -> None:
    """Remove module aliases without assuming that every alias is loaded."""

    for name in names:
        sys.modules.pop(name, None)


@contextmanager
def clean_package_imports() -> Iterator[None]:
    """Run with pipeline modules unloaded and no direct pipeline path entry."""

    original_path = list(sys.path)
    saved = repository_pipeline_modules()
    remove_modules(saved)
    sys.path[:] = [entry for entry in sys.path if entry != str(PIPELINES)]
    try:
        yield
    finally:
        remove_modules(repository_pipeline_modules())
        sys.modules.update(saved)
        sys.path[:] = original_path


@contextmanager
def direct_pipeline_path() -> Iterator[None]:
    """Temporarily expose ``pipelines/`` for direct-script imports."""

    sys.path.insert(0, str(PIPELINES))
    try:
        yield
    finally:
        sys.path.remove(str(PIPELINES))


def _module_aliases(names: tuple[str, ...]) -> tuple[str, ...]:
    return ("pipelines",) + tuple(alias for name in names for alias in (name, f"pipelines.{name}"))


def _saved_package_attributes(
    package: ModuleType | None,
    names: tuple[str, ...],
) -> dict[str, ModuleType | None]:
    if package is None:
        return {}
    return {name: getattr(package, name, None) for name in names}


def _restore_package_attributes(
    package: ModuleType | None,
    attributes: dict[str, ModuleType | None],
) -> None:
    if package is None:
        return
    for name, original in attributes.items():
        if original is None:
            package.__dict__.pop(name, None)
        else:
            setattr(package, name, original)


@contextmanager
def isolated_pipeline_modules(names) -> Iterator[None]:
    """Remove selected direct/package aliases, then restore them exactly."""

    selected = tuple(names)
    aliases = _module_aliases(selected)
    saved = {name: sys.modules.pop(name, None) for name in aliases}
    original_package = saved["pipelines"]
    original_attributes = _saved_package_attributes(original_package, selected)
    try:
        yield
    finally:
        remove_modules(aliases)
        sys.modules.update({name: module for name, module in saved.items() if module is not None})
        _restore_package_attributes(original_package, original_attributes)
