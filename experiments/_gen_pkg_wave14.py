#!/usr/bin/env python3
"""Generate experiments/pkg-mill-attest-wave14.py from a unique plant catalog."""
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
    ("cosign-verify-oci-referrer-os-vs-type", "referrer os leftover", "OCI referrer type"),
    ("cosign-sign-bundle-staging-vs-prod-dsse", "staging bundle leftover", "prod DSSE bundle"),
    ("cosign-fulcio-azure-oidc-vs-github", "Azure OIDC leftover", "GitHub Fulcio issuer"),
    ("cosign-rekor-entry-kind-rfc3161-vs-intoto", "RFC3161 leftover", "in-toto Rekor kind"),
    ("cosign-verify-tsa-root-expired", "expired TSA root leftover", "current TSA root"),
    ("cosign-policy-identity-job-name-vs-path", "job name leftover", "workflow path identity"),
    ("cosign-sign-kms-aws-mrk-vs-alias", "AWS MRK leftover", "AWS alias key"),
    ("cosign-verify-identity-release-published-vs-tag", "release published leftover", "tag identity"),
    ("cosign-attach-predicate-spdx-vs-slsa", "SPDX leftover", "SLSA predicate"),
    ("cosign-copy-signature-referrer-vs-tag", "sig referrer leftover", "tag signature"),
    ("cosign-verify-tuf-delegations-expired", "expired TUF delegations leftover", "refreshed TUF delegations"),
    ("cosign-sign-recursive-sbom-attest-partial", "partial SBOM attest leftover", "full index SBOM"),
    ("cosign-policy-ctlog-pubkey-stale-pem", "stale CT PEM leftover", "current CT PEM"),
    ("cosign-fulcio-uri-san-repo-mirror", "mirror repo SAN leftover", "canonical repo SAN"),
    ("cosign-verify-bundle-hash-algo-sha224-vs-sha256", "sha224 leftover", "sha256 payload algo"),
    ("cosign-sign-sk-piv-slot-83-vs-9a", "PIV slot 83 leftover", "PIV slot 9a"),
    ("cosign-oidc-issuer-okta-vs-github", "Okta leftover", "GitHub Actions OIDC"),
    ("cosign-verify-cert-notbefore-skew-hours", "notBefore hours leftover", "NTP-aligned notBefore"),
    ("cosign-policy-builder-id-tag-mismatch", "builder tag leftover", "exact builder id"),
    ("cosign-sign-payload-intoto-cdx-json", "in-toto CDX-JSON leftover", "in-toto SLSA payload"),
    ("cosign-rekor-inclusion-proof-entry-uuid", "entry uuid leftover", "signed entry uuid"),
    ("cosign-verify-oci-index-feature-filter", "feature filter leftover", "full OCI index"),
    ("cosign-sign-annotation-predicate-digest-set", "predicate digest leftover", "matching digest set"),
    ("cosign-policy-max-cert-lifetime-minutes", "max cert minutes leftover", "policy minutes"),
]

