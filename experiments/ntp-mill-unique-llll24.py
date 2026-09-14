#!/usr/bin/env python3
"""NTP unique leftover leftover leftover leftover mill wave 24: NEW dest plants. BAN dnsmasq leftover clones."""
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
    s_from(0, "iptables-save-leftover-as-dest", "ipts", "iptables save leftover", "iptables.save", "iptables save leftover", "iptables leftover && ls iptables.save", "not iptables-save leftover; iptables save leftover is not dest", "treat leftover iptables save as dest then CLI parquet.", "iptables leftover; # iptables.save claimed dest", "iptables leftover|iptables.save"),
    s_from(1, "nftables-conf-leftover-as-dest", "nftc", "nftables conf leftover", "nftables.conf", "nftables conf leftover", "nftables leftover && ls nftables.conf", "not nftables-conf leftover; nftables conf leftover is not dest", "treat leftover nftables conf as dest then CLI parquet.", "nftables leftover; # nftables.conf claimed dest", "nftables leftover|nftables.conf"),
    s_from(2, "coredns-db-leftover-as-dest", "cddb", "coredns db leftover", "coredns.db", "coredns db leftover", "coredns leftover && ls coredns.db", "not coredns-db leftover; coredns db leftover is not dest", "treat leftover coredns db as dest then CLI parquet.", "coredns leftover; # coredns.db claimed dest", "coredns leftover|coredns.db"),
    s_from(3, "unbound-cache-leftover-as-dest", "ubch", "unbound cache leftover", "unbound.cache", "unbound cache leftover", "unbound leftover && ls unbound.cache", "not unbound-cache leftover; unbound cache leftover is not dest", "treat leftover unbound cache as dest then CLI parquet.", "unbound leftover; # unbound.cache claimed dest", "unbound leftover|unbound.cache"),
    s_from(4, "bind-journal-leftover-as-dest", "bdjn", "bind journal leftover", "named.jnl", "bind journal leftover", "bind leftover && ls named.jnl", "not bind-journal leftover; bind journal leftover is not dest", "treat leftover bind journal as dest then CLI parquet.", "bind leftover; # named.jnl claimed dest", "bind leftover|named.jnl"),
    s_from(5, "resolved-lease-leftover-as-dest", "rsls", "resolved lease leftover", "resolved.lease", "resolved lease leftover", "resolved leftover && ls resolved.lease", "not resolved-lease leftover; resolved lease leftover is not dest", "treat leftover resolved lease as dest then CLI parquet.", "resolved leftover; # resolved.lease claimed dest", "resolved leftover|resolved.lease"),
    s_from(6, "wireguard-conf-leftover-as-dest", "wgcf", "wireguard conf leftover", "wg0.conf.bak", "wireguard conf leftover", "wireguard leftover && ls wg0.conf.bak", "not wireguard-conf leftover; wireguard conf leftover is not dest", "treat leftover wireguard conf as dest then CLI parquet.", "wireguard leftover; # wg0.conf.bak claimed dest", "wireguard leftover|wg0.conf.bak"),
    s_from(7, "openvpn-status-leftover-as-dest", "ovst", "openvpn status leftover", "openvpn-status.log", "openvpn status leftover", "openvpn leftover && ls openvpn-status.log", "not openvpn-status leftover; openvpn status leftover is not dest", "treat leftover openvpn status as dest then CLI parquet.", "openvpn leftover; # openvpn-status.log claimed dest", "openvpn leftover|openvpn-status.log"),
    s_from(8, "strongswan-conf-leftover-as-dest", "sscf", "strongswan conf leftover", "ipsec.conf.bak", "strongswan conf leftover", "strongswan leftover && ls ipsec.conf.bak", "not strongswan-conf leftover; strongswan conf leftover is not dest", "treat leftover strongswan conf as dest then CLI parquet.", "strongswan leftover; # ipsec.conf.bak claimed dest", "strongswan leftover|ipsec.conf.bak"),
    s_from(9, "tailscale-state-leftover-as-dest", "tsst", "tailscale state leftover", "tailscaled.state", "tailscale state leftover", "tailscale leftover && ls tailscaled.state", "not tailscale-state leftover; tailscale state leftover is not dest", "treat leftover tailscale state as dest then CLI parquet.", "tailscale leftover; # tailscaled.state claimed dest", "tailscale leftover|tailscaled.state"),
    s_from(10, "zerotier-id-leftover-as-dest", "ztid", "zerotier id leftover", "identity.secret", "zerotier id leftover", "zerotier leftover && ls identity.secret", "not zerotier-id leftover; zerotier id leftover is not dest", "treat leftover zerotier id as dest then CLI parquet.", "zerotier leftover; # identity.secret claimed dest", "zerotier leftover|identity.secret"),
    s_from(11, "nebula-conf-leftover-as-dest", "nbcf2", "nebula conf leftover", "nebula.yml.bak", "nebula conf leftover", "nebula leftover && ls nebula.yml.bak", "not nebula-conf leftover; nebula conf leftover is not dest", "treat leftover nebula conf as dest then CLI parquet.", "nebula leftover; # nebula.yml.bak claimed dest", "nebula leftover|nebula.yml.bak"),
    s_from(12, "caddy-data-leftover-as-dest", "cydt", "caddy data leftover", "caddy/data", "caddy data leftover", "caddy leftover && ls caddy/data", "not caddy-data leftover; caddy data leftover is not dest", "treat leftover caddy data as dest then CLI parquet.", "caddy leftover; # caddy/data claimed dest", "caddy leftover|caddy/data"),
    s_from(13, "nginx-cache-leftover-as-dest", "ngch", "nginx cache leftover", "nginx/cache", "nginx cache leftover", "nginx leftover && ls nginx/cache", "not nginx-cache leftover; nginx cache leftover is not dest", "treat leftover nginx cache as dest then CLI parquet.", "nginx leftover; # nginx/cache claimed dest", "nginx leftover|nginx/cache"),
    s_from(14, "haproxy-map-leftover-as-dest", "hpm", "haproxy map leftover", "haproxy.map", "haproxy map leftover", "haproxy leftover && ls haproxy.map", "not haproxy-map leftover; haproxy map leftover is not dest", "treat leftover haproxy map as dest then CLI parquet.", "haproxy leftover; # haproxy.map claimed dest", "haproxy leftover|haproxy.map"),
    s_from(15, "envoy-config-leftover-as-dest", "encf", "envoy config leftover", "envoy.yaml.bak", "envoy config leftover", "envoy leftover && ls envoy.yaml.bak", "not envoy-config leftover; envoy config leftover is not dest", "treat leftover envoy config as dest then CLI parquet.", "envoy leftover; # envoy.yaml.bak claimed dest", "envoy leftover|envoy.yaml.bak"),
    s_from(16, "traefik-acme-leftover-as-dest", "tfac", "traefik acme leftover", "acme.json", "traefik acme leftover", "traefik leftover && ls acme.json", "not traefik-acme leftover; traefik acme leftover is not dest", "treat leftover traefik acme as dest then CLI parquet.", "traefik leftover; # acme.json claimed dest", "traefik leftover|acme.json"),
    s_from(17, "varnish-vcl-leftover-as-dest", "vavc", "varnish vcl leftover", "default.vcl.bak", "varnish vcl leftover", "varnish leftover && ls default.vcl.bak", "not varnish-vcl leftover; varnish vcl leftover is not dest", "treat leftover varnish vcl as dest then CLI parquet.", "varnish leftover; # default.vcl.bak claimed dest", "varnish leftover|default.vcl.bak"),
    s_from(18, "squid-cache-leftover-as-dest", "sqch", "squid cache leftover", "squid/cache", "squid cache leftover", "squid leftover && ls squid/cache", "not squid-cache leftover; squid cache leftover is not dest", "treat leftover squid cache as dest then CLI parquet.", "squid leftover; # squid/cache claimed dest", "squid leftover|squid/cache"),
    s_from(19, "mitmproxy-flow-leftover-as-dest", "mtfl", "mitmproxy flow leftover", "mitmproxy.flow", "mitmproxy flow leftover", "mitmproxy leftover && ls mitmproxy.flow", "not mitmproxy-flow leftover; mitmproxy flow leftover is not dest", "treat leftover mitmproxy flow as dest then CLI parquet.", "mitmproxy leftover; # mitmproxy.flow claimed dest", "mitmproxy leftover|mitmproxy.flow"),
    s_from(20, "wireshark-pcap-leftover-as-dest", "wspc", "wireshark pcap leftover", "capture.pcap", "wireshark pcap leftover", "wireshark leftover && ls capture.pcap", "not wireshark-pcap leftover; wireshark pcap leftover is not dest", "treat leftover wireshark pcap as dest then CLI parquet.", "wireshark leftover; # capture.pcap claimed dest", "wireshark leftover|capture.pcap"),
    s_from(21, "tcpdump-pcap-leftover-as-dest", "tdpc", "tcpdump pcap leftover", "tcpdump.pcap", "tcpdump pcap leftover", "tcpdump leftover && ls tcpdump.pcap", "not tcpdump-pcap leftover; tcpdump pcap leftover is not dest", "treat leftover tcpdump pcap as dest then CLI parquet.", "tcpdump leftover; # tcpdump.pcap claimed dest", "tcpdump leftover|tcpdump.pcap"),
    s_from(22, "tshark-json-leftover-as-dest", "tsjs", "tshark json leftover", "tshark.json", "tshark json leftover", "tshark leftover && ls tshark.json", "not tshark-json leftover; tshark json leftover is not dest", "treat leftover tshark json as dest then CLI parquet.", "tshark leftover; # tshark.json claimed dest", "tshark leftover|tshark.json"),
    s_from(23, "socat-log-leftover-as-dest", "sotl", "socat log leftover", "socat.log", "socat log leftover", "socat leftover && ls socat.log", "not socat-log leftover; socat log leftover is not dest", "treat leftover socat log as dest then CLI parquet.", "socat leftover; # socat.log claimed dest", "socat leftover|socat.log"),
    s_from(24, "ncat-log-leftover-as-dest", "nclg2", "ncat log leftover", "ncat.log", "ncat log leftover", "ncat leftover && ls ncat.log", "not ncat-log leftover; ncat log leftover is not dest", "treat leftover ncat log as dest then CLI parquet.", "ncat leftover; # ncat.log claimed dest", "ncat leftover|ncat.log"),
    s_from(25, "iperf-json-leftover-as-dest", "ipjs", "iperf json leftover", "iperf.json", "iperf json leftover", "iperf leftover && ls iperf.json", "not iperf-json leftover; iperf json leftover is not dest", "treat leftover iperf json as dest then CLI parquet.", "iperf leftover; # iperf.json claimed dest", "iperf leftover|iperf.json"),
    s_from(26, "mtr-json-leftover-as-dest", "mtjs", "mtr json leftover", "mtr.json", "mtr json leftover", "mtr leftover && ls mtr.json", "not mtr-json leftover; mtr json leftover is not dest", "treat leftover mtr json as dest then CLI parquet.", "mtr leftover; # mtr.json claimed dest", "mtr leftover|mtr.json"),
    s_from(27, "traceroute-log-leftover-as-dest", "trlg2", "traceroute log leftover", "traceroute.log", "traceroute log leftover", "traceroute leftover && ls traceroute.log", "not traceroute-log leftover; traceroute log leftover is not dest", "treat leftover traceroute log as dest then CLI parquet.", "traceroute leftover; # traceroute.log claimed dest", "traceroute leftover|traceroute.log"),
    s_from(28, "keepalived-conf-leftover-as-dest", "kvcf", "keepalived conf leftover", "keepalived.conf.bak", "keepalived conf leftover", "keepalived leftover && ls keepalived.conf.bak", "not keepalived-conf leftover; keepalived conf leftover is not dest", "treat leftover keepalived conf as dest then CLI parquet.", "keepalived leftover; # keepalived.conf.bak claimed dest", "keepalived leftover|keepalived.conf.bak"),
    s_from(29, "bird-conf-leftover-as-dest", "brcf", "bird conf leftover", "bird.conf.bak", "bird conf leftover", "bird leftover && ls bird.conf.bak", "not bird-conf leftover; bird conf leftover is not dest", "treat leftover bird conf as dest then CLI parquet.", "bird leftover; # bird.conf.bak claimed dest", "bird leftover|bird.conf.bak"),
    s_from(30, "frr-conf-leftover-as-dest", "frcf", "frr conf leftover", "frr.conf.bak", "frr conf leftover", "frr leftover && ls frr.conf.bak", "not frr-conf leftover; frr conf leftover is not dest", "treat leftover frr conf as dest then CLI parquet.", "frr leftover; # frr.conf.bak claimed dest", "frr leftover|frr.conf.bak"),
    s_from(31, "strongswan-log-leftover-as-dest", "sslg", "strongswan log leftover", "charon.log", "strongswan log leftover", "strongswan leftover && ls charon.log", "not strongswan-log leftover; strongswan log leftover is not dest", "treat leftover strongswan log as dest then CLI parquet.", "strongswan leftover; # charon.log claimed dest", "strongswan leftover|charon.log"),
]

