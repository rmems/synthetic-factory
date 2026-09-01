# Neuromorphic Event + Language Bridge — NOTES round 4
Run: 2026-08-30 · Factory: neuromorphic-event-language-bridge · Output: `batch-r04.jsonl` (3 paired artifacts, 6 ThalamicTrajectories)

## Context / de-duplication
Prior corpus read: `NOTES-r02.md`, `NOTES-r03.md` (the two newest committed), and `batch-r03.jsonl` skimmed for
shape and scenario dedup. NOTES-r03 flagged five round-4 targets; this round stages all five: (1) the gate_snn
input→output volley pair at raster resolution under the tightened contract (a1 — with an honest scope note below);
(2) the TOTAL loss discovered only retrospectively (a2); (3) the magnitude-defeating insider forcing a
pure-custody case (a3); (4) the harvest of r02-a3's poisoned-frame hard-negative archive, the corpus's oldest
unharvested recorded obligation (a1, discharged exactly as recorded: the archive becomes the re-qualification
suite); (5) a serialized behavioral-distribution artifact whose statistic recomputes from the record's own values
(a3's two-sample KS block). It also closes r03 thin-item (v): the eligibility trace stops being declared
machinery and becomes the plot (a1's tau_e is the root cause, the ordered fix, and the validated cure). No
modality family repeats r01–r03 or the r1–r12 table.

## Round 4 batch summary (3 pairs, 6 trajectories)

| id | modality (NEW family) | domain | decisions | headline |
|----|----------------------|--------|-----------|----------|
| nelb-20260830-r04-a1 | SNN replay-harness / qualification telemetry (archive custody, replay block summaries, serialized output volleys, tau_e config events, shadow-audit summaries) | H7-vod-2026-0901: VOD-SNN-7 autonomy re-qualification using the r02-a3 hard-negative archive; retrained gate passes 63/63 hard negatives but goes late on true seeps because tau_e 2.5 s outlived the 2 s replay spacing | MODIFY (+0.46) / ACCEPT (+0.41) | archive obligation discharged + spike-in/spike-out re-staged: raster = held-out input frame TP-H3, its output volley (n2 first spike 4.3 ms, 7/8) serialized in the main stream with the producing spec (`classifier_snn`) in the record; the RQ-1 late volley (7.8 ms) and RQ-2 pass volley bracket the tau_e fix; first train/test split hygiene enforced by a safety gate; earned bounded ACCEPT with an explicit chemistry scope limit |
| nelb-20260830-r04-a2 | pharmaceutical cold-chain telemetry (compressor duty/suction cloud witness, reconstructed freeze windows, RFID logger-swap portal pairs, acceptance PDFs, sero/revax program events) | CCF-2026-0518: depot manager launders 66 days of freeze evidence with conditioned twin loggers; 128.4k doses ship clean, 96.7k administered; discovery is a returned carton 11 days after the last freeze window | REJECT (+0.33) / MODIFY (+0.36) | the corpus's first TOTAL loss: no defense engages inside the window, the attack fully succeeds, and the discovery gate prices the whole exposure (96.7k administered, 67.9-day detection gap as realized negative components) while refusing to let falsified data bound its own blast radius — recall scoped by carrier manifests × reconstructed windows only; the notification gate expands scope on custody grounds but tiers the remedy (infant revax-all, serology triage, monitoring floor) instead of blanketing |
| nelb-20260830-r04-a3 | stack-gas CEMS custody telemetry (config hash chain, cal-gas cylinder ledger, RATA windows, behavioral sweeps, DAS forensics, sealed FTIR reference) | CEM-2026-0221: technician compensates EVERY physics channel (k=0.83 on SO2 ppm and cal responses, matched sorbent logs, pre-RATA reverts, maintenance-distribution touch timing) | REJECT (+0.49) / REJECT (+0.44) | the hardest r03 adversary class staged: magnitude, mass balance, RATA, and the behavioral head all read clean, and the certification gate refuses to sign on custody structure alone — revert pairs bracketing the audit calendar + 19 days of cal passes citing a vendor-emptied cylinder — BEFORE any corrected-magnitude evidence exists (the k-script recovery day 296 confirms an inference made day 292.6); the behavioral null is serialized as a recomputable KS artifact (D=0.2302, p=0.600 from the record's own inter-arrivals); the disclosure gate then refuses the quiet-amendment path (false instruments + concealment clock) |

Decision spread: MODIFY / ACCEPT / REJECT / MODIFY / REJECT / REJECT — 1A/2M/3R, a new multiset (r01/r02 were
1A/3M/2R, r03 was 2A/2M/2R). The one ACCEPT is an earned, bounded accept with a shadow-audit tripwire and an
explicit statement of what the qualification does not cover.

## Raster sidecar (second round under the tightened contract)
Every record carries `raster` + top-level `gate_snn` + `gate_compute`: windows 32/42/26 ms; `window_s ==
window_ms/1000` exactly; `spikes == round(neurons·rate·window_s)` with zero slack (60/63/39 at 62.5/60.0/75.0 Hz
over 30/25/20 neurons); `energy_pJ = spikes·23` and `energy_uJ = spikes·23e-6` exact (1380/1449/897 pJ); routing
source/target + 3-entry tables + `third_factor` on all three (modulators da.replay_outcome_error /
na.retro_witness_salience / ach.custody_conflict_gate; τe 0.6/1.2/2.2 s as consistent `tau_e_s`+`tau_e_ms`
pairs — a1's 0.6 s is the story's corrected value, the first decision-relevant eligibility constant); excerpts are
integer `t_us`, in-window, `neuron_id`-bounded, sorted, full-window by construction, every spike carrying an
amplitude (units declared per raster). ISI histograms are computed from the full-window per-neuron trains with
explicit ≥1 ms bins; counts sum to `spikes − distinct_active_neurons` (30/38/19); all same-neuron gaps ≥1.05 ms
pre-round, ≥1000 µs serialized. Raster anchors: a1 = the exact held-out input frame whose serialized output
volley is in the main stream (decision-time frame); a2 = the earliest-detectable icing frame in the sealed
FrostWatch replay (fixing the priced detection gap); a3 = the custody-audit join frame where revert pairing
crossed threshold. `gate_snn` on all three (quota needs one): 5/5/5 populations, every rate-declaring
population's budget exact against its decision window, decisions MODIFY/REJECT/REJECT matching each lead
trajectory; a3 carries the zero-weight timing population with the unreachable threshold (r03's asymmetric-null
rule, now paired with the serialized artifact it governs). `gate_compute.per_check` windows 32–48 ms, budgets
exact (896+576 / 1152+540 / 1000+750), totals 33856/38916/40250 pJ with matching µJ. Main streams: 50/52/50
events, strictly increasing `t_rel_ms`, one clock domain each (`meta.clock_domain`), per-channel refractory
floors declared in encoder_spec and asserted at build time; native-unit aliases t_hr/t_day/t_day.

## Self-critique

### Edge cases added vs still thin
- **Added:** first TOTAL loss (attack fully succeeds; zero defense events inside the window; discovery
  out-of-band and late; full-window exposure priced as realized negative components inside a correct REJECT);
  first falsified-data-cannot-scope-its-own-blast-radius ruling (depot records ruled non-evidentiary for scoping
  while remaining evidence OF the fraud — reused in t2 against the subtler assay-sample laundering); first
  custody-only certification refusal made BEFORE any magnitude evidence exists, with the confirming forensics
  arriving four days later (decision-before-derivation as event order); first serialized, recomputable behavioral
  null (two-sample KS D and p computed from the record's own 14+36 serialized inter-arrivals, with the formula
  in-record); first decision-relevant eligibility trace (tau_e as root cause → ordered fix → validated cure, with
  the residual-eligibility measurement 0.45 on-stream); first train/test split hygiene enforced by a gate
  (sequestered frames with day-0 hashes, leakage refused); first revert-pairing custody motif (A→B→A hash
  excursions bracketing an announced audit calendar) and first stale-cylinder ledger contradiction (record vs
  unwritable vendor lifecycle); first tiered-remedy design with asymmetric-risk floors (infant revax-all,
  serology triage, monitoring floor validated at day-150); first false-instrument/concealment-clock disclosure
  gate; first earned ACCEPT with an explicit qualification scope limit and revert tripwire; archive-harvest
  obligation discharged exactly as recorded.
- **Still thin:** (i) the three-party collusion including the infra owner (r12 gap 3) is now the OLDEST open
  flagged gap — the only governance-recursion item never staged in any window; (ii) the corpus has intent-PENDING
  and referral patterns everywhere but zero exonerations: a wrongful-attribution case where the obvious suspect
  is innocent and the gate must refuse the easy referral is unwritten; (iii) a2's systemic fix (logger custody
  attestation + vendor-cloud cross-check at acceptance) and a1's 90-day audit close-out and unqualified poison
  class (H2S sulfidation) are new recorded follow-on obligations; (iv) every t2 this round is a governance gate
  (authority vote / notification scope / disclosure) — a shape repetition across the round's pairs; (v) no round
  yet stages an ACCEPT-heavy defensible distribution; with 3R this round, the refusal prior risks calcifying.

### Realism of noise / temporal fidelity
- Strong: a2's total loss is decodable from the stream alone (zero defense events between comp.suct day 9.31 and
  ret.carton day 70.1; log.pdf flat means bracketing cr2.freeze minima; comp.duty adaptation 36→71% snapping to
  44 at the unrelated day-67 repair); a3's case is carried by joins a reader can perform on serialized fields
  (from_hash/to_hash returning to 3f21 exactly 0.9 days before each rata.win; cal.chk cylinder=EB-4471 events
  after the RETURNED_EMPTY ledger event; the REJECT preceding K_SCRIPT_RECOVERED); a1's two serialized volleys
  bracket the tau_e correction on the same lead neuron (7.8 → 4.3 ms), and the eligibility bleed has an on-stream
  measurement (0.45) tied to the 2.5 s constant and 2 s spacing.
- **Gaps, honestly:** (i) stream amplitudes remain authored constants (a3's final KS D is the one computed
  exception) — the draw-order documentation covers rasters and the KS artifact only; (ii) heavy thinning persists
  (5 of ~6400 SO2 hourly averages, 6 of 290 cal checks, 7 of 66 duty nights, 2 of 97 volleys); (iii) a2's CR-2
  thermal model is referenced with its envelope, not serialized — the freeze-window reconstruction cannot be
  recomputed from the record; (iv) the a3 KS p uses the asymptotic Stephens approximation at n=14/m=36 (declared
  in-record; exact small-sample p is not claimed); (v) `classifier_snn` (the spec that produced a1's volleys) is
  a free-form block — internally consistent but not validated by the gate_snn budget machinery, so the
  input→output pair's producing spec is contract-checked only by review.

### Training value (SNN/LSM + agentic)
Distillation targets this round: end-to-end gas head (raster frame → serialized volley with architecture label);
qualification-margin head over conjunctive margins with holdout integrity; eligibility-bleed predictor
(tau_e × replay spacing × block adjacency → latency inflation, supervised by the 2.5 s failure and 0.6 s cure);
laundering detector via co-movement violation (reported trace vs compressor duty vs suction) plus
variance-collapse against a reference room; pairing-cadence head (twin-asset transits × download calendar ×
record-gap coincidence); blast-radius policy (custody-broken record-keeper → scoping-source whitelist +
full-window prior); tiered-remedy head (monotone intensity over calibrated exposure probability with
asymmetric-risk floors); detection-gap pricing (earliest-detectable frame vs actual discovery); revert-pairing
head (hash excursion geometry vs audit calendar); ledger-join head (serial × lifecycle-date contradictions,
zero physics); certifiability policy (custody-intact ∧ lineage-paired ∧ contradiction-free, with magnitude
agreement necessary-but-never-sufficient); serialized-null verifier (recompute D/p from stored samples, confirm
zero-release-weight routing); disclosure-clock head (knowledge-of-falsity starts a promptness clock reporting
calendars cannot satisfy). Agentic value concentrates in three patterns: pricing a correct decision against the
losses it inherits without hindsight blame, refusing to certify or scope from records the suspect could write,
and binding one's own earned accepts with tripwires and explicit scope limits.

## What round 5 should add (next densification target)
1. **Three-party collusion including the infra owner** (r12 gap 3): the last governance-recursion item, now the
   corpus's oldest open flagged gap — natural host: a case where the telemetry vendor (the "unwritable witness"
   this round leaned on twice) is itself a party, forcing defense onto witnesses nobody in the collusion set can
   write.
2. **An exoneration**: the obvious suspect is innocent (e.g., the a3 technician's access was shared, or a
   parallel actor framed the referral target); the gate must refuse the easy referral against social pressure —
   the corpus's intent-PENDING machinery has never once resolved to innocence.
3. **An ACCEPT-heavy defensible round** (e.g., 3A/2M/1R with every accept earned and bounded) so the
   gate-distribution prior does not calcify toward refusal.
4. **Serialize a reconstruction model**: stage one record whose physical model (a2's thermal envelope class) is
   serialized well enough to recompute the reconstruction from the record alone, closing the recurring
   referenced-not-serialized gap.
5. **Vary the t2 gate shape**: at least one companion trajectory that is an operational/execution gate rather
   than a governance gate.

## Verification
`batch-r04.jsonl`: 3 lines, each `json.loads`-clean (allow_nan=False), 39.0/40.7/40.4 KB. Repo gates run over
the staged bytes before publish: `check_records.check_jsonl` with `FactoryStaging(enabled=True)` → 0 errors,
0 warnings, kinds `{bridge_pair: 3}`; `round_txn_raster.validate_bridge_envelope` → no errors (raster + gate_snn
envelope, third_factor, routing tables); `curate_bridge.raster_status` per record → zero reason codes,
raster/gate_snn present and valid on all three; `curate_bridge.curate_record(require_raster=True,
require_routing_table=True)` → 3× retain; `verify_execution.verify_batch_for_frontier(strict=True)` → 3
verified, 0 inconclusive, 0 failed. Build-time asserts (in-generator): strict global time order; per-channel
refractory floors from each encoder_spec; ≥48 events per stream (50/52/50); excerpt t_us integer bounds, neuron
bounds, sort, and 1 ms per-neuron floor on serialized values; ISI-histogram count identity (30/38/19 = spikes −
active); spike budgets exact via Fraction arithmetic for raster, every rate-declaring gate_snn population, and
every gate_compute check; energy pJ/µJ exact; reward totals equal exact two-decimal component sums with per-tick
streams summing per-component exactly (+0.46/+0.41/+0.33/+0.36/+0.49/+0.44); gate_snn decisions match each lead
trajectory's safety_decision; `state.sim_or_real="designed"` on all six trajectories; `meta.round=4` everywhere;
no EXPLICIT_ORDER_KEYS or per-event clock keys; no hidden-reasoning keys; no `provenance` objects and no 'real'
claims; all 9 record/trajectory ids globally unique; the a3 KS artifact's D/p recompute exactly from its
serialized samples (asserted). Seeds 20260846/20260848/20260850 (rasters) + the recorded 20260851-family seed
for the KS samples, MT19937, draw order documented per encoder_spec (stream amplitudes are authored constants —
noted above as the standing realism gap).

Honest novelty accounting: 3/3 modality families are new; all five inherited targets are staged; and the round's
core structures (total loss with retrospective-only discovery, blast-radius scoping rule, pre-magnitude custody
refusal with decision-before-derivation ordering, recomputable serialized null, decision-relevant eligibility
trace, split hygiene, revert-pairing and stale-ledger custody motifs, tiered remedy with asymmetric floors,
concealment-clock disclosure gate, bounded earned accept) are firsts. Against that: the input→output volley
pair is a revival of r02-a3's pattern (its new content is the tightened-contract serialization plus the
producing spec, not the idea); the asymmetric-null rule, custody-freeze, unread-witness, pairing-structure,
intent-PENDING, cross-round-harvest, decision-code/thinning/per-tick vocabulary, and hash-sealing machinery are
all carried (second-to-fourth uses); and the three t2 gates repeat one governance shape. Net: a bit under half
the round's scenario/edge mass is genuinely novel.

Novel coverage: 45%
