#!/usr/bin/env python3
"""Mill package-release-factory r296+ wave-4 attestation plants."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("pkg_mill_r247", HERE / "pkg-mill-r247.py")
base = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(base)

CATALOG_FIRST = 296
hx = base.hx
BUILDERS = base.BUILDERS
notes_for = base.notes_for
banned_text = base.banned_text
_ok = base._ok
_fail = base._fail


def _pairs():
    extra = []

    def add(ok, fail):
        extra.append(("ok_attest", ok, "fail_leftover", fail))

    add(
        _ok(
            slug="cosign-bundle-v03-vs-policy-v01-media",
            plant="duftite-oci",
            gate="cosign",
            kind="bundle v0.3 leftover vs policy v0.1 mediaType",
            goal="Ship duftite-oci 1.9.0. leftover admission expects application/vnd.dev.sigstore.bundle+json v0.1; image has v0.3. Keep signed v1.9.0. Leave v0.1 asset leftover.",
            plan="rewrite mediaType string on the leftover v0.3 bundle to v0.1.",
            outcome="mediaType rewrite is not a real v0.1 bundle. Plan change: verify v0.3. Residual: v0.1 asset leftover.",
            inspect_cmd="cosign download bundle ghcr.io/duftite-designed/duftite-oci:1.9.0 | python3 -c 'import sys; print(sys.stdin.read()[:120])'",
            inspect_obs="mediaType application/vnd.dev.sigstore.bundle.v0.3+json",
            cfg_path="policy/cosign-verify.json",
            cfg_obs="{\n  \"bundleMediaType\": \"application/vnd.dev.sigstore.bundle+json\"\n}\n",
            sec_path=".github/workflows/sign.yml",
            sec_obs="run: cosign sign --yes --new-bundle-format $IMAGE\n",
            dump_cmd="cosign verify ghcr.io/duftite-designed/duftite-oci:1.9.0 2>&1 | tail -n 6",
            dump_obs="Error: policy wants v0.1 mediaType leftover; got v0.3",
            apply_cmd="python3 - <<'PY'\nprint('rewrote mediaType string to v0.1')\nPY",
            apply_obs="rewrote mediaType string to v0.1\nverify DENY: body still v0.3",
            apply_refl="Apply failed. Rewriting leftover mediaType string does not make a v0.1 bundle.",
            iso_cmd="echo HAVE=v0.3 WANT=v0.1_leftover_policy",
            iso_obs="HAVE=v0.3 WANT=v0.1_leftover_policy",
            id_cmd="echo CONSUMER=admission",
            id_obs="CONSUMER=admission",
            fix_path="policy/cosign-verify.json",
            fix_contents="{\n  \"bundleMediaType\": \"application/vnd.dev.sigstore.bundle.v0.3+json\"\n}\n",
            gate_cmd="cosign verify ghcr.io/duftite-designed/duftite-oci:1.9.0 --certificate-identity https://github.com/duftite-designed/duftite-oci/.github/workflows/sign.yml@refs/tags/v1.9.0 --certificate-oidc-issuer https://token.actions.githubusercontent.com 2>&1 | tail -n 5",
            gate_obs="Verified OK v0.3 bundle",
            pass_cmd="echo BUNDLE=v03_ok",
            pass_obs="BUNDLE=v03_ok",
            left_cmd="ls dist/duftite-1.9.0.v01.bundle.json && echo V01_ASSET=leftover",
            left_obs="dist/duftite-1.9.0.v01.bundle.json\nV01_ASSET=leftover",
            doc_cmd="echo KEEP_V01_ASSET=1",
            doc_obs="KEEP_V01_ASSET=1",
            tag_cmd="git verify-tag v1.9.0 >/dev/null && echo signed_tag_ok",
            tag_obs="signed_tag_ok",
            cmt_cmd="git add policy/cosign-verify.json && git commit -m 'verify v0.3 bundle; leftover v0.1 asset'",
            cmt_obs="[main " + hx("duf-cmt", 7) + "] verify v0.3 bundle; leftover v0.1 asset",
            res_cmd="echo BUNDLE=v03 V01=leftover",
            res_obs="BUNDLE=v03 V01=leftover",
            res_refl="v0.3 bundle is not a v0.1 string rewrite. Residual: v0.1 asset leftover.",
            seed="bundle v0.3 vs leftover v0.1 mediaType policy",
            first="rewrite mediaType string",
            change="policy accepts v0.3",
            term="success; v0.1 asset leftover",
        ),
        _fail(
            slug="npm-provenance-otp-automation-token-leftover",
            plant="conichalcite-js",
            gate="npm provenance",
            kind="OTP leftover vs trusted publisher",
            goal="conichalcite-js 8.8.0 leftover 2FA OTP publish has no provenance. 8.8.1 OIDC. latest still 8.8.0. Do not unpublish.",
            plan="npm publish --otp leftover over 8.8.0 --provenance.",
            outcome="OTP cannot attach provenance to 8.8.0. Residual: latest 8.8.0. Ticket not closed.",
            inspect_cmd="npm view @conichalcite/core@8.8.0 --json | python3 -c 'import json,sys; print(json.load(sys.stdin).get(\"dist\",{}).get(\"attestations\"))'",
            inspect_obs="None",
            wf_path=".github/workflows/npm.yml",
            wf_obs="run: npm publish --otp ${{ secrets.NPM_OTP }}\n",
            why_cmd="echo OTP=no_oidc ATTEST=null",
            why_obs="OTP=no_oidc ATTEST=null",
            con_path=".npmrc-fleet",
            con_obs="# fleet latest\n",
            apply_cmd="npm publish --otp 123456 --provenance --tag latest 2>&1 | tail -n 6",
            apply_obs="npm ERR! 403 cannot replace 8.8.0\nOTP path cannot attach provenance",
            apply_refl="Apply failed. OTP leftover publish is not trusted-publisher provenance.",
            still_cmd="npm view @conichalcite/core@8.8.0 version",
            still_obs="8.8.0",
            use_cmd="npm view @conichalcite/core dist-tags --json",
            use_obs="{\"latest\":\"8.8.0\"}",
            fix_cmd="echo NEXT=8.8.1 OIDC=1",
            fix_obs="NEXT=8.8.1 OIDC=1",
            pub_cmd="npm version 8.8.1 --no-git-tag-version && npm publish --access public --provenance 2>&1 | tail -n 5",
            pub_obs="+ @conichalcite/core@8.8.1\nprovenance uploaded",
            ver_cmd="echo ATTEST_881=true",
            ver_obs="ATTEST_881=true",
            tag_cmd="git tag -s v8.8.1 -m '8.8.1'",
            tag_obs="tagged v8.8.1",
            still2_cmd="npm view @conichalcite/core dist-tags --json",
            still2_obs="{\"latest\":\"8.8.0\",\"next\":\"8.8.1\"}",
            undo_cmd="echo skipped_unpublish_880=1",
            undo_obs="skipped_unpublish_880=1",
            split_cmd="echo LATEST=8.8.0_otp NEW=8.8.1_oidc",
            split_obs="LATEST=8.8.0_otp NEW=8.8.1_oidc",
            tix_cmd="echo TICKET=fleet_latest_still_8.8.0_otp",
            tix_obs="TICKET=fleet_latest_still_8.8.0_otp",
            res_cmd="echo NEW=8.8.1 LATEST=8.8.0",
            res_obs="NEW=8.8.1 LATEST=8.8.0",
            seed="npm OTP leftover vs OIDC provenance",
            first="OTP --provenance over 8.8.0",
            change="8.8.1 OIDC provenance",
            term="fail: latest still 8.8.0 OTP",
        ),
    )
    add(
        _ok(
            slug="pypi-trusted-publisher-workflow-sha-vs-tag",
            plant="austinite-py",
            gate="PyPI trusted publishing",
            kind="workflow_ref leftover SHA vs tag",
            goal="Ship austinite-py 5.0.0. leftover publisher workflow_ref pins a commit SHA; job runs refs/tags/v5.0.0. Align to tag. Leave 4.9.9 leftover.",
            plan="twine token so workflow_ref leftover SHA is ignored.",
            outcome="Token skips PEP 740. Plan change: register tag ref. Residual: 4.9.9 leftover.",
            inspect_cmd="echo ROW_REF=refs/heads/main@deadbeef LIVE=refs/tags/v5.0.0",
            inspect_obs="ROW_REF=refs/heads/main@deadbeef LIVE=refs/tags/v5.0.0",
            cfg_path=".github/workflows/pypi.yml",
            cfg_obs="on:\n  push:\n    tags: [\"v*\"]\n",
            sec_path="pyproject.toml",
            sec_obs="[project]\nname = \"austinite-py\"\nversion = \"5.0.0\"\n",
            dump_cmd="echo workflow_ref=austinite-designed/austinite-py/.github/workflows/pypi.yml@refs/tags/v5.0.0",
            dump_obs="workflow_ref=...@refs/tags/v5.0.0",
            apply_cmd="python3 -m twine upload dist/austinite_py-5.0.0-py3-none-any.whl 2>&1 | tail -n 6",
            apply_obs="403 Registered workflow_ref SHA leftover; got tag v5.0.0",
            apply_refl="Apply failed. Publisher workflow_ref leftover SHA is not the tag job.",
            iso_cmd="echo NEED=tag HAVE=sha leftover",
            iso_obs="NEED=tag HAVE=sha leftover",
            id_cmd="echo ISSUER=https://token.actions.githubusercontent.com",
            id_obs="ISSUER=https://token.actions.githubusercontent.com",
            fix_path="docs/publisher.json",
            fix_contents="{\n  \"workflow\": \"pypi.yml\",\n  \"environment\": \"release\"\n}\n",
            gate_cmd="python3 -m twine upload dist/austinite_py-5.0.0-py3-none-any.whl 2>&1 | tail -n 5",
            gate_obs="Uploading 5.0.0\nAttestations uploaded tag ref",
            pass_cmd="echo PROV_500=yes",
            pass_obs="PROV_500=yes",
            left_cmd="echo TOKEN_499=leftover",
            left_obs="TOKEN_499=leftover",
            doc_cmd="echo KEEP_499=1",
            doc_obs="KEEP_499=1",
            tag_cmd="git tag -s v5.0.0 -m '5.0.0' && echo signed_tag_ok",
            tag_obs="signed_tag_ok",
            cmt_cmd="git add docs/publisher.json && git commit -m 'publisher matches tag workflow_ref'",
            cmt_obs="[main " + hx("aus-cmt", 7) + "] publisher matches tag workflow_ref",
            res_cmd="echo REF=tag TOKEN_499=leftover",
            res_obs="REF=tag TOKEN_499=leftover",
            res_refl="workflow_ref leftover SHA is not the tag. Residual: 4.9.9 leftover.",
            seed="publisher workflow_ref SHA leftover vs tag",
            first="token bypass SHA row",
            change="register tag workflow_ref",
            term="success; 4.9.9 leftover",
        ),
        _fail(
            slug="maven-staging-close-without-gpg-plugin",
            plant="adelite-mvn",
            gate="Maven GPG",
            kind="nexus-staging leftover skip gpg plugin",
            goal="adelite-mvn 3.3.0 leftover skipped maven-gpg-plugin; staging close unsigned. Sign 3.3.1. BOM still orgadelite-7. Do not promote 7.",
            plan="attach leftover .asc and re-close 7.",
            outcome="staging 7 never signed. Residual: BOM 7. Ticket not closed.",
            inspect_cmd="rg skip pom.xml; echo STAGING=orgadelite-7",
            inspect_obs="<skip>true</skip> maven-gpg-plugin leftover\nSTAGING=orgadelite-7",
            wf_path="pom.xml",
            wf_obs="<plugin><artifactId>maven-gpg-plugin</artifactId><configuration><skip>true</skip></configuration></plugin>\n",
            why_cmd="echo PORTAL=require_asc GOT=skip leftover",
            why_obs="PORTAL=require_asc GOT=skip leftover",
            con_path="../adelite-bom/pom.xml",
            con_obs="<adelite.staging>orgadelite-7</adelite.staging>\n",
            apply_cmd="mvn nexus-staging:rc-close -DstagingRepositoryId=orgadelite-7 2>&1 | tail -n 6",
            apply_obs="close rejected: no signatures (gpg skip leftover)",
            apply_refl="Apply failed. skip leftover means staging 7 has no .asc.",
            still_cmd="echo STAGING_7=unsigned",
            still_obs="STAGING_7=unsigned",
            use_cmd="rg orgadelite-7 ../adelite-bom/pom.xml",
            use_obs="<adelite.staging>orgadelite-7</adelite.staging>",
            fix_cmd="echo NEXT=3.3.1 skip=false NEW_STAGING=1",
            fix_obs="NEXT=3.3.1 skip=false NEW_STAGING=1",
            pub_cmd="sed -i 's/true/false/; s/3.3.0/3.3.1/' pom.xml && mvn -B -Prelease deploy 2>&1 | tail -n 5",
            pub_obs="Uploaded orgadelite-12 signed",
            ver_cmd="gpg --verify adelite-mvn-3.3.1.jar.asc 2>&1 | tail -n 3",
            ver_obs="Good signature",
            tag_cmd="git tag -s v3.3.1 -m '3.3.1'",
            tag_obs="tagged v3.3.1",
            still2_cmd="rg orgadelite-7 ../adelite-bom/pom.xml",
            still2_obs="<adelite.staging>orgadelite-7</adelite.staging>",
            undo_cmd="echo skipped_promote_7=1",
            undo_obs="skipped_promote_7=1",
            split_cmd="echo NEW=12_signed BOM=7_skip",
            split_obs="NEW=12_signed BOM=7_skip",
            tix_cmd="echo TICKET=bom_still_orgadelite-7",
            tix_obs="TICKET=bom_still_orgadelite-7",
            res_cmd="echo NEW=3.3.1 BOM=7",
            res_obs="NEW=3.3.1 BOM=7",
            seed="maven-gpg-plugin skip leftover unsigned staging",
            first="re-close unsigned staging 7",
            change="3.3.1 skip=false new staging",
            term="fail: BOM still staging 7",
            extra_reward={"staging_leftover": 1},
        ),
    )
    add(
        _ok(
            slug="crates-yank-vs-cargo-tree-outdated-lock",
            plant="gottlobite-crate",
            gate="crates.io yank vs index",
            kind="cargo tree leftover lock after yank not a lock-yank twin",
            goal="Ship gottlobite-crate 1.2.3 after yanking 1.2.2 on crates.io sparse. leftover cargo tree in a docs snapshot still prints 1.2.2. Refresh docs. Leave snapshot leftover. Do not treat Cargo.lock as the plant.",
            plan="cargo yank --undo 1.2.2 so docs cargo tree stays.",
            outcome="Unyank refused. Plan change: 1.2.3 + leave docs snapshot. Residual: snapshot leftover.",
            inspect_cmd="curl -sS https://index.crates.io/go/tt/gottlobite-crate | tail -n 1; echo DOCS_TREE=1.2.2",
            inspect_obs="{\"vers\":\"1.2.2\",\"yanked\":true}\nDOCS_TREE=1.2.2",
            cfg_path="docs/tree.txt",
            cfg_obs="gottlobite-crate v1.2.2\n",
            sec_path="Cargo.toml",
            sec_obs="[package]\nname = \"gottlobite-crate\"\nversion = \"1.2.3\"\n",
            dump_cmd="echo SPARSE=yanked DOCS=1.2.2 leftover",
            dump_obs="SPARSE=yanked DOCS=1.2.2 leftover",
            apply_cmd="cargo yank --undo gottlobite-crate@1.2.2 2>&1 | tail -n 5",
            apply_obs="error: refuse unyank\ndocs tree leftover still 1.2.2",
            apply_refl="Apply failed. docs cargo tree leftover is not crates.io yank (and not a lock pin twin).",
            iso_cmd="echo DOCS=122 SPARSE=yanked",
            iso_obs="DOCS=122 SPARSE=yanked",
            id_cmd="echo CONSUMER=docs_snapshot",
            id_obs="CONSUMER=docs_snapshot",
            fix_path="docs/advise.json",
            fix_contents="{\"next\":\"1.2.3\",\"leave_docs_tree\":\"1.2.2\"}\n",
            gate_cmd="cargo publish --allow-dirty 2>&1 | tail -n 4",
            gate_obs="Uploaded gottlobite-crate v1.2.3",
            pass_cmd="echo CRATE_123=ok",
            pass_obs="CRATE_123=ok",
            left_cmd="cat docs/tree.txt",
            left_obs="gottlobite-crate v1.2.2",
            doc_cmd="echo KEEP_DOCS_TREE_122=1",
            doc_obs="KEEP_DOCS_TREE_122=1",
            tag_cmd="git tag -s v1.2.3 -m '1.2.3' && echo signed_tag_ok",
            tag_obs="signed_tag_ok",
            cmt_cmd="git add docs/advise.json && git commit -m '1.2.3; leftover docs cargo tree 1.2.2'",
            cmt_obs="[main " + hx("got-cmt", 7) + "] 1.2.3; leftover docs cargo tree 1.2.2",
            res_cmd="echo NEW=1.2.3 DOCS_TREE=leftover",
            res_obs="NEW=1.2.3 DOCS_TREE=leftover",
            res_refl="docs cargo tree leftover is not yank. Residual: snapshot leftover.",
            seed="yank vs leftover docs cargo tree snapshot",
            first="unyank so docs tree stays",
            change="1.2.3; leave docs snapshot",
            term="success; docs tree 1.2.2 leftover",
        ),
        _fail(
            slug="homebrew-bottle-cellar-any-skip-vs-relocatable",
            plant="cobaltaustinite-brew",
            gate="Homebrew bottle rebuild",
            kind="relocatable leftover vs skip_relocation bottle",
            goal="cobaltaustinite-brew 2.4.0 rebuilt skip_relocation; leftover formula still relocatable. Selfhost still relocatable bottle. Do not retag.",
            plan="retag skip_relocation bottle as relocatable leftover.",
            outcome="audit cellar class mismatch. Residual: selfhost relocatable. Ticket not closed.",
            inspect_cmd="rg cellar Formula/cobaltaustinite.rb",
            inspect_obs="sha256 cellar: :any_skip_relocation leftover formula says relocatable",
            wf_path="Formula/cobaltaustinite.rb",
            wf_obs="bottle do\n  sha256 cellar: :any, sonoma: \"" + hx("cob2", 64) + "\"\nend\n",
            why_cmd="echo POURED=skip_reloc FORMULA=any leftover",
            why_obs="POURED=skip_reloc FORMULA=any leftover",
            con_path="../cobaltaustinite-selfhost/Brewfile",
            con_obs="brew \"cobaltaustinite\"\n",
            apply_cmd="brew audit --strict cobaltaustinite 2>&1 | tail -n 6",
            apply_obs="* cellar class leftover :any vs poured skip_relocation",
            apply_refl="Apply failed. relocatable leftover formula is not skip_relocation bottle bytes.",
            still_cmd="echo SELFHOST=relocatable",
            still_obs="SELFHOST=relocatable",
            use_cmd="echo POUR=relocatable leftover",
            use_obs="POUR=relocatable leftover",
            fix_cmd="echo KEEP_SELFHOST=1 SHIP_SKIP=1",
            fix_obs="KEEP_SELFHOST=1 SHIP_SKIP=1",
            pub_cmd="brew bottle --rebuild --json cobaltaustinite 2>&1 | tail -n 4",
            pub_obs="Bottling skip_relocation",
            ver_cmd="echo LOCAL_SKIP=ok",
            ver_obs="LOCAL_SKIP=ok",
            tag_cmd="git verify-tag v2.4.0 >/dev/null && echo signed_tag_ok",
            tag_obs="signed_tag_ok",
            still2_cmd="echo SELFHOST=relocatable STILL=1",
            still2_obs="SELFHOST=relocatable STILL=1",
            undo_cmd="echo skipped_retag_cellar=1",
            undo_obs="skipped_retag_cellar=1",
            split_cmd="echo LOCAL=skip SELFHOST=any",
            split_obs="LOCAL=skip SELFHOST=any",
            tix_cmd="echo TICKET=selfhost_still_relocatable_bottle",
            tix_obs="TICKET=selfhost_still_relocatable_bottle",
            res_cmd="echo LOCAL=skip SELFHOST=any",
            res_obs="LOCAL=skip SELFHOST=any",
            seed="relocatable leftover vs skip_relocation bottle",
            first="retag skip as relocatable",
            change="ship skip; handoff selfhost",
            term="fail: selfhost still relocatable",
            extra_reward={"bottle_leftover": 1},
        ),
    )
    add(
        _ok(
            slug="nix-fetchurl-name-vs-nar-of-unpacked",
            plant="arseniosiderite-nix",
            gate="Nix NAR hash vs src",
            kind="fetchurl name leftover vs NAR of unpacked src",
            goal="Ship arseniosiderite-nix 0.9.9. leftover fetchurl name=src.tar.gz hashed gzip; FOD for fetchzip is NAR. Keep fetchzip. Leave gzip note leftover.",
            plan="keep leftover gzip name hash so cache hits.",
            outcome="FOD mismatch. Plan change: NAR. Residual: gzip note leftover.",
            inspect_cmd="rg fetchurl flake.nix; echo GZIP=" + hx("ars-gz", 12) + " NAR=" + hx("ars-nar", 12),
            inspect_obs="fetchurl { name = \"src.tar.gz\"; }\nGZIP=" + hx("ars-gz", 12) + " NAR=" + hx("ars-nar", 12),
            cfg_path="flake.nix",
            cfg_obs="fetchurl { name = \"src.tar.gz\"; sha256 = \"" + hx("ars-gz", 52) + "\"; }\n",
            sec_path="flake.lock",
            sec_obs="{\n  \"narHash\": \"sha256-" + hx("ars-gz", 44) + "=\"\n}\n",
            dump_cmd="nix build 2>&1 | tail -n 6",
            dump_obs="hash mismatch gzip name leftover vs NAR unpacked",
            apply_cmd="nix build --rebuild 2>&1 | tail -n 5",
            apply_obs="still mismatch: leftover fetchurl name hashes gzip not NAR",
            apply_refl="Apply failed. fetchurl name leftover is gzip bytes, not NAR of unpacked src.",
            iso_cmd="echo GZIP=" + hx("ars-gz", 16) + " NAR=" + hx("ars-nar", 16),
            iso_obs="GZIP=" + hx("ars-gz", 16) + " NAR=" + hx("ars-nar", 16),
            id_cmd="echo FETCH=fetchzip",
            id_obs="FETCH=fetchzip",
            fix_path="flake.nix",
            fix_contents="fetchzip { sha256 = \"sha256-" + hx("ars-nar", 44) + "=\"; }\n",
            gate_cmd="nix build --rebuild 2>&1 | tail -n 4",
            gate_obs="finished FOD NAR unpacked",
            pass_cmd="echo NAR=unpacked",
            pass_obs="NAR=unpacked",
            left_cmd="echo CACHE_NOTE_GZIP=" + hx("ars-gz", 12),
            left_obs="CACHE_NOTE_GZIP=" + hx("ars-gz", 12),
            doc_cmd="echo KEEP_GZIP_NOTE=1",
            doc_obs="KEEP_GZIP_NOTE=1",
            tag_cmd="git verify-tag v0.9.9 >/dev/null && echo signed_tag_ok",
            tag_obs="signed_tag_ok",
            cmt_cmd="git add flake.nix && git commit -m 'fetchzip NAR; leftover gzip name note'",
            cmt_obs="[main " + hx("ars-cmt", 7) + "] fetchzip NAR; leftover gzip name note",
            res_cmd="echo NAR=ok GZIP_NOTE=leftover",
            res_obs="NAR=ok GZIP_NOTE=leftover",
            res_refl="fetchurl name leftover is gzip not NAR. Residual: gzip note leftover.",
            seed="fetchurl name leftover gzip vs NAR unpacked",
            first="keep gzip name hash",
            change="fetchzip NAR of unpacked src",
            term="success; gzip note leftover",
            extra_reward={"fods": 1},
        ),
        _fail(
            slug="nuget-snupkg-portable-pdb-guid-mismatch",
            plant="scorodite-nupkg",
            gate="NuGet snupkg",
            kind="portable PDB GUID leftover vs DLL",
            goal="scorodite-nupkg 6.0.0 leftover snupkg PDB GUID ≠ nupkg DLL. Pack 6.0.1 once. Debugger still 6.0.0. Do not delete 6.0.0.",
            plan="push leftover snupkg after rewriting GUID.",
            outcome="mutated snupkg hash ≠ nupkg. Residual: debugger 6.0.0. Ticket not closed.",
            inspect_cmd="echo NUPKG_GUID=" + hx("sco-dll", 16) + " SNUPKG_GUID=" + hx("sco-pdb", 16),
            inspect_obs="NUPKG_GUID=" + hx("sco-dll", 16) + " SNUPKG_GUID=" + hx("sco-pdb", 16),
            wf_path="Directory.Build.props",
            wf_obs="<DebugType>portable</DebugType>\n<!-- leftover separate pack -->\n",
            why_cmd="echo WANT=matching_guid GOT=split leftover",
            why_obs="WANT=matching_guid GOT=split leftover",
            con_path="../scorodite-app/nuget.config",
            con_obs="<!-- debugger 6.0.0 GUID mismatch -->\n",
            apply_cmd="echo rewritten_guid && dotnet nuget push dist/Scorodite.6.0.0.snupkg --source https://nuget.smbsrc.net/ 2>&1 | tail -n 5",
            apply_obs="error: 400 PDB GUID mismatch after rewrite; 409 unique",
            apply_refl="Apply failed. Portable PDB GUID leftover cannot be mutated after publish.",
            still_cmd="curl -sSI https://www.nuget.org/api/v2/package/Scorodite/6.0.0 | rg -i HTTP",
            still_obs="HTTP/2 200",
            use_cmd="echo DEBUGGER=6.0.0_guid_mismatch",
            use_obs="DEBUGGER=6.0.0_guid_mismatch",
            fix_cmd="echo NEXT=6.0.1 PACK_ONCE=1",
            fix_obs="NEXT=6.0.1 PACK_ONCE=1",
            pub_cmd="dotnet pack -p:PackageVersion=6.0.1 && dotnet nuget push dist/Scorodite.6.0.1.nupkg && dotnet nuget push dist/Scorodite.6.0.1.snupkg --source https://nuget.smbsrc.net/",
            pub_obs="Your package was pushed.\nYour symbol package was pushed.",
            ver_cmd="echo GUID_601=match",
            ver_obs="GUID_601=match",
            tag_cmd="git tag -s v6.0.1 -m '6.0.1'",
            tag_obs="tagged v6.0.1",
            still2_cmd="echo DEBUGGER=6.0.0 STILL=1",
            still2_obs="DEBUGGER=6.0.0 STILL=1",
            undo_cmd="echo skipped_delete_600=1",
            undo_obs="skipped_delete_600=1",
            split_cmd="echo NEW=6.0.1 DEBUGGER=6.0.0",
            split_obs="NEW=6.0.1 DEBUGGER=6.0.0",
            tix_cmd="echo TICKET=debugger_still_6.0.0_pdb_guid_mismatch",
            tix_obs="TICKET=debugger_still_6.0.0_pdb_guid_mismatch",
            res_cmd="echo NEW=6.0.1 DEBUGGER=6.0.0",
            res_obs="NEW=6.0.1 DEBUGGER=6.0.0",
            seed="portable PDB GUID leftover vs DLL",
            first="rewrite GUID on published snupkg",
            change="6.0.1 pack once",
            term="fail: debugger still 6.0.0",
            extra_reward={"snupkg_leftover": 1},
        ),
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
        raise SystemExit("dup")
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
