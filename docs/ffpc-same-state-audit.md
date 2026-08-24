# FFPC same-state audit — the nineteen impure preference pairs

> Factory: `failure-as-fuel-preference-cascade` (sf-cic)
> Dataset: [`rmems/failure-as-fuel-preference-cascade`](https://huggingface.co/datasets/rmems/failure-as-fuel-preference-cascade)
> Audited payload: `data/raw/` at Hub revision `a9eaacfbeae4f66b94ddda5df3b793fda74fd39d`
> Machine-readable audit: [`ffpc-same-state-audit.json`](ffpc-same-state-audit.json)
> Transform: `same-context-preference-curation` 1.0.0
> Contract: [`preference-isolation.md`](preference-isolation.md) §3

**Do not train on the raw payload.** 17 of its 42 published pairs do not hold
`state` constant across `chosen` and `rejected`, and 19 of 42 break the full
same-context contract. The only training-eligible preference file is the
curated export described in §5, which is 100% same-context by construction.

## 1. Hub 17 and local 19 are the same finding

A `same_state` audit compares `chosen.state` against `rejected.state` and
nothing else. The same-context contract also requires
`chosen.proposed_action == rejected.proposed_action`
([`preference-isolation.md`](preference-isolation.md) §3.1), because a pair
that holds state constant and swaps the proposed action still lets a learner
prefer the easier task instead of the better judgment.

Both published numbers are correct measurements of different invariants:

| Statement | Pairs | Measures |
| --- | ---: | --- |
| Hub audit, `same_state = false` | 17 | `state` only |
| Factory scan, impure pairs | 19 | `state` **and** `proposed_action` |

The 19 impure pairs decompose without remainder:

| Divergence | Pairs |
| --- | ---: |
| `state` only | 5 |
| `proposed_action` only | 2 |
| both fields | 12 |
| **impure total** | **19** |

`17 = 5 + 12` state-divergent pairs, and `19 = 17 + 2`. The two pairs a
state-only audit cannot see are `ffpc-r5-002` and `ffpc-r5-003`
(`batch-r05.jsonl` lines 2 and 3): both hold `state` byte-identical and
diverge on `proposed_action`. Neither count is wrong; the state-only count is
a lower bound on same-context contamination.

The issue's "expected ~25 keep" is the same arithmetic: 42 − 17 = 25
same-state pairs. The curated export keeps 30, not 25, because 7 of the 19
impure pairs diverge only by a branch annotation that literally attests the
other side's context, so they are repairable losslessly (§4, §5). The
remaining 12 are excluded.

## 2. Hub raw and local raw are the same bytes

The reconciliation above is not a corpus difference. The published
`data/raw/` payload is byte-identical to the immutable local raw tree at
`outputs/raw/2026-08-17/failure-as-fuel-preference-cascade/`:

| File | Pairs | sha256 |
| --- | ---: | --- |
| `batch-r02.jsonl` | 3 | `0bf326678afb9710616cbad12f9b1ddf807bdb1dda6e29775423a6f3c047db42` |
| `batch-r03.jsonl` | 6 | `cde810a867708751c4a82ab3b3ba808b09c271d903f69a4d4a249666ef246d61` |
| `batch-r04.jsonl` | 6 | `9b7fca02378b50063cc8a2fbf71e7a017051138bececa53eefc98d6ab96bdb25` |
| `batch-r05.jsonl` | 6 | `9a9d54921f73c4eb59cb293c12366eef985a03d410ed77aa44229b7b3fe49a95` |
| `batch-r06.jsonl` | 3 | `5b85ba725e09f68b613359591e4e79d596cac2538b13a938212068af2820589d` |
| `batch-r07.jsonl` | 3 | `1241a25e351d23545a0ef851f346cba234b9b0d35f199f58a4938e1a7e528dc7` |
| `batch-r08.jsonl` | 3 | `9c5f6bf02a161258ea1f775188934f167927f423331c77207a03f1f4a5796799` |
| `batch-r09.jsonl` | 3 | `06541964901f9b173dea0d1772320433896d105e1d5cf6d40d9668c81917a091` |
| `batch-r10.jsonl` | 3 | `973d8e101c863cf386a11b793783cf42354f2006f4db4951dc3307d3e8c5836a` |
| `preferences.jsonl` | 6 | `7bc6f5f549c5ab77996341b6ad9783b1681df8ccfbc35d2f43ee8307556904de` |

Those digests are the ones the dataset's own `provenance.json` declares under
`raw_snapshot`. To prove the two copies scan identically, fetch the Hub
payload read-only and reconcile it against the local tree:

```bash
python3 pipelines/curate_preferences.py reconcile \
  <hub-data-raw> outputs/raw/2026-08-17/failure-as-fuel-preference-cascade
# → "<hub-data-raw> and outputs/... scan identically" (exit 0)
```

`reconcile` fails on three classes of disagreement: records one copy has and
the other does not, curation verdicts that differ, and identical verdicts
reached from different source bytes.

`preferences.jsonl` is the round-1 file and carries a second, thinner schema:
its 6 rows have no top-level `id`, so they are addressed by source line
below. All 6 are excluded.

## 3. The impure pairs

Every pair below is public evidence, addressed by record id where the record
has one and by `file:line` in the raw payload either way. `same_state` is the
Hub-side invariant; `same_proposed_action` is the half a state-only audit does
not measure. The table is generated — regenerate it with
`python3 pipelines/curate_preferences.py audit <source> --markdown`.

<!-- BEGIN GENERATED: curate_preferences audit --markdown -->
| Measure | Pairs |
| --- | ---: |
| Published preference pairs | 42 |
| `same_state = false` (state diverges) | 17 |
| `same_proposed_action = false` (proposal diverges) | 14 |
| Impure pairs (either field diverges) | 19 |
| - state only | 5 |
| - proposed action only | 2 |
| - both fields | 12 |
| - context not comparable | 0 |
| Curated keep (already identical + repaired) | 30 |
| Curated exclude | 12 |
| Curated same-context purity | 100.0% |

| Pair | Source | `same_state` | `same_proposed_action` | Curation | Reason codes |
| --- | --- | --- | --- | --- | --- |
| `ffpc-r2-001` | `batch-r02.jsonl:1` | no | yes | excluded | `BRANCH_SPECIFIC_STATE_METADATA_UNSAFE_TO_NORMALIZE` |
| `ffpc-r2-002` | `batch-r02.jsonl:2` | no | yes | excluded | `BRANCH_SPECIFIC_STATE_METADATA_UNSAFE_TO_NORMALIZE` |
| `ffpc-r2-003` | `batch-r02.jsonl:3` | no | yes | excluded | `BRANCH_SPECIFIC_STATE_METADATA_UNSAFE_TO_NORMALIZE` |
| `ffpc-r3-004` | `batch-r03.jsonl:4` | no | no | repaired | `EXACT_CONTEXT_COPIED_FROM_ATTESTED_REFERENCE`, `BRANCH_ONLY_IDENTITY_NOTE_REMOVED` |
| `ffpc-r3-005` | `batch-r03.jsonl:5` | no | no | repaired | `EXACT_CONTEXT_COPIED_FROM_ATTESTED_REFERENCE`, `BRANCH_ONLY_IDENTITY_NOTE_REMOVED` |
| `ffpc-r3-006` | `batch-r03.jsonl:6` | no | no | repaired | `EXACT_CONTEXT_COPIED_FROM_ATTESTED_REFERENCE`, `BRANCH_ONLY_IDENTITY_NOTE_REMOVED` |
| `ffpc-r4-004` | `batch-r04.jsonl:4` | no | no | repaired | `EXACT_CONTEXT_COPIED_FROM_ATTESTED_REFERENCE`, `BRANCH_ONLY_IDENTITY_NOTE_REMOVED` |
| `ffpc-r4-005` | `batch-r04.jsonl:5` | no | no | repaired | `EXACT_CONTEXT_COPIED_FROM_ATTESTED_REFERENCE`, `BRANCH_ONLY_IDENTITY_NOTE_REMOVED` |
| `ffpc-r4-006` | `batch-r04.jsonl:6` | no | no | repaired | `EXACT_CONTEXT_COPIED_FROM_ATTESTED_REFERENCE`, `BRANCH_ONLY_IDENTITY_NOTE_REMOVED` |
| `ffpc-r5-002` | `batch-r05.jsonl:2` | yes | no | excluded | `PROPOSED_ACTION_CONTEXT_DIVERGES` |
| `ffpc-r5-003` | `batch-r05.jsonl:3` | yes | no | repaired | `EXACT_PROPOSAL_COPIED_FROM_ATTESTED_REFERENCE`, `BRANCH_ONLY_PROPOSAL_ANNOTATION_REMOVED` |
| `ffpc-r6-002` | `batch-r06.jsonl:2` | no | yes | excluded | `POLICY_MEMORY_CONTEXT_DIVERGES` |
| `ffpc-r7-002` | `batch-r07.jsonl:2` | no | yes | excluded | `POLICY_MEMORY_CONTEXT_DIVERGES` |
| _(no record id)_ | `preferences.jsonl:1` | no | no | excluded | `STATE_CONTEXT_DIVERGES`, `PROPOSED_ACTION_CONTEXT_DIVERGES` |
| _(no record id)_ | `preferences.jsonl:2` | no | no | excluded | `STATE_CONTEXT_DIVERGES`, `PROPOSED_ACTION_CONTEXT_DIVERGES` |
| _(no record id)_ | `preferences.jsonl:3` | no | no | excluded | `STATE_CONTEXT_DIVERGES`, `PROPOSED_ACTION_CONTEXT_DIVERGES` |
| _(no record id)_ | `preferences.jsonl:4` | no | no | excluded | `STATE_CONTEXT_DIVERGES`, `PROPOSED_ACTION_CONTEXT_DIVERGES` |
| _(no record id)_ | `preferences.jsonl:5` | no | no | excluded | `STATE_CONTEXT_DIVERGES`, `PROPOSED_ACTION_CONTEXT_DIVERGES` |
| _(no record id)_ | `preferences.jsonl:6` | no | no | excluded | `STATE_CONTEXT_DIVERGES`, `PROPOSED_ACTION_CONTEXT_DIVERGES` |
<!-- END GENERATED -->

Per-pair `context_diff_paths` — the exact leaf paths that differ — are in
[`ffpc-same-state-audit.json`](ffpc-same-state-audit.json).

## 4. Reason codes

| Reason code | Meaning | Decision |
| --- | --- | --- |
| `PREFERENCE_CONTEXT_ALREADY_IDENTICAL` | `state` and `proposed_action` are already canonically equal. | retained |
| `EXACT_CONTEXT_COPIED_FROM_ATTESTED_REFERENCE` + `BRANCH_ONLY_IDENTITY_NOTE_REMOVED` | One branch carries a top-level `identity_note` that literally attests it is identical to the other branch's context; removing exactly that annotation makes the two sides byte-equal. The attested side is replaced by an exact copy of the reference. | repaired |
| `EXACT_PROPOSAL_COPIED_FROM_ATTESTED_REFERENCE` + `BRANCH_ONLY_PROPOSAL_ANNOTATION_REMOVED` | `state` already matches and the proposal differs only in `proposed_action.source` / `proposed_action.snn_readout.note`, where `source` attests an identical proposal to the other branch. | repaired |
| `BRANCH_SPECIFIC_STATE_METADATA_UNSAFE_TO_NORMALIZE` | `state` differs only in branch-scoped bookkeeping (`state.episode_id`, `state.note`). Nothing in the record says which value is the shared one, so normalizing would invent a context. | excluded |
| `POLICY_MEMORY_CONTEXT_DIVERGES` | The two sides carry different `state.agent.gate_memory` — different learned policy at decision time, which is a real context difference, not an annotation. | excluded |
| `STATE_CONTEXT_DIVERGES` | `state` differs outside the narrow annotation cases above. | excluded |
| `PROPOSED_ACTION_CONTEXT_DIVERGES` | `proposed_action` differs outside the narrow annotation cases above. | excluded |

The curation rule is deliberately narrow: repair only where one branch
attests the other's exact context, and exclude otherwise. State is never
silently rewritten to manufacture a match.

## 5. The curated export is the only training-eligible preference file

```bash
python3 pipelines/curate_preferences.py curate <raw-source> \
  --output <new>/preferences.jsonl --manifest <new>/manifest.jsonl
```

| Outcome | Pairs |
| --- | ---: |
| retained unchanged | 23 |
| repaired from an attested reference | 7 |
| **kept** | **30** |
| excluded with reason codes | 12 |
| same-context purity of the kept rows | 100% |

Both destinations must be absent and neither may live inside the source, so
the export never clobbers or rewrites raw evidence. The manifest records, per
source line, the source sha256, the action, the classification, the reason
codes, the diverging leaf paths, and the output sha256. Audited on its own,
the curated preference lane reports `training_ready: true` in
`pipelines/training_audit.py --strict`; the raw payload reports the
`19/42 preference pairs change state or proposal` blocker.

Composing this lane with the other curated lanes into a single release export
is [#23](https://github.com/rmems/synthetic-factory/issues/23); rematerializing
the local corpus is [#4](https://github.com/rmems/synthetic-factory/issues/4).

## 6. What the dataset card must say

The Hub card for `rmems/failure-as-fuel-preference-cascade` must carry a
limitations section citing this audit. Publishing card text is owned by
[#24](https://github.com/rmems/synthetic-factory/issues/24); this is the exact
section it has to add:

```markdown
## Limitations

This raw payload is preference **evidence**, not preference training data.
Of its 42 published pairs, **17 have `same_state = false`**: `chosen` and
`rejected` do not share one canonical `state`. Counting the full same-context
contract — identical `state` *and* identical `proposed_action` — **19 of 42
pairs are impure**. The 2-pair gap is `ffpc-r5-002` and `ffpc-r5-003`, which
hold state constant and diverge on the proposed action.

**Do not train on `data/raw/`.** A DPO or reward-model run over these pairs
can prefer the easier problem instead of the better judgment. The published
per-pair ID list, reason codes, and diverging field paths are in the factory
repository at `docs/ffpc-same-state-audit.md`.

Curation retains 30 of the 42 pairs at 100% same-context purity: 23 are
already identical and 7 diverge only by a branch annotation that attests the
other side's exact context. The remaining 12 are excluded with machine-readable
reason codes. That curated export, not this payload, is the training-ready
preference file.
```

## 7. Re-running this audit

```bash
# Public ID list plus reason codes, as JSON or as the Markdown above.
python3 pipelines/curate_preferences.py audit <source> --json
python3 pipelines/curate_preferences.py audit <source> --markdown

# Fail closed if a corpus has drifted from the published audit.
python3 pipelines/curate_preferences.py audit <source> \
  --expect docs/ffpc-same-state-audit.json

# Prove two copies of the corpus scan identically.
python3 pipelines/curate_preferences.py reconcile <source-a> <source-b>
```

`audit --expect` compares the summary, the impure-pair set, and every pair's
source sha256, record id, action, classification, reason codes, and diverging
field paths. It exits non-zero and names each difference on drift.
