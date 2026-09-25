"""Focused cases split from test_oracle_grounded_cli.py."""

from test_oracle_grounded_cli import (
    GENERATE,
    PINNED_COMMIT,
    Path,
    families,
    mock,
    oracle_validate,
    record,
    run_cli,
    tempfile,
    unittest,
)


class ValidateCliCase21(unittest.TestCase):
    def generate_run(self, parent, count=1):
        out = Path(parent) / "run"
        completed = run_cli(
            GENERATE,
            "--count",
            count,
            "--oracle-commit",
            PINNED_COMMIT,
            "--no-oracle-dirty",
            out,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return out
    def test_intermediate_directory_swap_cannot_escape_the_pinned_run(self):
        with tempfile.TemporaryDirectory(prefix="oracle-directory-race-") as temp:
            out = self.generate_run(temp)
            family_dir = next(path for path in out.iterdir() if path.is_dir())
            outside = Path(temp) / "outside"
            original_snapshot = oracle_validate._snapshot_regular_file
            swapped = False

            def race(root_fd, request):
                nonlocal swapped
                if request.relative != "manifest.json" and not swapped:
                    family_dir.rename(outside)
                    family_dir.symlink_to(outside, target_is_directory=True)
                    swapped = True
                return original_snapshot(root_fd, request)

            with mock.patch.object(oracle_validate, "_snapshot_regular_file", side_effect=race):
                _manifest, snapshots, errors = oracle_validate.authenticate_manifest(out)
            self.assertTrue(swapped)
            self.assertFalse(
                any(snapshot.relative.startswith(f"{family_dir.name}/") for snapshot in snapshots)
            )
            self.assertTrue(any("could not capture authenticated file" in e for e in errors))


class ValidateCliCase22(unittest.TestCase):
    def generate_run(self, parent, count=1):
        out = Path(parent) / "run"
        completed = run_cli(
            GENERATE,
            "--count",
            count,
            "--oracle-commit",
            PINNED_COMMIT,
            "--no-oracle-dirty",
            out,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return out
    def test_validation_uses_the_authenticated_bytes_not_a_later_path_read(self):
        with tempfile.TemporaryDirectory(prefix="oracle-snapshot-") as temp:
            out = self.generate_run(temp)
            _manifest, snapshots, errors = oracle_validate.authenticate_manifest(out)
            self.assertEqual(errors, [])
            snapshot = next(item for item in snapshots if item.body.strip())
            snapshot.path.write_text("not json\n", encoding="utf-8")
            totals, findings, _records = oracle_validate.validate_file(
                snapshot, oracle_validate.ValidationContext()
            )
            self.assertGreater(totals["records"], 0)
            self.assertEqual(totals["parse_failures"], 0)
            self.assertFalse(any("JSON parse error" in finding for finding in findings))


class ValidateCliCase23(unittest.TestCase):
    def test_a_final_record_exception_is_bounded_as_a_finding(self):
        snapshot = oracle_validate.FileSnapshot(
            path=Path("accepted-r01.jsonl"),
            relative=f"{families.ENCODER_FAMILY}/accepted-r01.jsonl",
            body=b"{}\n",
            device=1,
            inode=1,
        )
        with mock.patch.object(record, "classify", side_effect=RuntimeError("boom")):
            totals, findings, _records = oracle_validate.validate_file(
                snapshot, oracle_validate.ValidationContext()
            )
        self.assertEqual(totals["invalid"], 1)
        self.assertTrue(any("internal exception: RuntimeError" in f for f in findings))
