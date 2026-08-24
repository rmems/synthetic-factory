# Leftover-mill quarantine — kind mix

> Detector: **kind mix** (payload kind ≠ destination kind)
> Ledger: `pipelines/leftover_mill.py` (`KIND_MIX_QUARANTINE`)
> Issue: [rmems/synthetic-factory#30](https://github.com/rmems/synthetic-factory/issues/30)

## 1. What a leftover mill is

A *leftover mill* record is a record produced by one factory's generation mill
and then written into a destination that publishes a different record kind. It
is a schema-interpretation defect, not a naming one.

The test is **payload-first**. `curate_agentic.classify_record` decides what a
record is:

- The directory slug is not evidence. A record living under
  `code-review-preference-factory/` is not a preference pair because of where
  it sits.
- The `-leftover` id suffix is not evidence either. Thousands of legitimate
  episodes across the Grok 4.6 lane carry `leftover` in their id because
  *leftover state* is the scenario mechanic. `leftover`-in-id is naming, not
  mill mix.

## 2. Scope of this ledger

This ledger covers exactly one detector class:

| class | test | owner |
|---|---|---|
| **kind mix** | payload kind ≠ destination kind | this document / #30 |
| factory mix | `meta.factory` ≠ destination factory | #39, #43 |
| dest-stamped family mix | dest-stamped payload, foreign id-prefix / goal family | #38, #44 |

Factory mix and family mix are different detectors with different false-positive
profiles. They are deliberately not implemented in `pipelines/leftover_mill.py`.

## 3. Quarantined records

`code-review-preference-factory` → `rmems/code-review-preference-pairs`.
Destination kind is `preference`; these 12 records classify as `episode`. Each
carries episode keys (`id`, `goal`, `plan`, `steps`, `outcome`, `reward`,
`meta`), `meta.factory` = `code-review-preference-factory`, generator
`grok-4.6`, and 17–18 steps. None has `chosen`/`rejected`.

| raw file | line | id |
| --- | ---: | --- |
| `batch-r723.jsonl` | 1 | `dbc-r723-buildah-layers-vfs-id-leftover` |
| `batch-r723.jsonl` | 2 | `dbc-r723-buildah-vfs-graphroot-leftover` |
| `batch-r724.jsonl` | 1 | `dbc-r724-podman-sqlite-diff-leftover` |
| `batch-r724.jsonl` | 2 | `dbc-r724-podman-boltdb-compat-leftover` |
| `batch-r725.jsonl` | 1 | `dbc-r725-nerdctl-namespace-snapshot-leftover` |
| `batch-r725.jsonl` | 2 | `dbc-r725-nerdctl-cni-cache-leftover` |
| `batch-r726.jsonl` | 1 | `dbc-r726-containerd-content-lease-leftover` |
| `batch-r726.jsonl` | 2 | `dbc-r726-containerd-gc-label-leftover` |
| `batch-r727.jsonl` | 1 | `dbc-r727-crio-imagestore-pin-leftover` |
| `batch-r727.jsonl` | 2 | `dbc-r727-crio-overlay-mounts-leftover` |
| `batch-r728.jsonl` | 1 | `dbc-r728-buildx-builder-driver-opt-leftover` |
| `batch-r728.jsonl` | 2 | `dbc-r728-buildx-provenance-mode-leftover` |

`tool-use-preference-factory`, the other preference destination, has no
kind-mix records.

## 4. What the quarantine does and does not do

**Raw JSONL is never rewritten.** These records stay byte-for-byte in
`outputs/raw/2026-08-19-agentic/code-review-preference-factory/` and in the
published `data/raw/` snapshot. Editing a payload to fake a preference schema
would destroy the evidence that the defect existed.

Instead, three consumers key off the ledger:

1. **`pipelines/curate_preferences.py`** quarantines them. Each gets a manifest
   row with `action: "quarantined"`, `classification: "leftover_mill_episode"`,
   and reason code `LEFTOVER_MILL_KIND_MIX`. They are counted under
   `leftover_mill_records`, never under `preference_records`, `retained_pairs`,
   or any preference-yield denominator.
2. **`scripts/publish_grok46_hub.py`** discloses them. A preference destination
   whose snapshot contains ledger records renders a *Leftover-mill quarantine*
   section on the dataset card that names every record and states the corrected
   preference-pair count.
3. **`scripts/publish_grok46_hub.py`** also gates them. A snapshot of a
   preference destination fails outright when it would publish a kind-mix
   record that the ledger does not already name, or a payload line that cannot
   be decoded and therefore cannot be proven clean.

## 5. Adding to the ledger

Do not. The ledger acknowledges history; it is not a waiver mechanism. A new
kind-mix record means a generation mill wrote into the wrong destination, and
the fix belongs upstream in `pipelines/round_txn.py`, which already rejects a
staged batch whose kinds disagree with `AGENTIC_FACTORY_KINDS`. An entry is
only appropriate for records that were already published before that check
existed, and only after a payload-first census confirms the population.
