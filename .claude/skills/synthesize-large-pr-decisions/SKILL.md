---
name: synthesize-large-pr-decisions
description: "When cloud review refuses a large PR: research via parallel subagents, aggregate findings into a ledger, synthesize discrete decisions, implement with focused tests, verify against fixture regression. Use this skill when cloud review refuses a PR as too large (>27 files), or you have multiple massive feature PRs with accumulated gate failures that need triage and synthesis before landing."
trigger: "Use this skill when cloud review refuses a PR as too large (>27 files), or you have multiple massive feature PRs with accumulated gate failures that need triage and synthesis before landing."
author: montoyaraul34
source_sessions:
  - montoyaraul34_montoyaraul34's Organization_default_344701ce-d2c4-426c-96b1-716c94aac4d3
contributors:
  - montoyaraul34
version: 1
created_by_agent: claude_code
created_at: 2026-09-07T23:07:48.907Z
updated_at: 2026-09-07T23:07:48.907Z
---

# Synthesize and land large PRs when cloud review fails

Paths are relative to the repository root.

## When to use

Use this skill when:
- Cloud review (Copilot ultra, CodeRabbit) refuses a PR as too large (>27 files, >15k lines)
- You have multiple massive feature PRs with accumulated quality-gate failures that block landing as a stack
- You need to separate "what is broken" from "what to fix now" without blindly splitting or accepting all debt

## Core insight

Instead of splitting massive PRs on arbitrary line counts or attempting to fix every finding, conduct a local multi-angle research phase, aggregate findings into a structured ledger, synthesize them into discrete decisions (D1, D2, ... D8), and implement only the decided items with focused test coverage. This avoids premature splits and allows progressive landing with verification at each step.

## Workflow

### 1. Research phase (parallel subagents)

Launch independent specialized subagents for analysis:
- **Bugs and defects**: Code review for correctness, fail-closed behavior, guard coverage, contract violations
- **Structural debt**: Module sizes, import binding, primitive duplication (JSON encode, JSONL I/O, raw guard), function complexity
- **Gate state**: Inventory CI checks per PR, blocker vs warning, trend across merged PRs
- **Strategy synthesis**: Combine findings into discrete decisions with priority and concrete impact

Each subagent produces a standalone report; aggregate offline before deciding.

### 2. Aggregation phase

Create a findings ledger (JSON or markdown):
- **Verified findings**: Each defect reproduced against the PR head with exact failure case and test ID
- **Gate inventory**: All checks per PR, grouped by type (unit, static analysis, coverage, vendor), trending
- **Duplication matrix**: Which modules re-implement the same primitives (canonical JSON, JSONL, raw guard, validators)
- **Module structure**: Line counts, definition counts, longest functions, import patterns
- **Conflict analysis**: File overlap between PRs, decision dependencies

Store this ledger in project memory and reference it throughout implementation.

### 3. Synthesis phase

