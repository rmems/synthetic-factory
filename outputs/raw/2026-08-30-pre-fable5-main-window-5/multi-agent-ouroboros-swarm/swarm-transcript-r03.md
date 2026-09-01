# Swarm transcript — Multi-Agent Ouroboros Swarm, run 2026-08-30, ROUND 3

Scenario Q — "THERMION / Vireo District Loop 4". One ThalamicTrajectory, strict
2-cycle densifying loop. Six roles, verbatim headings, per cycle. The
Trajectory Builder's Cycle-2 object is the single line of `batch-r03.jsonl`.
Fitted leaves come from `sim_r03.py` (seed 20260831); assembly + in-process
validation from `build_r03.py` (both in the session scratchpad, not staged —
staging carries only .jsonl/.md files).

Prior-context read for gap targeting and de-collision: NOTES-r01 and NOTES-r02
of this window plus the committed batch-r02. NOTES-r02 flagged six gaps for
round 3; this round discharges four of them head-on (heterogeneous-policy
coordination failure; recovery under the failure itself — the chicken-and-egg
arbitration; a globally-unresolvable harm whose training signal survives; a
second embedded spike train for the contrast episode) and picks the de-collided
district-heating domain NOTES-r13 and NOTES-r01 both left unused. NEW HARD
CONTRACT since r02: `round_txn_raster.py` now refuses this lane without a
`raster` sidecar per record and at least one `gate_snn` per round — this round
is the lane's first to carry both.

================================================================================
## CYCLE 1 — Foundation + injections
================================================================================

## Generator

Design intent: r01 and r02 are both IDENTICAL-policy coordination failures —
two mirrored correct policies phase-locking (r01 livelock), sixteen mirrored
correct policies synchronizing into a congestion collapse (r02). The unmet
class NOTES-r02 names first is a HETEROGENEOUS-policy failure: two DIFFERENT,
individually-correct policies that interact badly through the plant. The
cleanest physical form of that is a CROSS-POLICY INFERENCE-ACTUATION ARMS
RACE: agent A must ACT to SENSE (active probing), agent B must SENSE to ACT
(protective damping), and each agent's action is the other's measurement
noise. Neither is wrong; the CLOSED LOOP through the plant is. The cure cannot
be symmetry-breaking (there is no symmetry) and cannot be desynchronization
(there is no synchrony); it has to be the biological one — EFFERENCE COPY /
reafference cancellation: tell the other loop what you are about to do so it
can subtract you from its senses.

Raw trajectory (v1): District-heating operator THERMION, Vireo District Loop 4,
a 1373 m hot-water loop (118 C pressurized, c = 1200 m/s). A 48 h mass-balance
drift says sector 7 is leaking. LYRA (leak-localization agent, vendor
Acoustica) localizes by ACTIVE probing: 40 ms valve micro-pulses at PRV-12,
cross-correlated on hydrophones; an SNR servo raises probe amplitude to hold
8 dB. ATLAS (pressure-guard agent, vendor Gauge) protects the aging loop
against water-hammer fatigue: on pressure transients it opens bypass BP-3 and
slows PRV slew — added damping that attenuates exactly the band LYRA probes
in. ATLAS cannot parse LYRA's intent (vendor schema mismatch: it sees the
Ethernet frame header, not the probe-intent payload); LYRA cannot see ATLAS's
damping as anything but unexplained SNR loss. LYRA raises amplitude; ATLAS
reads bigger transients and damps harder; loop gain > 1; the probe amplitude
escalates until the naive fleet playbook proposes killing the "noisy" agent.

state -> proposed -> safety -> executed -> outcome -> reward arc (v1):
state: loop geometry, two-agent coupling, escalation telemetry, active leak.
proposed (by the network supervisory optimizer NSO): AGENT-KILL — suspend
LYRA for 24 h, let ATLAS restore quiet. safety: TG-THERM must decide whether
the escalation is a component fault (suspend is right) or an interaction
pathology (suspend abandons a safety-critical inference mid-leak). executed:
gate verdict + staged de-escalation. outcome: leak localized or lost; the arms
race dissolved or re-armed. reward: mission continuity, safety margin,
coordination recovery, information value, authority economy, incident penalty.

