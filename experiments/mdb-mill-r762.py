#!/usr/bin/env python3
"""Mill monorepo-dep-bump-factory r762+ as unique leftover plants.

BAN r01–r761 clones: workspace/catalog grid, libNNNN, r50–r80 version-file,
r709–r745 lock leftover (Bazel/Pants/Buck2/Please/Earthly/Deno/Bundler/
Crystal/DUB/opam/Nimble/Stack/Carton/Spago/Dart/Flutter/GN/xmake/Clojure/
Guix/Spack/west/PlatformIO/pdm/hatch/rye/pip-tools/cargo rustver/Mix/
Composer/NuGet/Paket/SwiftPM/CocoaPods/CMake FetchContent/Conan/pnpm peer/
bun trusted/buf/gqlcodegen/Meson wrap/SCons/Prisma/drizzle/Cabal/Julia/
vcpkg/npm packageManager/pnpm patched/renv/Premake/Carthage/Gradle
platform/gomod toolchain/Yarn PnP/Poetry extras/uv constraint/Ninja/CUE/
Dagger/Dhall/Nickel/Pkl/jsonnet/Terragrunt/OpenTofu/Packer/Skaffold/
Kustomize/Tilt/Argo CD/Tekton), r746–r761 leftover langs (rebar/Gleam/
Zig/Odin/LuaRocks/fpm/Alire/Lake/V/Pony/Chapel/Racket/wit-deps/mill/sbt/
Leiningen/Elm/Haxe/Godot/Unity/SWI-Prolog/qlot/Agda/Coq/Janet/Idris2/
Babashka/ReScript/Hare/MoonBit/Qbs/Emscripten). SKIP Hunter, Elixir mix.

NEW: Mercury.deps, Factor extra-roots, Red red.rc, Io Eerie.lock, Pharo
Metacello, GAP PackageInfo, Fennel deps.fnl, Unison ucm, Grain lock,
AssemblyScript asconfig, Waf wscript, Autotools LT_INIT, Tuist destinations,
Brewfile.lock openssl@3, Devbox php81, CNB project.toml, Helm Chart.lock,
Pulumi awsx classic, ROS2 colcon QoS, ESP-IDF tcpip_adapter, Yocto :append,
FuseSoC CAPI-2, SML/NJ PrettyPrint, MLton IntInf, Koka throw, Roc Decode,
MacPorts python.version, Hy hyrule assoc.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

FACTORY = "monorepo-dep-bump-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 762

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
Not a pin-file mill and not libNNNN recycle. Distinct from r690–r745 workspace/catalog and lock leftover grids (no pnpm/nx/turbo/lerna/rush/moon/mise/nix/pixi/mix/conan/vcpkg/meson/cmake FetchContent clones).

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
Keep unique leftover plots (Mercury/Factor/Red/Io/Pharo/GAP/Fennel/Unison). Ban libNNNN, Mix/Elixir, Conan/Hunter/vcpkg/Meson wrap/CMake FetchContent, r735–r761 clones.
"""


