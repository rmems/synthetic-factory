#!/usr/bin/env python3
"""Mill monorepo-dep-bump-factory r776+ as unique leftover plants.

BAN r01–r775 clones: pnpm catalog/zod, changesets, maven BOM, gradle kotlin,
go.work, uv pydantic, poetry httpx, turbo, cargo patch, yarn constraints,
bun lock, nx migrate, macports-portfile-leftover-python39, hy-deps-leftover-assoc,
workspace/catalog/libNNNN, Mix/Elixir, Conan/Hunter/vcpkg/Meson wrap/CMake
FetchContent, r709–r761 lock leftover grids, r762–r775 leftover langs
(Mercury/Factor/Red/Io/Pharo/GAP/Fennel/Unison/Grain/AS/Waf/Autotools/Tuist/
Brewfile/Devbox/CNB/Helm/Pulumi/colcon/ESP-IDF/Yocto/FuseSoC/SMLNJ/MLton/
Koka/Roc/MacPorts/Hy).

NEW leftover bump surfaces start at r776 (Ansible FQCN, Salt pkg.latest, …).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

FACTORY = "monorepo-dep-bump-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 776

BANNED_SLUG_NEEDLES = (
    "catalog-zod",
    "changesets-snapshot",
    "changesets-ignore",
    "maven-bom",
    "gradle-kotlin",
    "gradle-catalog",
    "gowork-grpc",
    "gowork-use",
    "uv-pydantic",
    "uv-workspace",
    "poetry-httpx",
    "poetry-source",
    "turbo-",
    "cargo-wsdep-patch",
    "yarn-constraints",
    "bun-lock",
    "bun-catalog",
    "nx-migrate",
    "nx-implicit",
    "pnpm-override",
    "npm-catalog",
    "lib0",
    "lib1",
    "lib2",
    "npm3-lib",
    "cargo3-lib",
    "pypi3-lib",
    "lerna",
    "rush-",
    "moon-",
    "mise-",
    "pixi-",
    "nix-flake",
    "mix-umbrella",
    "elixir",
    "conan",
    "fetchcontent",
    "vcpkg",
    "meson-wrap",
    "hunter",
    "rebar3-lock",
    "gleam-manifest",
    "zig-zon",
    "odin-collection",
    "luarocks-lock",
    "fpm-lock",
    "alire-lock",
    "lean-lake",
    "vlang-vmod",
    "pony-corral",
    "chapel-mason",
    "racket-info",
    "witdeps-lock",
    "scala-mill",
    "sbt-lock",
    "lein-pedestal",
    "elm-json",
    "haxe-haxelib",
    "godot-addon",
    "unity-packages",
    "swiprolog-pack",
    "qlot-lock",
    "agda-libraries",
    "coq-project",
    "janet-lock",
    "idris2-pack",
    "babashka-bb",
    "rescript-json",
    "hare-pkg",
    "moonbit-mod",
    "qbs-modules",
    "emscripten-ports",
    "premake5",
    "carthage-resolved",
    "gradle-platform",
    "gomod-toolchain",
    "yarn-pnp",
    "poetry-extras",
    "uv-constraint",
    "ninja-rules",
    "cue-modules",
    "dagger-engine",
    "dhall-freeze",
    "nickel-lock",
    "pkl-project",
    "jsonnet-bundler",
    "terragrunt-source",
    "opentofu-lock",
    "packer-plugin",
    "skaffold-api",
    "kustomize-components",
    "tilt-ext",
    "argocd-appproj",
    "tekton-resolver",
    "macports-portfile",
    "hy-deps-leftover",
    "mercury-deps",
    "factor-vocabs",
    "red-rc",
    "io-eerie",
    "pharo-metacello",
    "gap-pkginfo",
    "fennel-deps",
    "unison-ucm",
    "grain-lock",
    "assemblyscript-asconfig",
    "waf-wscript",
    "autotools-ac",
    "tuist-manifest",
    "brewfile-lock",
    "devbox-lock",
    "buildpacks-toml",
    "helm-chartlock",
    "pulumi-lock",
    "colcon-pkgxml",
    "espidf-component",
    "yocto-layer",
    "fusesoc-core",
    "smlnj-cm",
    "mlton-mlb",
    "koka-pkg",
    "roc-packages",
)


def clip(text: str, n: int = 240) -> str:
    text = " ".join(str(text).split())
    if len(text) <= n:
        return text
    return text[: n - 1].rstrip() + "…"


def step(n: int, basis: str, name: str, args: dict, obs: str, reflection: str | None = None) -> dict:
    basis = clip(basis)
    prefix = basis.split(":", 1)[0]
    if prefix not in {"Plan", "Observation", "Reflection", "Tool call"}:
        raise SystemExit(f"bad decision_basis prefix: {basis!r}")
    if len(basis) > 240:
        raise SystemExit(f"decision_basis too long ({len(basis)}): {basis}")
    out = {
        "n": n,
        "decision_basis": basis,
        "tool_call": {"name": name, "args": args},
        "observation": obs,
    }
    if reflection:
        out["reflection"] = reflection
    return out


def bash(n: int, basis: str, cmd: str, obs: str, reflection: str | None = None) -> dict:
    return step(n, basis, "bash", {"command": cmd}, obs, reflection)


def read(n: int, basis: str, path: str, obs: str) -> dict:
    return step(n, basis, "read", {"path": path}, obs)


def edit(n: int, basis: str, path: str, old: str, new: str, obs: str, reflection: str | None = None) -> dict:
    return step(n, basis, "edit", {"path": path, "old": old, "new": new}, obs, reflection)


def fill(spec: dict) -> dict:
    s = dict(spec)
    pkg, old, new = s["pkg"], s["old"], s["new"]
    left_ver = s.setdefault("left_ver", old)
    fail = bool(s["fail"])
    s.setdefault(
        "inspect_cmd",
        f"rg -n '{pkg}|{old}|{new}' {s['sot']} {s['nested']} {s['left_file']} | head -n 40",
    )
    s.setdefault(
        "scan_cmd",
        f"rg -n '{old}|{new}|{left_ver}' {s['sot']} {s['nested']} {s['left_file']} | head -n 16",
    )
    verb = "leftover" if fail else "leave"
    s.setdefault("leave_cmd", f"echo {verb} {s['left']} {pkg} {left_ver}")
    s.setdefault("leave_obs", f"{verb} {s['left']} {pkg} {left_ver}")
    s.setdefault("confirm_cmd", f"rg -n '{left_ver}' {s['left_file']}")
    s.setdefault(
        "diffstat",
        f" {s['sot']} | 2\n {s['callsite']} | 2\n {s['left']} | 0\n",
    )
    s.setdefault(
        "inspect_obs",
        f"{s['sot']} {pkg} {old}\n{s['nested']} {pkg} {old}\n{s['left_file']} leftover {old}\n",
    )
    s.setdefault("sot_obs", s.get("sot_line", f"{pkg} {old}") + "\n")
    s.setdefault("nested_obs", s.get("nested_line", f"{pkg} {old}") + "\n")
    keep = (
        f"Ticket requires dropping leftover {s['left']} {left_ver}."
        if fail
        else f"Keep {s['left']} {left_ver}."
    )
    s.setdefault("ticket", f"docs/{s['slug']}.md")
    s.setdefault(
        "ticket_obs",
        f"# {pkg} {new}\n{s['api_break']}. {keep}\n",
    )
    s.setdefault("first_obs", f"{s['nested']} {pkg} {new} nested pin")
    s.setdefault("plan_obs", f"{s['sot']} {pkg} {new}")
    s.setdefault("companion_old", s["first_new"])
    s.setdefault("companion_obs", f"{s['nested']} realigned to SoT {pkg} {new}")
    s.setdefault("patch_obs", s["api_new"][:120])
    tests = s.setdefault("tests", 6 if fail else 4)
    s.setdefault("retest_obs", f"{tests} passed\n")
    s.setdefault(
        "goal",
        (
            f"Move {s['plant']} {s['surface']} {pkg} {old} → {new}. {s['api_break']}. "
            f"Ticket requires {s['left']} to drop {left_ver}."
            if fail
            else f"Bump {s['plant']} {s['surface']} {pkg} {old} → {new}. {s['api_break']}. Keep {s['left']} on {left_ver}."
        ),
    )
    s.setdefault(
        "plan",
        f"Pin only {s['nested']} to {new}; leave {s['sot']} {old} and leftover {s['left']}.",
    )
    s.setdefault(
        "outcome",
        (
            f"Nested {new} fought SoT {old}. Plan change: SoT {new}, {s['api_break']}. "
            f"Leftover-workspace fail: {s['left']} still {left_ver}."
            if fail
            else f"Nested {new} fought SoT {old}. Plan change: SoT {new}, {s['api_break']}. Residual: {s['left']} {left_ver}."
        ),
    )
    if fail:
        s.setdefault("ws_ok", "")
    else:
        s.setdefault("ws_fail", "")
    return s


def build_episode(round_n: int, spec: dict) -> dict:
    spec = fill(spec)
    slug = spec["slug"]
    for needle in BANNED_SLUG_NEEDLES:
        if needle in slug:
            raise SystemExit(f"banned slug needle {needle!r} in {slug}")
    eid = f"mdb-r{round_n}-{slug}"
    plant = spec["plant"]
    pkg = spec["pkg"]
    old, new = spec["old"], spec["new"]
    left_ver = spec.get("left_ver", old)
    fail = bool(spec["fail"])
    tests_n = int(spec.get("tests", 6 if fail else 4))
    left = spec["left"]
    api_break = spec["api_break"]

    steps = [
        bash(
            1,
            f"Plan: inspect {plant} {spec['surface']} layout before a nested-only bump.",
            spec["inspect_cmd"],
            spec["inspect_obs"],
        ),
        read(
            2,
            f"Observation: {pkg} {old} vs leftover {left_ver} (step 1). Read {spec['sot']}.",
            spec["sot"],
            spec["sot_obs"],
        ),
        read(
            3,
            f"Observation: SoT contents (step 2). Read nested {spec['nested']}.",
            spec["nested"],
            spec["nested_obs"],
        ),
        read(
            4,
            f"Observation: nested pin still old (step 3). Read ticket {spec['ticket']}.",
            spec["ticket"],
            spec["ticket_obs"],
        ),
        bash(
            5,
            f"Observation: ticket wants {pkg} {new} (step 4). Probe current resolver.",
            spec["probe_cmd"],
            spec["probe_obs"],
        ),
        edit(
            6,
            f"Plan: first apply — nested-only {pkg} {new} on {spec['nested']}.",
            spec["nested"],
            spec["first_old"],
            spec["first_new"],
            spec["first_obs"],
        ),
        bash(
            7,
            f"Observation: nested now {new} (step 6). Re-run in-scope resolver.",
            spec["fail_cmd"],
            spec["fail_obs"],
            reflection=f"Apply failed. Nested {new} diverged from SoT {old} and leftover {left_ver}.",
        ),
        edit(
            8,
            f"Reflection: plan change after nested fail — bump root SoT {pkg} to {new}.",
            spec["sot"],
            spec["plan_old"],
            spec["plan_new"],
            spec["plan_obs"],
        ),
        edit(
            9,
            f"Observation: root SoT bumped (step 8). Align {spec['nested']}.",
            spec["nested"],
            spec["companion_old"],
            spec["companion_new"],
            spec["companion_obs"],
        ),
        bash(
            10,
            "Observation: companion aligned (step 9). Re-run in-scope tests.",
            spec["test_cmd"],
            spec["api_fail_obs"],
            reflection=f"Edit→test fail: {api_break}.",
        ),
        read(
            11,
            f"Observation: API/config break (step 10). Read {spec['callsite']}.",
            spec["callsite"],
            spec["callsite_obs"],
        ),
        edit(
            12,
            f"Observation: {api_break} (step 11). Patch call site.",
            spec["callsite"],
            spec["api_old"],
            spec["api_new"],
            spec["patch_obs"],
        ),
        bash(
            13,
            "Observation: call site patched (step 12). Re-test in-scope packages.",
            spec["retest_cmd"],
            spec["retest_obs"],
        ),
        bash(
            14,
            f"Observation: in-scope green (step 13). Scan leftover {left}.",
            spec["scan_cmd"],
            spec["scan_obs"],
        ),
        bash(
            15,
            (
                f"Observation: leftover {left} still {left_ver} (step 14). "
                + (
                    "Ticket required dropping leftover; leave it."
                    if fail
                    else "Leave leftover as ticket allows."
                )
            ),
            spec["leave_cmd"],
            spec["leave_obs"],
        ),
        bash(
            16,
            "Observation: leftover decision recorded (step 15). Full workspace probe.",
            spec["ws_cmd"],
            spec["ws_fail"] if fail else spec["ws_ok"],
            reflection=(
                f"Leftover-workspace fail: {left} still {left_ver} vs {new}."
                if fail
                else f"{pkg} {new} in-scope. Residual: {left} {left_ver}."
            ),
        ),
        bash(
            17,
            "Observation: workspace probe (step 16). Diffstat the bump.",
            "git diff --stat",
            spec["diffstat"],
        ),
        bash(
            18,
            f"Observation: diffstat (step 17). Confirm leftover {left} {left_ver}.",
            spec["confirm_cmd"],
            spec["confirm_obs"],
            reflection=(
                f"{pkg} {new} + {api_break}. Leftover {left} {left_ver} fails the ticket."
                if fail
                else f"{pkg} {new} + {api_break}. Residual: {left} {left_ver}."
            ),
        ),
    ]
    if not (16 <= len(steps) <= 20):
        raise SystemExit(f"{eid} expected 16-20 steps, got {len(steps)}")

    return {
        "id": eid,
        "goal": spec["goal"],
        "plan": spec["plan"],
        "steps": steps,
        "outcome": spec["outcome"],
        "reward": {
            "success": not fail,
            "plan_changes": 1,
            "first_apply_fails": 1,
            "leftover_workspace_fail": 1 if fail else 0,
            "tests_passed": tests_n,
            "cost_steps": len(steps),
        },
        "meta": {"factory": FACTORY, "round": round_n, "generator": GEN},
    }


def notes_for(round_n: int, a: dict, b: dict) -> str:
    ea = f"mdb-r{round_n}-{a['slug']}"
    eb = f"mdb-r{round_n}-{b['slug']}"
    novel = 87 + (round_n % 6)
    return f"""# NOTES-r{round_n} monorepo-dep-bump-factory

