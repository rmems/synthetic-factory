#!/usr/bin/env python3
"""Generate experiments/pkg-mill-attest-wave15.py from a unique plant catalog."""
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
    ("cosign-verify-oci-referrer-arch-vs-type", "referrer arch leftover", "OCI referrer type"),
    ("cosign-sign-bundle-canary-vs-prod-dsse", "canary bundle leftover", "prod DSSE bundle"),
    ("cosign-fulcio-okta-oidc-vs-github", "Okta Fulcio leftover", "GitHub Fulcio issuer"),
    ("cosign-rekor-entry-kind-hashedrekord-vs-rfc3161", "hashedrekord leftover", "RFC3161 Rekor kind"),
    ("cosign-verify-tsa-intermediate-untrusted", "untrusted TSA intermediate leftover", "trusted TSA intermediate"),
    ("cosign-policy-identity-step-vs-path", "step leftover", "workflow path identity"),
    ("cosign-sign-kms-gcp-hsm-vs-software", "GCP HSM leftover", "GCP software key"),
    ("cosign-verify-identity-create-vs-tag", "create identity leftover", "tag identity"),
    ("cosign-attach-predicate-cdx-vs-slsa", "CDX leftover", "SLSA predicate"),
    ("cosign-copy-signature-digest-vs-tag", "sig digest leftover", "tag signature"),
    ("cosign-verify-tuf-snapshot-stale", "stale TUF snapshot leftover", "refreshed TUF snapshot"),
    ("cosign-sign-recursive-vex-partial", "partial VEX leftover", "full index VEX"),
    ("cosign-policy-ctlog-url-shard-stale", "stale CT shard URL leftover", "current CT shard URL"),
    ("cosign-fulcio-uri-san-repo-archived-org", "archived org SAN leftover", "canonical org SAN"),
    ("cosign-verify-bundle-hash-algo-md5-vs-sha256", "md5 leftover", "sha256 payload algo"),
    ("cosign-sign-sk-piv-slot-84-vs-9a", "PIV slot 84 leftover", "PIV slot 9a"),
    ("cosign-oidc-issuer-auth0-vs-github", "Auth0 leftover", "GitHub Actions OIDC"),
    ("cosign-verify-cert-notafter-skew-days", "notAfter days leftover", "NTP-aligned notAfter"),
    ("cosign-policy-builder-id-sha-mismatch", "builder sha leftover", "exact builder id"),
    ("cosign-sign-payload-intoto-vex-json", "in-toto VEX leftover", "in-toto SLSA payload"),
    ("cosign-rekor-inclusion-proof-checkpoint", "checkpoint leftover", "signed checkpoint"),
    ("cosign-verify-oci-index-osversion-filter", "osversion filter leftover", "full OCI index"),
    ("cosign-sign-annotation-predicate-media", "predicate media leftover", "matching media"),
    ("cosign-policy-max-cert-lifetime-weeks", "max cert weeks leftover", "policy weeks"),
]

