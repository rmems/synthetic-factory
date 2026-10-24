"""A candidate must not plant a module on the parent's import path."""

from __future__ import annotations

import importlib._bootstrap_external as _bootstrap_external
import importlib.util
import json
import os
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

from vset_testutil import PIPELINES, vset  # noqa: E402

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


_PLANT_PACKAGE = textwrap.dedent(
    """\
    import os
    env = open("/proc/%s/environ" % os.getppid(), "rb").read().split(b"\\0")
    root = [item[4:].decode() for item in env if item.startswith(b"PWD=")][0]
    folder = os.path.join(root, "pipelines", "statistics")
    os.makedirs(folder, exist_ok=True)
    handle = open(os.path.join(folder, "__init__.py"), "w")
    handle.write("import unittest\\n")
    handle.write("unittest.TestCase.assertEqual = lambda *a, **k: None\\n")
    handle.close()
    def add(a, b):
        return 0
    def total(a, b):
        return a + b
    """
)


def _clear_plant() -> None:
    (PIPELINES / "statistics.py").unlink(missing_ok=True)
    package = PIPELINES / "statistics"
    (package / "__init__.py").unlink(missing_ok=True)
    cache = package / "__pycache__"
    if cache.is_dir():
        for path in cache.glob("*.pyc"):
            path.unlink(missing_ok=True)
        cache.rmdir()
    if package.is_dir():
        package.rmdir()
    cache = PIPELINES / "__pycache__"
    if not cache.is_dir():
        return
    for path in cache.glob("statistics*.pyc"):
        path.unlink(missing_ok=True)


