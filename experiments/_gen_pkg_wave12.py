#!/usr/bin/env python3
"""Generate experiments/pkg-mill-attest-wave12.py from a unique plant catalog."""
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
    ("cosign-verify-oci-referrer-layer-digest-vs-type", "referrer layer leftover", "OCI referrer type"),
    ("cosign-sign-bundle-v01-legacy-vs-dsse", "bundle v0.1 leftover", "DSSE bundle"),
    ("cosign-fulcio-travis-oidc-vs-github", "Travis OIDC leftover", "GitHub Fulcio issuer"),
    ("cosign-rekor-entry-kind-dsse-vs-hashedrekord", "DSSE Rekor leftover", "hashedrekord kind"),
    ("cosign-verify-tsa-root-untrusted", "untrusted TSA root leftover", "trusted TSA root"),
    ("cosign-policy-identity-attempt-vs-path", "attempt leftover", "workflow path identity"),
    ("cosign-sign-kms-vault-transit-key-mismatch", "Vault transit leftover", "matching Vault key"),
    ("cosign-verify-identity-workflow-run-vs-tag", "workflow_run leftover", "tag identity"),
    ("cosign-attach-predicate-csaf-vs-slsa", "CSAF leftover", "SLSA predicate"),
    ("cosign-copy-signature-digest-mismatch", "sig digest leftover", "matching digest"),
    ("cosign-verify-tuf-targets-expired", "expired TUF targets leftover", "refreshed TUF targets"),
    ("cosign-sign-recursive-attestation-partial", "partial attestation leftover", "full index attestation"),
    ("cosign-policy-ctlog-shard-id-stale", "stale CT shard leftover", "current CT shard"),
    ("cosign-fulcio-uri-san-repo-private", "private repo SAN leftover", "public repo SAN"),
    ("cosign-verify-bundle-hash-algo-sha384-vs-sha256", "sha384 leftover", "sha256 payload algo"),
    ("cosign-sign-sk-piv-slot-9e-vs-9a", "PIV slot 9e leftover", "PIV slot 9a"),
    ("cosign-oidc-issuer-codefresh-vs-github", "Codefresh leftover", "GitHub Actions OIDC"),
    ("cosign-verify-cert-notbefore-leeway", "notBefore leeway leftover", "NTP-aligned notBefore"),
    ("cosign-policy-builder-id-path-mismatch", "builder path leftover", "exact builder id"),
    ("cosign-sign-payload-intoto-spdx-xml", "in-toto SPDX-XML leftover", "in-toto SLSA payload"),
    ("cosign-rekor-inclusion-proof-tree-id", "tree id leftover", "signed tree id"),
    ("cosign-verify-oci-index-arch-filter", "arch filter leftover", "full OCI index"),
    ("cosign-sign-annotation-predicate-type-uri", "predicate type leftover", "matching predicate type"),
    ("cosign-policy-max-cert-lifetime-days", "max cert lifetime leftover", "policy lifetime"),
]

