# Task-verification gate (#496)

`pipelines/task_gate/` turns unverified mutation proposals, procedural or model-backed, into
verified repair tasks. It mirrors SWE-smith's rule of keeping a bug only if it breaks at least
one test. Every proposal gets exactly one verdict row, so survival rate by reason is reportable.

```bash
# Gate a JSONL file of proposals against a pinned code-repair catalog
python3 pipelines/task_gate_cli.py verify --catalog <catalog_dir> --proposals proposals.jsonl \
  --denylist <denylist.txt> [--prior-index <old>/dedup-index.jsonl ...] --out <new_dir>
# Gate the procedural mutator's seeded proposals through the same code path
python3 pipelines/task_gate_cli.py procedural --catalog <catalog_dir> --seed 1 --count 200 \
  --denylist <denylist.txt> --out <new_dir>
python3 -m unittest tests.test_task_gate tests.test_task_gate_harness tests.test_task_gate_sandboxed \
  tests.test_task_gate_sandboxed_report -q -b
```

## Inputs

* **Programs** come from a pinned `code_repair` catalog (`program_id`, module text, target
  function). The target function's docstring examples are the doctests.
* **Proposals** are JSONL rows `{proposal_id?, program_id, replacement_text, source?}` plus a
  span as either `start_byte`/`end_byte` (UTF-8 byte offsets, the procedural `Site` shape;
  `original_text` is then optional and must match the bytes) or `original_text` alone, which
  must occur exactly once in the module. The procedural mutator is adapted to this same type in
  `procedural.py`; the gate never branches on `source`.
* **Denylist** is a required input: UTF-8, LF-framed, one program id per line, no blank lines,
  padding or duplicates, at least one entry. A missing, unreadable, empty or malformed list
  refuses the run (exit 2, nothing written). The vendored #494 list is wired in once #504 lands.
* **Prior indexes** (`--prior-index`, repeatable, optional on a first run) are earlier runs'
  `dedup-index.jsonl` files. They are read, never modified.

## Verdicts and evaluation order

The first failing rule wins.

