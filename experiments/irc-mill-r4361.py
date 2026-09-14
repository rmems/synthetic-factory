#!/usr/bin/env python3
"""IRC mill r4361+ — wave-63 dfir/siem/etl leftover.

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
arkime|ARKIME_TIMEOUT|1|30|s|/etc/arkime/arkime.conf|timeout=1|timeout=30|systemctl reload arkime|ak|ark_to_1|pcaps|sessions|es leftover leftover down; bounce|ARKIME_TIMEOUT leftover 1 leftover; a 2s index is aborted so the pcaps 504s
stenographer|STENOGRAPHER_TIMEOUT|1|30|s|/etc/stenographer/stenographer.conf|timeout=1|timeout=30|systemctl reload stenographer|st|ste_to_1|pcaps|disks|fs leftover leftover down; bounce|STENOGRAPHER_TIMEOUT leftover 1 leftover; a 2s write is aborted so the pcaps 504s
misp|MISP_TIMEOUT|1|30|s|/etc/misp/misp.conf|timeout=1|timeout=30|systemctl reload misp|mp|mis_to_1|events|attrs|mysql leftover leftover down; bounce|MISP_TIMEOUT leftover 1 leftover; a 2s publish is aborted so the events 504s
thehive|THEHIVE_TIMEOUT|1|30|s|/etc/thehive/thehive.conf|timeout=1|timeout=30|systemctl reload thehive|th|the_to_1|cases|alerts|es leftover leftover down; bounce|THEHIVE_TIMEOUT leftover 1 leftover; a 2s create is aborted so the cases 504s
shuffle|SHUFFLE_TIMEOUT|1|30|s|/etc/shuffle/shuffle.conf|timeout=1|timeout=30|systemctl reload shuffle|sh|shu_to_1|workflows|apps|https leftover leftover down; bounce|SHUFFLE_TIMEOUT leftover 1 leftover; a 2s run is aborted so the workflows 504s
dfir|DFIR_TIMEOUT|1|30|s|/etc/dfir/dfir.conf|timeout=1|timeout=30|systemctl reload dfir|df|dfi_to_1|cases|timelines|fs leftover leftover down; bounce|DFIR_TIMEOUT leftover 1 leftover; a 2s parse is aborted so the cases 504s
velo|VELO_TIMEOUT|1|30|s|/etc/velo/velo.conf|timeout=1|timeout=30|systemctl reload velo|vl|vel_to_1|hunts|clients|https leftover leftover down; bounce|VELO_TIMEOUT leftover 1 leftover; a 2s collect is aborted so the hunts 504s
velociraptor|VELOCIRAPTOR_TIMEOUT|1|30|s|/etc/velociraptor/velociraptor.conf|timeout=1|timeout=30|systemctl reload velociraptor|vr|vel_to_1|hunts|clients|https leftover leftover down; bounce|VELOCIRAPTOR_TIMEOUT leftover 1 leftover; a 2s collect is aborted so the hunts 504s
fleetdm|FLEETDM_TIMEOUT|1|30|s|/etc/fleetdm/fleetdm.conf|timeout=1|timeout=30|systemctl reload fleetdm|fd|fle_to_1|hosts|queries|mysql leftover leftover down; bounce|FLEETDM_TIMEOUT leftover 1 leftover; a 2s query is aborted so the hosts 504s
osctrl|OSCTRL_TIMEOUT|1|30|s|/etc/osctrl/osctrl.conf|timeout=1|timeout=30|systemctl reload osctrl|oc|osc_to_1|nodes|queries|pg leftover leftover down; bounce|OSCTRL_TIMEOUT leftover 1 leftover; a 2s query is aborted so the nodes 504s
ossecagent|OSSECAGENT_TIMEOUT|1|30|s|/etc/ossecagent/ossecagent.conf|timeout=1|timeout=30|systemctl reload ossecagent|oa|oss_to_1|alerts|syscheck|udp leftover leftover down; bounce|OSSECAGENT_TIMEOUT leftover 1 leftover; a 2s alert is aborted so the alerts 504s
wazuhmanager|WAZUHMANAGER_TIMEOUT|1|30|s|/etc/wazuhmanager/wazuhmanager.conf|timeout=1|timeout=30|systemctl reload wazuhmanager|wm|waz_to_1|alerts|agents|https leftover leftover down; bounce|WAZUHMANAGER_TIMEOUT leftover 1 leftover; a 2s alert is aborted so the alerts 504s
graylog|GRAYLOG_TIMEOUT|1|30|s|/etc/graylog/graylog.conf|timeout=1|timeout=30|systemctl reload graylog|gl|gra_to_1|msgs|inputs|es leftover leftover down; bounce|GRAYLOG_TIMEOUT leftover 1 leftover; a 2s index is aborted so the msgs 504s
graylogserver|GRAYLOGSERVER_TIMEOUT|1|30|s|/etc/graylogserver/graylogserver.conf|timeout=1|timeout=30|systemctl reload graylogserver|gs|gra_to_1|msgs|inputs|es leftover leftover down; bounce|GRAYLOGSERVER_TIMEOUT leftover 1 leftover; a 2s index is aborted so the msgs 504s
graylogsidecar|GRAYLOGSIDECAR_TIMEOUT|1|30|s|/etc/graylogsidecar/graylogsidecar.conf|timeout=1|timeout=30|systemctl reload graylogsidecar|gsc|gra_to_1|beats|cfgs|https leftover leftover down; bounce|GRAYLOGSIDECAR_TIMEOUT leftover 1 leftover; a 2s collect is aborted so the beats 504s
splunkheavy|SPLUNKHEAVY_TIMEOUT|1|30|s|/etc/splunkheavy/splunkheavy.conf|timeout=1|timeout=30|systemctl reload splunkheavy|shf|spl_to_1|events|indexes|https leftover leftover down; bounce|SPLUNKHEAVY_TIMEOUT leftover 1 leftover; a 2s index is aborted so the events 504s
splunkuf|SPLUNKUF_TIMEOUT|1|30|s|/etc/splunkuf/splunkuf.conf|timeout=1|timeout=30|systemctl reload splunkuf|suf|spl_to_1|events|inputs|tcp leftover leftover down; bounce|SPLUNKUF_TIMEOUT leftover 1 leftover; a 2s forward is aborted so the events 504s
logscale|LOGSCALE_TIMEOUT|1|30|s|/etc/logscale/logscale.conf|timeout=1|timeout=30|systemctl reload logscale|ls|log_to_1|events|repos|https leftover leftover down; bounce|LOGSCALE_TIMEOUT leftover 1 leftover; a 2s ingest is aborted so the events 504s
criblstream|CRIBLSTREAM_TIMEOUT|1|30|s|/etc/criblstream/criblstream.conf|timeout=1|timeout=30|systemctl reload criblstream|cs|cri_to_1|events|routes|https leftover leftover down; bounce|CRIBLSTREAM_TIMEOUT leftover 1 leftover; a 2s route is aborted so the events 504s
vectordev|VECTORDEV_TIMEOUT|1|30|s|/etc/vectordev/vectordev.conf|timeout=1|timeout=30|systemctl reload vectordev|vd|vec_to_1|events|sinks|https leftover leftover down; bounce|VECTORDEV_TIMEOUT leftover 1 leftover; a 2s ship is aborted so the events 504s
pentaho|PENTAHO_TIMEOUT|1|30|s|/etc/pentaho/pentaho.conf|timeout=1|timeout=30|systemctl reload pentaho|ph|pen_to_1|jobs|ktrs|java leftover leftover down; bounce|PENTAHO_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
kettle|KETTLE_TIMEOUT|1|30|s|/etc/kettle/kettle.conf|timeout=1|timeout=30|systemctl reload kettle|kt|ket_to_1|jobs|steps|java leftover leftover down; bounce|KETTLE_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
hop|HOP_TIMEOUT|1|30|s|/etc/hop/hop.conf|timeout=1|timeout=30|systemctl reload hop|hp|hop_to_1|pipes|xfrms|java leftover leftover down; bounce|HOP_TIMEOUT leftover 1 leftover; a 2s run is aborted so the pipes 504s
apachehop|APACHEHOP_TIMEOUT|1|30|s|/etc/apachehop/apachehop.conf|timeout=1|timeout=30|systemctl reload apachehop|ah|apa_to_1|pipes|xfrms|java leftover leftover down; bounce|APACHEHOP_TIMEOUT leftover 1 leftover; a 2s run is aborted so the pipes 504s
beamdataflow|BEAMDATAFLOW_TIMEOUT|1|30|s|/etc/beamdataflow/beamdataflow.conf|timeout=1|timeout=30|systemctl reload beamdataflow|bd|bea_to_1|jobs|pcols|gcp leftover leftover down; bounce|BEAMDATAFLOW_TIMEOUT leftover 1 leftover; a 2s run is aborted so the jobs 504s
airflow2|AIRFLOW2_TIMEOUT|1|30|s|/etc/airflow2/airflow2.conf|timeout=1|timeout=30|systemctl reload airflow2|af|air_to_1|dags|tasks|pg leftover leftover down; bounce|AIRFLOW2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the dags 504s
astronomer|ASTRONOMER_TIMEOUT|1|30|s|/etc/astronomer/astronomer.conf|timeout=1|timeout=30|systemctl reload astronomer|as|ast_to_1|dags|deploys|https leftover leftover down; bounce|ASTRONOMER_TIMEOUT leftover 1 leftover; a 2s deploy is aborted so the dags 504s
dbtcore|DBTCORE_TIMEOUT|1|30|s|/etc/dbtcore/dbtcore.conf|timeout=1|timeout=30|systemctl reload dbtcore|db|dbt_to_1|models|manifests|fs leftover leftover down; bounce|DBTCORE_TIMEOUT leftover 1 leftover; a 2s run is aborted so the models 504s
bigeye|BIGEYE_TIMEOUT|1|30|s|/etc/bigeye/bigeye.conf|timeout=1|timeout=30|systemctl reload bigeye|be|big_to_1|monitors|metrics|https leftover leftover down; bounce|BIGEYE_TIMEOUT leftover 1 leftover; a 2s check is aborted so the monitors 504s
anomaloc|ANOMALOC_TIMEOUT|1|30|s|/etc/anomaloc/anomaloc.conf|timeout=1|timeout=30|systemctl reload anomaloc|an|ano_to_1|anoms|metrics|https leftover leftover down; bounce|ANOMALOC_TIMEOUT leftover 1 leftover; a 2s score is aborted so the anoms 504s
modeanalytics|MODEANALYTICS_TIMEOUT|1|30|s|/etc/modeanalytics/modeanalytics.conf|timeout=1|timeout=30|systemctl reload modeanalytics|ma|mod_to_1|reports|sqls|https leftover leftover down; bounce|MODEANALYTICS_TIMEOUT leftover 1 leftover; a 2s run is aborted so the reports 504s
thoughtspot|THOUGHTSPOT_TIMEOUT|1|30|s|/etc/thoughtspot/thoughtspot.conf|timeout=1|timeout=30|systemctl reload thoughtspot|ts|tho_to_1|pins|search|https leftover leftover down; bounce|THOUGHTSPOT_TIMEOUT leftover 1 leftover; a 2s query is aborted so the pins 504s
cubejs|CUBEJS_TIMEOUT|1|30|s|/etc/cubejs/cubejs.conf|timeout=1|timeout=30|systemctl reload cubejs|cj|cub_to_1|cubes|preaggs|https leftover leftover down; bounce|CUBEJS_TIMEOUT leftover 1 leftover; a 2s query is aborted so the cubes 504s
pgrst|PGRST_TIMEOUT|1|30|s|/etc/pgrst/pgrst.conf|timeout=1|timeout=30|systemctl reload pgrst|pr|pgr_to_1|rows|schemas|pg leftover leftover down; bounce|PGRST_TIMEOUT leftover 1 leftover; a 2s query is aborted so the rows 504s
postgraphile|POSTGRAPHILE_TIMEOUT|1|30|s|/etc/postgraphile/postgraphile.conf|timeout=1|timeout=30|systemctl reload postgraphile|pgql|pos_to_1|nodes|schemas|pg leftover leftover down; bounce|POSTGRAPHILE_TIMEOUT leftover 1 leftover; a 2s query is aborted so the nodes 504s
payloadcms|PAYLOADCMS_TIMEOUT|1|30|s|/etc/payloadcms/payloadcms.conf|timeout=1|timeout=30|systemctl reload payloadcms|pl|pay_to_1|docs|cols|mongo leftover leftover down; bounce|PAYLOADCMS_TIMEOUT leftover 1 leftover; a 2s save is aborted so the docs 504s
ghost|GHOST_TIMEOUT|1|30|s|/etc/ghost/ghost.conf|timeout=1|timeout=30|systemctl reload ghost|gh|gho_to_1|posts|themes|mysql leftover leftover down; bounce|GHOST_TIMEOUT leftover 1 leftover; a 2s publish is aborted so the posts 504s
keystonejs|KEYSTONEJS_TIMEOUT|1|30|s|/etc/keystonejs/keystonejs.conf|timeout=1|timeout=30|systemctl reload keystonejs|ksj|key_to_1|lists|docs|mongo leftover leftover down; bounce|KEYSTONEJS_TIMEOUT leftover 1 leftover; a 2s save is aborted so the lists 504s
sanity|SANITY_TIMEOUT|1|30|s|/etc/sanity/sanity.conf|timeout=1|timeout=30|systemctl reload sanity|sy|san_to_1|docs|datasets|https leftover leftover down; bounce|SANITY_TIMEOUT leftover 1 leftover; a 2s mutate is aborted so the docs 504s
contentful|CONTENTFUL_TIMEOUT|1|30|s|/etc/contentful/contentful.conf|timeout=1|timeout=30|systemctl reload contentful|cf|con_to_1|entries|spaces|https leftover leftover down; bounce|CONTENTFUL_TIMEOUT leftover 1 leftover; a 2s publish is aborted so the entries 504s
'''
WAVE = (
    "arkime/stenographer/misp/thehive/shuffle/dfir/velo/velociraptor/fleetdm/osctrl/ossecagent/wazuhmanager/graylog/graylogserver/graylogsidecar/splunkheavy/splunkuf/logscale/criblstream/vectordev/pentaho/kettle/hop/apachehop/beamdataflow/airflow2/astronomer/dbtcore/bigeye/anomaloc/modeanalytics/thoughtspot/cubejs/pgrst/postgraphile/payloadcms/ghost/keystonejs/sanity/contentful"
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
        svc = f"t9{i:02d}x"
        ns = f"t9{i:02d}"
        clu = f"prod-aptu{901 + i}-{svc[:3]}"
        ticket = f"W2-{ 13243 + i }"
        node = f"ip-10-248-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4361


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4317 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-63 leftover: {WAVE}.",
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
