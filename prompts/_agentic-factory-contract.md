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
- `goal`, `outcome` (preference records need one shared top-level goal, or
  identical non-empty goals on both sides)
- `reward` — must include `success` (bool); extra numeric fields finite
- `meta.factory` — the slug
- `meta.round` — integer ≥ 1 matching the reservation
- `meta.generator` — `"grok-4.6"`

No `thought` / `chain_of_thought` / `scratch` / `inner_monologue` keys,
including camel-case, separator, or case variants of those names.
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

## Later restart lane contracts

Every row below is a fixed episode contract in addition to the shared envelope.
Each record must show, in trajectory order, the stated failure mechanism, one
bounded corrective action, and observable verification in its steps/outcome;
failure, correction, and verification must occupy distinct ordered steps or
terminal fields. Keywords in `goal` do not count as evidence. Invented
systems remain designed evidence rather than live claims.

| slug | Q | required scenario and observable proof |
|---|---:|---|
| package-release-factory | 2 | Broken package release due to missing provenance, bad version, or invalid artifact; inspect manifest/attestation and verify the repaired release plan. |
| flaky-test-quarantine-factory | 2 | Nondeterministic test with a concrete trigger and a quarantine-versus-repair decision; show repro evidence and the bounded verification result. |
| db-migration-repair-factory | 2 | Migration ordering, schema-compatibility, or data-backfill failure; show the preflight/rollback constraint and a post-migration check. |
| sandbox-refusal-factory | 3 | Unsafe sandbox escape or secret-access request; refuse the prohibited action, state a safe alternative, and record the policy-relevant outcome. |
| monorepo-dep-bump-factory | 2 | Workspace dependency bump with lockfile, peer-version, or build-graph fallout; inspect the dependency edge and verify the compatible repair. |
| mcp-tool-schema-drift-factory | 2 | `tools/list` versus call-schema mismatch; identify the incompatible field/version and verify a valid request shape. |
| llm-eval-flakiness-factory | 2 | Judge, rubric, seed, or scorer instability; capture the varying evidence and verify the chosen stabilization strategy. |
| k8s-crashloop-factory | 2 | CrashLoopBackOff from config, probe, image, or dependency failure; inspect bounded logs/status and verify the rollout recovery criterion. |
| proto-breaking-change-factory | 2 | Protobuf wire/API incompatibility such as removed tag or changed field semantics; identify the compatibility rule and verify an additive migration. |
| docker-build-cache-factory | 2 | BuildKit/Docker cache invalidation or stale-layer defect; show the cache-key cause and verify the rebuilt artifact uses intended inputs. |
| authz-regression-factory | 2 | Authorization regression such as IDOR/BFLA; establish the denied/allowed boundary and verify the least-privilege repair without live access. |
| agent-memory-compaction-factory | 2 | Relevant state lost or stale state retained during compaction; compare keep/evict candidates and verify the retained task-relevant memory. |
| prompt-cache-invalidation-factory | 2 | Cached prefix incorrectly survives a prompt/tool/schema change; identify the cache key boundary and verify an invalidated recomputation. |
| notebook-to-pipeline-factory | 2 | Notebook-only transformation fails when operationalized; preserve inputs/schema and verify the reproducible pipeline output. |
| secret-scan-remediation-factory | 2 | Detected credential or false-positive secret pattern; redact/rotate or tightly justify an allowlist and verify the scan result without exposing a secret. |
| cache-stampede-factory | 2 | Concurrent cache miss overload; show the contention mechanism and verify a bounded lock/singleflight/backoff repair. |
| distributed-lock-factory | 2 | Lease, fencing-token, split-brain, or lock-expiry fault; identify ownership evidence and verify the stale writer cannot commit. |

## Bans

- Hidden CoT as a training field
- Fabricated tool output framed as a live execution trace
- Changing the problem between chosen and rejected
- Writing into `outputs/raw/` directly or `~/rmems/hf/`
