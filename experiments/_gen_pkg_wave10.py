#!/usr/bin/env python3
"""Generate experiments/pkg-mill-attest-wave10.py from a unique plant catalog."""
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
    ("cosign-verify-oci-referrer-subject-media-type", "referrer subject mediaType leftover", "OCI subject mediaType"),
    ("cosign-sign-bundle-v03-dsse-payload-type", "bundle v0.3 payload leftover", "DSSE payload type"),
    ("cosign-fulcio-drone-oidc-vs-github", "Drone OIDC leftover", "GitHub Fulcio issuer"),
    ("cosign-rekor-entry-kind-intoto-vs-rfc3161", "in-toto Rekor leftover", "RFC3161 Rekor kind"),
    ("cosign-verify-tsa-leaf-untrusted", "untrusted TSA leaf leftover", "trusted TSA leaf"),
    ("cosign-policy-identity-job-id-vs-path", "job id leftover", "workflow path identity"),
    ("cosign-sign-kms-gcp-key-version-mismatch", "GCP key version leftover", "matching GCP key version"),
    ("cosign-verify-identity-merge-queue-vs-tag", "merge_queue identity leftover", "tag identity"),
    ("cosign-attach-predicate-vex-vs-slsa", "VEX predicate leftover", "SLSA predicate"),
    ("cosign-copy-referrer-artifact-type-mismatch", "referrer artifactType leftover", "matching artifactType"),
    ("cosign-verify-tuf-snapshot-expired", "expired TUF snapshot leftover", "refreshed TUF snapshot"),
    ("cosign-sign-recursive-attest-partial-index", "partial attest leftover", "full index attest"),
    ("cosign-policy-ctlog-key-id-stale", "stale CT key id leftover", "current CT key id"),
    ("cosign-fulcio-uri-san-repo-archived", "archived repo SAN leftover", "current repo SAN"),
    ("cosign-verify-bundle-hash-algo-sha512-vs-sha256", "sha512 payload leftover", "sha256 payload algo"),
    ("cosign-sign-sk-piv-slot-9c-vs-9a", "PIV slot 9c leftover", "PIV slot 9a"),
    ("cosign-oidc-issuer-gitlab-oidc-vs-github", "GitLab OIDC leftover", "GitHub Actions OIDC"),
    ("cosign-verify-cert-notafter-leeway", "notAfter leeway leftover", "NTP-aligned notAfter"),
    ("cosign-policy-builder-id-uri-mismatch", "builder-id URI leftover", "exact builder id"),
    ("cosign-sign-payload-intoto-spdx-json", "in-toto SPDX leftover", "in-toto SLSA payload"),
    ("cosign-rekor-inclusion-proof-tree-size", "tree size leftover", "signed tree size"),
    ("cosign-verify-oci-index-platform-filter", "platform filter leftover", "full OCI index"),
    ("cosign-sign-annotation-dev-cosign-bundle", "dev bundle annotation leftover", "matching annotation"),
    ("cosign-policy-max-cert-validity-hours", "max cert validity leftover", "policy validity hours"),
]

