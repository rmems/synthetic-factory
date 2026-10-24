# Procedural code-repair admission

The default `config/FACTORY-REGISTRY.json` (`factory-registry-v0.4`; procedural
rows were introduced in v0.3) carries the code-repair procedural route
`python-function-repair-factory`, carrying the
`python-function-repair` family and the dedicated `code_repair` record kind.
Existing hosted rows retain their provider, channel, and research-only/blocked
policy. The v0.1 and v0.2 decoders reject procedural fields and kinds.

The procedural row has no hosted provider or channel. Runtime implementation
ownership (`project_owned`), generation method (`deterministic_execution`),
and source-license evidence are separate fields. AI-assisted implementation
does not make runtime generation model-generated. The approved mutator version
is 2.1.0, including repeat execution evidence and catalog-bound record IDs.

## Source authority

`schemas/procedural-source-policy-v1.json` is independently pinned by
`POLICY_SHA256` in `pipelines/code_repair/source_policy.py`. The exact policy
bytes are validated at import, then recursively frozen for the process. An
alternate policy path is accepted only if it contains those exact bytes.
A self-consistent changed registry, policy, source, or license cannot grant
permission. Identity manifests pin the exact registry and procedural policy
digests.

Only the reviewed, locally vendored `catalogs/python-repair-v1` is authorized:
TheAlgorithms/Python commit
`2067ce6dfb3b0426a88c7a40531e355a5c703cff`, MIT license with SHA-256
`4395a1dc4bda1d6054c45b4d1230c709c7398e6d66f1d0aff4b22d95973bea56`.
Catalog metadata and programs bytes are independently pinned. Source identities
must match the trusted catalog, and the shared pure catalog validator recomputes
its structure, group, and split bindings.

The RUN2 catalog contains 197 programs. Its exact `CATALOG.json` SHA-256 is
`2402fe1d85a9a4a978ef4cc5e4491859cdf302b9c4b33415a66a4c00a5311f98`, and
`programs.jsonl` SHA-256 is
`fbd012638c92cbad072553405c545e5f8dc26bc677100a11e693d61b7bf9d904`.
The source policy digest is
`b8d1621798eb13eed8e5d73de365dc1028b08cef9645d08aff9d909630b23b1b`.
These pins supersede the catalog used for the historical `pilot-r3` report;
that report and its original output bytes are historical evidence.

Catalog rebuilds require a reviewed update to the JSON policy's catalog pins,
the single independent `POLICY_SHA256` trust anchor, and the corresponding
registry row's copied pins and policy digest. These are authority changes,
not runtime autodiscovery. Processes must restart to use the new policy.

## Pure inspection API

`pipelines/code_repair/admission.py` exposes:

```python
load_trusted_catalog(row=None) -> Catalog
validate_source_route(record, row, *, catalog=None) -> list[str]
natural_eligibility(record, row, *, catalog=None) -> tuple[bool, tuple[str, ...]]
```

Callers resolve `row` from the actual source directory using the loaded registry;
payload metadata cannot choose its own authority. `validate_source_route` checks
the row, generator, and source binding. `natural_eligibility` additionally calls
the shared family validator and raises `SourcePolicyError` for corrupt evidence.
Only accepted records with a validated oracle status are eligible. Valid natural
rejections or provisional evidence return false with their reasons.

These calls, the census, shape/deep checks, identity curation, and training audit
never execute candidate code. A malformed family claimant remains `code_repair`
and fails the family validator instead of escaping into an episode route.

The cached source metadata is recursively immutable; admission returns isolated
dict/list copies. Generator admission requires exactly the emitted `name`,
`version`, `kind`, `authority`, and `seed` fields, rejecting additional model or
provider claims. Operational `validate_run` and `check_records` checks bind
source evidence to the sealed catalog. The lower-level
`validation.validate_record(catalog=None)` remains a generic evidence check;
without an explicit catalog it does not establish source authority.

## Identity and publication boundaries

Identity curation preserves the original ID, complete payload and oracle digest;
it adds no synthetic state and no provenance inside the hashed record. Its
sidecar records the preserved identity and policy eligibility. Supplied UTF-8
source JSONL payload bytes are retained exactly. Physical CRLF terminators become
LF; the record payload excludes LF and its immediately preceding CR. Whitespace
within the payload is preserved. Without original bytes, canonical JSON supplies
the source snapshot. Revalidation replays the transform and compares the emitted
payload bytes against that snapshot.

The training audit counts valid accepted candidates separately from evidence-only
natural exclusions and corrupt records. Unpublished candidates retain
`training_ready: false` with an explicit fresh-gate blocker. An actual completed
round clears that blocker only when its marker, all bound artifacts, current
independent authority, full original run and exact selected batch bytes pass pure
revalidation. Read-only census, frontier and audit commands do not execute code.
There is no extra human-review sample gate, and the approved registry has
`publication_target: null`.

## Local transactional publication and admitted export

Create the registered factory directory, then use a new local round and a new
export destination:

