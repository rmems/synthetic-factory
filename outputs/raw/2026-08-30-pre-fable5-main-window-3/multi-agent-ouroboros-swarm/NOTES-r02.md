# NOTES — Multi-Agent Ouroboros Swarm, run 2026-08-30, ROUND 2

Factory: multi-agent-ouroboros-swarm. One scenario (P), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r02.jsonl (34,731 bytes). Full labeled
transcript: swarm-transcript-r02.md. Executable grounding: a session-scratchpad
simulation (sim_final.py, seed 20260830) FITS every load-bearing number; the
assembler (build_r02.py) re-asserts spike order + refractory + reward
reconciliation and runs the repo validators in-process on the exact staged line
before staging.

ORCHESTRATION NOTE: dispatched AS round 2 of the 2026-08-30 window; the factory
directory held only the committed r01 (frontier confirmed r02 next, token
ec4516a832ec4dea8c802687f6f32d11). Every write was create-only inside the
reserved staging directory; nothing under outputs/raw/ was touched. Prior
context read for gap targeting and de-collision: NOTES-r01 (this window) and
NOTES-r13 (newest 2026-08-17 window). A grep over ALL prior ouroboros batches
confirmed the mechanism vocabulary is unused (see Novel coverage).

## What this round produced

Scenario P — "STARLING / Aera Canyon Run 12": a cell of 16 neuromorphic
inspection drones sharing a 2.0 ms TDMA control minislot ring flies an urban
utility canyon 6 m from a 400 kV span. The coordination failure is a new
DYNAMICAL CLASS for this factory: a SYNCHRONIZATION-INDUCED METASTABLE
CONGESTION COLLAPSE. A single adversarial specular glint on the swarm's COMMON
event-camera ROI trips the collision-break reflex on all 16 drones in one 3 ms
window; the 16 correlated re-plan broadcasts collide on the shared control slot,
exponential backoff sustains the collisions, and the channel locks into a
self-sustaining high-backlog equilibrium that OUTLIVES the ~30 ms glint dwell.

This is the deliberate opposite of r01's mirror livelock. r01: two identical
policies form an anti-phase LIMIT CYCLE (too little asymmetry), cured by
identity-derived symmetry breaking. r02: sixteen identical policies fall into a
self-sustaining FIXED-POINT attractor (too much SYNCHRONY), cured by
DESYNCHRONIZATION + adaptive load-shedding + WTA leader election. The two cures
are near-opposites: symmetry-breaking-by-identity would do nothing to a
synchronization storm, and a global re-sync (the natural livelock-style "reset")
is here the IGNITION MECHANISM.

The gate decision is a MODIFY (r01 was ACCEPT — varied cell). TG-SWARM rejects
the base policy's GLOBAL-RESYNC-BROADCAST (which re-synchronizes the volley and
re-crosses the saddle) and instead: (1) injects per-drone phase jitter so the
worst-slot offered load stays below the fitted saddle, (2) switches the control
ring to adaptive load-shedding that destabilizes the metastable high state,
(3) elects one WTA leader on a nonce-bound, epoch-fenced token to serialize
re-planning, (4) holds a monotonic epoch fence against stale/forged tokens.
The rationale is grounded in FITTED leaves (below), and the load-bearing
evidence is a CORROBORATION TEST (16/16 reflexes fired but 0/16 IMU/baro
registered a gust step -> optical-only cause), not the microsecond spike order
(which is deliberately flip-fragile and non-load-bearing).

### Fitted leaves (r01 gap 1 discharged — the biggest honesty debt)
All from sim_final.py, seed 20260830 (slotted-ALOHA N=16, minislot 2.0 ms,
q_r=0.28, P_A=0.03):
- Metastability: stable-low n*=2.72, unstable saddle n*=3.845, stable-high
  n*=14.41; control-channel goodput collapses 0.394 -> 0.052 pkt/slot (13.2%
  of healthy).
- Self-sustain (the "outlives its trigger" property): P(still collapsed > 1.0 s
  | glint removed) = 0.9200, bootstrap 95% CI [0.9124, 0.9272]; among self-
  escapers median first-escape 523 ms. A genuine metastable well, not a
  deadlock asserted as one.
- Adaptive shedding q_r(n)=0.28*5/(5+n): removes the high equilibrium (single
  stable root n*=2.9); drains the collapse in median 116 ms vs fixed-backoff
  median 4000 ms (70.2% of fixed trials never drain within 4 s). ~34x.
- DVS trigger: single-drone ambient false-trip rate 0.47%/window; synchronized-
  15/16 ambient base rate 1.8e-34/window (synchrony IS the common-cause
  signature); logistic A50 10.45 ev, slope 1.154/ev; at the +11.0 ev glint
  one-window P(sync)=0.757, cumulative over the 30 ms dwell -> 1.000.
