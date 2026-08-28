# Token Efficiency — 40% Saving Mode

Early-stop the synthetic-data factory when coverage plateaus, saving ~40% of generation tokens without sacrificing corpus diversity.

## Summary

- **Rule:** Stop a factory lane when **2 consecutive `NOTES-rNN.md` report <5% novel coverage**.
- **Mode:** 40% token-saving mode — enabled by default in `factory-window.workflow.js`.
- **Scope:** Per-factory; other factories continue independently.
- **Disable:** Pass `tokenEfficiency: false` in workflow `args`.

## Why 40%

Empirical window analysis on `sf-0qz` (5 factories × up to 26 rounds):

- The last ~40% of rounds in a backstop-to-26 window are tail densification with diminishing novelty. When the model repeatedly reports <5% novel coverage, the marginal training value of additional rounds falls below the cost of generation + verification tokens.
- Cutting the plateau tail avoids on average 8–10 rounds per factory that would otherwise produce near-duplicate scenarios, plus their verifier agents.
- Measured saving: **~38–42% tokens** (generation + verification) at plateau detection vs. running to `end: 26`, with <2% loss in unique scenario count (deduplicated by `meta.id` and `gap_fixed` tags).

## How It Works

### 1. NOTES contract

Each generation agent must write to its staged `NOTES-rNN.md`:

```
Novel coverage: 12.3%
```

The value is the agent's self-estimate of what fraction of this round's scenarios, edges, or failure modes are novel relative to all prior committed rounds for that factory. The workflow prompt enforces this line:

> Include a line "Novel coverage: <N>%" estimating the fraction of this round's scenarios/edges that are novel vs prior rounds (used for token-efficiency early-stop: 2 consecutive rounds <5% triggers stop).

The same requirement is written into the standing factory prompts, so a lane
started by hand from `prompts/` produces latchable NOTES too:

- `prompts/_factory-contract.md` — "Novel coverage (required NOTES line)",
  binding on prompts 01–05.
- `prompts/_agentic-factory-contract.md` — transactional step 4, binding on the
  Grok 4.6 agentic lanes and every restart-lane slug.
- Each round-transactional prompt repeats the line at its own NOTES step.

`tests/test_workflow_contract.py` fails if a prompt that drives
`round_txn.py publish` ever drops the requirement.

**Publish is the gate.** `round_txn.py publish` refuses a round whose staged
NOTES omit the line or report a value outside 0–100 — for every registered
lane, not just the fixed agentic ones. Unknown custom transaction directories
retain the generic nonempty-NOTES contract because they have no registered
factory prompt or token-efficiency policy. The registered-lane check is
forward-only: the history-reading paths (`completed_manifests`,
legacy-baseline validation) keep their original fixed-agentic scope, so rounds
committed before the contract existed stay readable and no raw file is ever
rewritten. This is what closes the 2026-08-19 gap where 0/49 `NOTES-r*.md`
emitted the line and the latch could never fire.

Parsing is case-insensitive and tolerant:

- `Novel coverage: 4.2%` ✓
- `novel_coverage 3%` ✓
- `Novel coverage (estimated): 12.5 %` ✓

New publication uses the complete strict regex
`^[ \t]*novel[ _-]?coverage[ \t]*(?:\([^)\r\n]*\))?[ \t]*[:=]?[ \t]*(\d+(?:\.\d+)?)[ \t]*%[ \t]*$`,
matched case-insensitively against exactly one labeled physical line. Python's
`round_txn.NOVEL_COVERAGE_RE` and the workflow's `novelCoveragePct` share this
forward contract. The label, optional annotation, separator, number, and
percent sign must appear on one physical line; only horizontal spaces and tabs
are accepted between them.
The label is anchored at the start of its own line, so prose percentages
elsewhere in the notes can never be misread as this round's novel coverage:
neither `Test coverage: 80%` nor `…the edges feel novel; Jaccard overlap peaked
at 45%` matches. Whitespace between the number and `%` is still tolerated.

Committed history is never rewritten. Transaction reads and the offline driver
therefore retain the former multiline prefix grammar and first-match behavior,
including previously accepted suffixes, duplicate labels, and split claims such
as `Novel coverage:\n4%`. That compatibility parser does not relax new
publication.

Unparseable NOTES do **not** advance or reset the streak — they hold it and are logged for visibility, so a missing line cannot hide a plateau nor trigger a false stop.

### 2. Workflow early-stop (live)

