#!/usr/bin/env python3
"""Generate experiments/pkg-mill-attest-wave16.py from a unique plant catalog."""
from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
USED_SLUGS = set()
FAC = HERE.parent / "outputs" / "raw" / "2026-08-19-agentic" / "package-release-factory"
if FAC.exists():
    import json

    for path in FAC.glob("batch-r*.jsonl"):
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            pid = json.loads(line)["id"]
            if pid.startswith("pkg-r"):
                rest = pid[len("pkg-r") :]
                dash = rest.find("-")
                if dash >= 0:
                    USED_SLUGS.add(rest[dash + 1 :])

USED_MIN = set()
if FAC.exists():
    import json
    import re

    for path in FAC.glob("batch-r*.jsonl"):
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            m = re.search(
                r"(?:Ship )?([a-z]+)-(?:oci|js|py|mvn|crate|brew|nix|nupkg)\b",
                rec.get("goal", ""),
            )
            if m:
                USED_MIN.add(m.group(1))

MINERALS = [
    "afghanite", "ahrensite", "akatoreite", "allabogdanite", "alloriite",
    "aluminite", "alunogen", "amblygonite", "ancylite", "andyrobertsite",
    "anhydrite", "ankerite", "annabergite", "aphthitalite", "apjohnite",
    "arcanite", "argutite", "armenite", "arthurite", "asbecasite",
    "aubertite", "augelite", "aurichalcite", "axinite", "bakerite",
    "banalsite", "bassanite", "bauxite", "bayerite", "beaverite",
    "beraunite", "berlinite", "berryite", "berzelianite", "betafite",
    "beudantite", "bikitaite", "bindheimite", "bismite", "bornite",
    "braggite", "braunite", "brazilianite", "breunnerite", "brewsterite",
    "brucite", "brushite", "bunsenite", "cabalzarite", "cacoxenite",
    "cadmoindite", "calaverite", "calciborite", "calomel", "carletonite",
    "carminite", "cervantite", "chabazite", "chapmanite", "charoite",
    "childrenite", "chlorargyrite", "chondrodite", "chrysotile", "clausthalite",
    "colemanite", "columbite", "coronadite", "corrensite", "corundum",
    "creedite", "cristobalite", "cummingtonite", "danburite", "datolite",
    "dawsonite", "diaspore", "djurleite", "domeykite", "dundasite",
    "elbaite", "esperite", "ettringite", "euxenite", "fergusonite",
    "gormanite", "goslarite", "greigite", "halloysite", "hematite",
    "hemimorphite", "howlite", "huebnerite", "hydromagnesite", "idocrase",
    "illite", "jarosite", "kaolinite", "laumontite", "lazurite",
    "leucite", "lizardite", "monazite", "montmorillonite", "nacrite",
    "niccolite", "palygorskite", "phenakite", "powellite", "pyrophyllite",
    "pyrrhotite", "sanidine", "scolecite", "stilbite", "strontianite",
    "tennantite", "thorite", "thulite", "tourmaline", "triphylite",
    "variscite", "vermiculite", "vivianite", "willemite", "xenotime",
    "zincite", "zircon", "admontite", "afwillite", "agrinierite",
    "aguilarite", "ahlfeldite", "akdalaite", "akrochordite", "aksaite",
    "aktashite", "alacranite", "aldermanite", "alforsite", "algodonite",
    "allophane", "alluaudite", "alvanite", "amakinite", "amarillite",
    "amicite", "aminoffite", "analogite", "anauxite", "andremeierite",
    "antofagastaite", "apophyllite", "arcubisite", "ardennite", "artinite",
    "asbolane", "asisite", "asselbornite", "atelestite", "atheneite",
    "attapulgite", "auricupride", "avicennite", "awaruite", "babefphite",
    "balestraite", "barstowite", "bartelkeite", "batievaite", "belovite",
    "bensonite", "bergenite", "betpakdalite", "biehlite", "birnessite",
    "bismoclite", "bityite", "blatonite", "blixite", "blodite",
    "boggsite", "bonaccordite", "boothite", "boralsilite", "bornemanite",
    "botallackite", "bouazzerite", "boyleite", "brackebuschite", "brandholzite",
    "brannockite", "brassite", "brezinaite", "brianite", "brianyoungite",
    "brockite", "brodtkorbite", "brunogeierite", "buchwaldite", "bukovite",
    "burckhardtite", "burkeite", "burpalite", "butlerite", "bystromite",
    "cadwaladerite", "cahnite", "calciobetafite", "calderonite", "canaphite",
    "canasite", "cancrisilite", "cannizzarite", "capgaronnite", "carlfriesite",
    "carlosturanite", "carobbiite", "carrboydite", "caryinite", "caryopilite",
    "cassedanneite", "cattiite", "cavansite", "celadonite", "cernyite",
    "chalcophyllite", "chalcostibite", "changoite", "charlesite", "chatkalite",
    "chayesite", "cheremnykhite", "chernovite", "chiavennite", "chiolite",
    "chkalovite", "choloalite", "chovanite", "chrisstanleyite", "christite",
    "chudobaite", "churchite", "chursinite", "clairite", "claraite",
    "clarkeite", "claudetite", "cleusonite", "clinoclase", "clinohedrite",
]
MINERALS = [m for m in MINERALS if m not in USED_MIN]
extra = Path("/tmp/pkg-free-min.txt")
if extra.exists():
    MINERALS += [m for m in extra.read_text().split() if m not in USED_MIN]
