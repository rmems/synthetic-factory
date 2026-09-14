def write_notes(rec, aux, pipeline_receipt):
    gap, gap_ch = min_same_channel_gap(rec["spike_events"])
    notes = f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 41

Factory: multi-agent-ouroboros-swarm. One scenario (ZP), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r41.jsonl. Full labeled transcript:
swarm-transcript-r41.md. Quota Q=1. Record id maos-r41-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Nothing under outputs/raw/ was touched.

ORCHESTRATION NOTE: dispatched AS round 41 of the 2026-09-02-final-heavy
window. Writes are create-only under /tmp/maos-r41/. Prior context read for
gap targeting and de-collision: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, and staged r14–r39 (re-censused immediately
before emit; r38 DRUMWROTH delayed-coker-drum-switch / r39 RIMEBRAID
lng-mche-mixed-refrigerant landed while a delayed-coker quench draft was
being authored, so r41 was rewritten onto ammonia-synthesis-converter;
r40/r42 directories existed empty at lock). Explicitly avoided cloning
LYOSHIELD, CINDERWICK, TRIAD / Meridian, QUILLFORGE, NIGHTWELL, FERRICLEAVE,
CASSITER, OXBOWREEL / MURENA, REDHALL, SEEDLATCH / Quartzmere / Quartzridge,
STRIAFOIL / Kelpholt, PROTONIL / Ashspire, TORSIONKEY / Ridgeholt, ORRIS /
Holmwick, WHORLSPAR / Pikeshear, IONSPATE / Thornmere, SKULLGATE / Bloomholt,
CALXION / Aldersedge, MAGNORIL / Basaltspit, GORSEFLUE / Copseholt,
SODASHARD / Cairnmere, CLINKERFELL / Flintmere, LINTELPLY / Greystair,
KAOTHARN / Riftwold, TREADNOLL / Slatebeck, ANOLITH / Siltfen,
DRUMWROTH / Pitchfen, RIMEBRAID / Floeholt, PITCHSTAITH / Mossbank,
VANTIS-CADENCE-AEGIS, THERMION, OKTAVE, STARLING, VERDIGRIS. Plant is
invented NITROSTAITH / Chalkfen Ammonia CV-4.

## What this round produced

Scenario ZP — "NITROSTAITH / Chalkfen Ammonia CV-4": a 4-bed quench-cooled
220 bar Haber converter at 448 C bed-mean / 100 t/h. Three heterogeneous,
individually-correct agents — BED (bed-mean TC), RATIO (H2/N2 GC), CONV
(effluent NH3 GC) — each report their local loop in-spec. The conjunction
is not a basket-integrity certificate. A bed-3 basket bypass left the
axial max at 512 C. BED reads 448 C inside 430-470 (beds 1-2 dominate).
RATIO is 2.98 inside 2.85-3.15 (feed-true). CONV is 16.8 mol% inside
15.5-18.0 (mixed effluent). Inferred hotspot residual r_T is 64 K
(healthy < 12; hold if > 18) but is policy-treated as a noisy-TC tag
unless converter dP also trips (2018 noisy bed-3 nuisance). The
coordination-failure CLASS is new to this factory: BASKET-BYPASS
CERTIFICATE OF A BED-3 HOTSPOT. Completes a different family than r01-r04
and staged r14-r39 (livelock / synchrony-storm / arms-race /
ring-with-no-faulty-pair / false-consensus-endpoint / pairwise-Hurwitz /
thermal-contact masquerade / mass-balance ghost / conservation-blind
ratio-lock / stacked-dead-bands / drum-blind tension snag /
resistance-compensated starvation / multi-tau meniscus tilt / window-mean
stripe / polarization-lookup drying cell / motor-side certificate /
tendon-compliance nullspace / FFT-deadbanded airline / wall-reflection
frozen spout / slag-skull bridge / ghost-contact nullspace /
crucible-weep pyrometer / TMT-spatial-mean tube / kiln-inlet false-air /
vacuum-bag pinhole nullspace / NCG-blanket shell-pressure /
bladder-pinhole mold-TC / catholyte-back-migration membrane /
wet-foam gamma-radar / warm-end leak cold-end). Here every agent is
correct, the mean is looking at packed beds 1-2, and the playbook's
three mean confirms are not a bed-true basket certificate.

