# LLM Code-Repair Pilot v1 — executed evidence

The software/code lane's first family: code-generated, executed and verified Python
function-repair examples for Agoge-Forger. Everything below was executed on 2026-09-08 with
CPython 3.14.7 on the owner's workstation; nothing here is a design claim. The pilot is an
end-to-end pipeline demonstration. Its model utility is unmeasured.

## Pipeline (per candidate)

catalog program with doctests → seeded AST mutation (one byte span, exact inverse) → sandboxed
subprocess harness runs original, mutant, repaired (doctests + pinned hidden cases + reference) →
pure decision table → oracle-grounded envelope record → public-view SFT rendering → replay →
export. Modules: `pipelines/code_repair/`, CLI `pipelines/code_repair_cli.py`.

## Catalog: `catalogs/python-repair-v1`

Built once by `scripts/vendor_python_repair_catalog.py` from TheAlgorithms/Python at
`2067ce6dfb3b0426a88c7a40531e355a5c703cff` (MIT; `LICENSE.upstream` vendored, sha256
`4395a1dc…bea56`). Families: maths, sorts, searches, strings, bit_manipulation, conversions,
dynamic_programming; files under 3,072 bytes; explicitly allow-listed imports; targets are plain
module-level functions with at least two observable doctest examples and no free names.

The vendor allow-list is `__future__`, `bisect`, `cmath`, `collections`, `copy`, `dataclasses`,
`decimal`, `doctest`, `enum`, `fractions`, `functools`, `heapq`, `itertools`, `math`,
`operator`, `re`, `string`, `struct` and `typing`: pure computation plus the `doctest` the
upstream files run under `__main__`. Every import in a file is checked, including imports
inside functions, classes and guards; relative imports are refused. A target whose own doctest
examples import anything but a pure module (`math`, `fractions`, `itertools` and the like) is
not selected either: one upstream docstring drew on `random`, and a mutant's verdict then
differed between two generation runs.
The counts and digest in this section describe the historical `pilot-r3` catalog.
The current RUN2 catalog has 197 programs and updated pins documented in
[code-repair-admission.md](code-repair-admission.md); the historical outputs were preserved.
Rebuilding from raw upstream files can reject additional files whose nested imports were
previously unchecked. Cached raw bytes (including the license)
must match their Git blob SHA-1, and the tree SHA must match the pinned commit's tree SHA.

```
python3 scripts/vendor_python_repair_catalog.py --commit 2067ce6dfb3b0426a88c7a40531e355a5c703cff \
    --cache-dir <scratch>/tap-cache --references catalogs/python-repair-v1/references.json \
    --out catalogs/python-repair-v1
python3 pipelines/code_repair_cli.py catalog-check --catalog catalogs/python-repair-v1 --json
```

| Stage | Count |
|---|---:|
| candidate files | 287 |
| admissible files | 227 |
| selected targets | 222 |
| programs built (every original verified twice) | 206 |
| dropped or downgraded with a build note | 16 (ORIGINAL_TIMEOUT 8, ORIGINAL_FAILS_PUBLIC 3, REFERENCE_WITHOUT_CASES 2, REFERENCE_DISAGREES 1, ORIGINAL_FAILS_HIDDEN 1, ORIGINAL_HARNESS_ERROR 1) |
| certifying reference | 174 (reviewed_expression 166, sibling_same_file 8) |
| original_self (provisional only) | 32 |
| splits train / validation / held_out (by group) | 172 / 15 / 19 |

`catalog-check`: 206 programs, no finding. `programs_sha256`
`e22209fa0a56614e403c6c8facda665eac9c379c40f913c6c8c57dfb14f19a6c`; split policy
`sha256-atomic-bucket-v1`, seed 20260908, salt `python-repair-v1`, 80/10/10, sha256
`89401d6e…27aa`.

`references.json` is reviewed verification code (197 entries authored and self-checked
against the originals' neighbourhoods, then checked again by the builder on the pinned hidden
cases; the one disagreement, on the Gray-code program, sits on a program the builder drops
anyway). It never enters a prompt. Known selection limits: doctests that call through
`print(...)`, `list(...)`, keyword arguments or non-literal expressions contribute no hidden
cases, so those programs can only be provisional; in-place sorts returning `None` have no
reference. Harness limit deferred to #200 (a value whose `repr` raises is a harness error, not
a dropped case).

## Pilot run `pilot-r3` (real subprocesses)

`pilot-r3` supersedes `pilot-r1` and `pilot-r2` (same seed and stamp; the harness and the
catalog changed in the review rounds: exact integer comparison, discarded child output, an
executed reference phase, digests on passing rows, the hardened selector). Every number and hash
below is `pilot-r3`'s.

