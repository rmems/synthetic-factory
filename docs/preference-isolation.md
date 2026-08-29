# Preference Isolation — Two-Session Generation, Same-Context Purity & Independent Arms

> Factory: `failure-as-fuel-preference-cascade` (sf-cic)  
> Co-author: Muse Code powered by Muse Spark  
> Contract: `prompts/_factory-contract.md` · Prompt: `prompts/05-failure-as-fuel-preference-cascade.md`

## 1. Purpose

Preference training (DPO / ORPO / safety distillation) is only meaningful
when the `chosen` vs `rejected` contrast isolates **gate and execution
quality** rather than a changed problem. If the two sides propose different
tasks, different states, or different tool calls, the learner can exploit
the easier problem instead of the better judgment.

This document defines the **two-session isolation protocol**, the
**same-context purity gate**, and the **independent-arm gate** that together
enforce that property for every round of
`failure-as-fuel-preference-cascade`.

### 1.1 The single-session path is deprecated

Earlier rounds generated failure → diagnosis → repair → preference inside
**one** context. That path is **deprecated and must not be used for new
rounds.** A single context that has just written the failure writes the
repair as its negation: the two arms end up correlated, the DPO gradient
degenerates toward surface polarity, and the round becomes a monoculture
sample rather than an independent contrast.

Concretely, for every round generated from this point on:

| Rule | Enforcement |
|---|---|
| `rejected` + diagnosis come from Session A only | `prompts/05-…md` Session A isolation rule; the launcher runs it as its own agent |
| `chosen` comes from a fresh Session B whose only bridge is the diagnosis | `prompts/05-…md` Session B isolation rule; the launcher runs it as a separate agent |
| A content-blind controller reserves with `--preference-isolation two-session` before Session A starts | The launcher validates the exact receipt, staging path, token, and diagnosis-only handoff; record metadata cannot substitute for the reservation assertion |
| A separate arm-payload-blind verifier binds the diagnosis handoff before Session B starts | `preference_arms.py verify-handoff --write-receipt` validates the bounded six-section diagnosis format, rejects full-trajectory payload mappings, and exclusively persists exact basenames, byte counts, and SHA-256 digests; publication revalidates structure and receipt against captured bytes |
| Each record also declares `meta.isolation: "two-session"` | `pipelines/preference_arms.py` rejects a missing, conflicting, or non-`two-session` declaration |
| The two arms are not one arm restated | `round_txn.py publish` runs `preference_arms.py` over captured bytes before the commit point |

Legacy corpora that predate the protocol carry no attestation. Scan those
with `--no-require-isolation`, which reports the attestation but does not
block on it. New rounds MUST NOT use that flag.

## 2. Two-session generation

A single `pipelines/round_txn.py reserve` call creates one `staging_dir`
for the round. Both sessions operate inside that directory, but they MUST
NOT share generation context.

```
reserve ─► Session A (rejected + diagnosis) ─► arm-payload-blind verifier ─► Session B
              │                                      │                  │
              ▼                                      ▼                  ▼
         rejected-0i-rNN.json                 names/bytes/SHA-256   batch-rNN.jsonl
         diagnosis-0i-rNN.md                                      NOTES-rNN.md
                                                                  diagnoses retained
```

### 2.1 Session A — Rejected + Diagnosis

| Aspect | Requirement |
|---|---|
| **Input** | Round number, quota (3), factory contract, prior round notes |
| **Output** | 3 scratch `rejected` artifacts + 3 diagnosis files |
| **Forbidden** | Any `chosen` trajectory, any outline of the repair beyond the diagnosis sketch |
| **Diagnosis per record** | Root cause, cascade effects, supervisor-catch, repair sketch |
| **Batch file** | MUST NOT be written yet |

Scratch rejected artifacts are staged as `rejected-01-rNN.json` — one
ThalamicTrajectory JSON object per file — so they satisfy the artifact
allowlist and are publishable, but they are not the final batch.

Each `diagnosis-0i-rNN.md` must be self-contained: a reader who has never
seen the rejected JSON can reconstruct the intended repair from the
diagnosis alone. It must not paste the full rejected trajectory — only a
narrative repair sketch. The machine-enforced document is at most 64 KiB and
uses exactly these headings, in order: `# Diagnosis`, `## Shared context`,
`## Root cause`, `## Cascade effects`, `## Supervisor catch`, `## Repair
sketch`, and `## Target reward delta`. Shared context is one fenced JSON object
with exactly `state` and `proposed_action`; target delta is one fenced JSON
object with exactly `per_component` and a reconciled `total`. The four prose
sections are non-empty and at most 4 KiB each. Extra headings/fences and
serialized trajectory mappings are rejected, so the receipt cannot bless a
full rejected payload hidden in the Markdown.