NPM = [
    ("npm-provenance-bundleDependencies-nohoist", "nohoist leftover", "nohoist-lock"),
    ("npm-trusted-publisher-workflow-filename-ship-yml", "workflow ship.yml leftover", "ship-lock"),
    ("npm-oidc-audience-registry-yarnpkg-com", "audience yarnpkg leftover", "yarn-aud"),
    ("npm-provenance-postinstall-mutates-pack", "postinstall leftover", "postin-lock"),
    ("npm-trusted-publisher-environment-manual-approval", "manual approval leftover", "manap-lock"),
    ("npm-oidc-subject-ref-workflow-run", "workflow_run leftover", "wrun-lock"),
    ("npm-provenance-optionalDependencies-libc-gnu", "gnu libc leftover", "gnu-lock"),
    ("npm-publish-from-lxc-runner-no-oidc", "lxc runner without OIDC leftover", "lxc-lock"),
    ("npm-trusted-publisher-cid-token-still-latest", "cid token leftover", "cid-lock"),
    ("npm-provenance-private-workspace-include", "workspace include leftover", "winc-lock"),
    ("npm-oidc-permissions-id-token-write-packages", "packages write leftover", "pkgw-lock"),
    ("npm-provenance-files-field-includes-test", "files includes test leftover", "testf-lock"),
    ("npm-trusted-publisher-org-2fa-webauthn", "org webauthn leftover", "webauth-lock"),
    ("npm-oidc-job-container-user-root", "container root leftover", "croot-lock"),
    ("npm-provenance-lockfileVersion-3-vs-2", "lockfileVersion 3 leftover", "lf32-lock"),
    ("npm-publish-access-restricted-scoped-attest", "restricted scoped leftover", "rsc-lock"),
    ("npm-trusted-publisher-workflow-call-inputs-none", "workflow_call inputs none leftover", "wcin-lock"),
    ("npm-oidc-issuer-drone-vs-github", "Drone issuer leftover", "drone-lock"),
    ("npm-provenance-bin-field-string-subject", "bin string leftover", "bins-lock"),
    ("npm-trusted-publisher-environment-wait-timer-5", "wait_timer 5 leftover", "wt5-lock"),
    ("npm-oidc-audience-npmjs-com", "audience npmjs.com leftover", "ncom-lock"),
    ("npm-provenance-os-cpu-optional-win32-arm64", "win32-arm64 leftover", "warm-lock"),
    ("npm-publish-provenance-true-then-file", "true then file leftover", "ttf-lock"),
    ("npm-trusted-publisher-nektos-act-no-oidc", "nektos act leftover", "nektos-lock"),
]

PYPI = [
    ("pypi-trusted-publisher-workflow-path-custom-dir", "custom workflow dir leftover", "release.yml path"),
    ("pypi-oidc-issuer-gitlab-ci-vs-github", "GitLab CI leftover", "GitHub OIDC issuer"),
    ("pypi-attestation-wheel-abi3-missing-sdist", "abi3 wheel leftover", "sdist+wheel pair"),
    ("pypi-twine-attestations-yaml-not-dsse", "YAML attestation leftover", "DSSE envelope"),
    ("pypi-trusted-publisher-environment-name-stage-typo", "environment stage leftover", "environment production"),
    ("pypi-oidc-job-container-id-token-write", "container id-token write leftover", "runner id-token"),
    ("pypi-hatch-index-nexus-url-leftover", "hatch nexus leftover", "prod PyPI index"),
    ("pypi-uv-publish-trusted-publishing-skip-check", "uv skip-check leftover", "uv trusted publishing"),
    ("pypi-poetry-keyring-disabled-leftover", "poetry keyring disabled leftover", "OIDC trusted publisher"),
    ("pypi-oidc-subject-workflow-ref-heads-prod", "workflow ref heads/prod leftover", "exact tag ref"),
    ("pypi-attestation-pep740-signature-missing", "PEP 740 signature leftover", "pep740 signature"),
    ("pypi-trusted-publisher-project-name-mixed-case", "mixed-case project leftover", "normalized PyPI name"),
    ("pypi-oidc-issuer-github-enterprise-vs-dotcom", "GHE leftover", "GitHub OIDC issuer"),
    ("pypi-twine-config-file-toml-leftover", "twine toml leftover", "OIDC trusted publishing"),
    ("pypi-trusted-publisher-workflow-call-ref-v1", "workflow_call v1 leftover", "sha-pinned reusable workflow"),
    ("pypi-oidc-job-services-memcached-sidecar", "memcached sidecar leftover", "bare runner OIDC"),
    ("pypi-attestation-wheel-manylinux2014-vs-2-28", "manylinux2014 leftover", "manylinux_2_28 attestation"),
    ("pypi-hatch-index-token-file-vs-oidc", "hatch token file leftover", "hatch trusted publishing"),
    ("pypi-uv-publish-check-url-nexus-legacy", "uv nexus leftover", "uv check-url pypi.org"),
    ("pypi-poetry-pypi-token-env-vs-oidc", "poetry token env leftover", "poetry OIDC"),
    ("pypi-trusted-publisher-environment-required-reviewers-2", "two reviewers leftover", "immediate environment"),
    ("pypi-oidc-issuer-buddy-vs-github", "Buddy leftover", "GitHub OIDC issuer"),
    ("pypi-attestation-attestations-dir-msgpack-pair", "msgpack leftover", "wheel+sdist attestations"),
    ("pypi-twine-skip-existing-non-interactive", "skip-existing leftover", "twine attestations required"),
]

