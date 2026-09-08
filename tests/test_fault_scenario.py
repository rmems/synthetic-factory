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
    fault_parameters,
    fault_scenario,
    fault_simulator,
    fault_tiers,
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

    def test_the_fixture_0015_stream_is_reproduced(self):
        proposal = propose(SEED, 16)[15]
        self.assertEqual(
            proposal["intervention"],
            {
                "kind": "malformed_spike_burst",
                "parameters": {"channels": ["c0", "c1", "c2"], "malformed_count": 1, "malformed_kind": "unknown_channel"},
            },
        )
        self.assertEqual(proposal["scenario"]["system"]["min_healthy_channels"], 2)

    def test_only_the_generator_imports_random(self):
        for module in (fault_simulator, fault_tiers):
            with self.subTest(module=module.__name__):
                self.assertFalse(hasattr(module, "random"))
                self.assertNotIn("import random", inspect.getsource(module))
        self.assertIn("import random", inspect.getsource(fault_scenario))


class RequestRefusals(unittest.TestCase):
    def test_count_must_be_a_genuine_integer_of_at_least_one(self):
        for count in (0, -1, 2.0, True):
            with self.subTest(count=count), refusal(self, fv.FINDING_COUNT_OUT_OF_DOMAIN, "count must be >= 1"):
                propose(SEED, count)

    def test_seed_must_be_a_genuine_integer_never_a_bool(self):
        for seed in ("abc", 2.0, True):
            with self.subTest(seed=seed), refusal(self, fv.FINDING_SEED_NOT_AN_INTEGER, "seed"):
                propose(seed, 1)

    def test_a_negative_seed_is_refused_so_no_seed_aliases_its_absolute_value(self):
        """``random.Random(-n)`` draws the stream of ``n``; refusing ``-n`` keeps
        'a different seed yields different content' true for every accepted seed."""
        for seed in (-1, -5, -SEED):
            with self.subTest(seed=seed), refusal(self, fv.FINDING_SEED_NOT_AN_INTEGER, "non-negative"):
                propose(seed, 1)
        with refusal(self, fv.FINDING_SEED_NOT_AN_INTEGER, "non-negative"):
            fault_oracle.build_records(-5, 1)
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
                fault_parameters.checked_disturbance(proposal["intervention"], system)
                self.assertIn(engine.run(proposal["scenario"], proposal["intervention"]).outcome, fv.OUTCOMES)
                varied = {k for k, v in system.items() if v != fv.DEFAULT_SYSTEM[k]}
                self.assertTrue(varied <= {"min_healthy_channels", "fallback_source"}, varied)
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

