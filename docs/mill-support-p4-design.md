# P4 mill-support design (do not land in this PR)

Status: **design only**. Do not implement `pipelines/mill_support` until
after a main reset. Budget: **≤500 lines** for the new package (tests extra).
Surveyed at `main` `fef9fef` (post `#276` SSR land).

This document is the P4 plan. It does not change runtime code.

## 1. Why this exists

The mill burst is copying the same four seams into every leftover-extract
family:

1. AST literal helpers (`assignment_of`, `literal_value`, path joins)
2. `refuse_vendor_paths` (fail-closed on leftover mill scripts)
3. Compact catalog IO (`sha256_bytes`, `dumps_catalog`, `write_catalog_document`)
4. `bind_import_twin` (or a fork of it)

Landed extract families already carry near-copies:
`search`, `lef`, `ssr`, `evh`, `gor`, `iac`, `mdb`, `ntp`, `cst`.
`acm` inlines the AST pair in `generate.py`. `hopper` and `code_repair`
use `_contract.bind_import_twin` from
`oracle_grounded.import_twins`. `db` has a third copy of the binder.

Eighteen open mill PRs (`azr`, `dbc`, `dbm`, `dpr`, `irc`, `kcl`, `lhc`,
`lrd`, `mac`, `obs`, `pkg`, `qbp`, `sbox`, `tup`, `csv`, `maos`, `ttf`,
`nelb`, …) will copy the same helpers again unless a shared module exists
**before** those PRs rebase.

P4 lands **only** the shared module. It does not migrate already-landed
families (that collides with every in-flight mill PR). Remaining families
rebase onto it. Already-landed copies are a later cleanup.

## 2. Proposed files

Package name is `mill_support`, not `mill` (that is a landed family) and
not `leftover_mill` (that is the kind-mix auditor).

```text
pipelines/mill_support/
  __init__.py          ~40   re-exports + bind_import_twin(__name__)
  twins.py             ~50   re-export oracle_grounded.import_twins (no new binder)
  ast_literals.py     ~220   union of catalog_ast helpers; ast.parse only
  vendor.py            ~70   parameterized refuse_vendor_paths
  catalog_io.py        ~90   sha256, dumps, single-file write, catalog path
```

Hard cap: **sum of those five files ≤ 500 lines**. If the union of
`literal_value` extras (f-string, `frozenset()`, `/` path join) blows the
cap, drop `frozenset` / path-join into optional kwargs rather than a sixth
file.

Do **not** add `pipelines/mill_support.py` as a top-level sibling. That
would require `_PACKAGE_SIBLING_NAMES` in `pipelines/__init__.py` (shared
hot file). The package uses `bind_import_twin` the same way
`hopper` / `acm` / `code_repair` do, so `__init__.py` stays untouched.

Do **not** put `load_catalog`, `extract_mill_catalog`, plant dataclasses,
or finding-code tables in this package.

## 3. Public API sketch

```python
# mill_support (package)
from mill_support.twins import bind_import_twin, import_twin_of
from mill_support.ast_literals import (
    UNSET,
    assignment_of,
    assignment_names,
    tuple_assignment_names,
    literal_value,          # Constant, Name, ±number, tuple/list/set/dict,
                            # str Add, JoinedStr of str|int, frozenset(...)
    module_constants,       # walk Module.body via assignment_of + literal_value
    module_docstring,
    call_name,
    joined_path_constant,   # ROOT / "experiments" / "x.py" -> experiments/x.py
    extract_joined_path_assignment,
)
from mill_support.vendor import (
    refuse_vendor_paths,    # SystemExit("refusing to vendor {name}")
    prefixes_vendor,        # name.endswith(".py") and name.startswith(prefixes)
)
from mill_support.catalog_io import (
    sha256_bytes,
    mill_id_for_path,       # Path(path).stem
    catalog_json_path,      # (package_dir or caller_dir) / filename
    dumps_catalog,          # json.dumps(..., ensure_ascii=True, indent=2,
                            #             sort_keys=True) + "\n"
    write_catalog_document, # write dumps_catalog(document) to path
)

# Typical remaining-family identity.py (stays family-local except the loop):
from mill_support.vendor import refuse_vendor_paths, prefixes_vendor
from .vocabulary import VENDOR_PREFIXES

def is_vendor_filename(name: str) -> bool:
    return prefixes_vendor(name, VENDOR_PREFIXES)  # plus family extras

def refuse_vendor(paths):
    refuse_vendor_paths(paths, is_vendor_filename)
```

