# NOTES — Multi-Agent Ouroboros Swarm, run 2026-08-30, ROUND 3

Factory: multi-agent-ouroboros-swarm. One scenario (Q), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r03.jsonl (39,597 bytes). Full labeled
transcript: swarm-transcript-r03.md. Executable grounding: a session-scratchpad
simulation (sim_r03.py, seed 20260831) FITS every load-bearing number; the
assembler (build_r03.py) re-asserts both spike trains' order + refractory,
reward reconciliation (components, ticks, and the embedded contrast), the new
raster/gate_snn sidecar arithmetic, and runs the repo validators in-process
(check_records: 0 errors 0 warnings, kind thalamic; verify_execution:
verified) plus round_txn_raster.validate_bridge_envelope on the exact staged
file before staging.

ORCHESTRATION NOTE: dispatched AS round 3 of the 2026-08-30 window; the
factory directory held committed r01+r02 (reservation confirmed r03 next,
token fd9a9e7ff9604236972b38ba0ac1968b). Every write was create-only inside
the reserved staging directory; nothing under outputs/raw/ was touched.
Prior context read for gap targeting and de-collision: NOTES-r01, NOTES-r02,
and the committed batch-r02 record structure. CONTRACT CHANGE SINCE r02:
`round_txn_raster.py` now refuses this lane without a valid `raster` sidecar
per record and at least one `gate_snn` per round — r03 is the lane's first
round carrying both (r02 published before the enforcement landed).

## What this round produced

Scenario Q — "THERMION / Vireo District Loop 4": a district-heating operator's
1373 m corroded hot-water loop where two heterogeneous, individually-correct
agents share one acoustic medium. LYRA (leak localizer) must ACT to SENSE —
inject probe transients to localize an active 1.59 m3/h leak (bootstrap CI
[1.35, 1.83]); ATLAS (pressure guard) must SENSE to ACT — damp transients to
protect corroded welds from water-hammer fatigue. Neither can read the other's
intent (vendor schema mismatch). The coordination failure is a new DYNAMICAL
CLASS for this factory and the exact class NOTES-r02 gap 2 demanded: a
CROSS-POLICY INFERENCE-ACTUATION ARMS RACE — each agent's control action is
the other agent's measurement noise, and the loop closed through the plant has
fitted static gain 1.26 against a fitted operational escalation boundary of
0.38, so probe amplitude doubles every 160 s until weld-fatigue territory.

This completes a three-member family: r01 = too little asymmetry between
IDENTICAL policies (anti-phase livelock; cure = identity-derived symmetry
breaking), r02 = too much synchrony among IDENTICAL policies (metastable
congestion collapse; cure = desynchronization), r03 = HETEROGENEOUS policies
closing a loop through the plant (escalation spiral; cure = none of the
above — there is no symmetry to break and no synchrony to disperse). The cure
is the biological one, new to this factory: CROSS-AGENT EFFERENCE COPY /
reafference cancellation — announce your intended actuation 250 ms ahead so
the other loop can subtract you from its senses. Fitted: booked 11.5 dB
cancellation (MC median available 21.9 dB) drops residual coupling to 0.373 <
the 0.42 boundary; both agents then run CONCURRENTLY at 0.69 of the fatigue
limit with SNR 7.7 dB.

The gate decision is a primary REJECT (r01 ACCEPT, r02 MODIFY — the window now
covers all three cells, and the embedded contrast episodes cover the opposite
dispositions). TG-THERM REJECTs the naive playbook's AGENT-KILL (suspend the
"noisy" localizer) on a numeric three-part basis: (1) responsiveness rho =
0.93 >= 0.70 -> closed-loop interaction spiral, NOT component fault (the
suspend playbook's own runaway predicate requires the open-loop signature,
fitted at -0.15 in the contrast); (2) the leak is real and unlocated (CI
excludes zero and meter drift); (3) a fitted-sufficient de-escalation exists.
The executed alternative is the SEQUENCED chicken-and-egg recovery (NOTES-r02
gap 3 discharged with priced arithmetic): the TDM arbitration channel (9600-
baud PLC) is jammed BY the failure it must arbitrate (bypass-actuator EMI,
frame-error 0.38, P(commit)/attempt 0.092, E ~ 13 s of failing attempts), so
recovery must be one-way cap (60 kPa) -> ATLAS freeze-DON'T-fight (hold, not
zero: fitted worst p-p 156 kPa = 0.87 of limit; cap-without-freeze starves SNR
to -5.3 dB) -> handshake commits on the first post-ring-down attempt (P
0.903) -> TDM windows -> efference bridge.

