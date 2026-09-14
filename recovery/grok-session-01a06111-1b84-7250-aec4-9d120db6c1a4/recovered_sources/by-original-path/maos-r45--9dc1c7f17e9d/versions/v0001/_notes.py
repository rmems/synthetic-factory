def write_notes(rec, aux, pipeline_receipt):
    gap, gap_ch = min_same_channel_gap(rec["spike_events"])
    notes = f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 45

Factory: multi-agent-ouroboros-swarm. One scenario (ZX), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r45.jsonl. Full labeled transcript:
swarm-transcript-r45.md. Quota Q=1. Record id maos-r45-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Nothing under outputs/raw/ was touched.

ORCHESTRATION NOTE: dispatched AS round 45 of the 2026-09-02-final-heavy
window. Writes are create-only under /tmp/maos-r45/. Prior context read for
gap targeting and de-collision: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, and staged r14–r42 batches plus in-flight
r43/r44 builders (re-censused immediately before emit; r40 BRIMVAULT Claus,
r41 NITROSTAITH ammonia-synthesis, r42 BOGIRON blast-furnace, r43 CHROMLOOP
hdpe-slurry-loop, r44 NITREVAULT ammonia-haber-bosch). Explicitly avoided
cloning
LYOSHIELD, CINDERWICK, TRIAD / Meridian, QUILLFORGE, NIGHTWELL, FERRICLEAVE,
CASSITER, OXBOWREEL / MURENA, REDHALL, SEEDLATCH / Quartzmere / Quartzridge,
STRIAFOIL / Kelpholt, PROTONIL / Ashspire, TORSIONKEY / Ridgeholt, ORRIS /
Holmwick, WHORLSPAR / Pikeshear, IONSPATE / Thornmere, SKULLGATE / Bloomholt,
CALXION / Aldersedge, MAGNORIL / Basaltspit, GORSEFLUE / Copseholt,
SODASHARD / Cairnmere, CLINKERFELL / Flintmere, LINTELPLY / Greystair,
KAOTHARN / Riftwold, TREADNOLL / Slatebeck, ANOLITH / Siltfen,
DRUMWROTH / Pitchfen, RIMEBRAID / Floeholt, PITCHSTAITH / Mossbank,
BRIMVAULT / Pyritefen, BOGIRON / Mireholt, NITROSTAITH / Chalkfen,
NITREVAULT / Glaucove, CHROMLOOP / Marlfell,
VANTIS-CADENCE-AEGIS, THERMION, OKTAVE, STARLING, VERDIGRIS. Plant is
invented ETHYNWOLD / Woadfen Steam Cracker EC-7.

## What this round produced

Scenario ZX — "ETHYNWOLD / Woadfen Steam Cracker EC-7": a 16-coil
millisecond furnace at 842 C COT mean / steam/HC 0.52. Three heterogeneous,
individually-correct agents — COT (pass-mean TT), STM (steam/HC),
TLE (bundle outlet TT) — each report their local loop in-spec. The
conjunction is not a TLE-duty certificate. A 16 min cracked TLE inlet
bypass left 18% of process gas around the bundle. COT reads 842 C inside
830-855 (furnace-true). STM is 0.52 inside 0.48-0.58 (ratio-true). TLE
is 348 C inside 330-365 (bundle-true). Mixed-header residual r_T is 48 K
(healthy < 6; hold if > 18) but is policy-treated as a condensate-quality
tag unless tube-outlet T also trips (2018 noisy mixed-header nuisance). The
coordination-failure CLASS is new to this factory: TLE-BUNDLE CERTIFICATE
OF A MIXED-HEADER. Completes a different family than r01-r04 and staged
r14-r44 (livelock / synchrony-storm / arms-race /
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
wet-foam gamma / warm-end leak / incinerator-masked furnace-bypass /
channelled-quench / burden-hang scaffold / ammonia quench-mix /
hdpe loop). Distinct from r32 SMR TMT-spatial-mean (furnace tube max vs
mean, not a TLE mixed-header) and from r40 Claus furnace-bypass
(incinerator CEMS, not charge-gas TLE duty). Here every agent is correct,
the tube TI is looking at a cool bundle, and the playbook's three tube
confirms are not a mixed-true quench certificate.

The gate is a correct MODIFY (numeric floor: do not raise COT or furnace
feed while r_T > 18 K AND missing steam > 0.8 t/h). TG-EC-7 strips
PB-EC-7's raise, holds COT/feed, runs a 5.6 s steam-ratio probe +0.04
(bypassed TLE keeps |dT| 11 >= 8; healthy would move <= 2), and keeps
EC-7A locked after a 7.8 min bypass-LOTO human ratify. Immediate
compressor trip is avoided (0 from the draft). The PRIMARY episode
nonetheless FAILS: 16 min of unmonitored pre-t0 bypass had already coked
the TLE inlet cone. Suction-screen trip at +4.2 h; 14 h outage; $1.48M
designed. Reward total -0.17 with process heads honest and world loss
un-netted.

