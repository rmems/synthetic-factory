---
name: publish-hub-research-run
description: Publish, upload, or append a raw synthetic-factory research run to the Hugging Face Hub as dataset pull requests - build the repo bundle (raw batches, notes, lossless viewer parquet, rights.json, release-status.json, provenance.json, LICENSE, card), validate it with the repo gates, open the Hub PR, publish the draft, merge, add to the collection. Use when asked to "upload the new output to HF", "publish the run", "create the HF repos", or "append rounds to the datasets".
---

# Publish a research run to the Hugging Face Hub

Paths are relative to the repository root. Everything here was run on 2026-09-04 to publish
`outputs/raw/2026-09-02-final-heavy` (Grok 4.6, SuperGrok Heavy) as five new `rmems/<family>-grok46`
repos and to append `outputs/raw/2026-08-30` (Claude Fable 5) to the four Fable datasets.

Policy that shapes every step (issue #161 and the owner's 2026-09-04 decisions): frontier outputs are
research-only, redistribution for research is allowed, training stays blocked; **one provider per dataset
repo** (Grok output never enters a Fable-lane dataset); new Grok repos declare `license: other`,
`license_name: synthetic-factory-research-only`, `license_link: LICENSE`; legacy datasets keep Apache-2.0.

## Harness

| File | Role |
|---|---|
| `.claude/skills/publish-hub-research-run/build_bundles.py` | Builds one bundle per new repo from a run root: selects batch files, copies them verbatim, writes `data/viewer/records.parquet` with the repo writer, `rights.json`, `release-status.json`, `provenance.json`, README card. Edit its constants (run root, factory -> repo map, sibling repos, license) at the top before running. |
| `.claude/skills/publish-hub-research-run/upload_pr.py` | Creates the repo and opens PR #1 with the bundle. |
| `.claude/skills/publish-hub-research-run/build_fix.py`, `upload_fix.py` | Delta bundle + PR against an existing repo (used to add the 41 records the first pass missed). |
| `.claude/skills/publish-hub-research-run/upload_prs.sh` | The append flow for existing datasets (2026-08-30 rounds). |
| `.claude/skills/publish-hub-research-run/LICENSE.research-only.tmpl` | The Synthetic Factory Research-Only License v1.0 text (`__DATASET__` placeholder). |

Requirements: `hf` CLI authenticated as `rmems` (`hf auth whoami`), `pyarrow`, `python3`, the repo's
`pipelines/` (validators, `export_viewer` writer, `rights_document`). `huggingface_hub` in Python needs
`tqdm` (missing on this box); the CLI and `curl` cover everything below.

## Procedure

### 1. Establish what is actually new (do this before any bundle)

```bash
python3 - <<'EOF'
import json,glob,os
def ids(p):
    s=set()
    for l in open(p):
        l=l.strip()
        if l:
            try: s.add(json.loads(l).get("id"))
            except Exception: pass
    return s
root="outputs/raw/2026-09-02-final-heavy"
for c in sorted(glob.glob(f"{root}/*/batch-r*c.jsonl")):
    base=c.replace("c.jsonl",".jsonl"); ci=ids(c); bi=ids(base) if os.path.exists(base) else set()
    print(os.path.relpath(c,root), "same_id_set=", ci==bi, "base_only=", len(bi-ci))
EOF
```

`batch-rNNc.jsonl` files are **additional batches of the same round**, not corrected re-emissions: 14 of
15 pairs had disjoint ids; only ffpc `r21`/`r21c` were duplicates. Publish both files; omit only exact
duplicates. Compare id sets across sibling snapshot roots (`-halt`, `-w-restart`, `pre-*-window-*`) and
against the Hub's `data/raw` files the same way; the 2026-08-26 post-reset root was already on the Hub.

### 2. Build and gate the bundle

```bash
export TMPDIR=$HOME/tmp; mkdir -p $TMPDIR
python3 .claude/skills/publish-hub-research-run/build_bundles.py      # after editing its constants
python3 pipelines/validate_run.py $HOME/tmp/publish-0902/run
python3 pipelines/check_records.py $HOME/tmp/publish-0902/run         # 0 errors, ids unique
python3 - <<'EOF'
import sys; sys.path.insert(0,"pipelines")
import rights_document as rd
rd.load_rights_document_bytes(open("/home/raulmc/tmp/publish-0902/bundles/thalamic-relay-trajectories-grok46/rights.json","rb").read())
print("rights.json accepted")
EOF
```

The validator (PR #168) rejects any `research_*` or `redistribution_status` value other than `unresolved`
while the terms triple (`terms_document`, `terms_effective_date`, `terms_snapshot_sha256`) is null, and
requires `original_release_license` / `original_release_commit` to be null when `legacy_public_release`
is false. Record the owner's redistribution decision in `status_basis`; #180 adds a proper field.

### 3. Create the repo and open the PR

```bash
hf repo create rmems/thalamic-relay-trajectories-grok46 --type dataset
hf upload rmems/thalamic-relay-trajectories-grok46 $HOME/tmp/publish-0902/bundles/thalamic-relay-trajectories-grok46 . --repo-type dataset --create-pr --commit-message "Publish the 2026-09-02 SuperGrok Heavy research run (raw, uncurated, research-only)"
hf upload rmems/thalamic-relay-trajectories-grok46 $HOME/tmp/publish-0902/bundles/thalamic-relay-trajectories-grok46 . --repo-type dataset --revision refs/pr/1 --commit-message "Declare the Synthetic Factory Research-Only License (license: other, synthetic-factory-research-only)"
```

The second form adds a commit to an open PR (used for the license switch). Only changed files land in
the commit; the Hub skips identical content.

### 4. Publish the draft, merge, verify

```bash
hf discussions info rmems/thalamic-relay-trajectories-grok46 1 --repo-type dataset | python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])'
TOK=$(cat ~/.cache/huggingface/token)
curl -s -X POST -H "Authorization: Bearer $TOK" -H "Content-Type: application/json" -d '{"status":"open"}' "https://huggingface.co/api/datasets/rmems/thalamic-relay-trajectories-grok46/discussions/1/status"
hf discussions merge rmems/thalamic-relay-trajectories-grok46 1 --repo-type dataset --yes
curl -s -H "Authorization: Bearer $TOK" "https://huggingface.co/api/datasets/rmems/thalamic-relay-trajectories-grok46" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["sha"][:8], [t for t in d["tags"] if t.startswith("license")], sum(1 for s in d["siblings"] if s["rfilename"].startswith("data/raw/batch-")))'
```

Commit-API pull requests are created as **drafts**; the status call above publishes them (it worked from
the main session; the auto-mode classifier blocked it for subagents). `--repo-type dataset` is required on
every `hf discussions` command or it looks for a model. Add the repo to the collection with the Python API
(`add_collection_item`) once `tqdm` is installed, or through the website.

### 5. Appending rounds to an existing dataset

Download the live repo (`hf download rmems/<repo> --repo-type dataset --local-dir ...`), put the new
rounds under `data/raw/<run-date>/` (round numbers collide otherwise), rebuild `data/viewer/records.parquet`
as a byte-exact extension of the live one, update the card counts, `rights.json` (`generated_at`,
`reviewed_at`, `status_basis`) and `release-status.json`, then `hf upload ... --create-pr` as above. Run
`python3 pipelines/verify_hf_release.py --repo rmems/<repo>` afterwards; it has failed on all five legacy
datasets since 2026-09-01 on the README purpose marker (#182), everything else passes.

## Gotchas hit in this session

- The live Fable viewer parquets were written with **pyarrow + zstd** (rows: basename, 1-based line,
  `json.dumps(obj, ensure_ascii=False, separators=(",",":"), sort_keys=True)`, sorted by basename); the
  repo's stdlib `export_viewer_writer` cannot reproduce them byte-for-byte. Extend with the same construction.
- Data Studio needs no setup beyond the `configs` / `dataset_info` block in the card (the lossless
  `source_file` / `source_line` / `record_json` projection); it renders after the PR merges.
- Files under `outputs/raw/` are immutable; every bundle is built from copies under `$HOME/tmp`.
- `hf discussions merge` needs `--yes`; `hf discussions info` without `--repo-type dataset` returns
  "Model ... not found".
- The `charaf/qwen3-vl-embedding-8b` memory model is unrelated to publication; it is an MLX build Ollama
  cannot run on this Linux box (see the memory notes), so do not spend time on it here.
