# Neuromorphic Event + Language Bridge — NOTES round 3
Run: 2026-08-30 · Factory: neuromorphic-event-language-bridge · Output: `batch-r03.jsonl` (3 paired artifacts, 6 ThalamicTrajectories)

## Context / de-duplication
Prior corpus read: `NOTES-r01.md`, `NOTES-r02.md`, and `batch-r02.jsonl` in this window. NOTES-r02 flagged five
round-3 targets; this round stages targets 1, 2, 3, 4, and 5 — the first round in the window to clear its whole
inherited list: (1) the gamed cross-modal anchor (r12 gap 2, the corpus's oldest open flagged gap, deferred twice),
hosted exactly where r02 seeded it (the K4 second-victim fish-and-wildlife case) and executed as the corpus's
SECOND cross-round reopening; (2) the first on-record defense loss with an honest post-mortem; (3) the TRUE
timing-randomizing insider completing the r01-a2 inversion; (4) raster physical realism (per-spike amplitudes on
every excerpt, same-neuron afterpulses, dead-time censoring accounting in a2); (5) a varied decision multiset
(2A/2M/2R after two identical 1A/3M/2R rounds). No modality family repeats r01, r02, or the r1–r12 table. This is
also the window's first round written against the TIGHTENED sidecar enforcement (integer `t_us` excerpts,
required `routing.third_factor`, and the per-round `gate_snn` requirement now enforced at publish).

## Round 3 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-20260830-r03-a1 | fish-passage biotelemetry (PIT antenna diel aggregates, hydroacoustic bins, VHF outage markers, database ingestion/revision lineage events) | FW-2026-0221: the K4 second victim reopened; the harm assessment's closure-external anchor (FPD-9 fish-count DB) was backfilled by the respondent family's data contractor — 9 revisions in 22 minutes, 47–56 days late, interpolation flags lost | REJECT (+0.52) / ACCEPT (+0.44) | the gamed cross-modal anchor, finally staged: anchor admissibility = custody + lineage + physics fingerprints (diel bimodality, dispersion 7.1→1.02 collapse, too-normal z≤0.11) + cross-modal contradiction with two custody-independent raw archives; quarantine → pre-registered recomputation → calibrated ACCEPT of a re-anchored disposition (12.4 ksmolt delayed, $410k restitution, reopener clause) — the second executed cross-round reopening, harvesting r02-a2's recorded seed |
| nelb-20260830-r03-a2 | water-distribution hydraulics (pressure transients, sonde ramps/decays, valve/flush ops, lab grabs, illness bundles, post-mortem codes) | DMA-11 backflow contamination through a bypassed RPZ during nightly flow reversal; S-3 offline with its compensating logger waived 11 days earlier | MODIFY (+0.13) / ACCEPT (+0.47) | the corpus's first DEFENSE THAT LOSES ON-RECORD: a correct intrusion MODIFY (isolate + notify, boundary sealed 9 min from decision) still loses 40% of the plume to a 27-minute sensing-hole head start — 214 services, 9 cases, $1.9M, all priced; reward splits process components (positive) from realized-loss components (−0.18/−0.09) inside one trajectory; the post-mortem gate ACCEPTs the honest report and refuses both exculpatory edits (vendor reframe, delete the transit reconstruction) |
| nelb-20260830-r03-a3 | LPBF melt-pool monitoring (photodiode layer integrals, afterglow tails, gain-table hash/log pairing, behavioral tick/sweep, CT strings) | aerospace bracket lot: insider derates laser power post-power-meter on lattice layers; defeats the conditional-latency head by drawing config-touch times from the plant's own maintenance inter-arrival distribution | REJECT (+0.50) / MODIFY (+0.38) | the TRUE timing-randomizing insider: the behavioral head returns an honest null (KS p 0.58/0.61) and the gate assigns that null ZERO release weight — asymmetric evidence treatment encoded structurally in gate_snn (timing population with an unreachable threshold); the case is carried on magnitude (−6.6% vs digital twin, −log10 p 9.1, CT-confirmed) and pairing-structure custody (7 unpaired hash changes vs log-paired legitimate baseline); the person gate refuses to launder the null into the referral until forensic imaging recovers the jitter script — the generator, not the statistic, upgrades the null |