### 2.2 Session B — Chosen from Diagnosis Only

| Aspect | Requirement |
|---|---|
| **Input** | Independently verified `diagnosis-0i-rNN.md` files ONLY (plus the `state`/`proposed_action` they describe) |
| **Forbidden** | Reading `rejected-*-rNN.json`, copying rejected JSON, or reusing Session A context |
| **Output** | 3 repaired `chosen` ThalamicTrajectories |
| **Assembly** | Merge each `chosen` with its verbatim `rejected` (from Session A scratch) into `batch-rNN.jsonl` as `{id, chosen, rejected, critique, reward_delta}` |

Session B MUST start a **fresh generation context** (new model session).
The isolation is semantic: even though both sessions' artifacts coexist in
the same `staging_dir` on disk, Session B's prompt context must not contain
the rejected trajectory text. The diagnosis is the only bridge.

**Why diagnosis-only?** If Session B sees the full rejected trajectory it
can trivially negate surface wording ("do the opposite") without
understanding the failure class. Forcing reconstruction from the diagnosis
ensures the repair is grounded in causal analysis and generalizes to new
failures of the same class.

### 2.3 Session handoff requirements

- Session A produces exactly 3 diagnoses and 3 rejected scratch files.
- No `batch-rNN.jsonl` exists after Session A.
- `verify-handoff --write-receipt` validates the bounded six-section format and exclusively binds the exact three diagnosis basenames, sizes, and SHA-256 digests before Session B.
- Session B starts with reset context (new conversation / cleared history).
- Session B does not open any `rejected-rNN*.json` file.
- Final `batch-rNN.jsonl` has exactly 3 lines, each with `chosen` + `rejected` + non-empty `critique`.
- Every record attests `meta.isolation: "two-session"`.
- Publication binds each ordered Session A artifact to the pair published
  beside it: `diagnosis-0i-rNN.md`'s Shared-context block must be the
  published pair's own `state` and `proposed_action`, and `rejected-0i-rNN.json`
  must be the published `rejected` arm, allowing only the launcher's
  `meta.isolation` / `meta.round` / `meta.factory` assembly stamps. Validating
  each diagnosis alone left both halves unbound: a batch could publish records
  no authorized diagnosis described, and Session B could emit a `rejected` arm
  of its own beside Session A's unrelated failures, which is the two-session
  separation defeating itself.
- The same-context purity gate passes (Section 3).
- The independent-arm gate passes (Section 3.6).
- `NOTES-rNN.md` names residual weaknesses and the next densification target.

## 3. Same-context purity gate

### 3.1 Definition

For every preference record `r` in `batch-rNN.jsonl`:

```
r.chosen.state  == r.rejected.state          (deep JSON equality)
r.chosen.proposed_action == r.rejected.proposed_action
```

- Equality is **canonical equality** of JSON values: objects are equal
  irrespective of key order; arrays are order-sensitive; strings match by
  exact content; numbers match by canonical spelling, so `9` and `9.0` are
  *different* context and `True` is never `1`.
- The spelling rule is deliberate, not an oversight of value equality. Both
  arms copy `state` and `proposed_action` from the one Shared context block
  in the diagnosis. If the two spellings differ, the arms did not copy from
  a single source, which is the divergence this gate exists to catch. The
  strict-audit corpus pins that behaviour
  (`test_loosely_equal_cross_type_context_values_are_excluded`).
- The check applies to the entire `state` and `proposed_action` subtrees,
  including nested fields like `state.environment`, `state.timestamp_*`,
  `proposed_action.content`, `proposed_action.parameters`, etc.
- `safety_decision`, `executed_action`, `future_outcome`, and
  `reward_components` MUST differ (otherwise there is no preference signal),
  but `state` and `proposed_action` MUST NOT.

This is the same invariant stated in the factory contract
(`Preference chosen and rejected share the exact same state and proposed
action`) made executable.

### 3.2 Rationale

| Violation | What the learner exploits | Consequence |
|---|---|---|
| Different `state` | Easier initial conditions | Reward hacking via problem selection |
| Different `proposed_action` | Easier task to execute | Preference collapses to task difficulty |
| Both differ | Uncontrolled confound | DPO gradient is meaningless |

When `state` and `proposed_action` are identical, the reward delta can
only be attributed to **gate quality, execution quality, and recovery
quality** — the intended training signal.

### 3.3 Canonical validator