`refuse_vendor_paths(paths, is_vendor)` takes the **predicate**. The
shared function is only the loop + `SystemExit`. Prefixes, leftover
needles, and `SLUGS_FILENAME` stay in the family.

`literal_value` is the **superset** used by `lef` / `ssr` / `search`.
Narrower copies (`search` has no f-string / `frozenset`) still call the
same function; extra node types return `UNSET` unless they are the
documented safe set. Nothing `exec`s / `eval`s / `compile`s.

`bind_import_twin` is a **re-export** of
`oracle_grounded.import_twins.bind_import_twin`. P4 does not move or edit
that module. `_contract` files that already import it keep working.
Remaining families that want twins import `mill_support.twins` so they
do not grow a `db/import_twins.py` fork.

`dumps_catalog` is the majority spelling (`ensure_ascii=True`, indent 2,
`sort_keys`, trailing newline). `acm` (`ensure_ascii=False`), `evh`
(custom pair-line encoder), and `ntp` (header JSON + two JSONL files)
keep their own writers.

## 4. What MUST stay family-local

These look shared and must not enter `mill_support`.

### 4.1 leftover_mill auditor (`pipelines/leftover_mill.py`)

This is not a generation mill. It is the issue `#43` / `#30` read-only
auditor: frozen `PUBLISHED_FACTORY_MIX` (30 IDs), Hub name map,
`KIND_MIX_QUARANTINE` (12 raw episode identities inside
`code-review-preference-factory`), and `scan_jsonl_kind_mix`.

It uses the old `__package__` sibling prelude, not `bind_import_twin`.
Census, `curate_preferences`, `publish_grok46_hub`, and card tests bind
to its exact bytes.

Keep every public name here:

| helper | line |
|---|---|
| `expected_factory_mix_ids` | `leftover_mill.py:101` |
| `render_factory_mix_card_section` | `leftover_mill.py:111` |
| `audit_run` | `leftover_mill.py:139` |
| `destination_kind` | `leftover_mill.py:343` |
| `is_preference_destination` | `leftover_mill.py:348` |
| `quarantined_ids` | `leftover_mill.py:353` |
| `quarantine_provenance` | `leftover_mill.py:361` |
| `record_id` | `leftover_mill.py:366` |
| `kind_mix_kind` | `leftover_mill.py:379` |
| `find_kind_mix` | `leftover_mill.py:393` |
| `scan_jsonl_kind_mix` | `leftover_mill.py:434` |
| `unacknowledged` | `leftover_mill.py:496` |

`record_id` also exists at `mill/vocabulary.py:118` and
`srl/generate.py:39`. Those are different contracts. Do not unify them
with the auditor.

### 4.2 mill detection siblings

`mill_family.py`, `mill_signals.py`, `mill_locations.py`,
`mill_evidence.py`, `mill_resolution.py`, `mill_ownership.py`,
`mill_findings.py`, `mill_reviewed_vocabulary.py`, `compose_mill.py`,
`training_audit_mill.py`. Ownership resolution for published runs.
Not catalog extract. Do not import these from mill generation packages
except the existing `REVIEWED_MILL_PREFIX_HOMES[FAMILY]` pin
(`acm/_contract.py:43`).

### 4.3 Family identity and vendor predicates

`FAMILY`, `FACTORY`, `GENERATOR`, `VENDOR_PREFIXES`, `FORBIDDEN_MILL_GLOBS`,
`SOURCE_COMMIT` / `PRESERVE_COMMIT`, catalog schema ids, slice ids,
`is_vendor_filename`.

Search is the proof that the predicate is not one prefix list:
`search/identity.py:12` also matches `sir-mill-leftover*`,
`sir-loop-leftover*`, and `sir_r*_leftover*_mill.py`.
`lef/identity.py:15` treats `SLUGS_FILENAME` as vendor.
`ffpc/_contract.py:102` uses finding codes + name needles, not
`SystemExit`.
`acm/_contract.py:51` is `VENDOR_PREFIX + ".py"` only.

### 4.4 Family AST extractors

`extract_mill_catalog`, `extract_plant_catalog`, `extract_tree`,
`extract_companion_path`, `extract_source_path`, `extract_named_mill_path`,
`extract_replace_mill_target`, `extract_chain_bounds`,
`compact_pair_identity`, `ctor_identity`, `const_keyword`,
`spec_from_file_name`, `plants_from_source`, `pair_fields_for_arity`.

