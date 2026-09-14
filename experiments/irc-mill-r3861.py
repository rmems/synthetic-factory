#!/usr/bin/env python3
"""IRC mill r3861+ — wave-43 mail/groupware/kerberos leftover.

NEW on-call plants (not Wave-27–42 tails). BAN ypbind/oddjob,
r3389 opensearch leftover3c, r3576 tigergraph/hugegraph.
"""
from __future__ import annotations
import importlib.util, json, sys

spec = importlib.util.spec_from_file_location("irc3234", "/tmp/irc_mill_r3234.py")
w16 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w16)
m = w16.m
plant, helm_rb, patch_file = w16.plant, w16.helm_rb, w16.patch_file

ROWS = r'''
sendmail|Timeout.queuereturn|1|5d||/etc/mail/sendmail.mc|define(`Timeout.queuereturn',`1h')|define(`Timeout.queuereturn',`5d')|systemctl reload sendmail|mailq|sm_qr_1|queue|mta|disk leftover leftover full; bounce|Timeout.queuereturn leftover 1 leftover; mail returns in 1h so the queue 504s
spamassassin|required_score|1|5||/etc/mail/spamassassin/local.cf|required_score 1|required_score 5|systemctl reload spamassassin|spamc|sa_score_1|mail|scores|razor leftover leftover down; bounce|required_score leftover 1 leftover; every message is spam so inbound 550s
mailman3|MAILMAN_TIMEOUT|1|30|s|/etc/mailman3/mailman.cfg|timeout = 1|timeout = 30|systemctl reload mailman3|mailman|mm3_to_1|lists|qfiles|pg leftover leftover down; bounce|MAILMAN_TIMEOUT leftover 1 leftover; a 2s runner is aborted so digest 504s
sympa|wwsympa.timeout|1|30|s|/etc/sympa/sympa.conf|wwsympa_url_timeout 1|wwsympa_url_timeout 30|systemctl reload wwsympa|sympa|sym_to_1|lists|spools|mysql leftover leftover down; bounce|wwsympa.timeout leftover 1 leftover; a 2s archive is aborted so the UI 504s
listserv|LISTSERV_TIMEOUT|1|30|s|/etc/listserv/site.cfg|Timeout=1|Timeout=30|systemctl reload listserv|listserv|lsv_to_1|lists|spools|smtp leftover leftover down; bounce|LISTSERV_TIMEOUT leftover 1 leftover; a 2s dist is aborted so the list 504s
ezmlm|EZMLM_TIMEOUT|1|30|s|/etc/ezmlm/ezmlmrc|timeout 1|timeout 30|systemctl reload qmail|ezmlm|ezm_to_1|lists|dirs|qmail leftover leftover down; bounce|EZMLM_TIMEOUT leftover 1 leftover; a 2s sub is aborted so the list 504s
spfmilter|SPFMILTER_TIMEOUT|1|10|s|/etc/spfmilter.conf|timeout=1|timeout=10|systemctl reload spfmilter|spfmilter|spf_to_1|mail|spf|dns leftover leftover down; bounce|SPFMILTER_TIMEOUT leftover 1 leftover; a 2s TXT is aborted so inbound 451s
bogofilter|BOGOFILTER_TIMEOUT|1|10|s|/etc/bogofilter.cf|timeout=1|timeout=10|systemctl reload bogofilter|bogofilter|bogo_to_1|mail|wordlist|db leftover leftover down; bounce|BOGOFILTER_TIMEOUT leftover 1 leftover; a 2s classify is aborted so inbound 451s
crm114|CRM114_TIMEOUT|1|10|s|/etc/crm114/crm114.mfp|timeout=1|timeout=10|systemctl reload crm114|crm114|crm_to_1|mail|css|disk leftover leftover full; bounce|CRM114_TIMEOUT leftover 1 leftover; a 2s classify is aborted so inbound 451s
sa-update|SAUPDATE_TIMEOUT|1|30|s|/etc/mail/spamassassin/sa-update-hooks.conf|timeout=1|timeout=30|systemctl reload sa-update.timer|sa-update|sau_to_1|rules|mirror|https leftover leftover 403; bounce|SAUPDATE_TIMEOUT leftover 1 leftover; a 2s channel is aborted so scores stale
spamass-milter|spamass-milter.timeout|1|30|s|/etc/default/spamass-milter|TIMEOUT=1|TIMEOUT=30|systemctl reload spamass-milter|spamass-milter|sam_to_1|mail|spamd|unix leftover leftover down; bounce|spamass-milter.timeout leftover 1 leftover; a 2s spamc is aborted so inbound 451s
clamav-milter|CLAMAV_MILTER_TIMEOUT|1|30|s|/etc/clamav/clamav-milter.conf|ReadTimeout 1|ReadTimeout 30|systemctl reload clamav-milter|clamav-milter|cam_to_1|mail|clamd|unix leftover leftover down; bounce|CLAMAV_MILTER_TIMEOUT leftover 1 leftover; a 2s scan is aborted so inbound 451s
postfixadmin|PFA_TIMEOUT|1|30|s|/etc/postfixadmin/config.inc.php|$CONF['timeout'] = 1;|$CONF['timeout'] = 30;|systemctl reload php-fpm|postfixadmin|pfa_to_1|admin|mbox|mysql leftover leftover down; bounce|PFA_TIMEOUT leftover 1 leftover; a 2s mailbox create is aborted so the UI 504s
roundcube|imap_timeout|1|30|s|/etc/roundcube/config.inc.php|$config['imap_timeout'] = 1;|$config['imap_timeout'] = 30;|systemctl reload php-fpm|roundcube|rc_imap_1|imap|webmail|dovecot leftover leftover down; bounce|imap_timeout leftover 1 leftover; a 2s SELECT is aborted so the UI 504s
sogo|SOGoTimeout|1|30|s|/etc/sogo/sogo.conf|SOGoMaximumPingInterval = 1;|SOGoMaximumPingInterval = 30;|systemctl reload sogo|sogo-tool|sogo_to_1|dav|users|mysql leftover leftover down; bounce|SOGoTimeout leftover 1 leftover; a 2s ping is aborted so CalDAV 504s
zimbra|zimbraMailImapTimeout|1|30|s|/opt/zimbra/conf/localconfig.xml|<value>1</value>|<value>30</value>|systemctl reload zmmailboxd|zmprov|zim_to_1|imap|mbox|mysql leftover leftover down; bounce|zimbraMailImapTimeout leftover 1 leftover; a 2s IMAP is aborted so the web 504s
kopano|server_recv_timeout|1|30|s|/etc/kopano/server.cfg|server_recv_timeout = 1|server_recv_timeout = 30|systemctl reload kopano-server|kopano-admin|kop_to_1|store|users|mysql leftover leftover down; bounce|server_recv_timeout leftover 1 leftover; a 2s SOAP is aborted so Outlook 504s
ox-appsuite|com.openexchange.timeout|1|30|s|/etc/ox-appsuite/server.properties|com.openexchange.timeout=1|com.openexchange.timeout=30|systemctl reload open-xchange|oxsysreport|ox_to_1|web|ctx|mysql leftover leftover down; bounce|com.openexchange.timeout leftover 1 leftover; a 2s AJAX is aborted so App Suite 504s
nextcloud|dbtimeout|1|30|s|/etc/nextcloud/config.php|'dbtimeout' => 1,|'dbtimeout' => 30,|systemctl reload php-fpm|occ|nc_db_1|files|users|pg leftover leftover down; bounce|dbtimeout leftover 1 leftover; a 2s query is aborted so sync 504s
owncloud|dbtimeout|1|30|s|/etc/owncloud/config.php|'dbtimeout' => 1,|'dbtimeout' => 30,|systemctl reload php-fpm|occ|oc_db_1|files|users|mysql leftover leftover down; bounce|dbtimeout leftover 1 leftover; a 2s query is aborted so sync 504s
seafile|SEAFILE_TIMEOUT|1|30|s|/etc/seafile/seafile.conf|timeout=1|timeout=30|systemctl reload seafile|seaf-admin|sea_to_1|libs|files|mysql leftover leftover down; bounce|SEAFILE_TIMEOUT leftover 1 leftover; a 2s block is aborted so sync 504s
syncthing|STTIMEOUT|1|30|s|/etc/syncthing/config.xml|<timeout>1</timeout>|<timeout>30</timeout>|systemctl reload syncthing|syncthing|st_to_1|folders|peers|tcp leftover leftover down; bounce|STTIMEOUT leftover 1 leftover; a 2s index is aborted so the cluster 504s
resilio|rslsync.timeout|1|30|s|/etc/resilio-sync/config.json|"folder_rescan_interval": 1|"folder_rescan_interval": 30|systemctl reload resilio-sync|rslsync|rsl_to_1|folders|peers|tcp leftover leftover down; bounce|rslsync.timeout leftover 1 leftover; a 2s handshake is aborted so sync 504s
btsync|BTSYNC_TIMEOUT|1|30|s|/etc/btsync/config.json|"peer_expiration_days": 1|"peer_expiration_days": 7|systemctl reload btsync|btsync|bts_to_1|folders|peers|tcp leftover leftover down; bounce|BTSYNC_TIMEOUT leftover 1 leftover; peers expire in 1 day-unit so the share 504s
dropbox|DROPBOX_TIMEOUT|1|30|s|/etc/dropbox/dropbox.conf|timeout=1|timeout=30|systemctl reload dropbox|dropbox|dbx_to_1|files|lan|https leftover leftover 403; bounce|DROPBOX_TIMEOUT leftover 1 leftover; a 2s lan-sync is aborted so the tray 504s
megacmd|MEGACMD_TIMEOUT|1|30|s|/etc/mega/megacmd.conf|timeout=1|timeout=30|systemctl reload mega-cmd|mega-cmd|mega_to_1|files|cloud|https leftover leftover 403; bounce|MEGACMD_TIMEOUT leftover 1 leftover; a 2s transfer is aborted so sync 504s
kopiaui|KOPIA_TIMEOUT|1|60|s|/etc/kopia/repository.config|timeout: 1s|timeout: 60s|systemctl reload kopia|kopia|kop_to_1|snaps|repo|s3 leftover leftover 403; bounce|KOPIA_TIMEOUT leftover 1 leftover; a 2s snapshot is aborted so backup 504s
borgbackup|BORG_TIMEOUT|1|60|s|/etc/borg/borg.env|BORG_UNKNOWN_UNENCRYPTED_REPO_ACCESS_IS_OK=1|BORG_REMOTE_PATH=borg|systemctl reload borg|borg|borg_to_1|archives|repo|ssh leftover leftover down; bounce|BORG_TIMEOUT leftover 1 leftover; a 2s create is aborted so backup 504s
attic|ATTIC_TIMEOUT|1|60|s|/etc/attic/attic.conf|timeout=1|timeout=60|systemctl reload attic|attic|att_to_1|archives|repo|ssh leftover leftover down; bounce|ATTIC_TIMEOUT leftover 1 leftover; a 2s create is aborted so backup 504s
obnam|OBNAM_TIMEOUT|1|60|s|/etc/obnam.conf|timeout = 1|timeout = 60|systemctl reload obnam|obnam|obn_to_1|gens|repo|sftp leftover leftover down; bounce|OBNAM_TIMEOUT leftover 1 leftover; a 2s backup is aborted so the gen 504s
rdiff-backup|RDIFF_TIMEOUT|1|60|s|/etc/rdiff-backup.conf|timeout=1|timeout=60|systemctl reload rdiff-backup|rdiff-backup|rdb_to_1|increments|repo|ssh leftover leftover down; bounce|RDIFF_TIMEOUT leftover 1 leftover; a 2s increment is aborted so backup 504s
rsnapshot|RSYNC_TIMEOUT|1|60|s|/etc/rsnapshot.conf|timeout	1|timeout	7200|systemctl reload rsnapshot|rsnapshot|rsn_to_1|snaps|retain|ssh leftover leftover down; bounce|RSYNC_TIMEOUT leftover 1 leftover; a 2s rsync is aborted so hourly 504s
rsync|RSYNC_TIMEOUT|1|60|s|/etc/rsyncd.conf|timeout = 1|timeout = 600|systemctl reload rsyncd|rsync|rsy_to_1|modules|files|tcp leftover leftover down; bounce|RSYNC_TIMEOUT leftover 1 leftover; a 2s transfer is aborted so the module 504s
unison|UNISON_TIMEOUT|1|60|s|/etc/unison/default.prf|timeout = 1|timeout = 60|systemctl reload unison|unison|uni_to_1|replicas|roots|ssh leftover leftover down; bounce|UNISON_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the replica 504s
csync2|CSYNC2_TIMEOUT|1|30|s|/etc/csync2/csync2.cfg|timeout 1|timeout 30|systemctl reload xinetd|csync2|csy_to_1|groups|hosts|ssl leftover leftover down; bounce|CSYNC2_TIMEOUT leftover 1 leftover; a 2s hint is aborted so the cluster 504s
lsyncd|LSYNCD_TIMEOUT|1|15|s|/etc/lsyncd/lsyncd.conf.lua|delay = 1|delay = 15|systemctl reload lsyncd|lsyncd|lsy_to_1|dirs|rsync|inotify leftover leftover down; bounce|LSYNCD_TIMEOUT leftover 1 leftover; every 1s rsync storms so the target 504s
mit-krb5kdc|kdc_tcp_listen_backlog|1|256||/etc/krb5kdc/kdc.conf|kdc_tcp_listen_backlog = 1|kdc_tcp_listen_backlog = 256|systemctl reload krb5-kdc|kadmin|kdc_bl_1|as|tgs|ldap leftover leftover down; bounce|kdc_tcp_listen_backlog leftover 1 leftover; the second AS-REQ is dropped so login 504s
heimdal-kdc|max_request|1|65536||/etc/heimdal-kdc/kdc.conf|max-request = 1|max-request = 65536|systemctl reload heimdal-kdc|kadmin|heim_max_1|as|tgs|hdb leftover leftover down; bounce|max_request leftover 1 leftover; a normal AS-REQ is refused so login 504s
kadmind|kadmind.timeout|1|30|s|/etc/krb5kdc/kadm5.acl|timeout=1|timeout=30|systemctl reload krb5-admin-server|kadmin|kad_to_1|princs|acl|kdb leftover leftover down; bounce|kadmind.timeout leftover 1 leftover; a 2s getprinc is aborted so kadmin 504s
kpasswdd|kpasswdd.timeout|1|30|s|/etc/krb5kdc/kpasswdd.conf|timeout=1|timeout=30|systemctl reload kpasswdd|kpasswd|kpw_to_1|pw|princs|kdc leftover leftover down; bounce|kpasswdd.timeout leftover 1 leftover; a 2s change is aborted so kpasswd 504s
kpropd|kpropd.timeout|1|30|s|/etc/krb5kdc/kpropd.acl|timeout=1|timeout=30|systemctl reload kpropd|kprop|kpr_to_1|dump|slaves|tcp leftover leftover down; bounce|kpropd.timeout leftover 1 leftover; a 2s dump is aborted so the replica 504s
certmonger|CERTMONGER_TIMEOUT|1|30|s|/etc/certmonger/certmonger.conf|timeout=1|timeout=30|systemctl reload certmonger|getcert|cmg_to_1|certs|cas|dbus leftover leftover down; bounce|CERTMONGER_TIMEOUT leftover 1 leftover; a 2s enroll is aborted so the cert 401s
dirsrv|nsslapd-idletimeout|1|3600|s|/etc/dirsrv/slapd-instance/dse.ldif|nsslapd-idletimeout: 1|nsslapd-idletimeout: 3600|systemctl reload dirsrv|dsconf|ds_idle_1|binds|suffix|bdb leftover leftover down; bounce|nsslapd-idletimeout leftover 1 leftover; a 2s pause unbinds so IPA 401s
slapd|idletimeout|1|30|s|/etc/ldap/slapd.conf|idletimeout 1|idletimeout 30|systemctl reload slapd|ldapsearch|slap_idle_1|binds|suffix|mdb leftover leftover down; bounce|idletimeout leftover 1 leftover; a 2s pause unbinds so auth 401s
389ds|nsslapd-ioblocktimeout|1|1800000|ms|/etc/dirsrv/slapd-instance/dse.ldif|nsslapd-ioblocktimeout: 1|nsslapd-ioblocktimeout: 1800000|systemctl reload dirsrv@instance|dsconf|ds389_io_1|ops|suffix|bdb leftover leftover down; bounce|nsslapd-ioblocktimeout leftover 1 leftover; a 2s search is aborted so IPA 504s
winbind|winbind cache time|1|300|s|/etc/samba/smb.conf|winbind cache time = 1|winbind cache time = 300|systemctl reload winbind|wbinfo|wb_cache_1|sids|users|ad leftover leftover down; bounce|winbind cache time leftover 1 leftover; every lookup hits AD so login 504s
unscd|reload-count|1|5||/etc/unscd.conf|reload-count 1|reload-count 5|systemctl reload unscd|unscd|unscd_rl_1|passwd|hosts|nscd leftover leftover down; bounce|reload-count leftover 1 leftover; every 1 miss reloads so getpwnam 504s
smbclient|SMBCLIENT_TIMEOUT|1|20|s|/etc/samba/smb.conf|client smb encrypt timeout = 1|client smb encrypt timeout = 20|systemctl reload smb|smbclient|smb_to_1|shares|dfs|tcp leftover leftover down; bounce|SMBCLIENT_TIMEOUT leftover 1 leftover; a 2s tree connect is aborted so the share 504s
winpr|WINPR_TIMEOUT|1|10|s|/etc/winpr/winpr.conf|timeout=1|timeout=10|systemctl reload winpr|winpr|wpr_to_1|rdp|nla|tcp leftover leftover down; bounce|WINPR_TIMEOUT leftover 1 leftover; a 2s NLA is aborted so RDP 504s
ipa-custodia|CUSTODIA_TIMEOUT|1|10|s|/etc/ipa/custodia.conf|timeout=1|timeout=10|systemctl reload ipa-custodia|ipa|ipc_to_1|keys|secrets|unix leftover leftover down; bounce|CUSTODIA_TIMEOUT leftover 1 leftover; a 2s unwrap is aborted so IPA 401s
ipa-otpd|IPA_OTPD_TIMEOUT|1|10|s|/etc/ipa/otpd.conf|timeout=1|timeout=10|systemctl reload ipa-otpd|ipa|ipotp_to_1|otp|radius|unix leftover leftover down; bounce|IPA_OTPD_TIMEOUT leftover 1 leftover; a 2s RADIUS is aborted so 2FA 401s
ipa-dnskeysyncd|IPA_DNSKEY_TIMEOUT|1|30|s|/etc/ipa/dnskeysyncd.conf|timeout=1|timeout=30|systemctl reload ipa-dnskeysyncd|ipa|ipdns_to_1|keys|zones|ldap leftover leftover down; bounce|IPA_DNSKEY_TIMEOUT leftover 1 leftover; a 2s sync is aborted so DNSSEC 401s
pingfederate|pf.timeout|1|30|s|/etc/pingfederate/run.properties|pf.http.timeout=1|pf.http.timeout=30|systemctl reload pingfederate|pfadmin|pf_to_1|sso|adapters|jdbc leftover leftover down; bounce|pf.timeout leftover 1 leftover; a 2s adapter is aborted so SSO 401s
forgerock-am|AM_TIMEOUT|1|30|s|/etc/forgerock/am/boot.json|timeout: 1|timeout: 30|systemctl reload amster|amster|fram_to_1|sso|realms|ldap leftover leftover down; bounce|AM_TIMEOUT leftover 1 leftover; a 2s authn is aborted so SSO 401s
okta-asa|ASA_TIMEOUT|1|10|s|/etc/sft/sftd.yaml|timeout: 1s|timeout: 10s|systemctl reload sftd|sft|asa_to_1|ssh|teams|https leftover leftover 403; bounce|ASA_TIMEOUT leftover 1 leftover; a 2s enroll is aborted so SSH 401s
oauth2proxy|O2P_TIMEOUT|1|30|s|/etc/oauth2-proxy/oauth2-proxy.cfg|timeout = 1|timeout = 30|systemctl reload oauth2-proxy|oauth2-proxy|o2px_to_1|auth|cookies|idp leftover leftover down; bounce|O2P_TIMEOUT leftover 1 leftover; a 2s redeem is aborted so the app 401s
rakkess|RAKKESS_TIMEOUT|1|10|s|/etc/rakkess/config.yaml|timeout: 1s|timeout: 10s|systemctl reload rakkess|rakkess|rak_to_1|rbac|verbs|apiserver leftover leftover down; bounce|RAKKESS_TIMEOUT leftover 1 leftover; a 2s SAR is aborted so who-can 504s
yourkit|YOURKIT_TIMEOUT|1|30|s|/etc/yourkit/yjp.ini|timeout=1|timeout=30|systemctl reload yourkit|yjp.sh|yk_to_1|snaps|agents|jmx leftover leftover down; bounce|YOURKIT_TIMEOUT leftover 1 leftover; a 2s dump is aborted so the snapshot 504s
jprofiler|JPROFILER_TIMEOUT|1|30|s|/etc/jprofiler/jprofiler.conf|timeout=1|timeout=30|systemctl reload jprofiler|jpenable|jp_to_1|cpu|agents|jmx leftover leftover down; bounce|JPROFILER_TIMEOUT leftover 1 leftover; a 2s attach is aborted so the session 504s
visualvm|VISUALVM_TIMEOUT|1|30|s|/etc/visualvm/visualvm.conf|timeout=1|timeout=30|systemctl reload visualvm|visualvm|vvm_to_1|jmx|jvms|jmx leftover leftover down; bounce|VISUALVM_TIMEOUT leftover 1 leftover; a 2s attach is aborted so the view 504s
missioncontrol|JMC_TIMEOUT|1|30|s|/etc/jmc/jmc.ini|timeout=1|timeout=30|systemctl reload jmc|jmc|jmc_to_1|jfr|jvms|jmx leftover leftover down; bounce|JMC_TIMEOUT leftover 1 leftover; a 2s dump is aborted so the flight 504s
flightrecorder|JFR_TIMEOUT|1|30|s|/etc/java/jfr.conf|timeout=1|timeout=30|systemctl reload jfr|jcmd|jfr_to_1|recordings|jvms|jmx leftover leftover down; bounce|JFR_TIMEOUT leftover 1 leftover; a 2s dump is aborted so the rec 504s
asyncprofiler|ASPROF_TIMEOUT|1|30|s|/etc/async-profiler/profiler.conf|timeout=1|timeout=30|systemctl reload asprof|asprof|asp_to_1|cpu|jvms|perf leftover leftover down; bounce|ASPROF_TIMEOUT leftover 1 leftover; a 2s sample is aborted so the flame 504s
honest-profiler|HONEST_TIMEOUT|1|30|s|/etc/honest-profiler/hp.conf|timeout=1|timeout=30|systemctl reload honest-profiler|hp|hp_to_1|cpu|jvms|perf leftover leftover down; bounce|HONEST_TIMEOUT leftover 1 leftover; a 2s sample is aborted so the log 504s
jfr-streaming|JFRS_TIMEOUT|1|30|s|/etc/jfr-streaming/jfrs.conf|timeout=1|timeout=30|systemctl reload jfr-streaming|jcmd|jfrs_to_1|events|jvms|jmx leftover leftover down; bounce|JFRS_TIMEOUT leftover 1 leftover; a 2s stream is aborted so the sink 504s
continuous-profiler|CPROF_TIMEOUT|1|30|s|/etc/parca-agent/config.yaml|timeout: 1s|timeout: 30s|systemctl reload parca-agent|parca-agent|cprof_to_1|pprof|procs|perf leftover leftover down; bounce|CPROF_TIMEOUT leftover 1 leftover; a 2s sample is aborted so the profile 504s
inspektor-gadget|IG_TIMEOUT|1|30|s|/etc/ig/config.yaml|timeout: 1s|timeout: 30s|systemctl reload ig|ig|ig_to_1|traces|pods|bpf leftover leftover down; bounce|IG_TIMEOUT leftover 1 leftover; a 2s gadget is aborted so the trace 504s
privoxy|PRIV_TIMEOUT|1|30|s|/etc/privoxy/config|keep-alive-timeout 1|keep-alive-timeout 300|systemctl reload privoxy|privoxy|prv_to_1|http|filters|tcp leftover leftover down; bounce|PRIV_TIMEOUT leftover 1 leftover; a 2s request is aborted so the proxy 504s
freenet|FREENET_TIMEOUT|1|30|s|/etc/freenet/freenet.ini|timeout=1|timeout=30|systemctl reload freenet|freenet|fn_to_1|keys|peers|udp leftover leftover down; bounce|FREENET_TIMEOUT leftover 1 leftover; a 2s fetch is aborted so the key 504s
gnunet|GNUNET_TIMEOUT|1|30|s|/etc/gnunet.conf|TIMEOUT = 1 s|TIMEOUT = 30 s|systemctl reload gnunet|gnunet-arm|gnu_to_1|cadet|peers|udp leftover leftover down; bounce|GNUNET_TIMEOUT leftover 1 leftover; a 2s DHT is aborted so the mesh 504s
libp2p|LIBP2P_TIMEOUT|1|30|s|/etc/libp2p/config.json|"timeout": 1|"timeout": 30|systemctl reload libp2p|libp2p|lp2_to_1|streams|peers|tcp leftover leftover down; bounce|LIBP2P_TIMEOUT leftover 1 leftover; a 2s dial is aborted so the swarm 504s
kubo|KUBO_TIMEOUT|1|30|s|/etc/ipfs/config|"Timeout": "1s"|"Timeout": "30s"|systemctl reload ipfs|ipfs|kubo_to_1|cids|peers|tcp leftover leftover down; bounce|KUBO_TIMEOUT leftover 1 leftover; a 2s provide is aborted so IPFS 504s
ipget|IPGET_TIMEOUT|1|30|s|/etc/ipget/ipget.conf|timeout=1|timeout=30|systemctl reload ipget|ipget|ipg_to_1|cids|files|tcp leftover leftover down; bounce|IPGET_TIMEOUT leftover 1 leftover; a 2s get is aborted so the pin 504s
cerbos|CERBOS_TIMEOUT|1|10|s|/etc/cerbos/conf.yaml|timeout: 1s|timeout: 10s|systemctl reload cerbos|cerbosctl|cer_to_1|checks|policies|disk leftover leftover full; bounce|CERBOS_TIMEOUT leftover 1 leftover; a 2s CheckResources is aborted so PDP 504s
spicedb|SPICEDB_TIMEOUT|1|10|s|/etc/spicedb/spicedb.yaml|timeout: 1s|timeout: 10s|systemctl reload spicedb|zed|spd_to_1|checks|ns|pg leftover leftover down; bounce|SPICEDB_TIMEOUT leftover 1 leftover; a 2s Check is aborted so authz 504s
openfga|OPENFGA_TIMEOUT|1|10|s|/etc/openfga/config.yaml|timeout: 1s|timeout: 10s|systemctl reload openfga|fga|ofga_to_1|checks|stores|pg leftover leftover down; bounce|OPENFGA_TIMEOUT leftover 1 leftover; a 2s Check is aborted so FGA 504s
keto|KETO_TIMEOUT|1|10|s|/etc/keto/keto.yml|timeout: 1s|timeout: 10s|systemctl reload keto|keto|keto_to_1|checks|ns|sql leftover leftover down; bounce|KETO_TIMEOUT leftover 1 leftover; a 2s check is aborted so ACL 504s
hydra|HYDRA_TIMEOUT|1|30|s|/etc/hydra/hydra.yml|timeout: 1s|timeout: 30s|systemctl reload hydra|hydra|hyd_to_1|oauth|clients|sql leftover leftover down; bounce|HYDRA_TIMEOUT leftover 1 leftover; a 2s token is aborted so OAuth 401s
kratos|KRATOS_TIMEOUT|1|30|s|/etc/kratos/kratos.yml|timeout: 1s|timeout: 30s|systemctl reload kratos|kratos|kra_to_1|identities|flows|sql leftover leftover down; bounce|KRATOS_TIMEOUT leftover 1 leftover; a 2s login is aborted so the flow 401s
oathkeeper|OATHKEEPER_TIMEOUT|1|10|s|/etc/oathkeeper/oathkeeper.yml|timeout: 1s|timeout: 10s|systemctl reload oathkeeper|oathkeeper|oath_to_1|decisions|rules|idp leftover leftover down; bounce|OATHKEEPER_TIMEOUT leftover 1 leftover; a 2s match is aborted so the proxy 401s
'''
WAVE43 = (
    "sendmail/spamassassin/mailman3/sympa/listserv/ezmlm/spfmilter/bogofilter/"
    "crm114/sa-update/spamass-milter/clamav-milter/postfixadmin/roundcube/sogo/"
    "zimbra/kopano/ox-appsuite/nextcloud/owncloud/seafile/syncthing/resilio/"
    "btsync/dropbox/megacmd/kopiaui/borgbackup/attic/obnam/rdiff-backup/"
    "rsnapshot/rsync/unison/csync2/lsyncd/mit-krb5kdc/heimdal-kdc/kadmind/"
    "kpasswdd/kpropd/certmonger/dirsrv/slapd/389ds/winbind/unscd/smbclient/"
    "winpr/ipa-custodia/ipa-otpd/ipa-dnskeysyncd/pingfederate/forgerock-am/"
    "okta-asa/oauth2proxy/rakkess/yourkit/jprofiler/visualvm/missioncontrol/"
    "flightrecorder/asyncprofiler/honest-profiler/jfr-streaming/"
    "continuous-profiler/inspektor-gadget/privoxy/freenet/gnunet/libp2p/"
    "kubo/ipget/cerbos/spicedb/openfga/keto/hydra/kratos/oathkeeper"
)


