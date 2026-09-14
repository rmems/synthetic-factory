#!/usr/bin/env python3
"""Generate experiments/pkg-mill-attest-wave13.py from a unique plant catalog."""
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
    ("cosign-verify-oci-referrer-platform-vs-type", "referrer platform leftover", "OCI referrer type"),
    ("cosign-sign-bundle-dev-vs-prod-dsse", "dev bundle leftover", "prod DSSE bundle"),
    ("cosign-fulcio-jenkins-oidc-vs-github", "Jenkins OIDC leftover", "GitHub Fulcio issuer"),
    ("cosign-rekor-entry-kind-intoto-vs-dsse", "in-toto leftover", "DSSE Rekor kind"),
    ("cosign-verify-tsa-leaf-expired", "expired TSA leaf leftover", "current TSA leaf"),
    ("cosign-policy-identity-run-attempt-vs-path", "run attempt leftover", "workflow path identity"),
    ("cosign-sign-kms-azure-hsm-vs-software", "Azure HSM leftover", "Azure software key"),
    ("cosign-verify-identity-push-vs-tag", "push identity leftover", "tag identity"),
    ("cosign-attach-predicate-sarif-vs-slsa", "SARIF leftover", "SLSA predicate"),
    ("cosign-copy-signature-tag-vs-digest", "sig tag leftover", "digest signature"),
    ("cosign-verify-tuf-root-expired", "expired TUF root leftover", "refreshed TUF root"),
    ("cosign-sign-recursive-provenance-partial", "partial provenance leftover", "full index provenance"),
    ("cosign-policy-ctlog-url-stale", "stale CT URL leftover", "current CT URL"),
    ("cosign-fulcio-uri-san-repo-template", "template repo SAN leftover", "canonical repo SAN"),
    ("cosign-verify-bundle-hash-algo-sha1-vs-sha256", "sha1 leftover", "sha256 payload algo"),
    ("cosign-sign-sk-piv-slot-82-vs-9a", "PIV slot 82 leftover", "PIV slot 9a"),
    ("cosign-oidc-issuer-circle-vs-github", "Circle leftover", "GitHub Actions OIDC"),
    ("cosign-verify-cert-notafter-skew-hours", "notAfter hours leftover", "NTP-aligned notAfter"),
    ("cosign-policy-builder-id-ref-mismatch", "builder ref leftover", "exact builder id"),
    ("cosign-sign-payload-intoto-cdx-xml", "in-toto CDX-XML leftover", "in-toto SLSA payload"),
    ("cosign-rekor-inclusion-proof-shard-id", "shard id leftover", "signed shard id"),
    ("cosign-verify-oci-index-variant-filter", "variant filter leftover", "full OCI index"),
    ("cosign-sign-annotation-predicate-media-type", "predicate media leftover", "matching media type"),
    ("cosign-policy-max-cert-lifetime-hours", "max cert hours leftover", "policy hours"),
]

