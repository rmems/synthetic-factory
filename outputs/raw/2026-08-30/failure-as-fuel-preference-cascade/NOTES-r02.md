# NOTES r02 — failure-as-fuel-preference-cascade — 2026-08-30

## Protocol attestation

Two-session isolated generation. Session A staged the three rejected arms and
their diagnoses; an arm-payload-blind context bound the diagnosis handoff
(`diagnosis-handoff-receipt-r02.json`). Session B (this context) verified the
receipt digests against the staged bytes, read ONLY `diagnosis-01-r02.md`,
`diagnosis-02-r02.md`, and `diagnosis-03-r02.md`, synthesized each `chosen`
from the diagnosis narrative plus the Shared-context block, and assembled
`batch-r02.jsonl` with a mechanical script that json-loads each
`rejected-0N-r02.json` and injects it verbatim without the rejected content
entering Session B's generation context. `reward_delta` was script-computed at
assembly as chosen minus rejected per component. Every record attests
`meta.isolation: "two-session"`.

## Round contents

1. `ffpc-20260830-r02-pair01` — EAF water-cooled panel leak hot-repair
   authorization. Failure class: bright-line standard read down to an advisory
   on survivorship evidence (precedent with no attempt denominator) plus a
   verification aimed at the wrong object (dye penetrant on the patch, not the
   leak-extent hypothesis). Chosen verdict: REJECT — the round's
   refuse-a-proposed-repair pair; the compliant tap-out/localization path finds
   a second concealed defect and lands degraded (16.5 h outage, four late
   heats, penalties paid).
2. `ffpc-20260830-r02-pair02` — substation transformer heavy-lift
   authorization. Failure class: rating-basis confusion (vertical-basis sling
   WLL consumed at a 60.3-degree geometry — a plausible factor-2 error that no
   absurdity screen catches). Chosen verdict: MODIFY — spreader-beam re-rig,
   per-leg load cells, mandatory hover; the weather window is genuinely lost
   and four days of crane standby are paid with the slings intact.
3. `ffpc-20260830-r02-pair03` — digester FOG co-digestion end-of-month push.
   Failure class: objective myopia amplified by stale actuator context and a
   cosmetic-trim pseudo-modification. Chosen verdict: MODIFY — verified pump
   changeover, titration hold, capped increase, and an auto-revert tripwire
   that actually fires; the month closes honestly short of target.

All three chosen trajectories land degraded (late heats with penalties, a paid
4-day standby, a missed monthly KPI), covering round 1's near-miss-repair
densification target; pair 1 covers the refuse-a-proposed-repair direction and
pair 2 the plausible-magnitude unit/basis confusion resolved by an independent
observation.

## Self-critique and residual weaknesses

- Chosen gate verdicts this round are REJECT/MODIFY/MODIFY; combined with
  round 1 (MODIFY/REJECT/ACCEPT) the corpus still has only one ACCEPT-side
  repair, and none in which ACCEPT is correct under active commercial
  pressure.
- All three scenarios remain single-agent, single-gate decisions: no contested
  authority, no mid-action handover, no multi-party mandate conflict. This is
  now the oldest unaddressed weakness (flagged in r01).
- Realized reward deltas (6.4, 6.1, 6.9) again overshoot the diagnosis targets
  (5.1, 4.7, 4.9) because the rejected totals sit deeper in the negative range
  than Session A's targets assumed; the two-session protocol gives Session B
  no way to calibrate chosen totals against unseen rejected totals except
  through the diagnosis narrative.
- Degraded-landing numbers are still authorially tidy (exactly 4 late heats,
  exactly 4 standby days, a round 4100 Nm3 shortfall); a discriminator could
  learn residual tidiness even though the outcomes are no longer uniformly
  rosy.
- No spike_events streams on the chosen arms; behavioral contrast rides
  entirely on executed_action and future_outcome. Deliberate this round: with
  the rejected arms unseen, a chosen-side stream risks an unalignable list
  residual at the arm gate, so adding streams safely needs Session A to
  declare stream shape in the diagnosis envelope first.

## Next densification target

Multi-party gates: one pair where the correct verdict is ACCEPT under explicit
deadline pressure (teaching that MODIFY/REJECT is not a universal safe
default), one contested-authority case where two agents hold conflicting
mandates over the same actuator and the gate must arbitrate provenance, and a
handover-boundary failure where the load-bearing evidence expires mid-action.
If Session A adds a spike-stream shape declaration to the diagnosis envelope,
put the first chosen-side spike_events contrast on the tripwire pair.

Novel coverage: 65%

Basis: relative to all committed rounds of this factory, all three plant
domains are new (electric steelmaking, heavy-lift rigging, anaerobic
co-digestion), and the failure mechanisms are substantially new (survivorship
precedent against a bright-line clause; plausible-magnitude rating-basis
confusion; stale-mirror context loss with a cosmetic-trim pseudo-MODIFY). The
degraded-landing repair direction and the refuse-a-repair verdict are new.
Overlap that keeps the estimate below 70: the commercial-pressure-versus-gate
frame recurs in every pair of both rounds, pair 2's basis confusion is a
cousin of r01's unit-frame confusion, and pair 3's armed tripwire echoes r01
pair 3's ACCEPT-with-tripwires.
