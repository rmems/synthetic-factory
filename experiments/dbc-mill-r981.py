#!/usr/bin/env python3
"""Mill docker-build-cache-factory r981+. DB engines × I2C/SPI/WDT leftovers.

NEW unique-pair catalog after r933 crypto/GPIO.
BAN prior DBC catalogs, r645 nerdctl, r549 scsh/scsi, GNU Prolog/landlock/
SWI pack/seccomp/AppArmor/GOTOOLCHAIN, harbor-pin, leftover×sysctl.
17+18 steps. meta.generator=grok-4.6.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("dbc_mill_r933", HERE / "dbc-mill-r933.py")
_m = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_m)

FACTORY = _m.FACTORY
GEN = _m.GEN
lang = _m.lang
leftover = _m.leftover
success_episode = _m.success_episode
leftover_episode = _m.leftover_episode
notes_for = _m.notes_for
slug_taken = _m.slug_taken
BANNED_NEEDLES = _m.BANNED_NEEDLES + (
    "botan-cache",
    "pca953x-leftover",
    "sphinxbase-cache",
    "coretemp-leftover",
)

# slug, env, tool, old, new, artifact, mb
_CRYPTO = [
    ("duckdb-httpfs-cache", "DUCKDB_HOME", "duckdb", "1.1.3", "1.2.1", "share/duckdb/extensions/httpfs.duckdb_extension", "12MB"),
    ("lmdb-cache", "LMDB_HOME", "mdb_stat", "0.9.31", "0.9.33", "include/lmdb.h", "1MB"),
    ("wiredtiger-cache", "WIREDTIGER_HOME", "wt", "11.2.0", "11.3.1", "include/wiredtiger.h", "5MB"),
    ("rocksdb-cache", "ROCKSDB_HOME", "ldb", "9.1.1", "9.7.3", "include/rocksdb/db.h", "8MB"),
    ("leveldb-cache", "LEVELDB_HOME", "leveldbutil", "1.23", "1.23-post", "include/leveldb/db.h", "2MB"),
    ("unqlite-cache", "UNQLITE_HOME", "unqlite", "1.1.9", "1.1.9-post", "include/unqlite.h", "1MB"),
    ("sophia-db-cache", "SOPHIA_HOME", "sophia", "2.2", "2.2-post", "include/sophia.h", "1MB"),
    ("vedis-cache", "VEDIS_HOME", "vedis", "1.2.6", "1.2.6-post", "include/vedis.h", "1MB"),
    ("ejdb-cache", "EJDB_HOME", "jbs", "2.73", "2.74", "include/ejdb2/ejdb2.h", "3MB"),
    ("tkrzw-cache", "TKRZW_HOME", "tkrzw_dbm_util", "1.0.32", "1.0.32-post", "include/tkrzw_dbm.h", "2MB"),
    ("kyotocabinet-cache", "KC_HOME", "kchashmgr", "1.2.80", "1.2.80-post", "include/kchashdb.h", "3MB"),
    ("tokyocabinet-cache", "TC_HOME", "tchmgr", "1.4.48", "1.4.48-post", "include/tcutil.h", "2MB"),
    ("gdbm-cache", "GDBM_HOME", "gdbmtool", "1.23", "1.24", "include/gdbm.h", "1MB"),
    ("qdbm-cache", "QDBM_HOME", "dpmgr", "1.8.78", "1.8.78-post", "include/depot.h", "1MB"),
    ("tinycdb-cache", "TINYCDB_HOME", "cdb", "0.78", "0.81", "include/cdb.h", "1MB"),
    ("bdb-cache", "DB_HOME", "db_stat", "18.1.40", "18.1.40-post", "include/db.h", "6MB"),
    ("lmdbxx-cache", "LMDBXX_HOME", "lmdb++", "1.0.0", "1.0.0-post", "include/lmdb++.h", "1MB"),
    ("forestdb-cache", "FORESTDB_HOME", "forestdb", "1.2", "1.3", "include/libforestdb/forestdb.h", "4MB"),
    ("percona-ft-cache", "TOKUFT_HOME", "tokuftdump", "8.0.0", "8.0.0-post", "include/ft/ft-internal.h", "7MB"),
    ("upscaledb-cache", "UPS_HOME", "ups_bench", "2.2.1", "2.2.1-post", "include/ups/upscaledb.h", "3MB"),
    ("hamsterdb-cache", "HAM_HOME", "ham_info", "2.1.11", "2.2.0", "include/ham/hamsterdb.h", "3MB"),
    ("sophia-set-cache", "SOPHIA_SET", "sophia-set", "1.2", "1.2-post", "share/sophia/set.conf", "1MB"),
    ("rethinkdb-data-cache", "RETHINKDB_HOME", "rethinkdb", "2.4.3", "2.4.4", "share/rethinkdb/default-configs", "9MB"),
    ("foundationdb-cache", "FDB_CLUSTER_FILE", "fdbcli", "7.1.43", "7.3.43", "share/foundationdb/foundationdb.conf", "11MB"),
    ("tikv-cache", "TIKV_HOME", "tikv-server", "8.1.0", "8.5.0", "share/tikv/config.toml", "14MB"),
    ("badger-cache", "BADGER_HOME", "badger", "4.2.0", "4.5.0", "share/badger/badger.1", "3MB"),
    ("bolt-db-cache", "BOLT_HOME", "boltdb", "1.3.1", "1.4.0", "share/bolt/bolt.1", "2MB"),
    ("bbolt-cache", "BBOLT_HOME", "bbolt", "1.3.10", "1.4.0", "share/bbolt/bbolt.1", "2MB"),
    ("pebble-cache", "PEBBLE_HOME", "pebble", "1.1.2", "1.1.3", "share/pebble/pebble.1", "4MB"),
    ("redict-cache", "REDICT_HOME", "redict-server", "7.3.0", "7.3.5", "share/redict/redict.conf", "5MB"),
    ("keydb-cache", "KEYDB_HOME", "keydb-server", "6.3.4", "6.3.4-post", "share/keydb/keydb.conf", "6MB"),
    ("valkey-cache", "VALKEY_HOME", "valkey-server", "8.0.1", "8.1.0", "share/valkey/valkey.conf", "5MB"),
    ("dragonfly-cache", "DFLY_HOME", "dragonfly", "1.21.2", "1.27.0", "share/dragonfly/dragonfly.conf", "8MB"),
    ("kvrocks-cache", "KVROCKS_HOME", "kvrocks", "2.9.0", "2.11.1", "share/kvrocks/kvrocks.conf", "7MB"),
    ("ssdb-cache", "SSDB_HOME", "ssdb-server", "1.9.9", "1.9.9-post", "share/ssdb/ssdb.conf", "4MB"),
    ("ledisdb-cache", "LEDIS_HOME", "ledis-server", "0.6", "0.6-post", "share/ledisdb/ledis.conf", "3MB"),
    ("codis-cache", "CODIS_HOME", "codis-server", "3.2.2", "3.2.2-post", "share/codis/config.ini", "4MB"),
    ("tendis-cache", "TENDIS_HOME", "tendisplus", "2.6.0", "2.8.0", "share/tendisplus/tendisplus.conf", "6MB"),
    ("pika-cache", "PIKA_HOME", "pika", "3.5.2", "3.5.5", "share/pika/pika.conf", "5MB"),
    ("kvstore-cache", "KVSTORE_HOME", "kvstore", "1.0", "1.1", "share/kvstore/kvstore.conf", "2MB"),
    ("sled-cache", "SLED_HOME", "sled", "0.34.7", "0.34.7-post", "share/sled/sled.1", "3MB"),
    ("redb-cache", "REDB_HOME", "redb", "2.1.3", "2.4.0", "share/redb/redb.1", "2MB"),
    ("heed-cache", "HEED_HOME", "heed", "0.20.5", "0.21.0", "share/heed/heed.1", "2MB"),
    ("fjall-cache", "FJALL_HOME", "fjall", "2.4.0", "2.6.0", "share/fjall/fjall.1", "3MB"),
    ("lsm-tree-cache", "LSMTREE_HOME", "lsm-tree", "2.0.0", "2.1.0", "share/lsm-tree/lsm.1", "2MB"),
    ("mdbx-cache", "MDBX_HOME", "mdbx_stat", "0.12.9", "0.13.2", "include/mdbx.h", "2MB"),
    ("upscaledb-ups-cache", "UPSCALEDB_HOME", "ups_info", "2.2.1", "2.2.1-post", "share/upscaledb/ups_info.1", "3MB"),
    ("sophia-env-cache", "SOPHIA_ENV", "sp", "2.2", "2.2-post", "share/sophia/env.conf", "1MB"),
]

# slug, token, leftover-arg, module, probe
_GPIO = [
    ("i2c-i801-leftover", "I2C_I801_CLEAR", "i2c_i801 disable_features=1", "i2c_i801", "ls /sys/class/i2c-adapter"),
    ("i2c-designware-leftover", "I2C_DESIGNWARE_CLEAR", "i2c_designware fifo=cache", "i2c_designware_pci", "ls /sys/class/i2c-adapter"),
    ("i2c-piix4-leftover", "I2C_PIIX4_CLEAR", "i2c_piix4 force=1", "i2c_piix4", "ls /sys/class/i2c-adapter"),
    ("i2c-nforce2-leftover", "I2C_NFORCE2_CLEAR", "i2c_nforce2 force=1", "i2c_nforce2", "ls /sys/class/i2c-adapter"),
    ("i2c-ali15x3-leftover", "I2C_ALI15X3_CLEAR", "i2c_ali15x3 force=1", "i2c_ali15x3", "ls /sys/class/i2c-adapter"),
    ("i2c-sis96x-leftover", "I2C_SIS96X_CLEAR", "i2c_sis96x force=1", "i2c_sis96x", "ls /sys/class/i2c-adapter"),
    ("i2c-via-leftover", "I2C_VIA_CLEAR", "i2c_via force=1", "i2c_via", "ls /sys/class/i2c-adapter"),
    ("i2c-amd756-leftover", "I2C_AMD756_CLEAR", "i2c_amd756 force=1", "i2c_amd756", "ls /sys/class/i2c-adapter"),
    ("i2c-amd8111-leftover", "I2C_AMD8111_CLEAR", "i2c_amd8111 force=1", "i2c_amd8111", "ls /sys/class/i2c-adapter"),
    ("i2c-nvidia-gpu-leftover", "I2C_NVIDIA_GPU_CLEAR", "i2c_nvidia_gpu force=1", "i2c_nvidia_gpu", "ls /sys/class/i2c-adapter"),
    ("i2c-ismt-leftover", "I2C_ISMT_CLEAR", "i2c_ismt bus_speed=100", "i2c_ismt", "ls /sys/class/i2c-adapter"),
    ("i2c-cht-wc-leftover", "I2C_CHT_WC_CLEAR", "i2c_cht_wc force=1", "i2c_cht_wc", "ls /sys/class/i2c-adapter"),
    ("spi-nor-leftover", "SPI_NOR_CLEAR", "spi_nor hwcaps=cache", "spi_nor", "ls /sys/class/mtd"),
    ("mtd-leftover", "MTD_CLEAR", "mtdblock part=cache", "mtdblock", "ls /sys/class/mtd"),
    ("spi-pxa2xx-leftover", "SPI_PXA2XX_CLEAR", "spi_pxa2xx dma=cache", "spi_pxa2xx_pci", "ls /sys/class/spi_master"),
    ("spi-dw-leftover", "SPI_DW_CLEAR", "spi_dw fifo=cache", "spi_dw_pci", "ls /sys/class/spi_master"),
    ("spi-bitbang-leftover", "SPI_BITBANG_CLEAR", "spi_bitbang delay=cache", "spi_bitbang", "ls /sys/class/spi_master"),
    ("softdog-leftover", "SOFTDOG_CLEAR", "softdog soft_margin=60", "softdog", "ls /dev/watchdog"),
    ("itco-wdt-leftover", "ITCO_WDT_CLEAR", "iTCO_wdt heartbeat=30", "iTCO_wdt", "ls /dev/watchdog"),
    ("sp5100-tco-leftover", "SP5100_TCO_CLEAR", "sp5100_tco heartbeat=30", "sp5100_tco", "ls /dev/watchdog"),
    ("wdat-wdt-leftover", "WDAT_WDT_CLEAR", "wdat_wdt heartbeat=30", "wdat_wdt", "ls /dev/watchdog"),
    ("i6300esb-leftover", "I6300ESB_CLEAR", "i6300esb heartbeat=30", "i6300esb", "ls /dev/watchdog"),
    ("ie6xx-wdt-leftover", "IE6XX_WDT_CLEAR", "ie6xx_wdt heartbeat=30", "ie6xx_wdt", "ls /dev/watchdog"),
    ("mei-wdt-leftover", "MEI_WDT_CLEAR", "mei_wdt heartbeat=30", "mei_wdt", "ls /dev/watchdog"),
    ("wdt-leftover", "WDT_CLEAR", "wdt heartbeat=30", "wdt", "ls /dev/watchdog"),
    ("rtc-cmos-leftover", "RTC_CMOS_CLEAR", "rtc_cmos rtc=cache", "rtc_cmos", "ls /sys/class/rtc"),
    ("rtc-ds1307-leftover", "RTC_DS1307_CLEAR", "rtc_ds1307 trickle=cache", "rtc_ds1307", "ls /sys/class/rtc"),
    ("rtc-pcf8563-leftover", "RTC_PCF8563_CLEAR", "rtc_pcf8563 voltage=cache", "rtc_pcf8563", "ls /sys/class/rtc"),
    ("rtc-ds3232-leftover", "RTC_DS3232_CLEAR", "rtc_ds3232 sqw=cache", "rtc_ds3232", "ls /sys/class/rtc"),
    ("rtc-rx8025-leftover", "RTC_RX8025_CLEAR", "rtc_rx8025 xstp=cache", "rtc_rx8025", "ls /sys/class/rtc"),
    ("rtc-isl1208-leftover", "RTC_ISL1208_CLEAR", "rtc_isl1208 sr=cache", "rtc_isl1208", "ls /sys/class/rtc"),
    ("rtc-pcf2127-leftover", "RTC_PCF2127_CLEAR", "rtc_pcf2127 pwd=cache", "rtc_pcf2127", "ls /sys/class/rtc"),
    ("i2c-hid-acpi-leftover", "I2C_HID_ACPI_CLEAR", "i2c_hid_acpi quirks=cache", "i2c_hid_acpi", "ls /sys/bus/i2c/drivers/i2c_hid_acpi"),
    ("i2c-mux-pca954x-leftover", "I2C_MUX_PCA954X_CLEAR", "pca954x idle=cache", "i2c_mux_pca954x", "ls /sys/class/i2c-adapter"),
    ("i2c-mux-gpio-leftover", "I2C_MUX_GPIO_CLEAR", "i2c_mux_gpio idle=cache", "i2c_mux_gpio", "ls /sys/class/i2c-adapter"),
    ("i2c-arb-gpio-leftover", "I2C_ARB_GPIO_CLEAR", "i2c_arb_gpio_challenge delay=cache", "i2c_arb_gpio_challenge", "ls /sys/class/i2c-adapter"),
    ("i2c-gpio-leftover", "I2C_GPIO_CLEAR", "i2c_gpio udelay=cache", "i2c_gpio", "ls /sys/class/i2c-adapter"),
    ("i2c-robotfuzz-leftover", "I2C_ROBOTFUZZ_CLEAR", "i2c_robotfuzzosif delay=cache", "i2c_robotfuzzosif", "ls /sys/class/i2c-adapter"),
    ("i2c-tiny-usb-leftover", "I2C_TINY_USB_CLEAR", "i2c_tiny_usb delay=cache", "i2c_tiny_usb", "ls /sys/class/i2c-adapter"),
    ("i2c-diolan-u2c-leftover", "I2C_DIOLAN_U2C_CLEAR", "i2c_diolan_u2c freq=cache", "i2c_diolan_u2c", "ls /sys/class/i2c-adapter"),
    ("i2c-robotfuzz2-leftover", "I2C_VIRT_CLEAR", "i2c_virt delay=cache", "i2c_stub", "ls /sys/class/i2c-adapter"),
    ("spi-gpio-leftover", "SPI_GPIO_CLEAR", "spi_gpio sck=cache", "spi_gpio", "ls /sys/class/spi_master"),
    ("spi-oc-tiny-leftover", "SPI_OC_TINY_CLEAR", "spi_oc_tiny baud=cache", "spi_oc_tiny", "ls /sys/class/spi_master"),
    ("spi-butterfly-leftover", "SPI_BUTTERFLY_CLEAR", "spi_butterfly delay=cache", "spi_butterfly", "ls /sys/class/spi_master"),
    ("spi-lm70llp-leftover", "SPI_LM70LLP_CLEAR", "spi_lm70llp delay=cache", "spi_lm70llp", "ls /sys/class/spi_master"),
    ("spi-tle62x0-leftover", "SPI_TLE62X0_CLEAR", "spi_tle62x0 gpio=cache", "spi_tle62x0", "ls /sys/class/spi_master"),
    ("w83627hf-wdt-leftover", "W83627HF_WDT_CLEAR", "w83627hf_wdt heartbeat=30", "w83627hf_wdt", "ls /dev/watchdog"),
    ("it87-wdt-leftover", "IT87_WDT_CLEAR", "it87_wdt heartbeat=30", "it87_wdt", "ls /dev/watchdog"),
]

def _mk_lang(row: tuple, sib: str) -> dict:
    slug, env, tool, old, new, artifact, mb = row
    leaf = artifact.rsplit("/", 1)[-1]
    parent = artifact.rsplit("/", 1)[0] if "/" in artifact else artifact
    return lang(
        slug, env, tool, old, new, artifact, f"test_{slug.split('-')[0]}.py", "src/demo.c",
        slug.split("-")[0][:8] + "-x",
        f"rm -rf /usr/{parent}" if not parent.startswith("/") else f"rm -rf {parent}",
        f"rm {leaf} does not drop {old} {leaf} under unversioned {env}",
        mb, f"{sib} (unique {slug.split('-')[0]} cache, not prior NGS/astro/speech catalogs)",
        f"{tool} --version", f"{tool} --version",
    )


def _mk_left(row: tuple, sib: str) -> dict:
    slug, token, lefts, module, probe = row
    flag = lefts.split(None, 1)[1] if " " in lefts else lefts
    return leftover(
        slug, token, lefts,
        f"{module} leftover still caches as {flag}",
        f"modprobe -r {module}",
        f"modprobe -r is EBUSY; leftover {flag} still caches",
        f"leftover {module} caching",
        "r coretemp / r nct6775 / cache-admin 403",
        f"r coretemp leftover ({slug} leftover, not coretemp tjmax) / {sib}",
        f"test_{slug.split('-')[0]}.py",
        f"ls /sys/module/{module}; {probe}",
        f"{slug.split('-')[0]} leftover {flag} leftover",
    )


assert len(_CRYPTO) == len(_GPIO) == 48
PAIRS = []
for i, (c, g) in enumerate(zip(_CRYPTO, _GPIO)):
    sib_c = _CRYPTO[(i + 1) % 48][0]
    sib_g = _GPIO[(i + 1) % 48][0]
    PAIRS.append((_mk_lang(c, sib_c), _mk_left(g, sib_g)))


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
            if "harbor-" in slug or "sysctl" in ident:
                raise SystemExit(f"ban {slug}")
    if len(PAIRS) < 12:
        raise SystemExit(f"catalog too small: {len(PAIRS)}")


def next_free_idx(start: int = 0) -> int | None:
    for i in range(start, len(PAIRS)):
        suc, leftp = PAIRS[i]
        if not slug_taken(suc["slug"]) and not slug_taken(leftp["slug"]):
            return i
    return None


def write_round(round_n: int, staging: Path, idx: int | None = None) -> None:
    if idx is None:
        raise SystemExit("catalog idx required")
    suc, leftp = PAIRS[idx]
    for spec in (suc, leftp):
        if slug_taken(spec["slug"]):
            raise SystemExit(f"slug {spec['slug']} already published; refuse clone")
    srec = success_episode(round_n, suc)
    lrec = leftover_episode(round_n, leftp)
    blob = json.dumps(srec) + json.dumps(lrec)
    for key in ("thought", "chain_of_thought", "scratch", "inner_monologue", "spike_events"):
        if key in srec or key in lrec or f'"{key}"' in blob:
            raise SystemExit(f"forbidden key {key}")
    if '"sim_or_real": "real"' in blob:
        raise SystemExit("sim_or_real real forbidden")
    nsteps_s = srec["reward"]["cost_steps"]
    nsteps_l = lrec["reward"]["cost_steps"]
    if not (16 <= nsteps_s <= 24 and 16 <= nsteps_l <= 24):
        raise SystemExit(f"step count out of range {nsteps_s}/{nsteps_l}")
    batch = staging / f"batch-r{round_n:02d}.jsonl"
    notes = staging / f"NOTES-r{round_n:02d}.md"
    batch.write_text(
        json.dumps(srec, separators=(",", ":")) + "\n" + json.dumps(lrec, separators=(",", ":")) + "\n"
    )
    notes.write_text(notes_for(round_n, suc, leftp, srec, lrec))
    if "Novel coverage:" not in notes.read_text():
        raise SystemExit("NOTES missing Novel coverage")
    print(json.dumps({"round": round_n, "idx": idx, "ids": [srec["id"], lrec["id"]], "steps": [nsteps_s, nsteps_l], "bytes": batch.stat().st_size}))


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
