#!/usr/bin/env python3
"""Direct tests of ``fault_scenario``: seed determinism, request refusals,
generator/oracle separation, and that every generated configuration passes
the configuration and disturbance gates by construction."""

import inspect
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fault_test_support import (
    SEED,
    ensure_policy,
    envelope,
    fault_config,
    fault_oracle,
    fault_scenario,
    fault_simulator,
    fault_vocabulary as fv,
    oc,
    refusal,
)

propose = fault_scenario.propose_scenarios


class SeededStream(unittest.TestCase):
    def test_the_same_seed_reproduces_the_same_proposals(self):
        self.assertEqual(propose(SEED, 18), propose(SEED, 18))
        self.assertNotEqual(propose(SEED, 18), propose(SEED + 1, 18))

    def test_kinds_cycle_in_disturbance_order(self):
        self.assertEqual([p["intervention"]["kind"] for p in propose(SEED, 9)], list(fv.DISTURBANCES))
        counts = {kind: 0 for kind in fv.DISTURBANCES}
        for proposal in propose(SEED, 36):
            counts[proposal["scenario"]["disturbance_kind"]] += 1
        self.assertEqual(set(counts.values()), {4})

    def test_the_seed_stream_is_pinned_across_platforms(self):
        """The family's own draw stream (SHA-256 over seed and counter), pinned at
        two indexes of the fixture seed so a silent change to the draw order, the
        menus or the stream itself cannot keep this green."""
        proposals = propose(SEED, 16)
        self.assertEqual(
            proposals[0]["intervention"],
            {"kind": "sensor_loss", "parameters": {"channels": ["c0", "c1", "c2"], "onset_ms": 8.0, "duration_ms": 14.0}},
        )
        self.assertEqual(
            proposals[15]["intervention"],
            {
                "kind": "malformed_spike_burst",
                "parameters": {"channels": ["c2"], "malformed_count": 1, "malformed_kind": "negative_amplitude"},
            },
        )
        self.assertEqual(proposals[15]["scenario"]["system"]["min_healthy_channels"], 2)
        self.assertEqual(fault_scenario.DrawStream(0).bits(), 17227200041832915037)

    def test_no_family_module_imports_the_random_module(self):
        for module in (fault_scenario, fault_simulator, fault_oracle, fault_config):
            with self.subTest(module=module.__name__):
                self.assertNotIn("import random", inspect.getsource(module))
        stream, twin = fault_scenario.DrawStream(3), fault_scenario.DrawStream(3)
        self.assertEqual([stream.choice("ab") for _ in range(8)], [twin.choice("ab") for _ in range(8)])
        self.assertEqual(sorted(stream.sample(["c0", "c1", "c2", "c3"], 4)), ["c0", "c1", "c2", "c3"])
        self.assertTrue(all(1 <= stream.randint(1, 4) <= 4 for _ in range(50)))