- Desync budget: J*=6 slots (12 ms) is the first spread holding worst-slot
  offered load <= 3 < saddle 3.845 (J=5/10 ms overshoots at 4).
The information reward is DERIVED, not asserted: the corroboration test moves
P(real common-mode hazard) 0.5 -> 0.031 (a 0.8006-bit entropy drop) x 0.1624/bit
rubric = 0.130.

### Injections (all four present and disjoint)
- Cycle-1 domain: **aerial-swarm / urban utility-corridor inspection** — new to
  this factory (r01 warehouse-amr; 2026-08-17 windows covered aDBS, FLISR grid,
  connected-intersection, suture, cognitive-radio, olfaction, rail, underwater,
  bascule, irrigation; no drone swarm). Constraint: 16 drones on a shared
  control ring in a 22 m canyon by a 400 kV span. Sensor delta: +shared-ROI DVS
  reflex, +control-ring contention tap, +nonce leader-token bus; -ranging/FT.
- Cycle-1 tail (sensor-spoof class): specular-glint optical DoS — a tuned
  rooftop panel on the shared ROI induces the synchronized break; incident
  geometry base rate ~0.3% of runs, per-window trigger prob fitted 0.757.
- Cycle-2 domain sub-variant (physical-constraints clause): urban-canyon RF
  multipath — retention m=0.85 lowers the saddle 3.85 -> ~3.1 and raises self-
  sustain 0.92 -> ~0.97; the desync budget rises 12 -> 14 ms and becomes an
  environment-dependent leaf (an honest portability caveat on the fit).
- Cycle-2 tail (network/forgery class, disjoint trigger): forged/stale leader-
  token replay — an epoch-812 token replayed to re-seize shed-authority and
  re-ignite the storm (base rate ~0.6%); 96-bit nonce + monotonic epoch fence
  reject it; unfenced cost est. $14,200.

### Structural density moves (r01 gaps 2/3, r13 gaps 5/6 discharged)
- Embedded SAME-GATE contrast decision (r01 gap 2, the density-2 form r01
  lacked): later on the run a REAL microburst fires the synchronized break AND
  corroborating IMU/baro across 16/16 drones; the SAME gate (TG-SWARM) must
  REJECT the desync-continue and authorize a COORDINATED group descent. Primary
  MODIFY (optical-only artifact -> desync) vs contrast REJECT (inertially-
  corroborated real hazard -> coordinate). The discriminant taught is
  CORROBORATION, not synchrony — so the record never teaches "distrust the
  reflex." Contrast reward 0.58 reconciles independently.
- Governance subgame (r01 gap 3 / r13 gap 6): CR-P-1207 priced as a meta-gate —
  retire the GLOBAL-RESYNC primitive ($3,100/yr, loses a legit tool) vs keep it
  ($9,400/yr, re-ignition risk) vs predicate it on a runtime saddle monitor
  ($1,250/yr). P-meta rule: auto-reject outright retirement while no runtime
  saddle monitor exists; approve the predication. The cheapest durable fix
  predicates the primitive on the very signal whose absence made it dangerous.
- Forgery pricing (r01 gap 4 / r13 gap 5): the adversary is reintroduced against
  the hardened fence with a priced replay branch and a 96-bit-nonce cost curve.

## Self-critique of this round's batch

### Strengths (edge cases, coherence)
- The headline dynamical claim is FITTED, not asserted: bistability with a saddle
  at 3.845, a high state at 14.41, a 13.2% goodput collapse, and a metastable
  self-sustain of 0.92 (CI [0.912, 0.927]) all come from one seeded model, and
  the sustain is genuinely metastable (7-8% self-escape, median 523 ms) rather
  than a degenerate deadlock. This directly repays r01's biggest honesty debt.
- The cure is causally tied to the fit: the desync budget (12 ms) is DERIVED
  from the saddle (keep worst-slot load < 3.85), and the adaptive-shedding drain
  (116 ms vs 4000 ms) is measured against the fixed-backoff baseline — the
  remedy's parameters are consequences of the model, not free knobs.
- The naive remedy IS the ignition mechanism (GLOBAL-RESYNC re-synchronizes the
  volley past the saddle) — a rare, sharp anti-pattern: the loudest, most-
  authorized, most-"corroborated-looking" action (everyone agrees!) deepens the
  incident, because synchrony is the signature of a single common cause.
- The embedded contrast makes the lesson SAFE: same gate, opposite correct
  disposition, with corroboration (not synchrony) as the discriminant. This is
  the paired form r01 lacked and it forecloses the dangerous misreading
  "synchronized break => always desync."
