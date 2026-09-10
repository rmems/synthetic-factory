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

The builder rejects unordered literal arguments (including sets nested in
containers), relative or unreviewed imports, ambiguous duplicate definitions,
and direct or dynamic host access in executable doctests. It retains future
imports to preserve compilation semantics. Observation runs the public prelude,
uses batches no larger than the hidden-case cap, compares repeated observations,
and excludes truncated or unstable representations. A final observation verifies
that discarding failed probes did not change the state used by retained inputs.
These selection checks bound the pinned-source pilot; they are not an operating
system sandbox for arbitrary Python input.
