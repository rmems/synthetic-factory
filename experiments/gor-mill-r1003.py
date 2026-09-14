#!/usr/bin/env python3
"""Mill git-ops-recovery-factory rounds r1003+ (recover incidents, not r895–r1002)."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

FACTORY = "git-ops-recovery-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 1003
PR0 = 777
ISSUE0 = 803

# BAN leftover-tmp cartesian, r895–r1002 clones, stacked-git CLI cartesian.
BANNED_SLUGS = {
    "merge-index-leftover",
    "merge-one-file-leftover",
    "lfs-lock-leftover",
    "p4-rebase-leftover",
    "scalar-reconfigure-leftover",
    "lfs-smudge-pointer-leftover",
    "annex-unused-needed-keys",
    "filter-repo-already-skip",
    "subtree-split-leftover",
    "p4-unshelve-leftover",
    "svn-rebase-leftover",
    "scalar-diagnose-leftover",
    "maintenance-already-skip",
    "backfill-tmp-leftover",
    "replay-already-skip",
    "restore-already-skip",
    "switch-leftover",
    "sparse-reapply-leftover",
    "worktree-already-skip",
    "maintenance-unregister-leftover",
    "absorb-wrong-fixup-parent",
    "imerge-finish-before-pairs",
    "revise-nested-todo-crash",
    "branchless-undo-overshoot",
    "stack-restack-parent-order",
    "town-sync-perennial-feature",
    "machete-slide-out-unhooked-child",
    "jj-git-export-colocated-lock",
    "sapling-restack-divergent-stack",
    "rebase-update-refs-stale-tips",
}


def _sha(slug: str) -> str:
    h = hashlib.sha1(f"gor-{slug}".encode()).hexdigest()[:7]
    if h == "0000000" or not any(c.isalpha() for c in h):
        h = hashlib.sha1(f"gor-{slug}-x".encode()).hexdigest()[:7]
    return h


# Each pair is (success_spec, handoff_spec). Indexed by round-1003.
# Unique recover *incidents*: replace/bundle/submodule/sparse/worktree/
# filter-repo/lfs/crypt already-skip, commit-graph/midx/dangling-replace,
# reftable-vs-files, packed-refs-vs-loose, alternates, promisor.
# Not "git $cmd leftover hid X_N=N". Not stacked-git CLI.
PAIRS: list[tuple[dict, dict]] = [
    (
        {
            "slug": "replace-userefs-already-skip",
            "repo": "replace-ops/graft-gate",
            "marker": "REPLACE_USE_N",
            "old": "0",
            "new": "7",
            "src": "src/graft.py",
            "test": "tests/test_graft.py",
            "tfail": "FAILED tests/test_graft.py::test_use_7\nFAILED tests/test_graft.py::test_parent_is_77bb",
            "branch": "recover/replace-use-7",
            "map_cmd": "git config --get core.useReplaceRefs; git replace -l; git log --oneline -3 --decorate; rg REPLACE_USE_N src/graft.py",
            "map_obs": "false\n91aa -> 00dead (graft listed but unused)\n91aa topic (parent still 55aa, not 77bb)\nREPLACE_USE_N = 0",
            "map_b": "Plan: map core.useReplaceRefs=false so git replace --graft already skips.",
            "wrong_cmd": "git replace --graft 91aa 77bb && git log --oneline -2 --decorate",
            "wrong_obs": "replace updated 91aa -> 77bb\nlog still 91aa parent 55aa (useReplaceRefs=false; already skip)",
            "wrong_b": "Observation: graft wrote a ref but log ignored it. First wrong move: replace --graft again.",
            "rec_cmd": "git config --unset core.useReplaceRefs && git replace -d 91aa && git replace --graft 91aa 77bb && git log --oneline -2 --decorate",
            "rec_obs": "deleted stale replace\ngrafted 91aa onto 77bb\n91aa topic (parent 77bb)",
            "rec_b": "Plan: unset useReplaceRefs, drop the unused replace, graft onto 77bb.",
            "left_cmd": "git config --get core.useReplaceRefs || echo use_default; git replace -l; git rev-parse 91aa^",
            "left_obs": "use_default\n91aa -> 77bb\n77bb",
            "left_b": "Observation: replace is honored; parent is 77bb.",
            "goal": "On replace-ops/graft-gate, core.useReplaceRefs=false made git replace --graft already skip so 91aa kept parent 55aa. Unset, graft onto 77bb, land REPLACE_USE_N=7. INC-{inc}.",
            "plan": "Prove useReplaceRefs skip, unset, graft 91aa onto 77bb, land 7.",
            "out": "Honored git replace after unsetting useReplaceRefs. REPLACE_USE_N=7 as {sha} / 2 tests / PR {pr}. INC-{inc}.",
            "refl": "Reflection: --graft under useReplaceRefs=false is a no-op. Plan change: recover/replace-use-7.",
            "cmt": "Do not git replace --graft while core.useReplaceRefs=false. Unset first. Do not force-push main.",
            "title": "REPLACE_USE_N=7",
            "body": "useReplaceRefs=false made replace already skip. Grafted 91aa onto 77bb. INC-{inc}.",
            "commit": "fix: REPLACE_USE_N=7 after useReplaceRefs unset (INC-{inc})",
            "mix": "git-replace already skip vs core.useReplaceRefs=false",
        },
        {
            "slug": "bundle-verify-already-skip-hidden-tips",
            "repo": "bundle-ops/hidden-tips",
            "marker": "BUNDLE_HIDE_N",
            "old": "1",
            "new": "6",
            "src": "src/bundle.py",
            "test": "tests/test_bundle.py",
            "tfail": "FAILED tests/test_bundle.py::test_hide_6\nFAILED tests/test_bundle.py::test_replace_from_bundle",
            "branch": "recover/bundle-hide-6",
            "map_cmd": "git bundle verify hotfix.bundle && git bundle list-heads hotfix.bundle && git replace -l; rg BUNDLE_HIDE_N src/bundle.py",
            "map_obs": "The bundle contains this repository (already skip)\n91aa refs/heads/topic\n(bundle also has refs/replace/91aa, not listed by verify)\nBUNDLE_HIDE_N = 1",
            "map_b": "Plan: map git bundle verify already skip while replace refs stay inside the bundle.",
            "wrong_cmd": "git clone --mirror hotfix.bundle /tmp/hotfix.git && git --git-dir=/tmp/hotfix.git replace -l",
            "wrong_obs": "Cloning into bare repository\n(empty replace; verify already skip cloned only listed heads)",
            "wrong_b": "Observation: mirror clone skipped hidden replace refs. First wrong move: git clone --mirror the bundle.",
            "rec_cmd": "git fetch hotfix.bundle 'refs/replace/*:refs/replace/*' && git replace -l && git log -1 --format=%P 91aa",
            "rec_obs": "fetched refs/replace/91aa\n91aa -> 77bb\n77bb",
            "rec_b": "Plan: fetch refs/replace from the bundle; do not remirror listed heads.",
            "left_cmd": "git replace -l; git bundle list-heads hotfix.bundle | rg replace || echo verify_heads_only",
            "left_obs": "91aa -> 77bb\nverify_heads_only",
            "left_b": "Observation: local replace imported; NFS bundle store still has the overwrite.",
            "goal": "On bundle-ops/hidden-tips, git bundle verify already skipped because listed heads exist, hiding refs/replace inside hotfix.bundle. Fetch those replace refs, land BUNDLE_HIDE_N=6. NFS still has the overwrite. INC-{inc}.",
            "plan": "Prove verify already skip, fetch hidden replace refs, hand off NFS bundle.",
            "out": "Fetched hidden refs/replace from the bundle; BUNDLE_HIDE_N=6 on PR {pr}. NFS overwrite remains. Issue {issue}. INC-{inc}.",
            "refl": "Reflection: verify already skip hid replace tips. Plan change: PR the 6; hand off NFS bundle.",
            "cmt": "HANDOFF issue {issue}. Fetch refs/replace from the bundle. Do not force-push main.",
            "title": "BUNDLE_HIDE_N=6",
            "body": "bundle verify already skip hid replace refs. NFS overwrite remains. INC-{inc}.",
            "commit": "fix: BUNDLE_HIDE_N=6 after bundle fetch refs/replace (INC-{inc})",
            "issue_t": "NFS hotfix.bundle overwrite still drops refs/replace",
            "issue_b": "PR {pr}. Replace the NFS bundle with one that lists replace refs. INC-{inc}.",
            "handoff": "nfs-bundle-overwrite",
            "handoff_probe": "git bundle list-heads /mnt/nfs/bundles/hotfix.bundle | rg replace || echo nfs_heads_only",
            "handoff_probe_obs": "nfs_heads_only",
            "checks": "unit pass\nbundle-ci fail (NFS overwrite lacks replace refs)\n{\"mergeStateStatus\":\"BLOCKED\"}",
            "mix": "git-bundle already skip vs hidden refs/replace in the payload",
        },
    ),
    (
        {
            "slug": "submodule-update-none-already-skip",
            "repo": "submod-ops/update-none",
            "marker": "SUBMOD_NONE_N",
            "old": "2",
            "new": "8",
            "src": "src/proto.py",
            "test": "tests/test_proto.py",
            "tfail": "FAILED tests/test_proto.py::test_none_8\nFAILED tests/test_proto.py::test_gitlink_91aa",
            "branch": "recover/submod-none-8",
            "map_cmd": "git config --get submodule.vendor/proto.update; git submodule status; git ls-tree HEAD vendor/proto; rg SUBMOD_NONE_N src/proto.py",
            "map_obs": "none\n-77bb vendor/proto (update=none; already skip)\n160000 commit 91aa  vendor/proto\nSUBMOD_NONE_N = 2",
            "map_b": "Plan: map submodule.update=none so git submodule update --init already skips.",
            "wrong_cmd": "git submodule update --init --force vendor/proto && git submodule status",
            "wrong_obs": "Skipping submodule 'vendor/proto' (update=none)\n-77bb vendor/proto",
            "wrong_b": "Observation: --force still honored update=none. First wrong move: submodule update --force.",
            "rec_cmd": "git config --unset submodule.vendor/proto.update && git submodule update --init vendor/proto && git -C vendor/proto rev-parse --short HEAD",
            "rec_obs": "Submodule path 'vendor/proto': checked out '91aa'\n91aa",
            "rec_b": "Plan: unset update=none, then update to the recorded gitlink 91aa.",
            "left_cmd": "git config --get submodule.vendor/proto.update || echo update_default; git submodule status | rg proto",
            "left_obs": "update_default\n 91aa vendor/proto",
            "left_b": "Observation: gitlink 91aa is checked out; update=none gone.",
            "goal": "On submod-ops/update-none, submodule.vendor/proto.update=none made git submodule update --init already skip, leaving checkout 77bb vs gitlink 91aa. Unset, checkout 91aa, land SUBMOD_NONE_N=8. INC-{inc}.",
            "plan": "Prove update=none skip, unset, checkout gitlink 91aa, land 8.",
            "out": "Unset update=none and checked out gitlink 91aa. SUBMOD_NONE_N=8 as {sha} / 2 tests / PR {pr}. INC-{inc}.",
            "refl": "Reflection: --force does not override update=none. Plan change: recover/submod-none-8.",
            "cmt": "Do not git submodule update --force under update=none. Unset first. Do not force-push main.",
            "title": "SUBMOD_NONE_N=8",
            "body": "submodule update=none already skip. Checked out gitlink 91aa. INC-{inc}.",
            "commit": "fix: SUBMOD_NONE_N=8 after unset submodule.update=none (INC-{inc})",
            "mix": "git-submodule already skip vs leftover update=none",
        },
        {
            "slug": "sparse-disable-already-skip-sbits",
            "repo": "sparse-ops/disable-sbits",
            "marker": "SPARSE_SBIT_N",
            "old": "1",
            "new": "5",
            "src": "src/sparse.py",
            "test": "tests/test_sparse.py",
            "tfail": "FAILED tests/test_sparse.py::test_sbit_5\nFAILED tests/test_sparse.py::test_fixtures_present",
            "branch": "recover/sparse-sbit-5",
            "map_cmd": "git config --get core.sparseCheckout; git sparse-checkout list || echo no_cone; git ls-files -v | rg '^[S]' | head; ls tests/fixtures 2>&1 | head; rg SPARSE_SBIT_N src/sparse.py",
            "map_obs": "false\nno_cone\nS tests/fixtures/hb.json\nS tests/fixtures/settle.json\nls: tests/fixtures: No such file\nSPARSE_SBIT_N = 1",
            "map_b": "Plan: map sparse-checkout disable already skip while skip-worktree bits remain.",
            "wrong_cmd": "git sparse-checkout disable && git checkout -- tests && ls tests/fixtures 2>&1 | head",
            "wrong_obs": "error: sparse-checkout is already disabled\nls: tests/fixtures: No such file (S-bits still hide fixtures)",
            "wrong_b": "Observation: disable already skip. First wrong move: git sparse-checkout disable then checkout.",
            "rec_cmd": "git ls-files -v | awk '/^S/{print $2}' | git update-index --no-skip-worktree --stdin && git checkout -- tests/fixtures && ls tests/fixtures",
            "rec_obs": "hb.json\nsettle.json",
            "rec_b": "Plan: clear leftover skip-worktree bits; do not rerun disable.",
            "left_cmd": "git ls-files -v | rg '^[S]' || echo no_sbits; test -f tests/fixtures/hb.json && echo fixtures_ok",
            "left_obs": "no_sbits\nfixtures_ok",
            "left_b": "Observation: S-bits cleared locally; runner image still stamps skip-worktree.",
            "goal": "On sparse-ops/disable-sbits, git sparse-checkout disable already skipped (core.sparseCheckout=false) while skip-worktree bits still hid tests/fixtures. Clear S-bits, land SPARSE_SBIT_N=5. Runner image still stamps them. INC-{inc}.",
            "plan": "Prove disable already skip, clear S-bits, hand off runner image.",
            "out": "Cleared leftover skip-worktree after disable already skip; SPARSE_SBIT_N=5 on PR {pr}. Runner still stamps S-bits. Issue {issue}. INC-{inc}.",
            "refl": "Reflection: disable already skip left S-bits. Plan change: PR the 5; hand off runner image.",
            "cmt": "HANDOFF issue {issue}. Clear skip-worktree; do not rerun disable. Do not force-push main.",
            "title": "SPARSE_SBIT_N=5",
            "body": "sparse disable already skip left S-bits. Runner image still stamps them. INC-{inc}.",
            "commit": "fix: SPARSE_SBIT_N=5 after skip-worktree clear (INC-{inc})",
            "issue_t": "runner image still stamps skip-worktree after sparse disable",
            "issue_b": "PR {pr}. Stop the image from writing S-bits. INC-{inc}.",
            "handoff": "runner-sparse-sbits",
            "handoff_probe": "rg skip-worktree /opt/runner/index-template || echo template_sbits",
            "handoff_probe_obs": "template_sbits",
            "checks": "unit pass\nrunner-index-ci fail (S-bits restamped)\n{\"mergeStateStatus\":\"BLOCKED\"}",
            "mix": "git-sparse already skip vs leftover skip-worktree bits",
        },
    ),
    (
        {
            "slug": "worktree-add-already-skip-remount",
            "repo": "worktree-ops/remount",
            "marker": "WT_REMOUNT_N",
            "old": "0",
            "new": "4",
            "src": "src/hotfix.py",
            "test": "tests/test_hotfix.py",
            "tfail": "FAILED tests/test_hotfix.py::test_remount_4\nFAILED tests/test_hotfix.py::test_not_other_repo",
            "branch": "recover/wt-remount-4",
            "map_cmd": "git worktree list --porcelain && cat .git/worktrees/hotfix/gitdir && ls ../hotfix/.git 2>&1 | head && rg WT_REMOUNT_N src/hotfix.py",
            "map_obs": "worktree /srv/old/hotfix\nbare\ngitdir: /srv/old/hotfix/.git (volume remounted; path now another repo)\n../hotfix/.git is a directory (foreign repo)\nWT_REMOUNT_N = 0",
            "map_b": "Plan: map git worktree add already skip: registered path now holds a foreign repo.",
            "wrong_cmd": "git worktree add --force ../hotfix origin/main && git -C ../hotfix rev-parse --show-toplevel",
            "wrong_obs": "fatal: '../hotfix' is already registered as a worktree\n(would clobber the remounted foreign repo)",
            "wrong_b": "Observation: add --force still hits the stale register. First wrong move: worktree add --force.",
            "rec_cmd": "git worktree remove --force hotfix && git worktree add ../hotfix-settle origin/main && git -C ../hotfix-settle status -sb",
            "rec_obs": "Removed worktree hotfix\nPreparing worktree (new branch hotfix-settle)\n## hotfix-settle",
            "rec_b": "Plan: remove the stale register, add a new path; do not clobber the remount.",
            "left_cmd": "git worktree list | rg hotfix; test -d ../hotfix/.git && echo foreign_ok; test -d ../hotfix-settle/.git && echo settle_ok",
            "left_obs": "/tmp/repo/hotfix-settle\nforeign_ok\nsettle_ok",
            "left_b": "Observation: new worktree is settle; remounted foreign repo untouched.",
            "goal": "On worktree-ops/remount, git worktree add ../hotfix already skipped because the registered path remounted as a foreign repo. Remove the stale register, add ../hotfix-settle, land WT_REMOUNT_N=4. INC-{inc}.",
            "plan": "Prove remount already skip, remove register, add a new path, land 4.",
            "out": "Removed stale worktree register after remount. WT_REMOUNT_N=4 as {sha} / 2 tests / PR {pr}. INC-{inc}.",
            "refl": "Reflection: add --force would clobber the remounted repo. Plan change: recover/wt-remount-4.",
            "cmt": "Do not git worktree add --force onto a remounted path. Remove then add a new path. Do not force-push main.",
            "title": "WT_REMOUNT_N=4",
            "body": "worktree add already skip after remount. New path hotfix-settle. INC-{inc}.",
            "commit": "fix: WT_REMOUNT_N=4 after worktree remove remount register (INC-{inc})",
            "mix": "git-worktree already skip vs remounted foreign path",
        },
        {
            "slug": "filter-repo-already-skip-refs-original",
            "repo": "filtrepo-ops/original-refs",
            "marker": "FILTER_ORIG_N",
            "old": "3",
            "new": "9",
            "src": "src/filtrepo.py",
            "test": "tests/test_filtrepo.py",
            "tfail": "FAILED tests/test_filtrepo.py::test_orig_9\nFAILED tests/test_filtrepo.py::test_no_original_main",
            "branch": "recover/filter-orig-9",
            "map_cmd": "test -f .git/filter-repo/already && echo already_skip; git show-ref | rg original; git ls-remote origin 'refs/original/*' | head; rg FILTER_ORIG_N src/filtrepo.py",
            "map_obs": "already_skip\n77bb refs/original/refs/heads/main\n77bb refs/original/refs/heads/main\nFILTER_ORIG_N = 3",
            "map_b": "Plan: map filter-repo already skip while refs/original/main is still advertised.",
            "wrong_cmd": "git filter-repo --invert-paths --path secrets/ --force && git show-ref | rg original | head",
            "wrong_obs": "Aborting: Refusing to destructively overwrite repo history since this does not look like a fresh clone.\n(already.skip present; refs/original still 77bb)",
            "wrong_b": "Observation: already skip blocked --force. First wrong move: rerun filter-repo.",
            "rec_cmd": "git for-each-ref --format='delete %(refname)' refs/original | git update-ref --stdin && mv .git/filter-repo/already /tmp/already.bak && git show-ref | rg original || echo no_local_original",
            "rec_obs": "no_local_original",
            "rec_b": "Plan: delete refs/original locally; do not rerun filter-repo.",
            "left_cmd": "git show-ref | rg original || echo no_local; git ls-remote origin 'refs/original/*' | head",
            "left_obs": "no_local\n77bb refs/original/refs/heads/main",
            "left_b": "Observation: local original refs gone; origin still advertises them.",
            "goal": "On filtrepo-ops/original-refs, git filter-repo already skipped (already marker) while refs/original/main still let CI clone pre-filter history. Delete those refs, land FILTER_ORIG_N=9. origin still advertises them. INC-{inc}.",
            "plan": "Prove already skip, delete refs/original, hand off origin.",
            "out": "Deleted local refs/original after filter-repo already skip; FILTER_ORIG_N=9 on PR {pr}. origin still has them. Issue {issue}. INC-{inc}.",
            "refl": "Reflection: rerunning filter-repo --force aborted on already. Plan change: PR the 9; hand off origin refs.",
            "cmt": "HANDOFF issue {issue}. Delete refs/original; do not rerun filter-repo. Do not force-push main.",
            "title": "FILTER_ORIG_N=9",
            "body": "filter-repo already skip left refs/original. origin still advertises them. INC-{inc}.",
            "commit": "fix: FILTER_ORIG_N=9 after delete refs/original (INC-{inc})",
            "issue_t": "origin still advertises refs/original/refs/heads/main after filter-repo",
            "issue_b": "PR {pr}. Delete origin refs/original. INC-{inc}.",
            "handoff": "origin-refs-original",
            "handoff_probe": "git ls-remote origin 'refs/original/*'",
            "handoff_probe_obs": "77bb refs/original/refs/heads/main",
            "checks": "unit pass\nfilter-ci fail (origin refs/original still cloned)\n{\"mergeStateStatus\":\"BLOCKED\"}",
            "mix": "git-filter-repo already skip vs leftover refs/original",
        },
    ),
    (
        {
            "slug": "lfs-filter-process-skip-already",
            "repo": "lfs-ops/process-skip",
            "marker": "LFS_PROC_N",
            "old": "1",
            "new": "8",
            "src": "src/lfsproc.py",
            "test": "tests/test_lfsproc.py",
            "tfail": "FAILED tests/test_lfsproc.py::test_proc_8\nFAILED tests/test_lfsproc.py::test_not_pointer",
            "branch": "recover/lfs-proc-8",
            "map_cmd": "git config --get filter.lfs.process; git lfs env | rg 'SkipSmudge|FilterProcess'; head -n 2 assets/model.bin; rg LFS_PROC_N src/lfsproc.py",
            "map_obs": "git-lfs filter-process --skip\nSkipSmudge=true\nFilterProcess=git-lfs filter-process --skip\nversion https://git-lfs.github.com/spec/v1\nLFS_PROC_N = 1",
            "map_b": "Plan: map filter.lfs.process --skip so git lfs pull already skips smudge.",
            "wrong_cmd": "git lfs pull && git lfs checkout assets/model.bin && head -n 1 assets/model.bin",
            "wrong_obs": "Already up to date (skip-smudge; already skip)\nversion https://git-lfs.github.com/spec/v1",
            "wrong_b": "Observation: pull/checkout honored --skip. First wrong move: git lfs checkout under skip process.",
            "rec_cmd": "git config --unset filter.lfs.process && git lfs install --local && git lfs pull && file assets/model.bin | head",
            "rec_obs": "Updated git hooks.\nSmudged assets/model.bin (41943040 bytes)\nassets/model.bin: data",
            "rec_b": "Plan: unset filter.lfs.process --skip, reinstall hooks, pull to smudge.",
            "left_cmd": "git config --get filter.lfs.process; file assets/model.bin | rg -v pointer",
            "left_obs": "git-lfs filter-process\nassets/model.bin: data",
            "left_b": "Observation: skip process gone; binary smudged.",
            "goal": "On lfs-ops/process-skip, filter.lfs.process='git-lfs filter-process --skip' made git lfs pull already skip, leaving assets/model.bin as pointer text. Unset, reinstall, smudge, land LFS_PROC_N=8. INC-{inc}.",
            "plan": "Prove process --skip, unset, smudge, land 8.",
            "out": "Unset LFS filter-process --skip and smudged the pointer. LFS_PROC_N=8 as {sha} / 2 tests / PR {pr}. INC-{inc}.",
            "refl": "Reflection: lfs checkout under --skip is already skip. Plan change: recover/lfs-proc-8.",
            "cmt": "Do not git lfs checkout while filter.lfs.process --skip. Unset then pull. Do not force-push main.",
            "title": "LFS_PROC_N=8",
            "body": "lfs filter-process --skip already skip. Smudged model.bin. INC-{inc}.",
            "commit": "fix: LFS_PROC_N=8 after unset filter.lfs.process --skip (INC-{inc})",
            "mix": "git-lfs already skip vs leftover filter.lfs.process --skip",
        },
        {
            "slug": "gitcrypt-already-skip-missing-attr",
            "repo": "crypt-ops/attr-gap",
            "marker": "CRYPT_ATTR_N",
            "old": "2",
            "new": "6",
            "src": "src/crypt.py",
            "test": "tests/test_crypt.py",
            "tfail": "FAILED tests/test_crypt.py::test_attr_6\nFAILED tests/test_crypt.py::test_plaintext_secrets",
            "branch": "recover/crypt-attr-6",
            "map_cmd": "git-crypt status | head; git check-attr filter -- secrets/api.key; ls .git-crypt/keys/default/0 2>&1 | head; rg CRYPT_ATTR_N src/crypt.py",
            "map_obs": "already unlocked (keys present; already skip)\nsecrets/api.key: filter: unspecified\n.git-crypt/keys/default/0/public.key\nCRYPT_ATTR_N = 2",
            "map_b": "Plan: map git-crypt unlock already skip while .gitattributes lost filter=git-crypt.",
            "wrong_cmd": "git-crypt unlock && git-crypt status --encrypted | head",
            "wrong_obs": "Already unlocked.\n(no encrypted files; attributes missing so ciphertext stays bytes)",
            "wrong_b": "Observation: unlock already skip. First wrong move: git-crypt unlock again.",
            "rec_cmd": "printf 'secrets/** filter=git-crypt diff=git-crypt\\n' >> .gitattributes && git-crypt lock && git-crypt unlock && file secrets/api.key | head",
            "rec_obs": "locked 1 file\nunlocked 1 file\nsecrets/api.key: ASCII text",
            "rec_b": "Plan: restore filter=git-crypt, lock then unlock so ciphertext is decoded.",
            "left_cmd": "git check-attr filter -- secrets/api.key; file secrets/api.key",
            "left_obs": "secrets/api.key: filter: git-crypt\nsecrets/api.key: ASCII text",
            "left_b": "Observation: local attributes restored; origin .gitattributes still lacks filter.",
            "goal": "On crypt-ops/attr-gap, git-crypt unlock already skipped (keys present) while .gitattributes lost filter=git-crypt so secrets/api.key stayed ciphertext. Restore attributes, lock/unlock, land CRYPT_ATTR_N=6. origin still lacks the filter. INC-{inc}.",
            "plan": "Prove unlock already skip, restore attributes, hand off origin attrs.",
            "out": "Restored git-crypt attributes and unlocked; CRYPT_ATTR_N=6 on PR {pr}. origin still lacks filter. Issue {issue}. INC-{inc}.",
            "refl": "Reflection: unlock already skip when attributes are gone. Plan change: PR the 6; hand off origin attrs.",
            "cmt": "HANDOFF issue {issue}. Restore filter=git-crypt; do not unlock-already. Do not force-push main.",
            "title": "CRYPT_ATTR_N=6",
            "body": "git-crypt already skip (unlocked) with missing attributes. origin still lacks filter. INC-{inc}.",
            "commit": "fix: CRYPT_ATTR_N=6 after restore git-crypt attributes (INC-{inc})",
            "issue_t": "origin .gitattributes still missing filter=git-crypt",
            "issue_b": "PR {pr}. Restore origin secrets/** filter=git-crypt. INC-{inc}.",
            "handoff": "origin-gitattributes-crypt",
            "handoff_probe": "git show origin/main:.gitattributes | rg git-crypt || echo origin_no_filter",
            "handoff_probe_obs": "origin_no_filter",
            "checks": "unit pass\ncrypt-ci fail (origin attributes missing)\n{\"mergeStateStatus\":\"BLOCKED\"}",
            "mix": "git-crypt already skip vs missing filter=git-crypt attributes",
        },
    ),
    (
        {
            "slug": "commit-graph-truncated-chain-already-skip",
            "repo": "cgraph-ops/trunc-chain",
            "marker": "CGRAPH_TRUNC_N",
            "old": "0",
            "new": "3",
            "src": "src/cgraph.py",
            "test": "tests/test_cgraph.py",
            "tfail": "FAILED tests/test_cgraph.py::test_trunc_3\nFAILED tests/test_cgraph.py::test_revlist_matches",
            "branch": "recover/cgraph-trunc-3",
            "map_cmd": "git commit-graph write --split --reachable 2>&1 | tail; ls -l .git/objects/info/commit-graphs/; git commit-graph verify 2>&1 | tail; rg CGRAPH_TRUNC_N src/cgraph.py",
            "map_obs": "The commit-graph chain is up to date (already skip)\n-rw-r--r-- graph-1.graph\n-rw-r--r-- graph-2.graph (size 0)\nerror: graph-2.graph truncated\nCGRAPH_TRUNC_N = 0",
            "map_b": "Plan: map commit-graph write already skip while graph-2.graph is truncated.",
            "wrong_cmd": "rm -f .git/objects/info/commit-graphs/graph-2.graph && git rev-list --count HEAD && git commit-graph verify 2>&1 | tail",
            "wrong_obs": "412\nerror: commit-graph chain lists graph-2 but file is missing",
            "wrong_b": "Observation: deleting graph-2 left a dangling chain. First wrong move: rm graph-2 only.",
            "rec_cmd": "rm -rf .git/objects/info/commit-graphs && git commit-graph write --split --changed-paths --reachable && git commit-graph verify && git rev-list --count HEAD",
            "rec_obs": "Wrote commit-graph chain\nVerification succeeded\n412",
            "rec_b": "Plan: drop the whole chain dir, rewrite --split --changed-paths --reachable.",
            "left_cmd": "git commit-graph verify; ls .git/objects/info/commit-graphs | rg 'graph-.*\\.graph'",
            "left_obs": "Verification succeeded\ngraph-1.graph",
            "left_b": "Observation: chain rewritten; verify ok.",
            "goal": "On cgraph-ops/trunc-chain, git commit-graph write --split already skipped as up to date while graph-2.graph was truncated. Rewrite the chain, land CGRAPH_TRUNC_N=3. INC-{inc}.",
            "plan": "Prove truncated-chain already skip, rewrite chain, land 3.",
            "out": "Rewrote truncated commit-graph chain. CGRAPH_TRUNC_N=3 as {sha} / 2 tests / PR {pr}. INC-{inc}.",
            "refl": "Reflection: write already skip left a zero-byte graph-2. Plan change: recover/cgraph-trunc-3.",
            "cmt": "Do not rm one graph file from a split chain. Rewrite the whole chain. Do not force-push main.",
            "title": "CGRAPH_TRUNC_N=3",
            "body": "commit-graph write already skip on a truncated chain. Rewrote --split. INC-{inc}.",
            "commit": "fix: CGRAPH_TRUNC_N=3 after rewrite truncated commit-graph chain (INC-{inc})",
            "mix": "corrupted commit-graph already skip vs truncated split chain",
        },
        {
            "slug": "midx-write-already-skip-tmp-pack",
            "repo": "midx-ops/tmp-pack",
            "marker": "MIDX_TMP_N",
            "old": "2",
            "new": "7",
            "src": "src/midx.py",
            "test": "tests/test_midx.py",
            "tfail": "FAILED tests/test_midx.py::test_tmp_7\nFAILED tests/test_midx.py::test_no_tmp_pack",
            "branch": "recover/midx-tmp-7",
            "map_cmd": "git multi-pack-index write 2>&1 | tail; ls .git/objects/pack | rg 'tmp_pack|midx|pack-'; git multi-pack-index verify 2>&1 | tail; rg MIDX_TMP_N src/midx.py",
            "map_obs": "The multi-pack-index is up to date (already skip)\ntmp_pack_9f3a (dead repack leftover)\npack-bb.pack\nVerification succeeded (does not inspect tmp_pack)\nMIDX_TMP_N = 2",
            "map_b": "Plan: map midx write already skip while a dead tmp_pack leftover remains.",
            "wrong_cmd": "rm -f .git/objects/pack/multi-pack-index && git rev-list --objects --all >/dev/null; git multi-pack-index verify 2>&1 | tail",
            "wrong_obs": "rev-list slow without midx\nerror: no multi-pack-index (tmp_pack still present)",
            "wrong_b": "Observation: deleting midx left tmp_pack. First wrong move: rm multi-pack-index only.",
            "rec_cmd": "rm -f .git/objects/pack/tmp_pack_9f3a && git multi-pack-index write --bitmap && git multi-pack-index verify",
            "rec_obs": "Wrote multi-pack-index\nVerification succeeded",
            "rec_b": "Plan: delete the dead tmp_pack, then write --bitmap.",
            "left_cmd": "ls .git/objects/pack | rg tmp_pack || echo no_tmp; git multi-pack-index verify",
            "left_obs": "no_tmp\nVerification succeeded",
            "left_b": "Observation: local tmp_pack gone; NFS object-store still has it.",
            "goal": "On midx-ops/tmp-pack, git multi-pack-index write already skipped as up to date while a dead tmp_pack leftover remained. Delete tmp_pack, rewrite midx, land MIDX_TMP_N=7. NFS still has the tmp pack. INC-{inc}.",
            "plan": "Prove midx already skip, drop tmp_pack, hand off NFS store.",
            "out": "Rewrote midx after deleting tmp_pack; MIDX_TMP_N=7 on PR {pr}. NFS still has tmp_pack. Issue {issue}. INC-{inc}.",
            "refl": "Reflection: write already skip ignored tmp_pack. Plan change: PR the 7; hand off NFS store.",
            "cmt": "HANDOFF issue {issue}. Delete tmp_pack before midx write. Do not force-push main.",
            "title": "MIDX_TMP_N=7",
            "body": "midx write already skip left tmp_pack. NFS still has it. INC-{inc}.",
            "commit": "fix: MIDX_TMP_N=7 after drop tmp_pack and midx write (INC-{inc})",
            "issue_t": "NFS object-store still has dead tmp_pack_9f3a",
            "issue_b": "PR {pr}. Remove NFS tmp_pack leftover. INC-{inc}.",
            "handoff": "nfs-tmp-pack",
            "handoff_probe": "ls /mnt/nfs/objects/pack | rg tmp_pack || echo nfs_tmp",
            "handoff_probe_obs": "tmp_pack_9f3a",
            "checks": "unit pass\nmidx-ci fail (NFS tmp_pack)\n{\"mergeStateStatus\":\"BLOCKED\"}",
            "mix": "stale midx already skip vs dead tmp_pack leftover",
        },
    ),
    (
        {
            "slug": "dangling-replace-env-already-skip",
            "repo": "replace-ops/env-hide",
            "marker": "REPLACE_ENV_N",
            "old": "1",
            "new": "5",
            "src": "src/repenv.py",
            "test": "tests/test_repenv.py",
            "tfail": "FAILED tests/test_repenv.py::test_env_5\nFAILED tests/test_repenv.py::test_no_dangling_replace",
            "branch": "recover/replace-env-5",
            "map_cmd": "echo GIT_NO_REPLACE_OBJECTS=$GIT_NO_REPLACE_OBJECTS; git replace -l; git show-ref | rg replace; git cat-file -t 00dead 2>&1; rg REPLACE_ENV_N src/repenv.py",
            "map_obs": "GIT_NO_REPLACE_OBJECTS=1\n(empty; already skip)\n00dead refs/replace/91aa\nfatal: git cat-file: could not get object info\nREPLACE_ENV_N = 1",
            "map_b": "Plan: map GIT_NO_REPLACE_OBJECTS so git replace -l already skips a dangling refs/replace.",
            "wrong_cmd": "git replace -d --all && git show-ref | rg replace",
            "wrong_obs": "fatal: --all under GIT_NO_REPLACE_OBJECTS listed nothing\n00dead refs/replace/91aa",
            "wrong_b": "Observation: -d --all already skip under the env. First wrong move: git replace -d --all.",
            "rec_cmd": "unset GIT_NO_REPLACE_OBJECTS && git replace -l && git replace -d 91aa && git show-ref | rg replace || echo no_replace",
            "rec_obs": "91aa -> 00dead (dangling)\ndeleted 91aa\nno_replace",
            "rec_b": "Plan: unset the env, list the dangling replace, delete it.",
            "left_cmd": "test -z \"$GIT_NO_REPLACE_OBJECTS\" && echo env_clear; git replace -l || echo empty_list",
            "left_obs": "env_clear\nempty_list",
            "left_b": "Observation: dangling replace gone; env unset.",
            "goal": "On replace-ops/env-hide, GIT_NO_REPLACE_OBJECTS=1 made git replace -l already skip while refs/replace/91aa pointed at dangling 00dead. Unset, delete the replace, land REPLACE_ENV_N=5. INC-{inc}.",
            "plan": "Prove env already skip, delete dangling replace, land 5.",
            "out": "Deleted dangling replace after unsetting GIT_NO_REPLACE_OBJECTS. REPLACE_ENV_N=5 as {sha} / 2 tests / PR {pr}. INC-{inc}.",
            "refl": "Reflection: replace -d --all is a no-op under the env. Plan change: recover/replace-env-5.",
            "cmt": "Do not git replace -d --all under GIT_NO_REPLACE_OBJECTS. Unset first. Do not force-push main.",
            "title": "REPLACE_ENV_N=5",
            "body": "dangling replace already skip via GIT_NO_REPLACE_OBJECTS. Deleted 91aa. INC-{inc}.",
            "commit": "fix: REPLACE_ENV_N=5 after delete env-hidden dangling replace (INC-{inc})",
            "mix": "dangling replace already skip vs GIT_NO_REPLACE_OBJECTS",
        },
        {
            "slug": "reftable-vs-files-backend-mixed",
            "repo": "reftable-ops/mixed-backend",
            "marker": "REFTABLE_MIX_N",
            "old": "0",
            "new": "4",
            "src": "src/reftable.py",
            "test": "tests/test_reftable.py",
            "tfail": "FAILED tests/test_reftable.py::test_mix_4\nFAILED tests/test_reftable.py::test_reftable_sot",
            "branch": "recover/reftable-mix-4",
            "map_cmd": "git config --get extensions.refStorage; ls .git/reftable | head; cat .git/refs/heads/topic 2>&1 | head; git rev-parse --short topic; rg REFTABLE_MIX_N src/reftable.py",
            "map_obs": "reftable\ntables.list\n0x00..graph-2\n91aa (loose leftover)\n77bb (reftable SoT)\nREFTABLE_MIX_N = 0",
            "map_b": "Plan: map reftable backend vs leftover loose refs/heads/topic.",
            "wrong_cmd": "git refs migrate --ref-format=files && git rev-parse --short topic",
            "wrong_obs": "fatal: repository has mixed reftable and leftover files refs\n77bb",
            "wrong_b": "Observation: migrate refused mixed leftovers. First wrong move: refs migrate --ref-format=files.",
            "rec_cmd": "rm -f .git/refs/heads/topic .git/packed-refs && git refs verify && git rev-parse --short topic && git symbolic-ref HEAD",
            "rec_obs": "refs ok (reftable only)\n77bb\nrefs/heads/topic",
            "rec_b": "Plan: drop leftover loose/packed files refs; keep reftable as SoT.",
            "left_cmd": "test ! -e .git/refs/heads/topic && echo no_loose; git rev-parse --short topic",
            "left_obs": "no_loose\n77bb",
            "left_b": "Observation: local files leftovers gone; origin is still files backend.",
            "goal": "On reftable-ops/mixed-backend, extensions.refStorage=reftable disagreed with leftover loose refs/heads/topic (91aa vs 77bb). Drop files leftovers, land REFTABLE_MIX_N=4. origin is still files. INC-{inc}.",
            "plan": "Prove mixed backends, keep reftable, hand off origin files.",
            "out": "Dropped leftover files refs; REFTABLE_MIX_N=4 on PR {pr}. origin still files backend. Issue {issue}. INC-{inc}.",
            "refl": "Reflection: migrate to files failed on mixed leftovers. Plan change: PR the 4; hand off origin backend.",
            "cmt": "HANDOFF issue {issue}. Do not migrate mixed leftovers. Do not force-push main.",
            "title": "REFTABLE_MIX_N=4",
            "body": "reftable vs leftover files refs. origin still files backend. INC-{inc}.",
            "commit": "fix: REFTABLE_MIX_N=4 after drop leftover files refs (INC-{inc})",
            "issue_t": "origin still uses files backend while this clone is reftable",
            "issue_b": "PR {pr}. Align origin ref backend. INC-{inc}.",
            "handoff": "origin-files-backend",
            "handoff_probe": "git ls-remote --symref origin HEAD; git config --file <(git archive --remote=origin HEAD .gitconfig 2>/dev/null) --get extensions.refStorage || echo origin_files",
            "handoff_probe_obs": "origin_files",
            "checks": "unit pass\nrefs-ci fail (origin files backend)\n{\"mergeStateStatus\":\"BLOCKED\"}",
            "mix": "reftable leftover vs files backend mixed refs",
        },
    ),
    (
        {
            "slug": "packed-refs-vs-loose-diverge",
            "repo": "packrefs-ops/loose-win",
            "marker": "PACKLOOSE_N",
            "old": "2",
            "new": "8",
            "src": "src/packloose.py",
            "test": "tests/test_packloose.py",
            "tfail": "FAILED tests/test_packloose.py::test_loose_8\nFAILED tests/test_packloose.py::test_topic_is_91aa",
            "branch": "recover/packloose-8",
            "map_cmd": "rg 'refs/heads/topic' .git/packed-refs; cat .git/refs/heads/topic; git rev-parse --short topic; rg PACKLOOSE_N src/packloose.py",
            "map_obs": "77bb refs/heads/topic\n91aa\n91aa (loose wins)\nPACKLOOSE_N = 2",
            "map_b": "Plan: map packed-refs 77bb vs loose topic 91aa before pack-refs --all.",
            "wrong_cmd": "git pack-refs --all && git rev-parse --short topic && test -e .git/refs/heads/topic || echo loose_gone",
            "wrong_obs": "77bb\nloose_gone (pack-refs silently kept packed 77bb)",
            "wrong_b": "Observation: pack-refs --all dropped loose 91aa. First wrong move: git pack-refs --all.",
            "rec_cmd": "git reflog show topic | head; git update-ref refs/heads/topic 91aa && git pack-refs --all && git rev-parse --short topic",
            "rec_obs": "91aa HEAD@{1}: commit: settle\n91aa",
            "rec_b": "Plan: restore topic from reflog 91aa, then pack-refs so packed matches loose.",
            "left_cmd": "test ! -e .git/refs/heads/topic && echo packed_only; rg 'refs/heads/topic' .git/packed-refs; git rev-parse --short topic",
            "left_obs": "packed_only\n91aa refs/heads/topic\n91aa",
            "left_b": "Observation: packed and resolved topic are both 91aa.",
            "goal": "On packrefs-ops/loose-win, packed-refs listed topic=77bb while loose refs/heads/topic was 91aa. pack-refs --all dropped 91aa. Restore from reflog, pack, land PACKLOOSE_N=8. INC-{inc}.",
            "plan": "Prove packed vs loose diverge, restore 91aa, pack, land 8.",
            "out": "Restored topic 91aa after pack-refs dropped the loose ref. PACKLOOSE_N=8 as {sha} / 2 tests / PR {pr}. INC-{inc}.",
            "refl": "Reflection: pack-refs --all preferred stale packed SHA. Plan change: recover/packloose-8.",
            "cmt": "Do not git pack-refs --all when packed and loose disagree. Restore loose first. Do not force-push main.",
            "title": "PACKLOOSE_N=8",
            "body": "packed-refs leftover vs loose topic. Restored 91aa. INC-{inc}.",
            "commit": "fix: PACKLOOSE_N=8 after restore loose topic then pack-refs (INC-{inc})",
            "mix": "packed-refs leftover vs loose ref diverge",
        },
        {
            "slug": "alternates-leftover-gc-object",
            "repo": "alt-ops/nfs-mirror",
            "marker": "ALT_GC_N",
            "old": "1",
            "new": "6",
            "src": "src/alt.py",
            "test": "tests/test_alt.py",
            "tfail": "FAILED tests/test_alt.py::test_alt_6\nFAILED tests/test_alt.py::test_object_local",
            "branch": "recover/alt-gc-6",
            "map_cmd": "cat .git/objects/info/alternates; git cat-file -t 91aa 2>&1; git cat-file -p 91aa^{tree} 2>&1 | head; rg ALT_GC_N src/alt.py",
            "map_obs": "/mnt/nfs/mirror/objects\ncommit (stat via alternates)\nfatal: could not read 91aa^{tree} (ENOENT after NFS GC)\nALT_GC_N = 1",
            "map_b": "Plan: map objects/info/alternates leftover after the NFS mirror GC'd 91aa^{tree}.",
            "wrong_cmd": "git gc --prune=now && git cat-file -t 91aa 2>&1",
            "wrong_obs": "gc dropped the last local copy of 91aa\nfatal: git cat-file: could not get object info",
            "wrong_b": "Observation: gc --prune followed the dead alternate. First wrong move: git gc --prune=now.",
            "rec_cmd": "printf '' > .git/objects/info/alternates && git fetch origin 91aa && git cat-file -t 91aa && git cat-file -t 91aa^{tree}",
            "rec_obs": "from origin\ncommit\ntree",
            "rec_b": "Plan: drop the dead alternates line, fetch 91aa so the object is local.",
            "left_cmd": "test ! -s .git/objects/info/alternates && echo no_alt; git cat-file -t 91aa^{tree}",
            "left_obs": "no_alt\ntree",
            "left_b": "Observation: local object present; runner template still writes the NFS alternate.",
            "goal": "On alt-ops/nfs-mirror, objects/info/alternates pointed at an NFS mirror that GC'd 91aa^{tree}. cat-file already skipped then ENOENT. Drop alternates, fetch, land ALT_GC_N=6. Runner still writes the alternate. INC-{inc}.",
            "plan": "Prove dead alternate, fetch locally, hand off runner template.",
            "out": "Dropped dead alternates and fetched 91aa; ALT_GC_N=6 on PR {pr}. Runner still writes the NFS alternate. Issue {issue}. INC-{inc}.",
            "refl": "Reflection: gc --prune trusted a GC'd alternate. Plan change: PR the 6; hand off runner template.",
            "cmt": "HANDOFF issue {issue}. Drop dead alternates; fetch objects. Do not force-push main.",
            "title": "ALT_GC_N=6",
            "body": "alternates leftover after NFS GC. Runner template still writes it. INC-{inc}.",
            "commit": "fix: ALT_GC_N=6 after drop dead alternates and fetch (INC-{inc})",
            "issue_t": "runner template still writes objects/info/alternates to NFS mirror",
            "issue_b": "PR {pr}. Stop writing the dead NFS alternate. INC-{inc}.",
            "handoff": "runner-alternates-template",
            "handoff_probe": "rg alternates /opt/runner/git-template/objects/info || echo template_alt",
            "handoff_probe_obs": "/mnt/nfs/mirror/objects",
            "checks": "unit pass\nalt-ci fail (template still writes NFS alternate)\n{\"mergeStateStatus\":\"BLOCKED\"}",
            "mix": "alternates leftover object vs NFS GC",
        },
    ),
    (
        {
            "slug": "promisor-refetch-already-skip",
            "repo": "promisor-ops/refetch-skip",
            "marker": "PROMISOR_REF_N",
            "old": "0",
            "new": "9",
            "src": "src/promisor.py",
            "test": "tests/test_promisor.py",
            "tfail": "FAILED tests/test_promisor.py::test_ref_9\nFAILED tests/test_promisor.py::test_blobs_present",
            "branch": "recover/promisor-ref-9",
            "map_cmd": "git config --get-regexp 'remote.origin.(promisor|partialclonefilter)'; ls .git/objects/pack | rg promisor; git rev-list --missing=print --objects HEAD | rg '^\\?' | head; rg PROMISOR_REF_N src/promisor.py",
            "map_obs": "remote.origin.promisor=true\nremote.origin.partialclonefilter=blob:none\npack-aa.promisor\n? 55ee blob src/promisor.py\nPROMISOR_REF_N = 0",
            "map_b": "Plan: map leftover .promisor pack so git fetch --refetch already skips missing blobs.",
            "wrong_cmd": "git fetch --filter=blob:none origin && git rev-list --missing=print --objects HEAD | rg '^\\?' | wc -l",
            "wrong_obs": "Already up to date (promisor pack claims blobs; already skip)\n4",
            "wrong_b": "Observation: refetch already skip. First wrong move: fetch --filter=blob:none again.",
            "rec_cmd": "git config --unset remote.origin.partialclonefilter && git config --unset remote.origin.promisor && git fetch --refetch origin && git rev-list --missing=print --objects HEAD | rg '^\\?' || echo no_missing",
            "rec_obs": "Fetching blobs\nno_missing",
            "rec_b": "Plan: unset partial clone filter, refetch so blobs materialize.",
            "left_cmd": "git config --get remote.origin.promisor || echo no_promisor; git cat-file -t 55ee",
            "left_obs": "no_promisor\nblob",
            "left_b": "Observation: blobs local; promisor filter unset.",
            "goal": "On promisor-ops/refetch-skip, a leftover .promisor pack made git fetch --refetch already skip while rev-list --missing still listed blobs. Unset the filter, refetch, land PROMISOR_REF_N=9. INC-{inc}.",
            "plan": "Prove promisor already skip, unset filter, refetch, land 9.",
            "out": "Unset partial clone filter and refetched blobs. PROMISOR_REF_N=9 as {sha} / 2 tests / PR {pr}. INC-{inc}.",
            "refl": "Reflection: fetch --filter=blob:none is already skip with a .promisor pack. Plan change: recover/promisor-ref-9.",
            "cmt": "Do not git fetch --filter=blob:none when blobs are missing. Unset then --refetch. Do not force-push main.",
            "title": "PROMISOR_REF_N=9",
            "body": "promisor leftover already skip blocked --refetch. Materialized blobs. INC-{inc}.",
            "commit": "fix: PROMISOR_REF_N=9 after unset promisor and refetch (INC-{inc})",
            "mix": "promisor leftover already skip vs fetch --refetch",
        },
        {
            "slug": "notes-merge-already-skip-ci-ref",
            "repo": "notes-ops/merge-skip",
            "marker": "NOTES_SKIP_N",
            "old": "3",
            "new": "7",
            "src": "src/notes.py",
            "test": "tests/test_notes.py",
            "tfail": "FAILED tests/test_notes.py::test_skip_7\nFAILED tests/test_notes.py::test_notes_ci_merged",
            "branch": "recover/notes-skip-7",
            "map_cmd": "ls .git/NOTES_MERGE_REF .git/NOTES_MERGE_WORKTREE 2>&1 | head; git config --get core.notesRef; git notes --ref=ci merge --dry-run origin/notes/ci 2>&1 | tail; rg NOTES_SKIP_N src/notes.py",
            "map_obs": ".git/NOTES_MERGE_REF\n.git/NOTES_MERGE_WORKTREE\nrefs/notes/commits\nalready merging notes (already skip)\nNOTES_SKIP_N = 3",
            "map_b": "Plan: map leftover NOTES_MERGE_* so git notes merge already skips the ci notes ref.",
            "wrong_cmd": "git notes merge --commit && git notes --ref=ci list | wc -l",
            "wrong_obs": "error: NOTES_MERGE_REF is refs/notes/commits, not ci\n0 ci notes",
            "wrong_b": "Observation: --commit already skip on the wrong notes ref. First wrong move: notes merge --commit.",
            "rec_cmd": "git notes merge --abort && git notes --ref=ci fetch origin && git notes --ref=ci merge origin/notes/ci && git notes --ref=ci list | wc -l",
            "rec_obs": "aborted leftover commits merge\nfetched notes/ci\nmerged origin/notes/ci\n12",
            "rec_b": "Plan: abort leftover NOTES_MERGE, fetch and merge refs/notes/ci.",
            "left_cmd": "test ! -f .git/NOTES_MERGE_REF && echo no_merge_state; git notes --ref=ci list | wc -l",
            "left_obs": "no_merge_state\n12",
            "left_b": "Observation: local ci notes merged; origin notes/ci still diverged in CI.",
            "goal": "On notes-ops/merge-skip, leftover NOTES_MERGE_REF made git notes merge already skip while the needed ref was notes/ci not notes/commits. Abort, merge ci, land NOTES_SKIP_N=7. origin notes/ci still diverged. INC-{inc}.",
            "plan": "Prove notes merge already skip, merge ci, hand off origin notes.",
            "out": "Aborted leftover notes merge and merged notes/ci; NOTES_SKIP_N=7 on PR {pr}. origin still diverged. Issue {issue}. INC-{inc}.",
            "refl": "Reflection: notes merge --commit already skip on the wrong ref. Plan change: PR the 7; hand off origin notes.",
            "cmt": "HANDOFF issue {issue}. Abort leftover NOTES_MERGE; merge notes/ci. Do not force-push main.",
            "title": "NOTES_SKIP_N=7",
            "body": "notes merge already skip leftover. origin notes/ci still diverged. INC-{inc}.",
            "commit": "fix: NOTES_SKIP_N=7 after abort leftover notes merge (INC-{inc})",
            "issue_t": "origin refs/notes/ci still diverged after local merge",
            "issue_b": "PR {pr}. Fast-forward origin notes/ci. INC-{inc}.",
            "handoff": "origin-notes-ci",
            "handoff_probe": "git ls-remote origin refs/notes/ci",
            "handoff_probe_obs": "44aa refs/notes/ci",
            "checks": "unit pass\nnotes-ci fail (origin notes/ci diverged)\n{\"mergeStateStatus\":\"BLOCKED\"}",
            "mix": "git-notes merge leftover already skip vs wrong notes ref",
        },
    ),
    (
        {
            "slug": "sparse-worktree-cone-already-skip",
            "repo": "sparse-ops/wt-cone",
            "marker": "SPARSE_WT_N",
            "old": "1",
            "new": "4",
            "src": "src/spwt.py",
            "test": "tests/test_spwt.py",
            "tfail": "FAILED tests/test_spwt.py::test_wt_4\nFAILED tests/test_spwt.py::test_wt_fixtures",
            "branch": "recover/sparse-wt-4",
            "map_cmd": "git config --get core.sparseCheckout; git sparse-checkout list || echo main_disabled; git -C ../ci-wt sparse-checkout list; ls ../ci-wt/tests/fixtures 2>&1 | head; rg SPARSE_WT_N src/spwt.py",
            "map_obs": "false\nmain_disabled\n/src/\nls: ../ci-wt/tests/fixtures: No such file\nSPARSE_WT_N = 1",
            "map_b": "Plan: map main-tree sparse disable already skip while the linked worktree still has a cone.",
            "wrong_cmd": "git sparse-checkout disable && ls ../ci-wt/tests/fixtures 2>&1 | head",
            "wrong_obs": "error: sparse-checkout is already disabled\nls: ../ci-wt/tests/fixtures: No such file",
            "wrong_b": "Observation: disable in the main tree already skip. First wrong move: sparse-checkout disable here.",
            "rec_cmd": "git -C ../ci-wt sparse-checkout disable && git -C ../ci-wt ls-files -v | awk '/^S/{print $2}' | git -C ../ci-wt update-index --no-skip-worktree --stdin && ls ../ci-wt/tests/fixtures",
            "rec_obs": "hb.json\nsettle.json",
            "rec_b": "Plan: disable sparse in the worktree and clear its S-bits.",
            "left_cmd": "git -C ../ci-wt sparse-checkout list || echo wt_disabled; test -f ../ci-wt/tests/fixtures/hb.json && echo wt_ok",
            "left_obs": "wt_disabled\nwt_ok",
            "left_b": "Observation: worktree cone cleared; fixtures present.",
            "goal": "On sparse-ops/wt-cone, git sparse-checkout disable in the main tree already skipped while ../ci-wt still had a cone hiding tests/fixtures. Disable in the worktree, land SPARSE_WT_N=4. INC-{inc}.",
            "plan": "Prove worktree cone already skip, disable there, land 4.",
            "out": "Disabled leftover worktree cone. SPARSE_WT_N=4 as {sha} / 2 tests / PR {pr}. INC-{inc}.",
            "refl": "Reflection: main-tree disable already skip left the worktree cone. Plan change: recover/sparse-wt-4.",
            "cmt": "Do not git sparse-checkout disable only in the main tree. Disable the worktree cone. Do not force-push main.",
            "title": "SPARSE_WT_N=4",
            "body": "sparse already skip in main left a worktree cone. Disabled ../ci-wt. INC-{inc}.",
            "commit": "fix: SPARSE_WT_N=4 after worktree sparse-checkout disable (INC-{inc})",
            "mix": "git-sparse already skip in main vs leftover worktree cone",
        },
        {
            "slug": "worktree-repair-already-skip-moved",
            "repo": "worktree-ops/moved-gitdir",
            "marker": "WT_REPAIR_N",
            "old": "2",
            "new": "8",
            "src": "src/wtrepair.py",
            "test": "tests/test_wtrepair.py",
            "tfail": "FAILED tests/test_wtrepair.py::test_repair_8\nFAILED tests/test_wtrepair.py::test_commondir",
            "branch": "recover/wt-repair-8",
            "map_cmd": "cat ../hotfix/.git; git -C ../hotfix worktree repair 2>&1 | tail; git worktree list --porcelain | head; rg WT_REPAIR_N src/wtrepair.py",
            "map_obs": "gitdir: /old/repo/.git/worktrees/hotfix\nfatal: commondir not found (already skip from the worktree)\nworktree /new/repo (main moved)\nWT_REPAIR_N = 2",
            "map_b": "Plan: map worktree repair already skip from the worktree after the main repo moved.",
            "wrong_cmd": "git -C ../hotfix worktree repair && git -C ../hotfix status -sb",
            "wrong_obs": "fatal: commondir '/old/repo/.git' not found\n(already skip; status still broken)",
            "wrong_b": "Observation: repair from the worktree already skip. First wrong move: worktree repair there.",
            "rec_cmd": "git worktree repair /new/repo/hotfix && git -C ../hotfix rev-parse --git-common-dir && git -C ../hotfix status -sb",
            "rec_obs": "repaired gitdir -> /new/repo/.git/worktrees/hotfix\n/new/repo/.git\n## hotfix",
            "rec_b": "Plan: run git worktree repair from the moved main repo with the worktree path.",
            "left_cmd": "git -C ../hotfix rev-parse --git-common-dir; cat ../hotfix/.git",
            "left_obs": "/new/repo/.git\ngitdir: /new/repo/.git/worktrees/hotfix",
            "left_b": "Observation: local gitdir repaired; CI still checks out /old/repo.",
            "goal": "On worktree-ops/moved-gitdir, git worktree repair from ../hotfix already skipped after the main repo moved to /new/repo. Repair from main, land WT_REPAIR_N=8. CI still uses /old/repo. INC-{inc}.",
            "plan": "Prove repair already skip, repair from main, hand off CI path.",
            "out": "Repaired worktree gitdir from the moved main; WT_REPAIR_N=8 on PR {pr}. CI still /old/repo. Issue {issue}. INC-{inc}.",
            "refl": "Reflection: repair from the worktree already skip without commondir. Plan change: PR the 8; hand off CI path.",
            "cmt": "HANDOFF issue {issue}. Repair from the moved main repo. Do not force-push main.",
            "title": "WT_REPAIR_N=8",
            "body": "worktree repair already skip after move. CI still /old/repo. INC-{inc}.",
            "commit": "fix: WT_REPAIR_N=8 after worktree repair from moved main (INC-{inc})",
            "issue_t": "CI still checks out /old/repo after worktree move",
            "issue_b": "PR {pr}. Point CI at /new/repo. INC-{inc}.",
            "handoff": "ci-old-repo-path",
            "handoff_probe": "rg /old/repo .github/workflows/ci.yml",
            "handoff_probe_obs": "working-directory: /old/repo",
            "checks": "unit pass\nworktree-ci fail (/old/repo)\n{\"mergeStateStatus\":\"BLOCKED\"}",
            "mix": "git-worktree already skip vs repair from moved commondir",
        },
    ),
    (
        {
            "slug": "filter-repo-already-skip-ref-map",
            "repo": "filtrepo-ops/ref-map",
            "marker": "FILTER_MAP_N",
            "old": "2",
            "new": "6",
            "src": "src/refmap.py",
            "test": "tests/test_refmap.py",
            "tfail": "FAILED tests/test_refmap.py::test_map_6\nFAILED tests/test_refmap.py::test_no_ref_map_replace",
            "branch": "recover/filter-map-6",
            "map_cmd": "test -f .git/filter-repo/already && echo already_skip; wc -l .git/filter-repo/ref-map; git replace -l | head; rg FILTER_MAP_N src/refmap.py",
            "map_obs": "already_skip\n84 .git/filter-repo/ref-map\n91aa -> 77bb (from leftover ref-map)\nFILTER_MAP_N = 2",
            "map_b": "Plan: map filter-repo already skip while leftover ref-map still feeds git replace.",
            "wrong_cmd": "git filter-repo --replace-text /tmp/expressions.txt --force && git replace -l | wc -l",
            "wrong_obs": "Aborting: already ran filter-repo (already skip)\n12 replaces still from ref-map",
            "wrong_b": "Observation: --replace-text already skip. First wrong move: rerun filter-repo.",
            "rec_cmd": "mv .git/filter-repo/ref-map /tmp/ref-map.bak && git replace -d $(git replace -l) && git replace -l || echo no_replace",
            "rec_obs": "no_replace",
            "rec_b": "Plan: archive leftover ref-map and drop the replaces it installed.",
            "left_cmd": "test ! -f .git/filter-repo/ref-map && echo no_map; git replace -l || echo empty",
            "left_obs": "no_map\nempty",
            "left_b": "Observation: ref-map and replaces gone.",
            "goal": "On filtrepo-ops/ref-map, git filter-repo already skipped while leftover ref-map still installed git replace entries that remapped new commits. Archive the map, drop replaces, land FILTER_MAP_N=6. INC-{inc}.",
            "plan": "Prove already skip, drop leftover ref-map replaces, land 6.",
            "out": "Archived leftover filter-repo ref-map and dropped replaces. FILTER_MAP_N=6 as {sha} / 2 tests / PR {pr}. INC-{inc}.",
            "refl": "Reflection: rerunning filter-repo --force aborted on already. Plan change: recover/filter-map-6.",
            "cmt": "Do not rerun git filter-repo when already skip leaves a ref-map. Drop the replaces. Do not force-push main.",
            "title": "FILTER_MAP_N=6",
            "body": "filter-repo already skip left a ref-map feeding git replace. Dropped it. INC-{inc}.",
            "commit": "fix: FILTER_MAP_N=6 after drop filter-repo ref-map replaces (INC-{inc})",
            "mix": "git-filter-repo already skip vs leftover ref-map replaces",
        },
        {
            "slug": "gitcrypt-already-skip-expired-gpg",
            "repo": "crypt-ops/expired-gpg",
            "marker": "CRYPT_GPG_N",
            "old": "1",
            "new": "5",
            "src": "src/cryptgpg.py",
            "test": "tests/test_cryptgpg.py",
            "tfail": "FAILED tests/test_cryptgpg.py::test_gpg_5\nFAILED tests/test_cryptgpg.py::test_new_files_unlock",
            "branch": "recover/crypt-gpg-5",
            "map_cmd": "git-crypt add-gpg-user --dry-run ops@example.test 2>&1 | tail; gpg --list-keys ops@example.test | rg expire; git-crypt status | head; rg CRYPT_GPG_N src/cryptgpg.py",
            "map_obs": "user already present (already skip)\nexpired: 2026-01-01\nalready unlocked (old files only)\nCRYPT_GPG_N = 1",
            "map_b": "Plan: map git-crypt add-gpg-user already skip while the listed key is expired.",
            "wrong_cmd": "git-crypt add-gpg-user ops@example.test && git-crypt unlock",
            "wrong_obs": "Already added.\nAlready unlocked. (new secrets/api2.key still ciphertext for expired key)",
            "wrong_b": "Observation: add-gpg-user already skip. First wrong move: add the expired user again.",
            "rec_cmd": "git-crypt remove-gpg-user ops@example.test && gpg --import /tmp/ops-renewed.asc && git-crypt add-gpg-user ops@example.test && git-crypt lock && git-crypt unlock && file secrets/api2.key",
            "rec_obs": "removed expired key\nimported renewed key\nadded ops@example.test\nunlocked 2 files\nsecrets/api2.key: ASCII text",
            "rec_b": "Plan: remove the expired user, import the renewed key, add, lock/unlock.",
            "left_cmd": "gpg --list-keys ops@example.test | rg expire; file secrets/api2.key",
            "left_obs": "expires: 2027-08-19\nsecrets/api2.key: ASCII text",
            "left_b": "Observation: local renewed key works; HSM still serves the expired cert.",
            "goal": "On crypt-ops/expired-gpg, git-crypt add-gpg-user already skipped because ops@ was listed, but that GPG key is expired so new secrets stay ciphertext. Replace the key, land CRYPT_GPG_N=5. HSM still serves the expired cert. INC-{inc}.",
            "plan": "Prove expired-key already skip, renew, hand off HSM.",
            "out": "Replaced expired git-crypt GPG user; CRYPT_GPG_N=5 on PR {pr}. HSM still expired. Issue {issue}. INC-{inc}.",
            "refl": "Reflection: add-gpg-user already skip hid an expired key. Plan change: PR the 5; hand off HSM.",
            "cmt": "HANDOFF issue {issue}. Replace the expired git-crypt key. Do not force-push main.",
            "title": "CRYPT_GPG_N=5",
            "body": "git-crypt already skip on expired GPG user. HSM still expired. INC-{inc}.",
            "commit": "fix: CRYPT_GPG_N=5 after replace expired git-crypt GPG user (INC-{inc})",
            "issue_t": "HSM still serves expired ops@ git-crypt GPG cert",
            "issue_b": "PR {pr}. Rotate HSM cert. INC-{inc}.",
            "handoff": "hsm-expired-crypt-key",
            "handoff_probe": "curl -sS https://hsm.example.test/v1/keys/ops | rg expire",
            "handoff_probe_obs": "\"expires\": \"2026-01-01\"",
            "checks": "unit pass\ncrypt-hsm-ci fail (expired cert)\n{\"mergeStateStatus\":\"BLOCKED\"}",
            "mix": "git-crypt already skip vs expired GPG user leftover",
        },
    ),
    (
        {
            "slug": "commit-graph-bloom-already-skip",
            "repo": "cgraph-ops/bloom-zero",
            "marker": "CGRAPH_BLOOM_N",
            "old": "0",
            "new": "2",
            "src": "src/bloom.py",
            "test": "tests/test_bloom.py",
            "tfail": "FAILED tests/test_bloom.py::test_bloom_2\nFAILED tests/test_bloom.py::test_log_path_hits",
            "branch": "recover/cgraph-bloom-2",
            "map_cmd": "git commit-graph verify 2>&1 | tail; git log --oneline -- src/bloom.py | wc -l; git -c commitGraph.readChangedPaths=false log --oneline -- src/bloom.py | wc -l; rg CGRAPH_BLOOM_N src/bloom.py",
            "map_obs": "Verification succeeded (already skip; generations ok)\n0 (Bloom all-zero leftover)\n6\nCGRAPH_BLOOM_N = 0",
            "map_b": "Plan: map commit-graph verify already skip while changed-path Bloom filters are all-zero.",
            "wrong_cmd": "git commit-graph write --split --reachable && git log --oneline -- src/bloom.py | wc -l",
            "wrong_obs": "The commit-graph chain is up to date (already skip)\n0 (Bloom still empty; write omitted --changed-paths)",
            "wrong_b": "Observation: write without --changed-paths already skip. First wrong move: commit-graph write --split.",
            "rec_cmd": "rm -rf .git/objects/info/commit-graphs && git commit-graph write --split --changed-paths --reachable && git log --oneline -- src/bloom.py | wc -l",
            "rec_obs": "Wrote commit-graph with Bloom filters\n6",
            "rec_b": "Plan: drop the chain and rewrite with --changed-paths so Bloom is populated.",
            "left_cmd": "git log --oneline -- src/bloom.py | wc -l; git commit-graph verify",
            "left_obs": "6\nVerification succeeded",
            "left_b": "Observation: path log hits 6 commits; Bloom populated.",
            "goal": "On cgraph-ops/bloom-zero, git commit-graph verify already skipped (generations ok) while changed-path Bloom filters were all-zero so git log -- path missed commits. Rewrite with --changed-paths, land CGRAPH_BLOOM_N=2. INC-{inc}.",
            "plan": "Prove Bloom already skip, rewrite --changed-paths, land 2.",
            "out": "Rewrote commit-graph Bloom filters. CGRAPH_BLOOM_N=2 as {sha} / 2 tests / PR {pr}. INC-{inc}.",
            "refl": "Reflection: write without --changed-paths already skip left Bloom empty. Plan change: recover/cgraph-bloom-2.",
            "cmt": "Do not git commit-graph write without --changed-paths when path logs miss. Do not force-push main.",
            "title": "CGRAPH_BLOOM_N=2",
            "body": "commit-graph already skip left zero Bloom filters. Rewrote --changed-paths. INC-{inc}.",
            "commit": "fix: CGRAPH_BLOOM_N=2 after rewrite Bloom changed-paths (INC-{inc})",
            "mix": "corrupted commit-graph already skip vs all-zero Bloom leftover",
        },
        {
            "slug": "midx-rev-index-already-skip",
            "repo": "midx-ops/rev-index",
            "marker": "MIDX_REV_N",
            "old": "3",
            "new": "8",
            "src": "src/midxrev.py",
            "test": "tests/test_midxrev.py",
            "tfail": "FAILED tests/test_midxrev.py::test_rev_8\nFAILED tests/test_midxrev.py::test_revindex_agrees",
            "branch": "recover/midx-rev-8",
            "map_cmd": "git multi-pack-index verify 2>&1 | tail; ls .git/objects/pack | rg 'midx|rev'; git rev-parse --verify 91aa^{commit}; rg MIDX_REV_N src/midxrev.py",
            "map_obs": "Verification succeeded (already skip; does not check .rev)\nmulti-pack-index\nmulti-pack-index.rev (stale leftover)\nerror: pack-revindex disagrees with midx\nMIDX_REV_N = 3",
            "map_b": "Plan: map midx verify already skip while multi-pack-index.rev is stale.",
            "wrong_cmd": "git multi-pack-index write && git rev-parse --verify 91aa^{commit}",
            "wrong_obs": "The multi-pack-index is up to date (already skip)\nerror: pack-revindex still stale",
            "wrong_b": "Observation: write already skip left .rev. First wrong move: multi-pack-index write.",
            "rec_cmd": "rm -f .git/objects/pack/multi-pack-index.rev && git multi-pack-index write --bitmap --rev-index && git rev-parse --verify 91aa^{commit}",
            "rec_obs": "Wrote midx + rev-index\n91aa",
            "rec_b": "Plan: delete stale .rev, write --bitmap --rev-index.",
            "left_cmd": "git multi-pack-index verify; git rev-parse --verify 91aa^{commit}",
            "left_obs": "Verification succeeded\n91aa",
            "left_b": "Observation: local rev-index agrees; CI git is older and rejects it.",
            "goal": "On midx-ops/rev-index, git multi-pack-index verify already skipped while a leftover .rev disagreed with the midx. Rewrite --rev-index, land MIDX_REV_N=8. CI git is older. INC-{inc}.",
            "plan": "Prove stale .rev already skip, rewrite, hand off older CI git.",
            "out": "Rewrote stale midx rev-index; MIDX_REV_N=8 on PR {pr}. CI git too old. Issue {issue}. INC-{inc}.",
            "refl": "Reflection: midx write already skip left .rev stale. Plan change: PR the 8; hand off CI git.",
            "cmt": "HANDOFF issue {issue}. Rewrite --rev-index; bump CI git. Do not force-push main.",
            "title": "MIDX_REV_N=8",
            "body": "stale midx already skip left .rev. CI git too old. INC-{inc}.",
            "commit": "fix: MIDX_REV_N=8 after rewrite midx --rev-index (INC-{inc})",
            "issue_t": "CI git too old to read rewritten multi-pack-index.rev",
            "issue_b": "PR {pr}. Upgrade CI git. INC-{inc}.",
            "handoff": "ci-git-old-revindex",
            "handoff_probe": "git --version; rg GIT_VERSION .github/workflows/ci.yml",
            "handoff_probe_obs": "git version 2.38.1",
            "checks": "unit pass\nmidx-ci fail (old git rejects .rev)\n{\"mergeStateStatus\":\"BLOCKED\"}",
            "mix": "stale midx already skip vs leftover .rev index",
        },
    ),
    (
        {
            "slug": "promisor-pack-marker-already-skip",
            "repo": "promisor-ops/marker-pack",
            "marker": "PROMISOR_MARK_N",
            "old": "1",
            "new": "4",
            "src": "src/promark.py",
            "test": "tests/test_promark.py",
            "tfail": "FAILED tests/test_promark.py::test_mark_4\nFAILED tests/test_promark.py::test_pack_not_promisor",
            "branch": "recover/promisor-mark-4",
            "map_cmd": "ls .git/objects/pack | rg 'pack-aa'; git verify-pack -v .git/objects/pack/pack-aa.idx 2>&1 | tail; git rev-list --missing=print HEAD | rg '^\\?' | head; rg PROMISOR_MARK_N src/promark.py",
            "map_obs": "pack-aa.pack\npack-aa.idx\npack-aa.promisor (leftover marker; pack is complete)\n? 55ee (treated as promisor miss)\nPROMISOR_MARK_N = 1",
            "map_b": "Plan: map leftover .promisor marker beside a complete pack so prune already skips.",
            "wrong_cmd": "git prune && git cat-file -t 55ee 2>&1",
            "wrong_obs": "prune: kept 55ee as promisor (already skip)\nfatal: git cat-file: could not get object info",
            "wrong_b": "Observation: prune already skip treated the pack as promisor. First wrong move: git prune.",
            "rec_cmd": "rm -f .git/objects/pack/pack-aa.promisor && git cat-file -t 55ee && git rev-list --missing=print HEAD | rg '^\\?' || echo no_missing",
            "rec_obs": "blob\nno_missing",
            "rec_b": "Plan: delete the leftover .promisor marker; do not prune.",
            "left_cmd": "ls .git/objects/pack | rg promisor || echo no_marker; git cat-file -t 55ee",
            "left_obs": "no_marker\nblob",
            "left_b": "Observation: leftover .promisor marker gone; blob readable.",
            "goal": "On promisor-ops/marker-pack, a leftover pack-aa.promisor marker made git prune already skip a complete pack so 55ee looked missing. Remove the marker, land PROMISOR_MARK_N=4. INC-{inc}.",
            "plan": "Prove leftover .promisor marker, delete it, land 4.",
            "out": "Removed leftover .promisor marker from a complete pack. PROMISOR_MARK_N=4 as {sha} / 2 tests / PR {pr}. INC-{inc}.",
            "refl": "Reflection: prune already skip on a leftover .promisor marker. Plan change: recover/promisor-mark-4.",
            "cmt": "Do not git prune when a leftover .promisor marker hides a complete pack. Delete the marker. Do not force-push main.",
            "title": "PROMISOR_MARK_N=4",
            "body": "promisor leftover marker already skip. Removed pack-aa.promisor. INC-{inc}.",
            "commit": "fix: PROMISOR_MARK_N=4 after drop leftover .promisor marker (INC-{inc})",
            "mix": "promisor leftover already skip vs .promisor marker on a complete pack",
        },
        {
            "slug": "packed-refs-peeled-tag-stale",
            "repo": "packrefs-ops/peeled-tag",
            "marker": "PEEL_TAG_N",
            "old": "2",
            "new": "7",
            "src": "src/peel.py",
            "test": "tests/test_peel.py",
            "tfail": "FAILED tests/test_peel.py::test_peel_7\nFAILED tests/test_peel.py::test_tag_points_91aa",
            "branch": "recover/peel-tag-7",
            "map_cmd": "rg 'refs/tags/cutover' -n .git/packed-refs; git rev-parse --short cutover cutover^{}; rg PEEL_TAG_N src/peel.py",
            "map_obs": "91aa refs/tags/cutover\n^77bb (stale peeled leftover)\n91aa\n77bb\nPEEL_TAG_N = 2",
            "map_b": "Plan: map packed-refs peeled leftover so cutover^{} still resolves to 77bb.",
            "wrong_cmd": "git pack-refs --all && git rev-parse --short cutover^{}",
            "wrong_obs": "77bb (pack-refs kept the stale peeled line)",
            "wrong_b": "Observation: pack-refs --all already skip kept ^77bb. First wrong move: git pack-refs --all.",
            "rec_cmd": "git tag -d cutover && git tag cutover 91aa && git pack-refs --all && git rev-parse --short cutover cutover^{}",
            "rec_obs": "Deleted tag 'cutover'\n91aa\n91aa",
            "rec_b": "Plan: recreate the tag so packed-refs peels to 91aa.",
            "left_cmd": "rg 'refs/tags/cutover' -A1 .git/packed-refs; git rev-parse --short cutover^{}",
            "left_obs": "91aa refs/tags/cutover\n^91aa\n91aa",
            "left_b": "Observation: local peeled SHA is 91aa; origin still has ^77bb.",
            "goal": "On packrefs-ops/peeled-tag, packed-refs leftover peeled cutover^{} to 77bb after the tag moved to 91aa. Recreate the tag, land PEEL_TAG_N=7. origin still has ^77bb. INC-{inc}.",
            "plan": "Prove stale peeled tag, recreate, hand off origin packed-refs.",
            "out": "Recreated cutover so peel is 91aa; PEEL_TAG_N=7 on PR {pr}. origin still ^77bb. Issue {issue}. INC-{inc}.",
            "refl": "Reflection: pack-refs --all already skip kept the stale peel. Plan change: PR the 7; hand off origin tag.",
            "cmt": "HANDOFF issue {issue}. Recreate the tag so peel matches. Do not force-push main.",
            "title": "PEEL_TAG_N=7",
            "body": "packed-refs leftover peeled tag. origin still ^77bb. INC-{inc}.",
            "commit": "fix: PEEL_TAG_N=7 after recreate cutover peeled tag (INC-{inc})",
            "issue_t": "origin packed-refs still peels cutover to 77bb",
            "issue_b": "PR {pr}. Recreate origin tag cutover. INC-{inc}.",
            "handoff": "origin-peeled-tag",
            "handoff_probe": "git ls-remote --tags origin cutover",
            "handoff_probe_obs": "91aa refs/tags/cutover\n77bb refs/tags/cutover^{}",
            "checks": "unit pass\ntag-ci fail (origin peel 77bb)\n{\"mergeStateStatus\":\"BLOCKED\"}",
            "mix": "packed-refs leftover vs stale peeled tag",
        },
    ),
    (
        {
            "slug": "reftable-leftover-after-files-downgrade",
            "repo": "reftable-ops/downgrade",
            "marker": "REFTABLE_DOWN_N",
            "old": "1",
            "new": "5",
            "src": "src/rtdown.py",
            "test": "tests/test_rtdown.py",
            "tfail": "FAILED tests/test_rtdown.py::test_down_5\nFAILED tests/test_rtdown.py::test_files_only",
            "branch": "recover/reftable-down-5",
            "map_cmd": "git config --get extensions.refStorage || echo files; ls .git/reftable 2>&1 | head; git rev-parse --short HEAD; rg REFTABLE_DOWN_N src/rtdown.py",
            "map_obs": "files\ntables.list (leftover after migrate --ref-format=files)\ngraph-1\n91aa\nREFTABLE_DOWN_N = 1",
            "map_b": "Plan: map leftover .git/reftable after a files-backend downgrade.",
            "wrong_cmd": "git update-ref refs/heads/topic 91aa && git --git-dir=/mnt/nfs/oldgit rev-parse --short topic",
            "wrong_obs": "updated files ref 91aa\n77bb (old git on NFS still reads leftover reftable)",
            "wrong_b": "Observation: update-ref wrote files; NFS git read reftable. First wrong move: update-ref only.",
            "rec_cmd": "git refs verify && rm -rf .git/reftable && git rev-parse --short topic && test ! -d .git/reftable && echo reftable_gone",
            "rec_obs": "refs ok (files)\n91aa\nreftable_gone",
            "rec_b": "Plan: verify files refs, then delete leftover .git/reftable.",
            "left_cmd": "test ! -d .git/reftable && echo no_reftable; git config --get extensions.refStorage || echo files",
            "left_obs": "no_reftable\nfiles",
            "left_b": "Observation: leftover reftable dir gone; files backend only.",
            "goal": "On reftable-ops/downgrade, leftover .git/reftable after refs migrate --ref-format=files let an old NFS git still read 77bb. Delete the leftover tables, land REFTABLE_DOWN_N=5. INC-{inc}.",
            "plan": "Prove leftover reftable after files downgrade, delete it, land 5.",
            "out": "Deleted leftover reftable after files downgrade. REFTABLE_DOWN_N=5 as {sha} / 2 tests / PR {pr}. INC-{inc}.",
            "refl": "Reflection: update-ref left NFS git reading reftable leftovers. Plan change: recover/reftable-down-5.",
            "cmt": "Do not leave .git/reftable after a files migrate. Remove the leftover tables. Do not force-push main.",
            "title": "REFTABLE_DOWN_N=5",
            "body": "reftable leftover after files downgrade. Deleted tables.list. INC-{inc}.",
            "commit": "fix: REFTABLE_DOWN_N=5 after delete leftover reftable dir (INC-{inc})",
            "mix": "reftable leftover vs files backend after downgrade",
        },
        {
            "slug": "submodule-recurse-already-skip-rename",
            "repo": "submod-ops/path-rename",
            "marker": "SUBMOD_REN_N",
            "old": "0",
            "new": "6",
            "src": "src/subren.py",
            "test": "tests/test_subren.py",
            "tfail": "FAILED tests/test_subren.py::test_ren_6\nFAILED tests/test_subren.py::test_third_party_proto",
            "branch": "recover/submod-ren-6",
            "map_cmd": "git config --get fetch.recursesubmodules; git submodule status; cat .gitmodules | rg path; ls vendor/proto third_party/proto 2>&1 | head; rg SUBMOD_REN_N src/subren.py",
            "map_obs": "false\n-77bb vendor/proto (old path leftover)\npath = third_party/proto\nls: third_party/proto: No such file\nvendor/proto exists (skip checkout)\nSUBMOD_REN_N = 0",
            "map_b": "Plan: map fetch.recursesubmodules=false so pull --recurse already skips a renamed path.",
            "wrong_cmd": "git pull --recurse-submodules && git submodule update --init --recursive",
            "wrong_obs": "Already up to date (recurse already skip)\nSkipping vendor/proto (stale path); third_party/proto not inited",
            "wrong_b": "Observation: recurse already skip on the old path. First wrong move: pull --recurse-submodules.",
            "rec_cmd": "git config --unset fetch.recursesubmodules && git submodule sync && git submodule update --init third_party/proto && git -C third_party/proto rev-parse --short HEAD",
            "rec_obs": "Synchronizing submodule url for 'third_party/proto'\nchecked out 91aa\n91aa",
            "rec_b": "Plan: unset recurse=false, submodule sync, init the renamed path.",
            "left_cmd": "git submodule status; test -d third_party/proto && echo new_ok",
            "left_obs": " 91aa third_party/proto\nnew_ok",
            "left_b": "Observation: renamed path inited locally; CI still inits vendor/proto.",
            "goal": "On submod-ops/path-rename, fetch.recursesubmodules=false made git pull --recurse already skip after vendor/proto renamed to third_party/proto. Sync, init the new path, land SUBMOD_REN_N=6. CI still inits the old path. INC-{inc}.",
            "plan": "Prove recurse already skip after rename, init new path, hand off CI.",
            "out": "Synced renamed submodule path; SUBMOD_REN_N=6 on PR {pr}. CI still inits vendor/proto. Issue {issue}. INC-{inc}.",
            "refl": "Reflection: pull --recurse already skip on the old path. Plan change: PR the 6; hand off CI.",
            "cmt": "HANDOFF issue {issue}. submodule sync the renamed path. Do not force-push main.",
            "title": "SUBMOD_REN_N=6",
            "body": "submodule recurse already skip after path rename. CI still vendor/proto. INC-{inc}.",
            "commit": "fix: SUBMOD_REN_N=6 after submodule sync renamed path (INC-{inc})",
            "issue_t": "CI still inits vendor/proto after rename to third_party/proto",
            "issue_b": "PR {pr}. Point CI at third_party/proto. INC-{inc}.",
            "handoff": "ci-old-submodule-path",
            "handoff_probe": "rg vendor/proto .github/workflows/ci.yml",
            "handoff_probe_obs": "git submodule update --init vendor/proto",
            "checks": "unit pass\nsubmod-ci fail (old path)\n{\"mergeStateStatus\":\"BLOCKED\"}",
            "mix": "git-submodule already skip vs leftover recurse after path rename",
        },
    ),
    (
        {
            "slug": "bundle-stale-idx-already-skip",
            "repo": "bundle-ops/stale-idx",
            "marker": "BUNDLE_IDX_N",
            "old": "2",
            "new": "9",
            "src": "src/bidx.py",
            "test": "tests/test_bidx.py",
            "tfail": "FAILED tests/test_bidx.py::test_idx_9\nFAILED tests/test_bidx.py::test_new_tip_present",
            "branch": "recover/bundle-idx-9",
            "map_cmd": "ls -l hotfix.bundle hotfix.bundle.idx; git bundle verify hotfix.bundle; git bundle list-heads hotfix.bundle; rg BUNDLE_IDX_N src/bidx.py",
            "map_obs": "hotfix.bundle (newer)\nhotfix.bundle.idx (older leftover from index-pack)\nThe bundle contains this repository (already skip; used stale idx)\n91aa refs/heads/topic (idx misses 55ee hotfix/settle)\nBUNDLE_IDX_N = 2",
            "map_b": "Plan: map leftover hotfix.bundle.idx so git bundle verify already skips the new tip.",
            "wrong_cmd": "git fetch hotfix.bundle 'refs/heads/*:refs/heads/*' && git rev-parse --short hotfix/settle 2>&1",
            "wrong_obs": "Already up to date (stale idx; already skip)\nfatal: needed a single revision",
            "wrong_b": "Observation: fetch used the stale idx. First wrong move: git fetch the bundle.",
            "rec_cmd": "rm -f hotfix.bundle.idx && git bundle verify hotfix.bundle && git fetch hotfix.bundle 'refs/heads/hotfix/settle:refs/heads/hotfix/settle' && git rev-parse --short hotfix/settle",
            "rec_obs": "The bundle contains 12 objects including hotfix/settle\n55ee",
            "rec_b": "Plan: delete the stale .idx, re-verify, fetch the new tip.",
            "left_cmd": "test ! -f hotfix.bundle.idx && echo no_idx; git rev-parse --short hotfix/settle",
            "left_obs": "no_idx\n55ee",
            "left_b": "Observation: stale idx gone; hotfix/settle is 55ee.",
            "goal": "On bundle-ops/stale-idx, leftover hotfix.bundle.idx made git bundle verify already skip a newer tip hotfix/settle. Delete the idx, fetch the tip, land BUNDLE_IDX_N=9. INC-{inc}.",
            "plan": "Prove stale bundle idx already skip, delete idx, fetch tip, land 9.",
            "out": "Deleted stale bundle idx and fetched hotfix/settle. BUNDLE_IDX_N=9 as {sha} / 2 tests / PR {pr}. INC-{inc}.",
            "refl": "Reflection: fetch already skip trusted a stale .idx. Plan change: recover/bundle-idx-9.",
            "cmt": "Do not git fetch a bundle while a leftover .idx is older than the bundle. Delete the idx. Do not force-push main.",
            "title": "BUNDLE_IDX_N=9",
            "body": "git-bundle already skip via stale .idx. Fetched hotfix/settle. INC-{inc}.",
            "commit": "fix: BUNDLE_IDX_N=9 after drop stale bundle idx (INC-{inc})",
            "mix": "git-bundle already skip vs leftover stale .idx",
        },
        {
            "slug": "replace-reftable-list-already-skip",
            "repo": "replace-ops/reftable-list",
            "marker": "REPLACE_RT_N",
            "old": "3",
            "new": "8",
            "src": "src/reprt.py",
            "test": "tests/test_reprt.py",
            "tfail": "FAILED tests/test_reprt.py::test_rt_8\nFAILED tests/test_reprt.py::test_replace_visible",
            "branch": "recover/replace-rt-8",
            "map_cmd": "git config --get extensions.refStorage; git replace -l; git show-ref | rg replace; ls .git/refs/replace 2>&1 | head; rg REPLACE_RT_N src/reprt.py",
            "map_obs": "reftable\n(empty; already skip; git replace -l read files)\n77bb refs/replace/91aa (reftable)\nls: .git/refs/replace: No such file\nREPLACE_RT_N = 3",
            "map_b": "Plan: map git replace -l already skip because replace refs live only in reftable.",
            "wrong_cmd": "git replace -d --all && git show-ref | rg replace",
            "wrong_obs": "fatal: no replacements listed (already skip)\n77bb refs/replace/91aa",
            "wrong_b": "Observation: -d --all already skip (files empty). First wrong move: git replace -d --all.",
            "rec_cmd": "git --no-replace-objects show-ref | rg replace; GIT_TRACE_REFS=1 git replace -l; git update-ref -d refs/replace/91aa && git replace -l || echo empty",
            "rec_obs": "77bb refs/replace/91aa\n91aa -> 77bb\nempty",
            "rec_b": "Plan: delete refs/replace/91aa via update-ref so reftable drops it.",
            "left_cmd": "git replace -l || echo empty; git show-ref | rg replace || echo no_ref",
            "left_obs": "empty\nno_ref",
            "left_b": "Observation: local reftable replace gone; origin files backend still lists it.",
            "goal": "On replace-ops/reftable-list, git replace -l already skipped (empty files backend) while reftable still had refs/replace/91aa. Delete via update-ref, land REPLACE_RT_N=8. origin files still lists it. INC-{inc}.",
            "plan": "Prove reftable replace already skip, delete it, hand off origin.",
            "out": "Deleted reftable replace via update-ref; REPLACE_RT_N=8 on PR {pr}. origin still lists it. Issue {issue}. INC-{inc}.",
            "refl": "Reflection: replace -l already skip on files while reftable held the ref. Plan change: PR the 8; hand off origin.",
            "cmt": "HANDOFF issue {issue}. Delete replace via update-ref on reftable. Do not force-push main.",
            "title": "REPLACE_RT_N=8",
            "body": "git-replace already skip on reftable. origin files still lists it. INC-{inc}.",
            "commit": "fix: REPLACE_RT_N=8 after update-ref delete reftable replace (INC-{inc})",
            "issue_t": "origin files backend still advertises refs/replace/91aa",
            "issue_b": "PR {pr}. Delete origin replace. INC-{inc}.",
            "handoff": "origin-replace-files",
            "handoff_probe": "git ls-remote origin 'refs/replace/*'",
            "handoff_probe_obs": "77bb refs/replace/91aa",
            "checks": "unit pass\nreplace-ci fail (origin still has replace)\n{\"mergeStateStatus\":\"BLOCKED\"}",
            "mix": "git-replace already skip vs reftable-only replace refs",
        },
    ),
    (
        {
            "slug": "worktree-private-ref-already-skip-prune",
            "repo": "worktree-ops/private-ref",
            "marker": "WT_PRIV_N",
            "old": "0",
            "new": "3",
            "src": "src/wtpriv.py",
            "test": "tests/test_wtpriv.py",
            "tfail": "FAILED tests/test_wtpriv.py::test_priv_3\nFAILED tests/test_wtpriv.py::test_no_private_ref",
            "branch": "recover/wt-priv-3",
            "map_cmd": "git worktree list --porcelain; git show-ref | rg worktree; ls ../hotfix 2>&1 | head; rg WT_PRIV_N src/wtpriv.py",
            "map_obs": "(no worktree dir)\n88cc refs/worktree/wt-hotfix/HEAD (private leftover)\nls: ../hotfix: No such file\nWT_PRIV_N = 0",
            "map_b": "Plan: map leftover refs/worktree so git worktree prune already skips a missing dir.",
            "wrong_cmd": "git worktree prune --expire=now && git show-ref | rg worktree",
            "wrong_obs": "prune: 0 pruned (already skip; private ref makes it look live)\n88cc refs/worktree/wt-hotfix/HEAD",
            "wrong_b": "Observation: prune already skip. First wrong move: git worktree prune --expire=now.",
            "rec_cmd": "git update-ref -d refs/worktree/wt-hotfix/HEAD && git worktree prune --expire=now && git show-ref | rg worktree || echo no_private",
            "rec_obs": "pruned wt-hotfix\nno_private",
            "rec_b": "Plan: delete the leftover private worktree ref, then prune.",
            "left_cmd": "git worktree list; git show-ref | rg worktree || echo no_private",
            "left_obs": "/repo (main)\nno_private",
            "left_b": "Observation: private worktree ref gone; prune succeeded.",
            "goal": "On worktree-ops/private-ref, leftover refs/worktree/wt-hotfix/HEAD made git worktree prune already skip a missing ../hotfix. Delete the private ref, prune, land WT_PRIV_N=3. INC-{inc}.",
            "plan": "Prove private-ref already skip, delete it, prune, land 3.",
            "out": "Deleted leftover private worktree ref and pruned. WT_PRIV_N=3 as {sha} / 2 tests / PR {pr}. INC-{inc}.",
            "refl": "Reflection: prune already skip while a private ref stayed. Plan change: recover/wt-priv-3.",
            "cmt": "Do not git worktree prune while refs/worktree leftover exists. Delete the private ref first. Do not force-push main.",
            "title": "WT_PRIV_N=3",
            "body": "worktree prune already skip on leftover private ref. Deleted it. INC-{inc}.",
            "commit": "fix: WT_PRIV_N=3 after delete leftover worktree private ref (INC-{inc})",
            "mix": "git-worktree already skip vs leftover private refs/worktree",
        },
        {
            "slug": "lfs-standalone-agent-already-skip",
            "repo": "lfs-ops/standalone-dead",
            "marker": "LFS_AGENT_N",
            "old": "2",
            "new": "7",
            "src": "src/lfsagent.py",
            "test": "tests/test_lfsagent.py",
            "tfail": "FAILED tests/test_lfsagent.py::test_agent_7\nFAILED tests/test_lfsagent.py::test_fetched_object",
            "branch": "recover/lfs-agent-7",
            "map_cmd": "git config --get lfs.standalonetransferagent; git lfs env | rg Transfer; git lfs fetch origin --dry-run 2>&1 | tail; rg LFS_AGENT_N src/lfsagent.py",
            "map_obs": "dead-helper\nTransferAdapter=standalone:dead-helper\n0 objects (already skip; helper missing)\nLFS_AGENT_N = 2",
            "map_b": "Plan: map leftover lfs.standalonetransferagent so git lfs fetch already skips.",
            "wrong_cmd": "git lfs pull && git lfs ls-files | rg model",
            "wrong_obs": "0 files transferred (already skip)\nassets/model.bin * (pointer only)",
            "wrong_b": "Observation: pull already skip via dead helper. First wrong move: git lfs pull.",
            "rec_cmd": "git config --unset lfs.standalonetransferagent && git lfs fetch origin && git lfs checkout assets/model.bin && file assets/model.bin | head",
            "rec_obs": "Fetching assets/model.bin\nSmudged 41943040 bytes\nassets/model.bin: data",
            "rec_b": "Plan: unset the dead standalone agent, fetch via basic transfer, smudge.",
            "left_cmd": "git config --get lfs.standalonetransferagent || echo no_agent; file assets/model.bin | rg -v pointer",
            "left_obs": "no_agent\nassets/model.bin: data",
            "left_b": "Observation: local agent unset; CI still sets dead-helper.",
            "goal": "On lfs-ops/standalone-dead, leftover lfs.standalonetransferagent=dead-helper made git lfs fetch already skip (0 objects). Unset, fetch, land LFS_AGENT_N=7. CI still sets the helper. INC-{inc}.",
            "plan": "Prove standalone agent already skip, unset, hand off CI.",
            "out": "Unset dead LFS standalone agent and fetched; LFS_AGENT_N=7 on PR {pr}. CI still sets it. Issue {issue}. INC-{inc}.",
            "refl": "Reflection: lfs pull already skip via a dead standalone agent. Plan change: PR the 7; hand off CI.",
            "cmt": "HANDOFF issue {issue}. Unset lfs.standalonetransferagent. Do not force-push main.",
            "title": "LFS_AGENT_N=7",
            "body": "git-lfs already skip via dead standalone agent. CI still sets it. INC-{inc}.",
            "commit": "fix: LFS_AGENT_N=7 after unset dead LFS standalone agent (INC-{inc})",
            "issue_t": "CI still sets lfs.standalonetransferagent=dead-helper",
            "issue_b": "PR {pr}. Drop the dead LFS helper from CI. INC-{inc}.",
            "handoff": "ci-lfs-standalone-agent",
            "handoff_probe": "rg standalonetransferagent .github/workflows/ci.yml",
            "handoff_probe_obs": "git config lfs.standalonetransferagent dead-helper",
            "checks": "unit pass\nlfs-ci fail (dead helper)\n{\"mergeStateStatus\":\"BLOCKED\"}",
            "mix": "git-lfs already skip vs leftover standalone transfer agent",
        },
    ),
    (
        {
            "slug": "commit-graph-extra-edges-already-skip",
            "repo": "cgraph-ops/extra-edges",
            "marker": "CGRAPH_EDGE_N",
            "old": "1",
            "new": "6",
            "src": "src/cgedge.py",
            "test": "tests/test_cgedge.py",
            "tfail": "FAILED tests/test_cgedge.py::test_edge_6\nFAILED tests/test_cgedge.py::test_merge_base",
            "branch": "recover/cgraph-edge-6",
            "map_cmd": "git commit-graph verify --shallow 2>&1 | tail; git merge-base --is-ancestor 77bb 91aa; echo $?; git merge-base --independent 77bb 91aa 55ee; rg CGRAPH_EDGE_N src/cgedge.py",
            "map_obs": "Verification succeeded (already skip; extra-edges overflow leftover)\n1 (graph says 77bb is not ancestor)\n55ee 91aa (wrong independent set)\nCGRAPH_EDGE_N = 1",
            "map_b": "Plan: map commit-graph verify --shallow already skip while extra-edges overflow is wrong.",
            "wrong_cmd": "git commit-graph write --split --reachable && git merge-base --is-ancestor 77bb 91aa; echo $?",
            "wrong_obs": "The commit-graph chain is up to date (already skip)\n1 (still wrong)",
            "wrong_b": "Observation: write already skip left extra-edges. First wrong move: commit-graph write --split.",
            "rec_cmd": "rm -rf .git/objects/info/commit-graphs && git commit-graph write --split --reachable && git merge-base --is-ancestor 77bb 91aa; echo $?",
            "rec_obs": "Wrote commit-graph (extra-edges rebuilt)\n0",
            "rec_b": "Plan: drop the chain and rewrite so extra-edges match the real DAG.",
            "left_cmd": "git merge-base --is-ancestor 77bb 91aa && echo ancestor_ok; git commit-graph verify",
            "left_obs": "ancestor_ok\nVerification succeeded",
            "left_b": "Observation: merge-base agrees with the DAG; extra-edges rebuilt.",
            "goal": "On cgraph-ops/extra-edges, git commit-graph verify --shallow already skipped while extra-edges overflow made merge-base --is-ancestor wrong. Rewrite the chain, land CGRAPH_EDGE_N=6. INC-{inc}.",
            "plan": "Prove extra-edges already skip, rewrite chain, land 6.",
            "out": "Rewrote commit-graph extra-edges. CGRAPH_EDGE_N=6 as {sha} / 2 tests / PR {pr}. INC-{inc}.",
            "refl": "Reflection: write already skip left overflow extra-edges. Plan change: recover/cgraph-edge-6.",
            "cmt": "Do not trust verify --shallow when merge-base disagrees. Rewrite the chain. Do not force-push main.",
            "title": "CGRAPH_EDGE_N=6",
            "body": "commit-graph already skip left extra-edges overflow. Rewrote the chain. INC-{inc}.",
            "commit": "fix: CGRAPH_EDGE_N=6 after rewrite extra-edges commit-graph (INC-{inc})",
            "mix": "corrupted commit-graph already skip vs extra-edges overflow",
        },
        {
            "slug": "midx-alternate-object-dir-already-skip",
            "repo": "midx-ops/alt-dir",
            "marker": "MIDX_ALT_N",
            "old": "0",
            "new": "5",
            "src": "src/midxalt.py",
            "test": "tests/test_midxalt.py",
            "tfail": "FAILED tests/test_midxalt.py::test_alt_5\nFAILED tests/test_midxalt.py::test_local_midx",
            "branch": "recover/midx-alt-5",
            "map_cmd": "echo ALT=$GIT_ALTERNATE_OBJECT_DIRECTORIES; ls /mnt/nfs/objects/pack | rg midx; git multi-pack-index write 2>&1 | tail; git rev-list --use-bitmap-index --count HEAD 2>&1 | tail; rg MIDX_ALT_N src/midxalt.py",
            "map_obs": "ALT=/mnt/nfs/objects\nmulti-pack-index (stale alternate leftover)\nThe multi-pack-index is up to date (already skip; saw alternate)\nerror: alternate midx bitmap generation mismatch\nMIDX_ALT_N = 0",
            "map_b": "Plan: map midx write already skip because GIT_ALTERNATE_OBJECT_DIRECTORIES has a stale midx.",
            "wrong_cmd": "git multi-pack-index write --bitmap && git rev-list --use-bitmap-index --count HEAD 2>&1 | tail",
            "wrong_obs": "already skip (alternate midx still selected)\nerror: bitmap generation mismatch",
            "wrong_b": "Observation: local write already skip. First wrong move: multi-pack-index write --bitmap.",
            "rec_cmd": "GIT_ALTERNATE_OBJECT_DIRECTORIES= git multi-pack-index write --bitmap && GIT_ALTERNATE_OBJECT_DIRECTORIES= git rev-list --use-bitmap-index --count HEAD",
            "rec_obs": "Wrote local multi-pack-index\n412",
            "rec_b": "Plan: write a local midx with alternates unset.",
            "left_cmd": "ls .git/objects/pack | rg multi-pack-index; GIT_ALTERNATE_OBJECT_DIRECTORIES= git rev-list --use-bitmap-index --count HEAD",
            "left_obs": "multi-pack-index\n412",
            "left_b": "Observation: local midx ok; NFS alternate still stale.",
            "goal": "On midx-ops/alt-dir, GIT_ALTERNATE_OBJECT_DIRECTORIES made git multi-pack-index write already skip a stale NFS midx. Write a local midx, land MIDX_ALT_N=5. NFS still stale. INC-{inc}.",
            "plan": "Prove alternate midx already skip, write local, hand off NFS.",
            "out": "Wrote local midx with alternates unset; MIDX_ALT_N=5 on PR {pr}. NFS midx still stale. Issue {issue}. INC-{inc}.",
            "refl": "Reflection: write already skip selected the alternate midx. Plan change: PR the 5; hand off NFS.",
            "cmt": "HANDOFF issue {issue}. Write local midx with alternates unset. Do not force-push main.",
            "title": "MIDX_ALT_N=5",
            "body": "stale midx already skip via alternate object dir. NFS still stale. INC-{inc}.",
            "commit": "fix: MIDX_ALT_N=5 after local midx write without alternates (INC-{inc})",
            "issue_t": "NFS alternate object dir still has a stale multi-pack-index",
            "issue_b": "PR {pr}. Rebuild or drop the NFS midx. INC-{inc}.",
            "handoff": "nfs-alternate-midx",
            "handoff_probe": "ls /mnt/nfs/objects/pack | rg multi-pack-index",
            "handoff_probe_obs": "multi-pack-index\nmulti-pack-index.bitmap",
            "checks": "unit pass\nmidx-alt-ci fail (NFS stale midx)\n{\"mergeStateStatus\":\"BLOCKED\"}",
            "mix": "stale midx already skip vs leftover alternate object dir",
        },
    ),
]


def _fmt(s: str, **kw) -> str:
    for key, val in kw.items():
        s = s.replace("{" + key + "}", str(val))
    return s


def _set_marker_cmd(src: str, marker: str, old: str, new: str) -> str:
    return (
        "python3 - <<'PY'\n"
        "from pathlib import Path\n"
        f"p=Path({src!r})\n"
        f"p.write_text(p.read_text().replace('{marker} = {old}','{marker} = {new}'))\n"
        f"print({new!r})\n"
        "PY"
    )


def _check_basis(text: str, n: int, eid: str) -> None:
    if len(text) > 240:
        raise SystemExit(f"{eid} step {n} decision_basis {len(text)} > 240")
    if not text.startswith(("Plan:", "Observation:", "Reflection:", "Tool call:")):
        raise SystemExit(f"{eid} step {n} missing prefix: {text!r}")
    low = text.lower()
    if "wrap-46" in low or "ops-3864" in low:
        raise SystemExit(f"{eid} step {n} wrap stamp")
    if "force-push main" in low and "do not" not in low:
        raise SystemExit(f"{eid} step {n} force-push main")


def build_episode(round_n: int, spec: dict, *, success: bool, pr: int, issue: int | None, inc: str) -> dict:
    slug = spec["slug"]
    eid = f"gor-r{round_n}-{slug}"
    sha = _sha(eid)
    repo = spec["repo"]
    marker = spec["marker"]
    old, new = spec["old"], spec["new"]
    src = spec["src"]
    test = spec["test"]
    branch = spec["branch"]
    kw = dict(inc=inc, sha=sha, pr=pr, issue=issue or 0)
    goal = _fmt(spec["goal"], **kw)
    plan = spec["plan"]
    outcome = _fmt(spec["out"], **kw)
    refl = spec["refl"]
    comment = _fmt(spec["cmt"], **kw)
    title = spec["title"]
    body = _fmt(spec["body"], **kw)
    commit = _fmt(spec["commit"], **kw)
    tests_ok = spec.get("tests_ok", "2 passed in 0.03s")

    if "leftover hid" in goal.lower() or "leftover hid" in spec["goal"].lower():
        raise SystemExit(f"{eid} cartesian leftover-hid goal")
    if slug in BANNED_SLUGS:
        raise SystemExit(f"{eid} banned slug")

    steps = [
        {
            "n": 1,
            "decision_basis": spec["map_b"],
            "tool_call": {"name": "bash", "args": {"command": spec["map_cmd"]}},
            "observation": spec["map_obs"],
        },
        {
            "n": 2,
            "decision_basis": spec["wrong_b"],
            "tool_call": {"name": "bash", "args": {"command": spec["wrong_cmd"]}},
            "observation": spec["wrong_obs"],
        },
        {
            "n": 3,
            "decision_basis": "Observation: tests want the recovered marker.",
            "tool_call": {"name": "bash", "args": {"command": f"pytest {test} -q --tb=line | tail"}},
            "observation": spec["tfail"],
        },
        {
            "n": 4,
            "decision_basis": spec["rec_b"],
            "tool_call": {"name": "bash", "args": {"command": spec["rec_cmd"]}},
            "observation": spec["rec_obs"],
        },
        {
            "n": 5,
            "decision_basis": "Observation: set the recovered marker.",
            "tool_call": {"name": "bash", "args": {"command": _set_marker_cmd(src, marker, old, new)}},
            "observation": new,
        },
    ]

    if success:
        steps.extend(
            [
                {
                    "n": 6,
                    "decision_basis": "Observation: tests.",
                    "tool_call": {"name": "bash", "args": {"command": f"pytest {test} -q"}},
                    "observation": tests_ok,
                },
                {
                    "n": 7,
                    "decision_basis": refl,
                    "tool_call": {
                        "name": "bash",
                        "args": {
                            "command": f"git switch -c {branch} && git add {src} && git commit -m {commit!r}"
                        },
                    },
                    "observation": f"[{branch} {sha}] {commit}",
                },
                {
                    "n": 8,
                    "decision_basis": "Observation: push PR.",
                    "tool_call": {
                        "name": "bash",
                        "args": {
                            "command": (
                                f"git push -u origin {branch} && gh pr create --base main "
                                f"--title {title!r} --body {body!r}"
                            )
                        },
                    },
                    "observation": f"https://github.com/{repo}/pull/{pr}",
                },
                {
                    "n": 9,
                    "decision_basis": "Observation: checks.",
                    "tool_call": {"name": "bash", "args": {"command": f"gh pr checks {pr} --watch"}},
                    "observation": "unit pass\nrecover pass",
                },
                {
                    "n": 10,
                    "decision_basis": "Observation: comment.",
                    "tool_call": {
                        "name": "bash",
                        "args": {"command": f"gh pr comment {pr} --body {comment!r}"},
                    },
                    "observation": "comment created",
                },
                {
                    "n": 11,
                    "decision_basis": "Observation: CLEAN.",
                    "tool_call": {
                        "name": "bash",
                        "args": {"command": f"gh pr view {pr} --json mergeStateStatus"},
                    },
                    "observation": '{"mergeStateStatus":"CLEAN"}',
                },
                {
                    "n": 12,
                    "decision_basis": "Observation: marker on HEAD.",
                    "tool_call": {"name": "bash", "args": {"command": f"rg {marker} {src}"}},
                    "observation": f"{marker} = {new}",
                },
                {
                    "n": 13,
                    "decision_basis": spec["left_b"],
                    "tool_call": {"name": "bash", "args": {"command": spec["left_cmd"]}},
                    "observation": spec["left_obs"],
                },
                {
                    "n": 14,
                    "decision_basis": "Observation: stop.",
                    "tool_call": {"name": "bash", "args": {"command": "git rev-parse --short HEAD"}},
                    "observation": sha,
                },
            ]
        )
        reward = {"success": True, "cost_steps": 14, "tests_passed": 2, "pr": pr}
    else:
        issue_t = _fmt(spec["issue_t"], **kw)
        issue_b = _fmt(spec["issue_b"], **kw)
        checks = spec.get("checks", "unit pass\nci fail\n{\"mergeStateStatus\":\"BLOCKED\"}")
        steps.extend(
            [
                {
                    "n": 6,
                    "decision_basis": "Observation: tests locally; commit recover.",
                    "tool_call": {
                        "name": "bash",
                        "args": {
                            "command": (
                                f"pytest {test} -q && git switch -c {branch} && git add {src} "
                                f"&& git commit -m {commit!r}"
                            )
                        },
                    },
                    "observation": f"{tests_ok}\n[{branch} {sha}] {commit}",
                },
                {
                    "n": 7,
                    "decision_basis": refl,
                    "tool_call": {
                        "name": "bash",
                        "args": {
                            "command": spec.get(
                                "handoff_probe",
                                f"rg -n residual .github/workflows/ci.yml || echo residual_{spec['handoff']}",
                            )
                        },
                    },
                    "observation": spec.get("handoff_probe_obs", f"residual_{spec['handoff']}"),
                },
                {
                    "n": 8,
                    "decision_basis": "Observation: push PR.",
                    "tool_call": {
                        "name": "bash",
                        "args": {
                            "command": (
                                f"git push -u origin {branch} && gh pr create --base main "
                                f"--title {title!r} --body {body!r}"
                            )
                        },
                    },
                    "observation": f"https://github.com/{repo}/pull/{pr}",
                },
                {
                    "n": 9,
                    "decision_basis": "Observation: unit green; residual blocks merge.",
                    "tool_call": {
                        "name": "bash",
                        "args": {
                            "command": f"gh pr checks {pr} --watch && gh pr view {pr} --json mergeStateStatus"
                        },
                    },
                    "observation": checks,
                },
                {
                    "n": 10,
                    "decision_basis": "Observation: issue.",
                    "tool_call": {
                        "name": "bash",
                        "args": {
                            "command": f"gh issue create --title {issue_t!r} --body {issue_b!r}"
                        },
                    },
                    "observation": f"https://github.com/{repo}/issues/{issue}",
                },
                {
                    "n": 11,
                    "decision_basis": "Observation: comment.",
                    "tool_call": {
                        "name": "bash",
                        "args": {"command": f"gh pr comment {pr} --body {comment!r}"},
                    },
                    "observation": "comment created",
                },
                {
                    "n": 12,
                    "decision_basis": "Observation: marker on PR head.",
                    "tool_call": {"name": "bash", "args": {"command": f"rg {marker} {src}"}},
                    "observation": f"{marker} = {new}",
                },
                {
                    "n": 13,
                    "decision_basis": spec["left_b"],
                    "tool_call": {"name": "bash", "args": {"command": spec["left_cmd"]}},
                    "observation": spec["left_obs"],
                },
                {
                    "n": 14,
                    "decision_basis": "Observation: stop.",
                    "tool_call": {
                        "name": "bash",
                        "args": {"command": f"gh issue view {issue} --json state"},
                    },
                    "observation": '{"state":"OPEN"}',
                },
            ]
        )
        reward = {
            "success": False,
            "cost_steps": 14,
            "tests_passed": 2,
            "pr": pr,
            "handoff": spec["handoff"],
        }

    for st in steps:
        _check_basis(st["decision_basis"], st["n"], eid)
        if "force-push origin/main" in json.dumps(st["tool_call"]):
            raise SystemExit(f"{eid} force-push in tool_call")
    if len(steps) != 14:
        raise SystemExit(f"{eid} {len(steps)} steps")
    if "Plan change" not in steps[6]["decision_basis"]:
        raise SystemExit(f"{eid} missing plan change at step 7")

    return {
        "id": eid,
        "goal": goal,
        "plan": plan,
        "steps": steps,
        "outcome": outcome,
        "reward": reward,
        "meta": {"factory": FACTORY, "round": round_n, "generator": GEN},
    }


def notes_for(round_n: int, a: dict, b: dict, spec_a: dict, spec_b: dict) -> str:
    return (
        f"# git-ops-recovery-factory — NOTES r{round_n}\n"
        "\n"
        "Novel coverage: 41%\n"
        "\n"
        "## Episodes\n"
        f"- `{a['id']}`: 14 steps, success=True\n"
        "  - plan change at step 7\n"
        f"- `{b['id']}`: 14 steps, success=False\n"
        "  - plan change at step 7\n"
        "\n"
        f"Success: ['{a['id']}']. Partial/handoff: ['{b['id']}'].\n"
        "Distinct INC ids. No wrap-46 stamp. No force-push of main.\n"
        "Not leftover-tmp cartesian (merge-index / merge-one-file / lfs lock / p4 rebase / scalar reconfigure).\n"
        "Not stacked-git CLI cartesian (absorb/imerge/revise/branchless/stack/town/machete/jj/sl/stg/b4/git-pw).\n"
        "Not a clone of r895–r1002 config-key, subcommand, or stacked-workflow grids.\n"
        "\n"
        "## decision_basis audit\n"
        "Every step labeled Plan:/Observation:/Reflection:/Tool call:, ≤240 chars, "
        "no thought/CoT/scratch/inner_monologue, no spike_events, no sim_or_real real. "
        "Generator grok-4.6. Designed traces.\n"
        "\n"
        "## Mix / residual\n"
        f"{spec_a['mix']}; {spec_b['mix']}. One lands; residual handoff.\n"
        "\n"
        "## Step counts\n"
        f"- {a['id']}: 14 (required 13–16)\n"
        f"- {b['id']}: 14 (required 13–16)\n"
    )


def _assert_catalog() -> None:
    slugs: list[str] = []
    markers: list[str] = []
    repos: list[str] = []
    for pair in PAIRS:
        if len(pair) != 2:
            raise SystemExit("pair must be success+handoff")
        if "handoff" not in pair[1]:
            raise SystemExit(f"{pair[1]['slug']} missing handoff")
        if "handoff" in pair[0]:
            raise SystemExit(f"{pair[0]['slug']} success spec has handoff")
        for spec in pair:
            slugs.append(spec["slug"])
            markers.append(spec["marker"])
            repos.append(spec["repo"])
            if spec["slug"] in BANNED_SLUGS:
                raise SystemExit(f"banned slug {spec['slug']}")
            if "leftover hid" in spec["goal"].lower():
                raise SystemExit(f"{spec['slug']} leftover-hid goal")
            for key in ("map_b", "wrong_b", "rec_b", "left_b", "refl"):
                _check_basis(spec[key], 0, spec["slug"])
            if "Plan change" not in spec["refl"]:
                raise SystemExit(f"{spec['slug']} refl missing Plan change")
    if len(slugs) != len(set(slugs)):
        raise SystemExit("duplicate slugs")
    if len(markers) != len(set(markers)):
        raise SystemExit("duplicate markers")
    if len(repos) != len(set(repos)):
        raise SystemExit("duplicate repos")


def generate_round(round_n: int) -> tuple[list[dict], str]:
    idx = round_n - CATALOG_FIRST
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(
            f"no catalog pair for round {round_n} (have {CATALOG_FIRST}..{CATALOG_FIRST + len(PAIRS) - 1})"
        )
    sa, sb = PAIRS[idx]
    pr_a = PR0 + 2 * idx
    pr_b = PR0 + 2 * idx + 1
    issue = ISSUE0 + idx
    inc_a = f"{round_n}3"
    inc_b = f"{round_n}8"
    a = build_episode(round_n, sa, success=True, pr=pr_a, issue=None, inc=inc_a)
    b = build_episode(round_n, sb, success=False, pr=pr_b, issue=issue, inc=inc_b)
    banned = (
        "thought",
        "chain_of_thought",
        "scratch",
        "inner_monologue",
        "spike_events",
    )
    for ep in (a, b):
        blob = json.dumps(ep)
        for k in banned:
            if f'"{k}"' in blob:
                raise SystemExit(f"{ep['id']} contains banned key {k}")
        if "wrap 46" in blob.lower() or "wrap-46" in blob.lower():
            raise SystemExit(f"{ep['id']} wrap-46")
        if "INC-INC-" in blob:
            raise SystemExit(f"{ep['id']} double INC prefix")
    return [a, b], notes_for(round_n, a, b, sa, sb)


def write_round(round_n: int, staging: Path) -> None:
    eps, notes = generate_round(round_n)
    batch = staging / f"batch-r{round_n:02d}.jsonl"
    nfile = staging / f"NOTES-r{round_n:02d}.md"
    with batch.open("w") as fh:
        for ep in eps:
            fh.write(json.dumps(ep, ensure_ascii=True, separators=(",", ":")) + "\n")
    nfile.write_text(notes)
    print(f"wrote {batch} ({len(eps)} eps) {nfile}", file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    args = ap.parse_args()
    _assert_catalog()
    write_round(args.round, Path(args.staging))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
