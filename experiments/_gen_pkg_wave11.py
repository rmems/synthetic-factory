#!/usr/bin/env python3
"""Generate experiments/pkg-mill-attest-wave11.py from a unique plant catalog."""
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
    ("cosign-verify-oci-referrer-annotation-vs-type", "referrer annotation leftover", "OCI referrer type"),
    ("cosign-sign-bundle-v02-simple-vs-dsse", "bundle v0.2 simple leftover", "DSSE bundle"),
    ("cosign-fulcio-appveyor-oidc-vs-github", "AppVeyor OIDC leftover", "GitHub Fulcio issuer"),
    ("cosign-rekor-entry-kind-hashedrekord-vs-intoto", "hashedrekord leftover", "in-toto Rekor kind"),
    ("cosign-verify-tsa-intermediate-expired", "expired TSA intermediate leftover", "current TSA chain"),
    ("cosign-policy-identity-run-id-vs-path", "run id leftover", "workflow path identity"),
    ("cosign-sign-kms-aws-alias-vs-arn", "AWS alias leftover", "matching AWS KMS ARN"),
    ("cosign-verify-identity-workflow-call-vs-tag", "workflow_call identity leftover", "tag identity"),
    ("cosign-attach-predicate-openvex-vs-slsa", "OpenVEX leftover", "SLSA predicate"),
    ("cosign-copy-signature-annotation-mismatch", "sig annotation leftover", "matching annotation"),
    ("cosign-verify-tuf-timestamp-expired", "expired TUF timestamp leftover", "refreshed TUF timestamp"),
    ("cosign-sign-recursive-sbom-partial-index", "partial SBOM leftover", "full index SBOM"),
    ("cosign-policy-ctlog-pubkey-fingerprint", "CT pubkey fingerprint leftover", "current CT fingerprint"),
    ("cosign-fulcio-uri-san-repo-forked", "forked repo SAN leftover", "canonical repo SAN"),
    ("cosign-verify-bundle-hash-algo-blake2-vs-sha256", "blake2 leftover", "sha256 payload algo"),
    ("cosign-sign-sk-piv-slot-9d-vs-9a", "PIV slot 9d leftover", "PIV slot 9a"),
    ("cosign-oidc-issuer-buildkite-vs-github", "Buildkite OIDC leftover", "GitHub Actions OIDC"),
    ("cosign-verify-cert-notafter-grace-period", "notAfter grace leftover", "NTP-aligned notAfter"),
    ("cosign-policy-builder-id-hostname-mismatch", "builder hostname leftover", "exact builder id"),
    ("cosign-sign-payload-intoto-spdx-tv", "in-toto SPDX-TV leftover", "in-toto SLSA payload"),
    ("cosign-rekor-inclusion-proof-log-index", "log index leftover", "signed log index"),
    ("cosign-verify-oci-index-os-filter", "os filter leftover", "full OCI index"),
    ("cosign-sign-annotation-predicate-uri", "predicate URI leftover", "matching predicate URI"),
    ("cosign-policy-max-cert-chain-intermediates", "max intermediates leftover", "policy chain depth"),
]

