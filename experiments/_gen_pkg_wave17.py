#!/usr/bin/env python3
"""Generate experiments/pkg-mill-attest-wave17.py from a unique plant catalog."""
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
    ("cosign-verify-oci-referrer-features-vs-type", "referrer features leftover", "OCI referrer type"),
    ("cosign-sign-bundle-hotfix-vs-prod-dsse", "hotfix bundle leftover", "prod DSSE bundle"),
    ("cosign-fulcio-keycloak-oidc-vs-github", "Keycloak Fulcio leftover", "GitHub Fulcio issuer"),
    ("cosign-rekor-entry-kind-intoto-vs-rfc3161-dsse", "in-toto leftover", "RFC3161 DSSE kind"),
    ("cosign-verify-tsa-chain-revoked", "revoked TSA leftover", "current TSA chain"),
    ("cosign-policy-identity-strategy-vs-path", "strategy leftover", "workflow path identity"),
    ("cosign-sign-kms-oracle-vs-aws", "Oracle KMS leftover", "AWS KMS key"),
    ("cosign-verify-identity-fork-vs-tag", "fork identity leftover", "tag identity"),
    ("cosign-attach-predicate-scitt-vs-slsa", "SCITT leftover", "SLSA predicate"),
    ("cosign-copy-signature-bundle-vs-tlog", "bundle leftover", "tlog signature"),
    ("cosign-verify-tuf-root-stale", "stale TUF root leftover", "refreshed TUF root"),
    ("cosign-sign-recursive-scitt-partial", "partial SCITT leftover", "full index SCITT"),
    ("cosign-policy-ctlog-url-expired", "expired CT URL leftover", "current CT URL"),
    ("cosign-fulcio-uri-san-repo-moved-org", "moved org SAN leftover", "canonical org SAN"),
    ("cosign-verify-bundle-hash-algo-whirlpool-vs-sha256", "whirlpool leftover", "sha256 payload algo"),
    ("cosign-sign-sk-piv-slot-86-vs-9a", "PIV slot 86 leftover", "PIV slot 9a"),
    ("cosign-oidc-issuer-zitadel-vs-github", "Zitadel leftover", "GitHub Actions OIDC"),
    ("cosign-verify-cert-notafter-skew-months", "notAfter months leftover", "NTP-aligned notAfter"),
    ("cosign-policy-builder-id-team-mismatch", "builder team leftover", "exact builder id"),
    ("cosign-sign-payload-intoto-scitt-json", "in-toto SCITT leftover", "in-toto SLSA payload"),
    ("cosign-rekor-inclusion-proof-note-v1", "note v1 leftover", "signed note v1"),
    ("cosign-verify-oci-index-osversion-range", "osversion range leftover", "full OCI index"),
    ("cosign-sign-annotation-predicate-profile-uri", "predicate profile leftover", "matching profile URI"),
    ("cosign-policy-max-cert-lifetime-years", "max cert years leftover", "policy years"),
]

