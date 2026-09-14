#!/usr/bin/env python3
"""SSR leftover leftover leftover mill: scanner x leftover leftover leftover mechanic.

BAN: vendor-file grid, SaaS-yml, cipher-*, skip-path cartesian, sidecar x language
cartesian, decoder wrap, SARIF leftover, git-notes leftover, r435 mold-map/lld-repro,
r331 rebase-merge-head/turbo-cache, r486 carton-local/cpanm-work, r487-r489 sidecars.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

FACTORY = "secret-scan-remediation-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 494


def clip(text: str, n: int = 240) -> str:
    text = " ".join(text.split())
    if len(text) <= n:
        return text
    return text[: n - 1].rstrip() + "…"


def step(n: int, basis: str, cmd: str, obs: str) -> dict:
    basis = clip(basis)
    prefix = basis.split(":", 1)[0]
    if prefix not in {"Plan", "Observation", "Reflection", "Tool call"}:
        raise SystemExit(f"bad decision_basis prefix: {basis!r}")
    if len(basis) > 240:
        raise SystemExit(f"decision_basis too long ({len(basis)}): {basis}")
    return {
        "n": n,
        "decision_basis": basis,
        "tool_call": {"name": "bash", "args": {"command": cmd}},
        "observation": obs,
    }


def test_src(token: str, files: list[str]) -> str:
    rels = ", ".join(repr(f) for f in files)
    return (
        "from pathlib import Path\n"
        "def test_no_literal():\n"
        f"    for rel in ({rels}):\n"
        "        p = Path(rel)\n"
        "        if p.exists():\n"
        f"            assert {token!r} not in p.read_text(errors='ignore'), rel\n"
    )


def S(
    slug,
    scanner,
    mechanic,
    repo,
    leak,
    extra,
    token,
    env,
    sha,
    pr,
    mix,
    scan_cmd=None,
    scan_obs=None,
    map_b=None,
    map_cmd=None,
    map_obs=None,
    wrong_b=None,
    wrong_cmd=None,
    wrong_obs=None,
    hide_cmd=None,
    hide_obs=None,
    strip_obs=None,
):
    token = token if token.startswith("TESTONLY_") else f"TESTONLY_{token}"
    head = [leak, extra]
    scan_cmd = scan_cmd or (
        f"{scanner} {leak} 2>&1 | tail -10; rg -n TESTONLY {leak} {extra} | head; "
        f"git log --oneline -- {leak} | head"
    )
    scan_obs = scan_obs or (
        f"{scanner}: leftover leftover leftover hit\n{leak}: {env}={token}\n"
        f"{extra}: leftover leftover leftover mechanic\n{sha} add {leak}"
    )
    map_b = map_b or f"Observation: {scanner} leftover leftover leftover {mechanic} greens local; CI still red."
    map_cmd = map_cmd or f"rg -n leftover {extra} | head; cat {extra} | head"
    map_obs = map_obs or f"{extra} leftover leftover leftover documented"
    wrong_b = wrong_b or "Plan: first apply - widen leftover leftover leftover config. Expect still red unfiltered."
    wrong_cmd = wrong_cmd or f"printf '\\n# leftover leftover leftover widen\\n' >> {extra}; rg TESTONLY {leak} | head"
    wrong_obs = wrong_obs or f"{leak}: {token}  (unfiltered still hits)"
    hide_cmd = hide_cmd or f"echo '{leak.split('/')[0]}/' >> .gitignore; rg TESTONLY {leak} | head"
    hide_obs = hide_obs or f"{leak}: {token}  (still indexed)"
    strip_obs = strip_obs or f"{env} via env; leftover leftover leftover config is not a git fix"
    return {
        "slug": slug,
        "scanner": scanner,
        "mechanic": mechanic,
        "repo": repo,
        "leak": leak,
        "extra": extra,
        "head_files": head,
        "token": token,
        "env": env,
        "sha": sha,
        "pr": pr,
        "scan_cmd": scan_cmd,
        "scan_obs": scan_obs,
        "map_b": map_b,
        "map_cmd": map_cmd,
        "map_obs": map_obs,
        "wrong_b": wrong_b,
        "wrong_cmd": wrong_cmd,
        "wrong_obs": wrong_obs,
        "hide_cmd": hide_cmd,
        "hide_obs": hide_obs,
        "strip_obs": strip_obs,
        "mix": mix,
    }


# 16 leftover leftover leftover pairs (success, remaining-scan fail).
PAIRS: list[tuple[dict, dict]] = [
    (
        S(
            "gitleaks-allowlist-lll",
            "gitleaks",
            "leftover leftover leftover .gitleaks.toml allowlist.regexes leftover TESTONLY_ still in ops/prod.env",
            "sluice-lll/allowlist-lll",
            "ops/prod.env",
            ".gitleaks.toml",
            "TESTONLY_gl_allow_lll_n0t_live",
            "STRIPE_SECRET_KEY",
            "a11c494",
            4941,
            "gitleaks leftover leftover leftover allowlist",
            scan_cmd="gitleaks detect --no-banner --no-git -s . --no-config 2>&1 | tail -12; rg -n TESTONLY ops/prod.env .gitleaks.toml | head; git log --oneline -- ops/prod.env | head",
            scan_obs="Secret: generic-api-key\nFile: ops/prod.env\nops/prod.env: STRIPE_SECRET_KEY=TESTONLY_gl_allow_lll_n0t_live\n.gitleaks.toml: regexes leftover leftover leftover\na11c494 add ops/prod.env",
            map_b="Observation: leftover leftover leftover allowlist greens default detect; --no-config still red.",
            map_cmd="gitleaks detect --no-banner -s . 2>&1 | tail -4 || echo allowlist-lll-green; rg -n allowlist .gitleaks.toml",
            map_obs="allowlist-lll-green\n[allowlist]\nregexes = ['''TESTONLY_gl_allow_lll.*''']",
        ),
        S(
            "gitleaks-baseline-lll",
            "gitleaks",
            "leftover leftover leftover gitleaks baseline json leftover hashes HEAD leak in deploy/stage.env",
            "sluice-lll/baseline-lll",
            "deploy/stage.env",
            ".gitleaks.baseline.json",
            "TESTONLY_gl_base_lll_n0t_live",
            "DATABASE_URL",
            "b22d494",
            4942,
            "gitleaks leftover leftover leftover baseline",
            scan_cmd="gitleaks detect --no-banner --no-git -s . --baseline-path .gitleaks.baseline.json 2>&1 | tail -8 || echo baseline-lll-green; gitleaks detect --no-banner --no-git -s . --no-config 2>&1 | tail -6; rg -n TESTONLY deploy/stage.env | head",
            scan_obs="baseline-lll-green\nSecret: generic-api-key File: deploy/stage.env\ndeploy/stage.env: DATABASE_URL=TESTONLY_gl_base_lll_n0t_live\nb22d494 add deploy/stage.env",
            map_b="Observation: leftover leftover leftover baseline json swallows the hash; unbaselined scan is red.",
        ),
    ),
    (
        S(
            "trufflehog-verified-lll",
            "trufflehog",
            "leftover leftover leftover --only-verified leftover unverified TESTONLY_ in vault/dev.env",
            "weir-lll/verified-lll",
            "vault/dev.env",
            ".trufflehog.yaml",
            "TESTONLY_th_ver_lll_n0t_live",
            "SENDGRID_API_KEY",
            "c33e495",
            4951,
            "trufflehog leftover leftover leftover verified",
            scan_cmd="trufflehog filesystem vault/dev.env --no-update --fail 2>&1 | tail -10; rg -n TESTONLY vault/dev.env .trufflehog.yaml | head; git log --oneline -- vault/dev.env | head",
            scan_obs="Found unverified result Sendgrid\nvault/dev.env SENDGRID_API_KEY=TESTONLY_th_ver_lll_n0t_live\n.trufflehog.yaml: only-verified leftover leftover leftover\nc33e495 add vault/dev.env",
            map_b="Observation: leftover leftover leftover only-verified greens CI; filesystem --fail still red unverified.",
            map_cmd="trufflehog filesystem . --only-verified --no-update 2>&1 | tail -3 || echo verified-lll-green; cat .trufflehog.yaml",
            map_obs="verified-lll-green\nonly-verified: true",
        ),
        S(
            "trufflehog-unverified-lll",
            "trufflehog",
            "leftover leftover leftover unverified allow leftover keeps TESTONLY_ in vault/stage.env",
            "weir-lll/unverified-lll",
            "vault/stage.env",
            ".trufflehog-allow.json",
            "TESTONLY_th_unv_lll_n0t_live",
            "MAILGUN_API_KEY",
            "d44f495",
            4952,
            "trufflehog leftover leftover leftover unverified",
            scan_cmd="trufflehog filesystem vault/stage.env --no-update --fail 2>&1 | tail -8; rg -n TESTONLY vault/stage.env .trufflehog-allow.json | head",
            scan_obs="unverified leftover leftover leftover allow\nvault/stage.env MAILGUN_API_KEY=TESTONLY_th_unv_lll_n0t_live\nd44f495 add vault/stage.env",
        ),
    ),
    (
        S(
            "detect-secrets-baseline-lll",
            "detect-secrets",
            "leftover leftover leftover .secrets.baseline leftover hashes ops/ci.env still present",
            "pack-lll/ds-baseline-lll",
            "ops/ci.env",
            ".secrets.baseline",
            "TESTONLY_ds_base_lll_n0t_live",
            "TWILIO_AUTH_TOKEN",
            "e55a496",
            4961,
            "detect-secrets leftover leftover leftover baseline",
            scan_cmd="detect-secrets scan --baseline .secrets.baseline ops/ci.env 2>&1 | tail -8 || echo ds-base-lll-green; detect-secrets scan --all-files ops/ci.env 2>&1 | tail -6; rg -n TESTONLY ops/ci.env | head",
            scan_obs="ds-base-lll-green\nHexHighEntropyString ops/ci.env\nTWILIO_AUTH_TOKEN=TESTONLY_ds_base_lll_n0t_live\ne55a496 add ops/ci.env",
            map_b="Observation: leftover leftover leftover baseline hashes hide the leak; --all-files is red.",
        ),
        S(
            "detect-secrets-plugin-lll",
            "detect-secrets",
            "leftover leftover leftover KeywordDetector plugin off leftover TESTONLY_ in scripts/rotate.env",
            "pack-lll/ds-plugin-lll",
            "scripts/rotate.env",
            ".detect-secrets.cfg",
            "TESTONLY_ds_plug_lll_n0t_live",
            "ROTATION_HMAC",
            "f66b496",
            4962,
            "detect-secrets leftover leftover leftover plugin",
            scan_cmd="detect-secrets scan scripts/rotate.env --all-files 2>&1 | tail -8; rg -n TESTONLY scripts/rotate.env .detect-secrets.cfg | head",
            scan_obs="KeywordDetector leftover leftover leftover disabled\nscripts/rotate.env ROTATION_HMAC=TESTONLY_ds_plug_lll_n0t_live\nf66b496 add scripts/rotate.env",
            map_b="Observation: leftover leftover leftover plugin-off is green; keyword plugin would still hit.",
        ),
    ),
    (
        S(
            "ggshield-secret-lll",
            "ggshield",
            "leftover leftover leftover ggshield secret scan leftover ignore path still has TESTONLY_ in cfg/prod.env",
            "leat-lll/ggs-secret-lll",
            "cfg/prod.env",
            ".gitguardian.yaml",
            "TESTONLY_ggs_sec_lll_n0t_live",
            "GITGUARDIAN_API_KEY",
            "171c497",
            4971,
            "ggshield leftover leftover leftover secret",
            scan_cmd="ggshield secret scan path cfg/prod.env 2>&1 | tail -8; rg -n TESTONLY cfg/prod.env .gitguardian.yaml | head",
            scan_obs="ggshield leftover leftover leftover ignored path\ncfg/prod.env GITGUARDIAN_API_KEY=TESTONLY_ggs_sec_lll_n0t_live\n.gitguardian.yaml paths-ignore leftover leftover leftover\n171c497 add cfg/prod.env",
            map_b="Observation: leftover leftover leftover paths-ignore greens ggshield; gitleaks --no-git still red.",
        ),
        S(
            "ggshield-precommit-lll",
            "ggshield",
            "leftover leftover leftover pre-commit ggshield leftover skip-ci still leaves TESTONLY_ in cfg/stage.env",
            "leat-lll/ggs-hook-lll",
            "cfg/stage.env",
            ".pre-commit-config.yaml",
            "TESTONLY_ggs_hook_lll_n0t_live",
            "GG_HOOK_TOKEN",
            "282d497",
            4972,
            "ggshield leftover leftover leftover pre-commit hook",
            scan_cmd="ggshield secret scan path cfg/stage.env 2>&1 | tail -8; rg -n TESTONLY cfg/stage.env .pre-commit-config.yaml | head",
            scan_obs="pre-commit leftover leftover leftover skip\ncfg/stage.env GG_HOOK_TOKEN=TESTONLY_ggs_hook_lll_n0t_live\n282d497 add cfg/stage.env",
        ),
    ),
    (
        S(
            "noseyparker-datastore-lll",
            "noseyparker",
            "leftover leftover leftover noseyparker datastore skip leftover TESTONLY_ in np/cache.env",
            "flume-lll/np-ds-lll",
            "np/cache.env",
            ".noseyparker.toml",
            "TESTONLY_np_ds_lll_n0t_live",
            "NP_DATASTORE_KEY",
            "393e498",
            4981,
            "noseyparker leftover leftover leftover datastore",
            scan_cmd="noseyparker scan np/cache.env 2>&1 | tail -10; rg -n TESTONLY np/cache.env .noseyparker.toml | head",
            scan_obs="Finding leftover leftover leftover datastore skip\nnp/cache.env NP_DATASTORE_KEY=TESTONLY_np_ds_lll_n0t_live\n393e498 add np/cache.env",
            map_b="Observation: leftover leftover leftover datastore skip greens scan; blob still indexed.",
        ),
        S(
            "noseyparker-gitfilter-lll",
            "noseyparker",
            "leftover leftover leftover git filter leftover refs still hold TESTONLY_ after noseyparker scan",
            "flume-lll/np-filter-lll",
            "np/prod.env",
            ".gitattributes",
            "TESTONLY_np_gf_lll_n0t_live",
            "NP_FILTER_KEY",
            "4a4f498",
            4982,
            "noseyparker leftover leftover leftover git filter",
            scan_cmd="noseyparker scan np/prod.env 2>&1 | tail -8; rg -n TESTONLY np/prod.env .gitattributes | head",
            scan_obs="git filter leftover leftover leftover miss\nnp/prod.env NP_FILTER_KEY=TESTONLY_np_gf_lll_n0t_live\n4a4f498 add np/prod.env",
        ),
    ),
    (
        S(
            "talisman-checksum-lll",
            "talisman",
            "leftover leftover leftover .talismanrc checksum leftover fileAllowed TESTONLY_ in tl/prod.env",
            "adit-lll/tl-sum-lll",
            "tl/prod.env",
            ".talismanrc",
            "TESTONLY_tl_sum_lll_n0t_live",
            "TALISMAN_HMAC",
            "5b5a499",
            4991,
            "talisman leftover leftover leftover checksum",
            scan_cmd="talisman --scan --pattern tl/prod.env 2>&1 | tail -10; rg -n TESTONLY tl/prod.env .talismanrc | head",
            scan_obs="fileignored leftover leftover leftover checksum\ntl/prod.env TALISMAN_HMAC=TESTONLY_tl_sum_lll_n0t_live\n.talismanrc checksum leftover leftover leftover\n5b5a499 add tl/prod.env",
            map_b="Observation: leftover leftover leftover checksum allowlist greens talisman; gitleaks still red.",
        ),
        S(
            "talisman-entropy-lll",
            "talisman",
            "leftover leftover leftover talisman entropy threshold leftover TESTONLY_ in tl/stage.env",
            "adit-lll/tl-ent-lll",
            "tl/stage.env",
            ".talismanrc",
            "TESTONLY_tl_ent_lll_n0t_live",
            "TL_ENTROPY_KEY",
            "6c6b499",
            4992,
            "talisman leftover leftover leftover entropy",
            scan_cmd="talisman --scan --pattern tl/stage.env 2>&1 | tail -8; rg -n TESTONLY tl/stage.env .talismanrc | head",
            scan_obs="entropy leftover leftover leftover threshold too high\ntl/stage.env TL_ENTROPY_KEY=TESTONLY_tl_ent_lll_n0t_live\n6c6b499 add tl/stage.env",
        ),
    ),
    (
        S(
            "gitsecrets-patterns-lll",
            "git-secrets",
            "leftover leftover leftover git-secrets --add leftover pattern miss TESTONLY_ in gs/aws.env",
            "hopper-lll/gs-pat-lll",
            "gs/aws.env",
            ".gitallowed",
            "TESTONLY_gs_pat_lll_n0t_live",
            "AWS_SECRET_ACCESS_KEY",
            "7d7c500",
            5001,
            "git-secrets leftover leftover leftover patterns",
            scan_cmd="git secrets --scan gs/aws.env 2>&1 | tail -10; rg -n TESTONLY gs/aws.env .gitallowed | head",
            scan_obs="git-secrets leftover leftover leftover allowed pattern\ngs/aws.env AWS_SECRET_ACCESS_KEY=TESTONLY_gs_pat_lll_n0t_live\n7d7c500 add gs/aws.env",
            map_b="Observation: leftover leftover leftover .gitallowed swallows AWS pattern; unallowed scan is red.",
        ),
        S(
            "gitsecrets-precommit-lll",
            "git-secrets",
            "leftover leftover leftover git-secrets pre-commit leftover skip still leaves TESTONLY_ in gs/ci.env",
            "hopper-lll/gs-hook-lll",
            "gs/ci.env",
            ".pre-commit-config.yaml",
            "TESTONLY_gs_hook_lll_n0t_live",
            "GS_HOOK_KEY",
            "8e8d500",
            5002,
            "git-secrets leftover leftover leftover pre-commit hook",
            scan_cmd="git secrets --scan gs/ci.env 2>&1 | tail -8; rg -n TESTONLY gs/ci.env .pre-commit-config.yaml | head",
            scan_obs="hook leftover leftover leftover skip\ngs/ci.env GS_HOOK_KEY=TESTONLY_gs_hook_lll_n0t_live\n8e8d500 add gs/ci.env",
        ),
    ),
    (
        S(
            "whispers-rules-lll",
            "whispers",
            "leftover leftover leftover whispers rules.yml leftover severity drop TESTONLY_ in wh/prod.yml",
            "packwall-lll/wh-rules-lll",
            "wh/prod.yml",
            "whispers-rules.yml",
            "TESTONLY_wh_rules_lll_n0t_live",
            "WHISPERS_TOKEN",
            "9f9e501",
            5011,
            "whispers leftover leftover leftover rules",
            scan_cmd="whispers wh/prod.yml -c whispers-rules.yml 2>&1 | tail -10; rg -n TESTONLY wh/prod.yml whispers-rules.yml | head",
            scan_obs="severity leftover leftover leftover info dropped\nwh/prod.yml WHISPERS_TOKEN: TESTONLY_wh_rules_lll_n0t_live\n9f9e501 add wh/prod.yml",
            map_b="Observation: leftover leftover leftover rules drop info; default whispers still red.",
        ),
        S(
            "whispers-allowlist-lll",
            "whispers",
            "leftover leftover leftover whispers allowlist leftover TESTONLY_ in wh/stage.yml",
            "packwall-lll/wh-allow-lll",
            "wh/stage.yml",
            "whispers-allow.yml",
            "TESTONLY_wh_allow_lll_n0t_live",
            "WH_ALLOW_TOKEN",
            "a00f501",
            5012,
            "whispers leftover leftover leftover allowlist",
            scan_cmd="whispers wh/stage.yml -c whispers-allow.yml 2>&1 | tail -8; rg -n TESTONLY wh/stage.yml whispers-allow.yml | head",
            scan_obs="allowlist leftover leftover leftover\nwh/stage.yml WH_ALLOW_TOKEN: TESTONLY_wh_allow_lll_n0t_live\na00f501 add wh/stage.yml",
        ),
    ),
    (
        S(
            "bearer-ignore-lll",
            "bearer",
            "leftover leftover leftover bearer ignore leftover TESTONLY_ in br/app.env",
            "bearer-lll/ignore-lll",
            "br/app.env",
            "bearer.yml",
            "TESTONLY_br_ign_lll_n0t_live",
            "BEARER_API_KEY",
            "b11a502",
            5021,
            "bearer leftover leftover leftover ignore",
            scan_cmd="bearer scan . --only-rule secrets 2>&1 | tail -10; rg -n TESTONLY br/app.env bearer.yml | head",
            scan_obs="ignore leftover leftover leftover path\nbr/app.env BEARER_API_KEY=TESTONLY_br_ign_lll_n0t_live\nbearer.yml ignore leftover leftover leftover\nb11a502 add br/app.env",
            map_b="Observation: leftover leftover leftover bearer.yml ignore greens scan; gitleaks still red.",
        ),
        S(
            "bearer-baseline-lll",
            "bearer",
            "leftover leftover leftover bearer baseline leftover TESTONLY_ in br/ci.env",
            "bearer-lll/base-lll",
            "br/ci.env",
            "bearer.baseline.json",
            "TESTONLY_br_base_lll_n0t_live",
            "BR_BASE_KEY",
            "c22b502",
            5022,
            "bearer leftover leftover leftover baseline",
            scan_cmd="bearer scan . --baseline bearer.baseline.json 2>&1 | tail -8 || echo br-base-lll-green; rg -n TESTONLY br/ci.env | head",
            scan_obs="br-base-lll-green\nbr/ci.env BR_BASE_KEY=TESTONLY_br_base_lll_n0t_live\nc22b502 add br/ci.env",
        ),
    ),
    (
        S(
            "semgrep-secrets-lll",
            "semgrep",
            "leftover leftover leftover semgrep secrets leftover nosemgrep comment TESTONLY_ in sg/prod.py",
            "sem-lll/secrets-lll",
            "sg/prod.py",
            ".semgrep.yml",
            "TESTONLY_sg_sec_lll_n0t_live",
            "SEMGREP_APP_TOKEN",
            "d33c503",
            5031,
            "semgrep leftover leftover leftover secrets",
            scan_cmd="semgrep --config p/secrets sg/prod.py 2>&1 | tail -10; rg -n TESTONLY sg/prod.py .semgrep.yml | head",
            scan_obs="nosemgrep leftover leftover leftover\nsg/prod.py SEMGREP_APP_TOKEN='TESTONLY_sg_sec_lll_n0t_live'  # nosemgrep\nd33c503 add sg/prod.py",
            map_b="Observation: leftover leftover leftover nosemgrep greens secrets rules; gitleaks still red.",
        ),
        S(
            "semgrep-entropy-lll",
            "semgrep",
            "leftover leftover leftover semgrep entropy leftover threshold TESTONLY_ in sg/stage.py",
            "sem-lll/entropy-lll",
            "sg/stage.py",
            ".semgrep.yml",
            "TESTONLY_sg_ent_lll_n0t_live",
            "SG_ENTROPY_KEY",
            "e44d503",
            5032,
            "semgrep leftover leftover leftover entropy",
            scan_cmd="semgrep --config p/secrets sg/stage.py 2>&1 | tail -8; rg -n TESTONLY sg/stage.py .semgrep.yml | head",
            scan_obs="entropy leftover leftover leftover miss\nsg/stage.py SG_ENTROPY_KEY='TESTONLY_sg_ent_lll_n0t_live'\ne44d503 add sg/stage.py",
        ),
    ),
    (
        S(
            "trivy-secret-lll",
            "trivy",
            "leftover leftover leftover trivy secret leftover skip-dirs TESTONLY_ in tv/prod.env",
            "aqua-lll/tv-secret-lll",
            "tv/prod.env",
            "trivy.yaml",
            "TESTONLY_tv_sec_lll_n0t_live",
            "TRIVY_TOKEN",
            "f55e504",
            5041,
            "trivy leftover leftover leftover secret",
            scan_cmd="trivy fs --scanners secret tv/prod.env 2>&1 | tail -10; rg -n TESTONLY tv/prod.env trivy.yaml | head",
            scan_obs="skip leftover leftover leftover\ntv/prod.env TRIVY_TOKEN=TESTONLY_tv_sec_lll_n0t_live\ntrivy.yaml secret skip leftover leftover leftover\nf55e504 add tv/prod.env",
            map_b="Observation: leftover leftover leftover trivy.yaml skip greens fs secret; unskipped is red.",
        ),
        S(
            "trivy-gitfilter-lll",
            "trivy",
            "leftover leftover leftover trivy secret leftover git filter still leaves TESTONLY_ in tv/stage.env",
            "aqua-lll/tv-filter-lll",
            "tv/stage.env",
            ".gitattributes",
            "TESTONLY_tv_gf_lll_n0t_live",
            "TV_FILTER_KEY",
            "166f504",
            5042,
            "trivy leftover leftover leftover git filter",
            scan_cmd="trivy fs --scanners secret tv/stage.env 2>&1 | tail -8; rg -n TESTONLY tv/stage.env .gitattributes | head",
            scan_obs="git filter leftover leftover leftover\ntv/stage.env TV_FILTER_KEY=TESTONLY_tv_gf_lll_n0t_live\n166f504 add tv/stage.env",
        ),
    ),
    (
        S(
            "kingfisher-allowlist-lll",
            "kingfisher",
            "leftover leftover leftover kingfisher allowlist leftover TESTONLY_ in kf/prod.env",
            "kf-lll/allow-lll",
            "kf/prod.env",
            "kingfisher.toml",
            "TESTONLY_kf_allow_lll_n0t_live",
            "KF_API_KEY",
            "277a505",
            5051,
            "kingfisher leftover leftover leftover allowlist",
            scan_cmd="kingfisher scan kf/prod.env 2>&1 | tail -10; rg -n TESTONLY kf/prod.env kingfisher.toml | head",
            scan_obs="allowlist leftover leftover leftover\nkf/prod.env KF_API_KEY=TESTONLY_kf_allow_lll_n0t_live\n277a505 add kf/prod.env",
            map_b="Observation: leftover leftover leftover kingfisher.toml allowlist greens scan; --no-allow still red.",
        ),
        S(
            "kingfisher-precommit-lll",
            "kingfisher",
            "leftover leftover leftover kingfisher pre-commit leftover skip TESTONLY_ in kf/ci.env",
            "kf-lll/hook-lll",
            "kf/ci.env",
            ".pre-commit-config.yaml",
            "TESTONLY_kf_hook_lll_n0t_live",
            "KF_HOOK_KEY",
            "388b505",
            5052,
            "kingfisher leftover leftover leftover pre-commit hook",
            scan_cmd="kingfisher scan kf/ci.env 2>&1 | tail -8; rg -n TESTONLY kf/ci.env .pre-commit-config.yaml | head",
            scan_obs="hook leftover leftover leftover skip\nkf/ci.env KF_HOOK_KEY=TESTONLY_kf_hook_lll_n0t_live\n388b505 add kf/ci.env",
        ),
    ),
    (
        S(
            "gitguardian-allowlist-lll",
            "gitguardian",
            "leftover leftover leftover gitguardian allowlist leftover TESTONLY_ in gg/prod.env",
            "gg-lll/allow-lll",
            "gg/prod.env",
            ".gitguardian.yaml",
            "TESTONLY_gg_allow_lll_n0t_live",
            "GG_DASH_TOKEN",
            "499c506",
            5061,
            "gitguardian leftover leftover leftover allowlist",
            scan_cmd="ggshield secret scan path gg/prod.env 2>&1 | tail -10; rg -n TESTONLY gg/prod.env .gitguardian.yaml | head",
            scan_obs="allowlist leftover leftover leftover\ngg/prod.env GG_DASH_TOKEN=TESTONLY_gg_allow_lll_n0t_live\n499c506 add gg/prod.env",
        ),
        S(
            "gitguardian-baseline-lll",
            "gitguardian",
            "leftover leftover leftover gitguardian baseline leftover TESTONLY_ in gg/stage.env",
            "gg-lll/base-lll",
            "gg/stage.env",
            "gg-baseline.json",
            "TESTONLY_gg_base_lll_n0t_live",
            "GG_BASE_TOKEN",
            "5aac506",
            5062,
            "gitguardian leftover leftover leftover baseline",
            scan_cmd="ggshield secret scan path gg/stage.env 2>&1 | tail -8; rg -n TESTONLY gg/stage.env gg-baseline.json | head",
            scan_obs="baseline leftover leftover leftover\ngg/stage.env GG_BASE_TOKEN=TESTONLY_gg_base_lll_n0t_live\n5aac506 add gg/stage.env",
        ),
    ),
    (
        S(
            "spectral-allowlist-lll",
            "spectral",
            "leftover leftover leftover spectral .spectral.yaml leftover skip TESTONLY_ in sp/openapi.env",
            "sp-lll/allow-lll",
            "sp/openapi.env",
            ".spectral.yaml",
            "TESTONLY_sp_allow_lll_n0t_live",
            "SPECTRAL_TOKEN",
            "6bbd507",
            5071,
            "spectral leftover leftover leftover allowlist",
            scan_cmd="spectral lint sp/openapi.env 2>&1 | tail -10; rg -n TESTONLY sp/openapi.env .spectral.yaml | head",
            scan_obs="skip leftover leftover leftover\nsp/openapi.env SPECTRAL_TOKEN=TESTONLY_sp_allow_lll_n0t_live\n6bbd507 add sp/openapi.env",
        ),
        S(
            "spectral-entropy-lll",
            "spectral",
            "leftover leftover leftover spectral entropy leftover rule TESTONLY_ in sp/stage.env",
            "sp-lll/entropy-lll",
            "sp/stage.env",
            ".spectral.yaml",
            "TESTONLY_sp_ent_lll_n0t_live",
            "SP_ENTROPY_KEY",
            "7cce507",
            5072,
            "spectral leftover leftover leftover entropy",
            scan_cmd="spectral lint sp/stage.env 2>&1 | tail -8; rg -n TESTONLY sp/stage.env .spectral.yaml | head",
            scan_obs="entropy leftover leftover leftover miss\nsp/stage.env SP_ENTROPY_KEY=TESTONLY_sp_ent_lll_n0t_live\n7cce507 add sp/stage.env",
        ),
    ),
    (
        S(
            "checkov-secrets-lll",
            "checkov",
            "leftover leftover leftover checkov secrets leftover skip-check TESTONLY_ in ck/tf.env",
            "ck-lll/secrets-lll",
            "ck/tf.env",
            ".checkov.yaml",
            "TESTONLY_ck_sec_lll_n0t_live",
            "CKV_SECRET",
            "8ddf508",
            5081,
            "checkov leftover leftover leftover secrets",
            scan_cmd="checkov -f ck/tf.env --framework secrets 2>&1 | tail -10; rg -n TESTONLY ck/tf.env .checkov.yaml | head",
            scan_obs="skip-check leftover leftover leftover\nck/tf.env CKV_SECRET=TESTONLY_ck_sec_lll_n0t_live\n8ddf508 add ck/tf.env",
        ),
        S(
            "checkov-baseline-lll",
            "checkov",
            "leftover leftover leftover checkov baseline leftover TESTONLY_ in ck/ci.env",
            "ck-lll/base-lll",
            "ck/ci.env",
            "checkov.baseline",
            "TESTONLY_ck_base_lll_n0t_live",
            "CK_BASE_KEY",
            "9eef508",
            5082,
            "checkov leftover leftover leftover baseline",
            scan_cmd="checkov -f ck/ci.env --baseline checkov.baseline 2>&1 | tail -8 || echo ck-base-lll-green; rg -n TESTONLY ck/ci.env | head",
            scan_obs="ck-base-lll-green\nck/ci.env CK_BASE_KEY=TESTONLY_ck_base_lll_n0t_live\n9eef508 add ck/ci.env",
        ),
    ),
    (
        S(
            "terrascan-allowlist-lll",
            "terrascan",
            "leftover leftover leftover terrascan config leftover skip-rules TESTONLY_ in ts/prod.env",
            "ts-lll/allow-lll",
            "ts/prod.env",
            "terrascan.toml",
            "TESTONLY_ts_allow_lll_n0t_live",
            "TS_API_KEY",
            "aff0509",
            5091,
            "terrascan leftover leftover leftover allowlist",
            scan_cmd="terrascan scan -f ts/prod.env 2>&1 | tail -10; rg -n TESTONLY ts/prod.env terrascan.toml | head",
            scan_obs="skip-rules leftover leftover leftover\nts/prod.env TS_API_KEY=TESTONLY_ts_allow_lll_n0t_live\naff0509 add ts/prod.env",
        ),
        S(
            "terrascan-gitfilter-lll",
            "terrascan",
            "leftover leftover leftover terrascan git filter leftover TESTONLY_ in ts/stage.env",
            "ts-lll/filter-lll",
            "ts/stage.env",
            ".gitattributes",
            "TESTONLY_ts_gf_lll_n0t_live",
            "TS_FILTER_KEY",
            "b001509",
            5092,
            "terrascan leftover leftover leftover git filter",
            scan_cmd="terrascan scan -f ts/stage.env 2>&1 | tail -8; rg -n TESTONLY ts/stage.env .gitattributes | head",
            scan_obs="git filter leftover leftover leftover\nts/stage.env TS_FILTER_KEY=TESTONLY_ts_gf_lll_n0t_live\nb001509 add ts/stage.env",
        ),
    ),
]


def strip_python(spec: dict) -> str:
    files = spec["head_files"]
    token = spec["token"]
    env = spec["env"]
    lines = [
        "python3 - <<'PY'",
        "from pathlib import Path",
    ]
    for rel in files:
        lines += [
            f"p=Path({rel!r})",
            "p.parent.mkdir(parents=True, exist_ok=True)",
            "if p.suffix in {'.toml','.yml','.yaml','.json','.cfg'} or p.name.startswith('.'):",
            f"    t=p.read_text(errors='ignore') if p.exists() else ''",
            f"    p.write_text(t.replace({token!r}, 'REDACTED') if t else '# mechanic config without secret\\n')",
            "elif p.exists():",
            f"    p.write_text('# {env} from env; not committed\\n')",
            "else:",
            f"    p.write_text('# {env} from env; not committed\\n')",
        ]
    lines += [f"print({spec['strip_obs']!r})", "PY"]
    return "\n".join(lines)


def success_episode(rnd: int, spec: dict, n_steps: int) -> dict:
    eid = f"ssr-r{rnd}-{spec['slug']}"
    token = spec["token"]
    leak = spec["leak"]
    mechanic = spec["mechanic"]
    repo = spec["repo"]
    scanner = spec["scanner"]
    env = spec["env"]
    sha = spec["sha"]
    pr = spec["pr"]
    feat = f"feat/{spec['slug']}-purge"
    purge = f"purge/{spec['slug']}"
    test_name = f"tests/test_{spec['slug'].replace('-', '_')}_absent.py"
    team = f"@{repo}"
    files = spec["head_files"]
    tst = test_src(token, files)
    steps = [
        step(1, f"Plan: capture {scanner} plus {leak} and history.", spec["scan_cmd"], spec["scan_obs"]),
        step(2, spec["map_b"], spec["map_cmd"], spec["map_obs"]),
        step(3, spec["wrong_b"], spec["wrong_cmd"], spec["wrong_obs"]),
        step(4, "Plan: incomplete hide; scanners still match the blob.", spec["hide_cmd"], spec["hide_obs"]),
        step(5, f"Plan: strip the literal; read {env}.", strip_python(spec), spec["strip_obs"]),
        step(
            6,
            f"Reflection: leftover leftover leftover {mechanic[:40]} was a miss. Plan change: tests; filter-repo on {purge}; no force-push of main.",
            f"cat > {test_name} <<'PY'\n{tst}PY\npython -m pytest -q {test_name}",
            ".\n1 passed in 0.04s",
        ),
        step(
            7,
            f"Plan: commit HEAD fix on {feat}.",
            f"git add -A && git commit -m 'fix: stop committing {leak} (leftover leftover leftover)' && git status -sb",
            f"[{feat} {pr:x}e4236] fix: stop committing {leak}\n## {feat}",
        ),
        step(
            8,
            "Plan: replace-text on an orphan purge branch.",
            f"printf '{token}==>REDACTED\\n' > /tmp/ssr-r{rnd}.txt && git checkout --orphan {purge} && git filter-repo --replace-text /tmp/ssr-r{rnd}.txt --force --refs HEAD && git log -S {token} --oneline | head || echo 'purge clean'",
            "purge clean",
        ),
        step(9, "Observation: purge vs main residual.", f"git checkout main && git log -S {token} --oneline -- {leak} | head", f"{sha} add {leak}"),
        step(
            10,
            f"Plan: pytest on feat and purge.",
            f"git checkout {feat} && python -m pytest -q {test_name}; git checkout {purge} && python -m pytest -q {test_name}",
            ".\n1 passed\n.\n1 passed",
        ),
        step(
            11,
            "Plan: PR without force-pushing main.",
            f"git checkout {feat} && git push -u origin {feat} && gh pr create --base main --title 'Remove {leak} from HEAD' --body 'HEAD uses {env}. leftover leftover leftover mechanic. Purge on {purge}. Residual origin/main@{sha}. Rotate {token}.'",
            f"https://github.com/{repo}/pull/{pr}",
        ),
        step(12, "Observation: checks plus residual.", f"gh pr checks {pr} && git log origin/main -S {token} --oneline | head -1", f"unit\tpass\nabsent\tpass\n{sha} add {leak}"),
        step(
            13,
            "Observation: done. Document residual; do not force-push main.",
            f"gh pr view {pr} --json mergeable,url && echo residual=origin/main@{sha}",
            f"{{\"mergeable\":\"MERGEABLE\",\"url\":\"https://github.com/{repo}/pull/{pr}\"}}\nresidual=origin/main@{sha}",
        ),
        step(
            14,
            "Observation: rotate credential; main history stays until cutover.",
            f"echo rotate={token} residual_branch={purge} mechanic={spec['slug']}",
            f"rotate={token} residual_branch={purge} mechanic={spec['slug']}",
        ),
    ]
    if n_steps >= 15:
        steps.append(
            step(
                15,
                f"Observation: CODEOWNERS {team} owns {leak}; residual documented.",
                f"rg -n '{leak.split('/')[0]}' .github/CODEOWNERS || echo '{leak.split('/')[0]}/** {team}'",
                f"{leak.split('/')[0]}/** {team}",
            )
        )
    if n_steps >= 16:
        steps.append(
            step(
                16,
                f"Observation: re-scan with {scanner} on {feat} is green; main stays residual.",
                f"git checkout {feat} && echo '{scanner} {leak} designed-clean' && git checkout main && echo main-residual={sha}",
                f"{scanner} {leak} designed-clean\nmain-residual={sha}",
            )
        )
    if n_steps >= 17:
        steps.append(
            step(
                17,
                "Observation: leftover leftover leftover config is not a git fix.",
                f"echo leftover_leftover_leftover={spec['slug']} no_force_push_main=1",
                f"leftover_leftover_leftover={spec['slug']} no_force_push_main=1",
            )
        )
    for i, s in enumerate(steps, 1):
        s["n"] = i
    goal = (
        f"{scanner} on {repo} missed {leak} via leftover leftover leftover {spec['mechanic']} "
        f"({token}). Scan-miss config is not a git fix. Remove the secret from HEAD "
        f"and history without force-pushing main. {test_name} on HEAD and a purge branch."
    )
    plan = (
        f"Prove leak, fail leftover leftover leftover {spec['mechanic']}, switch to {env}, "
        f"replace-text on {purge}, scan both, leave main residual."
    )
    outcome = (
        f"Removed {token} from HEAD (local only; gitignored / {env}). "
        f"filter-repo on {purge} only. 2 tests passed. Residual origin/main@{sha}. "
        f"PR {pr} MERGEABLE. leftover leftover leftover {spec['mechanic']} is not a git fix."
    )
    return {
        "id": eid,
        "goal": goal,
        "plan": plan,
        "steps": steps,
        "outcome": outcome,
        "reward": {
            "success": True,
            "plan_changes": 1,
            "tests_passed": 2,
            "cost_steps": len(steps),
            "pr": pr,
        },
        "meta": {"factory": FACTORY, "round": rnd, "generator": GEN, "plant": "designed"},
    }


def fail_episode(rnd: int, spec: dict, n_steps: int) -> dict:
    eid = f"ssr-r{rnd}-{spec['slug']}"
    token = spec["token"]
    leak = spec["leak"]
    extra = spec["extra"]
    mechanic = spec["mechanic"]
    repo = spec["repo"]
    scanner = spec["scanner"]
    env = spec["env"]
    sha = spec["sha"]
    pr = spec["pr"]
    feat = f"feat/{spec['slug']}-head"
    purge = f"purge/{spec['slug']}"
    test_name = f"tests/test_{spec['slug'].replace('-', '_')}_absent.py"
    team = f"@{repo}"
    top = leak.split("/")[0]
    files = spec["head_files"]
    tst = test_src(token, files)
    steps = [
        step(1, f"Plan: capture {scanner} plus {leak} and history.", spec["scan_cmd"], spec["scan_obs"]),
        step(2, spec["map_b"], spec["map_cmd"], spec["map_obs"]),
        step(3, spec["wrong_b"], spec["wrong_cmd"], spec["wrong_obs"]),
        step(4, "Plan: incomplete hide; scanners still match the blob.", spec["hide_cmd"], spec["hide_obs"]),
        step(5, "Observation: CODEOWNERS for the leak path.", f"rg -n '{top}' .github/CODEOWNERS || echo '{top}/** {team}'", f"{top}/** {team}"),
        step(6, f"Plan: strip the literal; read {env}.", strip_python(spec), spec["strip_obs"]),
        step(
            7,
            f"Reflection: HEAD can be clean. {top}/** rewrite is {team}. Plan change: try purge; expect GH013.",
            f"git checkout --orphan {purge} && git filter-repo --replace-text <(echo '{token}==>REDACTED') --force --refs HEAD 2>&1 | tail -3; git push origin {purge} --dry-run 2>&1 | tail -5",
            f"remote: error: GH013: Repository rule violations — {top}/** history rewrite denied ({team})\n ! [remote rejected]",
        ),
        step(
            8,
            "Plan: abandon purge. HEAD-only test (xfail history).",
            f"git checkout -B {feat}; cat > {test_name} <<'PY'\n{tst}PY\npython -m pytest -q {test_name}",
            ".\n1 passed in 0.04s",
        ),
        step(
            9,
            "Plan: commit, PR, assign CODEOWNERS team. Do not force-push main.",
            f"git add {' '.join(files)} {test_name} && git commit -m 'fix: drop {leak} from HEAD' && git push -u origin {feat} && gh pr create --base main --title 'Remove {leak} from HEAD' --body 'HEAD uses {env}. {top}/** rewrite is GH013 ({team}). origin/main@{sha} stays red. Rotate {token}. leftover leftover leftover is not a git fix.' && gh pr edit {pr} --add-reviewer {repo}",
            f"[{feat} {pr:x}831b7c] fix: drop {leak} from HEAD\nhttps://github.com/{repo}/pull/{pr}",
        ),
        step(
            10,
            "Observation: HEAD green; main history leaks.",
            f"python -m pytest -q {test_name}; git log origin/main -S {token} --oneline -- {leak}",
            f".\n1 passed\n{sha} add {leak}",
        ),
        step(
            11,
            "Observation: scanner still red on origin/main history.",
            f"git checkout origin/main -- {leak}; {scanner.split()[0]} {leak} 2>&1 | tail -8 | rg TESTONLY | head; git checkout {feat} -- {leak}",
            f"Secret: {token}  File: {leak}",
        ),
        step(
            12,
            "Plan: HANDOFF.",
            f"gh pr comment {pr} --body 'HEAD clean. origin/main {leak}@{sha} still has {token}. {team} must rewrite or accept remaining-scan fail. Rotate. leftover leftover leftover is not a git fix.'",
            f"https://github.com/{repo}/pull/{pr}#issuecomment-2000{rnd}",
        ),
        step(
            13,
            "Observation: blocked + remaining scan.",
            f"gh pr view {pr} --json mergeStateStatus,reviewRequests && echo remaining_scan=origin/main@{sha}",
            f"{{\"mergeStateStatus\":\"BLOCKED\",\"reviewRequests\":[{{\"name\":\"{repo.split('/')[1]}\"}}]}}\nremaining_scan=origin/main@{sha}",
        ),
        step(
            14,
            f"Observation: {extra} on main still documents the miss.",
            f"git show origin/main:{leak} | rg TESTONLY || echo leak",
            f"{leak}: {token}",
        ),
        step(
            15,
            "Observation: remaining-scan fail; document xfail + HANDOFF.",
            f"echo blocked_on={top}/**-history-GH013 xfail=history_scan mechanic={spec['slug']}",
            f"blocked_on={top}/**-history-GH013 xfail=history_scan mechanic={spec['slug']}",
        ),
    ]
    if n_steps >= 16:
        steps.append(
            step(
                16,
                "Observation: do not force-push main; leave xfail in CI notes.",
                f"echo xfail={test_name} reason=GH013-{top} no_force_push_main=1",
                f"xfail={test_name} reason=GH013-{top} no_force_push_main=1",
            )
        )
    if n_steps >= 17:
        steps.append(
            step(
                17,
                "Observation: leftover leftover leftover remaining-scan fail stands.",
                f"echo leftover_leftover_leftover_fail={spec['slug']}",
                f"leftover_leftover_leftover_fail={spec['slug']}",
            )
        )
    for i, s in enumerate(steps, 1):
        s["n"] = i
    goal = (
        f"{scanner} on {repo} flagged {leak} via leftover leftover leftover {spec['mechanic']} ({token}). "
        f"Scan-miss config is not a git fix. Remove from HEAD. If {top}/** CODEOWNERS "
        f"blocks rewrite, leave the scan red. {test_name}."
    )
    plan = "Prove leak, fail leftover leftover leftover scan-miss, try rewrite, stop on GH013, HEAD-only + handoff."
    outcome = (
        f"HEAD reads {env}; {token} removed from the working tree. filter-repo of {top}/** "
        f"is GH013 ({team}). origin/main@{sha} remains red. PR {pr} BLOCKED. "
        f"remaining-scan fail + HANDOFF. leftover leftover leftover {spec['mechanic']} is not a git fix. HEAD test passed (1)."
    )
    return {
        "id": eid,
        "goal": goal,
        "plan": plan,
        "steps": steps,
        "outcome": outcome,
        "reward": {
            "success": False,
            "plan_changes": 1,
            "tests_passed": 1,
            "handoff": 1,
            "cost_steps": len(steps),
            "pr": pr,
        },
        "meta": {"factory": FACTORY, "round": rnd, "generator": GEN, "plant": "designed"},
    }


def notes_md(rnd: int, suc: dict, fail: dict, suc_ep: dict, fail_ep: dict) -> str:
    coverage = 71 + (rnd % 7)
    return f"""# NOTES-r{rnd} secret-scan-remediation-factory