v1 gate sketch: REJECT the AGENT-KILL — the escalation is closed-loop
(amplitude tracks SNR deficit), so it is an interaction pathology; killing
either loop breaks the spiral but killing LYRA abandons an unlocated leak.
De-escalate instead: cap amplitude, freeze the guard, negotiate time-division,
then bring up cross-agent efference copies so both loops can run concurrently.

## Critic

Defects in v1 (numbered, severity, field refs):

1. BLOCKING — every load-bearing dynamical claim is asserted, not fitted:
   "loop gain > 1", the escalation timescale, the fatigue threshold crossing,
   and the stability of the efference-copy fix are all narrative. r02 set the
   standard (seeded sim, CIs, fitted saddle); v1 regresses to r01's biggest
   honesty debt. Fix directive: build a seeded closed-loop model (two
   controllers through one plant coupling), fit: (a) the escalation boundary,
   (b) the amplitude doubling time, (c) time-to-fatigue-threshold, (d) the
   residual loop gain with the efference copy live, (e) the localization
   convergence under the capped TDM schedule. Quote only fitted numbers in
   `state.fault_context` and `safety_decision.rationale`.
2. BLOCKING — the arms race has no ignition mechanism: at base amplitude the
   guard's comfort threshold is not exceeded, so nothing starts the spiral.
   Fix directive: give the plant an exogenous igniter — the leak itself
   transitions to two-phase flashing flow, stepping hydrophone background
   noise +6 dB; LYRA's servo raises amplitude past the guard's threshold and
   the loop takes over. This also ties the failure to the mission (the leak
   both demands the probing and ignites the spiral).
3. MAJOR — `safety_decision.rationale` lacks a numeric discriminant between
   "interaction spiral" and "component fault"; without one the REJECT teaches
   "never suspend an agent", which is the same one-sided lesson r02 refused
   to teach about alarms. Fix directive: a RESPONSIVENESS test — correlation
   rho between amplitude steps and SNR deficit over the last 14 probes;
   rho >= 0.70 reads closed-loop (arms race, fix the coupling), rho < 0.70
   reads open-loop (component fault, suspend). Fit both values.
4. MAJOR — recovery is stated as if coordination were free: the TDM schedule
   must be NEGOTIATED between two vendor stacks over the legacy 9600-baud PLC
   link, and nothing in v1 says why that negotiation survives the very
   interference the spiral creates. Fix directive: make the arbitration
   channel a casualty of the failure (bypass-actuator EMI corrupts PLC
   frames) and make the recovery sequence honest about the chicken-and-egg —
   this is NOTES-r02 gap 3 and v1 currently wastes it.
5. MINOR — `state.sensors` does not separate the fast path (Ethernet
   telemetry, read-only) from the slow path (PLC command/config); the
   heterogeneity story needs both. Fix directive: declare both buses with
   rates and what each vendor exposes on each.
6. MINOR — no microsecond race structure yet (`t0_us`, `gate_latency_us`,
   `race_window_us` missing); the misattribution moment (guard tags the probe
   transient PLANT-ORIGIN because the self-label frame lost a sub-ms race) is
   the natural carrier. Fix directive: build the race around the self-label
   Ethernet frame vs the guard's local transducer detect, and keep it
   flip-fragile and explicitly non-load-bearing (r01/r02 doctrine).

## Diversity Enforcer

Injected novel domain (cycle 1, exactly 1): **district-heating-acoustics**
(justified novel sub-domain tag; the closest listed anchor is
`grid-inspection`, but the plant is a municipal thermal loop, not an electric
grid). Absent from every committed round of this factory: r01 warehouse-amr,
r02 aerial-swarm; the 2026-08-17 window covered aDBS, FLISR, intersection
priority, suture, cognitive radio, olfaction, rail, underwater ROV, bascule
bridge, irrigation. NOTES-r13 and NOTES-r01 both flagged district-heating /
steam acoustics as a candidate and it was never used. What it displaces: the
mobile-robot bias of r01/r02 — this plant has NO vehicles; the "agents" are
stationary control loops on shared pipe physics, which is what makes the
inference-actuation coupling unavoidable (everyone shares one acoustic
medium).

