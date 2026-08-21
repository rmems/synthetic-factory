#!/usr/bin/env python3
"""validate_run.py must not write manifest.json unless --write is passed.

Also locks the shape layer's contract: reward arithmetic, and the id layering
where `id` coverage belongs to the deep layer (check_records / training_audit)
and this layer only type-checks an id that is present.
"""

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VALIDATE = REPO / "pipelines" / "validate_run.py"
V2_SCHEMA = REPO / "schemas" / "thalamic-trajectory-v2.schema.json"

sys.path.insert(0, str(REPO / "pipelines"))

import validate_run  # noqa: E402
import verify_execution  # noqa: E402

# Minimal record that passes the thalamic shape check (required keys + decision).
# Includes strict fields: meta.round and valid provenance/state.
TINY_THALAMIC = {
    "state": {"episode_id": "tiny-001", "sim_or_real": "designed"},
    "proposed_action": {"action_type": "noop"},
    "safety_decision": {"decision": "ACCEPT", "rationale": "test fixture"},
    "executed_action": {"action_type": "noop"},
    "future_outcome": {"success": "full"},
    "reward_components": {"total": 0.0},
    "meta": {"round": 1},
    "provenance": {"kind": "designed", "claimed": "designed"},
}

EXPECTED_TOTALS = {
    "files": 1,
    "records": 1,
    "by_kind": {"thalamic": 1},
    "error_count": 0,
}


def _tiny_run_dir(tmp: Path) -> Path:
    run_dir = tmp / "run"
    run_dir.mkdir()
    (run_dir / "tiny.jsonl").write_text(json.dumps(TINY_THALAMIC) + "\n")
    return run_dir


def _invoke(*args):
    return subprocess.run(
        [sys.executable, str(VALIDATE), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def _run_with_record(record):
    """Helper: write single record to temp dir and invoke validator."""
    with tempfile.TemporaryDirectory() as raw:
        run_dir = Path(raw) / "run"
        run_dir.mkdir()
        (run_dir / "case.jsonl").write_text(json.dumps(record) + "\n")
        result = _invoke(str(run_dir))
        return result


class ValidateRunWriteFlag(unittest.TestCase):
    def test_v2_schema_requires_root_id_and_state_provenance(self):
        schema = json.loads(V2_SCHEMA.read_text())
        strict = schema["allOf"][1]
        self.assertIn("id", strict["required"])
        self.assertIn("state", strict["required"])
        self.assertIn("sim_or_real", strict["properties"]["state"]["required"])

    def test_default_does_not_create_manifest(self):
        with tempfile.TemporaryDirectory() as raw:
            run_dir = _tiny_run_dir(Path(raw))
            result = _invoke(str(run_dir))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout), EXPECTED_TOTALS)
            self.assertFalse(
                (run_dir / "manifest.json").exists(),
                "default invoke must not create manifest.json",
            )

    def test_write_creates_manifest_with_matching_totals(self):
        with tempfile.TemporaryDirectory() as raw:
            run_dir = _tiny_run_dir(Path(raw))
            result = _invoke("--write", str(run_dir))
            self.assertEqual(result.returncode, 0, result.stderr)
            stdout_totals = json.loads(result.stdout)
            self.assertEqual(stdout_totals, EXPECTED_TOTALS)
            manifest_path = run_dir / "manifest.json"
            self.assertTrue(manifest_path.is_file())
            manifest = json.loads(manifest_path.read_text())
            self.assertEqual(manifest["totals"], stdout_totals)

    def test_default_does_not_overwrite_existing_manifest(self):
        with tempfile.TemporaryDirectory() as raw:
            run_dir = _tiny_run_dir(Path(raw))
            sentinel = {"sentinel": True, "files": []}
            manifest_path = run_dir / "manifest.json"
            manifest_path.write_text(json.dumps(sentinel) + "\n")
            result = _invoke(str(run_dir))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(manifest_path.read_text()), sentinel)

    def test_non_object_line_is_error_not_traceback(self):
        with tempfile.TemporaryDirectory() as raw:
            run_dir = Path(raw) / "run"
            run_dir.mkdir()
            (run_dir / "junk.jsonl").write_text("null\n")
            result = _invoke(str(run_dir))
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertIn("must be a JSON object", result.stderr)

    def test_invalid_utf8_is_error_not_traceback(self):
        with tempfile.TemporaryDirectory() as raw:
            run_dir = Path(raw) / "run"
            run_dir.mkdir()
            (run_dir / "bad.jsonl").write_bytes(b'{"id":"bad-\xff"}\n')
            result = _invoke(str(run_dir))
            self.assertEqual(result.returncode, 1)
            self.assertNotIn("Traceback", result.stderr)
            self.assertIn("invalid UTF-8", result.stderr)

    def test_nonstandard_json_constants_are_parse_errors(self):
        for constant in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(constant=constant), tempfile.TemporaryDirectory() as raw:
                run_dir = Path(raw) / "run"
                run_dir.mkdir()
                (run_dir / "bad-number.jsonl").write_text(
                    '{"goal":"test","steps":[{"decision_basis":"observe",'
                    '"tool_call":{"name":"probe","args":{"value":'
                    + constant
                    + '}},"observation":"ok"}],"outcome":"passed",'
                    '"reward":{"success":true}}\n'
                )

                result = _invoke(str(run_dir))

                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertIn("JSON parse error", result.stderr)
                self.assertIn(
                    f"non-standard JSON numeric constant {constant}", result.stderr
                )

    def test_non_object_episode_step_is_error_not_traceback(self):
        with tempfile.TemporaryDirectory() as raw:
            run_dir = Path(raw) / "run"
            run_dir.mkdir()
            episode = {
                "goal": "test",
                "steps": [None],
                "outcome": "failed",
                "reward": {"success": False},
            }
            (run_dir / "episode.jsonl").write_text(json.dumps(episode) + "\n")
            result = _invoke(str(run_dir))
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertNotIn("Traceback", result.stderr)
            self.assertIn("step 0: must be an object", result.stderr)

    def test_bridge_requires_globally_sorted_finite_events(self):
        with tempfile.TemporaryDirectory() as raw:
            run_dir = Path(raw) / "run"
            run_dir.mkdir()
            bridge = {
                "spike_events": [
                    {"channel": "a", "t_rel_ms": 2.0, "amplitude": 0.4},
                    {"channel": "b", "t_rel_ms": 1.0, "amplitude": 0.3},
                ],
                "language_view": {"trajectory": copy.deepcopy(TINY_THALAMIC)},
            }
            (run_dir / "bridge.jsonl").write_text(json.dumps(bridge) + "\n")
            result = _invoke(str(run_dir))
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn("not globally non-decreasing", result.stderr)