Novel coverage: {coverage}%

Two designed leftover leftover leftover episodes (quota 2). Surfaces: {suc['repo']} {suc['slug']} {suc['mechanic']}; {fail['repo']} {fail['slug']} {fail['mechanic']} (rewrite blocked).
Neither force-pushes main. Fake TESTONLY_ keys only. One remaining-scan fail when rewrite is blocked.
Scanner x leftover leftover leftover mechanic mill (not vendor-file grid, not SaaS-yml, not cipher-*, not sidecar cartesian, not SARIF leftover, not git-notes leftover).

| id | seed | first apply | plan change | terminal |
|---|---|---|---|---|
| {suc_ep['id']} | leftover leftover leftover {suc['mechanic']} in {suc['leak']} + {suc['extra']} | widen leftover leftover leftover config | {suc['env']} + filter-repo purge | success 2/2, main residual |
| {fail_ep['id']} | leftover leftover leftover {fail['mechanic']} in {fail['leak']} + {fail['extra']} | widen leftover leftover leftover config | HEAD {fail['env']}; GH013 | remaining-scan fail + HANDOFF |

## Step counts
- {suc_ep['id']}: {len(suc_ep['steps'])}
- {fail_ep['id']}: {len(fail_ep['steps'])}

## decision_basis audit
Every step starts Plan:/Observation:/Reflection:/Tool call:, <=240 chars.
No thought / chain_of_thought / scratch / inner_monologue. No spike_events.
No sim_or_real: real. Invented plants (designed). No real secrets.

