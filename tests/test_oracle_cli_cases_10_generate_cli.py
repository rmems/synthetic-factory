"""Focused cases split from test_oracle_grounded_cli.py."""

from test_oracle_grounded_cli import (
    FIXTURES,
    GENERATE,
    GOLDEN,
    PINNED_COMMIT,
    Path,
    families,
    json,
    oracle_generate,
    oracles,
    os,
    run_cli,
    sys,
    tempfile,
    unittest,
)


class GenerateCliCase07(unittest.TestCase):
    def test_a_bound_runtime_refuses_a_stamped_commit_that_does_not_match_the_checkout(self):
        # A bound named runtime can make this run's records publishable, so
        # --oracle-commit may not silently stamp a different, if resolvable,
        # revision than the one that actually supplied module_digest.
        with tempfile.TemporaryDirectory(prefix="oracle-commit-mismatch-") as temp:
            out = Path(temp) / "run"
            env = dict(os.environ)
            for runtime in families.ALL_RUNTIMES:
                env.pop(oracles.env_key(runtime), None)
            env[oracles.env_key("axon-encoder")] = (
                f"{sys.executable} {FIXTURES / 'protocol_double.py'} ok"
            )
            historical_commit = json.loads((GOLDEN / "manifest.json").read_text())["oracle_commit"]
            self.assertNotEqual(historical_commit, PINNED_COMMIT)
            completed = run_cli(
                GENERATE,
                "--family",
                families.ENCODER_FAMILY,
                "--count",
                1,
                "--oracle-commit",
                historical_commit,
                out,
                env=env,
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn("does not match the checked-out HEAD", completed.stderr)
            self.assertFalse(out.exists())


class GenerateCliCase08(unittest.TestCase):
    def test_a_clean_reference_run_refuses_a_stamp_that_does_not_match_the_checkout(self):
        # Reference measurements can be published, so clean historical stamps
        # must not authenticate measurements made by the current checkout.
        with tempfile.TemporaryDirectory(prefix="oracle-commit-reference-") as temp:
            out = Path(temp) / "run"
            historical_commit = json.loads((GOLDEN / "manifest.json").read_text())["oracle_commit"]
            self.assertNotEqual(historical_commit, PINNED_COMMIT)
            completed = run_cli(
                GENERATE,
                "--family",
                families.ENCODER_FAMILY,
                "--count",
                1,
                "--oracle-commit",
                historical_commit,
                "--no-oracle-dirty",
                out,
            )
            self.assertEqual(completed.returncode, 2, completed.stderr)
            self.assertIn("does not match the checked-out HEAD", completed.stderr)
            self.assertFalse(out.exists())


class GenerateCliCase09(unittest.TestCase):
    def test_an_unknown_family_is_a_usage_error(self):
        with tempfile.TemporaryDirectory(prefix="oracle-bad-family-") as temp:
            completed = run_cli(GENERATE, "--family", "nope", Path(temp) / "run")
            self.assertEqual(completed.returncode, 2)
            self.assertIn("unknown families", completed.stderr)


class GenerateCliCase10(unittest.TestCase):
    def test_an_unresolved_or_noncanonical_source_commit_writes_nothing(self):
        for forged in ("main", "a" * 39, "A" * 40, "a" * 41, "f" * 40):
            with (
                self.subTest(commit=forged),
                tempfile.TemporaryDirectory(prefix="oracle-bad-commit-") as temp,
            ):
                out = Path(temp) / "run"
                completed = run_cli(
                    GENERATE,
                    "--count",
                    1,
                    "--oracle-commit",
                    forged,
                    out,
                )
                self.assertEqual(completed.returncode, 2)
                self.assertIn("resolve to an existing", completed.stderr)
                self.assertFalse(out.exists())


class GenerateCliCase11(unittest.TestCase):
    def test_a_non_positive_count_is_a_usage_error(self):
        with tempfile.TemporaryDirectory(prefix="oracle-count-") as temp:
            self.assertEqual(run_cli(GENERATE, "--count", 0, Path(temp) / "run").returncode, 2)
            self.assertEqual(run_cli(GENERATE, "--round", 0, Path(temp) / "run").returncode, 2)
            self.assertEqual(
                run_cli(
                    GENERATE,
                    "--count",
                    oracle_generate.MAX_COUNT + 1,
                    Path(temp) / "too-many",
                ).returncode,
                2,
            )
            self.assertEqual(
                run_cli(
                    GENERATE,
                    "--round",
                    oracle_generate.MAX_ROUND + 1,
                    Path(temp) / "too-late",
                ).returncode,
                2,
            )


class GenerateCliCase12(unittest.TestCase):
    def test_count_limit_applies_to_the_whole_selected_run(self):
        with tempfile.TemporaryDirectory(prefix="oracle-total-count-") as temp:
            count = oracle_generate.MAX_RUN_RECORDS // len(families.FAMILY_NAMES) + 1
            completed = run_cli(
                GENERATE,
                "--count",
                count,
                "--oracle-commit",
                PINNED_COMMIT,
                Path(temp) / "run",
            )
            self.assertEqual(completed.returncode, 2)
            self.assertIn("requested run would contain", completed.stderr)


class GenerateCliCase13(unittest.TestCase):
    def test_no_output_directory_is_a_usage_error(self):
        self.assertEqual(run_cli(GENERATE).returncode, 2)

