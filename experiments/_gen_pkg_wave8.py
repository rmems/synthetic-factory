#!/usr/bin/env python3
"""Generate experiments/pkg-mill-attest-wave8.py from a unique plant catalog."""
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
# unique preserve
seen = set()
mins = []
for m in MINERALS:
    if m not in seen:
        seen.add(m)
        mins.append(m)
MINERALS = mins

COSIGN = [
    ("cosign-verify-oci-referrers-api-vs-tag-digest-list", "OCI referrers API", "tag digest list"),
    ("cosign-sign-bundle-v03-json-vs-proto", "bundle v0.3 JSON", "bundle proto"),
    ("cosign-fulcio-codefresh-oidc-vs-github", "Codefresh OIDC issuer", "GitHub Fulcio issuer"),
    ("cosign-rekor-entry-kind-intoto-vs-hashedrekord", "in-toto Rekor kind", "hashedrekord kind"),
    ("cosign-verify-tsa-chain-untrusted-intermediate", "untrusted TSA intermediate", "trusted TSA chain"),
    ("cosign-policy-source-workflow-name-vs-filepath", "workflow name identity", "workflow filepath identity"),
    ("cosign-sign-kms-gcp-location-multi-region", "multi-region GCP KMS", "regional GCP KMS"),
    ("cosign-verify-identity-workflow-dispatch-vs-release", "workflow_dispatch identity", "release identity"),
    ("cosign-attach-predicate-slsa-v12-vs-v10", "SLSA predicate v1.2", "SLSA predicate v1.0"),
    ("cosign-copy-dest-registry-missing-referrer", "dest missing referrer", "copied referrer bundle"),
    ("cosign-verify-tuf-metadata-expired-offline", "expired TUF metadata", "refreshed TUF root"),
    ("cosign-sign-recursive-digest-list-partial", "partial digest list", "full index signatures"),
    ("cosign-policy-ctlog-key-id-rotated", "rotated CT log key id", "current CT log key"),
    ("cosign-fulcio-uri-san-repo-transferred", "transferred repo SAN", "current repo SAN"),
    ("cosign-verify-bundle-content-type-dsse-vs-simple", "DSSE content-type", "simple signing type"),
    ("cosign-sign-sk-piv-touch-policy-cached-slot", "cached PIV touch slot", "live PIV touch"),
    ("cosign-oidc-issuer-bitbucket-pipelines-vs-github", "Bitbucket Pipelines OIDC", "GitHub Actions OIDC"),
    ("cosign-verify-cert-notafter-clock-skew-ntp", "clock-skew notAfter", "NTP-aligned validity"),
    ("cosign-policy-untrusted-builder-id-regexp", "untrusted builder regexp", "exact builder id"),
    ("cosign-sign-payload-simple-signing-vs-intoto-spdx", "simple signing payload", "in-toto SPDX payload"),
    ("cosign-rekor-signed-checkpoint-note-missing", "missing checkpoint note", "signed checkpoint"),
    ("cosign-verify-docker-schema2-vs-oci-index", "Docker schema2 manifest", "OCI index"),
    ("cosign-sign-annotation-bundle-digest-mismatch", "annotation bundle digest", "matching subject digest"),
    ("cosign-policy-max-attestation-age-expired", "expired max attestation age", "10m max age policy"),
]

