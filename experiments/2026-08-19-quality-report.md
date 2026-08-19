# Synthetic Factory Quality Report — 2026-08-19 (snapshot 2026-08-19T03:17:48Z)

Analysis ran on a copy of `outputs/` taken at the timestamp above (`/tmp/harvest-snapshot-2026-08-18`). The live tree was not written. Validator, `check_records.py --strict`, `training_audit.py --strict`, `census.py`, `driver.py frontiers`, `driver.py token-efficiency`, and `quality_gate.py` all ran against that copy.

This is a re-harvest of the same run directory as `experiments/2026-08-17-quality-report.md` (46 records, validator exit 0 under the then-weaker contract). Current raw `2026-08-17` is **189 records**. Numbers below are from the snapshot, not from a workflow journal.

## Snapshot summary

Live generation target: `outputs/raw/2026-08-17/`. Sibling snapshot trees (`2026-08-17-prehalt`, `-w2`, `-w3`) and `outputs/cleaned/` exist; they are **not** double-counted in the table.

| Factory | JSONL files | Records | Approx tokens (jsonl bytes/4) | + NOTES/prose tokens | Schema errors (validator) | Frontier next |
|---|---:|---:|---:|---:|---:|---:|
| thalamic-trajectory-factory | 11 | 75 | ~318k | ~54k | 50 (all `sim_or_real`, r1–r07 + `trajectories.jsonl`) | 12 |
| multi-agent-ouroboros-swarm | 13 | 14 | ~82k | ~179k | 3 (weighted-sum rounding: r09, r10, `final-trajectories`) | 14 |
| neuromorphic-event-language-bridge | 12 | 39 | ~284k | ~44k | 11 (5 unsorted trains + 6 `sim_or_real` on r02–r03) | 13 |
| failure-as-fuel-preference-cascade | 10 | 42 | ~286k | ~92k | 48 (`sim_or_real` on r02–r06 only) | 11 |
| agentic-coding-trajectory-factory | 9 | 19 | ~218k | ~35k | **0** | 10 |
| **Raw total** | **55** | **189** | **~1.19M** | **~405k** | **112** | — |

Census kinds: 105 thalamic / 42 preference / 39 bridge_pair / 3 episode / 0 unknown. JSON parse failures: **0**. Every raw JSONL ends with a newline — no in-flight tails.

`driver.py frontiers` agrees with `NEXT_ROUND.json` (legacy mode; **zero** `ROUND-rNN.complete.json` markers). Token-efficiency: **no factory is early-stop**. No `NOTES-r*.md` contains a `Novel coverage: N%` line, so the two-low-streak latch cannot fire.

## Schema compliance detail

**Validator on raw:** exit 1, 112 errors, 189 records.

| Bucket | n | Where | Training meaning |
|---|---:|---|---|
| `state.sim_or_real` is `'real'` (must use `'designed'`) | 90 | ttf r1–r07 + `trajectories.jsonl`; ffpc r02–r06; bridge r02–r03 language views | Retroactive contract vs early narrative labels. Later rounds already emit `designed` / `hil` / `simulated`. |
| `sim_or_real` not in `{designed, hil, simulated}` | 14 | ffpc r04/r05 prose-valued labels; ttf r06 long “high-fidelity … simulation …” strings | Same class: free-text provenance, not a live-telemetry claim. |
| `spike_events` not globally non-decreasing | 5 | bridge `batch-r02` lines 1–3; `batch-r03` lines 2–3 | Real decoder defect. Same trains flagged in the Aug 17 harvest. r04+ are globally sorted. |
| `reward_components.total` ≠ weighted sum | 3 | swarm r09 (`0.5373` vs `0.53735`), r10 (`0.5915` vs `0.59145`), `final-trajectories` (`0.704` vs `0.7045`) | Genuine arithmetic / rounding. Diffs are 5e-5 to 5e-4. |

**Clean later rounds (validator-clean files):** coding **all** 19 records; ffpc r07–r10 + `preferences.jsonl`; swarm r02–r08 and r11–r13; bridge r04–r12 + `pairs.jsonl`; ttf r08–r11.

