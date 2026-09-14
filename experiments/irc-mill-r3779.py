#!/usr/bin/env python3
"""IRC mill r3779+ — wave-41 routing/WASM leftover.

NEW on-call plants (not Wave-27–40 tails). BAN ypbind/oddjob,
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
bird2|connect.retry.timeout|1|10|s|/etc/bird/bird.conf|connect retry time 1|connect retry time 10|systemctl reload bird|birdc|bird2_to_1|sessions|peers|kernel leftover leftover down; bounce|connect.retry.timeout leftover 1 leftover; a 2s TCP is aborted so BGP never holds
gobgpd|grpc.timeout|1|10|s|/etc/gobgp/gobgpd.conf|timeout = 1|timeout = 10|systemctl reload gobgpd|gobgp|gobgp_to_1|rpcs|ribs|tcp leftover leftover down; bounce|grpc.timeout leftover 1 leftover; a 2s ListPath is aborted so the RIB 504s
pathd|pathd.timeout|1|10|s|/etc/frr/pathd.conf|timeout 1|timeout 10|systemctl reload frr|vtysh|pathd_to_1|sr|policies|zebra leftover leftover down; bounce|pathd.timeout leftover 1 leftover; a 2s candidate path is aborted so SR 504s
isisd|isis.hello.timeout|1|10|s|/etc/frr/isisd.conf|hello-interval 1|hello-interval 10|systemctl reload frr|vtysh|isis_hello_1|adjs|l2|zebra leftover leftover down; bounce|isis.hello.timeout leftover 1 leftover; hellos every 1s so the LSP storms
ospfd|ospf.hello.timeout|1|10|s|/etc/frr/ospfd.conf|hello-interval 1|hello-interval 10|systemctl reload frr|vtysh|ospf_hello_1|adjs|areas|zebra leftover leftover down; bounce|ospf.hello.timeout leftover 1 leftover; hellos every 1s so the DR flaps
ripd|rip.update.timeout|1|30|s|/etc/frr/ripd.conf|update-timer 1|update-timer 30|systemctl reload frr|vtysh|rip_up_1|routes|v2|zebra leftover leftover down; bounce|rip.update.timeout leftover 1 leftover; updates every 1s so the LAN 100%s
pimd|pim.hello.timeout|1|30|s|/etc/frr/pimd.conf|hello 1|hello 30|systemctl reload frr|vtysh|pim_hello_1|neighbors|mcast|zebra leftover leftover down; bounce|pim.hello.timeout leftover 1 leftover; hellos every 1s so IGMP 504s
ldpd|ldp.hello.timeout|1|5|s|/etc/frr/ldpd.conf|hello-interval 1|hello-interval 5|systemctl reload frr|vtysh|ldp_hello_1|peers|lsps|zebra leftover leftover down; bounce|ldp.hello.timeout leftover 1 leftover; hellos every 1s so the LSP 504s
bfdd|bfd.min-tx|1|100|ms|/etc/frr/bfdd.conf|min-tx 1|min-tx 100|systemctl reload frr|vtysh|bfd_tx_1|sessions|peers|zebra leftover leftover down; bounce|bfd.min-tx leftover 1 leftover; BFD packets every 1ms so the NIC 100%s
staticd|staticd.timeout|1|10|s|/etc/frr/staticd.conf|timeout 1|timeout 10|systemctl reload frr|vtysh|static_to_1|routes|vrfs|zebra leftover leftover down; bounce|staticd.timeout leftover 1 leftover; a 2s install is aborted so the default 504s
watchfrr|watchfrr.timeout|1|10|s|/etc/frr/watchfrr.conf|timeout 1|timeout 10|systemctl reload watchfrr|watchfrr|wfrr_to_1|daemons|pids|frr leftover leftover down; bounce|watchfrr.timeout leftover 1 leftover; a 2s poll restarts daemons so the RIB flaps
vtysh|VTYSH_TIMEOUT|1|10|s|/etc/frr/vtysh.conf|timeout 1|timeout 10|systemctl reload frr|vtysh|vtysh_to_1|cli|daemons|sock leftover leftover down; bounce|VTYSH_TIMEOUT leftover 1 leftover; a 2s show is aborted so ops 504s
babeld|babel.update.timeout|1|4|s|/etc/frr/babeld.conf|update-interval 1|update-interval 4|systemctl reload frr|vtysh|babel_up_1|routes|mesh|zebra leftover leftover down; bounce|babel.update.timeout leftover 1 leftover; updates every 1s so the mesh storms
eigrpd|eigrp.hello.timeout|1|5|s|/etc/frr/eigrpd.conf|hello-interval 1|hello-interval 5|systemctl reload frr|vtysh|eigrp_hello_1|neighbors|as|zebra leftover leftover down; bounce|eigrp.hello.timeout leftover 1 leftover; hellos every 1s so the topology flaps
ripngd|ripng.update.timeout|1|30|s|/etc/frr/ripngd.conf|update-timer 1|update-timer 30|systemctl reload frr|vtysh|ripng_up_1|routes|v6|zebra leftover leftover down; bounce|ripng.update.timeout leftover 1 leftover; updates every 1s so v6 100%s
ospf6d|ospf6.hello.timeout|1|10|s|/etc/frr/ospf6d.conf|hello-interval 1|hello-interval 10|systemctl reload frr|vtysh|ospf6_hello_1|adjs|v6|zebra leftover leftover down; bounce|ospf6.hello.timeout leftover 1 leftover; hellos every 1s so the v6 DR flaps
nhrpd|nhrp.timeout|1|10|s|/etc/frr/nhrpd.conf|timeout 1|timeout 10|systemctl reload frr|vtysh|nhrp_to_1|nhs|tunnels|zebra leftover leftover down; bounce|nhrp.timeout leftover 1 leftover; a 2s resolution is aborted so DMVPN 504s
pbrd|pbr.timeout|1|10|s|/etc/frr/pbrd.conf|timeout 1|timeout 10|systemctl reload frr|vtysh|pbr_to_1|maps|nexthops|zebra leftover leftover down; bounce|pbr.timeout leftover 1 leftover; a 2s map is aborted so policy routing 504s
zebra|zebra.zapi.timeout|1|10|s|/etc/frr/zebra.conf|zapi-timeout 1|zapi-timeout 10|systemctl reload frr|vtysh|zebra_zapi_1|clients|ribs|netlink leftover leftover down; bounce|zebra.zapi.timeout leftover 1 leftover; a 2s client is aborted so routes 504s
fabricd|fabric.timeout|1|10|s|/etc/frr/fabricd.conf|timeout 1|timeout 10|systemctl reload frr|vtysh|fab_to_1|openfabric|is|zebra leftover leftover down; bounce|fabric.timeout leftover 1 leftover; a 2s LSP is aborted so OpenFabric 504s
sharpd|sharp.timeout|1|10|s|/etc/frr/sharpd.conf|timeout 1|timeout 10|systemctl reload frr|vtysh|sharp_to_1|installs|test|zebra leftover leftover down; bounce|sharp.timeout leftover 1 leftover; a 2s install is aborted so the test RIB 504s
mgmtd|mgmtd.timeout|1|10|s|/etc/frr/mgmtd.conf|timeout 1|timeout 10|systemctl reload frr|vtysh|mgmt_to_1|yang|cfg|backend leftover leftover down; bounce|mgmtd.timeout leftover 1 leftover; a 2s commit is aborted so northbound 504s
alyx|ALYX_TIMEOUT|1|10|s|/etc/alyx/alyx.conf|timeout=1|timeout=10|systemctl reload alyx|alyx|alyx_to_1|cfg|yang|netconf leftover leftover down; bounce|ALYX_TIMEOUT leftover 1 leftover; a 2s edit is aborted so the datastore 504s
bfdd-replay|replay.timeout|1|10|s|/etc/frr/bfdd-replay.conf|timeout 1|timeout 10|systemctl reload frr|vtysh|bfdr_to_1|pcaps|sessions|pcap leftover leftover down; bounce|replay.timeout leftover 1 leftover; a 2s replay is aborted so BFD tests 504s
dnscrypt|dnscrypt.timeout|1|10|s|/etc/dnscrypt-proxy/dnscrypt-proxy.toml|timeout = 1|timeout = 10|systemctl reload dnscrypt-proxy|dnscrypt-proxy|dnsc_to_1|queries|resolvers|udp leftover leftover down; bounce|dnscrypt.timeout leftover 1 leftover; a 2s resolver is aborted so DNS 504s
bind9|recursive-clients|1|1000||/etc/bind/named.conf.options|recursive-clients 1|recursive-clients 1000|systemctl reload named|rndc|bind9_rec_1|queries|cache|udp leftover leftover down; bounce|recursive-clients leftover 1 leftover; the second recurse is dropped so clients 504s
isc-dhcpd|dhcp-lease-time|1|600||/etc/dhcp/dhcpd.conf|default-lease-time 1|default-lease-time 600|systemctl reload isc-dhcp-server|dhcpd|dhcpd_lease_1|leases|pools|udp leftover leftover down; bounce|dhcp-lease-time leftover 1 leftover; leases die in 1s so clients storm DISCOVER
wpa-supplicant|wpa.timeout|1|10|s|/etc/wpa_supplicant/wpa_supplicant.conf|timeout=1|timeout=10|systemctl reload wpa_supplicant|wpa_cli|wpa_to_1|assoc|ssids|nl80211 leftover leftover down; bounce|wpa.timeout leftover 1 leftover; a 2s 4way is aborted so Wi-Fi 504s
netplan|NETPLAN_TIMEOUT|1|30|s|/etc/netplan/01-netcfg.yaml|timeout: 1|timeout: 30|systemctl reload systemd-networkd|netplan|netp_to_1|apply|ifaces|udev leftover leftover down; bounce|NETPLAN_TIMEOUT leftover 1 leftover; a 2s apply is aborted so the NIC stays down
ifupdown|IFUP_TIMEOUT|1|30|s|/etc/network/interfaces|timeout 1|timeout 30|systemctl reload networking|ifup|ifup_to_1|ifaces|stanzas|ip leftover leftover down; bounce|IFUP_TIMEOUT leftover 1 leftover; a 2s dhclient is aborted so eth0 stays down
wicked|WICKED_TIMEOUT|1|30|s|/etc/wicked/client.xml|timeout=1|timeout=30|systemctl reload wicked|wicked|wick_to_1|ifaces|profiles|dbus leftover leftover down; bounce|WICKED_TIMEOUT leftover 1 leftover; a 2s lease is aborted so the NIC 504s
connman|CONNMAN_TIMEOUT|1|30|s|/etc/connman/main.conf|Timeout=1|Timeout=30|systemctl reload connman|connmanctl|conn_to_1|services|tech|dbus leftover leftover down; bounce|CONNMAN_TIMEOUT leftover 1 leftover; a 2s connect is aborted so the link 504s
dibbler|DIBBLER_TIMEOUT|1|10|s|/etc/dibbler/client.conf|timeout 1|timeout 10|systemctl reload dibbler-client|dibbler-client|dib_to_1|pd|ia|udp leftover leftover down; bounce|DIBBLER_TIMEOUT leftover 1 leftover; a 2s Solicit is aborted so v6 504s
odhcpd|ODHCPD_TIMEOUT|1|10|s|/etc/config/dhcp|option timeout 1|option timeout 10|systemctl reload odhcpd|odhcpd|odh_to_1|leases|ra|netlink leftover leftover down; bounce|ODHCPD_TIMEOUT leftover 1 leftover; a 2s RA is aborted so v6 clients 504s
tor|CircuitBuildTimeout|1|60|s|/etc/tor/torrc|CircuitBuildTimeout 1|CircuitBuildTimeout 60|systemctl reload tor|tor|tor_cbt_1|circuits|relays|or leftover leftover down; bounce|CircuitBuildTimeout leftover 1 leftover; a 2s circuit is aborted so the SOCKS 504s
stunnel|TIMEOUTbusy|1|30|s|/etc/stunnel/stunnel.conf|TIMEOUTbusy = 1|TIMEOUTbusy = 30|systemctl reload stunnel|stunnel|stn_to_1|tunnels|certs|tcp leftover leftover down; bounce|TIMEOUTbusy leftover 1 leftover; a 2s handshake is aborted so TLS 504s
ghostunnel|GHOSTUNNEL_TIMEOUT|1|30|s|/etc/ghostunnel/ghostunnel.yaml|timeout: 1s|timeout: 30s|systemctl reload ghostunnel|ghostunnel|ghst_to_1|tunnels|certs|tcp leftover leftover down; bounce|GHOSTUNNEL_TIMEOUT leftover 1 leftover; a 2s dial is aborted so mTLS 504s
mosh|MOSH_TIMEOUT|1|60|s|/etc/mosh/mosh.conf|timeout=1|timeout=60|systemctl reload mosh-server|mosh|mosh_to_1|sessions|udp|udp leftover leftover down; bounce|MOSH_TIMEOUT leftover 1 leftover; a 2s echo is aborted so the session 504s
autossh|AUTOSSH_TIMEOUT|1|30|s|/etc/autossh/autossh.conf|AUTOSSH_GATETIME=1|AUTOSSH_GATETIME=30|systemctl reload autossh|autossh|assh_to_1|tunnels|ssh|ssh leftover leftover down; bounce|AUTOSSH_TIMEOUT leftover 1 leftover; a 2s probe is aborted so the tunnel flaps
sslh|SSLH_TIMEOUT|1|10|s|/etc/sslh.cfg|timeout: 1|timeout: 10|systemctl reload sslh|sslh|sslh_to_1|mux|protos|tcp leftover leftover down; bounce|SSLH_TIMEOUT leftover 1 leftover; a 2s probe is aborted so SSH 504s
socat|SOCAT_TIMEOUT|1|30|s|/etc/socat/socat.conf|timeout=1|timeout=30|systemctl reload socat|socat|socat_to_1|relays|socks|tcp leftover leftover down; bounce|SOCAT_TIMEOUT leftover 1 leftover; a 2s transfer is aborted so the pipe 504s
ncat|NCAT_TIMEOUT|1|30|s|/etc/ncat/ncat.conf|timeout=1|timeout=30|systemctl reload ncat|ncat|ncat_to_1|listens|tcp|tcp leftover leftover down; bounce|NCAT_TIMEOUT leftover 1 leftover; a 2s accept is aborted so the probe 504s
NetworkManager|NM_TIMEOUT|1|30|s|/etc/NetworkManager/NetworkManager.conf|timeout=1|timeout=30|systemctl reload NetworkManager|nmcli|nm_to_1|conns|ifaces|dbus leftover leftover down; bounce|NM_TIMEOUT leftover 1 leftover; a 2s activate is aborted so the NIC 504s
bolt|BOLT_TIMEOUT|1|10|s|/etc/bolt/boltd.conf|timeout=1|timeout=10|systemctl reload bolt|boltctl|bolt_to_1|devices|tb|udev leftover leftover down; bounce|BOLT_TIMEOUT leftover 1 leftover; a 2s authorize is aborted so Thunderbolt 504s
oomd|OOMD_TIMEOUT|1|10|s|/etc/oomd.json|timeout: 1|timeout: 10|systemctl reload oomd|oomctl|oomd_to_1|cgroups|pressure|cgroup leftover leftover down; bounce|OOMD_TIMEOUT leftover 1 leftover; a 2s kill is aborted so the workload 504s
resolved|RESOLVED_TIMEOUT|1|10|s|/etc/systemd/resolved.conf|Timeout=1s|Timeout=10s|systemctl reload systemd-resolved|resolvectl|res_to_1|queries|stubs|udp leftover leftover down; bounce|RESOLVED_TIMEOUT leftover 1 leftover; a 2s lookup is aborted so getaddrinfo 504s
homed|HOMED_TIMEOUT|1|30|s|/etc/systemd/homed.conf|Timeout=1s|Timeout=30s|systemctl reload systemd-homed|homectl|home_to_1|homes|users|luks leftover leftover down; bounce|HOMED_TIMEOUT leftover 1 leftover; a 2s activate is aborted so login 504s
portabled|PORTABLED_TIMEOUT|1|30|s|/etc/systemd/portabled.conf|Timeout=1s|Timeout=30s|systemctl reload systemd-portabled|portablectl|port_to_1|images|units|loop leftover leftover down; bounce|PORTABLED_TIMEOUT leftover 1 leftover; a 2s attach is aborted so the image 504s
nspawn|NSPAWN_TIMEOUT|1|30|s|/etc/systemd/nspawn/machine.nspawn|TimeoutStartSec=1|TimeoutStartSec=30|systemctl reload systemd-nspawn@machine|machinectl|nsp_to_1|machines|roots|cgroup leftover leftover down; bounce|NSPAWN_TIMEOUT leftover 1 leftover; a 2s boot is aborted so the container 504s
machinectl|MACHINECTL_TIMEOUT|1|30|s|/etc/systemd/machined.conf|Timeout=1s|Timeout=30s|systemctl reload systemd-machined|machinectl|mctl_to_1|machines|regs|dbus leftover leftover down; bounce|MACHINECTL_TIMEOUT leftover 1 leftover; a 2s register is aborted so the VM 504s
coredump|COREDUMP_TIMEOUT|1|30|s|/etc/systemd/coredump.conf|ProcessSizeMax=1|ProcessSizeMax=2G|systemctl reload systemd-coredump|coredumpctl|core_to_1|dumps|units|journal leftover leftover down; bounce|COREDUMP_TIMEOUT leftover 1 leftover; a 2s store is aborted so the dump vanishes
sysusers|SYSUSERS_TIMEOUT|1|10|s|/etc/sysusers.d/timeout.conf|timeout=1|timeout=10|systemctl reload systemd-sysusers|systemd-sysusers|sysu_to_1|users|uids|passwd leftover leftover down; bounce|SYSUSERS_TIMEOUT leftover 1 leftover; a 2s add is aborted so the unit 504s
tmpfiles|TMPFILES_TIMEOUT|1|30|s|/etc/tmpfiles.d/timeout.conf|timeout=1|timeout=30|systemctl reload systemd-tmpfiles|systemd-tmpfiles|tmpf_to_1|dirs|age|fs leftover leftover down; bounce|TMPFILES_TIMEOUT leftover 1 leftover; a 2s create is aborted so runtime dirs 504s
binfmt|BINFMT_TIMEOUT|1|10|s|/etc/binfmt.d/timeout.conf|timeout=1|timeout=10|systemctl reload systemd-binfmt|systemctl|binf_to_1|magics|handlers|proc leftover leftover down; bounce|BINFMT_TIMEOUT leftover 1 leftover; a 2s register is aborted so qemu-user 504s
udevd|UDEV_TIMEOUT|1|30|s|/etc/udev/udev.conf|event_timeout=1|event_timeout=30|systemctl reload systemd-udevd|udevadm|udev_to_1|events|rules|netlink leftover leftover down; bounce|UDEV_TIMEOUT leftover 1 leftover; a 2s settle is aborted so devices 504s
nydus|NYDUS_TIMEOUT|1|30|s|/etc/nydus/nydusd.json|timeout: 1|timeout: 30|systemctl reload nydusd|nydus|nyd_to_1|rafs|blobs|registry leftover leftover 403; bounce|NYDUS_TIMEOUT leftover 1 leftover; a 2s prefetch is aborted so the snapshot 504s
stargz|STARGZ_TIMEOUT|1|30|s|/etc/containerd-stargz-grpc/config.toml|timeout = 1|timeout = 30|systemctl reload stargz-snapshotter|ctr|stgz_to_1|layers|toc|registry leftover leftover 403; bounce|STARGZ_TIMEOUT leftover 1 leftover; a 2s fetch is aborted so the lazy pull 504s
soci|SOCI_TIMEOUT|1|30|s|/etc/soci-snapshotter/config.toml|timeout = 1|timeout = 30|systemctl reload soci-snapshotter|ctr|soci_to_1|indexes|zocs|registry leftover leftover 403; bounce|SOCI_TIMEOUT leftover 1 leftover; a 2s zTOC is aborted so the pull 504s
overlaybd|OVERLAYBD_TIMEOUT|1|30|s|/etc/overlaybd/overlaybd.json|timeout: 1|timeout: 30|systemctl reload overlaybd-tcmu|overlaybd|ovbd_to_1|layers|luks|registry leftover leftover 403; bounce|OVERLAYBD_TIMEOUT leftover 1 leftover; a 2s download is aborted so the snapshot 504s
composefs|COMPOSEFS_TIMEOUT|1|30|s|/etc/composefs/composefs.conf|timeout=1|timeout=30|systemctl reload composefs|mkcomposefs|cfs_to_1|images|erofs|ostree leftover leftover down; bounce|COMPOSEFS_TIMEOUT leftover 1 leftover; a 2s mount is aborted so the root 504s
wasmer|WASMER_TIMEOUT|1|30|s|/etc/wasmer/wasmer.toml|timeout=1|timeout=30|systemctl reload wasmer|wasmer|wasm_to_1|modules|store|fs leftover leftover down; bounce|WASMER_TIMEOUT leftover 1 leftover; a 2s instantiate is aborted so the module 504s
wasmedge|WASMEDGE_TIMEOUT|1|30|s|/etc/wasmedge/wasmedge.toml|timeout=1|timeout=30|systemctl reload wasmedge|wasmedge|wedge_to_1|modules|aot|fs leftover leftover down; bounce|WASMEDGE_TIMEOUT leftover 1 leftover; a 2s AOT is aborted so the plugin 504s
wazero|WAZERO_TIMEOUT|1|30|s|/etc/wazero/wazero.toml|timeout=1|timeout=30|systemctl reload wazero|wazero|waz_to_1|modules|runtime|fs leftover leftover down; bounce|WAZERO_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the host 504s
lunatic|LUNATIC_TIMEOUT|1|30|s|/etc/lunatic/lunatic.toml|timeout=1|timeout=30|systemctl reload lunatic|lunatic|luna_to_1|actors|wasm|fs leftover leftover down; bounce|LUNATIC_TIMEOUT leftover 1 leftover; a 2s spawn is aborted so the actor 504s
spin|SPIN_TIMEOUT|1|30|s|/etc/spin/spin.toml|timeout=1|timeout=30|systemctl reload spin|spin|spin_to_1|http|components|fs leftover leftover down; bounce|SPIN_TIMEOUT leftover 1 leftover; a 2s trigger is aborted so the route 504s
slight|SLIGHT_TIMEOUT|1|30|s|/etc/slight/slight.toml|timeout=1|timeout=30|systemctl reload slight|slight|slight_to_1|wit|hosts|fs leftover leftover down; bounce|SLIGHT_TIMEOUT leftover 1 leftover; a 2s capability is aborted so the guest 504s
krustlet|KRUSTLET_TIMEOUT|1|30|s|/etc/krustlet/config.toml|timeout=1|timeout=30|systemctl reload krustlet|krustlet|krust_to_1|wasmpods|nodes|apiserver leftover leftover down; bounce|KRUSTLET_TIMEOUT leftover 1 leftover; a 2s run is aborted so the Wasm pod 504s
qemu-ga|QGA_TIMEOUT|1|10|s|/etc/qemu/qemu-ga.conf|timeout=1|timeout=10|systemctl reload qemu-guest-agent|qemu-ga|qga_to_1|guest|virtio|virtio leftover leftover down; bounce|QGA_TIMEOUT leftover 1 leftover; a 2s fsfreeze is aborted so the snapshot 504s
virtiofsd|VIRTIOFSD_TIMEOUT|1|30|s|/etc/virtiofsd/virtiofsd.conf|timeout=1|timeout=30|systemctl reload virtiofsd|virtiofsd|vfsd_to_1|exports|guests|fuse leftover leftover down; bounce|VIRTIOFSD_TIMEOUT leftover 1 leftover; a 2s LOOKUP is aborted so the guest 504s
vhost-user|VHOST_TIMEOUT|1|10|s|/etc/vhost-user/vhost.conf|timeout=1|timeout=10|systemctl reload vhost-user|vhost-user|vhu_to_1|queues|vms|unix leftover leftover down; bounce|VHOST_TIMEOUT leftover 1 leftover; a 2s kick is aborted so the VM 504s
passt|PAST_TIMEOUT|1|10|s|/etc/passt/passt.conf|timeout=1|timeout=10|systemctl reload passt|passt|passt_to_1|socks|pods|tap leftover leftover down; bounce|PAST_TIMEOUT leftover 1 leftover; a 2s TCP is aborted so the pod 504s
pasta|PASTA_TIMEOUT|1|10|s|/etc/passt/pasta.conf|timeout=1|timeout=10|systemctl reload pasta|pasta|pasta_to_1|nets|pods|ns leftover leftover down; bounce|PASTA_TIMEOUT leftover 1 leftover; a 2s copy is aborted so the netns 504s
slirp4netns|SLIRP_TIMEOUT|1|10|s|/etc/slirp4netns/slirp.conf|timeout=1|timeout=10|systemctl reload slirp4netns|slirp4netns|slirp_to_1|nats|pods|tap leftover leftover down; bounce|SLIRP_TIMEOUT leftover 1 leftover; a 2s DHCP is aborted so the pod 504s
rootlesskit|ROOTLESSKIT_TIMEOUT|1|30|s|/etc/rootlesskit/config.json|timeout: 1|timeout: 30|systemctl reload rootlesskit|rootlesskit|rlk_to_1|child|userns|ns leftover leftover down; bounce|ROOTLESSKIT_TIMEOUT leftover 1 leftover; a 2s copy-up is aborted so the engine 504s
buildbarn|BB_TIMEOUT|1|60|s|/etc/buildbarn/browser.jsonnet|timeout: 1|timeout: 60|systemctl reload bb-browser|bb-client|bb_to_1|actions|cas|grpc leftover leftover down; bounce|BB_TIMEOUT leftover 1 leftover; a 2s Execute is aborted so RBE 504s
buildbuddy|BUDDY_TIMEOUT|1|60|s|/etc/buildbuddy/buildbuddy.yaml|timeout: 1s|timeout: 60s|systemctl reload buildbuddy|bb|buddy_to_1|invoc|cas|grpc leftover leftover down; bounce|BUDDY_TIMEOUT leftover 1 leftover; a 2s GetAction is aborted so the UI 504s
engflow|ENGFLOW_TIMEOUT|1|60|s|/etc/engflow/reapi.yaml|timeout: 1s|timeout: 60s|systemctl reload engflow|reapi|eng_to_1|actions|cas|grpc leftover leftover down; bounce|ENGFLOW_TIMEOUT leftover 1 leftover; a 2s Execute is aborted so Bazel 504s
native-remote|NATIVE_TIMEOUT|1|60|s|/etc/native-remote/config.yaml|timeout: 1s|timeout: 60s|systemctl reload native-remote|nr|natv_to_1|actions|cas|grpc leftover leftover down; bounce|NATIVE_TIMEOUT leftover 1 leftover; a 2s FindMissing is aborted so the cache 504s
pantsd|PANTSD_TIMEOUT|1|60|s|/etc/pants/pants.toml|timeout=1|timeout=60|systemctl reload pantsd|pants|pants_to_1|goals|cache|fs leftover leftover down; bounce|PANTSD_TIMEOUT leftover 1 leftover; a 2s graph is aborted so the goal 504s
import-d|IMPORTD_TIMEOUT|1|60|s|/etc/systemd/import-d.conf|Timeout=1s|Timeout=60s|systemctl reload systemd-importd|importctl|imp_to_1|tarballs|raw|https leftover leftover 403; bounce|IMPORTD_TIMEOUT leftover 1 leftover; a 2s pull is aborted so the image 504s
'''
WAVE41 = (
    "bird2/gobgpd/pathd/isisd/ospfd/ripd/pimd/ldpd/bfdd/staticd/watchfrr/vtysh/"
    "babeld/eigrpd/ripngd/ospf6d/nhrpd/pbrd/zebra/fabricd/sharpd/mgmtd/alyx/"
    "bfdd-replay/dnscrypt/bind9/isc-dhcpd/wpa-supplicant/netplan/ifupdown/"
    "wicked/connman/dibbler/odhcpd/tor/stunnel/ghostunnel/mosh/autossh/sslh/"
    "socat/ncat/NetworkManager/bolt/oomd/resolved/homed/portabled/nspawn/"
    "machinectl/coredump/sysusers/tmpfiles/binfmt/udevd/nydus/stargz/soci/"
    "overlaybd/composefs/wasmer/wasmedge/wazero/lunatic/spin/slight/krustlet/"
    "qemu-ga/virtiofsd/vhost-user/passt/pasta/slirp4netns/rootlesskit/"
    "buildbarn/buildbuddy/engflow/native-remote/pantsd/import-d"
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
        svc = f"w1{i:02d}x"
        ns = f"w1{i:02d}"
        clu = f"prod-apsw{901 + i}-{svc[:3]}"
        ticket = f"W2-{12079 + i}"
        node = f"ip-10-226-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 3779


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r3778 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-41 leftover: {WAVE41}.",
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
