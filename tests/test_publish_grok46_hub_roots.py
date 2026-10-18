#!/usr/bin/env python3
"""Configurable Hub mirror and factory source roots for the Grok 4.6 publisher.

Each root resolves once per run: the CLI flag, then the environment, then the
publisher's module default. A configured root fails closed unless it already
exists as a real directory, and the Hub root is refused when it names or
aliases ``outputs/raw/`` or overlaps the factory source. The resolved roots
are active only inside ``main``'s run.
"""

import contextlib
import importlib.util
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"
sys.path.insert(0, str(SCRIPTS))

import publish_grok46_hub as publisher  # noqa: E402
import publish_hub_roots as hub_roots  # noqa: E402

HF_ENV = hub_roots.HF_ROOT_SETTING.env
FACTORY_ENV = hub_roots.FACTORY_ROOT_SETTING.env
RAW = "names or aliases outputs/raw/"
PUBLISHER_MODULES = ("publish_grok46_hub", "publish_hub_roots")


def publisher_defaults():
    """The publisher's module defaults, read now so a patched one is honoured."""
    return hub_roots.PublisherRoots(hf=publisher.HF_ROOT, factory=publisher.FACTORY_ROOT)


def resolve(hf_flag=None, factory_flag=None, environ=None):
    flags = {"hf_root": hf_flag, "factory_root": factory_flag}
    return hub_roots.resolve_publisher_roots(flags, environ or {}, publisher_defaults())


def temporary_root(test):
    """A fresh directory that is removed when ``test`` finishes."""
    temporary = tempfile.TemporaryDirectory()
    test.addCleanup(temporary.cleanup)
    return Path(temporary.name)


def make_directory(root, *parts):
    path = root.joinpath(*parts)
    path.mkdir(parents=True)
    return path


def assert_refused(test, message, **call):
    """Require ``resolve(**call)`` to refuse with ``message``; return the refusal."""
    with test.assertRaisesRegex(hub_roots.PublisherRootError, message) as caught:
        resolve(**call)
    return str(caught.exception)


def run_main(argv, **exported):
    """Run the publisher CLI; return its exit code and what it wrote to stderr."""
    stderr = io.StringIO()
    with mock.patch.object(sys, "argv", ["publish_grok46_hub.py", *argv]), (
        mock.patch.dict(os.environ, exported)
    ), contextlib.redirect_stderr(stderr):
        try:
            code = publisher.main()
        except SystemExit as exc:
            code = exc.code
    return code, stderr.getvalue()


