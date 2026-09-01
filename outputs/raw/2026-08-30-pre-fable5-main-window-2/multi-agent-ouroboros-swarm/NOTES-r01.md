# NOTES — Multi-Agent Ouroboros Swarm, run 2026-08-30, ROUND 1

Factory: multi-agent-ouroboros-swarm. One scenario (O), strict loop:
Generator v1 → cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder → v2) → cycle 2 (all six → v3
final). v3 is the single line of batch-r01.jsonl (25,196 bytes). Full labeled
transcript: swarm-transcript-r01.md. Executable grounding: a session-scratchpad
assertion script (build_r01.py) re-derived every load-bearing number and ran
the repo validators in-process on the exact staged line before staging.

ORCHESTRATION NOTE: dispatched AS round 1 of a fresh run date (2026-08-30);
the factory directory was empty, reservation confirmed r01 as the frontier
(token 3b540a4d817c44579f036b3a93289d0e). Every write was create-only inside
the reserved staging directory; nothing under outputs/raw/ was touched by this
session. Prior-context inputs: NOTES-r12/NOTES-r13 and batch-r13 of the
2026-08-17 windows (newest committed rounds of this factory) were read for gap
targeting and tag de-collision.

## What this round produced

Scenario O — "OKTAVE / Brenner Cold Dock 3": a warehouse-amr cold-chain
airlock corridor where a 38.0 s network partition splits the corridor lease
between two identical-firmware robots. The coordination failure is new to the
batch in KIND, not just domain: a HOMOGENEOUS-POLICY MIRROR LIVELOCK — two
CORRECT, deterministic courtesy policies yield and re-claim on the same beat,
forming an anti-phase limit cycle (period 40.5 ms, offset 20.2 ms, 4 cycles),
visible directly as alternating decaying motor-current spikes. Every fault is
benign infrastructure: AP power-save firmware, cold-soak oscillator drift
(3.1 ppm × 774 s = 2.4 ms skew), a defrost sag, a store-and-forward buffer.
There is NO adversary anywhere in the record — a first for this factory.

The gate decision discharges NOTES-r13 gap 1 (density on the ACCEPT cell,
"ACCEPT despite a poisoned context" — the inverse of r13's celebrated
override): the fleet manager demands E-STOP-ALL on a collision alarm (closing
1.35 m/s, TTC 5.5 s) that is itself an artifact of the same 2.4 ms skew that
split the lease — reproduced numerically in-record (β-gain 0.018 ×
1.5127 m alternating one-way cross-clock bias / 0.0202 s anti-phase beat =
1.348 m/s, within 0.15% of the displayed value), backed by a standing
e-stop-first memo whose own predicate (a VALIDATED convergence track) is shown
unmet on two independent clocks. TG-DOCK-3 ACCEPTs the guarded
symmetry-breaking grant on skew-immune evidence only (DVS zero-burst on a
local pixel clock; two-way TDoA 7.40 ± 0.03 m ≥ 4.1 m envelope), with five
numeric predicates in the rationale. Right process, right outcome — and the
poison is disarmed by REPRODUCING the artifact, not by distrusting alarms.

Recovery machinery new to the batch: identity-derived symmetry breaking
(CRC8-seeded per-robot backoff — the tie-break key must be drift-invariant,
never the corrupted clock), monotonic epoch fencing (rejects two duplicate
lease-releases replayed by the healing partition), and pausing the stalled
party's lease clock so the livelock cannot re-arm around a silent robot.