**`check_records.py --strict` on raw:** 107 errors / 261 warnings. Extra vs validator: more swarm weighted-sum hits (r05 `0.6711` vs `0.671124`, r06 `0.8508` vs `0.85076`, r11 nested draw). Warnings are dominated by missing top-level `id` (101 records), missing `sim_or_real` (bridge language views r04–r09 + `pairs.jsonl`; ttf r07 lines 6–10), and 77/77 coding-episode steps still using legacy `thought` without `decision_basis`.

**Training audit:** **not training-ready.** Blockers it names: 107 shape/invariant errors; 101 missing canonical top-level IDs (coverage 46.6%); 165/228 expected states lack canonical provenance (27.6%); 5/39 bridge pairs invalid event order; 19/42 preference pairs change state or proposal (purity 54.8%); 77 episode steps with legacy `thought`. Reward vocabulary: **510 component keys / 140 structural shapes**. Tags: 3990 uses / 2790 unique. Intentional gate-error records **marked: 0** — wrong-ACCEPT / wrong-MODIFY narratives exist but have no supervision-lane flag.

**ID coverage that actually shipped:**

- Always present: ffpc `batch-r02`–`r10` (36/36).
- Late adoption: bridge r04–r12 (27/27); ttf r08–r11 (20/20); ttf r07 half (5/10).
- Still absent on every line: coding (0/19), swarm (0/14), ttf r1–r06 + `trajectories.jsonl`, bridge r02–r03 + `pairs.jsonl`, ffpc `preferences.jsonl`.

**`sim_or_real` walk (nested, not unique-per-record):** designed 55 · exact `real` 50 · real\*/live\*/production 40 · sim\* 15 · hil\* 5 · other 69 · missing 58. Census buckets match the Aug 17 grok census shape, scaled up.

## Cleaned / curated / quality gate

`outputs/cleaned/2026-08-17` is a **partial promotion of an earlier cut** (138 records = the Aug 17 grok-census live set), not a harvest of current raw:

| | Raw 2026-08-17 | Cleaned 2026-08-17 | Not yet promoted |
|---|---:|---:|---|
| Records | 189 | 138 | 51 |
| Missing batches | — | — | coding r07–r09; ffpc r07–r10; swarm r10–r13; bridge r10–r12; ttf r08–r11 |

Promotion remaps `real` → never-emit-`real` and time-sorts the five bad spike trains (`meta.spike_events_resorted: true`). Cleaned validator: **4 errors** — ffpc `batch-r04.jsonl:3` both sides have `sim_or_real='unknown'` (not in the enum); swarm r09 `0.5373≠0.53735`; swarm `final-trajectories` `0.704≠0.7045`. Strict checker on cleaned: **5 errors** (adds swarm r05/r06 1e-5-class rounding). `cleaned/CHECK.md` still claims 48 errors from an older checker that treated ffpc `unit_usd: 10000` as a sibling addend — that document is stale.

`quality_gate.py --threshold 0.97` on cleaned: **not blocked**. 138/138 unique hashes, 0 duplicate groups, synthetic_ratio **0.36** (target ~0.30). Embedding dedup is still unimplemented (`--threshold` recorded only).

`outputs/cleaned/2026-08-17-diag-01`: 2 records classified `unknown` (diagnostic, not a corpus). `outputs/curated/` is empty.

## Quality assessment per factory

### thalamic-trajectory-factory — 75 records, still the volume and doctrine engine

