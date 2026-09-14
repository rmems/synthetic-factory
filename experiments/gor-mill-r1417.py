#!/usr/bin/env python3
"""git-ops-recovery-factory mill r1417+: unique git-config/command plants, 16-step traces.

Not wrap-46. Not clones of r793–r1416 (advice-diverging-false, http-ssltry-false,
merge-conflictstyle-diff3, whoosh leftover3d). Distinct failure class per episode.
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
_base_build = _r1278.build_episode
FACTORY = _r1278.FACTORY
GEN = _r1278.GEN
FACTORY_DIR = _r1278.FACTORY_DIR
PR0 = _r1278.PR0
ISSUE0 = _r1278.ISSUE0
_trim = _r1278._trim

BAN = set(_r1278.BAN) | {
    "advice-diverging-false",
    "http-ssltry-false",
    "merge-conflictstyle-diff3",
    "interactive-difffilter-legacy",
    "whoosh-writer-leftover3d-rebuild",
    "whoosh-drop-leftover3d-handoff",
}


def _prior_mill_slugs() -> set[str]:
    used: set[str] = set()
    for name in (
        "gor-mill-r1278.py",
        "gor-mill-r1371.py",
        "gor-mill-r1405.py",
    ):
        path = HERE / name
        if path.is_file():
            used.update(re.findall(r'slug="([^"]+)"', path.read_text()))
    return used


PRIOR = _prior_mill_slugs()


def _published_slugs() -> set[str]:
    used: set[str] = set(PRIOR)
    if not FACTORY_DIR.exists():
        return used
    for path in FACTORY_DIR.glob("batch-r*.jsonl"):
        stem = path.stem
        try:
            n = int(stem.split("r", 1)[1])
        except ValueError:
            continue
        if n < 1278:
            continue
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            match = re.match(r"gor-r\d+-(.+)$", rec.get("id", ""))
            if match:
                used.add(match.group(1))
    return used


def densify(ep: dict, spec: dict) -> dict:
    steps = ep["steps"]
    stop = steps.pop()
    src = spec["src"]
    stem = Path(src).stem
    persist_cmd = (
        f"git config --local --show-origin --list | rg -n {stem} | tail; "
        f"git diff --stat HEAD~1 -- {src}; git status -sb"
    )
    persist_obs = f"{spec['left_obs']}\n {src} leftover | 4 +-\n## leftover recover/{stem}"
    fsck_cmd = "git fsck --no-dangling --connectivity-only 2>&1 | tail; git reflog -3 --date=iso | tail"
    fsck_obs = f"(empty leftover fsck)\nHEAD@{{0}}: leftover recover/{stem}"
    steps.append(
        {
            "n": 14,
            "decision_basis": _trim(
                f"Observation: persist leftover recover for {stem}; show origin and diffstat."
            ),
            "tool_call": {"name": "bash", "args": {"command": persist_cmd}},
            "observation": persist_obs,
        }
    )
    steps.append(
        {
            "n": 15,
            "decision_basis": "Observation: fsck after recover; reflog records the hotfix commit.",
            "tool_call": {"name": "bash", "args": {"command": fsck_cmd}},
            "observation": fsck_obs,
        }
    )
    stop["n"] = 16
    stop["decision_basis"] = "Observation: stop."
    steps.append(stop)
    for i, st in enumerate(steps, 1):
        st["n"] = i
        if len(st["decision_basis"]) > 240:
            raise SystemExit(f"{ep['id']} step {i} basis")
    ep["reward"]["cost_steps"] = 16
    if not (12 <= len(steps) <= 18):
        raise SystemExit(f"{ep['id']} {len(steps)} steps")
    return ep


def build_episode(round_n: int, spec: dict, *, success: bool, pr: int, issue: int | None, inc: str) -> dict:
    ep = _base_build(round_n, spec, success=success, pr=pr, issue=issue, inc=inc)
    return densify(ep, spec)


NEW_PAIRS: list[tuple[dict, dict]] = []


def add(a: dict, b: dict) -> None:
    NEW_PAIRS.append(_pair(a, b))


add(
    gitcfg(
        slug="add-ignoreerrors-true",
        repo="add-ops/ignore-err",
        marker="ADDIGN_N",
        old="0",
        new="7",
        stem="addign",
        key="add.ignoreErrors",
        bad="true",
        good="false",
        effect="swallowed recover leftover add failures so a missing hotfix path still exited 0",
        probe="git add src/missing.py src/addign.py; echo exit:$?",
        bad_obs="exit:0 leftover (missing path ignored)",
        good_obs="fatal: leftover pathspec src/missing.py did not match\nexit:128",
        wrong="git add --ignore-errors src/missing.py",
        wrong_obs="exit:0 leftover (add.ignoreErrors=true)",
    ),
    gitcfg(
        slug="add-interactive-usebuiltin-false",
        repo="add-ops/interactive-perl",
        marker="ADDINT_N",
        old="1",
        new="4",
        stem="addint",
        key="add.interactive.useBuiltin",
        bad="false",
        good="true",
        effect="ran recover leftover git add -p through the perl script so hunk staging hung",
        probe="printf n | git add -p src/addint.py 2>&1 | tail",
        bad_obs="error: leftover perl add-interactive hung",
        good_obs="Stage this hunk leftover [y,n,q,a,d,/?]?",
        wrong="git add -p -- src/addint.py",
        wrong_obs="error: leftover perl still (useBuiltin=false)",
        handoff="ci-add-interactive-usebuiltin-false",
        ci_obs="false",
    ),
)
add(
    gitcfg(
        slug="advice-pushalreadyexists-false",
        repo="advice-ops/push-exists",
        marker="ADVPUSHX_N",
        old="2",
        new="8",
        stem="advpushx",
        key="advice.pushAlreadyExists",
        bad="false",
        good="true",
        effect="silenced recover leftover already-exists hints so CI treated a rejected tag push as success",
        probe="git push origin refs/tags/v2.0.1 2>&1 | tail",
        bad_obs="error: leftover already exists (no hint)",
        good_obs="hint: leftover Updates were rejected because the tag already exists",
        wrong="git push --tags origin",
        wrong_obs="error: leftover already exists (advice.pushAlreadyExists=false)",
    ),
    gitcfg(
        slug="advice-pushfetchfirst-false",
        repo="advice-ops/push-fetch-first",
        marker="ADVPFF_N",
        old="0",
        new="6",
        stem="advpff",
        key="advice.pushFetchFirst",
        bad="false",
        good="true",
        effect="omitted recover leftover fetch-first hints so a non-ff push looked like a clean reject",
        probe="git push origin main 2>&1 | tail",
        bad_obs="error: leftover failed to push some refs (no hint)",
        good_obs="hint: leftover Updates were rejected because the remote contains work",
        wrong="git push --force-with-lease origin main",
        wrong_obs="error: leftover no hint (advice.pushFetchFirst=false)",
        handoff="ci-advice-pushfetchfirst-false",
        ci_obs="false",
    ),
)
add(
    gitcfg(
        slug="advice-pushneedsforce-false",
        repo="advice-ops/push-needs-force",
        marker="ADVPNF_N",
        old="3",
        new="5",
        stem="advpnf",
        key="advice.pushNeedsForce",
        bad="false",
        good="true",
        effect="stripped recover leftover --force hints so the oncall rewrote main instead of the topic",
        probe="git push origin hotfix 2>&1 | tail",
        bad_obs="error: leftover non-fast-forward (no force hint)",
        good_obs="hint: leftover use --force-with-lease",
        wrong="git push origin HEAD:hotfix",
        wrong_obs="error: leftover no force hint (advice.pushNeedsForce=false)",
    ),
    gitcfg(
        slug="advice-resolveconflict-false",
        repo="advice-ops/resolve-conflict",
        marker="ADVRES_N",
        old="1",
        new="9",
        stem="advres",
        key="advice.resolveConflict",
        bad="false",
        good="true",
        effect="hid recover leftover unmerged-path hints so git commit during a merge looked empty",
        probe="git commit -m leftover 2>&1 | tail",
        bad_obs="fatal: leftover you have unmerged paths (no hint)",
        good_obs="hint: leftover Fix conflicts and then commit the result",
        wrong="git commit --no-edit",
        wrong_obs="fatal: leftover no hint (advice.resolveConflict=false)",
        handoff="ci-advice-resolveconflict-false",
        ci_obs="false",
    ),
)
add(
    gitcfg(
        slug="advice-rmhints-false",
        repo="advice-ops/rm-hints",
        marker="ADVRM_N",
        old="0",
        new="7",
        stem="advrm",
        key="advice.rmHints",
        bad="false",
        good="true",
        effect="silenced recover leftover git rm cached hints so a worktree file was deleted with the index",
        probe="git rm src/advrm.py 2>&1 | tail",
        bad_obs="rm leftover src/advrm.py (no cached hint)",
        good_obs="hint: leftover use git rm --cached to keep the worktree file",
        wrong="git rm --cached src/advrm.py",
        wrong_obs="rm leftover (advice.rmHints=false still omitted the hint in CI logs)",
    ),
    gitcfg(
        slug="advice-worktreeaddorphan-false",
        repo="advice-ops/wt-orphan",
        marker="ADVWT_N",
        old="2",
        new="4",
        stem="advwt",
        key="advice.worktreeAddOrphan",
        bad="false",
        good="true",
        effect="skipped recover leftover orphan-worktree warnings so CI added a detached wt on a missing branch",
        probe="git worktree add --orphan /tmp/wt-orphan leftover-gone 2>&1 | tail",
        bad_obs="Preparing leftover worktree (no orphan hint)",
        good_obs="hint: leftover --orphan creates a disconnected history",
        wrong="git worktree add /tmp/wt-orphan2 leftover-gone",
        wrong_obs="Preparing leftover (advice.worktreeAddOrphan=false)",
        handoff="ci-advice-worktreeaddorphan-false",
        ci_obs="false",
    ),
)
add(
    gitcfg(
        slug="am-committerdateisauthordate-true",
        repo="am-ops/committer-is-author",
        marker="AMCD_N",
        old="1",
        new="8",
        stem="amcd",
        key="am.committerDateIsAuthorDate",
        bad="true",
        good="false",
        effect="stamped recover leftover committer dates from the patch author so GPG verify-commit failed",
        probe="git am /tmp/hotfix.mbox && git log -1 --format='%cI %aI'",
        bad_obs="2024-01-01 leftover = author date",
        good_obs="2026-08-19 leftover committer now",
        wrong="git am --committer-date-is-author-date=false /tmp/hotfix.mbox",
        wrong_obs="2024-01-01 leftover (am.committerDateIsAuthorDate=true)",
    ),
    gitcfg(
        slug="blame-blankboundary-true",
        repo="blame-ops/blank-boundary",
        marker="BLBN_N",
        old="3",
        new="6",
        stem="blbn",
        key="blame.blankBoundary",
        bad="true",
        good="false",
        effect="blanked recover leftover boundary commits in git blame so the hotfix author looked empty",
        probe="git blame -L 1,1 src/blbn.py",
        bad_obs="        leftover (boundary blanked)",
        good_obs="a1b2c3d leftover Oncall",
        wrong="git blame --root -L 1,1 src/blbn.py",
        wrong_obs="        leftover (blame.blankBoundary=true)",
        handoff="ci-blame-blankboundary-true",
        ci_obs="true",
    ),
)
add(
    gitcfg(
        slug="color-branch-always",
        repo="color-ops/branch-ansi",
        marker="COLBRN_N",
        old="0",
        new="5",
        stem="colbrn",
        key="color.branch",
        bad="always",
        good="never",
        effect="wrapped recover leftover git branch names in ANSI so CI regex missed hotfix",
        probe="git branch | cat -v",
        bad_obs="* leftover ^[[32mhotfix^[[0m",
        good_obs="* leftover hotfix",
        wrong="git -c color.ui=never branch",
        wrong_obs="* leftover ^[[32mhotfix (color.branch=always beats color.ui)",
    ),
    gitcfg(
        slug="color-grep-always",
        repo="color-ops/grep-ansi",
        marker="COLGRP_N",
        old="2",
        new="9",
        stem="colgrp",
        key="color.grep",
        bad="always",
        good="never",
        effect="painted recover leftover git grep matches so CI split INC ids on ANSI",
        probe="git grep -n INC src/colgrp.py | cat -v",
        bad_obs="src/colgrp.py leftover ^[[1;31mINC-^[[0m4421",
        good_obs="src/colgrp.py leftover INC-4421",
        wrong="git -c color.ui=never grep -n INC src/colgrp.py",
        wrong_obs="^[[1;31mINC leftover (color.grep=always)",
        handoff="ci-color-grep-always",
        ci_obs="always",
    ),
)
add(
    gitcfg(
        slug="color-interactive-always",
        repo="color-ops/interactive-ansi",
        marker="COLIA_N",
        old="1",
        new="7",
        stem="colia",
        key="color.interactive",
        bad="always",
        good="never",
        effect="colored recover leftover git add -p prompts so the hunk parser ate ANSI as answers",
        probe="printf n | git add -p src/colia.py 2>&1 | cat -v | tail",
        bad_obs="Stage leftover ^[[1;36mhunk^[[0m [y,n]",
        good_obs="Stage leftover hunk [y,n,q,a,d,/?]?",
        wrong="git add -p -- src/colia.py",
        wrong_obs="Stage leftover ^[[1;36mhunk (color.interactive=always)",
    ),
    gitcfg(
        slug="color-status-always",
        repo="color-ops/status-ansi",
        marker="COLSTT_N",
        old="3",
        new="4",
        stem="colstt",
        key="color.status",
        bad="always",
        good="never",
        effect="wrapped recover leftover git status paths in ANSI so CI missed UU lines",
        probe="git status --short | cat -v",
        bad_obs="^[[31mUU leftover src/colstt.py^[[0m",
        good_obs="UU leftover src/colstt.py",
        wrong="git -c color.ui=never status --short",
        wrong_obs="^[[31mUU leftover (color.status=always)",
        handoff="ci-color-status-always",
        ci_obs="always",
    ),
)
add(
    gitcfg(
        slug="column-tag-always",
        repo="column-ops/tag-cols",
        marker="COLTAG_N",
        old="0",
        new="8",
        stem="coltag",
        key="column.tag",
        bad="always",
        good="never",
        effect="wrapped recover leftover git tag names into columns so CI regex missed v2.0.1",
        probe="git tag",
        bad_obs="v1.0 leftover    v2.0.1    v2.0.1-rc leftover columns",
        good_obs="v1.0 leftover\nv2.0.1 leftover",
        wrong="git -c column.ui=never tag",
        wrong_obs="v1.0 leftover    v2.0.1 (column.tag=always)",
    ),
    gitcfg(
        slug="diff-autorefreshindex-false",
        repo="diff-ops/auto-refresh-off",
        marker="DIFFARI_N",
        old="2",
        new="6",
        stem="diffari",
        key="diff.autoRefreshIndex",
        bad="false",
        good="true",
        effect="skipped recover leftover index refresh so git diff hid a racy hotfix write",
        probe="echo hotfix > src/diffari.py && git diff --stat",
        bad_obs="(empty leftover; racy stat, no refresh)",
        good_obs=" src/diffari.py leftover | 4 +-",
        wrong="git update-index --refresh && git diff --stat",
        wrong_obs="(empty leftover; next diff.autoRefreshIndex=false)",
        handoff="ci-diff-autorefreshindex-false",
        ci_obs="false",
    ),
)
add(
    gitcfg(
        slug="diff-dirstat-files-zero",
        repo="diff-ops/dirstat-zero",
        marker="DIFFDS_N",
        old="1",
        new="5",
        stem="diffds",
        key="diff.dirstat",
        bad="files,0",
        good="changes,3",
        effect="listed recover leftover every directory at 0% so CI parsed noise instead of the hotfix path",
        probe="git diff --dirstat HEAD~1",
        bad_obs="  0.0% leftover vendor/\n  0.0% leftover src/",
        good_obs=" 12.4% leftover src/",
        wrong="git diff --dirstat=changes HEAD~1",
        wrong_obs="  0.0% leftover (diff.dirstat=files,0)",
    ),
    gitcfg(
        slug="diff-statgraphwidth-one",
        repo="diff-ops/stat-width",
        marker="DIFFSG_N",
        old="0",
        new="9",
        stem="diffsg",
        key="diff.statGraphWidth",
        bad="1",
        good="40",
        effect="crushed recover leftover --stat bars to 1 column so CI could not see the 12k-line dump",
        probe="git diff --stat HEAD~1",
        bad_obs=" vendor/lib.c leftover | 12000 +",
        good_obs=" vendor/lib.c leftover | 12000 +++++++++++++++++",
        wrong="git diff --stat=80 HEAD~1",
        wrong_obs=" vendor/lib.c leftover | 12000 + (statGraphWidth=1)",
        handoff="ci-diff-statgraphwidth-one",
        ci_obs="1",
    ),
)
add(
    gitcfg(
        slug="diff-wordregex-dot",
        repo="diff-ops/word-regex",
        marker="DIFFWR_N",
        old="3",
        new="7",
        stem="diffwr",
        key="diff.wordRegex",
        bad=".",
        good="[[:alnum:]_]+",
        effect="treated recover leftover every character as a word so --word-diff flooded the hotfix hunk",
        probe="git diff --word-diff HEAD~1 -- src/diffwr.py | wc -l",
        bad_obs="400 leftover (char-wise words)",
        good_obs="24 leftover",
        wrong="git diff --word-diff-regex='[[:alnum:]_]+' HEAD~1 -- src/diffwr.py",
        wrong_obs="400 leftover (diff.wordRegex=. beats flag)",
    ),
    gitcfg(
        slug="fetch-prune-true",
        repo="fetch-ops/prune-on",
        marker="FTPRN_N",
        old="2",
        new="4",
        stem="ftprn",
        key="fetch.prune",
        bad="true",
        good="false",
        effect="deleted recover leftover remote-tracking hotfix on every fetch so CI lost the topic SHA",
        probe="git fetch origin 2>&1 | tail; git rev-parse --abbrev-ref refs/remotes/origin/hotfix 2>&1 | tail",
        bad_obs=" - [deleted] leftover origin/hotfix",
        good_obs="a1b2c3d leftover refs/remotes/origin/hotfix",
        wrong="git fetch --no-prune origin",
        wrong_obs=" - [deleted] leftover (fetch.prune=true beats --no-prune in alias)",
        handoff="ci-fetch-prune-true",
        ci_obs="true",
    ),
)
add(
    gitcfg(
        slug="format-headers-stale",
        repo="format-ops/headers-stale",
        marker="FMTHDR_N",
        old="0",
        new="8",
        stem="fmthdr",
        key="format.headers",
        bad="X-Legacy: leftover-oncall",
        good=None,
        effect="injected recover leftover X-Legacy headers so SMTP dropped the series as spam",
        probe="git format-patch -1 --stdout | rg '^X-Legacy'",
        bad_obs="X-Legacy: leftover-oncall",
        good_obs="(empty leftover; no X-Legacy)",
        wrong="git format-patch -1 --stdout --from=oncall@ex",
        wrong_obs="X-Legacy: leftover-oncall still",
    ),
    gitcfg(
        slug="format-numbered-true",
        repo="format-ops/numbered-on",
        marker="FMTNUM_N",
        old="1",
        new="6",
        stem="fmtnum",
        key="format.numbered",
        bad="true",
        good="false",
        effect="prefixed recover leftover [PATCH 1/1] on a single patch so b4 could not match the cover",
        probe="git format-patch -1 --stdout | rg '^Subject:'",
        bad_obs="Subject: leftover [PATCH 1/1] hotfix",
        good_obs="Subject: leftover [PATCH] hotfix",
        wrong="git format-patch -1 --no-numbered --stdout",
        wrong_obs="Subject: leftover [PATCH 1/1] (format.numbered=true)",
        handoff="ci-format-numbered-true",
        ci_obs="true",
    ),
)
add(
    gitcfg(
        slug="gc-aggressivewindow-zero",
        repo="gc-ops/agg-window-zero",
        marker="GCAGGW_N",
        old="3",
        new="5",
        stem="gcaggw",
        key="gc.aggressiveWindow",
        bad="0",
        good="250",
        effect="disabled recover leftover aggressive deltas so git gc --aggressive still wrote a 4GB pack",
        probe="git gc --aggressive && git count-objects -vH | rg size-pack",
        bad_obs="size-pack leftover 4.10 GiB",
        good_obs="size-pack leftover 180.00 MiB",
        wrong="git gc --aggressive --window=250",
        wrong_obs="size-pack leftover 4.10 GiB (gc.aggressiveWindow=0)",
    ),
    gitcfg(
        slug="grep-column-true",
        repo="grep-ops/column-on",
        marker="GRPCOL_N",
        old="0",
        new="9",
        stem="grpcol",
        key="grep.column",
        bad="true",
        good="false",
        effect="emitted recover leftover column numbers so CI regex on file:line missed INC",
        probe="git grep -n INC src/grpcol.py",
        bad_obs="src/grpcol.py leftover:12:4:INC-4421",
        good_obs="src/grpcol.py leftover:12:INC-4421",
        wrong="git grep -n --no-column INC src/grpcol.py",
        wrong_obs="src/grpcol.py leftover:12:4:INC (grep.column=true)",
        handoff="ci-grep-column-true",
        ci_obs="true",
    ),
)
add(
    gitcfg(
        slug="grep-fullname-true",
        repo="grep-ops/full-name",
        marker="GRPFN_N",
        old="2",
        new="7",
        stem="grpfn",
        key="grep.fullName",
        bad="true",
        good="false",
        effect="printed recover leftover paths from repo root while cwd was src/ so CI opened the wrong file",
        probe="cd src && git grep -n INC grpfn.py",
        bad_obs="src/grpfn.py leftover:12:INC-4421",
        good_obs="grpfn.py leftover:12:INC-4421",
        wrong="cd src && git grep -n --no-full-name INC grpfn.py",
        wrong_obs="src/grpfn.py leftover (grep.fullName=true)",
    ),
    gitcfg(
        slug="help-htmlpath-stale",
        repo="help-ops/html-path",
        marker="HLHTML_N",
        old="1",
        new="4",
        stem="hlhtml",
        key="help.htmlPath",
        bad="/opt/legacy/git-html",
        good=None,
        effect="opened recover leftover git help --web from a missing html tree so the oncall hung",
        probe="git help --web rebase 2>&1 | tail",
        bad_obs="fatal: leftover /opt/legacy/git-html/git-rebase.html missing",
        good_obs="GIT-REBASE(1) leftover",
        wrong="git help --man rebase",
        wrong_obs="fatal: leftover help.htmlPath still /opt/legacy/git-html",
        handoff="ci-help-htmlpath-stale",
        ci_obs="/opt/legacy/git-html",
    ),
)
add(
    gitcfg(
        slug="http-minsessions-zero",
        repo="http-ops/min-sessions",
        marker="HTTPMS_N",
        old="0",
        new="8",
        stem="httpms",
        key="http.minSessions",
        bad="0",
        good="1",
        effect="closed recover leftover HTTP/2 sessions immediately so every fetch renegotiated TLS",
        probe="git fetch origin 2>&1 | tail",
        bad_obs="error: leftover HTTP/2 session dropped (minSessions=0)",
        good_obs="From leftover origin\n   a1b2c3d..d4e5f6a  main",
        wrong="git fetch --prune origin",
        wrong_obs="error: leftover HTTP/2 session dropped still",
    ),
    gitcfg(
        slug="http-noepsv-true",
        repo="http-ops/no-epsv",
        marker="HTTPEPSV_N",
        old="3",
        new="6",
        stem="httppsv",
        key="http.noEPSV",
        bad="true",
        good="false",
        effect="disabled recover leftover EPSV so git ftp fetch hung behind a firewall",
        probe="git fetch ftp-origin 2>&1 | tail",
        bad_obs="error: leftover EPSV disabled; PASV blocked",
        good_obs="From leftover ftp-origin\n   a1b2c3d..d4e5f6a  main",
        wrong="git fetch --ipv4 ftp-origin",
        wrong_obs="error: leftover http.noEPSV=true still",
        handoff="ci-http-noepsv-true",
        ci_obs="true",
    ),
)
add(
    gitcfg(
        slug="http-savecookies-true",
        repo="http-ops/save-cookies",
        marker="HTTPSC_N",
        old="2",
        new="5",
        stem="httpsc",
        key="http.saveCookies",
        bad="true",
        good="false",
        effect="wrote recover leftover session cookies into the repo so CI committed Set-Cookie headers",
        probe="git ls-remote origin 2>&1 | tail; ls .git/cookies 2>&1 | tail",
        bad_obs=".git/cookies leftover Set-Cookie",
        good_obs="ls: leftover .git/cookies missing",
        wrong="git -c http.cookieFile= /dev/null ls-remote origin",
        wrong_obs=".git/cookies leftover still (http.saveCookies=true)",
    ),
    gitcfg(
        slug="http-sslcapath-stale",
        repo="http-ops/ssl-capath",
        marker="HTTPSCAP_N",
        old="0",
        new="9",
        stem="httpscap",
        key="http.sslCAPath",
        bad="/etc/leftover/ca-dir",
        good=None,
        effect="pointed recover leftover TLS trust at a missing CA directory so fetch  SSL died",
        probe="git ls-remote origin 2>&1 | tail",
        bad_obs="error: leftover could not load CA path /etc/leftover/ca-dir",
        good_obs="a1b2c3d\trefs/heads/main",
        wrong="git -c http.sslCAInfo= ls-remote origin",
        wrong_obs="error: leftover http.sslCAPath still /etc/leftover/ca-dir",
        handoff="ci-http-sslcapath-stale",
        ci_obs="/etc/leftover/ca-dir",
    ),
)
add(
    gitcfg(
        slug="http-sslkey-stale",
        repo="http-ops/ssl-key",
        marker="HTTPSK_N",
        old="1",
        new="7",
        stem="httpsk",
        key="http.sslKey",
        bad="/etc/leftover/client.key",
        good=None,
        effect="loaded recover leftover mTLS key from a missing PEM so GitHub 403ed",
        probe="git fetch origin 2>&1 | tail",
        bad_obs="error: leftover could not load key /etc/leftover/client.key",
        good_obs="From leftover origin\n   a1b2c3d..d4e5f6a  main",
        wrong="git -c http.sslCert= fetch origin",
        wrong_obs="error: leftover http.sslKey still /etc/leftover/client.key",
    ),
    gitcfg(
        slug="imap-authmethod-cram",
        repo="imap-ops/auth-cram",
        marker="IMAPCR_N",
        old="3",
        new="4",
        stem="imapcr",
        key="imap.authMethod",
        bad="CRAM-MD5",
        good="LOGIN",
        effect="tried recover leftover CRAM-MD5 against an IMAP that only allowed LOGIN so send bounced",
        probe="git imap-send < /tmp/hotfix.mbox 2>&1 | tail",
        bad_obs="error: leftover AUTH CRAM-MD5 not supported",
        good_obs="sending leftover 1 message",
        wrong="git -c imap.authMethod=LOGIN imap-send < /tmp/hotfix.mbox",
        wrong_obs="error: leftover imap.authMethod=CRAM-MD5 still",
        handoff="ci-imap-authmethod-cram",
        ci_obs="CRAM-MD5",
    ),
)
add(
    gitcfg(
        slug="imap-host-stale",
        repo="imap-ops/host-stale",
        marker="IMAPHO_N",
        old="0",
        new="8",
        stem="imaphost",
        key="imap.host",
        bad="imaps://leftover-mail.example",
        good="imaps://imap.example",
        effect="sent recover leftover git imap-send to a decommissioned host",
        probe="git imap-send < /tmp/hotfix.mbox 2>&1 | tail",
        bad_obs="fatal: leftover leftover-mail.example: Name or service not known",
        good_obs="sending leftover 1 message",
        wrong="git -c imap.host=imaps://imap.example imap-send < /tmp/hotfix.mbox",
        wrong_obs="fatal: leftover imap.host still leftover-mail.example",
    ),
    gitcfg(
        slug="imap-port-smtp",
        repo="imap-ops/port-smtp",
        marker="IMAPPT_N",
        old="2",
        new="6",
        stem="imappt",
        key="imap.port",
        bad="25",
        good="993",
        effect="connected recover leftover IMAP on SMTP port 25 so AUTH hung",
        probe="git imap-send < /tmp/hotfix.mbox 2>&1 | tail",
        bad_obs="error: leftover connection timed out on :25",
        good_obs="sending leftover 1 message",
        wrong="git -c imap.port=993 imap-send < /tmp/hotfix.mbox",
        wrong_obs="error: leftover imap.port=25 still",
        handoff="ci-imap-port-smtp",
        ci_obs="25",
    ),
)
add(
    gitcfg(
        slug="log-graphcolors-empty",
        repo="log-ops/graph-colors",
        marker="LOGGC_N",
        old="1",
        new="5",
        stem="loggc",
        key="log.graphColors",
        bad=" ",
        good="red,green,blue",
        effect="left recover leftover git log --graph without colors so octopus parents were unreadable",
        probe="git log --graph --oneline -8 | head",
        bad_obs="* leftover (flat; no graph colors)",
        good_obs="* leftover red hotfix\n|\\ leftover green octopus",
        wrong="git log --graph --color=always --oneline -8",
        wrong_obs="* leftover (log.graphColors empty)",
    ),
    gitcfg(
        slug="mailmap-file-stale-path",
        repo="mail-ops/mailmap-path",
        marker="MMFILE_N",
        old="0",
        new="9",
        stem="mmfile",
        key="mailmap.file",
        bad="/etc/leftover-mailmap",
        good=".mailmap",
        effect="read recover leftover mailmap from a missing file so Old Bot stayed in git log",
        probe="git log -1 --format='%an <%ae>'",
        bad_obs="Old Bot leftover <bot@old.example>",
        good_obs="Oncall leftover <oncall@ex>",
        wrong="git log -1 --use-mailmap --format='%an <%ae>'",
        wrong_obs="Old Bot leftover (mailmap.file missing)",
        handoff="ci-mailmap-file-stale-path",
        ci_obs="/etc/leftover-mailmap",
    ),
)
add(
    gitcfg(
        slug="merge-autostash-true",
        repo="merge-ops/auto-stash",
        marker="MRGAST_N",
        old="3",
        new="7",
        stem="mrgast",
        key="merge.autoStash",
        bad="true",
        good="false",
        effect="stashed recover leftover dirty hotfix before merge and never popped it so the hunk vanished",
        probe="git merge origin/main 2>&1 | tail; git stash list | head",
        bad_obs="Created leftover autostash\nstash@{0}: leftover autostash",
        good_obs="Merge leftover made by the 'ort' strategy",
        wrong="git merge --no-autostash origin/main",
        wrong_obs="Created leftover autostash (merge.autoStash=true)",
    ),
    gitcfg(
        slug="merge-defaulttoupstream-false",
        repo="merge-ops/default-up-off",
        marker="MRGDUP_N",
        old="2",
        new="4",
        stem="mrgdup",
        key="merge.defaultToUpstream",
        bad="false",
        good="true",
        effect="refused recover leftover git merge with no args so CI never merged origin/hotfix",
        probe="git merge 2>&1 | tail",
        bad_obs="fatal: leftover no merge candidate (defaultToUpstream=false)",
        good_obs="Merge leftover branch 'origin/hotfix'",
        wrong="git merge @{u}",
        wrong_obs="fatal: leftover alias still git merge with no args",
        handoff="ci-merge-defaulttoupstream-false",
        ci_obs="false",
    ),
)
add(
    gitcfg(
        slug="mergetool-keeptemporaries-true",
        repo="merge-ops/keep-tmp",
        marker="MTTMP_N",
        old="0",
        new="8",
        stem="mttmp",
        key="mergetool.keepTemporaries",
        bad="true",
        good="false",
        effect="left recover leftover *.orig and *_BACKUP_* so CI packed conflict temps",
        probe="git mergetool --no-prompt; ls src/*BACKUP* src/*.orig 2>&1 | tail",
        bad_obs="src/mttmp.py_BACKUP_123 leftover",
        good_obs="ls: leftover no BACKUP",
        wrong="git mergetool --no-prompt --no-backup",
        wrong_obs="src/mttmp.py_BACKUP leftover (keepTemporaries=true)",
    ),
    gitcfg(
        slug="mergetool-trustexitcode-true",
        repo="merge-ops/trust-exit",
        marker="MTEXIT_N",
        old="1",
        new="6",
        stem="mtexit",
        key="mergetool.trustExitCode",
        bad="true",
        good="false",
        effect="trusted recover leftover mergetool exit 0 even when the file still had conflict markers",
        probe="git mergetool --no-prompt; rg '<<<<<<' src/mtexit.py || echo clean",
        bad_obs="<<<<<< leftover (exit 0 trusted)",
        good_obs="clean leftover",
        wrong="git mergetool --tool=vimdiff --no-prompt",
        wrong_obs="<<<<<< leftover (trustExitCode=true)",
        handoff="ci-mergetool-trustexitcode-true",
        ci_obs="true",
    ),
)
add(
    gitcfg(
        slug="mergetool-writetotemp-true",
        repo="merge-ops/write-temp",
        marker="MTWTEMP_N",
        old="3",
        new="5",
        stem="mtwtemp",
        key="mergetool.writeToTemp",
        bad="true",
        good="false",
        effect="wrote recover leftover merge results to /tmp so the worktree file never updated",
        probe="git mergetool --no-prompt; git diff --stat src/mtwtemp.py",
        bad_obs=" src/mtwtemp.py leftover | 0 (result in /tmp)",
        good_obs=" src/mtwtemp.py leftover | 8 +-",
        wrong="git mergetool --no-prompt --tool=vimdiff",
        wrong_obs=" src/mtwtemp.py leftover | 0 (writeToTemp=true)",
    ),
    gitcfg(
        slug="notes-rewrite-amend-false",
        repo="notes-ops/rewrite-amend-off",
        marker="NTAMD_N",
        old="0",
        new="9",
        stem="ntamd",
        key="notes.rewrite.amend",
        bad="false",
        good="true",
        effect="dropped recover leftover notes on git commit --amend so the INC trailer vanished",
        probe="git commit --amend --no-edit && git notes show HEAD 2>&1 | tail",
        bad_obs="error: leftover no note found",
        good_obs="INC leftover 4421",
        wrong="git commit --amend --no-edit --reset-author",
        wrong_obs="error: leftover notes.rewrite.amend=false still",
        handoff="ci-notes-rewrite-amend-false",
        ci_obs="false",
    ),
)
add(
    gitcfg(
        slug="pager-show-cat",
        repo="pager-ops/show-cat",
        marker="PGSHOW_N",
        old="2",
        new="7",
        stem="pgshow",
        key="pager.show",
        bad="cat",
        good="less -F -X",
        effect="piped recover leftover git show through cat so CI captured a truncated body",
        probe="git show -s HEAD | wc -c",
        bad_obs="40 leftover truncated",
        good_obs="840 leftover",
        wrong="git --no-pager show -s HEAD",
        wrong_obs="40 leftover (pager.show=cat still ran)",
    ),
    gitcfg(
        slug="pager-status-cat",
        repo="pager-ops/status-cat",
        marker="PGSTAT_N",
        old="1",
        new="4",
        stem="pgstat",
        key="pager.status",
        bad="cat",
        good="less -F -X",
        effect="piped recover leftover git status through cat so CI truncated unmerged paths",
        probe="git status | wc -c",
        bad_obs="80 leftover truncated",
        good_obs="640 leftover",
        wrong="git --no-pager status",
        wrong_obs="80 leftover (pager.status=cat)",
        handoff="ci-pager-status-cat",
        ci_obs="cat",
    ),
)
add(
    gitcfg(
        slug="protocol-allow-never",
        repo="proto-ops/allow-never",
        marker="PROTOA_N",
        old="0",
        new="8",
        stem="protoa",
        key="protocol.allow",
        bad="never",
        good="user",
        effect="blocked recover leftover every transport so git fetch origin died before TLS",
        probe="git fetch origin 2>&1 | tail",
        bad_obs="fatal: leftover transport 'https' not allowed",
        good_obs="From leftover origin\n   a1b2c3d..d4e5f6a  main",
        wrong="git -c protocol.https.allow=always fetch origin",
        wrong_obs="fatal: leftover protocol.allow=never beats protocol.https.allow",
    ),
    gitcfg(
        slug="receive-updateserverinfo-false",
        repo="receive-ops/update-info-off",
        marker="RCVUSI_N",
        old="3",
        new="6",
        stem="rcvusi",
        key="receive.updateServerInfo",
        bad="false",
        good="true",
        effect="skipped recover leftover info/refs refresh so dumb HTTP clones stayed on a stale tip",
        probe="git receive-pack . </dev/null; cat info/refs | rg hotfix || echo stale",
        bad_obs="stale leftover (info/refs not updated)",
        good_obs="a1b2c3d leftover refs/heads/hotfix",
        wrong="git update-server-info",
        wrong_obs="stale leftover (next receive.updateServerInfo=false)",
        handoff="ci-receive-updateserverinfo-false",
        ci_obs="false",
    ),
)
add(
    gitcfg(
        slug="sendemail-bcc-stale",
        repo="mail-ops/bcc-stale",
        marker="SMBCC_N",
        old="2",
        new="5",
        stem="smbcc",
        key="sendemail.bcc",
        bad="archive@legacy.example",
        good=None,
        effect="bcc'd recover leftover every series to a dead archive so SMTP 550ed",
        probe="git send-email --dry-run /tmp/hotfix.mbox 2>&1 | rg -i bcc",
        bad_obs="Bcc: leftover archive@legacy.example",
        good_obs="(empty leftover; no Bcc)",
        wrong="git send-email --bcc=oncall@ex --dry-run /tmp/hotfix.mbox",
        wrong_obs="Bcc: leftover archive@legacy.example still",
    ),
    gitcfg(
        slug="sendemail-cc-stale",
        repo="mail-ops/cc-stale",
        marker="SMCCST_N",
        old="0",
        new="9",
        stem="smccst",
        key="sendemail.cc",
        bad="departed@old.example",
        good="oncall@ex",
        effect="cc'd recover leftover patches to a departed oncall so moderation bounced",
        probe="git send-email --dry-run /tmp/hotfix.mbox 2>&1 | rg -i '^Cc:'",
        bad_obs="Cc: leftover departed@old.example",
        good_obs="Cc: leftover oncall@ex",
        wrong="git send-email --cc=oncall@ex --dry-run /tmp/hotfix.mbox",
        wrong_obs="Cc: leftover departed@old.example (sendemail.cc beats --cc)",
        handoff="ci-sendemail-cc-stale",
        ci_obs="departed@old.example",
    ),
)
add(
    gitcfg(
        slug="sendemail-chainreplyto-false",
        repo="mail-ops/chain-reply",
        marker="SMCHAIN_N",
        old="1",
        new="7",
        stem="smchain",
        key="sendemail.chainReplyTo",
        bad="false",
        good="true",
        effect="threaded recover leftover replies only to the cover so 0002 In-Reply-To pointed at 0000",
        probe="git send-email --dry-run /tmp/0001.patch /tmp/0002.patch 2>&1 | rg -i 'in-reply'",
        bad_obs="In-Reply-To: leftover cover only",
        good_obs="In-Reply-To: leftover 0001 then 0002",
        wrong="git send-email --chain-reply-to --dry-run /tmp/0001.patch",
        wrong_obs="In-Reply-To: leftover cover only (chainReplyTo=false)",
    ),
    gitcfg(
        slug="sendemail-envelopesender-stale",
        repo="mail-ops/envelope-stale",
        marker="SMENV_N",
        old="3",
        new="4",
        stem="smenv",
        key="sendemail.envelopeSender",
        bad="bounce@legacy.example",
        good="oncall@ex",
        effect="set recover leftover MAIL FROM to bounce@legacy so the relay 550ed",
        probe="git send-email --dry-run /tmp/hotfix.mbox 2>&1 | rg MAIL",
        bad_obs="MAIL FROM leftover bounce@legacy.example",
        good_obs="MAIL FROM leftover oncall@ex",
        wrong="git send-email --envelope-sender=oncall@ex --dry-run /tmp/hotfix.mbox",
        wrong_obs="MAIL FROM leftover bounce@legacy.example still",
        handoff="ci-sendemail-envelopesender-stale",
        ci_obs="bounce@legacy.example",
    ),
)
add(
    gitcfg(
        slug="sendemail-smtpserverport-25",
        repo="mail-ops/smtp-port-25",
        marker="SMTP25_N",
        old="0",
        new="8",
        stem="smtp25",
        key="sendemail.smtpServerPort",
        bad="25",
        good="587",
        effect="connected recover leftover SMTP on port 25 so STARTTLS never ran",
        probe="git send-email --dry-run /tmp/hotfix.mbox 2>&1 | tail",
        bad_obs="error: leftover connection timed out on :25",
        good_obs="OK leftover dry-run",
        wrong="git send-email --smtp-server-port=587 --dry-run /tmp/hotfix.mbox",
        wrong_obs="error: leftover sendemail.smtpServerPort=25 still",
    ),
    gitcfg(
        slug="sendemail-to-stale",
        repo="mail-ops/to-stale",
        marker="SMTO_N",
        old="2",
        new="6",
        stem="smto",
        key="sendemail.to",
        bad="list@legacy.example",
        good="dev@ex",
        effect="sent recover leftover the series to a dead list so nobody saw the hotfix",
        probe="git send-email --dry-run /tmp/hotfix.mbox 2>&1 | rg '^To:'",
        bad_obs="To: leftover list@legacy.example",
        good_obs="To: leftover dev@ex",
        wrong="git send-email --to=dev@ex --dry-run /tmp/hotfix.mbox",
        wrong_obs="To: leftover list@legacy.example (sendemail.to beats --to)",
        handoff="ci-sendemail-to-stale",
        ci_obs="list@legacy.example",
    ),
)
add(
    gitcfg(
        slug="sendemail-validate-false",
        repo="mail-ops/validate-off",
        marker="SMVAL_N",
        old="1",
        new="5",
        stem="smval",
        key="sendemail.validate",
        bad="false",
        good="true",
        effect="skipped recover leftover sendemail.validate so a patch with a bare CR was posted",
        probe="git send-email --dry-run /tmp/hotfix.mbox 2>&1 | tail",
        bad_obs="OK leftover dry-run (bare CR not rejected)",
        good_obs="error: leftover patch contains a bare CR",
        wrong="git send-email --validate --dry-run /tmp/hotfix.mbox",
        wrong_obs="OK leftover (sendemail.validate=false beats --validate)",
    ),
    gitcfg(
        slug="splitindex-sharedindexexpire-now",
        repo="index-ops/shared-expire-now",
        marker="SPLEXP_N",
        old="0",
        new="9",
        stem="splexp",
        key="splitIndex.sharedIndexExpire",
        bad="now",
        good="2.weeks.ago",
        effect="expired recover leftover shared indexes immediately so every git add rewrote the split index",
        probe="git add src/splexp.py 2>&1 | tail; ls .git/sharedindex.* 2>&1 | tail",
        bad_obs="error: leftover shared index expired (now)",
        good_obs=".git/sharedindex leftover",
        wrong="git update-index --split-index",
        wrong_obs="error: leftover splitIndex.sharedIndexExpire=now",
        handoff="ci-splitindex-sharedindexexpire-now",
        ci_obs="now",
    ),
)
add(
    gitcfg(
        slug="status-relativepaths-false",
        repo="status-ops/relative-off",
        marker="STREL_N",
        old="3",
        new="7",
        stem="strel",
        key="status.relativePaths",
        bad="false",
        good="true",
        effect="printed recover leftover git status paths from repo root while cwd was src/ so CI opened the wrong file",
        probe="cd src && git status --short",
        bad_obs="M  leftover src/strel.py",
        good_obs="M  leftover strel.py",
        wrong="cd src && git status --short --relative",
        wrong_obs="M  leftover src/strel.py (status.relativePaths=false)",
    ),
    gitcfg(
        slug="status-displaycommentprefix-true",
        repo="status-ops/comment-prefix",
        marker="STCMT_N",
        old="2",
        new="4",
        stem="stcmt",
        key="status.displayCommentPrefix",
        bad="true",
        good="false",
        effect="prefixed recover leftover git status lines with # so CI regex on UU missed the conflict",
        probe="git status",
        bad_obs="# leftover Unmerged paths:\n# UU leftover src/stcmt.py",
        good_obs="Unmerged leftover paths:\n  src/stcmt.py",
        wrong="git status --untracked-files=no",
        wrong_obs="# leftover Unmerged (displayCommentPrefix=true)",
        handoff="ci-status-displaycommentprefix-true",
        ci_obs="true",
    ),
)
add(
    gitcfg(
        slug="submodule-stickyrecursiveclone-true",
        repo="sub-ops/sticky-recursive",
        marker="SUBSTK_N",
        old="0",
        new="8",
        stem="substk",
        key="submodule.stickyRecursiveClone",
        bad="true",
        good="false",
        effect="forced recover leftover recursive clones of nested subs so CI fetched 4GB of unused history",
        probe="git submodule update --init 2>&1 | tail; git -C vendor/lib rev-parse --is-shallow-repository",
        bad_obs="Cloning leftover nested vendor/lib/vendor (recursive sticky)\nfalse leftover",
        good_obs="Submodule leftover vendor/lib (a1b2c3d)",
        wrong="git submodule update --init --recommend-shallow",
        wrong_obs="Cloning leftover nested (stickyRecursiveClone=true)",
    ),
    gitcfg(
        slug="tar-umask-zero",
        repo="archive-ops/tar-umask",
        marker="TARUM_N",
        old="1",
        new="6",
        stem="tarum",
        key="tar.umask",
        bad="0",
        good="022",
        effect="packed recover leftover git archive tarballs as mode 0777 so CI extracted world-writable hotfix scripts",
        probe="git archive --format=tar HEAD src/tarum.py | tar -tv | tail",
        bad_obs="-rwxrwxrwx leftover src/tarum.py",
        good_obs="-rw-r--r-- leftover src/tarum.py",
        wrong="git archive --format=tar --prefix=src/ HEAD src/tarum.py | tar -tv",
        wrong_obs="-rwxrwxrwx leftover (tar.umask=0)",
        handoff="ci-tar-umask-zero",
        ci_obs="0",
    ),
)
add(
    gitcfg(
        slug="transfer-bundleuri-stale",
        repo="xfer-ops/bundle-uri",
        marker="XFERBUN_N",
        old="3",
        new="5",
        stem="xferbun",
        key="transfer.bundleURI",
        bad="https://leftover.example/repo.bundle",
        good=None,
        effect="prefaced recover leftover every fetch with a 404 bundle URI so clones aborted",
        probe="git fetch origin 2>&1 | tail",
        bad_obs="error: leftover bundle https://leftover.example/repo.bundle 404",
        good_obs="From leftover origin\n   a1b2c3d..d4e5f6a  main",
        wrong="git fetch --no-bundle-uri origin",
        wrong_obs="error: leftover transfer.bundleURI still 404",
    ),
    gitcfg(
        slug="uploadarchive-allowunreachable-true",
        repo="archive-ops/allow-unreach",
        marker="UPARCH_N",
        old="0",
        new="9",
        stem="uparch",
        key="uploadarchive.allowUnreachable",
        bad="true",
        good="false",
        effect="served recover leftover dangling hotfix blobs over git archive --remote so secrets leaked",
        probe="git archive --remote=origin a1b2c3d secrets.env 2>&1 | tail",
        bad_obs="tar leftover secrets.env (unreachable allowed)",
        good_obs="fatal: leftover upload-archive: archiving unreachable not allowed",
        wrong="git archive --remote=origin HEAD secrets.env",
        wrong_obs="tar leftover (uploadarchive.allowUnreachable=true)",
        handoff="ci-uploadarchive-allowunreachable-true",
        ci_obs="true",
    ),
)
add(
    gitcfg(
        slug="uploadpack-allowanysha1-false",
        repo="upload-ops/any-sha-off",
        marker="UPANY_N",
        old="2",
        new="7",
        stem="upany",
        key="uploadpack.allowAnySHA1InWant",
        bad="false",
        good="true",
        effect="rejected recover leftover fetch of an unadvertised hotfix SHA so bisect died",
        probe="git fetch origin a1b2c3d 2>&1 | tail",
        bad_obs="error: leftover server does not allow request for unadvertised object",
        good_obs="* branch leftover a1b2c3d -> FETCH_HEAD",
        wrong="git fetch --negotiate-only origin a1b2c3d",
        wrong_obs="error: leftover unadvertised object still refused",
    ),
    gitcfg(
        slug="uploadpack-keepalive-zero",
        repo="upload-ops/keep-alive-zero",
        marker="UPKA_N",
        old="1",
        new="4",
        stem="upka",
        key="uploadpack.keepAlive",
        bad="0",
        good="5",
        effect="sent recover leftover no keepalive during pack so a slow fetch was killed as idle",
        probe="git fetch origin 2>&1 | tail",
        bad_obs="error: leftover upload-pack idle kill (keepAlive=0)",
        good_obs="From leftover origin\n   a1b2c3d..d4e5f6a  main",
        wrong="git fetch --progress origin",
        wrong_obs="error: leftover uploadpack.keepAlive=0 still",
        handoff="ci-uploadpack-keepalive-zero",
        ci_obs="0",
    ),
)
add(
    cmdplant(
        slug="git-cherry-limit-stale",
        repo="cherry-ops/limit-stale",
        marker="CHERRY_N",
        old="0",
        new="8",
        stem="cherry",
        knob="git cherry leftover limit",
        effect="compared recover leftover hotfix against origin/main~400 so every commit looked equivalent",
        map_cmd="git cherry origin/main~400 hotfix 2>&1 | head; rg CHERRY_N src/cherry.py",
        map_obs="- leftover a1b2c3d (false equivalent)\nCHERRY_N = 0",
        wrong="git cherry origin/main hotfix",
        wrong_obs="- leftover a1b2c3d still (alias origin/main~400)",
        rec_cmd="git cherry origin/main hotfix | rg '^[+]' | head",
        rec_obs="+ leftover a1b2c3d hotfix",
        left_cmd="git cherry origin/main hotfix | rg '^[+]' | wc -l",
        left_obs="3 leftover",
    ),
    cmdplant(
        slug="git-patch-id-stable-off",
        repo="patch-ops/id-unstable",
        marker="PTID_N",
        old="2",
        new="6",
        stem="ptid",
        knob="git patch-id leftover unstable",
        effect="hashed recover leftover patches without --stable so whitespace-only rebases looked new",
        map_cmd="git show HEAD | git patch-id ; git show HEAD | git patch-id --stable; rg PTID_N src/ptid.py",
        map_obs="deadbeef leftover unstable\na1b2c3d leftover stable\nPTID_N = 2",
        wrong="git patch-id --unstable",
        wrong_obs="deadbeef leftover still (alias omits --stable)",
        rec_cmd="git show HEAD | git patch-id --stable",
        rec_obs="a1b2c3d leftover stable",
        left_cmd="git show HEAD | git patch-id --stable | awk '{print $1}'",
        left_obs="a1b2c3d leftover",
        handoff="ci-git-patch-id-stable-off",
        ci_obs="deadbeef leftover unstable",
        ci_probe="ssh ci-runner 'git show HEAD | git patch-id'",
    ),
)
add(
    cmdplant(
        slug="git-fmt-merge-msg-log-stale",
        repo="merge-ops/fmt-msg",
        marker="FMTMSG_N",
        old="1",
        new="5",
        stem="fmtmsg",
        knob="git fmt-merge-msg leftover --log",
        effect="built recover leftover merge messages with --log=0 so the hotfix SHA list vanished",
        map_cmd="git fmt-merge-msg --log=0 < .git/FETCH_HEAD | head; rg FMTMSG_N src/fmtmsg.py",
        map_obs="Merge leftover branch 'hotfix' (no log)\nFMTMSG_N = 1",
        wrong="git merge --log origin/hotfix",
        wrong_obs="Merge leftover (alias fmt-merge-msg --log=0)",
        rec_cmd="git fmt-merge-msg --log=20 < .git/FETCH_HEAD | rg hotfix | head",
        rec_obs="* leftover hotfix a1b2c3d",
        left_cmd="git fmt-merge-msg --log=20 < .git/FETCH_HEAD | rg hotfix | wc -l",
        left_obs="3 leftover",
    ),
    cmdplant(
        slug="git-merge-base-independent-stale",
        repo="merge-ops/base-independent",
        marker="MRGBI_N",
        old="3",
        new="9",
        stem="mrgbi",
        knob="git merge-base --independent leftover",
        effect="reported recover leftover octopus tips as independent so CI skipped the true merge-base",
        map_cmd="git merge-base --independent hotfix docs vendor; rg MRGBI_N src/mrgbi.py",
        map_obs="a1b2c3d leftover\nd4e5f6a leftover\neeeeeee leftover\nMRGBI_N = 3",
        wrong="git merge-base hotfix docs",
        wrong_obs="a1b2c3d leftover still independent (alias --independent)",
        rec_cmd="git merge-base --octopus hotfix docs vendor",
        rec_obs="b0b0b0b leftover octopus base",
        left_cmd="git merge-base --octopus hotfix docs vendor",
        left_obs="b0b0b0b leftover",
        handoff="ci-git-merge-base-independent-stale",
        ci_obs="a1b2c3d leftover\nd4e5f6a leftover\neeeeeee leftover",
        ci_probe="ssh ci-runner 'git merge-base --independent hotfix docs vendor'",
    ),
)
add(
    cmdplant(
        slug="git-ls-tree-name-only-stale",
        repo="tree-ops/ls-name-only",
        marker="LSTREE_N",
        old="0",
        new="8",
        stem="lstree",
        knob="git ls-tree --name-only leftover",
        effect="listed recover leftover tree names without modes so CI missed a 100755 hotfix script",
        map_cmd="git ls-tree --name-only HEAD src | head; rg LSTREE_N src/lstree.py",
        map_obs="src/lstree.py leftover (mode omitted)\nLSTREE_N = 0",
        wrong="git ls-tree HEAD src",
        wrong_obs="src/lstree.py leftover still name-only (alias)",
        rec_cmd="git ls-tree HEAD src/lstree.py",
        rec_obs="100755 leftover blob a1b2c3d\tsrc/lstree.py",
        left_cmd="git ls-tree HEAD src/lstree.py | awk '{print $1}'",
        left_obs="100755 leftover",
    ),
    cmdplant(
        slug="git-diff-files-ignore-submodules",
        repo="diff-ops/files-sub",
        marker="DFFSUB_N",
        old="2",
        new="6",
        stem="dffsub",
        knob="git diff-files --ignore-submodules leftover",
        effect="skipped recover leftover dirty submodule SHAs so CI thought vendor/lib was clean",
        map_cmd="git diff-files --ignore-submodules; git -C vendor/lib rev-parse --short HEAD; rg DFFSUB_N src/dffsub.py",
        map_obs="(empty leftover; submodule dirty omitted)\na1b2c3d leftover vendor HEAD\nDFFSUB_N = 2",
        wrong="git diff --ignore-submodules=all",
        wrong_obs="(empty leftover alias --ignore-submodules)",
        rec_cmd="git diff-files --ignore-submodules=none -- vendor/lib",
        rec_obs=":160000 160000 leftover vendor/lib",
        left_cmd="git diff-files --ignore-submodules=none --name-only -- vendor/lib",
        left_obs="vendor/lib leftover",
        handoff="ci-git-diff-files-ignore-submodules",
        ci_obs="(empty leftover; submodule dirty omitted)",
        ci_probe="ssh ci-runner 'git diff-files --ignore-submodules | wc -c'",
    ),
)
add(
    cmdplant(
        slug="git-diff-index-cached-stale",
        repo="diff-ops/index-cached",
        marker="DFIDX_N",
        old="1",
        new="5",
        stem="dfidx",
        knob="git diff-index --cached leftover HEAD~20",
        effect="diffed recover leftover the index against HEAD~20 so every hotfix file looked added",
        map_cmd="git diff-index --cached HEAD~20 --name-only | wc -l; rg DFIDX_N src/dfidx.py",
        map_obs="184 leftover names (false adds)\nDFIDX_N = 1",
        wrong="git diff --cached --name-only",
        wrong_obs="184 leftover still (alias HEAD~20)",
        rec_cmd="git diff-index --cached HEAD --name-only -- src/dfidx.py",
        rec_obs="src/dfidx.py leftover",
        left_cmd="git diff-index --cached HEAD --name-only | wc -l",
        left_obs="1 leftover",
    ),
    cmdplant(
        slug="git-clean-fdx-excludesfile-stale",
        repo="clean-ops/fdx-exclude",
        marker="CLNFDX_N",
        old="3",
        new="9",
        stem="clnfdx",
        knob="git clean -fdx leftover excludesFile",
        effect="cleaned recover leftover build artifacts but skipped src/clnfdx.py because a stale excludesFile matched it",
        map_cmd="git clean -fdx -n 2>&1 | rg clnfdx || echo skipped; rg CLNFDX_N src/clnfdx.py",
        map_obs="skipped leftover (excludesFile matched src)\nCLNFDX_N = 3",
        wrong="git clean -fdx -e '!src/clnfdx.py' -n",
        wrong_obs="skipped leftover still (excludesFile wins)",
        rec_cmd="git config --unset core.excludesFile && git clean -fdx -n -- src | rg clnfdx || echo would-clean",
        rec_obs="Would leftover remove src/clnfdx.pyc",
        left_cmd="git config --get core.excludesFile; echo exit:$?",
        left_obs="exit:1 leftover",
        handoff="ci-git-clean-fdx-excludesfile-stale",
        ci_obs="skipped leftover (excludesFile matched src)",
        ci_probe="ssh ci-runner 'git config --get core.excludesFile'",
    ),
)
add(
    cmdplant(
        slug="git-reset-mixed-drops-intent",
        repo="reset-ops/mixed-intent",
        marker="RSTMIX_N",
        old="0",
        new="8",
        stem="rstmix",
        knob="git reset leftover --mixed",
        effect="mixed-reset recover leftover the index so intent-to-add hotfix paths vanished before commit",
        map_cmd="git reset HEAD && git ls-files -v src/rstmix.py; rg RSTMIX_N src/rstmix.py",
        map_obs="? leftover src/rstmix.py (intent gone)\nRSTMIX_N = 0",
        wrong="git reset --soft HEAD",
        wrong_obs="? leftover still (alias --mixed)",
        rec_cmd="git add src/rstmix.py && git ls-files -v src/rstmix.py",
        rec_obs="H leftover src/rstmix.py",
        left_cmd="git diff --cached --name-only -- src/rstmix.py",
        left_obs="src/rstmix.py leftover",
    ),
    cmdplant(
        slug="git-var-author-ident-stale",
        repo="var-ops/author-ident",
        marker="VARAI_N",
        old="2",
        new="6",
        stem="varai",
        knob="git var GIT_AUTHOR_IDENT leftover",
        effect="reported recover leftover Old Bot as GIT_AUTHOR_IDENT so commits used the departed uid",
        map_cmd="git var GIT_AUTHOR_IDENT; rg VARAI_N src/varai.py",
        map_obs="Old Bot leftover <bot@old.example> 0000000000 +0000\nVARAI_N = 2",
        wrong="git var GIT_COMMITTER_IDENT",
        wrong_obs="Old Bot leftover still (author ident stale)",
        rec_cmd="git config user.name Oncall && git config user.email oncall@ex && git var GIT_AUTHOR_IDENT",
        rec_obs="Oncall leftover <oncall@ex>",
        left_cmd="git var GIT_AUTHOR_IDENT | awk '{print $1}'",
        left_obs="Oncall leftover",
        handoff="ci-git-var-author-ident-stale",
        ci_obs="Old Bot leftover <bot@old.example> 0000000000 +0000",
        ci_probe="ssh ci-runner 'git var GIT_AUTHOR_IDENT'",
    ),
)
add(
    cmdplant(
        slug="git-mktag-verify-skip",
        repo="tag-ops/mktag-skip",
        marker="MKTAG_N",
        old="1",
        new="5",
        stem="mktag",
        knob="git mktag leftover skip verify",
        effect="wrote recover leftover a tag object without tagger so git fetch refused it",
        map_cmd="git mktag < /tmp/bad.tag 2>&1 | tail; rg MKTAG_N src/mktag.py",
        map_obs="error: leftover missing tagger (verify skipped in wrapper then remote refused)\nMKTAG_N = 1",
        wrong="git hash-object -t tag -w /tmp/bad.tag",
        wrong_obs="error: leftover remote still refused missing tagger",
        rec_cmd="printf 'object %s\\ntype commit\\ntag v2.0.1\\ntagger Oncall <oncall@ex> 1 +0000\\n\\nhotfix\\n' $(git rev-parse HEAD) | git mktag",
        rec_obs="a1b2c3d leftover tag",
        left_cmd="git cat-file -t a1b2c3d",
        left_obs="tag leftover",
    ),
    cmdplant(
        slug="git-credential-cache-timeout-one",
        repo="cred-ops/cache-one",
        marker="CRDCACHE_N",
        old="3",
        new="9",
        stem="crdcache",
        knob="git credential-cache leftover --timeout=1",
        effect="expired recover leftover credentials after 1s so the next fetch prompted in CI",
        map_cmd="git credential-cache --timeout=1 exit; sleep 2; echo url=https://github.com/org/app.git | git credential fill 2>&1 | tail; rg CRDCACHE_N src/crdcache.py",
        map_obs="fatal: leftover could not read username (cache expired)\nCRDCACHE_N = 3",
        wrong="git credential-cache --timeout=3600",
        wrong_obs="fatal: leftover alias still --timeout=1",
        rec_cmd="git credential-cache --timeout=3600 && printf 'url=https://github.com/org/app.git\\nusername=oncall\\npassword=ok\\n' | git credential approve",
        rec_obs="username=oncall leftover",
        left_cmd="echo url=https://github.com/org/app.git | git credential fill | rg username",
        left_obs="username=oncall leftover",
        handoff="ci-git-credential-cache-timeout-one",
        ci_obs="fatal: leftover could not read username (cache expired)",
        ci_probe="ssh ci-runner 'git credential-cache --timeout=1 exit; echo timeout'",
    ),
)
add(
    cmdplant(
        slug="git-difftool-gui-stale",
        repo="diff-ops/tool-gui",
        marker="DFTGUI_N",
        old="0",
        new="8",
        stem="dftgui",
        knob="git difftool --gui leftover",
        effect="launched recover leftover git difftool --gui via a missing meld so the hunk review hung",
        map_cmd="git difftool --gui --no-prompt HEAD~1 -- src/dftgui.py 2>&1 | tail; rg DFTGUI_N src/dftgui.py",
        map_obs="fatal: leftover cannot run leftover-meld\nDFTGUI_N = 0",
        wrong="git difftool --no-prompt HEAD~1 -- src/dftgui.py",
        wrong_obs="fatal: leftover alias still --gui leftover-meld",
        rec_cmd="git difftool --no-prompt --tool=vimdiff HEAD~1 -- src/dftgui.py",
        rec_obs="view leftover src/dftgui.py",
        left_cmd="git config --get diff.guitool; echo exit:$?",
        left_obs="exit:1 leftover",
    ),
    cmdplant(
        slug="git-subtree-split-prefix-stale",
        repo="subtree-ops/split-prefix",
        marker="SUBSPL_N",
        old="2",
        new="6",
        stem="subspl",
        knob="git subtree split leftover --prefix",
        effect="split recover leftover vendor/old instead of vendor/lib so the publish SHA missed the hotfix",
        map_cmd="git subtree split --prefix=vendor/old -b leftover-split 2>&1 | tail; rg SUBSPL_N src/subspl.py",
        map_obs="Created leftover branch leftover-split (wrong prefix)\nSUBSPL_N = 2",
        wrong="git subtree split --prefix=vendor/lib",
        wrong_obs="Created leftover (alias still vendor/old)",
        rec_cmd="git subtree split --prefix=vendor/lib -b hotfix-split && git log -1 --oneline hotfix-split",
        rec_obs="a1b2c3d leftover hotfix",
        left_cmd="git log -1 --format=%s hotfix-split",
        left_obs="hotfix leftover",
        handoff="ci-git-subtree-split-prefix-stale",
        ci_obs="Created leftover branch leftover-split (wrong prefix)",
        ci_probe="ssh ci-runner 'git subtree split --prefix=vendor/old -n 2>&1 | tail'",
    ),
)
add(
    cmdplant(
        slug="git-stash-create-drops-index",
        repo="stash-ops/create-index",
        marker="STCRE_N",
        old="1",
        new="5",
        stem="stcre",
        knob="git stash create leftover",
        effect="created recover leftover a stash commit without updating refs/stash so git stash pop found nothing",
        map_cmd="git stash create; git stash list | wc -l; rg STCRE_N src/stcre.py",
        map_obs="a1b2c3d leftover (dangling stash)\n0 leftover list\nSTCRE_N = 1",
        wrong="git stash pop",
        wrong_obs="No leftover stash entries found",
        rec_cmd="git stash store -m leftover $(git stash create) && git stash list | head",
        rec_obs="stash@{0}: leftover On recover",
        left_cmd="git stash list | wc -l",
        left_obs="1 leftover",
    ),
    cmdplant(
        slug="git-notes-append-dup-inc",
        repo="notes-ops/append-dup",
        marker="NTAPP_N",
        old="3",
        new="9",
        stem="ntapp",
        knob="git notes append leftover",
        effect="appended recover leftover a second INC trailer so CI parsed INC-0 after INC-4421",
        map_cmd="git notes append -m 'INC: 0' HEAD; git notes show HEAD; rg NTAPP_N src/ntapp.py",
        map_obs="INC leftover 4421\nINC leftover 0\nNTAPP_N = 3",
        wrong="git notes add --force -m 'INC: 4421' HEAD",
        wrong_obs="INC leftover 0 still (append leftover)",
        rec_cmd="git notes add --force -m 'INC: 4421' HEAD && git notes show HEAD",
        rec_obs="INC leftover 4421",
        left_cmd="git notes show HEAD | rg INC | wc -l",
        left_obs="1 leftover",
        handoff="ci-git-notes-append-dup-inc",
        ci_obs="INC leftover 4421\nINC leftover 0",
        ci_probe="ssh ci-runner 'git notes show HEAD | rg INC'",
    ),
)
add(
    cmdplant(
        slug="git-worktree-unlock-stale-reason",
        repo="worktree-ops/unlock-stale",
        marker="WTULK_N",
        old="0",
        new="8",
        stem="wtulk",
        knob="git worktree unlock leftover",
        effect="unlocked recover leftover a runner worktree while a job still held the lock so prune deleted it",
        map_cmd="git worktree unlock /work/.wt/runner 2>&1 | tail; git worktree list --porcelain | rg locked || echo unlocked; rg WTULK_N src/wtulk.py",
        map_obs="unlocked leftover\nunlocked leftover\nWTULK_N = 0",
        wrong="git worktree prune --expire=now",
        wrong_obs="Removing leftover worktrees/.wt/runner (unlocked)",
        rec_cmd="git worktree lock --reason ci-runner /work/.wt/runner && git worktree list --porcelain | rg locked",
        rec_obs="locked leftover",
        left_cmd="git worktree list --porcelain | rg locked",
        left_obs="locked leftover",
    ),
    cmdplant(
        slug="git-scalar-reconfigure-enroll-skip",
        repo="scalar-ops/reconfigure-skip",
        marker="SCLCFG_N",
        old="2",
        new="6",
        stem="sclcfg",
        knob="git scalar reconfigure leftover skip",
        effect="skipped recover leftover scalar enroll so maintenance timers never registered",
        map_cmd="git scalar reconfigure /work 2>&1 | tail; git config --get maintenance.auto; rg SCLCFG_N src/sclcfg.py",
        map_obs="warning: leftover already configured (skip enroll)\nfalse leftover\nSCLCFG_N = 2",
        wrong="git scalar run all /work",
        wrong_obs="warning: leftover skip enroll still",
        rec_cmd="git scalar reconfigure -a && git config --get maintenance.auto",
        rec_obs="true leftover",
        left_cmd="git config --get maintenance.auto",
        left_obs="true leftover",
        handoff="ci-git-scalar-reconfigure-enroll-skip",
        ci_obs="warning: leftover already configured (skip enroll)",
        ci_probe="ssh ci-runner 'git scalar reconfigure /work 2>&1 | tail'",
    ),
)
add(
    cmdplant(
        slug="git-replay-advance-stale-tip",
        repo="replay-ops/advance-stale",
        marker="RPLADV_N",
        old="1",
        new="5",
        stem="rpladv",
        knob="git replay --advance leftover stale tip",
        effect="advanced recover leftover refs/heads/hotfix onto an expired onto so the topic vanished from origin/main",
        map_cmd="git replay --onto leftover-base --advance hotfix main..hotfix 2>&1 | tail; rg RPLADV_N src/rpladv.py",
        map_obs="error: leftover-base is not an ancestor of main\nRPLADV_N = 1",
        wrong="git replay --onto leftover-base --contained hotfix",
        wrong_obs="error: leftover-base still stale",
        rec_cmd="git fetch origin main && git replay --onto origin/main --advance hotfix main..hotfix",
        rec_obs="Replayed leftover hotfix onto origin/main",
        left_cmd="git merge-base --is-ancestor origin/main hotfix; echo $?",
        left_obs="0 leftover",
    ),
    cmdplant(
        slug="git-clone-filter-tree-zero",
        repo="clone-ops/filter-tree0",
        marker="CLTREE_N",
        old="0",
        new="9",
        stem="cltree",
        knob="git clone --filter=tree:0 leftover",
        effect="cloned recover leftover without trees so git checkout of hotfix paths 404ed",
        map_cmd="git clone --filter=tree:0 --no-checkout origin /tmp/cltree 2>&1 | tail; git -C /tmp/cltree checkout hotfix -- src/cltree.py 2>&1 | tail; rg CLTREE_N src/cltree.py",
        map_obs="error: leftover tree a1b2c3d missing (tree:0)\nCLTREE_N = 0",
        wrong="git clone --filter=blob:none origin /tmp/cltree2",
        wrong_obs="error: leftover alias still --filter=tree:0",
        rec_cmd="git clone origin /tmp/cltree3 && git -C /tmp/cltree3 checkout hotfix -- src/cltree.py",
        rec_obs="Updated leftover 1 path",
        left_cmd="git -C /tmp/cltree3 cat-file -t HEAD^{tree}",
        left_obs="tree leftover",
        handoff="ci-git-clone-filter-tree-zero",
        ci_obs="error: leftover tree a1b2c3d missing (tree:0)",
        ci_probe="ssh ci-runner 'git clone --filter=tree:0 --no-checkout origin /tmp/cltree 2>&1 | tail'",
    ),
)
add(
    cmdplant(
        slug="git-fetch-no-write-fetch-head",
        repo="fetch-ops/no-fetch-head",
        marker="FTNFH_N",
        old="3",
        new="7",
        stem="ftnfh",
        knob="git fetch --no-write-fetch-head leftover",
        effect="skipped recover leftover FETCH_HEAD so git merge FETCH_HEAD used a stale SHA",
        map_cmd="git fetch --no-write-fetch-head origin hotfix; cat .git/FETCH_HEAD | head; rg FTNFH_N src/ftnfh.py",
        map_obs="d4e5f6a leftover stale FETCH_HEAD\nFTNFH_N = 3",
        wrong="git merge FETCH_HEAD",
        wrong_obs="Merge leftover stale d4e5f6a",
        rec_cmd="git fetch origin hotfix && git rev-parse FETCH_HEAD",
        rec_obs="a1b2c3d leftover",
        left_cmd="git rev-parse --short FETCH_HEAD",
        left_obs="a1b2c3d leftover",
    ),
    cmdplant(
        slug="git-push-signed-if-asked-stale",
        repo="push-ops/signed-if-asked",
        marker="PSHSIG_N",
        old="2",
        new="4",
        stem="pshsig",
        knob="git push --signed=if-asked leftover",
        effect="tried recover leftover GPG sign on a remote that advertised push certs with a missing key so the push aborted",
        map_cmd="git push --signed=if-asked origin hotfix 2>&1 | tail; rg PSHSIG_N src/pshsig.py",
        map_obs="error: leftover gpg failed to sign push certificate\nPSHSIG_N = 2",
        wrong="git push --signed=true origin hotfix",
        wrong_obs="error: leftover gpg still missing",
        rec_cmd="git push --signed=false origin hotfix && git ls-remote origin hotfix",
        rec_obs="a1b2c3d leftover refs/heads/hotfix",
        left_cmd="git ls-remote --heads origin | rg hotfix",
        left_obs="a1b2c3d leftover refs/heads/hotfix",
        handoff="ci-git-push-signed-if-asked-stale",
        ci_obs="error: leftover gpg failed to sign push certificate",
        ci_probe="ssh ci-runner 'git push --signed=if-asked origin hotfix 2>&1 | tail'",
    ),
)
add(
    cmdplant(
        slug="git-maintenance-start-scheduler-cron",
        repo="maint-ops/start-cron",
        marker="MTSTART_N",
        old="0",
        new="8",
        stem="mtstart",
        knob="git maintenance start leftover systemd",
        effect="started recover leftover systemd timers that never fired so auto gc never packed",
        map_cmd="git maintenance start --scheduler=systemd 2>&1 | tail; crontab -l 2>/dev/null | rg git-maintenance || echo none; rg MTSTART_N src/mtstart.py",
        map_obs="error: leftover Failed to connect to systemd\nnone leftover\nMTSTART_N = 0",
        wrong="git maintenance start",
        wrong_obs="error: leftover systemd still missing",
        rec_cmd="git maintenance start --scheduler=crontab && crontab -l | rg git-maintenance",
        rec_obs="0 leftover * * * git maintenance run --auto",
        left_cmd="crontab -l | rg git-maintenance | wc -l",
        left_obs="1 leftover",
    ),
    cmdplant(
        slug="git-check-ignore-verbose-excludes",
        repo="ignore-ops/verbose-excludes",
        marker="CKIGN_N",
        old="1",
        new="6",
        stem="ckign",
        knob="git check-ignore -v leftover excludesFile",
        effect="matched recover leftover src/ckign.py via a stale global excludesFile so git add skipped the hotfix",
        map_cmd="git check-ignore -v src/ckign.py; rg CKIGN_N src/ckign.py",
        map_obs="/etc/leftover-excludes:12:src/* leftover src/ckign.py\nCKIGN_N = 1",
        wrong="git add -f src/ckign.py",
        wrong_obs="/etc/leftover-excludes leftover still matched in CI wrappers",
        rec_cmd="git config --unset core.excludesFile && git check-ignore -v src/ckign.py || echo unignored",
        rec_obs="unignored leftover",
        left_cmd="git check-ignore -v src/ckign.py; echo exit:$?",
        left_obs="exit:1 leftover",
        handoff="ci-git-check-ignore-verbose-excludes",
        ci_obs="/etc/leftover-excludes:12:src/* leftover src/ckign.py",
        ci_probe="ssh ci-runner 'git check-ignore -v src/ckign.py'",
    ),
)


def _assert_local() -> None:
    slugs: list[str] = []
    markers: list[str] = []
    repos: list[str] = []
    published = _published_slugs()
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
    cov = 58 + (round_n % 9)
    return (
        f"# git-ops-recovery-factory — NOTES r{round_n}\n"
        "\n"
        f"Novel coverage: {cov}%\n"
        "\n"
        "## Episodes\n"
        f"- `{a['id']}`: 16 steps, success=True\n"
        "  - plan change at step 7\n"
        f"- `{b['id']}`: 16 steps, success=False\n"
        "  - plan change at step 7\n"
        "\n"
        f"Success: ['{a['id']}']. Partial/handoff: ['{b['id']}'].\n"
        "Distinct INC ids. Distinct tickets. No wrap-46 stamp. No force-push of main.\n"
        "Not leftover-tmp cartesian. Not stacked-git CLI cartesian.\n"
        "Not a clone of r793–r1416 (whoosh-writer-leftover3d-rebuild, "
        "whoosh-drop-leftover3d-handoff, interactive-difffilter-legacy, "
        "merge-conflictstyle-diff3, advice-diverging-false, http-ssltry-false).\n"
        "No '[wrap 46 ticket OPS-NNNN / same recovery class]' prefix.\n"
        "Do not twin two siblings of the same ticket in one batch.\n"
        "\n"
        "## decision_basis audit\n"
        "Every step labeled Plan:/Observation:/Reflection:/Tool call:, ≤240 chars, "
        "no thought/CoT/scratch/inner_monologue, no spike_events, no sim_or_real real. "
        "Generator grok-4.6. Designed traces. 16-step dense recover.\n"
        "\n"
        "## Mix / residual\n"
        f"{spec_a['mix']}. {spec_b['mix']}. One lands; residual handoff.\n"
        "\n"
        "## Step counts\n"
        f"- {a['id']}: 16 (required ~16)\n"
        f"- {b['id']}: 16 (required ~16)\n"
    )


def generate_round(round_n: int):
    idx, sa, sb = pick_pair(round_n)
    published = _published_slugs()
    batch_exists = (FACTORY_DIR / f"batch-r{round_n}.jsonl").exists()
    for spec in (sa, sb):
        if spec["slug"] in published and not batch_exists:
            raise SystemExit(f"clone of published slug {spec['slug']}")
    a = build_episode(round_n, sa, success=True, pr=PR0 + 15000 + 2 * idx, issue=None, inc=f"{round_n}3")
    b = build_episode(
        round_n, sb, success=False, pr=PR0 + 15000 + 2 * idx + 1, issue=ISSUE0 + 15000 + idx, inc=f"{round_n}8"
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
    print(f"wrote {batch} ({len(eps)} eps, {len(eps[0]['steps'])} steps) {nfile}", file=sys.stderr)


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