NPM = [
    ("npm-provenance-bundleDependencies-rewrites-integrity", "bundleDependencies rewrite", "bd-lock"),
    ("npm-trusted-publisher-workflow-filename-publish-prod", "workflow publish-prod.yml leftover", "prod-lock"),
    ("npm-oidc-audience-pkgs-github-vs-npmjs", "audience pkgs.github.com", "pkg-aud"),
    ("npm-provenance-prepack-mutates-files-field", "prepack files-field mutate", "prepack-lock"),
    ("npm-trusted-publisher-environment-custom-protection", "custom protection rules leftover", "prot-lock"),
    ("npm-oidc-subject-ref-pull-request-target", "pull_request_target subject", "prt-lock"),
    ("npm-provenance-optionalDependencies-native-addon", "optional native addon leftover", "opt-lock"),
    ("npm-publish-from-arc-runner-no-oidc", "ARC runner without OIDC", "arc-lock"),
    ("npm-trusted-publisher-classic-token-still-latest", "classic token latest leftover", "classic-lock"),
    ("npm-provenance-private-workspace-root-name", "private workspace root name", "wsroot-lock"),
    ("npm-oidc-permissions-id-token-read", "id-token read leftover", "idread-lock"),
    ("npm-provenance-files-glob-excludes-dist", "files glob excludes dist", "files-lock"),
    ("npm-trusted-publisher-org-renamed-scope", "renamed org scope leftover", "scope-lock"),
    ("npm-oidc-job-container-network-host", "container network host leftover", "net-lock"),
    ("npm-provenance-lockfileVersion-1-vs-3", "lockfileVersion 1 leftover", "lfv-lock"),
    ("npm-publish-access-restricted-with-provenance", "restricted access leftover", "restr-lock"),
    ("npm-trusted-publisher-workflow-call-inputs-unpinned", "unpinned workflow_call leftover", "call-lock"),
    ("npm-oidc-issuer-gitea-actions-hostname", "Gitea Actions issuer leftover", "gitea-lock"),
    ("npm-provenance-bin-wrapper-vs-pkg-subject", "bin wrapper subject leftover", "bin-lock"),
    ("npm-trusted-publisher-environment-deployment-branch", "deployment branch leftover", "deploy-lock"),
    ("npm-oidc-audience-ghcr-io-vs-registry-npmjs", "audience ghcr.io leftover", "ghcr-aud"),
    ("npm-provenance-cpu-os-optional-native-pack", "cpu/os optional native pack", "cpu-lock"),
    ("npm-publish-provenance-omit-then-retry-same-ver", "omit provenance retry leftover", "omit-lock"),
    ("npm-trusted-publisher-codespaces-oidc-unavailable", "Codespaces OIDC leftover", "cs-lock"),
]

PYPI = [
    ("pypi-trusted-publisher-workflow-path-after-move", "moved workflow path leftover", "release.yml path"),
    ("pypi-oidc-issuer-woodpecker-ci-vs-github", "Woodpecker CI issuer leftover", "GitHub OIDC issuer"),
    ("pypi-attestation-sdist-missing-from-pair", "sdist missing from pair leftover", "sdist+wheel pair"),
    ("pypi-twine-attestations-json-not-dsse", "bare JSON attestation leftover", "DSSE envelope"),
    ("pypi-trusted-publisher-environment-name-prod-typo", "environment prod typo leftover", "environment production"),
    ("pypi-oidc-job-container-without-id-token", "container without id-token leftover", "runner id-token"),
    ("pypi-hatch-index-testpypi-url-leftover", "hatch testpypi index leftover", "prod PyPI index"),
    ("pypi-uv-publish-skip-trusted-publishing", "uv skip trusted publishing leftover", "uv trusted publishing"),
    ("pypi-poetry-pypi-token-keyring-leftover", "poetry keyring token leftover", "OIDC trusted publisher"),
    ("pypi-oidc-subject-workflow-ref-tags-vstar", "workflow ref tags/v* leftover", "exact tag ref"),
    ("pypi-attestation-pep740-subject-missing-digest", "PEP 740 subject missing digest", "subject digest pep740"),
    ("pypi-trusted-publisher-project-name-normalized", "unnormalized project name leftover", "normalized PyPI name"),
    ("pypi-oidc-issuer-buildkite-agent-vs-github", "Buildkite agent issuer leftover", "GitHub OIDC issuer"),
    ("pypi-twine-keyring-backend-leftover", "twine keyring backend leftover", "OIDC trusted publishing"),
    ("pypi-trusted-publisher-workflow-call-unpinned-ref", "unpinned workflow_call leftover", "sha-pinned reusable workflow"),
    ("pypi-oidc-job-services-redis-sidecar", "redis sidecar leftover", "bare runner OIDC"),
    ("pypi-attestation-wheel-abi3-vs-cp312", "abi3 wheel leftover", "cp312 wheel attestation"),
    ("pypi-hatch-user-pass-vs-trusted-publishing", "hatch user/pass leftover", "hatch trusted publishing"),
    ("pypi-uv-publish-check-url-legacy-pypi", "uv check-url legacy leftover", "uv check-url pypi.org"),
    ("pypi-poetry-http-basic-vs-oidc-xor", "poetry http-basic leftover", "poetry OIDC"),
    ("pypi-trusted-publisher-environment-wait-timer-prod", "environment wait_timer leftover", "immediate environment"),
    ("pypi-oidc-issuer-codeberg-ci-vs-github", "Codeberg CI issuer leftover", "GitHub OIDC issuer"),
    ("pypi-attestation-attestations-dir-sdist-only-pair", "sdist-only attestations dir leftover", "wheel+sdist attestations"),
    ("pypi-twine-skip-attestation-flag-ci-leftover", "twine skip-attestation leftover", "twine attestations required"),
]

