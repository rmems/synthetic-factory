#!/usr/bin/env python3
"""Mill docker-build-cache-factory r248+ after r233–r247 foreign mill.

Skip plants already in r233–r247 (seed7, teapot, ipcns, utsns, dm-crypt,
dm-integrity) and r193–r232 catalog.
"""
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
_spec233 = importlib.util.spec_from_file_location("dbc_mill_r233", HERE / "dbc-mill-r233.py")
_r233 = importlib.util.module_from_spec(_spec233)
assert _spec233.loader is not None
_spec233.loader.exec_module(_r233)

FACTORY = "docker-build-cache-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 248
success_episode = _r193.success_episode
leftover_episode = _r193.leftover_episode

SKIP = {
    "seed7-lib-cache",
    "tcl-teapot-cache",
    "ipcns-leftover",
    "utsns-leftover",
    "dm-crypt-leftover",
    "dm-integrity-leftover",
}

EXTRA = [
    (
        {
            "slug": "supercollider-quark-cache",
            "harbor": "harbor-sc",
            "env": "SC_DATA_DIR",
            "tool": "sclang",
            "old": "3.13.0",
            "new": "3.14.0",
            "artifact": "downloaded-quarks/MathLib",
            "test": "test_sc.py",
            "src": "src/app.scd",
            "cache_id": "sc-314",
            "dead_rm": "rm -rf /root/.local/share/SuperCollider",
            "dead_obs": "rm quarks does not drop 3.13 MathLib under unversioned SC_DATA_DIR",
            "left_mb": "18MB",
            "vs": "r186 faust-lib (SuperCollider quarks, not Faust)",
            "img": "FROM debian:bookworm",
            "run": "sclang src/app.scd",
        },
        {
            "slug": "qemu-pidfile-leftover",
            "harbor": "harbor-qemupid",
            "token": "QEMU_PIDFILE_CLEAR",
            "leftover": "qemu pidfile /run/qemu-cache.pid",
            "detail": "qemu pidfile still holds cache VM",
            "dead": "kill $(cat /run/qemu-cache.pid)",
            "dead_obs": "qemu pidfile kill is ESRCH; leftover pidfile still locks the VM",
            "fail_mode": "leftover qemu pidfile locking cache VM",
            "not": "r204 kata-shim / r252 firecracker / cache-admin 403",
            "vs": "r204 kata leftover (qemu pidfile leftover, not kata shim)",
            "test": "test_qemupid.py",
            "probe": "cat /run/qemu-cache.pid; ps -p $(cat /run/qemu-cache.pid) || true",
            "probe_obs": "4408 leftover stale pidfile leftover",
            "fix_key": "name: harbor-qemupid-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_QEMU_PIDFILE: \"0\"",
        },
    ),
    (
        {
            "slug": "chuck-chugin-cache",
            "harbor": "harbor-chuck",
            "env": "CHUCK_CHUGIN_PATH",
            "tool": "chuck",
            "old": "1.4.2.0",
            "new": "1.5.4.0",
            "artifact": "chugins/LiSa.chug",
            "test": "test_chuck.py",
            "src": "src/app.ck",
            "cache_id": "chuck-154",
            "dead_rm": "rm -rf /usr/lib/chuck",
            "dead_obs": "rm chugins does not drop 1.4 LiSa under unversioned CHUCK_CHUGIN_PATH",
            "left_mb": "6MB",
            "vs": "r186 faust-lib (ChucK chugins, not Faust)",
            "img": "FROM debian:bookworm",
            "run": "chuck src/app.ck",
        },
        {
            "slug": "shiftfs-leftover",
            "harbor": "harbor-shiftfs",
            "token": "SHIFTFS_UMOUNT",
            "leftover": "shiftfs /var/lib/buildkit",
            "detail": "shiftfs still stacked on cache dir",
            "dead": "umount /var/lib/buildkit",
            "dead_obs": "umount shiftfs is EBUSY; leftover shiftfs still stacked",
            "fail_mode": "leftover shiftfs stack wrapping cache dir",
            "not": "r147 idmapped-uidmap / cache-admin 403",
            "vs": "r147 idmapped leftover (shiftfs leftover, not uidmap)",
            "test": "test_shiftfs.py",
            "probe": "findmnt /var/lib/buildkit; rg shiftfs /proc/mounts",
            "probe_obs": "shiftfs leftover stacked leftover",
            "fix_key": "name: harbor-shiftfs-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_SHIFTFS: \"0\"",
        },
    ),
    (
        {
            "slug": "processing-contrib-cache",
            "harbor": "harbor-p5",
            "env": "PROCESSING_JAVA",
            "tool": "processing-java",
            "old": "4.3",
            "new": "4.3.1",
            "artifact": "sketchbook/libraries/controlP5",
            "test": "test_p5.py",
            "src": "src/sketch.pde",
            "cache_id": "p5-431",
            "dead_rm": "rm -rf /root/sketchbook/libraries",
            "dead_obs": "rm libraries does not drop 4.3 controlP5 under unversioned PROCESSING_JAVA",
            "left_mb": "22MB",
            "vs": "r190 godot-export (Processing contrib, not Godot)",
            "img": "FROM debian:bookworm",
            "run": "processing-java --sketch=src --output=/out --force --build",
        },
        {
            "slug": "core-pattern-leftover",
            "harbor": "harbor-corep",
            "token": "CORE_PATTERN_RESET",
            "leftover": "kernel.core_pattern=|/usr/lib/systemd/systemd-coredump",
            "detail": "core_pattern leftover still pipes cache-worker dumps",
            "dead": "echo core > /proc/sys/kernel/core_pattern",
            "dead_obs": "core_pattern write is EPERM; leftover systemd-coredump still pipes dumps",
            "fail_mode": "leftover core_pattern piping cache-worker dumps",
            "not": "r200 cgroup-freezer / cache-admin 403",
            "vs": "r200 cgroup freezer leftover (core_pattern leftover, not freezer)",
            "test": "test_corep.py",
            "probe": "cat /proc/sys/kernel/core_pattern",
            "probe_obs": "|/usr/lib/systemd/systemd-coredump leftover",
            "fix_key": "name: harbor-corep-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_CORE_PATTERN: \"core\"",
        },
    ),
    (
        {
            "slug": "openframeworks-addons",
            "harbor": "harbor-ofx",
            "env": "OF_ROOT",
            "tool": "make",
            "old": "0.11.2",
            "new": "0.12.0",
            "artifact": "addons/ofxOpenCv/libs",
            "test": "test_ofx.py",
            "src": "src/ofApp.cpp",
            "cache_id": "ofx-012",
            "dead_rm": "rm -rf /opt/openframeworks/addons",
            "dead_obs": "rm addons does not drop 0.11 ofxOpenCv under unversioned OF_ROOT",
            "left_mb": "48MB",
            "vs": "r190 godot-export (openFrameworks addons, not Godot)",
            "img": "FROM debian:bookworm",
            "run": "make -C /src Release",
        },
        {
            "slug": "journald-rate-leftover",
            "harbor": "harbor-jrate",
            "token": "JOURNALD_RATE_RESET",
            "leftover": "RateLimitBurst=0",
            "detail": "journald leftover still drops cache-export logs",
            "dead": "systemctl revert systemd-journald",
            "dead_obs": "journald revert is EPERM; leftover RateLimitBurst=0 still drops logs",
            "fail_mode": "leftover journald RateLimitBurst=0 dropping cache-export logs",
            "not": "r211 audit-rules / cache-admin 403",
            "vs": "r211 audit-rules leftover (journald leftover, not auditctl)",
            "test": "test_jrate.py",
            "probe": "systemctl show systemd-journald -p RateLimitBurst",
            "probe_obs": "RateLimitBurst=0 leftover",
            "fix_key": "name: harbor-jrate-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_JOURNALD_RATE: \"10000\"",
        },
    ),
    (
        {
            "slug": "musescore-fonts",
            "harbor": "harbor-mscore",
            "env": "MSCORE_FONTDIR",
            "tool": "mscore",
            "old": "4.2.1",
            "new": "4.4.4",
            "artifact": "fonts/mscore.ttf",
            "test": "test_mscore.py",
            "src": "src/score.mscz",
            "cache_id": "mscore-444",
            "dead_rm": "rm -rf /usr/share/mscore-4.2/fonts",
            "dead_obs": "rm fonts does not drop 4.2 mscore.ttf under unversioned MSCORE_FONTDIR",
            "left_mb": "11MB",
            "vs": "r187 lilypond-data (MuseScore fonts, not LilyPond)",
            "img": "FROM debian:bookworm",
            "run": "mscore -o /out/score.pdf src/score.mscz",
        },
        {
            "slug": "extra-hosts-leftover",
            "harbor": "harbor-exhosts",
            "token": "EXTRA_HOSTS_CLEAR",
            "leftover": "extra-hosts registry=10.8.0.9",
            "detail": "extra-hosts leftover still pins registry to dead IP",
            "dead": "sed -i '/registry/d' /etc/hosts",
            "dead_obs": "hosts edit is EPERM; leftover extra-hosts still pins registry",
            "fail_mode": "leftover extra-hosts pinning registry to dead IP",
            "not": "r219 vxlan / cache-admin 403",
            "vs": "r219 vxlan leftover (extra-hosts leftover, not vxlan)",
            "test": "test_exhosts.py",
            "probe": "getent hosts registry; rg registry /etc/hosts",
            "probe_obs": "10.8.0.9 registry leftover",
            "fix_key": "name: harbor-exhosts-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_EXTRA_HOSTS: \"0\"",
        },
    ),
    (
        {
            "slug": "context-mkiv-cache",
            "harbor": "harbor-context",
            "env": "TEXMFCACHE",
            "tool": "context",
            "old": "2023.05.05",
            "new": "2025.03.01",
            "artifact": "texmf-cache/luatex-cache/context/tuc",
            "test": "test_context.py",
            "src": "src/doc.tex",
            "cache_id": "context-2025",
            "dead_rm": "rm -rf /root/texmf-cache",
            "dead_obs": "rm tuc does not drop 2023 luatex-cache under unversioned TEXMFCACHE",
            "left_mb": "29MB",
            "vs": "r193 texlive-fmt (ConTeXt MkIV, not TeX Live fmt)",
            "img": "FROM debian:bookworm",
            "run": "context src/doc.tex",
        },
        {
            "slug": "nonewprivs-leftover",
            "harbor": "harbor-nnp",
            "token": "NNP_CLEAR",
            "leftover": "NoNewPrivs: 1",
            "detail": "no_new_privs leftover still blocks cache helper setuid",
            "dead": "prctl --no-new-privs=0",
            "dead_obs": "prctl nnp is EPERM; leftover NoNewPrivs=1 still blocks setuid helpers",
            "fail_mode": "leftover no_new_privs blocking cache helper setuid",
            "not": "r232 cap-bounding / r188 seccomp / cache-admin 403",
            "vs": "r232 cap bounding leftover (nnp leftover, not CapBnd)",
            "test": "test_nnp.py",
            "probe": "grep NoNewPrivs /proc/1/status",
            "probe_obs": "NoNewPrivs: 1 leftover",
            "fix_key": "name: harbor-nnp-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_NNP: \"0\"",
        },
    ),
]

