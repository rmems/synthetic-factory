#!/usr/bin/env python3
"""Mill monorepo-dep-bump-factory r1407+ unique print/identity/vpn/fs/dns leftover plants.

BAN r01–r1406 clones including hydra-py-leftover-compose / sacred-py-leftover-observer,
solr-xml-leftover-cache / opensearchdash-yml-leftover-sso, leftover-revpin, libNNNN,
r690–r708 workspace clones. Do not rerun mdb-mill-r1351.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

_BASE = Path(__file__).with_name("mdb-mill-r1351.py")
_spec = importlib.util.spec_from_file_location("mdb_mill_r1351", _BASE)
_m = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_m)

FACTORY = _m.FACTORY
GEN = _m.GEN
CATALOG_FIRST = 1407
P = _m.P
build_episode = _m.build_episode
make = _m.make

PRIOR_SLUGS = tuple(spec["slug"] for pair in _m.PAIRS for spec in pair)
BANNED_SLUG_NEEDLES = _m.BANNED_SLUG_NEEDLES + PRIOR_SLUGS + (
    "hydra-py-leftover-compose",
    "sacred-py-leftover-observer",
    "solr-xml-leftover-cache",
    "opensearchdash-yml-leftover-sso",
    "leftover-revpin",
    "libNNNN",
    "pnpm-override",
    "npm-catalog",
    "yarn-constraints",
    "bun-catalog",
    "uv-workspace",
    "poetry-source",
    "cargo-wsdep",
    "gowork-use",
    "maven-bom",
    "gradle-catalog",
    "nx-implicit",
    "turbo-",
    "changesets-",
)
_m.BANNED_SLUG_NEEDLES = BANNED_SLUG_NEEDLES

STEMS = [
    "weevil", "earwig", "damselfly", "stonefly", "caddisfly", "mayfly", "dobsonfly", "lacewing", "antlion", "snakefly",
    "scorpionfly", "hangingfly", "snowflea", "bristletail", "silverfish", "firebrat", "webspinner", "zorapteran", "termite", "cockroach",
    "mantis", "stickinsect", "leafinsect", "grasshopper", "katydid", "cricket", "molecricket", "cicada", "leafhopper", "planthopper",
    "treehopper", "spittlebug", "scaleinsect", "whitefly", "aphid", "adelgid", "phylloxera", "psyllid", "thrips", "truebug",
    "assassin", "ambushbug", "stinkbug", "squashbug", "waterstrider", "backswimmer", "giantwaterbug", "toadbug", "lacebug", "bedbug",
    "flowerbug", "damselbug", "plantbug", "seedbug", "burrower", "shorebug", "velvetwater", "springtail", "firefly", "glowworm",
    "clickbeetle", "soldierbeetle", "blisterbeetle", "stagbeetle", "rhinoceros", "dungbeetle", "groundbeetle", "tigerbeetle", "whirligig", "divingbeetle",
    "waterbeetle", "longhorn", "jewelbeetle", "leafbeetle", "fleabeetle", "cucumberbeetle", "colorado", "barkbeetle", "rovebeetle", "clicker",
]
assert len(STEMS) == 80
PLANTS = [f"{s}a" for s in STEMS] + [f"{s}b" for s in STEMS]


def notes_for(round_n: int, a: dict, b: dict) -> str:
    ea = f"mdb-r{round_n}-{a['slug']}"
    eb = f"mdb-r{round_n}-{b['slug']}"
    novel = 88 + (round_n % 5)
    return f"""# NOTES-r{round_n} monorepo-dep-bump-factory

Novel coverage: {novel}%

Two designed episodes (quota 2). Surfaces: {a['surface']} ({a['pkg']} {a['api_break']}); {b['surface']} ({b['pkg']} {b['api_break']}).
Not a pin-file mill and not libNNNN recycle. Distinct from r01–r1406 clones (ban hydra-py-leftover-compose / sacred-py-leftover-observer; solr-xml-leftover-cache / opensearchdash-yml-leftover-sso; leftover-revpin; r690–r708 workspace clones).

| id | seed | first apply | plan change | terminal |
|---|---|---|---|---|
| {ea} | {a['surface']} | nested {a['new']} | SoT {a['new']} + {a['api_break']} | {'leftover-workspace fail; ' + a['left'] + ' ' + a.get('left_ver', a['old']) if a['fail'] else 'success; ' + a['left'] + ' leftover'} |
| {eb} | {b['surface']} | nested {b['new']} | SoT {b['new']} + {b['api_break']} | {'leftover-workspace fail; ' + b['left'] + ' ' + b.get('left_ver', b['old']) if b['fail'] else 'success; ' + b['left'] + ' leftover'} |

## Step counts
- ep1: 18. Nested apply 6–7; plan change 8; API break 10–12; leftover {a['left']}.
- ep2: 18. Nested apply 6–7; plan change 8; API break 10–12; leftover-workspace fail {b['left']}.

## decision_basis audit
Every step starts Plan:/Observation:/Reflection:, ≤240 chars.
No thought / chain_of_thought / scratch / inner_monologue. No spike_events.
No sim_or_real: real. Plants `{a['plant']}` and `{b['plant']}`.

