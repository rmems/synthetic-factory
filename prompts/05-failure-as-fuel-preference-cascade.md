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

---

## Two-session isolation protocol

### Session A — Rejected + Diagnosis (failure mining)

**Goal:** produce the `rejected` sides and their diagnoses. No `chosen`
trajectory is produced in this session.

1. After `reserve`, Session A owns the `staging_dir`. Create per-record
   diagnosis files:
   - `diagnosis-rNN-01.md`, `diagnosis-rNN-02.md`, `diagnosis-rNN-03.md`
     (where `NN` is the zero-padded round number from the reservation,
     e.g. `r05` → `diagnosis-r05-01.md`).
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
     staging dir, e.g. `rejected-rNN-0i.json` (one JSON object per file)
     or `rejected-rNN.jsonl` (one JSON per line). These scratch files
     MUST match the `artifact_re` allowlist (`*-rNN.json`) and will be
     linked on publish but are NOT the final batch.

3. For each rejected trajectory, write its diagnosis to the corresponding
   `diagnosis-rNN-0i.md`. Each diagnosis MUST contain:
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
   - **Reward delta** — the expected `reward_delta` for the preference
     pair: a `per_component` map plus `total` where `chosen.total >
     rejected.total`, `total == sum(per_component values)` within `1e-6`,
     and each per-component delta equals `chosen.<comp> -
     rejected.<comp>`. This delta is authored in Session A as part of
     the diagnosis and carried verbatim into the final
     `batch-rNN.jsonl` record's `reward_delta` (Session B MUST NOT
     re-derive or alter it, only copy it).

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
   conversation). Session B reads ONLY `diagnosis-rNN-0i.md` files plus
   the shared `state` + `proposed_action` pair they describe — nothing
   else from Session A. Allowed bridge: diagnosis narrative (root cause,
   cascade effects, supervisor catch, repair sketch, reward delta) and
   the `state`/`proposed_action` JSON implied by the diagnosis.
   Forbidden inputs: `rejected-rNN*.json` / `rejected-rNN.jsonl`, any
   file containing the full rejected trajectory, and any
   `safety_decision` rationale text copied verbatim. If the diagnosis
   references the rejected trajectory, it does so only through the
   repair-sketch narrative, not through copied JSON or copied safety
   text.

2. For each diagnosis, synthesize one fully repaired gold-standard
   `chosen` ThalamicTrajectory that:
   - Shares **byte-identical** `state` and `proposed_action` with the
     rejected trajectory it pairs with (see Same-Context Purity Gate
     below). Copy the `state`/`proposed_action` from the diagnosis's
     description — do not invent a new problem to make the fix easier.
   - Implements the diagnosis's repair sketch (correct checks, fallbacks,
     refusals, attestation, deadline-aware defaults, constraint
     injections, etc.) WITHOUT copying `safety_decision` rationale text
     verbatim from the diagnosis — synthesize original safety rationale
     that reflects the repaired gate's actual checks and evidence.
   - Earns a higher `reward_components.total` via the same declared
     aggregation, reconciled numerically; the `reward_delta` itself is
     already authored in the diagnosis (Session A) and MUST be carried
     verbatim — do not re-derive it.

3. Assemble the final staged batch:
   - `batch-rNN.jsonl` — exactly 3 top-level preference records, one JSON
     object per line, no fences or prose. Each record embeds:
     ```json
     {"id": "...", "chosen": {ThalamicTrajectory}, "rejected": {ThalamicTrajectory}, "critique": "...", "reward_delta": {...}}
     ```
     `chosen` is from Session B; `rejected` is the Session A trajectory
     re-embedded verbatim (deep copy from the scratch artifact) so that
     the published batch is self-contained; `reward_delta` is the Session A
     diagnosis value carried verbatim (Session B copies it without
     re-derivation). Phase 1 and Phase 2 do not add extra top-level JSONL
     lines.
   - `NOTES-rNN.md` — self-critique: residual weaknesses and the next
     round's densification target.
   - Retain the `diagnosis-rNN-*.md` files alongside the batch — they are
     part of the published round and document the repair rationale.

4. Run the **same-context purity gate** (see `docs/preference-isolation.md`)
   over `batch-rNN.jsonl` before publishing. If any pair fails, repair
   only staged files; never hand-edit a committed raw file.

**Session B isolation rule:** Session B MUST NOT open `rejected-rNN*.json`
/ `rejected-rNN.jsonl` or any file containing the full rejected
trajectory, and MUST NOT copy `safety_decision` / safety rationale text
verbatim from the diagnosis or rejected artifacts. It reconstructs the
`chosen` solely from the diagnosis narrative + the shared
`state`/`proposed_action`, synthesizing fresh safety text for the
repaired trajectory. This prevents leakage where the repair merely negates
the rejected text or copies safety wording rather than reasoning from the
diagnosis.

---

## Same-context purity gate (summary)

Preference `chosen` and `rejected` MUST satisfy:

- `chosen.state` deeply equals `rejected.state`
- `chosen.proposed_action` deeply equals `rejected.proposed_action`

as JSON values (key order irrelevant, value equality strict). The contrast
must teach gate/execution/recovery quality, not reward a changed problem.
See `docs/preference-isolation.md` for the canonical validator and the
failure taxonomy. The gate is enforced at `publish` time by the staged
batch validator; a round with a same-context violation is not training-ready.

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
diags = sorted(pathlib.Path('<staging_dir>').glob('diagnosis-rNN-*.md'))
if not diags:
    single = pathlib.Path('<staging_dir>/diagnosis-rNN.md')
    diags = [single] if single.exists() else []
diag_text = '\n'.join(p.read_text() for p in diags)

def deep_equal(a, b):
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
    for field in ('state', 'proposed_action'):
        a, b = r.get('chosen', {}).get(field), r.get('rejected', {}).get(field)
        if a is None or b is None:
            errors.append(f'line {lineno}: missing chosen/rejected.{field}')
        elif not deep_equal(a, b):
            errors.append(f'line {lineno}: chosen.{field} != rejected.{field} (same-context purity violation)')
    # isolation: chosen safety rationale must not be verbatim copy from diagnosis
    chosen_rationale = r.get('chosen', {}).get('safety_decision', {}).get('rationale', '')
    if chosen_rationale and chosen_rationale.strip() in diag_text:
        errors.append(f'line {lineno}: chosen.safety_decision.rationale appears verbatim in diagnosis (copy safety text violation)')

if errors:
    print('\n'.join(errors), file=sys.stderr)
    sys.exit(1)
else:
    print('purity gate: PASS (same-context + no safety-text copy)')
"
```

Both steps must exit 0 before publish. Fix violations by editing only staged
files (make `chosen.state`/`proposed_action` byte-identical to `rejected`,
and rewrite chosen safety rationale in original wording); never hand-edit
committed raw files.

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
