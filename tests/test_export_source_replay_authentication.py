#!/usr/bin/env python3
"""Authenticate an export by replaying the source it claims."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from compose_curated_test_support import preference_pair, write_jsonl  # noqa: E402
from export_test_support import ONE_CALIBRATION, compose_fixture  # noqa: E402
import compose_curated  # noqa: E402
import export_compose_auth  # noqa: E402
import export_contract  # noqa: E402
import export_hf  # noqa: E402


class ExportSourceReplayAuthentication(unittest.TestCase):
    def test_direct_factory_root_replays_the_published_factory_coordinate(self):
        """Physical root members replay under the coordinate compose published."""

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "failure-as-fuel-preference-cascade"
            first = preference_pair(pure=True)
            first["id"] = "ffpc-r5-002"
            second = preference_pair(pure=True)
            second["id"] = "legacy-pref-second"
            second["critique"] = "second retained preference"
            write_jsonl(source / "batch-r01.jsonl", [first, second])
            (source / "units-migration.json").write_text(
                ONE_CALIBRATION,
                encoding="utf-8",
            )
            curated = root / "curated"
            summary = compose_curated.compose_run(source, curated)

            provenance = export_hf.export_run(curated, root / "export")

        self.assertEqual(summary["calibration"]["mode"], "source_run")
        self.assertEqual(summary["calibration"]["records"], 1)
        self.assertEqual(summary["calibrated_records"], 1)
        self.assertEqual(summary["counts"]["source_files"], 1)
        self.assertEqual(provenance["records"], 2)

    # ---- one tamper helper per mutation, all resealing digests coherently ----

    @staticmethod
    def _write_summary(ctx):
        ctx["summary_path"].write_text(
            json.dumps(ctx["summary"], indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    @staticmethod
    def _documents_of(path):
        return [json.loads(line) for line in path.read_text(encoding="utf-8").split("\n") if line]

    @classmethod
    def _reseal_documents(cls, ctx, path, documents, descriptor_key):
        payload = "".join(
            json.dumps(item, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
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
            lambda documents: cls._retained_row(documents).__setitem__("output_sha256", "0" * 64),
        )

    @classmethod
    def _mutate_coordinated_manifest_output_id(cls, ctx):
        cls._tamper_manifest(
            ctx,
            lambda documents: cls._retained_row(documents).__setitem__("output_id", "sfcur-forged"),
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

    def test_duplicate_captured_output_paths_are_refused(self):
        """One compose path must bind to exactly one captured byte snapshot."""

        captured = export_contract.CuratedFile(
            source_file="data/curated/duplicate.jsonl",
            payload=b"",
            rows=(),
        )

        with self.assertRaisesRegex(export_hf.ExportError, "duplicate captured output path"):
            export_compose_auth._curated_outputs_by_compose_path([captured, captured])

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
            json.dumps(entry, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
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


if __name__ == "__main__":
    unittest.main()
