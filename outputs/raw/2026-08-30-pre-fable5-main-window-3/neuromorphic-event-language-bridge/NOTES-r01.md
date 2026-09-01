# Neuromorphic Event + Language Bridge — NOTES round 1
Run: 2026-08-30 · Factory: neuromorphic-event-language-bridge · Output: `batch-r01.jsonl` (3 paired artifacts, 6 ThalamicTrajectories)

## Context / de-duplication
This is round 1 of a fresh window: `outputs/raw/2026-08-30/neuromorphic-event-language-bridge/` held no committed
rounds at reservation time, so the two newest NOTES read were the newest committed anywhere for this factory —
`2026-08-17-pre-window-fable-final/NOTES-r12.md` and `NOTES-r11.md` — and `batch-r12.jsonl` was skimmed for shape and
scenario dedup. Prior corpus (12 committed rounds in that window): modality families r1–r12 as tabulated in NOTES-r12
(DVS, cochlea, SPAD ToF, DAS, PMU, e-skin, vestibular, atomic clocks, tokamak, QEC, neutrino networks, fab OES,
space weather, pulsar TOA, eddy covariance, flow cytometry, and their siblings), plus a six-class wrong-ACCEPT
taxonomy and six flagged round-13 targets. **This round deliberately takes three of those six flagged targets and
leaves the governance-recursion trio for round 2**, and it is the corpus's first round written against the raster
sidecar contract now in `prompts/03` §D (no committed round carries `raster`/`gate_compute` at all).

## Round 1 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-20260830-r01-a1 | rail axle-counter interlocking (dual-sensor pulse trains, EMI burst, decision-code events) | movement authority over a section whose occupancy is undecidable (88-in/87-out; masked sr2 pulse INSIDE the burst envelope) | MODIFY (+0.58) / REJECT (+0.66) | genuine-ambiguity revival (r12 gap 6, last staged r10-a2): posterior 0.62/0.38 stays OPEN at episode end; supervision is the reversibility split (on-sight sweep vs full MA vs 3–4 h walk-out), admissible-vs-informative evidence (vital counter vs EoT radio + acoustic count), and the refusal of an evidence-destroying pre-sweep reset under schedule pressure; the miscount is an ABSENT spike inside a flagged window — a detection target no prior pair encodes |
| nelb-20260830-r01-a2 | bioprocess lot disposition (EWMA z-steps, DO limit-cycle phase extrema, marker-ion comb, adversary action events) | 2000 L CHO batch contaminated; insider PE-3 watches the public EWMA alarm fire, then retunes below every visible threshold (span bias −6%, timed dilutions, port switch) | REJECT (+0.71) / MODIFY (+0.49) | the ADAPTIVE adversary r11/r12 flagged but never staged (r12 gap 4): defense wins only on channels the adversary could not observe or write — a DO-phase tripwire whose SECRET threshold was pre-committed as SHA-256 27 days pre-inoculation (commit-and-reveal verified on-record) plus QA-owned mass-spec; the behavioral signature is conditional action latency (median 66 min after each defense observable), an event-timing statistic; person-gate MODIFY separates the irreversible culture decision from the reversible personnel decision, innocent composite priced 0.09, intent PENDING |
| nelb-20260830-r01-a3 | muon tomography of a sealed dry cask (sector-deficit series, tilt/bracket events, LED-comb raster) | 21-day continuity-of-knowledge campaign; sector deficit deepens; day-9 forklift bump invites a geometry attribution | ACCEPT (+0.21) / MODIFY (+0.61) | the corpus's first deliberately seeded cross-round retraction target (r12 gap 5): the day-21 ACCEPT rests on a tilt correction computed under axis convention rev B while the day-2.1 bracket-swap event IN THE SAME STREAM records rev C (sign inverted) — under the installed convention the correction deepens the deficit instead of erasing it; every fact needed to recompute (rev-B parameters, bracket note, segment hashes, uncorrected series) is archived with the decision; the ops-gate MODIFY (segmentation + overlap calibration before any correction is chosen) is what keeps the wrong conclusion recomputable |