MAVEN = [
    ("maven-gpg-sign-javadoc-classifier-missing", "javadoc classifier unsigned leftover", "javadoc-stg"),
    ("maven-central-portal-publishing-type-user-managed-hang", "user-managed portal hang leftover", "portal-hang"),
    ("maven-gpg-keyring-pinentry-loopback-missing", "pinentry loopback missing leftover", "pin-stg"),
    ("maven-gpg-passphrase-env-vs-settings-xor", "passphrase env XOR settings leftover", "xor-stg"),
    ("maven-central-bundle-missing-sources-checksum", "sources checksum missing leftover", "srcsum-stg"),
    ("maven-gpg-useagent-loopback-pinentry-mode", "useagent loopback leftover", "loop-stg"),
    ("maven-ossrh-staging-profile-id-retired", "retired OSSRH profile leftover", "retired-stg"),
    ("maven-gpg-sign-attached-binary-vs-armor", "binary attached leftover", "armor-stg"),
    ("maven-central-publisher-api-namespace-rejected", "namespace rejected leftover", "ns-stg"),
    ("maven-gpg-digest-sha1-vs-sha256-policy", "SHA1 digest leftover", "sha-stg"),
    ("maven-settings-gpg-executable-homebrew-path", "homebrew gpg path leftover", "hb-stg"),
    ("maven-gpg-skip-attached-artifacts-asc", "skip attached artifacts leftover", "skip-stg"),
    ("maven-gpg-sign-tests-sources-both-missing", "tests+sources unsigned leftover", "ts-stg"),
    ("maven-central-portal-poll-interval-vs-timeout", "portal poll interval leftover", "poll-stg"),
    ("maven-gpg-homedir-relative-vs-absolute", "relative gnupg homedir leftover", "home-stg"),
    ("maven-gpg-bestpractices-plugin-vs-maven-gpg", "bestpractices plugin leftover", "bp-stg"),
    ("maven-central-user-token-vs-portal-oidc", "user token leftover", "oidc-stg"),
    ("maven-gpg-signer-bc-vs-gpg-executable", "BC signer leftover", "bc-stg"),
    ("maven-settings-server-central-vs-ossrh-id", "OSSRH server id leftover", "sid-stg"),
    ("maven-gpg-exclude-classifiers-tests-leftover", "exclude classifiers leftover", "excl-stg"),
    ("maven-central-bundle-missing-module-md5", "module md5 missing leftover", "md5-stg"),
    ("maven-gpg-sign-javadoc-and-sources-xor", "javadoc XOR sources leftover", "xor2-stg"),
    ("maven-ossrh-s01-host-after-portal-cutover", "s01 host leftover after portal", "s01-stg"),
    ("maven-gpg-passphrase-server-id-mismatch", "passphrase server id leftover", "psid-stg"),
]

CRATES = [
    ("crates-yank-vs-cargo-outdated-report", "cargo-outdated report leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-deny-bans", "cargo-deny bans leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-audit-db", "cargo-audit db leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-geiger-report", "cargo-geiger report leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-bloat-cache", "cargo-bloat cache leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-llvm-lines", "cargo-llvm-lines leftover", "sparse yank index"),
    ("crates-yank-vs-crates-io-feed-json", "crates.io feed.json leftover", "sparse yank index"),
    ("crates-yank-vs-lib-rs-readme-render", "lib.rs readme render leftover", "sparse yank index"),
    ("crates-yank-vs-docsrs-source-browser", "docs.rs source browser leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-release-index", "cargo-release index leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-clone-cache", "cargo-clone cache leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-info-registry", "cargo info registry leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-tree-duplicates", "cargo-tree duplicates leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-minimal-versions", "cargo minimal-versions leftover", "sparse yank index"),
    ("crates-yank-vs-crates-io-api-v1-downloads", "crates.io api v1 downloads leftover", "sparse yank index"),
    ("crates-yank-vs-lib-rs-owners-page", "lib.rs owners page leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-public-api-diff", "cargo-public-api diff leftover", "sparse yank index"),
    ("crates-yank-vs-rustdoc-scrape-examples", "rustdoc scrape-examples leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-dist-hosting-index", "cargo-dist hosting leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-semver-checks-release", "cargo-semver-checks release leftover", "sparse yank index"),
    ("crates-yank-vs-crates-io-trustpub-page", "crates.io trustpub page leftover", "sparse yank index"),
    ("crates-yank-vs-lib-rs-reverse-deps-atom", "lib.rs reverse-deps atom leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-show-asm-cache-alt", "cargo-show-asm alt cache leftover", "sparse yank index"),
    ("crates-yank-vs-docsrs-rustdoc-json-v2", "docs.rs rustdoc json v2 leftover", "sparse yank index"),
]