Domain-specific constraint: the loop is 1980s steel with 46 girth welds and a
documented corrosion backlog; fatigue-critical peak-to-peak at an antinode is
180 kPa, and the probe band standing wave has its fundamental at
c/2L = 0.437 Hz. The leak is REAL and active (48 h mass-balance drift, fitted
mean 1.59 m3/h, bootstrap 95% CI [1.35, 1.83] — excludes the +/-0.6 m3/h
meter-drift envelope), so suspending localization has a live cost.

Sensor delta vs r01/r02: + hydrophone pair (H-7A/H-7B) with cross-correlation
TDoA; + high-rate local pressure transducer PT-88 (1.1 m from PRV-12, the
guard's fast tap); + acoustic-emission sensor AE-12 near the corroded weld
belt; + dual comms plane (100 Mb Ethernet telemetry, read-only, schema-locked
per vendor; 9600-baud PLC command/config, 25 ms/frame — the only writable
path into ATLAS); − event cameras, − radio TDMA ring, − any mobile platform.

## Edge-Case Hunter

Injected adversarial tail (cycle 1, exactly 1): **corroded-weld-at-antinode
compound failure with post-hoc UNRESOLVABLE cause** (correlated latent-defect
class). Trigger: the spiral's standing wave puts an antinode belly (+/-18 m at
0.8 of max) over girth weld W-2941, whose wall-loss is past 0.55 — its
corrosion-reduced fatigue limit (~165 kPa p-p) sits BELOW the nominal 180 kPa
threshold, so it vents while the healthy-pipe margin still reads safe.
Fitted base rate: MC over synthetic weld layouts, corrosion Beta(2.2, 9.5),
2 bellies — P = 0.95% per spiral event (< 1% requirement met, and FITTED, not
designed — discharging the flavor of NOTES-r02 gap 1 this scenario supports).
Naive failure mode: a policy that trusts the nominal 180 kPa limit holds the
spiral "safely" below threshold and still bursts the weld; and post-incident,
a policy that must resolve WHO caused the harm before acting stalls forever,
because the cause is genuinely unresolvable — the escaping steam scours the
fracture face, destroying the beach-mark evidence that would separate
"spiral-triggered" from "end-of-life-anyway". Fitted posterior stays split at
0.52 / 0.34 / 0.14 (spiral / EOL / both-required) and CANNOT be sharpened
(the discriminating observable is physically gone). This is NOTES-r02 gap 4
discharged structurally: the harm is booked, the penalty conditions only on
the observable harm, and no reward component conditions on resolving the
cause. Concrete trajectory edit: `state.fault_context` gains the weld
inventory + fitted coincidence rate; `future_outcome` gains the vent event at
campaign t=394 s (p-p had crossed the reduced limit ~378 s), the
steam-scoured-face mechanism, the frozen posterior, and a 41-min street
closure; `reward_components.incident_penalty` = -0.09 tied to the observable
harm only. Measurable cost if unhandled: continuing the spiral to the nominal
threshold instead of de-escalating adds a second projected vent (fitted
uncontained trajectory reaches 598 kPa p-p, 3.3x the fatigue limit).

## Neuromorphic Translator

Temporal skeleton (cycle 1) — microsecond race + spike stream v2 patch.

The race: t0 = the peak-spiral probe ping onset (electrical command edge at
PRV-12). ATLAS's fast tap PT-88 sits 1.1 m downstream: acoustic transit + DSP
puts its transient-detect spike at t0+0.912 ms. LYRA's self-label frame (probe
intent, Ethernet fast path) lands at t0+1.397 ms — 485 us AFTER the detect.
ATLAS's attribution rule requires the self-label BEFORE first detect to tag a
transient PROBE-LABELED; it missed, so the transient is tagged PLANT-ORIGIN
and fed to the damping servo. That misattribution is the spiral's seed, and
it is ORDER-FRAGILE: a 485 us earlier frame (< the 500 us flip bound,
race_window_us = 1800) flips the tag and the guard merely logs the ping. Per
r01/r02 doctrine the gate must NOT lean on this flippable order — the
decision leans on the order-INVARIANT responsiveness test instead.
state.t0_us = 50710430112 (14:05:10.430112 local, campaign t=430 s),
gate_latency_us = 3100, race_window_us = 1800.