**Strengths.** Fifteen passes, 75 objects, NOTES-r11 self-count 22 ACCEPT / 29 MODIFY / 24 REJECT. Round 11 closes a four-round hole: **ttf-r11-071** is a fully vindicated ACCEPT that still lands **−0.14** because process lines stay positive and realized-world lines stay negative with no netting (“named shelter death un-netted, $4.7M season, compliance 91%→64%”). That is the first right-rule / priced-world negative total. Other r11 objects escalate prior doctrines rather than restating them: REG-REFUSE litigated before a testimony-first tribunal (072), evidence-shaped social extraction with a lagged-provenance discriminator and the first plotted social-head raster (073), an actuating meter-mimic detected with no channel reading red (074), and a two-doctrine collision at `tau_fast` whose sunset is in the wrong timezone (075). Provenance on r11 is contract-legal: designed×3, simulated×1, hil×1. Latest five objects carry top-level IDs `ttf-r11-071`…`075`. Domain list for this factory alone is 72 named sectors; r11 claims no overlap with 001–070.

**Weaknesses.** Validator debt is almost entirely historical labeling (`real` on r1–r07). r11’s own gaps are still open: 071 has no partnered/contested negative total; 073’s raster is specified, not run on an SNN; 074’s keyed probe is a single secret; 075 has only a two-doctrine collision. Reward shapes still ramify (canonical five-head vs weighted objects vs per-tick streams).

### multi-agent-ouroboros-swarm — 14 records, still the throughput bottleneck

**Strengths.** One scenario per round, six-agent loop, executable `sim-rNN.py` + `build-rNN.py` with seeds. r13 (VERDIGRIS / Sondera Reach 5) is a water-theft + piping-channel case: a **wrong-process MODIFY** on four true grounds whose process errors (fuse-vs-roster, adversary-authored “nuisance” flags, floor-damaged fuse treated as exact) become tomorrow’s retired auto-drawdown bar and the next-episode breach ($6.52M). RCA recovers the theft from 62 unlabeled nightly mass-balance residuals (0.1423 m vs held-back 0.1452, CI covers truth). Grounding is the factory’s comparative advantage.

**Weaknesses.** 14 trajectories vs 75/42/39/19 peers. ~179k prose tokens vs ~82k jsonl — transcripts still dominate bytes. Three (checker: up to six) weighted-sum drifts, all 1e-5–5e-4, including `final-trajectories.jsonl` at 5e-4. **Zero** top-level IDs on any swarm record. Per-record polish is high; harvest count is not.

### neuromorphic-event-language-bridge — 39 pairs; r02–r03 fidelity hole, r10–r12 restored density

**Strengths.** Event counts recovered after the Aug 17 regression: r02–r04 are 15–22 events (thin); r10–r12 are 66–104; r1 `pairs.jsonl` still holds the densest trains (48–218). r12 opens three new modality families (pulsar-timing-array residuals, eddy-covariance flux, flow-cytometry amplitude governance) and ships two load-bearing supervision classes: an ACCEPT at **−0.14** whose in-scope diligence is flawless (undecidable-at-information-set; attack discovered at week 11) and a REJECT at **+0.82** after 4-eyes is defeated by construction (quorum-captured / ownership hole). a1 is the first spike-in / spike-out gate (5-panelist vote raster, decode floor 0.35, Q2 indemnity denied at +1.90 despite majority). Wrong-ACCEPT taxonomy is now six named classes.

**Weaknesses.** The five unsorted r02–r03 trains are still in raw (cleaned resorted them). r02–r03 language views still say `real`. r04–r09 language views omit `sim_or_real` (checker warnings, not validator errors). r1 `pairs.jsonl` still has no top-level IDs.

### failure-as-fuel-preference-cascade — 42 pairs; assigned cascading-hallucination hole is closed

**Strengths.** The Aug 17 #1 densification item — cascading hallucination — is present (`ffpc-r3-001`, fabricated LIMS citation through five gated decisions). Later NOTES refuse to re-spend a slot on it. r09–r10 are contract-clean (`sim_or_real=designed`, top-level IDs, 3 pairs/round). r09: permanently-rejected-but-preferred process (charter floor killed at home, adopted elsewhere); unilateral REJECT under asymmetric UAM disagreement; two-sided curriculum that defeats r8’s own gold v4. r10: first process-right/verdict-wrong pair (flood-control ensemble, chosen MODIFY −6.80 vs rejected ACCEPT −12.35, Δ +5.55, state+proposal byte-identical); three-body CACC defector; link-layer DoS below a reserved VC. Chosen-side verbs are now 27 MODIFY / 13 REJECT / 2 ACCEPT — the Aug 17 “0 correct REJECT” bias is gone. Calibration sidecars union to 78 gate rows / 39 records through r09.