NPM = [
    ("npm-provenance-bundleDependencies-ignore-scripts", "ignore-scripts leftover", "ign-lock"),
    ("npm-trusted-publisher-workflow-filename-nightly-yml", "workflow nightly.yml leftover", "night-lock"),
    ("npm-oidc-audience-npmjs-net", "audience npmjs.net leftover", "nnet-aud"),
    ("npm-provenance-preuninstall-mutates-pack", "preuninstall leftover", "preun-lock"),
    ("npm-trusted-publisher-environment-required-check", "required check leftover", "rchk-lock"),
    ("npm-oidc-subject-ref-deployment-status", "deployment_status leftover", "dstat-lock"),
    ("npm-provenance-optionalDependencies-libc-ohos", "ohos libc leftover", "ohos-lock"),
    ("npm-publish-from-gvisor-runner-no-oidc", "gvisor without OIDC leftover", "gv-lock"),
    ("npm-trusted-publisher-pat-still-latest", "PAT leftover", "pat-lock"),
    ("npm-provenance-private-workspace-ignore", "workspace ignore leftover", "wign-lock"),
    ("npm-oidc-permissions-id-token-write-checks", "checks write leftover", "chkw-lock"),
    ("npm-provenance-files-field-includes-bin", "files includes bin leftover", "binf-lock"),
    ("npm-trusted-publisher-org-sso-scim", "org SCIM leftover", "scim-lock"),
    ("npm-oidc-job-container-user-daemon", "container daemon leftover", "cdae-lock"),
    ("npm-provenance-lockfileVersion-2-vs-9", "lockfileVersion 2 leftover", "lf29-lock"),
    ("npm-publish-access-public-restricted-scope", "public restricted leftover", "prsc-lock"),
    ("npm-trusted-publisher-workflow-call-outputs-map", "workflow_call outputs leftover", "wcom-lock"),
    ("npm-oidc-issuer-circleci-vs-github", "CircleCI leftover", "circ-lock"),
    ("npm-provenance-bin-field-dir-subject", "bin dir leftover", "bind-lock"),
    ("npm-trusted-publisher-environment-wait-timer-120", "wait_timer 120 leftover", "wt120-lock"),
    ("npm-oidc-audience-yarnpkg-net", "audience yarnpkg.net leftover", "ynet-lock"),
    ("npm-provenance-os-cpu-optional-openbsd-x64", "openbsd leftover", "obsd-lock"),
    ("npm-publish-provenance-true-then-omit-retry", "true then omit leftover", "tto-lock"),
    ("npm-trusted-publisher-arc-ephemeral-no-oidc", "ARC ephemeral leftover", "arce-lock"),
]

PYPI = [
    ("pypi-trusted-publisher-workflow-path-packages-dir", "packages workflow leftover", "release.yml path"),
    ("pypi-oidc-issuer-forgejo-actions-vs-github", "Forgejo Actions leftover", "GitHub OIDC issuer"),
    ("pypi-attestation-data-missing-sdist", "data leftover", "sdist+wheel pair"),
    ("pypi-twine-attestations-bson-not-dsse", "BSON leftover", "DSSE envelope"),
    ("pypi-trusted-publisher-environment-name-canary-typo", "environment canary leftover", "environment production"),
    ("pypi-oidc-job-container-id-token-request-write", "container request write leftover", "runner id-token"),
    ("pypi-hatch-index-jfrog-url-leftover", "hatch jfrog leftover", "prod PyPI index"),
    ("pypi-uv-publish-trusted-publishing-strict", "uv strict leftover", "uv trusted publishing"),
    ("pypi-poetry-keyring-backend-kwallet-leftover", "poetry kwallet leftover", "OIDC trusted publisher"),
    ("pypi-oidc-subject-workflow-ref-heads-canary", "workflow ref heads/canary leftover", "exact tag ref"),
    ("pypi-attestation-pep740-tsa-missing", "PEP 740 TSA leftover", "pep740 TSA"),
    ("pypi-trusted-publisher-project-name-emoji", "emoji project leftover", "normalized PyPI name"),
    ("pypi-oidc-issuer-harness-vs-github", "Harness leftover", "GitHub OIDC issuer"),
    ("pypi-twine-config-file-json-leftover", "twine json leftover", "OIDC trusted publishing"),
    ("pypi-trusted-publisher-workflow-call-ref-v4", "workflow_call v4 leftover", "sha-pinned reusable workflow"),
    ("pypi-oidc-job-services-kafka-sidecar", "kafka sidecar leftover", "bare runner OIDC"),
    ("pypi-attestation-wheel-manylinux_2_24-vs-2-28", "manylinux_2_24 leftover", "manylinux_2_28 attestation"),
    ("pypi-hatch-index-secret-vs-oidc", "hatch secret leftover", "hatch trusted publishing"),
    ("pypi-uv-publish-check-url-jfrog-legacy", "uv jfrog leftover", "uv check-url pypi.org"),
    ("pypi-poetry-pypi-token-pass-vs-oidc", "poetry pass leftover", "poetry OIDC"),
    ("pypi-trusted-publisher-environment-required-reviewers-5", "five reviewers leftover", "immediate environment"),
    ("pypi-oidc-issuer-spacelift-vs-github", "Spacelift leftover", "GitHub OIDC issuer"),
    ("pypi-attestation-attestations-dir-avro-pair", "avro leftover", "wheel+sdist attestations"),
    ("pypi-twine-skip-existing-attest-only", "skip-existing attest leftover", "twine attestations required"),
]

