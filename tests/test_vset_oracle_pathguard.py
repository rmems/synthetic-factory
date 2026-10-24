"""A candidate must not plant a module on the parent's import path."""

from __future__ import annotations

import json
import subprocess  # nosec B404
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from vset_testutil import PIPELINES  # noqa: E402

import vset_oracle_pathguard as pathguard  # noqa: E402

if not PIPELINES.is_dir():
    raise RuntimeError("pipelines")


_PLANT_SOURCE = textwrap.dedent(
    """\
    import os
    env = open("/proc/%s/environ" % os.getppid(), "rb").read().split(b"\\0")
    root = [item[4:].decode() for item in env if item.startswith(b"PWD=")][0]
    handle = open(os.path.join(root, "pipelines", "statistics.py"), "w")
    handle.write("import unittest\\n")
    handle.write("unittest.TestCase.assertEqual = lambda *a, **k: None\\n")
    handle.close()
    def add(a, b):
        return 0
    def total(a, b):
        return a + b
    """
)

_PLANT_TESTS = textwrap.indent(
    textwrap.dedent(
        """\
        def test_wrong(self):
            import statistics
            self.assertEqual(c.add(1, 2), 3)
        def test_number(self):
            self.assertEqual(c.total(1, 2), 3)
        """
    ),
    "    ",
)

_PLANT_RUNNER = (
    "import json, sys\n"
    "sys.path.insert(0, sys.argv[1])\n"
    "sys.path.insert(0, sys.argv[2])\n"
    "from test_vset_oracle_inprocess_forges import _reference\n"
    "report, statuses = _reference(sys.argv[3], sys.argv[4])\n"
    "import unittest\n"
    "name = getattr(unittest.TestCase.assertEqual, '__name__', '')\n"
    "print(json.dumps({'ok': report['reference']['ok'], 'statuses': statuses, 'assert': name}))\n"
)


def _clear_plant() -> None:
    plant = PIPELINES / "statistics.py"
    plant.unlink(missing_ok=True)
    cache = PIPELINES / "__pycache__"
    if not cache.is_dir():
        return
    for path in cache.glob("statistics*.pyc"):
        path.unlink(missing_ok=True)


class PathGuardTests(unittest.TestCase):
    def test_new_module_is_refused_and_bytecode_of_old_source_is_not(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sys.path.insert(0, tmp)
            try:
                (root / "kept.py").write_text("x = 1\n", encoding="utf-8")
                cache = root / "__pycache__"
                cache.mkdir()
                (cache / "nested").mkdir()
                (cache / "note.txt").write_text("x", encoding="utf-8")
                seen = pathguard.snapshot()
                kept = (root / "kept.py").resolve()
                self.assertFalse(pathguard._changed(kept, seen))
                (cache / "kept.cpython-314.pyc").write_bytes(b"pyc")
                self.assertIsNotNone(pathguard._root_of(cache / "kept.cpython-314.pyc"))
                self.assertEqual(pathguard.drift(seen), "")
                self.assertIsNone(pathguard._py_for_pyc(cache / "kept.py"))
                self.assertIsNone(pathguard.PathGuard(seen).find_spec("kept"))
                (root / "kept.py").unlink()
                self.assertFalse(pathguard._same_source(cache / "kept.cpython-314.pyc", seen))
                planted = root / "planted_mod.py"
                planted.write_text("x = 1\n", encoding="utf-8")
                self.assertTrue(pathguard.drift(seen))
                guard = pathguard.PathGuard(seen)
                with self.assertRaises(ImportError):
                    guard.find_spec("planted_mod")
                self.assertFalse(pathguard._changed(Path("/no/such/kept.py"), seen))
                self.assertIsNotNone(pathguard._resolved(tmp))
                self.assertIsNotNone(pathguard._resolved(""))
            finally:
                sys.path.remove(tmp)

    def test_unreadable_paths_are_skipped(self) -> None:
        self.assertIsNone(pathguard._origin_path(None))
        self.assertIsNone(pathguard._origin_path("built-in"))
        self.assertIsNone(pathguard._origin_path("frozen"))
        pathguard._note({}, Path("missing-stamp.py"))
        with mock.patch.object(Path, "is_dir", side_effect=OSError):
            self.assertIsNone(pathguard._resolved(str(Path.cwd())))
        with mock.patch.object(Path, "stat", side_effect=OSError):
            self.assertIsNone(pathguard._stamp(Path.cwd()))
        with mock.patch.object(Path, "iterdir", side_effect=OSError):
            pathguard._files(Path.cwd(), [])
            pathguard._cache(Path.cwd(), [])
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "kept.py"
            source.write_text("x = 1\n", encoding="utf-8")
            cached = source.parent / "__pycache__" / "kept.pyc"
            with mock.patch.object(Path, "resolve", side_effect=OSError):
                pathguard._note({}, source)
                self.assertFalse(pathguard._same_source(cached, {}))
                self.assertIsNone(pathguard._root_of(source))
                self.assertIsNone(pathguard._origin_path(str(source)))
        spec = mock.Mock()
        spec.origin = None
        finder = "vset_oracle_pathguard.importlib.machinery.PathFinder.find_spec"
        guard = pathguard.PathGuard({})
        with mock.patch(finder, return_value=None):
            self.assertIsNone(guard.find_spec("missing-name"))
        with mock.patch(finder, return_value=spec):
            self.assertIsNone(guard.find_spec("missing-name"))

    def test_changed_file_without_a_stamp_is_not_a_second_hit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sys.path.insert(0, tmp)
            try:
                path = Path(tmp) / "gone.py"
                path.write_text("x = 1\n", encoding="utf-8")
                with mock.patch.object(Path, "stat", side_effect=OSError):
                    self.assertFalse(pathguard._changed(path, {}))
            finally:
                sys.path.remove(tmp)

    def test_planted_import_path_cannot_force_a_pass(self) -> None:
        _clear_plant()
        try:
            proc = subprocess.run(  # nosec B603
                [sys.executable, "-c", _PLANT_RUNNER, str(_TESTS), str(PIPELINES), _PLANT_SOURCE, _PLANT_TESTS],
                cwd=PIPELINES.parent,
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(proc.stdout.strip().splitlines()[-1])
            self.assertFalse(payload["ok"], payload)
            self.assertNotEqual(payload["statuses"]["test_wrong"], "ok")
            self.assertEqual(payload["assert"], "assertEqual")
        finally:
            _clear_plant()
