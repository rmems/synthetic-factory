# NOTES r01 — failure-as-fuel-preference-cascade — 2026-08-30

## Protocol attestation

Two-session isolated generation. Session A staged the three rejected arms and
their diagnoses; an arm-payload-blind context bound the diagnosis handoff
(`diagnosis-handoff-receipt-r01.json`). Session B (this context) verified the
receipt digests, read ONLY `diagnosis-01-r01.md`, `diagnosis-02-r01.md`, and
`diagnosis-03-r01.md`, synthesized each `chosen` from the diagnosis narrative
plus the Shared-context block, and assembled `batch-r01.jsonl` with a
mechanical script that json-loads each `rejected-0N-r01.json` and injects it
verbatim without the rejected content entering Session B's generation context.
`reward_delta` was script-computed at assembly as chosen minus rejected per
component. Every record attests `meta.isolation: "two-session"`.

## Round contents

1. `ffpc-20260830-r01-pair01` — kraft recovery boiler firing-rate gate.
   Failure class: provenance-by-format (valid certificate + in-range frozen
   value + health-service OK trusted over behavioral liveness). Chosen verdict:
   MODIFY (cap below the interlock boundary, verify the frozen channel first).
2. `ffpc-20260830-r01-pair02` — adaptive radiotherapy plan-of-the-day gate.
   Failure class: modification-by-truncation (out-of-tolerance correction
   clamped to the ceiling on a broken registration reference chain). Chosen
   verdict: REJECT (evidence-integrity stop, re-register, reimage, verify).
3. `ffpc-20260830-r01-pair03` — tailings storage facility storm routing gate.
   Failure class: unit-frame confusion amplified by refusal-as-safe-default
   (legacy inches mapping over an in-band millimetre declaration; the refusal
   branch was the deteriorating one). Chosen verdict: ACCEPT with tripwires.

The three chosen gate verdicts span MODIFY, REJECT, and ACCEPT, including the
rarer repair direction in which the correct gate accepts an action the failed
gate refused.

## Self-critique and residual weaknesses

- Chosen outcomes lean on clean, round outcome metrics (1.05 m minimum
  freeboard, 16 minute delay, 197500 m3) rather than noisy telemetry; a
  discriminator could learn "tidy numbers means chosen".
- All three scenarios are single-agent, single-gate decisions; no contested
  authority, handover, or multi-party mandate pressure.
- Chosen rewards are uniformly strong positives. Only record 2 pays a visible
  component penalty (efficiency minus 0.1); none of the repairs lands with a
  materially degraded task outcome.
- Because Session B never sees the rejected arms, lexical contrast is enforced
  only by the independent-arm gate, not by deliberate authorial phrasing
  distance; realized reward deltas (5.15, 4.1, 5.25) overshoot the diagnosis
  targets (3.2, 3.0, 3.5) since the rejected totals sit deeper in the negative
  range than the targets assumed.
- No spike_events streams on the chosen arms this round; behavioral contrast
  rides entirely on executed_action and future_outcome.

## Next densification target

Near-miss repairs: chosen trajectories that are correct yet land degraded (a
partial burn-down, a deferred fraction, a tripwire that actually fires and
stops routing), one pair in which the correct verdict is refusing a proposed
*repair*, and a unit-confusion case where the wrong value is plausible (factor
2, not factor 25) so the plausibility screen must lean on the independent
observation instead of absurdity.

Novel coverage: 70%

Basis: relative to all committed rounds of this factory (the 2026-08-17
windows), all three plant domains are new (kraft chemical recovery, adaptive
radiotherapy delivery, tailings storm-water routing), and two of three failure
mechanisms are new (credential-versus-liveness masking; clamp-to-tolerance).
The unsafe-refusal direction and freeboard hydraulics partially overlap the
earlier flood-spillway pre-release and refusal-override pairs, which keeps the
estimate below 80.