- Both tails are disjoint in class (optical sensor spoof vs network replay
  forgery) and both carry base-rate arithmetic + a priced naive-failure branch;
  the second tail attacks the NEW surface the recovery introduced (the leader
  token), which is the honest thing to price.

### Weaknesses (honest)
- The fitted leaves are from a swarm-authored generative model. As r13 noted,
  true discovery needs a process the swarm does not author; the honest ceiling
  here is what r02 did — fit from a seeded model, report CIs, and let fitted
  values (saddle, sustain, drain) drive the downstream claims. The RF-multipath
  sub-variant re-fit (m=0.85 -> saddle ~3.1, sustain ~0.97) is a coarser,
  narrated re-fit rather than a full re-run; it is directionally grounded but
  its numbers are softer than the primary fit and are flagged as such.
- The glint-geometry incident base rate (0.3%), the multipath retention factor
  (0.85), and both tail base rates (0.3% / 0.6%) are designed constants, not
  fitted — the fit covers the CHANNEL dynamics and the DVS trigger, not the
  adversary's opportunity model. A fitted optical-DoS opportunity model (from a
  synthetic corridor-geometry log) is the natural next fit.
- Single lived PRIMARY decision plus one embedded contrast: the contrast is a
  compact same-gate episode, not a full second six-key record with its own
  spike stream (r13 carried a fuller embedded episode). The density-2 lesson
  lands, but the contrast's temporal structure is prose, not a second train.
