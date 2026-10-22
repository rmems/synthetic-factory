"""Compose fails closed on eval-denylisted and do-not-train sources, and export replays it (#494)."""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))
import compose_curated  # noqa: E402
import compose_eval_gate as gate  # noqa: E402
import eval_exclusion_lists as lists  # noqa: E402
import eval_exclusion_policy as policy  # noqa: E402
import export_hf  # noqa: E402
from compose_contract import ComposeDecision, ComposeError  # noqa: E402
from export_contract import ExportError  # noqa: E402

FIXTURES = REPO / "tests" / "fixtures" / "eval-exclusion"
MANIFEST = "manifest/compose-manifest.jsonl"
STAGE = {"lane": "identity", "action": "retained", "reason_codes": [], "detail": {}}


def fixture_policy():
    return policy.load_policy(
        FIXTURES / "eval-denylist.json", FIXTURES / "do-not-train.json",
        FIXTURES / "repo-aliases.json",
    )


def code_repair_record(repository="TheAlgorithms/Python", program_id="tap-0"):
    upstream = {"repository": repository, "commit": "2067ce6dfb3b0426a88c7a40531e355a5c703cff"}
    return {"family": "python-function-repair", "id": "cr-1",
            "scenario": {"source": {"program_id": program_id, "upstream": upstream}}}


def real_record(environment):
    return {"source_kind": "real_public_engineering", "environment": environment,
            "oracle": {"repo_commit": "abc123"}}


def retained(record):
    return ComposeDecision("retained", record, ("lane.reason",), (dict(STAGE),),
                           {"sidecar_id": "s"}, record.get("id"))


def _jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def write_policy(root, *, denylist=None, do_not_train=None):
    """A reviewed policy in ``root`` carrying the given entries over the committed cache."""

    paths = []
    for slot, values in ((lists.LIST_EVAL_DENYLIST, denylist), (lists.LIST_DO_NOT_TRAIN,
                                                                do_not_train)):
        values = values or {}
        document = {
            "schema_version": lists.LIST_SCHEMA_VERSION, "list": slot, "status": "reviewed",
            "note": "test-only list",
            **{key: sorted(values.get(key, ())) for key in lists.VALUE_KEYS},
        }
        path = Path(root) / f"{slot}.json"
        path.write_bytes(lists.canonical_bytes(document))
        paths.append(path)
    return policy.load_policy(*paths, policy.ALIAS_CACHE_PATH)


