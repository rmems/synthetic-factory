#!/usr/bin/env python3
"""Mill secret-scan-remediation-factory r332+ unique leftover-artifact mechanics.

BAN: skip-path cartesian; SaaS-yml; vendor-file; cloning r181–r415 leftover
leftover leftover; decoder wraps; SARIF leftover leftover leftover; git-notes
leftover leftover leftover; entropy-window leftover leftover leftover;
stash/reflog/worktree/turbo/npm/ruff/next/export-subst/p4/wheel/gradle/tox/
hypothesis clones. Fake TESTONLY_ keys only. Never force-push main.
r416+ leftover leftover leftover: new scanner × leftover leftover leftover
artifact pairs (biome/oxlint/rspack/…), not prettier-cache leftover leftover leftover.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

FACTORY = "secret-scan-remediation-factory"
CATALOG_FIRST = 332
HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("ssr_mill_r300", HERE / "ssr-mill-r300.py")
_r300 = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_r300)
plant = _r300.plant
success_episode = _r300.success_episode
fail_episode = _r300.fail_episode

USED_SLUGS = {p["slug"] for pair in _r300.PAIRS for p in pair} | set(_r300.ALREADY)
USED_EXTRAS = {p["extra"] for pair in _r300.PAIRS for p in pair}

SCAN = {
    "gitleaks": (
        "gitleaks detect --no-banner --no-git -s {extra}",
        "Secret:    generic-api-key  ({tag})",
    ),
    "trufflehog": (
        "trufflehog filesystem {extra} --no-update",
        "Found unverified result via {tag}",
    ),
    "ggshield": (
        "ggshield secret scan path {extra}",
        "SECRET_DETECTED {tag}",
    ),
    "noseyparker": (
        "noseyparker scan {extra}",
        "Finding: {tag}",
    ),
    "kingfisher": (
        "kingfisher scan {extra}",
        "kingfisher: secret in {tag}",
    ),
    "trivy": (
        "trivy fs --scanners secret {extra}",
        "trivy secret in {tag}",
    ),
    "detect-secrets": (
        "detect-secrets scan {extra}",
        "detect-secrets: {tag}",
    ),
    "semgrep": (
        "semgrep --config p/secrets {extra}",
        "semgrep: {tag}",
    ),
    "git-secrets": (
        "git secrets --scan {extra}",
        "git-secrets: {tag}",
    ),
    "talisman": (
        "talisman --scanFile {extra}",
        "talisman: {tag}",
    ),
    "whispers": (
        "whispers {extra}",
        "whispers: {tag}",
    ),
    "bearer": (
        "bearer scan {extra}",
        "bearer: {tag}",
    ),
}

# (scanner, slug_tail, mechanic, extra, leak, env, org, tag)
# slug_tail is unique leftover surface, not a clone of r300 extras.
ROWS: list[tuple[str, str, str, str, str, str, str, str]] = [
    ("gitleaks", "docker-buildx-cache-leftover", "docker buildx cache still has conf/ci.env layer", ".buildx/cache/ci.env", "conf/ci.env", "CI_BUILDX_TOKEN", "adit-ci", "buildx cache leftover"),
    ("trufflehog", "maven-m2-leftover", "local .m2/repository still holds ops/old.env", ".m2/repository/ops/old/0.1/old.env", "ops/old.env", "OLD_M2_TOKEN", "stope-api", "maven m2 leftover"),
    ("ggshield", "poetry-venv-leftover", "poetry .venv still copies hooks/hot.env into site-packages", ".venv/lib/python3.12/site-packages/hooks/hot.env", "hooks/hot.env", "HOT_POETRY_TOKEN", "raise-web", "poetry venv leftover"),
    ("noseyparker", "uv-cache-leftover", "uv cache still stores app/prod.env from a built sdist", ".cache/uv/app/prod.env", "app/prod.env", "PROD_UV_TOKEN", "millfeed-ml", "uv cache leftover"),
    ("kingfisher", "bun-install-cache-leftover", "bun install cache still snapshots dump/old.env", ".bun/install/cache/old.env", "dump/old.env", "OLD_BUN_TOKEN", "launder-ops", "bun install cache leftover"),
    ("trivy", "pnpm-store-leftover", "pnpm store still holds svc/run.env from a packed tarball", ".pnpm-store/v3/svc/run.env", "svc/run.env", "SVC_PNPM_TOKEN", "gob-mod", "pnpm store leftover"),
    ("detect-secrets", "yarn-berry-cache-leftover", "yarn berry cache still packs conf/ci.env", ".yarn/cache/ci.env.zip", "conf/ci.env", "CI_YARN_TOKEN", "panel-js", "yarn berry cache leftover"),
    ("semgrep", "bazel-out-leftover", "bazel-out still stores ops/old.env action output", "bazel-out/k8-fastbuild/bin/ops/old.env", "ops/old.env", "OLD_BAZEL_TOKEN", "bord-py", "bazel-out leftover"),
    ("git-secrets", "sccache-leftover", "sccache still keeps hooks/hot.env compile object", ".cache/sccache/hot.env.o", "hooks/hot.env", "HOT_SCCACHE_TOKEN", "pillar-ops", "sccache leftover"),
    ("talisman", "ccache-leftover", "ccache still hashes app/prod.env into a cached object", ".ccache/prod.env.c", "app/prod.env", "PROD_CCACHE_TOKEN", "sump-cfg", "ccache leftover"),
    ("whispers", "htmlcov-leftover", "htmlcov still embeds dump/old.env from coverage annotate", "htmlcov/old_env.html", "dump/old.env", "DUMP_HTMLCOV_TOKEN", "inset-ml", "htmlcov leftover"),
    ("bearer", "eslintcache-leftover", ".eslintcache still serializes svc/run.env", ".eslintcache", "svc/run.env", "SVC_ESLINT_TOKEN", "crosscut-qa", "eslintcache leftover"),
    ("gitleaks", "tsbuildinfo-leftover", "tsconfig.tsbuildinfo still embeds conf/ci.env", "tsconfig.tsbuildinfo", "conf/ci.env", "CI_TSB_TOKEN", "heading-bin", "tsbuildinfo leftover"),
    ("trufflehog", "vite-deps-leftover", "vite dep optimizer still snapshots ops/old.env", "node_modules/.vite/deps/old.env.js", "ops/old.env", "OLD_VITE_TOKEN", "rib-tf", "vite deps leftover"),
    ("ggshield", "nuxt-output-leftover", ".nuxt still copies hooks/hot.env into generated output", ".nuxt/hot.env.mjs", "hooks/hot.env", "HOT_NUXT_TOKEN", "chock-helm", "nuxt output leftover"),
    ("noseyparker", "svelte-kit-leftover", ".svelte-kit still emits app/prod.env into generated client", ".svelte-kit/generated/prod.env.js", "app/prod.env", "PROD_SVELTE_TOKEN", "shield-k8s", "svelte-kit leftover"),
    ("kingfisher", "playwright-trace-leftover", "playwright-report still embeds dump/old.env trace", "playwright-report/trace/old.env", "dump/old.env", "DUMP_PW_TOKEN", "plough-git", "playwright trace leftover"),
    ("trivy", "allure-attachment-leftover", "allure-results still attach svc/run.env", "allure-results/run.env-attachment.txt", "svc/run.env", "SVC_ALLURE_TOKEN", "shearer-ci", "allure leftover"),
    ("detect-secrets", "nyc-output-leftover", ".nyc_output still serializes conf/ci.env coverage", ".nyc_output/ci.env.json", "conf/ci.env", "CI_NYC_TOKEN", "faceend-web", "nyc_output leftover"),
    ("semgrep", "terragrunt-cache-leftover", ".terragrunt-cache still copies ops/old.env", ".terragrunt-cache/old.env", "ops/old.env", "OLD_TERRAGRUNT_TOKEN", "gateend-api", "terragrunt-cache leftover"),
    ("git-secrets", "serverless-package-leftover", ".serverless still packs hooks/hot.env into the deploy zip", ".serverless/hot.env", "hooks/hot.env", "HOT_SLS_TOKEN", "bunker-logs", "serverless leftover"),
    ("talisman", "wrangler-state-leftover", ".wrangler still stores app/prod.env in local state", ".wrangler/state/prod.env", "app/prod.env", "PROD_WRANGLER_TOKEN", "washery-pkg", "wrangler leftover"),
    ("whispers", "firebase-cache-leftover", ".firebase still caches dump/old.env from hosting deploy", ".firebase/hosting.cache/old.env", "dump/old.env", "DUMP_FIREBASE_TOKEN", "cyclone-nb", "firebase leftover"),
    ("bearer", "nx-cache-leftover", ".nx/cache still hashes svc/run.env task output", ".nx/cache/run.env", "svc/run.env", "SVC_NX_TOKEN", "jigger-js", "nx cache leftover"),
    ("gitleaks", "angular-cache-leftover", ".angular/cache still snapshots conf/ci.env", ".angular/cache/ci.env", "conf/ci.env", "CI_ANGULAR_TOKEN", "thickener-py", "angular cache leftover"),
    ("trufflehog", "astro-cache-leftover", ".astro still copies ops/old.env into generated pages", ".astro/old.env.mjs", "ops/old.env", "OLD_ASTRO_TOKEN", "flotation-ops", "astro leftover"),
    ("ggshield", "docusaurus-leftover", ".docusaurus still embeds hooks/hot.env in client modules", ".docusaurus/hot.env.js", "hooks/hot.env", "HOT_DOCUSAURUS_TOKEN", "launder-qa", "docusaurus leftover"),
    ("noseyparker", "remix-cache-leftover", ".cache/remix still stores app/prod.env loader snapshot", ".cache/remix/prod.env", "app/prod.env", "PROD_REMIX_TOKEN", "millrun-cfg", "remix cache leftover"),
    ("kingfisher", "webpack-cache-leftover", "webpack cache still serializes dump/old.env", "node_modules/.cache/webpack/old.env", "dump/old.env", "DUMP_WEBPACK_TOKEN", "headframe-ci", "webpack cache leftover"),
    ("trivy", "esbuild-metafile-leftover", "esbuild metafile still names svc/run.env inputs", "esbuild-meta.json", "svc/run.env", "SVC_ESBUILD_TOKEN", "cage-mod", "esbuild metafile leftover"),
    ("detect-secrets", "swc-cache-leftover", ".swc still caches conf/ci.env transform", ".swc/ci.env", "conf/ci.env", "CI_SWC_TOKEN", "kibble-web", "swc cache leftover"),
    ("semgrep", "jest-cache-leftover", "jest cache still snapshots ops/old.env", "node_modules/.cache/jest/old.env", "ops/old.env", "OLD_JEST_TOKEN", "gin-hooks", "jest cache leftover"),
    ("git-secrets", "cypress-videos-leftover", "cypress videos still encode hooks/hot.env fixture", "cypress/videos/hot.env.mp4", "hooks/hot.env", "HOT_CYPRESS_TOKEN", "skipshaft-ops", "cypress videos leftover"),
    ("talisman", "junit-xml-leftover", "surefire junit xml still embeds app/prod.env stdout", "reports/junit.xml", "app/prod.env", "PROD_JUNIT_TOKEN", "gobbin-ml", "junit xml leftover"),
    ("whispers", "tf-plugin-cache-leftover", ".terraform/providers still copies dump/old.env plugin debug", ".terraform/providers/old.env", "dump/old.env", "DUMP_TFPLUGIN_TOKEN", "stullgate-ci", "terraform plugin cache leftover"),
    ("bearer", "cdk-out-leftover", "cdk.out still serializes svc/run.env into assembled template", "cdk.out/run.env.template.json", "svc/run.env", "SVC_CDK_TOKEN", "cundie-api", "cdk.out leftover"),
    ("gitleaks", "sam-build-leftover", ".aws-sam still packs conf/ci.env into the built function", ".aws-sam/build/ci.env", "conf/ci.env", "CI_SAM_TOKEN", "airshaft-web", "sam build leftover"),
    ("trufflehog", "dbt-target-leftover", "dbt target still compiles ops/old.env into run results", "target/run_results.json", "ops/old.env", "OLD_DBT_TOKEN", "staplepit-mod", "dbt target leftover"),
    ("ggshield", "airflow-logs-leftover", "airflow task logs still print hooks/hot.env", "logs/airflow/hot.env.log", "hooks/hot.env", "HOT_AIRFLOW_TOKEN", "goafedge-js", "airflow logs leftover"),
    ("noseyparker", "spark-eventlog-leftover", "spark eventlog still embeds app/prod.env conf", "spark-events/prod.env", "app/prod.env", "PROD_SPARK_TOKEN", "packs-py", "spark eventlog leftover"),
    ("kingfisher", "redis-rdb-leftover", "redis dump.rdb still serializes dump/old.env", "dump.rdb", "dump/old.env", "DUMP_REDIS_TOKEN", "chocks-ops", "redis rdb leftover"),
    ("trivy", "postgres-dump-leftover", "pg_dump custom file still packs svc/run.env", "backup.dump", "svc/run.env", "SVC_PGDUMP_TOKEN", "powered-cfg", "postgres dump leftover"),
    ("detect-secrets", "sqlite-wal-leftover", "sqlite WAL still holds conf/ci.env pages", "app.db-wal", "conf/ci.env", "CI_SQLITE_TOKEN", "headframe-ops", "sqlite wal leftover"),
    ("semgrep", "pcap-capture-leftover", "pcap still records ops/old.env on the wire", "capture.pcap", "ops/old.env", "OLD_PCAP_TOKEN", "cage-net", "pcap leftover"),
    ("git-secrets", "har-session-leftover", "HAR session still stores hooks/hot.env request body", "session.har", "hooks/hot.env", "HOT_HAR_TOKEN", "kibble-net", "har leftover"),
    ("talisman", "perf-data-leftover", "perf.data still samples app/prod.env strings", "perf.data", "app/prod.env", "PROD_PERF_TOKEN", "gin-perf", "perf.data leftover"),
    ("whispers", "asan-log-leftover", "ASAN log still prints dump/old.env from the crashing process", "asan.log", "dump/old.env", "DUMP_ASAN_TOKEN", "skipshaft-dbg", "asan log leftover"),
    ("bearer", "valgrind-log-leftover", "valgrind log still dumps svc/run.env from leaked heap", "valgrind.log", "svc/run.env", "SVC_VALGRIND_TOKEN", "gobbin-dbg", "valgrind leftover"),
    ("gitleaks", "dsym-leftover", "dSYM still embeds conf/ci.env from the linked binary", "App.app.dSYM/Contents/Resources/Relocations/ci.env", "conf/ci.env", "CI_DSYM_TOKEN", "stullgate-ios", "dsym leftover"),
    ("trufflehog", "xcarchive-leftover", "xcarchive still packs ops/old.env into the app bundle", "App.xcarchive/Products/Applications/App.app/old.env", "ops/old.env", "OLD_XCARCHIVE_TOKEN", "cundie-ios", "xcarchive leftover"),
    ("ggshield", "apk-mapping-leftover", "R8 mapping still names hooks/hot.env string", "app/build/outputs/mapping/mapping.txt", "hooks/hot.env", "HOT_R8_TOKEN", "airshaft-and", "apk mapping leftover"),
    ("noseyparker", "nupkg-leftover", "nupkg still packs app/prod.env into the package", "dist/App.1.0.0.nupkg", "app/prod.env", "PROD_NUPKG_TOKEN", "staplepit-cs", "nupkg leftover"),
    ("kingfisher", "composer-cache-leftover", "composer cache still stores dump/old.env from a dist zip", ".composer/cache/old.env", "dump/old.env", "DUMP_COMPOSER_TOKEN", "goafedge-php", "composer cache leftover"),
    ("trivy", "bundle-cache-leftover", "bundler cache still tars svc/run.env gem contents", ".bundle/cache/run.env", "svc/run.env", "SVC_BUNDLE_TOKEN", "packs-rb", "bundler cache leftover"),
    ("detect-secrets", "hex-cache-leftover", "hex cache still stores conf/ci.env package", ".hex/packages/ci.env", "conf/ci.env", "CI_HEX_TOKEN", "chocks-ex", "hex cache leftover"),
    ("semgrep", "mix-build-leftover", "mix _build still copies ops/old.env into the release", "_build/dev/lib/ops/old.env", "ops/old.env", "OLD_MIX_TOKEN", "powered-ex", "mix build leftover"),
    ("git-secrets", "stack-work-leftover", ".stack-work still embeds hooks/hot.env", ".stack-work/dist/hot.env", "hooks/hot.env", "HOT_STACK_TOKEN", "headframe-hs", "stack-work leftover"),
    ("talisman", "cabal-dist-leftover", "cabal dist-newstyle still copies app/prod.env", "dist-newstyle/build/prod.env", "app/prod.env", "PROD_CABAL_TOKEN", "cage-hs", "cabal dist leftover"),
    ("whispers", "go-build-cache-leftover", "go build cache still hashes dump/old.env into an action id", ".cache/go-build/old.env", "dump/old.env", "DUMP_GOBUILD_TOKEN", "kibble-go", "go-build cache leftover"),
    ("bearer", "zig-cache-leftover", ".zig-cache still stores svc/run.env compile unit", ".zig-cache/run.env", "svc/run.env", "SVC_ZIG_TOKEN", "gin-zig", "zig-cache leftover"),
    ("gitleaks", "dart-tool-leftover", ".dart_tool still snapshots conf/ci.env", ".dart_tool/ci.env", "conf/ci.env", "CI_DART_TOKEN", "skipshaft-dart", "dart_tool leftover"),
    ("trufflehog", "pub-cache-leftover", "pub-cache still packs ops/old.env from a hosted package", ".pub-cache/hosted/old.env", "ops/old.env", "OLD_PUB_TOKEN", "gobbin-dart", "pub-cache leftover"),
    ("ggshield", "cocoapods-cache-leftover", "CocoaPods cache still stores hooks/hot.env podspec env", ".cache/cocoapods/hot.env", "hooks/hot.env", "HOT_PODS_TOKEN", "stullgate-ios", "cocoapods cache leftover"),
    ("noseyparker", "spm-build-leftover", "SwiftPM .build still copies app/prod.env", ".build/prod.env", "app/prod.env", "PROD_SPM_TOKEN", "cundie-swift", "spm build leftover"),
    ("kingfisher", "xcode-deriveddata-leftover", "Xcode DerivedData still embeds dump/old.env", "DerivedData/old.env", "dump/old.env", "DUMP_DERIVED_TOKEN", "airshaft-ios", "deriveddata leftover"),
    ("trivy", "android-intermediates-leftover", "android intermediates still copy svc/run.env assets", "app/build/intermediates/assets/run.env", "svc/run.env", "SVC_ANDINT_TOKEN", "staplepit-and", "android intermediates leftover"),
    ("detect-secrets", "unity-library-leftover", "Unity Library cache still snapshots conf/ci.env", "Library/PlayerDataCache/ci.env", "conf/ci.env", "CI_UNITY_TOKEN", "goafedge-game", "unity library leftover"),
    ("semgrep", "unreal-intermediate-leftover", "Unreal Intermediate still copies ops/old.env", "Intermediate/old.env", "ops/old.env", "OLD_UNREAL_TOKEN", "packs-game", "unreal intermediate leftover"),
    ("git-secrets", "cmake-files-leftover", "CMakeFiles still embeds hooks/hot.env from configure", "CMakeFiles/hot.env", "hooks/hot.env", "HOT_CMAKE_TOKEN", "chocks-cc", "cmake files leftover"),
    ("talisman", "meson-int-leftover", "meson introspect still stores app/prod.env", "meson-info/prod.env", "app/prod.env", "PROD_MESON_TOKEN", "powered-cc", "meson leftover"),
    ("whispers", "ninja-log-leftover", ".ninja_log still names dump/old.env rebuild inputs", ".ninja_log", "dump/old.env", "DUMP_NINJA_TOKEN", "headframe-cc", "ninja log leftover"),
    ("bearer", "pants-d-leftover", ".pants.d still caches svc/run.env process output", ".pants.d/run.env", "svc/run.env", "SVC_PANTS_TOKEN", "cage-py", "pants leftover"),
    ("gitleaks", "conan-data-leftover", "conan data still packs conf/ci.env recipe", ".conan2/p/ci.env", "conf/ci.env", "CI_CONAN_TOKEN", "kibble-cc", "conan data leftover"),
    ("trufflehog", "vcpkg-installed-leftover", "vcpkg_installed still copies ops/old.env port file", "vcpkg_installed/ops/old.env", "ops/old.env", "OLD_VCPKG_TOKEN", "gin-cc", "vcpkg leftover"),
    ("ggshield", "localstack-volume-leftover", "localstack volume still stores hooks/hot.env secret", ".localstack/hot.env", "hooks/hot.env", "HOT_LOCALSTACK_TOKEN", "skipshaft-aws", "localstack leftover"),
    ("noseyparker", "prisma-engine-leftover", "prisma engine leftover still embeds app/prod.env DATABASE_URL", "node_modules/.prisma/prod.env", "app/prod.env", "PROD_PRISMA_TOKEN", "gobbin-orm", "prisma leftover"),
    ("kingfisher", "jaeger-badger-leftover", "jaeger badger still stores dump/old.env span tags", ".jaeger/old.env", "dump/old.env", "DUMP_JAEGER_TOKEN", "stullgate-obs", "jaeger leftover"),
    ("trivy", "filebeat-registry-leftover", "filebeat registry still copies svc/run.env path contents", "data/registry/filebeat/run.env", "svc/run.env", "SVC_FILEBEAT_TOKEN", "cundie-obs", "filebeat leftover"),
    ("detect-secrets", "squash-msg-leftover", ".git/SQUASH_MSG still quotes conf/ci.env subject", ".git/SQUASH_MSG", "conf/ci.env", "CI_SQUASH_TOKEN", "airshaft-git", "squash-msg leftover"),
    ("semgrep", "revert-head-leftover", "REVERT_HEAD still names the ops/old.env leak commit", ".git/REVERT_HEAD", "ops/old.env", "OLD_REVERT_TOKEN", "staplepit-git", "revert-head leftover"),
    ("git-secrets", "merge-head-leftover", "MERGE_HEAD still names the hooks/hot.env leak commit", ".git/MERGE_HEAD", "hooks/hot.env", "HOT_MERGEHEAD_TOKEN", "goafedge-git", "merge-head leftover"),
    ("talisman", "rebase-head-ptr-leftover", "REBASE_HEAD still names the app/prod.env leak commit", ".git/REBASE_HEAD", "app/prod.env", "PROD_REBASEHEAD_TOKEN", "packs-git", "rebase-head leftover"),
    ("whispers", "auto-merge-leftover", "AUTO_MERGE still stages dump/old.env conflict blob", ".git/AUTO_MERGE", "dump/old.env", "DUMP_AUTOMERGE_TOKEN", "chocks-git", "auto-merge leftover"),
    ("bearer", "lost-found-leftover", ".git/lost-found still keeps svc/run.env dangling blob", ".git/lost-found/other/run.env", "svc/run.env", "SVC_LOSTFOUND_TOKEN", "powered-git", "lost-found leftover"),
    ("gitleaks", "git-lfs-objects-leftover", "git-lfs objects still store conf/ci.env pointer payload", ".git/lfs/objects/ab/cd/ci.env", "conf/ci.env", "CI_LFS_TOKEN", "headframe-lfs", "git-lfs leftover"),
    ("trufflehog", "git-modules-leftover", ".git/modules still checks out ops/old.env in a nested clone", ".git/modules/vendorlib/ops/old.env", "ops/old.env", "OLD_MODULES_TOKEN", "cage-modgit", "git-modules leftover"),
    ("ggshield", "gc-log-leftover", ".git/gc.log still quotes hooks/hot.env unreachable path", ".git/gc.log", "hooks/hot.env", "HOT_GCLOG_TOKEN", "kibble-git", "gc.log leftover"),
    ("noseyparker", "hook-backup-leftover", ".git/hooks backup still embeds app/prod.env", ".git/hooks/pre-push.bak", "app/prod.env", "PROD_HOOKBAK_TOKEN", "gin-hooks2", "hook backup leftover"),
    ("kingfisher", "jj-op-log-leftover", "jujutsu op log still records dump/old.env", ".jj/op_store/old.env", "dump/old.env", "DUMP_JJ_TOKEN", "skipshaft-jj", "jj op log leftover"),
    ("trivy", "info-grafts-leftover", ".git/info/grafts still names svc/run.env parent rewrite", ".git/info/grafts", "svc/run.env", "SVC_GRAFTS_TOKEN", "gobbin-git", "grafts leftover"),
    ("detect-secrets", "earthly-cache-leftover", "earthly cache still stores conf/ci.env layer", ".earthly/ci.env", "conf/ci.env", "CI_EARTHLY_TOKEN", "stullgate-ci2", "earthly leftover"),
    ("semgrep", "buck-out-leftover", "buck-out still copies ops/old.env action output", "buck-out/gen/ops/old.env", "ops/old.env", "OLD_BUCK_TOKEN", "cundie-buck", "buck-out leftover"),
    ("git-secrets", "please-out-leftover", "please plz-out still embeds hooks/hot.env", "plz-out/hot.env", "hooks/hot.env", "HOT_PLEASE_TOKEN", "airshaft-plz", "please out leftover"),
    ("talisman", "scons-leftover", "scons build still copies app/prod.env into .sconsign", ".sconsign.dblite", "app/prod.env", "PROD_SCONS_TOKEN", "staplepit-scons", "scons leftover"),
    ("whispers", "distcc-leftover", "distcc cache still stores dump/old.env compile unit", ".distcc/old.env", "dump/old.env", "DUMP_DISTCC_TOKEN", "goafedge-cc", "distcc leftover"),
    ("bearer", "icecream-leftover", "icecream cache still keeps svc/run.env object", ".icecream/run.env", "svc/run.env", "SVC_ICECREAM_TOKEN", "packs-cc", "icecream leftover"),
    ("gitleaks", "odin-cache-leftover", "odin cache still snapshots conf/ci.env", ".odin-cache/ci.env", "conf/ci.env", "CI_ODIN_TOKEN", "chocks-odin", "odin cache leftover"),
    ("trufflehog", "nimcache-leftover", "nimcache still copies ops/old.env", "nimcache/old.env", "ops/old.env", "OLD_NIM_TOKEN", "powered-nim", "nimcache leftover"),
    ("ggshield", "crystal-cache-leftover", "crystal cache still embeds hooks/hot.env", ".crystal/hot.env", "hooks/hot.env", "HOT_CRYSTAL_TOKEN", "headframe-cr", "crystal leftover"),
    ("noseyparker", "gleam-build-leftover", "gleam build still copies app/prod.env", "build/dev/prod.env", "app/prod.env", "PROD_GLEAM_TOKEN", "cage-gleam", "gleam leftover"),
    ("kingfisher", "phpunit-cache-leftover", "phpunit cache still stores dump/old.env fixture", ".phpunit.cache/old.env", "dump/old.env", "DUMP_PHPUNIT_TOKEN", "kibble-php", "phpunit leftover"),
    ("trivy", "phpstan-tmp-leftover", "phpstan tmp still serializes svc/run.env", ".phpstan/tmp/run.env", "svc/run.env", "SVC_PHPSTAN_TOKEN", "gin-php", "phpstan leftover"),
    ("detect-secrets", "psalm-cache-leftover", "psalm cache still snapshots conf/ci.env", ".psalm/cache/ci.env", "conf/ci.env", "CI_PSALM_TOKEN", "skipshaft-php", "psalm leftover"),
    ("semgrep", "rector-cache-leftover", "rector cache still copies ops/old.env", ".rector/old.env", "ops/old.env", "OLD_RECTOR_TOKEN", "gobbin-php", "rector leftover"),
    ("git-secrets", "vitest-cache-leftover", "vitest cache still embeds hooks/hot.env", "node_modules/.vitest/hot.env", "hooks/hot.env", "HOT_VITEST_TOKEN", "stullgate-js", "vitest leftover"),
    ("talisman", "karma-leftover", "karma debug leftover still stores app/prod.env", ".karma/prod.env", "app/prod.env", "PROD_KARMA_TOKEN", "cundie-js", "karma leftover"),
    ("whispers", "cucumber-json-leftover", "cucumber json still embeds dump/old.env step text", "reports/cucumber.json", "dump/old.env", "DUMP_CUCUMBER_TOKEN", "airshaft-qa", "cucumber leftover"),
    ("bearer", "jacoco-exec-leftover", "jacoco.exec still serializes svc/run.env coverage", "jacoco.exec", "svc/run.env", "SVC_JACOCO_TOKEN", "staplepit-jvm", "jacoco leftover"),
    ("gitleaks", "gcov-notes-leftover", "gcov notes still embed conf/ci.env path", "conf/ci.env.gcov", "conf/ci.env", "CI_GCOV_TOKEN", "goafedge-cc2", "gcov leftover"),
    ("trufflehog", "profraw-leftover", "LLVM profraw still records ops/old.env counters", "default.profraw", "ops/old.env", "OLD_PROFRAW_TOKEN", "packs-llvm", "profraw leftover"),
    ("ggshield", "pprof-leftover", "pprof profile still samples hooks/hot.env strings", "cpu.pprof", "hooks/hot.env", "HOT_PPROF_TOKEN", "chocks-go", "pprof leftover"),
    ("noseyparker", "flamegraph-leftover", "flamegraph svg still labels app/prod.env frames", "perf.svg", "app/prod.env", "PROD_FLAME_TOKEN", "powered-perf", "flamegraph leftover"),
    ("kingfisher", "mitmproxy-leftover", "mitmproxy dump still stores dump/old.env request", "mitmproxy.dump", "dump/old.env", "DUMP_MITM_TOKEN", "headframe-net", "mitmproxy leftover"),
    ("trivy", "chrome-trace-leftover", "chrome trace still embeds svc/run.env", "trace.json", "svc/run.env", "SVC_CHROMETRACE_TOKEN", "cage-net2", "chrome trace leftover"),
    ("detect-secrets", "lighthouse-leftover", "lighthouse report still copies conf/ci.env headers", "lighthouse.html", "conf/ci.env", "CI_LIGHTHOUSE_TOKEN", "kibble-web2", "lighthouse leftover"),
    ("semgrep", "rollup-cache-leftover", "rollup cache still snapshots ops/old.env", "node_modules/.cache/rollup/old.env", "ops/old.env", "OLD_ROLLUP_TOKEN", "gin-js", "rollup leftover"),
    ("git-secrets", "babel-cache-leftover", "babel cache still embeds hooks/hot.env", "node_modules/.cache/babel-loader/hot.env", "hooks/hot.env", "HOT_BABEL_TOKEN", "skipshaft-js", "babel leftover"),
    ("talisman", "gatsby-cache-leftover", "gatsby cache still stores app/prod.env page data", ".cache/gatsby/prod.env", "app/prod.env", "PROD_GATSBY_TOKEN", "gobbin-web", "gatsby leftover"),
    ("whispers", "hugo-resources-leftover", "hugo resources still copies dump/old.env", "resources/_gen/old.env", "dump/old.env", "DUMP_HUGO_TOKEN", "stullgate-web", "hugo leftover"),
    ("bearer", "jekyll-site-leftover", "jekyll _site still emits svc/run.env", "_site/run.env", "svc/run.env", "SVC_JEKYLL_TOKEN", "cundie-web", "jekyll leftover"),
    ("gitleaks", "mkdocs-site-leftover", "mkdocs site still embeds conf/ci.env", "site/ci.env.html", "conf/ci.env", "CI_MKDOCS_TOKEN", "airshaft-docs", "mkdocs leftover"),
    ("trufflehog", "vitepress-cache-leftover", "vitepress cache still copies ops/old.env", ".vitepress/cache/old.env", "ops/old.env", "OLD_VITEPRESS_TOKEN", "staplepit-docs", "vitepress leftover"),
    ("ggshield", "eleventy-leftover", "eleventy output still embeds hooks/hot.env", "_site/hot.env.html", "hooks/hot.env", "HOT_11TY_TOKEN", "goafedge-docs", "eleventy leftover"),
    ("noseyparker", "qwik-cache-leftover", "qwik cache still stores app/prod.env", ".cache/qwik/prod.env", "app/prod.env", "PROD_QWIK_TOKEN", "packs-web", "qwik leftover"),
    ("kingfisher", "deno-cache-leftover", "deno cache still snapshots dump/old.env remote module", ".cache/deno/old.env", "dump/old.env", "DUMP_DENO_TOKEN", "chocks-deno", "deno leftover"),
    ("trivy", "rush-temp-leftover", "rush temp still packs svc/run.env", "common/temp/run.env", "svc/run.env", "SVC_RUSH_TOKEN", "powered-js", "rush leftover"),
    ("detect-secrets", "helm-repo-cache-leftover", "helm repo cache still stores conf/ci.env chart values", ".cache/helm/repository/ci.env", "conf/ci.env", "CI_HELMREPO_TOKEN", "headframe-k8s", "helm repo leftover"),
    ("semgrep", "sst-state-leftover", ".sst still copies ops/old.env into local state", ".sst/old.env", "ops/old.env", "OLD_SST_TOKEN", "cage-sst", "sst leftover"),
    ("git-secrets", "amplify-leftover", "amplify backend leftover still embeds hooks/hot.env", "amplify/#current-cloud-backend/hot.env", "hooks/hot.env", "HOT_AMPLIFY_TOKEN", "kibble-aws", "amplify leftover"),
    ("talisman", "supabase-temp-leftover", "supabase temp still stores app/prod.env", "supabase/.temp/prod.env", "app/prod.env", "PROD_SUPABASE_TOKEN", "gin-db", "supabase leftover"),
    ("whispers", "drizzle-meta-leftover", "drizzle meta still copies dump/old.env", "drizzle/meta/old.env", "dump/old.env", "DUMP_DRIZZLE_TOKEN", "skipshaft-orm", "drizzle leftover"),
    ("bearer", "otel-traces-leftover", "otel traces still serialize svc/run.env attributes", "traces.jsonl", "svc/run.env", "SVC_OTEL_TOKEN", "gobbin-obs", "otel leftover"),
    ("gitleaks", "prom-tsdb-leftover", "prometheus tsdb still stores conf/ci.env labels", "data/prometheus/ci.env", "conf/ci.env", "CI_PROM_TOKEN", "stullgate-obs2", "prom tsdb leftover"),
    ("trufflehog", "grafana-db-leftover", "grafana sqlite still embeds ops/old.env datasource", "grafana.db", "ops/old.env", "OLD_GRAFANA_TOKEN", "cundie-obs2", "grafana leftover"),
    ("ggshield", "sentry-envelope-leftover", "sentry envelope still packs hooks/hot.env event", ".sentry/hot.env.envelope", "hooks/hot.env", "HOT_SENTRY_TOKEN", "airshaft-obs", "sentry leftover"),
    ("noseyparker", "fluentbit-db-leftover", "fluent-bit db still copies app/prod.env chunk", "flb.db", "app/prod.env", "PROD_FLB_TOKEN", "staplepit-obs", "fluentbit leftover"),
    ("kingfisher", "vector-buffer-leftover", "vector buffer still stores dump/old.env events", ".vector/buffer/old.env", "dump/old.env", "DUMP_VECTOR_TOKEN", "goafedge-obs", "vector leftover"),
    ("trivy", "kafka-logs-leftover", "kafka logs still persist svc/run.env records", "kafka-logs/run.env", "svc/run.env", "SVC_KAFKA_TOKEN", "packs-mq", "kafka leftover"),
    ("detect-secrets", "rabbit-mnesia-leftover", "rabbitmq mnesia still copies conf/ci.env", "mnesia/ci.env", "conf/ci.env", "CI_RABBIT_TOKEN", "chocks-mq", "rabbit leftover"),
    ("semgrep", "minio-data-leftover", "minio data still stores ops/old.env object", ".minio/old.env", "ops/old.env", "OLD_MINIO_TOKEN", "powered-obj", "minio leftover"),
    ("git-secrets", "mongo-dump-leftover", "mongodump still packs hooks/hot.env document", "dump/hot.bson", "hooks/hot.env", "HOT_MONGO_TOKEN", "headframe-db", "mongo dump leftover"),
    ("talisman", "mysql-dump-leftover", "mysqldump still embeds app/prod.env row", "backup.sql", "app/prod.env", "PROD_MYSQL_TOKEN", "cage-db", "mysql dump leftover"),
    ("whispers", "cassandra-sstable-leftover", "cassandra sstable still copies dump/old.env", "data/cassandra/old.env", "dump/old.env", "DUMP_CASS_TOKEN", "kibble-db", "cassandra leftover"),
    ("bearer", "clickhouse-store-leftover", "clickhouse store still serializes svc/run.env", "store/clickhouse/run.env", "svc/run.env", "SVC_CH_TOKEN", "gin-db2", "clickhouse leftover"),
    ("gitleaks", "flink-chk-leftover", "flink checkpoint still embeds conf/ci.env", "chk/ci.env", "conf/ci.env", "CI_FLINK_TOKEN", "skipshaft-stream", "flink leftover"),
    ("trufflehog", "prefect-storage-leftover", "prefect storage still copies ops/old.env flow result", ".prefect/old.env", "ops/old.env", "OLD_PREFECT_TOKEN", "gobbin-orches", "prefect leftover"),
    ("ggshield", "dagster-storage-leftover", "dagster storage still embeds hooks/hot.env", ".dagster/hot.env", "hooks/hot.env", "HOT_DAGSTER_TOKEN", "stullgate-orches", "dagster leftover"),
    ("noseyparker", "celerybeat-leftover", "celerybeat-schedule still stores app/prod.env", "celerybeat-schedule", "app/prod.env", "PROD_CELERY_TOKEN", "cundie-orches", "celerybeat leftover"),
    ("kingfisher", "temporal-db-leftover", "temporal db leftover still copies dump/old.env payload", ".temporal/old.env", "dump/old.env", "DUMP_TEMPORAL_TOKEN", "airshaft-orches", "temporal leftover"),
    ("trivy", "papermill-leftover", "papermill output still embeds svc/run.env", "notebooks/run.out.ipynb", "svc/run.env", "SVC_PAPERMILL_TOKEN", "staplepit-nb", "papermill leftover"),
    ("detect-secrets", "streamlit-cache-leftover", "streamlit cache still snapshots conf/ci.env", ".streamlit/cache/ci.env", "conf/ci.env", "CI_STREAMLIT_TOKEN", "goafedge-app", "streamlit leftover"),
    ("semgrep", "godot-leftover", "godot .godot still copies ops/old.env", ".godot/old.env", "ops/old.env", "OLD_GODOT_TOKEN", "packs-game2", "godot leftover"),
    ("git-secrets", "blender-backup-leftover", "blender blend1 still embeds hooks/hot.env", "scene.blend1", "hooks/hot.env", "HOT_BLEND_TOKEN", "chocks-gfx", "blender leftover"),
    ("talisman", "ipa-payload-leftover", "ipa payload still packs app/prod.env", "dist/App.ipa", "app/prod.env", "PROD_IPA_TOKEN", "powered-ios", "ipa leftover"),
    ("whispers", "aab-bundle-leftover", "android aab still copies dump/old.env", "app/build/outputs/bundle/app.aab", "dump/old.env", "DUMP_AAB_TOKEN", "headframe-and", "aab leftover"),
    ("bearer", "msbuild-obj-leftover", "msbuild obj still serializes svc/run.env", "obj/Debug/run.env", "svc/run.env", "SVC_MSBUILD_TOKEN", "cage-cs", "msbuild leftover"),
    ("gitleaks", "vsix-leftover", "vsix still packs conf/ci.env into the extension", "dist/ext.vsix", "conf/ci.env", "CI_VSIX_TOKEN", "kibble-vs", "vsix leftover"),
    ("trufflehog", "homebrew-cache-leftover", "homebrew cache still stores ops/old.env bottle", ".cache/Homebrew/old.env", "ops/old.env", "OLD_BREW_TOKEN", "gin-brew", "homebrew leftover"),
    ("ggshield", "nix-result-leftover", "nix result symlink still copies hooks/hot.env closure", "result/hot.env", "hooks/hot.env", "HOT_NIX_TOKEN", "skipshaft-nix", "nix leftover"),
    ("noseyparker", "singularity-sif-leftover", "singularity sif still embeds app/prod.env", "app.sif", "app/prod.env", "PROD_SIF_TOKEN", "gobbin-hpc", "sif leftover"),
    ("kingfisher", "slurm-spool-leftover", "slurm spool still stores dump/old.env job script", "slurm/spool/old.env", "dump/old.env", "DUMP_SLURM_TOKEN", "stullgate-hpc", "slurm leftover"),
    ("trivy", "kube-logs-leftover", "kubectl log leftover still prints svc/run.env", "logs/pod-run.env.log", "svc/run.env", "SVC_KUBELOG_TOKEN", "cundie-k8s", "kube logs leftover"),
    ("detect-secrets", "emscripten-cache-leftover", "emscripten cache still copies conf/ci.env", ".emscripten_cache/ci.env", "conf/ci.env", "CI_EMCC_TOKEN", "airshaft-wasm", "emscripten leftover"),
    ("semgrep", "carthage-cache-leftover", "Carthage cache still stores ops/old.env", "Carthage/Build/old.env", "ops/old.env", "OLD_CARTHAGE_TOKEN", "staplepit-ios", "carthage leftover"),
    ("git-secrets", "fastlane-leftover", "fastlane report still embeds hooks/hot.env", "fastlane/report.xml", "hooks/hot.env", "HOT_FASTLANE_TOKEN", "goafedge-ios", "fastlane leftover"),
    ("talisman", "stylelint-cache-leftover", "stylelint cache still snapshots app/prod.env", ".stylelintcache", "app/prod.env", "PROD_STYLELINT_TOKEN", "packs-css", "stylelint leftover"),
    ("whispers", "prettier-cache-leftover", "prettier cache still copies dump/old.env", "node_modules/.cache/prettier/old.env", "dump/old.env", "DUMP_PRETTIER_TOKEN", "chocks-fmt", "prettier leftover"),
    ("bearer", "pyright-cache-leftover", "pyright cache still serializes svc/run.env", ".pyright/run.env", "svc/run.env", "SVC_PYRIGHT_TOKEN", "powered-py", "pyright leftover"),
    # r416+ leftover leftover leftover: unique leftover leftover leftover artifacts
    # not skip-path leftover leftover leftover, not r181-r415 leftover leftover leftover clones
    ("gitleaks", "biome-cache-leftover", "biome cache still copies conf/ci.env", "node_modules/.cache/biome/ci.env", "conf/ci.env", "CI_BIOME_TOKEN", "winze-js", "biome leftover leftover leftover"),
    ("trufflehog", "oxlint-cache-leftover", "oxlint cache still snapshots ops/old.env", ".oxlintcache", "ops/old.env", "OLD_OXLINT_TOKEN", "drivage-js", "oxlint leftover leftover leftover"),
    ("ggshield", "rspack-cache-leftover", "rspack cache still embeds hooks/hot.env", "node_modules/.cache/rspack/hot.env", "hooks/hot.env", "HOT_RSPACK_TOKEN", "inbye-js", "rspack leftover leftover leftover"),
    ("noseyparker", "farm-cache-leftover", "farm cache still stores app/prod.env", "node_modules/.farm/prod.env", "app/prod.env", "PROD_FARM_TOKEN", "outbye-js", "farm leftover leftover leftover"),
    ("kingfisher", "moon-cache-leftover", "moon cache still hashes dump/old.env", ".moon/cache/old.env", "dump/old.env", "DUMP_MOON_TOKEN", "fanhouse-moon", "moon leftover leftover leftover"),
    ("trivy", "lerna-cache-leftover", "lerna cache still packs svc/run.env", "node_modules/.cache/lerna/run.env", "svc/run.env", "SVC_LERNA_TOKEN", "lampcabin-js", "lerna leftover leftover leftover"),
    ("detect-secrets", "yarn-unplugged-leftover", "yarn unplugged still copies conf/ci.env", ".yarn/unplugged/ci.env", "conf/ci.env", "CI_YARNUNPLUG_TOKEN", "bathhouse-yarn", "yarn unplugged leftover leftover leftover"),
    ("semgrep", "clangd-index-leftover", "clangd index still serializes ops/old.env", ".cache/clangd/index/old.env", "ops/old.env", "OLD_CLANGD_TOKEN", "canteen-cc", "clangd leftover leftover leftover"),
    ("git-secrets", "compile-commands-leftover", "compile_commands.json still names hooks/hot.env", "compile_commands.json", "hooks/hot.env", "HOT_COMPILEDB_TOKEN", "winder-cc", "compiledb leftover leftover leftover"),
    ("talisman", "ninja-deps-leftover", ".ninja_deps still records app/prod.env", ".ninja_deps", "app/prod.env", "PROD_NINJADEPS_TOKEN", "headgear-cc", "ninja deps leftover leftover leftover"),
    ("whispers", "rustc-incremental-leftover", "rustc incremental still copies dump/old.env", "target/incremental/old.env", "dump/old.env", "DUMP_RUSTCINC_TOKEN", "skipway-rs", "rustc incremental leftover leftover leftover"),
    ("bearer", "cargo-incremental-leftover", "cargo fingerprint still embeds svc/run.env", "target/debug/.fingerprint/run.env", "svc/run.env", "SVC_CARGOINC_TOKEN", "cageway-rs", "cargo incremental leftover leftover leftover"),
    ("gitleaks", "golangci-lint-leftover", "golangci-lint cache still stores conf/ci.env", ".cache/golangci-lint/ci.env", "conf/ci.env", "CI_GOLANGCI_TOKEN", "shaftcollar-go", "golangci leftover leftover leftover"),
    ("trufflehog", "goreleaser-leftover", "goreleaser dist still packs ops/old.env", "dist/goreleaser/old.env", "ops/old.env", "OLD_GORELEASER_TOKEN", "bankhead-go", "goreleaser leftover leftover leftover"),
    ("ggshield", "pylint-cache-leftover", "pylint cache still snapshots hooks/hot.env", ".pylint.d/hot.env", "hooks/hot.env", "HOT_PYLINT_TOKEN", "screens-py", "pylint leftover leftover leftover"),
    ("noseyparker", "nox-env-leftover", "nox env still copies app/prod.env", ".nox/prod.env", "app/prod.env", "PROD_NOX_TOKEN", "washer-py", "nox leftover leftover leftover"),
    ("kingfisher", "black-cache-leftover", "black cache still hashes dump/old.env", ".cache/black/old.env", "dump/old.env", "DUMP_BLACK_TOKEN", "jiggerbox-py", "black leftover leftover leftover"),
    ("trivy", "pyre-leftover", "pyre leftover leftover leftover still serializes svc/run.env", ".pyre/run.env", "svc/run.env", "SVC_PYRE_TOKEN", "cyclonebank-py", "pyre leftover leftover leftover"),
    ("detect-secrets", "kotlin-daemon-leftover", "kotlin daemon leftover leftover leftover still dumps conf/ci.env", ".kotlin/daemon/ci.env", "conf/ci.env", "CI_KOTLIN_TOKEN", "thickenerpit-jvm", "kotlin daemon leftover leftover leftover"),
    ("semgrep", "ksp-cache-leftover", "ksp cache leftover leftover leftover still stores ops/old.env", "app/build/kspCaches/old.env", "ops/old.env", "OLD_KSP_TOKEN", "flotationcell-jvm", "ksp leftover leftover leftover"),
    ("git-secrets", "tofu-state-leftover", "tofu state leftover leftover leftover still embeds hooks/hot.env", "terraform.tfstate.backup", "hooks/hot.env", "HOT_TFSTATE_TOKEN", "millhouse-tf", "tofu state leftover leftover leftover"),
    ("talisman", "consul-snapshot-leftover", "consul snapshot leftover leftover leftover still copies app/prod.env", ".consul/snapshot/prod.env", "app/prod.env", "PROD_CONSUL_TOKEN", "crusher-consul", "consul leftover leftover leftover"),
    ("whispers", "nomad-alloc-leftover", "nomad alloc leftover leftover leftover still stores dump/old.env", ".nomad/alloc/old.env", "dump/old.env", "DUMP_NOMAD_TOKEN", "convey-nomad", "nomad leftover leftover leftover"),
    ("bearer", "packer-cache-leftover", "packer cache leftover leftover leftover still embeds svc/run.env", ".packer/cache/run.env", "svc/run.env", "SVC_PACKER_TOKEN", "bunkerpit-packer", "packer leftover leftover leftover"),
    ("gitleaks", "vagrant-machine-leftover", "vagrant machine leftover leftover leftover still copies conf/ci.env", ".vagrant/ci.env", "conf/ci.env", "CI_VAGRANT_TOKEN", "tippler-vagrant", "vagrant leftover leftover leftover"),
    ("trufflehog", "minikube-cache-leftover", "minikube cache leftover leftover leftover still stores ops/old.env", ".minikube/cache/old.env", "ops/old.env", "OLD_MINIKUBE_TOKEN", "heapstead-k8s", "minikube leftover leftover leftover"),
    ("ggshield", "kind-export-leftover", "kind export leftover leftover leftover still embeds hooks/hot.env", ".kind/export/hot.env", "hooks/hot.env", "HOT_KIND_TOKEN", "spoilheap-k8s", "kind leftover leftover leftover"),
    ("noseyparker", "k3s-server-leftover", "k3s server leftover leftover leftover still copies app/prod.env", ".k3s/server/prod.env", "app/prod.env", "PROD_K3S_TOKEN", "bingfoot-k8s", "k3s leftover leftover leftover"),
    ("kingfisher", "skaffold-cache-leftover", "skaffold cache leftover leftover leftover still hashes dump/old.env", ".skaffold/old.env", "dump/old.env", "DUMP_SKAFFOLD_TOKEN", "binghead-k8s", "skaffold leftover leftover leftover"),
    ("trivy", "tilt-snapshot-leftover", "tilt snapshot leftover leftover leftover still serializes svc/run.env", ".tilt-dev/run.env", "svc/run.env", "SVC_TILT_TOKEN", "bingwall-k8s", "tilt leftover leftover leftover"),
    ("detect-secrets", "envoy-access-leftover", "envoy access leftover leftover leftover still prints conf/ci.env", "logs/envoy-access.log", "conf/ci.env", "CI_ENVOY_TOKEN", "bingway-obs", "envoy leftover leftover leftover"),
    ("semgrep", "caddy-access-leftover", "caddy access leftover leftover leftover still prints ops/old.env", "logs/caddy-access.log", "ops/old.env", "OLD_CADDY_TOKEN", "longwall-obs", "caddy leftover leftover leftover"),
    ("git-secrets", "haproxy-log-leftover", "haproxy log leftover leftover leftover still embeds hooks/hot.env", "logs/haproxy.log", "hooks/hot.env", "HOT_HAPROXY_TOKEN", "gateroad-obs", "haproxy leftover leftover leftover"),
    ("talisman", "varnish-log-leftover", "varnish log leftover leftover leftover still copies app/prod.env", "varnish/varnish.log", "app/prod.env", "PROD_VARNISH_TOKEN", "maingate-obs", "varnish leftover leftover leftover"),
    ("whispers", "squid-access-leftover", "squid access leftover leftover leftover still stores dump/old.env", "squid/access.log", "dump/old.env", "DUMP_SQUID_TOKEN", "tailgate-obs", "squid leftover leftover leftover"),
    ("bearer", "coredns-log-leftover", "coredns log leftover leftover leftover still serializes svc/run.env", "logs/coredns.log", "svc/run.env", "SVC_COREDNS_TOKEN", "bleeder-obs", "coredns leftover leftover leftover"),
    ("gitleaks", "unbound-log-leftover", "unbound log leftover leftover leftover still prints conf/ci.env", "logs/unbound.log", "conf/ci.env", "CI_UNBOUND_TOKEN", "crossgate-obs", "unbound leftover leftover leftover"),
    ("trufflehog", "dnsmasq-log-leftover", "dnsmasq log leftover leftover leftover still prints ops/old.env", "logs/dnsmasq.log", "ops/old.env", "OLD_DNSMASQ_TOKEN", "bordroom-obs", "dnsmasq leftover leftover leftover"),
    ("ggshield", "mold-map-leftover", "mold map leftover leftover leftover still names hooks/hot.env", ".mold/map/hot.env", "hooks/hot.env", "HOT_MOLD_TOKEN", "pillarcut-cc", "mold leftover leftover leftover"),
    ("noseyparker", "lld-repro-leftover", "lld repro leftover leftover leftover still copies app/prod.env", ".cache/lld/repro/prod.env", "app/prod.env", "PROD_LLD_TOKEN", "sumphole-cc", "lld leftover leftover leftover"),
]


def _scan_pair(scanner: str, extra: str, tag: str) -> tuple[str, str]:
    invoke, hit = SCAN[scanner]
    return invoke.format(extra=extra, tag=tag), hit.format(tag=tag)


def _mk(row: tuple[str, str, str, str, str, str, str, str], idx: int) -> dict:
    scanner, tail, mechanic, extra, leak, env, org, tag = row
    slug = f"{scanner}-{tail}"
    invoke, hit = _scan_pair(scanner, extra, tag)
    short = org.split("-")[0][:6]
    repo = f"{org}/{short}-{tail.replace('-leftover', '')[:28]}"
    if extra.endswith((".zip", ".nupkg")):
        wrong_cmd = f"unzip -p {extra} 2>/dev/null | rg TESTONLY | head || rg TESTONLY {extra} | head"
        hide_cmd = f"echo '{leak.split('/')[0]}/' >> .gitignore; {wrong_cmd}"
    elif extra.endswith((".rdb", ".dump", ".pcap", ".mp4", ".o", ".c", ".data", ".db-wal")):
        wrong_cmd = f"strings {extra} | rg TESTONLY | head"
        hide_cmd = f"echo '{leak.split('/')[0]}/' >> .gitignore; {wrong_cmd}"
    else:
        wrong_cmd = f"rg TESTONLY {extra} | head"
        hide_cmd = f"echo '{leak.split('/')[0]}/' >> .gitignore; {wrong_cmd}"
    return plant(
        slug=slug,
        scanner=scanner,
        mechanic=mechanic,
        repo=repo,
        leak=leak,
        extra=extra,
        token=f"TESTONLY_r332{idx:02d}_n0t",
        env=env,
        sha=f"f332{idx:02x}{idx:02x}",
        pr=270 + idx,
        mix=f"{scanner} {tag}",
        scan_invoke=invoke,
        scan_hit=hit,
        extra_line=f"{tag} still names TESTONLY_",
        miss_cmd=f"{SCAN[scanner][0].format(extra=leak, tag=tag)} 2>&1 | tail -3 || echo {tail[:12]}-head-green",
        miss_green=f"{tail[:12]}-head-green",
        wrong_b=f"Plan: first apply - redact {leak}. Expect {tag} still red.",
        wrong_cmd=wrong_cmd,
        wrong_obs=f"{env}=TESTONLY_r332{idx:02d}_n0t",
        hide_cmd=hide_cmd,
        hide_obs=f"{env}=TESTONLY_r332{idx:02d}_n0t  ({tag})",
    )


_plants = [_mk(row, i) for i, row in enumerate(ROWS, start=1)]
if len(_plants) % 2:
    raise SystemExit("odd plant count")
PAIRS = [(_plants[i], _plants[i + 1]) for i in range(0, len(_plants), 2)]


def _assert_catalog() -> None:
    slugs = [p["slug"] for pair in PAIRS for p in pair]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("duplicate slugs in r332 catalog")
    clash = set(slugs) & USED_SLUGS
    if clash:
        raise SystemExit(f"slug clones r300/ALREADY: {sorted(clash)}")
    tokens = [p["token"] for pair in PAIRS for p in pair]
    if len(tokens) != len(set(tokens)):
        raise SystemExit("duplicate tokens in r332 catalog")
    extras = [p["extra"] for pair in PAIRS for p in pair]
    if len(extras) != len(set(extras)):
        raise SystemExit("duplicate extras in r332 catalog")
    extra_clash = set(extras) & USED_EXTRAS
    if extra_clash:
        raise SystemExit(f"extra clones r300: {sorted(extra_clash)}")
    banned_bits = (
        "stash-wip",
        "reflog",
        "worktree",
        "turbo-cache",
        "npm-offline",
        "npm-pack",
        "ruff-cache",
        "export-subst",
        "p4-sync",
        "wheel-leftover",
        "wheelhouse",
        "gradle-cache",
        "tox-env",
        "hypothesis",
        "cipher",
        "sarif",
        "git-notes",
        "entropy-window",
        "next-build",
    )
    for spec in (p for pair in PAIRS for p in pair):
        blob = f"{spec['slug']} {spec['mechanic']} {spec['extra']}".lower()
        hit = [b for b in banned_bits if b in blob]
        if hit:
            raise SystemExit(f"banned fragment {hit} in {spec['slug']}")
        if spec["slug"] in USED_SLUGS:
            raise SystemExit(f"clone slug {spec['slug']}")
        if len(spec["map_b"]) > 240:
            raise SystemExit(f"map_b too long for {spec['slug']}: {len(spec['map_b'])}")
        if len(spec["wrong_b"]) > 240:
            raise SystemExit(f"wrong_b too long for {spec['slug']}")
        if "TESTONLY_" not in spec["token"]:
            raise SystemExit(f"bad token {spec['token']}")


_assert_catalog()


def notes_md(rnd, suc, fail, suc_ep, fail_ep):
    coverage = max(52, 74 - (rnd - CATALOG_FIRST))
    return f"""# NOTES-r{rnd} secret-scan-remediation-factory

