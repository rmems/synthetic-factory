# Mill catalog encoding playbook

Future millers encode the catalog **before** opening the PR so babysitters
stop slimming after the fact. This document is the encoding contract extracted
from the seven merged mill PRs that actually hit the ≤2,500-added-line cap.
It does **not** onboard a new mill family, change
`REVIEWED_MILL_PREFIX_HOMES`, or authorize a raw-tree publisher.

Measured 2026-09-15 against `rmems/synthetic-factory` with `gh pr view` and
`gh api repos/rmems/synthetic-factory/compare/{baseRefOid}...{headRefOid}`.
Line counts below are GitHub **additions** on that 3-dot compare (the merge
cap), not `wc -l` of one file. Landed files on `main` were re-read after
`origin/main` advanced through the mill burst; catalog-file line counts match
the compare.

## 1. The cap babysitters were enforcing

| gate | limit | what GitHub counts |
|---|---|---|
| added lines | **≤ 2,500** | newline-separated additions on `origin/main...HEAD` |
| changed files | **≤ 20** | paths in that same compare |

The live check, copy-paste:

```bash
git fetch origin main
git diff --stat origin/main...HEAD
# last line must read: N files changed, M insertions(+)
# with N <= 20 and M <= 2500
```

`git diff --shortstat origin/main...HEAD` is the same number GitHub's
`additions` field reports for a single-commit mill PR. Multi-commit PRs that
add then delete still report the **net** additions of the compare, not the
sum of every commit. Slimming therefore belongs on the **same head** as a
forward commit (RLB `aeea952`, ACM `c90b2da`, EVH `75ecf45`). Do not open a
second PR. Do not rebase.

A pretty-printed JSON object costs one GitHub line per key, per indent, per
array element. A compact JSONL record costs **one line per plant or pair**,
regardless of how wide the object is. That is the whole encoding fight.

The cap is a merge-hygiene gate, not a data-quality gate. Dropping cases to
fit, minifying a catalog onto one line, or vendoring the mill so the catalog
can be smaller are all failures.

## 2. Winning encoding (ranked)

Three encodings shipped. Only the first two are allowed on a new mill PR.
Pretty JSON of full pair bodies is the encoding that forced babysitters to
intervene.

| rank | encoding | GitHub cost | when it wins | exemplars |
|---|---|---|---|---|
| **1** | **Pretty header + compact JSONL payloads** | header ≈ 20–80 lines; payloads = N records | N pair/plant rows fit in the leftover budget after the package | RLB #252 (47 + 64), CEI #270 (26 + 39). House pattern: `catalogs/python-repair-v1/`. Also AMC #274, LEF #273, GQL #248, RAG #245, FLK #244, MSD #242 |
| **2** | **Pretty header + counts for every mill + first-slice compact identities** | header + one identity line per committed pair + ≈15 lines per deferred mill | full JSONL of the extract exceeds the cap | EVH #278 (r801's 126 compact identities + counts for 15 dests), GOR #265 (r946's 27 identities + counts), MDB #268 (r709's 37 identities + counts). NTP #271 is the counts-only extreme (12-line header, 1625 rows deferred) |
| **3 — do not copy** | Pretty JSON of full pair bodies | ≈ 40–70 lines per pair | never, unless N ≤ 8 **and** the catalog file stays under ≈ 200 lines | WSR #272 sat at **2497 / 2500**. EWR #257 (1043-line pretty catalog, **2639** additions) and CST #256 (20751-line pretty catalog, **21566** additions) overshot |
| **last resort** | Representative pretty slice of **real** rows + `extract.full_*` pins | slice rows + a handful of source pins | even compact JSONL of the full extract cannot fit | ACM #255 (8 of 1052 pairs) |

Rank 1 is the default. Rank 2 is the overflow valve. Rank 3 is how WSR
almost missed the cap with only 16 pairs. The last resort is how ACM
survived a 1052-row extract.

### 2.1 What "compact" means (and what it does not)

Compact is **one JSON object per record, one record per line**, with no
leading whitespace on the record line.

```text
{"slug":"...","ok":{...},"bad":{...}}
{"slug":"...","ok":{...},"bad":{...}}
```

It is not:

- `json.dumps(entire_catalog, separators=(",", ":"))` written as a single
  line so GitHub reports `+1`. That is minify-JSON gaming. Unreviewable.
  Forbidden.
- Pretty-printed pair objects inside `CATALOG.json` (`{\n  "fail_slug": ...`
  over eight lines). GOR and MDB paid that tax on the first slice; EVH's
  `dumps_catalog` avoided it by encoding the `pairs` array as one object per
  line inside an otherwise pretty document.
