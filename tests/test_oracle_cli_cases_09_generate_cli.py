"""Focused cases split from test_oracle_grounded_cli.py."""

from test_oracle_grounded_cli import (
    FIXTURES,
    GENERATE,
    PINNED_COMMIT,
    Path,
    build,
    families,
    oracle_generate,
    oracle_validate,
    oracles,
    os,
    record,
    relabel_as_named_runtime,
    run_cli,
    sys,
    tempfile,
    unittest,
)


class GenerateCliCase03(unittest.TestCase):
    def test_the_manifest_note_reflects_whether_anything_is_publishable(self):
        # A run none of whose records earned publication must not claim
        # otherwise; a run containing a genuinely publishable record must not
        # claim the opposite. The note is informational text read by operators
        # and publication tooling, so it must track the records.
        args = oracle_generate.parse_args(["--count", "1", "ignored-out-dir"])
        availability = oracles.availability_report(())

        def manifest_for(item):
            return oracle_generate.build_manifest(
                args,
                [families.ENCODER_FAMILY],
                availability,
                PINNED_COMMIT,
                False,
                {families.ENCODER_FAMILY: ([item], [], [])},
                {},
            )

        # Unresolved dirty state is unresolved provenance, so even a reference
        # record at the current digest cannot be published.
        unpublishable = record.build_record(
            families.ENCODER_FAMILY, 0, seed=20260823, commit=PINNED_COMMIT, dirty=None, environ={}
        )
        self.assertFalse(unpublishable["validation"]["publishable"])
        manifest = manifest_for(unpublishable)
        self.assertIn("no record here", manifest["note"])
        # The validator recomputes the note, so the two vocabularies must be
        # byte-identical or every generated run would fail note validation.
        self.assertEqual(manifest["note"], oracle_validate.MANIFEST_NOTE_UNPUBLISHABLE)

        # #171: an accepted reference record at the current digest is
        # publishable, and so is the same record measured by a named runtime.
        reference = next(
            item
            for item in (build(families.ENCODER_FAMILY, index) for index in range(24))
            if item["validation"]["status"] == "accepted"
        )
        for publishable in (reference, relabel_as_named_runtime(reference)):
            with self.subTest(implementation=publishable["oracle"]["implementation"]):
                self.assertTrue(
                    publishable["validation"]["publishable"], publishable["validation"]
                )
                manifest = manifest_for(publishable)
                self.assertNotIn("no record here", manifest["note"])
                self.assertIn("publishable", manifest["note"])
                self.assertEqual(manifest["note"], oracle_validate.MANIFEST_NOTE_PUBLISHABLE)


class GenerateCliCase04(unittest.TestCase):
    def test_it_refuses_to_overwrite_an_existing_run(self):
        with tempfile.TemporaryDirectory(prefix="oracle-twice-") as temp:
            out = Path(temp) / "run"
            first = run_cli(
                GENERATE,
                "--count",
                1,
                "--oracle-commit",
                PINNED_COMMIT,
                "--no-oracle-dirty",
                out,
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            second = run_cli(
                GENERATE,
                "--count",
                1,
                "--oracle-commit",
                PINNED_COMMIT,
                "--no-oracle-dirty",
                out,
            )
            self.assertEqual(second.returncode, 2)
            self.assertIn("refusing to overwrite", second.stderr)


class GenerateCliCase05(unittest.TestCase):
    def test_require_runtime_refuses_to_write_when_nothing_is_bound(self):
        with tempfile.TemporaryDirectory(prefix="oracle-req-") as temp:
            out = Path(temp) / "run"
            completed = run_cli(
                GENERATE,
                "--require-runtime",
                "--count",
                1,
                "--oracle-commit",
                PINNED_COMMIT,
                out,
            )
            self.assertEqual(completed.returncode, 3)
            self.assertIn("not bound", completed.stderr)
            self.assertFalse(out.exists())


class GenerateCliCase06(unittest.TestCase):
    def test_reference_backend_does_not_treat_ambient_command_as_selected_runtime(self):
        with tempfile.TemporaryDirectory(prefix="oracle-selected-runtime-") as temp:
            out = Path(temp) / "run"
            env = dict(os.environ)
            for runtime in families.ALL_RUNTIMES:
                env.pop(oracles.env_key(runtime), None)
            env[oracles.env_key("axon-encoder")] = (
                f"{sys.executable} {FIXTURES / 'protocol_double.py'} ok"
            )
            completed = run_cli(
                GENERATE,
                "--family",
                families.ENCODER_FAMILY,
                "--count",
                1,
                "--require-runtime",
                "--oracle-commit",
                PINNED_COMMIT,
                out,
                env=env,
            )
            # Reference is now an explicit backend: ambient command bindings do
            # not authorize execution. Only the selected family is reported.
            self.assertEqual(completed.returncode, 3, completed.stderr)
            self.assertIn("not bound: axon-encoder", completed.stderr)
            self.assertNotIn("neuromod", completed.stderr)
            self.assertFalse(out.exists())
