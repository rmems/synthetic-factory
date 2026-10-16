"""Tests for pipelines/promote.py claim remapping and per-record provenance."""

import json
import sys
import unittest
from pathlib import Path

TESTS = Path(__file__).resolve().parent
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))

from promote_test_support import CLAIMED_LIVE, _thalamic, promote


class TestRemapClaimed(unittest.TestCase):
    def test_production_actions_live_is_designed(self):
        prov = promote.remap_claimed(CLAIMED_LIVE)
        self.assertEqual(prov["kind"], "designed")
        self.assertEqual(prov["claimed"], CLAIMED_LIVE)

    def test_exact_real_is_designed(self):
        self.assertEqual(promote.remap_claimed("real")["kind"], "designed")
        self.assertEqual(promote.remap_claimed("REAL")["kind"], "designed")

    def test_live_prefix_is_designed(self):
        claimed = "live allocation; arbiter writes schedules"
        self.assertEqual(promote.remap_claimed(claimed)["kind"], "designed")
        self.assertEqual(promote.remap_claimed(claimed)["claimed"], claimed)

    def test_simulation_and_high_fidelity(self):
        hi = "high-fidelity plant simulation calibrated on telemetry"
        self.assertEqual(promote.remap_claimed(hi)["kind"], "simulated")
        self.assertEqual(
            promote.remap_claimed("operations-grade simulation calibrated on HIL valve")["kind"],
            "simulated",
        )

    def test_hil(self):
        self.assertEqual(
            promote.remap_claimed("hardware-in-the-loop (flight SPAD array)")["kind"],
            "hil",
        )
        self.assertEqual(promote.remap_claimed("hil-rig-3")["kind"], "hil")

    def test_missing_is_unknown_claimed_null(self):
        self.assertEqual(
            promote.remap_claimed(None),
            {"kind": "unknown", "claimed": None},
        )

    def test_unmatched_keeps_claimed(self):
        claimed = "decision-support in live IOC; the relay's disposition drives recovery"
        prov = promote.remap_claimed(claimed)
        self.assertEqual(prov["kind"], "unknown")

    def test_existing_provenance_still_strips_real_sim_or_real(self):
        rec = _thalamic()
        rec["provenance"] = {"kind": "designed", "claimed": "already stamped"}
        rec["state"]["sim_or_real"] = "real"
        out = promote.promote_record(rec)
        self.assertEqual(out["state"]["sim_or_real"], "designed")
        self.assertEqual(out["state"]["provenance"]["claimed"], "real")


