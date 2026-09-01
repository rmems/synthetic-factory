# Thalamic Trajectory Factory — NOTES round 1 (run 2026-08-30, v2 diversity-guard prompt)

Run: 2026-08-30 · Round: 1 · Output: `batch-r01.jsonl` (5 objects)

**Domains this batch (diversity guard, 5 distinct from the 8-pool):** `industrial-assembly`, `surgical-assist`, `autonomous-driving`, `aerial-swarm`, `underwater-rov`. Held back for round-2 rotation: `warehouse-amr`, `humanoid-locomotion`, `grid-inspection` (rotate at least those three in next batch to avoid inter-batch mode collapse).

**Lineage note.** This is the first committed round of the 2026-08-30 run directory under the v2 prompt (8-domain pool, microsecond race scalars, reward ticks). The prior windows (2026-08-17*, ttf-001..075) were a different prompt lineage with free-form domains; none of their records carry `t0_us`/`race_window_us`/`ticks`. I checked their coverage before writing: no overlap on surgical suturing, urban V2X left turns, fastener torque seating, or quadrotor downwash; partial territorial overlap exists on underwater inspection (their subsea-pipeline AUV and under-ice gliders vs my tether-snap feedforward ROV — same sector, different plant, sensors, and failure mode).

## What this round covered

| id | domain | decision | correctness | outcome class | race (winner / margin) | total |
|----|--------|----------|-------------|----------------|------------------------|-------|
| thalamic-v2-r01-torque-seat-ft-race-8f2a41 | industrial-assembly | ACCEPT | correct | clean success; delayed throughput echo | F/T contact beats vision confirm / 139 µs in 240 µs window | +1.33 |
| thalamic-v2-r01-suture-strain-gate-c47d19 | surgical-assist | MODIFY | correct | partial failure (0.6 mm skive) + regrasp recovery | strain alarm beats command latch / 205 µs in 320 µs window | +0.77 |
| thalamic-v2-r01-v2x-left-turn-hold-3be208 | autonomous-driving | REJECT | correct | safe hold; efficiency deliberately negative | V2X BSM beats radar confirm / 210 µs in 480 µs window | +0.57 |
| thalamic-v2-r01-downwash-wrong-clamp-95ec66 | aerial-swarm | MODIFY | **incorrect (wrong-modify)** | near-miss + reserve-floor crossing + 40 s mission delay | anemometer beats belly pressure / 278 µs in 700 µs window | **−0.06** |
| thalamic-v2-r01-tether-jerk-feedforward-6d0b3f | underwater-rov | ACCEPT | correct | earned success; two delayed costs | tether jerk beats DVL update / 160 µs in 380 µs window | +1.12 |

Decision mix: 2 ACCEPT / 2 MODIFY / 1 REJECT; exactly one wrong gate (wrong-modify — round 2 must alternate to **wrong-reject**). Provenance: all five `designed` (invented plants; nothing here ran in a simulator or on hardware, so claiming `simulated`/`hil` would be provenance inflation).

## The wrong gate, and why it is the one worth training on

Trajectory 4 is the mandated incorrect supervisor decision. The MODIFY is well-formed and cites a real constraint (2.0 m inter-agent separation), which is exactly what makes it a good error-detection target: the flaw is not in the arithmetic but in *bindingness*. The measured +Y margin was 2.6 m (7.5 UWB sigma above the floor), so the sequencing delay defended a non-binding constraint; the vertical clamp acted on an axis with commanded use of zero; and the imposed 250 ms delay exceeded the measured 180 ms gust ETA — the single number that made the pre-emptive window real. `future_outcome.recovery.correct_gate` states the corrective rule (ACCEPT as filed, or speed-only MODIFY; any gate output preserving start_delay < 40 ms keeps the pre-emptive exit). The cost is fully priced: 0.35 m parapet clearance vs 0.5 m floor, battery reserve floor crossed, 6.3 s late re-form, +40 s payload handoff — and the aggregate total lands at −0.06, the round's only negative, so the wrong gate is distinguishable from the correct REJECT (+0.57) *in the reward ledger, not just in the labels*. A subtle bonus in the race construction: had the pressure spike won, the supervisor's own policy table would have released the immediate evade — the flawed rationale is only expressible on the pre-emptive side of the race, tying the gate error to the microsecond ordering.

## Microsecond race realism

