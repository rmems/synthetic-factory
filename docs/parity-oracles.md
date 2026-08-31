# Parity oracles: what ran, what did not, and what that leaves unverified

This document covers the two verification-oriented dataset families:

- `hardware-parity-spike-trajectories`
- `nir-cross-runtime-equivalence`

Both answer the same shape of question — *did the same neuromorphic
computation actually remain the same after translation or deployment?* — and
both are built on the rule that generators propose experiments while oracles
produce truth.

## Oracle availability in this environment

Run the probes yourself; they are the source of truth, not this table.

```bash
python3 pipelines/neuro_oracle.py        # hardware-parity oracles
python3 pipelines/nir_equivalence.py availability
```

| Oracle | Kind | Status here | Reason code |
|---|---|---|---|
| `spikenaut_software_float` | in-repo float64 LIF simulator | **executes** | — |
| `spikenaut_q88_reference_model` | in-repo Q8.8 datapath model | **executes** | — |
| `recorded_capture` | replay of a recorded hardware run | executes when a capture file is supplied; **no capture is committed** | `CAPTURE_FILE_ABSENT` |
| `spikenaut_fpga` | physical FPGA | **did not execute** | `FPGA_DEVICE_NOT_DECLARED` |
| `nir_reference_v1` | in-repo NIR interpreter | **executes** | — |
| `nir_reference_v1_altorder` | in-repo NIR interpreter, alternative conventions | **executes** | — |
| `nir_rs` | the authority-contract oracle for the NIR family | **did not execute** | `RUNTIME_NOT_INSTALLED` |
| `nir_python` (`nir`) | reference NIR serialization library | **did not execute** | `RUNTIME_NOT_INSTALLED` |
| `nirtorch_snntorch` | upstream-compatible execution backend | **did not execute** | `RUNTIME_NOT_INSTALLED` |

## What that leaves unverified

Stated plainly, because a parity dataset that overstates its own coverage is
worse than no dataset:

1. **No FPGA was executed.** No board is attached, declared, or driven, and
   this repository ships no board transport. Every hardware-parity record in
   `tests/fixtures/parity-run/` therefore carries `ORACLE_UNAVAILABLE` and
   `LATENCY_NOT_MEASURED` in its reason codes, and its deployment-side
   `execution_target` is `fixed_point_reference_model` — a model of an FPGA
   datapath, not an FPGA.
2. **No hardware repeatability was measured.** Repeat runs of a deterministic
   reference model are bit-identical by construction. The record says so in
   `parity.repeatability.meaning`, sets
   `parity.repeatability.hardware_repeatability_measured` to `false`, and
   carries `REPEATABILITY_UNPROVEN`. Determinism of a model is not evidence
   about run-to-run variability of silicon.
3. **No latency was measured.** A Python simulator's wall-clock time is not a
   hardware latency, so the field records `measured: false` with a reason code
   instead of a plausible number.
4. **No upstream NIR runtime was executed.** `nir-rs` is the authority-contract
   oracle for that family and it is absent, as are `nir`, `nirtorch`,
   `snntorch`, `norse`, `lava`, and `sinabs`. What did execute is a pair of
   in-repo interpreters. A record from that pair is evidence about the
   *conventions they declare*, and its `oracle.evidence_scope` field says
   exactly that. It is not evidence about `nir-rs` or any upstream backend.

None of these gaps is patched by a substitute. Each adapter that cannot run
raises rather than returning something plausible, and the record that results
says `inconclusive` or carries the unavailability on its face.

## The hardware-parity oracle pair

```text
scenario (float model + encoded input fixture)
        |
        +--> software_float          -> spikes, action, membrane
        |
        +--> deployment target       -> spikes, action, membrane, Q8.8 provenance
                 |
                 +-- fixed_point_reference_model   (executes here)
                 +-- recorded_capture              (needs a committed capture)
                 +-- fpga_hardware                 (needs a board)
```

Both sides receive the identical encoded input fixture, and the fixture's
sha256 is recorded on the scenario *and* on the oracle block. The validator
recomputes it from the stored event grid, so "they ran the same input" is
checkable from the record alone rather than asserted.

### What makes an `fpga_hardware` claim believable

A record whose deployment-side `execution_target` is `fpga_hardware` or
`recorded_capture` is rejected unless it carries all of:

- `hardware.revision` and `hardware.board_serial`
- `bitstream.sha256` and `bitstream.toolchain`
- the stored capture source plus matching source, manifest, and payload digests
- a latency with `measured: true` and a numeric `value_ms`
- at least two retained repeat observations plus their derived digests, so
  determinism is measured rather than assumed

The validator also requires a capture adapter (or a physical-hardware runtime
class), re-hashes the retained source, manifest, and payload, binds the input
fixture, hardware, bitstream, quantization, latency, repeats, spike events,
membrane trace, and action back to that payload, and rejects a reference-model
record that was merely relabelled and decorated with metadata. These checks
establish the capture file's internal integrity. They do not establish that a
physical run happened; that separate limitation is stated below.

