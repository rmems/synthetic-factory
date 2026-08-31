#!/usr/bin/env python3
"""Tests for composing the five curation lanes into one curated destination."""

import copy
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

TESTS = Path(__file__).resolve().parent
REPO = TESTS.parent
for _path in (TESTS, REPO / "pipelines"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import compose_curated  # noqa: E402
import curate_agentic  # noqa: E402
import curate_bridge  # noqa: E402
import curate_coding  # noqa: E402
import curate_identity  # noqa: E402
import curate_preferences  # noqa: E402
import curate_rewards  # noqa: E402
import training_audit  # noqa: E402
from compose_curated_test_support import (  # noqa: E402
    bridge_pair,
    build_source_run,
    episode,
    multi_agent,
    preference_pair,
    read_jsonl,
    safety_case,
    thalamic,
    write_jsonl,
)


class ComposeCurated(unittest.TestCase):
    def test_composes_every_lane_into_a_training_ready_tree(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = build_source_run(root / "run")
            summary = compose_curated.compose_run(source, root / "curated")

            self.assertEqual(summary["counts"]["source_records"], 8)
            self.assertEqual(summary["counts"]["retained"], 7)
            self.assertEqual(summary["counts"]["excluded"], 1)
            self.assertEqual(summary["lane_order"], list(compose_curated.LANE_ORDER))
            self.assertEqual(
                summary["transforms"]["preferences"]["trajectory"]["implementation"],
                (
                    "reviewed_module"
                    if compose_curated.curate_trajectory_preferences is not None
                    else "compatible_core"
                ),
            )
            self.assertTrue(summary["audit"]["training_ready"], summary["audit"]["blockers"])
            self.assertEqual(summary["audit"]["blockers"], [])
            self.assertEqual(summary["audit"]["records"], 7)

            records_dir = root / "curated" / compose_curated.RECORDS_DIRNAME
            report = training_audit.audit_run(records_dir)
            self.assertTrue(report["training_ready"], report["blockers"])
            self.assertEqual(report["identity"]["coverage_pct"], 100.0)
            self.assertEqual(report["preferences"]["context_purity_pct"], 100.0)
            self.assertEqual(report["episodes"]["hidden_thought_fields"], 0)

            self._assert_every_record_has_a_canonical_id(records_dir)
            self._assert_bridge_stream_is_ordered(records_dir)
            self._assert_coding_lane_grounded_the_episodes(records_dir)
            self._assert_rewards_lane_annotated_the_thalamic_records(records_dir)

            # The impure preference pair is the only exclusion.
            self.assertEqual(
                sum(summary["exclusions"].values()), summary["counts"]["excluded"]
            )
            self.assertIn(
                "PROPOSED_ACTION_CONTEXT_DIVERGES", summary["exclusions"]
            )

    def _assert_every_record_has_a_canonical_id(self, records_dir):
        # Identity ran first: every retained record carries a canonical ID.
        for path in records_dir.rglob("*.jsonl"):
            for record in read_jsonl(path):
                self.assertTrue(record["id"].startswith("sfcur-"), record["id"])

    def _assert_bridge_stream_is_ordered(self, records_dir):
        # Identity now refuses unsorted spikes, so the composed bridge
        # stream is the already-ordered identity-valid form.
        bridge = read_jsonl(
            records_dir / "neuromorphic-event-language-bridge" / "batch-r01.jsonl"
        )[0]
        self.assertEqual(
            [event["t_rel_ms"] for event in bridge["spike_events"]], [1.0, 2.0, 3.0]
        )

    def _assert_coding_lane_grounded_the_episodes(self, records_dir):
        # Coding stripped the hidden thought and grounded a decision basis.
        episodes = read_jsonl(
            records_dir / "agentic-coding-trajectory-factory" / "batch-r01.jsonl"
        )
        self.assertEqual(len(episodes), 2)
        for record in episodes:
            self.assertNotIn("thought", record["steps"][0])
            self.assertTrue(record["steps"][0]["decision_basis"].strip())

    def _assert_rewards_lane_annotated_the_thalamic_records(self, records_dir):
        # Rewards annotated the records that actually carry reward payloads.
        thalamic_records = read_jsonl(
            records_dir / "thalamic-trajectory-factory" / "batch-r01.jsonl"
        )
        for record in thalamic_records:
            annotation = record["reward_training"]
            self.assertEqual(annotation["ontology_version"], "reward-ontology-v1")
            self.assertTrue(annotation["source_sidecar_id"])

    def test_registered_agentic_shapes_strip_hidden_fields_before_strict_audit(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            multi = multi_agent()
            multi["transcript"][1]["inner_monologue"] = "hidden review reasoning"
            safety = safety_case()
            safety["steps"][0]["thought"] = "hidden refusal reasoning"
            source = root / "run"
            write_jsonl(
                source / "multi-agent-coordination-factory" / "batch-r01.jsonl",
                [multi],
            )
            write_jsonl(
                source / "safety-calibration-factory" / "batch-r01.jsonl",
                [safety],
            )

            summary = compose_curated.compose_run(source, root / "curated")

            self.assertTrue(summary["audit"]["training_ready"], summary["audit"])
            self.assertEqual(summary["audit"]["blockers"], [])
            self.assertEqual(
                summary["transforms"]["coding"]["registered_agentic"],
                {
                    "name": curate_agentic.TRANSFORM_NAME,
                    "version": curate_agentic.TRANSFORM_VERSION,
                    "record_kinds": ["multi_agent", "safety_case"],
                },
            )
            records_dir = root / "curated" / compose_curated.RECORDS_DIRNAME
            report = training_audit.audit_run(records_dir)
            self.assertTrue(report["training_ready"], report["blockers"])
            self.assertEqual(report["episodes"]["hidden_thought_fields"], 0)
            for output in records_dir.rglob("*.jsonl"):
                for record in read_jsonl(output):
                    self.assertFalse(curate_agentic.contains_hidden_thought_key(record))

            manifest = read_jsonl(
                root / "curated" / summary["manifest"]["path"]
            )
            coding_stages = [
                next(stage for stage in entry["stages"] if stage["lane"] == "coding")
                for entry in manifest
            ]
            self.assertEqual(
                {stage["transform_name"] for stage in coding_stages},
                {curate_agentic.TRANSFORM_NAME},
            )
            self.assertTrue(
                all(
                    curate_agentic.REASON_THOUGHT_REMOVED in stage["reason_codes"]
                    for stage in coding_stages
                )
            )

    def test_registered_agentic_shapes_strip_the_full_hidden_reasoning_vocabulary(self):
        """Codex #97 P2: agentic curation must catch what the audit catches.

        ``curate_agentic`` used to recognise only the narrow scratch-pad
        vocabulary (thought/chain_of_thought/scratch/inner_monologue).  A
        multi_agent or safety_case record carrying the coding-factory key
        ``reasoning`` or an ``internal_reasoning*`` variant was retained by
        this lane with the private field intact, then rejected by
        ``training_audit``'s broader hidden-reasoning check -- an
        otherwise-repairable record that composition could never make
        training-ready. Both keys must now be stripped here too.
        """
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            multi = multi_agent()
            multi["transcript"][1]["reasoning"] = "hidden coding-style reasoning"
            safety = safety_case()
            safety["steps"][0]["internal_reasoning_optimizer"] = "hidden optimizer trace"
            source = root / "run"
            write_jsonl(
                source / "multi-agent-coordination-factory" / "batch-r01.jsonl",
                [multi],
            )
            write_jsonl(
                source / "safety-calibration-factory" / "batch-r01.jsonl",
                [safety],
            )

            summary = compose_curated.compose_run(source, root / "curated")

            self.assertTrue(summary["audit"]["training_ready"], summary["audit"])
            self.assertEqual(summary["audit"]["blockers"], [])
            records_dir = root / "curated" / compose_curated.RECORDS_DIRNAME
            report = training_audit.audit_run(records_dir)
            self.assertTrue(report["training_ready"], report["blockers"])
            self.assertEqual(report["episodes"]["hidden_thought_fields"], 0)
            for output in records_dir.rglob("*.jsonl"):
                for record in read_jsonl(output):
                    self.assertFalse(curate_agentic.contains_hidden_thought_key(record))
                    self.assertNotIn("reasoning", json.dumps(record))
                    self.assertNotIn("internal_reasoning_optimizer", json.dumps(record))

    def test_lane_gates_match_each_lane_predicate(self):
        record = thalamic("gate")
        decision = compose_curated.compose_record(
            record,
            source_path="thalamic-trajectory-factory/batch-r01.jsonl",
            source_line=1,
            source_sha256="0" * 64,
        )
        self.assertEqual(decision.action, "retained")
        actions = {stage["lane"]: stage["action"] for stage in decision.stages}
        self.assertEqual(actions["bridge"], compose_curated.ACTION_NOT_APPLICABLE)
        self.assertEqual(actions["preferences"], compose_curated.ACTION_NOT_APPLICABLE)
        self.assertEqual(actions["coding"], compose_curated.ACTION_NOT_APPLICABLE)
        self.assertEqual(actions["identity"], compose_curated.ACTION_RETAINED)
        self.assertEqual(actions["rewards"], compose_curated.ACTION_RETAINED)

        unstamped = thalamic("unstamped")
        unstamped["meta"].pop("factory")
        refused = compose_curated.compose_record(
            unstamped,
            source_path="thalamic-trajectory-factory/batch-r01.jsonl",
            source_line=1,
            source_sha256="0" * 64,
        )
        self.assertEqual(refused.action, compose_curated.ACTION_EXCLUDED)
        self.assertEqual(
            refused.reason_codes,
            ("identity.factory_path_payload_mismatch",),
        )

        # The compose gates must agree with the gates the lanes apply themselves.
        samples = [
            thalamic("x"),
            bridge_pair(),
            preference_pair(),
            episode(),
            {"reward_delta": 1.0},
            {"steps": "not-a-list"},
            {"language_view": {}, "spike_events": "not-a-list"},
        ]
        for sample in samples:
            self.assertEqual(
                compose_curated.is_preference_record(sample),
                curate_preferences._is_preference_candidate(sample),
                sample,
            )
            bridge_decision = curate_bridge.curate_record(
                sample,
                source_path="factory/batch-r01.jsonl",
                source_line=1,
                source_hash="0" * 64,
            )
            rejected_as_bridge = (
                curate_bridge.REASON_NOT_BRIDGE
                in bridge_decision.manifest["reason_codes"]
            )
            self.assertEqual(
                compose_curated.is_bridge_record(sample), not rejected_as_bridge, sample
            )
            _curated, coding_manifest = curate_coding.curate_episode(sample)
            rejected_as_episode = coding_manifest["reason_codes"] == [
                curate_coding.REASON_STEPS_NOT_ARRAY
            ]
            self.assertEqual(
                compose_curated.is_episode_record(sample),
                not rejected_as_episode,
                sample,
            )

    def test_bridge_order_error_fragment_matches_the_validator(self):
        """The deferral below keys off this exact validator phrasing."""

        import validate_run

        events = [
            {"channel": "c", "amplitude": 1.0, "t_rel_ms": 3.0},
            {"channel": "c", "amplitude": 1.0, "t_rel_ms": 1.0},
        ]
        errors = validate_run.check_spike_order(events, "record")
        self.assertTrue(errors)
        self.assertTrue(
            all(
                compose_curated.BRIDGE_ORDER_ERROR_FRAGMENT in error
                for error in errors
            ),
            errors,
        )

    def test_unsorted_bridge_streams_reach_the_repair_instead_of_being_dropped(self):
        """Codex #97 P2: identity must not make a repairable order terminal.

        ``curate_bridge`` deterministically stable-sorts a single-clock stream
        and records BRIDGE_EVENTS_STABLE_SORTED_SINGLE_GLOBAL_CLOCK. Identity
        applies the same invariant first, so a terminal refusal there drops an
        explicitly repairable supported record before its lane ever runs.
        """

        decision = compose_curated.compose_record(
            bridge_pair(unsorted=True),
            source_path="neuromorphic-event-language-bridge/batch-r01.jsonl",
            source_line=1,
            source_sha256="0" * 64,
        )

        self.assertEqual(decision.action, compose_curated.ACTION_RETAINED)
        identity_stage = next(
            stage for stage in decision.stages if stage["lane"] == "identity"
        )
        self.assertTrue(identity_stage["detail"]["bridge_order_deferred_to_bridge_lane"])
        bridge_stage = next(
            stage for stage in decision.stages if stage["lane"] == "bridge"
        )
        # The bridge lane, not identity, owns and records the repair.
        self.assertIn(curate_bridge.REASON_REPAIRED, bridge_stage["reason_codes"])
        times = [event["t_rel_ms"] for event in decision.record["spike_events"]]
        self.assertEqual(times, sorted(times))

    def test_bridge_deferral_does_not_smuggle_records_the_lane_refuses(self):
        """Only a stream the bridge lane will actually repair may be deferred."""

        record = bridge_pair(unsorted=True)
        record["meta"]["event_order"] = "explicit"
        decision = compose_curated.compose_record(
            record,
            source_path="neuromorphic-event-language-bridge/batch-r01.jsonl",
            source_line=1,
            source_sha256="0" * 64,
        )

        self.assertEqual(decision.action, compose_curated.ACTION_EXCLUDED)
        identity_stage = next(
            stage for stage in decision.stages if stage["lane"] == "identity"
        )
        self.assertNotIn(
            "bridge_order_deferred_to_bridge_lane", identity_stage["detail"]
        )

    def test_coding_wrap_records_reach_the_coding_lane(self):
        """A wrap keeps its steps at executed_action.steps; compose must route it."""

        from coding_curation_helpers import visible_step, wrap_record

        record = wrap_record([visible_step()])
        record["meta"]["factory"] = "thalamic-trajectory-factory"
        self.assertIsNone(record.get("steps"))
        self.assertTrue(compose_curated.is_episode_record(record))

        decision = compose_curated.compose_record(
            record,
            source_path="thalamic-trajectory-factory/batch-r02.jsonl",
            source_line=1,
            source_sha256="0" * 64,
        )
        coding_stage = next(
            stage for stage in decision.stages if stage["lane"] == "coding"
        )
        self.assertNotEqual(
            coding_stage["action"], compose_curated.ACTION_NOT_APPLICABLE
        )
        self.assertEqual(coding_stage["transform_name"], curate_coding.TRANSFORM_NAME)
        if decision.record is not None:
            steps = decision.record[curate_coding.WRAP_STEPS_PARENT]["steps"]
            self.assertNotIn("thought", steps[0])


    def test_rewardless_record_adopts_the_curators_annotation_stripped_result(self):
        stale, _sidecar = curate_rewards.curate_record({"payload": "now removed"})
        record = {
            "id": "legacy-rewardless",
            "payload": "now removed",
            "meta": {"factory": "thalamic-trajectory-factory", "round": 1},
            "reward_training": stale["reward_training"],
        }
        curated = {
            "id": "sfcur-rewardless",
            "payload": "now removed",
            "meta": copy.deepcopy(record["meta"]),
            "provenance": {"kind": "designed", "claimed": None, "basis": "test"},
            "reward_training": stale["reward_training"],
        }
        mapping = {
            "action": "retained",
            "reason_codes": ["identity.assigned", "provenance.canonicalized"],
            "record_kind": "thalamic",
            "output_id": curated["id"],
            "id_mappings": [
                {
                    "owner_path": "/",
                    "output_id": curated["id"],
                    "original_ids": [{"path": "/id", "value": "legacy-rewardless"}],
                }
            ],
        }

        with mock.patch.object(
            curate_identity,
            "curate_record",
            return_value=curate_identity.CurationResult(
                "retained", curated, mapping
            ),
        ):
            decision = compose_curated.compose_record(
                record,
                source_path="thalamic-trajectory-factory/batch-r01.jsonl",
                source_line=1,
                source_sha256="0" * 64,
            )

        self.assertEqual(decision.action, compose_curated.ACTION_RETAINED)
        self.assertNotIn(curate_rewards.ANNOTATION_FIELD, decision.record)
        self.assertIsNone(decision.reward_sidecar)
        rewards = next(stage for stage in decision.stages if stage["lane"] == "rewards")
        self.assertEqual(rewards["action"], compose_curated.ACTION_NOT_APPLICABLE)
        self.assertEqual(rewards["source_reward_count"], 0)

    def test_reward_sidecar_restores_the_final_post_coding_record(self):
        decision = compose_curated.compose_record(
            episode("final-hash"),
            source_path="agentic-coding-trajectory-factory/batch-r01.jsonl",
            source_line=1,
            source_sha256="0" * 64,
        )

        self.assertEqual(decision.stages[-1]["lane"], "rewards")
        self.assertNotIn("thought", decision.record["steps"][0])
        expected = copy.deepcopy(decision.record)
        expected.pop(curate_rewards.ANNOTATION_FIELD)
        self.assertEqual(
            curate_rewards.restore_source_record(
                decision.record, decision.reward_sidecar
            ),
            expected,
        )

    def test_source_jsonl_uses_lf_only_and_preserves_unicode_separators(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run" / "thalamic-trajectory-factory"
            source.mkdir(parents=True)
            first = thalamic("unicode-separators")
            first["state"]["domain"] = "line\u2028separator\u2029paragraph"
            write_jsonl(source / "batch-r01.jsonl", [first, thalamic("plain")])

            summary = compose_curated.compose_run(root / "run", root / "curated")
            output = (
                root
                / "curated"
                / compose_curated.RECORDS_DIRNAME
                / "thalamic-trajectory-factory"
                / "batch-r01.jsonl"
            ).read_text(encoding="utf-8")
            records = [json.loads(line) for line in output.split("\n") if line]

            self.assertEqual(summary["counts"]["source_records"], 2)
            self.assertEqual(summary["audit"]["records"], 2)
            self.assertTrue(
                summary["audit"]["training_ready"], summary["audit"]["blockers"]
            )
            self.assertEqual(len(records), 2)
            self.assertEqual(
                records[0]["state"]["domain"], first["state"]["domain"]
            )


    def test_unsupported_and_unparseable_lines_are_excluded_with_reasons(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run" / "thalamic-trajectory-factory"
            source.mkdir(parents=True)
            (source / "batch-r01.jsonl").write_text(
                json.dumps(thalamic("keep"))
                + "\n"
                + "{not json\n"
                + '{"nan": NaN}\n'
                + json.dumps({"unknown": "shape"})
                + "\n"
                + "\n",
                encoding="utf-8",
            )
            summary = compose_curated.compose_run(root / "run", root / "curated")

            self.assertEqual(summary["counts"]["source_records"], 4)
            self.assertEqual(summary["counts"]["blank_lines"], 1)
            self.assertEqual(summary["counts"]["retained"], 1)
            self.assertEqual(summary["counts"]["excluded"], 3)
            self.assertEqual(
                summary["exclusions"],
                {
                    compose_curated.REASON_INVALID_JSON: 2,
                    "identity.unsupported_record_shape": 1,
                },
            )


    def test_uncommitted_marker_mode_batches_never_compose(self):
        """Codex #97 P1: composition honors round-transaction visibility.

        Once a factory enters marker mode, only batches named by committed
        round manifests are corpus — census and the training audit already
        hide the rest, so composing (and replaying) an uncommitted batch
        would certify records the round contract says do not exist yet.
        """
        from training_audit_test_helpers import commit_marker_batch
        from training_audit_test_helpers import thalamic as marker_thalamic
        from training_audit_test_helpers import write as marker_write

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run"
            factory = source / "thalamic-trajectory-factory"
            committed = factory / "batch-r01.jsonl"
            marker_write(committed, [marker_thalamic("committed-1")])
            commit_marker_batch(factory, committed)
            marker_write(
                factory / "batch-r02.jsonl", [marker_thalamic("uncommitted-1")]
            )

            self.assertEqual(
                compose_curated.source_jsonl_members(source),
                ("thalamic-trajectory-factory/batch-r01.jsonl",),
            )
            summary = compose_curated.compose_run(source, root / "curated")

            self.assertEqual(summary["counts"]["source_records"], 1)
            self.assertEqual(summary["counts"]["source_files"], 1)

    def test_foreign_mill_records_are_quarantined_before_identity(self):
        """Codex #97 P1: mill ownership resolves before identity rewrites ids.

        A destination-stamped leftover mill is identifiable only by its
        foreign id prefix and goal family. Composing it record-by-record let
        identity replace that prefix with a canonical digest, so the curated
        tree audited clean and the export shipped the foreign record while
        reporting training_ready.
        """
        from curate_agentic_fixtures import (
            DEST_STAMPED_MILL,
            STAMPEDE_CONTROLS,
            write_mill_run,
        )

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run"
            source.mkdir()
            write_mill_run(source, list(STAMPEDE_CONTROLS) + [DEST_STAMPED_MILL])

            summary = compose_curated.compose_run(source, root / "curated")

            self.assertEqual(summary["counts"]["source_records"], 5)
            self.assertEqual(summary["counts"]["excluded"], 1)
            self.assertIn("FOREIGN_MILL_ID_PREFIX", summary["exclusions"])
            records_dir = root / "curated" / compose_curated.RECORDS_DIRNAME
            emitted = "".join(
                path.read_text(encoding="utf-8")
                for path in records_dir.rglob("*.jsonl")
            )
            self.assertNotIn(DEST_STAMPED_MILL["goal"], emitted)
            manifest = read_jsonl(root / "curated" / summary["manifest"]["path"])
            quarantined = [
                entry
                for entry in manifest
                if "FOREIGN_MILL_ID_PREFIX" in entry["reason_codes"]
            ]
            self.assertEqual(len(quarantined), 1)
            self.assertEqual(quarantined[0]["action"], "excluded")
            self.assertEqual(
                quarantined[0]["stages"][0]["classification"],
                "foreign_mill_quarantined",
            )

    def test_empty_composition_is_never_training_ready(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "run" / "thalamic-trajectory-factory"
            source.mkdir(parents=True)
            (source / "batch-r01.jsonl").write_text(
                json.dumps({"unknown": "shape"}) + "\n", encoding="utf-8"
            )
            summary = compose_curated.compose_run(root / "run", root / "curated")

            self.assertEqual(summary["counts"]["retained"], 0)
            self.assertFalse(summary["audit"]["training_ready"])
            self.assertEqual(
                summary["audit"]["blockers"], [compose_curated.REASON_EMPTY_CORPUS]
            )

    def test_composition_is_deterministic_and_leaves_the_source_untouched(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = build_source_run(root / "run")
            before = {
                path: path.read_bytes() for path in sorted(source.rglob("*.jsonl"))
            }

            first = compose_curated.compose_run(source, root / "curated-a")
            second = compose_curated.compose_run(source, root / "curated-b")

            self.assertEqual(first["manifest"]["sha256"], second["manifest"]["sha256"])
            self.assertEqual(
                first["reward_sidecars"]["sha256"], second["reward_sidecars"]["sha256"]
            )
            self.assertEqual(
                [item["sha256"] for item in first["outputs"]],
                [item["sha256"] for item in second["outputs"]],
            )
            self.assertEqual(first["counts"], second["counts"])
            self.assertEqual(
                {path: path.read_bytes() for path in sorted(source.rglob("*.jsonl"))},
                before,
            )


    def test_cli_reports_strict_blockers_and_refuses_existing_destinations(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = build_source_run(root / "run")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                status = compose_curated.main(
                    ["--strict", str(source), str(root / "curated")]
                )
            self.assertEqual(status, 0)
            self.assertTrue(json.loads(stdout.getvalue())["audit"]["training_ready"])

            stderr = io.StringIO()
            with redirect_stdout(io.StringIO()), redirect_stderr(stderr):
                status = compose_curated.main([str(source), str(root / "curated")])
            self.assertEqual(status, 2)
            self.assertIn("refusing to overwrite", stderr.getvalue())

            blocked = root / "blocked-run" / "thalamic-trajectory-factory"
            blocked.mkdir(parents=True)
            (blocked / "batch-r01.jsonl").write_text(
                json.dumps({"unknown": "shape"}) + "\n", encoding="utf-8"
            )
            stderr = io.StringIO()
            with redirect_stdout(io.StringIO()), redirect_stderr(stderr):
                status = compose_curated.main(
                    ["--strict", str(root / "blocked-run"), str(root / "curated-blocked")]
                )
            self.assertEqual(status, 1)
            self.assertIn(compose_curated.REASON_EMPTY_CORPUS, stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