def _grade_plant(source: str) -> dict[str, object]:
    # Fresh interpreter, fixed argv, no shell. A miss must not share this process.
    proc = subprocess.run(  # nosec B603  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit.dangerous-subprocess-use-audit
        [sys.executable, "-c", _PLANT_RUNNER, str(_TESTS), str(PIPELINES), source, _PLANT_TESTS],
        cwd=PIPELINES.parent,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if proc.returncode != 0:
        raise AssertionError(proc.stderr)
    return json.loads(proc.stdout.strip().splitlines()[-1])


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
                self.assertIsNone(pathguard._py_for_pyc(kept))
                self.assertFalse(pathguard._same_source(kept, seen))
                (cache / "kept.cpython-314.pyc").write_bytes(b"pyc")
                self.assertIsNotNone(pathguard._root_of(cache / "kept.cpython-314.pyc"))
                self.assertIsNone(pathguard._root_of(Path("/no/such/place.py")))
                self.assertIn("kept.cpython-314.pyc", pathguard.drift(seen))
                self.assertTrue(pathguard._changed(cache / "kept.cpython-314.pyc", seen))
                self.assertIsNone(pathguard._py_for_pyc(cache / "kept.py"))
                spec = pathguard.PathGuard(seen).find_spec("kept")
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self.assertEqual(module.x, 1)
                self.assertTrue(spec.has_location)
                self.assertTrue(module.__file__.endswith("kept.py"))
                self.assertTrue(pathguard._same_source(cache / "kept.cpython-314.pyc", seen))
                self.assertIsNone(pathguard.PathGuard(seen).find_spec("math"))
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
            pathguard._files(Path.cwd(), [], set())
        with mock.patch.object(Path, "stat", side_effect=OSError):
            pathguard._files(Path.cwd(), [], set())
        with tempfile.TemporaryDirectory() as tmp:
            unread = Path(tmp) / "kept.py"
            unread.write_text("x = 1\n", encoding="utf-8")
            with mock.patch.object(Path, "read_bytes", side_effect=OSError):
                self.assertIsNone(pathguard._stamp(unread))
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "kept.py"
            source.write_text("x = 1\n", encoding="utf-8")
            cached = source.parent / "__pycache__" / "kept.pyc"
            with mock.patch.object(Path, "resolve", side_effect=OSError):
                pathguard._note({}, source)
                self.assertFalse(pathguard._same_source(cached, {}))
                self.assertIsNone(pathguard._root_of(source))
                self.assertIsNone(pathguard._origin_path(str(source)))
                self.assertFalse(pathguard._changed(source, {}))
                self.assertFalse(pathguard._trusted(source, b"x", {}))
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

    def test_forged_pyc_body_is_not_executed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "census_mod.py"
            source.write_text("VALUE = 1\n", encoding="utf-8")
            sys.path.insert(0, tmp)
            try:
                seen = pathguard.snapshot()
                info = source.stat()
                code = compile("VALUE = 2\n", str(source), "exec")
                payload = _bootstrap_external._code_to_timestamp_pyc(
                    code, info.st_mtime, info.st_size
                )
                cached = Path(importlib.util.cache_from_source(str(source)))
                cached.parent.mkdir(exist_ok=True)
                cached.write_bytes(bytes(payload))
                self.assertTrue(pathguard._changed(cached, seen))
                self.assertIn(cached.name, pathguard.drift(seen))
                guard = pathguard.PathGuard(seen)
                sys.meta_path.insert(0, guard)
                try:
                    spec = importlib.util.find_spec("census_mod")
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    self.assertEqual(module.VALUE, 1)
                    self.assertFalse(pathguard._trusted(source, b"", seen))
                    self.assertFalse(pathguard._trusted(Path("not-in-seen.py"), b"x", seen))
                    source.write_text("VALUE = 3\n", encoding="utf-8")
                    with self.assertRaises(ImportError):
                        spec.loader.get_code("census_mod")
                finally:
                    if guard in sys.meta_path:
                        sys.meta_path.remove(guard)
                    sys.modules.pop("census_mod", None)
            finally:
                sys.path.remove(tmp)

    def test_fresh_stdlib_package_keeps_file_and_submodules(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pack = Path(tmp)
            (pack / "src").mkdir()
            (pack / "src" / "c.py").write_text(
                "def add(a, b):\n    return a + b\n", encoding="utf-8"
            )
            (pack / "tests").mkdir()
            (pack / "tests" / "helper.py").write_text(
                "import pathlib\nHERE = pathlib.Path(__file__).resolve().parent\n",
                encoding="utf-8",
            )
            (pack / "tests" / "use.py").write_text(
                "import unittest\nimport fractions\nimport helper\n"
                "class T(unittest.TestCase):\n"
                "    def test_xml(self):\n"
                "        import xml.etree.ElementTree as ET\n"
                "        self.assertEqual(ET.fromstring('<a/>').tag, 'a')\n"
                "        self.assertTrue(fractions.__file__.endswith('fractions.py'))\n"
                "        self.assertTrue(helper.HERE.is_dir())\n",
                encoding="utf-8",
            )
            saved = {}
            for name in list(sys.modules):
                if name == "fractions":
                    saved[name] = sys.modules.pop(name)
                elif name.startswith("xml"):
                    saved[name] = sys.modules.pop(name)
            try:
                report = vset.run_oracle(pack, reference_tests=["tests/use.py"])
            finally:
                sys.modules.update(saved)
        self.assertTrue(report["reference"]["ok"], report["reference"])

    def test_planted_import_path_cannot_force_a_pass(self) -> None:
        _clear_plant()
        try:
            payload = _grade_plant(_PLANT_SOURCE)
            self.assertFalse(payload["ok"], payload)
            self.assertNotEqual(payload["statuses"]["test_wrong"], "ok")
            self.assertEqual(payload["assert"], "assertEqual")
        finally:
            _clear_plant()

    def test_planted_package_cannot_force_a_pass(self) -> None:
        _clear_plant()
        try:
            payload = _grade_plant(_PLANT_PACKAGE)
            self.assertFalse(payload["ok"], payload)
            self.assertNotEqual(payload["statuses"]["test_wrong"], "ok")
            self.assertEqual(payload["assert"], "assertEqual")
        finally:
            _clear_plant()

    def test_same_length_rewrite_restoring_mtime_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            helper = root / "helper.py"
            helper.write_text("value = 1\n", encoding="utf-8")
            file_info = helper.stat()
            dir_info = root.stat()
            sys.path.insert(0, tmp)
            try:
                seen = pathguard.snapshot()
                helper.write_text("value = 2\n", encoding="utf-8")
                os.utime(helper, ns=(file_info.st_atime_ns, file_info.st_mtime_ns))
                os.utime(root, ns=(dir_info.st_atime_ns, dir_info.st_mtime_ns))
                rewritten = helper.stat()
                self.assertEqual(rewritten.st_size, file_info.st_size)
                self.assertEqual(rewritten.st_mtime_ns, file_info.st_mtime_ns)
                self.assertNotEqual(pathguard.drift(seen), "")
                with self.assertRaises(ImportError):
                    pathguard.PathGuard(seen).find_spec("helper")
            finally:
                sys.path.remove(tmp)

    def test_nested_package_plant_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "heldpkg"
            package.mkdir()
            init = package / "__init__.py"
            init.write_text("marker = 1\n", encoding="utf-8")
            (root / "loop").symlink_to(root, target_is_directory=True)
            (root / "broken").symlink_to(root / "missing-target")
            sys.path.insert(0, tmp)
            try:
                seen = pathguard.snapshot()
                self.assertEqual(pathguard.drift(seen), "")
                self.assertIsNotNone(pathguard._root_of(init))
                (package / "extra.py").write_text("marker = 2\n", encoding="utf-8")
                self.assertIn("extra.py", pathguard.drift(seen))
                with self.assertRaises(ImportError):
                    pathguard.PathGuard(seen).find_spec("heldpkg.extra", [str(package)])
            finally:
                sys.path.remove(tmp)