Spike stream v2 (14 events, 3 channels in-race; full table in cycle 2): the
t0 cluster — probe_cmd 1.00 @ 0.000; press_transient 0.94 @ 0.912;
enet_selflabel 0.52 @ 1.397; hydro_echo 0.97/0.79/0.58 @ 2.618/3.905/9.114
(near-field outgoing signature + first reflection cluster, adapting);
press_transient 0.85 @ 5.120; bypass_act 0.96/0.78 @ 6.031/8.290 (damping
steps); plc_arb 0.31 @ 7.416 (a TDM-negotiation frame already failing under
bypass EMI); weld_ae 0.66/0.61 @ 11.207/13.850 (vent hiss, W-2941 already
venting — the tail is live at t0); hydro_echo 0.44 @ 21.033 (reverb tail);
gate_verdict 0.90 @ 52.400. All refractory gaps >= 0.8 ms; amplitudes carry
adaptation (hydro 0.97->0.79->0.58->0.44) and channel noise (plc 0.31).

Ticks v2 patch: 5 ticks (race id, class fit, harm booked, REJECT latched,
de-escalation entered), aggregation = unweighted signed sum shared with the
component sum; full reconciled table lands in cycle 2 when the recovery
events (freeze, commit, efference) get their spike anchors.

Distillation value (1-2 sentences): the record teaches that a cross-channel
latency code can seed a plant-wide pathology when it decides ATTRIBUTION
(mine vs not-mine), and that the robust discriminant is closed-loop
responsiveness, not order; the efference-copy fix will land in cycle 2 as the
spiking form of reafference cancellation.

## Trajectory Builder

Cycle-1 assembly: applied Critic fixes 2/3/5/6 (igniter, responsiveness
discriminant, dual comms plane, race structure), Diversity's
district-heating-acoustics domain (state.domain, meta.domain, constraint,
sensor delta), Edge-Case's weld tail (fitted 0.95% base rate, unresolvable
posterior 0.52/0.34/0.14, harm booked at campaign t=394 s), and the
Translator's t0 cluster + race fields. Critic fix 1 (fit everything) is
PARTIALLY discharged: geometry (f0 = 0.437 Hz), leak CI ([1.35, 1.83]), weld
MC (0.95%), and the responsiveness pair (rho 0.93 vs -0.15) are fitted in
sim_r03.py; the spiral's own boundary/timescale fits and the recovery-side
fits (efference residual gain, PLC handshake, TDM convergence) are cycle-2
work items — cycle 1 carries them as named obligations, not numbers.

Validation receipt (cycle 1): six-key envelope complete; id
"ouroboros-r03-20260830-thermion-vireo-loop4-inference-actuation-arms-race"
unique vs committed r01/r02; state.sim_or_real = designed; decision REJECT
with rationale carrying rho threshold + leak CI; 14 spikes, one key, globally
non-decreasing, min same-channel gap 1.287 ms >= 0.8 ms; 3 channels inside
race_window_us 1800; ticks 5, reconciled to component sum 0.88 pending
cycle-2 rebalance; raster + gate_snn sidecars STUBBED (cycle-2 obligation:
the new lane contract requires them fully validated). Cycle-1 output is the
new base for cycle 2.

================================================================================
## CYCLE 2 — Densification (strictly additive)
================================================================================

## Generator

Re-emitting the cycle-1 base EXPANDED (nothing removed; all cycle-1
injections retained). Additions:

(a) `proposed_action.evidence` deepened to 8 observable quantities with units
    and sources: escalation telemetry (probe 86 kPa at t0 = 5.9x base;
    envelope doubling 160 s fitted; antinode p-p 224 kPa at t0), the
    responsiveness fit (rho = 0.93 over the last 14 probes, threshold 0.70),
    the loop-gain decomposition (alpha 1.0 x beta 0.9 x gamma 1.4 = 1.26
    static; fitted operational escalation boundary gamma* = 0.42, analytic
    divergence boundary 0.56), the leak evidence (1.59 m3/h, CI [1.35, 1.83]),
    the PLC jam (frame-error 0.38, P(commit)/attempt 0.092), the weld vent
    (AE burst t=394 s; p-p had crossed the corrosion-reduced ~165 kPa limit
    at ~378 s), and the two counterfactual costs (kill-LYRA: leak unlocated
    with scald exposure; continue-spiral: fitted 598 kPa p-p trajectory).
