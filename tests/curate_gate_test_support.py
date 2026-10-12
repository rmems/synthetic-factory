"""Shared TestCase base for the curation-gate integration test modules.

test_curate_gate.py (composition and manifest), test_curate_gate_plan.py,
test_curate_gate_lane_authentication.py, test_curate_gate_destination.py and
test_curate_gate_evidence_snapshots.py each cover one concern of
`curate_gate integrate`. The per-test temporary root they share lives here so
no concern module repeats it; the six-lane GateFixture and the record builders
stay in gate_fixture.py.
"""

import tempfile
import unittest
from pathlib import Path


class CurateGateCase(unittest.TestCase):
    """Give every test a fresh temporary root that is removed when it ends."""

    def setUp(self):
        self._temp = tempfile.TemporaryDirectory(prefix="curate-gate-")
        self.addCleanup(self._temp.cleanup)
        self.root = Path(self._temp.name)
