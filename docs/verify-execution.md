# Execution Verification — Frontier Gate Integration

Co-authored-by: Muse Code powered by Muse Spark <muse-spark@meta.com>

Mirrors `tests/tests_verify_execution.md` (test matrix and fixtures). This
document is the canonical spec for `pipelines/verify_execution.py` and its
comment hook into `pipelines/round_txn.py`.

## Objective

Distinguish **verified / inconclusive / failed** for every record and gate
frontier advancement on that taxonomy. Never promote `cannot-verify` to
`verified` (Ouroboros #1991, Codex #37278).

## Taxonomy

| Status | Meaning | Frontier (non-strict) | Frontier (strict) |
|---|---|---|---|
| `verified` | Observable execution evidence present and well-formed | passes | passes |
| `inconclusive` | Missing observation / provenance not in training set / unrecognized shape — cannot verify | passes (flagged) | **blocks** |
| `failed` | Structural defect (missing safety rationale, step not an object, bad JSON) | **blocks** | **blocks** |

Thalamic records require `state.sim_or_real ∈ {designed, simulated, hil}`,
non-empty `safety_decision.rationale`, and a `future_outcome` with
`timeline` / `observed_effects` / `new_state`. Episode steps require
`tool_call` with known tool name, non-empty `observation`, and
`decision_basis` when `thought` is present. Preference pairs take the
minimum of both sides; bridge records delegate to
`language_view.trajectory`.

## Integration with `pipelines/round_txn.py` Frontier Gate

`pipelines/round_txn.py` owns the atomic commit point:
`ROUND-rNN.complete.json` is hard-linked only after `validate_stage()`
passes `check_jsonl()` and quota checks. Execution verification is a
co-gate invoked via the **comment hook** in `pipelines/verify_execution.py`:

```python
# Frontier gate hook — pipelines/round_txn.py:validate_stage()
#   from verify_execution import verify_batch_for_frontier
#   counts, findings, blocked = verify_batch_for_frontier(batch, strict=True)
#   if blocked:
#       raise TransactionError("execution verification blocks frontier: ...")
```

Separation of concerns:

* `round_txn` — filesystem invariants, exclusive creation, no-clobber links,
  SHA-256 manifest, completion marker. Knows nothing about episode semantics.
* `verify_execution` — source of truth for verified / inconclusive / failed.
  Knows nothing about staging paths or tokens except via
  `verify_stage_for_frontier(stage_dir, round_number)`.

The frontier advances (`frontier_status().next_round` increments) only when
**both** gates pass. Failed staging areas stay inspectable and never advance
the frontier.

### Hook API

```python
from verify_execution import verify_batch_for_frontier, verify_stage_for_frontier, frontier_gate_result

counts, findings, blocked = verify_batch_for_frontier(Path("staging/.../batch-r03.jsonl"), strict=False)
# strict=False: blocked = (failed > 0)
# strict=True:  blocked = (failed > 0) or (inconclusive > 0)

counts, findings, blocked = verify_stage_for_frontier(Path("staging/.../r03-TOKEN"), round_number=3, strict=True)

verdict = frontier_gate_result(batch_path, strict=True)  # JSON-serializable for error messages
```

Import is on-demand to avoid a hard cycle (`round_txn` works without
`verify_execution`; `verify_execution audit_run` works without `round_txn`).

## CLI

```bash
python3 pipelines/verify_execution.py <run_dir> [--strict] [--json]
python3 pipelines/verify_execution.py --batch <path/to/batch-rNN.jsonl> [--strict] [--json]
python3 pipelines/verify_execution.py --record <path.jsonl> --line N
```

Exit code `1` when blocked, `0` otherwise. `--json` emits
`{counts, findings, blocked}`.

## Tests — `tests/tests_verify_execution.md` Matrix

The test doc (this file mirrors it) exercises every clause:

1. **Episode verified** — steps each have `tool_call.name ∈ KNOWN_TOOLS`,
   `observation` non-empty, `decision_basis` present when `thought` present.
2. **Episode inconclusive: hidden thought** — `thought` without `decision_basis`
   → inconclusive (not verified).
3. **Episode inconclusive: missing observation** — empty `observation` → inconclusive.
4. **Episode inconclusive: unknown tool** — tool name not in allow-list → inconclusive.
5. **Episode failed: steps not a list / step not an object** → failed.
6. **Thalamic verified** — `sim_or_real` allowed, `rationale` present,
   `future_outcome` has timeline/effects → verified.
7. **Thalamic inconclusive: bad provenance** — `sim_or_real` not in
   `ALLOWED_PROVENANCE` → inconclusive, counted as non-training.
8. **Thalamic failed: missing rationale** → failed.
9. **Thalamic inconclusive: future_outcome lacks observables** → inconclusive.
10. **Preference pair** — both sides verified → verified; any side failed →
    failed; any side inconclusive → inconclusive.
11. **Bridge pair** — delegates to `language_view.trajectory`; missing
    trajectory → inconclusive.
12. **Unrecognized shape** → inconclusive with key listing.
13. **Frontier gate (non-strict)** — `failed` blocks, `inconclusive` does not.
14. **Frontier gate (strict)** — `failed` or `inconclusive` blocks.
15. **Batch hook** — `verify_batch_for_frontier` on a staged
    `batch-rNN.jsonl` returns same verdict as `audit_run` on that file;
    `verify_stage_for_frontier` resolves the staged path correctly.
16. **Round-trip via round_txn staging** — reserve → stage batch with
    inconclusive record → `validate_stage` with `verify_batch_for_frontier(strict=True)`
    raises `TransactionError`; with `strict=False` the check_jsonl gate still
    governs and execution findings are advisory but logged.

Fixtures live under `tests/fixtures/verify_execution/` (or inline in
`tests/test_verify_execution.py` when running without files): minimal
episode, thalamic, preference, and bridge JSONL lines for each status.

## References

* `pipelines/verify_execution.py` — implementation and comment hook
* `pipelines/round_txn.py:validate_stage`, `publish`, `frontier_status`
* `pipelines/check_records.py:ALLOWED_PROVENANCE`, `pipelines/validate_run.py:event_time`
