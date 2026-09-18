"""Training-candidate profiles require sealed rows, sources and evidence states."""

import ast
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.test_curate_identity_rights import (
    _attested_procedural_row, _load_temp_registry, _registry_payload, identity,
)
from tests.test_rights_policy import mutable_policy_document, rights_policy
from pipelines import curate_identity_registry_sources as source_pins


def _reviewed_simulator_row():
    document = json.loads(identity.FACTORY_REGISTRY_PATH.read_bytes())
    rows = {row["path_id"]: row for row in document["factories"]}
    return rows["fault-recovery-simulator-factory"]


class ReviewedRegistryAssignments(unittest.TestCase):
    def test_simulator_authority_cannot_move_to_an_unreviewed_factory_or_shape(self):
        changes = (
            {"path_id": "unreviewed-factory"},
            {"payload_factory": "unreviewed-factory"},
            {"training_ready_policy": "compose_eligible"},
            {"record_kinds": ["coding"],
             "provenance_contract_by_kind": {"coding": "require_state_claim"}},
            {"identity_authoritative": False},
            {"publication_target": "unreviewed-publication"},
            {"allowed_curation_lanes": ["curate_identity", "curate_coding"]},
            {"provenance_contract_by_kind": {"thalamic": "synthetic_shape_implies_designed"}},
        )
        for change in changes:
            with self.subTest(change=change), tempfile.TemporaryDirectory() as temp:
                row = dict(_reviewed_simulator_row(), **change)
                with self.assertRaises(identity.IdentityCurationError):
                    _load_temp_registry(temp, _registry_payload([row]))

    def test_unreviewed_procedural_digest_cannot_grant_registry_authority(self):
        for authorship in ("human-authored", "permissive-upstream-license"):
            with self.subTest(authorship=authorship), tempfile.TemporaryDirectory() as temp:
                row = _attested_procedural_row(
                    catalog_authorship=authorship,
                    generator_source_digest="sha256:" + "0" * 64,
                )
                with self.assertRaises(identity.IdentityCurationError):
                    _load_temp_registry(temp, _registry_payload([row]))

    def test_changed_simulator_dependency_refuses_registry_authority(self):
        original = Path.read_bytes
        dependency = Path(__file__).resolve().parents[1] / "pipelines/oracle_grounded/fault_config.py"

        def changed_bytes(path):
            payload = original(path)
            return payload + b"\n# changed oracle dependency\n" if path == dependency else payload

        with tempfile.TemporaryDirectory() as temp, patch.object(Path, "read_bytes", changed_bytes):
            with self.assertRaises(identity.IdentityCurationError):
                _load_temp_registry(temp, _registry_payload([_reviewed_simulator_row()]))


class ReviewedEvidenceStatuses(unittest.TestCase):
    def test_candidate_evidence_statuses_cannot_be_self_authorized(self):
        for profile_id in (rights_policy.PROCEDURAL_PROFILE_ID, rights_policy.SIMULATOR_PROFILE_ID):
            self._assert_profile_statuses_sealed(profile_id)

    def _assert_profile_statuses_sealed(self, profile_id):
        fields = mutable_policy_document()["profiles"][0]["evidence_statuses"]
        for field in fields:
            with self.subTest(profile=profile_id, field=field):
                document = mutable_policy_document()
                profiles = {row["id"]: row for row in document["profiles"]}
                profile = profiles[profile_id]
                statuses = profile["evidence_statuses"]
                statuses[field] = "allowed" if statuses[field] == "unresolved" else "unresolved"
                with self.assertRaises(rights_policy.RightsPolicyError):
                    rights_policy.load_rights_policy_bytes(json.dumps(document).encode())


class SimulatorExecutableClosure(unittest.TestCase):
    def test_all_relative_executable_dependencies_are_pinned(self):
        root = Path(__file__).resolve().parents[1]
        declared = set(source_pins.SIMULATOR_SOURCE_PINS)
        for relative in declared:
            path = root / relative
            if path.suffix != ".py":
                continue
            dependencies = self._relative_dependencies(path)
            with self.subTest(source=relative):
                self.assertTrue(dependencies.issubset(declared), dependencies - declared)
        self.assertIn("pipelines/oracle_grounded/__init__.py", declared)
        self.assertIn("schemas/thalamic-trajectory.schema.json", declared)

    @classmethod
    def _relative_dependencies(cls, path):
        candidates = (
            candidate
            for node in ast.walk(ast.parse(path.read_bytes()))
            for candidate in cls._import_candidates(path, node)
        )
        root = Path(__file__).resolve().parents[1]
        return {str(candidate.relative_to(root)) for candidate in candidates if candidate.is_file()}

    @staticmethod
    def _import_candidates(path, node):
        if not isinstance(node, ast.ImportFrom) or not node.level:
            return ()
        names = (node.module,) if node.module else tuple(alias.name for alias in node.names)
        base = path.parents[node.level - 1]
        return tuple(base / (name.replace(".", "/") + ".py") for name in names)

    def test_each_pinned_dependency_drift_is_refused(self):
        original = Path.read_bytes
        root = Path(__file__).resolve().parents[1]
        for relative in source_pins.SIMULATOR_SOURCE_PINS:
            target = root / relative

            def substituted(path, target=target):
                payload = original(path)
                return payload + b"\n# drift\n" if path == target else payload

            with self.subTest(source=relative), patch.object(Path, "read_bytes", substituted):
                with self.assertRaises(identity.IdentityCurationError):
                    source_pins.require_simulator_sources()

    def test_unavailable_dependency_is_refused(self):
        with patch.object(Path, "read_bytes", side_effect=FileNotFoundError):
            with self.assertRaises(identity.IdentityCurationError):
                source_pins.require_simulator_sources()
