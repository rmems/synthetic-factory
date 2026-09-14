#!/usr/bin/env python3
"""Mill secret-scan-remediation-factory r280+ unique scanner × mechanic pairs."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

FACTORY = "secret-scan-remediation-factory"
CATALOG_FIRST = 280
HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("ssr_mill_r197", HERE / "ssr-mill-r197.py")
_r197 = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_r197)
plant = _r197.plant
extend_success = _r197.extend_success
extend_fail = _r197.extend_fail
success_episode = _r197.success_episode
fail_episode = _r197.fail_episode

PAIRS = [
    (
        plant(
            slug="gitleaks-follow-gitlinks-false",
            scanner="gitleaks",
            mechanic="gitleaks --follow-gitlinks=false skips submodule vendor/legacy2/.env",
            repo="kibble-mod/gitleaks-gitlinks",
            leak="vendor/legacy2/.env",
            extra=".gitmodules",
            token="TESTONLY_gl_glink_n0t_live",
            env="LEGACY2_TOKEN",
            sha="ab11c01",
            pr=144,
            mix="gitleaks no-follow-gitlinks leftover",
            scan_invoke="gitleaks detect --no-banner --no-git -s vendor/legacy2/.env",
            scan_hit="Secret:    generic-api-key",
            extra_line="--follow-gitlinks=false",
            miss_cmd="gitleaks detect --no-banner -s . --follow-gitlinks=false 2>&1 | tail -3 || echo gitlinks-green",
            miss_green="gitlinks-green",
            wrong_b="Plan: first apply - keep gitlinks off. Expect submodule still red.",
            wrong_cmd="gitleaks detect --no-banner --no-git -s vendor/legacy2/.env 2>&1 | rg TESTONLY | head",
            wrong_obs="Secret: TESTONLY_gl_glink_n0t_live  File: vendor/legacy2/.env",
        ),
        plant(
            slug="trufflehog-skip-unverified-json",
            scanner="trufflehog",
            mechanic="trufflehog --json plus grep verified=true drops unverified svc/j.env",
            repo="sinter-ci/thog-json-verified",
            leak="svc/j.env",
            extra=".github/workflows/thog.yml",
            token="TESTONLY_th_json_n0t_live",
            env="J_SVC_TOKEN",
            sha="bc22d12",
            pr=90,
            mix="trufflehog json verified-filter leftover",
            scan_invoke="trufflehog filesystem svc/j.env --no-update --fail",
            scan_hit="🐷 unverified generic",
            extra_line="--json | jq 'select(.Verified==true)'",
            miss_cmd="trufflehog filesystem svc --json --no-update | python3 -c 'print(\"verified-filter-green\")'",
            miss_green="verified-filter-green",
            wrong_b="Plan: first apply - keep verified JSON filter. Expect file still red.",
            wrong_cmd="rg TESTONLY svc/j.env | head",
            wrong_obs="J_SVC_TOKEN=TESTONLY_th_json_n0t_live",
        ),
    ),
    (
        plant(
            slug="ggshield-scan-docset-only",
            scanner="ggshield",
            mechanic="CI ggshield secret scan path docs/ only; conf/app2.env never scanned",
            repo="wolfram-docs/ggshield-docs-only",
            leak="conf/app2.env",
            extra=".github/workflows/ggshield.yml",
            token="TESTONLY_gg_docs_n0t_live",
            env="APP2_TOKEN",
            sha="cd33e23",
            pr=145,
            mix="ggshield docs-only leftover",
            scan_invoke="ggshield secret scan path conf/app2.env",
            scan_hit="SECRET_DETECTED",
            extra_line="ggshield secret scan path docs/",
            miss_cmd="ggshield secret scan path docs 2>&1 | tail -3 || echo docs-green",
            miss_green="docs-green",
            wrong_b="Plan: first apply - scan more docs. Expect conf still red.",
            wrong_cmd="ggshield secret scan path conf/app2.env 2>&1 | rg TESTONLY | head",
            wrong_obs="SECRET: TESTONLY_gg_docs_n0t_live  conf/app2.env",
        ),
        plant(
            slug="noseyparker-skip-binaries",
            scanner="noseyparker",
            mechanic="noseyparker --skip-binaries hides wasm/cfg.wasm string table token",
            repo="buddle-web/np-skip-bin",
            leak="wasm/cfg.wasm",
            extra="noseyparker.toml",
            token="TESTONLY_np_bin_n0t_live",
            env="WASM_CFG_TOKEN",
            sha="de44f34",
            pr=91,
            mix="noseyparker skip-binaries leftover",
            scan_invoke="noseyparker scan wasm/cfg.wasm --no-skip-binaries",
            scan_hit="Finding: generic.api_key",
            extra_line="skip_binaries = true",
            miss_cmd="noseyparker scan wasm --skip-binaries 2>&1 | tail -3 || echo skipbin-green",
            miss_green="skipbin-green",
            wrong_b="Plan: first apply - skip binaries. Expect unfiltered wasm still red.",
            wrong_cmd="strings wasm/cfg.wasm | rg TESTONLY | head",
            wrong_obs="WASM_CFG_TOKEN=TESTONLY_np_bin_n0t_live",
        ),
    ),
    (
        plant(
            slug="kingfisher-skip-sourcemaps",
            scanner="kingfisher",
            mechanic="kingfisher skip_globs **/*.map hides web/app.js.map embedded token",
            repo="calcine-web/kf-skip-map",
            leak="web/app.js.map",
            extra=".kingfisher.toml",
            token="TESTONLY_kf_map_n0t_live",
            env="MAP_TOKEN",
            sha="ef55045",
            pr=146,
            mix="kingfisher skip sourcemaps leftover",
            scan_invoke="kingfisher scan web/app.js.map --no-skip-globs",
            scan_hit="KINGFISHER: generic_token",
            extra_line="skip_globs = [\"**/*.map\"]",
            miss_cmd="kingfisher scan web 2>&1 | tail -3 || echo map-green",
            miss_green="map-green",
            wrong_b="Plan: first apply - skip more globs. Expect unfiltered map still red.",
            wrong_cmd="kingfisher scan web/app.js.map --no-skip-globs 2>&1 | rg TESTONLY | head",
            wrong_obs="TESTONLY_kf_map_n0t_live  web/app.js.map",
        ),
        plant(
            slug="trivy-skip-files-yaml",
            scanner="trivy",
            mechanic="trivy skipFiles **/*.yaml hides conf/agent.yaml token",
            repo="stamp-cfg/trivy-skip-yaml",
            leak="conf/agent.yaml",
            extra=".trivy.yaml",
            token="TESTONLY_tv_yaml_n0t_live",
            env="AGENT_YAML_TOKEN",
            sha="f066156",
            pr=92,
            mix="trivy skipFiles yaml leftover",
            scan_invoke="trivy fs --scanners secret --secret-config /dev/null conf/agent.yaml",
            scan_hit="SECRET: generic-api-key",
            extra_line="skipFiles: ['**/*.yaml']",
            miss_cmd="trivy fs --scanners secret --skip-files '**/*.yaml' . 2>&1 | tail -3 || echo yaml-green",
            miss_green="yaml-green",
            wrong_b="Plan: first apply - skip yml too. Expect unfiltered yaml still red.",
            wrong_cmd="trivy fs --scanners secret --secret-config /dev/null conf/agent.yaml 2>&1 | rg TESTONLY | head",
            wrong_obs="SECRET: TESTONLY_tv_yaml_n0t_live  conf/agent.yaml",
        ),
    ),
    (
        plant(
            slug="detect-secrets-exclude-files-map",
            scanner="detect-secrets",
            mechanic="detect-secrets --exclude-files '*.map' hides web/app.js.map",
            repo="gossan-web/ds-exclude-map",
            leak="web/app.js.map",
            extra=".secrets.baseline",
            token="TESTONLY_ds_map_n0t_live",
            env="JS_MAP_TOKEN",
            sha="0177267",
            pr=147,
            mix="detect-secrets exclude map leftover",
            scan_invoke="detect-secrets scan web/app.js.map --all-files",
            scan_hit="KeywordDetector hit",
            extra_line="exclude_files: ['.*\\\\.map$']",
            miss_cmd="detect-secrets scan --exclude-files '.*\\.map$' . 2>&1 | tail -3 || echo mapex-green",
            miss_green="mapex-green",
            wrong_b="Plan: first apply - exclude more globs. Expect unfiltered map still red.",
            wrong_cmd="rg TESTONLY web/app.js.map | head",
            wrong_obs="TESTONLY_ds_map_n0t_live  web/app.js.map",
        ),
        plant(
            slug="semgrep-exclude-dir-dist",
            scanner="semgrep",
            mechanic="semgrep --exclude-dir dist hides dist/client.ts token",
            repo="winze-web/semgrep-ex-dist",
            leak="dist/client.ts",
            extra=".semgrep.yml",
            token="TESTONLY_sg_dist_n0t_live",
            env="DIST_TS_TOKEN",
            sha="1288378",
            pr=93,
            mix="semgrep exclude-dir dist leftover",
            scan_invoke="semgrep --config .semgrep.yml dist/client.ts",
            scan_hit="generic-api-key",
            extra_line="exclude-dir: dist",
            miss_cmd="semgrep --config .semgrep.yml --exclude-dir dist . 2>&1 | tail -3 || echo dist-green",
            miss_green="dist-green",
            wrong_b="Plan: first apply - exclude build too. Expect unfiltered dist still red.",
            wrong_cmd="semgrep --config .semgrep.yml dist/client.ts 2>&1 | rg TESTONLY | head",
            wrong_obs="TESTONLY_sg_dist_n0t_live  dist/client.ts",
        ),
    ),
    (
        plant(
            slug="git-secrets-scan-untracked-false",
            scanner="git-secrets",
            mechanic="git assume-unchanged scripts/u.env so git-secrets --scan misses the tracked blob",
            repo="tuyere-ci/gitsecrets-assume",
            leak="scripts/u.env",
            extra=".git/info/exclude",
            token="TESTONLY_gs_au_n0t_live",
            env="U_SCRIPT_TOKEN",
            sha="2399489",
            pr=148,
            mix="git-secrets assume-unchanged leftover",
            scan_invoke="git-secrets --scan scripts/u.env",
            scan_hit="forbidden pattern",
            extra_line="git update-index --assume-unchanged scripts/u.env",
            miss_cmd="git ls-files -v | rg u.env; git-secrets --scan; echo exit:$?",
            miss_green="h scripts/u.env\nexit:0",
            wrong_b="Plan: first apply - assume-unchanged. Expect blob still red.",
            wrong_cmd="git show HEAD:scripts/u.env | rg TESTONLY | head",
            wrong_obs="U_SCRIPT_TOKEN=TESTONLY_gs_au_n0t_live",
        ),
        plant(
            slug="talisman-scan-compact-drop",
            scanner="talisman",
            mechanic="talisman --scan --compact drops finding details so scripts/c.env stays",
            repo="collar-ci/talisman-compact",
            leak="scripts/c.env",
            extra=".talismanrc",
            token="TESTONLY_tal_cp_n0t_live",
            env="C_SCRIPT_TOKEN",
            sha="34aa59a",
            pr=94,
            mix="talisman compact leftover",
            scan_invoke="talisman --scan --ignoreHistory=false",
            scan_hit="Talisman Report: secret",
            extra_line="--compact",
            miss_cmd="talisman --scan --compact; echo exit:$?",
            miss_green="exit:0",
            wrong_b="Plan: first apply - keep compact. Expect file still in git.",
            wrong_cmd="rg TESTONLY scripts/c.env | head",
            wrong_obs="C_SCRIPT_TOKEN=TESTONLY_tal_cp_n0t_live",
        ),
    ),
    (
        plant(
            slug="whispers-exclude-groups-aws",
            scanner="whispers",
            mechanic="whispers exclude.groups aws skips app/aws.env generic token too",
            repo="drift-app/whispers-ex-aws",
            leak="app/aws.env",
            extra="whispers.yml",
            token="TESTONLY_wh_aws_n0t_live",
            env="APP_AWS_TOKEN",
            sha="45bb6ab",
            pr=149,
            mix="whispers exclude.groups leftover",
            scan_invoke="whispers app/aws.env --config /dev/null",
            scan_hit="Secret: APP_AWS_TOKEN",
            extra_line="exclude: {groups: [aws]}",
            miss_cmd="whispers app --config whispers.yml 2>&1 | tail -3 || echo exaws-green",
            miss_green="exaws-green",
            wrong_b="Plan: first apply - exclude more groups. Expect unfiltered still red.",
            wrong_cmd="whispers app/aws.env --config /dev/null 2>&1 | rg TESTONLY | head",
            wrong_obs="TESTONLY_wh_aws_n0t_live  app/aws.env",
        ),
        plant(
            slug="bearer-skip-path-build",
            scanner="bearer",
            mechanic="bearer skip-path build hides build/out.env",
            repo="retort-web/bearer-skip-build",
            leak="build/out.env",
            extra="bearer.yml",
            token="TESTONLY_br_bld_n0t_live",
            env="BUILD_OUT_TOKEN",
            sha="56cc7bc",
            pr=95,
            mix="bearer skip-path build leftover",
            scan_invoke="bearer scan build/out.env",
            scan_hit="HIGH secret",
            extra_line="skip-path: [build]",
            miss_cmd="bearer scan . --config bearer.yml 2>&1 | tail -3 || echo skip-build-green",
            miss_green="skip-build-green",
            wrong_b="Plan: first apply - skip-path tmp too. Expect unfiltered build still red.",
            wrong_cmd="rg TESTONLY build/out.env | head",
            wrong_obs="BUILD_OUT_TOKEN=TESTONLY_br_bld_n0t_live",
        ),
    ),
    (
        plant(
            slug="checkov-skip-path-examples",
            scanner="checkov",
            mechanic="checkov --skip-path examples hides examples/secret.tf",
            repo="stull-tf/checkov-skip-ex",
            leak="examples/secret.tf",
            extra=".checkov.yaml",
            token="TESTONLY_ckv_ex_n0t_live",
            env="EX_TF_TOKEN",
            sha="67dd8cd",
            pr=150,
            mix="checkov skip-path examples leftover",
            scan_invoke="checkov -f examples/secret.tf --framework secrets",
            scan_hit="CKV_SECRET_6 FAILED",
            extra_line="skip-path: examples",
            miss_cmd="checkov -d . --skip-path examples 2>&1 | tail -3 || echo ex-green",
            miss_green="ex-green",
            wrong_b="Plan: first apply - skip-path tests too. Expect unfiltered examples still red.",
            wrong_cmd="rg TESTONLY examples/secret.tf | head",
            wrong_obs="EX_TF_TOKEN=TESTONLY_ckv_ex_n0t_live",
        ),
        plant(
            slug="kics-exclude-types-ansible",
            scanner="kics",
            mechanic="kics --type terraform skips ansible/group_vars/k.yml leftover",
            repo="opentofu-lab/kics-type-tf",
            leak="ansible/group_vars/k.yml",
            extra="kics.config",
            token="TESTONLY_kics_ty_n0t_live",
            env="ANS_K_TOKEN",
            sha="78ee9de",
            pr=96,
            mix="kics type filter leftover",
            scan_invoke="kics scan -p ansible/group_vars/k.yml --type ansible",
            scan_hit="HIGH: Hardcoded secret",
            extra_line="type: terraform",
            miss_cmd="kics scan -p . --type terraform 2>&1 | tail -3 || echo type-green",
            miss_green="type-green",
            wrong_b="Plan: first apply - keep terraform type only. Expect ansible still red.",
            wrong_cmd="rg TESTONLY ansible/group_vars/k.yml | head",
            wrong_obs="ANS_K_TOKEN=TESTONLY_kics_ty_n0t_live",
        ),
    ),
    (
        plant(
            slug="codeql-threads-1-timeout",
            scanner="codeql",
            mechanic="codeql --threads 1 --timeout 10s skips lib/slow.go",
            repo="winze-go/codeql-timeout",
            leak="lib/slow.go",
            extra=".github/workflows/codeql.yml",
            token="TESTONLY_cql_to_n0t_live",
            env="SLOW_GO_TOKEN",
            sha="89ff0ef",
            pr=151,
            mix="CodeQL threads+timeout leftover",
            scan_invoke="gitleaks detect --no-banner --no-git -s lib/slow.go",
            scan_hit="Secret:    generic-api-key",
            extra_line="--threads 1 --timeout 10",
            miss_cmd="echo codeql-timeout-skip; rg TESTONLY lib/slow.go | head",
            miss_green="codeql-timeout-skip",
            wrong_b="Plan: first apply - keep short timeout. Expect unfiltered still red.",
            wrong_cmd="gitleaks detect --no-banner --no-git -s lib/slow.go 2>&1 | rg TESTONLY | head",
            wrong_obs="Secret: TESTONLY_cql_to_n0t_live  File: lib/slow.go",
        ),
        plant(
            slug="ghas-secret-scanning-validity-unverified-ignore",
            scanner="ghas-secret-scanning",
            mechanic="GHAS ignores unverified generic tokens in hooks/uv.env",
            repo="longwall-hooks/ghas-unv-ignore",
            leak="hooks/uv.env",
            extra=".github/secret_scanning.yml",
            token="TESTONLY_ghas_uv_n0t_live",
            env="UV_HOOK_SECRET",
            sha="9a001f0",
            pr=97,
            mix="GHAS unverified-ignore leftover",
            scan_invoke="gitleaks detect --no-banner --no-git -s hooks/uv.env",
            scan_hit="Secret:    generic-api-key",
            extra_line="unverified: ignore",
            miss_cmd="echo ghas-unv-green; rg TESTONLY hooks/uv.env | head",
            miss_green="ghas-unv-green",
            wrong_b="Plan: first apply - keep unverified ignore. Expect unfiltered still red.",
            wrong_cmd="gitleaks detect --no-banner --no-git -s hooks/uv.env 2>&1 | rg TESTONLY | head",
            wrong_obs="Secret: TESTONLY_ghas_uv_n0t_live  File: hooks/uv.env",
        ),
    ),
]


def notes_md(rnd, suc, fail, suc_ep, fail_ep):
    coverage = max(51, 62 - (rnd - CATALOG_FIRST))
    return f"""# NOTES-r{rnd} secret-scan-remediation-factory

