# Distillation dataset families (issue #78)

Three control-oriented families, all built on the shared oracle-grounded
envelope in `schemas/oracle-grounded-record.schema.json`, enforced by
`pipelines/oracle_contract.py`.

| Family | Generator proposes | Oracle produces the label | Status here |
|---|---|---|---|
| `neuromorphic-fault-recovery` | disturbance + a shallow prediction | `RelayReflexSimulator` (deterministic) | fully exercised |
| `snn-energy-routing-preferences` | equivalent policies | a meter reading an actual execution | exercised in `cpu_time_s`; joules unavailable |
| `moe-router-distillation-trajectories` | text/code/task contexts | the teacher model's own router | reference stand-in only; real teacher unavailable |

## The rule the envelope enforces

Generators propose; oracles decide. Concretely:

- `generator.authority` is pinned to `propose_only`.
- No oracle-measured key name (`measurements`, `outcome`, `energy_j`,
  `router_logits`, `task_quality`, `preference`, …) may appear anywhere inside
  `generator`, `scenario`, `intervention` or `candidate_prediction`.
- Every key under `candidate_prediction` is `predicted_*` (plus `rationale`,
  `confidence`, `method`), so a guess can never be read as a label.
- Producers write `validation.status = "unvalidated"`. Only
  `pipelines/validate_distill.py` stamps a verdict, and the stamp names itself.
- `oracle_contract.curation_eligible` fails closed: it needs an
  `authoritative` oracle, a `measured` result with at least one measurement,
  and a passed validation. Structural validity alone is never training-ready.

Every measurement carries `quantity`, canonical `unit`, `meter`, `measured` and
`source: "oracle"`. Energy-class quantities (`energy_j`, `energy_per_op_j`,
`power_w`) are rejected unless the meter physically measures energy. There is no
code path that turns an operation count, a synaptic-operation model or a
measured second into a joule.

### What the validator cannot check

It checks internal consistency, not authenticity. A record whose measurements
were fabricated by hand and hashed correctly is structurally indistinguishable
from one a meter produced. What defends against that is upstream: the producing
code is the only thing that writes measurements, the oracle block records the
meter probe and fingerprint, and `provenance.record_sha256` makes later
tampering visible. `validate_distill.py` catches contract violations and edited
records; it does not attest that a meter ran.

## `neuromorphic-fault-recovery`

