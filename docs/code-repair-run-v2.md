# Code-repair generation version 2

Generator `2.0.0` writes new `code-repair-run/2` artifacts. Existing run directories
and historical candidate bytes must remain unchanged. Regenerate from the pinned
catalog into a new destination to obtain the evidence required by this version;
do not add fields to old candidate records or rewrite their RUN files.

Canonical IDs now have the form `pfr-<catalog-sha256>-<seed>-<draw-index>`.
The catalog component is the complete lowercase SHA-256 of the canonical JSON
array `[catalog_id, programs_sha256]`. The final draw index remains five decimal
digits. Identical catalogs, seeds, and draws retain identical IDs; distinct
catalog revisions cannot collide merely because the seed and draw index match.

`RUN.json` keeps the top-level integer `records` count and adds
`candidates_sha256`, the bare lowercase SHA-256 of the exact written
`candidates.jsonl` bytes. The returned generation summary equals the written
RUN object. Volatile execution logs remain separate.

The run also carries `split_policy`, serialized from the catalog policy (or null
when absent). Consumers compare this policy with their trusted catalog before
using the recorded split assignments. `skips.MUTATION_NO_SITES` counts catalog
programs with no eligible mutation sites; it does not count attempted draws.
Draw conservation is `count = records + sum(skips except MUTATION_NO_SITES)`.

Every stored phase includes the executed `module_sha256` and `limits_applied`,
alongside `status`, `load_ok`, public and hidden rows, and the row digest `sha256`.
Rows preserve their bounded `got` text and `truncated` flag as well as the full
observation `got_sha256`. The digest of the complete phase map binds these fields.
The new `original_repeat` phase executes the same original source in a fresh
process before mutants run. Differing stable observations reject with
`SOURCE_NONDETERMINISTIC`; a restored repair must also reproduce those observations.
Reference checks certify hidden wants independently. Resource limits must be
reported as applied before generation continues.

Stored evidence is locally checked by re-deriving the decision and public
projection. This is an integrity check, not authentication of a consistently
forged artifact. Trusted admission/export boundaries must still execute replay
against their pinned catalog and exact run hash.

Agoge rows retain the existing identity fields and exact prompt/separator/completion
text. `completion_start_char` is the Python character count of the prompt plus
separator computed during construction. It is a Unicode code-point offset, not
a UTF-8 byte offset or a token index. Consumers must use the offset directly;
separator text may also occur inside source programs or docstrings.

The fake-executor golden record was explicitly re-pinned for this version's
catalog-bound identity, complete phase observations, and repeat-source evidence.
No historical generated output was modified.
