"""Pin round_txn's fail-closed refusal paths and their exact messages.

Each case drives a public transaction entry point (or, for the agentic
envelope, the predicate that decides it) into one refusal branch, so a
refactor cannot reorder or reword a check without a failing test.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))
sys.path.insert(0, str(REPO / "tests"))

import round_txn
import round_txn_agentic
from round_txn_test_helpers import raw_factory, stage_round, thalamic, write_records

TOKEN = "a" * 32


def _write_json(path, payload):
    path.write_text(json.dumps(payload) + "\n")


class ReserveArgumentTests(unittest.TestCase):
    def test_round_and_expected_must_be_positive_plain_ints(self):
        with tempfile.TemporaryDirectory() as root:
            factory = raw_factory(root, "thalamic-trajectory-factory")
            for bad_round in (0, True, 1.0):
                with (
                    self.subTest(round=bad_round),
                    self.assertRaisesRegex(
                        round_txn.TransactionError, "^round number must be at least 1$"
                    ),
                ):
                    round_txn.reserve(factory, bad_round, 1)
            for bad_expected in (0, False):
                with (
                    self.subTest(expected=bad_expected),
                    self.assertRaisesRegex(
                        round_txn.TransactionError,
                        "^expected record count must be at least 1$",
                    ),
                ):
                    round_txn.reserve(factory, 1, bad_expected)

    def test_existing_reservation_stage_is_refused(self):
        with tempfile.TemporaryDirectory() as root:
            factory = raw_factory(root, "thalamic-trajectory-factory")
            round_txn.create_reservation_stage(factory, 1, TOKEN)
            with self.assertRaisesRegex(
                round_txn.TransactionError, "reservation staging directory already exists"
            ):
                round_txn.create_reservation_stage(factory, 1, TOKEN)


class CompletionManifestEntryTests(unittest.TestCase):
    def test_malformed_entry_digest_is_refused(self):
        with tempfile.TemporaryDirectory() as root:
            artifact = Path(root) / "batch-r01.jsonl"
            artifact.write_text("{}\n")
            manifest = {"files": [{"name": artifact.name, "sha256": "not-a-digest"}]}
            with self.assertRaisesRegex(
                round_txn.TransactionError, "completion marker has invalid file hash for"
            ):
                round_txn.completion_manifest_file_matches(artifact, manifest)


def _execution_gate_policy_for(mode):
    with tempfile.TemporaryDirectory() as root:
        factory = Path(root)
        _write_json(factory / round_txn.MODE_FILE, mode)
        return round_txn.execution_gate_policy(factory)


class ExecutionVerifiedRoundsTests(unittest.TestCase):
    def test_bound_rounds_must_be_an_ascending_positive_list_below_cutover(self):
        key = round_txn.EXECUTION_VERIFIED_ROUNDS_FIELD
        cutover = round_txn.EXECUTION_CUTOVER_FIELD
        for label, mode in (
            ("not a list", {cutover: 5, key: 3}),
            ("non-positive", {cutover: 5, key: [0]}),
            ("boolean", {cutover: 5, key: [True]}),
            ("duplicate", {cutover: 5, key: [2, 2]}),
            ("unsorted", {cutover: 5, key: [3, 2]}),
            ("no cutover", {key: [2]}),
            ("at cutover", {cutover: 5, key: [5]}),
        ):
            with (
                self.subTest(label),
                self.assertRaisesRegex(round_txn.TransactionError, f"invalid {key} in"),
            ):
                _execution_gate_policy_for(mode)

    def test_valid_bound_rounds_are_returned(self):
        key = round_txn.EXECUTION_VERIFIED_ROUNDS_FIELD
        cutover = round_txn.EXECUTION_CUTOVER_FIELD
        self.assertEqual(_execution_gate_policy_for({cutover: 5, key: [2, 4]}), (5, frozenset({2, 4})))
        self.assertEqual(_execution_gate_policy_for({}), (None, frozenset()))


class InFlightBatchPathTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.factory = raw_factory(self._tmp.name, "thalamic-trajectory-factory")
        self.marker = self.factory / "ROUND-r02.publishing.json"
        self.reservation = self.factory / "ROUND-r02.reserved.json"
        self.stage = round_txn.staging_dir(self.factory, 2, TOKEN)

    def tearDown(self):
        self._tmp.cleanup()

    def _publishing(self, **overrides):
        payload = {"factory": self.factory.name, "round": 2, "token": TOKEN}
        payload.update(overrides)
        _write_json(self.marker, payload)

    def _reserved(self, **overrides):
        payload = {"token": TOKEN, "staging_dir": str(self.stage)}
        payload.update(overrides)
        _write_json(self.reservation, payload)

    def _paths(self):
        return list(round_txn.in_flight_batch_paths(self.factory))

    def test_unparseable_marker_name_is_ignored(self):
        _write_json(self.factory / "ROUND-rxx.publishing.json", {})
        self.assertEqual(self._paths(), [])

    def test_identity_mismatch(self):
        self._publishing(factory="other-factory")
        with self.assertRaisesRegex(round_txn.TransactionError, "publishing marker identity"):
            self._paths()

    def test_missing_reservation(self):
        self._publishing()
        with self.assertRaisesRegex(round_txn.TransactionError, "has no reservation"):
            self._paths()

    def test_token_mismatch(self):
        self._publishing()
        self._reserved(token="b" * 32)
        with self.assertRaisesRegex(round_txn.TransactionError, "publishing marker token mismatch"):
            self._paths()

    def test_escaped_staging_path(self):
        self._publishing()
        self._reserved(staging_dir="/elsewhere")
        with self.assertRaisesRegex(
            round_txn.TransactionError, "publishing marker staging path is unsafe"
        ):
            self._paths()

    def test_no_readable_batch(self):
        self._publishing()
        self._reserved()
        with self.assertRaisesRegex(round_txn.TransactionError, "has no readable batch"):
            self._paths()

    def test_staged_batch_wins_over_linked_batch(self):
        self._publishing()
        self._reserved()
        linked = self.factory / "batch-r02.jsonl"
        write_records(linked, [thalamic("linked", 2)])
        self.assertEqual(self._paths(), [linked])
        self.stage.mkdir(parents=True)
        staged = self.stage / "batch-r02.jsonl"
        write_records(staged, [thalamic("staged", 2)])
        self.assertEqual(self._paths(), [staged])


class SiblingIdTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.factory = raw_factory(self._tmp.name, "thalamic-trajectory-factory")
        self.sibling = self.factory.parent / "neuromorphic-event-language-bridge"
        self.sibling.mkdir()
        round_txn._SIBLING_ID_CACHE.clear()
        self.addCleanup(round_txn._SIBLING_ID_CACHE.clear)

    def tearDown(self):
        self._tmp.cleanup()

    def _mode(self, **overrides):
        payload = {
            "version": 1,
            "commit_point": round_txn.MARKER_MODE_COMMIT_POINT,
            "legacy_baseline": 0,
        }
        payload.update(overrides)
        _write_json(self.sibling / round_txn.MODE_FILE, payload)

    def test_invalid_sibling_marker_mode_is_refused(self):
        for overrides in ({"version": 2}, {"commit_point": "x"}, {"legacy_baseline": -1}):
            with self.subTest(overrides):
                round_txn._SIBLING_ID_CACHE.clear()
                self._mode(**overrides)
                with self.assertRaisesRegex(
                    round_txn.TransactionError, "invalid sibling marker mode"
                ):
                    round_txn.sibling_committed_and_inflight_ids(self.factory)

    def test_only_owned_completed_batches_seed_ids(self):
        self._mode()
        _write_json(self.sibling / "ROUND-rxx.complete.json", {})
        _write_json(
            self.sibling / "ROUND-r01.complete.json",
            {"factory": "someone-else", "round": 1, "commit_point": "ROUND-r01.complete.json"},
        )
        write_records(self.sibling / "batch-r01.jsonl", [thalamic("foreign-claim")])
        _write_json(
            self.sibling / "ROUND-r02.complete.json",
            {"factory": self.sibling.name, "round": 2, "commit_point": "ROUND-r02.complete.json"},
        )
        _write_json(
            self.sibling / "ROUND-r03.complete.json",
            {"factory": self.sibling.name, "round": 3, "commit_point": "ROUND-r03.complete.json"},
        )
        write_records(self.sibling / "batch-r03.jsonl", [thalamic("owned-r03", 3)])
        seen = round_txn.sibling_committed_and_inflight_ids(self.factory)
        self.assertIn("owned-r03", seen)
        self.assertNotIn("foreign-claim", seen)


class CompletedRoundRecoveryTests(unittest.TestCase):
    """``publish`` on an already completed round re-checks leftover recovery state."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.factory = raw_factory(self._tmp.name, "thalamic-trajectory-factory")
        reservation = stage_round(round_txn, self.factory, [thalamic("done-1")])
        self.token = reservation["token"]
        self.reservation_payload = {
            key: reservation[key] for key in ("version", "factory", "round", "token")
        }
        self.reservation_payload["staging_dir"] = reservation["staging_dir"]
        self.manifest = round_txn.publish(self.factory, 1, self.token)
        self.paths = round_txn.marker_paths(self.factory, 1)

    def tearDown(self):
        self._tmp.cleanup()

    def _publish_again(self):
        return round_txn.publish(self.factory, 1, self.token)

    def test_clean_retry_returns_the_committed_manifest(self):
        self.assertEqual(self._publish_again(), self.manifest)

    def test_non_regular_publishing_marker(self):
        self.paths["publishing"].mkdir()
        with self.assertRaisesRegex(
            round_txn.TransactionError, "unsafe publishing marker for completed round"
        ):
            self._publish_again()

    def test_conflicting_publishing_marker(self):
        _write_json(self.paths["publishing"], {**self.manifest, "records": 99})
        with self.assertRaisesRegex(
            round_txn.TransactionError, "publishing marker conflicts with completed round"
        ):
            self._publish_again()

    def test_non_regular_reservation(self):
        self.paths["reservation"].mkdir()
        with self.assertRaisesRegex(
            round_txn.TransactionError, "unsafe reservation for completed round"
        ):
            self._publish_again()

    def test_reservation_for_another_token(self):
        _write_json(self.paths["reservation"], {**self.reservation_payload, "token": "c" * 32})
        with self.assertRaisesRegex(
            round_txn.TransactionError, "reservation conflicts with completed round"
        ):
            self._publish_again()

    def test_reservation_isolation_must_match_a_version_2_manifest(self):
        _write_json(
            self.paths["reservation"],
            {**self.reservation_payload, "preference_isolation": "two-session"},
        )
        with self.assertRaisesRegex(
            round_txn.TransactionError, "reservation isolation conflicts with completed round"
        ):
            self._publish_again()

    def test_matching_reservation_and_stage_are_cleaned_up(self):
        _write_json(self.paths["reservation"], self.reservation_payload)
        stage = Path(self.reservation_payload["staging_dir"])
        stage.mkdir(parents=True)
        self.assertEqual(self._publish_again(), self.manifest)
        self.assertFalse(self.paths["reservation"].exists())
        self.assertFalse(stage.exists())

    def test_stage_path_occupied_by_a_file(self):
        stage = round_txn.staging_dir(self.factory, 1, self.token)
        stage.parent.mkdir(parents=True, exist_ok=True)
        stage.write_text("not a directory\n")
        with self.assertRaisesRegex(round_txn.TransactionError, "staging directory is unsafe"):
            self._publish_again()


