---
name: run-synthetic-factory-windows-monitor
description: "Monitor and advance bounded multi-lane synthetic-factory windows with transactional rounds, circuit breakers, and inter-window state management. Use this skill when running bounded synthetic-factory workflow windows in transactional mode, monitoring per-lane progress, handling partial lane failures via circuit breakers, or advancing to the next window phase."
trigger: "Use this skill when running bounded synthetic-factory workflow windows in transactional mode, monitoring per-lane progress, handling partial lane failures via circuit breakers, or advancing to the next window phase."
author: montoyaraul34
source_sessions:
  - montoyaraul34_montoyaraul34's Organization_default_b3b8d9ea-21c2-49ca-9569-bdb1d0e65557
contributors:
  - montoyaraul34
version: 1
created_by_agent: claude_code
created_at: 2026-08-30T21:15:52.766Z
updated_at: 2026-08-30T21:15:52.766Z
---

## When to use
You are running a multi-round synthetic campaign via transactional factory windows and need to:
- Monitor progress across independent factory lanes (TTF, swarm, NELB, FFPC, agentic)
- Handle lane failures gracefully (circuit breaker isolation, no cascade)
- Distinguish between "keep going" as "already running" vs. "launch next window"
- Track per-lane state (frontier position, records written, novel coverage %, stopped reason)
- Measure campaign health between windows (validate, audit, frontiers, token-efficiency)
- Advance through campaign blocks (Block A: 2 rounds per lane; Block B: rounds 3–4 adversarial/failure-heavy)

## Workflow
1. **Track per-lane state** — for each factory lane, maintain frontier position, committed records, novel coverage %, and stopped reason. Use tables to show lane | round | status for visibility.
2. **Circuit breaker isolation** — when a lane fails (model safeguard refusal, verification failure, session limit), mark it circuit-open; note it gets a clean retry in the next window. Other lanes continue uninterrupted.
3. **Interpret "keep going" intent**:
   - If agents are running: report their live status (transcript size, checkpoint time) and confirm the window auto-closes when done.
   - If the window closed: run the full measurement pass (validate → audit → frontiers → token-efficiency → leftover-mill), snapshot, then launch the next window with updated `starts` bounds.
4. **Report progress concisely** — show lane | round | records | coverage | status (✅/⏳/❌) for at-a-glance visibility on committed vs. running vs. failed lanes.
5. **Measure between windows** — always run the full post-window audit before launching the next one. This captures token efficiency, detects plateaus, and confirms audit training-readiness.

## Anti-patterns
- **Retrying model safeguard refusals immediately** — if a lane hits a model-level refusal (category `reasoning_extraction`, ToS violation), let it circuit-open and retry in the next window. Do not retry it in the same window.
- **Launching the next window without measurement** — always run validate/audit/frontiers/token-efficiency after a window closes, and snapshot, before advancing.
- **Treating "keep going" as a restart signal** — if the window is still running, confirm it with live status and let it close itself. Only launch the next window after measurement.
- **Losing per-lane frontier state** — track which lanes have committed/verified each round and which are retrying. This state gates entry into Block B (failure-heavy).

## Key files
- Workflow script: `.claude/skills/run-synthetic-factory/factory-window.workflow.js`
- Campaign progress: `outputs/raw/{date}/` (live agent transcripts, committed batches, marker verifier outputs)
- Measurement suite: validate, audit, frontiers, token-efficiency, leftover-mill (run in sequence)
- Baseline census: AGENTS.md (prior frozen record counts for canary validation)
