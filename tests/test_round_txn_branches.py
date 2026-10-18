"""Branch coverage for round_txn fail-closed refusals and recovery paths."""

import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
for _path in (REPO / "pipelines", REPO / "tests"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

import preference_arms
import round_txn
from round_txn_test_helpers import (
    raw_factory,
    stage_round,
    thalamic,
    write_completion_marker,
    write_records,
)

TXN = round_txn.TransactionError
THALAMIC = "thalamic-trajectory-factory"
CUSTOM = "custom-branch-factory"


def write_json(path, payload):
    Path(path).write_text(json.dumps(payload) + "\n")


def write_mode(factory, baseline=0, **extra):
    payload = {"version": 1, "legacy_baseline": baseline, "commit_point": "ROUND-rNN.complete.json"}
    payload.update(extra)
    write_json(factory / round_txn.MODE_FILE, payload)


class TempCaseMixin:
    def setUp(self):
        self.root = Path(self.enterContext(tempfile.TemporaryDirectory()))

    def factory(self, slug=THALAMIC, fresh=False):
        root = tempfile.mkdtemp(dir=self.root) if fresh else self.root
        return raw_factory(root, slug)

    def committed(self):
        """A marker-mode factory with one hand-written completed round."""
        factory = self.factory(fresh=True)
        round_txn.ensure_marker_mode(factory)
        batch, notes = factory / "batch-r01.jsonl", factory / "NOTES-r01.md"
        write_records(batch, [thalamic("branch-committed")])
        notes.write_text("# Critique\n\nFixture.\n")
        marker = write_completion_marker(round_txn, factory, batch, notes)
        return factory, marker

    def published(self):
        factory = self.factory(fresh=True)
        reservation = stage_round(round_txn, factory, [thalamic("branch-published")])
        round_txn.publish(factory, 1, reservation["token"])
        return factory, reservation

    def interrupted(self):
        """Publish up to (but not including) the completion link."""
        factory = self.factory(fresh=True)
        reservation = stage_round(round_txn, factory, [thalamic("branch-interrupted")])
        link = mock.patch.object(
            round_txn, "link_verified_completion_marker", side_effect=RuntimeError("crash")
        )
        with link, self.assertRaises(RuntimeError):
            round_txn.publish(factory, 1, reservation["token"])
        return factory, reservation


class FilePrimitiveTests(TempCaseMixin, unittest.TestCase):
    def test_read_json_requires_an_object(self):
        path = self.root / "list.json"
        path.write_text("[1]\n")
        with self.assertRaisesRegex(TXN, "must contain an object"):
            round_txn.read_json(path)

    def test_non_regular_sources_are_refused(self):
        cases = (
            (lambda: round_txn.file_sha256(self.root), "unsafe non-regular file"),
            (lambda: round_txn.capture_regular_file(self.root, self.root / "c"), "non-regular"),
            (lambda: round_txn.copy_verified_exclusive(self.root, self.root / "d", "0"),
             "staged source is not a regular file"),
            (lambda: round_txn.copy_verified_exclusive(self.root / "gone", self.root / "e", "0"),
             "cannot open staged file safely"),
        )
        for call, pattern in cases:
            with self.subTest(pattern=pattern), self.assertRaisesRegex(TXN, pattern):
                call()

    def test_capture_refuses_an_existing_destination(self):
        source, destination = self.root / "src", self.root / "dst"
        source.write_text("a\n")
        destination.write_text("b\n")
        with self.assertRaisesRegex(TXN, "cannot capture staged file"):
            round_txn.capture_regular_file(source, destination)

    def test_copy_accepts_identical_destination_and_refuses_a_race(self):
        source, destination = self.root / "src", self.root / "dst"
        source.write_text("same\n")
        digest = round_txn.file_sha256(source)
        destination.write_text("same\n")
        round_txn.copy_verified_exclusive(source, destination, digest)
        destination.write_text("different\n")
        with self.assertRaisesRegex(TXN, "publication race"):
            round_txn.copy_verified_exclusive(source, destination, digest)

    def test_exclusive_writers_remove_partial_files_on_failure(self):
        writers = (
            lambda path: round_txn.write_exclusive_json(path, {"a": 1}),
            lambda path: round_txn.write_exclusive_text(path, "a\n"),
        )
        for index, writer in enumerate(writers):
            for vanish in (False, True):
                path = self.root / f"partial-{index}-{vanish}"

                def fail(_fd, path=path, vanish=vanish):
                    if vanish:
                        path.unlink()
                    raise OSError("disk full")

                with self.subTest(index=index, vanish=vanish):
                    with mock.patch.object(round_txn.os, "fsync", side_effect=fail):
                        self.assertRaises(OSError, writer, path)
                    self.assertFalse(path.exists())


class CompletionMarkerTests(TempCaseMixin, unittest.TestCase):
    def mutated_marker_error(self, mutate, pattern):
        factory, marker = self.committed()
        payload = json.loads(marker.read_text())
        mutate(payload)
        write_json(marker, payload)
        with self.assertRaisesRegex(TXN, pattern):
            round_txn.completed_manifests(factory)

    def test_invalid_marker_fields_are_refused(self):
        def files(entries):
            return lambda payload: payload.update(files=entries(payload["files"]))

        cases = (
            (lambda p: p.update(round="1"), "completion marker round mismatch"),
            (lambda p: p.update(round=2), "completion marker round mismatch"),
            (lambda p: p.update(files={}), "files must be an array"),
            (files(lambda f: [{"name": "", "sha256": "0" * 64}]), "unsafe file entry"),
            (files(lambda f: [{"name": "a/b", "sha256": "0" * 64}]), "unsafe file entry"),
            (files(lambda f: f[:1]), "no unique notes entry"),
            (lambda p: p.update(version="x"), "unsupported completion marker version for"),
            (lambda p: p.update(version=3), "unsupported completion marker version for"),
            (lambda p: p.update(kinds={"preference": 1}), "kinds do not match batch"),
        )
        for mutate, pattern in cases:
            with self.subTest(pattern=pattern):
                self.mutated_marker_error(mutate, pattern)

    def test_unmatched_names_are_ignored_and_symlinks_refused(self):
        factory, marker = self.committed()
        (factory / "ROUND-rX.complete.json").write_text("{}\n")
        self.assertEqual(list(round_txn.completed_manifests(factory)), [1])
        self.assertEqual(round_txn.completed_rounds(factory), [1])
        (factory / "ROUND-r02.complete.json").symlink_to(marker)
        with self.assertRaisesRegex(TXN, "unsafe completion marker"):
            round_txn.completed_manifests(factory)

    def test_two_spellings_of_one_round_rebind_the_same_batch_ids(self):
        factory, marker = self.committed()
        payload = {**json.loads(marker.read_text()), "commit_point": "ROUND-r1.complete.json"}
        write_json(factory / "ROUND-r1.complete.json", payload)
        with self.assertRaisesRegex(TXN, "duplicate record id 'branch-committed'"):
            round_txn.completed_manifests(factory)

    def test_completed_rounds_rejects_a_mismatched_round(self):
        factory = self.factory()
        write_json(factory / "ROUND-r03.complete.json", {"round": 4})
        with self.assertRaisesRegex(TXN, "says 4"):
            round_txn.completed_rounds(factory)

    def test_marker_version_without_batch_context(self):
        for version in ("1", 0, 9):
            with self.subTest(version=version), self.assertRaisesRegex(TXN, "version: here"):
                round_txn.completion_marker_version({"version": version}, "here")

    def test_manifest_file_entry_must_be_unique_and_hashed(self):
        path = self.root / "batch-r01.jsonl"
        path.write_text("x\n")
        cases = (
            ([{"name": path.name, "sha256": "0" * 64}] * 2, "no unique file entry"),
            ([{"name": path.name, "sha256": "XYZ"}], "invalid file hash"),
        )
        for entries, pattern in cases:
            with self.subTest(pattern=pattern), self.assertRaisesRegex(TXN, pattern):
                round_txn.completion_manifest_file_matches(path, {"files": entries})


class MarkerModeTests(TempCaseMixin, unittest.TestCase):
    def test_validated_marker_mode_requires_a_declaration(self):
        factory = self.factory(CUSTOM)
        with self.assertRaisesRegex(TXN, "marker mode is not enabled"):
            round_txn.validated_marker_mode(factory)
        write_mode(factory, baseline=True)
        with self.assertRaisesRegex(TXN, "invalid legacy_baseline"):
            round_txn.validated_marker_mode(factory)

    def test_execution_gate_policy_rejects_malformed_bindings(self):
        rounds, cutover = round_txn.EXECUTION_VERIFIED_ROUNDS_KEY, round_txn.EXECUTION_CUTOVER_KEY
        cases = (
            ({rounds: "1"}, rounds), ({cutover: 3, rounds: [0]}, rounds),
            ({cutover: 3, rounds: [2, 1]}, rounds), ({rounds: [1]}, rounds),
            ({cutover: 2, rounds: [2]}, rounds), ({cutover: "3"}, cutover),
        )
        factory = self.factory(CUSTOM)
        for extra, key in cases:
            write_mode(factory, **extra)
            with self.subTest(extra=extra), self.assertRaisesRegex(TXN, f"invalid {key}"):
                round_txn.execution_gate_policy(factory)

    def test_cutover_round_reads_the_binding(self):
        factory = self.factory(CUSTOM)
        self.assertIsNone(round_txn.execution_gate_cutover_round(factory))
        write_mode(factory, execution_verified_from_round=3, execution_verified_rounds=[1])
        self.assertEqual(round_txn.execution_gate_cutover_round(factory), 3)

    def test_remember_cutover_binds_gap_rounds_and_refuses_bad_cutover(self):
        factory = self.factory(CUSTOM)
        self.assertIsNone(round_txn.remember_execution_gate_cutover(factory, 1))
        self.assertFalse((factory / round_txn.MODE_FILE).exists())
        write_mode(factory, execution_verified_from_round=3)
        round_txn.remember_execution_gate_cutover(factory, 1)
        self.assertEqual(round_txn.execution_gate_policy(factory), (3, frozenset({1})))
        write_mode(factory, execution_verified_from_round=0)
        with self.assertRaisesRegex(TXN, "invalid execution_verified_from_round"):
            round_txn.remember_execution_gate_cutover(factory, 1)

    def test_remember_cutover_ignores_unmatched_marker_names(self):
        factory = self.factory(CUSTOM)
        write_mode(factory)
        (factory / "ROUND-rX.complete.json").write_text("{}\n")
        round_txn.remember_execution_gate_cutover(factory, 2)
        self.assertEqual(round_txn.execution_gate_cutover_round(factory), 2)

    def test_ensure_marker_mode_handles_a_concurrent_creator(self):
        factory = self.factory(CUSTOM)

        def lose_race(path, _payload):
            if racer_writes:
                write_mode(factory)
            raise FileExistsError(path)

        for racer_writes in (False, True):
            (factory / round_txn.MODE_FILE).unlink(missing_ok=True)
            with self.subTest(racer_writes=racer_writes), mock.patch.object(
                round_txn, "write_exclusive_json", side_effect=lose_race
            ):
                if racer_writes:
                    self.assertEqual(round_txn.ensure_marker_mode(factory)["legacy_baseline"], 0)
                    continue
                with self.assertRaisesRegex(TXN, "disappeared"):
                    round_txn.ensure_marker_mode(factory)


class LegacyDiscoveryTests(TempCaseMixin, unittest.TestCase):
    def test_unrecognised_and_symlinked_payloads_do_not_advance_frontiers(self):
        factory = self.factory(CUSTOM)
        write_records(factory / "other.jsonl", [thalamic("legacy-other")])
        write_records(factory / "batch-rX.jsonl", [thalamic("legacy-bad-name")])
        (factory / "batch-r01.jsonl").symlink_to(factory / "other.jsonl")
        self.assertEqual(round_txn.valid_legacy_file(factory / "batch-r01.jsonl"), 0)
        self.assertEqual(round_txn.discover_legacy_frontier(factory), 0)
        self.assertEqual(round_txn.discover_unmarked_legacy_frontier(factory), 0)

    def test_marker_baseline_exposes_legacy_batch_and_named_payloads(self):
        factory = self.factory(CUSTOM)
        write_records(factory / "batch-r01.jsonl", [thalamic("legacy-batch")])
        write_records(factory / "trajectories.jsonl", [thalamic("legacy-named")])
        write_records(factory / "other.jsonl", [thalamic("legacy-hidden")])
        write_mode(factory, baseline=1)
        names = [path.name for path in round_txn.committed_jsonl_paths(factory)]
        self.assertEqual(names, ["batch-r01.jsonl", "trajectories.jsonl"])

    def test_baseline_payloads_must_meet_the_lane_quota(self):
        factory = self.factory()
        write_records(factory / "trajectories.jsonl", [thalamic("legacy-short")])
        with self.assertRaisesRegex(TXN, "do not meet quota 5"):
            round_txn.validate_legacy_baseline_payloads(factory, 1)

    def test_sibling_scan_refuses_bad_mode_and_skips_unbound_markers(self):
        factory, sibling = self.factory(CUSTOM), self.factory("sibling-factory")
        write_mode(sibling, version=2)
        with self.assertRaisesRegex(TXN, "invalid sibling marker mode"):
            round_txn.sibling_committed_and_inflight_ids(factory)
        write_mode(sibling)
        (sibling / "ROUND-rX.complete.json").write_text("{}\n")
        write_json(sibling / "ROUND-r01.complete.json", {"factory": "someone-else"})
        write_json(sibling / "ROUND-r02.complete.json",
                   {"factory": sibling.name, "round": 2, "commit_point": "ROUND-r02.complete.json"})
        round_txn._SIBLING_ID_CACHE.clear()
        self.assertEqual(round_txn.sibling_committed_and_inflight_ids(factory), {})


class InFlightTests(TempCaseMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.factory_dir = self.factory()
        self.reservation = stage_round(round_txn, self.factory_dir, [thalamic("inflight-1")])
        self.marker = self.factory_dir / "ROUND-r01.publishing.json"
        self.reserved = self.factory_dir / "ROUND-r01.reserved.json"

    def inflight(self, **marker):
        write_json(self.marker, {"factory": THALAMIC, "round": 1,
                                 "token": self.reservation["token"], **marker})
        return list(round_txn.in_flight_batch_paths(self.factory_dir))

    def test_publishing_marker_refusals(self):
        cases = (
            ({"factory": "other"}, None, "identity mismatch"),
            ({"token": "f" * 32}, None, "token mismatch"),
            ({}, {"staging_dir": "/elsewhere"}, "staging path is unsafe"),
        )
        for marker, reservation, pattern in cases:
            if reservation:
                write_json(self.reserved, {**self.reservation, **reservation})
            with self.subTest(pattern=pattern), self.assertRaisesRegex(TXN, pattern):
                self.inflight(**marker)

    def test_linked_batch_is_used_once_the_stage_copy_is_gone(self):
        stage = Path(self.reservation["staging_dir"])
        (factory_batch := self.factory_dir / "batch-r01.jsonl").write_bytes(
            (stage / "batch-r01.jsonl").read_bytes()
        )
        (stage / "batch-r01.jsonl").unlink()
        (self.factory_dir / "ROUND-rX.publishing.json").write_text("{}\n")
        self.assertEqual(self.inflight(), [factory_batch])
        factory_batch.unlink()
        with self.assertRaisesRegex(TXN, "no readable batch"):
            self.inflight()
        self.reserved.unlink()
        with self.assertRaisesRegex(TXN, "has no reservation"):
            self.inflight()


class StagingTests(TempCaseMixin, unittest.TestCase):
    def test_staging_paths_require_the_raw_layout(self):
        token = "a" * 32
        with self.assertRaisesRegex(TXN, "must be outputs/raw"):
            round_txn.staging_dir(self.root / "loose", 1, token)
        factory = self.factory()
        with self.assertRaisesRegex(TXN, "escaped its transaction root"):
            round_txn.validated_reservation_stage(factory, 1, token, str(self.root / "elsewhere"))

    def test_create_stage_refusals(self):
        token = "b" * 32
        missing = self.root / "absent" / "outputs" / "raw" / "d" / THALAMIC
        with self.assertRaisesRegex(TXN, "staging directory is unsafe"):
            round_txn.create_reservation_stage(missing, 1, token)
        factory = self.factory()
        round_txn.staging_dir(factory, 1, token).mkdir(parents=True)
        with self.assertRaisesRegex(TXN, "already exists"):
            round_txn.create_reservation_stage(factory, 1, token)
        with (
            mock.patch.object(round_txn.os, "mkdir", side_effect=PermissionError("denied")),
            self.assertRaisesRegex(TXN, "cannot create reservation staging"),
        ):
            round_txn.create_reservation_stage(factory, 1, "c" * 32)

    def test_reserve_rejects_bad_counts_and_cleans_stage_on_write_failure(self):
        factory = self.factory()
        for round_number, expected in ((0, 1), (True, 1), (1, 0), (1, False)):
            with self.subTest(round=round_number, expected=expected):
                self.assertRaisesRegex(TXN, "at least 1", round_txn.reserve,
                                       factory, round_number, expected)
        round_txn.ensure_marker_mode(factory)
        with mock.patch.object(round_txn, "write_exclusive_json", side_effect=OSError("full")):
            self.assertRaises(OSError, round_txn.reserve, factory, 1, 1)
        stage_parent = self.root / "outputs" / "staging" / "2099-01-01" / THALAMIC
        self.assertEqual(list(stage_parent.iterdir()), [])

    def test_validate_stage_refuses_a_stage_mutated_during_capture(self):
        real_capture = round_txn.capture_regular_file
        mutations = (
            (shutil.rmtree, "cannot inspect staging directory"),
            (lambda stage: (stage / "extra.txt").write_text("x"), "file set changed"),
            (lambda stage: ((stage / "NOTES-r01.md").unlink(), (stage / "NOTES-r01.md").mkdir()),
             "file set changed"),
        )
        for index, (mutate, pattern) in enumerate(mutations):
            factory = raw_factory(self.root / str(index), THALAMIC)
            reservation = stage_round(round_txn, factory, [thalamic(f"mutated-{index}")])
            stage = Path(reservation["staging_dir"])

            def capture(source, destination, stage=stage, mutate=mutate):
                result = real_capture(source, destination)
                if source.name == "batch-r01.jsonl":
                    mutate(stage)
                return result

            with self.subTest(pattern=pattern), mock.patch.object(
                round_txn, "capture_regular_file", side_effect=capture
            ), self.assertRaisesRegex(TXN, pattern):
                round_txn.validate_stage(factory, stage, 1, 1, reservation["token"])


class PublishRecoveryTests(TempCaseMixin, unittest.TestCase):
    def test_completed_round_cleanup_refusals(self):
        def as_dir(path):
            path.unlink(missing_ok=True)
            path.mkdir()

        def reservation(reserved, **extra):
            write_json(reserved, {**self.original, **extra})

        cases = (
            (lambda p, r: as_dir(p), "unsafe publishing marker for completed round"),
            (lambda p, r: write_json(p, {"x": 1}), "publishing marker conflicts"),
            (lambda p, r: as_dir(r), "unsafe reservation for completed round"),
            (lambda p, r: reservation(r, round=2), "reservation conflicts"),
            (lambda p, r: reservation(r, preference_isolation="two-session"),
             "reservation isolation conflicts"),
        )
        for mutate, pattern in cases:
            factory, self.original = self.published()
            paths = round_txn.marker_paths(factory, 1)
            mutate(paths["publishing"], paths["reservation"])
            with self.subTest(pattern=pattern), self.assertRaisesRegex(TXN, pattern):
                round_txn.publish(factory, 1, self.original["token"])

    def test_completed_round_token_and_stage_refusals(self):
        factory, reservation = self.published()
        token = reservation["token"]
        with self.assertRaisesRegex(TXN, "token does not match"):
            round_txn.publish(factory, 1, "f" * 32)
        stage = Path(reservation["staging_dir"])
        stage.write_text("not a directory\n")
        with self.assertRaisesRegex(TXN, "staging directory is unsafe"):
            round_txn.publish(factory, 1, token)
        stage.unlink()
        stage.mkdir()
        with (
            mock.patch.object(round_txn.shutil, "rmtree", side_effect=OSError("busy")),
            self.assertRaisesRegex(TXN, "cannot finish completed round staging cleanup"),
        ):
            round_txn.publish(factory, 1, token)
        with (
            mock.patch.object(round_txn, "completed_manifests", return_value={}),
            self.assertRaisesRegex(TXN, "round completion marker is invalid"),
        ):
            round_txn.publish(factory, 1, token)

    def test_publish_rejects_reservation_drift(self):
        cases = (({"round": 2}, "round/token does not match"),
                 ({"expected_records": 0}, "invalid expected_records value"))
        factory = self.factory()
        reservation = stage_round(round_txn, factory, [thalamic("drift-1")])
        reserved = factory / "ROUND-r01.reserved.json"
        for extra, pattern in cases:
            write_json(reserved, {**reservation, **extra})
            with self.subTest(pattern=pattern), self.assertRaisesRegex(TXN, pattern):
                round_txn.publish(factory, 1, reservation["token"])

    def test_resumed_publish_refuses_non_regular_existing_output(self):
        def replace_with_symlink(notes):
            copy = notes.with_name("notes-copy.md")
            shutil.copyfile(notes, copy)
            notes.unlink()
            notes.symlink_to(copy)

        def replace_with_dir(notes):
            notes.unlink()
            notes.mkdir()

        for replace in (replace_with_dir, replace_with_symlink):
            factory, reservation = self.interrupted()
            replace(factory / "NOTES-r01.md")
            with self.subTest(replace=replace.__name__), self.assertRaisesRegex(
                TXN, "refusing to replace conflicting output"
            ):
                round_txn.publish(factory, 1, reservation["token"])

    def test_abort_refusals(self):
        factory = self.factory()
        with self.assertRaisesRegex(TXN, "no reservation to abort"):
            round_txn.abort(factory, 1, "a" * 32)
        reservation = round_txn.reserve(factory, 1, 1)
        stage = Path(reservation["staging_dir"])
        stage.rmdir()
        stage.write_text("file\n")
        with self.assertRaisesRegex(TXN, "reservation staging directory is unsafe"):
            round_txn.abort(factory, 1, reservation["token"])

    def test_publish_lock_refuses_a_symlinked_lock(self):
        factory = self.factory()
        (factory.parent / ".round-publish.lock").symlink_to(self.root / "elsewhere")
        with self.assertRaisesRegex(TXN, "cannot acquire run publish lock"):
            round_txn.abort(factory, 1, "a" * 32)


class GateHelperTests(TempCaseMixin, unittest.TestCase):
    def gate(self, scan=None, error=None, records=1):
        patched = mock.patch.object(preference_arms, "scan_source", return_value=scan,
                                    side_effect=error)
        with patched:
            return round_txn.validate_preference_arm_gate(self.root / "b", records, "two-session")

    def test_preference_arm_gate_refusals(self):
        def scan(pairs, skipped):
            summary = {"preference_pairs": pairs, "skipped_non_preference_records": skipped}
            return SimpleNamespace(summary=summary, blocked=False, decisions=[])

        cases = (
            ({"error": OSError("gone")}, "preference arm gate failed"),
            ({"scan": scan(2, 0)}, "did not inspect every staged record"),
            ({"scan": scan(1, 1)}, "skipped non-preference records"),
        )
        for kwargs, pattern in cases:
            with self.subTest(pattern=pattern), self.assertRaisesRegex(TXN, pattern):
                self.gate(**kwargs)

    def test_unreadable_notes_and_unregistered_generator(self):
        message = round_txn.validate_novel_coverage(self.root / "missing.md", self.root,
                                                    required=True)
        self.assertRegex(message, "cannot read notes as UTF-8")
        with self.assertRaisesRegex(TXN, "no reviewed hosted generator authority"):
            round_txn._reviewed_hosted_generator(self.root / "unregistered-factory")

    def test_completed_agentic_batch_must_meet_its_fixed_quota(self):
        factory = self.factory("cache-stampede-factory")
        with self.assertRaisesRegex(TXN, "requires exactly 2"):
            round_txn._completed_agentic_envelope_matches(
                factory, 1, factory / "batch-r01.jsonl", {"episode": 1}, 1
            )


class CliTests(TempCaseMixin, unittest.TestCase):
    @staticmethod
    def run_cli(*argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = round_txn.main([str(arg) for arg in argv])
        return code, out.getvalue(), err.getvalue()

    def test_reserve_then_abort_round_trip(self):
        factory = self.factory()
        code, out, _err = self.run_cli("reserve", factory, "--round", 1, "--expected", 1)
        self.assertEqual(code, 0)
        token = json.loads(out)["token"]
        code, out, _err = self.run_cli("abort", factory, "--round", 1, "--token", token)
        self.assertEqual((code, json.loads(out)["aborted"]), (0, True))

    def test_migrate_refuses_a_non_preference_lane(self):
        code, out, err = self.run_cli("migrate-preference-v1", self.factory())
        self.assertEqual((code, out), (1, ""))
        self.assertTrue(err.startswith("ERROR: "))


if __name__ == "__main__":
    unittest.main()