These encode leftover3 / leftover-lll / plant / `S` / `TAILS` / STEM
shapes. Putting any one family's walker in the shared module freezes the
wrong schema for the next family.

### 4.5 Family catalog load / document / summary

`load_catalog` (28 copies) binds schema + factory + source pins and
builds family dataclasses (`SearchCatalog`, hopper `Catalog`, ACM
`dict` + `rows_sha256`, code_repair sealed catalog).
`catalog_document` / `mill_summary` field sets differ
(`lef` 21 lines vs the 13-line majority).
`catalog_first_from_name` has four regex variants.

Hopper `plants.py` (`load_catalog` at `:243`) is a different compact
shape: `CATALOG.json` + `plants.jsonl` + `plants_sha256`, 30-field
plants, uniqueness on slug/mod/domain/ticket. That loader stays on
hopper. Later hopper-style families (`qbp`, `kcl`) already import
hopper's public API (`_p`, `START`, `PAIRS`, `build_success` /
`build_fail`) — those stay on hopper.

### 4.6 hopper replay

`episode.py`: `assert_clean`, `build_success`, `build_fail`,
`build_pair`, `validate_pair`, `dumps_episode`, `emit_stage`,
`factory_dir`. Reward constants, 16/17-step envelopes, banned
reasoning keys. Not extract support.

### 4.7 code_repair catalog and `_contract`

`code_repair` is the procedural training-candidate mill. Its catalog is
source-policy sealed (`source_policy.py`, trusted replay, executor,
publication). `code_repair/_contract.py` is the import-twin + exact-JSON
+ envelope facade, not leftover-mill extract. Do not rebase it onto
`mill_support.catalog_io`. It may *import* `bind_import_twin` from
`mill_support.twins` in a later cleanup; P4 must not edit
`code_repair/`.

### 4.8 `_contract` finding tables and Refusal classes

`HopperRefusal`, `FINDING_*` codes, `refuse` / `refuse_when` /
`refuse_first`, `load_strict_json` wrappers, `repo_root`. Each family's
coded refusal set is the review contract. `load_strict_json` in
`tag_jsonutil.py:78` has no `ExactJSONFloat`; the `_contract` copies add
it. Do not replace either from mill_support.

### 4.9 CLI / generate / notes / sources tables

`build_parser`, `run`, `main`, `catalog_sources`, `MILL_SOURCES` blob
pins, `notes_md`, plant constructors other than hopper's `_p` export.

## 5. Duplicated helpers across `pipelines/*` (file:line)

Inventoried by AST `FunctionDef` name. A name listed here appears in
more than one file under `pipelines/`. Clustered by whether P4 absorbs
it.

### 5.1 Absorb into mill_support (shared body, or shared loop + local predicate)

#### `assignment_of` — 9 defs, **1 body** (absorb)

- `pipelines/acm/generate.py:56`
- `pipelines/evh/catalog_ast.py:21`
- `pipelines/gor/catalog_ast.py:18`
- `pipelines/iac/catalog_ast.py:16`
- `pipelines/lef/catalog_ast.py:16`
- `pipelines/mdb/catalog_ast.py:16`
- `pipelines/ntp/catalog_ast.py:21`
- `pipelines/search/catalog_ast.py:16`
- `pipelines/ssr/catalog_ast.py:17`

#### `assignment_names` — 6 defs, 2 bodies (absorb majority; `lef` wraps)

- `pipelines/gor/catalog_ast.py:30`
- `pipelines/iac/catalog_ast.py:28`
- `pipelines/lef/catalog_ast.py:28` (same logic, extra line wrap)
- `pipelines/ntp/catalog_ast.py:33`
- `pipelines/search/catalog_ast.py:28`
- `pipelines/ssr/catalog_ast.py:29`

#### `call_name` — 7 defs, **1 body** (absorb)

- `pipelines/evh/catalog_ast.py:33`
- `pipelines/gor/catalog_ast.py:106`
- `pipelines/iac/catalog_ast.py:104`
- `pipelines/lef/catalog_ast.py:133`
- `pipelines/mdb/catalog_ast.py:96`
- `pipelines/ntp/catalog_ast.py:109`
- `pipelines/ssr/catalog_ast.py:105`

#### `extract_joined_path_assignment` — 5 defs, **1 body** (absorb)

