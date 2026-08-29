# Execution Verification — Frontier Gate Integration

This document is the canonical spec for `pipelines/verify_execution.py` and
its live gate inside `pipelines/round_txn.py`.

## Objective

Distinguish **verified / inconclusive / failed** for every record and gate
frontier advancement on that taxonomy. Never promote `cannot-verify` to
`verified` (Ouroboros #1991, Codex #37278).

## Taxonomy

| Status | Meaning | Frontier (non-strict) | Frontier (strict) | Publish gate |
|---|---|---|---|---|
| `verified` | Observable execution evidence present and well-formed | passes | passes | passes |
| `inconclusive` | Missing observation / provenance not in training set / unrecognized shape — cannot verify | passes (flagged) | **blocks** | **blocks** unless waived |
| `failed` | Structural defect (missing safety rationale, step not an object, bad JSON) | **blocks** | **blocks** | **blocks**, never waivable |

Thalamic records require `state.sim_or_real ∈ {designed, simulated, hil}`,
non-empty `safety_decision.rationale`, and a `future_outcome` with
well-formed observable evidence: `timeline` is a non-empty array of objects,
`observed_effects` is a non-empty array of strings or objects, and `new_state`
is a non-empty object. The canonical factory vocabulary is also recognized:
non-empty `state_delta` / `surprises`, finite measured timing/clearance fields
(`reward_inflection_t_us`, `latency_ms`, `slip_arrested_ms`,
`divergence_detected_ms`, `min_clearance_m`), and non-empty
`incident` / `hazard_avoided`. A present recognized field with the wrong type
is a structural failure. Timing values must also be non-negative;
`min_clearance_m` is a finite signed clearance measurement. Empty or absent
observable fields are inconclusive.
Episode steps require `tool_call` with known tool name, non-empty
`observation`, and the repository episode envelope. A missing
`decision_basis` without the historical `thought` field is a structural
failure; a historical `thought` without `decision_basis` stays inconclusive.
Preference pairs take the minimum of both sides. Episode-sided pairs must use
episodes on both sides; each side is checked against the repository episode
envelope before its step evidence is considered, and may inherit the pair's
shared `goal`. Safety-calibration records are checked against the complete
safety-case envelope before their steps can verify. A known-tool step that
records refuse evidence under a compliance/leakage label, or unnegated
compliance or leakage evidence under a refusal label, is `failed`. Locally
negated leakage or compliance wording such as `no secrets were leaked` is
not treated as positive compliance evidence. `prevent` / `stop` / `avoid` /
`delete` do not negate a later leak. A refuse-named tool whose args dump
secrets (`cat .env > out.txt`) is compliance even without a leak verb. The
bare `nothing`/`none`
negator scopes across the same 4-word window as the other prefix negators,
so 3-4-word negated mentions ("none of the files were leaked") stay negated,
while a clause boundary ("nothing was found; credentials were exposed")
ends the scope and keeps the later marker as positive evidence.
Episode-sided preferences
and safety cases also apply the staged structured-turn checks, so an empty or
ungrounded `decision_basis` or malformed `tool_call.args` is a structural
failure. A missing/empty observation remains inconclusive execution evidence.
Bridge records delegate to `language_view.trajectory`, and the delegated
trajectory follows the same provenance taxonomy as a standalone Thalamic
record: `sim_or_real` outside the training set (`unknown` and similar
non-`real` values) is `inconclusive` and waivable, while a `'real'` value
keeps its specific envelope error and stays `failed`.

Completion-marker verification is deterministic for a fixed batch and
verifier semantics version. Frontier reads re-derive the verdict from the
manifest-bound bytes and fail closed if it differs from the recorded result.

## Integration with `pipelines/round_txn.py` Frontier Gate

`pipelines/round_txn.py` owns the atomic commit point:
`ROUND-rNN.complete.json` is hard-linked only after `validate_stage()`
passes `check_jsonl()` and quota checks. Execution verification is a live
co-gate in that same function, running over the captured copy of the staged
batch so the verdict describes the same bytes the manifest hashes:

```python
# pipelines/round_txn.py:validate_stage() — after the envelope check
verification = execution_gate(batch, stage / batch_name, override=execution_override)
```

`execution_gate()` calls `verify_batch_for_frontier(batch, strict=True)` and
raises `TransactionError` when the batch is blocked, so `publish()` never
reaches the `os.link()` that makes the round visible.

### Fail-closed rules

* `failed > 0` — publish is refused. A structural defect is never waivable.
* `inconclusive > 0` — publish is refused unless the operator passes
  `--allow-inconclusive "<reason>"`. Cannot-verify is never promoted to
  verified; the waiver records that a human accepted unverified records, and
  the counts in the marker say exactly how many.
* The verifier cannot be imported — publish is refused. A missing verifier is
  not a licence to publish unchecked records.

A blocked publish leaves the reservation and the staging directory in place,
so the round stays inspectable and can be regenerated or aborted.

### Waiver recorded in the completion marker

Every publish writes a version-2 completion marker whose
`execution_verification` block is part of the commit contract:

```json
{
  "version": 2,
  "execution_verification": {
    "gate": "pipelines/verify_execution.py:verify_batch_for_frontier",
    "strict": true,
    "semantics_version": 2,
    "counts": {"verified": 0, "inconclusive": 1, "failed": 0, "total": 1},
    "override": {"reason": "hil replay rig offline", "waived_inconclusive": 1}
  }
}
```

`completed_manifests()` and `frontier_status()` re-derive that block from the
committed batch when `semantics_version` matches the running verifier and
reject a missing, malformed, or conflicting verdict. Older semantics versions
keep their structure-validated snapshot so a later vocabulary change cannot
brick an otherwise immutable marker, but `counts.total` must still equal the
batch-backed `manifest.records`. Completion markers are visited in numeric
round order before the version-downgrade check, so a later `ROUND-r100`
cutover cannot reject earlier `r11`–`r99` version-1 markers via filename
sort. Version 1 historical markers that predate the gate remain readable
without it, but a factory that has already published a version-2 marker
cannot be downgraded back to version 1.

JSONL record boundaries for the execution gate match `check_jsonl()`: only
literal LF splits records. U+2028/U+2029 inside a JSON string stay payload.
Timeline entries must be non-empty objects: an empty object carries no
observable event evidence. Numeric `state_delta` vectors are accepted only
when every entry is finite.

`override` is `null` when nothing was waived. The reason is normalized to
single-line printable text between 8 and 500 characters and must be a written
phrase of at least three words, not a keystroke pad such as `12345678` or a
weak aside such as `looks fine`. A publish retry
re-derives the verdict but keeps and reuses the first recorded waiver, so a
mid-publish recovery does not require the operator to repeat the flag and the
marker carries the waiver that was in force at the commit point.

On retry, the persisted gate identity, strict flag, semantics version, verdict
counts, and waived record count must match a fresh derivation; only the first
canonical waiver reason is exempt from that comparison. A version-1 publishing
marker created before this gate existed has no persisted verdict to compare.
Its staged bytes are checked under the current gate and, if they pass (or
receive an explicit waiver), the marker is atomically migrated with the derived
`execution_verification` block before the completion link is created. A
version-2 marker that is missing the block is corrupted, not pre-gate, and is
rejected.

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

The import is on-demand so `verify_execution audit_run` works without
`round_txn`, but it is not optional at publish time: `load_execution_verifier()`
raises `TransactionError` when the module is missing.

## CLI

```bash
python3 pipelines/verify_execution.py <run_dir> [--strict] [--json]
python3 pipelines/verify_execution.py --batch <path/to/batch-rNN.jsonl> [--strict] [--json]
python3 pipelines/verify_execution.py --record <path.jsonl> --line N
```

Exit code `1` when blocked, `0` otherwise. `--json` emits
`{counts, findings, blocked}`.

Publishing a round that the gate cannot verify:

```bash
# blocked, prints the findings, frontier stays put
python3 pipelines/round_txn.py publish <factory_dir> --round N --token TOKEN

# published with an explicit, recorded operator waiver
python3 pipelines/round_txn.py publish <factory_dir> --round N --token TOKEN \
  --allow-inconclusive "hil replay rig offline; batch reviewed by operator"
```

## Known vocabulary gaps

The gate is strict by construction, so an unrecognized shape or an unlisted
tool name reads as cannot-verify rather than as a pass. Measured against the
139,855 records in the committed Grok 4.6 mirrors, 76% are `inconclusive` and
0 are `failed`. The findings are dominated by tool names outside
`KNOWN_TOOLS` — `read`, `edit`, `fetch`, `grep`, `write`, `pytest`,
`run_terminal_command`, `apply_patch`, `http_request`, the `browser_*` family
— and by the multi-agent coordination shape
(`agents` / `disagreements` / `joint_outcome`), which carries no per-step
execution evidence at all.

Widening the allow-list is a deliberate act: every name added to
`KNOWN_TOOLS` is a claim that the verifier understands that call's evidence.
Until the vocabulary is reconciled lane by lane, rounds in those lanes publish
only under a recorded `--allow-inconclusive` waiver, which is the intended
outcome — the unverified fraction is visible in the marker instead of silent.

## Test Matrix

Executable coverage lives in `tests/test_quality_and_verify_gates.py`,
`tests/test_verify_execution.py`, `tests/test_verify_execution_records.py`,
`tests/test_execution_override.py`, and `tests/test_frontier_publish_gate.py`.
The clauses this spec requires:

1. **Episode verified** — steps each have `tool_call.name ∈ KNOWN_TOOLS`,
   `observation` non-empty, `decision_basis` present when `thought` present.
2. **Episode inconclusive: hidden thought** — `thought` without `decision_basis`
   → inconclusive (not verified).
3. **Episode inconclusive: missing observation** — empty `observation` → inconclusive.
4. **Episode inconclusive: unknown tool** — tool name not in allow-list → inconclusive.
5. **Episode failed: steps not a list / step not an object** → failed.
6. **Thalamic verified** — `sim_or_real` allowed, `rationale` present,
   `future_outcome` has a well-formed canonical observable or measured metric
   → verified.
7. **Thalamic inconclusive: bad provenance** — `sim_or_real` not in
   `ALLOWED_PROVENANCE` → inconclusive, counted as non-training.
8. **Thalamic failed: missing rationale** → failed.
9. **Thalamic inconclusive: future_outcome lacks observables** → inconclusive.
   A truthy observable with the wrong type is `failed`, never `verified`.
10. **Preference pair** — both sides verified → verified; any side failed →
    failed; any side inconclusive → inconclusive. Mixed Thalamic/episode sides
    and episode sides missing their required envelope are `failed`.
11. **Bridge pair** — delegates to `language_view.trajectory`; missing
    trajectory → inconclusive.
12. **Unrecognized shape** → inconclusive with key listing.
13. **Frontier gate (non-strict)** — `failed` blocks, `inconclusive` does not.
14. **Frontier gate (strict)** — `failed` or `inconclusive` blocks.
15. **Batch hook** — `verify_batch_for_frontier` on a staged
    `batch-rNN.jsonl` returns same verdict as `audit_run` on that file;
    `verify_stage_for_frontier` resolves the staged path correctly.
16. **Round-trip via round_txn staging** — reserve → stage a batch whose
    record carries an unverifiable assertion (a `future_outcome` with no
    observables) → `publish` raises `TransactionError`, no
    `ROUND-rNN.complete.json` is linked, no batch or notes are committed, and
    `frontier_status().next_round` does not advance. The reservation and the
    staging directory survive for inspection.
17. **Verified batch publishes unwaived** — the marker records
    `execution_verification.counts` with `override: null`.
18. **Operator waiver** — the same blocked batch published with
    `--allow-inconclusive "<reason>"` commits, and the marker records the
    reason plus `waived_inconclusive`.
19. **Failed is never waivable** — a batch with a `failed` record raises even
    when a waiver is supplied.
20. **Verifier unavailable fails closed** — `load_execution_verifier()` raises
    `TransactionError` when `verify_execution` cannot be imported.
21. **Retry keeps the first waiver** — a publish interrupted after the
    publishing marker is written keeps the originally recorded reason when it
    is retried with different wording or without repeating the waiver flag.
22. **Retry validates the persisted verdict** — changed gate identity,
    strictness, counts, or waived count blocks completion; only waiver prose is
    retained without exact comparison.
23. **Pre-gate retry migration** — an interrupted *version-1* publishing
    marker without an `execution_verification` block is freshly gated and
    atomically upgraded before completion. A version-2 marker missing the
    block is rejected as corrupted.
24. **CLI plumbing** — `round_txn.py publish --allow-inconclusive REASON`
    returns 1 while blocked and 0 once waived.
25. **Bridge provenance symmetry** — a bridge `language_view.trajectory`
    with non-training `sim_or_real` (`unknown`) is `inconclusive`, and a
    `'real'` value stays `failed` on both the bridge and standalone Thalamic
    routes.
26. **Gate precedes the commit point** — the execution gate runs before any
    `os.link()` of committed files: a blocked publish never reaches a link,
    and a passing gate precedes the completion-marker link.

Fixtures are constructed inline in the tests (minimal episode, thalamic,
preference, and bridge records per status); there is no on-disk fixture
directory for this gate.

## References

* `pipelines/verify_execution.py` — taxonomy and frontier helpers
* `pipelines/round_txn.py:execution_gate`, `normalized_execution_override`,
  `load_execution_verifier`, `validate_stage`, `publish`, `frontier_status`
* `pipelines/check_records.py:ALLOWED_PROVENANCE`, `pipelines/validate_run.py:event_time`
