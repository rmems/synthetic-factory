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

## Hugging Face card viewer schemas

Published cards declare their Dataset Viewer schema by hand, one JSON file per
dataset at `config/card-schemas/<hub-dataset-name>.json`. The format and the
rules live in `pipelines/card_schema.py`. Audit the set with:

```bash
python3 scripts/publish_grok46_hub.py schemas          # lists declared/undeclared
python3 scripts/publish_grok46_hub.py schemas --strict # nonzero while any gap remains
```

A dataset with no declaration publishes a card that says so. Never rewrite
historical raw JSONL to fix a viewer schema — declare the union on the card.

## Cursor Cloud specific instructions

Cloud agents should start from `.cursor/environment.json`, which builds
`.cursor/Dockerfile` (Ubuntu 24.04, git, sudo, Python 3). The install script
creates `.venv`, compiles the pipelines, runs unit tests, and runs the
operator smoke check.

Do not COPY the repo into the image. Cursor checks out the target commit.
Do not treat `outputs/raw/` as a scratch directory. Prefer the committed
fixtures and `driver.py smoke` for environment verification.
