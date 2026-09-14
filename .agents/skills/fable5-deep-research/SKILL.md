---
name: fable5-deep-research
description: Deep-research orchestration for Fable 5 Ultracode synthetic data — parallel swarm over 189-record corpus with SOTA grounding.
---

# Fable 5 Deep Research

Orchestrates massive parallel research over Fable 5 synthetic corpus `outputs/raw/2026-08-17`.

## When to use

User asks for Fable 5, Ultracode, deep research, massive subagents, Grok + Muse-1.2 swarm.

## Swarm (8x Muse-1.2 + 2x Grok)

| # | Lens | Files |
|---|------|-------|
| 1 | Thalamic 75 | `thalamic-trajectory-factory/*.jsonl` |
| 2 | Bridge 39 | `neuromorphic-event-language-bridge/`, `curate_bridge.py` |
| 3 | Preference 42 | `failure-as-fuel-preference-cascade/`, `curate_preferences.py` |
| 4 | Coding 19 | `agentic-coding-trajectory-factory/`, `curate_coding.py` |
| 5 | Ouroboros 14 | `multi-agent-ouroboros-swarm/` |
| 6 | Curation | `.beads/issues.jsonl`, `provenance.md` |
| 7 | Ops pipeline | `round_txn.py`, `training_audit.py` |
| 8 | Safety/reward | `check_records.py`, `curate_rewards.py` |
| G1 | Grok census | `training_audit --strict` |
| G2 | Grok verify | `validate_run`, `quality_gate` |

Each subagent read-only, returns 5 bullets with file:line + SOTA link.

## Synthesis

Collect results, dedup, append one synthesis to Notion `3bfb11c3-7ce7-8056-ac11-fec43e6f01e7` end, create beads issue per net-new gap if needed.

## Constraints

Read-only on `outputs/raw/`, max 8 concurrent, never treat cannot-verify as verified.
