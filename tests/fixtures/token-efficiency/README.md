# token-efficiency fixture

A minimal committed marker-mode run directory for the coverage-convergence
early-stop (`docs/token-efficiency.md`). Each visible round includes a JSONL
payload, NOTES, and a hash-bound `ROUND-rNN.complete.json`; the fixture therefore
exercises the same visibility contract as a real committed run.

- `thalamic-trajectory-factory/` -- the plateau pair: r01 at 4.2% and r02 at
  3.1%, two consecutive rounds under the 5% threshold, so the lane early-stops
  at r02.
- `agentic-coding-trajectory-factory/` -- the control pair: r01 at 4.8% (one
  low round) followed by r02 at 12.0%, which clears the streak, so the lane
  keeps running to its backstop.

`tests/test_factory_driver.py` first validates both marker-mode frontiers and
then asserts both outcomes through `driver.py token-efficiency --json`.