The gate is enforced at publish time by `round_txn.py`, which runs
`preference_arms.py` over a captured copy of the staged batch before the
completion marker is linked. The arm gate delegates its same-context
decision to `curate_preferences.context_is_pure`; `check_records.py` and
`validate_run.py` continue to own the shape checks. A round that fails any
part of this gate never reaches the commit point.

Reference implementation (pure Python, no external deps):

```python
import json, pathlib

def deep_equal(a, b) -> bool:
    if type(a) is not type(b):
        # Canonical spelling, not value: 42 and 42.0 are different context,
        # and True is never 1. Both arms copy this subtree from the one
        # Shared context block, so a spelling difference means they did not.
        return False
    if isinstance(a, dict):
        return set(a) == set(b) and all(deep_equal(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(deep_equal(x, y) for x, y in zip(a, b))
    return a == b

def check_purity(batch_path: str | pathlib.Path) -> list[str]:
    errors: list[str] = []
    for lineno, line in enumerate(pathlib.Path(batch_path).read_text().splitlines(), 1):
        if not line.strip():
            continue
        r = json.loads(line)
        for field in ("state", "proposed_action"):
            a, b = r.get("chosen", {}).get(field), r.get("rejected", {}).get(field)
            if a is None or b is None:
                errors.append(f"line {lineno}: missing chosen/rejected.{field}")
            elif not deep_equal(a, b):
                errors.append(
                    f"line {lineno}: chosen.{field} != rejected.{field} "
                    f"(same-context purity violation)"
                )
    return errors
```

The block above is a *reference implementation* for reviewers — there is no
importable `docs.preference_isolation` module; this repo keeps executable
code under `pipelines/`. The equivalent gate that actually runs is the
read-only scan in `pipelines/curate_preferences.py`, which applies the same
canonical `state` / `proposed_action` equality:

```
python3 pipelines/curate_preferences.py scan <batch-or-staging-dir> --json
```

Its `summary.impure_pairs` counts same-context violations, and each impure
`decisions[]` entry names the offending `source_line`, `reason_codes`
(e.g. `STATE_CONTEXT_DIVERGES`) and `context_diff_paths`.

Run it in CI before `round_txn.py publish` and gate on
`summary.unpublishable_pairs`, which must be 0. Gate on that field rather
than on `impure_pairs`: `impure_pairs` deliberately counts only the four
context-divergence and comparability buckets, so that the published
same-context audit stays truthful. A pair can have equal, fully comparable
context and still be unusable -- a non-finite `reward_delta`, for instance,
is excluded by the curator while leaving `impure_pairs` at 0.
`unpublishable_pairs` counts every pair that is impure *or* unemittable, so
neither kind of defect can reach a published round.

That CI step is an audit preview. Publication independently re-runs the
canonical equality through `preference_arms.py`; skipping this preview
cannot bypass the publisher.

`summary` also splits the violations by field — `state_divergent_pairs`,
`proposed_action_divergent_pairs`, and `proposed_action_only_divergent_pairs`
— so a state-only audit can be reconciled against this gate. A published
worked example of that reconciliation, with the per-pair ID list and reason
codes, is [`ffpc-same-state-audit.md`](ffpc-same-state-audit.md):

```
python3 pipelines/curate_preferences.py audit <source> --markdown
python3 pipelines/curate_preferences.py audit <source> --expect docs/ffpc-same-state-audit.json
python3 pipelines/curate_preferences.py reconcile <source-a> <source-b>
```

The audit embeds a relative-path plus whole-file SHA-256 inventory. Both
`audit --expect` and `reconcile` therefore cover retained pairs, skipped JSON
records, non-preference-only files, line endings, and trailing blank lines in
addition to the per-pair decisions.

### 3.4 Failure taxonomy

| Class | Example | Detection |
|---|---|---|
| **State drift** | `rejected.state.environment.patient.mrn` differs from `chosen` | `deep_equal` on `state` fails |
| **Action drift** | `proposed_action.content` reworded to be easier | `deep_equal` on `proposed_action` fails |
| **Timestamp skew** | `state.timestamp_local` shifted by 1s | `deep_equal` fails (timestamps are part of state) |
| **Missing field** | `chosen.proposed_action` has extra `tool` that `rejected` lacks | `deep_equal` fails (key sets differ) |
| **Type coercion** | `state.sim_or_real` string vs missing | Gate reports missing field |

### 3.5 Repair procedure on gate failure

1. Identify the violating `field` and line.
2. Repair **only staged files** — never hand-edit a committed raw file.
3. Make `chosen` match `rejected` on `state`/`proposed_action` (or vice
   versa if the diagnosis intent was to keep the original problem). Do not
   weaken the problem to make the repair easier.
