"""Focused cases split from test_oracle_grounded_cli.py."""

from test_oracle_grounded_cli import (
    GENERATE,
    GOLDEN,
    PINNED_COMMIT,
    Path,
    VALIDATE,
    json,
    run_cli,
    tempfile,
    unittest,
)


class ValidateCliCase14(unittest.TestCase):
    def test_an_unknown_family_is_a_usage_error(self):
        completed = run_cli(VALIDATE, "--family", "not-a-family", GOLDEN)
        self.assertEqual(completed.returncode, 2)
        self.assertIn("unknown families", completed.stderr)


class ValidateCliCase15(unittest.TestCase):
    def test_the_validator_writes_nothing(self):
        before = {
            str(path.relative_to(GOLDEN)): path.stat().st_mtime_ns
            for path in GOLDEN.rglob("*")
            if path.is_file()
        }
        run_cli(VALIDATE, "--reproduce", GOLDEN)
        after = {
            str(path.relative_to(GOLDEN)): path.stat().st_mtime_ns
            for path in GOLDEN.rglob("*")
            if path.is_file()
        }
        self.assertEqual(before, after)


class ValidateCliCase16(unittest.TestCase):
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
    def test_manifest_digest_count_and_exact_file_set_are_enforced(self):
        with tempfile.TemporaryDirectory(prefix="oracle-manifest-") as temp:
            out = self.generate_run(temp)
            path = next(out.rglob("accepted-*.jsonl"))
            path.write_text(path.read_text() + "\n", encoding="utf-8")
            completed = run_cli(VALIDATE, out)
            self.assertEqual(completed.returncode, 1)
            self.assertIn("sha256 mismatch", completed.stderr)

        with tempfile.TemporaryDirectory(prefix="oracle-manifest-count-") as temp:
            out = self.generate_run(temp)
            manifest_path = out / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            relative = next(iter(manifest["files"]))
            manifest["files"][relative]["records"] += 1
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            completed = run_cli(VALIDATE, out)
            self.assertEqual(completed.returncode, 1)
            self.assertIn("record-count mismatch", completed.stderr)

        with tempfile.TemporaryDirectory(prefix="oracle-manifest-extra-") as temp:
            out = self.generate_run(temp)
            (out / "unmanifested.txt").write_text("not authenticated\n", encoding="utf-8")
            completed = run_cli(VALIDATE, out)
            self.assertEqual(completed.returncode, 1)
            self.assertIn("unmanifested file", completed.stderr)

        with tempfile.TemporaryDirectory(prefix="oracle-manifest-missing-") as temp:
            out = self.generate_run(temp)
            path = next(out.rglob("rejected-*.jsonl"))
            path.unlink()
            completed = run_cli(VALIDATE, out)
            self.assertEqual(completed.returncode, 1)
            self.assertIn("manifest file is missing", completed.stderr)


class ValidateCliCase17(unittest.TestCase):
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
    def test_manifest_paths_cannot_escape_the_run(self):
        with tempfile.TemporaryDirectory(prefix="oracle-manifest-path-") as temp:
            out = self.generate_run(temp)
            manifest_path = out / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["files"]["../outside.jsonl"] = {
                "sha256": "0" * 64,
                "records": 0,
            }
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            completed = run_cli(VALIDATE, out)
            self.assertEqual(completed.returncode, 1)
            self.assertIn("unsafe manifest file path", completed.stderr)