NPM = [
    ("npm-provenance-bundleDependencies-hoist-pattern", "hoist pattern leftover", "hpatt-lock"),
    ("npm-trusted-publisher-workflow-filename-deploy-yml", "workflow deploy.yml leftover", "dep-lock"),
    ("npm-oidc-audience-npm-org", "audience npm.org leftover", "norg-aud"),
    ("npm-provenance-prepare-mutates-pack", "prepare leftover", "prep-lock"),
    ("npm-trusted-publisher-environment-required-approvers", "required approvers leftover", "rapp-lock"),
    ("npm-oidc-subject-ref-workflow-call", "workflow_call leftover", "wcall-lock"),
    ("npm-provenance-optionalDependencies-libc-musl-static", "musl static leftover", "mstat-lock"),
    ("npm-publish-from-firecracker-runner-no-oidc", "firecracker without OIDC leftover", "fc-lock"),
    ("npm-trusted-publisher-session-token-still-latest", "session token leftover", "sess-lock"),
    ("npm-provenance-private-workspace-exclude", "workspace exclude leftover", "wexc-lock"),
    ("npm-oidc-permissions-id-token-write-attest", "attest write leftover", "attw-lock"),
    ("npm-provenance-files-field-includes-docs", "files includes docs leftover", "docs-lock"),
    ("npm-trusted-publisher-org-sso-saml", "org SAML leftover", "saml-lock"),
    ("npm-oidc-job-container-user-node", "container node leftover", "cnode-lock"),
    ("npm-provenance-lockfileVersion-1-vs-2", "lockfileVersion 1 leftover", "lf12-lock"),
    ("npm-publish-access-public-scoped-attest", "public scoped leftover", "psco-lock"),
    ("npm-trusted-publisher-workflow-call-secrets-map", "workflow_call secrets map leftover", "wcsm-lock"),
    ("npm-oidc-issuer-travis-vs-github", "Travis issuer leftover", "trav-lock"),
    ("npm-provenance-bin-field-map-subject", "bin map leftover", "binm-lock"),
    ("npm-trusted-publisher-environment-wait-timer-45", "wait_timer 45 leftover", "wt45-lock"),
    ("npm-oidc-audience-yarnpkg-com", "audience yarnpkg leftover", "ypkg-lock"),
    ("npm-provenance-os-cpu-optional-linux-riscv64", "linux-riscv leftover", "risc-lock"),
    ("npm-publish-provenance-file-then-true", "file then true leftover", "ftt-lock"),
    ("npm-trusted-publisher-github-hosted-large-no-oidc", "large runner leftover", "large-lock"),
]

PYPI = [
    ("pypi-trusted-publisher-workflow-path-monorepo", "monorepo workflow leftover", "release.yml path"),
    ("pypi-oidc-issuer-gitea-vs-github", "Gitea leftover", "GitHub OIDC issuer"),
    ("pypi-attestation-purelib-missing-sdist", "purelib leftover", "sdist+wheel pair"),
    ("pypi-twine-attestations-msgpack-not-dsse", "msgpack leftover", "DSSE envelope"),
    ("pypi-trusted-publisher-environment-name-qa-typo", "environment qa leftover", "environment production"),
    ("pypi-oidc-job-container-id-token-none-explicit", "container none leftover", "runner id-token"),
    ("pypi-hatch-index-codeartifact-url-leftover", "hatch codeartifact leftover", "prod PyPI index"),
    ("pypi-uv-publish-trusted-publishing-force", "uv force leftover", "uv trusted publishing"),
    ("pypi-poetry-keyring-backend-env-leftover", "poetry keyring env leftover", "OIDC trusted publisher"),
    ("pypi-oidc-subject-workflow-ref-heads-ship", "workflow ref heads/ship leftover", "exact tag ref"),
    ("pypi-attestation-pep740-payload-missing", "PEP 740 payload leftover", "pep740 payload"),
    ("pypi-trusted-publisher-project-name-spaces", "spaced project leftover", "normalized PyPI name"),
    ("pypi-oidc-issuer-codeberg-ci-actions-vs-github", "Codeberg CI leftover", "GitHub OIDC issuer"),
    ("pypi-twine-config-file-ini-leftover", "twine ini leftover", "OIDC trusted publishing"),
    ("pypi-trusted-publisher-workflow-call-ref-v2", "workflow_call v2 leftover", "sha-pinned reusable workflow"),
    ("pypi-oidc-job-services-minio-sidecar", "minio sidecar leftover", "bare runner OIDC"),
    ("pypi-attestation-wheel-musllinux-1-1-vs-1-2", "musllinux 1.1 leftover", "musllinux 1.2 attestation"),
    ("pypi-hatch-index-env-token-vs-oidc", "hatch env token leftover", "hatch trusted publishing"),
    ("pypi-uv-publish-check-url-codeartifact", "uv codeartifact leftover", "uv check-url pypi.org"),
    ("pypi-poetry-http-basic-env-vs-oidc", "poetry http-basic env leftover", "poetry OIDC"),
    ("pypi-trusted-publisher-environment-required-reviewers-3", "three reviewers leftover", "immediate environment"),
    ("pypi-oidc-issuer-semaphore-vs-github", "Semaphore leftover", "GitHub OIDC issuer"),
    ("pypi-attestation-attestations-dir-cbor-pair", "cbor leftover", "wheel+sdist attestations"),
    ("pypi-twine-skip-existing-attestations-dir", "skip-existing dir leftover", "twine attestations required"),
]