Validation probes FPGA availability again instead of trusting the availability
snapshot stored by the producer. It accepts only the exact recorded-capture or
live-board adapter/runtime identity for the declared target. A live-board
identity is accepted only when the current adapter probe reports an available
transport; the adapter in this revision always reports unavailable because its
board driver is not implemented. Validation also requires canonical lowercase
`sha256:<64-hex>` bitstream identifiers and checks every primary and repeated
spike and membrane matrix against the catalog neuron count and stimulus window.
Spike cells must be integer zero or one; spike events and the complete decoded
action must exactly restate that bitmap. Every repeat digest is derived again
from the complete retained observation (spikes, events, membrane, and action),
and the first repeat must equal the primary observation. For the two
re-executable in-repo targets, latency, exact repeat digests, and adapter
identity are independently re-derived. The complete scenario identity is also
rebuilt from its catalog entry: name, model, full stimulus, stress, hypothesis,
and intervention cannot be relabelled separately.

### To add a real hardware leg later

1. Implement a board transport in `FpgaHardwareAdapter.run`
   (`pipelines/neuro_oracle.py`) and set `SPIKENAUT_FPGA_DEVICE` and
   `SPIKENAUT_FPGA_BITSTREAM`.
2. Or record a capture and replay it:
   `python3 pipelines/hardware_parity.py generate <out> --capture <capture.json>`.
   A capture is a JSON object with `execution_target`, `quantization` (the Q8.8
   conversion that produced the bitstream), `hardware`, `bitstream`, a
   `manifest` carrying `payload_sha256` and `input_fixture_sha256`, and a
   `payload` holding the observed spikes, spike events, action, membrane,
   latency, and a `repeat_outputs`/`repeat_digests` pair. The adapter verifies
   both manifest digests, each repeat digest, the primary-to-first-repeat tie,
   and refuses a capture taken against a different input fixture. The emitted
   record retains that source and the validator independently re-checks the
   chain, dimensions, value domains, and every projected observation.
   A wholly fabricated but internally consistent capture remains outside what
   this repository can detect, as described below.

No capture is committed to this repository. Committing a synthetic one would
be indistinguishable from committing a fabricated hardware result.

## The NIR cross-runtime pair

The two in-repo interpreters differ in exactly four declared conventions,
each of which is a real interoperability hazard between neuromorphic runtimes
rather than an invented bug:

| Convention | `nir_reference_v1` | `nir_reference_v1_altorder` |
|---|---|---|
| Spike reset | subtract threshold | reset to zero |
| `Delay` unit | N whole timesteps | N-1 timesteps |
| Cycle break order | node insertion order | reverse-name order |
| `LI` coverage | implemented | declared unsupported |

Attribution is deliberately conservative. A convention is listed as a
*candidate* cause of an observed divergence only when the graph actually
contains the construct that convention governs — and for reset, only when a
spike actually fired. The `attribution.basis` string says in the record that
this is a candidate explanation and not a proven cause.

### Mismatches are the product

Nothing in `pipelines/nir_equivalence.py` repairs, retries, or filters a
divergence. The validator enforces the opposite direction:

- outputs that differ while the verdict claims a match is
  `DIVERGENCE_SUPPRESSED`;
- an unsupported diagnostic that has been edited away is
  `UNSUPPORTED_NOT_DIAGNOSED`;
- a runtime marked `unavailable` or `unsupported` that nonetheless carries
  outputs is `UNAVAILABLE_RUNTIME_HAS_OUTPUT`;
- fewer than two executed runtimes can never be a `match` — it is
  `unsupported` when a runtime refused a construct and `inconclusive`
  otherwise.

Every record carries the complete five-runtime inventory in a fixed order,
including unavailable upstream runtimes. The validator re-runs the
availability probe, binds each runtime class, convention declaration, and
supported-type list to the selected implementation, and rejects duplicate or
missing names. An unavailable upstream runtime cannot be relabelled as
`executed` or `unsupported`, and an in-repo unsupported diagnostic is checked
against the exception raised on re-execution.

The selected graph is likewise bound to the catalog entry with the same id,
class, and canonical graph digest; editing only the class label or replacing
the graph under a known id fails validation. `result.derived_from` preserves
runtime-inventory order and names every executed output digest plus every
unsupported or unavailable diagnostic digest. The training view must reproduce
that complete lineage exactly, so a consumer cannot silently retain only the
successful legs.

Parse/write evidence is produced and rechecked through each in-repo runtime's
declared codec adapter. Output event streams are compared exactly; numerical
traces use `NUMERIC_TOL`, so harmless within-tolerance floating-point noise is
not turned into a mismatch merely because canonical output digests differ.
Those digests remain evidence identifiers, not a numerical comparator.

