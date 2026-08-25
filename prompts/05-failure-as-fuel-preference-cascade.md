## Session bootstrap

- Factory slug: `failure-as-fuel-preference-cascade`
- Shared rules: `prompts/_factory-contract.md`
- Reserve, stage, validate, and publish only through `pipelines/round_txn.py`
- Never write generated content directly into `outputs/raw/`
- `state.sim_or_real` ∈ {designed, simulated, hil}; invented plants are designed
- Never emit `real`; see `schemas/provenance.md`

You are the Failure-as-Fuel Preference Cascade Factory.

This factory uses a **two-session isolated generation protocol** (see
`docs/preference-isolation.md` for the full purity-gate specification).
The two sessions MUST be executed in order and MUST NOT share generation
context beyond the diagnosis artifacts. A single `round_txn.py reserve`
covers both sessions — they operate on the same `staging_dir`.

**The single-session path is DEPRECATED.** Generating failure, diagnosis,
and repair in one context produces correlated arms — the repair becomes the
negation of the failure it just wrote — and that is the collapse vector this
factory exists to avoid. No new round may be produced that way. Every
record attests `meta.isolation: "two-session"`, and
`pipelines/preference_arms.py` blocks a round that cannot produce that
attestation or whose two arms are one arm restated.

**Execution note (automated launcher):** under
`.claude/skills/run-synthetic-factory/factory-window.workflow.js`, Session A
and Session B run as two separate workflow agents with independent
generation contexts — Session A reserves and stages failures + diagnoses,
Session B (a fresh agent that receives only the staging path, reserve token,
and diagnosis filenames) synthesizes `chosen`, assembles, and publishes.
Never run both sessions inside one generation context; each record's
`meta.isolation` must be set to `"two-session"`.

---

## Two-session isolation protocol

### Session A — Rejected + Diagnosis (failure mining)

**Goal:** produce the `rejected` sides and their diagnoses. No `chosen`
trajectory is produced in this session.

1. After `reserve`, Session A owns the `staging_dir`. Create per-record
   diagnosis files. Publish's `artifact_re` allowlist accepts only names
   **ending in `-rNN.md|json|txt`** (and rejects every extra `.jsonl`), so
   the record index goes BEFORE the round suffix:
   - `diagnosis-01-rNN.md`, `diagnosis-02-rNN.md`, `diagnosis-03-rNN.md`
     (where `NN` is the zero-padded round number from the reservation,
     e.g. round 5 → `diagnosis-01-r05.md`).
   - Alternatively a single `diagnosis-rNN.md` with clearly delimited
     `## Record 01` / `## Record 02` / `## Record 03` sections is accepted
     if the three sections are independently parseable. The per-file form is
     preferred.

2. For each of the exactly 3 preference records, author one deliberately
   imperfect / failed / hallucinated / unsafe / inefficient `rejected`
   ThalamicTrajectory. Failures must be realistic and educational (wrong
   tool use, ignored safety, incomplete evidence, context loss, reward
   hacking, format-as-provenance, deadline-miss optimistic accept, etc.).
   - Keep each trajectory on one unchanged `state` + `proposed_action`
     pair so the later preference contrast is causally meaningful.
   - Record the full trajectory in a **scratch artifact** inside the
     staging dir: `rejected-01-rNN.json`, `rejected-02-rNN.json`,
     `rejected-03-rNN.json` (one JSON object per file). These names match
     the `artifact_re` allowlist (`^[A-Za-z0-9][A-Za-z0-9._-]*-rNN\.(md|json|txt)$`)
     and will be linked on publish but are NOT the final batch. Never use
     a `.jsonl` scratch file — publish rejects any `.jsonl` other than the
     reserved batch.