class ValidateRewardTotal(unittest.TestCase):
    def test_reward_total_reconciles(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["reward_components"] = {"task": 0.4, "safety": 0.3, "total": 0.7}
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_reward_total_mismatch_fails(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["reward_components"] = {"task": 0.4, "safety": 0.3, "total": 0.9}
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("reward_components.total", result.stderr)
        self.assertIn("sum of components", result.stderr)

    def test_reward_total_non_finite_fails(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["reward_components"] = {"task": 0.4, "total": float("inf")}
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("non-standard JSON numeric constant Infinity", result.stderr)

    def test_reward_total_ignores_bookkeeping_keys(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["reward_components"] = {
            "task": 0.5,
            "weights_note": "not counted",
            "total": 0.5,
        }
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_reward_total_zero_with_no_components(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["reward_components"] = {"total": 0.0}
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_reward_total_boolean_fails(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["reward_components"] = {"task": 0.4, "total": True}
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("reward_components.total", result.stderr)
        self.assertIn("finite", result.stderr)

    def test_reward_metadata_keys_are_not_components(self):
        # Same exclusion vocabulary as check_records: numeric bookkeeping keys
        # must not be summed as reward components.
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["reward_components"] = {
            "task": 0.4,
            "safety": 0.6,
            "unit_usd": 10000,
            "rounding_decimals": 3,
            "total": 1.0,
        }
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_unresolved_weighted_layout_is_not_rechecked_unweighted(self):
        # Declared weights whose components this layer cannot resolve must not
        # fall through to the sibling-sum check (that produced false errors).
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["reward_components"] = {
            "task": 1.0,
            "weights": {"task": 0.5, "mystery": 0.5},
            "total": 0.5,
        }
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 0, result.stderr)


class ValidateProvenanceStrict(unittest.TestCase):
    def test_provenance_valid_kinds(self):
        for kind in ["designed", "simulated", "hil", "unknown"]:
            rec = copy.deepcopy(TINY_THALAMIC)
            rec["provenance"] = {"kind": kind}
            result = _run_with_record(rec)
            self.assertEqual(result.returncode, 0, f"kind={kind} {result.stderr}")

    def test_provenance_invalid_kind_fails(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["provenance"] = {"kind": "real"}
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("provenance.kind", result.stderr)

    def test_state_sim_or_real_must_be_valid(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["state"]["sim_or_real"] = "real"
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("sim_or_real", result.stderr)

    def test_state_sim_or_real_valid(self):
        for v in ["designed", "simulated", "hil"]:
            rec = copy.deepcopy(TINY_THALAMIC)
            rec["state"]["sim_or_real"] = v
            result = _run_with_record(rec)
            self.assertEqual(result.returncode, 0, f"sim_or_real={v} {result.stderr}")

    def test_provenance_claimed_wrong_type_fails(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["provenance"] = {"kind": "designed", "claimed": 123}
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("provenance.claimed", result.stderr)


class ValidateMetaRound(unittest.TestCase):
    def test_meta_round_present(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["meta"] = {"round": 2}
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_meta_missing_fails(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec.pop("meta", None)
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("meta", result.stderr)
        # One violation, one error: an absent meta is reported by the
        # required-key check only; check_meta_round no longer adds a second
        # error for the same missing field.
        self.assertEqual(result.stderr.strip().count("ERROR:"), 1, result.stderr)

    def test_one_violation_reports_exactly_one_error(self):
        cases = {
            "real provenance": lambda r: r.__setitem__("state", {"sim_or_real": "real"}),
            "invalid provenance": lambda r: r.__setitem__("state", {"sim_or_real": "bogus"}),
            "meta wrong type": lambda r: r.__setitem__("meta", "not-an-object"),
            "reward wrong type": lambda r: r.__setitem__("reward_components", "not-an-object"),
        }
        for label, mutate in cases.items():
            with self.subTest(case=label):
                rec = copy.deepcopy(TINY_THALAMIC)
                mutate(rec)
                result = _run_with_record(rec)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertEqual(
                    result.stderr.strip().count("ERROR:"), 1, f"{label}: {result.stderr}"
                )

    def test_meta_round_not_integer_fails(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["meta"] = {"round": "2"}
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("meta.round", result.stderr)

    def test_meta_round_zero_fails(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["meta"] = {"round": 0}
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("meta.round", result.stderr)

    def test_meta_round_bool_rejected(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["meta"] = {"round": True}
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("meta.round", result.stderr)


class ValidateSpikeOrderIdempotent(unittest.TestCase):
    def test_spike_order_sorted_passes(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        bridge = {
            "spike_events": [
                {"channel": "a", "t_rel_ms": 1.0, "amplitude": 0.4},
                {"channel": "b", "t_rel_ms": 1.0, "amplitude": 0.3},
                {"channel": "c", "t_ms": 2.0, "amplitude": 0.5},
            ],
            "language_view": {"trajectory": rec},
        }
        with tempfile.TemporaryDirectory() as raw:
            run_dir = Path(raw) / "run"
            run_dir.mkdir()
            (run_dir / "bridge.jsonl").write_text(json.dumps(bridge) + "\n")
            result = _invoke(str(run_dir))
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_spike_order_idempotent(self):
        # Running validator twice yields identical error counts
        bridge = {
            "spike_events": [
                {"channel": "a", "t_rel_ms": 5.0, "amplitude": 0.4},
                {"channel": "b", "t_rel_ms": 3.0, "amplitude": 0.3},
            ],
            "language_view": {"trajectory": copy.deepcopy(TINY_THALAMIC)},
        }
        with tempfile.TemporaryDirectory() as raw:
            run_dir = Path(raw) / "run"
            run_dir.mkdir()
            (run_dir / "bridge.jsonl").write_text(json.dumps(bridge) + "\n")
            r1 = _invoke(str(run_dir))
            r2 = _invoke(str(run_dir))
            self.assertEqual(r1.returncode, 1)
            self.assertEqual(r2.returncode, 1)
            self.assertEqual(r1.stderr, r2.stderr)


class ValidateIdLayering(unittest.TestCase):
    """The shape layer type-checks `id`; coverage is a deep-layer concern.

    check_records / training_audit own "every record has a canonical id".
    validate_run must not reject a legacy record for a missing id, or the
    routing regresses to hiding every other invariant behind an id error.
    """

    def test_valid_string_id_accepted(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["id"] = "tiny-001"
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_id_is_not_a_shape_error(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec.pop("id", None)
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("'id'", result.stderr)

    def test_non_string_id_rejected(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["id"] = 123
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("'id' must be a non-empty string", result.stderr)

    def test_blank_id_rejected(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["id"] = "   "
        result = _run_with_record(rec)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("'id' must be a non-empty string", result.stderr)


class VerifyFrontierMalformedRecords(unittest.TestCase):
    """Malformed records must reach a verdict through the frontier entry point.

    verify_batch_for_frontier runs over untrusted generated JSONL, so a
    non-string safety_decision.rationale or a non-object
    language_view.trajectory must return failed/inconclusive instead of
    raising and taking the frontier gate down with it.
    """

    def _verify(self, record):
        with tempfile.TemporaryDirectory() as raw:
            batch = Path(raw) / "batch-r01.jsonl"
            batch.write_text(json.dumps(record) + "\n")
            return verify_execution.verify_batch_for_frontier(batch, strict=True)

    def test_non_string_rationale_blocks_without_raising(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["safety_decision"] = {
            "decision": "ACCEPT",
            "rationale": {"hidden": "object"},
        }
        counts, findings, blocked = self._verify(rec)
        self.assertEqual(counts["failed"], 1, findings)
        self.assertTrue(blocked)
        self.assertEqual(findings[0]["status"], "failed")

    def test_non_object_trajectory_blocks_without_raising(self):
        record = {
            "spike_events": [{"channel": "a", "t_rel_ms": 1.0, "amplitude": 0.2}],
            "language_view": {"trajectory": "not-an-object"},
        }
        counts, findings, blocked = self._verify(record)
        self.assertEqual(counts["inconclusive"], 1, findings)
        self.assertEqual(counts["verified"], 0, findings)
        self.assertTrue(blocked)
        self.assertIn("not an object", findings[0]["reason"])


if __name__ == "__main__":
    unittest.main()


class SchemaRefResolution(unittest.TestCase):
    """The v2 schema layers on v1 via a relative $ref, and validate_run derives
    its required-key sets from v1. Nothing else checks that those three stay in
    agreement, so a schema edit can silently change validator behavior.
    """

    SCHEMA_DIR = REPO / "schemas"

    def _load(self, name):
        return json.loads((self.SCHEMA_DIR / name).read_text())

    def test_v2_relative_ref_resolves_to_a_parseable_schema(self):
        v2 = self._load("thalamic-trajectory-v2.schema.json")
        refs = [
            part["$ref"]
            for part in v2.get("allOf", [])
            if isinstance(part, dict) and "$ref" in part
        ]
        self.assertTrue(refs, "v2 schema must layer on the base schema via $ref")
        for ref in refs:
            self.assertFalse(
                ref.startswith(("http://", "https://")),
                f"$ref must stay repo-relative, got {ref}",
            )
            target = (self.SCHEMA_DIR / ref).resolve()
            self.assertTrue(target.is_file(), f"unresolvable $ref target: {ref}")
            json.loads(target.read_text())

    def test_validator_key_sets_match_the_base_schema(self):
        base = self._load("thalamic-trajectory.schema.json")
        self.assertEqual(
            list(validate_run.THALAMIC_REQUIRED),
            list(base["required"]),
            "validate_run derives THALAMIC_REQUIRED from the base schema; they drifted",
        )
        for key in validate_run.THALAMIC_OBJECT_KEYS:
            self.assertEqual(base["properties"][key].get("type"), "object", key)
        for key in validate_run.THALAMIC_STRING_KEYS:
            self.assertEqual(base["properties"][key].get("type"), "string", key)
        self.assertNotIn(
            "meta",
            validate_run.THALAMIC_CORE_KEYS,
            "routing must not require meta, or legacy records skip every invariant",
        )

    def test_v2_required_keys_are_a_subset_of_the_resolved_union(self):
        base = self._load("thalamic-trajectory.schema.json")
        v2 = self._load("thalamic-trajectory-v2.schema.json")
        local = [
            part for part in v2.get("allOf", [])
            if isinstance(part, dict) and "required" in part
        ]
        for part in local:
            for key in part["required"]:
                self.assertIn(
                    key,
                    base["properties"],
                    f"v2 requires {key!r} which the resolved base schema does not define",
                )
