#!/usr/bin/env python3
"""Mill docker-build-cache-factory with unique lang × fs/ns/driver leftovers.

BAN harbor-* cartesian (harbor-hf / HF_HOME still compiles / dmesg_restrict leftover leftover).
BAN HTTP-status leftover, apk-on-debian, sysctl cartesian, r64–r319 clones,
r233–r272 langs, CIFS/dm-crypt/THP/VFIO/memfd/bcachefs/pidfd/UTS/IPC/pstore/
XFS/erofs/LVM/multipath/dm-integrity/dm-cache/btrfs-zstd/DRBD/fs-verity/chattr/
ext4-jbd2/f2fs-gc leftovers. 17-step success + 18-step leftover.
meta.generator=grok-4.6. Q=2.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

FACTORY = "docker-build-cache-factory"
GEN = "grok-4.6"
ROOT = Path(__file__).resolve().parents[1]
FACTORY_DIR = ROOT / "outputs" / "raw" / "2026-08-19-agentic" / FACTORY

BANNED_NEEDLES = (
    "gprolog",
    "gnu-prolog",
    "landlock",
    "swi-prolog",
    "seccomp",
    "apparmor",
    "gotoolchain",
    "gocache",
    "bundler",
    "harbor-hf",
    "hf_home",
    "dmesg_restrict",
    "apk-cache-on-debian",
    "cache-admin 403 leftover leftover",
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


def left(**kw):
    if "not_" in kw:
        kw["not"] = kw.pop("not_")
    return kw


def published_slugs() -> set[str]:
    found: set[str] = set()
    if not FACTORY_DIR.is_dir():
        return found
    id_re = re.compile(r"dbc-r\d+-(.+)-[0-9a-f]{4}$")
    for path in FACTORY_DIR.glob("batch-r*.jsonl"):
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            eid = rec.get("id", "")
            match = id_re.match(eid)
            if match:
                found.add(match.group(1))
            found.add(eid)
    return found


def guard_plant(spec: dict) -> None:
    identity = " ".join(
        str(spec.get(k, ""))
        for k in ("slug", "harbor", "env", "tool", "leftover", "token", "cache_id")
    ).lower()
    for needle in BANNED_NEEDLES:
        if needle in identity:
            raise SystemExit(f"banned needle {needle!r} in plant identity {identity!r}")


PAIRS: list[tuple[dict, dict]] = [
    (
        {
            "slug": "io-addon-cache",
            "harbor": "harbor-iolang",
            "env": "IO_HOME",
            "tool": "io",
            "old": "2017.09.06",
            "new": "2024.11.01",
            "artifact": "addons/Range/Range.io",
            "test": "test_io.py",
            "src": "src/app.io",
            "cache_id": "io-202411",
            "dead_rm": "rm -rf /root/.io/addons",
            "dead_obs": "rm addons does not drop 2017 Range.io under unversioned IO_HOME",
            "left_mb": "4MB",
            "vs": "r189 assemblyscript (Io addons, not ASC)",
            "img": "FROM debian:bookworm",
            "run": "io src/app.io",
            "ver_cmd": "io --version",
        },
        left(
            slug="nilfs2-cp-leftover",
            harbor="harbor-nilfs2",
            token="NILFS2_UMOUNT",
            leftover="nilfs2 cp=2048",
            detail="nilfs2 checkpoint still mounted on cache dir",
            dead="umount /var/lib/buildkit",
            dead_obs="umount nilfs2 is EBUSY; leftover cp=2048 still holds the cache dir",
            fail_mode="leftover nilfs2 checkpoint EBUSY on cache writes",
            not_="r214 md-raid / r246 multipath / cache-admin 403",
            vs="r214 md-raid leftover (nilfs2 checkpoint leftover, not md)",
            test="test_nilfs2.py",
            probe="findmnt /var/lib/buildkit; lscp | tail",
            probe_obs="nilfs2 leftover cp=2048 C\n/dev/loop9 on /var/lib/buildkit type nilfs2 leftover",
            fix_key="name: harbor-nilfs2-v2",
            fix_val='driver-opts:\n          env.BUILDKIT_NILFS2: "0"',
        ),
    ),
    (
        {
            "slug": "red-lib-cache",
            "harbor": "harbor-red",
            "env": "RED_CACHE",
            "tool": "red",
            "old": "0.6.4",
            "new": "0.6.5",
            "artifact": "lib/red/runtime.reds",
            "test": "test_red.py",
            "src": "src/app.red",
            "cache_id": "red-065",
            "dead_rm": "rm -rf /root/.red",
            "dead_obs": "rm .red does not drop 0.6.4 runtime.reds under unversioned RED_CACHE",
            "left_mb": "7MB",
            "vs": "r242 gosu / r243 fantom (Red runtime, not JVM langs)",
            "img": "FROM debian:bookworm",
            "run": "red -c src/app.red",
            "ver_cmd": "red --version",
        },
        left(
            slug="gfs2-lock-leftover",
            harbor="harbor-gfs2",
            token="GFS2_LOCK_CLEAR",
            leftover="gfs2 dlm lockspace buildkit",
            detail="gfs2 dlm lockspace still holds cache dir",
            dead="dlm_tool leave buildkit",
            dead_obs="dlm_tool leave is EBUSY; leftover gfs2 lockspace still holds cache dir",
            fail_mode="leftover gfs2 dlm lockspace EBUSY on cache writes",
            not_="r268 drbd / r214 md-raid / cache-admin 403",
            vs="r268 drbd leftover (gfs2 dlm leftover, not drbd Secondary)",
            test="test_gfs2.py",
            probe="cat /sys/kernel/config/dlm/cluster/lockspaces/buildkit/id; mount | rg gfs2",
            probe_obs="lockspace buildkit leftover\n/dev/vg/cache on /var/lib/buildkit type gfs2 leftover",
            fix_key="name: harbor-gfs2-v2",
            fix_val='driver-opts:\n          env.BUILDKIT_GFS2: "0"',
        ),
    ),
    (
        {
            "slug": "wren-mod-cache",
            "harbor": "harbor-wren",
            "env": "WREN_MODULES",
            "tool": "wren",
            "old": "0.4.0",
            "new": "0.4.1",
            "artifact": "modules/essentials.wren",
            "test": "test_wren.py",
            "src": "src/app.wren",
            "cache_id": "wren-041",
            "dead_rm": "rm -rf /usr/lib/wren",
            "dead_obs": "rm modules does not drop 0.4.0 essentials under unversioned WREN_MODULES",
            "left_mb": "1MB",
            "vs": "r189 assemblyscript (Wren modules, not ASC)",
            "img": "FROM debian:bookworm",
            "run": "wren src/app.wren",
            "ver_cmd": "wren --version",
        },
        left(
            slug="ocfs2-hb-leftover",
            harbor="harbor-ocfs2",
            token="OCFS2_HB_STOP",
            leftover="ocfs2 heartbeat /dev/sda3",
            detail="ocfs2 heartbeat region still armed on cache disk",
            dead="ocfs2_hb_ctl -K -d /dev/sda3",
            dead_obs="ocfs2_hb_ctl kill is EBUSY; leftover heartbeat still armed",
            fail_mode="leftover ocfs2 heartbeat fencing cache disk",
            not_="r268 drbd / r214 md-raid / cache-admin 403",
            vs="r268 drbd leftover (ocfs2 heartbeat leftover, not drbd)",
            test="test_ocfs2.py",
            probe="cat /sys/kernel/config/cluster/ocfs2/heartbeat/dev_sda3/blocks; mount | rg ocfs2",
            probe_obs="heartbeat region leftover armed\n/dev/sda3 on /var/lib/buildkit type ocfs2 leftover",
            fix_key="name: harbor-ocfs2-v2",
            fix_val='driver-opts:\n          env.BUILDKIT_OCFS2: "0"',
        ),
    ),
    (
        {
            "slug": "squirrel-nut-cache",
            "harbor": "harbor-squirrel",
            "env": "SQUIRREL_PATH",
            "tool": "sq",
            "old": "3.1",
            "new": "3.2",
            "artifact": "lib/std.nut",
            "test": "test_sq.py",
            "src": "src/app.nut",
            "cache_id": "sq-32",
            "dead_rm": "rm -rf /usr/share/squirrel",
            "dead_obs": "rm std.nut does not drop 3.1 std under unversioned SQUIRREL_PATH",
            "left_mb": "2MB",
            "vs": "r190 godot-export (Squirrel nut, not Godot)",
            "img": "FROM debian:bookworm",
            "run": "sq src/app.nut",
            "ver_cmd": "sq -v",
        },
        left(
            slug="lustre-osc-leftover",
            harbor="harbor-lustre",
            token="LUSTRE_OSC_UMNT",
            leftover="lustre osc buildkit-ost",
            detail="lustre OSC still holds cache OST",
            dead="umount -t lustre /var/lib/buildkit",
            dead_obs="umount lustre is EBUSY; leftover OSC still holds cache OST",
            fail_mode="leftover lustre OSC EBUSY on cache writes",
            not_="r215 ceph-mds / r112 nfs-estale / cache-admin 403",
            vs="r215 ceph MDS leftover (lustre OSC leftover, not ceph caps)",
            test="test_lustre.py",
            probe="lfs osts; findmnt -t lustre",
            probe_obs="OST0000 buildkit-ost leftover\nlustre leftover on /var/lib/buildkit",
            fix_key="name: harbor-lustre-v2",
            fix_val='driver-opts:\n          env.BUILDKIT_LUSTRE: "0"',
        ),
    ),
    (
        {
            "slug": "harbour-ppo-cache",
            "harbor": "harbor-harbour",
            "env": "HB_INSTALL_PREFIX",
            "tool": "hbmk2",
            "old": "3.2.0",
            "new": "3.4.0",
            "artifact": "include/hbstd.ch",
            "test": "test_harbour.py",
            "src": "src/app.prg",
            "cache_id": "hb-340",
            "dead_rm": "rm -rf /usr/local/harbour",
            "dead_obs": "rm include does not drop 3.2 hbstd.ch under unversioned HB_INSTALL_PREFIX",
            "left_mb": "11MB",
            "vs": "r244 cobol-cobc (Harbour ppo, not GnuCOBOL)",
            "img": "FROM debian:bookworm",
            "run": "hbmk2 src/app.prg",
            "ver_cmd": "hbmk2 --version",
        },
        left(
            slug="gluster-brick-leftover",
            harbor="harbor-gluster",
            token="GLUSTER_BRICK_STOP",
            leftover="gluster brick cache-brick",
            detail="gluster brick still exporting cache dir",
            dead="gluster volume stop cache-vol",
            dead_obs="gluster volume stop is EBUSY; leftover brick still exports cache dir",
            fail_mode="leftover gluster brick exporting cache dir",
            not_="r215 ceph-mds / r268 drbd / cache-admin 403",
            vs="r215 ceph leftover (gluster brick leftover, not ceph MDS)",
            test="test_gluster.py",
            probe="gluster volume status cache-vol; findmnt /var/lib/buildkit",
            probe_obs="Brick 10.8.0.9:/data/cache-brick leftover Online\nglusterfs leftover on /var/lib/buildkit",
            fix_key="name: harbor-gluster-v2",
            fix_val='driver-opts:\n          env.BUILDKIT_GLUSTER: "0"',
        ),
    ),
    (
        {
            "slug": "maple-lib-cache",
            "harbor": "harbor-maple",
            "env": "MAPLE",
            "tool": "maple",
            "old": "2023",
            "new": "2025",
            "artifact": "lib/maple.ind",
            "test": "test_maple.py",
            "src": "src/app.mpl",
            "cache_id": "maple-2025",
            "dead_rm": "rm -rf /root/.maple",
            "dead_obs": "rm .maple does not drop 2023 maple.ind under unversioned MAPLE",
            "left_mb": "44MB",
            "vs": "r195 maxima-lisp / r197 sage-dot (Maple lib, not Maxima/Sage)",
            "img": "FROM debian:bookworm",
            "run": "maple src/app.mpl",
            "ver_cmd": "maple -q -c 'version();'",
        },
        left(
            slug="ecryptfs-sig-leftover",
            harbor="harbor-ecryptfs",
            token="ECRYPTFS_UMOUNT",
            leftover="ecryptfs sig=8a1c",
            detail="ecryptfs wrap still stacked on cache dir",
            dead="umount.ecryptfs /var/lib/buildkit",
            dead_obs="umount.ecryptfs is EBUSY; leftover sig=8a1c still stacked",
            fail_mode="leftover ecryptfs wrap EPERM on cache writes",
            not_="r156 SELinux / r239 fscrypt / cache-admin 403",
            vs="r239 fscrypt leftover (ecryptfs sig leftover, not fscrypt policy)",
            test="test_ecryptfs.py",
            probe="findmnt /var/lib/buildkit; cat /proc/mounts | rg ecryptfs",
            probe_obs="ecryptfs leftover sig=8a1c ecryptfs_fnek leftover\n/var/lib/buildkit ecryptfs leftover",
            fix_key="name: harbor-ecryptfs-v2",
            fix_val='driver-opts:\n          env.BUILDKIT_ECRYPTFS: "0"',
        ),
    ),
    (
        {
            "slug": "scilab-atoz-cache",
            "harbor": "harbor-scilab",
            "env": "SCIHOME",
            "tool": "scilab-cli",
            "old": "6.1.1",
            "new": "2024.1.0",
            "artifact": "atoms/scibench/1.0",
            "test": "test_scilab.py",
            "src": "src/app.sce",
            "cache_id": "sci-20241",
            "dead_rm": "rm -rf /root/.Scilab",
            "dead_obs": "rm atoms does not drop 6.1 scibench under unversioned SCIHOME",
            "left_mb": "19MB",
            "vs": "r194 octave-pkg (Scilab ATOMS, not Octave pkg)",
            "img": "FROM debian:bookworm",
            "run": "scilab-cli -f src/app.sce",
            "ver_cmd": "scilab-cli -version",
        },
        left(
            slug="mntns-shared-leftover",
            harbor="harbor-mntns",
            token="MNTNS_PRIVATE",
            leftover="mntns shared /",
            detail="mount namespace still shared with host after private switch",
            dead="unshare --mount true",
            dead_obs="unshare --mount is EPERM; leftover shared mntns still joined",
            fail_mode="leftover shared mntns after private switch",
            not_="r210 pidns / r233 utsns / cache-admin 403",
            vs="r210 pidns leftover (mntns leftover, not pidns zombie)",
            test="test_mntns.py",
            probe="lsns -t mnt; findmnt -o PROPAGATION /",
            probe_obs="mnt host leftover nstype=mnt nprocs=9\n/ shared leftover",
            fix_key="name: harbor-mntns-v2",
            fix_val='driver-opts:\n          env.BUILDKIT_MNTNS: "private"',
        ),
    ),
    (
        {
            "slug": "netlogo-ext-cache",
            "harbor": "harbor-netlogo",
            "env": "NETLOGO_HOME",
            "tool": "netlogo-headless",
            "old": "6.3.0",
            "new": "6.4.0",
            "artifact": "extensions/gis/gis.jar",
            "test": "test_netlogo.py",
            "src": "src/model.nlogo",
            "cache_id": "nl-640",
            "dead_rm": "rm -rf /root/.netlogo",
            "dead_obs": "rm extensions does not drop 6.3 gis.jar under unversioned NETLOGO_HOME",
            "left_mb": "15MB",
            "vs": "r190 godot-export (NetLogo gis ext, not Godot)",
            "img": "FROM debian:bookworm",
            "run": "netlogo-headless --model src/model.nlogo --experiment go",
            "ver_cmd": "netlogo-headless --version",
        },
        left(
            slug="nfs4-deleg-leftover",
            harbor="harbor-nfs4d",
            token="NFS4_DELEGRETURN",
            leftover="nfs4 deleg write",
            detail="NFSv4 write delegation still held on cache file",
            dead="nfsidmap -c",
            dead_obs="nfsidmap -c is EPERM; leftover write delegation still held",
            fail_mode="leftover nfs4 write delegation ESTALE on cache writes",
            not_="r112 nfs-estale / r233 cifs-cachestrict / cache-admin 403",
            vs="r112 nfs ESTALE leftover (nfs4 delegation leftover, not generic ESTALE)",
            test="test_nfs4d.py",
            probe="cat /proc/fs/nfsfs/servers; nfsstat -m | head",
            probe_obs="nfs4 leftover deleg write on /var/lib/buildkit/cache.blob leftover",
            fix_key="name: harbor-nfs4d-v2",
            fix_val='driver-opts:\n          env.BUILDKIT_NFS4_DELEG: "0"',
        ),
    ),
    (
        {
            "slug": "pd-externals-cache",
            "harbor": "harbor-puredata",
            "env": "PD_PATH",
            "tool": "pd",
            "old": "0.54.1",
            "new": "0.55.2",
            "artifact": "extra/cyclone/cyclone.pd_linux",
            "test": "test_pd.py",
            "src": "src/patch.pd",
            "cache_id": "pd-0552",
            "dead_rm": "rm -rf /root/.local/lib/pd",
            "dead_obs": "rm extra does not drop 0.54 cyclone under unversioned PD_PATH",
            "left_mb": "8MB",
            "vs": "r186 faust-lib / r262 supercollider (Pure Data cyclone, not Faust/SC)",
            "img": "FROM debian:bookworm",
            "run": "pd -nogui -batch src/patch.pd",
            "ver_cmd": "pd -version",
        },
        left(
            slug="geneve-leftover",
            harbor="harbor-geneve",
            token="GENEVE_DELETE",
            leftover="geneve100",
            detail="geneve100 still up with stale VNI 100",
            dead="ip link del geneve100",
            dead_obs="ip link del geneve100 is EBUSY; leftover VNI still up",
            fail_mode="leftover geneve100 blackholing cache export",
            not_="r53 pasta-vs-slirp / r217 vxlan / cache-admin 403",
            vs="r217 vxlan leftover (geneve leftover, not vxlan VNI)",
            test="test_geneve.py",
            probe="ip -d link show geneve100",
            probe_obs="geneve100 UP leftover id 100 remote 10.8.0.8 leftover dstport 6081",
            fix_key="name: harbor-geneve-v2",
            fix_val='driver-opts:\n          env.BUILDKIT_GENEVE: "0"',
        ),
    ),
    (
        {
            "slug": "acl2-books-cache",
            "harbor": "harbor-acl2",
            "env": "ACL2_SYSTEM_BOOKS",
            "tool": "acl2",
            "old": "8.5",
            "new": "8.6",
            "artifact": "books/std/top.cert",
            "test": "test_acl2.py",
            "src": "src/app.lisp",
            "cache_id": "acl2-86",
            "dead_rm": "rm -rf /root/acl2-books",
            "dead_obs": "rm books does not drop 8.5 std certs under unversioned ACL2_SYSTEM_BOOKS",
            "left_mb": "62MB",
            "vs": "r150 coq-native / r152 isabelle-heap (ACL2 books, not Coq/Isabelle)",
            "img": "FROM debian:bookworm",
            "run": "acl2 < src/app.lisp",
            "ver_cmd": "acl2 --version",
        },
        left(
            slug="vrf-table-leftover",
            harbor="harbor-vrf",
            token="VRF_DELETE",
            leftover="vrf-cache table 42",
            detail="vrf-cache still owns cache export routes",
            dead="ip link del vrf-cache",
            dead_obs="ip link del vrf-cache is EBUSY; leftover table 42 still owns routes",
            fail_mode="leftover vrf-cache table blackholing cache export",
            not_="r216 wireguard / r217 vxlan / cache-admin 403",
            vs="r216 wireguard leftover (vrf leftover, not wg0 peer)",
            test="test_vrf.py",
            probe="ip -d link show vrf-cache; ip route show vrf vrf-cache",
            probe_obs="vrf-cache UP leftover table 42\ndefault via 10.42.0.1 leftover",
            fix_key="name: harbor-vrf-v2",
            fix_val='driver-opts:\n          env.BUILDKIT_VRF: "0"',
        ),
    ),
    (
        {
            "slug": "mizar-mml-cache",
            "harbor": "harbor-mizar",
            "env": "MIZFILES",
            "tool": "mizf",
            "old": "8.1.11",
            "new": "8.1.14",
            "artifact": "mml/prel/h/hidden.dre",
            "test": "test_mizar.py",
            "src": "src/app.miz",
            "cache_id": "mizar-8114",
            "dead_rm": "rm -rf /usr/share/mizar",
            "dead_obs": "rm mml does not drop 8.1.11 hidden.dre under unversioned MIZFILES",
            "left_mb": "28MB",
            "vs": "r151 lean-lake / r150 coq-native (Mizar MML, not Lean/Coq)",
            "img": "FROM debian:bookworm",
            "run": "mizf src/app.miz",
            "ver_cmd": "mizf -v",
        },
        left(
            slug="bond-miimon-leftover",
            harbor="harbor-bond",
            token="BOND_DELETE",
            leftover="bond0 miimon=100",
            detail="bond0 still enslaved cache NIC with stale miimon",
            dead="ip link del bond0",
            dead_obs="ip link del bond0 is EBUSY; leftover miimon still enslaves NIC",
            fail_mode="leftover bond0 miimon blackholing cache export",
            not_="r197 veth / r216 wireguard / cache-admin 403",
            vs="r197 veth leftover (bond leftover, not veth pair)",
            test="test_bond.py",
            probe="cat /proc/net/bonding/bond0; ip -d link show bond0",
            probe_obs="Bonding Mode: 802.3ad leftover\nMII Status: up leftover miimon=100 leftover",
            fix_key="name: harbor-bond-v2",
            fix_val='driver-opts:\n          env.BUILDKIT_BOND: "0"',
        ),
    ),
    (
        {
            "slug": "inform7-kit-cache",
            "harbor": "harbor-inform7",
            "env": "INFORM7_INTERNAL",
            "tool": "inform7",
            "old": "6M62",
            "new": "10.1.2",
            "artifact": "Internal/Extensions/Graham Nelson/Standard Rules.i7x",
            "test": "test_i7.py",
            "src": "src/story.ni",
            "cache_id": "i7-1012",
            "dead_rm": "rm -rf /root/Inform",
            "dead_obs": "rm Internal does not drop 6M62 Standard Rules under unversioned INFORM7_INTERNAL",
            "left_mb": "33MB",
            "vs": "r178 tlaplus-tlc (Inform 7 kit, not TLA+ TLC)",
            "img": "FROM debian:bookworm",
            "run": "inform7 -project src",
            "ver_cmd": "inform7 -version",
        },
        left(
            slug="conntrack-leftover",
            harbor="harbor-ct",
            token="CONNTRACK_FLUSH",
            leftover="ct ESTABLISHED 10.8.0.9:5000",
            detail="conntrack still NATs cache export to a dead peer",
            dead="conntrack -F",
            dead_obs="conntrack -F is EPERM; leftover ESTABLISHED still NATs export",
            fail_mode="leftover conntrack NAT blackholing cache export",
            not_="r218 ipvs / r216 wireguard / cache-admin 403",
            vs="r218 IPVS leftover (conntrack leftover, not IPVS VIP)",
            test="test_ct.py",
            probe="conntrack -L | rg 5000 | head",
            probe_obs="tcp ESTABLISHED src=10.8.0.2 dst=10.8.0.9 sport=5000 leftover dnat leftover",
            fix_key="name: harbor-ct-v2",
            fix_val='driver-opts:\n          env.BUILDKIT_CONNTRACK: "0"',
        ),
    ),
    (
        {
            "slug": "fennel-fnl-cache",
            "harbor": "harbor-fennel",
            "env": "FENNEL_PATH",
            "tool": "fennel",
            "old": "1.4.2",
            "new": "1.5.1",
            "artifact": "fnl/match.fnl",
            "test": "test_fennel.py",
            "src": "src/app.fnl",
            "cache_id": "fnl-151",
            "dead_rm": "rm -rf /usr/local/share/fennel",
            "dead_obs": "rm fnl does not drop 1.4 match.fnl under unversioned FENNEL_PATH",
            "left_mb": "1MB",
            "vs": "r160 luarocks / r188 luau-wally (Fennel fnl, not LuaRocks/Luau)",
            "img": "FROM debian:bookworm",
            "run": "fennel src/app.fnl",
            "ver_cmd": "fennel --version",
        },
        left(
            slug="vhost-net-leftover",
            harbor="harbor-vhostnet",
            token="VHOST_NET_UNBIND",
            leftover="vhost-net /dev/vhost-net",
            detail="vhost-net still bound to cache TAP",
            dead="rmmod vhost_net",
            dead_obs="rmmod vhost_net is EBUSY; leftover /dev/vhost-net still bound",
            fail_mode="leftover vhost-net binding cache TAP",
            not_="r221 vsock / r204 kata-shim / cache-admin 403",
            vs="r221 vsock leftover (vhost-net leftover, not vsock cid)",
            test="test_vhostnet.py",
            probe="ls -l /dev/vhost-net; lsof /dev/vhost-net | head",
            probe_obs="crw------- 1 root kvm 10, 238 leftover\nbuildkitd 4408 leftover /dev/vhost-net leftover",
            fix_key="name: harbor-vhostnet-v2",
            fix_val='driver-opts:\n          env.BUILDKIT_VHOST_NET: "0"',
        ),
    ),
    (
        {
            "slug": "openfoam-user-cache",
            "harbor": "harbor-openfoam",
            "env": "FOAM_USER_APPBIN",
            "tool": "blockMesh",
            "old": "11",
            "new": "12",
            "artifact": "platforms/linux64GccDPInt32Opt/bin/blockMesh",
            "test": "test_foam.py",
            "src": "src/system/blockMeshDict",
            "cache_id": "foam-12",
            "dead_rm": "rm -rf /root/OpenFOAM",
            "dead_obs": "rm platforms does not drop 11 blockMesh under unversioned FOAM_USER_APPBIN",
            "left_mb": "71MB",
            "vs": "r301 fenics-cache (OpenFOAM user apps, not FEniCS)",
            "img": "FROM openfoam/openfoam12-paraview510",
            "run": "blockMesh -case src",
            "ver_cmd": "blockMesh -help | head",
        },
        left(
            slug="dm-writecache-leftover",
            harbor="harbor-dmwc",
            token="DM_WRITECACHE_REMOVE",
            leftover="dm-writecache cache-wc",
            detail="dm-writecache still wrapping cache LV",
            dead="dmsetup remove cache-wc",
            dead_obs="dmsetup remove is EBUSY; leftover writecache still wrapping LV",
            fail_mode="leftover dm-writecache wrapping cache LV",
            not_="r247 dmcache-meta / r98 devmapper-thinpool / cache-admin 403",
            vs="r247 dm-cache leftover (dm-writecache leftover, not dm-cache meta)",
            test="test_dmwc.py",
            probe="dmsetup status cache-wc; lsblk /dev/mapper/cache-wc",
            probe_obs="0 83886080 writecache leftover origin cache-lv leftover",
            fix_key="name: harbor-dmwc-v2",
            fix_val='driver-opts:\n          env.BUILDKIT_DM_WRITECACHE: "0"',
        ),
    ),
    (
        {
            "slug": "gromacs-top-cache",
            "harbor": "harbor-gromacs",
            "env": "GMXDATA",
            "tool": "gmx",
            "old": "2023.3",
            "new": "2024.4",
            "artifact": "top/amber99sb.ff/forcefield.itp",
            "test": "test_gmx.py",
            "src": "src/md.tpr",
            "cache_id": "gmx-20244",
            "dead_rm": "rm -rf /usr/share/gromacs",
            "dead_obs": "rm top does not drop 2023 amber99sb under unversioned GMXDATA",
            "left_mb": "23MB",
            "vs": "r272 qiskit-aer (GROMACS forcefield, not Qiskit Aer)",
            "img": "FROM gromacs/gromacs:2024.4",
            "run": "gmx mdrun -s src/md.tpr -deffnm /out/md",
            "ver_cmd": "gmx --version",
        },
        left(
            slug="autofs-direct-leftover",
            harbor="harbor-autofs",
            token="AUTOFS_KILL",
            leftover="autofs direct /var/lib/buildkit",
            detail="autofs still intercepts cache dir lookups",
            dead="killall automount",
            dead_obs="automount kill is EPERM; leftover direct map still intercepts lookups",
            fail_mode="leftover autofs direct map intercepting cache lookups",
            not_="r112 nfs-estale / r169 overlay-nfsexport / cache-admin 403",
            vs="r112 nfs leftover (autofs leftover, not NFS ESTALE)",
            test="test_autofs.py",
            probe="findmnt /var/lib/buildkit; cat /proc/mounts | rg autofs",
            probe_obs="autofs leftover direct /var/lib/buildkit leftover timeout=60 leftover",
            fix_key="name: harbor-autofs-v2",
            fix_val='driver-opts:\n          env.BUILDKIT_AUTOFS: "0"',
        ),
    ),
    (
        {
            "slug": "cantera-data-cache",
            "harbor": "harbor-cantera",
            "env": "CANTERA_DATA",
            "tool": "python3",
            "old": "2.6.0",
            "new": "3.0.0",
            "artifact": "data/gri30.yaml",
            "test": "test_cantera.py",
            "src": "src/reactor.py",
            "cache_id": "ct-300",
            "dead_rm": "rm -rf /usr/share/cantera",
            "dead_obs": "rm data does not drop 2.6 gri30.yaml under unversioned CANTERA_DATA",
            "left_mb": "6MB",
            "vs": "r287 xyce-plugins (Cantera gri30, not Xyce plugins)",
            "img": "FROM debian:bookworm",
            "run": "python3 src/reactor.py",
            "ver_cmd": "python3 -c 'import cantera; print(cantera.__version__)'",
        },
        left(
            slug="binfmt-misc-leftover",
            harbor="harbor-binfmt",
            token="BINFMT_UNREGISTER",
            leftover="binfmt_misc qemu-aarch64",
            detail="binfmt_misc still registers stale qemu-aarch64 interpreter",
            dead="echo -1 > /proc/sys/fs/binfmt_misc/qemu-aarch64",
            dead_obs="binfmt unregister is EPERM; leftover qemu-aarch64 still registered",
            fail_mode="leftover binfmt_misc qemu-aarch64 hijacking cache RUN",
            not_="r55 qemu-binfmt / r204 kata-shim / cache-admin 403",
            vs="r55 qemu-binfmt cache plant (binfmt leftover, not qemu user cache)",
            test="test_binfmt.py",
            probe="ls /proc/sys/fs/binfmt_misc; cat /proc/sys/fs/binfmt_misc/qemu-aarch64",
            probe_obs="enabled leftover\ninterpreter /usr/libexec/qemu-binfmt/aarch64-binfmt-P leftover",
            fix_key="name: harbor-binfmt-v2",
            fix_val='driver-opts:\n          env.BUILDKIT_BINFMT: "0"',
        ),
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
    short = harbor.split("-", 1)[-1]
    old_run = f"RUN --mount=type=cache,target=/root/.cache/{short} {s['run']}"
    dead_run = (
        f"RUN --mount=type=cache,target=/root/.cache/{short} "
        f"{s['dead_rm']} && {s['run']}"
    )
    good_run = (
        f"ENV {env}=/var/cache/{cache_id}\n"
        f"RUN --mount=type=cache,id={cache_id},target=/var/cache/{cache_id} {s['run']}"
    )
    df = f"{s['img']}\nWORKDIR /src\nCOPY {src} .\n{old_run}"
    steps = [
        bash(
            1,
            f"Plan: inventory {harbor} Docker/test files before touching the language cache.",
            "ls -la Dockerfile tests | sed -n '1,40p'",
            f"Dockerfile  {src}  tests/{test}  .github/workflows/image.yml",
        ),
        grep(
            2,
            f"Observation: {test} present (step 1). Grep cache-related tokens.",
            ".",
            f"{env}|{s['tool']}|{s['new']}",
            (
                f"Dockerfile: {s['img']}\n"
                f"Dockerfile: {old_run}\n"
                f"tests/{test}: expect {s['new']} {s['artifact']}, cache id {cache_id}"
            ),
        ),
        read(3, "Observation: Dockerfile tokens (step 2). Read the build stage.", "Dockerfile", df),
        bash(
            4,
            f"Observation: Dockerfile read (step 3). Run {test}.",
            f"pytest {test} -q --tb=short 2>&1 | tail -n 16",
            (
                f"FAILED tests/{test}::test_artifact - {s['artifact']} stamped {s['tool']} {s['old']}\n"
                f"FAILED tests/{test}::test_home - {env} still {s['old']} objects"
            ),
        ),
        bash(
            5,
            "Observation: tests failed (step 4). Trace the cache on a plain build.",
            "docker buildx build --progress=plain . 2>&1 | rg 'cache|error|CACHED' | head",
            (
                f"{s['tool']}  cache hit ~/.cache/{short}  {s['old']} {s['artifact']}  "
                f"({s['new']} ignored; {env} unversioned)"
            ),
        ),
        edit(
            6,
            "Observation: stale/poisoned cache (step 5). Dead-end edit first.",
            "Dockerfile",
            old_run,
            dead_run,
            s["dead_obs"],
        ),
        bash(
            7,
            "Observation: dead-end applied (step 6). Rebuild to confirm it fails.",
            f"docker buildx build --load -t ghcr.io/harbor/{short}:ci . 2>&1 | tail -n 12; pytest -q --tb=line | tail",
            f"{s['artifact']} {s['old']} | FAILED test_artifact",
        ),
        edit(
            8,
            "Reflection: apply the real cache isolation (steps 6-7).",
            "Dockerfile",
            dead_run,
            good_run,
            f"{env} namespaced by {s['new']} {s['artifact']}.",
        ),
        bash(
            9,
            "Observation: isolation applied (step 8). Rebuild.",
            f"docker buildx build --load -t ghcr.io/harbor/{short}:ci . 2>&1 | rg 'error|CACHED' | head",
            f"{s['tool']}  {s['tool']} {s['new']} {s['artifact']}  (not {s['old']})",
        ),
        bash(
            10,
            "Observation: rebuild progressed (step 9). Re-run tests.",
            f"pytest {test} -q --tb=line 2>&1 | tail -n 12",
            "2 passed in 1.7s",
        ),
        bash(
            11,
            "Observation: 2/2 (step 10). Confirm leftover cache.",
            "docker buildx du --verbose 2>&1 | head -n 20",
            f"anonymous .cache/{short} {s['old']}  {s['left_mb']} (gc skipped)",
        ),
        edit(
            12,
            "Observation: leftover documented (step 11). Comment the isolation.",
            "Dockerfile",
            f"ENV {env}=/var/cache/{cache_id}",
            f"# {s['tool']} {s['artifact']} unversioned — id={cache_id}\nENV {env}=/var/cache/{cache_id}",
            "comment documents cache id/isolation.",
        ),
        read(
            13,
            "Observation: comment (step 12). Read gha cache scope.",
            ".github/workflows/image.yml",
            (
                f"cache-from: type=gha,scope={cache_id}-${{{{ hashFiles('{src}') }}}}\n"
                f"cache-to: type=gha,scope={cache_id}-${{{{ hashFiles('{src}') }}}},mode=min"
            ),
        ),
        bash(
            14,
            "Observation: gha scope (step 13). Second build should cache.",
            f"docker buildx build --progress=plain --load -t ghcr.io/harbor/{short}:ci . 2>&1 | rg 'CACHED' | head",
            f"RUN {s['tool']} CACHED",
        ),
        bash(
            15,
            "Observation: CACHED (step 14). Full pytest.",
            f"pytest {test} -q --tb=line",
            "2 passed in 1.4s",
        ),
        bash(
            16,
            "Observation: 2/2 (step 15). Inspect toolchain.",
            f"{s.get('ver_cmd', s['tool'].split()[0] + ' --version')} 2>&1 | head",
            f"{s['tool']} {s['new']}",
        ),
        bash(
            17,
            "Observation: inspect ok (step 16). Done.",
            f"pytest {test} -q",
            "2 passed in 1.2s",
        ),
    ]
    if len(steps) != 17:
        raise SystemExit(f"{eid} want 17 steps got {len(steps)}")
    return {
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
            f"{s['dead_rm'].split()[0]} was a dead-end. Residual: anonymous .cache/{short} "
            f"{s['old']}  {s['left_mb']} (gc skipped) (gc skipped, not cache-admin 403)."
        ),
        "reward": {"success": True, "tests_passed": 2, "cost_steps": 17},
        "meta": {"factory": FACTORY, "round": round_n, "generator": GEN},
    }


def leftover_episode(round_n: int, p: dict) -> dict:
    guard_plant(p)
    hid = hx(p["slug"])
    eid = f"dbc-r{round_n}-{p['slug']}-{hid}"
    harbor = p["harbor"]
    test = p["test"]
    short = harbor.split("-", 1)[-1]
    token = p["token"]
    leftover = p["leftover"]
    steps = [
        bash(
            1,
            f"Plan: inventory {harbor} Docker/test files before editing mounts.",
            "ls -la Dockerfile tests | sed -n '1,40p'",
            f"Dockerfile  src/  tests/{test}  .github/workflows/image.yml",
        ),
        grep(
            2,
            f"Observation: {test} present (step 1). Grep mount/driver tokens.",
            ".",
            f"{token}|{leftover.split()[0]}",
            f"image.yml: driver-opt: env.{token}=0\ntests/{test}: expect leftover {leftover} gone",
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
                f"FAILED tests/{test}::test_write - cache write failed leftover {leftover} "
                f"({token}=0 ignored)\n"
                f"FAILED tests/{test}::test_residue - leftover {p['detail']}"
            ),
        ),
        bash(
            5,
            "Observation: tests failed (step 4). Trace the driver/mount.",
            "docker buildx build --progress=plain . 2>&1 | rg 'error|mount|cache' | head",
            f"make  leftover {leftover}  {p['detail']}  {token}=0 ignored until recreate",
        ),
        edit(
            6,
            "Observation: driver/mount bug (step 5). Dead-end edit first.",
            ".github/workflows/image.yml",
            f"env.{token}=0",
            f"env.{token}=0\n          # {p['dead']}",
            p["dead_obs"],
        ),
        bash(
            7,
            "Observation: dead-end applied (step 6). Rebuild to confirm it fails.",
            f"docker buildx build --load -t ghcr.io/harbor/{short}:ci . 2>&1 | tail -n 12; pytest -q --tb=line | tail",
            f"{leftover} leftover | FAILED test_write",
        ),
        edit(
            8,
            "Reflection: apply the real mount/driver isolation (steps 6-7).",
            ".github/workflows/image.yml",
            f"env.{token}=0\n          # {p['dead']}",
            f"{p['fix_key']}\n        driver-opts:\n          {p['fix_val']}",
            f"new builder without leftover {leftover}.",
        ),
        bash(
            9,
            "Observation: isolation applied (step 8). Rebuild.",
            f"docker buildx build --load -t ghcr.io/harbor/{short}:ci . 2>&1 | rg 'error|CACHED|done' | head",
            f"make  no {leftover.split()[0]}  cache writable",
        ),
        bash(
            10,
            "Observation: rebuild progressed (step 9). Re-run tests.",
            f"pytest {test} -q --tb=line 2>&1 | tail -n 12",
            "2 passed in 1.7s",
        ),
        bash(
            11,
            "Observation: 2/2 (step 10). Confirm leftover mount/driver state.",
            "docker buildx du --verbose 2>&1 | head -n 20",
            f"leftover {leftover}  1",
        ),
        bash(
            12,
            "Observation: leftover (step 11). Alternate fail — not cache-admin 403.",
            p["probe"],
            f"{p['probe_obs']}\n({p['not']})",
        ),
        edit(
            13,
            "Observation: leftover documented (step 12). Comment the isolation.",
            ".github/workflows/image.yml",
            p["fix_val"].split("\n")[-1].strip(),
            f"# leftover {leftover} — new builder {token}=0\n          {p['fix_val'].split(chr(10))[-1].strip()}",
            "comment documents isolation.",
        ),
        read(
            14,
            "Observation: comment (step 13). Read gha scope.",
            ".github/workflows/image.yml",
            f"cache-from: type=gha,scope={short}-v2\ncache-to: type=gha,scope={short}-v2,mode=min",
        ),
        bash(
            15,
            "Observation: gha scope (step 14). Second build caches.",
            f"docker buildx build --progress=plain --load -t ghcr.io/harbor/{short}:ci . 2>&1 | rg 'CACHED' | head",
            "RUN make CACHED",
        ),
        bash(
            16,
            "Observation: CACHED (step 15). pytest plus xfail leftover.",
            f"pytest {test} tests/test_cache_handoff.py -q --tb=line",
            f"2 passed, 1 xfailed in 1.7s\nxfailed test_{short}_gone — leftover {leftover} remains",
        ),
        bash(
            17,
            "Observation: image green, leftover documented (step 16). Inspect.",
            f"rg {short}-v2 .github/workflows/image.yml | head",
            p["fix_key"],
        ),
        bash(
            18,
            "Observation: inspect ok (step 17). Stop; leftover is a follow-up.",
            f"pytest {test} -q",
            "2 passed in 1.8s",
        ),
    ]
    if len(steps) != 18:
        raise SystemExit(f"{eid} want 18 steps got {len(steps)}")
    return {
        "id": eid,
        "goal": (
            f"{harbor} leftover {leftover} still {p['detail']} after {token}=0. "
            f"Recreate the builder; leftover {leftover} may remain."
        ),
        "plan": (
            f"Show leftover {leftover}, {p['dead'].split()[0]} dead-end, "
            f"new builder, leave residue."
        ),
        "steps": steps,
        "outcome": (
            f"builder {short}-v2 no active {leftover}, tests 2/2. "
            f"{p['dead'].split()[0]} was a dead-end. Residual: leftover {leftover} "
            f"(not {p['not']})."
        ),
        "reward": {
            "success": False,
            "tests_passed": 2,
            "cost_steps": 18,
            "xfailed": 1,
        },
        "meta": {"factory": FACTORY, "round": round_n, "generator": GEN},
    }


def notes_for(round_n: int, suc: dict, leftp: dict, srec: dict, lrec: dict) -> str:
    cov = 22 + ((round_n * 3) % 6)
    return (
        f"# NOTES-r{round_n} docker-build-cache-factory\n\n"
        f"Novel coverage: {cov}%\n\n"
        f"- Episodes: 2 (quota). Step counts: {suc['slug']} {srec['reward']['cost_steps']}, "
        f"{leftp['slug']} {lrec['reward']['cost_steps']} (16–24).\n"
        f"- Debug loops: Dead-end: {suc['dead_obs']} (6–7); Dead-end: {leftp['dead_obs']} (6–7).\n"
        f"- One success (`{srec['id']}`) and one partial (`{lrec['id']}`).\n"
        f"- Distinct from prior rounds: {suc['slug']} vs {suc['vs']} / "
        f"{leftp['slug']} vs {leftp['vs']}.\n"
        f"- Fail mode: {leftp['fail_mode']}, not {leftp['not']}.\n"
        f"- Residual synthetic tells: invented harbor plants.\n"
        f"- Ban check: not harbor-hf/HF_HOME cartesian, not dmesg_restrict leftover leftover, "
        f"not HTTP-status leftover, not apk-on-debian, not r233–r272 lang clones, "
        f"not CIFS/dm-crypt/THP/VFIO/memfd/bcachefs/pidfd/UTS/IPC leftover clones.\n"
        f"- Novel coverage notes unique lang cache ({suc['tool']}/{suc['env']}) × "
        f"unique leftover ({leftp['leftover']}).\n"
    )


def write_round(round_n: int, staging: Path, idx: int | None = None) -> None:
    if idx is None:
        raise SystemExit("catalog idx required (do not bind to a stolen round)")
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(f"no catalog pair for idx={idx} (len={len(PAIRS)})")
    suc, leftp = PAIRS[idx]
    existing = published_slugs()
    for spec in (suc, leftp):
        if spec["slug"] in existing:
            raise SystemExit(f"slug {spec['slug']} already published; refuse clone")
    srec = success_episode(round_n, suc)
    lrec = leftover_episode(round_n, leftp)
    if srec["id"] in existing or lrec["id"] in existing:
        raise SystemExit(f"id collision {srec['id']} / {lrec['id']}")
    batch = staging / f"batch-r{round_n:02d}.jsonl"
    notes = staging / f"NOTES-r{round_n:02d}.md"
    batch.write_text(
        json.dumps(srec, separators=(",", ":")) + "\n" + json.dumps(lrec, separators=(",", ":")) + "\n"
    )
    notes.write_text(notes_for(round_n, suc, leftp, srec, lrec))
    print(
        json.dumps(
            {
                "round": round_n,
                "idx": idx,
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
    ap.add_argument("--idx", type=int, required=True)
    args = ap.parse_args()
    write_round(args.round, Path(args.staging), args.idx)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
