# What a PR must pass, in the order python.yml / python-smoke.yml run it.
# The mini-run validator exit-code dance stays in python-smoke.yml: it is
# CI logic about a defective fixture, not an operator command.

# Run the PR gate locally: compile, gated lint, driver smoke, fixture census, Rust check
ci: compile lint smoke census-fixture rust-check
