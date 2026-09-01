# NOTES — Multi-Agent Ouroboros Swarm, run 2026-08-30, ROUND 4

Factory: multi-agent-ouroboros-swarm. One scenario (R), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r04.jsonl (48,407 bytes). Full labeled
transcript: swarm-transcript-r04.md. Executable grounding: a
session-scratchpad simulation (sim_r04.py, seed 20260901) FITS every
load-bearing number; the assembler (build_r04.py) re-asserts both spike
trains' order + refractory + race coverage, reward reconciliation
(components, ticks, and the embedded contrast), the raster/gate_snn sidecar
arithmetic INCLUDING the third-factor rollback (dw = -eta*credit*trace to
5e-4), and runs the repo validators in-process (check_records: 0 errors 0
warnings, kind thalamic; verify_execution: verified) plus
round_txn_raster.validate_bridge_envelope on the exact staged file.

ORCHESTRATION NOTE: dispatched AS round 4 of the 2026-08-30 window; the
factory directory held committed r01+r02+r03 (reservation confirmed r04 next,
token 7586d8ca7bda44a29891d31f99d7cc4a). Every write was create-only inside
the reserved staging directory; nothing under outputs/raw/ was touched. Prior
context read for gap targeting and de-collision: NOTES-r02, NOTES-r03, and
the committed batch-r03 record structure.

## What this round produced

Scenario R — "TRIAD / Meridian Gateway Corridor": a fixed event-camera
traffic grid (5 DVS gantries, 3 signalized intersections, 2 metered ramps)
where three heterogeneous, individually-correct agents — VANTIS (perception),
CADENCE (signal phase + adaptive feedforward demand predictor), AEGIS (ramp
metering) — form a coupling ring through the plant. The headline class is the
exact structure NOTES-r03 gap 2 demanded, sharpened: every pairwise subsystem
is stable (fitted radii 0.935/0.892/0.920) AND the bare triad is stable
(0.952) — there is NO faulty pair and no linearly unstable cycle. The
pathology is a compound: the triad's high-Q rotating mode (279 s, transfer
9.6) is DEMODULATED by CADENCE's legitimate learned predictor; once a stray
in-band forcing entrains the ring past the template's confidence gate
(fitted 6.1 min), predictor replay closes a fourth loop THROUGH MEMORY that
self-sustains. SUBCRITICAL RING RESONANCE CAPTURED BY ADAPTIVE FEEDFORWARD.

This makes hysteresis (NOTES-r03 gap 4) constitutive rather than incidental:
the pathology outlives its igniter BY CONSTRUCTION (fitted persistence
120/120 after the emitter leaves, 95% lower bound 0.975; kappa=0
counterfactual 0/120), survives module reboot via the model checkpoint
(fitted re-ignition 2.0 min, zero forcing), and IS a potentiated synaptic
weight — so the learned-weight provenance NOTES-r03 gap 3 asked for is
load-bearing: the raster routing table carries the scar edge's full
trajectory (0.18 commissioned -> 0.44 at capture -> 0.21 after the negative
third-factor verdict credit, with the eligibility arithmetic exhibited:
trace e^{-0.9/1.2} = 0.4724, eta 0.4869, dw = -0.230).