4. Re-run `check_purity` and `pipelines/check_records.py` before re-attempting
   `round_txn.py publish`.

### 3.6 Independent-arm gate

Same-context purity says the two arms share a problem. It says nothing about
whether they are two independent answers. A Session B that restated the
rejected arm — same gate decision, same execution, same outcome, a synonym
swapped in the rationale — passes Section 3 and still teaches nothing.

`pipelines/preference_arms.py` closes that hole:

```
python3 pipelines/preference_arms.py scan <staging_dir-or-batch> --json
```

The command is a read-only preview; it exits non-zero when any pair is blocked,
and it fails closed when a source contains no preference pairs at all. For new
FFPC rounds, `round_txn.py publish` invokes the same check against captured
bytes, requires the reservation's orchestrator-issued isolation assertion, and
records a path-independent gate result in the v2 completion marker.

**What it measures.** For each side it builds an allowlisted behavioral
*contrast surface*: `executed_action`, `future_outcome`, and `spike_events`.
Shared context, safety prose, IDs, metadata, provenance labels, reward labels,
and unknown extension fields cannot manufacture distance. Unknown top-level
arm fields block the pair.
Each surface becomes a path-scoped term-frequency vector: string leaves
contribute normalized lexical terms, non-string leaves stay atomic so `0.2`
and `-0.2` never collide, and list positions are collapsed so a reordered list
is not a different arm.
Each observable path is scored on its own vector and the results are averaged
with equal weight:

```
arm_distance = 1 - mean(
    cosine_similarity(terms(chosen, path), terms(rejected, path))
    for path in observable_paths
)
```

Weighting paths rather than pooling every term into one vector is what keeps
the floor comparable across records: pooled, a long run of identical spike
telemetry outvoted a changed `executed_action`, so whether a real contrast
cleared the floor depended on how many events the record happened to carry.

This is a deterministic, stdlib-only lexical metric, not an embedding-model
surrogate. Its independent, fixture-calibrated default floor is 0.03; the
separate corpus near-duplicate threshold in `quality_gate.py` makes no claim
of metric equivalence. Floats are quantized to twelve significant digits, so
arithmetic noise on an otherwise copied arm is not a delta. Compatibility
decomposition removes accent-only inflation, common Greek/Cyrillic homoglyphs
are folded, a word whose letters mix scripts is refused as an ambiguous
skeleton rather than normalized, an identifier that swaps script between the
arms is not a delta, and invisible Unicode
format marks cannot split visible words. Other non-ASCII letters and digits
are emitted as code-point terms so unspaced CJK edits are measured
proportionally. A structural check also rejects arms whose only behavioral
contrast is `safety_decision.decision`; reward-only changes remain
near-verbatim. Independently of the lexical score, at least one scalar or
bounded identifier leaf present in both arms must differ under
`executed_action`, `future_outcome`, or `spike_events`; one-sided nested
padding and free-form rationale edits cannot satisfy that invariant. Observed
distance on an honest two-session round
runs ~0.7; `--min-distance` tightens the preview when a round wants more
headroom than "not a copy".

**Reason codes.**

| Code | Meaning |
|---|---|
| `PREFERENCE_PAIR_MALFORMED` | `chosen`/`rejected` are not both objects |
| `PREFERENCE_CONTEXT_DIVERGES` | Section 3 violation (delegated to `curate_preferences.context_is_pure`) |
| `PREFERENCE_ARMS_NEAR_VERBATIM` | `arm_distance <= --min-distance`: one arm restated, not repaired |
| `PREFERENCE_ARM_CONTRAST_EMPTY` | An arm carries no contrastive content at all |
| `PREFERENCE_ARMS_ISOLATION_UNDECLARED` | No `meta.isolation` on the record or either arm |
| `PREFERENCE_ARMS_ISOLATION_CONFLICT` | Record and arms disagree about how the pair was generated |
| `PREFERENCE_ARMS_SINGLE_SESSION_PATH` | The attestation names the deprecated single-context path |
| `PREFERENCE_ARMS_ISOLATION_UNTRUSTED` | Publication lacks the reservation's orchestrator-issued two-session assertion |
| `PREFERENCE_ARMS_LABEL_ONLY_COPY` | Removing the gate decision label leaves identical observable behavior; reward relabeling cannot clear it |
| `PREFERENCE_ARM_EXTENSION_FIELDS` | An arm carries an unknown top-level field that could manufacture lexical distance |
| `PREFERENCE_ARMS_OBSERVABLES_IDENTICAL` | No shared machine-observable leaf differs; prose edits or one-sided nested padding are not independent behavior |

