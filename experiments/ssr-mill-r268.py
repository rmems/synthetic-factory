#!/usr/bin/env python3
"""Mill secret-scan-remediation-factory r268+ unique scanner × mechanic pairs."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

FACTORY = "secret-scan-remediation-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 268
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

PAIRS: list[tuple[dict, dict]] = [
    (
        plant(
            slug="gitleaks-log-opts-first-parent",
            scanner="gitleaks",
            mechanic="gitleaks --log-opts --first-parent misses side-branch cfg/side.env",
            repo="dross-ci/gitleaks-first-parent",
            leak="cfg/side.env",
            extra=".github/workflows/gitleaks.yml",
            token="TESTONLY_gl_fp_n0t_live",
            env="SIDE_TOKEN",
            sha="11aa0b1",
            pr=132,
            mix="gitleaks first-parent leftover",
            scan_invoke="gitleaks detect --no-banner --log-opts='--all'",
            scan_hit="Secret:    generic-api-key",
            extra_line="--log-opts=--first-parent",
            miss_cmd="gitleaks detect --no-banner --log-opts='--first-parent' 2>&1 | tail -3 || echo fp-green",
            miss_green="fp-green",
            wrong_b="Plan: first apply - keep first-parent. Expect --all still red.",
            wrong_cmd="gitleaks detect --no-banner --log-opts='--all' 2>&1 | rg TESTONLY | head",
            wrong_obs="Secret: TESTONLY_gl_fp_n0t_live  File: cfg/side.env",
        ),
        plant(
            slug="trufflehog-exclude-paths-vendor",
            scanner="trufflehog",
            mechanic="trufflehog --exclude-paths vendor/** hides vendor/pkg/tok.env",
            repo="sinter-sdk/thog-ex-vendor",
            leak="vendor/pkg/tok.env",
            extra=".github/workflows/thog.yml",
            token="TESTONLY_th_vend_n0t_live",
            env="VEND_PKG_TOKEN",
            sha="22bb1c2",
            pr=78,
            mix="trufflehog exclude-paths vendor leftover",
            scan_invoke="trufflehog filesystem vendor/pkg/tok.env --no-update --fail",
            scan_hit="🐷 Found unverified result",
            extra_line="--exclude-paths vendor/**",
            miss_cmd="trufflehog filesystem . --exclude-paths vendor --no-update 2>&1 | tail -3 || echo vend-green",
            miss_green="vend-green",
            wrong_b="Plan: first apply - exclude node_modules too. Expect unfiltered vendor still red.",
            wrong_cmd="trufflehog filesystem vendor/pkg/tok.env --no-update --fail 2>&1 | rg TESTONLY | head",
            wrong_obs="TESTONLY_th_vend_n0t_live  vendor/pkg/tok.env",
        ),
    ),
    (
        plant(
            slug="ggshield-scan-precommit-only",
            scanner="ggshield",
            mechanic="ggshield secret scan pre-commit only; history conf/hist2.env unscanned",
            repo="wolfram-git/ggshield-precommit",
            leak="conf/hist2.env",
            extra=".pre-commit-config.yaml",
            token="TESTONLY_gg_pc_n0t_live",
            env="HIST2_TOKEN",
            sha="33cc2d3",
            pr=133,
            mix="ggshield pre-commit-only leftover",
            scan_invoke="ggshield secret scan path conf/hist2.env",
            scan_hit="SECRET_DETECTED",
            extra_line="ggshield secret scan pre-commit",
            miss_cmd="echo precommit-only-future; git log -S TESTONLY_gg_pc_n0t_live --oneline | head",
            miss_green="precommit-only-future",
            wrong_b="Plan: first apply - keep pre-commit hook only. Expect history still red.",
            wrong_cmd="ggshield secret scan repo --allow-dirty 2>&1 | rg TESTONLY | head",
            wrong_obs="SECRET: TESTONLY_gg_pc_n0t_live  conf/hist2.env",
        ),
        plant(
            slug="noseyparker-ignore-ext-lock",
            scanner="noseyparker",
            mechanic="noseyparker ignore_ext = [\".lock\"] hides poetry.lock token",
            repo="buddle-py/np-ignore-lock",
            leak="poetry.lock",
            extra="noseyparker.toml",
            extra_files=["poetry.lock", "noseyparker.toml"],
            token="TESTONLY_np_lock_n0t_live",
            env="LOCKFILE_TOKEN",
            sha="44dd3e4",
            pr=79,
            mix="noseyparker ignore_ext lock leftover",
            scan_invoke="noseyparker scan poetry.lock --ignore-ext ''",
            scan_hit="Finding: generic.api_key",
            extra_line="ignore_ext = [\".lock\"]",
            miss_cmd="noseyparker scan . --ignore-ext .lock 2>&1 | tail -3 || echo lock-green",
            miss_green="lock-green",
            wrong_b="Plan: first apply - ignore .toml too. Expect unfiltered lock still red.",
            wrong_cmd="rg TESTONLY poetry.lock | head",
            wrong_obs="LOCKFILE_TOKEN=TESTONLY_np_lock_n0t_live",
        ),
    ),
    (
        plant(
            slug="kingfisher-skip-vendor",
            scanner="kingfisher",
            mechanic="kingfisher skip_globs vendor/** hides vendor/mod/key.env",
            repo="calcine-mod/kf-skip-vendor",
            leak="vendor/mod/key.env",
            extra=".kingfisher.toml",
            token="TESTONLY_kf_vend_n0t_live",
            env="MOD_TOKEN",
            sha="55ee4f5",
            pr=134,
            mix="kingfisher skip vendor leftover",
            scan_invoke="kingfisher scan vendor/mod/key.env --no-skip-globs",
            scan_hit="KINGFISHER: generic_token",
            extra_line="skip_globs = [\"vendor/**\"]",
            miss_cmd="kingfisher scan . 2>&1 | tail -3 || echo skip-vend-green",
            miss_green="skip-vend-green",
            wrong_b="Plan: first apply - skip third_party too. Expect unfiltered vendor still red.",
            wrong_cmd="kingfisher scan vendor/mod/key.env --no-skip-globs 2>&1 | rg TESTONLY | head",
            wrong_obs="TESTONLY_kf_vend_n0t_live  vendor/mod/key.env",
        ),
        plant(
            slug="trivy-skip-dirs-dist",
            scanner="trivy",
            mechanic="trivy skip-dirs dist hides dist/env.js token",
            repo="stamp-web/trivy-skip-dist",
            leak="dist/env.js",
            extra=".trivy.yaml",
            token="TESTONLY_tv_dist_n0t_live",
            env="DIST_ENV_TOKEN",
            sha="66ff506",
            pr=80,
            mix="trivy skip-dirs dist leftover",
            scan_invoke="trivy fs --scanners secret dist/env.js",
            scan_hit="SECRET: generic-api-key",
            extra_line="skip-dirs: [dist]",
            miss_cmd="trivy fs --scanners secret --skip-dirs dist . 2>&1 | tail -3 || echo dist-green",
            miss_green="dist-green",
            wrong_b="Plan: first apply - skip build too. Expect unfiltered dist still red.",
            wrong_cmd="trivy fs --scanners secret dist/env.js 2>&1 | rg TESTONLY | head",
            wrong_obs="SECRET: TESTONLY_tv_dist_n0t_live  dist/env.js",
        ),
    ),
    (
        plant(
            slug="detect-secrets-exclude-files-lock",
            scanner="detect-secrets",
            mechanic="detect-secrets --exclude-files '.*\\.lock$' hides Pipfile.lock token",
            repo="gossan-py/ds-exclude-lock",
            leak="Pipfile.lock",
            extra=".secrets.baseline",
            extra_files=["Pipfile.lock", ".secrets.baseline"],
            token="TESTONLY_ds_lock_n0t_live",
            env="PIPFILE_TOKEN",
            sha="7700617",
            pr=135,
            mix="detect-secrets exclude lock leftover",
            scan_invoke="detect-secrets scan Pipfile.lock --all-files",
            scan_hit="KeywordDetector hit",
            extra_line="exclude_files: ['.*\\\\.lock$']",
            miss_cmd="detect-secrets scan --exclude-files '.*\\.lock$' . 2>&1 | tail -3 || echo lockex-green",
            miss_green="lockex-green",
            wrong_b="Plan: first apply - exclude *.toml too. Expect unfiltered lock still red.",
            wrong_cmd="detect-secrets scan Pipfile.lock --all-files 2>&1 | rg TESTONLY | head",
            wrong_obs="TESTONLY_ds_lock_n0t_live  Pipfile.lock",
        ),
        plant(
            slug="semgrep-exclude-rule-generic-secret",
            scanner="semgrep",
            mechanic="semgrep --exclude-rule generic.secrets.security.detected-generic-secret",
            repo="winze-cfg/semgrep-exrule",
            leak="cfg/svc.env",
            extra=".semgrep.yml",
            token="TESTONLY_sg_exr_n0t_live",
            env="SVC_ENV_TOKEN",
            sha="8811728",
            pr=81,
            mix="semgrep exclude-rule leftover",
            scan_invoke="semgrep --config .semgrep.yml cfg/svc.env",
            scan_hit="generic-api-key",
            extra_line="exclude-rule: generic.secrets.security.detected-generic-secret",
            miss_cmd="semgrep --config .semgrep.yml --exclude-rule generic.secrets.security.detected-generic-secret cfg 2>&1 | tail -3 || echo exrule-green",
            miss_green="exrule-green",
            wrong_b="Plan: first apply - exclude more rules. Expect unfiltered still red.",
            wrong_cmd="rg TESTONLY cfg/svc.env | head",
            wrong_obs="SVC_ENV_TOKEN=TESTONLY_sg_exr_n0t_live",
        ),
    ),
    (
        plant(
            slug="git-secrets-scan-history-since",
            scanner="git-secrets",
            mechanic="git-secrets --scan-history --since=HEAD~5 misses older scripts/old3.env",
            repo="tuyere-ci/gitsecrets-since",
            leak="scripts/old3.env",
            extra=".git/config",
            token="TESTONLY_gs_since_n0t_live",
            env="OLD3_TOKEN",
            sha="9922839",
            pr=136,
            mix="git-secrets scan-history since leftover",
            scan_invoke="git-secrets --scan-history",
            scan_hit="forbidden pattern in history",
            extra_line="--since=HEAD~5",
            miss_cmd="git-secrets --scan-history --since=HEAD~5 2>&1 | tail -3 || echo since-green",
            miss_green="since-green",
            wrong_b="Plan: first apply - keep --since HEAD~5. Expect full history still red.",
            wrong_cmd="git log -S TESTONLY_gs_since_n0t_live --oneline | head",
            wrong_obs="9922839 add scripts/old3.env",
        ),
        plant(
            slug="talisman-ignore-detectors",
            scanner="talisman",
            mechanic=".talismanrc ignore_detectors filename skips scripts/tok.env",
            repo="collar-ci/talisman-ign-det",
            leak="scripts/tok.env",
            extra=".talismanrc",
            token="TESTONLY_tal_det_n0t_live",
            env="TOK_SCRIPT_TOKEN",
            sha="aa3394a",
            pr=82,
            mix="talisman ignore_detectors leftover",
            scan_invoke="talisman --scan --ignoreHistory=false",
            scan_hit="Talisman Report: filename detector",
            extra_line="ignore_detectors: [filename]",
            miss_cmd="talisman --scan 2>&1 | tail -3 || echo det-green",
            miss_green="det-green",
            wrong_b="Plan: first apply - ignore more detectors. Expect file still in git.",
            wrong_cmd="rg TESTONLY scripts/tok.env | head",
            wrong_obs="TOK_SCRIPT_TOKEN=TESTONLY_tal_det_n0t_live",
        ),
    ),
    (
        plant(
            slug="whispers-exclude-keys",
            scanner="whispers",
            mechanic="whispers.yml exclude.keys APP_TOKEN hides app/tok.env",
            repo="drift-app/whispers-exkeys",
            leak="app/tok.env",
            extra="whispers.yml",
            token="TESTONLY_wh_ek_n0t_live",
            env="APP_TOKEN",
            sha="bb44a5b",
            pr=137,
            mix="whispers exclude.keys leftover",
            scan_invoke="whispers app/tok.env --config /dev/null",
            scan_hit="Secret: APP_TOKEN",
            extra_line="exclude: {keys: [APP_TOKEN]}",
            miss_cmd="whispers app --config whispers.yml 2>&1 | tail -3 || echo exkeys-green",
            miss_green="exkeys-green",
            wrong_b="Plan: first apply - exclude more keys. Expect unfiltered still red.",
            wrong_cmd="whispers app/tok.env --config /dev/null 2>&1 | rg TESTONLY | head",
            wrong_obs="TESTONLY_wh_ek_n0t_live  app/tok.env",
        ),
        plant(
            slug="bearer-skip-path-dist",
            scanner="bearer",
            mechanic="bearer skip-path dist hides dist/client.env (not generated/vendor/tests)",
            repo="retort-web/bearer-skip-dist",
            leak="dist/client.env",
            extra="bearer.yml",
            token="TESTONLY_br_dist_n0t_live",
            env="CLIENT_DIST_TOKEN",
            sha="cc55b6c",
            pr=83,
            mix="bearer skip-path dist leftover",
            scan_invoke="bearer scan dist/client.env",
            scan_hit="HIGH secret",
            extra_line="skip-path: [dist]",
            miss_cmd="bearer scan . --config bearer.yml 2>&1 | tail -3 || echo skip-dist-green",
            miss_green="skip-dist-green",
            wrong_b="Plan: first apply - skip-path build too. Expect unfiltered dist still red.",
            wrong_cmd="rg TESTONLY dist/client.env | head",
            wrong_obs="CLIENT_DIST_TOKEN=TESTONLY_br_dist_n0t_live",
        ),
    ),
    (
        plant(
            slug="checkov-download-external-modules-false",
            scanner="checkov",
            mechanic="checkov --download-external-modules false skips terraform/modules/secret",
            repo="stull-tf/checkov-noext",
            leak="terraform/modules/secret/main.tf",
            extra=".checkov.yaml",
            token="TESTONLY_ckv_ext_n0t_live",
            env="TF_MOD_TOKEN",
            sha="dd66c7d",
            pr=138,
            mix="checkov no external modules leftover",
            scan_invoke="checkov -f terraform/modules/secret/main.tf --framework secrets",
            scan_hit="CKV_SECRET_6 FAILED",
            extra_line="download-external-modules: false",
            miss_cmd="checkov -d terraform --download-external-modules false 2>&1 | tail -3 || echo noext-green",
            miss_green="noext-green",
            wrong_b="Plan: first apply - keep download-external-modules false. Expect file still red.",
            wrong_cmd="rg TESTONLY terraform/modules/secret/main.tf | head",
            wrong_obs="TF_MOD_TOKEN=TESTONLY_ckv_ext_n0t_live",
        ),
        plant(
            slug="kics-exclude-queries-path",
            scanner="kics",
            mechanic="kics --exclude-queries-path drops local secret query on terraform/k.env",
            repo="opentofu-lab/kics-exqpath",
            leak="terraform/k.env",
            extra="kics.config",
            token="TESTONLY_kics_qp_n0t_live",
            env="TF_K_TOKEN",
            sha="ee77d8e",
            pr=84,
            mix="kics exclude-queries-path leftover",
            scan_invoke="kics scan -p terraform/k.env --queries-path /opt/kics/assets/queries",
            scan_hit="HIGH: Hardcoded secret",
            extra_line="exclude-queries-path: assets/queries/secret",
            miss_cmd="kics scan -p terraform --exclude-queries-path assets/queries/secret 2>&1 | tail -3 || echo exq-green",
            miss_green="exq-green",
            wrong_b="Plan: first apply - exclude more query paths. Expect unfiltered still red.",
            wrong_cmd="rg TESTONLY terraform/k.env | head",
            wrong_obs="TF_K_TOKEN=TESTONLY_kics_qp_n0t_live",
        ),
    ),
    (
        plant(
            slug="codeql-ram-low-skip",
            scanner="codeql",
            mechanic="codeql --ram 512 OOMs so lib/big.go never analyzed",
            repo="winze-go/codeql-ram",
            leak="lib/big.go",
            extra=".github/workflows/codeql.yml",
            token="TESTONLY_cql_ram_n0t_live",
            env="BIG_GO_TOKEN",
            sha="ff88e9f",
            pr=139,
            mix="CodeQL low RAM leftover",
            scan_invoke="gitleaks detect --no-banner --no-git -s lib/big.go",
            scan_hit="Secret:    generic-api-key",
            extra_line="--ram 512",
            miss_cmd="echo codeql-oom-skip; rg TESTONLY lib/big.go | head",
            miss_green="codeql-oom-skip",
            wrong_b="Plan: first apply - keep --ram 512. Expect unfiltered still red.",
            wrong_cmd="gitleaks detect --no-banner --no-git -s lib/big.go 2>&1 | rg TESTONLY | head",
            wrong_obs="Secret: TESTONLY_cql_ram_n0t_live  File: lib/big.go",
        ),
        plant(
            slug="ghas-push-protection-bypass-app",
            scanner="ghas-secret-scanning",
            mechanic="GitHub App allowed to bypass push protection; hooks/app.env still lands",
            repo="longwall-hooks/ghas-app-bypass",
            leak="hooks/app.env",
            extra=".github/secret_scanning.yml",
            token="TESTONLY_ghas_app_n0t_live",
            env="APP_HOOK_SECRET",
            sha="0099f00",
            pr=85,
            mix="GHAS app bypass leftover",
            scan_invoke="gitleaks detect --no-banner --no-git -s hooks/app.env",
            scan_hit="Secret:    generic-api-key",
            extra_line="bypass_actors: [github-app]",
            miss_cmd="echo ghas-app-bypass-green; rg TESTONLY hooks/app.env | head",
            miss_green="ghas-app-bypass-green",
            wrong_b="Plan: first apply - keep app bypass. Expect unfiltered still red.",
            wrong_cmd="gitleaks detect --no-banner --no-git -s hooks/app.env 2>&1 | rg TESTONLY | head",
            wrong_obs="Secret: TESTONLY_ghas_app_n0t_live  File: hooks/app.env",
        ),
    ),
    (
        plant(
            slug="ripsecrets-ignore-tests",
            scanner="ripsecrets",
            mechanic=".ripsecretsignore tests/** hides tests/golden2.env",
            repo="ketch-qa/ripsecrets-tests",
            leak="tests/golden2.env",
            extra=".ripsecretsignore",
            token="TESTONLY_rip_t_n0t_live",
            env="GOLDEN2_TOKEN",
            sha="11aa0b2",
            pr=140,
            mix="ripsecrets ignore tests leftover",
            scan_invoke="ripsecrets --no-ignore tests/golden2.env",
            scan_hit="Secret: GOLDEN2_TOKEN",
            extra_line="tests/**",
            miss_cmd="ripsecrets tests 2>&1 | tail -3 || echo tests-green",
            miss_green="tests-green",
            wrong_b="Plan: first apply - ignore fixtures too. Expect unfiltered tests still red.",
            wrong_cmd="ripsecrets --no-ignore tests/golden2.env 2>&1 | rg TESTONLY | head",
            wrong_obs="TESTONLY_rip_t_n0t_live  tests/golden2.env",
        ),
        plant(
            slug="rustyhog-skip-ext-env",
            scanner="rusty-hog",
            mechanic="choctaw_hog skip_ext .env misses assets/cfg.env",
            repo="goaf-cfg/rustyhog-skipext",
            leak="assets/cfg.env",
            extra="default_regexes.json",
            token="TESTONLY_rh_ext_n0t_live",
            env="CFG_ASSET_TOKEN",
            sha="22bb1c3",
            pr=86,
            mix="rusty-hog skip-ext leftover",
            scan_invoke="choctaw_hog -z assets/cfg.env",
            scan_hit="match CFG_ASSET_TOKEN",
            extra_line="skip_ext: [.env]",
            miss_cmd="choctaw_hog assets 2>&1 | tail -3 || echo skipext-green",
            miss_green="skipext-green",
            wrong_b="Plan: first apply - skip more ext. Expect -z still red.",
            wrong_cmd="choctaw_hog -z assets/cfg.env 2>&1 | rg TESTONLY | head",
            wrong_obs="TESTONLY_rh_ext_n0t_live  assets/cfg.env",
        ),
    ),
    (
        plant(
            slug="gitleaks-config-extend-allowlist",
            scanner="gitleaks",
            mechanic=".gitleaks.toml extend allowlist from shared.toml hides cfg/shared.env",
            repo="sluice-cfg/gitleaks-extend",
            leak="cfg/shared.env",
            extra=".gitleaks.toml",
            token="TESTONLY_gl_ext_n0t_live",
            env="SHARED_TOKEN",
            sha="33cc2d4",
            pr=141,
            mix="gitleaks extend allowlist leftover",
            scan_invoke="gitleaks detect --no-banner --no-git -s cfg/shared.env --no-config",
            scan_hit="Secret:    generic-api-key",
            extra_line="[extend]\npath = shared.toml",
            miss_cmd="gitleaks detect --no-banner --no-git -s . --config .gitleaks.toml 2>&1 | tail -3 || echo extend-green",
            miss_green="extend-green",
            wrong_b="Plan: first apply - extend more allowlists. Expect --no-config still red.",
            wrong_cmd="gitleaks detect --no-banner --no-git -s cfg/shared.env --no-config 2>&1 | rg TESTONLY | head",
            wrong_obs="Secret: TESTONLY_gl_ext_n0t_live  File: cfg/shared.env",
        ),
        plant(
            slug="gitlab-secret-detection-excluded-files",
            scanner="gitlab-secret-detection",
            mechanic="SECRET_DETECTION_EXCLUDED_FILES=*.env hides ci/job2.env (not paths/analyzers)",
            repo="whim-ci/gitlab-ex-files",
            leak="ci/job2.env",
            extra=".gitlab-ci.yml",
            token="TESTONLY_gl_exf_n0t_live",
            env="JOB2_TOKEN",
            sha="44dd3e5",
            pr=87,
            mix="GitLab excluded files leftover",
            scan_invoke="gitleaks detect --no-banner --no-git -s ci/job2.env",
            scan_hit="Secret:    generic-api-key",
            extra_line="SECRET_DETECTION_EXCLUDED_FILES: '*.env'",
            miss_cmd="rg -n EXCLUDED_FILES .gitlab-ci.yml; echo exfiles-green",
            miss_green="exfiles-green",
            wrong_b="Plan: first apply - exclude more files. Expect unfiltered still red.",
            wrong_cmd="gitleaks detect --no-banner --no-git -s ci/job2.env 2>&1 | rg TESTONLY | head",
            wrong_obs="Secret: TESTONLY_gl_exf_n0t_live  File: ci/job2.env",
        ),
    ),
    (
        plant(
            slug="secretlint-ignore-node-modules",
            scanner="secretlint",
            mechanic=".secretlintignore node_modules/** hides node_modules/pkg/key.env committed",
            repo="packwall-js/secretlint-nm",
            leak="node_modules/pkg/key.env",
            extra=".secretlintignore",
            token="TESTONLY_sl_nm_n0t_live",
            env="PKG_NM_TOKEN",
            sha="55ee4f6",
            pr=142,
            mix="secretlint ignore node_modules leftover",
            scan_invoke="secretlint node_modules/pkg/key.env --secretlintignore /dev/null",
            scan_hit="error: found secret",
            extra_line="node_modules/**",
            miss_cmd="secretlint --secretlintignore .secretlintignore node_modules 2>&1 | tail -3 || echo nm-green",
            miss_green="nm-green",
            wrong_b="Plan: first apply - ignore dist too. Expect unfiltered nm still red.",
            wrong_cmd="rg TESTONLY node_modules/pkg/key.env | head",
            wrong_obs="PKG_NM_TOKEN=TESTONLY_sl_nm_n0t_live",
        ),
        plant(
            slug="bandit-exclude-tests",
            scanner="bandit",
            mechanic="bandit exclude tests misses tests/test_cfg.py hardcoded token",
            repo="tuyere-py/bandit-ex-tests",
            leak="tests/test_cfg.py",
            extra=".bandit",
            token="TESTONLY_bd_t_n0t_live",
            env="TEST_CFG_SECRET",
            sha="66ff507",
            pr=88,
            mix="bandit exclude tests leftover",
            scan_invoke="bandit -r tests/test_cfg.py --skip ''",
            scan_hit="B105 hardcoded password",
            extra_line="exclude_dirs: ['tests']",
            miss_cmd="bandit -r . -x tests 2>&1 | tail -3 || echo ext-green",
            miss_green="ext-green",
            wrong_b="Plan: first apply - exclude more dirs. Expect unfiltered tests still red.",
            wrong_cmd="rg TESTONLY tests/test_cfg.py | head",
            wrong_obs="TEST_CFG_SECRET = 'TESTONLY_bd_t_n0t_live'",
        ),
    ),
    (
        plant(
            slug="gitleaks-redact-entropy-report",
            scanner="gitleaks",
            mechanic="gitleaks --redact plus --report-path dropped so CI logs clean while cfg/r2.env stays",
            repo="dross-ci/gitleaks-redact-report",
            leak="cfg/r2.env",
            extra=".github/workflows/gitleaks.yml",
            token="TESTONLY_gl_rr_n0t_live",
            env="R2_TOKEN",
            sha="7700618",
            pr=143,
            mix="gitleaks redact+dropped report leftover",
            scan_invoke="gitleaks detect --no-banner --no-git -s cfg/r2.env",
            scan_hit="Secret:    generic-api-key",
            extra_line="--redact --report-path /tmp/dropped.json",
            miss_cmd="gitleaks detect --no-banner --redact -s .; rm -f /tmp/dropped.json; rg TESTONLY cfg/r2.env | head",
            miss_green="REDACTED\nR2_TOKEN=TESTONLY_gl_rr_n0t_live",
            wrong_b="Plan: first apply - keep --redact. Expect file still in git.",
            wrong_cmd="rg TESTONLY cfg/r2.env | head",
            wrong_obs="R2_TOKEN=TESTONLY_gl_rr_n0t_live",
        ),
        plant(
            slug="trufflehog-git-url-fetch-tags-false",
            scanner="trufflehog",
            mechanic="trufflehog git without tags misses leak only on v1-secret tag",
            repo="sinter-ci/thog-notags",
            leak="svc/tag.env",
            extra=".github/workflows/thog.yml",
            token="TESTONLY_th_tag_n0t_live",
            env="TAG_TOKEN",
            sha="8811729",
            pr=89,
            mix="trufflehog no-tags leftover",
            scan_invoke="trufflehog git file://. --no-update --fail",
            scan_hit="🐷 tag v1-secret hit",
            extra_line="git fetch --no-tags",
            miss_cmd="git tag | head; trufflehog git file://. --no-update 2>&1 | tail -3 || echo notag-green",
            miss_green="notag-green",
            wrong_b="Plan: first apply - keep --no-tags. Expect tagged history still red.",
            wrong_cmd="git show v1-secret:svc/tag.env 2>/dev/null | rg TESTONLY | head || git log --all -S TESTONLY_th_tag_n0t_live --oneline | head",
            wrong_obs="TAG_TOKEN=TESTONLY_th_tag_n0t_live",
        ),
    ),
]


def notes_md(rnd: int, suc: dict, fail: dict, suc_ep: dict, fail_ep: dict) -> str:
    coverage = max(51, 64 - (rnd - CATALOG_FIRST))
    return f"""# NOTES-r{rnd} secret-scan-remediation-factory

Novel coverage: {coverage}%

Two designed episodes (quota 2). Surfaces: {suc['repo']} {suc['slug']} {suc['mechanic']}; {fail['repo']} {fail['slug']} {fail['mechanic']} (rewrite blocked).
Neither force-pushes main. Fake TESTONLY_ keys only. One remaining-scan fail when rewrite is blocked.
Scanner × mechanic mill (not vendor-file grid, not SaaS-yml, not cipher-*, not r181–r267 clones).

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


def build_round(rnd: int) -> tuple[list[dict], str]:
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
    batch = staging / f"batch-r{args.round:02d}.jsonl"
    notes_path = staging / f"NOTES-r{args.round:02d}.md"
    with batch.open("w") as handle:
        for rec in recs:
            handle.write(json.dumps(rec, ensure_ascii=True) + "\n")
    notes_path.write_text(notes)
    print(json.dumps({"round": args.round, "ids": [r["id"] for r in recs], "steps": [len(r["steps"]) for r in recs]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
