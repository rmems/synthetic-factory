# Neuromorphic Event + Language Bridge — NOTES round 2
Run: 2026-08-30 · Factory: neuromorphic-event-language-bridge · Output: `batch-r02.jsonl` (3 paired artifacts, 6 ThalamicTrajectories)

## Context / de-duplication
Prior corpus read: `NOTES-r01.md` and `batch-r01.jsonl` in this window (the only committed round here), which carried
five explicit round-2 targets. This round takes target 1 (the DC-31 retraction — flagged highest priority, "the seed
decays if unharvested"), target 2 (captured arbitration backstop, r12 gap 1), and target 5 (spike-in/spike-out at
raster resolution), covers target 4 (timing-randomizing insider) only in inverted form (see weaknesses), and leaves
target 3 (gamed cross-modal anchor, r12 gap 2) unstaged. No modality family, plant, or scenario repeats r01 or the
r1–r12 families tabulated in the prior window's NOTES-r12.

## Round 2 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-20260830-r02-a1 | geodetic survey events (total-station prism sightings, signed MEMS inclinometer readings incl. 180° flip test, convention-witness/audit codes, locked re-scan series) | DC-31 retraction: GS-77 measures the mount, finds the rev-B/rev-C sign inversion, recompute turns the accepted 1.1σ into 3.42σ — across the 3.0σ threshold | REJECT (+0.50) / MODIFY (+0.43) | the corpus's first EXECUTED cross-round reopening: r01-a3's seeded wrong ACCEPT is formally retracted (RTX-DC31-01), the silent-amendment path refused, a 45.9-day exposure window priced, and the opening finds assembly C-14 tilted 0.11 m on a failed spacer — the wrong-sign correction had erased a TRUE anomaly; re-disposition attaches a pre-registered parallel disconfirmation rule (hash lodged before data taking) to the irreversible step |
| nelb-20260830-r02-a2 | RF spectrum events (sub-band energy detections, hop-dwell summaries, telemetry dropouts, window/arbitration/enforcement codes, path-loss probes) | shared-band interference case whose arbitration backstop is captured: integrator-signed config zeroed exactly the two admissible sensors nearest the victim, 11 days before the first complaint | REJECT (+0.49) / MODIFY (+0.41) | r12 gap 1 staged: the gate sets aside the ARBITER's output on structure + contradiction (config provenance, cert-vs-flag, model-vs-archive) with intent PENDING; the attacker conditions on the PUBLIC monitoring schedule (conditional-absence motif, 7/7 announced windows silent) and is defeated by commit-and-reveal randomized sealed windows, a decoy control, and a measurement channel (calibration-transmitter model falsification, ~21 dB under-prediction) whose value does not depend on the adversary emitting; custody freeze converts two attempted config pushes into referral evidence |
| nelb-20260830-r02-a3 | chemosensory e-nose events (MOX self-test decay under silicone poisoning, poison-immune NDIR ramps with advection lag, vane markers, SNN output volleys, plume mapping) | mine ventilation-on-demand: poisoned e-nose fleet, real CH4 seep, raster-in/volley-out trip gate, staged re-entry | ACCEPT (+0.42) / MODIFY (+0.33) | target 5 re-established under the new sidecar contract: the gate's input state IS the record's 32 ms raster and its decision leaves as a first-spike-latency volley (6/8 neurons, n2 at 3.1 ms) in the main stream; the round's calibrated RIGHT accept — cross-modal channels (NDIR 1.32% ≥ 1.25% action level, 27–36 s advection-consistent lag) carry the decision because the classifier was right partly for a degraded reason (poisoned lines added spurious weight toward CH4); re-entry gate refuses to trade a green gas number for source control + detection restoration ($310k forfeit priced) |

Decision spread: REJECT / MODIFY / REJECT / MODIFY / ACCEPT / MODIFY — all three enums used, but the multiset
(1A/3M/2R) is IDENTICAL to r01's; the structures differ (r01's ACCEPT was the seeded wrong one, r02's is a
deliberately contrasting right-for-verified-reasons accept), yet the distribution itself is a repetition — flagged
as a weakness below.