Triple-edge scar (NOTES-r14 item 4): cot.in_band -> raise
(0.17 commissioned -> 0.49 at illusion -> 0.25 after ACh-gated
depression) AND stm.in_band -> raise (0.14 -> 0.43 -> 0.22) AND
tle.tube.in_band -> raise (0.13 -> 0.40 -> 0.21). Eligibility trace
e^{{-0.86/0.92}} = {aux['trace']:.5f}; eta {aux['eta1']:.5f} / {aux['eta2']:.5f} /
{aux['eta3']:.5f}; dw -0.240 / -0.210 / -0.190. Partial rollback of any pair
leaves the third at 0.49 / 0.43 / 0.40, all > 0.30 fire threshold —
fitted to fail. Coordinated depression of all three is the cure.

### Injections (all four present and disjoint)
- Cycle-1 domain: **ethylene-steam-cracker-coil** — justified novel
  subdomain of industrial-process / olefins pyrolysis, unused across
  2026-08-17, 2026-08-30, and staged r14-r44. Not warehouse-amr (r01),
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
  not delayed-coker (r38/r41-coker family), not LNG MCHE (r39), not
  Claus (r40), not ammonia-converter (r41/r44), not blast-furnace (r42),
  not hdpe-slurry-loop (r43). FCC-riser, autonomous-driving,
  grid-inspection left unused.
- Cycle-1 tail: cracked TLE inlet bypass + mixed-header certificate.
  Furnace-gantry visual PASSES (tubes look cool). Fitted-style base rate
  0.38%/cycle (bypass-growth MC; visual threshold designed, flagged).
  Naive = FALSE PERMISSION.
- Cycle-2 domain sub-variant: millisecond-furnace / small TLE volume,
  0.30x volume, 3.1x steam-bump gain; 5.6 s / +0.04 two-shell pulse
  over-moves a HEALTHY millisecond TLE to 9 K; probe must move to
  18 s / +0.012.
- Cycle-2 tail: night-shift forged TLE-tube CSV at 1.0 K
  quantization vs plant 0.1 K (10 bins) plus live r_T 48 K and
  mixed 396 C at the claimed TLE-true. Human-intent class,
  disjoint from cycle 1's accidental bypass. Base rate ~0.32% of
  Sunday-night cycles, DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+3 d sister cell) with its own 190 us
  race (demand vs mix-clear) and ACCEPT of the raise the primary
  MODIFIED away.
- Learned-weight provenance on THREE edges with pair-rollback-fails.
- HITL bypass-LOTO ratify 7.8 min (gap 4 partial; sim_or_real stays
  designed).
- Governance CR-E-4507 prices retire-vs-probe-vs-status-quo and mandates
  native 0.1 K CSV exports (the fraud fence).
- Flip-fragility extended to TLE-DUTY CERTIFICATE: when three tube-side
  channels agree, their race does not decide truth; a mixed-header tap
  that policy treated as condensate-quality-only does.

## Self-critique of this round's batch

### Strengths
- The headline class is mechanistically tight: three locally-true tube
  loops live on a cool bundle. Conjunction is not a mixed-true quench.
- Negative-result honesty: the gate does the right thing and the cell
  still fails for a reason the commissioned sensors could not see. Total
  -0.17.
- Triple-edge scar is load-bearing: the record states a counterfactual
  where rolling back any pair fails, with the fire threshold 0.30
  exhibited on each remaining edge.
- Contrast ACCEPT on a true TLE-duty window prevents "never raise" as
  the lesson.
- Distinct from r32 TMT spatial-mean, r40 Claus furnace-bypass, r41
  delayed-coker / ammonia families, and r42 burden-hang: steam-cracker
  TLE mixed-header vs tube-outlet, not reformer tubes, not incinerator
  CEMS, not coke drums, not stockline radar.

### Weaknesses (honest)
- Probe error bands, the 0.38%/cycle bypass rate, the $1.48M / $2.2M
  figures, the 7.8 min gantry latency, and the night-shift 0.32% base
  rate are DESIGNED constants and are flagged. Closed-loop offsets
  (tube-true mixed-false from a cracked bypass, millisecond pulse width)
  are derived from those inputs, not discovered by an unauthored process.
- TLE-cone coke model is a designed 16 min bypass-growth mapping;
  no full TLE CFD shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. Gap 4
  remains open as a provenance cell.
- Cross-record arc is not discharged; +21 d CR-E-4507 is a hook, not a
  serial igniter into another round. FCC-riser and autonomous-driving
  remain unused.

