"""Focused cases split from test_oracle_grounded_cli.py."""

from test_oracle_grounded_cli import (
    PINNED_COMMIT,
    Path,
    families,
    generate_status,
    io,
    json,
    mock,
    oracle_generate,
    read_jsonl,
    tempfile,
    unittest,
)


class GenerateCliCase19(unittest.TestCase):
    def test_an_explicit_commit_stamp_resolves_the_dirty_state(self):
        # --oracle-commit without a dirty flag must not stamp a null dirty
        # state; the checkout's own state is resolved instead.
        with tempfile.TemporaryDirectory(prefix="oracle-dirty-stamp-") as temp:
            out = Path(temp) / "run"
            with mock.patch("builtins.print"):
                status = oracle_generate.main(
                    [
                        "--family",
                        families.ENCODER_FAMILY,
                        "--count",
                        "1",
                        "--oracle-commit",
                        PINNED_COMMIT,
                        str(out),
                    ]
                )
            self.assertEqual(status, 0)
            manifest = json.loads((out / "manifest.json").read_text())
            self.assertIsInstance(manifest["oracle_dirty"], bool)
            for path in out.rglob("*.jsonl"):
                for item in read_jsonl(path):
                    self.assertIsInstance(item["oracle"]["dirty"], bool)


class GenerateCliCase20(unittest.TestCase):
    def test_argument_guards_reject_in_process(self):
        # The subprocess suite proves these exits end to end; exercising the
        # same guards in process keeps the refusal branches measured.
        cases = (
            ([], "an output directory is required"),
            (["--count", "0", "run"], "--count must be in"),
            (["--round", "0", "run"], "--round must be in"),
            (["--family", "no-such-family", "run"], "unknown families"),
            (
                ["--count", str(oracle_generate.MAX_RUN_RECORDS), "run"],
                "requested run would contain",
            ),
            (["--oracle-commit", "zz", "run"], "must resolve to an existing"),
            (["--oracle-commit", "a" * 40, "run"], "must resolve to an existing"),
        )
        with tempfile.TemporaryDirectory(prefix="oracle-arg-guards-") as temp:
            for argv, fragment in cases:
                argv = [str(Path(temp) / arg) if arg == "run" else arg for arg in argv]
                captured = io.StringIO()
                with mock.patch("sys.stderr", captured):
                    status = oracle_generate.main(argv)
                with self.subTest(argv=argv):
                    self.assertEqual(status, 2, captured.getvalue())
                    self.assertIn(fragment, captured.getvalue())


class GenerateCliCase21(unittest.TestCase):
    def test_list_families_prints_the_five_families_in_process(self):
        captured = io.StringIO()
        with mock.patch("sys.stdout", captured):
            status = oracle_generate.main(["--list-families"])
        self.assertEqual(status, 0)
        self.assertEqual(captured.getvalue().split(), list(families.FAMILY_NAMES))


class GenerateCliCase22(unittest.TestCase):
    def test_a_destination_under_outputs_raw_is_refused_before_the_lock(self):
        # AGENTS.md: outputs/raw/ is immutable. Even the sibling reservation
        # lock must never be created there, so the refusal runs first.
        with tempfile.TemporaryDirectory(prefix="oracle-raw-guard-") as temp:
            raw = Path(temp) / "outputs" / "raw"
            raw.mkdir(parents=True)
            status, err = generate_status(
                raw / "2026-09-01",
                mock.patch.object(oracle_generate, "RAW_TREE", raw))
            self.assertEqual(status, 2)
            self.assertIn("immutable raw tree", err)
            self.assertEqual(list(raw.iterdir()), [])


class GenerateCliCase23(unittest.TestCase):
    def test_a_destination_that_resolves_into_outputs_raw_is_refused(self):
        # A path that only reaches the raw tree through a symlink must be
        # refused too; realpath, not string prefixing, decides.
        with tempfile.TemporaryDirectory(prefix="oracle-raw-symlink-") as temp:
            raw = Path(temp) / "outputs" / "raw"
            raw.mkdir(parents=True)
            link = Path(temp) / "innocent-looking"
            link.symlink_to(raw, target_is_directory=True)
            status, err = generate_status(
                link / "run",
                mock.patch.object(oracle_generate, "RAW_TREE", raw))
            self.assertEqual(status, 2)
            self.assertIn("immutable raw tree", err)
            self.assertEqual(list(raw.iterdir()), [])


class GenerateCliCase24(unittest.TestCase):
    def test_the_raw_destination_check_covers_the_repository_tree(self):
        # Pure-function checks against the real repository constant: no
        # filesystem writes happen on either path.
        inside = oracle_generate.RAW_TREE / "2026-09-01"
        self.assertIsNotNone(oracle_generate._raw_destination_error(inside))
        self.assertIsNotNone(oracle_generate._raw_destination_error(oracle_generate.RAW_TREE))
        with tempfile.TemporaryDirectory(prefix="oracle-raw-outside-") as temp:
            self.assertIsNone(oracle_generate._raw_destination_error(Path(temp) / "run"))

