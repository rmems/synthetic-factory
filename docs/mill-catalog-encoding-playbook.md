# Mill catalog encoding playbook

Encode the catalog **before** opening the mill PR. The 2026-09-15 burst
kept blowing the merge cap, then babysitters slimmed RLB, ACM, AMC, and
EVH after the fact. This document is the encoding those merged PRs
already paid for.

Docs-only. It does **not** onboard a mill family, change
`REVIEWED_MILL_PREFIX_HOMES`, vendor leftover mills, or authorize a
`round_txn` publisher. Do not mill from this playbook.

Additions and file counts below are the merge-time compare (the cap),
re-checked 2026-10-12 against each PR's squash commit (§11.7). Catalog
line counts are as merged unless the text says "on `main`"; follow-up
slices have since changed several of those files (§7).

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
     package + tests   ≈ 550–2100                  # measured at merge, §11.7
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

These five already landed. Copy the **encoding** each PR merged with,
not the family. Later slices committed most of the deferred rows (§7),
so the files on `main` are larger than the merge-time catalog column.

| family | PR | additions / files | catalog at merge | encoding | extracted | committed |
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
| #274 AMC | `pipelines/amc/CATALOG.json` **+6615** pretty catalog in a 7-module extract skeleton (7962 additions) | catalog-only package, `config/amc/CATALOG.json` +231, `pairs.jsonl` +24 (890 additions) | `dba8dff` "mill/amc: slim catalog to compact JSONL subset" |

CEI #270 encoded before opening and merged as one commit. That is the
point of this playbook.

ACM also dropped the vendored loop fixture
`tests/fixtures/contract-drift/tiny-source/acm-loop-r1.py` in `7dccd5c`
**before** the slice slim. Cut vendoring and encoding yourself.

## 5. Header + first-slice shape

Put the header where the package shape puts it (§11.6):
`config/<family>/CATALOG.json` for catalog-only and generate-library
packages (RLB, AMC, CEI), `pipelines/<family>/CATALOG.json` for extract
skeletons (GOR, MDB, EVH; WSR and ACM also keep theirs there).
Pretty-print the header. Filename:
`CATALOG.json`, not `catalog.json`. Field sets are in §11.1.

Rank 1: header lists mills and hashes; `pairs.jsonl` / `plants.jsonl`
holds every extracted row of the named mills. See
`config/rlb/CATALOG.json` + `config/rlb/pairs.jsonl` and
`config/cei/CATALOG.json` + `config/cei/plants.jsonl`.

Rank 2: header keeps extract totals even when bodies are omitted. AMC
#274 merged as the overflow valve, with these header values:

```json
{
  "n_pair_rows_extracted": 1401,
  "n_pair_rows_committed": 24,
  "extraction": "AST literals only; remaining compact pair rows are deferred; no second PR this family."
}
```

Each `catalogs` row in that header carries `n_rows_extracted`,
`first_slug`, `last_slug`, `source_blob_sha1`, and `source_sha256`.
At #274 the 24-line `config/amc/pairs.jsonl` was the first slice: the
first and last identity of each of the 12 catalogs, one object per
line. The follow-up #309 appended the other 1377 rows as compact
identities (`"role": "deferred"`), so on `main` the file is 1401 lines
and both header counts are 1401.

EVH #278 is the same rank with the first slice **inside** the header:
at merge, r801's 126 pair identities were one compact object per line
(`fail_slug`, `success_slug`, plants, domains, `kind`). Metric
constructor strings (`leftover_ok`, `first_ok`, `fix_ok`, …) stay on
`origin/legacy-mill-lane`. The other 15 dests kept counts only until
#313 committed their 1716 identities as `pipelines/evh/pairs.jsonl`.

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

ACM's header still holds those 8 rows and 6 source pins. The follow-up
#312 committed the other 1044 rows as compact `pipelines/acm/rows.jsonl`,
pinned by `extract.deferred_rows_sha256`.