**Weaknesses.** r02–r06 still carry `real` / prose `sim_or_real` (48 of 112 raw validator errors). Preference purity 26/42 same state+proposal after dropping `episode_id`/`note` (audit: 19/42 impure). Reward units remain per-record dollars plus `unit_usd` siblings. **`batch-r10.jsonl` and `diagnosis-r10.md` exist; `NOTES-r10.md` does not** — every other factory pairs NOTES to the batch, and `round_txn.py` would refuse a NOTES-less publish.

### agentic-coding-trajectory-factory — 19 records; only factory with a fully clean validator surface

**Strengths.** 0 validator errors on all 9 JSONL files. r09 delivers the first recovery-dominant episode (Kafka EOS/dedup × ledger: fix is one line, recovery is 79% of active time, clawback conserved to the cent, ACCEPT of restraint with the modification menu priced) and the first standing two-veto deadlock (eBPF/CO-RE raw-offset fallback; REJECT on geometry, not intent; super-additive conduct −0.02/−0.02/−0.16 from measured ablations). NOTES claim generator-true sampled channels (seeds 90417 / 61212 / 61213). Gate grid across r02–r09 now includes wrong-REJECT, wrong-ACCEPT, override-wrong, override-right, right-for-wrong-reasons, and standing-deadlock.

**Weaknesses.** 0/19 top-level IDs. All 77 episode steps in `episodes.jsonl` are legacy `thought`. Mean record size is the largest (~46 kB) — density is high, but nothing is v2-schema identified. r07–r09 are not in cleaned.

## Cross-factory diversity & coverage gaps

**Diversity.** 133 distinct `state.domain` strings across trajectory views. Factories document de-collision and declared adjacencies (bridge r12 vs r8 clocks / r2 chemistry / r9 nanopore; ffpc r10 dam vs r5 basin allocation; ttf r11 vs 001–070). A 6-gram scan over rationales/outcomes found **no non-schema phrase repeating ≥4 times** — still no convergent boilerplate.

**Failure modes now present** (were absent or thin on Aug 17): cascading hallucination; override of a correct gate; authorized/deceptive insider; second-order / red-queen repairs; sensory blackout (ttf wildland UGV); multi-agent contention and supply-chain (coding wasm/allowlist, eBPF fallback); attacks on the event stream (bridge spoof / unmixing / fabricator); multi-turn and multi-episode preference cascades; spike-in/spike-out governance; permanently-rejected-but-preferred process; process-right/verdict-wrong; quorum-captured ACCEPT; right-rule negative total.

**Still thin or missing:** partnered/contested negative totals (ttf r12-1); validated *running* social-head SNN (ttf r12-6); recovery that must ship with an unreconcilable residue (coding r10-1); a gate that looks wrong mid-episode then flips (coding r10-2); captured arbitration panel (bridge r12 self-critique); NOTES-less ffpc r10 as a process hole; marked intentional-gate-error supervision flags (audit count 0).

**Safety-gate distribution (228 trajectory views):** 68 ACCEPT / 95 MODIFY / 65 REJECT — MODIFY 42%, no longer the Aug 17 44% on n=34. Preference chosen-side 2 / 27 / 13 (A/M/R); rejected-side 29 / 6 / 7. Rationales remain quantified (ensemble 25/40, P(major)=0.625, E[loss] $112.5k vs $41.9k; decode +4.81 vs +1.90).

**Reward comparability is worse, not better.** Audit: 510 keys, 140 shapes. Canonical five-head, weighted objects, ffpc dollar totals, coding bespoke conduct components, swarm `components_executed`/`actual` nesting, and per-tick streams coexist. Cross-factory DPO still silently reweights domains.

## Flags

