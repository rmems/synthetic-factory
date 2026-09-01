# Thalamic Trajectory Factory — NOTES round 2 (run 2026-08-30, v2 diversity-guard prompt)

Run: 2026-08-30 · Round: 2 · Output: `batch-r02.jsonl` (5 objects)

**Domains this batch (diversity guard, 5 distinct):** `warehouse-amr`, `humanoid-locomotion`, `grid-inspection`, `surgical-assist`, `industrial-assembly`. This rotates in all three domains r01 held back (warehouse-amr, humanoid-locomotion, grid-inspection) plus two r01 sectors on entirely different plants: surgical moves from suturing/strain to bipolar vessel sealing/impedance, industrial moves from fastener torque-seating to adhesive bead dispensing/open-time. Held back for round 3: `autonomous-driving`, `aerial-swarm`, `underwater-rov`.

## What this round covered

| id | domain | decision | correctness | edge | race (winner / margin / window) | total |
|----|--------|----------|-------------|------|--------------------------------|-------|
| …amr-uwb-jitter-floor-7be4d2 | warehouse-amr | ACCEPT | correct | knife-edge race below jitter floor | UWB vest beats lidar legs / 34 µs / 150 µs | +1.50 |
| …grate-slip-capture-sim-3fa9c8 | humanoid-locomotion | MODIFY | correct | **simulated provenance** (script-emitted stream) + counterfactual sim | pelvis jerk beats ankle confirm / 182 µs / 350 µs | +0.84 |
| …capbank-emi-spoof-c25e71 | grid-inspection | ACCEPT | correct | deceptive channel wins the race | cap-bank EMI beats IR / 96 µs / 420 µs | +0.67 |
| …seal-impedance-wrongreject-9d40b6 | surgical-assist | REJECT | **incorrect (wrong-reject)** | false-positive block; correct gate was MODIFY(defer) | impedance beats blood-pool / 260 µs / 600 µs | **−0.15** |
| …bead-watchdog-default-62f8a3 | industrial-assembly | MODIFY | correct | watchdog-as-contender; expected channel misses its window | low-conf partial beats watchdog / 441 µs / 900 µs | +0.99 |

Decision mix: 2 ACCEPT / 2 MODIFY / 1 REJECT; exactly one wrong gate, and it alternates flavor from r01 (**wrong-reject** after r01's wrong-modify). Every densification target r01 named was landed: (a) knife-edge margin < 50 µs at the sensor-jitter floor, (b) an empty-expected-channel/window-close race where the conservative default executes and is charged (realized within the ≥2-channels-in-window contract by making the watchdog spike a first-class contender), (c) a race won by a deceptive channel so order-trust itself fails, (d) wrong-reject with the added REJECT-should-have-been-MODIFY subtlety, (e) one shared reward-scale convention declared identically in all five records, and (f) one honestly `simulated` object.

## The wrong gate, and why it is detectable

T4's REJECT cites a real floor (45 Ω short-circuit) with a real reading (38 Ω) — the flaw is a temporal-predicate error, not arithmetic: the sample was drawn at +64 ms, inside the documented 120 ms post-grasp settling transient the floor explicitly does not apply to, while the settled read (52 Ω) sat in evidence at gate time and the gated latch event *was* the 45 Ω rising crossing. A critic can convict the gate from three in-record numbers (sample age 64 < settling window 120; settled 52 ≥ floor 45) plus the policy text in `state.constraints`. The cost is fully priced and lands at −0.15 (the round's only non-positive total, per the batch convention that wrong gates price ≤ 0): 41 s stall, +0.55 mL loss, one suction cycle, and a delayed trust cost — the surgeon pulls energy authority to manual for 9 remaining seals (−0.12 efficiency / −0.09 coherence tick at 44.4 s). `recovery.correct_gate` states the corrective rule: MODIFY (defer ~300 ms until settled, re-sample, release) — covering r01's noted missing REJECT-should-have-been-MODIFY subtlety. The race is deliberately orthogonal: reversal would have latched the urgent profile and the flawed rationale blocks that too, so error detection must come from the settling arithmetic, not the order.

## Microsecond race realism

All five carry integer `t0_us` (2026-08-30 epoch µs), `gate_latency_us` (260/520/890/470/1450), `race_window_us` (150/350/420/600/900) with `race_window_rel_ms` bounds reconciling exactly, ≥2 channels spiking in-window, and margins (34/182/96/260/441 µs) all under min(500, window) so every counterfactual reversal is live. Margin *meaning* now varies deliberately: T1's 34 µs sits below the measured 44 µs timestamp jitter (order ≈ coin flip; the gate's order-robustness check — both latch branches verified safe — is the teaching point), while T2's 182 µs is >3× jitter and carries a simulated 100/100 fall stake; T3's winner is legible as a spoof from the train itself (8.333 ms = 120 Hz-locked follow-on bursts, zero correlation with the 60 Hz `mag.line.current` reference channel); T5's loser is a watchdog, making timeout a first-class temporal event. Race mechanisms also diversify: sensor-vs-sensor (T1/T3/T4), detection-latency asymmetry between heterogeneous confirm pipelines (T2: 2-sample @2 kHz vs transmission+rise @8 kHz), and evidence-vs-deadline (T5). Refractory floor verified programmatically across all trains (≥ 0.8 ms same-channel, enforced at 0.9 ms in the T2 solver); adaptation ladders present on every repeated channel (e.g. T2 pelvis jerk 1.68→0.88 across five events; T4 impedance 1.60→1.42→1.05 with a 1.31 re-grasp reset — adaptation with stimulus-change recovery); noise via jitter draws, thermal/RH terms, occlusion, and context channels.

