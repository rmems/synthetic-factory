# CSV mill catalog replay

`python3 -m pipelines.csv_mill.cli catalog-check --json` checks the recovered
CSV catalog. Its source is
`experiments/mill_leftover_leftover_leftover_csv_r114.py` at commit
`813f93f1969c1c4421e5663492e9663739efa642` on `legacy-mill-lane`. Extraction
reads the AST without executing the archived program. The loader requires
that provenance declaration and authenticates the plants bytes before parsing
them. The small test fixture is a reduced, renumbered slice from this source.

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
Keep the containing directory stable during publication; the generator does not
roll back by deleting paths that another writer may have replaced.

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
