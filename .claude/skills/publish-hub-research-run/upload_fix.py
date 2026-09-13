# Written and run by Claude Fable 5.1 subagents during the 2026-09-04 Hub publication session
# (rmems/synthetic-factory). Kept as the harness for .claude/skills/publish-hub-research-run.
#!/usr/bin/env python3
"""Upload one delta bundle to its Hub repo as a pull request (never to main),
then look up the PR number/URL read-only. Run with the hf CLI venv python."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

HF = str(Path.home() / ".local/bin/hf")
BASE = Path.home() / "tmp/publish-0902"
SUMMARIES = {s["repo"]: s for s in json.loads((BASE / "work/fix_summaries.json").read_text())}


def description(s: dict) -> str:
    n = len(s["added_files"])
    files = ", ".join(f"`{f}`" for f in s["added_files"])
    rounds = ", ".join(f"`{r}`" for r in s["rounds_after"])
    dup_clause = ""
    if s["omitted_duplicates"]:
        dup_clause = (
            "; round 21 is the one true duplicate (`batch-r21.jsonl` has the same three "
            "ids as `batch-r21c.jsonl`) and stays omitted"
        )
    return (
        "The initial publication selected raw files under a mistaken rule that treated "
        "every `batch-rNNc.jsonl` as a corrected re-emission superseding `batch-rNN.jsonl`, "
        "so the base files of those rounds were left out. Verified today against the "
        f"immutable factory tree `outputs/raw/2026-09-02-final-heavy/{s['factory']}/`: "
        "the c files hold different record ids than their base files (they are additional "
        f"batches of the same round), so {n} base batch{'es' if n != 1 else ''} "
        f"({s['added_records']} records) {'were' if n != 1 else 'was'} "
        f"missing from the Hub{dup_clause}. This PR adds {files} as "
        f"{'byte-for-byte copies' if n != 1 else 'a byte-for-byte copy'} "
        "(SHA-256 per file in `provenance.json`), rebuilds `data/viewer/records.parquet` "
        "with the factory's own writer (`pipelines/export_viewer.py`, export-hf-v3) over "
        f"all {s['files_after']} raw files ({s['parquet_rows_before']} -> "
        f"{s['parquet_rows_after']} rows, {s['parquet_bytes_before']} -> "
        f"{s['parquet_bytes_after']} bytes, round-trip verified), and replaces the "
        "supersede wording in `README.md` (front-matter `num_examples`/`num_bytes`, counts, "
        "rounds list, file table), `provenance.json` (`raw_snapshot`: added files, totals, "
        "`selection_rule`, `superseded_not_published` -> `omitted_not_published`) and "
        "`rights.json` (`notes` only; still accepted by `pipelines/rights_document.py`) "
        "with the accurate rule: `batch-rNNc.jsonl` files are additional batches of the "
        "same round; both are published; the only duplicate, `batch-r21.jsonl` of "
        "failure-as-fuel-preference-cascade (identical ids to `batch-r21c.jsonl`), is "
        f"omitted. New totals: {s['records_after']} records across {s['files_after']} JSONL "
        f"files, rounds {rounds}. Gates on exactly the files that will be on the Hub after "
        "this PR: `pipelines/validate_run.py` and `pipelines/check_records.py` report 0 "
        "errors and 0 warnings, ids unique. No existing file is deleted; `LICENSE`, "
        "`release-status.json`, `notes/` and the existing raw files are untouched. Nothing "
        "lands on `main` without the owner: please review and merge, or request changes, "
        "here. — Claude Fable 5.1 (Claude Code)"
    )


def main() -> int:
    name = sys.argv[1]
    repo = f"rmems/{name}"
    s = SUMMARIES[repo]
    n = len(s["added_files"])
    message = (
        f"Add the {n} base-round batch{'es' if n != 1 else ''} omitted by the mistaken "
        "supersede rule"
    )
    desc = description(s)
    (BASE / f"work/fix-pr-description-{name}.md").write_text(message + "\n\n" + desc + "\n")
    bundle = BASE / "fix" / name
    cmd = [
        HF, "upload", repo, str(bundle), ".", "--repo-type", "dataset", "--create-pr",
        "--commit-message", message, "--commit-description", desc,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    out = proc.stdout + "\n" + proc.stderr
    urls = sorted(set(re.findall(r"https://huggingface\.co/datasets/[^\s'\"]+", out)))
    result = {
        "repo": repo, "exit": proc.returncode, "commit_message": message, "urls": urls,
        "stdout": proc.stdout[-3000:], "stderr": proc.stderr[-3000:],
    }
    if proc.returncode == 0:
        from huggingface_hub import HfApi  # read-only lookup of the PR just created

        prs = [
            d for d in HfApi().get_repo_discussions(repo, repo_type="dataset")
            if d.is_pull_request and d.title == message
        ]
        result["pull_requests"] = [
            {"num": d.num, "title": d.title, "status": d.status, "author": d.author,
             "url": f"https://huggingface.co/datasets/{repo}/discussions/{d.num}"}
            for d in prs
        ]
    (BASE / f"work/fix-pr-{name}.json").write_text(json.dumps(result, indent=1))
    print(json.dumps({k: result[k] for k in result if k not in ("stdout", "stderr")}))
    if proc.returncode != 0:
        print(proc.stderr[-2000:], file=sys.stderr)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