NPM = [
    ("npm-provenance-bundleDependencies-bundled-lock", "bundled lock leftover", "bdlock"),
    ("npm-trusted-publisher-workflow-filename-ci-yml", "workflow ci.yml leftover", "ci-lock"),
    ("npm-oidc-audience-registry-npmjs-org", "audience registry.npmjs.org leftover", "reg-aud"),
    ("npm-provenance-preinstall-mutates-pack", "preinstall mutate leftover", "prein-lock"),
    ("npm-trusted-publisher-environment-deployment-protection", "deployment protection leftover", "dprot-lock"),
    ("npm-oidc-subject-ref-schedule", "schedule subject leftover", "sched-lock"),
    ("npm-provenance-optionalDependencies-libc-musl", "musl libc leftover", "musl-lock"),
    ("npm-publish-from-docker-runner-no-oidc", "docker runner without OIDC leftover", "dock-lock"),
    ("npm-trusted-publisher-legacy-token-still-latest", "legacy token leftover", "leg-lock"),
    ("npm-provenance-private-workspace-root-package", "private root package leftover", "proot-lock"),
    ("npm-oidc-permissions-id-token-write-contents-none", "contents none leftover", "cnone-lock"),
    ("npm-provenance-files-field-includes-node-modules", "files node_modules leftover", "nm-lock"),
    ("npm-trusted-publisher-org-sso-enforced", "org SSO leftover", "sso-lock"),
    ("npm-oidc-job-container-image-private", "private container leftover", "pcimg-lock"),
    ("npm-provenance-lockfileVersion-3-vs-1", "lockfileVersion 3 leftover", "lf3-lock"),
    ("npm-publish-access-restricted-unscoped", "restricted unscoped leftover", "runsc-lock"),
    ("npm-trusted-publisher-workflow-call-inputs-secrets", "workflow_call secrets leftover", "wcs-lock"),
    ("npm-oidc-issuer-sourcehut-builds-vs-github", "Sourcehut builds issuer leftover", "srht-lock"),
    ("npm-provenance-bin-field-object-subject", "bin object subject leftover", "bino-lock"),
    ("npm-trusted-publisher-environment-wait-timer-60", "wait_timer 60 leftover", "wt60-lock"),
    ("npm-oidc-audience-ghcr-packages", "audience ghcr packages leftover", "ghcrp-lock"),
    ("npm-provenance-os-cpu-optional-linux-arm", "linux-arm optional leftover", "larm-lock"),
    ("npm-publish-provenance-file-then-omit", "provenance file omit leftover", "pfile-lock"),
    ("npm-trusted-publisher-codespace-no-id-token", "codespace no id-token leftover", "csid-lock"),
]

PYPI = [
    ("pypi-trusted-publisher-workflow-path-dot-github", "dot-github workflow leftover", "release.yml path"),
    ("pypi-oidc-issuer-travis-vs-github", "Travis OIDC leftover", "GitHub OIDC issuer"),
    ("pypi-attestation-wheel-only-missing-sdist", "wheel-only leftover", "sdist+wheel pair"),
    ("pypi-twine-attestations-pem-not-dsse", "PEM attestation leftover", "DSSE envelope"),
    ("pypi-trusted-publisher-environment-name-release-typo", "environment release typo leftover", "environment production"),
    ("pypi-oidc-job-container-with-id-token-none", "container id-token none leftover", "runner id-token"),
    ("pypi-hatch-index-pypiserver-url-leftover", "hatch pypiserver leftover", "prod PyPI index"),
    ("pypi-uv-publish-trusted-publishing-off", "uv trusted publishing off leftover", "uv trusted publishing"),
    ("pypi-poetry-http-basic-file-leftover", "poetry http-basic file leftover", "OIDC trusted publisher"),
    ("pypi-oidc-subject-workflow-ref-heads-release", "workflow ref heads/release leftover", "exact tag ref"),
    ("pypi-attestation-pep740-bundle-missing", "PEP 740 bundle leftover", "pep740 bundle"),
    ("pypi-trusted-publisher-project-name-dots", "dotted project name leftover", "normalized PyPI name"),
    ("pypi-oidc-issuer-appveyor-vs-github", "AppVeyor OIDC leftover", "GitHub OIDC issuer"),
    ("pypi-twine-config-file-keyring-leftover", "twine keyring leftover", "OIDC trusted publishing"),
    ("pypi-trusted-publisher-workflow-call-ref-tag", "workflow_call tag leftover", "sha-pinned reusable workflow"),
    ("pypi-oidc-job-services-mongo-sidecar", "mongo sidecar leftover", "bare runner OIDC"),
    ("pypi-attestation-wheel-manylinux1-vs-2-28", "manylinux1 leftover", "manylinux_2_28 attestation"),
    ("pypi-hatch-repo-token-vs-trusted-publishing", "hatch repo token leftover", "hatch trusted publishing"),
    ("pypi-uv-publish-check-url-testpypi-legacy", "uv testpypi legacy leftover", "uv check-url pypi.org"),
    ("pypi-poetry-pypi-token-file-vs-oidc", "poetry token file leftover", "poetry OIDC"),
    ("pypi-trusted-publisher-environment-reviewers-required", "reviewers required leftover", "immediate environment"),
    ("pypi-oidc-issuer-bitbucket-pipelines-vs-github", "Bitbucket Pipelines leftover", "GitHub OIDC issuer"),
    ("pypi-attestation-attestations-dir-tar-pair", "tar attestations leftover", "wheel+sdist attestations"),
    ("pypi-twine-skip-existing-with-attestations", "skip-existing leftover", "twine attestations required"),
]

