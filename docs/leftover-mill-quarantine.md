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

Acknowledgement requires every column below to match. The SHA-256 is over the
exact physical JSONL line, including its terminating newline; reusing an id,
moving a record, changing its kind, or changing one byte does not inherit the
historical acknowledgement.

| raw file | line | kind | id | exact-line sha256 |
| --- | ---: | --- | --- | --- |
| `batch-r723.jsonl` | 1 | `episode` | `dbc-r723-buildah-layers-vfs-id-leftover` | `f66b76a6d2bf9d6b95ba10a02a11ce69fd445745708c8aa75379066dfef58ea8` |
| `batch-r723.jsonl` | 2 | `episode` | `dbc-r723-buildah-vfs-graphroot-leftover` | `38fa7eb0880c270179487b273cd7e08fd05c47c438a19d396ee12f98c8e6e66d` |
| `batch-r724.jsonl` | 1 | `episode` | `dbc-r724-podman-sqlite-diff-leftover` | `ebc411ccf4093a84edeb6779a32036155311e838477e62bcdc33b897036a79be` |
| `batch-r724.jsonl` | 2 | `episode` | `dbc-r724-podman-boltdb-compat-leftover` | `eca3b3c110a21f2d995dd9ff5f1fc0e6e2500e95857f86a32c3889e34dfa35dd` |
| `batch-r725.jsonl` | 1 | `episode` | `dbc-r725-nerdctl-namespace-snapshot-leftover` | `1ca3983e511d56eae8f23ee235ab3e7304b118b74ca5bbc9afac3d6394fb17cc` |
| `batch-r725.jsonl` | 2 | `episode` | `dbc-r725-nerdctl-cni-cache-leftover` | `46b259d13994b8bd3122ef29f563d8c830600eca9d3b6fe5d075052ce8de6e8b` |
| `batch-r726.jsonl` | 1 | `episode` | `dbc-r726-containerd-content-lease-leftover` | `f4606247c917480c7d34efb8b852759f0aeb7556a71287cd9abc875668be77ce` |
| `batch-r726.jsonl` | 2 | `episode` | `dbc-r726-containerd-gc-label-leftover` | `4dfb0c4591cce8971d0697eeaa5a045505e39adfc23596af7d40bc8c8dec4a23` |
| `batch-r727.jsonl` | 1 | `episode` | `dbc-r727-crio-imagestore-pin-leftover` | `062876ad679109cda5dda7fdaa4f6177de30e932abc5b3d8fe3974bda1a67f39` |
| `batch-r727.jsonl` | 2 | `episode` | `dbc-r727-crio-overlay-mounts-leftover` | `7acb3ed0f3710d574c49feb4d6bb35e1baa7b9218cc4c1e1b53e2ef5049063e2` |
| `batch-r728.jsonl` | 1 | `episode` | `dbc-r728-buildx-builder-driver-opt-leftover` | `9ac3346ea6f4595f776cb6a1d9102aa4c305942653217dc80b41376b16931eef` |
| `batch-r728.jsonl` | 2 | `episode` | `dbc-r728-buildx-provenance-mode-leftover` | `7df9a381bae5b4cedb0c722e2190575d184231ac6e0cd756951ea1420fe3c2b1` |

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
