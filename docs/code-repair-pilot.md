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

The vendor allow-list is `__future__`, `cmath`, `collections`, `copy`, `decimal`,
`fractions`, `functools`, `itertools`, `math`, `operator`, `re`, `struct`, and `typing`:
the imports in the pinned catalog module texts, plus `__future__`. Every import is checked,
including imports inside functions, classes, and guards; relative imports are refused.
The existing catalog is unchanged. Rebuilding from raw upstream files may reject additional
files whose nested imports were previously unchecked. Cached raw bytes (including the license)
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
| admissible files | 233 |
| selected targets | 232 |
| programs built (every original verified twice) | 220 |
| dropped with a build note | 12 (ORIGINAL_TIMEOUT 7, ORIGINAL_FAILS_PUBLIC 3, ORIGINAL_FAILS_HIDDEN 1, ORIGINAL_HARNESS_ERROR 1) |
| certifying reference | 186 (reviewed_expression 175, sibling_same_file 11) |
| original_self (provisional only) | 34 |
| splits train / validation / held_out (by group) | 183 / 15 / 22 |

`catalog-check`: 220 programs, no finding. `programs_sha256`
`8930320df4959f3a4180c2eac35b5d6d4e32b281552b5bd680f0b8d12eb377d6`; split policy
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

## Pilot run `pilot-r2` (real subprocesses)

`pilot-r2` supersedes the earlier `pilot-r1` (same seed, stamp and catalog; the harness changed in
the Codex review round: exact integer comparison, bounded child output, an executed reference
phase). Counts are identical; every hash below is `pilot-r2`'s.

```
python3 pipelines/code_repair_cli.py generate --catalog catalogs/python-repair-v1 --seed 20260908 \
    --count 240 --per-program-cap 3 --produced-at 2026-09-08T00:00:00.000Z \
    --out outputs/code-repair/pilot-r2 --json
python3 pipelines/code_repair_cli.py replay --run outputs/code-repair/pilot-r2 \
    --catalog catalogs/python-repair-v1 --out outputs/code-repair/pilot-r2-replay --json
python3 pipelines/code_repair_cli.py export --run outputs/code-repair/pilot-r2 \
    --catalog catalogs/python-repair-v1 \
    --replay outputs/code-repair/pilot-r2-replay --out outputs/code-repair/pilot-r2-export --json
```

Export now requires the replay report's `run_identity` to match the candidate file bytes and
RUN metadata. Until S2 supplies that field, reports produced by this branch's replay command
are refused by export; the export test fixtures stamp the expected identity after `replay.run`.
The catalog digest, split policy, per-record lineage, and RUN summary counts are also checked
before any export files are written.

Generation took about 65 s (each certifying reference executed once per program); harness sha256
`c4d8a8ac0b2c531ae0ac1cb10d86e4a0859e7f88b4b6cf430a73a68dba50d248`; `candidates.jsonl` sha256
`419279b55b8fceb35a29ead20c3d480605b242a2a5e7f03ed545e562922d9ef5`. A second run with the same
seed and `produced_at` into `outputs/code-repair/pilot-r2b` produced a byte-identical
`candidates.jsonl` (same sha256).

| Quantity | Count |
|---|---:|
| draws | 240 |
| records (every executed candidate) | 217 |
| skipped before execution | 23 duplicate mutants, 3 draws with no site |
| accepted / rejected | 178 / 39 |
| validated / provisional | 191 / 26 (every validated record carries an executed reference phase that answered all its cases; `REFERENCE_NOT_CERTIFYING` 0) |
| positives (accepted and validated) | 156 over 113 programs |
| rejected by code | MUTANT_NO_OBSERVED_FAILURE 20, MUTANT_TIMEOUT 9, MUTANT_NO_PUBLIC_FAILURE 5, MUTANT_NO_HIDDEN_FAILURE 3, MUTANT_HARNESS_ERROR 2 |
| accepted per operator (of drawn) | arithmetic_operator 60/64, return_value 40/40, off_by_one 37/46, boolean_condition 30/35, comparison_boundary 11/32 |
| positives per split | train 131, validation 6, held_out 19 |
| positives per family | maths 48, dynamic_programming 29, strings 23, bit_manipulation 21, sorts 18, conversions 13, searches 4 |

Replay: 156 of 156 positives `REPLAY_PASSED` (all four phases re-executed, the reference from the
pinned catalog), 61 `not_replayed` (natural ineligibility), 0 failed; `REPLAY.json` sha256
`db2f4b5c84f3db603f7f343e9e0c3f25e74bd5873a0f9a26b22bc313046e2988`.

Export: 156 rows exported (no exact or structural duplicate, lineage cap 6 never reached);
`MANIFEST.json` sha256 `667e58f8e6733966f3fdfe53307f9e3400b1646bab1bd3da8d595f17473e682e`;
`pipeline_status: complete`; `replay: passed`; `admission.training_export: blocked` with blockers
`REGISTRY_ROW_MISSING`, `RIGHTS_PROFILE_MISSING`, `RECORD_KIND_UNSUPPORTED`, `ROUND_NOT_PUBLISHED`
and decisions D-A … D-E; `evaluation_limitations`: `PRETRAINING_EXPOSURE_UNKNOWN`,
`POSSIBLE_UPSTREAM_CODE_RECALL`; `training_run_prerequisites`:
`AGOGE_COMPLETION_ONLY_LOSS_UNTESTED`, `AGOGE_TRAINER_BATCH_TEST_MISSING`.