### Fitted leaves (all from sim_r03.py, seed 20260831)
- Standing-wave fundamental c/2L = 0.437 Hz (geometry-derived).
- Spiral: static loop gain 1.0 x 0.9 x 1.4 = 1.26; fitted operational
  escalation boundary gamma* = 0.42 (g* = 0.38), analytic divergence boundary
  0.56; envelope doubling 160 s (2x at t=220 s, 4x at t=380 s); healthy-weld
  fatigue amplitude reached t=400 s; uncontained trajectory pins at 598 kPa
  p-p (3.3x limit).
- Ignition: +6 dB flashing-leak noise step at t=120 s (the leak both demands
  the probing and ignites the spiral).
- Efference copy: MC median 21.9 dB cancellation available at 8%+/-2% model
  error; booked 11.5 dB (conservative); residual gamma 0.373 -> residual gain
  0.34; concurrent steady state 47.6 kPa probe / 124 kPa p-p / SNR 7.7 dB.
- Freeze window: cap+freeze bounds worst p-p at 156 kPa (0.87 of limit) over
  the 220 s negotiation window; counterfactual cap-without-freeze SNR -5.3 dB.
- PLC handshake: 5-frame descriptor, P(commit)/attempt 0.092 under storm EMI
  (frame-error 0.38) vs 0.903 post-freeze (0.02); E[commit] ~13 s vs 1.3 s.
- Weld tail: MC P(corroded fatigue-critical weld inside an antinode belly) =
  0.95% per spiral event (200k trials) — the tail base rate is FITTED this
  round (r02 designed its incident rates; NOTES-r02 gap 1's spirit, see
  weaknesses for the honest residual).
- Harm posterior: 0.52 / 0.34 / 0.14 (spiral / end-of-life / both) from
  designed priors x likelihoods, FROZEN by destroyed evidence (steam-scoured
  fracture face) — NOTES-r02 gap 4 discharged: penalties and governance
  proceed under the indeterminacy, nothing conditions on resolving it.
- TDM localization: per-window fix N(0, 0.9 m) with 25% multipath-ghost lock
  (+/-4-9 m), median estimator -> 8 windows (160 s) to 95th-pct error <= 1.2 m
  (achieved 1.17 m); leak quoted 6.5 +/- 1.2 m and found in-interval.
- Steam-spur sub-variant: beta 2.0 / gamma 1.55 -> gain 3.10; 95 kPa
  condensation-hammer threshold crossed at 240 s vs 400 s -> TDM must be
  PRE-ARMED there (deployment policy, not incident response).
- Responsiveness discriminant: rho 0.93 (closed-loop spiral) vs -0.15
  (stuck-DAC open-loop), threshold 0.70.
- Fraud tail fence: 300 s log -> 3.3 mHz resolution; claimed 0.500 Hz vs
  plant 0.437 Hz = 19 bins (unambiguous) + freeze-window cross-check.
- Information reward DERIVED: class-entropy drop 1.539 -> 0.383 = 1.157 bits
  x 0.1624/bit rubric = 0.188 -> information_value 0.19.

### Injections (all four present and disjoint)
- Cycle-1 domain: **district-heating-acoustics** — the candidate NOTES-r13
  and NOTES-r01 both flagged and no round used; first stationary-plant,
  no-vehicle domain of this window (r01 warehouse-amr, r02 aerial-swarm).
- Cycle-1 tail (correlated latent-defect class): corroded-weld-at-antinode
  compound — vents BELOW the nominal fatigue limit at its corrosion-reduced
  ~165 kPa; fitted 0.95%/spiral-event base rate; steam-scoured fracture face
  freezes the cause posterior at 0.52/0.34/0.14 (globally unresolvable harm
  with the training signal intact).
- Cycle-2 domain sub-variant (physical-constraints clause): legacy steam spur
  — c 480 m/s, condensation hammer, gain 3.10, fitted 240 s crossing; converts
  the fix into environment-dependent standing configuration.
