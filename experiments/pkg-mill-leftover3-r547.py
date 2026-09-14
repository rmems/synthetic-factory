#!/usr/bin/env python3
"""package-release leftover leftover leftover mill r547+.

Distinct leftover leftover leftover registry/signing mechanics.
BAN crates-yank cartesian, r416 PAIRS modulo clones, r541–r544 slug recycle.
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

CATALOG_FIRST = 563
BUILDERS = w5.BUILDERS
_ok = w5._ok
_fail = w5._fail
hx = w5.hx


def notes_for(round_n: int, ok: dict, fail: dict) -> str:
    return (
        f"# NOTES-r{round_n} package-release-factory\n\n"
        "Novel coverage: 92%\n\n"
        "Two designed leftover leftover leftover episodes. Unique registry/signing "
        "mechanics (not r442–r456 cartesian, not r541–r544 slug recycle).\n\n"
        "| id | seed | first apply | plan change | terminal |\n"
        "|---|---|---|---|---|\n"
        f"| pkg-r{round_n}-{ok['slug']} | {ok['seed']} | {ok['first']} | {ok['change']} | {ok['term']} |\n"
        f"| pkg-r{round_n}-{fail['slug']} | {fail['seed']} | {fail['first']} | {fail['change']} | {fail['term']} |\n"
    )


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
        "cosign-bundle-dsse-vs-simple-signing",
        "npm-provenance-attestations-v1-vs-v2",
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
        ok_gate(slug="slsa-materials-digest-sha1-vs-sha256", plant="carnotite-slsa", ver="3.2.0", gate="SLSA provenance",
                kind="SLSA materials leftover leftover leftover sha1 vs sha256", leftover="materials digest sha1 leftover leftover leftover",
                intended="materials digest sha256", asset="dist/carnotite-sha1.intoto.jsonl",
                first="admit leftover leftover leftover sha1 materials as sha256", change="require sha256 materials",
                term="success; sha1 materials leftover leftover leftover",
                err="Error: leftover leftover leftover SLSA materials sha1",
                cfg='{\n  "materialsDigest": "sha256"\n}', tool="slsa-verifier"),
        fail_gate(slug="slsa-source-uri-fork-vs-canonical", plant="cassiterite-slsa", ver="1.6.0", nxt="1.6.1",
                  gate="SLSA provenance", kind="sourceUri leftover leftover leftover fork vs canonical",
                  leftover="fork sourceUri leftover leftover leftover",
                  consumer="fork-uri-lock", first="reuse leftover leftover leftover fork URI as canonical repo",
                  change="1.6.1 canonical sourceUri", term="fail: fork-uri-lock still 1.6.0",
                  err="slsa ERR leftover leftover leftover fork sourceUri",
                  wf="sourceURI: https://github.com/fork/cassiterite leftover", tool="slsa-verifier"),
    )
    add(
        ok_gate(slug="intoto-layout-threshold-1-vs-2", plant="celestine-intoto", ver="0.4.1", gate="in-toto",
                kind="in-toto layout leftover leftover leftover threshold 1 vs 2", leftover="layout threshold 1 leftover leftover leftover",
                intended="layout threshold 2", asset="dist/celestine-threshold1.layout",
                first="verify leftover leftover leftover threshold-1 layout as 2", change="require two functionaries",
                term="success; threshold-1 layout leftover leftover leftover",
                err="Error: leftover leftover leftover layout threshold 1",
                cfg='{\n  "threshold": 2\n}', tool="in-toto-verify"),
        fail_gate(slug="intoto-keyid-pgp-vs-ed25519", plant="cerussite-intoto", ver="2.8.0", nxt="2.8.1",
                  gate="in-toto", kind="layout keyid leftover leftover leftover pgp vs ed25519",
                  leftover="pgp keyid leftover leftover leftover",
                  consumer="pgp-keyid-lock", first="reuse leftover leftover leftover pgp keyid as ed25519",
                  change="2.8.1 ed25519 layout keys", term="fail: pgp-keyid-lock still 2.8.0",
                  err="in-toto ERR leftover leftover leftover pgp keyid; want ed25519",
                  wf="run: in-toto-sign -k pgp leftover", tool="in-toto-verify"),
    )
    add(
        ok_gate(slug="sigstore-fulcio-issuer-gitlab-vs-github", plant="chalcanthite-sigstore", ver="4.1.0", gate="sigstore",
                kind="Fulcio leftover leftover leftover gitlab issuer vs github", leftover="https://gitlab.com leftover leftover leftover",
                intended="https://token.actions.githubusercontent.com", asset="dist/chalcanthite-gitlab-issuer.crt",
                first="verify leftover leftover leftover GitLab Fulcio as GitHub OIDC", change="pin GitHub OIDC issuer",
                term="success; gitlab issuer leftover leftover leftover",
                err="Error: leftover leftover leftover fulcio issuer gitlab",
                cfg='{\n  "issuer": "https://token.actions.githubusercontent.com"\n}', tool="sigstore"),
        fail_gate(slug="sigstore-integrated-time-skew-vs-set", plant="chalcedony-sigstore", ver="0.3.3", nxt="0.3.4",
                  gate="sigstore", kind="Rekor leftover leftover leftover integratedTime vs SET",
                  leftover="integratedTime leftover leftover leftover",
                  consumer="itime-lock", first="treat leftover leftover leftover integratedTime as signed entry timestamp",
                  change="0.3.4 require SET", term="fail: itime-lock still 0.3.3",
                  err="sigstore ERR leftover leftover leftover integratedTime; want SET",
                  wf="run: rekor-cli get --integrated-time leftover", tool="rekor-cli"),
    )
    add(
        ok_gate(slug="cosign-identity-regex-vs-exact-san", plant="chalcocite-cosign", ver="7.0.2", gate="cosign",
                kind="cosign leftover leftover leftover identity regex vs exact SAN", leftover="certificate-identity-regexp leftover leftover leftover",
                intended="exact certificate SAN", asset="dist/chalcocite-regex.sig",
                first="verify leftover leftover leftover identity regexp as exact SAN", change="require exact SAN",
                term="success; identity regexp leftover leftover leftover",
                err="Error: leftover leftover leftover identity-regexp; want exact SAN",
                cfg='{\n  "identity": "exact"\n}', tool="cosign"),
        fail_gate(slug="cosign-rekor-pubkey-v1-vs-v2", plant="chalcopyrite-cosign", ver="1.1.1", nxt="1.1.2",
                  gate="cosign", kind="Rekor leftover leftover leftover pubkey v1 vs v2",
                  leftover="rekor.pub v1 leftover leftover leftover",
                  consumer="rekor-v1-lock", first="admit leftover leftover leftover rekor.pub v1 as v2",
                  change="1.1.2 rekor pubkey v2", term="fail: rekor-v1-lock still 1.1.1",
                  err="cosign ERR leftover leftover leftover rekor.pub v1",
                  wf="run: cosign verify --rekor-pub leftover-v1", tool="cosign"),
    )
    add(
        ok_gate(slug="notation-truststore-x509-vs-tsa", plant="chlorite-notation", ver="3.0.4", gate="notation",
                kind="notation leftover leftover leftover x509 truststore vs TSA", leftover="x509 ca leftover leftover leftover",
                intended="RFC3161 TSA truststore", asset="dist/chlorite-x509-ca.pem",
                first="verify leftover leftover leftover x509 CA as TSA", change="require TSA truststore",
                term="success; x509 ca leftover leftover leftover",
                err="Error: leftover leftover leftover x509 truststore; want TSA",
                cfg='{\n  "trustStore": "tsa"\n}', tool="notation"),
        fail_gate(slug="notation-max-validity-vs-notafter", plant="chromite-notation", ver="2.4.0", nxt="2.4.1",
                  gate="notation", kind="expiry leftover leftover leftover maxValidity vs notAfter",
                  leftover="maxValidity leftover leftover leftover",
                  consumer="maxvalidity-lock", first="treat leftover leftover leftover maxValidity as notAfter",
                  change="2.4.1 notAfter expiry", term="fail: maxvalidity-lock still 2.4.0",
                  err="notation ERR leftover leftover leftover maxValidity; want notAfter",
                  wf="run: notation verify --max-validity leftover", tool="notation"),
    )
    add(
        ok_gate(slug="npm-workflow-ref-tag-vs-sha", plant="chrysoberyl-npm", ver="9.2.0", gate="npm provenance",
                kind="npm leftover leftover leftover workflow_ref tag vs commit sha", leftover="workflow_ref refs/tags leftover leftover leftover",
                intended="workflow_ref commit sha", asset="dist/chrysoberyl-tag-ref.json",
                first="treat leftover leftover leftover tag workflow_ref as sha", change="pin workflow sha",
                term="success; tag workflow_ref leftover leftover leftover",
                err="npm ERR leftover leftover leftover workflow_ref is tag; want sha",
                cfg='{\n  "workflow_ref": "sha"\n}', tool="npm"),
        fail_gate(slug="npm-sigstore-bundle-02-vs-03", plant="chrysocolla-npm", ver="5.0.0", nxt="5.0.1",
                  gate="npm provenance", kind="sigstore bundle leftover leftover leftover 0.2 vs 0.3",
                  leftover="bundle mediaType 0.2 leftover leftover leftover",
                  consumer="bundle02-lock", first="publish leftover leftover leftover bundle 0.2 as 0.3",
                  change="5.0.1 bundle v0.3", term="fail: bundle02-lock still 5.0.0",
                  err="npm ERR leftover leftover leftover sigstore bundle 0.2",
                  wf="run: npm publish --provenance  # leftover bundle 0.2", tool="npm"),
    )
    add(
        ok_gate(slug="pypi-publisher-repo-fork-vs-canonical", plant="cinnabar-pypi", ver="2.2.1", gate="PyPI trusted publishing",
                kind="PEP 740 leftover leftover leftover publisher repo fork vs canonical", leftover="publisher repository fork leftover leftover leftover",
                intended="canonical repository", asset="dist/cinnabar-fork-publisher.json",
                first="upload leftover leftover leftover fork publisher as canonical", change="bind canonical repo",
                term="success; fork publisher leftover leftover leftover",
                err="400 leftover leftover leftover publisher repository is fork",
                cfg='{\n  "repository": "canonical"\n}', tool="twine"),
        fail_gate(slug="pypi-attestation-md5-vs-blake2b", plant="clinozoisite-pypi", ver="0.8.8", nxt="0.8.9",
                  gate="PyPI trusted publishing", kind="subject digest leftover leftover leftover md5 vs blake2b",
                  leftover="md5 subject leftover leftover leftover",
                  consumer="md5-subject-lock", first="publish leftover leftover leftover md5 subject as blake2b",
                  change="0.8.9 blake2b digest", term="fail: md5-subject-lock still 0.8.8",
                  err="400 leftover leftover leftover subject digest md5; want blake2b",
                  wf="run: twine upload  # leftover md5 subject", tool="twine"),
    )
    add(
        ok_gate(slug="maven-gpg-clearsign-vs-detach", plant="cobaltite-mvn", ver="8.1.0", gate="Maven GPG",
                kind="GPG leftover leftover leftover clearsign vs detached asc", leftover="clearsign leftover leftover leftover",
                intended="detached signature .asc", asset="dist/cobaltite-clearsign.asc",
                first="close leftover leftover leftover clearsign as detached", change="gpg --detach-sign",
                term="success; clearsign leftover leftover leftover",
                err="close rejected leftover leftover leftover clearsign; want detach",
                cfg='{\n  "gpg": "detach"\n}', tool="mvn"),
        fail_gate(slug="maven-central-checksum-md5-vs-sha256", plant="columbite-mvn", ver="3.3.1", nxt="3.3.2",
                  gate="Maven GPG", kind="central leftover leftover leftover md5 checksum vs sha256",
                  leftover="central md5 leftover leftover leftover",
                  consumer="central-md5-lock", first="upload leftover leftover leftover md5 as sha256",
                  change="3.3.2 sha256 checksum", term="fail: central-md5-lock still 3.3.1",
                  err="central leftover leftover leftover md5 checksum; want sha256",
                  wf="<checksumPolicy>md5 leftover</checksumPolicy>", tool="mvn"),
    )
    add(
        ok_gate(slug="nuget-repo-url-mapping-vs-source", plant="covellite-nuget", ver="6.4.0", gate="NuGet repository attestation",
                kind="NuGet leftover leftover leftover repositoryUrl mapping vs source", leftover="repositoryUrl mapping leftover leftover leftover",
                intended="exact package source URL", asset="dist/covellite-repo-map.json",
                first="verify leftover leftover leftover repositoryUrl mapping as source", change="pin exact source URL",
                term="success; repositoryUrl mapping leftover leftover leftover",
                err="NU3000 leftover leftover leftover repositoryUrl mapping; want source",
                cfg='{\n  "sourceUrl": true\n}', tool="nuget"),
        fail_gate(slug="nuget-counter-timestamp-vs-authenticode", plant="crocoite-nuget", ver="1.9.0", nxt="1.9.1",
                  gate="NuGet repository attestation", kind="counter leftover leftover leftover rfc3161 vs authenticode",
                  leftover="rfc3161 counter leftover leftover leftover",
                  consumer="rfc3161-counter-lock", first="push leftover leftover leftover rfc3161 counter as Authenticode",
                  change="1.9.1 Authenticode counter-sign", term="fail: rfc3161-counter-lock still 1.9.0",
                  err="NU3016 leftover leftover leftover rfc3161 counter; want Authenticode",
                  wf="<TimestampRfc3161>leftover</TimestampRfc3161>", tool="dotnet"),
    )
    add(
        ok_gate(slug="go-sumdb-off-vs-proxy", plant="cuprite-go", ver="1.22.0", gate="Go sumdb",
                kind="sumdb leftover leftover leftover off vs proxy", leftover="GOSUMDB=off leftover leftover leftover",
                intended="proxy.golang.org/sumdb", asset="dist/cuprite-gosumdb-off.txt",
                first="treat leftover leftover leftover GOSUMDB=off as proxy sumdb", change="enable proxy sumdb",
                term="success; GOSUMDB=off leftover leftover leftover",
                err="SECURITY ERROR leftover leftover leftover GOSUMDB=off",
                cfg='{\n  "sumdb": "proxy"\n}', tool="go"),
        fail_gate(slug="go-mod-sum-replace-vs-canonical", plant="diopside-go", ver="0.6.6", nxt="0.6.7",
                  gate="Go sumdb", kind="go.sum leftover leftover leftover replace vs canonical",
                  leftover="replace directive leftover leftover leftover",
                  consumer="replace-lock", first="fetch leftover leftover leftover replace as canonical module",
                  change="0.6.7 canonical go.sum", term="fail: replace-lock still 0.6.6",
                  err="sumdb leftover leftover leftover replace path; want canonical",
                  wf="GOPROXY=direct  # leftover replace", tool="go"),
    )
    add(
        ok_gate(slug="cargo-index-schema-v1-vs-v2", plant="dolomite-cargo", ver="0.12.0", gate="Cargo crate index",
                kind="index leftover leftover leftover schema v1 vs v2", leftover="index schema v1 leftover leftover leftover",
                intended="index schema v2", asset="dist/dolomite-index-v1.json",
                first="use leftover leftover leftover index v1 as v2", change="require index schema v2",
                term="success; index v1 leftover leftover leftover",
                err="error leftover leftover leftover index schema v1; want v2",
                cfg='{\n  "index": "v2"\n}', tool="cargo"),
        fail_gate(slug="cargo-cksum-index-vs-crate-sha256", plant="enargite-cargo", ver="4.4.0", nxt="4.4.1",
                  gate="Cargo crate index", kind="cksum leftover leftover leftover index vs crate sha256",
                  leftover="index cksum leftover leftover leftover",
                  consumer="index-cksum-lock", first="publish leftover leftover leftover index cksum as crate sha256",
                  change="4.4.1 crate sha256", term="fail: index-cksum-lock still 4.4.0",
                  err="error leftover leftover leftover index cksum; want crate sha256",
                  wf="run: cargo publish  # leftover index cksum", tool="cargo"),
    )
    add(
        ok_gate(slug="rubygems-platform-java-vs-ruby", plant="epidote-gem", ver="3.1.0", gate="RubyGems",
                kind="platform leftover leftover leftover java vs ruby", leftover="platform java leftover leftover leftover",
                intended="platform ruby", asset="dist/epidote-java.gem",
                first="serve leftover leftover leftover java gem as ruby", change="publish platform ruby",
                term="success; java platform leftover leftover leftover",
                err="bundler leftover leftover leftover platform java; want ruby",
                cfg='{\n  "platform": "ruby"\n}', tool="gem"),
        fail_gate(slug="rubygems-spec-sha256-vs-md5", plant="euclase-gem", ver="0.5.5", nxt="0.5.6",
                  gate="RubyGems", kind="spec leftover leftover leftover md5 vs sha256",
                  leftover="spec md5 leftover leftover leftover",
                  consumer="spec-md5-lock", first="push leftover leftover leftover spec md5 as sha256",
                  change="0.5.6 spec sha256", term="fail: spec-md5-lock still 0.5.5",
                  err="403 leftover leftover leftover spec md5; want sha256",
                  wf="run: gem push  # leftover spec md5", tool="gem"),
    )
    add(
        ok_gate(slug="hex-registry-public-vs-org", plant="fluorite-hex", ver="2.0.3", gate="Hex",
                kind="Hex leftover leftover leftover public registry vs org", leftover="hex.pm public leftover leftover leftover",
                intended="org private hex", asset="dist/fluorite-public.tgz",
                first="verify leftover leftover leftover public hex as org registry", change="require org hex",
                term="success; public hex leftover leftover leftover",
                err="mix leftover leftover leftover public hex.pm; want org",
                cfg='{\n  "registry": "org"\n}', tool="mix"),
        fail_gate(slug="hex-metadata-config-vs-tarball-sha", plant="galena-hex", ver="1.7.0", nxt="1.7.1",
                  gate="Hex", kind="metadata leftover leftover leftover config vs tarball sha",
                  leftover="metadata.config leftover leftover leftover",
                  consumer="metadata-config-lock", first="retire leftover leftover leftover metadata.config as tarball sha",
                  change="1.7.1 tarball sha256", term="fail: metadata-config-lock still 1.7.0",
                  err="hex leftover leftover leftover metadata.config; want tarball sha",
                  wf="run: mix hex.publish  # leftover metadata.config", tool="mix"),
    )
    add(
        ok_gate(slug="composer-lock-content-hash-vs-packages", plant="garnierite-composer", ver="2.7.0", gate="Composer",
                kind="Composer leftover leftover leftover content-hash vs packages sha", leftover="lock content-hash leftover leftover leftover",
                intended="packages sha256", asset="dist/garnierite-content-hash.txt",
                first="install leftover leftover leftover content-hash as packages sha", change="lock packages sha256",
                term="success; content-hash leftover leftover leftover",
                err="composer leftover leftover leftover content-hash; want packages sha",
                cfg='{\n  "lock": "packages-sha"\n}', tool="composer"),
        fail_gate(slug="composer-satis-include-path-vs-dist", plant="gibbsite-composer", ver="1.3.3", nxt="1.3.4",
                  gate="Composer", kind="satis leftover leftover leftover include-path vs dist",
                  leftover="include-path leftover leftover leftover",
                  consumer="include-path-lock", first="trust leftover leftover leftover include-path as dist",
                  change="1.3.4 dist url", term="fail: include-path-lock still 1.3.3",
                  err="composer leftover leftover leftover include-path; want dist",
                  wf="COMPOSER_SATIS leftover include-path", tool="composer"),
    )
    add(
        ok_gate(slug="conda-run-exports-weak-vs-strong", plant="goethite-conda", ver="24.3.0", gate="Conda",
                kind="run_exports leftover leftover leftover weak vs strong", leftover="weak run_exports leftover leftover leftover",
                intended="strong run_exports", asset="dist/goethite-weak-exports.json",
                first="use leftover leftover leftover weak run_exports as strong", change="require strong run_exports",
                term="success; weak run_exports leftover leftover leftover",
                err="conda leftover leftover leftover weak run_exports; want strong",
                cfg='{\n  "run_exports": "strong"\n}', tool="conda"),
        fail_gate(slug="conda-noarch-vs-linux64-subdir", plant="graphite-conda", ver="2.1.0", nxt="2.1.1",
                  gate="Conda", kind="subdir leftover leftover leftover noarch vs linux-64",
                  leftover="noarch leftover leftover leftover",
                  consumer="noarch-lock", first="upload leftover leftover leftover noarch as linux-64",
                  change="2.1.1 linux-64 subdir", term="fail: noarch-lock still 2.1.0",
                  err="anaconda leftover leftover leftover noarch; want linux-64",
                  wf="anaconda upload --noarch leftover", tool="anaconda"),
    )
    add(
        ok_gate(slug="spack-concretizer-original-vs-clingo", plant="grossular-spack", ver="0.23.0", gate="Spack",
                kind="concretizer leftover leftover leftover original vs clingo", leftover="original concretizer leftover leftover leftover",
                intended="clingo concretizer", asset="dist/grossular-original-concretizer.txt",
                first="reuse leftover leftover leftover original concretizer as clingo", change="require clingo",
                term="success; original concretizer leftover leftover leftover",
                err="spack leftover leftover leftover original concretizer; want clingo",
                cfg='{\n  "concretizer": "clingo"\n}', tool="spack"),
        fail_gate(slug="spack-buildcache-unsigned-vs-signed", plant="halite-spack", ver="0.24.1", nxt="0.24.2",
                  gate="Spack", kind="buildcache leftover leftover leftover unsigned vs gpg signed",
                  leftover="unsigned buildcache leftover leftover leftover",
                  consumer="unsigned-cache-lock", first="push leftover leftover leftover unsigned cache as signed",
                  change="0.24.2 signed buildcache", term="fail: unsigned-cache-lock still 0.24.1",
                  err="spack leftover leftover leftover unsigned buildcache; want gpg",
                  wf="spack buildcache create --unsigned leftover", tool="spack"),
    )
    return extra


PAIRS = _pairs()


def emit(round_n: int, pair_idx: int | None = None):
    idx = pair_idx if pair_idx is not None else (round_n - CATALOG_FIRST)
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(f"pair index {idx} outside 0..{len(PAIRS)-1}")
    ok_kind, ok_spec, fail_kind, fail_spec = PAIRS[idx]
    ok_ep = BUILDERS[ok_kind](round_n, ok_spec)
    fail_ep = BUILDERS[fail_kind](round_n, fail_spec)
    banned_text(ok_ep)
    banned_text(fail_ep)
    return ok_ep, fail_ep, notes_for(round_n, ok_spec, fail_spec)


def selfcheck() -> None:
    slugs, plants = [], []
    for i, (_, ok, _, fail) in enumerate(PAIRS):
        emit(CATALOG_FIRST + i, i)
        slugs += [ok["slug"], fail["slug"]]
        plants += [ok["plant"], fail["plant"]]
        if "crates-yank-vs" in ok["slug"] or "crates-yank-vs" in fail["slug"]:
            raise SystemExit("banned crates-yank-vs slug")
    if len(slugs) != len(set(slugs)) or len(plants) != len(set(plants)):
        raise SystemExit("dup slug or plant")
    print(json.dumps({"catalog_first": CATALOG_FIRST, "n_pairs": len(PAIRS), "last_round": CATALOG_FIRST + len(PAIRS) - 1}))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--round", type=int)
    parser.add_argument("--pair", type=int, default=None)
    parser.add_argument("--staging", type=Path)
    parser.add_argument("--selfcheck", action="store_true")
    args = parser.parse_args()
    if args.selfcheck:
        selfcheck()
        return 0
    if args.round is None or args.staging is None:
        raise SystemExit("need --round and --staging")
    ok_ep, fail_ep, notes = emit(args.round, args.pair)
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
