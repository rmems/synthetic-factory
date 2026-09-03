#!/usr/bin/env python3
"""Focused tests for the factory-registry rights contract."""

from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from dataclasses import FrozenInstanceError
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
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(
                identity.IdentityCurationError,
                "rights_profile_id must be hosted-frontier-research-only-v1",
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
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(
                identity.IdentityCurationError,
                r"generator must be a non-empty normalized string",
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
                with self.subTest(field=field, defect="missing"):
                    with self.assertRaisesRegex(
                        identity.IdentityCurationError,
                        rf"missing fields.*{field}",
                    ):
                        _load_temp_registry(
                            Path(tmp) / f"missing-{field}",
                            _registry_payload(
                                [missing],
                                schema_version="factory-registry-v0.1",
                            ),
                        )

                with self.subTest(field=field, defect="null"):
                    with self.assertRaisesRegex(
                        identity.IdentityCurationError,
                        rf"{field} must be a non-empty normalized string",
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
                with self.subTest(overrides=overrides):
                    with self.assertRaisesRegex(identity.IdentityCurationError, message):
                        _load_temp_registry(
                            Path(tmp) / str(index),
                            _registry_payload([_valid_row(**overrides)]),
                        )

    def test_loaded_rights_fields_are_immutable_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = _load_temp_registry(tmp, _registry_payload([_valid_row()]))
        row = registry.by_path_id["tmp-factory"]
        self.assertEqual(row.provider, "anthropic")
        self.assertEqual(row.channel, "consumer")
        self.assertEqual(row.rights_profile_id, "hosted-frontier-research-only-v1")
        self.assertEqual(row.intended_use, "research_only")
        self.assertEqual(row.project_training_policy, "blocked")
        with self.assertRaises(AttributeError):
            row.__dict__["project_training_policy"] = "allowed"
        with self.assertRaises(FrozenInstanceError):
            row.project_training_policy = "allowed"

        slots = type(row).__slots__
        state = [object.__getattribute__(row, name) for name in slots]
        state[slots.index("project_training_policy")] = "allowed"
        with self.assertRaisesRegex(TypeError, "initialized"):
            row.__setstate__(state)
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
                with self.subTest(field=field):
                    with self.assertRaisesRegex(
                        identity.IdentityCurationError,
                        f"unknown {field}",
                    ):
                        _load_temp_registry(
                            Path(tmp) / str(index),
                            _registry_payload([_valid_row(**{field: value})]),
                        )