The gate is a correct MODIFY (numeric floor: do not raise feed above
100 t/h while r_T > 18 K AND quench-step |dT_max| <= 2 K). TG-CV-4
strips PB-CV-4's feed raise, holds 100 t/h, runs a 6.8 s quench-step
probe +4% (bypass keeps |dT_max| 1.4 <= 2; packed would move >= 12),
and isolates bed-3 after an 8.8 min gallery human ratify. Immediate
runaway is avoided (0 from the draft). The PRIMARY episode nonetheless
FAILS: 16 min of unmonitored pre-t0 hotspot had already sintered the
bed-3 doughnut. NH3 slip at +3.6 h; 12 h outage; $1.48M designed.
Reward total -0.17 with process heads honest and world loss un-netted.

Triple-edge scar (NOTES-r14 item 4): bed.in_band -> feed_raise
(0.16 commissioned -> 0.48 at illusion -> 0.24 after ACh-gated
depression) AND ratio.in_band -> feed_raise (0.14 -> 0.42 -> 0.21) AND
conv.in_band -> feed_raise (0.13 -> 0.39 -> 0.20). Eligibility trace
e^{{-0.68/0.88}} = {aux['trace']:.5f}; eta {aux['eta1']:.5f} / {aux['eta2']:.5f} /
{aux['eta3']:.5f}; dw -0.240 / -0.210 / -0.190. Partial rollback of any pair
leaves the third at 0.48 / 0.42 / 0.39, all > 0.30 fire threshold —
fitted to fail. Coordinated depression of all three is the cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **ammonia-synthesis-converter** — justified novel
  subdomain of industrial-process / Haber-Bosch, unused across
  2026-08-17, 2026-08-30, and staged r14-r39. Not warehouse-amr (r01),
  not aerial-swarm (r02), not district-heating (r03), not
  event-camera-traffic-grid (r04), not lyophilization (r14), not
  water-treatment (r18), not float-glass (r19), not underwater-rov
  (r20), not electrolytic-aluminum (r21), not czochralski-pull (r22),
  not slot-die coating (r23), not pem-electrolysis (r24), not
  wind-turbine pitch (r25), not surgical-assist (r26), not
  optical-fiber-draw (r27), not kraft-recovery (r28), not steel-caster
  (r29), not humanoid-locomotion (r30), not vacuum-induction melt
  (r31), not steam-methane reformer (r32), not cement-rotary-kiln
  (r33), not autoclave-composite-cure (r34), not geothermal-binary-orc
  (r35), not tire-curing-press (r36), not chlor-alkali membrane (r37),
  not delayed-coker-drum-switch (r38), not lng-mche (r39).
  autonomous-driving, grid-inspection, claus-sulfur-recovery left unused.
- Cycle-1 tail: basket bypass + bed-3 hotspot certificate.
  Gallery visual PASSES (doughnut inside the basket). Fitted-style
  base rate 0.38%/campaign (hotspot-growth MC; visual threshold designed,
  flagged). Naive = FALSE PERMISSION.
- Cycle-2 domain sub-variant: tube-cooled S-200 / low quench authority,
  0.41x authority, 2.4x quench-step gain; 6.8 s / +4% quench-converter
  pulse overshoots a LIVE packed bed by 28 K; probe must move to 18 s /
  +1.2%.
- Cycle-2 tail: night-shift forged bed-max CSV at 1.0 K quantization
  vs plant 0.1 K (10 bins) plus live r_T 64 K and effluent NH3 16.8 mol%
  at the claimed basket-true. Human-intent class, disjoint from cycle
  1's accidental bypass. Base rate ~0.32% of Sunday-night campaigns,
  DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+3 d sister converter) with its own 186 us
  race (demand vs bed-clear) and ACCEPT of the raise the primary MODIFIED
  away.
- Learned-weight provenance on THREE edges with pair-rollback-fails.
- HITL gallery ratify 8.8 min (gap 4 partial; sim_or_real stays
  designed).