- `pipelines/evh/catalog_ast.py:233`
- `pipelines/gor/catalog_ast.py:167`
- `pipelines/iac/catalog_ast.py:144`
- `pipelines/lef/catalog_ast.py:157`
- `pipelines/ssr/catalog_ast.py:166`

#### `joined_path_constant` — 7 defs, docstring-only variants (absorb)

- `pipelines/evh/catalog_ast.py:215`
- `pipelines/gor/catalog_ast.py:149`
- `pipelines/iac/catalog_ast.py:126`
- `pipelines/lef/catalog_ast.py:139`
- `pipelines/mdb/catalog_ast.py:116`
- `pipelines/ntp/catalog_ast.py:147`
- `pipelines/ssr/catalog_ast.py:148`

#### `literal_value` — 8 defs, family supersets (absorb **lef/ssr** superset)

- `pipelines/acm/generate.py:68` (dispatch table; no containers)
- `pipelines/gor/catalog_ast.py:38`
- `pipelines/iac/catalog_ast.py:36`
- `pipelines/lef/catalog_ast.py:54` (f-string + `frozenset` + str add)
- `pipelines/mdb/catalog_ast.py:28`
- `pipelines/ntp/catalog_ast.py:41`
- `pipelines/search/catalog_ast.py:36` (narrow: no f-string / call)
- `pipelines/ssr/catalog_ast.py:37` (f-string + str add)

Private helpers of those copies (do not export; fold into `literal_value`):

| helper | locations |
|---|---|
| `_sequence` | `evh/catalog_ast.py:80`, `gor:68`, `iac:66`, `lef:95`, `mdb:58`, `ntp:71`, `search:59`, `ssr:67` |
| `_mapping` | `evh/catalog_ast.py:90`, `gor:78`, `iac:76`, `lef:105`, `mdb:68`, `ntp:81`, `search:69`, `ssr:77` (plus unrelated `amc/catalog.py:173`, `rlb/catalog.py:123`) |
| `_joined_string` | `evh/catalog_ast.py:103`, `gor:91`, `iac:89`, `lef:118`, `mdb:81`, `ntp:94`, `ssr:90` |
| `_safe_call` | `lef/catalog_ast.py:86` (`frozenset` only), `evh/catalog_ast.py:185` (evh-local; **stay**) |
| `_module_constants` | `evh/catalog_extract.py:129`, `gor:101`, `iac:95`, `mdb:103`, `ntp:107`, `search:93`, `ssr:112` |

#### `refuse_vendor_paths` — 11 defs (absorb **loop**; keep predicate local)

- `pipelines/acm/_contract.py:51`
- `pipelines/amc/catalog.py:164`
- `pipelines/evh/identity.py:22`
- `pipelines/ffpc/_contract.py:102` (**stay**: `refuse_when` + finding code)
- `pipelines/gor/identity.py:22`
- `pipelines/iac/identity.py:22`
- `pipelines/lef/identity.py:22`
- `pipelines/mdb/identity.py:22`
- `pipelines/ntp/identity.py:22`
- `pipelines/search/identity.py:26`
- `pipelines/ssr/identity.py:20`

#### `forbidden_globs` — 8 defs, **1 body** (absorb as one-liner or skip)

- `pipelines/evh/identity.py:31`
- `pipelines/gor/identity.py:31`
- `pipelines/iac/identity.py:31`
- `pipelines/lef/identity.py:31`
- `pipelines/mdb/identity.py:31`
- `pipelines/ntp/identity.py:31`
- `pipelines/search/identity.py:35`
- `pipelines/ssr/identity.py:29`

Skip absorbing this if the 500-line budget is tight: it is
`return FORBIDDEN_MILL_GLOBS`.

#### `sha256_bytes` — 18 defs (absorb the mill-extract copies)

- `pipelines/cei/catalog.py:166`
- `pipelines/cst/catalog_extract.py:47`
- `pipelines/curate_identity_checks.py:302` (**stay**: identity lane)
- `pipelines/evh/catalog_extract.py:66`
- `pipelines/ffd/catalog.py:73`
- `pipelines/flk/catalog.py:139`
- `pipelines/gor/catalog_extract.py:50`
- `pipelines/gql/catalog.py:171`
- `pipelines/iac/catalog_extract.py:46`
- `pipelines/lef/catalog_extract.py:49`
- `pipelines/mdb/catalog_extract.py:54`
- `pipelines/mill/catalog_load.py:24`
- `pipelines/msd/catalog.py:187`
- `pipelines/ntp/catalog_extract.py:58`
- `pipelines/rag/catalog.py:119`
- `pipelines/saf/catalog.py:122`
- `pipelines/search/catalog_extract.py:33`
- `pipelines/ssr/catalog_extract.py:53`