class RootPrecedenceTests(unittest.TestCase):
    def setUp(self):
        self.root = temporary_root(self)

    def test_defaults_are_unchanged_without_flag_or_environment(self):
        self.assertEqual(publisher.HF_ROOT, Path("/home/raulmc/rmems/hf"))
        self.assertEqual(publisher.HF_DATASETS_DIRNAME, "grok-4.6")
        self.assertEqual(resolve(), publisher_defaults())
        self.assertEqual(
            publisher.hf_datasets_root(), Path("/home/raulmc/rmems/hf/grok-4.6")
        )

    def test_patched_defaults_still_steer_helpers_outside_a_run(self):
        hub = make_directory(self.root, "hf")
        source = make_directory(self.root, "raw")
        with mock.patch.object(publisher, "HF_ROOT", hub), mock.patch.object(
            publisher, "FACTORY_ROOT", source
        ):
            self.assertIsNone(hub_roots.current_roots())
            self.assertEqual(publisher.hf_datasets_root(), hub / "grok-4.6")
            self.assertEqual(resolve(), hub_roots.PublisherRoots(hf=hub, factory=source))

    def test_environment_overrides_the_default(self):
        hub = make_directory(self.root, "env-hf")
        source = make_directory(self.root, "env-raw")

        roots = resolve(environ={HF_ENV: str(hub), FACTORY_ENV: str(source)})

        self.assertEqual(roots, hub_roots.PublisherRoots(hf=hub, factory=source))

    def test_flag_overrides_the_environment(self):
        flag_hub = make_directory(self.root, "flag-hf")
        flag_source = make_directory(self.root, "flag-raw")
        environ = {
            HF_ENV: str(make_directory(self.root, "env-hf")),
            FACTORY_ENV: str(make_directory(self.root, "env-raw")),
        }

        roots = resolve(str(flag_hub), str(flag_source), environ)

        self.assertEqual(roots, hub_roots.PublisherRoots(hf=flag_hub, factory=flag_source))

    def test_flag_wins_even_when_the_environment_value_is_unusable(self):
        flag_hub = make_directory(self.root, "flag-hf")

        roots = resolve(str(flag_hub), environ={HF_ENV: str(self.root / "missing")})

        self.assertEqual(roots.hf, flag_hub)

    def test_each_root_resolves_independently(self):
        hub = make_directory(self.root, "flag-hf")
        source = make_directory(self.root, "env-raw")

        hub_only = resolve(str(hub))
        source_only = resolve(environ={FACTORY_ENV: str(source)})

        roots = hub_roots.PublisherRoots
        self.assertEqual(hub_only, roots(hf=hub, factory=publisher.FACTORY_ROOT))
        self.assertEqual(source_only, roots(hf=publisher.HF_ROOT, factory=source))

    def test_relative_configured_root_is_made_absolute(self):
        hub = make_directory(self.root, "hf")

        roots = resolve(os.path.relpath(hub))

        self.assertTrue(roots.hf.is_absolute())
        self.assertEqual(roots.hf, hub)

    def test_a_configured_factory_root_may_itself_be_a_raw_tree(self):
        # The factory root is the read-only source; only the Hub root is guarded.
        source = make_directory(self.root, "outputs", "raw", "2026-08-19-agentic")

        roots = resolve(str(make_directory(self.root, "hf")), str(source))

        self.assertEqual(roots.factory, source)


class ActiveRootsTests(unittest.TestCase):
    def setUp(self):
        self.root = temporary_root(self)

    def test_roots_are_active_only_inside_the_block(self):
        hub = make_directory(self.root, "hf")
        source = make_directory(self.root, "raw")
        roots = hub_roots.PublisherRoots(hf=hub, factory=source)

        with hub_roots.active_roots(roots) as active:
            self.assertIs(active, roots)
            self.assertIs(hub_roots.current_roots(), roots)
            self.assertEqual(publisher.hf_datasets_root(), hub / "grok-4.6")
            self.assertEqual(hub_roots.active_factory_root(Path("/unused")), source)

        self.assertIsNone(hub_roots.current_roots())
        self.assertEqual(hub_roots.active_hf_root(Path("/fallback")), Path("/fallback"))
        self.assertEqual(publisher.hf_datasets_root(), publisher.HF_ROOT / "grok-4.6")

    def test_roots_are_reset_when_the_run_raises(self):
        roots = hub_roots.PublisherRoots(hf=self.root, factory=self.root)
        with self.assertRaises(RuntimeError), hub_roots.active_roots(roots):
            raise RuntimeError("command failed")

        self.assertIsNone(hub_roots.current_roots())