MAVEN = [
    ("maven-gpg-sign-bom-only-missing-jar", "bom-only leftover", "bom-stg"),
    ("maven-central-portal-publishing-type-async-hang", "async hang leftover", "asyn-stg"),
    ("maven-gpg-keyring-agent-tty-stale", "stale tty leftover", "tty-stg"),
    ("maven-gpg-passphrase-askpass-xor-env", "askpass leftover", "ask-stg"),
    ("maven-central-bundle-missing-bom-checksum", "bom checksum leftover", "bomc-stg"),
    ("maven-gpg-useagent-true-pinentry-mac", "pinentry mac leftover", "mac-stg"),
    ("maven-ossrh-staging-profile-id-frozen", "frozen profile leftover", "fro-stg"),
    ("maven-gpg-sign-asc-armor-hash-header", "armor hash leftover", "ahash-stg"),
    ("maven-central-publisher-api-namespace-quarantine", "quarantine leftover", "quar-stg"),
    ("maven-gpg-digest-blake2-vs-sha256-policy", "blake2 leftover", "bl2-stg"),
    ("maven-settings-gpg-executable-guix-path", "guix leftover", "guix-stg"),
    ("maven-gpg-skip-bom-asc", "skip bom leftover", "sbom-stg"),
    ("maven-gpg-sign-bom-only-missing-modules", "bom modules leftover", "bmod-stg"),
    ("maven-central-portal-deployment-status-scanning", "scanning leftover", "scan-stg"),
    ("maven-gpg-homedir-gnupg2-vs-absolute", "gnupg2 leftover", "g2-stg"),
    ("maven-gpg-sign-plugin-skip-bom", "skip bom plugin leftover", "skb-stg"),
    ("maven-central-user-token-suspended", "suspended token leftover", "sus-stg"),
    ("maven-gpg-signer-class-bc-jdk18", "BC jdk18 leftover", "bc18-stg"),
    ("maven-settings-server-ossrh-staging-id", "ossrh staging leftover", "ostg-stg"),
    ("maven-gpg-exclude-classifiers-bom", "exclude bom leftover", "exb-stg"),
    ("maven-central-bundle-missing-module-blake2", "module blake2 leftover", "mbl2-stg"),
    ("maven-gpg-sign-attached-bom-missing", "attached bom leftover", "abom-stg"),
    ("maven-ossrh-s01-host-after-portal-vanity", "s01 vanity leftover", "van-stg"),
    ("maven-gpg-passphrase-server-id-staging-old", "old staging passphrase leftover", "sold-stg"),
]

CRATES = [
    ("crates-yank-vs-cargo-outdated-recursive", "cargo-outdated recursive leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-deny-sources-cfg", "cargo-deny sources cfg leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-audit-offline", "cargo-audit offline leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-cyclonedx-v1-3", "cargo-cyclonedx v1.3 leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-modules-cycles", "cargo-modules cycles leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-shear-unused-target", "cargo-shear unused-target leftover", "sparse yank index"),
    ("crates-yank-vs-crates-io-api-v2-reverse", "crates.io api v2 reverse leftover", "sparse yank index"),
    ("crates-yank-vs-lib-rs-badge", "lib.rs badge leftover", "sparse yank index"),
    ("crates-yank-vs-docsrs-source-crate", "docs.rs source crate leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-release-replace", "cargo-release replace leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-clone-vendor", "cargo-clone vendor leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-info-yanked", "cargo info yanked leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-tree-charset", "cargo-tree charset leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-minimal-versions-locked", "minimal-versions locked leftover", "sparse yank index"),
    ("crates-yank-vs-crates-io-api-v1-badges", "crates.io api v1 badges leftover", "sparse yank index"),
    ("crates-yank-vs-lib-rs-badge-svg", "lib.rs badge svg leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-public-api-diff-plain", "cargo-public-api plain leftover", "sparse yank index"),
    ("crates-yank-vs-rustdoc-scrape-examples-txt", "rustdoc scrape txt leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-dist-init", "cargo-dist init leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-semver-checks-baseline-lib", "semver-checks lib leftover", "sparse yank index"),
    ("crates-yank-vs-crates-io-trustpub-badge", "crates.io trustpub badge leftover", "sparse yank index"),
    ("crates-yank-vs-lib-rs-opml", "lib.rs opml leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-show-asm-llvm", "cargo-show-asm llvm leftover", "sparse yank index"),
    ("crates-yank-vs-docsrs-rustdoc-json-dev", "docs.rs rustdoc dev leftover", "sparse yank index"),
]