MAVEN = [
    ("maven-gpg-sign-ear-only-missing-jar", "ear-only leftover", "ear-stg"),
    ("maven-central-portal-publishing-type-sync-hang", "sync hang leftover", "sync-stg"),
    ("maven-gpg-keyring-agent-ssh-stale", "stale ssh leftover", "ssh-stg"),
    ("maven-gpg-passphrase-loopback-xor-env", "loopback leftover", "loop-stg"),
    ("maven-central-bundle-missing-ear-checksum", "ear checksum leftover", "earc-stg"),
    ("maven-gpg-useagent-true-pinentry-tty", "pinentry tty leftover", "tty2-stg"),
    ("maven-ossrh-staging-profile-id-paused", "paused profile leftover", "paus-stg"),
    ("maven-gpg-sign-asc-armor-version-1", "armor v1 leftover", "av1-stg"),
    ("maven-central-publisher-api-namespace-review", "review leftover", "revw-stg"),
    ("maven-gpg-digest-sha224-vs-sha256-policy", "SHA224 leftover", "s224-stg"),
    ("maven-settings-gpg-executable-pacman-path", "pacman leftover", "pac-stg"),
    ("maven-gpg-skip-ear-asc", "skip ear leftover", "sear-stg"),
    ("maven-gpg-sign-ear-only-missing-modules", "ear modules leftover", "emod-stg"),
    ("maven-central-portal-deployment-status-indexing", "indexing leftover", "idx-stg"),
    ("maven-gpg-homedir-gnupg-home-vs-absolute", "GNUPGHOME leftover", "ghome-stg"),
    ("maven-gpg-sign-plugin-skip-ear", "skip ear plugin leftover", "ske-stg"),
    ("maven-central-user-token-expired-refresh", "expired refresh leftover", "exref-stg"),
    ("maven-gpg-signer-class-bc-jdk17", "BC jdk17 leftover", "bc17-stg"),
    ("maven-settings-server-ossrh-public-id", "ossrh public leftover", "opub-stg"),
    ("maven-gpg-exclude-classifiers-ear", "exclude ear leftover", "exe-stg"),
    ("maven-central-bundle-missing-module-sha224", "module sha224 leftover", "s224m-stg"),
    ("maven-gpg-sign-attached-ear-missing", "attached ear leftover", "aear-stg"),
    ("maven-ossrh-s01-host-after-portal-edge", "s01 edge leftover", "edge-stg"),
    ("maven-gpg-passphrase-server-id-public-old", "old public passphrase leftover", "pold-stg"),
]

CRATES = [
    ("crates-yank-vs-cargo-outdated-verbose", "cargo-outdated verbose leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-deny-bans-workspace", "cargo-deny bans workspace leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-audit-dbpath", "cargo-audit dbpath leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-cyclonedx-v1-1", "cargo-cyclonedx v1.1 leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-modules-deps", "cargo-modules deps leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-shear-unused-proc", "cargo-shear unused-proc leftover", "sparse yank index"),
    ("crates-yank-vs-crates-io-api-v2-recent", "crates.io api v2 recent leftover", "sparse yank index"),
    ("crates-yank-vs-lib-rs-og", "lib.rs og leftover", "sparse yank index"),
    ("crates-yank-vs-docsrs-source-crate-tgz", "docs.rs crate tgz leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-release-sign", "cargo-release sign leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-clone-locked", "cargo-clone locked leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-info-homepage", "cargo info homepage leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-tree-invert-json", "cargo-tree invert json leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-minimal-versions-direct-dev", "minimal-versions direct-dev leftover", "sparse yank index"),
    ("crates-yank-vs-crates-io-api-v1-new", "crates.io api v1 new leftover", "sparse yank index"),
    ("crates-yank-vs-lib-rs-og-png", "lib.rs og png leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-public-api-diff-tsv", "cargo-public-api tsv leftover", "sparse yank index"),
    ("crates-yank-vs-rustdoc-scrape-examples-adoc", "rustdoc scrape adoc leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-dist-plan-json", "cargo-dist plan json leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-semver-checks-baseline-example", "semver-checks example leftover", "sparse yank index"),
    ("crates-yank-vs-crates-io-trustpub-png", "crates.io trustpub png leftover", "sparse yank index"),
    ("crates-yank-vs-lib-rs-robots", "lib.rs robots leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-show-asm-mips", "cargo-show-asm mips leftover", "sparse yank index"),
    ("crates-yank-vs-docsrs-rustdoc-json-workspace", "docs.rs rustdoc workspace leftover", "sparse yank index"),
]

