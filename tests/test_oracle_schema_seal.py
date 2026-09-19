"""Executable schema bytes belong to the independently reviewed source seal."""

import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipelines"))
from oracle_grounded import source_policy


class OracleSchemaSealTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for directory in ("pipelines/oracle_grounded", "schemas/oracle-grounded"):
            shutil.copytree(source_policy.ROOT / directory, self.root / directory)
        relatives = ["schemas/oracle-grounded-v1.schema.json", "LICENSE"]
        relatives.extend(f"pipelines/{name}" for name in source_policy.PROGRAM_NAMES)
        relatives.extend(("Cargo.toml", "Cargo.lock", "rust/sf-oracle/Cargo.toml",
                          "rust/sf-oracle/build.rs"))
        relatives.extend(f"rust/sf-oracle/src/{name}.rs"
                         for name in ("encoder", "identity", "main", "neuron", "protocol"))
        relatives.extend(("rust/nir-rs/Cargo.toml", "rust/nir-rs/src/main.rs",
                          "rust/nir-rs/src/meta.rs", "rust/nir-rs/src/codec.rs",
                          "rust/nir-rs/src/decode.rs", "rust/nir-rs/src/exec.rs",
                          "rust/silicon-bridge/Cargo.toml",
                          "rust/silicon-bridge/src/main.rs"))
        for relative in relatives:
            (self.root / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_policy.ROOT / relative, self.root / relative)
        patcher = mock.patch.object(source_policy, "ROOT", self.root)
        patcher.start()
        self.addCleanup(patcher.stop)
        source_policy.verify_source_bytes()

    def test_weakened_base_and_family_schemas_invalidate_source_authority(self):
        paths = [self.root / "schemas/oracle-grounded-v1.schema.json"]
        paths.extend(sorted((self.root / "schemas/oracle-grounded").glob("*.schema.json")))
        for path in paths:
            with self.subTest(schema=path.name):
                original = path.read_bytes()
                schema = json.loads(original)
                schema["additionalProperties"] = True
                path.write_text(json.dumps(schema))
                with self.assertRaises(source_policy.SourcePolicyError):
                    source_policy.verify_source_bytes()
                path.write_bytes(original)

    def test_missing_schema_invalidates_source_authority(self):
        paths = (
            self.root / "schemas/oracle-grounded-v1.schema.json",
            next((self.root / "schemas/oracle-grounded").glob("*.schema.json")),
        )
        for path in paths:
            with self.subTest(schema=path.name):
                original = path.read_bytes()
                path.unlink()
                with self.assertRaises(source_policy.SourcePolicyError):
                    source_policy.verify_source_bytes()
                path.write_bytes(original)

    def test_additional_family_schema_invalidates_source_authority(self):
        (self.root / "schemas/oracle-grounded/unreviewed.schema.json").write_text("{}")
        with self.assertRaises(source_policy.SourcePolicyError):
            source_policy.verify_source_bytes()

    def test_missing_or_changed_license_invalidates_source_authority(self):
        path = self.root / "LICENSE"
        original = path.read_bytes()
        for contents in (None, original + b"\nUnreviewed license change\n"):
            with self.subTest(missing=contents is None):
                path.unlink(missing_ok=True)
                if contents is not None:
                    path.write_bytes(contents)
                with self.assertRaises(source_policy.SourcePolicyError):
                    source_policy.verify_source_bytes()
                path.write_bytes(original)
        source_policy.verify_source_bytes()

    def test_shared_quarantine_helpers_are_sealed(self):
        for name in (
            "compose_destination_rename.py", "compose_destination_directory.py", "compose_contract.py",
        ):
            with self.subTest(helper=name):
                path = self.root / "pipelines" / name
                original = path.read_bytes()
                path.write_bytes(original + b"\n# unreviewed helper change\n")
                with self.assertRaises(source_policy.SourcePolicyError):
                    source_policy.verify_source_bytes()
                path.write_bytes(original)


class RustCatalogSealTests(unittest.TestCase):
    def test_rust_and_lock_changes_alter_independent_catalog_seal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in ("pipelines/oracle_grounded", "schemas/oracle-grounded", "rust"):
                shutil.copytree(source_policy.ROOT / relative, root / relative)
            for relative in ("Cargo.toml", "Cargo.lock", "schemas/oracle-grounded-v1.schema.json"):
                shutil.copyfile(source_policy.ROOT / relative, root / relative)
            package = root / "pipelines/oracle_grounded"
            baseline = source_policy.catalog_digest(package)
            for relative in ("Cargo.lock", "Cargo.toml", "rust/sf-oracle/Cargo.toml",
                             "rust/sf-oracle/build.rs", "rust/sf-oracle/src/encoder.rs",
                             "rust/sf-oracle/src/neuron.rs"):
                with self.subTest(relative=relative):
                    path = root / relative
                    original = path.read_bytes()
                    path.write_bytes(original + b"\n# altered authoritative runtime\n")
                    self.assertNotEqual(source_policy.catalog_digest(package), baseline)
                    path.write_bytes(original)


if __name__ == "__main__":
    unittest.main()