# unique preserve
seen = set()
mins = []
for m in MINERALS:
    if m not in seen:
        seen.add(m)
        mins.append(m)
MINERALS = mins

COSIGN = [
    ("cosign-verify-oci-referrer-variant-vs-type", "referrer variant leftover", "OCI referrer type"),
    ("cosign-sign-bundle-nightly-vs-prod-dsse", "nightly bundle leftover", "prod DSSE bundle"),
    ("cosign-fulcio-auth0-oidc-vs-github", "Auth0 Fulcio leftover", "GitHub Fulcio issuer"),
    ("cosign-rekor-entry-kind-dsse-vs-rfc3161", "DSSE leftover", "RFC3161 Rekor kind"),
    ("cosign-verify-tsa-chain-incomplete", "incomplete TSA chain leftover", "complete TSA chain"),
    ("cosign-policy-identity-matrix-vs-path", "matrix leftover", "workflow path identity"),
    ("cosign-sign-kms-ibm-vs-aws", "IBM KMS leftover", "AWS KMS key"),
    ("cosign-verify-identity-delete-vs-tag", "delete identity leftover", "tag identity"),
    ("cosign-attach-predicate-vsa-vs-slsa", "VSA leftover", "SLSA predicate"),
    ("cosign-copy-signature-oci-vs-tlog", "oci leftover", "tlog signature"),
    ("cosign-verify-tuf-timestamp-stale", "stale TUF timestamp leftover", "refreshed TUF timestamp"),
    ("cosign-sign-recursive-vsa-partial", "partial VSA leftover", "full index VSA"),
    ("cosign-policy-ctlog-pubkey-expired-pem", "expired CT PEM leftover", "current CT PEM"),
    ("cosign-fulcio-uri-san-repo-template-org", "template org SAN leftover", "canonical org SAN"),
    ("cosign-verify-bundle-hash-algo-ripemd-vs-sha256", "ripemd leftover", "sha256 payload algo"),
    ("cosign-sign-sk-piv-slot-85-vs-9a", "PIV slot 85 leftover", "PIV slot 9a"),
    ("cosign-oidc-issuer-keycloak-vs-github", "Keycloak leftover", "GitHub Actions OIDC"),
    ("cosign-verify-cert-notafter-skew-weeks", "notAfter weeks leftover", "NTP-aligned notAfter"),
    ("cosign-policy-builder-id-org-mismatch", "builder org leftover", "exact builder id"),
    ("cosign-sign-payload-intoto-vsa-json", "in-toto VSA leftover", "in-toto SLSA payload"),
    ("cosign-rekor-inclusion-proof-note", "note leftover", "signed note"),
    ("cosign-verify-oci-index-osfeatures-filter", "osfeatures leftover", "full OCI index"),
    ("cosign-sign-annotation-predicate-profile", "predicate profile leftover", "matching profile"),
    ("cosign-policy-max-cert-lifetime-months", "max cert months leftover", "policy months"),
]

NPM = [
    ("npm-provenance-bundleDependencies-legacy-bundling", "legacy bundling leftover", "legb-lock"),
    ("npm-trusted-publisher-workflow-filename-hotfix-yml", "workflow hotfix.yml leftover", "hot-lock"),
    ("npm-oidc-audience-npmjs-biz", "audience npmjs.biz leftover", "nbiz-aud"),
    ("npm-provenance-uninstall-mutates-pack", "uninstall leftover", "uninst-lock"),
    ("npm-trusted-publisher-environment-required-status", "required status leftover", "rsts-lock"),
    ("npm-oidc-subject-ref-check-run", "check_run leftover", "crun-lock"),
    ("npm-provenance-optionalDependencies-libc-aix", "aix libc leftover", "aix-lock"),
    ("npm-publish-from-sysbox-runner-no-oidc", "sysbox without OIDC leftover", "sys-lock"),
    ("npm-trusted-publisher-app-token-still-latest", "app token leftover", "appt-lock"),
    ("npm-provenance-private-workspace-only", "workspace only leftover", "wonly-lock"),
    ("npm-oidc-permissions-id-token-write-deployments", "deployments write leftover", "depw-lock"),
    ("npm-provenance-files-field-includes-scripts", "files includes scripts leftover", "scr-lock"),
    ("npm-trusted-publisher-org-sso-ldap", "org LDAP leftover", "ldap-lock"),
    ("npm-oidc-job-container-user-www", "container www leftover", "cwww-lock"),
    ("npm-provenance-lockfileVersion-1-vs-9", "lockfileVersion 1 leftover", "lf19-lock"),
    ("npm-publish-access-restricted-internal-scope", "restricted internal leftover", "rint-lock"),
    ("npm-trusted-publisher-workflow-call-secrets-json", "workflow_call secrets json leftover", "wcsj-lock"),
    ("npm-oidc-issuer-buildkite-vs-github", "Buildkite leftover", "bk-lock"),
    ("npm-provenance-bin-field-glob-subject", "bin glob leftover", "bing-lock"),
    ("npm-trusted-publisher-environment-wait-timer-180", "wait_timer 180 leftover", "wt180-lock"),
    ("npm-oidc-audience-yarnpkg-biz", "audience yarnpkg.biz leftover", "ybiz-lock"),
    ("npm-provenance-os-cpu-optional-netbsd-x64", "netbsd leftover", "nbsd-lock"),
    ("npm-publish-provenance-file-then-omit-retry", "file then omit leftover", "fto-lock"),
    ("npm-trusted-publisher-vm-ephemeral-no-oidc", "vm ephemeral leftover", "vme-lock"),
]