| Order | Verdict | Meaning |
| --- | --- | --- |
| 1 | `denylisted` | program id is on the eval denylist; nothing is parsed or executed for it |
| 2 | `parse_error` | malformed row, unknown program, span not resolving to exactly one span of the target body (outside its docstring), mutant does not compile, does not load, or kills the interpreter without a report, or the replacement changes anything outside the target body (`mutant_escapes_target_body`: another module statement, the target's header or docstring, a new write to its own name, `__doc__` or `__test__`, or a new read of a docstring, code object or source: `.__doc__`, `.__code__`, a `"__doc__"`/`"__code__"` literal, or `inspect.getsource`/`getdoc` and the like) |
| 3 | `duplicate` | `sha256(program_id, span, replacement_text)` of the canonical (minimal) edit, bound to the program's sha256, was kept in a prior run or earlier in this one; proposals that produce the same mutant share a key |
| 4 | `original_fails` | the unmodified program does not pass all its doctests, has none, does not load, or times out |
| 5 | `timeout` | the mutant exceeded the wall-clock budget (rejected, never kept) |
| 6 | `mutant_passes` | the mutant passes every doctest |
| 7 | `kept` | the mutant fails at least one doctest |

Each row also carries a `detail` code (for example `span_touches_docstring`). Only kept
proposals enter the dedup index: a rejected proposal is deterministic and is rejected again on
its own merits.

## Outputs

A run writes a brand-new directory (refused if it exists or names the raw tree), staged beside
its destination and moved into place with an atomic no-replace rename (`renameat2` with
`RENAME_NOREPLACE`, the repository's shared `compose_destination_rename.rename_noreplace`), so a
destination another writer creates mid-run is refused, never overwritten:

* `tasks.jsonl` -- one row per input proposal, in input order, with verdict, detail, resolved
  span, dedup key and program/mutant digests.
* `summary.json` -- counts for all seven verdicts (zeros included), `survival_rate`, rejection
  rates, detail counts, counts by `source`, and the digests of the denylist, prior indexes,
  programs and proposals the result depends on.
* `dedup-index.jsonl` -- cumulative: the prior keys plus this run's kept keys. The next run
  needs only this file.

## Harness

Each program text runs in a child `python3 -P -s -S -B -X utf8 _child.py` in a throwaway working
directory with an environment rebuilt from scratch (no proxy variables, no API keys), under a
wall-clock timeout (process group killed; the wait after the kill is itself bounded), CPU,
address-space and file-size limits (a child that cannot apply them reports `crashed` and never imports
the program), and with the socket entry points and `_socket` replaced before the program is imported. Neither the repository nor any
site-packages is importable, so no solver module is reachable (#160). `-P -s -S` is used instead
of `-I` because `-I` implies `-E`, which would discard `PYTHONHASHSEED=0` and make set and dict
reprs differ between the original and the mutant run.

`SubprocessHarness` is a harness, not a security sandbox: the network block is in-process and
best effort, and a hostile program can forge the report line.

For untrusted mutants (the model-backed proposer) pass `--sandbox`, which runs the same doctests
through `SandboxedHarness` on `code_repair`'s OS boundary (`bwrap-ro-netns-v1`: read-only root,
unshared user/net/pid namespaces, private tmp, seccomp, unprivileged uid) plus the Landlock
allowlist. The network is denied by the kernel (empty network namespace and EPERM on `connect`),
not by patching `socket`.

The sandboxed verdict is made in the parent, never in the process that loads the program. The
parent parses the target's doctests from the text (`sandboxed_plan.py`), writes `program.py`
with that docstring emptied, and sends the child only a per-run key and each example's source.
The child runs the examples through `doctest` with a checker that records what each one
produced, and writes one record per example, sealed with the key (HMAC-SHA256) and numbered, to
the report file. The parent opens the records and compares each with the expected output it kept
(`sandboxed_judge.py`), with `doctest`'s own checker and the example's option flags. What follows:

- A pass cannot be forged. The expected outputs never enter the sandbox, so a program passes only
  by producing them, or by guessing them from the example source alone.
- Writing to the report from outside the child's own code (a forked poller, a write to any
  inherited descriptor, a truncation) makes the run `crashed`, never a verdict. The key is read
  from stdin and stdin is replaced before `program.py` is read; it is never written to a file,
  argument or environment variable, and Landlock keeps `/proc/self/mem` unreadable.
- Not closed: a program that tampers with the interpreter it runs in (rebinding the child's
  checker, or reading the key out of the child's own objects) can make its own run report
  `failed` or `crashed`, though still never `passed`. That is the hostile-introspection class the
  AST tamper check also leaves open.

The examples are read from the source, so the target is the top-level `def` of that name (a
decorated target, or one whose name is bound anywhere else at module level, is `crashed` with
`target_binding`, since the object that runs may not be that `def`) and its docstring as the compiler stores it (`__doc__`, dedented on Python 3.13+), so the examples
match `DocTestFinder`'s; examples marked `+SKIP` are neither sent nor counted, and a docstring
`doctest` cannot parse is a `load_error` before anything runs. Output is recorded in full up to
1 MiB (UTF-8) per run across all examples; a run that prints more is `crashed`
(`output_truncated`), never `failed`, because a prefix cannot be judged. `SubprocessHarness` has no such
budget. The other difference is the emptied docstring itself: a program that reads its target's
docstring or source can tell. The gate refuses a mutant whose body newly reads `__doc__`,
`__code__`, a `"__doc__"`/`"__code__"` string literal (so `getattr`, `__getattribute__`,
`attrgetter` and the like) or `inspect.getsource`/`getdoc` (`mutant_escapes_target_body`),
so a mutant cannot pass under one harness and be kept under the other that way; reading its own
source text by other means is the same best-effort class as the rest of the AST tamper check. The flag never falls back: when
bwrap or Landlock is unavailable, or a run's resource-limit and Landlock attestations are
missing, the run is refused (`TASK_GATE_HARNESS_UNAVAILABLE`). `summary.json` records the harness in
`inputs.harness` (`kind`: `subprocess` or `sandboxed`, plus the isolation identity). `Gate`
accepts any object with `run(program_text, function)`.