```bash
mkdir -p /path/to/outputs/raw/2099-01-01/python-function-repair-factory

python3 pipelines/code_repair_cli.py publish \
  --run /path/to/generated-run \
  --factory-dir /path/to/outputs/raw/2099-01-01/python-function-repair-factory \
  --round 1 --lineage-cap 6 --json

python3 pipelines/code_repair_cli.py export \
  --run /path/to/generated-run --catalog catalogs/python-repair-v1 \
  --out /path/to/new-admitted-export --lineage-cap 6 \
  --admit --round-marker \
  /path/to/outputs/raw/2099-01-01/python-function-repair-factory/ROUND-r01.complete.json \
  --json
```

Publication captures the original `RUN.json` and `candidates.jsonl`, validates
every candidate, and selects accepted validated records in sorted ID order with
exact/structural deduplication and the per-lineage cap. It reserves the actual
nonempty selected count. The staged batch retains each original JSONL row's
bytes. `code-repair-input-rNN.json` preserves the complete original run and all
candidate bytes as UTF-8 strings, so rejected, abstained and provisional evidence
remains immutable without entering the training JSONL census. Useful `NOTES`
describe the selection and evidence. Existing transaction capture, hashing and
exclusive completion-link rules protect all three artifacts.

The mandatory transaction gate freshly replays every positive, including those
removed by deduplication or the cap, against the independently pinned catalog.
Direct `round_txn.py publish`, wrong factory paths, mixed-family batches and
execution waivers cannot bypass the gate. Corrupt evidence anywhere refuses the
run; valid natural exclusions do not. Failed transactions retain normal recovery
state and can be inspected or aborted with the existing transaction CLI.

An admitted export requires the same exact original run bytes, candidate bytes,
lineage cap and deterministic selected membership as the actual completed
round. It captures and verifies the marker and every artifact, then independently
replays the captured input again. Stored replay-report claims cannot authorize
it. The export manifest records the actual marker path and byte digest, current
authority pins, selected membership, fresh replay evidence and concrete passed
gates. It reports `training_export: training_candidate` and
`project_training_policy: allowed`, preserves the full evidence file, includes
the pinned upstream MIT notice, and freezes held-out SFT bytes by digest. Agoge
rows preserve IDs, groups, lineages and exact completion boundary offsets.

Ordinary export without `--admit` remains blocked candidate mode. A local
admitted export is distinct from an Agoge frozen split and a model-training
launch; these commands do not launch training or upload to a Hub. The reviewed
TheAlgorithms/Python pin may still run under rlimits alone. Any other catalog
source must execute inside `bwrap-ro-netns-v1` (issue #201) before it is
admitted; this is not a cryptographically signed transaction ledger.

## Consumer renderings and the Hub bundle

An export writes one verified pair in three renderings, each leak-checked
against its record before it is written and each frozen for the held-out split
by digest in `held_out/FREEZE.json`: `sft/<split>.jsonl` carries the prompt and
the complete corrected module (byte-equal to the text the harness executed);
`chat/<split>.jsonl` carries the same pair as a `messages` list with one user
and one assistant turn for chat-template trainers; `edit/<split>.jsonl` carries
the same prompt, with the instruction line asking for an edit, and one
SEARCH/REPLACE block as the completion. The block is the smallest window of
whole lines around the changed span that occurs exactly once in the broken
module, paired with the same window from the verified repair, and it is a valid
completion only when applying it to the broken module reproduces the repaired
module's `repaired_sha256`; every mutation is one span, so the whole-module
completion spends most of its tokens copying the prompt and the edit rendering
puts the loss on the repair itself. `MANIFEST.json` describes the renderings
under `views`. The record is the source of truth; a rendering is a projection
and never carries anything a record does not.

`python3 pipelines/code_repair_cli.py hub-bundle --export <export-dir> --out
<bundle-dir> --dataset-id <owner>/<name>` turns a complete export into a
directory the Hub can serve without custom loading code: `data/sft`,
`data/chat` and `data/edit` as typed configs whose `train`, `validation` and
`held_out` splits come from the records' lineage splits, the lossless `viewer`
projection over `evidence/candidates.jsonl` written by the same stdlib Parquet
writer the published datasets use, the export manifest, the held-out freeze,
the attribution notices of an admitted export, and a card, `provenance.json`
and `release-status.json` whose `training_ready` statement is derived from the
manifest's admission block (admitted, no blockers, replay passed) rather than
typed by hand. Every export file is re-digested against the manifest and the
viewer projection is read back before anything is written; a mismatch refuses
the bundle, which only ever targets a brand-new destination outside
`outputs/raw/`. The command creates no Hub repository and uploads nothing;
publication remains a separate, owner-gated step.

Generator 2.1.0 (`code_repair.planning.ProposalPlan`) draws train-split programs
only. A run stamped 2.0.0 validates and replays the earlier draw, which still
includes `validation` and `held_out` programs. Admission compares the record
with the sealed row, so a 2.0.0 record is `PROCEDURAL_GENERATOR_MISMATCH` and
is not a training candidate. Those programs stay in the catalog, and
the task gate still denies those ids, but a generated run's consumer files for
those splits are empty. The Hub bundle omits the empty splits. Every export records
the evaluation limitation `TRAIN_ONLY_DRAW_OMITS_EVAL_SPLITS`, and the bundle
summary carries a warning when train rows exist and held-out rows do not.
Programs whose catalog `split` is null (no split policy) stay eligible; only
the explicit `validation` and `held_out` splits are left out of the draw.
