"""Loaded measurement code and its digest come from one immutable source snapshot."""

import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from oracle_loaded_source_support import (
    PROBES,
    SOURCE_TREES,
    build_source_template,
    clone_probe_root,
    run_probe,
)
from process_test_support import ProcessTimeout, spawned_process_exit_code

REPO = Path(__file__).resolve().parents[1]


def _skip_source_path(path):
    if path.is_dir():
        return True
    if "__pycache__" in path.parts:
        return True
    if path.suffix == ".pyc":
        return True
    return False


def _source_fingerprint(root):
    digest = hashlib.sha256()
    for tree in SOURCE_TREES:
        for path in sorted((root / tree).rglob("*")):
            if _skip_source_path(path):
                continue
            relative = path.relative_to(root)
            relative_bytes = relative.as_posix().encode()
            content_digest = hashlib.sha256(path.read_bytes()).digest()
            digest.update(len(relative_bytes).to_bytes(4, "big"))
            digest.update(relative_bytes)
            digest.update(content_digest)
    return digest.digest()


class OracleLoadedSource(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._template_tmp = tempfile.TemporaryDirectory()
        cls.template = Path(cls._template_tmp.name)
        cls.repo_fingerprint = _source_fingerprint(REPO)
        build_source_template(REPO, cls.template)
        cls.template_fingerprint = _source_fingerprint(cls.template)
        if cls.template_fingerprint != cls.repo_fingerprint:
            raise AssertionError("loaded-source template differs from the repository")

    @classmethod
    def tearDownClass(cls):
        try:
            if _source_fingerprint(REPO) != cls.repo_fingerprint:
                raise AssertionError("loaded-source probes mutated the repository")
            if _source_fingerprint(cls.template) != cls.template_fingerprint:
                raise AssertionError("loaded-source probes mutated the pristine template")
        finally:
            cls._template_tmp.cleanup()

    def test_exact_loaded_bytes_and_import_ownership(self):
        # Driving the modes off the PROBES registry means a probe that is
        # registered can never go untested; the count pins the reviewed set
        # so a silent deletion still fails here.
        self.assertEqual(len(PROBES), 16)
        for mode in PROBES:
            for package_first in (False, True):
                with self.subTest(mode=mode, package_first=package_first):
                    status = spawned_process_exit_code(
                        run_probe, (str(self.template), mode, package_first),
                        timeout=ProcessTimeout(30, 5, "loaded source probe timed out"),
                    )
                    self.assertEqual(status, 0)

    def test_probe_clone_keeps_mutable_package_and_bytecode_private(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            clone_probe_root(self.template, root)
            source = self.template / "pipelines/oracle_grounded/sim.py"
            cloned = root / "pipelines/oracle_grounded/sim.py"
            before = source.read_bytes()

            self.assertNotEqual(source.stat().st_ino, cloned.stat().st_ino)
            cloned.write_bytes(b"changed")
            (cloned.parent / "__pycache__").mkdir()
            self.assertEqual(source.read_bytes(), before)
            self.assertFalse((source.parent / "__pycache__").exists())

    def test_probe_clone_falls_back_when_hard_links_are_unavailable(self):
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch("oracle_loaded_source_support.os.link", side_effect=OSError):
                clone_probe_root(self.template, Path(tmp))
            self.assertTrue((Path(tmp) / "schemas").is_dir())


if __name__ == "__main__":
    unittest.main()