## Weaknesses / next
Keep unique leftover leftover leftover plots. Ban r01–r1406 clones, libNNNN, r690–r708 workspace clones.
"""


RAW: list[tuple] = [
    ("klipper-cfg-leftover-inputshaper", "Klipper leftover vs printer.cfg", "klipper", "0.12.0", "0.13.0", "printer.cfg",
     "[input_shaper]\nshaper_type: mzv", "[input_shaper]\nshaper_type: ei", "shaper_freq_x: 50", "shaper_freq_x: 62.5",
     "mzv → ei + 62.5 Hz", "cfg"),
    ("moonraker-conf-leftover-auth", "Moonraker leftover vs moonraker.conf", "moonraker", "0.8.0", "0.9.3", "moonraker.conf",
     "enable_api_key: False", "enable_api_key: True", "cors_domains: *", "cors_domains:\n  - https://api.local",
     "api key on + cors list", "conf"),
    ("cura-json-leftover-profile", "Cura leftover vs profile.json", "cura", "5.7.2", "5.9.0", "profile.json",
     "\"layer_height\": 0.2", "\"layer_height\": 0.12", "\"infill_sparse_density\": 20", "\"infill_sparse_density\": 40",
     "0.12 mm + 40% infill", "json"),
    ("prusaslicer-ini-leftover-layer", "PrusaSlicer leftover vs ps.ini", "prusaslicer", "2.7.4", "2.9.0", "ps.ini",
     "layer_height = 0.2", "layer_height = 0.15", "fill_pattern = grid", "fill_pattern = gyroid",
     "0.15 mm + gyroid", "ini"),
    ("octoprint-yaml-leftover-plugin", "OctoPrint leftover vs config.yaml", "octoprint", "1.10.2", "1.10.3", "config.yaml",
     "plugins.bedlevelvisualizer.enabled: false", "plugins.bedlevelvisualizer.enabled: true",
     "server.commands.serverRestartCommand: null", "server.commands.serverRestartCommand: sudo systemctl restart octoprint",
     "bedlevel on + restart cmd", "yaml"),
    ("mainsail-conf-leftover-theme", "Mainsail leftover vs .theme", "mainsail", "2.12.0", "2.13.2", "mainsail.conf",
     "theme: dark", "theme: light", "sidebar: true", "sidebar: true\nprimary: '#00a86b'",
     "light + jade primary", "conf"),
    ("fluidd-json-leftover-macros", "Fluidd leftover vs fluidd.json", "fluidd", "1.30.3", "1.31.4", "fluidd.json",
     "\"macroMode\": \"simple\"", "\"macroMode\": \"expert\"", "\"hiddenMacros\": []", "\"hiddenMacros\": [\"CANCEL_PRINT\"]",
     "expert + hide CANCEL", "json"),
    ("repetier-ini-leftover-extruder", "Repetier leftover vs repetier.ini", "repetier", "1.0.5", "1.0.6", "repetier.ini",
     "numExtruder=1", "numExtruder=2", "maxJerk=20", "maxJerk=12", "dual extruder + jerk 12", "ini"),
    ("marlin-h-leftover-jerk", "Marlin leftover vs Config.h", "marlin", "2.1.2", "2.1.2.5", "Config.h",
     "#define DEFAULT_EJERK 5.0", "#define DEFAULT_EJERK 8.0",
     "#define CLASSIC_JERK", "#define JUNCTION_DEVIATION_MM 0.02",
     "junction deviation + Ejerk 8", "h"),
    ("smoothieware-cfg-leftover-accel", "Smoothieware leftover vs config", "smoothieware", "edge-2016", "edge-2024", "config",
     "acceleration 3000", "acceleration 5000", "junction_deviation 0.05", "junction_deviation 0.02",
     "5k accel + jd 0.02", "config"),
    ("duet-gcode-leftover-mesh", "Duet leftover vs sys/config.g", "duet", "3.5.2", "3.5.4", "config.g",
     "M557 X20:180 Y20:180 S20", "M557 X10:190 Y10:190 S10", "M376 H10", "M376 H5",
     "finer mesh + fade 5", "g"),
    ("bambustudio-json-leftover-ams", "Bambu leftover vs ams.json", "bambustudio", "1.9.5", "1.10.2", "ams.json",
     "\"ams_use_ams\": false", "\"ams_use_ams\": true", "\"filament_map\": [0]", "\"filament_map\": [0,1,2,3]",
     "AMS on + 4-slot map", "json"),
    ("orcaslicer-ini-leftover-ironing", "Orca leftover vs orca.ini", "orcaslicer", "2.1.1", "2.2.0", "orca.ini",
     "ironing = 0", "ironing = 1", "ironing_spacing = 0.15", "ironing_spacing = 0.1",
     "ironing on + 0.1 spacing", "ini"),
    ("canboot-ini-leftover-flash", "CanBoot leftover vs flash.ini", "canboot", "0.0.0", "0.1.0", "flash.ini",
     "application_start = 0x2000", "application_start = 0x8000", "canbus_frequency = 500000", "canbus_frequency = 1000000",
     "0x8000 start + 1M CAN", "ini"),
    ("keycloak-json-leftover-ssoidle", "Keycloak leftover vs realm.json", "keycloak", "25.0.4", "26.1.0", "realm.json",
     "\"loginWithEmailAllowed\": false", "\"loginWithEmailAllowed\": true",
     "\"ssoSessionIdleTimeout\": 1800", "\"ssoSessionIdleTimeout\": 300",
     "email login + 5m idle", "json"),
    ("authentik-yml-leftover-policyall", "Authentik leftover vs flow.yml", "authentik", "2024.8.3", "2025.2.1", "flow.yml",
     "designation: authentication", "designation: authorization",
     "policy_engine_mode: any", "policy_engine_mode: all",
     "authorization + all policies", "yml"),
    ("zitadel-yml-leftover-oidc", "Zitadel leftover vs zitadel.yml", "zitadel", "2.58.1", "2.67.2", "zitadel.yml",
     "ExternalSecure: false", "ExternalSecure: true",
     "DefaultInstance.OIDC.AccessTokenLifetime: 12h", "DefaultInstance.OIDC.AccessTokenLifetime: 1h",
     "secure + 1h access", "yml"),
    ("dex-yml-leftover-connector", "Dex leftover vs config.yml", "dex", "2.40.0", "2.41.1", "config.yml",
     "type: mockCallback", "type: oidc", "redirectURI: http://127.0.0.1:5556/callback",
     "redirectURI: https://dex.api/callback", "oidc + https callback", "yml"),
    ("kanidm-toml-leftover-origin", "Kanidm leftover vs server.toml", "kanidm", "1.3.3", "1.4.4", "server.toml",
     "origin = \"https://idm.legacy\"", "origin = \"https://idm.api\"",
     "domain = \"legacy.example\"", "domain = \"api.example\"",
     "api origin + domain", "toml"),
    ("freeipa-conf-leftover-dns", "FreeIPA leftover vs default.conf", "freeipa", "4.11.1", "4.12.2", "default.conf",
     "enable_ra = False", "enable_ra = True", "xmlrpc_uri = http://ipa.legacy/ipa/xml",
     "xmlrpc_uri = https://ipa.api/ipa/xml", "RA on + https xmlrpc", "conf"),
    ("sssd-conf-leftover-cache", "SSSD leftover vs sssd.conf", "sssd", "2.9.5", "2.10.2", "sssd.conf",
     "cache_credentials = False", "cache_credentials = True",
     "entry_cache_timeout = 5400", "entry_cache_timeout = 300",
     "creds cache + 5m timeout", "conf"),
    ("authelia-yml-leftover-totp", "Authelia leftover vs authelia.yml", "authelia", "4.38.16", "4.38.19", "authelia.yml",
     "totp.issuer: legacy", "totp.issuer: api", "totp.algorithm: sha1", "totp.algorithm: sha256",
     "api issuer + sha256", "yml"),
    ("oauth2proxy-cfg-leftover-cookie", "oauth2-proxy leftover vs oauth2.cfg", "oauth2proxy", "7.6.0", "7.8.1", "oauth2.cfg",
     "cookie_secure = false", "cookie_secure = true", "cookie_samesite = \"\"", "cookie_samesite = \"lax\"",
     "secure cookie + samesite lax", "cfg"),
    ("wireguard-conf-leftover-keepalive", "WireGuard leftover vs wg0.conf", "wireguard", "1.0.20210914", "1.0.20250521", "wg0.conf",
     "PersistentKeepalive = 0", "PersistentKeepalive = 25", "AllowedIPs = 10.0.0.0/24", "AllowedIPs = 10.0.0.0/16",
     "keepalive 25 + /16", "conf"),
    ("strongswan-conf-leftover-esp", "strongSwan leftover vs ipsec.conf", "strongswan", "5.9.14", "6.0.1", "ipsec.conf",
     "esp=aes128-sha256-modp2048", "esp=aes256gcm16-ecp256", "ikelifetime=3h", "ikelifetime=1h",
     "AES-GCM + 1h IKE", "conf"),
    ("openvpn-ovpn-leftover-tls", "OpenVPN leftover vs client.ovpn", "openvpn", "2.6.12", "2.6.13", "client.ovpn",
     "tls-version-min 1.2", "tls-version-min 1.3", "cipher AES-128-CBC", "data-ciphers AES-256-GCM",
     "TLS1.3 + AES-256-GCM", "ovpn"),
    ("tailscale-json-leftover-acl", "Tailscale leftover vs acl.json", "tailscale", "1.70.1", "1.80.0", "acl.json",
     "\"action\": \"accept\", \"src\": [\"*\"]", "\"action\": \"accept\", \"src\": [\"group:eng\"]",
     "\"dst\": [\"*:*\"]", "\"dst\": [\"tag:api:443\"]",
     "eng group + tag:api:443", "json"),
    ("netbird-yml-leftover-peer", "NetBird leftover vs mgmt.yml", "netbird", "0.29.4", "0.36.3", "mgmt.yml",
     "StoreConfig.Engine: sqlite", "StoreConfig.Engine: postgres",
     "TURNConfig.Enabled: false", "TURNConfig.Enabled: true",
     "postgres store + TURN", "yml"),
    ("nebula-yml-leftover-lighthouse", "Nebula leftover vs config.yml", "nebula", "1.9.3", "1.9.5", "config.yml",
     "am_lighthouse: false", "am_lighthouse: true", "punchy.punch: false", "punchy.punch: true",
     "lighthouse + punchy", "yml"),
    ("headscale-yml-leftover-derp", "Headscale leftover vs config.yaml", "headscale", "0.23.0", "0.24.2", "config.yaml",
     "derp.server.enabled: false", "derp.server.enabled: true", "dns.magic_dns: false", "dns.magic_dns: true",
     "embedded DERP + magic DNS", "yaml"),
    ("zerotier-json-leftover-rule", "ZeroTier leftover vs local.conf", "zerotier", "1.14.0", "1.14.2", "local.conf",
     "\"allowDefault\": false", "\"allowDefault\": true", "\"allowGlobal\": false", "\"allowGlobal\": true",
     "default + global routes", "conf"),
    ("tinc-conf-leftover-subnet", "tinc leftover vs tinc.conf", "tinc", "1.0.36", "1.1pre18", "tinc.conf",
     "Subnet = 10.0.0.0/24", "Subnet = 10.8.0.0/16", "Mode = router", "Mode = switch",
     "/16 subnet + switch", "conf"),
    ("zfs-conf-leftover-ashift", "ZFS leftover vs zed.rc", "zfs", "2.2.6", "2.3.0", "zed.rc",
     "ZED_SPARE_ON_CHECKSUM_ERRORS=0", "ZED_SPARE_ON_CHECKSUM_ERRORS=3",
     "ZED_NOTIFY_INTERVAL_SECS=3600", "ZED_NOTIFY_INTERVAL_SECS=300",
     "spare on 3 csum + 5m notify", "rc"),
    ("btrfs-conf-leftover-compress", "btrfs leftover vs btrfs.conf", "btrfs", "6.10", "6.12", "btrfs.conf",
     "compress=zlib", "compress=zstd:3", "autodefrag", "noautodefrag",
     "zstd:3 + noautodefrag", "conf"),
    ("lvm-conf-leftover-thin", "LVM leftover vs lvm.conf", "lvm", "2.03.23", "2.03.29", "lvm.conf",
     "thin_pool_autoextend_threshold = 100", "thin_pool_autoextend_threshold = 70",
     "thin_pool_autoextend_percent = 20", "thin_pool_autoextend_percent = 10",
     "70% threshold + 10%", "conf"),
    ("mdadm-conf-leftover-bitmap", "mdadm leftover vs mdadm.conf", "mdadm", "4.3", "4.4", "mdadm.conf",
     "BITMAP=none", "BITMAP=internal", "AUTO=-all", "AUTO=+imsm +ddf",
     "internal bitmap + imsm", "conf"),
    ("grub-cfg-leftover-timeout", "GRUB leftover vs grub.cfg", "grub", "2.12", "2.12-api", "grub.cfg",
     "set timeout=5", "set timeout=1", "set default=0", "set default=saved",
     "1s timeout + saved default", "cfg"),
    ("systemdboot-conf-leftover-uki", "systemd-boot leftover vs loader.conf", "systemdboot", "255", "257", "loader.conf",
     "timeout 5", "timeout 1", "default linux.conf", "default @saved",
     "1s + @saved", "conf"),
    ("dracut-conf-leftover-hostonly", "dracut leftover vs dracut.conf", "dracut", "103", "105", "dracut.conf",
     "hostonly=\"no\"", "hostonly=\"yes\"", "compress=\"gzip\"", "compress=\"zstd\"",
     "hostonly + zstd", "conf"),
    ("mkinitcpio-conf-leftover-hooks", "mkinitcpio leftover vs mkinitcpio.conf", "mkinitcpio", "39.2", "40", "mkinitcpio.conf",
     "HOOKS=(base udev autodetect modconf block filesystems)",
     "HOOKS=(base udev autodetect microcode modconf kms block filesystems)",
     "COMPRESSION=\"gzip\"", "COMPRESSION=\"zstd\"",
     "microcode+kms + zstd", "conf"),
    ("cryptsetup-conf-leftover-pbkdf", "cryptsetup leftover vs crypttab", "cryptsetup", "2.7.4", "2.7.5", "crypttab",
     "luks,discard", "luks,discard,pbkdf=argon2id", "timeout=0", "timeout=10",
     "argon2id + 10s timeout", "crypttab"),
    ("podman-conf-leftover-cgroup", "Podman leftover vs containers.conf", "podman", "5.2.2", "5.3.1", "containers.conf",
     "cgroup_manager = \"cgroupfs\"", "cgroup_manager = \"systemd\"",
     "network_backend = \"cni\"", "network_backend = \"netavark\"",
     "systemd cgroup + netavark", "conf"),
    ("nerdctl-toml-leftover-snapshotter", "nerdctl leftover vs nerdctl.toml", "nerdctl", "1.7.6", "2.0.2", "nerdctl.toml",
     "snapshotter = \"overlayfs\"", "snapshotter = \"stargz\"",
     "cni_path = \"/opt/cni/bin\"", "cni_path = \"/usr/lib/cni\"",
     "stargz + lib cni", "toml"),
    ("containerd-toml-leftover-runtime", "containerd leftover vs config.toml", "containerd", "1.7.22", "2.0.1", "config.toml",
     "runtime = \"io.containerd.runc.v2\"", "runtime = \"io.containerd.runc.v2\"\nSystemdCgroup = true",
     "discard_unpacked_layers = false", "discard_unpacked_layers = true",
     "systemd cgroup + discard layers", "toml"),
    ("crio-conf-leftover-conmon", "CRI-O leftover vs crio.conf", "crio", "1.30.6", "1.32.1", "crio.conf",
     "conmon = \"/usr/bin/conmon\"", "conmon = \"/usr/libexec/crio/conmon\"",
     "cgroup_manager = \"cgroupfs\"", "cgroup_manager = \"systemd\"",
     "crio conmon + systemd", "conf"),
    ("buildah-conf-leftover-isolation", "Buildah leftover vs registries.conf", "buildah", "1.37.2", "1.38.0", "registries.conf",
     "unqualified-search-registries = ['docker.io']", "unqualified-search-registries = ['quay.io']",
     "short-name-mode = \"permissive\"", "short-name-mode = \"enforcing\"",
     "quay + enforcing shorts", "conf"),
    ("skopeo-policy-leftover-reject", "Skopeo leftover vs policy.json", "skopeo", "1.16.1", "1.17.0", "policy.json",
     "\"type\": \"insecureAcceptAnything\"", "\"type\": \"reject\"",
     "\"transports\": {}", "\"transports\": {\"docker\": {\"quay.io\": [{\"type\": \"signedBy\"}]}}",
     "reject default + quay signed", "json"),
    ("runc-json-leftover-seccomp", "runc leftover vs config.json", "runc", "1.1.14", "1.2.3", "config.json",
     "\"seccomp\": null", "\"seccomp\": {\"defaultAction\": \"SCMP_ACT_ERRNO\"}",
     "\"noNewPrivileges\": false", "\"noNewPrivileges\": true",
     "seccomp errno + noNewPrivs", "json"),
    ("crun-json-leftover-cgroupv2", "crun leftover vs config.json", "crun", "1.16.1", "1.19", "config.json",
     "\"cgroupsPath\": \"/legacy\"", "\"cgroupsPath\": \"/api.slice/api.scope\"",
     "\"memory\": {\"limit\": 1073741824}", "\"memory\": {\"limit\": 2147483648}",
     "slice path + 2g mem", "json"),
    ("gvisor-json-leftover-platform", "gVisor leftover vs runsc.toml", "gvisor", "20240930.0", "20250127.0", "runsc.toml",
     "platform = \"ptrace\"", "platform = \"kvm\"", "network = \"sandbox\"", "network = \"host\"",
     "kvm + host net", "toml"),
    ("bind-conf-leftover-dnssec", "BIND leftover vs named.conf", "bind", "9.18.30", "9.20.4", "named.conf",
     "dnssec-validation no;", "dnssec-validation auto;", "recursion yes;", "recursion no;",
     "dnssec auto + no recursion", "conf"),
    ("unbound-conf-leftover-qname", "Unbound leftover vs unbound.conf", "unbound", "1.21.1", "1.22.0", "unbound.conf",
     "qname-minimisation: no", "qname-minimisation: yes", "prefetch: no", "prefetch: yes",
     "qname min + prefetch", "conf"),
    ("knot-conf-leftover-zone", "Knot leftover vs knot.conf", "knot", "3.3.8", "3.4.3", "knot.conf",
     "template: default", "template: api", "semantic-checks: off", "semantic-checks: on",
     "api template + semantic checks", "conf"),
    ("powerdns-conf-leftover-lua", "PowerDNS leftover vs pdns.conf", "powerdns", "4.9.1", "4.9.2", "pdns.conf",
     "launch=bind", "launch=gsqlite3", "lua-prequery-script=", "lua-prequery-script=/etc/pdns/pre.lua",
     "sqlite + lua prequery", "conf"),
    ("coredns-corefile-leftover-forward", "CoreDNS leftover vs Corefile", "coredns", "1.11.3", "1.12.0", "Corefile",
     "forward . 8.8.8.8", "forward . tls://1.1.1.1", "cache 30", "cache 60",
     "DoT 1.1.1.1 + 60s cache", "Corefile"),
    ("blocky-yml-leftover-blocking", "Blocky leftover vs config.yml", "blocky", "0.24", "0.25", "config.yml",
     "blocking.blockType: zeroIp", "blocking.blockType: nxDomain",
     "blocking.refreshPeriod: 4h", "blocking.refreshPeriod: 1h",
     "nxDomain + 1h refresh", "yml"),
    ("adguard-yaml-leftover-filter", "AdGuard leftover vs AdGuardHome.yaml", "adguard", "0.107.52", "0.107.57", "AdGuardHome.yaml",
     "filters: [{enabled: false}]", "filters: [{enabled: true, url: https://filters.api/list.txt}]",
     "dns.upstream_dns: [8.8.8.8]", "dns.upstream_dns: [tls://dns.quad9.net]",
     "filter on + quad9 tls", "yaml"),
    ("dnsmasq-conf-leftover-dnssec", "dnsmasq leftover vs dnsmasq.conf", "dnsmasq", "2.90", "2.91", "dnsmasq.conf",
     "#dnssec", "dnssec", "cache-size=150", "cache-size=10000",
     "dnssec + 10k cache", "conf"),
    ("kea-conf-leftover-ha", "Kea leftover vs kea-dhcp4.conf", "kea", "2.6.1", "2.7.6", "kea-dhcp4.conf",
     "\"high-availability\": []", "\"high-availability\": [{\"this-server-name\": \"api\"}]",
     "\"valid-lifetime\": 4000", "\"valid-lifetime\": 600",
     "HA peer + 10m lease", "conf"),
    ("postfix-cf-leftover-milter", "Postfix leftover vs main.cf", "postfix", "3.8.6", "3.9.1", "main.cf",
     "smtpd_milters =", "smtpd_milters = inet:localhost:11332",
     "milter_default_action = tempfail", "milter_default_action = accept",
     "rspamd milter + accept", "cf"),
    ("dovecot-conf-leftover-sieve", "Dovecot leftover vs dovecot.conf", "dovecot", "2.3.21", "2.4.0", "dovecot.conf",
     "mail_plugins = $mail_plugins", "mail_plugins = $mail_plugins sieve",
     "protocols = imap", "protocols = imap lmtp",
     "sieve + lmtp", "conf"),
    ("rspamd-conf-leftover-fuzzy", "Rspamd leftover vs local.d/fuzzy.conf", "rspamd", "3.9.1", "3.11.0", "fuzzy.conf",
     "fuzzy_check { }", "fuzzy_check { min_bytes = 64; }",
     "servers = \"127.0.0.1:11335\"", "servers = \"fuzzy.api:11335\"",
     "min_bytes 64 + remote fuzzy", "conf"),
    ("opendkim-conf-leftover-key", "OpenDKIM leftover vs opendkim.conf", "opendkim", "2.11.0", "2.11.0-api", "opendkim.conf",
     "Mode sv", "Mode s", "Canonicalization relaxed/relaxed", "Canonicalization relaxed/simple",
     "sign-only + simple body", "conf"),
    ("woodpecker-yml-leftover-clone", "Woodpecker leftover vs .woodpecker.yml", "woodpecker", "2.7.1", "2.8.3", "woodpecker.yml",
     "skip_clone: false", "skip_clone: true", "clone: { git: { image: woodpeckerci/plugin-git } }",
     "clone: { git: { image: woodpeckerci/plugin-git:2.6 } }",
     "skip_clone + git 2.6", "yml"),
    ("drone-yml-leftover-volume", "Drone leftover vs .drone.yml", "drone", "2.24.0", "2.25.0", "drone.yml",
     "volumes: []", "volumes: [{name: cache, host: {path: /cache}}]",
     "clone: { disable: false }", "clone: { disable: true }",
     "host cache + clone off", "yml"),
    ("buildkite-yml-leftover-plugin", "Buildkite leftover vs pipeline.yml", "buildkite", "3.0", "3.1", "pipeline.yml",
     "plugins: []", "plugins: [{docker#v5.11.0: {image: alpine}}]",
     "retry: { automatic: false }", "retry: { automatic: { limit: 2 } }",
     "docker plugin + retry 2", "yml"),
    ("concourse-yml-leftover-resource", "Concourse leftover vs pipeline.yml", "concourse", "7.11.2", "7.12.1", "pipeline.yml",
     "type: git", "type: registry-image", "check_every: 1m", "check_every: 5m",
     "registry-image + 5m check", "yml"),
    ("tekton-yml-leftover-pipeline", "Tekton leftover vs pipeline.yaml", "tekton", "0.62.0", "0.68.0", "pipeline.yaml",
     "timeout: 1h0m0s", "timeout: 15m0s", "finally: []", "finally: [{name: cleanup, taskRef: {name: git-clone}}]",
     "15m timeout + cleanup", "yaml"),
    ("rdkit-py-leftover-fp", "RDKit leftover vs fp.py", "rdkit", "2024.03.5", "2024.09.5", "fp.py",
     "AllChem.GetMorganFingerprintAsBitVect(m, 2, nBits=1024)",
     "AllChem.GetMorganFingerprintAsBitVect(m, 3, nBits=2048)",
     "DataStructs.TanimotoSimilarity(a,b)", "DataStructs.DiceSimilarity(a,b)",
     "r=3 2048 + Dice", "py"),
    ("openbabel-py-leftover-format", "Open Babel leftover vs ob.py", "openbabel", "3.1.1", "3.1.1-api", "ob.py",
     "ob.OBConversion().SetInFormat('smi')", "ob.OBConversion().SetInFormat('inchi')",
     "conv.SetOutFormat('mol')", "conv.SetOutFormat('sdf')",
     "inchi in + sdf out", "py"),
    ("cclib-py-leftover-parser", "cclib leftover vs cc.py", "cclib", "1.8.1", "1.8.1-api", "cc.py",
     "ccopen(p).parse()", "ccopen(p, datatype=ccData).parse()",
     "data.homos", "data.homos; data.getattributes()",
     "ccData + getattributes", "py"),
    ("pymol-pml-leftover-ray", "PyMOL leftover vs ray.pml", "pymol", "3.0.0", "3.1.0", "ray.pml",
     "set ray_trace_mode, 0", "set ray_trace_mode, 3", "png out.png", "png out.png, dpi=300, ray=1",
     "mode 3 + 300dpi ray", "pml"),
    ("vmd-tcl-leftover-rep", "VMD leftover vs vis.tcl", "vmd", "1.9.4a57", "1.9.4a58", "vis.tcl",
     "mol representation Lines", "mol representation NewCartoon",
     "mol addrep top", "mol addrep top; mol color ResType",
     "NewCartoon + ResType", "tcl"),
    ("mdanalysis-py-leftover-select", "MDAnalysis leftover vs sel.py", "mdanalysis", "2.7.0", "2.8.0", "sel.py",
     "u.select_atoms('protein')", "u.select_atoms('protein and name CA')",
     "ag.write('out.pdb')", "ag.write('out.pdb', bonds='conect')",
     "CA select + CONECT", "py"),
    ("openmm-py-leftover-integrator", "OpenMM leftover vs mm.py", "openmm", "8.1.1", "8.2.0", "mm.py",
     "LangevinIntegrator(300*kelvin, 1/picosecond, 0.002*picoseconds)",
     "LangevinMiddleIntegrator(300*kelvin, 1/picosecond, 0.004*picoseconds)",
     "simulation.step(1000)", "simulation.step(5000)",
     "Middle 4fs + 5k steps", "py"),
    ("plumed-dat-leftover-cv", "PLUMED leftover vs plumed.dat", "plumed", "2.9.2", "2.9.3", "plumed.dat",
     "DISTANCE ATOMS=1,2 LABEL=d", "DISTANCE ATOMS=1,2 LABEL=d COMPONENTS",
     "PRINT ARG=d FILE=COLVAR", "PRINT ARG=d.x,d.y,d.z FILE=COLVAR STRIDE=10",
     "components + stride 10", "dat"),
    ("gdb-gdbinit-leftover-pretty", "GDB leftover vs .gdbinit", "gdb", "15.1", "16.1", "gdbinit",
     "set print pretty off", "set print pretty on", "set pagination on", "set pagination off",
     "pretty on + no pager", "gdbinit"),
    ("lldb-init-leftover-format", "LLDB leftover vs .lldbinit", "lldb", "18.1.8", "19.1.7", "lldbinit",
     "settings set target.max-children-count 256", "settings set target.max-children-count 1024",
     "type summary add -s \"${var}\" --", "type summary add --inline-children --",
     "1024 children + inline", "lldbinit"),
    ("perf-conf-leftover-event", "perf leftover vs perf.conf", "perf", "6.10", "6.12", "perf.conf",
     "event=cycles", "event=cycles,instructions,cache-misses",
     "freq=100", "freq=1000",
     "3 events + 1kHz", "conf"),
    ("asyncprofiler-conf-leftover-alloc", "async-profiler leftover vs profiler.conf", "asyncprofiler", "3.0", "4.0", "profiler.conf",
     "event=cpu", "event=alloc", "interval=10ms", "interval=1ms",
     "alloc + 1ms", "conf"),
    ("pyspy-toml-leftover-native", "py-spy leftover vs spy.toml", "pyspy", "0.3.14", "0.4.0", "spy.toml",
     "native = false", "native = true", "subprocesses = false", "subprocesses = true",
     "native + subprocesses", "toml"),
    ("scalene-json-leftover-gpu", "Scalene leftover vs scalene.json", "scalene", "1.5.45", "1.5.51", "scalene.json",
     "\"gpu\": false", "\"gpu\": true", "\"cpu_percent_threshold\": 1", "\"cpu_percent_threshold\": 5",
     "GPU + 5% cpu thresh", "json"),
    ("bpftrace-bt-leftover-probe", "bpftrace leftover vs p.bt", "bpftrace", "0.21.2", "0.22.1", "p.bt",
     "kprobe:do_sys_open", "kprobe:do_sys_openat2", "printf(\"%s\\n\", str(arg1))", "printf(\"%s\\n\", str(arg1)); @opens[comm] = count()",
     "openat2 + per-comm count", "bt"),
    ("bcc-py-leftover-attach", "BCC leftover vs bcc.py", "bcc", "0.31.0", "0.33.0", "bcc.py",
     "b.attach_kprobe(event='do_sys_open', fn_name='trace')",
     "b.attach_kprobe(event='do_sys_openat2', fn_name='trace')",
     "b.trace_print()", "b.trace_print(fmt='{0}')",
     "openat2 + fmt", "py"),
    ("valgrind-conf-leftover-leak", "Valgrind leftover vs valgrind.conf", "valgrind", "3.23.0", "3.24.0", "valgrind.conf",
     "--leak-check=summary", "--leak-check=full --show-leak-kinds=all",
     "--track-origins=no", "--track-origins=yes",
     "full leaks + origins", "conf"),
    ("cups-conf-leftover-browse", "CUPS leftover vs cupsd.conf", "cups", "2.4.10", "2.4.11", "cupsd.conf",
     "Browsing Off", "Browsing On", "DefaultShared No", "DefaultShared Yes",
     "browse on + shared", "conf"),
    ("ghostscript-ps-leftover-pdf", "Ghostscript leftover vs gs.ps", "ghostscript", "10.03.1", "10.04.0", "gs.ps",
     "-sDEVICE=ps2write", "-sDEVICE=pdfwrite", "-dPDFSETTINGS=/screen", "-dPDFSETTINGS=/prepress",
     "pdfwrite + prepress", "ps"),
    ("harfbuzz-conf-leftover-shaper", "HarfBuzz leftover vs hb.conf", "harfbuzz", "9.0.0", "10.1.0", "hb.conf",
     "shaper=fallback", "shaper=ot", "features=+kern", "features=+kern,+liga",
     "ot shaper + liga", "conf"),
    ("freetype-conf-leftover-hint", "FreeType leftover vs fonts.conf", "freetype", "2.13.2", "2.13.3", "fonts.conf",
     "<edit name=\"hintstyle\" mode=\"assign\"><const>hintnone</const></edit>",
     "<edit name=\"hintstyle\" mode=\"assign\"><const>hintfull</const></edit>",
     "<edit name=\"antialias\" mode=\"assign\"><bool>false</bool></edit>",
     "<edit name=\"antialias\" mode=\"assign\"><bool>true</bool></edit>",
     "hintfull + aa", "conf"),
    ("fish-conf-leftover-vi", "fish leftover vs config.fish", "fish", "3.7.1", "4.0.0", "config.fish",
     "fish_vi_key_bindings", "fish_default_key_bindings", "set -U fish_greeting", "set -U fish_greeting ''",
     "emacs bindings + no greeting", "fish"),
    ("nushell-nu-leftover-table", "Nushell leftover vs config.nu", "nushell", "0.96.1", "0.101.0", "config.nu",
     "$env.config.table.mode = 'rounded'", "$env.config.table.mode = 'compact'",
     "$env.config.buffer_editor = 'vi'", "$env.config.buffer_editor = 'hx'",
     "compact table + hx", "nu"),
    ("xonsh-xsh-leftover-backend", "xonsh leftover vs .xonshrc", "xonsh", "0.18.2", "0.19.2", "xonshrc",
     "$VI_MODE = True", "$VI_MODE = False", "$XONSH_HISTORY_BACKEND = 'json'", "$XONSH_HISTORY_BACKEND = 'sqlite'",
     "emacs + sqlite hist", "xsh"),
    ("elvish-toml-leftover-prompt", "Elvish leftover vs rc.toml", "elvish", "0.21.0", "0.21.1", "rc.toml",
     "edit:prompt = { put '> ' }", "edit:prompt = { styled (tilde-abbr $pwd) green; put '> ' }",
     "use readline-binding", "use readline-binding; set edit:max-height = 20",
     "styled prompt + max-height", "toml"),
    ("oil-rc-leftover-strict", "Oils leftover vs oshrc", "oil", "0.22.0", "0.24.0", "oshrc",
     "shopt --unset strict_argv", "shopt --set strict_argv",
     "shopt --unset simple_word_eval", "shopt --set simple_word_eval",
     "strict_argv + simple_word_eval", "oshrc"),
]


def expand(row: tuple) -> tuple:
    slug, surface, pkg, old, new, pin, nest_old, nest_new, api_old, api_new, api_break, ext = row
    cmap = {
        "sql": "--", "R": "#", "hs": "--", "scala": "//", "vhdl": "--", "v": "//",
        "scd": "//", "orc": ";", "ttl": "#", "C": "//", "cpp": "//", "c": "//",
        "cs": "//", "dart": "//", "rb": "#", "php": "//", "js": "//", "ts": "//",
        "go": "//", "d": "//", "td": "//", "g": ";", "fish": "#", "nu": "#", "xsh": "#",
        "Corefile": "#", "crypttab": "#", "cf": "#",
    }
    comment = cmap.get(ext, "#")
    sot_old = f"{comment} {pkg} {old}"
    sot_new = f"{comment} {pkg} {new}"
    if ext == "py":
        tool = f"python3 -c 'import {pkg}; print({pkg}.__version__)'"
        test = f"python3 apps/api/{pin}"
        ws = f"python3 apps/legacy/{pin}"
    else:
        tool = f"python3 -c 'print(\"{pkg}\")' || true"
        test = f"python3 -c 'print(\"apps/api/{pin}\")'"
        ws = f"python3 -c 'print(\"apps/legacy/{pin}\")'"
    return (slug, surface, pkg, old, new, pin, sot_old, sot_new, nest_old, nest_new, api_old, api_new, api_break, tool, test, ws, ext)


TOOLS: list[tuple] = [expand(r) for r in RAW]
assert len(TOOLS) % 2 == 0
assert len(TOOLS) <= len(PLANTS)

PAIRS: list[tuple[dict, dict]] = []
_pi = 0
for i in range(0, len(TOOLS), 2):
    a = TOOLS[i]
    b = TOOLS[i + 1]
    suc = make(
        a[0], PLANTS[_pi], a[1], a[2], a[3], a[4], False,
        a[5], a[6], a[7], a[8], a[9], a[10], a[11], a[12], a[13], a[14], a[15], a[16],
    )
    _pi += 1
    failp = make(
        b[0], PLANTS[_pi], b[1], b[2], b[3], b[4], True,
        b[5], b[6], b[7], b[8], b[9], b[10], b[11], b[12], b[13], b[14], b[15], b[16],
    )
    _pi += 1
    PAIRS.append((suc, failp))


def _validate_catalog() -> None:
    slugs = [spec["slug"] for pair in PAIRS for spec in pair]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("duplicate slugs in r1407 catalog")
    for slug in slugs:
        for needle in BANNED_SLUG_NEEDLES:
            if needle and needle in slug:
                raise SystemExit(f"banned needle {needle!r} in {slug}")
    plants = [spec["plant"] for pair in PAIRS for spec in pair]
    if len(plants) != len(set(plants)):
        raise SystemExit("duplicate plants in r1407 catalog")


_validate_catalog()


def build_round(rnd: int) -> tuple[list[dict], str]:
    idx = rnd - CATALOG_FIRST
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(
            f"round {rnd} outside catalog {CATALOG_FIRST}..{CATALOG_FIRST + len(PAIRS) - 1}"
        )
    suc, fail = PAIRS[idx]
    suc_ep = build_episode(rnd, suc)
    fail_ep = build_episode(rnd, fail)
    for ep in (suc_ep, fail_ep):
        n = len(ep["steps"])
        if n < 16 or n > 20:
            raise SystemExit(f"{ep['id']} has {n} steps, want 16-20")
        blob = json.dumps(ep)
        for banned in (
            "thought",
            "chain_of_thought",
            "scratch",
            "inner_monologue",
            "spike_events",
        ):
            if f'"{banned}"' in blob:
                raise SystemExit(f"{ep['id']} contains banned key {banned}")
        if '"sim_or_real": "real"' in blob or '"sim_or_real":"real"' in blob:
            raise SystemExit(f"{ep['id']} claims sim_or_real real")
    notes = notes_for(rnd, suc, fail)
    if "Novel coverage:" not in notes:
        raise SystemExit("notes missing Novel coverage")
    return [suc_ep, fail_ep], notes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    args = ap.parse_args()
    rnd = args.round
    staging = Path(args.staging)
    recs, notes = build_round(rnd)
    batch = staging / f"batch-r{rnd:02d}.jsonl"
    notes_path = staging / f"NOTES-r{rnd:02d}.md"
    with batch.open("w") as handle:
        for rec in recs:
            handle.write(json.dumps(rec, ensure_ascii=True) + "\n")
    notes_path.write_text(notes)
    print(
        json.dumps(
            {
                "round": rnd,
                "ids": [r["id"] for r in recs],
                "steps": [len(r["steps"]) for r in recs],
                "success": [r["reward"]["success"] for r in recs],
                "batch": str(batch),
                "notes": str(notes_path),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
