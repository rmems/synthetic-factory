# Synthetic Corpus Curation Design

Date: 2026-08-17
Approved by: user instruction, “Create beads over those next move and start
sending subagents to start working on it”
Coordinator: codex/gpt-5.6-sol max
Tracking epic: `sf-c5l`

## Objective

Transform the immutable `outputs/raw/2026-08-17` evidence into a new,
versioned cleaned corpus that satisfies the strict training-readiness audit.
The curation pass must be deterministic, reversible, and explicit about every
repair, exclusion, and quarantine decision. It must never rewrite raw input or
silently convert uncertain examples into apparently authoritative training
data.

## Chosen approach

Use six independent, record-level curation lanes followed by one integration
and promotion gate.

Alternatives considered:

1. **One monolithic cleanup script.** Simple to invoke, but difficult to review,
   test, or parallelize safely. A bug can conflate identity, preference,
   reward, timing, and privacy decisions.
2. **Six isolated transforms plus a final gate (chosen).** Each lane owns a
   narrow semantic concern and a disjoint implementation surface. The final
   gate composes them into a brand-new destination only after every lane has
   passed targeted tests.
3. **Hand-edit the existing cleaned tree.** Fastest for a few records, but not
   reproducible, not reversible, and incompatible with raw-evidence integrity.

## Invariants

- `outputs/raw/2026-08-17` remains byte-identical.
- Existing `outputs/cleaned/2026-08-17` content is user-owned diagnostic output
  and is not overwritten or used as the final destination.
- Each transform is deterministic and idempotent on the same input.
- A repair is allowed only when source evidence supports one unambiguous
  interpretation. Otherwise the record is excluded or quarantined.
- Every changed or excluded record receives a manifest entry with source path,
  source line, source hash, transform name and version, action, reason codes,
  output ID when retained, and output hash when emitted.
- Original values remain recoverable from raw input or an explicitly linked
  sidecar. Curated records do not pretend that generated scenarios are real
  measurements.
- No curated coding example contains hidden chain-of-thought fields.
- No magnitude-weighted cross-factory training set is emitted until the reward
  ontology says the participating records are calibrated and comparable.
- Promotion uses a brand-new path and the existing no-clobber promoter.

## Work graph

### `sf-c5l.1` — Bridge timing

Repair or quarantine the five known globally unsorted event streams in Bridge
rounds r02 and r03. Stable sorting is acceptable only when events carry one
global clock and sorting does not change an explicit causal grouping. Ambiguous
streams are quarantined with a machine-readable reason. The lane owns
`pipelines/curate_bridge.py` and `tests/test_curate_bridge.py`.

### `sf-c5l.2` — Identity and provenance

Assign deterministic canonical top-level IDs and canonical provenance to every
retained record. IDs derive from stable source identity plus transform version,
not output ordering. Emit a reversible mapping for legacy IDs and nested
trajectory states. The lane owns `pipelines/curate_identity.py` and
`tests/test_curate_identity.py`.

### `sf-c5l.3` — Preference purity

Require chosen and rejected sides to share the same canonical state and
proposed action. Repair only when one side contains an exact source-supported
copy of the intended context; otherwise exclude the pair. The lane owns
`pipelines/curate_preferences.py` and `tests/test_curate_preferences.py`.

### `sf-c5l.4` — Reward ontology

Define reward ontology v1, map source reward layouts conservatively, and label
each record as `magnitude_comparable`, `sign_order_only`, or
`exclude_from_reward_training`. Preserve source reward structures in sidecars.
The lane owns `schemas/reward-ontology-v1.schema.json`,
`pipelines/curate_rewards.py`, and `tests/test_curate_rewards.py`.

### `sf-c5l.5` — Coding observability

Remove legacy `thought` fields from curated coding episodes. Retain a step only
when a concise `decision_basis` can be grounded in visible plan, tool call,
observation, or reflection evidence; otherwise exclude it with a reason. The
lane owns `pipelines/curate_coding.py` and `tests/test_curate_coding.py`.

### `sf-c5l.6` — Tag taxonomy

Map free-form tags into a compact controlled vocabulary without guessing at
unknown semantics. Preserve source tags in reversible provenance. The lane owns
`schemas/tag-taxonomy-v1.json`, `pipelines/curate_tags.py`, and
`tests/test_curate_tags.py`.

### `sf-c5l.7` — Integration and promotion gate

This task is blocked by all six lanes. It composes transforms in a documented
order, writes one new cleaned destination, runs all structural and strict audit
gates, records a stratified sample review, and promotes to a new curated path
only if `training_ready` is true.

## Parallel execution

At most five specialist agents run concurrently. The first wave covers Bridge,
identity/provenance, preference purity, reward ontology, and coding
observability. Tag normalization waits for a free slot. Agents may edit only
their declared files and must not touch raw data, existing cleaned data,
`.beads`, shared validators, the workflow skill, or another lane's files.

The coordinator owns Bead assignment, integration, shared-validator changes,
full-suite testing, commits, and status transitions. Agent self-reports are
evidence to review, not authority to close a Bead.

## Verification

Each lane must provide focused unit tests using temporary directories and
minimal fixtures. Before a lane closes, the coordinator reviews the diff,
runs its targeted tests, runs the full suite, and reruns the raw strict audit to
prove the source corpus was not changed.

The final gate additionally requires:

1. `training_ready: true` on a brand-new cleaned destination.
2. No parse, invariant, reward-arithmetic, duplicate-ID, or exact-duplicate
   errors.
3. Canonical ID and provenance coverage of 100 percent for retained records.
4. Preference context purity of 100 percent.
5. No curated `thought` fields.
6. A compact controlled tag vocabulary with all source tags recoverable.
7. Explicit reward-comparability classes and no unsafe magnitude mixing.
8. A recorded human review sampled across factory, record kind, safety-gate
   decision, repair action, and exclusion reason.
9. A manifest containing source and output hashes, transform versions, counts,
   exclusions, and quarantine decisions.

## Non-goals

- Do not generate new synthetic trajectories in this curation pass.
- Do not resume any previous continuous workflow.
- Do not publish to Hugging Face or push a branch without a separate request.
- Do not silently fill missing provenance, repair ambiguous event timing, or
  invent a comparable reward magnitude.
- Do not close the epic merely because scripts exist; closure requires the
  final audited corpus and review evidence.