- Cycle-2 tail (human-intent deception class, disjoint trigger): fraudulent
  $84,000 compensation claim with a fabricated vibration log — rejected on the
  fitted 19-bin spectral fingerprint (the forgery matches the PUBLIC report's
  rounded 0.5 Hz, not the plant's 0.437 Hz) plus the freeze-window overlap;
  base rate ~0.8% of publicized incidents (designed constant, flagged).

### Structural density moves
- Embedded SAME-GATE contrast decision WITH ITS OWN SPIKE TRAIN (NOTES-r02
  gap 5 discharged): W+3, LYRA's DAC latch sticks — open-loop amplitude ramp
  with rho -0.15 and efference copy-execution mismatch 2.9x; the SAME gate
  ACCEPTs the suspension the primary REJECTed. The discriminant taught is
  responsiveness + efference integrity, never "don't suspend agents". The
  9-event contrast train carries the mismatch signature (copy 0.35 vs
  executed 1.00 -> 1.24) — the machinery that CURES the primary is the
  DETECTOR in the contrast. Contrast reward 0.54 reconciles independently.
- Governance subgame priced UNDER the frozen posterior: CR-T-0412 approves
  the efference-schema mandate SCOPED to the 2 safety-coupled pairs, standing
  TDM for the rest, steam spur pre-armed — extending the r01/r02
  predicate-don't-retire authority line to PRICING THE COUPLING CLASS, and
  proving decisions survive an unresolvable harm attribution.
- New-contract sidecars, first in this lane: raster (40 ms window, 128
  neurons, 6.4 Hz, 33 spikes = round(32.768), 759 pJ at 23 pJ/spike, 13-event
  excerpt, routing with a NEGATIVE-weight efference_predictor ->
  hydro_correlator edge (-0.61) — the learned reafference subtraction IS the
  routing entry) and gate_snn (25 ms window, reject/accept/modify pools
  27/7/8 spikes at fitted rates, decision REJECT matching the gate).

## Self-critique of this round's batch

### Strengths (edge cases, coherence)
- The headline class is fitted end-to-end: boundary (0.42/0.56), timescale
  (160 s doubling), threshold crossing (400 s), the cure's residual gain
  (0.34), and the recovery's chicken-and-egg arithmetic (0.092 vs 0.903) all
  come from one seeded model, and the REJECT rationale quotes them as
  numeric thresholds rather than vibes.
- The recovery is SEQUENCED and each stage is load-bearing: the cap is
  one-way (needs no negotiation), the freeze is what un-jams the negotiation
  channel (fitted), and the counterfactuals price both wrong orderings
  (negotiate-before-freeze spins at P 0.092; cap-without-freeze starves SNR
  to -5.3 dB). "Freeze-don't-fight" (hold, don't zero) is a genuinely
  reusable de-escalation primitive.
- The unresolvable harm is structurally honest: the observable that would
  resolve it is physically destroyed (steam-scoured face), the posterior is
  frozen, the incident penalty conditions on observable harm only, and the
  governance decision demonstrably proceeds under the indeterminacy — the
  exact form r13 gap 4 and r02 gap 4 asked for and no prior round delivered.
- The efference-copy machinery closes symmetrically: cure in the primary
  (subtract announced actions from your senses), detector in the contrast
  (copy-execution mismatch flags open-loop faults), and it lands in the
  raster sidecar as a negative-weight routing edge — the same concept at
  narrative, decision, and substrate levels.
- Both tails carry arithmetic fences; the fraud tail's fence (public-rounding
  vs plant-truth spectral fingerprint) is a new deception-detection pattern
  for the factory and is fitted, not asserted.

### Weaknesses (honest)
- The spiral fit is a swarm-authored generative model, as in r02: the
  per-dB gains (alpha/beta/gamma), guard constants (lam, ki), ignition step
  (+6 dB), antinode gain (2.6), and fatigue thresholds are designed inputs;
  what is FITTED is the closed-loop behavior they produce (boundary,
  doubling, crossings, residuals). The honest ceiling remains r02's: seeded
  model + derived consequences, not discovery by a process the swarm does
  not author.
- The fraud tail's base rate (0.8% of publicized incidents) and the harm
  posterior's priors/likelihoods (0.50/0.38/0.12 x 0.83/0.71/0.90) are
  designed constants — the posterior's FROZENNESS is mechanistic (destroyed
  evidence) but its numeric split is authored. A fitted claim-arrival model
  and a fitted vent-timing likelihood are the natural next fits.
- Tick 6's commit time (13.9 s) and the storm-jam expectation (~13 s) are
  numerically close by coincidence; the record flags this in
  component_notes, but a cleaner design would have separated them by
  construction.