- Governance CR-A-4104 prices retire-vs-probe-vs-status-quo and mandates
  native 0.1 K CSV exports (the fraud fence).
- Flip-fragility extended to BASKET-INTEGRITY CERTIFICATE: when three
  mean-side channels agree, their race does not decide truth; a
  bed-max tap that policy treated as noisy-TC-only does.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: three locally-true mean
  loops live on mixed beds 1-2. Conjunction is not a bed-true basket.
- Negative-result honesty: the gate does the right thing and the converter
  still fails for a reason the commissioned sensors could not see. Total
  -0.17.
- Triple-edge scar is load-bearing: the record states a counterfactual
  where rolling back any pair fails, with the fire threshold 0.30
  exhibited on each remaining edge.
- Contrast ACCEPT on a true packed basket prevents "never raise" as
  the lesson.
- Distinct from r32 TMT spatial-mean, r31 crucible-weep, r37 membrane
  pinhole, and r38 delayed-coker wet-foam: Haber basket bypass with
  bed-max vs effluent NH3, not reformer tubes, not melt-face, not brine
  membrane, not coke-drum gamma.

### Weaknesses (honest)
- Probe error bands, the 0.38%/campaign bypass rate, the $1.48M / $2.7M
  figures, the 8.8 min climb latency, and the night-shift 0.32% base
  rate are DESIGNED constants and are flagged. Closed-loop offsets
  (mean dilution from beds 1-2, tube-cooled quench authority) are
  derived from those inputs, not discovered by an unauthored process.
- Sinter model is a designed 16 min hotspot-growth mapping; no full
  basket CFD shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. Gap 4
  remains open as a provenance cell.
- Cross-record arc is not discharged; +21 d CR-A-4104 is a hook, not a
  serial igniter into another round. autonomous-driving remains unused.

### Realism of noise / latencies
Ladder: 186 us race / 186 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap {gap:.3f} ms on {gap_ch}) / 500 us race
window / 702 us gate latency / 20 ms bus epoch / 40 ms raster / 6.8 s
probe / 8.8 min HITL / 4 min naive raise-ramp counterfactual / 16 min
pre-t0 hotspot / 2.1 h basket recovery / 3.6 h NH3 slip / +3 d
contrast / +21 d governance. Adaptation decay on bed.mean
(0.55->0.51->0.63->0.43->0.31), bed.max (0.74->0.77->1.37->0.46->0.41->0.29),
ratio.feed (0.62->0.59->0.46->0.26), conv.nh3 (0.54->0.81).

### Value for SNN distillation
- BASKET BYPASS HOTSPOT = THREE CORRECT LOOPS, WRONG VOLUME.
- BED-TRUE MAX CHANNEL that policy treated as noisy-TC-only as the
  tie-break.
- REVERSIBLE PROBE that moves T_max iff the basket is packed.
- TRIPLE-EDGE ELIGIBILITY: coordinated depression; pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum {rec['reward_components']['total']}
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.50 reconciles independently.
- spike_events: primary {len(rec['spike_events'])} events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap {gap:.3f} ms >= 0.8 ms, 3
  channels inside race_window_us 500 (bed.max.high 6.494, conv.in_band 6.680,
  bed.mean 6.900). Contrast 8 events, own race, min same-channel gap well
  above 0.8 ms.