NPM = [
    ("npm-provenance-bundleDependencies-workspace-root", "workspace root leftover", "wsroot-lock"),
    ("npm-trusted-publisher-workflow-filename-tag-yml", "workflow tag.yml leftover", "tag-lock"),
    ("npm-oidc-audience-npmjs-io", "audience npmjs.io leftover", "nio-aud"),
    ("npm-provenance-postpack-mutates-tarball", "postpack leftover", "ppack-lock"),
    ("npm-trusted-publisher-environment-required-teams", "required teams leftover", "rteam-lock"),
    ("npm-oidc-subject-ref-page-build", "page_build leftover", "page-lock"),
    ("npm-provenance-optionalDependencies-libc-android", "android libc leftover", "and-lock"),
    ("npm-publish-from-kata-runner-no-oidc", "kata runner without OIDC leftover", "kata-lock"),
    ("npm-trusted-publisher-refresh-token-still-latest", "refresh token leftover", "refr-lock"),
    ("npm-provenance-private-workspace-glob", "workspace glob leftover", "wglob-lock"),
    ("npm-oidc-permissions-id-token-write-security", "security write leftover", "secw-lock"),
    ("npm-provenance-files-field-includes-examples", "files includes examples leftover", "ex-lock"),
    ("npm-trusted-publisher-org-sso-oidc", "org SSO OIDC leftover", "ssoo-lock"),
    ("npm-oidc-job-container-user-nobody", "container nobody leftover", "cnob-lock"),
    ("npm-provenance-lockfileVersion-3-vs-9", "lockfileVersion 3 leftover", "lf39-lock"),
    ("npm-publish-access-restricted-public-scope", "restricted public leftover", "rpub-lock"),
    ("npm-trusted-publisher-workflow-call-inputs-map", "workflow_call inputs map leftover", "wcim-lock"),
    ("npm-oidc-issuer-appveyor-vs-github", "AppVeyor issuer leftover", "appv-lock"),
    ("npm-provenance-bin-field-path-subject", "bin path leftover", "binp-lock"),
    ("npm-trusted-publisher-environment-wait-timer-90", "wait_timer 90 leftover", "wt90-lock"),
    ("npm-oidc-audience-yarnpkg-org", "audience yarnpkg.org leftover", "yorg-lock"),
    ("npm-provenance-os-cpu-optional-freebsd-x64", "freebsd-x64 leftover", "fbsd-lock"),
    ("npm-publish-provenance-omit-then-file", "omit then file leftover", "otf-lock"),
    ("npm-trusted-publisher-self-hosted-ephemeral-no-oidc", "ephemeral runner leftover", "eph-lock"),
]

PYPI = [
    ("pypi-trusted-publisher-workflow-path-apps-dir", "apps workflow leftover", "release.yml path"),
    ("pypi-oidc-issuer-sourcehut-builds-vs-github", "Sourcehut builds leftover", "GitHub OIDC issuer"),
    ("pypi-attestation-platlib-missing-sdist", "platlib leftover", "sdist+wheel pair"),
    ("pypi-twine-attestations-toml-not-dsse", "TOML attestation leftover", "DSSE envelope"),
    ("pypi-trusted-publisher-environment-name-beta-typo", "environment beta leftover", "environment production"),
    ("pypi-oidc-job-container-id-token-request-none", "container request leftover", "runner id-token"),
    ("pypi-hatch-index-google-artifact-url-leftover", "hatch GAR leftover", "prod PyPI index"),
    ("pypi-uv-publish-trusted-publishing-required", "uv required leftover", "uv trusted publishing"),
    ("pypi-poetry-keyring-backend-pass-leftover", "poetry pass leftover", "OIDC trusted publisher"),
    ("pypi-oidc-subject-workflow-ref-heads-hotfix", "workflow ref heads/hotfix leftover", "exact tag ref"),
    ("pypi-attestation-pep740-cert-missing", "PEP 740 cert leftover", "pep740 cert"),
    ("pypi-trusted-publisher-project-name-unicode", "unicode project leftover", "normalized PyPI name"),
    ("pypi-oidc-issuer-woodpecker-vs-github", "Woodpecker leftover", "GitHub OIDC issuer"),
    ("pypi-twine-config-file-yaml-leftover", "twine yaml leftover", "OIDC trusted publishing"),
    ("pypi-trusted-publisher-workflow-call-ref-v3", "workflow_call v3 leftover", "sha-pinned reusable workflow"),
    ("pypi-oidc-job-services-elasticsearch-sidecar", "elasticsearch sidecar leftover", "bare runner OIDC"),
    ("pypi-attestation-wheel-manylinux_2_17-vs-2-28", "manylinux_2_17 leftover", "manylinux_2_28 attestation"),
    ("pypi-hatch-index-file-token-vs-oidc", "hatch file token leftover", "hatch trusted publishing"),
    ("pypi-uv-publish-check-url-gar-legacy", "uv GAR leftover", "uv check-url pypi.org"),
    ("pypi-poetry-pypi-token-keyring-file-vs-oidc", "poetry keyring file leftover", "poetry OIDC"),
    ("pypi-trusted-publisher-environment-required-reviewers-4", "four reviewers leftover", "immediate environment"),
    ("pypi-oidc-issuer-buildkite-vs-github", "Buildkite leftover", "GitHub OIDC issuer"),
    ("pypi-attestation-attestations-dir-protobuf-pair", "protobuf leftover", "wheel+sdist attestations"),
    ("pypi-twine-skip-existing-with-dir", "skip-existing with dir leftover", "twine attestations required"),
]

