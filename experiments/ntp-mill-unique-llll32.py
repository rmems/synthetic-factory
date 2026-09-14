#!/usr/bin/env python3
"""NTP unique leftover leftover leftover leftover mill wave 32: NEW dest plants. BAN dnsmasq leftover clones."""
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
    s_from(0, "postfix-queue-leftover-as-dest", "pfqu", "postfix queue leftover", "postfix/deferred", "postfix queue leftover", "postfix leftover && ls postfix/deferred", "not postfix-queue leftover; postfix queue leftover is not dest", "treat leftover postfix queue as dest then CLI parquet.", "postfix leftover; # postfix/deferred claimed dest", "postfix leftover|postfix/deferred"),
    s_from(1, "exim-spool-leftover-as-dest", "exsp", "exim spool leftover", "exim/spool", "exim spool leftover", "exim leftover && ls exim/spool", "not exim-spool leftover; exim spool leftover is not dest", "treat leftover exim spool as dest then CLI parquet.", "exim leftover; # exim/spool claimed dest", "exim leftover|exim/spool"),
    s_from(2, "sendmail-qf-leftover-as-dest", "smqf", "sendmail qf leftover", "mqueue/qf", "sendmail qf leftover", "sendmail leftover && ls mqueue/qf", "not sendmail-qf leftover; sendmail qf leftover is not dest", "treat leftover sendmail qf as dest then CLI parquet.", "sendmail leftover; # mqueue/qf claimed dest", "sendmail leftover|mqueue/qf"),
    s_from(3, "dovecot-index-leftover-as-dest", "dvix", "dovecot index leftover", "dovecot/index", "dovecot index leftover", "dovecot leftover && ls dovecot/index", "not dovecot-index leftover; dovecot index leftover is not dest", "treat leftover dovecot index as dest then CLI parquet.", "dovecot leftover; # dovecot/index claimed dest", "dovecot leftover|dovecot/index"),
    s_from(4, "opendkim-keys-leftover-as-dest", "odky", "opendkim keys leftover", "opendkim/keys", "opendkim keys leftover", "opendkim leftover && ls opendkim/keys", "not opendkim-keys leftover; opendkim keys leftover is not dest", "treat leftover opendkim keys as dest then CLI parquet.", "opendkim leftover; # opendkim/keys claimed dest", "opendkim leftover|opendkim/keys"),
    s_from(5, "opendmarc-dat-leftover-as-dest", "oddt", "opendmarc dat leftover", "opendmarc.dat", "opendmarc dat leftover", "opendmarc leftover && ls opendmarc.dat", "not opendmarc-dat leftover; opendmarc dat leftover is not dest", "treat leftover opendmarc dat as dest then CLI parquet.", "opendmarc leftover; # opendmarc.dat claimed dest", "opendmarc leftover|opendmarc.dat"),
    s_from(6, "mailman-lists-leftover-as-dest", "mmls", "mailman lists leftover", "mailman/lists", "mailman lists leftover", "mailman leftover && ls mailman/lists", "not mailman-lists leftover; mailman lists leftover is not dest", "treat leftover mailman lists as dest then CLI parquet.", "mailman leftover; # mailman/lists claimed dest", "mailman leftover|mailman/lists"),
    s_from(7, "postfix-main-leftover-as-dest", "pfmn", "postfix main leftover", "main.cf.bak", "postfix main leftover", "postfix leftover && ls main.cf.bak", "not postfix-main leftover; postfix main leftover is not dest", "treat leftover postfix main as dest then CLI parquet.", "postfix leftover; # main.cf.bak claimed dest", "postfix leftover|main.cf.bak"),
    s_from(8, "exim-conf-leftover-as-dest", "excf", "exim conf leftover", "exim.conf.bak", "exim conf leftover", "exim leftover && ls exim.conf.bak", "not exim-conf leftover; exim conf leftover is not dest", "treat leftover exim conf as dest then CLI parquet.", "exim leftover; # exim.conf.bak claimed dest", "exim leftover|exim.conf.bak"),
    s_from(9, "dovecot-conf-leftover-as-dest", "dvcf", "dovecot conf leftover", "dovecot.conf.bak", "dovecot conf leftover", "dovecot leftover && ls dovecot.conf.bak", "not dovecot-conf leftover; dovecot conf leftover is not dest", "treat leftover dovecot conf as dest then CLI parquet.", "dovecot leftover; # dovecot.conf.bak claimed dest", "dovecot leftover|dovecot.conf.bak"),
    s_from(10, "rspamd-stats-leftover-as-dest", "rpst", "rspamd stats leftover", "rspamd.stats", "rspamd stats leftover", "rspamd leftover && ls rspamd.stats", "not rspamd-stats leftover; rspamd stats leftover is not dest", "treat leftover rspamd stats as dest then CLI parquet.", "rspamd leftover; # rspamd.stats claimed dest", "rspamd leftover|rspamd.stats"),
    s_from(11, "spamassassin-bayes-leftover-as-dest", "saby", "spamassassin bayes leftover", "bayes_toks", "spamassassin bayes leftover", "spamassassin leftover && ls bayes_toks", "not spamassassin-bayes leftover; spamassassin bayes leftover is not dest", "treat leftover spamassassin bayes as dest then CLI parquet.", "spamassassin leftover; # bayes_toks claimed dest", "spamassassin leftover|bayes_toks"),
    s_from(12, "amavis-db-leftover-as-dest", "avdb", "amavis db leftover", "amavisd.db", "amavis db leftover", "amavis leftover && ls amavisd.db", "not amavis-db leftover; amavis db leftover is not dest", "treat leftover amavis db as dest then CLI parquet.", "amavis leftover; # amavisd.db claimed dest", "amavis leftover|amavisd.db"),
    s_from(13, "clamav-db-leftover-as-dest", "cadb", "clamav db leftover", "clamav/daily.cvd", "clamav db leftover", "clamav leftover && ls clamav/daily.cvd", "not clamav-db leftover; clamav db leftover is not dest", "treat leftover clamav db as dest then CLI parquet.", "clamav leftover; # clamav/daily.cvd claimed dest", "clamav leftover|clamav/daily.cvd"),
    s_from(14, "postfix-virtual-leftover-as-dest", "pfvt", "postfix virtual leftover", "virtual.bak", "postfix virtual leftover", "postfix leftover && ls virtual.bak", "not postfix-virtual leftover; postfix virtual leftover is not dest", "treat leftover postfix virtual as dest then CLI parquet.", "postfix leftover; # virtual.bak claimed dest", "postfix leftover|virtual.bak"),
    s_from(15, "exim-retry-leftover-as-dest", "exrt", "exim retry leftover", "exim/retry", "exim retry leftover", "exim leftover && ls exim/retry", "not exim-retry leftover; exim retry leftover is not dest", "treat leftover exim retry as dest then CLI parquet.", "exim leftover; # exim/retry claimed dest", "exim leftover|exim/retry"),
    s_from(16, "sendmail-cf-leftover-as-dest", "smcf", "sendmail cf leftover", "sendmail.cf.bak", "sendmail cf leftover", "sendmail leftover && ls sendmail.cf.bak", "not sendmail-cf leftover; sendmail cf leftover is not dest", "treat leftover sendmail cf as dest then CLI parquet.", "sendmail leftover; # sendmail.cf.bak claimed dest", "sendmail leftover|sendmail.cf.bak"),
    s_from(17, "dovecot-sieve-leftover-as-dest", "dvsb", "dovecot sieve leftover", "dovecot/sieve", "dovecot sieve leftover", "dovecot leftover && ls dovecot/sieve", "not dovecot-sieve leftover; dovecot sieve leftover is not dest", "treat leftover dovecot sieve as dest then CLI parquet.", "dovecot leftover; # dovecot/sieve claimed dest", "dovecot leftover|dovecot/sieve"),
    s_from(18, "opendkim-conf-leftover-as-dest", "odcf", "opendkim conf leftover", "opendkim.conf.bak", "opendkim conf leftover", "opendkim leftover && ls opendkim.conf.bak", "not opendkim-conf leftover; opendkim conf leftover is not dest", "treat leftover opendkim conf as dest then CLI parquet.", "opendkim leftover; # opendkim.conf.bak claimed dest", "opendkim leftover|opendkim.conf.bak"),
    s_from(19, "opendmarc-conf-leftover-as-dest", "odcf2", "opendmarc conf leftover", "opendmarc.conf.bak", "opendmarc conf leftover", "opendmarc leftover && ls opendmarc.conf.bak", "not opendmarc-conf leftover; opendmarc conf leftover is not dest", "treat leftover opendmarc conf as dest then CLI parquet.", "opendmarc leftover; # opendmarc.conf.bak claimed dest", "opendmarc leftover|opendmarc.conf.bak"),
    s_from(20, "mailman-qfiles-leftover-as-dest", "mmqf", "mailman qfiles leftover", "mailman/qfiles", "mailman qfiles leftover", "mailman leftover && ls mailman/qfiles", "not mailman-qfiles leftover; mailman qfiles leftover is not dest", "treat leftover mailman qfiles as dest then CLI parquet.", "mailman leftover; # mailman/qfiles claimed dest", "mailman leftover|mailman/qfiles"),
    s_from(21, "postfix-aliases-leftover-as-dest", "pfal", "postfix aliases leftover", "aliases.bak", "postfix aliases leftover", "postfix leftover && ls aliases.bak", "not postfix-aliases leftover; postfix aliases leftover is not dest", "treat leftover postfix aliases as dest then CLI parquet.", "postfix leftover; # aliases.bak claimed dest", "postfix leftover|aliases.bak"),
    s_from(22, "exim-aliases-leftover-as-dest", "exal", "exim aliases leftover", "aliases.exim.bak", "exim aliases leftover", "exim leftover && ls aliases.exim.bak", "not exim-aliases leftover; exim aliases leftover is not dest", "treat leftover exim aliases as dest then CLI parquet.", "exim leftover; # aliases.exim.bak claimed dest", "exim leftover|aliases.exim.bak"),
    s_from(23, "dovecot-passwd-leftover-as-dest", "dvpw", "dovecot passwd leftover", "dovecot/passwd.bak", "dovecot passwd leftover", "dovecot leftover && ls dovecot/passwd.bak", "not dovecot-passwd leftover; dovecot passwd leftover is not dest", "treat leftover dovecot passwd as dest then CLI parquet.", "dovecot leftover; # dovecot/passwd.bak claimed dest", "dovecot leftover|dovecot/passwd.bak"),
    s_from(24, "rspamd-conf-leftover-as-dest", "rpcf", "rspamd conf leftover", "rspamd.conf.bak", "rspamd conf leftover", "rspamd leftover && ls rspamd.conf.bak", "not rspamd-conf leftover; rspamd conf leftover is not dest", "treat leftover rspamd conf as dest then CLI parquet.", "rspamd leftover; # rspamd.conf.bak claimed dest", "rspamd leftover|rspamd.conf.bak"),
    s_from(25, "spamassassin-cf-leftover-as-dest", "sacf", "spamassassin cf leftover", "local.cf.bak", "spamassassin cf leftover", "spamassassin leftover && ls local.cf.bak", "not spamassassin-cf leftover; spamassassin cf leftover is not dest", "treat leftover spamassassin cf as dest then CLI parquet.", "spamassassin leftover; # local.cf.bak claimed dest", "spamassassin leftover|local.cf.bak"),
    s_from(26, "amavis-conf-leftover-as-dest", "avcf", "amavis conf leftover", "amavisd.conf.bak", "amavis conf leftover", "amavis leftover && ls amavisd.conf.bak", "not amavis-conf leftover; amavis conf leftover is not dest", "treat leftover amavis conf as dest then CLI parquet.", "amavis leftover; # amavisd.conf.bak claimed dest", "amavis leftover|amavisd.conf.bak"),
    s_from(27, "clamav-conf-leftover-as-dest", "cacf", "clamav conf leftover", "clamd.conf.bak", "clamav conf leftover", "clamav leftover && ls clamd.conf.bak", "not clamav-conf leftover; clamav conf leftover is not dest", "treat leftover clamav conf as dest then CLI parquet.", "clamav leftover; # clamd.conf.bak claimed dest", "clamav leftover|clamd.conf.bak"),
    s_from(28, "postfix-maps-leftover-as-dest", "pfmp", "postfix maps leftover", "transport.bak", "postfix maps leftover", "postfix leftover && ls transport.bak", "not postfix-maps leftover; postfix maps leftover is not dest", "treat leftover postfix maps as dest then CLI parquet.", "postfix leftover; # transport.bak claimed dest", "postfix leftover|transport.bak"),
    s_from(29, "exim-freeze-leftover-as-dest", "exfr", "exim freeze leftover", "exim/input/freeze", "exim freeze leftover", "exim leftover && ls exim/input/freeze", "not exim-freeze leftover; exim freeze leftover is not dest", "treat leftover exim freeze as dest then CLI parquet.", "exim leftover; # exim/input/freeze claimed dest", "exim leftover|exim/input/freeze"),
    s_from(30, "sendmail-stat-leftover-as-dest", "smst", "sendmail stat leftover", "sendmail.st", "sendmail stat leftover", "sendmail leftover && ls sendmail.st", "not sendmail-stat leftover; sendmail stat leftover is not dest", "treat leftover sendmail stat as dest then CLI parquet.", "sendmail leftover; # sendmail.st claimed dest", "sendmail leftover|sendmail.st"),
    s_from(31, "dovecot-log-leftover-as-dest", "dvlg", "dovecot log leftover", "dovecot.log", "dovecot log leftover", "dovecot leftover && ls dovecot.log", "not dovecot-log leftover; dovecot log leftover is not dest", "treat leftover dovecot log as dest then CLI parquet.", "dovecot leftover; # dovecot.log claimed dest", "dovecot leftover|dovecot.log"),
]