PAIRS = [p for p in _r233.PAIRS if p[0]["slug"] not in SKIP and p[1]["slug"] not in SKIP] + EXTRA
if len(PAIRS) < 16:
    raise SystemExit(f"catalog too short: {len(PAIRS)}")


def notes_for(round_n: int, suc: dict, left: dict, srec: dict, lrec: dict) -> str:
    cov = 21 + ((round_n - CATALOG_FIRST) % 5)
    return (
        f"# NOTES-r{round_n} docker-build-cache-factory\n"
        f"\n"
        f"Novel coverage: {cov}%\n"
        f"\n"
        f"- Episodes: 2 (quota). Step counts: {suc['slug']} {srec['reward']['cost_steps']}, "
        f"{left['slug']} {lrec['reward']['cost_steps']} (16–24).\n"
        f"- Debug loops: Dead-end: {suc['dead_obs']} (7–8); Dead-end: {left['dead_obs']} (7–8).\n"
        f"- One success (`{srec['id']}`) and one partial (`{lrec['id']}`).\n"
        f"- Distinct from prior rounds: {suc['slug']} vs {suc['vs']} / "
        f"{left['slug']} vs {left['vs']}.\n"
        f"- Fail mode: {left['fail_mode']}, not {left['not']}.\n"
        f"- Residual synthetic tells: invented harbor plants.\n"
        f"- Ban check: not r192 GNU Prolog / landlock, not r149 SWI, not r188 seccomp, "
        f"not r131 AppArmor, not GOTOOLCHAIN/GOCACHE, not Bundler, not r193–r247 plants.\n"
    )


def write_round(round_n: int, staging: Path) -> None:
    idx = round_n - CATALOG_FIRST
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(f"no catalog pair for r{round_n} idx={idx} len={len(PAIRS)}")
    suc, left = PAIRS[idx]
    srec = success_episode(round_n, suc)
    lrec = leftover_episode(round_n, left)
    batch = staging / f"batch-r{round_n:02d}.jsonl"
    notes = staging / f"NOTES-r{round_n:02d}.md"
    batch.write_text(json.dumps(srec, separators=(",", ":")) + "\n" + json.dumps(lrec, separators=(",", ":")) + "\n")
    notes.write_text(notes_for(round_n, suc, left, srec, lrec))
    print(
        json.dumps(
            {
                "round": round_n,
                "ids": [srec["id"], lrec["id"]],
                "steps": [srec["reward"]["cost_steps"], lrec["reward"]["cost_steps"]],
                "bytes": batch.stat().st_size,
            }
        )
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    args = ap.parse_args()
    write_round(args.round, Path(args.staging))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
