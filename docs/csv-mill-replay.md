# CSV mill catalog replay

`python3 -m pipelines.csv_mill.cli catalog-check --json` checks the recovered
CSV catalog. Exit status is 0 for success, 1 for catalog findings, and 2 for
a coded refusal or usage error. Its source is
`experiments/mill_leftover_leftover_leftover_csv_r114.py` at commit
`813f93f1969c1c4421e5663492e9663739efa642` on `legacy-mill-lane`. Extraction
reads the AST without executing the archived program. The loader requires
that provenance declaration and authenticates the plants bytes before parsing
them. The small test fixture is a reduced, renumbered slice from this source.

Unpinned source must consist of proven literal assignments and inert declarations.
The `dict` constructor must be unshadowed; unknown module-time calls, imports,
mutations, control flow, decorators, and evaluated default expressions refuse.
Ordinary function/lambda bodies and exact script-entry bodies remain deferred.
Every emitted effective round must fit the exact JSON integer domain, and loaded
mill rows must retain contiguous index order.

The exact archived path and full UTF-8 SHA-256
`98faa233ffe331fbd1d563c0aa3e190b48e40f18c5939939eab07d078d0ba570`
permit a separate AST text projection of its literal catalog. That pin was
independently derived from the preserved Git bytes. It does not assert runtime
equivalence or execute the archived setup/publisher; any changed byte loses the
exception. Source text must be a builtin string so parsed text and hashed bytes
cannot disagree through an overridden encoding method.

`generate --all --out <new-directory> --json` emits 16 designed success/handoff
pairs, a run summary, and notes. It stages all three files before publishing
the new directory and refuses an existing destination or `outputs/raw/`.
The hosted factory remains research-only and blocked from training.

Publication checks the pinned parent inode and its resolved location immediately
before the no-replace rename. The successful rename is the commit point; the CLI
reports `published_destination` separately from the requested `destination`.
A directory descriptor does not lock its pathname: another process can move the
containing directory between the final check and rename, or after success. These
checks do not provide an atomic pathname-location guarantee against such moves.
Staged entry names, original file identities, and written bytes are checked before
publication, but another process under the same UID can still alter content
between that check and rename. Keep the containing directory and staged content
stable through staging, publication, and cleanup. The generator does not attempt
post-publication rollback.

Cleanup preserves replaced entries observed by its identity/content checks and
refuses to recursively remove unknown content. Those checks are separate from
`unlink` and `rmdir`: a noncooperating same-UID actor can replace an entry between
the check and deletion, and the replacement may then be removed. The private
0700 stage is not isolation from other processes with the same filesystem access.
No atomic identity-bound deletion or adversarial same-UID safety is claimed;
an advisory lock would only constrain writers that cooperate with it.

## Source rounds and publication

The default rounds 114–129 preserve this archived mill's source identity.
They are replay coordinates, not reservations in a shared publication run.
The separate `config/cei/CATALOG.json` also contains historical CEI slices
whose round ranges overlap. Combining those replay outputs into a raw run
without an allocation plan is invalid; the catalog commands do not perform
that combination or publish completion markers.

Use `--plant <plant-id> --round <reviewed-round>` when preparing a selected
pair for a separately reviewed allocation. A later publication workflow must
reserve its actual destination round and check the run's quota and identities.
This package does not choose new global round numbers from an archive catalog.
Within one loaded CSV catalog, overlapping effective rounds are rejected so
`--all` cannot emit multiple quota-two pairs at the same coordinate.

The recovered plant fields remain intact. One output-template correction
removes a duplicate `-handoff` suffix from failure domains; the generated notes
now report that same domain. These records describe designed traces, not live
tool executions.

Before projection, the original AST is compiled only to validate Python constraints,
including deferred function bodies. Its code object is discarded without execution.
Both source text and its path must be builtin strings before parsing or hashing.

`Catalog.meta` is a recursive snapshot: mappings are read-only copies and JSON
sequences become tuples. Mutating the caller's constructor input cannot alter it.
Generation uses the validated plant/mill values; CLI JSON reports its explicit
summary fields rather than serializing the metadata view. Absent required plant
fields report `PLANT_FIELD_MISSING`; present invalid values report
`PLANT_FIELD_INVALID`, including numeric and Unicode checks.