NPM = [
    ("npm-provenance-bundleDependencies-shamefully-hoist", "shamefully-hoist leftover", "shame-lock"),
    ("npm-trusted-publisher-workflow-filename-canary-yml", "workflow canary.yml leftover", "can-lock"),
    ("npm-oidc-audience-npmjs-info", "audience npmjs.info leftover", "ninfo-aud"),
    ("npm-provenance-version-script-mutates-pack", "version script leftover", "ver-lock"),
    ("npm-trusted-publisher-environment-required-reviews", "required reviews leftover", "rrev-lock"),
    ("npm-oidc-subject-ref-check-suite", "check_suite leftover", "csuite-lock"),
    ("npm-provenance-optionalDependencies-libc-haiku", "haiku libc leftover", "haiku-lock"),
    ("npm-publish-from-youki-runner-no-oidc", "youki without OIDC leftover", "youki-lock"),
    ("npm-trusted-publisher-install-token-still-latest", "install token leftover", "instt-lock"),
    ("npm-provenance-private-workspace-filter-invert", "workspace invert leftover", "winv-lock"),
    ("npm-oidc-permissions-id-token-write-statuses", "statuses write leftover", "stsw-lock"),
    ("npm-provenance-files-field-includes-types", "files includes types leftover", "typ-lock"),
    ("npm-trusted-publisher-org-sso-oidc-pkce", "org PKCE leftover", "pkce-lock"),
    ("npm-oidc-job-container-user-guest", "container guest leftover", "cguest-lock"),
    ("npm-provenance-lockfileVersion-9-vs-3", "lockfileVersion 9 leftover", "lf93-lock"),
    ("npm-publish-access-restricted-workspace-scope", "restricted workspace leftover", "rws-lock"),
    ("npm-trusted-publisher-workflow-call-outputs-json", "workflow_call outputs json leftover", "wcoj-lock"),
    ("npm-oidc-issuer-concourse-vs-github", "Concourse leftover", "conc-lock"),
    ("npm-provenance-bin-field-symlink-subject", "bin symlink leftover", "binsy-lock"),
    ("npm-trusted-publisher-environment-wait-timer-240", "wait_timer 240 leftover", "wt240-lock"),
    ("npm-oidc-audience-yarnpkg-info", "audience yarnpkg.info leftover", "yinfo-lock"),
    ("npm-provenance-os-cpu-optional-sunos-x64", "sunos leftover", "sunos-lock"),
    ("npm-publish-provenance-omit-then-true-retry", "omit then true leftover", "ott2-lock"),
    ("npm-trusted-publisher-qemu-ephemeral-no-oidc", "qemu ephemeral leftover", "qemu-lock"),
]

PYPI = [
    ("pypi-trusted-publisher-workflow-path-src-dir", "src workflow leftover", "release.yml path"),
    ("pypi-oidc-issuer-forgejo-ci-vs-github", "Forgejo CI leftover", "GitHub OIDC issuer"),
    ("pypi-attestation-scripts-missing-sdist", "scripts leftover", "sdist+wheel pair"),
    ("pypi-twine-attestations-smile-not-dsse", "SMILE leftover", "DSSE envelope"),
    ("pypi-trusted-publisher-environment-name-hotfix-typo", "environment hotfix leftover", "environment production"),
    ("pypi-oidc-job-container-id-token-request-id", "container request id leftover", "runner id-token"),
    ("pypi-hatch-index-gitlab-pkg-url-leftover", "hatch gitlab leftover", "prod PyPI index"),
    ("pypi-uv-publish-trusted-publishing-audit", "uv audit leftover", "uv trusted publishing"),
    ("pypi-poetry-keyring-backend-mac-leftover", "poetry mac leftover", "OIDC trusted publisher"),
    ("pypi-oidc-subject-workflow-ref-heads-patch", "workflow ref heads/patch leftover", "exact tag ref"),
    ("pypi-attestation-pep740-sct-list-missing", "PEP 740 SCT list leftover", "pep740 SCT list"),
    ("pypi-trusted-publisher-project-name-zwj", "zwj project leftover", "normalized PyPI name"),
    ("pypi-oidc-issuer-woodpecker-ci-hostname-vs-github", "Woodpecker CI hostname leftover", "GitHub OIDC issuer"),
    ("pypi-twine-config-file-dotenv-leftover", "twine dotenv leftover", "OIDC trusted publishing"),
    ("pypi-trusted-publisher-workflow-call-ref-v6", "workflow_call v6 leftover", "sha-pinned reusable workflow"),
    ("pypi-oidc-job-services-pulsar-sidecar", "pulsar sidecar leftover", "bare runner OIDC"),
    ("pypi-attestation-wheel-manylinux_2_34-vs-2-28", "manylinux_2_34 leftover", "manylinux_2_28 attestation"),
    ("pypi-hatch-index-gitlab-token-vs-oidc", "hatch gitlab token leftover", "hatch trusted publishing"),
    ("pypi-uv-publish-check-url-gitlab-legacy", "uv gitlab leftover", "uv check-url pypi.org"),
    ("pypi-poetry-pypi-token-mac-vs-oidc", "poetry mac leftover", "poetry OIDC"),
    ("pypi-trusted-publisher-environment-required-reviewers-7", "seven reviewers leftover", "immediate environment"),
    ("pypi-oidc-issuer-tekton-vs-github", "Tekton leftover", "GitHub OIDC issuer"),
    ("pypi-attestation-attestations-dir-orc-pair", "orc leftover", "wheel+sdist attestations"),
    ("pypi-twine-skip-existing-attest-yaml", "skip-existing yaml leftover", "twine attestations required"),
]

