"""Descriptor ownership on run-tree inspection failures."""

import os
from pathlib import Path, PurePosixPath
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'pipelines'))
import oracle_validate  # noqa: E402


class OracleTreeDescriptors(unittest.TestCase):
    def test_child_descriptor_closes_when_stat_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'child').mkdir()
            parent_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
            child_fd = os.open(root / 'child', os.O_RDONLY | os.O_DIRECTORY)
            walk = oracle_validate._RunTreeWalk(root=root, directory_fd=parent_fd)
            entry_stat = os.stat(root / 'child')
            try:
                with mock.patch.object(oracle_validate.os, 'open', return_value=child_fd), \
                     mock.patch.object(oracle_validate.os, 'fstat', side_effect=OSError('stat failed')):
                    oracle_validate._push_subdirectory(
                        SimpleNamespace(name='child'), entry_stat, PurePosixPath('child'), walk,
                    )
                with self.assertRaises(OSError):
                    os.fstat(child_fd)
                self.assertEqual(walk.stack, [])
                self.assertEqual(walk.errors, [
                    f'{root / "child"}: could not open directory safely: OSError'
                ])
                os.fstat(parent_fd)
            finally:
                os.close(parent_fd)
                try:
                    os.close(child_fd)
                except OSError:
                    pass

    def test_root_descriptor_closes_when_stat_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            real_open = os.open
            descriptors = []

            def capture_open(*args, **kwargs):
                descriptor = real_open(*args, **kwargs)
                descriptors.append(descriptor)
                return descriptor

            try:
                with mock.patch.object(oracle_validate.os, 'open', side_effect=capture_open), \
                     mock.patch.object(oracle_validate.os, 'fstat', side_effect=OSError('stat failed')):
                    with self.assertRaises(OSError):
                        oracle_validate._open_run_root(temporary)
                self.assertEqual(len(descriptors), 1)
                with self.assertRaises(OSError):
                    os.fstat(descriptors[0])
            finally:
                for descriptor in descriptors:
                    try:
                        os.close(descriptor)
                    except OSError:
                        pass


if __name__ == '__main__':
    unittest.main()
