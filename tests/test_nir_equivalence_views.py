"""Training views and the CLI surface for pipelines/nir_equivalence.py."""

import copy
import json
import tempfile
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nir_equivalence_support import (  # noqa: E402
    FIXTURE,
    WHERE,
    cli as _cli,
    fixture_records as _fixture_records,
)

import nir_equivalence as nir  # noqa: E402
import oracle_contract as contract  # noqa: E402

class TrainingViews(unittest.TestCase):
    def test_views_preserve_every_record(self):
        records = _fixture_records()
        views, errors = nir.build_training_views(records)
        self.assertEqual(errors, [])
        self.assertEqual(len(views), len(records))

    def test_divergent_records_are_flagged(self):
        views, _ = nir.build_training_views(_fixture_records())
        failed = [view for view in views if view["parity_failed"]]
        self.assertTrue(failed)
        for view in failed:
            self.assertTrue(view["reason_codes"])

    def test_view_carries_the_evidence_scope(self):
        views, _ = nir.build_training_views(_fixture_records())
        for view in views:
            self.assertIn("in-repo", view["evidence_scope"])

    def test_training_view_evidence_parity(self):
        record = next(
            item
            for item in nir.generate_records(round_number=1, steps=4)
            if item["scenario"]["id"] == "nir-partial-coverage-li"
        )
        view = nir.training_view(record)
        self.assertEqual(view["evidence_digests"], record["result"]["derived_from"])

        view["evidence_digests"] = view["evidence_digests"][:-1]
        errors = nir.training_view_errors(record, view, WHERE)
        self.assertTrue(any("exactly match" in error for error in errors), errors)

    def test_every_nir_specific_training_field_is_rederived(self):
        record = copy.deepcopy(_fixture_records()[0])
        mutations = {
            "prompt": "fabricated prompt",
            "completion": "all upstream runtimes executed and matched",
            "graph_class": "fabricated-class",
            "scenario_id": "fabricated-scenario",
            "executed_runtimes": ["nir_rs"],
            "evidence_scope": "all intended runtimes executed",
        }
        for key, value in mutations.items():
            with self.subTest(key=key):
                view = nir.training_view(record)
                view[key] = value
                errors = nir.training_view_errors(record, view, WHERE)
                self.assertTrue(
                    any("validator-derived NIR projection" in error for error in errors),
                    errors,
                )

    def test_view_names_unavailable_runtimes_too(self):
        views, _ = nir.build_training_views(_fixture_records())
        self.assertTrue(
            any("nir_rs:unavailable" in target for target in views[0]["execution_targets"])
        )

    def test_prompt_does_not_invent_a_runtime_pair(self):
        record = next(
            item
            for item in _fixture_records()
            if item["result"]["comparison"]["executed_count"] < 2
        )
        prompt = nir.training_view(record)["prompt"]
        self.assertNotIn("more than one runtime", prompt)
        self.assertTrue("only one runtime" in prompt or "did not execute" in prompt)

    def test_filtering_out_divergences_is_rejected(self):
        records = _fixture_records()
        views = [
            nir.training_view(record)
            for record in records
            if record["result"]["verdict"] == contract.VERDICT_MATCH
        ]
        errors = contract.view_set_errors(records, views)
        self.assertTrue(any("TRAINING_VIEW_HIDES_FAILURE" in error for error in errors))

    def test_prefiltered_batch_fails_catalog_authentication(self):
        # The view/set checks compare views against the records they were
        # handed, which is vacuous when the input file was already filtered;
        # the batch itself must cover the fixed graph catalog.
        records = _fixture_records()
        retained = [
            record
            for record in records
            if record["result"]["verdict"] == contract.VERDICT_MATCH
        ]
        self.assertTrue(retained and len(retained) < len(records))
        views, errors = nir.build_training_views(retained, source="filtered")
        self.assertTrue(
            any(
                "does not cover the scenario catalog" in error
                and "TRAINING_VIEW_HIDES_FAILURE" in error
                for error in errors
            ),
            errors,
        )

    def test_completion_is_rederived_instead_of_copying_summary(self):
        record = copy.deepcopy(_fixture_records()[0])
        record["result"]["summary"] = "fabricated completion"
        self.assertNotEqual(
            nir.training_view(record)["completion"], "fabricated completion"
        )