## Simulated provenance (new to the lineage)

T2 is the first object in this factory whose stream a solver actually emitted: an RK4 (50 µs step) lateral-LIPM with support-slide + velocity-kick slip model, threshold-crossing event generation with per-channel Gaussian timestamp jitter, hard 0.9 ms refractory, amplitude-adaptation ladder, seeded (seed 0, seed policy documented in `state.simulation`), and a counterfactual branch run 100× to price the losing latch outcome (100/100 falls, median 0.52 s). Spike times, race margin, ICP/capture-deficit/sway/duty numbers, and tick timeline are copied verbatim from the script's output; `state.simulation.fidelity_limits` states plainly that it is a reduced-order event-level model not validated against gait data. This earns `simulated` honestly — r01's residual weakness #1 — without inflating the other four, which remain `designed`.

## Reward-tick reconciliation and the shared scale

One aggregation declared per record (`_aggregation`: component scalar = sum over ticks; total = sum of five components) plus, new this round, one batch-wide `convention` string in every record: components ∈ [−1, +1] with +1 = max attainable for that component this episode; clean success targets total ∈ [1.2, 1.6]; wrong gates must price ≤ 0. Verified programmatically before staging: every scalar equals its tick-column sum and every total equals the component sum to < 1e-9 (publisher tolerance 1e-6; 2-decimal increments). Tick counts 5/6/6/7/6; every `reward_inflection_t_us` points at an actual tick. Resulting totals are now comparable across domains: 1.50 (clean, order-robust) > 0.99 (MODIFY that caught a defect) > 0.84 (MODIFY partial+recovery) > 0.67 (correct gate, deceived world) > −0.15 (wrong gate) — a usable preference ordering, which r01's uncalibrated magnitudes were not.

## SNN / agentic training value

- **Order as evidence vs order as noise:** T1 (sub-jitter, ~0.62 posterior) against T2 (3.8× jitter, fall-stakes) teaches margin-conditioned trust in spike order — arguably the core thalamic-relay competency.
- **Temporal-pattern discrimination:** T3's deception is decodable purely from inter-spike intervals (120 Hz lock vs phase-correlated stochastic PD) inside the published train; no auxiliary features needed.
- **Timeout as spike:** T5 renders evidence-absence as an event with a price (441 µs from a 14-minute rework), plus a 9-second-early predictive transient (nozzle accel at 4.317 ms → defect at 9.481 s) for long-gap credit assignment.
- **Error detection:** T4's wrong gate is provable from a sample-age predicate in-record — trainable without privileged labels beyond `correctness`.
- **Solver-grade consistency:** T2's spikes, ticks, and narrated margins cannot disagree because one script produced them.

## Residual weaknesses (honest)

1. **Four of five records remain hand-shaped in their tick values** (T2's are script-conditioned but the shaping constants are still authorial); a batch-shared parametric scoring function emitting all five tick tables would better resist reward-hacking critiques.
2. **The T2 simulation is reduced-order** (lateral-only LIPM, no sagittal coupling, no contact transients beyond a modeled ring); its counterfactual 100/100 fall rate is honest sim output but the saturation (all worlds fall) wastes the graded-risk information a richer model would give.
3. **No `hil` object anywhere in the lineage**, and no way to earn one from this seat — permanent until real bench data enters the pipeline.
4. **Wrong-gate flavors now cover wrong-modify and wrong-reject once each**, but never a wrong-ACCEPT (missed hazard) — the highest-stakes supervisor error class has no v2 exemplar, partly because pricing a wrong-ACCEPT without narrating harm-as-spectacle takes care.
5. **Race margins and windows are still author-chosen round numbers** at the scenario level (150/350/420/600/900); a future round could derive windows from stated sensor cadences instead.
6. **All five scenarios resolve within one episode**; the lineage still lacks a v2 trajectory whose main consequence lands in a *different* episode's record (cross-record consequence threading), which the old free-form lineage did explore.

## Next densification target (round 3)

Rotate to `autonomous-driving`, `aerial-swarm`, `underwater-rov` + two least-used domains; make the wrong gate a **wrong-ACCEPT** (missed-hazard flavor, priced through a near-miss consequence chain, not spectacle) to complete the error taxonomy. Add: (a) a second `simulated` object with a *graded* counterfactual (fall/violation probability in the 20–60% band so risk is informative, e.g. a hydrodynamic tether or gust model), (b) one record whose window/geometry derive explicitly from declared sensor cadences (e.g. 100 ms BSM beacon vs 25 Hz lidar frame alignment), and (c) a batch-shared parametric tick-shaping rule documented once and instantiated five times. Consider threading one delayed consequence into a round-4 record (cross-record horizon) if the operator authorizes the linkage convention.

Novel coverage: 78%

(Accounting: versus this factory directory's only committed round (r01), all five scenario/edge/mechanism combos are new — no repeated plant, failure mode, race mechanism, or gate-error flavor, and three of five temporal edges (sub-jitter race, watchdog contender, script-emitted simulated stream) have no r01 analogue at all. The discount to 78% is for the wider pre-v2 lineage across earlier run windows: warehouse-AMR navigation and powerline inspection exist there as free-form domains (different plants/mechanisms here), a wrong-reject exemplar exists symbolically (open-pit haul truck), and adversarial spoofing exists institutionally though not as microsecond race-order deception; none carry v2 race scalars, ticks, or spike-train machinery.)
