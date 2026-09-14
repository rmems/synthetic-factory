#!/usr/bin/env python3
"""Append W11 unique git-ops plants to gor-mill-r1460.py."""
from __future__ import annotations

import re
from pathlib import Path

MILL = Path(__file__).resolve().parent / "gor-mill-r1460.py"


def js(val) -> str:
    if val is None:
        return "None"
    return '"' + str(val).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


ROWS: list[tuple] = []


def add_row(slug, stem, key, bad, good, effect, probe, bad_obs, good_obs, wrong, wrong_obs):
    ROWS.append((slug, stem, key, bad, good, effect, probe, bad_obs, good_obs, wrong, wrong_obs))


REMOTES = [
    ("ops", "git://legacy-ops/ops.git", "decommissioned ops git:// host"),
    ("prod", "https://legacy-prod/ops.git", "retired prod HTTPS mirror"),
    ("stage", "ssh://legacy-stage/ops.git", "retired stage SSH host"),
    ("qa", "https://legacy-qa/ops.git", "retired qa HTTPS host"),
    ("lab", "git://legacy-lab/ops.git", "retired lab git:// host"),
    ("edge", "ssh://legacy-edge/ops.git", "retired edge SSH host"),
    ("canary", "https://legacy-canary/ops.git", "retired canary HTTPS host"),
    ("drsite", "ssh://legacy-dr/ops.git", "retired DR SSH host"),
    ("bak", "https://legacy-bak/ops.git", "retired backup HTTPS host"),
    ("tmpcopy", "git://legacy-tmp/ops.git", "retired tmp git:// host"),
    ("build", "https://legacy-build/ops.git", "retired build HTTPS host"),
    ("nightly", "ssh://legacy-nightly/ops.git", "retired nightly SSH host"),
    ("release", "https://legacy-release/ops.git", "retired release HTTPS host"),
    ("hotfixrem", "ssh://legacy-hotfix/ops.git", "retired hotfix SSH host"),
    ("vendor2", "git://legacy-vendor/ops.git", "retired vendor git:// host"),
    ("docs2", "https://legacy-docs/ops.git", "retired docs HTTPS host"),
    ("data2", "ssh://legacy-data/ops.git", "retired data SSH host"),
    ("sec2", "https://legacy-sec/ops.git", "retired sec HTTPS host"),
    ("ci2", "git://legacy-ci/ops.git", "retired ci git:// host"),
    ("mirror2", "ssh://legacy-mirror2/ops.git", "retired second mirror SSH host"),
]
for i, (name, url, desc) in enumerate(REMOTES):
    add_row(
        f"remote-{name}-url-stale-w11a", f"j9a{i:02d}", f"remote.{name}.url", url, None,
        f"pointed recover leftover remote {name} at {desc} so leftover git fetch {name} 404ed",
        f"git fetch {name} 2>&1 | tail", f"fatal: leftover could not read from remote {name}",
        "a1b2 leftover HEAD", "git fetch origin", "fatal leftover still",
    )
    add_row(
        f"remote-{name}-proxy-stale-w11a", f"j9b{i:02d}", f"remote.{name}.proxy",
        f"http://legacy-proxy-{name}:8080", None,
        f"routed recover leftover remote {name} through a decommissioned leftover proxy so leftover fetch hung then 504ed",
        f"git fetch {name} 2>&1 | tail", f"fatal: leftover unable to access proxy legacy-proxy-{name}:8080",
        "a1b2 leftover HEAD", "git fetch origin", "fatal leftover still",
    )