PYPI = [
    ("pypi-trusted-publisher-workflow-path-libs-dir", "libs workflow leftover", "release.yml path"),
    ("pypi-oidc-issuer-gitea-actions-hostname-vs-github", "Gitea Actions hostname leftover", "GitHub OIDC issuer"),
    ("pypi-attestation-headers-missing-sdist", "headers leftover", "sdist+wheel pair"),
    ("pypi-twine-attestations-ubjson-not-dsse", "UBJSON leftover", "DSSE envelope"),
    ("pypi-trusted-publisher-environment-name-nightly-typo", "environment nightly leftover", "environment production"),
    ("pypi-oidc-job-container-id-token-request-read", "container request read leftover", "runner id-token"),
    ("pypi-hatch-index-azure-artifacts-url-leftover", "hatch azure leftover", "prod PyPI index"),
    ("pypi-uv-publish-trusted-publishing-warn", "uv warn leftover", "uv trusted publishing"),
    ("pypi-poetry-keyring-backend-secretstorage-leftover", "poetry secretstorage leftover", "OIDC trusted publisher"),
    ("pypi-oidc-subject-workflow-ref-heads-nightly", "workflow ref heads/nightly leftover", "exact tag ref"),
    ("pypi-attestation-pep740-sct-missing", "PEP 740 SCT leftover", "pep740 SCT"),
    ("pypi-trusted-publisher-project-name-control-chars", "control-char project leftover", "normalized PyPI name"),
    ("pypi-oidc-issuer-drone-cloud-vs-github", "Drone Cloud leftover", "GitHub OIDC issuer"),
    ("pypi-twine-config-file-envfile-leftover", "twine envfile leftover", "OIDC trusted publishing"),
    ("pypi-trusted-publisher-workflow-call-ref-v5", "workflow_call v5 leftover", "sha-pinned reusable workflow"),
    ("pypi-oidc-job-services-nats-sidecar", "nats sidecar leftover", "bare runner OIDC"),
    ("pypi-attestation-wheel-manylinux_2_31-vs-2-28", "manylinux_2_31 leftover", "manylinux_2_28 attestation"),
    ("pypi-hatch-index-azure-token-vs-oidc", "hatch azure token leftover", "hatch trusted publishing"),
    ("pypi-uv-publish-check-url-azure-legacy", "uv azure leftover", "uv check-url pypi.org"),
    ("pypi-poetry-pypi-token-secretstorage-vs-oidc", "poetry secretstorage leftover", "poetry OIDC"),
    ("pypi-trusted-publisher-environment-required-reviewers-6", "six reviewers leftover", "immediate environment"),
    ("pypi-oidc-issuer-concourse-vs-github", "Concourse leftover", "GitHub OIDC issuer"),
    ("pypi-attestation-attestations-dir-parquet-pair", "parquet leftover", "wheel+sdist attestations"),
    ("pypi-twine-skip-existing-attest-json", "skip-existing json leftover", "twine attestations required"),
]

MAVEN = [
    ("maven-gpg-sign-war-only-missing-jar", "war-only leftover", "war-stg"),
    ("maven-central-portal-publishing-type-stream-hang", "stream hang leftover", "strm-stg"),
    ("maven-gpg-keyring-agent-gpg-stale", "stale gpg leftover", "gpg-stg"),
    ("maven-gpg-passphrase-curses-xor-env", "curses leftover", "cur-stg"),
    ("maven-central-bundle-missing-war-checksum", "war checksum leftover", "warc-stg"),
    ("maven-gpg-useagent-true-pinentry-dmenu", "pinentry dmenu leftover", "dmenu-stg"),
    ("maven-ossrh-staging-profile-id-draining", "draining profile leftover", "drain-stg"),
    ("maven-gpg-sign-asc-armor-version-2", "armor v2 leftover", "av2-stg"),
    ("maven-central-publisher-api-namespace-audit", "audit leftover", "aud-stg"),
    ("maven-gpg-digest-sha384-vs-sha256-policy", "SHA384 leftover", "s384p-stg"),
    ("maven-settings-gpg-executable-apk-path", "apk leftover", "apk-stg"),
    ("maven-gpg-skip-war-asc", "skip war leftover", "swar-stg"),
    ("maven-gpg-sign-war-only-missing-modules", "war modules leftover", "wmod-stg"),
    ("maven-central-portal-deployment-status-replicating", "replicating leftover", "repl-stg"),
    ("maven-gpg-homedir-gnupg-home-env-vs-absolute", "GNUPGHOME env leftover", "ghenv-stg"),
    ("maven-gpg-sign-plugin-skip-war", "skip war plugin leftover", "skw-stg"),
    ("maven-central-user-token-compromised", "compromised leftover", "comp-stg"),
    ("maven-gpg-signer-class-bc-jdk11", "BC jdk11 leftover", "bc11-stg"),
    ("maven-settings-server-central-public-id", "central public leftover", "cpub-stg"),
    ("maven-gpg-exclude-classifiers-war", "exclude war leftover", "exw-stg"),
    ("maven-central-bundle-missing-module-sha3-256", "module sha3 leftover", "s3m-stg"),
    ("maven-gpg-sign-attached-war-missing", "attached war leftover", "awar-stg"),
    ("maven-ossrh-s01-host-after-portal-cdn", "s01 cdn leftover", "cdn-stg"),
    ("maven-gpg-passphrase-server-id-cdn-old", "old cdn passphrase leftover", "cdnold-stg"),
]

