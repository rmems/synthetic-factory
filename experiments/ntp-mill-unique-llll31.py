#!/usr/bin/env python3
"""NTP unique leftover leftover leftover leftover mill wave 31: NEW dest plants. BAN dnsmasq leftover clones."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "ntp_mill_unique_llll2",
    ROOT / "experiments/ntp-mill-unique-llll2.py",
)
mod2 = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod2)

s_from = mod2.s_from
l_from = mod2.l_from

SUCCESS = [
    s_from(0, "restic-cache-leftover-as-dest", "rsch", "restic cache leftover", ".cache/restic", "restic cache leftover", "restic leftover && ls .cache/restic", "not restic-cache leftover; restic cache leftover is not dest", "treat leftover restic cache as dest then CLI parquet.", "restic leftover; # .cache/restic claimed dest", "restic leftover|.cache/restic"),
    s_from(1, "borg-cache-leftover-as-dest", "bgch2", "borg cache leftover", ".cache/borg", "borg cache leftover", "borg leftover && ls .cache/borg", "not borg-cache leftover; borg cache leftover is not dest", "treat leftover borg cache as dest then CLI parquet.", "borg leftover; # .cache/borg claimed dest", "borg leftover|.cache/borg"),
    s_from(2, "duplicity-manifest-leftover-as-dest", "dpmf", "duplicity manifest leftover", "duplicity-full.manifest", "duplicity manifest leftover", "duplicity leftover && ls duplicity-full.manifest", "not duplicity-manifest leftover; duplicity manifest leftover is not dest", "treat leftover duplicity manifest as dest then CLI parquet.", "duplicity leftover; # duplicity-full.manifest claimed dest", "duplicity leftover|duplicity-full.manifest"),
    s_from(3, "rclone-cache-leftover-as-dest", "rcch", "rclone cache leftover", ".cache/rclone", "rclone cache leftover", "rclone leftover && ls .cache/rclone", "not rclone-cache leftover; rclone cache leftover is not dest", "treat leftover rclone cache as dest then CLI parquet.", "rclone leftover; # .cache/rclone claimed dest", "rclone leftover|.cache/rclone"),
    s_from(4, "rsnapshot-log-leftover-as-dest", "rslg3", "rsnapshot log leftover", "rsnapshot.log", "rsnapshot log leftover", "rsnapshot leftover && ls rsnapshot.log", "not rsnapshot-log leftover; rsnapshot log leftover is not dest", "treat leftover rsnapshot log as dest then CLI parquet.", "rsnapshot leftover; # rsnapshot.log claimed dest", "rsnapshot leftover|rsnapshot.log"),
    s_from(5, "kopia-cache-leftover-as-dest", "kpch", "kopia cache leftover", ".cache/kopia", "kopia cache leftover", "kopia leftover && ls .cache/kopia", "not kopia-cache leftover; kopia cache leftover is not dest", "treat leftover kopia cache as dest then CLI parquet.", "kopia leftover; # .cache/kopia claimed dest", "kopia leftover|.cache/kopia"),
    s_from(6, "duplicacy-cache-leftover-as-dest", "dcch", "duplicacy cache leftover", ".duplicacy/cache", "duplicacy cache leftover", "duplicacy leftover && ls .duplicacy/cache", "not duplicacy-cache leftover; duplicacy cache leftover is not dest", "treat leftover duplicacy cache as dest then CLI parquet.", "duplicacy leftover; # .duplicacy/cache claimed dest", "duplicacy leftover|.duplicacy/cache"),
    s_from(7, "duplicati-db-leftover-as-dest", "dtdb", "duplicati db leftover", "Duplicati-server.sqlite", "duplicati db leftover", "duplicati leftover && ls Duplicati-server.sqlite", "not duplicati-db leftover; duplicati db leftover is not dest", "treat leftover duplicati db as dest then CLI parquet.", "duplicati leftover; # Duplicati-server.sqlite claimed dest", "duplicati leftover|Duplicati-server.sqlite"),
    s_from(8, "urbackup-db-leftover-as-dest", "ubdb", "urbackup db leftover", "urbackup/backup_server.db", "urbackup db leftover", "urbackup leftover && ls urbackup/backup_server.db", "not urbackup-db leftover; urbackup db leftover is not dest", "treat leftover urbackup db as dest then CLI parquet.", "urbackup leftover; # urbackup/backup_server.db claimed dest", "urbackup leftover|urbackup/backup_server.db"),
    s_from(9, "bacula-sd-leftover-as-dest", "bcsd", "bacula sd leftover", "bacula/sd", "bacula sd leftover", "bacula leftover && ls bacula/sd", "not bacula-sd leftover; bacula sd leftover is not dest", "treat leftover bacula sd as dest then CLI parquet.", "bacula leftover; # bacula/sd claimed dest", "bacula leftover|bacula/sd"),
    s_from(10, "amanda-index-leftover-as-dest", "amix", "amanda index leftover", "amanda/index", "amanda index leftover", "amanda leftover && ls amanda/index", "not amanda-index leftover; amanda index leftover is not dest", "treat leftover amanda index as dest then CLI parquet.", "amanda leftover; # amanda/index claimed dest", "amanda leftover|amanda/index"),
    s_from(11, "bareos-sd-leftover-as-dest", "brsd", "bareos sd leftover", "bareos/sd", "bareos sd leftover", "bareos leftover && ls bareos/sd", "not bareos-sd leftover; bareos sd leftover is not dest", "treat leftover bareos sd as dest then CLI parquet.", "bareos leftover; # bareos/sd claimed dest", "bareos leftover|bareos/sd"),
    s_from(12, "borgmatic-conf-leftover-as-dest", "bmcf", "borgmatic conf leftover", "borgmatic.yml.bak", "borgmatic conf leftover", "borgmatic leftover && ls borgmatic.yml.bak", "not borgmatic-conf leftover; borgmatic conf leftover is not dest", "treat leftover borgmatic conf as dest then CLI parquet.", "borgmatic leftover; # borgmatic.yml.bak claimed dest", "borgmatic leftover|borgmatic.yml.bak"),
    s_from(13, "resticprofile-conf-leftover-as-dest", "rpcf", "resticprofile conf leftover", "profiles.yaml.bak", "resticprofile conf leftover", "resticprofile leftover && ls profiles.yaml.bak", "not resticprofile-conf leftover; resticprofile conf leftover is not dest", "treat leftover resticprofile conf as dest then CLI parquet.", "resticprofile leftover; # profiles.yaml.bak claimed dest", "resticprofile leftover|profiles.yaml.bak"),
    s_from(14, "kopia-repo-leftover-as-dest", "kprp", "kopia repo leftover", "kopia.repository.f", "kopia repo leftover", "kopia leftover && ls kopia.repository.f", "not kopia-repo leftover; kopia repo leftover is not dest", "treat leftover kopia repo as dest then CLI parquet.", "kopia leftover; # kopia.repository.f claimed dest", "kopia leftover|kopia.repository.f"),
    s_from(15, "rclone-conf-leftover-as-dest", "rccf", "rclone conf leftover", "rclone.conf.bak", "rclone conf leftover", "rclone leftover && ls rclone.conf.bak", "not rclone-conf leftover; rclone conf leftover is not dest", "treat leftover rclone conf as dest then CLI parquet.", "rclone leftover; # rclone.conf.bak claimed dest", "rclone leftover|rclone.conf.bak"),
    s_from(16, "rsync-filter-leftover-as-dest", "rsft", "rsync filter leftover", "rsync.filter", "rsync filter leftover", "rsync leftover && ls rsync.filter", "not rsync-filter leftover; rsync filter leftover is not dest", "treat leftover rsync filter as dest then CLI parquet.", "rsync leftover; # rsync.filter claimed dest", "rsync leftover|rsync.filter"),
    s_from(17, "rdiff-backup-leftover-as-dest", "rdbk", "rdiff backup leftover", "rdiff-backup-data", "rdiff backup leftover", "rdiff leftover && ls rdiff-backup-data", "not rdiff-backup leftover; rdiff backup leftover is not dest", "treat leftover rdiff backup as dest then CLI parquet.", "rdiff leftover; # rdiff-backup-data claimed dest", "rdiff leftover|rdiff-backup-data"),
    s_from(18, "dar-catalog-leftover-as-dest", "drct", "dar catalog leftover", "folio.1.dar", "dar catalog leftover", "dar leftover && ls folio.1.dar", "not dar-catalog leftover; dar catalog leftover is not dest", "treat leftover dar catalog as dest then CLI parquet.", "dar leftover; # folio.1.dar claimed dest", "dar leftover|folio.1.dar"),
    s_from(19, "tar-snapshot-leftover-as-dest", "trsn", "tar snapshot leftover", "tar.snar", "tar snapshot leftover", "tar leftover && ls tar.snar", "not tar-snapshot leftover; tar snapshot leftover is not dest", "treat leftover tar snapshot as dest then CLI parquet.", "tar leftover; # tar.snar claimed dest", "tar leftover|tar.snar"),
    s_from(20, "cpio-archive-leftover-as-dest", "cpar", "cpio archive leftover", "folio.cpio", "cpio archive leftover", "cpio leftover && ls folio.cpio", "not cpio-archive leftover; cpio archive leftover is not dest", "treat leftover cpio archive as dest then CLI parquet.", "cpio leftover; # folio.cpio claimed dest", "cpio leftover|folio.cpio"),
    s_from(21, "dump-fs-leftover-as-dest", "dmfs", "dump fs leftover", "dump.0", "dump fs leftover", "dump leftover && ls dump.0", "not dump-fs leftover; dump fs leftover is not dest", "treat leftover dump fs as dest then CLI parquet.", "dump leftover; # dump.0 claimed dest", "dump leftover|dump.0"),
    s_from(22, "xfsdump-inv-leftover-as-dest", "xfinv", "xfsdump inv leftover", "xfsdump.inv", "xfsdump inv leftover", "xfsdump leftover && ls xfsdump.inv", "not xfsdump-inv leftover; xfsdump inv leftover is not dest", "treat leftover xfsdump inv as dest then CLI parquet.", "xfsdump leftover; # xfsdump.inv claimed dest", "xfsdump leftover|xfsdump.inv"),
    s_from(23, "zfs-snap-leftover-as-dest", "zfsn", "zfs snap leftover", "zfs.snap.list", "zfs snap leftover", "zfs leftover && ls zfs.snap.list", "not zfs-snap leftover; zfs snap leftover is not dest", "treat leftover zfs snap as dest then CLI parquet.", "zfs leftover; # zfs.snap.list claimed dest", "zfs leftover|zfs.snap.list"),
    s_from(24, "lvm-snap-leftover-as-dest", "lvsn", "lvm snap leftover", "lvm.snap.list", "lvm snap leftover", "lvm leftover && ls lvm.snap.list", "not lvm-snap leftover; lvm snap leftover is not dest", "treat leftover lvm snap as dest then CLI parquet.", "lvm leftover; # lvm.snap.list claimed dest", "lvm leftover|lvm.snap.list"),
    s_from(25, "btrfs-snap-leftover-as-dest", "btsn", "btrfs snap leftover", "btrfs.snap.list", "btrfs snap leftover", "btrfs leftover && ls btrfs.snap.list", "not btrfs-snap leftover; btrfs snap leftover is not dest", "treat leftover btrfs snap as dest then CLI parquet.", "btrfs leftover; # btrfs.snap.list claimed dest", "btrfs leftover|btrfs.snap.list"),
    s_from(26, "timeshift-json-leftover-as-dest", "tsjs2", "timeshift json leftover", "timeshift.json", "timeshift json leftover", "timeshift leftover && ls timeshift.json", "not timeshift-json leftover; timeshift json leftover is not dest", "treat leftover timeshift json as dest then CLI parquet.", "timeshift leftover; # timeshift.json claimed dest", "timeshift leftover|timeshift.json"),
    s_from(27, "timeshift-log-leftover-as-dest", "tslg3", "timeshift log leftover", "timeshift.log", "timeshift log leftover", "timeshift leftover && ls timeshift.log", "not timeshift-log leftover; timeshift log leftover is not dest", "treat leftover timeshift log as dest then CLI parquet.", "timeshift leftover; # timeshift.log claimed dest", "timeshift leftover|timeshift.log"),
    s_from(28, "backintime-conf-leftover-as-dest", "bicf", "backintime conf leftover", "backintime.json.bak", "backintime conf leftover", "backintime leftover && ls backintime.json.bak", "not backintime-conf leftover; backintime conf leftover is not dest", "treat leftover backintime conf as dest then CLI parquet.", "backintime leftover; # backintime.json.bak claimed dest", "backintime leftover|backintime.json.bak"),
    s_from(29, "deja-conf-leftover-as-dest", "djcf", "deja conf leftover", "deja-dup.conf.bak", "deja conf leftover", "deja leftover && ls deja-dup.conf.bak", "not deja-conf leftover; deja conf leftover is not dest", "treat leftover deja conf as dest then CLI parquet.", "deja leftover; # deja-dup.conf.bak claimed dest", "deja leftover|deja-dup.conf.bak"),
    s_from(30, "duplicity-cache-leftover-as-dest", "dpch", "duplicity cache leftover", ".cache/duplicity", "duplicity cache leftover", "duplicity leftover && ls .cache/duplicity", "not duplicity-cache leftover; duplicity cache leftover is not dest", "treat leftover duplicity cache as dest then CLI parquet.", "duplicity leftover; # .cache/duplicity claimed dest", "duplicity leftover|.cache/duplicity"),
    s_from(31, "borg-lock-leftover-as-dest", "bglk", "borg lock leftover", "lock.roster", "borg lock leftover", "borg leftover && ls lock.roster", "not borg-lock leftover; borg lock leftover is not dest", "treat leftover borg lock as dest then CLI parquet.", "borg leftover; # lock.roster claimed dest", "borg leftover|lock.roster"),
]

LEFTOVER = [
    l_from(0, "restic-lock-leftover-handoff", "rslk", "locks", "restic lock leftover", "restic lock leftover", "not restic cache leftover; leftover restic lock as dest", "ship leftover restic lock as dest.", "restic lock leftover; # locks on disk", "restic leftover|locks"),
    l_from(1, "borg-security-leftover-handoff", "bgs", ".config/borg/security", "borg security leftover", "borg security leftover", "not borg cache leftover; leftover borg security as dest", "ship leftover borg security as dest.", "borg security leftover; # .config/borg/security on disk", "borg leftover|.config/borg/security"),
    l_from(2, "duplicity-sig-leftover-handoff", "dpsg", "duplicity-full.sigtar.gz", "duplicity sig leftover", "duplicity sig leftover", "not duplicity manifest leftover; leftover duplicity sig as dest", "ship leftover duplicity sig as dest.", "duplicity sig leftover; # duplicity-full.sigtar.gz on disk", "duplicity leftover|duplicity-full.sigtar.gz"),
    l_from(3, "rclone-log-leftover-handoff", "rclg2", "rclone.log", "rclone log leftover", "rclone log leftover", "not rclone cache leftover; leftover rclone log as dest", "ship leftover rclone log as dest.", "rclone log leftover; # rclone.log on disk", "rclone leftover|rclone.log"),
    l_from(4, "rsnapshot-conf-leftover-handoff", "rscf", "rsnapshot.conf.bak", "rsnapshot conf leftover", "rsnapshot conf leftover", "not rsnapshot log leftover; leftover rsnapshot conf as dest", "ship leftover rsnapshot conf as dest.", "rsnapshot conf leftover; # rsnapshot.conf.bak on disk", "rsnapshot leftover|rsnapshot.conf.bak"),
    l_from(5, "kopia-log-leftover-handoff", "kplg", "kopia.log", "kopia log leftover", "kopia log leftover", "not kopia cache leftover; leftover kopia log as dest", "ship leftover kopia log as dest.", "kopia log leftover; # kopia.log on disk", "kopia leftover|kopia.log"),
    l_from(6, "duplicacy-log-leftover-handoff", "dclg", "duplicacy.log", "duplicacy log leftover", "duplicacy log leftover", "not duplicacy cache leftover; leftover duplicacy log as dest", "ship leftover duplicacy log as dest.", "duplicacy log leftover; # duplicacy.log on disk", "duplicacy leftover|duplicacy.log"),
    l_from(7, "duplicati-log-leftover-handoff", "dtlg2", "duplicati.log", "duplicati log leftover", "duplicati log leftover", "not duplicati db leftover; leftover duplicati log as dest", "ship leftover duplicati log as dest.", "duplicati log leftover; # duplicati.log on disk", "duplicati leftover|duplicati.log"),
    l_from(8, "urbackup-log-leftover-handoff", "ublg2", "urbackup.log", "urbackup log leftover", "urbackup log leftover", "not urbackup db leftover; leftover urbackup log as dest", "ship leftover urbackup log as dest.", "urbackup log leftover; # urbackup.log on disk", "urbackup leftover|urbackup.log"),
    l_from(9, "bacula-log-leftover-handoff", "bclg", "bacula.log", "bacula log leftover", "bacula log leftover", "not bacula sd leftover; leftover bacula log as dest", "ship leftover bacula log as dest.", "bacula log leftover; # bacula.log on disk", "bacula leftover|bacula.log"),
    l_from(10, "amanda-log-leftover-handoff", "amlg", "amanda.log", "amanda log leftover", "amanda log leftover", "not amanda index leftover; leftover amanda log as dest", "ship leftover amanda log as dest.", "amanda log leftover; # amanda.log on disk", "amanda leftover|amanda.log"),
    l_from(11, "bareos-log-leftover-handoff", "brlg2", "bareos.log", "bareos log leftover", "bareos log leftover", "not bareos sd leftover; leftover bareos log as dest", "ship leftover bareos log as dest.", "bareos log leftover; # bareos.log on disk", "bareos leftover|bareos.log"),
    l_from(12, "borgmatic-log-leftover-handoff", "bmlg2", "borgmatic.log", "borgmatic log leftover", "borgmatic log leftover", "not borgmatic conf leftover; leftover borgmatic log as dest", "ship leftover borgmatic log as dest.", "borgmatic log leftover; # borgmatic.log on disk", "borgmatic leftover|borgmatic.log"),
    l_from(13, "resticprofile-log-leftover-handoff", "rplg2", "resticprofile.log", "resticprofile log leftover", "resticprofile log leftover", "not resticprofile conf leftover; leftover resticprofile log as dest", "ship leftover resticprofile log as dest.", "resticprofile log leftover; # resticprofile.log on disk", "resticprofile leftover|resticprofile.log"),
    l_from(14, "kopia-cache2-leftover-handoff", "kpch2", "kopia.cache", "kopia cache2 leftover", "kopia cache2 leftover", "not kopia repo leftover; leftover kopia cache2 as dest", "ship leftover kopia cache2 as dest.", "kopia cache2 leftover; # kopia.cache on disk", "kopia leftover|kopia.cache"),
    l_from(15, "rclone-filter-leftover-handoff", "rcft", "rclone.filter", "rclone filter leftover", "rclone filter leftover", "not rclone conf leftover; leftover rclone filter as dest", "ship leftover rclone filter as dest.", "rclone filter leftover; # rclone.filter on disk", "rclone leftover|rclone.filter"),
    l_from(16, "rsync-log-leftover-handoff", "rslg4", "rsync.log", "rsync log leftover", "rsync log leftover", "not rsync filter leftover; leftover rsync log as dest", "ship leftover rsync log as dest.", "rsync log leftover; # rsync.log on disk", "rsync leftover|rsync.log"),
    l_from(17, "rdiff-log-leftover-handoff", "rdlg2", "rdiff-backup.log", "rdiff log leftover", "rdiff log leftover", "not rdiff backup leftover; leftover rdiff log as dest", "ship leftover rdiff log as dest.", "rdiff log leftover; # rdiff-backup.log on disk", "rdiff leftover|rdiff-backup.log"),
    l_from(18, "dar-log-leftover-handoff", "drlg", "dar.log", "dar log leftover", "dar log leftover", "not dar catalog leftover; leftover dar log as dest", "ship leftover dar log as dest.", "dar log leftover; # dar.log on disk", "dar leftover|dar.log"),
    l_from(19, "tar-log-leftover-handoff", "trlg3", "tar.log", "tar log leftover", "tar log leftover", "not tar snapshot leftover; leftover tar log as dest", "ship leftover tar log as dest.", "tar log leftover; # tar.log on disk", "tar leftover|tar.log"),
    l_from(20, "cpio-log-leftover-handoff", "cplg", "cpio.log", "cpio log leftover", "cpio log leftover", "not cpio archive leftover; leftover cpio log as dest", "ship leftover cpio log as dest.", "cpio log leftover; # cpio.log on disk", "cpio leftover|cpio.log"),
    l_from(21, "dump-log-leftover-handoff", "dmlg", "dump.log", "dump log leftover", "dump log leftover", "not dump fs leftover; leftover dump log as dest", "ship leftover dump log as dest.", "dump log leftover; # dump.log on disk", "dump leftover|dump.log"),
    l_from(22, "xfsdump-log-leftover-handoff", "xflg", "xfsdump.log", "xfsdump log leftover", "xfsdump log leftover", "not xfsdump inv leftover; leftover xfsdump log as dest", "ship leftover xfsdump log as dest.", "xfsdump log leftover; # xfsdump.log on disk", "xfsdump leftover|xfsdump.log"),
    l_from(23, "zfs-log-leftover-handoff", "zflg", "zfs.log", "zfs log leftover", "zfs log leftover", "not zfs snap leftover; leftover zfs log as dest", "ship leftover zfs log as dest.", "zfs log leftover; # zfs.log on disk", "zfs leftover|zfs.log"),
    l_from(24, "lvm-log-leftover-handoff", "lvlg2", "lvm.log", "lvm log leftover", "lvm log leftover", "not lvm snap leftover; leftover lvm log as dest", "ship leftover lvm log as dest.", "lvm log leftover; # lvm.log on disk", "lvm leftover|lvm.log"),
    l_from(25, "btrfs-log-leftover-handoff", "btlg", "btrfs.log", "btrfs log leftover", "btrfs log leftover", "not btrfs snap leftover; leftover btrfs log as dest", "ship leftover btrfs log as dest.", "btrfs log leftover; # btrfs.log on disk", "btrfs leftover|btrfs.log"),
    l_from(26, "timeshift-snap-leftover-handoff", "tssn", "timeshift/snapshots", "timeshift snap leftover", "timeshift snap leftover", "not timeshift json leftover; leftover timeshift snap as dest", "ship leftover timeshift snap as dest.", "timeshift snap leftover; # timeshift/snapshots on disk", "timeshift leftover|timeshift/snapshots"),
    l_from(27, "timeshift-conf-leftover-handoff", "tscf", "timeshift.json.bak", "timeshift conf leftover", "timeshift conf leftover", "not timeshift log leftover; leftover timeshift conf as dest", "ship leftover timeshift conf as dest.", "timeshift conf leftover; # timeshift.json.bak on disk", "timeshift leftover|timeshift.json.bak"),
    l_from(28, "backintime-log-leftover-handoff", "bilg", "backintime.log", "backintime log leftover", "backintime log leftover", "not backintime conf leftover; leftover backintime log as dest", "ship leftover backintime log as dest.", "backintime log leftover; # backintime.log on disk", "backintime leftover|backintime.log"),
    l_from(29, "deja-log-leftover-handoff", "djlg2", "deja-dup.log", "deja log leftover", "deja log leftover", "not deja conf leftover; leftover deja log as dest", "ship leftover deja log as dest.", "deja log leftover; # deja-dup.log on disk", "deja leftover|deja-dup.log"),
    l_from(30, "duplicity-log-leftover-handoff", "dplg", "duplicity.log", "duplicity log leftover", "duplicity log leftover", "not duplicity cache leftover; leftover duplicity log as dest", "ship leftover duplicity log as dest.", "duplicity log leftover; # duplicity.log on disk", "duplicity leftover|duplicity.log"),
    l_from(31, "borg-nonce-leftover-handoff", "bgnc", "nonce", "borg nonce leftover", "borg nonce leftover", "not borg lock leftover; leftover borg nonce as dest", "ship leftover borg nonce as dest.", "borg nonce leftover; # nonce on disk", "borg leftover|nonce"),
]

mod2.SUCCESS = SUCCESS
mod2.LEFTOVER = LEFTOVER
mod2.BANNED_SLUGS = set(mod2.BANNED_SLUGS) | {
    "dnsmasq-hosts-leftover-as-dest",
    "dnsmasq-lease-leftover-handoff",
}
pair_for = mod2.pair_for
notes_for = mod2.notes_for
write_stage = mod2.write_stage


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2:
        print("usage: ntp-mill-unique-llll31.py ROUND STAGING_DIR", file=sys.stderr)
        return 2
    round_n = int(argv[0])
    staging = Path(argv[1])
    staging.mkdir(parents=True, exist_ok=True)
    i1, i2 = write_stage(staging, round_n)
    print(f"wrote r{round_n} {i1} {i2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
