#!/usr/bin/env python3
"""The spike-train contract this PR hardens, and its schema derivation.

A trajectory-level spike train obeys the same order contract as a bridge
stream: before this hardening, `check_spike_order` ran only for bridge
pairs, so a thalamic record could publish a channel-grouped (time-inverted)
train and the validator would exit 0. SchemaRefResolution locks the other
half of the contract — validate_run derives its timestamp keys, event field
types, and provenance vocabularies from the schema's own `$defs` rather than
restating them, so a schema edit cannot silently change what the runtime
enforces.
"""

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from validate_run_test_helpers import (  # noqa: E402
    REPO,
    TINY_THALAMIC,
    _invoke,
    _run_with_record,
)

import validate_run  # noqa: E402
import validate_run_spikes  # noqa: E402
from exact_json import dumps_exact_json, parse_finite_json_float  # noqa: E402


class ValidateSpikeOrderIdempotent(unittest.TestCase):
    def test_repo_remains_a_compatibility_reexport(self):
        self.assertEqual(validate_run.REPO, validate_run_spikes.REPO)

    def test_spike_order_sorted_passes(self):
        rec = copy.deepcopy(TINY_THALAMIC)
        bridge = {
            "spike_events": [
                {"channel": "a", "t_rel_ms": 1.0, "amplitude": 0.4},
                {"channel": "b", "t_rel_ms": 1.0, "amplitude": 0.3},
                {"channel": "c", "t_rel_ms": 2.0, "amplitude": 0.5},
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


class ClockDomainKeysStayInStepWithTheCurator(unittest.TestCase):
    """validate_run and curate_bridge must agree on what names a clock.

    curate_bridge is deliberately dependency-free (stdlib only, no pipelines
    imports), so it cannot import the tuple and the two are maintained as
    peers. If they drift, the validator would publish a stream the curator
    quarantines as BRIDGE_MULTIPLE_CLOCK_DOMAINS, or the reverse.
    """

    def test_the_two_clock_domain_key_tuples_are_identical(self):
        import curate_bridge

        self.assertEqual(
            validate_run.SPIKE_CLOCK_DOMAIN_KEYS, curate_bridge.CLOCK_DOMAIN_KEYS
        )


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

    def test_validator_spike_contract_matches_the_base_schema(self):
        """The spike-train constants are read from the schema, not restated.

        `spike_events` is the last invariant the schema did not describe; the
        validator now derives its timestamp keys and the bridge-only event
        keys from `$defs`, so a schema edit cannot silently change what the
        runtime enforces.
        """
        base = self._load("thalamic-trajectory.schema.json")
        events = base["properties"]["spike_events"]
        self.assertEqual(events["type"], "array")
        self.assertEqual(events["items"]["$ref"], "#/$defs/spike_event")

        spike_event = base["$defs"]["spike_event"]
        self.assertEqual(
            list(validate_run.SPIKE_TIME_KEYS),
            [key for branch in spike_event["oneOf"] for key in branch["required"]],
        )
        for key in validate_run.SPIKE_TIME_KEYS:
            self.assertEqual(spike_event["properties"][key]["type"], "number", key)
        self.assertEqual(
            list(validate_run.SPIKE_EVENT_STRING_KEYS),
            [
                key
                for key, definition in spike_event["properties"].items()
                if definition.get("type") == "string"
            ],
        )
        self.assertEqual(
            list(validate_run.SPIKE_EVENT_NUMBER_KEYS),
            [
                key
                for key, definition in spike_event["properties"].items()
                if definition.get("type") == "number"
            ],
        )
        self.assertEqual(spike_event["properties"]["channel"]["pattern"], r"\S")

        bridge_event = base["$defs"]["bridge_spike_event"]
        self.assertEqual(
            list(validate_run.BRIDGE_SPIKE_EVENT_KEYS),
            [key for part in bridge_event["allOf"] for key in part.get("required", ())],
        )
        self.assertEqual(
            bridge_event["allOf"][0]["$ref"],
            "#/$defs/spike_event",
            "the bridge event shape must layer on the base spike event",
        )

    def test_provenance_vocabularies_come_from_the_schema(self):
        base = self._load("thalamic-trajectory.schema.json")
        self.assertEqual(
            validate_run.ALLOWED_SIM_OR_REAL,
            frozenset(base["properties"]["state"]["properties"]["sim_or_real"]["enum"]),
        )
        self.assertEqual(
            validate_run.ALLOWED_PROVENANCE_KIND,
            frozenset(base["properties"]["provenance"]["properties"]["kind"]["enum"]),
        )
        self.assertNotIn("real", validate_run.ALLOWED_PROVENANCE_KIND)
        self.assertNotIn("real", validate_run.ALLOWED_SIM_OR_REAL)

    def test_schema_requires_the_hardened_fields(self):
        """Lock the field-level requirements the hardening added or kept."""
        base = self._load("thalamic-trajectory.schema.json")
        self.assertIn("kind", base["properties"]["provenance"]["required"])
        self.assertIn("total", base["properties"]["reward_components"]["required"])
        self.assertIn("round", base["properties"]["meta"]["required"])
        self.assertIn("rationale", base["properties"]["safety_decision"]["required"])
        # Ordering is not expressible in JSON Schema, so the schema must at
        # least say where it is enforced instead of leaving the stream untyped.
        description = base["properties"]["spike_events"]["description"]
        self.assertIn("non-decreasing", description)
        self.assertIn("same timestamp key", description)
        self.assertIn("check_spike_order", description)


class ThalamicSpikeStream(unittest.TestCase):
    """A trajectory-level spike train obeys the same order contract as bridge.

    Before this, `check_spike_order` ran only for bridge pairs, so a thalamic
    record could publish a channel-grouped (time-inverted) train and the
    validator would exit 0.
    """

    def _record(self, events):
        rec = copy.deepcopy(TINY_THALAMIC)
        rec["spike_events"] = events
        return rec

    def _accept(self, events):
        """Assert this stream validates clean."""
        result = _run_with_record(self._record(events))
        self.assertEqual(result.returncode, 0, result.stderr)
        return result

    def _reject(self, events, *expected, absent=(), errors=None):
        """Assert this stream is rejected, carrying every expected marker.

        ``absent`` markers must not appear, and ``errors`` pins the exact
        ERROR: count so a single defect cannot be reported twice.
        """
        result = _run_with_record(self._record(events))
        self.assertEqual(result.returncode, 1, result.stderr)
        for marker in expected:
            self.assertIn(marker, result.stderr)
        for marker in absent:
            self.assertNotIn(marker, result.stderr)
        if errors is not None:
            self.assertEqual(result.stderr.strip().count("ERROR:"), errors, result.stderr)
        return result

    @staticmethod
    def _validate_bridge(bridge):
        """Publish one bridge record into a scratch run and validate it."""
        with tempfile.TemporaryDirectory() as raw:
            run_dir = Path(raw) / "run"
            run_dir.mkdir()
            (run_dir / "bridge.jsonl").write_text(json.dumps(bridge) + "\n")
            return _invoke(str(run_dir))

    @staticmethod
    def _bridge(events):
        return {
            "spike_events": events,
            "language_view": {"trajectory": copy.deepcopy(TINY_THALAMIC)},
        }

    def test_sorted_stream_passes(self):
        self._accept(
            [
                {"channel": "a", "t_rel_ms": 1.0, "amplitude": 0.4},
                {"channel": "a", "t_rel_ms": 1.0, "amplitude": 0.5},
                {"channel": "b", "t_rel_ms": 2.0, "amplitude": 0.3},
            ]
        )

    def test_sorted_alias_stream_passes(self):
        self._accept(
            [
                {"channel": "a", "t_ms": 1.0, "amplitude": 0.4},
                {"channel": "b", "t_ms": 2.0, "amplitude": 0.3},
            ]
        )

    def test_mixed_timestamp_keys_are_rejected_without_an_order_verdict(self):
        self._reject(
            [
                {"channel": "a", "t_rel_ms": 120.0, "amplitude": 0.4},
                {"channel": "b", "t_ms": 90.0, "amplitude": 0.3},
            ],
            validate_run.SPIKE_TIME_KEY_MISMATCH,
            absent=(validate_run.SPIKE_ORDER_MISMATCH,),
            errors=1,
        )

    def test_multiple_declared_clock_domains_are_rejected_without_an_order_verdict(self):
        """Timestamps from two clocks are not one timeline, so an increasing
        sequence across them is not evidence of order. curate_bridge already
        quarantines this exact stream as BRIDGE_MULTIPLE_CLOCK_DOMAINS; the
        validator must not publish it (Codex #87 discussion_r3885917890)."""
        self._reject(
            [
                {"channel": "a", "t_rel_ms": 1.0, "clock_id": "sensor-a"},
                {"channel": "b", "t_rel_ms": 2.0, "clock_id": "sensor-b"},
            ],
            validate_run.SPIKE_CLOCK_DOMAIN_MISMATCH,
            absent=(validate_run.SPIKE_ORDER_MISMATCH,),
            errors=1,
        )

    def test_exact_numeric_clock_domains_are_not_rounded_together(self):
        """A cross-clock descent cannot pass after exact JSON parsing."""
        events = json.loads(
            "["
            '{"channel":"a","t_rel_ms":2.0,"clock_id":1.0},'
            '{"channel":"b","t_rel_ms":1.0,"clock_id":1.0000000000000001}'
            "]",
            parse_float=parse_finite_json_float,
        )
        record = self._record(events)

        self.assertEqual(
            validate_run.declared_clock_domains(events, record),
            {"1.0", "1.0000000000000001"},
        )
        with tempfile.TemporaryDirectory() as raw:
            run_dir = Path(raw) / "run"
            run_dir.mkdir()
            (run_dir / "case.jsonl").write_text(dumps_exact_json(record) + "\n")
            result = _invoke(str(run_dir))

        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(validate_run.SPIKE_CLOCK_DOMAIN_MISMATCH, result.stderr)
        self.assertNotIn(validate_run.SPIKE_ORDER_MISMATCH, result.stderr)

    def _record_with(self, events, **record_fields):
        """A thalamic record carrying this stream plus enclosing declarations."""
        rec = self._record(events)
        rec.update(record_fields)
        return rec

    def test_a_clock_declared_on_the_record_conflicts_with_an_event_clock(self):
        """curate_bridge._declared_clock_domains reads the record and its meta
        as well as the events, so a bridge with a top-level clock_id and an
        event-level source_clock is quarantined BRIDGE_MULTIPLE_CLOCK_DOMAINS.
        Reading only the events let the publish gate admit it (Codex #87)."""
        record = self._record_with(
            [
                {"channel": "a", "t_rel_ms": 1.0, "source_clock": "event-clock"},
                {"channel": "b", "t_rel_ms": 2.0, "source_clock": "event-clock"},
            ],
            clock_id="record-clock",
        )
        result = _run_with_record(record)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(validate_run.SPIKE_CLOCK_DOMAIN_MISMATCH, result.stderr)
        self.assertIn("record-clock", result.stderr)
        self.assertIn("event-clock", result.stderr)
        self.assertNotIn(validate_run.SPIKE_ORDER_MISMATCH, result.stderr)

    def test_a_clock_declared_on_record_meta_conflicts_with_an_event_clock(self):
        record = self._record_with(
            [
                {"channel": "a", "t_rel_ms": 1.0, "source_clock": "event-clock"},
                {"channel": "b", "t_rel_ms": 2.0, "source_clock": "event-clock"},
            ]
        )
        record.setdefault("meta", {})["timebase"] = "meta-clock"
        result = _run_with_record(record)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn(validate_run.SPIKE_CLOCK_DOMAIN_MISMATCH, result.stderr)
        self.assertIn("meta-clock", result.stderr)

    def test_a_record_clock_matching_its_events_is_one_domain(self):
        """The enclosing declaration must not manufacture a second domain."""
        record = self._record_with(
            [
                {"channel": "a", "t_rel_ms": 1.0, "source_clock": "one-clock"},
                {"channel": "b", "t_rel_ms": 2.0, "source_clock": "one-clock"},
            ],
            clock_id="one-clock",
        )
        result = _run_with_record(record)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_a_record_clock_over_unannotated_events_is_one_domain(self):
        record = self._record_with(
            [
                {"channel": "a", "t_rel_ms": 1.0},
                {"channel": "b", "t_rel_ms": 2.0},
            ],
            clock_id="record-clock",
        )
        result = _run_with_record(record)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_declared_clock_domains_reads_the_record_meta_and_events(self):
        """Unit-level parity with curate_bridge's three-container namespace."""
        events = [{"t_rel_ms": 1.0, "source_clock": "event-clock"}]
        record = {"clock_id": "record-clock", "meta": {"timebase": "meta-clock"}}
        self.assertEqual(
            validate_run.declared_clock_domains(events, record),
            {'"event-clock"', '"record-clock"', '"meta-clock"'},
        )
        self.assertEqual(
            validate_run.declared_clock_domains(events), {'"event-clock"'}
        )

    def test_one_clock_domain_under_aliased_field_names_passes(self):
        # Different alias fields carrying the same identifier name one domain.
        self._accept(
            [
                {"channel": "a", "t_rel_ms": 1.0, "clock_id": "sensor-a"},
                {"channel": "b", "t_rel_ms": 2.0, "timebase": "sensor-a"},
            ]
        )

    def test_a_partly_annotated_stream_keeps_its_single_clock_domain(self):
        # An event that names no clock does not invent a second domain.
        self._accept(
            [
                {"channel": "a", "t_rel_ms": 1.0, "clock_id": "sensor-a"},
                {"channel": "b", "t_rel_ms": 2.0},
            ]
        )

    def test_a_multi_clock_stream_is_still_ordered_once_domains_agree(self):
        self._reject(
            [
                {"channel": "a", "t_rel_ms": 9.0, "clock_id": "sensor-a"},
                {"channel": "b", "t_rel_ms": 1.0, "clock_id": "sensor-a"},
            ],
            validate_run.SPIKE_ORDER_MISMATCH,
            absent=(validate_run.SPIKE_CLOCK_DOMAIN_MISMATCH,),
            errors=1,
        )

    def test_unsorted_stream_is_rejected_once(self):
        self._reject(
            [
                {"channel": "a", "t_rel_ms": 9.0, "amplitude": 0.4},
                {"channel": "b", "t_rel_ms": 1.0, "amplitude": 0.3},
            ],
            "not globally non-decreasing",
            errors=1,
        )

    def test_untimed_event_is_rejected(self):
        self._reject(
            [{"channel": "a", "amplitude": 0.4}],
            "needs finite t_rel_ms or t_ms",
        )

    def test_event_with_both_timestamp_keys_is_rejected(self):
        self._reject(
            [{"t_rel_ms": 1.0, "t_ms": 1.0}],
            "must use exactly one of t_rel_ms or t_ms",
        )

    def test_invalid_timestamp_cannot_be_shadowed_by_valid_alias(self):
        self._reject(
            [{"t_rel_ms": "bad", "t_ms": 1.0}],
            "t_rel_ms must be a finite number",
            "must use exactly one of t_rel_ms or t_ms",
        )

    def test_oversized_timestamp_is_rejected_without_crashing(self):
        self._reject(
            [{"t_rel_ms": 10**400}],
            "t_rel_ms must be a finite number",
            absent=("Traceback",),
        )

    def test_large_integer_timestamp_order_preserves_precision(self):
        self._reject(
            [
                {"t_rel_ms": 9007199254740993},
                {"t_rel_ms": 9007199254740992},
            ],
            validate_run.SPIKE_ORDER_MISMATCH,
            "9007199254740993 -> 9007199254740992",
            errors=1,
        )

    def test_non_array_stream_is_rejected(self):
        self._reject({"channel": "a"}, "spike_events must be an array")

    def test_channel_and_amplitude_stay_a_bridge_only_requirement(self):
        # Trajectory streams are annotated more loosely than bridge streams;
        # requiring the bridge keys here would flag records the promotion lane
        # already round-trips (pipelines/promote.py sorts bare {channel, t_ms}).
        self._accept([{"t_rel_ms": 1.0}])

    def test_optional_event_fields_follow_schema_types_when_present(self):
        cases = (
            ({"t_rel_ms": 1.0, "channel": False}, "channel must be a non-empty string"),
            ({"t_rel_ms": 1.0, "channel": "   "}, "channel must be a non-empty string"),
            ({"t_rel_ms": 1.0, "amplitude": "bad"}, "amplitude must be a finite number"),
            ({"t_rel_ms": 1.0, "amplitude": False}, "amplitude must be a finite number"),
        )
        for event, marker in cases:
            with self.subTest(event=event):
                self._reject([event], marker)

    def test_bridge_stream_still_requires_channel_and_amplitude(self):
        result = self._validate_bridge(self._bridge([{"t_rel_ms": 1.0}]))
        self.assertEqual(result.returncode, 1, result.stderr)
        for key in validate_run.BRIDGE_SPIKE_EVENT_KEYS:
            self.assertIn(f"missing '{key}'", result.stderr)

    def test_bridge_event_field_types_are_enforced(self):
        result = self._validate_bridge(
            self._bridge([{"channel": False, "amplitude": "bad", "t_rel_ms": 1.0}])
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("channel must be a non-empty string", result.stderr)
        self.assertIn("amplitude must be a finite number", result.stderr)

if __name__ == "__main__":
    unittest.main()
