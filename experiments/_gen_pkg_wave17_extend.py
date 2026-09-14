#!/usr/bin/env python3
"""Append unique r1508+ pairs onto pkg-mill-attest-wave17.py."""
from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FAC = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / "package-release-factory"
MILL = HERE / "pkg-mill-attest-wave17.py"

USED_SLUGS: set[str] = set()
USED_MIN: set[str] = set()
if FAC.exists():
    for path in FAC.glob("batch-r*.jsonl"):
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            pid = rec["id"]
            if pid.startswith("pkg-r"):
                rest = pid[len("pkg-r") :]
                dash = rest.find("-")
                if dash >= 0:
                    USED_SLUGS.add(rest[dash + 1 :])
            m = re.search(
                r"(?:Ship )?([a-z]+)-(?:oci|js|py|mvn|crate|brew|nix|nupkg)\b",
                rec.get("goal", ""),
            )
            if m:
                USED_MIN.add(m.group(1))

for path in HERE.glob("pkg-mill-attest-wave*.py"):
    text = path.read_text()
    for m in re.finditer(r"slug='([^']+)'", text):
        USED_SLUGS.add(m.group(1))
    for m in re.finditer(r"plant='([a-z]+)-", text):
        USED_MIN.add(m.group(1))


def synth_mins():
    vowels = "aeiou"
    suffixes = ("lite", "ite", "ine", "ate", "ide")
    for a in "ijklmnopqrstuvwxyz":
        for v1 in vowels:
            for v2 in vowels:
                for s in suffixes:
                    name = a + v1 + v2 + s
                    if name not in USED_MIN:
                        yield name


MINERALS = list(synth_mins())

COSIGN = [
    ("cosign-verify-rekor-shard-us-central-vs-eu", "Rekor US-central leftover", "EU Rekor shard"),
    ("cosign-sign-kms-gcp-cloudhsm-vs-software", "GCP CloudHSM leftover", "software GCP KMS"),
    ("cosign-fulcio-kanidm-oidc-vs-github", "Kanidm Fulcio leftover", "GitHub Fulcio issuer"),
    ("cosign-policy-identity-regex-dotstar-vs-exact", "identity regex .* leftover", "exact workflow identity"),
    ("cosign-verify-bundle-media-type-jws-vs-dsse", "JWS media leftover", "DSSE media type"),
    ("cosign-sign-sk-piv-slot-9c-vs-9d", "PIV slot 9c leftover", "PIV slot 9d"),
    ("cosign-oidc-issuer-authentik-vs-github", "Authentik leftover", "GitHub Actions OIDC"),
    ("cosign-verify-cert-notbefore-skew-days", "notBefore days leftover", "NTP-aligned notBefore"),
    ("cosign-policy-ctlog-pubkey-der-vs-pem", "CT pubkey DER leftover", "CT pubkey PEM"),
    ("cosign-rekor-entry-kind-cose-vs-dsse", "COSE leftover", "DSSE Rekor kind"),
    ("cosign-sign-annotation-sbom-spdx-json-vs-cdx", "SPDX JSON leftover", "CycloneDX SBOM"),
    ("cosign-verify-tuf-mirrors-stale-vs-current", "stale TUF mirrors leftover", "current TUF mirrors"),
    ("cosign-fulcio-uri-san-email-vs-workflow", "email SAN leftover", "workflow SAN"),
    ("cosign-sign-recursive-oci-index-partial-os", "partial OS leftover", "full OCI index"),
    ("cosign-policy-max-sct-count-zero-vs-policy", "max SCT 0 leftover", "policy SCT count"),
    ("cosign-verify-oci-referrer-artifacttype-helm", "helm artifactType leftover", "OCI referrer type"),
    ("cosign-attach-predicate-in-toto-vsa02-vs-slsa", "in-toto VSA 0.2 leftover", "SLSA predicate"),
    ("cosign-copy-signature-oci-layer-vs-bundle", "OCI layer sig leftover", "bundle signature"),
    ("cosign-sign-payload-intoto-dssa-json", "DSSA leftover", "in-toto SLSA payload"),
    ("cosign-verify-identity-discussion-comment-vs-tag", "discussion comment leftover", "tag identity"),
    ("cosign-oidc-issuer-pocket-id-vs-github", "Pocket ID leftover", "GitHub Actions OIDC"),
    ("cosign-policy-builder-id-org-wildcard-vs-exact", "org wildcard leftover", "exact builder id"),
    ("cosign-verify-bundle-hash-algo-blake2s-vs-sha256", "blake2s leftover", "sha256 payload algo"),
    ("cosign-sign-kms-azure-mhsm-vs-software", "Azure MHSM leftover", "software Azure KMS"),
]

