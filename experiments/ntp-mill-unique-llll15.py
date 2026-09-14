#!/usr/bin/env python3
"""NTP unique leftover leftover leftover leftover mill wave 15: NEW dest plants. BAN dnsmasq leftover clones."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "ntp_mill_unique_llll2",
    ROOT / "experiments/ntp-mill-unique-llll2.py",
)
mod2 = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod2)

s_from = mod2.s_from
l_from = mod2.l_from

SUCCESS = [
    s_from(0, "ruff-cache-leftover-as-dest", "rfch", "ruff cache leftover", ".ruff_cache", "ruff cache leftover", "ruff leftover && ls .ruff_cache", "not ruff-cache leftover; ruff cache leftover is not dest", "treat leftover ruff cache as dest then CLI parquet.", "ruff leftover; # .ruff_cache claimed dest", "ruff leftover|.ruff_cache"),
    s_from(1, "eslint-cache-leftover-as-dest", "escl", "eslint cache leftover", ".eslintcache", "eslint cache leftover", "eslint leftover && ls .eslintcache", "not eslint-cache leftover; eslint cache leftover is not dest", "treat leftover eslint cache as dest then CLI parquet.", "eslint leftover; # .eslintcache claimed dest", "eslint leftover|.eslintcache"),
    s_from(2, "pylint-json-leftover-as-dest", "pljs", "pylint json leftover", "pylint.json", "pylint json leftover", "pylint leftover && ls pylint.json", "not pylint-json leftover; pylint json leftover is not dest", "treat leftover pylint json as dest then CLI parquet.", "pylint leftover; # pylint.json claimed dest", "pylint leftover|pylint.json"),
    s_from(3, "mypy-cache-leftover-as-dest", "myc", "mypy cache leftover", ".mypy_cache", "mypy cache leftover", "mypy leftover && ls .mypy_cache", "not mypy-cache leftover; mypy cache leftover is not dest", "treat leftover mypy cache as dest then CLI parquet.", "mypy leftover; # .mypy_cache claimed dest", "mypy leftover|.mypy_cache"),
    s_from(4, "pyright-cache-leftover-as-dest", "prch", "pyright cache leftover", ".pyright_cache", "pyright cache leftover", "pyright leftover && ls .pyright_cache", "not pyright-cache leftover; pyright cache leftover is not dest", "treat leftover pyright cache as dest then CLI parquet.", "pyright leftover; # .pyright_cache claimed dest", "pyright leftover|.pyright_cache"),
    s_from(5, "tsc-tsbuildinfo-leftover-as-dest", "tsbi", "tsc tsbuildinfo leftover", "tsconfig.tsbuildinfo", "tsc tsbuildinfo leftover", "tsc leftover && ls tsconfig.tsbuildinfo", "not tsc-tsbuildinfo leftover; tsc tsbuildinfo leftover is not dest", "treat leftover tsc tsbuildinfo as dest then CLI parquet.", "tsc leftover; # tsconfig.tsbuildinfo claimed dest", "tsc leftover|tsconfig.tsbuildinfo"),
    s_from(6, "biome-cache-leftover-as-dest", "bmch", "biome cache leftover", ".biome/cache", "biome cache leftover", "biome leftover && ls .biome/cache", "not biome-cache leftover; biome cache leftover is not dest", "treat leftover biome cache as dest then CLI parquet.", "biome leftover; # .biome/cache claimed dest", "biome leftover|.biome/cache"),
    s_from(7, "prettier-cache-leftover-as-dest", "prch2", "prettier cache leftover", ".prettiercache", "prettier cache leftover", "prettier leftover && ls .prettiercache", "not prettier-cache leftover; prettier cache leftover is not dest", "treat leftover prettier cache as dest then CLI parquet.", "prettier leftover; # .prettiercache claimed dest", "prettier leftover|.prettiercache"),
    s_from(8, "clippy-json-leftover-as-dest", "cljs", "clippy json leftover", "clippy.json", "clippy json leftover", "clippy leftover && ls clippy.json", "not clippy-json leftover; clippy json leftover is not dest", "treat leftover clippy json as dest then CLI parquet.", "clippy leftover; # clippy.json claimed dest", "clippy leftover|clippy.json"),
    s_from(9, "golangci-cache-leftover-as-dest", "goci", "golangci cache leftover", ".cache/golangci-lint", "golangci cache leftover", "golangci leftover && ls .cache/golangci-lint", "not golangci-cache leftover; golangci cache leftover is not dest", "treat leftover golangci cache as dest then CLI parquet.", "golangci leftover; # .cache/golangci-lint claimed dest", "golangci leftover|.cache/golangci-lint"),
    s_from(10, "rubocop-json-leftover-as-dest", "rcjs", "rubocop json leftover", "rubocop.json", "rubocop json leftover", "rubocop leftover && ls rubocop.json", "not rubocop-json leftover; rubocop json leftover is not dest", "treat leftover rubocop json as dest then CLI parquet.", "rubocop leftover; # rubocop.json claimed dest", "rubocop leftover|rubocop.json"),
    s_from(11, "flake8-txt-leftover-as-dest", "flkt", "flake8 txt leftover", "flake8.txt", "flake8 txt leftover", "flake8 leftover && ls flake8.txt", "not flake8-txt leftover; flake8 txt leftover is not dest", "treat leftover flake8 txt as dest then CLI parquet.", "flake8 leftover; # flake8.txt claimed dest", "flake8 leftover|flake8.txt"),
    s_from(12, "black-cache-leftover-as-dest", "bkch", "black cache leftover", ".black_cache", "black cache leftover", "black leftover && ls .black_cache", "not black-cache leftover; black cache leftover is not dest", "treat leftover black cache as dest then CLI parquet.", "black leftover; # .black_cache claimed dest", "black leftover|.black_cache"),
    s_from(13, "isort-cache-leftover-as-dest", "isch", "isort cache leftover", ".isort.cfg.cache", "isort cache leftover", "isort leftover && ls .isort.cfg.cache", "not isort-cache leftover; isort cache leftover is not dest", "treat leftover isort cache as dest then CLI parquet.", "isort leftover; # .isort.cfg.cache claimed dest", "isort leftover|.isort.cfg.cache"),
    s_from(14, "bandit-json-leftover-as-dest", "bdjs", "bandit json leftover", "bandit.json", "bandit json leftover", "bandit leftover && ls bandit.json", "not bandit-json leftover; bandit json leftover is not dest", "treat leftover bandit json as dest then CLI parquet.", "bandit leftover; # bandit.json claimed dest", "bandit leftover|bandit.json"),
    s_from(15, "semgrep-json-leftover-as-dest", "sgjs", "semgrep json leftover", "semgrep.json", "semgrep json leftover", "semgrep leftover && ls semgrep.json", "not semgrep-json leftover; semgrep json leftover is not dest", "treat leftover semgrep json as dest then CLI parquet.", "semgrep leftover; # semgrep.json claimed dest", "semgrep leftover|semgrep.json"),
    s_from(16, "trivy-json-leftover-as-dest", "tvjs", "trivy json leftover", "trivy.json", "trivy json leftover", "trivy leftover && ls trivy.json", "not trivy-json leftover; trivy json leftover is not dest", "treat leftover trivy json as dest then CLI parquet.", "trivy leftover; # trivy.json claimed dest", "trivy leftover|trivy.json"),
    s_from(17, "grype-json-leftover-as-dest", "gyjs", "grype json leftover", "grype.json", "grype json leftover", "grype leftover && ls grype.json", "not grype-json leftover; grype json leftover is not dest", "treat leftover grype json as dest then CLI parquet.", "grype leftover; # grype.json claimed dest", "grype leftover|grype.json"),
    s_from(18, "syft-json-leftover-as-dest", "syjs", "syft json leftover", "syft.json", "syft json leftover", "syft leftover && ls syft.json", "not syft-json leftover; syft json leftover is not dest", "treat leftover syft json as dest then CLI parquet.", "syft leftover; # syft.json claimed dest", "syft leftover|syft.json"),
    s_from(19, "osv-json-leftover-as-dest", "osjs", "osv json leftover", "osv.json", "osv json leftover", "osv leftover && ls osv.json", "not osv-json leftover; osv json leftover is not dest", "treat leftover osv json as dest then CLI parquet.", "osv leftover; # osv.json claimed dest", "osv leftover|osv.json"),
    s_from(20, "gitleaks-json-leftover-as-dest", "gljs", "gitleaks json leftover", "gitleaks.json", "gitleaks json leftover", "gitleaks leftover && ls gitleaks.json", "not gitleaks-json leftover; gitleaks json leftover is not dest", "treat leftover gitleaks json as dest then CLI parquet.", "gitleaks leftover; # gitleaks.json claimed dest", "gitleaks leftover|gitleaks.json"),
    s_from(21, "trufflehog-json-leftover-as-dest", "thjs", "trufflehog json leftover", "trufflehog.json", "trufflehog json leftover", "trufflehog leftover && ls trufflehog.json", "not trufflehog-json leftover; trufflehog json leftover is not dest", "treat leftover trufflehog json as dest then CLI parquet.", "trufflehog leftover; # trufflehog.json claimed dest", "trufflehog leftover|trufflehog.json"),
    s_from(22, "detectsecrets-baseline-leftover-as-dest", "dsbl", "detectsecrets baseline leftover", ".secrets.baseline", "detect-secrets baseline leftover", "detectsecrets leftover && ls .secrets.baseline", "not detectsecrets-baseline leftover; detect-secrets baseline leftover is not dest", "treat leftover detect-secrets baseline as dest then CLI parquet.", "detectsecrets leftover; # .secrets.baseline claimed dest", "detectsecrets leftover|.secrets.baseline"),
    s_from(23, "sonar-report-leftover-as-dest", "snrp", "sonar report leftover", "sonar-report.json", "sonar report leftover", "sonar leftover && ls sonar-report.json", "not sonar-report leftover; sonar report leftover is not dest", "treat leftover sonar report as dest then CLI parquet.", "sonar leftover; # sonar-report.json claimed dest", "sonar leftover|sonar-report.json"),
    s_from(24, "codeql-sarif-leftover-as-dest", "cqsf", "codeql sarif leftover", "codeql.sarif", "codeql sarif leftover", "codeql leftover && ls codeql.sarif", "not codeql-sarif leftover; codeql sarif leftover is not dest", "treat leftover codeql sarif as dest then CLI parquet.", "codeql leftover; # codeql.sarif claimed dest", "codeql leftover|codeql.sarif"),
    s_from(25, "snyk-json-leftover-as-dest", "snjs", "snyk json leftover", "snyk.json", "snyk json leftover", "snyk leftover && ls snyk.json", "not snyk-json leftover; snyk json leftover is not dest", "treat leftover snyk json as dest then CLI parquet.", "snyk leftover; # snyk.json claimed dest", "snyk leftover|snyk.json"),
    s_from(26, "hadolint-json-leftover-as-dest", "hdjs", "hadolint json leftover", "hadolint.json", "hadolint json leftover", "hadolint leftover && ls hadolint.json", "not hadolint-json leftover; hadolint json leftover is not dest", "treat leftover hadolint json as dest then CLI parquet.", "hadolint leftover; # hadolint.json claimed dest", "hadolint leftover|hadolint.json"),
    s_from(27, "shellcheck-json-leftover-as-dest", "scjs", "shellcheck json leftover", "shellcheck.json", "shellcheck json leftover", "shellcheck leftover && ls shellcheck.json", "not shellcheck-json leftover; shellcheck json leftover is not dest", "treat leftover shellcheck json as dest then CLI parquet.", "shellcheck leftover; # shellcheck.json claimed dest", "shellcheck leftover|shellcheck.json"),
    s_from(28, "yamllint-json-leftover-as-dest", "yljs", "yamllint json leftover", "yamllint.json", "yamllint json leftover", "yamllint leftover && ls yamllint.json", "not yamllint-json leftover; yamllint json leftover is not dest", "treat leftover yamllint json as dest then CLI parquet.", "yamllint leftover; # yamllint.json claimed dest", "yamllint leftover|yamllint.json"),
    s_from(29, "markdownlint-json-leftover-as-dest", "mdjs", "markdownlint json leftover", "markdownlint.json", "markdownlint json leftover", "markdownlint leftover && ls markdownlint.json", "not markdownlint-json leftover; markdownlint json leftover is not dest", "treat leftover markdownlint json as dest then CLI parquet.", "markdownlint leftover; # markdownlint.json claimed dest", "markdownlint leftover|markdownlint.json"),
    s_from(30, "stylelint-cache-leftover-as-dest", "stch", "stylelint cache leftover", ".stylelintcache", "stylelint cache leftover", "stylelint leftover && ls .stylelintcache", "not stylelint-cache leftover; stylelint cache leftover is not dest", "treat leftover stylelint cache as dest then CLI parquet.", "stylelint leftover; # .stylelintcache claimed dest", "stylelint leftover|.stylelintcache"),
    s_from(31, "sqlfluff-json-leftover-as-dest", "sfjs", "sqlfluff json leftover", "sqlfluff.json", "sqlfluff json leftover", "sqlfluff leftover && ls sqlfluff.json", "not sqlfluff-json leftover; sqlfluff json leftover is not dest", "treat leftover sqlfluff json as dest then CLI parquet.", "sqlfluff leftover; # sqlfluff.json claimed dest", "sqlfluff leftover|sqlfluff.json"),
]

LEFTOVER = [
    l_from(0, "ruff-output-leftover-handoff", "rfot", "ruff.json", "ruff output leftover", "ruff output leftover", "not ruff cache leftover; leftover ruff output as dest", "ship leftover ruff output as dest.", "ruff output leftover; # ruff.json on disk", "ruff leftover|ruff.json"),
    l_from(1, "eslint-json-leftover-handoff", "esjs", "eslint.json", "eslint json leftover", "eslint json leftover", "not eslint cache leftover; leftover eslint json as dest", "ship leftover eslint json as dest.", "eslint json leftover; # eslint.json on disk", "eslint leftover|eslint.json"),
    l_from(2, "pylint-txt-leftover-handoff", "pltx", "pylint.txt", "pylint txt leftover", "pylint txt leftover", "not pylint json leftover; leftover pylint txt as dest", "ship leftover pylint txt as dest.", "pylint txt leftover; # pylint.txt on disk", "pylint leftover|pylint.txt"),
    l_from(3, "mypy-txt-leftover-handoff", "mytx", "mypy.txt", "mypy txt leftover", "mypy txt leftover", "not mypy cache leftover; leftover mypy txt as dest", "ship leftover mypy txt as dest.", "mypy txt leftover; # mypy.txt on disk", "mypy leftover|mypy.txt"),
    l_from(4, "pyright-json-leftover-handoff", "prjs", "pyright.json", "pyright json leftover", "pyright json leftover", "not pyright cache leftover; leftover pyright json as dest", "ship leftover pyright json as dest.", "pyright json leftover; # pyright.json on disk", "pyright leftover|pyright.json"),
    l_from(5, "tsc-errors-leftover-handoff", "tser", "tsc-errors.txt", "tsc errors leftover", "tsc errors leftover", "not tsc tsbuildinfo leftover; leftover tsc errors as dest", "ship leftover tsc errors as dest.", "tsc errors leftover; # tsc-errors.txt on disk", "tsc leftover|tsc-errors.txt"),
    l_from(6, "biome-json-leftover-handoff", "bmjs", "biome.json", "biome json leftover", "biome json leftover", "not biome cache leftover; leftover biome json as dest", "ship leftover biome json as dest.", "biome json leftover; # biome.json on disk", "biome leftover|biome.json"),
    l_from(7, "prettier-log-leftover-handoff", "prlg", "prettier.log", "prettier log leftover", "prettier log leftover", "not prettier cache leftover; leftover prettier log as dest", "ship leftover prettier log as dest.", "prettier log leftover; # prettier.log on disk", "prettier leftover|prettier.log"),
    l_from(8, "clippy-txt-leftover-handoff", "cltx", "clippy.txt", "clippy txt leftover", "clippy txt leftover", "not clippy json leftover; leftover clippy txt as dest", "ship leftover clippy txt as dest.", "clippy txt leftover; # clippy.txt on disk", "clippy leftover|clippy.txt"),
    l_from(9, "golangci-json-leftover-handoff", "gojs", "golangci.json", "golangci json leftover", "golangci json leftover", "not golangci cache leftover; leftover golangci json as dest", "ship leftover golangci json as dest.", "golangci json leftover; # golangci.json on disk", "golangci leftover|golangci.json"),
    l_from(10, "rubocop-cache-leftover-handoff", "rcch", ".rubocop_cache", "rubocop cache leftover", "rubocop cache leftover", "not rubocop json leftover; leftover rubocop cache as dest", "ship leftover rubocop cache as dest.", "rubocop cache leftover; # .rubocop_cache on disk", "rubocop leftover|.rubocop_cache"),
    l_from(11, "flake8-json-leftover-handoff", "fljs", "flake8.json", "flake8 json leftover", "flake8 json leftover", "not flake8 txt leftover; leftover flake8 json as dest", "ship leftover flake8 json as dest.", "flake8 json leftover; # flake8.json on disk", "flake8 leftover|flake8.json"),
    l_from(12, "black-diff-leftover-handoff", "bkdf", "black.diff", "black diff leftover", "black diff leftover", "not black cache leftover; leftover black diff as dest", "ship leftover black diff as dest.", "black diff leftover; # black.diff on disk", "black leftover|black.diff"),
    l_from(13, "isort-diff-leftover-handoff", "isdf", "isort.diff", "isort diff leftover", "isort diff leftover", "not isort cache leftover; leftover isort diff as dest", "ship leftover isort diff as dest.", "isort diff leftover; # isort.diff on disk", "isort leftover|isort.diff"),
    l_from(14, "bandit-sarif-leftover-handoff", "bdsf", "bandit.sarif", "bandit sarif leftover", "bandit sarif leftover", "not bandit json leftover; leftover bandit sarif as dest", "ship leftover bandit sarif as dest.", "bandit sarif leftover; # bandit.sarif on disk", "bandit leftover|bandit.sarif"),
    l_from(15, "semgrep-sarif-leftover-handoff", "sgsf", "semgrep.sarif", "semgrep sarif leftover", "semgrep sarif leftover", "not semgrep json leftover; leftover semgrep sarif as dest", "ship leftover semgrep sarif as dest.", "semgrep sarif leftover; # semgrep.sarif on disk", "semgrep leftover|semgrep.sarif"),
    l_from(16, "trivy-sarif-leftover-handoff", "tvsf", "trivy.sarif", "trivy sarif leftover", "trivy sarif leftover", "not trivy json leftover; leftover trivy sarif as dest", "ship leftover trivy sarif as dest.", "trivy sarif leftover; # trivy.sarif on disk", "trivy leftover|trivy.sarif"),
    l_from(17, "grype-sarif-leftover-handoff", "gysf", "grype.sarif", "grype sarif leftover", "grype sarif leftover", "not grype json leftover; leftover grype sarif as dest", "ship leftover grype sarif as dest.", "grype sarif leftover; # grype.sarif on disk", "grype leftover|grype.sarif"),
    l_from(18, "syft-spdx-leftover-handoff", "sysp", "syft.spdx.json", "syft spdx leftover", "syft spdx leftover", "not syft json leftover; leftover syft spdx as dest", "ship leftover syft spdx as dest.", "syft spdx leftover; # syft.spdx.json on disk", "syft leftover|syft.spdx.json"),
    l_from(19, "osv-sarif-leftover-handoff", "ossf", "osv.sarif", "osv sarif leftover", "osv sarif leftover", "not osv json leftover; leftover osv sarif as dest", "ship leftover osv sarif as dest.", "osv sarif leftover; # osv.sarif on disk", "osv leftover|osv.sarif"),
    l_from(20, "gitleaks-sarif-leftover-handoff", "glsf", "gitleaks.sarif", "gitleaks sarif leftover", "gitleaks sarif leftover", "not gitleaks json leftover; leftover gitleaks sarif as dest", "ship leftover gitleaks sarif as dest.", "gitleaks sarif leftover; # gitleaks.sarif on disk", "gitleaks leftover|gitleaks.sarif"),
    l_from(21, "trufflehog-log-leftover-handoff", "thlg", "trufflehog.log", "trufflehog log leftover", "trufflehog log leftover", "not trufflehog json leftover; leftover trufflehog log as dest", "ship leftover trufflehog log as dest.", "trufflehog log leftover; # trufflehog.log on disk", "trufflehog leftover|trufflehog.log"),
    l_from(22, "detectsecrets-json-leftover-handoff", "dsjs", "detect-secrets.json", "detect-secrets json leftover", "detect-secrets json leftover", "not detect-secrets baseline leftover; leftover detect-secrets json as dest", "ship leftover detect-secrets json as dest.", "detect-secrets json leftover; # detect-secrets.json on disk", "detectsecrets leftover|detect-secrets.json"),
    l_from(23, "sonar-issues-leftover-handoff", "snis", "sonar-issues.json", "sonar issues leftover", "sonar issues leftover", "not sonar report leftover; leftover sonar issues as dest", "ship leftover sonar issues as dest.", "sonar issues leftover; # sonar-issues.json on disk", "sonar leftover|sonar-issues.json"),
    l_from(24, "codeql-bqrs-leftover-handoff", "cqbq", "codeql.bqrs", "codeql bqrs leftover", "codeql bqrs leftover", "not codeql sarif leftover; leftover codeql bqrs as dest", "ship leftover codeql bqrs as dest.", "codeql bqrs leftover; # codeql.bqrs on disk", "codeql leftover|codeql.bqrs"),
    l_from(25, "snyk-sarif-leftover-handoff", "snsf", "snyk.sarif", "snyk sarif leftover", "snyk sarif leftover", "not snyk json leftover; leftover snyk sarif as dest", "ship leftover snyk sarif as dest.", "snyk sarif leftover; # snyk.sarif on disk", "snyk leftover|snyk.sarif"),
    l_from(26, "hadolint-sarif-leftover-handoff", "hdsf", "hadolint.sarif", "hadolint sarif leftover", "hadolint sarif leftover", "not hadolint json leftover; leftover hadolint sarif as dest", "ship leftover hadolint sarif as dest.", "hadolint sarif leftover; # hadolint.sarif on disk", "hadolint leftover|hadolint.sarif"),
    l_from(27, "shellcheck-gcc-leftover-handoff", "scgc", "shellcheck.gcc", "shellcheck gcc leftover", "shellcheck gcc leftover", "not shellcheck json leftover; leftover shellcheck gcc as dest", "ship leftover shellcheck gcc as dest.", "shellcheck gcc leftover; # shellcheck.gcc on disk", "shellcheck leftover|shellcheck.gcc"),
    l_from(28, "yamllint-txt-leftover-handoff", "yltx", "yamllint.txt", "yamllint txt leftover", "yamllint txt leftover", "not yamllint json leftover; leftover yamllint txt as dest", "ship leftover yamllint txt as dest.", "yamllint txt leftover; # yamllint.txt on disk", "yamllint leftover|yamllint.txt"),
    l_from(29, "markdownlint-txt-leftover-handoff", "mdtx", "markdownlint.txt", "markdownlint txt leftover", "markdownlint txt leftover", "not markdownlint json leftover; leftover markdownlint txt as dest", "ship leftover markdownlint txt as dest.", "markdownlint txt leftover; # markdownlint.txt on disk", "markdownlint leftover|markdownlint.txt"),
    l_from(30, "stylelint-json-leftover-handoff", "stjs", "stylelint.json", "stylelint json leftover", "stylelint json leftover", "not stylelint cache leftover; leftover stylelint json as dest", "ship leftover stylelint json as dest.", "stylelint json leftover; # stylelint.json on disk", "stylelint leftover|stylelint.json"),
    l_from(31, "sqlfluff-txt-leftover-handoff", "sftx", "sqlfluff.txt", "sqlfluff txt leftover", "sqlfluff txt leftover", "not sqlfluff json leftover; leftover sqlfluff txt as dest", "ship leftover sqlfluff txt as dest.", "sqlfluff txt leftover; # sqlfluff.txt on disk", "sqlfluff leftover|sqlfluff.txt"),
]

mod2.SUCCESS = SUCCESS
mod2.LEFTOVER = LEFTOVER
mod2.BANNED_SLUGS = set(mod2.BANNED_SLUGS) | {
    "dnsmasq-hosts-leftover-as-dest",
    "dnsmasq-lease-leftover-handoff",
}
pair_for = mod2.pair_for
notes_for = mod2.notes_for
write_stage = mod2.write_stage


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2:
        print("usage: ntp-mill-unique-llll15.py ROUND STAGING_DIR", file=sys.stderr)
        return 2
    round_n = int(argv[0])
    staging = Path(argv[1])
    staging.mkdir(parents=True, exist_ok=True)
    i1, i2 = write_stage(staging, round_n)
    print(f"wrote r{round_n} {i1} {i2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
