#!/usr/bin/env python3
"""Append W10 unique git-ops plants to gor-mill-r1460.py (after W9)."""
from __future__ import annotations

import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
MILL = HERE / "gor-mill-r1460.py"

# Compact missing-binary / rewrite plants. good is None (unset recover).
# slug, stem, key, bad, effect, probe, bad_obs, good_obs, wrong, wrong_obs
MISSING: list[tuple] = []


def m(slug, stem, key, bad, effect, probe, bad_obs, good_obs, wrong, wrong_obs):
    MISSING.append((slug, stem, key, bad, effect, probe, bad_obs, good_obs, wrong, wrong_obs))


# --- aliases (missing wrappers) ---
for i, (cmd, desc) in enumerate([
    ("br", "branch listing"), ("ci", "commit wrapper"), ("df", "diff wrapper"),
    ("lola", "log graph"), ("undo", "reset wrapper"), ("recent", "reflog wrapper"),
    ("sw", "switch wrapper"), ("pu", "push wrapper"), ("pl", "pull wrapper"),
    ("stsh", "stash wrapper"), ("rb", "rebase wrapper"), ("mg", "merge wrapper"),
    ("tg", "tag wrapper"), ("ft", "fetch wrapper"), ("cl", "clone wrapper"),
    ("wt", "worktree wrapper"), ("sm", "submodule wrapper"), ("bl", "blame wrapper"),
    ("gr", "grep wrapper"), ("pk", "cherry-pick wrapper"),
]):
    m(f"alias-{cmd}-stale-w10a", f"h9a{i:02d}", f"alias.{cmd}", f"!/opt/legacy/{cmd}.sh",
      f"aliased recover leftover git {cmd} ({desc}) to a missing wrapper so leftover CI git {cmd} 404ed",
      f"git {cmd} 2>&1 | tail", f"error: leftover cannot run /opt/legacy/{cmd}.sh",
      f"leftover {cmd} ok", f"git {cmd}", "error leftover still")

# --- url insteadOf / pushInsteadOf ---
for i, (host, scheme, kind) in enumerate([
    ("retired-gitlab", "https", "insteadOf"), ("retired-github", "ssh", "insteadOf"),
    ("retired-gerrit", "git", "insteadOf"), ("legacy-bitbucket", "https", "pushInsteadOf"),
    ("legacy-azure", "ssh", "pushInsteadOf"), ("legacy-sourcehut", "https", "insteadOf"),
    ("legacy-codecommit", "https", "pushInsteadOf"), ("legacy-phab", "http", "insteadOf"),
    ("legacy-radicle", "https", "insteadOf"), ("legacy-tangled", "ssh", "pushInsteadOf"),
]):
    key = f"url.{scheme}://{host}/.{kind}"
    bad = "ssh://origin/" if kind == "pushInsteadOf" else "https://origin/"
    probe = "git push origin hotfix 2>&1 | tail" if kind == "pushInsteadOf" else "git fetch origin 2>&1 | tail"
    m(f"url-{host.replace('-', '')}-{kind.lower()}-w10a", f"h9b{i:02d}", key, bad,
      f"rewrote recover leftover {kind} through decommissioned {host} so leftover git never reached origin",
      probe, f"fatal: leftover unable to connect to {host}", "a1b2 leftover hotfix",
      "git fetch origin" if kind != "pushInsteadOf" else "git push ssh://origin/ hotfix",
      "fatal leftover still")

# --- includeIf ---
for i, (cond, path) in enumerate([
    ("onbranch:hotfix", "/etc/leftover-hotfix.gitconfig"),
    ("onbranch:main", "/etc/leftover-main.gitconfig"),
    ("gitdir:/srv/legacy/", "/etc/leftover-legacy.gitconfig"),
    ("gitdir:/opt/retired/", "/etc/leftover-retired.gitconfig"),
    ("gitdir:**/monorepo/", "/etc/leftover-mono.gitconfig"),
    ("hasconfig:remote.origin.url:git@legacy:**", "/etc/leftover-origin.gitconfig"),
    ("hasconfig:remote.origin.url:https://legacy/**", "/etc/leftover-https.gitconfig"),
    ("gitdir:/home/runner/work/", "/etc/leftover-runner.gitconfig"),
    ("onbranch:recover/**", "/etc/leftover-recover.gitconfig"),
    ("gitdir:/tmp/leftover-wt/", "/etc/leftover-wt.gitconfig"),
]):
    m(f"includeif-{cond.split(':')[0]}-{i}-w10a", f"h9c{i:02d}",
      f"includeIf.{cond}.path", path,
      f"included recover leftover {cond} config from missing {path} so leftover git config --get user.email died",
      "git config --get user.email 2>&1 | tail",
      f"fatal: leftover cannot include {path}", "oncall@ex leftover",
      "git -c include.path=/dev/null config --get user.email", "fatal leftover still")

# --- filter helpers ---
for i, name in enumerate([
    "keyword", "openssl", "gpgcrypt", "rot13", "dos2unix", "swiftlint", "clangfmt",
    "blackfmt", "prettier", "terraform", "ansible", "helm", "cuefmt", "nixfmt",
    "shfmt", "rustfmt", "gofmt", "javafmt", "sqlfmt", "protofmt",
]):
    m(f"filter-{name}-clean-w10a", f"h9d{i:02d}", f"filter.{name}.clean", f"/opt/legacy/{name}-clean",
      f"ran recover leftover {name} clean through a missing helper so leftover git add of src/h9d{i:02d}.py 404ed",
      f"git add src/h9d{i:02d}.py 2>&1 | tail",
      f"error: leftover cannot run /opt/legacy/{name}-clean", f"src/h9d{i:02d}.py leftover | 2 +-",
      f"git add --renormalize src/h9d{i:02d}.py", "error leftover still")

# --- mergetool / difftool / browser / pager paths ---
for i, (slug, key, path, verb, probe, good) in enumerate([
    ("mergetool-vimdiff-stale-w10a", "mergetool.vimdiff.path", "/opt/legacy/vimdiff", "mergetool vimdiff",
     "git mergetool --tool=vimdiff --no-prompt 2>&1 | tail", "leftover merged src/file.py"),
    ("mergetool-nvim-stale-w10a", "mergetool.nvim.path", "/opt/legacy/nvim", "mergetool nvim",
     "git mergetool --tool=nvim --no-prompt 2>&1 | tail", "leftover merged src/file.py"),
    ("mergetool-code-stale-w10a", "mergetool.vscode.path", "/opt/legacy/code", "mergetool vscode",
     "git mergetool --tool=vscode --no-prompt 2>&1 | tail", "leftover merged src/file.py"),
    ("mergetool-kdiff-stale-w10a", "mergetool.kdiff3.path", "/opt/legacy/kdiff3", "mergetool kdiff3",
     "git mergetool --tool=kdiff3 --no-prompt 2>&1 | tail", "leftover merged src/file.py"),
    ("difftool-bc-stale-w10a", "difftool.bc.path", "/opt/legacy/bcomp", "difftool beyondcompare",
     "git difftool --tool=bc --no-prompt HEAD -- src/file.py 2>&1 | tail", "leftover textual diff"),
    ("difftool-opendiff-stale-w10a", "difftool.opendiff.path", "/opt/legacy/opendiff", "difftool opendiff",
     "git difftool --tool=opendiff --no-prompt HEAD -- src/file.py 2>&1 | tail", "leftover textual diff"),
    ("browser-lynx-stale-w10a", "browser.lynx.path", "/opt/legacy/lynx", "web--browse lynx",
     "git web--browse --browser=lynx HEAD 2>&1 | tail", "leftover opened"),
    ("browser-chrome-stale-w10a", "browser.google-chrome.path", "/opt/legacy/chrome", "web--browse chrome",
     "git web--browse --browser=google-chrome HEAD 2>&1 | tail", "leftover opened"),
    ("pager-less-stale-w10a", "core.pager", "/opt/legacy/less", "core.pager less",
     "git log -1 --oneline 2>&1 | tail", "a1b2 leftover recover"),
    ("man-konqueror-stale-w10a", "man.konqueror.path", "/opt/legacy/konqueror", "man konqueror",
     "git help --web status 2>&1 | tail", "leftover opened"),
]):
    m(slug, f"h9e{i:02d}", key, path,
      f"launched recover leftover {verb} through missing {path} so leftover CI {verb} 404ed",
      probe, f"error: leftover cannot run {path}", good, probe.split(" 2")[0], "error leftover still")

