"""Shared scaffolding for the curation-gate integration test modules.

test_curate_gate.py (composition and manifest), test_curate_gate_plan.py,
test_curate_gate_lane_authentication.py, test_curate_gate_destination.py and
test_curate_gate_evidence_snapshots.py each cover one concern of
`curate_gate integrate`. The per-test temporary root and the integrate-refusal
assertions they share live here so no concern module repeats them; the
six-lane GateFixture and the record builders stay in gate_fixture.py.
"""

import json
import sys
import tempfile
from pathlib import Path

_TESTS = Path(__file__).resolve().parent
if str(_TESTS) not in sys.path:
    sys.path.insert(0, str(_TESTS))

from gate_fixture import _captured_main  # noqa: E402

REFUSED_EXIT_CODE = 2


def temp_root(case):
    """Return a fresh temporary directory that ``case`` removes when its test ends."""
    temp = tempfile.TemporaryDirectory(prefix="curate-gate-")
    case.addCleanup(temp.cleanup)
    return Path(temp.name)


def required_item(items):
    """Return the first of ``items``, failing the test clearly when there is none."""
    try:
        return next(iter(items))
    except StopIteration as exc:
        raise AssertionError("required item is missing") from exc


def rewrite_json(path, mutate):
    """Load the JSON document at ``path``, let ``mutate`` edit it in place, write it back."""
    document = json.loads(path.read_text())
    mutate(document)
    path.write_text(json.dumps(document))


class CurateGateAssertionsMixin:
    """Integrate-refusal and symlink helpers for ``unittest.TestCase`` subclasses."""

    def assert_integrate_refused(self, fixture, *messages, destination=None):
        """Run `integrate` on ``fixture``'s plan; assert exit 2 and every message on stderr."""
        cleaned = fixture.cleaned if destination is None else destination
        code, _report, stderr = _captured_main(
            [
                "integrate",
                "--plan",
                str(fixture.plan_path),
                "--cleaned-out",
                str(cleaned),
            ]
        )
        self.assertEqual(code, REFUSED_EXIT_CODE)
        for message in messages:
            self.assertIn(message, stderr)

    def assert_integrate_refused_without_output(self, fixture, *messages):
        """Assert `integrate` refuses with every message and leaves no cleaned tree."""
        self.assert_integrate_refused(fixture, *messages)
        self.assertFalse(fixture.cleaned.exists())

    def symlink_or_skip(self, link, target, *, directory=False):
        """Create ``link`` -> ``target``, skipping the test where symlinks are unavailable."""
        try:
            link.symlink_to(target, target_is_directory=directory)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks are unavailable on this platform")