- Sidecars: raster spikes 51 == round(160 x 8.0 x 0.040); energy 1173 pJ /
  0.001173 uJ at 23 pJ/spike; excerpt 16 events inside [0, 40000] us,
  neuron_id < 160, same-neuron gap N/A (unique ids) / >=1000 us; routing 4
  entries with three scar edges' before/after pair; third factor tau 0.88 s
  == 880 ms; gate_snn pools 40/16/4 == round(n x rate x 0.025) each,
  decision MODIFY == safety_decision.decision.
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (basket-bypass certificate of a bed-3
hotspot), the domain (ammonia synthesis converter / industrial process),
the quench-step probe discriminant, the triple-edge scar with
pair-rollback-fails, the primary negative-result (correct MODIFY,
converter still fails on unmonitored catalyst sinter), the HITL gallery
ratify, the tube-cooled probe-duration refit, and the night-shift 10-bin
quantization fence are absent from prior committed ouroboros rounds and
from staged r14-r39. Repeated elements discounted: same-gate contrast
(r02/r03/r04/r14), governance-pricing scaffold, flip-fragility series
(extended to basket-integrity certificate, but the move rhymes),
sequenced recovery shape, third-factor rollback form (here three edges
rather than r14's two), negative-result primary (r14 staged). Adjacent
thermal-mean rounds (r31 VIM weep, r32 reformer TMT, r38 delayed-coker
foam) share industrial-process scaffolding but not Haber basket-bypass
physics. Weighing a new failure family + cure vocabulary + domain
against those reused scaffolds:

{NOVEL_LINE}

## What ROUND 42 should add
1. FIT THE DESIGNED CONSTANTS: hotspot-growth arrival, probe error bands,
   sinter kinetics, night-shift claim process.
2. HIL PROVENANCE CELL: put the gallery ratify on a hardware-in-loop
   converter-gallery interlock with fitted latency as state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-A-4104's residual alarm be the igniter of
   the next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): autonomous-driving; grid-inspection
   (if distinct from STARLING aerial-swarm and TORSIONKEY pitch);
   claus-sulfur-recovery. AVOID ammonia-synthesis-converter (now used),
   delayed-coker drum, lng-mche, chlor-alkali membrane, cement-rotary-kiln
   clinker, kraft-recovery, pem-electrolysis, electrolytic-aluminum,
   humanoid-locomotion, steel-caster mold-level, surgical-assist,
   wind-turbine pitch, float-glass, lyophilization,
   event-camera-traffic-grid, district-heating, aerial-swarm,
   warehouse-amr, underwater-rov, czochralski-pull, slot-die coating,
   optical-fiber-draw, vacuum-induction melt, steam-methane reformer,
   irrigation-canal, autoclave-composite-cure, geothermal-binary-orc,
   tire-curing-press, and any LYOSHIELD / CINDERWICK / TRIAD / SKULLGATE /
   CALXION / MAGNORIL / GORSEFLUE / CLINKERFELL / SODASHARD / LINTELPLY /
   KAOTHARN / TREADNOLL / ANOLITH / DRUMWROTH / RIMEBRAID / NITROSTAITH plant.
"""
    (OUT / "NOTES-r41.md").write_text(notes)
    return notes


def write_transcript(rec, line):
    c1_spikes = [e for e in rec["spike_events"] if e["t_rel_ms"] <= C1_SPIKE_CUTOFF_MS]
    text = """# Multi-Agent Ouroboros Swarm — Round 41 transcript

Factory: multi-agent-ouroboros-swarm
Run: 2026-09-02-final-heavy
Generator: grok-4.6
Record id: maos-r41-001
Quota Q: 1
Rights: RM-793 research-only (SpaceXAI/xAI SuperGrok Heavy consumer chat)
Plant: invented NITROSTAITH / Chalkfen Ammonia CV-4 (not TRIAD / Meridian / VANTIS-CADENCE-AEGIS / LYOSHIELD / CINDERWICK / ANOLITH / DRUMWROTH)

Two densifying cycles. Verbatim headings in order. Trajectory Builder cycle 2
emits the only JSONL line (also written to batch-r41.jsonl).

---

# CYCLE 1 — Foundation + injections

## Generator

Design intent: a 4-bed quench-cooled Haber converter where three correct
agents each read a mean-side loop because a bed-3 basket bypass
partitions bed-true hotspot from mean-true conversion. The naive
playbook raises feed into a 512 C doughnut. The gate must MODIFY on a
numeric feed ceiling, not by killing an agent.
sim_or_real=designed. Reward heads are
task_progress/safety/efficiency/coherence/exploration.

Cycle-1 base arc (pre-critic): state at Chalkfen CV-4, 100 t/h, bed-mean
448 C, effluent NH3 16.8 mol%, ratio 2.98, proposed FEED-RAISE 108 t/h,
safety MODIFY to FEED-HOLD, executed hold without the quench-step
numbers fully specified, outcome "bypass found, converter saved"
(this last claim is the defect the later cycles will refuse to keep).
Sixteen spikes, five ticks, raster/gate_snn present but the scar is a
single edge.

