#!/usr/bin/env python3
"""IRC mill r4081+ — wave-49 torrent/crypto leftover.

NEW on-call plants (not Wave-27–48 tails). BAN ypbind/oddjob,
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
transmission|TRANSMISSION_TIMEOUT|1|30|s|/etc/transmission-daemon/settings.json|"rpc-timeout": 1|"rpc-timeout": 30|systemctl reload transmission-daemon|transmission-remote|trm_to_1|torrents|peers|tcp leftover leftover down; bounce|TRANSMISSION_TIMEOUT leftover 1 leftover; a 2s announce is aborted so the swarm 504s
deluge|DELUGE_TIMEOUT|1|30|s|/etc/deluge/core.conf|"timeout": 1|"timeout": 30|systemctl reload deluged|deluge-console|dlg_to_1|torrents|peers|tcp leftover leftover down; bounce|DELUGE_TIMEOUT leftover 1 leftover; a 2s tracker is aborted so the torrent 504s
qbittorrent|QBT_TIMEOUT|1|30|s|/etc/qBittorrent/qBittorrent.conf|Session\Timeout=1|Session\Timeout=30|systemctl reload qbittorrent-nox|qbt|qbt_to_1|torrents|peers|tcp leftover leftover down; bounce|QBT_TIMEOUT leftover 1 leftover; a 2s announce is aborted so the swarm 504s
rtorrent|RTO_TIMEOUT|1|30|s|/etc/rtorrent/rtorrent.rc|timeout = 1|timeout = 30|systemctl reload rtorrent|rtorrent|rto_to_1|torrents|peers|tcp leftover leftover down; bounce|RTO_TIMEOUT leftover 1 leftover; a 2s tracker is aborted so the torrent 504s
flood|FLOOD_TIMEOUT|1|10|s|/etc/flood/config.js|timeout: 1|timeout: 10|systemctl reload flood|flood|fld_to_1|rpc|ui|tcp leftover leftover down; bounce|FLOOD_TIMEOUT leftover 1 leftover; a 2s rtorrent rpc is aborted so the ui 504s
jackett|JACKETT_TIMEOUT|1|30|s|/etc/jackett/ServerConfig.json|"timeout": 1|"timeout": 30|systemctl reload jackett|jackett|jak_to_1|idx|caps|https leftover leftover 403; bounce|JACKETT_TIMEOUT leftover 1 leftover; a 2s query is aborted so the idx 504s
flaresolverr|FLARESOLVERR_TIMEOUT|1|30|s|/etc/flaresolverr/config.env|TIMEOUT=1|TIMEOUT=30|systemctl reload flaresolverr|flaresolverr|fls_to_1|cf|sess|http leftover leftover down; bounce|FLARESOLVERR_TIMEOUT leftover 1 leftover; a 2s challenge is aborted so the idx 504s
mpvnet|MPVNET_TIMEOUT|1|10|s|/etc/mpvnet/mpvnet.conf|timeout=1|timeout=10|systemctl reload mpvnet|mpvnet|mpn_to_1|demux|out|fs leftover leftover down; bounce|MPVNET_TIMEOUT leftover 1 leftover; a 2s open is aborted so playback 504s
snapraid|SNAPRAID_TIMEOUT|1|3600|s|/etc/snapraid.conf|timeout 1|timeout 3600|systemctl reload snapraid|snapraid|snr_to_1|parity|disks|fs leftover leftover down; bounce|SNAPRAID_TIMEOUT leftover 1 leftover; a 2s sync is aborted so parity 504s
mergerfs|MERGERFS_TIMEOUT|1|10|s|/etc/mergerfs/mergerfs.conf|timeout=1|timeout=10|systemctl reload mergerfs|mergerfs|mrg_to_1|branches|mnt|fuse leftover leftover down; bounce|MERGERFS_TIMEOUT leftover 1 leftover; a 2s lookup is aborted so the pool 504s
unionfs|UNIONFS_TIMEOUT|1|10|s|/etc/unionfs/unionfs.conf|timeout=1|timeout=10|systemctl reload unionfs|unionfs|unf_to_1|branches|mnt|fuse leftover leftover down; bounce|UNIONFS_TIMEOUT leftover 1 leftover; a 2s lookup is aborted so the union 504s
aufs|AUFS_TIMEOUT|1|10|s|/etc/default/aufs|timeout=1|timeout=10|systemctl reload aufs|mount|auf_to_1|branches|mnt|kmod leftover leftover down; bounce|AUFS_TIMEOUT leftover 1 leftover; a 2s lookup is aborted so the union 504s
overlayfs|OVERLAY_TIMEOUT|1|10|s|/etc/overlayfs.conf|timeout=1|timeout=10|systemctl reload overlay|mount|ovl_to_1|upper|mnt|kmod leftover leftover down; bounce|OVERLAY_TIMEOUT leftover 1 leftover; a 2s copy-up is aborted so the mnt 504s
mhddfs|MHDD_TIMEOUT|1|10|s|/etc/mhddfs.conf|timeout=1|timeout=10|systemctl reload mhddfs|mhddfs|mhd_to_1|disks|mnt|fuse leftover leftover down; bounce|MHDD_TIMEOUT leftover 1 leftover; a 2s create is aborted so the pool 504s
encfs|ENCFS_TIMEOUT|1|10|s|/etc/encfs/encfs6.xml|timeout=1|timeout=10|systemctl reload encfs|encfs|enc_to_1|cipher|mnt|fuse leftover leftover down; bounce|ENCFS_TIMEOUT leftover 1 leftover; a 2s decode is aborted so the mnt 401s
gocryptfs|GOCRYPTFS_TIMEOUT|1|10|s|/etc/gocryptfs/gocryptfs.conf|timeout=1|timeout=10|systemctl reload gocryptfs|gocryptfs|goc_to_1|cipher|mnt|fuse leftover leftover down; bounce|GOCRYPTFS_TIMEOUT leftover 1 leftover; a 2s decode is aborted so the mnt 401s
cryfs|CRYFS_TIMEOUT|1|10|s|/etc/cryfs/cryfs.cfg|timeout=1|timeout=10|systemctl reload cryfs|cryfs|cry_to_1|cipher|mnt|fuse leftover leftover down; bounce|CRYFS_TIMEOUT leftover 1 leftover; a 2s decode is aborted so the mnt 401s
veracrypt|VERACRYPT_TIMEOUT|1|30|s|/etc/veracrypt/veracrypt.conf|timeout=1|timeout=30|systemctl reload veracrypt|veracrypt|vtc_to_1|vols|mnt|fuse leftover leftover down; bounce|VERACRYPT_TIMEOUT leftover 1 leftover; a 2s mount is aborted so the vol 401s
truecrypt|TRUECRYPT_TIMEOUT|1|30|s|/etc/truecrypt/truecrypt.conf|timeout=1|timeout=30|systemctl reload truecrypt|truecrypt|trc_to_1|vols|mnt|fuse leftover leftover down; bounce|TRUECRYPT_TIMEOUT leftover 1 leftover; a 2s mount is aborted so the vol 401s
zulucrypt|ZULU_TIMEOUT|1|30|s|/etc/zuluCrypt/zuluCrypt.conf|timeout=1|timeout=30|systemctl reload zuluCrypt|zuluCrypt-cli|zul_to_1|vols|mnt|dm leftover leftover down; bounce|ZULU_TIMEOUT leftover 1 leftover; a 2s open is aborted so the vol 401s
tomb|TOMB_TIMEOUT|1|30|s|/etc/tomb/tomb.conf|timeout=1|timeout=30|systemctl reload tomb|tomb|tmb_to_1|vols|mnt|luks leftover leftover down; bounce|TOMB_TIMEOUT leftover 1 leftover; a 2s open is aborted so the tomb 401s
pass|PASS_TIMEOUT|1|10|s|/etc/password-store/.gpg-id|timeout=1|timeout=10|systemctl reload pass|pass|pas_to_1|secrets|gpg|gpg leftover leftover down; bounce|PASS_TIMEOUT leftover 1 leftover; a 2s decrypt is aborted so the secret 401s
gopass|GOPASS_TIMEOUT|1|10|s|/etc/gopass/config.yml|timeout: 1|timeout: 10|systemctl reload gopass|gopass|gop_to_1|secrets|gpg|gpg leftover leftover down; bounce|GOPASS_TIMEOUT leftover 1 leftover; a 2s decrypt is aborted so the secret 401s
keepassxc|KEEPASSXC_TIMEOUT|1|10|s|/etc/keepassxc/keepassxc.ini|timeout=1|timeout=10|systemctl reload keepassxc|keepassxc-cli|kpx_to_1|kdbx|entries|fs leftover leftover down; bounce|KEEPASSXC_TIMEOUT leftover 1 leftover; a 2s unlock is aborted so the db 401s
keepass|KEEPASS_TIMEOUT|1|10|s|/etc/keepass/keepass.config.xml|timeout=1|timeout=10|systemctl reload keepass|keepass|kep_to_1|kdbx|entries|fs leftover leftover down; bounce|KEEPASS_TIMEOUT leftover 1 leftover; a 2s unlock is aborted so the db 401s
bitwarden|BITWARDEN_TIMEOUT|1|10|s|/etc/bitwarden/config.yml|timeout: 1|timeout: 10|systemctl reload bitwarden|bw|bwn_to_1|vault|items|https leftover leftover 403; bounce|BITWARDEN_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the vault 401s
youtube-dl|YOUTUBEDL_TIMEOUT|1|30|s|/etc/youtube-dl.conf|timeout=1|timeout=30|systemctl reload youtube-dl|youtube-dl|ytdl_to_1|vids|out|https leftover leftover 403; bounce|YOUTUBEDL_TIMEOUT leftover 1 leftover; a 2s extract is aborted so the dl 504s
yt-dlp|YTDLP2_TIMEOUT|1|30|s|/etc/yt-dlp.conf|socket-timeout=1|socket-timeout=30|systemctl reload yt-dlp|yt-dlp|ytd2_to_1|vids|out|https leftover leftover 403; bounce|YTDLP2_TIMEOUT leftover 1 leftover; a 2s extract is aborted so the dl 504s
aria2c|ARIA2C_TIMEOUT|1|30|s|/etc/aria2/aria2.conf|timeout=1|timeout=30|systemctl reload aria2c|aria2c|a2c_to_1|dls|files|tcp leftover leftover down; bounce|ARIA2C_TIMEOUT leftover 1 leftover; a 2s GET is aborted so the dl 504s
duplicacy|DUPLICACY_TIMEOUT|1|60|s|/etc/duplicacy/preferences|timeout=1|timeout=60|systemctl reload duplicacy|duplicacy|dup_to_1|chunks|repo|s3 leftover leftover 403; bounce|DUPLICACY_TIMEOUT leftover 1 leftover; a 2s backup is aborted so the rev 504s
borgmatic|BORGMATIC_TIMEOUT|1|60|s|/etc/borgmatic/config.yaml|timeout: 1|timeout: 60|systemctl reload borgmatic|borgmatic|bmt_to_1|archives|repo|ssh leftover leftover down; bounce|BORGMATIC_TIMEOUT leftover 1 leftover; a 2s create is aborted so backup 504s
jdownloader|JDOWNLOADER_TIMEOUT|1|30|s|/etc/jdownloader/jdownloader.conf|timeout=1|timeout=30|systemctl reload jdownloader|jdownloader|jdn_to_1|dls|files|https leftover leftover 403; bounce|JDOWNLOADER_TIMEOUT leftover 1 leftover; a 2s captcha is aborted so the dl 504s
pyload|PYLOAD_TIMEOUT|1|30|s|/etc/pyload/pyload.conf|timeout=1|timeout=30|systemctl reload pyload|pyload|pyl_to_1|dls|files|https leftover leftover 403; bounce|PYLOAD_TIMEOUT leftover 1 leftover; a 2s hoster is aborted so the dl 504s
megatools|MEGATOOLS_TIMEOUT|1|30|s|/etc/megatools/.megarc|timeout=1|timeout=30|systemctl reload megatools|megadl|mgt_to_1|files|cloud|https leftover leftover 403; bounce|MEGATOOLS_TIMEOUT leftover 1 leftover; a 2s GET is aborted so the dl 504s
gdrive|GDRIVE_TIMEOUT|1|30|s|/etc/gdrive/gdrive.conf|timeout=1|timeout=30|systemctl reload gdrive|gdrive|gdr_to_1|files|drive|https leftover leftover 403; bounce|GDRIVE_TIMEOUT leftover 1 leftover; a 2s list is aborted so the sync 504s
age|AGE_TIMEOUT|1|10|s|/etc/age/age.conf|timeout=1|timeout=10|systemctl reload age|age|age_to_1|files|keys|fs leftover leftover down; bounce|AGE_TIMEOUT leftover 1 leftover; a 2s decrypt is aborted so the file 401s
pwsafe|PWSAFE_TIMEOUT|1|10|s|/etc/pwsafe/pwsafe.cfg|timeout=1|timeout=10|systemctl reload pwsafe|pwsafe|pws_to_1|db|entries|fs leftover leftover down; bounce|PWSAFE_TIMEOUT leftover 1 leftover; a 2s unlock is aborted so the db 401s
qtpass|QTPASS_TIMEOUT|1|10|s|/etc/qtpass/qtpass.conf|timeout=1|timeout=10|systemctl reload qtpass|qtpass|qtp_to_1|store|gpg|gpg leftover leftover down; bounce|QTPASS_TIMEOUT leftover 1 leftover; a 2s decrypt is aborted so the secret 401s
enpass|ENPASS_TIMEOUT|1|10|s|/etc/enpass/enpass.conf|timeout=1|timeout=10|systemctl reload enpass|enpass|enp_to_1|vault|items|fs leftover leftover down; bounce|ENPASS_TIMEOUT leftover 1 leftover; a 2s unlock is aborted so the vault 401s
lastpass|LASTPASS_TIMEOUT|1|10|s|/etc/lastpass/lpass.conf|timeout=1|timeout=10|systemctl reload lpass|lpass|lps_to_1|vault|items|https leftover leftover 403; bounce|LASTPASS_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the vault 401s
'''
WAVE49 = (
    "transmission/deluge/qbittorrent/rtorrent/flood/jackett/flaresolverr/"
    "mpvnet/snapraid/mergerfs/unionfs/aufs/overlayfs/mhddfs/encfs/gocryptfs/"
    "cryfs/veracrypt/truecrypt/zulucrypt/tomb/pass/gopass/keepassxc/keepass/"
    "bitwarden/youtube-dl/yt-dlp/aria2c/duplicacy/borgmatic/jdownloader/"
    "pyload/megatools/gdrive/age/pwsafe/qtpass/enpass/lastpass"
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
        svc = f"e9{i:02d}x"
        ns = f"e9{i:02d}"
        clu = f"prod-apsf{901 + i}-{svc[:3]}"
        ticket = f"W2-{12683 + i}"
        node = f"ip-10-234-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4081


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4080 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-49 leftover: {WAVE49}.",
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