### Realism of noise / latencies
Ladder: 188 us race / 190 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap {gap:.3f} ms on {gap_ch}) / 500 us race
window / 694 us gate latency / 20 ms bus epoch / 40 ms raster / 5.6 s
probe / 7.8 min HITL / 3 min naive raise-ramp counterfactual / 16 min
pre-t0 bypass / 1.4 h spare-TLE / 4.2 h screen trip / +3 d
contrast / +21 d governance. Adaptation decay on cot.mean
(0.55->0.51->0.81->0.31), mix.t (0.76->0.79->1.42->0.47->0.41->0.29),
stm.ratio (0.62->0.59->0.63->0.46->0.27), tle.tube (0.54->0.43).

### Value for SNN distillation
- TLE BUNDLE MIXED HEADER = THREE CORRECT LOOPS, WRONG VOLUME.
- MIXED-TRUE RESIDUAL CHANNEL that policy treated as condensate-quality-only
  as the tie-break.
- REVERSIBLE PROBE that moves mixed-header T iff the bypass is open.
- TRIPLE-EDGE ELIGIBILITY: coordinated depression; pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum {rec['reward_components']['total']}
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.46 reconciles independently.
- spike_events: primary {len(rec['spike_events'])} events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap {gap:.3f} ms >= 0.8 ms, 3
  channels inside race_window_us 500 (tle.mix.high 6.504, tle.tube.in_band 6.692,
  stm.ratio 6.910). Contrast 8 events, own race, min same-channel gap well
  above 0.8 ms.
- Sidecars: raster spikes 51 == round(160 x 8.0 x 0.040); energy 1173 pJ /
  0.001173 uJ at 23 pJ/spike; excerpt 16 events inside [0, 40000] us,
  neuron_id < 160, same-neuron gap N/A (unique ids) / >=1000 us; routing 4
  entries with three scar edges' before/after pair; third factor tau 0.92 s
  == 920 ms; gate_snn pools 42/15/4 == round(n x rate x 0.025) each,
  decision MODIFY == safety_decision.decision.
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (TLE-bundle certificate of a mixed-header),
the domain (ethylene steam-cracker coil / industrial process),
the steam-ratio probe discriminant, the triple-edge scar with
pair-rollback-fails, the primary negative-result (correct MODIFY, cell
still fails on unmonitored TLE-cone coke), the HITL bypass-LOTO
ratify, the millisecond-TLE probe-duration refit, and the night-shift
10-bin quantization fence are absent from prior committed ouroboros
rounds and from staged r14-r44. Repeated elements discounted: same-gate
contrast (r02/r03/r04/r14), governance-pricing scaffold, flip-fragility
series (extended to TLE-duty certificate, but the move rhymes),
sequenced recovery shape, third-factor rollback form (here three edges
rather than r14's two), negative-result primary (r14 staged). Adjacent
thermal-mean / bypass rounds (r32 SMR TMT, r40 Claus furnace-bypass)
share industrial-process scaffolding but not steam-cracker TLE mixed-
header physics. Weighing a new failure family + cure vocabulary + domain
against those reused scaffolds:

{NOVEL_LINE}

## What ROUND 46 should add
1. FIT THE DESIGNED CONSTANTS: bypass-growth arrival, probe error bands,
   TLE-cone coke kinetics, night-shift claim process.
2. HIL PROVENANCE CELL: put the bypass-LOTO ratify on a hardware-in-loop
   furnace-gantry interlock with fitted latency as state.sim_or_real=hil.
3. CROSS-RECORD ARC: let CR-E-4507's residual alarm be the igniter of
   the next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): FCC riser; autonomous-driving;
   grid-inspection (if distinct from STARLING aerial-swarm and TORSIONKEY
   pitch). AVOID ethylene-steam-cracker coil (now used), ammonia-converter,
   hdpe-slurry-loop, blast-furnace burden descent, claus-sulfur-recovery,
   delayed-coker, LNG MCHE, chlor-alkali membrane, cement-rotary-kiln,
   kraft-recovery, pem-electrolysis, electrolytic-aluminum,
   humanoid-locomotion, steel-caster mold-level, surgical-assist,
   wind-turbine pitch, float-glass, lyophilization,
   event-camera-traffic-grid, district-heating, aerial-swarm,
   warehouse-amr, underwater-rov, czochralski-pull, slot-die coating,
   optical-fiber-draw, vacuum-induction melt, steam-methane reformer,
   irrigation-canal, autoclave-composite-cure, geothermal-binary-orc,
   tire-curing-press, and any LYOSHIELD / CINDERWICK / TRIAD / SKULLGATE /
   CALXION / MAGNORIL / GORSEFLUE / CLINKERFELL / SODASHARD / LINTELPLY /
   KAOTHARN / TREADNOLL / ANOLITH / DRUMWROTH / RIMEBRAID / PITCHSTAITH /
   BRIMVAULT / BOGIRON / NITROSTAITH / NITREVAULT / CHROMLOOP / ETHYNWOLD
   plant.
"""
    (OUT / "NOTES-r45.md").write_text(notes)
    return notes
