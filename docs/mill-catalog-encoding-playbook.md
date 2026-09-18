# Mill catalog encoding playbook

Encode the catalog **before** opening the mill PR. The 2026-09-15 burst
kept blowing the merge cap, then babysitters slimmed RLB, ACM, and EVH
after the fact. This document is the encoding those merged PRs already
paid for.

Docs-only. It does **not** onboard a mill family, change
`REVIEWED_MILL_PREFIX_HOMES`, vendor leftover mills, or authorize a
`round_txn` publisher. Do not mill from this playbook.

Line counts below are GitHub **additions** on `origin/main...HEAD` (the
merge cap), re-checked 2026-09-15 against `gh pr view` and the files on
current `main`.

## 1. The cap

| gate | limit | what GitHub counts |
|---|---|---|
| added lines | **≤ 2,500** | newline-separated additions on `origin/main...HEAD` |
| changed files | **≤ 20** | paths in that same compare |

```bash
git fetch origin main
git diff --stat origin/main...HEAD
# last line: N files changed, M insertions(+)
# require N <= 20 and M <= 2500; keep ~200 lines of slack
```

`git diff --shortstat origin/main...HEAD` is the number GitHub reports
as `additions` on a single-commit mill PR. Multi-commit PRs still report
the **net** compare, not the sum of every commit. Slim on the **same
head** with a forward commit. Do not open a second PR. Do not rebase.

A pretty-printed JSON object costs one GitHub line per key, indent, and
array element. A compact JSONL record costs **one line per plant or
pair**, no matter how wide the object is. That is the whole encoding
fight.

The cap is merge hygiene, not data quality. Dropping cases to fit,
minifying a catalog onto one line, or vendoring the mill so the catalog
can be smaller are all failures.

## 2. Winning encoding

Two encodings are allowed on a new mill PR. Pretty JSON of full pair
bodies is not.

| rank | encoding | GitHub cost | when |
|---|---|---|---|
| **1 — default** | **Pretty header + compact JSONL** (one object per line) | header ≈ 20–80; payloads = N records | N extracted rows fit after the package |
| **2 — overflow** | Pretty header with **per-mill counts** + **one first-slice** of compact identities | header + one identity line per committed pair | full JSONL of the extract still blows 2,500 |
| last resort | Representative **real** rows + `extract.full_*` pins | slice rows + source pins | even compact identities of the extract cannot fit |

House pattern for rank 1: `catalogs/python-repair-v1/` (`CATALOG.json`
pretty header + `programs.jsonl` one object per line).

### 2.1 Compact means one object per line

```text
{"slug":"...","ok":{...},"bad":{...}}
{"slug":"...","ok":{...},"bad":{...}}
```

No leading whitespace on a record line. Trailing newline. No CR. Wide
lines are fine; GitHub charges 1. Reviewers `jq` a line. `sha256` is
over the file bytes including the final newline.

Compact is **not** `json.dumps(entire_catalog, separators=(",", ":"))`
written as a single line so GitHub reports `+1`. That is minify-JSON
gaming. Unreviewable. Forbidden.

Compact is also **not** pretty-printed pair objects inside
`CATALOG.json`. Rank 1 puts bodies in JSONL. Rank 2 puts **identities**
(slugs, plants, domains — not leftover/first/fix metric bodies) on one
line each, either in the JSONL first-slice or as a compact `pairs`
array inside an otherwise pretty header.

## 3. Decision tree

Run this **before** creating files. Fill the brackets from an
`ast.parse` extract (`exec: false`) of `origin/legacy-mill-lane`.

```text
1. Extract every pair/plant. Record n_rows_extracted, n_source_files,
   preserve commit, per-mill n_rows / first_slug / last_slug / sha256.

2. Estimate additions:
     package + tests   ≈ 1200–2200
     header            ≈ 30–80
     jsonl             = n_rows_extracted          # rank 1
     first-slice       = n_first_slice             # rank 2, typically 16–126
     mill counts       ≈ 15 * n_other_mills        # rank 2
     pretty pair bodies ≈ 60 * n_rows_extracted    # do not use

3. If header + jsonl + package + tests <= 2300:
     RANK 1. Commit every extracted row as compact JSONL. Defer nothing
     from that mill. RLB #252 (64/64). CEI #270 (39/39 of r81).

4. Else if header + counts + one first-slice + package + tests <= 2300:
     RANK 2. Commit per-mill n_rows, first_slug, last_slug, sha256,
     blob_sha, shape, plus compact identities for ONE first mill (or
     first/last per mill when that is the slice). Defer full pair
     bodies. Name the deferred set in the PR body. AMC #274 and
     EVH #278.

5. Else:
     LAST RESORT. Representative slice of real extracted rows (not
     invented) plus extract.full_row_count and extract.full_source_files.
     ACM #255: 8 of 1052.

6. Never: pretty-print full pair bodies. Never: minify the catalog to
   one line. Never: vendor *mill*.py / *loop*.py / _gen_*plants*.
   Never: commit both a pretty catalog and a JSONL of the same bodies.
   Never: open a second PR to slim this family.
```