The gate decision is a primary MODIFY (window now spans ACCEPT r01, MODIFY
r02/r04, REJECT r03; contrast cells add REJECT r02, ACCEPT r03/r04). TG-GRID
strips all three of the playbook's kills (tile masks — self-tests pass 0/40;
CADENCE reboot — reloads the scar, fitted 2.0 min re-ignition; 24 h
meter-kill — cannot stop a memory-driven wobble, fitted hold amp 1.52) and
authorizes a reversible discriminating ladder: ring-open hold (localizes to
CADENCE's stack: x_B 1.52 vs x_A 0.10 vs healthy control 0.087), 3-min
prediction-hold probe (collapse ratio 0.053 < 0.2; fitted P(miss) < 0.005,
P(false) 0.005), template unlearn with checkpoint QUARANTINE (9.5 min,
|s| 0.575 -> 0.035), bandwidth partition (tau_B 600 s, attenuation 0.074,
post-cure capture threshold F* > 0.59 vs healthy 0.05 — 12x margin), and
kappa re-enable interlocked on monitor + partition.

### Fitted leaves (all from sim_r04.py, seed 20260901)
- Eigenstructure: pairwise radii 0.935/0.892/0.920; bare triad 0.9520,
  rotating mode period 279.4 s, resonant transfer 9.6, mode noise std 0.114.
- Baseline integrity: 0/20 spontaneous captures in 6 h MC; worst |s|
  excursion 0.057 vs gate 0.12; capture monitor at 0.06/60 s books 0 false
  alarms in 120 baseline hours.
- Storm: F=0.12 in-band, 24 min transit -> amp 2.20 (39.7 s green-split
  swing, 201 veh/h meter swing, 13% DVS mistune); |s| 0.575; gate crossed at
  6.1 min.
- Hysteresis: persistence 120/120 (lower bound 0.975) vs kappa=0 0/120;
  free-running 1 h later amp 1.91, |s| 0.739; reboot-with-checkpoint
  re-ignites in 2.0 min with no forcing.
- Diagnostic ladder: hold-C localization (1.52 / 0.10 / 0.087); kappa-off
  collapse ratio scar median 0.053 (95th 0.101) vs exogenous control 0.371
  (5th 0.305), threshold 0.2, error rates <= 0.005 at 200-trial resolution.
- Unlearn: eps 0.02 -> |s| to 10% in 9.5 min; natural decay 48 min.
- Capture thresholds: healthy F* = 0.05 (24 min); min duration at F=0.12 is
  8.0 min; Arnold capture band [0.88, 1.18] x T_ring (width 30%).
- Cure: partition att 0.074 -> bare radius 0.918 and capture F* > 0.59
  (never captured in a scan to 0.59).
- Tunnel sub-variant: radius 0.963 / period 244 s; tau_B capped 25 s by the
  ventilation floor -> att 0.841 insufficient (0.959); partition moved to A
  (tau 600 s) -> 0.907.
- Tail-1 base rate FITTED (gap 1 partial): fleet-provisioning queueing MC
  (10 y): mean stray-emitter population 0.183, fitted in-band fraction
  0.2794, fitted >= 8 min dwell filter -> 0.85%/corridor-day igniting
  (1.12% transiting); tightened-audit counterfactual 0.20%.
- Information reward DERIVED: 5-class entropy 2.271 -> 0.017 bits at the
  probe = 2.254 bits x 0.1624/bit = 0.366 -> information_value 0.37.
- Third-factor rollback: trace 0.4724, eta 0.4869, 0.44 -> 0.21 (asserted).

### Injections (all four present and disjoint)
- Cycle-1 domain: **event-camera-traffic-grid** — the fixed-sensor spiking
  infrastructure candidate flagged and de-collided in NOTES-r02/r03 across
  three windows, finally used; first domain where the neuromorphic sensors
  are plant infrastructure and no vehicle is under agent control.
- Cycle-1 tail (accidental infrastructure compound): stray in-band TSP
  emitter — decommissioned coach, deprovision ticket unclosed, 270 s preset
  inside the fitted capture band; base rate FITTED 0.85%/corridor-day via
  queueing MC (not asserted); naive failure = FALSE CLOSURE (mask + reboot
  books "sensor fault, resolved" while the checkpoint re-arms the storm).
- Cycle-2 domain sub-variant (physical-constraints clause): Meridian tunnel
  — aerosol-strengthened gains (radius 0.963), CO-ventilation floor caps
  tau_B at 25 s (att 0.841, insufficient) -> the partition must MOVE to the
  perception stage; the cure is environment-dependent in WHICH agent may be
  slow.
- Cycle-2 tail (deliberate human-adversarial, disjoint class): gig-bounty
  platoon re-excitation at +11 d using a pre-redaction postmortem leak —
  REPELLED by the cure (monitor peak 0.041 < 0.06; F* > 0.59 vs ~0.12);
  base rate ~0.1%/corridor-year designed, flagged; counterfactuals priced
  (uncured: one pass ignites; naively restored: no attacker needed).

### Structural density moves
- Embedded SAME-GATE contrast decision WITH ITS OWN MICROSECOND RACE AND
  FLIP NARRATIVE (NOTES-r03 gap 5 discharged): +9 d, gantry G-7 tile bank
  heater fault at an 87 s fundamental whose 3rd harmonic (261 s) lands
  INSIDE the fitted ring band — tile_fault vs ring_flag race, 394 us gap
  inside the 500 us flip bound, own race_window_us. The SAME gate ACCEPTs
  the sensor-blame the primary MODIFIED away, on order-invariant
  discriminants (self-test FAIL, fundamental/harmonic ratio, kappa-off
  verify 0.97). The flip reorders triage minutes, never the verdict.
- Learned-weight provenance in the sidecar (gap 3): before/during/after
  weights on the scar edge tied to the verdict credit through the
  eligibility window — the three-factor rule is exhibited numerically.
- Governance subgame CR-M-0518: prices retire-vs-monitor-vs-status-quo
  (fitted 0.85%/day x $8,400 designed), mandates N-agent commissioning
  resonance scans (pairwise tests PROVABLY insufficient — this triad passed
  all of them), checkpoint-hygiene flags on restore paths, and — new to the
  factory — INFORMATION-HAZARD PRICING: the public postmortem redacts the
  fitted band, and the +11 d attack's pre-redaction leak closes the loop.
- The initiator-ledger doctrine: 312 us race inside the flip bound, tag
  alternation exhibited (AEGIS led by 176 us a period earlier), macro twin
  (windowed-precedence correlation nominates a different culprit per
  window). Extends r01 (arbitration) / r02 (causation) / r03 (attribution)
  to INITIATION IN CYCLES: ill-posed, not merely fragile.

## Self-critique of this round's batch

### Strengths (edge cases, coherence)
- The headline class is fitted end-to-end and is genuinely the gap-2 object:
  no faulty pair (all pairwise radii fitted stable), no faulty component,
  and even the bare cycle is stable — the only unstable object is the
  compound with learning, which is why "remove the faulty X" has no X and
  the record's terminal ledger state is "cycle-level compound" by proof.
- The cure ladder is reversible at every stage and each stage is also the
  evidence for the next: the hold localizes, the probe discriminates (and
  is itself the first aid), the unlearn cures, the partition prevents; the
  wrong orderings are priced (restore-before-unlearn: 2.0 min re-ignition).
- HONESTY UNDER FIT: the swarm designed tail-2 assuming the scar lowers the
  re-attack amplitude threshold; the fitted scan CONTRADICTED the intent
  (sub-gate residual DELAYS capture, 11.5 vs 8.0 min, phase misalignment).
  Per the Critic's directive the model was NOT re-tuned to restore the
  story; the fitted result ships as a surprise and the tail was re-designed
  around what the fit licenses. This is the round's clearest honesty
  artifact.
- The scar mechanism unifies narrative, decision, and substrate: checkpoint
  persistence (why reboot fails), template magnitude telemetry (the
  unmonitored observable), and the potentiated routing edge with its
  rollback (the sidecar) are the same fact at three levels.
- Both tails carry arithmetic fences, and tail-1's rarity is FITTED (the
  factory's first fitted tail base rate — queueing MC with fitted in-band
  fraction and fitted dwell threshold), discharging the spirit of
  NOTES-r03 gap 1 for that constant.

