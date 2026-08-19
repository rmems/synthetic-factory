# Preference Isolation — Two-Session Generation & Same-Context Purity Gate

> Factory: `failure-as-fuel-preference-cascade` (sf-cic)  
> Co-author: Muse Code powered by Muse Spark  
> Contract: `prompts/_factory-contract.md` · Prompt: `prompts/05-failure-as-fuel-preference-cascade.md`

## 1. Purpose

Preference training (DPO / ORPO / safety distillation) is only meaningful
when the `chosen` vs `rejected` contrast isolates **gate and execution
quality** rather than a changed problem. If the two sides propose different
tasks, different states, or different tool calls, the learner can exploit
the easier problem instead of the better judgment.

This document defines the **two-session isolation protocol** and the
**same-context purity gate** that together enforce that property for every
round of `failure-as-fuel-preference-cascade`.

## 2. Two-session generation

A single `pipelines/round_txn.py reserve` call creates one `staging_dir`
for the round. Both sessions operate inside that directory, but they MUST
NOT share generation context.

```
reserve  ──►  Session A (rejected + diagnosis)  ──►  Session B (chosen from diagnosis)
                │                                     │
                ▼                                     ▼
           rejected-rNN-0i.json                   batch-rNN.jsonl (chosen+rejected)
           diagnosis-rNN-0i.md                    NOTES-rNN.md
                                                  diagnosis-rNN-0i.md (retained)
```

### 2.1 Session A — Rejected + Diagnosis

| Aspect | Requirement |
|---|---|
| **Input** | Round number, quota (3), factory contract, prior round notes |
| **Output** | 3 scratch `rejected` artifacts + 3 diagnosis files |
| **Forbidden** | Any `chosen` trajectory, any outline of the repair beyond the diagnosis sketch |
| **Diagnosis per record** | Root cause, cascade effects, supervisor-catch, repair sketch |
| **Batch file** | MUST NOT be written yet |

Scratch rejected artifacts are staged as `rejected-rNN-01.json` (or
`rejected-rNN.jsonl`) — one ThalamicTrajectory JSON object per file/line —
so they satisfy the `artifact_re` allowlist (`*-rNN.(md|json|txt)`) and are
publishable, but they are not the final batch.

Each `diagnosis-rNN-0i.md` must be self-contained: a reader who has never
seen the rejected JSON can reconstruct the intended repair from the
diagnosis alone. It must not paste the full rejected trajectory — only a
narrative repair sketch.

### 2.2 Session B — Chosen from Diagnosis Only

| Aspect | Requirement |
|---|---|
| **Input** | `diagnosis-rNN-0i.md` files ONLY (plus the `state`/`proposed_action` they describe) |
| **Forbidden** | Reading `rejected-rNN*.json`, copying rejected JSON, or reusing Session A context |
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

### 2.3 Session handoff checklist

- [ ] Session A produced exactly 3 diagnoses and 3 rejected scratch files
- [ ] No `batch-rNN.jsonl` exists after Session A
- [ ] Session B context was reset (new conversation / cleared history)
- [ ] Session B did not open any `rejected-rNN*.json` file
- [ ] Final `batch-rNN.jsonl` has exactly 3 lines, each with `chosen` + `rejected` + non-empty `critique`
- [ ] Same-context purity gate passes (Section 3)
- [ ] `NOTES-rNN.md` names residual weaknesses and next densification target

## 3. Same-context purity gate

### 3.1 Definition

For every preference record `r` in `batch-rNN.jsonl`:

```
r.chosen.state  == r.rejected.state          (deep JSON equality)
r.chosen.proposed_action == r.rejected.proposed_action
```

- Equality is **deep structural equality** of JSON values: objects are
  equal irrespective of key order; arrays are order-sensitive; numbers are
  compared by value; strings by exact content.
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

The gate is enforced at `publish` time by `pipelines/check_records.py` and
`pipelines/validate_run.py` shape checks plus the additional same-context
equality check below. A round that fails this gate is not training-ready.

Reference implementation (pure Python, no external deps):

```python
import json, pathlib

def is_number(x) -> bool:
    # JSON numbers only: bool is a subclass of int and is NOT a number here.
    return isinstance(x, (int, float)) and not isinstance(x, bool)

def deep_equal(a, b) -> bool:
    if type(a) is not type(b):
        # JSON numbers: int vs float with same value are equal;
        # True/1 and False/0 are never equal (bool excluded above).
        if is_number(a) and is_number(b):
            return float(a) == float(b)
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
(e.g. `STATE_CONTEXT_DIVERGES`) and `context_diff_paths`. Run it in CI before
`round_txn.py publish`; any non-zero `impure_pairs` blocks publication.

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

## 4. End-to-end example (round r05)

```
# One-time reservation (covers both sessions)
python3 pipelines/round_txn.py reserve outputs/raw/2026-08-17/failure-as-fuel-preference-cascade --round 5 --expected 3
# → staging_dir = outputs/staging/2026-08-17/failure-as-fuel-preference-cascade/r05-<token>

# Session A: write failures + diagnoses
#   staging/r05-<token>/rejected-r05-01.json
#   staging/r05-<token>/rejected-r05-02.json
#   staging/r05-<token>/rejected-r05-03.json
#   staging/r05-<token>/diagnosis-r05-01.md
#   staging/r05-<token>/diagnosis-r05-02.md
#   staging/r05-<token>/diagnosis-r05-03.md

# Session B (fresh context): read only diagnosis-r05-*.md, synthesize chosen
#   staging/r05-<token>/batch-r05.jsonl      (3 preference records)
#   staging/r05-<token>/NOTES-r05.md

# Validate
python3 pipelines/check_records.py outputs/staging/2026-08-17/failure-as-fuel-preference-cascade/r05-<token>
python3 pipelines/curate_preferences.py scan outputs/staging/2026-08-17/failure-as-fuel-preference-cascade/r05-<token>/batch-r05.jsonl --json
# purity gate: summary.impure_pairs must be 0

# Publish
python3 pipelines/round_txn.py publish outputs/raw/2026-08-17/failure-as-fuel-preference-cascade --round 5 --token <token>
# → outputs/raw/2026-08-17/failure-as-fuel-preference-cascade/batch-r05.jsonl
# → outputs/raw/2026-08-17/failure-as-fuel-preference-cascade/diagnosis-r05-*.md
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
- No generated content is ever written directly into `outputs/raw/`; all
  writes go through the reserved `staging_dir` and are atomically linked
  on `publish`.

---
Co-author: Muse Code powered by Muse Spark