BREW = [
    ("homebrew-bottle-rebuild-vs-uses-from-macos-libxml2", "uses_from_macos libxml2 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-depends-on-macos-high-sierra", "depends_on macos high_sierra leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-head-spec-sha", "head sha leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-patch-data-p6", "patch DATA p6 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-resource-url-sha", "resource url sha leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-keg-only-because-provided-by-system", "keg_only system leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-disable-because-no-source", "disable no_source leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-deprecate-because-replaced", "deprecate replaced leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-service-keep-alive-always", "service always leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-std-dune-args", "std_dune leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-on-catalina-block", "on_catalina leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-depends-on-arch-loong", "depends_on arch loong leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-tap-migrations-ini", "tap_migrations ini leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-fails-with-gcc-9", "fails_with gcc 9 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-cxxstdlib-check-none", "cxxstdlib none leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-post-install-ln-s", "post_install ln leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-caveats-dscacheutil", "caveats dscacheutil leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-depends-on-perl", "depends_on perl leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-option-with-static", "option static leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-needs-mmx", "needs mmx leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-on-linux-netbsd", "on_linux netbsd leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-version-scheme-six", "version_scheme 6 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-revision-three", "revision 3 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-stable-url-blake2", "stable blake2 leftover", "rebuilt bottle sha"),
]

NIX = [
    ("nix-fetchFromBitbucket-project-vs-nar", "Bitbucket project leftover", "NAR of Bitbucket archive"),
    ("nix-fetchzip-md5-vs-nar", "fetchzip md5 leftover", "NAR of zip"),
    ("nix-fetchTarball-md5-vs-nar", "fetchTarball md5 leftover", "NAR of tarball"),
    ("nix-fetchPypi-md5-vs-nar", "fetchPypi md5 leftover", "NAR of PyPI sdist"),
    ("nix-fetchCrate-md5-vs-nar", "fetchCrate md5 leftover", "NAR of crates.io crate"),
    ("nix-fetchFromGitiles-md5-vs-nar", "Gitiles md5 leftover", "NAR of Gitiles archive"),
    ("nix-fetchsvn-md5-vs-nar", "svn md5 leftover", "NAR of svn export"),
    ("nix-fetchhg-md5-vs-nar", "hg md5 leftover", "NAR of hg archive"),
    ("nix-fetchcvs-md5-vs-nar", "CVS md5 leftover", "NAR of CVS export"),
    ("nix-fetchFromAzureDevOps-md5-vs-nar", "Azure md5 leftover", "NAR of Azure archive"),
    ("nix-fetchgit-fetchNotes-vs-nar", "fetchNotes leftover", "NAR of checkout"),
    ("nix-fetchurl-md5-vs-nar-url", "fetchurl md5 leftover", "NAR of fetched url"),
    ("nix-fetchFromGitHub-md5-vs-nar", "GitHub md5 leftover", "NAR of archive"),
    ("nix-fetchgit-rebase-vs-nar", "rebase leftover", "NAR of fetchgit"),
    ("nix-fetchFromGitLab-md5-vs-nar", "GitLab md5 leftover", "NAR of https archive"),
    ("nix-fetchgit-follow-vs-nar", "follow leftover", "NAR of pinned fetchgit"),
    ("nix-fetchFromGitea-md5-vs-nar", "Gitea md5 leftover", "NAR of public Gitea archive"),
    ("nix-fetchurl-sha1-vs-nar-store", "fetchurl sha1 leftover", "NAR of fetchurl store path"),
    ("nix-fetchFromCgit-md5-vs-nar", "cgit md5 leftover", "NAR of cgit archive"),
    ("nix-fetchgit-annotate-vs-nar", "annotate leftover", "NAR of pinned fetchgit"),
    ("nix-fetchFromSourcehut-md5-vs-nar", "Sourcehut md5 leftover", "NAR of sourcehut archive"),
    ("nix-fetchzip-md5-vs-nar-root", "fetchzip md5 leftover", "NAR of zip"),
    ("nix-builtins-toFile-vs-nar", "builtins.toFile leftover", "NAR of toFile"),
    ("nix-fetchgit-fetchNotes-true-vs-nar", "notes leftover", "NAR of checkout"),
]