MAVEN = [
    ("maven-gpg-sign-javadoc-only-missing-jar", "javadoc-only leftover", "jvo-stg"),
    ("maven-central-portal-publishing-type-manual-hang", "manual portal hang leftover", "man-stg"),
    ("maven-gpg-keyring-agent-socket-stale", "stale agent socket leftover", "sock-stg"),
    ("maven-gpg-passphrase-env-empty-xor", "empty passphrase env leftover", "empt-stg"),
    ("maven-central-bundle-missing-pom-checksum", "pom checksum leftover", "pomc-stg"),
    ("maven-gpg-useagent-false-pinentry-curses", "pinentry curses leftover", "curse-stg"),
    ("maven-ossrh-staging-profile-id-unknown", "unknown profile leftover", "unk-stg"),
    ("maven-gpg-sign-asc-armor-charset", "armor charset leftover", "char-stg"),
    ("maven-central-publisher-api-namespace-pending-claim", "pending claim leftover", "pend-stg"),
    ("maven-gpg-digest-sha1-policy-reject", "SHA1 policy leftover", "sha1p-stg"),
    ("maven-settings-gpg-executable-flatpak-path", "flatpak gpg leftover", "flat-stg"),
    ("maven-gpg-skip-sources-asc", "skip sources asc leftover", "ssa-stg"),
    ("maven-gpg-sign-tests-only-missing-main", "tests-only leftover", "tonly-stg"),
    ("maven-central-portal-deployment-status-failed", "failed deployment leftover", "fail-stg"),
    ("maven-gpg-homedir-symlink-vs-absolute", "symlink gnupg leftover", "sym-stg"),
    ("maven-gpg-sign-plugin-skip-true", "skip true leftover", "skip-stg"),
    ("maven-central-user-token-expired", "expired user token leftover", "exp-stg"),
    ("maven-gpg-signer-class-xmlsec", "xmlsec signer leftover", "xmls-stg"),
    ("maven-settings-server-central-snapshots-id", "central snapshots leftover", "csnap-stg"),
    ("maven-gpg-exclude-classifiers-tests-sources", "exclude tests sources leftover", "exts-stg"),
    ("maven-central-bundle-missing-module-sha1", "module sha1 leftover", "s1-stg"),
    ("maven-gpg-sign-attached-javadoc-missing", "attached javadoc leftover", "ajv-stg"),
    ("maven-ossrh-s01-host-after-cutover-cname", "s01 cutover leftover", "cut-stg"),
    ("maven-gpg-passphrase-server-id-central-mismatch", "central passphrase id leftover", "cpid-stg"),
]

CRATES = [
    ("crates-yank-vs-cargo-outdated-workspace", "cargo-outdated workspace leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-deny-sources", "cargo-deny sources leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-audit-json", "cargo-audit json leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-cyclonedx-v1-5", "cargo-cyclonedx v1.5 leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-modules-orphans", "cargo-modules orphans leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-shear-fix", "cargo-shear fix leftover", "sparse yank index"),
    ("crates-yank-vs-crates-io-api-v2-downloads", "crates.io api v2 downloads leftover", "sparse yank index"),
    ("crates-yank-vs-lib-rs-crate-page", "lib.rs crate page leftover", "sparse yank index"),
    ("crates-yank-vs-docsrs-source-tarball", "docs.rs source tarball leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-release-tag", "cargo-release tag leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-clone-registry", "cargo-clone registry leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-info-features", "cargo info features leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-tree-duplicates-json", "cargo-tree duplicates json leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-minimal-versions-direct", "minimal-versions direct leftover", "sparse yank index"),
    ("crates-yank-vs-crates-io-api-v1-reverse", "crates.io api v1 reverse leftover", "sparse yank index"),
    ("crates-yank-vs-lib-rs-owners-json", "lib.rs owners json leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-public-api-diff-markdown", "cargo-public-api md leftover", "sparse yank index"),
    ("crates-yank-vs-rustdoc-scrape-examples-json", "rustdoc scrape json leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-dist-github-index", "cargo-dist github leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-semver-checks-baseline-toml", "semver-checks toml leftover", "sparse yank index"),
    ("crates-yank-vs-crates-io-trustpub-feed", "crates.io trustpub feed leftover", "sparse yank index"),
    ("crates-yank-vs-lib-rs-rss2", "lib.rs rss2 leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-show-asm-intel", "cargo-show-asm intel leftover", "sparse yank index"),
    ("crates-yank-vs-docsrs-rustdoc-json-nightly", "docs.rs rustdoc nightly leftover", "sparse yank index"),
]