Keep 200 lines of slack. WSR #272 had 3 (2497 / 2500). That is why
babysitters exist.

## 4. Merged exemplars

These five already landed. Copy the **encoding**, not the family.

| family | PR | additions / files | catalog on `main` | encoding | extracted | committed |
|---|---|---|---|---|---|---|
| **rlb** | [#252](https://github.com/rmems/synthetic-factory/pull/252) | **668 / 5** | `config/rlb/CATALOG.json` 47 + `pairs.jsonl` 64 | rank 1 | 64 pairs / 128 cases from 4 sources | **64 / 64** |
| **cei** | [#270](https://github.com/rmems/synthetic-factory/pull/270) | **2193 / 10** | `config/cei/CATALOG.json` 26 + `plants.jsonl` 39 | rank 1 | 39 `_ok`/`_bad` plants from `cei-mill-r81` | **39 / 39** of r81 |
| **amc** | [#274](https://github.com/rmems/synthetic-factory/pull/274) | **890 / 5** | `config/amc/CATALOG.json` 231 + `pairs.jsonl` 24 | rank 2: counts + first-slice | 1401 pairs / 12 catalogs | **24** first/last identities |
| **evh** | [#278](https://github.com/rmems/synthetic-factory/pull/278) | **2177 / 9** | `pipelines/evh/CATALOG.json` 501 | rank 2: r801 identities + counts | 1842 pairs / 16 dests | 126 compact identities (r801) + counts |
| **acm** | [#255](https://github.com/rmems/synthetic-factory/pull/255) | **1341 / 9** | `pipelines/acm/CATALOG.json` 219 | last resort: 8-row slice | 1052 pairs / 95 source files | **8** real rows + 6 source pins |

Factory homes (already in `REVIEWED_MILL_PREFIX_HOMES`; do not edit that
table from a mill PR):

| prefix | factory |
|---|---|
| rlb | `rate-limit-backoff-factory` |
| cei | `csv-excel-ingest-factory` |
| amc | `agent-memory-compaction-factory` |
| evh | `eval-harness-trajectory-factory` |
| acm | `api-contract-migration-factory` |

### 4.1 Slims that babysitters should not have to write

Slim on the same head. Forward commit. No rebase. No second PR.

| PR | before | after | commit |
|---|---|---|---|
| #252 RLB | `config/rlb-case-catalog-v1.json` **+2231** pretty pairs | header +47, `pairs.jsonl` +64 | `aeea952` "Compact the RLB catalog into header JSON plus JSONL pairs" |
| #255 ACM | `rows.jsonl` +1052, pretty `CATALOG.json` +919, 9-module `contract_drift/` | 8-row `pipelines/acm/CATALOG.json` +219, five-module package | `c90b2da` "Slim ACM onto pipelines/acm with a representative catalog slice" |
| #278 EVH | `CATALOG.json` **2265** pretty pairs with leftover/first/fix metric bodies | `CATALOG.json` **501** (`+126 / -1890`) | `75ecf45` "Slim EVH r801 identities under the merge cap" |

CEI #270 and AMC #274 encoded before opening. That is the point of this
playbook.

ACM also dropped the vendored loop fixture
`tests/fixtures/contract-drift/tiny-source/acm-loop-r1.py` in `7dccd5c`
**before** the slice slim. Cut vendoring and encoding yourself.

## 5. Header + first-slice shape

Put the header at `config/<family>/CATALOG.json` (preferred) or
`pipelines/<family>/CATALOG.json` if the package is catalog-only.
Pretty-print the header. Filename: `CATALOG.json`, not `catalog.json`.

Rank 1: header lists mills and hashes; `pairs.jsonl` / `plants.jsonl`
holds every extracted row of the named mills. See
`config/rlb/CATALOG.json` + `config/rlb/pairs.jsonl` and
`config/cei/CATALOG.json` + `config/cei/plants.jsonl`.

Rank 2: header keeps extract totals even when bodies are omitted. AMC
#274 is the overflow valve:

```json
{
  "n_pair_rows_extracted": 1401,
  "n_pair_rows_committed": 24,
  "extraction": "AST literals only; remaining compact pair rows are deferred; no second PR this family."
}
```

Each mill row in that header already carries `n_rows_extracted`,
`first_slug`, `last_slug`, `source_blob_sha1`, and `source_sha256`.
The 24-line `config/amc/pairs.jsonl` is the first-slice: first and last
identity per mill, one object per line — not 1401 pretty pair bodies.

EVH #278 is the same rank with the first-slice **inside** the header:
r801's 126 pair identities are one compact object per line (`fail_slug`,
`success_slug`, plants, domains, `kind`). Metric constructor strings
(`leftover_ok`, `first_ok`, `fix_ok`, …) stay on
`origin/legacy-mill-lane`. Other dests keep counts only.

Last resort (ACM #255) pins the full extract and commits real rows:

```json
{
  "extract": {
    "exec": false,
    "method": "ast.parse",
    "slice": "representative",
    "full_row_count": 1052,
    "full_source_files": 95,
    "source_commit": "6d5ed0c1cac87618a05fab37f2e59bebca0a6031",
    "source_ref": "legacy-mill-lane"
  },
  "row_count": 8
}
```

`slice` values already used: `full` (RLB/CEI — every extracted row of
the named mills), `representative` (ACM), `r801` (EVH). Do not invent
`partial` / `slim` / `min`.

Do not also commit a pretty `rows` array of the same objects. ACM's
first head committed **both** a 919-line pretty source catalog **and**
a 1052-line JSONL; the babysitter deleted both. Header **or** JSONL for
the row set, never both encodings of the same bodies. The header may
list mills and hashes. The JSONL holds rows (or rank-2 identities).

## 6. Forbidden

### 6.1 Minify-JSON gaming

Writing the whole catalog as one minified line so GitHub reports `+1`
is a fail. Codex / Qodana / human review cannot leave an inline comment
on a pair. `git blame` and `git diff` become opaque. The EVH slim
message is the tell: write **one identity per line** so the PR stays
under 2,500 added — compact **records**, not a minified document.

A compactness check that asserts `len(lines) == N` for N records
rejects a 1-line file of 64 records.

### 6.2 Vendoring `*mill*` / `*loop*` / `_gen_*plants*`

The mill burst rule is parse-input-only. Scripts stay on
`origin/legacy-mill-lane`. Tests re-extract with `git show` when that
ref is present and skip the live re-extract when it is not. Pin blob
sha1 + sha256. Do not `git add`:

- `<family>-mill*.py` / `<family>*mill*.py`
- `<family>-loop*.py`
- `_gen_<family>_*.py` / `_gen_*plants*`
- `<family>-plants*.py` / `mill_plants*.py`

Loops load mills (`mdb-loop-r1084` → `mdb-mill-r1148.py`;
`gor-loop-r1196` → `gor-mill-r1214.py`). Vendoring the loop pulls the
mill next. That is the vendoring loop. ACM's second commit (`7dccd5c`)
exists only because the first head vendored `acm-loop-r1.py`.

Tiny-source test fixtures may be a **hand-written** pair/plant snippet
(`acm-pairs-r1.py`). They may not be a dump of a legacy loop or plant-gen.

### 6.3 Second-PR slims

A slim of a still-open family PR is a forward commit on that head. The
owner comment on #255:

> Slimmed this same head under the merge cap. Forward commit `c90b2da`
> on `mill/acm` (no rebase, no second PR).

A follow-up **slice after the family lands** is a new PR. "We will add
it in a second PR opened now" is how ACM almost doubled the burst.

### 6.4 Dual pretty + JSONL copies

Two encodings of the same extract both count. Rank 1 is header hashes +
JSONL bodies. Rank 2 is header counts + one identity slice. Never both
a pretty `rows`/`pairs` array **and** a JSONL of those same bodies.

### 6.5 Pretty-print the pair catalog

WSR #272: 16 leftover3 pairs → 1059 catalog lines → **2497** additions
(3 under). EWR #257: 16 leftover-event pairs → 1043 catalog lines →
**2639**. CST #256: 1026 pair rows pretty-printed → **20751** catalog
lines → **21566**. RLB's first commit: 64 pretty pairs → 2231-line
catalog, over the cap before the loader finished growing.

WSR's 16 pairs would have been 16 JSONL lines plus a ~30-line header.
If CST or EWR is the template, stop and use RLB / CEI.

### 6.6 Plants as Python modules

#251 (`mill/db`) split 88 plants into `plants_01.py` / `plants_02.py` /
`plants_03.py` and still reported **2585** additions. Put plants in
JSONL.

### 6.7 Treating `leftover` in an id as mill mix

`docs/leftover-mill-quarantine.md`: leftover-in-id is the scenario
mechanic, not the mill test. Catalog slugs will contain `leftover`. Do
not strip them. Do not quarantine on the token.

### 6.8 Rebase, amend, or force-push to hide the over-cap commit

The land-stacked-prs contract is merge-only. RLB / ACM / EVH slimmed
with forward commits. The over-cap commit staying in history is
acceptable; the compare vs `main` is what the cap reads.

### 6.9 Inventing rows to fill a representative slice

ACM's eight rows are real extracts (`g46-w2` … `r4230`) with source
paths and sha256s. A slice of made-up "examples" is not a catalog. The
loader must re-extract those rows from the preserve commit and match.

## 7. What each cited family deferred

A deferred row is still extracted. The preserve-commit pin, `n_rows`,
and first/last slug remain. The **payload body** stays on
`origin/legacy-mill-lane` until a follow-up slice **after** this
family's PR has landed. Name the deferred set in the PR body.

| family | committed | deferred |
|---|---|---|
| rlb | all 64 pairs | nothing from those four sources |
| cei | all 39 r81 plants | hop loop `cei-loop-r81.py`; leftover mills `cei_r42_mill.py`, `cei_r48_mill.py`, `cei_r65_leftover3_mill.py`, `cei_r137_leftover3_mill.py` |
| amc | 24 first/last identities | remaining compact rows of the 1401-pair extract |
| evh | r801 dest `mill_plants_w`: 126 compact identities | r801 leftover/first/fix metric bodies; dests `mill_plants_x`, `aa`, `ac`–`ao` |
| acm | 8 representative rows + 6 source sha256s | 1044 pairs; 89 of 95 source files |

Chained mills contribute **only the pairs declared in that file**, not
the inherited parent catalog. Do not inflate a follow-up by
re-committing the parent.

## 8. Line-budget section for the mill PR body

Every mill PR body needs this **before** CI starts.

```markdown
## Line budget

GitHub additions vs `main` are **<M>** (limit 2500). Files: **<N>** (limit 20).

Encoding: header + compact JSONL | counts + one first-slice | representative slice
Catalog files: `config/<family>/CATALOG.json` (<h> lines) + `<pairs|plants>.jsonl` (<n> lines)

Extracted: <n_rows_extracted> pairs / <n_source_files> source files @ <preserve_commit>
Committed: <n_rows_committed>
Deferred: <named mills / dests / leftover leftover leftover scripts>

No second PR. No rebase. No vendored `*mill*.py` / `*loop*.py` / `_gen_*plants*`.
No pretty+JSONL copy of the same bodies. No minify-JSON gaming.
```

Operator return already used (keep it):

```text
sha: <head>
branch: mill/<family>
files: <N>
additions: <M>
row_count: <committed> / <extracted>
```

## 9. What a miller does, in order

1. Confirm the family already has a `REVIEWED_MILL_PREFIX_HOMES` row.
   This playbook does not add one.
2. `git fetch origin legacy-mill-lane` and locate the preserve commit.
3. AST-extract into a temp tree. Do not `exec`. Count rows.
4. Run the decision tree in §3. Pick rank 1 or 2 **before** creating
   files.
5. Write header + JSONL, or header + counts + one first-slice.
6. Write the sanctioned package only. Refuse vendor globs.
7. Pin compactness (`N` record lines, trailing newline, no CR, no
   leading whitespace) and a `git ls-files` vendor check.
8. Run `git diff --stat origin/main...HEAD`. If M > 2300, drop to rank
   2 or shrink the first slice **now**, on this head.
9. Fill the PR body line-budget section. Name the deferred mills.
10. Do not merge from the miller PR. Do not close it. Do not open a
    second PR for the slim.

Babysitters landing the burst then only retarget, wait for checks, and
squash. They should not have to invent an encoding.

## 10. What this playbook does not authorize

- A new mill family, prefix, or `REVIEWED_MILL_PREFIX_HOMES` row
- Vendoring or executing leftover mills
- A `round_txn` / `write_round` publisher on PR-a
- Writes under `outputs/raw/`
- Changing a hosted-frontier row off `research_only` / `blocked`
- A follow-up slice opened **before** the family's first PR lands
- Minifying JSON to beat the cap
- Pretty-printing full pair bodies because "the catalog is the source
  of truth" — the source of truth is the preserve-commit blob; the
  catalog is the extracted, pin-verified projection that fits the cap
- Editing `pipelines/leftover_mill.py`,
  `pipelines/mill_reviewed_vocabulary.py`, or `pipelines/__init__.py`
  from a catalog-encoding change