class GateDecisionTests(unittest.TestCase):
    def setUp(self):
        self.policy = fixture_policy()

    def test_records_without_a_public_source_claim_are_untouched(self):
        for record in ({"goal": "g", "steps": []}, {"source_kind": "synthetic"}, ["x"]):
            with self.subTest(record=record):
                decision = ComposeDecision("retained", record, (), (), None, None)
                self.assertIs(gate.apply_gate(decision, self.policy), decision)
        excluded = ComposeDecision("excluded", None, ("identity.x",), (), None, None)
        self.assertIs(gate.apply_gate(excluded, self.policy), excluded)

    def test_clean_public_source_keeps_its_record_and_gains_gate_evidence(self):
        decision = gate.apply_gate(retained(code_repair_record()), self.policy)
        self.assertEqual(decision.action, "retained")
        self.assertEqual(decision.reason_codes, ("lane.reason",))
        self.assertEqual(decision.reward_sidecar, {"sidecar_id": "s"})
        stage = decision.stages[-1]
        self.assertEqual((stage["lane"], stage["action"], stage["reason_codes"]),
                         ("eval_exclusion", "retained", []))
        self.assertEqual(stage["detail"]["canonical_repo"], "thealgorithms/python")
        self.assertEqual(stage["detail"]["source_repo"], "TheAlgorithms/Python")
        self.assertEqual(stage["detail"]["rule"], "code_repair_upstream")

    def test_denylisted_program_refuses_the_shard_instead_of_dropping_the_row(self):
        with self.assertRaisesRegex(ComposeError, "refuse the shard"):
            gate.apply_gate(
                retained(code_repair_record(program_id="tap-fixture-held-out")), self.policy
            )

    def test_real_record_is_resolved_through_the_alias_cache_before_matching(self):
        renamed = real_record({"task_id": "clap-rs__clap-941", "source_repo": "kbknapp/clap-rs"})
        with self.assertRaisesRegex(ComposeError, "refuse the shard"):
            gate.apply_gate(retained(renamed), self.policy)
        evaluation = self.policy.evaluate(
            policy.SourceIdentity("kbknapp/clap-rs", task_id="clap-rs__clap-941")
        )
        self.assertEqual(evaluation.canonical_repo, "clap-rs/clap")
        self.assertEqual(evaluation.reason_codes, (policy.REASON_EVAL_DENYLISTED,))

    def test_thalamic_relay_does_not_capture_its_trajectories_repo(self):
        trajectories = real_record({"task_id": "t-1",
                                    "source_repo": "rmems/thalamic-relay-trajectories"})
        self.assertEqual(gate.apply_gate(retained(trajectories), self.policy).action, "retained")
        relay = real_record({"task_id": "t-1", "source_repo": "rmems/thalamic-relay"})
        with self.assertRaisesRegex(ComposeError, "refuse the shard"):
            gate.apply_gate(retained(relay), self.policy)

    def test_denylist_hit_on_any_record_kind_refuses_the_shard(self):
        episode = {"goal": "g", "steps": [], "meta": {"program_id": "tap-fixture-held-out"}}
        preference = {"chosen": {"program_id": "tap-fixture-held-out"}, "rejected": {"x": 1}}
        for record in (episode, preference):
            with self.subTest(record=record):
                with self.assertRaisesRegex(ComposeError, "refuse the shard"):
                    gate.apply_gate(retained(record), self.policy)

    def test_board_repo_trajectory_refuses_the_shard(self):
        trajectory = {
            "goal": "fix the board", "steps": [{"action": "edit"}],
            "environment": {"source_repo": "clap-rs/clap"},
        }
        with self.assertRaisesRegex(ComposeError, "refuse the shard"):
            gate.apply_gate(retained(trajectory), self.policy)

    def test_preference_board_repo_refuses_the_shard(self):
        preference = {"chosen": {"source_repo": "clap-rs/clap"}, "rejected": {"goal": "other"}}
        with self.assertRaisesRegex(ComposeError, "refuse the shard"):
            gate.apply_gate(retained(preference), self.policy)

    def test_instance_id_maps_to_denylisted_repo_and_refuses_the_shard(self):
        record = {"instance_id": "clap-rs__clap-5873"}
        with self.assertRaisesRegex(ComposeError, "refuse the shard"):
            gate.apply_gate(retained(record), self.policy)

    def test_spike_viz_episode_is_not_a_denylist_repo_hit(self):
        episode = {"goal": "g", "steps": [], "meta": {"repository": "rmems/spike-viz"}}
        self.assertEqual(gate.apply_gate(retained(episode)).action, "retained")
        self.assertEqual(gate.apply_gate(retained(episode), self.policy).action, "retained")

    def test_unresolvable_real_or_code_repair_sources_fail_closed(self):
        cases = {
            "missing repo": real_record({"task_id": "t-1"}),
            "provenance claim": {"provenance": {"source_kind": "real_public_engineering"}},
            "uncached repo": real_record({"task_id": "t-1", "source_repo": "someone/else"}),
            "code repair without upstream": {"family": "python-function-repair",
                                             "scenario": {"source": {}}},
        }
        for label, record in cases.items():
            with self.subTest(label=label):
                decision = gate.apply_gate(retained(record), self.policy)
                self.assertEqual(decision.reason_codes, (policy.REASON_REPO_UNRESOLVED,))
                self.assertIsNone(decision.record)
        invalid = gate.apply_gate(retained(code_repair_record("TheAlgorithms/Python.git/x")),
                                  self.policy)
        self.assertEqual(invalid.reason_codes, (policy.REASON_REPO_INVALID,))

    def test_gate_reads_the_loaded_policy_live(self):
        record = code_repair_record(program_id="tap-fixture-held-out")
        self.assertEqual(gate.apply_gate(retained(record)).action, "retained")
        with mock.patch.object(policy, "ACTIVE_POLICY", self.policy):
            with self.assertRaisesRegex(ComposeError, "refuse the shard"):
                gate.apply_gate(retained(record))
            self.assertEqual(gate.descriptor()["eval_denylist"]["status"], "reviewed")

    def test_published_summary_must_declare_exactly_the_committed_policy(self):
        expected = gate.descriptor()
        self.assertEqual(expected["name"], "eval-exclusion-gate")
        self.assertEqual(expected["version"], 1)
        self.assertEqual(gate.require_published({"eval_exclusion": expected}), expected)
        stale = dict(expected, eval_denylist=dict(expected["eval_denylist"], sha256="0" * 64))
        for summary in ({}, {"eval_exclusion": stale}, {"eval_exclusion": None}):
            with self.subTest(summary=summary), self.assertRaisesRegex(ComposeError, "recompose"):
                gate.require_published(summary)


