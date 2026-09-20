#!/usr/bin/env python3
"""Contract/envelope, manifest-binding, and fixture-builder gap tests.

Split out of ``test_distillation_review_gaps.py``: every test fails against
the code as it stood before the fix it names. The recurring shape is: take a
record the generator produced, tamper with one derived field, recompute
``provenance.record_sha256`` so the digest check is satisfied, and assert the
family checker still objects.
"""

import hashlib
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))



import energy_preferences as ep
import fault_recovery as fr
import moe_router as mr
import router_baseline as rb
import validate_distill as vd
from oracle_grounded import distill_contract as oc  # noqa: E402
from distill_gap_test_support import clone, rehash  # noqa: E402

class EnvelopeTypeGaps(unittest.TestCase):
    """distill_contract.py / validate_distill.py: malformed types are findings."""

    def test_unhashable_enum_fields_are_findings_not_crashes(self):
        # A JSON array where a string enum belongs used to raise TypeError
        # out of the set-membership test; validate_path does not catch that,
        # so one malformed line aborted validation of the entire run.
        tampers = [
            ("family", lambda r: r.__setitem__("family", ["not", "a", "family"])),
            ("generator.kind", lambda r: r["generator"].__setitem__("kind", ["llm"])),
            ("oracle.type", lambda r: r["oracle"].__setitem__("type", {})),
            (
                "oracle.authority",
                lambda r: r["oracle"].__setitem__("authority", ["authoritative"]),
            ),
            ("result.status", lambda r: r["result"].__setitem__("status", ["measured"])),
            (
                "validation.status",
                lambda r: r["validation"].__setitem__("status", ["passed"]),
            ),
            (
                "measurement.quantity",
                lambda r: r["result"]["measurements"][0].__setitem__(
                    "quantity", ["recovery_latency_ms"]
                ),
            ),
            (
                "candidate cost_quantity",
                lambda r: r["result"].__setitem__(
                    "preference", {"cost_quantity": ["energy_j"]}
                ),
            ),
        ]
        for label, tamper in tampers:
            with self.subTest(field=label):
                record = clone(fr.build_records(3, 1)[0])
                tamper(record)
                errors = vd.check_record(record, "x")
                self.assertTrue(errors, f"{label}: no findings reported")




class FixtureBuilderGaps(unittest.TestCase):
    """scripts/build_distillation_fixture.py"""

    def test_a_blocked_validation_aborts_the_rebuild(self):
        # A generator regression used to write MANIFEST.json and exit 0 even
        # though the freshly written run had validation findings.
        import importlib.util
        from unittest import mock

        spec = importlib.util.spec_from_file_location(
            "_bdf", REPO / "scripts" / "build_distillation_fixture.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        blocked_report = {
            "blocked": True,
            "findings": [{"file": "f", "line": 1, "error": "boom"}],
        }
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "run"
            out.mkdir()
            with mock.patch.object(
                module.validate_distill, "validate_path", return_value=blocked_report
            ):
                with self.assertRaises(SystemExit) as caught:
                    module._validation_summary(out)
            self.assertIn("refusing to publish MANIFEST.json", str(caught.exception))




