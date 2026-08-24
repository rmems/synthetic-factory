# token-efficiency fixture

A minimal committed run directory for the coverage-convergence early-stop
(`docs/token-efficiency.md`). It carries NOTES only -- no payloads -- because
the latch reads `NOTES-rNN.md` and nothing else.

- `thalamic-trajectory-factory/` -- the plateau pair: r05 at 4.2% and r06 at
  3.1%, two consecutive rounds under the 5% threshold, so the lane early-stops
  at r06.
- `agentic-coding-trajectory-factory/` -- the control pair: r05 at 4.8% (one
  low round) followed by r06 at 12.0%, which clears the streak, so the lane
  keeps running to its backstop.

`tests/test_factory_driver.py` asserts both outcomes through
`driver.py token-efficiency --json`.