# --- remote.* unique remotes ---
for i, (name, key, bad, effect, probe, bad_obs, good_obs, wrong) in enumerate([
    ("legacy", "remote.legacy.proxy", "http://legacy-proxy:8080",
     "routed recover leftover remote legacy through a decommissioned proxy so leftover fetch hung then 504ed",
     "git fetch legacy 2>&1 | tail", "fatal: leftover unable to access proxy legacy-proxy:8080",
     "a1b2 leftover HEAD", "git fetch origin"),
    ("mirror", "remote.mirror.url", "git://legacy-mirror/ops.git",
     "pointed recover leftover remote mirror at a decommissioned git:// URL so leftover git fetch mirror 404ed",
     "git fetch mirror 2>&1 | tail", "fatal: leftover unable to connect to legacy-mirror",
     "a1b2 leftover HEAD", "git fetch origin"),
    ("upstream", "remote.upstream.vcs", "legacy-hg",
     "invoked recover leftover a missing helper for upstream so leftover git fetch died looking for git-remote-legacy-hg",
     "git fetch upstream 2>&1 | tail", "error: leftover cannot run git-remote-legacy-hg",
     "a1b2 leftover HEAD", "git fetch origin"),
    ("fork", "remote.fork.pushurl", "ssh://legacy-fork/ops.git",
     "pushed recover leftover fork to a decommissioned pushurl so leftover git push fork 404ed",
     "git push fork hotfix 2>&1 | tail", "fatal: leftover could not read from remote legacy-fork",
     "a1b2 leftover hotfix", "git push origin hotfix"),
    ("vendor", "remote.vendor.fetch", "+refs/heads/leftover*:refs/remotes/vendor/*",
     "fetched recover leftover vendor leftover* refs so leftover git fetch vendor clobbered hotfix tracking",
     "git fetch vendor 2>&1 | tail; git rev-parse vendor/hotfix 2>&1 | tail",
     "fatal: leftover ambiguous argument 'vendor/hotfix'", "a1b2 leftover vendor/hotfix",
     "git fetch origin"),
    ("archive", "remote.archive.mirror", "true",
     "mirrored recover leftover every ref on fetch archive so leftover refs/pull/* flooded the leftover repo",
     "git fetch archive 2>&1 | tail; git for-each-ref refs/pull | wc -l",
     "400 leftover pull refs", "0 leftover pull refs", "git fetch --no-tags origin"),
    ("ci", "remote.ci.skipDefaultUpdate", "false",
     "updated recover leftover remote ci on every git remote update so leftover decommissioned ci 404ed the job",
     "git remote update 2>&1 | tail", "fatal: leftover could not read from remote ci",
     "a1b2 leftover origin/hotfix", "git remote update origin"),
    ("data", "remote.data.tagOpt", "--no-tags",
     "skipped recover leftover tags on fetch data so leftover v2.0.1 never arrived from the leftover data remote",
     "git fetch data && git rev-parse v2.0.1 2>&1 | tail",
     "fatal: leftover ambiguous argument 'v2.0.1'", "a1b2 leftover v2.0.1",
     "git fetch --tags origin"),
    ("docs", "remote.docs.prune", "true",
     "pruned recover leftover remote-tracking branches on fetch docs so leftover origin/hotfix vanished mid-job",
     "git fetch docs && git rev-parse origin/hotfix 2>&1 | tail",
     "fatal: leftover ambiguous argument 'origin/hotfix'", "a1b2 leftover origin/hotfix",
     "git fetch --no-prune origin"),
    ("sec", "remote.sec.receivepack", "/opt/legacy/receive-pack",
     "invoked recover leftover a missing receive-pack on push sec so leftover git push sec 404ed",
     "git push sec hotfix 2>&1 | tail", "error: leftover cannot run /opt/legacy/receive-pack",
     "a1b2 leftover hotfix", "git push origin hotfix"),
]):
    m(f"remote-{name}-{key.split('.')[-1].lower()}-w10a", f"h9f{i:02d}", key, bad,
      effect, probe, bad_obs, good_obs, wrong, "error leftover still")

