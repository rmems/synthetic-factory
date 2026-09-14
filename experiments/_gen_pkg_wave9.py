#!/usr/bin/env python3
"""Generate experiments/pkg-mill-attest-wave9.py from a unique plant catalog."""
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
    ("cosign-verify-referrer-artifact-type-vs-oci", "referrer artifactType leftover", "OCI referrer type"),
    ("cosign-sign-bundle-media-type-dsse-envelope", "bundle mediaType leftover", "DSSE envelope mediaType"),
    ("cosign-fulcio-woodpecker-oidc-vs-github", "Woodpecker OIDC leftover", "GitHub Fulcio issuer"),
    ("cosign-rekor-entry-kind-rfc3161-vs-hashedrekord", "RFC3161 Rekor kind leftover", "hashedrekord kind"),
    ("cosign-verify-tsa-chain-cross-signed", "cross-signed TSA leftover", "direct TSA chain"),
    ("cosign-policy-identity-job-workflow-name", "job workflow name leftover", "workflow path identity"),
    ("cosign-sign-kms-azure-vault-uri-mismatch", "Azure vault URI leftover", "matching Azure KMS URI"),
    ("cosign-verify-identity-merge-group-vs-tag", "merge_group identity leftover", "tag identity"),
    ("cosign-attach-predicate-vuln-vs-slsa", "vuln predicate leftover", "SLSA predicate"),
    ("cosign-copy-signature-layer-media-type", "sig layer mediaType leftover", "matching layer mediaType"),
    ("cosign-verify-tuf-delegated-target-stale", "stale TUF delegated target", "refreshed delegated target"),
    ("cosign-sign-recursive-multiarch-partial-index", "partial multiarch leftover", "full multiarch index"),
    ("cosign-policy-ctlog-shard-pubkey", "CT shard pubkey leftover", "current CT shard key"),
    ("cosign-fulcio-uri-san-org-moved", "moved org SAN leftover", "current org SAN"),
    ("cosign-verify-bundle-payload-hash-algo", "payload hash algo leftover", "policy hash algo"),
    ("cosign-sign-sk-piv-pin-policy-cached", "cached PIV PIN leftover", "live PIV PIN"),
    ("cosign-oidc-issuer-harness-vs-github", "Harness OIDC leftover", "GitHub Actions OIDC"),
    ("cosign-verify-cert-notbefore-clock-skew", "notBefore clock-skew leftover", "NTP-aligned notBefore"),
    ("cosign-policy-builder-id-digest-set", "builder-id digestSet leftover", "exact builder id"),
    ("cosign-sign-payload-intoto-cyclonedx", "in-toto CDX leftover", "in-toto SLSA payload"),
    ("cosign-rekor-inclusion-proof-missing-root", "missing inclusion root leftover", "signed inclusion root"),
    ("cosign-verify-oci-index-manifest-list", "manifest list leftover", "OCI index"),
    ("cosign-sign-annotation-predicate-digest", "annotation predicate leftover", "matching predicate digest"),
    ("cosign-policy-max-cert-chain-depth", "max cert chain depth leftover", "policy chain depth"),
]

