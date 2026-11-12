# What a PR must pass, in the order python.yml / python-smoke.yml run it.
# The mini-run validator exit-code dance stays in python-smoke.yml: it is
# CI logic about a defective fixture, not an operator command. CI shards the
# same unittest suite for speed and combines coverage separately.

# Run the local PR gate: compile, lint, smoke, census, full tests, Rust check, oracle e2e
ci: compile lint smoke census-fixture test rust-check oracle-e2e