NPM = [
    ("npm-provenance-bundleDependencies-hoist-false", "hoist false leftover", "hoist-lock"),
    ("npm-trusted-publisher-workflow-filename-build-yml", "workflow build.yml leftover", "bld-lock"),
    ("npm-oidc-audience-npm-registry-org", "audience npm.registry leftover", "nreg-aud"),
    ("npm-provenance-install-script-mutates-pack", "install script leftover", "inst-lock"),
    ("npm-trusted-publisher-environment-approval-gate", "approval gate leftover", "appr-lock"),
    ("npm-oidc-subject-ref-repository-dispatch", "repository_dispatch leftover", "rd-lock"),
    ("npm-provenance-optionalDependencies-libc-glibc", "glibc libc leftover", "glibc-lock"),
    ("npm-publish-from-podman-runner-no-oidc", "podman runner without OIDC leftover", "pod-lock"),
    ("npm-trusted-publisher-granular-token-still-latest", "granular token leftover", "gran-lock"),
    ("npm-provenance-private-workspace-filter", "workspace filter leftover", "wfilt-lock"),
    ("npm-oidc-permissions-id-token-write-only", "id-token write-only leftover", "idwo-lock"),
    ("npm-provenance-files-field-excludes-lib", "files excludes lib leftover", "nolib-lock"),
    ("npm-trusted-publisher-org-ip-allowlist", "org IP allowlist leftover", "ip-lock"),
    ("npm-oidc-job-container-workdir-mismatch", "container workdir leftover", "cwdir-lock"),
    ("npm-provenance-lockfileVersion-2-vs-1", "lockfileVersion 2 leftover", "lf21-lock"),
    ("npm-publish-access-public-unscoped-attest", "public unscoped leftover", "punsc-lock"),
    ("npm-trusted-publisher-workflow-call-secrets-none", "workflow_call secrets none leftover", "wcsn-lock"),
    ("npm-oidc-issuer-woodpecker-vs-github", "Woodpecker issuer leftover", "wood-lock"),
    ("npm-provenance-bin-field-array-subject", "bin array subject leftover", "bina-lock"),
    ("npm-trusted-publisher-environment-wait-timer-15", "wait_timer 15 leftover", "wt15-lock"),
    ("npm-oidc-audience-pkg-github-com", "audience pkg.github leftover", "pkggh-lock"),
    ("npm-provenance-os-cpu-optional-darwin-arm64", "darwin-arm64 leftover", "darm-lock"),
    ("npm-publish-provenance-omit-then-true", "omit then true leftover", "ott-lock"),
    ("npm-trusted-publisher-act-local-no-oidc", "act local no OIDC leftover", "act-lock"),
]

PYPI = [
    ("pypi-trusted-publisher-workflow-path-workflows-dir", "workflows dir leftover", "release.yml path"),
    ("pypi-oidc-issuer-jenkins-oidc-vs-github", "Jenkins OIDC leftover", "GitHub OIDC issuer"),
    ("pypi-attestation-sdist-only-missing-wheel", "sdist-only leftover", "sdist+wheel pair"),
    ("pypi-twine-attestations-xml-not-dsse", "XML attestation leftover", "DSSE envelope"),
    ("pypi-trusted-publisher-environment-name-ship-typo", "environment ship typo leftover", "environment production"),
    ("pypi-oidc-job-container-id-token-read", "container id-token read leftover", "runner id-token"),
    ("pypi-hatch-index-artifactory-url-leftover", "hatch artifactory leftover", "prod PyPI index"),
    ("pypi-uv-publish-trusted-publishing-never", "uv never leftover", "uv trusted publishing"),
    ("pypi-poetry-keyring-backend-file-leftover", "poetry keyring file leftover", "OIDC trusted publisher"),
    ("pypi-oidc-subject-workflow-ref-heads-stable", "workflow ref heads/stable leftover", "exact tag ref"),
    ("pypi-attestation-pep740-envelope-missing", "PEP 740 envelope leftover", "pep740 envelope"),
    ("pypi-trusted-publisher-project-name-hyphens", "hyphen project leftover", "normalized PyPI name"),
    ("pypi-oidc-issuer-azure-pipelines-vs-github", "Azure Pipelines leftover", "GitHub OIDC issuer"),
    ("pypi-twine-config-file-env-leftover", "twine env leftover", "OIDC trusted publishing"),
    ("pypi-trusted-publisher-workflow-call-ref-main", "workflow_call main leftover", "sha-pinned reusable workflow"),
    ("pypi-oidc-job-services-rabbit-sidecar", "rabbit sidecar leftover", "bare runner OIDC"),
    ("pypi-attestation-wheel-manylinux2010-vs-2-28", "manylinux2010 leftover", "manylinux_2_28 attestation"),
    ("pypi-hatch-index-user-pass-vs-oidc", "hatch user/pass leftover", "hatch trusted publishing"),
    ("pypi-uv-publish-check-url-devpi-legacy", "uv devpi leftover", "uv check-url pypi.org"),
    ("pypi-poetry-http-basic-pypi-file-xor", "poetry http-basic leftover", "poetry OIDC"),
    ("pypi-trusted-publisher-environment-gate-reviewers", "gate reviewers leftover", "immediate environment"),
    ("pypi-oidc-issuer-teamcity-vs-github", "TeamCity leftover", "GitHub OIDC issuer"),
    ("pypi-attestation-attestations-dir-zip-pair", "zip attestations leftover", "wheel+sdist attestations"),
    ("pypi-twine-non-interactive-skip-existing", "non-interactive skip leftover", "twine attestations required"),
]

