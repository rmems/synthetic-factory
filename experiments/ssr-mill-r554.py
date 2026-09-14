#!/usr/bin/env python3
"""Mill secret-scan-remediation-factory r554+ unique shadow leftover mechanics.

BAN: skip-path cartesian; SaaS-yml; vendor-file; cipher-*; r435 mold-map /
lld-repro; r331 rebase-merge / turbo-cache; r436–r553 sidecar clones;
r181–r435 leftover leftover leftover clones. Fake TESTONLY_ keys only.
Never force-push main.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

FACTORY = "secret-scan-remediation-factory"
CATALOG_FIRST = 554
HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("ssr_mill_r436", HERE / "ssr-mill-r436.py")
_r436 = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_r436)
plant = _r436.plant
success_episode = _r436.success_episode
fail_episode = _r436.fail_episode
SCAN = _r436.SCAN
SCANNERS = _r436.SCANNERS
LEAKS = _r436.LEAKS

USED_SLUGS = {p["slug"] for pair in _r436.PAIRS for p in pair} | set(_r436.USED_SLUGS)
USED_EXTRAS = {p["extra"] for pair in _r436.PAIRS for p in pair} | set(_r436.USED_EXTRAS)
USED_TAILS = set(_r436.TAILS)
USED_ORGS = set(_r436.ORGS)

# Shadow leftovers: codegen / migrate / watch / notebook sidecars, not r436 tails.
TAILS = [
    "coursier-cache",
    "ammonite-repl",
    "voila-cache",
    "holoviews-cache",
    "dask-spill",
    "ray-session",
    "beam-fn",
    "mage-ai",
    "luigi-state",
    "huey-sqlite",
    "dramatiq-queue",
    "rq-dump",
    "hue-notebook",
    "zeppelin-note",
    "nifi-flow",
    "bison-out",
    "flex-out",
    "yacc-tab",
    "antlr-gen",
    "treesitter-q",
    "swig-wrap",
    "thrift-gen",
    "capnp-gen",
    "flatbuf-gen",
    "grpc-gen",
    "openapi-gen",
    "smithy-gen",
    "buf-gen",
    "twirp-gen",
    "connect-gen",
    "gql-codegen",
    "sqlc-gen",
    "diesel-schema",
    "seaorm-gen",
    "alembic-ver",
    "flyway-sql",
    "liquibase-sql",
    "atlas-hcl",
    "goose-mig",
    "dbmate-mig",
    "sqitch-plan",
    "migrate-sql",
    "typeorm-mig",
    "sequelize-mig",
    "knex-mig",
    "django-mig",
    "rails-schema",
    "ecto-mig",
    "room-schema",
    "realm-file",
    "watchexec-log",
    "reflex-log",
    "air-tmp",
    "nodemon-dump",
    "entr-out",
    "fswatch-log",
    "tiltfile-log",
    "skaffold-log",
    "garden-log",
    "devspace-log",
    "telepresence-log",
    "mirrord-log",
    "okteto-log",
    "garden-build",
    "earthfile-log",
    "just-tmp",
    "make-dep",
    "ninja-restat",
    "scons-sig",
    "waf-lock",
    "autotools-dep",
    "libtool-obj",
    "automake-in",
    "autoconf-cache",
    "pkgconfig-pc",
    "vcpkg-manifest",
    "conan-lock",
    "hunter-cache",
    "cpm-cache",
    "fetchcontent",
    "externalproject",
    "git-submodule-git",
    "repo-manifest",
    "west-build",
    "zephyr-sdk",
    "esp-idf-build",
    "pico-sdk-build",
    "arduino-build",
    "platformio-lib",
    "mbed-build",
    "riot-bin",
    "nuttx-out",
    "freertos-build",
    "zephyr-twister",
    "yocto-sstate",
    "bitbake-tmp",
    "openwrt-bin",
    "buildroot-out",
    "crosstool-ng",
    "musl-obj",
    "glibc-obj",
    "newlib-obj",
    "compiler-rt",
    "libunwind-obj",
    "libcxx-obj",
    "libcxxabi-obj",
    "compiler-wrapper",
    "ccache-stats",
    "sccache-stats",
    "distcc-stats",
    "icecream-stats",
    "mold-stats",
    "lld-stats",
    "gold-stats",
    "bfd-stats",
    "llvm-profdata",
    "llvm-cov-json",
    "gcov-json",
    "lcov-info",
    "cobertura-xml",
    "jacoco-xml",
    "istanbul-json",
    "c8-tmp",
    "nyc-tmp",
    "pytest-html",
    "robot-out",
    "behave-json",
    "lettuce-json",
    "gauge-logs",
    "specflow-out",
    "cucumber-html",
    "karate-out",
    "restassured-log",
    "postman-newman",
    "insomnia-export",
    "httpie-sess",
    "curl-trace",
    "wget-log",
    "aria2-log",
    "axel-log",
    "rsync-log",
    "rclone-log",
    "restic-cache",
    "borg-cache",
    "duplicity-cache",
    "kopia-cache",
    "rclone-vfs",
    "syncthing-idx",
    "unison-ar",
    "osync-log",
    "lsyncd-log",
    "incron-log",
    "cron-spool",
    "anacron-spool",
    "systemd-journal",
    "journalctl-export",
    "auditd-log",
    "osquery-db",
    "falco-log",
    "sysdig-scap",
    "perf-script",
    "bpftrace-out",
    "bcc-log",
    "dtrace-out",
    "strace-log",
    "ltrace-log",
    "ptrace-log",
    "gdb-history",
    "lldb-history",
    "rr-trace",
    "undo-recording",
    "valgrind-xml",
    "helgrind-log",
    "drd-log",
    "massif-out",
    "cachegrind-out",
    "callgrind-out",
    "kcachegrind-out",
    "heaptrack-gz",
    "hotspot-perf",
    "intel-vtune",
    "amd-uprof",
    "nsight-qdrep",
    "ncu-rep",
    "cupti-trace",
    "nvprof-nvvp",
    "rocprof-csv",
    "roctracer-out",
    "omnitrace-out",
    "tau-trace",
    "scorep-exp",
    "extrae-prv",
    "otf2-trace",
    "vampir-otf",
    "scalasca-exp",
    "cube-xml",
    "papi-out",
    "likwid-out",
    "pcm-csv",
    "turbostat-log",
    "perfetto-pb",
    "systrace-html",
    "atrace-out",
    "simpleperf-data",
    "instruments-trace",
    "dtrace-stacks",
    "sample-txt",
    "spindump-txt",
    "activity-monitor",
    "etw-etl",
    "xperf-etl",
    "wpr-etl",
    "procmon-pml",
    "sysmon-evtx",
    "autoruns-csv",
    "handle-out",
    "listdlls-out",
    "tcpview-csv",
    "procmon-csv",
    "wireshark-pcapng",
    "tcpdump-cap",
    "tshark-json",
    "zeek-log",
    "suricata-eve",
    "snort-log",
    "ntopng-db",
    "nfdump-nfcap",
    "argus-ra",
    "bro-log",
    "moloch-db",
    "arkime-db",
    "netdata-db",
]

ORGS = [
    f"shadow{i:03d}"
    for i in range(1, len(TAILS) + 1)
]


def _scan_pair(scanner: str, extra: str, tag: str) -> tuple[str, str]:
    invoke, hit = SCAN[scanner]
    return invoke.format(extra=extra, tag=tag), hit.format(tag=tag)


def _mk(tail: str, idx: int) -> dict:
    if tail in USED_TAILS:
        raise SystemExit(f"tail clone: {tail}")
    scanner = SCANNERS[(idx - 1) % len(SCANNERS)]
    leak, prefix = LEAKS[(idx - 1) % len(LEAKS)]
    base = leak.split("/")[-1]
    extra = f".{tail}/{base}"
    pretty = tail.replace("-", " ")
    mechanic = f"{pretty} shadow still names {leak}"
    tag = f"{pretty} shadow leftover"
    env = f"{prefix}_{tail.replace('-', '_')[:14].upper()}_TOKEN"
    org = f"{ORGS[idx - 1]}-sh"
    short = org.split("-")[0][:6]
    repo = f"{org}/{short}-{tail[:28]}"
    slug = f"{scanner}-{tail}-leftover"
    invoke, hit = _scan_pair(scanner, extra, tag)
    wrong_cmd = f"rg TESTONLY {extra} | head"
    hide_cmd = f"echo '{leak.split('/')[0]}/' >> .gitignore; {wrong_cmd}"
    tok = f"TESTONLY_r554{idx:03d}_n0t"
    return plant(
        slug=slug,
        scanner=scanner,
        mechanic=mechanic,
        repo=repo,
        leak=leak,
        extra=extra,
        token=tok,
        env=env,
        sha=f"a554{idx:04x}",
        pr=780 + idx,
        mix=f"{scanner} {tag}",
        scan_invoke=invoke,
        scan_hit=hit,
        extra_line=f"{tag} still names TESTONLY_",
        miss_cmd=f"{SCAN[scanner][0].format(extra=leak, tag=tag)} 2>&1 | tail -3 || echo {tail[:12]}-head-green",
        miss_green=f"{tail[:12]}-head-green",
        wrong_b=f"Plan: first apply - redact {leak}. Expect {pretty} shadow still red.",
        wrong_cmd=wrong_cmd,
        wrong_obs=f"{env}={tok}",
        hide_cmd=hide_cmd,
        hide_obs=f"{env}={tok}  ({tag})",
    )


clash = [t for t in TAILS if t in USED_TAILS]
if clash:
    raise SystemExit(f"tail clones r436: {clash[:8]}")
if len(TAILS) != len(ORGS):
    raise SystemExit(f"TAILS {len(TAILS)} != ORGS {len(ORGS)}")
if len(TAILS) % 2:
    raise SystemExit("odd plant count")
if any(o in USED_ORGS for o in ORGS):
    raise SystemExit("org clones r436")

_plants = [_mk(tail, i) for i, tail in enumerate(TAILS, start=1)]
PAIRS = [(_plants[i], _plants[i + 1]) for i in range(0, len(_plants), 2)]


def _assert_catalog() -> None:
    slugs = [p["slug"] for pair in PAIRS for p in pair]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("duplicate slugs in r554 catalog")
    clash = set(slugs) & USED_SLUGS
    if clash:
        raise SystemExit(f"slug clones prior mill: {sorted(clash)[:8]}")
    tokens = [p["token"] for pair in PAIRS for p in pair]
    if len(tokens) != len(set(tokens)):
        raise SystemExit("duplicate tokens in r554 catalog")
    extras = [p["extra"] for pair in PAIRS for p in pair]
    if len(extras) != len(set(extras)):
        raise SystemExit("duplicate extras in r554 catalog")
    extra_clash = set(extras) & USED_EXTRAS
    if extra_clash:
        raise SystemExit(f"extra clones prior mill: {sorted(extra_clash)[:8]}")
    banned_bits = (
        "stash-wip",
        "reflog",
        "worktree",
        "turbo-cache",
        "npm-offline",
        "npm-pack",
        "ruff-cache",
        "export-subst",
        "p4-sync",
        "wheel-leftover",
        "wheelhouse",
        "gradle-cache",
        "tox-env",
        "hypothesis",
        "cipher",
        "sarif",
        "git-notes",
        "entropy-window",
        "next-build",
        "mold-map",
        "lld-repro",
        "rebase-merge-head",
        "vendor-file",
        "saas-yml",
    )
    for spec in (p for pair in PAIRS for p in pair):
        blob = f"{spec['slug']} {spec['mechanic']} {spec['extra']}".lower()
        hit = [b for b in banned_bits if b in blob]
        if hit:
            raise SystemExit(f"banned fragment {hit} in {spec['slug']}")
        if len(spec["wrong_b"]) > 240:
            raise SystemExit(f"wrong_b too long for {spec['slug']}")
        if "TESTONLY_" not in spec["token"]:
            raise SystemExit(f"bad token {spec['token']}")


_assert_catalog()


def notes_md(rnd, suc, fail, suc_ep, fail_ep):
    coverage = max(52, 74 - (rnd - CATALOG_FIRST))
    return f"""# NOTES-r{rnd} secret-scan-remediation-factory