MAVEN = [
    ("maven-gpg-sign-module-only-missing-parent", "module-only leftover", "mod-stg"),
    ("maven-central-portal-publishing-type-hybrid-hang", "hybrid hang leftover", "hyb-stg"),
    ("maven-gpg-keyring-agent-env-stale", "stale agent env leftover", "aenv-stg"),
    ("maven-gpg-passphrase-fd-xor-env", "passphrase fd leftover", "pfd-stg"),
    ("maven-central-bundle-missing-parent-checksum", "parent checksum leftover", "par-stg"),
    ("maven-gpg-useagent-true-pinentry-qt", "pinentry qt leftover", "qt-stg"),
    ("maven-ossrh-staging-profile-id-archived", "archived profile leftover", "arch-stg"),
    ("maven-gpg-sign-asc-armor-comment-header", "armor comment leftover", "acom-stg"),
    ("maven-central-publisher-api-namespace-reserved", "reserved namespace leftover", "resn-stg"),
    ("maven-gpg-digest-whirlpool-vs-sha256-policy", "Whirlpool leftover", "whirl-stg"),
    ("maven-settings-gpg-executable-appimage-path", "appimage leftover", "appi-stg"),
    ("maven-gpg-skip-assembly-asc", "skip assembly leftover", "sasm-stg"),
    ("maven-gpg-sign-parent-only-missing-modules", "parent-only leftover", "ponly-stg"),
    ("maven-central-portal-deployment-status-queued", "queued leftover", "que-stg"),
    ("maven-gpg-homedir-xdg-vs-absolute", "xdg gnupg leftover", "xdg-stg"),
    ("maven-gpg-sign-plugin-skip-assembly", "skip assembly plugin leftover", "skap-stg"),
    ("maven-central-user-token-rotated-old", "rotated old token leftover", "rot-stg"),
    ("maven-gpg-signer-class-xmlsec-fips", "xmlsec FIPS leftover", "xfips-stg"),
    ("maven-settings-server-central-releases-id", "central releases leftover", "crel-stg"),
    ("maven-gpg-exclude-classifiers-assembly", "exclude assembly leftover", "exas-stg"),
    ("maven-central-bundle-missing-module-sha3", "module sha3 leftover", "s3-stg"),
    ("maven-gpg-sign-attached-assembly-missing", "attached assembly leftover", "aasm-stg"),
    ("maven-ossrh-s01-host-after-portal-alias", "s01 alias leftover", "alias-stg"),
    ("maven-gpg-passphrase-server-id-central-old", "old central passphrase leftover", "cold-stg"),
]

CRATES = [
    ("crates-yank-vs-cargo-outdated-depth", "cargo-outdated depth leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-deny-advisories-db", "cargo-deny advisories db leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-audit-yanked", "cargo-audit yanked leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-cyclonedx-v1-4", "cargo-cyclonedx v1.4 leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-modules-orphans-json", "cargo-modules orphans json leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-shear-unused-build", "cargo-shear unused-build leftover", "sparse yank index"),
    ("crates-yank-vs-crates-io-api-v2-keywords", "crates.io api v2 keywords leftover", "sparse yank index"),
    ("crates-yank-vs-lib-rs-search-page", "lib.rs search leftover", "sparse yank index"),
    ("crates-yank-vs-docsrs-source-git", "docs.rs source git leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-release-hook", "cargo-release hook leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-clone-index", "cargo-clone index leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-info-deps", "cargo info deps leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-tree-edges", "cargo-tree edges leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-minimal-versions-offline", "minimal-versions offline leftover", "sparse yank index"),
    ("crates-yank-vs-crates-io-api-v1-categories", "crates.io api v1 categories leftover", "sparse yank index"),
    ("crates-yank-vs-lib-rs-search-json", "lib.rs search json leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-public-api-diff-text", "cargo-public-api text leftover", "sparse yank index"),
    ("crates-yank-vs-rustdoc-scrape-examples-md", "rustdoc scrape md leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-dist-ci", "cargo-dist ci leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-semver-checks-baseline-pkg", "semver-checks pkg leftover", "sparse yank index"),
    ("crates-yank-vs-crates-io-trustpub-json", "crates.io trustpub json leftover", "sparse yank index"),
    ("crates-yank-vs-lib-rs-json-feed", "lib.rs json feed leftover", "sparse yank index"),
    ("crates-yank-vs-cargo-show-asm-intel-att", "cargo-show-asm mixed leftover", "sparse yank index"),
    ("crates-yank-vs-docsrs-rustdoc-json-beta", "docs.rs rustdoc beta leftover", "sparse yank index"),
]