class ConfiguredRootRefusalTests(unittest.TestCase):
    def setUp(self):
        self.root = temporary_root(self)

    def test_missing_root_is_refused_and_never_created(self):
        missing = self.root / "absent" / "root"
        cases = (
            ("--hf-root", {"hf_flag": str(missing)}),
            ("--factory-root", {"factory_flag": str(missing)}),
            (HF_ENV, {"environ": {HF_ENV: str(missing)}}),
            (FACTORY_ENV, {"environ": {FACTORY_ENV: str(missing)}}),
        )
        for source, call in cases:
            with self.subTest(source=source):
                message = assert_refused(self, "does not exist; create it first", **call)
                self.assertTrue(message.startswith(source), message)
                self.assertFalse(os.path.lexists(missing.parent))

    def test_root_that_is_a_file_is_refused(self):
        regular = self.root / "not-a-directory"
        regular.write_text("x\n", encoding="utf-8")

        assert_refused(self, "--hf-root does not name a directory", hf_flag=str(regular))
        assert_refused(
            self, f"{FACTORY_ENV} does not name a directory", environ={FACTORY_ENV: str(regular)}
        )

    def test_symlinked_root_is_refused(self):
        target = make_directory(self.root, "real-hf")
        link = self.root / "linked-hf"
        link.symlink_to(target, target_is_directory=True)

        assert_refused(self, "--hf-root names a symlink", hf_flag=str(link))
        assert_refused(self, f"{FACTORY_ENV} names a symlink", environ={FACTORY_ENV: str(link)})

    def test_dangling_symlink_root_is_refused(self):
        link = self.root / "dangling"
        link.symlink_to(self.root / "gone", target_is_directory=True)

        assert_refused(self, "names a symlink", hf_flag=str(link))
        self.assertFalse((self.root / "gone").exists())

    def test_empty_root_is_refused_not_read_as_a_default_or_the_working_directory(self):
        assert_refused(self, "--hf-root is set but empty", hf_flag="")
        assert_refused(self, "--factory-root is set but empty", factory_flag="")
        assert_refused(self, f"{HF_ENV} is set but empty", environ={HF_ENV: ""})
        assert_refused(self, f"{FACTORY_ENV} is set but empty", environ={FACTORY_ENV: ""})

    def test_whitespace_only_root_is_refused_as_empty(self):
        for blank in (" ", "\t", "  \n"):
            with self.subTest(blank=repr(blank)):
                assert_refused(self, "--hf-root is set but empty", hf_flag=blank)
                assert_refused(
                    self, f"{FACTORY_ENV} is set but empty", environ={FACTORY_ENV: blank}
                )

    def test_uninspectable_root_is_refused(self):
        hub = make_directory(self.root, "hf")
        with mock.patch.object(hub_roots.os, "lstat", side_effect=PermissionError("denied")):
            assert_refused(self, "--hf-root cannot be inspected", hf_flag=str(hub))

    def test_refusal_names_the_setting_but_never_the_configured_value(self):
        secret = self.root / "token-abc123-not-a-dir"

        message = assert_refused(self, "does not exist", environ={HF_ENV: str(secret)})

        self.assertIn(HF_ENV, message)
        self.assertNotIn("token-abc123", message)


class HubRootRawGuardTests(unittest.TestCase):
    def setUp(self):
        self.root = temporary_root(self)

    def assert_hub_refused(self, message, hub, source):
        hf_flag = None if hub is None else str(hub)
        assert_refused(self, message, hf_flag=hf_flag, factory_flag=str(source))

    def test_hub_root_naming_outputs_raw_is_refused(self):
        hub = make_directory(self.root, "outputs", "raw", "hf")

        self.assert_hub_refused(RAW, hub, make_directory(self.root, "src"))

    def test_hub_root_aliasing_outputs_raw_through_a_symlinked_parent_is_refused(self):
        raw = make_directory(self.root, "outputs", "raw")
        (raw / "hf").mkdir()
        alias = self.root / "alias"
        alias.symlink_to(raw, target_is_directory=True)

        # The leaf is a real directory; only its resolved path names the raw tree.
        self.assert_hub_refused(RAW, alias / "hf", make_directory(self.root, "src"))

    def test_hub_root_at_or_under_the_repository_raw_tree_is_refused(self):
        # The guard's raw root has no outputs/raw segments here, so only the
        # path identity check can catch it.
        guarded = make_directory(self.root, "immutable")
        (guarded / "hf").mkdir()
        source = make_directory(self.root, "src")
        with mock.patch.object(hub_roots.raw_tree_guard, "DEFAULT_RAW_OUTPUT_ROOT", guarded):
            for hub in (guarded, guarded / "hf"):
                with self.subTest(hub=hub.name):
                    self.assert_hub_refused(RAW, hub, source)

    def test_hub_root_inside_or_equal_to_the_factory_root_is_refused(self):
        source = make_directory(self.root, "src")
        nested = make_directory(self.root, "src", "hf")

        for hub in (nested, source):
            with self.subTest(hub=hub.name):
                self.assert_hub_refused(
                    "Hub mirror root lies inside the factory source root", hub, source
                )

    def test_hub_root_inside_the_factory_root_through_a_symlinked_parent_is_refused(self):
        # The Hub leaf is a real directory reached through a link into the
        # factory tree; only the resolved or identity check sees the overlap.
        source = make_directory(self.root, "src")
        make_directory(self.root, "src", "hf")
        link = self.root / "link"
        link.symlink_to(source, target_is_directory=True)

        self.assert_hub_refused(
            "Hub mirror root lies inside the factory source root", link / "hf", source
        )

    def test_factory_root_inside_the_hub_root_is_refused(self):
        hub = make_directory(self.root, "hf")
        source = make_directory(self.root, "hf", "grok-4.6", "src")

        self.assert_hub_refused(
            "factory source root lies inside the Hub mirror root", hub, source
        )

    def test_default_hub_root_gets_the_same_raw_guard(self):
        unsafe_default = self.root / "outputs" / "raw" / "hf"
        with mock.patch.object(publisher, "HF_ROOT", unsafe_default):
            self.assert_hub_refused(RAW, None, make_directory(self.root, "src"))
        self.assertFalse(unsafe_default.exists())