class FourthRoundContractGaps(unittest.TestCase):
    """distill_contract.py — the fourth review pass."""

    def test_oracle_summaries_cannot_hide_in_generator_namespaces(self):
        # `top1_expert` was missing from the oracle-only denylist, so the
        # teacher label could be copied into the student-visible scenario.
        record = clone(mr.build_records(20260823, 1)[0])
        record["scenario"]["top1_expert"] = record["result"]["top1_expert"]
        rehash(record)
        errors = vd.check_record(record, "x")
        self.assertTrue(
            any(
                "ORACLE_FIELD_IN_GENERATOR_NAMESPACE" in e and "top1_expert" in e
                for e in errors
            ),
            f"a leaked teacher label passed: {errors}",
        )

    def test_measurement_values_respect_their_quantity_domains(self):
        # Any finite number used to pass: wall_time_s could go to -5 and
        # task_quality to 1.5 with only the digest to recompute.
        for quantity, value, fragment in (
            ("wall_time_s", -5.0, "cannot be negative"),
            ("task_quality", 1.5, "must lie in [0, 1]"),
        ):
            record = clone(ep.build_records(20260823, 1, repeats=1, warmup=0)[0])
            tampered = False
            for item in record["result"]["measurements"]:
                if item["quantity"] == quantity:
                    item["value"] = value
                    tampered = True
                    break
            self.assertTrue(tampered, f"no {quantity} measurement to tamper")
            rehash(record)
            with self.subTest(quantity=quantity):
                errors = vd.check_record(record, "x")
                self.assertTrue(
                    any(fragment in e for e in errors),
                    f"{quantity} = {value} passed: {errors}",
                )




class SixthRoundContractGaps(unittest.TestCase):
    """distill_contract.py and validate_distill.py — sixth pass."""

    def test_overflowing_float_literals_are_parse_failures(self):
        # json.loads turns 1e999 into inf; the first canonical
        # re-serialisation (allow_nan=False) then raised out of validation
        # instead of reporting the offending line.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rows.jsonl"
            path.write_text('{"value": 1e999}\n{"ok": 1.5}\n', encoding="utf-8")
            rows = oc.read_jsonl(str(path))
        self.assertIsNone(rows[0][1])
        self.assertEqual(rows[1][1], {"ok": 1.5})

    def test_a_lifted_validation_stamp_is_a_finding(self):
        # check_record verified the content digest but never the stamp
        # binding, so a verdict lifted from another record — any well-formed
        # 64-hex digest — stayed structurally valid.
        record = clone(fr.build_records(11, 1)[0])
        stamped = oc.stamp_validation(
            record, validator="validate_distill", version="1.0.0", findings=[]
        )
        self.assertEqual(vd.check_record(stamped, "x"), [])
        lifted = clone(stamped)
        lifted["validation"]["validator"]["validated_digest"] = "0" * 64
        errors = vd.check_record(lifted, "x")
        self.assertTrue(
            any("formed over the exact record" in e for e in errors),
            f"a lifted stamp passed: {errors}",
        )




