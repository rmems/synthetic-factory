"""Native count producers retain integer identity under the shared contract."""

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import energy_preferences as ep  # noqa: E402
import fault_recovery as fr  # noqa: E402
from oracle_grounded import distill_contract as oc  # noqa: E402


class IntegerCountProducers(unittest.TestCase):
    def test_process_meter_preserves_repeat_and_switch_counts(self):
        with (
            mock.patch.object(ep, "_context_switches", side_effect=[2**53, 2**53 + 3]),
            mock.patch.object(ep, "_reset_peak_rss", return_value=False),
        ):
            reading = ep.ProcessResourceMeter().measure(lambda: None, repeats=2, warmup=0)
        counts = {
            m["quantity"]: m["value"]
            for m in reading.extra
            if m["quantity"] in oc.INTEGER_QUANTITIES
        }
        self.assertEqual(counts, {"repeats": 2, "context_switches": 3})
        self.assertTrue(all(
            isinstance(value, int) and not isinstance(value, bool)
            for value in counts.values()
        ))

    @unittest.skipIf(ep.resource is None, "resource counters unavailable")
    def test_native_switch_counter_does_not_lose_integer_precision(self):
        usage = SimpleNamespace(ru_nvcsw=2**53, ru_nivcsw=3)
        with mock.patch.object(ep.resource, "getrusage", return_value=usage):
            value = ep._context_switches()
        self.assertIs(type(value), int)
        self.assertEqual(value, 2**53 + 3)

    def test_fault_counts_remain_integer_simulator_outputs(self):
        records = fr.build_records(3, 3)
        for item in records:
            counts = {
                m["quantity"]: m["value"]
                for m in item["result"]["measurements"]
                if m["quantity"] in oc.INTEGER_QUANTITIES
            }
            self.assertEqual(set(counts), {"healthy_channel_count", "dropped_event_count"})
            self.assertTrue(all(
            isinstance(value, int) and not isinstance(value, bool)
            for value in counts.values()
        ))


if __name__ == "__main__":
    unittest.main()
