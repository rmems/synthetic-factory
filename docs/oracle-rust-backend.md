# Rust-backed neuromorphic generation

Synthetic-factory produces agentic and coding datasets for LLMs and neuromorphic
data for SNNs. The Rust backend adds real calls to the published axon-encoder
0.4.0 and neuromod 0.6.0 crates for two neuromorphic families. Python continues
to orchestrate generation, admission, composition, and export.

## Build and run locally

From the repository root, explicitly build the executable once:

```bash
cargo build --locked -p sf-oracle
oracle_bin="$(pwd)/target/debug/sf-oracle"
python3 pipelines/oracle_generate.py outputs/rust-demo-generated \
  --backend rust --oracle-rust-bin "$oracle_bin" \
  --family spike-encoder-equivalence-pairs \
  --family neuron-dynamics-counterfactuals --seed 20260918 --count 8
python3 pipelines/oracle_validate.py outputs/rust-demo-generated \
  --oracle-rust-bin "$oracle_bin" --require-runtime
python3 pipelines/compose_curated.py outputs/rust-demo-generated \
  outputs/rust-demo-curated --oracle-rust-bin "$oracle_bin" \
  --oracle-selection eligible-training --strict
python3 pipelines/export_hf.py outputs/rust-demo-curated \
  outputs/rust-demo-export --oracle-rust-bin "$oracle_bin" \
  --dataset-name rust-neuromorphic-demo
```

Use fresh output directories for another run; publication is append-only.
These commands export locally. They do not upload to Hugging Face or train a
model. The executable must already exist. Generation, validation, and admission
do not compile code or download dependencies. `--backend reference` remains the
default; Rust rejects unsupported family selections before generation.
Validation with `--oracle-rust-bin` includes reproduction. Missing executables,
protocol failures, identity mismatches, and unequal replay results block
acceptance; they never select a reference fallback.

## Profiles and evidence

`axon-stream-v1` runs deterministic streaming rate and delta encoders on channel
0, resetting state between episodes. Full events retain channel, polarity, and
adapter-assigned millisecond timestamps at the start of each sample. Rate
reconstruction is each sample's event count divided by
`rate_hz * sample_ms / 1000`, clipped to [0,1]. Delta reconstruction begins at
zero and accumulates signed `delta_threshold` per event, clipping to [0,1]
after every event. Both are explicitly adapter-derived lossy estimators. The
comparison selects lower RMSE against the original signal; equal RMSE is a tie.

`neuromod-lif-v1` creates a fresh standalone `LifNeuron` for each baseline and
intervention episode. It calls `integrate`, records the pre-reset membrane
potential, and calls `check_fire` at each step. Interventions multiply threshold,
per-step decay, or input scale. Spikes are timestamped at the end of each step.
The step duration labels time; it does not rescale the crate's decay dynamics.
The profile does not implement adaptation or a timed refractory period.

Full traces are preserved alongside bounded human-readable previews. Each
encoder side includes its first 24 events in `spike_preview` and sets
`spike_preview_truncated` when the full trace contains more events. Crate
outputs are distinct from adapter-derived reconstruction, RMSE, timestamps, and
summaries. No energy metric is inferred from spike count. Exact parameter bounds
and computational details are documented in
[the Rust oracle contract](../rust/sf-oracle/README.md).

## Reproduction and identity

Every record binds its versioned profile and complete configuration to crate
name/version, the released crate's source revision, the locked dependency graph,
adapter source hash, build-time Git revision, and executable SHA-256. The adapter
source hash includes the workspace and package manifests, build script, and all
production Rust modules. The ordered paths and length-delimited SHA-256 framing
are specified in `rust/sf-oracle/build.rs` and checked by Python. Source hashes
represent uncommitted changes; a build's Git revision alone does not assert a
clean checkout.

Keep the matching executable, lockfile, and adapter sources for future replay.
Rebuilding with another toolchain can change executable identity even if the
model outputs agree. Composition and export preserve original record content
and source coordinates through the existing authenticated dataset pipeline.

Rust tests compare traces against direct crate calls. Python integration covers
generation, reproduction, composition, and local export, including tampering
and unavailable executables. CI installs Rust 1.98.1, builds with `--locked`,
runs formatting, Clippy, and Rust tests, and exercises the Python integration
using the latest Python CI version.

These datasets provide reproducible crate-grounded episodes for later Spikenaut
experiments. They do not by themselves demonstrate an artificial nervous
system, FPGA parity, or improved SNN training performance.