MAVEN = [
    ("maven-gpg-sign-rar-only-missing-jar", "rar-only leftover", "rar-stg"),
    ("maven-central-portal-publishing-type-queue-hang", "queue hang leftover", "queh-stg"),
    ("maven-gpg-keyring-agent-scd-stale", "stale scd leftover", "scd-stg"),
    ("maven-gpg-passphrase-gtk-xor-env", "gtk leftover", "gtk-stg"),
    ("maven-central-bundle-missing-rar-checksum", "rar checksum leftover", "rarc-stg"),
    ("maven-gpg-useagent-true-pinentry-fltk", "pinentry fltk leftover", "fltk-stg"),
    ("maven-ossrh-staging-profile-id-warming", "warming profile leftover", "warm-stg"),
    ("maven-gpg-sign-asc-armor-version-3", "armor v3 leftover", "av3-stg"),
    ("maven-central-publisher-api-namespace-hold-review", "hold-review leftover", "hrev-stg"),
    ("maven-gpg-digest-blake3-vs-sha256-policy", "blake3 leftover", "bl3-stg"),
    ("maven-settings-gpg-executable-xbps-path", "xbps leftover", "xbps-stg"),
    ("maven-gpg-skip-rar-asc", "skip rar leftover", "srar-stg"),
    ("maven-gpg-sign-rar-only-missing-modules", "rar modules leftover", "rmod-stg"),
    ("maven-central-portal-deployment-status-mirroring", "mirroring leftover", "mirr-stg"),
    ("maven-gpg-homedir-gnupg-socketdir-vs-absolute", "socketdir leftover", "sockd-stg"),
    ("maven-gpg-sign-plugin-skip-rar", "skip rar plugin leftover", "skr-stg"),
    ("maven-central-user-token-leaked", "leaked leftover", "leak-stg"),
    ("maven-gpg-signer-class-bc-jdk8", "BC jdk8 leftover", "bc8-stg"),
    ("maven-settings-server-ossrh-mirror-id", "ossrh mirror leftover", "omir-stg"),
    ("maven-gpg-exclude-classifiers-rar", "exclude rar leftover", "exr-stg"),
    ("maven-central-bundle-missing-module-blake3", "module blake3 leftover", "mbl3-stg"),
    ("maven-gpg-sign-attached-rar-missing", "attached rar leftover", "arar-stg"),
    ("maven-ossrh-s01-host-after-portal-anycast", "s01 anycast leftover", "any-stg"),
    ("maven-gpg-passphrase-server-id-mirror-old", "old mirror passphrase leftover", "mold-stg"),
]

CRATES = [
    ("crates-yank-vs-cargo-outdated-ignore", "cargo-outdated ignore leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-deny-bans-offline", "cargo-deny bans offline leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-audit-quiet", "cargo-audit quiet leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-cyclonedx-v1-7", "cargo-cyclonedx v1.7 leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-modules-cfg", "cargo-modules cfg leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-shear-unused-benches", "cargo-shear unused-benches leftover", "sparse yank index"),
    ("crates-yank-vs-crates-io-api-v2-updated", "crates.io api v2 updated leftover", "sparse yank index"),
    ("crates-yank-vs-lib-rs-opensearch", "lib.rs opensearch leftover", "sparse yank index"),
    ("crates-yank-vs-docsrs-source-crate-zst", "docs.rs crate zst leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-release-push", "cargo-release push leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-clone-sparse-offline", "cargo-clone sparse leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-info-docs", "cargo info docs leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-tree-edges-json", "cargo-tree edges json leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-minimal-versions-public", "minimal-versions public leftover", "sparse yank index"),
    ("crates-yank-vs-crates-io-api-v1-downloads-range", "crates.io api v1 downloads leftover", "sparse yank index"),
    ("crates-yank-vs-lib-rs-opensearch-json", "lib.rs opensearch json leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-public-api-diff-yaml", "cargo-public-api yaml leftover", "sparse yank index"),
    ("crates-yank-vs-rustdoc-scrape-examples-typ", "rustdoc scrape typ leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-dist-hosting-json", "cargo-dist hosting leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-semver-checks-baseline-fuzz", "semver-checks fuzz leftover", "sparse yank index"),
    ("crates-yank-vs-crates-io-trustpub-opensearch", "crates.io trustpub opensearch leftover", "sparse yank index"),
    ("crates-yank-vs-lib-rs-security", "lib.rs security leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-show-asm-loong64", "cargo-show-asm loong leftover", "sparse yank index"),
    ("crates-yank-vs-docsrs-rustdoc-json-fuzz", "docs.rs rustdoc fuzz leftover", "sparse yank index"),
]