CRATES = [
    ("crates-yank-vs-cargo-outdated-workspace-only", "cargo-outdated workspace leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-deny-advisories-offline", "cargo-deny advisories offline leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-audit-json-pretty", "cargo-audit json pretty leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-cyclonedx-v1-0", "cargo-cyclonedx v1.0 leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-modules-features", "cargo-modules features leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-shear-unused-examples", "cargo-shear unused-examples leftover", "sparse yank index"),
    ("crates-yank-vs-crates-io-api-v2-new", "crates.io api v2 new leftover", "sparse yank index"),
    ("crates-yank-vs-lib-rs-manifest", "lib.rs manifest leftover", "sparse yank index"),
    ("crates-yank-vs-docsrs-source-crate-zip", "docs.rs crate zip leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-release-verify", "cargo-release verify leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-clone-git", "cargo-clone git leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-info-repo", "cargo info repo leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-tree-prefix-json", "cargo-tree prefix json leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-minimal-versions-all", "minimal-versions all leftover", "sparse yank index"),
    ("crates-yank-vs-crates-io-api-v1-updated", "crates.io api v1 updated leftover", "sparse yank index"),
    ("crates-yank-vs-lib-rs-manifest-json", "lib.rs manifest json leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-public-api-diff-ndjson", "cargo-public-api ndjson leftover", "sparse yank index"),
    ("crates-yank-vs-rustdoc-scrape-examples-org", "rustdoc scrape org leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-dist-manifest-json", "cargo-dist manifest leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-semver-checks-baseline-test", "semver-checks test leftover", "sparse yank index"),
    ("crates-yank-vs-crates-io-trustpub-manifest", "crates.io trustpub manifest leftover", "sparse yank index"),
    ("crates-yank-vs-lib-rs-humans", "lib.rs humans leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-show-asm-s390x", "cargo-show-asm s390x leftover", "sparse yank index"),
    ("crates-yank-vs-docsrs-rustdoc-json-package", "docs.rs rustdoc package leftover", "sparse yank index"),
]

BREW = [
    ("homebrew-bottle-rebuild-vs-uses-from-macos-sqlite", "uses_from_macos sqlite leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-depends-on-macos-sierra", "depends_on macos sierra leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-head-spec-ref", "head ref leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-patch-data-p7", "patch DATA p7 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-resource-using", "resource using leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-keg-only-because-shadowed-by-xcode", "keg_only xcode leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-disable-because-unsigned", "disable unsigned leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-deprecate-because-forked", "deprecate forked leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-service-keep-alive-never", "service never leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-std-mix-args", "std_mix leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-on-mojave-block", "on_mojave leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-depends-on-arch-wasm32", "depends_on arch wasm leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-tap-migrations-xml", "tap_migrations xml leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-fails-with-gcc-8", "fails_with gcc 8 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-cxxstdlib-check-custom", "cxxstdlib custom leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-post-install-install-name-tool", "post_install install_name leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-caveats-nvram", "caveats nvram leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-depends-on-lua", "depends_on lua leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-option-with-shared", "option shared leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-needs-sse3", "needs sse3 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-on-linux-openbsd", "on_linux openbsd leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-version-scheme-seven", "version_scheme 7 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-revision-four", "revision 4 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-stable-url-sri", "stable sri leftover", "rebuilt bottle sha"),
]

