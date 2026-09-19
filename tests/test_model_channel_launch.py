"""Executable launch commands must enforce the revisions their metadata declares."""

import unittest

from pipelines.model_channel import source_policy, vllm


class PinnedLaunch(unittest.TestCase):
    def test_every_local_command_pins_weights_and_tokenizer(self):
        rows = [row for row in source_policy.reviewed_rows() if row["channel"] == "local_vllm"]
        self.assertTrue(rows)
        for row in rows:
            with self.subTest(path_id=row["path_id"]):
                spec = vllm.launch_spec(row["path_id"], runtime_version="test-runtime", device="test-device")
                command = spec["native_command"]
                for flag in ("--revision", "--tokenizer-revision"):
                    self.assertIn(flag, command)
                    self.assertEqual(command[command.index(flag) + 1], row["model_revision"])
