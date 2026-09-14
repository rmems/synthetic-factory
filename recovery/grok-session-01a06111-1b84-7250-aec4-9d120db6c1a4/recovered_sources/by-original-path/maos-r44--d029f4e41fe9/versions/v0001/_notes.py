def write_notes(rec, aux, pipeline_receipt):
    gap, gap_ch = min_same_channel_gap(rec["spike_events"])
    notes = f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 44

Factory: multi-agent-ouroboros-swarm. One scenario (ZP), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r44.jsonl. Full labeled transcript:
swarm-transcript-r44.md. Quota Q=1. Record id maos-r44-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Nothing under outputs/raw/ was touched.

ORCHESTRATION NOTE: dispatched AS round 44 of the 2026-09-02-final-heavy
window. Writes are create-only under /tmp/maos-r44/. Prior context read for
gap targeting and de-collision: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, and staged r14–r43 (re-censused immediately
before emit; r40 BRIMVAULT / Pyritefen Claus SR-3; r41 rewritten as
NITROSTAITH / Chalkfen Ammonia CV-4 ammonia-synthesis-converter, so the
first r44 ammonia lock was abandoned; r42 BOGIRON / Mireholt BF-6
blast-furnace; r43 in-flight CHROMLOOP / Marlfell LP-6 hdpe-slurry-loop;
r45 in-flight ETHYNWOLD ethylene-cracker). Explicitly avoided cloning
LYOSHIELD, CINDERWICK, TRIAD / Meridian, QUILLFORGE, NIGHTWELL, FERRICLEAVE,
CASSITER, OXBOWREEL / MURENA, REDHALL, SEEDLATCH, STRIAFOIL, PROTONIL,
TORSIONKEY, ORRIS, WHORLSPAR, IONSPATE, SKULLGATE, CALXION, BRACEGILT,
MAGNORIL, GORSEFLUE, SODASHARD, CLINKERFELL, LINTELPLY, KAOTHARN,
TREADNOLL, ANOLITH, DRUMWROTH, RIMEBRAID, PITCHSTAITH, BRIMVAULT,
NITROSTAITH, BOGIRON, CHROMLOOP, ETHYNWOLD, NITREVAULT,
VANTIS-CADENCE-AEGIS, THERMION, OKTAVE, STARLING, VERDIGRIS. Plant is
invented RUNNELGATE / Ghyllmere Hydro KT-5 (highland-ghyll hydropower
campus, not a mill-town, ice-fjord, fertilizer cove, blast-furnace bog,
or slurry loop). Leftover candidates bioreactor-perfusion /
autonomous-driving / grid-inspection / fcc-regenerator were left unused
so concurrent empty slots can take them.

## What this round produced

Scenario ZP — "RUNNELGATE / Ghyllmere Hydro KT-5": a 92 MW Kaplan unit
mid-hold at 42.6 m net head / 84.2 MW. Three heterogeneous,
individually-correct agents — POWER (MW TT), HEAD (forebay level),
GUIDE (wicket opening) — jointly report the unit raise-legal. The
consensus is false. A runner-hub seal gap dumps water past the blades
over 18 min. POWER stays in-band because remaining blades still make
nameplate at higher specific loading. HEAD 42.6 m sits inside 41.0-44.0
because the reservoir is upstream. GUIDE 68% sits inside 60-75 because
servomotor position is true. Uncommissioned r_sigma is 0.11 against a
0.22 hold. Uncommissioned r_vib is 4.8 mm/s against a 1.6 hold. The
coordination-failure CLASS is new to this factory: HUB-SEAL CAVITATION
NULLSPACE OF A POWER-OK CERTIFICATE. Completes a different family than
r01-r04 and staged r14-r43. Distinct from r25 wind-turbine pitch
(bearing spline), which is a different rotating machine. Here every
agent is correct, the unit is not unstable, and the playbook's three
confirms are one power-ok model of a leaking hub.

The gate is a correct MODIFY (numeric floor: do not raise the wicket on
the 92 MW Kaplan while r_sigma < 0.22 AND r_vib > 1.6 mm/s). TG-KT-5
strips PB-KT-11's raise, holds wicket at 68%, runs a 6.0 s gate-cut
probe 8% (leak jumps RMS 2.7 mm/s >= 2.4; sealed would stay <= 0.4),
and isolates the hub after a 10.4 min headcover human ratify. The
cavitating raise is avoided (0 extra percent). The PRIMARY episode
nonetheless FAILS: 18 min of unmonitored pre-t0 cavitation had already
pitted 2.1 mm of blade trailing edge. Efficiency -3.8% vs 0.6% spec;
9.4 d dump; $1.86M designed. Reward total -0.15 with process heads
honest and world loss un-netted.

