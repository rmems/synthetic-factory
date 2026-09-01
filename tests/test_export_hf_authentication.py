#!/usr/bin/env python3
"""Authenticating a published export against the source it claims."""

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from export_test_support import (  # noqa: E402
    ONE_CALIBRATION,
    calibration_document,
    compose_fixture,
)
import compose_curated  # noqa: E402
import export_contract  # noqa: E402
import export_hf  # noqa: E402


class ExportSourceReplayAuthentication(unittest.TestCase):
    # ---- one tamper helper per mutation, all resealing digests coherently ----

    @staticmethod
    def _write_summary(ctx):
        ctx["summary_path"].write_text(
            json.dumps(ctx["summary"], indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    @staticmethod
    def _documents_of(path):
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").split("\n")
            if line
        ]

    @classmethod
    def _reseal_documents(cls, ctx, path, documents, descriptor_key):
        payload = "".join(
            json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n"
            for item in documents
        ).encode("utf-8")
        path.write_bytes(payload)
        ctx["summary"][descriptor_key]["sha256"] = hashlib.sha256(payload).hexdigest()
        cls._write_summary(ctx)

    @classmethod
    def _tamper_manifest(cls, ctx, edit):
        documents = cls._documents_of(ctx["manifest_path"])
        edit(documents)
        cls._reseal_documents(ctx, ctx["manifest_path"], documents, "manifest")

    @classmethod
    def _mutate_output_digest(cls, ctx):
        output = ctx["curated"] / ctx["summary"]["outputs"][0]["path"]
        payload = output.read_bytes()
        output.write_bytes(payload.replace(b"\n", b" \n", 1))

    @classmethod
    def _mutate_manifest_digest(cls, ctx):
        ctx["manifest_path"].write_bytes(ctx["manifest_path"].read_bytes() + b" \n")

    @classmethod
    def _mutate_sidecar_digest(cls, ctx):
        ctx["sidecar_path"].write_bytes(ctx["sidecar_path"].read_bytes() + b" \n")

    @classmethod
    def _mutate_unsafe_output_path(cls, ctx):
        ctx["summary"]["outputs"][0]["path"] = "../escaped.jsonl"
        cls._write_summary(ctx)

    @staticmethod
    def _retained_row(documents):
        return next(item for item in documents if item["action"] == "retained")

    @classmethod
    def _mutate_coordinated_manifest_coordinate(cls, ctx):
        cls._tamper_manifest(
            ctx,
            lambda documents: cls._retained_row(documents).__setitem__(
                "output_sha256", "0" * 64
            ),
        )

    @classmethod
    def _mutate_coordinated_manifest_output_id(cls, ctx):
        cls._tamper_manifest(
            ctx,
            lambda documents: cls._retained_row(documents).__setitem__(
                "output_id", "sfcur-forged"
            ),
        )

    @classmethod
    def _mutate_malformed_sidecar_reference(cls, ctx):
        def edit(documents):
            retained = next(
                item
                for item in documents
                if item["action"] == "retained" and "reward_sidecar_id" in item
            )
            retained["reward_sidecar_id"] = []

        cls._tamper_manifest(ctx, edit)

    @classmethod
    def _mutate_excluded_sidecar_reference(cls, ctx):
        def edit(documents):
            excluded = next(item for item in documents if item["action"] == "excluded")
            excluded["reward_sidecar_id"] = "0" * 64

        cls._tamper_manifest(ctx, edit)

    @classmethod
    def _mutate_boolean_compose_count(cls, ctx):
        ctx["summary"]["counts"]["excluded"] = True
        cls._write_summary(ctx)

    @classmethod
    def _mutate_coordinated_sidecar_content(cls, ctx):
        documents = cls._documents_of(ctx["sidecar_path"])
        documents[0]["classification"]["reason_codes"].append("tampered")
        cls._reseal_documents(ctx, ctx["sidecar_path"], documents, "reward_sidecars")

    def test_compose_paths_digests_coordinates_and_sidecars_are_authenticated(self):
        mutations = (
            "output_digest",
            "manifest_digest",
            "sidecar_digest",
            "unsafe_output_path",
            "coordinated_manifest_coordinate",
            "coordinated_manifest_output_id",
            "malformed_sidecar_reference",
            "excluded_sidecar_reference",
            "boolean_compose_count",
            "coordinated_sidecar_content",
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                curated = compose_fixture(root)
                summary_path = curated / compose_curated.SUMMARY_FILENAME
                summary = json.loads(summary_path.read_text(encoding="utf-8"))
                ctx = {
                    "curated": curated,
                    "summary_path": summary_path,
                    "summary": summary,
                    "manifest_path": curated / summary["manifest"]["path"],
                    "sidecar_path": curated / summary["reward_sidecars"]["path"],
                }
                getattr(self, f"_mutate_{mutation}")(ctx)

                with self.assertRaises(export_hf.ExportError):
                    export_hf.export_run(curated, root / "export")
                self.assertFalse((root / "export").exists())

    # ---- one forgery per mutation; the manifest-editing ones reseal below ----

    _MANIFEST_RESEAL_MUTATIONS = frozenset(
        {
            "source_digest_types",
            "fabricated_stages",
            "dropped_exclusion",
            "excluded_source_mapping",
        }
    )

    @staticmethod
    def _forge_source_run_object(summary, documents):
        summary["source_run"] = {"forged": True}
        return documents

    @staticmethod
    def _forge_source_run_lexical_alias(summary, documents):
        source_root = Path(summary["source_run"])
        alias_parent = source_root.parent / "source-alias"
        alias_parent.mkdir()
        summary["source_run"] = f"{alias_parent.as_posix()}/../{source_root.name}"
        return documents

    @staticmethod
    def _forge_source_digest_types(summary, documents):
        documents[0]["source_sha256"] = []
        documents[0]["source_file_sha256"] = False
        return documents

    @staticmethod
    def _forge_fabricated_stages(summary, documents):
        documents[0]["stages"] = [
            {
                "lane": "identity",
                "transform_name": "forged",
                "transform_version": "forged-v1",
                "action": "retained",
                "reason_codes": [],
            }
        ]
        return documents

    @staticmethod
    def _forge_dropped_exclusion(summary, documents):
        documents = [entry for entry in documents if entry["action"] == "retained"]
        summary["counts"]["source_records"] = len(documents)
        summary["counts"]["excluded"] = 0
        summary["exclusions"] = {}
        return documents

    @staticmethod
    def _forge_excluded_source_mapping(summary, documents):
        excluded = next(entry for entry in documents if entry["action"] == "excluded")
        excluded["source_path"] = "forged/batch-r99.jsonl"
        excluded["source_line"] = 999
        excluded["source_sha256"] = "f" * 64
        excluded["source_file_sha256"] = "e" * 64
        return documents

    @staticmethod
    def _forge_fabricated_aggregates(summary, documents):
        summary["counts"]["source_files"] = 999
        summary["lane_actions"] = {}
        summary["exclusions"] = {"forged": 1}
        summary["transforms"] = {"identity": {"name": "forged"}}
        return documents

    @staticmethod
    def _forge_fabricated_calibration(summary, documents):
        summary["calibration"] = {
            "mode": "none",
            "path": None,
            "sha256": None,
            "records": 1,
        }
        summary["calibrated_records"] = 1
        return documents

    @staticmethod
    def _forge_fabricated_compose_audit(summary, documents):
        summary["audit"]["training_ready"] = False
        summary["audit"]["blockers"] = ["forged historical blocker"]
        return documents

    @staticmethod
    def _reseal_manifest(summary, manifest_path, documents):
        manifest_payload = "".join(
            json.dumps(entry, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n"
            for entry in documents
        ).encode("utf-8")
        manifest_path.write_bytes(manifest_payload)
        summary["manifest"]["entries"] = len(documents)
        summary["manifest"]["sha256"] = hashlib.sha256(manifest_payload).hexdigest()

    def test_refuses_self_resealed_source_history_and_aggregate_claims(self):
        mutations = (
            "source_run_object",
            "source_run_lexical_alias",
            "source_digest_types",
            "fabricated_stages",
            "dropped_exclusion",
            "excluded_source_mapping",
            "fabricated_aggregates",
            "fabricated_calibration",
            "fabricated_compose_audit",
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                curated = compose_fixture(root)
                summary_path = curated / compose_curated.SUMMARY_FILENAME
                summary = json.loads(summary_path.read_text(encoding="utf-8"))
                manifest_path = curated / summary["manifest"]["path"]
                documents = self._documents_of(manifest_path)

                documents = getattr(self, f"_forge_{mutation}")(summary, documents)
                if mutation in self._MANIFEST_RESEAL_MUTATIONS:
                    self._reseal_manifest(summary, manifest_path, documents)
                summary_path.write_text(
                    json.dumps(summary, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )

                with self.assertRaises(export_hf.ExportError):
                    export_hf.export_run(curated, root / "export")
                self.assertFalse((root / "export").exists())


class CalibrationAuthentication(unittest.TestCase):
    """COMPOSE.json's calibration descriptor is authenticated before replay.

    A published export carries the reward calibration it was composed with.
    Replay has to prove that descriptor against the bytes on disk, or a
    swapped conversion factor would silently rescale every reward.
    """

    def write_calibration(self, root, text=ONE_CALIBRATION, canonical=True):
        if canonical:
            path = root / compose_curated.FFPC_UNITS_MIGRATION
        else:
            path = root / "elsewhere" / "units-migration.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = text.encode("utf-8") if isinstance(text, str) else text
        path.write_bytes(payload)
        return path, hashlib.sha256(payload).hexdigest()

    def summary_for(self, path, digest, *, mode="source_run", records=1, calibrated=None):
        return {
            "calibration": {
                "mode": mode,
                "path": None if path is None else str(path),
                "sha256": digest,
                "records": records,
            },
            "calibrated_records": records if calibrated is None else calibrated,
        }

    def authenticate(self, summary, root):
        return export_hf._authenticated_calibration(summary, root)

    def assert_refused(self, summary, root, fragment):
        with self.assertRaises(export_hf.ExportError) as caught:
            self.authenticate(summary, root)
        self.assertIn(fragment, str(caught.exception))

    # ---- descriptor authentication ----

    def test_a_source_run_calibration_authenticates_and_builds_the_catalog(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path, digest = self.write_calibration(root)

            catalog, descriptor = self.authenticate(
                self.summary_for(path, digest), root
            )

        self.assertEqual(set(catalog), {"ffpc-r5-002"})
        entry = catalog["ffpc-r5-002"]
        # 0.5 of the canonical 10000-unit USD basis.
        self.assertEqual(entry["source_unit_usd"], 5000.0)
        self.assertEqual(entry["canonical_factor"], 0.5)
        self.assertTrue(entry["evidence_ref"].endswith("#/records/0"))
        self.assertEqual(descriptor["mode"], "source_run")
        self.assertEqual(descriptor["sha256"], digest)

    def test_an_incomplete_descriptor_is_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path, digest = self.write_calibration(root)
            summary = self.summary_for(path, digest)
            summary["calibration"].pop("sha256")

            self.assert_refused(summary, root, "calibration descriptor is incomplete")
            self.assert_refused({"calibration": None}, root, "incomplete")

    def test_the_record_count_must_be_a_nonnegative_integer(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path, digest = self.write_calibration(root)
            for bad in (True, -1, "1", 1.0):
                with self.subTest(records=bad):
                    self.assert_refused(
                        self.summary_for(path, digest, records=bad),
                        root,
                        "calibration.records must be nonnegative",
                    )

    def test_an_absent_calibration_must_not_name_a_file(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path, digest = self.write_calibration(root)

            self.assert_refused(
                self.summary_for(path, None, mode="none", records=0),
                root,
                "absent calibration must not name a file",
            )
            self.assert_refused(
                self.summary_for(None, digest, mode="none", records=0),
                root,
                "absent calibration must not name a file",
            )

    def test_an_absent_calibration_authenticates_as_an_empty_catalog(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)

            catalog, descriptor = self.authenticate(
                self.summary_for(None, None, mode="none", records=0), root
            )

        self.assertEqual(catalog, {})
        self.assertEqual(descriptor["mode"], "none")

    def test_an_absent_calibration_is_refused_once_the_default_appears(self):
        # Codex #97 P1: compose auto-discovers the canonical default file, so
        # a stale mode="none" descriptor no longer replays the current source
        # snapshot once that file exists. Trusting it would export
        # uncalibrated rewards while claiming the snapshot was replayed.
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.write_calibration(root)

            self.assert_refused(
                self.summary_for(None, None, mode="none", records=0),
                root,
                "recompose the source run before exporting",
            )

    def test_the_calibration_path_must_be_an_absolute_string(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            _path, digest = self.write_calibration(root)
            for bad in ("", None, 17):
                with self.subTest(path=bad):
                    summary = self.summary_for(None, digest)
                    summary["calibration"]["path"] = bad
                    self.assert_refused(summary, root, "must be an absolute string")

            summary = self.summary_for(None, digest)
            summary["calibration"]["path"] = "relative/units-migration.json"
            self.assert_refused(summary, root, "calibration.path must be absolute")

    def test_a_source_run_path_outside_the_canonical_location_is_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path, digest = self.write_calibration(root, canonical=False)

            self.assert_refused(
                self.summary_for(path, digest),
                root,
                "source-run calibration path is not canonical",
            )

    def test_an_explicit_calibration_may_live_anywhere_absolute(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path, digest = self.write_calibration(root, canonical=False)

            catalog, descriptor = self.authenticate(
                self.summary_for(path, digest, mode="explicit"), root
            )

        self.assertEqual(set(catalog), {"ffpc-r5-002"})
        self.assertEqual(descriptor["mode"], "explicit")

    def test_a_digest_mismatch_is_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path, _digest = self.write_calibration(root)

            self.assert_refused(
                self.summary_for(path, "0" * 64),
                root,
                "calibration digest mismatch",
            )

    def test_an_unsupported_mode_is_refused(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path, digest = self.write_calibration(root)

            self.assert_refused(
                self.summary_for(path, digest, mode="inherited"),
                root,
                "unsupported calibration mode",
            )

    def test_the_calibrated_record_count_must_authenticate(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path, digest = self.write_calibration(root)

            # The descriptor claims two calibrated records; the file has one.
            self.assert_refused(
                self.summary_for(path, digest, records=2),
                root,
                "calibrated record count does not authenticate",
            )
            # The descriptor agrees with the file, but the summary disagrees.
            self.assert_refused(
                self.summary_for(path, digest, records=1, calibrated=2),
                root,
                "calibrated record count does not authenticate",
            )

    def test_calibration_rewritten_during_source_replay_is_refused(self):
        """Replay may not combine source bytes with stale calibration evidence."""

        import export_replay
        from compose_curated_test_support import build_source_run

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = build_source_run(root / "run")
            calibration, _digest = self.write_calibration(source)
            curated = root / "curated"
            compose_curated.compose_run(source, curated)
            real_replay = export_replay._replay_source_lines

            def replay_then_rewrite(*args, **kwargs):
                snapshot = real_replay(*args, **kwargs)
                before = calibration.stat()
                calibration.write_bytes(calibration.read_bytes())
                os.utime(
                    calibration,
                    ns=(before.st_atime_ns, before.st_mtime_ns),
                )
                return snapshot

            with mock.patch.object(
                export_replay,
                "_replay_source_lines",
                side_effect=replay_then_rewrite,
            ):
                with self.assertRaisesRegex(
                    export_hf.ExportError,
                    "calibration evidence changed during source replay",
                ):
                    export_hf.export_run(curated, root / "export")
            self.assertFalse((root / "export").exists())


class CalibrationPayloadLoading(unittest.TestCase):
    """Only well-formed calibration entries reach the catalog."""

    def load(self, text):
        payload = text.encode("utf-8") if isinstance(text, str) else text
        return export_hf._load_calibration_payload(payload, Path("/pinned/units.json"))

    def assert_refused(self, text, fragment):
        with self.assertRaises(export_hf.ExportError) as caught:
            self.load(text)
        self.assertIn(fragment, str(caught.exception))

    def test_a_non_utf8_payload_is_refused(self):
        self.assert_refused(b'{"records": []}\xff', "payload is not UTF-8")

    def test_records_must_be_a_list(self):
        for document in ('{"records": {}}', "{}", "[]"):
            with self.subTest(document=document):
                self.assert_refused(document, "records must be a list")

    def test_unusable_entries_are_skipped_rather_than_fatal(self):
        catalog = self.load(
            calibration_document(
                "not an object",
                {"usd_conversion_factor": 0, "scope": "ffpc-r5-001"},
                {"usd_conversion_factor": -2, "scope": "ffpc-r5-004"},
                {"usd_conversion_factor": "0.5", "scope": "ffpc-r5-005"},
                {"usd_conversion_factor": 0.25, "scope": 17},
                {"usd_conversion_factor": 10**400, "scope": "ffpc-r5-006"},
                {"usd_conversion_factor": 10**305, "scope": "ffpc-r5-007"},
                {"usd_conversion_factor": 0.25, "scope": "ffpc-r5-002"},
            )
        )

        # Only the last entry is usable; a zero, negative, non-numeric factor
        # or non-string scope is evidence we cannot convert, not a hard error.
        self.assertEqual(set(catalog), {"ffpc-r5-002"})
        self.assertEqual(catalog["ffpc-r5-002"]["canonical_factor"], 0.25)
        self.assertTrue(catalog["ffpc-r5-002"]["evidence_ref"].endswith("#/records/7"))

    def test_one_scope_calibrates_every_record_it_names(self):
        catalog = self.load(
            calibration_document(
                {
                    "usd_conversion_factor": 0.5,
                    "scope": "covers ffpc-r5-002 and ffpc-r5-003",
                }
            )
        )

        self.assertEqual(set(catalog), {"ffpc-r5-002", "ffpc-r5-003"})

    def test_the_same_factor_from_two_entries_still_conflicts(self):
        # Fail closed: the calibration carries its own ``evidence_ref``, so
        # two entries calibrating one record are ambiguous provenance even
        # when the factor agrees -- there is no single record to cite.
        self.assert_refused(
            calibration_document(
                {"usd_conversion_factor": 0.5, "scope": "ffpc-r5-002"},
                {"usd_conversion_factor": 0.5, "scope": "ffpc-r5-002"},
            ),
            "conflicting calibrations for ffpc-r5-002",
        )

    def test_conflicting_calibrations_for_one_record_are_refused(self):
        self.assert_refused(
            calibration_document(
                {"usd_conversion_factor": 0.5, "scope": "ffpc-r5-002"},
                {"usd_conversion_factor": 0.25, "scope": "ffpc-r5-002"},
            ),
            "conflicting calibrations for ffpc-r5-002",
        )


class StrictExportJsonLoading(unittest.TestCase):
    def test_overflowed_json_numbers_are_refused(self):
        for literal in ("1e9999", "-1e9999"):
            with self.subTest(literal=literal):
                with self.assertRaisesRegex(export_hf.ExportError, "non-finite"):
                    export_hf._loads_json(f'{{"value":{literal}}}', "payload")

    def test_deep_json_is_wrapped_as_an_export_error(self):
        with mock.patch.object(
            export_contract.json,
            "loads",
            side_effect=RecursionError("decoder recursion limit"),
        ):
            with self.assertRaisesRegex(export_hf.ExportError, "invalid JSON"):
                export_hf._loads_json("[]", "payload")

    def test_duplicate_object_keys_are_rejected_at_every_depth(self):
        """Authenticated JSON must have one unambiguous value per key."""

        for payload in (
            '{"action":"bogus","action":"retained"}',
            '{"entry":{"action":"bogus","action":"retained"}}',
        ):
            with self.subTest(payload=payload):
                with self.assertRaisesRegex(
                    export_hf.ExportError,
                    "duplicate JSON object key 'action'",
                ):
                    export_hf._loads_json(payload, "authenticated evidence")


if __name__ == "__main__":
    unittest.main()
