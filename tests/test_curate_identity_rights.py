#!/usr/bin/env python3
"""Focused tests for the factory-registry rights contract."""

from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from test_curate_identity import (
    FABLE_ACT,
    _load_temp_registry,
    _manifest_bytes,
    _registry_payload,
    _valid_row,
    episode,
    identity,
)


def _legacy_row(**overrides):
    row = _valid_row(**overrides)
    for field in (
        "provider",
        "channel",
        "rights_profile_id",
        "intended_use",
        "project_training_policy",
    ):
        row.pop(field)
    return row


class TestFactoryRegistryRightsContract(unittest.TestCase):
    def test_identity_tree_replays_copied_v01_registry_sidecar(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src"
            dest = Path(tmp) / "dest"
            factory = src / FABLE_ACT
            factory.mkdir(parents=True)
            (factory / "records.jsonl").write_text(
                identity.canonical_json(episode(FABLE_ACT)) + "\n",
                encoding="utf-8",
            )
            identity.write_run(src, dest)

            registry_path = dest / identity.FACTORY_REGISTRY_SIDECAR
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            registry["schema_version"] = "factory-registry-v0.1"
            hosted_frontier = {
                "fable-5",
                "gpt-5.6-sol",
                "grok-4.6",
                "muse-spark-1.2",
            }
            registry["factories"] = [
                row
                for row in registry["factories"]
                if row.get("source_type") != "procedural"
                and row.get("generator") in hosted_frontier
            ]
            rights_fields = (
                "provider",
                "channel",
                "rights_profile_id",
                "intended_use",
                "project_training_policy",
            )
            for row in registry["factories"]:
                for field in rights_fields:
                    row.pop(field)
            legacy_bytes = _manifest_bytes(registry)
            registry_path.write_bytes(legacy_bytes)

            manifest_path = dest / identity.IDENTITY_MANIFEST_SIDECAR
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            legacy_digest = hashlib.sha256(legacy_bytes).hexdigest()
            for mapping in manifest:
                mapping["registry"] = {
                    "schema_version": "factory-registry-v0.1",
                    "sha256": legacy_digest,
                }
            manifest_path.write_bytes(_manifest_bytes(manifest))

            loaded = identity.validate_identity_tree(dest)

            self.assertEqual(loaded.schema_version, "factory-registry-v0.1")
            self.assertEqual(loaded.sha256, legacy_digest)
            with self.assertRaisesRegex(
                identity.IdentityCurationError,
                "write_run requires factory-registry-v0.2",
            ):
                identity.write_run(src, Path(tmp) / "legacy-rewrite", registry=loaded)
            self.assertFalse((Path(tmp) / "legacy-rewrite").exists())

    def test_policy_known_fallback_profile_cannot_replace_hosted_profile(self):
        with (
            tempfile.TemporaryDirectory() as tmp,
            self.assertRaisesRegex(
                identity.IdentityCurationError,
                "generator/provider/channel assignment is not reviewed",
            ),
        ):
            _load_temp_registry(
                tmp,
                _registry_payload(
                    [
                        _valid_row(
                            rights_profile_id="unknown-provenance-fail-closed-v1"
                        )
                    ]
                ),
            )

    def test_legacy_rows_cannot_smuggle_rights_fields_and_v02_requires_them(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(
                identity.IdentityCurationError,
                "v0.1 rows must not declare rights fields",
            ):
                _load_temp_registry(
                    Path(tmp) / "legacy",
                    _registry_payload(
                        [_valid_row()],
                        schema_version="factory-registry-v0.1",
                    ),
                )

            for field in (
                "provider",
                "channel",
                "rights_profile_id",
                "intended_use",
                "project_training_policy",
            ):
                with self.subTest(field=field):
                    row = _valid_row()
                    row.pop(field)
                    with self.assertRaisesRegex(
                        identity.IdentityCurationError,
                        rf"missing fields.*{field}",
                    ):
                        _load_temp_registry(Path(tmp) / field, _registry_payload([row]))

    def test_legacy_invalid_generator_fails_with_precise_identity_error(self):
        with (
            tempfile.TemporaryDirectory() as tmp,
            self.assertRaisesRegex(
                identity.IdentityCurationError,
                r"generator must be a non-empty normalized string",
            ),
        ):
            _load_temp_registry(
                tmp,
                _registry_payload(
                    [_legacy_row(generator=["fable-5"])],
                    schema_version="factory-registry-v0.1",
                ),
            )

    def test_legacy_missing_or_null_generator_fields_get_precise_diagnostics(self):
        with tempfile.TemporaryDirectory() as tmp:
            for field in ("generator", "generator_version"):
                missing = _legacy_row()
                missing.pop(field)
                with (
                    self.subTest(field=field, defect="missing"),
                    self.assertRaisesRegex(
                        identity.IdentityCurationError,
                        rf"missing fields.*{field}",
                    ),
                ):
                    _load_temp_registry(
                        Path(tmp) / f"missing-{field}",
                        _registry_payload(
                            [missing],
                            schema_version="factory-registry-v0.1",
                        ),
                    )

                with (
                    self.subTest(field=field, defect="null"),
                    self.assertRaisesRegex(
                        identity.IdentityCurationError,
                        rf"{field} must be a non-empty normalized string",
                    ),
                ):
                    _load_temp_registry(
                        Path(tmp) / f"null-{field}",
                        _registry_payload(
                            [_legacy_row(**{field: None})],
                            schema_version="factory-registry-v0.1",
                        ),
                    )

    def test_unknown_drifting_and_misassigned_rights_fields_fail_closed(self):
        cases = (
            ({"provider": "unknown-provider"}, "unknown provider"),
            ({"channel": "unknown-channel"}, "unknown channel"),
            ({"rights_profile_id": "unknown-profile"}, "unknown rights_profile_id"),
            ({"intended_use": "unknown-use"}, "unknown intended_use"),
            (
                {"project_training_policy": "unknown-policy"},
                "unknown project_training_policy",
            ),
            (
                {"intended_use": "training_candidate"},
                "rights fields drift from loaded policy",
            ),
            (
                {"project_training_policy": "allowed"},
                "rights fields drift from loaded policy",
            ),
            (
                {"generator": "unknown-generator"},
                r"unknown reviewed \(generator, generator_version\)",
            ),
            (
                {"generator_version": "fable-6"},
                r"unknown reviewed \(generator, generator_version\)",
            ),
            (
                {"generator": "fable-5", "provider": "openai"},
                "generator/provider/channel assignment",
            ),
            (
                {"generator": "fable-5", "channel": "api"},
                "generator/provider/channel assignment",
            ),
        )
        with tempfile.TemporaryDirectory() as tmp:
            for index, (overrides, message) in enumerate(cases):
                with (
                    self.subTest(overrides=overrides),
                    self.assertRaisesRegex(identity.IdentityCurationError, message),
                ):
                    _load_temp_registry(
                        Path(tmp) / str(index),
                        _registry_payload([_valid_row(**overrides)]),
                    )

    def test_loaded_rights_fields_are_immutable_values(self):
        row = identity.default_registry().by_path_id[FABLE_ACT]
        self.assertEqual(row.provider, "anthropic")
        self.assertEqual(row.channel, "consumer")
        self.assertEqual(row.rights_profile_id, "hosted-frontier-research-only-v1")
        self.assertEqual(row.intended_use, "research_only")
        self.assertEqual(row.project_training_policy, "blocked")
        with self.assertRaises(AttributeError):
            row.__dict__["project_training_policy"] = "allowed"
        with self.assertRaises((AttributeError, TypeError)):
            row.project_training_policy = "allowed"

        original_policy = object.__getattribute__(row, "project_training_policy")
        try:
            with self.assertRaises((AttributeError, TypeError)):
                object.__setattr__(row, "project_training_policy", "allowed")
        finally:
            if object.__getattribute__(row, "project_training_policy") != original_policy:
                object.__setattr__(row, "project_training_policy", original_policy)

        self.assertEqual(row.project_training_policy, "blocked")
        self.assertEqual(copy.deepcopy(row), row)

    def test_non_string_rights_fields_fail_with_registry_errors(self):
        cases = (
            ("provider", []),
            ("channel", {}),
            ("rights_profile_id", []),
            ("intended_use", {}),
            ("project_training_policy", []),
        )
        with tempfile.TemporaryDirectory() as tmp:
            for index, (field, value) in enumerate(cases):
                with (
                    self.subTest(field=field),
                    self.assertRaisesRegex(
                        identity.IdentityCurationError,
                        f"unknown {field}",
                    ),
                ):
                    _load_temp_registry(
                        Path(tmp) / str(index),
                        _registry_payload([_valid_row(**{field: value})]),
                    )


def _attested_digest():
    return "sha256:" + "a" * 64


def _candidate_row(path_id, **fields):
    return _valid_row(
        path_id=path_id,
        payload_factory=path_id,
        generator_version="1",
        channel="local",
        intended_use="training_candidate",
        project_training_policy="allowed",
        **fields,
    )


def _attested_procedural_row(**overrides):
    row = _candidate_row(
        "procedural-attested-factory",
        generator="procedural-attested",
        provider="procedural",
        rights_profile_id="procedural-local-attested-v1",
        catalog_authorship="human-authored",
        generator_source_digest=_attested_digest(),
    )
    row.update(overrides)
    return row


def _simulator_row(**overrides):
    row = _candidate_row(
        "fault-recovery-simulator-factory",
        generator="relay-reflex-simulator",
        provider="simulator",
        rights_profile_id="simulator-local-oracle-v1",
        commit_sha="6ca641465bbf8ce8339de1dce6ce77f77186e34a",
        module_digest="sha256:be267e0720662cf1f8c79b24384bd335df9ec127fce8184459e2e64e31c8d3e4",
    )
    row.update(overrides)
    return row


def _placeholder_row(provider, **overrides):
    row = _valid_row(
        path_id=f"{provider}-placeholder-factory",
        payload_factory=f"{provider}-placeholder-factory",
        generator=f"{provider}-placeholder",
        generator_version="pending-terms",
        provider=provider,
        channel="api",
        rights_profile_id=f"{provider}-terms-placeholder-v1",
        intended_use="research_only",
        project_training_policy="blocked",
    )
    row.update(overrides)
    return row


class TestNewProviderRightsProfiles(unittest.TestCase):
    def test_sealed_procedural_row_is_training_candidate_without_hosted_provider(self):
        row = identity.default_registry().by_path_id["python-function-repair-factory"]
        self.assertIsNone(row.provider)
        self.assertIsNone(row.channel)
        self.assertEqual(row.source_type, "procedural")
        self.assertEqual(row.intended_use, "training_candidate")
        self.assertEqual(row.project_training_policy, "allowed")
        self.assertEqual(row.source_license_evidence["license"], "MIT")

    def test_procedural_row_without_attestation_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            hosted = _attested_procedural_row()
            hosted.pop("catalog_authorship")
            with self.assertRaisesRegex(
                identity.IdentityCurationError,
                "procedural rows require catalog_authorship",
            ):
                _load_temp_registry(Path(tmp) / "hosted", _registry_payload([hosted]))

        payload = json.loads(identity.FACTORY_REGISTRY_PATH.read_text(encoding="utf-8"))
        procedural = {row["path_id"]: row for row in payload["factories"]}[
            "python-function-repair-factory"
        ]
        procedural.pop("source_license_evidence")
        with (
            tempfile.TemporaryDirectory() as tmp,
            self.assertRaisesRegex(identity.IdentityCurationError, "drifts from independently sealed policy"),
        ):
            _load_temp_registry(tmp, payload)

    def test_attested_procedural_hosted_row_classifies_as_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            loaded = _load_temp_registry(tmp, _registry_payload([_attested_procedural_row()]))
        row = loaded.by_path_id["procedural-attested-factory"]
        self.assertEqual(row.provider, "procedural")
        self.assertEqual(row.channel, "local")
        self.assertEqual(row.rights_profile_id, "procedural-local-attested-v1")
        self.assertEqual(row.intended_use, "training_candidate")
        self.assertEqual(row.project_training_policy, "allowed")
        self.assertEqual(row.catalog_authorship, "human-authored")

    def test_simulator_pin_substitution_is_refused_for_copied_registries(self):
        document = json.loads(identity.FACTORY_REGISTRY_PATH.read_text())
        original = {row["path_id"]: row for row in document["factories"]}["fault-recovery-simulator-factory"]
        for field, replacement in (("commit_sha", "a" * 40), ("module_digest", "sha256:" + "a" * 64)):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp:
                altered = dict(original, **{field: replacement})
                with self.assertRaises(identity.IdentityCurationError):
                    _load_temp_registry(tmp, _registry_payload([altered]))

    def test_simulator_row_without_pins_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing_digest = _simulator_row()
            missing_digest.pop("module_digest")
            with self.assertRaisesRegex(
                identity.IdentityCurationError,
                r"module_digest must be lowercase sha256:<64 hex>",
            ):
                _load_temp_registry(Path(tmp) / "digest", _registry_payload([missing_digest]))
            missing_commit = _simulator_row()
            missing_commit.pop("commit_sha")
            with self.assertRaisesRegex(
                identity.IdentityCurationError,
                "commit_sha must be a 40-character lowercase git SHA",
            ):
                _load_temp_registry(Path(tmp) / "commit", _registry_payload([missing_commit]))

    def test_default_simulator_and_placeholder_rows_match_policy(self):
        registry = identity.default_registry()
        simulator = registry.by_path_id["fault-recovery-simulator-factory"]
        self.assertEqual(simulator.provider, "simulator")
        self.assertEqual(simulator.channel, "local")
        self.assertEqual(simulator.intended_use, "training_candidate")
        self.assertEqual(simulator.project_training_policy, "allowed")
        self.assertEqual(simulator.rights_profile_id, "simulator-local-oracle-v1")
        source = (
            Path(__file__).resolve().parent.parent
            / "pipelines"
            / "oracle_grounded"
            / "fault_simulator.py"
        )
        normalized = source.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
        self.assertEqual(
            simulator.module_digest,
            "sha256:" + hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
        )

        deepseek = registry.by_path_id["deepseek-placeholder-factory"]
        nemotron = registry.by_path_id["nemotron-placeholder-factory"]
        self.assertEqual(deepseek.project_training_policy, "blocked")
        self.assertEqual(nemotron.project_training_policy, "blocked")
        self.assertEqual(deepseek.rights_profile_id, "deepseek-terms-placeholder-v1")
        self.assertEqual(nemotron.rights_profile_id, "nemotron-terms-placeholder-v1")

    def test_placeholder_rows_cannot_self_promote_to_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            for provider in ("deepseek", "nemotron"):
                with self.subTest(provider=provider):
                    row = _placeholder_row(
                        provider,
                        intended_use="training_candidate",
                        project_training_policy="allowed",
                    )
                    with self.assertRaisesRegex(
                        identity.IdentityCurationError,
                        "rights fields drift from loaded policy",
                    ):
                        _load_temp_registry(
                            Path(tmp) / provider,
                            _registry_payload([row]),
                        )

    def test_existing_frontier_rows_keep_research_only_blocked(self):
        hosted = [
            row
            for row in identity.default_registry().by_path_id.values()
            if row.rights_profile_id == "hosted-frontier-research-only-v1"
        ]
        self.assertEqual(len(hosted), 51)
        for row in hosted:
            self.assertEqual(row.intended_use, "research_only")
            self.assertEqual(row.project_training_policy, "blocked")