MAVEN = [
    ("maven-gpg-sign-site-only-missing-jar", "site-only leftover", "site-stg"),
    ("maven-central-portal-publishing-type-batch-hang", "batch hang leftover", "bat-stg"),
    ("maven-gpg-keyring-agent-display-stale", "stale display leftover", "disp-stg"),
    ("maven-gpg-passphrase-stdin-xor-env", "passphrase stdin leftover", "psin-stg"),
    ("maven-central-bundle-missing-site-checksum", "site checksum leftover", "sitec-stg"),
    ("maven-gpg-useagent-true-pinentry-emacs", "pinentry emacs leftover", "emac-stg"),
    ("maven-ossrh-staging-profile-id-locked", "locked profile leftover", "lock-stg"),
    ("maven-gpg-sign-asc-armor-charset-utf8", "armor utf8 leftover", "utf8-stg"),
    ("maven-central-publisher-api-namespace-blocked", "blocked namespace leftover", "blk-stg"),
    ("maven-gpg-digest-sha3-vs-sha256-policy", "SHA3 leftover", "sha3-stg"),
    ("maven-settings-gpg-executable-portage-path", "portage leftover", "port-stg"),
    ("maven-gpg-skip-site-asc", "skip site leftover", "ssite-stg"),
    ("maven-gpg-sign-site-only-missing-modules", "site modules leftover", "smod-stg"),
    ("maven-central-portal-deployment-status-validating", "validating leftover", "val-stg"),
    ("maven-gpg-homedir-gnupg1-vs-absolute", "gnupg1 leftover", "g1-stg"),
    ("maven-gpg-sign-plugin-skip-site", "skip site plugin leftover", "sks-stg"),
    ("maven-central-user-token-disabled", "disabled token leftover", "disab-stg"),
    ("maven-gpg-signer-class-bc-jdk21", "BC jdk21 leftover", "bc21-stg"),
    ("maven-settings-server-central-staging-id", "central staging leftover", "cstg-stg"),
    ("maven-gpg-exclude-classifiers-site", "exclude site leftover", "exs-stg"),
    ("maven-central-bundle-missing-module-sha384", "module sha384 leftover", "s384-stg"),
    ("maven-gpg-sign-attached-site-missing", "attached site leftover", "asit-stg"),
    ("maven-ossrh-s01-host-after-portal-apex", "s01 apex leftover", "apex-stg"),
    ("maven-gpg-passphrase-server-id-releases-old", "old releases passphrase leftover", "rold-stg"),
]

CRATES = [
    ("crates-yank-vs-cargo-outdated-quiet", "cargo-outdated quiet leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-deny-licenses-cfg", "cargo-deny licenses cfg leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-audit-stale", "cargo-audit stale leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-cyclonedx-v1-2", "cargo-cyclonedx v1.2 leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-modules-unused", "cargo-modules unused leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-shear-unused-workspace", "cargo-shear unused-workspace leftover", "sparse yank index"),
    ("crates-yank-vs-crates-io-api-v2-badges", "crates.io api v2 badges leftover", "sparse yank index"),
    ("crates-yank-vs-lib-rs-shields", "lib.rs shields leftover", "sparse yank index"),
    ("crates-yank-vs-docsrs-source-tar", "docs.rs source tar leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-release-pre-release", "cargo-release pre leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-clone-offline", "cargo-clone offline leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-info-authors", "cargo info authors leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-tree-no-dedupe", "cargo-tree no-dedupe leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-minimal-versions-published", "minimal-versions published leftover", "sparse yank index"),
    ("crates-yank-vs-crates-io-api-v1-recent", "crates.io api v1 recent leftover", "sparse yank index"),
    ("crates-yank-vs-lib-rs-shields-svg", "lib.rs shields svg leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-public-api-diff-csv", "cargo-public-api csv leftover", "sparse yank index"),
    ("crates-yank-vs-rustdoc-scrape-examples-rst", "rustdoc scrape rst leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-dist-generate", "cargo-dist generate leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-semver-checks-baseline-bin", "semver-checks bin leftover", "sparse yank index"),
    ("crates-yank-vs-crates-io-trustpub-svg", "crates.io trustpub svg leftover", "sparse yank index"),
    ("crates-yank-vs-lib-rs-sitemap", "lib.rs sitemap leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-show-asm-wasm", "cargo-show-asm wasm leftover", "sparse yank index"),
    ("crates-yank-vs-docsrs-rustdoc-json-local", "docs.rs rustdoc local leftover", "sparse yank index"),
]