class Cli(unittest.TestCase):
    def test_availability_reports_no_upstream_runtime(self):
        result = _cli(["availability"])
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertFalse(report["nir_rs"]["available"])

    def test_generate_then_validate(self):
        with tempfile.TemporaryDirectory() as tmp:
            generated = _cli(["generate", tmp, "--round", "3", "--steps", "6"])
            self.assertEqual(generated.returncode, 0, generated.stderr)
            out = Path(json.loads(generated.stdout)["written"])
            self.assertEqual(out.name, "batch-r03.jsonl")
            validated = _cli(["validate", str(out)])
            self.assertEqual(validated.returncode, 0, validated.stderr)

    def test_generate_refuses_to_overwrite_an_existing_round(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = _cli(["generate", tmp, "--round", "3", "--steps", "4"])
            self.assertEqual(first.returncode, 0, first.stderr)
            out = Path(json.loads(first.stdout)["written"])
            before = out.read_bytes()
            second = _cli(["generate", tmp, "--round", "3", "--steps", "6"])
            self.assertEqual(second.returncode, 2, second.stderr)
            self.assertIn("refusing to overwrite", second.stderr)
            self.assertEqual(out.read_bytes(), before)

    def test_validate_rejects_a_suppressed_divergence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "batch.jsonl"
            records = _fixture_records()
            for record in records:
                record["result"]["verdict"] = contract.VERDICT_MATCH
            path.write_text(
                "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
                encoding="utf-8",
            )
            result = _cli(["validate", str(path)])
            self.assertEqual(result.returncode, 1)
            self.assertIn("DIVERGENCE_SUPPRESSED", result.stderr)

    def test_training_view_cli_emits_one_line_per_record(self):
        result = _cli(["training-view", str(FIXTURE)])
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = [line for line in result.stdout.splitlines() if line.strip()]
        self.assertEqual(len(lines), len(_fixture_records()))

    def test_training_view_cli_refuses_an_invalid_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "batch.jsonl"
            record = copy.deepcopy(_fixture_records()[0])
            record["result"]["summary"] = "fabricated completion"
            path.write_text(json.dumps(record) + "\n", encoding="utf-8")
            result = _cli(["training-view", str(path)])
            self.assertEqual(result.returncode, 1)
            self.assertIn("result.summary", result.stderr)

    def test_validate_reports_an_unreadable_path(self):
        result = _cli(["validate", "/definitely/missing/nir.jsonl"])
        self.assertEqual(result.returncode, 1)
        self.assertIn("cannot read file", result.stderr)

    def test_jsonl_framing_uses_lf_not_unicode_line_separators(self):
        for separator in ("\u2028", "\u2029"):
            with self.subTest(separator=ord(separator)), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "batch.jsonl"
                path.write_text(
                    json.dumps({"id": f"left{separator}right"}, ensure_ascii=False)
                    + "\n",
                    encoding="utf-8",
                )
                records, errors = nir.read_jsonl(path)
                self.assertEqual(errors, [])
                self.assertEqual(records, [{"id": f"left{separator}right"}])

    def test_read_jsonl_rejects_non_standard_json_constants(self):
        # A record containing NaN/Infinity must be a parse error, not a
        # silently accepted value standards-compliant JSON parsers reject.
        for constant in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(constant=constant):
                with tempfile.TemporaryDirectory() as tmp:
                    path = Path(tmp) / "batch.jsonl"
                    path.write_text(
                        '{"pairing": %s}\n' % constant, encoding="utf-8"
                    )
                    records, errors = nir.read_jsonl(path)
                    self.assertEqual(records, [])
                    self.assertTrue(errors)
                    self.assertIn("non-standard JSON numeric constant", errors[0])

    def test_read_jsonl_rejects_overflowing_float_tokens(self):
        # `1e9999` is an ordinary numeric token, so parse_constant never sees
        # it; float() would silently turn it into infinity, a value digest()
        # can never re-derive.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "batch.jsonl"
            path.write_text('{"pairing": 1e9999}\n', encoding="utf-8")
            records, errors = nir.read_jsonl(path)
            self.assertEqual(records, [])
            self.assertTrue(errors)
            self.assertIn("non-finite JSON number", errors[0])

    def test_read_jsonl_reports_absurd_nesting_as_a_line_error(self):
        # A syntactically valid but absurdly nested line must be a line-level
        # parse error, not a decoder RecursionError that aborts the scan. The
        # depth at which the decoder gives up is a platform property (stack
        # budget), so probe for one it refuses rather than hard-coding it.
        depth = 100_000
        while depth <= 3_200_000:
            try:
                json.loads("[" * depth + "]" * depth)
            except RecursionError:
                break
            depth *= 2
        else:
            self.skipTest("this platform's decoder accepts 3.2M-deep nesting")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "batch.jsonl"
            path.write_text(
                "[" * depth + "]" * depth + '\n{"id": "after"}\n',
                encoding="utf-8",
            )
            records, errors = nir.read_jsonl(path)
            self.assertEqual(records, [{"id": "after"}])
            self.assertEqual(len(errors), 1)
            self.assertIn("JSON parse error", errors[0])



if __name__ == "__main__":
    unittest.main()