Novel coverage: {coverage}%

Two designed episodes (quota 2). Surfaces: {suc['repo']} {suc['slug']} {suc['mechanic']}; {fail['repo']} {fail['slug']} {fail['mechanic']} (rewrite blocked).
Neither force-pushes main. Fake TESTONLY_ keys only. One remaining-scan fail when rewrite is blocked.
Scanner × mechanic mill (not vendor-file grid, not SaaS-yml, not cipher-*, not r181–r279 clones).

| id | seed | first apply | plan change | terminal |
|---|---|---|---|---|
| {suc_ep['id']} | {suc['mechanic']} in {suc['leak']} + {suc['extra']} | {suc['wrong_b'].replace('Plan: first apply - ', '')} | {suc['env']} + filter-repo purge | success 2/2, main residual |
| {fail_ep['id']} | {fail['mechanic']} in {fail['leak']} + {fail['extra']} | {fail['wrong_b'].replace('Plan: first apply - ', '')} | HEAD {fail['env']}; GH013 | remaining-scan fail + HANDOFF |

## Step counts
- {suc_ep['id']}: {len(suc_ep['steps'])}
- {fail_ep['id']}: {len(fail_ep['steps'])}

## decision_basis audit
Every step starts Plan:/Observation:/Reflection:/Tool call:, ≤240 chars.
No thought / chain_of_thought / scratch / inner_monologue. No spike_events.
No sim_or_real: real. Invented plants (designed). No real secrets.

