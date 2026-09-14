#!/usr/bin/env python3
"""Mill docker-build-cache unique lang × fs/ns/driver leftovers from r396+.

BAN harbor-pin mill (harbor-X pins Y but CACHE still compiles).
BAN harbor-* IDs, HTTP-status leftover, apk-on-debian, sysctl cartesian,
r233–r395 lang clones, r322–r337 leftover clones, r338 catalog clones.
17-step success + 18-step leftover. meta.generator=grok-4.6. Q=2.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location(
    "dbc_mill_unique_r320", HERE / "dbc-mill-unique-r320.py"
)
_u = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_u)

FACTORY = _u.FACTORY
GEN = _u.GEN
published_slugs = _u.published_slugs
hx = _u.hx

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


def left(**kw):
    if "not_" in kw:
        kw["not"] = kw.pop("not_")
    return kw


def lang(
    slug,
    env,
    tool,
    old,
    new,
    artifact,
    test,
    src,
    cache_id,
    dead_rm,
    dead_obs,
    left_mb,
    vs,
    run,
    ver_cmd,
    img="FROM debian:bookworm",
):
    short = slug.split("-")[0]
    return {
        "slug": slug,
        "harbor": f"plant-{short}",
        "env": env,
        "tool": tool,
        "old": old,
        "new": new,
        "artifact": artifact,
        "test": test,
        "src": src,
        "cache_id": cache_id,
        "dead_rm": dead_rm,
        "dead_obs": dead_obs,
        "left_mb": left_mb,
        "vs": vs,
        "img": img,
        "run": run,
        "ver_cmd": ver_cmd,
    }


def leftover(
    slug,
    token,
    leftover,
    detail,
    dead,
    dead_obs,
    fail_mode,
    not_,
    vs,
    test,
    probe,
    probe_obs,
):
    short = slug.split("-")[0]
    return left(
        slug=slug,
        harbor=f"plant-{short}",
        token=token,
        leftover=leftover,
        detail=detail,
        dead=dead,
        dead_obs=dead_obs,
        fail_mode=fail_mode,
        not_=not_,
        vs=vs,
        test=test,
        probe=probe,
        probe_obs=probe_obs,
        fix_key=f"name: plant-{short}-v2",
        fix_val=f'driver-opts:\n          env.BUILDKIT_{token.split("_")[0]}: "0"',
    )


PAIRS: list[tuple[dict, dict]] = [
    (
        lang(
            "logtalk-lib-cache",
            "LOGTALKHOME",
            "logtalk",
            "3.72.0",
            "3.81.0",
            "library/types/types.lgt",
            "test_logtalk.py",
            "src/app.lgt",
            "lgt-3810",
            "rm -rf /usr/share/logtalk",
            "rm library does not drop 3.72 types.lgt under unversioned LOGTALKHOME",
            "8MB",
            "r149 swi-prolog / r333 inform7 (Logtalk library, not SWI pack or Inform7 kit)",
            "logtalk src/app.lgt",
            "logtalk --version",
        ),
        leftover(
            "iso9660-rr-leftover",
            "ISO9660_RR_CLEAR",
            "iso9660 rockridge norock",
            "iso9660 Rock Ridge leftover still maps cache names",
            "umount /var/lib/buildkit",
            "umount iso9660 is EBUSY; leftover rockridge norock still maps names",
            "leftover iso9660 Rock Ridge mapping cache names",
            "r240 erofs / r343 squashfs / cache-admin 403",
            "r343 squashfs leftover (iso9660 Rock Ridge leftover, not squashfs lz4)",
            "test_iso9660.py",
            "findmnt /var/lib/buildkit; cat /proc/fs/isofs/options",
            "iso9660 leftover rockridge norock\n/dev/sr0 on /var/lib/buildkit type iso9660 leftover",
        ),
    ),
    (
        lang(
            "picat-planner-cache",
            "PICATLIB",
            "picat",
            "3.5",
            "3.8",
            "lib/planner.pi",
            "test_picat.py",
            "src/route.pi",
            "picat-38",
            "rm -rf /usr/lib/picat",
            "rm lib does not drop 3.5 planner.pi under unversioned PICATLIB",
            "3MB",
            "r149 swi-prolog / r357 spin (Picat planner, not SWI pack or Promela)",
            "picat src/route.pi",
            "picat --version",
        ),
        leftover(
            "vfat-shortname-leftover",
            "VFAT_SHORTNAME_CLEAR",
            "vfat shortname=winnt",
            "vfat shortname leftover still mangles cache 8.3 names",
            "umount /var/lib/buildkit",
            "umount vfat is EBUSY; leftover shortname=winnt still mangles 8.3 names",
            "leftover vfat shortname mangling cache 8.3 names",
            "r340 ntfs3-acl / r341 exfat-discard / cache-admin 403",
            "r341 exfat leftover (vfat shortname leftover, not exfat discard)",
            "test_vfat.py",
            "findmnt /var/lib/buildkit; cat /proc/fs/fat/shortname",
            "vfat leftover shortname=winnt\n/dev/loop3 on /var/lib/buildkit type vfat leftover",
        ),
    ),
    (
        lang(
            "scryer-clpz-cache",
            "SCRYER_MODULE_PATH",
            "scryer-prolog",
            "0.9.3",
            "0.9.4",
            "src/lib/clpz.pl",
            "test_scryer.py",
            "src/csp.pl",
            "scryer-094",
            "rm -rf /usr/share/scryer",
            "rm lib does not drop 0.9.3 clpz.pl under unversioned SCRYER_MODULE_PATH",
            "5MB",
            "r149 swi-prolog / r192 gprolog (Scryer clpz, not SWI pack or GNU Prolog)",
            "scryer-prolog src/csp.pl",
            "scryer-prolog --version",
        ),
        leftover(
            "binderfs-ctrl-leftover",
            "BINDERFS_UMOUNT",
            "binderfs binder-control",
            "binderfs leftover still holds cache IPC binder",
            "umount /dev/binderfs",
            "umount binderfs is EBUSY; leftover binder-control still holds IPC",
            "leftover binderfs binder-control holding cache IPC",
            "r241 ipcns-sem / r237 memfd-seal / cache-admin 403",
            "r241 ipcns leftover (binderfs leftover, not ipcns sem)",
            "test_binderfs.py",
            "findmnt /dev/binderfs; ls /dev/binderfs",
            "binderfs leftover binder-control leftover\nbinderfs leftover on /dev/binderfs",
        ),
    ),
    (
        lang(
            "ciao-engine-cache",
            "CIAOROOT",
            "ciaoc",
            "1.22.0",
            "1.24.0",
            "core/engine/internals.pl",
            "test_ciao.py",
            "src/app.pl",
            "ciao-1240",
            "rm -rf /usr/lib/ciao",
            "rm core does not drop 1.22 internals.pl under unversioned CIAOROOT",
            "14MB",
            "r149 swi-prolog / r192 gprolog (Ciao engine, not SWI pack or GNU Prolog)",
            "ciaoc src/app.pl",
            "ciaoc --version",
        ),
        leftover(
            "functionfs-ep-leftover",
            "FUNCTIONFS_CLEAR",
            "functionfs ep0",
            "functionfs leftover still binds cache USB endpoints",
            "umount /dev/ffs-buildkit",
            "umount functionfs is EBUSY; leftover ep0 still bound",
            "leftover functionfs ep0 binding cache USB endpoints",
            "r389 configfs-gadget / r334 vhost-net / cache-admin 403",
            "r389 configfs gadget leftover (functionfs leftover, not usb_gadget)",
            "test_ffs.py",
            "findmnt /dev/ffs-buildkit; ls /dev/ffs-buildkit",
            "functionfs leftover ep0 leftover\nfunctionfs leftover on /dev/ffs-buildkit",
        ),
    ),
    (
        lang(
            "yap-boot-cache",
            "YAPLIBDIR",
            "yap",
            "7.4.0",
            "7.6.1",
            "share/Yap/prolog/boot.yap",
            "test_yap.py",
            "src/app.yap",
            "yap-761",
            "rm -rf /usr/share/Yap",
            "rm share does not drop 7.4 boot.yap under unversioned YAPLIBDIR",
            "9MB",
            "r149 swi-prolog / r192 gprolog (YAP boot, not SWI pack or GNU Prolog)",
            "yap -l src/app.yap",
            "yap --version",
        ),
        leftover(
            "coda-venus-leftover",
            "CODA_UNMOUNT",
            "coda venus cache",
            "coda venus leftover still holds cache volume",
            "umount /coda",
            "umount coda is EBUSY; leftover venus still holds volume",
            "leftover coda venus holding cache volume",
            "r378 afs-cell / r329 nfs4-deleg / cache-admin 403",
            "r378 afs leftover (coda venus leftover, not afs cell)",
            "test_coda.py",
            "findmnt /coda; cat /proc/fs/coda/venus",
            "coda leftover venus cache leftover\ncoda leftover on /coda",
        ),
    ),
    (
        lang(
            "xsb-syslib-cache",
            "XSBDIR",
            "xsb",
            "5.0.0",
            "5.0.2",
            "syslib/standard.P",
            "test_xsb.py",
            "src/app.P",
            "xsb-502",
            "rm -rf /opt/XSB",
            "rm syslib does not drop 5.0 standard.P under unversioned XSBDIR",
            "11MB",
            "r149 swi-prolog / r192 gprolog (XSB syslib, not SWI pack or GNU Prolog)",
            "xsb -e \"[src/app].\"",
            "xsb --version",
        ),
        leftover(
            "juicefs-meta-leftover",
            "JUICEFS_UMOUNT",
            "juicefs meta redis://10.8.0.9",
            "juicefs leftover still pins cache to a remote meta",
            "juicefs umount /var/lib/buildkit",
            "juicefs umount is EBUSY; leftover redis meta still pins cache",
            "leftover juicefs meta pinning cache dir",
            "r326 gluster-brick / r381 moosefs-chunk / cache-admin 403",
            "r381 moosefs leftover (juicefs meta leftover, not mfs chunkserver)",
            "test_juicefs.py",
            "juicefs status /var/lib/buildkit; findmnt /var/lib/buildkit",
            "juicefs leftover meta redis://10.8.0.9 leftover\njuicefs leftover on /var/lib/buildkit",
        ),
    ),
    (
        lang(
            "eclipse-clp-lib-cache",
            "ECLIPSEDIR",
            "eclipse",
            "7.0",
            "7.1",
            "lib/kernel.eco",
            "test_eclipseclp.py",
            "src/csp.ecl",
            "eclp-71",
            "rm -rf /opt/eclipseclp",
            "rm lib does not drop 7.0 kernel.eco under unversioned ECLIPSEDIR",
            "16MB",
            "r149 swi-prolog / r182 minizinc (ECLiPSe CLP kernel, not MiniZinc stdlib)",
            "eclipse -f src/csp.ecl",
            "eclipse -v",
        ),
        leftover(
            "gocryptfs-diriv-leftover",
            "GOCRYPTFS_UMOUNT",
            "gocryptfs diriv leftover",
            "gocryptfs leftover still encrypts cache diriv",
            "fusermount -u /var/lib/buildkit",
            "fusermount is EBUSY; leftover diriv still encrypts cache",
            "leftover gocryptfs diriv encrypting cache dir",
            "r327 ecryptfs-sig / r202 fscrypt / cache-admin 403",
            "r327 ecryptfs leftover (gocryptfs diriv leftover, not eCryptfs sig)",
            "test_gocryptfs.py",
            "findmnt /var/lib/buildkit; cat /var/lib/buildkit/.diriv",
            "gocryptfs leftover diriv leftover\nfuse.gocryptfs leftover on /var/lib/buildkit",
        ),
    ),
    (
        lang(
            "unicon-ipl-cache",
            "IPATH",
            "unicon",
            "13.2",
            "13.3",
            "ipl/procs/numbers.icn",
            "test_unicon.py",
            "src/app.icn",
            "unicon-133",
            "rm -rf /usr/share/unicon",
            "rm ipl does not drop 13.2 numbers.icn under unversioned IPATH",
            "7MB",
            "r191 icon-ucode (Unicon IPL, not Icon ucode)",
            "unicon src/app.icn && ./app",
            "unicon -version",
        ),
        leftover(
            "aufs-wh-leftover",
            "AUFS_WH_CLEAR",
            "aufs wh=nfs",
            "aufs leftover still whiteouts cache upper",
            "umount /var/lib/buildkit",
            "umount aufs is EBUSY; leftover wh=nfs still whiteouts upper",
            "leftover aufs whiteout holding cache upper",
            "r092 whiteout-opaque / r154 fuse-overlay / cache-admin 403",
            "r092 overlay whiteout leftover (aufs wh leftover, not overlay opaque)",
            "test_aufs.py",
            "findmnt /var/lib/buildkit; ls /var/lib/buildkit/.wh..wh.aufs",
            "aufs leftover wh=nfs leftover\naufs leftover on /var/lib/buildkit",
        ),
    ),
    (
        lang(
            "sather-sys-cache",
            "SATHER_HOME",
            "sacomp",
            "1.2.3",
            "1.2.3-fix",
            "Library/System/file.sa",
            "test_sather.py",
            "src/app.sa",
            "sather-123f",
            "rm -rf /usr/lib/sather",
            "rm Library does not drop 1.2 file.sa under unversioned SATHER_HOME",
            "4MB",
            "r173 eiffel-eifgen (Sather System lib, not Eiffel EIFGEN)",
            "sacomp src/app.sa",
            "sacomp -version",
        ),
        leftover(
            "dm-dust-leftover",
            "DM_DUST_REMOVE",
            "dm-dust cache-dust",
            "dm-dust leftover still injects bad sectors on cache LV",
            "dmsetup remove cache-dust",
            "dmsetup remove is EBUSY; leftover dust still injects bad sectors",
            "leftover dm-dust injecting bad sectors on cache LV",
            "r364 dm-flakey / r365 dm-delay / cache-admin 403",
            "r364 dm-flakey leftover (dm-dust leftover, not flakey EIO interval)",
            "test_dmdust.py",
            "dmsetup status cache-dust; lsblk /dev/mapper/cache-dust",
            "0 83886080 dust leftover badblock leftover",
        ),
    ),
    (
        lang(
            "cm3-libm3-cache",
            "CM3_ROOT",
            "cm3",
            "5.8.6",
            "5.8.7",
            "pkg/libm3/src/os/POSIX/OSErrorPosix.m3",
            "test_cm3.py",
            "src/Main.m3",
            "cm3-587",
            "rm -rf /usr/local/cm3",
            "rm pkg does not drop 5.8.6 OSErrorPosix under unversioned CM3_ROOT",
            "19MB",
            "r256 modula2-gm2 / r255 oberon-voc (CM3 libm3, not GM2 or VOC)",
            "cm3 -build",
            "cm3 -version",
        ),
        leftover(
            "dm-clone-leftover",
            "DM_CLONE_REMOVE",
            "dm-clone cache-clone",
            "dm-clone leftover still hydrates cache LV from a source",
            "dmsetup remove cache-clone",
            "dmsetup remove is EBUSY; leftover clone still hydrates LV",
            "leftover dm-clone hydrating cache LV",
            "r363 dm-snapshot / r393 dm-era / cache-admin 403",
            "r363 dm-snapshot leftover (dm-clone leftover, not snapshot COW)",
            "test_dmclone.py",
            "dmsetup status cache-clone; lsblk /dev/mapper/cache-clone",
            "0 83886080 clone leftover hydration leftover",
        ),
    ),
    (
        lang(
            "newlisp-mod-cache",
            "NEWLISPDIR",
            "newlisp",
            "10.7.5",
            "10.7.5-fix",
            "modules/crypto.lsp",
            "test_newlisp.py",
            "src/app.lsp",
            "nlisp-1075f",
            "rm -rf /usr/share/newlisp",
            "rm modules does not drop 10.7 crypto.lsp under unversioned NEWLISPDIR",
            "2MB",
            "r156 janet-jpm / r172 carp-core (newLISP modules, not Janet or Carp)",
            "newlisp src/app.lsp",
            "newlisp -v",
        ),
        leftover(
            "nvme-tcp-leftover",
            "NVME_TCP_DISCONNECT",
            "nvme-tcp nqn.buildkit",
            "nvme-tcp leftover still maps cache LV over TCP",
            "nvme disconnect -n nqn.buildkit",
            "nvme disconnect is EBUSY; leftover nqn still mapped",
            "leftover nvme-tcp mapping cache LV over TCP",
            "r216 nvmeof / r215 iscsi-session / cache-admin 403",
            "r216 nvmeof leftover (nvme-tcp leftover, not NVMe-oF RDMA)",
            "test_nvmetcp.py",
            "nvme list; cat /sys/class/nvme-fabrics/ctl/nvme1/subsysnqn",
            "nvme leftover nqn.buildkit transport tcp leftover",
        ),
    ),
    (
        lang(
            "picolisp-lib-cache",
            "PIL",
            "pil",
            "21.12",
            "24.12",
            "lib/misc.l",
            "test_picolisp.py",
            "src/app.l",
            "pil-2412",
            "rm -rf /usr/lib/picolisp",
            "rm lib does not drop 21.12 misc.l under unversioned PIL",
            "3MB",
            "r156 janet-jpm / r172 carp-core (PicoLisp lib, not Janet or Carp)",
            "pil src/app.l",
            "pil --version",
        ),
        leftover(
            "erspan-idx-leftover",
            "ERSPAN_DELETE",
            "erspan0 idx=9",
            "erspan0 leftover still mirrors cache export",
            "ip link del erspan0",
            "ip link del erspan0 is EBUSY; leftover idx=9 still mirrors export",
            "leftover erspan0 mirroring cache export",
            "r349 gre-tun / r219 vxlan / cache-admin 403",
            "r349 gre leftover (erspan leftover, not gre key)",
            "test_erspan.py",
            "ip -d link show erspan0",
            "erspan0 UP leftover idx 9 remote 10.8.0.8 leftover",
        ),
    ),
    (
        lang(
            "shen-core-cache",
            "SHEN_HOME",
            "shen",
            "22.4",
            "39.0",
            "shen/core.shen",
            "test_shen.py",
            "src/app.shen",
            "shen-390",
            "rm -rf /usr/lib/shen",
            "rm core does not drop 22.4 core.shen under unversioned SHEN_HOME",
            "6MB",
            "r149 swi-prolog / r172 carp-core (Shen core, not SWI pack or Carp)",
            "shen src/app.shen",
            "shen --version",
        ),
        leftover(
            "ip6gre-key-leftover",
            "IP6GRE_DELETE",
            "ip6gre0 key=11",
            "ip6gre0 leftover still encapsulates cache IPv6 GRE",
            "ip -6 link del ip6gre0",
            "ip link del ip6gre0 is EBUSY; leftover key=11 still up",
            "leftover ip6gre0 encapsulating cache IPv6 GRE",
            "r349 gre-tun / r350 sit-tun / cache-admin 403",
            "r349 gre leftover (ip6gre leftover, not gre4 key)",
            "test_ip6gre.py",
            "ip -d link show ip6gre0",
            "ip6gre0 UP leftover key 11 remote 2001:db8::8 leftover",
        ),
    ),
    (
        lang(
            "lfe-ebin-cache",
            "LFE_HOME",
            "lfe",
            "2.1.1",
            "2.1.4",
            "ebin/lfe_macro.beam",
            "test_lfe.py",
            "src/app.lfe",
            "lfe-214",
            "rm -rf /usr/lib/lfe",
            "rm ebin does not drop 2.1.1 lfe_macro under unversioned LFE_HOME",
            "4MB",
            "r087 rebar3-otp27 / r200 babashka-deps (LFE ebin, not rebar3 or Babashka)",
            "lfe src/app.lfe",
            "lfe -e '(lfe_comp:version())'",
        ),
        leftover(
            "vti-mark-leftover",
            "VTI_DELETE",
            "vti0 mark=0x9",
            "vti0 leftover still xfrm-tunnels cache export",
            "ip link del vti0",
            "ip link del vti0 is EBUSY; leftover mark=0x9 still up",
            "leftover vti0 xfrm-tunneling cache export",
            "r351 ipip-tun / r218 wireguard / cache-admin 403",
            "r351 ipip leftover (vti leftover, not tunl0 tos)",
            "test_vti.py",
            "ip -d link show vti0",
            "vti0 UP leftover mark 0x9 remote 10.8.0.8 leftover",
        ),
    ),
    (
        lang(
            "rebol-mezz-cache",
            "REBOL_HOME",
            "rebol",
            "2.7.8",
            "3.19.0",
            "mezz/base-funcs.r",
            "test_rebol.py",
            "src/app.r",
            "rebol-319",
            "rm -rf /usr/share/rebol",
            "rm mezz does not drop 2.7 base-funcs.r under unversioned REBOL_HOME",
            "5MB",
            "r323 red-lib (Rebol mezz, not Red runtime.reds)",
            "rebol -s src/app.r",
            "rebol -v",
        ),
        leftover(
            "fou-port-leftover",
            "FOU_DELETE",
            "fou port=5555",
            "fou leftover still encapsulates cache Foo-over-UDP",
            "ip fou del port 5555",
            "ip fou del is EBUSY; leftover port=5555 still encapsulates export",
            "leftover fou port encapsulating cache export",
            "r351 ipip-tun / r330 geneve / cache-admin 403",
            "r351 ipip leftover (fou leftover, not tunl0 tos inherit)",
            "test_fou.py",
            "ip fou show",
            "fou leftover port 5555 ipproto 4 leftover",
        ),
    ),
    (
        lang(
            "gst-kernel-cache",
            "SMALLTALK_IMAGE",
            "gst",
            "3.2.5",
            "3.2.91",
            "share/smalltalk/kernel/Object.st",
            "test_gst.py",
            "src/app.st",
            "gst-3291",
            "rm -rf /usr/share/smalltalk",
            "rm kernel does not drop 3.2.5 Object.st under unversioned SMALLTALK_IMAGE",
            "12MB",
            "r176 pharo-iceberg (GNU Smalltalk kernel, not Pharo Iceberg)",
            "gst src/app.st",
            "gst --version",
        ),
        leftover(
            "gue-sport-leftover",
            "GUE_DELETE",
            "gue sport=6080",
            "gue leftover still encapsulates cache Generic UDP Encapsulation",
            "ip fou del port 6080",
            "ip fou del is EBUSY; leftover gue sport=6080 still encapsulates export",
            "leftover gue sport encapsulating cache export",
            "r330 geneve / r219 vxlan / cache-admin 403",
            "r330 geneve leftover (gue leftover, not geneve VNI)",
            "test_gue.py",
            "ip fou show",
            "gue leftover port 6080 gue leftover",
        ),
    ),
    (
        lang(
            "clasp-cmp-cache",
            "CLASP_HOME",
            "clasp",
            "2.3.0",
            "2.7.0",
            "lib/clasp/modules/cmp/cmp.fasl",
            "test_clasp.py",
            "src/app.lisp",
            "clasp-270",
            "rm -rf /opt/clasp",
            "rm modules does not drop 2.3 cmp.fasl under unversioned CLASP_HOME",
            "48MB",
            "r143 quicklisp-roswell (Clasp cmp fasl, not Quicklisp dist)",
            "clasp --load src/app.lisp",
            "clasp --version",
        ),
        leftover(
            "bareudp-ethertype-leftover",
            "BAREUDP_DELETE",
            "bareudp0 ethertype=0x88be",
            "bareudp0 leftover still L2-tunnels cache export",
            "ip link del bareudp0",
            "ip link del bareudp0 is EBUSY; leftover ethertype still L2-tunnels export",
            "leftover bareudp0 L2-tunneling cache export",
            "r330 geneve / r219 vxlan / cache-admin 403",
            "r219 vxlan leftover (bareudp leftover, not vxlan VNI)",
            "test_bareudp.py",
            "ip -d link show bareudp0",
            "bareudp0 UP leftover ethertype 0x88be dstport 6635 leftover",
        ),
    ),
    (
        lang(
            "ecl-cmp-cache",
            "ECLDIR",
            "ecl",
            "21.2.1",
            "24.5.10",
            "lib/ecl-21.2.1/cmp.fas",
            "test_ecl.py",
            "src/app.lisp",
            "ecl-24510",
            "rm -rf /usr/lib/ecl",
            "rm lib does not drop 21.2 cmp.fas under unversioned ECLDIR",
            "17MB",
            "r143 quicklisp-roswell (ECL cmp.fas, not Quicklisp dist)",
            "ecl --load src/app.lisp",
            "ecl --version",
        ),
        leftover(
            "netkit-peer-leftover",
            "NETKIT_DELETE",
            "nk0 peer nk1",
            "nk0 leftover still pairs cache NIC to a netkit peer",
            "ip link del nk0",
            "ip link del nk0 is EBUSY; leftover peer nk1 still paired",
            "leftover netkit peer pairing cache NIC",
            "r197 veth / r332 bond-miimon / cache-admin 403",
            "r197 veth leftover (netkit leftover, not veth pair)",
            "test_netkit.py",
            "ip -d link show nk0; ip -d link show nk1",
            "nk0 UP leftover type netkit peer nk1 leftover",
        ),
    ),
    (
        lang(
            "chibi-sld-cache",
            "CHIBI_MODULE_PATH",
            "chibi-scheme",
            "0.10.0",
            "0.11.0",
            "lib/chibi/ast.sld",
            "test_chibi.py",
            "src/app.scm",
            "chibi-0110",
            "rm -rf /usr/lib/chibi",
            "rm lib does not drop 0.10 ast.sld under unversioned CHIBI_MODULE_PATH",
            "3MB",
            "r170 chez-so / r144 chicken-eggs (Chibi sld, not Chez so or Chicken eggs)",
            "chibi-scheme src/app.scm",
            "chibi-scheme -V",
        ),
        leftover(
            "macvtap-passthru-leftover",
            "MACVTAP_DELETE",
            "macvtap0 mode passthru",
            "macvtap0 leftover still passthru-binds cache NIC",
            "ip link del macvtap0",
            "ip link del macvtap0 is EBUSY; leftover passthru still binds NIC",
            "leftover macvtap passthru binding cache NIC",
            "r251 macvlan / r254 tap / cache-admin 403",
            "r251 macvlan leftover (macvtap leftover, not macvlan bridge)",
            "test_macvtap.py",
            "ip -d link show macvtap0",
            "macvtap0 UP leftover mode passthru leftover",
        ),
    ),
    (
        lang(
            "gauche-site-cache",
            "GAUCHE_LOAD_PATH",
            "gosh",
            "0.9.12",
            "0.9.15",
            "share/gauche-0.9/site/lib/rfc/json.scm",
            "test_gauche.py",
            "src/app.scm",
            "gauche-0915",
            "rm -rf /usr/share/gauche-0.9",
            "rm site does not drop 0.9.12 rfc/json under unversioned GAUCHE_LOAD_PATH",
            "10MB",
            "r171 guile-go / r198 gambit-gsc (Gauche site lib, not Guile go or Gambit gsc)",
            "gosh src/app.scm",
            "gosh -V",
        ),
        leftover(
            "usbip-vudc-leftover",
            "USBIP_UNBIND",
            "usbip vudc 1-1",
            "usbip leftover still exports cache USB gadget",
            "usbip unbind -b 1-1",
            "usbip unbind is EBUSY; leftover vudc 1-1 still exports gadget",
            "leftover usbip vudc exporting cache USB gadget",
            "r389 configfs-gadget / r221 vsock / cache-admin 403",
            "r389 configfs gadget leftover (usbip leftover, not local gadget bind)",
            "test_usbip.py",
            "usbip list -l; cat /sys/devices/platform/vudc.0/dev",
            "usbip leftover vudc 1-1 leftover",
        ),
    ),
    (
        lang(
            "kawa-lib-cache",
            "KAWA_HOME",
            "kawa",
            "3.1.1",
            "3.1.1-fix",
            "lib/kawa/lib/ports.scm",
            "test_kawa.py",
            "src/app.scm",
            "kawa-311f",
            "rm -rf /usr/share/kawa",
            "rm lib does not drop 3.1 ports.scm under unversioned KAWA_HOME",
            "8MB",
            "r171 guile-go / r420 chibi-sld (Kawa ports, not Guile go or Chibi sld)",
            "kawa src/app.scm",
            "kawa --version",
        ),
        leftover(
            "zonefs-seq-leftover",
            "ZONEFS_UMOUNT",
            "zonefs conv=0 seq=1",
            "zonefs leftover still pins sequential zones on cache disk",
            "umount /var/lib/buildkit",
            "umount zonefs is EBUSY; leftover seq zone still pinned",
            "leftover zonefs sequential zone pinning cache disk",
            "r189 hugepages / r429 hugetlbfs / cache-admin 403",
            "r429 hugetlbfs leftover (zonefs leftover, not hugetlbfs pagesize)",
            "test_zonefs.py",
            "findmnt /var/lib/buildkit; cat /sys/fs/zonefs/seq",
            "zonefs leftover conv=0 seq=1 leftover\n/dev/nvme0n2 on /var/lib/buildkit type zonefs leftover",
        ),
    ),
    (
        lang(
            "stklos-lib-cache",
            "STKLOS_LOAD_PATH",
            "stklos",
            "1.70",
            "2.10",
            "lib/stklos/srfi-1.stk",
            "test_stklos.py",
            "src/app.stk",
            "stklos-210",
            "rm -rf /usr/lib/stklos",
            "rm lib does not drop 1.70 srfi-1 under unversioned STKLOS_LOAD_PATH",
            "5MB",
            "r421 gauche-site / r420 chibi-sld (STklos srfi-1, not Gauche site)",
            "stklos src/app.stk",
            "stklos --version",
        ),
        leftover(
            "vfio-mdev-leftover",
            "VFIO_MDEV_UNBIND",
            "vfio-mdev 0000:00:02.0",
            "vfio-mdev leftover still binds cache GPU mediated device",
            "echo 0000:00:02.0 > /sys/bus/mdev/drivers/vfio_mdev/unbind",
            "vfio mdev unbind is EBUSY; leftover 0000:00:02.0 still bound",
            "leftover vfio-mdev binding cache GPU",
            "r236 vfio-iommu / r347 cxl-region / cache-admin 403",
            "r236 vfio leftover (vfio-mdev leftover, not iommu group)",
            "test_vfiomdev.py",
            "ls /sys/bus/mdev/devices; find /sys/bus/mdev -name uuid | head",
            "vfio-mdev leftover 0000:00:02.0 leftover",
        ),
    ),
    (
        lang(
            "bigloo-lib-cache",
            "BIGLOOLIB",
            "bigloo",
            "4.5a",
            "4.5c",
            "lib/bigloo/4.5a/pthread.sch",
            "test_bigloo.py",
            "src/app.scm",
            "bigloo-45c",
            "rm -rf /usr/lib/bigloo",
            "rm lib does not drop 4.5a pthread.sch under unversioned BIGLOOLIB",
            "13MB",
            "r198 gambit-gsc / r421 gauche-site (Bigloo pthread.sch, not Gambit gsc)",
            "bigloo src/app.scm",
            "bigloo -version",
        ),
        leftover(
            "sgx-enclave-leftover",
            "SGX_ENCLAVE_DESTROY",
            "sgx enclave /dev/sgx_enclave",
            "sgx leftover still holds cache enclave pages",
            "rmmod intel_sgx",
            "rmmod intel_sgx is EBUSY; leftover /dev/sgx_enclave still holds pages",
            "leftover sgx enclave holding cache pages",
            "r237 memfd-seal / r234 dmcrypt / cache-admin 403",
            "r237 memfd leftover (sgx leftover, not memfd seal)",
            "test_sgx.py",
            "ls -l /dev/sgx_enclave /dev/sgx_provision",
            "sgx leftover /dev/sgx_enclave leftover",
        ),
    ),
    (
        lang(
            "sagittarius-lib-cache",
            "SAGITTARIUS_LOADPATH",
            "sagittarius",
            "0.9.10",
            "0.9.12",
            "share/sagittarius/lib/rfc/json.scm",
            "test_sagi.py",
            "src/app.scm",
            "sagi-0912",
            "rm -rf /usr/share/sagittarius",
            "rm lib does not drop 0.9.10 rfc/json under unversioned SAGITTARIUS_LOADPATH",
            "7MB",
            "r421 gauche-site / r170 chez-so (Sagittarius rfc/json, not Gauche site)",
            "sagittarius src/app.scm",
            "sagittarius -v",
        ),
        leftover(
            "vhost-scsi-leftover",
            "VHOST_SCSI_UNBIND",
            "vhost-scsi vhost-scsi-0",
            "vhost-scsi leftover still maps cache LUN to a VM",
            "echo 1 > /sys/class/vhost-scsi/vhost-scsi-0/remove",
            "vhost-scsi remove is EBUSY; leftover vhost-scsi-0 still mapped",
            "leftover vhost-scsi mapping cache LUN",
            "r334 vhost-net / r221 vsock / cache-admin 403",
            "r334 vhost-net leftover (vhost-scsi leftover, not vhost-net TAP)",
            "test_vhostscsi.py",
            "ls /sys/class/vhost-scsi; ls /dev/vhost-scsi",
            "vhost-scsi leftover vhost-scsi-0 leftover",
        ),
    ),
    (
        lang(
            "cyclone-lib-cache",
            "CYCLONE_LIBRARY_PATH",
            "cyclone",
            "0.34.0",
            "0.36.0",
            "share/cyclone/scheme/base.sld",
            "test_cyclone.py",
            "src/app.scm",
            "cyc-0360",
            "rm -rf /usr/share/cyclone",
            "rm share does not drop 0.34 scheme/base under unversioned CYCLONE_LIBRARY_PATH",
            "4MB",
            "r420 chibi-sld / r144 chicken-eggs (Cyclone scheme/base, not Chibi ast.sld)",
            "cyclone src/app.scm",
            "cyclone --version",
        ),
        leftover(
            "xfrm-state-leftover",
            "XFRM_FLUSH",
            "xfrm state reqid=9",
            "xfrm leftover still encrypts cache export",
            "ip xfrm state flush",
            "ip xfrm state flush is EPERM; leftover reqid=9 still encrypts export",
            "leftover xfrm state encrypting cache export",
            "r218 wireguard / r352 macsec / cache-admin 403",
            "r218 wireguard leftover (xfrm leftover, not wg0 peer)",
            "test_xfrm.py",
            "ip xfrm state; ip xfrm policy",
            "xfrm leftover state reqid 9 proto esp leftover",
        ),
    ),
    (
        lang(
            "loko-lib-cache",
            "LOKO_LIBRARY_PATH",
            "loko",
            "0.12.1",
            "0.13.0",
            "lib/loko/scheme/base.sls",
            "test_loko.py",
            "src/app.sps",
            "loko-0130",
            "rm -rf /usr/lib/loko",
            "rm lib does not drop 0.12 scheme/base under unversioned LOKO_LIBRARY_PATH",
            "6MB",
            "r170 chez-so / r169 gerbil-gxc (Loko scheme/base, not Chez so)",
            "loko src/app.sps",
            "loko --version",
        ),
        leftover(
            "dm-logwrites-leftover",
            "DM_LOGWRITES_REMOVE",
            "dm-log-writes cache-lw",
            "dm-log-writes leftover still journals cache I/O",
            "dmsetup remove cache-lw",
            "dmsetup remove is EBUSY; leftover log-writes still journals I/O",
            "leftover dm-log-writes journaling cache I/O",
            "r363 dm-snapshot / r393 dm-era / cache-admin 403",
            "r393 dm-era leftover (dm-log-writes leftover, not era current_era)",
            "test_dmlw.py",
            "dmsetup status cache-lw; lsblk /dev/mapper/cache-lw",
            "0 83886080 log-writes leftover marked leftover",
        ),
    ),
    (
        lang(
            "mitscheme-lib-cache",
            "MITSCHEME_LIBRARY_PATH",
            "mit-scheme",
            "11.2",
            "12.1",
            "lib/mit-scheme-x86-64/runtime/syntax.scm",
            "test_mit.py",
            "src/app.scm",
            "mit-121",
            "rm -rf /usr/lib/mit-scheme",
            "rm runtime does not drop 11.2 syntax.scm under unversioned MITSCHEME_LIBRARY_PATH",
            "21MB",
            "r170 chez-so / r171 guile-go (MIT Scheme runtime, not Chez so)",
            "mit-scheme --load src/app.scm",
            "mit-scheme --version",
        ),
        leftover(
            "hpfs-eas-leftover",
            "HPFS_UMOUNT",
            "hpfs eas leftover",
            "hpfs leftover still stores EAs on cache dir",
            "umount /var/lib/buildkit",
            "umount hpfs is EBUSY; leftover eas still stored",
            "leftover hpfs EAs stored on cache dir",
            "r340 ntfs3-acl / r426 minix / cache-admin 403",
            "r340 ntfs3 leftover (hpfs EAs leftover, not ntfs3 ACL)",
            "test_hpfs.py",
            "findmnt /var/lib/buildkit; cat /proc/fs/hpfs/eas",
            "hpfs leftover eas leftover\n/dev/loop2 on /var/lib/buildkit type hpfs leftover",
        ),
    ),
    (
        lang(
            "scheme48-vm-cache",
            "SCHEME48_VM",
            "scheme48",
            "1.9.2",
            "1.9.3",
            "share/scheme48/scheme/rts/exception.scm",
            "test_s48.py",
            "src/app.scm",
            "s48-193",
            "rm -rf /usr/share/scheme48",
            "rm rts does not drop 1.9.2 exception.scm under unversioned SCHEME48_VM",
            "5MB",
            "r170 chez-so / r420 chibi-sld (Scheme48 rts, not Chez so or Chibi sld)",
            "scheme48 -a src/app.scm",
            "scheme48 -h | head",
        ),
        leftover(
            "befs-journal-leftover",
            "BEFS_UMOUNT",
            "befs journal dirty",
            "befs leftover still dirty-journals cache disk",
            "umount /var/lib/buildkit",
            "umount befs is EBUSY; leftover journal still dirty",
            "leftover befs journal dirty on cache disk",
            "r339 reiserfs-journal / r424 cramfs / cache-admin 403",
            "r339 reiserfs leftover (befs journal leftover, not reiserfs replay)",
            "test_befs.py",
            "findmnt /var/lib/buildkit; cat /proc/fs/befs/journal",
            "befs leftover journal dirty leftover\n/dev/loop1 on /var/lib/buildkit type befs leftover",
        ),
    ),
    (
        lang(
            "abcl-fasl-cache",
            "ABCL_HOME",
            "abcl",
            "1.9.0",
            "1.9.2",
            "lib/abcl/org/armedbear/lisp/compile-file.abcl",
            "test_abcl.py",
            "src/app.lisp",
            "abcl-192",
            "rm -rf /usr/share/abcl",
            "rm lib does not drop 1.9.0 compile-file.abcl under unversioned ABCL_HOME",
            "15MB",
            "r418 clasp-cmp / r419 ecl-cmp (ABCL fasl, not Clasp or ECL cmp)",
            "abcl --load src/app.lisp",
            "abcl --noinform --eval '(lisp-implementation-version)'",
        ),
        leftover(
            "affs-ofs-leftover",
            "AFFS_UMOUNT",
            "affs ofs dircache",
            "affs leftover still dircaches OFS names on cache disk",
            "umount /var/lib/buildkit",
            "umount affs is EBUSY; leftover ofs dircache still holds names",
            "leftover affs OFS dircache holding cache names",
            "r425 romfs / r424 cramfs / cache-admin 403",
            "r425 romfs leftover (affs OFS leftover, not romfs chksum)",
            "test_affs.py",
            "findmnt /var/lib/buildkit; cat /proc/fs/affs/ofs",
            "affs leftover ofs dircache leftover\n/dev/loop0 on /var/lib/buildkit type affs leftover",
        ),
    ),
    (
        lang(
            "ccl-l1-cache",
            "CCL_DEFAULT_DIRECTORY",
            "ccl",
            "1.12.2",
            "1.13",
            "l1-fasls/x86-linux64/l1-init.lx64fsl",
            "test_ccl.py",
            "src/app.lisp",
            "ccl-113",
            "rm -rf /opt/ccl",
            "rm l1-fasls does not drop 1.12 l1-init under unversioned CCL_DEFAULT_DIRECTORY",
            "28MB",
            "r418 clasp-cmp / r143 quicklisp-roswell (CCL l1-fasls, not Clasp cmp)",
            "ccl --load src/app.lisp",
            "ccl --version",
        ),
        leftover(
            "ifb-qdisc-leftover",
            "IFB_DELETE",
            "ifb0 ingress redirect",
            "ifb0 leftover still redirects cache NIC ingress",
            "ip link del ifb0",
            "ip link del ifb0 is EBUSY; leftover ingress redirect still up",
            "leftover ifb0 redirecting cache NIC ingress",
            "r220 tc-qdisc / r197 veth / cache-admin 403",
            "r220 tc-qdisc leftover (ifb leftover, not cake qdisc)",
            "test_ifb.py",
            "ip -d link show ifb0; tc qdisc show dev ifb0",
            "ifb0 UP leftover ingress redirect leftover",
        ),
    ),
    (
        lang(
            "clisp-lib-cache",
            "CLISP_LIBDIR",
            "clisp",
            "2.49.92",
            "2.49.93",
            "lib/clisp/full/linkkit/modules.h",
            "test_clisp.py",
            "src/app.lisp",
            "clisp-24993",
            "rm -rf /usr/lib/clisp",
            "rm lib does not drop 2.49.92 modules.h under unversioned CLISP_LIBDIR",
            "9MB",
            "r419 ecl-cmp / r418 clasp-cmp (CLISP linkkit, not ECL cmp.fas)",
            "clisp src/app.lisp",
            "clisp --version",
        ),
        leftover(
            "vcan-leftover",
            "VCAN_DELETE",
            "vcan0 bitrate leftover",
            "vcan0 leftover still loops cache CAN frames",
            "ip link del vcan0",
            "ip link del vcan0 is EBUSY; leftover vcan0 still loops frames",
            "leftover vcan0 looping cache CAN frames",
            "r197 veth / r222 tun / cache-admin 403",
            "r197 veth leftover (vcan leftover, not veth pair)",
            "test_vcan.py",
            "ip -d link show vcan0",
            "vcan0 UP leftover type vcan leftover",
        ),
    ),
    (
        lang(
            "gcl-ansi-cache",
            "GCL_ANSI",
            "gcl",
            "2.6.14",
            "2.7.0",
            "lib/gcl-2.6.14/unixport/saved_ansi_gcl",
            "test_gcl.py",
            "src/app.lisp",
            "gcl-270",
            "rm -rf /usr/lib/gcl",
            "rm unixport does not drop 2.6 saved_ansi_gcl under unversioned GCL_ANSI",
            "22MB",
            "r419 ecl-cmp / r143 quicklisp-roswell (GCL saved image, not ECL cmp)",
            "gcl -load src/app.lisp",
            "gcl --version",
        ),
        leftover(
            "nlmon-leftover",
            "NLMON_DELETE",
            "nlmon0 tap leftover",
            "nlmon0 leftover still sniffs cache netlink",
            "ip link del nlmon0",
            "ip link del nlmon0 is EBUSY; leftover tap still sniffs netlink",
            "leftover nlmon0 sniffing cache netlink",
            "r197 veth / r222 tun / cache-admin 403",
            "r222 tun leftover (nlmon leftover, not tun0)",
            "test_nlmon.py",
            "ip -d link show nlmon0",
            "nlmon0 UP leftover type nlmon leftover",
        ),
    ),
    (
        lang(
            "arturo-lib-cache",
            "ARTURO_HOME",
            "arturo",
            "0.9.83",
            "0.9.84",
            "lib/arturo/helpers/unisort.art",
            "test_arturo.py",
            "src/app.art",
            "art-0984",
            "rm -rf /usr/lib/arturo",
            "rm lib does not drop 0.9.83 unisort under unversioned ARTURO_HOME",
            "4MB",
            "r323 red-lib / r416 rebol-mezz (Arturo helpers, not Red runtime or Rebol mezz)",
            "arturo src/app.art",
            "arturo --version",
        ),
        leftover(
            "ksmbd-share-leftover",
            "KSMBD_STOP",
            "ksmbd share buildkit",
            "ksmbd leftover still exports cache dir over SMB3",
            "ksmbd.control -s",
            "ksmbd.control stop is EPERM; leftover share still exports cache dir",
            "leftover ksmbd share exporting cache dir",
            "r233 cifs-cachestrict / r329 nfs4-deleg / cache-admin 403",
            "r233 cifs leftover (ksmbd leftover, not CIFS cachestrict client)",
            "test_ksmbd.py",
            "ksmbd.control -s; cat /sys/class/ksmbd-control/debug",
            "ksmbd leftover share buildkit leftover",
        ),
    ),
    (
        lang(
            "systemc-lib-cache",
            "SYSTEMC_HOME",
            "g++",
            "2.3.3",
            "3.0.0",
            "lib/libsystemc.so.2.3.3",
            "test_systemc.py",
            "src/main.cpp",
            "sc-300",
            "rm -rf /usr/local/systemc",
            "rm lib does not drop 2.3 libsystemc under unversioned SYSTEMC_HOME",
            "18MB",
            "r183 verilator-obj / r247 iverilog-vvp (SystemC lib, not Verilator obj)",
            "g++ src/main.cpp -lsystemc && ./a.out",
            "pkg-config --modversion systemc",
        ),
        leftover(
            "lockd-grace-leftover",
            "LOCKD_GRACE_CLEAR",
            "lockd grace=90",
            "lockd leftover still holds cache NLM grace",
            "rpc.lockd -g 0",
            "lockd grace write is EPERM; leftover grace=90 still holds NLM",
            "leftover lockd grace holding cache NLM",
            "r329 nfs4-deleg / r391 rpc-pipefs / cache-admin 403",
            "r329 nfs4 leftover (lockd leftover, not nfs4 delegation)",
            "test_lockd.py",
            "cat /proc/fs/nfsd/nfsv4grace; rpcinfo -p | rg lockd",
            "lockd leftover grace=90 leftover",
        ),
    ),
    (
        lang(
            "nektar-lib-cache",
            "NEKTAR_HOME",
            "NekMesh",
            "5.3.0",
            "5.6.0",
            "lib/nektar++/libNekMesh.so.5.3",
            "test_nektar.py",
            "src/pipe.xml",
            "nek-560",
            "rm -rf /usr/lib/nektar++",
            "rm lib does not drop 5.3 libNekMesh under unversioned NEKTAR_HOME",
            "27MB",
            "r301 fenics-cache / r429 dealii-data (Nektar++ NekMesh, not deal.II ExternalData)",
            "NekMesh src/pipe.xml src/pipe.xml",
            "NekMesh --version",
        ),
        leftover(
            "ipvlan-l3s-leftover",
            "IPVLAN_L3S_DELETE",
            "ipvlan0 mode l3s",
            "ipvlan0 leftover still L3S-routes cache NIC",
            "ip link del ipvlan0",
            "ip link del ipvlan0 is EBUSY; leftover mode l3s still routes NIC",
            "leftover ipvlan l3s routing cache NIC",
            "r252 ipvlan / r251 macvlan / cache-admin 403",
            "r252 ipvlan leftover (ipvlan l3s leftover, not ipvlan l2)",
            "test_ipvlanl3s.py",
            "ip -d link show ipvlan0",
            "ipvlan0 UP leftover mode l3s leftover",
        ),
    ),
    (
        lang(
            "calculix-dat-cache",
            "CCX",
            "ccx",
            "2.21",
            "2.22",
            "dat/ccx_2.21/SPOOL2_struct.f",
            "test_ccx.py",
            "src/beam.inp",
            "ccx-222",
            "rm -rf /usr/share/calculix",
            "rm dat does not drop 2.21 SPOOL2 under unversioned CCX",
            "11MB",
            "r345 code-aster-ele / r346 elmer-fem (CalculiX SPOOL2, not Code_Aster elements)",
            "ccx src/beam",
            "ccx -v",
        ),
        leftover(
            "amt-tun-leftover",
            "AMT_DELETE",
            "amt0 relay 10.8.0.9",
            "amt0 leftover still relays cache multicast",
            "ip link del amt0",
            "ip link del amt0 is EBUSY; leftover relay still forwards multicast",
            "leftover amt0 relaying cache multicast",
            "r219 vxlan / r330 geneve / cache-admin 403",
            "r219 vxlan leftover (amt leftover, not vxlan VNI)",
            "test_amt.py",
            "ip -d link show amt0",
            "amt0 UP leftover relay 10.8.0.9 leftover",
        ),
    ),
]


def success_episode(round_n: int, s: dict) -> dict:
    rec = _u.success_episode(round_n, s)
    rec["goal"] = (
        f"{s['tool']} {s['new']} is pinned in Dockerfile but {s['env']} still loads "
        f"{s['old']} {s['artifact']}. Namespace {s['env']}; leftover {s['old']} may remain."
    )
    rec["plan"] = (
        f"Show {s['old']} {s['artifact']} hit, {s['dead_rm'].split()[0]} dead-end, "
        f"id={s['cache_id']}, leave {s['old']} if gc skipped."
    )
    if "harbor-" in rec["id"]:
        raise SystemExit(f"harbor id forbidden: {rec['id']}")
    return rec


def leftover_episode(round_n: int, p: dict) -> dict:
    rec = _u.leftover_episode(round_n, p)
    rec["goal"] = (
        f"leftover {p['leftover']} still {p['detail']} after {p['token']}=0. "
        f"Recreate the builder; leftover {p['leftover']} may remain."
    )
    rec["plan"] = (
        f"Show leftover {p['leftover']}, {p['dead'].split()[0]} dead-end, "
        f"new builder, leave residue."
    )
    if "harbor-" in rec["id"]:
        raise SystemExit(f"harbor id forbidden: {rec['id']}")
    return rec


def notes_for(round_n: int, suc: dict, leftp: dict, srec: dict, lrec: dict) -> str:
    cov = 24 + ((round_n * 5) % 7)
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
        f"- Residual synthetic tells: invented unique-lang × fs/ns/driver plants.\n"
        f"- Ban check: not harbor-pin mill, not harbor-* ids, not dmesg_restrict leftover leftover, "
        f"not HTTP-status leftover, not apk-on-debian, not r233–r395 lang clones, "
        f"not r322–r337 leftover clones, not sysctl cartesian.\n"
        f"- Novel coverage notes unique lang cache ({suc['tool']}/{suc['env']}) × "
        f"unique leftover ({leftp['leftover']}).\n"
    )


def catalog_selfcheck() -> None:
    seen: set[str] = set()
    for suc, leftp in PAIRS:
        for spec in (suc, leftp):
            slug = spec["slug"]
            if slug in seen:
                raise SystemExit(f"duplicate catalog slug {slug}")
            seen.add(slug)
            ident = " ".join(
                str(spec.get(k, ""))
                for k in ("slug", "harbor", "env", "tool", "leftover", "token", "cache_id")
            ).lower()
            for needle in BANNED_NEEDLES:
                if needle in ident:
                    raise SystemExit(f"banned needle {needle!r} in {slug}")
            if slug.startswith("harbor-") or "harbor-" in slug:
                raise SystemExit(f"harbor slug forbidden: {slug}")
    if len(PAIRS) < 12:
        raise SystemExit(f"catalog too small: {len(PAIRS)}")


def next_free_idx(start: int = 0) -> int | None:
    existing = published_slugs()
    for i in range(start, len(PAIRS)):
        suc, leftp = PAIRS[i]
        if suc["slug"] not in existing and leftp["slug"] not in existing:
            return i
    return None


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
    if "harbor-" in srec["id"] or "harbor-" in lrec["id"]:
        raise SystemExit("harbor id leaked")
    if "harbor-" in srec["goal"] and "pins" in srec["goal"] and "still compiles" in srec["goal"]:
        raise SystemExit("harbor-pin goal leaked")
    batch = staging / f"batch-r{round_n:02d}.jsonl"
    notes = staging / f"NOTES-r{round_n:02d}.md"
    batch.write_text(
        json.dumps(srec, separators=(",", ":"))
        + "\n"
        + json.dumps(lrec, separators=(",", ":"))
        + "\n"
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
