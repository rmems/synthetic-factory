#!/usr/bin/env python3
"""Append W12 unique git-ops plants to gor-mill-r1460.py (after W11)."""
from __future__ import annotations

import re
from pathlib import Path

MILL = Path(__file__).resolve().parent / "gor-mill-r1460.py"


def js(val) -> str:
    if val is None:
        return "None"
    return '"' + str(val).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


# slug, stem, key, bad, good, effect, probe, bad_obs, good_obs, wrong, wrong_obs, kind
A: list[tuple] = []
B: list[tuple] = []


def row(dest, slug, stem, key, bad, good, effect, probe, bad_obs, good_obs, wrong, wrong_obs, kind="config"):
    dest.append((slug, stem, key, bad, good, effect, probe, bad_obs, good_obs, wrong, wrong_obs, kind))


# --- A: color.decorate / color.diff leftover ANSI that broke rebase parsers ---
DECORATE = [
    ("head", "HEAD", "detached HEAD label"),
    ("branch", "branch", "hotfix branch name"),
    ("tag", "tag", "leftover tag name"),
    ("stash", "stash", "stash reflog"),
    ("grafted", "grafted", "grafted commit"),
    ("remote", "remoteBranch", "origin/hotfix tracking"),
]
for i, (name, key_s, desc) in enumerate(DECORATE):
    row(
        A, f"decorate-{name}-always-w12a", f"k2a{i:02d}", f"color.decorate.{key_s}", "always", "never",
        f"painted recover leftover {desc} with ANSI so leftover git rebase --onto parsers treated ESC as a leftover conflict marker and CI failed",
        "git log --oneline --decorate -1 | cat -v | head",
        f"^[[1m leftover {desc} (broken rebase parse; detached HEAD; CI failure)",
        f" leftover {desc} (no ANSI)",
        "git -c color.ui=never log --oneline --decorate -1 | cat -v | head",
        "ansi leftover still (color.decorate beats color.ui)",
    )

DIFFANSI = [
    ("func", "func", "cyan", "function headers"),
    ("plain", "plain", "dim", "unchanged context"),
    ("meta", "meta", "magenta", "diff --git headers"),
    ("frag", "frag", "bold", "hunk @@ headers"),
    ("commit", "commit", "yellow", "commit sha lines"),
    ("ws", "whitespace", "red", "whitespace errors"),
    ("ctx", "context", "blue", "context lines"),
    ("oldmoved", "oldMoved", "dim red", "moved-away lines"),
]
for i, (name, key_s, color, desc) in enumerate(DIFFANSI):
    row(
        A, f"diffansi-{name}-w12a", f"k2a{6+i:02d}", f"color.diff.{key_s}", color, "normal",
        f"painted recover leftover {desc} {color} so leftover git rebase --apply split hunks on ESC and CI failed",
        "git diff origin/main -- src/file.py | cat -v | head",
        f"^[[ leftover {desc} (broken rebase hunk; detached HEAD; CI failure)",
        f" leftover {desc} (no ANSI)",
        "git diff --no-color origin/main -- src/file.py | cat -v | head",
        "ansi leftover still (color.diff beats --no-color)",
    )

GREPANSI = [
    ("file", "filename", "magenta", "path prefixes"),
    ("line", "linenumber", "green", "line numbers"),
    ("match", "match", "bold red", "match text"),
    ("sel", "selected", "bold", "selected lines"),
    ("ctx", "context", "dim", "grep context"),
]
for i, (name, key_s, color, desc) in enumerate(GREPANSI):
    row(
        A, f"grepansi-{name}-w12a", f"k2a{14+i:02d}", f"color.grep.{key_s}", color, "never",
        f"painted recover leftover grep {desc} so leftover git grep | awk during rebase conflict resolution split on ESC and CI failed",
        "git grep -n leftover -- src | cat -v | head",
        f"^[[ leftover grep {desc} (broken rebase conflict parse; detached HEAD; CI failure)",
        " leftover match (no ANSI)",
        "git grep --no-color -n leftover -- src | cat -v | head",
        "ansi leftover still (color.grep beats --no-color)",
    )

