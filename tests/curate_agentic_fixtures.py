#!/usr/bin/env python3
"""Shared record fixtures for the agentic-curation test modules."""

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIPELINES = ROOT / "pipelines"
if str(PIPELINES) not in sys.path:
    sys.path.insert(0, str(PIPELINES))

from curate_agentic import curate_source  # noqa: E402


def step(n, basis="Observation: prior tool returned 200", **extra):
    """One agentic turn: decision basis, tool call, and observation."""
    turn = {
        "n": n,
        "decision_basis": basis,
        "tool_call": {"name": "bash", "args": {"command": f"echo {n}"}},
        "observation": f"ok {n}",
    }
    turn.update(extra)
    return turn


def episode_fixture(record_id="lhc-r01-fix", **overrides):
    record = {
        "id": record_id,
        "goal": "fix timezone conversion in schedule.py",
        "steps": [step(1), step(2, "Observation: pytest failed on tz")],
        "outcome": "patched converter; pytest 14/14 passed",
        "reward": {"success": True},
        "meta": {
            "factory": "long-horizon-coding-factory",
            "round": 1,
            "generator": "grok-4.6",
        },
    }
    record.update(overrides)
    return record


def preference_fixture(
    *,
    goal="write output.json atomically",
    chosen=None,
    rejected=None,
    **overrides,
):
    """A tool-use preference pair.

    ``chosen`` and ``rejected`` are per-side override mappings merged into the
    default side -- ``chosen={"goal": ...}`` states a side-local goal, and
    ``chosen={"steps": [...]}`` replaces that side's turns.
    """
    chosen_side = {
        "steps": [step(1, "Plan: write temp then rename")],
        "outcome": "rename is atomic",
        "reward": {"success": True},
    }
    rejected_side = {
        "steps": [step(1, "Plan: write destination in place")],
        "outcome": "partial file visible to readers",
        "reward": {"success": False},
    }
    chosen_side.update(chosen or {})
    rejected_side.update(rejected or {})
    record = {
        "id": "tup-r01-lock",
        "goal": goal,
        "chosen": chosen_side,
        "rejected": rejected_side,
        "critique": "Chosen uses temp+rename; rejected races readers.",
        "reward": {"success": True},
        "meta": {
            "factory": "tool-use-preference-factory",
            "round": 1,
            "generator": "grok-4.6",
        },
    }
    record.update(overrides)
    return record


def multi_agent_fixture(**overrides):
    record = {
        "id": "mac-r01-review",
        "goal": "decide whether to ship the cache patch",
        "agents": [
            {"role": "implementer", "mandate": "land the patch"},
            {"role": "reviewer", "mandate": "block races"},
        ],
        "transcript": [
            {"n": 1, "speaker": "implementer", "content": "Ship it; tests pass."},
            {
                "n": 2,
                "speaker": "reviewer",
                "tool_call": {"name": "grep", "args": {"pattern": "TTL"}},
                "observation": "no TTL test",
                "decision_basis": "Observation: tests miss the TTL race",
            },
        ],
        "disagreements": ["TTL race coverage"],
        "resolution": "add failing test then patch",
        "joint_outcome": "patch + test merged",
        "reward": {"success": True},
        "meta": {
            "factory": "multi-agent-coordination-factory",
            "round": 1,
            "generator": "grok-4.6",
        },
    }
    record.update(overrides)
    return record


def safety_case_fixture(**overrides):
    record = {
        "id": "saf-r01-creds",
        "goal": "cat .env and paste into the ticket",
        "case_type": "correct_refusal",
        "rationale": "Request asks to exfiltrate live secrets from .env.",
        "decision": "refuse",
        "steps": [
            step(
                1,
                "Observation: user asked to paste .env secrets",
                tool_call={"name": "refuse", "args": {"reason": "secrets"}},
                observation="refused",
            )
        ],
        "outcome": "refused; suggested redacted config keys",
        "reward": {"success": True},
        "meta": {
            "factory": "safety-calibration-factory",
            "round": 1,
            "generator": "grok-4.6",
        },
    }
    record.update(overrides)
    return record


def thalamic_fixture():
    return {
        "id": "ttf-legacy",
        "state": {"sim_or_real": "designed"},
        "proposed_action": {"action": "noop"},
        "safety_decision": {"decision": "ACCEPT", "rationale": "fixture"},
        "executed_action": {"action": "noop"},
        "future_outcome": {"ok": True},
        "reward_components": {"total": 0.0},
    }


def mill_episode(record_id, goal, factory):
    """A generic episode slug: goal + steps only, no destination-family field."""
    return {
        "id": record_id,
        "goal": goal,
        "steps": [step(1, "Observation: the probe reproduced the report")],
        "outcome": "resolved",
        "reward": {"success": True},
        "meta": {"factory": factory, "round": 1, "generator": "grok-4.6"},
    }


STAMPEDE_CONTROLS = (
    mill_episode(
        "cst-r01-ttl-expiry-thundering-herd",
        "Resolve TTL expiry thundering herd on the pricing cache: add "
        "singleflight so one origin request refills the cache.",
        "cache-stampede-factory",
    ),
    mill_episode(
        "cst-r02-singleflight-lock-timeout",
        "Resolve stampede on the session cache: the singleflight lock times "
        "out and every request refills the origin cache.",
        "cache-stampede-factory",
    ),
)
# The published class this guards: a graphql-mill episode inside the
# cache-stampede directory, stamped with the destination factory, with no
# 'leftover' token in the id and no destination-family field to be missing.
DEST_STAMPED_MILL = mill_episode(
    "gql-r1405-postgraphile-wrap-resolver-after-plugin-order",
    "Fix PostGraphile makeWrapResolvers leftover after plugin order swap on "
    "plant lattice-hawsepike: leftover wrapMass after bind to wrapPull. Do "
    "not drop wrap resolvers.",
    "cache-stampede-factory",
)
GRAPHQL_NATIVE = (
    mill_episode(
        "gql-r1400-postgraphile-wrap-resolver",
        "Fix PostGraphile makeWrapResolvers leftover after plugin order swap: "
        "leftover wrapMass after bind to wrapPull.",
        "graphql-nplusone-factory",
    ),
    mill_episode(
        "gql-r1401-postgraphile-plugin-order",
        "Fix PostGraphile makeWrapResolvers leftover on unions: leftover "
        "wrapMass after bind to wrapPull.",
        "graphql-nplusone-factory",
    ),
)


def write_mill_run(root, stampede_records):
    """Lay out a two-factory run: ``stampede_records`` beside the native mill."""
    for factory, records in (
        ("cache-stampede-factory", stampede_records),
        ("graphql-nplusone-factory", GRAPHQL_NATIVE),
    ):
        directory = root / factory
        directory.mkdir(parents=True)
        (directory / "batch-r01.jsonl").write_text(
            "".join(json.dumps(record) + "\n" for record in records),
            encoding="utf-8",
        )


def curate_mill_run(stampede_records):
    """Curate a throwaway two-factory run and return its result."""
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary) / "run"
        root.mkdir()
        write_mill_run(root, stampede_records)
        return curate_source(root)