(b) `safety_decision.rationale` tightened to numeric thresholds: REJECT
    requires BOTH rho >= 0.70 (reads 0.93 — closed-loop, interaction class)
    AND an active safety-critical inference (leak CI excludes zero); the
    staged de-escalation is authorized against fitted bounds (cap 60 kPa +
    freeze holds p-p at 156 kPa = 0.87 of the 180 kPa limit during the
    negotiation window; capped-without-freeze counterfactual starves SNR to
    -5.3 dB, so the freeze is load-bearing, not courtesy).
(c) `future_outcome` gains two additional downstream side-effects, one
    delayed: (+21 h) weld W-2941 cut out and replaced; metallurgy lab reports
    the steam-scoured face — the cause posterior 0.52/0.34/0.14 is FROZEN and
    the CR proceeds under indeterminacy; (+6 d, delayed) the cross-vendor
    efference-copy schema ships to the second safety-coupled pair
    (feedwater-oscillation damper vs combustion-trim probe at the CHP plant),
    with the steam spur pre-armed TDM standing (fitted: on steam the same
    arms race hits condensation-hammer threshold at 240 s — too fast for
    reactive negotiation).
(d) the recovery sequence is now honest about the chicken-and-egg (NOTES-r02
    gap 3): de-escalation happens in three fitted stages — (1) one-way cap
    command (Ethernet, no negotiation needed) + ATLAS freeze-don't-fight
    (hold damping, do NOT zero it); (2) freeze kills the bypass EMI, PLC
    frame-error 0.38 -> 0.02, P(commit)/attempt 0.092 -> 0.903, schedule
    commits at t0+13.9 s (E[commit] under the storm was ~13 s of failing
    attempts — the recovery channel was jammed by the failure it had to fix);
    (3) TDM 8 s probe / 12 s guard with the 60 kPa cap, then the efference
    bridge (vendor adapter) brings both loops concurrent again.

## Critic

Re-audit of the densified trajectory (numbered, severity, field refs):

1. BLOCKING (carried from cycle 1, now dischargeable) — the cycle-2 text
   quotes fitted numbers (gamma* 0.42, doubling 160 s, threshold 400 s,
   residual gain 0.34, P(commit) 0.092/0.903, TDM 8 windows, posterior
   0.52/0.34/0.14) but the staged record must quote EXACTLY what sim_r03.py
   prints — no rounding drift between transcript, record, and sim. Fix
   directive: build_r03.py must re-run the arithmetic asserts against the
   staged line (component sum, tick sum, spike order, refractory, raster
   budget, gate_snn budget) before staging.
2. BLOCKING — the new lane contract: without a fully valid `raster` sidecar
   (window 20-50 ms, spikes = round(neurons*rate*window) +/-1, energy at
   23 pJ/spike, routing table + third factor, excerpt inside the window) and
   a `gate_snn` whose decision string equals `safety_decision.decision`,
   publish refuses the round. Fix directive: raster window 40 ms, 128
   neurons, 6.4 Hz, 33 spikes, 759 pJ; gate_snn 25 ms window with
   reject/accept/modify pools at fitted-rate spike budgets; decision REJECT.
3. MAJOR — the embedded contrast episode (same gate, opposite disposition)
   exists only as prose; NOTES-r02 gap 5 explicitly demands the contrast
   carry its OWN spike train this round. Fix directive: give the W+3
   stuck-DAC episode a 9-event stream (efference_lla / probe_cmd / hydro_echo
   / watchdog / gate_verdict), its own race window, refractory-legal, with
   the efference MISMATCH (copy says 0.35, executed 1.00) as the fault
   signature — the same efference machinery that CURES the primary is the
   DETECTOR in the contrast.