MAVEN = [
    ("maven-gpg-sign-sources-only-missing-jar", "sources-only leftover", "sro-stg"),
    ("maven-central-portal-publishing-type-user-timeout", "user-managed timeout leftover", "umt-stg"),
    ("maven-gpg-keyring-agent-pid-stale", "stale agent pid leftover", "pid-stg"),
    ("maven-gpg-passphrase-file-xor-env", "passphrase file leftover", "pfile-stg"),
    ("maven-central-bundle-missing-module-md5sum", "module md5 leftover", "mmd5-stg"),
    ("maven-gpg-useagent-true-pinentry-gnome", "pinentry gnome leftover", "gnom-stg"),
    ("maven-ossrh-staging-profile-id-disabled", "disabled profile leftover", "dis-stg"),
    ("maven-gpg-sign-asc-armor-version-header", "armor version leftover", "aver-stg"),
    ("maven-central-publisher-api-namespace-hold", "namespace hold leftover", "hold-stg"),
    ("maven-gpg-digest-ripemd-vs-sha256-policy", "RIPEMD leftover", "ripe-stg"),
    ("maven-settings-gpg-executable-snap-classic", "snap classic leftover", "snapc-stg"),
    ("maven-gpg-skip-tests-asc", "skip tests asc leftover", "sta-stg"),
    ("maven-gpg-sign-main-only-missing-javadoc", "main-only leftover", "maino-stg"),
    ("maven-central-portal-deployment-status-pending", "pending deployment leftover", "pendd-stg"),
    ("maven-gpg-homedir-relative-dot-gnupg", "dot gnupg leftover", "dotg-stg"),
    ("maven-gpg-sign-plugin-skipTests-true", "skipTests leftover", "skt-stg"),
    ("maven-central-user-token-revoked", "revoked token leftover", "revt-stg"),
    ("maven-gpg-signer-class-bc-legacy", "BC legacy leftover", "bcl-stg"),
    ("maven-settings-server-ossrh-releases-id", "ossrh releases leftover", "orel-stg"),
    ("maven-gpg-exclude-classifiers-tests-only", "exclude tests leftover", "ext-stg"),
    ("maven-central-bundle-missing-module-sha256", "module sha256 leftover", "s256-stg"),
    ("maven-gpg-sign-attached-sources-missing", "attached sources leftover", "asrc-stg"),
    ("maven-ossrh-s01-host-after-portal-redirect", "s01 redirect leftover", "redir-stg"),
    ("maven-gpg-passphrase-server-id-ossrh-old", "old ossrh passphrase leftover", "oold-stg"),
]

CRATES = [
    ("crates-yank-vs-cargo-outdated-root", "cargo-outdated root leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-deny-bans-cfg", "cargo-deny bans cfg leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-audit-fix", "cargo-audit fix leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-cyclonedx-v1-6", "cargo-cyclonedx v1.6 leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-modules-structure-json", "cargo-modules structure leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-shear-unused-dev", "cargo-shear unused-dev leftover", "sparse yank index"),
    ("crates-yank-vs-crates-io-api-v2-owners", "crates.io api v2 owners leftover", "sparse yank index"),
    ("crates-yank-vs-lib-rs-crate-json", "lib.rs crate json leftover", "sparse yank index"),
    ("crates-yank-vs-docsrs-source-zip", "docs.rs source zip leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-release-config-toml", "cargo-release toml leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-clone-sparse", "cargo-clone sparse leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-info-versions", "cargo info versions leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-tree-prefix", "cargo-tree prefix leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-minimal-versions-workspace", "minimal-versions workspace leftover", "sparse yank index"),
    ("crates-yank-vs-crates-io-api-v1-keywords", "crates.io api v1 keywords leftover", "sparse yank index"),
    ("crates-yank-vs-lib-rs-owners-html", "lib.rs owners html leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-public-api-diff-html", "cargo-public-api html leftover", "sparse yank index"),
    ("crates-yank-vs-rustdoc-scrape-examples-html", "rustdoc scrape html leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-dist-plan", "cargo-dist plan leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-semver-checks-baseline-krate", "semver-checks krate leftover", "sparse yank index"),
    ("crates-yank-vs-crates-io-trustpub-html", "crates.io trustpub html leftover", "sparse yank index"),
    ("crates-yank-vs-lib-rs-atom1", "lib.rs atom1 leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-show-asm-att", "cargo-show-asm att leftover", "sparse yank index"),
    ("crates-yank-vs-docsrs-rustdoc-json-stable", "docs.rs rustdoc stable leftover", "sparse yank index"),
]

