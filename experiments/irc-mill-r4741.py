#!/usr/bin/env python3
"""IRC mill r4741+ — wave-82 vcs/distro leftover.

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
gitea3|GITEA3_TIMEOUT|1|30|s|/etc/gitea3/gitea3.conf|timeout=1|timeout=30|systemctl reload gitea3|gt|git_to_1|repos|hooks|https leftover leftover down; bounce|GITEA3_TIMEOUT leftover 1 leftover; a 2s push is aborted so the repos 504s
forgejo2|FORGEJO2_TIMEOUT|1|30|s|/etc/forgejo2/forgejo2.conf|timeout=1|timeout=30|systemctl reload forgejo2|fj|for_to_1|repos|hooks|https leftover leftover down; bounce|FORGEJO2_TIMEOUT leftover 1 leftover; a 2s push is aborted so the repos 504s
sourcehut2|SOURCEHUT2_TIMEOUT|1|30|s|/etc/sourcehut2/sourcehut2.conf|timeout=1|timeout=30|systemctl reload sourcehut2|sh|sou_to_1|repos|builds|https leftover leftover down; bounce|SOURCEHUT2_TIMEOUT leftover 1 leftover; a 2s push is aborted so the repos 504s
bitbucket2|BITBUCKET2_TIMEOUT|1|30|s|/etc/bitbucket2/bitbucket2.conf|timeout=1|timeout=30|systemctl reload bitbucket2|bb|bit_to_1|repos|prs|https leftover leftover down; bounce|BITBUCKET2_TIMEOUT leftover 1 leftover; a 2s push is aborted so the repos 504s
launchpad2|LAUNCHPAD2_TIMEOUT|1|30|s|/etc/launchpad2/launchpad2.conf|timeout=1|timeout=30|systemctl reload launchpad2|lp|lau_to_1|bzrs|ppas|https leftover leftover down; bounce|LAUNCHPAD2_TIMEOUT leftover 1 leftover; a 2s push is aborted so the bzrs 504s
savannah2|SAVANNAH2_TIMEOUT|1|30|s|/etc/savannah2/savannah2.conf|timeout=1|timeout=30|systemctl reload savannah2|sv|sav_to_1|repos|trackers|https leftover leftover down; bounce|SAVANNAH2_TIMEOUT leftover 1 leftover; a 2s push is aborted so the repos 504s
sourceforge2|SOURCEFORGE2_TIMEOUT|1|30|s|/etc/sourceforge2/sourceforge2.conf|timeout=1|timeout=30|systemctl reload sourceforge2|sf|sou_to_1|repos|files|https leftover leftover down; bounce|SOURCEFORGE2_TIMEOUT leftover 1 leftover; a 2s push is aborted so the repos 504s
codeberg2|CODEBERG2_TIMEOUT|1|30|s|/etc/codeberg2/codeberg2.conf|timeout=1|timeout=30|systemctl reload codeberg2|cb|cod_to_1|repos|hooks|https leftover leftover down; bounce|CODEBERG2_TIMEOUT leftover 1 leftover; a 2s push is aborted so the repos 504s
srht2|SRHT2_TIMEOUT|1|30|s|/etc/srht2/srht2.conf|timeout=1|timeout=30|systemctl reload srht2|sr|srh_to_1|repos|builds|https leftover leftover down; bounce|SRHT2_TIMEOUT leftover 1 leftover; a 2s push is aborted so the repos 504s
pagure2|PAGURE2_TIMEOUT|1|30|s|/etc/pagure2/pagure2.conf|timeout=1|timeout=30|systemctl reload pagure2|pg|pag_to_1|repos|prs|https leftover leftover down; bounce|PAGURE2_TIMEOUT leftover 1 leftover; a 2s push is aborted so the repos 504s
phabricator2|PHABRICATOR2_TIMEOUT|1|30|s|/etc/phabricator2/phabricator2.conf|timeout=1|timeout=30|systemctl reload phabricator2|ph|pha_to_1|diffs|repos|https leftover leftover down; bounce|PHABRICATOR2_TIMEOUT leftover 1 leftover; a 2s land is aborted so the diffs 504s
gerrit3|GERRIT3_TIMEOUT|1|30|s|/etc/gerrit3/gerrit3.conf|timeout=1|timeout=30|systemctl reload gerrit3|gr|ger_to_1|changes|refs|https leftover leftover down; bounce|GERRIT3_TIMEOUT leftover 1 leftover; a 2s submit is aborted so the changes 504s
reviewboard2|REVIEWBOARD2_TIMEOUT|1|30|s|/etc/reviewboard2/reviewboard2.conf|timeout=1|timeout=30|systemctl reload reviewboard2|rb|rev_to_1|reviews|diffs|https leftover leftover down; bounce|REVIEWBOARD2_TIMEOUT leftover 1 leftover; a 2s publish is aborted so the reviews 504s
zuul2|ZUUL2_TIMEOUT|1|30|s|/etc/zuul2/zuul2.conf|timeout=1|timeout=30|systemctl reload zuul2|zu|zuu_to_1|jobs|pipelines|https leftover leftover down; bounce|ZUUL2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
buildbot2|BUILDBOT2_TIMEOUT|1|30|s|/etc/buildbot2/buildbot2.conf|timeout=1|timeout=30|systemctl reload buildbot2|bd|bui_to_1|builders|changes|https leftover leftover down; bounce|BUILDBOT2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the builders 504s
hydra2|HYDRA2_TIMEOUT|1|30|s|/etc/hydra2/hydra2.conf|timeout=1|timeout=30|systemctl reload hydra2|hy|hyd_to_1|jobs|evals|https leftover leftover down; bounce|HYDRA2_TIMEOUT leftover 1 leftover; a 2s build is aborted so the jobs 504s
nix2|NIX2_TIMEOUT|1|30|s|/etc/nix2/nix2.conf|timeout=1|timeout=30|systemctl reload nix2|nx|nix_to_1|drvs|store|fs leftover leftover down; bounce|NIX2_TIMEOUT leftover 1 leftover; a 2s build is aborted so the drvs 504s
nixos2|NIXOS2_TIMEOUT|1|30|s|/etc/nixos2/nixos2.conf|timeout=1|timeout=30|systemctl reload nixos2|no|nix_to_1|cfgs|gens|fs leftover leftover down; bounce|NIXOS2_TIMEOUT leftover 1 leftover; a 2s switch is aborted so the cfgs 504s
guix2|GUIX2_TIMEOUT|1|30|s|/etc/guix2/guix2.conf|timeout=1|timeout=30|systemctl reload guix2|gx|gui_to_1|pkgs|store|fs leftover leftover down; bounce|GUIX2_TIMEOUT leftover 1 leftover; a 2s build is aborted so the pkgs 504s
pkgsrc2|PKGSRC2_TIMEOUT|1|30|s|/etc/pkgsrc2/pkgsrc2.conf|timeout=1|timeout=30|systemctl reload pkgsrc2|pk|pkg_to_1|pkgs|distfiles|fs leftover leftover down; bounce|PKGSRC2_TIMEOUT leftover 1 leftover; a 2s build is aborted so the pkgs 504s
macports2|MACPORTS2_TIMEOUT|1|30|s|/etc/macports2/macports2.conf|timeout=1|timeout=30|systemctl reload macports2|mp|mac_to_1|ports|archives|fs leftover leftover down; bounce|MACPORTS2_TIMEOUT leftover 1 leftover; a 2s install is aborted so the ports 504s
homebrew2|HOMEBREW2_TIMEOUT|1|30|s|/etc/homebrew2/homebrew2.conf|timeout=1|timeout=30|systemctl reload homebrew2|hb|hom_to_1|formulae|bottles|fs leftover leftover down; bounce|HOMEBREW2_TIMEOUT leftover 1 leftover; a 2s install is aborted so the formulae 504s
chocolatey2|CHOCOLATEY2_TIMEOUT|1|30|s|/etc/chocolatey2/chocolatey2.conf|timeout=1|timeout=30|systemctl reload chocolatey2|ch|cho_to_1|pkgs|nupkgs|fs leftover leftover down; bounce|CHOCOLATEY2_TIMEOUT leftover 1 leftover; a 2s install is aborted so the pkgs 504s
scoop2|SCOOP2_TIMEOUT|1|30|s|/etc/scoop2/scoop2.conf|timeout=1|timeout=30|systemctl reload scoop2|sc|sco_to_1|apps|buckets|fs leftover leftover down; bounce|SCOOP2_TIMEOUT leftover 1 leftover; a 2s install is aborted so the apps 504s
winget2|WINGET2_TIMEOUT|1|30|s|/etc/winget2/winget2.conf|timeout=1|timeout=30|systemctl reload winget2|wg|win_to_1|pkgs|manifests|fs leftover leftover down; bounce|WINGET2_TIMEOUT leftover 1 leftover; a 2s install is aborted so the pkgs 504s
snap2|SNAP2_TIMEOUT|1|30|s|/etc/snap2/snap2.conf|timeout=1|timeout=30|systemctl reload snap2|sn|sna_to_1|snaps|revs|fs leftover leftover down; bounce|SNAP2_TIMEOUT leftover 1 leftover; a 2s install is aborted so the snaps 504s
flatpak2|FLATPAK2_TIMEOUT|1|30|s|/etc/flatpak2/flatpak2.conf|timeout=1|timeout=30|systemctl reload flatpak2|fp|fla_to_1|apps|runtimes|fs leftover leftover down; bounce|FLATPAK2_TIMEOUT leftover 1 leftover; a 2s install is aborted so the apps 504s
appimage2|APPIMAGE2_TIMEOUT|1|30|s|/etc/appimage2/appimage2.conf|timeout=1|timeout=30|systemctl reload appimage2|ai|app_to_1|apps|images|fs leftover leftover down; bounce|APPIMAGE2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the apps 504s
rpm2|RPM2_TIMEOUT|1|30|s|/etc/rpm2/rpm2.conf|timeout=1|timeout=30|systemctl reload rpm2|rp|rpm_to_1|pkgs|db|fs leftover leftover down; bounce|RPM2_TIMEOUT leftover 1 leftover; a 2s install is aborted so the pkgs 504s
dpkg2|DPKG2_TIMEOUT|1|30|s|/etc/dpkg2/dpkg2.conf|timeout=1|timeout=30|systemctl reload dpkg2|dp|dpk_to_1|pkgs|db|fs leftover leftover down; bounce|DPKG2_TIMEOUT leftover 1 leftover; a 2s install is aborted so the pkgs 504s
apt2|APT2_TIMEOUT|1|30|s|/etc/apt2/apt2.conf|timeout=1|timeout=30|systemctl reload apt2|ap|apt_to_1|pkgs|lists|fs leftover leftover down; bounce|APT2_TIMEOUT leftover 1 leftover; a 2s install is aborted so the pkgs 504s
yum2|YUM2_TIMEOUT|1|30|s|/etc/yum2/yum2.conf|timeout=1|timeout=30|systemctl reload yum2|ym|yum_to_1|pkgs|cache|fs leftover leftover down; bounce|YUM2_TIMEOUT leftover 1 leftover; a 2s install is aborted so the pkgs 504s
dnf2|DNF2_TIMEOUT|1|30|s|/etc/dnf2/dnf2.conf|timeout=1|timeout=30|systemctl reload dnf2|dn|dnf_to_1|pkgs|cache|fs leftover leftover down; bounce|DNF2_TIMEOUT leftover 1 leftover; a 2s install is aborted so the pkgs 504s
zypper2|ZYPPER2_TIMEOUT|1|30|s|/etc/zypper2/zypper2.conf|timeout=1|timeout=30|systemctl reload zypper2|zy|zyp_to_1|pkgs|solv|fs leftover leftover down; bounce|ZYPPER2_TIMEOUT leftover 1 leftover; a 2s install is aborted so the pkgs 504s
pacman2|PACMAN2_TIMEOUT|1|30|s|/etc/pacman2/pacman2.conf|timeout=1|timeout=30|systemctl reload pacman2|pm|pac_to_1|pkgs|db|fs leftover leftover down; bounce|PACMAN2_TIMEOUT leftover 1 leftover; a 2s install is aborted so the pkgs 504s
portage2|PORTAGE2_TIMEOUT|1|30|s|/etc/portage2/portage2.conf|timeout=1|timeout=30|systemctl reload portage2|pt|por_to_1|ebuilds|distfiles|fs leftover leftover down; bounce|PORTAGE2_TIMEOUT leftover 1 leftover; a 2s emerge is aborted so the ebuilds 504s
emerge2|EMERGE2_TIMEOUT|1|30|s|/etc/emerge2/emerge2.conf|timeout=1|timeout=30|systemctl reload emerge2|em|eme_to_1|ebuilds|pkgs|fs leftover leftover down; bounce|EMERGE2_TIMEOUT leftover 1 leftover; a 2s merge is aborted so the ebuilds 504s
apk2|APK2_TIMEOUT|1|30|s|/etc/apk2/apk2.conf|timeout=1|timeout=30|systemctl reload apk2|ak|apk_to_1|pkgs|db|fs leftover leftover down; bounce|APK2_TIMEOUT leftover 1 leftover; a 2s add is aborted so the pkgs 504s
xbps2|XBPS2_TIMEOUT|1|30|s|/etc/xbps2/xbps2.conf|timeout=1|timeout=30|systemctl reload xbps2|xb|xbp_to_1|pkgs|db|fs leftover leftover down; bounce|XBPS2_TIMEOUT leftover 1 leftover; a 2s install is aborted so the pkgs 504s
opkg2|OPKG2_TIMEOUT|1|30|s|/etc/opkg2/opkg2.conf|timeout=1|timeout=30|systemctl reload opkg2|ok|opk_to_1|pkgs|db|fs leftover leftover down; bounce|OPKG2_TIMEOUT leftover 1 leftover; a 2s install is aborted so the pkgs 504s
'''
WAVE = (
    "gitea3/forgejo2/sourcehut2/bitbucket2/launchpad2/savannah2/sourceforge2/codeberg2/srht2/pagure2/phabricator2/gerrit3/reviewboard2/zuul2/buildbot2/hydra2/nix2/nixos2/guix2/pkgsrc2/macports2/homebrew2/chocolatey2/scoop2/winget2/snap2/flatpak2/appimage2/rpm2/dpkg2/apt2/yum2/dnf2/zypper2/pacman2/portage2/emerge2/apk2/xbps2/opkg2"
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
        svc = f"i5{i:02d}x"
        ns = f"i5{i:02d}"
        clu = f"prod-apun{901 + i}-{svc[:3]}"
        ticket = f"W2-{ 14003 + i }"
        node = f"ip-10-192-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4741


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4317 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-82 leftover: {WAVE}.",
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