BREW = [
    ("homebrew-bottle-rebuild-vs-uses-from-macos-libffi", "uses_from_macos libffi leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-depends-on-macos-el-capitan", "depends_on macos el_capitan leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-head-spec-oid", "head oid leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-patch-data-p8", "patch DATA p8 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-resource-stage-path", "resource stage leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-keg-only-because-shadowed-by-clt", "keg_only clt leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-disable-because-broken", "disable broken leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-deprecate-because-merged", "deprecate merged leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-service-keep-alive-immediate", "service immediate leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-std-stack-args", "std_stack leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-on-sierra-block", "on_sierra leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-depends-on-arch-mips64", "depends_on arch mips leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-tap-migrations-edn", "tap_migrations edn leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-fails-with-gcc-7", "fails_with gcc 7 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-cxxstdlib-check-vendor", "cxxstdlib vendor leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-post-install-codesign", "post_install codesign leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-caveats-csrutil", "caveats csrutil leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-depends-on-php", "depends_on php leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-option-with-lto", "option lto leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-needs-ssse3", "needs ssse3 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-on-linux-dragonfly", "on_linux dragonfly leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-version-scheme-eight", "version_scheme 8 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-revision-five", "revision 5 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-stable-url-git-lfs", "stable git-lfs leftover", "rebuilt bottle sha"),
]

NIX = [
    ("nix-fetchFromBitbucket-clone-vs-nar", "Bitbucket clone leftover", "NAR of Bitbucket archive"),
    ("nix-fetchzip-sha384-vs-nar", "fetchzip sha384 leftover", "NAR of zip"),
    ("nix-fetchTarball-sha384-vs-nar", "fetchTarball sha384 leftover", "NAR of tarball"),
    ("nix-fetchPypi-sha384-vs-nar", "fetchPypi sha384 leftover", "NAR of PyPI sdist"),
    ("nix-fetchCrate-sha384-vs-nar", "fetchCrate sha384 leftover", "NAR of crates.io crate"),
    ("nix-fetchFromGitiles-sha384-vs-nar", "Gitiles sha384 leftover", "NAR of Gitiles archive"),
    ("nix-fetchsvn-sha384-vs-nar", "svn sha384 leftover", "NAR of svn export"),
    ("nix-fetchhg-sha384-vs-nar", "hg sha384 leftover", "NAR of hg archive"),
    ("nix-fetchcvs-sha384-vs-nar", "CVS sha384 leftover", "NAR of CVS export"),
    ("nix-fetchFromAzureDevOps-sha384-vs-nar", "Azure sha384 leftover", "NAR of Azure archive"),
    ("nix-fetchgit-fetchGrafts-vs-nar", "fetchGrafts leftover", "NAR of checkout"),
    ("nix-fetchurl-sha384-vs-nar-url", "fetchurl sha384 leftover", "NAR of fetched url"),
    ("nix-fetchFromGitHub-sha384-vs-nar", "GitHub sha384 leftover", "NAR of archive"),
    ("nix-fetchgit-am-vs-nar", "am leftover", "NAR of fetchgit"),
    ("nix-fetchFromGitLab-sha384-vs-nar", "GitLab sha384 leftover", "NAR of https archive"),
    ("nix-fetchgit-reset-vs-nar", "reset leftover", "NAR of pinned fetchgit"),
    ("nix-fetchFromGitea-sha384-vs-nar", "Gitea sha384 leftover", "NAR of public Gitea archive"),
    ("nix-fetchurl-blake2-vs-nar-store", "fetchurl blake2 leftover", "NAR of fetchurl store path"),
    ("nix-fetchFromCgit-sha384-vs-nar", "cgit sha384 leftover", "NAR of cgit archive"),
    ("nix-fetchgit-stash-vs-nar", "stash leftover", "NAR of pinned fetchgit"),
    ("nix-fetchFromSourcehut-sha384-vs-nar", "Sourcehut sha384 leftover", "NAR of sourcehut archive"),
    ("nix-fetchzip-sha384-vs-nar-root", "fetchzip sha384 leftover", "NAR of zip"),
    ("nix-builtins-readFile-vs-nar", "builtins.readFile leftover", "NAR of readFile"),
    ("nix-fetchgit-fetchGrafts-true-vs-nar", "grafts leftover", "NAR of checkout"),
]