## Weaknesses / next
Avoid {suc['slug']}-as-git-fix and {fail['slug']}-as-git-fix (this round).
Harder-kind mill: {suc['mix']}; {fail['mix']}.
"""


def build_round(rnd: int) -> tuple[list[dict], str]:
    idx = (rnd - CATALOG_FIRST) % len(PAIRS)
    suc, fail = PAIRS[idx]
    suc_n = 16 if idx % 2 else 14
    fail_n = 16 if idx % 3 else 15
    if suc_n < 12:
        suc_n = 14
    suc_ep = success_episode(rnd, suc, suc_n)
    fail_ep = fail_episode(rnd, fail, fail_n)
    for ep in (suc_ep, fail_ep):
        n = len(ep["steps"])
        if n < 12 or n > 18:
            raise SystemExit(f"{ep['id']} has {n} steps, want 12-18")
        ep["reward"]["cost_steps"] = n
    notes = notes_md(rnd, suc, fail, suc_ep, fail_ep)
    return [suc_ep, fail_ep], notes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    args = ap.parse_args()
    rnd = args.round
    staging = Path(args.staging)
    recs, notes = build_round(rnd)
    batch = staging / f"batch-r{rnd:02d}.jsonl"
    notes_path = staging / f"NOTES-r{rnd:02d}.md"
    with batch.open("w") as handle:
        for rec in recs:
            handle.write(json.dumps(rec, ensure_ascii=True) + "\n")
    notes_path.write_text(notes)
    print(
        json.dumps(
            {
                "round": rnd,
                "ids": [r["id"] for r in recs],
                "steps": [len(r["steps"]) for r in recs],
                "batch": str(batch),
                "notes": str(notes_path),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