NIX = [
    ("nix-fetchFromBitbucket-uuid-vs-nar", "Bitbucket uuid leftover", "NAR of Bitbucket archive"),
    ("nix-fetchzip-sha1-vs-nar", "fetchzip sha1 leftover", "NAR of zip"),
    ("nix-fetchTarball-sha1-vs-nar", "fetchTarball sha1 leftover", "NAR of tarball"),
    ("nix-fetchPypi-sha1-vs-nar", "fetchPypi sha1 leftover", "NAR of PyPI sdist"),
    ("nix-fetchCrate-sha1-vs-nar", "fetchCrate sha1 leftover", "NAR of crates.io crate"),
    ("nix-fetchFromGitiles-sha1-vs-nar", "Gitiles sha1 leftover", "NAR of Gitiles archive"),
    ("nix-fetchsvn-sha1-vs-nar", "svn sha1 leftover", "NAR of svn export"),
    ("nix-fetchhg-sha1-vs-nar", "hg sha1 leftover", "NAR of hg archive"),
    ("nix-fetchcvs-sha1-vs-nar", "CVS sha1 leftover", "NAR of CVS export"),
    ("nix-fetchFromAzureDevOps-sha1-vs-nar", "Azure sha1 leftover", "NAR of Azure archive"),
    ("nix-fetchgit-fetchNotes-false-vs-nar", "no-notes leftover", "NAR of checkout"),
    ("nix-fetchurl-sha1-vs-nar-url", "fetchurl sha1 leftover", "NAR of fetched url"),
    ("nix-fetchFromGitHub-sha1-vs-nar", "GitHub sha1 leftover", "NAR of archive"),
    ("nix-fetchgit-cherry-vs-nar", "cherry leftover", "NAR of fetchgit"),
    ("nix-fetchFromGitLab-sha1-vs-nar", "GitLab sha1 leftover", "NAR of https archive"),
    ("nix-fetchgit-merge-vs-nar", "merge leftover", "NAR of pinned fetchgit"),
    ("nix-fetchFromGitea-sha1-vs-nar", "Gitea sha1 leftover", "NAR of public Gitea archive"),
    ("nix-fetchurl-sha384-vs-nar-store", "fetchurl sha384 leftover", "NAR of fetchurl store path"),
    ("nix-fetchFromCgit-sha1-vs-nar", "cgit sha1 leftover", "NAR of cgit archive"),
    ("nix-fetchgit-bisect-vs-nar", "bisect leftover", "NAR of pinned fetchgit"),
    ("nix-fetchFromSourcehut-sha1-vs-nar", "Sourcehut sha1 leftover", "NAR of sourcehut archive"),
    ("nix-fetchzip-sha1-vs-nar-root", "fetchzip sha1 leftover", "NAR of zip"),
    ("nix-builtins-derivation-vs-nar", "builtins.derivation leftover", "NAR of derivation"),
    ("nix-fetchgit-fetchNotes-all-vs-nar", "all notes leftover", "NAR of checkout"),
]

NUGET = [
    ("nuget-snupkg-embed-untracked-sources-bench", "EmbedUntrackedSources bench leftover", "untracked-bench"),
    ("nuget-snupkg-sourcelink-azure-repos-cloud-vs-tfs", "Azure Repos cloud leftover", "azdo-ctfs"),
    ("nuget-snupkg-deterministic-pathmap-msbuild", "msbuild PathMap leftover", "pathmap-msb"),
    ("nuget-snupkg-debug-type-none-vs-full", "DebugType none leftover", "none-full"),
    ("nuget-snupkg-include-symbols-snupkg-true-no-md", "IncludeSymbols no md leftover", "sym-nomd"),
    ("nuget-snupkg-sourcelink-bitbucket-server-vs-cloud-dc", "Bitbucket server leftover", "bb-svrdc"),
    ("nuget-snupkg-continuous-integration-build-true-gha", "CI gha leftover", "cigha"),
    ("nuget-snupkg-embed-all-sources-false-with-pdb", "EmbedAllSources with pdb leftover", "embed-fpdb"),
    ("nuget-snupkg-publish-gitlab-nuget-v7", "GitLab nuget v7 leftover", "gl-n7"),
    ("nuget-snupkg-pdb-checksum-algorithm-fnv", "PDB checksum fnv leftover", "pdb-fnv"),
    ("nuget-snupkg-sourcelink-gitea-drone-vs-github", "Gitea drone leftover", "gitea-dr"),
    ("nuget-snupkg-embedded-files-filter-none-glob", "embedded files none glob leftover", "embed-ng"),
    ("nuget-snupkg-source-root-unc-share", "UNC share leftover", "uncs-root"),
    ("nuget-snupkg-symbolpackageformat-snupkg-vs-symbols-pkg", "snupkg vs symbols leftover", "fmt-ssp"),
    ("nuget-snupkg-repository-branch-vs-type", "RepositoryBranch leftover", "repo-bt"),
    ("nuget-snupkg-sourcelink-codeberg-drone-vs-github", "Codeberg drone leftover", "cb-dr"),
    ("nuget-snupkg-publish-github-packages-nuget-v8", "GPR nuget v8 leftover", "gpr-n8"),
    ("nuget-snupkg-portable-pdb-guid-deadbeef", "portable PDB deadbeef leftover", "pdb-db"),
    ("nuget-snupkg-sourcelink-sourcehut-paste-vs-github", "sourcehut paste leftover", "srht-paste"),
    ("nuget-snupkg-source-link-mapped-path-unc-share", "UNC share mapped leftover", "uncs-map"),
    ("nuget-snupkg-publish-myget-v7-vs-nuget-org", "MyGet v7 leftover", "myget-v7"),
    ("nuget-snupkg-debug-type-pdbonly-vs-embedded-src", "DebugType pdbonly leftover", "pdbonly-embs"),
    ("nuget-snupkg-include-source-revision-true-release", "IncludeSourceRevision release leftover", "src-trel"),
    ("nuget-snupkg-sourcelink-forgejo-drone-vs-github", "Forgejo drone leftover", "fj-dr"),
]


def assert_unique(rows, label):
    slugs = [r[0] for r in rows]
    if len(slugs) != len(set(slugs)):
        raise SystemExit(f"dup in {label}")
    hits = [s for s in slugs if s in USED_SLUGS]
    if hits:
        raise SystemExit(f"{label} slug already published: {hits[:8]}")


for label, rows in (
    ("cosign", COSIGN),
    ("npm", NPM),
    ("pypi", PYPI),
    ("maven", MAVEN),
    ("crates", CRATES),
    ("brew", BREW),
    ("nix", NIX),
    ("nuget", NUGET),
):
    assert_unique(rows, label)

