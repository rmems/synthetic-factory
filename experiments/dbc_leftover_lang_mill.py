#!/usr/bin/env python3
"""docker-build-cache leftover-lang mill.

Unique leftover langs + leftover fs/ns/driver. Not harbor-pin mill.
Not leftover×sysctl cartesian. Not r233–r450 clones. Not r322–r337 langs.
IDs: dbc-rN-<slug>-<hash> without harbor-*. meta.generator=grok-4.6.
Shape: 17-step success + 18-step leftover.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "pipelines"))

FACTORY = (
    REPO
    / "outputs"
    / "raw"
    / "2026-08-19-agentic"
    / "docker-build-cache-factory"
)
HOP_FACTORY = (
    REPO
    / "outputs"
    / "raw"
    / "2026-08-19-agentic"
    / "k8s-crashloop-factory"
)
GENERATOR = "grok-4.6"
BANNED_KEYS = ("thought", "chain_of_thought", "scratch", "inner_monologue")
SLUG_RE = re.compile(r"^dbc-r\d+-(.+?)(?:-[0-9a-f]{4})?$")
KCL_SLUG_RE = re.compile(r"^kcl-r\d+-(.+?)(?:-n2-handoff)?$")


def _h(text: str, n: int = 4) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:n]


# leftover langs: obscure toolchains not in r1–r501 harbor-pin / unique-lang catalogs
LANGS: list[dict[str, str]] = [
    {
        "slug": "racket-collects-cache",
        "lang": "racket",
        "env": "PLTCOLLECTS",
        "cmd": "raco",
        "src": "src/app.rkt",
        "artifact": "collects/racket/private/kw.rkt",
        "new": "8.15",
        "old": "8.12",
        "cid": "rkt-815",
        "test": "test_racket.py",
        "rm": "/usr/share/racket/collects",
        "vs": "r149 swi-prolog / r402 logtalk (Racket collects, not SWI pack or Logtalk library)",
    },
    {
        "slug": "bigloo-lib-cache",
        "lang": "bigloo",
        "env": "BIGLOOLIB",
        "cmd": "bigloo",
        "src": "src/app.scm",
        "artifact": "lib/bigloo/4.4h/bigloo.h",
        "new": "4.5a",
        "old": "4.4h",
        "cid": "bgl-45a",
        "test": "test_bigloo.py",
        "rm": "/usr/lib/bigloo",
        "vs": "r170 chez-so / r420 chibi-sld (Bigloo C-backend lib, not Chez .so or Chibi sld)",
    },
    {
        "slug": "kawa-jar-cache",
        "lang": "kawa",
        "env": "KAWA_HOME",
        "cmd": "kawa",
        "src": "src/app.scm",
        "artifact": "lib/kawa.jar",
        "new": "3.1.1",
        "old": "3.0",
        "cid": "kawa-311",
        "test": "test_kawa.py",
        "rm": "/usr/share/java/kawa",
        "vs": "r169 gerbil-gxc / r198 gambit-gsc (Kawa JVM Scheme jar, not Gerbil gxc or Gambit gsc)",
    },
    {
        "slug": "smlnj-heap-cache",
        "lang": "smlnj",
        "env": "SMLNJ_HOME",
        "cmd": "sml",
        "src": "src/app.sml",
        "artifact": "lib/smlnj/heap/sml.amd64-linux",
        "new": "110.99.7",
        "old": "110.99.3",
        "cid": "sml-110997",
        "test": "test_smlnj.py",
        "rm": "/usr/lib/smlnj",
        "vs": "r233 polyml-heap / r178 mlton-lib (SML/NJ heap image, not Poly/ML heap or MLton lib)",
    },
    {
        "slug": "cakeml-boot-cache",
        "lang": "cakeml",
        "env": "CAKEMLDIR",
        "cmd": "cake",
        "src": "src/app.cml",
        "artifact": "compiler/bootstrap/compilation/x64/64/cake.S",
        "new": "1535",
        "old": "1510",
        "cid": "cake-1535",
        "test": "test_cakeml.py",
        "rm": "/opt/cakeml/compiler",
        "vs": "r178 mlton-lib / r233 polyml-heap (CakeML bootstrap asm, not MLton or Poly/ML)",
    },
    {
        "slug": "hol4-state-cache",
        "lang": "hol4",
        "env": "HOLDIR",
        "cmd": "hol",
        "src": "src/app.sml",
        "artifact": "bin/hol.state",
        "new": "kananaskis-14",
        "old": "kananaskis-13",
        "cid": "hol-k14",
        "test": "test_hol4.py",
        "rm": "/opt/hol/bin",
        "vs": "r153 isabelle-heap / r141 coq-native (HOL4 hol.state, not Isabelle heap or Coq cmxs)",
    },
    {
        "slug": "beef-corlib-cache",
        "lang": "beef",
        "env": "BEEF_HOME",
        "cmd": "BeefBuild",
        "src": "src/App.bf",
        "artifact": "BeefLibs/corlib/src/String.bf",
        "new": "0.43.5",
        "old": "0.43.4",
        "cid": "beef-0435",
        "test": "test_beef.py",
        "rm": "/opt/beef/BeefLibs",
        "vs": "r205 vala-vapi / r161 freepascal-fpcunit (Beef corlib String.bf, not Vala vapi or FPC units)",
    },
    {
        "slug": "qore-module-cache",
        "lang": "qore",
        "env": "QORE_MODULE_DIR",
        "cmd": "qore",
        "src": "src/app.q",
        "artifact": "lib/qore-modules/1.14.2/mysql.qmod",
        "new": "1.16.1",
        "old": "1.14.2",
        "cid": "qore-1161",
        "test": "test_qore.py",
        "rm": "/usr/lib/qore-modules",
        "vs": "r245 tcl-teapot / r180 pike-module (Qore .qmod, not Tcl teapot or Pike modules)",
    },
    {
        "slug": "oorexx-img-cache",
        "lang": "oorexx",
        "env": "RXHOME",
        "cmd": "rexx",
        "src": "src/app.rex",
        "artifact": "bin/rexx.img",
        "new": "5.1.0",
        "old": "5.0.0",
        "cid": "orx-510",
        "test": "test_oorexx.py",
        "rm": "/usr/lib/ooRexx",
        "vs": "r271 rexx-regina / r257 spitbol-snobol (ooRexx rexx.img, not Regina Rexx or Spitbol)",
    },
    {
        "slug": "gnuapl-ws-cache",
        "lang": "gnuapl",
        "env": "APL_LIB",
        "cmd": "apl",
        "src": "src/app.apl",
        "artifact": "lib-apl/workspaces/APs",
        "new": "1.9",
        "old": "1.8",
        "cid": "apl-19",
        "test": "test_gnuapl.py",
        "rm": "/usr/lib/apl",
        "vs": "r203 apl-dyalog / r202 bqn-cbqn (GNU APL workspaces, not Dyalog APL or CBQN)",
    },
    {
        "slug": "yorick-i0-cache",
        "lang": "yorick",
        "env": "YORICK_HOME",
        "cmd": "yorick",
        "src": "src/app.i",
        "artifact": "lib/yorick/i0/std.i",
        "new": "2.2.04",
        "old": "2.2.03",
        "cid": "yor-2204",
        "test": "test_yorick.py",
        "rm": "/usr/lib/yorick",
        "vs": "r196 octave-pkg / r328 scilab-atoz (Yorick i0/std.i, not Octave pkg or Scilab ATOMS)",
    },
    {
        "slug": "gdl-pro-cache",
        "lang": "gdl",
        "env": "GDL_PATH",
        "cmd": "gdl",
        "src": "src/app.pro",
        "artifact": "src/pro/plot.pro",
        "new": "1.0.4",
        "old": "1.0.2",
        "cid": "gdl-104",
        "test": "test_gdl.py",
        "rm": "/usr/share/gnudatalanguage",
        "vs": "r353 ncl-ncarg / r452 grads-data (GDL plot.pro, not NCL NCARG or GrADS GADDIR)",
    },
    {
        "slug": "meep-scheme-cache",
        "lang": "meep",
        "env": "MEEP_DATA",
        "cmd": "meep",
        "src": "src/app.ctl",
        "artifact": "scheme/meep.scm",
        "new": "1.29.0",
        "old": "1.28.0",
        "cid": "meep-1290",
        "test": "test_meep.py",
        "rm": "/usr/share/meep",
        "vs": "r213 gnuradio-mod / r335 openfoam-user (Meep scheme/meep.scm, not GNU Radio mods or OpenFOAM)",
    },
    {
        "slug": "openems-csx-cache",
        "lang": "openems",
        "env": "OPENEMS_INSTALL",
        "cmd": "openEMS",
        "src": "src/app.py",
        "artifact": "matlab/CSXCAD/InitCSX.m",
        "new": "0.0.36",
        "old": "0.0.35",
        "cid": "ems-0036",
        "test": "test_openems.py",
        "rm": "/usr/share/openEMS",
        "vs": "r212 ngspice-cm / r441 xschem-symbols (openEMS InitCSX.m, not ngspice cm or xschem symbols)",
    },
    {
        "slug": "whiley-jar-cache",
        "lang": "whiley",
        "env": "WHILEYHOME",
        "cmd": "wyjc",
        "src": "src/app.whiley",
        "artifact": "lib/whiley-all.jar",
        "new": "0.6.1",
        "old": "0.5.9",
        "cid": "wy-061",
        "test": "test_whiley.py",
        "rm": "/opt/whiley/lib",
        "vs": "r148 dafny-boogie / r181 why3-lib (Whiley whiley-all.jar, not Dafny Boogie or Why3 lib)",
    },
    {
        "slug": "umka-std-cache",
        "lang": "umka",
        "env": "UMKA_MODULES",
        "cmd": "umka",
        "src": "src/app.um",
        "artifact": "umka/std/std.um",
        "new": "1.5.1",
        "old": "1.4.0",
        "cid": "umka-151",
        "test": "test_umka.py",
        "rm": "/usr/lib/umka",
        "vs": "r324 wren-mod / r155 koka-klib (Umka std.um, not Wren modules or Koka klib)",
    },
    {
        "slug": "nelua-std-cache",
        "lang": "nelua",
        "env": "NELUA_PATH",
        "cmd": "nelua",
        "src": "src/app.nelua",
        "artifact": "lib/nelua/std/io.nelua",
        "new": "0.2.0",
        "old": "0.1.0",
        "cid": "nelua-020",
        "test": "test_nelua.py",
        "rm": "/usr/lib/nelua",
        "vs": "r188 luau-wally / r334 fennel-fnl (Nelua std/io.nelua, not Luau wally or Fennel fnl)",
    },
    {
        "slug": "pocketlang-inc-cache",
        "lang": "pocketlang",
        "env": "PK_HOME",
        "cmd": "pocket",
        "src": "src/app.pk",
        "artifact": "include/pocketlang.h",
        "new": "0.1.0",
        "old": "0.0.9",
        "cid": "pk-010",
        "test": "test_pocketlang.py",
        "rm": "/usr/include/pocketlang",
        "vs": "r324 wren-mod / r156 janet-jpm (Pocketlang pocketlang.h, not Wren or Janet jpm)",
    },
    {
        "slug": "coalton-math-cache",
        "lang": "coalton",
        "env": "COALTON_HOME",
        "cmd": "sbcl",
        "src": "src/app.lisp",
        "artifact": "src/library/math.lisp",
        "new": "0.0.6",
        "old": "0.0.5",
        "cid": "cltn-006",
        "test": "test_coalton.py",
        "rm": "/opt/coalton/src/library",
        "vs": "r418 clasp-cmp / r199 shadow-cljs (Coalton math.lisp, not Clasp cmp or shadow-cljs)",
    },
    {
        "slug": "hamler-beam-cache",
        "lang": "hamler",
        "env": "HAMLER_HOME",
        "cmd": "hamler",
        "src": "src/App.hm",
        "artifact": "ebin/Hamler.beam",
        "new": "0.2.2",
        "old": "0.2.1",
        "cid": "hml-022",
        "test": "test_hamler.py",
        "rm": "/usr/lib/hamler/ebin",
        "vs": "r415 lfe-ebin / r014 mix-otp27 (Hamler Hamler.beam, not LFE ebin or Mix OTP)",
    },
    {
        "slug": "aliceml-mozart-cache",
        "lang": "aliceml",
        "env": "ALICE_HOME",
        "cmd": "alicec",
        "src": "src/app.aml",
        "artifact": "share/alice/lib/system/Config.alc",
        "new": "1.4",
        "old": "1.3",
        "cid": "alice-14",
        "test": "test_aliceml.py",
        "rm": "/usr/share/alice",
        "vs": "r254 oz-mozart / r233 polyml-heap (Alice ML Config.alc, not Oz Mozart or Poly/ML)",
    },
    {
        "slug": "mosml-lib-cache",
        "lang": "mosml",
        "env": "MOSMLLIB",
        "cmd": "mosmlc",
        "src": "src/app.sml",
        "artifact": "lib/mosml/Int.ui",
        "new": "2.10.1",
        "old": "2.10.0",
        "cid": "mos-2101",
        "test": "test_mosml.py",
        "rm": "/usr/lib/mosml",
        "vs": "r233 polyml-heap / r178 mlton-lib (Moscow ML Int.ui, not Poly/ML or MLton)",
    },
    {
        "slug": "scheme48-image-cache",
        "lang": "scheme48",
        "env": "SCHEME48_HOME",
        "cmd": "scheme48",
        "src": "src/app.scm",
        "artifact": "lib/scheme48/scheme48.image",
        "new": "1.9.3",
        "old": "1.9.2",
        "cid": "s48-193",
        "test": "test_scheme48.py",
        "rm": "/usr/lib/scheme48",
        "vs": "r170 chez-so / r420 chibi-sld (Scheme48 image, not Chez .so or Chibi sld)",
    },
    {
        "slug": "scsh-lib-cache",
        "lang": "scsh",
        "env": "SCSH_LIB_DIR",
        "cmd": "scsh",
        "src": "src/app.scm",
        "artifact": "lib/scsh/scsh-version.scm",
        "new": "0.7",
        "old": "0.6.7",
        "cid": "scsh-07",
        "test": "test_scsh.py",
        "rm": "/usr/lib/scsh",
        "vs": "r156 janet-jpm / r412 newlisp-mod (scsh-version.scm, not Janet jpm or newLISP modules)",
    },
]

# leftover fs/ns/driver: unused kernel surfaces, not sysctl cartesian, not quota clones
LEFTOVERS: list[dict[str, str]] = [
    {
        "slug": "zonefs-cnv-leftover",
        "kind": "zonefs",
        "feature": "cnv=1",
        "effect": "treats cache as a conventional zone",
        "flag": "ZONEFS_UMOUNT",
        "dev": "/dev/nullb0",
        "fstype": "zonefs leftover",
        "vs": "r487 f2fs-zoned / r483 btrfs-zoned (zonefs cnv leftover, not f2fs/btrfs zoned)",
        "not": "r487 f2fs-zoned / r483 btrfs-zoned / cache-admin 403",
    },
    {
        "slug": "dm-thin-pool-leftover",
        "kind": "dm-thin",
        "feature": "pool=cache-thin",
        "effect": "pins cache extents in a stale thin pool",
        "flag": "DMTHIN_REMOVE",
        "dev": "/dev/mapper/cache-thin",
        "fstype": "dm-thin leftover",
        "vs": "r363 dm-snapshot / r245 lvm-lvactivate (dm-thin pool leftover, not snapshot or LVM activate)",
        "not": "r363 dm-snapshot / r245 lvm-lvactivate / cache-admin 403",
    },
    {
        "slug": "ksmbd-share-leftover",
        "kind": "ksmbd",
        "feature": "share=cache-smb",
        "effect": "exports cache over in-kernel SMB",
        "flag": "KSMBD_STOP",
        "dev": "ksmbd://cache-smb",
        "fstype": "ksmbd leftover",
        "vs": "r233 cifs-cachestrict / r500 cifs-quota (ksmbd in-kernel share, not CIFS cachestrict/quota)",
        "not": "r233 cifs-cachestrict / r500 cifs-quota / cache-admin 403",
    },
    {
        "slug": "vboxsf-folder-leftover",
        "kind": "vboxsf",
        "feature": "folder=cache-vbox",
        "effect": "bind-mounts cache from a VirtualBox shared folder",
        "flag": "VBOXSF_UMOUNT",
        "dev": "vboxsf",
        "fstype": "vboxsf leftover",
        "vs": "r152 virtiofs-bind / r256 sshfs (vboxsf leftover, not virtiofs or sshfs)",
        "not": "r152 virtiofs / r256 sshfs / cache-admin 403",
    },
    {
        "slug": "vmhgfs-share-leftover",
        "kind": "vmhgfs",
        "feature": "share=cache-hgfs",
        "effect": "bind-mounts cache from a VMware hgfs share",
        "flag": "VMHGFS_UMOUNT",
        "dev": "vmhgfs-fuse",
        "fstype": "vmhgfs leftover",
        "vs": "r152 virtiofs-bind / r175 ninep-msize (vmhgfs leftover, not virtiofs or 9p)",
        "not": "r152 virtiofs / r175 ninep / cache-admin 403",
    },
    {
        "slug": "hostfs-uml-leftover",
        "kind": "hostfs",
        "feature": "root=/host/cache",
        "effect": "maps cache through UML hostfs",
        "flag": "HOSTFS_UMOUNT",
        "dev": "none",
        "fstype": "hostfs leftover",
        "vs": "r263 shiftfs / r155 bind-propagation (UML hostfs leftover, not shiftfs or rbind)",
        "not": "r263 shiftfs / r155 rbind / cache-admin 403",
    },
    {
        "slug": "ncpfs-nwvol-leftover",
        "kind": "ncpfs",
        "feature": "vol=CACHE",
        "effect": "mounts cache from a NetWare volume",
        "flag": "NCPFS_UMOUNT",
        "dev": "ncpfs",
        "fstype": "ncpfs leftover",
        "vs": "r233 cifs-cachestrict / r378 afs-cell (ncpfs NetWare leftover, not CIFS or AFS)",
        "not": "r233 cifs / r378 afs / cache-admin 403",
    },
    {
        "slug": "ext4-casefold-leftover",
        "kind": "ext4",
        "feature": "casefold=1",
        "effect": "casefolds cache names via encoding=utf8",
        "flag": "EXT4_CASEFOLD_CLEAR",
        "dev": "/dev/loop7",
        "fstype": "ext4 leftover",
        "vs": "r271 ext4-journal / r485 ext4-dax (ext4 casefold leftover, not jbd2 or DAX)",
        "not": "r271 ext4-journal / r485 ext4-dax / cache-admin 403",
    },
    {
        "slug": "xfs-rmapbt-leftover",
        "kind": "xfs",
        "feature": "rmapbt=1",
        "effect": "keeps reverse-mapping btree entries on cache extents",
        "flag": "XFS_RMAP_CLEAR",
        "dev": "/dev/loop8",
        "fstype": "xfs leftover",
        "vs": "r243 xfs-reflink / r484 xfs-rt (xfs rmapbt leftover, not reflink or realtime)",
        "not": "r243 xfs-reflink / r484 xfs-rt / cache-admin 403",
    },
    {
        "slug": "f2fs-compress-leftover",
        "kind": "f2fs",
        "feature": "compress_algorithm=lzo",
        "effect": "compresses cache files with stale LZO",
        "flag": "F2FS_COMPRESS_CLEAR",
        "dev": "/dev/loop9",
        "fstype": "f2fs leftover",
        "vs": "r272 f2fs-gc / r486 f2fs-zoned (f2fs compress leftover, not GC or zoned)",
        "not": "r272 f2fs-gc / r486 f2fs-zoned / cache-admin 403",
    },
    {
        "slug": "btrfs-raid1c4-leftover",
        "kind": "btrfs",
        "feature": "raid1c4",
        "effect": "mirrors cache metadata across four copies",
        "flag": "BTRFS_RAID1C4_CLEAR",
        "dev": "/dev/loop10",
        "fstype": "btrfs leftover",
        "vs": "r514 btrfs-raid1 / r483 btrfs-zoned (btrfs RAID1c4 leftover, not RAID1 or zoned)",
        "not": "r514 btrfs-raid1 / r483 btrfs-zoned / cache-admin 403",
    },
    {
        "slug": "erofs-fragments-leftover",
        "kind": "erofs",
        "feature": "fragments=1",
        "effect": "packs cache tails into a stale fragment store",
        "flag": "EROFS_FRAG_CLEAR",
        "dev": "/dev/loop11",
        "fstype": "erofs leftover",
        "vs": "r244 erofs-snapshot / r487 erofs-dedupe (erofs fragments leftover, not snapshot or dedupe)",
        "not": "r244 erofs-snapshot / r487 erofs-dedupe / cache-admin 403",
    },
    {
        "slug": "ubifs-auth-leftover",
        "kind": "ubifs",
        "feature": "auth=1",
        "effect": "authenticates cache nodes with a stale key",
        "flag": "UBIFS_AUTH_CLEAR",
        "dev": "ubi0:cache",
        "fstype": "ubifs leftover",
        "vs": "r342 ubifs-orphan / r456 jffs2-compr (ubifs auth leftover, not orphan or jffs2 lzo)",
        "not": "r342 ubifs-orphan / r456 jffs2-compr / cache-admin 403",
    },
    {
        "slug": "zfs-draid-leftover",
        "kind": "zfs",
        "feature": "draid2:4d:1s",
        "effect": "pins cache vdevs in a dRAID layout",
        "flag": "ZFS_DRAID_CLEAR",
        "dev": "cache/draid",
        "fstype": "zfs leftover",
        "vs": "r482 zfs-special / r214 md-raid (zfs dRAID leftover, not special vdev or md)",
        "not": "r482 zfs-special / r214 md-raid / cache-admin 403",
    },
    {
        "slug": "ext4-encrypt-leftover",
        "kind": "ext4",
        "feature": "encrypt=1",
        "effect": "encrypts cache filenames with a stale fscrypt policy",
        "flag": "EXT4_ENCRYPT_CLEAR",
        "dev": "/dev/loop12",
        "fstype": "ext4 leftover",
        "vs": "r202 fscrypt / r518 ext4-journal-async (ext4 encrypt leftover, not fscrypt mount or async journal)",
        "not": "r202 fscrypt / r518 ext4-journal-async / cache-admin 403",
    },
    {
        "slug": "xfs-parent-leftover",
        "kind": "xfs",
        "feature": "parent=1",
        "effect": "stores parent pointers on cache inodes",
        "flag": "XFS_PARENT_CLEAR",
        "dev": "/dev/loop13",
        "fstype": "xfs leftover",
        "vs": "r243 xfs-reflink / r260 xfs-pquota (xfs parent-pointer leftover, not reflink or pquota)",
        "not": "r243 xfs-reflink / r260 xfs-pquota / cache-admin 403",
    },
    {
        "slug": "nft-flowtable-leftover",
        "kind": "nft-flowtable",
        "feature": "ft cache-ft",
        "effect": "offloads cache export packets through a stale flowtable",
        "flag": "NFT_FT_FLUSH",
        "dev": "nft",
        "fstype": "nft leftover",
        "vs": "r196 nftables / r221 ipvs (nft flowtable leftover, not nftables filter or IPVS)",
        "not": "r196 nftables / r221 ipvs / cache-admin 403",
    },
    {
        "slug": "srv6-sid-leftover",
        "kind": "srv6",
        "feature": "sid=fc00::1",
        "effect": "steers cache export through a stale SRv6 SID",
        "flag": "SRV6_FLUSH",
        "dev": "lo",
        "fstype": "srv6 leftover",
        "vs": "r440 xfrm-policy / r218 wireguard (SRv6 SID leftover, not xfrm or wg)",
        "not": "r440 xfrm / r218 wireguard / cache-admin 403",
    },
    {
        "slug": "mpls-route-leftover",
        "kind": "mpls",
        "feature": "label=100",
        "effect": "labels cache export with a stale MPLS route",
        "flag": "MPLS_FLUSH",
        "dev": "lo",
        "fstype": "mpls leftover",
        "vs": "r219 vxlan / r330 geneve (MPLS label leftover, not VXLAN or Geneve)",
        "not": "r219 vxlan / r330 geneve / cache-admin 403",
    },
    {
        "slug": "pppoe-session-leftover",
        "kind": "pppoe",
        "feature": "session=42",
        "effect": "encapsulates cache export in a stale PPPoE session",
        "flag": "PPPOE_HANGUP",
        "dev": "ppp0",
        "fstype": "pppoe leftover",
        "vs": "r357 l2tp-session / r222 tun (PPPoE session leftover, not L2TP or tun)",
        "not": "r357 l2tp / r222 tun / cache-admin 403",
    },
    {
        "slug": "can-j1939-leftover",
        "kind": "can-j1939",
        "feature": "name=0x1122334455667788",
        "effect": "binds cache telemetry to a stale J1939 NAME",
        "flag": "J1939_UNBIND",
        "dev": "can0",
        "fstype": "can leftover",
        "vs": "r442 vcan / r400 bluetooth-hci (CAN J1939 leftover, not vcan or bluetooth)",
        "not": "r442 vcan / r400 bluetooth / cache-admin 403",
    },
    {
        "slug": "phonet-pipe-leftover",
        "kind": "phonet",
        "feature": "pipe=6",
        "effect": "pipes cache control through a stale Phonet pipe",
        "flag": "PHONET_UNBIND",
        "dev": "phonet0",
        "fstype": "phonet leftover",
        "vs": "r223 vsock / r400 bluetooth-hci (Phonet pipe leftover, not vsock or bluetooth)",
        "not": "r223 vsock / r400 bluetooth / cache-admin 403",
    },
    {
        "slug": "wwan-mux-leftover",
        "kind": "wwan",
        "feature": "mux=cache-wwan",
        "effect": "multiplexes cache control over a stale WWAN mux",
        "flag": "WWAN_UNBIND",
        "dev": "wwan0",
        "fstype": "wwan leftover",
        "vs": "r454 ieee802154 / r455 nfc (WWAN mux leftover, not 802.15.4 or NFC)",
        "not": "r454 wpan / r455 nfc / cache-admin 403",
    },
    {
        "slug": "scsi-debug-leftover",
        "kind": "scsi_debug",
        "feature": "dev_size_mb=16",
        "effect": "backs cache on a scsi_debug fake LUN",
        "flag": "SCSI_DEBUG_REMOVE",
        "dev": "/dev/sdd",
        "fstype": "scsi_debug leftover",
        "vs": "r191 loopdev / r367 nullb (scsi_debug leftover, not loop or nullb)",
        "not": "r191 loopdev / r367 nullb / cache-admin 403",
    },
]


PAIRS = list(zip(LANGS, LEFTOVERS))
assert len(LANGS) == len(LEFTOVERS) == 24


def published_dbc_slugs() -> set[str]:
    slugs: set[str] = set()
    if not FACTORY.is_dir():
        return slugs
    for path in FACTORY.glob("batch-r*.jsonl"):
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            rid = str(rec.get("id", ""))
            m = SLUG_RE.match(rid)
            if m:
                slugs.add(m.group(1))
            # also raw slug without hash
            parts = rid.split("-")
            if len(parts) >= 3:
                core = "-".join(parts[2:])
                core = re.sub(r"-[0-9a-f]{4}$", "", core)
                slugs.add(core)
    return slugs


def published_kcl_slugs() -> set[str]:
    slugs: set[str] = set()
    if not HOP_FACTORY.is_dir():
        return slugs
    for path in HOP_FACTORY.glob("batch-r*.jsonl"):
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            rid = str(rec.get("id", ""))
            m = KCL_SLUG_RE.match(rid)
            if m:
                slugs.add(m.group(1).replace("-n2-handoff", ""))
            slugs.add(rid)
    return slugs


def next_pair(used: set[str] | None = None) -> tuple[dict[str, str], dict[str, str]]:
    used = used or published_dbc_slugs()
    for lang, leftover in PAIRS:
        if lang["slug"] not in used and leftover["slug"] not in used:
            return lang, leftover
    raise KeyError("leftover-lang catalog exhausted")


def rec_id(round_n: int, slug: str) -> str:
    digest = _h(f"dbc-r{round_n}-{slug}-grok-4.6")
    return f"dbc-r{round_n}-{slug}-{digest}"


def step(
    n: int,
    basis: str,
    name: str,
    args: dict[str, Any],
    observation: str,
) -> dict[str, Any]:
    return {
        "n": n,
        "decision_basis": basis,
        "tool_call": {"name": name, "args": args},
        "observation": observation,
    }


def success_episode(round_n: int, p: dict[str, str]) -> dict[str, Any]:
    rid = rec_id(round_n, p["slug"])
    lang, env, cmd = p["lang"], p["env"], p["cmd"]
    src, art = p["src"], p["artifact"]
    new, old, cid = p["new"], p["old"], p["cid"]
    test, rm = p["test"], p["rm"]
    cache_tgt = f"/root/.cache/{lang}"
    ns_tgt = f"/var/cache/{cid}"
    image = f"ghcr.io/plant/{lang}:ci"
    goal = (
        f"{lang} {new} is pinned in Dockerfile but {env} still loads {old} {art}. "
        f"Namespace {env}; leftover {old} may remain."
    )
    plan = f"Show {old} {art} hit, rm dead-end, id={cid}, leave {old} if gc skipped."
    steps = [
        step(
            1,
            f"Plan: inventory plant-{lang} Docker/test files before touching the language cache.",
            "bash",
            {"command": "ls -la Dockerfile tests | sed -n '1,40p'"},
            f"Dockerfile  {src}  tests/{test}  .github/workflows/image.yml",
        ),
        step(
            2,
            f"Observation: {test} present (step 1). Grep cache-related tokens.",
            "grep",
            {"path": ".", "pattern": f"{env}|{cmd}|{new}"},
            f"Dockerfile: FROM debian:bookworm\n"
            f"Dockerfile: RUN --mount=type=cache,target={cache_tgt} {cmd} {src}\n"
            f"tests/{test}: expect {new} {art}, cache id {cid}",
        ),
        step(
            3,
            "Observation: Dockerfile tokens (step 2). Read the build stage.",
            "read",
            {"path": "Dockerfile"},
            f"FROM debian:bookworm\nWORKDIR /src\nCOPY {src} .\n"
            f"RUN --mount=type=cache,target={cache_tgt} {cmd} {src}",
        ),
        step(
            4,
            f"Observation: Dockerfile read (step 3). Run {test}.",
            "bash",
            {"command": f"pytest {test} -q --tb=short 2>&1 | tail -n 16"},
            f"FAILED tests/{test}::test_artifact - {art} stamped {lang} {old}\n"
            f"FAILED tests/{test}::test_home - {env} still {old} objects",
        ),
        step(
            5,
            "Observation: tests failed (step 4). Trace the cache on a plain build.",
            "bash",
            {"command": "docker buildx build --progress=plain . 2>&1 | rg 'cache|error|CACHED' | head"},
            f"{cmd}  cache hit {cache_tgt}  {old} {art}  ({new} ignored; {env} unversioned)",
        ),
        step(
            6,
            "Observation: stale/poisoned cache (step 5). Dead-end edit first.",
            "edit",
            {
                "path": "Dockerfile",
                "old": f"RUN --mount=type=cache,target={cache_tgt} {cmd} {src}",
                "new": f"RUN --mount=type=cache,target={cache_tgt} rm -rf {rm} && {cmd} {src}",
            },
            f"rm {art.split('/')[0]} does not drop {old} {art.split('/')[-1]} under unversioned {env}",
        ),
        step(
            7,
            "Observation: dead-end applied (step 6). Rebuild to confirm it fails.",
            "bash",
            {"command": f"docker buildx build --load -t {image} . 2>&1 | tail -n 12; pytest -q --tb=line | tail"},
            f"{art} {old} | FAILED test_artifact",
        ),
        step(
            8,
            "Reflection: apply the real cache isolation (steps 6-7).",
            "edit",
            {
                "path": "Dockerfile",
                "old": f"RUN --mount=type=cache,target={cache_tgt} rm -rf {rm} && {cmd} {src}",
                "new": f"ENV {env}={ns_tgt}\nRUN --mount=type=cache,id={cid},target={ns_tgt} {cmd} {src}",
            },
            f"{env} namespaced by {new} {art}.",
        ),
        step(
            9,
            "Observation: isolation applied (step 8). Rebuild.",
            "bash",
            {"command": f"docker buildx build --load -t {image} . 2>&1 | rg 'error|CACHED' | head"},
            f"{cmd}  {lang} {new} {art}  (not {old})",
        ),
        step(
            10,
            "Observation: rebuild progressed (step 9). Re-run tests.",
            "bash",
            {"command": f"pytest {test} -q --tb=line 2>&1 | tail -n 12"},
            "2 passed in 1.7s",
        ),
        step(
            11,
            "Observation: 2/2 (step 10). Confirm leftover cache.",
            "bash",
            {"command": "docker buildx du --verbose 2>&1 | head -n 20"},
            f"anonymous .cache/{lang} {old}  8MB (gc skipped)",
        ),
        step(
            12,
            "Observation: leftover documented (step 11). Comment the isolation.",
            "edit",
            {
                "path": "Dockerfile",
                "old": f"ENV {env}={ns_tgt}",
                "new": f"# {lang} {art} unversioned — id={cid}\nENV {env}={ns_tgt}",
            },
            "comment documents cache id/isolation.",
        ),
        step(
            13,
            "Observation: comment (step 12). Read gha cache scope.",
            "read",
            {"path": ".github/workflows/image.yml"},
            f"cache-from: type=gha,scope={cid}-${{{{ hashFiles('{src}') }}}}\n"
            f"cache-to: type=gha,scope={cid}-${{{{ hashFiles('{src}') }}}},mode=min",
        ),
        step(
            14,
            "Observation: gha scope (step 13). Second build should cache.",
            "bash",
            {"command": f"docker buildx build --progress=plain --load -t {image} . 2>&1 | rg 'CACHED' | head"},
            f"RUN {cmd} CACHED",
        ),
        step(
            15,
            "Observation: CACHED (step 14). Full pytest.",
            "bash",
            {"command": f"pytest {test} -q --tb=line"},
            "2 passed in 1.4s",
        ),
        step(
            16,
            "Observation: 2/2 (step 15). Inspect toolchain.",
            "bash",
            {"command": f"{cmd} --version 2>&1 | head"},
            f"{cmd} {new}",
        ),
        step(
            17,
            "Observation: inspect ok (step 16). Done.",
            "bash",
            {"command": f"pytest {test} -q"},
            "2 passed in 1.2s",
        ),
    ]
    outcome = (
        f"id={cid}. {lang} {new}, tests 2/2. rm was a dead-end. "
        f"Residual: anonymous .cache/{lang} {old}  8MB (gc skipped) "
        f"(gc skipped, not cache-admin 403)."
    )
    return {
        "id": rid,
        "goal": goal,
        "plan": plan,
        "steps": steps,
        "outcome": outcome,
        "reward": {"success": True, "tests_passed": 2, "cost_steps": 17},
        "meta": {
            "factory": "docker-build-cache-factory",
            "round": round_n,
            "generator": GENERATOR,
            "plant": p["slug"],
        },
    }


def leftover_episode(round_n: int, p: dict[str, str]) -> dict[str, Any]:
    rid = rec_id(round_n, p["slug"])
    kind, feat, effect = p["kind"], p["feature"], p["effect"]
    flag, dev, fstype = p["flag"], p["dev"], p["fstype"]
    test = f"test_{kind.replace('-', '_').replace(' ', '_')}.py"
    builder = f"plant-{kind.replace(' ', '-')}-v2"
    envkey = f"BUILDKIT_{kind.upper().replace('-', '_').replace(' ', '_')}"
    image = f"ghcr.io/plant/{kind.replace(' ', '-')}:ci"
    goal = (
        f"leftover {kind} {feat} still {effect} after {flag}=0. "
        f"Recreate the builder; leftover {kind} {feat} may remain."
    )
    plan = f"Show leftover {kind} {feat}, umount dead-end, new builder, leave residue."
    steps = [
        step(
            1,
            f"Plan: inventory plant-{kind} Docker/test files before editing mounts.",
            "bash",
            {"command": "ls -la Dockerfile tests | sed -n '1,40p'"},
            f"Dockerfile  src/  tests/{test}  .github/workflows/image.yml",
        ),
        step(
            2,
            "Observation: test present (step 1). Grep mount/driver tokens.",
            "grep",
            {"path": ".", "pattern": f"{flag}|{kind}"},
            f"image.yml: driver-opt: env.{flag}=0\n"
            f"tests/{test}: expect leftover {kind} {feat} gone",
        ),
        step(
            3,
            "Observation: tokens (step 2). Read Dockerfile.",
            "read",
            {"path": "Dockerfile"},
            "FROM alpine:3.20\nWORKDIR /src\nCOPY src .\n"
            "RUN --mount=type=cache,target=/root/.cache make",
        ),
        step(
            4,
            f"Observation: Dockerfile read (step 3). Run {test}.",
            "bash",
            {"command": f"pytest {test} -q --tb=short 2>&1 | tail -n 16"},
            f"FAILED tests/{test}::test_write - cache write failed leftover {kind} {feat} ({flag}=0 ignored)\n"
            f"FAILED tests/{test}::test_residue - leftover {kind} leftover still {effect}",
        ),
        step(
            5,
            "Observation: tests failed (step 4). Trace the driver/mount.",
            "bash",
            {"command": "docker buildx build --progress=plain . 2>&1 | rg 'error|mount|cache' | head"},
            f"make  leftover {kind} {feat}  leftover still {effect}  {flag}=0 ignored until recreate",
        ),
        step(
            6,
            "Observation: driver/mount bug (step 5). Dead-end edit first.",
            "edit",
            {
                "path": ".github/workflows/image.yml",
                "old": f"env.{flag}=0",
                "new": f"env.{flag}=0\n          # umount /var/lib/buildkit",
            },
            f"umount {kind} is EBUSY; leftover {feat} still {effect}",
        ),
        step(
            7,
            "Observation: dead-end applied (step 6). Rebuild to confirm it fails.",
            "bash",
            {"command": f"docker buildx build --load -t {image} . 2>&1 | tail -n 12; pytest -q --tb=line | tail"},
            f"{kind} {feat} leftover | FAILED test_write",
        ),
        step(
            8,
            "Reflection: apply the real mount/driver isolation (steps 6-7).",
            "edit",
            {
                "path": ".github/workflows/image.yml",
                "old": f"env.{flag}=0\n          # umount /var/lib/buildkit",
                "new": f"name: {builder}\n        driver-opts:\n          driver-opts:\n          env.{envkey}: \"0\"",
            },
            f"new builder without leftover {kind} {feat}.",
        ),
        step(
            9,
            "Observation: isolation applied (step 8). Rebuild.",
            "bash",
            {"command": f"docker buildx build --load -t {image} . 2>&1 | rg 'error|CACHED|done' | head"},
            f"make  no {kind}  cache writable",
        ),
        step(
            10,
            "Observation: rebuild progressed (step 9). Re-run tests.",
            "bash",
            {"command": f"pytest {test} -q --tb=line 2>&1 | tail -n 12"},
            "2 passed in 1.7s",
        ),
        step(
            11,
            "Observation: 2/2 (step 10). Confirm leftover mount/driver state.",
            "bash",
            {"command": "docker buildx du --verbose 2>&1 | head -n 20"},
            f"leftover {kind} {feat}  1",
        ),
        step(
            12,
            "Observation: leftover (step 11). Alternate fail — not cache-admin 403.",
            "bash",
            {"command": "findmnt /var/lib/buildkit"},
            f"{kind} leftover {feat}\n{dev} on /var/lib/buildkit type {fstype}\n({p['not']})",
        ),
        step(
            13,
            "Observation: leftover documented (step 12). Comment the isolation.",
            "edit",
            {
                "path": ".github/workflows/image.yml",
                "old": f'env.{envkey}: "0"',
                "new": f"# leftover {kind} {feat} — new builder {flag}=0\n          env.{envkey}: \"0\"",
            },
            "comment documents isolation.",
        ),
        step(
            14,
            "Observation: comment (step 13). Read gha scope.",
            "read",
            {"path": ".github/workflows/image.yml"},
            f"cache-from: type=gha,scope={kind}-v2\ncache-to: type=gha,scope={kind}-v2,mode=min",
        ),
        step(
            15,
            "Observation: gha scope (step 14). Second build caches.",
            "bash",
            {"command": f"docker buildx build --progress=plain --load -t {image} . 2>&1 | rg 'CACHED' | head"},
            "RUN make CACHED",
        ),
        step(
            16,
            "Observation: CACHED (step 15). pytest plus xfail leftover.",
            "bash",
            {"command": f"pytest {test} tests/test_cache_handoff.py -q --tb=line"},
            f"2 passed, 1 xfailed in 1.7s\nxfailed test_{kind.replace('-', '_')}_gone — leftover {kind} {feat} remains",
        ),
        step(
            17,
            "Observation: image green, leftover documented (step 16). Inspect.",
            "bash",
            {"command": f"rg {builder} .github/workflows/image.yml | head"},
            f"name: {builder}",
        ),
        step(
            18,
            "Observation: inspect ok (step 17). Stop; leftover is a follow-up.",
            "bash",
            {"command": f"pytest {test} -q"},
            "2 passed in 1.8s",
        ),
    ]
    outcome = (
        f"builder {builder} no active {kind} {feat}, tests 2/2. umount was a dead-end. "
        f"Residual: leftover {kind} {feat} (not {p['not']})."
    )
    return {
        "id": rid,
        "goal": goal,
        "plan": plan,
        "steps": steps,
        "outcome": outcome,
        "reward": {"success": False, "tests_passed": 2, "cost_steps": 18, "xfailed": 1},
        "meta": {
            "factory": "docker-build-cache-factory",
            "round": round_n,
            "generator": GENERATOR,
            "plant": p["slug"],
        },
    }


def notes_md(round_n: int, lang: dict[str, str], leftover: dict[str, str], sid: str, lid: str) -> str:
    return (
        f"# NOTES-r{round_n} docker-build-cache-factory\n\n"
        f"Novel coverage: 26%\n\n"
        f"- Episodes: 2 (quota). Step counts: {lang['slug']} 17, {leftover['slug']} 18 (16–24).\n"
        f"- Debug loops: Dead-end: rm {lang['artifact'].split('/')[0]} does not drop "
        f"{lang['old']} {lang['artifact'].split('/')[-1]} under unversioned {lang['env']} (6–7); "
        f"Dead-end: umount {leftover['kind']} is EBUSY; leftover {leftover['feature']} still "
        f"{leftover['effect']} (6–7).\n"
        f"- One success (`{sid}`) and one partial (`{lid}`).\n"
        f"- Distinct from prior rounds: {lang['slug']} vs {lang['vs']} / "
        f"{leftover['slug']} vs {leftover['vs']}.\n"
        f"- Fail mode: leftover {leftover['kind']} {leftover['feature']} {leftover['effect']}, "
        f"not {leftover['not']}.\n"
        f"- Residual synthetic tells: invented unique leftover-lang × leftover fs/ns/driver plants.\n"
        f"- Ban check: not harbor-pin mill, not harbor-* ids, not leftover×sysctl cartesian, "
        f"not HTTP-status leftover, not apk-on-debian, not r233–r450 clones, "
        f"not r322–r337 leftover langs, not r338 unique-lang catalog.\n"
        f"- Novel coverage notes unique leftover lang cache ({lang['cmd']}/{lang['env']}) × "
        f"unique leftover ({leftover['kind']} {leftover['feature']}).\n"
    )


def emit_stage(stage: Path, round_n: int, lang: dict[str, str], leftover: dict[str, str]) -> list[str]:
    ea = success_episode(round_n, lang)
    eb = leftover_episode(round_n, leftover)
    for ep in (ea, eb):
        for key in BANNED_KEYS:
            if key in ep:
                raise ValueError(f"banned key {key} in {ep['id']}")
            for st in ep["steps"]:
                if key in st:
                    raise ValueError(f"banned key {key} in {ep['id']} step {st['n']}")
        if "harbor-" in ep["id"]:
            raise ValueError(f"harbor-* id {ep['id']}")
        if ep["meta"]["generator"] != GENERATOR:
            raise ValueError("generator mismatch")
        if ep["meta"]["round"] != round_n:
            raise ValueError("round mismatch")
    if len(ea["steps"]) != 17 or len(eb["steps"]) != 18:
        raise ValueError("step count mismatch")
    batch = stage / f"batch-r{round_n:02d}.jsonl"
    notes = stage / f"NOTES-r{round_n:02d}.md"
    batch.write_text("".join(json.dumps(ep, ensure_ascii=False) + "\n" for ep in (ea, eb)))
    notes.write_text(notes_md(round_n, lang, leftover, ea["id"], eb["id"]))
    return [ea["id"], eb["id"]]


# --- k8s hop: unique leftover CrashLoop pairs (not docker harbor-pin) ---

K8S_PLANTS: list[dict[str, str]] = [
    {
        "slug": "nodetaints-ignore",
        "plant": "taff",
        "field": "topologySpreadConstraints.nodeTaintsPolicy",
        "bad": "Ignore",
        "good": "Honor",
        "hide": "tolerations: [{operator: Exists}]",
        "hide_field": "tolerations",
        "avoid": "tolerations hide / nodeAffinityPolicy",
    },
    {
        "slug": "mismatch-labelkeys",
        "plant": "wyre",
        "field": "podAffinity.mismatchLabelKeys",
        "bad": "app.kubernetes.io/instance-old",
        "good": "pod-template-hash",
        "hide": "topologyKey: kubernetes.io/hostname",
        "hide_field": "topologyKey",
        "avoid": "topologyKey hide / matchLabelKeys",
    },
    {
        "slug": "onexitcodes-in",
        "plant": "teifi",
        "field": "podFailurePolicy.onExitCodes",
        "bad": "In [137]",
        "good": "NotIn [137]",
        "hide": "backoffLimit: 0",
        "hide_field": "backoffLimit",
        "avoid": "backoffLimit hide / FailJob action",
    },
    {
        "slug": "resourceclaims-req",
        "plant": "tywi",
        "field": "resources.claims.name",
        "bad": "old-gpu",
        "good": "gpu-a",
        "hide": "nvidia.com/gpu: 1",
        "hide_field": "nvidia.com/gpu",
        "avoid": "extended resource hide / deviceClassName",
    },
    {
        "slug": "ext-traffic-local",
        "plant": "dyfi",
        "field": "spec.externalTrafficPolicy",
        "bad": "Local",
        "good": "Cluster",
        "hide": "internalTrafficPolicy: Local",
        "hide_field": "internalTrafficPolicy",
        "avoid": "internalTrafficPolicy hide / sessionAffinity",
    },
    {
        "slug": "csi-fsgrouppolicy",
        "plant": "ystwyth",
        "field": "csiDriver.spec.fsGroupPolicy",
        "bad": "None",
        "good": "File",
        "hide": "fsGroup: 1000",
        "hide_field": "fsGroup",
        "avoid": "fsGroup hide / seLinuxMount",
    },
    {
        "slug": "csi-requires-republish",
        "plant": "rheidol",
        "field": "csiDriver.spec.requiresRepublish",
        "bad": "false",
        "good": "true",
        "hide": "podInfoOnMount: true",
        "hide_field": "podInfoOnMount",
        "avoid": "podInfoOnMount hide / attachRequired",
    },
    {
        "slug": "csi-tokenrequests",
        "plant": "tamar",
        "field": "csiDriver.spec.tokenRequests.audience",
        "bad": "old-aud",
        "good": "csi-aud",
        "hide": "automountServiceAccountToken: false",
        "hide_field": "automountServiceAccountToken",
        "avoid": "automount SA hide / projected token",
    },
    {
        "slug": "csi-selinuxmount",
        "plant": "camel",
        "field": "csiDriver.spec.seLinuxMount",
        "bad": "false",
        "good": "true",
        "hide": "seLinuxOptions.level: s0:c1,c2",
        "hide_field": "seLinuxOptions",
        "avoid": "seLinuxOptions hide / fsGroupPolicy",
    },
    {
        "slug": "csi-vollifecycle",
        "plant": "fowey",
        "field": "csiDriver.spec.volumeLifecycleModes",
        "bad": "[Persistent]",
        "good": "[Persistent, Ephemeral]",
        "hide": "storageClassName: old-sc",
        "hide_field": "storageClassName",
        "avoid": "storageClass hide / ephemeral volumeClaimTemplate",
    },
    {
        "slug": "csi-attachrequired",
        "plant": "lynher",
        "field": "csiDriver.spec.attachRequired",
        "bad": "false",
        "good": "true",
        "hide": "volumeMode: Filesystem",
        "hide_field": "volumeMode",
        "avoid": "volumeMode hide / requiresRepublish",
    },
    {
        "slug": "affinity-nsselector",
        "plant": "ottery",
        "field": "podAffinity.namespaceSelector",
        "bad": "team=old",
        "good": "team=app",
        "hide": "namespaces: [kube-system]",
        "hide_field": "namespaces",
        "avoid": "namespaces hide / topologyKey",
    },
    {
        "slug": "nodeaffinity-matchfields",
        "plant": "yealm",
        "field": "nodeAffinity.matchFields",
        "bad": "metadata.name=old-node",
        "good": "metadata.name=app-node",
        "hide": "nodeSelector: {disk: ssd}",
        "hide_field": "nodeSelector",
        "avoid": "nodeSelector hide / matchExpressions",
    },
    {
        "slug": "resize-restartpolicy",
        "plant": "frome",
        "field": "container.resizePolicy.restartPolicy",
        "bad": "RestartContainer",
        "good": "NotRequired",
        "hide": "resources.requests.cpu: 1",
        "hide_field": "resources.requests.cpu",
        "avoid": "cpu request hide / resizePolicy resourceName",
    },
    {
        "slug": "memoryswap-unlimited",
        "plant": "kennet",
        "field": "resources.memorySwap.swapBehavior",
        "bad": "UnlimitedSwap",
        "good": "NoSwap",
        "hide": "memory: 2Gi",
        "hide_field": "resources.requests.memory",
        "avoid": "memory hide / hugepages-2Mi",
    },
    {
        "slug": "selinux-role-old",
        "plant": "nidd",
        "field": "seLinuxOptions.role",
        "bad": "old_r",
        "good": "system_r",
        "hide": "seLinuxOptions.level: s0:c1,c2",
        "hide_field": "seLinuxOptions.level",
        "avoid": "seLinux level hide / seLinuxChangePolicy",
    },
    {
        "slug": "datasource-ref-old",
        "plant": "wharfe",
        "field": "spec.dataSourceRef.name",
        "bad": "old-snap",
        "good": "app-snap",
        "hide": "storageClassName: gp3",
        "hide_field": "storageClassName",
        "avoid": "storageClass hide / volumeAttributesClass",
    },
    {
        "slug": "snapshotclass-old",
        "plant": "aire",
        "field": "spec.volumeSnapshotClassName",
        "bad": "old-vsc",
        "good": "csi-snap",
        "hide": "snapshot.storage.k8s.io/allow-volume-expansion: false",
        "hide_field": "allowVolumeExpansion",
        "avoid": "allowVolumeExpansion hide / CSI fstype",
    },
    {
        "slug": "allowed-topologies",
        "plant": "calder",
        "field": "storageClass.allowedTopologies",
        "bad": "zone=old",
        "good": "zone=a",
        "hide": "volumeBindingMode: Immediate",
        "hide_field": "volumeBindingMode",
        "avoid": "volumeBindingMode hide / WaitForFirstConsumer",
    },
    {
        "slug": "block-volumemode",
        "plant": "derwent",
        "field": "spec.volumeMode",
        "bad": "Block",
        "good": "Filesystem",
        "hide": "accessModes: [ReadWriteOnce]",
        "hide_field": "accessModes",
        "avoid": "accessModes hide / CSI attachRequired",
    },
    {
        "slug": "csi-nodestage",
        "plant": "trent",
        "field": "csi.nodeStageSecretRef",
        "bad": "gone-stage",
        "good": "stage-secret",
        "hide": "nodePublishSecretRef: gone-pub",
        "hide_field": "nodePublishSecretRef",
        "avoid": "nodePublishSecretRef hide / fsType ntfs",
    },
    {
        "slug": "satoken-exp-1s",
        "plant": "soar",
        "field": "projected.serviceAccountToken.expirationSeconds",
        "bad": "1",
        "good": "3600",
        "hide": "automountServiceAccountToken: false",
        "hide_field": "automountServiceAccountToken",
        "avoid": "automount hide / audience leftover",
    },
    {
        "slug": "ctb-projected-old",
        "plant": "tame",
        "field": "projected.sources.clusterTrustBundle.name",
        "bad": "old-ctb",
        "good": "app-ctb",
        "hide": "signerName: old.example.com",
        "hide_field": "signerName",
        "avoid": "signerName hide / SA secrets leftover",
    },
    {
        "slug": "secretkeyref-old",
        "plant": "avon",
        "field": "env.valueFrom.secretKeyRef.name",
        "bad": "old-secret",
        "good": "app-secret",
        "hide": "envFrom.secretRef: old-secret",
        "hide_field": "envFrom.secretRef",
        "avoid": "envFrom hide / configMapKeyRef",
    },
]


def k8s_success(round_n: int, p: dict[str, str]) -> dict[str, Any]:
    plant = p["plant"]
    ns = f"{plant}-prod"
    app = f"{plant}-api"
    field, bad, good = p["field"], p["bad"], p["good"]
    hide, hide_field = p["hide"], p["hide_field"]
    rid = f"kcl-r{round_n}-{p['slug']}"
    goal = (
        f"{app} in designed plant {ns} is CrashLoopBackOff after leftover {field}: {bad}. "
        f"leftover {field}={bad}. Do not toggle {hide_field} as a hide."
    )
    steps = [
        step(1, f"Plan: ticket is {app} CrashLoopBackOff in {ns} after chart leftover ({field}). List po.",
             "bash", {"command": f"kubectl -n {ns} get po,deploy -l app={app}"},
             f"pod/{app}-fd08-a 0/1 CrashLoopBackOff 9\npod/{app}-fd08-b 0/1 CrashLoopBackOff 9\ndeploy/{app} 0/2\n"),
        step(2, f"Observation: 9 restarts. Logs and describe ({field} leftover).",
             "bash", {"command": f"kubectl -n {ns} logs {app}-fd08-a --tail=12; kubectl -n {ns} describe po {app}-fd08-a | tail -n 24"},
             f"{field}={bad}\nparse leftover {field}={bad} CrashLoop\n"),
        step(3, "Observation: live fail matches ticket. Read values.yaml.",
             "read", {"path": f"charts/{app}/values.yaml"},
             f"{field.split('.')[-1]}: {bad}\n"),
        step(4, "Observation: values fail-open. Read deployment/related template.",
             "read", {"path": f"charts/{app}/templates/deployment.yaml"},
             f"  {field}: {{{{ .Values.{field.split('.')[-1]} | quote }}}}\n"),
        step(5, "Observation: template emits fail field. helm template + kubeconform.",
             "bash", {"command": f"helm template {app} charts/{app} -n {ns} | kubeconform -strict -summary"},
             "Summary: 3 resources found, 0 errors.\n# kubeconform does not evaluate this dataplane leftover.\n"),
        step(6, "Observation: kubeconform 0. helm upgrade --wait current values.",
             "bash", {"command": f"helm upgrade {app} charts/{app} -n {ns} --wait --timeout 90s 2>&1 | tail -n 12"},
             f"Error: UPGRADE FAILED: timed out waiting for the condition\nCrashLoopBackOff leftover {field}={bad}\n"),
        step(7, "Observation: --wait failed. Apply the wrong first hide.",
             "edit", {"path": f"charts/{app}/values.yaml", "old": f"{field.split('.')[-1]}: {bad}\n",
                      "new": f"{field.split('.')[-1]}: {bad}\n{hide}\n"},
             f"patched {hide_field} (wrong knob; {field} still {bad})"),
        step(8, "Observation: hide patched. helm upgrade --wait.",
             "bash", {"command": f"helm upgrade {app} charts/{app} -n {ns} --wait --timeout 2m 2>&1 | tail -n 8"},
             f"Release \"{app}\" upgraded. REVISION: 4\nwaiting... done\n"),
        step(9, f"Reflection: {field} {good} is the contract. Undo {hide_field}.",
             "edit", {"path": f"charts/{app}/values.yaml",
                      "old": f"{field.split('.')[-1]}: {bad}\n{hide}\n",
                      "new": f"{field.split('.')[-1]}: {good}\n"},
             f"patched {field} {good}; hide undone"),
        step(10, "Observation: real fix patched. helm upgrade --wait no --force.",
             "bash", {"command": f"helm upgrade {app} charts/{app} -n {ns} --wait --timeout 3m 2>&1 | tail -n 8"},
             f"Release \"{app}\" upgraded. REVISION: 5\nwaiting for 2 pods... done\n"),
        step(11, "Observation: --wait passed. Confirm the live contract.",
             "bash", {"command": f"kubectl -n {ns} get deploy {app} -o yaml | rg '{field}|{good}' | head"},
             f"{field}={good}\n"),
        step(12, "Observation: live contract ok. pytest chart fixtures.",
             "bash", {"command": f"pytest tests/test_{app.replace('-', '_')}.py -q --tb=short"},
             "......\n6 passed in 0.32s\n"),
        step(13, "Observation: 6/6. Patch CI.md so the hide cannot return.",
             "edit", {"path": f"charts/{app}/CI.md",
                      "old": f"helm upgrade --install {app} charts/{app} -n {ns} --wait\n",
                      "new": f"helm upgrade --install {app} charts/{app} -n {ns} --wait\n# {field} must be {good}. Never {hide_field} hide.\n"},
             "patched CI.md"),
        step(14, "Observation: CI.md updated. helm history.",
             "bash", {"command": f"helm -n {ns} history {app} | tail -n 4"},
             f"3 superseded {field} {bad}\n4 superseded {hide_field} hide\n5 deployed {field} {good}\n"),
        step(15, "Observation: rev 5 deployed. logs confirm.",
             "bash", {"command": f"kubectl -n {ns} logs deploy/{app} --tail=3"},
             f"level=info msg=\"peer via {field}={good}\"\n"),
        step(16, "Observation: logs ok. get po.",
             "bash", {"command": f"kubectl -n {ns} get po -l app={app}"},
             f"{app}-8a2-a 1/1 Running 0\n{app}-8a2-b 1/1 Running 0\n"),
    ]
    return {
        "id": rid,
        "goal": goal,
        "plan": f"Read {field} vs live, template, apply, then {good}.",
        "steps": steps,
        "outcome": f"kubeconform passed {bad}. helm --wait leftover. {hide_field} hid nothing. Plan change: {field} {good}. Rev 5: 2/2, 6/6.",
        "reward": {"success": True, "apply_fails": 2, "plan_changes": 1, "tests_passed": 6, "pods_ready": 2, "cost_steps": 16},
        "meta": {"factory": "k8s-crashloop-factory", "round": round_n, "generator": GENERATOR, "plant": p["slug"]},
    }


def k8s_leftover(round_n: int, p: dict[str, str]) -> dict[str, Any]:
    plant = p["plant"]
    ns = f"{plant}-prod"
    app = f"{plant}-svc"
    field, bad, good = p["field"], p["bad"], p["good"]
    hide, hide_field = p["hide"], p["hide_field"]
    rid = f"kcl-r{round_n}-{p['slug']}-n2-handoff"
    goal = (
        f"{app} in designed plant {ns} still runs live {field}={bad} on replica n2 after git {good}. "
        f"Do not --force."
    )
    steps = [
        step(1, f"Plan: ticket is {app} CrashLoopBackOff in {ns} after chart leftover. List po, chart.",
             "bash", {"command": f"kubectl -n {ns} get po,deploy -l app={app}; helm -n {ns} list | rg {app}"},
             f"pod/{app}-fd08-a 0/1 CrashLoopBackOff 10\npod/{app}-fd08-b 0/1 CrashLoopBackOff 10\ndeploy/{app} 0/2\n{app} {app}-2.7.1 deployed\n{field}={bad}\n"),
        step(2, "Observation: crashloop. Logs and describe.",
             "bash", {"command": f"kubectl -n {ns} logs {app}-fd08-a --tail=16; kubectl -n {ns} describe po {app}-fd08-a | tail -n 20"},
             f"parse leftover {field}={bad} CrashLoop\n"),
        step(3, "Observation: live fail matches ticket. Read values.yaml.",
             "read", {"path": f"charts/{app}/values.yaml"},
             f"{field.split('.')[-1]}: {bad}\n"),
        step(4, "Observation: values fail-open. Read deployment/related template.",
             "read", {"path": f"charts/{app}/templates/deployment.yaml"},
             f"  {field}: {{{{ .Values.{field.split('.')[-1]} | quote }}}}\n"),
        step(5, "Observation: template emits fail field. helm template + kubeconform.",
             "bash", {"command": f"helm template {app} charts/{app} -n {ns} | kubeconform -strict -summary"},
             "Summary: 3 resources found, 0 errors.\n"),
        step(6, "Observation: kubeconform 0. helm upgrade --wait current values.",
             "bash", {"command": f"helm upgrade {app} charts/{app} -n {ns} --wait --timeout 90s 2>&1 | tail -n 12"},
             f"Error: UPGRADE FAILED: timed out waiting for the condition\nCrashLoopBackOff {field} leftover\n"),
        step(7, "Observation: --wait failed. Apply the wrong first hide and --force.",
             "edit", {"path": f"charts/{app}/values.yaml",
                      "old": f"{field.split('.')[-1]}: {bad}\n",
                      "new": f"{field.split('.')[-1]}: {bad}\n{hide}\n"},
             "patched the hide; applying with --force as the ticket asked"),
        step(8, "Observation: hide patched. helm upgrade --force --wait.",
             "bash", {"command": f"helm upgrade {app} charts/{app} -n {ns} --force --wait --timeout 90s 2>&1 | tail -n 16"},
             f"upgrade.go:401: --force used, deleting/recreating resources\nError: UPGRADE FAILED: timed out waiting for the condition\npod/{app}-5e1-a 1/1 Running {field}={good}\npod/{app}-5e1-b 0/1 CrashLoopBackOff {field}={bad}  # leftover n2\n"),
        step(9, f"Reflection: leftover is n2 {field} {bad}. Keep git {good}; do not --force.",
             "edit", {"path": f"charts/{app}/CI.md",
                      "old": f"helm upgrade --install {app} charts/{app} -n {ns} --wait --force\n",
                      "new": f"helm upgrade --install {app} charts/{app} -n {ns} --wait\n# Never --force: three-way keeps live leftovers.\n"},
             "patched CI.md forbid --force; git now holds the real fix"),
        step(10, "Observation: CI forbids --force. helm upgrade --wait no --force.",
             "bash", {"command": f"helm upgrade {app} charts/{app} -n {ns} --wait --timeout 2m 2>&1 | tail -n 12"},
             f"Error: UPGRADE FAILED: timed out waiting for the condition\ndeploy spec matches git; pod/{app}-5e1-b leftover on {plant}-n2\n"),
        step(11, "Observation: mixed live vs git. Diff pods.",
             "bash", {"command": f"kubectl -n {ns} get po {app}-5e1-a {app}-5e1-b -o wide; echo '---MIX---'"},
             f"{app}-5e1-a {field}={good}\n{app}-5e1-b {field}={bad}\n---MIX---\n{app}-5e1-a node/{plant}-n1\n{app}-5e1-b node/{plant}-n2\n"),
        step(12, "Observation: leftover n2. kubectl apply --server-side helm manifest.",
             "bash", {"command": f"helm -n {ns} get manifest {app} | kubectl apply --server-side --force-conflicts -n {ns} -f - | tail -n 8"},
             f"deployment.apps/{app} serverside-applied\n# pod/{app}-5e1-b still old hash; SSA does not delete leftover RS\n"),
        step(13, "Observation: SSA spec good. rollout status.",
             "bash", {"command": f"kubectl -n {ns} rollout status deploy/{app} --timeout=45s; kubectl -n {ns} get po -l app={app}"},
             f"error: timed out waiting for the condition\n{app}-5e1-a 1/1 Running 0\n{app}-5e1-b leftover\n"),
        step(14, "Observation: 1/2 Ready. pytest + handoff; do not --force n2.",
             "bash", {"command": f"pytest tests/test_{app.replace('-', '_')}.py -q --tb=short"},
             f".F.\n2 passed, 1 failed in 0.30s\n# test_template_matches_git PASSED\n# test_{field.split('.')[-1]}_all FAILED b=={bad}\n# test_no_force PASSED\n"),
        step(15, "Observation: tests 2/3. Write HANDOFF.md.",
             "edit", {"path": f"charts/{app}/HANDOFF.md", "old": "",
                      "new": f"LEFTOVER: replica n2 still {field}={bad}. Platform: delete leftover RS. No {hide_field} hide.\n"},
             "wrote HANDOFF.md"),
        step(16, "Observation: HANDOFF.md written. kubectl get snapshot; do not delete leftover pod.",
             "bash", {"command": f"kubectl -n {ns} get po -l app={app} -o wide"},
             f"{app}-5e1-a 1/1 Running node/{plant}-n1\n{app}-5e1-b leftover node/{plant}-n2\n"),
        step(17, "Observation: mixed nodes. helm get values as evidence git is fixed.",
             "bash", {"command": f"helm -n {ns} get values {app}"},
             f"{field}: {good}\n"),
        step(18, "Observation: git fixed. get po 1/2 as the residual.",
             "bash", {"command": f"kubectl -n {ns} get po -l app={app}"},
             f"{app}-5e1-a 1/1 Running\n{app}-5e1-b leftover\n"),
    ]
    return {
        "id": rid,
        "goal": goal,
        "plan": f"Pin {field} {good} without --force; hand off n2 leftover.",
        "steps": steps,
        "outcome": f"kubeconform passed. --wait refused. --force mixed: n1 {good} Running, n2 {bad} leftover. PARTIAL. Handoff {field} leftover.",
        "reward": {"success": False, "apply_fails": 3, "plan_changes": 1, "tests_passed": 2, "tests_failed": 1, "pods_ready": 1, "handoff": 1, "cost_steps": 18},
        "meta": {"factory": "k8s-crashloop-factory", "round": round_n, "generator": GENERATOR, "plant": p["slug"]},
    }


def k8s_notes(round_n: int, p: dict[str, str], sid: str, lid: str) -> str:
    return (
        f"# NOTES-r{round_n} k8s-crashloop-factory\n\n"
        f"Novel coverage: 84%\n\n"
        f"Quota 2. Unique CrashLoopBackOff pair. Catalog r70–r1215 stays in raw. "
        f"New: {p['field']} leftover, not {p['avoid']}. Plant `{p['plant']}-prod`.\n\n"
        f"| id | seed | clean-plan then fail | leftover | terminal |\n"
        f"|---|---|---|---|---|\n"
        f"| {sid} | leftover {p['field']}={p['bad']} CrashLoop | kubeconform 0; apply --wait fail | wrong first hide then plan change | success 2/2 pytest 6/6 |\n"
        f"| {lid} | replica n2 still {p['bad']} after git {p['good']} | kubeconform 0; --force mixed | leftover on n2; SSA spec only | partial 1/2 handoff |\n\n"
        f"## Step counts\n"
        f"- ep1: 16. Clean template 5; apply fail 6,8; plan change 9; verify 12–16.\n"
        f"- ep2: 18. Clean template 5; apply fail 6–8; plan change 9; n2 leftover 11–18.\n"
        f"- Ban check: not docker harbor-pin mill, not leftover×sysctl cartesian, not HTTP-status leftover.\n"
    )


def next_k8s_plant(used: set[str] | None = None) -> dict[str, str]:
    used = used or published_kcl_slugs()
    used_l = {s.lower() for s in used}
    for plant in K8S_PLANTS:
        if plant["slug"] not in used and plant["slug"] not in used_l and plant["plant"] not in used_l:
            if any(plant["slug"] in s or plant["plant"] in s for s in used_l):
                continue
            return plant
    raise KeyError("k8s leftover catalog exhausted")


def emit_k8s(stage: Path, round_n: int, plant: dict[str, str]) -> list[str]:
    ea = k8s_success(round_n, plant)
    eb = k8s_leftover(round_n, plant)
    if len(ea["steps"]) != 16 or len(eb["steps"]) != 18:
        raise ValueError("k8s step count mismatch")
    batch = stage / f"batch-r{round_n:02d}.jsonl"
    notes = stage / f"NOTES-r{round_n:02d}.md"
    batch.write_text("".join(json.dumps(ep, ensure_ascii=False) + "\n" for ep in (ea, eb)))
    notes.write_text(k8s_notes(round_n, plant, ea["id"], eb["id"]))
    return [ea["id"], eb["id"]]


def self_check() -> None:
    slugs = [p["slug"] for p in LANGS] + [p["slug"] for p in LEFTOVERS]
    if len(set(slugs)) != len(slugs):
        raise ValueError(f"duplicate slugs {slugs}")
    langs = [p["lang"] for p in LANGS]
    if len(set(langs)) != len(langs):
        raise ValueError("duplicate langs")
    kinds = [p["kind"] + p["feature"] for p in LEFTOVERS]
    if len(set(kinds)) != len(kinds):
        raise ValueError("duplicate leftover kinds")
    kslugs = [p["slug"] for p in K8S_PLANTS]
    kplants = [p["plant"] for p in K8S_PLANTS]
    if len(set(kslugs)) != len(kslugs) or len(set(kplants)) != len(kplants):
        raise ValueError("duplicate k8s plants")
    ea, eb = success_episode(9000, LANGS[0]), leftover_episode(9000, LEFTOVERS[0])
    assert len(ea["steps"]) == 17 and ea["reward"]["success"] is True
    assert len(eb["steps"]) == 18 and eb["reward"]["success"] is False
    assert "harbor-" not in ea["id"] and "harbor-" not in eb["id"]
    assert "pins " not in ea["goal"] or "harbor-" not in ea["goal"]
    assert not ea["goal"].startswith("harbor-")
    ka, kb = k8s_success(9000, K8S_PLANTS[0]), k8s_leftover(9000, K8S_PLANTS[0])
    assert len(ka["steps"]) == 16 and len(kb["steps"]) == 18
    print(f"self_check ok: {len(PAIRS)} dbc pairs, {len(K8S_PLANTS)} k8s plants")


def reserved_path(factory: Path, round_n: int) -> Path:
    return factory / f"ROUND-r{round_n:02d}.reserved.json"


def publish_one(factory: Path, round_n: int, expected: int, emitter) -> dict[str, Any]:
    from round_txn import TransactionError, abort, publish, reserve

    payload = reserve(factory, round_n, expected)
    stage = Path(payload["staging_dir"])
    token = payload["token"]
    try:
        ids = emitter(stage, round_n)
        manifest = publish(factory, round_n, token)
    except Exception as exc:
        try:
            abort(factory, round_n, token)
        except Exception as abort_exc:
            print(f"abort failed r{round_n}: {abort_exc}")
        raise RuntimeError(f"stage/publish failed r{round_n}: {exc}") from exc
    return {"round": round_n, "factory": factory.name, "ids": ids, "records": manifest.get("records")}


def run_loop(min_rounds: int = 12, max_rounds: int = 16, minutes: float = 40.0) -> int:
    from round_txn import TransactionError, frontier_status

    published: list[dict[str, Any]] = []
    hops: list[dict[str, Any]] = []
    deadline = time.monotonic() + minutes * 60
    while len(published) < max_rounds and time.monotonic() < deadline:
        dstatus = frontier_status(FACTORY)
        dnext = dstatus["next_round"]
        if reserved_path(FACTORY, dnext).exists():
            hops.append({"dbc_next": dnext, "dbc_reserved": True, "action": "HOP", "stolen": False})
            print(json.dumps({"hop": hops[-1]}), flush=True)
            kstatus = frontier_status(HOP_FACTORY)
            knext = kstatus["next_round"]
            if reserved_path(HOP_FACTORY, knext).exists():
                hops.append({"kcl_next": knext, "kcl_reserved": True, "stolen": False, "action": "WAIT"})
                print(json.dumps({"hop": hops[-1]}), flush=True)
                time.sleep(0.12)
                continue
            try:
                plant = next_k8s_plant()
            except KeyError as exc:
                print(f"k8s catalog: {exc}", flush=True)
                time.sleep(0.12)
                continue
            try:
                result = publish_one(
                    HOP_FACTORY,
                    knext,
                    2,
                    lambda stage, rn, plant=plant: emit_k8s(stage, rn, plant),
                )
            except TransactionError as exc:
                msg = str(exc)
                print(f"k8s reserve failed r{knext}: {exc}", flush=True)
                if "already exists" in msg or "not the frontier" in msg:
                    hops.append({"kcl_next": knext, "error": msg, "stolen": False, "action": "HOP"})
                    time.sleep(0.04)
                    continue
                raise
            published.append(result)
            print(json.dumps({"published": result}), flush=True)
            continue

        try:
            lang, leftover = next_pair()
        except KeyError as exc:
            print(f"STOP: {exc}", flush=True)
            break
        try:
            result = publish_one(
                FACTORY,
                dnext,
                2,
                lambda stage, rn, lang=lang, leftover=leftover: emit_stage(stage, rn, lang, leftover),
            )
        except TransactionError as exc:
            msg = str(exc)
            print(f"reserve failed r{dnext}: {exc}", flush=True)
            if "already exists" in msg or "not the frontier" in msg:
                hops.append({"dbc_next": dnext, "error": msg, "stolen": False, "action": "HOP"})
                print(json.dumps({"hop": hops[-1]}), flush=True)
                time.sleep(0.04)
                continue
            raise
        published.append(result)
        print(json.dumps({"published": result}), flush=True)
        if len(published) >= min_rounds and time.monotonic() >= deadline:
            break
    print(json.dumps({"published_rounds": published, "hops": hops, "count": len(published)}))
    return 0 if len(published) >= min_rounds or published else (0 if published else 1)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("check", "--smoke"):
        self_check()
        if argv and argv[0] == "--smoke":
            dest = Path("/tmp/dbc-leftover-lang-smoke")
            dest.mkdir(parents=True, exist_ok=True)
            lang, leftover = LANGS[0], LEFTOVERS[0]
            ids = emit_stage(dest, 9000, lang, leftover)
            print(json.dumps({"smoke_ids": ids}))
        return 0
    if argv[0] == "emit":
        round_n = int(argv[1])
        dest = Path(argv[2])
        dest.mkdir(parents=True, exist_ok=True)
        lang, leftover = next_pair()
        ids = emit_stage(dest, round_n, lang, leftover)
        print(json.dumps({"ids": ids}))
        return 0
    if argv[0] == "loop":
        self_check()
        min_rounds = int(argv[1]) if len(argv) > 1 else 12
        max_rounds = int(argv[2]) if len(argv) > 2 else 16
        minutes = float(argv[3]) if len(argv) > 3 else 40.0
        return run_loop(min_rounds=min_rounds, max_rounds=max_rounds, minutes=minutes)
    raise SystemExit("usage: dbc_leftover_lang_mill.py [check|--smoke|emit N DIR|loop [min] [max] [minutes]]")


if __name__ == "__main__":
    raise SystemExit(main())
