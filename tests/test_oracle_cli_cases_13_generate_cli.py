"""Focused cases split from test_oracle_grounded_cli.py."""

from test_oracle_grounded_cli import (
    GENERATE,
    PINNED_COMMIT,
    Path,
    families,
    generate_status,
    io,
    mock,
    oracle_generate,
    run_cli,
    tempfile,
    unittest,
)


class GenerateCliCase25(unittest.TestCase):
    def test_oversized_run_is_refused(self):
        with tempfile.TemporaryDirectory(prefix="oracle-oversized-run-") as temp:
            out = Path(temp) / "run"
            status, err = generate_status(
                out, mock.patch.object(oracle_generate, "MAX_RUN_BYTES", 1))
            self.assertEqual(status, 1)
            self.assertFalse(out.exists())
            self.assertIn("exceeding the validator's", err)
            self.assertIn("per-run limit", err)


class GenerateCliCase26(unittest.TestCase):
    def test_the_run_byte_cap_counts_the_manifest(self):
        # oracle_validate applies its per-run limit to every regular file,
        # manifest.json included; a run whose payloads fit but whose manifest
        # pushes it over would publish successfully and then always be
        # rejected, so generation must count the manifest too.
        with tempfile.TemporaryDirectory(prefix="oracle-manifest-cap-") as temp:
            published = Path(temp) / "published"
            args = [
                "--family",
                families.ENCODER_FAMILY,
                "--count",
                "1",
                "--oracle-commit",
                PINNED_COMMIT,
                "--no-oracle-dirty",
            ]
            with mock.patch("builtins.print"):
                self.assertEqual(oracle_generate.main([*args, str(published)]), 0)
            payload_bytes = sum(
                path.stat().st_size for path in published.rglob("*.jsonl")
            )
            capped = Path(temp) / "capped"
            captured = io.StringIO()
            with (
                mock.patch.object(oracle_generate, "MAX_RUN_BYTES", payload_bytes),
                mock.patch("sys.stderr", captured),
            ):
                status = oracle_generate.main([*args, str(capped)])
            self.assertEqual(status, 1)
            self.assertFalse(capped.exists())
            self.assertIn("including the manifest", captured.getvalue())


class GenerateCliCase27(unittest.TestCase):
    def test_generation_error_publishes_no_partial_run(self):
        with tempfile.TemporaryDirectory(prefix="oracle-transaction-build-") as temp:
            out = Path(temp) / "run"

            def fail_one(family, *_args, **_kwargs):
                if family == families.NEURON_FAMILY:
                    return [], [], ["synthetic build failure"]
                return [], [], []

            with (
                mock.patch.object(oracle_generate, "generate_family", side_effect=fail_one),
                mock.patch.object(oracle_generate, "write_jsonl") as write_jsonl,
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
            self.assertFalse(out.exists())
            write_jsonl.assert_not_called()
            self.assertEqual(
                sorted(path.name for path in Path(temp).iterdir()),
                [".run.oracle-generate.lock"],
            )


class GenerateCliCase28(unittest.TestCase):
    def test_staging_failure_publishes_no_partial_run_or_reservation(self):
        with tempfile.TemporaryDirectory(prefix="oracle-transaction-write-") as temp:
            out = Path(temp) / "run"
            with (
                mock.patch.object(
                    oracle_generate,
                    "generate_family",
                    return_value=([], [], []),
                ),
                mock.patch.object(
                    oracle_generate,
                    "write_jsonl",
                    side_effect=OSError("injected staging failure"),
                ),
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
            self.assertFalse(out.exists())
            quarantines = list(Path(temp).glob(".synthetic-factory-rollback-*"))
            self.assertEqual(len(quarantines), 1)
            self.assertTrue(quarantines[0].is_dir())
            self.assertEqual(
                {path for path in Path(temp).iterdir()},
                {quarantines[0], Path(temp) / ".run.oracle-generate.lock"},
            )


class GenerateCliCase29(unittest.TestCase):
    def test_a_stale_lock_path_does_not_block_a_new_kernel_lock(self):
        with tempfile.TemporaryDirectory(prefix="oracle-stale-lock-") as temp:
            out = Path(temp) / "run"
            lock_path = Path(temp) / ".run.oracle-generate.lock"
            lock_path.write_text("stale process\n", encoding="utf-8")
            completed = run_cli(
                GENERATE,
                "--count",
                1,
                "--oracle-commit",
                PINNED_COMMIT,
                out,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue(out.is_dir())