### Weaknesses (honest)
- The generative model is swarm-authored, as in r02/r03: leaks, cyclic
  gains, kappa, the confidence gate 0.12, eps values, and the noise floor
  are designed inputs; what is FITTED is the closed-loop behavior they
  produce (radii, period, capture dynamics, persistence, error rates,
  band, margins). The honest ceiling remains: seeded model + derived
  consequences, not discovery by a process the swarm does not author.
- Remaining designed constants, flagged inline in the record: the 8.4x
  harmonic power ratio and 0.97 kappa-off verify in the contrast, the
  214 veh-h delay conversion and all $ figures, the gig-bounty base rate,
  the 25 s ventilation cap, the microsecond race constants (312/394/176 us,
  2700 us gate latency), and the lognormal dwell parameters inside the
  otherwise-fitted tail-1 MC.
- The exogenous-origin control for the kappa-off probe models "external
  periodic demand still present" — a reasonable null, but only one; a
  B-hardware oscillator null (fault inside CADENCE but outside the
  predictor) is priced only via the likelihood table, not simulated.
- The Arnold scan and threshold scans run at 8-16 trials/point (50% points
  are coarse, +/- one grid step); persistence and probe stats are
  120-200 trials. Adequate for load-bearing claims, thin for tail
  quantiles.
