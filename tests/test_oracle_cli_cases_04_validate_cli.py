"""Focused cases split from test_oracle_grounded_cli.py."""

from test_oracle_grounded_cli import (
    GENERATE,
    PINNED_COMMIT,
    Path,
    REPO,
    VALIDATE,
    build,
    canon,
    families,
    json,
    oracles,
    record,
    run_cli,
    shutil,
    tempfile,
    unittest,
    write_test_manifest,
)


class ValidateCliCase09(unittest.TestCase):
    def test_mixed_oracle_chains_are_not_counted_as_named_runtime(self):
        item = build(families.CREDIT_FAMILY)
        oracle = item["oracle"]
        oracle["implementation"] = "mixed"
        oracle["authority"] = "mixed-reference-and-runtime"
        item["provenance"]["claimed"] = "mixed-reference-and-runtime"
        item["meta"]["tags"][-1] = "mixed"
        oracle["availability"]["runtimes"][0]["bound"] = True
        oracle["availability"]["unbound"] = ["plasticity-lab"]
        runtime_stage = oracle["stages"][0]
        runtime_stage["implementation"] = "named-runtime"
        runtime_stage["oracle_id"] = "limbic-critic"
        runtime_stage["version"] = "0.0.0-double"
        runtime_stage["runtime_commit"] = "a" * 40
        runtime_stage["executable"] = "limbic-critic"
        runtime_stage.pop("module_digest", None)
        oracle["id"] = "limbic-critic+plasticity-ref"
        item["result"]["produced_by"] = oracle["id"]
        item["result_hash"] = canon.digest(item["result"])
        item["validation"] = record.assess(item)
        with tempfile.TemporaryDirectory(prefix="oracle-mixed-") as temp:
            path = Path(temp) / families.CREDIT_FAMILY / "accepted-r01.jsonl"
            path.parent.mkdir(parents=True)
            path.write_text(canon.dumps_record(item) + "\n")
            write_test_manifest(temp)
            completed = run_cli(VALIDATE, temp)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = json.loads(completed.stdout)
            self.assertEqual(report["mixed_oracle"], 1)
            self.assertEqual(report["named_runtime"], 0)
            self.assertEqual(report["reference_oracle"], 0)


class ValidateCliCase10(unittest.TestCase):
    def test_an_empty_directory_without_a_manifest_fails_closed(self):
        with tempfile.TemporaryDirectory(prefix="oracle-empty-") as temp:
            completed = run_cli(VALIDATE, temp)
            self.assertEqual(completed.returncode, 1)
            self.assertIn("required run manifest is missing", completed.stderr)
            self.assertEqual(json.loads(completed.stdout)["records"], 0)


class ValidateCliCase11(unittest.TestCase):
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
    def test_an_authenticated_but_empty_run_fails_closed(self):
        with tempfile.TemporaryDirectory(prefix="oracle-empty-manifest-") as temp:
            out = self.generate_run(temp)
            manifest_path = out / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            for path in list(out.iterdir()):
                if path.is_dir():
                    shutil.rmtree(path)
            manifest["families"] = {}
            manifest["files"] = {}
            manifest["oracle_availability"] = oracles.availability_report((), {})
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            completed = run_cli(VALIDATE, out)
            self.assertEqual(completed.returncode, 1)
            self.assertIn("at least one", completed.stderr)
            self.assertEqual(json.loads(completed.stdout)["records"], 0)


class ValidateCliCase12(unittest.TestCase):
    def test_a_missing_directory_is_a_usage_error(self):
        completed = run_cli(VALIDATE, REPO / "no" / "such" / "dir")
        self.assertEqual(completed.returncode, 2)


class ValidateCliCase13(unittest.TestCase):
    def test_no_argument_is_a_usage_error(self):
        self.assertEqual(run_cli(VALIDATE).returncode, 2)

