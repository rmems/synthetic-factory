# Grok census — 2026-08-17

**Author:** Grok 4.6 (xhigh)  
**Taken:** 2026-08-17T12:06:44Z  
**Trees:** `outputs/raw/2026-08-17/` (live) and `outputs/raw/2026-08-17-prehalt/` (pre-resume copy)

Notebook twin: Notion page `synthetic-factory` (`3bfb11c3-7ce7-8056-ac11-fec43e6f01e7`).

## Live vs prehalt vs last Notion scribe (09:36 UTC)

| | Live | Prehalt | Notion 09:36 |
|---|---:|---:|---:|
| JSONL files | 37 | 27 | — |
| Records | **138** | 90 | 134 |
| JSON parse failures | 0 | 0 | 0 |
| JSONL bytes | 3.06 MB | 1.84 MB | tree 4.16 MB incl. prose |
| Newest jsonl | nelb `batch-r09.jsonl` @ 09:40 UTC | coding `batch-r06.jsonl` @ 08:33 UTC | — |

Live kinds: **75 thalamic / 30 preference / 30 bridge_pair / 3 episode**.

| Factory | Live records | Live `batch-rNN` | Prehalt records | Prehalt batches |
|---|---:|---|---:|---|
| thalamic-trajectory-factory | 55 | 2–7 | 35 | 2–4, 6–7 (no r05) |
| failure-as-fuel-preference-cascade | 30 | 2–6 | 18 | 2–5 |
| neuromorphic-event-language-bridge | 30 | 2–9 | 18 | 2–5 |
| agentic-coding-trajectory-factory | 13 | 2–6 | 13 | 2–6 |
| multi-agent-ouroboros-swarm | 10 | 2–9 | 6 | 2–5 |

Resume at 08:11 UTC already rewrote some r03–r04 files in place (Notion 08:32). Prehalt is the only copy of the pre-resume 90. Do not treat live r03–r04 as the same objects that passed the 06:xx harvests.

## `sim_or_real` (every nested occurrence)

Live walk (not unique-per-record; preference pairs contribute two):

| Bucket | Count |
|---|---:|
| missing | 58 |
| exact `"real"` | 50 |
| `real*` / `live*` / production-flavored | 40 |
| simulation-flavored | 11 |
| HIL-flavored | 1 |
| other | 2 |

These are designed factory stories. Cleaned output must not emit `real`.

## Defects that a shape validator cannot see

- Live `manifest.json` is still `{files: 0}`. `validate_run.py` was never written against the live tree (only snapshots).
- `cleaned/` and `curated/` empty.
- Orchestrator counter is stale: swarm/nelb dispatched as “round 6” when r08 existed; ttf r07 landed before r04–r06; coding r06 (01:49 local) is older than coding r05 (04:23).
- Reward scales are not one convention. ffpc `units-migration.json` covers that factory’s r1–r4 only.
- Bridge r02 spike trains can be channel-grouped / not globally time-ordered (05:58 report). Later NOTES claim r04 restored order — unverified by a checker until `check_records.py`.
- Notion quality section still ranks “cascading hallucination” as open. Later ffpc NOTES claim `ffpc-r3-001` closed it. That is author self-report, not a second deep-read.

## This window (approved plan C)

Harden + first honest promotion. No new trajectories. No prompts 06/07. No crates.io `neuromod` / `axon-encoder`. Raw JSONL is append-only.

## After hardening (same day)

- `pipelines/{census,next_round,validate_run,check_records,promote}.py` landed; **40** unittests pass.
- `outputs/raw/2026-08-17/NEXT_ROUND.json`: coding/ffpc **7**, ttf **8**, swarm/nelb **10**. Those files do not exist yet.
- `validate_run.py` without `--write` reports 37/138/0 errors and leaves live `manifest.json` at `{files: 0}`.
- Raw `check_records`: **53 errors / 61 warnings** (5 spike-order + 48 reward-structure).
- Cleaned 37 jsonl / 138 records. Spike-order errors **0**. Reward-structure errors **48** remain (ffpc dict heads + `unit_usd`; swarm `actual`/weights). See `outputs/cleaned/2026-08-17/CHECK.md`.
- Cleaned `sim_or_real` never `real` (90 designed / 11 simulated / 1 hil / 2 unknown on records that had a claim).