`slice` is a family-local label, not a shared vocabulary: headers on
`main` use 21 distinct values. A loader that reads it pins it to one
constant and refuses drift (GOR's `load_catalog` rejects any `slice`
other than `SLICE_ID = "r946"`). Common values are `full` (eight
headers, e.g. `config/leftover6`, `config/brw`; RLB and CEI have no
`slice` field), `representative` (ACM's `extract.slice`), and the
first-slice mill (`r946`, `r709`, `r801`). `pipelines/nelb` uses
`partial` in its `extract` block, which its loader does not read. What
nelb enforces is `plants_sha256`, `plant_count`, and `plants_for_round`
refusing a round with no committed plant; the header also lists the 17
skipped rounds in `extract.deferred_rounds`. The label does not prove
what was committed: pin the committed count and digest beside it, and
the full extract total (`n_pair_rows`, `extract.full_row_count`) or the
deferred list when rows are held back.

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

WSR and EWR were later re-encoded that way. WSR #327 replaced the
1059-line `config/wsr/catalog.json` with `pipelines/wsr/CATALOG.json`
(30 lines) and `pipelines/wsr/pairs.jsonl`, where the same 16 pairs are
16 lines (plus a 16-pair r89 slice). EWR #329 replaced its 1043-line
`config/ewr/catalog.json` with `config/ewr/CATALOG.json` and
`pairs.jsonl` the same way. CST is still a 20751-line pretty catalog on
`main`. If CST, or EWR or WSR as first merged, is the template, stop and
use RLB / CEI.

### 6.6 Plants as Python modules

#251 (`mill/db`) split 88 plants into `plants_01.py` / `plants_02.py` /
`plants_03.py` and still reported **2585** additions. Put plants in
JSONL.

### 6.7 Treating `leftover` in an id as mill mix

`docs/leftover-mill-quarantine.md`: leftover-in-id is the scenario
mechanic, not the mill test. Catalog slugs will contain `leftover`. Do
not strip them. Do not quarantine on the token.

### 6.8 Rebase, amend, or force-push to hide the over-cap commit

The land-stacked-prs contract is merge-only. RLB / ACM / AMC / EVH
slimmed with forward commits. The over-cap commit staying in history is
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

| family | committed at merge | deferred at merge | landed since (on `main`) |
|---|---|---|---|
| rlb | all 64 pairs | nothing from those four sources | — |
| cei | all 39 r81 plants | hop loop `cei-loop-r81.py`; leftover mills `cei_r42_mill.py`, `cei_r48_mill.py`, `cei_r65_leftover3_mill.py`, `cei_r137_leftover3_mill.py` | all four mills: r48 (16 plants) in #355, r42 / r65 / r137 (7 + 12 + 15) in #375, so `config/cei/plants.jsonl` holds 89 plants from 5 mills. The hop loop is refused (`cei.loop_refused`) and stays on the legacy lane |
| amc | 24 first/last identities | remaining compact rows of the 1401-pair extract | the other 1377 rows in #309; `config/amc/pairs.jsonl` holds all 1401 |
| evh | r801 dest `mill_plants_w`: 126 compact identities | r801 leftover/first/fix metric bodies; dests `mill_plants_x`, `aa`, `ac`–`ao` | the 1716 dest identities in #313 as `pipelines/evh/pairs.jsonl`; metric bodies stay on the legacy lane |
| acm | 8 representative rows + 6 source sha256s | 1044 pairs; 89 of 95 source files | the 1044 rows in #312 as `pipelines/acm/rows.jsonl`; the header still pins 6 source files |

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
5. Write header + JSONL, or header + counts + one first-slice
   (§11.1, §11.2, §11.4).
6. Write the sanctioned package only (§11.6). Refuse vendor globs
   (§11.5).
7. Pin compactness (`N` record lines, trailing newline, no CR, no
   leading whitespace) and a vendor-glob check (§11.3).
8. Run `git diff --stat origin/main...HEAD`. If M > 2300, drop to rank
   2 or shrink the first slice **now**, on this head (§11.7).
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

## 11. Copy-paste templates

Fill the `<angle-bracket>` placeholders. Fields and code below are
copied from the family each subsection cites, and every path and
command exists on `main`; when a template and the cited file disagree,
the file wins. `docs/mill-support-p4-design.md` plans to
move the vendor-refusal loop, `sha256_bytes`, the majority
`dumps_catalog`, and the AST literal helpers into one shared package.
That package has not landed, so each family still carries these bodies.

### 11.1 Header JSON

Two header shapes are on `main`. Use the one that matches the package
shape (§11.6); each family's loader pins its field set, so do not mix
them. `factory` is the family's `REVIEWED_MILL_PREFIX_HOMES` value and
must be a `config/FACTORY-REGISTRY.json` row.

**Generate library, rank 1** — `config/<family>/CATALOG.json` beside
`plants.jsonl` (CEI, GQL, FLK, MSD, RAG, SAF). The loader refuses a
`plants_sha256` that is not the sha256 of the `plants.jsonl` bytes
(final newline included). `record_kind` is pinned too: `episode`, or
`safety_case` for SAF, matching the registry row's `record_kinds`.

```json
{
  "catalog_id": "<family>-<plants|pairs>-v1",
  "factory": "<factory-slug>",
  "format": "<family>-catalog/1",
  "mill_prefix": "<family>",
  "mills": [
    {
      "base_round": <NN>,
      "mill_id": "<family>_r<NN>",
      "plant_count": <n_rows>,
      "source": "experiments/<legacy script name>.py"
    }
  ],
  "plant_count": <n_rows_total>,
  "plants_sha256": "<sha256 of plants.jsonl>",
  "quota_per_round": 2,
  "record_kind": "episode",
  "source": {
    "commit": "<40-hex preserve commit>",
    "method": "git-show+ast.parse",
    "ref": "legacy-mill-lane",
    "scripts": [
      "experiments/<legacy script name>.py"
    ]
  }
}
```

Copy each `source` path exactly as it is on `legacy-mill-lane`; the
names do not follow one pattern (`cei-mill-r81.py`,
`flk_r1489_leftover3_mill.py`, `msd-leftover-mill-r430.py`,
`rag-mill-lll-r670.py`). Only `mill_id` is regular: `<family>_r<NN>`.

**Extract skeleton, rank 2** — `pipelines/<family>/CATALOG.json` (GOR,
MDB, AZR, DBC, SSR). `mills` is an object keyed by `mill_id`; only the
first-slice mill also carries a `pairs` array of identities. `slice`
names that mill (`r946` GOR, `r709` MDB, `r801` EVH). SSR adds an
`extract` block; EVH adds archive keys from later slices.

```json
{
  "factory": "<factory-slug>",
  "generator": "grok-4.6",
  "mills": {
    "<family>-mill-r<NNN>": {
      "blob_sha": "<git blob sha1 of the source>",
      "catalog_first": <NNN>,
      "factory": "<factory-slug>",
      "first_slug": "<first success slug>",
      "generator": "grok-4.6",
      "kind": "pairs",
      "last_slug": "<last success slug>",
      "mill_id": "<family>-mill-r<NNN>",
      "n_rows": <n_rows>,
      "path": "experiments/<family>-mill-r<NNN>.py",
      "sha256": "<sha256 of the source bytes>",
      "shape": "<family shape id, e.g. pairs-literal>"
    }
  },
  "n_mills": <n_mills>,
  "n_pair_rows": <n_rows_extracted>,
  "preserve_commit": "<40-hex>",
  "schema": "<family>-catalog-extract/v1",
  "slice": "r<NNN>",
  "source_ref": "origin/legacy-mill-lane"
}
```

`mill_id` is the script's file stem (`mill_id_for_path` returns
`Path(path).stem`). The five first-slice mills above are all
`<family>-mill-r<NNN>`, but other mills keep their legacy names
(`ssr-mill-lll-r494`, `ssr-mill-decoder`); copy them as they are.