# --- remaining unused scalar keys ---
for i, (slug, key, bad, good, effect, probe, bad_obs, good_obs, wrong, wrong_obs) in enumerate([
    ("color-advice-always-w10a", "color.advice", "always", "auto",
     "painted recover leftover advice hints with ANSI so leftover CI parsers treated ESC as the leftover hint text",
     "git status 2>&1 | cat", "\x1b[33mhint: leftover use git add\x1b[m",
     "hint: leftover use git add", "git -c color.advice=never status", "ansi leftover still"),
    ("color-pager-always-w10a", "color.pager", "always", "true",
     "forced recover leftover color through the pager so leftover git log | cat still emitted ESC and CI greps died",
     "git log -1 --oneline | cat", "\x1b[32ma1b2 leftover recover\x1b[m",
     "a1b2 leftover recover", "git --no-pager log -1 --oneline", "ansi leftover still"),
    ("color-diff-old-red-w10a", "color.diff.old", "red", "normal",
     "painted recover leftover deleted lines red so leftover git diff | patch failed to parse ESC as a leftover hunk",
     "git diff HEAD -- src/file.py | head -5", "\x1b[31m-leftover old\x1b[m",
     "-leftover old", "git diff --no-color HEAD -- src/file.py", "ansi leftover still"),
    ("color-diff-new-green-w10a", "color.diff.new", "green", "normal",
     "painted recover leftover added lines green so leftover format-patch mailed ESC and leftover git am died",
     "git diff HEAD -- src/file.py | rg '^\\+' | head -1", "\x1b[32m+leftover new\x1b[m",
     "+leftover new", "git diff --no-color HEAD -- src/file.py", "ansi leftover still"),
    ("color-status-added-blue-w10a", "color.status.added", "blue", "green",
     "painted recover leftover added paths blue so leftover git status --short | awk picked ESC as the leftover path",
     "git status --short", "\x1b[34mA  leftover src/file.py\x1b[m",
     "A  leftover src/file.py", "git status --porcelain", "ansi leftover still"),
    ("color-status-changed-yellow-w10a", "color.status.changed", "yellow", "red",
     "painted recover leftover changed paths yellow so leftover CI regexes missed M src/file.py",
     "git status --short", "\x1b[33m M leftover src/file.py\x1b[m",
     " M leftover src/file.py", "git status --porcelain", "ansi leftover still"),
    ("color-status-untracked-cyan-w10a", "color.status.untracked", "cyan", "red",
     "painted recover leftover untracked paths cyan so leftover CI missed ?? src/newhotfix.py",
     "git status --short src/newhotfix.py", "\x1b[36m?? leftover src/newhotfix.py\x1b[m",
     "?? leftover src/newhotfix.py", "git status --porcelain", "ansi leftover still"),
    ("color-branch-current-bold-w10a", "color.branch.current", "bold", "green",
     "bolded recover leftover the current branch so leftover git branch --show-current | cat printed leftover ESC",
     "git branch --show-current | cat", "\x1b[1mleftover hotfix\x1b[m",
     "leftover hotfix", "git -c color.branch=never branch --show-current", "ansi leftover still"),
    ("core-checkroundtrip-true-w10a", "core.checkRoundtripEncoding", "true", "false",
     "rejected recover leftover commit messages that failed leftover encoding roundtrip so leftover UTF-8 INC ids died",
     "git commit --allow-empty -F /tmp/utf8.msg 2>&1 | tail",
     "error: leftover commit message failed roundtrip encoding", " [leftover master a1b2]",
     "git commit --allow-empty -m leftover", "error leftover still"),
    ("core-fsmonitorhookversion-one-w10a", "core.fsmonitorHookVersion", "1", "2",
     "spoke recover leftover fsmonitor v1 to a v2 hook so leftover git status thought the leftover hook died",
     "git status -sb 2>&1 | tail", "error: leftover fsmonitor hook version mismatch",
     "## leftover recover/h9g09", "git update-index --refresh && git status -sb", "error leftover still"),
    ("core-prefersymlinkrefs-true-w10a", "core.prefersSymlinkRefs", "true", "false",
     "wrote recover leftover refs as symlinks so leftover Windows checkout of packed-refs died",
     "ls -l .git/HEAD; git status -sb", "fatal: leftover .git/HEAD is a symlink (Windows)",
     "## leftover hotfix", "git checkout hotfix", "fatal leftover still"),
    ("core-repoformat-zero-w10a", "core.repositoryFormatVersion", "0", "1",
     "forced recover leftover repositoryFormatVersion 0 so leftover extensions.worktreeConfig was ignored and leftover hooks skipped",
     "git status -sb 2>&1 | tail", "warning: leftover ignoring extensions.* (format 0)",
     "## leftover hotfix", "git status -sb", "warning leftover still"),
    ("advice-experimental-false-w10a", "advice.experimental", "false", "true",
     "silenced recover leftover experimental-feature hints so leftover feature.experimental looked leftover-stable",
     "git status 2>&1 | tail", "(empty leftover; no experimental hint)",
     "hint: leftover feature.experimental is enabled", "git -c advice.experimental=true status",
     "no hint leftover still"),
    ("advice-fastforwardjoined-false-w10a", "advice.fastForwardJoined", "false", "true",
     "silenced recover leftover fast-forward-joined hints so leftover git pull of a leftover diverged hotfix looked clean",
     "git pull origin hotfix 2>&1 | tail", "Already leftover up to date (no joined hint)",
     "hint: leftover Fast-forwarding instead of merging", "git pull --ff-only origin hotfix",
     "no hint leftover still"),
    ("advice-resetquiet-false-w10a", "advice.resetQuiet", "false", "true",
     "silenced recover leftover reset --quiet hints so leftover git reset --quiet hid leftover unstaged leftover files",
     "git reset --quiet HEAD~1 && git status --short", "(empty leftover; dirty files hidden)",
     " M leftover src/file.py", "git reset HEAD~1", "empty leftover still"),
    ("advice-resolveconflict-false-w10a", "advice.resolveConflict", "false", "true",
     "silenced recover leftover resolve-conflict hints so leftover git merge --continue looked idle during leftover conflicts",
     "git merge --continue 2>&1 | tail", "error: leftover Committing is not possible because you have unmerged files (no hint)",
     "hint: leftover Fix conflicts and run git merge --continue", "git merge --abort",
     "no hint leftover still"),
    ("advice-worktreebadcwd-false-w10a", "advice.worktreeBadCwd", "false", "true",
     "silenced recover leftover bad-cwd worktree hints so leftover git status from a leftover deleted worktree looked clean",
     "git -C /tmp/gone status -sb 2>&1 | tail", "fatal: leftover this operation must be run in a work tree (no hint)",
     "hint: leftover The worktree is no longer valid", "git status -sb", "no hint leftover still"),
    ("advice-unknownoption-false-w10a", "advice.unknownOption", "false", "true",
     "silenced recover leftover unknown-option hints so leftover git -c leftover.typo=1 looked leftover-valid",
     "git -c leftover.typo=1 status 2>&1 | tail", "(empty leftover; unknown option swallowed)",
     "warning: leftover unknown option leftover.typo", "git status -sb", "empty leftover still"),
    ("advice-defaultremotewarning-false-w10a", "advice.defaultRemoteWarning", "false", "true",
     "silenced recover leftover default-remote hints so leftover git push with two remotes pushed leftover-mirror",
     "git push 2>&1 | tail", "a1b2 leftover legacy-mirror (no default-remote hint)",
     "hint: leftover push.default is unset; using origin", "git push origin hotfix",
     "mirror leftover still"),
    ("http-proxysslcainfo-stale-w10a", "http.proxySSLCAInfo", "/opt/legacy/proxy-ca.pem", None,
     "loaded recover leftover a missing proxy CA so leftover https via corp proxy died on leftover TLS verify",
     "git ls-remote https://origin/hotfix 2>&1 | tail",
     "error: leftover could not load proxy CA /opt/legacy/proxy-ca.pem", "a1b2 leftover HEAD",
     "git -c http.proxySSLCAInfo= ls-remote https://origin/hotfix", "error leftover still"),
    ("http-sslbackend-schannel-w10a", "http.sslBackend", "schannel", "openssl",
     "forced recover leftover Schannel on Linux so leftover https fetch died looking for leftover schannel",
     "git ls-remote https://origin/hotfix 2>&1 | tail",
     "error: leftover unsupported SSL backend schannel", "a1b2 leftover HEAD",
     "git -c http.sslBackend=openssl ls-remote https://origin/hotfix", "error leftover still"),
    ("http-sslcertpasswordprotected-true-w10a", "http.sslCertPasswordProtected", "true", "false",
     "prompted recover leftover a client-cert passphrase so leftover CI https fetch hung on leftover Password:",
     "git ls-remote https://origin/hotfix 2>&1 | tail", "Password leftover for client cert:",
     "a1b2 leftover HEAD", "git -c http.sslCertPasswordProtected=false ls-remote https://origin/hotfix",
     "Password leftover still"),
    ("http-schannelusesslcainfo-false-w10a", "http.schannelUseSSLCAInfo", "false", "true",
     "ignored recover leftover http.sslCAInfo under Schannel so leftover corp MITM CA was leftover-untrusted",
     "git ls-remote https://origin/hotfix 2>&1 | tail",
     "fatal: leftover SSL certificate problem: self signed certificate in certificate chain",
     "a1b2 leftover HEAD", "git -c http.schannelUseSSLCAInfo=true ls-remote https://origin/hotfix",
     "fatal leftover still"),
    ("http-curloptresolve-stale-w10a", "http.curloptResolve", "origin:443:10.0.0.1", None,
     "pinned recover leftover origin to a leftover retired IP so leftover https fetch hung then leftover timed out",
     "git ls-remote https://origin/hotfix 2>&1 | tail",
     "fatal: leftover unable to access 10.0.0.1:443", "a1b2 leftover HEAD",
     "git -c http.curloptResolve= ls-remote https://origin/hotfix", "fatal leftover still"),
    ("credential-wwwauth-false-w10a", "credential.wwwauth", "false", "true",
     "skipped recover leftover WWW-Authenticate parsing so leftover https fetch never invoked leftover credential helper",
     "git ls-remote https://origin/hotfix 2>&1 | tail",
     "fatal: leftover Authentication failed (helper never called)", "a1b2 leftover HEAD",
     "GIT_ASKPASS=echo git ls-remote https://origin/hotfix", "fatal leftover still"),
    ("difftool-guitool-stale-w10a", "diff.guitool", "/opt/legacy/meld", None,
     "launched recover leftover git difftool -g through a missing meld so leftover CI hung on leftover DISPLAY",
     "git difftool -g --no-prompt HEAD -- src/file.py 2>&1 | tail",
     "error: leftover cannot run /opt/legacy/meld", "leftover textual diff",
     "git difftool --no-gui --no-prompt HEAD -- src/file.py", "error leftover still"),
    ("gui-commitmsgwidth-one-w10a", "gui.commitMsgWidth", "1", "72",
     "wrapped recover leftover git gui commit messages at 1 column so leftover INC ids were leftover-split across leftover 40 lines",
     "git commit --allow-empty -F /tmp/inc.msg && git log -1 --format=%B | wc -l",
     "40 leftover lines", "1 leftover line", "git commit --allow-empty -m leftover",
     "40 leftover still"),
    ("gui-fastcopyblame-true-w10a", "gui.fastCopyBlame", "true", "false",
     "skipped recover leftover blame copy detection so leftover git gui blamed leftover-old authors on leftover moved lines",
     "git blame -L 1,1 src/file.py", "dead leftover (ops 2019; copy skipped)",
     "a1b2 leftover (ops 3 weeks ago)", "git blame -C -L 1,1 src/file.py",
     "dead leftover still"),
    ("gui-matchtrackingbranch-false-w10a", "gui.matchTrackingBranch", "false", "true",
     "skipped recover leftover tracking-branch match so leftover git gui checkout created leftover local leftover-gone",
     "git checkout hotfix && git status -sb", "## leftover leftover-gone",
     "## leftover hotfix...origin/hotfix", "git checkout --track origin/hotfix",
     "leftover-gone leftover still"),
    ("gui-pruneduringfetch-true-w10a", "gui.pruneDuringFetch", "true", "false",
     "pruned recover leftover remote-tracking branches on leftover git gui fetch so leftover origin/hotfix vanished mid-job",
     "git fetch origin && git rev-parse origin/hotfix 2>&1 | tail",
     "fatal: leftover ambiguous argument 'origin/hotfix'", "a1b2 leftover origin/hotfix",
     "git fetch --no-prune origin", "fatal leftover still"),
    ("mergetool-prompt-true-w10a", "mergetool.prompt", "true", "false",
     "prompted recover leftover on every leftover conflict so leftover git mergetool in CI hung on leftover Continue?",
     "git mergetool --tool=vimdiff 2>&1 | tail", "Continue leftover merging [y/n]?",
     "leftover merged src/file.py", "git mergetool --no-prompt --tool=vimdiff",
     "prompt leftover still"),
    ("mergetool-trustexitcode-true-w10a", "mergetool.trustExitCode", "true", "false",
     "treated recover leftover a mergetool exit 1 as leftover failure so leftover CI failed a leftover benign vimdiff",
     "git mergetool --no-prompt --tool=vimdiff; echo exit:$?", "exit:1 leftover",
     "exit:0 leftover", "git mergetool --no-prompt --no-trust-exit-code --tool=vimdiff",
     "exit:1 leftover still"),
    ("branch-hotfix-remote-legacy-w10a", "branch.hotfix.remote", "legacy-mirror", None,
     "tracked recover leftover hotfix against decommissioned leftover-mirror so leftover git pull fetched leftover-old",
     "git pull 2>&1 | tail; git status -sb", "## leftover hotfix...legacy-mirror/hotfix [behind 40]",
     "## leftover hotfix...origin/hotfix", "git pull origin hotfix", "mirror leftover still"),
    ("branch-hotfix-merge-stale-w10a", "branch.hotfix.merge", "refs/heads/leftover-old", None,
     "merged recover leftover leftover-old as the leftover upstream so leftover git pull of hotfix landed leftover-old commits",
     "git pull && git log -1 --oneline", "dead leftover leftover-old tip",
     "a1b2 leftover hotfix", "git pull origin hotfix", "leftover-old leftover still"),
    ("branch-hotfix-rebase-true-w10a", "branch.hotfix.rebase", "true", "false",
     "rebased recover leftover every git pull on hotfix so leftover a merge-commit hotfix was leftover-flattened and leftover CI SHAs died",
     "git pull origin hotfix && git log -1 --format=%P | awk '{print NF}'",
     "1 leftover parent (rebase flattened merge)", "2 leftover parents",
     "git pull --no-rebase origin hotfix", "1 leftover still"),
    ("branch-hotfix-pushremote-legacy-w10a", "branch.hotfix.pushRemote", "legacy-mirror", None,
     "pushed recover leftover hotfix to leftover-mirror so leftover git push never updated leftover origin",
     "git push 2>&1 | tail", "fatal: leftover could not read from remote leftover-mirror",
     "a1b2 leftover origin/hotfix", "git push origin hotfix", "fatal leftover still"),
    ("submodule-nested-url-legacy-w10a", "submodule.nested.url", "git://legacy-host/nested.git", None,
     "cloned recover leftover nested from a decommissioned git:// host so leftover git submodule update 404ed",
     "git submodule update --init 2>&1 | tail", "fatal: leftover unable to connect to legacy-host",
     "Submodule leftover path nested", "git submodule update --init --checkout",
     "fatal leftover still"),
    ("submodule-nested-update-none-w10a", "submodule.nested.update", "none", "checkout",
     "skipped recover leftover nested checkout so leftover git submodule update left leftover nested at leftover-old SHA",
     "git submodule update --init && git -C nested rev-parse HEAD",
     "dead leftover leftover-old", "a1b2 leftover nested hotfix",
     "git submodule update --init --checkout", "dead leftover still"),
    ("submodule-nested-ignore-all-w10a", "submodule.nested.ignore", "all", "none",
     "ignored recover leftover nested SHA drift so leftover git status looked leftover-clean while leftover nested pointed leftover-old",
     "git status --short nested", "(empty leftover; nested ignored)",
     " leftover nested | 1 +-", "git diff --submodule=log HEAD -- nested",
     "empty leftover still"),
    ("submodule-nested-branch-stale-w10a", "submodule.nested.branch", "leftover-old", None,
     "tracked recover leftover nested on leftover-old so leftover git submodule update --remote landed leftover-old",
     "git submodule update --remote && git -C nested branch --show-current",
     "leftover leftover-old", "leftover hotfix", "git submodule update --remote --checkout",
     "leftover-old leftover still"),
    ("pager-show-stale-w10a", "pager.show", "/opt/legacy/less", None,
     "piped recover leftover git show through a missing less so leftover CI captured leftover empty output",
     "git show -1 --oneline 2>&1 | tail", "error: leftover cannot run /opt/legacy/less",
     "a1b2 leftover recover", "git --no-pager show -1 --oneline", "error leftover still"),
    ("pager-branch-stale-w10a", "pager.branch", "/opt/legacy/less", None,
     "piped recover leftover git branch through a missing less so leftover CI captured leftover empty branch list",
     "git branch --show-current 2>&1 | tail", "error: leftover cannot run /opt/legacy/less",
     "leftover hotfix", "git --no-pager branch --show-current", "error leftover still"),
    ("pager-tag-stale-w10a", "pager.tag", "/opt/legacy/less", None,
     "piped recover leftover git tag through a missing less so leftover CI missed leftover v2.0.1",
     "git tag 2>&1 | tail", "error: leftover cannot run /opt/legacy/less",
     "v2.0.1 leftover", "git --no-pager tag", "error leftover still"),
    ("pager-blame-stale-w10a", "pager.blame", "/opt/legacy/less", None,
     "piped recover leftover git blame through a missing less so leftover CI captured leftover empty blame",
     "git blame -L 1,1 src/file.py 2>&1 | tail", "error: leftover cannot run /opt/legacy/less",
     "a1b2 leftover (ops 3 weeks ago)", "git --no-pager blame -L 1,1 src/file.py",
     "error leftover still"),
    ("pretty-hotfix-oneline-w10a", "pretty.hotfix", "oneline", None,
     "forced recover leftover pretty=hotfix to oneline so leftover git log --pretty=hotfix dropped leftover INC bodies",
     "git log --pretty=hotfix -1 | wc -l", "1 leftover line", "12 leftover lines",
     "git log --pretty=medium -1", "1 leftover still"),
    ("pretty-leftover-fuller-w10a", "pretty.leftoverfmt", "fuller", None,
     "forced recover leftover pretty leftoverfmt to fuller so leftover git log scripts parsed leftover CommitDate as a leftover SHA",
     "git log --pretty=leftoverfmt -1 | rg CommitDate", "CommitDate leftover 2026-08-01",
     "Date leftover 2026-08-01", "git log --pretty=medium -1", "CommitDate leftover still"),
    ("lfs-url-legacy-w10a", "lfs.url", "https://legacy-lfs/ops.git/info/lfs", None,
     "fetched recover leftover LFS objects from a decommissioned host so leftover git lfs pull 404ed leftover binaries",
     "git lfs pull 2>&1 | tail", "error: leftover LFS: 404 from leftover-lfs",
     "leftover 12 files downloaded", "git lfs pull --include=fixtures/hotfix.bin",
     "error leftover still"),
    ("lfs-standalonetransfer-stale-w10a", "lfs.standalonetransferagent", "/opt/legacy/lfs-transfer", None,
     "invoked recover leftover a missing LFS transfer agent so leftover git lfs fetch 404ed",
     "git lfs fetch 2>&1 | tail", "error: leftover cannot run /opt/legacy/lfs-transfer",
     "leftover 12 objects fetched", "git lfs fetch origin hotfix", "error leftover still"),
    ("lfs-concurrenttransfers-one-w10a", "lfs.concurrenttransfers", "1", "8",
     "serialized recover leftover LFS downloads so leftover git lfs pull of leftover 4G fixtures timed out",
     "time git lfs pull 2>&1 | tail", "real leftover 180s", "real leftover 20s",
     "git -c lfs.concurrenttransfers=8 lfs pull", "real leftover 170s still"),
    ("lfs-activitytimeout-one-w10a", "lfs.activitytimeout", "1", "30",
     "aborted recover leftover LFS transfers after leftover 1s idle so leftover git lfs pull of leftover large bins died",
     "git lfs pull 2>&1 | tail", "error: leftover activity timeout leftover 1s",
     "leftover 12 files downloaded", "git -c lfs.activitytimeout=30 lfs pull",
     "error leftover still"),
    ("gpg-ssh-allowedsigners-stale-w10a", "gpg.ssh.allowedSignersFile", "/opt/legacy/allowed_signers", None,
     "loaded recover leftover a missing allowedSigners file so leftover git log --show-signature died",
     "git log --show-signature -1 2>&1 | tail",
     "error: leftover could not open /opt/legacy/allowed_signers", "gpg: leftover Good signature",
     "git log --no-show-signature -1", "error leftover still"),
    ("filter-keyword-required-true-w10a", "filter.keyword.required", "true", "false",
     "required recover leftover the leftover keyword filter so leftover git checkout died when leftover keyword-clean was leftover-missing",
     "git checkout -- src/file.py 2>&1 | tail", "error: leftover required filter keyword missing",
     "Updated leftover 1 path", "git checkout --no-filters -- src/file.py",
     "error leftover still"),
    ("remote-sec-uploadpack-stale-w10a", "remote.sec.uploadpack", "/opt/legacy/upload-pack", None,
     "invoked recover leftover a missing upload-pack on fetch sec so leftover git fetch sec 404ed",
     "git fetch sec 2>&1 | tail", "error: leftover cannot run /opt/legacy/upload-pack",
     "a1b2 leftover HEAD", "git fetch origin", "error leftover still"),
    ("branch-hotfix-description-stale-w10a", "branch.hotfix.description", "/opt/legacy/hotfix.txt", None,
     "loaded recover leftover a missing branch description so leftover git request-pull died",
     "git request-pull origin/main hotfix 2>&1 | tail",
     "error: leftover could not read /opt/legacy/hotfix.txt", "leftover request-pull body",
     "git request-pull origin/main hotfix", "error leftover still"),
]):
    # good may be None
    pass