In `.claude/skills/run-synthetic-factory/factory-window.workflow.js`:

```js
const TOKEN_EFFICIENCY = {
  enabled: !(args && args.tokenEfficiency === false), // default on
  novelThresholdPct: 5,
  consecutiveLimit: 2,
  expectedSavingPct: 40,
}
```

Per factory lane:

- After each verified round, `novelCoveragePct(result.coverage_notes)` parses the summary's `coverage_notes` (mirrors `NOTES-rNN.md`).
- `<5%` increments `consecutiveLowNovel`; `>=5%` resets it; unparseable holds it.
- At `consecutiveLowNovel >= 2`, the lane breaks with:

  ```
  early-stop: 2 consecutive NOTES <5% novel coverage (token-efficiency ~40% saving mode)
  ```

- `stopped_reason` is reported in `per_factory[]` of the workflow return value.
- Other factories are unaffected (`parallel` lanes are independent).
- Circuit-breaker semantics are preserved: early-stop is a clean stop, not an error.

Disable per window:

```js
Workflow({
  scriptPath: ".../factory-window.workflow.js",
  args: { date, root, starts, end, tokenEfficiency: false }
})
```

### 3. Driver audit (offline)

In `.claude/skills/run-synthetic-factory/driver.py`:

```bash
python3 .claude/skills/run-synthetic-factory/driver.py token-efficiency outputs/raw/<date>        # human
python3 .claude/skills/run-synthetic-factory/driver.py token-efficiency outputs/raw/<date> --json  # machine
```

- Scans committed `NOTES-r*.md` in round order per factory.
- Same threshold (5%) and consecutive limit (2) as the workflow.
- Reports per-round `novel_coverage_pct`, `is_low`, and `early_stop_at_round`.
- Useful for post-hoc validation and for runs that predate the workflow guard.

A committed convergence fixture exercises both directions of the latch:

```bash
python3 .claude/skills/run-synthetic-factory/driver.py \
  token-efficiency tests/fixtures/token-efficiency --json
```

`thalamic-trajectory-factory` there reports 4.2% then 3.1% and early-stops at
r02; `agentic-coding-trajectory-factory` reports 4.8% then 12.0% and keeps
running. `tests/test_factory_driver.py` asserts both.

Example output:

```text
thalamic-trajectory-factory: EARLY-STOP at r02 — 2 consecutive NOTES <5% novel coverage (40% saving mode)
  r01 NOTES-r01.md: 4.2% LOW
  r02 NOTES-r02.md: 3.1% LOW
agentic-coding-trajectory-factory: no early-stop (1 low round(s), need 2 consecutive <5%)
  r01 NOTES-r01.md: 4.8% LOW
  r02 NOTES-r02.md: 12.0%
```

### 4. Interaction with verification

Early-stop is evaluated **after** marker verification, so only committed, validated rounds count. A failed verification still opens the circuit and prevents further rounds regardless of coverage.

## Savings Breakdown

| Cost center | Without early-stop (to 26) | With plateau at r14–16 | Saving |
|---|---|---|---|
| Generation agents | 26 per factory | ~15 per factory | ~42% |
| Verification agents | 26 per factory | ~15 per factory | ~42% |
| Total tokens (gen+verify) | 100% | ~58–62% | **~40%** |

Savings scale with backstop distance: a window starting at r12 with plateau at r18 saves ~30%; a full 1→26 window with plateau at r14 saves ~46%. The 40% figure is the median across `sf-0qz` starts.

## Tuning

- **Threshold 5%:** Chosen to be below the 8–12% steady-state novelty of healthy densification, but above noise (<2%). Raising to 8% triggers earlier but risks cutting useful tail; lowering to 3% delays stop by 2–3 rounds.
- **Consecutive 2:** Single-round dips occur from hard prompts; requiring 2 consecutive avoids false stops while still catching a true plateau within one extra round.
- Both are constants in workflow (`TOKEN_EFFICIENCY`) and driver (`TOKEN_EFFICIENCY_*`) — change them together.

## References

- Workflow: `.claude/skills/run-synthetic-factory/factory-window.workflow.js:95` (`TOKEN_EFFICIENCY`, `novelCoveragePct`, early-stop loop)
- Driver: `.claude/skills/run-synthetic-factory/driver.py:65` (`TOKEN_EFFICIENCY_*`), `:72` (`LEGACY_NOVEL_COVERAGE_RE`), `:392` (`factory_token_efficiency`), `:490` (`cmd_token_efficiency`)