## Anti-fabrication: what validation actually re-derives

Neither family trusts the numbers written on the record.

| Family | Re-derived during validation |
|---|---|
| hardware parity | the input-fixture digest, from the stored event grid; the scenario name/model/full stimulus/stress/hypothesis/intervention against the catalog; the entire Q8.8 conversion, from `scenario.model_float`; adapter identity and a fresh FPGA availability probe; **a full re-simulation of both in-repo oracles**, compared against the recorded spikes, action, membrane trace, output digest, latency, and exact repeat digests; every captured and repeated matrix dimension and value domain, event/action projection, retained-repeat digest, and canonical bitstream identity; every metric in `result.parity`, from the stored traces; and the verdict those traces support |
| NIR equivalence | the scenario id, graph class, structure digest, and graph digest against the catalog; the input-fixture digest; the fixed runtime inventory and complete output/diagnostic lineage; **a full re-execution of every in-repo runtime**, compared against the recorded outputs *in their entirety* and the round-trip block; and the comparison and verdict, from the recorded outputs |

A record whose result does not follow from its own evidence fails validation.
Recomputing the metrics from a record's own traces would not be enough on its
own: copying one side's traces onto the other yields a perfectly
self-consistent record asserting a match that never happened, which is why the
traces themselves are re-derived from the model and stimulus.

Only a runtime this validator can re-execute may be marked `executed`. An
`executed` claim naming `nir_rs` — which is not installed — is rejected
outright, because such a claim is unfalsifiable rather than merely unverified.

### The one thing that cannot be re-derived

A run on physical silicon is not reproducible from software; that is the point
of running it on hardware. So for a `fpga_hardware` or `recorded_capture`
target, the deployment traces rest on two things this repository *can* check —
the retained capture's internal digest chain and the binding from its payload
to every recorded observation and board/bitstream field — and on
one it cannot: that the capture describes a run that actually happened. A
capture file is trusted input. Nothing here can distinguish a genuine capture
from a well-formed fabricated one without an out-of-band trust anchor such as a
signed board attestation.

That limitation is not papered over. Every record with a physical target
carries `DEPLOYMENT_TRACE_NOT_REDERIVABLE` in its reason codes and in its
training view, so a hardware-claiming record can never read as fully
corroborated, and `provenance.kind` must be `hil` rather than `simulated`.

## Training views cannot hide a parity failure

`oracle_contract.build_training_view` copies the verdict, the failure flag,
and the reason codes onto the view, and `training_view_errors` re-checks them
against the record. `view_set_errors` rejects a view set that drops any
record, that repeats one (duplicating the agreeable half dilutes failures as
effectively as deleting them), or that contains a view with no record behind
it. There is no `--drop-mismatches` flag, and adding one would fail these
checks.

Views also carry `oracle_complete` alongside `parity_failed`. The two answer
different questions: `parity_failed: false` means *the oracles that ran
agreed*, which is not the same as *the intended oracles ran*. Without the
second flag a consumer filtering on `parity_failed` alone would read a clean
bill of health off a record from a family called
`hardware-parity-spike-trajectories` whose hardware leg never executed, or
off a physical/HIL MATCH whose deployment traces cannot be re-derived
(`DEPLOYMENT_TRACE_NOT_REDERIVABLE`). Every
record in the committed fixture has `oracle_complete: false`.

## Running the families

```bash
python3 pipelines/hardware_parity.py availability
python3 pipelines/hardware_parity.py generate outputs/staging/<date> --round 1
python3 pipelines/hardware_parity.py validate tests/fixtures/parity-run/hardware-parity-spike-trajectories/batch-r01.jsonl
python3 pipelines/hardware_parity.py training-view <path>

python3 pipelines/nir_equivalence.py availability
python3 pipelines/nir_equivalence.py generate outputs/staging/<date> --round 1
python3 pipelines/nir_equivalence.py validate tests/fixtures/parity-run/nir-cross-runtime-equivalence/batch-r01.jsonl
python3 pipelines/nir_equivalence.py training-view <path>
```

`outputs/raw/` is immutable committed evidence and never a generate target;
a staged round is promoted into it through `pipelines/round_txn.py`
(reserve, move the batch and NOTES into the returned stage, publish), as
documented in the README's parity-families section.

Both families also route through the normal factory layers:
`pipelines/census.py` classifies them, `pipelines/validate_run.py` enforces
the shared envelope, and `pipelines/check_records.py` runs the full
re-derivation described above.

## Publication status

Neither dataset has a Hugging Face repository and neither should get one yet.
Per the epic's publication rule, a name is reserved only after schema, working
oracle pipeline, deterministic fixtures, provenance, a sampled audit, and a
declared license all exist. Schema, pipeline, fixtures, and provenance exist
as of this document; the audit and license do not, and the FPGA and upstream
NIR legs above are unexecuted.