NPM = [
    ("npm-provenance-bundleDependencies-optional-native", "optional native bundleDeps leftover", "bnd-lock"),
    ("npm-trusted-publisher-workflow-filename-release-yml", "workflow release.yml leftover", "rel-lock"),
    ("npm-oidc-audience-npmjs-org-vs-registry", "audience npmjs.org leftover", "aud-lock"),
    ("npm-provenance-prepublishOnly-mutates-tarball", "prepublishOnly mutate leftover", "prepub-lock"),
    ("npm-trusted-publisher-environment-required-reviewers", "required reviewers leftover", "rev-lock"),
    ("npm-oidc-subject-ref-workflow-dispatch", "workflow_dispatch subject leftover", "wd-lock"),
    ("npm-provenance-optionalDependencies-cpu-os-pair", "cpu/os optional pair leftover", "pair-lock"),
    ("npm-publish-from-k8s-runner-no-oidc", "k8s runner without OIDC leftover", "k8s-lock"),
    ("npm-trusted-publisher-automation-token-still-latest", "automation token leftover", "auto-lock"),
    ("npm-provenance-private-workspace-package-name", "private workspace name leftover", "wsn-lock"),
    ("npm-oidc-permissions-id-token-none-explicit", "id-token none leftover", "none-lock"),
    ("npm-provenance-files-field-includes-src-map", "files src-map leftover", "srcmap-lock"),
    ("npm-trusted-publisher-org-two-factor-enforced", "org 2FA leftover", "tfa-lock"),
    ("npm-oidc-job-container-options-network", "container options leftover", "copt-lock"),
    ("npm-provenance-lockfileVersion-2-vs-3", "lockfileVersion 2 leftover", "lf2-lock"),
    ("npm-publish-access-public-with-restricted-scope", "restricted scope leftover", "rscope-lock"),
    ("npm-trusted-publisher-workflow-call-secrets-inherit", "secrets inherit leftover", "inh-lock"),
    ("npm-oidc-issuer-forgejo-actions-hostname", "Forgejo Actions issuer leftover", "fj-lock"),
    ("npm-provenance-bin-field-directory-subject", "bin directory subject leftover", "bindir-lock"),
    ("npm-trusted-publisher-environment-wait-timer-zero", "wait_timer 0 leftover", "wt0-lock"),
    ("npm-oidc-audience-npm-pkg-github-com", "audience npm.pkg.github leftover", "ghpkg-lock"),
    ("npm-provenance-os-cpu-optional-wasm32", "wasm32 optional leftover", "wasm-lock"),
    ("npm-publish-provenance-true-then-omit-same-ver", "provenance omit retry leftover", "omit2-lock"),
    ("npm-trusted-publisher-devcontainer-oidc-unavailable", "devcontainer OIDC leftover", "dc-lock"),
]

PYPI = [
    ("pypi-trusted-publisher-workflow-path-nested-dir", "nested workflow path leftover", "release.yml nested"),
    ("pypi-oidc-issuer-drone-ci-vs-github", "Drone CI issuer leftover", "GitHub OIDC issuer"),
    ("pypi-attestation-wheel-missing-from-pair", "wheel missing from pair leftover", "sdist+wheel pair"),
    ("pypi-twine-attestations-cbor-not-dsse", "CBOR attestation leftover", "DSSE envelope"),
    ("pypi-trusted-publisher-environment-name-live-typo", "environment live typo leftover", "environment production"),
    ("pypi-oidc-job-container-id-token-request", "container id-token leftover", "runner id-token"),
    ("pypi-hatch-index-devpi-url-leftover", "hatch devpi index leftover", "prod PyPI index"),
    ("pypi-uv-publish-trusted-publishing-disabled", "uv trusted publishing disabled leftover", "uv trusted publishing"),
    ("pypi-poetry-pypi-token-file-leftover", "poetry token file leftover", "OIDC trusted publisher"),
    ("pypi-oidc-subject-workflow-ref-heads-main", "workflow ref heads/main leftover", "exact tag ref"),
    ("pypi-attestation-pep740-predicate-missing", "PEP 740 predicate leftover", "pep740 predicate"),
    ("pypi-trusted-publisher-project-name-underscores", "underscore project name leftover", "normalized PyPI name"),
    ("pypi-oidc-issuer-circleci-oidc-vs-github", "CircleCI OIDC leftover", "GitHub OIDC issuer"),
    ("pypi-twine-config-file-pypirc-leftover", "pypirc leftover", "OIDC trusted publishing"),
    ("pypi-trusted-publisher-workflow-call-ref-branch", "workflow_call branch leftover", "sha-pinned reusable workflow"),
    ("pypi-oidc-job-services-mysql-sidecar", "mysql sidecar leftover", "bare runner OIDC"),
    ("pypi-attestation-wheel-musllinux-vs-manylinux", "musllinux wheel leftover", "manylinux wheel attestation"),
    ("pypi-hatch-auth-token-vs-trusted-publishing", "hatch auth token leftover", "hatch trusted publishing"),
    ("pypi-uv-publish-check-url-warehouse-legacy", "uv warehouse legacy leftover", "uv check-url pypi.org"),
    ("pypi-poetry-pypi-token-vs-oidc-xor", "poetry pypi-token leftover", "poetry OIDC"),
    ("pypi-trusted-publisher-environment-deployment-branch-policy", "deployment branch leftover", "immediate environment"),
    ("pypi-oidc-issuer-gitea-actions-vs-github", "Gitea Actions issuer leftover", "GitHub OIDC issuer"),
    ("pypi-attestation-attestations-dir-jsonl-pair", "jsonl attestations leftover", "wheel+sdist attestations"),
    ("pypi-twine-skip-existing-flag-ci-leftover", "twine skip-existing leftover", "twine attestations required"),
]