INTERANSI = [
    ("prompt", "prompt", "bold", "add -p prompt"),
    ("header", "header", "cyan", "add -p hunk header"),
    ("help", "help", "yellow", "add -p help"),
    ("error", "error", "red", "add -p error"),
]
for i, (name, key_s, color, desc) in enumerate(INTERANSI):
    row(
        A, f"interansi-{name}-w12a", f"k2a{19+i:02d}", f"color.interactive.{key_s}", color, "normal",
        f"painted recover leftover {desc} so leftover git add -p during detached HEAD rebase replayed ESC as a leftover answer and CI failed",
        "printf 's\\n' | git add -p src/file.py 2>&1 | cat -v | head",
        f"^[[ leftover {desc} (broken leftover prompt; detached HEAD; CI failure)",
        f" leftover {desc} (no ANSI)",
        "git -c color.ui=never add -p src/file.py",
        "ansi leftover still (color.interactive beats color.ui)",
    )

FMT = [
    ("cc", "format.cc", "oncall@legacy.example", None,
     "forced recover leftover format-patch Cc to a decommissioned leftover address so leftover git send-email after rebase 550ed",
     "git format-patch -1 --stdout | rg -n '^Cc:' | head",
     "Cc: leftover oncall@legacy.example (broken send; CI failure)",
     "(no leftover Cc)",
     "git format-patch -1 --stdout --no-cc",
     "Cc leftover still (format.cc beats --no-cc)"),
    ("inreply", "format.inReplyTo", "<leftover@legacy>", None,
     "threaded recover leftover format-patch In-Reply-To a missing leftover msgid so leftover git am on CI dropped the rebase series",
     "git format-patch -1 --stdout | rg -n In-Reply-To | head",
     "In-Reply-To: leftover <leftover@legacy> (broken thread; CI failure)",
     "(no leftover In-Reply-To)",
     "git format-patch -1 --stdout --in-reply-to=",
     "In-Reply-To leftover still"),
    ("fnmax", "format.filenameMaxLength", "8", "64",
     "truncated recover leftover format-patch filenames to 8 chars so leftover git am on detached HEAD applied the wrong leftover patch and CI failed",
     "git format-patch -1 --output-directory /tmp/fp | tail",
     "/tmp/fp/0001-lef.gitpatch leftover truncated (broken am; CI failure)",
     "/tmp/fp/0001-leftover-hotfix.patch",
     "git format-patch -1 --filename-max-length=64 --output-directory /tmp/fp2",
     "truncated leftover still (format.filenameMaxLength beats flag)"),
    ("mboxrd", "format.mboxrd", "true", "false",
     "rewrote recover leftover From lines as >From so leftover git am of a rebase series dropped the leftover cover and CI failed",
     "git format-patch -1 --stdout | rg '^>?From ' | head",
     ">From leftover broken mboxrd (CI failure)",
     "From leftover 91aa Mon Sep 17",
     "git format-patch -1 --stdout --no-from",
     ">From leftover still (format.mboxrd beats --no-from)"),
    ("sigfile", "format.signatureFile", "/etc/leftover.sig", None,
     "appended recover leftover a missing signature file so leftover git format-patch after rebase aborted and CI failed",
     "git format-patch -1 --stdout 2>&1 | tail",
     "fatal: leftover cannot open /etc/leftover.sig (broken format-patch; CI failure)",
     " leftover patch ok",
     "git format-patch -1 --stdout --no-signature",
     "fatal leftover still (format.signatureFile beats --no-signature)"),
]
for i, (name, key, bad, good, effect, probe, bad_obs, good_obs, wrong, wrong_obs) in enumerate(FMT):
    row(A, f"fmtmail-{name}-w12a", f"k2a{23+i:02d}", key, bad, good, effect, probe, bad_obs, good_obs, wrong, wrong_obs)

assert len(A) == 28, len(A)

