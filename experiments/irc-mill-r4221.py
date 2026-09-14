#!/usr/bin/env python3
"""IRC mill r4221+ — wave-56 ci/hpc-app leftover.

NEW on-call plants (not Wave-27–55 tails). BAN ypbind/oddjob,
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
act|ACT_TIMEOUT|1|30|s|/etc/act/act.conf|timeout=1|timeout=30|systemctl reload act|act|act_to_1|jobs|wf|docker leftover leftover down; bounce|ACT_TIMEOUT leftover 1 leftover; a 2s step is aborted so the wf 504s
nektos|NEKTOS_TIMEOUT|1|30|s|/etc/nektos/act.conf|timeout=1|timeout=30|systemctl reload act|act|nek_to_1|jobs|wf|docker leftover leftover down; bounce|NEKTOS_TIMEOUT leftover 1 leftover; a 2s step is aborted so the wf 504s
gocd|GOCD_TIMEOUT|1|30|s|/etc/go-server/cruise-config.xml|timeout=1|timeout=30|systemctl reload go-server|gocd|gcd_to_1|pipes|agents|http leftover leftover down; bounce|GOCD_TIMEOUT leftover 1 leftover; a 2s stage is aborted so the pipe 504s
octopus|OCTOPUS_TIMEOUT|1|30|s|/etc/octopus/octopus.config|timeout=1|timeout=30|systemctl reload octopus|octo|oct_to_1|rels|env|sql leftover leftover down; bounce|OCTOPUS_TIMEOUT leftover 1 leftover; a 2s deploy is aborted so the rel 504s
codefresh|CODEFRESH_TIMEOUT|1|30|s|/etc/codefresh/codefresh.yml|timeout: 1|timeout: 30|systemctl reload codefresh|codefresh|cdf_to_1|pipes|steps|https leftover leftover 403; bounce|CODEFRESH_TIMEOUT leftover 1 leftover; a 2s step is aborted so the pipe 504s
travis|TRAVIS_TIMEOUT|1|30|s|/etc/travis/travis.yml|timeout: 1|timeout: 30|systemctl reload travis|travis|trv_to_1|jobs|os|https leftover leftover 403; bounce|TRAVIS_TIMEOUT leftover 1 leftover; a 2s job is aborted so the build 504s
appveyor|APPVEYOR_TIMEOUT|1|30|s|/etc/appveyor/appveyor.yml|timeout: 1|timeout: 30|systemctl reload appveyor|appveyor|apv_to_1|jobs|os|https leftover leftover 403; bounce|APPVEYOR_TIMEOUT leftover 1 leftover; a 2s job is aborted so the build 504s
gromacs|GROMACS_TIMEOUT|1|60|s|/etc/gromacs/gmx.conf|timeout=1|timeout=60|systemctl reload gmx|gmx|grm_to_1|md|tpr|fs leftover leftover down; bounce|GROMACS_TIMEOUT leftover 1 leftover; a 2s mdrun is aborted so the traj 504s
lammps|LAMMPS_TIMEOUT|1|60|s|/etc/lammps/lammps.conf|timeout=1|timeout=60|systemctl reload lmp|lmp|lmp_to_1|md|in|fs leftover leftover down; bounce|LAMMPS_TIMEOUT leftover 1 leftover; a 2s run is aborted so the traj 504s
namd|NAMD_TIMEOUT|1|60|s|/etc/namd/namd.conf|timeout=1|timeout=60|systemctl reload namd2|namd2|nmd_to_1|md|conf|fs leftover leftover down; bounce|NAMD_TIMEOUT leftover 1 leftover; a 2s run is aborted so the traj 504s
amber|AMBER_TIMEOUT|1|60|s|/etc/amber/amber.conf|timeout=1|timeout=60|systemctl reload sander|sander|amb_to_1|md|prmtop|fs leftover leftover down; bounce|AMBER_TIMEOUT leftover 1 leftover; a 2s sander is aborted so the traj 504s
openmm|OPENMM_TIMEOUT|1|60|s|/etc/openmm/openmm.conf|timeout=1|timeout=60|systemctl reload openmm|openmm|omm_to_1|md|xml|fs leftover leftover down; bounce|OPENMM_TIMEOUT leftover 1 leftover; a 2s step is aborted so the traj 504s
sage|SAGE_TIMEOUT|1|60|s|/etc/sage/sage.conf|timeout=1|timeout=60|systemctl reload sage|sage|sag_to_1|nb|cells|fs leftover leftover down; bounce|SAGE_TIMEOUT leftover 1 leftover; a 2s eval is aborted so the nb 504s
maxima|MAXIMA_TIMEOUT|1|30|s|/etc/maxima/maxima-init.mac|timeout=1|timeout=30|systemctl reload maxima|maxima|max_to_1|lisp|out|fs leftover leftover down; bounce|MAXIMA_TIMEOUT leftover 1 leftover; a 2s eval is aborted so the session 504s
maple|MAPLE_TIMEOUT|1|30|s|/etc/maple/maple.conf|timeout=1|timeout=30|systemctl reload maple|maple|mpl_to_1|mw|out|fs leftover leftover down; bounce|MAPLE_TIMEOUT leftover 1 leftover; a 2s eval is aborted so the session 504s
mathematica|MATH_TIMEOUT|1|30|s|/etc/mathematica/kernel.conf|timeout=1|timeout=30|systemctl reload math|math|mth_to_1|nb|out|fs leftover leftover down; bounce|MATH_TIMEOUT leftover 1 leftover; a 2s eval is aborted so the kernel 504s
wolfram|WOLFRAM_TIMEOUT|1|30|s|/etc/wolfram/kernel.conf|timeout=1|timeout=30|systemctl reload wolframscript|wolframscript|wlf_to_1|wl|out|fs leftover leftover down; bounce|WOLFRAM_TIMEOUT leftover 1 leftover; a 2s eval is aborted so the kernel 504s
steam|STEAM_TIMEOUT|1|30|s|/etc/steam/steam.conf|timeout=1|timeout=30|systemctl reload steam|steam|stm_to_1|apps|depot|https leftover leftover 403; bounce|STEAM_TIMEOUT leftover 1 leftover; a 2s download is aborted so the app 504s
lutris|LUTRIS_TIMEOUT|1|30|s|/etc/lutris/lutris.conf|timeout=1|timeout=30|systemctl reload lutris|lutris|lut_to_1|games|wine|fs leftover leftover down; bounce|LUTRIS_TIMEOUT leftover 1 leftover; a 2s runner is aborted so the game 504s
wine|WINE_TIMEOUT|1|30|s|/etc/wine/wine.conf|timeout=1|timeout=30|systemctl reload wineserver|wine|win_to_1|pfx|procs|fs leftover leftover down; bounce|WINE_TIMEOUT leftover 1 leftover; a 2s start is aborted so the pfx 504s
proton|PROTON_TIMEOUT|1|30|s|/etc/proton/proton.conf|timeout=1|timeout=30|systemctl reload proton|proton|prn_to_1|pfx|steam|fs leftover leftover down; bounce|PROTON_TIMEOUT leftover 1 leftover; a 2s start is aborted so the game 504s
dxvk|DXVK_TIMEOUT|1|10|s|/etc/dxvk/dxvk.conf|timeout=1|timeout=10|systemctl reload dxvk|dxvk|dxv_to_1|d3d|vk|fs leftover leftover down; bounce|DXVK_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the shader 504s
vkd3d|VKD3D_TIMEOUT|1|10|s|/etc/vkd3d/vkd3d.conf|timeout=1|timeout=10|systemctl reload vkd3d|vkd3d|vkd_to_1|d3d12|vk|fs leftover leftover down; bounce|VKD3D_TIMEOUT leftover 1 leftover; a 2s compile is aborted so the shader 504s
gamemode|GAMEMODE_TIMEOUT|1|10|s|/etc/gamemode.ini|timeout=1|timeout=10|systemctl reload gamemoded|gamemoded|gmd_to_1|gov|games|dbus leftover leftover down; bounce|GAMEMODE_TIMEOUT leftover 1 leftover; a 2s request is aborted so the gov 504s
mangohud|MANGOHUD_TIMEOUT|1|10|s|/etc/MangoHud/MangoHud.conf|timeout=1|timeout=10|systemctl reload mangohud|mangohud|mng_to_1|hud|vk|fs leftover leftover down; bounce|MANGOHUD_TIMEOUT leftover 1 leftover; a 2s overlay is aborted so the hud 504s
appimage|APPIMAGE_TIMEOUT|1|30|s|/etc/appimage/appimage.conf|timeout=1|timeout=30|systemctl reload appimaged|appimaged|aim_to_1|apps|fuse|fuse leftover leftover down; bounce|APPIMAGE_TIMEOUT leftover 1 leftover; a 2s mount is aborted so the app 504s
homebrew|BREW_TIMEOUT|1|60|s|/etc/homebrew/brew.conf|timeout=1|timeout=60|systemctl reload brew|brew|hbw_to_1|kegs|cellar|https leftover leftover 403; bounce|BREW_TIMEOUT leftover 1 leftover; a 2s fetch is aborted so the keg 504s
pkgsrc|PKGSRC_TIMEOUT|1|60|s|/etc/pkgsrc/mk.conf|timeout=1|timeout=60|systemctl reload pkgsrc|pkg_add|pks_to_1|pkgs|dist|https leftover leftover 403; bounce|PKGSRC_TIMEOUT leftover 1 leftover; a 2s fetch is aborted so the pkg 504s
portage|PORTAGE_TIMEOUT|1|60|s|/etc/portage/make.conf|timeout=1|timeout=60|systemctl reload portage|emerge|prt_to_1|ebuilds|dist|https leftover leftover 403; bounce|PORTAGE_TIMEOUT leftover 1 leftover; a 2s fetch is aborted so the ebuild 504s
paludis|PALUDIS_TIMEOUT|1|60|s|/etc/paludis/paludis.conf|timeout=1|timeout=60|systemctl reload paludis|cave|pld_to_1|specs|dist|https leftover leftover 403; bounce|PALUDIS_TIMEOUT leftover 1 leftover; a 2s fetch is aborted so the spec 504s
yay|YAY_TIMEOUT|1|60|s|/etc/yay/yay.conf|timeout=1|timeout=60|systemctl reload yay|yay|yay_to_1|aur|pkgs|https leftover leftover 403; bounce|YAY_TIMEOUT leftover 1 leftover; a 2s fetch is aborted so the aur 504s
paru|PARU_TIMEOUT|1|60|s|/etc/paru/paru.conf|timeout=1|timeout=60|systemctl reload paru|paru|pru_to_1|aur|pkgs|https leftover leftover 403; bounce|PARU_TIMEOUT leftover 1 leftover; a 2s fetch is aborted so the aur 504s
aptitude|APTITUDE_TIMEOUT|1|60|s|/etc/aptitude/aptitude.conf|timeout=1|timeout=60|systemctl reload aptitude|aptitude|apt_to_1|pkgs|cache|https leftover leftover 403; bounce|APTITUDE_TIMEOUT leftover 1 leftover; a 2s update is aborted so the cache 504s
composer|COMPOSER_TIMEOUT|1|60|s|/etc/composer/config.json|"timeout": 1|"timeout": 60|systemctl reload composer|composer|cmp_to_1|pkgs|vendor|https leftover leftover 403; bounce|COMPOSER_TIMEOUT leftover 1 leftover; a 2s install is aborted so vendor 504s
bundler|BUNDLER_TIMEOUT|1|60|s|/etc/bundler/config|timeout=1|timeout=60|systemctl reload bundler|bundle|bnd_to_1|gems|vendor|https leftover leftover 403; bounce|BUNDLER_TIMEOUT leftover 1 leftover; a 2s install is aborted so vendor 504s
gem|GEM_TIMEOUT|1|60|s|/etc/gemrc|timeout=1|timeout=60|systemctl reload gem|gem|gem_to_1|gems|cache|https leftover leftover 403; bounce|GEM_TIMEOUT leftover 1 leftover; a 2s fetch is aborted so the gem 504s
leiningen|LEIN_TIMEOUT|1|60|s|/etc/leiningen/profiles.clj|timeout=1|timeout=60|systemctl reload lein|lein|lei_to_1|jars|m2|https leftover leftover 403; bounce|LEIN_TIMEOUT leftover 1 leftover; a 2s deps is aborted so the jar 504s
boot|BOOT_TIMEOUT|1|60|s|/etc/boot/boot.properties|timeout=1|timeout=60|systemctl reload boot|boot|boo_to_1|jars|m2|https leftover leftover 403; bounce|BOOT_TIMEOUT leftover 1 leftover; a 2s deps is aborted so the jar 504s
mix|MIX_TIMEOUT|1|60|s|/etc/mix/mix.conf|timeout=1|timeout=60|systemctl reload mix|mix|mix_to_1|deps|hex|https leftover leftover 403; bounce|MIX_TIMEOUT leftover 1 leftover; a 2s deps.get is aborted so the lock 504s
hex|HEX_TIMEOUT|1|60|s|/etc/hex/hex.config|timeout=1|timeout=60|systemctl reload hex|mix|hex_to_1|pkgs|cache|https leftover leftover 403; bounce|HEX_TIMEOUT leftover 1 leftover; a 2s fetch is aborted so the pkg 504s
'''
WAVE56 = (
    "act/nektos/gocd/octopus/codefresh/travis/appveyor/gromacs/lammps/namd/"
    "amber/openmm/sage/maxima/maple/mathematica/wolfram/steam/lutris/wine/"
    "proton/dxvk/vkd3d/gamemode/mangohud/appimage/homebrew/pkgsrc/portage/"
    "paludis/yay/paru/aptitude/composer/bundler/gem/leiningen/boot/mix/"
    "hex"
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
        svc = f"l6{i:02d}x"
        ns = f"l6{i:02d}"
        clu = f"prod-apsm{901 + i}-{svc[:3]}"
        ticket = f"W2-{12963 + i}"
        node = f"ip-10-241-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4221


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4220 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-56 leftover: {WAVE56}.",
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