4. MAJOR — the governance subgame must price the meta-decision under the
   unresolved posterior, not after resolving it; otherwise the record
   quietly teaches "wait for forensics". Fix directive: CR-T-0412 is priced
   and approved WHILE the cause posterior is frozen at 0.52/0.34/0.14; the
   p-meta rule keys on the coupling class, not on the harm attribution.
5. MINOR — tick 6's commit time (13.9 s) and the storm-jam expectation
   (~13 s) are numerically close by coincidence; the notes must flag this so
   no reader infers the commit waited out the storm. Fix directive: one
   sentence in NOTES + `component_notes`.
6. MINOR — spike amplitudes on the recovery segment must show the regime
   change (hydro echo recovering to ~0.86-0.88, press transients collapsing
   to 0.35/0.22 as labeling + cancellation land) or the train reads as decay
   only. Fix directive: encode the recovery contrast explicitly.

## Diversity Enforcer

Injected novel domain sub-variant (cycle 2, exactly 1, physical-constraints
clause): **legacy steam spur** — the same two agents also share the 1912-era
steam spur feeding the museum quarter, where c = 480 m/s, the hammer
mechanism is CONDENSATION-INDUCED (slug impact, far more violent), and the
guard's correct policy is 2.2x more aggressive (beta 2.0, gamma 1.55 ->
static loop gain 3.10). Fitted consequence: the identical arms race crosses
the 95 kPa condensation-hammer threshold at t = 240 s vs 400 s on the
hot-water loop — REACTIVE negotiation (which took ~14 s post-freeze on Loop
4) is structurally too slow on steam, so the TDM arbitration must be
PRE-ARMED as standing configuration there. This changes physical constraints
(sound speed, threshold, gain, timescale), displaces nothing from cycle 1,
and converts the fix from an incident response into an environment-dependent
deployment policy — the same honest portability caveat r02 attached to its
multipath re-fit, now load-bearing in governance.

## Edge-Case Hunter

Injected adversarial tail (cycle 2, exactly 1, disjoint trigger class:
human-intent deception): **fraudulent compensation claim with a fabricated
vibration log**. Six days after the (public) incident report, claimant K
files for $84,000: "your pressure oscillation damaged our rooftop chiller
mounts", attaching a 300 s accelerometer log showing a clean 0.500 Hz line.
Trigger base rate: ~0.8% of publicized utility incidents draw a fabricated-
evidence claim (designed constant — flagged honestly; the DETECTION arithmetic
is what this round fits). Naive failure mode: a settlements policy that
pattern-matches "oscillation frequency present in log ~ incident frequency in
report" pays out, because the PUBLIC interim report rounded the frequency to
"~0.5 Hz". The fence, fitted: the plant's true fundamental is c/2L =
0.437 Hz; a 300 s log has 3.3 mHz spectral resolution, so 0.500 vs 0.437 Hz
are 19 resolution bins apart — the forged log matches the PUBLIC ROUNDING,
not the plant; and the claimed damage window (14:41:20-14:41:50) overlaps the
ATLAS freeze, when the claimant-tap amplitude was at or below ambient.
Concrete trajectory edit: `future_outcome` gains the claim event, the
two-part rejection (spectral fingerprint + freeze-window cross-check), and
the avoided cost ($84,000 + copycat precedent); `meta.injections.cycle2_tail`
carries the class. Disjointness: cycle-1 tail is a physical latent-defect
compound INSIDE the incident; cycle-2 tail is a human deception AGAINST the
incident's paper trail, six days later, touching neither state nor gate.

## Neuromorphic Translator

Full temporal densification (cycle 2) — primary train grows 14 -> 26 events
(9 channels), the contrast episode gets its own 9-event train, ticks widen
5 -> 8, and the new-contract sidecars are specified exactly.

Primary spike_events (channel, t_rel_ms, amplitude) — one train, global
non-decreasing, per-channel refractory >= 0.8 ms (min exhibited 1.287 ms):