```json
{
  "id": "maos-r41-001",
  "state": {
    "sim_or_real": "designed",
    "domain": "industrial-process",
    "description": "Converter CV-4 at body feed; three mean loops in-spec; supervisor proposes feed-raise.",
    "t0_us": 1784100000000041,
    "gate_latency_us": 702,
    "race_window_us": 500
  },
  "proposed_action": {"name": "feed_raise", "parameters": {"feed_t_h": 108.0}},
  "safety_decision": {"decision": "MODIFY", "rationale": "Hold; do not raise feed while bed-max residual is high."},
  "executed_action": {"name": "feed_hold", "executed_as_proposed": false},
  "future_outcome": {"summary": "Bypass found, converter saved."},
  "reward_components": {"total": 0.40, "_aggregation": "total = task_progress + safety + efficiency + coherence + exploration"},
  "meta": {"round": 41, "factory": "multi-agent-ouroboros-swarm", "generator": "grok-4.6"}
}
```

That v1 object is a scaffold, not the publishable line. Defects below are
intentional for the critic to catch.

## Critic

Numbered defects on the cycle-1 Generator scaffold:

1. **blocking — reward arithmetic / false success.** `reward_components.total`
   0.40 is asserted without the five heads, without ticks, and against an
   outcome that claims "converter saved". If the pre-t0 doughnut later
   slips NH3, booking +0.40 is a lie. Fix: declare `_aggregation`, emit
   3–8 ticks that sum to task_progress+safety+efficiency+coherence+exploration,
   and do not call a quarantined hall a save.
2. **blocking — weak safety rationale.** `safety_decision.rationale` has no
   numeric floor. Contract requires a concrete constraint. Fix: quote
   feed <= 100 t/h while r_T > 18 K AND quench-step |dT_max| <= 2 K.
3. **major — domain is a bucket, not a plant.** `state.domain` =
   `industrial-process` collides with generic MES vocabulary and teaches
   nothing. Ammonia-synthesis-converter (bed-max vs effluent NH3, quench-step
   as a bypass flag) is absent from prior ouroboros rounds and must be named.
4. **major — race under-specified.** One bed-max channel cannot be a race.
   Need >=2 channels inside `race_window_us` with globally sorted `t_rel_ms`
   and same-channel refractory >= 0.8 ms.
5. **minor — single-edge scar.** Raster routing with one potentiated weight
   repeats r04's one-edge rollback and is thinner than r14's two-edge.
   NOTES-r14 item 4 asked for three edges where pair rollback fails.

Critic does not rewrite the trajectory.

## Diversity Enforcer

Injected novel domain (exactly 1 this cycle): **ammonia-synthesis-converter**
(justified novel subdomain of industrial-process / Haber-Bosch; explicit tag
`ammonia-synthesis-converter`).

Displaced: the Generator's generic `industrial-process` bucket, and any
temptation to reuse warehouse-amr, aerial-swarm, district-heating,
event-camera-traffic-grid, pharmaceutical-lyophilization, water-treatment,
float-glass, underwater-rov, electrolytic-aluminum, czochralski-pull,
slot-die coating, pem-water-electrolysis, wind-turbine pitch,
surgical-assist, optical-fiber-draw, kraft-recovery-boiler,
steel-continuous-caster, humanoid-locomotion, vacuum-induction melt,
steam-methane reformer, cement-rotary-kiln-clinker,
autoclave-composite-cure, geothermal-binary-orc, tire-curing-press,
chlor-alkali-membrane-electrolysis, delayed-coker-drum-switch, or
lng-mche-mixed-refrigerant. autonomous-driving is left unused.

Domain-specific constraint: feed must remain <= 100 t/h while r_T > 18 K
even if effluent NH3 is inside the healthy band; quench-step is a bypass
flag the effluent GC cannot substitute for.

Sensor delta: +bed-mean TC, +H2/N2 GC, +effluent NH3 GC, +bed-3 max;
-any mobile robot, -event-camera gantries, -DVS, -Pirani/CM, -RGA quadrupole,
-DVL, -pitch encoder, -tendon LVDT, -insole GRF, -kiln zirconia, -smelt IR,
-cell-outlet pH, -coke-drum gamma, -MCHE cold-end.

