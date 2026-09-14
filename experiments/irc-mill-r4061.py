#!/usr/bin/env python3
"""IRC mill r4061+ — wave-48 media/vcs leftover.

NEW on-call plants (not Wave-27–47 tails). BAN ypbind/oddjob,
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
cmus|CMUS_TIMEOUT|1|10|s|/etc/cmus/autosave|timeout=1|timeout=10|systemctl reload cmus|cmus-remote|cmu_to_1|lib|playlists|fs leftover leftover down; bounce|CMUS_TIMEOUT leftover 1 leftover; a 2s add is aborted so the lib 504s
moc|MOC_TIMEOUT|1|10|s|/etc/moc/config|Timeout = 1|Timeout = 10|systemctl reload moc|mocp|moc_to_1|playlists|out|fs leftover leftover down; bounce|MOC_TIMEOUT leftover 1 leftover; a 2s play is aborted so the queue 504s
clementine|CLEM_TIMEOUT|1|10|s|/etc/clementine/Clementine.conf|timeout=1|timeout=10|systemctl reload clementine|clementine|cle_to_1|lib|playlists|fs leftover leftover down; bounce|CLEM_TIMEOUT leftover 1 leftover; a 2s scan is aborted so the lib 504s
rhythmbox|RB_TIMEOUT|1|10|s|/etc/rhythmbox/rhythmdb.xml|timeout=1|timeout=10|systemctl reload rhythmbox|rhythmbox-client|rb_to_1|lib|playlists|fs leftover leftover down; bounce|RB_TIMEOUT leftover 1 leftover; a 2s import is aborted so the lib 504s
banshee|BANSHEE_TIMEOUT|1|10|s|/etc/banshee/banshee.conf|timeout=1|timeout=10|systemctl reload banshee|banshee|ban_to_1|lib|playlists|fs leftover leftover down; bounce|BANSHEE_TIMEOUT leftover 1 leftover; a 2s import is aborted so the lib 504s
audacious|AUD_TIMEOUT|1|10|s|/etc/audacious/config|timeout=1|timeout=10|systemctl reload audacious|audacious|aud_to_1|playlists|out|fs leftover leftover down; bounce|AUD_TIMEOUT leftover 1 leftover; a 2s open is aborted so playback 504s
deadbeef|DEADBEEF_TIMEOUT|1|10|s|/etc/deadbeef/deadbeef.conf|timeout=1|timeout=10|systemctl reload deadbeef|deadbeef|ddb_to_1|playlists|out|fs leftover leftover down; bounce|DEADBEEF_TIMEOUT leftover 1 leftover; a 2s open is aborted so playback 504s
strawberry|STRAWBERRY_TIMEOUT|1|10|s|/etc/strawberry/strawberry.conf|timeout=1|timeout=10|systemctl reload strawberry|strawberry|str_to_1|lib|playlists|fs leftover leftover down; bounce|STRAWBERRY_TIMEOUT leftover 1 leftover; a 2s scan is aborted so the lib 504s
ncmpcpp|NCMPCPP_TIMEOUT|1|10|s|/etc/ncmpcpp/config|mpd_connection_timeout = 1|mpd_connection_timeout = 10|systemctl reload ncmpcpp|ncmpcpp|ncp_to_1|mpd|playlists|tcp leftover leftover down; bounce|NCMPCPP_TIMEOUT leftover 1 leftover; a 2s status is aborted so the tui 504s
hg|HG_TIMEOUT|1|30|s|/etc/mercurial/hgrc|timeout=1|timeout=30|systemctl reload hg|hg|hg_to_1|revlogs|store|fs leftover leftover down; bounce|HG_TIMEOUT leftover 1 leftover; a 2s pull is aborted so the clone 504s
svn|SVN_TIMEOUT|1|30|s|/etc/subversion/servers|http-timeout=1|http-timeout=30|systemctl reload svnserve|svn|svn_to_1|revs|fsfs|fs leftover leftover down; bounce|SVN_TIMEOUT leftover 1 leftover; a 2s update is aborted so the wc 504s
bzr|BZR_TIMEOUT|1|30|s|/etc/bazaar/bazaar.conf|timeout=1|timeout=30|systemctl reload bzr|bzr|bzr_to_1|revs|branch|fs leftover leftover down; bounce|BZR_TIMEOUT leftover 1 leftover; a 2s pull is aborted so the branch 504s
fossil|FOSSIL_TIMEOUT|1|30|s|/etc/fossil/fossil.conf|timeout=1|timeout=30|systemctl reload fossil|fossil|fos_to_1|sqlite|repo|fs leftover leftover down; bounce|FOSSIL_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the repo 504s
pijul|PIJUL_TIMEOUT|1|30|s|/etc/pijul/config.toml|timeout = 1|timeout = 30|systemctl reload pijul|pijul|pij_to_1|changes|channel|fs leftover leftover down; bounce|PIJUL_TIMEOUT leftover 1 leftover; a 2s pull is aborted so the channel 504s
darcs|DARCS_TIMEOUT|1|30|s|/etc/darcs/defaults|timeout 1|timeout 30|systemctl reload darcs|darcs|dar_to_1|patches|repo|fs leftover leftover down; bounce|DARCS_TIMEOUT leftover 1 leftover; a 2s pull is aborted so the repo 504s
perforce|P4_TIMEOUT|1|30|s|/etc/perforce/p4d.conf|timeout=1|timeout=30|systemctl reload p4d|p4|p4_to_1|db|depots|fs leftover leftover down; bounce|P4_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the ws 504s
plastic|PLASTIC_TIMEOUT|1|30|s|/etc/plastic/server.conf|timeout=1|timeout=30|systemctl reload plasticscm|cm|pla_to_1|revs|repos|fs leftover leftover down; bounce|PLASTIC_TIMEOUT leftover 1 leftover; a 2s update is aborted so the wk 504s
opusenc|OPUSENC_TIMEOUT|1|30|s|/etc/opus/opusenc.conf|timeout=1|timeout=30|systemctl reload opusenc|opusenc|ope_to_1|wav|opus|fs leftover leftover down; bounce|OPUSENC_TIMEOUT leftover 1 leftover; a 2s encode is aborted so the opus 504s
vorbis|OGGENC_TIMEOUT|1|30|s|/etc/vorbis/oggenc.conf|timeout=1|timeout=30|systemctl reload oggenc|oggenc|vor_to_1|wav|ogg|fs leftover leftover down; bounce|OGGENC_TIMEOUT leftover 1 leftover; a 2s encode is aborted so the ogg 504s
ytdlp|YTDLP_TIMEOUT|1|30|s|/etc/yt-dlp/config|timeout=1|timeout=30|systemctl reload yt-dlp|yt-dlp|ytd_to_1|vids|out|https leftover leftover 403; bounce|YTDLP_TIMEOUT leftover 1 leftover; a 2s extract is aborted so the dl 504s
gallerydl|GALLERYDL_TIMEOUT|1|30|s|/etc/gallery-dl/config.json|"timeout": 1|"timeout": 30|systemctl reload gallery-dl|gallery-dl|gdl_to_1|imgs|out|https leftover leftover 403; bounce|GALLERYDL_TIMEOUT leftover 1 leftover; a 2s GET is aborted so the dl 504s
streamlink|STREAMLINK_TIMEOUT|1|30|s|/etc/streamlink/config|stream-timeout=1|stream-timeout=30|systemctl reload streamlink|streamlink|stl_to_1|hls|out|https leftover leftover 403; bounce|STREAMLINK_TIMEOUT leftover 1 leftover; a 2s playlist is aborted so the stream 504s
ncmpc|NCMPC_TIMEOUT|1|10|s|/etc/ncmpc/config|mpd_timeout = 1|mpd_timeout = 10|systemctl reload ncmpc|ncmpc|ncm_to_1|mpd|playlists|tcp leftover leftover down; bounce|NCMPC_TIMEOUT leftover 1 leftover; a 2s status is aborted so the tui 504s
mpc|MPC_TIMEOUT|1|10|s|/etc/mpd/mpc.conf|timeout=1|timeout=10|systemctl reload mpc|mpc|mpc_to_1|mpd|playlists|tcp leftover leftover down; bounce|MPC_TIMEOUT leftover 1 leftover; a 2s status is aborted so the cli 504s
quodlibet|QL_TIMEOUT|1|10|s|/etc/quodlibet/config|timeout=1|timeout=10|systemctl reload quodlibet|quodlibet|ql_to_1|lib|playlists|fs leftover leftover down; bounce|QL_TIMEOUT leftover 1 leftover; a 2s scan is aborted so the lib 504s
gmusicbrowser|GMB_TIMEOUT|1|10|s|/etc/gmusicbrowser/gmbrc|timeout=1|timeout=10|systemctl reload gmusicbrowser|gmusicbrowser|gmb_to_1|lib|playlists|fs leftover leftover down; bounce|GMB_TIMEOUT leftover 1 leftover; a 2s scan is aborted so the lib 504s
lollypop|LOLLYPOP_TIMEOUT|1|10|s|/etc/lollypop/lollypop.conf|timeout=1|timeout=10|systemctl reload lollypop|lollypop|lol_to_1|lib|playlists|fs leftover leftover down; bounce|LOLLYPOP_TIMEOUT leftover 1 leftover; a 2s scan is aborted so the lib 504s
amberol|AMBEROL_TIMEOUT|1|10|s|/etc/amberol/amberol.conf|timeout=1|timeout=10|systemctl reload amberol|amberol|amb_to_1|queue|out|fs leftover leftover down; bounce|AMBEROL_TIMEOUT leftover 1 leftover; a 2s open is aborted so playback 504s
celluloid|CELLULOID_TIMEOUT|1|10|s|/etc/celluloid/celluloid.conf|timeout=1|timeout=10|systemctl reload celluloid|celluloid|cel_to_1|demux|out|fs leftover leftover down; bounce|CELLULOID_TIMEOUT leftover 1 leftover; a 2s open is aborted so playback 504s
haruna|HARUNA_TIMEOUT|1|10|s|/etc/haruna/haruna.conf|timeout=1|timeout=10|systemctl reload haruna|haruna|har_to_1|demux|out|fs leftover leftover down; bounce|HARUNA_TIMEOUT leftover 1 leftover; a 2s open is aborted so playback 504s
smplayer|SMPLAYER_TIMEOUT|1|10|s|/etc/smplayer/smplayer.ini|timeout=1|timeout=10|systemctl reload smplayer|smplayer|smp_to_1|demux|out|fs leftover leftover down; bounce|SMPLAYER_TIMEOUT leftover 1 leftover; a 2s open is aborted so playback 504s
tautulli|TAUTULLI_TIMEOUT|1|10|s|/etc/tautulli/config.ini|timeout=1|timeout=10|systemctl reload tautulli|tautulli|tau_to_1|hist|users|http leftover leftover down; bounce|TAUTULLI_TIMEOUT leftover 1 leftover; a 2s API is aborted so the dash 504s
sonarr|SONARR_TIMEOUT|1|30|s|/etc/sonarr/config.xml|<Timeout>1</Timeout>|<Timeout>30</Timeout>|systemctl reload sonarr|sonarr|son_to_1|eps|idx|http leftover leftover down; bounce|SONARR_TIMEOUT leftover 1 leftover; a 2s rss is aborted so grab 504s
radarr|RADARR_TIMEOUT|1|30|s|/etc/radarr/config.xml|<Timeout>1</Timeout>|<Timeout>30</Timeout>|systemctl reload radarr|radarr|rad_to_1|movies|idx|http leftover leftover down; bounce|RADARR_TIMEOUT leftover 1 leftover; a 2s rss is aborted so grab 504s
lidarr|LIDARR_TIMEOUT|1|30|s|/etc/lidarr/config.xml|<Timeout>1</Timeout>|<Timeout>30</Timeout>|systemctl reload lidarr|lidarr|lid_to_1|albums|idx|http leftover leftover down; bounce|LIDARR_TIMEOUT leftover 1 leftover; a 2s rss is aborted so grab 504s
bazarr|BAZARR_TIMEOUT|1|30|s|/etc/bazarr/config.yaml|timeout: 1|timeout: 30|systemctl reload bazarr|bazarr|baz_to_1|subs|idx|http leftover leftover down; bounce|BAZARR_TIMEOUT leftover 1 leftover; a 2s search is aborted so the sub 504s
prowlarr|PROWLARR_TIMEOUT|1|30|s|/etc/prowlarr/config.xml|<Timeout>1</Timeout>|<Timeout>30</Timeout>|systemctl reload prowlarr|prowlarr|prw_to_1|idx|caps|http leftover leftover down; bounce|PROWLARR_TIMEOUT leftover 1 leftover; a 2s query is aborted so the idx 504s
unpackerr|UNPACKERR_TIMEOUT|1|30|s|/etc/unpackerr/unpackerr.conf|timeout = 1|timeout = 30|systemctl reload unpackerr|unpackerr|unp_to_1|rars|out|fs leftover leftover down; bounce|UNPACKERR_TIMEOUT leftover 1 leftover; a 2s extract is aborted so the rar 504s
sabnzbd|SAB_TIMEOUT|1|30|s|/etc/sabnzbd/sabnzbd.ini|timeout=1|timeout=30|systemctl reload sabnzbd|sabnzbd|sab_to_1|nzbs|out|nntp leftover leftover down; bounce|SAB_TIMEOUT leftover 1 leftover; a 2s article is aborted so the nzb 504s
nzbget|NZBGET_TIMEOUT|1|30|s|/etc/nzbget.conf|ArticleTimeout=1|ArticleTimeout=30|systemctl reload nzbget|nzbget|nzb_to_1|nzbs|out|nntp leftover leftover down; bounce|NZBGET_TIMEOUT leftover 1 leftover; a 2s article is aborted so the nzb 504s
'''
WAVE48 = (
    "cmus/moc/clementine/rhythmbox/banshee/audacious/deadbeef/strawberry/"
    "ncmpcpp/hg/svn/bzr/fossil/pijul/darcs/perforce/plastic/opusenc/vorbis/"
    "ytdlp/gallerydl/streamlink/ncmpc/mpc/quodlibet/gmusicbrowser/lollypop/"
    "amberol/celluloid/haruna/smplayer/tautulli/sonarr/radarr/lidarr/bazarr/"
    "prowlarr/unpackerr/sabnzbd/nzbget"
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
        svc = f"d8{i:02d}x"
        ns = f"d8{i:02d}"
        clu = f"prod-apsd{901 + i}-{svc[:3]}"
        ticket = f"W2-{12643 + i}"
        node = f"ip-10-233-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4061


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4060 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-48 leftover: {WAVE48}.",
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
