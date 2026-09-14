#!/usr/bin/env python3
"""Unique mill: package-release-factory attestation wave-7 (r444+).

BAN r247–r443 mill slugs including r379 nix-fetchipfs / nuget embedded-portable
and r442 cargo-sparse-etag-vs-git-index / cargo-publish-token-vs-trusted-publishing.
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

CATALOG_FIRST = 444
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
    "nix-fetchipfs-vs-nar-of-cid",
    "nuget-snupkg-snupkg-vs-embedded-portable-split",
    "cargo-sparse-etag-vs-git-index",
    "cargo-publish-token-vs-trusted-publishing",
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

    add(
        ok_cosign(
            slug="cosign-verify-platform-arm64-vs-amd64",
            plant="berthierite-oci", ver="1.4.1",
            kind="arm64 signature leftover vs amd64 image",
            leftover="arm64 cosign signature", intended="amd64 image signature",
            asset="dist/berthierite-arm64.sig",
            first="verify leftover arm64 signature against amd64 image",
            change="sign matching amd64 platform", term="success; arm64 sig leftover",
            err="Error: leftover arm64 signature; image is amd64",
            policy='{\n  "platform": "linux/amd64"\n}',
            sign="run: cosign sign --yes $IMAGE  # leftover arm64",
        ),
        fail_npm(
            slug="npm-provenance-lifecycle-prepare-mutates",
            plant="dickite-js", ver="2.1.0", nxt="2.1.1",
            kind="prepare leftover mutates pack vs provenance",
            leftover="prepare rewrite pack", consumer="prepare-lock",
            first="publish leftover prepare-mutated pack as provenance",
            change="2.1.1 drop prepare mutate then OIDC",
            term="fail: prepare-lock still 2.1.0",
            err="npm ERR! leftover prepare mutated pack; subjectDigest drift",
            wf="run: npm publish --provenance\n# leftover prepare mutates files",
        ),
    )
    add(
        ok_cosign(
            slug="cosign-fulcio-circleci-issuer-vs-github",
            plant="boulangerite-oci", ver="3.2.2",
            kind="CircleCI OIDC leftover vs GitHub Fulcio",
            leftover="CircleCI OIDC issuer", intended="GitHub Actions OIDC issuer",
            asset="dist/boulangerite-circleci.jwt",
            first="verify leftover CircleCI issuer against GitHub policy",
            change="sign keyless GitHub Fulcio", term="success; CircleCI issuer leftover",
            err="Error: leftover CircleCI issuer; Fulcio wants GitHub",
            policy='{\n  "oidcIssuer": "https://token.actions.githubusercontent.com"\n}',
            sign="run: cosign sign --yes $IMAGE  # leftover circleci",
        ),
        fail_npm(
            slug="npm-trusted-publisher-package-transferred",
            plant="digenite-js", ver="0.5.1", nxt="0.5.2",
            kind="trusted publisher leftover after package transfer",
            leftover="publisher old-owner", consumer="xfer-lock",
            first="publish leftover old-owner publisher onto transferred package",
            change="0.5.2 new-owner OIDC publisher",
            term="fail: xfer-lock still 0.5.1",
            err="npm ERR! leftover trusted publisher old-owner; package transferred",
            wf="run: npm publish --provenance\n# leftover publisher old-owner",
        ),
    )
    add(
        ok_cosign(
            slug="cosign-rekor-monolithic-vs-sharded-log",
            plant="breithauptite-oci", ver="4.0.3",
            kind="monolithic Rekor leftover vs sharded log",
            leftover="monolithic Rekor UUID", intended="sharded Rekor log",
            asset="dist/breithauptite-mono-uuid.txt",
            first="verify leftover monolithic UUID against sharded policy",
            change="sign into sharded Rekor", term="success; mono UUID leftover",
            err="Error: leftover monolithic Rekor UUID; policy is sharded",
            policy='{\n  "rekor": "sharded"\n}',
            sign="run: cosign sign --yes $IMAGE  # leftover mono rekor",
        ),
        fail_npm(
            slug="npm-oidc-audience-npmmirror-vs-github",
            plant="eucryptite-js", ver="8.8.0", nxt="8.8.1",
            kind="OIDC audience leftover npmmirror vs GitHub",
            leftover="audience registry.npmmirror.com", consumer="mirror-aud",
            first="exchange leftover npmmirror audience as GitHub OIDC",
            change="8.8.1 GitHub id-token audience",
            term="fail: mirror-aud still 8.8.0",
            err="npm ERR! leftover OIDC audience registry.npmmirror.com",
            wf="permissions:\n  id-token: write\n# leftover audience npmmirror",
        ),
    )
    add(
        ok_cosign(
            slug="cosign-oidc-redirect-localhost-vs-device",
            plant="cancrinite-oci", ver="0.9.4",
            kind="localhost OIDC redirect leftover vs device flow",
            leftover="OIDC redirect localhost", intended="device-code OIDC",
            asset="dist/cancrinite-localhost-oidc.txt",
            first="verify leftover localhost redirect as device flow",
            change="use device-code OIDC", term="success; localhost redirect leftover",
            err="Error: leftover localhost OIDC redirect; want device flow",
            policy='{\n  "oidc": "device"\n}',
            sign="run: cosign sign --oidc-issuer leftover --yes $IMAGE",
        ),
        fail_npm(
            slug="npm-provenance-overrides-field-subject",
            plant="ferrosilite-js", ver="1.6.6", nxt="1.6.7",
            kind="overrides field leftover vs packed subject",
            leftover="overrides leftover pin", consumer="ovr-lock",
            first="publish leftover overrides field as provenance subject",
            change="1.6.7 drop leftover overrides then OIDC",
            term="fail: ovr-lock still 1.6.6",
            err="npm ERR! leftover overrides field in subjectDigest",
            wf='run: npm publish --provenance\n# leftover "overrides": {"left":"1.0.0"}',
        ),
    )
    add(
        ok_cosign(
            slug="cosign-policy-identities-regexp-org",
            plant="carpholite-oci", ver="5.5.0",
            kind="identity regexp leftover vs exact org SAN",
            leftover="identity regexp leftover-.*", intended="exact org SAN",
            asset="policy/carpholite-regexp.yaml",
            first="admit leftover identity regexp as exact SAN",
            change="pin exact org SAN", term="success; regexp policy leftover",
            err="Error: leftover identity regexp; policy wants exact SAN",
            policy='{\n  "identity": "https://github.com/carpholite-designed/"\n}',
            sign="run: cosign sign --yes $IMAGE  # leftover regexp",
        ),
        fail_npm(
            slug="npm-trusted-publisher-environment-wait-timer",
            plant="geikielite-js", ver="3.0.2", nxt="3.0.3",
            kind="environment wait timer leftover vs immediate OIDC",
            leftover="environment wait_timer leftover", consumer="wait-lock",
            first="publish leftover wait_timer job as trusted publisher",
            change="3.0.3 immediate environment OIDC",
            term="fail: wait-lock still 3.0.2",
            err="npm ERR! leftover environment wait_timer; publisher is immediate",
            wf="environment:\n  name: release\n  wait_timer: 30\nrun: npm publish --provenance",
        ),
    )
    add(
        ok_cosign(
            slug="cosign-verify-blob-predicate-spdx-vs-cdx",
            plant="clintonite-oci", ver="2.2.8",
            kind="SPDX predicate leftover vs CycloneDX policy",
            leftover="SPDX blob predicate", intended="CycloneDX predicate",
            asset="dist/clintonite-spdx.json",
            first="verify leftover SPDX predicate as CycloneDX",
            change="attest CycloneDX predicate", term="success; SPDX leftover",
            err="Error: leftover SPDX predicate; policy wants CycloneDX",
            policy='{\n  "predicateType": "cyclonedx"\n}',
            sign="run: cosign attest --predicate leftover.spdx --yes $IMAGE",
        ),
        fail_npm(
            slug="npm-publish-from-gitlab-oidc-leftover",
            plant="glauconite-js", ver="7.4.0", nxt="7.4.1",
            kind="GitLab OIDC leftover vs npm GitHub publisher",
            leftover="GitLab OIDC id-token", consumer="gl-oidc-lock",
            first="publish leftover GitLab OIDC as npm trusted publisher",
            change="7.4.1 GitHub OIDC publisher",
            term="fail: gl-oidc-lock still 7.4.0",
            err="npm ERR! leftover GitLab OIDC; publisher is GitHub",
            wf="run: npm publish --provenance\n# leftover gitlab id-token",
        ),
    )
    add(
        ok_cosign(
            slug="cosign-fulcio-spiffe-id-vs-uri-san",
            plant="cookeite-oci", ver="6.1.1",
            kind="SPIFFE ID leftover vs URI SAN",
            leftover="SPIFFE ID leftover", intended="URI SAN identity",
            asset="dist/cookeite-spiffe.txt",
            first="verify leftover SPIFFE ID as URI SAN",
            change="require URI SAN", term="success; SPIFFE leftover",
            err="Error: leftover SPIFFE ID; policy wants URI SAN",
            policy='{\n  "identity": "uri-san"\n}',
            sign="run: cosign sign --yes $IMAGE  # leftover spiffe",
        ),
        fail_npm(
            slug="npm-oidc-permissions-id-token-none",
            plant="grunerite-js", ver="4.4.4", nxt="4.4.5",
            kind="id-token none leftover vs write",
            leftover="permissions id-token none", consumer="perm-none",
            first="publish leftover id-token:none job as provenance",
            change="4.4.5 id-token write OIDC",
            term="fail: perm-none still 4.4.4",
            err="npm ERR! leftover permissions id-token: none",
            wf="permissions:\n  id-token: none\nrun: npm publish --provenance",
        ),
    )
    add(
        ok_cosign(
            slug="cosign-rekor-integrated-time-skew",
            plant="corderoite-oci", ver="1.0.7",
            kind="integratedTime skew leftover vs policy window",
            leftover="integratedTime skew leftover", intended="policy time window",
            asset="dist/corderoite-itime.txt",
            first="verify leftover skewed integratedTime",
            change="require in-window integratedTime", term="success; skew leftover",
            err="Error: leftover integratedTime outside policy window",
            policy='{\n  "maxSkew": "2m"\n}',
            sign="run: cosign sign --yes $IMAGE  # leftover itime",
        ),
        fail_npm(
            slug="npm-provenance-engines-node-field",
            plant="hastingsite-js", ver="9.1.2", nxt="9.1.3",
            kind="engines.node leftover vs packed subject",
            leftover="engines.node leftover", consumer="engines-lock",
            first="publish leftover engines.node as provenance subject",
            change="9.1.3 align engines then OIDC",
            term="fail: engines-lock still 9.1.2",
            err="npm ERR! leftover engines.node in subjectDigest",
            wf='run: npm publish --provenance\n# leftover "engines": {"node":">=16"}',
        ),
    )
    add(
        ok_cosign(
            slug="cosign-bundle-v03-vs-legacy-sig-tag",
            plant="cornwallite-oci", ver="8.0.0",
            kind="legacy .sig tag leftover vs bundle v0.3",
            leftover="legacy .sig tag", intended="sigstore bundle v0.3",
            asset="dist/cornwallite.sig",
            first="verify leftover .sig tag as bundle v0.3",
            change="attach bundle v0.3 referrer", term="success; .sig tag leftover",
            err="Error: leftover legacy .sig tag; policy wants bundle v0.3",
            policy='{\n  "bundle": "0.3"\n}',
            sign="run: cosign sign --yes $IMAGE  # leftover .sig tag",
        ),
        fail_npm(
            slug="npm-trusted-publisher-workflow-publish-yaml",
            plant="kaersutite-js", ver="0.2.4", nxt="0.2.5",
            kind="publish.yaml leftover vs publish.yml publisher",
            leftover="workflow publish.yaml", consumer="yaml-lock",
            first="publish leftover publish.yaml as yml publisher",
            change="0.2.5 publish.yml OIDC",
            term="fail: yaml-lock still 0.2.4",
            err="npm ERR! leftover workflow publish.yaml; publisher is publish.yml",
            wf="# leftover .github/workflows/publish.yaml",
        ),
    )
    add(
        ok_cosign(
            slug="cosign-policy-ctlog-pubkey-pem",
            plant="cubanite-oci", ver="2.8.1",
            kind="CT log pubkey PEM leftover vs TUF CT",
            leftover="ctlog.pub PEM", intended="TUF CT log",
            asset="dist/cubanite-ctlog.pub",
            first="verify leftover ctlog.pub PEM against TUF CT",
            change="use TUF CT log", term="success; ctlog.pub leftover",
            err="Error: leftover ctlog.pub PEM; policy wants TUF CT",
            policy='{\n  "ctlog": "tuf"\n}',
            sign="run: cosign sign --yes $IMAGE  # leftover ctlog.pub",
        ),
        fail_npm(
            slug="npm-provenance-cpu-os-optional-pkg",
            plant="lamprophyllite-js", ver="5.5.5", nxt="5.5.6",
            kind="cpu/os optional leftover vs provenance subject",
            leftover="optional cpu/os leftover", consumer="cpuos-lock",
            first="publish leftover optional cpu/os as subject",
            change="5.5.6 drop leftover optional then OIDC",
            term="fail: cpuos-lock still 5.5.5",
            err="npm ERR! leftover optional cpu/os in subjectDigest",
            wf='run: npm publish --provenance\n# leftover "cpu":["x64"],"os":["linux"]',
        ),
    )
    add(
        ok_cosign(
            slug="cosign-sign-sk-piv-slot-vs-keyless",
            plant="cyanotrichite-oci", ver="3.3.7",
            kind="PIV slot leftover vs keyless Fulcio",
            leftover="cosign --sk PIV slot", intended="keyless Fulcio",
            asset="dist/cyanotrichite-piv.slot",
            first="verify leftover PIV slot signature as keyless",
            change="keyless Fulcio sign", term="success; PIV slot leftover",
            err="Error: leftover PIV slot signature; policy is keyless",
            policy='{\n  "keyless": true\n}',
            sign="run: cosign sign --sk --slot leftover --yes $IMAGE",
        ),
        fail_npm(
            slug="npm-provenance-dist-tag-beta-vs-latest",
            plant="lorenzenite-js", ver="6.0.1", nxt="6.0.2",
            kind="dist-tag beta leftover vs latest provenance",
            leftover="dist-tag beta", consumer="beta-lock",
            first="publish leftover beta tag as latest provenance",
            change="6.0.2 latest OIDC provenance",
            term="fail: beta-lock still 6.0.1",
            err="npm ERR! leftover dist-tag beta; publisher wants latest",
            wf="run: npm publish --tag beta --provenance",
        ),
    )
    add(
        ok_cosign(
            slug="cosign-verify-identity-workflow-sha-vs-ref",
            plant="cuprosklodowskite-oci", ver="7.7.2",
            kind="workflow SHA leftover vs tag ref identity",
            leftover="workflow SHA leftover", intended="tag ref identity",
            asset="dist/cuprosklodowskite-sha.txt",
            first="verify leftover workflow SHA as tag identity",
            change="require tag workflow ref", term="success; SHA leftover",
            err="Error: leftover workflow SHA; policy wants tag ref",
            policy='{\n  "identity": "refs/tags/v7.7.2"\n}',
            sign="run: cosign sign --yes $IMAGE  # leftover workflow sha",
        ),
        fail_npm(
            slug="npm-oidc-matrix-os-subject",
            plant="magnesiohornblende-js", ver="1.1.8", nxt="1.1.9",
            kind="matrix.os leftover vs single-OS provenance",
            leftover="matrix.os leftover", consumer="matrix-lock",
            first="publish leftover matrix OS as single-OS provenance",
            change="1.1.9 single ubuntu OIDC",
            term="fail: matrix-lock still 1.1.8",
            err="npm ERR! leftover matrix.os subjectDigest",
            wf="strategy:\n  matrix:\n    os: [ubuntu, leftover]\nrun: npm publish --provenance",
        ),
    )

    add(
        ok_pypi(
            slug="pypi-trusted-publisher-workflow-concurrency-cancel",
            plant="nordstrandite-py", ver="2.0.4",
            kind="concurrency cancel leftover vs publisher row",
            leftover="concurrency cancel-in-progress",
            intended="stable pypi.yml publisher",
            asset="docs/nordstrandite-conc-2.0.3.note",
            first="twine leftover after concurrency cancelled the OIDC job",
            change="register non-cancelling publisher workflow",
            term="success; concurrency note leftover",
            err="403 leftover concurrency cancel; OIDC job aborted",
            wf="concurrency:\n  cancel-in-progress: true",
            old="2.0.3",
        ),
        fail_maven(
            slug="maven-gpg-sign-sources-classifier-missing",
            plant="wagnerite-mvn", ver="1.4.0", nxt="1.4.1",
            kind="sources classifier leftover unsigned",
            leftover="sources.jar without .asc", staging="orgwagnerite-3",
            first="close leftover staging with unsigned sources",
            change="1.4.1 sign sources classifier; new staging",
            term="fail: BOM still orgwagnerite-3",
            err="close rejected: leftover sources classifier has no .asc",
            pom="<classifier>sources</classifier><!-- leftover unsigned -->",
        ),
    )
    add(
        ok_pypi(
            slug="pypi-oidc-issuer-forgejo-vs-github",
            plant="nosean-py", ver="0.8.8",
            kind="Forgejo OIDC leftover vs GitHub publisher",
            leftover="https://forgejo.example/_services/token",
            intended="https://token.actions.githubusercontent.com",
            asset="docs/nosean-forgejo-0.8.7.note",
            first="twine leftover Forgejo issuer so GitHub OIDC is unused",
            change="register GitHub issuer", term="success; Forgejo issuer leftover",
            err="403 leftover issuer forgejo.example; publisher is github.com",
            wf="run: twine upload dist/*\n# leftover forgejo oidc",
            old="0.8.7",
        ),
        fail_maven(
            slug="maven-central-portal-publishing-type-automatic-hang",
            plant="wollastonite-mvn", ver="5.0.1", nxt="5.0.2",
            kind="automatic publishing leftover hang vs user-managed",
            leftover="publishingType AUTOMATIC hang", staging="orgwollastonite-8",
            first="close leftover AUTOMATIC portal deploy that hung",
            change="5.0.2 user-managed; new staging",
            term="fail: BOM still orgwollastonite-8",
            err="close rejected: leftover AUTOMATIC publishing hung",
            pom="<publishingType>AUTOMATIC</publishingType>",
        ),
    )
    add(
        ok_pypi(
            slug="pypi-attestation-wheel-manylinux-vs-pure",
            plant="omphacite-py", ver="3.3.3",
            kind="manylinux wheel leftover vs purelib attestation",
            leftover="manylinux wheel subject", intended="purelib wheel attestation",
            asset="docs/omphacite-manylinux-3.3.2.note",
            first="twine leftover manylinux wheel as purelib attestation",
            change="attest matching purelib wheel",
            term="success; manylinux note leftover",
            err="400 leftover manylinux subject; publisher attests purelib",
            wf="run: pypi-attestations sign dist/*manylinux*.whl",
            old="3.3.2",
        ),
        fail_maven(
            slug="maven-gpg-keyring-gnupg-agent-socket-gone",
            plant="wurtzite-mvn", ver="2.2.0", nxt="2.2.1",
            kind="gpg-agent socket leftover gone vs batch",
            leftover="S.gpg-agent leftover gone", staging="orgwurtzite-5",
            first="close leftover staging using vanished agent socket",
            change="2.2.1 batch loopback; new staging",
            term="fail: BOM still orgwurtzite-5",
            err="close rejected: leftover S.gpg-agent socket gone",
            pom="<useAgent>true</useAgent><!-- leftover vanished socket -->",
        ),
    )
    add(
        ok_pypi(
            slug="pypi-twine-non-interactive-missing-oidc",
            plant="pargasite-py", ver="4.1.7",
            kind="twine --non-interactive leftover without OIDC",
            leftover="twine --non-interactive tokenless",
            intended="OIDC trusted publisher",
            asset="docs/pargasite-ni-4.1.6.note",
            first="twine leftover --non-interactive without OIDC token",
            change="enable OIDC then non-interactive",
            term="success; tokenless note leftover",
            err="403 leftover --non-interactive; no OIDC token",
            wf="run: twine upload --non-interactive dist/*",
            old="4.1.6",
        ),
        fail_maven(
            slug="maven-gpg-passphrase-maven-settings-server-xor",
            plant="zoisite-mvn", ver="0.6.6", nxt="0.6.7",
            kind="settings server passphrase leftover XOR env",
            leftover="settings server passphrase XOR", staging="orgzoisite-2",
            first="close leftover staging with XOR passphrase mismatch",
            change="0.6.7 single env passphrase; new staging",
            term="fail: BOM still orgzoisite-2",
            err="close rejected: leftover settings passphrase XOR env",
            pom="<serverId>gpg</serverId><!-- leftover xor env -->",
        ),
    )
    add(
        ok_pypi(
            slug="pypi-trusted-publisher-project-yanked-then-restore",
            plant="prehnite-py", ver="1.9.0",
            kind="yanked project leftover vs restored publisher",
            leftover="yanked project row", intended="restored trusted publisher",
            asset="docs/prehnite-yanked-1.8.9.note",
            first="twine leftover while project still marked yanked",
            change="restore project; OIDC publish",
            term="success; yanked-row note leftover",
            err="403 leftover yanked project; publisher not live",
            wf="run: twine upload dist/*\n# leftover yanked project",
            old="1.8.9",
        ),
        fail_maven(
            slug="maven-central-bundle-missing-module-checksum",
            plant="aegirine-mvn", ver="7.7.0", nxt="7.7.1",
            kind="module checksum leftover missing vs portal",
            leftover="module missing sha512", staging="orgaegirine-9",
            first="close leftover portal bundle without module sha512",
            change="7.7.1 emit module sha512; new staging",
            term="fail: BOM still orgaegirine-9",
            err="close rejected: leftover .module has no sha512",
            pom="<!-- leftover skip module checksum -->",
        ),
    )
    add(
        ok_pypi(
            slug="pypi-oidc-job-container-vs-runner",
            plant="riebeckite-py", ver="6.2.2",
            kind="job container leftover vs runner OIDC",
            leftover="job container leftover-image",
            intended="runner OIDC publisher",
            asset="docs/riebeckite-ctr-6.2.1.note",
            first="twine leftover container OIDC as runner publisher",
            change="register runner OIDC", term="success; container note leftover",
            err="403 leftover job container issuer; publisher is runner",
            wf="container: leftover-image\nrun: twine upload dist/*",
            old="6.2.1",
        ),
        fail_maven(
            slug="maven-gpg-useagent-true-no-daemon",
            plant="arfvedsonite-mvn", ver="3.3.1", nxt="3.3.2",
            kind="useAgent true leftover without daemon",
            leftover="useAgent true no daemon", staging="orgarfvedsonite-4",
            first="close leftover staging with useAgent and no daemon",
            change="3.3.2 start agent; new staging",
            term="fail: BOM still orgarfvedsonite-4",
            err="close rejected: leftover useAgent true; no daemon",
            pom="<useAgent>true</useAgent><!-- leftover no daemon -->",
        ),
    )
    add(
        ok_pypi(
            slug="pypi-hatch-publish-repo-url-testpypi",
            plant="thomsonite-py", ver="0.4.4",
            kind="hatch repo-url TestPyPI leftover vs prod",
            leftover="HATCH_INDEX_REPO testpypi",
            intended="hatch prod OIDC",
            asset="docs/thomsonite-test-0.4.3.note",
            first="hatch publish leftover TestPyPI repo-url",
            change="hatch prod trusted publishing",
            term="success; TestPyPI repo leftover",
            err="403 leftover HATCH_INDEX_REPO testpypi; project is prod",
            wf="run: hatch publish --repo https://test.pypi.org/legacy/",
            old="0.4.3",
        ),
        fail_maven(
            slug="maven-ossrh-staging-profile-retired",
            plant="astrophyllite-mvn", ver="8.1.1", nxt="8.1.2",
            kind="retired OSSRH profile leftover vs portal",
            leftover="retired OSSRH stagingProfileId", staging="orgastrophyllite-6",
            first="close leftover retired OSSRH profile",
            change="8.1.2 Central Portal; new staging",
            term="fail: BOM still orgastrophyllite-6",
            err="close rejected: leftover retired OSSRH stagingProfileId",
            pom="<stagingProfileId>RETIRED</stagingProfileId>",
        ),
    )
    add(
        ok_pypi(
            slug="pypi-attestation-attestations-dir-wheel-only",
            plant="titanite-py", ver="5.5.1",
            kind="attestations dir leftover wheel-only vs sdist required",
            leftover="attestations/ wheel only",
            intended="wheel + sdist PEP 740",
            asset="docs/titanite-wheel-only-5.5.0.note",
            first="twine leftover wheel-only attestations dir",
            change="attest wheel and sdist",
            term="success; wheel-only dir leftover",
            err="400 leftover wheel-only attestations; sdist required",
            wf="run: pypi-attestations sign dist/*.whl",
            old="5.5.0",
        ),
        fail_maven(
            slug="maven-gpg-sign-attached-armor-vs-binary",
            plant="babingtonite-mvn", ver="1.1.4", nxt="1.1.5",
            kind="attached armored leftover vs binary .asc",
            leftover="gpg --armor --sign attached", staging="orgbabingtonite-7",
            first="close leftover armored attached-sig staging",
            change="1.1.5 detached binary .asc; new staging",
            term="fail: BOM still orgbabingtonite-7",
            err="close rejected: leftover armored attached; want detached .asc",
            pom="<!-- leftover gpg --armor --sign -->",
        ),
    )
    add(
        ok_pypi(
            slug="pypi-trusted-publisher-workflow-call-sha-pin",
            plant="topaz-py", ver="2.7.7",
            kind="workflow_call SHA pin leftover vs ref publisher",
            leftover="workflow_call sha pin",
            intended="workflow ref publisher",
            asset="docs/topaz-sha-2.7.6.note",
            first="twine leftover SHA-pinned reusable call",
            change="register ref-based publisher",
            term="success; SHA-pin note leftover",
            err="403 leftover workflow_call SHA; publisher matches ref",
            wf="uses: org/pub.yml@deadbeef",
            old="2.7.6",
        ),
        fail_maven(
            slug="maven-central-publisher-api-namespace-pending",
            plant="barroisite-mvn", ver="4.4.0", nxt="4.4.1",
            kind="portal namespace leftover pending vs claimed",
            leftover="namespace pending leftover", staging="orgbarroisite-1",
            first="close leftover portal deploy under pending namespace",
            change="4.4.1 claimed namespace; new staging",
            term="fail: BOM still orgbarroisite-1",
            err="close rejected: leftover namespace pending",
            pom="<!-- leftover pending namespace -->",
        ),
    )
    add(
        ok_pypi(
            slug="pypi-uv-publish-check-url-leftover",
            plant="tremolite-py", ver="9.0.0",
            kind="uv --check-url leftover vs trusted publishing",
            leftover="UV_PUBLISH_CHECK_URL leftover",
            intended="uv trusted publishing",
            asset="docs/tremolite-checkurl-8.9.9.note",
            first="uv publish leftover --check-url so OIDC is unused",
            change="uv publish --trusted-publishing",
            term="success; check-url note leftover",
            err="403 leftover UV_PUBLISH_CHECK_URL; project requires OIDC",
            wf="run: uv publish --check-url https://pypi.org/simple/",
            old="8.9.9",
        ),
        fail_maven(
            slug="maven-gpg-digest-sha512-vs-sha256-policy",
            plant="beidellite-mvn", ver="6.6.1", nxt="6.6.2",
            kind="SHA512 leftover vs portal SHA256 policy",
            leftover="gpg digest SHA512 leftover", staging="orgbeidellite-8",
            first="close leftover SHA512-signed staging",
            change="6.6.2 SHA256 digest; new staging",
            term="fail: BOM still orgbeidellite-8",
            err="close rejected: leftover SHA512 digest; portal wants SHA256",
            pom="<digestName>SHA512</digestName>",
        ),
    )
    add(
        ok_pypi(
            slug="pypi-poetry-config-http-basic-pypi",
            plant="tridymite-py", ver="1.2.8",
            kind="poetry http-basic leftover vs OIDC",
            leftover="poetry http-basic pypi",
            intended="poetry OIDC trusted publisher",
            asset="docs/tridymite-httpbasic-1.2.7.note",
            first="poetry publish leftover http-basic so OIDC is unused",
            change="poetry publish OIDC trusted publisher",
            term="success; http-basic leftover",
            err="403 leftover poetry http-basic; project requires OIDC",
            wf="run: poetry config http-basic.pypi leftover leftover",
            old="1.2.7",
        ),
        fail_maven(
            slug="maven-settings-gpg-executable-snap-path",
            plant="bementite-mvn", ver="0.3.9", nxt="0.4.0",
            kind="snap gpg leftover vs /usr/bin/gpg",
            leftover="gpg.executable /snap/bin/gpg", staging="orgbementite-5",
            first="close leftover staging signed via snap gpg",
            change="0.4.0 /usr/bin/gpg; new staging",
            term="fail: BOM still orgbementite-5",
            err="close rejected: leftover snap gpg path missing",
            pom="<executable>/snap/bin/gpg</executable>",
        ),
    )
    add(
        ok_pypi(
            slug="pypi-oidc-subject-workflow-ref-merge-group",
            plant="vesuvianite-py", ver="3.8.1",
            kind="merge_group leftover vs release publisher",
            leftover="workflow_ref merge_group",
            intended="release workflow publisher",
            asset="docs/vesuvianite-mg-3.8.0.note",
            first="twine leftover merge_group ref as release publisher",
            change="register release event publisher",
            term="success; merge_group leftover",
            err="403 leftover workflow_ref merge_group; publisher is release",
            wf="on: merge_group\nrun: twine upload dist/*",
            old="3.8.0",
        ),
        fail_maven(
            slug="maven-gpg-skip-assembly-descriptor-asc",
            plant="benitoite-mvn", ver="2.8.8", nxt="2.8.9",
            kind="assembly descriptor leftover unsigned",
            leftover="skip assembly .asc", staging="orgbenitoite-3",
            first="close leftover staging with unsigned assembly",
            change="2.8.9 sign assembly; new staging",
            term="fail: BOM still orgbenitoite-3",
            err="close rejected: leftover assembly descriptor has no .asc",
            pom="<descriptor>assembly.xml</descriptor><!-- leftover skip -->",
        ),
    )

    add(
        ok_crates(
            slug="crates-yank-vs-cargo-hack-feature-powerset",
            plant="berthierine-crate", ver="1.1.1", yanked="1.1.0",
            kind="cargo-hack powerset leftover after yank",
            leftover="cargo-hack powerset 1.1.0", intended="sparse yanked 1.1.0",
            asset="docs/hack-1.1.0.txt",
            first="unyank so cargo-hack powerset stays",
            change="1.1.1; leave hack report",
            term="success; cargo-hack 1.1.0 leftover",
            err="error: refuse unyank\ncargo-hack leftover still 1.1.0",
            pointer="docs/hack-1.1.0.txt",
        ),
        fail_brew(
            slug="homebrew-bottle-rebuild-vs-conflicts-with",
            plant="tengerite-brew", ver="0.3.3",
            kind="conflicts_with leftover vs rebuilt bottle",
            leftover="conflicts_with leftover", intended="rebuilt bottle sha",
            consumer="conflicts",
            first="keep leftover conflicts_with after rebuild",
            change="clear conflicts; handoff conflicts",
            term="fail: conflicts still leftover",
            err="* leftover conflicts_with ≠ rebuilt bottle",
            formula='conflicts_with "leftover"\nbottle do\n  sha256 cellar: :any, sonoma: "BOTTLESHA"\nend',
        ),
    )
    add(
        ok_crates(
            slug="crates-yank-vs-cargo-nextest-archive",
            plant="boehmite-crate", ver="2.4.0", yanked="2.3.9",
            kind="cargo-nextest archive leftover after yank",
            leftover="nextest archive 2.3.9", intended="sparse yanked 2.3.9",
            asset="docs/nextest-2.3.9.tar.zst",
            first="unyank so nextest archive stays",
            change="2.4.0; leave nextest archive",
            term="success; nextest 2.3.9 leftover",
            err="error: refuse unyank\nnextest leftover still 2.3.9",
            pointer="docs/nextest-2.3.9.tar.zst",
        ),
        fail_brew(
            slug="homebrew-bottle-rebuild-vs-deprecate-date",
            plant="thenardite-brew", ver="1.8.0",
            kind="deprecate! date leftover vs rebuilt bottle",
            leftover="deprecate! date leftover", intended="rebuilt enabled bottle",
            consumer="deprecate-date",
            first="keep leftover deprecate! date after rebuild",
            change="clear deprecate; handoff deprecate-date",
            term="fail: deprecate-date still leftover",
            err="* leftover deprecate! date ≠ rebuilt bottle",
            formula='deprecate! date: "2025-01-01", because: :leftover\nbottle do\n  sha256 cellar: :any, sonoma: "BOTTLESHA"\nend',
        ),
    )
    add(
        ok_crates(
            slug="crates-yank-vs-cargo-llvm-cov-profdata",
            plant="chamosite-crate", ver="0.7.7", yanked="0.7.6",
            kind="cargo-llvm-cov profdata leftover after yank",
            leftover="llvm-cov profdata 0.7.6", intended="sparse yanked 0.7.6",
            asset="docs/cov-0.7.6.profdata",
            first="unyank so llvm-cov profdata stays",
            change="0.7.7; leave profdata",
            term="success; llvm-cov 0.7.6 leftover",
            err="error: refuse unyank\nllvm-cov leftover still 0.7.6",
            pointer="docs/cov-0.7.6.profdata",
        ),
        fail_brew(
            slug="homebrew-bottle-rebuild-vs-test-do-block",
            plant="tilleyite-brew", ver="4.2.2",
            kind="test do leftover vs rebuilt bottle",
            leftover="test do leftover sha", intended="rebuilt bottle sha",
            consumer="test-do",
            first="treat leftover test do sha as bottle sha",
            change="write bottle sha; handoff test-do",
            term="fail: test-do still leftover",
            err="* leftover test do sha ≠ rebuilt bottle",
            formula='test do\n  system "#{bin}/leftover"\nend\nbottle do\n  sha256 cellar: :any, sonoma: "BOTTLESHA"\nend',
        ),
    )
    add(
        ok_crates(
            slug="crates-yank-vs-cargo-tarpaulin-cache",
            plant="clinochlore-crate", ver="3.0.3", yanked="3.0.2",
            kind="cargo-tarpaulin cache leftover after yank",
            leftover="tarpaulin cache 3.0.2", intended="sparse yanked 3.0.2",
            asset="docs/tarp-3.0.2.note",
            first="unyank so tarpaulin cache stays",
            change="3.0.3; leave tarpaulin note",
            term="success; tarpaulin 3.0.2 leftover",
            err="error: refuse unyank\ntarpaulin leftover still 3.0.2",
            pointer="docs/tarp-3.0.2.note",
        ),
        fail_brew(
            slug="homebrew-bottle-rebuild-vs-link-overwrite",
            plant="tobermorite-brew", ver="2.2.5",
            kind="link_overwrite leftover vs rebuilt bottle",
            leftover="link_overwrite leftover", intended="rebuilt bottle sha",
            consumer="link-ow",
            first="keep leftover link_overwrite after rebuild",
            change="clear overwrite; handoff link-ow",
            term="fail: link-ow still leftover",
            err="* leftover link_overwrite ≠ rebuilt bottle",
            formula='link_overwrite "bin/leftover"\nbottle do\n  sha256 cellar: :any, sonoma: "BOTTLESHA"\nend',
        ),
    )
    add(
        ok_crates(
            slug="crates-yank-vs-crates-io-owners-index",
            plant="cronstedtite-crate", ver="5.1.0", yanked="5.0.9",
            kind="crates.io owners leftover after yank",
            leftover="owners index 5.0.9", intended="sparse yanked 5.0.9",
            asset="docs/owners-5.0.9.json",
            first="unyank so owners index stays",
            change="5.1.0; leave owners JSON",
            term="success; owners 5.0.9 leftover",
            err="error: refuse unyank\nowners index leftover still 5.0.9",
            pointer="docs/owners-5.0.9.json",
        ),
        fail_brew(
            slug="homebrew-bottle-rebuild-vs-keg-link-completion",
            plant="troilite-brew", ver="0.9.9",
            kind="keg completions leftover vs rebuilt bottle",
            leftover="keg completions leftover", intended="rebuilt bottle sha",
            consumer="keg-comp",
            first="keep leftover keg completions after rebuild",
            change="rebuild completions; handoff keg-comp",
            term="fail: keg-comp still leftover",
            err="* leftover keg completions ≠ rebuilt bottle",
            formula='# leftover bash completion\nbottle do\n  sha256 cellar: :any, sonoma: "BOTTLESHA"\nend',
        ),
    )
    add(
        ok_crates(
            slug="crates-yank-vs-lib-rs-similar-crates",
            plant="daphnite-crate", ver="0.2.2", yanked="0.2.1",
            kind="lib.rs similar leftover after yank",
            leftover="lib.rs similar 0.2.1", intended="sparse yanked 0.2.1",
            asset="docs/librs-sim-0.2.1.html",
            first="unyank so lib.rs similar stays",
            change="0.2.2; leave similar HTML",
            term="success; lib.rs similar 0.2.1 leftover",
            err="error: refuse unyank\nlib.rs similar leftover still 0.2.1",
            pointer="docs/librs-sim-0.2.1.html",
        ),
        fail_brew(
            slug="homebrew-bottle-rebuild-vs-option-universal",
            plant="tschermakite-brew", ver="6.0.0",
            kind="option --universal leftover vs rebuilt bottle",
            leftover="option universal leftover", intended="thin bottle sha",
            consumer="universal",
            first="pour leftover universal option as thin bottle",
            change="ship thin sha; handoff universal",
            term="fail: universal still leftover",
            err="* leftover option --universal ≠ thin bottle",
            formula='option "universal"\nbottle do\n  sha256 cellar: :any, sonoma: "BOTTLESHA"\nend',
        ),
    )
    add(
        ok_crates(
            slug="crates-yank-vs-cargo-show-asm-cache",
            plant="ferroceladonite-crate", ver="4.4.1", yanked="4.4.0",
            kind="cargo-show-asm leftover after yank",
            leftover="show-asm cache 4.4.0", intended="sparse yanked 4.4.0",
            asset="docs/asm-4.4.0.s",
            first="unyank so show-asm cache stays",
            change="4.4.1; leave asm listing",
            term="success; show-asm 4.4.0 leftover",
            err="error: refuse unyank\nshow-asm leftover still 4.4.0",
            pointer="docs/asm-4.4.0.s",
        ),
        fail_brew(
            slug="homebrew-bottle-rebuild-vs-env-std-go",
            plant="tveitite-brew", ver="3.3.3",
            kind="std_go_args leftover vs rebuilt bottle",
            leftover="std_go_args leftover", intended="rebuilt bottle sha",
            consumer="std-go",
            first="keep leftover std_go_args after rebuild",
            change="rebuild go args; handoff std-go",
            term="fail: std-go still leftover",
            err="* leftover std_go_args ≠ rebuilt bottle",
            formula='system "go", "build", *std_go_args\nbottle do\n  sha256 cellar: :any, sonoma: "BOTTLESHA"\nend',
        ),
    )
    add(
        ok_crates(
            slug="crates-yank-vs-cargo-expand-macros",
            plant="greenalite-crate", ver="8.8.0", yanked="8.7.9",
            kind="cargo-expand leftover after yank",
            leftover="expand macros 8.7.9", intended="sparse yanked 8.7.9",
            asset="docs/expand-8.7.9.rs",
            first="unyank so cargo-expand stays",
            change="8.8.0; leave expand rs",
            term="success; expand 8.7.9 leftover",
            err="error: refuse unyank\ncargo-expand leftover still 8.7.9",
            pointer="docs/expand-8.7.9.rs",
        ),
        fail_brew(
            slug="homebrew-bottle-rebuild-vs-resource-mirror",
            plant="tyrolite-brew", ver="1.0.5",
            kind="resource mirror leftover vs bottle sha",
            leftover="resource mirror leftover", intended="bottle rebuild sha",
            consumer="res-mirror",
            first="treat leftover resource mirror as bottle sha",
            change="write bottle sha; handoff res-mirror",
            term="fail: res-mirror still leftover",
            err="* leftover resource mirror ≠ bottle rebuild",
            formula='resource "src" do\n  url "https://mirror.leftover/src"\nend\nbottle do\n  sha256 cellar: :any, sonoma: "BOTTLESHA"\nend',
        ),
    )
    add(
        ok_crates(
            slug="crates-yank-vs-crates-io-keywords-page",
            plant="minnesotaite-crate", ver="2.2.2", yanked="2.2.1",
            kind="crates.io keywords leftover after yank",
            leftover="keywords page 2.2.1", intended="sparse yanked 2.2.1",
            asset="docs/kw-2.2.1.html",
            first="unyank so keywords page stays",
            change="2.2.2; leave keywords HTML",
            term="success; keywords 2.2.1 leftover",
            err="error: refuse unyank\nkeywords leftover still 2.2.1",
            pointer="docs/kw-2.2.1.html",
        ),
        fail_brew(
            slug="homebrew-bottle-rebuild-vs-inreplace-prefix",
            plant="witherite-brew", ver="5.5.5",
            kind="inreplace prefix leftover vs rebuilt bottle",
            leftover="inreplace prefix leftover", intended="rebuilt bottle sha",
            consumer="inreplace",
            first="keep leftover inreplace prefix after rebuild",
            change="rebuild prefix; handoff inreplace",
            term="fail: inreplace still leftover",
            err="* leftover inreplace prefix ≠ rebuilt bottle",
            formula='inreplace "Makefile", "/leftover", prefix\nbottle do\n  sha256 cellar: :any, sonoma: "BOTTLESHA"\nend',
        ),
    )
    add(
        ok_crates(
            slug="crates-yank-vs-cargo-udeps-report",
            plant="nepouite-crate", ver="0.6.0", yanked="0.5.9",
            kind="cargo-udeps leftover after yank",
            leftover="udeps report 0.5.9", intended="sparse yanked 0.5.9",
            asset="docs/udeps-0.5.9.txt",
            first="unyank so udeps report stays",
            change="0.6.0; leave udeps report",
            term="success; udeps 0.5.9 leftover",
            err="error: refuse unyank\nudeps leftover still 0.5.9",
            pointer="docs/udeps-0.5.9.txt",
        ),
        fail_brew(
            slug="homebrew-bottle-rebuild-vs-caveats-path",
            plant="zinkenite-brew", ver="2.1.1",
            kind="caveats path leftover vs rebuilt bottle",
            leftover="caveats path leftover", intended="rebuilt bottle sha",
            consumer="caveats",
            first="keep leftover caveats path after rebuild",
            change="rewrite caveats; handoff caveats",
            term="fail: caveats still leftover",
            err="* leftover caveats path ≠ rebuilt bottle",
            formula='def caveats; "leftover path"; end\nbottle do\n  sha256 cellar: :any, sonoma: "BOTTLESHA"\nend',
        ),
    )
    add(
        ok_crates(
            slug="crates-yank-vs-renovate-cargo-datasource",
            plant="odinite-crate", ver="7.0.1", yanked="7.0.0",
            kind="Renovate cargo leftover after yank",
            leftover="Renovate cargo 7.0.0", intended="sparse yanked 7.0.0",
            asset="docs/renovate-7.0.0.json",
            first="unyank so Renovate cargo stays",
            change="7.0.1; leave Renovate JSON",
            term="success; Renovate 7.0.0 leftover",
            err="error: refuse unyank\nRenovate leftover still 7.0.0",
            pointer="docs/renovate-7.0.0.json",
        ),
        fail_brew(
            slug="homebrew-bottle-rebuild-vs-on-os-if-linux",
            plant="zippeite-brew", ver="0.4.8",
            kind="on_linux leftover vs macos bottle",
            leftover="on_linux leftover", intended="macos poured bottle",
            consumer="on-linux",
            first="pour leftover on_linux bottle on macOS",
            change="rebuild macos; handoff on-linux",
            term="fail: on-linux still leftover",
            err="* leftover on_linux ≠ macos pour",
            formula='on_linux do\n  depends_on "leftover"\nend\nbottle do\n  sha256 cellar: :any, sonoma: "BOTTLESHA"\nend',
        ),
    )
    add(
        ok_crates(
            slug="crates-yank-vs-cargo-msrv-verify-report",
            plant="sudoite-crate", ver="1.8.8", yanked="1.8.7",
            kind="cargo-msrv leftover after yank",
            leftover="msrv verify 1.8.7", intended="sparse yanked 1.8.7",
            asset="docs/msrv-1.8.7.txt",
            first="unyank so msrv report stays",
            change="1.8.8; leave msrv report",
            term="success; msrv 1.8.7 leftover",
            err="error: refuse unyank\nmsrv leftover still 1.8.7",
            pointer="docs/msrv-1.8.7.txt",
        ),
        fail_brew(
            slug="homebrew-bottle-rebuild-vs-depends-on-xcode",
            plant="zunyite-brew", ver="3.7.0",
            kind="depends_on :xcode leftover vs rebuilt bottle",
            leftover="depends_on xcode leftover", intended="rebuilt bottle sha",
            consumer="xcode-dep",
            first="keep leftover xcode dep after rebuild",
            change="clear xcode dep; handoff xcode-dep",
            term="fail: xcode-dep still leftover",
            err="* leftover depends_on :xcode ≠ rebuilt bottle",
            formula='depends_on xcode: :build\nbottle do\n  sha256 cellar: :any, sonoma: "BOTTLESHA"\nend',
        ),
    )

    add(
        ok_nix(
            slug="nix-fetchFromGitHub-forceFetchGit-vs-nar",
            plant="alunite-nix", ver="1.2.3",
            kind="forceFetchGit leftover vs NAR of archive",
            leftover="forceFetchGit hash", intended="NAR of GitHub archive",
            asset="notes/forcefetchgit.txt",
            first="keep leftover forceFetchGit hash",
            change="NAR of GitHub archive",
            term="success; forceFetchGit note leftover",
            err="hash mismatch leftover forceFetchGit vs archive NAR",
            flake='fetchFromGitHub { forceFetchGit = true; sha256 = "sha256-LEFTHASH="; }',
            fix='fetchFromGitHub { hash = "sha256-NARHASH="; }',
        ),
        fail_nuget(
            slug="nuget-snupkg-sourcelink-gitlab-selfhosted-vs-saas",
            plant="andersonite-nupkg", ver="2.2.0", nxt="2.2.1",
            kind="SourceLink GitLab self-hosted leftover vs saas",
            leftover="SourceLink GitLab self-hosted", consumer="gl-self",
            first="push leftover self-hosted SourceLink onto saas package",
            change="2.2.1 gitlab.com SourceLink pack once",
            term="fail: gl-self still 2.2.0",
            err="error: 400 leftover SourceLink self-hosted ≠ gitlab.com",
            props="<RepositoryUrl>https://gitlab.leftover.example/andersonite</RepositoryUrl>",
        ),
    )
    add(
        ok_nix(
            slug="nix-fetchurl-netrcFile-vs-nar",
            plant="antigorite-nix", ver="0.4.4",
            kind="fetchurl netrcFile leftover vs NAR of file",
            leftover="fetchurl netrcFile hash", intended="NAR of fetched file",
            asset="notes/netrc.txt",
            first="keep leftover netrcFile hash",
            change="NAR of fetched file",
            term="success; netrc note leftover",
            err="hash mismatch leftover netrcFile vs file NAR",
            flake='fetchurl { netrcFile = ./leftover; sha256 = "sha256-LEFTHASH="; }',
            fix='fetchurl { hash = "sha256-NARHASH="; }',
        ),
        fail_nuget(
            slug="nuget-snupkg-document-id-vs-module-version",
            plant="bayleyite-nupkg", ver="3.3.1", nxt="3.3.2",
            kind="document id leftover vs module version",
            leftover="PDB document id leftover", consumer="doc-id",
            first="rewrite leftover snupkg document id",
            change="3.3.2 matching document id pack once",
            term="fail: doc-id still 3.3.1",
            err="error: 400 leftover PDB document id ≠ module version",
            props="<!-- leftover document id vs MVID -->",
        ),
    )
    add(
        ok_nix(
            slug="nix-fetchgit-nativeBuildInputs-cacert-vs-nar",
            plant="bischofite-nix", ver="2.8.0",
            kind="fetchgit cacert leftover vs NAR of checkout",
            leftover="fetchgit cacert hash", intended="NAR of git checkout",
            asset="notes/cacert.txt",
            first="keep leftover cacert-pinned fetchgit hash",
            change="NAR of git checkout",
            term="success; cacert note leftover",
            err="hash mismatch leftover cacert fetchgit vs checkout NAR",
            flake='fetchgit { nativeBuildInputs = [ cacert ]; sha256 = "sha256-LEFTHASH="; }',
            fix='fetchgit { hash = "sha256-NARHASH="; }',
        ),
        fail_nuget(
            slug="nuget-snupkg-embed-interop-types-vs-pdb",
            plant="becquerelite-nupkg", ver="1.0.4", nxt="1.0.5",
            kind="EmbedInteropTypes leftover vs portable PDB",
            leftover="EmbedInteropTypes leftover", consumer="interop",
            first="push leftover interop embed as snupkg pair",
            change="1.0.5 portable PDB pack once",
            term="fail: interop still 1.0.4",
            err="error: 400 leftover EmbedInteropTypes cannot pair snupkg",
            props="<EmbedInteropTypes>true</EmbedInteropTypes>",
        ),
    )
    add(
        ok_nix(
            slug="nix-fetchFromRepoOrCz-vs-nar",
            plant="boracite-nix", ver="5.1.1",
            kind="fetchFromRepoOrCz leftover vs NAR of export",
            leftover="RepoOrCz file hash", intended="NAR of RepoOrCz export",
            asset="notes/reporcz.txt",
            first="keep leftover RepoOrCz file hash",
            change="NAR of RepoOrCz export",
            term="success; RepoOrCz note leftover",
            err="hash mismatch leftover RepoOrCz file vs export NAR",
            flake='fetchgit { url = "https://repo.or.cz/leftover"; sha256 = "sha256-LEFTHASH="; }',
            fix='fetchgit { hash = "sha256-NARHASH="; }',
        ),
        fail_nuget(
            slug="nuget-snupkg-public-signing-snk-vs-delay",
            plant="billietite-nupkg", ver="4.4.4", nxt="4.4.5",
            kind="public SNK leftover vs delay-signed nupkg",
            leftover="public SNK leftover", consumer="snk-gate",
            first="push leftover public SNK snupkg onto delay-signed nupkg",
            change="4.4.5 matching signing pack once",
            term="fail: snk-gate still 4.4.4",
            err="error: 400 leftover public SNK ≠ delay-signed nupkg",
            props="<SignAssembly>true</SignAssembly>\n<DelaySign>true</DelaySign>",
        ),
    )
    add(
        ok_nix(
            slug="nix-fetchs3-vs-nar",
            plant="epsomite-nix", ver="0.9.2",
            kind="fetchs3 leftover vs NAR of object",
            leftover="fetchs3 etag hash", intended="NAR of S3 object",
            asset="notes/fetchs3.txt",
            first="keep leftover S3 etag hash",
            change="NAR of S3 object",
            term="success; S3 note leftover",
            err="hash mismatch leftover S3 etag vs object NAR",
            flake='fetchs3 { sha256 = "sha256-LEFTHASH="; }',
            fix='fetchs3 { hash = "sha256-NARHASH="; }',
        ),
        fail_nuget(
            slug="nuget-snupkg-sourcelink-gerrit-vs-github",
            plant="boltwoodite-nupkg", ver="6.1.0", nxt="6.1.1",
            kind="SourceLink Gerrit leftover vs GitHub repo",
            leftover="SourceLink Gerrit URL", consumer="gerrit-debug",
            first="push leftover Gerrit SourceLink onto GitHub package",
            change="6.1.1 GitHub SourceLink pack once",
            term="fail: gerrit-debug still 6.1.0",
            err="error: 400 leftover SourceLink Gerrit ≠ nupkg GitHub",
            props="<RepositoryUrl>https://gerrit.example/boltwoodite</RepositoryUrl>",
        ),
    )
    add(
        ok_nix(
            slug="nix-fetchmtn-vs-nar",
            plant="hanksite-nix", ver="3.0.0",
            kind="fetchmtn leftover vs NAR of checkout",
            leftover="fetchmtn revision hash", intended="NAR of monotone checkout",
            asset="notes/fetchmtn.txt",
            first="keep leftover monotone revision hash",
            change="NAR of monotone checkout",
            term="success; mtn note leftover",
            err="hash mismatch leftover mtn revision vs checkout NAR",
            flake='fetchmtn { sha256 = "sha256-LEFTHASH="; }',
            fix='fetchmtn { hash = "sha256-NARHASH="; }',
        ),
        fail_nuget(
            slug="nuget-snupkg-deterministic-pathmap-alias",
            plant="curite-nupkg", ver="0.8.3", nxt="0.8.4",
            kind="PathMap alias leftover vs deterministic paths",
            leftover="PathMap alias leftover", consumer="pathmap-alias",
            first="rewrite leftover snupkg PathMap alias",
            change="0.8.4 deterministic PathMap pack once",
            term="fail: pathmap-alias still 0.8.3",
            err="error: 400 leftover PathMap alias ≠ nupkg",
            props="<PathMap>C:\\leftover=src</PathMap>",
        ),
    )
    add(
        ok_nix(
            slug="nix-fetchbazaar-vs-nar",
            plant="kainite-nix", ver="1.5.5",
            kind="fetchbzr leftover vs NAR of export",
            leftover="fetchbzr revno hash", intended="NAR of bzr export",
            asset="notes/fetchbzr.txt",
            first="keep leftover bzr revno hash",
            change="NAR of bzr export",
            term="success; bzr note leftover",
            err="hash mismatch leftover bzr revno vs export NAR",
            flake='fetchbzr { sha256 = "sha256-LEFTHASH="; }',
            fix='fetchbzr { hash = "sha256-NARHASH="; }',
        ),
        fail_nuget(
            slug="nuget-snupkg-compiler-generated-files-flag",
            plant="fourmarierite-nupkg", ver="7.2.2", nxt="7.2.3",
            kind="EmitCompilerGeneratedFiles leftover vs snupkg",
            leftover="compiler generated files leftover", consumer="cgen",
            first="push leftover compiler-generated files as snupkg",
            change="7.2.3 pack once without leftover generated files",
            term="fail: cgen still 7.2.2",
            err="error: 400 leftover EmitCompilerGeneratedFiles in snupkg",
            props="<EmitCompilerGeneratedFiles>true</EmitCompilerGeneratedFiles>",
        ),
    )
    add(
        ok_nix(
            slug="nix-fetchFromGitea-lfs-vs-nar",
            plant="polyhalite-nix", ver="2.2.6",
            kind="fetchFromGitea LFS leftover vs NAR of pointers",
            leftover="Gitea LFS pointer hash", intended="NAR of LFS objects",
            asset="notes/gitea-lfs.txt",
            first="keep leftover Gitea LFS pointer hash",
            change="NAR of LFS objects",
            term="success; Gitea LFS note leftover",
            err="hash mismatch leftover Gitea LFS pointers vs objects NAR",
            flake='fetchFromGitea { fetchLFS = true; sha256 = "sha256-LEFTHASH="; }',
            fix='fetchFromGitea { hash = "sha256-NARHASH="; }',
        ),
        fail_nuget(
            slug="nuget-snupkg-publish-github-packages-gpr-v2",
            plant="ianthinite-nupkg", ver="1.7.7", nxt="1.7.8",
            kind="GPR v2 leftover without symbols",
            leftover="GPR v2 no symbols", consumer="gpr-v2",
            first="push leftover snupkg to GPR v2 without symbols",
            change="1.7.8 nuget.org symbols pack once",
            term="fail: gpr-v2 still 1.7.7",
            err="error: 404 leftover GPR v2 has no symbols endpoint",
            props="<!-- leftover GPR v2 -->",
        ),
    )
    add(
        ok_nix(
            slug="nix-fetchgit-branch-symbolic-vs-nar",
            plant="schoenite-nix", ver="4.4.0",
            kind="fetchgit symbolic branch leftover vs NAR of commit",
            leftover="fetchgit branch leftover", intended="NAR of pinned commit",
            asset="notes/fetchgit-branch.txt",
            first="keep leftover symbolic branch hash",
            change="NAR of pinned commit",
            term="success; branch note leftover",
            err="hash mismatch leftover symbolic branch vs commit NAR",
            flake='fetchgit { branch = "leftover"; sha256 = "sha256-LEFTHASH="; }',
            fix='fetchgit { rev = "abc"; hash = "sha256-NARHASH="; }',
        ),
        fail_nuget(
            slug="nuget-snupkg-debug-type-pdbonly-vs-portable",
            plant="masuyite-nupkg", ver="8.0.1", nxt="8.0.2",
            kind="DebugType pdbonly leftover vs portable snupkg",
            leftover="DebugType pdbonly leftover", consumer="pdbonly",
            first="push leftover pdbonly as portable snupkg",
            change="8.0.2 portable DebugType pack once",
            term="fail: pdbonly still 8.0.1",
            err="error: 400 leftover DebugType pdbonly cannot pair snupkg",
            props="<DebugType>pdbonly</DebugType>",
        ),
    )
    add(
        ok_nix(
            slug="nix-fetchurl-recursiveHash-vs-nar",
            plant="tachyhydrite-nix", ver="0.1.9",
            kind="fetchurl recursiveHash leftover vs flat NAR",
            leftover="fetchurl recursiveHash leftover", intended="flat NAR of file",
            asset="notes/rechash.txt",
            first="keep leftover recursiveHash",
            change="flat NAR of file",
            term="success; recursiveHash note leftover",
            err="hash mismatch leftover recursiveHash vs flat NAR",
            flake='fetchurl { recursiveHash = true; sha256 = "sha256-LEFTHASH="; }',
            fix='fetchurl { hash = "sha256-NARHASH="; }',
        ),
        fail_nuget(
            slug="nuget-snupkg-source-link-url-rewrite-rules",
            plant="rutherfordine-nupkg", ver="2.9.0", nxt="2.9.1",
            kind="SourceLink URL rewrite leftover vs repo URL",
            leftover="SourceLink rewrite leftover", consumer="url-rw",
            first="push leftover rewritten SourceLink onto GitHub package",
            change="2.9.1 matching repo URL pack once",
            term="fail: url-rw still 2.9.0",
            err="error: 400 leftover SourceLink rewrite ≠ RepositoryUrl",
            props="<SourceLinkUrlRewrite>leftover</SourceLinkUrlRewrite>",
        ),
    )
    add(
        ok_nix(
            slug="nix-fetchdarcs-hashed-inventory-vs-nar",
            plant="trona-nix", ver="3.3.8",
            kind="fetchdarcs inventory leftover vs NAR of get",
            leftover="darcs hashed inventory", intended="NAR of darcs get",
            asset="notes/darcs-inv.txt",
            first="keep leftover darcs inventory hash",
            change="NAR of darcs get",
            term="success; inventory note leftover",
            err="hash mismatch leftover darcs inventory vs get NAR",
            flake='fetchdarcs { sha256 = "sha256-LEFTHASH="; }',
            fix='fetchdarcs { hash = "sha256-NARHASH="; }',
        ),
        fail_nuget(
            slug="nuget-snupkg-include-symbols-without-format",
            plant="schoepite-nupkg", ver="5.4.4", nxt="5.4.5",
            kind="IncludeSymbols leftover without SymbolPackageFormat",
            leftover="IncludeSymbols no format", consumer="inc-sym",
            first="push leftover IncludeSymbols package as snupkg",
            change="5.4.5 SymbolPackageFormat snupkg pack once",
            term="fail: inc-sym still 5.4.4",
            err="error: 400 leftover IncludeSymbols without format",
            props="<IncludeSymbols>true</IncludeSymbols>\n<!-- leftover no format -->",
        ),
    )
    add(
        ok_nix(
            slug="nix-fetchFromSourcehut-git-vs-hg-nar",
            plant="vanthoffite-nix", ver="1.6.6",
            kind="fetchFromSourcehut git leftover vs hg NAR",
            leftover="Sourcehut git hash", intended="NAR of hg export",
            asset="notes/srht-hg.txt",
            first="keep leftover Sourcehut git hash as hg",
            change="NAR of hg export",
            term="success; git-as-hg note leftover",
            err="hash mismatch leftover Sourcehut git vs hg NAR",
            flake='fetchFromSourcehut { vc = "git"; sha256 = "sha256-LEFTHASH="; }',
            fix='fetchFromSourcehut { vc = "hg"; hash = "sha256-NARHASH="; }',
        ),
        fail_nuget(
            slug="nuget-snupkg-sourcelink-pagure-vs-github",
            plant="soddyite-nupkg", ver="0.5.5", nxt="0.5.6",
            kind="SourceLink Pagure leftover vs GitHub repo",
            leftover="SourceLink Pagure URL", consumer="pagure-debug",
            first="push leftover Pagure SourceLink onto GitHub package",
            change="0.5.6 GitHub SourceLink pack once",
            term="fail: pagure-debug still 0.5.5",
            err="error: 400 leftover SourceLink Pagure ≠ nupkg GitHub",
            props="<RepositoryUrl>https://pagure.io/soddyite</RepositoryUrl>",
        ),
    )
    add(
        ok_cosign(
            slug="cosign-verify-recursive-referrers-vs-tag",
            plant="dufrenite-oci", ver="1.5.0",
            kind="recursive referrers leftover vs tag signature",
            leftover="recursive referrers leftover", intended="tag signature",
            asset="dist/dufrenite-referrers.json",
            first="verify leftover recursive referrers as tag sig",
            change="sign tag identity only", term="success; referrers leftover",
            err="Error: leftover recursive referrers; policy wants tag sig",
            policy='{\n  "referrers": false\n}',
            sign="run: cosign sign --recursive --yes $IMAGE",
        ),
        fail_npm(
            slug="npm-provenance-workspaces-nohoist-subject",
            plant="eulytine-js", ver="2.4.1", nxt="2.4.2",
            kind="nohoist leftover vs provenance subject",
            leftover="workspaces nohoist leftover", consumer="nohoist-lock",
            first="publish leftover nohoist workspace as provenance",
            change="2.4.2 hoist then OIDC",
            term="fail: nohoist-lock still 2.4.1",
            err="npm ERR! leftover nohoist in subjectDigest",
            wf='run: npm publish --provenance\n# leftover nohoist',
        ),
    )
    add(
        ok_cosign(
            slug="cosign-fulcio-spire-workload-vs-github",
            plant="fluocerite-oci", ver="3.1.2",
            kind="SPIRE workload leftover vs GitHub Fulcio",
            leftover="SPIRE workload identity", intended="GitHub Fulcio SAN",
            asset="dist/fluocerite-spire.svid",
            first="verify leftover SPIRE SVID as GitHub Fulcio",
            change="sign keyless GitHub Fulcio", term="success; SPIRE leftover",
            err="Error: leftover SPIRE SVID; Fulcio wants GitHub",
            policy='{\n  "oidcIssuer": "https://token.actions.githubusercontent.com"\n}',
            sign="run: cosign sign --yes $IMAGE  # leftover spire",
        ),
        fail_npm(
            slug="npm-trusted-publisher-ghes-hostname",
            plant="gahnite-js", ver="0.9.3", nxt="0.9.4",
            kind="GHES hostname leftover vs github.com publisher",
            leftover="publisher ghes.example", consumer="ghes-lock",
            first="publish leftover GHES publisher onto github.com package",
            change="0.9.4 github.com OIDC",
            term="fail: ghes-lock still 0.9.3",
            err="npm ERR! leftover trusted publisher ghes.example",
            wf="run: npm publish --provenance\n# leftover ghes hostname",
        ),
    )
    add(
        ok_pypi(
            slug="pypi-oidc-issuer-sourcehut-vs-github",
            plant="hauyne-py", ver="1.4.4",
            kind="Sourcehut OIDC leftover vs GitHub publisher",
            leftover="https://meta.sr.ht/_services/token",
            intended="https://token.actions.githubusercontent.com",
            asset="docs/hauyne-srht-1.4.3.note",
            first="twine leftover Sourcehut issuer so GitHub OIDC is unused",
            change="register GitHub issuer", term="success; Sourcehut leftover",
            err="403 leftover issuer meta.sr.ht; publisher is github.com",
            wf="run: twine upload dist/*\n# leftover sourcehut oidc",
            old="1.4.3",
        ),
        fail_maven(
            slug="maven-gpg-sign-tests-javadoc-both-missing",
            plant="ilvaite-mvn", ver="2.0.2", nxt="2.0.3",
            kind="tests+javadoc leftover unsigned pair",
            leftover="tests and javadoc no .asc", staging="orgilvaite-4",
            first="close leftover staging with unsigned tests+javadoc",
            change="2.0.3 sign both classifiers; new staging",
            term="fail: BOM still orgilvaite-4",
            err="close rejected: leftover tests+javadoc have no .asc",
            pom="<!-- leftover skip tests and javadoc sign -->",
        ),
    )
    add(
        ok_pypi(
            slug="pypi-trusted-publisher-environment-reviewers-gate",
            plant="jadeite-py", ver="5.0.1",
            kind="environment reviewers leftover vs auto publisher",
            leftover="environment reviewers leftover",
            intended="auto release environment",
            asset="docs/jadeite-rev-5.0.0.note",
            first="twine leftover while reviewers pending",
            change="register auto environment", term="success; reviewers leftover",
            err="403 leftover environment reviewers pending",
            wf="environment:\n  name: release\n  reviewers: leftover",
            old="5.0.0",
        ),
        fail_maven(
            slug="maven-central-portal-wait-timeout-vs-poll",
            plant="kamacite-mvn", ver="3.3.0", nxt="3.3.1",
            kind="portal wait timeout leftover vs poll",
            leftover="waitForPublish timeout leftover", staging="orgkamacite-2",
            first="close leftover portal deploy after wait timeout",
            change="3.3.1 poll then new staging",
            term="fail: BOM still orgkamacite-2",
            err="close rejected: leftover waitForPublish timeout",
            pom="<waitForPublish>true</waitForPublish><!-- leftover timeout -->",
        ),
    )
    add(
        ok_crates(
            slug="crates-yank-vs-cargo-semver-checks-rustdoc",
            plant="labradorite-crate", ver="4.1.1", yanked="4.1.0",
            kind="semver-checks rustdoc leftover after yank",
            leftover="semver rustdoc 4.1.0", intended="sparse yanked 4.1.0",
            asset="docs/semver-rd-4.1.0.json",
            first="unyank so semver rustdoc stays",
            change="4.1.1; leave rustdoc JSON",
            term="success; semver rustdoc 4.1.0 leftover",
            err="error: refuse unyank\nsemver rustdoc leftover still 4.1.0",
            pointer="docs/semver-rd-4.1.0.json",
        ),
        fail_brew(
            slug="homebrew-bottle-rebuild-vs-on-macos-if-arm",
            plant="malachite-brew", ver="0.6.6",
            kind="on_macos arm leftover vs intel bottle",
            leftover="on_macos arm leftover", intended="intel poured bottle",
            consumer="macos-arm",
            first="pour leftover arm on_macos bottle on intel",
            change="rebuild intel; handoff macos-arm",
            term="fail: macos-arm still leftover",
            err="* leftover on_macos arm ≠ intel pour",
            formula='on_macos do\n  depends_on arch: :arm64\nend\nbottle do\n  sha256 cellar: :any, sonoma: "BOTTLESHA"\nend',
        ),
    )
    add(
        ok_crates(
            slug="crates-yank-vs-lib-rs-reverse-deps-rss",
            plant="nepheline-crate", ver="1.3.3", yanked="1.3.2",
            kind="lib.rs reverse-deps RSS leftover after yank",
            leftover="lib.rs revdeps RSS 1.3.2", intended="sparse yanked 1.3.2",
            asset="docs/librs-rss-1.3.2.xml",
            first="unyank so lib.rs RSS stays",
            change="1.3.3; leave RSS XML",
            term="success; lib.rs RSS 1.3.2 leftover",
            err="error: refuse unyank\nlib.rs RSS leftover still 1.3.2",
            pointer="docs/librs-rss-1.3.2.xml",
        ),
        fail_brew(
            slug="homebrew-bottle-rebuild-vs-fails-with-unused",
            plant="olivine-brew", ver="2.2.0",
            kind="fails_with leftover vs rebuilt bottle",
            leftover="fails_with unused leftover", intended="rebuilt bottle sha",
            consumer="fails-with",
            first="keep leftover fails_with after rebuild",
            change="clear fails_with; handoff fails-with",
            term="fail: fails-with still leftover",
            err="* leftover fails_with ≠ rebuilt bottle",
            formula='fails_with :clang\nbottle do\n  sha256 cellar: :any, sonoma: "BOTTLESHA"\nend',
        ),
    )
    add(
        ok_nix(
            slug="nix-fetchFromGitLab-subgroup-vs-nar",
            plant="peridot-nix", ver="2.7.1",
            kind="fetchFromGitLab subgroup leftover vs NAR",
            leftover="GitLab subgroup file hash", intended="NAR of subgroup archive",
            asset="notes/gitlab-sub.txt",
            first="keep leftover GitLab subgroup hash",
            change="NAR of subgroup archive",
            term="success; subgroup note leftover",
            err="hash mismatch leftover GitLab subgroup vs archive NAR",
            flake='fetchFromGitLab { group = "left/over"; sha256 = "sha256-LEFTHASH="; }',
            fix='fetchFromGitLab { hash = "sha256-NARHASH="; }',
        ),
        fail_nuget(
            slug="nuget-snupkg-sourcelink-cgit-vs-github",
            plant="quartzite-nupkg", ver="3.0.3", nxt="3.0.4",
            kind="SourceLink cgit leftover vs GitHub repo",
            leftover="SourceLink cgit URL", consumer="cgit-debug",
            first="push leftover cgit SourceLink onto GitHub package",
            change="3.0.4 GitHub SourceLink pack once",
            term="fail: cgit-debug still 3.0.3",
            err="error: 400 leftover SourceLink cgit ≠ nupkg GitHub",
            props="<RepositoryUrl>https://git.leftover.example/quartzite.git</RepositoryUrl>",
        ),
    )
    add(
        ok_nix(
            slug="nix-fetchgit-deepClone-no-leaveDotGit-vs-nar",
            plant="rhodonite-nix", ver="0.8.8",
            kind="deepClone leftover without leaveDotGit vs NAR",
            leftover="deepClone no .git hash", intended="NAR of shallow checkout",
            asset="notes/deepclone.txt",
            first="keep leftover deepClone hash",
            change="NAR of shallow checkout",
            term="success; deepClone note leftover",
            err="hash mismatch leftover deepClone vs shallow NAR",
            flake='fetchgit { deepClone = true; sha256 = "sha256-LEFTHASH="; }',
            fix='fetchgit { hash = "sha256-NARHASH="; }',
        ),
        fail_nuget(
            slug="nuget-snupkg-embed-all-sources-on-no-repo",
            plant="sapphire-nupkg", ver="1.6.1", nxt="1.6.2",
            kind="EmbedAllSources leftover without RepositoryUrl",
            leftover="EmbedAllSources no repo", consumer="embed-norepo",
            first="push leftover embedded sources without repo URL",
            change="1.6.2 RepositoryUrl + snupkg pack once",
            term="fail: embed-norepo still 1.6.1",
            err="error: 400 leftover EmbedAllSources without RepositoryUrl",
            props="<EmbedAllSources>true</EmbedAllSources>",
        ),
    )
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
        raise SystemExit("dup slug or plant in attest wave7 catalog")
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
        handle.write(json.dumps(ok_ep, ensure_ascii=False) + "\n")
        handle.write(json.dumps(fail_ep, ensure_ascii=False) + "\n")
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