Novel coverage: {novel}%

Two designed episodes (quota 2). Surfaces: {a['surface']} ({a['pkg']} {a['api_break']}); {b['surface']} ({b['pkg']} {b['api_break']}).
Not a pin-file mill and not libNNNN recycle. Distinct from r01–r775 clones (no pnpm/zod/changesets/maven/gradle/go.work/uv/poetry/turbo/cargo-patch/yarn/bun/nx/macports-python39/hy-assoc).

| id | seed | first apply | plan change | terminal |
|---|---|---|---|---|
| {ea} | {a['surface']} | nested {a['new']} | SoT {a['new']} + {a['api_break']} | {'leftover-workspace fail; ' + a['left'] + ' ' + a.get('left_ver', a['old']) if a['fail'] else 'success; ' + a['left'] + ' leftover'} |
| {eb} | {b['surface']} | nested {b['new']} | SoT {b['new']} + {b['api_break']} | {'leftover-workspace fail; ' + b['left'] + ' ' + b.get('left_ver', b['old']) if b['fail'] else 'success; ' + b['left'] + ' leftover'} |

## Step counts
- ep1: 18. Nested apply 6–7; plan change 8; API break 10–12; leftover {a['left']}.
- ep2: 18. Nested apply 6–7; plan change 8; API break 10–12; leftover-workspace fail {b['left']}.

## decision_basis audit
Every step starts Plan:/Observation:/Reflection:, ≤240 chars.
No thought / chain_of_thought / scratch / inner_monologue. No spike_events.
No sim_or_real: real. Plants `{a['plant']}` and `{b['plant']}`.