NUGET = [
    ("nuget-snupkg-embed-untracked-sources-test", "EmbedUntrackedSources test leftover", "untracked-test"),
    ("nuget-snupkg-sourcelink-azure-repos-azdo-vs-github", "Azure Repos azdo leftover", "azdo-az"),
    ("nuget-snupkg-deterministic-pathmap-ci", "ci PathMap leftover", "pathmap-ci"),
    ("nuget-snupkg-debug-type-pdbonly-vs-none", "DebugType pdbonly leftover", "pdbonly-none"),
    ("nuget-snupkg-include-symbols-snupkg-true-no-xml", "IncludeSymbols no xml leftover", "sym-noxml"),
    ("nuget-snupkg-sourcelink-bitbucket-pipelines-vs-github", "Bitbucket pipelines leftover", "bb-pipes"),
    ("nuget-snupkg-continuous-integration-build-true-ado", "CI ado leftover", "ciado"),
    ("nuget-snupkg-embed-all-sources-true-no-link", "EmbedAllSources no link leftover", "embed-nl"),
    ("nuget-snupkg-publish-gitlab-nuget-v6", "GitLab nuget v6 leftover", "gl-n6"),
    ("nuget-snupkg-pdb-checksum-algorithm-xxhash", "PDB checksum xxhash leftover", "pdb-xx"),
    ("nuget-snupkg-sourcelink-gitea-woodpecker-vs-github", "Gitea woodpecker leftover", "gitea-wp"),
    ("nuget-snupkg-embedded-files-filter-all", "embedded files all leftover", "embed-all"),
    ("nuget-snupkg-source-root-mapped-drive", "mapped SourceRoot leftover", "mapd-root"),
    ("nuget-snupkg-symbolpackageformat-none-vs-symbols", "none vs symbols leftover", "fmt-ns"),
    ("nuget-snupkg-repository-type-vs-commit", "RepositoryType leftover", "repo-tc"),
    ("nuget-snupkg-sourcelink-codeberg-woodpecker-vs-github", "Codeberg woodpecker leftover", "cb-wp"),
    ("nuget-snupkg-publish-github-packages-nuget-v7", "GPR nuget v7 leftover", "gpr-n7"),
    ("nuget-snupkg-portable-pdb-guid-ones", "portable PDB ones leftover", "pdb-ones"),
    ("nuget-snupkg-sourcelink-sourcehut-pages-raw", "sourcehut pages raw leftover", "srht-praw"),
    ("nuget-snupkg-source-link-mapped-path-drive", "drive mapped path leftover", "drv-map"),
    ("nuget-snupkg-publish-myget-v6-vs-nuget-org", "MyGet v6 leftover", "myget-v6"),
    ("nuget-snupkg-debug-type-embedded-vs-pdbonly", "DebugType embedded leftover", "emb-pdbonly"),
    ("nuget-snupkg-include-source-revision-false-local", "IncludeSourceRevision local leftover", "src-floc"),
    ("nuget-snupkg-sourcelink-forgejo-woodpecker-vs-github", "Forgejo woodpecker leftover", "fj-wp"),
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
"""Unique mill: package-release-factory attestation wave-15 (r1220+).

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

CATALOG_FIRST = 1220
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
        raise SystemExit("dup slug or plant in attest wave15 catalog")
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
    out = HERE / "pkg-mill-attest-wave15.py"
    out.write_text(body)
    print(f"wrote {out} pairs={N*4} minerals_used_estimate={N*8} minerals_avail={len(MINERALS)}")


if __name__ == "__main__":
    main()