class TestPromoteRecord(unittest.TestCase):
    def test_fixture_real_production_becomes_designed(self):
        rec = _thalamic()
        out = promote.promote_record(json.loads(json.dumps(rec)))
        self.assertEqual(out["provenance"]["kind"], "designed")
        self.assertEqual(out["provenance"]["claimed"], CLAIMED_LIVE)
        self.assertEqual(out["state"]["provenance"]["kind"], "designed")
        self.assertEqual(out["state"]["provenance"]["claimed"], CLAIMED_LIVE)
        self.assertEqual(out["state"]["sim_or_real"], "designed")
        self.assertNotEqual(out["state"]["sim_or_real"].lower(), "real")

    def test_remapped_state_claim_is_idempotent_across_two_passes(self):
        first = promote.promote_record(_thalamic(sim_or_real="real"))
        second = promote.promote_record(json.loads(json.dumps(first)))

        self.assertEqual(first["state"]["sim_or_real"], "designed")
        self.assertEqual(first["state"]["provenance"]["claimed"], "real")
        self.assertEqual(first["provenance"]["claimed"], "real")
        self.assertEqual(second, first)

    def test_nested_chosen_rejected_and_trajectory(self):
        pair = {
            "chosen": _thalamic(sim_or_real="real", meta={"id": "c"}),
            "rejected": _thalamic(
                sim_or_real="high-fidelity plant simulation",
                meta={"id": "r"},
            ),
            "critique": "process over luck",
            "meta": {"id": "pref-1"},
        }
        out = promote.promote_record(pair)
        self.assertEqual(out["chosen"]["provenance"]["kind"], "designed")
        self.assertEqual(out["chosen"]["state"]["sim_or_real"], "designed")
        self.assertEqual(out["chosen"]["provenance"]["claimed"], "real")
        self.assertEqual(out["rejected"]["provenance"]["kind"], "simulated")
        self.assertEqual(out["rejected"]["state"]["sim_or_real"], "simulated")

        bridge = {
            "language_view": {
                "trajectory": _thalamic(
                    sim_or_real="hardware-in-the-loop (flight SPAD array)"
                )
            },
            "spike_events": [
                {"channel": "a", "t_rel_ms": 10.0},
                {"channel": "b", "t_rel_ms": 20.0},
            ],
            "meta": {"id": "bridge-1"},
        }
        bout = promote.promote_record(bridge)
        traj = bout["language_view"]["trajectory"]
        self.assertEqual(traj["provenance"]["kind"], "hil")
        self.assertEqual(traj["state"]["sim_or_real"], "hil")

    def test_missing_sim_or_real_unknown(self):
        rec = _thalamic()
        del rec["state"]["sim_or_real"]
        out = promote.promote_record(rec)
        self.assertEqual(out["provenance"]["kind"], "unknown")
        self.assertIsNone(out["provenance"]["claimed"])
        self.assertEqual(out["state"]["provenance"]["kind"], "unknown")
        self.assertNotIn("sim_or_real", out["state"])

    def test_nested_state_provenance_precedes_default_unknown(self):
        record = {
            "id": "nested-provenance-1",
            "state": {
                "domain": "test",
                "provenance": {
                    "kind": "hil",
                    "claimed": "hardware-in-the-loop rig",
                },
            },
        }

        out = promote.promote_record(record)

        expected = {
            "kind": "hil",
            "claimed": "hardware-in-the-loop rig",
        }
        self.assertEqual(out["state"]["provenance"], expected)
        self.assertEqual(out["provenance"], expected)
        self.assertNotIn("sim_or_real", out["state"])

    def test_nested_state_provenance_precedes_root_provenance(self):
        record = {
            "id": "nested-provenance-2",
            "state": {
                "provenance": {
                    "kind": "simulated",
                    "claimed": "high-fidelity simulation",
                },
            },
            "provenance": {"kind": "unknown", "claimed": None},
        }

        out = promote.promote_record(record)

        self.assertEqual(out["state"]["provenance"]["kind"], "simulated")
        self.assertEqual(out["provenance"], out["state"]["provenance"])

    def test_rejected_nested_state_claim_precedes_canonical_root(self):
        record = {
            "id": "nested-provenance-3",
            "state": {"provenance": {"kind": "real"}},
            "provenance": {"kind": "hil", "claimed": "test rig"},
        }

        out = promote.promote_record(record)

        expected = {"kind": "designed", "claimed": "real"}
        self.assertEqual(out["state"]["provenance"], expected)
        self.assertEqual(out["provenance"], expected)

    def test_stateless_factory_record_is_stamped_designed(self):
        record = {
            "id": "coding-episode-1",
            "goal": "repair a queue consumer",
            "steps": [],
            "outcome": "verified",
            "meta": {"factory": "agentic-coding-trajectory-factory"},
            "provenance": {"kind": "unknown", "claimed": None},
        }

        out = promote.promote_record(record)

        self.assertEqual(out["provenance"]["kind"], "designed")
        self.assertIsNone(out["provenance"]["claimed"])
        self.assertEqual(out["provenance"]["inferred_from"], "meta.factory")

    def test_rejected_provenance_kind_keeps_its_claim(self):
        """A stateless wrapper whose provenance.kind is outside ALLOWED_KINDS
        used to be re-stamped with remap_claimed(None), erasing the original
        claim that PROVENANCE.md promises survives in provenance.claimed. The
        stateful path kept it, so the two disagreed about the same real-world
        claim (mergestorm #98, promote.py:153).
        """
        record = {
            "id": "coding-episode-2",
            "goal": "repair a queue consumer",
            "steps": [],
            "outcome": "verified",
            "meta": {"factory": "agentic-coding-trajectory-factory"},
            "provenance": {"kind": "real", "claimed": CLAIMED_LIVE},
        }

        out = promote.promote_record(record)

        # Cleaned records never emit `real` (PROVENANCE.md); the claim itself
        # is what survives, exactly as on the stateful path.
        self.assertEqual(out["provenance"]["kind"], "designed")
        self.assertEqual(out["provenance"]["claimed"], CLAIMED_LIVE)

    def test_rejected_kind_without_a_claim_is_itself_the_claim(self):
        record = {
            "id": "coding-episode-3",
            "steps": [],
            "meta": {"factory": "agentic-coding-trajectory-factory"},
            "provenance": {"kind": "real"},
        }

        out = promote.promote_record(record)

        self.assertEqual(out["provenance"]["kind"], "designed")
        self.assertEqual(out["provenance"]["claimed"], "real")

    def test_mix_bucket_does_not_depend_on_factory_envelope_metadata(self):
        """The same claim must land in the same mix bucket whether or not the
        record happens to carry meta.factory; otherwise synthetic_ratio, and
        the blocking mix verdict, moved on unrelated metadata.
        """
        def record(meta):
            out = {
                "id": "coding-episode-4",
                "steps": [],
                "provenance": {"kind": "real", "claimed": CLAIMED_LIVE},
            }
            if meta is not None:
                out["meta"] = meta
            return out

        with_factory = promote.promote_record(
            record({"factory": "agentic-coding-trajectory-factory"})
        )
        without_factory = promote.promote_record(record(None))

        self.assertEqual(
            with_factory["provenance"]["kind"], without_factory["provenance"]["kind"]
        )
        self.assertEqual(
            with_factory["provenance"]["claimed"],
            without_factory["provenance"]["claimed"],
        )

    def test_stateful_wrapper_without_sim_or_real_keeps_its_claim(self):
        record = {
            "id": "coding-episode-5",
            "state": {"note": "no sim_or_real key here"},
            "meta": {"factory": "agentic-coding-trajectory-factory"},
            "provenance": {"kind": "real", "claimed": CLAIMED_LIVE},
        }

        out = promote.promote_record(record)

        self.assertEqual(out["provenance"]["kind"], "designed")
        self.assertEqual(out["provenance"]["claimed"], CLAIMED_LIVE)
        self.assertEqual(out["state"]["provenance"]["claimed"], CLAIMED_LIVE)


if __name__ == "__main__":
    unittest.main()
