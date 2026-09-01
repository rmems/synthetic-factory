# NOTES r03 — failure-as-fuel-preference-cascade — 2026-08-30

## Protocol attestation

Two-session isolated generation. Session A staged the three rejected arms and
their diagnoses; an arm-payload-blind context bound the diagnosis handoff
(`diagnosis-handoff-receipt-r03.json`). Session B (this context, fresh, with
no Session A memory) verified the receipt digests and byte counts against the
staged bytes, read ONLY `diagnosis-01-r03.md`, `diagnosis-02-r03.md`, and
`diagnosis-03-r03.md`, synthesized each `chosen` from the diagnosis narrative
plus the Shared-context block, and assembled `batch-r03.jsonl` with a
mechanical script that json-loads each `rejected-0N-r03.json` and injects it
verbatim without the rejected content entering Session B's generation context.
`reward_delta` was script-computed at assembly as chosen minus rejected per
component, reconciled within 1e-6. Every record attests
`meta.isolation: "two-session"`.

## Round contents

This round lands all three of round 2's densification targets:

1. `ffpc-20260830-r03-pair01` — BESS enclosure off-gas alarm and
   suppression-discharge authorization. Failure class: an over-refusal — a
   two-detector confirmation ritual imported from occupied-building practice
   into a decision class the site policy had carved out, priced on only one
   side of a 190k-versus-9.2M bet, demanding confirmations arithmetically
   slower than the 2-to-8-minute propagation window. Chosen verdict:
   ACCEPT under explicit deadline pressure — the corpus's first
   ACCEPT-is-correct repair with active commercial cost, landing degraded
   (module scrapped, 10-day re-commissioning, refill and shortfall paid).
2. `ffpc-20260830-r03-pair02` — contested authority: a statutory methane hold
   and a signed demand-response mandate contending for the same sole district
   fan. Failure class: credential-versus-hazard-class arbitration — signed,
   fresh, priority-high beats unsigned statutory, with a dilution-dependent
   falling trend read as near-clearance. Chosen verdict: REJECT — arbitrate
   by mandate class first, answer the dispatch with genuine substitute
   curtailment, forfeit most of the 8400 USD honestly.
3. `ffpc-20260830-r03-pair03` — confined-space re-entry after a mid-job
   interruption spanning a shift handover. Failure class: evidence expiring
   mid-action — a certificate voided by the permit's own validity clause
   treated as merely stale, an unlogged verbal note preferred over the
   recorded interruption, monitors-during substituted for testing-before.
   Chosen verdict: MODIFY that blocks entry until the evidence is restored;
   the first low-point sample genuinely fails at 19.2 percent oxygen,
   vindicating the hold, and the hydrotest slips about two hours.

Chosen verdicts this round are ACCEPT/REJECT/MODIFY — with rounds 1 and 2 the
corpus now covers every verdict class in both flawed and repaired direction,
and pair 1 closes the standing no-ACCEPT-under-pressure gap.

## Self-critique and residual weaknesses

- Realized reward deltas (7.1, 7.2, 6.1) again overshoot the diagnosis
  targets (5.3, 5.8, 4.9), for the structural reason noted in r02: Session B
  cannot calibrate chosen totals against unseen rejected totals, and Session
  A's rejected arms land deeper negative than its own targets assume. If this
  matters downstream, Session A should start declaring the rejected total's
  intended band in the diagnosis envelope.
- Degraded-landing numbers remain authorially tidy (a 105-minute delay, a
  1.9 h slip, a net 750 USD): a discriminator could still learn residual
  tidiness even though outcomes are honestly degraded.
- Still no spike_events streams on either arm; behavioral contrast rides
  entirely on executed_action and future_outcome. Same reason as r02: without
  a Session A stream-shape declaration in the diagnosis envelope, a
  chosen-side stream risks an unalignable list residual at the arm gate.
- Pair 2's chosen gate reads as globally wise partly because the state
  discloses the onboarding gap; a harder variant would omit that disclosure
  and make the gate discover the precedence-table staleness itself.
- All three repairs succeed on their first attempt at the repaired path
  (discharge works, hold clears, re-test passes on the second sample); the
  corpus still lacks a chosen arm whose correct decision is followed by a
  partial failure of the repair itself, handled well.

## Next densification target

A correct-gate-then-imperfect-execution pair: the chosen verdict is right but
the repaired path itself degrades mid-execution (a suppression valve that
sticks, a substitute curtailment that underdelivers, a re-test instrument that
fails calibration) and the trajectory must recover inside the same record —
teaching that a good gate does not guarantee a clean run. Secondarily: a
Session A envelope extension declaring rejected-total bands and a spike-stream
shape so Session B can calibrate deltas and add the first chosen-side
spike_events contrast without risking list-alignment failures.

Novel coverage: 55%

Basis: relative to both committed rounds, all three plant domains are new
(grid-scale battery storage, gassy underground coal ventilation, specialty
chemicals confined-space permits), and the failure mechanisms are new
(imported confirmation ritual with one-sided expected-loss pricing;
credential-versus-hazard-class mandate arbitration; validity-clause voiding
across a shift handover). The multi-party contested-actuator frame and the
ACCEPT-under-deadline repair direction appear for the first time. Overlap
keeping the estimate at 55: the commercial-pressure-versus-gate frame recurs
in every pair of all three rounds, pair 1's base-rate-generation error is a
cousin of r01's certificate-as-health trust, pair 3's void-certificate logic
is adjacent to the same r01 pair, and the degraded-landing repair grammar now
repeats from r02.