- The contrast train is 9 events — legal and purposeful (the mismatch
  signature needs few spikes), but thinner than a full second episode's
  train; its race window is declared in its own state, not exercised by a
  flip narrative of its own.
- The efference-copy adapter's 250 ms lead requirement is asserted as a
  correlator constraint, not fitted; and the 2019 runaway backstory that
  justifies PB-ACOUSTIC-07 exists only as prose.
- No metastability/self-sustain structure this round (the spiral is a clean
  divergence, not a trap): r02's trigger-outlives-cause lesson has no r03
  analogue — deliberate, since the class differs, but it means the round
  teaches escalation, not hysteresis.

### Realism of noise / latencies
Ladder spans ~9 decades, each rung load-bearing: 485 us self-label race /
0.8 ms refractory floor (tightest exhibited 1.287 ms) / 0.912 ms acoustic
transit+DSP (1.1 m at 1200 m/s) / 1.4 ms Ethernet frame / 1.8 ms race window
/ 3.1 ms gate latency / 25 ms PLC frame / 40 ms probe pulse & raster window /
160 s amplitude doubling / 1.2 s handshake attempt / 13.9 s commit / 20 s
probe cycle / 8 s / 12 s TDM windows / 160 s localization / 240 s vs 400 s
threshold crossings / 41 min closure / +21 h weld replacement / +6 d schema
ship & fraud claim. Sensor noise is present and explained: 25% multipath-
ghost correlator locks, PLC frame corruption under EMI (0.31/0.28 amplitude
events), hydrophone background +6 dB flashing step, adaptation decay on
hydro_echo (0.97 -> 0.79 -> 0.58 -> 0.44) with the REGIME-CHANGE recovery
(0.88/0.86) explicitly encoded, vent-hiss decay on weld_ae, and the guard's
transients collapsing 0.94 -> 0.35 -> 0.22 as labeling then cancellation land.

### Value for SNN distillation
- CROSS-AGENT COROLLARY DISCHARGE (headline): the biological principle that
  an actor must tell its own sensors what it is about to do, lifted to the
  multi-agent level — each loop broadcasts efference copies so the other can
  cancel reafference. Encoded three ways: the 250 ms copy-lead spike pair
  (efference_guard @ 51750 -> bypass_act @ 52000 -> cancelled transient
  0.22), the negative-weight routing edge in the raster sidecar, and the
  copy-mismatch fault detector in the contrast train.
- ACT-TO-SENSE VS SENSE-TO-ACT COUPLING: active-sensing agents and
  protective-damping agents on one plant form a positive-feedback pair even
  when both are correct; the class signature is escalation with INTACT
  feedback on both sides (rho >= 0.70 both loops).
- RESPONSIVENESS AS THE CLASS DISCRIMINANT: closed-loop (amplitude tracks
  error) => interaction pathology, fix the COUPLING and keep the agents;
  open-loop (ramp ignores error, efference mismatch) => component fault,
  suspend. The paired REJECT/ACCEPT episodes make the boundary trainable.
- FREEZE-DON'T-FIGHT + SEQUENCED RECOVERY: when the arbitration channel is
  jammed by the pathology it must arbitrate, the de-escalation order is
  one-way constraint -> unilateral hold (NOT zeroing) -> negotiate -> learn;
  holding is what clears the channel; zeroing re-exposes the plant.
- ATTRIBUTION ORDER-CODES ARE FLIP-FRAGILE: the mine-vs-not-mine tag rode a
  485 us race inside the 500 us flip bound; the gate excludes it and rides
  the order-invariant responsiveness fit — extends the r01 (arbitration) and
  r02 (causation) flip-fragility doctrine to ATTRIBUTION.
- DECIDE UNDER FROZEN POSTERIORS: when the discriminating evidence is
  physically destroyed, the correct system prices decisions on the coupling
  class and observable harm, and provably does not stall on attribution.

## Reconciliation and validity receipts
- reward_components: 6-component unweighted signed sum 0.88 and 8-tick signed
  sum 0.88 both reconcile to total with |diff| < 1e-9 (script-asserted;
  validator tolerance 1e-6). Embedded contrast: 4-component sum 0.54
  reconciles independently.
- spike_events: primary 26 events / 9 channels, one key t_rel_ms, globally
  non-decreasing, min same-channel gap 1.287 ms >= 0.8 ms, 3 channels inside
  race_window_us 1800; contrast 9 events / 5 channels, independently ordered,
  min same-channel gap 18.83 ms; adaptation + regime-change amplitudes per
  the realism section.