class SeventhRoundSevereGaps(unittest.TestCase):
    """The severe findings of the seventh review pass (convergence-capped)."""

    def test_the_fixture_builder_refuses_the_immutable_raw_tree(self):
        # --force hands the out path to shutil.rmtree; pointed beneath
        # outputs/raw that deletes published evidence.
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "bdf_raw_guard", REPO / "scripts" / "build_distillation_fixture.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for target in ("outputs/raw", "outputs/raw/distillation-fixture"):
            with self.subTest(out=target):
                with self.assertRaises(SystemExit) as caught:
                    module.build(Path(target), force=True)
                self.assertIn("immutable evidence tree", str(caught.exception))
        self.assertFalse((REPO / "outputs/raw/distillation-fixture").exists())

    def test_duplicate_relay_channels_are_refused(self):
        # The healthy budget counts list entries while per-channel state
        # collapses duplicates: ['c0'] * 4 reported four healthy channels
        # from one distinct sensor, replaying as an authoritative outcome.
        record = clone(fr.build_records(11, 1)[0])
        system = dict(record["scenario"].get("system", {}))
        system["channels"] = ["c0", "c0", "c0", "c0"]
        record["scenario"]["system"] = system
        rehash(record)
        simulator = fr.RelayReflexSimulator()
        with self.assertRaises(oc.ContractError) as caught:
            simulator.run(record["scenario"], record["intervention"])
        self.assertIn("unique", str(caught.exception))
        errors = fr.check_family(record, "x")
        self.assertTrue(
            any("unique" in e for e in errors),
            f"duplicate channels passed validation: {errors}",
        )

    def test_a_non_string_fallback_source_cannot_engage(self):
        # Any truthy value satisfied the fallback tier: fallback_source 123
        # produced an authoritative `fallback` with FALLBACK_SOURCE_ENGAGED
        # and no named source.
        simulator = fr.RelayReflexSimulator()
        disturbance = {
            "kind": "sensor_loss",
            "parameters": {
                "onset_ms": 2.0,
                "duration_ms": 40.0,
                "channels": ["c0"],
            },
        }
        bad = {
            "system": {
                **fr.DEFAULT_SYSTEM,
                "min_healthy_channels": 4,
                "fallback_source": 123,
            }
        }
        with self.assertRaises(oc.ContractError) as caught:
            simulator.run(bad, disturbance)
        self.assertIn("fallback_source", str(caught.exception))
        # null stays legal: no fallback is an honest configuration.
        simulator.run(
            {"system": {**fr.DEFAULT_SYSTEM, "fallback_source": None}},
            disturbance,
        )

    def test_energy_records_must_carry_their_oracle_audit_metadata(self):
        # Deleting oracle.configuration contents and the fingerprint left a
        # record curation-eligible with no meter host, probe result, or
        # solver settings behind its measured preference.
        record = clone(ep.build_records(20260823, 1, repeats=1, warmup=0)[0])
        record["oracle"]["configuration"] = {}
        record["oracle"]["fingerprint"] = None
        rehash(record)
        errors = ep.check_family(record, "x")
        self.assertTrue(
            any("fingerprint must identify" in e for e in errors), errors
        )
        self.assertTrue(
            any("meter_probe must document" in e for e in errors), errors
        )

    def test_the_meter_probe_must_match_the_corpus_denomination(self):
        record = clone(ep.build_records(20260823, 1, repeats=1, warmup=0)[0])
        record["oracle"]["configuration"]["meter_probe"]["cost_quantity"] = (
            "energy_j"
        )
        rehash(record)
        errors = ep.check_family(record, "x")
        self.assertTrue(
            any("denominated" in e for e in errors),
            f"a probe contradicting the corpus quantity passed: {errors}",
        )


class EighthRoundSevereGaps(unittest.TestCase):
    """The severe findings of the eighth review pass (convergence-capped)."""

    def test_a_primary_channel_cannot_be_its_own_fallback(self):
        # fallback_source "c0" with "c0" among the primaries let a surviving
        # primary engage as its own fallback: losing c1 and c2 produced an
        # authoritative `fallback` with no redundant relay behind it.
        simulator = fr.RelayReflexSimulator()
        record = clone(fr.build_records(11, 1)[0])
        system = dict(record["scenario"].get("system", {}))
        system["fallback_source"] = "c0"
        record["scenario"]["system"] = system
        rehash(record)
        with self.assertRaises(oc.ContractError) as caught:
            simulator.run(record["scenario"], record["intervention"])
        self.assertIn("redundant source", str(caught.exception))
        errors = fr.check_family(record, "x")
        self.assertTrue(
            any("redundant source" in e for e in errors),
            f"a primary channel posing as its own fallback passed: {errors}",
        )

    def test_duplicate_contexts_cannot_straddle_the_split(self):
        # The committed fixture has duplicate-context groups; keyed on the
        # record id, four of them crossed the train/test split, leaking
        # exact input-label pairs into the holdout and inflating the
        # escalation verdict to learnable_nonlinear.
        records = [
            obj
            for _, obj in oc.read_jsonl(
                REPO / "tests/fixtures/distillation-run/moe-router/batch-r01.jsonl"
            )
        ]
        samples = rb.dataset_from_records(records)
        train, test = rb.split(samples)
        test_features = {s.features for s in test}
        train_features = {s.features for s in train}
        self.assertEqual(
            test_features & train_features,
            set(),
            "identical compact inputs appear on both sides of the split",
        )

    def test_a_changed_rapl_domain_set_is_unmeasurable(self):
        # A domain vanishing after workload() used to read as a zero delta
        # and silently underreport the interval, which can flip the measured
        # preference.
        range_uj = 10_000_000
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("intel-rapl:0", "intel-rapl:1"):
                domain = root / name
                domain.mkdir()
                (domain / "energy_uj").write_text("0\n")
                (domain / "max_energy_range_uj").write_text(f"{range_uj}\n")
            meter = ep.RaplEnergyMeter(root=root)
            state = {"n": 0}

            def workload():
                state["n"] += 1
                (root / "intel-rapl:0" / "energy_uj").write_text(
                    f"{state['n'] * 1_000_000}\n"
                )
                if state["n"] == 1:
                    import shutil

                    shutil.rmtree(root / "intel-rapl:1")

            with self.assertRaises(oc.OracleUnavailable) as caught:
                meter.measure(workload, repeats=2, warmup=0)
        self.assertIn("domain set changed", str(caught.exception))