`generator` records the hosted model that wrote the legacy script. It
is provenance, not onboarding: the registry row stays `research_only` /
`blocked`, and a generate library does not stamp it on records. Write
this header with the majority `dumps_catalog`
(`pipelines/gor/catalog_extract.py`):
`json.dumps(document, ensure_ascii=True, indent=2, sort_keys=True) + "\n"`.

### 11.2 Compact JSONL writer

From `dumps_pairs_jsonl` in `pipelines/gor/catalog_extract.py` (EVH,
AZR, and LHC carry the same body):

```python
import json
from collections.abc import Mapping
from typing import Any


def dumps_pairs_jsonl(rows: list[Mapping[str, Any]]) -> str:
    """One record per line. No pretty indent. Trailing newline. No CR."""

    lines = [
        json.dumps(row, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        for row in rows
    ]
    return "\n".join(lines) + "\n"
```

`separators=(",", ":")` is correct **per record** and forbidden for the
header or a whole-catalog dump (§6.1). The family writes this text only
to its own committed `pairs.jsonl` / `plants.jsonl`, never under
`outputs/`. Read it back fail-closed the way GOR's `load_pair_rows`
does: refuse CR, a missing final newline, an empty line, or a line that
starts with whitespace. To see a landed record:

```bash
head -n 1 config/rlb/pairs.jsonl | python3 -m json.tool
```

