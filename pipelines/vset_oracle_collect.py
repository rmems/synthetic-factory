"""Compare source-counted oracle ids with unittest's own collection.

Collection imports the suite in this process with candidate modules stubbed,
so ``src/`` never runs. If unittest sees a different set of tests than the
source walk, the suite is not evidence.
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

if __package__:  # pragma: no cover - package-child import path
    from . import _assert_direct_sibling, _expose_package_sibling

    _assert_direct_sibling("vset_oracle_collect")
    from .vset_constants import ERR_ORACLE_EXECUTION_MISMATCH, VSetValidationError
else:
    getattr(sys.modules.get("pipelines"), "_join_package_sibling", lambda name: None)(
        "vset_oracle_collect"
    )
    from vset_constants import ERR_ORACLE_EXECUTION_MISMATCH, VSetValidationError


class _Stub:
    def __call__(self, *args: object, **kwargs: object) -> _Stub:
        return self

    def __mro_entries__(self, bases: tuple[object, ...]) -> tuple[type, ...]:
        # Collection must not import src/. Dropping the stub base lets
        # ``class Square(Base)`` finish so honest tests in the same module
        # still match the source walk. The real base is used when grading.
        return ()

    def __getattr__(self, name: str) -> _Stub:
        return _Stub()


class _StubLoader:
    def create_module(self, spec: importlib.machinery.ModuleSpec) -> None:
        return None

    def exec_module(self, module: object) -> None:
        def missing(name: str) -> _Stub:
            return _Stub()

        module.__getattr__ = missing  # type: ignore[attr-defined]


class _StubFinder:
    def __init__(self, local: set[str]) -> None:
        self._local = local
        self._loader = _StubLoader()

    def find_spec(
        self,
        fullname: str,
        path: object = None,
        target: object = None,
    ) -> importlib.machinery.ModuleSpec | None:
        root = fullname.split(".", 1)[0]
        if root in sys.stdlib_module_names:
            return None
        if root in self._local:
            return None
        return importlib.util.spec_from_loader(fullname, self._loader)


def _walk(suite: unittest.TestSuite, found: list[str]) -> None:
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            _walk(item, found)
            continue
        found.append(item.id())


def _load_ids(spec: dict[str, str], path: Path) -> set[str]:
    """Collect ids without writing ``.pyc`` under an import root."""

    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        return _imported_ids(spec, path)
    finally:
        sys.dont_write_bytecode = previous


def _imported_ids(spec: dict[str, str], path: Path) -> set[str]:
    module_spec = importlib.util.spec_from_file_location(spec["module"], path)
    if module_spec is None:
        raise VSetValidationError(
            ERR_ORACLE_EXECUTION_MISMATCH,
            f"test module {spec['relative']} failed to load: missing loader",
        )
    if module_spec.loader is None:
        raise VSetValidationError(
            ERR_ORACLE_EXECUTION_MISMATCH,
            f"test module {spec['relative']} failed to load: missing loader",
        )
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[spec["module"]] = module
    module_spec.loader.exec_module(module)
    found: list[str] = []
    _walk(unittest.defaultTestLoader.loadTestsFromModule(module), found)
    return set(found)


def _drop_new(before: set[str]) -> None:
    for name in list(sys.modules):
        if name not in before:
            sys.modules.pop(name, None)


def _restore_collection(folder: str, finder: _StubFinder, before: set[str]) -> None:
    if sys.path:
        if sys.path[0] == folder:
            del sys.path[0]
    if finder in sys.meta_path:
        sys.meta_path.remove(finder)
    _drop_new(before)


def _write_sources(sources: dict[str, str]) -> tempfile.TemporaryDirectory[str]:
    temp = tempfile.TemporaryDirectory(prefix="vset-collect-")
    root = Path(temp.name)
    for name, text in sources.items():
        (root / name).write_text(text, encoding="utf-8")
    return temp


def _collect(spec: dict[str, str], sources: dict[str, str]) -> set[str]:
    temp = _write_sources(sources)
    folder = temp.name
    before = set(sys.modules)
    finder = _StubFinder({Path(name).stem for name in sources})
    sys.meta_path.insert(0, finder)
    sys.path.insert(0, folder)
    try:
        return _load_ids(spec, Path(folder) / Path(spec["relative"]).name)
    except VSetValidationError:
        raise
    except Exception as exc:
        raise VSetValidationError(
            ERR_ORACLE_EXECUTION_MISMATCH,
            f"test module {spec['relative']} failed to load: {exc}",
        ) from exc
    finally:
        _restore_collection(folder, finder, before)
        temp.cleanup()


def _declared(spec: dict[str, str], expected: list[str]) -> set[str]:
    prefix = spec["module"] + "."
    return {item for item in expected if item.startswith(prefix)}


def require_match(
    spec: dict[str, str], expected: list[str], sources: dict[str, str]
) -> None:
    """Refuse a suite whose source walk and unittest collection disagree."""

    if _collect(spec, sources) == _declared(spec, expected):
        return
    raise VSetValidationError(
        ERR_ORACLE_EXECUTION_MISMATCH,
        f"oracle test ids do not match unittest collection for {spec['relative']}",
    )


if __package__:  # pragma: no cover - package-child import path
    _expose_package_sibling(__name__)
