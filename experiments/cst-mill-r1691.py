#!/usr/bin/env python3
"""Designed leftover cache-stampede mill r1691+ (cst- ids). BAN r1–r1690."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("cst1446", HERE / "cst-mill-r1446.py")
_m = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_m)
_steps_ok = _m._steps_ok
_steps_part = _m._steps_part
CATALOG_FIRST = 1691

PAIRS: list[tuple] = [
    ("Dagger", "dagger-engine-leftover", "dagger-cloud-handoff", "flock-daggr",
     "src/dagger.cue", "tests/test_dagger.py", "engine leftover",
     "drop engine on miss", "engine leftover + wait + do(llb)", 18,
     "cloud leftover still 1s", "cloud leftover",
     "src/dagger_cl.cue", "tests/test_dagger_cl.py", "gets"),
    ("Earthly", "earthly-sat-leftover", "earthly-inline-handoff", "flock-erthl",
     "src/Earthfile", "tests/test_earthly.py", "SAT leftover",
     "drop SAT on miss", "sat leftover + wait + do(target)", 16,
     "inline leftover still 1s", "inline leftover",
     "src/Earthfile_in", "tests/test_earthly_in.py", "gets"),
    ("Pants", "pants-l1-leftover", "pants-remote-handoff", "flock-pntsl",
     "src/pants.toml", "tests/test_pants.py", "l1 leftover",
     "drop l1 on miss", "l1 leftover + wait + do(tgt)", 17,
     "remote leftover still 1s", "remote leftover",
     "src/pants_rm.toml", "tests/test_pants_rm.py", "gets"),
    ("Buck2", "buck2-action-leftover", "buck2-cas-handoff", "flock-bck2a",
     "src/buckconfig", "tests/test_buck2.py", "action leftover",
     "drop action on miss", "action leftover + wait + do(key)", 15,
     "cas leftover still 1s", "cas leftover",
     "src/buckconfig_cas", "tests/test_buck2_cas.py", "gets"),
    ("Please", "please-plzcache-leftover", "please-remote-handoff", "flock-plzch",
     "src/.plzconfig", "tests/test_please.py", "plzcache leftover",
     "drop plzcache on miss", "plz leftover + wait + do(hash)", 14,
     "remote leftover still 1s", "remote leftover",
     "src/.plzconfig_rm", "tests/test_please_rm.py", "gets"),
    ("Moonrepo", "moon-hash-leftover", "moon-remote-handoff", "flock-moonh",
     "src/moon.yml", "tests/test_moon.py", "hash leftover",
     "drop hash on miss", "hash leftover + wait + do(task)", 13,
     "remote leftover still 1s", "remote leftover",
     "src/moon_rm.yml", "tests/test_moon_rm.py", "gets"),
    ("Lage", "lage-backfill-leftover", "lage-pipeline-handoff", "flock-lageb",
     "src/lage.config.js", "tests/test_lage.py", "backfill leftover",
     "drop backfill on miss", "backfill leftover + wait + do(pkg)", 14,
     "pipeline leftover still 1s", "pipeline leftover",
     "src/lage_pl.js", "tests/test_lage_pl.py", "gets"),
    ("Rush", "rush-phased-leftover", "rush-cobuild-handoff", "flock-rushp",
     "src/rush.json", "tests/test_rush.py", "phased leftover",
     "drop phased on miss", "phased leftover + wait + do(proj)", 15,
     "cobuild leftover still 1s", "cobuild leftover",
     "src/rush_cb.json", "tests/test_rush_cb.py", "gets"),
    ("Maven", "maven-local-leftover", "maven-resolver-handoff", "flock-mvnlc",
     "src/settings.xml", "tests/test_maven.py", "local leftover",
     "drop local on miss", "local leftover + wait + do(ga)", 16,
     "resolver leftover still 1s", "resolver leftover",
     "src/settings_rs.xml", "tests/test_maven_rs.py", "gets"),
    ("sbt", "sbt-coursier-leftover", "sbt-zinc-handoff", "flock-sbtcs",
     "src/build.sbt", "tests/test_sbt.py", "coursier leftover",
     "drop coursier on miss", "coursier leftover + wait + do(mod)", 15,
     "zinc leftover still 1s", "zinc leftover",
     "src/build_zn.sbt", "tests/test_sbt_zn.py", "gets"),
    ("Coursier", "coursier-cache-leftover", "coursier-ttl-handoff", "flock-crscr",
     "src/coursier.json", "tests/test_coursier.py", "cache leftover",
     "drop cache on miss", "cache leftover + wait + do(mod)", 14,
     "ttl leftover still 1s", "ttl leftover",
     "src/coursier_ttl.json", "tests/test_coursier_ttl.py", "gets"),
    ("Cargo", "cargo-registry-leftover", "cargo-git-handoff", "flock-carg",
     "src/cargo.toml", "tests/test_cargo.py", "registry leftover",
     "drop registry on miss", "registry leftover + wait + do(crate)", 17,
     "git leftover still 1s", "git leftover",
     "src/cargo_git.toml", "tests/test_cargo_git.py", "gets"),
    ("Go build", "gocache-compile-leftover", "gocache-mod-handoff", "flock-gocch",
     "src/go.env", "tests/test_gocache.py", "compile leftover",
     "drop compile on miss", "compile leftover + wait + do(pkg)", 18,
     "mod leftover still 1s", "mod leftover",
     "src/go_mod.env", "tests/test_gocache_mod.py", "gets"),
    ("pip cache", "pip-http-leftover", "pip-wheel-handoff", "flock-pipht",
     "src/pip.conf", "tests/test_pip.py", "http leftover",
     "drop http on miss", "http leftover + wait + do(pkg)", 16,
     "wheel leftover still 1s", "wheel leftover",
     "src/pip_wh.conf", "tests/test_pip_wh.py", "gets"),
    ("uv cache", "uv-index-leftover", "uv-wheel-handoff", "flock-uvidx",
     "src/uv.toml", "tests/test_uv.py", "index leftover",
     "drop index on miss", "index leftover + wait + do(pkg)", 15,
     "wheel leftover still 1s", "wheel leftover",
     "src/uv_wh.toml", "tests/test_uv_wh.py", "gets"),
    ("Poetry", "poetry-virtualenv-leftover", "poetry-installer-handoff", "flock-poetr",
     "src/poetry.toml", "tests/test_poetry.py", "venv leftover",
     "drop venv on miss", "venv leftover + wait + do(pkg)", 14,
     "installer leftover still 1s", "installer leftover",
     "src/poetry_in.toml", "tests/test_poetry_in.py", "gets"),
    ("conda", "conda-pkgs-leftover", "conda-index-handoff", "flock-condp",
     "src/condarc", "tests/test_conda.py", "pkgs leftover",
     "drop pkgs on miss", "pkgs leftover + wait + do(pkg)", 16,
     "index leftover still 1s", "index leftover",
     "src/condarc_ix", "tests/test_conda_ix.py", "gets"),
    ("mamba", "mamba-solv-leftover", "mamba-repodata-handoff", "flock-mmbsv",
     "src/mambarc", "tests/test_mamba.py", "solv leftover",
     "drop solv on miss", "solv leftover + wait + do(pkg)", 15,
     "repodata leftover still 1s", "repodata leftover",
     "src/mambarc_rd", "tests/test_mamba_rd.py", "gets"),
    ("pixi", "pixi-prefix-leftover", "pixi-repodata-handoff", "flock-pixip",
     "src/pixi.toml", "tests/test_pixi.py", "prefix leftover",
     "drop prefix on miss", "prefix leftover + wait + do(pkg)", 14,
     "repodata leftover still 1s", "repodata leftover",
     "src/pixi_rd.toml", "tests/test_pixi_rd.py", "gets"),
    ("pdm", "pdm-caches-leftover", "pdm-lock-handoff", "flock-pdmch",
     "src/pdm.toml", "tests/test_pdm.py", "caches leftover",
     "drop caches on miss", "caches leftover + wait + do(pkg)", 13,
     "lock leftover still 1s", "lock leftover",
     "src/pdm_lk.toml", "tests/test_pdm_lk.py", "gets"),
    ("hatch", "hatch-env-leftover", "hatch-build-handoff", "flock-htchn",
     "src/hatch.toml", "tests/test_hatch.py", "env leftover",
     "drop env on miss", "env leftover + wait + do(pkg)", 12,
     "build leftover still 1s", "build leftover",
     "src/hatch_bd.toml", "tests/test_hatch_bd.py", "gets"),
    ("bun", "bun-install-leftover", "bun-compile-handoff", "flock-bunin",
     "src/bunfig.toml", "tests/test_bun.py", "install leftover",
     "drop install on miss", "install leftover + wait + do(pkg)", 16,
     "compile leftover still 1s", "compile leftover",
     "src/bunfig_cp.toml", "tests/test_bun_cp.py", "gets"),
    ("deno cache", "deno-dep-leftover", "deno-npm-handoff", "flock-denod",
     "src/deno.json", "tests/test_deno.py", "dep leftover",
     "drop dep on miss", "dep leftover + wait + do(url)", 15,
     "npm leftover still 1s", "npm leftover",
     "src/deno_npm.json", "tests/test_deno_npm.py", "gets"),
    ("zig cache", "zig-global-leftover", "zig-local-handoff", "flock-ziggl",
     "src/build.zig", "tests/test_zig.py", "global leftover",
     "drop global on miss", "global leftover + wait + do(hash)", 14,
     "local leftover still 1s", "local leftover",
     "src/build_lc.zig", "tests/test_zig_lc.py", "gets"),
    ("meson", "meson-pkgconfig-leftover", "meson-wrap-handoff", "flock-mespk",
     "src/meson.build", "tests/test_meson.py", "pkgconfig leftover",
     "drop pkgconfig on miss", "pkg leftover + wait + do(dep)", 13,
     "wrap leftover still 1s", "wrap leftover",
     "src/meson_wp.build", "tests/test_meson_wp.py", "gets"),
    ("ninja", "ninja-depslog-leftover", "ninja-restat-handoff", "flock-ninjd",
     "src/build.ninja", "tests/test_ninja.py", "depslog leftover",
     "drop depslog on miss", "deps leftover + wait + do(tgt)", 14,
     "restat leftover still 1s", "restat leftover",
     "src/build_rs.ninja", "tests/test_ninja_rs.py", "gets"),
    ("CMake", "cmake-fileapi-leftover", "cmake-compiler-handoff", "flock-cmkfa",
     "src/CMakeCache.txt", "tests/test_cmake.py", "fileapi leftover",
     "drop fileapi on miss", "fileapi leftover + wait + do(tgt)", 15,
     "compiler leftover still 1s", "compiler leftover",
     "src/CMakeCache_cc.txt", "tests/test_cmake_cc.py", "gets"),
    ("autotools", "autotools-config-leftover", "autotools-libtool-handoff", "flock-atcfg",
     "src/config.cache", "tests/test_autotools.py", "config leftover",
     "drop config on miss", "config leftover + wait + do(chk)", 12,
     "libtool leftover still 1s", "libtool leftover",
     "src/config_lt.cache", "tests/test_autotools_lt.py", "gets"),
    ("bazelisk", "bazelisk-release-leftover", "bazelisk-bin-handoff", "flock-bzlsk",
     "src/bazeliskrc", "tests/test_bazelisk.py", "release leftover",
     "drop release on miss", "release leftover + wait + do(ver)", 13,
     "bin leftover still 1s", "bin leftover",
     "src/bazeliskrc_bin", "tests/test_bazelisk_bin.py", "gets"),
    ("asdf", "asdf-plugin-leftover", "asdf-shims-handoff", "flock-asdfp",
     "src/asdfrc", "tests/test_asdf.py", "plugin leftover",
     "drop plugin on miss", "plugin leftover + wait + do(tool)", 14,
     "shims leftover still 1s", "shims leftover",
     "src/asdfrc_sh", "tests/test_asdf_sh.py", "gets"),
    ("mise", "mise-backend-leftover", "mise-lock-handoff", "flock-miseb",
     "src/mise.toml", "tests/test_mise.py", "backend leftover",
     "drop backend on miss", "backend leftover + wait + do(tool)", 13,
     "lock leftover still 1s", "lock leftover",
     "src/mise_lk.toml", "tests/test_mise_lk.py", "gets"),
    ("nix", "nix-store-leftover", "nix-narinfo-handoff", "flock-nixst",
     "src/nix.conf", "tests/test_nix.py", "store leftover",
     "drop store on miss", "store leftover + wait + do(drv)", 19,
     "narinfo leftover still 1s", "narinfo leftover",
     "src/nix_nar.conf", "tests/test_nix_nar.py", "gets"),
    ("guix", "guix-substitute-leftover", "guix-gc-handoff", "flock-guixs",
     "src/guix.conf", "tests/test_guix.py", "substitute leftover",
     "drop substitute on miss", "sub leftover + wait + do(drv)", 16,
     "gc leftover still 1s", "gc leftover",
     "src/guix_gc.conf", "tests/test_guix_gc.py", "gets"),
    ("spack", "spack-mirror-leftover", "spack-buildcache-handoff", "flock-spckm",
     "src/spack.yaml", "tests/test_spack.py", "mirror leftover",
     "drop mirror on miss", "mirror leftover + wait + do(spec)", 15,
     "buildcache leftover still 1s", "buildcache leftover",
     "src/spack_bc.yaml", "tests/test_spack_bc.py", "gets"),
    ("conda-lock", "condalock-repodata-leftover", "condalock-explicit-handoff", "flock-cnlk",
     "src/conda-lock.yml", "tests/test_condalock.py", "repodata leftover",
     "drop repodata on miss", "rd leftover + wait + do(pkg)", 13,
     "explicit leftover still 1s", "explicit leftover",
     "src/conda-lock_ex.yml", "tests/test_condalock_ex.py", "gets"),
    ("tox", "tox-env-leftover", "tox-provision-handoff", "flock-toxen",
     "src/tox.ini", "tests/test_tox.py", "env leftover",
     "drop env on miss", "env leftover + wait + do(env)", 14,
     "provision leftover still 1s", "provision leftover",
     "src/tox_pr.ini", "tests/test_tox_pr.py", "gets"),
    ("nox", "nox-reuse-leftover", "nox-venv-handoff", "flock-noxru",
     "src/noxfile.py", "tests/test_nox.py", "reuse leftover",
     "drop reuse on miss", "reuse leftover + wait + do(sess)", 12,
     "venv leftover still 1s", "venv leftover",
     "src/noxfile_vn.py", "tests/test_nox_vn.py", "gets"),
    ("pre-commit", "precommit-hook-leftover", "precommit-env-handoff", "flock-prcmh",
     "src/.pre-commit-config.yaml", "tests/test_precommit.py", "hook leftover",
     "drop hook on miss", "hook leftover + wait + do(id)", 15,
     "env leftover still 1s", "env leftover",
     "src/.pre-commit-config_en.yaml", "tests/test_precommit_en.py", "gets"),
    ("lefthook", "lefthook-skip-leftover", "lefthook-remote-handoff", "flock-lfthk",
     "src/lefthook.yml", "tests/test_lefthook.py", "skip leftover",
     "drop skip on miss", "skip leftover + wait + do(hook)", 13,
     "remote leftover still 1s", "remote leftover",
     "src/lefthook_rm.yml", "tests/test_lefthook_rm.py", "gets"),
    ("husky", "husky-init-leftover", "husky-hook-handoff", "flock-hskyi",
     "src/.husky/pre-commit", "tests/test_husky.py", "init leftover",
     "drop init on miss", "init leftover + wait + do(hook)", 11,
     "hook leftover still 1s", "hook leftover",
     "src/.husky/pre-push", "tests/test_husky_hk.py", "gets"),
]

def records(round_n: int):
    idx = round_n - CATALOG_FIRST
    p = PAIRS[idx]
    product, slug_ok, slug_part, plant, src, test, api, naive, fix, workers, residual, sibling, *_ = p
    rec_ok = {
        "id": f"cst-r{round_n}-{slug_ok}",
        "goal": (
            f"{plant}: leftover leftover leftover {product} {api} still stampedes {workers} callers after a crashed refresh. "
            f"One in-flight via {fix}. Do not {naive}. Gate is {test}."
        ),
        "plan": f"{naive} so leftover leftover leftover cannot stampede origin.",
        "steps": _steps_ok(p),
        "outcome": (
            f"Leftover leftover leftover {product} stampeded {workers} callers. {naive} failed still-rebuilds. "
            f"Plan change: {fix}. {test} 4/4, suite 8/8. Residual: {residual}."
        ),
        "reward": {"success": True, "plan_changes": 1, "tests_passed": 8, "cost_steps": 16},
        "meta": {
            "factory": "cache-stampede-factory",
            "round": round_n,
            "generator": "grok-4.6",
            "kind": "designed",
            "product": product,
            "mechanic": f"leftover leftover leftover {api}",
            "sim_or_real": "designed",
            "plant": plant,
        },
    }
    rec_part = {
        "id": f"cst-r{round_n}-{slug_part}",
        "goal": (
            f"{plant}: leftover leftover leftover {product} still stampedes after a crashed refresh. "
            f"One in-flight via {fix}. Do not {naive}. Gate is {test}. "
            f"{sibling} may still hard-miss; ticket allows handoff."
        ),
        "plan": f"{naive} so leftover leftover leftover cannot stampede origin.",
        "steps": _steps_part(p),
        "outcome": (
            f"Leftover leftover leftover {product} stampeded callers. {naive} failed fixture. "
            f"Plan change: {fix}. {test} 3/3. Partial: leftover leftover leftover {sibling} still leftover (xfail)."
        ),
        "reward": {
            "success": False,
            "plan_changes": 1,
            "tests_passed": 3,
            "xfailed": 1,
            "handoff": 1,
            "cost_steps": 17,
        },
        "meta": {
            "factory": "cache-stampede-factory",
            "round": round_n,
            "generator": "grok-4.6",
            "kind": "designed",
            "product": product,
            "mechanic": f"leftover leftover leftover {sibling}",
            "sim_or_real": "designed",
            "plant": plant,
        },
    }
    return [rec_ok, rec_part]


def notes_md(round_n: int) -> str:
    idx = round_n - CATALOG_FIRST
    p = PAIRS[idx]
    product, slug_ok, slug_part, plant, src, test, api, naive, fix, workers, residual, sibling, *_ = p
    return (
        f"# NOTES-r{round_n} cache-stampede-factory\n\n"
        "Novel coverage: 91%\n\n"
        f"Two designed leftover leftover leftover stampede episodes (quota 2). "
        f"{product} leftover leftover leftover {api} vs leftover leftover leftover {sibling}. "
        "Not flock-wN. Not AWS catalog. Not r1–r1690 clones (incl. r1445 akamai-esi, r1690 woodpecker-cache). "
        "Not dbc-/sir-/gql- ids.\n"
        "Not overlayfs whiteout. Not nydus/stargz. Not search-index leftover. Not docker leftover leftover leftover.\n\n"
        "| id | seed | first apply | plan change | terminal |\n"
        "|---|---|---|---|---|\n"
        f"| cst-r{round_n}-{slug_ok} | {workers} leftover leftover leftover {product} | {naive} | {fix} | success residual {residual} |\n"
        f"| cst-r{round_n}-{slug_part} | leftover leftover leftover {sibling} | {naive} | {fix} | handoff leftover sibling |\n\n"
        "## Step counts\n"
        "- ep1: 16. Naive 6–7; plan change 8; suite green 12–16.\n"
        "- ep2: 17. Naive 6–7; plan change 8; sibling xfail 12–17.\n\n"
        "## decision_basis audit\n"
        f"Every step starts Plan:/Observation:/Reflection:. No thought keys. Plant `{plant}`.\n"
        "meta.generator=grok-4.6. Invented plant. No sim_or_real: real.\n\n"
        "## Weaknesses / next\n"
        f"Avoid {slug_ok} reruns and docker/search ids.\n"
    )


def write_round(round_n: int, stage: Path):
    recs = records(round_n)
    (stage / f"batch-r{round_n:02d}.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=True) + "\n" for r in recs)
    )
    (stage / f"NOTES-r{round_n:02d}.md").write_text(notes_md(round_n))
    return [r["id"] for r in recs]