```
python3 pipelines/code_repair_cli.py generate --catalog catalogs/python-repair-v1 --seed 20260908 \
    --count 240 --per-program-cap 3 --produced-at 2026-09-08T00:00:00.000Z \
    --out outputs/code-repair/pilot-r3 --json
python3 pipelines/code_repair_cli.py replay --run outputs/code-repair/pilot-r3 \
    --catalog catalogs/python-repair-v1 --out outputs/code-repair/pilot-r3-replay --json
python3 pipelines/code_repair_cli.py export --run outputs/code-repair/pilot-r3 \
    --catalog catalogs/python-repair-v1 \
    --replay outputs/code-repair/pilot-r3-replay --out outputs/code-repair/pilot-r3-export --json
```

Current exports require RUN2 generation and five-phase evidence, including the repeated
original. Replay emits `run_identity` binding exact candidate bytes and all RUN metadata.
Export validates every evidence record and RUN counter, recomputes structural groups against
the catalog, and freshly executes replay when a report is supplied. Editing report verdicts
cannot authorize export. All integrity checks precede output creation; natural nonpositive
records remain in the unchanged evidence bytes. A candidate export without replay stays blocked.
The historical pilot-r3 numbers below predate this protocol and require a new run before they
can serve as current admission or training evidence.

Generation took about 65 s (each certifying reference executed once per program); harness sha256
`b52848d8e88cda206f517f175f4aa25799235132eb0013b04b7fcb50f312a4fd`; `candidates.jsonl` sha256
`760d17baaaf276f7a6d6340ed443a5211a49dfb6e84dcbb5e8c3298380102322`. A second run with the same
seed and `produced_at` into `outputs/code-repair/pilot-r3b` produced a byte-identical
`candidates.jsonl` (same sha256).

| Quantity | Count |
|---|---:|
| draws | 240 |
| records (every executed candidate) | 213 |
| skipped before execution | 27 duplicate mutants, 4 draws with no site |
| accepted / rejected | 166 / 47 |
| validated / provisional | 173 / 40 (every validated record carries an executed reference phase that answered all its cases; `REFERENCE_NOT_CERTIFYING` 0) |
| positives (accepted and validated) | 132 over 99 programs |
| rejected by code | MUTANT_NO_OBSERVED_FAILURE 22, MUTANT_TIMEOUT 14, MUTANT_NO_PUBLIC_FAILURE 7, MUTANT_NO_HIDDEN_FAILURE 4 |
| accepted per operator (of drawn) | return_value 43/43, boolean_condition 42/44, arithmetic_operator 34/41, off_by_one 26/40, comparison_boundary 21/45 |
| positives per split | train 113, validation 7, held_out 12 |
| positives per family | maths 46, bit_manipulation 27, dynamic_programming 17, strings 16, conversions 13, sorts 10, searches 3 |

Replay: 132 of 132 positives `REPLAY_PASSED` (all four phases re-executed, the reference from the
pinned catalog), 81 `not_replayed` (natural ineligibility), 0 failed; `REPLAY.json` sha256
`db4ad9381200884d47c6b5a948aba5be20dd5e56b40c0e3964fc14d037c5eec8`, carrying the run identity
the exporter binds to.

Export: 132 rows exported (no exact or structural duplicate, lineage cap 6 never reached);
`MANIFEST.json` sha256 `292f9b8d02108b28d4a7f9259e7effb6b6399818dc957ef57274be3499f45c7b`;
`pipeline_status: complete`; `replay: passed`; `admission.training_export: blocked` with blockers
`REGISTRY_ROW_MISSING`, `RIGHTS_PROFILE_MISSING`, `RECORD_KIND_UNSUPPORTED`, `ROUND_NOT_PUBLISHED`
and decisions D-A … D-E; `evaluation_limitations`: `PRETRAINING_EXPOSURE_UNKNOWN`,
`POSSIBLE_UPSTREAM_CODE_RECALL`; `training_run_prerequisites`:
`AGOGE_COMPLETION_ONLY_LOSS_UNTESTED`, `AGOGE_TRAINER_BATCH_TEST_MISSING`.

