#!/usr/bin/env python3
"""package-release leftover leftover leftover mill r514+ (16 registry/signing pairs).

BAN crates-yank cartesian, digest≠git-SHA, nix-fetchgit, nuget-snupkg, homebrew-bottle.
Families: SLSA, in-toto, sigstore, cosign, notation, npm, PyPI, Maven GPG,
Go sumdb, Cargo crate (not yank), RubyGems, Hex, Composer, Conda, Spack, NuGet catalog.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
DIR = ROOT / "outputs/raw/2026-08-19-agentic/package-release-factory"
TXN = ["python3", str(ROOT / "pipelines/round_txn.py")]
FACTORY = "package-release-factory"
GEN = "grok-4.6"
MAX_ROUNDS = 16
HERE = ROOT / "experiments"
_spec = importlib.util.spec_from_file_location(
    "pkg_mill_attest_wave5", HERE / "pkg-mill-attest-wave5.py"
)
w5 = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(w5)

BUILDERS = w5.BUILDERS
notes_for = w5.notes_for
_ok = w5._ok
_fail = w5._fail
hx = w5.hx
ok_cosign = w5.ok_cosign
fail_npm = w5.fail_npm
ok_pypi = w5.ok_pypi
fail_maven = w5.fail_maven


def _min(plant: str) -> str:
    return plant.split("-")[0]


def ok_gate(*, slug, plant, gate, ver, kind, leftover, intended, asset, first, change, term, err, cfg, cfg_path, sec_path, sec_obs, fix_path, gate_cmd, gate_obs, extra=None):
    mineral = _min(plant)
    return _ok(
        slug=slug, plant=plant, gate=gate, kind=kind,
        goal=f"Ship {plant} {ver}. leftover {leftover}; gate wants {intended}. Keep {ver}. Leave {asset} leftover. Do not rewrite the tag.",
        plan=f"{first}.",
        outcome=f"{leftover} is not {intended}. Plan change: {change}. Residual: {asset} leftover.",
        inspect_cmd=f"echo LEFT={leftover!r} WANT={intended!r}",
        inspect_obs=f"LEFT={leftover} WANT={intended}",
        cfg_path=cfg_path, cfg_obs=cfg + "\n",
        sec_path=sec_path, sec_obs=sec_obs + "\n",
        dump_cmd=f"echo GATE={gate!r} 2>&1 | tail -n 6", dump_obs=err,
        apply_cmd=f"echo try_leftover={leftover!r}",
        apply_obs=f"still mismatch: leftover {leftover} not {intended}",
        apply_refl=f"Apply failed. leftover {leftover} is not {intended}.",
        iso_cmd=f"echo LEFT={hx(slug+'-l',16)} INT={hx(slug+'-i',16)}",
        iso_obs=f"LEFT={hx(slug+'-l',16)} INT={hx(slug+'-i',16)}",
        id_cmd=f"echo FETCH={intended!r}", id_obs=f"FETCH={intended}",
        fix_path=fix_path,
        fix_contents=json.dumps({"intended": intended, "leave": asset}, indent=2) + "\n",
        gate_cmd=gate_cmd, gate_obs=gate_obs,
        pass_cmd=f"echo INTENDED={intended!r}", pass_obs=f"INTENDED={intended}",
        left_cmd=f"echo {asset}={hx(slug+'-l',12)}", left_obs=f"{asset}={hx(slug+'-l',12)}",
        doc_cmd=f"echo KEEP_{mineral.upper()}_NOTE=1", doc_obs=f"KEEP_{mineral.upper()}_NOTE=1",
        tag_cmd=f"git verify-tag v{ver} >/dev/null && echo signed_tag_ok", tag_obs="signed_tag_ok",
        cmt_cmd=f"git add {fix_path} && git commit -m '{intended}; leftover {asset}'",
        cmt_obs=f"[main {hx(slug+'-cmt',7)}] {intended}; leftover {asset}",
        res_cmd="echo GATE=ok NOTE=leftover", res_obs="GATE=ok NOTE=leftover",
        res_refl=f"{leftover} is not {intended}. Residual: {asset} leftover.",
        seed=f"{leftover} vs {intended}", first=first, change=change, term=term,
        extra_reward=extra,
    )


def fail_gate(*, slug, plant, gate, ver, nxt, kind, leftover, consumer, first, change, term, err, wf_path, wf, extra=None):
    mineral = _min(plant)
    return _fail(
        slug=slug, plant=plant, gate=gate, kind=kind,
        goal=f"{plant} {ver} leftover {leftover}. Ship {nxt} once. {consumer} still {ver}. Do not delete {ver}.",
        plan=f"{first}.",
        outcome=f"mutated {gate} is not a new pack. Residual: {consumer} {ver}. Ticket not closed.",
        inspect_cmd=f"echo KIND={leftover!r} VER={ver}",
        inspect_obs=f"KIND={leftover} VER={ver}",
        wf_path=wf_path, wf_obs=wf + "\n",
        why_cmd=f"echo WANT=correct_{gate} GOT={leftover!r}",
        why_obs=f"WANT=correct_{gate} GOT={leftover}",
        con_path=f"../{mineral}-app/lock.txt", con_obs=f"# {consumer} {ver} {leftover}\n",
        apply_cmd=f"echo rewrite_{leftover!r}",
        apply_obs=err,
        apply_refl=f"Apply failed. leftover {leftover} cannot be mutated after publish.",
        still_cmd=f"echo HTTP=200 VER={ver}", still_obs="HTTP/2 200",
        use_cmd=f"echo {consumer}={ver}_{leftover}", use_obs=f"{consumer}={ver}_{leftover}",
        fix_cmd=f"echo NEXT={nxt} PACK_ONCE=1", fix_obs=f"NEXT={nxt} PACK_ONCE=1",
        pub_cmd=f"echo publish {nxt} {gate}", pub_obs=f"published {plant} {nxt}",
        ver_cmd=f"echo PAIR_{nxt.replace('.','')}=match", ver_obs=f"PAIR_{nxt.replace('.','')}=match",
        tag_cmd=f"git tag -s v{nxt} -m '{nxt}'", tag_obs=f"tagged v{nxt}",
        still2_cmd=f"echo {consumer}={ver} STILL=1", still2_obs=f"{consumer}={ver} STILL=1",
        undo_cmd=f"echo skipped_delete_{ver.replace('.','')}=1", undo_obs=f"skipped_delete_{ver.replace('.','')}=1",
        split_cmd=f"echo NEW={nxt} {consumer}={ver}", split_obs=f"NEW={nxt} {consumer}={ver}",
        tix_cmd=f"echo TICKET={consumer}_still_{ver}", tix_obs=f"TICKET={consumer}_still_{ver}",
        res_cmd=f"echo NEW={nxt} {consumer}={ver}", res_obs=f"NEW={nxt} {consumer}={ver}",
        seed=f"{leftover} vs {nxt} {gate}", first=first, change=change, term=term,
        extra_reward=extra,
    )


def _pairs():
    extra = []

    def add(ok, fail):
        extra.append(("ok_attest", ok, "fail_leftover", fail))

    add(
        ok_gate(
            slug="slsa-builder-id-gha-hosted-vs-selfhosted",
            plant="almandine-slsa", ver="1.2.0", gate="SLSA provenance",
            kind="builder-id hosted leftover vs self-hosted",
            leftover="GHA hosted builder-id", intended="self-hosted builder-id",
            asset="notes/hosted-builder.txt",
            first="keep leftover hosted builder-id",
            change="predicate builder-id self-hosted runner",
            term="success; hosted builder-id leftover",
            err="SLSA verify: leftover builder-id hosted; policy wants self-hosted",
            cfg='builder.id: https://github.com/actions/runner',
            cfg_path="slsa/predicate.json",
            sec_path=".github/workflows/slsa.yml",
            sec_obs="uses: slsa-framework/slsa-github-generator@v1.9.0",
            fix_path="slsa/predicate.json",
            gate_cmd="slsa-verifier verify-artifact dist/almandine.tgz --source-uri github.com/almandine-designed/almandine-slsa",
            gate_obs="PASSED builder-id self-hosted",
            extra={"fods": 1},
        ),
        fail_gate(
            slug="slsa-source-uri-fork-vs-canonical",
            plant="andalusite-slsa", ver="0.4.1", nxt="0.4.2", gate="SLSA provenance",
            kind="source-uri fork leftover vs canonical repo",
            leftover="fork source-uri", consumer="fork-lock",
            first="attest leftover fork source-uri as canonical",
            change="0.4.2 canonical source-uri predicate",
            term="fail: fork-lock still 0.4.1",
            err="error: leftover source-uri is fork; cannot rewrite v0.4.1",
            wf_path="slsa/source.json",
            wf="source.uri: git+https://github.com/fork/andalusite-slsa",
        ),
    )
    add(
        ok_gate(
            slug="intoto-layout-expired-root-vs-live-keys",
            plant="anorthite-intoto", ver="2.0.3", gate="in-toto",
            kind="expired layout root leftover vs live keys",
            leftover="expired layout root", intended="live layout keys",
            asset="notes/expired-root.pem",
            first="keep leftover expired layout root",
            change="resign layout with live keys",
            term="success; expired root leftover",
            err="in-toto-verify: leftover expired layout root",
            cfg='{"_type": "layout", "expires": "2020-01-01T00:00:00Z"}',
            cfg_path="in-toto/root.layout",
            sec_path="in-toto/keyids.json",
            sec_obs='{"expired": "aabb"}',
            fix_path="in-toto/root.layout",
            gate_cmd="in-toto-verify --layout root.layout --layout-keys live.pub",
            gate_obs="PASS live layout keys",
            extra={"fods": 1},
        ),
        fail_gate(
            slug="intoto-link-stepname-mismatch-vs-layout",
            plant="apatite-intoto", ver="1.1.1", nxt="1.1.2", gate="in-toto",
            kind="link step-name leftover vs layout step",
            leftover="wrong link step-name", consumer="step-lock",
            first="reuse leftover link filename as layout step",
            change="1.1.2 matching step-name links",
            term="fail: step-lock still 1.1.1",
            err="error: leftover link step-name ≠ layout; refuse overwrite",
            wf_path="in-toto/package.link",
            wf='{"_type": "link", "name": "leftover-pack"}',
        ),
    )
    add(
        ok_gate(
            slug="sigstore-bundle-v01-dsse-vs-v02",
            plant="aragonite-sigstore", ver="3.3.0", gate="sigstore",
            kind="bundle v0.1 leftover vs v0.2",
            leftover="bundle mediaType v0.1", intended="bundle v0.2 DSSE",
            asset="dist/aragonite.v01.sigstore",
            first="verify leftover v0.1 bundle as v0.2",
            change="re-attest v0.2 bundle",
            term="success; v0.1 bundle leftover",
            err="cosign: leftover bundle v0.1; verifier wants v0.2",
            cfg='{"mediaType": "application/vnd.dev.sigstore.bundle+json;version=0.1"}',
            cfg_path="dist/aragonite.sigstore",
            sec_path="policy/sigstore.json",
            sec_obs='{"bundleVersion": "0.2"}',
            fix_path="dist/aragonite.sigstore",
            gate_cmd="cosign verify-blob --bundle dist/aragonite.sigstore dist/aragonite.tgz",
            gate_obs="Verified OK bundle v0.2 DSSE",
            extra={"fods": 1},
        ),
        fail_gate(
            slug="sigstore-rekor-uuid-logindex-vs-inclusion",
            plant="azurite-sigstore", ver="0.9.0", nxt="0.9.1", gate="sigstore",
            kind="Rekor UUID leftover vs inclusion proof",
            leftover="bare Rekor UUID", consumer="uuid-lock",
            first="treat leftover Rekor UUID as inclusion proof",
            change="0.9.1 inclusion proof bundle",
            term="fail: uuid-lock still 0.9.0",
            err="error: leftover Rekor UUID is not inclusion proof; immutable 0.9.0",
            wf_path="rekor/uuid.txt",
            wf="logIndex leftover UUID only",
        ),
    )
    add(
        ok_cosign(
            slug="cosign-attach-sbom-spdx-tag-vs-referrers",
            plant="baryte-oci", ver="4.1.4",
            kind="attach SBOM tag leftover vs referrers API",
            leftover=":sbom tag attach", intended="referrers API artifact",
            asset="dist/baryte-sbom-tag.oci",
            first="verify leftover :sbom tag as referrers subject",
            change="cosign attest referrers API",
            term="success; :sbom tag leftover",
            err="Error: leftover :sbom tag; policy wants referrers",
            policy='{\n  "referrers": true\n}',
            sign="run: cosign attach sbom --sbom leftover.spdx $IMAGE",
        ),
        fail_npm(
            slug="npm-provenance-packument-integrity-vs-tarball",
            plant="beryl-js", ver="2.4.0", nxt="2.4.1",
            kind="packument integrity leftover vs tarball digest",
            leftover="packument integrity leftover", consumer="packument-lock",
            first="publish leftover packument integrity as provenance subject",
            change="2.4.1 tarball digest OIDC",
            term="fail: packument-lock still 2.4.0",
            err="npm ERR! leftover packument integrity ≠ tarball; refuse replace",
            wf="run: npm publish --provenance\n# leftover packument integrity",
        ),
    )
    add(
        ok_gate(
            slug="notation-truststore-ca-expired-vs-policy",
            plant="biotite-notation", ver="1.0.7", gate="notation",
            kind="expired CA leftover vs trust policy",
            leftover="expired notation CA", intended="current truststore CA",
            asset="notes/expired-ca.crt",
            first="keep leftover expired notation CA",
            change="notation cert add current CA",
            term="success; expired CA leftover",
            err="notation verify: leftover expired CA; policy untrusted",
            cfg='{"trustPolicies": [{"name": "leftover-ca"}]}',
            cfg_path="notation/trustpolicy.json",
            sec_path="notation/truststore/x509/ca/leftover.crt",
            sec_obs="-----BEGIN CERTIFICATE-----\nLEFTOVER\n",
            fix_path="notation/trustpolicy.json",
            gate_cmd="notation verify ghcr.io/biotite-designed/biotite-notation:1.0.7",
            gate_obs="Signature verified current truststore CA",
            extra={"fods": 1},
        ),
        fail_gate(
            slug="notation-unsigned-referrer-vs-signed-oci",
            plant="bornite-notation", ver="0.3.3", nxt="0.3.4", gate="notation",
            kind="unsigned referrer leftover vs signed OCI",
            leftover="unsigned referrer", consumer="referrer-lock",
            first="push leftover unsigned referrer as signed",
            change="0.3.4 notation sign once",
            term="fail: referrer-lock still 0.3.3",
            err="error: leftover unsigned referrer; cannot overwrite 0.3.3",
            wf_path="notation/unsigned.json",
            wf='{"artifactType": "application/vnd.cncf.notary.signature", "signed": false}',
        ),
    )
    add(
        ok_pypi(
            slug="pypi-trusted-publisher-environment-prod-vs-staging",
            plant="brookite-py", ver="5.0.1",
            kind="staging environment leftover vs prod publisher",
            leftover="staging environment publisher", intended="production environment",
            asset="notes/staging-oidc.txt",
            first="upload leftover staging environment as prod",
            change="OIDC environment=production",
            term="success; staging publisher leftover",
            err="HTTPError: leftover staging environment; trusted publisher is production",
            wf="id-token: write\nenvironment: leftover-staging",
            old="4.9.9",
        ),
        fail_maven(
            slug="maven-gpg-subkey-expired-vs-primary",
            plant="calcite-mvn", ver="1.8.0", nxt="1.8.1",
            kind="expired GPG subkey leftover vs primary",
            leftover="expired GPG subkey", staging="calcite-1018",
            first="close leftover expired-subkey staging",
            change="1.8.1 primary key new staging",
            term="fail: BOM still calcite-1018",
            err="Failed to close: leftover expired GPG subkey; no usable .asc",
            pom="<gpg.keyname>EXPIRED-SUBKEY</gpg.keyname>",
        ),
    )
    add(
        ok_gate(
            slug="gosumdb-note-hash-vs-module-zip",
            plant="cassiterite-go", ver="0.7.2", gate="Go sumdb",
            kind="sumdb note leftover vs module zip hash",
            leftover="stale sumdb note", intended="module zip hash",
            asset="notes/sumdb-stale.txt",
            first="keep leftover stale sumdb note",
            change="GOSUMDB verify module zip",
            term="success; stale sumdb note leftover",
            err="SECURITY ERROR leftover sumdb note ≠ zip hash",
            cfg="cassiterite-go 0.7.2 h1:LEFTOVERNOTE",
            cfg_path="go.sum",
            sec_path="sumdb/notes.txt",
            sec_obs="note leftover vs zip",
            fix_path="go.sum",
            gate_cmd="GOSUMDB=sum.golang.org go mod download cassiterite-go@v0.7.2",
            gate_obs="verified module zip hash",
            extra={"fods": 1},
        ),
        fail_gate(
            slug="gosumdb-proxy-stale-tile-vs-sumdb",
            plant="celestine-go", ver="1.4.4", nxt="1.4.5", gate="Go sumdb",
            kind="GOPROXY stale tile leftover vs sumdb",
            leftover="stale GOPROXY tile", consumer="tile-lock",
            first="trust leftover GOPROXY tile over sumdb",
            change="1.4.5 sumdb-backed zip",
            term="fail: tile-lock still 1.4.4",
            err="error: leftover GOPROXY tile ≠ sumdb; refuse replace 1.4.4",
            wf_path="proxy/tile.bin",
            wf="stale GOPROXY tile leftover",
        ),
    )
    add(
        ok_gate(
            slug="cargo-crate-checksum-index-vs-tarball",
            plant="cerussite-crate", ver="2.2.2", gate="Cargo crate",
            kind="index checksum leftover vs crate tarball",
            leftover="sparse index checksum", intended="tarball sha256",
            asset="notes/index-cksum.txt",
            first="keep leftover sparse index checksum",
            change="publish tarball matching checksum",
            term="success; index checksum leftover",
            err="error: leftover sparse checksum ≠ tarball",
            cfg='{"name":"cerussite-crate","vers":"2.2.2","cksum":"LEFTOVER"}',
            cfg_path=".cargo/index.json",
            sec_path="Cargo.toml",
            sec_obs='[package]\nname = "cerussite-crate"\nversion = "2.2.2"',
            fix_path=".cargo/index.json",
            gate_cmd="cargo publish --dry-run --allow-dirty",
            gate_obs="checksum matches tarball sha256",
            extra={"fods": 1},
        ),
        fail_gate(
            slug="cargo-git-dep-rev-vs-crates-io-release",
            plant="chalcedony-crate", ver="0.6.0", nxt="0.6.1", gate="Cargo crate",
            kind="git rev leftover vs crates.io crate",
            leftover="git dep rev leftover", consumer="gitrev-lock",
            first="publish leftover git rev as crates.io 0.6.0",
            change="0.6.1 crates.io crate once",
            term="fail: gitrev-lock still 0.6.0",
            err="error: leftover git rev is not crates.io crate; refuse mutate 0.6.0",
            wf_path="Cargo.toml",
            wf='chalcedony-crate = { git = "https://example/chalcedony", rev = "leftover" }',
        ),
    )
    add(
        ok_gate(
            slug="rubygems-attestation-sigstore-vs-gem-bytes",
            plant="chrysoberyl-gem", ver="3.1.0", gate="RubyGems",
            kind="sigstore gem attestation leftover vs gem bytes",
            leftover="stale gem attestation", intended="gem bytes digest",
            asset="notes/stale-gem.sigstore",
            first="keep leftover stale gem attestation",
            change="gem push with live attestation",
            term="success; stale attestation leftover",
            err="ERROR: leftover gem attestation ≠ gem bytes",
            cfg="checksums.yaml.gz leftover attestation",
            cfg_path="pkg/chrysoberyl.gemspec",
            sec_path=".github/workflows/gem.yml",
            sec_obs="gem push --attest leftover",
            fix_path="pkg/chrysoberyl.gemspec",
            gate_cmd="gem push pkg/chrysoberyl-3.1.0.gem",
            gate_obs="Pushed gem with gem bytes digest attestation",
            extra={"fods": 1},
        ),
        fail_gate(
            slug="rubygems-platform-java-vs-ruby",
            plant="cinnabar-gem", ver="0.2.8", nxt="0.2.9", gate="RubyGems",
            kind="java platform leftover vs ruby gem",
            leftover="java platform gem", consumer="jruby-lock",
            first="overwrite leftover java gem as ruby",
            change="0.2.9 ruby platform gem",
            term="fail: jruby-lock still 0.2.8",
            err="error: leftover java platform gem immutable at 0.2.8",
            wf_path="pkg/cinnabar.gemspec",
            wf="s.platform = Gem::Platform::JAVA",
        ),
    )
    add(
        ok_gate(
            slug="hex-tarball-inner-checksum-vs-outer",
            plant="cordierite-hex", ver="1.5.5", gate="Hex",
            kind="outer tarball leftover vs inner checksum",
            leftover="outer tarball checksum", intended="inner VERSION checksum",
            asset="notes/outer-cksum.txt",
            first="keep leftover outer tarball checksum",
            change="mix hex.publish inner checksum",
            term="success; outer checksum leftover",
            err="Mix.Error leftover outer checksum ≠ inner VERSION",
            cfg=":checksum leftover-outer",
            cfg_path="mix.exs",
            sec_path="hex/metadata.config",
            sec_obs="{<<\"outer\">>, leftover}",
            fix_path="mix.exs",
            gate_cmd="mix hex.publish --yes",
            gate_obs="Published inner VERSION checksum",
            extra={"fods": 1},
        ),
        fail_gate(
            slug="hex-retired-package-vs-new-release",
            plant="corundum-hex", ver="0.8.1", nxt="0.8.2", gate="Hex",
            kind="retired package leftover vs new release",
            leftover="retired hex package", consumer="retired-lock",
            first="unretire leftover package in place",
            change="0.8.2 new hex release",
            term="fail: retired-lock still 0.8.1",
            err="error: leftover retired package cannot unretire 0.8.1",
            wf_path="hex/retire.json",
            wf='{"retired": true, "reason": "leftover"}',
        ),
    )
    add(
        ok_gate(
            slug="composer-dist-url-zipball-vs-source-ref",
            plant="dolomite-php", ver="4.4.0", gate="Composer",
            kind="dist zipball leftover vs source ref",
            leftover="stale dist zipball URL", intended="source git ref",
            asset="notes/zipball-url.txt",
            first="keep leftover dist zipball URL",
            change="composer.json source ref dist",
            term="success; zipball URL leftover",
            err="Composer\\Downloader leftover dist URL ≠ source ref",
            cfg='"dist": {"url": "https://leftover/zipball"}',
            cfg_path="composer.json",
            sec_path="composer.lock",
            sec_obs='"dist-url": "leftover"',
            fix_path="composer.json",
            gate_cmd="composer validate --strict",
            gate_obs="OK source git ref",
            extra={"fods": 1},
        ),
        fail_gate(
            slug="composer-packagist-abandoned-vs-replacement",
            plant="epidote-php", ver="1.0.0", nxt="1.0.1", gate="Composer",
            kind="abandoned leftover vs replacement package",
            leftover="abandoned packagist row", consumer="abandon-lock",
            first="reattach leftover abandoned as current",
            change="1.0.1 replacement package",
            term="fail: abandon-lock still 1.0.0",
            err="error: leftover abandoned package immutable 1.0.0",
            wf_path="composer.json",
            wf='"abandoned": "leftover/epidote"',
        ),
    )
    add(
        ok_gate(
            slug="conda-pkg-sha256-buildstring-vs-index",
            plant="fluorite-conda", ver="2.1.3", gate="Conda",
            kind="build string leftover vs index sha256",
            leftover="stale build string hash", intended="repodata sha256",
            asset="notes/buildstr.txt",
            first="keep leftover build string hash",
            change="conda index repodata sha256",
            term="success; build string leftover",
            err="CondaHTTPError leftover build string ≠ repodata sha256",
            cfg="build: py310_leftover\nsha256: LEFTOVER",
            cfg_path="meta.yaml",
            sec_path="conda-build/index.json",
            sec_obs='"sha256": "leftover"',
            fix_path="meta.yaml",
            gate_cmd="conda-build . --output",
            gate_obs="index sha256 matches tarball",
            extra={"fods": 1},
        ),
        fail_gate(
            slug="conda-noarch-vs-linux64-subdir",
            plant="galena-conda", ver="0.5.0", nxt="0.5.1", gate="Conda",
            kind="noarch leftover vs linux-64 subdir",
            leftover="noarch subdir leftover", consumer="noarch-lock",
            first="rewrite leftover noarch as linux-64 same version",
            change="0.5.1 linux-64 build",
            term="fail: noarch-lock still 0.5.0",
            err="error: leftover noarch package immutable at 0.5.0",
            wf_path="meta.yaml",
            wf="build:\n  noarch: python",
        ),
    )
    add(
        ok_gate(
            slug="spack-spec-dag-hash-vs-binary-cache",
            plant="halite-spack", ver="1.9.9", gate="Spack",
            kind="dag-hash leftover vs binary cache",
            leftover="stale spec dag-hash", intended="binary cache hash",
            asset="notes/dag-hash.txt",
            first="keep leftover stale dag-hash",
            change="spack buildcache create matching hash",
            term="success; dag-hash leftover",
            err="Error: leftover dag-hash ≠ binary cache",
            cfg="halite@1.9.9/leftoverdag",
            cfg_path="spack.yaml",
            sec_path="opt/spack/.spack/spec.json",
            sec_obs='"hash": "leftoverdag"',
            fix_path="spack.yaml",
            gate_cmd="spack buildcache list halite",
            gate_obs="binary cache hash matches",
            extra={"fods": 1},
        ),
        fail_gate(
            slug="spack-mirror-unsigned-vs-gpg",
            plant="ilmenite-spack", ver="0.1.4", nxt="0.1.5", gate="Spack",
            kind="unsigned mirror leftover vs gpg signed",
            leftover="unsigned buildcache", consumer="unsigned-lock",
            first="trust leftover unsigned mirror as signed",
            change="0.1.5 gpg-signed buildcache",
            term="fail: unsigned-lock still 0.1.4",
            err="error: leftover unsigned buildcache; refuse mutate 0.1.4",
            wf_path="spack/mirrors.yaml",
            wf="mirrors:\n  leftover: unsigned",
        ),
    )
    add(
        ok_gate(
            slug="nuget-catalog-leaf-vs-nupkg-hash",
            plant="jadeite-nupkg", ver="6.6.0", gate="NuGet catalog",
            kind="catalog leaf leftover vs nupkg hash",
            leftover="stale catalog leaf hash", intended="nupkg sha512",
            asset="notes/catalog-leaf.txt",
            first="keep leftover catalog leaf hash",
            change="push nupkg matching catalog sha512",
            term="success; catalog leaf leftover",
            err="error: leftover catalog leaf ≠ nupkg sha512",
            cfg='{"catalogEntry": "leftover-hash"}',
            cfg_path="nuget/catalog.json",
            sec_path="Directory.Build.props",
            sec_obs="<PackageVersion>6.6.0</PackageVersion>",
            fix_path="nuget/catalog.json",
            gate_cmd="dotnet nuget push dist/Jadeite.6.6.0.nupkg",
            gate_obs="catalog sha512 matches nupkg",
            extra={"fods": 1},
        ),
        fail_gate(
            slug="nuget-nuspec-id-case-vs-feed",
            plant="kyanite-nupkg", ver="2.0.0", nxt="2.0.1", gate="NuGet catalog",
            kind="nuspec id case leftover vs feed id",
            leftover="nuspec id case leftover", consumer="case-lock",
            first="replace leftover nuspec case in place",
            change="2.0.1 feed-id case pack once",
            term="fail: case-lock still 2.0.0",
            err="error: leftover nuspec id case immutable 2.0.0",
            wf_path="Kyanite.nuspec",
            wf="<id>KYANITE</id>",
        ),
    )
    add(
        ok_gate(
            slug="slsa-hermetic-false-vs-level3",
            plant="labradorite-slsa", ver="0.2.0", gate="SLSA provenance",
            kind="hermetic=false leftover vs L3",
            leftover="hermetic false leftover", intended="SLSA L3 hermetic",
            asset="notes/hermetic-false.json",
            first="keep leftover hermetic=false predicate",
            change="rebuild hermetic L3 provenance",
            term="success; hermetic=false leftover",
            err="SLSA: leftover hermetic=false; policy L3",
            cfg='"resolvedDependencies": "unhermetic"',
            cfg_path="slsa/l3.json",
            sec_path=".github/workflows/slsa.yml",
            sec_obs="hermetic: false leftover",
            fix_path="slsa/l3.json",
            gate_cmd="slsa-verifier verify-artifact dist/labradorite.tgz --source-uri github.com/labradorite-designed/labradorite-slsa",
            gate_obs="PASSED SLSA L3 hermetic",
            extra={"fods": 1},
        ),
        fail_gate(
            slug="intoto-materials-hash-vs-products",
            plant="malachite-intoto", ver="3.3.3", nxt="3.3.4", gate="in-toto",
            kind="materials hash leftover vs products",
            leftover="stale materials hash", consumer="materials-lock",
            first="rewrite leftover materials as products",
            change="3.3.4 matching products hash",
            term="fail: materials-lock still 3.3.3",
            err="error: leftover materials hash ≠ products; refuse 3.3.3",
            wf_path="in-toto/package.link",
            wf='{"materials": {"leftover": "stale"}}',
        ),
    )
    add(
        ok_cosign(
            slug="cosign-keyless-fulcio-email-vs-workflow",
            plant="natrolite-oci", ver="1.1.8",
            kind="Fulcio email leftover vs workflow identity",
            leftover="Fulcio email SAN leftover", intended="workflow certificate identity",
            asset="dist/natrolite-email.crt",
            first="verify leftover Fulcio email as workflow identity",
            change="cosign keyless workflow identity",
            term="success; email SAN leftover",
            err="Error: leftover Fulcio email SAN; policy wants workflow",
            policy='{\n  "certificate-identity": "https://github.com/natrolite-designed/natrolite-oci/.github/workflows/sign.yml@refs/tags/v1.1.8"\n}',
            sign="run: cosign sign --yes $IMAGE  # leftover email SAN",
        ),
        fail_npm(
            slug="npm-oidc-audience-npm-vs-sigstore",
            plant="obsidian-js", ver="0.0.9", nxt="0.1.0",
            kind="OIDC audience leftover vs npm provenance",
            leftover="audience sigstore leftover", consumer="aud-lock",
            first="publish leftover sigstore audience as npm provenance",
            change="0.1.0 npm audience OIDC",
            term="fail: aud-lock still 0.0.9",
            err="npm ERR! leftover OIDC audience sigstore; npm wants npm:registry",
            wf="id-token audience leftover-sigstore",
        ),
    )
    return extra


PAIRS = _pairs()


def hop_unreserved() -> Path | None:
    parent = DIR.parent
    for child in sorted(parent.iterdir()):
        if not child.is_dir() or child == DIR:
            continue
        if not (child / "batch-r01.jsonl").exists() and not list(child.glob("batch-r*.jsonl")):
            continue
        try:
            fr = _cmd(TXN + ["frontier", str(child)])
        except Exception:
            continue
        nxt = int(fr.get("next_round") or 0)
        if nxt and not (child / f"ROUND-r{nxt:02d}.reserved.json").exists():
            return child
    return None


def _cmd(argv: list[str]) -> dict:
    p = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr or p.stdout)
    text = p.stdout.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        line = text.splitlines()[-1]
        return json.loads(line)


def emit(round_n: int, idx: int):
    ok_kind, ok_spec, fail_kind, fail_spec = PAIRS[idx]
    ok_ep = BUILDERS[ok_kind](round_n, ok_spec)
    fail_ep = BUILDERS[fail_kind](round_n, fail_spec)
    w5.banned_text(ok_ep)
    w5.banned_text(fail_ep)
    blob = json.dumps([ok_ep, fail_ep]).lower()
    for phrase in (
        "crates-yank",
        "yank vs",
        "digest-vs-git",
        "nix-fetchgit",
        "nuget-snupkg",
        "homebrew-bottle",
        '"sim_or_real": "real"',
        "sir-",
        "dbc-",
    ):
        if phrase in blob:
            raise SystemExit(f"banned phrase: {phrase}")
    notes = notes_for(round_n, ok_spec, fail_spec)
    notes = notes.replace(
        "(sigstore/cosign, npm provenance, PyPI trusted publishing, Maven GPG, crates.io yank vs index, Homebrew bottle rebuild, Nix NAR hash vs src, NuGet snupkg)",
        "(SLSA, in-toto, sigstore, cosign, notation, npm provenance, PyPI trusted publishing, Maven GPG, Go sumdb, Cargo crate checksum, RubyGems, Hex, Composer, Conda, Spack, NuGet catalog). Not crates-yank, not nix-fetchgit, not nuget-snupkg.",
    )
    return ok_ep, fail_ep, notes


def write_round(staging: Path, batch_name: str, notes_name: str, rnd: int, idx: int) -> list[str]:
    ok_ep, fail_ep, notes = emit(rnd, idx)
    staging.mkdir(parents=True, exist_ok=True)
    batch = staging / batch_name
    npath = staging / notes_name
    with batch.open("w") as fh:
        fh.write(json.dumps(ok_ep, ensure_ascii=False) + "\n")
        fh.write(json.dumps(fail_ep, ensure_ascii=False) + "\n")
    npath.write_text(notes)
    return [ok_ep["id"], fail_ep["id"]]


def main() -> None:
    slugs = []
    for _, ok, _, fail in PAIRS:
        slugs += [ok["slug"], fail["slug"]]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("dup slugs")
    if len(PAIRS) != 16:
        raise SystemExit(f"need 16 pairs, have {len(PAIRS)}")
    published = []
    failed_round = None
    CATALOG_FIRST = 514
    fr = _cmd(TXN + ["frontier", str(DIR)])
    start = int(fr["next_round"])
    if (DIR / f"ROUND-r{start:02d}.reserved.json").exists():
        hop = hop_unreserved()
        print(f"reserved at {start}; hop {hop}", file=sys.stderr)
        raise SystemExit(2)
    target_end = CATALOG_FIRST + MAX_ROUNDS
    rnd = start
    while rnd < target_end:
        idx = rnd - CATALOG_FIRST
        if idx < 0 or idx >= len(PAIRS):
            print(f"idx {idx} out of catalog for round {rnd}; stop")
            break
        try:
            res = _cmd(TXN + ["reserve", str(DIR), "--round", str(rnd), "--expected", "2"])
        except RuntimeError as exc:
            failed_round = rnd
            print(f"reserve failed round {failed_round}: {exc}", file=sys.stderr)
            hop = hop_unreserved()
            print(f"hop {hop}", file=sys.stderr)
            break
        ids = write_round(Path(res["staging_dir"]), Path(res["batch_file"]).name, Path(res["notes_file"]).name, rnd, idx)
        _cmd(TXN + ["publish", str(DIR), "--round", str(rnd), "--token", res["token"]])
        published.append({"round": rnd, "ids": ids})
        print(json.dumps({"published": rnd, "ids": ids}))
        rnd += 1
        if len(published) >= MAX_ROUNDS:
            break
    print(json.dumps({"done": published, "failed_round": failed_round}, indent=2))


if __name__ == "__main__":
    main()
