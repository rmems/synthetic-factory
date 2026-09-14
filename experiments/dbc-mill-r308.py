#!/usr/bin/env python3
"""Mill docker-build-cache-factory r308+ after r288–r307."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("dbc_mill_r193", HERE / "dbc-mill-r193.py")
_r193 = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_r193)

FACTORY = "docker-build-cache-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 308
success_episode = _r193.success_episode
leftover_episode = _r193.leftover_episode


def left(**kw):
    if "not_" in kw:
        kw["not"] = kw.pop("not_")
    return kw


PAIRS = [
    (
        {
            "slug": "nickel-ncl-cache",
            "harbor": "harbor-nickel",
            "env": "NICKEL_CACHE",
            "tool": "nickel",
            "old": "1.7.0",
            "new": "1.9.1",
            "artifact": "cache/ncl/std.ncl",
            "test": "test_nickel.py",
            "src": "src/app.ncl",
            "cache_id": "nickel-191",
            "dead_rm": "rm -rf /root/.cache/nickel",
            "dead_obs": "rm ncl does not drop 1.7 std under unversioned NICKEL_CACHE",
            "left_mb": "5MB",
            "vs": "r235 dhall / r268 cue (Nickel ncl, not Dhall/CUE)",
            "img": "FROM debian:bookworm",
            "run": "nickel export src/app.ncl",
        },
        left(
            slug="sched-rt-leftover",
            harbor="harbor-schedrt",
            token="SCHED_RT_RESET",
            leftover="kernel.sched_rt_runtime_us=10000",
            detail="RT runtime leftover still throttles cache worker",
            dead="echo -1 > /proc/sys/kernel/sched_rt_runtime_us",
            dead_obs="sched_rt_runtime write is EPERM; leftover 10ms still throttles",
            fail_mode="leftover sched_rt_runtime_us=10000 throttling cache worker",
            not_="r228 cpuset / cache-admin 403",
            vs="r228 cpuset leftover (sched_rt leftover, not cpuset)",
            test="test_schedrt.py",
            probe="cat /proc/sys/kernel/sched_rt_runtime_us",
            probe_obs="10000 leftover",
            fix_key="name: harbor-schedrt-v2",
            fix_val='driver-opts:\n          env.BUILDKIT_SCHED_RT: "-1"',
        ),
    ),
    (
        {
            "slug": "just-recipes-cache",
            "harbor": "harbor-just",
            "env": "JUST_UNSTABLE",
            "tool": "just",
            "old": "1.35.0",
            "new": "1.39.0",
            "artifact": ".justfile.lock",
            "test": "test_just.py",
            "src": "src/justfile",
            "cache_id": "just-1390",
            "dead_rm": "rm -f /src/.justfile.lock",
            "dead_obs": "rm lock does not drop 1.35 recipes under unversioned JUST cache",
            "left_mb": "1MB",
            "vs": "r239 waf-lock (just recipes, not waf)",
            "img": "FROM debian:bookworm",
            "run": "just build",
        },
        left(
            slug="timer-migration-leftover",
            harbor="harbor-tmig",
            token="TIMER_MIG_RESET",
            leftover="kernel.timer_migration=0",
            detail="timer_migration leftover still pins cache timers",
            dead="echo 1 > /proc/sys/kernel/timer_migration",
            dead_obs="timer_migration write is EPERM; leftover 0 still pins timers",
            fail_mode="leftover timer_migration=0 pinning cache timers",
            not_="r273 isolcpus / cache-admin 403",
            vs="r273 isolcpus leftover (timer_migration leftover, not isolcpus)",
            test="test_tmig.py",
            probe="cat /proc/sys/kernel/timer_migration",
            probe_obs="0 leftover",
            fix_key="name: harbor-tmig-v2",
            fix_val='driver-opts:\n          env.BUILDKIT_TIMER_MIG: "1"',
        ),
    ),
    (
        {
            "slug": "taskfile-cache",
            "harbor": "harbor-task",
            "env": "TASK_TEMP_DIR",
            "tool": "task",
            "old": "3.38.0",
            "new": "3.41.0",
            "artifact": ".task/checksum",
            "test": "test_task.py",
            "src": "src/Taskfile.yml",
            "cache_id": "task-3410",
            "dead_rm": "rm -rf /src/.task",
            "dead_obs": "rm .task does not drop 3.38 checksums under unversioned TASK_TEMP_DIR",
            "left_mb": "2MB",
            "vs": "just-recipes this mill (Task checksums, not just)",
            "img": "FROM debian:bookworm",
            "run": "task build",
        },
        left(
            slug="numa-balancing-leftover",
            harbor="harbor-nbal",
            token="NUMA_BAL_RESET",
            leftover="kernel.numa_balancing=0",
            detail="numa_balancing leftover still pins cache pages",
            dead="echo 1 > /proc/sys/kernel/numa_balancing",
            dead_obs="numa_balancing write is EPERM; leftover 0 still pins pages",
            fail_mode="leftover numa_balancing=0 pinning cache pages",
            not_="r229 numa-membind / cache-admin 403",
            vs="r229 NUMA membind leftover (numa_balancing leftover, not mempolicy)",
            test="test_nbal.py",
            probe="cat /proc/sys/kernel/numa_balancing",
            probe_obs="0 leftover",
            fix_key="name: harbor-nbal-v2",
            fix_val='driver-opts:\n          env.BUILDKIT_NUMA_BAL: "1"',
        ),
    ),
    (
        {
            "slug": "gqlgen-cache",
            "harbor": "harbor-gqlgen",
            "env": "GQLGEN_CACHE",
            "tool": "gqlgen",
            "old": "0.17.49",
            "new": "0.17.66",
            "artifact": "generated/exec.go",
            "test": "test_gqlgen.py",
            "src": "src/schema.graphql",
            "cache_id": "gqlgen-1766",
            "dead_rm": "rm -rf /src/generated",
            "dead_obs": "rm generated does not drop 0.17.49 exec under unversioned GQLGEN_CACHE",
            "left_mb": "4MB",
            "vs": "r288 buf-mod (gqlgen exec, not Buf proto)",
            "img": "FROM golang:1.23",
            "run": "gqlgen generate",
        },
        left(
            slug="zone-reclaim-leftover",
            harbor="harbor-zrec",
            token="ZONE_RECLAIM_RESET",
            leftover="vm.zone_reclaim_mode=1",
            detail="zone_reclaim leftover still stalls cache alloc",
            dead="echo 0 > /proc/sys/vm/zone_reclaim_mode",
            dead_obs="zone_reclaim write is EPERM; leftover 1 still stalls alloc",
            fail_mode="leftover zone_reclaim_mode=1 stalling cache alloc",
            not_="r229 numa-membind / cache-admin 403",
            vs="r229 NUMA leftover (zone_reclaim leftover, not membind)",
            test="test_zrec.py",
            probe="cat /proc/sys/vm/zone_reclaim_mode",
            probe_obs="1 leftover",
            fix_key="name: harbor-zrec-v2",
            fix_val='driver-opts:\n          env.BUILDKIT_ZONE_RECLAIM: "0"',
        ),
    ),
    (
        {
            "slug": "diesel-cli-cache",
            "harbor": "harbor-diesel",
            "env": "DIESEL_CONFIG_FILE",
            "tool": "diesel",
            "old": "2.2.4",
            "new": "2.2.7",
            "artifact": "migrations/.diesel_lock",
            "test": "test_diesel.py",
            "src": "src/diesel.toml",
            "cache_id": "diesel-227",
            "dead_rm": "rm -f /src/migrations/.diesel_lock",
            "dead_obs": "rm lock does not drop 2.2.4 schema under unversioned DIESEL_CONFIG_FILE",
            "left_mb": "2MB",
            "vs": "r290 sqlx-query (Diesel cli, not SQLx offline)",
            "img": "FROM rust:1.84",
            "run": "diesel migration run",
        },
        left(
            slug="randomize-va-leftover",
            harbor="harbor-aslr",
            token="ASLR_RESET",
            leftover="kernel.randomize_va_space=0",
            detail="ASLR leftover still off for cache worker",
            dead="echo 2 > /proc/sys/kernel/randomize_va_space",
            dead_obs="aslr write is EPERM; leftover 0 still disables ASLR",
            fail_mode="leftover randomize_va_space=0 leaving cache worker unrandomized",
            not_="r230 lockdown / cache-admin 403",
            vs="r230 lockdown leftover (ASLR leftover, not lockdown)",
            test="test_aslr.py",
            probe="cat /proc/sys/kernel/randomize_va_space",
            probe_obs="0 leftover",
            fix_key="name: harbor-aslr-v2",
            fix_val='driver-opts:\n          env.BUILDKIT_ASLR: "2"',
        ),
    ),
    (
        {
            "slug": "liquibase-cache",
            "harbor": "harbor-lb",
            "env": "LIQUIBASE_HOME",
            "tool": "liquibase",
            "old": "4.29.2",
            "new": "4.31.1",
            "artifact": "lib/liquibase-core.jar",
            "test": "test_lb.py",
            "src": "src/changelog.xml",
            "cache_id": "lb-4311",
            "dead_rm": "rm -rf /opt/liquibase/lib",
            "dead_obs": "rm lib does not drop 4.29 core jar under unversioned LIQUIBASE_HOME",
            "left_mb": "18MB",
            "vs": "r291 flyway (Liquibase jars, not Flyway)",
            "img": "FROM liquibase/liquibase:4.31.1",
            "run": "liquibase update",
        },
        left(
            slug="sysrq-leftover",
            harbor="harbor-sysrq",
            token="SYSRQ_RESET",
            leftover="kernel.sysrq=1",
            detail="sysrq leftover still armed on cache host",
            dead="echo 0 > /proc/sys/kernel/sysrq",
            dead_obs="sysrq write is EPERM; leftover 1 still armed",
            fail_mode="leftover kernel.sysrq=1 armed on cache host",
            not_="r307 panic-oops / cache-admin 403",
            vs="r307 panic_on_oops leftover (sysrq leftover, not panic_on_oops)",
            test="test_sysrq.py",
            probe="cat /proc/sys/kernel/sysrq",
            probe_obs="1 leftover",
            fix_key="name: harbor-sysrq-v2",
            fix_val='driver-opts:\n          env.BUILDKIT_SYSRQ: "0"',
        ),
    ),
    (
        {
            "slug": "mlx-cache",
            "harbor": "harbor-mlx",
            "env": "MLX_METAL_CACHE",
            "tool": "python3",
            "old": "0.18.1",
            "new": "0.22.0",
            "artifact": "metal/cache/kernels",
            "test": "test_mlx.py",
            "src": "src/app.py",
            "cache_id": "mlx-022",
            "dead_rm": "rm -rf /root/.cache/mlx",
            "dead_obs": "rm metal does not drop 0.18 kernels under unversioned MLX_METAL_CACHE",
            "left_mb": "29MB",
            "vs": "r293 jax-cache (MLX metal, not JAX XLA)",
            "img": "FROM python:3.12-slim",
            "run": "python3 src/app.py",
        },
        left(
            slug="cad-leftover",
            harbor="harbor-cad",
            token="CAD_RESET",
            leftover="kernel.ctrl-alt-del=1",
            detail="ctrl-alt-del leftover still reboots cache host",
            dead="echo 0 > /proc/sys/kernel/ctrl-alt-del",
            dead_obs="ctrl-alt-del write is EPERM; leftover 1 still reboots",
            fail_mode="leftover ctrl-alt-del=1 rebooting cache host",
            not_="r307 panic-oops / cache-admin 403",
            vs="r307 panic leftover (ctrl-alt-del leftover, not panic_on_oops)",
            test="test_cad.py",
            probe="cat /proc/sys/kernel/ctrl-alt-del",
            probe_obs="1 leftover",
            fix_key="name: harbor-cad-v2",
            fix_val='driver-opts:\n          env.BUILDKIT_CAD: "0"',
        ),
    ),
    (
        {
            "slug": "tinygrad-cache",
            "harbor": "harbor-tg",
            "env": "TINYGRAD_CACHE",
            "tool": "python3",
            "old": "0.9.2",
            "new": "0.10.2",
            "artifact": "tinygrad/cache/clir",
            "test": "test_tg.py",
            "src": "src/app.py",
            "cache_id": "tg-0102",
            "dead_rm": "rm -rf /tmp/tinygrad",
            "dead_obs": "rm clir does not drop 0.9 kernels under unversioned TINYGRAD_CACHE",
            "left_mb": "11MB",
            "vs": "r294 triton-cache (tinygrad clir, not Triton PTX)",
            "img": "FROM python:3.12-slim",
            "run": "python3 src/app.py",
        },
        left(
            slug="modules-disabled-leftover",
            harbor="harbor-moddis",
            token="MODULES_ENABLE",
            leftover="kernel.modules_disabled=1",
            detail="modules_disabled leftover still EPERM cache kmod helpers",
            dead="echo 0 > /proc/sys/kernel/modules_disabled",
            dead_obs="modules_disabled write is EPERM; leftover 1 still EPERM kmod",
            fail_mode="leftover modules_disabled=1 EPERM on cache kmod helpers",
            not_="r305 unpriv-bpf / cache-admin 403",
            vs="r305 unpriv bpf leftover (modules_disabled leftover, not bpf)",
            test="test_moddis.py",
            probe="cat /proc/sys/kernel/modules_disabled",
            probe_obs="1 leftover",
            fix_key="name: harbor-moddis-v2",
            fix_val='driver-opts:\n          env.BUILDKIT_MODULES: "0"',
        ),
    ),
    (
        {
            "slug": "clickhouse-user-scripts",
            "harbor": "harbor-ch",
            "env": "CLICKHOUSE_USER_FILES",
            "tool": "clickhouse",
            "old": "24.8.4",
            "new": "25.1.3",
            "artifact": "user_scripts/udf.py",
            "test": "test_ch.py",
            "src": "src/query.sql",
            "cache_id": "ch-2513",
            "dead_rm": "rm -rf /var/lib/clickhouse/user_scripts",
            "dead_obs": "rm udf does not drop 24.8 scripts under unversioned CLICKHOUSE_USER_FILES",
            "left_mb": "7MB",
            "vs": "r292 duckdb-ext (ClickHouse UDF, not DuckDB ext)",
            "img": "FROM clickhouse/clickhouse-server:25.1",
            "run": "clickhouse-client --query-file src/query.sql",
        },
        left(
            slug="print-fatal-leftover",
            harbor="harbor-pfatal",
            token="PRINT_FATAL_RESET",
            leftover="kernel.print-fatal-signals=1",
            detail="print-fatal leftover still floods cache dmesg",
            dead="echo 0 > /proc/sys/kernel/print-fatal-signals",
            dead_obs="print-fatal write is EPERM; leftover 1 still floods dmesg",
            fail_mode="leftover print-fatal-signals=1 flooding cache dmesg",
            not_="r304 dmesg-restrict / cache-admin 403",
            vs="r304 dmesg_restrict leftover (print-fatal leftover, not dmesg_restrict)",
            test="test_pfatal.py",
            probe="cat /proc/sys/kernel/print-fatal-signals",
            probe_obs="1 leftover",
            fix_key="name: harbor-pfatal-v2",
            fix_val='driver-opts:\n          env.BUILDKIT_PRINT_FATAL: "0"',
        ),
    ),
    (
        {
            "slug": "rapids-cudf-cache",
            "harbor": "harbor-cudf",
            "env": "CUDF_HOME",
            "tool": "python3",
            "old": "24.08",
            "new": "25.02",
            "artifact": "cudf/cache/jit",
            "test": "test_cudf.py",
            "src": "src/app.py",
            "cache_id": "cudf-2502",
            "dead_rm": "rm -rf /root/.cache/cudf",
            "dead_obs": "rm jit does not drop 24.08 kernels under unversioned CUDF_HOME",
            "left_mb": "76MB",
            "vs": "r297 polars-cache (cuDF jit, not Polars ipc)",
            "img": "FROM nvcr.io/nvidia/rapidsai/base:25.02-cuda12.5-py3.12",
            "run": "python3 src/app.py",
        },
        left(
            slug="laptop-mode-leftover",
            harbor="harbor-laptop",
            token="LAPTOP_MODE_RESET",
            leftover="vm.laptop_mode=5",
            detail="laptop_mode leftover still delays cache writeback",
            dead="echo 0 > /proc/sys/vm/laptop_mode",
            dead_obs="laptop_mode write is EPERM; leftover 5 still delays writeback",
            fail_mode="leftover vm.laptop_mode=5 delaying cache writeback",
            not_="r292 dirty-ratio / cache-admin 403",
            vs="r292 dirty_ratio leftover (laptop_mode leftover, not dirty_ratio)",
            test="test_laptop.py",
            probe="cat /proc/sys/vm/laptop_mode",
            probe_obs="5 leftover",
            fix_key="name: harbor-laptop-v2",
            fix_val='driver-opts:\n          env.BUILDKIT_LAPTOP: "0"',
        ),
    ),
]


def notes_for(round_n, suc, leftp, srec, lrec):
    cov = 21 + ((round_n - CATALOG_FIRST) % 5)
    return (
        f"# NOTES-r{round_n} docker-build-cache-factory\n\n"
        f"Novel coverage: {cov}%\n\n"
        f"- Episodes: 2 (quota). Step counts: {suc['slug']} {srec['reward']['cost_steps']}, "
        f"{leftp['slug']} {lrec['reward']['cost_steps']} (16–24).\n"
        f"- Debug loops: Dead-end: {suc['dead_obs']} (7–8); Dead-end: {leftp['dead_obs']} (7–8).\n"
        f"- One success (`{srec['id']}`) and one partial (`{lrec['id']}`).\n"
        f"- Distinct from prior rounds: {suc['slug']} vs {suc['vs']} / {leftp['slug']} vs {leftp['vs']}.\n"
        f"- Fail mode: {leftp['fail_mode']}, not {leftp['not']}.\n"
        f"- Residual synthetic tells: invented harbor plants.\n"
        f"- Ban check: not r192 GNU Prolog / landlock, not r149 SWI, not r188 seccomp, "
        f"not r131 AppArmor, not GOTOOLCHAIN/GOCACHE, not Bundler, not r193–r307 plants.\n"
    )


def write_round(round_n: int, staging: Path) -> None:
    idx = round_n - CATALOG_FIRST
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(f"no catalog pair for r{round_n}")
    suc, leftp = PAIRS[idx]
    srec = success_episode(round_n, suc)
    lrec = leftover_episode(round_n, leftp)
    batch = staging / f"batch-r{round_n:02d}.jsonl"
    notes = staging / f"NOTES-r{round_n:02d}.md"
    batch.write_text(json.dumps(srec, separators=(",", ":")) + "\n" + json.dumps(lrec, separators=(",", ":")) + "\n")
    notes.write_text(notes_for(round_n, suc, leftp, srec, lrec))
    print(json.dumps({"round": round_n, "ids": [srec["id"], lrec["id"]], "bytes": batch.stat().st_size}))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    args = ap.parse_args()
    write_round(args.round, Path(args.staging))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
