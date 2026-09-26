# Crate-backed oracle

Build explicitly with `cargo build --locked -p sf-oracle` from the repository
root. Generation and validation use the prebuilt executable and do not invoke
Cargo. One invocation reads one `sf-oracle/1` JSON object from stdin, writes one
response to stdout, and exits. Errors exit 2 and leave stdout empty. No command
arguments are accepted. Requests are limited to 262,144 bytes and responses to
1,048,576 bytes. All objects reject unknown fields; duplicate fields are rejected
including inside profile parameters.

The supported canonical families are `spike-encoder-equivalence-pairs` with
runtime `axon-encoder` and profile `axon-stream-v1`, and
`neuron-dynamics-counterfactuals` with runtime `neuromod` and profile
`neuromod-lif-v1`. Signal arrays contain 1–4096 finite numbers in [0,1].

## Encoder semantics

Parameters are `sample_ms` in [0.01,100], `rate_hz` in [0.01,1000], and
`delta_threshold` in (0,1] representable as a positive f32. The product
`rate_hz * sample_ms / 1000` must not exceed 1. The crate receives f32 samples
on channel 0, one streaming call per sample, with reset state for each episode.
The deterministic streaming rate path is used, never stochastic batch encoding.

Crate events carry a local timestamp of zero. The adapter places each event at
`sample_index * sample_ms` and retains its channel and Boolean polarity. The
entire event array is returned, with `spike_preview` containing its first 24
events and `spike_preview_truncated` indicating whether further events exist.
Two explicitly adapter-derived reconstruction
estimators make the comparison reproducible:

* Rate: count events from that sample, divide by `rate_hz * sample_ms / 1000`,
  and clip to [0,1].
* Delta: start at zero, add or subtract `delta_threshold` for every positive or
  negative event respectively, clipping to [0,1] after each event.

These are lossy estimators from events, not reconstructions provided by the
crate or claims of encoder equivalence. RMSE is computed in f64 against the
original signal. The lower RMSE wins; exactly equal RMSE yields `tie`.

## Neuron semantics

Parameters are `dt_ms` in [0.01,100], `threshold` in [0.0001,100], `decay` in
[0,1], and `input_scale` in [0,100]. An intervention multiplies exactly one of
`threshold`, `decay`, or `input_scale` by `factor` in (0,100]; the resulting
parameters must satisfy the same bounds.

Both episodes start with a new `neuromod::LifNeuron`. For each sample, the
adapter calls `integrate((sample * input_scale) as f32)`, records the membrane
potential before reset, then calls `check_fire`. A spike is assigned to
`(sample_index + 1) * dt_ms`, the end of the integration step. `dt_ms` assigns
physical time to discrete steps; it does not change the crate's per-step decay.
The native computation adds stimulus, applies fractional leakage, then fires
and resets if the threshold is reached. This profile does not model adaptation
or a timed refractory period. Membrane values have crate units rather than an
asserted biological voltage unit.

## Execution identity

Versions are exact registry dependencies in the workspace lockfile. Published
source revisions come from each released crate's `.cargo_vcs_info.json`:

* axon-encoder 0.4.0: `102946f40dd55287a89aa363cd2d080a9d6195d8`
* neuromod 0.6.0: `184c80cbdad84c83042987e1b3ec6fed69578a87`

Each result includes SHA-256 of the locked dependency graph and current
executable bytes, plus the adapter source digest and the Git HEAD at build time.
The source digest covers root/package manifests, build script, and all adapter
production Rust modules. See the ordered `paths` list in `build.rs`: each entry
hashes UTF-8 repository-relative path, a NUL byte, u64 big-endian byte length,
and file bytes. Uncommitted source changes are represented by that digest;
`adapter_revision` alone is not a claim that the checkout was clean. This is
reproducibility evidence, not a cryptographic attestation of trustworthy code.

Run `cargo test --locked -p sf-oracle`, `cargo fmt --all --check`, and
`cargo clippy --locked --all-targets -- -D warnings`. Tests compare full traces
against direct calls to the published crates and cover reset, silence, timing,
interventions, invalid protocols, bounded episodes, and executable identity.