**Repair on failure.** A near-verbatim pair is not a formatting defect — it
means Session B did not actually reason from the diagnosis. Re-run Session B
from a fresh context against the same diagnosis; never hand-widen the two
arms to clear the floor.

## 4. End-to-end example (round r05)

```
# Content-blind controller reservation (before either arm-producing session)
# reserve returns an absolute staging_dir; verify-handoff requires one, so
# capture it rather than rebuilding the path by hand.
STAGE=$(python3 pipelines/round_txn.py reserve outputs/raw/2026-08-17/failure-as-fuel-preference-cascade --round 5 --expected 3 --preference-isolation two-session | jq -r .staging_dir)
# → $STAGE = /<repo>/outputs/staging/2026-08-17/failure-as-fuel-preference-cascade/r05-<token>

# Session A: write failures + diagnoses
#   $STAGE/rejected-01-r05.json
#   $STAGE/rejected-02-r05.json
#   $STAGE/rejected-03-r05.json
#   $STAGE/diagnosis-01-r05.md
#   $STAGE/diagnosis-02-r05.md
#   $STAGE/diagnosis-03-r05.md

# Separate read-only context: bind the only files Session B may open
python3 pipelines/preference_arms.py verify-handoff "$STAGE" \
  --file diagnosis-01-r05.md --file diagnosis-02-r05.md \
  --file diagnosis-03-r05.md --write-receipt
# → diagnosis-handoff-receipt-r05.json (required and revalidated by publish)

# Session B (fresh context): read only diagnosis-*-r05.md, synthesize chosen
#   $STAGE/batch-r05.jsonl      (3 preference records)
#   $STAGE/NOTES-r05.md

# Validate
python3 pipelines/check_records.py "$STAGE"
python3 pipelines/curate_preferences.py scan "$STAGE/batch-r05.jsonl" --json
# purity gate: summary.unpublishable_pairs must be 0
# (impure_pairs alone misses equal-context pairs the curator cannot emit)
python3 pipelines/preference_arms.py scan "$STAGE/batch-r05.jsonl"
# preview: must exit 0 (publish re-runs it against captured bytes)

# Publish
python3 pipelines/round_txn.py publish outputs/raw/2026-08-17/failure-as-fuel-preference-cascade --round 5 --token <token>
# → outputs/raw/2026-08-17/failure-as-fuel-preference-cascade/batch-r05.jsonl
# → outputs/raw/2026-08-17/failure-as-fuel-preference-cascade/diagnosis-*-r05.md
# → outputs/raw/2026-08-17/failure-as-fuel-preference-cascade/NOTES-r05.md
# → outputs/raw/2026-08-17/failure-as-fuel-preference-cascade/ROUND-r05.complete.json
```

## 5. Compliance notes

- The factory contract's `Reward total reconciles` and `spike_events
  globally non-decreasing` checks apply independently to both `chosen` and
  `rejected` trajectories inside each preference record.
- The diagnosis files are retained on publish as round artifacts; they
  document the repair rationale for audit and for training the next round's
  densification.
- Every published record carries `meta.isolation: "two-session"`, and the
  reservation separately carries the orchestrator-issued protocol assertion.
  `round_txn.py publish` requires both, runs the same-context and independent-
  arm decisions, and stores their deterministic summary in the completion
  marker. The launcher obtains that reservation in a separate content-blind
  context. An arm-payload-blind verifier parses the bounded diagnosis envelope,
  refuses every artifact Session A is not the author of immediately before and
  after its exclusive receipt write -- an allowlist of `diagnosis-NN-rNN.md`
  and `rejected-NN-rNN.json`, so no other spelling can carry chosen-side
  output into a stage the receipt then certifies as pre-Session-B -- and binds
  the exact allowlist, regular-file type, bytes, sizes, and
  SHA-256 digests before opening Session B. This is auditable orchestration
  evidence, not a cryptographic attestation of what happened inside an external
  model session; a manual operator invoking the reserve command is explicitly
  making the same protocol assertion. Read-only receipt and publishing-plan
  modes make accidental mutation visible, but do not defend against the same OS
  user deliberately changing permissions, rewriting content, and resealing it.
  The receipt file and staging-directory `fsync` are the ordering point: a
  Session-B output created after that point is later than the receipt even if
  the verifier has not yet returned its bounded JSON summary. Final inode/path
  checks catch accidental overlap before cleanup; they cannot make an
  owner-writable directory immutable against a hostile same-user process that
  deliberately mutates it after the last check.
- No generated content is ever written directly into `outputs/raw/`; all
  writes go through the reserved `staging_dir` and are atomically linked
  on `publish`.

---
Co-author: Muse Code powered by Muse Spark