class GateImportIdentityTests(unittest.TestCase):
    """Direct and package imports must share one policy object, or patching it would split."""

    NAMES = ("compose_eval_gate", "eval_exclusion_aliases", "eval_exclusion_lists",
             "eval_exclusion_policy", "eval_exclusion_subject", "repo_identity")

    def test_every_gate_module_is_one_object_in_both_import_modes(self):
        from tests import pipeline_import_catalog

        for name in self.NAMES:
            with self.subTest(name=name):
                self.assertIs(pipeline_import_catalog.load_direct(name),
                              pipeline_import_catalog.load_package(name))
        self.assertIs(compose_curated._run_impl._eval_gate, gate)
        self.assertIs(gate._policy, policy)


class ComposeIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from tests.code_repair_admission_test_support import sealed_published_factory
        cls.published_run = sealed_published_factory().parent

    def setUp(self):
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.root = Path(scratch.name)
        self.source = self.root / "outputs/raw/2099-01-01"
        self.source.parent.mkdir(parents=True)
        shutil.copytree(self.published_run, self.source)

    def _compose(self, label):
        curated = self.root / label
        summary = compose_curated.compose_run(compose_curated.ComposeRunContext(self.source, curated))
        return curated, summary

    def _program_ids(self):
        ids = []
        for path in sorted(self.source.rglob("*.jsonl")):
            for record in _jsonl(path):
                if record.get("family") == "python-function-repair":
                    ids.append(record["scenario"]["source"]["program_id"])
        return ids

    def test_committed_policy_is_recorded_in_compose_and_export(self):
        curated, summary = self._compose("curated")
        self.assertEqual(summary["eval_exclusion"], gate.descriptor())
        on_disk = json.loads((curated / "COMPOSE.json").read_text(encoding="utf-8"))
        self.assertEqual(on_disk["eval_exclusion"]["eval_denylist"]["sha256"],
                         lists.sha256_hex(policy.DENYLIST_PATH.read_bytes()))
        self.assertEqual(on_disk["eval_exclusion"]["do_not_train"]["sha256"],
                         lists.sha256_hex(policy.DO_NOT_TRAIN_PATH.read_bytes()))
        entries = _jsonl(curated / MANIFEST)
        self.assertTrue(entries)
        self.assertEqual(summary["lane_actions"]["eval_exclusion"], {"retained": len(entries)})
        for entry in entries:
            self.assertEqual(entry["stages"][-1]["lane"], "eval_exclusion")
            self.assertEqual(entry["stages"][-1]["action"], "retained")
        exported = export_hf.export_run(export_hf.ExportRequest(curated, self.root / "export"))
        self.assertTrue(exported["training_ready"])
        provenance = json.loads((self.root / "export/provenance.json").read_text(encoding="utf-8"))
        self.assertEqual(provenance["compose"]["eval_exclusion"], gate.descriptor())
        changed = write_policy(self.root)
        stale_request = export_hf.ExportRequest(curated, self.root / "export-stale")
        with (
            mock.patch.object(policy, "ACTIVE_POLICY", changed),
            self.assertRaisesRegex(ExportError, "eval_exclusion does not match"),
        ):
            export_hf.export_run(stale_request)

    def test_denylisted_program_refuses_compose_rather_than_dropping_the_row(self):
        held_out = self._program_ids()[0]
        listed = write_policy(self.root, denylist={"program_ids": [held_out]})
        with mock.patch.object(policy, "ACTIVE_POLICY", listed):
            with self.assertRaisesRegex(ComposeError, "refuse the shard"):
                self._compose("curated")

    def test_a_do_not_train_source_repository_refuses_the_shard(self):
        listed = write_policy(self.root, do_not_train={"repos": ["thealgorithms/python"]})
        with mock.patch.object(policy, "ACTIVE_POLICY", listed):
            with self.assertRaisesRegex(ComposeError, "refuse the shard"):
                self._compose("curated")


if __name__ == "__main__":
    unittest.main()
