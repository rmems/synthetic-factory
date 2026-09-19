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

Issue #77 names six ground-truth runtimes. The optional Rust executable now
uses published `axon-encoder 0.4.0` and `neuromod 0.6.0` dependencies for two
versioned crate-native profiles. Generation defaults to reference simulation;
`--backend rust --oracle-rust-bin PATH` explicitly selects crate execution.
Runtime binding, rather than ambient `PATH` membership, is retained in data.

| Family | Reference default | Optional crate-native profile |
|---|---|---|
| `spike-encoder-equivalence-pairs` | reference encoder bank | `axon-stream-v1` |
| `neuron-dynamics-counterfactuals` | reference adaptive LIF | `neuromod-lif-v1` |
| `synaptic-delay-causal-trajectories` | reference delay mesh | not integrated |
| `neuromodulator-credit-assignment` | reference critic and STDP | not integrated |
| `temporal-memory-spike-challenges` | reference recurrent delay-loop network | not integrated |

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

and `validation.publishable` follows the simulator decision of #171: a
deterministic in-repo reference simulator is an authoritative oracle for
training-candidate data when its measurement is reproducible. An accepted
reference record whose `provenance.kind` is `simulated` and whose
`oracle.module_digest` matches the current reference sources is therefore
publishable, and its `publishable_reason` says that it is a reproducible
simulation, not a runtime attestation. A record whose digest the current
sources cannot reproduce, whose commit or dirty state is unresolved, or that
failed validation keeps `publishable: false`, with the reason spelled out.
Publication also requires the generator name/version and factory identity to
match the reviewed procedural policy. Caller-supplied model or factory names
remain valid diagnostic metadata but cannot claim that policy's publication
authority; training admission independently enforces the exact registry route.
Binding a named runtime remains optional stronger evidence and is recorded
exactly as before. `pipelines/oracle_grounded/*.py` is pinned to LF line
endings in `.gitattributes` so the digest reproduces across checkouts.

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

Follow [the Rust backend guide](oracle-rust-backend.md) to build the locked
executable and select it explicitly. The reference CLI backend ignores ambient
`SF_ORACLE_*_CMD` bindings. Low-level external-command adapters still support
the existing `sf-oracle/1` interface for custom callers; their metadata alone
does not grant training admission.

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

Training admission independently replays accepted reference measurements with
the built-in oracle and requires an exact result digest match. Named and mixed
runtime records are ineligible by default with `authenticated runtime replay required`:
their metadata alone cannot authenticate their measurements. This identifies
missing evidence, not a claim that their runtime measurements are incorrect.
Pure metadata admission does not invoke external runtime commands. The
[crate-native backend](oracle-rust-backend.md) adds an explicit
`--oracle-rust-bin` option to validation, assembly, and export: the caller-selected
executable freshly replays each native record within that operation. A previous
CLI report is never treated as an admission receipt. Other named or mixed
runtimes remain ineligible.

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
  measurement, and it stays meaningful in a dirty tree. `rng.py` also carries
  the contract-wide `DrawStream` that the fault-recovery and code-repair
  families draw from, so an edit there moves this digest too and the golden
  fixture must be regenerated with it.
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
sibling lock file for the full transaction, builds each selected family before
publication, writes a sibling staging directory,
and on Linux publishes the complete manifest-authenticated tree with
`renameat2(RENAME_NOREPLACE)`. A non-cooperating process that creates the
destination after reservation wins its own path and causes generation to fail;
its content is never replaced. If the no-replace primitive is unavailable, the
generator fails closed rather than falling back to overwrite-capable `rename`.
Before publication it checks that the requested parent still names the pinned
directory, and afterward it checks both that binding and the published leaf
identity. A failed final check returns nonzero without a success manifest;
the diagnostic identifies that publication already occurred, and the retained
tree is not deleted through a pathname another writer may have replaced.
The staging directory's device/inode identity is authenticated immediately
before and after rename; a substituted source is quarantined rather than
reported as the published run. A staging failure atomically moves the owned
private tree to a unique `.synthetic-factory-rollback-*` sibling for recovery;
it never recursively deletes a path that another writer could replace. A
raced foreign replacement is restored when possible without overwriting any
entry, and otherwise retained under its quarantine name. If atomic quarantine
is unavailable, the staging tree remains in place with a recovery diagnostic.
These failed artifacts are not published runs: no generator-authored run is
left at the requested output path. A fatal runtime, generation, or envelope error stops remaining
proposals and families in that atomic run; honest rejected measurements remain
retained evidence and do not stop generation. Separate campaign lanes are
independent of this transaction. A stdout failure after publication reports that the run already
exists instead of claiming the transaction rolled back. Accepted and rejected
records go to separate files so that a
consumer reading only `accepted-*.jsonl` cannot pick up a record that failed its
family's gate. Each family lives in its own directory, so families can be
curated independently.