BREW = [
    ("homebrew-bottle-rebuild-vs-uses-from-macos-bison", "uses_from_macos bison leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-depends-on-macos-symbol", "depends_on macos leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-head-branch", "head branch leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-patch-data-eof", "patch DATA leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-resource-url-only", "resource url leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-keg-only-because", "keg_only because leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-disable-because", "disable! leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-deprecate-replacement", "deprecate replacement leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-service-keep-alive", "service keep_alive leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-std-meson-args", "std_meson_args leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-on-sonoma-block", "on_sonoma leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-depends-on-arch-intel", "depends_on arch intel leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-tap-migration", "tap migration leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-compiler-gcc", "fails_with gcc leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-cxxstdlib-check", "cxxstdlib check leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-post-install-keg", "post_install leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-caveats-kext", "caveats kext leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-depends-on-java", "depends_on java leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-option-cxx11", "option cxx11 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-needs-openmp", "needs openmp leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-on-arm-block", "on_arm leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-version-scheme", "version_scheme leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-revision-bump", "revision leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-stable-url-only", "stable url leftover", "rebuilt bottle sha"),
]

NIX = [
    ("nix-fetchFromBitbucket-vs-nar", "Bitbucket file hash leftover", "NAR of Bitbucket archive"),
    ("nix-fetchzip-stripRoot-false-vs-nar", "stripRoot false leftover", "NAR of stripped zip"),
    ("nix-fetchTarball-flake-vs-nar", "fetchTarball flake leftover", "NAR of tarball"),
    ("nix-fetchPypi-pname-vs-nar", "fetchPypi pname leftover", "NAR of PyPI sdist"),
    ("nix-fetchCrate-vs-nar", "fetchCrate leftover", "NAR of crates.io crate"),
    ("nix-fetchFromGitiles-format-vs-nar", "Gitiles format leftover", "NAR of Gitiles archive"),
    ("nix-fetchsvn-peg-revision-vs-nar", "svn peg revision leftover", "NAR of svn export"),
    ("nix-fetchhg-rev-vs-nar", "hg rev leftover", "NAR of hg archive"),
    ("nix-fetchcvs-module-vs-nar", "CVS module leftover", "NAR of CVS export"),
    ("nix-fetchFromAzureDevOps-project-vs-nar", "Azure DevOps project leftover", "NAR of Azure archive"),
    ("nix-fetchgit-fetchSubmodules-vs-nar", "fetchSubmodules leftover", "NAR of no-submodules checkout"),
    ("nix-fetchurl-curlOptsList-vs-nar", "curlOptsList leftover", "NAR of fetched url"),
    ("nix-fetchFromGitHub-sparseCheckout-patterns-vs-nar", "sparseCheckout patterns leftover", "NAR of sparse archive"),
    ("nix-fetchgit-preFetch-hook-vs-nar", "preFetch hook leftover", "NAR of plain fetchgit"),
    ("nix-fetchFromGitLab-protocol-ssh-vs-nar", "GitLab ssh protocol leftover", "NAR of https archive"),
    ("nix-fetchgit-lfs-files-vs-nar", "git LFS files leftover", "NAR of LFS-smudged tree"),
    ("nix-fetchFromGitea-token-header-vs-nar", "Gitea token header leftover", "NAR of public Gitea archive"),
    ("nix-fetchurl-downloadToTemp-vs-nar", "downloadToTemp leftover", "NAR of fetchurl store path"),
    ("nix-fetchFromCgit-snapshot-vs-nar", "cgit snapshot leftover", "NAR of cgit archive"),
    ("nix-fetchgit-shallowSince-vs-nar", "shallowSince leftover", "NAR of full fetchgit"),
    ("nix-fetchFromSourcehut-rev-vs-nar", "Sourcehut rev leftover", "NAR of sourcehut archive"),
    ("nix-fetchzip-extension-tbz-vs-nar", "tbz extension leftover", "NAR of unzipped tree"),
    ("nix-builtins-fetchTree-vs-nar", "builtins.fetchTree leftover", "NAR of fetchTree locked"),
    ("nix-fetchgit-sparseCheckout-nonCone-vs-nar", "nonCone sparse leftover", "NAR of cone sparse checkout"),
]