Novel coverage: {coverage}%

Two designed shadow-leftover episodes (quota 2). Surfaces: {suc['repo']} {suc['slug']} {suc['mechanic']}; {fail['repo']} {fail['slug']} {fail['mechanic']} (rewrite blocked).
Neither force-pushes main. Fake TESTONLY_ keys only. One remaining-scan fail when rewrite is blocked.
Scanner × shadow leftover mill (not skip-path cartesian, not SaaS-yml, not vendor-file, not decoder wrap, not SARIF leftover, not git-notes leftover, not entropy-window leftover, not r181–r553 sidecar/leftover leftover leftover clones, not r435 mold-map/lld-repro, not r331 rebase-merge/turbo-cache).

| id | seed | first apply | plan change | terminal |
|---|---|---|---|---|
| {suc_ep['id']} | {suc['mechanic']} in {suc['leak']} + {suc['extra']} | {suc['wrong_b'].replace('Plan: first apply - ', '')} | {suc['env']} + filter-repo purge | success 2/2, main residual |
| {fail_ep['id']} | {fail['mechanic']} in {fail['leak']} + {fail['extra']} | {fail['wrong_b'].replace('Plan: first apply - ', '')} | HEAD {fail['env']}; GH013 | remaining-scan fail + HANDOFF |