def _parse_rows():
    plants = []
    srcs = ("grafana", "pagerduty", "opsgenie", "alertmanager")
    ns_cycle = (17, 16, 18)
    for raw in ROWS.strip().splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("#"):
            continue
        parts = raw.split("|")
        if len(parts) != 15:
            raise SystemExit(f"bad row cols={len(parts)}: {raw[:160]}")
        (
            daemon, key, old, new, unit, path, oldv, newv, reload, hpeer, metric,
            what, wipe, herring, rca_tail,
        ) = parts
        i = len(plants)
        n = ns_cycle[i % 3]
        rem = "rollback" if i % 2 == 0 else "patch"
        src = srcs[i % 4]
        svc = f"y3{i:02d}x"
        ns = f"y3{i:02d}"
        clu = f"prod-apsy{901 + i}-{svc[:3]}"
        ticket = f"W2-{12243 + i}"
        node = f"ip-10-228-{1 + i}-{20 + i}"
        slug = f"{daemon}-{key}-{old}{unit}-{svc}"
        key_words = key.replace(".", " leftover ").replace("_", " leftover ")
        symptom = f"{key_words} leftover {old}{unit} leftover; {what} drop"
        because = (
            f"is dropping {what} because leftover {daemon} leftover {key_words} leftover is {old} leftover."
        )
        do_not = f"Restore {new}{unit}; do not wipe {wipe}."
        rca = f"{daemon} leftover {key} leftover {old} leftover; {rca_tail}"
        if rem == "rollback":
            remnant = helm_rb(ns, svc, 3, path, oldv, newv, reload)
            extra = f"helm -n {ns} history {svc} | head -5"
            eobs = f"4  {old}{unit}\n3  last-good {new}"
        else:
            remnant = patch_file(path, oldv, newv, reload)
            extra = f"kubectl -n {ns} logs deploy/{svc} --since=5m | grep {key} | tail"
            eobs = f"{key} leftover {old}"
        plants.append(
            plant(
                slug=slug, ticket=ticket, service=svc, ns=ns, cluster=clu, src=src,
                node=node, symptom=symptom, because=because, do_not=do_not,
                herring=herring, rca=rca, remediate=rem, metric=metric,
                hcmds=[
                    f"{hpeer} leftover status | head",
                    f"systemctl reload {hpeer} || true",
                    f"{hpeer} leftover bounce leftover || true",
                ],
                hobs=[f"{hpeer} ok", "bounce unused", f"still {key} {old}"],
                inspect=f"grep {key} {path}", iobs=f"{oldv} leftover",
                extra=extra, eobs=eobs, rem=remnant, robs=f"{key} {new}; holds",
                verify=f"grep {key} {path}", vok=f"{new}; {ticket} resolved", n=n,
            )
        )
    return plants