### 11.3 Compactness and vendor tests

Compactness is pinned in `tests/test_rlb_catalog.py`,
`tests/test_amc.py`, `tests/test_gor.py`, and most extract-family
tests; the prefix, vendor-glob, and no-exec checks are from
`tests/test_gor.py`. The module below is written for an **extract
skeleton**, where `cv` is the family's `vocabulary`. A generate library
has no `vocabulary.py`: point `PAIRS_JSONL` at
`config/<family>/plants.jsonl`, take `FACTORY` and the prefix
(`MILL_PREFIX` in CEI) from `_contract`, and replace the vendor-glob
test with the package scan for `*mill*.py` that `tests/test_cei.py`
uses.

```python
import ast
import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

# Extract skeleton. A generate library imports <family>._contract instead.
from <family> import vocabulary as cv  # noqa: E402
from mill_reviewed_vocabulary import REVIEWED_MILL_PREFIX_HOMES  # noqa: E402

PACKAGE = REPO / "pipelines" / "<family>"
# Generate library: REPO / "config" / "<family>" / "plants.jsonl"
PAIRS_JSONL = PACKAGE / "pairs.jsonl"
EXPECTED_ROWS = <n_rows_committed>


def _module_uses_exec(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return [
        f"{path.name}:{node.lineno}:{node.func.id}"
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in {"exec", "eval", "compile"}
    ]


class CatalogEncodingTests(unittest.TestCase):
    def test_reviewed_prefix_maps_to_factory(self):
        self.assertEqual(REVIEWED_MILL_PREFIX_HOMES[cv.FAMILY_PREFIX], cv.FACTORY)

    def test_pairs_jsonl_stays_compact(self):
        text = PAIRS_JSONL.read_text(encoding="utf-8")
        lines = text.splitlines()
        self.assertEqual(len(lines), EXPECTED_ROWS)
        self.assertTrue(text.endswith("\n"))
        self.assertNotIn("\r", text)
        for line in lines:
            self.assertFalse(line.startswith((" ", "\t")))
            json.loads(line)

    def test_no_vendored_mill_scripts(self):
        hits = []
        for pattern in cv.FORBIDDEN_MILL_GLOBS:
            hits.extend(
                path for path in REPO.rglob(pattern) if "legacy-mill-lane" not in str(path)
            )
        self.assertEqual(hits, [])

    def test_package_never_execs(self):
        hits = []
        for path in sorted(PACKAGE.glob("*.py")):
            hits.extend(_module_uses_exec(path))
        self.assertEqual(hits, [])
```

`assertEqual(len(lines), EXPECTED_ROWS)` is what rejects a one-line
minified file. Also pin, as the cited tests do:

- the committed row count against the header: equal to `plant_count`
  for rank 1; below the pinned extract total (`n_pair_rows`,
  `extract.full_row_count`) for rank 2 / last resort
- each mill's source blob sha1 and content sha256 (`blob_sha` /
  `sha256` in an extract header, `source_blob_sha1` / `source_sha256`
  in RLB's)
- the **bytes** of a regenerated header, not its parsed value. GOR's
  live re-extract test compares `dumps_catalog(catalog_document(...))`
  with the file text. EVH's compares `json.loads` of both, and on
  `main` its r801 `pairs` are pretty-printed again: the file is 1,827
  lines where EVH's own `dumps_catalog` of the same document is 819.

### 11.4 Rank-2 hybrid dumper