3. For each rejected trajectory, write its diagnosis to the corresponding
   indexed file (`diagnosis-01-rNN.md`, `diagnosis-02-rNN.md`, or
   `diagnosis-03-rNN.md`). Each diagnosis MUST contain:
   - **Shared context** — the exact `state` and `proposed_action` JSON of
     the rejected trajectory, embedded verbatim as a fenced JSON block.
     This block (and only this block) is what Session B copies
     byte-identically into `chosen`; the rejected trajectory's
     `safety_decision`, `executed_action`, `future_outcome`, and
     `reward_components` MUST NOT appear in the diagnosis.
   - **Root cause** — the single load-bearing error in the trajectory
     (gate, execution, or reasoning).
   - **Cascade effects** — how the error propagates through
     `safety_decision` → `executed_action` → `future_outcome` →
     `reward_components`.
   - **Supervisor catch** — what a correct Thalamic gate should have
     checked, constrained, or denied, and the concrete evidence it would
     have needed.
   - **Repair sketch** — the minimal change that a correct `chosen`
     trajectory must make (new checks, fallback, constraint injection,
     refusal, deferred verification, etc.) WITHOUT pasting the full
     rejected JSON. The sketch is the only bridge Session B may read.
   - **Target reward delta** — the *intended* improvement for the
     preference pair: a `per_component` map plus `total` with
     `total == sum(per_component values)` within `1e-6`. This is a
     design target for Session B's repair, not the published value: the
     final record's `reward_delta` is computed by Session B at assembly
     time as `chosen − rejected` per component (the only point at which
     both trajectories exist), and must reconcile the same way with
     `chosen.total > rejected.total`.

4. Session A ends after the 3 `rejected` scratch artifacts and 3 diagnosis
   files are present. **Do NOT write `batch-rNN.jsonl` yet.** Validate
   locally with `pipelines/check_records.py` on the scratch files if
   desired, but do not publish.

**Session A isolation rule:** Session A MUST NOT draft, outline, or
pre-generate any `chosen` content. Its output is failures + diagnoses only.

### Session B — Chosen from Diagnosis Only (repair synthesis)

**Goal:** produce the `chosen` sides and the final preference batch using
ONLY the diagnosis files as input. Session B MUST NOT read the `rejected`
scratch artifacts.

1. Start a **fresh generation context** (new model session / new
   conversation). Session B reads ONLY `diagnosis-01-rNN.md`,
   `diagnosis-02-rNN.md`, and `diagnosis-03-rNN.md` —
   nothing else from Session A. Allowed bridge: diagnosis narrative
   (root cause, cascade effects, supervisor catch, repair sketch, target
   reward delta) and the **Shared context** block's exact
   `state`/`proposed_action` JSON. Forbidden inputs:
   `rejected-01-rNN.json` / `rejected-02-rNN.json` / `rejected-03-rNN.json`
   scratch files, any file containing the full
   rejected trajectory, and any `safety_decision` rationale text copied
   verbatim. If the diagnosis references the rejected trajectory, it
   does so only through the repair-sketch narrative plus the shared
   context block, never through the rejected gate/execution/outcome
   JSON or copied safety text.

2. For each diagnosis, synthesize one fully repaired gold-standard
   `chosen` ThalamicTrajectory that:
   - Shares **byte-identical** `state` and `proposed_action` with the
     rejected trajectory it pairs with (see Same-Context Purity Gate
     below). Copy them verbatim from the diagnosis's **Shared context**
     JSON block — do not invent a new problem to make the fix easier.
   - Implements the diagnosis's repair sketch (correct checks, fallbacks,
     refusals, attestation, deadline-aware defaults, constraint
     injections, etc.) WITHOUT copying `safety_decision` rationale text
     verbatim from the diagnosis — synthesize original safety rationale
     that reflects the repaired gate's actual checks and evidence.
   - Earns a higher `reward_components.total` via the same declared
     aggregation, reconciled numerically, aiming for the diagnosis's
     target reward delta.