## Direct replay resource bounds

The synaptic-delay family accepts durations up to 140 ms at its fixed 0.5 ms
step, including through direct `record.reproduce` calls. The family request
checks that bound before creating events or selecting an oracle adapter.
The shared `simulate_mesh` API requires finite positive duration and timestep
values and refuses more than 10,000 steps before allocating simulator state.
That broader limit preserves the credit-assignment and temporal-memory windows,
as well as the existing 5,000 ms direct simulation case. Spike-count limits
remain a separate bound on excitatory activity; a quiet simulation is bounded
even when it produces no spikes.

Boolean schema nodes are unsupported and produce schema findings rather than
validator exceptions, including through properties, alternatives, and references.
Boolean `additionalProperties` retains its supported JSON Schema meaning.

## Assemble eligible reference measurements

The default composition preserves every valid oracle record, including honest
rejections. Its training audit therefore blocks export when rejected or otherwise
ineligible evidence is retained. To create a training candidate from the eligible
part of an authenticated oracle run, request selection explicitly:

```bash
python3 pipelines/compose_curated.py --oracle-selection eligible-training \
    outputs/oracle-grounded/2026-09-01 outputs/curated/oracle-training
python3 pipelines/export_hf.py outputs/curated/oracle-training outputs/curated/oracle-export
```

Selection requires the complete original oracle run and its manifest, including
rejected rows and empty declared files. It reuses fresh identity admission and
reference replay; a stored accepted or publishable flag is not sufficient.
Corrupt evidence refuses the run even if selection would otherwise omit it.
Each omitted row remains in the compose manifest with original source coordinates,
text, hashes, and an explicit eligibility reason. The original run is unchanged.
The versioned selection declaration and every decision are replayed again before
export. Named or mixed runtime rows remain ineligible without authenticated
runtime replay evidence. Selection only executes the crate-native runtime when
the caller explicitly supplies `--oracle-rust-bin`; metadata alone never authorizes it.

This is a local dataset assembly and export operation. It neither publishes a
remote dataset nor establishes that an accepted-only sample is statistically
unbiased. The default `--oracle-selection all` keeps the prior preservation
behavior. New dataset families still require reviewed generator, schema, and
registry code; the CLI selects and parameterizes the five implemented families.

## Tests

`tests/test_oracle_grounded_*.py`, all stdlib `unittest`:

* **deterministic golden fixture** — `tests/fixtures/oracle-grounded/golden-r01/`
  is regenerated through a trusted test-only replay helper and compared byte
  for byte, including the manifest. Its historical commit is fixture data:
  unresolved dirty state makes every replayed row diagnostic and nonpublishable.
  Public CLI generation separately requires explicit commit stamps to match
  the actual checkout, including reference-only and dirty runs.
* **invalid-oracle fixture** — `invalid/invalid-oracle.jsonl`, nine records with
  a missing result, a misattributed result, a stale `result_hash`, an unknown
  commit, a missing module digest, a reference run whose `publishable_reason`
  claims the named runtime, an empty measurement, no executed stages, and a
  reference run relabelled as a named runtime. Every one must be rejected.
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
* `pipelines/validate_run.py` routes explicit oracle envelopes to their oracle
  checks before generic trajectory shapes. The dedicated `oracle_validate.py`
  additionally authenticates the complete run manifest and can explicitly
  reproduce measurements. `check_records.py` and `promote.py` remain outside
  this integration.