#### `mill_id_for_path` — 9 defs, **1 body** (absorb)

- `pipelines/cst/catalog_extract.py:51`
- `pipelines/evh/catalog_extract.py:70`
- `pipelines/gor/catalog_extract.py:54`
- `pipelines/iac/catalog_extract.py:50`
- `pipelines/lef/catalog_extract.py:53`
- `pipelines/mdb/catalog_extract.py:58`
- `pipelines/ntp/catalog_extract.py:62`
- `pipelines/search/catalog_extract.py:37`
- `pipelines/ssr/catalog_extract.py:57`

#### `catalog_json_path` — 9 defs, **1 body** (absorb)

- `pipelines/cst/catalog_extract.py:233`
- `pipelines/evh/catalog_extract.py:645`
- `pipelines/gor/catalog_extract.py:322`
- `pipelines/iac/catalog_extract.py:474`
- `pipelines/lef/catalog_extract.py:475`
- `pipelines/mdb/catalog_extract.py:361`
- `pipelines/ntp/catalog_extract.py:340`
- `pipelines/search/catalog_extract.py:202`
- `pipelines/ssr/catalog_extract.py:402`

#### `dumps_catalog` — 10 defs, 4 bodies (absorb **majority** `ensure_ascii=True`)

- Majority (2-line): `cst:229`, `gor:318`, `iac:470`, `lef:471`, `mdb:357`, `search:198`, `ssr:398`
- `pipelines/acm/catalog.py:94` (**stay**: `ensure_ascii=False`)
- `pipelines/evh/catalog_extract.py:612` (**stay**: custom pair encoder)
- `pipelines/ntp/catalog_extract.py:328` (**stay**: header-only)

#### `write_catalog_document` — 9 defs (absorb **single-file** majority)

- Majority (4-line): `cst:238`, `evh:650`, `gor:327`, `iac:479`, `lef:485`, `mdb:366`, `search:207`, `ssr:407`
- `pipelines/ntp/catalog_extract.py:353` (**stay**: writes JSON + two JSONL)

#### `bind_import_twin` / `import_twin_of` — 2 implementations (re-export, do not fork)

- Canonical: `pipelines/oracle_grounded/import_twins.py:21` / `:29`
- Fork: `pipelines/db/import_twins.py:13` / `:20` (later cleanup: delete fork)

Re-export sites (not defs; do not edit in P4): every
`pipelines/*/ _contract.py` that does
`from ..oracle_grounded.import_twins import bind_import_twin`
(`acm`, `actf`, `cei`, `code_repair`, `crp`, `dlk`, `ewr`, `ffd`,
`ffpc`, `flk`, `gql`, `hopper`, `mill`, `msd`, `rag`, `saf`, `wsr`).

### 5.2 Stay family-local (duplicated name, different contract)

#### `is_vendor_filename` — 9 defs, **9 bodies**

- `pipelines/amc/catalog.py:158`
- `pipelines/evh/identity.py:12`
- `pipelines/gor/identity.py:12`
- `pipelines/iac/identity.py:12`
- `pipelines/lef/identity.py:12`
- `pipelines/mdb/identity.py:12`
- `pipelines/ntp/identity.py:12`
- `pipelines/search/identity.py:12`
- `pipelines/ssr/identity.py:12`

#### `load_strict_json` — 14 defs

- Shared non-float: `pipelines/tag_jsonutil.py:78`
- Exact-float `_contract` copies: `actf:38`, `cei:211`, `code_repair:54`,
  `ewr:96`, `ffd:89`, `flk:105`, `gql:151`, `hopper:88`, `mill:48`,
  `msd:109`, `rag:114`, `saf:149`, `wsr:105`

#### `load_catalog` — 28 defs (all family-local)