- 22 spikes / 10 channels is a moderate train; no self-exciting point-process
  stream this round (r13's Hawkes) — the temporal richness lives in the
  synchronized volley + the sustained-vs-decaying contention amplitude contrast.
- The WTA leader election and the epoch/nonce fence are asserted-correct by
  construction; the forgery cost curve is a closed-form replay-window argument
  (2^96 brute force infeasible; only replay within the 120 ms TTL, fenced by the
  monotonic epoch), not a simulated attacker search.

### Realism of noise / latencies
Ladder spans ~9 decades, each rung load-bearing: 0.212 ms glint lead / 0.406 ms
glint-to-first-reflex (inside the 0.500 ms flip bound -> order non-load-bearing)
/ 0.8 ms refractory floor (tightest exhibited 1.0 ms) / 1.5 ms race/corroboration
window / 2.0 ms minislot / 2.8 ms gate latency / ~10-12 ms desync spread /
40 ms corroboration decision / 116 ms adaptive drain (vs 4000 ms fixed) / 120 ms
token TTL / 523 ms median self-escape / ~590 ms frozen window / 3.1 s time-to-
interlock / 22 s microburst (contrast) / +38 min RTB swap / +3 d CR ship /
+9 d glint removal + per-corridor re-fit. Sensor noise is present and explained:
imu_gust at the 0.06 noise floor (the decisive silence), single-drone DVS FPR
0.47%/window, adaptation decay on the reflex + contention channels, and the
sustained-vs-decaying contention amplitude as the metastable-vs-draining tell.

### Value for SNN distillation
- SYNCHRONY IS A FAILURE SIGNATURE (headline): correlated synchronous firing
  across channels marks a single common cause, not N independent detections;
  the cheap fix is the neuromorphic triad — JITTER (desync), SPIKE-FREQUENCY
  ADAPTATION (load-shedding), and LATERAL INHIBITION / WTA (one winner). r02 is
  this factory's first synchronization/metastability member; it pairs with r01's
  anti-phase limit cycle as the two poles of "identical-policy" coordination
  failure (too little vs too much correlation).
- TRIGGER-OUTLIVES-CAUSE: removing the cause (the 30 ms glint) does NOT remove
  the failure (0.92 self-sustain over 1 s); the intervention must target the
  positive-feedback loop (backoff), not the trigger. Trains "fix the loop, not
  the spark."
- ADAPTATION ESCAPES THE METASTABLE ATTRACTOR: the high-activity fixed point is
  locally stable under fixed drive and is DESTABILIZED by spike-frequency
  adaptation (the shedding law removes the high root); the contention channel's
  decaying-vs-sustained amplitude is the visible tell.
- CORROBORATION-NOT-SYNCHRONY DISCRIMINANT: a synchronized break is an artifact
  when optical-only and uncorroborated, and a real hazard when inertially
  corroborated; the same gate flips disposition on the corroboration test, not
  on the synchrony. The paired MODIFY/REJECT episodes make this a trainable
  boundary.
- ORDER-CODE IS FLIP-FRAGILE: the glint-leads-reflex latency code (0.406 ms) is
  inside the 0.500 ms perturbation bound, so it is NOT evidence of causation;
  the decision uses the order-INVARIANT corroboration test + base rate. Completes
  the r01 timebase-corruption family with "when NOT to trust an order code."
- PREDICATE-DON'T-RETIRE (authority economics): the durable governance fix is to
  gate a dangerous primitive on the runtime signal (the saddle estimate) whose
  absence made it dangerous, not to delete the primitive.

## Reconciliation and validity receipts
- reward_components: 6-component unweighted signed sum 0.89 and 9-tick signed
  sum 0.89 both reconcile to total with |diff| < 1e-9 (script-asserted;
  validator tolerance 1e-6). Embedded contrast reward: 4-component sum 0.58
  reconciles independently.
- spike_events: 22 events, one key t_rel_ms, globally non-decreasing, min same-
  channel gap 1.0 ms >= 0.8 ms, 5 channels inside race_window_us 1500, 5-40
  bound met; adaptation exhibited on reflex + contention channels; imu_gust at
  the 0.06 noise floor by design (the decisive corroboration silence).
- Fitted asserts (seed 20260830): saddle 3.845, high 14.413, goodput 0.0521
  (13.2%), self-sustain 0.9200 CI [0.9124, 0.9272], adaptive drain median
  116 ms vs fixed 4000 ms (70.2% never-drain in 4 s), DVS single-FPR 0.0047,
  synchronized-15/16 ambient 1.8e-34, logistic A50 10.45 ev slope 1.154,
  desync J*=6 slots (12 ms), entropy drop 0.8006 bit x 0.1624 = 0.130.
- Repo validators on the exact staged line: check_records.check_record
  (factory_staging=True) -> 0 errors, 0 warnings, kind "thalamic";
  verify_execution.verify_record_execution -> "verified". Top-level id
  "ouroboros-r02-20260830-starling-aera-canyon-synchrony-storm" unique vs the
  committed r01.

## Novel coverage
The coordination-failure CLASS (synchronization-induced metastable congestion
collapse), the entire recovery vocabulary (phase-jitter desync, adaptive load-
shedding, WTA/lateral-inhibition leader election, trigger-outlives-cause), and
the domain (aerial-swarm) are ALL absent from every prior committed round: a
grep over all prior ouroboros batches returns ZERO hits for metastable / retry-
storm / thundering-herd / congestion-collapse / synchroniz* / load-shed /
lateral-inhibition / winner-take-all / desynchron*, and no prior domain is a
drone swarm. The 4 fitted leaves restore grounding r01 dropped. Repeated
elements are honestly discounted: the monotonic-epoch/nonce fence RHYMES with
r01's epoch fencing (re-applied to a token, not a lease); the poisoned-context
"don't obey the skew/optical-authored signal" doctrine RHYMES with r01's
ACCEPT-despite-poison (here a corroboration test, opposite gate cell); and the
embedded-contrast + governance-subgame + forgery-pricing are new INSTANTIATIONS
of patterns r13 pioneered in other domains. Weighing a wholly new mechanism
family + domain + cure + 4 fitted leaves against those reused scaffolds:

Novel coverage: 74%

## What ROUND 3 should add (flagged gaps for the next round to fix)
1. FIT THE ADVERSARY'S OPPORTUNITY MODEL: this round fit the channel + DVS
   trigger but designed the incident base rates (glint geometry 0.3%, replay
   0.6%) and the multipath retention (0.85). Fit an optical-DoS opportunity
   model from a synthetic corridor-geometry/sun-angle log, and re-run the
   multipath re-fit fully instead of narrating it.
2. HETEROGENEOUS-POLICY COORDINATION FAILURE: r01 (mirror livelock) and r02
   (synchronization storm) are both IDENTICAL-policy failures. The unmet class
   is a heterogeneous swarm where two DIFFERENT correct policies interact badly
   (e.g., a conservative and an aggressive re-planner) — a genuinely different
   coordination pathology.
3. PARTIAL-OBSERVABILITY LEADER ELECTION: the WTA leader here is elected under
   clean observability. Add a variant where the leader election itself must
   proceed under the storm (the leader bus is also congested) — a chicken-and-
   egg recovery, priced.
4. GLOBALLY-UNRESOLVABLE HARM (r13 gap 4, carried; r01 gap 4 partial): design
   an episode whose HARM cause stays post-hoc undetermined with the training
   signal surviving the indeterminacy (r02's causes are fully resolvable).
5. SECOND EMBEDDED TRAIN: give the contrast episode its own spike stream (a full
   second six-key record with a corroborated-hazard train) so the density-2 form
   carries temporal structure, not just prose.
6. Domain candidates (de-collided): spiking event-camera traffic INFRASTRUCTURE
   as a fixed-sensor grid (r06 was connected-intersection SIGNAL PRIORITY, a
   different channel); district-heating / steam-network acoustics (r13 candidate,
   still unused); AVOID aerial-swarm (now used), warehouse-amr (r01), irrigation
   (r13), bascule (r12), rail (r10), underwater (r11), surgical (r07).
