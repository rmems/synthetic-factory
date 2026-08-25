# Payload-kind census: `rmems/multi-agent-ouroboros-swarm`

Finding for [synthetic-factory#75](https://github.com/rmems/synthetic-factory/issues/75)
(`PAYLOAD_KIND_MISMATCH`). Audited 2026-08-23, read-only.

Machine-readable form: [`ouroboros-swarm-payload-kind.json`](ouroboros-swarm-payload-kind.json).
Operator deliverable: [`ouroboros-swarm-payload-kind.card.md`](ouroboros-swarm-payload-kind.card.md).

## Verdict

**The issue's count is correct.** All 14 published JSONL records are
thalamic-gate wraps. Zero are swarm trajectories.

The card sold the payload as "14 raw **multi-agent** records" of "Synthetic
multi-agent trajectories for delegation, critique, conflict resolution,
recursive improvement, and coordinated densification". What is actually
published is 14 single-decision safety-gate adjudications sharing one schema.

One nuance the issue understates, and the corrected card now carries: the
mislabel is about the **record kind**, not about the subject matter. 9 of the
14 records genuinely stage a multi-actor scenario inside `state`. What no
record contains is a swarm *trajectory* — a turn-by-turn exchange between
agents as the training unit. The swarm dialogue exists, but only as markdown
sidecars.

## What was audited

`~/rmems/hf/fable-5/multi-agent-ouroboros-swarm/` is a **card-only** clone: it
holds `README.md`, `provenance.json`, `release-status.json`, and
`.gitattributes`, and no `data/` tree. The payload census therefore comes from
the factory source at `outputs/raw/2026-08-17/multi-agent-ouroboros-swarm`
(gitignored here), and is tied to the public release by digest:

> All 13 `data/raw/*.jsonl` SHA-256 digests declared in the Hub
> `provenance.json` `raw_snapshot` (revision
> `c287048233f1f5724b50d0dc17f4c592e2ca5159`) are **byte-identical** to the
> local factory files of the same name.

So the census below describes exactly the bytes the public release declares
immutable. Nothing under `outputs/raw/` or `~/rmems/hf/` was written.

## Record census

| Measure | Value |
| --- | --- |
| JSONL files | 13 |
| Records | 14 |
| Parse failures | 0 |
| Total JSONL bytes | 328,743 (0.329 MB) |
| Distinct top-level key sets | **1** |
| Thalamic-gate wrap records | **14 / 14** |
| Swarm-trajectory records | **0 / 14** |
| Records with a multi-actor `state` | 9 / 14 |
| Records naming peers under `state.agents` | 7 / 14 |
| Records with hidden proposer reasoning | 14 / 14 |
| Records with a public `decision_basis` | 0 / 14 |

Every record has exactly these seven top-level keys: `executed_action`,
`future_outcome`, `meta`, `proposed_action`, `reward_components`,
`safety_decision`, `state`. That is the wrap family published by
`rmems/thalamic-relay-trajectories`. The trajectory classifier does not infer
shape from arbitrary key names: it recursively searches `conversation`,
`messages`, `transcript`, and `turns` arrays and requires at least two
content-bearing turns from distinct actors. None of the 14 records contains
such an exchange.

All 14 are dest-stamped `meta.factory = "multi-agent-ouroboros-swarm"`, so this
is a labelling defect at the destination, not foreign leftover-mill records.

Gate outcomes: **3 ACCEPT, 6 MODIFY, 5 REJECT.**

## Per-record classification

`multi-actor state` lists the `state` keys that stage a multi-actor scenario.
`hidden` is the field carrying the proposer's private deliberation.

| Record id | Round | Gate | Multi-actor `state` | Named gate | Hidden |
| --- | --- | --- | --- | --- | --- |
| `batch-r02.jsonl#L1` | 2 | ACCEPT | — | — | `internal_reasoning` |
| `batch-r03.jsonl#L1` | 3 | MODIFY | `multi_agent` | — | `internal_reasoning` |
| `batch-r04.jsonl#L1` | 4 | REJECT | `agents` (5) | TG-1 | `internal_reasoning` |
| `batch-r05.jsonl#L1` | 5 | ACCEPT | `agents` (6) | TG-2 | `internal_reasoning` |
| `batch-r06.jsonl#L1` | 6 | MODIFY | `agents` (6) | TG-3 | `internal_reasoning_verbatim` |
| `batch-r07.jsonl#L1` | 7 | REJECT | `agents` (4) | TG-S1 | `internal_reasoning_verbatim` |
| `batch-r08.jsonl#L1` | 8 | MODIFY | `agents` (4) | TG-Z1 | `internal_reasoning_verbatim` |
| `batch-r09.jsonl#L1` | 9 | ACCEPT | `agents` (5) | TG-OLF-3 | `internal_reasoning_verbatim` |
| `batch-r10.jsonl#L1` | 10 | REJECT | `agents` (6) | TG-AXL-5 | `internal_reasoning_verbatim` |
| `batch-r11.jsonl#L1` | 11 | MODIFY | — | TG-HYD-2 | `internal_reasoning` |
| `batch-r12.jsonl#L1` | 12 | REJECT | — | TG-BAS-9 | `internal_reasoning_verbatim` |
| `batch-r13.jsonl#L1` | 13 | MODIFY | — | TG-CAN-7 | `internal_reasoning_verbatim` |
| `final-trajectories.jsonl#L1` | 2 | MODIFY | `fleet`, `orchestrator` | — | `internal_reasoning` |
| `final-trajectories.jsonl#L2` | 2 | REJECT | — | — | `internal_reasoning` |

The 7 records with `state.agents` name peer agents and a quorum rule — for
example `batch-r05.jsonl#L1` lists `F1-A`, `F2-A`, `SUB-A`, `DER-A`, `CREW-D`,
the gate `TG-2`, and a `quorum_rule` requiring three consents before escalation.
The census excludes structural `protocol` and `quorum_rule` mapping entries
from participant IDs. The remaining entries are real coordination content. It
is still one gate adjudication per record, and the negotiation that produced it
is narrated in prose fields, not recorded as agent turns.

## Where the swarm content actually lives

The factory tree carries 13 `swarm-transcript*.md` files (one per JSONL file),
13 `NOTES*.md` files, and 16 `build-*.py` / `sim-*.py` scripts. These are the
Hub's `data/metadata/` sidecars. They are not viewer rows and not JSONL
training records, and the corrected card says so explicitly.

## Not fixed here

- **Reward-component arithmetic.** `reward_components` uses a per-record
  vocabulary rather than one fixed component set — for example r02 weights
  `task_progress`/`safety`/`efficiency`/`exploration`/`coherence`, r05 weights
  `task_progress`/`safety_alignment`/`efficiency`/`coordination_integrity`/
  `privacy_ethics`/`gate_calibration`, and r12 adds `calibration` and
  `human_team`. PR #97 reports 3 reward-arithmetic blockers that make
  `export_hf` refuse this dataset. That defect is owned by the reward lanes and
  is untouched here; the corrected card only notes that curation must resolve
  it.
- **Hidden supervision** on all 14 wraps is tracked as
  [#26](https://github.com/rmems/synthetic-factory/issues/26). The corrected
  card discloses it as evidence rather than re-filing it.
- **`release-status.json` license drift** is tracked as
  [#24](https://github.com/rmems/synthetic-factory/issues/24) / PR #80. The
  corrected card leaves the `## License` section exactly as PR #80 expects it,
  and drops only the stale "a data license is declared" clause from the
  remaining-gates sentence, since Apache-2.0 is already declared on the card and
  in `LICENSE`.

## What changed in this repository

`pipelines/verify_hf_release.py` was the reason the mislabel survived: its
`REQUIRED_PURPOSE_TEXT` **required** the card to say "delegation, critique,
conflict resolution", so the verifier reported `OK` for this repository while
the card misdescribed its own payload.

- `REQUIRED_PURPOSE_TEXT["rmems/multi-agent-ouroboros-swarm"]` is now
  `"safety-gate adjudication trajectories"`.
- A new `REQUIRED_PAYLOAD_DISCLOSURE` mapping requires three payload-kind
  disclosures inside the `## Published raw payload` section for this
  repository: `thalamic-gate wrap schema`, `7 of the 14 records`, and
  `sidecars, not JSONL training records`. Repositories absent from the mapping
  are unaffected.

`tests/test_ouroboros_swarm_payload_kind.py` pins the finding. Its
`CommittedCensusContract` class always runs and needs no raw tree; its
`RawCorpusCensusFidelity` class re-derives the census from
`outputs/raw/2026-08-17/multi-agent-ouroboros-swarm` and is skipped where that
gitignored tree is absent, so CI stays green without the mirror.

## Operator action

**The Hub card correction cannot be written from this repository.** This is a
Fable-5 dataset. It is not one of the 44 repositories
`scripts/publish_grok46_hub.py` manages, no Fable-5 publisher exists here, and
this repository holds no Hub write credentials. `config/card-schemas/` does not
reach it either — an entry there would be orphaned.

To resolve the issue, publish
[`ouroboros-swarm-payload-kind.card.md`](ouroboros-swarm-payload-kind.card.md)
verbatim as `README.md` on
`https://huggingface.co/datasets/rmems/multi-agent-ouroboros-swarm`. It is the
current live card with the payload-kind claims corrected; nothing else about
the release changes, and no `data/` file is touched.

Until that write happens, `python3 pipelines/verify_hf_release.py --repo
rmems/multi-agent-ouroboros-swarm` fails closed with the payload-kind errors,
which is the intended signal.

## Re-deriving this

```bash
python3 -m unittest tests.test_ouroboros_swarm_payload_kind -v
```

Where `outputs/raw/2026-08-17/multi-agent-ouroboros-swarm` is present, that
recomputes every number above from the raw bytes and requires an exact match
against the committed JSON. Where it is absent, the raw-corpus class is skipped
and the committed contract is still checked.