BREW = [
    ("homebrew-bottle-rebuild-vs-uses-from-macos-ncurses", "uses_from_macos ncurses leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-depends-on-macos-catalina", "depends_on macos catalina leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-head-spec-commit", "head commit leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-patch-data-p4", "patch DATA p4 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-resource-livecheck", "resource livecheck leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-keg-only-because-shadowed-by-system", "keg_only system leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-disable-because-cannot-build", "disable cannot_build leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-deprecate-because-moved", "deprecate moved leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-service-keep-alive-error", "service error leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-std-zig-args", "std_zig leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-on-monterey-block", "on_monterey leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-depends-on-arch-riscv", "depends_on arch riscv leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-tap-migrations-jsonl", "tap_migrations jsonl leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-fails-with-gcc-11", "fails_with gcc 11 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-cxxstdlib-check-libstdc", "cxxstdlib libstdc leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-post-install-touch", "post_install touch leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-caveats-sysctl", "caveats sysctl leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-depends-on-go", "depends_on go leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-option-without-default-names", "option without names leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-needs-neon", "needs neon leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-on-linux-android", "on_linux android leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-version-scheme-four", "version_scheme 4 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-revision-one", "revision 1 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-stable-url-sha256", "stable sha leftover", "rebuilt bottle sha"),
]

NIX = [
    ("nix-fetchFromBitbucket-workspace-vs-nar", "Bitbucket workspace leftover", "NAR of Bitbucket archive"),
    ("nix-fetchzip-sha256-vs-nar-zip", "fetchzip sha leftover", "NAR of zip"),
    ("nix-fetchTarball-hash-vs-nar-tar", "fetchTarball hash leftover", "NAR of tarball"),
    ("nix-fetchPypi-sha256-vs-nar-sdist", "fetchPypi sha leftover", "NAR of PyPI sdist"),
    ("nix-fetchCrate-sha-vs-nar-crate", "fetchCrate sha leftover", "NAR of crates.io crate"),
    ("nix-fetchFromGitiles-hash-vs-nar", "Gitiles hash leftover", "NAR of Gitiles archive"),
    ("nix-fetchsvn-hash-vs-nar-export", "svn hash leftover", "NAR of svn export"),
    ("nix-fetchhg-hash-vs-nar-archive", "hg hash leftover", "NAR of hg archive"),
    ("nix-fetchcvs-hash-vs-nar-export", "CVS hash leftover", "NAR of CVS export"),
    ("nix-fetchFromAzureDevOps-org-sha-vs-nar", "Azure org sha leftover", "NAR of Azure archive"),
    ("nix-fetchgit-fetchTags-false-vs-nar", "no-tags leftover", "NAR of checkout"),
    ("nix-fetchurl-sha256-vs-nar-url", "fetchurl sha leftover", "NAR of fetched url"),
    ("nix-fetchFromGitHub-owner-vs-nar", "GitHub owner leftover", "NAR of archive"),
    ("nix-fetchgit-shallow-vs-nar", "shallow leftover", "NAR of fetchgit"),
    ("nix-fetchFromGitLab-namespace-vs-nar", "GitLab namespace leftover", "NAR of https archive"),
    ("nix-fetchgit-ref-vs-nar", "ref leftover", "NAR of pinned fetchgit"),
    ("nix-fetchFromGitea-hash-vs-nar", "Gitea hash leftover", "NAR of public Gitea archive"),
    ("nix-fetchurl-sri-vs-nar-store", "fetchurl sri leftover", "NAR of fetchurl store path"),
    ("nix-fetchFromCgit-hash-vs-nar", "cgit hash leftover", "NAR of cgit archive"),
    ("nix-fetchgit-commit-vs-nar", "commit leftover", "NAR of pinned fetchgit"),
    ("nix-fetchFromSourcehut-hash-vs-nar", "Sourcehut hash leftover", "NAR of sourcehut archive"),
    ("nix-fetchzip-sha-vs-nar-root", "fetchzip sha leftover", "NAR of zip"),
    ("nix-builtins-filterSource-vs-nar", "builtins.filterSource leftover", "NAR of filtered path"),
    ("nix-fetchgit-fetchWorktrees-true-vs-nar", "worktrees leftover", "NAR of checkout"),
]