# The last loop used a different shape; rebuild it properly below.
SCALAR: list[tuple] = []


def s(slug, stem, key, bad, good, effect, probe, bad_obs, good_obs, wrong, wrong_obs):
    SCALAR.append((slug, stem, key, bad, good, effect, probe, bad_obs, good_obs, wrong, wrong_obs))


# Re-add scalars with stems h9g00+
_scalars_src = [
    ("color-advice-always-w10a", "color.advice", "always", "auto",
     "painted recover leftover advice hints with ANSI so leftover CI parsers treated ESC as the leftover hint text",
     "git status 2>&1 | cat", "\x1b[33mhint: leftover use git add\x1b[m",
     "hint: leftover use git add", "git -c color.advice=never status", "ansi leftover still"),
    ("color-pager-always-w10a", "color.pager", "always", "true",
     "forced recover leftover color through the pager so leftover git log | cat still emitted ESC and CI greps died",
     "git log -1 --oneline | cat", "\x1b[32ma1b2 leftover recover\x1b[m",
     "a1b2 leftover recover", "git --no-pager log -1 --oneline", "ansi leftover still"),
    ("color-diff-old-red-w10a", "color.diff.old", "red", "normal",
     "painted recover leftover deleted lines red so leftover git diff | patch failed to parse ESC as a leftover hunk",
     "git diff HEAD -- src/file.py | head -5", "\x1b[31m-leftover old\x1b[m",
     "-leftover old", "git diff --no-color HEAD -- src/file.py", "ansi leftover still"),
    ("color-diff-new-green-w10a", "color.diff.new", "green", "normal",
     "painted recover leftover added lines green so leftover format-patch mailed ESC and leftover git am died",
     "git diff HEAD -- src/file.py | rg '^\\+' | head -1", "\x1b[32m+leftover new\x1b[m",
     "+leftover new", "git diff --no-color HEAD -- src/file.py", "ansi leftover still"),
    ("color-status-added-blue-w10a", "color.status.added", "blue", "green",
     "painted recover leftover added paths blue so leftover git status --short | awk picked ESC as the leftover path",
     "git status --short", "\x1b[34mA  leftover src/file.py\x1b[m",
     "A  leftover src/file.py", "git status --porcelain", "ansi leftover still"),
    ("color-status-changed-yellow-w10a", "color.status.changed", "yellow", "red",
     "painted recover leftover changed paths yellow so leftover CI regexes missed M src/file.py",
     "git status --short", "\x1b[33m M leftover src/file.py\x1b[m",
     " M leftover src/file.py", "git status --porcelain", "ansi leftover still"),
    ("color-status-untracked-cyan-w10a", "color.status.untracked", "cyan", "red",
     "painted recover leftover untracked paths cyan so leftover CI missed ?? src/newhotfix.py",
     "git status --short src/newhotfix.py", "\x1b[36m?? leftover src/newhotfix.py\x1b[m",
     "?? leftover src/newhotfix.py", "git status --porcelain", "ansi leftover still"),
    ("color-branch-current-bold-w10a", "color.branch.current", "bold", "green",
     "bolded recover leftover the current branch so leftover git branch --show-current | cat printed leftover ESC",
     "git branch --show-current | cat", "\x1b[1mleftover hotfix\x1b[m",
     "leftover hotfix", "git -c color.branch=never branch --show-current", "ansi leftover still"),
    ("core-checkroundtrip-true-w10a", "core.checkRoundtripEncoding", "true", "false",
     "rejected recover leftover commit messages that failed leftover encoding roundtrip so leftover UTF-8 INC ids died",
     "git commit --allow-empty -F /tmp/utf8.msg 2>&1 | tail",
     "error: leftover commit message failed roundtrip encoding", " [leftover master a1b2]",
     "git commit --allow-empty -m leftover", "error leftover still"),
    ("core-fsmonitorhookversion-one-w10a", "core.fsmonitorHookVersion", "1", "2",
     "spoke recover leftover fsmonitor v1 to a v2 hook so leftover git status thought the leftover hook died",
     "git status -sb 2>&1 | tail", "error: leftover fsmonitor hook version mismatch",
     "## leftover recover/h9g09", "git update-index --refresh && git status -sb", "error leftover still"),
    ("core-prefersymlinkrefs-true-w10a", "core.prefersSymlinkRefs", "true", "false",
     "wrote recover leftover refs as symlinks so leftover Windows checkout of packed-refs died",
     "ls -l .git/HEAD; git status -sb", "fatal: leftover .git/HEAD is a symlink (Windows)",
     "## leftover hotfix", "git checkout hotfix", "fatal leftover still"),
    ("core-repoformat-zero-w10a", "core.repositoryFormatVersion", "0", "1",
     "forced recover leftover repositoryFormatVersion 0 so leftover extensions.worktreeConfig was ignored and leftover hooks skipped",
     "git status -sb 2>&1 | tail", "warning: leftover ignoring extensions.* (format 0)",
     "## leftover hotfix", "git status -sb", "warning leftover still"),
    ("advice-experimental-false-w10a", "advice.experimental", "false", "true",
     "silenced recover leftover experimental-feature hints so leftover feature.experimental looked leftover-stable",
     "git status 2>&1 | tail", "(empty leftover; no experimental hint)",
     "hint: leftover feature.experimental is enabled", "git -c advice.experimental=true status",
     "no hint leftover still"),
    ("advice-fastforwardjoined-false-w10a", "advice.fastForwardJoined", "false", "true",
     "silenced recover leftover fast-forward-joined hints so leftover git pull of a leftover diverged hotfix looked clean",
     "git pull origin hotfix 2>&1 | tail", "Already leftover up to date (no joined hint)",
     "hint: leftover Fast-forwarding instead of merging", "git pull --ff-only origin hotfix",
     "no hint leftover still"),
    ("advice-resetquiet-false-w10a", "advice.resetQuiet", "false", "true",
     "silenced recover leftover reset --quiet hints so leftover git reset --quiet hid leftover unstaged leftover files",
     "git reset --quiet HEAD~1 && git status --short", "(empty leftover; dirty files hidden)",
     " M leftover src/file.py", "git reset HEAD~1", "empty leftover still"),
    ("advice-resolveconflict-false-w10a", "advice.resolveConflict", "false", "true",
     "silenced recover leftover resolve-conflict hints so leftover git merge --continue looked idle during leftover conflicts",
     "git merge --continue 2>&1 | tail", "error: leftover Committing is not possible because you have unmerged files (no hint)",
     "hint: leftover Fix conflicts and run git merge --continue", "git merge --abort",
     "no hint leftover still"),
    ("advice-worktreebadcwd-false-w10a", "advice.worktreeBadCwd", "false", "true",
     "silenced recover leftover bad-cwd worktree hints so leftover git status from a leftover deleted worktree looked clean",
     "git -C /tmp/gone status -sb 2>&1 | tail", "fatal: leftover this operation must be run in a work tree (no hint)",
     "hint: leftover The worktree is no longer valid", "git status -sb", "no hint leftover still"),
    ("advice-unknownoption-false-w10a", "advice.unknownOption", "false", "true",
     "silenced recover leftover unknown-option hints so leftover git -c leftover.typo=1 looked leftover-valid",
     "git -c leftover.typo=1 status 2>&1 | tail", "(empty leftover; unknown option swallowed)",
     "warning: leftover unknown option leftover.typo", "git status -sb", "empty leftover still"),
    ("advice-defaultremotewarning-false-w10a", "advice.defaultRemoteWarning", "false", "true",
     "silenced recover leftover default-remote hints so leftover git push with two remotes pushed leftover-mirror",
     "git push 2>&1 | tail", "a1b2 leftover legacy-mirror (no default-remote hint)",
     "hint: leftover push.default is unset; using origin", "git push origin hotfix",
     "mirror leftover still"),
    ("http-proxysslcainfo-stale-w10a", "http.proxySSLCAInfo", "/opt/legacy/proxy-ca.pem", None,
     "loaded recover leftover a missing proxy CA so leftover https via corp proxy died on leftover TLS verify",
     "git ls-remote https://origin/hotfix 2>&1 | tail",
     "error: leftover could not load proxy CA /opt/legacy/proxy-ca.pem", "a1b2 leftover HEAD",
     "git -c http.proxySSLCAInfo= ls-remote https://origin/hotfix", "error leftover still"),
    ("http-sslbackend-schannel-w10a", "http.sslBackend", "schannel", "openssl",
     "forced recover leftover Schannel on Linux so leftover https fetch died looking for leftover schannel",
     "git ls-remote https://origin/hotfix 2>&1 | tail",
     "error: leftover unsupported SSL backend schannel", "a1b2 leftover HEAD",
     "git -c http.sslBackend=openssl ls-remote https://origin/hotfix", "error leftover still"),
    ("http-sslcertpasswordprotected-true-w10a", "http.sslCertPasswordProtected", "true", "false",
     "prompted recover leftover a client-cert passphrase so leftover CI https fetch hung on leftover Password:",
     "git ls-remote https://origin/hotfix 2>&1 | tail", "Password leftover for client cert:",
     "a1b2 leftover HEAD", "git -c http.sslCertPasswordProtected=false ls-remote https://origin/hotfix",
     "Password leftover still"),
    ("http-schannelusesslcainfo-false-w10a", "http.schannelUseSSLCAInfo", "false", "true",
     "ignored recover leftover http.sslCAInfo under Schannel so leftover corp MITM CA was leftover-untrusted",
     "git ls-remote https://origin/hotfix 2>&1 | tail",
     "fatal: leftover SSL certificate problem: self signed certificate in certificate chain",
     "a1b2 leftover HEAD", "git -c http.schannelUseSSLCAInfo=true ls-remote https://origin/hotfix",
     "fatal leftover still"),
    ("http-curloptresolve-stale-w10a", "http.curloptResolve", "origin:443:10.0.0.1", None,
     "pinned recover leftover origin to a leftover retired IP so leftover https fetch hung then leftover timed out",
     "git ls-remote https://origin/hotfix 2>&1 | tail",
     "fatal: leftover unable to access 10.0.0.1:443", "a1b2 leftover HEAD",
     "git -c http.curloptResolve= ls-remote https://origin/hotfix", "fatal leftover still"),
    ("credential-wwwauth-false-w10a", "credential.wwwAuthExtraHeader", "false", "true",
     "skipped recover leftover WWW-Authenticate parsing so leftover https fetch never invoked leftover credential helper",
     "git ls-remote https://origin/hotfix 2>&1 | tail",
     "fatal: leftover Authentication failed (helper never called)", "a1b2 leftover HEAD",
     "GIT_ASKPASS=echo git ls-remote https://origin/hotfix", "fatal leftover still"),
    ("difftool-guitool-stale-w10a", "diff.guitool", "/opt/legacy/meld", None,
     "launched recover leftover git difftool -g through a missing meld so leftover CI hung on leftover DISPLAY",
     "git difftool -g --no-prompt HEAD -- src/file.py 2>&1 | tail",
     "error: leftover cannot run /opt/legacy/meld", "leftover textual diff",
     "git difftool --no-gui --no-prompt HEAD -- src/file.py", "error leftover still"),
    ("gui-commitmsgwidth-one-w10a", "gui.commitMsgWidth", "1", "72",
     "wrapped recover leftover git gui commit messages at 1 column so leftover INC ids were leftover-split across leftover 40 lines",
     "git commit --allow-empty -F /tmp/inc.msg && git log -1 --format=%B | wc -l",
     "40 leftover lines", "1 leftover line", "git commit --allow-empty -m leftover",
     "40 leftover still"),
    ("gui-fastcopyblame-true-w10a", "gui.fastCopyBlame", "true", "false",
     "skipped recover leftover blame copy detection so leftover git gui blamed leftover-old authors on leftover moved lines",
     "git blame -L 1,1 src/file.py", "dead leftover (ops 2019; copy skipped)",
     "a1b2 leftover (ops 3 weeks ago)", "git blame -C -L 1,1 src/file.py",
     "dead leftover still"),
    ("gui-matchtrackingbranch-false-w10a", "gui.matchTrackingBranch", "false", "true",
     "skipped recover leftover tracking-branch match so leftover git gui checkout created leftover local leftover-gone",
     "git checkout hotfix && git status -sb", "## leftover leftover-gone",
     "## leftover hotfix...origin/hotfix", "git checkout --track origin/hotfix",
     "leftover-gone leftover still"),
    ("gui-pruneduringfetch-true-w10a", "gui.pruneDuringFetch", "true", "false",
     "pruned recover leftover remote-tracking branches on leftover git gui fetch so leftover origin/hotfix vanished mid-job",
     "git fetch origin && git rev-parse origin/hotfix 2>&1 | tail",
     "fatal: leftover ambiguous argument 'origin/hotfix'", "a1b2 leftover origin/hotfix",
     "git fetch --no-prune origin", "fatal leftover still"),
    ("mergetool-prompt-true-w10a", "mergetool.prompt", "true", "false",
     "prompted recover leftover on every leftover conflict so leftover git mergetool in CI hung on leftover Continue?",
     "git mergetool --tool=vimdiff 2>&1 | tail", "Continue leftover merging [y/n]?",
     "leftover merged src/file.py", "git mergetool --no-prompt --tool=vimdiff",
     "prompt leftover still"),
    ("mergetool-trustexitcode-true-w10a", "mergetool.trustExitCode", "true", "false",
     "treated recover leftover a mergetool exit 1 as leftover failure so leftover CI failed a leftover benign vimdiff",
     "git mergetool --no-prompt --tool=vimdiff; echo exit:$?", "exit:1 leftover",
     "exit:0 leftover", "git mergetool --no-prompt --no-trust-exit-code --tool=vimdiff",
     "exit:1 leftover still"),
    ("branch-hotfix-remote-legacy-w10a", "branch.hotfix.remote", "legacy-mirror", None,
     "tracked recover leftover hotfix against decommissioned leftover-mirror so leftover git pull fetched leftover-old",
     "git pull 2>&1 | tail; git status -sb", "## leftover hotfix...legacy-mirror/hotfix [behind 40]",
     "## leftover hotfix...origin/hotfix", "git pull origin hotfix", "mirror leftover still"),
    ("branch-hotfix-merge-stale-w10a", "branch.hotfix.merge", "refs/heads/leftover-old", None,
     "merged recover leftover leftover-old as the leftover upstream so leftover git pull of hotfix landed leftover-old commits",
     "git pull && git log -1 --oneline", "dead leftover leftover-old tip",
     "a1b2 leftover hotfix", "git pull origin hotfix", "leftover-old leftover still"),
    ("branch-hotfix-rebase-true-w10a", "branch.hotfix.rebase", "true", "false",
     "rebased recover leftover every git pull on hotfix so leftover a merge-commit hotfix was leftover-flattened and leftover CI SHAs died",
     "git pull origin hotfix && git log -1 --format=%P | awk '{print NF}'",
     "1 leftover parent (rebase flattened merge)", "2 leftover parents",
     "git pull --no-rebase origin hotfix", "1 leftover still"),
    ("branch-hotfix-pushremote-legacy-w10a", "branch.hotfix.pushRemote", "legacy-mirror", None,
     "pushed recover leftover hotfix to leftover-mirror so leftover git push never updated leftover origin",
     "git push 2>&1 | tail", "fatal: leftover could not read from remote leftover-mirror",
     "a1b2 leftover origin/hotfix", "git push origin hotfix", "fatal leftover still"),
    ("submodule-nested-url-legacy-w10a", "submodule.nested.url", "git://legacy-host/nested.git", None,
     "cloned recover leftover nested from a decommissioned git:// host so leftover git submodule update 404ed",
     "git submodule update --init 2>&1 | tail", "fatal: leftover unable to connect to legacy-host",
     "Submodule leftover path nested", "git submodule update --init --checkout",
     "fatal leftover still"),
    ("submodule-nested-update-none-w10a", "submodule.nested.update", "none", "checkout",
     "skipped recover leftover nested checkout so leftover git submodule update left leftover nested at leftover-old SHA",
     "git submodule update --init && git -C nested rev-parse HEAD",
     "dead leftover leftover-old", "a1b2 leftover nested hotfix",
     "git submodule update --init --checkout", "dead leftover still"),
    ("submodule-nested-ignore-all-w10a", "submodule.nested.ignore", "all", "none",
     "ignored recover leftover nested SHA drift so leftover git status looked leftover-clean while leftover nested pointed leftover-old",
     "git status --short nested", "(empty leftover; nested ignored)",
     " leftover nested | 1 +-", "git diff --submodule=log HEAD -- nested",
     "empty leftover still"),
    ("submodule-nested-branch-stale-w10a", "submodule.nested.branch", "leftover-old", None,
     "tracked recover leftover nested on leftover-old so leftover git submodule update --remote landed leftover-old",
     "git submodule update --remote && git -C nested branch --show-current",
     "leftover leftover-old", "leftover hotfix", "git submodule update --remote --checkout",
     "leftover-old leftover still"),
    ("pager-show-stale-w10a", "pager.show", "/opt/legacy/less", None,
     "piped recover leftover git show through a missing less so leftover CI captured leftover empty output",
     "git show -1 --oneline 2>&1 | tail", "error: leftover cannot run /opt/legacy/less",
     "a1b2 leftover recover", "git --no-pager show -1 --oneline", "error leftover still"),
    ("pager-branch-stale-w10a", "pager.branch", "/opt/legacy/less", None,
     "piped recover leftover git branch through a missing less so leftover CI captured leftover empty branch list",
     "git branch --show-current 2>&1 | tail", "error: leftover cannot run /opt/legacy/less",
     "leftover hotfix", "git --no-pager branch --show-current", "error leftover still"),
    ("pager-tag-stale-w10a", "pager.tag", "/opt/legacy/less", None,
     "piped recover leftover git tag through a missing less so leftover CI missed leftover v2.0.1",
     "git tag 2>&1 | tail", "error: leftover cannot run /opt/legacy/less",
     "v2.0.1 leftover", "git --no-pager tag", "error leftover still"),
    ("pager-blame-stale-w10a", "pager.blame", "/opt/legacy/less", None,
     "piped recover leftover git blame through a missing less so leftover CI captured leftover empty blame",
     "git blame -L 1,1 src/file.py 2>&1 | tail", "error: leftover cannot run /opt/legacy/less",
     "a1b2 leftover (ops 3 weeks ago)", "git --no-pager blame -L 1,1 src/file.py",
     "error leftover still"),
    ("pretty-hotfix-oneline-w10a", "pretty.hotfix", "oneline", None,
     "forced recover leftover pretty=hotfix to oneline so leftover git log --pretty=hotfix dropped leftover INC bodies",
     "git log --pretty=hotfix -1 | wc -l", "1 leftover line", "12 leftover lines",
     "git log --pretty=medium -1", "1 leftover still"),
    ("pretty-leftover-fuller-w10a", "pretty.leftoverfmt", "fuller", None,
     "forced recover leftover pretty leftoverfmt to fuller so leftover git log scripts parsed leftover CommitDate as a leftover SHA",
     "git log --pretty=leftoverfmt -1 | rg CommitDate", "CommitDate leftover 2026-08-01",
     "Date leftover 2026-08-01", "git log --pretty=medium -1", "CommitDate leftover still"),
    ("lfs-url-legacy-w10a", "lfs.url", "https://legacy-lfs/ops.git/info/lfs", None,
     "fetched recover leftover LFS objects from a decommissioned host so leftover git lfs pull 404ed leftover binaries",
     "git lfs pull 2>&1 | tail", "error: leftover LFS: 404 from leftover-lfs",
     "leftover 12 files downloaded", "git lfs pull --include=fixtures/hotfix.bin",
     "error leftover still"),
    ("lfs-standalonetransfer-stale-w10a", "lfs.standalonetransferagent", "/opt/legacy/lfs-transfer", None,
     "invoked recover leftover a missing LFS transfer agent so leftover git lfs fetch 404ed",
     "git lfs fetch 2>&1 | tail", "error: leftover cannot run /opt/legacy/lfs-transfer",
     "leftover 12 objects fetched", "git lfs fetch origin hotfix", "error leftover still"),
    ("lfs-concurrenttransfers-one-w10a", "lfs.concurrenttransfers", "1", "8",
     "serialized recover leftover LFS downloads so leftover git lfs pull of leftover 4G fixtures timed out",
     "time git lfs pull 2>&1 | tail", "real leftover 180s", "real leftover 20s",
     "git -c lfs.concurrenttransfers=8 lfs pull", "real leftover 170s still"),
    ("lfs-activitytimeout-one-w10a", "lfs.activitytimeout", "1", "30",
     "aborted recover leftover LFS transfers after leftover 1s idle so leftover git lfs pull of leftover large bins died",
     "git lfs pull 2>&1 | tail", "error: leftover activity timeout leftover 1s",
     "leftover 12 files downloaded", "git -c lfs.activitytimeout=30 lfs pull",
     "error leftover still"),
    ("gpg-ssh-allowedsigners-stale-w10a", "gpg.ssh.allowedSignersFile", "/opt/legacy/allowed_signers", None,
     "loaded recover leftover a missing allowedSigners file so leftover git log --show-signature died",
     "git log --show-signature -1 2>&1 | tail",
     "error: leftover could not open /opt/legacy/allowed_signers", "gpg: leftover Good signature",
     "git log --no-show-signature -1", "error leftover still"),
    ("filter-keyword-required-true-w10a", "filter.keyword.required", "true", "false",
     "required recover leftover the leftover keyword filter so leftover git checkout died when leftover keyword-clean was leftover-missing",
     "git checkout -- src/file.py 2>&1 | tail", "error: leftover required filter keyword missing",
     "Updated leftover 1 path", "git checkout --no-filters -- src/file.py",
     "error leftover still"),
    ("remote-sec-uploadpack-stale-w10a", "remote.sec.uploadpack", "/opt/legacy/upload-pack", None,
     "invoked recover leftover a missing upload-pack on fetch sec so leftover git fetch sec 404ed",
     "git fetch sec 2>&1 | tail", "error: leftover cannot run /opt/legacy/upload-pack",
     "a1b2 leftover HEAD", "git fetch origin", "error leftover still"),
    ("branch-hotfix-description-stale-w10a", "branch.hotfix.description", "/opt/legacy/hotfix.txt", None,
     "loaded recover leftover a missing branch description so leftover git request-pull died",
     "git request-pull origin/main hotfix 2>&1 | tail",
     "error: leftover could not read /opt/legacy/hotfix.txt", "leftover request-pull body",
     "git request-pull origin/main hotfix", "error leftover still"),
]
for i, row in enumerate(_scalars_src):
    slug, key, bad, good, effect, probe, bad_obs, good_obs, wrong, wrong_obs = row
    s(slug, f"h9g{i:02d}", key, bad, good, effect, probe, bad_obs, good_obs, wrong, wrong_obs)