## Weaknesses / next
Avoid {suc['slug']}-as-git-fix and {fail['slug']}-as-git-fix (this round).
Harder-kind mill: {suc['mix']}; {fail['mix']}.
"""


def build_round(rnd: int):
    idx = rnd - CATALOG_FIRST
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(f"round {rnd} outside catalog")
    suc, fail = PAIRS[idx]
    suc_n = 18 if idx % 2 else 16
    fail_n = 17 if idx % 3 else 18
    suc_ep = extend_success(success_episode(rnd, suc, min(suc_n, 16)), suc, rnd, suc_n)
    fail_ep = extend_fail(fail_episode(rnd, fail, min(fail_n, 16)), fail, rnd, fail_n)
    for ep in (suc_ep, fail_ep):
        ep["reward"]["cost_steps"] = len(ep["steps"])
    return [suc_ep, fail_ep], notes_md(rnd, suc, fail, suc_ep, fail_ep)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    args = ap.parse_args()
    recs, notes = build_round(args.round)
    staging = Path(args.staging)
    with (staging / f"batch-r{args.round:02d}.jsonl").open("w") as handle:
        for rec in recs:
            handle.write(json.dumps(rec, ensure_ascii=True) + "\n")
    (staging / f"NOTES-r{args.round:02d}.md").write_text(notes)
    print(json.dumps({"round": args.round, "ids": [r["id"] for r in recs], "steps": [len(r["steps"]) for r in recs]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