`acm/catalog.py:158`, `amc/catalog.py:363`, `cei/catalog.py:575`,
`code_repair/catalog.py:199`, `code_repair/catalog_load.py:341`,
`crp/catalog.py:1087`, `cst/catalog.py:55`, `dlk/catalog.py:137`,
`evh/catalog.py:67`, `ewr/catalog.py:422`, `ffd/catalog.py:317`,
`ffpc/catalog.py:1143`, `flk/catalog.py:364`, `gor/catalog.py:50`,
`gql/catalog.py:511`, `hopper/plants.py:243`, `iac/catalog.py:51`,
`lef/catalog.py:85`, `mdb/catalog.py:48`, `mill/catalog_load.py:131`,
`msd/catalog.py:519`, `ntp/catalog.py:62`, `rag/catalog.py:415`,
`rlb/catalog.py:354`, `saf/catalog.py:363`, `search/catalog.py:56`,
`ssr/catalog.py:61`, `wsr/catalog.py:483`

#### `extract_mill_catalog` — 8 defs, 7 bodies

`cst/catalog_extract.py:110`, `gor:66`, `iac:62`, `lef:263`, `mdb:70`,
`ntp:74`, `search:41`, `ssr:66`

#### `extract_companion_path` — 7 defs, 6 bodies

`evh/catalog_extract.py:83`, `gor:271`, `iac:419`, `lef:376`,
`mdb:314`, `ntp:243`, `ssr:305`

#### `catalog_document` — 9 defs, 5 bodies

`cst/catalog_extract.py:213`, `evh:591`, `gor:303`, `iac:455`,
`lef:448`, `mdb:342`, `ntp:290`, `search:183`, `ssr:376`

#### `mill_summary` — 8 defs

`evh/catalog_extract.py:552`, `gor:278`, `iac:429`, `lef:410`,
`mdb:320`, `ntp:263`, `search:157`, `ssr:321`

#### `catalog_first_from_name` — 8 defs, 4 bodies

`cst/catalog_extract.py:55`, `evh:74`, `gor:58`, `iac:54`, `lef:57`,
`mdb:62`, `ntp:66`, `ssr:61`

#### `write_catalog` — 2 defs (different writers)

- `pipelines/acm/catalog.py:146` (refuse exists + vendor)
- `pipelines/code_repair/catalog_build.py:391` (sealed catalog)

#### `sha256_text` — 5 defs

`acm/catalog.py:82`, `code_repair/catalog.py:127`, `ewr/catalog.py:94`,
`ffd/catalog.py:77`, `wsr/catalog.py:97`

#### `repo_root` — 8 defs, 1 body (do not absorb in P4; `_contract` local)

`cei/_contract.py:207`, `ewr:107`, `flk:101`, `gql:147`, `msd:105`,
`rag:110`, `saf:145`, `wsr:116`

#### `default_catalog_dir` — 8 defs, 8 bodies

`acm/catalog.py:88`, `cei/catalog.py:162`, `ffd/_contract.py:100`,
`flk/catalog.py:135`, `gql/catalog.py:167`, `msd/catalog.py:183`,
`rag/catalog.py:115`, `saf/catalog.py:118`

#### Replay / CLI name collisions (stay; not mill-support)