Injections (all four present and disjoint):
- Cycle-1 domain: warehouse-amr cold-storage dock (unused in all 13 prior
  rounds; r04's ammonia plant was machine-room acoustics, not an AMR fleet).
  Constraint: 240 s/h door-open budget with 137 s spent; −26 °C physics
  (sound speed 315.1 m/s re-scales the ultrasonic numbers).
- Cycle-1 tail (power class): pad-sag stall — defrost-driven 0.82 pu sag
  through the charge pad resets AMR-7's drive controller mid-dispute
  (base rate ≈ 0.22% of conflicts); the reset ISR masks its own fault
  snapshot, so the stall cause is carried as an explicit UNRESOLVED posterior
  {0.61, 0.28, 0.11} — a structural (partial) discharge of r13 gap 4.
- Cycle-2 domain sub-variant (physical-constraints clause): thermocline fog
  band — DVS event rate −78% (flow floor 0.02 → 0.05 m/s, exhibited by a
  0.24-amplitude curtain flutter where clear air gives ~1.1), horn
  condensation +1.9 cm one-way TDoA bias.
- Cycle-2 tail (network/Byzantine class, disjoint trigger): duplicate-release
  replay flood — the heal-flush re-delivers 42 messages incl. 2 stale
  corridor releases (epochs 4088/4092 < 4117), causally correlated with the
  dispute through the same partition (base rate ≈ 0.7%); unfenced cost
  est. $9,800 + 3 h closure (387 J at 1.1 m/s closing, 640 kg).

## Self-critique of this round's batch

### Strengths (edge cases, coherence)
- One root fault (the partition) propagates down three independent paths —
  split lease, drift-poisoned estimator, buffered replays — so the compound
  tails are causally correlated, not a coincidence stack; both tails carry
  base-rate arithmetic and priced naive-failure branches.
- The poisoned context is disarmed by numeric reproduction (1.348 vs 1.35,
  0.15%), which teaches "explain the artifact" rather than "ignore alarms" —
  and the record prices the opposite error too (E-STOP-ALL: ≥ 557 s door-open
  vs 233 s realized, $2,900 vs $310 expected loss).
- The winner-flip narrative is load-bearing, not decorative: the naive
  first-timestamp branch is a drift-noise coin flip whose loser branch (grant
  to the robot that then stalls holding a live lease) is priced at +9.1 min.
- The self-masking-forensics surprise (the ISR that caused the stall erased
  its own fault register) gives the unresolved-cause posterior a MECHANISM
  rather than an excuse, and no reward component conditions on resolving it.
- Strict additivity held: cycle-2 output 25,196 B > cycle-1 17,872 B with
  every cycle-1 injection retained; receipts in the transcript.

### Weaknesses (honest)
- NO FITTED LEAVES this round: the β gain (0.018), fog attenuation (78%),
  CRC8 seeds, cause posterior {0.61/0.28/0.11}, and both tail base-rate
  factor sets are designed constants. r12/r13 had reached fitted-ROC /
  EM-discovery grounding; this round regresses on that axis and says so. The
  phantom-velocity "reproduction" is a first-order steady-state response
  approximation, declared as such — not a simulated filter trace.
- Single lived decision: no embedded second six-key episode (r12/r13 carried
  two-decision density). The ACCEPT-cell density move lands, but without an
  in-record contrast episode its lesson is weaker than r13's paired form.
- The direction-of-closure of the phantom velocity (why the artifact reads as
  approach rather than oscillation) is narrated via ping-direction sign
  correlation, not derived — the weakest link in the alarm-reproduction chain.
- Adversary-free by design: r13 carried gaps 3/5/6 (defender repertoire
  pricing, forgery-branch pricing, prosecution/governance subgame) remain
  untouched; this round deliberately spent its novelty budget elsewhere.
- 26 spikes / 7 channels is a modest train; no self-exciting point-process
  stream (r13's Hawkes) — the temporal richness lives in the anti-phase
  rhythm and refractory-legal doublets instead.

### Realism of noise / latencies
Ladder spans ~9 decades, each rung load-bearing: 412 µs claim separation /
0.8 ms refractory floor (tightest legal doublet 0.957 ms exhibited) / 1.86 ms
race window / 2.4 ms measured skew / 3.12 ms gate latency / 20.2 ms
anti-phase offset / 40.5 ms livelock period / 340 ms evidence window / 480 ms
ISR mask / 0.9 s sag / 1.55 s flush backoff / 13.9 s drive POST vs ~150 ms
beacon cold-boot / 38 s partition / 96 s corridor cycle / 774 s sync age /
+14 min HACCP peak / +3 d and +7 d institutional repairs / 21 d recurrence
window. Sensor noise is present and explained (DVS flicker floor 0.10–0.12,
fog-attenuated 0.24 transient, adaptation decay on all driven channels,
anomaly doublet breaking the decay exactly where the fault physics says).

### Value for SNN distillation
- CLOCK-DOMAIN GATING OF ORDER CODES (headline): a cross-channel latency code
  is evidence only while its clock domain is intact; here the 412 µs order is
  real but its medium (2.4 ms skew) is corrupted, so arbitration must fall
  back to a drift-invariant key. Completes the timebase-corruption family
  next to r13's send-on-delta time-dilation (tempo theft) with ORDER theft —
  and benign, where r13's was adversarial.
- ANTI-PHASE LIVELOCK AS A SPIKE SIGNATURE: mirrored deterministic policies
  produce a detectable anti-phase limit cycle; symmetry must be broken by
  identity, not by the corrupted clock and not by e-stop.
- ADAPTATION BASELINE MAKES ANOMALIES CHEAP: the inrush spike (1.41) is
  detectable only against the exhibited 1.32→0.99 decay — adaptation is the
  feature, not cosmetics.
- REPRODUCE-THE-ARTIFACT DOCTRINE: an alarm sharing a root with the fault it
  reports is disarmed by quantitative reproduction plus predicate-checking
  the standing rule that amplifies it (memo IM-2026-081's own terms), never
  by generic alarm skepticism.
- FENCING + PAUSED CLOCKS: duplicate stale authority ages into poison;
  monotonic epochs and bounded store-and-forward TTL are the $0-hardware
  repairs, mirrored as the +7 d institutional side-effect.

## Reconciliation and validity receipts
- reward_components: component sum 0.92 and 7-tick sum 0.92 both reconcile to
  total with |diff| < 1e-9 (script-asserted; validator tolerance 1e-6).
- spike_events: 26 events, one timestamp key, globally non-decreasing,
  min same-channel gap 0.957 ms ≥ 0.8 ms, 3 channels inside race_window_us
  1860, 5–40 bound met; adaptation monotone on driven channels with the
  anomaly doublet flagged by design.
- Physics asserts: c_sound(−26 °C) 315.14 m/s; skew 2.3994 ms; one-way bias
  0.7561 m; phantom 1.3476 m/s (0.15% of displayed 1.35); TTC 5.49 s; ΔH
  0.9438 bits × 0.148 = 0.140; stop distance 0.141 m; 387.2 J; tail rates
  0.22% / 0.72%; door budget 137 + 96 = 233 ≤ 240 s/h.
- Repo validators on the exact staged line: check_records.check_record
  (factory_staging=True) → 0 errors, 0 warnings, kind "thalamic";
  verify_execution.verify_record_execution → "verified". Top-level id unique
  in the 2026-08-30 run namespace (no sibling batches committed yet).

## Novel coverage
The coordination-failure class (mirror livelock on a split-brain lease), the
zero-adversary compound structure, the domain, the recovery machinery
(identity-derived symmetry breaking, epoch fencing, paused lease clocks), and
the benign cross-clock aliasing mechanism are all absent from rounds 2–13.
Repeated elements: the ACCEPT decision cell itself (r13 flagged it for
density — this is deliberate), the poisoned-context structural rhyme with
r13's adversary-authored evidence base, and the factory's spike/tick
conventions. Honest estimate below.

Novel coverage: 78%

## What ROUND 2 should add (flagged gaps for the next round to fix)
1. RESTORE FITTED-LEAF GROUNDING: fit ≥ 2 leaves from synthetic logs — e.g.
   the tracker's phantom response from a simulated filter trace (replacing
   the first-order approximation), and the fog attenuation curve from a
   synthetic DVS event-rate vs thermocline log. This round's biggest honesty
   debt.
2. EMBEDDED CONTRAST EPISODE ON THE SAME GATE: the next corridor dispute
   after CR-88 where the collision alarm is REAL (a genuinely converging
   robot) — same gate, opposite correct disposition (REJECT the grant) — so
   the pair teaches "reproduce the artifact" without teaching "disbelieve
   alarms". This is the density-2 form this round lacks.
3. GOVERNANCE SUBGAME (r13 gap 6, carried): should memo IM-2026-081 be
   repealed, or predicated on track validation? A priced meta-gate CR
   decision, extending the r10/r12/r13 authority-economics line.
4. DEFENDER/FORGERY PRICING (r13 gaps 3/5, carried): still open; a natural
   fit for a round that reintroduces an adversary against the now-hardened
   fence (e.g., epoch-forgery cost curve).
5. Domain candidates (de-collided): spiking event-camera traffic
   infrastructure (named r09–r11 and again here, STILL unused);
   district-heating/steam acoustics (r13 candidate, unused); AVOID
   warehouse-amr (now used), irrigation (r13), movable-bridge (r12), rail
   (r10), surgical (r07).
