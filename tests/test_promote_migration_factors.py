"""How pipelines/promote.py builds reward-scale entries from units-migration factors."""

import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

PIPELINES = Path(__file__).resolve().parents[1] / "pipelines"
if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

promote = importlib.import_module("promote")


def _migration_run(root, factor):
    """A raw run whose FFPC batch is scoped by one migration record carrying ``factor``."""

    ffpc = root / "raw" / promote.FFPC
    ffpc.mkdir(parents=True)
    (ffpc / "batch-r02.jsonl").write_text(json.dumps({"meta": {"id": "a"}}) + "\n")
    (ffpc / "units-migration.json").write_text(json.dumps({"records": [
        {"scope": "batch-r02.jsonl / a", "usd_conversion_factor": factor},
    ]}))
    return root / "raw", Path(promote.FFPC) / "batch-r02.jsonl"


class UnhashableMigrationFactors(unittest.TestCase):
    def test_a_list_or_object_factor_aborts_the_reward_scale(self):
        """A list or object factor raises before any single-factor fallback.

        This pins the behaviour main already has (the factors are compared as a
        set first), so a refactor cannot change it silently. Normalizing such
        factors instead would be a deliberate change, made together with this test.
        """
        for factor in ([0.2], {"usd": 0.2}):
            with self.subTest(factor=factor), tempfile.TemporaryDirectory() as td:
                raw, rel = _migration_run(Path(td), factor)
                with self.assertRaisesRegex(TypeError, "unhashable type"):
                    promote.build_reward_scale(raw, [rel])


if __name__ == "__main__":
    unittest.main()