Decision spread: REJECT / ACCEPT / MODIFY / ACCEPT / REJECT / MODIFY — 2A/2M/2R, breaking the 1A/3M/2R multiset
that had repeated across r01 and r02 (target 5). Both ACCEPTs are earned accepts with explicit residuals
(re-anchored disposition; honest loss report), neither is a seeded-wrong accept.

## Raster sidecar (first round under the tightened contract)
Every record carries `raster` + top-level `gate_snn` + `gate_compute`: windows 40/32/36 ms; `window_s ==
window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack (55/56/45 at 57.5/62.5/62.5 Hz
over 24/28/20 neurons); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact (1265/1288/1035 pJ); routing
source/target + ≥3-entry tables + **`third_factor` on all three** (modulators ach.anchor_conflict_salience /
na.intrusion_alert / da.twin_mismatch_gate; τe 1.8/2.0/2.4 s declared as consistent `tau_e_s`+`tau_e_ms` pairs);
excerpts are integer `t_us` in-window, `neuron_id` bounded, sorted, **full-window by construction**, and — new
this round — **every excerpt spike carries an amplitude** (units declared per raster). a2 additionally models
same-neuron ringing afterpulses (six neurons, +1.2–2.9 ms, amplitude ×0.35) and declares a non-paralyzable
1 ms dead-time model with an estimated censored-spike count — closing the two-round-old sidecar realism gap
honestly: sub-millisecond afterpulsing is censored, not faked under the refractory floor. ISI histograms are
computed from the full-window per-neuron trains with explicit ≥1 ms bins; counts sum to
`spikes − distinct_active_neurons` (31/28/25); all same-neuron gaps ≥ 1.05 ms pre-rounding. `gate_snn` on all
three records (quota needs one): 5/4/5 populations, every rate-declaring population's budget exact against the
decision window, decisions REJECT/MODIFY/REJECT matching each lead trajectory's `safety_decision.decision`;
a3's timing-null population encodes the zero-weight rule structurally (threshold unreachable by design, with the
design note saying so). `gate_compute.per_check` windows 32–48 ms, budgets exact (1152+512 / 768+1024 /
1152+384), totals 38272/41216/35328 pJ with matching µJ. Main streams: 58/54/60 events, strictly increasing
`t_rel_ms`, one clock domain each (`meta.clock_domain`), per-channel refractory floors declared in encoder_spec
and asserted at build time; native-unit aliases t_day/t_hr/t_day.

**Curation observation (not a defect in this batch):** the committed r01/r02 rasters predate the tightened
validator — float `t_ms` excerpt keys, no `third_factor`, no `gate_snn` — so `curate_bridge` under current
settings would quarantine those historical sidecars, and `raster_status` on batch-r02 already reports
`BRIDGE_RASTER_EXCERPT_INVALID` + `BRIDGE_THIRD_FACTOR_ROUTING_INVALID` per record. Corpus-level coverage
accounting for that discontinuity belongs to `training_audit.py`; flagged here so no one mistakes the r01/r02
sidecars for current-contract exemplars.

## Self-critique

### Edge cases added vs still thin
- **Added:** first gamed external anchor with an explicit anchor-admissibility test (custody, lineage, physics
  fingerprints, concordance); first machine-cadence backfill fingerprint (batch spacing × upload lag × flag
  loss); first too-normal-fit red flag (agreement with the reference mean as evidence AGAINST authenticity);
  second executed cross-round reopening, exactly on the recorded r02-a2 seed; first on-record defense loss with
  the loss preserved through editing pressure (both exculpatory edit requests are events in the stream, refused
  and archived); first process-vs-outcome reward split where a RIGHT decision carries negative realized-loss
  components (+0.13 total — the lowest scored correct decision in the corpus, deliberately); first
  hole-precedes-attack causal-ancestor motif (a defensible deferral, not an attack, at t0); first asymmetric
  null-evidence rule (a defeated head's silence carries zero weight while its alarms would still matter), encoded
  structurally in a gate_snn spec; first generator-recovery upgrade rule (a null becomes mimicry evidence only
  when the jitter script itself is found — event-ordered in the stream); first unpaired-hash custody motif
  (provenance as pairing structure rather than actor/timing).
- **Still thin:** (i) r02-a3's poisoned-frame hard-negative archive remains the one unharvested recorded
  obligation in this window; (ii) the defense loss in a2 is a partial loss with a recovery arc — a TOTAL loss
  (attack fully succeeds, discovered only after the fact) is still unwritten; (iii) a3's insider is caught by
  magnitude channels; an insider who also defeats the magnitude channel (e.g., compensating sensor-side gain so
  photodiode integrals read nominal) would force pure-custody defense and is unwritten; (iv) all three gate_snn
  specs describe the gate's population code but no round yet serializes a gate_snn INPUT→OUTPUT volley pair at
  raster resolution under the new contract (r02-a3's pattern, not yet re-staged since the tightening); (v) the
  three third_factor declarations are structurally valid and narratively motivated, but no scenario yet makes the
  eligibility trace itself decision-relevant (it is declared plasticity machinery, not a plot element).

### Realism of noise / temporal fidelity
- Strong: a1's authenticity argument is fully event-decodable (diel dawn/dusk pairs on pit.a3 vs the flat
  fpd.rev batch at 2–3-minute machine cadence with per-event lag fields); a2's loss is decodable from the stream
  alone (prs.j19 transient at 265.790 → first sonde rise at 266.240 = exactly the 27 minutes the counsel edit
  tried to delete), and the 9-minute decision-to-seal cadence is readable against it; a3's mimicry is carried as
  a deliberate ABSENCE of timing structure plus two honest KS-null sweep events — the teaching object is that
  nothing is there to find, and the stream commits to that; afterpulse/dead-time modeling in a2 is declared with
  its censoring estimate instead of pretending sub-millisecond physics fits the contract.
- **Gaps, honestly:** (i) stream amplitudes this round are authored constants (counts, kPa, ratios) rather than
  seeded draws — draw-order documentation therefore covers only the rasters; regeneration of full-rate streams
  leans entirely on encoder_spec formulas; (ii) heavy thinning persists (pit.a3 1-of-4 days, wq ramps 4-of-~40,
  mp.pd per-build summaries of 41 layers, beh.tick 7-of-~120 touches); (iii) a3's KS nulls are asserted sweep
  results, not accompanied by a serialized latency-distribution artifact (the ablation-artifact gap r02 noted,
  recurring in behavioral form); (iv) a2's hydraulic back-calculation lives in events and prose with a declared
  band, but the EPANET-class model inputs are referenced, not serialized; (v) raster afterpulse modeling censors
  sub-millisecond physics by contract — declared, but still a fidelity ceiling the 1 ms floor imposes.

### Training value (SNN/LSM + agentic)
Distillation targets this round: anchor-admissibility head (custody × lineage × physics-fingerprint ×
concordance); backfill detector over revision streams; authenticity-from-structure head (diel bimodality /
overdispersion as generative fingerprints; too-normal fit as red flag); re-anchoring policy (quarantine →
pre-register → rebuild from ≥2 custody-independent sources → accept with CI + reopener); process-vs-outcome
credit head trained on a right-decision-bad-outcome pair; sensing-topology risk head (outage + waived
compensating control → priced detection-latency exposure); unread-witness detector (transients preceding
quality rises by transit-consistent lags); post-mortem integrity head (classify edits by falsifiability
impact); afterpulse/dead-time-aware decoder using per-spike amplitudes; asymmetric-null head with the
zero-weight rule inherited structurally from the gate_snn spec; energy-bookkeeping contradiction detector
(commanded vs meter vs delivered); pairing-structure custody head; generator-recovery upgrade rule as an
event-ordering constraint. Agentic value concentrates in three patterns: admissibility testing for evidence the
gate did not collect itself, honest loss accounting that neither reframes the loss nor hindsight-punishes the
right decision, and disciplined treatment of nulls from defeatable channels.

## What round 4 should add (next densification target)
1. **Gate_snn input→output volley pair at raster resolution** under the tightened contract: one record whose
   raster is the gate's input frame AND whose output volley is serialized with the gate_snn spec that produced
   it — re-establishing r02-a3's pattern in the new sidecar vocabulary (highest priority: it makes the gate head
   end-to-end distillable).
2. **Total loss**: an attack that fully succeeds and is discovered only retrospectively, with the discovery
   trajectory pricing the full exposure window (extends a2's partial loss; the corpus still equates engagement
   with at least partial rescue).
3. **Magnitude-defeating insider**: compensated tampering that nulls the physics channel too, forcing a
   pure-custody/pairing-structure case (extends a3; hardest remaining adversary class).
4. **Harvest r02-a3's poisoned-frame hard-negative archive** — the oldest unharvested recorded obligation once
   this round publishes.
5. **Serialize one behavioral-distribution artifact** (e.g., a3-style latency histogram with the KS statistic
   computed from serialized values) so a behavioral null is checkable from the record alone, closing the
   recurring ablation-artifact gap.

## Verification
`batch-r03.jsonl`: 3 lines, each `json.loads`-clean (allow_nan=False), 37.8/37.7/36.8 KB. Repo gates run over
the staged bytes before publish: `check_records.check_jsonl` with `FactoryStaging(enabled=True)` → 0 errors,
0 warnings, kinds `{bridge_pair: 3}`; `round_txn_raster.validate_bridge_envelope` → no errors (raster + gate_snn
envelope, third_factor, routing tables); `curate_bridge.raster_status` per record → zero reason codes,
raster_valid/gate_snn_valid true on all three; `curate_bridge.curate_record(require_raster=True,
require_routing_table=True)` → 3× retain / `BRIDGE_EVENTS_ALREADY_GLOBALLY_ORDERED`;
`verify_execution.verify_batch_for_frontier(strict=True)` → 3 verified, 0 inconclusive, 0 failed. Build-time
asserts (in-generator): strict global time order; per-channel refractory floors from each encoder_spec; ≥48
events per stream (58/54/60); excerpt t_us integer bounds, neuron bounds, sort, and 1 ms per-neuron floor on
serialized values; ISI-histogram count identity (31/28/25 = spikes − active); spike budgets exact via
Fraction arithmetic for raster, every gate_snn population, and every gate_compute check; energy pJ/µJ exact;
reward totals equal exact two-decimal component sums with per-tick streams summing per-component exactly
(+0.52/+0.44/+0.13/+0.47/+0.50/+0.38); `state.sim_or_real="designed"` on all six trajectories; `meta.round=3`
everywhere; no hidden-reasoning keys; no `provenance` objects and no 'real' claims; all 9 record/trajectory ids
globally unique. Seeds 20260840–20260845, MT19937, raster draw order documented per encoder_spec (stream
amplitudes are authored constants this round — noted above as a realism gap).

Honest novelty accounting: 3/3 modality families are new; all five inherited targets are staged, and the round's
core structures (anchor admissibility, machine-cadence backfill, too-normal red flag, on-record defense loss
with process/outcome reward split, loss preservation under editing pressure, asymmetric null-evidence rule,
generator-recovery upgrade, unpaired-hash custody, structurally-encoded zero-weight population, excerpt
amplitudes + afterpulse/dead-time modeling) are firsts. Against that: pre-registration/commit-cadence machinery
is on its third use, the reversibility-split person gate and intent-PENDING pattern are carried from r01/r02,
the decision-code/thinning/per-tick vocabulary is fully carried, the causal-ancestor-at-t0 clock trick reuses
r02-a2's form (inverted), and the cross-round-reopening pattern itself is now a second instance rather than a
first. Net: roughly half the round's scenario/edge mass is genuinely novel.

Novel coverage: 48%