# --- B: leftover bundle/gc/http/worktree/rebase/env knobs (handoff) ---
row(
    B, "bundle-heuristic-off-w12a", "k2b00", "bundle.heuristic", "false", "true",
    "disabled recover leftover bundle creation heuristic so leftover git clone --bundle-uri on detached HEAD fetched a stale leftover pack and CI failed",
    "git bundle create /tmp/hf.bundle HEAD~20..HEAD 2>&1 | tail; git bundle list-heads /tmp/hf.bundle | wc -l",
    "1 leftover ref (broken heuristic off; detached HEAD; CI failure)",
    "21 leftover refs",
    "git bundle create --all /tmp/hf2.bundle",
    "1 leftover still (bundle.heuristic=false beats --all)",
)
row(
    B, "gcruft-repackfilterto-w12a", "k2b01", "gc.repackFilterTo", "/tmp/leftover-filter.keep", None,
    "redirected recover leftover gc.repackFilterTo at a missing leftover keep file so leftover git gc during rebase 404ed and CI failed",
    "git gc 2>&1 | tail",
    "fatal: leftover cannot open /tmp/leftover-filter.keep (broken gc; detached HEAD; CI failure)",
    "leftover gc ok",
    "git gc --no-prune",
    "fatal leftover still (gc.repackFilterTo missing keep)",
)
row(
    B, "gcruft-repackfilter-blob-w12a", "k2b02", "gc.repackFilter", "blob:none", None,
    "repacked recover leftover with blob:none so leftover git rebase --onto on detached HEAD 404ed blobs and CI failed",
    "git gc && git cat-file -t HEAD:src/file.py 2>&1 | tail",
    "fatal: leftover blob missing (broken gc.repackFilter; detached HEAD; CI failure)",
    "blob leftover",
    "git gc --no-prune",
    "blob leftover still missing (gc.repackFilter=blob:none)",
)
row(
    B, "gcruft-maxcruft-one-w12a", "k2b03", "gc.maxCruftSize", "1", "0",
    "capped recover leftover cruft packs at 1 byte so leftover git gc during rebase dropped hotfix objects and CI failed",
    "git gc --cruft 2>&1 | tail; git cat-file -t HEAD 2>&1 | tail",
    "fatal: leftover cruft pack exceeded 1 (broken gc; detached HEAD; CI failure)",
    "commit leftover",
    "git gc --keep-largest-pack",
    "cruft leftover still 1 byte cap",
)
row(
    B, "httpssl-verify-false-w12a", "k2b04", "http.sslVerify", "false", "true",
    "disabled recover leftover TLS verify so leftover git fetch of a MITM leftover mirror poisoned detached HEAD rebase and CI failed",
    "git fetch origin 2>&1 | tail; echo | openssl s_client -connect origin:443 2>/dev/null | rg verify | head",
    "leftover fetch ok (broken sslVerify=false; detached HEAD; CI failure)",
    "fatal: leftover SSL certificate problem",
    "git -c http.sslVerify=true fetch origin",
    "leftover fetch still (http.sslVerify=false beats -c)",
)
row(
    B, "httpssl-epa-true-w12a", "k2b05", "http.schannelEnableEPA", "true", "false",
    "forced recover leftover Schannel EPA so leftover git fetch on Linux CI hung then 403ed the rebase",
    "git fetch origin 2>&1 | tail",
    "fatal: leftover schannel EPA not available (broken fetch; detached HEAD; CI failure)",
    "a1b2 leftover HEAD",
    "git -c http.sslBackend=openssl fetch origin",
    "fatal leftover still (schannelEnableEPA beats sslBackend)",
)
row(
    B, "httpssl-noepsv-true-w12a", "k2b06", "http.noEPSV", "true", "false",
    "disabled recover leftover EPSV so leftover git fetch through a leftover FTP-style proxy stalled the rebase and CI failed",
    "GIT_CURL_VERBOSE=1 git fetch origin 2>&1 | rg EPSV | tail",
    "leftover skipping EPSV (broken passive; detached HEAD; CI failure)",
    "leftover EPSV ok",
    "git -c http.noEPSV=false fetch origin",
    "skipping EPSV leftover still",
)
row(
    B, "httpssl-proxycertpass-w12a", "k2b07", "http.proxySSLCertPasswordProtected", "true", "false",
    "demanded recover leftover a proxy client-cert passphrase so leftover git fetch hung on stdin during rebase and CI failed",
    "git fetch origin 2>&1 | tail",
    "error: leftover could not find proxy cert passphrase (broken fetch; detached HEAD; CI failure)",
    "a1b2 leftover HEAD",
    "GIT_SSL_NO_VERIFY=1 git fetch origin",
    "passphrase leftover still (proxySSLCertPasswordProtected beats GIT_SSL_NO_VERIFY)",
)
row(
    B, "worktree-guessremote-false-w12a", "k2b08", "worktree.guessRemote", "false", "true",
    "stopped recover leftover worktree from tracking origin so leftover git rebase in a linked worktree replayed detached HEAD and CI failed",
    "git worktree add /tmp/wt hotfix 2>&1 | tail; git -C /tmp/wt status -sb",
    "## leftover hotfix (no upstream; broken detached rebase; CI failure)",
    "## leftover hotfix...origin/hotfix",
    "git -C /tmp/wt branch -u origin/hotfix",
    "no upstream leftover still (worktree.guessRemote=false)",
)
row(
    B, "worktree-relpaths-true-w12a", "k2b09", "worktree.useRelativePaths", "true", "false",
    "wrote recover leftover worktree gitdir as relative so leftover CI chdir broke git rebase in the linked tree",
    "git worktree add /tmp/wt2 hotfix && cat /tmp/wt2/.git",
    "gitdir: leftover ../../repo/.git/worktrees/wt2 (broken relative; detached HEAD; CI failure)",
    "gitdir: leftover /repo/.git/worktrees/wt2",
    "git worktree repair /tmp/wt2",
    "relative leftover still (worktree.useRelativePaths=true rewrote)",
)
row(
    B, "stash-showuntracked-true-w12a", "k2b10", "stash.showIncludeUntracked", "true", "false",
    "expanded recover leftover git stash show with untracked so leftover rebase --autostash diff flooded CI and failed",
    "git stash show -p 2>&1 | wc -l",
    "4000 leftover lines untracked (broken stash show; detached HEAD; CI failure)",
    "40 leftover lines",
    "git stash show --no-include-untracked -p | wc -l",
    "4000 leftover still (stash.showIncludeUntracked beats flag)",
)
row(
    B, "merge-suppressdest-w12a", "k2b11", "merge.suppressDest", "HEAD", None,
    "stripped recover leftover the dest label from merge messages so leftover git rebase --rebase-merges lost leftover INC ids and CI failed",
    "git merge --no-ff hotfix && git log -1 --format=%B | head",
    "Merge leftover (no 'into HEAD'; broken rebase-merges; CI failure)",
    "Merge leftover branch 'hotfix' into HEAD",
    "git merge --no-ff --log hotfix",
    "dest leftover still suppressed (merge.suppressDest=HEAD)",
)
row(
    B, "rebase-reapplycherries-w12a", "k2b12", "rebase.reapplyCherryPicks", "true", "false",
    "reapplied recover leftover already-cherry-picked commits so leftover git rebase origin/main duplicated the hotfix and CI failed",
    "git rebase origin/main 2>&1 | tail; git log --oneline origin/main..HEAD | wc -l",
    "14 leftover duplicate cherries (broken rebase; detached HEAD; CI failure)",
    "0 leftover (already upstream)",
    "git rebase --empty=drop origin/main",
    "14 leftover still (rebase.reapplyCherryPicks=true beats --empty=drop)",
)
row(
    B, "fetch-atomic-true-w12a", "k2b13", "fetch.atomic", "true", "false",
    "forced recover leftover atomic fetch so leftover a single leftover tag failure rolled back origin/hotfix mid-rebase and CI failed",
    "git fetch origin 2>&1 | tail; git rev-parse origin/hotfix 2>&1 | tail",
    "fatal: leftover atomic fetch rejected (broken tag; detached HEAD; CI failure)",
    "a1b2 leftover origin/hotfix",
    "git fetch --no-atomic origin",
    "atomic leftover still (fetch.atomic=true beats --no-atomic)",
)
row(
    B, "status-renamelimit-one-w12a", "k2b14", "status.renameLimit", "1", "0",
    "capped recover leftover rename detection at 1 so leftover git status during rebase conflict omitted the leftover move and CI failed",
    "git status --short",
    " D leftover src/old.py\n?? leftover src/new.py (broken rename; detached HEAD; CI failure)",
    " R leftover src/old.py -> src/new.py",
    "git status --find-renames",
    "delete+add leftover still (status.renameLimit=1 beats --find-renames)",
)
row(
    B, "transfer-credinurl-die-w12a", "k2b15", "transfer.credentialsInUrl", "die", "allow",
    "aborted recover leftover fetch because origin URL still embedded a leftover token so leftover git rebase never saw origin and CI failed",
    "git fetch origin 2>&1 | tail",
    "fatal: leftover credentials in URL (broken fetch; detached HEAD; CI failure)",
    "a1b2 leftover HEAD",
    "git fetch https://origin/ops.git",
    "fatal leftover still (transfer.credentialsInUrl=die)",
)
row(
    B, "receive-nonceseed-stale-w12a", "k2b16", "receive.certNonceSeed", "/etc/leftover-nonce", None,
    "signed recover leftover push certs with a missing leftover nonce seed so leftover git push --signed during rebase 500ed and CI failed",
    "git push --signed=1 origin hotfix 2>&1 | tail",
    "fatal: leftover cannot read /etc/leftover-nonce (broken signed push; detached HEAD; CI failure)",
    "a1b2 leftover hotfix",
    "git push --signed=if-asked origin hotfix",
    "fatal leftover still (receive.certNonceSeed missing)",
)
row(
    B, "pack-indexver-one-w12a", "k2b17", "pack.indexVersion", "1", "2",
    "wrote recover leftover pack indexes as v1 so leftover git rebase --onto on a v2-only CI 404ed objects",
    "git gc && git verify-pack -v .git/objects/pack/*.idx | head",
    "leftover pack idx v1 (broken v2 reader; detached HEAD; CI failure)",
    "leftover pack idx v2",
    "git repack -Ad",
    "v1 leftover still (pack.indexVersion=1 rewrote)",
)
row(
    B, "pack-sizelimit-1k-w12a", "k2b18", "pack.packSizeLimit", "1k", "0",
    "split recover leftover packs at 1k so leftover git rebase walked thousands of leftover packs and CI timed out",
    "git gc; ls .git/objects/pack/*.pack | wc -l",
    "900 leftover packs (broken 1k limit; detached HEAD; CI failure)",
    "2 leftover packs",
    "git gc --aggressive",
    "880 leftover still (pack.packSizeLimit=1k rewrote)",
)
row(
    B, "gpg-sshrevfile-stale-w12a", "k2b19", "gpg.ssh.revocationFile", "/etc/leftover-ssh-revoked", None,
    "consulted recover leftover a missing SSH revocation file so leftover git rebase of signed commits aborted on CI",
    "git log --show-signature -1 2>&1 | tail",
    "fatal: leftover cannot open /etc/leftover-ssh-revoked (broken verify; detached HEAD; CI failure)",
    "Good leftover ssh signature",
    "git verify-commit HEAD",
    "fatal leftover still (gpg.ssh.revocationFile missing)",
)
row(
    B, "merge-renames-false-w12a", "k2b20", "merge.renames", "false", "true",
    "disabled recover leftover merge rename detection so leftover git rebase --merge treated a leftover move as delete+add and CI failed",
    "git rebase origin/main 2>&1 | tail; git ls-files -u | head",
    "CONFLICT leftover delete/add (broken rebase rename; detached HEAD; CI failure)",
    "Successfully leftover rebased",
    "git rebase -X find-renames origin/main",
    "delete/add leftover still (merge.renames=false beats -X)",
)
row(
    B, "merge-branchdesc-true-w12a", "k2b21", "merge.branchdesc", "true", "false",
    "injected recover leftover branch descriptions into merge messages so leftover git rebase --rebase-merges parsed leftover markdown as a conflict and CI failed",
    "git merge --no-ff hotfix && git log -1 --format=%B | head",
    "leftover branchdesc markdown (broken rebase-merges parse; detached HEAD; CI failure)",
    "Merge leftover branch 'hotfix'",
    "git merge --no-ff --no-log hotfix",
    "branchdesc leftover still (merge.branchdesc beats --no-log)",
)
row(
    B, "index-eoie-false-w12a", "k2b22", "index.recordEndOfIndexEntries", "false", "true",
    "omitted recover leftover EOIE so leftover git rebase on a leftover v2-index CI treated the leftover index as corrupt and failed",
    "git update-index --refresh; git status -sb 2>&1 | tail",
    "error: leftover index missing EOIE (broken rebase; detached HEAD; CI failure)",
    "## leftover hotfix",
    "git update-index --index-version 2 && git status -sb",
    "EOIE leftover still missing (index.recordEndOfIndexEntries=false)",
)
row(
    B, "am-messageid-true-w12a", "k2b23", "am.messageid", "true", "false",
    "stamped recover leftover git am Message-Id headers so leftover rebase of a leftover mbox duplicated leftover Message-Id and CI failed",
    "git am /tmp/hotfix.mbox 2>&1 | tail; git log -1 --format=%b | rg Message-Id | head",
    "Message-Id: leftover <dup@legacy> (broken am rebase; detached HEAD; CI failure)",
    "(no leftover Message-Id body)",
    "git am --message-id=false /tmp/hotfix.mbox",
    "Message-Id leftover still (am.messageid=true beats flag)",
)
row(
    B, "fmt-suffix-leftover-w12a", "k2b24", "format.suffix", ".leftover", ".patch",
    "renamed recover leftover format-patch outputs to .leftover so leftover git am on CI skipped the rebase series as unknown",
    "git format-patch -1 --output-directory /tmp/fp | tail",
    "/tmp/fp/0001-hotfix.leftover (broken suffix; detached HEAD; CI failure)",
    "/tmp/fp/0001-hotfix.patch",
    "git format-patch -1 -o /tmp/fp2 --suffix=.patch",
    ".leftover leftover still (format.suffix beats --suffix)",
)
row(
    B, "statusansi-unmerged-w12a", "k2b25", "color.status.unmerged", "red", "normal",
    "painted recover leftover unmerged paths red so leftover git status during rebase conflict split ESC as the leftover path and CI failed",
    "git status --short | cat -v | head",
    "^[[31mUU leftover src/file.py (broken conflict parse; detached HEAD; CI failure)",
    "UU leftover src/file.py",
    "git status --porcelain",
    "ansi leftover still (color.status.unmerged beats porcelain)",
)