Three-edge scar (NOTES-r14 item 4): power.ok -> raise_gate
(0.16 commissioned -> 0.46 at illusion -> 0.22 after ACh-gated
depression) AND head.ok -> raise_gate (0.14 -> 0.41 -> 0.20)
AND guide.ok -> raise_gate (0.13 -> 0.38 -> 0.19). Eligibility
trace e^{{-6.0/6.0}} = {aux['trace']:.5f}; eta {aux['eta1']:.5f} /
{aux['eta2']:.5f} / {aux['eta3']:.5f}; dw -0.240 / -0.210 / -0.190.
Rolling back any pair leaves the remaining edge above the 0.30 raise
threshold — fitted to fail. Coordinated depression of all three is the
cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **hydroelectric-kaplan-wicket** — justified novel
  sub-domain, unused across 2026-08-17, 2026-08-30, and staged r14-r43.
  Not warehouse-amr, aerial-swarm, district-heating, event-camera grid,
  lyophilization, stator-weld, air-separation, water-treatment,
  float-glass, underwater-rov, potline, czochralski, slot-die, PEM,
  wind-turbine-pitch, surgical-assist, optical-fiber-draw,
  kraft-recovery, caster-mold-level, humanoid-locomotion, VIM, SMR,
  cement kiln, autoclave, geothermal-ORC, tire-curing, chlor-alkali,
  delayed-coker, lng-mche, claus, ammonia-synthesis (r41), blast-furnace
  (r42), hdpe-slurry-loop (r43 in flight), ethylene-cracker (r45 in
  flight).
- Cycle-1 tail: 0.11 Thoma hub-seal leak + power-ok model. Weekend
  blade-angle stroke PASSES 0.30. Fitted-style base rate 0.36%/hold
  (hub-seal MC; liner-gap spec designed, flagged). Naive = FALSE
  PERMISSION.
- Cycle-2 domain sub-variant: 4.8 MW mini-hydro Kaplan, 0.16x inertia;
  6.0 s / 8% production pulse overspeeds 14%; probe must move to 18 s /
  2.5%.
- Cycle-2 tail: Sunday-night forged Thoma-sigma CSV at 0.05
  quantization vs plant 0.002 (25 bins) plus live r_sigma 0.11 at the
  claimed sealed-hub. Human-intent class, disjoint from cycle 1's
  accidental leak. Base rate ~0.26% of Sunday-night holds, DESIGNED,
  flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+3 d sister unit) with its own 192 us
  race (demand vs leak-clear) and ACCEPT of the raise the primary
  MODIFIED away.
- Learned-weight provenance on THREE edges with any-pair-rollback-fails.
- HITL headcover-interlock ratify 10.4 min (gap 4 partial; sim_or_real
  stays designed).
- Governance CR-K-4404 prices retire-vs-probe-vs-status-quo and mandates
  native 0.002 CSV exports (the fraud fence).
- Flip-fragility extended to HUB-SEAL-CAVITATION-NULLSPACE.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: 0.11 Thoma under a
  power-ok-only model is the arithmetic that makes POWER's success
  HEAD's irrelevance and GUIDE's silence.
- Negative-result honesty: the gate does the right thing and the runner
  still fails for a reason the commissioned sensors could not see.
  Total -0.15.
- Three-edge scar is load-bearing: rolling back any pair fails, with
  the raise threshold 0.30 exhibited on the remaining edge.
- Contrast ACCEPT on a true sealed hub prevents "never raise" as the
  lesson.
- Domain is not a recycle of r25 pitch or r41 ammonia: Kaplan wicket /
  draft-tube cavitation vs pitch-bearing spline vs converter basket.

### Weaknesses (honest)
- Probe error bands (leak >= 2.4 mm/s RMS jump, sealed <= 0.4), the
  0.36%/hold leak rate, the $1.86M / $3.74M figures, the 10.4 min LOTO
  latency, and the Sunday-night 0.26% base rate are DESIGNED constants
  and are flagged. Closed-loop offsets (phantom in-band MW from 0.11
  sigma hub mix, mini-hydro overspeed width) are derived from those
  inputs, not discovered by an unauthored process.
- Pitting-growth model is a designed 18 min mapping; no full runner CFD
  shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. The
  NOTES-r14 HIL provenance cell remains open.
- Cross-record arc is a hook (CR-K-4404 +21 d), not a serial igniter
  into another round.

