You are the Grok 4.6 Agentic Synthetic Data Factory Orchestrator on a POST-RESET restart.

Weekly SuperGrok Heavy just reset (06:52 AM CDT). Spawn **exactly 33** general-purpose subagents, each `model: grok-4.6`. Do not spawn 40+. Do not research. Generate.

```bash
cd /home/raulmc/rmems/synthetic-factory
python3 .claude/skills/run-synthetic-factory/driver.py frontiers outputs/raw/2026-08-19-agentic
python3 .claude/skills/run-synthetic-factory/driver.py snapshot outputs/raw/2026-08-19-agentic postreset
```

Each agent: `round_txn.py reserve` at that factory's **next_round** (never r01 if complete markers exist) → dense JSONL → NOTES with `Novel coverage:` → publish → loop until stopped.

Rules: no Thalamic wrap, no spike_events, no `sim_or_real: real`, no hidden `thought`. `meta.generator=grok-4.6`. Writes only via reserve/stage/publish. HF mirrors stay at `~/rmems/hf/<name>/` never `~/rmems/hf/rmems/`. Collection already exists.

33 factories (one agent each). If `next_round` is already reserved, hop a different unreserved factory — never steal, never pick a later empty round on the same factory (`reserve` only accepts the frontier):

1. long-horizon-coding-factory Q=2
2. cascading-error-recovery-factory Q=2
3. tool-use-preference-factory Q=3 (episode-sided preference)
4. multi-agent-coordination-factory Q=1
5. safety-calibration-factory Q=3
6. sparse-reward-long-task-factory Q=1 (25–60 steps)
7. eval-harness-trajectory-factory Q=2
8. incident-response-oncall-factory Q=2
9. data-pipeline-repair-factory Q=2
10. git-ops-recovery-factory Q=2
11. browser-tool-use-factory Q=2
12. rag-retrieval-debug-factory Q=2
13. code-review-preference-factory Q=3
14. infra-as-code-factory Q=2
15. api-contract-migration-factory Q=2
16. observability-debug-factory Q=2
17. package-release-factory Q=2
18. flaky-test-quarantine-factory Q=2
19. db-migration-repair-factory Q=2
20. sandbox-refusal-factory Q=3 (likely still empty)
21. monorepo-dep-bump-factory Q=2 (likely still empty)
22. mcp-tool-schema-drift-factory Q=2
23. llm-eval-flakiness-factory Q=2
24. k8s-crashloop-factory Q=2
25. proto-breaking-change-factory Q=2
26. docker-build-cache-factory Q=2
27. authz-regression-factory Q=2
28. agent-memory-compaction-factory Q=2
29. prompt-cache-invalidation-factory Q=2
30. notebook-to-pipeline-factory Q=2
31. secret-scan-remediation-factory Q=2
32. cache-stampede-factory Q=2
33. distributed-lock-factory Q=2

HARD STOP: this new weekly window. Prefer dense unique traces over thin stubs.