NUGET = [
    ("nuget-snupkg-embed-untracked-sources-fuzz", "EmbedUntrackedSources fuzz leftover", "untracked-fuzz"),
    ("nuget-snupkg-sourcelink-azure-repos-cloud-vs-onprem", "Azure Repos cloud leftover", "azdo-cop"),
    ("nuget-snupkg-deterministic-pathmap-dotnet", "dotnet PathMap leftover", "pathmap-dn"),
    ("nuget-snupkg-debug-type-full-vs-pdbonly", "DebugType full leftover", "full-pdbonly"),
    ("nuget-snupkg-include-symbols-snupkg-true-no-txt", "IncludeSymbols no txt leftover", "sym-notxt"),
    ("nuget-snupkg-sourcelink-bitbucket-cloud-vs-server-dc", "Bitbucket cloud leftover", "bb-cldc"),
    ("nuget-snupkg-continuous-integration-build-true-azdo", "CI azdo leftover", "ciazdo"),
    ("nuget-snupkg-embed-all-sources-true-with-pdb", "EmbedAllSources with pdb leftover", "embed-tpdb"),
    ("nuget-snupkg-publish-gitlab-nuget-v8", "GitLab nuget v8 leftover", "gl-n8"),
    ("nuget-snupkg-pdb-checksum-algorithm-murmur", "PDB checksum murmur leftover", "pdb-mur"),
    ("nuget-snupkg-sourcelink-gitea-jenkins-vs-github", "Gitea jenkins leftover", "gitea-jk"),
    ("nuget-snupkg-embedded-files-filter-prefix", "embedded files prefix leftover", "embed-pre"),
    ("nuget-snupkg-source-root-unc-dfs", "UNC dfs leftover", "uncd-root"),
    ("nuget-snupkg-symbolpackageformat-none-vs-snupkg-only", "none vs snupkg leftover", "fmt-nso"),
    ("nuget-snupkg-repository-commit-vs-type", "RepositoryCommit leftover", "repo-ct"),
    ("nuget-snupkg-sourcelink-codeberg-jenkins-vs-github", "Codeberg jenkins leftover", "cb-jk"),
    ("nuget-snupkg-publish-github-packages-nuget-v9", "GPR nuget v9 leftover", "gpr-n9"),
    ("nuget-snupkg-portable-pdb-guid-cafebabe", "portable PDB cafebabe leftover", "pdb-cb"),
    ("nuget-snupkg-sourcelink-sourcehut-todo-vs-github", "sourcehut todo leftover", "srht-todo"),
    ("nuget-snupkg-source-link-mapped-path-unc-dfs", "UNC dfs mapped leftover", "uncd-map"),
    ("nuget-snupkg-publish-myget-v8-vs-nuget-org", "MyGet v8 leftover", "myget-v8"),
    ("nuget-snupkg-debug-type-embedded-vs-full-src", "DebugType embedded leftover", "emb-fulls"),
    ("nuget-snupkg-include-source-revision-false-release", "IncludeSourceRevision release leftover", "src-frel"),
    ("nuget-snupkg-sourcelink-forgejo-jenkins-vs-github", "Forgejo jenkins leftover", "fj-jk"),
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
"""Unique mill: package-release-factory attestation wave-17 (r1412+).

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

CATALOG_FIRST = 1412
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
        raise SystemExit("dup slug or plant in attest wave17 catalog")
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
    out = HERE / "pkg-mill-attest-wave17.py"
    out.write_text(body)
    print(f"wrote {out} pairs={N*4} minerals_used_estimate={N*8} minerals_avail={len(MINERALS)}")


if __name__ == "__main__":
    main()