def json_str(val) -> str:
    if val is None:
        return "None"
    return '"' + str(val).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def to_cfg_tuple(row, *, kind: str) -> tuple:
    # MISSING: slug, stem, key, bad, effect, probe, bad_obs, good_obs, wrong, wrong_obs  (good=None)
    # SCALAR:  slug, stem, key, bad, good, effect, probe, bad_obs, good_obs, wrong, wrong_obs
    if kind == "missing":
        slug, stem, key, bad, effect, probe, bad_obs, good_obs, wrong, wrong_obs = row
        good = None
    else:
        slug, stem, key, bad, good, effect, probe, bad_obs, good_obs, wrong, wrong_obs = row
    return (slug, stem, key, bad, good, effect, probe, bad_obs, good_obs, wrong, wrong_obs)


def main() -> int:
    mill_text = MILL.read_text()
    mill_slugs = set(re.findall(r'slug="([^"]+)"', mill_text)) | set(
        re.findall(r'_cfg\(\s*"([^"]+)"', mill_text)
    )
    mill_stems = {m.group(2) for m in re.finditer(r'_(?:cfg|cmd)\(\s*"([^"]+)"\s*,\s*"([^"]+)"', mill_text)}

    rows = [to_cfg_tuple(r, kind="missing") for r in MISSING] + [
        to_cfg_tuple(r, kind="scalar") for r in SCALAR
    ]
    if len(rows) % 2:
        raise SystemExit(f"odd rows {len(rows)}")
    slugs = [r[0] for r in rows]
    stems = [r[1] for r in rows]
    if len(slugs) != len(set(slugs)):
        raise SystemExit(f"dup slugs {set(s for s in slugs if slugs.count(s)>1)}")
    if len(stems) != len(set(stems)):
        raise SystemExit(f"dup stems {set(s for s in stems if stems.count(s)>1)}")
    hit_slug = [s for s in slugs if s in mill_slugs]
    hit_stem = [s for s in stems if s in mill_stems]
    if hit_slug:
        raise SystemExit(f"slug collision {hit_slug[:12]}")
    if hit_stem:
        raise SystemExit(f"stem collision {hit_stem[:12]}")

    # pair consecutive; if sibling first-token, swap with next different
    paired: list[tuple] = []
    i = 0
    used = set()
    while i < len(rows):
        if i in used:
            i += 1
            continue
        a = rows[i]
        used.add(i)
        pa = a[0].split("-")[0]
        b = None
        for j in range(i + 1, len(rows)):
            if j in used:
                continue
            cand = rows[j]
            if cand[0].split("-")[0] != pa:
                b = cand
                used.add(j)
                break
        if b is None:
            raise SystemExit(f"no partner for {a[0]}")
        paired.append((a, b))
        i += 1

    lines = ["\n# --- W10 unique plants (continuation; not clones of r793-r1724 / W9) ---\n"]
    for n, (a, b) in enumerate(paired):
        oa, na_ = str(n % 4), str(5 + (n % 5))
        ob, nb = str((n + 1) % 4), str(5 + ((n + 2) % 5))

        def call(row, *, handoff: bool, old: str, new: str) -> str:
            slug, stem, key, bad, good, effect, probe, bad_obs, good_obs, wrong, wrong_obs = row
            extra = ",\n         handoff=True" if handoff else ""
            return (
                f"    _cfg({json_str(slug)}, {json_str(stem)}, {json_str(key)}, {json_str(bad)}, {json_str(good)},\n"
                f"         {json_str(effect)},\n"
                f"         {json_str(probe)},\n"
                f"         {json_str(bad_obs)}, {json_str(good_obs)},\n"
                f"         {json_str(wrong)},\n"
                f"         {json_str(wrong_obs)}{extra}, old={json_str(old)}, new={json_str(new)}),"
            )

        lines.append("add(\n")
        lines.append(call(a, handoff=False, old=oa, new=na_) + "\n")
        lines.append(call(b, handoff=True, old=ob, new=nb) + "\n")
        lines.append(")\n")

    block = "".join(lines)
    needle = "\ndef _assert_local() -> None:\n"
    if needle not in mill_text:
        raise SystemExit("cannot find _assert_local")
    if "W10 unique plants" in mill_text:
        raise SystemExit("W10 already present")
    MILL.write_text(mill_text.replace(needle, block + needle, 1))
    print(f"appended {len(paired)} W10 pairs ({len(rows)} plants)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