ALIASES = [
    ("amend", "commit --amend wrapper"), ("fixup", "commit --fixup wrapper"),
    ("wip", "work-in-progress commit"), ("unwip", "reset wip wrapper"),
    ("sync", "fetch+rebase wrapper"), ("ship", "push wrapper"),
    ("land", "merge wrapper"), ("abort", "rebase --abort wrapper"),
    ("cont", "rebase --continue wrapper"), ("skip", "rebase --skip wrapper"),
    ("ours", "checkout --ours wrapper"), ("theirs", "checkout --theirs wrapper"),
    ("ours2", "merge -s ours wrapper"), ("theirs2", "merge -X theirs wrapper"),
    ("graph", "log --graph wrapper"), ("files", "ls-files wrapper"),
    ("ignored", "ls-files --ignored wrapper"), ("untracked", "ls-files --others wrapper"),
    ("staged", "diff --cached wrapper"), ("unstaged", "diff wrapper"),
]
for i, (cmd, desc) in enumerate(ALIASES):
    add_row(
        f"alias-{cmd}-stale-w11a", f"j9c{i:02d}", f"alias.{cmd}", f"!/opt/legacy/{cmd}.sh", None,
        f"aliased recover leftover git {cmd} ({desc}) to a missing wrapper so leftover CI git {cmd} 404ed",
        f"git {cmd} 2>&1 | tail", f"error: leftover cannot run /opt/legacy/{cmd}.sh",
        f"leftover {cmd} ok", f"git {cmd}", "error leftover still",
    )

FILTERS = [
    "yamlfmt", "jsonnet", "bicep", "pulumi", "opentofu", "crossplane", "kustomize",
    "skaffold", "argocd", "fluxcd", "istioctl", "linkerd", "consul", "vault",
    "boundary", "waypoint", "nomad", "packer", "vagrant", "dolt",
]
for i, name in enumerate(FILTERS):
    add_row(
        f"filter-{name}-smudge-w11a", f"j9d{i:02d}", f"filter.{name}.smudge",
        f"/opt/legacy/{name}-smudge", None,
        f"ran recover leftover {name} smudge through a missing helper so leftover git checkout of src/j9d{i:02d}.py 404ed",
        f"git checkout -- src/j9d{i:02d}.py 2>&1 | tail",
        f"error: leftover cannot run /opt/legacy/{name}-smudge", "Updated leftover 1 path",
        f"git checkout --no-filters -- src/j9d{i:02d}.py", "error leftover still",
    )

INCLUDE = [
    ("gitdir:/srv/ops/", "/etc/leftover-ops.gitconfig"),
    ("gitdir:/srv/prod/", "/etc/leftover-prod.gitconfig"),
    ("gitdir:/srv/stage/", "/etc/leftover-stage.gitconfig"),
    ("gitdir:/var/lib/git/", "/etc/leftover-var.gitconfig"),
    ("onbranch:release/**", "/etc/leftover-release.gitconfig"),
    ("onbranch:nightly", "/etc/leftover-nightly.gitconfig"),
    ("hasconfig:remote.origin.url:git@retired:**", "/etc/leftover-retired.gitconfig"),
    ("hasconfig:remote.origin.url:https://retired/**", "/etc/leftover-rethttps.gitconfig"),
]
for i, (cond, path) in enumerate(INCLUDE):
    token = cond.split(":")[0] + str(i)
    add_row(
        f"includeif-{token}-w11a", f"j9e{i:02d}", f"includeIf.{cond}.path", path, None,
        f"included recover leftover {cond} config from missing {path} so leftover git config --get user.email died",
        "git config --get user.email 2>&1 | tail",
        f"fatal: leftover cannot include {path}", "oncall@ex leftover",
        "git -c include.path=/dev/null config --get user.email", "fatal leftover still",
    )