MAVEN = [
    ("maven-gpg-sign-javadoc-sources-xor-classifier", "javadoc XOR sources leftover", "jvs-stg"),
    ("maven-central-portal-publishing-type-automatic-timeout", "automatic portal timeout leftover", "auto-stg"),
    ("maven-gpg-keyring-pinentry-mode-error", "pinentry mode leftover", "pin2-stg"),
    ("maven-gpg-passphrase-server-xor-env", "passphrase server XOR env leftover", "xor3-stg"),
    ("maven-central-bundle-missing-javadoc-checksum", "javadoc checksum leftover", "jdc-stg"),
    ("maven-gpg-useagent-pinentry-loopback-error", "useagent pinentry leftover", "ual-stg"),
    ("maven-ossrh-staging-profile-name-retired", "retired profile name leftover", "rpn-stg"),
    ("maven-gpg-sign-asc-armor-headers-missing", "armor headers leftover", "arm2-stg"),
    ("maven-central-publisher-api-namespace-unverified", "unverified namespace leftover", "unv-stg"),
    ("maven-gpg-digest-md5-vs-sha256-policy", "MD5 digest leftover", "md5d-stg"),
    ("maven-settings-gpg-executable-nix-store-path", "nix store gpg leftover", "nixg-stg"),
    ("maven-gpg-skip-javadoc-asc", "skip javadoc asc leftover", "sja-stg"),
    ("maven-gpg-sign-tests-javadoc-xor", "tests XOR javadoc leftover", "tjx-stg"),
    ("maven-central-portal-deployment-id-stale", "stale deployment id leftover", "dep-stg"),
    ("maven-gpg-homedir-tilde-vs-absolute", "tilde gnupg homedir leftover", "tilde-stg"),
    ("maven-gpg-sign-plugin-version-old", "old gpg plugin leftover", "oldp-stg"),
    ("maven-central-user-password-vs-portal-token", "user password leftover", "upw-stg"),
    ("maven-gpg-signer-class-bc-fips", "BC FIPS signer leftover", "bcf-stg"),
    ("maven-settings-server-ossrh-snapshots-id", "snapshots server id leftover", "snap-stg"),
    ("maven-gpg-exclude-classifiers-javadoc-leftover", "exclude javadoc leftover", "exj-stg"),
    ("maven-central-bundle-missing-module-sha512", "module sha512 leftover", "s512-stg"),
    ("maven-gpg-sign-attached-tests-missing", "attached tests leftover", "att-stg"),
    ("maven-ossrh-s01-host-dns-cname-stale", "s01 cname leftover", "cname-stg"),
    ("maven-gpg-passphrase-server-id-ossrh-mismatch", "ossrh passphrase id leftover", "opid-stg"),
]

CRATES = [
    ("crates-yank-vs-cargo-udeps-cache", "cargo-udeps cache leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-deny-licenses", "cargo-deny licenses leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-audit-lock", "cargo-audit lock leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-cyclonedx-report", "cargo-cyclonedx report leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-modules-graph", "cargo-modules graph leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-shear-report", "cargo-shear report leftover", "sparse yank index"),
    ("crates-yank-vs-crates-io-api-v2-meta", "crates.io api v2 leftover", "sparse yank index"),
    ("crates-yank-vs-lib-rs-versions-page", "lib.rs versions page leftover", "sparse yank index"),
    ("crates-yank-vs-docsrs-builds-log", "docs.rs builds log leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-release-config", "cargo-release config leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-clone-git-index", "cargo-clone git index leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-info-sparse", "cargo info sparse leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-tree-invert", "cargo-tree invert leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-direct-minimal-versions", "direct minimal-versions leftover", "sparse yank index"),
    ("crates-yank-vs-crates-io-api-v1-owners", "crates.io api v1 owners leftover", "sparse yank index"),
    ("crates-yank-vs-lib-rs-reverse-deps-html", "lib.rs reverse-deps html leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-public-api-diff-json", "cargo-public-api json leftover", "sparse yank index"),
    ("crates-yank-vs-rustdoc-scrape-examples-cache", "rustdoc scrape cache leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-dist-manifest", "cargo-dist manifest leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-semver-checks-baseline-json", "semver-checks json leftover", "sparse yank index"),
    ("crates-yank-vs-crates-io-trustpub-api", "crates.io trustpub api leftover", "sparse yank index"),
    ("crates-yank-vs-lib-rs-atom-feed", "lib.rs atom leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-show-asm-target", "cargo-show-asm target leftover", "sparse yank index"),
    ("crates-yank-vs-docsrs-rustdoc-json-v3", "docs.rs rustdoc json v3 leftover", "sparse yank index"),
]

