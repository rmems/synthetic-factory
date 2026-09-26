"""A pinned publication inode must still be reachable at the requested path."""

import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))
import oracle_generate
from oracle_grounded import families


class PublicationBinding(unittest.TestCase):
    def _run(self, destination):
        with mock.patch.object(sys, "stdout", io.StringIO()) as output, mock.patch.object(
            sys, "stderr", io.StringIO()
        ) as errors:
            status = oracle_generate.main([
                "--count", "1", "--family", families.ENCODER_FAMILY, str(destination),
            ])
        return status, output.getvalue(), errors.getvalue()

    def test_parent_replaced_after_reservation_cannot_publish_elsewhere(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            parent = root / "parent"
            parent.mkdir()
            moved = root / "moved"
            reserve = oracle_generate.reserve_run

            def replace(destination):
                descriptors = reserve(destination)
                parent.rename(moved)
                parent.mkdir()
                (parent / "foreign").write_text("preserve")
                return descriptors

            with mock.patch.object(oracle_generate, "reserve_run", side_effect=replace):
                status, output, errors = self._run(parent / "run")
            self.assertNotEqual(status, 0)
            self.assertEqual(output, "")
            self.assertIn("requested parent", errors)
            self.assertFalse((moved / "run").exists())
            self.assertEqual((parent / "foreign").read_text(), "preserve")

    def test_parent_replaced_after_rename_cannot_report_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            parent = root / "parent"
            parent.mkdir()
            moved = root / "moved"
            publish = oracle_generate.publish_noreplace

            def replace(*args):
                publish(*args)
                parent.rename(moved)
                parent.mkdir()
                (parent / "foreign").write_text("preserve")

            with mock.patch.object(oracle_generate, "publish_noreplace", side_effect=replace):
                status, output, errors = self._run(parent / "run")
            self.assertNotEqual(status, 0)
            self.assertEqual(output, "")
            self.assertIn("after publication", errors)
            self.assertTrue((moved / "run/manifest.json").is_file())
            self.assertFalse((parent / "run").exists())
            self.assertEqual((parent / "foreign").read_text(), "preserve")

    def test_unchanged_parent_alias_remains_supported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "target"
            target.mkdir()
            alias = root / "alias"
            alias.symlink_to(target, target_is_directory=True)
            status, output, errors = self._run(alias / "run")
            self.assertEqual(status, 0, errors)
            self.assertTrue(json.loads(output)["files"])
            self.assertTrue((target / "run/manifest.json").is_file())


if __name__ == "__main__":
    unittest.main()