NPM = [
    ("npm-provenance-optionalDependencies-libc-freebsd", "freebsd libc leftover", "fbsd-lock"),
    ("npm-trusted-publisher-workflow-filename-shipit-yml", "workflow shipit.yml leftover", "ship-lock"),
    ("npm-oidc-audience-npmmirror-com", "audience npmmirror.com leftover", "nmm-aud"),
    ("npm-provenance-prepare-script-mutates-tarball", "prepare script leftover", "prep-lock"),
    ("npm-trusted-publisher-environment-wait-timer-1080", "wait_timer 1080 leftover", "wt1080-lock"),
    ("npm-oidc-subject-ref-milestone", "milestone leftover", "mile-lock"),
    ("npm-publish-from-wasm-edge-runner-no-oidc", "WasmEdge without OIDC leftover", "wasme-lock"),
    ("npm-trusted-publisher-classic-pat-still-latest", "classic PAT leftover", "cpat-lock"),
    ("npm-provenance-workspaces-filter-include", "workspace include leftover", "winc-lock"),
    ("npm-oidc-permissions-id-token-write-discussions", "discussions write leftover", "discw-lock"),
    ("npm-provenance-files-field-includes-flow", "files includes flow leftover", "flow-lock"),
    ("npm-trusted-publisher-org-scim-oidc-implicit", "org SCIM leftover", "scim-lock"),
    ("npm-oidc-job-container-user-operator", "container operator leftover", "coper-lock"),
    ("npm-provenance-lockfileVersion-4-vs-3", "lockfileVersion 4 leftover", "lf4-lock"),
    ("npm-publish-access-unlisted-workspace-scope", "unlisted workspace leftover", "ulws-lock"),
    ("npm-trusted-publisher-workflow-call-inputs-json", "workflow_call inputs leftover", "wci-lock"),
    ("npm-oidc-issuer-harness-vs-github", "Harness leftover", "harn-lock"),
    ("npm-provenance-bin-field-windows-ps1-subject", "bin ps1 leftover", "binps-lock"),
    ("npm-oidc-audience-registry-yarnpkg-net", "audience registry.yarnpkg.net leftover", "rynet-lock"),
    ("npm-provenance-os-cpu-optional-freebsd-arm64", "freebsd arm leftover", "fbsda-lock"),
    ("npm-publish-provenance-omit-optional-then-true", "omit-optional then true leftover", "oot-lock"),
    ("npm-trusted-publisher-wasm-edge-ephemeral-no-oidc", "WasmEdge ephemeral leftover", "wem-lock"),
    ("npm-provenance-bundleDependencies-public-hoist-pattern", "public-hoist leftover", "phoist-lock"),
    ("npm-oidc-subject-ref-issue-comment", "issue_comment leftover", "icmt-lock"),
]

PYPI = [
    ("pypi-trusted-publisher-workflow-path-release-ps1", "release.ps1 leftover", "release.yml path"),
    ("pypi-oidc-issuer-dagger-cloud-vs-github", "Dagger Cloud leftover", "GitHub OIDC issuer"),
    ("pypi-attestation-data-files-missing-sdist", "data-files leftover", "sdist+wheel pair"),
    ("pypi-twine-attestations-ion-not-dsse", "Ion leftover", "DSSE envelope"),
    ("pypi-trusted-publisher-environment-name-shipit-typo", "environment shipit leftover", "environment production"),
    ("pypi-oidc-job-container-id-token-audience-mismatch", "container audience leftover", "runner id-token"),
    ("pypi-hatch-index-codeberg-pkg-url-leftover", "hatch codeberg leftover", "prod PyPI index"),
    ("pypi-uv-publish-trusted-publishing-dry-run", "uv dry-run leftover", "uv trusted publishing"),
]