BREW = [
    ("homebrew-bottle-rebuild-vs-uses-from-macos-expat", "uses_from_macos expat leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-depends-on-macos-big-sur", "depends_on macos big_sur leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-head-spec-tag", "head tag leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-patch-data-p3", "patch DATA p3 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-resource-patches", "resource patches leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-keg-only-because-shadowed-by-macos", "keg_only macos leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-disable-because-does-not-build", "disable does_not_build leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-deprecate-because-unsupported", "deprecate unsupported leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-service-keep-alive-crashed", "service crashed leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-std-cabal-v2-args", "std_cabal leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-on-ventura-block", "on_ventura leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-depends-on-arch-ppc", "depends_on arch ppc leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-tap-migrations-csv", "tap_migrations csv leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-fails-with-gcc-12", "fails_with gcc 12 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-cxxstdlib-check-libstdcxx", "cxxstdlib libstdcxx leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-post-install-mkdir", "post_install mkdir leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-caveats-sudo", "caveats sudo leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-depends-on-rust", "depends_on rust leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-option-with-default-names", "option default names leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-needs-avx", "needs avx leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-on-linux-glibc", "on_linux glibc leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-version-scheme-three", "version_scheme 3 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-revision-zero", "revision 0 leftover", "rebuilt bottle sha"),
    ("homebrew-bottle-rebuild-vs-stable-url-and-mirror", "stable url+mirror leftover", "rebuilt bottle sha"),
]

NIX = [
    ("nix-fetchFromBitbucket-owner-vs-nar", "Bitbucket owner leftover", "NAR of Bitbucket archive"),
    ("nix-fetchzip-hash-vs-nar", "fetchzip hash leftover", "NAR of zip"),
    ("nix-fetchTarball-url-name-vs-nar", "fetchTarball url leftover", "NAR of tarball"),
    ("nix-fetchPypi-hash-vs-nar-sdist-name", "fetchPypi hash leftover", "NAR of PyPI sdist"),
    ("nix-fetchCrate-hash-vs-nar", "fetchCrate hash leftover", "NAR of crates.io crate"),
    ("nix-fetchFromGitiles-sha-vs-nar", "Gitiles sha leftover", "NAR of Gitiles archive"),
    ("nix-fetchsvn-sha256-vs-nar", "svn sha leftover", "NAR of svn export"),
    ("nix-fetchhg-sha256-vs-nar", "hg sha leftover", "NAR of hg archive"),
    ("nix-fetchcvs-sha256-vs-nar", "CVS sha leftover", "NAR of CVS export"),
    ("nix-fetchFromAzureDevOps-project-sha-vs-nar", "Azure project leftover", "NAR of Azure archive"),
    ("nix-fetchgit-fetchWorktrees-false-vs-nar", "no-worktrees leftover", "NAR of checkout"),
    ("nix-fetchurl-recursive-vs-nar", "fetchurl recursive leftover", "NAR of fetched url"),
    ("nix-fetchFromGitHub-repo-vs-nar", "GitHub repo leftover", "NAR of archive"),
    ("nix-fetchgit-deepClone-false-vs-nar", "deepClone false leftover", "NAR of fetchgit"),
    ("nix-fetchFromGitLab-group-vs-nar", "GitLab group leftover", "NAR of https archive"),
    ("nix-fetchgit-branch-vs-nar", "branch leftover", "NAR of pinned fetchgit"),
    ("nix-fetchFromGitea-sha-vs-nar", "Gitea sha leftover", "NAR of public Gitea archive"),
    ("nix-fetchurl-hash-vs-nar-store", "fetchurl hash leftover", "NAR of fetchurl store path"),
    ("nix-fetchFromCgit-sha256-vs-nar", "cgit sha leftover", "NAR of cgit archive"),
    ("nix-fetchgit-tag-vs-nar", "tag leftover", "NAR of pinned fetchgit"),
    ("nix-fetchFromSourcehut-sha-vs-nar", "Sourcehut sha leftover", "NAR of sourcehut archive"),
    ("nix-fetchzip-postFetch-vs-nar", "fetchzip postFetch leftover", "NAR of zip"),
    ("nix-builtins-path-vs-nar", "builtins.path leftover", "NAR of path locked"),
    ("nix-fetchgit-fetchLFS-false-vs-nar", "no-LFS leftover", "NAR of checkout"),
]