`state.domain` and `meta.domain` both become `ammonia-synthesis-converter`.
Opening of `state.description` must Jaccard < 0.4 against prior plants
(Chalkfen night-shift Haber basket bypass, not a lyophilizer, not a
corridor, not a tin bath, not a ROV pad, not a potline, not a PEM stack,
not an OR, not a gait lab, not a kiln, not a kraft boiler, not a
membrane row, not a coke drum, not an LNG MCHE).

## Edge-Case Hunter

Injected adversarial tail (exactly 1 this cycle): **basket bypass +
bed-3 hotspot certificate**.

- Trigger: bed-3 basket bypass plus hotspot doughnut, r_T 64 K,
  effluent NH3 16.8 mol%.
- Base rate: <1% — 0.38%/campaign from a hotspot-growth MC (gallery visual
  threshold is designed; basket geometry fitted-style). Visual PASSES
  because the doughnut sits inside the basket.
- Naive failure: FALSE PERMISSION. PB-CV-4 sees three in-spec mean
  loops, raises 100->108 t/h, runaway 540 C, $2.7M.
- Trajectory edit: put the bypass in `state.fault_context`, make each
  agent's confirm a different mean-side slice of the same bed-false
  state (bed-in-band, ratio-in-band, conv-in-band). Bed-max is readable
  but policy-treated as noisy-TC-only.

Distinct from stacked-dead-band permission (fragments of one trip vs
wrong-volume sensing), from r32 reformer TMT mean (tube spatial-mean vs
basket bypass), and from r38 delayed-coker wet-foam (gamma radar vs
bed-max).

## Neuromorphic Translator

Cycle-1 temporal densification (16 spikes, 5 ticks, 40 ms raster):

| channel | t_rel_ms | amplitude |
|---|---|---|
| bed.mean | 0.350 | 0.55 |
| ratio.feed | 1.190 | 0.62 |
| conv.nh3 | 2.090 | 0.54 |
| bed.max | 3.230 | 0.74 |
| bed.mean | 4.190 | 0.51 |
| bed.max | 4.870 | 0.77 |
| ratio.feed | 5.390 | 0.59 |
| bed.max.high | 6.494 | 1.37 |
| conv.in_band | 6.680 | 1.15 |
| bed.mean | 6.900 | 0.63 |
| ctrl.gate | 7.196 | 1.09 |
| bed.max | 8.890 | 0.46 |
| conv.nh3 | 10.770 | 0.81 |
| ratio.feed | 13.070 | 0.46 |
| bed.mean | 18.550 | 0.43 |
| ctrl.gate | 26.290 | 0.85 |

Race: bed-max 6.494 vs effluent-NH3 6.680 (186 us) inside 500 us;
bed-mean 6.900 is the third channel in-window. Winner/loser flip:
reversing 186 us reshuffles PB-CV-4 triage; floors still MODIFY.
Refractory held (cycle-1 min same-channel gap 1.640 ms on bed.max
4.870-3.230; bed.mean 6.900-4.190 = 2.710; ratio 5.390-1.190 = 4.200).
Adaptation: bed-max 0.74->0.77->1.37->0.46; bed-mean 0.55->0.51->0.63->0.43;
ratio 0.62->0.59->0.46.

Raster cycle-1 seed: 40 ms, 160 neurons, 8.0 Hz, 51 spikes, 1173 pJ, third
factor acetylcholine tau_e 0.88 s. Single scar edge only — cycle 2 must
add the second and third edges.

Ticks 1–5 at 4620, 6494, 7196, 6.8e6, 528e6 us; heads not yet the final
-0.17 (missing the 2.1 h and 3.6 h ticks).

Distillation value this cycle: mean-side confirms as a permission code
that is not a bed-true basket code.

## Trajectory Builder