BREW = [
    ("homebrew-bottle-rebuild-vs-uses-from-macos-zlib", "uses_from_macos zlib leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-depends-on-macos-ventura", "depends_on macos ventura leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-head-spec-url", "head spec url leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-patch-data-p0", "patch DATA p0 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-resource-sha256-only", "resource sha256 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-keg-only-because-shadowed", "keg_only shadowed leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-disable-date-iso", "disable date leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-deprecate-because-unmaintained", "deprecate unmaintained leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-service-keep-alive-true", "service keep_alive leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-std-go-args", "std_go_args leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-on-tahoe-block", "on_tahoe leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-depends-on-arch-arm64", "depends_on arch arm64 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-tap-migrations-json", "tap_migrations json leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-fails-with-clang-16", "fails_with clang leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-cxxstdlib-libstdcxx", "cxxstdlib libstdcxx leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-post-install-chmod", "post_install chmod leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-caveats-plist", "caveats plist leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-depends-on-python", "depends_on python leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-option-c-plus-plus-11", "option cxx11 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-needs-avx2", "needs avx2 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-on-linux-gnu", "on_linux leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-version-scheme-zero", "version_scheme 0 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-revision-only", "revision leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-stable-url-mirror", "stable url mirror leftover", "rebuilt bottle sha"),
]

NIX = [
    ("nix-fetchFromBitbucket-tag-vs-nar", "Bitbucket tag leftover", "NAR of Bitbucket archive"),
    ("nix-fetchzip-name-vs-nar", "fetchzip name leftover", "NAR of zip"),
    ("nix-fetchTarball-sha256-vs-nar", "fetchTarball sha leftover", "NAR of tarball"),
    ("nix-fetchPypi-version-vs-nar", "fetchPypi version leftover", "NAR of PyPI sdist"),
    ("nix-fetchCrate-pname-vs-nar", "fetchCrate pname leftover", "NAR of crates.io crate"),
    ("nix-fetchFromGitiles-commit-vs-nar", "Gitiles commit leftover", "NAR of Gitiles archive"),
    ("nix-fetchsvn-rev-vs-nar", "svn rev leftover", "NAR of svn export"),
    ("nix-fetchhg-tag-vs-nar", "hg tag leftover", "NAR of hg archive"),
    ("nix-fetchcvs-date-vs-nar", "CVS date leftover", "NAR of CVS export"),
    ("nix-fetchFromAzureDevOps-sha-vs-nar", "Azure sha leftover", "NAR of Azure archive"),
    ("nix-fetchgit-fetchWorktrees-vs-nar", "fetchWorktrees leftover", "NAR of no-worktrees checkout"),
    ("nix-fetchurl-postFetch-vs-nar", "fetchurl postFetch leftover", "NAR of fetched url"),
    ("nix-fetchFromGitHub-leaveDotGit-vs-nar", "GitHub leaveDotGit leftover", "NAR of archive"),
    ("nix-fetchgit-name-vs-nar", "fetchgit name leftover", "NAR of plain fetchgit"),
    ("nix-fetchFromGitLab-project-vs-nar", "GitLab project leftover", "NAR of https archive"),
    ("nix-fetchgit-sparseCheckout-vs-nar", "sparseCheckout leftover", "NAR of full tree"),
    ("nix-fetchFromGitea-owner-vs-nar", "Gitea owner leftover", "NAR of public Gitea archive"),
    ("nix-fetchurl-hashMode-recursive-vs-nar", "recursive hashMode leftover", "NAR of fetchurl store path"),
    ("nix-fetchFromCgit-sha-vs-nar", "cgit sha leftover", "NAR of cgit archive"),
    ("nix-fetchgit-rev-symbolic-vs-nar", "symbolic rev leftover", "NAR of pinned fetchgit"),
    ("nix-fetchFromSourcehut-owner-vs-nar", "Sourcehut owner leftover", "NAR of sourcehut archive"),
    ("nix-fetchzip-stripRoot-vs-nar-of-root", "stripRoot leftover", "NAR of rooted zip"),
    ("nix-builtins-fetchTarball-vs-nar", "builtins.fetchTarball leftover", "NAR of fetchTarball locked"),
    ("nix-fetchgit-fetchSubmodules-recursive-vs-nar", "recursive submodules leftover", "NAR of no-submodules checkout"),
]