When the first-slice identities live inside a pretty header, a pretty
identity costs about nine lines (seven keys plus braces, as in GOR's
r946 slice). GOR (27) and MDB (37) paid that. Above about 40
identities, use EVH's encoder from `pipelines/evh/catalog_extract.py`,
which keeps the header pretty and writes each `pairs` element on one
line. Drop metric bodies first; the identity is the slugs, plants,
domains, and kind.

```python
import json
from collections.abc import Mapping
from typing import Any

PAIR_IDENTITY_KEYS = (
    "fail_domain",
    "fail_plant",
    "fail_slug",
    "kind",
    "success_domain",
    "success_plant",
    "success_slug",
)


def compact_pair_identity(pair: Mapping[str, Any]) -> dict[str, Any]:
    """Keep pair identity; drop leftover/first/fix metric bodies."""

    return {key: pair[key] for key in PAIR_IDENTITY_KEYS}


def dumps_catalog(document: Mapping[str, Any]) -> str:
    """Pretty-print the catalog; pair identities stay one object per line."""

    return _encode(document, 0, key=None) + "\n"


def _encode(value: Any, level: int, key: str | None) -> str:
    pad = "  " * level
    if isinstance(value, dict):
        if not value:
            return "{}"
        parts = [
            f"{pad}  {json.dumps(item_key)}: {_encode(value[item_key], level + 1, item_key)}"
            for item_key in sorted(value)
        ]
        return "{\n" + ",\n".join(parts) + f"\n{pad}}}"
    if isinstance(value, list):
        if not value:
            return "[]"
        if key == "pairs":
            lines = [
                f"{pad}  "
                + json.dumps(
                    item, ensure_ascii=True, sort_keys=True, separators=(", ", ": ")
                )
                for item in value
            ]
            return "[\n" + ",\n".join(lines) + f"\n{pad}]"
        lines = [f"{pad}  {_encode(item, level + 1, None)}" for item in value]
        return "[\n" + ",\n".join(lines) + f"\n{pad}]"
    return json.dumps(value, ensure_ascii=True)
```

`PAIR_IDENTITY_KEYS` is EVH's; a family substitutes its own identity
fields. EVH's slim (`75ecf45`) took `pipelines/evh/CATALOG.json` from
2265 lines of pretty pairs with metric bodies to 501 (`+126 / -1890`).
Pin the header bytes (§11.3) so a later slice cannot undo it.

### 11.5 Vendor refusal

From `pipelines/gor/identity.py` and `pipelines/gor/vocabulary.py`; the
extract skeletons on `main` share this shape. The predicate and the
prefix tuple stay family-local (the P4 design keeps them local too);
only the loop is common. Refusal is `SystemExit` with
`refusing to vendor <name>`, and `tests/test_gor.py` asserts it.

```python
# pipelines/<family>/vocabulary.py
FAMILY_PREFIX = "<family>"
FACTORY = "<factory-slug>"
VENDOR_PREFIXES = ("<family>-mill-", "<family>-loop-", "_gen_<family>_")
FORBIDDEN_MILL_GLOBS = (
    "<family>-mill*.py",
    "<family>-loop*.py",
    "_gen_<family>_*.py",
)
```

```python
# pipelines/<family>/identity.py
from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from .vocabulary import VENDOR_PREFIXES


def is_vendor_filename(name: str) -> bool:
    """True when ``name`` is a mill / loop / plant-gen publisher script."""

    if not name.endswith(".py"):
        return False
    return name.startswith(VENDOR_PREFIXES)


def refuse_vendor_paths(paths: Iterable[Path | str]) -> None:
    """Fail closed if any path would vendor a legacy mill script."""

    for raw in paths:
        name = Path(raw).name
        if is_vendor_filename(name):
            raise SystemExit(f"refusing to vendor {name}")
```

Extend the predicate, never narrow it. The landed sets go past the three
prefixes: GOR also refuses `gor_*_mill.py`, MDB `mdb-hop-` and
`mdb_*_mill.py`, EVH `eval_harness_` and `mill_plants`. Read the
family's legacy tree for the names it actually uses.

### 11.6 Package skeletons

Three shapes are on `main`. Do not invent a fourth on a first PR.

**Catalog-only** (RLB, AMC): loader, header, JSONL. RLB landed at 668
additions.