| name | files:lines |
|---|---|
| `build_parser` | `acm/cli.py:28`, `actf/cli.py:17`, `brw/cli.py:47`, `cei/cli.py:30`, `cer/cli.py:19`, `code_repair/cli.py:32`, `crp/cli.py:24`, `dlk/cli.py:54`, `ewr/cli.py:29`, `ffd/cli.py:29`, `ffpc/cli.py:32`, `flk/cli.py:30`, `gql/cli.py:30`, `hopper/cli.py:45`, `mill/cli.py:25`, `msd/cli.py:30`, `rag/cli.py:30`, `saf/cli.py:30`, `srl/cli.py:46`, `wsr/cli.py:29` |
| `build_success` | `brw/generate.py:134`, `cei/generate.py:173`, `ewr/generate.py:332`, `hopper/episode.py:395`, `wsr/generate.py:160` |
| `build_fail` | `brw/generate.py:476`, `cei/generate.py:343`, `hopper/episode.py:407`, `wsr/generate.py:218` |
| `build_pair` | `db/notes.py:44`, `ewr/generate.py:552`, `hopper/episode.py:437`, `wsr/generate.py:339` |
| `validate_pair` | `brw/generate.py:578`, `ewr/generate.py:524`, `hopper/episode.py:420`, `wsr/generate.py:313` |
| `assert_clean` | `db/episode.py:38`, `ffd/generate.py:45`, `hopper/episode.py:75` |
| `catalog_check` | `cei/catalog.py:693`, `code_repair/catalog_check.py:163`, `crp/catalog.py:205`, `ewr/catalog.py:446`, `ffd/catalog.py:378`, `ffpc/catalog.py:385`, `flk/catalog.py:471`, `gql/catalog.py:618`, `msd/catalog.py:626`, `rag/catalog.py:522`, `saf/catalog.py:470`, `wsr/catalog.py:507` |
| `catalog_sources` | `cst/sources.py:158`, `evh/sources.py:93`, `gor/sources.py:245`, `iac/sources.py:129`, `lef/sources.py:75`, `mdb/sources.py:298`, `ntp/sources.py:623`, `search/sources.py:46`, `ssr/sources.py:161` |
| `source_by_id` | `cst/sources.py:166`, `evh:101`, `gor:257`, `iac:141`, `lef:91`, `mdb:310`, `ntp:639`, `search:50`, `ssr:173` |
| `loop_sources` | `cst/sources.py:162`, `evh:97`, `gor:249`, `iac:133`, `lef:83`, `mdb:302`, `ntp:627`, `ssr:165` (1 body; still family tables) |
| `gen_sources` | `gor/sources.py:253`, `iac:137`, `mdb:306`, `ntp:631` |
| `is_slice_mill` | `gor/catalog_extract.py:333`, `mdb:372`, `ntp:368` |
| `plant` | `cei/catalog.py:149`, `crp:96`, `dlk:87`, `ffpc:95`, `flk:122`, `gql:154`, `mill:95`, `msd:170`, `rag:95`, `saf:105` |
| `plants_from_source` | `cei/catalog.py:326`, `crp:163`, `ffpc:274`, `flk:175`, `gql:306`, `msd:351`, `rag:211`, `saf:173` |
| `notes_markdown` | `cei/generate.py:535`, `cer/record_builder.py:230`, `ewr/generate.py:476`, `flk:437`, `gql:313`, `msd:499`, `rag:406`, `saf:495` |
| `success_episode` / `fail_episode` | `flk/generate.py:380/:409`, `gql:297/:305`, `mill/records.py:84/:167`, `msd:434/:465`, `rag:349/:374` |

Single-family helpers that look shareable but are not: `module_docstring`
(`search/catalog_ast.py:82` — promote into `ast_literals` as a **new**
shared helper, not a duplicate), `tuple_assignment_names`
(`lef/catalog_ast.py:38` — include in the union), `compact_pair_identity`
(`evh/catalog_extract.py:606` — stay), `const_keyword` /
`ctor_identity` / `spec_from_file_name` (`ssr/catalog_ast.py:111/:124/:175`
— stay).

## 6. Two landed family shapes (rebase targets)

| shape | packages | twins? | P4 consumer? |
|---|---|---|---|
| Extract catalog (`identity` + `catalog_ast` + `catalog_extract` + `sources` + `vocabulary`) | `search`, `lef`, `ssr`, `evh`, `gor`, `iac`, `mdb`, `ntp`, `cst` | no | **yes** — remaining open mill PRs copy this |
| `_contract` + replay / sealed catalog | `hopper`, `acm`, `code_repair`, `cei`, `wsr`, `ewr`, `mill`, … | yes, via `oracle_grounded.import_twins` | optional later; not P4 |

`acm` is a hybrid: `_contract.refuse_vendor_paths` + `generate.assignment_of`
/ `literal_value` + `catalog.dumps_catalog`. Remaining ACM-like families
can import `mill_support` for the three shared pieces and keep
`extract_tree` local.

`hopper` is the plant-catalog + Q=2 replay template. `qbp` / `kcl` should
keep importing hopper, not mill_support, for `_p` / `START` / `PAIRS`.

## 7. Migration order (after reset)

P4 is **additive**. Order is the point of the 500-line cap.

0. **Reset main.** Do not land P4 onto a moving mill-burst tip. In-flight
   mill PRs rebase once, onto a main that already has `mill_support`.
1. **P4 (this module only).** `pipelines/mill_support/*` +
   `tests/test_mill_support.py`. Zero edits to landed families,
   `leftover_mill.py`, `mill_*.py`, `pipelines/__init__.py`,
   `oracle_grounded/import_twins.py`, `FACTORY-REGISTRY.json`.
2. **Remaining extract families** (open mill PRs) rebase: local
   `catalog_ast.py` becomes a thin re-export or is deleted; `identity.py`
   keeps `is_vendor_filename` and calls `mill_support.vendor.refuse_vendor_paths`;
   `catalog_extract.py` imports `sha256_bytes` / `dumps_catalog` /
   `write_catalog_document` / `assignment_of` / `literal_value`.
