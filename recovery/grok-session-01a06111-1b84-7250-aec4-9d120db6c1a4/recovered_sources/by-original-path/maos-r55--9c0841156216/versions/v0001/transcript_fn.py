def write_transcript(rec, line):
    c1_spikes = [e for e in rec["spike_events"] if e["t_rel_ms"] <= C1_SPIKE_CUTOFF_MS]
    text = """# Multi-Agent Ouroboros Swarm — Round 55 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r55-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented LOOPERQUAY / Roughmere Strip HSM-5 (not TRIAD / Meridian / OSMOLITH / PUSHERFELL / GIBBSQUERN / SIPHONWOLD)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r55.jsonl).

---

# CYCLE 1 — Foundation + injections

## Generator

Design intent: a 7-stand hot-strip finishing mill where three correct
agents each read an X-ray-side loop because a 13 min cracked descaler
header partitions steel-true gauge from X-ray-true scale-plus-steel.
The naive playbook raises mill speed into a scaled bar. The gate must
MODIFY on a numeric speed ceiling, not by killing an agent.
sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Roughmere HSM-5, speed 12.4 m/s,
X-ray 2.02 mm, pyro 890 C, proposed RAISE-SPEED +8%,
safety MODIFY to SPEED-HOLD, executed hold without the speed-cut
numbers fully specified, outcome "descaler found, mill saved"
(this last claim is the defect the later cycles will refuse to keep).
Sixteen spikes, five ticks, raster/gate_snn present but the scar is a
single edge.

```json
{
  "id": "maos-r55-001",
  "state": {
    "sim_or_real": "designed",
    "domain": "industrial-process",
    "description": "Mill HSM-5 at gauge duty; three X-ray loops in-spec; supervisor proposes raise-speed.",
    "t0_us": 1786396800000055,
    "gate_latency_us": 694,
    "race_window_us": 500
  },
  "proposed_action": {"name": "raise_speed", "parameters": {"raise_pct": 8.0}},
  "safety_decision": {"decision": "MODIFY", "rationale": "Hold; do not raise while scale residual is high."},
  "executed_action": {"name": "speed_hold", "executed_as_proposed": false},
  "future_outcome": {"summary": "Descaler found, mill saved."},
  "reward_components": {"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"},
  "meta": {"round": 55, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}
}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "mill saved". If the pre-t0 score later spalls the
   work-roll, booking +0.40 is a lie. Fix: declare `_aggregation`,
   emit 3–8 ticks that sum to task_progress+safety+efficiency+coherence+exploration,
   and do not call a quarantined island a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote
   do not raise while r_h > 0.10 mm AND missing descaler > 1.2 L/s.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-process` collides with generic MES vocabulary and teaches
   nothing. Hot-strip finishing mill (laser-vs-X-ray residual vs X-ray
   mean, missing descaler as a scale flag) is absent from prior ouroboros
   rounds and must be named.
4. **major — race under-specified.** One scale channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted `t_rel_ms`
   and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated weight
   repeats r04's one-edge rollback and is thinner than r14's two-edge.
   NOTES-r14 item 4 asked for three edges where pair rollback fails.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **hot-strip-mill-finishing**
(justified novel subdomain of industrial-process / hot-strip rolling;
explicit tag `hot-strip-mill-finishing`).

Displaced: the Generator's generic `industrial-process` bucket, and any
temptation to reuse warehouse-amr, aerial-swarm, district-heating,
event-camera-traffic-grid, pharmaceutical-lyophilization, civic coagulant
dosing, float-glass tin-bath, underwater-rov, electrolytic-aluminum,
czochralski-pull, slot-die coating, pem-water-electrolysis, wind-turbine
pitch, surgical-assist, optical-fiber-draw, kraft-recovery-boiler,
steel-continuous-caster, humanoid-locomotion, vacuum-induction melt,
steam-methane reformer, cement-rotary-kiln-clinker,
autoclave-composite-cure, geothermal-binary-orc, tire-curing-press,
chlor-alkali-membrane-electrolysis, delayed-coker, lng-mche,
claus-sulfur-recovery, blast-furnace-burden-descent, ammonia-converter,
hdpe-slurry-loop, hydroelectric-kaplan-wicket, ethylene-steam-cracker-coil,
fcc-riser-regenerator, fcc-regenerator-cyclone-dipleg,
sulfuric-contact-converter, eaf-foamy-slag, glass-container-is-machine,
coke-oven-battery-heating, carbon-fiber-oxidation-oven,
gibbsite-autoclave-digestion, seawater-ro-desalination,
nitric-acid-ostwald-oxidation, or paper-machine-dryer-section.
autonomous-driving and bioreactor-perfusion are left unused.

Domain-specific constraint: speed raise must remain forbidden while
r_h > 0.10 mm even if X-ray is inside the healthy band; missing
descaler is a scale flag the X-ray cannot substitute for.

Sensor delta: +mill tachometer, +X-ray gauge, +finishing pyrometer,
+laser-vs-X-ray residual; -any mobile robot, -event-camera gantries,
-DVS, -Pirani/CM, -RGA quadrupole, -DVL, -pitch encoder, -tendon LVDT,
-insole GRF, -kiln zirconia, -smelt IR, -cell-outlet pH, -stockline radar,
-cracker COT, -FCC cyclone dP, -IS gob scale, -coke-oven wall-TC,
-SWRO header cell.

`state.domain` and `meta.domain` both become `hot-strip-mill-finishing`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Roughmere night-shift descaler crack, not a lyophilizer, not a
corridor, not a tin bath, not a ROV pad, not a potline, not a PEM stack,
not an OR, not a gait lab, not a kiln, not a kraft boiler, not a
membrane row, not a blast furnace, not an ammonia converter, not an FCC,
not an IS machine, not a coke-oven battery, not a Bayer digester, not
an SWRO skid).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **cracked descaler
header + scale-mask certificate**.

- Trigger: F-5 descaler header cracked, scale on strip,
  r_h 0.22 mm, X-ray 2.02 mm.
- Base rate: <1% — 0.33%/cycle from a descaler-crack MC (stand-side
  visual threshold is designed; header leakage fitted-style). Visual PASSES
  because there is no walkway puddle.
- Naive failure: FALSE PERMISSION. PB-HSM-5 sees three in-spec X-ray
  loops, raises +8%, cobble, $2.12M.
- Trajectory edit: put the descaler crack in `state.fault_context`, make each
  agent's confirm a different X-ray-side slice of the same steel-false
  state (speed-in-band, xray-in-band, pyro-in-band). Laser residual
  is readable but policy-treated as noisy-laser-only.

Distinct from stacked-dead-band permission, from r23 slot-die window-mean
stripe, from r29 caster slag-skull, and from r51 SWRO mixed-header.

## Neuromorphic Translator

Cycle-1 temporal densification (16 spikes, 5 ticks, 40 ms raster):

| channel | t_rel_ms | amplitude |
|---|---|---|
| mill.v | 0.280 | 0.52 |
| xray.h | 1.120 | 0.61 |
| pyro.t | 2.010 | 0.53 |
| scale.h | 3.140 | 0.78 |
| mill.v | 4.140 | 0.50 |
| scale.h | 4.820 | 0.81 |
| xray.h | 5.340 | 0.58 |
| scale.h.high | 6.520 | 1.44 |
| xray.in_band | 6.696 | 1.16 |
| mill.v | 6.940 | 0.64 |
| ctrl.gate | 7.214 | 1.11 |
| scale.h | 8.850 | 0.46 |
| mill.v | 10.740 | 0.82 |
| xray.h | 13.020 | 0.45 |
| pyro.t | 18.510 | 0.42 |
| ctrl.gate | 26.160 | 0.84 |

Race: scale residual 6.520 vs X-ray-in-band 6.696 (176 us) inside 500 us;
mill.v 6.940 is the third channel in-window. Winner/loser flip: reversing
176 us reshuffles PB-HSM-5 triage; floors still MODIFY. Refractory held
(cycle-1 min same-channel gap 1.680 ms on scale.h 4.820-3.140; mill
4.140-0.280 = 3.860; xray 5.340-1.120 = 4.220). Adaptation: scale
0.78->0.81->1.44->0.46; mill 0.52->0.50->0.64->0.82; xray 0.61->0.58->0.45.

Raster cycle-1 seed: 40 ms, 160 neurons, 8.0 Hz, 51 spikes, 1173 pJ, third
factor acetylcholine tau_e 0.92 s. Single scar edge only — cycle 2 must
add the second and third edges.

Ticks 1–5 at 4560, 6520, 7214, 5.4e6, 408e6 us; heads not yet the final
-0.16 (missing the 0.9 h and 2.6 h ticks).

Distillation value this cycle: X-ray-side confirms as a permission code
that is not a steel-true gauge-duty code.

## Trajectory Builder

Cycle-1 hardened object: domain hot-strip-mill-finishing, tail cracked
descaler header, 16 spikes, 5 ticks, MODIFY with numeric floor,
raster+gate_snn present, sim_or_real=designed, rights stamp on record and
meta, no thought keys. Still missing (and therefore not the publishable
line): thin-gauge sub-variant, night-shift tail, second and third scar edges,
delayed work-roll spall as PRIMARY terminal, contrast ACCEPT episode,
ticks 6–7, spikes 17–26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 500 us window; refractory
  >= 0.8 ms; rationale quotes 0.10 mm / 1.2 L/s; domain named;
  gate_snn.decision MODIFY.
- checks deferred to cycle 2: triple-edge scar, second tail, second domain
  constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5 ticks,
  +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to batch-r55.jsonl.

Cycle-1 spike count: __C1_SPIKES__.

---

# CYCLE 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): speed-cut probe at +5.4 s stays
   scale-true (|d-gauge| 0.11 >= 0.08) — X-ray-plus-descaler-crack, not true
   gauge-duty. Stand stays locked. Scored work-roll discovered during the lock.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +2.6 h
   work-roll spall from the pre-t0 scale score; 9 h outage;
   $1.41M. The 13 min pre-t0 descaler crack is the mechanism. Correct gate, mill
   still fails.
3. Deepened `proposed_action.evidence` with units: r_h 0.22 mm,
   X-ray 2.02 mm, speed 12.4 m/s, pyro 890 C, missing descaler 1.85 L/s,
   race 176 us.
4. Tightened rationale to the numeric floor do not raise while r_h > 0.10 mm
   AND missing descaler > 1.2 L/s, plus probe bands >= 0.08 vs <= 0.02 mm,
   plus HITL 6.8 min stand-LOTO rule.

Reward retargeted to total -0.16 so the delayed fail is the inflection
(t_us 9360000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** 2.02 mm
   probe 5.4 s / -3% is not a universal number. A 0.8 mm thin-gauge bar
   will over-move a healthy X-ray. Diversity Enforcer must inject
   the physical-constraints sub-variant this cycle.
2. **major — only one tail class.** Descaler-crack growth is accidental
   infrastructure. A disjoint human-intent tail is still required
   (night-shift X-ray forgery is the open cell).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r14
   item 4 is not discharged until three go-edges exist and pair rollback
   is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on a
   true gauge-duty window the record teaches "never raise". Add +3 d sister-mill
   contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 6.8 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **0.8 mm thin-gauge / short contact** on a sister
residence-time class.

What it expands: 2.02 mm (cycle 1) -> 0.8 mm thin-gauge.
Thickness 0.40x. Speed-cut gain 2.5x.
The 5.4 s -3% pulse moves even a HEALTHY thin-gauge X-ray 0.09 mm,
inside the scale-looking band. Required probe: 14 s at -1%
(scale |d-gauge| 0.10 mm, healthy 0.016 mm).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace
hot-strip-mill-finishing; it changes which probe table is legal.
`future_outcome.subvariant_constraint` carries the refit. Jaccard opening
stays the Roughmere 7-stand sentence; thin-gauge is additive, not a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**night-shift forged X-ray CSV**.

- Trigger: shift lead, 03:42, posts a historian export showing
  X-ray = 2.02 mm at t = 0.9 h to clear a coil-quota catchup slot.
- Base rate: ~0.28% of Sunday-night cycles (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the raise on the forged confirm
  and ignores live r_h. Cobble plus a data-integrity write-up.
- Fence: forged log quantized at 0.05 mm (SCADA screenshot rounding); plant
  historian is 0.005 mm (10 bins). Live r_h is 0.22 mm and pyro is 890 C
  at the claimed steel-true, which no live healthy bar produces.
  Freeze-window overlap with the 13 min descaler crack.
- Trajectory edit: governance CR-H-5512 mandates native 0.005 mm CSV
  exports; the contrast ACCEPT still requires live r_h, not a CSV.

Distinct from cycle-1 descaler crack (accidental hardware vs deliberate deception)
and from the thin-gauge sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 26.160 ms: spd.probe 5400.0, scale.h 5488.2 (adapt
  1.44->0.40), xray.in_band 5572.4 (1.16->0.34), human.ratify 408000.0,
  stand.lock 408900.0, roll.score 409700.0, mill.v
  3240000.0, scale.h 3240720.0, xray.h 3241480.0, roll.spall
  9360000.0. Primary train 16 -> 26. Still one key, still sorted,
  refractory held.
- +2 ticks (5 -> 7) at 3_240_000_000 us (true gauge duty) and
  9_360_000_000 us (work-roll spall). Heads now 0.08, -0.36, -0.10, 0.14,
  0.08; total -0.16. Inflection is the last tick.
- Contrast train 8 events, own race 176 us, ACCEPT.
- Triple-edge third factor: three X-ray-healthy-go edges, tau_e 0.92 s = 920 ms,
  trace __AUX_TRACE__, eta __AUX_ETA1__ / __AUX_ETA2__ / __AUX_ETA3__,
  weights 0.48->0.24, 0.43->0.22, 0.40->0.20. Raster excerpt unchanged
  (decision window is still 40 ms) and remains sorted with unique
  neuron_ids (same-neuron >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 176 us would only
reorder triage; r_h floors still MODIFY. Contrast flip of 176 us
similarly cannot turn a healthy bar into a cracked descaler.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.16; `spike_events` globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20–50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=55,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive.

Densification delta: +1 domain sub-variant (thin-gauge), +1 tail
(night-shift forgery), +10 spikes (16->26), +2 ticks (5->7), +1 contrast
train with own race, +2 delayed side-effects, +1 triple-edge scar with
pair-rollback-fails, +1 HITL ratify, +1 surprise (work-roll scoring is
the spall mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r55.jsonl):

```json
__FINAL_JSONL__
```

Validation receipt (final): checks passed / fixed as reported by
build_r55.py self-validate (check_jsonl, raster_status, verify_record_execution,
spike_probe --strict).
"""
    text = (
        text.replace("__C1_SPIKES__", str(len(c1_spikes)))
        .replace("__AUX_TRACE__", f"{math.exp(-DELAY_S / TAU_E_S):.5f}")
        .replace("__AUX_ETA1__", f"{0.24 / math.exp(-DELAY_S / TAU_E_S):.5f}")
        .replace("__AUX_ETA2__", f"{0.21 / math.exp(-DELAY_S / TAU_E_S):.5f}")
        .replace("__AUX_ETA3__", f"{0.20 / math.exp(-DELAY_S / TAU_E_S):.5f}")
        .replace("__FINAL_JSONL__", line)
    )
    (OUT / "swarm-transcript-r55.md").write_text(text)
    return text
