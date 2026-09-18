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
        relatives = ["schemas/oracle-grounded-v1.schema.json"]
        relatives.extend(f"pipelines/{name}" for name in source_policy.PROGRAM_NAMES)
        for relative in relatives:
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


if __name__ == "__main__":
    unittest.main()