NUGET = [
    ("nuget-snupkg-embed-untracked-sources-flag", "EmbedUntrackedSources leftover", "untracked-src"),
    ("nuget-snupkg-sourcelink-azure-devops-server-vs-cloud", "Azure DevOps Server SourceLink leftover", "azdo-server"),
    ("nuget-snupkg-deterministic-pathmap-missing", "missing PathMap leftover", "pathmap-miss"),
    ("nuget-snupkg-debug-type-full-vs-portable", "DebugType full leftover", "full-debug"),
    ("nuget-snupkg-include-symbols-snupkg-and-pdb", "IncludeSymbols dual leftover", "dual-sym"),
    ("nuget-snupkg-sourcelink-sourcehut-vs-github", "SourceLink sourcehut leftover", "srht-debug"),
    ("nuget-snupkg-continuous-integration-build-flag", "ContinuousIntegrationBuild leftover", "cibuild"),
    ("nuget-snupkg-embed-all-sources-without-sourcelink", "EmbedAllSources no SourceLink leftover", "embed-nosl"),
    ("nuget-snupkg-publish-gitlab-generic-vs-nuget", "GitLab generic package leftover", "gl-generic"),
    ("nuget-snupkg-pdb-checksum-algorithm-sha256-vs-sha1", "PDB checksum SHA1 leftover", "pdb-sha1"),
    ("nuget-snupkg-sourcelink-gogs-vs-github", "SourceLink gogs leftover", "gogs-debug"),
    ("nuget-snupkg-embedded-files-filter-exclude", "embedded files filter leftover", "embed-filt"),
    ("nuget-snupkg-source-root-unix-vs-windows", "unix SourceRoot leftover", "unix-root"),
    ("nuget-snupkg-symbolpackageformat-snupkg-vs-symbols-nupkg", "symbols.nupkg format leftover", "sym-fmt"),
    ("nuget-snupkg-repository-branch-vs-commit", "RepositoryBranch leftover", "repo-branch"),
    ("nuget-snupkg-sourcelink-codeberg-vs-github", "SourceLink codeberg leftover", "cb-debug"),
    ("nuget-snupkg-publish-myget-vs-nuget-org", "MyGet push leftover", "myget-push"),
    ("nuget-snupkg-portable-pdb-age-mismatch", "portable PDB age leftover", "pdb-age"),
    ("nuget-snupkg-sourcelink-gitweb-vs-github", "SourceLink gitweb leftover", "gitweb-debug"),
    ("nuget-snupkg-source-link-mapped-path", "SourceLink mapped path leftover", "map-path"),
    ("nuget-snupkg-publish-github-packages-gpr-v3", "GPR v3 leftover", "gpr-v3"),
    ("nuget-snupkg-debug-type-embedded-vs-portable", "DebugType embedded leftover", "embed-dbg"),
    ("nuget-snupkg-include-source-revision-in-informational", "IncludeSourceRevision leftover", "src-rev"),
    ("nuget-snupkg-sourcelink-forgejo-vs-github", "SourceLink forgejo leftover", "fj-debug"),
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
"""Unique mill: package-release-factory attestation wave-8 (r514+).

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

CATALOG_FIRST = 514
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
        raise SystemExit("dup slug or plant in attest wave8 catalog")
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
    out = HERE / "pkg-mill-attest-wave8.py"
    out.write_text(body)
    print(f"wrote {out} pairs={N*4} minerals_used_estimate={N*8} minerals_avail={len(MINERALS)}")


if __name__ == "__main__":
    main()