**Oracle contract.** `pipelines/fault_recovery.py:RelayReflexSimulator`
(`oracle.type = "deterministic_simulator"`, `authority = "authoritative"` —
epic #76 admits a deterministic simulator as ground truth). It steps a
multi-channel relay on a fixed tick grid, applies the disturbance to the event
stream and thermal state, and selects an outcome. Given the same scenario and
disturbance it returns the same result on any machine. A hardware-replay oracle
would implement the same `FaultOracle` boundary; no neuromorphic board is
present here, so none was used.

**Disturbances.** `sensor_loss`, `stale_sensor`, `event_jitter`,
`burst_corruption`, `thermal_excursion`, `missing_channel`,
`malformed_spike_burst`, `delayed_result`, `temporary_saturation`.

**Outcomes**, canonical snake_case with the issue's prose spelling kept in
`result.outcome_label`: `continue`, `degrade_gracefully`, `fallback`,
`reflex_action`, `quarantine`, `fail_closed`.

**Precedence**, most protective first — the simulator stops at the first match:

1. `fail_closed` — no timely input (`delay >= hard_deadline_ms`), thermal
   shutdown, or too few healthy channels with no usable fallback.
2. `quarantine` — a malformed burst, or corruption at or above the quarantine
   ratio.
3. `reflex_action` — thermal limit crossed, or saturation held past the reflex
   tick count.
4. `fallback` — too few healthy channels, but a validated fallback source is
   available.
5. `degrade_gracefully` — staleness, jitter, drops, corruption below the
   quarantine ratio, a thermal warning, a late result, or a reduced channel
   set, with the channel budget still met.
6. `continue` — everything inside tolerance.

Every outcome carries a non-empty `result.reason_codes`. The generator's
`candidate_prediction.predicted_outcome` keys only on the disturbance kind and
ignores severity, so the corpus contains genuine disagreements;
`result.prediction_agreement` records them without ever letting the prediction
influence the label.

## `snn-energy-routing-preferences`

**Oracle contract.** A meter that reads a counter around an actually executed
workload, behind `pipelines/energy_preferences.py:EnergyOracle`:

- `RaplEnergyMeter` — `/sys/class/powercap/intel-rapl:*/energy_uj` before and
  after the workload, handling counter wraparound. Real joules. **Unavailable
  in this environment**: the counters are not readable by a non-root user
  (`Permission denied`), which `meters_report()` states verbatim.
- `RecordedEnergyMeter` — replays a measurement recorded by a real metered run
  elsewhere, keyed by candidate and workload. Fails closed on an unknown key.
- `ProcessResourceMeter` — CPU time, wall time, latency and RSS of the executed
  workload. Real measurements of a real execution, but of *time*. A corpus
  metered this way is denominated in `cpu_time_s` and says so in
  `result.cost_is_energy = false`.

**Preference rule.** `min_measured_cost_subject_to_quality_and_safety`:
among candidates with `task_quality >= constraints.quality_floor` **and**
`safety_ok`, take the lowest measured cost, ties broken by candidate id. When
no candidate is feasible the record abstains with
`NO_CANDIDATE_SATISFIES_QUALITY_AND_SAFETY_CONSTRAINTS` rather than picking a
least-bad option.

The task is a capped quadratic actuator allocation with four candidate policies
per record — an exhaustive grid search (correct, expensive), the closed-form
KKT solution (correct, cheap), a coarse grid (feasible but below the quality
floor) and an unclipped proportional split (highest quality, cheapest, and it
breaks an actuator cap). The scenario generator binds the cheapest actuator's
cap just under the share the unclipped policy would take, so that policy always
has a real safety violation. The expected preference is the KKT solution, with
the cheaper unclipped policy listed in
`preference.cheaper_but_constraint_violating` — the record shows the constraint
doing work rather than asserting it.

`check_family` re-derives the decision: it rejects a preferred candidate that is
unsafe, one below the quality floor, one whose `cost_value` disagrees with the
oracle measurement it claims, and any preference where a feasible candidate was
measured cheaper.

## `moe-router-distillation-trajectories`

**Oracle contract.** `pipelines/moe_router.py:RouterOracle`, with three
implementations:

- `TransformersMoERouter` — the real teacher. Runs a Hugging Face MoE
  checkpoint with `output_router_logits=True` and reads the per-layer gate
  logits at the final position, recording model id, revision/checkpoint, a
  SHA-256 of the model config, dtype, device, expert counts, and the
  transformers/torch versions. `authority = "authoritative"`,
  `is_llm_teacher = true`. **Not exercised here**: the local `transformers`
  install cannot import (`ModuleNotFoundError: regex`) and no MoE checkpoint is
  available offline. With the dependency missing, `available()` is false and
  `route()` raises `OracleUnavailable` — nothing downstream substitutes a guess.
- `RecordedTeacherRouter` — replays a recording from a real teacher run, keyed
  by the SHA-256 of the context, and refuses a recording that does not name its
  teacher. Fails closed on an unknown key. No recording is committed, because
  fabricating one would be exactly the thing #78 forbids.
- `ReferenceMoERouter` — a deterministic seeded top-k gate in pure Python. It
  is a real router computation (linear gate, softmax, top-k over actual
  features) but it is not a language model. `authority = "reference_only"`,
  `is_llm_teacher = false`, and `curation_eligible` rejects every record it
  produces. It exists to prove the pipeline shape end to end.

**Captured targets.** Per layer: `top_k_experts`, `router_logits` where the
oracle exposes them, `top1_top2_margin`, `routing_entropy` (nats). Per record:
`top1_expert` and `expert_agreement` across layers. `check_family` re-derives
the expert ordering from the logits, bounds the entropy by `ln(num_experts)`,
and requires `result.teacher_grounded` to follow from the oracle's authority
and `is_llm_teacher` rather than being asserted.

**Student input.** `scenario.compact_input.features` is a deliberately lossy
view of the gate input — the leading components plus tail mean/energy/max/min —
so the distillation target is not a copy of what the gate itself consumed.

## Baseline before escalation

`pipelines/router_baseline.py` implements the conventional baselines #78
requires before an SNN student is considered: a majority-class baseline,
multinomial logistic regression, and a one-hidden-layer MLP, all deterministic
and standard library, on a train/test split keyed by hashing the record id.

A lift over the majority class only counts when it clears `required_lift`, the
larger of `min_lift` and two binomial standard errors of the test accuracy. A
thin holdout can manufacture a lift out of noise — 120 random-label samples
leave a ~34-record test split on which noise alone produced a ~0.12 lift — and
the standard-error floor is what keeps that from reading as a learnable target.

`escalation_gate` turns the report into a decision:

- `not_learnable_from_compact_inputs` — no baseline beat the majority class by
  `required_lift`; do not escalate.
- `learnable_linear` — a linear model already predicts the router; an SNN is
  only justified if it beats that number.
- `learnable_nonlinear` — the MLP is meaningfully ahead of the linear model.

## The committed fixture run

`tests/fixtures/distillation-run/` is a small real run, rebuilt by
`python3 scripts/build_distillation_fixture.py --force`, with a `MANIFEST.json`
recording which oracles ran, which were unavailable, the validation totals and
the baseline report. It sets `training_ready: false` and says why. It proves the
shape end to end; it is not a corpus.

Validate it with:

```bash
python3 pipelines/validate_distill.py tests/fixtures/distillation-run
python3 pipelines/router_baseline.py evaluate \
  tests/fixtures/distillation-run/moe-router/batch-r01.jsonl
```
