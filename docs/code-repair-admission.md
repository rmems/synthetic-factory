# Procedural code-repair admission

The default `config/FACTORY-REGISTRY.json` revision v0.3 adds one procedural
route: `python-function-repair-factory`, carrying the
`python-function-repair` family and the dedicated `code_repair` record kind.
Existing hosted rows retain their provider, channel, and research-only/blocked
policy. The v0.1 and v0.2 decoders reject procedural fields and kinds.

The procedural row has no hosted provider or channel. Runtime implementation
ownership (`project_owned`), generation method (`deterministic_execution`),
and source-license evidence are separate fields. AI-assisted implementation
does not make runtime generation model-generated. The approved mutator version
is 2.0.0, including repeat execution evidence and catalog-bound record IDs.

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
natural exclusions and corrupt records. For this family its verdict remains
`training_ready: false` with an explicit fresh-gate blocker. Pure inspection is
necessary but cannot certify fresh execution, completion, publication, or training.
The dedicated publication workflow must freshly replay the evidence and verify
actual round completion, membership, and hashes. There is no extra human-review
sample gate, and the approved registry has `publication_target: null`.