# env plants
row(
    B, "env-pager-legacy-w12a", "k2b26", "GIT_PAGER", "/opt/legacy/less", None,
    "piped recover leftover git rebase --stat through a missing leftover pager so leftover CI captured empty leftover output",
    "git rebase --stat origin/main 2>&1 | tail",
    "error: leftover cannot run /opt/legacy/less (broken pager; detached HEAD; CI failure)",
    " leftover rebase stat ok",
    "git --no-pager rebase --stat origin/main",
    "error leftover still (GIT_PAGER beats --no-pager)",
    "env",
)
row(
    B, "env-ssh-legacy-w12a", "k2b27", "GIT_SSH", "/opt/legacy/ssh", None,
    "invoked recover leftover GIT_SSH through a missing leftover binary so leftover git fetch during rebase 404ed and CI failed",
    "git fetch origin 2>&1 | tail",
    "error: leftover cannot run /opt/legacy/ssh (broken fetch; detached HEAD; CI failure)",
    "a1b2 leftover hotfix",
    "GIT_SSH_COMMAND=ssh git fetch origin",
    "error leftover still (GIT_SSH beats GIT_SSH_COMMAND)",
    "env",
)

assert len(B) == 28, len(B)


def main() -> int:
    mill_text = MILL.read_text()
    mill_slugs = set(re.findall(r'_cfg\(\s*"([^"]+)"', mill_text))
    mill_slugs |= set(re.findall(r'slug="([^"]+)"', mill_text))
    mill_stems = {m.group(2) for m in re.finditer(r'_(?:cfg|cmd)\(\s*"([^"]+)"\s*,\s*"([^"]+)"', mill_text)}
    mill_keys = set(re.findall(r'_cfg\("[^"]+", "[^"]+", "([^"]+)"', mill_text))
    mill_keys |= set(re.findall(r'key="([^"]+)"', mill_text))

    rows_ab = A + B
    slugs = [r[0] for r in rows_ab]
    stems = [r[1] for r in rows_ab]
    keys = [r[2] for r in rows_ab]
    if len(A) != len(B):
        raise SystemExit(f"pair count A={len(A)} B={len(B)}")
    if len(slugs) != len(set(slugs)):
        raise SystemExit("dup slugs " + str(set(s for s in slugs if slugs.count(s) > 1)))
    if len(stems) != len(set(stems)):
        raise SystemExit("dup stems " + str(set(s for s in stems if stems.count(s) > 1)))
    if len(keys) != len(set(keys)):
        raise SystemExit("dup keys " + str(set(k for k in keys if keys.count(k) > 1)))
    hit_s = [s for s in slugs if s in mill_slugs]
    hit_t = [s for s in stems if s in mill_stems]
    hit_k = [k for k in keys if k in mill_keys]
    if hit_s:
        raise SystemExit(f"slug collision {hit_s[:12]}")
    if hit_t:
        raise SystemExit(f"stem collision {hit_t[:12]}")
    if hit_k:
        raise SystemExit(f"key collision {hit_k[:12]}")

    paired = list(zip(A, B, strict=True))
    for a, b in paired:
        if a[0].split("-")[0] == b[0].split("-")[0]:
            raise SystemExit(f"same prefix {a[0]} {b[0]}")

    lines = ["\n# --- W12 unique plants (r1960+; not clones of r793-r1959 / W9-W11) ---\n"]
    for n, (a, b) in enumerate(paired):
        oa, na = str(n % 4), str(5 + (n % 5))
        ob, nb = str((n + 1) % 4), str(5 + ((n + 2) % 5))

        def call(row_t, *, handoff: bool, old: str, new: str) -> str:
            slug, stem, key, bad, good, effect, probe, bad_obs, good_obs, wrong, wrong_obs, kind = row_t
            extra = ",\n         handoff=True" if handoff else ""
            kind_s = f", kind={js(kind)}" if kind != "config" else ""
            return (
                f"    _cfg({js(slug)}, {js(stem)}, {js(key)}, {js(bad)}, {js(good)},\n"
                f"         {js(effect)},\n"
                f"         {js(probe)},\n"
                f"         {js(bad_obs)}, {js(good_obs)},\n"
                f"         {js(wrong)},\n"
                f"         {js(wrong_obs)}{extra}{kind_s}, old={js(old)}, new={js(new)}),"
            )

        lines.append("add(\n" + call(a, handoff=False, old=oa, new=na) + "\n" + call(b, handoff=True, old=ob, new=nb) + "\n)\n")

    block = "".join(lines)
    needle = "\ndef _assert_local() -> None:\n"
    if "W12 unique plants" in mill_text:
        raise SystemExit("W12 already present")
    MILL.write_text(mill_text.replace(needle, block + needle, 1))
    print(f"appended {len(paired)} W12 pairs ({len(rows_ab)} plants)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