N = len(COSIGN)
assert all(
    len(x) == N
    for x in (NPM, PYPI, MAVEN, CRATES, BREW, NIX, NUGET)
), (N, len(NPM), len(PYPI), len(MAVEN), len(CRATES), len(BREW), len(NIX), len(NUGET))
need = N * 8
if len(MINERALS) < need:
    raise SystemExit(f"need {need} minerals, have {len(MINERALS)}")

HEADER = '''#!/usr/bin/env python3
"""Unique mill: package-release-factory attestation wave-16 (r1316+).

BAN r247–r513 mill slugs including r513 nix-fetchgit-deepClone-no-leaveDotGit-vs-nar /
nuget-snupkg-embed-all-sources-on-no-repo.
BAN digest-vs-git-SHA + lock-yank twins and leftover license/supplier clones.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
_spec = importlib.util.spec_from_file_location(
    "pkg_mill_attest_wave5", HERE / "pkg-mill-attest-wave5.py"
)
w5 = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(w5)

CATALOG_FIRST = 1316
BUILDERS = w5.BUILDERS
notes_for = w5.notes_for
ok_cosign = w5.ok_cosign
fail_npm = w5.fail_npm
ok_pypi = w5.ok_pypi
fail_maven = w5.fail_maven
ok_crates = w5.ok_crates
fail_brew = w5.fail_brew
ok_nix = w5.ok_nix
fail_nuget = w5.fail_nuget

BANNED_PHRASES = (
    "digest equals git sha",
    "digest=git sha",
    "lockfile yank twin",
    "reuse-downloaded-gpl-license",
    "cdx-metadata-supplier",
    "nix-fetchgit-deepclone-no-leavedotgit-vs-nar",
    "nuget-snupkg-embed-all-sources-on-no-repo",
    '"sim_or_real": "real"',
)


def banned_text(obj: dict) -> None:
    w5.banned_text(obj)
    blob = json.dumps(obj).lower()
    for phrase in BANNED_PHRASES:
        if phrase in blob:
            raise SystemExit(f"banned phrase present: {phrase}")


def _pairs():
    extra = []

    def add(ok, fail):
        extra.append(("ok_attest", ok, "fail_leftover", fail))

'''