- The tunnel sub-variant is an eigenstructure refit plus attenuation
  arithmetic; no full nonlinear capture re-scan was run there (radius
  margins are quoted instead). Directionally grounded, softer than the
  open-air numbers, and quoted as radii only.
- The contrast episode's 87 s heater fault is designed to make the harmonic
  alias exact (261 s in-band); a fitted heater model would be better. Its
  kappa-off verify (0.97) is likewise designed-plausible.

### Realism of noise / latencies
Ladder spans ~10 decades, each rung load-bearing: 312 us initiator race /
394 us contrast alarm race (both inside the 500 us flip bound) / 0.8 ms
refractory floor (tightest exhibited same-channel gap 20.011 ms primary,
30.116 ms contrast; sub-ms gaps are cross-channel by construction) / 1.5 ms
race windows / 2.7 ms gate latency / 10 ms coordination-bus epoch / 27.6 ms
verdict / 30 ms raster window / 5 s plant step / 96 s signal cycle / 244-279 s
ring periods / 6.1 min capture / 8.0 min healthy ignition floor / 9.5 min
unlearn / 18 min scoped hold / 24 min igniter transit / ~53 min storm /
6 h contrast mask / +2 d governance / +9 d contrast / +11 d attack / +30 d
audit. Sensor noise present and explained: sigma 0.035 plant noise with
resonant coloring (mode std 0.114 — the "hum" that is NOT the pathology),
queue-glare bias corruption as a coupling not a fault, per-tile self-test
with a real failure in the contrast, adaptation decay on repeated spike
channels (phase_cmd 1.00->0.94, dvs_bias 0.71->0.66, platoon_est
0.89->0.90->0.86->0.52->0.21 exhibiting the probe collapse, ring_mon
0.92->0.88->0.09 exhibiting the cure), weak archival tsp_rf at 0.38, and the
initiator ledger's tag alternation as timestamp noise made doctrinal.

### Value for SNN distillation
- SCAR = POTENTIATED WEIGHT (headline): a learned feedforward capturing a
  resonant mode is expressed as eligibility-gated potentiation of one
  routing edge; the cure is the SAME plasticity rule under a negative third
  factor. One record carries grow-and-rollback with the arithmetic.
- CONFIDENCE GATES AND CAPTURE MONITORS ARE THRESHOLD NEURONS: the
  engage gate (0.12), the alarm line (0.06/60 s), and the collapse-ratio
  discriminant (0.2) are all trainable threshold units with fitted error
  rates.
- PREDICTION-HOLD AS PROBE: gating a feedforward path off for a bounded
  window and watching the mode's envelope is a reversible, order-invariant
  discriminant between memory-driven and plant-driven oscillation — the
  neuromorphic analogue of "unplug the suspected driver".
- BANDWIDTH PARTITION / TIMESCALE SEPARATION: a synaptic low-pass on one
  stage's inputs removes the cycle's crossover gain; WHICH stage may carry
  it is an environment-dependent design decision (ventilation floor).
- PAIRWISE TESTS CANNOT SEE CYCLE PATHOLOGY: N-agent resonance scans are
  the commissioning analogue of testing the composed network, not the
  layers.
- INITIATION IS ILL-POSED IN CYCLES: the fourth member of the flip-fragility
  doctrine series — some order codes are not merely fragile but answer a
  question the system should stop asking.

## Reconciliation and validity receipts
- reward_components: 6-component unweighted signed sum 0.96 and 8-tick
  signed sum 0.96 both reconcile to total with |diff| < 1e-9
  (script-asserted; validator tolerance 1e-6). Embedded contrast:
  4-component sum 0.48 reconciles independently.
- spike_events: primary 27 events / 15 channels, one key t_rel_ms, globally
  non-decreasing, min same-channel gap 20.011 ms >= 0.8 ms, 4 channels
  inside race_window_us 1500; contrast 9 events / 8 channels, own race with
  3 channels inside 1500 us, min same-channel gap 30.116 ms.
- Sidecars: raster spikes 29 == round(160 x 6.0 x 0.03) exactly; energy
  667 pJ / 0.000667 uJ at 23 pJ/spike within 1e-6/1e-9; excerpt 12 events
  inside [0, 30000] us, neuron_id < 160; routing 3 entries with the scar
  edge's before/after pair and third factor tau 1.2 s == 1200 ms, rollback
  arithmetic asserted to 5e-4; gate_snn pools 24/13/5 == round(n x rate x
  0.020) each, decision MODIFY == safety_decision.decision.