BREW = [
    ("homebrew-bottle-rebuild-vs-uses-from-macos-bzip2", "uses_from_macos bzip2 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-depends-on-macos-monterey", "depends_on macos monterey leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-head-spec-branch", "head branch leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-patch-data-p2", "patch DATA p2 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-resource-mirror-only", "resource mirror leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-keg-only-because-provided", "keg_only provided leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-disable-because-unmaintained", "disable unmaintained leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-deprecate-because-repo-archived", "deprecate archived leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-service-keep-alive-successful-exit", "service successful_exit leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-std-cargo-args", "std_cargo_args leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-on-sonoma-if-arm", "on_sonoma arm leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-depends-on-arch-x86-64", "depends_on arch x86 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-tap-migrations-yml", "tap_migrations yml leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-fails-with-gcc-13", "fails_with gcc 13 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-cxxstdlib-check-libcxx", "cxxstdlib check leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-post-install-ln", "post_install ln leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-caveats-launchctl", "caveats launchctl leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-depends-on-node", "depends_on node leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-option-universal-binary-on", "option universal leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-needs-sse4", "needs sse4 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-on-linux-musl", "on_linux musl leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-version-scheme-two", "version_scheme 2 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-revision-and-rebuild", "revision and rebuild leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-stable-url-only-no-mirror", "stable url only leftover", "rebuilt bottle sha"),
]

NIX = [
    ("nix-fetchFromBitbucket-rev-vs-nar", "Bitbucket rev leftover", "NAR of Bitbucket archive"),
    ("nix-fetchzip-url-vs-nar", "fetchzip url leftover", "NAR of zip"),
    ("nix-fetchTarball-name-vs-nar-of-tar", "fetchTarball name leftover", "NAR of tarball"),
    ("nix-fetchPypi-extension-vs-nar", "fetchPypi extension leftover", "NAR of PyPI sdist"),
    ("nix-fetchCrate-version-vs-nar", "fetchCrate version leftover", "NAR of crates.io crate"),
    ("nix-fetchFromGitiles-path-vs-nar", "Gitiles path leftover", "NAR of Gitiles archive"),
    ("nix-fetchsvn-url-vs-nar", "svn url leftover", "NAR of svn export"),
    ("nix-fetchhg-url-vs-nar", "hg url leftover", "NAR of hg archive"),
    ("nix-fetchcvs-cvsRoot-vs-nar", "CVSROOT leftover", "NAR of CVS export"),
    ("nix-fetchFromAzureDevOps-org-vs-nar", "Azure org leftover", "NAR of Azure archive"),
    ("nix-fetchgit-fetchTags-vs-nar", "fetchTags leftover", "NAR of no-tags checkout"),
    ("nix-fetchurl-executable-vs-nar", "fetchurl executable leftover", "NAR of fetched url"),
    ("nix-fetchFromGitHub-varPrefix-vs-nar", "GitHub varPrefix leftover", "NAR of archive"),
    ("nix-fetchgit-url-vs-nar", "fetchgit url leftover", "NAR of plain fetchgit"),
    ("nix-fetchFromGitLab-repo-vs-nar", "GitLab repo leftover", "NAR of https archive"),
    ("nix-fetchgit-leaveDotGit-false-vs-nar", "leaveDotGit false leftover", "NAR of checkout"),
    ("nix-fetchFromGitea-repo-vs-nar", "Gitea repo leftover", "NAR of public Gitea archive"),
    ("nix-fetchurl-hashMode-flat-vs-nar-store", "flat hashMode leftover", "NAR of fetchurl store path"),
    ("nix-fetchFromCgit-url-vs-nar", "cgit url leftover", "NAR of cgit archive"),
    ("nix-fetchgit-rev-vs-nar-of-commit", "rev leftover", "NAR of pinned fetchgit"),
    ("nix-fetchFromSourcehut-repo-vs-nar", "Sourcehut repo leftover", "NAR of sourcehut archive"),
    ("nix-fetchzip-extraPostFetch-vs-nar", "extraPostFetch leftover", "NAR of zip"),
    ("nix-builtins-fetchurl-vs-nar", "builtins.fetchurl leftover", "NAR of fetchurl locked"),
    ("nix-fetchgit-fetchSubmodules-false-vs-nar", "no-submodules leftover", "NAR of no-submodules checkout"),
]