3. Assemble the final staged batch:
   - `batch-rNN.jsonl` — exactly 3 top-level preference records, one JSON
     object per line, no fences or prose. Each record embeds:
     ```json
     {"id": "...", "chosen": {ThalamicTrajectory}, "rejected": {ThalamicTrajectory}, "critique": "...", "reward_delta": {...}}
     ```
     `chosen` is from Session B; `rejected` is the Session A trajectory
     embedded verbatim — **mechanically, via a script** (e.g. a short
     `python3` snippet that json-loads each `rejected-01-rNN.json` /
     `rejected-02-rNN.json` / `rejected-03-rNN.json` and
     injects it into the assembled record) so the published batch is
     self-contained WITHOUT the rejected content ever entering Session
     B's generation context; `reward_delta` is computed at this assembly
     step as `chosen − rejected` per component (script-computed, with
     `total == sum(per_component)` within `1e-6`). Set
     `meta.isolation: "two-session"` on each record. Phase 1 and Phase 2
     do not add extra top-level JSONL lines.
   - `NOTES-rNN.md` — self-critique: residual weaknesses and the next
     round's densification target.
   - Retain the `diagnosis-01-rNN.md` / `diagnosis-02-rNN.md` /
     `diagnosis-03-rNN.md` files alongside the batch — they are
     part of the published round and document the repair rationale.

4. Run the **same-context purity gate** and the **independent-arm gate**
   (see `docs/preference-isolation.md`) over `batch-rNN.jsonl` before
   publishing. If any pair fails, repair only staged files; never hand-edit
   a committed raw file. A near-verbatim arm pair is not a formatting
   defect — re-synthesize that `chosen` from the diagnosis instead of
   padding it to clear the floor.

**Session B isolation rule:** Session B MUST NOT read `rejected-01-rNN.json`,
`rejected-02-rNN.json`, or `rejected-03-rNN.json` (or any file containing
the full rejected trajectory) into its generation
context, and MUST NOT copy `safety_decision` / safety rationale text
verbatim from the diagnosis or rejected artifacts. It reconstructs the
`chosen` solely from the diagnosis narrative + the shared
`state`/`proposed_action`, synthesizing fresh safety text for the
repaired trajectory. The only permitted contact with the rejected files
is the mechanical assembly script in step 3, whose output is written
directly to `batch-rNN.jsonl` without being read back. This prevents
leakage where the repair merely negates the rejected text or copies
safety wording rather than reasoning from the diagnosis.

---

## Same-context purity gate (summary)

Preference `chosen` and `rejected` MUST satisfy:

- `chosen.state` deeply equals `rejected.state`
- `chosen.proposed_action` deeply equals `rejected.proposed_action`

as JSON values (key order irrelevant, value equality strict). The contrast
must teach gate/execution/recovery quality, not reward a changed problem.
See `docs/preference-isolation.md` for the canonical validator and the
failure taxonomy. **Enforcement:** reserve this factory with
`--preference-isolation two-session`. `round_txn.py publish` then runs the
canonical same-context and independent-arm checks against captured staged
bytes before linking the completion marker. The commands below are useful
previews, and post-publish `pipelines/curate_preferences.py` plus
`pipelines/training_audit.py` remain independent audits, but skipping a
preview cannot bypass publication.

## Independent-arm gate (summary)

Same context is necessary but not sufficient: two arms that share a problem
can still be one arm restated. `pipelines/preference_arms.py` requires that
each pair's contrast surface (everything except `state`, `proposed_action`,
`id`, and `meta`) sit more than the arm-distance floor apart, and that the
record attest `meta.isolation: "two-session"`. See
`docs/preference-isolation.md` §3.6 for the lexical metric and reason codes.
Publication additionally requires the two-session value from the reservation;
mutable record metadata is not trusted as proof of the protocol.

## Purity check command

Run from the repo root after assembling `batch-rNN.jsonl` and before
`round_txn.py publish` — replace `<staging_dir>` with the reserved staging
path and `rNN` with the zero-padded round (e.g. `r05`):

