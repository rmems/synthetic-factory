# search-index-rebuild-factory — NOTES r50

Novel coverage: 85%

## Episodes
- `sir-r50-zombodb-refresh-vs-truncate`: 16 steps, success=True, domain=zombodb-refresh-vs-truncate-heap, seed=zombodb-refresh-vs-truncate
  - 502 at step 6 recovered 7; 429 at step 8 recovered 9
  - plan change at step 12: zdb.request _refresh. Do not TRUNCATE or DROP INDEX.
  - edit→test→fail→re-read→fix at steps 10-13
- `sir-r50-coveo-source-handoff`: 17 steps, success=False, domain=coveo-source-rebuild-vs-query, seed=coveo-source-handoff
  - 429 at step 6 recovered 7; 502 at step 8 recovered 9 (order may swap with success side)
  - plan change at step 12: Source push is coveo-plat. Handoff CV-SRC-2. Not TRUNCATE.
  - edit→test→fail→re-read→fix at steps 10-13

## decision_basis audit
Every step has decision_basis starting with Plan:/Observation:/Reflection:/Tool call:, length ≤240, no thought/chain_of_thought/scratch/inner_monologue keys, no spike_events, no sim_or_real real, no Spikenaut. Generator grok-4.6. No [variant …] goal stamp.

## Mix
Success: ['sir-r50-zombodb-refresh-vs-truncate']. Realistic failure/handoff: ['sir-r50-coveo-source-handoff'].

## Realism / weak recovery paths
Noise recoveries are backoff+retry or local fixture cache. First patches are domain-plausible and fail closed. Designed traces — not live executions.

## Step counts
- sir-r50-zombodb-refresh-vs-truncate: 16 (required 14–18)
- sir-r50-coveo-source-handoff: 17 (required 14–18)

## Weaknesses / next
Not TRUNCATE-then-reindex. Left sir-r26 placeholder in raw. Not TRUNCATE-then-reindex.