NUGET = [
    ("nuget-snupkg-embed-untracked-sources-on-ci", "EmbedUntrackedSources CI leftover", "untracked-ci"),
    ("nuget-snupkg-sourcelink-azure-repos-server-vs-cloud", "Azure Repos Server leftover", "azdo-srv"),
    ("nuget-snupkg-deterministic-pathmap-empty", "empty PathMap leftover", "pathmap-empty"),
    ("nuget-snupkg-debug-type-pdbonly-vs-embedded", "DebugType pdbonly leftover", "pdbonly-emb"),
    ("nuget-snupkg-include-symbols-true-no-snupkg", "IncludeSymbols no snupkg leftover", "sym-nosnupkg"),
    ("nuget-snupkg-sourcelink-bitbucket-data-center-vs-cloud", "Bitbucket DC leftover", "bb-dc"),
    ("nuget-snupkg-continuous-integration-build-unset", "CI build unset leftover", "ciunset"),
    ("nuget-snupkg-embed-all-sources-true-no-repo-url", "EmbedAllSources no repo leftover", "embed-norepourl"),
    ("nuget-snupkg-publish-gitlab-nuget-v3", "GitLab nuget v3 leftover", "gl-n3"),
    ("nuget-snupkg-pdb-checksum-algorithm-md5", "PDB checksum MD5 leftover", "pdb-md5"),
    ("nuget-snupkg-sourcelink-gitea-enterprise-vs-cloud", "Gitea enterprise leftover", "gitea-ent"),
    ("nuget-snupkg-embedded-files-filter-wildcard", "embedded files wildcard leftover", "embed-wild"),
    ("nuget-snupkg-source-root-unc-path", "UNC SourceRoot leftover", "unc-root"),
    ("nuget-snupkg-symbolpackageformat-snupkg-and-symbols", "dual format leftover", "dual-fmt"),
    ("nuget-snupkg-repository-type-vs-url", "RepositoryType leftover", "repo-type"),
    ("nuget-snupkg-sourcelink-codeberg-pages-git-vs-github", "Codeberg pages leftover", "cb-pg"),
    ("nuget-snupkg-publish-github-packages-nuget-v1", "GPR nuget v1 leftover", "gpr-n1"),
    ("nuget-snupkg-portable-pdb-guid-empty", "portable PDB empty guid leftover", "pdb-empty"),
    ("nuget-snupkg-sourcelink-sourcehut-hg-vs-github", "sourcehut hg leftover", "srht-hg"),
    ("nuget-snupkg-source-link-mapped-path-unc", "UNC mapped path leftover", "unc-map"),
    ("nuget-snupkg-publish-myget-v3-vs-nuget-org", "MyGet v3 leftover", "myget-v3"),
    ("nuget-snupkg-debug-type-none-vs-embedded", "DebugType none leftover", "none-emb"),
    ("nuget-snupkg-include-source-revision-unset", "IncludeSourceRevision unset leftover", "src-unset"),
    ("nuget-snupkg-sourcelink-forgejo-enterprise-vs-github", "Forgejo enterprise leftover", "fj-ent"),
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
"""Unique mill: package-release-factory attestation wave-11 (r836+).

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

CATALOG_FIRST = 836
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
        raise SystemExit("dup slug or plant in attest wave11 catalog")
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
    out = HERE / "pkg-mill-attest-wave11.py"
    out.write_text(body)
    print(f"wrote {out} pairs={N*4} minerals_used_estimate={N*8} minerals_avail={len(MINERALS)}")


if __name__ == "__main__":
    main()