The first export attempt of `pilot-r1` was refused: the evidence check compared the mutant's
failing rows in stored (id-text) order, so the thirteen-example `is_match` record looked forged.
Fixed with a regression test (also raised by Codex on #197).

## One example (record `pfr-20260908-00078`, train split)

Source `strings/reverse_words.py::reverse_words` at the pinned commit (file sha256
`95df74cf…169b`; module sha256 `7a321030eda87113744a1afb78c035adcf36a6d62fe7c605457f3b5f949dd7a4`).
Mutation `off_by_one` / `plus_one` at line 11 col 40, bytes 322–323: `1` → `2`
(`[::-1]` → `[::-2]`). Original 2/2 public and 10/10 hidden pass; mutant 0/2 public and 2/10
hidden; repaired 2/2 and 10/10; reference phase 10/10. Reason codes `MUTANT_FAILS_PUBLIC`,
`MUTANT_FAILS_HIDDEN`, `REPAIR_PASSES_ALL`; oracle status `validated` (reviewed-expression
reference executed in this run). Hashes: broken `f1bb2704…da28`, repaired `7a321030…d7a4` (equal
to the original module), evidence `69eab9d7…9f86`, record
`2b80ba8a8b8051bcbe12e3d76a45204955e3d9f53ed05b68aca3f39026f39f49`. Rendered with
`python3 pipelines/code_repair_cli.py render outputs/code-repair/pilot-r2 pfr-20260908-00078
--json`, no leak finding:

````
You are given a Python module containing one function whose docstring examples are its specification. The function has a bug: at least one docstring example fails under doctest. Return the corrected module.

### Module: program.py
```python
def reverse_words(sentence: str) -> str:
    """Reverse the order of words in a given string.

    Extra whitespace between words is ignored.

    >>> reverse_words("I love Python")
    'Python love I'
    >>> reverse_words("I     Love          Python")
    'Python Love I'
    """
    return " ".join(sentence.split()[::-2])
```

### Failing doctest examples
Failed example:
    reverse_words("I love Python")
Expected:
    'Python love I'
Got:
    'Python I'

Failed example:
    reverse_words("I     Love          Python")
Expected:
    'Python Love I'
Got:
    'Python I'

### Instructions
Reply with the complete corrected contents of program.py and nothing else.
````

Completion: the module above with `[::-1]` restored (raw text, trailing newline, no fence).

## Agoge consumer probe (Agoge-Forger head 9cb81bdf, its own virtualenv)

```
/home/raulmc/rmems/agoge-forger/.venv/bin/python scripts/agoge_consumer_probe.py \
    outputs/code-repair/pilot-r2-export/agoge/code_repair_v1.jsonl \
    --manifest outputs/code-repair/pilot-r2-export/MANIFEST.json \
    --config /home/raulmc/rmems/agoge-forger/configs/minicpm5_canary.yaml \
    --tokenizer-revision 156170697656c48f69915b33a2fb44110242187c \
    --freeze-into <scratch>/pilot-agoge --json
```

Result `pass: true`: 156 rows through `normalize_row` and the frozen-split reader with a declared
lineage; Agoge's own `assign_records` reproduces the recorded splits exactly (131 / 6 / 19);
`materialize_split` wrote a frozen snapshot whose report lists every leakage gate as holding
(content hashes, canonical ids, source coordinates, lineage ids, declared group ids do not
cross splits) with no exclusion.

Tokenization and labels (`openbmb/MiniCPM5-1B-Base` at the pinned revision, TRL 1.4.0 collator,
canary `max_seq_length` 512): prompt tokens 222 / 438 / 842 (min / median / max), completion
tokens 81 / 257 / 586; 127 of 156 rows exceed 512 tokens and lose part or all of their
completion to `keep_start` truncation; no row exceeds 2,048. Under Agoge's current path (one
`text` column, `completion_only_loss` resolves False) 77,399 tokens receive loss, 66,008 of them
prompt tokens; with a prompt/completion pair and `completion_only_loss=True` the same batch puts
loss on 11,391 tokens, all corrected code. Gap codes reported: `PROMPT_COMPLETION_UNSUPPORTED_RENDERED_TO_TEXT`,
`NO_LOSS_MASKING_PROMPT_TOKENS_TRAINED`, `CONFIG_REVISION_PIN_REQUIRED_40_HEX`,
`CONFIG_HAS_NO_SPLIT_FIELD_DATASET_PATH_MUST_BE_SPLITS_TRAIN`,
`EVAL_IDENTIFIES_HELD_OUT_BY_CANONICAL_ID_ONLY`.

What this establishes: the export loads under Agoge's contract today and the split
re-derivation agrees. What it does not: that Agoge's training path masks prompts. That fix and
its real trainer-batch test are Agoge-side work, tracked as rmems/agoge-forger#133 and recorded
here as a prerequisite for the training launch only.

## Evidence by kind

- Fake-executor test evidence (canned phase reports, golden digests, decision-table rules, leak
  tampers, forged-record and drift codes): `tests/test_code_repair_*.py`.
- Real subprocess evidence: harness, executor, builder and replay tests; `catalog-check`,
  `pilot-r2`, its replay, its export and the probe above; the vendor script's offline test builds
  a catalog from the fixture's upstream files and checks it.

## Not done, by design

No registry row, rights profile, record-kind route, publication through `round_txn`, Hub
publication, or training launch (S4, owner-gated). Pretraining exposure of the upstream code for
any model is unknown; held-out numbers may measure recall of upstream code.