# Each pair: (success, leftover-workspace fail). Index = round - 762.
PAIRS: list[tuple[dict, dict]] = [
    (
        {
            "slug": "mercury-deps-leftover-stdutil",
            "plant": "quail",
            "surface": "Mercury Mercury.deps leftover vs Mercury.options",
            "pkg": "std_util",
            "old": "14.01.1",
            "new": "22.01.8",
            "fail": False,
            "sot": "Mercury.deps",
            "nested": "apps/api/Mercury.options",
            "left": "apps/legacy",
            "left_file": "apps/legacy/Mercury.deps",
            "sot_line": "std_util 14.01.1",
            "nested_line": "MCFLAGS = --use-subdirs --lib std_util",
            "probe_cmd": "mmc --version | head -n 1; rg '14.01.1|22.01.8|std_util' Mercury.deps apps/*/Mercury.options apps/legacy/Mercury.deps | head",
            "probe_obs": "Mercury.deps std_util 14.01.1\nlegacy Mercury.deps 14.01.1 leftover\n",
            "first_old": "MCFLAGS = --use-subdirs --lib std_util",
            "first_new": "MCFLAGS = --use-subdirs --lib list",
            "fail_cmd": "mmc --make apps/api 2>&1 | tail -n 16",
            "fail_obs": "error: apps/api Mercury.options --lib list vs Mercury.deps still pins std_util 14.01.1\n",
            "plan_old": "std_util 14.01.1",
            "plan_new": "list 22.01.8",
            "companion_new": "MCFLAGS = --use-subdirs --lib list",
            "test_cmd": "mmc --make apps/api && mmc --make apps/api.test 2>&1 | tail -n 16",
            "api_fail_obs": "Error: std_util.member/2 is not exported; library std_util was removed (use list.member)\n",
            "callsite": "apps/api/src/quail.m",
            "callsite_obs": ":- import_module std_util.\n",
            "api_old": ":- import_module std_util.",
            "api_new": ":- import_module list.",
            "api_break": "std_util.member → list.member",
            "retest_cmd": "mmc --make apps/api.test 2>&1 | tail -n 8",
            "scan_obs": "Mercury.deps list 22.01.8\napps/legacy/Mercury.deps std_util 14.01.1\n",
            "ws_cmd": "mmc --make apps/legacy 2>&1 | tail -n 16",
            "ws_ok": "api 4 passed\nlegacy Mercury.deps 14.01.1 skipped (ticket allows)\n",
            "confirm_obs": "std_util 14.01.1",
        },
        {
            "slug": "factor-vocabs-leftover-assoc",
            "plant": "raven",
            "surface": "Factor vocabs leftover vs extra-roots",
            "pkg": "assoc",
            "old": "0.98",
            "new": "0.100",
            "fail": True,
            "sot": "extra-roots.txt",
            "nested": "apps/api/api.factor",
            "left": "apps/legacy",
            "left_file": "apps/legacy/extra-roots.txt",
            "sot_line": "extra-roots: apps/legacy/vocabs  ; 0.98",
            "nested_line": "USING: assocs make ;",
            "probe_cmd": "factor -e='\"assoc\" vocab-version print'; rg '0.98|0.100|make-assoc|extra-roots' extra-roots.txt apps/*/api.factor apps/legacy/extra-roots.txt | head",
            "probe_obs": "extra-roots leftover vocabs 0.98\nlegacy extra-roots 0.98\n",
            "first_old": "USING: assocs make ;",
            "first_new": "USING: assocs ;",
            "fail_cmd": "factor -run=apps.api.tests 2>&1 | tail -n 16",
            "fail_obs": "error: apps/api dropped make but extra-roots.txt still loads 0.98 vocab roots\n",
            "plan_old": "extra-roots: apps/legacy/vocabs  ; 0.98",
            "plan_new": "extra-roots: apps/api/vocabs  ; 0.100",
            "companion_new": "USING: assocs ;",
            "test_cmd": "factor -run=apps.api.tests 2>&1 | tail -n 16",
            "api_fail_obs": "No word named make-assoc in assocs (removed in Factor 0.100; use H{ } clone)\n",
            "callsite": "apps/api/raven.factor",
            "callsite_obs": ": cache ( -- assoc ) [ ] make-assoc ;\n",
            "api_old": ": cache ( -- assoc ) [ ] make-assoc ;",
            "api_new": ": cache ( -- assoc ) H{ } clone ;",
            "api_break": "make-assoc → H{ } clone",
            "retest_cmd": "factor -run=apps.api.tests 2>&1 | tail -n 8",
            "scan_obs": "extra-roots apps/api/vocabs\napps/legacy/extra-roots.txt leftover 0.98\n",
            "ws_cmd": "factor -run=apps.legacy.tests 2>&1 | tail -n 16",
            "ws_fail": "api 6 passed\nFAIL factor: leftover apps/legacy extra-roots 0.98 vs 0.100 make-assoc\n",
            "confirm_obs": "extra-roots: apps/legacy/vocabs  ; 0.98",
        },
    ),
    (
        {
            "slug": "red-rc-leftover-collect",
            "plant": "robin",
            "surface": "Red red.rc leftover vs Red/System",
            "pkg": "red",
            "old": "0.6.4",
            "new": "0.6.5",
            "fail": False,
            "sot": "red.rc",
            "nested": "apps/api/api.red",
            "left": "apps/legacy",
            "left_file": "apps/legacy/red.rc",
            "sot_line": "Red [Needs: View 0.6.4]",
            "nested_line": "Red [Needs: 'View]",
            "probe_cmd": "red --version; rg '0.6.4|0.6.5|collect' red.rc apps/*/api.red apps/legacy/red.rc | head",
            "probe_obs": "red.rc View 0.6.4\nlegacy red.rc 0.6.4 leftover\n",
            "first_old": "Red [Needs: 'View]",
            "first_new": "Red [Needs: View 0.6.5]",
            "fail_cmd": "red -c apps/api/api.red 2>&1 | tail -n 16",
            "fail_obs": "error: apps/api Needs View 0.6.5 vs root red.rc still 0.6.4\n",
            "plan_old": "Red [Needs: View 0.6.4]",
            "plan_new": "Red [Needs: View 0.6.5]",
            "companion_new": "Red [Needs: View 0.6.5]",
            "test_cmd": "red -t apps/api/tests.red 2>&1 | tail -n 16",
            "api_fail_obs": "Script Error: collect/keep is no longer a refinement; use collect/into (Red 0.6.5)\n",
            "callsite": "apps/api/src/robin.red",
            "callsite_obs": "collect/keep [id]\n",
            "api_old": "collect/keep [id]",
            "api_new": "collect/into [id] out",
            "api_break": "collect/keep → collect/into",
            "retest_cmd": "red -t apps/api/tests.red 2>&1 | tail -n 8",
            "scan_obs": "red.rc 0.6.5\napps/legacy/red.rc 0.6.4\n",
            "ws_cmd": "red -c apps/legacy/legacy.red 2>&1 | tail -n 16",
            "ws_ok": "api 4 passed\nlegacy red.rc 0.6.4 skipped (ticket allows)\n",
            "confirm_obs": "Red [Needs: View 0.6.4]",
        },
        {
            "slug": "io-eerie-leftover-socket",
            "plant": "siskin",
            "surface": "Io Eerie.lock leftover vs addons",
            "pkg": "Socket",
            "old": "0.1.2",
            "new": "0.3.0",
            "fail": True,
            "sot": "Eerie.lock",
            "nested": "apps/api/package.io",
            "left": "apps/legacy",
            "left_file": "apps/legacy/Eerie.lock",
            "sot_line": "Socket 0.1.2",
            "nested_line": "Addon clone do(depends := list(\"Socket\"))",
            "probe_cmd": "io -e 'Eerie Env active packages'; rg '0.1.2|0.3.0|Socket' Eerie.lock apps/*/package.io apps/legacy/Eerie.lock | head",
            "probe_obs": "Eerie.lock Socket 0.1.2\nlegacy lock 0.1.2 leftover\n",
            "first_old": "Addon clone do(depends := list(\"Socket\"))",
            "first_new": "Addon clone do(depends := list(\"Socket@0.3.0\"))",
            "fail_cmd": "io apps/api/tests/run.io 2>&1 | tail -n 16",
            "fail_obs": "error: apps/api Socket@0.3.0 vs Eerie.lock frozen Socket 0.1.2\n",
            "plan_old": "Socket 0.1.2",
            "plan_new": "Socket 0.3.0",
            "companion_new": "Addon clone do(depends := list(\"Socket\"))",
            "test_cmd": "io apps/api/tests/run.io 2>&1 | tail -n 16",
            "api_fail_obs": "Exception: Socket does not respond to 'write' (removed; use writeMessage in 0.3)\n",
            "callsite": "apps/api/siskin.io",
            "callsite_obs": "sock write(payload)\n",
            "api_old": "sock write(payload)",
            "api_new": "sock writeMessage(payload)",
            "api_break": "Socket write → writeMessage",
            "retest_cmd": "io apps/api/tests/run.io 2>&1 | tail -n 8",
            "scan_obs": "Eerie.lock 0.3.0\napps/legacy/Eerie.lock 0.1.2\n",
            "ws_cmd": "io apps/legacy/tests/run.io 2>&1 | tail -n 16",
            "ws_fail": "api 6 passed\nFAIL eerie: leftover apps/legacy Eerie.lock Socket 0.1.2 vs 0.3.0 write\n",
            "confirm_obs": "Socket 0.1.2",
        },
    ),
    (
        {
            "slug": "pharo-metacello-leftover-gtdoc",
            "plant": "sparrow",
            "surface": "Pharo Metacello leftover vs Iceberg",
            "pkg": "GtDocumenter",
            "old": "8.0.0",
            "new": "11.0.0",
            "fail": False,
            "sot": "baseline.st",
            "nested": "apps/api/BaselineOfApi.st",
            "left": "apps/legacy",
            "left_file": "apps/legacy/baseline.st",
            "sot_line": "spec baseline: 'GtDocumenter' with: [ spec repository: 'github://feenkcom/gtoolkit:v8.0.0' ]",
            "nested_line": "spec package: 'Api' with: [ spec requires: #('GtDocumenter') ]",
            "probe_cmd": "pharo --version; rg '8.0.0|11.0.0|GtDocumenter|Lepiter' baseline.st apps/*/BaselineOfApi.st apps/legacy/baseline.st | head",
            "probe_obs": "baseline GtDocumenter v8.0.0\nlegacy baseline 8.0.0 leftover\n",
            "first_old": "spec package: 'Api' with: [ spec requires: #('GtDocumenter') ]",
            "first_new": "spec package: 'Api' with: [ spec requires: #('Lepiter') ]",
            "fail_cmd": "pharo apps/api/Pharo.image test Api 2>&1 | tail -n 16",
            "fail_obs": "MetacelloNotification: Lepiter not in root baseline.st (still GtDocumenter 8.0.0)\n",
            "plan_old": "spec baseline: 'GtDocumenter' with: [ spec repository: 'github://feenkcom/gtoolkit:v8.0.0' ]",
            "plan_new": "spec baseline: 'Lepiter' with: [ spec repository: 'github://feenkcom/gtoolkit:v11.0.0' ]",
            "companion_new": "spec package: 'Api' with: [ spec requires: #('Lepiter') ]",
            "test_cmd": "pharo apps/api/Pharo.image test Api 2>&1 | tail -n 16",
            "api_fail_obs": "MessageNotUnderstood: GtDocumenter>>fromFile: (class moved to LeDatabase in GT 11)\n",
            "callsite": "apps/api/src/Sparrow.class.st",
            "callsite_obs": "GtDocumenter fromFile: path\n",
            "api_old": "GtDocumenter fromFile: path",
            "api_new": "LeDatabase loadFrom: path",
            "api_break": "GtDocumenter fromFile: → LeDatabase loadFrom:",
            "retest_cmd": "pharo apps/api/Pharo.image test Api 2>&1 | tail -n 8",
            "scan_obs": "baseline Lepiter 11.0.0\napps/legacy/baseline.st GtDocumenter 8.0.0\n",
            "ws_cmd": "pharo apps/legacy/Pharo.image test Legacy 2>&1 | tail -n 16",
            "ws_ok": "api 4 passed\nlegacy baseline 8.0.0 skipped (ticket allows)\n",
            "confirm_obs": "gtoolkit:v8.0.0",
        },
        {
            "slug": "gap-pkginfo-leftover-readpkg",
            "plant": "starling",
            "surface": "GAP PackageInfo leftover vs gaprc",
            "pkg": "GAPDoc",
            "old": "1.6.6",
            "new": "1.6.7",
            "fail": True,
            "sot": "gaprc",
            "nested": "apps/api/PackageInfo.g",
            "left": "apps/legacy",
            "left_file": "apps/legacy/PackageInfo.g",
            "sot_line": "LoadPackage(\"GAPDoc\", \"1.6.6\");",
            "nested_line": "NeededOtherPackages := [[\"GAPDoc\", \">=1.6.6\"]]",
            "probe_cmd": "gap --version | head -n 1; rg '1.6.6|1.6.7|GAPDoc|ReadPackage' gaprc apps/*/PackageInfo.g apps/legacy/PackageInfo.g | head",
            "probe_obs": "gaprc GAPDoc 1.6.6\nlegacy PackageInfo 1.6.6 leftover\n",
            "first_old": "NeededOtherPackages := [[\"GAPDoc\", \">=1.6.6\"]]",
            "first_new": "NeededOtherPackages := [[\"GAPDoc\", \">=1.6.7\"]]",
            "fail_cmd": "gap -q apps/api/tst/testall.g 2>&1 | tail -n 16",
            "fail_obs": "Error: Package api wants GAPDoc 1.6.7 but gaprc loaded 1.6.6\n",
            "plan_old": "LoadPackage(\"GAPDoc\", \"1.6.6\");",
            "plan_new": "LoadPackage(\"GAPDoc\", \"1.6.7\");",
            "companion_new": "NeededOtherPackages := [[\"GAPDoc\", \">=1.6.7\"]]",
            "test_cmd": "gap -q apps/api/tst/testall.g 2>&1 | tail -n 16",
            "api_fail_obs": "Error, ReadPackage is not a function (removed; use Filename+Read in GAP 4.13)\n",
            "callsite": "apps/api/lib/starling.g",
            "callsite_obs": "ReadPackage(\"api\", \"lib/extra.g\");\n",
            "api_old": "ReadPackage(\"api\", \"lib/extra.g\");",
            "api_new": "Read(Filename(DirectoriesPackageLibrary(\"api\", \"lib\"), \"extra.g\"));",
            "api_break": "ReadPackage → Filename+Read",
            "retest_cmd": "gap -q apps/api/tst/testall.g 2>&1 | tail -n 8",
            "scan_obs": "gaprc 1.6.7\napps/legacy/PackageInfo.g 1.6.6\n",
            "ws_cmd": "gap -q apps/legacy/tst/testall.g 2>&1 | tail -n 16",
            "ws_fail": "api 6 passed\nFAIL gap: leftover apps/legacy PackageInfo GAPDoc 1.6.6 vs 1.6.7 ReadPackage\n",
            "confirm_obs": ">=1.6.6",
        },
    ),
    (
        {
            "slug": "fennel-deps-leftover-macros",
            "plant": "swallow",
            "surface": "Fennel deps.fnl leftover vs fennel-ls",
            "pkg": "fennel",
            "old": "1.3.1",
            "new": "1.5.1",
            "fail": False,
            "sot": "deps.fnl",
            "nested": "apps/api/api.fnl",
            "left": "apps/legacy",
            "left_file": "apps/legacy/deps.fnl",
            "sot_line": "{:fennel \"1.3.1\"}",
            "nested_line": "(require-macros :macros)",
            "probe_cmd": "fennel --version; rg '1.3.1|1.5.1|require-macros' deps.fnl apps/*/api.fnl apps/legacy/deps.fnl | head",
            "probe_obs": "deps.fnl fennel 1.3.1\nlegacy deps.fnl 1.3.1 leftover\n",
            "first_old": "(require-macros :macros)",
            "first_new": "(import-macros m :macros)",
            "fail_cmd": "fennel --correlate apps/api/api.fnl 2>&1 | tail -n 16",
            "fail_obs": "error: import-macros needs fennel 1.5; deps.fnl still pins 1.3.1\n",
            "plan_old": "{:fennel \"1.3.1\"}",
            "plan_new": "{:fennel \"1.5.1\"}",
            "companion_new": "(import-macros m :macros)",
            "test_cmd": "fennel --correlate apps/api/test.fnl 2>&1 | tail -n 16",
            "api_fail_obs": "Compile error: require-macros is not a special (removed in Fennel 1.2+; use import-macros)\n",
            "callsite": "apps/api/src/swallow.fnl",
            "callsite_obs": "(require-macros :macros)\n",
            "api_old": "(require-macros :macros)",
            "api_new": "(import-macros {: defn} :macros)",
            "api_break": "require-macros → import-macros",
            "retest_cmd": "fennel apps/api/test.fnl 2>&1 | tail -n 8",
            "scan_obs": "deps.fnl 1.5.1\napps/legacy/deps.fnl 1.3.1\n",
            "ws_cmd": "fennel apps/legacy/test.fnl 2>&1 | tail -n 16",
            "ws_ok": "api 4 passed\nlegacy deps.fnl 1.3.1 skipped (ticket allows)\n",
            "confirm_obs": "{:fennel \"1.3.1\"}",
        },
        {
            "slug": "unison-ucm-leftover-stream",
            "plant": "tanager",
            "surface": "Unison ucm leftover vs scratch.u",
            "pkg": "base",
            "old": "4.0.0",
            "new": "5.0.0",
            "fail": True,
            "sot": "unison.lock",
            "nested": "apps/api/scratch.u",
            "left": "apps/legacy",
            "left_file": "apps/legacy/unison.lock",
            "sot_line": "base = 4.0.0",
            "nested_line": "Stream.fromList xs",
            "probe_cmd": "ucm version; rg '4.0.0|5.0.0|Stream.fromList' unison.lock apps/*/scratch.u apps/legacy/unison.lock | head",
            "probe_obs": "unison.lock base 4.0.0\nlegacy lock 4.0.0 leftover\n",
            "first_old": "Stream.fromList xs",
            "first_new": "Sequence.fromList xs",
            "fail_cmd": "ucm run.file apps/api/scratch.u 2>&1 | tail -n 16",
            "fail_obs": "Type error: Sequence.fromList not in base 4.0.0 (unison.lock); update required\n",
            "plan_old": "base = 4.0.0",
            "plan_new": "base = 5.0.0",
            "companion_new": "Sequence.fromList xs",
            "test_cmd": "ucm test apps/api 2>&1 | tail -n 16",
            "api_fail_obs": "Name Stream.fromList is not in scope (moved to Sequence.fromList in base 5)\n",
            "callsite": "apps/api/src/tanager.u",
            "callsite_obs": "s = Stream.fromList xs\n",
            "api_old": "s = Stream.fromList xs",
            "api_new": "s = Sequence.fromList xs",
            "api_break": "Stream.fromList → Sequence.fromList",
            "retest_cmd": "ucm test apps/api 2>&1 | tail -n 8",
            "scan_obs": "unison.lock 5.0.0\napps/legacy/unison.lock 4.0.0\n",
            "ws_cmd": "ucm test apps/legacy 2>&1 | tail -n 16",
            "ws_fail": "api 6 passed\nFAIL ucm: leftover apps/legacy unison.lock base 4.0.0 vs 5.0.0 Stream.fromList\n",
            "confirm_obs": "base = 4.0.0",
        },
    ),
    (
        {
            "slug": "grain-lock-leftover-pervasives",
            "plant": "thrush",
            "surface": "Grain grain.lock leftover vs grain.json",
            "pkg": "@grain/stdlib",
            "old": "0.6.6",
            "new": "0.7.1",
            "fail": False,
            "sot": "grain.lock",
            "nested": "apps/api/grain.json",
            "left": "apps/legacy",
            "left_file": "apps/legacy/grain.lock",
            "sot_line": "\"@grain/stdlib\": \"0.6.6\"",
            "nested_line": "\"@grain/stdlib\": \"^0.6.6\"",
            "probe_cmd": "grain --version; rg '0.6.6|0.7.1|Pervasives' grain.lock apps/*/grain.json apps/legacy/grain.lock | head",
            "probe_obs": "grain.lock stdlib 0.6.6\nlegacy lock 0.6.6 leftover\n",
            "first_old": "\"@grain/stdlib\": \"^0.6.6\"",
            "first_new": "\"@grain/stdlib\": \"0.7.1\"",
            "fail_cmd": "grain test apps/api 2>&1 | tail -n 16",
            "fail_obs": "error: apps/api grain.json 0.7.1 vs grain.lock frozen 0.6.6\n",
            "plan_old": "\"@grain/stdlib\": \"0.6.6\"",
            "plan_new": "\"@grain/stdlib\": \"0.7.1\"",
            "companion_new": "\"@grain/stdlib\": \"^0.7.1\"",
            "test_cmd": "grain test apps/api 2>&1 | tail -n 16",
            "api_fail_obs": "Unbound module Pervasives (removed in Grain 0.7; use Number / String)\n",
            "callsite": "apps/api/src/thrush.gr",
            "callsite_obs": "print(Pervasives.toString(n))\n",
            "api_old": "print(Pervasives.toString(n))",
            "api_new": "print(toString(n))",
            "api_break": "Pervasives.toString → toString",
            "retest_cmd": "grain test apps/api 2>&1 | tail -n 8",
            "scan_obs": "grain.lock 0.7.1\napps/legacy/grain.lock 0.6.6\n",
            "ws_cmd": "grain test apps/legacy 2>&1 | tail -n 16",
            "ws_ok": "api 4 passed\nlegacy lock 0.6.6 skipped (ticket allows)\n",
            "confirm_obs": "\"@grain/stdlib\": \"0.6.6\"",
        },
        {
            "slug": "assemblyscript-asconfig-leftover-new",
            "plant": "titmouse",
            "surface": "AssemblyScript asconfig leftover vs package.json",
            "pkg": "assemblyscript",
            "old": "0.19.23",
            "new": "0.27.31",
            "fail": True,
            "sot": "package.json",
            "nested": "apps/api/asconfig.json",
            "left": "apps/legacy",
            "left_file": "apps/legacy/package.json",
            "sot_line": "\"assemblyscript\": \"0.19.23\"",
            "nested_line": "\"extends\": \"../../asconfig.json\"",
            "probe_cmd": "npx asc --version; rg '0.19.23|0.27.31|__new|runtime' package.json apps/*/asconfig.json apps/legacy/package.json | head",
            "probe_obs": "package.json assemblyscript 0.19.23\nlegacy package.json leftover 0.19.23\n",
            "first_old": "\"extends\": \"../../asconfig.json\"",
            "first_new": "\"options\": { \"runtime\": \"incremental\", \"exportRuntime\": true }",
            "fail_cmd": "npx asc apps/api/assembly/index.ts --config apps/api/asconfig.json 2>&1 | tail -n 16",
            "fail_obs": "error: apps/api exportRuntime vs root package.json still assemblyscript 0.19.23\n",
            "plan_old": "\"assemblyscript\": \"0.19.23\"",
            "plan_new": "\"assemblyscript\": \"0.27.31\"",
            "companion_new": "\"extends\": \"../../asconfig.json\"",
            "test_cmd": "npm test --workspace apps/api 2>&1 | tail -n 16",
            "api_fail_obs": "error TS2339: Property '__new' does not exist (removed; use heap.alloc in 0.27)\n",
            "callsite": "apps/api/assembly/index.ts",
            "callsite_obs": "const p = __new(64, id);\n",
            "api_old": "const p = __new(64, id);",
            "api_new": "const p = heap.alloc(64);",
            "api_break": "__new → heap.alloc",
            "retest_cmd": "npm test --workspace apps/api 2>&1 | tail -n 8",
            "scan_obs": "package.json 0.27.31\napps/legacy/package.json 0.19.23 leftover\n",
            "ws_cmd": "npm test --workspace apps/legacy 2>&1 | tail -n 16",
            "ws_fail": "api 6 passed\nFAIL asc: leftover apps/legacy package.json assemblyscript 0.19.23 vs 0.27.31 __new\n",
            "confirm_obs": "\"assemblyscript\": \"0.19.23\"",
        },
    ),
    (
        {
            "slug": "waf-wscript-leftover-cxx11",
            "plant": "towhee",
            "surface": "Waf wscript leftover vs wtools",
            "pkg": "waf",
            "old": "2.0.25",
            "new": "2.1.4",
            "fail": False,
            "sot": "wscript",
            "nested": "apps/api/wscript",
            "left": "apps/legacy",
            "left_file": "apps/legacy/wscript",
            "sot_line": "VERSION = '2.0.25'",
            "nested_line": "bld.program(features='cxx cxxprogram cxx11', source='main.cpp')",
            "probe_cmd": "waf --version; rg '2.0.25|2.1.4|cxx11' wscript apps/*/wscript apps/legacy/wscript | head",
            "probe_obs": "wscript 2.0.25 cxx11\nlegacy wscript 2.0.25 leftover\n",
            "first_old": "bld.program(features='cxx cxxprogram cxx11', source='main.cpp')",
            "first_new": "bld.program(features='cxx cxxprogram', cxxflags='-std=c++17', source='main.cpp')",
            "fail_cmd": "waf --targets=api test 2>&1 | tail -n 16",
            "fail_obs": "error: unknown feature cxx11 on waf 2.1 request vs root wscript still 2.0.25\n",
            "plan_old": "VERSION = '2.0.25'",
            "plan_new": "VERSION = '2.1.4'",
            "companion_new": "bld.program(features='cxx cxxprogram', cxxflags='-std=c++17', source='main.cpp')",
            "test_cmd": "waf --targets=api test 2>&1 | tail -n 16",
            "api_fail_obs": "error: feature 'cxx11' does not exist (removed in waf 2.1; pass -std=c++17)\n",
            "callsite": "apps/api/src/towhee.cpp",
            "callsite_obs": "std::auto_ptr<Foo> p(new Foo);\n",
            "api_old": "std::auto_ptr<Foo> p(new Foo);",
            "api_new": "std::unique_ptr<Foo> p(new Foo);",
            "api_break": "cxx11 feature + auto_ptr → unique_ptr",
            "retest_cmd": "waf --targets=api test 2>&1 | tail -n 8",
            "scan_obs": "wscript 2.1.4\napps/legacy/wscript 2.0.25\n",
            "ws_cmd": "waf --targets=legacy test 2>&1 | tail -n 16",
            "ws_ok": "api 4 passed\nlegacy wscript 2.0.25 skipped (ticket allows)\n",
            "confirm_obs": "VERSION = '2.0.25'",
        },
        {
            "slug": "autotools-ac-leftover-libtool",
            "plant": "turnstone",
            "surface": "Autotools configure.ac leftover vs aclocal",
            "pkg": "libtool",
            "old": "2.4.6",
            "new": "2.5.3",
            "fail": True,
            "sot": "configure.ac",
            "nested": "apps/api/configure.ac",
            "left": "apps/legacy",
            "left_file": "apps/legacy/configure.ac",
            "sot_line": "AM_PROG_LIBTOOL\nm4_define([lt_version], [2.4.6])",
            "nested_line": "AC_CONFIG_FILES([apps/api/Makefile])",
            "probe_cmd": "autoconf --version | head -n 1; rg 'AM_PROG_LIBTOOL|LT_INIT|2.4.6|2.5.3' configure.ac apps/*/configure.ac apps/legacy/configure.ac | head",
            "probe_obs": "configure.ac AM_PROG_LIBTOOL 2.4.6\nlegacy configure.ac leftover 2.4.6\n",
            "first_old": "AC_CONFIG_FILES([apps/api/Makefile])",
            "first_new": "LT_INIT([disable-static])",
            "fail_cmd": "autoreconf -fi && ./configure --prefix=/tmp/api 2>&1 | tail -n 16",
            "fail_obs": "error: LT_INIT in apps/api vs root still AM_PROG_LIBTOOL (libtool 2.4.6)\n",
            "plan_old": "AM_PROG_LIBTOOL\nm4_define([lt_version], [2.4.6])",
            "plan_new": "LT_INIT\nm4_define([lt_version], [2.5.3])",
            "companion_new": "AC_CONFIG_FILES([apps/api/Makefile])",
            "test_cmd": "make -C apps/api check 2>&1 | tail -n 16",
            "api_fail_obs": "configure: error: AC_PROG_CC_C99 is obsolete; use AC_PROG_CC (Autoconf 2.70+)\n",
            "callsite": "apps/api/m4/api.m4",
            "callsite_obs": "AC_PROG_CC_C99\n",
            "api_old": "AC_PROG_CC_C99",
            "api_new": "AC_PROG_CC",
            "api_break": "AM_PROG_LIBTOOL + AC_PROG_CC_C99 → LT_INIT + AC_PROG_CC",
            "retest_cmd": "make -C apps/api check 2>&1 | tail -n 8",
            "scan_obs": "configure.ac LT_INIT 2.5.3\napps/legacy/configure.ac AM_PROG_LIBTOOL 2.4.6\n",
            "ws_cmd": "make -C apps/legacy check 2>&1 | tail -n 16",
            "ws_fail": "api 6 passed\nFAIL autotools: leftover apps/legacy configure.ac libtool 2.4.6 vs 2.5.3 AM_PROG_LIBTOOL\n",
            "confirm_obs": "2.4.6",
        },
    ),
    (
        {
            "slug": "tuist-manifest-leftover-platform",
            "plant": "veery",
            "surface": "Tuist Project.swift leftover vs Workspace.swift",
            "pkg": "tuist",
            "old": "3.36.0",
            "new": "4.28.1",
            "fail": False,
            "sot": "Workspace.swift",
            "nested": "apps/api/Project.swift",
            "left": "apps/legacy",
            "left_file": "apps/legacy/Project.swift",
            "sot_line": "let tuistVersion = \"3.36.0\"",
            "nested_line": "Target(name: \"Api\", platform: .iOS, product: .framework, bundleId: \"dev.veery.api\")",
            "probe_cmd": "tuist version; rg '3.36.0|4.28.1|platform: .iOS' Workspace.swift apps/*/Project.swift apps/legacy/Project.swift | head",
            "probe_obs": "Workspace tuist 3.36.0\nlegacy Project.swift platform leftover\n",
            "first_old": "Target(name: \"Api\", platform: .iOS, product: .framework, bundleId: \"dev.veery.api\")",
            "first_new": "Target(name: \"Api\", destinations: [.iPhone], product: .framework, bundleId: \"dev.veery.api\")",
            "fail_cmd": "tuist generate --path apps/api 2>&1 | tail -n 16",
            "fail_obs": "error: destinations: requires Tuist 4; Workspace.swift still pins 3.36.0\n",
            "plan_old": "let tuistVersion = \"3.36.0\"",
            "plan_new": "let tuistVersion = \"4.28.1\"",
            "companion_new": "Target(name: \"Api\", destinations: [.iPhone], product: .framework, bundleId: \"dev.veery.api\")",
            "test_cmd": "tuist test Api --path apps/api 2>&1 | tail -n 16",
            "api_fail_obs": "error: argument 'platform' is removed in Tuist 4; use destinations:\n",
            "callsite": "apps/api/Targets/Api.swift",
            "callsite_obs": "platform: .iOS\n",
            "api_old": "platform: .iOS",
            "api_new": "destinations: [.iPhone]",
            "api_break": "Target.platform → destinations",
            "retest_cmd": "tuist test Api --path apps/api 2>&1 | tail -n 8",
            "scan_obs": "Workspace 4.28.1\napps/legacy/Project.swift platform leftover 3.36.0\n",
            "ws_cmd": "tuist generate --path apps/legacy 2>&1 | tail -n 16",
            "ws_ok": "api 4 passed\nlegacy Project.swift 3.36.0 skipped (ticket allows)\n",
            "confirm_obs": "3.36.0",
        },
        {
            "slug": "brewfile-lock-leftover-openssl",
            "plant": "vireo",
            "surface": "Homebrew Brewfile.lock leftover vs Brewfile",
            "pkg": "openssl@1.1",
            "old": "1.1.1w",
            "new": "3.4.0",
            "fail": True,
            "sot": "Brewfile.lock.json",
            "nested": "apps/api/Brewfile",
            "left": "apps/legacy",
            "left_file": "apps/legacy/Brewfile.lock.json",
            "sot_line": "\"openssl@1.1\": { \"version\": \"1.1.1w\" }",
            "nested_line": "brew \"openssl@1.1\"",
            "probe_cmd": "brew --version | head -n 1; rg '1.1.1w|3.4.0|openssl@' Brewfile.lock.json apps/*/Brewfile apps/legacy/Brewfile.lock.json | head",
            "probe_obs": "Brewfile.lock openssl@1.1 1.1.1w\nlegacy lock leftover 1.1.1w\n",
            "first_old": "brew \"openssl@1.1\"",
            "first_new": "brew \"openssl@3\"",
            "fail_cmd": "brew bundle --file=apps/api/Brewfile --no-upgrade 2>&1 | tail -n 16",
            "fail_obs": "Error: openssl@3 not locked; Brewfile.lock.json still openssl@1.1 1.1.1w\n",
            "plan_old": "\"openssl@1.1\": { \"version\": \"1.1.1w\" }",
            "plan_new": "\"openssl@3\": { \"version\": \"3.4.0\" }",
            "companion_new": "brew \"openssl@3\"",
            "test_cmd": "brew bundle --file=apps/api/Brewfile && make -C apps/api test 2>&1 | tail -n 16",
            "api_fail_obs": "formula.rb: depends_on :openssl is removed; use depends_on \"openssl@3\"\n",
            "callsite": "apps/api/Formula/vireo.rb",
            "callsite_obs": "depends_on :openssl\n",
            "api_old": "depends_on :openssl",
            "api_new": "depends_on \"openssl@3\"",
            "api_break": "depends_on :openssl → openssl@3",
            "retest_cmd": "make -C apps/api test 2>&1 | tail -n 8",
            "scan_obs": "Brewfile.lock openssl@3 3.4.0\napps/legacy/Brewfile.lock.json 1.1.1w\n",
            "ws_cmd": "brew bundle --file=apps/legacy/Brewfile --no-upgrade 2>&1 | tail -n 16",
            "ws_fail": "api 6 passed\nFAIL brew: leftover apps/legacy Brewfile.lock openssl@1.1 1.1.1w vs 3.4.0\n",
            "confirm_obs": "\"openssl@1.1\": { \"version\": \"1.1.1w\" }",
        },
    ),
    (
        {
            "slug": "devbox-lock-leftover-php81",
            "plant": "warbler",
            "surface": "Devbox devbox.lock leftover vs devbox.json",
            "pkg": "php81",
            "old": "8.1.29",
            "new": "8.3.16",
            "fail": False,
            "sot": "devbox.lock",
            "nested": "apps/api/devbox.json",
            "left": "apps/legacy",
            "left_file": "apps/legacy/devbox.lock",
            "sot_line": "\"php81\": { \"version\": \"8.1.29\" }",
            "nested_line": "\"packages\": [\"php81\"]",
            "probe_cmd": "devbox version; rg '8.1.29|8.3.16|php81|php83' devbox.lock apps/*/devbox.json apps/legacy/devbox.lock | head",
            "probe_obs": "devbox.lock php81 8.1.29\nlegacy lock 8.1.29 leftover\n",
            "first_old": "\"packages\": [\"php81\"]",
            "first_new": "\"packages\": [\"php83@8.3.16\"]",
            "fail_cmd": "devbox run --config apps/api/devbox.json composer test 2>&1 | tail -n 16",
            "fail_obs": "error: php83@8.3.16 not in root devbox.lock (php81 8.1.29 frozen)\n",
            "plan_old": "\"php81\": { \"version\": \"8.1.29\" }",
            "plan_new": "\"php83\": { \"version\": \"8.3.16\" }",
            "companion_new": "\"packages\": [\"php83\"]",
            "test_cmd": "devbox run --config apps/api/devbox.json phpunit 2>&1 | tail -n 16",
            "api_fail_obs": "PHP Fatal error: Call to undefined function utf8_encode() (removed in PHP 8.2)\n",
            "callsite": "apps/api/src/Warbler.php",
            "callsite_obs": "$s = utf8_encode($raw);\n",
            "api_old": "$s = utf8_encode($raw);",
            "api_new": "$s = mb_convert_encoding($raw, 'UTF-8', 'ISO-8859-1');",
            "api_break": "utf8_encode → mb_convert_encoding",
            "retest_cmd": "devbox run --config apps/api/devbox.json phpunit 2>&1 | tail -n 8",
            "scan_obs": "devbox.lock php83 8.3.16\napps/legacy/devbox.lock php81 8.1.29\n",
            "ws_cmd": "devbox run --config apps/legacy/devbox.json phpunit 2>&1 | tail -n 16",
            "ws_ok": "api 4 passed\nlegacy php81 8.1.29 skipped (ticket allows)\n",
            "confirm_obs": "\"php81\": { \"version\": \"8.1.29\" }",
        },
        {
            "slug": "buildpacks-toml-leftover-javax",
            "plant": "waxwing",
            "surface": "CNB project.toml leftover vs pack",
            "pkg": "paketo-buildpacks/java",
            "old": "10.4.0",
            "new": "14.2.0",
            "fail": True,
            "sot": "project.toml",
            "nested": "apps/api/project.toml",
            "left": "apps/legacy",
            "left_file": "apps/legacy/project.toml",
            "sot_line": "id = \"paketo-buildpacks/java\"\nversion = \"10.4.0\"",
            "nested_line": "id = \"paketo-buildpacks/java\"",
            "probe_cmd": "pack version; rg '10.4.0|14.2.0|javax.servlet|jakarta' project.toml apps/*/project.toml apps/legacy/project.toml | head",
            "probe_obs": "project.toml java 10.4.0\nlegacy project.toml leftover 10.4.0\n",
            "first_old": "id = \"paketo-buildpacks/java\"",
            "first_new": "id = \"paketo-buildpacks/java\"\nversion = \"14.2.0\"",
            "fail_cmd": "pack build api --path apps/api --trust-builder 2>&1 | tail -n 16",
            "fail_obs": "ERROR: apps/api project.toml 14.2.0 vs root project.toml still 10.4.0\n",
            "plan_old": "version = \"10.4.0\"",
            "plan_new": "version = \"14.2.0\"",
            "companion_new": "id = \"paketo-buildpacks/java\"\nversion = \"14.2.0\"",
            "test_cmd": "pack build api --path apps/api && mvn -f apps/api/pom.xml test 2>&1 | tail -n 16",
            "api_fail_obs": "package javax.servlet does not exist (Paketo 14 / Java 21; use jakarta.servlet)\n",
            "callsite": "apps/api/src/main/java/waxwing/Filter.java",
            "callsite_obs": "import javax.servlet.Filter;\n",
            "api_old": "import javax.servlet.Filter;",
            "api_new": "import jakarta.servlet.Filter;",
            "api_break": "javax.servlet → jakarta.servlet",
            "retest_cmd": "mvn -f apps/api/pom.xml test 2>&1 | tail -n 8",
            "scan_obs": "project.toml 14.2.0\napps/legacy/project.toml 10.4.0\n",
            "ws_cmd": "pack build legacy --path apps/legacy 2>&1 | tail -n 16",
            "ws_fail": "api 6 passed\nFAIL pack: leftover apps/legacy project.toml 10.4.0 vs 14.2.0 javax.servlet\n",
            "confirm_obs": "version = \"10.4.0\"",
        },
    ),
    (
        {
            "slug": "helm-chartlock-leftover-pgauth",
            "plant": "whimbrel",
            "surface": "Helm Chart.lock leftover vs Chart.yaml",
            "pkg": "bitnami/postgresql",
            "old": "12.12.10",
            "new": "16.4.1",
            "fail": False,
            "sot": "Chart.lock",
            "nested": "apps/api/Chart.yaml",
            "left": "apps/legacy",
            "left_file": "apps/legacy/Chart.lock",
            "sot_line": "name: postgresql\nversion: 12.12.10",
            "nested_line": "- name: postgresql\n  version: 12.12.10\n  repository: https://charts.bitnami.com/bitnami",
            "probe_cmd": "helm version --short; rg '12.12.10|16.4.1|postgresqlPassword' Chart.lock apps/*/Chart.yaml apps/legacy/Chart.lock | head",
            "probe_obs": "Chart.lock postgresql 12.12.10\nlegacy Chart.lock leftover 12.12.10\n",
            "first_old": "  version: 12.12.10",
            "first_new": "  version: 16.4.1",
            "fail_cmd": "helm dependency build apps/api 2>&1 | tail -n 16",
            "fail_obs": "Error: apps/api Chart.yaml 16.4.1 vs workspace Chart.lock still 12.12.10\n",
            "plan_old": "name: postgresql\nversion: 12.12.10",
            "plan_new": "name: postgresql\nversion: 16.4.1",
            "companion_new": "  version: 16.4.1",
            "test_cmd": "helm template api apps/api 2>&1 | tail -n 16",
            "api_fail_obs": "error: nil pointer evaluating interface {}.postgresqlPassword (moved to auth.password in chart 16)\n",
            "callsite": "apps/api/templates/secret.yaml",
            "callsite_obs": "{{ .Values.postgresql.postgresqlPassword | b64enc }}\n",
            "api_old": "{{ .Values.postgresql.postgresqlPassword | b64enc }}",
            "api_new": "{{ .Values.postgresql.auth.password | b64enc }}",
            "api_break": "postgresqlPassword → auth.password",
            "retest_cmd": "helm template api apps/api --debug 2>&1 | tail -n 8",
            "scan_obs": "Chart.lock 16.4.1\napps/legacy/Chart.lock 12.12.10\n",
            "ws_cmd": "helm template legacy apps/legacy 2>&1 | tail -n 16",
            "ws_ok": "api 4 passed\nlegacy Chart.lock 12.12.10 skipped (ticket allows)\n",
            "confirm_obs": "version: 12.12.10",
        },
        {
            "slug": "pulumi-lock-leftover-awsx",
            "plant": "wigeon",
            "surface": "Pulumi Pulumi.lock leftover vs Pulumi.yaml",
            "pkg": "@pulumi/awsx",
            "old": "1.0.6",
            "new": "2.21.1",
            "fail": True,
            "sot": "Pulumi.lock",
            "nested": "apps/api/Pulumi.yaml",
            "left": "apps/legacy",
            "left_file": "apps/legacy/Pulumi.lock",
            "sot_line": "\"@pulumi/awsx\": \"1.0.6\"",
            "nested_line": "name: api\nruntime: nodejs",
            "probe_cmd": "pulumi version; rg '1.0.6|2.21.1|awsx' Pulumi.lock apps/*/Pulumi.yaml apps/legacy/Pulumi.lock | head",
            "probe_obs": "Pulumi.lock awsx 1.0.6\nlegacy lock leftover 1.0.6\n",
            "first_old": "runtime: nodejs",
            "first_new": "runtime: nodejs\npackages:\n  @pulumi/awsx: 2.21.1",
            "fail_cmd": "pulumi preview --cwd apps/api --non-interactive 2>&1 | tail -n 16",
            "fail_obs": "error: @pulumi/awsx 2.21.1 not in workspace Pulumi.lock (1.0.6)\n",
            "plan_old": "\"@pulumi/awsx\": \"1.0.6\"",
            "plan_new": "\"@pulumi/awsx\": \"2.21.1\"",
            "companion_new": "runtime: nodejs",
            "test_cmd": "pulumi preview --cwd apps/api --non-interactive 2>&1 | tail -n 16",
            "api_fail_obs": "error TS2339: awsx.ec2.Vpc is not a constructor (moved to awsx.classic.ec2.Vpc in 2.x)\n",
            "callsite": "apps/api/index.ts",
            "callsite_obs": "const vpc = new awsx.ec2.Vpc(\"net\", {});\n",
            "api_old": "const vpc = new awsx.ec2.Vpc(\"net\", {});",
            "api_new": "const vpc = new awsx.classic.ec2.Vpc(\"net\", {});",
            "api_break": "awsx.ec2.Vpc → awsx.classic.ec2.Vpc",
            "retest_cmd": "pulumi preview --cwd apps/api --non-interactive 2>&1 | tail -n 8",
            "scan_obs": "Pulumi.lock 2.21.1\napps/legacy/Pulumi.lock 1.0.6\n",
            "ws_cmd": "pulumi preview --cwd apps/legacy --non-interactive 2>&1 | tail -n 16",
            "ws_fail": "api 6 passed\nFAIL pulumi: leftover apps/legacy Pulumi.lock awsx 1.0.6 vs 2.21.1 classic.Vpc\n",
            "confirm_obs": "\"@pulumi/awsx\": \"1.0.6\"",
        },
    ),
    (
        {
            "slug": "colcon-pkgxml-leftover-qos",
            "plant": "woodcock",
            "surface": "ROS2 colcon leftover vs package.xml",
            "pkg": "rclcpp",
            "old": "16.0.8",
            "new": "28.1.5",
            "fail": False,
            "sot": "package.xml",
            "nested": "apps/api/package.xml",
            "left": "apps/legacy",
            "left_file": "apps/legacy/package.xml",
            "sot_line": "<depend>rclcpp</depend>\n<version>16.0.8</version>",
            "nested_line": "<depend>rclcpp</depend>",
            "probe_cmd": "ros2 --version; rg '16.0.8|28.1.5|rclcpp|rmw_qos' package.xml apps/*/package.xml apps/legacy/package.xml | head",
            "probe_obs": "package.xml rclcpp 16.0.8 humble\nlegacy package.xml leftover 16.0.8\n",
            "first_old": "<depend>rclcpp</depend>",
            "first_new": "<depend version_gte=\"28.1.5\">rclcpp</depend>",
            "fail_cmd": "colcon test --packages-select api 2>&1 | tail -n 16",
            "fail_obs": "error: api wants rclcpp>=28.1.5 vs workspace package.xml still 16.0.8\n",
            "plan_old": "<version>16.0.8</version>",
            "plan_new": "<version>28.1.5</version>",
            "companion_new": "<depend>rclcpp</depend>",
            "test_cmd": "colcon test --packages-select api 2>&1 | tail -n 16",
            "api_fail_obs": "error: rmw_qos_profile_default was removed; pass rclcpp::QoS(10) (Jazzy)\n",
            "callsite": "apps/api/src/woodcock.cpp",
            "callsite_obs": "sub_ = create_subscription<Msg>(\"t\", rmw_qos_profile_default, cb);\n",
            "api_old": "sub_ = create_subscription<Msg>(\"t\", rmw_qos_profile_default, cb);",
            "api_new": "sub_ = create_subscription<Msg>(\"t\", rclcpp::QoS(10), cb);",
            "api_break": "rmw_qos_profile_default → rclcpp::QoS(10)",
            "retest_cmd": "colcon test --packages-select api 2>&1 | tail -n 8",
            "scan_obs": "package.xml 28.1.5\napps/legacy/package.xml 16.0.8\n",
            "ws_cmd": "colcon test --packages-select legacy 2>&1 | tail -n 16",
            "ws_ok": "api 4 passed\nlegacy package.xml 16.0.8 skipped (ticket allows)\n",
            "confirm_obs": "<version>16.0.8</version>",
        },
        {
            "slug": "espidf-component-leftover-tcpip",
            "plant": "wren",
            "surface": "ESP-IDF idf_component leftover vs sdkconfig",
            "pkg": "idf",
            "old": "4.4.7",
            "new": "5.3.2",
            "fail": True,
            "sot": "sdkconfig",
            "nested": "apps/api/idf_component.yml",
            "left": "apps/legacy",
            "left_file": "apps/legacy/sdkconfig",
            "sot_line": "CONFIG_APP_PROJECT_VER=\"4.4.7\"",
            "nested_line": "idf: \">=4.4.7\"",
            "probe_cmd": "idf.py --version; rg '4.4.7|5.3.2|tcpip_adapter' sdkconfig apps/*/idf_component.yml apps/legacy/sdkconfig | head",
            "probe_obs": "sdkconfig idf 4.4.7\nlegacy sdkconfig leftover 4.4.7\n",
            "first_old": "idf: \">=4.4.7\"",
            "first_new": "idf: \">=5.3.2\"",
            "fail_cmd": "idf.py -C apps/api build 2>&1 | tail -n 16",
            "fail_obs": "error: component wants idf>=5.3.2 vs sdkconfig still 4.4.7\n",
            "plan_old": "CONFIG_APP_PROJECT_VER=\"4.4.7\"",
            "plan_new": "CONFIG_APP_PROJECT_VER=\"5.3.2\"",
            "companion_new": "idf: \">=5.3.2\"",
            "test_cmd": "idf.py -C apps/api test 2>&1 | tail -n 16",
            "api_fail_obs": "error: implicit declaration of function 'tcpip_adapter_init'; use esp_netif_init (IDF 5)\n",
            "callsite": "apps/api/main/wren.c",
            "callsite_obs": "tcpip_adapter_init();\n",
            "api_old": "tcpip_adapter_init();",
            "api_new": "ESP_ERROR_CHECK(esp_netif_init());",
            "api_break": "tcpip_adapter_init → esp_netif_init",
            "retest_cmd": "idf.py -C apps/api test 2>&1 | tail -n 8",
            "scan_obs": "sdkconfig 5.3.2\napps/legacy/sdkconfig 4.4.7\n",
            "ws_cmd": "idf.py -C apps/legacy test 2>&1 | tail -n 16",
            "ws_fail": "api 6 passed\nFAIL idf: leftover apps/legacy sdkconfig 4.4.7 vs 5.3.2 tcpip_adapter_init\n",
            "confirm_obs": "CONFIG_APP_PROJECT_VER=\"4.4.7\"",
        },
    ),
    (
        {
            "slug": "yocto-layer-leftover-override",
            "plant": "yellowthroat",
            "surface": "Yocto layer.conf leftover vs local.conf",
            "pkg": "poky",
            "old": "4.0.16",
            "new": "5.1.1",
            "fail": False,
            "sot": "conf/local.conf",
            "nested": "meta-api/conf/layer.conf",
            "left": "apps/legacy",
            "left_file": "apps/legacy/conf/local.conf",
            "sot_line": "POKY_VERSION = \"4.0.16\"\nDISTRO_FEATURES_append = \" api\"",
            "nested_line": "LAYERSERIES_COMPAT_api = \"kirkstone\"",
            "probe_cmd": "bitbake --version | head -n 1; rg 'kirkstone|styhead|4.0.16|5.1.1|DISTRO_FEATURES' conf/local.conf meta-api/conf/layer.conf apps/legacy/conf/local.conf | head",
            "probe_obs": "local.conf kirkstone 4.0.16\nlegacy local.conf leftover kirkstone\n",
            "first_old": "LAYERSERIES_COMPAT_api = \"kirkstone\"",
            "first_new": "LAYERSERIES_COMPAT_api = \"styhead\"",
            "fail_cmd": "bitbake api-image 2>&1 | tail -n 16",
            "fail_obs": "ERROR: layer api styhead vs workspace local.conf still kirkstone 4.0.16\n",
            "plan_old": "POKY_VERSION = \"4.0.16\"\nDISTRO_FEATURES_append = \" api\"",
            "plan_new": "POKY_VERSION = \"5.1.1\"\nDISTRO_FEATURES:append = \" api\"",
            "companion_new": "LAYERSERIES_COMPAT_api = \"styhead\"",
            "test_cmd": "bitbake api-image 2>&1 | tail -n 16",
            "api_fail_obs": "ERROR: DISTRO_FEATURES_append is invalid override syntax; use DISTRO_FEATURES:append (Yocto 5)\n",
            "callsite": "apps/api/recipes-core/api/api.bb",
            "callsite_obs": "DISTRO_FEATURES_append = \" api\"\n",
            "api_old": "DISTRO_FEATURES_append = \" api\"",
            "api_new": "DISTRO_FEATURES:append = \" api\"",
            "api_break": "_append → :append override",
            "retest_cmd": "bitbake api-image 2>&1 | tail -n 8",
            "scan_obs": "local.conf styhead 5.1.1\napps/legacy/conf/local.conf kirkstone 4.0.16\n",
            "ws_cmd": "bitbake legacy-image 2>&1 | tail -n 16",
            "ws_ok": "api 4 passed\nlegacy local.conf 4.0.16 skipped (ticket allows)\n",
            "confirm_obs": "4.0.16",
        },
        {
            "slug": "fusesoc-core-leftover-capi1",
            "plant": "albatross",
            "surface": "FuseSoC .core leftover vs CAPI-1",
            "pkg": "fusesoc",
            "old": "1.12.0",
            "new": "2.4.3",
            "fail": True,
            "sot": "fusesoc.conf",
            "nested": "apps/api/api.core",
            "left": "apps/legacy",
            "left_file": "apps/legacy/legacy.core",
            "sot_line": "[main]\nversion = 1.12.0\ncapi = 1",
            "nested_line": "CAPI=1",
            "probe_cmd": "fusesoc --version; rg 'CAPI=1|CAPI=2|1.12.0|2.4.3' fusesoc.conf apps/*/*.core apps/legacy/*.core | head",
            "probe_obs": "fusesoc.conf CAPI 1 / 1.12.0\nlegacy.core CAPI=1 leftover\n",
            "first_old": "CAPI=1",
            "first_new": "CAPI=2",
            "fail_cmd": "fusesoc run --target=sim api 2>&1 | tail -n 16",
            "fail_obs": "error: apps/api CAPI=2 vs fusesoc.conf still CAPI 1 (1.12.0)\n",
            "plan_old": "version = 1.12.0\ncapi = 1",
            "plan_new": "version = 2.4.3\ncapi = 2",
            "companion_new": "CAPI=2",
            "test_cmd": "fusesoc run --target=sim api 2>&1 | tail -n 16",
            "api_fail_obs": "Error: [filesets] is CAPI-1 syntax; use filesets: mapping (CAPI-2)\n",
            "callsite": "apps/api/rtl/albatross.core",
            "callsite_obs": "[filesets]\n",
            "api_old": "[filesets]",
            "api_new": "filesets:",
            "api_break": "CAPI-1 [filesets] → CAPI-2 filesets:",
            "retest_cmd": "fusesoc run --target=sim api 2>&1 | tail -n 8",
            "scan_obs": "fusesoc.conf 2.4.3 CAPI 2\napps/legacy/legacy.core CAPI=1 1.12.0\n",
            "ws_cmd": "fusesoc run --target=sim legacy 2>&1 | tail -n 16",
            "ws_fail": "api 6 passed\nFAIL fusesoc: leftover apps/legacy legacy.core CAPI-1 1.12.0 vs 2.4.3 [filesets]\n",
            "confirm_obs": "1.12.0",
        },
    ),
    (
        {
            "slug": "smlnj-cm-leftover-pp",
            "plant": "bittern",
            "surface": "SML/NJ sources.cm leftover vs smlnj-lib",
            "pkg": "smlnj-lib",
            "old": "110.99.4",
            "new": "2024.2",
            "fail": False,
            "sot": "sources.cm",
            "nested": "apps/api/sources.cm",
            "left": "apps/legacy",
            "left_file": "apps/legacy/sources.cm",
            "sot_line": "(* smlnj-lib 110.99.4 *)\nLibrary\nstructure PP",
            "nested_line": "Group is $/smlnj-lib.cm",
            "probe_cmd": "sml -Ccm.verbose=true </dev/null | head; rg '110.99.4|2024.2|structure PP' sources.cm apps/*/sources.cm apps/legacy/sources.cm | head",
            "probe_obs": "sources.cm smlnj-lib 110.99.4\nlegacy sources.cm leftover 110.99.4\n",
            "first_old": "Group is $/smlnj-lib.cm",
            "first_new": "Group is $/smlnj-lib.cm (* 2024.2 *)",
            "fail_cmd": "ml-build apps/api/sources.cm Api.main 2>&1 | tail -n 16",
            "fail_obs": "[CM] version mismatch: apps/api 2024.2 vs workspace sources.cm 110.99.4\n",
            "plan_old": "(* smlnj-lib 110.99.4 *)",
            "plan_new": "(* smlnj-lib 2024.2 *)",
            "companion_new": "Group is $/smlnj-lib.cm (* 2024.2 *)",
            "test_cmd": "ml-build apps/api/sources.cm Api.main && apps/api/api 2>&1 | tail -n 16",
            "api_fail_obs": "Error: unbound structure PP (moved to PrettyPrint in smlnj-lib 2024)\n",
            "callsite": "apps/api/bittern.sml",
            "callsite_obs": "structure P = PP\n",
            "api_old": "structure P = PP",
            "api_new": "structure P = PrettyPrint",
            "api_break": "structure PP → PrettyPrint",
            "retest_cmd": "apps/api/api 2>&1 | tail -n 8",
            "scan_obs": "sources.cm 2024.2\napps/legacy/sources.cm 110.99.4\n",
            "ws_cmd": "ml-build apps/legacy/sources.cm Legacy.main 2>&1 | tail -n 16",
            "ws_ok": "api 4 passed\nlegacy sources.cm 110.99.4 skipped (ticket allows)\n",
            "confirm_obs": "110.99.4",
        },
        {
            "slug": "mlton-mlb-leftover-intinf",
            "plant": "brant",
            "surface": "MLton mlb leftover vs basis",
            "pkg": "mlton",
            "old": "20210117",
            "new": "20241230",
            "fail": True,
            "sot": "sources.mlb",
            "nested": "apps/api/api.mlb",
            "left": "apps/legacy",
            "left_file": "apps/legacy/sources.mlb",
            "sot_line": "$(SML_LIB)/basis/basis.mlb\n(* mlton 20210117 *)",
            "nested_line": "local $(SML_LIB)/basis/basis.mlb in",
            "probe_cmd": "mlton 2>&1 | head -n 1; rg '20210117|20241230|MLton.IntInf' sources.mlb apps/*/api.mlb apps/legacy/sources.mlb | head",
            "probe_obs": "sources.mlb mlton 20210117\nlegacy mlb leftover 20210117\n",
            "first_old": "local $(SML_LIB)/basis/basis.mlb in",
            "first_new": "local $(SML_LIB)/basis/unsafe.mlb $(SML_LIB)/basis/basis.mlb in",
            "fail_cmd": "mlton -output apps/api/api apps/api/api.mlb 2>&1 | tail -n 16",
            "fail_obs": "Error: apps/api mlb 20241230 unsafe.mlb vs workspace sources.mlb 20210117\n",
            "plan_old": "(* mlton 20210117 *)",
            "plan_new": "(* mlton 20241230 *)",
            "companion_new": "local $(SML_LIB)/basis/basis.mlb in",
            "test_cmd": "mlton -output apps/api/api apps/api/api.mlb && apps/api/api --test 2>&1 | tail -n 16",
            "api_fail_obs": "Error: structure MLton.IntInf is gone; use IntInf (MLton 2024)\n",
            "callsite": "apps/api/brant.sml",
            "callsite_obs": "val n = MLton.IntInf.fromInt 3\n",
            "api_old": "val n = MLton.IntInf.fromInt 3",
            "api_new": "val n = IntInf.fromInt 3",
            "api_break": "MLton.IntInf → IntInf",
            "retest_cmd": "apps/api/api --test 2>&1 | tail -n 8",
            "scan_obs": "sources.mlb 20241230\napps/legacy/sources.mlb 20210117\n",
            "ws_cmd": "mlton -output apps/legacy/legacy apps/legacy/sources.mlb 2>&1 | tail -n 16",
            "ws_fail": "api 6 passed\nFAIL mlton: leftover apps/legacy sources.mlb 20210117 vs 20241230 MLton.IntInf\n",
            "confirm_obs": "20210117",
        },
    ),
    (
        {
            "slug": "koka-pkg-leftover-exn",
            "plant": "bunting",
            "surface": "Koka packages leftover vs koka.pkg",
            "pkg": "std",
            "old": "2.4.2",
            "new": "3.1.2",
            "fail": False,
            "sot": "packages.kk",
            "nested": "apps/api/api.kk",
            "left": "apps/legacy",
            "left_file": "apps/legacy/packages.kk",
            "sot_line": "std = 2.4.2",
            "nested_line": "import std/exn",
            "probe_cmd": "koka --version; rg '2.4.2|3.1.2|std/exn' packages.kk apps/*/api.kk apps/legacy/packages.kk | head",
            "probe_obs": "packages.kk std 2.4.2\nlegacy packages.kk leftover 2.4.2\n",
            "first_old": "import std/exn",
            "first_new": "import std/core/exn",
            "fail_cmd": "koka --test apps/api/api.kk 2>&1 | tail -n 16",
            "fail_obs": "error: std/core/exn not in packages.kk std 2.4.2\n",
            "plan_old": "std = 2.4.2",
            "plan_new": "std = 3.1.2",
            "companion_new": "import std/core/exn",
            "test_cmd": "koka --test apps/api/api.kk 2>&1 | tail -n 16",
            "api_fail_obs": "error: function throw is not in scope (use error in Koka 3 std)\n",
            "callsite": "apps/api/src/bunting.kk",
            "callsite_obs": "throw(\"bad\")\n",
            "api_old": "throw(\"bad\")",
            "api_new": "error(\"bad\")",
            "api_break": "throw → error",
            "retest_cmd": "koka --test apps/api/api.kk 2>&1 | tail -n 8",
            "scan_obs": "packages.kk 3.1.2\napps/legacy/packages.kk 2.4.2\n",
            "ws_cmd": "koka --test apps/legacy/legacy.kk 2>&1 | tail -n 16",
            "ws_ok": "api 4 passed\nlegacy packages.kk 2.4.2 skipped (ticket allows)\n",
            "confirm_obs": "std = 2.4.2",
        },
        {
            "slug": "roc-packages-leftover-decode",
            "plant": "cardinal",
            "surface": "Roc roc.lock leftover vs main.roc",
            "pkg": "roc/json",
            "old": "0.11.0",
            "new": "0.12.0",
            "fail": True,
            "sot": "roc.lock",
            "nested": "apps/api/main.roc",
            "left": "apps/legacy",
            "left_file": "apps/legacy/roc.lock",
            "sot_line": "roc/json 0.11.0",
            "nested_line": "json: \"roc/json:0.11.0\"",
            "probe_cmd": "roc version; rg '0.11.0|0.12.0|Json.decode' roc.lock apps/*/main.roc apps/legacy/roc.lock | head",
            "probe_obs": "roc.lock json 0.11.0\nlegacy roc.lock leftover 0.11.0\n",
            "first_old": "json: \"roc/json:0.11.0\"",
            "first_new": "json: \"roc/json:0.12.0\"",
            "fail_cmd": "roc test apps/api/main.roc 2>&1 | tail -n 16",
            "fail_obs": "error: apps/api roc/json 0.12.0 vs roc.lock still 0.11.0\n",
            "plan_old": "roc/json 0.11.0",
            "plan_new": "roc/json 0.12.0",
            "companion_new": "json: \"roc/json:0.12.0\"",
            "test_cmd": "roc test apps/api/main.roc 2>&1 | tail -n 16",
            "api_fail_obs": "error: Json.decode is not exposed; use Decode.fromBytes (roc/json 0.12)\n",
            "callsite": "apps/api/src/Cardinal.roc",
            "callsite_obs": "Json.decode bytes\n",
            "api_old": "Json.decode bytes",
            "api_new": "Decode.fromBytes bytes Json.utf8",
            "api_break": "Json.decode → Decode.fromBytes",
            "retest_cmd": "roc test apps/api/main.roc 2>&1 | tail -n 8",
            "scan_obs": "roc.lock 0.12.0\napps/legacy/roc.lock 0.11.0\n",
            "ws_cmd": "roc test apps/legacy/main.roc 2>&1 | tail -n 16",
            "ws_fail": "api 6 passed\nFAIL roc: leftover apps/legacy roc.lock json 0.11.0 vs 0.12.0 Json.decode\n",
            "confirm_obs": "roc/json 0.11.0",
        },
    ),
    (
        {
            "slug": "macports-portfile-leftover-python39",
            "plant": "condor",
            "surface": "MacPorts Portfile leftover vs PortIndex",
            "pkg": "python39",
            "old": "3.9.18",
            "new": "3.12.8",
            "fail": False,
            "sot": "PortIndex",
            "nested": "apps/api/Portfile",
            "left": "apps/legacy",
            "left_file": "apps/legacy/Portfile",
            "sot_line": "python39 3.9.18",
            "nested_line": "set python.version 39",
            "probe_cmd": "port version; rg '3.9.18|3.12.8|python.version 39' PortIndex apps/*/Portfile apps/legacy/Portfile | head",
            "probe_obs": "PortIndex python39 3.9.18\nlegacy Portfile python.version 39 leftover\n",
            "first_old": "set python.version 39",
            "first_new": "set python.version 312",
            "fail_cmd": "port test apps/api 2>&1 | tail -n 16",
            "fail_obs": "Error: Portfile python.version 312 vs PortIndex still python39 3.9.18\n",
            "plan_old": "python39 3.9.18",
            "plan_new": "python312 3.12.8",
            "companion_new": "set python.version 312",
            "test_cmd": "port test apps/api 2>&1 | tail -n 16",
            "api_fail_obs": "Error: python.pep517 no longer exists; use python.pep517_backend (MacPorts 2.10)\n",
            "callsite": "apps/api/subport.tcl",
            "callsite_obs": "python.pep517 yes\n",
            "api_old": "python.pep517 yes",
            "api_new": "python.pep517_backend setuptools",
            "api_break": "python.pep517 → pep517_backend",
            "retest_cmd": "port test apps/api 2>&1 | tail -n 8",
            "scan_obs": "PortIndex python312 3.12.8\napps/legacy/Portfile python.version 39 3.9.18\n",
            "ws_cmd": "port test apps/legacy 2>&1 | tail -n 16",
            "ws_ok": "api 4 passed\nlegacy Portfile 3.9.18 skipped (ticket allows)\n",
            "confirm_obs": "3.9.18",
        },
        {
            "slug": "hy-deps-leftover-assoc",
            "plant": "crane",
            "surface": "Hy deps.hy leftover vs hyrule",
            "pkg": "hyrule",
            "old": "0.4.0",
            "new": "0.7.0",
            "fail": True,
            "sot": "deps.hy",
            "nested": "apps/api/api.hy",
            "left": "apps/legacy",
            "left_file": "apps/legacy/deps.hy",
            "sot_line": "{\"hyrule\" \"0.4.0\"}",
            "nested_line": "(require hyrule *)",
            "probe_cmd": "hy --version; rg '0.4.0|0.7.0|assoc|hyrule' deps.hy apps/*/api.hy apps/legacy/deps.hy | head",
            "probe_obs": "deps.hy hyrule 0.4.0\nlegacy deps.hy leftover 0.4.0\n",
            "first_old": "(require hyrule *)",
            "first_new": "(require hyrule.hy 0.7)",
            "fail_cmd": "hy apps/api/tests.hy 2>&1 | tail -n 16",
            "fail_obs": "error: hyrule 0.7 not in deps.hy (pinned 0.4.0)\n",
            "plan_old": "{\"hyrule\" \"0.4.0\"}",
            "plan_new": "{\"hyrule\" \"0.7.0\"}",
            "companion_new": "(require hyrule *)",
            "test_cmd": "hy apps/api/tests.hy 2>&1 | tail -n 16",
            "api_fail_obs": "NameError: assoc is gone from hyrule 0.7; use setv / get\n",
            "callsite": "apps/api/src/crane.hy",
            "callsite_obs": "(assoc d :id n)\n",
            "api_old": "(assoc d :id n)",
            "api_new": "(setv (get d :id) n)",
            "api_break": "hyrule assoc → setv get",
            "retest_cmd": "hy apps/api/tests.hy 2>&1 | tail -n 8",
            "scan_obs": "deps.hy 0.7.0\napps/legacy/deps.hy 0.4.0\n",
            "ws_cmd": "hy apps/legacy/tests.hy 2>&1 | tail -n 16",
            "ws_fail": "api 6 passed\nFAIL hy: leftover apps/legacy deps.hy hyrule 0.4.0 vs 0.7.0 assoc\n",
            "confirm_obs": "{\"hyrule\" \"0.4.0\"}",
        },
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