NUGET = [
    ("nuget-snupkg-embed-untracked-sources-true-no-link", "EmbedUntrackedSources no-link leftover", "untracked-nolink"),
    ("nuget-snupkg-sourcelink-azure-devops-vs-github", "Azure DevOps SourceLink leftover", "azdo-cloud"),
    ("nuget-snupkg-deterministic-pathmap-duplicate", "duplicate PathMap leftover", "pathmap-dup"),
    ("nuget-snupkg-debug-type-embedded-sources", "DebugType embedded leftover", "embed-src"),
    ("nuget-snupkg-include-symbols-snupkg-false", "IncludeSymbols snupkg false leftover", "sym-false"),
    ("nuget-snupkg-sourcelink-bitbucket-cloud-vs-github", "Bitbucket Cloud SourceLink leftover", "bb-cloud"),
    ("nuget-snupkg-continuous-integration-build-true-local", "CI build true local leftover", "cilocal"),
    ("nuget-snupkg-embed-all-sources-true-no-pdb", "EmbedAllSources no pdb leftover", "embed-nopdb"),
    ("nuget-snupkg-publish-gitlab-package-registry", "GitLab package registry leftover", "gl-pkg"),
    ("nuget-snupkg-pdb-checksum-algorithm-sha512", "PDB checksum SHA512 leftover", "pdb-sha512"),
    ("nuget-snupkg-sourcelink-gitea-cloud-vs-github", "Gitea cloud SourceLink leftover", "gitea-cloud"),
    ("nuget-snupkg-embedded-files-filter-none", "embedded files none leftover", "embed-none"),
    ("nuget-snupkg-source-root-mixed-separators", "mixed SourceRoot leftover", "mix-root"),
    ("nuget-snupkg-symbolpackageformat-symbols-nupkg-only", "symbols.nupkg-only leftover", "symnupkg"),
    ("nuget-snupkg-repository-url-vs-commit", "RepositoryUrl leftover", "repo-url"),
    ("nuget-snupkg-sourcelink-codeberg-git-vs-github", "Codeberg git SourceLink leftover", "cb-git"),
    ("nuget-snupkg-publish-github-packages-nuget-v2", "GPR nuget v2 leftover", "gpr-n2"),
    ("nuget-snupkg-portable-pdb-guid-age-zero", "portable PDB age 0 leftover", "pdb-age0"),
    ("nuget-snupkg-sourcelink-sourcehut-git-vs-github", "sourcehut git leftover", "srht-git"),
    ("nuget-snupkg-source-link-mapped-path-windows", "windows mapped path leftover", "win-map"),
    ("nuget-snupkg-publish-myget-legacy-vs-nuget-org", "MyGet legacy leftover", "myget-leg"),
    ("nuget-snupkg-debug-type-full-pdb-vs-portable", "DebugType full leftover", "full-pdb"),
    ("nuget-snupkg-include-source-revision-in-info-false", "IncludeSourceRevision info false leftover", "src-info-off"),
    ("nuget-snupkg-sourcelink-forgejo-cloud-vs-github", "Forgejo cloud leftover", "fj-cloud"),
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
"""Unique mill: package-release-factory attestation wave-10 (r740+).

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

CATALOG_FIRST = 740
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
        raise SystemExit("dup slug or plant in attest wave10 catalog")
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
    out = HERE / "pkg-mill-attest-wave10.py"
    out.write_text(body)
    print(f"wrote {out} pairs={N*4} minerals_used_estimate={N*8} minerals_avail={len(MINERALS)}")


if __name__ == "__main__":
    main()
