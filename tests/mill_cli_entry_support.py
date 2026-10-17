"""In-process start-ups for the mill subpackage CLIs (``pipelines/<family>/cli.py``).

Each helper returns an entry that takes ``argv``, so it composes with
``cli_test_support.main_in_process`` and yields the exit code, stdout and
stderr a subprocess would see. They cover the three ways a mill CLI starts:
``main()`` reading ``sys.argv``, the file run as a script, and
``python3 -m <module>``. Each one undoes what that start-up leaves behind:
``sys.argv``, the ``sys.path`` entry a script prelude inserts, the family
package a script run imports afresh, and the import-twin alias a module run
as ``__main__`` registers.
"""

from __future__ import annotations

import runpy
import sys
import tempfile
import unittest
import warnings
from collections.abc import Callable, Iterator, Mapping
from contextlib import ExitStack, contextmanager
from pathlib import Path
from types import ModuleType
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
PIPELINES = REPO / "pipelines"

for _path in (REPO / "tests", PIPELINES):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from cli_test_support import main_in_process

Entry = Callable[[list[str]], object]

__all__ = [
    "PIPELINES",
    "REPO",
    "argv_main",
    "assert_usage_error",
    "main_in_process",
    "module_entry",
    "refusal_object",
    "scratch_dir",
    "script_entry",
    "write_files",
]


def argv_main(main: Callable[[], object]) -> Entry:
    """``main()`` as a console script calls it: arguments come from ``sys.argv``."""

    def entry(argv: list[str]) -> object:
        with mock.patch.object(sys, "argv", ["cli", *argv]):
            return main()

    return entry


def _family_modules(family: str) -> dict[str, ModuleType]:
    """Every loaded module of package ``family``, under its flat and ``pipelines.`` names."""

    packages = (family, f"pipelines.{family}")
    submodules = tuple(f"{package}." for package in packages)
    return {
        name: module
        for name, module in sys.modules.items()
        if name in packages or name.startswith(submodules)
    }


@contextmanager
def _family_unloaded(family: str) -> Iterator[None]:
    """Inside the block ``family`` is not imported; afterwards the same objects are back.

    The import twins rely on one object per module, so the copies a run
    imports are dropped and the originals restored, never re-imported.
    """

    saved = _family_modules(family)
    for name in saved:
        del sys.modules[name]
    try:
        yield
    finally:
        for name in _family_modules(family):
            del sys.modules[name]
        sys.modules.update(saved)


def script_entry(path: Path, *, pythonpath: tuple[Path, ...] = ()) -> Entry:
    """``PYTHONPATH=<pythonpath> python3 <path> ...``: ``__main__`` outside any package.

    The run sees what a fresh interpreter hands a script. ``sys.path`` is the
    script's own directory, then ``pythonpath``, with ``pipelines/`` only when
    it is listed there. The script's family package is not imported yet, so
    the prelude and every sibling import really run.
    """

    inherited = [item for item in sys.path if item != str(PIPELINES)]
    fresh_path = [str(path.parent), *map(str, pythonpath), *inherited]

    def entry(argv: list[str]) -> object:
        modules_before = sys.modules.copy()
        try:
            with ExitStack() as stack:
                stack.enter_context(mock.patch.object(sys, "argv", [str(path), *argv]))
                stack.enter_context(mock.patch.object(sys, "path", fresh_path.copy()))
                stack.enter_context(_family_unloaded(path.parent.name))
                return runpy.run_path(str(path), run_name="__main__")
        finally:
            for name, module in modules_before.items():
                sys.modules[name] = module
            for name in list(sys.modules):
                if name not in modules_before:
                    del sys.modules[name]

    return entry


def module_entry(module: ModuleType) -> Entry:
    """``python3 -m <module.__name__> ...``; ``sys.modules`` is restored afterwards.

    The module and its ``pipelines.`` twin share one object, and runpy only
    accepts the spelling that object was imported under first, so the run uses
    that spelling whichever order the test suite imported them in.
    """

    def entry(argv: list[str]) -> object:
        spelling = module.__name__
        with ExitStack() as stack:
            stack.enter_context(mock.patch.object(sys, "argv", [spelling, *argv]))
            stack.enter_context(mock.patch.dict(sys.modules))
            stack.enter_context(warnings.catch_warnings())
            # runpy warns that the module is already imported; re-running its
            # body is the point here, so the warning would only be noise.
            warnings.simplefilter("ignore", RuntimeWarning)
            return runpy.run_module(spelling, run_name="__main__")

    return entry


def assert_usage_error(
    case: unittest.TestCase, entry: Entry, argv: list[str], fragment: str
) -> None:
    """argparse refuses ``argv``: exit 2, nothing on stdout, ``fragment`` on stderr."""

    result = main_in_process(entry, argv)
    case.assertEqual((result.returncode, result.stdout), (2, ""))
    case.assertIn(fragment, result.stderr)


def refusal_object(command: str, code: str, message: str) -> dict[str, str]:
    """The ``--json`` refusal object the catalog-style mill CLIs print on stdout.

    Its ``message`` is the refusal's ``str()``, which repeats ``code`` as a prefix.
    """

    return {"code": code, "command": command, "message": f"{code}: {message}", "status": "refused"}


def scratch_dir(case: unittest.TestCase) -> Path:
    """A fresh, resolved temporary directory removed when ``case`` finishes."""

    holder = tempfile.TemporaryDirectory()
    case.addCleanup(holder.cleanup)
    return Path(holder.name).resolve()


def write_files(directory: Path, files: Mapping[str, str]) -> Path:
    """Create ``directory`` holding ``files`` (name -> text); return it."""

    directory.mkdir(parents=True)
    for name, text in files.items():
        (directory / name).write_text(text, encoding="utf-8")
    return directory
