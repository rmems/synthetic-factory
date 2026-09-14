#!/usr/bin/env python3
"""Unique mill: package-release-factory attestation wave-5 (r313+).

Do NOT share pkg-mill-r300.py (leftover-archive mill owns that path).
BAN r247–r312 mill slugs including r300–r304 attestation + r305–r312 leftover-archive.
BAN r299 nix-fetchurl-name-vs-nar-of-unpacked / nuget-snupkg-portable-pdb-guid-mismatch.
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
_spec = importlib.util.spec_from_file_location("pkg_mill_r247", HERE / "pkg-mill-r247.py")
base = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(base)

CATALOG_FIRST = 313
hx = base.hx
BUILDERS = base.BUILDERS
notes_for = base.notes_for
_ok = base._ok
_fail = base._fail


def banned_text(obj: dict) -> None:
    base.banned_text(obj)
    blob = json.dumps(obj).lower()
    for phrase in (
        "digest equals git sha",
        "digest=git sha",
        "lockfile yank twin",
        "reuse-downloaded-gpl-license",
        "cdx-metadata-supplier",
        "nix-fetchurl-name-vs-nar-of-unpacked",
        "nuget-snupkg-portable-pdb-guid-mismatch",
        '"sim_or_real": "real"',
    ):
        if phrase in blob:
            raise SystemExit(f"banned phrase present: {phrase}")


def _min(plant: str) -> str:
    return plant.split("-")[0]


def _org(plant: str) -> str:
    return _min(plant) + "-designed"


def ok_cosign(*, slug, plant, ver, kind, leftover, intended, asset, first, change, term, err, policy, sign):
    org = _org(plant)
    img = f"ghcr.io/{org}/{plant}:{ver}"
    digest = hx(slug + "-img", 64)
    return _ok(
        slug=slug, plant=plant, gate="cosign", kind=kind,
        goal=f"Ship {plant} {ver}. leftover {leftover}; admission wants {intended}. Keep signed {ver}. Leave {asset} leftover. Do not rewrite the tag.",
        plan=f"{first}.",
        outcome=f"{leftover} is not {intended}. Plan change: {change}. Residual: {asset} leftover.",
        inspect_cmd=f"echo LEFTOVER={leftover!r} WANT={intended!r}; crane digest {img}",
        inspect_obs=f"LEFTOVER={leftover} WANT={intended}\nsha256:{digest}",
        cfg_path=f"policy/{_min(plant)}-verify.json", cfg_obs=policy + "\n",
        sec_path=".github/workflows/sign.yml", sec_obs=sign + "\n",
        dump_cmd=f"cosign verify {img} 2>&1 | tail -n 6", dump_obs=err,
        apply_cmd=f"echo try_leftover={leftover!r} && cosign verify {img} 2>&1 | tail -n 6",
        apply_obs=f"DENY {err}", apply_refl=f"Apply failed. leftover {leftover} is not {intended}.",
        iso_cmd=f"echo HAVE={leftover!r} NEED={intended!r}", iso_obs=f"HAVE={leftover} NEED={intended}",
        id_cmd=f"echo CONSUMER=admission ASSET={asset}", id_obs=f"CONSUMER=admission ASSET={asset}",
        fix_path=f"policy/{_min(plant)}-verify.json",
        fix_contents=json.dumps({"intended": intended, "leave": asset}, indent=2) + "\n",
        gate_cmd=f"cosign verify {img} --certificate-identity https://github.com/{org}/{plant}/.github/workflows/sign.yml@refs/tags/v{ver} --certificate-oidc-issuer https://token.actions.githubusercontent.com 2>&1 | tail -n 5",
        gate_obs=f"Verified OK {intended}",
        pass_cmd=f"echo IMG={ver} INTENDED=ok", pass_obs=f"IMG={ver} INTENDED=ok",
        left_cmd=f"ls {asset} && echo ASSET=leftover", left_obs=f"{asset}\nASSET=leftover",
        doc_cmd=f"echo KEEP_{_min(plant).upper()}_ASSET=1", doc_obs=f"KEEP_{_min(plant).upper()}_ASSET=1",
        tag_cmd=f"git verify-tag v{ver} >/dev/null && echo signed_tag_ok", tag_obs="signed_tag_ok",
        cmt_cmd=f"git add policy/{_min(plant)}-verify.json && git commit -m '{intended}; leftover {asset}'",
        cmt_obs=f"[main {hx(slug + '-cmt', 7)}] {intended}; leftover {asset}",
        res_cmd="echo INTENDED=ok ASSET=leftover", res_obs="INTENDED=ok ASSET=leftover",
        res_refl=f"{leftover} is not {intended}. Residual: {asset} leftover.",
        seed=f"{leftover} vs {intended}", first=first, change=change, term=term,
    )


def fail_npm(*, slug, plant, ver, nxt, kind, leftover, consumer, first, change, term, err, wf):
    mineral = _min(plant)
    pkg = f"@{mineral}/core"
    return _fail(
        slug=slug, plant=plant, gate="npm provenance", kind=kind,
        goal=f"{plant} {ver} leftover {leftover} has no trusted provenance. Publish {nxt} with OIDC. {consumer} still {ver}. Do not unpublish {ver}.",
        plan=f"{first}.",
        outcome=f"{leftover} cannot attach provenance to {ver}. Residual: {consumer} {ver}. Ticket not closed.",
        inspect_cmd=f"npm view {pkg}@{ver} --json | python3 -c 'import json,sys; print(json.load(sys.stdin).get(\"dist\",{{}}).get(\"attestations\"))'",
        inspect_obs="None", wf_path=".github/workflows/npm.yml", wf_obs=wf + "\n",
        why_cmd=f"echo LEFTOVER={leftover!r} ATTEST=null", why_obs=f"LEFTOVER={leftover} ATTEST=null",
        con_path=f"../{mineral}-app/.npmrc", con_obs=f"# {consumer} pins {pkg}@{ver}\n",
        apply_cmd=f"echo try={leftover!r} && npm publish --access public --provenance 2>&1 | tail -n 6",
        apply_obs=err, apply_refl=f"Apply failed. leftover {leftover} is not trusted-publisher provenance.",
        still_cmd=f"npm view {pkg}@{ver} version", still_obs=ver,
        use_cmd=f"npm view {pkg} dist-tags --json", use_obs='{"latest":"%s"}' % ver,
        fix_cmd=f"echo NEXT={nxt} OIDC=1", fix_obs=f"NEXT={nxt} OIDC=1",
        pub_cmd=f"npm version {nxt} --no-git-tag-version && npm publish --access public --provenance 2>&1 | tail -n 5",
        pub_obs=f"+ {pkg}@{nxt}\nprovenance uploaded",
        ver_cmd=f"echo ATTEST_{nxt.replace('.', '')}=true", ver_obs=f"ATTEST_{nxt.replace('.', '')}=true",
        tag_cmd=f"git tag -s v{nxt} -m '{nxt}'", tag_obs=f"tagged v{nxt}",
        still2_cmd=f"echo CONSUMER={consumer} STILL={ver}", still2_obs=f"CONSUMER={consumer} STILL={ver}",
        undo_cmd=f"echo skipped_unpublish_{ver.replace('.', '')}=1", undo_obs=f"skipped_unpublish_{ver.replace('.', '')}=1",
        split_cmd=f"echo NEW={nxt}_oidc CONSUMER={ver}_{leftover}", split_obs=f"NEW={nxt}_oidc CONSUMER={ver}_{leftover}",
        tix_cmd=f"echo TICKET={consumer}_still_{ver}", tix_obs=f"TICKET={consumer}_still_{ver}",
        res_cmd=f"echo NEW={nxt} CONSUMER={ver}", res_obs=f"NEW={nxt} CONSUMER={ver}",
        seed=f"{leftover} vs OIDC provenance", first=first, change=change, term=term,
    )


def ok_pypi(*, slug, plant, ver, kind, leftover, intended, asset, first, change, term, err, wf, old):
    mineral = _min(plant)
    dist = f"dist/{mineral}_py-{ver}-py3-none-any.whl"
    return _ok(
        slug=slug, plant=plant, gate="PyPI trusted publishing", kind=kind,
        goal=f"Ship {plant} {ver}. leftover {leftover}; publisher wants {intended}. Keep {ver}. Leave {asset} leftover. Do not use a long-lived token as the fix.",
        plan=f"{first}.",
        outcome=f"{leftover} is not {intended}. Plan change: {change}. Residual: {asset} leftover.",
        inspect_cmd=f"echo ROW={leftover!r} LIVE={intended!r} OLD={old}",
        inspect_obs=f"ROW={leftover} LIVE={intended} OLD={old}",
        cfg_path=".github/workflows/pypi.yml", cfg_obs=wf + "\n",
        sec_path="pyproject.toml", sec_obs=f"[project]\nname = \"{mineral}-py\"\nversion = \"{ver}\"\n",
        dump_cmd=f"echo publisher={intended!r}", dump_obs=f"publisher={intended}",
        apply_cmd=f"python3 -m twine upload {dist} 2>&1 | tail -n 6",
        apply_obs=err, apply_refl=f"Apply failed. leftover {leftover} is not {intended}.",
        iso_cmd=f"echo NEED={intended!r} HAVE={leftover!r}", iso_obs=f"NEED={intended} HAVE={leftover}",
        id_cmd="echo ISSUER=https://token.actions.githubusercontent.com",
        id_obs="ISSUER=https://token.actions.githubusercontent.com",
        fix_path=f"docs/{mineral}-publisher.json",
        fix_contents=json.dumps({"workflow": "pypi.yml", "match": intended, "leave": asset}, indent=2) + "\n",
        gate_cmd=f"python3 -m twine upload {dist} 2>&1 | tail -n 5",
        gate_obs=f"Uploading {ver}\nAttestations uploaded {intended}",
        pass_cmd=f"echo PROV_{ver.replace('.', '')}=yes", pass_obs=f"PROV_{ver.replace('.', '')}=yes",
        left_cmd=f"echo {asset}=leftover OLD={old}", left_obs=f"{asset}=leftover OLD={old}",
        doc_cmd=f"echo KEEP_{old.replace('.', '')}=1", doc_obs=f"KEEP_{old.replace('.', '')}=1",
        tag_cmd=f"git tag -s v{ver} -m '{ver}' && echo signed_tag_ok", tag_obs="signed_tag_ok",
        cmt_cmd=f"git add docs/{mineral}-publisher.json && git commit -m 'publisher {intended}; leftover {asset}'",
        cmt_obs=f"[main {hx(slug + '-cmt', 7)}] publisher {intended}; leftover {asset}",
        res_cmd=f"echo REF={intended} ASSET=leftover", res_obs=f"REF={intended} ASSET=leftover",
        res_refl=f"{leftover} is not {intended}. Residual: {asset} leftover.",
        seed=f"{leftover} vs {intended}", first=first, change=change, term=term,
    )


def fail_maven(*, slug, plant, ver, nxt, kind, leftover, staging, first, change, term, err, pom):
    mineral = _min(plant)
    return _fail(
        slug=slug, plant=plant, gate="Maven GPG", kind=kind,
        goal=f"{plant} {ver} leftover {leftover}; staging {staging} unsigned. Sign {nxt}. BOM still {staging}. Do not promote {staging}.",
        plan=f"{first}.",
        outcome=f"staging {staging} never signed. Residual: BOM {staging}. Ticket not closed.",
        inspect_cmd=f"rg leftover pom.xml; echo STAGING={staging} KIND={leftover!r}",
        inspect_obs=f"{leftover}\nSTAGING={staging}",
        wf_path="pom.xml", wf_obs=pom + "\n",
        why_cmd=f"echo PORTAL=require_asc GOT={leftover!r}", why_obs=f"PORTAL=require_asc GOT={leftover}",
        con_path=f"../{mineral}-bom/pom.xml", con_obs=f"<{mineral}.staging>{staging}</{mineral}.staging>\n",
        apply_cmd=f"mvn nexus-staging:rc-close -DstagingRepositoryId={staging} 2>&1 | tail -n 6",
        apply_obs=err, apply_refl=f"Apply failed. leftover {leftover} means staging {staging} has no usable .asc.",
        still_cmd=f"echo STAGING_{staging}=unsigned", still_obs=f"STAGING_{staging}=unsigned",
        use_cmd=f"rg {staging} ../{mineral}-bom/pom.xml", use_obs=f"<{mineral}.staging>{staging}</{mineral}.staging>",
        fix_cmd=f"echo NEXT={nxt} NEW_STAGING=1", fix_obs=f"NEXT={nxt} NEW_STAGING=1",
        pub_cmd=f"sed -i 's/{ver}/{nxt}/' pom.xml && mvn -B -Prelease deploy 2>&1 | tail -n 5",
        pub_obs=f"Uploaded {mineral}-{nxt} signed",
        ver_cmd=f"gpg --verify {mineral}-mvn-{nxt}.jar.asc 2>&1 | tail -n 3", ver_obs="Good signature",
        tag_cmd=f"git tag -s v{nxt} -m '{nxt}'", tag_obs=f"tagged v{nxt}",
        still2_cmd=f"rg {staging} ../{mineral}-bom/pom.xml", still2_obs=f"<{mineral}.staging>{staging}</{mineral}.staging>",
        undo_cmd=f"echo skipped_promote_{staging}=1", undo_obs=f"skipped_promote_{staging}=1",
        split_cmd=f"echo NEW={nxt}_signed BOM={staging}_leftover", split_obs=f"NEW={nxt}_signed BOM={staging}_leftover",
        tix_cmd=f"echo TICKET=bom_still_{staging}", tix_obs=f"TICKET=bom_still_{staging}",
        res_cmd=f"echo NEW={nxt} BOM={staging}", res_obs=f"NEW={nxt} BOM={staging}",
        seed=f"{leftover} unsigned staging", first=first, change=change, term=term,
        extra_reward={"staging_leftover": 1},
    )


def ok_crates(*, slug, plant, ver, yanked, kind, leftover, intended, asset, first, change, term, err, pointer):
    crate = _min(plant) + "-crate"
    return _ok(
        slug=slug, plant=plant, gate="crates.io yank vs index", kind=kind,
        goal=f"Ship {crate} {ver} after yanking {yanked} on crates.io sparse. leftover {leftover} still {yanked}. Refresh to {intended}. Leave {asset} leftover. Do not treat Cargo.lock as the plant.",
        plan=f"{first}.",
        outcome=f"Unyank refused. Plan change: {change}. Residual: {asset} leftover.",
        inspect_cmd=f"curl -sS https://index.crates.io/{crate[:2]}/{crate[2:4]}/{crate} | tail -n 1; echo LEFTOVER={leftover}={yanked}",
        inspect_obs=f'{{\"vers\":\"{yanked}\",\"yanked\":true}}\nLEFTOVER={leftover}={yanked}',
        cfg_path=pointer, cfg_obs=f"{crate} v{yanked} leftover {leftover}\n",
        sec_path="Cargo.toml", sec_obs=f"[package]\nname = \"{crate}\"\nversion = \"{ver}\"\n",
        dump_cmd=f"echo SPARSE=yanked LEFTOVER={leftover}={yanked}", dump_obs=f"SPARSE=yanked LEFTOVER={leftover}={yanked}",
        apply_cmd=f"cargo yank --undo {crate}@{yanked} 2>&1 | tail -n 5",
        apply_obs=err, apply_refl=f"Apply failed. leftover {leftover} is not crates.io yank (and not a lock pin twin).",
        iso_cmd=f"echo LEFTOVER={yanked} SPARSE=yanked", iso_obs=f"LEFTOVER={yanked} SPARSE=yanked",
        id_cmd=f"echo CONSUMER={leftover}", id_obs=f"CONSUMER={leftover}",
        fix_path=f"docs/{_min(plant)}-advise.json",
        fix_contents=json.dumps({"next": ver, "leave": asset, "yanked": yanked}) + "\n",
        gate_cmd="cargo publish --allow-dirty 2>&1 | tail -n 4", gate_obs=f"Uploaded {crate} v{ver}",
        pass_cmd=f"echo CRATE_{ver.replace('.', '')}=ok", pass_obs=f"CRATE_{ver.replace('.', '')}=ok",
        left_cmd=f"cat {pointer}", left_obs=f"{crate} v{yanked} leftover {leftover}",
        doc_cmd=f"echo KEEP_{asset}=1", doc_obs=f"KEEP_{asset}=1",
        tag_cmd=f"git tag -s v{ver} -m '{ver}' && echo signed_tag_ok", tag_obs="signed_tag_ok",
        cmt_cmd=f"git add docs/{_min(plant)}-advise.json && git commit -m '{ver}; leftover {asset}'",
        cmt_obs=f"[main {hx(slug + '-cmt', 7)}] {ver}; leftover {asset}",
        res_cmd=f"echo NEW={ver} LEFTOVER={asset}", res_obs=f"NEW={ver} LEFTOVER={asset}",
        res_refl=f"{leftover} leftover is not yank. Residual: {asset} leftover.",
        seed=f"yank vs leftover {leftover}", first=first, change=change, term=term,
    )


def fail_brew(*, slug, plant, ver, kind, leftover, intended, consumer, first, change, term, err, formula):
    mineral = _min(plant)
    bottle = hx(slug + "-bot", 64)
    return _fail(
        slug=slug, plant=plant, gate="Homebrew bottle rebuild", kind=kind,
        goal=f"{plant} {ver} rebuilt {intended}; leftover formula still {leftover}. {consumer} still {leftover}. Do not retag the bottle.",
        plan=f"{first}.",
        outcome=f"audit {err}. Residual: {consumer} {leftover}. Ticket not closed.",
        inspect_cmd=f"rg cellar Formula/{mineral}.rb; echo POURED={intended!r} FORMULA={leftover!r}",
        inspect_obs=f"sha256 leftover {leftover} poured {intended}",
        wf_path=f"Formula/{mineral}.rb", wf_obs=formula.replace("BOTTLESHA", bottle) + "\n",
        why_cmd=f"echo POURED={intended!r} FORMULA={leftover!r}", why_obs=f"POURED={intended} FORMULA={leftover}",
        con_path=f"../{mineral}-selfhost/Brewfile", con_obs=f"brew \"{mineral}\"\n# {consumer} {leftover}\n",
        apply_cmd=f"brew audit --strict {mineral} 2>&1 | tail -n 6",
        apply_obs=err, apply_refl=f"Apply failed. leftover {leftover} is not {intended} bottle bytes.",
        still_cmd=f"echo {consumer}={leftover}", still_obs=f"{consumer}={leftover}",
        use_cmd=f"echo POUR={leftover} leftover", use_obs=f"POUR={leftover} leftover",
        fix_cmd=f"echo KEEP_{consumer}=1 SHIP_{intended.replace(' ', '_')}=1",
        fix_obs=f"KEEP_{consumer}=1 SHIP_{intended.replace(' ', '_')}=1",
        pub_cmd=f"brew bottle --rebuild --json {mineral} 2>&1 | tail -n 4", pub_obs=f"Bottling {intended}",
        ver_cmd=f"echo LOCAL_{intended.replace(' ', '_')}=ok", ver_obs=f"LOCAL_{intended.replace(' ', '_')}=ok",
        tag_cmd=f"git verify-tag v{ver} >/dev/null && echo signed_tag_ok", tag_obs="signed_tag_ok",
        still2_cmd=f"echo {consumer}={leftover} STILL=1", still2_obs=f"{consumer}={leftover} STILL=1",
        undo_cmd="echo skipped_retag_bottle=1", undo_obs="skipped_retag_bottle=1",
        split_cmd=f"echo LOCAL={intended} {consumer}={leftover}", split_obs=f"LOCAL={intended} {consumer}={leftover}",
        tix_cmd=f"echo TICKET={consumer}_still_{leftover.replace(' ', '_')}",
        tix_obs=f"TICKET={consumer}_still_{leftover.replace(' ', '_')}",
        res_cmd=f"echo LOCAL={intended} {consumer}={leftover}", res_obs=f"LOCAL={intended} {consumer}={leftover}",
        seed=f"{leftover} leftover vs {intended} bottle", first=first, change=change, term=term,
        extra_reward={"bottle_leftover": 1},
    )


def ok_nix(*, slug, plant, ver, kind, leftover, intended, asset, first, change, term, err, flake, fix):
    mineral = _min(plant)
    leftover_h = hx(slug + "-left", 52)
    nar_h = hx(slug + "-nar", 52)
    return _ok(
        slug=slug, plant=plant, gate="Nix NAR hash vs src", kind=kind,
        goal=f"Ship {plant} {ver}. leftover {leftover} hashed as {leftover_h[:12]}; FOD wants {intended}. Keep {intended}. Leave {asset} leftover.",
        plan=f"{first}.",
        outcome=f"FOD mismatch. Plan change: {change}. Residual: {asset} leftover.",
        inspect_cmd=f"rg fetch flake.nix; echo LEFT={leftover} NAR={intended}",
        inspect_obs=f"{leftover}\nLEFT={leftover_h[:12]} NAR={nar_h[:12]}",
        cfg_path="flake.nix", cfg_obs=flake.replace("LEFTHASH", leftover_h) + "\n",
        sec_path="flake.lock", sec_obs='{\n  "narHash": "sha256-' + leftover_h[:44] + '="\n}\n',
        dump_cmd="nix build 2>&1 | tail -n 6", dump_obs=err,
        apply_cmd="nix build --rebuild 2>&1 | tail -n 5",
        apply_obs=f"still mismatch: leftover {leftover} not {intended}",
        apply_refl=f"Apply failed. leftover {leftover} is not {intended}.",
        iso_cmd=f"echo LEFT={leftover_h[:16]} NAR={nar_h[:16]}", iso_obs=f"LEFT={leftover_h[:16]} NAR={nar_h[:16]}",
        id_cmd=f"echo FETCH={intended}", id_obs=f"FETCH={intended}",
        fix_path="flake.nix", fix_contents=fix.replace("NARHASH", nar_h) + "\n",
        gate_cmd="nix build --rebuild 2>&1 | tail -n 4", gate_obs=f"finished FOD {intended}",
        pass_cmd=f"echo NAR={intended}", pass_obs=f"NAR={intended}",
        left_cmd=f"echo {asset}={leftover_h[:12]}", left_obs=f"{asset}={leftover_h[:12]}",
        doc_cmd=f"echo KEEP_{mineral.upper()}_NOTE=1", doc_obs=f"KEEP_{mineral.upper()}_NOTE=1",
        tag_cmd=f"git verify-tag v{ver} >/dev/null && echo signed_tag_ok", tag_obs="signed_tag_ok",
        cmt_cmd=f"git add flake.nix && git commit -m '{intended}; leftover {asset}'",
        cmt_obs=f"[main {hx(slug + '-cmt', 7)}] {intended}; leftover {asset}",
        res_cmd="echo NAR=ok NOTE=leftover", res_obs="NAR=ok NOTE=leftover",
        res_refl=f"{leftover} is not {intended}. Residual: {asset} leftover.",
        seed=f"{leftover} vs {intended}", first=first, change=change, term=term,
        extra_reward={"fods": 1},
    )


def fail_nuget(*, slug, plant, ver, nxt, kind, leftover, consumer, first, change, term, err, props):
    mineral = _min(plant)
    pkg = mineral[0].upper() + mineral[1:]
    dll = hx(slug + "-dll", 16)
    pdb = hx(slug + "-pdb", 16)
    return _fail(
        slug=slug, plant=plant, gate="NuGet snupkg", kind=kind,
        goal=f"{plant} {ver} leftover snupkg {leftover} (dll {dll} vs pdb {pdb}). Pack {nxt} once. {consumer} still {ver}. Do not delete {ver}.",
        plan=f"{first}.",
        outcome=f"mutated snupkg is not a new pack. Residual: {consumer} {ver}. Ticket not closed.",
        inspect_cmd=f"echo NUPKG={dll} SNUPKG={pdb} KIND={leftover!r}",
        inspect_obs=f"NUPKG={dll} SNUPKG={pdb} KIND={leftover}",
        wf_path="Directory.Build.props", wf_obs=props + "\n",
        why_cmd=f"echo WANT=paired_snupkg GOT={leftover!r}", why_obs=f"WANT=paired_snupkg GOT={leftover}",
        con_path=f"../{mineral}-app/nuget.config", con_obs=f"<!-- {consumer} {ver} {leftover} -->\n",
        apply_cmd=f"echo rewrite_{leftover} && dotnet nuget push dist/{pkg}.{ver}.snupkg --source https://nuget.smbsrc.net/ 2>&1 | tail -n 5",
        apply_obs=err, apply_refl=f"Apply failed. leftover {leftover} cannot be mutated after publish.",
        still_cmd=f"curl -sSI https://www.nuget.org/api/v2/package/{pkg}/{ver} | rg -i HTTP", still_obs="HTTP/2 200",
        use_cmd=f"echo {consumer}={ver}_{leftover}", use_obs=f"{consumer}={ver}_{leftover}",
        fix_cmd=f"echo NEXT={nxt} PACK_ONCE=1", fix_obs=f"NEXT={nxt} PACK_ONCE=1",
        pub_cmd=f"dotnet pack -p:PackageVersion={nxt} && dotnet nuget push dist/{pkg}.{nxt}.nupkg && dotnet nuget push dist/{pkg}.{nxt}.snupkg --source https://nuget.smbsrc.net/",
        pub_obs="Your package was pushed.\nYour symbol package was pushed.",
        ver_cmd=f"echo PAIR_{nxt.replace('.', '')}=match", ver_obs=f"PAIR_{nxt.replace('.', '')}=match",
        tag_cmd=f"git tag -s v{nxt} -m '{nxt}'", tag_obs=f"tagged v{nxt}",
        still2_cmd=f"echo {consumer}={ver} STILL=1", still2_obs=f"{consumer}={ver} STILL=1",
        undo_cmd=f"echo skipped_delete_{ver.replace('.', '')}=1", undo_obs=f"skipped_delete_{ver.replace('.', '')}=1",
        split_cmd=f"echo NEW={nxt} {consumer}={ver}", split_obs=f"NEW={nxt} {consumer}={ver}",
        tix_cmd=f"echo TICKET={consumer}_still_{ver}_{leftover.replace(' ', '_')}",
        tix_obs=f"TICKET={consumer}_still_{ver}_{leftover.replace(' ', '_')}",
        res_cmd=f"echo NEW={nxt} {consumer}={ver}", res_obs=f"NEW={nxt} {consumer}={ver}",
        seed=f"{leftover} leftover vs paired snupkg", first=first, change=change, term=term,
        extra_reward={"snupkg_leftover": 1},
    )


def _pairs():
    extra = []

    def add(ok, fail):
        extra.append(("ok_attest", ok, "fail_leftover", fail))

    add(
        ok_pypi(slug="pypi-pep740-missing-dsse-envelope", plant="oligoclase-py", ver="3.3.1",
                kind="PEP 740 leftover without DSSE envelope", leftover="bare attestation JSON",
                intended="DSSE envelope pep740", asset="dist/oligoclase-3.3.0.bare.json",
                first="twine --attestations leftover bare JSON", change="pypi-attestations enable DSSE",
                term="success; 3.3.0 bare JSON leftover",
                err="400 PEP 740 requires DSSE; leftover bare JSON rejected",
                wf="run: pypi-attestations sign dist/*.whl", old="3.3.0"),
        fail_maven(slug="maven-gpg-expired-signing-subkey", plant="sphalerite-mvn", ver="4.0.0", nxt="4.0.1",
                   kind="expired signing subkey leftover", leftover="expired 2019 signing subkey",
                   staging="orgsphalerite-9", first="re-sign leftover staging with expired subkey",
                   change="4.0.1 new subkey; new staging", term="fail: BOM still orgsphalerite-9",
                   err="close rejected: leftover expired subkey; BAD signature",
                   pom="<signingKey>DEAD2019</signingKey><!-- leftover expired -->"),
    )
    add(
        ok_crates(slug="crates-yank-vs-cargo-vet-imports", plant="pyrope-crate", ver="2.0.1", yanked="2.0.0",
                  kind="cargo-vet imports leftover after yank", leftover="supply-chain/imports.lock audits",
                  intended="sparse yanked 2.0.0", asset="supply-chain/imports.lock",
                  first="unyank 2.0.0 so cargo-vet imports stay", change="2.0.1; leave imports.lock 2.0.0",
                  term="success; cargo-vet imports 2.0.0 leftover",
                  err="error: refuse unyank\ncargo-vet imports leftover still 2.0.0",
                  pointer="supply-chain/imports.lock"),
        fail_brew(slug="homebrew-bottle-root-url-custom-domain", plant="brochantite-brew", ver="1.5.5",
                  kind="custom root_url leftover vs ghcr bottle", leftover="https://bottles.leftover.example",
                  intended="ghcr.io homebrew bottle", consumer="mirrorhost",
                  first="rewrite ghcr bottle as custom root_url leftover",
                  change="ship ghcr; handoff mirrorhost", term="fail: mirrorhost still custom root_url",
                  err="* root_url leftover custom domain vs poured ghcr.io",
                  formula='bottle do\n  root_url "https://ghcr.io/v2/homebrew/core"\n  sha256 cellar: :any, sonoma: "BOTTLESHA"\nend'),
    )
    add(
        ok_nix(slug="nix-outputhashmode-flat-vs-recursive-nar", plant="hercynite-nix", ver="1.1.1",
               kind="outputHashMode flat leftover vs recursive NAR", leftover="outputHashMode = flat",
               intended="recursive NAR", asset="notes/flat-hash.txt",
               first="keep leftover flat hash so the FOD cache hits", change="outputHashMode recursive NAR",
               term="success; flat hash note leftover", err="hash mismatch flat leftover vs recursive NAR",
               flake='stdenv.mkDerivation { outputHashMode = "flat"; outputHash = "sha256-LEFTHASH="; }',
               fix='stdenv.mkDerivation { outputHashMode = "recursive"; outputHash = "sha256-NARHASH="; }'),
        fail_nuget(slug="nuget-snupkg-mvid-vs-dll", plant="torbernite-nupkg", ver="3.3.3", nxt="3.3.4",
                   kind="snupkg MVID leftover vs DLL MVID", leftover="MVID mismatch", consumer="windbg",
                   first="rewrite leftover snupkg MVID to match DLL", change="3.3.4 pack once",
                   term="fail: windbg still 3.3.3", err="error: 400 snupkg MVID leftover ≠ nupkg DLL MVID",
                   props="<Deterministic>false</Deterministic>\n<!-- leftover MVID split -->"),
    )
    add(
        ok_cosign(slug="cosign-key-pair-pem-vs-keyless-fulcio", plant="anglesite-oci", ver="0.9.3",
                  kind="cosign.key leftover vs keyless Fulcio", leftover="COSIGN_PRIVATE_KEY pem",
                  intended="keyless Fulcio identity", asset="cosign.key",
                  first="cosign verify --key leftover pem so policy matches",
                  change="keyless sign+verify Fulcio SAN", term="success; cosign.key leftover",
                  err="Error: policy wants Fulcio SAN; leftover key-pair pem",
                  policy='{\n  "keyless": true,\n  "identity": "https://github.com/anglesite-designed/anglesite-oci/"\n}',
                  sign="run: cosign sign --key env://COSIGN_PRIVATE_KEY --yes $IMAGE"),
        fail_npm(slug="npm-provenance-git-protocol-repository-url", plant="andalusite-js", ver="8.8.2", nxt="8.8.3",
                 kind="git:// repository leftover in provenance subject", leftover="repository.url git://github.com/...",
                 consumer="sbom-gate", first="publish leftover git:// URL with --provenance",
                 change="8.8.3 https repository URL + OIDC", term="fail: sbom-gate still git:// 8.8.2",
                 err="npm ERR! provenance subject repository leftover git:// not https",
                 wf='run: npm publish --provenance\n# leftover "repository": "git://github.com/andalusite-designed/andalusite-js.git"'),
    )
    add(
        ok_pypi(slug="pypi-pdm-publish-password-vs-oidc", plant="andesine-py", ver="0.7.7",
                kind="pdm publish password leftover vs OIDC", leftover="PDM_PUBLISH_PASSWORD token",
                intended="trusted publisher OIDC", asset="docs/pdm-password-0.7.6.note",
                first="pdm publish --password leftover so OIDC row is unused",
                change="pdm publish OIDC trusted publisher", term="success; 0.7.6 password note leftover",
                err="403 password leftover; project requires trusted publisher OIDC",
                wf="run: pdm publish\nenv:\n  PDM_PUBLISH_PASSWORD: ${{ secrets.PYPI }}", old="0.7.6"),
        fail_maven(slug="maven-gpg-useagent-false-batch", plant="chalcopyrite-mvn", ver="2.2.2", nxt="2.2.3",
                   kind="gpg.useAgent false leftover vs batch agent", leftover="gpg.useAgent=false",
                   staging="orgchalcopyrite-5", first="close leftover staging with useAgent false",
                   change="2.2.3 useAgent true; new staging", term="fail: BOM still orgchalcopyrite-5",
                   err="close rejected: useAgent false leftover; no agent socket .asc",
                   pom="<useAgent>false</useAgent><!-- leftover -->"),
    )
    add(
        ok_crates(slug="crates-yank-vs-lib-rs-mirror", plant="spessartine-crate", ver="1.4.4", yanked="1.4.3",
                  kind="lib.rs mirror leftover after yank", leftover="lib.rs crate page",
                  intended="crates.io sparse yanked", asset="docs/librs-1.4.3.html",
                  first="unyank so lib.rs mirror stays", change="1.4.4; leave lib.rs HTML",
                  term="success; lib.rs 1.4.3 leftover", err="error: refuse unyank\nlib.rs leftover still 1.4.3",
                  pointer="docs/librs-1.4.3.html"),
        fail_brew(slug="homebrew-on-linux-bottle-vs-macos-pour", plant="langite-brew", ver="0.8.8",
                  kind="linux bottle leftover vs macos pour", leftover="x86_64_linux bottle",
                  intended="arm64_sonoma bottle", consumer="macstadium",
                  first="pour leftover linux bottle on macOS runners",
                  change="rebuild sonoma bottle; handoff macstadium", term="fail: macstadium still linux bottle",
                  err="* poured x86_64_linux leftover on macOS; want arm64_sonoma",
                  formula='bottle do\n  sha256 cellar: :any_skip_relocation, x86_64_linux: "BOTTLESHA"\nend'),
    )
    add(
        ok_nix(slug="nix-flake-narhash-vs-unlocked-rev", plant="galaxite-nix", ver="5.0.0",
               kind="flake narHash leftover vs unlocked rev", leftover="unlocked rev without narHash",
               intended="locked narHash", asset="notes/unlocked-rev.txt",
               first="keep leftover unlocked rev so the flake.lock is untouched",
               change="lock narHash for the rev", term="success; unlocked note leftover",
               err="error: unlocked leftover rev; NAR hash required",
               flake='inputs.src = { url = "github:galaxite-designed/galaxite-nix"; flake = false; };',
               fix='{ narHash = "sha256-NARHASH="; }'),
        fail_nuget(slug="nuget-snupkg-pdb-checksum-age", plant="carnotite-nupkg", ver="9.1.0", nxt="9.1.1",
                   kind="snupkg PDB checksum age leftover vs DLL", leftover="stale PDB checksum",
                   consumer="vsdbg", first="re-push leftover snupkg after rewriting checksum age",
                   change="9.1.1 pack once", term="fail: vsdbg still 9.1.0",
                   err="error: 400 leftover PDB checksum age ≠ DLL CodeView",
                   props="<DebugType>portable</DebugType>\n<!-- leftover separate snupkg age -->"),
    )
    add(
        ok_cosign(slug="cosign-rekor-hashedrekord-vs-dsse-kind", plant="polybasite-oci", ver="4.0.1",
                  kind="Rekor hashedrekord leftover vs dsse kind", leftover="hashedrekord tlog kind",
                  intended="dsse intoto tlog kind", asset="dist/polybasite.hashedrekord.json",
                  first="verify leftover hashedrekord as if it were dsse",
                  change="attest dsse and verify kind=dsse", term="success; hashedrekord JSON leftover",
                  err="Error: tlog kind hashedrekord leftover; policy wants dsse",
                  policy='{\n  "rekorKind": "dsse"\n}',
                  sign="run: cosign sign --yes $IMAGE  # leftover hashedrekord"),
        fail_npm(slug="npm-provenance-access-restricted-vs-public", plant="kyanite-js", ver="2.3.0", nxt="2.3.1",
                 kind="restricted leftover vs public provenance", leftover="--access restricted",
                 consumer="public-cdn", first="publish leftover restricted with --provenance",
                 change="2.3.1 public OIDC provenance", term="fail: public-cdn still restricted 2.3.0",
                 err="npm ERR! 402 provenance public leftover access=restricted",
                 wf="run: npm publish --access restricted --provenance"),
    )
    add(
        ok_pypi(slug="pypi-project-normalize-underscore-hyphen", plant="labradorite-py", ver="6.6.0",
                kind="publisher project labradorite_py vs labradorite-py", leftover="project name labradorite_py",
                intended="normalized labradorite-py", asset="docs/underscore-6.5.9.note",
                first="twine token so leftover underscore name is accepted",
                change="register normalized hyphen project", term="success; 6.5.9 underscore note leftover",
                err="403 publisher project leftover labradorite_py; normalized labradorite-py",
                wf="run: twine upload dist/*", old="6.5.9"),
        fail_maven(slug="maven-gpg-central-user-token-without-asc", plant="pyrite-mvn", ver="0.3.3", nxt="0.3.4",
                   kind="central user token leftover without .asc", leftover="sonatype user token skip gpg",
                   staging="orgpyrite-2", first="portal upload leftover token-only bundle without .asc",
                   change="0.3.4 gpg plugin; new staging", term="fail: BOM still orgpyrite-2",
                   err="rejected: user token leftover bundle has no .asc",
                   pom="<!-- leftover skip gpg; central user token -->\n<skip>true</skip>"),
    )
    add(
        ok_crates(slug="crates-trusted-publishing-vs-api-token", plant="grossular-crate", ver="0.2.9", yanked="0.2.8",
                  kind="API token leftover vs crates trusted publishing", leftover="CRATES_IO_TOKEN",
                  intended="OIDC trusted publishing", asset="docs/token-0.2.8.note",
                  first="cargo publish leftover API token so OIDC row is unused",
                  change="0.2.9 OIDC trusted publishing; leave token note",
                  term="success; API token note leftover",
                  err="error: token leftover; crate requires trusted publishing OIDC",
                  pointer="docs/token-0.2.8.note"),
        fail_brew(slug="homebrew-pour-bottle-false-vs-rebuild", plant="posnjakite-brew", ver="2.0.0",
                  kind="pour_bottle? false leftover vs rebuilt bottle", leftover="pour_bottle? false",
                  intended="poured rebuilt bottle", consumer="ci-runners",
                  first="force leftover source build despite rebuilt bottle",
                  change="allow pour; handoff ci-runners", term="fail: ci-runners still pour_bottle false",
                  err="* pour_bottle? false leftover; rebuilt bottle unused",
                  formula="def pour_bottle?\n  false # leftover\nend\nbottle do\n  sha256 cellar: :any, sonoma: \"BOTTLESHA\"\nend"),
    )
    add(
        ok_nix(slug="nix-fetchcrate-vs-cargo-vendor-nar", plant="magnetite-nix", ver="1.9.9",
               kind="fetchCrate leftover vs cargo vendor NAR", leftover="fetchCrate crate tarball hash",
               intended="cargo vendor NAR", asset="notes/fetchcrate-gzip.txt",
               first="keep leftover fetchCrate hash so the crate tarball cache hits",
               change="cargoHash vendor NAR", term="success; fetchCrate note leftover",
               err="hash mismatch fetchCrate leftover vs cargo vendor NAR",
               flake='fetchCrate { sha256 = "sha256-LEFTHASH="; }',
               fix='rustPlatform.buildRustPackage { cargoHash = "sha256-NARHASH="; }'),
        fail_nuget(slug="nuget-snupkg-minclientversion-mismatch", plant="tyuyamunite-nupkg", ver="5.5.0", nxt="5.5.1",
                   kind="snupkg minClientVersion leftover vs nupkg", leftover="minClientVersion 2.12 vs 6.0",
                   consumer="old-vs", first="push leftover snupkg after rewriting minClientVersion",
                   change="5.5.1 pack once with matching minClientVersion", term="fail: old-vs still 5.5.0",
                   err="error: 400 snupkg minClientVersion leftover ≠ nupkg",
                   props="<minClientVersion>2.12</minClientVersion>\n<!-- leftover vs nupkg 6.0 -->"),
    )
    add(
        ok_cosign(slug="cosign-oci11-referrers-vs-tag-sig", plant="proustite-oci", ver="3.2.2",
                  kind="OCI 1.1 referrers leftover vs tag .sig", leftover="tag sha256-*.sig",
                  intended="OCI 1.1 referrers API", asset="notes/tag-sig.txt",
                  first="verify leftover tag-based .sig as if referrers existed",
                  change="cosign sign --registry-referrers", term="success; tag .sig note leftover",
                  err="Error: referrers empty; leftover tag-based .sig only",
                  policy='{\n  "ociReferrers": true\n}',
                  sign="run: cosign sign --yes $IMAGE  # leftover tag signature"),
        fail_npm(slug="npm-packument-attestations-404-mirror", plant="sillimanite-js", ver="0.5.5", nxt="0.5.6",
                 kind="packument attestations 404 leftover mirror", leftover="Artifactory packument without attestations URL",
                 consumer="corp-mirror", first="force leftover mirror packument to report provenance",
                 change="0.5.6 npmjs provenance; handoff mirror", term="fail: corp-mirror still 404 attestations",
                 err="npm ERR! 404 leftover mirror packument has no attestations",
                 wf="run: npm publish --provenance --registry https://npm.leftover.example/"),
    )
    add(
        ok_pypi(slug="pypi-maturin-publish-token-vs-oidc", plant="bytownite-py", ver="1.2.3",
                kind="maturin publish token leftover vs OIDC", leftover="MATURIN_PYPI_TOKEN",
                intended="trusted publisher OIDC", asset="docs/maturin-token-1.2.2.note",
                first="maturin publish leftover token so OIDC is unused", change="maturin publish OIDC",
                term="success; 1.2.2 token note leftover",
                err="403 token leftover; project requires trusted publisher",
                wf="run: maturin publish\nenv:\n  MATURIN_PYPI_TOKEN: ${{ secrets.PYPI }}", old="1.2.2"),
        fail_maven(slug="maven-gpg-keyring-v1-gpg-vs-kbx", plant="marcasite-mvn", ver="8.1.0", nxt="8.1.1",
                   kind="secring.gpg v1 leftover vs pubring.kbx", leftover="secring.gpg v1",
                   staging="orgmarcasite-11", first="sign leftover staging with secring.gpg v1",
                   change="8.1.1 kbx keyring; new staging", term="fail: BOM still orgmarcasite-11",
                   err="close rejected: leftover secring.gpg v1 unreadable by gpg 2.4",
                   pom="<gpgHome>${project.basedir}/.gnupg-v1</gpgHome><!-- leftover secring -->"),
    )
    add(
        ok_crates(slug="crates-yank-vs-cdn-edge-cache", plant="andradite-crate", ver="3.3.0", yanked="3.2.9",
                  kind="crates.io CDN edge leftover after yank", leftover="static.crates.io edge .crate",
                  intended="sparse yanked=true", asset="docs/cdn-3.2.9.note",
                  first="unyank so CDN edge stays hot", change="3.3.0; leave CDN note",
                  term="success; CDN 3.2.9 note leftover",
                  err="error: refuse unyank\nCDN edge leftover still 3.2.9", pointer="docs/cdn-3.2.9.note"),
        fail_brew(slug="homebrew-linux-only-rebuild-leftover", plant="antlerite-brew", ver="4.4.1",
                  kind="linux-only rebuild leftover vs macos bottle", leftover="linux bottle only",
                  intended="macos + linux bottles", consumer="mac-fleet",
                  first="advertise leftover linux bottle as macos",
                  change="rebuild macos bottle; handoff mac-fleet", term="fail: mac-fleet still linux-only",
                  err="* linux-only leftover rebuild; macos bottle missing",
                  formula='bottle do\n  sha256 cellar: :any_skip_relocation, x86_64_linux: "BOTTLESHA"\nend'),
    )
    add(
        ok_nix(slug="nix-prefetch-url-unpack-vs-nar", plant="chromite-nix", ver="2.4.0",
               kind="nix-prefetch-url --unpack leftover vs NAR", leftover="prefetch-url --unpack sha",
               intended="fetchzip NAR", asset="notes/prefetch-unpack.txt",
               first="keep leftover prefetch-url --unpack hash", change="fetchzip NAR",
               term="success; prefetch note leftover",
               err="hash mismatch prefetch-url --unpack leftover vs fetchzip NAR",
               flake='# leftover nix-prefetch-url --unpack\nfetchurl { sha256 = "sha256-LEFTHASH="; }',
               fix='fetchzip { sha256 = "sha256-NARHASH="; }'),
        fail_nuget(slug="nuget-snupkg-symbolpackageformat-none", plant="uraninite-nupkg", ver="1.0.1", nxt="1.0.2",
                   kind="SymbolPackageFormat none leftover vs snupkg", leftover="SymbolPackageFormat none",
                   consumer="symstore", first="push leftover nupkg as if it contained snupkg",
                   change="1.0.2 SymbolPackageFormat snupkg", term="fail: symstore still 1.0.1 none",
                   err="error: 400 leftover SymbolPackageFormat none; no snupkg",
                   props="<SymbolPackageFormat>none</SymbolPackageFormat>"),
    )
    add(
        ok_cosign(slug="cosign-fulcio-gitlab-issuer-vs-github", plant="pyrargyrite-oci", ver="5.5.0",
                  kind="Fulcio GitLab issuer leftover vs GitHub", leftover="https://gitlab.com OIDC issuer",
                  intended="https://token.actions.githubusercontent.com", asset="dist/gitlab-cert.pem",
                  first="verify leftover GitLab Fulcio cert against GitHub policy",
                  change="sign with GitHub OIDC issuer", term="success; GitLab cert leftover",
                  err="Error: issuer leftover gitlab.com; policy wants GitHub Actions",
                  policy='{\n  "oidcIssuer": "https://token.actions.githubusercontent.com"\n}',
                  sign="run: cosign sign --yes $IMAGE  # leftover gitlab oidc"),
        fail_npm(slug="npm-trusted-publisher-after-package-rename", plant="staurolite-js", ver="6.0.0", nxt="6.0.1",
                 kind="trusted publisher leftover old package name", leftover="publisher row @staurolite/legacy",
                 consumer="rename-lock", first="publish leftover @staurolite/core onto legacy publisher row",
                 change="6.0.1 new publisher row for @staurolite/core", term="fail: rename-lock still legacy 6.0.0",
                 err="npm ERR! 403 leftover publisher package @staurolite/legacy",
                 wf="run: npm publish --provenance\n# leftover name @staurolite/legacy"),
    )
    add(
        ok_pypi(slug="pypi-twine-attestations-empty-dir", plant="anorthite-py", ver="4.4.4",
                kind="twine --attestations empty dir leftover", leftover="--attestations dist/empty/",
                intended="PEP 740 sidecar attestations", asset="dist/empty/.keep",
                first="twine upload leftover empty attestations dir",
                change="generate PEP 740 sidecars then upload", term="success; empty dir leftover",
                err="400 leftover --attestations dir empty; PEP 740 required",
                wf="run: twine upload dist/*.whl --attestations dist/empty/", old="4.4.3"),
        fail_maven(slug="maven-gpg-plugin-1x-vs-3x-signing", plant="arsenopyrite-mvn", ver="7.7.0", nxt="7.7.1",
                   kind="maven-gpg-plugin 1.6 leftover vs 3.2", leftover="maven-gpg-plugin 1.6",
                   staging="orgarsenopyrite-4", first="close leftover staging signed by 1.6 plugin",
                   change="7.7.1 plugin 3.2; new staging", term="fail: BOM still orgarsenopyrite-4",
                   err="close rejected: leftover gpg-plugin 1.6 signatures SHA1",
                   pom="<artifactId>maven-gpg-plugin</artifactId><version>1.6</version>"),
    )
    add(
        ok_crates(slug="crates-yank-vs-cargo-binstall-index", plant="uvarovite-crate", ver="0.9.1", yanked="0.9.0",
                  kind="cargo-binstall index leftover after yank", leftover="cargo-binstall binary index",
                  intended="sparse yanked 0.9.0", asset="docs/binstall-0.9.0.json",
                  first="unyank so binstall index stays", change="0.9.1; leave binstall JSON",
                  term="success; binstall 0.9.0 leftover",
                  err="error: refuse unyank\nbinstall index leftover still 0.9.0",
                  pointer="docs/binstall-0.9.0.json"),
        fail_brew(slug="homebrew-bottle-json-root-url-mismatch", plant="chalcanthite-brew", ver="3.0.2",
                  kind="bottle JSON root_url leftover vs formula", leftover="bottle JSON root_url file://",
                  intended="ghcr root_url", consumer="json-mirror",
                  first="merge leftover file:// bottle JSON into formula",
                  change="rewrite JSON ghcr; handoff json-mirror", term="fail: json-mirror still file://",
                  err="* bottle JSON leftover file:// root_url vs formula ghcr",
                  formula='bottle do\n  root_url "https://ghcr.io/v2/homebrew/core"\n  sha256 cellar: :any, sonoma: "BOTTLESHA"\nend'),
    )
    add(
        ok_nix(slug="nix-fetchzip-striproot-vs-nar", plant="trevorite-nix", ver="0.1.8",
               kind="fetchzip stripRoot leftover vs NAR", leftover="stripRoot = false",
               intended="stripRoot NAR", asset="notes/striproot-false.txt",
               first="keep leftover stripRoot=false hash", change="stripRoot true NAR",
               term="success; stripRoot false note leftover",
               err="hash mismatch stripRoot=false leftover vs NAR stripped",
               flake='fetchzip { stripRoot = false; sha256 = "sha256-LEFTHASH="; }',
               fix='fetchzip { sha256 = "sha256-NARHASH="; }'),
        fail_nuget(slug="nuget-snupkg-includesymbols-false", plant="brannerite-nupkg", ver="2.8.0", nxt="2.8.1",
                   kind="IncludeSymbols false leftover vs snupkg", leftover="IncludeSymbols false",
                   consumer="appinsights", first="push leftover nupkg claiming snupkg exists",
                   change="2.8.1 IncludeSymbols true pack once", term="fail: appinsights still 2.8.0",
                   err="error: 404 leftover IncludeSymbols false; no snupkg",
                   props="<IncludeSymbols>false</IncludeSymbols>"),
    )
    add(
        ok_cosign(slug="cosign-attach-sbom-vs-predicate-attestation", plant="stephanite-oci", ver="1.1.9",
                  kind="cosign attach SBOM leftover vs predicate attestation", leftover="cosign attach sbom layer",
                  intended="in-toto predicate attestation", asset="dist/stephanite.spdx.json",
                  first="verify leftover attached SBOM as an in-toto predicate",
                  change="cosign attest -p slsaprovenance", term="success; SPDX layer leftover",
                  err="Error: leftover attach sbom is not a DSSE predicate",
                  policy='{\n  "predicateType": "https://slsa.dev/provenance/v1"\n}',
                  sign="run: cosign attach sbom --sbom dist/stephanite.spdx.json $IMAGE"),
        fail_npm(slug="npm-publish-from-dist-tgz-leftover", plant="cordierite-js", ver="3.9.0", nxt="3.9.1",
                 kind="publish dist tgz leftover vs pack+OIDC", leftover="npm publish dist/cordierite-3.9.0.tgz",
                 consumer="offline-mirror", first="attach provenance to leftover prebuilt tgz",
                 change="3.9.1 pack in OIDC job", term="fail: offline-mirror still 3.9.0 tgz",
                 err="npm ERR! leftover tgz subjectDigest ≠ OIDC pack",
                 wf="run: npm publish dist/cordierite-3.9.0.tgz --provenance"),
    )
    add(
        ok_pypi(slug="pypi-trusted-publisher-workflow-subdir", plant="microcline-py", ver="9.0.0",
                kind="publisher workflow_filename subdir leftover", leftover=".github/workflows/release/pypi.yml",
                intended=".github/workflows/pypi.yml", asset="docs/subdir-8.9.9.note",
                first="twine token so leftover subdir workflow_filename is ignored",
                change="register workflow pypi.yml at repo root workflows",
                term="success; 8.9.9 subdir note leftover",
                err="403 leftover workflow_filename release/pypi.yml; registered pypi.yml",
                wf="on:\n  push:\n    tags: [\"v*\"]", old="8.9.9"),
        fail_maven(slug="maven-gpg-allowweakdigest-leftover", plant="stannite-mvn", ver="5.1.1", nxt="5.1.2",
                   kind="allowWeakDigests leftover SHA1 .asc", leftover="allowWeakDigests true",
                   staging="orgstannite-8", first="close leftover SHA1 staging as if SHA256",
                   change="5.1.2 digest SHA256; new staging", term="fail: BOM still orgstannite-8",
                   err="close rejected: leftover allowWeakDigests SHA1 .asc",
                   pom="<allowWeakDigests>true</allowWeakDigests>"),
    )
    add(
        ok_crates(slug="crates-yank-vs-docsrs-rustdoc-json", plant="rhodolite-crate", ver="1.0.3", yanked="1.0.2",
                  kind="docs.rs rustdoc-json leftover after yank", leftover="docs.rs rustdoc.json 1.0.2",
                  intended="sparse yanked 1.0.2", asset="docs/rustdoc-1.0.2.json",
                  first="unyank so rustdoc JSON stays", change="1.0.3; leave rustdoc JSON",
                  term="success; rustdoc JSON 1.0.2 leftover",
                  err="error: refuse unyank\nrustdoc JSON leftover still 1.0.2",
                  pointer="docs/rustdoc-1.0.2.json"),
        fail_brew(slug="homebrew-bottle-tag-sequoia-vs-sonoma", plant="atacamite-brew", ver="6.6.6",
                  kind="arm64_sequoia leftover vs sonoma bottle", leftover="arm64_sequoia sha",
                  intended="arm64_sonoma bottle", consumer="sonoma-fleet",
                  first="pour leftover sequoia bottle on sonoma",
                  change="rebuild sonoma; handoff sonoma-fleet", term="fail: sonoma-fleet still sequoia tag",
                  err="* leftover arm64_sequoia sha vs poured sonoma",
                  formula='bottle do\n  sha256 cellar: :any, arm64_sequoia: "BOTTLESHA"\nend'),
    )
    add(
        ok_nix(slug="nix-builtins-fetchurl-vs-fetchzip-nar", plant="cuprospinel-nix", ver="3.3.9",
               kind="builtins.fetchurl leftover vs fetchzip NAR", leftover="builtins.fetchurl file hash",
               intended="fetchzip NAR", asset="notes/builtins-fetchurl.txt",
               first="keep leftover builtins.fetchurl hash", change="fetchzip NAR",
               term="success; builtins.fetchurl note leftover",
               err="hash mismatch builtins.fetchurl leftover vs fetchzip NAR",
               flake='src = builtins.fetchurl { sha256 = "LEFTHASH"; };',
               fix='fetchzip { sha256 = "sha256-NARHASH="; }'),
        fail_nuget(slug="nuget-snupkg-deterministic-mvid-off", plant="davidite-nupkg", ver="4.4.0", nxt="4.4.1",
                   kind="Deterministic false leftover MVID vs snupkg", leftover="Deterministic false",
                   consumer="sourcelink-ci", first="rewrite leftover snupkg MVID after non-deterministic pack",
                   change="4.4.1 Deterministic true pack once", term="fail: sourcelink-ci still 4.4.0",
                   err="error: 400 leftover non-deterministic MVID ≠ snupkg",
                   props="<Deterministic>false</Deterministic>"),
    )
    add(
        ok_cosign(slug="cosign-offline-bundle-missing-set", plant="acanthite-oci", ver="6.0.2",
                  kind="offline bundle leftover missing Rekor SET", leftover="bundle without signedEntryTimestamp",
                  intended="offline bundle with SET", asset="dist/acanthite.noset.bundle",
                  first="cosign verify --offline leftover bundle missing SET",
                  change="re-sign and download bundle with SET", term="success; noset bundle leftover",
                  err="Error: leftover bundle missing signedEntryTimestamp",
                  policy='{\n  "offline": true,\n  "requireSET": true\n}',
                  sign="run: cosign sign --yes --tlog-upload=false $IMAGE"),
        fail_npm(slug="npm-oidc-permissions-contents-without-id-token", plant="aquamarine-js", ver="1.6.0", nxt="1.6.1",
                 kind="permissions contents leftover without id-token", leftover="permissions: contents: write",
                 consumer="release-bot", first="publish leftover job without id-token: write",
                 change="1.6.1 id-token write + provenance", term="fail: release-bot still 1.6.0 no id-token",
                 err="npm ERR! OIDC leftover missing id-token permission",
                 wf="permissions:\n  contents: write\nrun: npm publish --provenance"),
    )
    add(
        ok_pypi(slug="pypi-warehouse-disable-attestations-flag", plant="sanidine-py", ver="2.9.0",
                kind="warehouse disable-attestations leftover", leftover="PYPI_DISABLE_ATTESTATIONS=1",
                intended="PEP 740 required", asset="docs/disable-2.8.9.note",
                first="upload leftover with attestations disabled",
                change="enable PEP 740; register publisher", term="success; disable note leftover",
                err="400 leftover PYPI_DISABLE_ATTESTATIONS; PEP 740 required",
                wf="env:\n  PYPI_DISABLE_ATTESTATIONS: \"1\"\nrun: twine upload dist/*", old="2.8.9"),
        fail_maven(slug="maven-gpg-sign-and-deploy-file-vs-plugin", plant="wolframite-mvn", ver="0.6.6", nxt="0.6.7",
                   kind="gpg:sign-and-deploy-file leftover vs plugin", leftover="gpg:sign-and-deploy-file",
                   staging="orgwolframite-1", first="re-close leftover staging deployed via sign-and-deploy-file",
                   change="0.6.7 maven-gpg-plugin; new staging", term="fail: BOM still orgwolframite-1",
                   err="close rejected: leftover sign-and-deploy-file missing checksums",
                   pom="<!-- leftover mvn gpg:sign-and-deploy-file -->"),
    )
    add(
        ok_crates(slug="crates-oidc-job-environment-vs-workflow", plant="demantoid-crate", ver="4.1.0", yanked="4.0.9",
                  kind="OIDC job environment leftover vs workflow", leftover="job environment production",
                  intended="workflow-level environment release", asset="docs/env-production.note",
                  first="cargo publish leftover job environment production",
                  change="4.1.0 environment release; leave production note",
                  term="success; production env note leftover",
                  err="error: leftover job environment production; publisher wants release",
                  pointer="docs/env-production.note"),
        fail_brew(slug="homebrew-bottle-domain-env-leftover", plant="paratacamite-brew", ver="1.3.3",
                  kind="HOMEBREW_BOTTLE_DOMAIN leftover vs ghcr", leftover="HOMEBREW_BOTTLE_DOMAIN https://bottles.internal",
                  intended="ghcr.io bottles", consumer="internal-domain",
                  first="pour leftover internal bottle domain as ghcr",
                  change="ship ghcr; handoff internal-domain", term="fail: internal-domain still custom domain",
                  err="* HOMEBREW_BOTTLE_DOMAIN leftover vs poured ghcr",
                  formula='bottle do\n  sha256 cellar: :any, sonoma: "BOTTLESHA"\nend'),
    )
    add(
        ok_nix(slug="nix-npmdepshash-vs-pnpm-nar", plant="magnesiochromite-nix", ver="8.0.0",
               kind="npmDepsHash leftover vs pnpm NAR", leftover="npmDepsHash of npm pack",
               intended="pnpm fetch NAR", asset="notes/npmdepshash.txt",
               first="keep leftover npmDepsHash so the npm FOD hits", change="pnpmDeps NAR",
               term="success; npmDepsHash note leftover",
               err="hash mismatch npmDepsHash leftover vs pnpm NAR",
               flake='buildNpmPackage { npmDepsHash = "sha256-LEFTHASH="; }',
               fix='pnpm.config.depsHash = "sha256-NARHASH=";'),
        fail_nuget(slug="nuget-snupkg-folder-package-type", plant="euxenite-nupkg", ver="0.2.2", nxt="0.2.3",
                   kind="snupkg leftover vs Folder package type", leftover="PackageType Folder",
                   consumer="vssdk", first="push leftover Folder package as snupkg",
                   change="0.2.3 NuGet package type + snupkg", term="fail: vssdk still 0.2.2 Folder",
                   err="error: 400 leftover PackageType Folder cannot pair snupkg",
                   props="<PackageType>Folder</PackageType>"),
    )
    add(
        ok_cosign(slug="cosign-fulcio-oidc-client-id-leftover", plant="argentite-oci", ver="2.8.8",
                  kind="Fulcio OIDC client-id leftover vs sigstore", leftover="client-id leftover-sigstore",
                  intended="sigstore client-id", asset="dist/client-id-leftover.pem",
                  first="verify leftover client-id cert against public good",
                  change="sign with default sigstore client-id", term="success; leftover client-id cert leftover",
                  err="Error: leftover Fulcio client-id; public good rejects",
                  policy='{\n  "oidcClientID": "sigstore"\n}',
                  sign="run: cosign sign --oidc-client-id leftover-sigstore --yes $IMAGE"),
        fail_npm(slug="npm-provenance-subject-integrity-sha1-vs-sha512", plant="morganite-js", ver="7.7.7", nxt="7.7.8",
                 kind="subject integrity sha1 leftover vs sha512", leftover="subjectDigest sha1",
                 consumer="integrity-gate", first="publish leftover sha1 subjectDigest as provenance",
                 change="7.7.8 sha512 provenance subject", term="fail: integrity-gate still sha1 7.7.7",
                 err="npm ERR! leftover subjectDigest sha1; registry wants sha512",
                 wf="run: npm publish --provenance\n# leftover integrity sha1"),
    )
    add(
        ok_pypi(slug="pypi-setuptools-scm-local-version-attestation", plant="anorthoclase-py", ver="1.0.0",
                kind="setuptools-scm +n local version leftover vs PEP 440", leftover="1.0.0+dirty local version",
                intended="PEP 440 1.0.0 attestation", asset="docs/dirty-local.note",
                first="attest leftover +dirty local version", change="clean 1.0.0 then PEP 740",
                term="success; dirty note leftover",
                err="400 leftover local version +dirty; PEP 440 attestation subject",
                wf="run: python -m build && twine upload dist/*", old="0.9.9"),
        fail_maven(slug="maven-gpg-digest-sha1-vs-sha256", plant="molybdenite-mvn", ver="3.0.3", nxt="3.0.4",
                   kind="gpg digest SHA1 leftover vs SHA256", leftover="digestName SHA1",
                   staging="orgmolybdenite-6", first="close leftover SHA1 .asc staging",
                   change="3.0.4 SHA256; new staging", term="fail: BOM still orgmolybdenite-6",
                   err="close rejected: leftover digestName SHA1", pom="<digestName>SHA1</digestName>"),
    )
    add(
        ok_crates(slug="crates-yank-vs-source-replacement-dir", plant="tsavorite-crate", ver="2.2.4", yanked="2.2.3",
                  kind="source replacement directory leftover after yank", leftover="[source.crates-io] replace-with directory",
                  intended="sparse yanked 2.2.3", asset="vendor-dir/tsavorite-crate-2.2.3",
                  first="unyank so directory replacement stays", change="2.2.4; leave vendor-dir copy",
                  term="success; vendor-dir 2.2.3 leftover",
                  err="error: refuse unyank\nvendor-dir leftover still 2.2.3",
                  pointer=".cargo/config.toml"),
        fail_brew(slug="homebrew-bottle-only-json-leftover", plant="clinoatacamite-brew", ver="0.0.9",
                  kind="brew bottle --only-json leftover vs tarball", leftover="--only-json without tarball",
                  intended="bottle tarball + json", consumer="bottle-cache",
                  first="publish leftover JSON as if the tarball existed",
                  change="rebuild tarball; handoff bottle-cache", term="fail: bottle-cache still JSON-only",
                  err="* leftover --only-json; bottle tarball missing",
                  formula='bottle do\n  sha256 cellar: :any, sonoma: "BOTTLESHA"\nend'),
    )
    add(
        ok_nix(slug="nix-fetchhex-vs-mix-nar", plant="zincochromite-nix", ver="0.5.1",
               kind="fetchHex leftover vs mix FOD NAR", leftover="fetchHex tarball hash",
               intended="mixFodDeps NAR", asset="notes/fetchhex.txt",
               first="keep leftover fetchHex hash", change="mixFodDeps NAR",
               term="success; fetchHex note leftover", err="hash mismatch fetchHex leftover vs mix NAR",
               flake='fetchHex { sha256 = "sha256-LEFTHASH="; }',
               fix='beamPackages.mixRelease { mixFodDeps = "sha256-NARHASH="; }'),
        fail_nuget(slug="nuget-snupkg-pdb-checksum-sha1-vs-sha256", plant="samarskite-nupkg", ver="8.8.0", nxt="8.8.1",
                   kind="PDB checksum SHA1 leftover vs SHA256", leftover="PdbChecksum SHA1",
                   consumer="symweb", first="rewrite leftover snupkg checksum to SHA256",
                   change="8.8.1 pack SHA256 checksums", term="fail: symweb still 8.8.0 SHA1",
                   err="error: 400 leftover PDB checksum SHA1 ≠ SHA256 DLL",
                   props="<PdbChecksum>SHA1</PdbChecksum>"),
    )
    add(
        ok_cosign(slug="cosign-policy-controller-cip-vs-kyverno", plant="cerargyrite-oci", ver="0.4.4",
                  kind="policy-controller CIP leftover vs Kyverno", leftover="ClusterImagePolicy keyless",
                  intended="Kyverno verifyImages", asset="policy/cip-leftover.yaml",
                  first="apply leftover CIP as if Kyverno would honor it",
                  change="Kyverno verifyImages match Fulcio SAN", term="success; CIP yaml leftover",
                  err="Error: leftover CIP not evaluated; Kyverno DENY",
                  policy="apiVersion: policy.sigstore.dev/v1beta1\nkind: ClusterImagePolicy",
                  sign="run: cosign sign --yes $IMAGE"),
        fail_npm(slug="npm-trusted-publisher-reusable-caller-not-callee", plant="heliodor-js", ver="5.2.0", nxt="5.2.1",
                 kind="trusted publisher leftover caller workflow vs callee", leftover="caller .github/workflows/release.yml",
                 consumer="reusable-lock", first="publish leftover from caller workflow filename",
                 change="5.2.1 publisher row = callee publish.yml", term="fail: reusable-lock still caller 5.2.0",
                 err="npm ERR! leftover workflow filename release.yml; registered publish.yml",
                 wf="jobs:\n  call:\n    uses: ./.github/workflows/publish.yml"),
    )
    add(
        ok_pypi(slug="pypi-oidc-subject-repo-transfer-pending", plant="orthoclase-py", ver="3.1.4",
                kind="OIDC subject leftover after repo transfer", leftover="sub old-org/orthoclase-py",
                intended="sub new-org/orthoclase-py", asset="docs/old-org-3.1.3.note",
                first="twine token so leftover old-org subject is ignored",
                change="register publisher on transferred repo", term="success; old-org note leftover",
                err="403 leftover OIDC sub old-org/orthoclase-py after transfer",
                wf="run: twine upload dist/*", old="3.1.3"),
        fail_maven(slug="maven-gpg-defaultkey-vs-signingkey", plant="bismuthinite-mvn", ver="9.9.0", nxt="9.9.1",
                   kind="defaultKey leftover vs signingKey fingerprint", leftover="defaultKey email",
                   staging="orgbismuthinite-14", first="close leftover staging signed by defaultKey email",
                   change="9.9.1 signingKey fingerprint; new staging", term="fail: BOM still orgbismuthinite-14",
                   err="close rejected: leftover defaultKey email ≠ required fingerprint",
                   pom="<defaultKey>rel@bismuthinite.example</defaultKey>"),
    )
    add(
        ok_crates(slug="crates-yank-vs-cargo-dist-github-artifact", plant="hessonite-crate", ver="0.8.0", yanked="0.7.9",
                  kind="cargo-dist GitHub artifact leftover after yank", leftover="cargo-dist GitHub Release zip",
                  intended="sparse yanked 0.7.9", asset="docs/dist-0.7.9.zip.note",
                  first="unyank so cargo-dist artifact stays", change="0.8.0; leave dist zip note",
                  term="success; cargo-dist 0.7.9 leftover",
                  err="error: refuse unyank\ncargo-dist artifact leftover still 0.7.9",
                  pointer="docs/dist-0.7.9.zip.note"),
        fail_brew(slug="homebrew-formula-bottle-sha-vs-rebuild-artifact", plant="botallackite-brew", ver="2.7.1",
                  kind="formula bottle sha leftover vs rebuild artifact", leftover="formula sha from previous rebuild",
                  intended="new rebuild artifact sha", consumer="bottle-tap",
                  first="keep leftover formula sha after rebuild",
                  change="write new sha; handoff bottle-tap", term="fail: bottle-tap still old sha",
                  err="* leftover formula bottle sha ≠ rebuilt artifact",
                  formula='bottle do\n  sha256 cellar: :any, sonoma: "BOTTLESHA"\nend'),
    )
    add(
        ok_nix(slug="nix-outputhashalgo-md5-vs-sha256-nar", plant="coulsonite-nix", ver="1.4.1",
               kind="outputHashAlgo md5 leftover vs sha256 NAR", leftover="outputHashAlgo md5",
               intended="sha256 NAR", asset="notes/md5-fod.txt",
               first="keep leftover md5 FOD so the cache hits", change="sha256 NAR",
               term="success; md5 note leftover", err="hash mismatch leftover md5 vs sha256 NAR",
               flake='stdenv.mkDerivation { outputHashAlgo = "md5"; outputHash = "LEFTHASH"; }',
               fix='stdenv.mkDerivation { outputHashAlgo = "sha256"; outputHash = "sha256-NARHASH="; }'),
        fail_nuget(slug="nuget-snupkg-sourcelink-gitlab-vs-github", plant="aeschynite-nupkg", ver="6.1.0", nxt="6.1.1",
                   kind="SourceLink GitLab leftover vs GitHub repo", leftover="SourceLink GitLab URL",
                   consumer="debugger-src", first="push leftover snupkg with GitLab SourceLink onto GitHub package",
                   change="6.1.1 GitHub SourceLink pack once", term="fail: debugger-src still 6.1.0 GitLab",
                   err="error: 400 leftover SourceLink GitLab ≠ nupkg GitHub RepositoryUrl",
                   props="<RepositoryUrl>https://gitlab.com/aeschynite/aeschynite</RepositoryUrl>"),
    )
    add(
        ok_cosign(slug="cosign-verify-offline-without-bundle", plant="xanthoconite-oci", ver="7.1.0",
                  kind="verify --offline leftover without bundle", leftover="--offline without --bundle",
                  intended="offline bundle path", asset="notes/offline-no-bundle.txt",
                  first="cosign verify --offline leftover without bundle file",
                  change="download bundle then --offline --bundle", term="success; no-bundle note leftover",
                  err="Error: leftover --offline requires --bundle",
                  policy='{\n  "offline": true\n}',
                  sign="run: cosign verify --offline $IMAGE"),
        fail_npm(slug="npm-pack-pack-destination-vs-provenance-cwd", plant="goshenite-js", ver="0.3.1", nxt="0.3.2",
                 kind="pack --pack-destination leftover vs provenance cwd", leftover="pack --pack-destination ./out",
                 consumer="artifact-store", first="publish leftover ./out tarball with provenance from cwd",
                 change="0.3.2 pack+publish same cwd OIDC", term="fail: artifact-store still out/ 0.3.1",
                 err="npm ERR! leftover pack-destination subjectDigest ≠ cwd pack",
                 wf="run: npm pack --pack-destination ./out && npm publish ./out/*.tgz --provenance"),
    )
    add(
        ok_pypi(slug="pypi-poetry-publish-repository-leftover", plant="hyalophane-py", ver="5.5.5",
                kind="poetry publish --repository leftover vs pypi OIDC", leftover="--repository leftover-pypi",
                intended="pypi.org trusted publisher", asset="docs/repo-5.5.4.note",
                first="poetry publish leftover --repository so OIDC is unused",
                change="poetry publish OIDC to pypi", term="success; 5.5.4 repository note leftover",
                err="403 leftover repository leftover-pypi; trusted publisher is pypi.org",
                wf="run: poetry publish --repository leftover-pypi", old="5.5.4"),
        fail_maven(slug="maven-gpg-skip-pom-signing-leftover", plant="gersdorffite-mvn", ver="2.4.4", nxt="2.4.5",
                   kind="skip pom .asc leftover vs required pom signature", leftover="gpg.skipPom=true",
                   staging="orggersdorffite-7", first="close leftover staging without pom.asc",
                   change="2.4.5 sign pom; new staging", term="fail: BOM still orggersdorffite-7",
                   err="close rejected: leftover skip pom signing; pom.asc missing",
                   pom="<skipPom>true</skipPom>"),
    )
    add(
        ok_crates(slug="crates-sparse-index-etag-vs-yank", plant="hydrogrossular-crate", ver="1.7.0", yanked="1.6.9",
                  kind="sparse index ETag leftover after yank", leftover="If-None-Match ETag 1.6.9",
                  intended="sparse yanked 1.6.9", asset="docs/etag-1.6.9.note",
                  first="unyank so leftover ETag 304 stays", change="1.7.0; leave ETag note",
                  term="success; ETag 1.6.9 leftover",
                  err="error: refuse unyank\nsparse ETag leftover still 1.6.9",
                  pointer="docs/etag-1.6.9.note"),
        fail_brew(slug="homebrew-audit-bottle-leftover-vs-rebuilt-sha", plant="connellite-brew", ver="8.1.8",
                  kind="brew audit --bottle leftover vs rebuilt sha", leftover="audit cached bottle sha",
                  intended="rebuilt bottle sha", consumer="audit-bot",
                  first="pass leftover audit cache as rebuilt sha",
                  change="rebuild and refresh audit; handoff audit-bot", term="fail: audit-bot still cached sha",
                  err="* leftover audit --bottle sha ≠ rebuilt artifact",
                  formula='bottle do\n  sha256 cellar: :any, sonoma: "BOTTLESHA"\nend'),
    )
    add(
        ok_nix(slug="nix-fetchtarball-vs-fetchzip-nar", plant="vuorelainenite-nix", ver="4.2.0",
               kind="fetchTarball leftover vs fetchzip NAR", leftover="fetchTarball unpacked hash",
               intended="fetchzip NAR", asset="notes/fetchtarball.txt",
               first="keep leftover fetchTarball hash", change="fetchzip NAR",
               term="success; fetchTarball note leftover",
               err="hash mismatch fetchTarball leftover vs fetchzip NAR",
               flake='src = fetchTarball { sha256 = "LEFTHASH"; };',
               fix='fetchzip { sha256 = "sha256-NARHASH="; }'),
        fail_nuget(slug="nuget-snupkg-packageid-case-mismatch", plant="pyrochlore-nupkg", ver="3.0.9", nxt="3.1.0",
                   kind="snupkg PackageId case leftover vs nupkg", leftover="PackageId pyrochlore vs Pyrochlore",
                   consumer="nuget-org", first="push leftover snupkg with lowercase PackageId",
                   change="3.1.0 matching PackageId pack once", term="fail: nuget-org still 3.0.9 case split",
                   err="error: 400 leftover snupkg PackageId pyrochlore ≠ Pyrochlore",
                   props="<PackageId>pyrochlore</PackageId>"),
    )
    add(
        ok_cosign(slug="cosign-rekor-logindex-vs-uuid-lookup", plant="miargyrite-oci", ver="3.3.7",
                  kind="Rekor logIndex leftover vs UUID lookup", leftover="REKOR_LOG_INDEX integer",
                  intended="Rekor UUID lookup", asset="notes/logindex.txt",
                  first="verify leftover logIndex against a UUID policy",
                  change="record UUID; verify by UUID", term="success; logIndex note leftover",
                  err="Error: leftover logIndex not accepted; policy stores UUID",
                  policy='{\n  "rekorLookup": "uuid"\n}',
                  sign="run: cosign sign --yes $IMAGE\n# leftover print logIndex"),
        fail_npm(slug="npm-version-from-git-tag-vs-package-json", plant="bixbite-js", ver="2.0.8", nxt="2.0.9",
                 kind="git tag version leftover vs package.json provenance subject",
                 leftover="git tag v2.0.8 vs package.json 2.0.7", consumer="semver-lock",
                 first="publish leftover tag version with mismatched package.json",
                 change="2.0.9 package.json matches tag + OIDC", term="fail: semver-lock still mismatched 2.0.8",
                 err="npm ERR! leftover git tag subject ≠ package.json version",
                 wf="run: npm publish --provenance\n# leftover package.json version 2.0.7 tag v2.0.8"),
    )
    add(
        ok_pypi(slug="pypi-attestations-slsa-predicate-vs-pypi-v1", plant="celsian-py", ver="0.8.1",
                kind="SLSA predicate leftover vs pypi-publish-v1", leftover="SLSA provenance predicate",
                intended="pypi://publish/v1 attestation", asset="dist/celsian.slsa.json",
                first="upload leftover SLSA predicate as PEP 740",
                change="pypi-attestations pypi-publish-v1", term="success; SLSA json leftover",
                err="400 leftover SLSA predicate; want pypi publish v1",
                wf="run: gh attestation download --predicate-type slsa", old="0.8.0"),
        fail_maven(slug="maven-ossrh-host-leftover-vs-central-portal", plant="ullmannite-mvn", ver="1.1.2", nxt="1.1.3",
                   kind="oss.sonatype.org leftover vs central portal", leftover="https://oss.sonatype.org",
                   staging="orgullmannite-ossrh", first="close leftover OSSRH staging as if it were portal",
                   change="1.1.3 central portal; new upload", term="fail: BOM still orgullmannite-ossrh",
                   err="rejected: leftover oss.sonatype.org host; portal required",
                   pom="<url>https://oss.sonatype.org/service/local/staging/deploy/maven2/</url>"),
    )
    add(
        ok_crates(slug="crates-publish-vs-cargo-release-token", plant="topazolite-crate", ver="5.0.2", yanked="5.0.1",
                  kind="cargo-release token leftover vs cargo publish OIDC", leftover="cargo-release --token",
                  intended="cargo publish OIDC", asset="docs/release-token-5.0.1.note",
                  first="cargo-release leftover token so OIDC is unused",
                  change="5.0.2 cargo publish OIDC; leave token note",
                  term="success; cargo-release token note leftover",
                  err="error: leftover cargo-release token; crate requires OIDC",
                  pointer="docs/release-token-5.0.1.note"),
        fail_brew(slug="homebrew-rebuild-linux-only-formula-macos-sha", plant="spangolite-brew", ver="9.0.0",
                  kind="linux rebuild leftover vs macos sha in formula", leftover="macos sha from previous linux-only rebuild",
                  intended="macos rebuild sha", consumer="macos-ci",
                  first="keep leftover macos sha after linux-only rebuild",
                  change="rebuild macos; handoff macos-ci", term="fail: macos-ci still leftover sha",
                  err="* leftover macos sha after linux-only rebuild",
                  formula='bottle do\n  sha256 cellar: :any, sonoma: "BOTTLESHA"\nend'),
    )
    add(
        ok_nix(slug="nix-filterSource-leftover-vs-nar-src", plant="nichromite-nix", ver="2.0.5",
               kind="filterSource leftover vs NAR of src", leftover="builtins.filterSource hash",
               intended="lib.cleanSource NAR", asset="notes/filtersource.txt",
               first="keep leftover filterSource hash", change="lib.cleanSource NAR",
               term="success; filterSource note leftover",
               err="hash mismatch filterSource leftover vs cleanSource NAR",
               flake='src = builtins.filterSource (n: t: true) ./.; # leftover',
               fix='src = lib.cleanSource ./.; # NAR sha256-NARHASH'),
        fail_nuget(slug="nuget-snupkg-embed-pdb-and-snupkg-both", plant="microlite-nupkg", ver="1.9.9", nxt="2.0.0",
                   kind="embedded PDB leftover plus snupkg both", leftover="DebugType embedded + snupkg",
                   consumer="mixed-debugger", first="push leftover snupkg while DLL already embeds PDB",
                   change="2.0.0 portable + snupkg pack once", term="fail: mixed-debugger still 1.9.9 embedded",
                   err="error: 400 leftover embedded PDB cannot pair snupkg",
                   props="<DebugType>embedded</DebugType>\n<SymbolPackageFormat>snupkg</SymbolPackageFormat>"),
    )
    add(
        ok_cosign(slug="cosign-rekor-public-good-vs-private-monocle", plant="polyhalite-oci", ver="1.2.8",
                  kind="Rekor public-good leftover vs private Monocle log", leftover="rekor.sigstore.dev UUID",
                  intended="private Rekor Monocle", asset="dist/polyhalite.public-good.uuid",
                  first="verify leftover public-good UUID against private Monocle",
                  change="sign+verify against private Rekor", term="success; public-good UUID leftover",
                  err="Error: leftover public-good UUID not in private Monocle",
                  policy='{\n  "rekorURL": "https://rekor.monocle.internal"\n}',
                  sign="run: cosign sign --yes --rekor-url https://rekor.sigstore.dev $IMAGE"),
        fail_npm(slug="npm-provenance-trusted-publisher-package-json-name-rename", plant="tanzanite-js", ver="0.4.0", nxt="0.4.1",
                 kind="package.json name leftover vs trusted publisher row", leftover="name @tanzanite/legacy",
                 consumer="scope-lock", first="publish leftover @tanzanite/core onto legacy publisher name",
                 change="0.4.1 publisher row matches package.json", term="fail: scope-lock still legacy 0.4.0",
                 err="npm ERR! leftover package.json name @tanzanite/legacy",
                 wf="run: npm publish --provenance\n# leftover name @tanzanite/legacy"),
    )
    add(
        ok_pypi(slug="pypi-trusted-publisher-claimset-repo-visibility", plant="amazonite-py", ver="2.1.0",
                kind="OIDC claimset leftover private vs public repo", leftover="repository_visibility private",
                intended="public repo trusted publisher", asset="docs/private-claim-2.0.9.note",
                first="twine token so leftover private claimset is ignored",
                change="register public-repo publisher", term="success; private claim note leftover",
                err="403 leftover repository_visibility=private; publisher is public",
                wf="run: twine upload dist/*", old="2.0.9"),
        fail_maven(slug="maven-gpg-bestpractices-error-vs-warn", plant="violarite-mvn", ver="6.2.0", nxt="6.2.1",
                   kind="gpg.bestPractices error leftover vs warn", leftover="bestPractices=error SHA1",
                   staging="orgviolarite-3", first="close leftover SHA1 staging under error bestPractices",
                   change="6.2.1 SHA256; new staging", term="fail: BOM still orgviolarite-3",
                   err="close rejected: leftover bestPractices=error on SHA1 .asc",
                   pom="<bestPractices>error</bestPractices>"),
    )
    add(
        ok_crates(slug="crates-yank-vs-docsrs-source-tarball-cache", plant="melanite-crate", ver="0.3.2", yanked="0.3.1",
                  kind="docs.rs source tarball cache leftover after yank", leftover="docs.rs src crate.tgz",
                  intended="sparse yanked 0.3.1", asset="docs/docsrs-src-0.3.1.tgz.note",
                  first="unyank so docs.rs source tarball cache stays",
                  change="0.3.2; leave docs.rs src note", term="success; docs.rs src 0.3.1 leftover",
                  err="error: refuse unyank\ndocs.rs src leftover still 0.3.1",
                  pointer="docs/docsrs-src-0.3.1.tgz.note"),
        fail_brew(slug="homebrew-bottle-rebuild-vs-rebuild-linux-only-sha", plant="linarite-brew", ver="4.1.0",
                  kind="linux-only rebuild leftover sha vs macos formula", leftover="linux rebuild wrote macos sha",
                  intended="macos rebuild sha", consumer="macos-bottles",
                  first="keep leftover macos sha after linux-only rebuild",
                  change="rebuild macos; handoff macos-bottles", term="fail: macos-bottles still leftover sha",
                  err="* leftover macos sha after linux-only rebuild",
                  formula='bottle do\n  sha256 cellar: :any, sonoma: "BOTTLESHA"\nend'),
    )
    add(
        ok_nix(slug="nix-fetchgit-deepclone-false-vs-nar", plant="hematite-nix", ver="3.0.1",
               kind="fetchgit deepClone leftover vs NAR", leftover="deepClone = true hash",
               intended="shallow fetchgit NAR", asset="notes/deepclone.txt",
               first="keep leftover deepClone hash so the git FOD hits",
               change="deepClone false NAR", term="success; deepClone note leftover",
               err="hash mismatch leftover deepClone vs shallow NAR",
               flake='fetchgit { deepClone = true; sha256 = "sha256-LEFTHASH="; }',
               fix='fetchgit { sha256 = "sha256-NARHASH="; }'),
        fail_nuget(slug="nuget-snupkg-include-pdb-without-portable", plant="saleeite-nupkg", ver="5.0.2", nxt="5.0.3",
                   kind="IncludePdb leftover vs portable snupkg", leftover="IncludePdb without portable DebugType",
                   consumer="symreader", first="push leftover full PDB as snupkg",
                   change="5.0.3 portable + snupkg pack once", term="fail: symreader still 5.0.2",
                   err="error: 400 leftover full PDB cannot pair snupkg",
                   props="<IncludePdb>true</IncludePdb>\n<DebugType>full</DebugType>"),
    )
    add(
        ok_cosign(slug="cosign-new-bundle-format-vs-old-sig-layer", plant="kainite-oci", ver="8.4.0",
                  kind="new bundle format leftover vs old .sig layer", leftover="cosign.sig image layer",
                  intended="bundle v0.3 referrer", asset="notes/old-sig-layer.txt",
                  first="verify leftover .sig layer as a v0.3 bundle",
                  change="cosign sign --new-bundle-format", term="success; old .sig layer leftover",
                  err="Error: leftover tag .sig layer; policy wants bundle v0.3",
                  policy='{\n  "bundleFormat": "v0.3"\n}',
                  sign="run: cosign sign --yes $IMAGE  # leftover old sig layer"),
        fail_npm(slug="npm-oidc-audience-npm-vs-sigstore", plant="iolite-js", ver="1.8.0", nxt="1.8.1",
                 kind="OIDC audience leftover sigstore vs npm", leftover="audience sigstore",
                 consumer="audience-gate", first="publish leftover sigstore-audience token as npm provenance",
                 change="1.8.1 audience npmjs", term="fail: audience-gate still sigstore 1.8.0",
                 err="npm ERR! leftover OIDC audience sigstore; npm wants npm:registry",
                 wf="run: npm publish --provenance\n# leftover aud=sigstore"),
    )
    add(
        ok_pypi(slug="pypi-trusted-publisher-workflow-ref-branch-vs-tag", plant="moonstone-py", ver="0.9.4",
                kind="publisher workflow_ref leftover branch vs tag", leftover="refs/heads/release",
                intended="refs/tags/v0.9.4", asset="docs/branch-ref-0.9.3.note",
                first="twine token so leftover branch workflow_ref is ignored",
                change="register tag workflow_ref", term="success; 0.9.3 branch note leftover",
                err="403 leftover workflow_ref refs/heads/release; got tag v0.9.4",
                wf="on:\n  push:\n    tags: [\"v*\"]", old="0.9.3"),
        fail_maven(slug="maven-gpg-signer-name-vs-key-fingerprint", plant="polydymite-mvn", ver="1.4.0", nxt="1.4.1",
                   kind="signer name leftover vs fingerprint", leftover="signerName RelBot",
                   staging="orgpolydymite-6", first="close leftover staging signed by signerName",
                   change="1.4.1 fingerprint; new staging", term="fail: BOM still orgpolydymite-6",
                   err="close rejected: leftover signerName RelBot ≠ fingerprint",
                   pom="<signerName>RelBot</signerName>"),
    )
    add(
        ok_crates(slug="crates-yank-vs-cargo-outdated-tree-json", plant="goldmanite-crate", ver="2.5.0", yanked="2.4.9",
                  kind="cargo outdated --json leftover after yank", leftover="cargo-outdated JSON 2.4.9",
                  intended="sparse yanked 2.4.9", asset="docs/outdated-2.4.9.json",
                  first="unyank so cargo-outdated JSON stays", change="2.5.0; leave outdated JSON",
                  term="success; cargo-outdated 2.4.9 leftover",
                  err="error: refuse unyank\ncargo-outdated leftover still 2.4.9",
                  pointer="docs/outdated-2.4.9.json"),
        fail_brew(slug="homebrew-bottle-rebuild-vs-github-release-asset", plant="caledonite-brew", ver="0.7.0",
                  kind="GitHub release bottle leftover vs ghcr rebuild", leftover="GH release .tar.gz bottle",
                  intended="ghcr rebuilt bottle", consumer="release-asset",
                  first="retag leftover GH release bottle as ghcr",
                  change="ship ghcr; handoff release-asset", term="fail: release-asset still GH tar",
                  err="* leftover GitHub release bottle vs poured ghcr",
                  formula='bottle do\n  sha256 cellar: :any, sonoma: "BOTTLESHA"\nend'),
    )
    add(
        ok_nix(slug="nix-fetchpatch-vs-src-nar", plant="maghemite-nix", ver="1.6.0",
               kind="fetchpatch leftover vs NAR of patched src", leftover="fetchpatch file hash",
               intended="NAR of patched src", asset="notes/fetchpatch.txt",
               first="keep leftover fetchpatch hash", change="NAR of patched src",
               term="success; fetchpatch note leftover",
               err="hash mismatch leftover fetchpatch vs patched src NAR",
               flake='fetchpatch { sha256 = "sha256-LEFTHASH="; }',
               fix='src = fetchFromGitHub { hash = "sha256-NARHASH="; };'),
        fail_nuget(slug="nuget-snupkg-snupkg-compression-deflate-vs-lzma", plant="sabugalite-nupkg", ver="3.2.1", nxt="3.2.2",
                   kind="snupkg Deflate leftover vs LZMA nupkg", leftover="snupkg Deflate",
                   consumer="pack-tool", first="rewrite leftover snupkg compression to LZMA",
                   change="3.2.2 pack once matching compression", term="fail: pack-tool still 3.2.1",
                   err="error: 400 leftover snupkg Deflate ≠ nupkg LZMA",
                   props="<Compression>Deflate</Compression>"),
    )
    add(
        ok_cosign(slug="cosign-certificate-chain-leftover-vs-fulcio-root", plant="carnallite-oci", ver="2.0.3",
                  kind="leftover intermediate chain vs Fulcio root", leftover="custom intermediate PEM",
                  intended="Fulcio production root", asset="dist/carnallite-intermediate.pem",
                  first="verify leftover custom chain against Fulcio root",
                  change="sign keyless Fulcio production", term="success; intermediate PEM leftover",
                  err="Error: leftover intermediate chain not anchored at Fulcio root",
                  policy='{\n  "fulcio": "https://fulcio.sigstore.dev"\n}',
                  sign="run: cosign sign --certificate-chain dist/carnallite-intermediate.pem --yes $IMAGE"),
        fail_npm(slug="npm-provenance-publish-with-dry-run-packument", plant="hiddenite-js", ver="9.1.0", nxt="9.1.1",
                 kind="dry-run packument leftover vs live provenance", leftover="npm publish --dry-run packument",
                 consumer="dry-run-lock", first="upload leftover dry-run packument as provenance",
                 change="9.1.1 live OIDC publish", term="fail: dry-run-lock still 9.1.0",
                 err="npm ERR! leftover dry-run packument has no attestations",
                 wf="run: npm publish --dry-run --provenance"),
    )
    add(
        ok_pypi(slug="pypi-oidc-issuer-ghe-vs-github-dot-com", plant="sunstone-py", ver="4.0.2",
                kind="GHE OIDC issuer leftover vs github.com", leftover="https://ghe.example/_services/token",
                intended="https://token.actions.githubusercontent.com", asset="docs/ghe-issuer-4.0.1.note",
                first="twine token so leftover GHE issuer is ignored",
                change="register github.com issuer", term="success; GHE issuer note leftover",
                err="403 leftover issuer ghe.example; publisher is github.com",
                wf="run: twine upload dist/*", old="4.0.1"),
        fail_maven(slug="maven-gpg-passphrase-server-env-vs-agent", plant="siegenite-mvn", ver="8.0.1", nxt="8.0.2",
                   kind="passphrase server leftover vs gpg-agent", leftover="settings.xml passphrase server",
                   staging="orgsiegenite-2", first="close leftover staging using settings passphrase",
                   change="8.0.2 gpg-agent; new staging", term="fail: BOM still orgsiegenite-2",
                   err="close rejected: leftover settings passphrase empty .asc",
                   pom="<serverId>gpg</serverId><!-- leftover passphrase -->"),
    )
    add(
        ok_crates(slug="crates-yank-vs-rustup-component-index", plant="kimzeyite-crate", ver="1.1.4", yanked="1.1.3",
                  kind="rustup component leftover after yank", leftover="rustup extra crate index 1.1.3",
                  intended="sparse yanked 1.1.3", asset="docs/rustup-1.1.3.note",
                  first="unyank so rustup extra index stays", change="1.1.4; leave rustup note",
                  term="success; rustup 1.1.3 leftover",
                  err="error: refuse unyank\nrustup leftover still 1.1.3",
                  pointer="docs/rustup-1.1.3.note"),
        fail_brew(slug="homebrew-bottle-cellar-linuxbrew-prefix-leftover", plant="leadhillite-brew", ver="2.2.1",
                  kind="linuxbrew prefix leftover vs skip_relocation", leftover="cellar linuxbrew prefix",
                  intended="any_skip_relocation bottle", consumer="linuxbrew-host",
                  first="retag leftover linuxbrew prefix bottle as skip_relocation",
                  change="ship skip_relocation; handoff linuxbrew-host",
                  term="fail: linuxbrew-host still prefix cellar",
                  err="* leftover linuxbrew prefix cellar vs skip_relocation",
                  formula='bottle do\n  sha256 cellar: :any_skip_relocation, x86_64_linux: "BOTTLESHA"\nend'),
    )
    add(
        ok_nix(slug="nix-fetchhg-vs-nar-of-export", plant="magnesioferrite-nix", ver="0.8.3",
               kind="fetchhg leftover vs NAR of hg archive", leftover="fetchhg working-copy hash",
               intended="NAR of hg archive", asset="notes/fetchhg.txt",
               first="keep leftover fetchhg working-copy hash", change="NAR of hg archive",
               term="success; fetchhg note leftover",
               err="hash mismatch leftover hg wc vs archive NAR",
               flake='fetchhg { sha256 = "sha256-LEFTHASH="; }',
               fix='fetchhg { sha256 = "sha256-NARHASH="; }'),
        fail_nuget(slug="nuget-snupkg-source-link-azure-vs-github", plant="novacekite-nupkg", ver="7.0.0", nxt="7.0.1",
                   kind="SourceLink Azure leftover vs GitHub repo", leftover="SourceLink Azure Repos URL",
                   consumer="azure-debug", first="push leftover Azure SourceLink onto GitHub package",
                   change="7.0.1 GitHub SourceLink pack once", term="fail: azure-debug still 7.0.0",
                   err="error: 400 leftover SourceLink Azure ≠ nupkg GitHub",
                   props="<RepositoryUrl>https://dev.azure.com/novacekite/novacekite</RepositoryUrl>"),
    )
    add(
        ok_cosign(slug="cosign-sct-log-id-leftover-vs-fulcio-sct", plant="sylvite-oci", ver="5.1.1",
                  kind="SCT log ID leftover vs Fulcio SCT", leftover="custom CT log ID",
                  intended="Fulcio SCT", asset="dist/sylvite-custom-sct.der",
                  first="verify leftover custom SCT log ID",
                  change="require Fulcio SCT", term="success; custom SCT leftover",
                  err="Error: leftover custom CT log ID; Fulcio SCT missing",
                  policy='{\n  "requireSCT": true\n}',
                  sign="run: cosign sign --yes $IMAGE  # leftover custom sct"),
        fail_npm(slug="npm-provenance-workspace-root-vs-package-dir", plant="kunzite-js", ver="3.4.0", nxt="3.4.1",
                 kind="workspace root leftover vs package dir provenance", leftover="publish from repo root",
                 consumer="workspace-lock", first="publish leftover root tarball as package provenance",
                 change="3.4.1 publish from packages/kunzite", term="fail: workspace-lock still root 3.4.0",
                 err="npm ERR! leftover workspace root subjectDigest ≠ package dir",
                 wf="run: npm publish --workspace kunzite --provenance\n# leftover cwd repo root"),
    )
    add(
        ok_pypi(slug="pypi-attestation-bundle-dpop-vs-oidc", plant="aventurine-py", ver="6.1.1",
                kind="DPoP leftover vs GitHub OIDC publisher", leftover="DPoP access token",
                intended="GitHub OIDC trusted publisher", asset="docs/dpop-6.1.0.note",
                first="twine leftover DPoP token so OIDC is unused",
                change="OIDC trusted publisher", term="success; DPoP note leftover",
                err="403 leftover DPoP token; project requires GitHub OIDC",
                wf="run: twine upload dist/* --non-interactive", old="6.1.0"),
        fail_maven(slug="maven-gpg-homedir-tmp-vs-runner-cache", plant="carrollite-mvn", ver="0.5.5", nxt="0.5.6",
                   kind="GNUPGHOME /tmp leftover vs runner cache", leftover="GNUPGHOME=/tmp/gpg-leftover",
                   staging="orgcarrollite-9", first="close leftover staging signed from /tmp homedir",
                   change="0.5.6 runner cache homedir; new staging", term="fail: BOM still orgcarrollite-9",
                   err="close rejected: leftover /tmp GNUPGHOME wiped; no .asc",
                   pom="<homedir>/tmp/gpg-leftover</homedir>"),
    )
    add(
        ok_crates(slug="crates-yank-vs-cargo-minimal-versions-report", plant="schorlomite-crate", ver="4.4.0", yanked="4.3.9",
                  kind="cargo -Z minimal-versions leftover after yank", leftover="minimal-versions report 4.3.9",
                  intended="sparse yanked 4.3.9", asset="docs/minver-4.3.9.txt",
                  first="unyank so minimal-versions report stays", change="4.4.0; leave minver report",
                  term="success; minver 4.3.9 leftover",
                  err="error: refuse unyank\nminver leftover still 4.3.9",
                  pointer="docs/minver-4.3.9.txt"),
        fail_brew(slug="homebrew-bottle-rebuild-vs-github-packages-tag", plant="susannite-brew", ver="1.0.8",
                  kind="GHCR package tag leftover vs rebuild digest", leftover="ghcr tag :latest",
                  intended="rebuild digest tag", consumer="latest-tag",
                  first="retag leftover :latest as rebuilt digest",
                  change="ship digest tag; handoff latest-tag", term="fail: latest-tag still :latest",
                  err="* leftover ghcr :latest vs rebuilt digest",
                  formula='bottle do\n  sha256 cellar: :any, sonoma: "BOTTLESHA"\nend'),
    )
    add(
        ok_nix(slug="nix-fetchsvn-vs-nar-of-export", plant="goethite-nix", ver="2.7.2",
               kind="fetchsvn leftover vs NAR of svn export", leftover="fetchsvn wc hash",
               intended="NAR of svn export", asset="notes/fetchsvn.txt",
               first="keep leftover fetchsvn wc hash", change="NAR of svn export",
               term="success; fetchsvn note leftover",
               err="hash mismatch leftover svn wc vs export NAR",
               flake='fetchsvn { sha256 = "sha256-LEFTHASH="; }',
               fix='fetchsvn { sha256 = "sha256-NARHASH="; }'),
        fail_nuget(slug="nuget-snupkg-deterministic-sourcepaths-root-diff", plant="zeunerite-nupkg", ver="2.1.1", nxt="2.1.2",
                   kind="SourceRoot leftover vs deterministic paths", leftover="SourceRoot D:\\leftover",
                   consumer="pathmap", first="rewrite leftover snupkg SourceRoot",
                   change="2.1.2 deterministic SourceRoot pack once", term="fail: pathmap still 2.1.1",
                   err="error: 400 leftover SourceRoot D:\\leftover ≠ nupkg",
                   props="<DeterministicSourcePaths>true</DeterministicSourcePaths>\n<SourceRoot>D:\\leftover</SourceRoot>"),
    )
    add(
        ok_cosign(slug="cosign-tuf-root-v11-vs-v12-checkpoint", plant="leonite-oci", ver="3.4.1",
                  kind="TUF root v11 leftover vs v12 checkpoint", leftover="TUF root v11",
                  intended="TUF root v12", asset="dist/leonite-tuf-v11.json",
                  first="verify leftover TUF v11 root against v12 policy",
                  change="refresh TUF root v12", term="success; v11 root leftover",
                  err="Error: leftover TUF root v11; policy checkpoint v12",
                  policy='{\n  "tufRoot": "v12"\n}',
                  sign="run: cosign sign --yes $IMAGE  # leftover tuf v11"),
        fail_npm(slug="npm-provenance-bundle-dependencies-optional", plant="spodumene-js", ver="2.2.0", nxt="2.2.1",
                 kind="optionalDependencies leftover vs provenance subject", leftover="optionalDependencies vendor",
                 consumer="optional-lock", first="publish leftover optional vendor in subjectDigest",
                 change="2.2.1 drop optional leftover then OIDC", term="fail: optional-lock still 2.2.0",
                 err="npm ERR! leftover optionalDependencies in subjectDigest",
                 wf='run: npm publish --provenance\n# leftover "optionalDependencies": {"vendor":"1.0.0"}'),
    )
    add(
        ok_pypi(slug="pypi-trusted-publisher-environment-protection-rules", plant="agate-py", ver="1.3.3",
                kind="environment protection leftover vs unprotected OIDC", leftover="environment protection wait",
                intended="release environment OIDC", asset="docs/protection-1.3.2.note",
                first="twine token so leftover protection wait is skipped",
                change="register unprotected release env", term="success; protection note leftover",
                err="403 leftover environment protection pending; job unprotected",
                wf="environment:\n  name: release\n  protection: leftover", old="1.3.2"),
        fail_maven(slug="maven-gpg-key-expire-date-leftover", plant="vaesite-mvn", ver="4.4.2", nxt="4.4.3",
                   kind="gpg key expire leftover vs new subkey", leftover="expired expire-date 2020",
                   staging="orgvaesite-5", first="re-sign leftover staging with expired expire-date",
                   change="4.4.3 new subkey; new staging", term="fail: BOM still orgvaesite-5",
                   err="close rejected: leftover expire-date 2020 BAD signature",
                   pom="<expireDate>2020-01-01</expireDate>"),
    )
    add(
        ok_crates(slug="crates-yank-vs-crates-io-download-endpoint-cache", plant="morimotoite-crate", ver="0.1.7", yanked="0.1.6",
                  kind="crates.io /api/v1/crates download leftover after yank", leftover="download endpoint cache",
                  intended="sparse yanked 0.1.6", asset="docs/dl-0.1.6.note",
                  first="unyank so download endpoint cache stays", change="0.1.7; leave download note",
                  term="success; download 0.1.6 leftover",
                  err="error: refuse unyank\ndownload endpoint leftover still 0.1.6",
                  pointer="docs/dl-0.1.6.note"),
        fail_brew(slug="homebrew-bottle-rebuild-vs-github-attestation-predicate", plant="chenite-brew", ver="5.5.1",
                  kind="GHCR attestation leftover vs bottle sha", leftover="gh attestation predicate",
                  intended="rebuilt bottle sha", consumer="attest-bot",
                  first="treat leftover GH attestation as bottle sha",
                  change="rebuild bottle sha; handoff attest-bot", term="fail: attest-bot still leftover predicate",
                  err="* leftover GH attestation predicate ≠ rebuilt bottle sha",
                  formula='bottle do\n  sha256 cellar: :any, sonoma: "BOTTLESHA"\nend'),
    )
    add(
        ok_nix(slug="nix-fetchcvs-vs-nar-of-export", plant="lepidocrocite-nix", ver="0.2.4",
               kind="fetchcvs leftover vs NAR of cvs export", leftover="fetchcvs module hash",
               intended="NAR of cvs export", asset="notes/fetchcvs.txt",
               first="keep leftover fetchcvs module hash", change="NAR of cvs export",
               term="success; fetchcvs note leftover",
               err="hash mismatch leftover cvs module vs export NAR",
               flake='fetchcvs { sha256 = "sha256-LEFTHASH="; }',
               fix='fetchcvs { sha256 = "sha256-NARHASH="; }'),
        fail_nuget(slug="nuget-snupkg-pdb-portable-pdb-age-vs-timestamp", plant="metatorbernite-nupkg", ver="8.1.1", nxt="8.1.2",
                   kind="portable PDB age leftover vs timestamp", leftover="PDB age 0 vs timestamp",
                   consumer="dia", first="rewrite leftover snupkg PDB age",
                   change="8.1.2 pack once matching age", term="fail: dia still 8.1.1",
                   err="error: 400 leftover PDB age ≠ DLL timestamp",
                   props="<DebugType>portable</DebugType>\n<!-- leftover age 0 -->"),
    )
    add(
        ok_cosign(slug="cosign-experimental-features-oci-artifact-type", plant="langbeinite-oci", ver="6.6.1",
                  kind="experimental OCI artifact type leftover vs image", leftover="artifactType leftover.sig",
                  intended="oci image signature", asset="notes/artifact-type.txt",
                  first="verify leftover artifactType as an image signature",
                  change="sign standard oci image", term="success; artifactType note leftover",
                  err="Error: leftover artifactType application/vnd.dev.cosign.artifact; want image",
                  policy='{\n  "mediaType": "application/vnd.oci.image.manifest.v1+json"\n}',
                  sign="run: cosign sign --yes --registry-referrers=false $IMAGE"),
        fail_npm(slug="npm-trusted-publisher-org-vs-user-account", plant="triphane-js", ver="0.6.6", nxt="0.6.7",
                 kind="trusted publisher leftover user vs org", leftover="publisher user leftover-bot",
                 consumer="org-lock", first="publish leftover user publisher onto org package",
                 change="0.6.7 org OIDC publisher", term="fail: org-lock still user 0.6.6",
                 err="npm ERR! leftover trusted publisher user leftover-bot; package is org",
                 wf="run: npm publish --provenance\n# leftover user publisher"),
    )
    add(
        ok_pypi(slug="pypi-uv-publish-trusted-publishing-explicit", plant="jasper-py", ver="3.8.0",
                kind="uv publish leftover token vs --trusted-publishing", leftover="UV_PUBLISH_TOKEN",
                intended="uv --trusted-publishing OIDC", asset="docs/uv-token-3.7.9.note",
                first="uv publish leftover token so OIDC is unused",
                change="uv publish --trusted-publishing", term="success; token note leftover",
                err="403 leftover UV_PUBLISH_TOKEN; project requires trusted publishing",
                wf="run: uv publish\nenv:\n  UV_PUBLISH_TOKEN: ${{ secrets.PYPI }}", old="3.7.9"),
        fail_maven(slug="maven-gpg-sign-attached-vs-detached-asc", plant="linnaeite-mvn", ver="7.3.0", nxt="7.3.1",
                   kind="attached signature leftover vs detached .asc", leftover="gpg --sign attached",
                   staging="orglinnaeite-8", first="close leftover attached-sig staging",
                   change="7.3.1 detached .asc; new staging", term="fail: BOM still orglinnaeite-8",
                   err="close rejected: leftover attached signature; portal wants detached .asc",
                   pom="<!-- leftover gpg --sign attached -->"),
    )
    add(
        ok_crates(slug="crates-yank-vs-lib-rs-reverse-deps-page", plant="eltyubyuite-crate", ver="2.8.8", yanked="2.8.7",
                  kind="lib.rs reverse-deps leftover after yank", leftover="lib.rs reverse deps 2.8.7",
                  intended="sparse yanked 2.8.7", asset="docs/librs-revdeps-2.8.7.html",
                  first="unyank so lib.rs reverse-deps stays", change="2.8.8; leave reverse-deps HTML",
                  term="success; reverse-deps 2.8.7 leftover",
                  err="error: refuse unyank\nlib.rs reverse-deps leftover still 2.8.7",
                  pointer="docs/librs-revdeps-2.8.7.html"),
        fail_brew(slug="homebrew-bottle-rebuild-vs-homebrew-core-pr-sha", plant="mattheddleite-brew", ver="0.9.2",
                  kind="homebrew-core PR sha leftover vs local rebuild", leftover="core PR bottle sha",
                  intended="local rebuild sha", consumer="core-pr",
                  first="keep leftover core PR sha after local rebuild",
                  change="write local sha; handoff core-pr", term="fail: core-pr still leftover sha",
                  err="* leftover homebrew-core PR sha ≠ local rebuild",
                  formula='bottle do\n  sha256 cellar: :any, sonoma: "BOTTLESHA"\nend'),
    )
    add(
        ok_nix(slug="nix-fetchipfs-vs-nar-of-cid", plant="akaganeite-nix", ver="1.1.8",
               kind="fetchipfs leftover vs NAR of CID", leftover="fetchipfs CID hash",
               intended="NAR of unpacked CID", asset="notes/fetchipfs.txt",
               first="keep leftover fetchipfs CID hash", change="NAR of unpacked CID",
               term="success; CID note leftover",
               err="hash mismatch leftover CID bytes vs NAR",
               flake='fetchipfs { cid = "QmLeftover"; sha256 = "sha256-LEFTHASH="; }',
               fix='fetchipfs { cid = "QmOk"; sha256 = "sha256-NARHASH="; }'),
        fail_nuget(slug="nuget-snupkg-snupkg-vs-embedded-portable-split", plant="bassetite-nupkg", ver="4.0.4", nxt="4.0.5",
                   kind="embedded portable leftover plus snupkg split", leftover="embedded portable + snupkg",
                   consumer="hybrid-dbg", first="push leftover snupkg with embedded portable PDB",
                   change="4.0.5 portable-only + snupkg pack once", term="fail: hybrid-dbg still 4.0.4",
                   err="error: 400 leftover embedded portable cannot pair snupkg",
                   props="<DebugType>embedded</DebugType>\n<DebugSymbols>true</DebugSymbols>"),
    )
    return extra


PAIRS = _pairs()


def emit(round_n: int):
    idx = round_n - CATALOG_FIRST
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(f"round {round_n} outside catalog {CATALOG_FIRST}+{len(PAIRS)}")
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
        raise SystemExit("dup slug or plant in attest wave5 catalog")
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
    print(json.dumps({
        "catalog_first": CATALOG_FIRST,
        "n_pairs": len(PAIRS),
        "last_round": CATALOG_FIRST + len(PAIRS) - 1,
        "n_slugs": len(slugs),
    }))


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
        raise SystemExit("need --round and --staging (or --selfcheck)")
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