class AbortStageTests(unittest.TestCase):
    def test_stage_path_occupied_by_a_file_is_refused(self):
        with tempfile.TemporaryDirectory() as root:
            factory = raw_factory(root, "thalamic-trajectory-factory")
            reservation = round_txn.reserve(factory, 1, 1)
            stage = Path(reservation["staging_dir"])
            stage.rmdir()
            stage.write_text("not a directory\n")
            with self.assertRaisesRegex(
                round_txn.TransactionError, "reservation staging directory is unsafe"
            ):
                round_txn.abort(factory, 1, reservation["token"])


class AgenticPredicateTests(unittest.TestCase):
    def test_long_horizon_success_with_partial_language_is_unsupported(self):
        text = "verified: all tests passed; partial rollback remains"
        self.assertTrue(round_txn_agentic._long_horizon_success_unsupported({}, text))

    def test_plan_change_needs_a_change_term_and_no_ignored_term(self):
        self.assertFalse(round_txn_agentic._names_plan_change("we keep going"))
        self.assertTrue(round_txn_agentic._names_plan_change("we adopt the queue design"))

    def test_plan_change_terms_match_whole_words_and_their_inflections(self):
        for text in (
            "we added a failing test",
            "the reviewer is escalating to the owner",
            "deferred the migration to the next release",
            "rollbacks are gated on the checkpoint",
            "we are changing the ttl race coverage plan",
            "revising the rollout order",
            "the second revision removes the flag",
        ):
            with self.subTest(text=text):
                self.assertTrue(round_txn_agentic._names_plan_change(text))
        for text in (
            "the reviewer will address the race later",
            "padding the buffer hides the race",
            "the additional test is unchanged",
            "proceed with the original plan",
        ):
            with self.subTest(text=text):
                self.assertFalse(round_txn_agentic._names_plan_change(text))

    def test_plan_change_must_follow_the_disagreement(self):
        contents = ["we disagree", "we adopt the queue design"]
        self.assertTrue(
            round_txn_agentic._plan_changes_after([0], [1], "resolution", contents)
        )
        self.assertFalse(
            round_txn_agentic._plan_changes_after([1], [0], "resolution", contents)
        )

    def test_mentioned_last(self):
        class _Match:
            def __init__(self, start):
                self._start = start

            def start(self):
                return self._start

        self.assertFalse(round_txn_agentic._mentioned_last([], [_Match(1)]))
        self.assertTrue(round_txn_agentic._mentioned_last([_Match(1)], []))
        self.assertTrue(round_txn_agentic._mentioned_last([_Match(5)], [_Match(1)]))
        self.assertFalse(round_txn_agentic._mentioned_last([_Match(1)], [_Match(5)]))

    def test_non_object_preference_side_has_no_outcome_errors(self):
        self.assertEqual(
            round_txn_agentic._preference_side_outcome_errors(None, "chosen", "not-a-dict"), []
        )


if __name__ == "__main__":
    unittest.main()
