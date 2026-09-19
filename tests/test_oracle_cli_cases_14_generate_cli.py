"""Focused cases split from test_oracle_grounded_cli.py."""

from test_oracle_grounded_cli import (
    PINNED_COMMIT,
    Path,
    errno,
    mock,
    oracle_generate,
    tempfile,
    unittest,
)


class GenerateCliCase30(unittest.TestCase):
    def test_stdout_failure_reports_that_publication_already_succeeded(self):
        with tempfile.TemporaryDirectory(prefix="oracle-stdout-failure-") as temp:
            out = Path(temp) / "run"
            stderr_messages = []

            def fail_stdout(*args, **kwargs):
                if kwargs.get("file") is None:
                    raise BrokenPipeError("closed stdout")
                stderr_messages.append(" ".join(str(arg) for arg in args))

            with mock.patch("builtins.print", side_effect=fail_stdout):
                status = oracle_generate.main(
                    [
                        "--count",
                        "1",
                        "--oracle-commit",
                        PINNED_COMMIT,
                        str(out),
                    ]
                )
            self.assertEqual(status, 1)
            self.assertTrue(out.is_dir())
            self.assertTrue(any("run was published" in line for line in stderr_messages))


class GenerateCliCase31(unittest.TestCase):
    def test_a_noncooperating_writer_cannot_win_after_reservation(self):
        with tempfile.TemporaryDirectory(prefix="oracle-transaction-race-") as temp:
            out = Path(temp) / "run"
            real_publish = oracle_generate.publish_noreplace

            def race(staging, destination, expected_identity):
                destination.mkdir()
                (destination / "other-writer.txt").write_text("must survive\n", encoding="utf-8")
                return real_publish(staging, destination, expected_identity)

            with (
                mock.patch.object(oracle_generate, "publish_noreplace", side_effect=race),
                mock.patch("builtins.print"),
            ):
                status = oracle_generate.main(
                    [
                        "--count",
                        "1",
                        "--oracle-commit",
                        PINNED_COMMIT,
                        "--no-oracle-dirty",
                        str(out),
                    ]
                )
            self.assertEqual(status, 1)
            self.assertEqual((out / "other-writer.txt").read_text(), "must survive\n")
            quarantines = list(Path(temp).glob(".synthetic-factory-rollback-*"))
            self.assertEqual(len(quarantines), 1)
            self.assertTrue((quarantines[0] / "manifest.json").is_file())
            self.assertEqual(
                {path for path in Path(temp).iterdir()},
                {quarantines[0], Path(temp) / ".run.oracle-generate.lock", out},
            )


class GenerateCliCase32(unittest.TestCase):
    def test_a_replaced_staging_inode_is_never_reported_as_published(self):
        with tempfile.TemporaryDirectory(prefix="oracle-source-race-") as temp:
            staging = Path(temp) / "staging"
            displaced = Path(temp) / "displaced"
            destination = Path(temp) / "run"
            staging.mkdir()
            (staging / "manifest.json").write_text("legitimate\n", encoding="utf-8")
            expected_identity = oracle_generate._directory_identity(staging)
            real_rename = oracle_generate._rename_noreplace

            def substitute(source, target):
                if Path(source) == staging:
                    staging.rename(displaced)
                    staging.mkdir()
                    (staging / "manifest.json").write_text(
                        "attacker-controlled\n", encoding="utf-8"
                    )
                return real_rename(source, target)

            with mock.patch.object(oracle_generate, "_rename_noreplace", side_effect=substitute):
                with self.assertRaises(OSError) as raised:
                    oracle_generate.publish_noreplace(staging, destination, expected_identity)
            self.assertEqual(raised.exception.errno, errno.ESTALE)
            self.assertFalse(destination.exists())
            self.assertEqual(
                (displaced / "manifest.json").read_text(encoding="utf-8"),
                "legitimate\n",
            )


class GenerateCliCase33(unittest.TestCase):
    def test_atomic_publication_fails_closed_without_renameat2(self):
        with tempfile.TemporaryDirectory(prefix="oracle-no-renameat2-") as temp:
            staging = Path(temp) / "staging"
            destination = Path(temp) / "run"
            staging.mkdir()
            with mock.patch.object(oracle_generate.sys, "platform", "darwin"):
                with self.assertRaises(OSError) as raised:
                    oracle_generate.publish_noreplace(staging, destination)
            self.assertEqual(raised.exception.errno, errno.ENOSYS)
            self.assertTrue(staging.is_dir())
            self.assertFalse(destination.exists())