Decision spread: MODIFY / REJECT / REJECT / MODIFY / ACCEPT / MODIFY — all three enums used; the round's one ACCEPT
is the seeded-wrong disposition, scored honestly at its information set (+0.21 with a −0.06 humility term), a
seventh wrong-ACCEPT flavor distinct from the six classes in the r12 taxonomy: verified-against-the-wrong-AUTHORITY
(datasheet on file vs hardware installed), neither negligent nor captured nor scope-limited.

## Raster sidecar (new contract, first use)
Every record carries `raster` + `gate_compute`: windows 40/32/48 ms; `window_s == window_ms/1000` exactly;
`spikes == round(neurons·rate·window_s)` with zero slack (58/61/50); `energy_pJ = spikes·23` and
`energy_uJ = spikes·23e-6` exact; routing source/target/table; excerpts sorted, in-window, `neuron_id` bounded, and
**excerpt = full window by construction**, so the required ISI histogram is derivable from the record alone — bin
counts sum to `spikes − distinct_active_neurons` (43/38/32), all ISIs ≥ 1.0 ms (refractory floor asserted on the
serialized values). Rasters are anchored to named main-stream moments (the flagged group-8 crossing; the 90.5 h
mass-spec scan; the day-9.30 LED calibration frame), so the fast window and the slow narrative cross-reference.
`gate_compute.per_check` windows were kept inside 20–50 ms per §D even though only the budget arithmetic is
machine-enforced. Main streams: 66/57/52 events, strictly increasing `t_rel_ms`, one clock domain declared in meta,
per-channel refractory floors declared in each `encoder_spec` and asserted at build time; curate_bridge over the
staged batch: 3× retain / `BRIDGE_EVENTS_ALREADY_GLOBALLY_ORDERED`, raster + gate_compute validators clean.

## Self-critique

### Edge cases added vs still thin
- **Added:** first unresolved-at-end central question since r10-a2 (with a booked evidence deadline — the 72 h log
  rollover — honestly at risk); first absent-spike anomaly (the miscount IS a missing event, not an outlier); first
  adaptive adversary and first commit-and-reveal secret threshold; first conditional-latency behavioral statistic;
  first seeded cross-round retraction with a recomputable archive; first person-gate/product-gate irreversibility
  split inside one pair.
- **Still thin:** (i) the governance-recursion trio r12 flagged (captured arbitration backstop, gamed cross-modal
  anchor, three-party collusion including the infra owner) is deliberately deferred, not covered; (ii) a2's insider
  adapts thresholds but not TIMING — an adversary who randomizes action latencies would blunt the
  conditional-latency head this round teaches; that counter-adversary is unwritten; (iii) a3's retraction only pays
  off if a later round actually stages the GS-77 survey/re-scan reopening `nelb-20260830-r01-a3` — a cross-round
  obligation recorded here and in the record's own `distillation_note`; (iv) no gate this round consumes a raster as
  its input state (r12's spike-in/spike-out pattern is not re-staged in the new window); (v) all three defenses that
  engage, win — a1's ambiguity aside, the round has no successful attack.

### Realism of noise / temporal fidelity
- Strong: speed is decodable from ISI alone in a1 (pair spacing 0.14 m/v, group spacing 19.2 m/v, deceleration
  ramp), and the EMI envelope enclosing the masked pulse gives the absence a physical context; a2's suppression
  step (−2.1 z in one inter-event interval) is a discontinuity biology cannot produce — the step-vs-drift contrast
  is the teaching object; a3's between-channel divergence (monitored sectors vs reference band) is the slow motif,
  with the LED-comb-vs-Poisson raster giving structured and stochastic ISIs in one window.
- **Gaps, honestly:** (i) heavy declared thinning (1-of-8 axles, 1-of-40 DO extrema, 3-day sector integration) —
  full-rate regeneration leans on encoder_spec formulas rather than emitted events; (ii) raster stochastic
  components are seeded draws with a rejection floor, not simulated detector physics (no afterpulsing,
  no amplitude field on excerpt items); (iii) a2's hour-scale timestamps make the ms unit strained (values reach
  3.5e8 ms) — legal and finite, but a per-record native-unit alias would read better; (iv) a1's wheel-flat 18.2 g
  outlier is narrative color that no trajectory consumes; (v) sector series in a3 carry no per-sample error bars
  (the sigmas live in prose, not on events).

