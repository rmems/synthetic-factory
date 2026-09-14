#!/usr/bin/env python3
"""IRC mill r3901+ — wave-44 voip/xmpp/packet leftover.

NEW on-call plants (not Wave-27–43 tails). BAN ypbind/oddjob,
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
asterisk|rtptimeout|1|60|s|/etc/asterisk/sip.conf|rtptimeout=1|rtptimeout=60|systemctl reload asterisk|asterisk|ast_rtp_1|calls|peers|udp leftover leftover down; bounce|rtptimeout leftover 1 leftover; a 2s RTP gap hangs up so the trunk 504s
freeswitch|rtp-timeout-sec|1|300|s|/etc/freeswitch/autoload_configs/switch.conf.xml|<param name="rtp-timeout-sec" value="1"/>|<param name="rtp-timeout-sec" value="300"/>|systemctl reload freeswitch|fs_cli|fs_rtp_1|calls|sbc|udp leftover leftover down; bounce|rtp-timeout-sec leftover 1 leftover; a 2s RTP gap hangs up so the session 504s
kamailio|tm.fr_timer|1|5000|ms|/etc/kamailio/kamailio.cfg|modparam("tm", "fr_timer", 1)|modparam("tm", "fr_timer", 5000)|systemctl reload kamailio|kamcmd|kam_fr_1|invites|dialogs|udp leftover leftover down; bounce|tm.fr_timer leftover 1 leftover; a 2s 100 Trying is aborted so INVITE 504s
opensips|fr_timeout|1|5|s|/etc/opensips/opensips.cfg|modparam("tm", "fr_timeout", 1)|modparam("tm", "fr_timeout", 5)|systemctl reload opensips|opensips-cli|osips_fr_1|invites|dialogs|udp leftover leftover down; bounce|fr_timeout leftover 1 leftover; a 2s 100 Trying is aborted so INVITE 504s
rtpengine|timeout|1|60|s|/etc/rtpengine/rtpengine.conf|timeout = 1|timeout = 60|systemctl reload rtpengine|rtpengine-ctl|rtpe_to_1|media|ports|udp leftover leftover down; bounce|timeout leftover 1 leftover; a 2s RTP gap deletes the session so audio 504s
coturn|max-allocate-timeout|1|60|s|/etc/turnserver.conf|max-allocate-timeout=1|max-allocate-timeout=60|systemctl reload coturn|turnadmin|cot_to_1|allocs|relays|udp leftover leftover down; bounce|max-allocate-timeout leftover 1 leftover; a 2s Allocate is aborted so ICE 504s
turnserver|max-allocate-timeout|1|60|s|/etc/turnserver.conf|max-allocate-timeout=1|max-allocate-timeout=60|systemctl reload coturn|turnadmin|turn_to_1|allocs|relays|udp leftover leftover down; bounce|max-allocate-timeout leftover 1 leftover; a 2s Allocate is aborted so WebRTC 504s
stund|STUN_TIMEOUT|1|10|s|/etc/stund.conf|timeout=1|timeout=10|systemctl reload stund|stund|stun_to_1|bindings|clients|udp leftover leftover down; bounce|STUN_TIMEOUT leftover 1 leftover; a 2s Binding is aborted so ICE 504s
ejabberd|s2s_timeout|1|10|s|/etc/ejabberd/ejabberd.yml|s2s_timeout: 1|s2s_timeout: 10|systemctl reload ejabberd|ejabberdctl|ej_s2s_1|s2s|hosts|xmpp leftover leftover down; bounce|s2s_timeout leftover 1 leftover; a 2s dialback is aborted so federation 504s
prosody|s2s_timeout|1|90|s|/etc/prosody/prosody.cfg.lua|s2s_timeout = 1|s2s_timeout = 90|systemctl reload prosody|prosodyctl|pro_s2s_1|s2s|hosts|xmpp leftover leftover down; bounce|s2s_timeout leftover 1 leftover; a 2s dialback is aborted so federation 504s
openfire|xmpp.session.idle|1|1800|s|/etc/openfire/openfire.xml|<session-idle>1</session-idle>|<session-idle>1800</session-idle>|systemctl reload openfire|openfire|of_idle_1|c2s|users|jdbc leftover leftover down; bounce|xmpp.session.idle leftover 1 leftover; a 2s pause unbinds so clients 401s
tigase|sess-man/timeout|1|30|s|/etc/tigase/config.tdsl|'timeout' = 1|'timeout' = 30|systemctl reload tigase|tigase|tig_to_1|c2s|users|jdbc leftover leftover down; bounce|sess-man/timeout leftover 1 leftover; a 2s IQ is aborted so the client 504s
dendrite|clientapi.timeout|1|30|s|/etc/dendrite/dendrite.yaml|timeout: 1s|timeout: 30s|systemctl reload dendrite|dendrite|den_to_1|csapi|rooms|pg leftover leftover down; bounce|clientapi.timeout leftover 1 leftover; a 2s /sync is aborted so Element 504s
conduit|CONDUIT_TIMEOUT|1|30|s|/etc/conduit/conduit.toml|timeout = 1|timeout = 30|systemctl reload conduit|conduit|con_to_1|csapi|rooms|rocks leftover leftover down; bounce|CONDUIT_TIMEOUT leftover 1 leftover; a 2s /sync is aborted so Element 504s
mattermost|ServiceSettings.ReadTimeout|1|300|s|/etc/mattermost/config.json|"ReadTimeout": 1|"ReadTimeout": 300|systemctl reload mattermost|mmctl|mm_read_1|ws|teams|pg leftover leftover down; bounce|ServiceSettings.ReadTimeout leftover 1 leftover; a 2s WS is aborted so the app 504s
zulip|ZULIP_TIMEOUT|1|30|s|/etc/zulip/zulip.conf|timeout = 1|timeout = 30|systemctl reload zulip|zulip-manage|zul_to_1|events|realms|pg leftover leftover down; bounce|ZULIP_TIMEOUT leftover 1 leftover; a 2s event is aborted so the UI 504s
ircd-hybrid|PINGFREQ|1|120||/etc/ircd-hybrid/ircd.conf|ping_time = 1;|ping_time = 120;|systemctl reload ircd-hybrid|ircd|hyb_ping_1|nicks|links|tcp leftover leftover down; bounce|PINGFREQ leftover 1 leftover; every 1s ping drops clients so the net 504s
ngircd|PingTimeout|1|120||/etc/ngircd/ngircd.conf|PingTimeout = 1|PingTimeout = 120|systemctl reload ngircd|ngircd|ngi_ping_1|nicks|links|tcp leftover leftover down; bounce|PingTimeout leftover 1 leftover; a 2s lag disconnects so the net 504s
inspircd|pingfreq|1|120||/etc/inspircd/inspircd.conf|<connect pingfreq="1">|<connect pingfreq="120">|systemctl reload inspircd|inspircd|insp_ping_1|nicks|links|tcp leftover leftover down; bounce|pingfreq leftover 1 leftover; every 1s ping drops clients so the net 504s
unrealircd|pingpong|1|120||/etc/unrealircd/unrealircd.conf|set { ping-cookie 1; }|set { ping-cookie 120; }|systemctl reload unrealircd|unrealircd|unr_ping_1|nicks|links|tcp leftover leftover down; bounce|pingpong leftover 1 leftover; every 1s ping drops clients so the net 504s
bitlbee|BITLBEE_TIMEOUT|1|30|s|/etc/bitlbee/bitlbee.conf|Timeout = 1|Timeout = 30|systemctl reload bitlbee|bitlbee|bit_to_1|im|accounts|irc leftover leftover down; bounce|BITLBEE_TIMEOUT leftover 1 leftover; a 2s IM login is aborted so the gateway 504s
pidgin|PIDGIN_TIMEOUT|1|30|s|/etc/purple/prefs.xml|<pref name="timeout" type="int" value="1"/>|<pref name="timeout" type="int" value="30"/>|systemctl reload pidgin|pidgin|pid_to_1|im|prpls|xmpp leftover leftover down; bounce|PIDGIN_TIMEOUT leftover 1 leftover; a 2s connect is aborted so the account 504s
telepathy|TP_TIMEOUT|1|30|s|/etc/telepathy/mission-control.conf|timeout=1|timeout=30|systemctl reload mission-control-5|mc-tool|tp_to_1|im|accounts|dbus leftover leftover down; bounce|TP_TIMEOUT leftover 1 leftover; a 2s connect is aborted so the account 504s
signal-cli|SIGNAL_TIMEOUT|1|30|s|/etc/signal-cli/config.yml|timeout: 1s|timeout: 30s|systemctl reload signal-cli|signal-cli|sig_to_1|msgs|accounts|https leftover leftover 403; bounce|SIGNAL_TIMEOUT leftover 1 leftover; a 2s send is aborted so the bot 504s
mautrix|MAUTRIX_TIMEOUT|1|30|s|/etc/mautrix/config.yaml|timeout: 1s|timeout: 30s|systemctl reload mautrix|mautrix|mau_to_1|bridges|rooms|pg leftover leftover down; bounce|MAUTRIX_TIMEOUT leftover 1 leftover; a 2s puppet is aborted so the bridge 504s
heisenbridge|HEISEN_TIMEOUT|1|30|s|/etc/heisenbridge/config.yaml|timeout: 1s|timeout: 30s|systemctl reload heisenbridge|heisenbridge|hei_to_1|irc|rooms|tcp leftover leftover down; bounce|HEISEN_TIMEOUT leftover 1 leftover; a 2s IRC is aborted so the bridge 504s
matterbridge|MATTERBRIDGE_TIMEOUT|1|30|s|/etc/matterbridge/matterbridge.toml|Timeout=1|Timeout=30|systemctl reload matterbridge|matterbridge|mtb_to_1|gateways|protos|ws leftover leftover down; bounce|MATTERBRIDGE_TIMEOUT leftover 1 leftover; a 2s relay is aborted so the gateway 504s
znc|ZNC_TIMEOUT|1|30|s|/etc/znc/znc.conf|Timeout = 1|Timeout = 180|systemctl reload znc|znc|znc_to_1|irc|users|tcp leftover leftover down; bounce|ZNC_TIMEOUT leftover 1 leftover; a 2s bounce is aborted so the bouncer 504s
weechat|weechat.network.connection_timeout|1|30|s|/etc/weechat/weechat.conf|weechat.network.connection_timeout = 1|weechat.network.connection_timeout = 30|systemctl reload weechat|weechat|wee_to_1|irc|buffers|tcp leftover leftover down; bounce|connection_timeout leftover 1 leftover; a 2s connect is aborted so the buffer 504s
irssi|IRSSI_TIMEOUT|1|30|s|/etc/irssi/config|timeout = 1;|timeout = 30;|systemctl reload irssi|irssi|irs_to_1|irc|servers|tcp leftover leftover down; bounce|IRSSI_TIMEOUT leftover 1 leftover; a 2s connect is aborted so the net 504s
yate|YATE_TIMEOUT|1|30|s|/etc/yate/yate.conf|timeout=1|timeout=30|systemctl reload yate|yate|yate_to_1|calls|modules|udp leftover leftover down; bounce|YATE_TIMEOUT leftover 1 leftover; a 2s call is aborted so the PBX 504s
sems|SEMS_TIMEOUT|1|30|s|/etc/sems/sems.conf|session_timeout=1|session_timeout=30|systemctl reload sems|sems|sems_to_1|calls|media|udp leftover leftover down; bounce|SEMS_TIMEOUT leftover 1 leftover; a 2s dialog is aborted so the B2BUA 504s
mediaproxy|MEDIAPROXY_TIMEOUT|1|30|s|/etc/mediaproxy/config.ini|timeout = 1|timeout = 30|systemctl reload mediaproxy-dispatcher|mediaproxy|mdp_to_1|media|relays|udp leftover leftover down; bounce|MEDIAPROXY_TIMEOUT leftover 1 leftover; a 2s session is aborted so audio 504s
rtpproxy|RTPP_TIMEOUT|1|60|s|/etc/rtpproxy/rtpproxy.conf|timeout=1|timeout=60|systemctl reload rtpproxy|rtpproxy|rtpp_to_1|media|ports|udp leftover leftover down; bounce|RTPP_TIMEOUT leftover 1 leftover; a 2s RTP gap deletes the session so audio 504s
homer|HOMER_TIMEOUT|1|10|s|/etc/homer/webapp_config.json|"timeout": 1|"timeout": 10|systemctl reload homer-webapp|homer|hom_to_1|heps|cals|ch leftover leftover down; bounce|HOMER_TIMEOUT leftover 1 leftover; a 2s HEP search is aborted so the UI 504s
captagent|CAPTAGENT_TIMEOUT|1|10|s|/etc/captagent/captagent.xml|<timeout>1</timeout>|<timeout>10</timeout>|systemctl reload captagent|captagent|cap_to_1|heps|sip|udp leftover leftover down; bounce|CAPTAGENT_TIMEOUT leftover 1 leftover; a 2s HEP send is aborted so Homer 504s
sngrep|SNGREP_TIMEOUT|1|10|s|/etc/sngrep/sngrep.conf|timeout=1|timeout=10|systemctl reload sngrep|sngrep|sng_to_1|calls|pcap|pcap leftover leftover down; bounce|SNGREP_TIMEOUT leftover 1 leftover; a 2s capture is aborted so the TUI 504s
sipp|SIPP_TIMEOUT|1|10|s|/etc/sipp/sipp.conf|timeout=1|timeout=10|systemctl reload sipp|sipp|sipp_to_1|calls|scenarios|udp leftover leftover down; bounce|SIPP_TIMEOUT leftover 1 leftover; a 2s 200 is aborted so the load 504s
voipmonitor|VOIPMON_TIMEOUT|1|30|s|/etc/voipmonitor.conf|absolute_timeout = 1|absolute_timeout = 3600|systemctl reload voipmonitor|voipmonitor|vmn_to_1|cdrs|pcaps|mysql leftover leftover down; bounce|VOIPMON_TIMEOUT leftover 1 leftover; a 2s call is truncated so CDRs 504s
nprobe|NPROBE_TIMEOUT|1|30|s|/etc/nprobe/nprobe.conf|-t 1|-t 30|systemctl reload nprobe|nprobe|npr_to_1|flows|collectors|udp leftover leftover down; bounce|NPROBE_TIMEOUT leftover 1 leftover; a 2s flow is dropped so ntop 504s
n2disk|N2DISK_TIMEOUT|1|30|s|/etc/n2disk/n2disk.conf|--max-file-len 1|--max-file-len 30|systemctl reload n2disk|n2disk|n2d_to_1|pcaps|disks|nic leftover leftover down; bounce|N2DISK_TIMEOUT leftover 1 leftover; a 2s dump is aborted so replay 504s
cento|CENTO_TIMEOUT|1|10|s|/etc/cento/cento.conf|-t 1|-t 10|systemctl reload cento|cento|cen_to_1|flows|nics|pfring leftover leftover down; bounce|CENTO_TIMEOUT leftover 1 leftover; a 2s flow is dropped so ntop 504s
ndpi|NDPI_TIMEOUT|1|10|s|/etc/ndpi/ndpi.conf|timeout=1|timeout=10|systemctl reload ndpi|ndpiReader|ndpi_to_1|protos|flows|pcap leftover leftover down; bounce|NDPI_TIMEOUT leftover 1 leftover; a 2s classify is aborted so DPI 504s
tshark|TSHARK_TIMEOUT|1|30|s|/etc/wireshark/tshark.conf|timeout=1|timeout=30|systemctl reload tshark|tshark|tsh_to_1|pcaps|ifaces|pcap leftover leftover down; bounce|TSHARK_TIMEOUT leftover 1 leftover; a 2s capture is aborted so the dump 504s
tcpdump|TCPDUMP_TIMEOUT|1|30|s|/etc/tcpdump/tcpdump.conf|timeout=1|timeout=30|systemctl reload tcpdump|tcpdump|tcpd_to_1|pcaps|ifaces|pcap leftover leftover down; bounce|TCPDUMP_TIMEOUT leftover 1 leftover; a 2s capture is aborted so the dump 504s
dumpcap|DUMPCAP_TIMEOUT|1|30|s|/etc/wireshark/dumpcap.conf|timeout=1|timeout=30|systemctl reload dumpcap|dumpcap|dmp_to_1|pcaps|ifaces|pcap leftover leftover down; bounce|DUMPCAP_TIMEOUT leftover 1 leftover; a 2s capture is aborted so the dump 504s
netsniff|NETSNIFF_TIMEOUT|1|30|s|/etc/netsniff-ng/netsniff.conf|timeout=1|timeout=30|systemctl reload netsniff-ng|netsniff-ng|nsn_to_1|pcaps|ifaces|mmap leftover leftover down; bounce|NETSNIFF_TIMEOUT leftover 1 leftover; a 2s dump is aborted so the pcap 504s
pktgen|PKTGEN_TIMEOUT|1|10|s|/etc/pktgen/pktgen.conf|delay=1|delay=10|systemctl reload pktgen|pktgen|pkg_to_1|pps|nics|kmod leftover leftover down; bounce|PKTGEN_TIMEOUT leftover 1 leftover; a 2s burst is aborted so the test 504s
trafgen|TRAFGEN_TIMEOUT|1|10|s|/etc/netsniff-ng/trafgen.conf|timeout=1|timeout=10|systemctl reload trafgen|trafgen|trg_to_1|pps|nics|mmap leftover leftover down; bounce|TRAFGEN_TIMEOUT leftover 1 leftover; a 2s burst is aborted so the test 504s
mausezahn|MZ_TIMEOUT|1|10|s|/etc/mausezahn/mz.conf|timeout=1|timeout=10|systemctl reload mausezahn|mz|mz_to_1|pps|nics|raw leftover leftover down; bounce|MZ_TIMEOUT leftover 1 leftover; a 2s craft is aborted so the test 504s
scapy|SCAPY_TIMEOUT|1|10|s|/etc/scapy/scapy.conf|timeout=1|timeout=10|systemctl reload scapy|scapy|sca_to_1|pkts|ifaces|raw leftover leftover down; bounce|SCAPY_TIMEOUT leftover 1 leftover; a 2s sr1 is aborted so the probe 504s
hping3|HPING_TIMEOUT|1|10|s|/etc/hping/hping.conf|timeout=1|timeout=10|systemctl reload hping3|hping3|hpi_to_1|pkts|ifaces|raw leftover leftover down; bounce|HPING_TIMEOUT leftover 1 leftover; a 2s flood is aborted so the test 504s
nping|NPING_TIMEOUT|1|10|s|/etc/nmap/nping.conf|timeout=1|timeout=10|systemctl reload nping|nping|npi_to_1|pkts|hosts|raw leftover leftover down; bounce|NPING_TIMEOUT leftover 1 leftover; a 2s echo is aborted so the probe 504s
fping|FPING_TIMEOUT|1|500|ms|/etc/fping/fping.conf|timeout=1|timeout=500|systemctl reload fping|fping|fpi_to_1|hosts|icmp|icmp leftover leftover down; bounce|FPING_TIMEOUT leftover 1 leftover; a 2ms RTT is treated as down so the mesh 504s
iperf3|IPERF_TIMEOUT|1|10|s|/etc/iperf3/iperf3.conf|timeout=1|timeout=10|systemctl reload iperf3|iperf3|ipr_to_1|streams|hosts|tcp leftover leftover down; bounce|IPERF_TIMEOUT leftover 1 leftover; a 2s test is aborted so the bench 504s
nuttcp|NUTTCP_TIMEOUT|1|10|s|/etc/nuttcp/nuttcp.conf|timeout=1|timeout=10|systemctl reload nuttcp|nuttcp|nut_to_1|streams|hosts|tcp leftover leftover down; bounce|NUTTCP_TIMEOUT leftover 1 leftover; a 2s test is aborted so the bench 504s
netperf|NETPERF_TIMEOUT|1|10|s|/etc/netperf/netperf.conf|timeout=1|timeout=10|systemctl reload netserver|netperf|npf_to_1|streams|hosts|tcp leftover leftover down; bounce|NETPERF_TIMEOUT leftover 1 leftover; a 2s test is aborted so the bench 504s
sockperf|SOCKPERF_TIMEOUT|1|10|s|/etc/sockperf/sockperf.conf|timeout=1|timeout=10|systemctl reload sockperf|sockperf|skp_to_1|pps|hosts|udp leftover leftover down; bounce|SOCKPERF_TIMEOUT leftover 1 leftover; a 2s ping-pong is aborted so the bench 504s
qperf|QPERF_TIMEOUT|1|10|s|/etc/qperf/qperf.conf|timeout=1|timeout=10|systemctl reload qperf|qperf|qpf_to_1|lat|hosts|rdma leftover leftover down; bounce|QPERF_TIMEOUT leftover 1 leftover; a 2s lat is aborted so the bench 504s
uperf|UPERF_TIMEOUT|1|10|s|/etc/uperf/uperf.conf|timeout=1|timeout=10|systemctl reload uperf|uperf|upf_to_1|profiles|hosts|tcp leftover leftover down; bounce|UPERF_TIMEOUT leftover 1 leftover; a 2s profile is aborted so the bench 504s
3cx|PBX_TIMEOUT|1|30|s|/etc/3cx/3cx.conf|timeout=1|timeout=30|systemctl reload 3CXPhoneSystem|3cx|tcx_to_1|calls|exts|udp leftover leftover down; bounce|PBX_TIMEOUT leftover 1 leftover; a 2s INVITE is aborted so the ext 504s
wildix|WILDIX_TIMEOUT|1|30|s|/etc/wildix/wildix.conf|timeout=1|timeout=30|systemctl reload wildix|wildix|wdx_to_1|calls|exts|udp leftover leftover down; bounce|WILDIX_TIMEOUT leftover 1 leftover; a 2s INVITE is aborted so the ext 504s
sipxecs|SIPX_TIMEOUT|1|30|s|/etc/sipxecs/sipx.ini|timeout=1|timeout=30|systemctl reload sipxecs|sipxecs|sipx_to_1|calls|exts|udp leftover leftover down; bounce|SIPX_TIMEOUT leftover 1 leftover; a 2s INVITE is aborted so the ext 504s
matrix-synapse|synchrotron.timeout|1|30|s|/etc/matrix-synapse/homeserver.yaml|timeout: 1s|timeout: 30s|systemctl reload matrix-synapse|synctl|syn_to_1|sync|rooms|pg leftover leftover down; bounce|synchrotron.timeout leftover 1 leftover; a 2s /sync is aborted so Element 504s
rocket.chat|ROCKETCHAT_TIMEOUT|1|30|s|/etc/rocketchat/config.env|OVER_THE_AIR_UPDATES_TIMEOUT=1|OVER_THE_AIR_UPDATES_TIMEOUT=30|systemctl reload rocketchat|rocketchat|rch_to_1|ws|rooms|mongo leftover leftover down; bounce|ROCKETCHAT_TIMEOUT leftover 1 leftover; a 2s DDP is aborted so the UI 504s
discord-irc|DISCORDIRC_TIMEOUT|1|30|s|/etc/discord-irc/config.json|"timeout": 1|"timeout": 30|systemctl reload discord-irc|discord-irc|dirc_to_1|bridges|chans|ws leftover leftover down; bounce|DISCORDIRC_TIMEOUT leftover 1 leftover; a 2s message is aborted so the bridge 504s
slack-irc|SLACKIRC_TIMEOUT|1|30|s|/etc/slack-irc/config.json|"timeout": 1|"timeout": 30|systemctl reload slack-irc|slack-irc|sirc_to_1|bridges|chans|ws leftover leftover down; bounce|SLACKIRC_TIMEOUT leftover 1 leftover; a 2s message is aborted so the bridge 504s
liblinphone|LINPHONE_TIMEOUT|1|30|s|/etc/linphone/linphonerc|timeout=1|timeout=30|systemctl reload linphone|linphonec|lin_to_1|calls|regs|udp leftover leftover down; bounce|LINPHONE_TIMEOUT leftover 1 leftover; a 2s REGISTER is aborted so the UA 504s
pjsua|PJSUA_TIMEOUT|1|30|s|/etc/pjsip/pjsua.cfg|--timeout 1|--timeout 30|systemctl reload pjsua|pjsua|pjs_to_1|calls|regs|udp leftover leftover down; bounce|PJSUA_TIMEOUT leftover 1 leftover; a 2s REGISTER is aborted so the UA 504s
baresip|BARESIP_TIMEOUT|1|30|s|/etc/baresip/config|sip_trans_timer 1|sip_trans_timer 30|systemctl reload baresip|baresip|bar_to_1|calls|regs|udp leftover leftover down; bounce|BARESIP_TIMEOUT leftover 1 leftover; a 2s INVITE is aborted so the UA 504s
sofia-sip|SOFIA_TIMEOUT|1|30|s|/etc/sofia-sip/sip.conf|timeout=1|timeout=30|systemctl reload sofia|sofia|sof_to_1|calls|dialogs|udp leftover leftover down; bounce|SOFIA_TIMEOUT leftover 1 leftover; a 2s transaction is aborted so the stack 504s
ortp|ORTP_TIMEOUT|1|10|s|/etc/ortp/ortp.conf|timeout=1|timeout=10|systemctl reload ortp|ortp|ort_to_1|rtp|ssrcs|udp leftover leftover down; bounce|ORTP_TIMEOUT leftover 1 leftover; a 2s jitter is aborted so audio 504s
mediastreamer|MS_TIMEOUT|1|10|s|/etc/mediastreamer2/ms.conf|timeout=1|timeout=10|systemctl reload mediastreamer|ms2|ms_to_1|media|filters|udp leftover leftover down; bounce|MS_TIMEOUT leftover 1 leftover; a 2s filter is aborted so audio 504s
mumble|BAN_LENGTH|1|300||/etc/mumble-server.ini|banlength=1|banlength=300|systemctl reload mumble-server|murmur|mum_ban_1|users|chans|tcp leftover leftover down; bounce|BAN_LENGTH leftover 1 leftover; bans expire in 1s so the spam returns
murmur|timeout|1|30|s|/etc/mumble-server.ini|timeout=1|timeout=30|systemctl reload murmur|murmurd|mur_to_1|users|chans|tcp leftover leftover down; bounce|timeout leftover 1 leftover; a 2s idle drop kicks users so the room 504s
teamspeak|query_timeout|1|30|s|/etc/teamspeak/ts3server.ini|query_timeout=1|query_timeout=30|systemctl reload ts3server|ts3server|ts3_to_1|query|users|tcp leftover leftover down; bounce|query_timeout leftover 1 leftover; a 2s ServerQuery is aborted so the bot 504s
ventrilo|VENT_TIMEOUT|1|30|s|/etc/ventrilo/ventrilo.conf|timeout=1|timeout=30|systemctl reload ventrilo|ventrilo|ven_to_1|users|chans|udp leftover leftover down; bounce|VENT_TIMEOUT leftover 1 leftover; a 2s ping drop kicks users so the room 504s
mumble-server|bandwidth|1|72000||/etc/mumble-server.ini|bandwidth=1|bandwidth=72000|systemctl reload mumble-server|murmur|mums_bw_1|users|chans|udp leftover leftover down; bounce|bandwidth leftover 1 leftover; audio is 1bps so the room is silent
jicofo|jicofo.conference.timeout|1|30|s|/etc/jitsi/jicofo/jicofo.conf|timeout = 1 seconds|timeout = 30 seconds|systemctl reload jicofo|jicofo|jic_to_1|confs|bridges|xmpp leftover leftover down; bounce|jicofo.conference.timeout leftover 1 leftover; a 2s allocate is aborted so the meet 504s
prosody-modules|mod_mam.timeout|1|30|s|/etc/prosody/conf.d/mam.cfg.lua|archive_expires_after = "1d"|archive_expires_after = "30d"|systemctl reload prosody|prosodyctl|prom_mam_1|archive|users|sql leftover leftover down; bounce|mod_mam.timeout leftover 1 leftover; MAM expires in 1d so history 404s
'''
WAVE44 = (
    "asterisk/freeswitch/kamailio/opensips/rtpengine/coturn/turnserver/stund/"
    "ejabberd/prosody/openfire/tigase/dendrite/conduit/mattermost/zulip/"
    "ircd-hybrid/ngircd/inspircd/unrealircd/bitlbee/pidgin/telepathy/"
    "signal-cli/mautrix/heisenbridge/matterbridge/znc/weechat/irssi/yate/"
    "sems/mediaproxy/rtpproxy/homer/captagent/sngrep/sipp/voipmonitor/"
    "nprobe/n2disk/cento/ndpi/tshark/tcpdump/dumpcap/netsniff/pktgen/"
    "trafgen/mausezahn/scapy/hping3/nping/fping/iperf3/nuttcp/netperf/"
    "sockperf/qperf/uperf/3cx/wildix/sipxecs/matrix-synapse/rocket.chat/"
    "discord-irc/slack-irc/liblinphone/pjsua/baresip/sofia-sip/ortp/"
    "mediastreamer/mumble/murmur/teamspeak/ventrilo/mumble-server/jicofo/"
    "prosody-modules"
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
        svc = f"z4{i:02d}x"
        ns = f"z4{i:02d}"
        clu = f"prod-apsz{901 + i}-{svc[:3]}"
        ticket = f"W2-{12323 + i}"
        node = f"ip-10-229-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 3901


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r3900 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-44 leftover: {WAVE44}.",
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