class DirectoryGuardTests(unittest.TestCase):
    def setUp(self):
        self.root = temporary_root(self)

    def test_safe_factory_root_returns_a_real_active_root(self):
        source = make_directory(self.root, "raw")
        roots = hub_roots.PublisherRoots(hf=self.root / "hf", factory=source)
        with hub_roots.active_roots(roots):
            self.assertEqual(hub_roots.safe_factory_root(Path("/unused")), source)

    def test_safe_factory_root_refuses_a_missing_or_symlinked_root(self):
        link = self.root / "link"
        link.symlink_to(make_directory(self.root, "raw"), target_is_directory=True)
        for unsafe in (self.root / "missing", link):
            with self.subTest(root=unsafe.name), self.assertRaisesRegex(
                SystemExit, "unsafe factory root"
            ):
                hub_roots.safe_factory_root(unsafe)

    def test_real_directory_creates_or_accepts_a_real_directory(self):
        nested = self.root / "a" / "b"
        hub_roots.real_directory(nested, parents=True)
        hub_roots.real_directory(nested)

        self.assertTrue(nested.is_dir())

    def test_real_directory_refuses_a_symlink_dangling_link_or_file(self):
        linked = self.root / "linked"
        linked.symlink_to(make_directory(self.root, "target"), target_is_directory=True)
        dangling = self.root / "dangling"
        dangling.symlink_to(self.root / "gone", target_is_directory=True)
        regular = self.root / "file"
        regular.write_text("x\n", encoding="utf-8")
        for unsafe in (linked, dangling, regular):
            with self.subTest(entry=unsafe.name), self.assertRaisesRegex(
                SystemExit, "unsafe snapshot directory"
            ):
                hub_roots.real_directory(unsafe)
        self.assertFalse((self.root / "gone").exists())

    def test_real_directory_checks_what_a_concurrent_writer_left(self):
        # mkdir loses the race: another writer creates the entry first. A real
        # directory is accepted; a symlink planted in that window is refused.
        target = make_directory(self.root, "target")

        def racer_makes(entry):
            def mkdir(path, *_args, **_kwargs):
                entry(path)
                raise FileExistsError(path)
            return mkdir

        real = self.root / "real"
        with mock.patch.object(Path, "mkdir", autospec=True, side_effect=racer_makes(os.mkdir)):
            hub_roots.real_directory(real)
        self.assertTrue(real.is_dir())

        planted = self.root / "planted"
        plant = racer_makes(lambda path: path.symlink_to(target, target_is_directory=True))
        with mock.patch.object(Path, "mkdir", autospec=True, side_effect=plant), (
            self.assertRaisesRegex(SystemExit, "unsafe snapshot directory")
        ):
            hub_roots.real_directory(planted)


