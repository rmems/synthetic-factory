# Oracle-grounded neuromorphic datasets

Implements the simulation-grounded half of epic #76 (issue #77): five dataset
families in which a **generator proposes** and an **oracle measures**.

```text
generator -> scenario / intervention -> oracle execution -> measured result
          -> validation -> curation
```

A generator may author scenarios, perturbations, interventions, questions, and
candidate predictions. It may never author a measurement. That rule is enforced
by code, not by convention — see [Separation](#how-the-separation-is-enforced).

## Status of the named oracles

Issue #77 names six ground-truth runtimes. **None of them are bundled or bound
by default in this repository**, which the repo's own harvest notes already
record ("No crates.io `neuromod` / `axon-encoder`",
`experiments/2026-08-17-grok-census.md`). Runtime binding, rather than ambient
`PATH` membership, is the only availability fact retained in canonical data.

Rather than fabricate their output, this PR implements the *boundary*:

| Family | Named oracle (issue #77) | Bound here? | What ran instead |
|---|---|---|---|
| `spike-encoder-equivalence-pairs` | `axon-encoder` | no | reference encoder bank |
| `neuron-dynamics-counterfactuals` | `neuromod` | no | reference adaptive LIF |
| `synaptic-delay-causal-trajectories` | `synaptic-mesh` + runtime | no | reference delay mesh |
| `neuromodulator-credit-assignment` | `limbic-critic` → `plasticity-lab` | no | reference critic → reference three-factor STDP |
| `temporal-memory-spike-challenges` | validated recurrent SNN | no | reference recurrent delay-loop network |

Every record produced without a bound runtime carries:

```json
"oracle": {
  "implementation": "reference",
  "authority": "reference-simulator",
  "requested_runtime": ["axon-encoder"],
  "runtime_bound": false,
  "availability": { "unbound": ["axon-encoder"], "runtimes": [ ... ] }
}
```

and `validation.publishable` is **false**, with the reason spelled out. A
reference simulator is a real measurement of a real (small) model; it is not a
measurement of the runtime the issue names, and `record.publishability()`
refuses to let it claim otherwise. Nothing here is publishable to the Hugging
Face Hub on the strength of a reference run.

### What that leaves unverified

* Whether these encodings, neuron dynamics, delay effects, modulator levels, or
  retention horizons agree with `axon-encoder`, `neuromod`, `synaptic-mesh`,
  `limbic-critic`, `plasticity-lab`, or a validated recurrent SNN. **Nothing in
  this PR tests that**, and no record claims it.
* Absolute physical calibration. Voltages are normalized so that threshold is
  1.0; reward is normalized to [0, 1]. Only the energy figure is anchored to an
  external constant (23 pJ/spike, the Loihi-2-class number already used by
  `schemas/raster.schema.json`).

What *is* verified is in [Tests](#tests): determinism, reproducibility from the
stored scenario, hash and provenance integrity, the generator/oracle split, the
fail-closed curation gate, and each family's own invariants.

## Binding a real runtime

An oracle is bound by pointing an environment variable at a command that
speaks the `sf-oracle/1` protocol. No code change is needed.

```bash
export SF_ORACLE_AXON_ENCODER_CMD="axon-encoder serve-oracle"
python3 pipelines/oracle_generate.py --family spike-encoder-equivalence-pairs \
    --require-runtime outputs/oracle-grounded/2026-09-01
```

Request on stdin:

```json
{"protocol": "sf-oracle/1", "oracle": "axon-encoder",
 "family": "spike-encoder-equivalence-pairs",
 "request": {"configuration": {...}, "data": {...}}}
```

Response on stdout:

```json
{"protocol": "sf-oracle/1", "runtime_version": "1.2.3",
 "runtime_commit": "<7-64 hex revision>", "measured": {...}, "units": {...}}
```

A bound oracle **never** silently degrades to the reference implementation.
Nonzero exit, timeout, non-JSON output, a protocol mismatch, a missing
`runtime_version`, a missing or invalid 7-64 digit hexadecimal
`runtime_commit`, a non-finite number, empty units, or an empty measurement all
raise
`OracleError`, and the record is dropped rather than filled in. The chain
family binds each stage separately, so a deployment with only `limbic-critic`
available produces `implementation: "mixed"` and stage-level attribution.
Protocol stdout is capped at 8 MiB and stderr at 1 MiB while the child runs, so
an untrusted adapter cannot turn validation into an unbounded capture. External
stderr and the configured argv are diagnostic input only and are never copied
into canonical records or error messages.

The environment variable name is derived mechanically:
`SF_ORACLE_` + the runtime name upper-cased with `-` replaced by `_` + `_CMD`.

## How the separation is enforced

| Rule | Mechanism |
|---|---|
| A generator cannot author a measurement | generator subtrees are scanned for reserved keys (`measured`, `result`, `ground_truth`, `produced_by`, …) at build time and at validation time |
| A measurement cannot be back-written into a scenario | `proposal_hash` covers exactly `{generator, scenario, intervention, candidate_prediction}` and is recomputed on validation |
| A seed cannot be rewritten around a retained proposal | the canonical generator block and all three proposal sections are replayed from `generator.seed`; run validation also derives that seed from the manifest master seed, family, and record index |
| A result cannot be edited after the fact | `result_hash` covers exactly `result` |
| A result cannot be misattributed | `result.produced_by` must equal `oracle.id` |
| A reference run cannot be relabelled as a runtime measurement | `oracle.implementation` must agree with every `oracle.stages[*].implementation`, canonical stage identity and adapter version, runtime executable evidence, the current reference `module_digest`, and `oracle.availability` |
| Curation fails closed | a missing, empty, or unattributed `result` is an error, never a warning |
| A generator's guess is never truth | `candidate_prediction.kind` must be `non_authoritative_guess`; it is scored against the oracle into `validation.candidate_prediction_correct` |
| A rejected record cannot rewrite its own reason | stored `validation.reasons` must equal the recomputed findings |
| A redundant training label cannot drift from its evidence | encoder winners, neuron deltas, mesh delays, every plasticity delta and post-update weight, every memory response/ambiguity label, and temporal dependence are recomputed from retained primitive measurements |
| Schema requirements cannot be treated as prose | the stdlib-only validator executes every assertion keyword used by the base and family schemas before family checks run |
| Host discovery cannot perturb canonical bytes | records retain only runtime name, binding environment key, and bound state; `PATH` membership and operator notes remain diagnostics from `probe_runtime()` |
| A command binding cannot leak its arguments | stage provenance retains only a basename-level executable identity; argv and external stderr are never copied into records or validation errors |

## Reproducibility and provenance

Records are byte-reproducible. The generator uses an explicit SplitMix64 stream
rather than `random.Random`, the proposal is rounded to canonical precision
*before* the oracle sees it, and all JSON is emitted canonically (sorted keys,
six-decimal floats, no NaN/Inf).

`pipelines/oracle_validate.py --reproduce` first requires a lowercase 40- or
64-hex source commit that resolves to that exact commit object in this Git
repository. For reference and mixed records it also requires the
stored top-level and stage-level module digests to equal the current reference
implementation before rebuilding the oracle request. It then verifies that the
rebuilt configuration matches the retained configuration, re-runs the oracle,
compares the replayed stage identities, and finally compares `result_hash`. A
requested replay that is unavailable is an error, not a successful
verification. Accepted and rejected filenames are also checked against each
record's recomputed verdict, and mixed runtime/reference chains are reported
separately from named runtimes.

Before any record is trusted, the validator pins the run root with a directory
descriptor, rejects symlinks, hardlink aliases, non-regular files, escaping or
noncanonical manifest paths, and excessive file sizes/counts/nesting, then reads
each manifest-declared file exactly once through no-follow descriptor-relative
traversal. Digests, nonblank counts, record validation, duplicate-id detection,
and reproduction all consume those captured bytes rather than reopening a path.
The manifest's round, master seed, per-family proposal count, family/file layout,
derived record seeds and ids, commit, dirty state, current reference module
digest, runtime availability, and per-family summaries are cross-checked against
that same snapshot. An authenticated run must declare at least one family and
one payload record, and both generation and validation enforce a 100,000-record
whole-run ceiling rather than applying the limit independently to each family.

Family validation also bounds every retained event to its declared physical or
simulation domain: encoder event channels and sample times, neuron spike times,
mesh arrivals, credit-assignment pre/behavior spikes, and temporal-memory latch
and response times must all fit the scenario window they claim to measure.

This is an integrity boundary, not an origin attestation. `manifest.json` is
unsigned: a local writer that can replace every record can also recompute every
digest and summary coherently. Likewise, `sf-oracle/1` authenticates response
shape and retained code identity but supplies no external signature, hardware
attestation, or independent proof that a command really is the runtime named in
its binding. Named-runtime records remain explicit operator claims; the code
does not upgrade them to externally attested measurements.

Every accepted record retains:

* `oracle.repo`, `oracle.commit`, `oracle.dirty` — the tree the oracle ran from.
  A record whose commit is not a lowercase 40- or 64-hex identifier resolving
  to that exact commit object in the local source repository is **rejected**;
  symbolic names, nonexistent object IDs, and `"unknown"` are not acceptable.
* `oracle.module_digest` — checkout-path-independent sha256 over the oracle implementation sources
  (`canon.py`, `families.py`, `generators.py`, `oracles.py`, `rng.py`, `sim.py`;
  `record.py` validates records and never measures, so it is excluded). This,
  not the git commit, is what actually pins the code that produced a
  measurement, and it stays meaningful in a dirty tree.
* `oracle.configuration` and `oracle.seed` — enough, with the stored scenario,
  to re-run the measurement.
* `oracle.units` — units for every measured quantity.
* `oracle.stages` — one entry per executed stage, with per-stage attribution.

## The five families

### 1. `spike-encoder-equivalence-pairs`

The generator emits a sensor trace (baseline, burst, drift, outlier, periodic,
or sparse events) optionally degraded by a perturbation (additive noise,
dropout, quantization, gain drift), and names two of the four encoding families
`rate | latency | delta | temporal`.

The oracle encodes the trace with both, decodes each with its matched decoder,
and measures what survived: `rmse`, `max_abs_error`, `pearson_r`,
`information_retention` (= `1 - rmse`, clipped), `spike_count`, `mean_rate_hz`,
`energy_pJ`, plus the spike representation as a bounded excerpt with a digest
over the full train. The winner is decided by the measurement, with a
spike-count tiebreak (`winner_basis: "spike_count_tiebreak"`): when retention
is within the tie epsilon, the encoding that spent fewer spikes — and so less
energy at the fixed per-spike cost — wins.

### 2. `neuron-dynamics-counterfactuals`

The generator proposes a stimulus (step, pulse train, ramp), a baseline neuron
configuration, and one intervention over `threshold | decay | adaptation |
refractory | input_intensity | neuromodulatory_state`.

The oracle runs the identical stimulus before and after, and reports spike
times, rate, ISI statistics, CV, an adaptation index, and a membrane trace for
each, plus the signed delta and its direction. Both halves of the counterfactual
share one configuration block and one seed, so the pair is reproducible.

### 3. `synaptic-delay-causal-trajectories`

The generator proposes a six-node delayed network with one inhibitory edge and
a perturbation: `delay_change | edge_removal | sign_flip | weight_change |
add_recurrent_edge`.

The oracle reports, before and after, first-arrival time per node, firing order,
downstream activation, source→sink propagation delay, and — as a delta —
suppressed nodes, recruited nodes, and whether reachability changed.

### 4. `neuromodulator-credit-assignment`

The generator proposes an outcome (expected value, received reward, risk,
novelty, effort) and a small pre-synaptic circuit.

Stage 1 (critic) maps the outcome to a reward prediction error and modulator
levels: `dopamine_phasic` (signed, the third factor), `dopamine`, `serotonin`,
`acetylcholine`, `norepinephrine`. Stage 2 (plasticity) computes per-synapse
STDP eligibility decayed to the reward time and applies

```text
dw = learning_rate * eligibility * dopamine_phasic * modulatory_gain
```

**The update is applied, not asserted.** Validation independently derives every
`weight_delta` from the retained learning rate, eligibility, phasic dopamine,
and modulatory gain, applies the retained weight bounds, and requires
`weights_after` to close against that derived update. Those weights are written
into a second run of the same circuit on the same input, and
`post_update_behavior` is a measurement of that run. When every derived delta
falls below the update epsilon, `update_applied` is `false` and no learning claim
is published. Reference reruns — recomputing the critic modulators, the STDP
eligibility traces, and the pre/post circuit behaviour — apply per stage and
only to stages the record says were run by the in-repo reference; a
named-runtime stage is authenticated through its own reproduction path (the
boundary above leaves agreement with the named runtimes unverified), while its
retained measurements still close against the update rule.

### 5. `temporal-memory-spike-challenges`

The generator proposes a delayed-dependency trial: a cue (A or B), a delay from
80 ms to 700 ms, zero to four distractors, sometimes a state-reset pulse, and a
network variant that varies loop delay, loop fatigue, and distractor strength.

The oracle is a recurrent network of two mutually inhibiting delay loops read
out through a probe gate. The output neurons need the loop drive *and* the probe
burst together — neither alone reaches threshold — so a response is evidence
that the cue is still circulating. Retention is limited by the loops' own
spike-frequency adaptation, so how long the state survives is a measured
consequence of the parameters, not a label.

For the baseline and every control, `response` and `response_ambiguous` are
derived from the retained OA/OB output-spike counts inside the response window:
only OA means A, only OB means B, neither means no response, and simultaneous
OA/OB activity is retained as an ambiguous no-response. Stored labels must match
that derivation.

**Temporal dependence is measured.** The same network is re-run with the cue
removed, and with the reset removed when there is one. A record is accepted only
if an ablation changes the measured response or the retained latch state at the
probe: two `none` responses whose `state_retained_at_probe` flags disagree still
demonstrate dependence. Trials where the loop had already forgotten are written
to `rejected-*.jsonl` with exactly that reason — a forgotten cue is a real
measurement of the retention limit, and it is kept as evidence rather than
deleted.

## Running it

```bash
# List the families
python3 pipelines/oracle_generate.py --list-families

# Generate a run (writes accepted-*.jsonl and rejected-*.jsonl per family)
python3 pipelines/oracle_generate.py --count 8 outputs/oracle-grounded/2026-09-01

# Validate, and re-run every oracle to confirm the measurements reproduce
python3 pipelines/oracle_validate.py --reproduce outputs/oracle-grounded/2026-09-01

# Only one family; refuse anything not measured by a bound named runtime
python3 pipelines/oracle_validate.py --family neuron-dynamics-counterfactuals \
    --require-runtime outputs/oracle-grounded/2026-09-01
```

`oracle_generate.py` never overwrites: it holds a kernel `flock` on a persistent
sibling lock file for the full transaction, builds every family before
publication, writes a sibling staging directory,
and on Linux publishes the complete manifest-authenticated tree with
`renameat2(RENAME_NOREPLACE)`. A non-cooperating process that creates the
destination after reservation wins its own path and causes generation to fail;
its content is never replaced. If the no-replace primitive is unavailable, the
generator fails closed rather than falling back to overwrite-capable `rename`.
The staging directory's device/inode identity is authenticated immediately
before and after rename; a substituted source is quarantined rather than
reported as the published run. Any generation or staging failure removes the
private staging tree and leaves no generator-authored run at the requested
output path. A stdout failure after publication reports that the run already
exists instead of claiming the transaction rolled back. Accepted and rejected
records go to separate files so that a
consumer reading only `accepted-*.jsonl` cannot pick up a record that failed its
family's gate. Each family lives in its own directory, so families can be
curated independently.

## Tests

`tests/test_oracle_grounded_*.py`, all stdlib `unittest`:

* **deterministic golden fixture** — `tests/fixtures/oracle-grounded/golden-r01/`
  is regenerated and compared byte for byte, including the manifest.
* **invalid-oracle fixture** — `invalid/invalid-oracle.jsonl`, nine records with
  a missing result, a misattributed result, a stale `result_hash`, an unknown
  commit, a missing module digest, a reference run claiming publishability, an
  empty measurement, no executed stages, and a reference run relabelled as a
  named runtime. Every one must be rejected.
* **malformed-generator fixture** — `invalid/malformed-generator.jsonl`, seven
  records where the generator authored a measurement key, edited the scenario
  after the proposal hash, claimed authority, dressed a guess as ground truth,
  emptied the scenario, relabelled a failing record as accepted, or rewrote its
  own rejection reason. Every one must be rejected.
* **reproducibility** — every golden record is re-measured from its stored
  scenario and must produce the same `result_hash`.
* **provenance / hash** — hashes cover what they claim, provenance vocabulary
  matches `schemas/provenance.md`, and commit plus module digest are present.
* **protocol** — `tests/fixtures/oracle-grounded/protocol_double.py` exercises
  the external-oracle path end to end, including every failure mode. It is a
  protocol double, not a simulator; its responses are tagged `protocol_double`
  and are never written to a dataset directory.

## Not done in this PR

* No corpus. The committed fixture is 20 records, four proposals per family,
  and exists to prove the shape end to end.
* No named runtime was executed. The boundary is implemented and tested with a
  protocol double; binding a real `axon-encoder`/`neuromod`/`synaptic-mesh`/
  `limbic-critic`/`plasticity-lab`/recurrent-SNN build is future work.
* No Hugging Face publication, and no dataset repositories created.
* The other five families in epic #76 (fault recovery, energy routing, MoE
  router distillation, hardware parity, NIR cross-runtime) are out of scope for
  #77.
* These records are not wired into `pipelines/validate_run.py`,
  `check_records.py`, or `promote.py`; the oracle-grounded families have their
  own validator because their envelope is not a thalamic trajectory.