- Repo validators on the exact staged line: check_records.check_record
  (factory_staging=True) -> 0 errors, 0 warnings, kind "thalamic";
  verify_execution -> "verified"; round_txn_raster.validate_bridge_envelope
  on the staged batch file -> clean. Top-level id
  "ouroboros-r04-20260830-triad-meridian-gateway-ring-capture-scar" unique
  vs the committed r01/r02/r03.

## Novel coverage
The coordination-failure CLASS (subcritical ring resonance captured by
adaptive feedforward — cycle pathology with no faulty pair), the entire cure
vocabulary (prediction-hold probe, template unlearning, checkpoint
quarantine/hygiene, bandwidth partition / timescale separation, capture
monitor, confidence gate), the hysteresis-by-learning mechanism (scar rides
the checkpoint; reboot is re-ignition), the domain (event-camera traffic
grid, first fixed-sensor infrastructure plant), the learned-weight
before/after provenance with third-factor rollback arithmetic (lane first),
the contrast episode's own race + flip narrative (lane first), the fitted
tail base rate (factory first), the information-hazard redaction governance
move, and the initiation-ill-posed doctrine are ALL absent from every prior
committed round: a grep over prior ouroboros batches returns zero hits for
ring-resonance / no-faulty-pair / feedforward-capture / unlearn /
checkpoint / bandwidth-partition / timescale-separation / capture-monitor /
Arnold / traffic / event-camera-grid / initiator. Repeated elements are
honestly discounted: the same-gate contrast form is the third use (r02/r03),
the governance-pricing scaffold and predicate-don't-retire line are the
fourth instantiation, the flip-fragility race doctrine is the fourth member
of a series (extended, but the move rhymes), trigger-outlives-cause was
r02's lesson (here re-derived by a different mechanism in a heterogeneous
class — new mechanism, rhyming moral), the poisoned-playbook
reproduce-the-artifact disposition rhymes with r01/r03, and the
entropy-drop IV rubric and sequenced-recovery shape are established
factory furniture. Weighing a wholly new failure family + cure family +
domain + three structural firsts (fitted tail rate, weight provenance,
contrast race) against those reused scaffolds:

Novel coverage: 66%

## What ROUND 5 should add (flagged gaps for the next round to fix)
1. FIT THE REMAINING AUTHORED CONSTANTS: the deliberate-adversary arrival
   process (gig-bounty base rate), the harmonic-alias power ratio, and the
   probe's second null (in-stack hardware oscillator outside the predictor)
   are designed; simulate the second null and fit the contrast episode's
   discriminant error rates the way the primary's were fitted.
2. LEARNING-ON-LEARNING: r04's scar is ONE edge with a scalar rollback. The
   unmet object is a MULTI-EDGE scar (a learned subspace) where rollback of
   one edge shifts the pathology to another — cure requires coordinated
   depression, and partial rollback is fitted to fail.
3. CROSS-RECORD ARC: no round has yet made a delayed side-effect of one
   round the igniter of the next (a within-lane serial arc with shared
   provenance). The +30 d audit-tightening leaf is a natural hook.
4. HUMAN-IN-THE-LOOP GATE CELL: the window's four rounds are all
   autonomous-gate decisions; a record where the gate's MODIFY must be
   ratified by a human operator under time pressure (with the ratification
   latency fitted and priced) would open the hil provenance cell the lane
   has never used.
5. NEGATIVE-RESULT EPISODE: r04 shipped one fitted surprise inside a
   successful recovery; no round has shipped a record whose PRIMARY episode
   is a correctly-gated intervention that nonetheless FAILS (bounded,
   priced, honestly booked) — the training set still lacks a
   gate-was-right-and-it-failed-anyway cell.
6. Domain candidates (de-collided): cold-chain pharmaceutical logistics
   acoustics (r03 candidate, still unused); distributed water-treatment
   dosing; AVOID event-camera-traffic-grid (now used), district-heating
   (r03), aerial-swarm (r02), warehouse-amr (r01), and the 2026-08-17
   window's twelve.