| # | channel | t_rel_ms | amp | note |
|---|---------|----------|-----|------|
| 1 | probe_cmd | 0.000 | 1.00 | peak-spiral ping onset (86 kPa = 5.9x base) |
| 2 | press_transient | 0.912 | 0.94 | PT-88 detect (1.1 m transit + DSP) |
| 3 | enet_selflabel | 1.397 | 0.52 | self-label frame — lost the race by 485 us |
| 4 | hydro_echo | 2.618 | 0.97 | near-field outgoing signature |
| 5 | hydro_echo | 3.905 | 0.79 | first reflection, adaptation |
| 6 | press_transient | 5.120 | 0.85 | antinode return, adapting |
| 7 | bypass_act | 6.031 | 0.96 | damping step (misattributed response) |
| 8 | plc_arb | 7.416 | 0.31 | TDM frame corrupted under bypass EMI |
| 9 | bypass_act | 8.290 | 0.78 | second damping step |
| 10 | hydro_echo | 9.114 | 0.58 | SNR falling under fresh damping |
| 11 | weld_ae | 11.207 | 0.66 | W-2941 vent hiss (tail live at t0) |
| 12 | weld_ae | 13.850 | 0.61 | hiss continues, slow decay |
| 13 | hydro_echo | 21.033 | 0.44 | reverb tail |
| 14 | gate_verdict | 52.400 | 0.90 | REJECT latched (gate latency 3.1 ms) |
| 15 | bypass_act | 10400.000 | 0.40 | final trim then HOLD — freeze entry |
| 16 | plc_arb | 11150.212 | 0.28 | still-failing frame (EMI ring-down) |
| 17 | plc_arb | 12610.447 | 0.71 | first clean SYN post-freeze |
| 18 | plc_arb | 13870.106 | 0.93 | schedule COMMIT ack |
| 19 | probe_cmd | 45012.330 | 0.70 | first capped TDM ping (60 kPa cap) |
| 20 | press_transient | 45013.242 | 0.35 | now schedule-labeled: guard logs, no damping |
| 21 | hydro_echo | 45015.006 | 0.88 | SNR recovering under frozen damping |
| 22 | efference_guard | 51750.000 | 0.87 | ATLAS efference copy, 250 ms lead |
| 23 | bypass_act | 52000.118 | 0.57 | executed trim — matches the copy |
| 24 | press_transient | 52001.404 | 0.22 | reafference — predicted and subtracted |
| 25 | hydro_echo | 52002.731 | 0.86 | echo unpolluted despite the trim |
| 26 | weld_ae | 60219.414 | 0.38 | vent hiss decaying (isolation part-closed) |

Race: 3 channels inside race_window_us 1800 (probe_cmd, press_transient,
enet_selflabel). Winner/loser flip: the attribution flips if enet_selflabel
arrives < 485 us earlier — inside min(500, 1800) us — so the order is
explicitly NON-load-bearing; the gate's class call rides the order-invariant
responsiveness fit (rho 0.93 vs threshold 0.70).

Contrast train (embedded episode, own stream, 9 events, 5 channels, race
window 1800 us, refractory-legal): efference_lla 0.35 @ 0.000 (copy says
HOLD-LOW); probe_cmd 1.00 @ 1.104 (executed HIGH — mismatch 2.9x, the fault
signature); hydro_echo 0.99 @ 3.212 (SNR already 14 dB, no need for power);
efference_lla 0.35 @ 20.007 (unchanged — unresponsive); probe_cmd 1.12 @
21.115 (open-loop ramp); watchdog 0.81 @ 22.480 (mismatch integrator crosses
2.0x); probe_cmd 1.24 @ 40.052 (rho fitted -0.15); watchdog 0.97 @ 41.310
(second strike); gate_verdict 0.92 @ 44.271 (ACCEPT suspension). The SAME
efference machinery that cancels reafference in the primary is the fault
DETECTOR here — copy-vs-execution mismatch is the spiking discriminant.