class SiblingImportTests(unittest.TestCase):
    """The publisher reaches its roots sibling without the implicit script dir."""

    def test_publisher_and_tests_share_one_roots_module(self):
        # One module object means one ContextVar: roots a test activates are
        # the roots the publisher's helpers read.
        self.assertIs(sys.modules["publish_hub_roots"], hub_roots)
        self.assertIs(publisher.active_roots, hub_roots.active_roots)
        self.assertIs(publisher.active_hf_root, hub_roots.active_hf_root)

    def test_schemas_runs_identically_without_the_script_directory_on_sys_path(self):
        # python -I / -P / PYTHONSAFEPATH=1 leave the script's own directory off
        # sys.path. Reproduce that in-process: unload both modules, drop every
        # entry that names scripts/, and load the publisher by file path.
        expected = schemas_run(publisher)
        with without_script_directory():
            self.assertFalse(any(names_scripts_directory(entry) for entry in sys.path))
            isolated = load_publisher_by_path()
            self.assertIsNot(isolated, publisher)
            actual = schemas_run(isolated)

        self.assertEqual(expected[0], 0)
        self.assertTrue(expected[1])
        self.assertEqual(actual, expected)
        self.assertIs(sys.modules["publish_hub_roots"], hub_roots)


def names_scripts_directory(entry):
    """Whether a sys.path entry ('' meaning the working directory) is scripts/."""
    return Path(entry or os.getcwd()).resolve() == SCRIPTS


@contextlib.contextmanager
def without_script_directory():
    """Take scripts/ off sys.path and unload the publisher modules; restore both."""
    saved_path = list(sys.path)
    saved_modules = {
        name: sys.modules.pop(name) for name in PUBLISHER_MODULES if name in sys.modules
    }
    sys.path[:] = [entry for entry in sys.path if not names_scripts_directory(entry)]
    try:
        yield
    finally:
        sys.path[:] = saved_path
        for name in PUBLISHER_MODULES:
            sys.modules.pop(name, None)
        sys.modules.update(saved_modules)


def load_publisher_by_path():
    """Execute the publisher from its file, as `python path/to/script.py` would."""
    spec = importlib.util.spec_from_file_location(
        "publish_grok46_hub", SCRIPTS / "publish_grok46_hub.py"
    )
    if spec is None or spec.loader is None:
        raise AssertionError("cannot build an import spec for the publisher")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def schemas_run(module):
    """Run ``schemas`` through ``module.main``; return the exit code and stdout."""
    stdout = io.StringIO()
    with mock.patch.object(sys, "argv", ["publish_grok46_hub.py", "schemas"]), (
        contextlib.redirect_stdout(stdout)
    ):
        code = module.main()
    return code, stdout.getvalue()