## Weaknesses / next
Keep unique leftover plots. Ban r01–r775 clones, libNNNN, Mix/Elixir, Conan/Hunter/vcpkg/Meson wrap/CMake FetchContent.
"""


def P(
    slug: str,
    plant: str,
    surface: str,
    pkg: str,
    old: str,
    new: str,
    fail: bool,
    sot: str,
    nested: str,
    sot_old: str,
    sot_new: str,
    nest_old: str,
    nest_new: str,
    api_old: str,
    api_new: str,
    api_break: str,
    tool: str,
    test: str,
    ws: str,
    callsite: str,
    companion_new: str | None = None,
) -> dict:
    left = "apps/legacy"
    left_file = f"{left}/{Path(sot).name}"
    return {
        "slug": slug,
        "plant": plant,
        "surface": surface,
        "pkg": pkg,
        "old": old,
        "new": new,
        "fail": fail,
        "sot": sot,
        "nested": nested,
        "left": left,
        "left_file": left_file,
        "sot_line": sot_old,
        "nested_line": nest_old,
        "probe_cmd": f"{tool}; rg '{old}|{new}|{pkg}' {sot} {nested} {left_file} | head",
        "probe_obs": f"{sot} {pkg} {old}\nlegacy leftover {old}\n",
        "first_old": nest_old,
        "first_new": nest_new,
        "fail_cmd": f"{test} 2>&1 | tail -n 16",
        "fail_obs": f"error: {nested} wants {pkg} {new} vs {sot} still {old}\n",
        "plan_old": sot_old,
        "plan_new": sot_new,
        "companion_new": companion_new if companion_new is not None else nest_new,
        "test_cmd": f"{test} 2>&1 | tail -n 16",
        "api_fail_obs": f"error: {api_break} ({pkg} {new}; leftover still {old})\n",
        "callsite": callsite,
        "callsite_obs": api_old + "\n",
        "api_old": api_old,
        "api_new": api_new,
        "api_break": api_break,
        "retest_cmd": f"{test} 2>&1 | tail -n 8",
        "scan_obs": f"{sot} {pkg} {new}\n{left_file} leftover {old}\n",
        "ws_cmd": f"{ws} 2>&1 | tail -n 16",
        "ws_ok": f"api 4 passed\nlegacy {pkg} {old} skipped (ticket allows)\n",
        "ws_fail": f"api 6 passed\nFAIL leftover {left} {pkg} {old} vs {new} {api_old}\n",
        "confirm_obs": old,
    }


# Each pair: (success, leftover-workspace fail). Index = round - 776.
PAIRS: list[tuple[dict, dict]] = [
    (
        P("ansible-galaxy-leftover-k8score", "dunlin", "Ansible galaxy.yml leftover vs collections/requirements.yml", "community.kubernetes", "2.0.1", "5.0.0", False, "galaxy.yml", "apps/api/requirements.yml", "community.kubernetes: 2.0.1", "kubernetes.core: 5.0.0", "  - name: community.kubernetes", "  - name: kubernetes.core", "k8s:", "kubernetes.core.k8s:", "k8s → kubernetes.core.k8s", "ansible-galaxy --version | head -n 1", "ansible-playbook apps/api/site.yml --syntax-check", "ansible-playbook apps/legacy/site.yml --syntax-check", "apps/api/tasks/dunlin.yml"),
        P("salt-pillar-leftover-pkglatest", "eagle", "Salt formulas leftover vs pillar", "salt", "3005.1", "3007.1", True, "pillar/top.sls", "apps/api/init.sls", "salt: 3005.1", "salt: 3007.1", "pkg.latest:", "pkg.installed:", "pkg.latest", "pkg.installed", "pkg.latest → pkg.installed", "salt --version | head -n 1", "salt-call --local state.apply apps.api", "salt-call --local state.apply apps.legacy", "apps/api/states/eagle.sls"),
    ),
    (
        P("chef-berks-leftover-nodeset", "egret", "Chef Berksfile.lock leftover vs Policyfile.lock", "chef", "17.10.0", "18.5.0", False, "Berksfile.lock", "apps/api/Policyfile.lock.json", "chef (17.10.0)", "chef (18.5.0)", "    chef: 17.10.0", "    chef: 18.5.0", "node.set[:api] = n", "node.default[:api] = n", "node.set → node.default", "chef --version | head -n 1", "chef exec rspec apps/api", "chef exec rspec apps/legacy", "apps/api/recipes/egret.rb"),
        P("puppet-puppetfile-leftover-validate", "falcon", "Puppet Puppetfile.lock leftover vs metadata.json", "puppetlabs-stdlib", "8.6.0", "9.6.0", True, "Puppetfile.lock", "apps/api/metadata.json", "PUPPETLABS-STDLIB (8.6.0)", "PUPPETLABS-STDLIB (9.6.0)", '"version": "8.6.0"', '"version": "9.6.0"', "validate_string($name)", "assert_type(String, $name)", "validate_string → assert_type String", "puppet --version", "puppet parser validate apps/api/manifests", "puppet parser validate apps/legacy/manifests", "apps/api/manifests/falcon.pp"),
    ),
    (
        P("snapcraft-yaml-leftover-ctl", "flamingo", "Snapcraft snapcraft.yaml leftover vs snapcraftctl", "snapcraft", "7.5.4", "8.4.3", False, "snapcraft.yaml", "apps/api/snapcraft.yaml", "base: core20\n# snapcraft 7.5.4", "base: core24\n# snapcraft 8.4.3", "override-pull: snapcraftctl pull", "override-pull: craftctl default", "snapcraftctl set-version $VER", "craftctl set version=$VER", "snapcraftctl → craftctl", "snapcraft --version", "snapcraft --destructive-mode apps/api", "snapcraft --destructive-mode apps/legacy", "apps/api/snap/flamingo.sh"),
        P("flatpak-manifest-leftover-sdk", "gadwall", "Flatpak flathub leftover vs appdata", "org.freedesktop.Platform", "22.08", "24.08", True, "flathub.json", "apps/api/com.gadwall.Api.json", '"runtime-version": "22.08"', '"runtime-version": "24.08"', '"sdk": "org.freedesktop.Sdk//22.08"', '"sdk": "org.freedesktop.Sdk//24.08"', '"--filesystem=home"', '"--filesystem=home:ro"', "finish-args home → home:ro", "flatpak --version", "flatpak-builder --force-clean /tmp/api apps/api/com.gadwall.Api.json", "flatpak-builder --force-clean /tmp/legacy apps/legacy/com.gadwall.Legacy.json", "apps/api/finish-args.json"),
    ),
    (
        P("pkgsrc-mk-leftover-replacepy", "gannet", "pkgsrc Makefile leftover vs distinfo", "python", "3.9.18", "3.12.8", False, "mk/python.mk", "apps/api/Makefile", "PYTHON_VERSION_DEFAULT= 39", "PYTHON_VERSION_DEFAULT= 312", "PYTHON_VERSIONS_ACCEPTED= 39", "PYTHON_VERSIONS_ACCEPTED= 312", "REPLACE_PYTHON+= bin/api", "REPLACE_PYTHON.bin+= bin/api", "REPLACE_PYTHON → REPLACE_PYTHON.bin", "pkg_info -V | head -n 1", "bmake -C apps/api test", "bmake -C apps/legacy test", "apps/api/gannet.mk"),
        P("portage-ebuild-leftover-eapi", "godwit", "Portage ebuild leftover vs Manifest", "EAPI", "6", "8", True, "profiles/eapi", "apps/api/api-1.ebuild", "EAPI=6", "EAPI=8", "inherit eutils", "inherit edo", "epatch \"${FILESDIR}/fix.patch\"", "eapply \"${FILESDIR}/fix.patch\"", "epatch → eapply", "emerge --info | head -n 1", "ebuild apps/api/api-1.ebuild test", "ebuild apps/legacy/legacy-1.ebuild test", "apps/api/files/godwit.ebuild"),
    ),
    (
        P("alpine-apkbuild-leftover-py2", "grebe", "Alpine APKBUILD leftover vs APKINDEX", "python2", "2.7.18", "3.12.8", False, "APKINDEX", "apps/api/APKBUILD", "python2-2.7.18-r0", "python3-3.12.8-r0", 'makedepends="python2 py2-setuptools"', 'makedepends="python3 py3-setuptools"', "python2 setup.py build", "python3 -m build", "python2 → python3", "apk --version", "abuild -r apps/api", "abuild -r apps/legacy", "apps/api/grebe.sh"),
        P("freebsd-ports-leftover-uses", "grouse", "FreeBSD ports leftover vs distinfo", "python", "3.9", "3.11", True, "Mk/bsd.python.mk", "apps/api/Makefile", "PYTHON_DEFAULT= 3.9", "PYTHON_DEFAULT= 3.11", "USES= python:3.9", "USES= python:3.11", "FLAVOR= py39", "FLAVOR= py311", "USES python:3.9 → 3.11", "pkg -v", "make -C apps/api test", "make -C apps/legacy test", "apps/api/grouse.mk"),
    ),
    (
        P("fuchsia-cipd-leftover-fidl", "harrier", "Fuchsia CIPD leftover vs jiri manifest", "fuchsia_sdk", "12.20240122", "18.20250115", False, "jiri.lock", "apps/api/meta/fidl", "fuchsia_sdk 12.20240122", "fuchsia_sdk 18.20250115", "library harrier { strict union X { 1: int32 a; }; }", "library harrier { flexible union X { 1: int32 a; }; }", "zx_handle_close(h);", "zx_handle_close_many(&h, 1);", "zx_handle_close → zx_handle_close_many", "jiri -version", "fx test //apps/api:harrier", "fx test //apps/legacy:legacy", "apps/api/src/harrier.cc"),
        P("serenity-ports-leftover-lagom", "heron", "SerenityOS Ports leftover vs package.sh", "Lagom", "1.0.0", "2.0.0", True, "Ports/package.sh", "apps/api/package.sh", "LAGOM_VERSION=1.0.0", "LADYBIRD_VERSION=2.0.0", "depends=\"Lagom\"", "depends=\"Ladybird\"", "GUI::Application::the()", "Ladybird::App::the()", "LibGUI::Application → Ladybird::App", "Meta/serenity.sh --version", "Meta/serenity.sh test apps/api", "Meta/serenity.sh test apps/legacy", "apps/api/src/heron.cpp"),
    ),
    (
        P("riot-makefile-leftover-xtimer", "ibis", "RIOT OS leftover vs Makefile.include", "riot", "2022.07", "2024.10", False, "Makefile.include", "apps/api/Makefile", "RIOT_VERSION = 2022.07", "RIOT_VERSION = 2024.10", "USEMODULE += xtimer", "USEMODULE += ztimer_usec", "xtimer_usleep(1000);", "ztimer_sleep(ZTIMER_USEC, 1000);", "xtimer → ztimer", "make --version | head -n 1", "make -C apps/api test", "make -C apps/legacy test", "apps/api/ibis.c"),
        P("contiki-ng-leftover-rpl", "jacana", "Contiki-NG leftover vs Makefile", "contiki-ng", "4.8", "5.0", True, "Makefile.identify-target", "apps/api/Makefile", "CONTIKI_VERSION = 4.8", "CONTIKI_VERSION = 5.0", "MAKE_ROUTING = MAKE_ROUTING_RPL_CLASSIC", "MAKE_ROUTING = MAKE_ROUTING_RPL_LITE", "uip_ipaddr(&ip, a, b, c, d);", "uip_ip6addr(&ip, a, b, c, d, 0, 0, 0, 0);", "rpl-classic uip_ipaddr → rpl-lite uip_ip6addr", "make -C apps/api TARGET=native version", "make -C apps/api TARGET=native test", "make -C apps/legacy TARGET=native test", "apps/api/jacana.c"),
    ),
    (
        P("nuttx-defconfig-leftover-nsh", "jay", "NuttX leftover vs defconfig", "nuttx", "11.0.0", "12.6.0", False, "defconfig", "apps/api/defconfig", "CONFIG_VERSION_STRING=\"11.0.0\"", "CONFIG_VERSION_STRING=\"12.6.0\"", "CONFIG_NSH_CONSOLE=y", "CONFIG_SYSTEM_NSH=y", "nsh_consolemain(0, NULL);", "nsh_main(0, NULL);", "nsh_consolemain → nsh_main", "nuttx --version || true", "make -C apps/api test", "make -C apps/legacy test", "apps/api/jay.c"),
        P("freertos-config-leftover-tick", "kestrel", "FreeRTOS leftover vs FreeRTOSConfig.h", "FreeRTOS", "10.4.6", "11.1.0", True, "FreeRTOSConfig.h", "apps/api/FreeRTOSConfig.h", "#define tskKERNEL_VERSION_NUMBER \"10.4.6\"", "#define tskKERNEL_VERSION_NUMBER \"11.1.0\"", "#define configUSE_PREEMPTION 1", "#define configUSE_PREEMPTION 1 /* 11.1 */", "vTaskDelay(pdMS_TO_TICKS(10) / portTICK_RATE_MS);", "vTaskDelay(pdMS_TO_TICKS(10));", "portTICK_RATE_MS → portTICK_PERIOD_MS", "arm-none-eabi-gcc --version | head -n 1", "make -C apps/api test", "make -C apps/legacy test", "apps/api/kestrel.c"),
    ),
    (
        P("sel4-camkes-leftover-wait", "killdeer", "seL4 leftover vs camkes", "seL4", "12.1.0", "13.0.0", False, "kernel/VERSION", "apps/api/api.camkes", "12.1.0", "13.0.0", "uses seL4Notification n;", "uses seL4Notification n; /* 13 */", "seL4_Wait(ep, &badge);", "seL4_Recv(ep, &badge);", "seL4_Wait → seL4_Recv", "python3 -c 'import camkes' || true", "make -C apps/api test", "make -C apps/legacy test", "apps/api/src/killdeer.c"),
        P("genode-run-leftover-nitpicker", "kingfisher", "Genode leftover vs run script", "genode", "23.05", "24.11", True, "repos/base/version", "apps/api/run/api.run", "23.05", "24.11", "build \"app/nitpicker\"", "build \"app/gui_session\"", "Nitpicker::Connection nit;", "Gui::Connection gui;", "Nitpicker::Connection → Gui::Connection", "tool/run --version || true", "tool/run apps/api/run/api.run", "tool/run apps/legacy/run/legacy.run", "apps/api/src/kingfisher.cc"),
    ),
    (
        P("micropython-manifest-leftover-uasyncio", "kite", "MicroPython leftover vs manifest.py", "micropython", "1.19.1", "1.24.1", False, "manifest.py", "apps/api/manifest.py", "freeze('uasyncio', version='1.19.1')", "freeze('asyncio', version='1.24.1')", "require('uasyncio')", "require('asyncio')", "import uasyncio as asyncio", "import asyncio", "uasyncio → asyncio", "micropython --version", "micropython apps/api/tests.py", "micropython apps/legacy/tests.py", "apps/api/kite.py"),
        P("circuitpython-req-leftover-group", "lapwing", "CircuitPython leftover vs requirements", "circuitpython", "8.2.10", "9.2.1", True, "requirements.txt", "apps/api/requirements.txt", "circuitpython==8.2.10", "circuitpython==9.2.1", "adafruit-blinka==8.2.10", "adafruit-blinka==9.2.1", "g = displayio.Group(max_size=8)", "g = displayio.Group()", "displayio.Group(max_size=) removed", "circup --version || true", "circup install -r apps/api/requirements.txt", "circup install -r apps/legacy/requirements.txt", "apps/api/code.py"),
    ),
    (
        P("isabelle-root-leftover-simp", "lark", "Isabelle leftover vs ROOT", "Isabelle", "2022", "2024", False, "ROOT", "apps/api/ROOT", "session Api = HOL + (* Isabelle2022 *)", "session Api = HOL + (* Isabelle2024 *)", "theories Api", "theories Api (* 2024 *)", "by (simp add: api_def)", "by (simp only: api_def)", "simp add → simp only", "isabelle version", "isabelle build -d apps/api Api", "isabelle build -d apps/legacy Legacy", "apps/api/Lark.thy"),
        P("dafny-dfyconfig-leftover-fnmethod", "loon", "Dafny leftover vs dfyconfig.toml", "dafny", "3.9.1", "4.8.0", True, "dfyconfig.toml", "apps/api/dfyconfig.toml", 'dafny-version = "3.9.1"', 'dafny-version = "4.8.0"', "includes = [\"src/**/*.dfy\"]", "includes = [\"src/**/*.dfy\"] # 4.8", "function method Foo(): int { 1 }", "function Foo(): int { 1 }", "function method → function", "dafny --version", "dafny test apps/api", "dafny test apps/legacy", "apps/api/src/Loon.dfy"),
    ),
    (
        P("fstar-fst-leftover-hyperstack", "magpie", "F* leftover vs fstar.fsti", "fstar", "2022.03.10", "2025.03.01", False, "fstar.fsti", "apps/api/Api.fst", "module Api (* fstar 2022.03.10 *)", "module Api (* fstar 2025.03.01 *)", "open FStar.HyperStack", "open FStar.HyperStack.ST", "let _ = FStar.HyperStack.push_frame ()", "let _ = FStar.HyperStack.ST.push_frame ()", "FStar.HyperStack.push_frame → ST.push_frame", "fstar.exe --version", "fstar.exe apps/api/Api.fst", "fstar.exe apps/legacy/Legacy.fst", "apps/api/Magpie.fst"),
        P("why3-conf-leftover-altergo", "mallard", "Why3 leftover vs why3.conf", "why3", "1.5.1", "1.7.2", True, "why3.conf", "apps/api/why3.conf", "[main] version = 1.5.1", "[main] version = 1.7.2", "prover = \"Alt-Ergo\"", "prover = \"CVC5\"", "why3 prove -P alt-ergo", "why3 prove -P cvc5", "Alt-Ergo → CVC5", "why3 --version", "why3 prove apps/api/api.mlw", "why3 prove apps/legacy/legacy.mlw", "apps/api/mallard.mlw"),
    ),
    (
        P("verilator-flags-leftover-trace", "merlin", "Verilator leftover vs verilator.f", "verilator", "4.228", "5.028", False, "verilator.f", "apps/api/verilator.f", "--cc --trace // 4.228", "--cc --trace-fst // 5.028", "--trace", "--trace-fst", "VerilatedVcdC* tfp = new VerilatedVcdC;", "VerilatedFstC* tfp = new VerilatedFstC;", "VerilatedVcdC → VerilatedFstC", "verilator --version", "verilator --lint-only apps/api/api.v", "verilator --lint-only apps/legacy/legacy.v", "apps/api/sim/merlin.cpp"),
        P("yosys-synth-leftover-blif", "nighthawk", "Yosys leftover vs Makefile", "yosys", "0.17", "0.44", True, "synth.ys", "apps/api/synth.ys", "yosys -V 0.17", "yosys -V 0.44", "synth_ice40 -blif api.blif", "synth_ice40 -json api.json", "write_blif api.blif", "write_json api.json", "write_blif → write_json", "yosys -V", "yosys -q apps/api/synth.ys", "yosys -q apps/legacy/synth.ys", "apps/api/nighthawk.v"),
    ),
    (
        P("openroad-pdn-leftover-pdngen", "osprey", "OpenROAD leftover vs config.mk", "openroad", "2.0", "2.1", False, "config.mk", "apps/api/config.mk", "OPENROAD_VERSION = 2.0", "OPENROAD_VERSION = 2.1", "include $(PDN_TCL)", "include $(PDNGEN_TCL)", "pdn::set_voltage_domain -name CORE", "ord::set_voltage_domain -name CORE", "pdn:: → ord::", "openroad -version", "openroad -exit apps/api/pdn.tcl", "openroad -exit apps/legacy/pdn.tcl", "apps/api/pdn.tcl"),
        P("klayout-lym-leftover-rba", "owl", "KLayout leftover vs lym", "klayout", "0.27.11", "0.29.8", True, "klayout.lym", "apps/api/api.lym", "# klayout 0.27.11", "# klayout 0.29.8", "module RBA", "module pya", "RBA::CellView.active", "pya.CellView.active", "RBA:: → pya.", "klayout -v", "klayout -b -r apps/api/api.lym", "klayout -b -r apps/legacy/legacy.lym", "apps/api/owl.rb"),
    ),
    (
        P("openfoam-wmake-leftover-dim", "oystercatcher", "OpenFOAM leftover vs Allwmake", "OpenFOAM", "9", "12", False, "etc/bashrc", "apps/api/Allwmake", "export WM_PROJECT_VERSION=9", "export WM_PROJECT_VERSION=12", "wmake libso", "wmake -j libso", "dimensionedScalar k(\"k\", dimless, 1);", "dimensioned<scalar> k(\"k\", dimless, 1);", "dimensionedScalar → dimensioned<scalar>", "foamVersion || true", "wmake -C apps/api test", "wmake -C apps/legacy test", "apps/api/src/oystercatcher.C"),
        P("fenics-dolfin-leftover-x", "parrot", "FEniCS leftover vs pyproject", "fenics-dolfin", "2019.1.0", "0.8.0", True, "pyproject.toml", "apps/api/pyproject.toml", 'fenics-dolfin = "2019.1.0"', 'fenics-dolfinx = "0.8.0"', "from dolfin import *", "import dolfinx", "from dolfin import Function", "from dolfinx.fem import Function", "dolfin.Function → dolfinx.fem.Function", "python3 -c 'import dolfinx' || true", "pytest -q apps/api", "pytest -q apps/legacy", "apps/api/src/parrot.py"),
    ),
    (
        P("petsc-makefile-leftover-vec", "pelican", "PETSc leftover vs makefile", "petsc", "3.18.6", "3.22.2", False, "petscconf.mk", "apps/api/makefile", "PETSC_VERSION = 3.18.6", "PETSC_VERSION = 3.22.2", "include ${PETSC_DIR}/lib/petsc/conf/variables", "include ${PETSC_DIR}/lib/petsc/conf/variables # 3.22", "VecCreateSeq(PETSC_COMM_SELF, n, &x);", "VecCreate(PETSC_COMM_SELF, &x); VecSetType(x, VECSEQ);", "VecCreateSeq → VecCreate+VecSetType", "petscmpiexec -n 1 true || true", "make -C apps/api test", "make -C apps/legacy test", "apps/api/pelican.c"),
        P("trilinos-cmake-leftover-epetra", "penguin", "Trilinos leftover vs CMakeLists", "trilinos", "13.4.1", "16.0.0", True, "CMakeLists.txt", "apps/api/CMakeLists.txt", "find_package(Trilinos 13.4.1 REQUIRED)", "find_package(Trilinos 16.0.0 REQUIRED)", "find_package(Epetra REQUIRED)", "find_package(Tpetra REQUIRED)", "Epetra_Vector x(map);", "Tpetra::Vector<double> x(map);", "Epetra_Vector → Tpetra::Vector", "cmake --version | head -n 1", "ctest --test-dir apps/api", "ctest --test-dir apps/legacy", "apps/api/src/penguin.cpp"),
    ),
    (
        P("kokkos-view-leftover-openmp", "peregrine", "Kokkos leftover vs CMakeLists", "kokkos", "3.7.1", "4.4.1", False, "CMakeLists.txt", "apps/api/CMakeLists.txt", "find_package(Kokkos 3.7.1 REQUIRED)", "find_package(Kokkos 4.4.1 REQUIRED)", "Kokkos::initialize(Kokkos::OpenMP());", "Kokkos::initialize(Kokkos::InitializationSettings());", "Kokkos::OpenMP exec;", "Kokkos::DefaultExecutionSpace exec;", "Kokkos::OpenMP() → DefaultExecutionSpace", "ctest --test-dir apps/api -N || true", "ctest --test-dir apps/api", "ctest --test-dir apps/legacy", "apps/api/src/peregrine.cpp"),
        P("sycl-cmake-leftover-clns", "petrel", "SYCL leftover vs CMakeLists", "intel-sycl", "2023.2.0", "2025.0.0", True, "CMakeLists.txt", "apps/api/CMakeLists.txt", "find_package(IntelSYCL 2023.2 REQUIRED)", "find_package(IntelSYCL 2025.0 REQUIRED)", "set(CMAKE_CXX_COMPILER dpcpp)", "set(CMAKE_CXX_COMPILER icpx)", "cl::sycl::queue q;", "sycl::queue q;", "cl::sycl::queue → sycl::queue", "icpx --version | head -n 1", "ctest --test-dir apps/api", "ctest --test-dir apps/legacy", "apps/api/src/petrel.cpp"),
    ),
    (
        P("hip-cmake-leftover-launch", "pheasant", "HIP leftover vs CMakeLists", "hip", "5.7.1", "6.2.4", False, "CMakeLists.txt", "apps/api/CMakeLists.txt", "find_package(hip 5.7.1 REQUIRED)", "find_package(hip 6.2.4 REQUIRED)", "hip_add_executable(api main.cpp)", "add_executable(api main.cpp)", "hipLaunchKernelGGL(k, dim3(1), dim3(1), 0, 0);", "hipLaunchKernelExC(k, dim3(1), dim3(1), 0, 0);", "hipLaunchKernelGGL → hipLaunchKernelExC", "hipcc --version | head -n 1", "ctest --test-dir apps/api", "ctest --test-dir apps/legacy", "apps/api/src/pheasant.hip"),
        P("oneapi-icpx-leftover-dpcpp", "pigeon", "oneAPI leftover vs CMakeLists", "dpcpp", "2023.2.0", "2025.0.0", True, "CMakeLists.txt", "apps/api/CMakeLists.txt", "set(CMAKE_CXX_COMPILER dpcpp) # 2023.2", "set(CMAKE_CXX_COMPILER icpx) # 2025.0", "add_compile_options(-fsycl)", "add_compile_options(-fsycl -fno-sycl-libspirv)", "dpcpp -fsycl main.cpp", "icpx -fsycl main.cpp", "dpcpp → icpx", "icpx --version | head -n 1", "ctest --test-dir apps/api", "ctest --test-dir apps/legacy", "apps/api/src/pigeon.cpp"),
    ),
    (
        P("charm-ck-leftover-callback", "pintail", "Charm++ leftover vs Makefile", "charm", "7.0.0", "8.0.0", False, "Makefile", "apps/api/Makefile", "CHARM_VERSION = 7.0.0", "CHARM_VERSION = 8.0.0", "CHARMC = charm7/bin/charmc", "CHARMC = charm8/bin/charmc", "CkCallbackResumeThread cb;", "CkCallback cb;", "CkCallbackResumeThread → CkCallback", "charmc -V || true", "make -C apps/api test", "make -C apps/legacy test", "apps/api/pintail.C"),
        P("upcxx-rpc-leftover-view", "plover", "UPC++ leftover vs Makefile", "upcxx", "2022.3.0", "2023.9.0", True, "Makefile", "apps/api/Makefile", "UPCXX_VERSION = 2022.3.0", "UPCXX_VERSION = 2023.9.0", "upcxx-meta CXX", "upcxx-meta CXX # 2023.9", "upcxx::make_view(buf, n)", "upcxx::view(buf, n)", "upcxx::make_view → upcxx::view", "upcxx --version || true", "make -C apps/api test", "make -C apps/legacy test", "apps/api/plover.cpp"),
    ),
    (
        P("tbb-parallel-leftover-taskinit", "puffin", "oneTBB leftover vs CMakeLists", "tbb", "2020.3", "2021.13", False, "CMakeLists.txt", "apps/api/CMakeLists.txt", "find_package(TBB 2020 REQUIRED)", "find_package(TBB 2021 REQUIRED)", "tbb::task_scheduler_init init;", "oneapi::tbb::global_control c(oneapi::tbb::global_control::max_allowed_parallelism, 4);", "tbb::task_scheduler_init init;", "oneapi::tbb::global_control c(oneapi::tbb::global_control::max_allowed_parallelism, 4);", "tbb::task_scheduler_init → oneapi::tbb::global_control", "ctest --test-dir apps/api -N || true", "ctest --test-dir apps/api", "ctest --test-dir apps/legacy", "apps/api/src/puffin.cpp"),
        P("hpx-async-leftover-dataflow", "rail", "HPX leftover vs CMakeLists", "hpx", "1.8.1", "1.10.0", True, "CMakeLists.txt", "apps/api/CMakeLists.txt", "find_package(HPX 1.8.1 REQUIRED)", "find_package(HPX 1.10.0 REQUIRED)", "hpx::dataflow(hpx::unwrapping(f), a, b)", "hpx::experimental::task_group g; g.run(f);", "hpx::dataflow(f, x)", "hpx::experimental::task_group{}.run(f)", "hpx::dataflow → task_group", "ctest --test-dir apps/api", "ctest --test-dir apps/api", "ctest --test-dir apps/legacy", "apps/api/src/rail.cpp"),
    ),
    (
        P("slurm-job-leftover-gres", "redhead", "SLURM leftover vs job.slurm", "slurm", "22.05.9", "24.11.1", False, "slurm.conf", "apps/api/job.slurm", "SlurmctldPort=6817 # 22.05.9", "SlurmctldPort=6817 # 24.11.1", "#SBATCH --gres=gpu:1", "#SBATCH --gpus=1", "#SBATCH --gres=gpu:1", "#SBATCH --gpus=1", "--gres=gpu → --gpus", "sbatch --version", "sbatch --test-only apps/api/job.slurm", "sbatch --test-only apps/legacy/job.slurm", "apps/api/redhead.slurm"),
        P("htcondor-submit-leftover-reqmem", "sandpiper", "HTCondor leftover vs submit", "condor", "9.0.17", "23.10.1", True, "condor_config", "apps/api/job.submit", "CONDOR_VERSION = 9.0.17", "CONDOR_VERSION = 23.10.1", "requirements = Memory > 2048", "request_memory = 2GB", "requirements = Memory > 2048", "request_memory = 2GB", "requirements Memory → request_memory", "condor_version", "condor_submit -dry-run apps/api/job.submit", "condor_submit -dry-run apps/legacy/job.submit", "apps/api/sandpiper.submit"),
    ),
    (
        P("sam-template-leftover-cfnresp", "scaup", "AWS SAM leftover vs template.yaml", "AWS::Serverless-2016-10-31", "python3.8", "python3.12", False, "template.yaml", "apps/api/template.yaml", "Runtime: python3.8", "Runtime: python3.12", "  Runtime: python3.8", "  Runtime: python3.12", "import cfnresponse", "from crhelper import CfnResource", "cfn-response → crhelper", "sam --version", "sam validate -t apps/api/template.yaml", "sam validate -t apps/legacy/template.yaml", "apps/api/src/scaup.py"),
        P("crossplane-comp-leftover-patches", "shrike", "Crossplane leftover vs composition.yaml", "crossplane", "1.14.5", "1.18.2", True, "composition.yaml", "apps/api/composition.yaml", "apiVersion: apiextensions.crossplane.io/v1 # 1.14.5", "apiVersion: apiextensions.crossplane.io/v1 # 1.18.2", "  patches:", "  pipeline:", "patches:", "pipeline:\n  - step: patch-and-transform", "patches → pipeline function-patch-and-transform", "kubectl explain composition --api-version=apiextensions.crossplane.io/v1 | head", "kubectl apply --dry-run=client -f apps/api/composition.yaml", "kubectl apply --dry-run=client -f apps/legacy/composition.yaml", "apps/api/shrike.yaml"),
    ),
    (
        P("flux-gitrepo-leftover-v1beta2", "snipe", "Flux leftover vs kustomization.yaml", "flux", "0.41.2", "2.4.0", False, "clusters/root/kustomization.yaml", "apps/api/gitrepository.yaml", "apiVersion: source.toolkit.fluxcd.io/v1beta2", "apiVersion: source.toolkit.fluxcd.io/v1", "kind: GitRepository", "kind: GitRepository # v1", "apiVersion: source.toolkit.fluxcd.io/v1beta2", "apiVersion: source.toolkit.fluxcd.io/v1", "source.toolkit v1beta2 → v1", "flux --version", "flux diff kustomization api --path apps/api", "flux diff kustomization legacy --path apps/legacy", "apps/api/snipe.yaml"),
        P("helmfile-needs-leftover-selectors", "stork", "Helmfile leftover vs helmfile.yaml", "helmfile", "0.151.0", "0.169.1", True, "helmfile.yaml", "apps/api/helmfile.yaml", "# helmfile 0.151.0", "# helmfile 0.169.1", "helmfiles:", "releases:", "helmfiles:\n  - path: nested.yaml", "releases:\n  - name: api\n    needs: [\"infra\"]", "helmfiles: → releases[].needs", "helmfile --version", "helmfile -f apps/api/helmfile.yaml lint", "helmfile -f apps/legacy/helmfile.yaml lint", "apps/api/stork.yaml"),
    ),
    (
        P("operatorsdk-project-leftover-v1a", "teal", "Operator SDK leftover vs PROJECT", "operator-sdk", "1.25.4", "1.38.0", False, "PROJECT", "apps/api/PROJECT", "version: \"3\"\nplugins:\n  go.sdk.operatorframework.io/v1-alpha: {}", "version: \"3\"\nplugins:\n  go.sdk.operatorframework.io/v1: {}", "domain: teal.dev\nlayout:\n  - go.kubebuilder.io/v3", "domain: teal.dev\nlayout:\n  - go.kubebuilder.io/v4", "apiVersion: teal.dev/v1alpha1", "apiVersion: teal.dev/v1", "v1alpha1 → v1", "operator-sdk version", "make -C apps/api test", "make -C apps/legacy test", "apps/api/api/v1alpha1/teal_types.go"),
        P("ivy-xml-leftover-revconstraint", "tern", "Apache Ivy leftover vs ivy.xml", "ivy", "2.4.0", "2.5.2", True, "ivy.xml", "apps/api/ivy.xml", '<ivy-module version="2.0"> <!-- ivy 2.4.0 -->', '<ivy-module version="2.0"> <!-- ivy 2.5.2 -->', '<dependency org="org.slf4j" name="slf4j-api" rev="1.7.36" revConstraint="[1.7,1.8["/>', '<dependency org="org.slf4j" name="slf4j-api" rev="2.0.16" force="true"/>', 'revConstraint="[1.7,1.8["', 'force="true"', "revConstraint → force", "java -jar ivy.jar -version", "ant -f apps/api/build.xml resolve", "ant -f apps/legacy/build.xml resolve", "apps/api/tern.ivy"),
    ),
    (
        P("nodegyp-binding-leftover-wrap", "toucan", "node-gyp leftover vs binding.gyp", "node-gyp", "9.4.1", "11.0.0", False, "binding.gyp", "apps/api/binding.gyp", '"node-gyp": "9.4.1"', '"node-gyp": "11.0.0"', '"sources": [ "src/api.cc" ]', '"sources": [ "src/api.cc" ] /* 11 */', "class Api : public node::ObjectWrap {", "class Api : public Napi::ObjectWrap<Api> {", "node::ObjectWrap → Napi::ObjectWrap", "node-gyp --version", "node-gyp rebuild --directory apps/api", "node-gyp rebuild --directory apps/legacy", "apps/api/src/toucan.cc"),
        P("wasi-sdk-leftover-preview1", "turkey", "WASI leftover vs wasi-sdk", "wasi-sdk", "19", "25", True, "wasi-sdk.version", "apps/api/Makefile", "WASI_SDK_VERSION=19", "WASI_SDK_VERSION=25", "clang --target=wasm32-wasi", "clang --target=wasm32-wasip2", "wasi_snapshot_preview1", "wasi:io/streams@0.2.0", "wasi-snapshot-preview1 → wasip2", "clang --version | head -n 1", "make -C apps/api test", "make -C apps/legacy test", "apps/api/turkey.c"),
    ),
    (
        P("wasmtime-toml-leftover-fuel", "vulture", "Wasmtime leftover vs wasmtime.toml", "wasmtime", "14.0.4", "27.0.0", False, "wasmtime.toml", "apps/api/wasmtime.toml", "version = \"14.0.4\"", "version = \"27.0.0\"", "wasm_simd = true", "wasm_relaxed_simd = true", "store.set_fuel(10_000)", "store.set_fuel(10_000).expect(\"fuel\")", "Store::set_fuel now Result", "wasmtime --version", "wasmtime run apps/api/api.wasm", "wasmtime run apps/legacy/legacy.wasm", "apps/api/src/vulture.rs"),
        P("wasmer-toml-leftover-mapdir", "willet", "Wasmer leftover vs wasmer.toml", "wasmer", "3.3.0", "4.4.0", True, "wasmer.toml", "apps/api/wasmer.toml", "wasmer = \"3.3.0\"", "wasmer = \"4.4.0\"", "mapdir = [\"/data:./data\"]", "fs = { \"/data\" = \"./data\" }", "wasmer run --mapdir /data:./data api.wasm", "wasmer run --dir ./data api.wasm", "--mapdir → --dir", "wasmer --version", "wasmer run apps/api/api.wasm", "wasmer run apps/legacy/legacy.wasm", "apps/api/willet.toml"),
    ),
    (
        P("cranelift-ir-leftover-abiparam", "woodpecker", "Cranelift leftover vs cranelift.toml", "cranelift", "0.99.2", "0.115.0", False, "cranelift.toml", "apps/api/cranelift.toml", "cranelift-codegen = \"0.99.2\"", "cranelift-codegen = \"0.115.0\"", "use cranelift_codegen::ir::AbiParam;", "use cranelift_codegen::ir::Signature;", "AbiParam::new(types::I32)", "Signature::new(CallConv::SystemV).params.push(AbiParam::new(types::I32))", "ir::AbiParam builder → Signature", "clif-util --version || true", "cargo test -p apps-api --manifest-path apps/api/Cargo.toml", "cargo test -p apps-legacy --manifest-path apps/legacy/Cargo.toml", "apps/api/src/woodpecker.rs"),
        P("quickjs-eval-leftover-this", "avocet", "QuickJS leftover vs Makefile", "quickjs", "2021-03-27", "2024-01-13", True, "VERSION", "apps/api/Makefile", "2021-03-27", "2024-01-13", "JS_Eval(ctx, src, len, name, flags)", "JS_EvalThis(ctx, this_val, src, len, name, flags)", "JS_Eval(ctx, src, len, \"api.js\", 0);", "JS_EvalThis(ctx, JS_UNDEFINED, src, len, \"api.js\", 0);", "JS_Eval → JS_EvalThis", "qjsc -v || true", "make -C apps/api test", "make -C apps/legacy test", "apps/api/avocet.c"),
    ),
    (
        P("duktape-peval-leftover-safe", "bobolink", "Duktape leftover vs Makefile", "duktape", "2.7.0", "3.0.0", False, "duktape.h", "apps/api/Makefile", "#define DUK_VERSION 20700", "#define DUK_VERSION 30000", "duk_peval_string(ctx, src)", "duk_pcompile_string(ctx, 0, src); duk_pcall(ctx, 0)", "duk_peval_string(ctx, src);", "duk_pcompile_string(ctx, 0, src); duk_pcall(ctx, 0);", "duk_peval_string → pcompile+pcall", "make -C apps/api -n || true", "make -C apps/api test", "make -C apps/legacy test", "apps/api/bobolink.c"),
        P("jerryscript-parse-leftover-fn", "canvasback", "JerryScript leftover vs CMake", "jerryscript", "2.4.0", "3.0.0", True, "CMakeLists.txt", "apps/api/CMakeLists.txt", "project(jerryscript VERSION 2.4.0)", "project(jerryscript VERSION 3.0.0)", "jerry_parse(src, len, JERRY_PARSE_NO_OPTS)", "jerry_parse_function(src, len, NULL, 0, JERRY_PARSE_NO_OPTS)", "jerry_parse(src, n, JERRY_PARSE_NO_OPTS);", "jerry_parse_function(src, n, NULL, 0, JERRY_PARSE_NO_OPTS);", "jerry_parse → jerry_parse_function", "ctest --test-dir apps/api -N || true", "ctest --test-dir apps/api", "ctest --test-dir apps/legacy", "apps/api/src/canvasback.c"),
    ),
    (
        P("vegalite-sel-leftover-param", "dipper", "Vega-Lite leftover vs vl.json", "vega-lite", "4.17.0", "5.21.0", False, "vl.json", "apps/api/vl.json", '"$schema": "https://vega.github.io/schema/vega-lite/v4.json"', '"$schema": "https://vega.github.io/schema/vega-lite/v5.json"', '"selection": { "brush": { "type": "interval" } }', '"params": [ { "name": "brush", "select": "interval" } ]', '"selection": {', '"params": [', "selection → params", "vl2png --version || true", "vl2png apps/api/vl.json /tmp/api.png", "vl2png apps/legacy/vl.json /tmp/legacy.png", "apps/api/dipper.json"),
        P("bokeh-charts-leftover-bar", "eider", "Bokeh leftover vs environment.yml", "bokeh", "2.4.3", "3.6.2", True, "environment.yml", "apps/api/environment.yml", "  - bokeh=2.4.3", "  - bokeh=3.6.2", "from bokeh.charts import Bar", "from bokeh.plotting import figure", "from bokeh.charts import Bar", "from bokeh.plotting import figure", "bokeh.charts.Bar removed", "python3 -c 'import bokeh; print(bokeh.__version__)' || true", "pytest -q apps/api", "pytest -q apps/legacy", "apps/api/src/eider.py"),
    ),
    (
        P("streamlit-rerun-leftover-exp", "firecrest", "Streamlit leftover vs requirements", "streamlit", "1.22.0", "1.41.1", False, "requirements.txt", "apps/api/requirements.txt", "streamlit==1.22.0", "streamlit==1.41.1", "st.experimental_rerun()", "st.rerun()", "st.experimental_rerun()", "st.rerun()", "st.experimental_rerun → st.rerun", "streamlit --version", "pytest -q apps/api", "pytest -q apps/legacy", "apps/api/src/firecrest.py"),
        P("gradio-inputs-leftover-queue", "goldfinch", "Gradio leftover vs requirements", "gradio", "3.50.2", "5.9.1", True, "requirements.txt", "apps/api/requirements.txt", "gradio==3.50.2", "gradio==5.9.1", "gr.inputs.Textbox()", "gr.Textbox()", "demo.launch(enable_queue=True)", "demo.launch()", "gr.inputs + enable_queue removed", "python3 -c 'import gradio' || true", "pytest -q apps/api", "pytest -q apps/legacy", "apps/api/src/goldfinch.py"),
    ),
    (
        P("dash-runserver-leftover-app", "hawfinch", "Dash leftover vs requirements", "dash", "2.9.3", "2.18.2", False, "requirements.txt", "apps/api/requirements.txt", "dash==2.9.3", "dash==2.18.2", "app.run_server(debug=True)", "app.run(debug=True)", "app.run_server(debug=True)", "app.run(debug=True)", "app.run_server → app.run", "python3 -c 'import dash' || true", "pytest -q apps/api", "pytest -q apps/legacy", "apps/api/src/hawfinch.py"),
        P("shiny-fluid-leftover-bslib", "indigo", "Shiny leftover vs renv.lock", "shiny", "1.7.4", "1.10.0", True, "renv.lock", "apps/api/renv.lock", '"Version": 1.7.4"', '"Version: 1.10.0"', "fluidPage(", "bslib::page_sidebar(", "fluidPage(", "bslib::page_sidebar(", "fluidPage → bslib::page_sidebar", "Rscript -e 'packageVersion(\"shiny\")' || true", "Rscript -e 'testthat::test_dir(\"apps/api/tests\")'", "Rscript -e 'testthat::test_dir(\"apps/legacy/tests\")'", "apps/api/app.R"),
    ),
    (
        P("htmx-oob-leftover-swap", "junco", "HTMX leftover vs package.json", "htmx", "1.9.10", "2.0.4", False, "package.json", "apps/api/package.json", '"htmx.org": "1.9.10"', '"htmx.org": "2.0.4"', "hx-swap-oob=\"true\"", "hx-swap-oob=\"outerHTML\"", "hx-swap-oob=\"true\"", "hx-swap-oob=\"outerHTML\"", "hx-swap-oob true → outerHTML", "npm --prefix apps/api ls htmx.org || true", "npm test --prefix apps/api", "npm test --prefix apps/legacy", "apps/api/src/junco.html"),
        P("alpinejs-spread-leftover-bind", "knot", "Alpine.js leftover vs package.json", "alpinejs", "2.8.2", "3.14.7", True, "package.json", "apps/api/package.json", '"alpinejs": "2.8.2"', '"alpinejs": "3.14.7"', "x-spread=\"attrs\"", "x-bind=\"attrs\"", "x-spread=\"attrs\"", "x-bind=\"attrs\"", "x-spread → x-bind", "npm --prefix apps/api ls alpinejs || true", "npm test --prefix apps/api", "npm test --prefix apps/legacy", "apps/api/src/knot.html"),
    ),
    (
        P("stimulus-targets-leftover-static", "linnet", "Stimulus leftover vs package.json", "stimulus", "1.1.1", "3.2.2", False, "package.json", "apps/api/package.json", '"stimulus": "1.1.1"', '"@hotwired/stimulus": "3.2.2"', "targets: [\"output\"]", "static targets = [\"output\"]", "targets: [\"output\"]", "static targets = [\"output\"]", "Controller.extend targets → static targets", "npm --prefix apps/api ls @hotwired/stimulus || true", "npm test --prefix apps/api", "npm test --prefix apps/legacy", "apps/api/src/linnet_controller.js"),
        P("livewire-defer-leftover-live", "meadowlark", "Livewire leftover vs composer.json", "livewire/livewire", "2.12.6", "3.5.12", True, "composer.json", "apps/api/composer.json", '"livewire/livewire": "2.12.6"', '"livewire/livewire": "3.5.12"', "wire:model.defer=\"q\"", "wire:model=\"q\"", "wire:model.defer=\"q\"", "wire:model=\"q\"", "wire:model.defer → wire:model", "composer --working-dir=apps/api show livewire/livewire || true", "php artisan test apps/api", "php artisan test apps/legacy", "apps/api/resources/views/meadowlark.blade.php"),
    ),
    (
        P("inertia-share-leftover-pkg", "nutcracker", "Inertia leftover vs package.json", "@inertiajs/inertia", "0.11.1", "2.0.3", False, "package.json", "apps/api/package.json", '"@inertiajs/inertia": "0.11.1"', '"@inertiajs/vue3": "2.0.3"', "Inertia.share({ user })", "Inertia::defer(fn () => [\"user\" => $u])", "Inertia::share([\"user\" => $u]);", "Inertia::defer(fn () => [\"user\" => $u]);", "Inertia::share → Inertia::defer", "npm --prefix apps/api ls @inertiajs/vue3 || true", "php artisan test apps/api", "php artisan test apps/legacy", "apps/api/app/Http/Middleware/Nutcracker.php"),
        P("pandoc-citeproc-leftover-cite", "oriole", "Pandoc leftover vs defaults.yaml", "pandoc", "2.19.2", "3.6.2", True, "defaults.yaml", "apps/api/defaults.yaml", "from: markdown\n# pandoc 2.19.2", "from: markdown\n# pandoc 3.6.2", "filters:\n  - pandoc-citeproc", "citeproc: true", "--filter pandoc-citeproc", "--citeproc", "pandoc-citeproc → --citeproc", "pandoc --version | head -n 1", "pandoc -d apps/api/defaults.yaml -o /tmp/api.html apps/api/doc.md", "pandoc -d apps/legacy/defaults.yaml -o /tmp/legacy.html apps/legacy/doc.md", "apps/api/oriole.md"),
    ),
    (
        P("quarto-knitr-leftover-crossref", "pipit", "Quarto leftover vs _quarto.yml", "quarto", "1.2.335", "1.6.40", False, "_quarto.yml", "apps/api/_quarto.yml", "project:\n  type: website # 1.2.335", "project:\n  type: website # 1.6.40", "execute:\n  engine: knitr", "execute:\n  engine: jupyter", "fig-cap: \"A\"", "fig-cap-location: bottom", "knitr + fig-cap → jupyter + fig-cap-location", "quarto --version", "quarto render apps/api", "quarto render apps/legacy", "apps/api/pipit.qmd"),
        P("observable-fw-leftover-require", "quetzal", "Observable Framework leftover vs observablehq.config.js", "@observablehq/framework", "1.7.0", "1.13.0", True, "observablehq.config.js", "apps/api/observablehq.config.js", "export default { title: \"api\" }; // 1.7.0", "export default { title: \"api\" }; // 1.13.0", "const d3 = require(\"d3\");", "import * as d3 from \"npm:d3\";", "require(\"d3\")", "import * as d3 from \"npm:d3\"", "require(d3) → npm:d3 import", "npx observable --version || true", "npm test --prefix apps/api", "npm test --prefix apps/legacy", "apps/api/src/quetzal.md"),
    ),
    (
        P("cfn-getatt-leftover-list", "redstart", "CloudFormation leftover vs template.yaml", "AWS::LanguageExtensions", "2021-08-01", "2024-12-01", False, "template.yaml", "apps/api/template.yaml", "Transform: AWS::LanguageExtensions # 2021-08-01", "Transform: AWS::LanguageExtensions # 2024-12-01", "Fn::GetAtt: [Bucket, Arn]", "Fn::GetAtt: Bucket.Arn", "!GetAtt [Bucket, Arn]", "!GetAtt Bucket.Arn", "Fn::GetAtt list → dotted string", "cfn-lint apps/api/template.yaml", "cfn-lint apps/api/template.yaml", "cfn-lint apps/legacy/template.yaml", "apps/api/redstart.yaml"),
        P("cdk-core-leftover-v1", "sapsucker", "AWS CDK leftover vs package.json", "aws-cdk-lib", "1.204.0", "2.173.0", True, "package.json", "apps/api/package.json", '"@aws-cdk/core": "1.204.0"', '"aws-cdk-lib": "2.173.0"', "import { Construct } from '@aws-cdk/core'", "import { Construct } from 'constructs'", "from '@aws-cdk/core'", "from 'aws-cdk-lib'", "@aws-cdk/core → aws-cdk-lib", "npx cdk --version", "npx cdk synth --app apps/api", "npx cdk synth --app apps/legacy", "apps/api/lib/sapsucker-stack.ts"),
    ),
    (
        P("antlr-g4-leftover-visitor", "treecreeper", "ANTLR leftover vs .g4", "antlr4", "4.9.3", "4.13.2", False, "Api.g4", "apps/api/Api.g4", "grammar Api; // 4.9.3", "grammar Api; // 4.13.2", "options { tokenVocab=ApiLexer; }", "options { tokenVocab=ApiLexer; superClass=ApiParserBase; }", "parse : expr EOF; // visitor", "parse : expr EOF; // listener default", "visitor TokenStream → listener + tokenVocab", "antlr4 -version", "antlr4 -Dlanguage=Java apps/api/Api.g4", "antlr4 -Dlanguage=Java apps/legacy/Legacy.g4", "apps/api/src/Treecreeper.java"),
        P("openapi-gen-leftover-apimodel", "verdin", "OpenAPI Generator leftover vs openapi-generator.yaml", "swagger-codegen", "3.0.36", "7.10.0", True, "openapi-generator.yaml", "apps/api/openapi-generator.yaml", "generatorName: java\n# swagger-codegen 3.0.36", "generatorName: java\n# openapi-generator 7.10.0", "library: resttemplate", "library: native", "@ApiModel(description = \"x\")", "@Schema(description = \"x\")", "@ApiModel → @Schema", "openapi-generator-cli version", "openapi-generator-cli generate -c apps/api/openapi-generator.yaml", "openapi-generator-cli generate -c apps/legacy/openapi-generator.yaml", "apps/api/src/Verdin.java"),
    ),
    (
        P("asyncapi-yaml-leftover-publish", "whydah", "AsyncAPI leftover vs asyncapi.yaml", "@asyncapi/generator", "1.9.17", "2.6.0", False, "asyncapi.yaml", "apps/api/asyncapi.yaml", "asyncapi: 2.6.0", "asyncapi: 3.0.0", "  publish:\n    message:\n      $ref: '#/components/messages/Evt'", "  send:\n    messages:\n      evt:\n        $ref: '#/components/messages/Evt'", "publish:", "send:", "channel publish → send/receive", "ag --version || true", "ag asyncapi.yaml @asyncapi/html-template -o /tmp/api", "ag apps/legacy/asyncapi.yaml @asyncapi/html-template -o /tmp/legacy", "apps/api/whydah.yaml"),
        P("jsonschema-draft-leftover-defs", "xenops", "JSON Schema leftover vs schema.json", "jsonschema", "draft-07", "2020-12", True, "schema.json", "apps/api/schema.json", '"$schema": "http://json-schema.org/draft-07/schema#"', '"$schema": "https://json-schema.org/draft/2020-12/schema"', '"definitions": { "Id": { "type": "string" } }', '"$defs": { "Id": { "type": "string" } }', '"$ref": "#/definitions/Id"', '"$ref": "#/$defs/Id"', "definitions → $defs", "check-jsonschema --version || true", "check-jsonschema --schemafile apps/api/schema.json apps/api/inst.json", "check-jsonschema --schemafile apps/legacy/schema.json apps/legacy/inst.json", "apps/api/xenops.schema.json"),
    ),
    (
        P("avro-schema-leftover-logical", "yellowhammer", "Apache Avro leftover vs avsc", "avro", "1.10.2", "1.12.0", False, "schema.avsc", "apps/api/schema.avsc", '"namespace": "api", "version": "1.10.2"', '"namespace": "api", "version": "1.12.0"', '"type": "int", "logicalType": "date"', '"type": "int", "logicalType": "date", "connect.name": "org.apache.kafka.connect.data.Date"', "GenericData.get().addLogicalTypeConversion(new TimeConversions.DateConversion());", "GenericData.get().addLogicalTypeConversion(new Conversions.DecimalConversion());", "TimeConversions → Conversions", "java -jar avro-tools.jar --help | head", "java -jar avro-tools.jar compile schema apps/api/schema.avsc /tmp/api", "java -jar avro-tools.jar compile schema apps/legacy/schema.avsc /tmp/legacy", "apps/api/src/Yellowhammer.java"),
        P("thrift-idl-leftover-pyns", "zosterops", "Apache Thrift leftover vs .thrift", "thrift", "0.16.0", "0.21.0", True, "api.thrift", "apps/api/api.thrift", "namespace py api # 0.16.0", "namespace py3 api # 0.21.0", "namespace py api", "namespace py3 api", "from api.ttypes import Evt", "from api.thrift_types import Evt", "namespace py → py3", "thrift --version", "thrift -gen py apps/api/api.thrift", "thrift -gen py apps/legacy/legacy.thrift", "apps/api/zosterops.thrift"),
    ),
    (
        P("capnproto-schema-leftover-root", "anhinga", "Cap'n Proto leftover vs .capnp", "capnproto", "0.10.4", "1.0.2", False, "api.capnp", "apps/api/api.capnp", "@0xdbb9ad1f14bf0b36; # 0.10.4", "@0xdbb9ad1f14bf0b36; # 1.0.2", "struct Evt { id @0 :UInt32; }", "struct Evt { id @0 :UInt64; }", "message.getRoot<Evt>()", "message.initRoot<Evt>()", "getRoot → initRoot", "capnp --version", "capnp compile -oc++ apps/api/api.capnp", "capnp compile -oc++ apps/legacy/legacy.capnp", "apps/api/src/anhinga.c++"),
        P("flatbuffers-fbs-leftover-shared", "booby", "FlatBuffers leftover vs .fbs", "flatbuffers", "2.0.8", "24.12.23", True, "api.fbs", "apps/api/api.fbs", "// flatc 2.0.8", "// flatc 24.12.23", "table Evt { name:string; }", "table Evt { name:shared_string; }", "builder.CreateString(name)", "builder.CreateSharedString(name)", "CreateString → CreateSharedString", "flatc --version", "flatc --cpp apps/api/api.fbs", "flatc --cpp apps/legacy/legacy.fbs", "apps/api/src/booby.cpp"),
    ),
    (
        P("msgpack-packb-leftover-encoding", "cormorant", "MessagePack leftover vs requirements", "msgpack", "1.0.4", "1.1.0", False, "requirements.txt", "apps/api/requirements.txt", "msgpack==1.0.4", "msgpack==1.1.0", "packb(obj, encoding='utf-8')", "packb(obj)", "packb(d, encoding='utf-8')", "packb(d)", "packb encoding= removed", "python3 -c 'import msgpack' || true", "pytest -q apps/api", "pytest -q apps/legacy", "apps/api/src/cormorant.py"),
        P("parquet-schema-leftover-int96", "dovekie", "Apache Parquet leftover vs schema", "parquet-mr", "1.12.3", "1.15.0", True, "schema.parquet.json", "apps/api/schema.parquet.json", '"created-by": "parquet-mr version 1.12.3"', '"created-by": "parquet-mr version 1.15.0"', '"type": "INT96"', '"type": "INT64", "logicalType": "TIMESTAMP(MICROS,false)"', "Types.optional(INT96).named(\"ts\")", "Types.optional(INT64).as(timestampType()).named(\"ts\")", "INT96 → INT64 TIMESTAMP_MICROS", "parquet-tools schema apps/api/t.parquet || true", "parquet-tools schema apps/api/t.parquet", "parquet-tools schema apps/legacy/t.parquet", "apps/api/src/Dovekie.java"),
    ),
    (
        P("arrow-dataset-leftover-legacy", "emu", "Apache Arrow leftover vs pyproject", "pyarrow", "10.0.1", "18.1.0", False, "pyproject.toml", "apps/api/pyproject.toml", 'pyarrow = "10.0.1"', 'pyarrow = "18.1.0"', "pq.read_table(path, use_legacy_dataset=True)", "ds.dataset(path).scanner().to_table()", "pq.read_table(p, use_legacy_dataset=True)", "ds.dataset(p).scanner().to_table()", "use_legacy_dataset removed", "python3 -c 'import pyarrow' || true", "pytest -q apps/api", "pytest -q apps/legacy", "apps/api/src/emu.py"),
        P("duckdb-pragma-leftover-threads", "frigatebird", "DuckDB leftover vs .duckdb", "duckdb", "0.7.1", "1.1.3", True, "init.sql", "apps/api/init.sql", "-- duckdb 0.7.1", "-- duckdb 1.1.3", "PRAGMA threads=4;", "SET threads=4;", "read_csv_auto('f.csv')", "read_csv('f.csv')", "PRAGMA threads + read_csv_auto → SET + read_csv", "duckdb --version", "duckdb apps/api/api.duckdb -c '.read apps/api/init.sql'", "duckdb apps/legacy/legacy.duckdb -c '.read apps/legacy/init.sql'", "apps/api/frigatebird.sql"),
    ),
    (
        P("clickhouse-xml-leftover-jsonextract", "goose", "ClickHouse leftover vs config.xml", "clickhouse", "22.8.15", "24.12.1", False, "config.xml", "apps/api/config.xml", "<yandex><!-- 22.8.15 -->", "<clickhouse><!-- 24.12.1 -->", "<yandex>", "<clickhouse>", "JSONExtract(raw, 'id', 'UInt64')", "JSONExtractString(raw, 'id')", "JSONExtract → JSONExtractString + yandex root", "clickhouse-client --version", "clickhouse-client --queries-file apps/api/q.sql", "clickhouse-client --queries-file apps/legacy/q.sql", "apps/api/goose.sql"),
        P("sqlite-json1-leftover-jsonb", "hoatzin", "SQLite leftover vs sqlite3", "sqlite", "3.37.2", "3.47.2", True, "schema.sql", "apps/api/schema.sql", "-- sqlite 3.37.2", "-- sqlite 3.47.2", "json_extract(doc, '$.id')", "doc ->> '$.id'", "json_extract(doc, '$.id')", "doc ->> '$.id'", "json_extract → ->> JSONB", "sqlite3 --version", "sqlite3 apps/api/api.db < apps/api/schema.sql", "sqlite3 apps/legacy/legacy.db < apps/legacy/schema.sql", "apps/api/hoatzin.sql"),
    ),
    (
        P("redis-conf-leftover-slaveof", "iwi", "Redis leftover vs redis.conf", "redis", "6.2.14", "7.4.1", False, "redis.conf", "apps/api/redis.conf", "redis_version 6.2.14", "redis_version 7.4.1", "slaveof 10.0.0.2 6379", "replicaof 10.0.0.2 6379", "SLAVEOF no one", "REPLICAOF no one", "SLAVEOF → REPLICAOF", "redis-server --version", "redis-server apps/api/redis.conf --test-memory 1", "redis-server apps/legacy/redis.conf --test-memory 1", "apps/api/iwi.conf"),
        P("kafka-server-leftover-zk", "jaeger", "Kafka leftover vs server.properties", "kafka", "2.8.2", "3.9.0", True, "server.properties", "apps/api/server.properties", "inter.broker.protocol.version=2.8", "inter.broker.protocol.version=3.9", "zookeeper.connect=zk:2181", "controller.quorum.voters=1@broker:9093", "zookeeper.connect=zk:2181", "controller.quorum.voters=1@broker:9093", "zookeeper.connect → controller.quorum.voters", "kafka-topics.sh --version || true", "kafka-storage.sh format -t $UUID -c apps/api/server.properties", "kafka-storage.sh format -t $UUID -c apps/legacy/server.properties", "apps/api/jaeger.properties"),
    ),
    (
        P("pulsar-broker-leftover-fnworker", "kiwi", "Pulsar leftover vs broker.conf", "pulsar", "2.10.4", "3.3.2", False, "broker.conf", "apps/api/broker.conf", "clusterName=api # 2.10.4", "clusterName=api # 3.3.2", "functionsWorkerEnabled=true", "functionsWorkerEnabled=false", "pulsar-admin functions localrun", "pulsar-admin functions-worker", "functions localrun → functions-worker", "pulsar-admin --version || true", "bin/pulsar broker -c apps/api/broker.conf --help", "bin/pulsar broker -c apps/legacy/broker.conf --help", "apps/api/kiwi.conf"),
        P("nats-conf-leftover-jetstream", "limpkin", "NATS leftover vs nats.conf", "nats-server", "2.9.25", "2.10.24", True, "nats.conf", "apps/api/nats.conf", "# nats-server 2.9.25", "# nats-server 2.10.24", "cluster { routes = [nats://n1:6222] }", "jetstream { store_dir: /data }", "cluster {", "jetstream { store_dir: /data }", "cluster routes → jetstream store_dir", "nats-server --version", "nats-server -c apps/api/nats.conf -t", "nats-server -c apps/legacy/nats.conf -t", "apps/api/limpkin.conf"),
    ),
    (
        P("rabbitmq-conf-leftover-hamode", "moa", "RabbitMQ leftover vs rabbitmq.conf", "rabbitmq", "3.9.29", "4.0.5", False, "rabbitmq.conf", "apps/api/rabbitmq.conf", "# rabbitmq 3.9.29", "# rabbitmq 4.0.5", "ha-mode = all", "x-queue-type = quorum", "ha-mode = all", "x-queue-type = quorum", "ha-mode → x-queue-type quorum", "rabbitmqctl version", "rabbitmq-diagnostics check_running -n api || true", "rabbitmq-diagnostics check_running -n legacy || true", "apps/api/moa.conf"),
        P("consul-hcl-leftover-aclmaster", "noddy", "Consul leftover vs consul.hcl", "consul", "1.14.7", "1.20.2", True, "consul.hcl", "apps/api/consul.hcl", "# consul 1.14.7", "# consul 1.20.2", "acl_master_token = \"root\"", "acl { tokens { initial_management = \"root\" } }", "acl_master_token = \"root\"", "acl { tokens { initial_management = \"root\" } }", "acl_master_token → initial_management", "consul version", "consul validate apps/api/consul.hcl", "consul validate apps/legacy/consul.hcl", "apps/api/noddy.hcl"),
    ),
    (
        P("nomad-hcl-leftover-rawexec", "oilbird", "Nomad leftover vs nomad.hcl", "nomad", "1.4.12", "1.9.5", False, "nomad.hcl", "apps/api/job.hcl", "# nomad 1.4.12", "# nomad 1.9.5", "driver = \"raw_exec\"", "driver = \"exec\"", "driver = \"raw_exec\"", "driver = \"exec\"", "raw_exec → exec", "nomad version", "nomad job validate apps/api/job.hcl", "nomad job validate apps/legacy/job.hcl", "apps/api/oilbird.hcl"),
        P("vault-hcl-leftover-kv1", "ptarmigan", "Vault leftover vs vault.hcl", "vault", "1.12.7", "1.18.3", True, "vault.hcl", "apps/api/policy.hcl", "# vault 1.12.7", "# vault 1.18.3", "path \"secret/\" { policy = \"write\" }", "path \"secret/data/\" { capabilities = [\"update\"] }", "path \"secret/\" { policy = \"write\" }", "path \"secret/data/\" { capabilities = [\"update\"] }", "kv v1 policy=write → kv v2 capabilities update", "vault version", "vault policy fmt apps/api/policy.hcl", "vault policy fmt apps/legacy/policy.hcl", "apps/api/ptarmigan.hcl"),
    ),
    (
        P("boundary-hcl-leftover-hostset", "quelea", "Boundary leftover vs boundary.hcl", "boundary", "0.12.2", "0.18.2", False, "boundary.hcl", "apps/api/target.hcl", "# boundary 0.12.2", "# boundary 0.18.2", "host_set_ids = [\"hs_api\"]", "address = \"10.0.0.8:22\"", "boundary targets add-host-sets -id tt_api -host-set hs_api", "boundary targets add-host-sources -id tt_api -host-source hs_api", "add-host-sets → add-host-sources", "boundary version", "boundary config validate apps/api/target.hcl || true", "boundary config validate apps/legacy/target.hcl || true", "apps/api/quelea.hcl"),
        P("airflow-req-leftover-bashop", "rhea", "Airflow leftover vs requirements", "apache-airflow", "2.5.3", "2.10.4", True, "requirements.txt", "apps/api/requirements.txt", "apache-airflow==2.5.3", "apache-airflow==2.10.4", "from airflow.operators.bash_operator import BashOperator", "from airflow.operators.bash import BashOperator", "from airflow.operators.bash_operator import BashOperator", "from airflow.operators.bash import BashOperator", "bash_operator → operators.bash", "airflow version || true", "pytest -q apps/api", "pytest -q apps/legacy", "apps/api/dags/rhea.py"),
    ),
    (
        P("prefect-yaml-leftover-deploy", "shearwater", "Prefect leftover vs prefect.yaml", "prefect", "2.10.21", "3.1.8", False, "prefect.yaml", "apps/api/prefect.yaml", "prefect-version: 2.10.21", "prefect-version: 3.1.8", "deployments:\n  - name: api", "name: api", "Deployment.build_from_flow(flow, name=\"api\")", "flow.serve(name=\"api\")", "Deployment.build_from_flow → flow.serve", "prefect version", "prefect deploy --prefect-file apps/api/prefect.yaml --dry-run", "prefect deploy --prefect-file apps/legacy/prefect.yaml --dry-run", "apps/api/shearwater.py"),
        P("dagster-yaml-leftover-solid", "tropicbird", "Dagster leftover vs workspace.yaml", "dagster", "1.3.13", "1.9.6", True, "workspace.yaml", "apps/api/workspace.yaml", "load_from:\n  - python_file: repo.py # 1.3.13", "load_from:\n  - python_module: apps.api # 1.9.6", "@solid", "@op", "@solid\ndef extract():", "@op\ndef extract():", "@solid → @op", "dagster --version", "dagster dev -w apps/api/workspace.yaml --dry-run || true", "dagster dev -w apps/legacy/workspace.yaml --dry-run || true", "apps/api/tropicbird.py"),
    ),
    (
        P("luigi-cfg-leftover-run", "upupa", "Luigi leftover vs luigi.cfg", "luigi", "3.1.1", "3.6.0", False, "luigi.cfg", "apps/api/luigi.cfg", "[core]\n# luigi 3.1.1", "[core]\n# luigi 3.6.0", "luigi.run()", "luigi.build([Api()], local_scheduler=True)", "luigi.run()", "luigi.build([Api()], local_scheduler=True)", "luigi.run → luigi.build", "python3 -c 'import luigi' || true", "pytest -q apps/api", "pytest -q apps/legacy", "apps/api/src/upupa.py"),
        P("dbt-project-leftover-tests", "auk", "dbt leftover vs dbt_project.yml", "dbt-core", "1.4.9", "1.9.1", True, "dbt_project.yml", "apps/api/dbt_project.yml", "name: api\nversion: '1.4.9'", "name: api\nversion: '1.9.1'", "tests:", "data_tests:", "tests:\n  - unique", "data_tests:\n  - unique", "tests: → data_tests:", "dbt --version", "dbt parse --project-dir apps/api", "dbt parse --project-dir apps/legacy", "apps/api/models/auk.yml"),
    ),
    (
        P("gx-yml-leftover-datacontext", "auklet", "Great Expectations leftover vs great_expectations.yml", "great_expectations", "0.15.50", "1.2.5", False, "great_expectations.yml", "apps/api/great_expectations.yml", "config_version: 3.0 # 0.15.50", "config_version: 4.0 # 1.2.5", "DataContext.create(project_root_dir)", "gx.get_context(mode=\"file\")", "context = DataContext.create(\".\")", "context = gx.get_context(mode=\"file\")", "DataContext.create → gx.get_context", "great_expectations --version || true", "pytest -q apps/api", "pytest -q apps/legacy", "apps/api/src/auklet.py"),
        P("mlflow-conda-leftover-pyfunc", "bee-eater", "MLflow leftover vs conda.yaml", "mlflow", "2.5.0", "2.19.0", True, "conda.yaml", "apps/api/conda.yaml", "  - mlflow=2.5.0", "  - mlflow=2.19.0", "mlflow.pyfunc.log_model(conda_env=env)", "mlflow.pyfunc.log_model(pip_requirements=reqs)", "conda_env=env", "pip_requirements=reqs", "conda_env → pip_requirements", "mlflow --version", "pytest -q apps/api", "pytest -q apps/legacy", "apps/api/src/bee_eater.py"),
    ),
    (
        P("wandb-yaml-leftover-init", "blackbird", "W&B leftover vs wandb.yaml", "wandb", "0.15.8", "0.19.1", False, "wandb.yaml", "apps/api/wandb.yaml", "wandb: 0.15.8", "wandb: 0.19.1", "wandb.init(project=\"api\")", "run = wandb.init(project=\"api\")", "wandb.log({\"acc\": acc})", "run.log({\"acc\": acc})", "wandb.init/log → run.log", "wandb --version", "pytest -q apps/api", "pytest -q apps/legacy", "apps/api/src/blackbird.py"),
        P("hfhub-req-leftover-authtoken", "bluebird", "huggingface_hub leftover vs requirements", "huggingface_hub", "0.16.4", "0.27.0", True, "requirements.txt", "apps/api/requirements.txt", "huggingface_hub==0.16.4", "huggingface_hub==0.27.0", "hf_hub_download(repo, f, use_auth_token=True)", "hf_hub_download(repo, f, token=True)", "use_auth_token=True", "token=True", "use_auth_token → token", "python3 -c 'import huggingface_hub' || true", "pytest -q apps/api", "pytest -q apps/legacy", "apps/api/src/bluebird.py"),
    ),
    (
        P("transformers-req-leftover-token", "bobwhite", "transformers leftover vs requirements", "transformers", "4.30.2", "4.47.1", False, "requirements.txt", "apps/api/requirements.txt", "transformers==4.30.2", "transformers==4.47.1", "AutoTokenizer.from_pretrained(n, use_auth_token=True)", "AutoTokenizer.from_pretrained(n, token=True)", "use_auth_token=True", "token=True", "use_auth_token → token", "python3 -c 'import transformers' || true", "pytest -q apps/api", "pytest -q apps/legacy", "apps/api/src/bobwhite.py"),
        P("langchain-req-leftover-llmchain", "bowerbird", "langchain leftover vs requirements", "langchain", "0.0.200", "0.3.13", True, "requirements.txt", "apps/api/requirements.txt", "langchain==0.0.200", "langchain==0.3.13", "from langchain import LLMChain", "from langchain_core.runnables import RunnableSequence", "LLMChain(llm=llm, prompt=p)", "prompt | llm", "LLMChain → RunnableSequence", "python3 -c 'import langchain' || true", "pytest -q apps/api", "pytest -q apps/legacy", "apps/api/src/bowerbird.py"),
    ),
    (
        P("llamaindex-req-leftover-gptidx", "bullfinch", "llama-index leftover vs requirements", "llama-index", "0.8.29", "0.12.9", False, "requirements.txt", "apps/api/requirements.txt", "llama-index==0.8.29", "llama-index==0.12.9", "from llama_index import GPTSimpleVectorIndex", "from llama_index.core import VectorStoreIndex", "GPTSimpleVectorIndex.from_documents(docs)", "VectorStoreIndex.from_documents(docs)", "GPTSimpleVectorIndex → VectorStoreIndex", "python3 -c 'import llama_index' || true", "pytest -q apps/api", "pytest -q apps/legacy", "apps/api/src/bullfinch.py"),
        P("opencv-cmake-leftover-sift", "bushtit", "OpenCV leftover vs CMakeLists", "opencv", "4.5.5", "4.10.0", True, "CMakeLists.txt", "apps/api/CMakeLists.txt", "find_package(OpenCV 4.5.5 REQUIRED)", "find_package(OpenCV 4.10.0 REQUIRED)", "cv::xfeatures2d::SIFT::create()", "cv::SIFT::create()", "cv2.xfeatures2d.SIFT_create()", "cv2.SIFT_create()", "xfeatures2d.SIFT → cv2.SIFT", "pkg-config --modversion opencv4 || true", "ctest --test-dir apps/api", "ctest --test-dir apps/legacy", "apps/api/src/bushtit.cpp"),
    ),
    (
        P("pcl-cmake-leftover-boostptr", "chickadee", "PCL leftover vs CMakeLists", "pcl", "1.12.1", "1.14.1", False, "CMakeLists.txt", "apps/api/CMakeLists.txt", "find_package(PCL 1.12 REQUIRED)", "find_package(PCL 1.14 REQUIRED)", "boost::shared_ptr<pcl::PointCloud<pcl::PointXYZ>> c", "std::shared_ptr<pcl::PointCloud<pcl::PointXYZ>> c", "boost::shared_ptr<", "std::shared_ptr<", "boost::shared_ptr → std::shared_ptr", "pkg-config --modversion pcl_common-1.14 || true", "ctest --test-dir apps/api", "ctest --test-dir apps/legacy", "apps/api/src/chickadee.cpp"),
        P("gazebo-classic-leftover-transport", "chough", "Gazebo Classic leftover vs CMakeLists", "gazebo", "11.14.0", "8.6.0", True, "CMakeLists.txt", "apps/api/CMakeLists.txt", "find_package(gazebo 11 REQUIRED)", "find_package(gz-sim8 REQUIRED)", "gazebo::transport::Node node;", "gz::transport::Node node;", "gazebo::transport::Node", "gz::transport::Node", "gazebo::transport → gz::transport", "gz sim --versions || true", "ctest --test-dir apps/api", "ctest --test-dir apps/legacy", "apps/api/src/chough.cc"),
    ),
    (
        P("moveit-config-leftover-movegroup", "cockatoo", "MoveIt leftover vs package.xml", "moveit", "1.1.11", "2.10.0", False, "package.xml", "apps/api/package.xml", "<version>1.1.11</version>", "<version>2.10.0</version>", "moveit::planning_interface::MoveGroup g(\"arm\");", "moveit::planning_interface::MoveGroupInterface g(n, \"arm\");", "MoveGroup g(\"arm\");", "MoveGroupInterface g(n, \"arm\");", "MoveGroup → MoveGroupInterface", "ros2 pkg prefix moveit_ros_planning_interface || true", "colcon test --packages-select api", "colcon test --packages-select legacy", "apps/api/src/cockatoo.cpp"),
        P("gstreamer-meson-leftover-pad", "cowbird", "GStreamer leftover vs meson.build", "gstreamer", "1.20.7", "1.24.10", True, "meson.build", "apps/api/meson.build", "dependency('gstreamer-1.0', version: '>=1.20')", "dependency('gstreamer-1.0', version: '>=1.24')", "gst_element_get_request_pad(e, \"src_%u\")", "gst_element_request_pad_simple(e, \"src_%u\")", "gst_element_get_request_pad(", "gst_element_request_pad_simple(", "get_request_pad → request_pad_simple", "pkg-config --modversion gstreamer-1.0", "meson test -C apps/api/build", "meson test -C apps/legacy/build", "apps/api/src/cowbird.c"),
    ),
    (
        P("ffmpeg-pc-leftover-decode", "crossbill", "FFmpeg leftover vs configure", "ffmpeg", "4.4.4", "7.1", False, "ffbuild/config.mak", "apps/api/Makefile", "LIBAVCODEC_VERSION=58.134.100", "LIBAVCODEC_VERSION=61.19.101", "avcodec_decode_video2(ctx, fr, &got, pkt)", "avcodec_send_packet(ctx, pkt); avcodec_receive_frame(ctx, fr)", "avcodec_decode_video2(ctx, fr, &got, pkt);", "avcodec_send_packet(ctx, pkt); avcodec_receive_frame(ctx, fr);", "avcodec_decode_video2 → send/receive", "pkg-config --modversion libavcodec", "make -C apps/api test", "make -C apps/legacy test", "apps/api/src/crossbill.c"),
        P("llvm-cmake-leftover-opaque", "cuckoo", "LLVM leftover vs CMakeLists", "llvm", "14.0.6", "19.1.6", True, "CMakeLists.txt", "apps/api/CMakeLists.txt", "find_package(LLVM 14 REQUIRED)", "find_package(LLVM 19 REQUIRED)", "PointerType::get(elemTy, as)", "PointerType::get(ctx, as)", "PointerType::get(ty, as)", "PointerType::get(ctx, as)", "typed pointer → opaque PointerType::get(ctx, as)", "llvm-config --version", "ctest --test-dir apps/api", "ctest --test-dir apps/legacy", "apps/api/src/cuckoo.cpp"),
    ),
    (
        P("mlir-td-leftover-funcop", "curlew", "MLIR leftover vs TableGen", "mlir", "14.0.6", "19.1.6", False, "CMakeLists.txt", "apps/api/CMakeLists.txt", "find_package(MLIR 14 REQUIRED)", "find_package(MLIR 19 REQUIRED)", "mlir::FuncOp fn", "mlir::func::FuncOp fn", "mlir::FuncOp", "mlir::func::FuncOp", "mlir::FuncOp → mlir::func::FuncOp", "mlir-opt --version", "ctest --test-dir apps/api", "ctest --test-dir apps/legacy", "apps/api/src/curlew.cpp"),
        P("sphinx-conf-leftover-stylesheet", "dickcissel", "Sphinx leftover vs conf.py", "sphinx", "5.3.0", "8.1.3", True, "conf.py", "apps/api/conf.py", "needs_sphinx = \"5.3\"", "needs_sphinx = \"8.1\"", "app.add_stylesheet(\"api.css\")", "app.add_css_file(\"api.css\")", "app.add_stylesheet(\"api.css\")", "app.add_css_file(\"api.css\")", "add_stylesheet → add_css_file", "sphinx-build --version", "sphinx-build -b html apps/api /tmp/api-docs", "sphinx-build -b html apps/legacy /tmp/legacy-docs", "apps/api/dickcissel.py"),
    ),
    (
        P("mkdocs-yml-leftover-theme", "dowitcher", "MkDocs leftover vs mkdocs.yml", "mkdocs", "1.4.3", "1.6.1", False, "mkdocs.yml", "apps/api/mkdocs.yml", "site_name: api # 1.4.3", "site_name: api # 1.6.1", "theme: readthedocs", "theme:\n  name: material", "theme: readthedocs", "theme:\n  name: material", "readthedocs → material", "mkdocs --version", "mkdocs build -f apps/api/mkdocs.yml", "mkdocs build -f apps/legacy/mkdocs.yml", "apps/api/docs/dowitcher.md"),
        P("javadoc-opts-leftover-doclet", "drongo", "Javadoc leftover vs options", "javadoc", "11", "21", True, "javadoc.options", "apps/api/javadoc.options", "-source 11", "-source 21", "-html4", "-html5", "import com.sun.javadoc.RootDoc;", "import jdk.javadoc.doclet.Doclet;", "com.sun.javadoc → jdk.javadoc.doclet", "javadoc --version", "javadoc @apps/api/javadoc.options", "javadoc @apps/legacy/javadoc.options", "apps/api/src/Drongo.java"),
    ),
    (
        P("doxygen-cfg-leftover-tclsubst", "elfowl", "Doxygen leftover vs Doxyfile", "doxygen", "1.8.20", "1.12.0", False, "Doxyfile", "apps/api/Doxyfile", "PROJECT_NUMBER = 1.8.20", "PROJECT_NUMBER = 1.12.0", "TCL_SUBST = api", "ALIASES += api{1}=\"\\1\"", "TCL_SUBST = api", "ALIASES += api{1}=\"\\1\"", "TCL_SUBST removed → ALIASES", "doxygen -v", "doxygen apps/api/Doxyfile", "doxygen apps/legacy/Doxyfile", "apps/api/elfowl.h"),
        P("plantuml-jar-leftover-includeurl", "fairywren", "PlantUML leftover vs plantuml.cfg", "plantuml", "1.2022.5", "1.2024.8", True, "plantuml.cfg", "apps/api/plantuml.cfg", "skin rose # 1.2022.5", "!theme plain # 1.2024.8", "!includeurl https://example/styles.puml", "!include styles.puml", "!includeurl https://example/styles.puml", "!include styles.puml", "!includeurl → !include", "java -jar plantuml.jar -version", "java -jar plantuml.jar apps/api/fair.puml", "java -jar plantuml.jar apps/legacy/fair.puml", "apps/api/fairywren.puml"),
    ),
    (
        P("graphviz-dot-leftover-nslimit", "fieldfare", "Graphviz leftover vs .dot", "graphviz", "2.43.0", "12.2.1", False, "graph.dot", "apps/api/graph.dot", "// graphviz 2.43.0", "// graphviz 12.2.1", "nslimit=2", "nslimit1=2", "overlap=false", "overlap=prism", "nslimit + overlap=false → nslimit1 + prism", "dot -V", "dot -Tsvg apps/api/graph.dot -o /tmp/api.svg", "dot -Tsvg apps/legacy/graph.dot -o /tmp/legacy.svg", "apps/api/fieldfare.dot"),
        P("bison-y-leftover-pure", "flycatcher", "Bison leftover vs .y", "bison", "3.5.4", "3.8.2", True, "api.y", "apps/api/api.y", "/* bison 3.5.4 */", "/* bison 3.8.2 */", "%pure-parser", "%define api.pure full", "%pure-parser", "%define api.pure full", "%pure-parser → %define api.pure full", "bison --version | head -n 1", "bison -d apps/api/api.y", "bison -d apps/legacy/legacy.y", "apps/api/flycatcher.y"),
    ),
    (
        P("swig-i-leftover-pyint", "fulmar", "SWIG leftover vs .i", "swig", "4.0.2", "4.3.0", False, "api.i", "apps/api/api.i", "%module api /* 4.0.2 */", "%module api /* 4.3.0 */", "%pythoncode %{ %}", "%pythonbegin %{ %}", "PyInt_FromLong(n)", "PyLong_FromLong(n)", "PyInt_FromLong → PyLong_FromLong", "swig -version | head -n 1", "swig -python apps/api/api.i", "swig -python apps/legacy/legacy.i", "apps/api/fulmar.i"),
        P("gcc-plugin-leftover-bb", "gnatcatcher", "GCC plugin leftover vs plugin.api", "gcc", "11.4.0", "14.2.0", True, "plugin.version", "apps/api/plugin.cc", "GCC 11.4.0", "GCC 14.2.0", "FOR_EACH_BB (bb)", "FOR_EACH_BB_FN (bb, fun)", "FOR_EACH_BB (bb)", "FOR_EACH_BB_FN (bb, cfun)", "FOR_EACH_BB → FOR_EACH_BB_FN", "gcc --version | head -n 1", "make -C apps/api test", "make -C apps/legacy test", "apps/api/gnatcatcher.cc"),
    ),
    (
        P("clang-tidy-leftover-checks", "grackle", "clang-tidy leftover vs .clang-tidy", "clang-tidy", "14.0.6", "19.1.6", False, ".clang-tidy", "apps/api/.clang-tidy", "Checks: 'google-readability-function-size' # 14", "Checks: 'readability-function-size' # 19", "Checks: 'google-readability-function-size'", "Checks: 'readability-function-size'", "google-readability-function-size", "readability-function-size", "google-readability-function-size → readability-function-size", "clang-tidy --version", "clang-tidy -p apps/api apps/api/src/grackle.cpp", "clang-tidy -p apps/legacy apps/legacy/src/grackle.cpp", "apps/api/src/grackle.cpp"),
        P("spinnaker-hal-leftover-kayenta", "greenshank", "Spinnaker leftover vs halyard", "spinnaker", "1.28.6", "1.34.2", True, "halconfig.yml", "apps/api/halconfig.yml", "currentDeployment: api # 1.28.6", "currentDeployment: api # 1.34.2", "kayenta:\n  enabled: true", "canary:\n  enabled: true", "hal config canary enable", "spin canary-config list", "kayenta → canary + spin", "hal --version || true", "hal config --file apps/api/halconfig.yml", "hal config --file apps/legacy/halconfig.yml", "apps/api/greenshank.yml"),
    ),
    (
        P("argo-wf-leftover-retry", "grosbeak", "Argo Workflows leftover vs workflow.yaml", "argo-workflows", "3.4.17", "3.6.2", False, "workflow.yaml", "apps/api/workflow.yaml", "apiVersion: argoproj.io/v1alpha1 # 3.4.17", "apiVersion: argoproj.io/v1alpha1 # 3.6.2", "retryStrategy:\n  retryPolicy: Always", "retryStrategy:\n  expression: \"true\"", "retryPolicy: Always", "expression: \"true\"", "retryPolicy → expression", "argo version", "argo lint apps/api/workflow.yaml", "argo lint apps/legacy/workflow.yaml", "apps/api/grosbeak.yaml"),
        P("ignition-gz-leftover-msgs", "guillemot", "Ignition leftover vs package.xml", "ignition-gazebo", "6.16.0", "gz-sim8 8.6.0", True, "package.xml", "apps/api/package.xml", "<name>ignition-gazebo6</name>", "<name>gz-sim8</name>", "ignition::msgs::StringMsg m;", "gz::msgs::StringMsg m;", "ignition::msgs::", "gz::msgs::", "ignition::msgs → gz::msgs", "gz topic --list || true", "colcon test --packages-select api", "colcon test --packages-select legacy", "apps/api/src/guillemot.cc"),
    ),
]


def build_round(rnd: int) -> tuple[list[dict], str]:
    idx = rnd - CATALOG_FIRST
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(
            f"round {rnd} outside catalog {CATALOG_FIRST}..{CATALOG_FIRST + len(PAIRS) - 1}"
        )
    suc, fail = PAIRS[idx]
    suc_ep = build_episode(rnd, suc)
    fail_ep = build_episode(rnd, fail)
    for ep in (suc_ep, fail_ep):
        n = len(ep["steps"])
        if n < 16 or n > 20:
            raise SystemExit(f"{ep['id']} has {n} steps, want 16-20")
        blob = json.dumps(ep)
        for banned in (
            "thought",
            "chain_of_thought",
            "scratch",
            "inner_monologue",
            "spike_events",
        ):
            if f'"{banned}"' in blob:
                raise SystemExit(f"{ep['id']} contains banned key {banned}")
        if '"sim_or_real": "real"' in blob or '"sim_or_real":"real"' in blob:
            raise SystemExit(f"{ep['id']} claims sim_or_real real")
    notes = notes_for(rnd, suc, fail)
    if "Novel coverage:" not in notes:
        raise SystemExit("notes missing Novel coverage")
    return [suc_ep, fail_ep], notes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    args = ap.parse_args()
    rnd = args.round
    staging = Path(args.staging)
    recs, notes = build_round(rnd)
    batch = staging / f"batch-r{rnd:02d}.jsonl"
    notes_path = staging / f"NOTES-r{rnd:02d}.md"
    with batch.open("w") as handle:
        for rec in recs:
            handle.write(json.dumps(rec, ensure_ascii=True) + "\n")
    notes_path.write_text(notes)
    print(
        json.dumps(
            {
                "round": rnd,
                "ids": [r["id"] for r in recs],
                "steps": [len(r["steps"]) for r in recs],
                "success": [r["reward"]["success"] for r in recs],
                "batch": str(batch),
                "notes": str(notes_path),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