BREW = [
    ("homebrew-bottle-rebuild-vs-uses-from-macos-bison-flex", "uses_from_macos bison/flex leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-depends-on-macos-sonoma", "depends_on macos sonoma leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-head-url-only", "head url leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-patch-p1-data", "patch p1 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-resource-only-url", "resource-only url leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-keg-only-shadowed", "keg_only shadowed leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-disable-because-deprecated", "disable because leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-deprecate-because", "deprecate because leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-service-run-at-load", "service run_at_load leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-std-cmake-args-ninja", "std_cmake_args ninja leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-on-sequoia-block", "on_sequoia leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-depends-on-arch-arm", "depends_on arch arm leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-tap-migrations-rb", "tap_migrations leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-fails-with-gcc-14", "fails_with gcc 14 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-cxxstdlib-libcxx", "cxxstdlib libcxx leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-post-install-symlink", "post_install symlink leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-caveats-kextload", "caveats kextload leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-depends-on-openjdk", "depends_on openjdk leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-option-universal-binary", "option universal leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-needs-openmp-libomp", "needs libomp leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-on-intel-block", "on_intel leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-version-scheme-1", "version_scheme 1 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-revision-plus-rebuild", "revision+rebuild leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-stable-mirror-only", "stable mirror leftover", "rebuilt bottle sha"),
]

NIX = [
    ("nix-fetchFromBitbucket-commit-vs-nar", "Bitbucket commit leftover", "NAR of Bitbucket archive"),
    ("nix-fetchzip-stripRoot-true-vs-nar", "stripRoot true leftover", "NAR of unstripped zip"),
    ("nix-fetchTarball-url-vs-nar", "fetchTarball url leftover", "NAR of tarball"),
    ("nix-fetchPypi-format-vs-nar", "fetchPypi format leftover", "NAR of PyPI sdist"),
    ("nix-fetchCrate-sha256-vs-nar", "fetchCrate sha leftover", "NAR of crates.io crate"),
    ("nix-fetchFromGitiles-ref-vs-nar", "Gitiles ref leftover", "NAR of Gitiles archive"),
    ("nix-fetchsvn-export-vs-nar", "svn export leftover", "NAR of svn checkout"),
    ("nix-fetchhg-bookmark-vs-nar", "hg bookmark leftover", "NAR of hg archive"),
    ("nix-fetchcvs-tag-vs-nar", "CVS tag leftover", "NAR of CVS export"),
    ("nix-fetchFromAzureDevOps-repo-vs-nar", "Azure repo leftover", "NAR of Azure archive"),
    ("nix-fetchgit-fetchLFS-vs-nar", "fetchLFS leftover", "NAR of no-LFS checkout"),
    ("nix-fetchurl-curlOpts-vs-nar", "curlOpts leftover", "NAR of fetched url"),
    ("nix-fetchFromGitHub-fetchSubmodules-vs-nar", "GitHub submodules leftover", "NAR of no-submodules archive"),
    ("nix-fetchgit-postFetch-vs-nar", "postFetch leftover", "NAR of plain fetchgit"),
    ("nix-fetchFromGitLab-api-vs-nar", "GitLab api leftover", "NAR of https archive"),
    ("nix-fetchgit-leaveDotGit-true-vs-nar", "leaveDotGit leftover", "NAR of no-dotgit tree"),
    ("nix-fetchFromGitea-domain-vs-nar", "Gitea domain leftover", "NAR of public Gitea archive"),
    ("nix-fetchurl-name-drv-vs-nar", "fetchurl name leftover", "NAR of fetchurl store path"),
    ("nix-fetchFromCgit-ref-vs-nar", "cgit ref leftover", "NAR of cgit archive"),
    ("nix-fetchgit-deepClone-true-vs-nar", "deepClone true leftover", "NAR of shallow fetchgit"),
    ("nix-fetchFromSourcehut-forge-vs-nar", "Sourcehut forge leftover", "NAR of sourcehut archive"),
    ("nix-fetchzip-extension-tgz-vs-nar", "tgz extension leftover", "NAR of unzipped tree"),
    ("nix-builtins-fetchGit-vs-nar", "builtins.fetchGit leftover", "NAR of fetchGit locked"),
    ("nix-fetchgit-sparseCheckout-cone-vs-nar", "cone sparse leftover", "NAR of noncone sparse checkout"),
]