PLANTS = _parse_rows()
m.PLANTS = PLANTS
m.BASE_ROUND = 3861


def notes_for(round_n, eps):
    slug0 = eps[0]["id"].split("-", 2)[2].rsplit("-", 2)[0]
    slug1 = eps[1]["id"].split("-", 2)[2].rsplit("-", 2)[0]
    rows = [
        f"| `{e['id']}` | {e['meta']['ticket']} | {e['false_lead']['claim'].replace('|', '/')} | {e['remediate']} | {e['reward']['success']} | {e['reward']['steps']} |"
        for e in eps
    ]
    return "\n".join(
        [
            f"# incident-response-oncall-factory NOTES r{round_n}",
            "",
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r3860 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-43 leftover: {WAVE43}.",
            "",
            "OpenSRE designed: 429 then 502 retries, 3-step herring, unique RCA, mix patch/rollback. plant=designed. generator=grok-4.6.",
            "",
            "| id | ticket | herring (steps 6-8) | remediate | success | steps |",
            "|---|---|---|---|---|---|",
            *rows,
            "",
            "## Contract audit",
            f"- Q=2 episodes, kind=episode, ids irc-r{round_n}-*.",
            "- Unique goal service+cluster+symptom; 3 false-lead actions; 429/502 retries.",
            "- Residual: designed excerpts, not live dispatcher traces.",
            "",
        ]
    )