class PublisherMainRootTests(unittest.TestCase):
    def setUp(self):
        self.root = temporary_root(self)
        # An operator's exported overrides must not leak into these runs;
        # the snapshot taken here restores them afterwards.
        restore = mock.patch.dict(os.environ)
        restore.start()
        self.addCleanup(restore.stop)
        for setting in hub_roots.ROOT_SETTINGS:
            os.environ.pop(setting.env, None)

    def test_bad_configured_root_exits_2_before_any_work(self):
        missing = self.root / "missing"
        cases = (
            (["snapshot", "--hf-root", str(missing)], {}, "does not exist"),
            (["upload"], {HF_ENV: str(missing)}, "does not exist"),
            (["status", "--factory-root", str(missing)], {}, "does not exist"),
            (["status", "--hf-root", ""], {}, "--hf-root is set but empty"),
            (["snapshot", "--factory-root", ""], {}, "--factory-root is set but empty"),
            (["status"], {FACTORY_ENV: ""}, f"{FACTORY_ENV} is set but empty"),
        )
        with mock.patch.object(publisher, "factories") as factories, mock.patch.object(
            publisher, "cmd_snapshot"
        ) as snapshot, mock.patch.object(publisher.subprocess, "run") as whoami:
            for argv, environ, reason in cases:
                with self.subTest(argv=argv, environ=environ):
                    code, stderr = run_main(argv, **environ)
                    self.assertEqual(code, 2)
                    self.assertIn("refusing publication root:", stderr)
                    self.assertIn(reason, stderr)

        factories.assert_not_called()
        snapshot.assert_not_called()
        whoami.assert_not_called()
        self.assertFalse(missing.exists())

    def test_environment_roots_are_active_while_the_command_runs(self):
        hub = make_directory(self.root, "hf")
        source = make_directory(self.root, "raw")
        seen = []
        with mock.patch.object(
            publisher, "cmd_status", side_effect=lambda: seen.append(hub_roots.current_roots())
        ) as status:
            code, _stderr = run_main(["status"], **{HF_ENV: str(hub), FACTORY_ENV: str(source)})

        self.assertEqual(code, 0)
        status.assert_called_once_with()
        self.assertEqual(seen, [hub_roots.PublisherRoots(hf=hub, factory=source)])
        self.assertIsNone(hub_roots.current_roots())

    def test_flags_override_environment_at_the_command_line(self):
        flag_hub = make_directory(self.root, "flag-hf")
        env_hub = make_directory(self.root, "env-hf")
        seen = []
        with mock.patch.object(
            publisher, "cmd_status", side_effect=lambda: seen.append(publisher.hf_datasets_root())
        ):
            argv = ["status", "--hf-root", str(flag_hub)]
            code, _stderr = run_main(argv, **{HF_ENV: str(env_hub)})

        self.assertEqual(code, 0)
        self.assertEqual(seen, [flag_hub / "grok-4.6"])

    def test_only_target_is_checked_against_the_configured_factory_root(self):
        source = make_directory(self.root, "raw")
        seen = []

        def no_factories():
            seen.append(hub_roots.active_factory_root(publisher.FACTORY_ROOT))
            return []

        with mock.patch.object(
            publisher, "factories", side_effect=no_factories
        ), mock.patch.object(publisher, "cmd_snapshot") as snapshot:
            code, stderr = run_main(["snapshot", "--only", "typo", "--factory-root", str(source)])

        self.assertEqual(code, 2)
        self.assertIn("unknown --only target", stderr)
        self.assertEqual(seen, [source])
        snapshot.assert_not_called()

    def test_schemas_refuses_root_flags_even_when_empty(self):
        with mock.patch.object(publisher, "cmd_schemas", return_value=0) as schemas:
            for flag in ("--hf-root", "--factory-root"):
                for value in (str(self.root), ""):
                    with self.subTest(flag=flag, value=value):
                        code, stderr = run_main(["schemas", flag, value])
                        self.assertEqual(code, 2)
                        self.assertIn(f"schemas does not accept {flag}", stderr)

        schemas.assert_not_called()

    def test_schemas_ignores_the_root_environment(self):
        with mock.patch.object(publisher, "cmd_schemas", return_value=0) as schemas:
            code, stderr = run_main(
                ["schemas"], **{HF_ENV: str(self.root / "missing"), FACTORY_ENV: ""}
            )

        self.assertEqual(code, 0)
        self.assertEqual(stderr, "")
        schemas.assert_called_once_with(strict=False)

    def test_schemas_still_refuses_only(self):
        with mock.patch.object(publisher, "cmd_schemas") as schemas:
            code, stderr = run_main(["schemas", "--only", "anything"])

        self.assertEqual(code, 2)
        self.assertIn("schemas does not accept --only", stderr)
        schemas.assert_not_called()

    def test_help_documents_flags_environment_and_defaults(self):
        stdout = io.StringIO()
        plain = {"NO_COLOR": "1", "PYTHON_COLORS": "0", "COLUMNS": "200"}
        with mock.patch.object(sys, "argv", ["publish_grok46_hub.py", "--help"]), (
            mock.patch.dict(os.environ, plain)
        ), contextlib.redirect_stdout(stdout), self.assertRaises(SystemExit):
            publisher.main()

        text = " ".join(stdout.getvalue().split())
        for setting in hub_roots.ROOT_SETTINGS:
            self.assertIn(setting.flag, text)
            self.assertIn(f"${setting.env}", text)
        self.assertIn(str(publisher.HF_ROOT), text)


if __name__ == "__main__":
    unittest.main()
