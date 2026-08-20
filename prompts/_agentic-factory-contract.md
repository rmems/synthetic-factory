# Agentic factory contract (Grok 4.6 lane)

Training-data producers for `outputs/raw/2026-08-19-agentic/`. Not Thalamic.
Do not emit `spike_events`, Spikenaut, neuromorphic rasters, or
`sim_or_real: real`. Invented plants are `designed`.

## Transactional output

Same publisher as prompts 01–05:

1. `python3 pipelines/round_txn.py reserve <factory-dir> --round N --expected Q`
2. Write only into returned `staging_dir` at exact `batch_file` and `notes_file`.
3. One JSON object per nonblank JSONL line. No fences, headings, comments.
4. Nonempty NOTES with a `Novel coverage: <N>%` line, then
   `python3 pipelines/round_txn.py publish <factory-dir> --round N --token TOKEN`.
5. Repair staging only. Never overwrite committed raw. Never invent `c` suffixes.

## Shared envelope

Every JSONL line:

- `id` — globally unique string (`lhc-rNN-…`, `cer-rNN-…`, …)
- `goal`, `outcome`
- `reward` — must include `success` (bool); extra numeric fields finite
- `meta.factory` — the slug
- `meta.round` — integer ≥ 1 matching the reservation
- `meta.generator` — `"grok-4.6"`

No `thought` / `chain_of_thought` / `scratch` / `inner_monologue` keys.
Every tool step has observable `decision_basis` plus `tool_call` and `observation`.

## Factory quotas

| slug | Q | kind |
|---|---|---|
| long-horizon-coding-factory | 2 | episode |
| cascading-error-recovery-factory | 2 | episode |
| tool-use-preference-factory | 3 | preference (episode sides) |
| multi-agent-coordination-factory | 1 | multi_agent |
| safety-calibration-factory | 3 | safety_case |
| sparse-reward-long-task-factory | 1 | episode (25–60 steps) |
| eval-harness-trajectory-factory | 2 | episode (DeepEval/pytest eval loops) |
| incident-response-oncall-factory | 2 | episode (OpenSRE-style RCA, red herrings) |
| data-pipeline-repair-factory | 2 | episode (schema drift / late data) |
| git-ops-recovery-factory | 2 | episode (rebase, detached HEAD, CI) |
| browser-tool-use-factory | 2 | episode (selector fail + retry) |
| rag-retrieval-debug-factory | 2 | episode (wrong chunk / citation miss) |
| code-review-preference-factory | 3 | preference (episode sides) |
| infra-as-code-factory | 2 | episode (tf/k8s misconfig) |
| api-contract-migration-factory | 2 | episode (OpenAPI drift) |
| observability-debug-factory | 2 | episode (trace/metrics lie) |

## Bans

- Hidden CoT as a training field
- Fabricated tool output framed as a live execution trace
- Changing the problem between chosen and rejected
- Writing into `outputs/raw/` directly or `~/rmems/hf/`
