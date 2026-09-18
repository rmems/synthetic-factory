# Additional SIR leftover catalogs

This package preserves two leftover-mill catalogs from `origin/legacy-mill-lane`:
`sir-mill-leftover3-r72` and `sir_r108_leftover3d_mill`, with 16 pair rows each.
Its source inventory, `CATALOG.json`, and `pairs.jsonl` contain only those mills.

The existing `search` package owns the home mills `sir-mill-r31`, `sir-mill-r52`,
and `sir-mill-r72`. Use `search.catalog.R31`, `R52`, and `R72` for their 56 pair
rows and `search.sources` for their source identities. They retain the
`home-pairs` kind. The leftover r72 catalog records a sibling reference to r31
using the canonical `search.sources.R31_SOURCE.path`; it does not duplicate
the home catalog or load the legacy publisher.

Extraction evaluates AST literals without importing or executing legacy code.
Explicit unresolved assignments are rejected, while omitted optional metadata
can use documented defaults. Catalog loading binds source references, embedded
mill identities, counts, and pair value types to the committed contract. The
source reproduction test compares the full extracted header and JSONL bytes
against the preserve commit when those Git objects are available locally.

Hop destinations are catalog metadata. This package does not generate or
publish records, and the leftover mills and loop publishers remain off-branch.