BREW = [
    ("homebrew-bottle-rebuild-vs-uses-from-macos-icu4c", "uses_from_macos icu4c leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-depends-on-macos-mojave", "depends_on macos mojave leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-head-spec-revision", "head revision leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-patch-data-p5", "patch DATA p5 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-resource-version", "resource version leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-keg-only-because-provided-by-macos", "keg_only provided leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-disable-because-fails-with", "disable fails leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-deprecate-because-renamed", "deprecate renamed leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-service-keep-alive-success", "service success leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-std-nim-args", "std_nim leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-on-big-sur-block", "on_big_sur leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-depends-on-arch-s390x", "depends_on arch s390x leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-tap-migrations-toml", "tap_migrations toml leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-fails-with-gcc-10", "fails_with gcc 10 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-cxxstdlib-check-libc", "cxxstdlib libc leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-post-install-chmod-x", "post_install chmod leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-caveats-pfctl", "caveats pfctl leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-depends-on-ruby", "depends_on ruby leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-option-with-debug", "option debug leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-needs-sse2", "needs sse2 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-on-linux-freebsd", "on_linux freebsd leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-version-scheme-five", "version_scheme 5 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-revision-two", "revision 2 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-stable-url-sha512", "stable sha512 leftover", "rebuilt bottle sha"),
]

NIX = [
    ("nix-fetchFromBitbucket-slug-vs-nar", "Bitbucket slug leftover", "NAR of Bitbucket archive"),
    ("nix-fetchzip-sri-vs-nar", "fetchzip sri leftover", "NAR of zip"),
    ("nix-fetchTarball-sri-vs-nar", "fetchTarball sri leftover", "NAR of tarball"),
    ("nix-fetchPypi-sri-vs-nar", "fetchPypi sri leftover", "NAR of PyPI sdist"),
    ("nix-fetchCrate-sri-vs-nar", "fetchCrate sri leftover", "NAR of crates.io crate"),
    ("nix-fetchFromGitiles-sri-vs-nar", "Gitiles sri leftover", "NAR of Gitiles archive"),
    ("nix-fetchsvn-sri-vs-nar", "svn sri leftover", "NAR of svn export"),
    ("nix-fetchhg-sri-vs-nar", "hg sri leftover", "NAR of hg archive"),
    ("nix-fetchcvs-sri-vs-nar", "CVS sri leftover", "NAR of CVS export"),
    ("nix-fetchFromAzureDevOps-sri-vs-nar", "Azure sri leftover", "NAR of Azure archive"),
    ("nix-fetchgit-fetchTags-true-vs-nar", "tags leftover", "NAR of checkout"),
    ("nix-fetchurl-sri-vs-nar-url", "fetchurl sri leftover", "NAR of fetched url"),
    ("nix-fetchFromGitHub-sri-vs-nar", "GitHub sri leftover", "NAR of archive"),
    ("nix-fetchgit-unshallow-vs-nar", "unshallow leftover", "NAR of fetchgit"),
    ("nix-fetchFromGitLab-sri-vs-nar", "GitLab sri leftover", "NAR of https archive"),
    ("nix-fetchgit-deref-vs-nar", "deref leftover", "NAR of pinned fetchgit"),
    ("nix-fetchFromGitea-sri-vs-nar", "Gitea sri leftover", "NAR of public Gitea archive"),
    ("nix-fetchurl-md5-vs-nar-store", "fetchurl md5 leftover", "NAR of fetchurl store path"),
    ("nix-fetchFromCgit-sri-vs-nar", "cgit sri leftover", "NAR of cgit archive"),
    ("nix-fetchgit-peel-vs-nar", "peel leftover", "NAR of pinned fetchgit"),
    ("nix-fetchFromSourcehut-sri-vs-nar", "Sourcehut sri leftover", "NAR of sourcehut archive"),
    ("nix-fetchzip-sri-vs-nar-root", "fetchzip sri leftover", "NAR of zip"),
    ("nix-builtins-storePath-vs-nar", "builtins.storePath leftover", "NAR of store path"),
    ("nix-fetchgit-fetchLFS-true-vs-nar", "LFS leftover", "NAR of checkout"),
]