NUGET = [
    ("nuget-snupkg-embed-untracked-sources-local", "EmbedUntrackedSources local leftover", "untracked-local"),
    ("nuget-snupkg-sourcelink-azure-repos-cloud-vs-github", "Azure Repos cloud leftover", "azdo-cld"),
    ("nuget-snupkg-deterministic-pathmap-relative", "relative PathMap leftover", "pathmap-rel"),
    ("nuget-snupkg-debug-type-portable-vs-full", "DebugType portable leftover", "port-full"),
    ("nuget-snupkg-include-symbols-snupkg-true-no-pdb", "IncludeSymbols no pdb leftover", "sym-nopdb"),
    ("nuget-snupkg-sourcelink-bitbucket-cloud-workspace", "Bitbucket workspace leftover", "bb-ws"),
    ("nuget-snupkg-continuous-integration-build-true-ci", "CI build true leftover", "citrue"),
    ("nuget-snupkg-embed-all-sources-false-with-link", "EmbedAllSources false leftover", "embed-falselink"),
    ("nuget-snupkg-publish-gitlab-nuget-v2", "GitLab nuget v2 leftover", "gl-n2"),
    ("nuget-snupkg-pdb-checksum-algorithm-sha3", "PDB checksum SHA3 leftover", "pdb-sha3"),
    ("nuget-snupkg-sourcelink-gitea-tea-vs-github", "Gitea tea leftover", "gitea-tea"),
    ("nuget-snupkg-embedded-files-filter-glob", "embedded files glob leftover", "embed-glob"),
    ("nuget-snupkg-source-root-long-path", "long SourceRoot leftover", "long-root"),
    ("nuget-snupkg-symbolpackageformat-none-vs-snupkg", "format none leftover", "fmt-none"),
    ("nuget-snupkg-repository-branch-vs-url", "RepositoryBranch leftover", "repo-br"),
    ("nuget-snupkg-sourcelink-codeberg-forgejo-vs-github", "Codeberg forge leftover", "cb-fj"),
    ("nuget-snupkg-publish-github-packages-nuget-v4", "GPR nuget v4 leftover", "gpr-n4"),
    ("nuget-snupkg-portable-pdb-guid-nil", "portable PDB nil leftover", "pdb-nil"),
    ("nuget-snupkg-sourcelink-sourcehut-git-pages", "sourcehut pages leftover", "srht-pg"),
    ("nuget-snupkg-source-link-mapped-path-long", "long mapped path leftover", "long-map"),
    ("nuget-snupkg-publish-myget-v2-vs-nuget-org", "MyGet v2 leftover", "myget-v2"),
    ("nuget-snupkg-debug-type-embedded-vs-full", "DebugType embedded leftover", "emb-full"),
    ("nuget-snupkg-include-source-revision-true-local", "IncludeSourceRevision local leftover", "src-local"),
    ("nuget-snupkg-sourcelink-forgejo-tea-vs-github", "Forgejo tea leftover", "fj-tea"),
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
"""Unique mill: package-release-factory attestation wave-12 (r932+).

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

CATALOG_FIRST = 932
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
        raise SystemExit("dup slug or plant in attest wave12 catalog")
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
    out = HERE / "pkg-mill-attest-wave12.py"
    out.write_text(body)
    print(f"wrote {out} pairs={N*4} minerals_used_estimate={N*8} minerals_avail={len(MINERALS)}")


if __name__ == "__main__":
    main()
