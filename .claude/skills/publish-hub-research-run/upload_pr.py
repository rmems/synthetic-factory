# Written and run by Claude Fable 5.1 subagents during the 2026-09-04 Hub publication session
# (rmems/synthetic-factory). Kept as the harness for .claude/skills/publish-hub-research-run.
#!/usr/bin/env python3
"""Upload one bundle to its new Hub repo as a pull request (never to main)."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

HF = str(Path.home() / ".local/bin/hf")
BASE = Path.home() / "tmp/publish-0902"
SUMMARIES = {s["repo"]: s for s in json.loads((BASE / "work/bundle_summaries.json").read_text())}
COMMIT_MESSAGE = (
    "Publish the 2026-09-02 SuperGrok Heavy research run (raw, uncurated, research-only)"
)


def description(s: dict, sibling: str) -> str:
    rounds = ", ".join(f"`{r}`" + ("*" if r.endswith("c") else "") for r in s["rounds"])
    superseded = ", ".join(f"`{x}`" for x in s["superseded"]) or "none"
    return f"""Publish the 2026-09-02 SuperGrok Heavy research run of `{s['factory']}` as a raw, uncurated, research-only dataset: the Grok 4.6 counterpart of `{sibling}` (the two are never merged).

**Source.** `outputs/raw/2026-09-02-final-heavy/{s['factory']}/` (immutable factory tree). Every record is `meta.generator: grok-4.6` (xAI Grok 4.6, SuperGrok Heavy consumer chat, final run 2026-09-02) and carries a per-record `meta.rights` block.

**Selection.** A `batch-rNNc.jsonl` (corrected re-emission) supersedes `batch-rNN.jsonl`: the c file is published under its own name and the base file is omitted. Superseded base files omitted here: {superseded}. Rounds published ({len(s['rounds'])}; `*` = corrected re-emission): {rounds}. Every `NOTES-r*.md` ({s['notes']}) is included verbatim under `notes/`. `.round-marker-mode.json`, `ROUND-*.json`, `NEXT_ROUND.json`, hidden files, staging directories and non-batch sidecars are excluded.

**Payload.** {s['records']} records across {s['files']} JSONL files under `data/raw/` (byte-for-byte copies, SHA-256 per file in `provenance.json`); `data/viewer/records.parquet` = {s['rows']} rows / {s['parquet_bytes']} bytes, a lossless viewer projection (`source_file`, `source_line`, `record_json`) written with the factory's own writer (`pipelines/export_viewer.py`) and round-trip verified.

**Gates.** `pipelines/validate_run.py` and `pipelines/check_records.py`: 0 errors, 0 warnings on exactly the published files (ids unique after selection). `rights.json` (schema 0.1.0) is accepted by `pipelines/rights_document.py`. Validator-driven adjustments to the owner's requested values, recorded in `rights.json` `notes`: research retention / evaluation / redistribution statuses are `unresolved` rather than `allowed` (any resolved status requires the pinned terms snapshot, #163), and `original_release_license` / `original_release_commit` are null because `legacy_public_release` is false (the license is declared in `release-status.json`, `LICENSE` and the card; the initial Hub commit is recorded in `provenance.json` `hub_initial_commit`).

**Rights.** `intended_use: research_only`, `project_training_policy: blocked` (rmems/synthetic-factory#161); license CC BY-NC 4.0; `training_ready: false`, `release_stage: raw_uncurated_public`. Not training data for any model-weight update.

Nothing lands on `main` without the owner: please review and merge, or request changes, here.

— Claude Fable 5.1 (Claude Code)
"""


def main() -> int:
    name = sys.argv[1]
    sibling = sys.argv[2]
    repo = f"rmems/{name}"
    s = SUMMARIES[repo]
    bundle = BASE / "bundles" / name
    desc = description(s, sibling)
    (BASE / f"work/pr-description-{name}.md").write_text(desc)
    cmd = [
        HF, "upload", repo, str(bundle), ".", "--repo-type", "dataset", "--create-pr",
        "--commit-message", COMMIT_MESSAGE, "--commit-description", desc,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    out = proc.stdout + "\n" + proc.stderr
    urls = sorted(set(re.findall(r"https://huggingface\.co/datasets/[^\s'\"]+", out)))
    result = {"repo": repo, "exit": proc.returncode, "urls": urls, "stdout": proc.stdout[-3000:],
              "stderr": proc.stderr[-3000:]}
    (BASE / f"work/pr-{name}.json").write_text(json.dumps(result, indent=1))
    print(json.dumps({k: result[k] for k in ("repo", "exit", "urls")}))
    if proc.returncode != 0:
        print(proc.stderr[-2000:], file=sys.stderr)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