```text
pipelines/<family>/__init__.py
pipelines/<family>/catalog.py
config/<family>/CATALOG.json
config/<family>/pairs.jsonl
tests/test_<family>.py
```

**Generate library** (CEI, GQL, FLK, MSD, RAG, SAF): five modules.

```text
pipelines/<family>/__init__.py
pipelines/<family>/_contract.py    # identity, coded refusals, import twins
pipelines/<family>/catalog.py      # load header + plants.jsonl; ast.parse extract
pipelines/<family>/generate.py     # 16-step success + 17-step handoff pairs
pipelines/<family>/cli.py          # catalog-check | generate
config/<family>/CATALOG.json
config/<family>/plants.jsonl
tests/test_<family>.py
tests/fixtures/<family>/CATALOG.json
tests/fixtures/<family>/plants.jsonl   # one hand-written plant, not a dump
```

Each module binds its two import names with `bind_import_twin(__name__)`
(imported in `_contract` from `oracle_grounded.import_twins`; `cli.py`
binds only when imported as a package), so `pipelines/__init__.py`
stays untouched. `generate` writes a brand-new `--out` directory,
refuses one that exists, and refuses any path that names or aliases
`outputs/raw/` (`raw_tree_guard.is_under_raw`). It does not import
`round_txn`. Check a landed one against its fixture:

```bash
python3 -m pipelines.cei.cli catalog-check --json
python3 -m pipelines.cei.cli catalog-check --catalog tests/fixtures/cei --json
python3 -m pipelines.cei.cli generate --catalog tests/fixtures/cei --all --out <new-directory> --json
```

Records reach `outputs/raw/` only through `round_txn.py` (reserve →
stage → validate → publish), in a separate reviewed change; a mill PR
does not do that (§10).

**Extract skeleton** (GOR, AZR, DBC, SSR; MDB and EVH grew from it):
no generate, no CLI.

```text
pipelines/<family>/__init__.py
pipelines/<family>/catalog.py
pipelines/<family>/catalog_ast.py
pipelines/<family>/catalog_extract.py
pipelines/<family>/identity.py
pipelines/<family>/sources.py
pipelines/<family>/vocabulary.py
pipelines/<family>/CATALOG.json
pipelines/<family>/pairs.jsonl      # compact identities (GOR added its own in a follow-up slice)
tests/test_<family>.py
```

ACM's first head used a nine-module `pipelines/contract_drift/`; the
slim collapsed it to five. Start at the smallest shape that holds the
catalog.

### 11.7 Budget arithmetic

Additions at merge, per file, from each squash commit. Reproduce with
`git show --numstat --format= <commit>`; a shallow clone needs
`git fetch --shallow-since=2026-09-10 origin main` first.

```text
additions ≈ package_py + tests + header + payload_lines (+ fixtures)

RLB #252  c1890c35   668 = 31+380 (__init__, catalog) + 146 tests + 47 header + 64 jsonl
CEI #270  1ea42d4a  2193 = 15+222+702+175+642 (five modules) + 353 tests
                           + 26 header + 39 jsonl + 18+1 fixtures
EVH #278  4e68fe4c  2177 = 33+154+246+653+40+105+47 (extract skeleton) + 398 tests + 501 catalog
GOR #265  6ea0f6c2  1885 = 32+116+173+334+40+261+84 + 354 tests + 491 catalog
MDB #268  6491f951  1957 = 32+112+155+373+40+314+59 + 319 tests + 553 catalog
WSR #272  b9953980  2497 = 33+161+544+109+397 + 194 tests + 1059 pretty catalog
ACM #255  beb658cd  1341 = 45+81+270+57+437 + 125 tests + 219 slice + 47+60 fixtures
```

Package plus tests ran 557 for catalog-only RLB, 1394–1676 for the
three extract skeletons, and 1015–2109 for the five-module packages
(ACM, WSR, CEI). Against the 2,300-line target that leaves roughly
200–1300 lines of catalog for the last two shapes. At WSR's ≈66 lines
per pretty pair (1059 / 16) that is three to twenty pairs; as JSONL it
is one line per row.

These are the files as merged. `main` has since moved several of them
(WSR's catalog is now `pipelines/wsr/CATALOG.json`), so measure your
own head with `git diff --stat origin/main...HEAD` (§1).
