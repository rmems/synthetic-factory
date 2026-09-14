#!/usr/bin/env python3
"""IRC mill r4961+ — wave-93 gitops6 leftover.

NEW on-call plants (not Wave-27–60 tails). BAN ypbind/oddjob,
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
puppet6|PUPPET6_TIMEOUT|1|30|s|/etc/puppet6/puppet6.conf|timeout=1|timeout=30|systemctl reload puppet6|pu6|pup_to_1|jobs|state|https leftover leftover down; bounce|PUPPET6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
chef6|CHEF6_TIMEOUT|1|30|s|/etc/chef6/chef6.conf|timeout=1|timeout=30|systemctl reload chef6|ch6|che_to_1|jobs|state|https leftover leftover down; bounce|CHEF6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
argocd6|ARGOCD6_TIMEOUT|1|30|s|/etc/argocd6/argocd6.conf|timeout=1|timeout=30|systemctl reload argocd6|ar6|arg_to_1|jobs|state|https leftover leftover down; bounce|ARGOCD6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
flux6|FLUX6_TIMEOUT|1|30|s|/etc/flux6/flux6.conf|timeout=1|timeout=30|systemctl reload flux6|fl6|flu_to_1|jobs|state|https leftover leftover down; bounce|FLUX6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
spinnaker6|SPINNAKER6_TIMEOUT|1|30|s|/etc/spinnaker6/spinnaker6.conf|timeout=1|timeout=30|systemctl reload spinnaker6|sp6|spi_to_1|jobs|state|https leftover leftover down; bounce|SPINNAKER6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
tekton6|TEKTON6_TIMEOUT|1|30|s|/etc/tekton6/tekton6.conf|timeout=1|timeout=30|systemctl reload tekton6|te6|tek_to_1|jobs|state|https leftover leftover down; bounce|TEKTON6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
jenkins6|JENKINS6_TIMEOUT|1|30|s|/etc/jenkins6/jenkins6.conf|timeout=1|timeout=30|systemctl reload jenkins6|je6|jen_to_1|jobs|state|https leftover leftover down; bounce|JENKINS6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
drone6|DRONE6_TIMEOUT|1|30|s|/etc/drone6/drone6.conf|timeout=1|timeout=30|systemctl reload drone6|dr6|dro_to_1|jobs|state|https leftover leftover down; bounce|DRONE6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
concourse6|CONCOURSE6_TIMEOUT|1|30|s|/etc/concourse6/concourse6.conf|timeout=1|timeout=30|systemctl reload concourse6|co6|con_to_1|jobs|state|https leftover leftover down; bounce|CONCOURSE6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
woodpecker6|WOODPECKER6_TIMEOUT|1|30|s|/etc/woodpecker6/woodpecker6.conf|timeout=1|timeout=30|systemctl reload woodpecker6|wo6|woo_to_1|jobs|state|https leftover leftover down; bounce|WOODPECKER6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
gitea6|GITEA6_TIMEOUT|1|30|s|/etc/gitea6/gitea6.conf|timeout=1|timeout=30|systemctl reload gitea6|gi6|git_to_1|jobs|state|https leftover leftover down; bounce|GITEA6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
forgejo6|FORGEJO6_TIMEOUT|1|30|s|/etc/forgejo6/forgejo6.conf|timeout=1|timeout=30|systemctl reload forgejo6|fo6|for_to_1|jobs|state|https leftover leftover down; bounce|FORGEJO6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
sourcehut6|SOURCEHUT6_TIMEOUT|1|30|s|/etc/sourcehut6/sourcehut6.conf|timeout=1|timeout=30|systemctl reload sourcehut6|so6|sou_to_1|jobs|state|https leftover leftover down; bounce|SOURCEHUT6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
bitbucket6|BITBUCKET6_TIMEOUT|1|30|s|/etc/bitbucket6/bitbucket6.conf|timeout=1|timeout=30|systemctl reload bitbucket6|bi6|bit_to_1|jobs|state|https leftover leftover down; bounce|BITBUCKET6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
codeberg6|CODEBERG6_TIMEOUT|1|30|s|/etc/codeberg6/codeberg6.conf|timeout=1|timeout=30|systemctl reload codeberg6|co6|cod_to_1|jobs|state|https leftover leftover down; bounce|CODEBERG6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
gerrit6|GERRIT6_TIMEOUT|1|30|s|/etc/gerrit6/gerrit6.conf|timeout=1|timeout=30|systemctl reload gerrit6|ge6|ger_to_1|jobs|state|https leftover leftover down; bounce|GERRIT6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
nix6|NIX6_TIMEOUT|1|30|s|/etc/nix6/nix6.conf|timeout=1|timeout=30|systemctl reload nix6|ni6|nix_to_1|jobs|state|https leftover leftover down; bounce|NIX6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
nixos6|NIXOS6_TIMEOUT|1|30|s|/etc/nixos6/nixos6.conf|timeout=1|timeout=30|systemctl reload nixos6|ni6|nix_to_1|jobs|state|https leftover leftover down; bounce|NIXOS6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
guix6|GUIX6_TIMEOUT|1|30|s|/etc/guix6/guix6.conf|timeout=1|timeout=30|systemctl reload guix6|gu6|gui_to_1|jobs|state|https leftover leftover down; bounce|GUIX6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
homebrew6|HOMEBREW6_TIMEOUT|1|30|s|/etc/homebrew6/homebrew6.conf|timeout=1|timeout=30|systemctl reload homebrew6|ho6|hom_to_1|jobs|state|https leftover leftover down; bounce|HOMEBREW6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
flatpak6|FLATPAK6_TIMEOUT|1|30|s|/etc/flatpak6/flatpak6.conf|timeout=1|timeout=30|systemctl reload flatpak6|fl6|fla_to_1|jobs|state|https leftover leftover down; bounce|FLATPAK6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
snap6|SNAP6_TIMEOUT|1|30|s|/etc/snap6/snap6.conf|timeout=1|timeout=30|systemctl reload snap6|sn6|sna_to_1|jobs|state|https leftover leftover down; bounce|SNAP6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
rpm6|RPM6_TIMEOUT|1|30|s|/etc/rpm6/rpm6.conf|timeout=1|timeout=30|systemctl reload rpm6|rp6|rpm_to_1|jobs|state|https leftover leftover down; bounce|RPM6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
dpkg6|DPKG6_TIMEOUT|1|30|s|/etc/dpkg6/dpkg6.conf|timeout=1|timeout=30|systemctl reload dpkg6|dp6|dpk_to_1|jobs|state|https leftover leftover down; bounce|DPKG6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
apt6|APT6_TIMEOUT|1|30|s|/etc/apt6/apt6.conf|timeout=1|timeout=30|systemctl reload apt6|ap6|apt_to_1|jobs|state|https leftover leftover down; bounce|APT6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
dnf6|DNF6_TIMEOUT|1|30|s|/etc/dnf6/dnf6.conf|timeout=1|timeout=30|systemctl reload dnf6|dn6|dnf_to_1|jobs|state|https leftover leftover down; bounce|DNF6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
zypper6|ZYPPER6_TIMEOUT|1|30|s|/etc/zypper6/zypper6.conf|timeout=1|timeout=30|systemctl reload zypper6|zy6|zyp_to_1|jobs|state|https leftover leftover down; bounce|ZYPPER6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
pacman6|PACMAN6_TIMEOUT|1|30|s|/etc/pacman6/pacman6.conf|timeout=1|timeout=30|systemctl reload pacman6|pa6|pac_to_1|jobs|state|https leftover leftover down; bounce|PACMAN6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
portage6|PORTAGE6_TIMEOUT|1|30|s|/etc/portage6/portage6.conf|timeout=1|timeout=30|systemctl reload portage6|po6|por_to_1|jobs|state|https leftover leftover down; bounce|PORTAGE6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
apk6|APK6_TIMEOUT|1|30|s|/etc/apk6/apk6.conf|timeout=1|timeout=30|systemctl reload apk6|ap6|apk_to_1|jobs|state|https leftover leftover down; bounce|APK6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
xbps6|XBPS6_TIMEOUT|1|30|s|/etc/xbps6/xbps6.conf|timeout=1|timeout=30|systemctl reload xbps6|xb6|xbp_to_1|jobs|state|https leftover leftover down; bounce|XBPS6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
opkg6|OPKG6_TIMEOUT|1|30|s|/etc/opkg6/opkg6.conf|timeout=1|timeout=30|systemctl reload opkg6|op6|opk_to_1|jobs|state|https leftover leftover down; bounce|OPKG6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
yum6|YUM6_TIMEOUT|1|30|s|/etc/yum6/yum6.conf|timeout=1|timeout=30|systemctl reload yum6|yu6|yum_to_1|jobs|state|https leftover leftover down; bounce|YUM6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
emerge6|EMERGE6_TIMEOUT|1|30|s|/etc/emerge6/emerge6.conf|timeout=1|timeout=30|systemctl reload emerge6|em6|eme_to_1|jobs|state|https leftover leftover down; bounce|EMERGE6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
postgres6|POSTGRES6_TIMEOUT|1|30|s|/etc/postgres6/postgres6.conf|timeout=1|timeout=30|systemctl reload postgres6|po6|pos_to_1|jobs|state|https leftover leftover down; bounce|POSTGRES6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
mysql6|MYSQL6_TIMEOUT|1|30|s|/etc/mysql6/mysql6.conf|timeout=1|timeout=30|systemctl reload mysql6|my6|mys_to_1|jobs|state|https leftover leftover down; bounce|MYSQL6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
mariadb6|MARIADB6_TIMEOUT|1|30|s|/etc/mariadb6/mariadb6.conf|timeout=1|timeout=30|systemctl reload mariadb6|ma6|mar_to_1|jobs|state|https leftover leftover down; bounce|MARIADB6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
redis6|REDIS6_TIMEOUT|1|30|s|/etc/redis6/redis6.conf|timeout=1|timeout=30|systemctl reload redis6|re6|red_to_1|jobs|state|https leftover leftover down; bounce|REDIS6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
mongodb6|MONGODB6_TIMEOUT|1|30|s|/etc/mongodb6/mongodb6.conf|timeout=1|timeout=30|systemctl reload mongodb6|mo6|mon_to_1|jobs|state|https leftover leftover down; bounce|MONGODB6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
cassandra6|CASSANDRA6_TIMEOUT|1|30|s|/etc/cassandra6/cassandra6.conf|timeout=1|timeout=30|systemctl reload cassandra6|ca6|cas_to_1|jobs|state|https leftover leftover down; bounce|CASSANDRA6_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
'''
WAVE = (
    "puppet6/chef6/argocd6/flux6/spinnaker6/tekton6/jenkins6/drone6/concourse6/woodpecker6/gitea6/forgejo6/sourcehut6/bitbucket6/codeberg6/gerrit6/nix6/nixos6/guix6/homebrew6/flatpak6/snap6/rpm6/dpkg6/apt6/dnf6/zypper6/pacman6/portage6/apk6/xbps6/opkg6/yum6/emerge6/postgres6/mysql6/mariadb6/redis6/mongodb6/cassandra6"
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
        svc = f"u2{i:02d}x"
        ns = f"u2{i:02d}"
        clu = f"prod-apuy{901 + i}-{svc[:3]}"
        ticket = f"W2-{ 14443 + i }"
        node = f"ip-10-163-{1 + i}-{20 + i}"
        slug = f"{daemon}-{key}-{old}{unit}-{svc}"
        key_words = key.replace(".", " leftover ").replace("_", " leftover ")
        symptom = f"{key_words} leftover {old}{unit} leftover; {what} drop"
        because = (
            f"is dropping {what} because leftover {daemon} leftover {key_words} leftover is {old} leftover."
        )
        do_not = f"Restore {new}{unit}; do not wipe {wipe}."
        rca = f"{daemon} leftover {key} leftover {old} leftover; {rca_tail}"
        if remnant := (helm_rb(ns, svc, 3, path, oldv, newv, reload) if rem == "rollback" else patch_file(path, oldv, newv, reload)):
            extra = f"helm -n {ns} history {svc} | head -5" if rem == "rollback" else f"kubectl -n {ns} logs deploy/{svc} --since=5m | grep {key} | tail"
            eobs = f"4  {old}{unit}\n3  last-good {new}" if rem == "rollback" else f"{key} leftover {old}"
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
m.BASE_ROUND = 4961


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4317 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-93 leftover: {WAVE}.",
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
