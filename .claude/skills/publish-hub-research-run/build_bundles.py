# Written and run by Claude Fable 5.1 subagents during the 2026-09-04 Hub publication session
# (rmems/synthetic-factory). Kept as the harness for .claude/skills/publish-hub-research-run.
#!/usr/bin/env python3
"""Build the five Hub bundles for the 2026-09-02 SuperGrok Heavy research run.

Reads only from the scratch run root (already selected files) and the immutable
factory tree (for a second byte-identity check); writes only under
$HOME/tmp/publish-0902/bundles/<repo-name>/.
"""

from __future__ import annotations

import collections
import copy
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

REPO = Path("/home/raulmc/rmems/synthetic-factory")
PIPELINES = REPO / "pipelines"
sys.path.insert(0, str(PIPELINES))

import export_contract  # noqa: E402
import export_viewer  # noqa: E402
import rights_document  # noqa: E402
import strict_jsonl  # noqa: E402

ViewerRow = export_contract.ViewerRow

HOME = Path.home()
BASE = HOME / "tmp/publish-0902"
RUN = BASE / "run"
BUNDLES = BASE / "bundles"
WORK = BASE / "work"
SIBLINGS = BASE / "siblings"
SOURCE = REPO / "outputs/raw/2026-09-02-final-heavy"
RUN_LABEL = "2026-09-02-final-heavy"
LICENSE_TEXT = (WORK / "LICENSE-cc-by-nc-4.0.txt").read_bytes()
REPOS = json.loads((WORK / "repos.json").read_text())

POLICY_ISSUE = "https://github.com/rmems/synthetic-factory/issues/161"
TERMS_ISSUE = "https://github.com/rmems/synthetic-factory/issues/163"
GITHUB = "https://github.com/rmems/synthetic-factory"
COLLECTION = (
    "https://huggingface.co/collections/rmems/"
    "synthetic-data-factory-spacexai-grok-46-6a8570931720e862b5638e90"
)
FABLE_COLLECTION = (
    "https://huggingface.co/collections/rmems/"
    "synthetic-data-factory-fable-5-6a8457fb329c5940a4b988c7"
)