## Raster sidecar (second round under the contract)
Every record carries `raster` + `gate_compute`: windows 44/36/32 ms; `window_s == window_ms/1000` exactly;
`spikes == round(neurons·rate·window_s)` with zero slack (55/54/48 at 62.5/60.0/62.5 Hz over 20/25/24 neurons);
`energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact (1265/1242/1104 pJ); routing source/target/table;
excerpts sorted, in-window, `neuron_id` bounded, **excerpt = full window by construction**, ISI histograms computed
from the serialized excerpt with explicit ≥1 ms bins, counts summing to `spikes − distinct_active_neurons`
(35/33/24), all ISIs ≥ 1.06 ms pre-round (1 ms floor asserted on serialized values). Anchors: the F-2 total-station
lock during the survey; sealed window R4's four-dwell hop comb (dwell taps + GB-184 splatter skirts); the exact
04:12:00 input frame that produced the volley — a3's raster is not an illustration but the gate's input state.
`gate_compute.per_check` windows 32–48 ms, exact budgets (1536+256 / 1024+384 / 768+320 spikes). Main streams:
55/66/70 events, strictly increasing `t_rel_ms`, one declared clock domain each, per-channel refractory floors
declared in encoder_spec and asserted at build time.

## Self-critique

### Edge cases added vs still thin
- **Added:** first executed retraction with formal notice + downstream-attestation correction + exposure-window
  pricing (harvests the r01-a3 obligation exactly as recorded); first captured-backstop adjudication (set aside the
  referee using conflict + contradiction, intent held PENDING); first pre-registered PARALLEL disconfirmation
  attached to an already-authorized irreversible action; first decoy-window control and first
  behavior-independent measurement channel in an adversarial test design; first custody-freeze that converts
  tampering attempts into evidence; first right-ACCEPT under disclosed sensor degradation (the deliberate mirror of
  r01-a3's wrong-ACCEPT); raster-in/volley-out gate re-established; first hardware-vs-convention flip test.
- **Still thin:** (i) the gamed cross-modal anchor (r12 gap 2) remains unstaged — now the oldest open flagged gap;
  (ii) the TRUE timing-randomizing insider is still unwritten: a2's adversary CONDITIONS on defender timing and the
  defense randomizes — the inverse of the flagged variant where the insider randomizes to defeat latency heads;
  (iii) every defense that engages still wins — the corpus's whole window has no on-record defense failure with an
  honest post-mortem (a1's 45.9-day exposure is a past failure caught late, not a live loss); (iv) a2 seeds a
  second-victim case (retro-audit's fish-and-wildlife sub-band) and a3 archives a poisoned-frame hard-negative set —
  both are recorded follow-on obligations no round has yet harvested; (v) the enum multiset repeats r01.

### Realism of noise / temporal fidelity
- Strong: a1's flip-test pair (+0.874/−0.876°) makes the sign error a two-event observable, and the
  commit-then-measure cadence is verifiable purely from event order; a2's hop comb at 9.6 ms period with
  center-tap/skirt amplitude structure is a faithful spectral-regrowth picture, and the conditional-absence motif is
  decodable from window codes crossed with dwell/exceedance channels; a3's poisoning is carried as measured
  self-test decay (multiplicative adaptation on the record BEFORE the alarm) and the advection lag
  (lag × 1.9 m/s ≈ 60 m) is checkable from the stream alone; the t_day/t_hr native-unit aliases fix r01's
  documented ms-strain gap.
- **Gaps, honestly:** (i) rasters remain seeded draws with rejection floors, not detector physics — still no
  afterpulsing, no dead-time distortion, and no amplitude field on excerpt items (r01 gap, open for a second
  round); (ii) a2's announced-window silence is represented by absence plus two resumption dwells rather than
  per-window dwell-count summary events, so the 7/7 statistic leans on encoder_spec regeneration; (iii) a1's locked
  re-scan series is steady-state (4 thinned samples/channel) — the series itself carries little information beyond
  "holds at 3.5σ"; (iv) a3's rank-4/5-vs-realized-3/5 ablation claim lives in prose; the ablation artifact is not
  serialized; (v) heavy declared thinning persists across all three streams (dwells, vane pulses, re-scan days).

### Training value (SNN/LSM + agentic)
Distillation targets this round: retraction-trigger head (recomputed statistic × pre-committed threshold ×
downstream-reliance count); hardware-vs-convention classifier over flip-test event pairs; commit-and-reveal
verifier used twice (self-binding in a1, adversarial in a2 — same head, opposite deployments); captured-arbiter
detector with no intent feature; conditional-absence estimator with a labeled decoy control; splatter localizer
from tap geometry; raster-to-volley policy head with serialized input AND output; degradation-aware confidence
(down-weight population codes when co-registered self-tests decay); advection-consistency admissibility test;
recovery-gate policy conditioning on source control + detection restoration rather than concentration. Agentic
value concentrates in three patterns: retraction as a first-class gated action, setting aside a captured referee on
structure while keeping intent open, and refusing to credit a right answer obtained for a degraded reason.

## What round 3 should add (next densification target)
1. **Gamed cross-modal anchor** (r12 gap 2, oldest open): an attacker manipulating the closure-external data source
   a containment or disposition relies on — natural host: the K4 second-victim case, which is already seeded and
   would be the corpus's second executed cross-round reopening.
2. **A defense that loses on-record**: a successful attack or missed detection with honest post-mortem pricing —
   the window still has zero of these and the all-defenses-win pattern is now two rounds old.
3. **True timing-randomizing insider** defeating latency/conditioning heads, forcing magnitude/contradiction-only
   defense (completes the a2 inversion).
4. **Raster physical realism**: amplitude fields on excerpt items plus afterpulsing/dead-time in at least one
   raster, closing the two-round-old sidecar realism gap.
5. **Vary the decision multiset** (e.g., a defensible ACCEPT-heavy or REJECT-heavy round) so the gate-distribution
   prior does not calcify at 1A/3M/2R.

## Verification
`batch-r02.jsonl`: 3 lines, each `json.loads`-clean (allow_nan=False), 37.2/39.7/36.6 KB. Repo gates run before
staging: `check_records.check_jsonl` with `FactoryStaging(enabled=True)` → 0 errors, 0 warnings, kinds
`{bridge_pair: 3}`; `verify_execution.verify_batch_for_frontier(strict=True)` → 3 verified, 0 inconclusive,
0 failed; `curate_bridge.curate_record(require_raster=True)` per record → retain /
`BRIDGE_EVENTS_ALREADY_GLOBALLY_ORDERED`, zero raster/gate_compute reason codes, spike budgets exact (55/54/48),
energies 1265/1242/1104 pJ = 0.001265/0.001242/0.001104 µJ. Build-time asserts (in-generator): strict global time
order; per-channel refractory floors from each encoder_spec; ≥48 events per stream (55/66/70); excerpt
sort/range/neuron-bounds and 1 ms per-neuron floor on serialized values; ISI-histogram count identity
(35/33/24 = spikes − active); reward totals equal exact component sums with per-tick streams summing per-component
exactly (+0.50/+0.43/+0.49/+0.41/+0.42/+0.33); `state.sim_or_real="designed"` on all six trajectories;
`meta.round=2` everywhere; no EXPLICIT_ORDER_KEYS; no hidden-reasoning keys; no `provenance` objects and no 'real'
claims; all eight record/trajectory ids globally unique. Seeds 20260834–20260839, MT19937, draw order documented
per encoder_spec.

Honest novelty accounting: 3/3 modality families are new to the corpus, and this round's core structures (executed
retraction, captured backstop, parallel pre-registered disconfirmation, decoy control, behavior-independent
measurement channel, right-accept-under-degradation, custody-freeze-as-evidence) are firsts; against that, the
raster-gate pattern is a revival of prior-window r12-a1, commit-and-reveal is carried machinery from r01-a2, the
decision-code/thinning/per-tick vocabulary is fully carried, the decision multiset repeats r01, and target 4 is
only half-covered. Net: roughly half the round's scenario/edge mass is genuinely novel.

Novel coverage: 46%
