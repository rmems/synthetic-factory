# Agent notes

This repository is a bounded synthetic-data factory. There is no long-running
HTTP service. The runnable surface is stdlib Python CLIs under `pipelines/`
plus the operator driver at
`.claude/skills/run-synthetic-factory/driver.py`.

Track work with Beads (`bd`). Do not add markdown TODO lists.

## Local checks

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -q
python3 .claude/skills/run-synthetic-factory/driver.py smoke
python3 pipelines/census.py tests/fixtures/mini-run
```

`tests/fixtures/mini-run` includes one intentional JSON parse failure.
`validate_run.py` on that path is expected to exit nonzero.

## Parity oracles

The `hardware-parity-spike-trajectories` and `nir-cross-runtime-equivalence`
families depend on oracles that mostly do **not** exist in this environment.
No FPGA is attached and no upstream NIR runtime is installed. Do not add a
fallback that produces a plausible result in their place: the adapters raise
with a reason code on purpose, and the validators reject any record that
claims an execution target it cannot substantiate.

```bash
python3 pipelines/neuro_oracle.py            # hardware-parity oracle availability
python3 pipelines/nir_equivalence.py availability
```

`docs/parity-oracles.md` records what ran, what did not, and what that leaves
unverified. Keep it accurate if you change an adapter.

`tests/fixtures/parity-run/` is the committed fixture round. It is the
generators' default output and `tests/test_parity_factory_integration.py`
compares it byte-for-byte, so regenerate it deliberately rather than letting
it drift.

## Cursor Cloud specific instructions

Cloud agents should start from `.cursor/environment.json`, which builds
`.cursor/Dockerfile` (Ubuntu 24.04, git, sudo, Python 3). The install script
creates `.venv`, compiles the pipelines, runs unit tests, and runs the
operator smoke check.

Do not COPY the repo into the image. Cursor checks out the target commit.
Do not treat `outputs/raw/` as a scratch directory. Prefer the committed
fixtures and `driver.py smoke` for environment verification.
