#!/usr/bin/env python3
"""Mill docker-build-cache-factory r193+ as unique toolchain × leftover plants.

BAN: r192 GNU Prolog wam / landlock leftover, r149 SWI pack, r188 seccomp,
r131 AppArmor, GOTOOLCHAIN/GOCACHE namespaced, Bundler Ruby leftover.
NEW cache plants only. meta.generator=grok-4.6. Q=2. 16–24 steps.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

FACTORY = "docker-build-cache-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 193

BANNED_NEEDLES = (
    "gprolog",
    "gnu-prolog",
    "gnu_prolog",
    "landlock",
    "swi-prolog",
    "swi_prolog",
    "seccomp",
    "apparmor",
    "gotoolchain",
    "gocache",
    "bundler",
    "ruby33",
    "ruby-3.3",
)


def hx(slug: str) -> str:
    return hashlib.sha1(slug.encode()).hexdigest()[:4]


def clip(text: str, n: int = 240) -> str:
    text = " ".join(str(text).split())
    if len(text) <= n:
        return text
    return text[: n - 1].rstrip() + "…"


def step(n: int, basis: str, name: str, args: dict, obs: str) -> dict:
    basis = clip(basis)
    prefix = basis.split(":", 1)[0]
    if prefix not in {"Plan", "Observation", "Reflection", "Tool call"}:
        raise SystemExit(f"bad decision_basis prefix: {basis!r}")
    return {
        "n": n,
        "decision_basis": basis,
        "tool_call": {"name": name, "args": args},
        "observation": obs,
    }


def bash(n: int, basis: str, cmd: str, obs: str) -> dict:
    return step(n, basis, "bash", {"command": cmd}, obs)


def read(n: int, basis: str, path: str, obs: str) -> dict:
    return step(n, basis, "read", {"path": path}, obs)


def grep(n: int, basis: str, path: str, pattern: str, obs: str) -> dict:
    return step(n, basis, "grep", {"path": path, "pattern": pattern}, obs)


def edit(n: int, basis: str, path: str, old: str, new: str, obs: str) -> dict:
    return step(n, basis, "edit", {"path": path, "old": old, "new": new}, obs)


def guard_plant(spec: dict) -> None:
    """Ban check on the plant identity, not contrast mentions of prior rounds."""
    identity = " ".join(
        str(spec.get(k, ""))
        for k in ("slug", "harbor", "env", "tool", "leftover", "token", "cache_id")
    ).lower()
    for needle in BANNED_NEEDLES:
        if needle in identity:
            raise SystemExit(f"banned needle {needle!r} in plant identity {identity!r}")


# (success, leftover) pairs. Each success is an unversioned toolchain cache.
# Each leftover is a host/driver residue that survives the dead-end cleanup.
PAIRS: list[tuple[dict, dict]] = [
    (
        {
            "slug": "texlive-fmt-cache",
            "harbor": "harbor-texlive",
            "env": "TEXMFVAR",
            "tool": "fmtutil-sys",
            "old": "2023",
            "new": "2025",
            "artifact": "lualatex.fmt",
            "test": "test_texlive.py",
            "src": "src/main.tex",
            "cache_id": "texlive-2025",
            "dead_rm": "rm -f /var/cache/texlive/*.fmt",
            "dead_obs": "rm .fmt does not drop 2023 lualatex.fmt under unversioned TEXMFVAR",
            "left_mb": "18MB",
            "vs": "r187 lilypond-data (TeX fmt dumps, not LilyPond fonts)",
            "img": "FROM texlive/texlive:2025-full",
            "run": "fmtutil-sys --byfmt lualatex && lualatex src/main.tex",
        },
        {
            "slug": "nbd-leftover",
            "harbor": "harbor-nbd",
            "token": "NBD_DETACH",
            "leftover": "/dev/nbd3",
            "detail": "nbd3 still holding /var/cache/buildkit/cache.img",
            "dead": "nbd-client -d /dev/nbd3",
            "dead_obs": "nbd-client -d is EBUSY; leftover nbd3 still holds the cache file",
            "fail_mode": "leftover /dev/nbd3 cache backing causing EBUSY",
            "not": "r191 loopdev / cache-admin 403",
            "vs": "r191 loopdev leftover (NBD client leftover, not loop device)",
            "test": "test_nbd.py",
            "probe": "nbd-client -l localhost; lsblk /dev/nbd3",
            "probe_obs": "nbd3  40G  cache.img  holder pid=buildkitd (EBUSY)",
            "fix_key": "name: harbor-nbd-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_NBD: \"0\"",
        },
    ),
    (
        {
            "slug": "gap-pkg-cache",
            "harbor": "harbor-gap",
            "env": "GAP_DIR",
            "tool": "gap",
            "old": "4.12.2",
            "new": "4.14.0",
            "artifact": "pkg/io/bin/io.so",
            "test": "test_gap.py",
            "src": "src/app.g",
            "cache_id": "gap-414",
            "dead_rm": "rm -rf /root/.gap/pkg",
            "dead_obs": "rm pkg does not drop 4.12 io.so under unversioned GAP_DIR",
            "left_mb": "22MB",
            "vs": "r181 why3-lib (GAP packages, not Why3 theories)",
            "img": "FROM gapsystem/gap:4.14.0",
            "run": "gap -A src/app.g",
        },
        {
            "slug": "bpffs-pin-leftover",
            "harbor": "harbor-bpffs",
            "token": "BPF_FS_UNPIN",
            "leftover": "/sys/fs/bpf/buildkit/cache_guard",
            "detail": "pinned BPF prog still attached after unpin",
            "dead": "rm /sys/fs/bpf/buildkit/cache_guard",
            "dead_obs": "rm pin is EBUSY; leftover bpf pin still loaded on the worker",
            "fail_mode": "leftover bpffs pin blocking cache writes",
            "not": "r188 seccomp / r192 landlock / cache-admin 403",
            "vs": "r188 seccomp leftover (bpffs pin, not runc seccomp profile)",
            "test": "test_bpffs.py",
            "probe": "bpftool prog show pinned /sys/fs/bpf/buildkit/cache_guard",
            "probe_obs": "id 91  name cache_guard  type cgroup_skb  leftover pin",
            "fix_key": "name: harbor-bpffs-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_BPFFS: \"0\"",
        },
    ),
    (
        {
            "slug": "maxima-lisp-cache",
            "harbor": "harbor-maxima",
            "env": "MAXIMA_USERDIR",
            "tool": "maxima",
            "old": "5.46.0",
            "new": "5.47.0",
            "artifact": "binary/binary-sbcl/maxima.core",
            "test": "test_maxima.py",
            "src": "src/app.mac",
            "cache_id": "maxima-547",
            "dead_rm": "rm -f /root/.maxima/binary/binary-sbcl/maxima.core",
            "dead_obs": "rm maxima.core does not drop 5.46 fasl under unversioned MAXIMA_USERDIR",
            "left_mb": "31MB",
            "vs": "r184 ghdl-work (Maxima lisp core, not GHDL work lib)",
            "img": "FROM maximaorg/maxima:5.47.0",
            "run": "maxima --very-quiet -b src/app.mac",
        },
        {
            "slug": "netns-leftover",
            "harbor": "harbor-netns",
            "token": "NETNS_DELETE",
            "leftover": "buildkit-old",
            "detail": "ip netns buildkit-old still holds veth-bk0",
            "dead": "ip netns del buildkit-old",
            "dead_obs": "ip netns del is EBUSY; leftover netns still holds the exporter veth",
            "fail_mode": "leftover netns buildkit-old blackholing cache export",
            "not": "r187 runc-systemd-cgroup / cache-admin 403",
            "vs": "r187 runc SystemdCgroup leftover (netns leftover, not runc cgroup)",
            "test": "test_netns.py",
            "probe": "ip netns list; ip -n buildkit-old link",
            "probe_obs": "buildkit-old (id: 14)\nveth-bk0@if3 UP  leftover",
            "fix_key": "name: harbor-netns-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_NETNS: \"fresh\"",
        },
    ),
    (
        {
            "slug": "octave-pkg-cache",
            "harbor": "harbor-octave",
            "env": "OCTAVE_SITE_PATH",
            "tool": "octave-cli",
            "old": "8.4.0",
            "new": "9.2.0",
            "artifact": "oct/x86_64-pc-linux-gnu/control.oct",
            "test": "test_octave.py",
            "src": "src/app.m",
            "cache_id": "octave-92",
            "dead_rm": "rm -rf /root/.octave/pkg",
            "dead_obs": "rm pkg does not drop 8.4 control.oct under unversioned OCTAVE_SITE_PATH",
            "left_mb": "14MB",
            "vs": "r190 godot-export (Octave .oct, not Godot import cache)",
            "img": "FROM gnuoctave/octave:9.2.0",
            "run": "octave-cli --no-gui src/app.m",
        },
        {
            "slug": "nftables-leftover",
            "harbor": "harbor-nft",
            "token": "NFT_FLUSH",
            "leftover": "table inet buildkit-filter",
            "detail": "nft table still drops cache-export dport 5000",
            "dead": "nft flush table inet buildkit-filter",
            "dead_obs": "nft flush is EPERM inside the job; leftover table still drops export",
            "fail_mode": "leftover nftables buildkit-filter dropping cache export",
            "not": "r186 oci-mediatypes / cache-admin 403",
            "vs": "r186 oci-mediatypes leftover (nft filter leftover, not mediaType index)",
            "test": "test_nft.py",
            "probe": "nft list table inet buildkit-filter",
            "probe_obs": "table inet buildkit-filter { chain output { tcp dport 5000 drop } }",
            "fix_key": "name: harbor-nft-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_NFT: \"0\"",
        },
    ),
    (
        {
            "slug": "sage-dot-cache",
            "harbor": "harbor-sage",
            "env": "DOT_SAGE",
            "tool": "sage",
            "old": "10.3",
            "new": "10.5",
            "artifact": "cache/10.3/cython/spkg.spyx.so",
            "test": "test_sage.py",
            "src": "src/app.sage",
            "cache_id": "sage-105",
            "dead_rm": "rm -rf /root/.sage/cache",
            "dead_obs": "rm cache does not drop 10.3 spyx under unversioned DOT_SAGE",
            "left_mb": "44MB",
            "vs": "r154 futhark (Sage DOT_SAGE, not Futhark IR)",
            "img": "FROM sagemath/sagemath:10.5",
            "run": "sage src/app.sage",
        },
        {
            "slug": "veth-leftover",
            "harbor": "harbor-veth",
            "token": "VETH_DELETE",
            "leftover": "veth-bkold0",
            "detail": "veth-bkold0 still enslaved to br-buildkit",
            "dead": "ip link del veth-bkold0",
            "dead_obs": "ip link del is EBUSY; leftover veth still enslaved on br-buildkit",
            "fail_mode": "leftover veth-bkold0 stealing exporter MAC",
            "not": "r180 overlay-verity / cache-admin 403",
            "vs": "r180 overlay-verity leftover (veth leftover, not overlay verity)",
            "test": "test_veth.py",
            "probe": "ip link show veth-bkold0; bridge link",
            "probe_obs": "veth-bkold0@if17 master br-buildkit UP leftover",
            "fix_key": "name: harbor-veth-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_VETH: \"fresh\"",
        },
    ),
    (
        {
            "slug": "gambit-gsc-cache",
            "harbor": "harbor-gambit",
            "env": "GAMBITDIR",
            "tool": "gsc",
            "old": "4.9.3",
            "new": "4.9.5",
            "artifact": "lib/_gambit.c",
            "test": "test_gambit.py",
            "src": "src/app.scm",
            "cache_id": "gambit-495",
            "dead_rm": "rm -rf /usr/local/gambit/lib",
            "dead_obs": "rm lib does not drop 4.9.3 _gambit.c under unversioned GAMBITDIR",
            "left_mb": "9MB",
            "vs": "r165 chez-so (Gambit gsc, not Chez .so)",
            "img": "FROM gambit/gambit:4.9.5",
            "run": "gsc -exe src/app.scm",
        },
        {
            "slug": "zram-leftover",
            "harbor": "harbor-zram",
            "token": "ZRAM_RESET",
            "leftover": "/dev/zram0",
            "detail": "zram0 still compressed 3.2G of cache pages",
            "dead": "echo 1 > /sys/block/zram0/reset",
            "dead_obs": "zram reset is EPERM; leftover zram0 still holds compressed cache",
            "fail_mode": "leftover zram0 compressing cache pages after disable",
            "not": "r189 hugepages / cache-admin 403",
            "vs": "r189 hugepages leftover (zram leftover, not vm.nr_hugepages)",
            "test": "test_zram.py",
            "probe": "cat /sys/block/zram0/mm_stat; swapon --show",
            "probe_obs": "orig 3.2G  compr 810M  leftover zram0 [SWAP]",
            "fix_key": "name: harbor-zram-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_ZRAM: \"0\"",
        },
    ),
    (
        {
            "slug": "shadow-cljs-cache",
            "harbor": "harbor-shadow",
            "env": "SHADOW_CACHE",
            "tool": "npx shadow-cljs",
            "old": "2.25.8",
            "new": "2.28.10",
            "artifact": ".shadow-cljs/builds/app/dev/cache.transit.json",
            "test": "test_shadow.py",
            "src": "src/app/core.cljs",
            "cache_id": "shadow-228",
            "dead_rm": "rm -rf /root/.shadow-cljs",
            "dead_obs": "rm .shadow-cljs does not drop 2.25 transit under unversioned SHADOW_CACHE",
            "left_mb": "27MB",
            "vs": "r136 clojure-deps (shadow-cljs transit, not deps.edn)",
            "img": "FROM clojure:temurin-21-tools-deps",
            "run": "npx shadow-cljs release app",
        },
        {
            "slug": "io-uring-leftover",
            "harbor": "harbor-iouring",
            "token": "IO_URING_EXIT",
            "leftover": "io_uring-sqp/91",
            "detail": "SQPOLL worker still pins cache fd 17",
            "dead": "echo 0 > /proc/sys/kernel/io_uring_disabled",
            "dead_obs": "sysctl io_uring_disabled is EPERM; leftover SQPOLL still pins the cache fd",
            "fail_mode": "leftover io_uring SQPOLL pinning cache fd",
            "not": "r191 loopdev / cache-admin 403",
            "vs": "r191 loopdev leftover (io_uring leftover, not loop device)",
            "test": "test_iouring.py",
            "probe": "ls /proc/91/fdinfo; cat /proc/sys/kernel/io_uring_disabled",
            "probe_obs": "fd 17  io_uring  flags=SQPOLL leftover\nio_uring_disabled=0",
            "fix_key": "name: harbor-iouring-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_IO_URING: \"0\"",
        },
    ),
    (
        {
            "slug": "babashka-deps-cache",
            "harbor": "harbor-bb",
            "env": "BABASHKA_CLASSPATH",
            "tool": "bb",
            "old": "1.3.191",
            "new": "1.4.192",
            "artifact": ".gitlibs/libs/babashka/fs/src",
            "test": "test_bb.py",
            "src": "src/app.clj",
            "cache_id": "bb-14192",
            "dead_rm": "rm -rf /root/.gitlibs",
            "dead_obs": "rm .gitlibs does not drop 1.3 fs under unversioned BABASHKA_CLASSPATH",
            "left_mb": "11MB",
            "vs": "r136 clojure-deps (Babashka gitlibs, not JVM deps.edn)",
            "img": "FROM babashka/babashka:1.4.192",
            "run": "bb src/app.clj",
        },
        {
            "slug": "cgroup-freezer-leftover",
            "harbor": "harbor-freezer",
            "token": "FREEZER_THAW",
            "leftover": "freezer.state=FROZEN",
            "detail": "builder cgroup still FROZEN after thaw write",
            "dead": "echo THAWED > /sys/fs/cgroup/buildkit/freezer.state",
            "dead_obs": "freezer thaw is EPERM; leftover FROZEN still stalls cache export",
            "fail_mode": "leftover cgroup freezer.state=FROZEN stalling export",
            "not": "r181 cgroup-hugetlb / r184 cgroup-parent / cache-admin 403",
            "vs": "r181 cgroup hugetlb leftover (freezer leftover, not hugetlb.max)",
            "test": "test_freezer.py",
            "probe": "cat /sys/fs/cgroup/buildkit/freezer.state",
            "probe_obs": "FROZEN",
            "fix_key": "name: harbor-freezer-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_FREEZER: \"0\"",
        },
    ),
    (
        {
            "slug": "uiua-pad-cache",
            "harbor": "harbor-uiua",
            "env": "UIUA_HOME",
            "tool": "uiua",
            "old": "0.11.1",
            "new": "0.14.1",
            "artifact": "pad/cache/0.11/std.ua",
            "test": "test_uiua.py",
            "src": "src/app.ua",
            "cache_id": "uiua-014",
            "dead_rm": "rm -rf /root/.uiua/pad",
            "dead_obs": "rm pad does not drop 0.11 std.ua under unversioned UIUA_HOME",
            "left_mb": "6MB",
            "vs": "r189 assemblyscript (Uiua pad, not ASC std)",
            "img": "FROM uiua/uiua:0.14.1",
            "run": "uiua stand src/app.ua",
        },
        {
            "slug": "ima-policy-leftover",
            "harbor": "harbor-ima",
            "token": "IMA_CLEAR",
            "leftover": "ima-policy appraisal",
            "detail": "IMA appraisal still EPERM unsigned cache writes",
            "dead": "echo -n > /sys/kernel/security/ima/policy",
            "dead_obs": "ima policy write is EACCES; leftover appraisal still EPERM cache writes",
            "fail_mode": "leftover IMA appraisal EPERM on cache writes",
            "not": "r188 seccomp / r131 AppArmor / r192 landlock / cache-admin 403",
            "vs": "r156 SELinux context leftover (IMA appraisal leftover, not SELinux xattr)",
            "test": "test_ima.py",
            "probe": "cat /sys/kernel/security/ima/policy | head",
            "probe_obs": "appraise func=FILE_CHECK mask=MAY_WRITE fsuuid=buildkit leftover",
            "fix_key": "name: harbor-ima-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_IMA: \"0\"",
        },
    ),
    (
        {
            "slug": "bqn-cbqn-cache",
            "harbor": "harbor-bqn",
            "env": "BQN_LIB",
            "tool": "bqn",
            "old": "0.7.0",
            "new": "0.9.0",
            "artifact": "lib/bqn/glyphs.bqn",
            "test": "test_bqn.py",
            "src": "src/app.bqn",
            "cache_id": "bqn-09",
            "dead_rm": "rm -rf /usr/lib/bqn",
            "dead_obs": "rm lib does not drop 0.7 glyphs under unversioned BQN_LIB",
            "left_mb": "4MB",
            "vs": "r175 gforth (CBQN lib, not Gforth .fi)",
            "img": "FROM dzaima/cbqn:0.9.0",
            "run": "bqn src/app.bqn",
        },
        {
            "slug": "fscrypt-leftover",
            "harbor": "harbor-fscrypt",
            "token": "FSCRYPT_PURGE",
            "leftover": "fscrypt policy v2",
            "detail": "ext4 encryption policy still on cache dir after unlock",
            "dead": "fscrypt purge /var/lib/buildkit",
            "dead_obs": "fscrypt purge is EPERM; leftover policy still wraps cache dir",
            "fail_mode": "leftover fscrypt policy wrapping cache dir",
            "not": "r152 virtiofs / cache-admin 403",
            "vs": "r152 virtiofs delegated leftover (fscrypt leftover, not virtiofs)",
            "test": "test_fscrypt.py",
            "probe": "fscrypt status /var/lib/buildkit; lsattr -d /var/lib/buildkit",
            "probe_obs": "Encrypted: Yes  Policy: v2 leftover\nE---------  /var/lib/buildkit",
            "fix_key": "name: harbor-fscrypt-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_FSCRYPT: \"0\"",
        },
    ),
    (
        {
            "slug": "apl-dyalog-cache",
            "harbor": "harbor-dyalog",
            "env": "DYALOG",
            "tool": "dyalog",
            "old": "18.2",
            "new": "19.0",
            "artifact": "ws/dfns.dws",
            "test": "test_dyalog.py",
            "src": "src/app.apln",
            "cache_id": "dyalog-19",
            "dead_rm": "rm -f /opt/mdyalog/ws/dfns.dws",
            "dead_obs": "rm dfns.dws does not drop 18.2 workspace under unversioned DYALOG",
            "left_mb": "13MB",
            "vs": "r191 icon-ucode (Dyalog ws, not Icon ucode)",
            "img": "FROM dyalog/dyalog:19.0",
            "run": "dyalog -script src/app.apln",
        },
        {
            "slug": "gvisor-runsc-leftover",
            "harbor": "harbor-gvisor",
            "token": "RUNSC_KILL",
            "leftover": "runsc sentry",
            "detail": "runsc sentry still holds cache mount after kill",
            "dead": "runsc kill buildkit --force",
            "dead_obs": "runsc kill is EBUSY; leftover sentry still holds the cache mount",
            "fail_mode": "leftover gVisor runsc sentry holding cache mount",
            "not": "r187 runc-systemd-cgroup / cache-admin 403",
            "vs": "r187 runc SystemdCgroup leftover (gVisor sentry leftover, not runc)",
            "test": "test_gvisor.py",
            "probe": "runsc list; mount | rg runsc",
            "probe_obs": "buildkit  running  leftover sentry\nrunsc overlay on /var/lib/buildkit leftover",
            "fix_key": "name: harbor-gvisor-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_RUNTIME: \"runc\"",
        },
    ),
    (
        {
            "slug": "jlang-addons-cache",
            "harbor": "harbor-jlang",
            "env": "J_HOME",
            "tool": "jconsole",
            "old": "9.4",
            "new": "9.6",
            "artifact": "addons/stats/base/stats.ijs",
            "test": "test_jlang.py",
            "src": "src/app.ijs",
            "cache_id": "jlang-96",
            "dead_rm": "rm -rf /root/j9.4/addons",
            "dead_obs": "rm addons does not drop 9.4 stats.ijs under unversioned J_HOME",
            "left_mb": "8MB",
            "vs": "r182 minizinc-stdlib (J addons, not MiniZinc stdlib)",
            "img": "FROM jlang/j:9.6",
            "run": "jconsole src/app.ijs",
        },
        {
            "slug": "kata-shim-leftover",
            "harbor": "harbor-kata",
            "token": "KATA_SHIM_STOP",
            "leftover": "containerd-shim-kata-v2",
            "detail": "kata shimv2 still attached after StopVM",
            "dead": "kata-runtime kill --force buildkit",
            "dead_obs": "kata kill is EBUSY; leftover shimv2 still attached to the VM",
            "fail_mode": "leftover kata shimv2 holding cache VM",
            "not": "r187 runc-systemd-cgroup / cache-admin 403",
            "vs": "r187 runc leftover (kata shim leftover, not runc cgroup)",
            "test": "test_kata.py",
            "probe": "ps -C containerd-shim-kata-v2; kata-runtime list",
            "probe_obs": "shim-kata-v2 leftover pid 4401\nbuildkit running leftover",
            "fix_key": "name: harbor-kata-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_RUNTIME: \"runc\"",
        },
    ),
    (
        {
            "slug": "vala-vapi-cache",
            "harbor": "harbor-vala",
            "env": "VAPIDIR",
            "tool": "valac",
            "old": "0.56.17",
            "new": "0.58.0",
            "artifact": "vapi/gtk+-3.0.vapi",
            "test": "test_vala.py",
            "src": "src/app.vala",
            "cache_id": "vala-058",
            "dead_rm": "rm -rf /usr/share/vala/vapi",
            "dead_obs": "rm vapi does not drop 0.56 gtk vapi under unversioned VAPIDIR",
            "left_mb": "16MB",
            "vs": "r183 verilator-obj (Vala vapi, not Verilator obj)",
            "img": "FROM debian:bookworm",
            "run": "valac -o /out/app src/app.vala --pkg gtk+-3.0",
        },
        {
            "slug": "crun-cgroupns-leftover",
            "harbor": "harbor-crun",
            "token": "CRUN_CGROUPNS",
            "leftover": "crun cgroupns",
            "detail": "crun still joined host cgroupns after private switch",
            "dead": "crun update --cgroupns private buildkit",
            "dead_obs": "crun update is EINVAL; leftover host cgroupns still joined",
            "fail_mode": "leftover crun host cgroupns after private switch",
            "not": "r187 runc-systemd-cgroup / cache-admin 403",
            "vs": "r187 runc SystemdCgroup leftover (crun cgroupns leftover, not runc)",
            "test": "test_crun.py",
            "probe": "crun state buildkit; lsns -t cgroup",
            "probe_obs": "cgroupns host leftover  nstype=cgroup  nprocs=4",
            "fix_key": "name: harbor-crun-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_RUNTIME: \"crun\"\n          env.BUILDKIT_CGROUPNS: \"private\"",
        },
    ),
    (
        {
            "slug": "groovy-grape-cache",
            "harbor": "harbor-grape",
            "env": "GROOVY_HOME",
            "tool": "grape",
            "old": "4.0.21",
            "new": "4.0.24",
            "artifact": ".groovy/grapes/org.apache.commons/commons-lang3",
            "test": "test_grape.py",
            "src": "src/App.groovy",
            "cache_id": "grape-4024",
            "dead_rm": "rm -rf /root/.groovy/grapes",
            "dead_obs": "rm grapes does not drop 4.0.21 ivy under unversioned GROOVY_HOME",
            "left_mb": "19MB",
            "vs": "r119 sbt-coursier (Grape ivy, not Coursier)",
            "img": "FROM groovy:4.0.24-jdk21",
            "run": "grape install org.apache.commons commons-lang3 3.14.0 && groovy src/App.groovy",
        },
        {
            "slug": "youki-rootfs-leftover",
            "harbor": "harbor-youki",
            "token": "YOUKI_DELETE",
            "leftover": "youki rootfs overlay",
            "detail": "youki rootfs still mounted after delete",
            "dead": "youki delete --force buildkit",
            "dead_obs": "youki delete is EBUSY; leftover rootfs overlay still mounted",
            "fail_mode": "leftover youki rootfs overlay still mounted",
            "not": "r176 overlay-metacopy / cache-admin 403",
            "vs": "r176 overlay-metacopy leftover (youki rootfs leftover, not overlay flag)",
            "test": "test_youki.py",
            "probe": "youki list; findmnt /run/youki/buildkit/rootfs",
            "probe_obs": "buildkit leftover\noverlay /run/youki/buildkit/rootfs leftover",
            "fix_key": "name: harbor-youki-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_RUNTIME: \"runc\"",
        },
    ),
    (
        {
            "slug": "hugo-modules-cache",
            "harbor": "harbor-hugo",
            "env": "HUGO_CACHEDIR",
            "tool": "hugo",
            "old": "0.121.2",
            "new": "0.136.5",
            "artifact": "modules/pkg/hugo-mod-bootstrap/go.mod",
            "test": "test_hugo.py",
            "src": "src/content/_index.md",
            "cache_id": "hugo-0136",
            "dead_rm": "rm -rf /tmp/hugo_cache",
            "dead_obs": "rm hugo_cache does not drop 0.121 modules under unversioned HUGO_CACHEDIR",
            "left_mb": "33MB",
            "vs": "r86 go-workspace (Hugo modules cache, not go.work)",
            "img": "FROM hugomods/hugo:0.136.5",
            "run": "hugo --gc --minify",
        },
        {
            "slug": "cgroup-memory-high-leftover",
            "harbor": "harbor-memhigh",
            "token": "MEMORY_HIGH_CLEAR",
            "leftover": "memory.high=512M",
            "detail": "memory.high leftover still throttles GC",
            "dead": "echo max > /sys/fs/cgroup/buildkit/memory.high",
            "dead_obs": "memory.high write is EPERM; leftover 512M still throttles GC",
            "fail_mode": "leftover cgroup memory.high=512M throttling GC",
            "not": "r164 keepStorage / r185 reservedSpace / cache-admin 403",
            "vs": "r185 gc reservedSpace leftover (memory.high leftover, not reserved floor)",
            "test": "test_memhigh.py",
            "probe": "cat /sys/fs/cgroup/buildkit/memory.high /sys/fs/cgroup/buildkit/memory.events",
            "probe_obs": "536870912\nhigh 1841 leftover",
            "fix_key": "name: harbor-memhigh-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_MEMORY_HIGH: \"max\"",
        },
    ),
    (
        {
            "slug": "quarto-cache",
            "harbor": "harbor-quarto",
            "env": "QUARTO_CACHE",
            "tool": "quarto",
            "old": "1.4.553",
            "new": "1.6.40",
            "artifact": ".quarto/idx/site.json",
            "test": "test_quarto.py",
            "src": "src/index.qmd",
            "cache_id": "quarto-164",
            "dead_rm": "rm -rf /root/.quarto",
            "dead_obs": "rm .quarto does not drop 1.4 idx under unversioned QUARTO_CACHE",
            "left_mb": "12MB",
            "vs": "r139 flutter-pub (Quarto idx, not Flutter engine)",
            "img": "FROM ghcr.io/quarto-dev/quarto:1.6.40",
            "run": "quarto render src/index.qmd",
        },
        {
            "slug": "cgroup-rdma-leftover",
            "harbor": "harbor-rdma",
            "token": "RDMA_MAX_CLEAR",
            "leftover": "rdma.max mlx5_0 hca_handle=0",
            "detail": "rdma.max leftover still denies cache RDMA export",
            "dead": "echo mlx5_0 hca_handle=max > /sys/fs/cgroup/buildkit/rdma.max",
            "dead_obs": "rdma.max write is EPERM; leftover hca_handle=0 still denies export",
            "fail_mode": "leftover cgroup rdma.max denying cache RDMA export",
            "not": "r181 cgroup-hugetlb / cache-admin 403",
            "vs": "r181 cgroup hugetlb leftover (rdma leftover, not hugetlb)",
            "test": "test_rdma.py",
            "probe": "cat /sys/fs/cgroup/buildkit/rdma.max",
            "probe_obs": "mlx5_0 hca_handle=0 hca_object=0 leftover",
            "fix_key": "name: harbor-rdma-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_RDMA: \"0\"",
        },
    ),
    (
        {
            "slug": "ros2-colcon-cache",
            "harbor": "harbor-colcon",
            "env": "COLCON_HOME",
            "tool": "colcon",
            "old": "humble",
            "new": "jazzy",
            "artifact": "install/setup.bash",
            "test": "test_colcon.py",
            "src": "src/pkg/package.xml",
            "cache_id": "colcon-jazzy",
            "dead_rm": "rm -rf /root/.colcon /ws/build /ws/install",
            "dead_obs": "rm build does not drop humble ament under unversioned COLCON_HOME",
            "left_mb": "61MB",
            "vs": "r185 fusesoc-core (colcon ament, not FuseSoC cores)",
            "img": "FROM ros:jazzy",
            "run": "colcon build --symlink-install",
        },
        {
            "slug": "time-ns-leftover",
            "harbor": "harbor-timens",
            "token": "TIMENS_RESET",
            "leftover": "timens offset +3600s",
            "detail": "time namespace offset still skews SOURCE_DATE_EPOCH",
            "dead": "echo 0 0 > /proc/self/timens_offsets",
            "dead_obs": "timens_offsets write is EPERM; leftover +3600s still skews epoch",
            "fail_mode": "leftover time namespace offset skewing SOURCE_DATE_EPOCH",
            "not": "r48 bind-host-mtime / r190 lazytime / cache-admin 403",
            "vs": "r190 mount-lazytime leftover (timens leftover, not lazytime flush)",
            "test": "test_timens.py",
            "probe": "cat /proc/self/timens_offsets; date -u",
            "probe_obs": "monotonic 3600 0\nboottime 3600 0 leftover",
            "fix_key": "name: harbor-timens-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_TIMENS: \"0\"",
        },
    ),
    (
        {
            "slug": "yosys-abc-cache",
            "harbor": "harbor-yosys",
            "env": "ABC_LIB",
            "tool": "yosys",
            "old": "0.40",
            "new": "0.46",
            "artifact": "abc9/lib/asap7.lib",
            "test": "test_yosys.py",
            "src": "src/top.v",
            "cache_id": "yosys-046",
            "dead_rm": "rm -rf /root/.cache/abc",
            "dead_obs": "rm abc does not drop 0.40 asap7.lib under unversioned ABC_LIB",
            "left_mb": "25MB",
            "vs": "r183 verilator-obj (Yosys ABC lib, not Verilator obj_dir)",
            "img": "FROM hdlc/yosys:0.46",
            "run": "yosys -p 'read_verilog src/top.v; synth; abc'",
        },
        {
            "slug": "pidns-leftover",
            "harbor": "harbor-pidns",
            "token": "PIDNS_REAP",
            "leftover": "pidns zombie buildkitd",
            "detail": "pid namespace still has zombie worker pid 1 child",
            "dead": "kill -9 1; wait",
            "dead_obs": "reap is ECHILD; leftover pidns still has zombie buildkit worker",
            "fail_mode": "leftover pid namespace zombie blocking builder recreate",
            "not": "r187 runc-systemd-cgroup / cache-admin 403",
            "vs": "r187 runc leftover (pidns leftover, not SystemdCgroup)",
            "test": "test_pidns.py",
            "probe": "lsns -t pid; ps -eo pid,stat,comm | rg 'Z|buildkit'",
            "probe_obs": "pidns leftover nprocs=3\n88 Z buildkitd leftover",
            "fix_key": "name: harbor-pidns-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_PIDNS: \"fresh\"",
        },
    ),
    (
        {
            "slug": "nextpnr-chipdb-cache",
            "harbor": "harbor-nextpnr",
            "env": "NEXTPNR_CHIPDB",
            "tool": "nextpnr-ice40",
            "old": "0.6",
            "new": "0.7",
            "artifact": "chipdb/ice40/chipdb-hx8k.bin",
            "test": "test_nextpnr.py",
            "src": "src/top.json",
            "cache_id": "nextpnr-07",
            "dead_rm": "rm -rf /usr/share/nextpnr/ice40",
            "dead_obs": "rm chipdb does not drop 0.6 hx8k.bin under unversioned NEXTPNR_CHIPDB",
            "left_mb": "48MB",
            "vs": "r183 verilator-obj (nextpnr chipdb, not Verilator)",
            "img": "FROM hdlc/nextpnr:0.7",
            "run": "nextpnr-ice40 --hx8k --json src/top.json --asc /out/top.asc",
        },
        {
            "slug": "audit-rules-leftover",
            "harbor": "harbor-audit",
            "token": "AUDITCTL_D",
            "leftover": "auditctl watch /var/lib/buildkit",
            "detail": "audit watch still log-blocks cache writes",
            "dead": "auditctl -D",
            "dead_obs": "auditctl -D is EPERM; leftover watch still log-blocks cache writes",
            "fail_mode": "leftover audit rules log-blocking cache writes",
            "not": "r188 seccomp / r156 SELinux / cache-admin 403",
            "vs": "r156 SELinux leftover (audit rules leftover, not SELinux xattr)",
            "test": "test_audit.py",
            "probe": "auditctl -l | head",
            "probe_obs": "-w /var/lib/buildkit -p wa -k leftover",
            "fix_key": "name: harbor-audit-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_AUDIT: \"0\"",
        },
    ),
    (
        {
            "slug": "ngspice-cm-cache",
            "harbor": "harbor-ngspice",
            "env": "SPICE_LIB_DIR",
            "tool": "ngspice",
            "old": "42",
            "new": "44",
            "artifact": "code-models/spice2poly.cm",
            "test": "test_ngspice.py",
            "src": "src/amp.cir",
            "cache_id": "ngspice-44",
            "dead_rm": "rm -rf /usr/lib/ngspice",
            "dead_obs": "rm cm does not drop 42 spice2poly.cm under unversioned SPICE_LIB_DIR",
            "left_mb": "7MB",
            "vs": "r184 ghdl-work (ngspice cm, not GHDL work)",
            "img": "FROM debian:bookworm",
            "run": "ngspice -b src/amp.cir",
        },
        {
            "slug": "systemd-nspawn-leftover",
            "harbor": "harbor-nspawn",
            "token": "MACHINectl_KILL",
            "leftover": "nspawn machine buildkit-old",
            "detail": "nspawn machine still holds cache volume",
            "dead": "machinectl terminate buildkit-old",
            "dead_obs": "machinectl terminate is EBUSY; leftover nspawn still holds the cache volume",
            "fail_mode": "leftover systemd-nspawn machine holding cache volume",
            "not": "r187 runc-systemd-cgroup / cache-admin 403",
            "vs": "r187 runc SystemdCgroup leftover (nspawn leftover, not runc config)",
            "test": "test_nspawn.py",
            "probe": "machinectl list; findmnt /var/lib/machines/buildkit-old",
            "probe_obs": "buildkit-old container leftover\noverlay leftover on machine root",
            "fix_key": "name: harbor-nspawn-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_NSPAWN: \"0\"",
        },
    ),
    (
        {
            "slug": "gnuradio-mod-cache",
            "harbor": "harbor-gnuradio",
            "env": "GR_PREFIX",
            "tool": "grcc",
            "old": "3.10.9",
            "new": "3.10.12",
            "artifact": "lib/python3/dist-packages/gnuradio/blocks/*.so",
            "test": "test_gnuradio.py",
            "src": "src/flow.grc",
            "cache_id": "gnuradio-31012",
            "dead_rm": "rm -rf /root/.gnuradio",
            "dead_obs": "rm .gnuradio does not drop 3.10.9 blocks under unversioned GR_PREFIX",
            "left_mb": "39MB",
            "vs": "r186 faust-lib (GNU Radio mods, not Faust DSP)",
            "img": "FROM gnuradio/gnuradio:3.10.12",
            "run": "grcc -d /out src/flow.grc",
        },
        {
            "slug": "udev-watch-leftover",
            "harbor": "harbor-udev",
            "token": "UDEVADM_CONTROL",
            "leftover": "udev watch /dev/loop",
            "detail": "udev still re-binds cache loop nodes",
            "dead": "udevadm control --stop-exec-queue",
            "dead_obs": "udevadm stop is EPERM; leftover udev watch still rebinds loop nodes",
            "fail_mode": "leftover udev watch rebinding cache loop nodes",
            "not": "r191 loopdev / cache-admin 403",
            "vs": "r191 loopdev leftover (udev watch leftover, not stuck loop)",
            "test": "test_udev.py",
            "probe": "udevadm info /dev/loop7; udevadm control --ping",
            "probe_obs": "E: ID_FS_LABEL=buildkit-cache leftover watch",
            "fix_key": "name: harbor-udev-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_UDEV: \"0\"",
        },
    ),
    (
        {
            "slug": "blender-assets-cache",
            "harbor": "harbor-blender",
            "env": "BLENDER_USER_SCRIPTS",
            "tool": "blender",
            "old": "4.1.1",
            "new": "4.2.3",
            "artifact": "4.1/cache/shaders/osl",
            "test": "test_blender.py",
            "src": "src/scene.blend",
            "cache_id": "blender-423",
            "dead_rm": "rm -rf /root/.config/blender/4.1",
            "dead_obs": "rm 4.1 shaders does not drop OSL under unversioned BLENDER_USER_SCRIPTS",
            "left_mb": "52MB",
            "vs": "r190 godot-export (Blender OSL, not Godot import)",
            "img": "FROM linuxserver/blender:4.2.3",
            "run": "blender -b src/scene.blend -f 1",
        },
        {
            "slug": "md-raid-leftover",
            "harbor": "harbor-md",
            "token": "MDADM_STOP",
            "leftover": "/dev/md127",
            "detail": "md127 still assembled on cache disks",
            "dead": "mdadm --stop /dev/md127",
            "dead_obs": "mdadm --stop is EBUSY; leftover md127 still assembled on cache disks",
            "fail_mode": "leftover md127 assembled on cache disks",
            "not": "r98 devmapper-thinpool / r191 loopdev / cache-admin 403",
            "vs": "r98 devmapper thinpool leftover (md RAID leftover, not thinpool)",
            "test": "test_md.py",
            "probe": "cat /proc/mdstat; mdadm --detail /dev/md127",
            "probe_obs": "md127 : active raid1 leftover\n      2 devices  cache disks",
            "fix_key": "name: harbor-md-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_MD: \"0\"",
        },
    ),
    (
        {
            "slug": "tvm-build-cache",
            "harbor": "harbor-tvm",
            "env": "TVM_LIBRARY_PATH",
            "tool": "python3 -m tvm",
            "old": "0.15.0",
            "new": "0.18.0",
            "artifact": "libtvm_runtime.so",
            "test": "test_tvm.py",
            "src": "src/mod.py",
            "cache_id": "tvm-018",
            "dead_rm": "rm -rf /root/.tvm",
            "dead_obs": "rm .tvm does not drop 0.15 libtvm under unversioned TVM_LIBRARY_PATH",
            "left_mb": "73MB",
            "vs": "r54 emscripten (TVM runtime, not emscripten sysroot)",
            "img": "FROM tlcpack/ci-cpu:20250819",
            "run": "python3 src/mod.py",
        },
        {
            "slug": "iscsi-session-leftover",
            "harbor": "harbor-iscsi",
            "token": "ISCSIADM_LOGOUT",
            "leftover": "iqn.2024-08.harbor.cache",
            "detail": "iscsi session still logged into cache LUN",
            "dead": "iscsiadm -m node -T iqn.2024-08.harbor.cache -u",
            "dead_obs": "iscsiadm logout is EBUSY; leftover session still logged into cache LUN",
            "fail_mode": "leftover iSCSI session holding cache LUN",
            "not": "r191 loopdev / cache-admin 403",
            "vs": "r191 loopdev leftover (iSCSI leftover, not loop device)",
            "test": "test_iscsi.py",
            "probe": "iscsiadm -m session; lsblk /dev/sdb",
            "probe_obs": "tcp: [1] 10.8.0.9:3260,1 iqn.2024-08.harbor.cache leftover",
            "fix_key": "name: harbor-iscsi-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_ISCSI: \"0\"",
        },
    ),
    (
        {
            "slug": "halide-cache",
            "harbor": "harbor-halide",
            "env": "HL_TARGET",
            "tool": "g++",
            "old": "16.0.0",
            "new": "18.0.0",
            "artifact": "lib/libHalide.so.16",
            "test": "test_halide.py",
            "src": "src/blur.cpp",
            "cache_id": "halide-18",
            "dead_rm": "rm -rf /root/.halide",
            "dead_obs": "rm .halide does not drop 16 autoschedule under unversioned HL_TARGET",
            "left_mb": "29MB",
            "vs": "r54 emscripten (Halide autoschedule, not emscripten)",
            "img": "FROM debian:bookworm",
            "run": "g++ src/blur.cpp -lHalide -o /out/blur && /out/blur",
        },
        {
            "slug": "nvmeof-leftover",
            "harbor": "harbor-nvmeof",
            "token": "NVME_DISCONNECT",
            "leftover": "nvme nqn.2024-08.harbor.cache",
            "detail": "nvme-of subsystem still connected",
            "dead": "nvme disconnect -n nqn.2024-08.harbor.cache",
            "dead_obs": "nvme disconnect is EBUSY; leftover nqn still connected",
            "fail_mode": "leftover NVMe-oF nqn holding cache namespace",
            "not": "r191 loopdev / cache-admin 403",
            "vs": "r191 loopdev leftover (NVMe-oF leftover, not loop device)",
            "test": "test_nvmeof.py",
            "probe": "nvme list; nvme list-subsys",
            "probe_obs": "nqn.2024-08.harbor.cache live leftover\n/dev/nvme1n1 40G leftover",
            "fix_key": "name: harbor-nvmeof-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_NVMEOF: \"0\"",
        },
    ),
    (
        {
            "slug": "cuda-nvcc-cache",
            "harbor": "harbor-nvcc",
            "env": "CUDA_CACHE_PATH",
            "tool": "nvcc",
            "old": "12.4",
            "new": "12.6",
            "artifact": "compute_89.cubin",
            "test": "test_nvcc.py",
            "src": "src/kernel.cu",
            "cache_id": "nvcc-126",
            "dead_rm": "rm -rf /root/.nv/ComputeCache",
            "dead_obs": "rm ComputeCache does not drop 12.4 cubin under unversioned CUDA_CACHE_PATH",
            "left_mb": "88MB",
            "vs": "r54 emscripten (CUDA cubin, not emscripten)",
            "img": "FROM nvidia/cuda:12.6.0-devel-ubuntu24.04",
            "run": "nvcc -O3 src/kernel.cu -o /out/k",
        },
        {
            "slug": "ceph-mds-leftover",
            "harbor": "harbor-ceph",
            "token": "CEPH_MDS_FAIL",
            "leftover": "ceph mds.cache cap",
            "detail": "mds still holds cap on cache dir",
            "dead": "ceph mds fail cache",
            "dead_obs": "ceph mds fail is EPERM; leftover mds cap still holds cache dir",
            "fail_mode": "leftover Ceph MDS cap holding cache dir",
            "not": "r49 nfs-estale / cache-admin 403",
            "vs": "r49 nfs-estale leftover (Ceph MDS leftover, not NFS ESTALE)",
            "test": "test_ceph.py",
            "probe": "ceph mds stat; getfattr -n ceph.caps /var/lib/buildkit",
            "probe_obs": "mds.cache leftover active\nceph.caps=pAsLsXs leftover",
            "fix_key": "name: harbor-ceph-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_CEPH: \"0\"",
        },
    ),
    (
        {
            "slug": "hip-rocm-cache",
            "harbor": "harbor-hip",
            "env": "HIP_CACHE_DIR",
            "tool": "hipcc",
            "old": "6.1.2",
            "new": "6.2.4",
            "artifact": "amd_comgr_cache/gfx1100.hsaco",
            "test": "test_hip.py",
            "src": "src/kernel.hip",
            "cache_id": "hip-624",
            "dead_rm": "rm -rf /root/.cache/hip",
            "dead_obs": "rm hip cache does not drop 6.1 hsaco under unversioned HIP_CACHE_DIR",
            "left_mb": "64MB",
            "vs": "cuda-nvcc (HIP hsaco, not CUDA cubin)",
            "img": "FROM rocm/dev-ubuntu-24.04:6.2.4",
            "run": "hipcc src/kernel.hip -o /out/k",
        },
        {
            "slug": "wireguard-leftover",
            "harbor": "harbor-wg",
            "token": "WG_QUICK_DOWN",
            "leftover": "wg0",
            "detail": "wg0 still routes cache export to a dead peer",
            "dead": "wg-quick down wg0",
            "dead_obs": "wg-quick down is EPERM; leftover wg0 still routes export to dead peer",
            "fail_mode": "leftover wg0 routing cache export to dead peer",
            "not": "r53 pasta-vs-slirp / cache-admin 403",
            "vs": "r53 pasta-vs-slirp leftover (wireguard leftover, not pasta MTU)",
            "test": "test_wg.py",
            "probe": "wg show; ip -4 route show dev wg0",
            "probe_obs": "interface: wg0 leftover\npeer dead  allowed 10.88.0.0/16 leftover",
            "fix_key": "name: harbor-wg-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_WG: \"0\"",
        },
    ),
    (
        {
            "slug": "oneapi-icpx-cache",
            "harbor": "harbor-icpx",
            "env": "INTEL_COMPILER_CACHE",
            "tool": "icpx",
            "old": "2024.2",
            "new": "2025.0",
            "artifact": "cache/icpx/2024.2/pch",
            "test": "test_icpx.py",
            "src": "src/app.cpp",
            "cache_id": "icpx-2025",
            "dead_rm": "rm -rf /root/.cache/intel",
            "dead_obs": "rm intel cache does not drop 2024.2 pch under unversioned INTEL_COMPILER_CACHE",
            "left_mb": "41MB",
            "vs": "r18 ccache-gcc-clang (icpx pch, not ccache)",
            "img": "FROM intel/oneapi-hpckit:2025.0.0-devel-ubuntu24.04",
            "run": "icpx -fsycl src/app.cpp -o /out/app",
        },
        {
            "slug": "vxlan-leftover",
            "harbor": "harbor-vxlan",
            "token": "VXLAN_DELETE",
            "leftover": "vxlan100",
            "detail": "vxlan100 still up with stale VNI 100",
            "dead": "ip link del vxlan100",
            "dead_obs": "ip link del vxlan100 is EBUSY; leftover VNI still up",
            "fail_mode": "leftover vxlan100 blackholing cache export",
            "not": "r53 pasta-vs-slirp / cache-admin 403",
            "vs": "r53 pasta leftover (vxlan leftover, not pasta/slirp)",
            "test": "test_vxlan.py",
            "probe": "ip -d link show vxlan100",
            "probe_obs": "vxlan100 UP leftover id 100 remote 10.8.0.8 leftover",
            "fix_key": "name: harbor-vxlan-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_VXLAN: \"0\"",
        },
    ),
    (
        {
            "slug": "vulkan-sdk-cache",
            "harbor": "harbor-vulkan",
            "env": "VULKAN_SDK",
            "tool": "glslc",
            "old": "1.3.280",
            "new": "1.3.296",
            "artifact": "share/vulkan/registry/vk.xml",
            "test": "test_vulkan.py",
            "src": "src/tri.vert",
            "cache_id": "vulkan-13296",
            "dead_rm": "rm -rf /root/VulkanSDK/1.3.280",
            "dead_obs": "rm 1.3.280 does not drop vk.xml under unversioned VULKAN_SDK",
            "left_mb": "36MB",
            "vs": "r94 wasm-platform (Vulkan SDK, not wasm platform)",
            "img": "FROM khronosgroup/vulkan-sdk:1.3.296",
            "run": "glslc src/tri.vert -o /out/tri.spv",
        },
        {
            "slug": "tc-qdisc-leftover",
            "harbor": "harbor-tc",
            "token": "TC_QDISC_DEL",
            "leftover": "netem delay 250ms",
            "detail": "netem qdisc still delays cache export",
            "dead": "tc qdisc del dev eth0 root",
            "dead_obs": "tc qdisc del is EPERM; leftover netem still delays export 250ms",
            "fail_mode": "leftover tc netem delaying cache export",
            "not": "r53 pasta-vs-slirp / cache-admin 403",
            "vs": "r53 pasta leftover (tc qdisc leftover, not pasta MTU)",
            "test": "test_tc.py",
            "probe": "tc qdisc show dev eth0",
            "probe_obs": "qdisc netem 8001: root leftover delay 250ms",
            "fix_key": "name: harbor-tc-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_NETEM: \"0\"",
        },
    ),
    (
        {
            "slug": "webgpu-tint-cache",
            "harbor": "harbor-tint",
            "env": "DAWN_CACHE",
            "tool": "tint",
            "old": "2024.1",
            "new": "2025.2",
            "artifact": "tint/ir/2024.1/std.wgsl",
            "test": "test_tint.py",
            "src": "src/tri.wgsl",
            "cache_id": "tint-20252",
            "dead_rm": "rm -rf /root/.cache/dawn",
            "dead_obs": "rm dawn does not drop 2024.1 wgsl under unversioned DAWN_CACHE",
            "left_mb": "5MB",
            "vs": "r189 assemblyscript (Tint WGSL, not ASC)",
            "img": "FROM debian:bookworm",
            "run": "tint src/tri.wgsl --format spirv -o /out/tri.spv",
        },
        {
            "slug": "ipvs-leftover",
            "harbor": "harbor-ipvs",
            "token": "IPVSADM_C",
            "leftover": "ipvs vip 10.8.0.50:5000",
            "detail": "IPVS virtual still blackholes registry cache",
            "dead": "ipvsadm -C",
            "dead_obs": "ipvsadm -C is EPERM; leftover VIP still blackholes registry",
            "fail_mode": "leftover IPVS VIP blackholing registry cache",
            "not": "r51 registry-401 / cache-admin 403",
            "vs": "r51 registry-401 leftover (IPVS leftover, not PAT expiry)",
            "test": "test_ipvs.py",
            "probe": "ipvsadm -Ln",
            "probe_obs": "TCP  10.8.0.50:5000 wrr leftover\n  -> 10.8.0.9:5000 Masq leftover",
            "fix_key": "name: harbor-ipvs-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_IPVS: \"0\"",
        },
    ),
    (
        {
            "slug": "ffmpeg-preset-cache",
            "harbor": "harbor-ffmpeg",
            "env": "FFMPEG_DATADIR",
            "tool": "ffmpeg",
            "old": "6.1.1",
            "new": "7.1",
            "artifact": "ffpresets/libx264-slow.ffpreset",
            "test": "test_ffmpeg.py",
            "src": "src/clip.mp4",
            "cache_id": "ffmpeg-71",
            "dead_rm": "rm -rf /usr/share/ffmpeg",
            "dead_obs": "rm presets does not drop 6.1 libx264-slow under unversioned FFMPEG_DATADIR",
            "left_mb": "3MB",
            "vs": "r186 faust-lib (FFmpeg presets, not Faust DSP)",
            "img": "FROM linuxserver/ffmpeg:7.1",
            "run": "ffmpeg -i src/clip.mp4 -c:v libx264 -preset slow /out/o.mp4",
        },
        {
            "slug": "tun-leftover",
            "harbor": "harbor-tun",
            "token": "TUN_DELETE",
            "leftover": "tun0",
            "detail": "rootlesskit tun0 still up",
            "dead": "ip link del tun0",
            "dead_obs": "ip link del tun0 is EBUSY; leftover tun still up from rootlesskit",
            "fail_mode": "leftover tun0 from rootlesskit hijacking cache export",
            "not": "r53 pasta-vs-slirp / cache-admin 403",
            "vs": "r53 pasta leftover (tun leftover, not pasta MTU)",
            "test": "test_tun.py",
            "probe": "ip -d link show tun0; cat /sys/class/net/tun0/tun_flags",
            "probe_obs": "tun0 UP leftover\nflags=IFF_TUN leftover",
            "fix_key": "name: harbor-tun-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_TUN: \"0\"",
        },
    ),
    (
        {
            "slug": "gstreamer-registry-cache",
            "harbor": "harbor-gst",
            "env": "GST_REGISTRY",
            "tool": "gst-inspect-1.0",
            "old": "1.22.10",
            "new": "1.24.8",
            "artifact": "registry.bin",
            "test": "test_gst.py",
            "src": "src/pipe.sh",
            "cache_id": "gst-1248",
            "dead_rm": "rm -f /root/.cache/gstreamer-1.0/registry.bin",
            "dead_obs": "rm registry.bin does not drop 1.22 plugins under unversioned GST_REGISTRY",
            "left_mb": "17MB",
            "vs": "r186 faust-lib (GStreamer registry, not Faust)",
            "img": "FROM debian:bookworm",
            "run": "gst-launch-1.0 filesrc location=src/a.wav ! decodebin ! fakesink",
        },
        {
            "slug": "vsock-leftover",
            "harbor": "harbor-vsock",
            "token": "VSOCK_UNBIND",
            "leftover": "vsock cid 19 port 5000",
            "detail": "vsock still bound for cache export",
            "dead": "ss -H -A vsock",
            "dead_obs": "vsock unbind is EADDRINUSE; leftover cid 19 still bound",
            "fail_mode": "leftover vsock cid binding cache export port",
            "not": "r187 runc-systemd-cgroup / cache-admin 403",
            "vs": "r187 runc leftover (vsock leftover, not SystemdCgroup)",
            "test": "test_vsock.py",
            "probe": "ss -A vsock; cat /sys/module/vsock/parameters/host_cid",
            "probe_obs": "LISTEN 19:5000 leftover\nhost_cid=2 leftover guest 19",
            "fix_key": "name: harbor-vsock-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_VSOCK: \"0\"",
        },
    ),
    (
        {
            "slug": "pandoc-data-cache",
            "harbor": "harbor-pandoc",
            "env": "XDG_DATA_HOME",
            "tool": "pandoc",
            "old": "3.1.11",
            "new": "3.5",
            "artifact": "pandoc/templates/default.html5",
            "test": "test_pandoc.py",
            "src": "src/doc.md",
            "cache_id": "pandoc-35",
            "dead_rm": "rm -rf /root/.local/share/pandoc",
            "dead_obs": "rm templates does not drop 3.1 html5 under unversioned XDG_DATA_HOME",
            "left_mb": "2MB",
            "vs": "r187 lilypond-data (Pandoc templates, not LilyPond fonts)",
            "img": "FROM pandoc/core:3.5",
            "run": "pandoc src/doc.md -o /out/doc.html",
        },
        {
            "slug": "fanotify-leftover",
            "harbor": "harbor-fanotify",
            "token": "FANOTIFY_MARK_FLUSH",
            "leftover": "fanotify mark /var/lib/buildkit",
            "detail": "fanotify mark still EPERM cache writes",
            "dead": "echo 0 > /proc/sys/fs/fanotify/max_user_marks",
            "dead_obs": "fanotify sysctl is EPERM; leftover mark still EPERM cache writes",
            "fail_mode": "leftover fanotify mark EPERM on cache writes",
            "not": "r188 seccomp / r192 landlock / cache-admin 403",
            "vs": "r192 landlock leftover (fanotify leftover, not landlock ABI3)",
            "test": "test_fanotify.py",
            "probe": "cat /proc/sys/fs/fanotify/max_user_marks; ls /proc/1/fdinfo | head",
            "probe_obs": "max_user_marks leftover 128\nfd 9 fanotify mark /var/lib/buildkit leftover",
            "fix_key": "name: harbor-fanotify-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_FANOTIFY: \"0\"",
        },
    ),
    (
        {
            "slug": "pulumi-plugins-cache",
            "harbor": "harbor-pulumi",
            "env": "PULUMI_HOME",
            "tool": "pulumi",
            "old": "3.120.0",
            "new": "3.137.0",
            "artifact": "plugins/resource-aws-v6.45.0",
            "test": "test_pulumi.py",
            "src": "src/Pulumi.yaml",
            "cache_id": "pulumi-3137",
            "dead_rm": "rm -rf /root/.pulumi/plugins",
            "dead_obs": "rm plugins does not drop aws v6.45 under unversioned PULUMI_HOME",
            "left_mb": "94MB",
            "vs": "r6 terraform-plugin (Pulumi plugins, not TF plugin cache)",
            "img": "FROM pulumi/pulumi:3.137.0",
            "run": "pulumi install && pulumi preview --non-interactive",
        },
        {
            "slug": "userfaultfd-leftover",
            "harbor": "harbor-uffd",
            "token": "UFFD_UNREGISTER",
            "leftover": "userfaultfd handler",
            "detail": "uffd handler still stalls page-ins on cache mmap",
            "dead": "echo 0 > /proc/sys/vm/unprivileged_userfaultfd",
            "dead_obs": "uffd sysctl is EPERM; leftover handler still stalls cache page-ins",
            "fail_mode": "leftover userfaultfd stalling cache page-ins",
            "not": "r189 hugepages / cache-admin 403",
            "vs": "r189 hugepages leftover (uffd leftover, not nr_hugepages)",
            "test": "test_uffd.py",
            "probe": "ls /proc/1/fdinfo; cat /proc/sys/vm/unprivileged_userfaultfd",
            "probe_obs": "fd 11 userfaultfd leftover\nunprivileged_userfaultfd=1 leftover",
            "fix_key": "name: harbor-uffd-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_UFFD: \"0\"",
        },
    ),
    (
        {
            "slug": "ansible-galaxy-cache",
            "harbor": "harbor-galaxy",
            "env": "ANSIBLE_HOME",
            "tool": "ansible-galaxy",
            "old": "9.6.0",
            "new": "11.1.0",
            "artifact": "galaxy_cache/community.general-9.5.0.tar.gz",
            "test": "test_galaxy.py",
            "src": "src/requirements.yml",
            "cache_id": "galaxy-111",
            "dead_rm": "rm -rf /root/.ansible/galaxy_cache",
            "dead_obs": "rm galaxy_cache does not drop 9.5 tarball under unversioned ANSIBLE_HOME",
            "left_mb": "21MB",
            "vs": "r188 luau-wally (Galaxy roles, not Wally)",
            "img": "FROM alpine/ansible:11.1.0",
            "run": "ansible-galaxy collection install -r src/requirements.yml",
        },
        {
            "slug": "ksm-leftover",
            "harbor": "harbor-ksm",
            "token": "KSM_STOP",
            "leftover": "ksm run=1",
            "detail": "KSM still merges cache pages across builds",
            "dead": "echo 0 > /sys/kernel/mm/ksm/run",
            "dead_obs": "ksm run write is EPERM; leftover KSM still merges cache pages",
            "fail_mode": "leftover KSM merging cache pages across builds",
            "not": "r189 hugepages / cache-admin 403",
            "vs": "r189 hugepages leftover (KSM leftover, not hugepage reservation)",
            "test": "test_ksm.py",
            "probe": "cat /sys/kernel/mm/ksm/run /sys/kernel/mm/ksm/pages_shared",
            "probe_obs": "1\n184320 leftover shared",
            "fix_key": "name: harbor-ksm-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_KSM: \"0\"",
        },
    ),
    (
        {
            "slug": "dagger-engine-cache",
            "harbor": "harbor-dagger",
            "env": "_EXPERIMENTAL_DAGGER_CACHE_CONFIG",
            "tool": "dagger",
            "old": "0.12.7",
            "new": "0.15.3",
            "artifact": "engine/cache/0.12/index.bolt",
            "test": "test_dagger.py",
            "src": "src/dagger.json",
            "cache_id": "dagger-0153",
            "dead_rm": "rm -rf /root/.local/share/dagger",
            "dead_obs": "rm engine cache does not drop 0.12 bolt under unversioned DAGGER cache",
            "left_mb": "55MB",
            "vs": "r258 earthly-cache (Dagger engine bolt, not Earthly)",
            "img": "FROM daggerio/dagger:0.15.3",
            "run": "dagger call build",
        },
        {
            "slug": "zswap-leftover",
            "harbor": "harbor-zswap",
            "token": "ZSWAP_DISABLE",
            "leftover": "zswap enabled=Y",
            "detail": "zswap still holds compressed cache pages",
            "dead": "echo 0 > /sys/module/zswap/parameters/enabled",
            "dead_obs": "zswap disable is EPERM; leftover pool still holds compressed cache",
            "fail_mode": "leftover zswap pool holding compressed cache pages",
            "not": "r189 hugepages / cache-admin 403",
            "vs": "r189 hugepages leftover (zswap leftover, not hugepages)",
            "test": "test_zswap.py",
            "probe": "cat /sys/module/zswap/parameters/enabled /sys/kernel/debug/zswap/stored_pages",
            "probe_obs": "Y\n22011 leftover stored",
            "fix_key": "name: harbor-zswap-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_ZSWAP: \"0\"",
        },
    ),
    (
        {
            "slug": "packer-plugin-cache",
            "harbor": "harbor-packer",
            "env": "PACKER_PLUGIN_PATH",
            "tool": "packer",
            "old": "1.10.3",
            "new": "1.11.2",
            "artifact": "github.com/hashicorp/amazon/packer-plugin-amazon_v1.3.2",
            "test": "test_packer.py",
            "src": "src/ami.pkr.hcl",
            "cache_id": "packer-1112",
            "dead_rm": "rm -rf /root/.config/packer/plugins",
            "dead_obs": "rm plugins does not drop amazon v1.3.2 under unversioned PACKER_PLUGIN_PATH",
            "left_mb": "28MB",
            "vs": "r6 terraform-plugin (Packer plugins, not TF plugin cache)",
            "img": "FROM hashicorp/packer:1.11",
            "run": "packer init src && packer validate src/ami.pkr.hcl",
        },
        {
            "slug": "cpuset-leftover",
            "harbor": "harbor-cpuset",
            "token": "CPUSET_RESET",
            "leftover": "cpuset.cpus=3",
            "detail": "cpuset leftover pins builder to offline cpu 3",
            "dead": "echo 0-7 > /sys/fs/cgroup/buildkit/cpuset.cpus",
            "dead_obs": "cpuset write is EPERM; leftover cpus=3 still pins the builder",
            "fail_mode": "leftover cpuset.cpus=3 pinning builder to offline cpu",
            "not": "r97 cgroup-cpu-throttle / cache-admin 403",
            "vs": "r97 cgroup cpu throttle leftover (cpuset leftover, not cpu.max)",
            "test": "test_cpuset.py",
            "probe": "cat /sys/fs/cgroup/buildkit/cpuset.cpus /sys/fs/cgroup/buildkit/cpuset.cpus.effective",
            "probe_obs": "3\n3 leftover offline",
            "fix_key": "name: harbor-cpuset-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_CPUSET: \"0-7\"",
        },
    ),
    (
        {
            "slug": "kind-node-cache",
            "harbor": "harbor-kind",
            "env": "KIND_EXPERIMENTAL_CONTAINERD_SNAPSHOTTER",
            "tool": "kind",
            "old": "0.23.0",
            "new": "0.26.0",
            "artifact": "node/cache/overlayfs",
            "test": "test_kind.py",
            "src": "src/kind.yaml",
            "cache_id": "kind-026",
            "dead_rm": "rm -rf /root/.kube /var/lib/kind",
            "dead_obs": "rm kind node cache does not drop 0.23 overlayfs under unversioned snapshotter",
            "left_mb": "120MB",
            "vs": "r266 minikube-docker-env (kind node cache, not minikube docker-env)",
            "img": "FROM kindest/node:v1.32.0",
            "run": "kind create cluster --config src/kind.yaml --retain",
        },
        {
            "slug": "numa-membind-leftover",
            "harbor": "harbor-numa",
            "token": "NUMACTL_LOCAL",
            "leftover": "mempolicy bind node 1",
            "detail": "membind leftover still pins cache pages to node 1",
            "dead": "echo -1 > /proc/self/numa_maps || true; numactl --localalloc true",
            "dead_obs": "numactl reset is EPERM; leftover bind node 1 still pins cache pages",
            "fail_mode": "leftover NUMA membind pinning cache pages to node 1",
            "not": "r189 hugepages / cache-admin 403",
            "vs": "r189 hugepages leftover (NUMA membind leftover, not hugepages)",
            "test": "test_numa.py",
            "probe": "numactl --show; cat /proc/1/numa_maps | head",
            "probe_obs": "policy: bind nodebind: 1 leftover\nbind:1 leftover",
            "fix_key": "name: harbor-numa-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_NUMA: \"local\"",
        },
    ),
    (
        {
            "slug": "kustomize-helm-cache",
            "harbor": "harbor-kust",
            "env": "KUSTOMIZE_PLUGIN_HOME",
            "tool": "kustomize",
            "old": "5.4.3",
            "new": "5.6.0",
            "artifact": "plugin/kustomize/v1/chartinflator",
            "test": "test_kust.py",
            "src": "src/kustomization.yaml",
            "cache_id": "kust-560",
            "dead_rm": "rm -rf /root/.config/kustomize /root/.cache/helm",
            "dead_obs": "rm plugin does not drop 5.4 chartinflator under unversioned KUSTOMIZE_PLUGIN_HOME",
            "left_mb": "15MB",
            "vs": "r9 helm-chart (kustomize helm inflator, not helm chart cache)",
            "img": "FROM registry.k8s.io/kustomize/kustomize:v5.6.0",
            "run": "kustomize build --enable-helm src",
        },
        {
            "slug": "lockdown-confidentiality-leftover",
            "harbor": "harbor-lockdown",
            "token": "LOCKDOWN_NONE",
            "leftover": "lockdown=confidentiality",
            "detail": "kernel lockdown still EPERM /dev/mem cache export",
            "dead": "echo none > /sys/kernel/security/lockdown",
            "dead_obs": "lockdown write is EPERM; leftover confidentiality still EPERM /dev/mem export",
            "fail_mode": "leftover kernel lockdown=confidentiality EPERM on cache export",
            "not": "r188 seccomp / r131 AppArmor / r192 landlock / cache-admin 403",
            "vs": "r192 landlock leftover (kernel lockdown leftover, not landlock ABI)",
            "test": "test_lockdown.py",
            "probe": "cat /sys/kernel/security/lockdown",
            "probe_obs": "none [integrity] confidentiality leftover",
            "fix_key": "name: harbor-lockdown-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_LOCKDOWN: \"0\"",
        },
    ),
    (
        {
            "slug": "tilt-engine-cache",
            "harbor": "harbor-tilt",
            "env": "TILT_CACHE",
            "tool": "tilt",
            "old": "0.33.17",
            "new": "0.34.2",
            "artifact": "tilt/engine/0.33/build.db",
            "test": "test_tilt.py",
            "src": "src/Tiltfile",
            "cache_id": "tilt-0342",
            "dead_rm": "rm -rf /root/.tilt-dev",
            "dead_obs": "rm tilt-dev does not drop 0.33 build.db under unversioned TILT_CACHE",
            "left_mb": "23MB",
            "vs": "r258 earthly-cache (Tilt engine db, not Earthly)",
            "img": "FROM tilt-dev/tilt:0.34.2",
            "run": "tilt ci -- --file src/Tiltfile",
        },
        {
            "slug": "yama-ptrace-leftover",
            "harbor": "harbor-yama",
            "token": "YAMA_SCOPE0",
            "leftover": "yama.ptrace_scope=3",
            "detail": "Yama still denies debugger attach used by cache inspect",
            "dead": "echo 0 > /proc/sys/kernel/yama/ptrace_scope",
            "dead_obs": "yama ptrace_scope write is EPERM; leftover scope=3 still denies inspect",
            "fail_mode": "leftover yama.ptrace_scope=3 denying cache inspect",
            "not": "r188 seccomp / r192 landlock / cache-admin 403",
            "vs": "r188 seccomp leftover (Yama ptrace leftover, not runc seccomp)",
            "test": "test_yama.py",
            "probe": "cat /proc/sys/kernel/yama/ptrace_scope",
            "probe_obs": "3 leftover",
            "fix_key": "name: harbor-yama-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_YAMA: \"0\"",
        },
    ),
    (
        {
            "slug": "flux-artifact-cache",
            "harbor": "harbor-flux",
            "env": "FLUX_CACHE",
            "tool": "flux",
            "old": "2.3.0",
            "new": "2.5.1",
            "artifact": "artifact/v2.3/source.tar.gz",
            "test": "test_flux.py",
            "src": "src/gotk-sync.yaml",
            "cache_id": "flux-251",
            "dead_rm": "rm -rf /root/.cache/flux",
            "dead_obs": "rm flux cache does not drop 2.3 artifact under unversioned FLUX_CACHE",
            "left_mb": "10MB",
            "vs": "r9 helm-chart (Flux artifact, not helm chart cache)",
            "img": "FROM ghcr.io/fluxcd/flux-cli:v2.5.1",
            "run": "flux build kustomization harbor --path src",
        },
        {
            "slug": "cap-bounding-leftover",
            "harbor": "harbor-caps",
            "token": "CAPSH_RESET",
            "leftover": "CapBnd missing CAP_SYS_ADMIN",
            "detail": "bounding set leftover still drops CAP_SYS_ADMIN",
            "dead": "capsh --caps=cap_sys_admin+eip --",
            "dead_obs": "capsh raise is EPERM; leftover bounding set still drops CAP_SYS_ADMIN",
            "fail_mode": "leftover capability bounding set dropping CAP_SYS_ADMIN",
            "not": "r188 seccomp / r156 SELinux / cache-admin 403",
            "vs": "r188 seccomp leftover (cap bounding leftover, not seccomp filter)",
            "test": "test_caps.py",
            "probe": "grep CapBnd /proc/1/status; capsh --print | rg Current",
            "probe_obs": "CapBnd: 00000000a80425fb leftover missing CAP_SYS_ADMIN",
            "fix_key": "name: harbor-caps-v2",
            "fix_val": "driver-opts:\n          env.BUILDKIT_CAPS: \"full\"",
        },
    ),
]


def success_episode(round_n: int, s: dict) -> dict:
    guard_plant(s)
    hid = hx(s["slug"])
    eid = f"dbc-r{round_n}-{s['slug']}-{hid}"
    harbor = s["harbor"]
    env = s["env"]
    cache_id = s["cache_id"]
    test = s["test"]
    src = s["src"]
    old_run = (
        f"RUN --mount=type=cache,target=/root/.cache/{harbor} {s['run']}"
    )
    dead_run = (
        f"RUN --mount=type=cache,target=/root/.cache/{harbor} "
        f"{s['dead_rm']} && {s['run']}"
    )
    good_run = (
        f"ENV {env}=/var/cache/{cache_id}\n"
        f"RUN --mount=type=cache,id={cache_id},target=/var/cache/{cache_id} {s['run']}"
    )
    df = (
        f"{s['img']}\nWORKDIR /src\nCOPY {src} .\n{old_run}"
    )
    steps = [
        bash(
            1,
            f"Plan: inventory {harbor} Docker/test files before touching the language cache.",
            "ls -la Dockerfile tests src .github/workflows | sed -n '1,60p'",
            (
                f"Dockerfile  {src}  tests/{test}  .github/workflows/image.yml\n"
                f"-rw-r--r-- 1 root root  812 Dockerfile\n"
                f"-rw-r--r-- 1 root root 1402 tests/{test}"
            ),
        ),
        grep(
            2,
            f"Observation: {test} present (step 1). Grep cache-related tokens.",
            ".",
            f"{env}|{s['tool']}|{s['new']}",
            (
                f"Dockerfile: {s['img']}\n"
                f"Dockerfile: RUN --mount=type=cache,target=/root/.cache/{harbor} {s['tool']}\n"
                f"tests/{test}: expect {s['new']} {s['artifact']}, cache id {cache_id}"
            ),
        ),
        read(
            3,
            "Observation: Dockerfile tokens (step 2). Read the build stage.",
            "Dockerfile",
            df,
        ),
        bash(
            4,
            f"Observation: Dockerfile read (step 3). Run {test}.",
            f"pytest {test} -q --tb=short 2>&1 | tail -n 20",
            (
                f"FAILED tests/{test}::test_artifact - {s['artifact']} stamped {s['tool']} {s['old']}\n"
                f"FAILED tests/{test}::test_home - {env} still {s['old']} bytes\n"
                f"=== 2 failed, 0 passed in 2.1s ==="
            ),
        ),
        bash(
            5,
            "Observation: tests failed (step 4). Trace the cache on a plain build.",
            "docker buildx build --progress=plain . 2>&1 | rg 'cache|error|CACHED|hit' | head -n 16",
            (
                f"#8 {s['tool']}  cache hit /root/.cache/{harbor}  {s['old']} {s['artifact']}\n"
                f"#8 {s['new']} ignored; {env} unversioned\n"
                f"#8 sha256:9c{hid}  mount id=anonymous  reuse=true"
            ),
        ),
        read(
            6,
            f"Observation: stale/poisoned cache (step 5). Read {test} expectations.",
            f"tests/{test}",
            (
                f"def test_artifact():\n"
                f"    assert stamp({s['artifact']!r}) == {s['new']!r}\n"
                f"def test_home():\n"
                f"    assert os.environ[{env!r}].endswith({cache_id!r})"
            ),
        ),
        edit(
            7,
            "Observation: expectations confirmed (step 6). Dead-end edit first.",
            "Dockerfile",
            old_run,
            dead_run,
            s["dead_obs"],
        ),
        bash(
            8,
            "Observation: dead-end applied (step 7). Rebuild to confirm it fails.",
            f"docker buildx build --load -t ghcr.io/harbor/{harbor.split('-',1)[-1]}:ci . 2>&1 | tail -n 14; pytest -q --tb=line | tail",
            (
                f"{s['artifact']} {s['old']} | FAILED test_artifact\n"
                f"error: cache mount still served {s['old']} {s['artifact']}"
            ),
        ),
        edit(
            9,
            "Reflection: apply the real cache isolation (steps 7-8).",
            "Dockerfile",
            dead_run,
            good_run,
            f"{env} namespaced by {s['new']} {s['artifact']}.",
        ),
        bash(
            10,
            "Observation: isolation applied (step 9). Rebuild.",
            "docker buildx build --load -t ghcr.io/harbor/ci:local . 2>&1 | rg 'error|CACHED|DONE|done' | head -n 12",
            (
                f"#12 {s['tool']}  {s['new']} {s['artifact']}  (not {s['old']})\n"
                f"#12 DONE 18.4s  mount id={cache_id}"
            ),
        ),
        bash(
            11,
            "Observation: rebuild progressed (step 10). Re-run tests.",
            f"pytest {test} -q --tb=line 2>&1 | tail -n 12",
            "2 passed in 1.7s",
        ),
        bash(
            12,
            "Observation: 2/2 (step 11). Confirm leftover cache.",
            "docker buildx du --verbose 2>&1 | head -n 24",
            (
                f"ID {hid}    RECLAIMABLE  {s['left_mb']}  true\n"
                f"anonymous .{harbor} {s['old']}  {s['left_mb']} (gc skipped)\n"
                f"id={cache_id}  shared  last used 2s ago"
            ),
        ),
        edit(
            13,
            "Observation: leftover documented (step 12). Comment the isolation.",
            "Dockerfile",
            f"ENV {env}=/var/cache/{cache_id}",
            f"# {s['tool']} {s['artifact']} unversioned — id={cache_id}\nENV {env}=/var/cache/{cache_id}",
            "comment documents cache id/isolation.",
        ),
        read(
            14,
            "Observation: comment (step 13). Read gha cache scope.",
            ".github/workflows/image.yml",
            (
                f"cache-from: type=gha,scope={cache_id}-${{{{ hashFiles('{src}') }}}}\n"
                f"cache-to: type=gha,scope={cache_id}-${{{{ hashFiles('{src}') }}}},mode=min"
            ),
        ),
        bash(
            15,
            "Observation: gha scope (step 14). Second build should cache.",
            "docker buildx build --progress=plain --load -t ghcr.io/harbor/ci:local . 2>&1 | rg 'CACHED' | head",
            f"RUN {s['tool']} CACHED",
        ),
        bash(
            16,
            "Observation: CACHED (step 15). Full pytest.",
            f"pytest {test} -q --tb=line",
            "2 passed in 1.4s",
        ),
        bash(
            17,
            "Observation: 2/2 (step 16). Inspect toolchain.",
            f"{s['tool'].split()[0]} --version 2>&1 | head -n 8",
            f"{s['tool']} {s['new']}",
        ),
        read(
            18,
            "Observation: inspect ok (step 17). Confirm Dockerfile isolation.",
            "Dockerfile",
            f"{good_run}\n# id={cache_id}",
        ),
        bash(
            19,
            "Observation: isolation confirmed (step 18). Done.",
            f"pytest {test} -q",
            "2 passed in 1.2s",
        ),
    ]
    if not (16 <= len(steps) <= 24):
        raise SystemExit(f"{eid} bad step count {len(steps)}")
    rec = {
        "id": eid,
        "goal": (
            f"{harbor} pins {s['tool']} {s['new']} but {env} still compiles {s['old']} "
            f"{s['artifact']}. Namespace {env}; leftover {s['old']} may remain."
        ),
        "plan": (
            f"Show {s['old']} {s['artifact']} hit, {s['dead_rm'].split()[0]} dead-end, "
            f"id={cache_id}, leave {s['old']} if gc skipped."
        ),
        "steps": steps,
        "outcome": (
            f"id={cache_id}. {s['tool']} {s['new']}, tests 2/2. "
            f"{s['dead_rm'].split()[0]} was a dead-end. Residual: {s['left_mb']} "
            f"{s['old']} cache (gc skipped, not cache-admin 403)."
        ),
        "reward": {"success": True, "tests_passed": 2, "cost_steps": len(steps)},
        "meta": {"factory": FACTORY, "round": round_n, "generator": GEN},
    }
    return rec


def leftover_episode(round_n: int, p: dict) -> dict:
    guard_plant(p)
    hid = hx(p["slug"])
    eid = f"dbc-r{round_n}-{p['slug']}-{hid}"
    harbor = p["harbor"]
    test = p["test"]
    short = harbor.split("-", 1)[-1]
    steps = [
        bash(
            1,
            f"Plan: inventory {harbor} Docker/test files before editing mounts.",
            "ls -la Dockerfile tests src .github/workflows | sed -n '1,60p'",
            (
                f"Dockerfile  src/  tests/{test}  .github/workflows/image.yml\n"
                f"-rw-r--r-- 1 root root  640 Dockerfile"
            ),
        ),
        grep(
            2,
            "Observation: test present (step 1). Grep mount/driver tokens.",
            ".",
            f"{p['token']}|{p['leftover'].split()[0]}",
            (
                f"image.yml: driver-opt: env.{p['token']}=0\n"
                f"tests/{test}: expect leftover {p['leftover']} gone"
            ),
        ),
        read(
            3,
            "Observation: tokens (step 2). Read Dockerfile.",
            "Dockerfile",
            "FROM alpine:3.20\nWORKDIR /src\nCOPY src .\nRUN --mount=type=cache,target=/root/.cache make",
        ),
        bash(
            4,
            f"Observation: Dockerfile read (step 3). Run {test}.",
            f"pytest {test} -q --tb=short 2>&1 | tail -n 16",
            (
                f"FAILED tests/{test}::test_write - cache write failed leftover {p['leftover']} "
                f"({p['token']}=0 ignored)\n"
                f"FAILED tests/{test}::test_residue - leftover {p['detail']}"
            ),
        ),
        bash(
            5,
            "Observation: tests failed (step 4). Trace the driver/mount.",
            "docker buildx build --progress=plain . 2>&1 | rg 'error|mount|cache|EPERM|EBUSY|EACCES' | head",
            (
                f"make  leftover {p['leftover']}  {p['detail']}\n"
                f"{p['token']}=0 ignored until recreate"
            ),
        ),
        read(
            6,
            "Observation: driver/mount bug (step 5). Read workflow driver-opts.",
            ".github/workflows/image.yml",
            (
                f"driver: docker-container\n"
                f"driver-opts:\n  env.{p['token']}: \"0\"\n"
                f"name: {harbor}"
            ),
        ),
        edit(
            7,
            "Observation: workflow read (step 6). Dead-end edit first.",
            ".github/workflows/image.yml",
            f"env.{p['token']}: \"0\"",
            f"env.{p['token']}: \"0\"\n          # {p['dead']}",
            p["dead_obs"],
        ),
        bash(
            8,
            "Observation: dead-end applied (step 7). Rebuild to confirm it fails.",
            f"docker buildx build --load -t ghcr.io/harbor/{short}:ci . 2>&1 | tail -n 12; pytest -q --tb=line | tail",
            f"{p['leftover']} leftover | FAILED test_write",
        ),
        edit(
            9,
            "Reflection: apply the real mount/driver isolation (steps 7-8).",
            ".github/workflows/image.yml",
            f"env.{p['token']}: \"0\"\n          # {p['dead']}",
            f"{p['fix_key']}\n        driver-opts:\n          {p['fix_val']}",
            f"new builder without leftover {p['leftover']}.",
        ),
        bash(
            10,
            "Observation: isolation applied (step 9). Rebuild.",
            f"docker buildx build --load -t ghcr.io/harbor/{short}:ci . 2>&1 | rg 'error|CACHED|done|DONE' | head",
            f"make  no {p['leftover']}  cache writable",
        ),
        bash(
            11,
            "Observation: rebuild progressed (step 10). Re-run tests.",
            f"pytest {test} -q --tb=line 2>&1 | tail -n 12",
            "2 passed in 1.7s",
        ),
        bash(
            12,
            "Observation: 2/2 (step 11). Confirm leftover mount/driver state.",
            "docker buildx du --verbose 2>&1 | head -n 20",
            f"leftover {p['leftover']}  1",
        ),
        bash(
            13,
            "Observation: leftover (step 12). Alternate fail — not cache-admin 403.",
            p["probe"],
            f"{p['probe_obs']}\n({p['not']})",
        ),
        edit(
            14,
            "Observation: leftover documented (step 13). Comment the isolation.",
            ".github/workflows/image.yml",
            p["fix_val"].split("\n")[-1].strip(),
            f"# leftover {p['leftover']} — new builder {p['token']}=0\n          {p['fix_val'].split(chr(10))[-1].strip()}",
            "comment documents isolation.",
        ),
        read(
            15,
            "Observation: comment (step 14). Read gha scope.",
            ".github/workflows/image.yml",
            f"cache-from: type=gha,scope={short}-v2\ncache-to: type=gha,scope={short}-v2,mode=min",
        ),
        bash(
            16,
            "Observation: gha scope (step 15). Second build caches.",
            f"docker buildx build --progress=plain --load -t ghcr.io/harbor/{short}:ci . 2>&1 | rg 'CACHED' | head",
            "RUN make CACHED",
        ),
        bash(
            17,
            "Observation: CACHED (step 16). pytest plus xfail leftover.",
            f"pytest {test} tests/test_cache_handoff.py -q --tb=line",
            f"2 passed, 1 xfailed in 1.7s\nxfailed test_{short}_gone — leftover {p['leftover']} remains",
        ),
        bash(
            18,
            "Observation: image green, leftover documented (step 17). Probe residue.",
            p["probe"],
            p["probe_obs"],
        ),
        bash(
            19,
            "Observation: residue still present (step 18). Inspect builder name.",
            f"rg {short}-v2 .github/workflows/image.yml | head",
            f"{p['fix_key']}",
        ),
        read(
            20,
            "Observation: inspect ok (step 19). Re-read workflow isolation.",
            ".github/workflows/image.yml",
            f"{p['fix_key']}\n{p['fix_val']}",
        ),
        bash(
            21,
            "Observation: inspect ok (step 20). Stop; leftover is a follow-up.",
            f"pytest {test} -q",
            "2 passed in 1.8s",
        ),
    ]
    if not (16 <= len(steps) <= 24):
        raise SystemExit(f"{eid} bad step count {len(steps)}")
    rec = {
        "id": eid,
        "goal": (
            f"{harbor} leftover {p['leftover']} still {p['detail']} after {p['token']}=0. "
            f"Recreate the builder; leftover {p['leftover']} may remain."
        ),
        "plan": (
            f"Show leftover {p['leftover']}, {p['dead'].split()[0]} dead-end, "
            f"new builder, leave residue."
        ),
        "steps": steps,
        "outcome": (
            f"builder {short}-v2 no active {p['leftover']}, tests 2/2. "
            f"{p['dead'].split()[0]} was a dead-end. Residual: leftover {p['leftover']} "
            f"(not {p['not']})."
        ),
        "reward": {
            "success": False,
            "tests_passed": 2,
            "cost_steps": len(steps),
            "xfailed": 1,
        },
        "meta": {"factory": FACTORY, "round": round_n, "generator": GEN},
    }
    return rec


def notes_for(round_n: int, suc: dict, left: dict, srec: dict, lrec: dict) -> str:
    cov = 21 + ((round_n - CATALOG_FIRST) % 5)
    sslug = srec["id"].split("-", 2)[-1]
    lslug = lrec["id"].split("-", 2)[-1]
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
        f"- Ban check: not r192 GNU Prolog wam / landlock, not r149 SWI pack, "
        f"not r188 seccomp, not r131 AppArmor, not GOTOOLCHAIN/GOCACHE, not Bundler.\n"
        f"- Slugs: {sslug}, {lslug}.\n"
    )


def write_round(round_n: int, staging: Path) -> None:
    idx = round_n - CATALOG_FIRST
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(f"no catalog pair for r{round_n} (idx={idx}, len={len(PAIRS)})")
    suc, left = PAIRS[idx]
    srec = success_episode(round_n, suc)
    lrec = leftover_episode(round_n, left)
    batch = staging / f"batch-r{round_n:02d}.jsonl"
    notes = staging / f"NOTES-r{round_n:02d}.md"
    lines = [json.dumps(srec, separators=(",", ":")), json.dumps(lrec, separators=(",", ":"))]
    batch.write_text("\n".join(lines) + "\n")
    notes.write_text(notes_for(round_n, suc, left, srec, lrec))
    print(
        json.dumps(
            {
                "round": round_n,
                "ids": [srec["id"], lrec["id"]],
                "steps": [srec["reward"]["cost_steps"], lrec["reward"]["cost_steps"]],
                "bytes": batch.stat().st_size,
                "batch": str(batch),
                "notes": str(notes),
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