- A `.py` module of plant dicts (`pipelines/db/plants_01.py` at 564 lines × 3
  in #251). That is a catalog wearing a Python costume.

EVH's writer is the reference for rank-2 hybrid encoding:
`pipelines/evh/catalog_extract.py` `dumps_catalog` / `_encode`. Pretty wrapper;
when `key == "pairs"`, each element is
`json.dumps(item, ensure_ascii=True, sort_keys=True, separators=(", ", ": "))`
on its own line.

## 3. Decision tree (run this before writing files)

Copy-paste and fill the brackets.

```text
1. AST-extract every pair/plant from origin/legacy-mill-lane (ast.parse, exec:false).
   Record: n_rows_extracted, n_source_files, preserve commit, per-mill n_rows.

2. Estimate GitHub additions:
     package_py   ≈ 800–1800   (five-module generate library) 
                               or 900–1600 (extract skeleton)
     tests        ≈ 150–400
     header       ≈ 30–80
     jsonl        = n_rows_extracted          # rank 1
     identities   = n_first_slice             # rank 2, typically 16–126
     mill_counts  ≈ 15 * n_other_mills        # rank 2
     pretty_pairs ≈ 60 * n_rows_extracted     # rank 3 — do not use

3. If header + jsonl + package + tests <= 2300:
     RANK 1. Commit every extracted row as compact JSONL. Defer nothing.
     RLB did this (668 additions, 64/64 pairs). CEI did this for r81 (39/39).

4. Else if header + mill_counts + first_slice_identities + package + tests <= 2300:
     RANK 2. Commit:
       - per-mill n_rows, first_slug, last_slug, sha256, blob_sha, shape
       - compact identities for ONE first mill (the smallest or earliest)
       - extract.full_row_count / n_pair_rows for the rest
     Defer full pair bodies. Say so in the PR body. No second PR.

5. Else:
     LAST RESORT. Representative slice of real extracted rows (not invented),
     plus extract.full_row_count and extract.full_source_files.
     ACM: 8 of 1052. Follow-up slice after this PR lands, same family.

6. Never: pretty-print full pair bodies. Never: minify the catalog to one line.
   Never: vendor *mill*.py / *loop*.py / _gen_*plants*.py.
   Never: open a second PR to slim this family.
```

Keep 200 lines of slack. WSR had 3. That is why babysitters exist.

## 4. Per-family ledger (the seven PRs)

Compare status is `gh api compare/{baseRefOid}...{headRefOid}`. Additions are
the PR's GitHub `additions` field (same as the compare file-sum for these
heads). Merge commits are squash-onto-main.