URLS = [
    ("retired-ops", "https", "insteadOf"),
    ("retired-prod", "ssh", "insteadOf"),
    ("retired-stage", "git", "insteadOf"),
    ("retired-qa", "https", "pushInsteadOf"),
    ("retired-lab", "ssh", "pushInsteadOf"),
    ("retired-edge", "https", "insteadOf"),
    ("retired-canary", "git", "insteadOf"),
    ("retired-dr", "https", "pushInsteadOf"),
]
for i, (host, scheme, kind) in enumerate(URLS):
    key = f"url.{scheme}://{host}/.{kind}"
    bad = "ssh://origin/" if kind == "pushInsteadOf" else "https://origin/"
    probe = "git push origin hotfix 2>&1 | tail" if kind == "pushInsteadOf" else "git fetch origin 2>&1 | tail"
    add_row(
        f"url-{host.replace('-', '')}-{kind.lower()}-w11a", f"j9f{i:02d}", key, bad, None,
        f"rewrote recover leftover {kind} through decommissioned {host} so leftover git never reached origin",
        probe, f"fatal: leftover unable to connect to {host}", "a1b2 leftover hotfix",
        "git fetch origin" if kind != "pushInsteadOf" else "git push ssh://origin/ hotfix",
        "fatal leftover still",
    )


def main() -> int:
    mill_text = MILL.read_text()
    mill_slugs = set(re.findall(r'_cfg\(\s*"([^"]+)"', mill_text))
    mill_stems = {m.group(2) for m in re.finditer(r'_(?:cfg|cmd)\(\s*"([^"]+)"\s*,\s*"([^"]+)"', mill_text)}
    slugs = [r[0] for r in ROWS]
    stems = [r[1] for r in ROWS]
    if len(ROWS) % 2:
        raise SystemExit(f"odd rows {len(ROWS)}")
    if len(slugs) != len(set(slugs)):
        raise SystemExit("dup slugs " + str(set(s for s in slugs if slugs.count(s) > 1)))
    if len(stems) != len(set(stems)):
        raise SystemExit("dup stems " + str(set(s for s in stems if stems.count(s) > 1)))
    hit_s = [s for s in slugs if s in mill_slugs]
    hit_t = [s for s in stems if s in mill_stems]
    if hit_s:
        raise SystemExit(f"slug collision {hit_s[:12]}")
    if hit_t:
        raise SystemExit(f"stem collision {hit_t[:12]}")

    used: set[int] = set()
    paired: list[tuple] = []
    for i, a in enumerate(ROWS):
        if i in used:
            continue
        pa = a[0].split("-")[0]
        used.add(i)
        b = None
        for j in range(i + 1, len(ROWS)):
            if j in used:
                continue
            if ROWS[j][0].split("-")[0] != pa:
                b = ROWS[j]
                used.add(j)
                break
        if b is None:
            raise SystemExit(f"no partner for {a[0]}")
        paired.append((a, b))

    lines = ["\n# --- W11 unique plants (continuation; not clones of r793-r1724 / W9 / W10) ---\n"]
    for n, (a, b) in enumerate(paired):
        oa, na = str(n % 4), str(5 + (n % 5))
        ob, nb = str((n + 1) % 4), str(5 + ((n + 2) % 5))

        def call(row, *, handoff: bool, old: str, new: str) -> str:
            slug, stem, key, bad, good, effect, probe, bad_obs, good_obs, wrong, wrong_obs = row
            extra = ",\n         handoff=True" if handoff else ""
            return (
                f"    _cfg({js(slug)}, {js(stem)}, {js(key)}, {js(bad)}, {js(good)},\n"
                f"         {js(effect)},\n"
                f"         {js(probe)},\n"
                f"         {js(bad_obs)}, {js(good_obs)},\n"
                f"         {js(wrong)},\n"
                f"         {js(wrong_obs)}{extra}, old={js(old)}, new={js(new)}),"
            )

        lines.append("add(\n" + call(a, handoff=False, old=oa, new=na) + "\n" + call(b, handoff=True, old=ob, new=nb) + "\n)\n")

    block = "".join(lines)
    needle = "\ndef _assert_local() -> None:\n"
    if "W11 unique plants" in mill_text:
        raise SystemExit("W11 already present")
    MILL.write_text(mill_text.replace(needle, block + needle, 1))
    print(f"appended {len(paired)} W11 pairs ({len(ROWS)} plants)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
