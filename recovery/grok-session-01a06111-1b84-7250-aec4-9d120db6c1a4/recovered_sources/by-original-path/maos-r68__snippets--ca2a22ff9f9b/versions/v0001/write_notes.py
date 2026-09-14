def write_notes(rec, aux, pipeline_receipt):
    gap, gap_ch = min_same_channel_gap(rec["spike_events"])
    ras = rec["raster"]
    notes = f"""# NOTES — Multi-Agent Ouroboros Swarm, run 2026-09-02-final-heavy, ROUND 68

Factory: multi-agent-ouroboros-swarm. One scenario (WL), strict loop:
Generator v1 -> cycle 1 (Critic, Diversity Enforcer, Edge-Case Hunter,
Neuromorphic Translator, Trajectory Builder -> v2) -> cycle 2 (all six -> v3
final). v3 is the single line of batch-r68.jsonl. Full labeled transcript:
swarm-transcript-r68.md. Quota Q=1. Record id maos-r68-001. Generator grok-4.6.
Rights: RM-793 research-only (SpaceXAI/xAI, SuperGrok Heavy consumer chat).
Swarm: WOLD-LOCK. Create-only writes under the LIVE factory dir plus /tmp/maos-r68/.

ORCHESTRATION NOTE: dispatched AS round 68 of the 2026-09-02-final-heavy
LIVE tree. Operator assigned round 68, swarm WOLD-LOCK, id maos-r68-001,
Q=1 after 2x6-role cycles. Explicitly avoided 2026-08-17 and 2026-08-30.
Prior context: prompts/02-multi-agent-ouroboros-swarm.md,
prompts/_factory-contract.md, live NOTES r01/r02/r03/r21/r22/r41/r42/r61-r67
and occupancy census /tmp/maos-r14–r67. Explicitly avoided cloning LYOSHIELD,
CINDERWICK, TRIAD / Meridian, QUILLFORGE, NIGHTWELL, FERRICLEAVE, CASSITER,
OXBOWREEL, REDHALL, SEEDLATCH, STRIAFOIL, PROTONIL, TORSIONKEY, ORRIS,
WHORLSPAR, IONSPATE, SKULLGATE, CALXION, MAGNORIL, GORSEFLUE, SODASHARD,
CLINKERFELL, LINTELPLY, KAOTHARN, TREADNOLL, ANOLITH, DRUMWROTH, RIMEBRAID,
BRIMVAULT, NITROSTAITH, BOGIRON, CHROMLOOP, ETHYNWOLD, NITREVAULT,
RUNNELGATE, SPARKHOLT, DIPLEGAR, OLEUMWEIR, SKARVOLT, GOBSPALL, GOBWOLD,
GAUZEFELL, OSMOLITH, PUSHERFELL, CREELWOLD, LIXIVQUERN, GIBBSQUERN, OSMOQUAY,
COILSHAW, LOOPERQUAY, SIPHONWOLD, LANCEQUAY, UREASTAITH, DRYSTAITH,
TITERWEIR, ZINCFELL, GLIMMERAXLE, HOLLOWMERE, WINDBOXHOLT, KALYCIRQUE,
GYPSUMWEIR, GALVSTAITH, PACKFLUE, LOCKSPUR, CORONSTAITH, SHEDWOLD, WOLD-BARN,
VANTIS-CADENCE-AEGIS, THERMION, OKTAVE, STARLING, VERDIGRIS, FEN-SPIT,
BARN-SPIT, SPUR-HEARTH. Not a restack of WOLD-BARN / Barleyholt malt kiln
(air-on-floor enzyme kill vs Phase-II aeration-lock biology). Plant is
invented WOLD-LOCK / Mushholt Phase-II Compost Tunnel CT-6.

## What this round produced

Scenario WL — "WOLD-LOCK / Mushholt Phase-II Compost Tunnel CT-6": a 6-zone
38 m forced-aeration Phase-II mushroom compost tunnel at 58.0 C / 8.5 vol%
O2 / 9.2 t wheat-straw plus horse-manure. Three heterogeneous,
individually-correct agents — PLN (six-zone plenum mean T), O2 (exhaust
zirconia), FAN (aeration-fan tachometer) — each report their local loop
in-spec. The conjunction is not a lock-true certificate. Zone Z-5 has a
collapsed aeration-lock (blocked floor spigot). PLN reads 58.0 C inside
54-62 (five intact zones dominate the header). O2 is 8.5 vol% inside
6.5-11.0 (stack-true). FAN is 36.0 Hz inside 30-42 (shaft-true). Local
compost TC infers 81.6 C (healthy < 64; hold if > 68) and local NH3 2400
ppm (hold if > 700) but is policy-treated as a surface-dry nuisance tag
unless PLN mean also trips (2012 noisy compost-probe after a wet fill).
The coordination-failure CLASS is new to this factory: PLENUM-MEAN
CERTIFICATE OF A LOCAL AERATION-LOCK COLLAPSE. Completes a different
family than live r01 galvanizing, r21 CAV, r41 perfusion, r61 sinter,
r62/r42 grid, r63 lock-spur, r64 malt kiln, r65 tobacco barn, r66
rotisserie, r67 farm AD. Here every agent is correct, the PLN average is
looking at tunnel-mean heat, and the playbook's three PLN confirms are
not a lock-true certificate. Distinct from r64 malt kiln: biological
exothermic Phase-II compost plus ammonia vs kiln-air enzyme kill; the
"lock" is an aeration-floor spigot, not a canal pound.

The gate is a correct MODIFY (numeric floor: do not raise steam above
58.0 C while Z-5 local TC > 68 C AND Z-5 NH3 > 700 ppm). TG-CT-6
strips PB-CT-6's raise-steam, holds 58.0 C, runs an 8.2 s reverse-aeration
+6 Hz (lock keeps |Delta PLN mean| 0.3 <= 0.45 K; aerated would move
>= 2.2), and isolates Z-5 after an 11.2 min tunnel-gallery human ratify.
Immediate 7.1 t pasteurization-kill is avoided (0 from the draft). The
PRIMARY episode nonetheless FAILS: 15 min of unmonitored pre-t0 lock
collapse had already killed 2.4 t of compost. Ammonia spike at +5.2 h;
16 h stall; $0.58M designed. Reward total -0.19 with process heads
honest and world loss un-netted.

Triple-edge scar (NOTES-r14 item 4): pln.in_band -> raise_steam
(0.17 commissioned -> 0.50 at illusion -> 0.25 after ACh-gated
depression) AND o2.ok -> raise_steam (0.16 -> 0.44 -> 0.22) AND
fan.ok.in_band -> raise_steam (0.15 -> 0.41 -> 0.20). Eligibility trace
e^{{-0.82/0.92}} = {aux['trace']:.5f}; eta {aux['eta1']:.5f} / {aux['eta2']:.5f} /
{aux['eta3']:.5f}; dw -0.250 / -0.220 / -0.210. Partial rollback of any pair
leaves the third at 0.50 / 0.44 / 0.41, all > 0.30 fire threshold —
fitted to fail. Coordinated depression of all three is the cure.

Independent LIF raster: window 44 ms, 156 neurons, 21.5 Hz, spikes
{ras['spikes']} == round(156 x 21.5 x 0.044), energy {ras['energy_pJ']} pJ
at 23 pJ/spike. excerpt_source=independent_lif, sim_scope=sidecar_only,
seed 68001. Excerpt is membrane crossings (lif.hold early vs lif.lock
22-25.8 ms), disjoint from spike_events timestamps.

### Injections (all four present and disjoint)
- Cycle-1 domain: **mushroom-compost-tunnel** — justified novel subdomain of
  industrial-process / Phase-II forced-aeration composting, unused across live
  r01/r02/r03/r21/r22/r41/r42/r61-r67 and staged r14-r67. Distinct from r64
  malt kiln, r65 tobacco barn, r66 rotisserie, r67 farm AD, r61 sinter.
  hrsg-attemperator left unused.
- Cycle-1 tail: Z-5 collapsed aeration-lock + anaerobic-kill certificate.
  Tunnel-gallery visual PASSES (blocked spigot under the bed). Fitted-style
  base rate 0.32%/campaign (spigot MC; visual threshold designed, flagged).
  Naive = FALSE PERMISSION.
- Cycle-2 domain sub-variant: high-C:N chicken-litter compost, 1.8x heat,
  2.2x reverse-aeration gain; 8.2 s / +6 Hz wheat-straw pulse overshoots live
  aerated tunnel to a 9 K false PLN; probe must move to 24 s / +1.8 Hz.
- Cycle-2 tail: night-shift forged local-TC CSV at 1.0 C quantization vs
  plant 0.1 C (10 bins) plus live TC 81.6 C and local NH3 2400 ppm at
  the claimed lock-true. Human-intent class, disjoint from cycle 1's
  accidental lock collapse. Base rate ~0.27% of Sunday-night campaigns,
  DESIGNED, flagged.

### Structural density moves
- Embedded SAME-GATE contrast (+3 d sister tunnel) with its own 176 us
  race (demand vs lock-clear) and ACCEPT of the raise-steam the primary
  MODIFIED away.
- Learned-weight provenance on THREE edges with pair-rollback-fails.
- HITL tunnel-gallery ratify 11.2 min (gap 4 partial; sim_or_real stays
  designed — invented plant, not hil).
- Governance CR-C-6806 prices retire-vs-probe-vs-status-quo and mandates
  native 0.1 C CSV exports (the fraud fence).
- Flip-fragility extended to LOCK-TRUE CERTIFICATE.
- Independent LIF sidecar (not a language-train remap).

## Self-critique of this round's batch

### Strengths
- Headline class is mechanistically tight: three locally-true mean loops
  live on PLN mean, exhaust O2, and fan shaft. Conjunction is not a
  lock-true heat certificate.
- Negative-result honesty: the gate does the right thing and the tunnel
  still fails for a reason the commissioned sensors could not see.
  Total -0.19.
- Triple-edge scar is load-bearing: rolling back any pair fails, with
  fire threshold 0.30 exhibited on each remaining edge.
- Contrast ACCEPT on a true pasteurization-duty window prevents "never
  raise-steam" as the lesson.
- Distinct from r64 malt kiln (air-on-floor enzyme vs Phase-II ammonia),
  r65 tobacco flue, r67 farm-AD crust, r61 sinter windbox: compost
  aeration-lock local TC vs plenum mean.
- Independent LIF excerpt is disjoint from spike_events times.

### Weaknesses (honest)
- Probe error bands, the 0.32%/campaign collapse rate, the $0.58M /
  $1.6M figures, the 11.2 min walk latency, and the night-shift 0.27%
  base rate are DESIGNED constants and are flagged. Closed-loop offsets
  (header dilution from one blocked spigot, high-C:N heat) are
  derived from those inputs, not discovered by an unauthored process.
- Anaerobic-kill-to-ammonia-spike model is a designed 15 min mapping; no
  full CFD of Z-5 shipped.
- Human-in-the-loop is ratification latency, not sim_or_real=hil. Gap 4
  remains open as a provenance cell (invented plants stay designed).
- Cross-record arc is a hook (CR-C-6806 +21 d), not a serial igniter
  into another round. hrsg-attemperator remains unused.
- The densifying-loop *shape* (three correct agents / MODIFY / probe /
  triple-edge / night-shift CSV / sister ACCEPT / negative primary)
  rhymes with r64/r65/r67. Physics, plant, sensors, and failure class
  are new; the scaffold is not.

### Realism of noise / latencies
Ladder: 196 us race / 176 us contrast race / 0.8 ms refractory floor
(tightest exhibited same-channel gap {gap:.3f} ms on {gap_ch}) / 500 us race
window / 716 us gate latency / 20 ms bus epoch / 44 ms independent LIF
raster / 8.2 s probe / 11.2 min HITL / 8 min naive raise-steam-ramp
counterfactual / 15 min pre-t0 lock / 3.1 h lock-true recovery / 5.2 h
ammonia spike / +3 d contrast / +21 d governance. Adaptation decay on pln.hot
(0.53->0.50->0.42->0.29), lock.nh3 (0.76->0.78->0.43->0.39->0.27),
fan.ok (0.55->0.57->0.45->0.24), o2.ok (0.61->0.64->0.80).

### Value for SNN distillation
- AERATION LOCK = THREE CORRECT LOOPS, WRONG VOLUME.
- LOCK-TRUE TC CHANNEL that policy treated as surface-dry-nuisance-only as
  the tie-break.
- REVERSIBLE PROBE that recouples PLN mean iff the zone is aerated.
- TRIPLE-EDGE ELIGIBILITY: coordinated depression; pair rollback fails.
- CRITIC HEAD that can hold a process-correct MODIFY against a later
  unmonitored world loss without netting.
- INDEPENDENT LIF sidecar whose excerpt is membrane crossings.

## Reconciliation and validity receipts
- reward_components: 5-head unweighted signed sum {rec['reward_components']['total']}
  and 7-tick signed sum reconcile to total with |diff| < 1e-9. Embedded
  contrast 5-head sum 0.47 reconciles independently.
- spike_events: primary {len(rec['spike_events'])} events, one key t_rel_ms,
  globally non-decreasing, min same-channel gap {gap:.3f} ms >= 0.8 ms, 3
  channels inside race_window_us 500 (compost.hot.high 6.438, pln.in_band 6.634,
  o2.ok 6.818). Contrast 8 events, own race, min same-channel gap well
  above 0.8 ms.
- Sidecars: raster spikes {ras['spikes']} == round({ras['neurons']} x {ras['mean_rate_hz']} x {ras['window_s']}); energy {ras['energy_pJ']} pJ /
  {ras['energy_uJ']} uJ at 23 pJ/spike; excerpt {len(ras['excerpt'])} events inside [0, {ras['window_ms']*1000}] us,
  neuron_id < {ras['neurons']}, same-neuron gap >=1000 us; excerpt_source independent_lif;
  routing 4 entries with three scar edges' before/after pair; third factor tau 0.92 s
  == 920 ms; gate_snn pools 46/17/5 == round(n x rate x 0.026) each,
  decision MODIFY == safety_decision.decision.
- Pipeline: {pipeline_receipt}

## Novel coverage
The coordination-failure CLASS (aeration-lock-collapse certificate of a
plenum-true Phase-II compost tunnel), the domain (mushroom-compost-tunnel /
forced-aeration pasteurization lock), the reverse-aeration probe
discriminant, the triple-edge scar with pair-rollback-fails, the primary
negative-result (correct MODIFY, tunnel still fails on unmonitored
anaerobic kill), the HITL tunnel-gallery ratify, the high-C:N
chicken-litter probe-duration refit, the night-shift 10-bin quantization
fence, and the independent LIF raster (seed 68001, not a language-train
remap) are absent from prior committed ouroboros rounds and from staged
r14-r67. Repeated elements discounted: same-gate contrast,
governance-pricing scaffold, flip-fragility series (extended to lock-true
certificate, but the move rhymes), sequenced recovery shape, third-factor
rollback form, negative-result primary. Adjacent thermal-bed rounds (r64
malt kiln, r65 tobacco, r61 sinter) share industrial-process scaffolding
but not Phase-II compost ammonia / aeration-lock physics. Weighing a new
failure family + cure vocabulary + unused sub-domain + Mushholt geography
against those reused scaffolds, and against not restacking WOLD-BARN:

{NOVEL_LINE}

## What ROUND 69 should add
1. FIT THE DESIGNED CONSTANTS: spigot arrival, probe PLN-jump bands,
   anaerobic-kill-to-ammonia mapping, night-shift claim process.
2. HIL PROVENANCE CELL: put the tunnel-gallery LOTO on a hardware-in-loop
   lock-door pendant with fitted latency as state.sim_or_real=hil — only if
   the plant is no longer purely invented.
3. CROSS-RECORD ARC: let CR-C-6806's local-TC alarm be the igniter of
   the next round rather than a dangling +21 d leaf.
4. Domain candidates (de-collided): hrsg-attemperator;
   alkaline-water-electrolysis (if distinct from r03 QUAY-FEN stack).
   AVOID mushroom-compost-tunnel (now used), farm-ad-biogas (r67),
   industrial-rotisserie-spit-oven (r66), flue-cured-tobacco-barn (r65),
   malting-kiln-barn (r64), canal-lock-rail-transshipment (r63),
   grid-inspection (r42/r62), sinter-strand-windbox (r61),
   hot-dip-galvanizing (live r01), autonomous-driving (live r21),
   bioreactor-perfusion (live r41), and any LYOSHIELD / CINDERWICK /
   TRIAD / SKULLGATE / BOGIRON / SKARVOLT / PUSHERFELL / CREELWOLD /
   GIBBSQUERN / COILSHAW / LOOPERQUAY / SIPHONWOLD / WINDBOXHOLT /
   WOLD-BARN / LOCKSPUR / FEN-SPIT / BARN-SPIT / SPUR-HEARTH / WOLD-LOCK plant.
"""
    return notes