class RequestRefusals(unittest.TestCase):
    def test_count_must_be_a_genuine_integer_of_at_least_one(self):
        for count in (0, -1, 2.0, True, fv.MAX_COUNT + 1, 10**5000):
            with self.subTest(count=fv.shown(count)[:24]), refusal(self, fv.FINDING_COUNT_OUT_OF_DOMAIN, "count must be >= 1"):
                propose(SEED, count)
        with refusal(self, fv.FINDING_COUNT_OUT_OF_DOMAIN, "an unprintable int of 16610 bits"):
            fault_oracle.build_records(SEED, 10**5000)

    def test_seed_must_be_a_genuine_integer_never_a_bool(self):
        for seed in ("abc", 2.0, True):
            with self.subTest(seed=seed), refusal(self, fv.FINDING_SEED_NOT_AN_INTEGER, "seed"):
                propose(seed, 1)

    def test_a_seed_outside_the_64_bit_domain_is_refused(self):
        """A seed is one unambiguous integer in ids and in ``generator.seed``, and
        the draw stream formats it as text: negative and wider-than-64-bit seeds
        are refused with a coded domain error, never a raw ``ValueError``."""
        for seed in (-1, -5, -SEED, fv.MAX_SEED + 1, 10**5000):
            with self.subTest(bits=seed.bit_length()), refusal(self, fv.FINDING_SEED_OUT_OF_DOMAIN, "must lie in [0"):
                propose(seed, 1)
        with refusal(self, fv.FINDING_SEED_OUT_OF_DOMAIN, "got an unprintable int of 16610 bits"):
            propose(10**5000, 1)
        with refusal(self, fv.FINDING_SEED_OUT_OF_DOMAIN, "must lie in [0"):
            fault_oracle.build_records(-5, 1)
        self.assertEqual(len(propose(fv.MAX_SEED, 2)), 2)
        # Direct construction is guarded by the same rule as the generator.
        for seed, code in ((-1, fv.FINDING_SEED_OUT_OF_DOMAIN), (fv.MAX_SEED + 1, fv.FINDING_SEED_OUT_OF_DOMAIN), (True, fv.FINDING_SEED_NOT_AN_INTEGER), ("7", fv.FINDING_SEED_NOT_AN_INTEGER)):
            with self.subTest(direct=repr(seed)), refusal(self, code, "seed"):
                fault_scenario.DrawStream(seed)
        content = [
            [(p["scenario"], p["intervention"]) for p in propose(seed, 9)] for seed in (0, 5, 6)
        ]
        self.assertEqual(len({repr(stream) for stream in content}), 3)


class ProposalsAreProposals(unittest.TestCase):
    def setUp(self):
        ensure_policy()

    def test_proposals_carry_no_oracle_owned_or_label_key(self):
        for proposal in propose(4, 9):
            record = {section: proposal[section] for section in ("scenario", "intervention", "candidate_prediction")}
            with self.subTest(index=proposal["index"]):
                self.assertEqual(oc.check_generator_oracle_separation(record, "p"), [])
                self.assertEqual(envelope.reserved_key_hits(record, fv.ORACLE_LABEL_KEYS), [])

    def test_every_generated_configuration_passes_both_gates_by_construction(self):
        engine = fault_simulator.RelayReflexSimulator()
        seen = set()
        for seed in range(1, 11):
            for proposal in propose(seed, 9):
                system = fault_config.checked_system(proposal["scenario"])
                fault_config.checked_disturbance(proposal["intervention"], system)
                self.assertIn(engine.run(proposal["scenario"], proposal["intervention"]).outcome, fv.OUTCOMES)
                varied = {k for k, v in system.items() if v != fv.DEFAULT_SYSTEM[k]}
                self.assertLessEqual(varied, {"min_healthy_channels", "fallback_source"}, varied)
                seen.add((system["min_healthy_channels"], system["fallback_source"]))
        self.assertEqual({budget for budget, _ in seen}, {2, 3})
        self.assertEqual({fallback for _, fallback in seen}, {"redundant_relay_b", None})

    def test_proposal_systems_are_private_copies(self):
        first, second = propose(SEED, 2)
        first["scenario"]["system"]["channels"].append("ghost")
        self.assertEqual(fv.DEFAULT_SYSTEM["channels"], ["c0", "c1", "c2", "c3"])
        self.assertEqual(second["scenario"]["system"]["channels"], ["c0", "c1", "c2", "c3"])

    def test_the_candidate_prediction_is_the_shallow_kind_keyed_lookup(self):
        for proposal in propose(SEED, 9):
            kind = proposal["intervention"]["kind"]
            predicted = fv.PREDICTION_BY_KIND[kind]
            with self.subTest(kind=kind):
                self.assertEqual(
                    proposal["candidate_prediction"],
                    {
                        "predicted_outcome": predicted,
                        "predicted_outcome_label": fv.OUTCOME_LABELS[predicted],
                        "method": fv.PREDICTION_METHOD,
                        "confidence": 0.5,
                    },
                )
                self.assertEqual(proposal["scenario"]["mission"], fv.MISSION)