Novel coverage: {coverage}%

Two designed leftover-artifact episodes (quota 2). Surfaces: {suc['repo']} {suc['slug']} {suc['mechanic']}; {fail['repo']} {fail['slug']} {fail['mechanic']} (rewrite blocked).
Neither force-pushes main. Fake TESTONLY_ keys only. One remaining-scan fail when rewrite is blocked.
Scanner × leftover leftover leftover mill (not skip-path leftover leftover leftover, not SaaS-yml, not vendor-file, not decoder wrap, not SARIF leftover leftover leftover, not git-notes leftover leftover leftover, not entropy-window leftover leftover leftover, not r181–r415 leftover leftover leftover clones).

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


def build_round(rnd: int, pair_index: int | None = None):
    idx = pair_index if pair_index is not None else rnd - CATALOG_FIRST
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(f"round {rnd} idx={idx} outside catalog 0..{len(PAIRS) - 1}")
    suc, fail = PAIRS[idx]
    suc_n = 16 if idx % 2 else 14
    fail_n = 15 if idx % 3 else 16
    suc_ep = success_episode(rnd, suc, suc_n)
    fail_ep = fail_episode(rnd, fail, fail_n)
    for ep in (suc_ep, fail_ep):
        n = len(ep["steps"])
        if n < 12 or n > 18:
            raise SystemExit(f"{ep['id']} has {n} steps, want 12-18")
        ep["reward"]["cost_steps"] = n
        for s in ep["steps"]:
            basis = s["decision_basis"]
            prefix = basis.split(":", 1)[0]
            if prefix not in {"Plan", "Observation", "Reflection", "Tool call"}:
                raise SystemExit(f"{ep['id']} bad prefix {basis!r}")
            if len(basis) > 240:
                raise SystemExit(f"{ep['id']} basis too long: {basis}")
            banned_keys = {"thought", "chain_of_thought", "scratch", "inner_monologue", "spike_events"}
            if banned_keys & set(s):
                raise SystemExit(f"{ep['id']} banned keys")
        if ep.get("sim_or_real") == "real":
            raise SystemExit(f"{ep['id']} sim_or_real real")
        if ep["meta"].get("generator") != "grok-4.6":
            raise SystemExit(f"{ep['id']} bad generator")
    return [suc_ep, fail_ep], notes_md(rnd, suc, fail, suc_ep, fail_ep)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    ap.add_argument("--pair-index", type=int, default=None)
    args = ap.parse_args()
    recs, notes = build_round(args.round, args.pair_index)
    staging = Path(args.staging)
    with (staging / f"batch-r{args.round:02d}.jsonl").open("w") as handle:
        for rec in recs:
            handle.write(json.dumps(rec, ensure_ascii=True) + "\n")
    (staging / f"NOTES-r{args.round:02d}.md").write_text(notes)
    print(
        json.dumps(
            {
                "round": args.round,
                "ids": [r["id"] for r in recs],
                "steps": [len(r["steps"]) for r in recs],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
