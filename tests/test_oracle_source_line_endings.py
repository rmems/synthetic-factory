"""Every byte-hashed authority input survives checkout newline conversion."""

from pathlib import Path
from fnmatch import fnmatchcase
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "pipelines"))
from oracle_grounded import source_policy  # noqa: E402


class OracleSourceLineEndings(unittest.TestCase):
    def test_all_policy_catalog_and_program_inputs_are_pinned_to_lf(self):
        members = list((ROOT / "pipelines/oracle_grounded").glob("*.py"))
        members.extend((ROOT / "schemas/oracle-grounded").glob("*.schema.json"))
        members.extend(ROOT / "pipelines" / name for name in source_policy.PROGRAM_NAMES)
        members.extend((
            ROOT / "schemas/oracle-grounded-v1.schema.json",
            source_policy.POLICY_PATH,
        ))
        paths = sorted(path.relative_to(ROOT).as_posix() for path in members)
        rules = [line.split() for line in (ROOT / ".gitattributes").read_text().splitlines()
                 if line.strip() and not line.startswith("#")]
        for path in paths:
            with self.subTest(path=path):
                matches = [fields[1:] for fields in rules if fnmatchcase(path, fields[0])]
                self.assertTrue(matches, "byte-hashed input has no checkout attributes")
                self.assertIn("eol=lf", matches[-1])



if __name__ == "__main__":
    unittest.main()