```bash
# 1. Standard record checks (schema, reward arithmetic, spike order)
python3 pipelines/check_records.py <staging_dir>

# 2. Same-context purity gate + safety-text isolation check
python3 -c "
import json, pathlib, sys

batch = pathlib.Path('<staging_dir>/batch-rNN.jsonl')
diags = sorted(pathlib.Path('<staging_dir>').glob('diagnosis-*-rNN.md'))
if not diags:
    single = pathlib.Path('<staging_dir>/diagnosis-rNN.md')
    diags = [single] if single.exists() else []
if not diags:
    # Fail CLOSED: no diagnosis files means the glob is wrong (un-replaced
    # rNN?) or Session A never ran — the safety-text check cannot be skipped.
    print('purity gate: FAIL — no diagnosis files matched; check the rNN substitution', file=sys.stderr)
    sys.exit(1)
diag_text = '\n'.join(p.read_text() for p in diags)

def deep_equal(a, b):
    # bool is a subclass of int: True == 1 must NOT count as equal.
    if isinstance(a, bool) != isinstance(b, bool):
        return False
    if type(a) != type(b):
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return float(a) == float(b)
        return False
    if isinstance(a, dict):
        return set(a) == set(b) and all(deep_equal(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(deep_equal(x, y) for x, y in zip(a, b))
    return a == b

errors = []
for lineno, line in enumerate(batch.read_text().splitlines(), 1):
    if not line.strip():
        continue
    r = json.loads(line)
    chosen, rejected = r.get('chosen'), r.get('rejected')
    if not isinstance(chosen, dict) or not isinstance(rejected, dict):
        errors.append(f'line {lineno}: chosen/rejected must both be objects')
        continue
    for field in ('state', 'proposed_action'):
        a, b = chosen.get(field), rejected.get(field)
        if a is None or b is None:
            errors.append(f'line {lineno}: missing chosen/rejected.{field}')
        elif not deep_equal(a, b):
            errors.append(f'line {lineno}: chosen.{field} != rejected.{field} (same-context purity violation)')
    # isolation: chosen safety rationale must not be verbatim copy from diagnosis
    sd = chosen.get('safety_decision')
    chosen_rationale = sd.get('rationale', '') if isinstance(sd, dict) else ''
    if chosen_rationale and chosen_rationale.strip() in diag_text:
        errors.append(f'line {lineno}: chosen.safety_decision.rationale appears verbatim in diagnosis (copy safety text violation)')

if errors:
    print('\n'.join(errors), file=sys.stderr)
    sys.exit(1)
else:
    print('purity gate: PASS (same-context + no safety-text copy)')
"
```

```bash
# 3. Independent-arm gate: arms must not be one arm restated, and each
#    record must attest the two-session protocol
python3 pipelines/preference_arms.py scan <staging_dir>/batch-rNN.jsonl
```

All three preview steps must exit 0 before publish, and publish independently
re-runs the same-context plus arm gate over captured bytes. Fix violations by editing only
staged files (make `chosen.state`/`proposed_action` byte-identical to
`rejected`, and rewrite chosen safety rationale in original wording); never
hand-edit committed raw files. `PREFERENCE_ARMS_NEAR_VERBATIM` is repaired
by re-synthesizing that `chosen` from its diagnosis in a fresh context, not
by widening the wording until the floor clears. A
`PREFERENCE_ARMS_LABEL_ONLY_COPY` finding likewise requires a substantive
execution, evidence, or outcome contrast rather than a different gate label.

---

## Additional constraints

- The staged batch contains exactly 3 top-level preference records. Each
  embeds one `chosen` and one `rejected` ThalamicTrajectory; Phase 1 and
  Phase 2 do not add extra top-level JSONL lines.
- Use more nuanced near-miss failures in later committed rounds. Keep each
  current preference pair on one unchanged state and proposed action so the
  chosen/rejected contrast is causally meaningful for DPO/ORPO and safety
  distillation.
- Every ThalamicTrajectory follows `schemas/thalamic-trajectory-v2.schema.json`
  (object-valued `state`, `proposed_action`, `safety_decision`,
  `executed_action`, `future_outcome`, `reward_components`; finite
  `spike_events` timestamps globally non-decreasing; `reward_components.total`
  reconciled; `safety_decision.decision` ∈ {ACCEPT, MODIFY, REJECT} with
  concrete rationale).
- Auxiliary artifacts must be `*-rNN.md|json|txt` inside the staging dir.

---
Co-author: Muse Code powered by Muse Spark