| family | PR | head | additions / files | catalog files (landed lines) | encoding | extracted | committed | deferred |
|---|---|---|---|---|---|---|---|---|
| **rlb** | [#252](https://github.com/rmems/synthetic-factory/pull/252) | `aeea952` | **668 / 5** | `config/rlb/CATALOG.json` 47 + `pairs.jsonl` 64 | rank 1: header + compact JSONL | 64 pairs / 128 cases from 4 sources | **64 / 64** | **none**. The pretty 2231-line `config/rlb-case-catalog-v1.json` was split on this same PR, not dropped |
| **acm** | [#255](https://github.com/rmems/synthetic-factory/pull/255) | `c90b2da` | **1341 / 9** | `pipelines/acm/CATALOG.json` 219 | last resort: 8-row pretty slice | 1052 pairs / 95 source files | **8** real rows + 6 source pins | 1044 pairs; 89 source pins; `catalogs/api-contract-migration-v1/{CATALOG.json,rows.jsonl}`; 9-module `pipelines/contract_drift/`; `acm-loop-r1.py` fixture |
| **evh** | [#278](https://github.com/rmems/synthetic-factory/pull/278) | `75ecf45` | **2177 / 9** | `pipelines/evh/CATALOG.json` 501 | rank 2: r801 126 compact identities + counts | 1842 pairs / 16 dests / 9 scripts | 126 identities (r801) + counts for 15 dests | leftover/first/fix metric **bodies** on r801; all pair payloads for dests x, aa, ac–ao (1716 rows) |
| **wsr** | [#272](https://github.com/rmems/synthetic-factory/pull/272) | `6a0a1c7` | **2497 / 7** | `config/wsr/catalog.json` 1059 | rank 3 pretty (do not copy) | 16 leftover3 pairs (r41–56) from one mill | **16 / 16** leftover3 | `wsr-plants-r73.py`; QBP leftover3 constructors; hopper helpers |
| **gor** | [#265](https://github.com/rmems/synthetic-factory/pull/265) | `51b9b68` | **1885 / 9** | `pipelines/gor/CATALOG.json` 491 | rank 2: r946 27 pretty identities + counts | 988 declared rows / 16 mills / 33 scripts | 27 identities (r946) + counts for 15 mills | full pair payloads for r973+ (961 rows), including `gor-mill-r1460` 528 |
| **cei** | [#270](https://github.com/rmems/synthetic-factory/pull/270) | `b6fa49e` | **2193 / 10** | `config/cei/CATALOG.json` 26 + `plants.jsonl` 39 | rank 1: header + compact JSONL | 39 `_ok`/`_bad` pairs from `cei-mill-r81` | **39 / 39** of r81 | hop loop `cei-loop-r81.py`; leftover leftover leftover mills `cei_r42_mill.py`, `cei_r48_mill.py`, `cei_r65_leftover3_mill.py`, `cei_r137_leftover3_mill.py` |
| **mdb** | [#268](https://github.com/rmems/synthetic-factory/pull/268) | `b67cee8` | **1957 / 9** | `pipelines/mdb/CATALOG.json` 553 | rank 2: r709 37 pretty identities + counts | 1321 composed rows / 20 mills / 41 scripts | 37 identities (r709) + counts for 19 mills | full pair payloads for r746+ (1284 rows). Filename `mdb-mill-r961` keeps `CATALOG_FIRST = 977` |

Factory homes (already in `REVIEWED_MILL_PREFIX_HOMES`; do not edit that table
from a mill PR):

| prefix | factory |
|---|---|
| rlb | `rate-limit-backoff-factory` |
| acm | `api-contract-migration-factory` |
| evh | `eval-harness-trajectory-factory` |
| wsr | `websocket-reconnect-factory` |
| gor | `git-ops-recovery-factory` |
| cei | `csv-excel-ingest-factory` |
| mdb | `monorepo-dep-bump-factory` |

### 4.1 Slimming commits babysitters should not have to write

| PR | before | after | commit |
|---|---|---|---|
| #252 RLB | `config/rlb-case-catalog-v1.json` **+2231** pretty pairs | header +47, `pairs.jsonl` +64 | `aeea952` "Compact the RLB catalog into header JSON plus JSONL pairs" |
| #255 ACM | `rows.jsonl` +1052, `CATALOG.json` +919, 9-module `contract_drift/` | 8-row `pipelines/acm/CATALOG.json` +219, five-module package | `c90b2da` "Slim ACM onto pipelines/acm with a representative catalog slice"; owner comment on the same head |
| #278 EVH | `CATALOG.json` **2265** pretty pairs with leftover/first/fix metric bodies | `CATALOG.json` **501** (`+126 / -1890`) | `75ecf45` "Slim EVH r801 identities under the merge cap" |

ACM also dropped the vendored loop fixture `tests/fixtures/contract-drift/tiny-source/acm-loop-r1.py` in `7dccd5c` **before** the slice slim. That is a vendoring-loop cut, not an encoding cut. Do both cuts yourself.

GOR, MDB, CEI, and WSR shipped in one commit. GOR/MDB chose rank 2 up front.
CEI chose rank 1 up front. WSR chose rank 3 and arrived at 2497. The playbook
exists so the next miller does not repeat WSR or wait for a babysitter to
repeat RLB/ACM/EVH.

## 5. What each family deferred (do not "complete" these on a new-family PR)

A deferred row is still extracted. The preserve-commit pin, `n_rows`, and
first/last slug remain. The **payload body** stays on `origin/legacy-mill-lane`
until a follow-up slice **after** this family's PR has landed. The PR body
must name the deferred set. "We will add it in a second PR opened now" is
how ACM almost doubled the burst.

| family | committed | deferred | follow-up shape |
|---|---|---|---|
| rlb | all 64 pairs | nothing | none |
| acm | 8 representative rows (`g46-w2`, `g46-w3`, `g46-w6`, `r3561`, `r3620`, `r3667`, `r3698`, `r4230`) + 6 source sha256s | 1044 pairs; 89 of 95 source files | rank-1 JSONL of the remaining rows, or rank-2 identities if that JSONL still exceeds the cap. `extract.full_row_count = 1052` / `full_source_files = 95` already pinned |
| evh | r801 dest `mill_plants_w`: 126 compact identities (`success_slug`, `fail_slug`, `success_domain`, `fail_domain`, `success_plant`, `fail_plant`, `kind`) | r801 leftover/first/fix metric constructor strings; dests `mill_plants_x`, `aa`, `ac`–`ao` (78+117+4×351+117 = 1716 rows) | one dest per follow-up PR as compact JSONL or compact identities |
| wsr | 16 leftover3 pairs r41–56 from `experiments/wsr-mill-leftover3-r41.py` | r73 plants (`wsr-plants-r73.py`) that hop QBP leftover3 constructors and hopper | own PR; do not fold QBP/hopper into `pipelines/wsr` |
| gor | r946: 27 pair identities (`success_slug`, `fail_slug`, markers, stems, `fail_handoff`) | r973 (30), r1003 (16), r1044 (19), r1046 (46), r1111 (20), r1127 (48), r1131 (24), r1196 (16), r1214 (16), r1230 (16), r1278 (93), r1371 (34), r1405 (12), r1417 (43), **r1460 (528)** | r1460 is its own slice; do not pretty-print 528 pairs |
| cei | all 39 r81 plants | `cei-loop-r81.py`; `cei_r42_mill.py`; `cei_r48_mill.py`; `cei_r65_leftover3_mill.py`; `cei_r137_leftover3_mill.py` | AST-extract those mills into additional JSONL files after #270. Do not vendor the hop loop |
| mdb | r709: 37 pair identities (`success_slug`, `fail_slug`, plants, `fail`) | r746 (16), r762 (14), r776 (64), r840 (78), r918 (150), r961/977 (16), r1068 (16), r1084 (64), r1148 (60), r1208 (143), r1351 (56), r1407 (47), r1454 (80), r1534 (80), r1614 (80), r1694 (80), r1774 (80), r1854 (80), r1934 (80) | tools-make / slugs-row mills are large; rank 1 JSONL or rank 2 identities, never pretty |

Chained mills contribute **only the pairs declared in that file**
(`PAIRS` / `NEW_PAIRS` / `MORE_PAIRS` / `MORE` / `add`), not the inherited
parent catalog. GOR and MDB already encode that in `n_rows`. Do not inflate
a follow-up by re-committing the parent.

## 6. Copy-paste: header JSON

Put the header at `config/<family>/CATALOG.json` (preferred) or
`pipelines/<family>/CATALOG.json` if the package is catalog-only. Pretty-print
the header. Never put pair bodies in it when N > 8.

```json
{
  "schema": "<family>-catalog-extract/v1",
  "family": "<family>",
  "factory": "<factory-slug-from-REVIEWED_MILL_PREFIX_HOMES>",
  "generator": "grok-4.6",
  "source_ref": "origin/legacy-mill-lane",
  "preserve_commit": "<40-hex>",
  "extraction": "AST literals only; legacy modules were never imported or executed",
  "slice": "full",
  "n_mills": 1,
  "n_pair_rows": 64,
  "n_pair_rows_committed": 64,
  "quota_per_round": 2,
  "steps": 16,
  "plants_sha256": "<sha256 of the JSONL bytes, including the terminating newline>",
  "mills": [
    {
      "mill_id": "<family>-mill-rNN",
      "path": "experiments/<family>-mill-rNN.py",
      "source_blob_sha1": "<git blob sha1>",
      "sha256": "<content sha256>",
      "shape": "pairs-literal",
      "catalog_first": 81,
      "n_rows": 39,
      "first_slug": "<first success slug>",
      "last_slug": "<last success slug>"
    }
  ]
}
```

Rank-2 / last-resort headers **must** keep the extract totals even when
bodies are omitted. ACM's landed pin:

```json
{
  "extract": {
    "exec": false,
    "method": "ast.parse",
    "slice": "representative",
    "full_row_count": 1052,
    "full_source_files": 95,
    "source_commit": "6d5ed0c1cac87618a05fab37f2e59bebca0a6031",
    "source_ref": "legacy-mill-lane",
    "source_files": 95
  },
  "row_count": 8,
  "rows_sha256": "51d5a9cc622c2a5c1f69e27527841fd3f27d25cdc4d85fafa94758950fd55f8e"
}
```

`slice` values already used: `full` (implied by RLB/CEI — every extracted row
of the named mills), `representative` (ACM), `r801` (EVH), `leftover` (NTP).
Pick one. Do not invent `partial` / `slim` / `min`.

Filename: `CATALOG.json`, not `catalog.json`. WSR and EWR used lowercase and
that is one more inconsistency babysitters should not perpetuate.

## 7. Copy-paste: compact JSONL writer

```python
import json
from pathlib import Path


def write_pairs_jsonl(path: Path, rows: list[dict]) -> str:
    """One record per line. No pretty indent. Trailing newline. No CR."""
    lines = [
        json.dumps(row, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        for row in rows
    ]
    text = "\n".join(lines) + "\n"
    path.write_text(text, encoding="utf-8")
    return text
```

`separators=(",", ":")` is correct **per record**. It is forbidden for the
header and forbidden for a whole-catalog dump.

RLB landed records look like this (one line, fields intact):

```json
{"source_path":"experiments/rlb_leftover3_mill.py","success":{"slug":"shopify-gql-leftover-cost","api":"Shopify GraphQL","header":"X-Shopify-GraphQL-Cost-Left","naive":"X-Shopify-Shop-Api-Call-Limit","expected_value":842,"naive_value":"39/40","module":"shplef","docs":["https://shopify.dev/docs/api/usage/rate-limits","https://shopify.dev/docs/api/admin-graphql"],"domain":"shopify-gql-leftover-cost-vs-rest-remaining","stack":"Shopify GraphQL leftover cost","coverage":80},"handoff":{"slug":"shopify-rest-leftover-handoff","api":"Shopify REST","leftover_kind":"rest-remaining-leftover","naive":"X-Shopify-Shop-Api-Call-Limit","module":"shprest","docs":["https://shopify.dev/docs/api/admin-rest/usage/rate-limits","https://shopify.dev/docs/api/admin-rest"],"domain":"shopify-rest-leftover-remaining-vs-naive-rps","stack":"Shopify REST leftover remaining","ticket":"SH-LF-3","coverage":80},"round":82}
```

CEI landed the same idea for a full `_ok` / `_bad` plant. Wide lines are
fine. GitHub charges 1. Reviewers `jq` a line. `sha256` is over the file
bytes including the final newline.

Do not also commit a pretty `rows` array of the same objects. ACM's first
head committed **both** a 919-line pretty source catalog **and** a 1052-line
JSONL; the babysitter deleted both.

## 8. Copy-paste: compactness test

From `tests/test_rlb_catalog.py` `test_pairs_jsonl_stays_compact`. Every
rank-1 family needs this. A future pretty-reformat of the JSONL is a
regression against the cap.

```python
def test_pairs_jsonl_stays_compact(self):
    text = PAIRS_JSONL.read_text(encoding="utf-8")
    lines = text.splitlines()
    self.assertEqual(len(lines), EXPECTED_N)
    self.assertTrue(text.endswith("\n"))
    self.assertNotIn("\r", text)
    for line in lines:
        self.assertFalse(line.startswith((" ", "\t")))
        json.loads(line)
```

Also pin:

- `n_rows_committed == n_rows_extracted` for rank 1
- `n_rows_committed < n_rows_extracted` **and** `extract.full_row_count`
  equals the extract for rank 2 / last resort
- source blob sha1 + content sha256 for every pinned mill
- no `exec` / `eval` / `compile` in the package
- `git ls-files` contains no `<family>-mill*.py`, `<family>-loop*.py`,
  `_gen_<family>_*.py`, `<family>-plants*.py`

## 9. Copy-paste: rank-2 hybrid dumper

When the header stays pretty but the first-slice identities must not expand
to eight lines each, copy EVH — do not pretty-print the `pairs` array.

```python
PAIR_IDENTITY_KEYS = (
    "fail_domain",
    "fail_plant",
    "fail_slug",
    "kind",
    "success_domain",
    "success_plant",
    "success_slug",
)


def compact_pair_identity(pair: dict) -> dict:
    """Identity only. Drop leftover/first/fix metric bodies (EVH #278)."""
    return {key: pair[key] for key in PAIR_IDENTITY_KEYS}


def dumps_catalog(document: dict) -> str:
    return _encode(document, 0, key=None) + "\n"


def _encode(value, level: int, key: str | None) -> str:
    import json

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

EVH's slim compared `19c2b9d...75ecf45` was `+126 / -1890` on
`pipelines/evh/CATALOG.json`. That is the cost of pretty metric bodies:
`leftover_ok`, `leftover_bad`, `first_ok`, `first_bad`, `fix_ok`, `fix_bad`
turned 126 identities into ~1,800 extra lines. Drop bodies. Keep slugs.

GOR and MDB pretty-printed those identity objects (≈8 lines each). That
worked because they committed 27 and 37 identities, not 126. If the first
slice is > 40 pairs, use the EVH dumper.

## 10. Copy-paste: vendor refusal

Every family package fails closed on mill / loop / plant-gen destinations.
The scripts stay on `origin/legacy-mill-lane`. Tests re-extract with
`git show` when that ref is present.

```python
import fnmatch
from pathlib import Path

VENDOR_GLOBS = (
    "<family>-mill*.py",
    "<family>-loop*.py",
    "<family>*mill*.py",
    "_gen_<family>_*.py",
    "<family>-plants*.py",
    "mill_plants*.py",
)


def refuse_vendor_paths(path: Path) -> None:
    name = path.name
    if any(fnmatch.fnmatch(name, pat) for pat in VENDOR_GLOBS):
        raise ValueError(f"refusing to vendor mill/loop/plant-gen path: {path}")
```

Observed refusals (copy the family's set, do not invent a weaker one):

| family | refused destinations |
|---|---|
| rlb | no generation CLI; package is `{__init__,catalog}.py` only; tests ban `subprocess`, `round_txn`, `outputs/raw` |
| acm | `acm-mill*.py`; `acm-loop-*.py` |
| evh | `evh-loop*.py`; `_gen_evh_*.py`; `mill_plants*.py`; `eval_harness_*` |
| wsr | `wsr*mill*.py`; `wsr-plants-r73.py`; QBP constructors; hopper helpers |
| gor | `gor-mill*.py`; `gor-loop*.py`; `_gen_gor_*.py` |
| cei | `*mill*.py`; hop loop and leftover leftover leftover mills stay on the legacy lane |
| mdb | `mdb-mill*.py`; loops and the plant-gen stay pinned as blobs, not files |

Historical loop-to-mill companions stay AST-true in `sources.py` and are
**not** vendored: `mdb-loop-r1084` loads `mdb-mill-r1148.py`;
`gor-loop-r1196` loads `gor-mill-r1214.py`; four GOR plant-gens load
`gor-mill-r1460.py`. Pin the blob. Do not copy the file.

Tiny-source test fixtures may be a **hand-written** pair/plant snippet
(`acm-pairs-r1.py`, `_gen_acm_plants_r2.py`). They may not be a dump of a
legacy loop.

## 11. Copy-paste: package skeletons

Two shapes shipped. Do not invent a third on the first PR.

**Generate library** (CEI, WSR, ACM) — five modules, catalog beside or under
`config/<family>/`:

```text
pipelines/<family>/__init__.py
pipelines/<family>/_contract.py    # prefix home, vendor refusal, quota, steps
pipelines/<family>/catalog.py      # load header + JSONL; ast.parse extract
pipelines/<family>/generate.py     # 16-step success + 17-step handoff; refuses outputs/raw/
pipelines/<family>/cli.py          # catalog | catalog-check | generate
config/<family>/CATALOG.json
config/<family>/pairs.jsonl        # or plants.jsonl
tests/test_<family>.py
tests/fixtures/<family>/CATALOG.json
tests/fixtures/<family>/plants.jsonl   # one-row fixture, not a dump
```

**Extract skeleton** (EVH, GOR, MDB) — no publisher on the first PR:

```text
pipelines/<family>/__init__.py
pipelines/<family>/catalog.py
pipelines/<family>/catalog_ast.py
pipelines/<family>/catalog_extract.py
pipelines/<family>/identity.py
pipelines/<family>/sources.py
pipelines/<family>/vocabulary.py
pipelines/<family>/CATALOG.json
tests/test_<family>.py
```

RLB is the catalog-only minimum: `{__init__,catalog}.py` + header + JSONL.
That is why it finished at 668 additions.

ACM's first head used a 9-module `pipelines/contract_drift/`
(`catalog_ast`, `catalog_extract`, `check`, `identity`, `plants`, …). The
slim collapsed it to the sanctioned five-module `pipelines/acm/`. New
families start at five (or the extract skeleton), not nine.

`generate` writes a **new** destination and refuses one that exists. It
refuses any path that names or aliases `outputs/raw/`. It does not import
`round_txn`. It does not stamp `grok-4.6` as a live generator identity
beyond the catalog pin. Hosted-frontier registry rows stay
`research_only` / `blocked`.

## 12. Copy-paste: PR body (line-budget section)

Every mill PR body needs this section **before** CI starts. RLB's is the
model; ACM's owner comment is the babysitter version of the same text.

```markdown
## Line budget

GitHub additions vs `main` are **<M>** (limit 2500). Files: **<N>** (limit 20).

Encoding: header + compact JSONL | first-slice identities + counts | representative slice
Catalog files: `config/<family>/CATALOG.json` (<h> lines) + `<pairs|plants>.jsonl` (<n> lines)

Extracted: <n_rows_extracted> pairs / <n_source_files> source files @ <preserve_commit>
Committed: <n_rows_committed>
Deferred: <named mills / dests / leftover leftover leftover scripts / r73 plants>

No second PR. No rebase. No vendored `*mill*.py` / `*loop*.py` / `_gen_*`.
```

Operator return already used (keep it):

```text
sha: <head>
branch: mill/<family>
files: <N>
additions: <M>
row_count: <committed> / <extracted>
```

## 13. Anti-patterns (with the PRs that paid for them)

### 13.1 Pretty-print the pair catalog

**What it looks like.** One `CATALOG.json` whose `pairs` array is
pretty-printed full plants: goal, plan, src_body, test_body, docs, coverage,
first_old / first_new / fix_new, …

**Why it blows the cap.** WSR: 16 pairs → 1059 catalog lines → **2497**
additions (3 under). EWR #257: 16 leftover-event pairs → 1043 catalog lines
→ **2639**. CST #256: 1026 pair rows + 48 plants pretty-printed →
**20751** catalog lines → **21566**. RLB's first commit: 64 pretty pairs →
2231-line catalog, over the cap before the loader even finished growing.

**Fix.** Rank 1 JSONL. WSR's 16 leftover3 pairs would have been 16 JSONL
lines plus a 30-line header (≈ 46 catalog lines, ~1000 lines of slack)
instead of 1059.

### 13.2 Minify-JSON gaming

**What it looks like.**

```python
path.write_text(json.dumps(document, separators=(",", ":")))  # one line
```

or a pretty header whose `pairs` value is a single monster line of 126
objects.

**Why it is a fail.** GitHub's cap counts newlines. One-line catalogs report
`+1` and are unreviewable. Codex/Qodana/human review cannot leave an inline
comment on a pair. `git blame` and `git diff` become opaque. The EVH slim
message is the tell: "write **one identity per line** so #278 stays under
2,500 added" — compact **records**, not a minified document.

**The test above rejects this** if you also assert `len(lines) == N` for N
records. A 1-line file of 64 records fails `len(lines) == 64`.

### 13.3 Vendoring loops

**What it looks like.**

- `git add experiments/<family>-loop-rNN.py` or `acm-loop-r1.py` as a
  fixture
- copying `_gen_<family>_plants_rNN.py` into `tests/fixtures/`
- committing `mill_plants_w.py` so the extractor does not need `git show`
- a "tiny-source" tree that is a trimmed dump of the preserve commit

**Why it is a fail.** The mill burst rule is parse-input-only. ACM's second
commit (`7dccd5c`) exists only because the first head vendored
`acm-loop-r1.py`. Loops load mills (`mdb-loop-r1084` → `mdb-mill-r1148.py`);
vendoring the loop pulls the mill next. That is the vendoring loop.

**Fix.** `git show origin/legacy-mill-lane:experiments/<file>` in tests when
the ref exists. Skip the live re-extract when it does not. Pin blob sha1 +
sha256 in `sources.py`. Refuse the globs in §10.

### 13.4 Both pretty CATALOG and JSONL of the same extract

ACM head 1: `catalogs/api-contract-migration-v1/CATALOG.json` (919) **plus**
`rows.jsonl` (1052) **plus** a 9-module package. The cap does not care that
the JSONL was already compact. Two copies of 1052 pairs is still 1052 + 919
catalog lines.

**Fix.** Header **or** JSONL for the row set, never both encodings of the
same bodies. The header may list mills and hashes. The JSONL holds rows.

### 13.5 A second PR to slim

ACM, RLB, and EVH all say "no second PR". The owner comment on #255 is the
policy in one paragraph:

> Slimmed this same head under the merge cap. Forward commit `c90b2da` on
> `mill/acm` (no rebase, no second PR).

A follow-up slice **after the family lands** is a new PR. A slim of the
still-open family PR is a commit on that head.

### 13.6 Plants as Python modules

#251 (`mill/db`) split 88 plants into `plants_01.py` / `plants_02.py` /
`plants_03.py` (564 + 564 + 529) and still reported **2585** additions / 16
files. That is a catalog the cap cannot see as data. Put plants in JSONL.

### 13.7 Opening generate + extract + full pretty catalog on PR-a

EVH/GOR/MDB kept generate off PR-a and still spent 1885–2177 lines on the
extract skeleton. Adding `generate.py` + `cli.py` on top of a pretty catalog
is how WSR hit 2497 with 16 pairs. If you need generate on PR-a, the catalog
**must** be rank 1 JSONL (CEI: 2193 with generate + 39 JSONL plants) or you
must drop generate until the follow-up.

### 13.8 Rebase, amend, or force-push to hide the over-cap commit

The land-stacked-prs contract is merge-only. RLB/ACM/EVH slimmed with
forward commits. The over-cap commit staying in history is acceptable; the
compare vs `main` is what the cap reads.

### 13.9 Inventing rows to fill a representative slice

ACM's eight rows are real extracts (`g46-w2` … `r4230`) with source paths
and sha256s. A slice of made-up "examples" is not a catalog. The loader
must re-extract those eight from the preserve commit and match.

### 13.10 Treating `leftover` in an id as mill mix

`docs/leftover-mill-quarantine.md`: leftover-in-id is the scenario mechanic,
not the mill test. Catalog slugs will contain `leftover`. Do not strip them
to look cleaner. Do not quarantine on the token.

## 14. Budget arithmetic (copy and substitute)

```text
additions ≈ package_py + tests + header + payload_lines

RLB  668  = 31+380 (__init__,catalog) + 146 tests + 47 header + 64 jsonl
CEI 2193  = 15+222+702+175+642 (five-module + generate) + 353 tests
            + 26 header + 39 jsonl + 18+1 fixtures
EVH 2177  = 33+154+246+653+40+105+47 (extract skeleton) + 398 tests + 501 catalog
GOR 1885  = 32+116+173+334+40+261+84 + 354 tests + 491 catalog
MDB 1957  = 32+112+155+373+40+314+59 + 319 tests + 553 catalog
WSR 2497  = 33+161+544+109+397 + 194 tests + 1059 pretty catalog
ACM 1341  = 45+81+270+57+437 + 125 tests + 219 slice + 47+60 fixtures
```

Package + tests alone are 1200–1800 for an extract skeleton and 1600–2200
for a generate library. That leaves **300–1300 lines** for the catalog.
Pretty pairs consume that in 8–20 rows. JSONL consumes it in hundreds.

## 15. Compare commands used for this playbook

```bash
# PR metadata
gh pr view 252 --repo rmems/synthetic-factory \
  --json number,title,state,mergedAt,additions,deletions,changedFiles,baseRefOid,headRefOid,mergeCommit,files,commits,body

# 3-dot compare (the cap)
gh api repos/rmems/synthetic-factory/compare/5044954ffa086209bdc46eb03f2c451b87439965...aeea95275b2bc7e8c5ca39b391568dc64e2189ab

# Slim commit vs its parent (RLB / ACM / EVH)
gh api repos/rmems/synthetic-factory/compare/1f95fa78bad725047d4e58c40b70b11518a22955...aeea95275b2bc7e8c5ca39b391568dc64e2189ab
gh api repos/rmems/synthetic-factory/compare/186e094e913a137250cdfc4907dc9c0aa7bdef72...c90b2da52f5096f799ad23e01d13cec7b4d53bc1
gh api repos/rmems/synthetic-factory/compare/19c2b9d4d45de81c566b11391ce3b175b75f8295...75ecf45e1e40bc5fa9e7fd2eb8055c7cf5bbcfb5

# Raw catalog bytes at the merged head
gh api "repos/rmems/synthetic-factory/contents/config/rlb/pairs.jsonl?ref=aeea95275b2bc7e8c5ca39b391568dc64e2189ab" \
  -H "Accept: application/vnd.github.raw"
```

Compare file-sums (added lines only):

| PR | compare files (added) |
|---|---|
| #252 | `CATALOG.json` +47, `pairs.jsonl` +64, `__init__.py` +31, `catalog.py` +380, `test_rlb_catalog.py` +146 |
| #255 | `CATALOG.json` +219, five `pipelines/acm/` modules +890, two tiny-source fixtures +107, `test_contract_drift.py` +125 |
| #278 | `CATALOG.json` +501, eight package/test files +1676 |
| #272 | `catalog.json` +1059, five `pipelines/wsr/` +1244, `test_wsr.py` +194 |
| #265 | `CATALOG.json` +491, eight package/test files +1394 |
| #270 | `CATALOG.json` +26, `plants.jsonl` +39, five `pipelines/cei/` +1756, fixtures +19, `test_cei.py` +353 |
| #268 | `CATALOG.json` +553, eight package/test files +1404 |

#252 compare was `diverged ahead=4 behind=17` because main moved during the
burst. The cap still reads the compare file-sum, not `ahead_by`.

## 16. Related encodings (not the seven, but the same cap)

These landed in the same burst and confirm the ranking. They are not
permission to add families.

| PR | family | additions | encoding | note |
|---|---|---|---|---|
| #274 | amc | 890 | rank 1/2 hybrid: header 231 + `pairs.jsonl` 24 | header says `n_pair_rows_extracted: 1401`, `n_pair_rows_committed: 24`, remaining compact rows deferred |
| #273 | lef | 1783 | header 126 + `rows.jsonl` 48 | 48 committed of a larger table extract |
| #271 | ntp | 2176 | counts-only header, 12 lines | `n_pair_rows: 1625`, `slice: leftover` — bodies entirely deferred |
| #248 | gql | 1868 | header 68 + `plants.jsonl` 102 | rank 1, generate library |
| #245 | rag | 1696 | header 30 + `plants.jsonl` 16 | rank 1 |
| #244 | flk | 1698 | header 54 + `plants.jsonl` 80 | rank 1 |
| #242 | msd | 1981 | header 33 + `plants.jsonl` 92 | rank 1 |
| #257 | ewr | **2639** | pretty `config/ewr/catalog.json` 1043 | rank 3 overshoot; same shape as WSR |
| #256 | cst | **21566** | pretty `pipelines/cst/CATALOG.json` 20751 | full 1026-pair dump; the cap did not hold |
| #251 | db | **2585** | plants as Python modules | see §13.6 |

If CST or EWR is your template, stop and use RLB/CEI.

## 17. What a miller does, in order

1. Confirm the family already has a `REVIEWED_MILL_PREFIX_HOMES` row. This
   playbook does not add one.
2. `git fetch origin legacy-mill-lane` and locate the preserve commit
   ("Preserve the \<family\> mill family as generated").
3. AST-extract into a temp tree. Do not `exec`. Count rows.
4. Run the decision tree in §3. Pick rank 1 or 2 **before** creating files.
5. Write header + JSONL (or header + counts + compact identities).
6. Write the sanctioned package only. Refuse vendor globs.
7. Write the compactness test and the `git ls-files` vendor test.
8. Run `git diff --stat origin/main...HEAD`. If M > 2300, drop to rank 2 or
   shrink the first slice **now**, on this head.
9. Fill the PR body line-budget section with extracted / committed /
   deferred. Name the deferred mills.
10. Do not merge from the miller PR. Do not close it. Do not open a second
    PR for the slim.

Babysitters landing the burst then only retarget, wait for checks, and
squash. They should not have to invent an encoding.

## 18. What this playbook does not authorize

- A new mill family, prefix, or `REVIEWED_MILL_PREFIX_HOMES` row
- Vendoring or executing leftover mills
- A `round_txn` / `write_round` publisher on PR-a
- Writes under `outputs/raw/`
- Changing a hosted-frontier row off `research_only` / `blocked`
- A follow-up slice opened **before** the family's first PR lands
- Minifying JSON to beat the cap
- Pretty-printing full pair bodies because "the catalog is the source of truth"
  — the source of truth is the preserve-commit blob; the catalog is the
  extracted, pin-verified projection that fits the cap
