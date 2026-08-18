# Synthetic Factory Hardening Design

Date: 2026-08-17  
Approved by: user reply, “Okay do your magic”  
Implementer: codex/gpt-5.6-sol max

## Objective

Turn the existing synthetic-data scenario laboratory into a safer, truthful
factory without rewriting the append-only raw corpus or launching more
generation. The hardened path must distinguish shape validity from semantic
training readiness, prevent round overwrites mechanically, stop dispatching
after systemic failures, and publish only verified round artifacts.

## Chosen approach

Implement an operational hardening slice around the current v1 corpus.

Alternatives considered:

1. **Documentation-only repair.** Cheapest, but leaves filename-based frontiers,
   prompt-only overwrite protection, and misleading validation intact.
2. **Operational hardening around v1 (chosen).** Adds transaction boundaries,
   semantic checks, honest reporting, and a stricter next-round contract while
   preserving all raw data.
3. **Immediate schema-v2 corpus rewrite.** Ultimately useful, but too broad for
   a safe first change because it would mix tooling fixes with irreversible data
   transformation and curation decisions.

## Scope

### 1. Truthful validation and audit

- Keep `validate_run.py` as the structural gate, but make it robust to malformed
  episode steps and enforce global bridge-event ordering.
- Make `check_records.py` understand existing reward layouts:
  numeric siblings, `{value, detail}` components, and weighted nested
  `components`/`actual` maps. Unsupported layouts become explicit warnings,
  not fabricated arithmetic failures.
- Check record IDs globally across files rather than resetting per file.
- Add a training-readiness audit that reports provenance coverage, canonical ID
  coverage, preference-context purity, decision balance, token-size estimates,
  reward-shape entropy, tag entropy, and exact duplicates.
- Make the skill report structural and semantic results separately.

### 2. Atomic round lifecycle

- Add a deterministic transaction helper with `reserve`, `publish`, and
  `frontier` operations.
- `reserve` uses exclusive file creation and creates a unique staging directory.
- Agents write only inside that staging directory.
- `publish` validates the staged JSONL, verifies the expected quota, refuses all
  target collisions, publishes with no-clobber links, records SHA-256 hashes,
  and writes a completion marker.
- Frontiers advance only through completion markers after marker mode is
  enabled. Existing pre-marker batches become a recorded legacy baseline.
- Failed staging areas remain inspectable; they never advance the frontier.

### 3. Bounded workflow behavior

- Keep at most five concurrent factory loops.
- Stop a factory loop after its first failed round instead of dispatching every
  remaining round into an exhausted session.
- Require each successful agent result to name its completion marker and exact
  quota.
- Remove collision suffixes as a normal path: a collision is a failed
  reservation, not permission to create ambiguous `rNNc` rounds.

### 4. Contract and skill repair

- Require one JSON object per line, stable IDs, explicit provenance, reconciled
  reward aggregation, and observable decision evidence rather than invented
  hidden chain-of-thought.
- Keep the long-form NOTES critique as a sidecar, not model-visible training
  content.
- Make `.claude/skills/run-synthetic-factory` canonical and expose the Codex
  `.agents` path through a single-source link so the two copies cannot drift.
- Add the transaction and audit commands to the skill; retain snapshot and
  read-only validation workflows.

### 5. Promotion safety

- Refuse a cleaned destination equal to or nested beneath raw input.
- Do not regenerate or overwrite the existing cleaned tree in this change.
- Document that curated output remains blocked until semantic checks and
  provenance gates pass.

## Non-goals

- Do not alter any file under `outputs/raw/2026-08-17`.
- Do not rewrite the existing 138-record cleaned tree.
- Do not normalize the full reward corpus in place.
- Do not launch factory agents or create new trajectories.
- Do not publish to Hugging Face, push a branch, or open a pull request.

## Verification

The change is complete when:

1. Existing unit tests pass and new tests cover reward layouts, global IDs,
   malformed steps, sorted bridge events, reservation races, no-clobber
   publication, quotas, completion-marker frontiers, and circuit-break logic.
2. The 189-record raw corpus parses; semantic output truthfully identifies the
   five legacy unsorted bridge records without the previous reward false
   positives.
3. The transaction smoke test publishes a staged round once, refuses a second
   publication, and advances the frontier only after completion.
4. The skill validator passes for the canonical skill and its `.agents` entry.
5. CodeRabbit critical/major findings are either fixed or explicitly rejected
   with evidence.
6. A focused commit contains only intentional hardening files and carries the
   requested Codex co-author trailer.
7. The existing Notion page is updated and re-fetched to verify the work log.