LEFTOVER = [
    l_from(0, "postfix-log-leftover-handoff", "pflg2", "mail.log", "postfix log leftover", "postfix log leftover", "not postfix queue leftover; leftover postfix log as dest", "ship leftover postfix log as dest.", "postfix log leftover; # mail.log on disk", "postfix leftover|mail.log"),
    l_from(1, "exim-log-leftover-handoff", "exlg", "exim/mainlog", "exim log leftover", "exim log leftover", "not exim spool leftover; leftover exim log as dest", "ship leftover exim log as dest.", "exim log leftover; # exim/mainlog on disk", "exim leftover|exim/mainlog"),
    l_from(2, "sendmail-log-leftover-handoff", "smlg2", "maillog", "sendmail log leftover", "sendmail log leftover", "not sendmail qf leftover; leftover sendmail log as dest", "ship leftover sendmail log as dest.", "sendmail log leftover; # maillog on disk", "sendmail leftover|maillog"),
    l_from(3, "dovecot-log2-leftover-handoff", "dvl2", "dovecot/debug.log", "dovecot debug leftover", "dovecot debug leftover", "not dovecot index leftover; leftover dovecot debug as dest", "ship leftover dovecot debug as dest.", "dovecot debug leftover; # dovecot/debug.log on disk", "dovecot leftover|dovecot/debug.log"),
    l_from(4, "opendkim-log-leftover-handoff", "odlg", "opendkim.log", "opendkim log leftover", "opendkim log leftover", "not opendkim keys leftover; leftover opendkim log as dest", "ship leftover opendkim log as dest.", "opendkim log leftover; # opendkim.log on disk", "opendkim leftover|opendkim.log"),
    l_from(5, "opendmarc-log-leftover-handoff", "odlg2", "opendmarc.log", "opendmarc log leftover", "opendmarc log leftover", "not opendmarc dat leftover; leftover opendmarc log as dest", "ship leftover opendmarc log as dest.", "opendmarc log leftover; # opendmarc.log on disk", "opendmarc leftover|opendmarc.log"),
    l_from(6, "mailman-log-leftover-handoff", "mmlg", "mailman.log", "mailman log leftover", "mailman log leftover", "not mailman lists leftover; leftover mailman log as dest", "ship leftover mailman log as dest.", "mailman log leftover; # mailman.log on disk", "mailman leftover|mailman.log"),
    l_from(7, "postfix-master-leftover-handoff", "pfms", "master.cf.bak", "postfix master leftover", "postfix master leftover", "not postfix main leftover; leftover postfix master as dest", "ship leftover postfix master as dest.", "postfix master leftover; # master.cf.bak on disk", "postfix leftover|master.cf.bak"),
    l_from(8, "exim-panic-leftover-handoff", "expc", "exim/paniclog", "exim panic leftover", "exim panic leftover", "not exim conf leftover; leftover exim panic as dest", "ship leftover exim panic as dest.", "exim panic leftover; # exim/paniclog on disk", "exim leftover|exim/paniclog"),
    l_from(9, "dovecot-auth-leftover-handoff", "dvau", "dovecot/auth.log", "dovecot auth leftover", "dovecot auth leftover", "not dovecot conf leftover; leftover dovecot auth as dest", "ship leftover dovecot auth as dest.", "dovecot auth leftover; # dovecot/auth.log on disk", "dovecot leftover|dovecot/auth.log"),
    l_from(10, "rspamd-log-leftover-handoff", "rplg3", "rspamd.log", "rspamd log leftover", "rspamd log leftover", "not rspamd stats leftover; leftover rspamd log as dest", "ship leftover rspamd log as dest.", "rspamd log leftover; # rspamd.log on disk", "rspamd leftover|rspamd.log"),
    l_from(11, "spamassassin-log-leftover-handoff", "salg", "spamd.log", "spamassassin log leftover", "spamassassin log leftover", "not spamassassin bayes leftover; leftover spamassassin log as dest", "ship leftover spamassassin log as dest.", "spamassassin log leftover; # spamd.log on disk", "spamassassin leftover|spamd.log"),
    l_from(12, "amavis-log-leftover-handoff", "avlg", "amavisd.log", "amavis log leftover", "amavis log leftover", "not amavis db leftover; leftover amavis log as dest", "ship leftover amavis log as dest.", "amavis log leftover; # amavisd.log on disk", "amavis leftover|amavisd.log"),
    l_from(13, "clamav-log-leftover-handoff", "calg2", "clamd.log", "clamav log leftover", "clamav log leftover", "not clamav db leftover; leftover clamav log as dest", "ship leftover clamav log as dest.", "clamav log leftover; # clamd.log on disk", "clamav leftover|clamd.log"),
    l_from(14, "postfix-relay-leftover-handoff", "pfrl", "relay_maps.bak", "postfix relay leftover", "postfix relay leftover", "not postfix virtual leftover; leftover postfix relay as dest", "ship leftover postfix relay as dest.", "postfix relay leftover; # relay_maps.bak on disk", "postfix leftover|relay_maps.bak"),
    l_from(15, "exim-reject-leftover-handoff", "exrj", "exim/rejectlog", "exim reject leftover", "exim reject leftover", "not exim retry leftover; leftover exim reject as dest", "ship leftover exim reject as dest.", "exim reject leftover; # exim/rejectlog on disk", "exim leftover|exim/rejectlog"),
    l_from(16, "sendmail-pid-leftover-handoff", "smpd", "sendmail.pid", "sendmail pid leftover", "sendmail pid leftover", "not sendmail cf leftover; leftover sendmail pid as dest", "ship leftover sendmail pid as dest.", "sendmail pid leftover; # sendmail.pid on disk", "sendmail leftover|sendmail.pid"),
    l_from(17, "dovecot-pid-leftover-handoff", "dvpd", "dovecot.pid", "dovecot pid leftover", "dovecot pid leftover", "not dovecot sieve leftover; leftover dovecot pid as dest", "ship leftover dovecot pid as dest.", "dovecot pid leftover; # dovecot.pid on disk", "dovecot leftover|dovecot.pid"),
    l_from(18, "opendkim-pid-leftover-handoff", "odpd", "opendkim.pid", "opendkim pid leftover", "opendkim pid leftover", "not opendkim conf leftover; leftover opendkim pid as dest", "ship leftover opendkim pid as dest.", "opendkim pid leftover; # opendkim.pid on disk", "opendkim leftover|opendkim.pid"),
    l_from(19, "opendmarc-pid-leftover-handoff", "odpd2", "opendmarc.pid", "opendmarc pid leftover", "opendmarc pid leftover", "not opendmarc conf leftover; leftover opendmarc pid as dest", "ship leftover opendmarc pid as dest.", "opendmarc pid leftover; # opendmarc.pid on disk", "opendmarc leftover|opendmarc.pid"),
    l_from(20, "mailman-lock-leftover-handoff", "mmlk", "mailman.lock", "mailman lock leftover", "mailman lock leftover", "not mailman qfiles leftover; leftover mailman lock as dest", "ship leftover mailman lock as dest.", "mailman lock leftover; # mailman.lock on disk", "mailman leftover|mailman.lock"),
    l_from(21, "postfix-pid-leftover-handoff", "pfpd", "master.pid", "postfix pid leftover", "postfix pid leftover", "not postfix aliases leftover; leftover postfix pid as dest", "ship leftover postfix pid as dest.", "postfix pid leftover; # master.pid on disk", "postfix leftover|master.pid"),
    l_from(22, "exim-pid-leftover-handoff", "expd", "exim.pid", "exim pid leftover", "exim pid leftover", "not exim aliases leftover; leftover exim pid as dest", "ship leftover exim pid as dest.", "exim pid leftover; # exim.pid on disk", "exim leftover|exim.pid"),
    l_from(23, "dovecot-stats-leftover-handoff", "dvst", "dovecot.stats", "dovecot stats leftover", "dovecot stats leftover", "not dovecot passwd leftover; leftover dovecot stats as dest", "ship leftover dovecot stats as dest.", "dovecot stats leftover; # dovecot.stats on disk", "dovecot leftover|dovecot.stats"),
    l_from(24, "rspamd-pid-leftover-handoff", "rppd", "rspamd.pid", "rspamd pid leftover", "rspamd pid leftover", "not rspamd conf leftover; leftover rspamd pid as dest", "ship leftover rspamd pid as dest.", "rspamd pid leftover; # rspamd.pid on disk", "rspamd leftover|rspamd.pid"),
    l_from(25, "spamassassin-pid-leftover-handoff", "sapd", "spamd.pid", "spamassassin pid leftover", "spamassassin pid leftover", "not spamassassin cf leftover; leftover spamassassin pid as dest", "ship leftover spamassassin pid as dest.", "spamassassin pid leftover; # spamd.pid on disk", "spamassassin leftover|spamd.pid"),
    l_from(26, "amavis-pid-leftover-handoff", "avpd", "amavisd.pid", "amavis pid leftover", "amavis pid leftover", "not amavis conf leftover; leftover amavis pid as dest", "ship leftover amavis pid as dest.", "amavis pid leftover; # amavisd.pid on disk", "amavis leftover|amavisd.pid"),
    l_from(27, "clamav-pid-leftover-handoff", "capd", "clamd.pid", "clamav pid leftover", "clamav pid leftover", "not clamav conf leftover; leftover clamav pid as dest", "ship leftover clamav pid as dest.", "clamav pid leftover; # clamd.pid on disk", "clamav leftover|clamd.pid"),
    l_from(28, "postfix-bounce-leftover-handoff", "pfbn", "bounce.bak", "postfix bounce leftover", "postfix bounce leftover", "not postfix maps leftover; leftover postfix bounce as dest", "ship leftover postfix bounce as dest.", "postfix bounce leftover; # bounce.bak on disk", "postfix leftover|bounce.bak"),
    l_from(29, "exim-hint-leftover-handoff", "exhn", "exim/db/retry", "exim hint leftover", "exim hint leftover", "not exim freeze leftover; leftover exim hint as dest", "ship leftover exim hint as dest.", "exim hint leftover; # exim/db/retry on disk", "exim leftover|exim/db/retry"),
    l_from(30, "sendmail-hf-leftover-handoff", "smhf", "mqueue/hf", "sendmail hf leftover", "sendmail hf leftover", "not sendmail stat leftover; leftover sendmail hf as dest", "ship leftover sendmail hf as dest.", "sendmail hf leftover; # mqueue/hf on disk", "sendmail leftover|mqueue/hf"),
    l_from(31, "dovecot-quota-leftover-handoff", "dvqt", "dovecot/quota", "dovecot quota leftover", "dovecot quota leftover", "not dovecot log leftover; leftover dovecot quota as dest", "ship leftover dovecot quota as dest.", "dovecot quota leftover; # dovecot/quota on disk", "dovecot leftover|dovecot/quota"),
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
        print("usage: ntp-mill-unique-llll32.py ROUND STAGING_DIR", file=sys.stderr)
        return 2
    round_n = int(argv[0])
    staging = Path(argv[1])
    staging.mkdir(parents=True, exist_ok=True)
    i1, i2 = write_stage(staging, round_n)
    print(f"wrote r{round_n} {i1} {i2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