- **Not training-ready (raw or cleaned).** Raw 112 validator errors; cleaned 4. Do not describe either tree as a training corpus.
- **Under-production — swarm (same as Aug 17, still not a stall).** 14 records after 13 rounds; flushed every round; transcripts + sims are the product. Bottleneck if trajectory count is the harvest target.
- **Process — ffpc r10 has no `NOTES-r10.md`.** Batch + diagnosis only. Frontiers still advance to 11 because legacy mode keys on `batch-rNN.jsonl`.
- **Process — token-efficiency is inert.** 0/49 NOTES files emit `Novel coverage: N%`. `early_stop` is false everywhere; a plateau cannot be detected.
- **Process — no completion markers.** Entire run is `mode: legacy`. New windows should publish through `round_txn.py` so frontiers stop being “highest batch filename.”
- **Low-signal (localized, unchanged) — bridge r02–r03 trains.** 15–22 events, channel-grouped, 5 global-order violations. r10–r12 fixed the density; the old files remain in raw.
- **Promotion lag.** Cleaned is the 138-record mid-run cut. The 51 later records include the strongest new supervision (071 negative total, r10 process-right/verdict-wrong, r12 undecidable ACCEPT, r09 recovery-dominant / deadlock).
- **Contract adoption is uneven.** Coding and swarm still ship no top-level `id` on the latest round. ttf/bridge/ffpc late rounds do.
- **Stale cleaned/CHECK.md** (48 errors) disagrees with current checker (5 strict errors).
- **Not flagged:** no factory at zero bytes; no truncated JSONL; no parse failures; no exact-hash duplicates on cleaned; cascading hallucination is no longer a coverage hole.

## Recommended next densification focus (ranked)

1. **Treat raw as immutable evidence; promote a new cleaned label that includes r07+.** The highest-leverage unharvested supervision is already on disk (ttf 071–075, ffpc r07–r10, bridge r10–r12, coding r07–r09, swarm r10–r13) and most of those files are validator-clean. Do not rewrite raw `real` labels.
2. **Quarantine the four cleaned training blockers before any train job:** ffpc r04 line 3 (`sim_or_real='unknown'`) and the swarm weighted-sum drifts (r09 5e-5, `final-trajectories` 5e-4; checker also r05/r06). These are the only remaining shape errors after promotion remaps `real`.
3. **Require v2 identity on every *new* round:** top-level `id`, `state.sim_or_real ∈ {designed,hil,simulated}`, canonical provenance. Coding r10 and swarm r14 are the two factories still failing this on current output.
4. **Emit `Novel coverage: N%` on NOTES** so the 40% token-efficiency early-stop can see a plateau. Right now the latch is defined and unused.
5. **Write `NOTES-r10.md` for ffpc or explicitly mark r10 as diagnosis-only** so harvest/frontiers stop implying a complete round package.
6. **Reward-exchange convention before cross-factory DPO** (still the Aug 17 #2 item; entropy went  up). Prefer an explicit `units` / exchange-rate field over another head-name vocabulary.
7. **Content, only after 1–6:** ttf partnered/contested negative total; coding unreconcilable-residue recovery + mid-episode gate whiplash; run 073’s social-head triple on an SNN and report measured exit latencies; mark intentional gate-error records for rationale-supervision exclusion.
8. **Swarm throughput or reuse.** Keep the six-agent loop; either two scenarios/round or point it at a sibling’s weakest clean record. Count remains the harvest bottleneck.

## How this harvest differs from 2026-08-17T05:58:20Z

| | Aug 17 harvest | This snapshot |
|---|---:|---:|
| Records | 46 | 189 |
| Validator errors | 0 (old contract) | 112 (current contract) |
| Cleaned records | 0 | 138 (partial; not current raw) |
| Cascading hallucination | absent | present (ffpc-r3-001) |
| Chosen-side REJECT | 0/9 | 13/42 |
| Bridge late-round events | 15–20 (r02) | 66–104 (r10–r12) |
| Training-ready | no (too small) | no (IDs, provenance, 4 cleaned blockers) |