3. **Do not** force-rebase already-merged families (`search`, `lef`,
   `ssr`, `acm`, `hopper`, …) in the same week. Optional cleanup PRs
   after the burst, one family at a time, still ≤ the family's current
   test pin.
4. **Later, not P4:** delete `db/import_twins.py` in favor of
   `mill_support.twins`; optionally point `_contract.py` files at
   `mill_support.twins` instead of `oracle_grounded.import_twins`
   (behavior-identical re-export).
5. **Never:** fold `leftover_mill.py`, `mill_family.py`, hopper
   `episode.py`, or `code_repair` catalog into mill_support.

## 8. Risk of touching shared files during the mill burst

| shared file | who edits it now | P4 may touch? | risk |
|---|---|---|---|
| `pipelines/mill_reviewed_vocabulary.py` | every new family adds a prefix home | **no** | Highest collision. Concurrent mill PRs already race this file. |
| `pipelines/leftover_mill.py` | publisher, cards, quarantine tests | **no** | Frozen `#43` / `#30` ledgers. A one-line import change retouches every Hub/card test. |
| `pipelines/mill_family.py` + `mill_*.py` | ownership / census | **no** | Fail-closed mix detector. Not extract support. |
| `pipelines/__init__.py` | sibling loader table | **no** | Adding `mill_support` to `_PACKAGE_SIBLING_NAMES` is unnecessary if it is a package with `bind_import_twin`. |
| `pipelines/oracle_grounded/import_twins.py` | every `_contract` family | **no** | P4 re-exports. Editing the binder during the burst breaks `code_repair`, hopper, ACM, and `tests/test_distill_contract.py`. |
| `pipelines/db/import_twins.py` | db family only | **no** in P4 | Third binder. Cleanup after burst. |
| `config/FACTORY-REGISTRY.json` | onboarding | **no** | Raise-at-load identity authority. |
| `pipelines/compose_mill.py` | compose / export | **no** | Source-identity mill quarantine. |
| `tests/test_pipelines_package_imports.py` | package catalog | **yes, one name** | Add `mill_support` to the import catalog when P4 lands. Isolated, but still a shared test; do it in P4, not in family PRs. |
| hopper public API (`_p`, `START`, `PAIRS`) | `qbp` / `kcl` / `wsr` / `ewr` / `cei` | **no** | Replay template. mill_support must not re-export hopper plants. |

**P4 blast radius if done during the burst (before reset):** every open
mill PR that copied `catalog_ast.py` / `identity.py` will conflict on
those copies *and* on any shared file P4 also touches. That is why the
plan is: reset, land ≤500 additive lines, then rebase remaining
families onto the new import. Touching `leftover_mill.py` or
`import_twins.py` in that same commit turns a greenfield add into a
cross-family merge hazard.

**P4 blast radius if scoped correctly:** new directory + one test
module. Remaining families rebase by deleting local copies and adding
imports. Already-landed families keep their copies until a dedicated
cleanup.

## 9. Acceptance for the later implementation PR

- Package line count ≤ 500.
- No `exec` / `eval` / `compile` / mill-script copy.
- `refuse_vendor_paths` still `SystemExit`s with `refusing to vendor {name}`
  for the extract-family spelling (ffpc stays on `refuse_when`).
- `bind_import_twin` is the `oracle_grounded` object (identity, not a
  rewrite).
- `leftover_mill.py`, `mill_*.py`, `pipelines/__init__.py`,
  `oracle_grounded/import_twins.py` unchanged.
- Unit tests for AST literals (including `UNSET` on calls other than
  `frozenset`), vendor refusal, and catalog dumps/write.
- No family `load_catalog` or `extract_mill_catalog` moved.

## 10. Path + API (operator return)

- **Design artifact (repo):** `docs/mill-support-p4-design.md`
- **Design artifact (this run):** `/opt/cursor/artifacts/mill-support-p4-design.md`
- **Implement later at:** `pipelines/mill_support/`
- **API:** `bind_import_twin`, `import_twin_of`, `UNSET`, `assignment_of`,
  `assignment_names`, `tuple_assignment_names`, `literal_value`,
  `module_constants`, `module_docstring`, `call_name`,
  `joined_path_constant`, `extract_joined_path_assignment`,
  `refuse_vendor_paths`, `prefixes_vendor`, `sha256_bytes`,
  `mill_id_for_path`, `catalog_json_path`, `dumps_catalog`,
  `write_catalog_document`
