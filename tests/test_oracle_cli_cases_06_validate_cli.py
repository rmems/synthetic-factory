"""Focused cases split from test_oracle_grounded_cli.py."""

from test_oracle_grounded_cli import (
    GENERATE,
    PINNED_COMMIT,
    Path,
    VALIDATE,
    canon,
    families,
    json,
    os,
    read_jsonl,
    run_cli,
    tempfile,
    unittest,
    write_test_manifest,
)


class ValidateCliCase18(unittest.TestCase):
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
    def test_manifest_metadata_is_recomputed_from_the_captured_records(self):
        mutations = {
            "round": lambda manifest: manifest.__setitem__("round", manifest["round"] + 1),
            "seed": lambda manifest: manifest.__setitem__("seed", manifest["seed"] + 1),
            "count": lambda manifest: manifest.__setitem__(
                "count_per_family", manifest["count_per_family"] + 1
            ),
            "commit": lambda manifest: manifest.__setitem__("oracle_commit", "f" * 40),
            "module": lambda manifest: manifest.__setitem__(
                "module_digest", canon.digest({"forged": "implementation"})
            ),
            "summary": lambda manifest: manifest["families"][families.ENCODER_FAMILY][
                "accepted"
            ].__setitem__("records", 999),
        }
        for label, mutate in mutations.items():
            with (
                self.subTest(metadata=label),
                tempfile.TemporaryDirectory(prefix=f"oracle-metadata-{label}-") as temp,
            ):
                out = self.generate_run(temp)
                manifest_path = out / "manifest.json"
                manifest = json.loads(manifest_path.read_text())
                mutate(manifest)
                manifest_path.write_text(
                    json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                completed = run_cli(VALIDATE, out)
                self.assertEqual(completed.returncode, 1)
                self.assertFalse(json.loads(completed.stdout)["manifest_valid"])
                self.assertTrue(completed.stderr.strip())


class ValidateCliCase19(unittest.TestCase):
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
    def test_unhashable_manifest_and_record_metadata_are_bounded_findings(self):
        with tempfile.TemporaryDirectory(prefix="oracle-manifest-runtime-type-") as temp:
            out = self.generate_run(temp)
            manifest_path = out / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["oracle_availability"]["runtimes"][0]["runtime"] = []
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            completed = run_cli(VALIDATE, out)
            self.assertEqual(completed.returncode, 1)
            self.assertNotIn("Traceback", completed.stderr)
            self.assertIn("runtime names must be strings", completed.stderr)

        with tempfile.TemporaryDirectory(prefix="oracle-record-implementation-type-") as temp:
            out = self.generate_run(temp)
            payload = next(
                path for path in out.rglob("accepted-*.jsonl") if path.read_text().strip()
            )
            items = read_jsonl(payload)
            items[0]["oracle"]["implementation"] = []
            payload.write_text(
                "".join(canon.dumps_record(item) + "\n" for item in items),
                encoding="utf-8",
            )
            write_test_manifest(out)
            completed = run_cli(VALIDATE, out)
            self.assertEqual(completed.returncode, 1)
            self.assertNotIn("Traceback", completed.stderr)
            self.assertIn("oracle.implementation must be a string", completed.stderr)

        with tempfile.TemporaryDirectory(prefix="oracle-manifest-count-bound-") as temp:
            out = self.generate_run(temp)
            manifest_path = out / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["count_per_family"] = 10**12
            manifest_path.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            completed = run_cli(VALIDATE, out)
            self.assertEqual(completed.returncode, 1)
            self.assertNotIn("Traceback", completed.stderr)
            self.assertIn("count_per_family must be an integer", completed.stderr)


class ValidateCliCase20(unittest.TestCase):
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
    def test_manifest_rejects_symlinked_and_hardlinked_payloads(self):
        with tempfile.TemporaryDirectory(prefix="oracle-symlink-") as temp:
            out = self.generate_run(temp)
            payload = next(out.rglob("accepted-*.jsonl"))
            outside = Path(temp) / "outside.jsonl"
            outside.write_bytes(payload.read_bytes())
            payload.unlink()
            payload.symlink_to(outside)
            completed = run_cli(VALIDATE, out)
            self.assertEqual(completed.returncode, 1)
            self.assertIn("symbolic links are not allowed", completed.stderr)

        with tempfile.TemporaryDirectory(prefix="oracle-hardlink-") as temp:
            out = self.generate_run(temp)
            payload = next(out.rglob("accepted-*.jsonl"))
            outside = Path(temp) / "outside.jsonl"
            outside.write_bytes(payload.read_bytes())
            payload.unlink()
            os.link(outside, payload)
            completed = run_cli(VALIDATE, out)
            self.assertEqual(completed.returncode, 1)
            self.assertIn("hard-linked files are not allowed", completed.stderr)