Every trajectory carries integer `t0_us` (epoch µs on 2026-08-30), `gate_latency_us` (380/520/640/810/450), `race_window_us` (240/320/480/700/380), explicit `race_window_rel_ms` bounds that reconcile exactly with `race_window_us`, and ≥2 channels spiking inside the window. Race margins (139/205/210/278/160 µs) are all under the min(500, window) reversal bound and each `future_outcome.race_result.counterfactual_if_reversed` narrates a concrete, numerically different world (spiral-search +450 ms; tear-with-bleeding vs recoverable skive; 0.7 g braking in the junction box; delay error inexpressible; 0.42 m excursion and a scrubbed traverse). Gate spikes land at winner-time + gate_latency + stated relay jitter (23–40 µs), so the latency chain is auditable in the train itself. Refractory floor verified programmatically: minimum same-channel gap across all five trains is 922 µs (imu.tool.tremor, T2) — every consecutive same-channel pair ≥ 800 µs. Adaptation is present and physically motivated in each train (F/T contact ring-down 1.85→0.86; strain relaxation under tissue creep 1.90→0.94; radar re-confirm 1.20→0.85; post-gust IMU decay 2.10→0.88; tether harmonic damping 2.30→1.18 with lengthening ISIs). Noise: thermal drift inflating vision latency and residuals, perfusion artifact once crossing the alarm threshold and being vetoed, RSU relay jitter, UWB sigma, silt-degraded visibility.

## Reward-tick reconciliation

One aggregation declared per record in `reward_components._aggregation`: scalar component = arithmetic sum over ticks; total = sum of the five scalar components; single dimensionless scale, no unit mixing. Verified programmatically before staging: every scalar equals its tick-column sum to <1e-9 and every total equals the component sum to <1e-9 (publisher tolerance 1e-6). Tick counts 5/6/5/6/5, each spanning race → execution → consequence horizon, and every `future_outcome.reward_inflection_t_us` points at a real tick where the ledger bends (11 276 µs thread-clean, 7 902 µs skive dip, 4 851 µs safety-spike/efficiency-flip, 182 336 µs gust collapse, 3 431 µs feedforward lock). Deliberate reward-shape variety: T3 teaches a *correct* gate with a persistently negative efficiency component; T4 teaches a *wrong* gate with a negative total; T2 teaches a full-column negative tick that recovers.

## SNN / agentic training value

- **Latency coding as decision content:** in all five, *when* a spike arrives relative to a commit tick is the decision variable (entry-strategy latch, drive rewrite, actor instantiation, pre-emptive-vs-reactive classification, feedforward inclusion). T5's tension line is the cleanest: physical preview whose value is entirely in its arrival order.
- **Credit assignment across timescale gaps:** T4 separates decision spikes (3–4 ms) from consequence spikes (182–260 ms) by ~500× the race margin; T3 embeds the 100 ms BSM cadence beside a sub-millisecond fusion race — two timescales in one ordered train.
- **Error detection:** the wrong-modify is detectable from observables included in-record (binding-margin arithmetic, ETA-vs-delay comparison), so a critic head can be trained to flag it without privileged labels beyond `correctness`.
- **Adaptation/refractory:** every train is usable as-is for Thalamic-Relay → Spikenaut distillation of sensory adaptation; refractory gaps are physically kept, not asserted.

## Residual weaknesses (honest)

1. **All five provenance `designed`; no `simulated` or `hil` object.** Legitimate for invented narratives, but the lineage eventually needs tick/spike streams that a simulator actually emitted, with solver/validation statements to earn `simulated`.
2. **Race margins cluster at 139–278 µs (0.4–0.6× window).** No knife-edge race (<50 µs, near sensor-jitter floor) and no *lost* race (window closing empty, forcing the conservative default path). Both are higher-information temporal edges than a comfortable win.
3. **Every race winner was also the "informative" channel.** No trajectory where the race winner is a *deceptive* channel (spoofed V2X, stuck load cell) and winning makes things worse — the adversarial-timing class the prior lineage explored symbolically has no v2-format exemplar yet.
4. **Reward magnitudes are not yet calibrated across domains** (T1's +1.33 vs T3's +0.57 reflect narrative weight, not a normalized scale); a cross-record convention (e.g., max attainable per episode) would make totals comparable for preference distillation.
5. **Single wrong-gate flavor** (wrong-modify); wrong-reject owed next round. Also no REJECT-that-should-have-been-MODIFY subtlety yet.
6. **Tick components are hand-shaped**, not emitted by a scoring function; the shapes are internally consistent but a shared parametric shaping rule across the batch would resist reward-hacking critiques better.

## Next densification target (round 2)

Rotate to `warehouse-amr`, `humanoid-locomotion`, `grid-inspection` + two unused-pool or least-used domains; make the wrong gate a **wrong-reject** (false-positive block of a safe action, cost = task stall/missed window); add (a) one knife-edge race with margin < 50 µs at the sensor-jitter floor, (b) one *empty-window* race where the conservative default executes and is charged its efficiency price, and (c) one race won by a deceptive channel so order-trust itself is the failure mode. Declare one shared reward-scale convention across the batch and consider one `simulated` object with a stated co-sim validation to diversify provenance honestly.

Novel coverage: 90%

(Accounting: versus prior committed rounds of THIS factory directory the round is trivially 100% novel — there are none. Versus the whole thalamic lineage across earlier run windows, four of five scenario/failure-mode/edge combinations are new territory; the underwater object shares its sector (not plant, sensors, race mechanism, or failure mode) with two prior subsea objects, and the v2 temporal/tick machinery is new to all five. Honest blended estimate: 90%.)