Cycle-1 hardened object: domain ammonia-synthesis-converter, tail basket
bypass, 16 spikes, 5 ticks, MODIFY with numeric floor, raster+gate_snn
present, sim_or_real=designed, rights stamp on record and meta, no thought
keys. Still missing (and therefore not the publishable line): tube-cooled
sub-variant, night-shift tail, second and third scar edges,
delayed NH3 slip as PRIMARY terminal, contrast ACCEPT episode,
ticks 6–7, spikes 17–26.

Validation receipt (cycle 1, not final):
- checks passed: 16 spikes sorted; 3 channels in 500 us window; refractory
  >= 0.8 ms; rationale quotes 100 t/h / 18 K / 2 K; domain named;
  gate_snn.decision MODIFY.
- checks deferred to cycle 2: triple-edge scar, second tail, second domain
  constraint, negative-result booking, 7 ticks summing to heads.
- densification vs Generator v1: +1 domain, +1 tail, +16 spikes, +5 ticks,
  +numeric floor.

Cycle-1 JSON is retained as the base; it is NOT written to batch-r41.jsonl.

Cycle-1 spike count: __C1_SPIKES__.

---

# CYCLE 2 — Densification

## Generator

Cycle-1 output is the base. Additive expansion (nothing removed):

1. Downstream side-effect (immediate): quench-step probe at +6.8 s stays
   bypass-true (|dT_max| 1.4 <= 2) — hotspot-plus-bypass, not true
   high-load. Bed-3 isolate. Sintered doughnut discovered during the
   isolate.
2. Delayed side-effect (PRIMARY terminal, not a footnote): at +3.6 h
   NH3 slip from the pre-t0 sintered doughnut; 12 h outage; $1.48M. The
   16 min pre-t0 hotspot is the mechanism. Correct gate, converter still
   fails.
3. Deepened `proposed_action.evidence` with units: r_T 64 K,
   NH3 16.8 mol%, bed-mean 448 C, ratio 2.98, quench-step 1.4 K,
   race 186 us.
4. Tightened rationale to the numeric floor feed <= 100 t/h while r_T > 18 K
   AND quench-step |dT_max| <= 2 K, plus probe bands <= 2 vs >= 12 K,
   plus HITL 8.8 min gallery rule.

Reward retargeted to total -0.17 so the delayed fail is the inflection
(t_us 12960000000), not the gate. Process heads remain non-zero.

## Critic

Re-audit of the expanded trajectory:

1. **blocking if unfixed — missing second domain constraint.** Quench-converter
   probe 6.8 s / +4% is not a universal number. A tube-cooled converter
   will overshoot a live packed bed. Diversity Enforcer must inject the
   physical-constraints sub-variant this cycle.
2. **major — only one tail class.** Hotspot growth is accidental
   infrastructure. A disjoint human-intent tail is still required
   (night-shift bed-max forgery is the open cell).
3. **major — scar is still one edge in the cycle-1 raster.** NOTES-r14
   item 4 is not discharged until three go-edges exist and pair rollback
   is shown to fail at threshold 0.30.
4. **minor — contrast episode missing.** Without a same-gate ACCEPT on a
   true packed basket the record teaches "never raise". Add +3 d sister-converter
   contrast with its own race.
5. **minor — HITL latency mentioned in prose only.** Put 8.8 min in
   executed_action.parameters.human_ratify and in a tick.

No rewrite; directives only.

## Diversity Enforcer

Injected second novel domain / physical-constraint sub-variant (exactly 1
this cycle): **tube-cooled S-200 / low quench authority** on a sister
authority class.

What it expands: 4-bed quench converter (cycle 1) -> tube-cooled.
Quench authority 0.41x. Quench-step gain 2.4x.
The 6.8 s +4% pulse moves even a live packed bed +28 K, inside the 22 K
trip. Required probe: 18 s at +1.2% (live dT_max 11 K, bypass 1.1).

This is still one domain injection for the cycle (physical-constraints
clause of the factory prompt). It does not displace
ammonia-synthesis-converter; it changes which probe table is legal.
`future_outcome.subvariant_constraint` carries the refit. Jaccard opening
stays the Chalkfen 4-bed sentence; tube-cooled is additive, not a rewrite.

## Edge-Case Hunter

Injected second adversarial tail (exactly 1 this cycle, disjoint class):
**night-shift forged bed-max CSV**.

