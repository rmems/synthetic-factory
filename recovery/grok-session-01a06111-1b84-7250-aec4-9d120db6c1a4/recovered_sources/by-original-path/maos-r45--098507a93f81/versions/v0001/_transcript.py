def write_transcript(rec, line):
    c1_spikes = [e for e in rec["spike_events"] if e["t_rel_ms"] <= C1_SPIKE_CUTOFF_MS]
    text = """# Multi-Agent Ouroboros Swarm — Round 45 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r45-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented ETHYNWOLD / Woadfen Steam Cracker EC-7 (not TRIAD / Meridian / VANTIS-CADENCE-AEGIS / LYOSHIELD / CINDERWICK / BOGIRON / NITREVAULT)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r45.jsonl).

---

# CYCLE 1 — Foundation + injections

## Generator

Design intent: a 16-coil millisecond steam cracker where three
correct agents each read a tube-side loop because a 16 min cracked TLE
inlet bypass partitions mixed-true process gas from tube-true cooling.
The naive playbook raises COT into a bypassed TLE. The gate must MODIFY
on a numeric severity ceiling, not by killing an agent.
sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Woadfen EC-7, COT 842 C,
tube 348 C, steam/HC 0.52, proposed RAISE-SEVERITY +8 K,
safety MODIFY to SEVERITY-HOLD, executed hold without the steam-ratio
numbers fully specified, outcome "bypass found, cell saved"
(this last claim is the defect the later cycles will refuse to keep).
Sixteen spikes, five ticks, raster/gate_snn present but the scar is a
single edge.

```json
{
  "id": "maos-r45-001",
  "state": {
    "sim_or_real": "designed",
    "domain": "industrial-process",
    "description": "Cell EC-7 at TLE duty; three tube loops in-spec; supervisor proposes raise-severity.",
    "t0_us": 1786224000000061,
    "gate_latency_us": 694,
    "race_window_us": 500
  },
  "proposed_action": {"name": "raise_severity", "parameters": {"raise_k": 8.0}},
  "safety_decision": {"decision": "MODIFY", "rationale": "Hold; do not raise while mixed residual is high."},
  "executed_action": {"name": "severity_hold", "executed_as_proposed": false},
  "future_outcome": {"summary": "Bypass found, cell saved."},
  "reward_components": {"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"},
  "meta": {"round": 45, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}
}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "cell saved". If the pre-t0 cone later trips the
   compressor screen, booking +0.40 is a lie. Fix: declare `_aggregation`,
   emit 3–8 ticks that sum to task_progress+safety+efficiency+coherence+exploration,
   and do not call a quarantined island a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote
   do not raise while r_T > 18 K AND missing steam > 0.8 t/h.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-process` collides with generic MES vocabulary and teaches
   nothing. Ethylene steam-cracker coil (mixed-header residual vs TLE
   tube-outlet, missing steam as a bypass flag) is absent from prior
   ouroboros rounds and must be named.
4. **major — race under-specified.** One mix channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted `t_rel_ms`
   and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated weight
   repeats r04's one-edge rollback and is thinner than r14's two-edge.
   NOTES-r14 item 4 asked for three edges where pair rollback fails.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **ethylene-steam-cracker-coil**
(justified novel subdomain of industrial-process / olefins pyrolysis; explicit tag
`ethylene-steam-cracker-coil`).

Displaced: the Generator's generic `industrial-process` bucket, and any
temptation to reuse warehouse-amr, aerial-swarm, district-heating,
event-camera-traffic-grid, pharmaceutical-lyophilization, water-treatment,
float-glass, underwater-rov, electrolytic-aluminum, czochralski-pull,
slot-die coating, pem-water-electrolysis, wind-turbine pitch,
surgical-assist, optical-fiber-draw, kraft-recovery-boiler,
steel-continuous-caster, humanoid-locomotion, vacuum-induction melt,
steam-methane reformer, cement-rotary-kiln-clinker,
autoclave-composite-cure, geothermal-binary-orc, tire-curing-press,
chlor-alkali-membrane-electrolysis, delayed-coker, lng-mche,
claus-sulfur-recovery, blast-furnace-burden-descent, ammonia-converter,
or hdpe-slurry-loop. FCC-riser and autonomous-driving are left unused.

Domain-specific constraint: severity raise must remain forbidden while
r_T > 18 K even if tube-outlet T is inside the healthy band; missing
steam is a bypass flag the tube TI cannot substitute for.

Sensor delta: +COT mean TT, +steam/HC ratio, +TLE tube-outlet TT,
+mixed-header residual; -any mobile robot, -event-camera gantries,
-DVS, -Pirani/CM, -RGA quadrupole, -DVL, -pitch encoder, -tendon LVDT,
-insole GRF, -kiln zirconia, -smelt IR, -cell-outlet pH, -stockline radar.

`state.domain` and `meta.domain` both become `ethylene-steam-cracker-coil`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Woadfen night-shift steam-cracker bypass, not a lyophilizer, not a
corridor, not a tin bath, not a ROV pad, not a potline, not a PEM stack,
not an OR, not a gait lab, not a kiln, not a kraft boiler, not a
membrane row, not a blast furnace, not an ammonia converter).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **cracked TLE inlet
bypass + mixed-header certificate**.

- Trigger: EC-7A TLE inlet bypass 18% open plus unquenched mixed header,
  r_T 48 K, tube 348 C.
- Base rate: <1% — 0.38%/cycle from a bypass-growth MC (furnace-gantry
  visual threshold is designed; tee leakage fitted-style). Visual PASSES
  because the tubes look cool.
- Naive failure: FALSE PERMISSION. PB-EC-7 sees three in-spec tube
  loops, raises +8 K, compressor trip, $2.2M.
- Trajectory edit: put the bypass in `state.fault_context`, make each
  agent's confirm a different tube-side slice of the same mixed-false
  state (cot-in-band, stm-in-band, tle-tube-in-band). Mixed residual is
  readable but policy-treated as condensate-quality-only.

Distinct from stacked-dead-band permission (fragments of one trip vs
wrong-volume sensing), from r32 TMT-spatial-mean (furnace tube max vs
TLE mixed-header), and from r40 Claus furnace-bypass (incinerator CEMS
vs charge-gas TLE duty).

## Neuromorphic Translator

Cycle-1 temporal densification (16 spikes, 5 ticks, 40 ms raster):

| channel | t_rel_ms | amplitude |
|---|---|---|
| cot.mean | 0.310 | 0.55 |
| stm.ratio | 1.120 | 0.62 |
| tle.tube | 2.020 | 0.54 |
| mix.t | 3.160 | 0.76 |
| cot.mean | 4.140 | 0.51 |
| mix.t | 4.820 | 0.79 |
| stm.ratio | 5.340 | 0.59 |
| tle.mix.high | 6.504 | 1.42 |
| tle.tube.in_band | 6.692 | 1.15 |
| stm.ratio | 6.910 | 0.63 |
| ctrl.gate | 7.198 | 1.09 |
| mix.t | 8.840 | 0.47 |
| cot.mean | 10.720 | 0.81 |
| stm.ratio | 13.020 | 0.46 |
| tle.tube | 18.500 | 0.43 |
| ctrl.gate | 26.160 | 0.85 |

Race: mixed residual 6.504 vs tube-in-band 6.692 (188 us) inside 500 us;
stm.ratio 6.910 is the third channel in-window. Winner/loser flip: reversing
188 us reshuffles PB-EC-7 triage; floors still MODIFY. Refractory held
(cycle-1 min same-channel gap 1.570 ms on stm.ratio 6.910-5.340; mix
4.820-3.160 = 1.660; cot 4.140-0.310 = 3.830). Adaptation: mix
0.76->0.79->1.42->0.47; cot 0.55->0.51->0.81; stm 0.62->0.59->0.63.

Raster cycle-1 seed: 40 ms, 160 neurons, 8.0 Hz, 51 spikes, 1173 pJ, third
factor acetylcholine tau_e 0.92 s. Single scar edge only — cycle 2 must
add the second and third edges.

Ticks 1–5 at 4560, 6504, 7198, 5.6e6, 468e6 us; heads not yet the final
-0.17 (missing the 1.4 h and 4.2 h ticks).

Distillation value this cycle: tube-side confirms as a permission code
that is not a mixed-true TLE-duty code.

## Trajectory Builder

Cycle-1 hardened object: domain ethylene-steam-cracker-coil, tail cracked
TLE bypass, 16 spikes, 5 ticks, MODIFY with numeric floor, raster+gate_snn
present, sim_or_real=designed, rights stamp on record and meta, no thought
keys. Still missing (and therefore not the publishable line): millisecond
sub-variant, night-shift tail, second and third scar edges,
delayed screen trip as PRIMARY terminal, contrast ACCEPT episode,
ticks 6–7, spikes 17–26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 500 us window; refractory
  >= 0.8 ms; rationale quotes 18 K / 0.8 t/h; domain named;
  gate_snn.decision MODIFY.
- checks deferred to cycle 2: triple-edge scar, second tail, second domain
  constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5 ticks,
  +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to batch-r45.jsonl.

Cycle-1 spike count: __C1_SPIKES__.

---

# CYCLE 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): steam-ratio probe at +5.6 s stays
   bypass-true (|dT| 11 >= 8) — mixed-header-plus-bypass, not true
   TLE-duty. Bypass stays locked. Coked cone discovered during the lock.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +4.2 h
   suction-screen trip from the pre-t0 TLE-cone fragment; 14 h outage;
   $1.48M. The 16 min pre-t0 bypass is the mechanism. Correct gate, cell
   still fails.
3. Deepened `proposed_action.evidence` with units: r_T 48 K,
   tube 348 C, COT 842 C, steam/HC 0.52, missing steam 4.2 t/h,
   race 188 us.
4. Tightened rationale to the numeric floor do not raise while r_T > 18 K
   AND missing steam > 0.8 t/h, plus probe bands >= 8 vs <= 2 K,
   plus HITL 7.8 min bypass-LOTO rule.

Reward retargeted to total -0.17 so the delayed fail is the inflection
(t_us 15120000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** Two-shell
   probe 5.6 s / +0.04 is not a universal number. A millisecond TLE
   will over-move a healthy mixed header. Diversity Enforcer must inject
   the physical-constraints sub-variant this cycle.
2. **major — only one tail class.** Bypass growth is accidental
   infrastructure. A disjoint human-intent tail is still required
   (night-shift TLE-tube forgery is the open cell).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r14
   item 4 is not discharged until three go-edges exist and pair rollback
   is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on a
   true TLE-duty window the record teaches "never raise". Add +3 d sister-cell
   contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 7.8 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **millisecond-furnace / small TLE volume** on a sister
residence-time class.

What it expands: two-shell TLE (cycle 1) -> millisecond TLE.
Volume 0.30x. Steam-bump gain 3.1x.
The 5.6 s +0.04 pulse moves even a HEALTHY millisecond mixed header 9 K,
inside the bypass-looking band. Required probe: 18 s at +0.012
(bypass |dT| 10 K, healthy 1.4 K).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace
ethylene-steam-cracker-coil; it changes which probe table is legal.
`future_outcome.subvariant_constraint` carries the refit. Jaccard opening
stays the Woadfen 16-coil sentence; millisecond-TLE is additive, not a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**night-shift forged TLE-tube CSV**.

- Trigger: shift lead, 03:06, posts a historian export showing
  tube-outlet = 348.0 C at t = 1.1 h to clear a conversion catchup slot.
- Base rate: ~0.32% of Sunday-night cycles (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the raise on the forged confirm
  and ignores live r_T. Compressor trip plus a data-integrity write-up.
- Fence: forged log quantized at 1.0 K (SCADA screenshot rounding); plant
  historian is 0.1 K (10 bins). Live r_T is 48 K and mixed is 396 C
  at the claimed TLE-true, which no live healthy TLE produces.
  Freeze-window overlap with the 16 min bypass.
- Trajectory edit: governance CR-E-4507 mandates native 0.1 K CSV
  exports; the contrast ACCEPT still requires live r_T, not a CSV.

Distinct from cycle-1 bypass (accidental tee vs deliberate deception)
and from the millisecond sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 26.160 ms: steam.probe 5600.0, mix.t 5688.4 (adapt
  1.42->0.41), tle.tube.in_band 5772.6 (1.15->0.35), human.ratify 468000.0,
  bypass.lock 468900.0, cone.attack 469700.0, cot.mean
  5040000.0, mix.t 5040720.0, stm.ratio 5041480.0, screen.trip
  15120000.0. Primary train 16 -> 26. Still one key, still sorted,
  refractory held.
- +2 ticks (5 -> 7) at 5_040_000_000 us (true TLE duty) and
  15_120_000_000 us (screen trip). Heads now 0.08, -0.37, -0.10, 0.14,
  0.08; total -0.17. Inflection is the last tick.
- Contrast train 8 events, own race 190 us, ACCEPT.
- Triple-edge third factor: three tube-healthy-go edges, tau_e 0.92 s = 920 ms,
  trace __AUX_TRACE__, eta __AUX_ETA1__ / __AUX_ETA2__ / __AUX_ETA3__,
  weights 0.49->0.25, 0.43->0.22, 0.40->0.21. Raster excerpt unchanged
  (decision window is still 40 ms) and remains sorted with unique
  neuron_ids (same-neuron >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 188 us would only
reorder triage; r_T floors still MODIFY. Contrast flip of 190 us
similarly cannot turn a healthy TLE into a cracked bypass.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.17; `spike_events` globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20–50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=45,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive.

Densification delta: +1 domain sub-variant (millisecond TLE), +1 tail
(night-shift forgery), +10 spikes (16->26), +2 ticks (5->7), +1 contrast
train with own race, +2 delayed side-effects, +1 triple-edge scar with
pair-rollback-fails, +1 HITL ratify, +1 surprise (TLE-cone coke is
the screen-trip mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r45.jsonl):

```json
__FINAL_JSONL__
```

Validation receipt (final): checks passed / fixed as reported by
build_r45.py self-validate (check_jsonl, raster_status, verify_record_execution,
spike_probe --strict).
"""
    text = (
        text.replace("__C1_SPIKES__", str(len(c1_spikes)))
        .replace("__AUX_TRACE__", f"{math.exp(-DELAY_S / TAU_E_S):.5f}")
        .replace("__AUX_ETA1__", f"{0.24 / math.exp(-DELAY_S / TAU_E_S):.5f}")
        .replace("__AUX_ETA2__", f"{0.21 / math.exp(-DELAY_S / TAU_E_S):.5f}")
        .replace("__AUX_ETA3__", f"{0.19 / math.exp(-DELAY_S / TAU_E_S):.5f}")
        .replace("__FINAL_JSONL__", line)
    )
    (OUT / "swarm-transcript-r45.md").write_text(text)
    return text