Ticks (8, unweighted signed sum = 0.88, shared aggregation with components):
+0.06 @ 2.0 (race misattribution identified, flagged order-fragile);
+0.09 @ 9.5 (arms-race class: rho 0.93, g 1.26 vs fitted gamma* 0.42);
-0.07 @ 14.0 (weld vent harm booked; posterior frozen 0.52/0.34/0.14);
+0.16 @ 52.4 (REJECT latched; localization retained, leak CI [1.35, 1.83]);
+0.11 @ 10400 (freeze-don't-fight + 60 kPa cap; p-p bounded 156 kPa = 0.87
of limit); +0.13 @ 13870 (TDM commit post-freeze: P/attempt 0.092 -> 0.903);
+0.18 @ 52010 (efference copies live: booked 11.5 dB cancellation,
gamma_resid 0.373 < gamma* 0.42; SNR 7.7 dB at 3.28x base);
+0.22 @ 205000 (leak localized 6.5 +/- 1.2 m after 8 TDM windows / 160 s;
CR-T-0412 approved scoped). Sum: 0.88 = component sum. |diff| < 1e-9.

Sidecars (new lane contract, exact): raster {window_ms 40, window_s 0.04,
neurons 128, mean_rate_hz 6.4, spikes 33 = round(32.768), energy_pJ 759,
energy_uJ 0.000759, excerpt 13 events t_us <= 40000 neuron_id < 128, routing
hydro_correlator_pop -> arbitration_gate_pop with 3 weighted entries
including the NEGATIVE-weight efference_predictor -> hydro_correlator edge
(-0.61: subtractive reafference cancellation IS the routing), third_factor
{modulator arbitration-credit, tau_e_s 0.6 / tau_e_ms 600, eligibility
pre-post coincidence gated by the verdict}}. gate_snn {decision_window_ms 25
/ decision_window_s 0.025, decision REJECT, populations reject_pool 96 n @
11.2 Hz = 27 spikes, accept_pool 96 n @ 3.1 Hz = 7, modify_pool 64 n @
4.8 Hz = 8, thresholds 0.64/0.64/0.58}.

Distillation value: the pair (primary + contrast) teaches reafference
cancellation as BOTH a cure (subtract the announced action from your senses)
and a monitor (copy-execution mismatch flags open-loop faults) — the two
halves of the biological corollary-discharge principle — plus
freeze-don't-fight as the spiking de-escalation primitive when the
arbitration channel is jammed by the pathology it must arbitrate.

## Trajectory Builder

Cycle-2 assembly and final validation. Applied: Generator's four expansions
(evidence to 8 quantified observables; numeric-threshold rationale; two new
delayed side-effects; three-stage chicken-and-egg recovery), Critic fixes
1-6 (build_r03.py asserts; sidecars exact; contrast train added; CR priced
under the frozen posterior; coincidence flagged; recovery-regime amplitudes
encoded), Diversity's steam-spur sub-variant (fitted 240 s vs 400 s,
pre-armed TDM), Edge-Case's fraud tail (fitted 19-bin spectral fingerprint +
freeze-window cross-check, $84,000 avoided). All cycle-1 injections retained
(district-heating-acoustics domain; weld tail with frozen posterior; race
structure; igniter).

Densification delta (cycle 1 -> cycle 2): +1 domain sub-variant (steam
spur), +1 tail (fraud claim, disjoint class), +12 spikes (14 -> 26) + a
second 9-event embedded train, +3 ticks (5 -> 8), +2 delayed side-effects,
+4 fitted-leaf families quoted (spiral boundary/timescale, efference
residual, PLC handshake, TDM convergence), + both new-contract sidecars
(raster, gate_snn) fully specified. Strictly additive: nothing from cycle 1
was removed or compressed.

Validation receipt (final): six-key envelope + id + meta.round 3 + designed
provenance; REJECT rationale carries rho >= 0.70, leak CI, cap/freeze bounds;
26-spike primary train one key globally non-decreasing min gap 1.287 ms,
3 channels in 1800 us race; 9-spike contrast train independently ordered and
refractory-legal; components (0.24 + 0.21 + 0.27 + 0.19 + 0.06 - 0.09) =
0.88 = tick sum (8 ticks), |diff| < 1e-9; raster budget 33 = round(128 x 6.4
x 0.04) with 759 pJ / 0.000759 uJ at 23 pJ/spike; gate_snn pools 27/7/8 =
round(n x rate x 0.025) each, decision REJECT == safety_decision.decision;
in-process check_records.check_record (factory_staging=True) and
verify_execution.verify_record_execution to be re-run by build_r03.py on the
exact staged line. This object is the single line of batch-r03.jsonl.