LEFTOVER = [
    l_from(0, "iptables-log-leftover-handoff", "iptl", "iptables.log", "iptables log leftover", "iptables log leftover", "not iptables save leftover; leftover iptables log as dest", "ship leftover iptables log as dest.", "iptables log leftover; # iptables.log on disk", "iptables leftover|iptables.log"),
    l_from(1, "nftables-log-leftover-handoff", "nftl", "nftables.log", "nftables log leftover", "nftables log leftover", "not nftables conf leftover; leftover nftables log as dest", "ship leftover nftables log as dest.", "nftables log leftover; # nftables.log on disk", "nftables leftover|nftables.log"),
    l_from(2, "coredns-log-leftover-handoff", "cdlg2", "coredns.log", "coredns log leftover", "coredns log leftover", "not coredns db leftover; leftover coredns log as dest", "ship leftover coredns log as dest.", "coredns log leftover; # coredns.log on disk", "coredns leftover|coredns.log"),
    l_from(3, "unbound-log-leftover-handoff", "ublg", "unbound.log", "unbound log leftover", "unbound log leftover", "not unbound cache leftover; leftover unbound log as dest", "ship leftover unbound log as dest.", "unbound log leftover; # unbound.log on disk", "unbound leftover|unbound.log"),
    l_from(4, "bind-log-leftover-handoff", "bdlg2", "named.log", "bind log leftover", "bind log leftover", "not bind journal leftover; leftover bind log as dest", "ship leftover bind log as dest.", "bind log leftover; # named.log on disk", "bind leftover|named.log"),
    l_from(5, "resolved-log-leftover-handoff", "rslg", "resolved.log", "resolved log leftover", "resolved log leftover", "not resolved lease leftover; leftover resolved log as dest", "ship leftover resolved log as dest.", "resolved log leftover; # resolved.log on disk", "resolved leftover|resolved.log"),
    l_from(6, "wireguard-log-leftover-handoff", "wglg", "wg-quick.log", "wireguard log leftover", "wireguard log leftover", "not wireguard conf leftover; leftover wireguard log as dest", "ship leftover wireguard log as dest.", "wireguard log leftover; # wg-quick.log on disk", "wireguard leftover|wg-quick.log"),
    l_from(7, "openvpn-log-leftover-handoff", "ovlg2", "openvpn.log", "openvpn log leftover", "openvpn log leftover", "not openvpn status leftover; leftover openvpn log as dest", "ship leftover openvpn log as dest.", "openvpn log leftover; # openvpn.log on disk", "openvpn leftover|openvpn.log"),
    l_from(8, "strongswan-secrets-leftover-handoff", "sssc", "ipsec.secrets.bak", "strongswan secrets leftover", "strongswan secrets leftover", "not strongswan conf leftover; leftover strongswan secrets as dest", "ship leftover strongswan secrets as dest.", "strongswan secrets leftover; # ipsec.secrets.bak on disk", "strongswan leftover|ipsec.secrets.bak"),
    l_from(9, "tailscale-log-leftover-handoff", "tslg", "tailscaled.log", "tailscale log leftover", "tailscale log leftover", "not tailscale state leftover; leftover tailscale log as dest", "ship leftover tailscale log as dest.", "tailscale log leftover; # tailscaled.log on disk", "tailscale leftover|tailscaled.log"),
    l_from(10, "zerotier-log-leftover-handoff", "ztlg", "zerotier.log", "zerotier log leftover", "zerotier log leftover", "not zerotier id leftover; leftover zerotier log as dest", "ship leftover zerotier log as dest.", "zerotier log leftover; # zerotier.log on disk", "zerotier leftover|zerotier.log"),
    l_from(11, "nebula-log-leftover-handoff", "nblg", "nebula.log", "nebula log leftover", "nebula log leftover", "not nebula conf leftover; leftover nebula log as dest", "ship leftover nebula log as dest.", "nebula log leftover; # nebula.log on disk", "nebula leftover|nebula.log"),
    l_from(12, "caddy-log-leftover-handoff", "cylg", "caddy.log", "caddy log leftover", "caddy log leftover", "not caddy data leftover; leftover caddy log as dest", "ship leftover caddy log as dest.", "caddy log leftover; # caddy.log on disk", "caddy leftover|caddy.log"),
    l_from(13, "nginx-log-leftover-handoff", "nglg", "nginx/access.log", "nginx log leftover", "nginx log leftover", "not nginx cache leftover; leftover nginx log as dest", "ship leftover nginx log as dest.", "nginx log leftover; # nginx/access.log on disk", "nginx leftover|nginx/access.log"),
    l_from(14, "haproxy-log-leftover-handoff", "hplg", "haproxy.log", "haproxy log leftover", "haproxy log leftover", "not haproxy map leftover; leftover haproxy log as dest", "ship leftover haproxy log as dest.", "haproxy log leftover; # haproxy.log on disk", "haproxy leftover|haproxy.log"),
    l_from(15, "envoy-log-leftover-handoff", "enlg", "envoy.log", "envoy log leftover", "envoy log leftover", "not envoy config leftover; leftover envoy log as dest", "ship leftover envoy log as dest.", "envoy log leftover; # envoy.log on disk", "envoy leftover|envoy.log"),
    l_from(16, "traefik-log-leftover-handoff", "tflg", "traefik.log", "traefik log leftover", "traefik log leftover", "not traefik acme leftover; leftover traefik log as dest", "ship leftover traefik log as dest.", "traefik log leftover; # traefik.log on disk", "traefik leftover|traefik.log"),
    l_from(17, "varnish-log-leftover-handoff", "valg", "varnish.log", "varnish log leftover", "varnish log leftover", "not varnish vcl leftover; leftover varnish log as dest", "ship leftover varnish log as dest.", "varnish log leftover; # varnish.log on disk", "varnish leftover|varnish.log"),
    l_from(18, "squid-log-leftover-handoff", "sqlg", "squid/access.log", "squid log leftover", "squid log leftover", "not squid cache leftover; leftover squid log as dest", "ship leftover squid log as dest.", "squid log leftover; # squid/access.log on disk", "squid leftover|squid/access.log"),
    l_from(19, "mitmproxy-log-leftover-handoff", "mtlg", "mitmproxy.log", "mitmproxy log leftover", "mitmproxy log leftover", "not mitmproxy flow leftover; leftover mitmproxy log as dest", "ship leftover mitmproxy log as dest.", "mitmproxy log leftover; # mitmproxy.log on disk", "mitmproxy leftover|mitmproxy.log"),
    l_from(20, "wireshark-log-leftover-handoff", "wslg2", "wireshark.log", "wireshark log leftover", "wireshark log leftover", "not wireshark pcap leftover; leftover wireshark log as dest", "ship leftover wireshark log as dest.", "wireshark log leftover; # wireshark.log on disk", "wireshark leftover|wireshark.log"),
    l_from(21, "tcpdump-log-leftover-handoff", "tdlg", "tcpdump.log", "tcpdump log leftover", "tcpdump log leftover", "not tcpdump pcap leftover; leftover tcpdump log as dest", "ship leftover tcpdump log as dest.", "tcpdump log leftover; # tcpdump.log on disk", "tcpdump leftover|tcpdump.log"),
    l_from(22, "tshark-log-leftover-handoff", "tslg2", "tshark.log", "tshark log leftover", "tshark log leftover", "not tshark json leftover; leftover tshark log as dest", "ship leftover tshark log as dest.", "tshark log leftover; # tshark.log on disk", "tshark leftover|tshark.log"),
    l_from(23, "socat-pid-leftover-handoff", "sotpid", "socat.pid", "socat pid leftover", "socat pid leftover", "not socat log leftover; leftover socat pid as dest", "ship leftover socat pid as dest.", "socat pid leftover; # socat.pid on disk", "socat leftover|socat.pid"),
    l_from(24, "ncat-pid-leftover-handoff", "ncpid", "ncat.pid", "ncat pid leftover", "ncat pid leftover", "not ncat log leftover; leftover ncat pid as dest", "ship leftover ncat pid as dest.", "ncat pid leftover; # ncat.pid on disk", "ncat leftover|ncat.pid"),
    l_from(25, "iperf-log-leftover-handoff", "iplg", "iperf.log", "iperf log leftover", "iperf log leftover", "not iperf json leftover; leftover iperf log as dest", "ship leftover iperf log as dest.", "iperf log leftover; # iperf.log on disk", "iperf leftover|iperf.log"),
    l_from(26, "mtr-log-leftover-handoff", "mtlg2", "mtr.log", "mtr log leftover", "mtr log leftover", "not mtr json leftover; leftover mtr log as dest", "ship leftover mtr log as dest.", "mtr log leftover; # mtr.log on disk", "mtr leftover|mtr.log"),
    l_from(27, "traceroute-json-leftover-handoff", "trjs2", "traceroute.json", "traceroute json leftover", "traceroute json leftover", "not traceroute log leftover; leftover traceroute json as dest", "ship leftover traceroute json as dest.", "traceroute json leftover; # traceroute.json on disk", "traceroute leftover|traceroute.json"),
    l_from(28, "keepalived-log-leftover-handoff", "kvlg", "keepalived.log", "keepalived log leftover", "keepalived log leftover", "not keepalived conf leftover; leftover keepalived log as dest", "ship leftover keepalived log as dest.", "keepalived log leftover; # keepalived.log on disk", "keepalived leftover|keepalived.log"),
    l_from(29, "bird-log-leftover-handoff", "brlg", "bird.log", "bird log leftover", "bird log leftover", "not bird conf leftover; leftover bird log as dest", "ship leftover bird log as dest.", "bird log leftover; # bird.log on disk", "bird leftover|bird.log"),
    l_from(30, "frr-log-leftover-handoff", "frlg", "frr.log", "frr log leftover", "frr log leftover", "not frr conf leftover; leftover frr log as dest", "ship leftover frr log as dest.", "frr log leftover; # frr.log on disk", "frr leftover|frr.log"),
    l_from(31, "charon-pid-leftover-handoff", "chpid", "charon.pid", "charon pid leftover", "charon pid leftover", "not strongswan log leftover; leftover charon pid as dest", "ship leftover charon pid as dest.", "charon pid leftover; # charon.pid on disk", "charon leftover|charon.pid"),
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
        print("usage: ntp-mill-unique-llll24.py ROUND STAGING_DIR", file=sys.stderr)
        return 2
    round_n = int(argv[0])
    staging = Path(argv[1])
    staging.mkdir(parents=True, exist_ok=True)
    i1, i2 = write_stage(staging, round_n)
    print(f"wrote r{round_n} {i1} {i2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