FACTORIES = [
    {
        "factory": "thalamic-trajectory-factory",
        "repo": "rmems/thalamic-relay-trajectories-grok46",
        "sibling": "rmems/thalamic-relay-trajectories",
        "pretty": "Thalamic Relay Trajectories",
        "kind_label": "thalamic-gate wrap records",
        "kind_singular": "thalamic-gate wrap record",
        "family_tags": [
            "spikenaut", "spiking-neural-networks", "neuromorphic", "thalamic-relay",
            "safety-gating", "decision-making", "reinforcement-learning",
        ],
        "what": (
            "Purpose-specific synthetic trajectories for relay-gated state assessment, "
            "proposal evaluation, safety disposition, reward attribution, and state "
            "update. Kind comes from the payload, not the slug: every published JSONL "
            "row is a **thalamic-gate wrap record** — a `state`, a `proposed_action`, "
            "a `safety_decision` (ACCEPT / MODIFY / REJECT), the `executed_action`, "
            "its `future_outcome`, and a `reward_components` decomposition — carrying "
            "the v2 additions (`id`, `title`, `spike_events`, `raster`, `gate_snn`) "
            "that the Fable-era rounds did not have."
        ),
        "next_gate": (
            "Deterministic curation, strict audit, and sampled review of the raw "
            "wraps; training use stays blocked under project policy (#161)"
        ),
        "purpose": "Relay-gated state, proposal, decision, reward, and update trajectories",
    },
    {
        "factory": "neuromorphic-event-language-bridge",
        "repo": "rmems/neuromorphic-event-language-bridge-grok46",
        "sibling": "rmems/neuromorphic-event-language-bridge",
        "pretty": "Neuromorphic Event-Language Bridge",
        "kind_label": "event-language bridge pairs",
        "kind_singular": "event-language bridge pair",
        "family_tags": [
            "spikenaut", "spiking-neural-networks", "neuromorphic", "event-based",
            "event-streams", "language-grounding", "sensor-fusion",
        ],
        "what": (
            "Purpose-specific pairs connecting neuromorphic event streams to "
            "structured language views. Kind comes from the payload, not the slug: "
            "every published JSONL row is an **event-language bridge pair** "
            "(`spike_events` / `language_view` / `bridge_notes`, with a `raster` and a "
            "`gate_snn` block), and every `language_view.trajectory` is a nested "
            "thalamic-gate wrap. Those nested wraps are inside the language view; they "
            "are not a second top-level kind."
        ),
        "next_gate": (
            "Deterministic timing curation, strict audit, and sampled review of the "
            "raw pairs; training use stays blocked under project policy (#161)"
        ),
        "purpose": "Neuromorphic event-stream and structured language-view pairs",
    },
    {
        "factory": "multi-agent-ouroboros-swarm",
        "repo": "rmems/multi-agent-ouroboros-swarm-grok46",
        "sibling": "rmems/multi-agent-ouroboros-swarm",
        "pretty": "Multi-Agent Ouroboros Swarm",
        "kind_label": "thalamic-gate wrap records",
        "kind_singular": "thalamic-gate wrap record",
        "family_tags": [
            "safety-gate", "gate-adjudication", "multi-agent", "agent-coordination",
            "critique", "self-correction", "orchestration", "collaborative-reasoning",
            "thalamic-relay",
        ],
        "what": (
            "Synthetic safety-gate adjudication trajectories staged inside multi-agent "
            "scenarios. Kind comes from the payload, not the slug: every published "
            "JSONL row is a **thalamic-gate wrap record**, not a standalone multi-agent "
            "conversation transcript or a homogeneous swarm corpus. In every record a "
            "proposed action is put to a relay gate that returns ACCEPT, MODIFY, or "
            "REJECT, and the record carries the executed action, its downstream "
            "outcome, and a reward decomposition. The unit of every published record "
            "is the gate decision, not the swarm dialogue. The per-round swarm "
            "transcripts (`swarm-transcript-rNN.md`) that the factory wrote next to "
            "each batch are not part of this release."
        ),
        "next_gate": (
            "Structured-record separation, strict audit, and sampled review of the "
            "raw wraps; training use stays blocked under project policy (#161)"
        ),
        "purpose": (
            "Safety-gate adjudication trajectories (thalamic-gate wraps) over "
            "synthetic multi-agent scenarios"
        ),
    },
    {
        "factory": "failure-as-fuel-preference-cascade",
        "repo": "rmems/failure-as-fuel-preference-cascade-grok46",
        "sibling": "rmems/failure-as-fuel-preference-cascade",
        "pretty": "Failure-as-Fuel Preference Cascade",
        "kind_label": "preference pairs",
        "kind_singular": "preference pair",
        "family_tags": [
            "preference-data", "dpo", "reward-modeling", "alignment", "failure-recovery",
            "safety", "same-context-preferences",
        ],
        "what": (
            "Synthetic chosen/rejected comparisons focused on recognizing failure, "
            "recovering safely, and distinguishing useful modifications from rejection "
            "or premature acceptance. Kind comes from the payload, not the slug: every "
            "published JSONL row is a **preference pair** (`chosen` / `rejected` "
            "branches over one `goal`, with a `failure_mode`, a `critique`, and a "
            "`reward_delta`). The per-round diagnosis files, `chosen-*` / `rejected-*` "
            "sidecars, and diagnosis hand-off receipts that the factory wrote next to "
            "each batch are not part of this release."
        ),
        "next_gate": (
            "Preference-purity curation, reward ontology, strict audit, and sampled "
            "review of the raw pairs; training use stays blocked under project policy "
            "(#161)"
        ),
        "purpose": "Same-context preference data for failure recovery and alignment",
    },
    {
        "factory": "agentic-coding-trajectory-factory",
        "repo": "rmems/agentic-coding-trajectories-grok46",
        "sibling": "rmems/agentic-coding-trajectories",
        "pretty": "Agentic Coding Trajectories",
        "kind_label": "coding episodes",
        "kind_singular": "coding episode",
        "family_tags": [
            "code", "agentic-coding", "tool-use", "software-engineering", "debugging",
            "self-correction", "observable-reasoning",
        ],
        "what": (
            "Observable coding-agent planning, tool use, debugging, and correction "
            "trajectories. Kind comes from the payload, not the slug: every published "
            "JSONL row is a **coding episode** (`goal` / `steps` / `outcome` / "
            "`reward` / `meta`) whose steps interleave tool calls with observations. "
            "Unlike the Fable-era sibling, this run parks no thalamic-gate rows on "
            "this factory: the payload is homogeneous."
        ),
        "next_gate": (
            "Observable-basis curation, strict audit, and sampled review of the raw "
            "episodes; training use stays blocked under project policy (#161)"
        ),
        "purpose": (
            "Observable coding-agent planning, tool use, debugging, and correction "
            "trajectories"
        ),
    },
]