NUGET = [
    ("nuget-snupkg-embed-untracked-sources-release", "EmbedUntrackedSources release leftover", "untracked-rel"),
    ("nuget-snupkg-sourcelink-azure-repos-onprem-vs-cloud", "Azure Repos onprem leftover", "azdo-onp"),
    ("nuget-snupkg-deterministic-pathmap-absolute", "absolute PathMap leftover", "pathmap-abs"),
    ("nuget-snupkg-debug-type-full-vs-embedded", "DebugType full leftover", "full-emb"),
    ("nuget-snupkg-include-symbols-snupkg-true-no-src", "IncludeSymbols no src leftover", "sym-nosrc"),
    ("nuget-snupkg-sourcelink-bitbucket-workspace-vs-github", "Bitbucket workspace leftover", "bb-wsgh"),
    ("nuget-snupkg-continuous-integration-build-false-ci", "CI build false leftover", "cifalse"),
    ("nuget-snupkg-embed-all-sources-true-with-link", "EmbedAllSources with link leftover", "embed-link"),
    ("nuget-snupkg-publish-gitlab-nuget-v4", "GitLab nuget v4 leftover", "gl-n4"),
    ("nuget-snupkg-pdb-checksum-algorithm-blake2", "PDB checksum blake2 leftover", "pdb-bl2"),
    ("nuget-snupkg-sourcelink-gitea-tea-pages-vs-github", "Gitea tea pages leftover", "gitea-tpg"),
    ("nuget-snupkg-embedded-files-filter-regex", "embedded files regex leftover", "embed-re"),
    ("nuget-snupkg-source-root-device-path", "device SourceRoot leftover", "dev-root"),
    ("nuget-snupkg-symbolpackageformat-snupkg-vs-none", "snupkg vs none leftover", "fmt-snp"),
    ("nuget-snupkg-repository-commit-vs-url", "RepositoryCommit leftover", "repo-cu"),
    ("nuget-snupkg-sourcelink-codeberg-pages-vs-github-app", "Codeberg pages leftover", "cb-pga"),
    ("nuget-snupkg-publish-github-packages-nuget-v5", "GPR nuget v5 leftover", "gpr-n5"),
    ("nuget-snupkg-portable-pdb-guid-ffff", "portable PDB ffff leftover", "pdb-ffff"),
    ("nuget-snupkg-sourcelink-sourcehut-git-raw", "sourcehut raw leftover", "srht-raw"),
    ("nuget-snupkg-source-link-mapped-path-device", "device mapped path leftover", "dev-map"),
    ("nuget-snupkg-publish-myget-v4-vs-nuget-org", "MyGet v4 leftover", "myget-v4"),
    ("nuget-snupkg-debug-type-pdbonly-vs-full", "DebugType pdbonly leftover", "pdbonly-full"),
    ("nuget-snupkg-include-source-revision-false-ci", "IncludeSourceRevision false leftover", "src-fci"),
    ("nuget-snupkg-sourcelink-forgejo-tea-pages-vs-github", "Forgejo tea pages leftover", "fj-tpg"),
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
"""Unique mill: package-release-factory attestation wave-13 (r1028+).

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

CATALOG_FIRST = 1028
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
        raise SystemExit("dup slug or plant in attest wave13 catalog")
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
    out = HERE / "pkg-mill-attest-wave13.py"
    out.write_text(body)
    print(f"wrote {out} pairs={N*4} minerals_used_estimate={N*8} minerals_avail={len(MINERALS)}")


if __name__ == "__main__":
    main()