NUGET = [
    ("nuget-snupkg-embed-untracked-sources-false", "EmbedUntrackedSources false leftover", "untracked-off"),
    ("nuget-snupkg-sourcelink-azure-repos-vs-github", "Azure Repos SourceLink leftover", "azdo-repos"),
    ("nuget-snupkg-deterministic-pathmap-extra", "extra PathMap leftover", "pathmap-x"),
    ("nuget-snupkg-debug-type-none-vs-portable", "DebugType none leftover", "none-debug"),
    ("nuget-snupkg-include-symbols-false-snupkg", "IncludeSymbols false leftover", "sym-off"),
    ("nuget-snupkg-sourcelink-bitbucket-server-vs-cloud", "Bitbucket Server SourceLink leftover", "bb-server"),
    ("nuget-snupkg-continuous-integration-build-false", "ContinuousIntegrationBuild false leftover", "cibuild-off"),
    ("nuget-snupkg-embed-all-sources-false-sourcelink", "EmbedAllSources false leftover", "embed-off"),
    ("nuget-snupkg-publish-gitlab-nuget-vs-generic", "GitLab nuget leftover", "gl-nuget"),
    ("nuget-snupkg-pdb-checksum-algorithm-sha384", "PDB checksum SHA384 leftover", "pdb-sha384"),
    ("nuget-snupkg-sourcelink-gitea-selfhosted-vs-cloud", "Gitea selfhosted SourceLink leftover", "gitea-sh"),
    ("nuget-snupkg-embedded-files-filter-include", "embedded files include leftover", "embed-inc"),
    ("nuget-snupkg-source-root-windows-vs-unix", "windows SourceRoot leftover", "win-root"),
    ("nuget-snupkg-symbolpackageformat-snupkg-only", "snupkg-only format leftover", "snupkg-only"),
    ("nuget-snupkg-repository-commit-vs-branch", "RepositoryCommit leftover", "repo-commit"),
    ("nuget-snupkg-sourcelink-codeberg-pages-vs-github", "Codeberg Pages SourceLink leftover", "cb-pages"),
    ("nuget-snupkg-publish-github-packages-nuget-v3", "GPR nuget v3 leftover", "gpr-n3"),
    ("nuget-snupkg-portable-pdb-timestamp-mismatch", "portable PDB timestamp leftover", "pdb-ts"),
    ("nuget-snupkg-sourcelink-sourcehut-pages-vs-github", "sourcehut pages leftover", "srht-pages"),
    ("nuget-snupkg-source-link-mapped-path-unix", "unix mapped path leftover", "unix-map"),
    ("nuget-snupkg-publish-myget-symbols-vs-nuget-org", "MyGet symbols leftover", "myget-sym"),
    ("nuget-snupkg-debug-type-portable-vs-embedded", "DebugType portable leftover", "port-dbg"),
    ("nuget-snupkg-include-source-revision-false", "IncludeSourceRevision false leftover", "src-rev-off"),
    ("nuget-snupkg-sourcelink-forgejo-selfhosted-vs-github", "Forgejo selfhosted leftover", "fj-sh"),
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
"""Unique mill: package-release-factory attestation wave-9 (r644+).

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

CATALOG_FIRST = 644
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
        raise SystemExit("dup slug or plant in attest wave9 catalog")
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
    out = HERE / "pkg-mill-attest-wave9.py"
    out.write_text(body)
    print(f"wrote {out} pairs={N*4} minerals_used_estimate={N*8} minerals_avail={len(MINERALS)}")


if __name__ == "__main__":
    main()