FOOTER = '''
    return extra


PAIRS = _pairs()


def emit(round_n: int, idx: int | None = None):
    if idx is None:
        idx = round_n - CATALOG_FIRST
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(f"idx {idx} outside catalog 0+{len(PAIRS)} (round {round_n})")
    ok_kind, ok_spec, fail_kind, fail_spec = PAIRS[idx]
    ok_ep = BUILDERS[ok_kind](round_n, ok_spec)
    fail_ep = BUILDERS[fail_kind](round_n, fail_spec)
    banned_text(ok_ep)
    banned_text(fail_ep)
    return ok_ep, fail_ep, notes_for(round_n, ok_spec, fail_spec)


def selfcheck():
    slugs, plants = [], []
    for i, (_, ok, _, fail) in enumerate(PAIRS):
        emit(CATALOG_FIRST + i)
        slugs += [ok["slug"], fail["slug"]]
        plants += [ok["plant"], fail["plant"]]
    if len(slugs) != len(set(slugs)) or len(plants) != len(set(plants)):
        raise SystemExit("dup slug or plant in attest wave16 catalog")
    fac = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "package-release-factory"
    hits = []
    if fac.exists():
        published = []
        for path in fac.glob("batch-r*.jsonl"):
            for line in path.read_text().splitlines():
                if line.strip():
                    published.append(json.loads(line)["id"])
        assigned = {}
        for i, (_, ok, _, fail) in enumerate(PAIRS):
            rnd = CATALOG_FIRST + i
            assigned[ok["slug"]] = f"pkg-r{rnd}-{ok['slug']}"
            assigned[fail["slug"]] = f"pkg-r{rnd}-{fail['slug']}"
        for slug, expected_id in assigned.items():
            for pid in published:
                if pid.endswith("-" + slug) and pid != expected_id:
                    hits.append(pid)
    if hits:
        raise SystemExit(f"slug already published: {hits[:8]}")
    print(
        json.dumps(
            {
                "catalog_first": CATALOG_FIRST,
                "n_pairs": len(PAIRS),
                "last_round": CATALOG_FIRST + len(PAIRS) - 1,
                "n_slugs": len(slugs),
            }
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--round", type=int)
    parser.add_argument("--staging", type=Path)
    parser.add_argument("--idx", type=int)
    parser.add_argument("--selfcheck", action="store_true")
    args = parser.parse_args()
    if args.selfcheck:
        selfcheck()
        return 0
    if args.round is None or args.staging is None:
        raise SystemExit("need --round and --staging (or --selfcheck)")
    ok_ep, fail_ep, notes = emit(args.round, args.idx)
    args.staging.mkdir(parents=True, exist_ok=True)
    batch = args.staging / f"batch-r{args.round:02d}.jsonl"
    notes_path = args.staging / f"NOTES-r{args.round:02d}.md"
    with batch.open("w") as handle:
        handle.write(json.dumps(ok_ep, ensure_ascii=False) + "\\n")
        handle.write(json.dumps(fail_ep, ensure_ascii=False) + "\\n")
    notes_path.write_text(notes)
    print(
        json.dumps(
            {
                "round": args.round,
                "ids": [ok_ep["id"], fail_ep["id"]],
                "steps": [len(ok_ep["steps"]), len(fail_ep["steps"])],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def ver_triple(i, a0, b0, c0):
    a = a0 + (i % 7)
    b = b0 + (i % 6)
    c = c0 + (i % 5)
    return f"{a}.{b}.{c}"


def bump(ver):
    a, b, c = ver.split(".")
    return f"{a}.{b}.{int(c) + 1}"


def emit_add_calls() -> str:
    lines = []
    mi = 0

    def take(suffix):
        nonlocal mi
        plant = f"{MINERALS[mi]}-{suffix}"
        mi += 1
        return plant

    # rotation A: cosign + npm
    for i, ((cslug, cleft, cint), (nslug, nleft, ncons)) in enumerate(zip(COSIGN, NPM)):
        cp, np_ = take("oci"), take("js")
        ver = ver_triple(i, 1, 1, 1)
        nv = ver_triple(i, 2, 0, 1)
        nxt = bump(nv)
        minc = cp.split("-")[0]
        lines.append("    add(")
        lines.append("        ok_cosign(")
        lines.append(f'            slug={cslug!r},')
        lines.append(f"            plant={cp!r}, ver={ver!r},")
        lines.append(f"            kind={cleft!r} + ' leftover vs ' + {cint!r},")
        # wait, that's wrong - kind should be a string not python concat in source...
        # I'll fix by using formatted strings
        lines[-1] = f"            kind={(cleft + ' leftover vs ' + cint)!r},"
        lines.append(f"            leftover={cleft!r}, intended={cint!r},")
        lines.append(f"            asset='dist/{minc}-left.txt',")
        lines.append(f"            first={'verify leftover ' + cleft + ' against ' + cint!r},")
        lines.append(f"            change={'sign matching ' + cint!r},")
        lines.append(f"            term={'success; ' + cleft + ' leftover'!r},")
        lines.append(f"            err={'Error: leftover ' + cleft + '; want ' + cint!r},")
        lines.append("            policy='{\\n  \"intended\": %s\\n}' % " + repr(cint) + ",")
        # policy as literal
        lines[-1] = f"            policy={('{\\n  \"intended\": ' + json_escape(cint) + '\\n}')!r},"
        lines.append(f"            sign={'run: cosign sign --yes $IMAGE  # leftover ' + cleft!r},")
        lines.append("        ),")
        lines.append("        fail_npm(")
        lines.append(f"            slug={nslug!r},")
        lines.append(f"            plant={np_!r}, ver={nv!r}, nxt={nxt!r},")
        lines.append(f"            kind={(nleft + ' leftover vs provenance')!r},")
        lines.append(f"            leftover={nleft!r}, consumer={ncons!r},")
        lines.append(f"            first={'publish leftover ' + nleft + ' as provenance'!r},")
        lines.append(f"            change={nxt + ' drop leftover then OIDC'!r},")
        lines.append(f"            term={'fail: ' + ncons + ' still ' + nv!r},")
        lines.append(f"            err={'npm ERR! leftover ' + nleft!r},")
        lines.append(f"            wf={'run: npm publish --provenance\\n# leftover ' + nleft!r},")
        lines.append("        ),")
        lines.append("    )")

    # rotation B: pypi + maven
    for i, ((pslug, pleft, pint), (mslug, mleft, mstg)) in enumerate(zip(PYPI, MAVEN)):
        pp, mp = take("py"), take("mvn")
        ver = ver_triple(i + 3, 3, 1, 0)
        old = ver_triple(i + 3, 3, 0, 9)
        mv = ver_triple(i + 4, 1, 2, 0)
        nxt = bump(mv)
        stg = f"{mp.split('-')[0]}-{mstg}"
        lines.append("    add(")
        lines.append("        ok_pypi(")
        lines.append(f"            slug={pslug!r},")
        lines.append(f"            plant={pp!r}, ver={ver!r},")
        lines.append(f"            kind={(pleft + ' leftover vs ' + pint)!r},")
        lines.append(f"            leftover={pleft!r}, intended={pint!r},")
        lines.append(f"            asset='dist/{pp.split('-')[0]}-old.json',")
        lines.append(f"            first={'twine leftover ' + pleft!r},")
        lines.append(f"            change={'enable ' + pint!r},")
        lines.append(f"            term={'success; ' + pleft + ' leftover'!r},")
        lines.append(f"            err={'HTTPError: leftover ' + pleft + '; want ' + pint!r},")
        lines.append(f"            wf={'permissions:\\n  id-token: write\\n# leftover ' + pleft!r},")
        lines.append(f"            old={old!r},")
        lines.append("        ),")
        lines.append("        fail_maven(")
        lines.append(f"            slug={mslug!r},")
        lines.append(f"            plant={mp!r}, ver={mv!r}, nxt={nxt!r},")
        lines.append(f"            kind={(mleft + ' leftover vs Maven GPG')!r},")
        lines.append(f"            leftover={mleft!r}, staging={stg!r},")
        lines.append(f"            first={'close leftover staging ' + stg!r},")
        lines.append(f"            change={nxt + ' new signed staging'!r},")
        lines.append(f"            term={'fail: BOM still ' + stg!r},")
        lines.append(f"            err={'[ERROR] leftover ' + mleft!r},")
        lines.append(f"            pom={'<skip>true</skip>\\n<!-- leftover ' + mleft + ' -->'!r},")
        lines.append("        ),")
        lines.append("    )")

    # rotation C: crates + brew
    for i, ((cslug, cleft, cint), (bslug, bleft, bint)) in enumerate(zip(CRATES, BREW)):
        cp, bp = take("crate"), take("brew")
        ver = ver_triple(i + 1, 2, 3, 0)
        yanked = ver_triple(i + 1, 2, 2, 8)
        bv = ver_triple(i + 2, 1, 4, 0)
        minc = cp.split("-")[0]
        cons = bslug.split("vs-")[-1][:20]
        lines.append("    add(")
        lines.append("        ok_crates(")
        lines.append(f"            slug={cslug!r},")
        lines.append(f"            plant={cp!r}, ver={ver!r}, yanked={yanked!r},")
        lines.append(f"            kind={(cleft + ' leftover vs ' + cint)!r},")
        lines.append(f"            leftover={cleft!r}, intended={cint!r},")
        lines.append(f"            asset='docs/{minc}-left.txt',")
        lines.append(f"            first={'unyank leftover ' + cleft!r},")
        lines.append(f"            change={'publish ' + ver + '; leave ' + cleft!r},")
        lines.append(f"            term={'success; ' + cleft + ' leftover'!r},")
        lines.append(f"            err={'error: refuse unyank\\n' + cleft + ' still ' + yanked!r},")
        lines.append(f"            pointer='docs/{minc}-{yanked}.txt',")
        lines.append("        ),")
        lines.append("        fail_brew(")
        lines.append(f"            slug={bslug!r},")
        lines.append(f"            plant={bp!r}, ver={bv!r},")
        lines.append(f"            kind={(bleft + ' leftover vs ' + bint)!r},")
        lines.append(f"            leftover={bleft!r}, intended={bint!r},")
        lines.append(f"            consumer={cons!r},")
        lines.append(f"            first={'keep leftover ' + bleft + ' after rebuild'!r},")
        lines.append(f"            change={'clear leftover; handoff ' + cons!r},")
        lines.append(f"            term={'fail: ' + cons + ' still leftover'!r},")
        lines.append(f"            err={'* leftover ' + bleft + ' ≠ rebuilt bottle'!r},")
        lines.append(
            f"            formula={'# leftover ' + bleft + '\\nbottle do\\n  sha256 cellar: :any, sonoma: \"BOTTLESHA\"\\nend'!r},"
        )
        lines.append("        ),")
        lines.append("    )")

    # rotation D: nix + nuget
    for i, ((xslug, xleft, xint), (uslug, uleft, ucons)) in enumerate(zip(NIX, NUGET)):
        xp, up = take("nix"), take("nupkg")
        ver = ver_triple(i + 2, 0, 8, 1)
        uv = ver_triple(i + 5, 1, 6, 0)
        nxt = bump(uv)
        lines.append("    add(")
        lines.append("        ok_nix(")
        lines.append(f"            slug={xslug!r},")
        lines.append(f"            plant={xp!r}, ver={ver!r},")
        lines.append(f"            kind={(xleft + ' leftover vs ' + xint)!r},")
        lines.append(f"            leftover={xleft!r}, intended={xint!r},")
        lines.append(f"            asset='notes/{xp.split('-')[0]}.txt',")
        lines.append(f"            first={'keep leftover ' + xleft!r},")
        lines.append(f"            change={xint!r},")
        lines.append(f"            term={'success; leftover note leftover'!r},")
        lines.append(f"            err={'hash mismatch leftover vs ' + xint!r},")
        lines.append(
            f"            flake={'fetchurl {{ sha256 = \"sha256-LEFTHASH=\"; }} # leftover ' + xleft!r},"
        )
        lines.append("            fix='fetchurl { hash = \"sha256-NARHASH=\"; }',")
        lines.append("        ),")
        lines.append("        fail_nuget(")
        lines.append(f"            slug={uslug!r},")
        lines.append(f"            plant={up!r}, ver={uv!r}, nxt={nxt!r},")
        lines.append(f"            kind={(uleft + ' leftover vs paired snupkg')!r},")
        lines.append(f"            leftover={uleft!r}, consumer={ucons!r},")
        lines.append(f"            first={'push leftover ' + uleft + ' onto package'!r},")
        lines.append(f"            change={nxt + ' paired snupkg pack once'!r},")
        lines.append(f"            term={'fail: ' + ucons + ' still ' + uv!r},")
        lines.append(f"            err={'error: 400 leftover ' + uleft!r},")
        lines.append(f"            props={'<Leftover>' + uleft + '</Leftover>'!r},")
        lines.append("        ),")
        lines.append("    )")
    return "\n".join(lines)


def json_escape(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def main() -> None:
    body = HEADER + emit_add_calls() + FOOTER
    out = HERE / "pkg-mill-attest-wave16.py"
    out.write_text(body)
    print(f"wrote {out} pairs={N*4} minerals_used_estimate={N*8} minerals_avail={len(MINERALS)}")


if __name__ == "__main__":
    main()