MAVEN = [
    ("maven-gpg-sign-aar-only-missing-jar", "aar-only leftover", "aar-stg"),
    ("maven-central-portal-publishing-type-validation", "validation leftover", "val-stg"),
    ("maven-gpg-keyring-agent-scd-busy", "busy scd leftover", "bscd-stg"),
    ("maven-gpg-passphrase-qt-xor-env", "qt leftover", "qt-stg"),
    ("maven-central-bundle-missing-aar-checksum", "aar checksum leftover", "aarc-stg"),
    ("maven-gpg-useagent-true-pinentry-curses", "pinentry curses leftover", "pcurses-stg"),
    ("maven-ossrh-staging-profile-id-canary", "canary profile leftover", "canp-stg"),
    ("maven-gpg-sign-asc-armor-version-5", "armor v5 leftover", "av5-stg"),
]


def assert_unique(rows, label):
    slugs = [r[0] for r in rows]
    if len(slugs) != len(set(slugs)):
        raise SystemExit(f"dup in {label}")
    hits = [s for s in slugs if s in USED_SLUGS]
    if hits:
        raise SystemExit(f"{label} slug already published/catalogued: {hits[:8]}")


for label, rows in (
    ("cosign", COSIGN),
    ("npm", NPM),
    ("pypi", PYPI),
    ("maven", MAVEN),
):
    assert_unique(rows, label)

N = len(COSIGN)
assert len(NPM) == N
assert len(PYPI) == 8 and len(MAVEN) == 8
need = N * 2 + 8 * 2
if len(MINERALS) < need:
    raise SystemExit(f"need {need} minerals, have {len(MINERALS)}")


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

    for i, ((cslug, cleft, cint), (nslug, nleft, ncons)) in enumerate(zip(COSIGN, NPM)):
        cp, np_ = take("oci"), take("js")
        ver = ver_triple(i, 2, 2, 2)
        nv = ver_triple(i, 3, 1, 2)
        nxt = bump(nv)
        minc = cp.split("-")[0]
        lines.append("    add(")
        lines.append("        ok_cosign(")
        lines.append(f"            slug={cslug!r},")
        lines.append(f"            plant={cp!r}, ver={ver!r},")
        lines.append(f"            kind={(cleft + ' leftover vs ' + cint)!r},")
        lines.append(f"            leftover={cleft!r}, intended={cint!r},")
        lines.append(f"            asset='dist/{minc}-left.txt',")
        lines.append(f"            first={'verify leftover ' + cleft + ' against ' + cint!r},")
        lines.append(f"            change={'sign matching ' + cint!r},")
        lines.append(f"            term={'success; ' + cleft + ' leftover'!r},")
        lines.append(f"            err={'Error: leftover ' + cleft + '; want ' + cint!r},")
        pol = '{\\n  "intended": "' + cint + '"\\n}'
        lines.append(f"            policy={pol!r},")
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

    for i, ((pslug, pleft, pint), (mslug, mleft, mstg)) in enumerate(zip(PYPI, MAVEN)):
        pp, mp = take("py"), take("mvn")
        ver = ver_triple(i + 4, 4, 2, 1)
        old = ver_triple(i + 4, 4, 1, 10)
        mv = ver_triple(i + 5, 2, 3, 1)
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
    return "\n".join(lines)


def main() -> None:
    extra = emit_add_calls()
    src = MILL.read_text()
    marker = "    return extra\n"
    if src.count(marker) != 1:
        raise SystemExit(f"expected 1 return extra, got {src.count(marker)}")
    if "cosign-verify-rekor-shard-us-central-vs-eu" in src:
        raise SystemExit("extend catalog already present")
    MILL.write_text(src.replace(marker, extra + "\n" + marker, 1))
    print(f"appended {N + 8} pairs to {MILL.name}; minerals start {MINERALS[0]}")


if __name__ == "__main__":
    main()