- Sidecars: raster spikes 33 == round(128 x 6.4 x 0.04) exactly; energy 759
  pJ / 0.000759 uJ at 23 pJ/spike within 1e-6/1e-9; excerpt 13 events inside
  [0, 40000] us, neuron_id < 128; routing 3 valid entries + third factor tau
  0.6 s == 600 ms; gate_snn pools 27/7/8 == round(n x rate x 0.025) each,
  decision REJECT == safety_decision.decision;
  round_txn_raster.validate_bridge_envelope on the staged file: clean.
- Repo validators on the exact staged line: check_records.check_record
  (factory_staging=True) -> 0 errors, 0 warnings, kind "thalamic";
  verify_execution.verify_record_execution -> "verified". Top-level id
  "ouroboros-r03-20260830-thermion-vireo-loop4-inference-actuation-arms-race"
  unique vs the committed r01/r02.

## Novel coverage
The coordination-failure CLASS (heterogeneous-policy inference-actuation arms
race), the entire cure vocabulary (cross-agent efference copy / corollary
discharge / reafference cancellation, freeze-don't-fight, sequenced
chicken-and-egg de-escalation, responsiveness discriminant), the domain
(district-heating acoustics, first stationary no-vehicle plant), the
unresolvable-harm structure (frozen posterior with destroyed evidence), the
deception tail's public-rounding fingerprint, and the lane's first
raster/gate_snn sidecars are ALL absent from every prior committed round: a
grep over prior ouroboros batches returns zero hits for efference / corollary
/ reafference / arms-race / heterogeneous-policy / freeze-don't-fight /
responsiveness-discriminant / district-heating. Repeated elements are
honestly discounted: the same-gate contrast form and governance-pricing
scaffold are r02/r13 patterns re-instantiated; the flip-fragile race doctrine
is the third member of an r01/r02 series (extended to attribution, but the
move rhymes); the poisoned-playbook disposition (reproduce the artifact,
don't distrust alarms) rhymes with r01; TDM quiet windows rhyme distantly
with r02's desynchronization in that both manage interference, though the
mechanism and failure class differ. Weighing a wholly new failure family +
cure family + domain + two structural firsts (frozen-posterior harm; contrast
train) against those reused scaffolds:

Novel coverage: 70%

## What ROUND 4 should add (flagged gaps for the next round to fix)
1. FIT THE AUTHORED CONSTANTS THIS ROUND LEANED ON: the harm posterior's
   likelihood triple, the fraud-claim arrival rate, and the efference
   250 ms lead requirement are designed; fit a vent-timing likelihood model
   and a claim-arrival process from synthetic logs, and derive the lead
   bound from correlator physics.
2. N > 2 HETEROGENEOUS AGENTS: r03's arms race is pairwise. The unmet class
   is a 3+-agent heterogeneous pathology where pairwise-stable couplings
   compose into an unstable cycle (A stabilizes B, B stabilizes C, C
   destabilizes A) — a coordination failure with NO faulty pair, only a
   faulty cycle.
3. LEARNED-WEIGHT PROVENANCE: the raster's -0.61 subtractive edge is
   declared as learned via the third factor, but no round has shown the
   LEARNING TRAJECTORY (weight before/after, eligibility windows exercised).
   A record whose sidecar carries a before/after routing pair tied to the
   verdict credit would make the three-factor rule load-bearing.
4. HYSTERESIS IN A HETEROGENEOUS CLASS: r02 owned metastability for
   identical policies; no round shows a heterogeneous pathology that
   OUTLIVES its igniter (e.g., the guard's learned damping bias persisting
   after the leak is fixed — a plant-level scar). Trigger-outlives-cause
   with heterogeneous agents is open.
5. CONTRAST EPISODE WITH ITS OWN FLIP NARRATIVE: r03 gave the contrast a
   train but not a race story; give the next embedded episode a full
   microsecond race with its own flip bound.
6. Domain candidates (de-collided): spiking event-camera traffic
   infrastructure as a FIXED-SENSOR grid (still unused after three windows
   of candidacy); cold-chain pharmaceutical logistics acoustics; AVOID
   district-heating (now used), aerial-swarm (r02), warehouse-amr (r01),
   irrigation/bascule/rail/underwater/surgical (2026-08-17 window).