class NinthRoundContractGaps(unittest.TestCase):
    """Envelope, JSONL and manifest findings of the ninth review pass."""

    def test_jsonl_reading_is_streamed(self):
        # read_jsonl buffered the whole raw file and every decoded record
        # before validate_path saw the first row, so one large batch could
        # kill validation of an otherwise valid corpus.
        import inspect

        self.assertTrue(inspect.isgeneratorfunction(oc.iter_jsonl))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "batch.jsonl"
            path.write_text('{"a": 1}\n\n{"b": 2}\n', encoding="utf-8")
            seen = []
            for lineno, obj in oc.iter_jsonl(path):
                seen.append((lineno, obj))
            self.assertEqual(seen, [(1, {"a": 1}), (3, {"b": 2})])

    def test_invalid_utf8_is_a_line_finding_not_an_abort(self):
        # read_text raised UnicodeDecodeError before per-line handling ran,
        # so one undecodable byte aborted the whole run with a traceback and
        # no validation report.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.jsonl"
            path.write_bytes(b'{"id": "x"}\n\xff\xfe not utf-8\n')
            report = vd.validate_path(Path(tmp))
        self.assertTrue(report["blocked"])
        self.assertTrue(
            any(
                finding["line"] == 2 and "JSON parse failure" in finding["error"]
                for finding in report["findings"]
            ),
            report["findings"],
        )

    def test_oracle_seed_and_commit_must_carry_schema_types(self):
        # Presence-only checks accepted seed {} and commit [] as
        # reproducibility metadata on an otherwise curation-eligible record.
        record = clone(fr.build_records(11, 1)[0])
        record["oracle"]["seed"] = {}
        record["oracle"]["commit"] = []
        rehash(record)
        errors = oc.check_envelope(record, "x")
        self.assertTrue(
            any("oracle.seed must be an integer or null" in e for e in errors),
            errors,
        )
        self.assertTrue(
            any("oracle.commit must be a string or null" in e for e in errors),
            errors,
        )

    def test_generator_seed_must_be_an_integer_or_null(self):
        record = clone(fr.build_records(11, 1)[0])
        for seed in ("11", True, [11], {}):
            with self.subTest(seed=seed):
                tampered = clone(record)
                tampered["generator"]["seed"] = seed
                rehash(tampered)
                errors = oc.check_envelope(tampered, "x")
                self.assertTrue(
                    any(
                        "generator.seed must be an integer or null" in e
                        for e in errors
                    ),
                    errors,
                )

    def test_run_files_are_reconciled_with_the_manifest(self):
        # validate_path scanned only the JSONL files: removing a listed
        # batch, changing bytes under a stale digest, or smuggling an extra
        # unlisted batch all returned blocked: false.
        records = fr.build_records(11, 2)
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / "run"
            batch = run / "fault-recovery" / "batch-r01.jsonl"
            oc.write_jsonl(batch, records)
            import hashlib as _hashlib

            good_sha = _hashlib.sha256(batch.read_bytes()).hexdigest()
            manifest = {
                "generated_by": "scripts/build_distillation_fixture.py",
                "files": {
                    "fault-recovery/batch-r01.jsonl": {
                        "records": 2,
                        "sha256": good_sha,
                    }
                },
            }
            manifest_path = run / "MANIFEST.json"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            self.assertFalse(vd.validate_path(run)["blocked"])

            with self.subTest(case="listed batch missing"):
                broken = dict(manifest)
                broken["files"] = {
                    **manifest["files"],
                    "energy-preferences/batch-r01.jsonl": {
                        "records": 4,
                        "sha256": "0" * 64,
                    },
                }
                manifest_path.write_text(json.dumps(broken), encoding="utf-8")
                report = vd.validate_path(run)
                self.assertTrue(report["blocked"])
                self.assertTrue(
                    any(
                        "does not contain it" in finding["error"]
                        for finding in report["findings"]
                    ),
                    report["findings"],
                )

            with self.subTest(case="stale digest and count"):
                manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                extra = clone(records[0])
                extra["id"] = "fr-extra-0001"
                rehash(extra)
                with batch.open("a", encoding="utf-8") as handle:
                    handle.write(oc.canonical_json(extra) + "\n")
                report = vd.validate_path(run)
                self.assertTrue(report["blocked"])
                self.assertTrue(
                    any(
                        "hashes to" in finding["error"]
                        for finding in report["findings"]
                    ),
                    report["findings"],
                )
                self.assertTrue(
                    any(
                        "records but the file carries 3" in finding["error"]
                        for finding in report["findings"]
                    ),
                    report["findings"],
                )

            with self.subTest(case="unlisted extra batch"):
                oc.write_jsonl(run / "moe-router" / "batch-r01.jsonl", [])
                report = vd.validate_path(run)
                self.assertTrue(
                    any(
                        "MANIFEST.json does not bind it" in finding["error"]
                        for finding in report["findings"]
                    ),
                    report["findings"],
                )

    def test_every_escalation_gate_parameter_is_validated(self):
        # mlp_hidden=0 published a bias-only model as an MLP,
        # min_test_records=-1 disabled the minimum-holdout guard, and a
        # negative (or NaN) nonlinear_margin classified a trailing MLP as
        # meaningfully nonlinear.
        samples = rb.dataset_from_records(mr.build_records(11, 40))
        for knobs in (
            {"mlp_hidden": 0},
            {"mlp_hidden": True},
            {"min_test_records": 0},
            {"min_test_records": -1},
            {"nonlinear_margin": -1.0},
            {"nonlinear_margin": math.nan},
        ):
            with self.subTest(knobs=knobs):
                with self.assertRaises(rb.BaselineError):
                    rb.evaluate_baselines(samples, **knobs)




class ManifestBindingGaps(unittest.TestCase):
    """validate_distill.py: the manifest binds a genuine integer count."""

    def _report(self, records_value):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "run"
            path = root / "batch.jsonl"
            oc.write_jsonl(path, fr.build_records(3, 1))
            sha = hashlib.sha256(path.read_bytes()).hexdigest()
            manifest = {"files": {"batch.jsonl": {
                "sha256": sha, "records": records_value}}}
            (root / "MANIFEST.json").write_text(
                json.dumps(manifest), encoding="utf-8"
            )
            return vd.validate_path(root)

    def test_a_boolean_or_float_record_count_does_not_bind(self):
        for value in (True, 1.0):
            with self.subTest(records=value):
                report = self._report(value)
                self.assertTrue(
                    any(
                        "records" in f["error"]
                        for f in report["findings"]
                    ),
                    f"a {type(value).__name__} count bound the file: "
                    f"{report['findings']}",
                )

    def test_an_integer_count_still_binds(self):
        report = self._report(1)
        self.assertFalse(
            any("MANIFEST" in f["error"] for f in report["findings"]),
            report["findings"],
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()