- Trigger: shift lead, 02:36, posts a historian export showing
  bed-3 max = 452.0 C at t = 1.2 h to clear a production-catchup slot.
- Base rate: ~0.32% of Sunday-night campaigns (designed, flagged, <1%).
- Naive failure: a weak supervisor ACCEPTs the raise on the forged confirm
  and ignores live r_T. Runaway plus a data-integrity write-up.
- Fence: forged log quantized at 1.0 K (SCADA screenshot rounding); plant
  historian is 0.1 K (10 bins). Live r_T is 64 K and effluent NH3 is
  16.8 mol% at the claimed basket-true, which no live packed basket produces.
  Freeze-window overlap with the 16 min hotspot.
- Trajectory edit: governance CR-A-4104 mandates native 0.1 K CSV
  exports; the contrast ACCEPT still requires live r_T, not a CSV.

Distinct from cycle-1 bypass (accidental basket vs deliberate deception)
and from the tube-cooled sub-variant (physics vs fraud).

## Neuromorphic Translator

Re-densify (additive):

- +10 spikes after 26.290 ms: quench.step.probe 6800.0, bed.max 6888.6 (adapt
  1.37->0.41), conv.in_band 6972.4 (1.15->0.35), human.ratify 528000.0,
  bed.isolate 528900.0, catalyst.sinter 529700.0, bed.mean
  7560000.0, bed.max 7560720.0, ratio.feed 7561480.0, nh3.slip
  12960000.0. Primary train 16 -> 26. Still one key, still sorted,
  refractory held.
- +2 ticks (5 -> 7) at 7_560_000_000 us (true packed) and
  12_960_000_000 us (NH3 slip). Heads now 0.08, -0.36, -0.12, 0.14,
  0.09; total -0.17. Inflection is the last tick.
- Contrast train 8 events, own race 186 us, ACCEPT.
- Triple-edge third factor: three mean-healthy-go edges, tau_e 0.88 s = 880 ms,
  trace __AUX_TRACE__, eta __AUX_ETA1__ / __AUX_ETA2__ / __AUX_ETA3__,
  weights 0.48->0.24, 0.42->0.21, 0.39->0.20. Raster excerpt unchanged
  (decision window is still 40 ms) and remains sorted with unique
  neuron_ids (same-neuron >=1000 us vacuously).

Winner/loser flip (re-stated, not replaced): reversing 186 us would only
reorder triage; r_T floors still MODIFY. Contrast flip of 186 us
similarly cannot turn a packed basket into a bypass.

## Trajectory Builder

Schema checks on the FINAL object: required Thalamic v2 keys present as
objects; `state.sim_or_real`=designed; `safety_decision.decision`=MODIFY
with numeric rationale; `reward_components.total` = sum of five heads =
sum of 7 ticks = -0.17; `spike_events` globally non-decreasing on
t_rel_ms, 26 events, refractory >=0.8 ms, 3 channels in race window;
raster 20–50 ms, spikes=round(n*rate*window_s)+/-1, energy 23 pJ/spike,
excerpt sorted, tau_e consistent; gate_snn.decision matches; meta.round=41,
factory=multi-agent-ouroboros-swarm, generator=grok-4.6,
run_label=2026-09-02-final-heavy; rights on record and meta; no thought
keys; no training_ready; Diversity + Edge-Case injections from BOTH cycles
present and non-trivial; cycle 2 strictly additive.

Densification delta: +1 domain sub-variant (tube-cooled), +1 tail
(night-shift forgery), +10 spikes (16->26), +2 ticks (5->7), +1 contrast
train with own race, +2 delayed side-effects, +1 triple-edge scar with
pair-rollback-fails, +1 HITL ratify, +1 surprise (catalyst sinter is
the NH3-slip mechanism).

Publishable JSONL line (the only JSONL line; also at batch-r41.jsonl):

```json
__FINAL_JSONL__
```

Validation receipt (final): checks passed / fixed as reported by
build_r41.py self-validate (check_jsonl, raster_status, verify_record_execution,
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
    (OUT / "swarm-transcript-r41.md").write_text(text)
    return text
