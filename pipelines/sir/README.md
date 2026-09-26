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

Unpinned source accepts literal assignments and inert function/lambda bodies.
Definition-time defaults and annotations must be proven inert. The exact
`if __name__ == "__main__"` body is deferred, while its import-time `else` branch
is checked. Unknown module-time calls, imports, class creation, control flow,
and mutation are refused even when they do not mention catalog variables.
Explicit unresolved assignments are rejected; omitted optional metadata can
use documented defaults.

The two preserved full sources have a separate AST text projection authorized
only by exact path and full UTF-8 SHA-256 from `sources.py`, independently pinned
to the preserve commit. Caller-supplied blob labels do not grant this exception.
Those scripts contain module-time loader/path setup; their projected literals
are not evidence of runtime equivalence. No legacy source is imported or
executed. Any changed byte, including an appended call or comment, loses the
archive exception and must satisfy the strict literal-input contract.

Catalog loading binds source references, embedded mill identities, counts,
and pair types to the committed contract. The source reproduction test compares
the complete extracted header and JSONL bytes against the preserve commit when
those Git objects are available locally. Standalone literal and refusal tests
also run without archival Git objects.

Hop destinations are catalog metadata. This package does not generate or
publish records, and the leftover mills and loop publishers remain off-branch.
