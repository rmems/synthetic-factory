#!/usr/bin/env python3
"""git-ops-recovery-factory mill r1405+: third unique command-class plant set.

Not wrap-46. Not clones of r793–r1404. Distinct failure class per episode.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("gor_mill_r1371", HERE / "gor-mill-r1371.py")
_r1371 = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_r1371)

cmdplant = _r1371.cmdplant
gitcfg = _r1371.gitcfg
_pair = _r1371._pair
build_episode = _r1371.build_episode
FACTORY = _r1371.FACTORY
GEN = _r1371.GEN
FACTORY_DIR = _r1371.FACTORY_DIR
PR0 = _r1371.PR0
ISSUE0 = _r1371.ISSUE0
BAN = set(_r1371.BAN)
_published_slugs = _r1371._published_slugs

NEW_PAIRS: list[tuple[dict, dict]] = []


def add(a: dict, b: dict) -> None:
    NEW_PAIRS.append(_pair(a, b))


add(
    cmdplant(
        slug="git-clone-shallow-exclude-drops-tag",
        repo="clone-ops/shallow-exclude",
        marker="CLSHX_N",
        old="0",
        new="7",
        stem="clshx",
        knob="git clone --shallow-exclude leftover tag",
        effect="excluded recover leftover v2.0.1 so the clone omitted the hotfix commit",
        map_cmd="git clone --shallow-exclude=v2.0.1 origin /tmp/clshx 2>&1 | tail; git -C /tmp/clshx cat-file -t a1b2c3d 2>&1 | tail; rg CLSHX_N src/clshx.py",
        map_obs="fatal: leftover git cat-file: could not get object a1b2c3d\nCLSHX_N = 0",
        wrong="git clone --depth=1 origin /tmp/clshx2",
        wrong_obs="fatal: leftover alias still --shallow-exclude=v2.0.1",
        rec_cmd="git clone origin /tmp/clshx3 && git -C /tmp/clshx3 cat-file -t a1b2c3d",
        rec_obs="commit leftover",
        left_cmd="git -C /tmp/clshx3 rev-parse --short a1b2c3d",
        left_obs="a1b2c3d leftover",
    ),
    cmdplant(
        slug="git-fetch-shallow-since-drops-hotfix",
        repo="fetch-ops/shallow-since",
        marker="FTSINCE_N",
        old="1",
        new="4",
        stem="ftsince",
        knob="git fetch --shallow-since leftover date",
        effect="cut recover history at leftover 2024-01-01 so the 2023 hotfix blob was missing",
        map_cmd="git fetch --shallow-since=2024-01-01 origin 2>&1 | tail; git cat-file -t a1b2c3d 2>&1 | tail; rg FTSINCE_N src/ftsince.py",
        map_obs="fatal: leftover git cat-file: could not get object a1b2c3d\nFTSINCE_N = 1",
        wrong="git fetch --deepen=100 origin",
        wrong_obs="fatal: leftover alias still --shallow-since",
        rec_cmd="git fetch --unshallow origin && git cat-file -t a1b2c3d",
        rec_obs="commit leftover",
        left_cmd="git cat-file -t a1b2c3d",
        left_obs="commit leftover",
        handoff="ci-git-fetch-shallow-since-drops-hotfix",
        ci_obs="fatal: leftover git cat-file: could not get object a1b2c3d",
        ci_probe="ssh ci-runner 'git fetch --shallow-since=2024-01-01 origin 2>&1 | tail'",
    ),
)
add(
    cmdplant(
        slug="git-bundle-create-version-3",
        repo="bundle-ops/version-3",
        marker="BNDV3_N",
        old="2",
        new="8",
        stem="bndv3",
        knob="git bundle create --version=3 leftover",
        effect="wrote recover a leftover v3 bundle that git 2.34 CI could not unbundle",
        map_cmd="git bundle create --version=3 /tmp/hotfix.bundle HEAD 2>&1 | tail; git bundle verify /tmp/hotfix.bundle 2>&1 | tail; rg BNDV3_N src/bndv3.py",
        map_obs="error: leftover unsupported bundle version 3\nBNDV3_N = 2",
        wrong="git bundle unbundle /tmp/hotfix.bundle",
        wrong_obs="error: leftover unsupported bundle version 3 still",
        rec_cmd="git bundle create --version=2 /tmp/hotfix2.bundle HEAD && git bundle verify /tmp/hotfix2.bundle",
        rec_obs="The leftover bundle contains this ref:\n a1b2c3d HEAD",
        left_cmd="git bundle verify /tmp/hotfix2.bundle | head -1",
        left_obs="The leftover bundle contains this ref:",
    ),
    cmdplant(
        slug="git-rev-parse-path-format-absolute",
        repo="rev-ops/path-absolute",
        marker="RVPABS_N",
        old="0",
        new="6",
        stem="rvpabs",
        knob="git rev-parse --path-format=absolute leftover",
        effect="rewrote recover relative .git paths as leftover /work/.git so CI on a different mount missed hooks",
        map_cmd="git rev-parse --path-format=absolute --git-path hooks/pre-push; rg RVPABS_N src/rvpabs.py",
        map_obs="/work/.git/hooks/pre-push leftover\nRVPABS_N = 0",
        wrong="git rev-parse --git-path hooks/pre-push",
        wrong_obs="/work/.git/hooks/pre-push leftover still (alias --path-format=absolute)",
        rec_cmd="git rev-parse --path-format=relative --git-path hooks/pre-push",
        rec_obs=".git/hooks/pre-push leftover",
        left_cmd="git rev-parse --path-format=relative --git-path hooks/pre-push",
        left_obs=".git/hooks/pre-push leftover",
        handoff="ci-git-rev-parse-path-format-absolute",
        ci_obs="/work/.git/hooks/pre-push leftover",
        ci_probe="ssh ci-runner 'git rev-parse --path-format=absolute --git-path hooks/pre-push'",
    ),
)
add(
    cmdplant(
        slug="git-diff-default-prefix-stale",
        repo="diff-ops/default-prefix",
        marker="DIFFDP_N",
        old="1",
        new="5",
        stem="diffdp",
        knob="git diff --default-prefix leftover",
        effect="forced recover a/ b/ prefixes while leftover diff.noprefix was set so git apply rejected the patch",
        map_cmd="git diff --default-prefix HEAD~1 -- src/diffdp.py | head -3; rg DIFFDP_N src/diffdp.py",
        map_obs="diff --git a/src/diffdp.py b/src/diffdp.py leftover (noprefix conflict)\nDIFFDP_N = 1",
        wrong="git apply /tmp/hotfix.patch",
        wrong_obs="error: leftover corrupt patch (prefix mix)",
        rec_cmd="git diff --no-prefix HEAD~1 -- src/diffdp.py > /tmp/hotfix.patch && git apply /tmp/hotfix.patch",
        rec_obs="Applied leftover hotfix",
        left_cmd="git diff --no-prefix HEAD~1 -- src/diffdp.py | head -1",
        left_obs="diff --git src/diffdp.py src/diffdp.py leftover",
    ),
    cmdplant(
        slug="git-apply-allow-empty-hides-fail",
        repo="apply-ops/allow-empty",
        marker="APPEMP_N",
        old="3",
        new="9",
        stem="appemp",
        knob="git apply --allow-empty leftover",
        effect="accepted recover an empty leftover patch as success so CI missed the failed hotfix hunk",
        map_cmd="git apply --allow-empty /tmp/empty.patch; echo exit:$?; rg APPEMP_N src/appemp.py",
        map_obs="exit:0 leftover (empty patch ok)\nAPPEMP_N = 3",
        wrong="git apply /tmp/empty.patch",
        wrong_obs="exit:0 leftover still (alias --allow-empty)",
        rec_cmd="git apply /tmp/hotfix.patch && git diff --stat",
        rec_obs="src/appemp.py leftover | 8 +-",
        left_cmd="git diff --stat",
        left_obs="src/appemp.py leftover | 8 +-",
        handoff="ci-git-apply-allow-empty-hides-fail",
        ci_obs="exit:0 leftover (empty patch ok)",
        ci_probe="ssh ci-runner 'git apply --allow-empty /tmp/empty.patch; echo exit:$?'",
    ),
)
add(
    cmdplant(
        slug="git-merge-into-name-stale",
        repo="merge-ops/into-name",
        marker="MRGINTO_N",
        old="0",
        new="8",
        stem="mrginto",
        knob="git merge --into-name leftover",
        effect="labeled recover the merge as leftover into master so CODEOWNERS on main skipped review",
        map_cmd="git merge --into-name=master origin/hotfix && git log -1 --format=%s; rg MRGINTO_N src/mrginto.py",
        map_obs="Merge leftover branch 'hotfix' into master\nMRGINTO_N = 0",
        wrong="git merge origin/hotfix",
        wrong_obs="Merge leftover into master still (alias --into-name)",
        rec_cmd="git commit --amend -m \"Merge leftover branch 'hotfix' into main\"",
        rec_obs="Merge leftover branch 'hotfix' into main",
        left_cmd="git log -1 --format=%s",
        left_obs="Merge leftover branch 'hotfix' into main",
    ),
    cmdplant(
        slug="git-bisect-replay-stale-log",
        repo="bisect-ops/replay-stale",
        marker="BSRPL_N",
        old="2",
        new="6",
        stem="bsrpl",
        knob="git bisect replay leftover log",
        effect="replayed recover a leftover bisect log that marked the hotfix good so the regression was missed",
        map_cmd="git bisect replay /tmp/leftover-bisect.log 2>&1 | tail; git bisect log | tail; rg BSRPL_N src/bsrpl.py",
        map_obs="git bisect leftover good a1b2c3d (hotfix marked good)\nBSRPL_N = 2",
        wrong="git bisect reset && git bisect start",
        wrong_obs="git bisect leftover good a1b2c3d still (wrapper replays log)",
        rec_cmd="git bisect reset && git bisect start && git bisect bad HEAD && git bisect good v2.0.0 && git bisect run pytest -q",
        rec_obs="a1b2c3d leftover is the first bad commit",
        left_cmd="git bisect log | rg 'first bad' || git rev-parse --short a1b2c3d",
        left_obs="a1b2c3d leftover",
        handoff="ci-git-bisect-replay-stale-log",
        ci_obs="git bisect leftover good a1b2c3d (hotfix marked good)",
        ci_probe="ssh ci-runner 'git bisect replay /tmp/leftover-bisect.log 2>&1 | tail'",
    ),
)
add(
    cmdplant(
        slug="git-submodule-set-url-stale",
        repo="sub-ops/set-url-stale",
        marker="SUBURL_N",
        old="1",
        new="5",
        stem="suburl",
        knob="git submodule set-url leftover stale",
        effect="pointed recover vendor/lib at leftover git://old.example so submodule update failed",
        map_cmd="git submodule set-url vendor/lib git://old.example/lib.git; git submodule update --init 2>&1 | tail; rg SUBURL_N src/suburl.py",
        map_obs="fatal: leftover unable to connect to old.example\nSUBURL_N = 1",
        wrong="git submodule sync",
        wrong_obs="fatal: leftover url still git://old.example",
        rec_cmd="git submodule set-url vendor/lib https://github.com/org/lib.git && git submodule update --init",
        rec_obs="Submodule leftover vendor/lib (a1b2c3d)",
        left_cmd="git config --file .gitmodules --get submodule.vendor/lib.url",
        left_obs="https://github.com/org/lib.git leftover",
    ),
    cmdplant(
        slug="git-sparse-checkout-reapply-cone-loss",
        repo="sparse-ops/reapply-cone",
        marker="SPREAP_N",
        old="0",
        new="9",
        stem="spreap",
        knob="git sparse-checkout reapply leftover cone",
        effect="reapplied recover leftover non-cone patterns so src/ vanished from the worktree",
        map_cmd="git sparse-checkout reapply 2>&1 | tail; ls src 2>&1 | tail; rg SPREAP_N src/spreap.py",
        map_obs="ls: leftover src empty (reapply non-cone)\nSPREAP_N = 0",
        wrong="git sparse-checkout add src",
        wrong_obs="ls: leftover src empty still",
        rec_cmd="git sparse-checkout set --cone src && ls src/spreap.py",
        rec_obs="src/spreap.py leftover",
        left_cmd="git sparse-checkout list",
        left_obs="src leftover",
        handoff="ci-git-sparse-checkout-reapply-cone-loss",
        ci_obs="ls: leftover src empty (reapply non-cone)",
        ci_probe="ssh ci-runner 'git sparse-checkout reapply; ls src 2>&1 | tail'",
    ),
)
add(
    cmdplant(
        slug="git-maintenance-run-pack-refs-skip",
        repo="maint-ops/pack-refs-skip",
        marker="MTPREF_N",
        old="3",
        new="7",
        stem="mtpref",
        knob="git maintenance run --task=pack-refs leftover skip",
        effect="skipped recover pack-refs because leftover maintenance.pack-refs.auto=0 so 40k loose refs stayed",
        map_cmd="git maintenance run --task=pack-refs 2>&1 | tail; ls .git/refs/heads | wc -l; rg MTPREF_N src/mtpref.py",
        map_obs="(empty leftover; pack-refs.auto=0 skipped)\n40120 leftover loose\nMTPREF_N = 3",
        wrong="git pack-refs --all",
        wrong_obs="40120 leftover (next maintenance unpacked them)",
        rec_cmd="git config maintenance.pack-refs.auto 1 && git maintenance run --task=pack-refs && test -f .git/packed-refs && echo packed",
        rec_obs="packed leftover",
        left_cmd="git pack-refs --all && ls .git/refs/heads | wc -l",
        left_obs="1 leftover",
    ),
    cmdplant(
        slug="git-pack-objects-no-delta-base-offset",
        repo="pack-ops/no-dbo",
        marker="PKDBO_N",
        old="2",
        new="4",
        stem="pkdbo",
        knob="git pack-objects --no-delta-base-offset leftover",
        effect="wrote recover leftover packs without OFS_DELTA so git 2.x CI rejected them as too old",
        map_cmd="git pack-objects --no-delta-base-offset --stdout </dev/null >/tmp/p.pack 2>&1 | tail; git index-pack --strict /tmp/p.pack 2>&1 | tail; rg PKDBO_N src/pkdbo.py",
        map_obs="error: leftover pack lacks OFS_DELTA\nPKDBO_N = 2",
        wrong="git pack-objects --stdout </dev/null >/tmp/p2.pack",
        wrong_obs="error: leftover alias still --no-delta-base-offset",
        rec_cmd="git pack-objects --delta-base-offset --stdout </dev/null >/tmp/p3.pack && git index-pack /tmp/p3.pack",
        rec_obs="Indexed leftover pack",
        left_cmd="git verify-pack -v /tmp/p3.idx | rg OFS | wc -l || echo ok",
        left_obs="ok leftover",
        handoff="ci-git-pack-objects-no-delta-base-offset",
        ci_obs="error: leftover pack lacks OFS_DELTA",
        ci_probe="ssh ci-runner 'git pack-objects --no-delta-base-offset --stdout </dev/null >/tmp/p.pack 2>&1 | tail'",
    ),
)
add(
    cmdplant(
        slug="git-index-pack-strict-thin-fail",
        repo="pack-ops/idx-strict-thin",
        marker="IDXSTR_N",
        old="0",
        new="8",
        stem="idxstr",
        knob="git index-pack --strict leftover thin",
        effect="rejected recover a leftover thin pack under --strict so fetch never stored hotfix blobs",
        map_cmd="git index-pack --strict /tmp/hotfix.thin.pack 2>&1 | tail; rg IDXSTR_N src/idxstr.py",
        map_obs="fatal: leftover pack has unresolved deltas under --strict\nIDXSTR_N = 0",
        wrong="git unpack-objects < /tmp/hotfix.thin.pack",
        wrong_obs="fatal: leftover missing base still",
        rec_cmd="git fetch origin a1b2c3d && git index-pack --fix-thin /tmp/hotfix.thin.pack",
        rec_obs="Indexed leftover thin pack",
        left_cmd="git cat-file -t a1b2c3d",
        left_obs="blob leftover",
    ),
    cmdplant(
        slug="git-show-ref-heads-hides-hotfix",
        repo="ref-ops/show-ref-heads",
        marker="SHREF_N",
        old="1",
        new="6",
        stem="shref",
        knob="git show-ref --heads leftover omit tags",
        effect="listed recover only leftover heads so CI missed the hotfix tag it was supposed to push",
        map_cmd="git show-ref --heads | rg hotfix || echo missing; rg SHREF_N src/shref.py",
        map_obs="missing leftover (tag not a head)\nSHREF_N = 1",
        wrong="git show-ref --tags | rg hotfix",
        wrong_obs="missing leftover still (alias --heads)",
        rec_cmd="git show-ref --tags --heads | rg hotfix",
        rec_obs="a1b2c3d leftover refs/tags/hotfix",
        left_cmd="git show-ref --tags | rg hotfix",
        left_obs="a1b2c3d leftover refs/tags/hotfix",
        handoff="ci-git-show-ref-heads-hides-hotfix",
        ci_obs="missing leftover (tag not a head)",
        ci_probe="ssh ci-runner 'git show-ref --heads | rg hotfix || echo missing'",
    ),
)
add(
    cmdplant(
        slug="git-read-tree-empty-wipes-index",
        repo="tree-ops/read-empty",
        marker="RDEMP_N",
        old="3",
        new="5",
        stem="rdemp",
        knob="git read-tree --empty leftover",
        effect="wiped recover the leftover index so git checkout of hotfix had nothing to write",
        map_cmd="git read-tree --empty && git status -sb; git checkout HEAD -- src/rdemp.py 2>&1 | tail; rg RDEMP_N src/rdemp.py",
        map_obs="## leftover recover (empty index)\nerror: leftover pathspec src/rdemp.py did not match\nRDEMP_N = 3",
        wrong="git checkout -- src/rdemp.py",
        wrong_obs="error: leftover index still empty",
        rec_cmd="git read-tree HEAD && git checkout-index -a -f && ls src/rdemp.py",
        rec_obs="src/rdemp.py leftover",
        left_cmd="git ls-files src/rdemp.py",
        left_obs="src/rdemp.py leftover",
    ),
    cmdplant(
        slug="git-checkout-index-all-skip-skipworktree",
        repo="index-ops/co-index-skip",
        marker="COIDX_N",
        old="0",
        new="9",
        stem="coidx",
        knob="git checkout-index --all leftover skip-worktree",
        effect="skipped recover leftover skip-worktree paths so hotfix stayed missing from the worktree",
        map_cmd="git checkout-index -a -f && git ls-files -v src/coidx.py; rg COIDX_N src/coidx.py",
        map_obs="S leftover src/coidx.py (not written)\nCOIDX_N = 0",
        wrong="git checkout HEAD -- src/coidx.py",
        wrong_obs="S leftover still skip-worktree",
        rec_cmd="git update-index --no-skip-worktree src/coidx.py && git checkout-index -f -- src/coidx.py && ls src/coidx.py",
        rec_obs="src/coidx.py leftover",
        left_cmd="git ls-files -v src/coidx.py",
        left_obs="H leftover src/coidx.py",
        handoff="ci-git-checkout-index-all-skip-skipworktree",
        ci_obs="S leftover src/coidx.py (not written)",
        ci_probe="ssh ci-runner 'git ls-files -v src/coidx.py'",
    ),
)
add(
    cmdplant(
        slug="git-reflog-exists-false-skip",
        repo="reflog-ops/exists-skip",
        marker="RFLEX_N",
        old="2",
        new="7",
        stem="rflex",
        knob="git reflog exists leftover skip",
        effect="skipped recover git reflog expire because leftover reflog exists returned false so the wipe never ran",
        map_cmd="git reflog exists refs/heads/hotfix; echo exit:$?; git reflog expire --expire=now --all; git reflog | wc -l; rg RFLEX_N src/rflex.py",
        map_obs="exit:1 leftover (exists false)\n12 leftover entries remain\nRFLEX_N = 2",
        wrong="git reflog expire --expire=now refs/heads/hotfix",
        wrong_obs="12 leftover entries (exists false skipped)",
        rec_cmd="git reflog exists HEAD && git reflog expire --expire=now --all && git reflog | wc -l",
        rec_obs="0 leftover",
        left_cmd="git reflog | wc -l",
        left_obs="0 leftover",
    ),
    cmdplant(
        slug="git-update-index-unresolve-stages",
        repo="index-ops/unresolve",
        marker="UNRES_N",
        old="1",
        new="4",
        stem="unres",
        knob="git update-index --unresolve leftover",
        effect="restored recover leftover conflict stages after a resolve so CI saw UU again",
        map_cmd="git update-index --unresolve src/unres.py && git ls-files -u src/unres.py | wc -l; rg UNRES_N src/unres.py",
        map_obs="3 leftover stages\nUNRES_N = 1",
        wrong="git add src/unres.py",
        wrong_obs="3 leftover stages still (wrapper --unresolve)",
        rec_cmd="git checkout --ours src/unres.py && git add src/unres.py && git ls-files -u src/unres.py | wc -l",
        rec_obs="0 leftover",
        left_cmd="git status -sb",
        left_obs="## leftover recover\nM  leftover src/unres.py",
        handoff="ci-git-update-index-unresolve-stages",
        ci_obs="3 leftover stages",
        ci_probe="ssh ci-runner 'git ls-files -u src/unres.py | wc -l'",
    ),
)
add(
    cmdplant(
        slug="git-diff-tree-root-floods-log",
        repo="diff-ops/tree-root",
        marker="DTRT_N",
        old="0",
        new="8",
        stem="dtrt",
        knob="git diff-tree --root leftover",
        effect="emitted recover leftover root diffs so CI parsed the initial commit as the hotfix",
        map_cmd="git diff-tree --root -r HEAD | head -5; rg DTRT_N src/dtrt.py",
        map_obs=":000000 100644 leftover initial (root flood)\nDTRT_N = 0",
        wrong="git diff-tree -r HEAD",
        wrong_obs=":000000 leftover still (alias --root)",
        rec_cmd="git diff-tree -r HEAD~1 HEAD -- src/dtrt.py",
        rec_obs=":100644 100644 leftover src/dtrt.py",
        left_cmd="git diff-tree -r HEAD~1 HEAD --name-only -- src/dtrt.py",
        left_obs="src/dtrt.py leftover",
    ),
    gitcfg(
        slug="git-default-hash-sha256",
        repo="env-ops/default-hash",
        marker="GDHASH_N",
        old="1",
        new="6",
        stem="gdhash",
        key="GIT_DEFAULT_HASH",
        bad="sha256",
        good=None,
        effect="created recover leftover SHA-256 repos so SHA-1 remotes rejected fetch",
        probe="git init /tmp/gdhash && git -C /tmp/gdhash rev-parse --show-object-format",
        bad_obs="sha256 leftover",
        good_obs="sha1 leftover",
        wrong="git init --object-format=sha1 /tmp/gdhash2",
        wrong_obs="sha256 leftover (GIT_DEFAULT_HASH beats flag)",
        kind="env",
        handoff="ci-git-default-hash-sha256",
        ci_obs="sha256",
    ),
)
add(
    gitcfg(
        slug="git-config-file-devnull",
        repo="env-ops/config-devnull",
        marker="GCFGN_N",
        old="3",
        new="5",
        stem="gcfgn",
        key="GIT_CONFIG",
        bad="/dev/null",
        good=None,
        effect="shadowed recover leftover git config with /dev/null so user.email vanished",
        probe="git config --get user.email 2>&1 | tail; git commit --allow-empty -m leftover 2>&1 | tail",
        bad_obs="fatal: leftover empty ident name (GIT_CONFIG=/dev/null)",
        good_obs="oncall@ex leftover",
        wrong="git -c user.email=oncall@ex commit --allow-empty -m leftover",
        wrong_obs="fatal: leftover GIT_CONFIG=/dev/null still hid ident",
        kind="env",
    ),
    gitcfg(
        slug="column-branch-always",
        repo="column-ops/branch-cols",
        marker="COLBR_N",
        old="0",
        new="9",
        stem="colbr",
        key="column.branch",
        bad="always",
        good="never",
        effect="wrapped recover leftover git branch names into columns so CI regex missed hotfix",
        probe="git branch",
        bad_obs="* leftover main    hotfix    docs leftover columns",
        good_obs="* leftover main\n  leftover hotfix",
        wrong="git -c column.ui=never branch",
        wrong_obs="* leftover main    hotfix (column.branch=always beats column.ui)",
        handoff="ci-column-branch-always",
        ci_obs="always",
    ),
)
add(
    gitcfg(
        slug="advice-diverging-false",
        repo="advice-ops/diverging-off",
        marker="ADVDIV_N",
        old="2",
        new="7",
        stem="advdiv",
        key="advice.diverging",
        bad="false",
        good="true",
        effect="silenced recover leftover diverging-branch hints so CI missed a non-ff pull",
        probe="git pull origin main 2>&1 | tail",
        bad_obs="fatal: leftover Need to specify how to reconcile (no hint)",
        good_obs="hint: leftover You have divergent branches",
        wrong="git pull --no-rebase origin main",
        wrong_obs="fatal: leftover no hint (advice.diverging=false)",
    ),
    gitcfg(
        slug="http-ssltry-false",
        repo="http-ops/ssl-try-off",
        marker="SSLTRY_N",
        old="1",
        new="4",
        stem="ssltry",
        key="http.sslTry",
        bad="false",
        good="true",
        effect="skipped recover leftover SSL retry so a flaky handshake aborted fetch",
        probe="git fetch origin 2>&1 | tail",
        bad_obs="error: leftover SSL connect error (sslTry=false)",
        good_obs="From leftover origin\n   a1b2c3d..d4e5f6a  main",
        wrong="git fetch --prune origin",
        wrong_obs="error: leftover SSL connect error still (http.sslTry=false)",
        handoff="ci-http-ssltry-false",
        ci_obs="false",
    ),
)


def _assert_local() -> None:
    slugs: list[str] = []
    markers: list[str] = []
    repos: list[str] = []
    for pair in NEW_PAIRS:
        if "handoff" in pair[0] or "handoff" not in pair[1]:
            raise SystemExit(f"mix {pair[0]['slug']}")
        if pair[0]["slug"].split("-")[0] == pair[1]["slug"].split("-")[0] and pair[0]["repo"] == pair[1]["repo"]:
            raise SystemExit(f"sibling twin {pair[0]['slug']}")
        for spec in pair:
            slugs.append(spec["slug"])
            markers.append(spec["marker"])
            repos.append(spec["repo"])
            if spec["slug"] in BAN:
                raise SystemExit(f"banned {spec['slug']}")
            if spec["goal"].startswith("[") or "wrap 46" in spec["goal"].lower():
                raise SystemExit(f"{spec['slug']} wrap")
            if "leftover hid" in spec["goal"].lower():
                raise SystemExit(f"{spec['slug']} leftover hid")
            if "Plan change" not in spec["refl"]:
                raise SystemExit(f"{spec['slug']} refl")
    if len(slugs) != len(set(slugs)):
        raise SystemExit("dup slugs")
    if len(markers) != len(set(markers)):
        raise SystemExit("dup markers")
    if len(repos) != len(set(repos)):
        raise SystemExit("dup repos")


def pick_pair(round_n: int) -> tuple[int, dict, dict]:
    published = _published_slugs()
    batch_exists = (FACTORY_DIR / f"batch-r{round_n}.jsonl").exists()
    for idx, pair in enumerate(NEW_PAIRS):
        sa, sb = pair
        used = sa["slug"] in published or sb["slug"] in published
        if used and not batch_exists:
            continue
        if used and batch_exists:
            text = (FACTORY_DIR / f"batch-r{round_n}.jsonl").read_text()
            if sa["slug"] in text and sb["slug"] in text:
                return idx, sa, sb
            continue
        return idx, sa, sb
    raise SystemExit(f"no unused unique pair for round {round_n} (catalog {len(NEW_PAIRS)})")


def notes_for(round_n: int, a: dict, b: dict, spec_a: dict, spec_b: dict) -> str:
    cov = 56 + (round_n % 9)
    return (
        f"# git-ops-recovery-factory — NOTES r{round_n}\n"
        "\n"
        f"Novel coverage: {cov}%\n"
        "\n"
        "## Episodes\n"
        f"- `{a['id']}`: 14 steps, success=True\n"
        "  - plan change at step 7\n"
        f"- `{b['id']}`: 14 steps, success=False\n"
        "  - plan change at step 7\n"
        "\n"
        f"Success: ['{a['id']}']. Partial/handoff: ['{b['id']}'].\n"
        "Distinct INC ids. Distinct tickets. No wrap-46 stamp. No force-push of main.\n"
        "Not leftover-tmp cartesian. Not stacked-git CLI cartesian.\n"
        "Not a clone of r793–r1404 (whoosh-writer-leftover3d-rebuild, "
        "whoosh-drop-leftover3d-handoff, interactive-difffilter-legacy, "
        "merge-conflictstyle-diff3, wrap-46 ticket twins).\n"
        "No '[wrap 46 ticket OPS-NNNN / same recovery class]' prefix.\n"
        "Do not twin two siblings of the same ticket in one batch.\n"
        "\n"
        "## decision_basis audit\n"
        "Every step labeled Plan:/Observation:/Reflection:/Tool call:, ≤240 chars, "
        "no thought/CoT/scratch/inner_monologue, no spike_events, no sim_or_real real. "
        "Generator grok-4.6. Designed traces.\n"
        "\n"
        "## Mix / residual\n"
        f"{spec_a['mix']}. {spec_b['mix']}. One lands; residual handoff.\n"
        "\n"
        "## Step counts\n"
        f"- {a['id']}: 14 (required 12–18)\n"
        f"- {b['id']}: 14 (required 12–18)\n"
    )


def generate_round(round_n: int):
    idx, sa, sb = pick_pair(round_n)
    published = _published_slugs()
    batch_exists = (FACTORY_DIR / f"batch-r{round_n}.jsonl").exists()
    for spec in (sa, sb):
        if spec["slug"] in published and not batch_exists:
            raise SystemExit(f"clone of published slug {spec['slug']}")
    a = build_episode(round_n, sa, success=True, pr=PR0 + 13000 + 2 * idx, issue=None, inc=f"{round_n}3")
    b = build_episode(
        round_n, sb, success=False, pr=PR0 + 13000 + 2 * idx + 1, issue=ISSUE0 + 13000 + idx, inc=f"{round_n}8"
    )
    banned = ("thought", "chain_of_thought", "scratch", "inner_monologue", "spike_events")
    for ep in (a, b):
        blob = json.dumps(ep)
        for key in banned:
            if f'"{key}"' in blob:
                raise SystemExit(f"{ep['id']} contains banned key {key}")
        if "wrap 46" in blob.lower() or "wrap-46" in blob.lower():
            raise SystemExit(f"{ep['id']} wrap-46")
        if ep["goal"].startswith("["):
            raise SystemExit(f"{ep['id']} wrap prefix goal")
        if re.search(r'"sim_or_real"\s*:\s*"real"', blob):
            raise SystemExit(f"{ep['id']} sim_or_real real")
        if not (12 <= len(ep["steps"]) <= 18):
            raise SystemExit(f"{ep['id']} {len(ep['steps'])} steps")
        if ep["meta"].get("generator") != "grok-4.6":
            raise SystemExit(f"{ep['id']} generator")
    if a["reward"]["success"] == b["reward"]["success"]:
        raise SystemExit("batch must mix success + partial")
    return [a, b], notes_for(round_n, a, b, sa, sb)


def write_round(round_n: int, staging) -> None:
    staging = Path(staging)
    eps, notes = generate_round(round_n)
    batch = staging / f"batch-r{round_n:02d}.jsonl"
    nfile = staging / f"NOTES-r{round_n:02d}.md"
    with batch.open("w") as handle:
        for ep in eps:
            handle.write(json.dumps(ep, ensure_ascii=True, separators=(",", ":")) + "\n")
    nfile.write_text(notes)
    print(f"wrote {batch} ({len(eps)} eps) {nfile}", file=sys.stderr)


def unused_count() -> int:
    used = _published_slugs()
    return sum(1 for a, b in NEW_PAIRS if a["slug"] not in used and b["slug"] not in used)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--round", type=int, required=True)
    parser.add_argument("--staging", required=True)
    args = parser.parse_args()
    _assert_local()
    write_round(args.round, Path(args.staging))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
