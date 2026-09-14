#!/usr/bin/env python3
"""Mill secret-scan-remediation-factory r288+ unique scanner × mechanic pairs."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

FACTORY = "secret-scan-remediation-factory"
CATALOG_FIRST = 288
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
            slug="gitleaks-linguist-generated-skip",
            scanner="gitleaks",
            mechanic=".gitattributes linguist-generated on generated/keys.ts skipped by some CI wrappers",
            repo="dross-js/gitleaks-linguist-gen",
            leak="generated/keys.ts",
            extra=".gitattributes",
            token="TESTONLY_gl_ling_n0t_live",
            env="GEN_KEYS_TOKEN",
            sha="a011b12",
            pr=152,
            mix="gitleaks linguist-generated leftover",
            scan_invoke="gitleaks detect --no-banner --no-git -s generated/keys.ts",
            scan_hit="Secret:    generic-api-key",
            extra_line="generated/** linguist-generated",
            miss_cmd="rg linguist-generated .gitattributes; echo wrapper-skip-green",
            miss_green="wrapper-skip-green",
            wrong_b="Plan: first apply - mark more paths generated. Expect unfiltered still red.",
            wrong_cmd="gitleaks detect --no-banner --no-git -s generated/keys.ts 2>&1 | rg TESTONLY | head",
            wrong_obs="Secret: TESTONLY_gl_ling_n0t_live  File: generated/keys.ts",
        ),
        plant(
            slug="trufflehog-exclude-paths-generated",
            scanner="trufflehog",
            mechanic="trufflehog --exclude-paths generated/** hides generated/env.ts",
            repo="sinter-api/thog-ex-gen",
            leak="generated/env.ts",
            extra=".github/workflows/thog.yml",
            token="TESTONLY_th_gen_n0t_live",
            env="GEN_ENV_TOKEN",
            sha="b122c23",
            pr=98,
            mix="trufflehog exclude-paths generated leftover",
            scan_invoke="trufflehog filesystem generated/env.ts --no-update --fail",
            scan_hit="🐷 Found unverified result",
            extra_line="--exclude-paths generated/**",
            miss_cmd="trufflehog filesystem . --exclude-paths generated --no-update 2>&1 | tail -3 || echo gen-green",
            miss_green="gen-green",
            wrong_b="Plan: first apply - exclude dist too. Expect unfiltered generated still red.",
            wrong_cmd="trufflehog filesystem generated/env.ts --no-update --fail 2>&1 | rg TESTONLY | head",
            wrong_obs="TESTONLY_th_gen_n0t_live  generated/env.ts",
        ),
    ),
    (
        plant(
            slug="ggshield-scan-repo-shallow-fetch",
            scanner="ggshield",
            mechanic="ggshield secret scan repo after fetch-depth 1 misses conf/deep2.env history",
            repo="wolfram-ci/ggshield-shallow",
            leak="conf/deep2.env",
            extra=".github/workflows/ggshield.yml",
            token="TESTONLY_gg_sh_n0t_live",
            env="DEEP2_TOKEN",
            sha="c233d34",
            pr=153,
            mix="ggshield shallow fetch leftover",
            scan_invoke="ggshield secret scan path conf/deep2.env",
            scan_hit="SECRET_DETECTED",
            extra_line="fetch-depth: 1 then scan repo",
            miss_cmd="git rev-list --count HEAD; ggshield secret scan repo --allow-dirty 2>&1 | tail -3 || echo shallow-green",
            miss_green="1\nshallow-green",
            wrong_b="Plan: first apply - keep fetch-depth 1. Expect full history still red.",
            wrong_cmd="git log -S TESTONLY_gg_sh_n0t_live --oneline | head",
            wrong_obs="c233d34 add conf/deep2.env",
        ),
        plant(
            slug="noseyparker-ignore-path-vendor",
            scanner="noseyparker",
            mechanic="noseyparker --ignore-path vendor skips vendor/mod2/key.env",
            repo="buddle-mod/np-ignore-vendor",
            leak="vendor/mod2/key.env",
            extra="noseyparker.toml",
            token="TESTONLY_np_vend_n0t_live",
            env="MOD2_TOKEN",
            sha="d344e45",
            pr=99,
            mix="noseyparker ignore-path vendor leftover",
            scan_invoke="noseyparker scan vendor/mod2/key.env",
            scan_hit="Finding: generic.api_key",
            extra_line="ignore_path = \"vendor\"",
            miss_cmd="noseyparker scan --ignore-path vendor . 2>&1 | tail -3 || echo vend-green",
            miss_green="vend-green",
            wrong_b="Plan: first apply - ignore third_party too. Expect unfiltered vendor still red.",
            wrong_cmd="rg TESTONLY vendor/mod2/key.env | head",
            wrong_obs="MOD2_TOKEN=TESTONLY_np_vend_n0t_live",
        ),
    ),
    (
        plant(
            slug="kingfisher-skip-generated",
            scanner="kingfisher",
            mechanic="kingfisher skip_globs generated/** hides generated/client.env",
            repo="calcine-api/kf-skip-gen",
            leak="generated/client.env",
            extra=".kingfisher.toml",
            token="TESTONLY_kf_gen_n0t_live",
            env="GEN_CLIENT_TOKEN",
            sha="e455f56",
            pr=154,
            mix="kingfisher skip generated leftover",
            scan_invoke="kingfisher scan generated/client.env --no-skip-globs",
            scan_hit="KINGFISHER: generic_token",
            extra_line="skip_globs = [\"generated/**\"]",
            miss_cmd="kingfisher scan . 2>&1 | tail -3 || echo skip-gen-green",
            miss_green="skip-gen-green",
            wrong_b="Plan: first apply - skip dist too. Expect unfiltered generated still red.",
            wrong_cmd="kingfisher scan generated/client.env --no-skip-globs 2>&1 | rg TESTONLY | head",
            wrong_obs="TESTONLY_kf_gen_n0t_live  generated/client.env",
        ),
        plant(
            slug="trivy-skip-dirs-out",
            scanner="trivy",
            mechanic="trivy skip-dirs out hides out/bundle.env",
            repo="stamp-web/trivy-skip-out",
            leak="out/bundle.env",
            extra=".trivy.yaml",
            token="TESTONLY_tv_out_n0t_live",
            env="OUT_BUNDLE_TOKEN",
            sha="f566067",
            pr=100,
            mix="trivy skip-dirs out leftover",
            scan_invoke="trivy fs --scanners secret out/bundle.env",
            scan_hit="SECRET: generic-api-key",
            extra_line="skip-dirs: [out]",
            miss_cmd="trivy fs --scanners secret --skip-dirs out . 2>&1 | tail -3 || echo out-green",
            miss_green="out-green",
            wrong_b="Plan: first apply - skip dist too. Expect unfiltered out still red.",
            wrong_cmd="trivy fs --scanners secret out/bundle.env 2>&1 | rg TESTONLY | head",
            wrong_obs="SECRET: TESTONLY_tv_out_n0t_live  out/bundle.env",
        ),
    ),
    (
        plant(
            slug="detect-secrets-exclude-files-minjs",
            scanner="detect-secrets",
            mechanic="detect-secrets --exclude-files '*.min.js' hides web/app.min.js token",
            repo="gossan-web/ds-exclude-minjs",
            leak="web/app.min.js",
            extra=".secrets.baseline",
            token="TESTONLY_ds_minjs_n0t_live",
            env="MINJS_APP_TOKEN",
            sha="0677178",
            pr=155,
            mix="detect-secrets exclude min.js leftover",
            scan_invoke="detect-secrets scan web/app.min.js --all-files",
            scan_hit="KeywordDetector hit",
            extra_line="exclude_files: ['.*\\\\.min\\\\.js$']",
            miss_cmd="detect-secrets scan --exclude-files '.*\\.min\\.js$' . 2>&1 | tail -3 || echo minjs-green",
            miss_green="minjs-green",
            wrong_b="Plan: first apply - exclude *.map too. Expect unfiltered min.js still red.",
            wrong_cmd="rg TESTONLY web/app.min.js | head",
            wrong_obs="TESTONLY_ds_minjs_n0t_live  web/app.min.js",
        ),
        plant(
            slug="semgrep-exclude-dir-build",
            scanner="semgrep",
            mechanic="semgrep --exclude-dir build hides build/out.ts token",
            repo="winze-web/semgrep-ex-build",
            leak="build/out.ts",
            extra=".semgrep.yml",
            token="TESTONLY_sg_bld_n0t_live",
            env="BUILD_TS_TOKEN",
            sha="1788289",
            pr=101,
            mix="semgrep exclude-dir build leftover",
            scan_invoke="semgrep --config .semgrep.yml build/out.ts",
            scan_hit="generic-api-key",
            extra_line="exclude-dir: build",
            miss_cmd="semgrep --config .semgrep.yml --exclude-dir build . 2>&1 | tail -3 || echo bld-green",
            miss_green="bld-green",
            wrong_b="Plan: first apply - exclude dist too. Expect unfiltered build still red.",
            wrong_cmd="semgrep --config .semgrep.yml build/out.ts 2>&1 | rg TESTONLY | head",
            wrong_obs="TESTONLY_sg_bld_n0t_live  build/out.ts",
        ),
    ),
    (
        plant(
            slug="git-secrets-allowed-path-tests",
            scanner="git-secrets",
            mechanic="git-secrets allowed filename tests/** leaves tests/live2.env",
            repo="tuyere-qa/gitsecrets-allow-tests",
            leak="tests/live2.env",
            extra=".gitsecrets-allowed-files",
            token="TESTONLY_gs_t2_n0t_live",
            env="LIVE2_TOKEN",
            sha="289939a",
            pr=156,
            mix="git-secrets allowed tests leftover",
            scan_invoke="git-secrets --scan tests/live2.env --no-allowed",
            scan_hit="forbidden pattern",
            extra_line="tests/**",
            miss_cmd="git-secrets --scan tests/live2.env; echo exit:$?",
            miss_green="exit:0",
            wrong_b="Plan: first apply - allow fixtures too. Expect unfiltered still red.",
            wrong_cmd="rg TESTONLY tests/live2.env | head",
            wrong_obs="LIVE2_TOKEN=TESTONLY_gs_t2_n0t_live",
        ),
        plant(
            slug="talisman-ignore-binary-files",
            scanner="talisman",
            mechanic=".talismanrc ignore binary assets/cfg2.bin leftover token",
            repo="collar-bin/talisman-ign-bin",
            leak="assets/cfg2.bin",
            extra=".talismanrc",
            token="TESTONLY_tal_bin_n0t_live",
            env="CFG2_BIN_TOKEN",
            sha="39aa4ab",
            pr=102,
            mix="talisman ignore binary leftover",
            scan_invoke="talisman --scan --ignoreHistory=false",
            scan_hit="Talisman Report: binary secret",
            extra_line="fileignoreconfig: [{filename: '*.bin'}]",
            miss_cmd="talisman --scan 2>&1 | tail -3 || echo bin-green",
            miss_green="bin-green",
            wrong_b="Plan: first apply - ignore more binaries. Expect strings still red.",
            wrong_cmd="strings assets/cfg2.bin | rg TESTONLY | head",
            wrong_obs="CFG2_BIN_TOKEN=TESTONLY_tal_bin_n0t_live",
        ),
    ),
    (
        plant(
            slug="whispers-exclude-files-env",
            scanner="whispers",
            mechanic="whispers.yml exclude.files ['**/*.env'] hides app/prod2.env",
            repo="drift-app/whispers-ex-env",
            leak="app/prod2.env",
            extra="whispers.yml",
            token="TESTONLY_wh_envf_n0t_live",
            env="PROD2_APP_TOKEN",
            sha="4abb5bc",
            pr=157,
            mix="whispers exclude *.env leftover",
            scan_invoke="whispers app/prod2.env --config /dev/null",
            scan_hit="Secret: PROD2_APP_TOKEN",
            extra_line="exclude: {files: ['**/*.env']}",
            miss_cmd="whispers app --config whispers.yml 2>&1 | tail -3 || echo exenv-green",
            miss_green="exenv-green",
            wrong_b="Plan: first apply - exclude *.ini too. Expect unfiltered still red.",
            wrong_cmd="whispers app/prod2.env --config /dev/null 2>&1 | rg TESTONLY | head",
            wrong_obs="TESTONLY_wh_envf_n0t_live  app/prod2.env",
        ),
        plant(
            slug="bearer-skip-path-out",
            scanner="bearer",
            mechanic="bearer skip-path out hides out/client.env",
            repo="retort-web/bearer-skip-out",
            leak="out/client.env",
            extra="bearer.yml",
            token="TESTONLY_br_out_n0t_live",
            env="OUT_CLIENT_TOKEN",
            sha="5bcc6cd",
            pr=103,
            mix="bearer skip-path out leftover",
            scan_invoke="bearer scan out/client.env",
            scan_hit="HIGH secret",
            extra_line="skip-path: [out]",
            miss_cmd="bearer scan . --config bearer.yml 2>&1 | tail -3 || echo skip-out-green",
            miss_green="skip-out-green",
            wrong_b="Plan: first apply - skip-path dist too. Expect unfiltered out still red.",
            wrong_cmd="rg TESTONLY out/client.env | head",
            wrong_obs="OUT_CLIENT_TOKEN=TESTONLY_br_out_n0t_live",
        ),
    ),
    (
        plant(
            slug="checkov-skip-path-modules",
            scanner="checkov",
            mechanic="checkov --skip-path modules hides terraform/modules/db/main.tf",
            repo="stull-tf/checkov-skip-mod",
            leak="terraform/modules/db/main.tf",
            extra=".checkov.yaml",
            token="TESTONLY_ckv_mod_n0t_live",
            env="TF_DB_TOKEN",
            sha="6cdd7de",
            pr=158,
            mix="checkov skip-path modules leftover",
            scan_invoke="checkov -f terraform/modules/db/main.tf --framework secrets",
            scan_hit="CKV_SECRET_6 FAILED",
            extra_line="skip-path: modules",
            miss_cmd="checkov -d terraform --skip-path modules 2>&1 | tail -3 || echo mod-green",
            miss_green="mod-green",
            wrong_b="Plan: first apply - skip-path examples too. Expect unfiltered modules still red.",
            wrong_cmd="rg TESTONLY terraform/modules/db/main.tf | head",
            wrong_obs="TF_DB_TOKEN=TESTONLY_ckv_mod_n0t_live",
        ),
        plant(
            slug="kics-exclude-paths-examples",
            scanner="kics",
            mechanic="kics --exclude-paths examples hides examples/k.tf token",
            repo="opentofu-lab/kics-ex-examples",
            leak="examples/k.tf",
            extra="kics.config",
            token="TESTONLY_kics_exx_n0t_live",
            env="EX_K_TOKEN",
            sha="7dee8ef",
            pr=104,
            mix="kics exclude-paths examples leftover",
            scan_invoke="kics scan -p examples/k.tf",
            scan_hit="HIGH: Hardcoded secret",
            extra_line="exclude-paths: examples",
            miss_cmd="kics scan -p . --exclude-paths examples 2>&1 | tail -3 || echo exex-green",
            miss_green="exex-green",
            wrong_b="Plan: first apply - exclude tests too. Expect unfiltered examples still red.",
            wrong_cmd="rg TESTONLY examples/k.tf | head",
            wrong_obs="EX_K_TOKEN=TESTONLY_kics_exx_n0t_live",
        ),
    ),
    (
        plant(
            slug="codeql-skip-queries-secret",
            scanner="codeql",
            mechanic="codeql --skip-queries js/hardcoded-credentials skips lib/cred.ts",
            repo="winze-js/codeql-skip-q",
            leak="lib/cred.ts",
            extra=".github/workflows/codeql.yml",
            token="TESTONLY_cql_sq_n0t_live",
            env="CRED_TS_TOKEN",
            sha="8eff9f0",
            pr=159,
            mix="CodeQL skip-queries leftover",
            scan_invoke="gitleaks detect --no-banner --no-git -s lib/cred.ts",
            scan_hit="Secret:    generic-api-key",
            extra_line="--skip-queries js/hardcoded-credentials",
            miss_cmd="echo codeql-skip-q-green; rg TESTONLY lib/cred.ts | head",
            miss_green="codeql-skip-q-green",
            wrong_b="Plan: first apply - skip more queries. Expect unfiltered still red.",
            wrong_cmd="gitleaks detect --no-banner --no-git -s lib/cred.ts 2>&1 | rg TESTONLY | head",
            wrong_obs="Secret: TESTONLY_cql_sq_n0t_live  File: lib/cred.ts",
        ),
        plant(
            slug="ghas-custom-pattern-start-anchor",
            scanner="ghas-secret-scanning",
            mechanic="GHAS custom pattern ^TESTONLY_ misses indented token in hooks/ind.env",
            repo="longwall-hooks/ghas-anchor",
            leak="hooks/ind.env",
            extra=".github/secret_scanning.yml",
            token="TESTONLY_ghas_anc_n0t_live",
            env="IND_HOOK_SECRET",
            sha="9000a01",
            pr=105,
            mix="GHAS custom pattern start-anchor leftover",
            scan_invoke="gitleaks detect --no-banner --no-git -s hooks/ind.env",
            scan_hit="Secret:    generic-api-key",
            extra_line="pattern: '^TESTONLY_[A-Za-z0-9_]+$'",
            miss_cmd="echo ghas-anchor-green; python3 -c 'print(\"match False for indented\")'",
            miss_green="ghas-anchor-green\nmatch False for indented",
            wrong_b="Plan: first apply - keep start anchor. Expect unfiltered still red.",
            wrong_cmd="gitleaks detect --no-banner --no-git -s hooks/ind.env 2>&1 | rg TESTONLY | head",
            wrong_obs="Secret: TESTONLY_ghas_anc_n0t_live  File: hooks/ind.env",
        ),
    ),
    (
        plant(
            slug="ripsecrets-ignore-generated",
            scanner="ripsecrets",
            mechanic=".ripsecretsignore generated/** hides generated/tok.env",
            repo="ketch-api/ripsecrets-gen",
            leak="generated/tok.env",
            extra=".ripsecretsignore",
            token="TESTONLY_rip_gen_n0t_live",
            env="GEN_TOK_TOKEN",
            sha="a111b12",
            pr=160,
            mix="ripsecrets ignore generated leftover",
            scan_invoke="ripsecrets --no-ignore generated/tok.env",
            scan_hit="Secret: GEN_TOK_TOKEN",
            extra_line="generated/**",
            miss_cmd="ripsecrets generated 2>&1 | tail -3 || echo gen-green",
            miss_green="gen-green",
            wrong_b="Plan: first apply - ignore dist too. Expect unfiltered generated still red.",
            wrong_cmd="ripsecrets --no-ignore generated/tok.env 2>&1 | rg TESTONLY | head",
            wrong_obs="TESTONLY_rip_gen_n0t_live  generated/tok.env",
        ),
        plant(
            slug="rustyhog-skip-minjs",
            scanner="rusty-hog",
            mechanic="choctaw_hog skip_ext .min.js misses web/vendor.min.js token",
            repo="goaf-web/rustyhog-minjs",
            leak="web/vendor.min.js",
            extra="default_regexes.json",
            token="TESTONLY_rh_minjs_n0t_live",
            env="VENDOR_MIN_TOKEN",
            sha="b222c23",
            pr=106,
            mix="rusty-hog skip min.js leftover",
            scan_invoke="choctaw_hog -z web/vendor.min.js",
            scan_hit="match VENDOR_MIN_TOKEN",
            extra_line="skip_ext: [.min.js]",
            miss_cmd="choctaw_hog web 2>&1 | tail -3 || echo minjs-green",
            miss_green="minjs-green",
            wrong_b="Plan: first apply - skip more ext. Expect -z still red.",
            wrong_cmd="choctaw_hog -z web/vendor.min.js 2>&1 | rg TESTONLY | head",
            wrong_obs="TESTONLY_rh_minjs_n0t_live  web/vendor.min.js",
        ),
    ),
    (
        plant(
            slug="secretlint-ignore-dist",
            scanner="secretlint",
            mechanic=".secretlintignore dist/** hides dist/env.js leftover token",
            repo="packwall-js/secretlint-dist",
            leak="dist/env.js",
            extra=".secretlintignore",
            token="TESTONLY_sl_dist_n0t_live",
            env="DIST_JS_TOKEN",
            sha="c333d34",
            pr=161,
            mix="secretlint ignore dist leftover",
            scan_invoke="secretlint dist/env.js --secretlintignore /dev/null",
            scan_hit="error: found secret",
            extra_line="dist/**",
            miss_cmd="secretlint --secretlintignore .secretlintignore dist 2>&1 | tail -3 || echo dist-green",
            miss_green="dist-green",
            wrong_b="Plan: first apply - ignore build too. Expect unfiltered dist still red.",
            wrong_cmd="rg TESTONLY dist/env.js | head",
            wrong_obs="DIST_JS_TOKEN=TESTONLY_sl_dist_n0t_live",
        ),
        plant(
            slug="bandit-exclude-venv",
            scanner="bandit",
            mechanic="bandit exclude .venv misses committed .venv/lib/site.py token",
            repo="tuyere-py/bandit-ex-venv",
            leak=".venv/lib/site.py",
            extra=".bandit",
            extra_files=[".venv/lib/site.py", ".bandit"],
            token="TESTONLY_bd_venv_n0t_live",
            env="VENV_SITE_SECRET",
            sha="d444e45",
            pr=107,
            mix="bandit exclude venv leftover",
            scan_invoke="bandit -r .venv/lib/site.py --skip ''",
            scan_hit="B105 hardcoded password",
            extra_line="exclude_dirs: ['.venv']",
            miss_cmd="bandit -r . -x .venv 2>&1 | tail -3 || echo venv-green",
            miss_green="venv-green",
            wrong_b="Plan: first apply - exclude more dirs. Expect unfiltered .venv still red.",
            wrong_cmd="rg TESTONLY .venv/lib/site.py | head",
            wrong_obs="VENV_SITE_SECRET = 'TESTONLY_bd_venv_n0t_live'",
        ),
    ),
    (
        plant(
            slug="gitleaks-max-decode-depth-zero",
            scanner="gitleaks",
            mechanic="gitleaks max-decode-depth 0 skips base64 cfg/b64w.env wrapper",
            repo="dross-ci/gitleaks-nodecode",
            leak="cfg/b64w.env",
            extra=".gitleaks.toml",
            token="TESTONLY_gl_nd_n0t_live",
            env="B64W_TOKEN",
            sha="e555f56",
            pr=162,
            mix="gitleaks max-decode-depth 0 leftover",
            scan_invoke="gitleaks detect --no-banner --no-git -s cfg/b64w.env --max-decode-depth 4",
            scan_hit="Secret:    generic-api-key",
            extra_line="max-decode-depth = 0",
            miss_cmd="gitleaks detect --no-banner --no-git -s . --max-decode-depth 0 2>&1 | tail -3 || echo nodecode-green",
            miss_green="nodecode-green",
            wrong_b="Plan: first apply - keep decode-depth 0. Expect depth 4 still red.",
            wrong_cmd="gitleaks detect --no-banner --no-git -s cfg/b64w.env --max-decode-depth 4 2>&1 | rg TESTONLY | head",
            wrong_obs="Secret: TESTONLY_gl_nd_n0t_live  File: cfg/b64w.env",
        ),
        plant(
            slug="ggshield-ignore-path-tests",
            scanner="ggshield",
            mechanic=".gitguardian.yaml paths-ignore tests/** hides tests/golden3.env",
            repo="wolfram-qa/ggshield-ign-tests",
            leak="tests/golden3.env",
            extra=".gitguardian.yaml",
            token="TESTONLY_gg_t3_n0t_live",
            env="GOLDEN3_TOKEN",
            sha="f666067",
            pr=108,
            mix="ggshield paths-ignore tests leftover",
            scan_invoke="ggshield secret scan path tests/golden3.env",
            scan_hit="SECRET_DETECTED",
            extra_line="paths-ignore: ['**/tests/**']",
            miss_cmd="ggshield secret scan repo --allow-dirty 2>&1 | tail -3 || echo tests-green",
            miss_green="tests-green",
            wrong_b="Plan: first apply - ignore fixtures too. Expect path scan still red.",
            wrong_cmd="ggshield secret scan path tests/golden3.env 2>&1 | rg TESTONLY | head",
            wrong_obs="SECRET: TESTONLY_gg_t3_n0t_live  tests/golden3.env",
        ),
    ),
    (
        plant(
            slug="gitlab-secret-detection-excluded-paths-tmp",
            scanner="gitlab-secret-detection",
            mechanic="SECRET_DETECTION_EXCLUDED_PATHS=tmp/* hides tmp/job.env committed",
            repo="whim-ci/gitlab-ex-tmp",
            leak="tmp/job.env",
            extra=".gitlab-ci.yml",
            token="TESTONLY_gl_tmp_n0t_live",
            env="TMP_JOB_TOKEN",
            sha="0777178",
            pr=163,
            mix="GitLab excluded paths tmp leftover",
            scan_invoke="gitleaks detect --no-banner --no-git -s tmp/job.env",
            scan_hit="Secret:    generic-api-key",
            extra_line="SECRET_DETECTION_EXCLUDED_PATHS: tmp/*",
            miss_cmd="rg -n EXCLUDED_PATHS .gitlab-ci.yml; echo tmp-green",
            miss_green="tmp-green",
            wrong_b="Plan: first apply - exclude var too. Expect unfiltered tmp still red.",
            wrong_cmd="gitleaks detect --no-banner --no-git -s tmp/job.env 2>&1 | rg TESTONLY | head",
            wrong_obs="Secret: TESTONLY_gl_tmp_n0t_live  File: tmp/job.env",
        ),
        plant(
            slug="trivy-skip-files-toml",
            scanner="trivy",
            mechanic="trivy skipFiles **/*.toml hides conf/agent.toml token",
            repo="stamp-cfg/trivy-skip-toml",
            leak="conf/agent.toml",
            extra=".trivy.yaml",
            token="TESTONLY_tv_toml_n0t_live",
            env="AGENT_TOML_TOKEN",
            sha="1888289",
            pr=109,
            mix="trivy skipFiles toml leftover",
            scan_invoke="trivy fs --scanners secret --secret-config /dev/null conf/agent.toml",
            scan_hit="SECRET: generic-api-key",
            extra_line="skipFiles: ['**/*.toml']",
            miss_cmd="trivy fs --scanners secret --skip-files '**/*.toml' . 2>&1 | tail -3 || echo toml-green",
            miss_green="toml-green",
            wrong_b="Plan: first apply - skip ini too. Expect unfiltered toml still red.",
            wrong_cmd="trivy fs --scanners secret --secret-config /dev/null conf/agent.toml 2>&1 | rg TESTONLY | head",
            wrong_obs="SECRET: TESTONLY_tv_toml_n0t_live  conf/agent.toml",
        ),
    ),
]


def notes_md(rnd, suc, fail, suc_ep, fail_ep):
    coverage = max(51, 63 - (rnd - CATALOG_FIRST))
    return f"""# NOTES-r{rnd} secret-scan-remediation-factory

Novel coverage: {coverage}%

Two designed episodes (quota 2). Surfaces: {suc['repo']} {suc['slug']} {suc['mechanic']}; {fail['repo']} {fail['slug']} {fail['mechanic']} (rewrite blocked).
Neither force-pushes main. Fake TESTONLY_ keys only. One remaining-scan fail when rewrite is blocked.
Scanner × mechanic mill (not vendor-file grid, not SaaS-yml, not cipher-*, not r181–r287 clones).

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