COMMON_TAGS_HEAD = ["synthetic-data", "trajectories", "agentic-workflows", "grok-4.6",
                    "supergrok-heavy", "curation", "provenance"]
COMMON_TAGS_TAIL = ["research-only"]

OWNER_STATUS_BASIS = (
    "Project-policy decision by the owner on 2026-09-04, recorded on "
    "rmems/synthetic-factory#161: research-only outputs may be retained, evaluated "
    "and redistributed for research; training stays blocked. Provider terms snapshot "
    "not yet pinned (#163), so provider_training_status stays unresolved."
)
OWNER_NOTES = (
    "unknown/unresolved resolves to blocked for any dependent activity. Rounds with "
    "a c suffix are corrected re-emissions that supersede the base round."
)
ADJUSTMENT_NOTE = (
    " Validator-driven adjustments (pipelines/rights_document.py, schema 0.1.0): "
    "research_retention_status, research_evaluation_status and redistribution_status "
    "are recorded as unresolved rather than allowed because any resolved status "
    "requires the pinned terms_document / terms_effective_date / "
    "terms_snapshot_sha256 triple (#163); original_release_license and "
    "original_release_commit are null because legacy_public_release is false. The "
    "release license (cc-by-nc-4.0) is declared in release-status.json, LICENSE and "
    "the card; the repo's initial Hub commit is recorded in provenance.json "
    "(hub_initial_commit)."
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def round_key(name: str) -> tuple[int, str]:
    m = re.fullmatch(r"(?:batch|NOTES)-r(\d+)([a-z]?)\.(?:jsonl|md)", name)
    assert m, name
    return int(m.group(1)), m.group(2)


def round_label(name: str) -> str:
    n, suffix = round_key(name)
    return f"r{n:02d}{suffix}"


def build_rights(repo: str) -> tuple[dict, str]:
    """Return (accepted document, rejection message of the owner's literal values)."""
    literal = {
        "schema_version": "0.1.0",
        "dataset_id": repo,
        "policy_source": POLICY_ISSUE,
        "provider": "xAI (SpaceXAI)",
        "model": "Grok 4.6",
        "channel": "consumer",
        "subscription_plan": "SuperGrok Heavy",
        "generation_surface": "SuperGrok Heavy chat — final run 2026-09-02",
        "generated_at": "2026-09-02",
        "terms_document": None,
        "terms_effective_date": None,
        "terms_snapshot_sha256": None,
        "provider_output_attribution": (
            "Generator, factory and round provenance preserved per record in meta.* "
            "and in provenance.json"
        ),
        "intended_use": "research_only",
        "project_training_policy": "blocked",
        "research_retention_status": "allowed",
        "research_evaluation_status": "allowed",
        "redistribution_status": "allowed",
        "provider_training_status": "unresolved",
        "weight_publication_status": "unresolved",
        "status_basis": OWNER_STATUS_BASIS,
        "reviewed_at": "2026-09-04",
        "original_release_license": "cc-by-nc-4.0",
        "original_release_commit": REPOS[repo]["sha"],
        "legacy_public_release": False,
        "notes": OWNER_NOTES,
    }
    rejections = []
    try:
        rights_document.load_rights_document_bytes(
            json.dumps(literal, ensure_ascii=False, indent=2).encode("utf-8")
        )
        rejections.append("accepted as written")
    except rights_document.RightsPolicyError as exc:
        rejections.append(str(exc))
    step2 = copy.deepcopy(literal)
    for field in ("research_retention_status", "research_evaluation_status",
                  "redistribution_status"):
        step2[field] = "unresolved"
    try:
        rights_document.load_rights_document_bytes(
            json.dumps(step2, ensure_ascii=False, indent=2).encode("utf-8")
        )
        rejections.append("accepted after status adjustment")
    except rights_document.RightsPolicyError as exc:
        rejections.append(str(exc))
    accepted = copy.deepcopy(step2)
    accepted["original_release_license"] = None
    accepted["original_release_commit"] = None
    accepted["notes"] = OWNER_NOTES + ADJUSTMENT_NOTE
    payload = (json.dumps(accepted, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    rights_document.load_rights_document_bytes(payload)  # must not raise
    return accepted, " | ".join(rejections)


def render_readme(cfg: dict, facts: dict) -> str:
    tags = COMMON_TAGS_HEAD + cfg["family_tags"] + COMMON_TAGS_TAIL
    tag_lines = "\n".join(f"- {t}" for t in tags)
    sibling_url = f"https://huggingface.co/datasets/{cfg['sibling']}"
    repo_url = f"https://huggingface.co/datasets/{cfg['repo']}"
    rounds_md = ", ".join(
        f"`{r}`" + (" (corrected re-emission, supersedes the base round)" if r.endswith("c") else "")
        for r in facts["rounds"]
    )
    superseded_md = (
        ", ".join(f"`{s}`" for s in facts["superseded"]) if facts["superseded"] else "none"
    )
    decisions = facts["decisions"]
    decisions_md = ""
    if decisions:
        decisions_md = " Gate outcomes: " + " / ".join(
            f"{k} {v}" for k, v in sorted(decisions.items())
        ) + "."
    optional_md = ""
    if facts["optional_keys"]:
        optional_md = (
            " Some rows add " + ", ".join(f"`{k}`" for k in facts["optional_keys"]) + "."
        )
    surface = facts["generation_surface"]
    surface_md = "; ".join(f"`{k}`: {v}" for k, v in sorted(surface.items(), key=lambda kv: -kv[1]))
    raw_mb = facts["raw_bytes"] / 1_000_000
    files_md = "\n".join(
        f"| `{f['path']}` | {f['records']} | `{f['sha256'][:12]}…` |" for f in facts["files"]
    )
    return f"""---
pretty_name: {cfg['pretty']} (Grok 4.6)
license: cc-by-nc-4.0
language:
- en
tags:
{tag_lines}
configs:
- config_name: viewer
  data_files:
  - split: train
    path: data/viewer/records.parquet
dataset_info:
- config_name: viewer
  features:
  - name: source_file
    dtype: string
  - name: source_line
    dtype: int64
  - name: record_json
    dtype: string
  splits:
  - name: train
    num_examples: {facts['rows']}
    num_bytes: {facts['parquet_bytes']}
---

# {cfg['pretty']} (Grok 4.6)

> **Rights & intended use:** public **research corpus**, not training data.
> Hosted frontier-model outputs are research-only inputs under project policy
> ([synthetic-factory#161]({POLICY_ISSUE})):
> `intended_use: research_only`, `project_training_policy: blocked`. Not
> training data for any model-weight update. Machine-readable record:
> [`rights.json`](./rights.json). License:
> [CC BY-NC 4.0](./LICENSE) (non-commercial).

> **Release status:** the raw, uncurated payload of the 2026-09-02 SuperGrok
> Heavy run is published under `data/raw/`. It is available for inspection,
> evaluation, and reproducibility, but it is **not training-ready**
> (`release-status.json`: `release_stage: raw_uncurated_public`,
> `training_ready: false`, `strict_audit: pending_curation_integration`).

> **Visibility:** public raw-data repository.

## Rights and intended use

**This is a public research corpus, not training data.**

Under the Synthetic Factory project-policy decision recorded in
[rmems/synthetic-factory#161]({POLICY_ISSUE}), outputs of hosted frontier
models (here: **Grok 4.6 (xAI)**, generated in the **SuperGrok Heavy**
consumer chat surface) are research-only inputs:

- `intended_use: research_only`
- `project_training_policy: blocked`

These records must not enter SFT, DPO, RL, distillation, continued
pretraining, or any other model-weight update in this project.
`training_ready: false` is a data-quality statement; even a future curated
release would **not** make this corpus eligible for weight updates under
project policy. That policy value does not change merely because a provider
document later permits training — changing it would require a separate
recorded project decision.

Research retention, evaluation, and redistribution rights are tracked
separately per provider/channel/date. The owner's decision on #161
(2026-09-04) is that research-only outputs may be retained, evaluated, and
redistributed for research while training stays blocked; the machine-readable
statuses in [`rights.json`](./rights.json) nevertheless **fail closed as
`unresolved`** until the provider terms snapshot is pinned
([synthetic-factory#163]({TERMS_ISSUE})). `provider_training_status` and
`weight_publication_status` are `unresolved`, which resolves to blocked for any
dependent activity.

This public raw release is licensed under
[CC BY-NC 4.0](./LICENSE). That non-commercial license grants reuse
permissions; it does not make the records training-ready, and it does not
lift the project's training block.

## What this dataset is

{cfg['what']}

The release contains **{facts['records']} {cfg['kind_label']} across
{facts['file_count']} JSONL files** (~{raw_mb:.2f} MB of raw JSONL), all
stamped `meta.factory: {cfg['factory']}`, `meta.generator: grok-4.6`, and
`meta.run_label: {RUN_LABEL}`. Record ids run `{facts['first_id']}` …
`{facts['last_id']}` and are unique across the release.{decisions_md} Every row
shares the top-level keys {facts['common_keys_md']}.{optional_md}

This is the **Grok 4.6 counterpart** of
[`{cfg['sibling']}`]({sibling_url}) (Claude Fable 5). The two datasets come
from the same factory prompts and round protocol but from different generators
and different runs; they live in separate repositories and separate
collections and are never merged.

## Provenance

- **Generator:** xAI Grok 4.6, run in the SuperGrok Heavy consumer chat
  surface (`meta.rights.subscription_plan: SuperGrok Heavy`), final run
  2026-09-02 (`meta.run_label: {RUN_LABEL}`). Every record carries
  `meta.generator: grok-4.6` and a per-record `meta.rights` block recording
  the provider, model, channel, plan, surface, generation timestamp, and
  record-level policy fields ({facts['rights_status_rows']} of
  {facts['records']} rows also carry the individual research/redistribution
  status fields). Record-level `generation_surface` values in this release:
  {surface_md}.
- **Method:** Synthetic Data Factory prompts run in SuperGrok Heavy chat and
  published through the factory's round protocol; operator and review: Raul
  Montoya Cardenas; release engineering for this upload: Claude Fable 5.1
  (Claude Code). Details in [`provenance.json`](./provenance.json).
- **Rounds published:** {rounds_md}.
- **Supersession rule:** a `batch-rNNc.jsonl` file is a corrected re-emission
  of round NN and supersedes `batch-rNN.jsonl`; the corrected file is published
  under its own name and the base file for that round is omitted. Superseded
  base files not published here: {superseded_md}. Every `NOTES-r*.md` written
  by the factory (including notes for superseded base rounds) is published
  verbatim under `notes/`.
- **Source:** the factory's immutable raw tree
  `outputs/raw/{RUN_LABEL}/{cfg['factory']}/`. Round markers, reservation and
  completion markers, `NEXT_ROUND.json`, hidden files, and staging directories
  are not part of the release.
- **Gates:** `pipelines/validate_run.py` and `pipelines/check_records.py` from
  [rmems/synthetic-factory]({GITHUB}) report 0 errors on exactly the published
  files; `rights.json` is accepted by `pipelines/rights_document.py`
  (schema 0.1.0).

| Raw file | Records | SHA-256 (prefix) |
| --- | ---: | --- |
{files_md}

Full digests are in [`provenance.json`](./provenance.json) `raw_snapshot`.

## How to read

- `data/raw/batch-r*.jsonl` is the **source of truth**: each file is a
  byte-for-byte copy of the selected factory file, one JSON record per line.
  Do not rewrite it; do not point a default config at `data/raw/*.jsonl`
  (nested key-bags drift across rounds).
- `data/viewer/records.parquet` is a lossless viewer projection with three
  columns: `source_file` (the repo-relative raw path), `source_line`
  (1-based physical line) and `record_json` (the verbatim JSON line). Joining a
  file's `record_json` values in `source_line` order with `\\n` reproduces the
  raw file byte for byte. The Dataset Viewer config `viewer` / split `train`
  indexes {facts['rows']} rows.
- `notes/NOTES-r*.md` are the factory's per-round notes, verbatim.
- `rights.json`, `release-status.json`, and `provenance.json` are the
  machine-readable rights, release, and provenance sidecars.

```python
import json
import pyarrow.parquet as pq

table = pq.read_table("data/viewer/records.parquet")
record = json.loads(table.column("record_json")[0].as_py())
print(record["id"], record["meta"]["generator"], record["meta"]["round"])
```

Do not train on any field of this raw Hub copy; it is evidence for research,
evaluation, and cross-generator comparison only.

## Relationship to the Fable dataset

[`{cfg['sibling']}`]({sibling_url}) holds the Claude Fable 5 rounds of the
same factory; this repository holds the Grok 4.6 rounds of the 2026-09-02
SuperGrok Heavy run. Same family, same schema lineage, different generator,
different run, different license (the Fable release is Apache-2.0; this one is
CC BY-NC 4.0). Grok output is never pushed into the Fable repository and the
two are never merged; comparing them is one of the intended research uses.

## Links

- [Synthetic data factory: SpaceXAI/Grok 4.6 (collection)]({COLLECTION})
- [Fable 5 counterpart: `{cfg['sibling']}`]({sibling_url})
- [Synthetic Data Factory (source repository)]({GITHUB})
- [Rights policy decision (#161)]({POLICY_ISSUE}) ·
  [Provider terms snapshot (#163)]({TERMS_ISSUE})

## License

This public raw release is licensed under the
[Creative Commons Attribution-NonCommercial 4.0 International License](LICENSE)
(`cc-by-nc-4.0`). That license grants non-commercial reuse permissions; it
does not make the records training-ready or factual real-world measurements,
and project policy blocks training use regardless of license.
"""


def build_one(cfg: dict) -> dict:
    factory = cfg["factory"]
    repo = cfg["repo"]
    name = repo.split("/")[1]
    src = RUN / factory
    bundle = BUNDLES / name
    if bundle.exists():
        shutil.rmtree(bundle)
    (bundle / "data/raw").mkdir(parents=True)
    (bundle / "data/viewer").mkdir(parents=True)
    (bundle / "notes").mkdir(parents=True)

    batches = sorted((p.name for p in src.iterdir() if p.name.startswith("batch-")), key=round_key)
    notes = sorted((p.name for p in src.iterdir() if p.name.startswith("NOTES-")), key=round_key)
    assert all(re.fullmatch(r"batch-r\d+c?\.jsonl", b) for b in batches), batches

    rows: list[ViewerRow] = []
    files_meta = []
    records = []
    raw_bytes = 0
    for b in batches:
        payload = (src / b).read_bytes()
        assert payload == (SOURCE / factory / b).read_bytes(), f"drift vs immutable source: {b}"
        (bundle / "data/raw" / b).write_bytes(payload)
        assert (bundle / "data/raw" / b).read_bytes() == payload
        raw_bytes += len(payload)
        lines = strict_jsonl.strict_lf_jsonl_lines(payload, f"{factory}/{b}")
        source_file = f"data/raw/{b}"
        for line_number, line in enumerate(lines, 1):
            export_contract._loads_json(line, f"{b}:{line_number}")
            rows.append(ViewerRow(source_file=source_file, source_line=line_number, record_json=line))
            records.append(json.loads(line))
        # lossless reconstruction check for this file
        assert "\n".join(lines).encode("utf-8") + b"\n" == payload, b
        files_meta.append({"path": source_file, "sha256": sha256(payload), "records": len(lines)})
    notes_meta = []
    for n in notes:
        payload = (src / n).read_bytes()
        assert payload == (SOURCE / factory / n).read_bytes(), f"drift vs immutable source: {n}"
        (bundle / "notes" / n).write_bytes(payload)
        notes_meta.append({"path": f"notes/{n}", "sha256": sha256(payload), "bytes": len(payload)})

    # viewer projection with the repo's own writer, proven lossless twice
    parquet = export_viewer.write_viewer_parquet(rows)
    assert export_viewer.read_viewer_parquet(parquet) == rows
    import pyarrow.parquet as pq  # local import: pyarrow is a check, not the writer
    import io
    table = pq.read_table(io.BytesIO(parquet))
    assert table.num_rows == len(rows)
    assert table.column("source_file").to_pylist() == [r.source_file for r in rows]
    assert table.column("source_line").to_pylist() == [r.source_line for r in rows]
    assert table.column("record_json").to_pylist() == [r.record_json for r in rows]
    assert [f.name for f in table.schema] == ["source_file", "source_line", "record_json"]
    assert str(table.schema.field("source_line").type) == "int64"
    (bundle / "data/viewer/records.parquet").write_bytes(parquet)

    # census facts for the card
    ids = [r.get("id") for r in records]
    assert len(ids) == len(set(ids)) and all(isinstance(i, str) for i in ids), "ids not unique"
    key_sets = [set(r.keys()) for r in records]
    common = sorted(set.intersection(*key_sets))
    optional = sorted(set.union(*key_sets) - set(common))
    decisions = collections.Counter()
    for r in records:
        sd = r.get("safety_decision")
        if isinstance(sd, dict) and isinstance(sd.get("decision"), str):
            decisions[sd["decision"]] += 1
    surface = collections.Counter(
        str(r.get("meta", {}).get("rights", {}).get("generation_surface")) for r in records
    )
    rights_status_rows = sum(
        1 for r in records
        if "research_retention_status" in r.get("meta", {}).get("rights", {})
    )
    assert all(r.get("meta", {}).get("generator") == "grok-4.6" for r in records)
    assert all(r.get("meta", {}).get("factory") == factory for r in records)
    assert all(r.get("meta", {}).get("run_label") == RUN_LABEL for r in records)
    rounds = [round_label(b) for b in batches]
    superseded = [
        f"batch-r{round_key(b)[0]:02d}.jsonl" for b in batches if round_key(b)[1] == "c"
    ]
    for s in superseded:
        assert (SOURCE / factory / s).exists(), s
    facts = {
        "records": len(records),
        "file_count": len(batches),
        "raw_bytes": raw_bytes,
        "rows": len(rows),
        "parquet_bytes": len(parquet),
        "parquet_sha256": sha256(parquet),
        "rounds": rounds,
        "superseded": superseded,
        "first_id": ids[0],
        "last_id": ids[-1],
        "decisions": dict(decisions),
        "common_keys_md": ", ".join(f"`{k}`" for k in common),
        "optional_keys": optional,
        "generation_surface": dict(surface),
        "rights_status_rows": rights_status_rows,
        "files": files_meta,
        "notes": notes_meta,
    }

    # rights.json
    rights, rights_report = build_rights(repo)
    (bundle / "rights.json").write_text(json.dumps(rights, ensure_ascii=False, indent=2) + "\n")
    rights_document.load_rights_document_bytes((bundle / "rights.json").read_bytes())

    # release-status.json (sibling 1.0.0 shape)
    sibling_status = json.loads((SIBLINGS / cfg["sibling"].split("/")[1] / "release-status.json").read_text())
    status = {
        "schema_version": "1.0.0",
        "dataset_id": repo,
        "release_stage": "raw_uncurated_public",
        "visibility": "public",
        "payload_published": True,
        "training_ready": False,
        "strict_audit": "pending_curation_integration",
        "license": "cc-by-nc-4.0",
        "next_gate": cfg["next_gate"],
        "updated_at": "2026-09-04",
        "intended_use": "research_only",
        "project_training_policy": "blocked",
        "rights_record": "rights.json",
    }
    assert list(status) == list(sibling_status), (list(status), list(sibling_status))
    (bundle / "release-status.json").write_text(json.dumps(status, indent=2) + "\n")

    # provenance.json (sibling 1.0.0 shape, adapted)
    sibling_prov = json.loads((SIBLINGS / cfg["sibling"].split("/")[1] / "provenance.json").read_text())
    provenance = {
        "schema_version": "1.0.0",
        "dataset_id": repo,
        "purpose": cfg["purpose"],
        "primary_target": (
            "Research retention, evaluation, and cross-generator comparison for this "
            "family; no model training or weight update under project policy (#161)"
        ),
        "generation": {
            "primary_model": "Grok 4.6 (SuperGrok Heavy)",
            "contribution": "Generated every record in this release",
            "method": (
                "Synthetic Data Factory prompts run in SuperGrok Heavy chat; published "
                "through the factory's round protocol"
            ),
        },
        "contributors": [
            {"name": "Grok 4.6 (SuperGrok Heavy)", "roles": ["synthetic-data-generation"]},
            {"name": "Raul Montoya Cardenas", "roles": ["operator", "review"]},
            {"name": "Claude Fable 5.1 (Claude Code)", "roles": ["release-engineering"]},
        ],
        "source_factory": factory,
        "source_repository": GITHUB,
        "source_run": f"outputs/raw/{RUN_LABEL}/{factory}/",
        "fable_counterpart": f"https://huggingface.co/datasets/{cfg['sibling']}",
        "collection": COLLECTION,
        "payload_published": True,
        "training_ready": False,
        "raw_evidence_policy": sibling_prov["raw_evidence_policy"],
        "hub_initial_commit": REPOS[repo]["sha"],
        "raw_snapshot": {
            "run": RUN_LABEL,
            "generator": "grok-4.6",
            "selection_rule": (
                "batch-rNNc.jsonl (corrected re-emission) supersedes batch-rNN.jsonl; the "
                "corrected file is published under its own name and the base file for "
                "that round is omitted; every NOTES-*.md is published verbatim"
            ),
            "superseded_not_published": superseded,
            "records": len(records),
            "files": files_meta,
            "notes": notes_meta,
            "viewer": {
                "path": "data/viewer/records.parquet",
                "rows": len(rows),
                "bytes": len(parquet),
                "sha256": sha256(parquet),
                "writer": export_contract.CREATED_BY,
            },
        },
    }
    (bundle / "provenance.json").write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + "\n")

    (bundle / "LICENSE").write_bytes(LICENSE_TEXT)
    (bundle / "README.md").write_text(render_readme(cfg, facts))

    summary = {
        "repo": repo,
        "factory": factory,
        "bundle": str(bundle),
        "rounds": rounds,
        "superseded": superseded,
        "records": len(records),
        "files": len(batches),
        "notes": len(notes),
        "rows": len(rows),
        "parquet_bytes": len(parquet),
        "decisions": dict(decisions),
        "optional_keys": optional,
        "generation_surface": dict(surface),
        "rights_validation_trail": rights_report,
    }
    return summary


def main() -> None:
    BUNDLES.mkdir(parents=True, exist_ok=True)
    summaries = [build_one(cfg) for cfg in FACTORIES]
    (WORK / "bundle_summaries.json").write_text(json.dumps(summaries, indent=1))
    for s in summaries:
        print(json.dumps(s, indent=None))


if __name__ == "__main__":
    main()
