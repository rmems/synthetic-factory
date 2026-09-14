#!/usr/bin/env python3
"""git-ops-recovery-factory mill r1371+: second unique command-class plant set.

Not wrap-46. Not clones of r793–r1370. Distinct failure class per episode.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("gor_mill_r1278", HERE / "gor-mill-r1278.py")
_r1278 = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_r1278)

gitcfg = _r1278.gitcfg
cmdplant = _r1278.cmdplant
_pair = _r1278._pair
build_episode = _r1278.build_episode
FACTORY = _r1278.FACTORY
GEN = _r1278.GEN
FACTORY_DIR = _r1278.FACTORY_DIR
PR0 = _r1278.PR0
ISSUE0 = _r1278.ISSUE0
BAN = set(_r1278.BAN)
_trim = _r1278._trim
_published_slugs = _r1278._published_slugs

NEW_PAIRS: list[tuple[dict, dict]] = []


def add(a: dict, b: dict) -> None:
    NEW_PAIRS.append(_pair(a, b))


add(
    cmdplant(
        slug="git-last-modified-pathspec-stale",
        repo="mod-ops/last-modified",
        marker="LASTMOD_N",
        old="0",
        new="7",
        stem="lastmod",
        knob="git last-modified leftover pathspec",
        effect="reported recover src/lastmod.py as unchanged because leftover pathspec excluded it",
        map_cmd="git last-modified -- src ':!src/lastmod.py' 2>&1 | tail; rg LASTMOD_N src/lastmod.py",
        map_obs="(empty leftover; pathspec skipped hotfix)\nLASTMOD_N = 0",
        wrong="git log -1 --format=%ci -- src/lastmod.py",
        wrong_obs="(empty leftover alias still ':!src/lastmod.py')",
        rec_cmd="git last-modified -- src/lastmod.py && git log -1 --format=%ci -- src/lastmod.py",
        rec_obs="a1b2c3d leftover 2026-08-19",
        left_cmd="git last-modified -- src/lastmod.py | wc -l",
        left_obs="1 leftover",
    ),
    cmdplant(
        slug="git-refs-verify-skip-corrupt",
        repo="refs-ops/verify-skip",
        marker="REFVFY_N",
        old="1",
        new="4",
        stem="refvfy",
        knob="git refs verify leftover skip",
        effect="skipped recover refs verify so a leftover truncated reftable stayed on disk",
        map_cmd="git refs verify 2>&1 | tail; rg REFVFY_N src/refvfy.py",
        map_obs="warning: leftover reftable truncated (ignored)\nREFVFY_N = 1",
        wrong="git refs migrate --ref-format=files",
        wrong_obs="warning: leftover reftable truncated still",
        rec_cmd="rm -rf .git/reftable && git refs migrate --ref-format=files && git refs verify",
        rec_obs="ok leftover",
        left_cmd="git refs verify; echo $?",
        left_obs="ok leftover\n0",
        handoff="ci-git-refs-verify-skip-corrupt",
        ci_obs="warning: leftover reftable truncated (ignored)",
        ci_probe="ssh ci-runner 'git refs verify 2>&1 | tail'",
    ),
)
add(
    cmdplant(
        slug="git-hook-list-hookspath-stale",
        repo="hook-ops/list-path",
        marker="HKLIST_N",
        old="2",
        new="8",
        stem="hklist",
        knob="git hook list leftover core.hooksPath",
        effect="listed recover hooks from leftover /opt/legacy/hooks so pre-push never ran",
        map_cmd="git hook list 2>&1 | tail; git config --get core.hooksPath; rg HKLIST_N src/hklist.py",
        map_obs="pre-push leftover /opt/legacy/hooks/pre-push (missing)\n/opt/legacy/hooks\nHKLIST_N = 2",
        wrong="git hook run pre-push",
        wrong_obs="fatal: leftover cannot run /opt/legacy/hooks/pre-push",
        rec_cmd="git config --unset core.hooksPath && git hook list",
        rec_obs="pre-push leftover .git/hooks/pre-push",
        left_cmd="git config --get core.hooksPath; echo exit:$?",
        left_obs="exit:1 leftover",
    ),
    cmdplant(
        slug="git-fetch-negotiate-only-stale",
        repo="fetch-ops/negotiate-only",
        marker="FTNEG_N",
        old="0",
        new="6",
        stem="ftneg",
        knob="git fetch --negotiate-only leftover",
        effect="ran recover fetch --negotiate-only against leftover origin so no objects arrived",
        map_cmd="git fetch --negotiate-only origin 2>&1 | tail; git cat-file -t a1b2c3d 2>&1 | tail; rg FTNEG_N src/ftneg.py",
        map_obs="negotiated leftover; no objects\nfatal: leftover git cat-file: could not get object a1b2c3d\nFTNEG_N = 0",
        wrong="git fetch --dry-run origin",
        wrong_obs="negotiated leftover still (alias --negotiate-only)",
        rec_cmd="git fetch origin a1b2c3d && git cat-file -t a1b2c3d",
        rec_obs="commit leftover",
        left_cmd="git cat-file -t a1b2c3d",
        left_obs="commit leftover",
        handoff="ci-git-fetch-negotiate-only-stale",
        ci_obs="negotiated leftover; no objects",
        ci_probe="ssh ci-runner 'git fetch --negotiate-only origin 2>&1 | tail'",
    ),
)
add(
    cmdplant(
        slug="git-fetch-atomic-partial-fail",
        repo="fetch-ops/atomic-fail",
        marker="FTATM_N",
        old="3",
        new="5",
        stem="ftatm",
        knob="git fetch --atomic leftover partial",
        effect="aborted recover the whole leftover fetch because one remote ref was missing so hotfix never updated",
        map_cmd="git fetch --atomic origin main hotfix-gone 2>&1 | tail; git rev-parse --short hotfix; rg FTATM_N src/ftatm.py",
        map_obs="error: leftover couldn't find remote ref hotfix-gone (atomic rolled back)\nd4e5f6a leftover old\nFTATM_N = 3",
        wrong="git fetch origin main",
        wrong_obs="error: leftover alias still --atomic with hotfix-gone",
        rec_cmd="git fetch origin main hotfix && git rev-parse --short hotfix",
        rec_obs="a1b2c3d leftover",
        left_cmd="git rev-parse --abbrev-ref hotfix; git rev-parse --short hotfix",
        left_obs="hotfix\na1b2c3d leftover",
    ),
    cmdplant(
        slug="git-push-atomic-one-reject",
        repo="push-ops/atomic-reject",
        marker="PSHATM_N",
        old="1",
        new="9",
        stem="pshatm",
        knob="git push --atomic leftover one reject",
        effect="rolled recover every leftover ref back because docs failed non-ff so hotfix never landed",
        map_cmd="git push --atomic origin hotfix docs 2>&1 | tail; git ls-remote origin hotfix; rg PSHATM_N src/pshatm.py",
        map_obs="error: leftover atomic push failed (docs non-ff); hotfix rolled back\n(empty leftover remote hotfix)\nPSHATM_N = 1",
        wrong="git push origin hotfix",
        wrong_obs="error: leftover alias still --atomic with docs",
        rec_cmd="git push origin hotfix && git ls-remote origin hotfix",
        rec_obs="a1b2c3d leftover refs/heads/hotfix",
        left_cmd="git ls-remote --heads origin | rg hotfix",
        left_obs="a1b2c3d leftover refs/heads/hotfix",
        handoff="ci-git-push-atomic-one-reject",
        ci_obs="error: leftover atomic push failed (docs non-ff); hotfix rolled back",
        ci_probe="ssh ci-runner 'git push --atomic origin hotfix docs 2>&1 | tail'",
    ),
)
add(
    cmdplant(
        slug="git-stash-pathspec-from-file-crlf",
        repo="stash-ops/pathspec-crlf",
        marker="STPS_N",
        old="0",
        new="8",
        stem="stps",
        knob="git stash --pathspec-from-file leftover CRLF",
        effect="parsed recover stash pathspec with leftover CRLF so src/stps.py\\r was missing and secrets stayed dirty",
        map_cmd="printf 'src/stps.py\\r\\n' > /tmp/ps && git stash push --pathspec-from-file=/tmp/ps 2>&1 | tail; rg STPS_N src/stps.py",
        map_obs="fatal: leftover pathspec 'src/stps.py\\r' did not match\nSTPS_N = 0",
        wrong="git stash push -- src/stps.py",
        wrong_obs="fatal: leftover wrapper still --pathspec-from-file CRLF",
        rec_cmd="printf 'src/stps.py\\n' > /tmp/ps && git stash push --pathspec-from-file=/tmp/ps && git stash list | head",
        rec_obs="stash@{0}: leftover On recover: src/stps.py",
        left_cmd="git stash show --name-only stash@{0}",
        left_obs="src/stps.py leftover",
    ),
    cmdplant(
        slug="git-shortlog-group-committer",
        repo="log-ops/shortlog-group",
        marker="SHLOG_N",
        old="2",
        new="6",
        stem="shlog",
        knob="git shortlog --group=committer leftover",
        effect="grouped recover shortlog by leftover committer so the author hotfix count was zero",
        map_cmd="git shortlog --group=committer HEAD~20..HEAD | head; rg SHLOG_N src/shlog.py",
        map_obs="Legacy Bot leftover (20):\n      hotfix recover\nSHLOG_N = 2",
        wrong="git shortlog --group=author HEAD~20..HEAD",
        wrong_obs="Legacy Bot leftover still (alias --group=committer)",
        rec_cmd="git shortlog HEAD~20..HEAD | rg Oncall",
        rec_obs="Oncall leftover (12):",
        left_cmd="git shortlog -sn HEAD~20..HEAD | head",
        left_obs="12 leftover Oncall",
        handoff="ci-git-shortlog-group-committer",
        ci_obs="Legacy Bot leftover (20):",
        ci_probe="ssh ci-runner 'git shortlog --group=committer HEAD~20..HEAD | head'",
    ),
)
add(
    cmdplant(
        slug="git-unpack-objects-strict-fail",
        repo="pack-ops/unpack-strict",
        marker="UNPK_N",
        old="1",
        new="5",
        stem="unpk",
        knob="git unpack-objects --strict leftover",
        effect="rejected recover a leftover thin pack under --strict so hotfix blobs never loosened",
        map_cmd="git unpack-objects --strict < /tmp/hotfix.pack 2>&1 | tail; rg UNPK_N src/unpk.py",
        map_obs="fatal: leftover unpack-objects: unresolved deltas under --strict\nUNPK_N = 1",
        wrong="git unpack-objects < /tmp/hotfix.pack",
        wrong_obs="fatal: leftover alias still --strict",
        rec_cmd="git unpack-objects < /tmp/hotfix.pack && git cat-file -t a1b2c3d",
        rec_obs="blob leftover",
        left_cmd="git cat-file -t a1b2c3d",
        left_obs="blob leftover",
    ),
    cmdplant(
        slug="git-prune-packed-drops-loose",
        repo="pack-ops/prune-packed",
        marker="PRNPK_N",
        old="3",
        new="9",
        stem="prnpk",
        knob="git prune-packed leftover",
        effect="deleted recover leftover loose hotfix blobs that were not actually in a pack",
        map_cmd="git prune-packed -n 2>&1 | tail; git cat-file -t a1b2c3d 2>&1 | tail; rg PRNPK_N src/prnpk.py",
        map_obs="Would leftover remove .git/objects/a1/b2c3d\nfatal: leftover git cat-file after prune-packed\nPRNPK_N = 3",
        wrong="git prune-packed",
        wrong_obs="fatal: leftover object already pruned",
        rec_cmd="git fetch origin a1b2c3d && git cat-file -t a1b2c3d",
        rec_obs="commit leftover",
        left_cmd="git cat-file -t a1b2c3d",
        left_obs="commit leftover",
        handoff="ci-git-prune-packed-drops-loose",
        ci_obs="fatal: leftover git cat-file after prune-packed",
        ci_probe="ssh ci-runner 'git prune-packed -n | tail'",
    ),
)
add(
    cmdplant(
        slug="git-verify-pack-stat-only",
        repo="pack-ops/verify-stat",
        marker="VFYPACK_N",
        old="0",
        new="8",
        stem="vfypack",
        knob="git verify-pack leftover --stat-only skip",
        effect="printed recover pack stats without leftover SHA checks so a corrupt hotfix blob stayed packed",
        map_cmd="git verify-pack --stat-only .git/objects/pack/*.idx 2>&1 | tail; rg VFYPACK_N src/vfypack.py",
        map_obs="non delta leftover 12 objects\nVFYPACK_N = 0",
        wrong="git verify-pack .git/objects/pack/*.idx",
        wrong_obs="non delta leftover (wrapper still --stat-only)",
        rec_cmd="git verify-pack -v .git/objects/pack/*.idx | rg error || echo ok",
        rec_obs="error leftover: SHA1 mismatch a1b2c3d",
        left_cmd="git verify-pack -v .git/objects/pack/*.idx | rg -c error || echo 0",
        left_obs="1 leftover",
    ),
    cmdplant(
        slug="git-mailsplit-mboxrd-stale",
        repo="mail-ops/mailsplit-mboxrd",
        marker="MLSPLIT_N",
        old="2",
        new="6",
        stem="mlsplit",
        knob="git mailsplit leftover mboxrd skip",
        effect="split recover a leftover mboxrd without --keep-cr so cover From_ lines ate the first patch",
        map_cmd="git mailsplit -o/tmp/mbox /tmp/series.mbox 2>&1 | tail; ls /tmp/mbox | wc -l; rg MLSPLIT_N src/mlsplit.py",
        map_obs="1 leftover (cover From_ swallowed 0001)\nMLSPLIT_N = 2",
        wrong="git mailsplit --keep-cr -o/tmp/mbox2 /tmp/series.mbox",
        wrong_obs="1 leftover still (alias omitted --mboxrd)",
        rec_cmd="git mailsplit --mboxrd -o/tmp/mbox3 /tmp/series.mbox && ls /tmp/mbox3 | wc -l",
        rec_obs="3 leftover",
        left_cmd="ls /tmp/mbox3 | wc -l",
        left_obs="3 leftover",
        handoff="ci-git-mailsplit-mboxrd-stale",
        ci_obs="1 leftover (cover From_ swallowed 0001)",
        ci_probe="ssh ci-runner 'git mailsplit -o/tmp/mbox /tmp/series.mbox | tail'",
    ),
)
add(
    cmdplant(
        slug="git-send-pack-force-stale",
        repo="send-ops/force-stale",
        marker="SNDPK_N",
        old="1",
        new="5",
        stem="sndpk",
        knob="git send-pack leftover --force",
        effect="forced recover send-pack of leftover main so the remote non-ff hotfix was overwritten",
        map_cmd="git send-pack --force origin refs/heads/hotfix:refs/heads/main 2>&1 | tail; rg SNDPK_N src/sndpk.py",
        map_obs="+ a1b2c3d...d4e5f6a leftover main (forced)\nSNDPK_N = 1",
        wrong="git push --force-with-lease origin hotfix:main",
        wrong_obs="+ leftover forced still (alias send-pack --force)",
        rec_cmd="git send-pack origin refs/heads/hotfix:refs/heads/hotfix && git ls-remote origin hotfix",
        rec_obs="a1b2c3d leftover refs/heads/hotfix",
        left_cmd="git ls-remote --heads origin | rg 'main|hotfix'",
        left_obs="d4e5f6a leftover refs/heads/main\na1b2c3d leftover refs/heads/hotfix",
    ),
    cmdplant(
        slug="git-http-fetch-recover-pack",
        repo="http-ops/http-fetch",
        marker="HTFETCH_N",
        old="0",
        new="9",
        stem="htfetch",
        knob="git http-fetch leftover recover pack",
        effect="fetched recover a leftover pack over dumb HTTP into the wrong GIT_DIR so objects vanished",
        map_cmd="GIT_DIR=/tmp/leftover.git git http-fetch --recover a1b2c3d https://leftover.example/repo.git/ 2>&1 | tail; rg HTFETCH_N src/htfetch.py",
        map_obs="fatal: leftover not a git repository /tmp/leftover.git\nHTFETCH_N = 0",
        wrong="git http-fetch a1b2c3d https://leftover.example/repo.git/",
        wrong_obs="fatal: leftover GIT_DIR still /tmp/leftover.git",
        rec_cmd="unset GIT_DIR && git fetch origin a1b2c3d && git cat-file -t a1b2c3d",
        rec_obs="commit leftover",
        left_cmd="git cat-file -t a1b2c3d",
        left_obs="commit leftover",
        handoff="ci-git-http-fetch-recover-pack",
        ci_obs="fatal: leftover not a git repository /tmp/leftover.git",
        ci_probe="ssh ci-runner 'GIT_DIR=/tmp/leftover.git git http-fetch --recover a1b2c3d https://leftover.example/repo.git/ 2>&1 | tail'",
    ),
)
add(
    cmdplant(
        slug="git-credential-reject-clears-store",
        repo="cred-ops/reject-store",
        marker="CRDREJ_N",
        old="2",
        new="7",
        stem="crdrej",
        knob="git credential reject leftover store",
        effect="wiped recover the leftover credential store so the next fetch had no token",
        map_cmd="printf 'url=https://github.com/org/app.git\\n' | git credential reject; git credential fill 2>&1 | tail; rg CRDREJ_N src/crdrej.py",
        map_obs="fatal: leftover could not read username (store empty)\nCRDREJ_N = 2",
        wrong="git credential approve",
        wrong_obs="fatal: leftover store still empty",
        rec_cmd="printf 'url=https://github.com/org/app.git\\nusername=oncall\\npassword=ok\\n' | git credential approve && echo url=https://github.com/org/app.git | git credential fill | rg username",
        rec_obs="username=oncall leftover",
        left_cmd="echo url=https://github.com/org/app.git | git credential fill | rg username",
        left_obs="username=oncall leftover",
    ),
    cmdplant(
        slug="git-restore-overlay-stale-index",
        repo="restore-ops/overlay-stale",
        marker="RSTOV_N",
        old="1",
        new="4",
        stem="rstov",
        knob="git restore --overlay leftover stale index",
        effect="restored recover paths in overlay mode so leftover deleted files came back from HEAD~20",
        map_cmd="git restore --overlay --source=HEAD~20 -- src; ls src/deleted.py 2>&1 | tail; rg RSTOV_N src/rstov.py",
        map_obs="src/deleted.py leftover resurrected\nRSTOV_N = 1",
        wrong="git restore --source=HEAD -- src/rstov.py",
        wrong_obs="src/deleted.py leftover still (alias --overlay)",
        rec_cmd="git restore --no-overlay --source=HEAD -- src && test ! -f src/deleted.py && echo gone",
        rec_obs="gone leftover",
        left_cmd="test ! -f src/deleted.py && echo gone",
        left_obs="gone leftover",
        handoff="ci-git-restore-overlay-stale-index",
        ci_obs="src/deleted.py leftover resurrected",
        ci_probe="ssh ci-runner 'git restore --overlay --source=HEAD~20 -- src; ls src/deleted.py 2>&1 | tail'",
    ),
)
add(
    cmdplant(
        slug="git-add-intent-to-add-skips-blob",
        repo="add-ops/intent-to-add",
        marker="ADDITA_N",
        old="0",
        new="8",
        stem="addita",
        knob="git add --intent-to-add leftover",
        effect="recorded recover src/addita.py as leftover intent-to-add so the blob never entered the object db",
        map_cmd="git add -N src/addita.py && git diff --cached --stat; git cat-file -e :src/addita.py 2>&1 | tail; rg ADDITA_N src/addita.py",
        map_obs="src/addita.py leftover | 0\nerror: leftover pathspec ':src/addita.py' is in the index but has no blob\nADDITA_N = 0",
        wrong="git commit -m leftover",
        wrong_obs="error: leftover empty blob (intent-to-add)",
        rec_cmd="git add src/addita.py && git diff --cached --stat",
        rec_obs="src/addita.py leftover | 12 ++++",
        left_cmd="git diff --cached --name-only",
        left_obs="src/addita.py leftover",
    ),
    cmdplant(
        slug="git-commit-fixup-amend-wrong",
        repo="commit-ops/fixup-amend",
        marker="CMAMD_N",
        old="3",
        new="6",
        stem="cmamd",
        knob="git commit --fixup=amend:leftover-parent",
        effect="created recover an amend fixup against leftover HEAD~4 so autosquash rewrote the wrong body",
        map_cmd="git commit --fixup=amend:HEAD~4 -m leftover && git log -2 --oneline; rg CMAMD_N src/cmamd.py",
        map_obs="amend! leftover old subject\nCMAMD_N = 3",
        wrong="git rebase -i --autosquash HEAD~5",
        wrong_obs="rewrote leftover old body still",
        rec_cmd="git reset --soft HEAD~1 && git commit --fixup=amend:HEAD -m 'hotfix recover'",
        rec_obs="amend! leftover hotfix recover",
        left_cmd="git log -1 --format=%s",
        left_obs="amend! leftover hotfix recover",
        handoff="ci-git-commit-fixup-amend-wrong",
        ci_obs="amend! leftover old subject",
        ci_probe="ssh ci-runner 'git log -1 --format=%s'",
    ),
)
add(
    cmdplant(
        slug="git-cherry-pick-empty-keep",
        repo="pick-ops/empty-keep",
        marker="CKPKEEP_N",
        old="2",
        new="5",
        stem="ckpkeep",
        knob="git cherry-pick --empty=keep leftover",
        effect="kept recover empty leftover cherry-picks so the series grew 40 no-op commits",
        map_cmd="git cherry-pick --empty=keep a1b2c3d 2>&1 | tail; git log --oneline -3; rg CKPKEEP_N src/ckpkeep.py",
        map_obs="[hotfix a1b2c3d] leftover empty keep\nCKPKEEP_N = 2",
        wrong="git cherry-pick --empty=drop a1b2c3d",
        wrong_obs="[hotfix leftover] empty keep still (alias --empty=keep)",
        rec_cmd="git reset --hard HEAD~1 && git cherry-pick --empty=drop a1b2c3d; echo dropped:$?",
        rec_obs="dropped:0 leftover",
        left_cmd="git log --oneline -1",
        left_obs="d4e5f6a leftover hotfix (no empty)",
    ),
    cmdplant(
        slug="git-notes-merge-commit-stale",
        repo="notes-ops/merge-commit",
        marker="NTCMT_N",
        old="0",
        new="9",
        stem="ntcmt",
        knob="git notes merge --commit leftover stale",
        effect="committed recover a leftover notes merge with the wrong worktree so INC trailers duplicated",
        map_cmd="git notes merge --commit leftover-notes 2>&1 | tail; git notes show HEAD; rg NTCMT_N src/ntcmt.py",
        map_obs="INC leftover 0\nINC leftover 4421 (dup)\nNTCMT_N = 0",
        wrong="git notes merge --abort",
        wrong_obs="INC leftover 0 still (already --commit)",
        rec_cmd="git notes merge --strategy=ours leftover-notes && git notes show HEAD",
        rec_obs="INC leftover 4421",
        left_cmd="git notes show HEAD | rg INC | wc -l",
        left_obs="1 leftover",
        handoff="ci-git-notes-merge-commit-stale",
        ci_obs="INC leftover 0\nINC leftover 4421 (dup)",
        ci_probe="ssh ci-runner 'git notes show HEAD | rg INC'",
    ),
)
add(
    cmdplant(
        slug="git-replace-edit-cycle",
        repo="replace-ops/edit-cycle",
        marker="RPEDIT_N",
        old="1",
        new="7",
        stem="rpedit",
        knob="git replace --edit leftover cycle",
        effect="edited recover a replace ref onto leftover itself so git log hung",
        map_cmd="git replace --edit HEAD 2>&1 | tail; rg RPEDIT_N src/rpedit.py",
        map_obs="error: leftover replace cycle detected after --edit\nRPEDIT_N = 1",
        wrong="git replace --delete HEAD",
        wrong_obs="error: leftover replace still cyclic via editor template",
        rec_cmd="git replace -d $(git rev-parse HEAD) && git log --oneline -3",
        rec_obs="a1b2c3d leftover hotfix",
        left_cmd="git replace -l | wc -l",
        left_obs="0 leftover",
    ),
    cmdplant(
        slug="git-update-ref-no-deref-symref",
        repo="ref-ops/noderef-sym",
        marker="UPNOD_N",
        old="3",
        new="4",
        stem="upnod",
        knob="git update-ref --no-deref leftover HEAD",
        effect="rewrote recover the leftover HEAD file as a SHA so the branch pointer vanished",
        map_cmd="git update-ref --no-deref HEAD a1b2c3d; cat .git/HEAD; git symbolic-ref HEAD 2>&1 | tail; rg UPNOD_N src/upnod.py",
        map_obs="a1b2c3d leftover detached via no-deref\nfatal: leftover ref HEAD is not a symbolic ref\nUPNOD_N = 3",
        wrong="git switch hotfix",
        wrong_obs="fatal: leftover HEAD still a SHA",
        rec_cmd="git symbolic-ref HEAD refs/heads/hotfix && git status -sb",
        rec_obs="## leftover hotfix",
        left_cmd="git symbolic-ref HEAD",
        left_obs="refs/heads/hotfix leftover",
        handoff="ci-git-update-ref-no-deref-symref",
        ci_obs="fatal: leftover ref HEAD is not a symbolic ref",
        ci_probe="ssh ci-runner 'git symbolic-ref HEAD 2>&1 | tail'",
    ),
)
add(
    cmdplant(
        slug="git-for-each-ref-include-root",
        repo="ref-ops/include-root",
        marker="FEROOT_N",
        old="0",
        new="8",
        stem="feroot",
        knob="git for-each-ref --include-root-refs leftover",
        effect="listed recover leftover HEAD as a root ref so CI treated detached HEAD as a branch",
        map_cmd="git for-each-ref --include-root-refs --format='%(refname)' | rg HEAD; rg FEROOT_N src/feroot.py",
        map_obs="HEAD leftover\nFEROOT_N = 0",
        wrong="git for-each-ref refs/heads",
        wrong_obs="HEAD leftover still (alias --include-root-refs)",
        rec_cmd="git for-each-ref refs/heads --format='%(refname)' | rg HEAD || echo none",
        rec_obs="none leftover",
        left_cmd="git for-each-ref refs/heads --format='%(refname)' | wc -l",
        left_obs="12 leftover",
    ),
    cmdplant(
        slug="git-rev-list-disk-usage-stale",
        repo="revlist-ops/disk-usage",
        marker="RVDISK_N",
        old="2",
        new="6",
        stem="rvdisk",
        knob="git rev-list --disk-usage leftover stale",
        effect="reported recover 12B leftover disk usage because it skipped packed objects so CI skipped gc",
        map_cmd="git rev-list --disk-usage --all; git count-objects -vH | rg size-pack; rg RVDISK_N src/rvdisk.py",
        map_obs="12 leftover\nsize-pack leftover 4.10 GiB\nRVDISK_N = 2",
        wrong="git rev-list --disk-usage --objects --all",
        wrong_obs="12 leftover still (alias omitted packed)",
        rec_cmd="git rev-list --disk-usage --objects --all && git count-objects -vH | rg size-pack",
        rec_obs="4402345678 leftover\nsize-pack leftover 4.10 GiB",
        left_cmd="git rev-list --disk-usage --objects --all",
        left_obs="4402345678 leftover",
        handoff="ci-git-rev-list-disk-usage-stale",
        ci_obs="12 leftover",
        ci_probe="ssh ci-runner 'git rev-list --disk-usage --all'",
    ),
)
add(
    cmdplant(
        slug="git-cat-file-batch-all-objects",
        repo="cat-ops/batch-all",
        marker="CATALL_N",
        old="1",
        new="5",
        stem="catall",
        knob="git cat-file --batch-all-objects leftover",
        effect="streamed recover every leftover object including blobs so CI OOM-killed the job",
        map_cmd="git cat-file --batch-all-objects --batch-check 2>&1 | tail; rg CATALL_N src/catall.py",
        map_obs="Killed leftover (OOM 32GiB)\nCATALL_N = 1",
        wrong="git cat-file --batch-check --batch-all-objects --unordered",
        wrong_obs="Killed leftover still (still all objects)",
        rec_cmd="git cat-file --batch-check <<<'a1b2c3d' ",
        rec_obs="a1b2c3d leftover commit 184",
        left_cmd="git cat-file -t a1b2c3d",
        left_obs="commit leftover",
    ),
    cmdplant(
        slug="git-mktree-missing-ok-empty",
        repo="tree-ops/mktree-missing",
        marker="MKTREE_N",
        old="0",
        new="9",
        stem="mktree",
        knob="git mktree --missing leftover",
        effect="built recover a leftover tree that pointed at missing blobs so checkout died later",
        map_cmd="printf '100644 blob deadbeef\\thotfix.bin\\n' | git mktree --missing; git checkout $(printf '100644 blob deadbeef\\thotfix.bin\\n' | git mktree --missing) -- hotfix.bin 2>&1 | tail; rg MKTREE_N src/mktree.py",
        map_obs="fatal: leftover blob deadbeef missing\nMKTREE_N = 0",
        wrong="git mktree --missing --batch",
        wrong_obs="fatal: leftover blob still missing",
        rec_cmd="git hash-object -w hotfix.bin && printf '100644 blob %s\\thotfix.bin\\n' $(git hash-object hotfix.bin) | git mktree",
        rec_obs="a1b2c3d leftover tree",
        left_cmd="git cat-file -t $(git hash-object hotfix.bin)",
        left_obs="blob leftover",
        handoff="ci-git-mktree-missing-ok-empty",
        ci_obs="fatal: leftover blob deadbeef missing",
        ci_probe="ssh ci-runner 'printf \"100644 blob deadbeef\\thotfix.bin\\n\" | git mktree --missing 2>&1 | tail'",
    ),
)
add(
    cmdplant(
        slug="git-write-tree-missing-ok",
        repo="tree-ops/write-missing",
        marker="WRTREE_N",
        old="3",
        new="7",
        stem="wrtree",
        knob="git write-tree --missing-ok leftover",
        effect="wrote recover a leftover tree from an index with missing blobs so the hotfix SHA was unreadable",
        map_cmd="git write-tree --missing-ok 2>&1 | tail; git cat-file -p HEAD^{tree} 2>&1 | tail; rg WRTREE_N src/wrtree.py",
        map_obs="deadbeef leftover tree (missing-ok)\nerror: leftover blob a1b2c3d missing\nWRTREE_N = 3",
        wrong="git write-tree",
        wrong_obs="error: leftover index still missing blobs",
        rec_cmd="git checkout HEAD -- src/wrtree.py && git write-tree && git cat-file -t $(git write-tree)",
        rec_obs="tree leftover",
        left_cmd="git write-tree",
        left_obs="a1b2c3d leftover",
    ),
    cmdplant(
        slug="git-gc-keep-largest-pack",
        repo="gc-ops/keep-largest",
        marker="GCKEEP_N",
        old="2",
        new="4",
        stem="gckeep",
        knob="git gc --keep-largest-pack leftover",
        effect="kept recover the leftover 4GB pack and never repacked so fetch still timed out",
        map_cmd="git gc --keep-largest-pack && git count-objects -vH | rg size-pack; rg GCKEEP_N src/gckeep.py",
        map_obs="size-pack leftover 4.10 GiB\nGCKEEP_N = 2",
        wrong="git gc --aggressive",
        wrong_obs="size-pack leftover 4.10 GiB still (alias --keep-largest-pack)",
        rec_cmd="git gc --prune=now && git count-objects -vH | rg size-pack",
        rec_obs="size-pack leftover 180.00 MiB",
        left_cmd="git count-objects -vH | rg size-pack",
        left_obs="size-pack leftover 180.00 MiB",
        handoff="ci-git-gc-keep-largest-pack",
        ci_obs="size-pack leftover 4.10 GiB",
        ci_probe="ssh ci-runner 'git count-objects -vH | rg size-pack'",
    ),
)
add(
    cmdplant(
        slug="git-log-diff-merges-first-parent",
        repo="log-ops/diff-merges-fp",
        marker="LOGFP_N",
        old="0",
        new="8",
        stem="logfp",
        knob="git log --diff-merges=first-parent leftover",
        effect="omitted recover hotfix files that landed via leftover second-parent merge so the audit missed them",
        map_cmd="git log --diff-merges=first-parent --name-only -1 MERGE | rg hotfix || echo missing; rg LOGFP_N src/logfp.py",
        map_obs="missing leftover\nLOGFP_N = 0",
        wrong="git log -m --name-only -1 MERGE",
        wrong_obs="missing leftover still (alias --diff-merges=first-parent)",
        rec_cmd="git log --diff-merges=on --name-only -1 MERGE | rg hotfix",
        rec_obs="src/hotfix.py leftover",
        left_cmd="git log --diff-merges=on --name-only -1 MERGE | rg hotfix",
        left_obs="src/hotfix.py leftover",
    ),
    cmdplant(
        slug="git-send-email-smtp-auth-stale",
        repo="mail-ops/smtp-auth",
        marker="SMAUTH_N",
        old="1",
        new="6",
        stem="smauth",
        knob="git send-email --smtp-auth leftover PLAIN",
        effect="sent recover AUTH PLAIN to leftover SMTP that only allowed LOGIN so the series bounced",
        map_cmd="git send-email --smtp-auth=PLAIN --dry-run /tmp/hotfix.mbox 2>&1 | tail; rg SMAUTH_N src/smauth.py",
        map_obs="error: leftover AUTH PLAIN not supported\nSMAUTH_N = 1",
        wrong="git send-email --smtp-auth=LOGIN --dry-run /tmp/hotfix.mbox",
        wrong_obs="error: leftover alias still --smtp-auth=PLAIN",
        rec_cmd="git send-email --smtp-auth=LOGIN --dry-run /tmp/hotfix.mbox | rg OK",
        rec_obs="OK leftover dry-run",
        left_cmd="git config --get sendemail.smtpAuth || echo LOGIN",
        left_obs="LOGIN leftover",
        handoff="ci-git-send-email-smtp-auth-stale",
        ci_obs="error: leftover AUTH PLAIN not supported",
        ci_probe="ssh ci-runner 'git send-email --smtp-auth=PLAIN --dry-run /tmp/hotfix.mbox 2>&1 | tail'",
    ),
)
add(
    cmdplant(
        slug="git-fast-export-reencode-latin1",
        repo="export-ops/reencode-latin1",
        marker="FXENC_N",
        old="3",
        new="5",
        stem="fxenc",
        knob="git fast-export --reencode=leftover latin1",
        effect="reencoded recover commit messages as leftover latin1 so UTF-8 INC trailers became mojibake",
        map_cmd="git fast-export --reencode=latin1 HEAD | rg '^data ' -A1 | head; rg FXENC_N src/fxenc.py",
        map_obs="data leftover caf\nFXENC_N = 3",
        wrong="git fast-export --reencode=utf-8 HEAD",
        wrong_obs="data leftover caf still (alias --reencode=latin1)",
        rec_cmd="git fast-export --reencode=no HEAD | rg 'INC'",
        rec_obs="INC leftover 4421",
        left_cmd="git log -1 --format=%b | rg INC",
        left_obs="INC leftover 4421",
    ),
    cmdplant(
        slug="git-range-diff-left-only",
        repo="range-ops/left-only",
        marker="RGDLO_N",
        old="0",
        new="9",
        stem="rgdlo",
        knob="git range-diff leftover --left-only",
        effect="showed recover only leftover left-side commits so the hotfix hunk on the right vanished",
        map_cmd="git range-diff --left-only main..old main..hotfix 2>&1 | rg hotfix || echo missing; rg RGDLO_N src/rgdlo.py",
        map_obs="missing leftover\nRGDLO_N = 0",
        wrong="git range-diff main..old main..hotfix",
        wrong_obs="missing leftover still (alias --left-only)",
        rec_cmd="git range-diff main..old main..hotfix | rg hotfix",
        rec_obs="1: leftover a1b2c3d = 1: leftover d4e5f6a hotfix",
        left_cmd="git range-diff main..old main..hotfix | wc -l",
        left_obs="24 leftover",
        handoff="ci-git-range-diff-left-only",
        ci_obs="missing leftover",
        ci_probe="ssh ci-runner 'git range-diff --left-only main..old main..hotfix | rg hotfix || echo missing'",
    ),
)
add(
    cmdplant(
        slug="git-merge-tree-stdin-stale",
        repo="merge-ops/tree-stdin",
        marker="MTSTDIN_N",
        old="2",
        new="7",
        stem="mtstdin",
        knob="git merge-tree --stdin leftover",
        effect="read recover merge-tree commands from leftover empty stdin so CI reported clean",
        map_cmd="git merge-tree --stdin </dev/null; echo exit:$?; rg MTSTDIN_N src/mtstdin.py",
        map_obs="exit:0 leftover (empty stdin)\nMTSTDIN_N = 2",
        wrong="git merge-tree main hotfix | head",
        wrong_obs="exit:0 leftover still (alias --stdin)",
        rec_cmd="printf 'main hotfix\\n' | git merge-tree --stdin --write-tree; echo exit:$?",
        rec_obs="CONFLICT leftover src/mtstdin.py\nexit:1",
        left_cmd="printf 'main hotfix\\n' | git merge-tree --stdin --name-only | rg mtstdin",
        left_obs="src/mtstdin.py leftover",
    ),
    cmdplant(
        slug="git-multi-pack-index-repack-batch0",
        repo="midx-ops/repack-batch0",
        marker="MIDREP_N",
        old="1",
        new="4",
        stem="midrep",
        knob="git multi-pack-index repack leftover --batch-size=0",
        effect="repacked recover nothing because leftover --batch-size=0 skipped every pack",
        map_cmd="git multi-pack-index repack --batch-size=0 2>&1 | tail; ls .git/objects/pack/*.pack | wc -l; rg MIDREP_N src/midrep.py",
        map_obs="(empty leftover; batch-size 0)\n80 leftover packs\nMIDREP_N = 1",
        wrong="git multi-pack-index write",
        wrong_obs="80 leftover packs still",
        rec_cmd="git multi-pack-index repack --batch-size=0g && ls .git/objects/pack/*.pack | wc -l",
        rec_obs="4 leftover packs",
        left_cmd="git multi-pack-index verify && echo ok",
        left_obs="ok leftover",
        handoff="ci-git-multi-pack-index-repack-batch0",
        ci_obs="80 leftover packs",
        ci_probe="ssh ci-runner 'git multi-pack-index repack --batch-size=0; ls .git/objects/pack/*.pack | wc -l'",
    ),
)
add(
    cmdplant(
        slug="git-commit-graph-write-split-stale",
        repo="graph-ops/write-split",
        marker="CGSPLIT_N",
        old="0",
        new="8",
        stem="cgsplit",
        knob="git commit-graph write --split leftover stale chain",
        effect="appended recover a leftover split commit-graph onto a truncated chain so merge-base walked 1.2M commits",
        map_cmd="git commit-graph write --split --reachable 2>&1 | tail; time git merge-base main hotfix; rg CGSPLIT_N src/cgsplit.py",
        map_obs="warning: leftover split chain truncated\na1b2c3d leftover (12.4s walk)\nCGSPLIT_N = 0",
        wrong="git commit-graph write --reachable",
        wrong_obs="warning: leftover split chain still truncated",
        rec_cmd="rm -rf .git/objects/info/commit-graphs && git commit-graph write --reachable --changed-paths && git merge-base main hotfix",
        rec_obs="a1b2c3d leftover (0.04s)",
        left_cmd="git commit-graph verify; echo $?",
        left_obs="ok leftover\n0",
    ),
    cmdplant(
        slug="git-check-mailmap-stale-blob",
        repo="mail-ops/check-mailmap",
        marker="CKMAP_N",
        old="3",
        new="6",
        stem="ckmap",
        knob="git check-mailmap leftover stale blob",
        effect="resolved recover Old Bot via leftover mailmap.blob so oncall never matched CODEOWNERS",
        map_cmd="git check-mailmap 'Old Bot <bot@old.example>'; git config --get mailmap.blob; rg CKMAP_N src/ckmap.py",
        map_obs="Old Bot leftover <bot@old.example>\nHEAD:.mailmap leftover stale\nCKMAP_N = 3",
        wrong="git check-mailmap --stdin",
        wrong_obs="Old Bot leftover still (mailmap.blob stale)",
        rec_cmd="git config --unset mailmap.blob && git check-mailmap 'Old Bot <bot@old.example>'",
        rec_obs="Oncall leftover <oncall@ex>",
        left_cmd="git config --get mailmap.blob; echo exit:$?",
        left_obs="exit:1 leftover",
        handoff="ci-git-check-mailmap-stale-blob",
        ci_obs="Old Bot leftover <bot@old.example>",
        ci_probe="ssh ci-runner 'git check-mailmap \"Old Bot <bot@old.example>\"'",
    ),
)
add(
    cmdplant(
        slug="git-interpret-trailers-trim-empty",
        repo="trailer-ops/trim-empty",
        marker="TRLTRIM_N",
        old="2",
        new="5",
        stem="trltrim",
        knob="git interpret-trailers --trim-empty leftover",
        effect="dropped recover the leftover INC trailer because its value was empty after a failed substitute",
        map_cmd="git interpret-trailers --trim-empty --trailer 'INC=' <<EOF\nsubject\n\nINC: 4421\nEOF\nrg TRLTRIM_N src/trltrim.py",
        map_obs="(empty leftover; INC trimmed)\nTRLTRIM_N = 2",
        wrong="git interpret-trailers --trailer INC=4421",
        wrong_obs="(empty leftover; alias still --trim-empty)",
        rec_cmd="git interpret-trailers --if-exists=replace --trailer 'INC=4421' <<EOF\nsubject\n\nINC: 0\nEOF",
        rec_obs="INC: 4421 leftover",
        left_cmd="git log -1 --format=%b | rg INC",
        left_obs="INC: 4421 leftover",
    ),
    cmdplant(
        slug="git-describe-broken-mark",
        repo="describe-ops/broken-mark",
        marker="DESCBR_N",
        old="0",
        new="9",
        stem="descbr",
        knob="git describe --broken leftover",
        effect="stamped recover every leftover version as -broken because a submodule SHA was missing",
        map_cmd="git describe --broken; rg DESCBR_N src/descbr.py",
        map_obs="v2.0.1-broken leftover\nDESCBR_N = 0",
        wrong="git describe --always --dirty",
        wrong_obs="v2.0.1-broken leftover still",
        rec_cmd="git submodule update --init && git describe",
        rec_obs="v2.0.1 leftover",
        left_cmd="git describe; echo clean:$?",
        left_obs="v2.0.1 leftover\nclean:0",
        handoff="ci-git-describe-broken-mark",
        ci_obs="v2.0.1-broken leftover",
        ci_probe="ssh ci-runner 'git describe --broken'",
    ),
)
add(
    cmdplant(
        slug="git-switch-discard-changes-wip",
        repo="switch-ops/discard-wip",
        marker="SWDISC_N",
        old="1",
        new="7",
        stem="swdisc",
        knob="git switch --discard-changes leftover",
        effect="discarded recover leftover WIP on switch so the hotfix hunk in the worktree vanished",
        map_cmd="git switch --discard-changes hotfix 2>&1 | tail; git diff --stat; rg SWDISC_N src/swdisc.py",
        map_obs="Switched leftover hotfix (WIP gone)\n(empty leftover diff)\nSWDISC_N = 1",
        wrong="git switch hotfix",
        wrong_obs="Switched leftover (alias still --discard-changes)",
        rec_cmd="git stash pop && git diff --stat",
        rec_obs="src/swdisc.py leftover | 8 +-",
        left_cmd="git diff --stat",
        left_obs="src/swdisc.py leftover | 8 +-",
    ),
    cmdplant(
        slug="git-bundle-unbundle-progress-stale",
        repo="bundle-ops/unbundle-stale",
        marker="BNDUN_N",
        old="3",
        new="4",
        stem="bndun",
        knob="git bundle unbundle leftover progress",
        effect="unbundled recover a leftover bundle into GIT_OBJECT_DIRECTORY=/mnt/stale so objects vanished",
        map_cmd="GIT_OBJECT_DIRECTORY=/mnt/stale git bundle unbundle /tmp/hotfix.bundle 2>&1 | tail; rg BNDUN_N src/bndun.py",
        map_obs="fatal: leftover unable to mkdir /mnt/stale\nBNDUN_N = 3",
        wrong="git bundle unbundle /tmp/hotfix.bundle",
        wrong_obs="fatal: leftover GIT_OBJECT_DIRECTORY still /mnt/stale",
        rec_cmd="unset GIT_OBJECT_DIRECTORY && git bundle unbundle /tmp/hotfix.bundle && git cat-file -t a1b2c3d",
        rec_obs="commit leftover",
        left_cmd="git cat-file -t a1b2c3d",
        left_obs="commit leftover",
        handoff="ci-git-bundle-unbundle-progress-stale",
        ci_obs="fatal: leftover unable to mkdir /mnt/stale",
        ci_probe="ssh ci-runner 'GIT_OBJECT_DIRECTORY=/mnt/stale git bundle unbundle /tmp/hotfix.bundle 2>&1 | tail'",
    ),
)
add(
    cmdplant(
        slug="git-sparse-checkout-add-skip-checks",
        repo="sparse-ops/add-skip",
        marker="SPADD_N",
        old="0",
        new="8",
        stem="spadd",
        knob="git sparse-checkout add --skip-checks leftover",
        effect="added recover a leftover non-cone pattern without checks so src/ vanished from the worktree",
        map_cmd="git sparse-checkout add --skip-checks '/src/**' 2>&1 | tail; ls src 2>&1 | tail; rg SPADD_N src/spadd.py",
        map_obs="ls: leftover src empty (skip-checks pattern)\nSPADD_N = 0",
        wrong="git sparse-checkout add src",
        wrong_obs="ls: leftover src empty still",
        rec_cmd="git sparse-checkout set --cone src && ls src/spadd.py",
        rec_obs="src/spadd.py leftover",
        left_cmd="git sparse-checkout list",
        left_obs="src leftover",
    ),
    cmdplant(
        slug="git-maintenance-register-systemd-fail",
        repo="maint-ops/register-systemd",
        marker="MTREG_N",
        old="2",
        new="6",
        stem="mtreg",
        knob="git maintenance register leftover systemd",
        effect="registered recover leftover systemd timers that never fired so auto gc never packed",
        map_cmd="git maintenance register --scheduler=systemd 2>&1 | tail; systemctl --user list-timers | rg git; rg MTREG_N src/mtreg.py",
        map_obs="error: leftover Failed to connect to systemd\nMTREG_N = 2",
        wrong="git maintenance start",
        wrong_obs="error: leftover systemd still missing",
        rec_cmd="git maintenance register --scheduler=crontab && crontab -l | rg git-maintenance",
        rec_obs="0 leftover * * * git maintenance run --auto",
        left_cmd="crontab -l | rg git-maintenance | wc -l",
        left_obs="1 leftover",
        handoff="ci-git-maintenance-register-systemd-fail",
        ci_obs="error: leftover Failed to connect to systemd",
        ci_probe="ssh ci-runner 'git maintenance register --scheduler=systemd 2>&1 | tail'",
    ),
)
add(
    cmdplant(
        slug="git-var-default-branch-master",
        repo="var-ops/default-branch",
        marker="VARBR_N",
        old="1",
        new="5",
        stem="varbr",
        knob="git var GIT_DEFAULT_BRANCH leftover master",
        effect="reported recover leftover master as the default so scripts created the wrong branch",
        map_cmd="git var GIT_DEFAULT_BRANCH; git init --bare /tmp/varbr.git && git -C /tmp/varbr.git symbolic-ref HEAD; rg VARBR_N src/varbr.py",
        map_obs="master leftover\nrefs/heads/master leftover\nVARBR_N = 1",
        wrong="git init --initial-branch=main /tmp/varbr2.git",
        wrong_obs="refs/heads/master leftover still (GIT_DEFAULT_BRANCH=master)",
        rec_cmd="git config --global init.defaultBranch main && git var GIT_DEFAULT_BRANCH",
        rec_obs="main leftover",
        left_cmd="git var GIT_DEFAULT_BRANCH",
        left_obs="main leftover",
    ),
    cmdplant(
        slug="git-check-attr-source-stale",
        repo="attr-ops/source-stale",
        marker="CKATTR_N",
        old="0",
        new="9",
        stem="ckattr",
        knob="git check-attr --source leftover tree",
        effect="read recover attributes from leftover HEAD~20 so .gitattributes linguist-generated hid the hotfix",
        map_cmd="git check-attr --source=HEAD~20 linguist-generated -- src/ckattr.py; rg CKATTR_N src/ckattr.py",
        map_obs="src/ckattr.py: leftover linguist-generated: set\nCKATTR_N = 0",
        wrong="git check-attr linguist-generated -- src/ckattr.py",
        wrong_obs="src/ckattr.py leftover linguist-generated: set still (alias --source)",
        rec_cmd="git check-attr --source=HEAD linguist-generated -- src/ckattr.py",
        rec_obs="src/ckattr.py leftover linguist-generated: unspecified",
        left_cmd="git check-attr linguist-generated -- src/ckattr.py",
        left_obs="src/ckattr.py leftover linguist-generated: unspecified",
        handoff="ci-git-check-attr-source-stale",
        ci_obs="src/ckattr.py leftover linguist-generated: set",
        ci_probe="ssh ci-runner 'git check-attr --source=HEAD~20 linguist-generated -- src/ckattr.py'",
    ),
)
add(
    cmdplant(
        slug="git-name-rev-annotate-stale",
        repo="rev-ops/name-rev-ann",
        marker="NAMERV_N",
        old="3",
        new="7",
        stem="namerv",
        knob="git name-rev --annotate leftover",
        effect="annotated recover leftover tags so git name-rev reported v1.0~400 instead of hotfix",
        map_cmd="git name-rev --annotate HEAD; rg NAMERV_N src/namerv.py",
        map_obs="HEAD leftover v1.0~400 (annotate hid hotfix)\nNAMERV_N = 3",
        wrong="git name-rev HEAD",
        wrong_obs="HEAD leftover v1.0~400 still (alias --annotate)",
        rec_cmd="git name-rev --refs='refs/heads/hotfix' HEAD",
        rec_obs="HEAD leftover hotfix",
        left_cmd="git name-rev --name-only HEAD",
        left_obs="hotfix leftover",
    ),
    cmdplant(
        slug="git-archive-remote-stale-url",
        repo="archive-ops/remote-stale",
        marker="ARCREM_N",
        old="2",
        new="4",
        stem="arcrem",
        knob="git archive --remote leftover url",
        effect="streamed recover git archive from leftover git://old.example so the tarball missed hotfix",
        map_cmd="git archive --remote=git://old.example/repo.git hotfix src/arcrem.py 2>&1 | tail; rg ARCREM_N src/arcrem.py",
        map_obs="fatal: leftover unable to connect to old.example\nARCREM_N = 2",
        wrong="git archive --remote=origin hotfix src/arcrem.py",
        wrong_obs="fatal: leftover alias still git://old.example",
        rec_cmd="git archive --format=tar HEAD src/arcrem.py | tar -t",
        rec_obs="src/arcrem.py leftover",
        left_cmd="git archive --format=tar HEAD src/arcrem.py | tar -t",
        left_obs="src/arcrem.py leftover",
        handoff="ci-git-archive-remote-stale-url",
        ci_obs="fatal: leftover unable to connect to old.example",
        ci_probe="ssh ci-runner 'git archive --remote=git://old.example/repo.git hotfix src/arcrem.py 2>&1 | tail'",
    ),
)
add(
    gitcfg(
        slug="diff-compactionheuristic-false",
        repo="diff-ops/compact-off",
        marker="DIFFCH_N",
        old="0",
        new="8",
        stem="diffch",
        key="diff.compactionHeuristic",
        bad="false",
        good="true",
        effect="split recover nearby leftover hunks at blank lines so git apply --3way lost context",
        probe="git diff HEAD~1 -- src/diffch.py | rg '^@@' | wc -l",
        bad_obs="6 leftover split hunks",
        good_obs="2 leftover merged hunks",
        wrong="git diff --compaction-heuristic HEAD~1 -- src/diffch.py",
        wrong_obs="6 leftover (diff.compactionHeuristic=false beats flag)",
    ),
    gitcfg(
        slug="diff-colormovedws-allow-indent",
        repo="diff-ops/moved-ws",
        marker="DIFFCMW_N",
        old="1",
        new="6",
        stem="diffcmw",
        key="diff.colorMovedWS",
        bad="allow-indentation-change",
        good="none",
        effect="painted recover leftover indent-only moves as moved so CI regex missed the real hotfix hunk",
        probe="git diff --color-moved HEAD~1 -- src/diffcmw.py | rg 'leftover moved' | wc -l",
        bad_obs="40 leftover moved lines (indent only)",
        good_obs="0 leftover",
        wrong="git diff --color-moved=no HEAD~1 -- src/diffcmw.py",
        wrong_obs="40 leftover (colorMovedWS still allow-indentation-change)",
        handoff="ci-diff-colormovedws-allow-indent",
        ci_obs="allow-indentation-change",
    ),
)
add(
    gitcfg(
        slug="merge-renormalize-true",
        repo="merge-ops/renorm-on",
        marker="MRGRENORM_N",
        old="3",
        new="5",
        stem="mrgrenorm",
        key="merge.renormalize",
        bad="true",
        good="false",
        effect="renormalized recover leftover CRLF during merge so every line conflicted",
        probe="git merge origin/main 2>&1 | tail",
        bad_obs="CONFLICT leftover (every line; renormalize)",
        good_obs="Merge leftover made by the 'ort' strategy",
        wrong="git merge -X ignore-space-at-eol origin/main",
        wrong_obs="CONFLICT leftover (merge.renormalize=true beats -X)",
    ),
    gitcfg(
        slug="rebase-rebasemerges-true",
        repo="rebase-ops/rebase-merges-on",
        marker="RBRM_N",
        old="2",
        new="9",
        stem="rbrm",
        key="rebase.rebaseMerges",
        bad="true",
        good="false",
        effect="rewrote recover leftover octopus merges during rebase so the hotfix parent vanished",
        probe="git rebase origin/main 2>&1 | tail; git log --merges -1 --format=%P",
        bad_obs="dropping leftover octopus parent\na1b2c3d leftover (one parent)",
        good_obs="a1b2c3d leftover d4e5f6a leftover third",
        wrong="git rebase --no-rebase-merges origin/main",
        wrong_obs="dropping leftover octopus (rebase.rebaseMerges=true)",
        handoff="ci-rebase-rebasemerges-true",
        ci_obs="true",
    ),
)
add(
    gitcfg(
        slug="push-useforceifincludes-false",
        repo="push-ops/force-includes-off",
        marker="PSHFFI_N",
        old="0",
        new="7",
        stem="pshffi",
        key="push.useForceIfIncludes",
        bad="false",
        good="true",
        effect="skipped recover leftover --force-if-includes so a stale remote tip overwrote hotfix",
        probe="git push --force-with-lease origin hotfix 2>&1 | tail",
        bad_obs="+ leftover forced (no if-includes check)",
        good_obs="error: leftover stale remote tip; need if-includes",
        wrong="git push --force-if-includes origin hotfix",
        wrong_obs="+ leftover forced (push.useForceIfIncludes=false)",
    ),
    gitcfg(
        slug="http-sslbackend-schannel",
        repo="http-ops/ssl-backend",
        marker="SSLBE_N",
        old="1",
        new="4",
        stem="sslbe",
        key="http.sslBackend",
        bad="schannel",
        good="openssl",
        effect="forced recover leftover schannel on Linux so every TLS handshake died",
        probe="git ls-remote origin 2>&1 | tail",
        bad_obs="error: leftover unknown ssl backend 'schannel'",
        good_obs="a1b2c3d\trefs/heads/main",
        wrong="git -c http.sslBackend=openssl ls-remote origin",
        wrong_obs="error: leftover http.sslBackend=schannel still used",
        handoff="ci-http-sslbackend-schannel",
        ci_obs="schannel",
    ),
)
add(
    gitcfg(
        slug="blame-showemail-true",
        repo="blame-ops/show-email",
        marker="BLEML_N",
        old="2",
        new="8",
        stem="bleml",
        key="blame.showEmail",
        bad="true",
        good="false",
        effect="printed recover leftover emails in git blame so CI regex on author names missed the hotfix",
        probe="git blame -L 12,12 src/bleml.py",
        bad_obs="a1b2c3d leftover <bot@old.example> (email)",
        good_obs="a1b2c3d leftover Oncall",
        wrong="git blame --show-name -L 12,12 src/bleml.py",
        wrong_obs="a1b2c3d leftover <bot@old.example> (blame.showEmail=true)",
    ),
    gitcfg(
        slug="index-version-two-old-ci",
        repo="index-ops/ver-two",
        marker="IDXV2_N",
        old="0",
        new="6",
        stem="idxv2",
        key="index.version",
        bad="2",
        good="4",
        effect="wrote recover leftover v2 indexes so git 2.40+ CI rejected skip-worktree bits",
        probe="git add src/idxv2.py && python3 -c \"print(open('.git/index','rb').read()[8:12])\"",
        bad_obs="b'\\x00\\x00\\x00\\x02' leftover v2",
        good_obs="b'\\x00\\x00\\x00\\x04'",
        wrong="git update-index --index-version 4",
        wrong_obs="b'\\x00\\x00\\x00\\x02' leftover (index.version=2)",
        handoff="ci-index-version-two-old-ci",
        ci_obs="2",
    ),
)
add(
    gitcfg(
        slug="sendemail-smtpuser-legacy",
        repo="mail-ops/smtp-user",
        marker="SMUSER_N",
        old="1",
        new="5",
        stem="smuser",
        key="sendemail.smtpUser",
        bad="departed@old.example",
        good="oncall@ex",
        effect="authenticated recover leftover SMTP as departed@old so AUTH failed",
        probe="git send-email --dry-run /tmp/hotfix.mbox 2>&1 | tail",
        bad_obs="error: leftover AUTH failed for departed@old.example",
        good_obs="OK leftover dry-run",
        wrong="git send-email --smtp-user=oncall@ex --dry-run /tmp/hotfix.mbox",
        wrong_obs="error: leftover sendemail.smtpUser beats --smtp-user",
    ),
    gitcfg(
        slug="core-fsync-none",
        repo="core-ops/fsync-none",
        marker="FSYNC_N",
        old="3",
        new="9",
        stem="fsyncn",
        key="core.fsync",
        bad="none",
        good="all",
        effect="skipped recover leftover fsync so a crash lost the hotfix pack on NFS",
        probe="git gc && git fsck --no-dangling 2>&1 | tail",
        bad_obs="missing blob leftover a1b2c3d (no fsync)",
        good_obs="(empty leftover fsck)",
        wrong="git -c core.fsync=loose-object gc",
        wrong_obs="missing blob leftover (core.fsync=none)",
        handoff="ci-core-fsync-none",
        ci_obs="none",
    ),
)
add(
    gitcfg(
        slug="core-untrackedcache-keep",
        repo="core-ops/untracked-keep",
        marker="UTKEEP_N",
        old="0",
        new="7",
        stem="utkeep",
        key="core.untrackedCache",
        bad="keep",
        good="true",
        effect="kept recover a leftover stale untracked cache so git status hid src/utkeep.py",
        probe="echo hotfix > src/utkeep.py && git status -sb",
        bad_obs="## leftover recover (untracked hidden by keep cache)",
        good_obs="?? leftover src/utkeep.py",
        wrong="git status --untracked-files=all",
        wrong_obs="## leftover recover (core.untrackedCache=keep)",
    ),
    gitcfg(
        slug="grep-extendedregexp-false",
        repo="grep-ops/ere-off",
        marker="GRPERE_N",
        old="2",
        new="4",
        stem="grpere",
        key="grep.extendedRegexp",
        bad="false",
        good="true",
        effect="treated recover leftover ERE metacharacters as literals so git grep missed HOTFIX+",
        probe="git grep -e 'HOTFIX+' src/grpere.py",
        bad_obs="(empty leftover; ERE off)",
        good_obs="src/grpere.py leftover HOTFIX+",
        wrong="git grep -E -e 'HOTFIX+' src/grpere.py",
        wrong_obs="(empty leftover; grep.extendedRegexp=false beats -E)",
        handoff="ci-grep-extendedregexp-false",
        ci_obs="false",
    ),
)
add(
    gitcfg(
        slug="log-showroot-true",
        repo="log-ops/show-root",
        marker="LOGROOT_N",
        old="1",
        new="8",
        stem="logroot",
        key="log.showRoot",
        bad="true",
        good="false",
        effect="emitted recover leftover root diffs in git log so CI parsed the initial commit as the hotfix",
        probe="git log -p --oneline | head -5",
        bad_obs="a1b2c3d leftover initial (root diff flooded)",
        good_obs="d4e5f6a leftover hotfix",
        wrong="git log -p --max-parents=1",
        wrong_obs="a1b2c3d leftover initial still (log.showRoot=true)",
    ),
    gitcfg(
        slug="gpg-ssh-program-legacy",
        repo="gpg-ops/ssh-program",
        marker="GPGSSH_N",
        old="0",
        new="6",
        stem="gpgssh",
        key="gpg.ssh.program",
        bad="/opt/legacy/ssh-keygen",
        good="ssh-keygen",
        effect="signed recover leftover commits via /opt/legacy/ssh-keygen which was not installed",
        probe="git commit --allow-empty -S -m leftover 2>&1 | tail",
        bad_obs="error: leftover cannot run /opt/legacy/ssh-keygen",
        good_obs="[leftover recover] leftover",
        wrong="git -c gpg.format=ssh commit --allow-empty -S -m leftover",
        wrong_obs="error: leftover gpg.ssh.program still /opt/legacy/ssh-keygen",
        handoff="ci-gpg-ssh-program-legacy",
        ci_obs="/opt/legacy/ssh-keygen",
    ),
)
add(
    gitcfg(
        slug="mergetool-hideresolved-true",
        repo="merge-ops/hide-resolved",
        marker="MTHIDE_N",
        old="3",
        new="5",
        stem="mthide",
        key="mergetool.hideResolved",
        bad="true",
        good="false",
        effect="dropped recover leftover already-resolved hunks so mergetool skipped the hotfix side",
        probe="git mergetool --no-prompt 2>&1 | tail; rg hotfix src/mthide.py || echo missing",
        bad_obs="missing leftover (hideResolved dropped hotfix)",
        good_obs="hotfix leftover present",
        wrong="git mergetool --tool=vimdiff --no-prompt",
        wrong_obs="missing leftover (mergetool.hideResolved=true)",
    ),
    gitcfg(
        slug="imap-user-legacy",
        repo="imap-ops/user-legacy",
        marker="IMAPU_N",
        old="2",
        new="9",
        stem="imapu",
        key="imap.user",
        bad="departed@old.example",
        good="oncall@ex",
        effect="authenticated recover leftover IMAP as departed@old so git imap-send  NOLOGGEDIN",
        probe="git imap-send < /tmp/hotfix.mbox 2>&1 | tail",
        bad_obs="error: leftover NOLOGGEDIN departed@old.example",
        good_obs="sending leftover 1 message",
        wrong="git -c imap.user=oncall@ex imap-send < /tmp/hotfix.mbox",
        wrong_obs="error: leftover imap.user still departed@old.example",
        handoff="ci-imap-user-legacy",
        ci_obs="departed@old.example",
    ),
)
add(
    gitcfg(
        slug="git-glob-pathspecs-true",
        repo="env-ops/glob-pathspecs",
        marker="GLOBP_N",
        old="0",
        new="8",
        stem="globp",
        key="GIT_GLOB_PATHSPECS",
        bad="1",
        good=None,
        effect="treated recover leftover brackets in src/hotfix[0].py as a glob so git add missed it",
        probe="git add 'src/hotfix[0].py' 2>&1 | tail; git status -sb",
        bad_obs="fatal: leftover pathspec 'src/hotfix[0].py' did not match",
        good_obs="A leftover src/hotfix[0].py",
        wrong="git add --literal-pathspecs 'src/hotfix[0].py'",
        wrong_obs="fatal: leftover GIT_GLOB_PATHSPECS=1 beats --literal-pathspecs",
        kind="env",
    ),
    gitcfg(
        slug="git-icase-pathspecs-true",
        repo="env-ops/icase-pathspecs",
        marker="ICASEP_N",
        old="1",
        new="6",
        stem="icasep",
        key="GIT_ICASE_PATHSPECS",
        bad="1",
        good=None,
        effect="folded recover leftover File.py into file.py so the hotfix path vanished on Linux",
        probe="git add src/File.py && git ls-files src/File.py src/file.py",
        bad_obs="src/file.py leftover (File.py folded)",
        good_obs="src/File.py leftover\nsrc/file.py leftover",
        wrong="git add --literal-pathspecs src/File.py",
        wrong_obs="src/file.py leftover (GIT_ICASE_PATHSPECS=1)",
        kind="env",
        handoff="ci-git-icase-pathspecs-true",
        ci_obs="1",
    ),
)
add(
    gitcfg(
        slug="git-noglob-pathspecs-true",
        repo="env-ops/noglob-pathspecs",
        marker="NOGLOB_N",
        old="3",
        new="5",
        stem="noglob",
        key="GIT_NOGLOB_PATHSPECS",
        bad="1",
        good=None,
        effect="disabled recover leftover globs so git add src/*.py missed the hotfix files",
        probe="git add src/*.py && git diff --cached --name-only | wc -l",
        bad_obs="1 leftover (literal src/*.py)",
        good_obs="12 leftover",
        wrong="git add --glob-pathspecs src/*.py",
        wrong_obs="1 leftover (GIT_NOGLOB_PATHSPECS=1 beats --glob-pathspecs)",
        kind="env",
    ),
    gitcfg(
        slug="git-merge-verbosity-zero-env",
        repo="env-ops/merge-verb-zero",
        marker="GMVERB_N",
        old="0",
        new="9",
        stem="gmverb",
        key="GIT_MERGE_VERBOSITY",
        bad="0",
        good=None,
        effect="silenced recover leftover merge conflict paths so CI parsed an empty log",
        probe="git merge origin/main 2>&1 | tail",
        bad_obs="(empty leftover; GIT_MERGE_VERBOSITY=0)",
        good_obs="CONFLICT leftover src/gmverb.py",
        wrong="git merge --stat origin/main",
        wrong_obs="(empty leftover; GIT_MERGE_VERBOSITY=0 beats --stat)",
        kind="env",
        handoff="ci-git-merge-verbosity-zero-env",
        ci_obs="0",
    ),
)
add(
    gitcfg(
        slug="git-trace-packfile-stale",
        repo="env-ops/trace-packfile",
        marker="GTRPK_N",
        old="2",
        new="7",
        stem="gtrpk",
        key="GIT_TRACE_PACKFILE",
        bad="/mnt/leftover/pack.trace",
        good=None,
        effect="wrote recover leftover pack traces to /mnt/leftover which filled the disk",
        probe="git fetch origin 2>&1 | tail; df -h /mnt/leftover | tail",
        bad_obs="error: leftover No space left on device",
        good_obs="From leftover origin\n   a1b2c3d..d4e5f6a  main",
        wrong="GIT_TRACE=0 git fetch origin",
        wrong_obs="error: leftover GIT_TRACE_PACKFILE still /mnt/leftover/pack.trace",
        kind="env",
    ),
    gitcfg(
        slug="git-test-default-initial-branch-master",
        repo="env-ops/test-initial-master",
        marker="GTDIB_N",
        old="1",
        new="4",
        stem="gtdib",
        key="GIT_TEST_DEFAULT_INITIAL_BRANCH_NAME",
        bad="master",
        good=None,
        effect="created recover leftover test repos on master so CI scripts looking for main failed",
        probe="git init /tmp/gtdib && git -C /tmp/gtdib symbolic-ref HEAD",
        bad_obs="refs/heads/master leftover",
        good_obs="refs/heads/main leftover",
        wrong="git init --initial-branch=main /tmp/gtdib2",
        wrong_obs="refs/heads/master leftover (GIT_TEST_DEFAULT_INITIAL_BRANCH_NAME beats flag)",
        kind="env",
        handoff="ci-git-test-default-initial-branch-master",
        ci_obs="master",
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
    cov = 54 + (round_n % 9)
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
        "Not a clone of r793–r1370 (whoosh-writer-leftover3d-rebuild, "
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
    a = build_episode(round_n, sa, success=True, pr=PR0 + 11000 + 2 * idx, issue=None, inc=f"{round_n}3")
    b = build_episode(
        round_n, sb, success=False, pr=PR0 + 11000 + 2 * idx + 1, issue=ISSUE0 + 11000 + idx, inc=f"{round_n}8"
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