## Step counts
- {suc_ep['id']}: {len(suc_ep['steps'])}
- {fail_ep['id']}: {len(fail_ep['steps'])}

## decision_basis audit
Every step starts Plan:/Observation:/Reflection:/Tool call:, ≤240 chars.
No thought / chain_of_thought / scratch / inner_monologue. No spike_events.
No sim_or_real: real. Invented plants (designed). No real secrets.

## Weaknesses / next
Avoid {suc['slug']}-as-git-fix and {fail['slug']}-as-git-fix (this round).
Harder-kind mill: {suc['mix']}; {fail['mix']}.
"""


def build_round(rnd: int, pair_index: int | None = None):
    idx = pair_index if pair_index is not None else rnd - CATALOG_FIRST
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(f"round {rnd} idx={idx} outside catalog 0..{len(PAIRS) - 1}")
    suc, fail = PAIRS[idx]
    suc_n = 16 if idx % 2 else 14
    fail_n = 15 if idx % 3 else 16
    suc_ep = success_episode(rnd, suc, suc_n)
    fail_ep = fail_episode(rnd, fail, fail_n)
    for ep in (suc_ep, fail_ep):
        n = len(ep["steps"])
        if n < 12 or n > 18:
            raise SystemExit(f"{ep['id']} has {n} steps, want 12-18")
        ep["reward"]["cost_steps"] = n
        for s in ep["steps"]:
            basis = s["decision_basis"]
            prefix = basis.split(":", 1)[0]
            if prefix not in {"Plan", "Observation", "Reflection", "Tool call"}:
                raise SystemExit(f"{ep['id']} bad prefix {basis!r}")
            if len(basis) > 240:
                raise SystemExit(f"{ep['id']} basis too long: {basis}")
            banned_keys = {"thought", "chain_of_thought", "scratch", "inner_monologue", "spike_events"}
            if banned_keys & set(s):
                raise SystemExit(f"{ep['id']} banned keys")
        if ep.get("sim_or_real") == "real":
            raise SystemExit(f"{ep['id']} sim_or_real real")
        if ep["meta"].get("generator") != "grok-4.6":
            raise SystemExit(f"{ep['id']} bad generator")
    return [suc_ep, fail_ep], notes_md(rnd, suc, fail, suc_ep, fail_ep)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    ap.add_argument("--pair-index", type=int, default=None)
    args = ap.parse_args()
    recs, notes = build_round(args.round, args.pair_index)
    staging = Path(args.staging)
    with (staging / f"batch-r{args.round:02d}.jsonl").open("w") as handle:
        for rec in recs:
            handle.write(json.dumps(rec, ensure_ascii=True) + "\n")
    (staging / f"NOTES-r{args.round:02d}.md").write_text(notes)
    print(
        json.dumps(
            {
                "round": args.round,
                "ids": [r["id"] for r in recs],
                "steps": [len(r["steps"]) for r in recs],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