Analyze the ledger to identify discrete decisions:
- **D1, D2, ... D8**: Specific, implementable changes (e.g., "extract shared JSON encoder," "add family-owned label declarations," "support B-D value shapes in measurement validation")
- **Prioritize by impact**: What blocks merge? What is debt? What is future-family-specific?
- **Respect closed decisions**: Do not reopen earlier design choices (#172's envelope consolidation, row-15 held measurements) without explicit evidence
- **Track blockers**: D2 may depend on D1; D3 may need evidence from a reproduction pass before approval

Document each decision with:
- Exact change scope (files, functions, test matrix)
- What findings this resolves (ledger reproducers)
- Which blockers remain or are deferred
- Any held assumptions (e.g., "row 15 held," "D3 needs cases B-D verified")

### 4. Implementation phase

For each approved decision:
1. **Write failing regressions first**: Capture the exact issue from the ledger
2. **Implement the minimal fix**: Only the decided change, no adjacent refactoring or cleanup
3. **Preserve existing behavior**: Test coverage, fail-closed semantics, metadata, boundary decisions
4. **Record assumptions** in code comments or PR body (e.g., "row 15 held" means a specific test case deferred)
5. **Push to branch and watch CI** in background; do not merge until all verification passes

### 5. Verification phase

For each implemented decision:
- **Focused tests pass**: New failing regressions must pass on the new commit
- **Fixture regression**: Run on all committed records (e.g., 102 from #138); no records should gain new findings
- **Ledger reproducers**: All exact cases from the findings ledger must be caught (e.g., A–F measurement shapes)
- **Main comparison**: Unit suite on branch vs exact main must show identical pre-existing failures
- **CI gates**: Coverage %, new Codacy/CodeScene/qlty/Qodana issues (count, category, blocker vs debt)

Stop implementation if any verification fails; do not suppress findings or lower coverage targets.

### 6. Reporting phase

For each decided item, report:
- **What was implemented**: Commit SHA, files changed, test count (e.g., "91 direct tests, 12 new")
- **Verification**: Pass/fail for focused tests, fixture, ledger, main comparison, coverage delta
- **Gate status**: Which checks pass/fail, which items are new (blocker vs warning)
- **Disposition**: What this fixes, what remains as debt, what is held and why

Classify remaining findings by concrete impact:
- **Blocker**: Prevents merge or causes wrong behavior
- **Debt**: Accumulated patterns (duplication, complexity, coverage gap) for future slices
- **Deferred/held**: Requires evidence or decision before implementation (e.g., "D3 held until B-D cases reproduced")
- **Future work**: Feature-specific enhancements (e.g., fault recovery config, energy meter identity evidence)
- **Non-blocking**: Style, vendor warnings on legacy code, or architectural decisions left unchanged

## Gotchas

- **Cloud refuses at 27 files; size itself is the blocker.** Do not split to get below 3k lines without dependency analysis. Splitting must follow structure, not line count.
- **Fixture regression is ground truth.** A fix that passes new tests but stops catching defects on production data is a regression, not a fix. Test on all historical records.
- **Ledger reproducers must stay caught.** If a case from the findings ledger stops being reported after implementation, the fix is incomplete.
- **Do not auto-fix every static finding.** Codacy, qlty, CodeScene may report on code already red in main. Classify each finding by whether it is a blocker, debt, or already-known issue before fixing.
- **Main comparison proves no new regression.** Unit suite failures identical at main and your branch mean you have not introduced a new bug.
- **Hold is not abandoned.** If D3 is held until cases B-D reproduce, do not implement D3 early. Move to the next unblocked decision (D4, D6, etc.) and return to D3 when approval comes.
- **Do not introduce frameworks or engines.** Avoid schema validation engines, indefinitely growing keyword blacklists, or broad envelope consolidations in a fix pass. Keep changes focused and structural.

## Environment

Tools:
- `gh pr view/diff/checks` for PR state and CI results
- `git log/diff` for change analysis
- `python3 -m unittest` for local verification
- Fixture runners (e.g., `python3 pipelines/census.py`) for regression checks
- Subagents (Agent tool) for parallel independent research

Memory:
- Store findings ledger in project memory or Ogham
- Record decisions in issue comments and PR body (e.g., "D1 implemented in commit abc123")
- Track held items and blockers in decision comments
- Scratchpad channels (Slack, Notion) for team visibility

## Example: Handling #138 (26k lines, cloud refuses)

1. **Research**: Cloud refuses at 27 files. Launch 3 subagents (bugs/complexity, duplication, strategy).
2. **Ledger**: 15 verified findings: unbound oracle identity, fixture builder bypassing raw guard, unsupported value shapes in measurements, duplicated primitives across PRs.
3. **Decisions**: D1-D4 (bugs/coverage), D3 held until cases B-D verified, D6-D8 deferred to family slices.
4. **Implement D1, D4**: Focused tests, green CI, verify D1+D4 together.
5. **Implement D2**: Family-owned label declarations, 10 tests, fixture regression pass, main comparison identical.
6. **Hold D3**: Wait for approval. Implement D6 (writer framing policy) while waiting.
7. **Implement D3 (after approval)**: Add B-D measurement shape support, verify all 18-row test matrix, fixture and ledger pass, CI green.
8. **Report**: All decided items verified, remaining findings classified as debt (complexity, duplication) or future (fault recovery, energy meter identity), coverage gaps identified for test slices.

Result: #190 holds only approved changes, is testable in isolation, and can land progressively without accumulating unknowns.