### Realism of noise / latencies
Ladder: 192 us race / 192 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap {gap:.3f} ms on {gap_ch}) / 500 us race
window / 700 us gate latency / 20 ms bus epoch / 40 ms raster / 6.0 s
probe / 10.4 min HITL / 18 min pre-t0 leak / 2.5 h sealed-legal hold /
3.4 h efficiency assay / +3 d contrast / +21 d governance. Adaptation
decay on power.mw (0.53->0.49->0.45->0.30), sigma.th
(0.71->1.26->0.85->0.39->0.19), head.lvl (0.61->0.64->0.46->0.28),
guide.pct (0.55->0.52->0.43).

### Value for SNN distillation
- HUB-SEAL CAVITATION NULLSPACE = THREE CORRECT LOOPS, ONE LEAKING RUNNER.
- r_sigma + r_vib as the tie-break that is not in the power-ok window.
- REVERSIBLE PROBE that spikes draft-tube RMS iff the hub is leaking.
- THREE-EDGE ELIGIBILITY: coordinated depression; any-pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum {rec['reward_components']['total']}
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.46 reconciles independently.
- spike_events: primary {len(rec['spike_events'])} events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap {gap:.3f} ms >= 0.8 ms, 3
  channels inside race_window_us 500 (sigma 6.812, power-ok 7.004,
  draft.vib 7.148). Contrast 8 events, own race, min same-channel gap well
  above 0.8 ms.
- Sidecars: raster spikes 54 == round(168 x 8.0 x 0.040); energy 1242 pJ /
  0.001242 uJ at 23 pJ/spike; excerpt 16 events inside [0, 40000] us,
  neuron_id < 168, same-neuron gap unique-ids / >=1000 us; routing 4
  entries with three scar edges' before/after pair; third factor tau 6.0 s
  == 6000 ms; gate_snn pools 45/18/6 == round(n x rate x 0.028) each,
  decision MODIFY == safety_decision.decision.
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (hub-seal cavitation nullspace of a
power-ok certificate), the domain (hydroelectric-kaplan-wicket),
the gate-cut probe discriminant, the three-edge scar with
any-pair-rollback-fails, the primary negative-result (correct MODIFY,
runner still fails -3.8% efficiency on unmonitored pre-t0 pitting), the
HITL headcover-interlock ratify, the 4.8 MW mini-hydro probe-duration
refit, and the Sunday-night 25-bin quantization fence are absent from
prior committed ouroboros rounds and from staged r14-r43. Repeated
elements discounted: same-gate contrast, governance-pricing scaffold,
flip-fragility series (extended to hub-seal-cavitation-nullspace, but
the move rhymes), sequenced recovery shape, third-factor rollback form,
negative-result primary (here blade pitting). Weighing a new failure
family + cure vocabulary + unused sub-domain + highland-ghyll geography
against those reused scaffolds:

{NOVEL_LINE}

## What ROUND 45 should add
1. FIT THE DESIGNED CONSTANTS: leak arrival, probe RMS-jump bands,
   pitting-to-efficiency CFD, Sunday-night claim process.
2. HIL PROVENANCE CELL: put the headcover-interlock LOTO on a
   hardware-in-loop power-hall pendant with fitted latency as
   state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-K-4404's r_sigma alarm be the igniter of the
   next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): bioreactor-perfusion;
   autonomous-driving; grid-inspection (if distinct from STARLING
   aerial-swarm); fcc-regenerator-afterburn.
   AVOID hydroelectric-kaplan-wicket (now used), ammonia-synthesis
   (r41), blast-furnace (r42), hdpe-slurry-loop (r43 in flight),
   ethylene-cracker (r45 in flight), claus (r40), delayed-coker,
   lng-mche, chlor-alkali, tire-curing, geothermal-ORC, autoclave,
   cement kiln, SMR, VIM, kraft-recovery, optical-fiber, PEM,
   surgical-assist, wind-turbine-pitch, slot-die, czochralski, potline,
   float-glass, water-treatment, lyophilization, event-camera grid,
   district-heating, aerial-swarm, warehouse-amr, air-separation,
   underwater-rov, humanoid-locomotion, and any LYOSHIELD / CINDERWICK /
   TRIAD / NITROSTAITH / BOGIRON / CHROMLOOP / ETHYNWOLD / NITREVAULT /
   BRIMVAULT / RIMEBRAID / DRUMWROTH / RUNNELGATE plant.
"""
    (OUT / "NOTES-r44.md").write_text(notes)
    return notes
