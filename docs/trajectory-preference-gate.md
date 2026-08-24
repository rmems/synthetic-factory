# Trajectory-Pair Preference Gate

> Pipeline: `pipelines/curate_trajectory_preferences.py`
> Tests: `tests/test_curate_trajectory_preferences.py`
> Companion: `docs/preference-isolation.md` (Fable same-state gate)
> Tracking: [rmems/synthetic-factory#35](https://github.com/rmems/synthetic-factory/issues/35)

## 1. Why a second preference lane exists

`pipelines/curate_preferences.py` is the **Fable same-state/same-proposal
gate**. It compares `chosen.state` / `rejected.state` and
`chosen.proposed_action` / `rejected.proposed_action` and retains a pair only
when both subtrees are canonically identical. That gate assumes the
ThalamicTrajectory preference schema produced by
`failure-as-fuel-preference-cascade`.

The Grok 4.6 preference dumps do not use that schema. Their sides are
**trajectories**:

```json
{
  "id": "tup-r01-atomic-manifest",
  "goal": "Publish output/manifest.json so readers never see a partial object.",
  "outcome": "...", "reward": {...}, "meta": {...}, "critique": "...",
  "chosen":   {"steps": [{"n": 1, "decision_basis": "...", "tool_call": {...},
                          "observation": "..."}], "outcome": "...", "reward": {...}},
  "rejected": {"steps": [...], "outcome": "...", "reward": {...}}
}
```

There is no `state` and no `proposed_action` to compare, so the same-state gate
returned `PREFERENCE_CONTEXT_MISSING_OR_INVALID` for every eligible pair and
yielded nothing (measured 0% in `EXP-G46-PREF-YIELD-001`; explained in
`EXP-G46-PREF-CONTEXT-SCHEMA-001`).

The fix is **not** to inject fabricated `state` / `proposed_action` into raw
records. It is this second lane, which gates the contrast a trajectory pair
actually carries. `curate_preferences.py` now names such pairs
`PREFERENCE_PAIR_IS_A_TRAJECTORY_PAIR` (classification
`trajectory_pair_out_of_scope`) instead of calling them malformed, and reports
`summary.out_of_scope_trajectory_pairs` so a 0% same-state yield is readable.

## 2. Lane routing (denominators never mix)

| Record | Routed to | Action here |
|---|---|---|
| Both sides carry dict `state` **and** `proposed_action` | `curate_preferences.py` | `skipped` — `SAME_STATE_PAIR_DEFERRED_TO_CURATE_PREFERENCES` |
| Both sides carry `steps` | this gate | keep / repair / reject |
| No `chosen`/`rejected` (for example leftover mill episodes, [#30](https://github.com/rmems/synthetic-factory/issues/30)) | neither | `skipped` — `NOT_A_PREFERENCE_PAIR_RECORD` |
| `chosen`/`rejected` present but not objects | this gate | `excluded` — `TRAJECTORY_PAIR_SIDES_NOT_OBJECTS` |

`trajectory_pairs_considered` counts only the pairs this gate judges. Skipped
records are reported separately, so a Grok retain rate and a Fable FFPC retain
rate are never averaged into one figure.

## 3. Keep

A pair is `retained` when all of the following hold, on the thought-stripped
copy:

1. **Shared goal.** Every present goal string (top-level, `chosen.goal`,
   `rejected.goal`) is identical after whitespace normalization, and either the
   top-level `goal` is present or both side goals are.
2. **Shared step prefix > 0.** The leading steps of both sides are byte-equal
   under canonical JSON (`curate_agentic.prefix_overlap`).
3. **Trajectories are not identical.** A pair with the same `steps` on both
   sides carries no preference signal.
4. **`outcome` diverges.** Both sides have an `outcome` and they differ.
5. **`reward` diverges.** Both sides have a `reward` and they differ.

Reason code on the keep path: `TRAJECTORY_PAIR_SHARED_GOAL_AND_PREFIX`.

## 4. Repair

Repairs are narrow, evidence-supported, and never invent context.

| Repair | Reason code | Rule |
|---|---|---|
| Hidden reasoning removed | `HIDDEN_THOUGHT_REMOVED` | Recursively drop `thought`, `chain_of_thought`, `scratch`, `inner_monologue` (shared vocabulary with `curate_agentic.py`) |
| Goal whitespace normalized | `TRAJECTORY_GOAL_WHITESPACE_NORMALIZED` | Only when two or more goal strings are present, are not byte-identical, and *are* identical after whitespace normalization |

A repaired record is emitted only if it then passes every keep rule; the
curator re-checks the emitted record and raises rather than writing a pair that
fails its own gate. Repair is idempotent: re-curating a repaired record yields
`retained` and an identical record.

## 5. Reject

| Reason code | Meaning |
|---|---|
| `TRAJECTORY_RECORD_NOT_AN_OBJECT` | Line is not a JSON object |
| `TRAJECTORY_PAIR_SIDES_NOT_OBJECTS` | `chosen` / `rejected` present but not objects |
| `TRAJECTORY_STEPS_MISSING_OR_INVALID` | A side has no `steps` list |
| `TRAJECTORY_STEPS_EMPTY` | A side has an empty `steps` list |
| `PREFERENCE_GOAL_MISSING` / `PREFERENCE_GOAL_NOT_TEXT` / `PREFERENCE_GOAL_DIVERGES` | Goal rules (vocabulary shared with `curate_agentic.py`) |
| `TRAJECTORY_PAIR_IDENTICAL` | Both sides have identical `steps` |
| `TRAJECTORY_PREFIX_OVERLAP_ABSENT` | Zero shared leading steps |
| `FIRST_STEP_DIFFERS_BY_BRANCH_LABEL_ONLY` | Disclosure note on a zero-prefix reject (Section 6) |
| `TRAJECTORY_OUTCOME_MISSING` / `TRAJECTORY_OUTCOME_DOES_NOT_DIVERGE` | Outcome rules |
| `TRAJECTORY_REWARD_MISSING` / `TRAJECTORY_REWARD_DOES_NOT_DIVERGE` | Reward rules |

Every applicable reason is reported for one record, in a fixed order, so a
manifest entry is fully diagnostic and byte-stable across runs.

## 6. The zero-prefix tool-use pairs

`curate_agentic.py` retains all published Grok preference pairs and only notes
`PREFIX_OVERLAP_NOTED`. That 100% retain figure hides a real defect: in
`tool-use-preference-pairs`, **36 of 6192 pairs have no shared prefix at all**.

Inspecting them shows the divergence is at step 1 and is *only* the branch
label — the `decision_basis` text ends with "— chosen policy starts by locating
the target." on one side and "— rejected policy starts by locating the target."
on the other. That is native impurity: the trajectory names its own branch, so
a learner can separate the sides on a label token instead of on judgment.

This gate therefore **excludes** all 36 with `TRAJECTORY_PREFIX_OVERLAP_ABSENT`
and additionally names the cause with
`FIRST_STEP_DIFFERS_BY_BRANCH_LABEL_ONLY`, surfaced in the summary as
`prefix_overlap_absent_pairs` and `branch_label_only_first_step_pairs`. The
gate never rewrites the leaked text — repairing generated step text would
fabricate evidence, and the fix belongs upstream in generation.

## 7. Measured yield on the published dumps

Read-only scans of the local Hub mirrors under `/home/raulmc/rmems/hf/grok-4.6/`
(no writes, raw untouched):

| Dump | Lines | Pairs considered | Retained | Excluded | Skipped |
|---|---:|---:|---:|---:|---:|
| `code-review-preference-pairs` | 2976 | 2964 | 2964 (100.0%) | 0 | 12 mill episodes ([#30](https://github.com/rmems/synthetic-factory/issues/30)) |
| `tool-use-preference-pairs` | 6192 | 6192 | 6156 (99.42%) | 36 zero-prefix | 0 |
| `tests/fixtures/preference-purity` (Fable FFPC) | 42 | 0 | 0 | 0 | 42 same-state |

## 8. Commands

```bash
# Read-only classification, human or JSON
python3 pipelines/curate_trajectory_preferences.py scan <source>
python3 pipelines/curate_trajectory_preferences.py scan <source> --json

# Write a curated view plus a per-record manifest (both must be absent)
python3 pipelines/curate_trajectory_preferences.py curate <source> \
  --output <new-pairs.jsonl> --manifest <new-manifest.jsonl>
```

Safety rules enforced by the CLI:

- Sources are read only; the curator never writes into its source tree.
- Destinations under `outputs/raw/` are refused outright.
- Both destinations must be absent; writes use `O_EXCL` and are fsynced.
- If a curated view of a Hub dataset is wanted, clone the Hub repo into a
  separate writable workspace. `/home/raulmc/rmems/hf/` is a read-only mirror
  of published evidence.

## 9. Out of scope

- Fable FFPC impurity ([#4](https://github.com/rmems/synthetic-factory/issues/4),
  [#25](https://github.com/rmems/synthetic-factory/issues/25)) — pairs that
  *have* `state` / `proposed_action` and diverge.
- Independent preference arms / generation isolation
  ([#11](https://github.com/rmems/synthetic-factory/issues/11)).
- Leftover mill episodes in `code-review-preference-pairs`
  ([#30](https://github.com/rmems/synthetic-factory/issues/30)) — skipped and
  counted here, quarantined there.
- Training. This gate defines training-readiness for one schema; it does not
  publish a training corpus.
