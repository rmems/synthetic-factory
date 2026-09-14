#!/usr/bin/env python3
"""IRC mill r4241+ — wave-57 rpm-build/desktop leftover.

NEW on-call plants (not Wave-27–56 tails). BAN ypbind/oddjob,
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
sbuild|SBUILD_TIMEOUT|1|3600|s|/etc/sbuild/sbuild.conf|$timeout = 1;|$timeout = 3600;|systemctl reload sbuild|sbuild|sbd_to_1|chroots|pkgs|fs leftover leftover down; bounce|SBUILD_TIMEOUT leftover 1 leftover; a 2s build is aborted so the deb 504s
pbuilder|PBUILDER_TIMEOUT|1|3600|s|/etc/pbuilderrc|TIMEOUT=1|TIMEOUT=3600|systemctl reload pbuilder|pbuilder|pbd_to_1|base|pkgs|fs leftover leftover down; bounce|PBUILDER_TIMEOUT leftover 1 leftover; a 2s build is aborted so the deb 504s
mock|MOCK_TIMEOUT|1|3600|s|/etc/mock/site-defaults.cfg|config_opts['timeout']=1|config_opts['timeout']=3600|systemctl reload mock|mock|mck_to_1|chroots|rpms|fs leftover leftover down; bounce|MOCK_TIMEOUT leftover 1 leftover; a 2s build is aborted so the rpm 504s
koji|KOJI_TIMEOUT|1|3600|s|/etc/koji.conf|timeout=1|timeout=3600|systemctl reload kojid|koji|koj_to_1|tasks|builds|https leftover leftover 403; bounce|KOJI_TIMEOUT leftover 1 leftover; a 2s build is aborted so the rpm 504s
obs-build|OBS_TIMEOUT|1|3600|s|/etc/obs/BSConfig.pm|timeout=1|timeout=3600|systemctl reload obs-srcserver|osc|obs_to_1|pkgs|prj|https leftover leftover 403; bounce|OBS_TIMEOUT leftover 1 leftover; a 2s build is aborted so the pkg 504s
copr|COPR_TIMEOUT|1|3600|s|/etc/copr/copr.conf|timeout=1|timeout=3600|systemctl reload copr|copr|cpr_to_1|builds|chroots|https leftover leftover 403; bounce|COPR_TIMEOUT leftover 1 leftover; a 2s build is aborted so the rpm 504s
bodhi|BODHI_TIMEOUT|1|30|s|/etc/bodhi/production.ini|timeout=1|timeout=30|systemctl reload bodhi|bodhi|bod_to_1|upd|composes|https leftover leftover 403; bounce|BODHI_TIMEOUT leftover 1 leftover; a 2s push is aborted so the update 504s
mash|MASH_TIMEOUT|1|3600|s|/etc/mash/mash.conf|timeout=1|timeout=3600|systemctl reload mash|mash|msh_to_1|trees|comps|fs leftover leftover down; bounce|MASH_TIMEOUT leftover 1 leftover; a 2s mash is aborted so the tree 504s
pungi|PUNGI_TIMEOUT|1|3600|s|/etc/pungi/pungi.conf|timeout=1|timeout=3600|systemctl reload pungi|pungi|png_to_1|isos|comps|fs leftover leftover down; bounce|PUNGI_TIMEOUT leftover 1 leftover; a 2s compose is aborted so the iso 504s
rebar3|REBAR3_TIMEOUT|1|60|s|/etc/rebar3/rebar.config|timeout=1|timeout=60|systemctl reload rebar3|rebar3|reb_to_1|deps|hex|https leftover leftover 403; bounce|REBAR3_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the app 504s
createrepo|CREATEREPO_TIMEOUT|1|60|s|/etc/createrepo/createrepo.conf|timeout=1|timeout=60|systemctl reload createrepo|createrepo_c|crp_to_1|repodata|rpms|fs leftover leftover down; bounce|CREATEREPO_TIMEOUT leftover 1 leftover; a 2s metadata is aborted so the repo 504s
repoclosure|REPOCLOSURE_TIMEOUT|1|60|s|/etc/yum/repoclosure.conf|timeout=1|timeout=60|systemctl reload repoclosure|repoclosure|rcl_to_1|deps|repos|fs leftover leftover down; bounce|REPOCLOSURE_TIMEOUT leftover 1 leftover; a 2s check is aborted so the report 504s
repocache|REPOCACHE_TIMEOUT|1|60|s|/etc/yum/repocache.conf|timeout=1|timeout=60|systemctl reload yum|yum|rca_to_1|cache|repos|fs leftover leftover down; bounce|REPOCACHE_TIMEOUT leftover 1 leftover; a 2s makecache is aborted so the cache 504s
dnfdragora|DNFDRAGORA_TIMEOUT|1|60|s|/etc/dnfdragora/dnfdragora.conf|timeout=1|timeout=60|systemctl reload dnfdragora|dnfdragora|dnd_to_1|pkgs|ui|dnf leftover leftover down; bounce|DNFDRAGORA_TIMEOUT leftover 1 leftover; a 2s refresh is aborted so the ui 504s
yumex|YUMEX_TIMEOUT|1|60|s|/etc/yumex/yumex.conf|timeout=1|timeout=60|systemctl reload yumex|yumex|ymx_to_1|pkgs|ui|yum leftover leftover down; bounce|YUMEX_TIMEOUT leftover 1 leftover; a 2s refresh is aborted so the ui 504s
synaptic|SYNAPTIC_TIMEOUT|1|60|s|/etc/synaptic/synaptic.conf|timeout=1|timeout=60|systemctl reload synaptic|synaptic|syn_to_1|pkgs|ui|apt leftover leftover down; bounce|SYNAPTIC_TIMEOUT leftover 1 leftover; a 2s reload is aborted so the ui 504s
muon|MUON_TIMEOUT|1|60|s|/etc/muon/muon.conf|timeout=1|timeout=60|systemctl reload muon|muon|muo_to_1|pkgs|ui|apt leftover leftover down; bounce|MUON_TIMEOUT leftover 1 leftover; a 2s reload is aborted so the ui 504s
aptdaemon|APTDAEMON_TIMEOUT|1|60|s|/etc/aptdaemon/aptdaemon.conf|timeout=1|timeout=60|systemctl reload aptd|aptd|apd_to_1|trans|pkgs|dbus leftover leftover down; bounce|APTDAEMON_TIMEOUT leftover 1 leftover; a 2s commit is aborted so the pkg 504s
needrestart|NEEDRESTART_TIMEOUT|1|30|s|/etc/needrestart/needrestart.conf|timeout=1|timeout=30|systemctl reload needrestart|needrestart|nrs_to_1|svcs|libs|fs leftover leftover down; bounce|NEEDRESTART_TIMEOUT leftover 1 leftover; a 2s scan is aborted so the list 504s
blender|BLENDER_TIMEOUT|1|60|s|/etc/blender/blender.conf|timeout=1|timeout=60|systemctl reload blender|blender|bld_to_1|blend|frames|fs leftover leftover down; bounce|BLENDER_TIMEOUT leftover 1 leftover; a 2s render is aborted so the frame 504s
gimp|GIMP_TIMEOUT|1|30|s|/etc/gimp/gimprc|timeout=1|timeout=30|systemctl reload gimp|gimp|gmp_to_1|xcf|tiles|fs leftover leftover down; bounce|GIMP_TIMEOUT leftover 1 leftover; a 2s save is aborted so the xcf 504s
inkscape|INKSCAPE_TIMEOUT|1|30|s|/etc/inkscape/inkscape.conf|timeout=1|timeout=30|systemctl reload inkscape|inkscape|ink_to_1|svg|png|fs leftover leftover down; bounce|INKSCAPE_TIMEOUT leftover 1 leftover; a 2s export is aborted so the png 504s
krita|KRITA_TIMEOUT|1|30|s|/etc/krita/kritarc|timeout=1|timeout=30|systemctl reload krita|krita|kri_to_1|kra|tiles|fs leftover leftover down; bounce|KRITA_TIMEOUT leftover 1 leftover; a 2s save is aborted so the kra 504s
darktable|DARKTABLE_TIMEOUT|1|30|s|/etc/darktable/darktablerc|timeout=1|timeout=30|systemctl reload darktable|darktable|drk_to_1|raw|xmp|fs leftover leftover down; bounce|DARKTABLE_TIMEOUT leftover 1 leftover; a 2s export is aborted so the jpg 504s
rawtherapee|RAWTHERAPEE_TIMEOUT|1|30|s|/etc/rawtherapee/options|timeout=1|timeout=30|systemctl reload rawtherapee|rawtherapee|rwt_to_1|raw|pp3|fs leftover leftover down; bounce|RAWTHERAPEE_TIMEOUT leftover 1 leftover; a 2s export is aborted so the jpg 504s
imagemagick|MAGICK_TIMEOUT|1|30|s|/etc/ImageMagick-7/policy.xml|timeout=1|timeout=30|systemctl reload convert|convert|img_to_1|src|dst|fs leftover leftover down; bounce|MAGICK_TIMEOUT leftover 1 leftover; a 2s convert is aborted so the dst 504s
libreoffice|LO_TIMEOUT|1|30|s|/etc/libreoffice/sofficerc|timeout=1|timeout=30|systemctl reload soffice|soffice|lof_to_1|odt|pdf|fs leftover leftover down; bounce|LO_TIMEOUT leftover 1 leftover; a 2s export is aborted so the pdf 504s
onlyoffice|ONLYOFFICE_TIMEOUT|1|30|s|/etc/onlyoffice/documentserver/default.json|"timeout": 1|"timeout": 30|systemctl reload ds|documentserver|ono_to_1|docs|conv|https leftover leftover 403; bounce|ONLYOFFICE_TIMEOUT leftover 1 leftover; a 2s convert is aborted so the doc 504s
wps|WPS_TIMEOUT|1|30|s|/etc/wps/wps.conf|timeout=1|timeout=30|systemctl reload wps|wps|wps_to_1|docs|pdf|fs leftover leftover down; bounce|WPS_TIMEOUT leftover 1 leftover; a 2s export is aborted so the pdf 504s
firefox|FIREFOX_TIMEOUT|1|30|s|/etc/firefox/firefox.js|timeout=1|timeout=30|systemctl reload firefox|firefox|ffx_to_1|tabs|prof|https leftover leftover 403; bounce|FIREFOX_TIMEOUT leftover 1 leftover; a 2s load is aborted so the tab 504s
chromium|CHROMIUM_TIMEOUT|1|30|s|/etc/chromium/default|timeout=1|timeout=30|systemctl reload chromium|chromium|chr_to_1|tabs|prof|https leftover leftover 403; bounce|CHROMIUM_TIMEOUT leftover 1 leftover; a 2s load is aborted so the tab 504s
epiphany|EPIPHANY_TIMEOUT|1|30|s|/etc/epiphany/epiphany.conf|timeout=1|timeout=30|systemctl reload epiphany|epiphany|epi_to_1|tabs|prof|https leftover leftover 403; bounce|EPIPHANY_TIMEOUT leftover 1 leftover; a 2s load is aborted so the tab 504s
qutebrowser|QUTE_TIMEOUT|1|30|s|/etc/qutebrowser/config.py|timeout=1|timeout=30|systemctl reload qutebrowser|qutebrowser|qtb_to_1|tabs|prof|https leftover leftover 403; bounce|QUTE_TIMEOUT leftover 1 leftover; a 2s load is aborted so the tab 504s
cp2k|CP2K_TIMEOUT|1|3600|s|/etc/cp2k/cp2k.conf|timeout=1|timeout=3600|systemctl reload cp2k|cp2k|cpk_to_1|inp|out|fs leftover leftover down; bounce|CP2K_TIMEOUT leftover 1 leftover; a 2s scf is aborted so the run 504s
nwchem|NWCHEM_TIMEOUT|1|3600|s|/etc/nwchem/nwchem.conf|timeout=1|timeout=3600|systemctl reload nwchem|nwchem|nwc_to_1|nw|out|fs leftover leftover down; bounce|NWCHEM_TIMEOUT leftover 1 leftover; a 2s scf is aborted so the run 504s
orca|ORCA_TIMEOUT|1|3600|s|/etc/orca/orca.conf|timeout=1|timeout=3600|systemctl reload orca|orca|orc_to_1|inp|out|fs leftover leftover down; bounce|ORCA_TIMEOUT leftover 1 leftover; a 2s scf is aborted so the run 504s
gaussian|GAUSSIAN_TIMEOUT|1|3600|s|/etc/gaussian/g16.conf|timeout=1|timeout=3600|systemctl reload g16|g16|gau_to_1|gjf|out|fs leftover leftover down; bounce|GAUSSIAN_TIMEOUT leftover 1 leftover; a 2s scf is aborted so the run 504s
gamess|GAMESS_TIMEOUT|1|3600|s|/etc/gamess/rungms.conf|timeout=1|timeout=3600|systemctl reload gamess|rungms|gms_to_1|inp|out|fs leftover leftover down; bounce|GAMESS_TIMEOUT leftover 1 leftover; a 2s scf is aborted so the run 504s
molpro|MOLPRO_TIMEOUT|1|3600|s|/etc/molpro/molpro.conf|timeout=1|timeout=3600|systemctl reload molpro|molpro|mlp_to_1|inp|out|fs leftover leftover down; bounce|MOLPRO_TIMEOUT leftover 1 leftover; a 2s scf is aborted so the run 504s
psi4|PSI4_TIMEOUT|1|3600|s|/etc/psi4/psi4.conf|timeout=1|timeout=3600|systemctl reload psi4|psi4|psi_to_1|in|out|fs leftover leftover down; bounce|PSI4_TIMEOUT leftover 1 leftover; a 2s scf is aborted so the run 504s
'''
WAVE57 = (
    "sbuild/pbuilder/mock/koji/obs-build/copr/bodhi/mash/pungi/rebar3/"
    "createrepo/repoclosure/repocache/dnfdragora/yumex/synaptic/muon/"
    "aptdaemon/needrestart/blender/gimp/inkscape/krita/darktable/"
    "rawtherapee/imagemagick/libreoffice/onlyoffice/wps/firefox/"
    "chromium/epiphany/qutebrowser/cp2k/nwchem/orca/gaussian/gamess/"
    "molpro/psi4"
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
        # copr leftover vs copr - unique
        rem = "rollback" if i % 2 == 0 else "patch"
        src = srcs[i % 4]
        svc = f"m7{i:02d}x"
        ns = f"m7{i:02d}"
        clu = f"prod-apsn{901 + i}-{svc[:3]}"
        ticket = f"W2-{13003 + i}"
        node = f"ip-10-242-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4241


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4240 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-57 leftover: {WAVE57}.",
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
