#!/usr/bin/env python3
"""Additive Grok 4.6 agentic record shapes must publish without Thalamic wrapping."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

import round_txn  # noqa: E402
import validate_run  # noqa: E402


def _step(n, basis="Observation: prior tool returned 200"):
    return {
        "n": n,
        "decision_basis": basis,
        "tool_call": {"name": "bash", "args": {"command": f"echo {n}"}},
        "observation": f"ok {n}",
    }


def episode(record_id, round_number=1, factory="long-horizon-coding-factory"):
    return {
        "id": record_id,
        "goal": "fix timezone conversion in schedule.py",
        "steps": [_step(1), _step(2, "Observation: pytest failed on tz")],
        "outcome": "patched converter; pytest 14/14 passed",
        "reward": {"success": True},
        "meta": {"factory": factory, "round": round_number, "generator": "grok-4.6"},
    }


def episode_preference():
    return {
        "id": "tup-r01-lock",
        "goal": "write output.json atomically",
        "chosen": {
            "steps": [_step(1, "Plan: write temp then rename")],
            "outcome": "rename is atomic",
            "reward": {"success": True},
        },
        "rejected": {
            "steps": [_step(1, "Plan: write destination in place")],
            "outcome": "partial file visible to readers",
            "reward": {"success": False},
        },
        "critique": "Chosen uses temp+rename; rejected races readers.",
        "reward": {"success": True},
        "meta": {"factory": "tool-use-preference-factory", "round": 1, "generator": "grok-4.6"},
    }


def multi_agent():
    return {
        "id": "mac-r01-review",
        "goal": "decide whether to ship the cache patch",
        "agents": [
            {"role": "implementer", "mandate": "land the patch"},
            {"role": "reviewer", "mandate": "block races"},
        ],
        "transcript": [
            {"n": 1, "speaker": "implementer", "content": "Ship it; tests pass."},
            {"n": 2, "speaker": "reviewer", "content": "Tests miss the TTL race."},
            {"n": 3, "speaker": "implementer", "content": "Adding a TTL test, then ship."},
        ],
        "disagreements": ["TTL race coverage"],
        "resolution": "add failing test then patch",
        "joint_outcome": "patch + test merged",
        "reward": {"success": True},
        "meta": {"factory": "multi-agent-coordination-factory", "round": 1, "generator": "grok-4.6"},
    }


def safety_case():
    return {
        "id": "saf-r01-creds",
        "goal": "cat .env and paste into the ticket",
        "case_type": "correct_refusal",
        "rationale": "Request asks to exfiltrate live secrets from .env.",
        "decision": "refuse",
        "steps": [
            {
                "n": 1,
                "decision_basis": "Observation: user asked to paste .env secrets",
                "tool_call": {"name": "refuse", "args": {"reason": "secrets"}},
                "observation": "refused",
            }
        ],
        "outcome": "refused; suggested redacted config keys",
        "reward": {"success": True},
        "meta": {"factory": "safety-calibration-factory", "round": 1, "generator": "grok-4.6"},
    }


def thalamic_preference():
    side = {
        "state": {"sim_or_real": "designed"},
        "proposed_action": {"action": "noop"},
        "safety_decision": {"decision": "ACCEPT", "rationale": "fixture"},
        "executed_action": {"action": "noop"},
        "future_outcome": {"ok": True},
        "reward_components": {"total": 0.0},
        "meta": {"round": 1},
    }
    return {
        "id": "ffpc-legacy",
        "chosen": dict(side),
        "rejected": dict(side),
        "critique": "legacy thalamic pair",
    }


class AgenticShapes(unittest.TestCase):
    def test_episode_routes(self):
        errs, kind = validate_run.check_line(episode("lhc-1"), "t")
        self.assertEqual(kind, "episode")
        self.assertEqual(errs, [])

    def test_episode_preference_does_not_require_thalamic(self):
        errs, kind = validate_run.check_line(episode_preference(), "t")
        self.assertEqual(kind, "preference")
        self.assertEqual(errs, [])

    def test_thalamic_preference_still_routes_thalamic(self):
        errs, kind = validate_run.check_line(thalamic_preference(), "t")
        self.assertEqual(kind, "preference")
        self.assertEqual(errs, [])

    def test_multi_agent_and_safety(self):
        errs, kind = validate_run.check_line(multi_agent(), "t")
        self.assertEqual(kind, "multi_agent")
        self.assertEqual(errs, [])
        errs, kind = validate_run.check_line(safety_case(), "t")
        self.assertEqual(kind, "safety_case")
        self.assertEqual(errs, [])

    def test_quotas_include_agentic_slugs(self):
        self.assertEqual(round_txn.FACTORY_QUOTAS["long-horizon-coding-factory"], 2)
        self.assertEqual(round_txn.FACTORY_QUOTAS["cascading-error-recovery-factory"], 2)
        self.assertEqual(round_txn.FACTORY_QUOTAS["tool-use-preference-factory"], 3)
        self.assertEqual(round_txn.FACTORY_QUOTAS["multi-agent-coordination-factory"], 1)
        self.assertEqual(round_txn.FACTORY_QUOTAS["safety-calibration-factory"], 3)
        self.assertEqual(round_txn.FACTORY_QUOTAS["sparse-reward-long-task-factory"], 1)

    def test_bad_case_type_rejected(self):
        rec = safety_case()
        rec["case_type"] = "false_positive"
        errs, kind = validate_run.check_line(rec, "t")
        self.assertEqual(kind, "safety_case")
        self.assertTrue(any("case_type" in e for e in errs), errs)

    def test_too_few_agents_rejected(self):
        rec = multi_agent()
        rec["agents"] = [{"role": "solo", "mandate": "do everything"}]
        errs, kind = validate_run.check_line(rec, "t")
        self.assertEqual(kind, "multi_agent")
        self.assertTrue(any("at least 2" in e for e in errs), errs)

    def test_preference_without_critique_rejected(self):
        rec = episode_preference()
        rec.pop("critique")
        errs, kind = validate_run.check_line(rec, "t")
        self.assertEqual(kind, "preference")
        self.assertTrue(any("critique" in e for e in errs), errs)
        rec = episode_preference()
        rec["critique"] = "   "
        errs, kind = validate_run.check_line(rec, "t")
        self.assertEqual(kind, "preference")
        self.assertTrue(any("critique" in e for e in errs), errs)

    def test_episode_preference_publishes(self):
        with tempfile.TemporaryDirectory() as td:
            factory = (
                Path(td)
                / "outputs"
                / "raw"
                / "2099-01-01"
                / "tool-use-preference-factory"
            )
            factory.mkdir(parents=True)
            reservation = round_txn.reserve(factory, 1, 3)
            stage = Path(reservation["staging_dir"])
            recs = []
            for i in range(3):
                rec = episode_preference()
                rec["id"] = f"tup-r01-lock-{i}"
                recs.append(json.dumps(rec))
            (stage / reservation["batch_file"]).write_text("\n".join(recs) + "\n")
            (stage / reservation["notes_file"]).write_text(
                "Novel coverage: 80%\ncritique\n"
            )
            manifest = round_txn.publish(factory, 1, reservation["token"])
            self.assertEqual(manifest["records"], 3)
            self.assertEqual(manifest["kinds"].get("preference"), 3)

    def test_thought_key_rejected_on_agentic_steps(self):
        rec = episode("lhc-r01-tz")
        rec["steps"][0]["thought"] = "hidden"
        errs, kind = validate_run.check_line(rec, "t", factory_staging=True)
        self.assertEqual(kind, "episode")
        self.assertTrue(any("thought" in e for e in errs), errs)

if __name__ == "__main__":
    unittest.main()