NUGET = [
    ("nuget-snupkg-embed-untracked-sources-debug", "EmbedUntrackedSources debug leftover", "untracked-dbg"),
    ("nuget-snupkg-sourcelink-azure-repos-tfs-vs-cloud", "Azure Repos TFS leftover", "azdo-tfs"),
    ("nuget-snupkg-deterministic-pathmap-env", "env PathMap leftover", "pathmap-env"),
    ("nuget-snupkg-debug-type-embedded-vs-none", "DebugType embedded leftover", "emb-none"),
    ("nuget-snupkg-include-symbols-snupkg-true-no-docs", "IncludeSymbols no docs leftover", "sym-nodocs"),
    ("nuget-snupkg-sourcelink-bitbucket-pipeline-vs-github", "Bitbucket pipeline leftover", "bb-pipe"),
    ("nuget-snupkg-continuous-integration-build-true-local-ci", "CI local leftover", "cilocal2"),
    ("nuget-snupkg-embed-all-sources-false-no-link", "EmbedAllSources false leftover", "embed-fnl"),
    ("nuget-snupkg-publish-gitlab-nuget-v5", "GitLab nuget v5 leftover", "gl-n5"),
    ("nuget-snupkg-pdb-checksum-algorithm-crc32", "PDB checksum crc32 leftover", "pdb-crc"),
    ("nuget-snupkg-sourcelink-gitea-actions-vs-github", "Gitea actions leftover", "gitea-act"),
    ("nuget-snupkg-embedded-files-filter-negate", "embedded files negate leftover", "embed-neg"),
    ("nuget-snupkg-source-root-subst-drive", "subst SourceRoot leftover", "subst-root"),
    ("nuget-snupkg-symbolpackageformat-symbols-vs-none", "symbols vs none leftover", "fmt-sym"),
    ("nuget-snupkg-repository-url-vs-type", "RepositoryUrl leftover", "repo-ut"),
    ("nuget-snupkg-sourcelink-codeberg-actions-vs-github", "Codeberg actions leftover", "cb-act"),
    ("nuget-snupkg-publish-github-packages-nuget-v6", "GPR nuget v6 leftover", "gpr-n6"),
    ("nuget-snupkg-portable-pdb-guid-zeros", "portable PDB zeros leftover", "pdb-zero"),
    ("nuget-snupkg-sourcelink-sourcehut-builds-vs-github", "sourcehut builds leftover", "srht-bld"),
    ("nuget-snupkg-source-link-mapped-path-subst", "subst mapped path leftover", "subst-map"),
    ("nuget-snupkg-publish-myget-v5-vs-nuget-org", "MyGet v5 leftover", "myget-v5"),
    ("nuget-snupkg-debug-type-full-vs-none", "DebugType full leftover", "full-none"),
    ("nuget-snupkg-include-source-revision-true-ci", "IncludeSourceRevision ci leftover", "src-tci"),
    ("nuget-snupkg-sourcelink-forgejo-actions-vs-github", "Forgejo actions leftover", "fj-act"),
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
"""Unique mill: package-release-factory attestation wave-14 (r1124+).

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

CATALOG_FIRST = 1124
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
        raise SystemExit("dup slug or plant in attest wave14 catalog")
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
    out = HERE / "pkg-mill-attest-wave14.py"
    out.write_text(body)
    print(f"wrote {out} pairs={N*4} minerals_used_estimate={N*8} minerals_avail={len(MINERALS)}")


if __name__ == "__main__":
    main()
