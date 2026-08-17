# check_records on cleaned/2026-08-17

```
python3 pipelines/check_records.py outputs/cleaned/2026-08-17
```

Totals: 37 files, 138 records (75 thalamic / 30 preference / 30 bridge_pair / 3 episode). Exit 1. **48 errors, 61 warnings.**

## Spike order — gone

Raw had 5 globally unsorted `spike_events` trains (nelb `batch-r02.jsonl` lines 1–3, `batch-r03.jsonl` lines 2–3). Cleaned copies are time-sorted and carry `meta.spike_events_resorted: true`. Zero spike-order errors remain.

## Remaining errors (reward structure; not rewritten)

Promotion does not change `reward_components` totals. Checker still flags:

| File | n | Why |
|---|---:|---|
| `failure-as-fuel-preference-cascade/batch-r03.jsonl` | 12 | Dict heads (`task_progress.value` etc.) plus numeric `unit_usd: 10000` treated as an unweighted sibling; recomputed total collapses to 10000. |
| `failure-as-fuel-preference-cascade/batch-r04.jsonl` | 12 | Same dict-head / `unit_usd` pattern. |
| `failure-as-fuel-preference-cascade/batch-r05.jsonl` | 12 | Same. |
| `failure-as-fuel-preference-cascade/batch-r06.jsonl` | 6 | Same (3 pairs × chosen+rejected). |
| `multi-agent-ouroboros-swarm/batch-r05.jsonl` … `batch-r09.jsonl` | 5 | Weighted check: component values live under `actual`, so recompute is 0 vs stated total. |
| `multi-agent-ouroboros-swarm/final-trajectories.jsonl` | 1 | Weighted total 0.704 vs recomputed 0.7045 (5e-4 > 1e-4). |

ffpc `preferences.jsonl` and `batch-r02.jsonl` do not trip this (no `unit_usd` sibling / different shape).

## Warnings

61× missing `sim_or_real` on expected `state` objects (never present in raw). Cleaned attaches `provenance.kind: unknown` / `claimed: null` but does not invent `sim_or_real`. Not errors.

## Sidecars

- `reward-scale.json` — per factory/file. ffpc r1 `sign_order_only` (null factor); r02 `exclude_from_magnitude` (mixed 0.2 / 2.0 / null); r03–r04 `apply_usd_factor` 1.0; r05–r06 and every other factory `sign_order_only`.
- `PROVENANCE.md` — cleaned kinds never say `real`; raw is SoT.