The first export attempt of `pilot-r1` was refused: the evidence check compared the mutant's
failing rows in stored (id-text) order, so the thirteen-example `is_match` record looked forged.
Fixed with a regression test (also raised by Codex on #197).

## One example (record `pfr-20260908-00013`, train split)

Source `conversions/ipv4_conversion.py::alt_ipv4_to_decimal` at the pinned commit (file sha256 `343df7f4…6e7a`;
module sha256 `d66f8c83e7b6984120b2625b3f92388f98dd5c68dca943625694dd8138880698`, program
`tap-8b1387aa93347e64`). Mutation `arithmetic_operator` / `swap` at line 8,
bytes 201–202: `+` → `-`. Original 2/2 public and 7/7 hidden pass;
mutant 0/2 public and 0/7 hidden; repaired 2/2 public and 7/7 hidden; reference phase 7/7. Reason codes
`MUTANT_FAILS_PUBLIC`, `MUTANT_FAILS_HIDDEN`, `REPAIR_PASSES_ALL`; oracle status `validated` (reference executed in this
run). Hashes: broken `ca48ad86…cd34`, repaired `d66f8c83…0698` (equal to the original
module), evidence `c7a3c534…d15d`, record
`c5227daf1fc83e064111afe86195e80f1ce728ddaf1a0ea92d00d5c79412cf54`. Rendered with
`python3 pipelines/code_repair_cli.py render outputs/code-repair/pilot-r3 pfr-20260908-00013 --json`,
no leak finding:

````
You are given a Python module containing one function whose docstring examples are its specification. The function has a bug: at least one docstring example fails under doctest. Return the corrected module.

### Module: program.py
```python
def alt_ipv4_to_decimal(ipv4_address: str) -> int:
    """
    >>> alt_ipv4_to_decimal("192.168.0.1")
    3232235521
    >>> alt_ipv4_to_decimal("10.0.0.255")
    167772415
    """
    return int("0x" - "".join(f"{int(i):02x}" for i in ipv4_address.split(".")), 16)
```

### Failing doctest examples
Failed example:
    alt_ipv4_to_decimal("192.168.0.1")
Expected:
    3232235521
Got:
    TypeError: unsupported operand type(s) for -: 'str' and 'str'

Failed example:
    alt_ipv4_to_decimal("10.0.0.255")
Expected:
    167772415
Got:
    TypeError: unsupported operand type(s) for -: 'str' and 'str'

### Instructions
Reply with the complete corrected contents of program.py and nothing else.

````

Completion: the module above with `+` restored (raw text, trailing newline, no fence).

## Agoge consumer probe (Agoge-Forger head 9cb81bdf, its own virtualenv)

```
/home/raulmc/rmems/agoge-forger/.venv/bin/python scripts/agoge_consumer_probe.py \
    outputs/code-repair/pilot-r3-export/agoge/code_repair_v1.jsonl \
    --manifest outputs/code-repair/pilot-r3-export/MANIFEST.json \
    --config /home/raulmc/rmems/agoge-forger/configs/minicpm5_canary.yaml \
    --tokenizer-revision 156170697656c48f69915b33a2fb44110242187c \
    --freeze-into <scratch>/pilot-agoge --source-revision <producer-commit-40hex> \
    --dataset-version <immutable-dataset-version> --json
```

Result `passed: true` (input bound to the manifest's digest and row count): 132 rows through
`normalize_row` and the frozen-split reader with a declared lineage; Agoge's own
`assign_records` reproduces the recorded splits exactly (113 / 7 / 12);
`materialize_split` wrote a frozen snapshot whose report lists every leakage gate as holding
(content hashes, canonical ids, source coordinates, lineage ids, declared group ids do not
cross splits) with no exclusion.

Tokenization and labels (`openbmb/MiniCPM5-1B-Base` at the pinned revision, TRL 1.4.0 collator,
canary `max_seq_length` 512): prompt tokens 265 / 436 / 888 (min / median / max), completion
tokens 103 / 253 / 691; 109 of 132 rows exceed 512 tokens and lose part or all of their
completion to `keep_start` truncation; no row exceeds 2,048. Under the historical Agoge path (one
`text` column, `completion_only_loss` resolves False) 66,014 tokens receive loss, 55,648 of them
prompt tokens; with a prompt/completion pair and `completion_only_loss=True` the same batch puts
loss on 10,366 tokens, all corrected code. Gap codes reported: `PROMPT_COMPLETION_UNSUPPORTED_RENDERED_TO_TEXT`,
`NO_LOSS_MASKING_PROMPT_TOKENS_TRAINED`, `CONFIG_REVISION_PIN_REQUIRED_40_HEX`,
`CONFIG_HAS_NO_SPLIT_FIELD_DATASET_PATH_MUST_BE_SPLITS_TRAIN`,
`EVAL_IDENTIFIES_HELD_OUT_BY_CANONICAL_ID_ONLY`.

Those measurements describe the historical probe, not the current completion masking path.
The current probe uses `agoge_forger.train.completion.completion_tokens` and the real TRL
collator, reads the producer's Unicode `completion_start_char`, and rejects over-budget or
ambiguous examples without truncation. Tokenizers must already be cached locally. Its report
states the configured loss mode and both prompt-loss counts. Actual freeze requires a real
producer commit and dataset version; placeholder provenance is diagnostic only.
The Agoge implementation and trainer-batch proof are tracked by rmems/agoge-forger#133 and
PR #138. A successful standalone batch probe is not a training launch. The final integrated
pilot and frozen handoff must be generated separately.

## Evidence by kind

- Fake-executor test evidence (canned phase reports, golden digests, decision-table rules, leak
  tampers, forged-record and drift codes): `tests/test_code_repair_*.py`.
- Real subprocess evidence: harness, executor, builder and replay tests; `catalog-check`,
  `pilot-r3`, its replay, its export and the probe above; the vendor script's offline test builds
  a catalog from the fixture's upstream files and checks it.

## Not done, by design

No registry row, rights profile, record-kind route, publication through `round_txn`, Hub
publication, or training launch (S4, owner-gated). Pretraining exposure of the upstream code for
any model is unknown; held-out numbers may measure recall of upstream code.
