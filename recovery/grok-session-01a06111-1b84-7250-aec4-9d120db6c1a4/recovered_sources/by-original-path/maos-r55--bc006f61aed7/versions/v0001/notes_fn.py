def write_notes(rec, aux, pipeline_receipt):
    gap, gap_ch = min_same_channel_gap(rec["spike_events"])
    notes = """# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 55

Factory: multi-agent-ouroboros-swarm. One scenario (ZB), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r55.jsonl. Full labeled transcript:
swarm-transcript-r55.md. Quota Q=1. Record id maos-r55-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Nothing under outputs/raw/ was touched.

ORCHESTRATION NOTE: dispatched AS round 55 of the 2026-09-02-final-heavy
window. Writes are create-only under /tmp/maos-r55/. Prior context read for
gap targeting and de-collision: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, and staged r14–r54 batches plus in-flight
r57 SIPHONWOLD builder-only (paper-machine-dryer-section) and empty r56.
Re-censused immediately before emit. r50 GAUZEFELL nitric Ostwald, r51
OSMOLITH seawater-RO, r52 PUSHERFELL coke-oven, r53 CREELWOLD carbon-fiber
oxidation, r54 GIBBSQUERN gibbsite autoclave. SWRO was taken by r51 so
this round locked hot-strip finishing instead. Explicitly avoided cloning
LYOSHIELD, CINDERWICK, TRIAD / Meridian, QUILLFORGE, NIGHTWELL, FERRICLEAVE,
CASSITER, OXBOWREEL / MURENA, REDHALL, SEEDLATCH, STRIAFOIL, PROTONIL,
TORSIONKEY, ORRIS, WHORLSPAR, IONSPATE, SKULLGATE, CALXION, MAGNORIL,
GORSEFLUE, SODASHARD, CLINKERFELL, LINTELPLY, KAOTHARN, TREADNOLL, ANOLITH,
DRUMWROTH, RIMEBRAID, PITCHSTAITH, BRIMVAULT, BOGIRON, NITROSTAITH,
NITREVAULT, CHROMLOOP, RUNNELGATE, ETHYNWOLD, SPARKHOLT, DIPLEGAR,
OLEUMWEIR, SKARVOLT, GOBSPALL, GOBWOLD, PUSHERFELL, CREELWOLD, LIXIVQUERN,
OSMOLITH, GAUZEFELL, GIBBSQUERN, SIPHONWOLD, OSMOQUAY, VANTIS-CADENCE-AEGIS,
THERMION, OKTAVE, STARLING, VERDIGRIS. Plant is invented LOOPERQUAY /
Roughmere Strip HSM-5.

## What this round produced

Scenario ZB — "LOOPERQUAY / Roughmere Strip HSM-5": a 7-stand finishing
mill at 2.02 mm / 12.4 m/s. Three heterogeneous, individually-correct
agents — SPEED (tachometer), THICK (X-ray mean), TEMP (finishing
pyrometer) — each report their local loop in-spec. The conjunction is
not a steel-true gauge certificate. A 13 min cracked descaler header
on stand F-5 left scale on the strip. SPEED reads 12.4 m/s inside
11.8-13.0 (mill-true). THICK is 2.02 mm inside 1.95-2.10 (X-ray-true
of scale-plus-steel). TEMP is 890 C inside 870-920 (scale-surface-true).
Laser-vs-X-ray residual r_h is 0.22 mm (healthy < 0.04; hold if > 0.10)
but is policy-treated as a noisy-laser tag unless X-ray also trips
(2014 noisy shadow laser). The coordination-failure CLASS is new to
this factory: SCALE-MASK CERTIFICATE OF A STEEL-TRUE GAUGE. Completes a
different family than r01-r04 and staged r14-r54. Distinct from r16
stator weld, r23 slot-die stripe, r29 caster mold-level, r42 blast
furnace, r49 EAF panel, r51 SWRO mixed-header, r52 coke-oven wall-mean,
r57 paper-machine dryer (claimed). Here every agent is correct, the
X-ray is looking at scale-plus-steel, and the playbook's three confirms
are not a steel-true gauge certificate.

The gate is a correct MODIFY (numeric floor: do not raise mill speed
while r_h > 0.10 mm AND missing descaler > 1.2 L/s). TG-HSM-5 strips
PB-HSM-5's raise, holds 12.4 m/s, runs a 5.4 s speed-cut probe -3%
(scaled bar keeps |d-gauge| 0.11 >= 0.08; healthy would move <= 0.02),
and keeps F-5 locked after a 6.8 min stand-LOTO human ratify. Immediate
cobble is avoided (0 from the draft). The PRIMARY episode nonetheless
FAILS: 13 min of unmonitored pre-t0 descaler crack had already scored
the work-roll. Roll spall at +2.6 h; 9 h outage; $1.41M designed.
Reward total -0.16 with process heads honest and world loss un-netted.

Triple-edge scar (NOTES-r14 item 4): mill.v -> raise
(0.16 commissioned -> 0.48 at illusion -> 0.24 after ACh-gated
depression) AND xray.in_band -> raise (0.14 -> 0.43 -> 0.22) AND
pyro.t -> raise (0.13 -> 0.40 -> 0.20). Eligibility trace
e^{-0.84/0.92} = __TRACE__; eta __ETA1__ / __ETA2__ /
__ETA3__; dw -0.240 / -0.210 / -0.200. Partial rollback of any pair
leaves the third at 0.48 / 0.43 / 0.40, all > 0.30 fire threshold —
fitted to fail. Coordinated depression of all three is the cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **hot-strip-mill-finishing** — justified novel
  subdomain of industrial-process / hot-strip rolling, unused across
  staged r14-r54. Not warehouse-amr, aerial-swarm, district-heating,
  lyophilization, civic dosing, float-glass, underwater-rov, potline,
  CZ-pull, slot-die, PEM, wind pitch, surgical-assist, fiber-draw,
  kraft-recovery, caster, humanoid, VIM, SMR, cement kiln, autoclave,
  ORC, tire press, chlor-alkali, delayed-coker, LNG MCHE, Claus,
  ammonia, blast furnace, HDPE loop, Kaplan, steam-cracker, FCC,
  sulfuric-contact, EAF, glass IS, coke-oven, carbon-fiber oxidation,
  gibbsite autoclave, seawater-RO (r51), nitric Ostwald (r50), or
  paper-machine dryer (r57 claimed). autonomous-driving,
  grid-inspection, bioreactor-perfusion left unused.
- Cycle-1 tail: cracked descaler header + scale-mask certificate.
  Stand-side visual PASSES (no walkway puddle). Fitted-style base
  rate 0.33%/cycle. Naive = FALSE PERMISSION.
- Cycle-2 domain sub-variant: 0.8 mm thin-gauge, 0.40x thickness,
  2.5x speed-cut gain; 5.4 s / -3% 2 mm pulse over-moves a HEALTHY
  thin-gauge X-ray to 0.09 mm; probe must move to 14 s / -1%.
- Cycle-2 tail: night-shift forged X-ray CSV at 0.05 mm quantization
  vs plant 0.005 mm (10 bins) plus live r_h 0.22 mm. Human-intent
  class, disjoint from cycle 1's accidental descaler crack. Base rate
  ~0.28% of Sunday-night cycles, DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+3 d sister mill) with its own 176 us
  race (demand vs scale-clear) and ACCEPT of the raise the primary
  MODIFIED away.
- Learned-weight provenance on THREE edges with pair-rollback-fails.
- HITL stand-LOTO ratify 6.8 min (gap 4 partial; sim_or_real stays
  designed).
- Governance CR-H-5512 prices retire-vs-probe-vs-status-quo and mandates
  native 0.005 mm CSV exports (the fraud fence).
- Flip-fragility extended to GAUGE-DUTY CERTIFICATE.

## Self-critique of this round's batch

### Strengths
- Headline class is mechanistically tight: three locally-true loops
  live on scale-plus-steel. Conjunction is not steel-true gauge.
- Negative-result honesty: correct gate, mill still fails. Total -0.16.
- Triple-edge scar is load-bearing; pair rollback fails at 0.30.
- Contrast ACCEPT prevents "never raise" as the lesson.
- Distinct from r16 weld, r23 slot-die, r29 caster, r51 SWRO header,
  r52 coke-oven wall, r57 paper dryer.

### Weaknesses (honest)
- Probe bands, 0.33%/cycle descaler-crack rate, $1.41M / $2.12M,
  6.8 min walk latency, and 0.28% night-shift rate are DESIGNED and
  flagged.
- Work-roll scoring model is a designed 13 min mapping; no full mill
  FEM shipped.
- HITL is ratification latency, not sim_or_real=hil.
- Cross-record arc is not discharged; CR-H-5512 is a hook.

### Realism of noise / latencies
Ladder: 176 us race / 176 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap __GAP__ ms on __GAP_CH__) / 500 us
race window / 694 us gate latency / 20 ms bus epoch / 40 ms raster /
5.4 s probe / 6.8 min HITL / 3 min naive raise-ramp / 13 min pre-t0
descaler crack / 0.9 h stand lineup / 2.6 h roll spall / +3 d contrast
/ +21 d governance. Adaptation on mill.v (0.52->0.50->0.64->0.82->0.30),
scale.h (0.78->0.81->1.44->0.46->0.40->0.28), xray.h (0.61->0.58->0.45->0.26),
pyro.t (0.53->0.42).

### Value for SNN distillation
- SCALE MASK = THREE CORRECT LOOPS, WRONG VOLUME.
- LASER-VS-X-RAY CHANNEL that policy treated as noisy-laser-only.
- REVERSIBLE PROBE that moves X-ray iff scale is present.
- TRIPLE-EDGE ELIGIBILITY; pair rollback fails.
- CRITIC HEAD that books a process-correct MODIFY against later world
  loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum __TOTAL__
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.46 reconciles independently.
- spike_events: primary __NSPIKES__ events, globally non-decreasing,
  min same-channel gap __GAP__ ms >= 0.8 ms, 3 channels inside
  race_window_us 500 (scale.h.high 6.520, xray.in_band 6.696, mill.v 6.940).
  Contrast 8 events, own race.
- Sidecars: raster spikes 51 == round(160 x 8.0 x 0.040); energy 1173 pJ /
  0.001173 uJ at 23 pJ/spike; excerpt 16 events inside [0, 40000] us;
  third factor tau 0.92 s; gate_snn pools 42/15/4; decision MODIFY.
- Pipeline: __PIPELINE__

## Novel coverage
The coordination-failure CLASS (scale-mask certificate of a steel-true
gauge), the domain (hot-strip finishing mill), the speed-cut probe, the
triple-edge scar with pair-rollback-fails, the primary negative-result,
the HITL stand-LOTO ratify, the thin-gauge probe-duration refit, and the
night-shift 10-bin quantization fence are absent from prior committed
ouroboros rounds and from staged r14-r54. Repeated scaffolds discounted
(same-gate contrast, governance pricing, flip-fragility series,
negative-result primary). Adjacent thickness/mean rounds (r23 slot-die,
r29 caster, r51 SWRO header) share industrial-process scaffolding but
not finishing-mill scale-vs-steel physics.

__NOVEL_LINE__

## What ROUND 56 should add
1. FIT THE DESIGNED CONSTANTS: descaler-crack arrival, probe error bands,
   work-roll scoring kinetics, night-shift claim process.
2. HIL PROVENANCE CELL: stand-LOTO ratify as state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-H-5512's residual alarm ignite the next round.
4. Domain candidates (de-collided): autonomous-driving; grid-inspection;
   bioreactor-perfusion; alkaline-water-electrolysis; Francis turbine.
   AVOID hot-strip-mill-finishing (now used), seawater-ro-desalination,
   coke-oven-battery-heating, carbon-fiber-oxidation-oven,
   gibbsite-autoclave-digestion, nitric-acid-ostwald-oxidation,
   paper-machine-dryer-section, and any LYOSHIELD / OSMOLITH / GAUZEFELL /
   PUSHERFELL / CREELWOLD / GIBBSQUERN / SIPHONWOLD / LOOPERQUAY plant.
"""
    notes = (
        notes.replace("__TRACE__", f"{aux['trace']:.5f}")
        .replace("__ETA1__", f"{aux['eta1']:.5f}")
        .replace("__ETA2__", f"{aux['eta2']:.5f}")
        .replace("__ETA3__", f"{aux['eta3']:.5f}")
        .replace("__GAP__", f"{gap:.3f}")
        .replace("__GAP_CH__", str(gap_ch))
        .replace("__TOTAL__", str(rec["reward_components"]["total"]))
        .replace("__NSPIKES__", str(len(rec["spike_events"])))
        .replace("__PIPELINE__", pipeline_receipt)
        .replace("__NOVEL_LINE__", NOVEL_LINE)
    )
    (OUT / "NOTES-r55.md").write_text(notes)
    return notes
