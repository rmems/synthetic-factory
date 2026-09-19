"""Focused cases split from test_oracle_grounded_cli.py."""

from test_oracle_grounded_cli import (
    GENERATE,
    PINNED_COMMIT,
    Path,
    VALIDATE,
    build,
    canon,
    families,
    json,
    record,
    run_cli,
    tempfile,
    unittest,
    write_test_manifest,
)


class ValidateCliCase24(unittest.TestCase):
    def test_domain_malformed_neuron_records_are_findings_not_tracebacks(self):
        cases = {
            "zero-period": lambda scenario: scenario.__setitem__(
                "stimulus",
                {
                    "kind": "pulse_train",
                    "parameters": {
                        "amplitude": 1.0,
                        "period_ms": 0.0,
                        "width_ms": 0.5,
                        "onset_ms": 1.0,
                    },
                },
            ),
            "overflowing-ratio": lambda scenario: scenario.update(
                {"duration_ms": 1_000_000.0, "dt_ms": 0.000001}
            ),
        }
        for label, mutate in cases.items():
            with (
                self.subTest(case=label),
                tempfile.TemporaryDirectory(prefix=f"oracle-domain-{label}-") as temp,
            ):
                item = build(families.NEURON_FAMILY)
                mutate(item["scenario"])
                item["proposal_hash"] = canon.digest(record.proposal_of(item))
                item["validation"] = record.assess(item)
                verdict = item["validation"]["status"]
                path = Path(temp) / families.NEURON_FAMILY / f"{verdict}-r01.jsonl"
                path.parent.mkdir(parents=True)
                path.write_text(canon.dumps_record(item) + "\n", encoding="utf-8")
                write_test_manifest(temp)
                completed = run_cli(VALIDATE, temp)
                self.assertEqual(completed.returncode, 1)
                self.assertNotIn("Traceback", completed.stderr)
                self.assertTrue(completed.stderr.strip())


class ValidateCliCase25(unittest.TestCase):
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
    def test_duplicate_ids_within_and_across_files_are_fatal(self):
        with tempfile.TemporaryDirectory(prefix="oracle-duplicate-within-") as temp:
            out = self.generate_run(temp)
            path = next(path for path in out.rglob("accepted-*.jsonl") if path.read_text().strip())
            line = path.read_text().splitlines()[0]
            path.write_text(f"{line}\n{line}\n", encoding="utf-8")
            write_test_manifest(out)
            completed = run_cli(VALIDATE, out)
            self.assertEqual(completed.returncode, 1)
            self.assertIn("duplicate record id", completed.stderr)

        with tempfile.TemporaryDirectory(prefix="oracle-duplicate-across-") as temp:
            out = self.generate_run(temp)
            accepted = next(
                path for path in out.rglob("accepted-*.jsonl") if path.read_text().strip()
            )
            rejected = accepted.with_name(accepted.name.replace("accepted-", "rejected-"))
            rejected.write_text(accepted.read_text(), encoding="utf-8")
            write_test_manifest(out)
            completed = run_cli(VALIDATE, out)
            self.assertEqual(completed.returncode, 1)
            self.assertIn("duplicate record id", completed.stderr)


class ValidateCliCase26(unittest.TestCase):
    def test_negative_max_findings_is_clamped_once(self):
        with tempfile.TemporaryDirectory(prefix="oracle-max-findings-") as temp:
            completed = run_cli(VALIDATE, "--max-findings", -5, temp)
            self.assertEqual(completed.returncode, 1)
            self.assertRegex(completed.stderr.strip(), r"^\.\.\. [1-9][0-9]* more findings$")
            self.assertNotIn("Traceback", completed.stderr)


class GenerateCliCase01(unittest.TestCase):
    def test_list_families_prints_all_five(self):
        completed = run_cli(GENERATE, "--list-families")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.split(), list(families.FAMILY_NAMES))


class GenerateCliCase02(unittest.TestCase):
    def test_a_single_family_run_writes_only_that_family(self):
        with tempfile.TemporaryDirectory(prefix="oracle-one-") as temp:
            out = Path(temp) / "run"
            completed = run_cli(
                GENERATE,
                "--family",
                families.ENCODER_FAMILY,
                "--count",
                2,
                "--oracle-commit",
                PINNED_COMMIT,
                "--no-oracle-dirty",
                out,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(
                sorted(p.name for p in out.iterdir()),
                ["manifest.json", families.ENCODER_FAMILY],
            )
            manifest = json.loads((out / "manifest.json").read_text())
            self.assertEqual(list(manifest["families"]), [families.ENCODER_FAMILY])
            self.assertEqual(manifest["generation_errors"], [])