### Training value (SNN/LSM + agentic)
Distillation targets this round: absent-spike detector against a co-registered noise reference; ISI speed decoder;
step-vs-drift discriminator tied to config events; conditional-latency behavioral head (identity+timing only);
commit-and-reveal verifier; convention-lineage checker (join correction provenance against hardware-change events);
between-channel divergence detector; custody planner (seal primaries before choosing corrections). Agentic value
concentrates in the three decision patterns: reversibility splits under undecidable posteriors, secrecy-vs-
robustness for alarm thresholds with a cryptographic mechanism, and archives engineered so even wrong conclusions
stay recomputable.

## What round 2 should add (next densification target)
1. **Stage the DC-31 retraction**: GS-77 geometry survey or the 90-day re-scan discovers the rev-B/rev-C sign error,
   retracts the r01-a3 ACCEPT, prices the retraction and the 90-day exposure window — the corpus's first executed
   cross-round reopening (this is the highest-priority item; the seed decays if unharvested).
2. **Captured backstop** (r12 gap 1): an appeal/arbitration layer that is itself compromised.
3. **Gamed cross-modal anchor** (r12 gap 2): an attacker manipulating the closure-external data source a
   containment relies on.
4. **Timing-randomizing insider**: defeat this round's conditional-latency head; force defense onto magnitude/
   contradiction evidence alone.
5. **Spike-in, spike-out at raster resolution**: a gate whose input state is a raster sidecar and whose decision is
   emitted as one, re-establishing the r12-a1 pattern under the new contract.

## Verification
`batch-r01.jsonl`: 3 lines, each `json.loads`-clean (allow_nan=False), 30.0/29.6/28.7 KB. Repo gates run before
staging: `check_records.check_jsonl` with `FactoryStaging(enabled=True)` → 0 errors, 0 warnings, kinds
`{bridge_pair: 3}`; `verify_execution.verify_batch_for_frontier(strict=True)` → 3 verified, 0 inconclusive,
0 failed; `curate_bridge --emit summary` → 3 retain, all `BRIDGE_EVENTS_ALREADY_GLOBALLY_ORDERED`;
`curate_bridge._validate_raster` + `_validate_gate_compute` → zero reason codes per record, spike budgets exact
(58/61/50), energies 1334/1403/1150 pJ = 0.001334/0.001403/0.00115 µJ. Build-time asserts (in-generator): strict
global time order; per-channel refractory floors from each encoder_spec; ≥48 events per stream; excerpt sort/range/
neuron-bounds and 1 ms per-neuron floor on serialized values; ISI-histogram count identity; reward totals equal to
exact component sums (and per-tick streams, where present, sum per-component exactly: +0.58/+0.66/+0.71/+0.49/
+0.21/+0.61); `state.sim_or_real="designed"` on all six trajectories; `meta.round=1` everywhere; no
EXPLICIT_ORDER_KEYS anywhere; no `provenance` objects and no 'real' claims. Seeds 20260830–20260833, MT19937, draw
order documented per encoder_spec.

Honest novelty accounting: 3/3 modality families are new to the corpus, and 3 of 6 staged edge classes are firsts
(adaptive adversary, seeded retraction, commit-and-reveal); the remaining machinery (decision-code event channels,
measured response, priced innocent-composite branches, per-tick reward streams, thinned excerpt conventions) is
carried vocabulary from r9–r12 of the prior window, and the ambiguity pattern is a revival rather than a first.

Novel coverage: 55%
