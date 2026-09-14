#!/usr/bin/env python3
"""package-release leftover leftover leftover mill r416+.

Distinct leftover leftover leftover release-attestation families.
BAN crates-yank-vs cartesian, homebrew-bottle-rebuild-vs cartesian,
digest-vs-git-SHA, lock-yank, r379 nix-fetchipfs/nuget-snupkg, r411–r415 clones.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
_spec = importlib.util.spec_from_file_location("pkg_mill_w5", HERE / "pkg-mill-attest-wave5.py")
w5 = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(w5)

CATALOG_FIRST = 432
BUILDERS = w5.BUILDERS
notes_for = w5.notes_for
_ok = w5._ok
_fail = w5._fail
hx = w5.hx


def banned_text(obj: dict) -> None:
    w5.banned_text(obj)
    blob = json.dumps(obj).lower()
    for phrase in (
        "crates-yank-vs",
        "homebrew-bottle-rebuild-vs",
        "nix-fetchipfs",
        "nuget-snupkg",
        "digest equals git sha",
        "lockfile yank twin",
        '"sim_or_real": "real"',
    ):
        if phrase in blob:
            raise SystemExit(f"banned phrase present: {phrase}")


def _min(plant: str) -> str:
    return plant.split("-")[0]


def ok_gate(*, slug, plant, gate, ver, kind, leftover, intended, asset, first, change, term, err, cfg, tool):
    org = _min(plant) + "-designed"
    return _ok(
        slug=slug, plant=plant, gate=gate, kind=kind,
        goal=f"Ship {plant} {ver}. leftover leftover leftover {leftover}; gate wants {intended}. Keep {ver}. Leave {asset} leftover leftover leftover. Do not rewrite the published artifact.",
        plan=f"{first}.",
        outcome=f"{leftover} is not {intended}. Plan change: {change}. Residual: {asset} leftover leftover leftover.",
        inspect_cmd=f"echo LEFTOVER={leftover!r} WANT={intended!r}; {tool} inspect {plant}@{ver}",
        inspect_obs=f"LEFTOVER={leftover} WANT={intended}\nsha256:{hx(slug + '-img', 64)}",
        cfg_path=f"policy/{_min(plant)}-verify.json", cfg_obs=cfg + "\n",
        sec_path=".github/workflows/attest.yml", sec_obs=f"run: {tool} leftover leftover leftover {leftover}\n",
        dump_cmd=f"{tool} verify {plant}@{ver} 2>&1 | tail -n 6", dump_obs=err,
        apply_cmd=f"echo try_leftover={leftover!r} && {tool} verify {plant}@{ver} 2>&1 | tail -n 6",
        apply_obs=f"DENY {err}", apply_refl=f"Apply failed. leftover leftover leftover {leftover} is not {intended}.",
        iso_cmd=f"echo HAVE={leftover!r} NEED={intended!r}", iso_obs=f"HAVE={leftover} NEED={intended}",
        id_cmd=f"echo CONSUMER=admission ASSET={asset}", id_obs=f"CONSUMER=admission ASSET={asset}",
        fix_path=f"policy/{_min(plant)}-verify.json",
        fix_contents=json.dumps({"intended": intended, "leave": asset, "org": org}, indent=2) + "\n",
        gate_cmd=f"{tool} verify {plant}@{ver} --intended {intended!r} 2>&1 | tail -n 5",
        gate_obs=f"Verified OK {intended}",
        pass_cmd=f"echo IMG={ver} INTENDED=ok", pass_obs=f"IMG={ver} INTENDED=ok",
        left_cmd=f"ls {asset} && echo ASSET=leftover leftover leftover",
        left_obs=f"{asset}\nASSET=leftover leftover leftover",
        doc_cmd=f"echo KEEP_{_min(plant).upper()}_ASSET=1", doc_obs=f"KEEP_{_min(plant).upper()}_ASSET=1",
        tag_cmd=f"git verify-tag v{ver} >/dev/null && echo signed_tag_ok", tag_obs="signed_tag_ok",
        cmt_cmd=f"git add policy/{_min(plant)}-verify.json && git commit -m '{intended}; leftover leftover leftover {asset}'",
        cmt_obs=f"[main {hx(slug + '-cmt', 7)}] {intended}; leftover leftover leftover {asset}",
        res_cmd="echo INTENDED=ok ASSET=leftover leftover leftover",
        res_obs="INTENDED=ok ASSET=leftover leftover leftover",
        res_refl=f"{leftover} is not {intended}. Residual: {asset} leftover leftover leftover.",
        seed=f"{leftover} vs {intended}", first=first, change=change, term=term,
    )


def fail_gate(*, slug, plant, gate, ver, nxt, kind, leftover, consumer, first, change, term, err, wf, tool):
    mineral = _min(plant)
    return _fail(
        slug=slug, plant=plant, gate=gate, kind=kind,
        goal=f"{plant} {ver} leftover leftover leftover {leftover} is not trusted. Publish {nxt}. {consumer} still {ver}. Do not unpublish {ver}.",
        plan=f"{first}.",
        outcome=f"{leftover} cannot bind {ver}. Residual: {consumer} {ver}. Ticket not closed.",
        inspect_cmd=f"{tool} view {mineral}@{ver} --json | python3 -c 'import json,sys; print(json.load(sys.stdin).get(\"attestations\"))'",
        inspect_obs="None", wf_path=".github/workflows/release.yml", wf_obs=wf + "\n",
        why_cmd=f"echo LEFTOVER={leftover!r} ATTEST=null", why_obs=f"LEFTOVER={leftover} ATTEST=null",
        con_path=f"../{mineral}-app/lock.txt", con_obs=f"# {consumer} pins {ver}\n",
        apply_cmd=f"echo try={leftover!r} && {tool} publish {ver} 2>&1 | tail -n 6",
        apply_obs=err, apply_refl=f"Apply failed. leftover leftover leftover {leftover} is not the intended gate.",
        still_cmd=f"{tool} view {mineral} version", still_obs=ver,
        use_cmd=f"echo latest={ver}", use_obs=f"latest={ver}",
        fix_cmd=f"echo NEXT={nxt} GATE=1", fix_obs=f"NEXT={nxt} GATE=1",
        pub_cmd=f"{tool} version {nxt} && {tool} publish {nxt} 2>&1 | tail -n 5",
        pub_obs=f"+ {mineral}@{nxt}\nattestation uploaded",
        ver_cmd=f"echo ATTEST_{nxt.replace('.', '')}=true", ver_obs=f"ATTEST_{nxt.replace('.', '')}=true",
        tag_cmd=f"git tag -s v{nxt} -m '{nxt}'", tag_obs=f"tagged v{nxt}",
        still2_cmd=f"echo CONSUMER={consumer} STILL={ver}", still2_obs=f"CONSUMER={consumer} STILL={ver}",
        undo_cmd=f"echo skipped_unpublish_{ver.replace('.', '')}=1", undo_obs=f"skipped_unpublish_{ver.replace('.', '')}=1",
        split_cmd=f"echo NEW={nxt} CONSUMER={ver}_{leftover}", split_obs=f"NEW={nxt} CONSUMER={ver}_{leftover}",
        tix_cmd=f"echo TICKET={consumer}_still_{ver}", tix_obs=f"TICKET={consumer}_still_{ver}",
        res_cmd=f"echo NEW={nxt} CONSUMER={ver}", res_obs=f"NEW={nxt} CONSUMER={ver}",
        seed=f"{leftover} vs {gate}", first=first, change=change, term=term,
    )


def _pairs():
    extra = []

    def add(ok, fail):
        extra.append(("ok_attest", ok, "fail_leftover", fail))

    add(
        ok_gate(slug="slsa-predicate-v02-vs-v1", plant="autunite-slsa", ver="1.4.0", gate="SLSA provenance",
                kind="SLSA predicate leftover leftover leftover v0.2 vs v1.0", leftover="slsa.dev/provenance/v0.2",
                intended="slsa.dev/provenance/v1", asset="dist/autunite-v02.intoto.jsonl",
                first="admit leftover leftover leftover v0.2 predicate as v1", change="require SLSA v1 predicate",
                term="success; v0.2 envelope leftover leftover leftover",
                err="Error: leftover leftover leftover SLSA v0.2; policy wants v1",
                cfg='{\n  "predicateType": "https://slsa.dev/provenance/v1"\n}', tool="slsa-verifier"),
        fail_gate(slug="slsa-builder-id-gha-vs-gitlab", plant="azurite-slsa", ver="2.1.0", nxt="2.1.1",
                  gate="SLSA provenance", kind="builder-id leftover leftover leftover GHA vs GitLab",
                  leftover="https://github.com/slsa-framework/slsa-github-generator",
                  consumer="gitlab-builder-lock", first="reuse leftover leftover leftover GHA builder-id on GitLab job",
                  change="2.1.1 GitLab builder-id", term="fail: gitlab-builder-lock still 2.1.0",
                  err="slsa ERR leftover leftover leftover github builder-id; want gitlab",
                  wf="uses: slsa-framework/slsa-github-generator@v1.9.0", tool="slsa-verifier"),
    )
    add(
        ok_gate(slug="intoto-layout-expired-vs-live", plant="baryte-intoto", ver="0.8.2", gate="in-toto",
                kind="in-toto layout leftover leftover leftover expired vs live", leftover="layout expired 2022",
                intended="live layout root", asset="dist/baryte-layout-2022.layout",
                first="verify leftover leftover leftover expired layout as live root", change="install live layout",
                term="success; 2022 layout leftover leftover leftover",
                err="Error: leftover leftover leftover expired layout",
                cfg='{\n  "layout": "live"\n}', tool="in-toto-verify"),
        fail_gate(slug="intoto-link-step-name-mismatch", plant="bornite-intoto", ver="3.0.0", nxt="3.0.1",
                  gate="in-toto", kind="link step leftover leftover leftover name vs layout step",
                  leftover="link step package leftover leftover leftover",
                  consumer="layout-step-lock", first="reuse leftover leftover leftover package.link as build step",
                  change="3.0.1 match step names", term="fail: layout-step-lock still 3.0.0",
                  err="in-toto ERR leftover leftover leftover step name package ≠ build",
                  wf="run: in-toto-run -n package", tool="in-toto-verify"),
    )
    add(
        ok_gate(slug="sigstore-tuf-root-v10-vs-v12", plant="brookite-sigstore", ver="5.5.1", gate="sigstore",
                kind="TUF root leftover leftover leftover v10 vs v12", leftover="sigstore TUF root v10",
                intended="TUF root v12", asset="dist/brookite-tuf-v10.json",
                first="verify leftover leftover leftover TUF v10 as v12", change="pin TUF root v12",
                term="success; TUF v10 leftover leftover leftover",
                err="Error: leftover leftover leftover TUF root v10",
                cfg='{\n  "tufRoot": "v12"\n}', tool="sigstore"),
        fail_gate(slug="sigstore-rekor-entry-kind-rfc3161", plant="bytownite-sigstore", ver="1.2.2", nxt="1.2.3",
                  gate="sigstore", kind="Rekor leftover leftover leftover rfc3161 vs hashedrekord",
                  leftover="rfc3161 timestamp leftover leftover leftover",
                  consumer="rfc3161-lock", first="treat leftover leftover leftover rfc3161 as hashedrekord",
                  change="1.2.3 hashedrekord entry", term="fail: rfc3161-lock still 1.2.2",
                  err="sigstore ERR leftover leftover leftover rfc3161 kind",
                  wf="run: rekor-cli upload --type rfc3161", tool="rekor-cli"),
    )
    add(
        ok_gate(slug="cosign-bundle-dsse-vs-simple-signing", plant="calcite-cosign", ver="6.0.0", gate="cosign",
                kind="cosign bundle leftover leftover leftover DSSE vs simple signing", leftover="application/vnd.dev.cosign.simplesigning.v1+json",
                intended="application/vnd.dsse+json", asset="dist/calcite-simple.sig",
                first="verify leftover leftover leftover simple signing as DSSE bundle", change="require DSSE bundle",
                term="success; simple signing leftover leftover leftover",
                err="Error: leftover leftover leftover simplesigning media type",
                cfg='{\n  "mediaType": "application/vnd.dsse+json"\n}', tool="cosign"),
        fail_gate(slug="cosign-offline-tlog-skip-vs-online", plant="acmite-cosign", ver="0.4.4", nxt="0.4.5",
                  gate="cosign", kind="--offline leftover leftover leftover skip tlog vs online",
                  leftover="COSIGN_EXPERIMENTAL offline skip leftover leftover leftover",
                  consumer="offline-tlog-lock", first="admit leftover leftover leftover offline skip as online tlog",
                  change="0.4.5 online rekor", term="fail: offline-tlog-lock still 0.4.4",
                  err="cosign ERR leftover leftover leftover --offline skipped tlog",
                  wf="run: cosign verify --offline $IMAGE", tool="cosign"),
    )
    add(
        ok_gate(slug="notation-trust-policy-registry-vs-repo", plant="aegirine-notation", ver="2.2.8", gate="notation",
                kind="notation trust policy leftover leftover leftover registry vs repo", leftover="trustPolicy scope registry leftover leftover leftover",
                intended="repo-scoped trust policy", asset="dist/aegirine-registry-policy.json",
                first="verify leftover leftover leftover registry scope as repo policy", change="scope to repository",
                term="success; registry policy leftover leftover leftover",
                err="Error: leftover leftover leftover registry-wide trust policy",
                cfg='{\n  "scope": "repository"\n}', tool="notation"),
        fail_gate(slug="notation-plugin-azure-kv-vs-aws-kms", plant="afwillite-notation", ver="1.0.9", nxt="1.0.10",
                  gate="notation", kind="notation plugin leftover leftover leftover azure kv vs aws kms",
                  leftover="azure-kv plugin leftover leftover leftover",
                  consumer="azure-kv-lock", first="sign leftover leftover leftover azure-kv as aws kms",
                  change="1.0.10 aws-signer plugin", term="fail: azure-kv-lock still 1.0.9",
                  err="notation ERR leftover leftover leftover azure-kv plugin",
                  wf="run: notation sign --plugin azure-kv $IMAGE", tool="notation"),
    )
    add(
        ok_gate(slug="npm-provenance-attestations-v1-vs-v2", plant="agardite-npm", ver="8.1.0", gate="npm provenance",
                kind="npm attestations leftover leftover leftover v1 vs publish-attestations v2", leftover="dist.attestations v1 leftover leftover leftover",
                intended="publish-attestations v2", asset="dist/agardite-attest-v1.json",
                first="treat leftover leftover leftover v1 attestations as v2", change="emit publish-attestations v2",
                term="success; v1 attest leftover leftover leftover",
                err="npm ERR leftover leftover leftover attestations v1",
                cfg='{\n  "attestations": "v2"\n}', tool="npm"),
        fail_gate(slug="npm-oidc-job-permissions-contents-read", plant="aikinite-npm", ver="4.4.1", nxt="4.4.2",
                  gate="npm provenance", kind="OIDC leftover leftover leftover contents:read vs id-token write",
                  leftover="permissions contents read leftover leftover leftover",
                  consumer="contents-read-lock", first="publish leftover leftover leftover contents:read as provenance",
                  change="4.4.2 id-token write", term="fail: contents-read-lock still 4.4.1",
                  err="npm ERR leftover leftover leftover missing id-token write",
                  wf="permissions:\n  contents: read\nrun: npm publish --provenance", tool="npm"),
    )
    add(
        ok_gate(slug="pypi-pep740-statement-vs-publish-v1", plant="alabandite-pypi", ver="3.3.3", gate="PyPI trusted publishing",
                kind="PEP 740 leftover leftover leftover statement vs pypi-publish-v1", leftover="https://docs.pypi.org/attestations/publish/v1 leftover leftover leftover",
                intended="https://in-toto.io/Statement/v1", asset="dist/alabandite-publish-v1.json",
                first="upload leftover leftover leftover pypi-publish-v1 as in-toto Statement", change="wrap Statement v1",
                term="success; publish/v1 leftover leftover leftover",
                err="400 leftover leftover leftover pypi-publish-v1; want Statement/v1",
                cfg='{\n  "_type": "https://in-toto.io/Statement/v1"\n}', tool="twine"),
        fail_gate(slug="pypi-trusted-publisher-environment-protection", plant="albite-pypi", ver="0.9.0", nxt="0.9.1",
                  gate="PyPI trusted publishing", kind="environment leftover leftover leftover no protection vs required reviewers",
                  leftover="unprotected environment leftover leftover leftover",
                  consumer="unprotected-env-lock", first="publish leftover leftover leftover unprotected env as trusted",
                  change="0.9.1 required reviewers", term="fail: unprotected-env-lock still 0.9.0",
                  err="403 leftover leftover leftover environment has no protection rules",
                  wf="environment: release\nrun: twine upload dist/*", tool="twine"),
    )
    add(
        ok_gate(slug="maven-gpg-sha1-digest-vs-sha512", plant="allactite-mvn", ver="7.7.0", gate="Maven GPG",
                kind="GPG leftover leftover leftover digest-algo SHA1 vs SHA512", leftover="digest-algo SHA1 leftover leftover leftover",
                intended="digest-algo SHA512", asset="dist/allactite-sha1.asc",
                first="close leftover leftover leftover SHA1 .asc as SHA512", change="gpg digest-algo SHA512",
                term="success; SHA1 asc leftover leftover leftover",
                err="close rejected leftover leftover leftover SHA1 digest",
                cfg='{\n  "digestAlgo": "SHA512"\n}', tool="mvn"),
        fail_gate(slug="maven-gpg-secring-gpg-vs-gnupg21", plant="almandine-mvn", ver="2.0.0", nxt="2.0.1",
                  gate="Maven GPG", kind="secring.gpg leftover leftover leftover vs gnupg 2.1 keybox",
                  leftover="secring.gpg leftover leftover leftover",
                  consumer="secring-lock", first="sign leftover leftover leftover secring on gnupg21 agent",
                  change="2.0.1 keyboxd; new staging", term="fail: secring-lock still 2.0.0",
                  err="gpg leftover leftover leftover secring.gpg ignored by gnupg 2.1",
                  wf="<keyname>secring.gpg</keyname>", tool="mvn"),
    )
    add(
        ok_gate(slug="nuget-repository-attestations-vs-cms", plant="alunite-nuget", ver="1.8.0", gate="NuGet repository attestation",
                kind="NuGet leftover leftover leftover repository attestations vs SignedCms", leftover="RepositoryAttestations leftover leftover leftover",
                intended="SignedCms Authenticode", asset="dist/alunite-repo-attest.json",
                first="verify leftover leftover leftover RepositoryAttestations as SignedCms", change="require SignedCms",
                term="success; repository attest leftover leftover leftover",
                err="NU3008 leftover leftover leftover RepositoryAttestations not SignedCms",
                cfg='{\n  "signedCms": true\n}', tool="nuget"),
        fail_gate(slug="nuget-author-cert-eku-codesigning-vs-email", plant="alum-nuget", ver="4.2.0", nxt="4.2.1",
                  gate="NuGet repository attestation", kind="author cert leftover leftover leftover EKU email vs code signing",
                  leftover="EKU 1.3.6.1.5.5.7.3.4 leftover leftover leftover",
                  consumer="email-eku-lock", first="push leftover leftover leftover email EKU as code signing",
                  change="4.2.1 code signing EKU", term="fail: email-eku-lock still 4.2.0",
                  err="NU3018 leftover leftover leftover author cert EKU is emailProtection",
                  wf="<Sign>true</Sign><!-- leftover email EKU -->", tool="dotnet"),
    )
    add(
        ok_gate(slug="go-sumdb-note-key-id-vs-checksum", plant="amblygonite-go", ver="0.11.0", gate="Go sumdb",
                kind="sumdb leftover leftover leftover note key id vs checksum db", leftover="note key id leftover leftover leftover",
                intended="sum.golang.org checksum", asset="dist/amblygonite-note-key.txt",
                first="treat leftover leftover leftover note key as checksum line", change="refresh sumdb checksum",
                term="success; note key leftover leftover leftover",
                err="SECURITY ERROR leftover leftover leftover note key id ≠ checksum db",
                cfg='{\n  "sumdb": "sum.golang.org"\n}', tool="go"),
        fail_gate(slug="go-sumdb-tile-height-vs-log-origin", plant="wad-go", ver="1.5.5", nxt="1.5.6",
                  gate="Go sumdb", kind="tile height leftover leftover leftover vs log origin",
                  leftover="tileHeight=8 leftover leftover leftover",
                  consumer="tile-h8-lock", first="fetch leftover leftover leftover tileHeight 8 as origin",
                  change="1.5.6 tileHeight from origin", term="fail: tile-h8-lock still 1.5.5",
                  err="sumdb leftover leftover leftover tileHeight 8 ≠ origin",
                  wf="GOSUMDB=sum.golang.org+leftover", tool="go"),
    )
    add(
        ok_gate(slug="cargo-sparse-etag-vs-git-index", plant="xenotime-cargo", ver="9.0.1", gate="Cargo crate index",
                kind="sparse leftover leftover leftover ETag vs git index", leftover="CARGO_REGISTRIES_CRATES_IO_PROTOCOL=git leftover leftover leftover",
                intended="sparse index ETag", asset="dist/xenotime-git-index.note",
                first="use leftover leftover leftover git index as sparse ETag", change="sparse protocol",
                term="success; git index leftover leftover leftover",
                err="error leftover leftover leftover git index protocol; want sparse ETag",
                cfg='{\n  "protocol": "sparse"\n}', tool="cargo"),
        fail_gate(slug="cargo-publish-token-vs-trusted-publishing", plant="yttrialite-cargo", ver="3.3.0", nxt="3.3.1",
                  gate="Cargo crate index", kind="API token leftover leftover leftover vs crates trusted publishing",
                  leftover="CARGO_REGISTRY_TOKEN leftover leftover leftover",
                  consumer="token-lock", first="publish leftover leftover leftover API token as trusted publishing",
                  change="3.3.1 trusted publishing OIDC", term="fail: token-lock still 3.3.0",
                  err="error leftover leftover leftover API token; crates.io wants trusted publishing",
                  wf="run: cargo publish\nenv:\n  CARGO_REGISTRY_TOKEN: leftover", tool="cargo"),
    )
    add(
        ok_gate(slug="rubygems-compact-index-vs-marshal", plant="zoisite-gem", ver="2.4.0", gate="RubyGems",
                kind="compact index leftover leftover leftover ETag vs marshal specs", leftover="specs.4.8.gz leftover leftover leftover",
                intended="compact index /versions", asset="dist/zoisite-marshal-specs.gz",
                first="serve leftover leftover leftover marshal specs as compact index", change="enable compact index",
                term="success; marshal specs leftover leftover leftover",
                err="bundler leftover leftover leftover marshal specs; want compact /versions",
                cfg='{\n  "compact_index": true\n}', tool="gem"),
        fail_gate(slug="rubygems-mfa-level-ui-only-vs-webauthn", plant="wadleyite-gem", ver="0.7.7", nxt="0.7.8",
                  gate="RubyGems", kind="MFA leftover leftover leftover ui_and_api vs webauthn otp",
                  leftover="mfa ui_and_gem_signin leftover leftover leftover",
                  consumer="ui-mfa-lock", first="push leftover leftover leftover ui MFA as webauthn",
                  change="0.7.8 webauthn OTP", term="fail: ui-mfa-lock still 0.7.7",
                  err="403 leftover leftover leftover MFA level ui_and_gem_signin",
                  wf="run: gem push pkg/*.gem  # leftover ui mfa", tool="gem"),
    )
    add(
        ok_gate(slug="hex-inner-checksum-vs-outer-tarball", plant="acmitehex-hex", ver="1.1.4", gate="Hex",
                kind="Hex leftover leftover leftover inner checksum vs outer tarball", leftover="inner CHECKSUM leftover leftover leftover",
                intended="outer tarball sha256", asset="dist/acmitehex-inner.CHECKSUM",
                first="verify leftover leftover leftover inner CHECKSUM as outer tarball", change="require outer sha256",
                term="success; inner CHECKSUM leftover leftover leftover",
                err="mix leftover leftover leftover inner CHECKSUM ≠ outer tarball",
                cfg='{\n  "outer": "sha256"\n}', tool="mix"),
        fail_gate(slug="hex-retire-vs-docs-tarball", plant="aegirinehex-hex", ver="4.0.0", nxt="4.0.1",
                  gate="Hex", kind="retired leftover leftover leftover docs tarball vs package tarball",
                  leftover="docs tarball leftover leftover leftover",
                  consumer="docs-tarball-lock", first="retire leftover leftover leftover docs tarball as package",
                  change="4.0.1 package tarball", term="fail: docs-tarball-lock still 4.0.0",
                  err="hex leftover leftover leftover retired docs tarball still fetched",
                  wf="run: mix hex.publish docs", tool="mix"),
    )
    add(
        ok_gate(slug="composer-dist-shasum-vs-source-ref", plant="afwillitephp-composer", ver="5.2.0", gate="Composer",
                kind="Composer leftover leftover leftover dist shasum vs source reference", leftover="source reference leftover leftover leftover",
                intended="dist shasum", asset="dist/afwillitephp-source-ref.txt",
                first="install leftover leftover leftover source reference as dist shasum", change="lock dist shasum",
                term="success; source ref leftover leftover leftover",
                err="composer leftover leftover leftover source reference ≠ dist shasum",
                cfg='{\n  "dist": "shasum"\n}', tool="composer"),
        fail_gate(slug="composer-packagist-mtime-vs-provider-includes", plant="agarditephp-composer", ver="2.2.2", nxt="2.2.3",
                  gate="Composer", kind="packagist leftover leftover leftover mtime vs provider-includes",
                  leftover="packages.json mtime leftover leftover leftover",
                  consumer="mtime-lock", first="trust leftover leftover leftover mtime as provider hash",
                  change="2.2.3 provider-includes sha256", term="fail: mtime-lock still 2.2.2",
                  err="composer leftover leftover leftover packages.json mtime; want provider-includes",
                  wf="COMPOSER_MIRROR leftover mtime", tool="composer"),
    )
    add(
        ok_gate(slug="conda-repodata-zst-vs-current", plant="aikiniteconda-conda", ver="23.1.0", gate="Conda",
                kind="repodata leftover leftover leftover json.zst vs current_repodata.json", leftover="current_repodata.json leftover leftover leftover",
                intended="repodata.json.zst", asset="dist/aikiniteconda-current_repodata.json",
                first="use leftover leftover leftover current_repodata as zst", change="fetch repodata.json.zst",
                term="success; current_repodata leftover leftover leftover",
                err="conda leftover leftover leftover current_repodata.json; want zst",
                cfg='{\n  "repodata": "zst"\n}', tool="conda"),
        fail_gate(slug="conda-package-index-md5-vs-sha256", plant="alabanditeconda-conda", ver="1.0.0", nxt="1.0.1",
                  gate="Conda", kind="index leftover leftover leftover md5 vs sha256",
                  leftover="md5 leftover leftover leftover",
                  consumer="md5-lock", first="upload leftover leftover leftover md5 as sha256",
                  change="1.0.1 sha256 index", term="fail: md5-lock still 1.0.0",
                  err="anaconda leftover leftover leftover md5 only; want sha256",
                  wf="anaconda upload --no-progress  # leftover md5", tool="anaconda"),
    )
    add(
        ok_gate(slug="spack-spec-json-hash-vs-package-py", plant="albite-spack", ver="0.21.0", gate="Spack",
                kind="spec.json leftover leftover leftover hash vs package.py version", leftover="package.py version leftover leftover leftover",
                intended="spec.json dag hash", asset="dist/albite-package-py-ver.txt",
                first="reuse leftover leftover leftover package.py version as spec hash", change="lock spec.json dag hash",
                term="success; package.py version leftover leftover leftover",
                err="spack leftover leftover leftover package.py version ≠ spec.json hash",
                cfg='{\n  "spec": "dag_hash"\n}', tool="spack"),
        fail_gate(slug="spack-buildcache-index-vs-spec-cdash", plant="allactite-spack", ver="0.22.1", nxt="0.22.2",
                  gate="Spack", kind="buildcache leftover leftover leftover index.json vs CDash spec",
                  leftover="CDash spec leftover leftover leftover",
                  consumer="cdash-lock", first="push leftover leftover leftover CDash spec as buildcache index",
                  change="0.22.2 buildcache index.json", term="fail: cdash-lock still 0.22.1",
                  err="spack leftover leftover leftover CDash spec; want buildcache index",
                  wf="spack buildcache create --cdash leftover", tool="spack"),
    )
    return extra


PAIRS = _pairs()


def emit(round_n: int):
    if round_n < CATALOG_FIRST:
        raise SystemExit(f"round {round_n} below catalog {CATALOG_FIRST}")
    idx = (round_n - CATALOG_FIRST) % len(PAIRS)
    ok_kind, ok_spec, fail_kind, fail_spec = PAIRS[idx]
    ok_ep = BUILDERS[ok_kind](round_n, ok_spec)
    fail_ep = BUILDERS[fail_kind](round_n, fail_spec)
    banned_text(ok_ep)
    banned_text(fail_ep)
    return ok_ep, fail_ep, notes_for(round_n, ok_spec, fail_spec)


def selfcheck() -> None:
    slugs, plants = [], []
    for i, (_, ok, _, fail) in enumerate(PAIRS):
        emit(CATALOG_FIRST + i)
        slugs += [ok["slug"], fail["slug"]]
        plants += [ok["plant"], fail["plant"]]
        if "crates-yank-vs" in ok["slug"] or "crates-yank-vs" in fail["slug"]:
            raise SystemExit("banned crates-yank-vs slug")
        if "homebrew-bottle-rebuild-vs" in ok["slug"] or "homebrew-bottle-rebuild-vs" in fail["slug"]:
            raise SystemExit("banned brew cartesian slug")
    if len(slugs) != len(set(slugs)) or len(plants) != len(set(plants)):
        raise SystemExit("dup slug or plant")
    print(json.dumps({"catalog_first": CATALOG_FIRST, "n_pairs": len(PAIRS), "last_round": CATALOG_FIRST + len(PAIRS) - 1}))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--round", type=int)
    parser.add_argument("--staging", type=Path)
    parser.add_argument("--selfcheck", action="store_true")
    args = parser.parse_args()
    if args.selfcheck:
        selfcheck()
        return 0
    if args.round is None or args.staging is None:
        raise SystemExit("need --round and --staging")
    ok_ep, fail_ep, notes = emit(args.round)
    args.staging.mkdir(parents=True, exist_ok=True)
    batch = args.staging / f"batch-r{args.round:02d}.jsonl"
    notes_path = args.staging / f"NOTES-r{args.round:02d}.md"
    with batch.open("w") as handle:
        handle.write(json.dumps(ok_ep, ensure_ascii=False) + "\n")
        handle.write(json.dumps(fail_ep, ensure_ascii=False) + "\n")
    notes_path.write_text(notes)
    print(json.dumps({"round": args.round, "ids": [ok_ep["id"], fail_ep["id"]], "steps": [len(ok_ep["steps"]), len(fail_ep["steps"])]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
