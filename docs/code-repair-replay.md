# Code-repair replay boundaries

`code_repair.replay.replay_record(record, catalog, executor)` freshly executes
an eligible record against a trusted loaded catalog. It binds source and hidden
oracle identity, lineage and split, the complete recorded mutation site and
inverse repair, the harness, fresh execution fingerprint, public examples and
bounded failure evidence. The returned entry identifies the executed source,
broken and repaired program digests, record digest, harness digest and fresh
execution evidence digest. A persisted report or its self-hash does not
authenticate a run; consumers must invoke fresh execution at their trust boundary.

`catalog_check.catalog_structure_findings(catalog)` is the pure companion gate.
It derives structural digests, connected groups and group bucket assignments
from the complete catalog and compares all declared pins. Positive-weight splits
must be populated, including for an empty catalog. Admission and export callers
must check these findings before consuming a catalog's lineage values.

Run replay additionally requires `RUN.json` to pin `candidates_sha256` as the
SHA-256 hex digest of the exact `candidates.jsonl` bytes, and `records` as an
integer matching the complete candidate set. Removing or modifying candidate
lines is refused. Old pilot runs missing this pin must be regenerated; replay
does not silently invent a generation-time pin from the files it receives.
Only `code-repair-run/2` with the current generator version is accepted. Positive
record IDs must bind the complete catalog digest, run seed, and draw index.
Replay uses shared record-shape and verdict validation, executes `original_repeat`
before the mutant, and compares all five complete phase blocks, including the
bounded observation text, full observation hashes, source digests and limits flags.

The builder rejects unordered literal arguments (including sets nested in
containers), relative or unreviewed imports, ambiguous duplicate definitions,
and direct or dynamic host access in executable doctests. It retains future
imports to preserve compilation semantics. Observation runs the public prelude,
then loads a fresh module for the hidden suite, matching generation's isolation,
uses batches no larger than the hidden-case cap, compares repeated observations,
and excludes truncated or unstable representations. A final observation verifies
that discarding failed probes did not change the state used by retained inputs.
These selection checks bound the pinned-source pilot. Execution of any catalog
that is not that reviewed pin requires the `bwrap-ro-netns-v1` OS boundary
recorded in the oracle fingerprint; replay refuses a different sandbox identity.

## What a Hub card may claim about replay

`REPLAY.json`'s top-level `status` is computed over the replayed positives
only. Rejected and provisional records are listed as `not_replayed`, so
`status: passed` next to `not_replayed > 0` is a partial replay, not a passed
full batch (#420). A code-repair Hub card's verification and contents sentences
are therefore rendered from the evidence by `pipelines/code_repair/card_claims.py`
(`verification_statement`, `split_statement`, `contents_statement`), and
`pipelines/verify_hf_release.py --repo <id>` checks a published code-repair card
(`REPLAY_CLAIM_REPOS`) against its `evidence/REPLAY.json` and
`evidence/RUN.json`, after reconciling the summary counts with the per-record list.
The card must state `<passed> of <records>`, the failed and not-replayed counts
with the not-replayed outcomes, the replay `status`, the outcome and oracle-status
splits, and the requested-draw and draw-skip counts. Each draw-skip count must
be followed, before the next draw count and before the clause ends, by its own
reason (the skip code, or a plain name such as "duplicate mutant"). The
`MUTATION_NO_SITES` count must share a clause with
"excluded from the draw pool", because those programs use no draws and don't
account for a shortfall between requested and produced candidates.

The default `verify_hf_release.py` run (`DEFAULT_REPOS`) must pass against what
is published today, so a code-repair release joins it only once its published
card passes. `rmems/python-function-repair-20261006` is checked on request
until its card-only Hub fix for #420 merges.