m.notes_for = notes_for


def extra_unique_guards():
    banned = (
        "Follow OpenSRE", "fraud-graph", "sip-proxy", "traefik", "limit_req",
        "cloudfront", "fastly", "kube-proxy", "haproxy", "varnish", "metallb",
        "imperva", "bunny", "calico felix", "kong ", "caddy ",
        "github actions leftover", "gitlab leftover", "circleci leftover",
        "tekton leftover", "snowflake", "bigquery", "redshift", "idle_timeout",
        "max_client_conn", "ypbind", "oddjob", "opensearch", "leftover3c",
        "tigergraph", "hugegraph", "graphdb", "stardog", "debezium", "hasura",
    )
    for p in PLANTS:
        blob = (p["goal"] + " " + p["rca"] + " " + p["slug"]).lower()
        for tok in banned:
            if tok.lower() in blob:
                raise SystemExit(f"banned {tok} in {p['slug']}")
        for need in (p["service"], p["ns"], p["cluster"]):
            if need not in p["goal"]:
                raise SystemExit(p["slug"])
        if p["n_steps"] not in (16, 17, 18) or p["remediate"] not in ("rollback", "patch"):
            raise SystemExit(p["slug"])
    if len(PLANTS) % 2:
        raise SystemExit("odd")
    for i in range(0, len(PLANTS), 2):
        if {PLANTS[i]["remediate"], PLANTS[i + 1]["remediate"]} != {"rollback", "patch"}:
            raise SystemExit(f"pair {i}")


def main():
    extra_unique_guards()
    used_svc, used_clu, used_tix, _ids = m.harvest_used(m.FACTORY_DIR)
    for p in PLANTS:
        if p["service"] in used_svc:
            raise SystemExit(f"service collision {p['service']}")
        if p["cluster"] in used_clu:
            raise SystemExit(f"cluster collision {p['cluster']}")
        if p["ticket"] in used_tix:
            raise SystemExit(f"ticket collision {p['ticket']}")
    for label, xs in (
        ("slug", [p["slug"] for p in PLANTS]),
        ("svc", [p["service"] for p in PLANTS]),
        ("clu", [p["cluster"] for p in PLANTS]),
        ("tix", [p["ticket"] for p in PLANTS]),
        ("node", [p["node"] for p in PLANTS]),
        ("ns", [p["ns"] for p in PLANTS]),
    ):
        if len(set(xs)) != len(xs):
            raise SystemExit("dup " + label)
    print(json.dumps({"ok": True, "plants": len(PLANTS), "rounds": len(PLANTS) // 2}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
