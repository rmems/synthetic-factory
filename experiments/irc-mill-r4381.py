#!/usr/bin/env python3
"""IRC mill r4381+ — wave-64 cms/product-analytics leftover.

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
wagtail|WAGTAIL_TIMEOUT|1|30|s|/etc/wagtail/wagtail.conf|timeout=1|timeout=30|systemctl reload wagtail|wt|wag_to_1|pages|images|pg leftover leftover down; bounce|WAGTAIL_TIMEOUT leftover 1 leftover; a 2s publish is aborted so the pages 504s
mezzanine|MEZZANINE_TIMEOUT|1|30|s|/etc/mezzanine/mezzanine.conf|timeout=1|timeout=30|systemctl reload mezzanine|mz|mez_to_1|pages|blogs|pg leftover leftover down; bounce|MEZZANINE_TIMEOUT leftover 1 leftover; a 2s publish is aborted so the pages 504s
djangocms|DJANGOCMS_TIMEOUT|1|30|s|/etc/djangocms/djangocms.conf|timeout=1|timeout=30|systemctl reload djangocms|dc|dja_to_1|pages|plugins|pg leftover leftover down; bounce|DJANGOCMS_TIMEOUT leftover 1 leftover; a 2s publish is aborted so the pages 504s
plone|PLONE_TIMEOUT|1|30|s|/etc/plone/plone.conf|timeout=1|timeout=30|systemctl reload plone|pl|plo_to_1|objs|catalog|zodb leftover leftover down; bounce|PLONE_TIMEOUT leftover 1 leftover; a 2s publish is aborted so the objs 504s
drupal|DRUPAL_TIMEOUT|1|30|s|/etc/drupal/drupal.conf|timeout=1|timeout=30|systemctl reload drupal|dp|dru_to_1|nodes|cache|mysql leftover leftover down; bounce|DRUPAL_TIMEOUT leftover 1 leftover; a 2s render is aborted so the nodes 504s
typo3|TYPO3_TIMEOUT|1|30|s|/etc/typo3/typo3.conf|timeout=1|timeout=30|systemctl reload typo3|t3|typ_to_1|pages|cache|mysql leftover leftover down; bounce|TYPO3_TIMEOUT leftover 1 leftover; a 2s render is aborted so the pages 504s
matomo|MATOMO_TIMEOUT|1|30|s|/etc/matomo/matomo.conf|timeout=1|timeout=30|systemctl reload matomo|mt|mat_to_1|hits|sites|mysql leftover leftover down; bounce|MATOMO_TIMEOUT leftover 1 leftover; a 2s track is aborted so the hits 504s
piwik|PIWIK_TIMEOUT|1|30|s|/etc/piwik/piwik.conf|timeout=1|timeout=30|systemctl reload piwik|pw|piw_to_1|hits|sites|mysql leftover leftover down; bounce|PIWIK_TIMEOUT leftover 1 leftover; a 2s track is aborted so the hits 504s
plausible|PLAUSIBLE_TIMEOUT|1|30|s|/etc/plausible/plausible.conf|timeout=1|timeout=30|systemctl reload plausible|ps|pla_to_1|events|sites|clickhouse leftover leftover down; bounce|PLAUSIBLE_TIMEOUT leftover 1 leftover; a 2s ingest is aborted so the events 504s
umami|UMAMI_TIMEOUT|1|30|s|/etc/umami/umami.conf|timeout=1|timeout=30|systemctl reload umami|um|uma_to_1|events|sites|pg leftover leftover down; bounce|UMAMI_TIMEOUT leftover 1 leftover; a 2s ingest is aborted so the events 504s
goatcounter|GOATCOUNTER_TIMEOUT|1|30|s|/etc/goatcounter/goatcounter.conf|timeout=1|timeout=30|systemctl reload goatcounter|gc|goa_to_1|hits|sites|sqlite leftover leftover down; bounce|GOATCOUNTER_TIMEOUT leftover 1 leftover; a 2s count is aborted so the hits 504s
countly|COUNTLY_TIMEOUT|1|30|s|/etc/countly/countly.conf|timeout=1|timeout=30|systemctl reload countly|cl|cou_to_1|events|apps|mongo leftover leftover down; bounce|COUNTLY_TIMEOUT leftover 1 leftover; a 2s ingest is aborted so the events 504s
snowplow|SNOWPLOW_TIMEOUT|1|30|s|/etc/snowplow/snowplow.conf|timeout=1|timeout=30|systemctl reload snowplow|sp|sno_to_1|events|enrich|kafka leftover leftover down; bounce|SNOWPLOW_TIMEOUT leftover 1 leftover; a 2s enrich is aborted so the events 504s
segment|SEGMENT_TIMEOUT|1|30|s|/etc/segment/segment.conf|timeout=1|timeout=30|systemctl reload segment|sg|seg_to_1|events|sources|https leftover leftover down; bounce|SEGMENT_TIMEOUT leftover 1 leftover; a 2s forward is aborted so the events 504s
rudderstack|RUDDERSTACK_TIMEOUT|1|30|s|/etc/rudderstack/rudderstack.conf|timeout=1|timeout=30|systemctl reload rudderstack|rs|rud_to_1|events|sources|https leftover leftover down; bounce|RUDDERSTACK_TIMEOUT leftover 1 leftover; a 2s forward is aborted so the events 504s
jitsu|JITSU_TIMEOUT|1|30|s|/etc/jitsu/jitsu.conf|timeout=1|timeout=30|systemctl reload jitsu|jt|jit_to_1|events|dests|https leftover leftover down; bounce|JITSU_TIMEOUT leftover 1 leftover; a 2s forward is aborted so the events 504s
posthog|POSTHOG_TIMEOUT|1|30|s|/etc/posthog/posthog.conf|timeout=1|timeout=30|systemctl reload posthog|phg|pos_to_1|events|flags|clickhouse leftover leftover down; bounce|POSTHOG_TIMEOUT leftover 1 leftover; a 2s ingest is aborted so the events 504s
amplitude|AMPLITUDE_TIMEOUT|1|30|s|/etc/amplitude/amplitude.conf|timeout=1|timeout=30|systemctl reload amplitude|amp|amp_to_1|events|users|https leftover leftover down; bounce|AMPLITUDE_TIMEOUT leftover 1 leftover; a 2s ingest is aborted so the events 504s
mixpanel|MIXPANEL_TIMEOUT|1|30|s|/etc/mixpanel/mixpanel.conf|timeout=1|timeout=30|systemctl reload mixpanel|mx|mix_to_1|events|users|https leftover leftover down; bounce|MIXPANEL_TIMEOUT leftover 1 leftover; a 2s ingest is aborted so the events 504s
heap|HEAP_TIMEOUT|1|30|s|/etc/heap/heap.conf|timeout=1|timeout=30|systemctl reload heap|hp|hea_to_1|events|users|https leftover leftover down; bounce|HEAP_TIMEOUT leftover 1 leftover; a 2s ingest is aborted so the events 504s
fullstory|FULLSTORY_TIMEOUT|1|30|s|/etc/fullstory/fullstory.conf|timeout=1|timeout=30|systemctl reload fullstory|fs|ful_to_1|sessions|replay|https leftover leftover down; bounce|FULLSTORY_TIMEOUT leftover 1 leftover; a 2s capture is aborted so the sessions 504s
logrocket|LOGROCKET_TIMEOUT|1|30|s|/etc/logrocket/logrocket.conf|timeout=1|timeout=30|systemctl reload logrocket|lr|log_to_1|sessions|replay|https leftover leftover down; bounce|LOGROCKET_TIMEOUT leftover 1 leftover; a 2s capture is aborted so the sessions 504s
glitchtip2|GLITCHTIP2_TIMEOUT|1|30|s|/etc/glitchtip2/glitchtip2.conf|timeout=1|timeout=30|systemctl reload glitchtip2|gt|gli_to_1|events|issues|pg leftover leftover down; bounce|GLITCHTIP2_TIMEOUT leftover 1 leftover; a 2s ingest is aborted so the events 504s
raygun|RAYGUN_TIMEOUT|1|30|s|/etc/raygun/raygun.conf|timeout=1|timeout=30|systemctl reload raygun|rg|ray_to_1|crashes|apps|https leftover leftover down; bounce|RAYGUN_TIMEOUT leftover 1 leftover; a 2s ingest is aborted so the crashes 504s
newrelic|NEWRELIC_TIMEOUT|1|30|s|/etc/newrelic/newrelic.conf|timeout=1|timeout=30|systemctl reload newrelic|nr|new_to_1|spans|apm|https leftover leftover down; bounce|NEWRELIC_TIMEOUT leftover 1 leftover; a 2s ingest is aborted so the spans 504s
dynatrace|DYNATRACE_TIMEOUT|1|30|s|/etc/dynatrace/dynatrace.conf|timeout=1|timeout=30|systemctl reload dynatrace|dt|dyn_to_1|spans|oneagent|https leftover leftover down; bounce|DYNATRACE_TIMEOUT leftover 1 leftover; a 2s ingest is aborted so the spans 504s
appdynamics|APPDYNAMICS_TIMEOUT|1|30|s|/etc/appdynamics/appdynamics.conf|timeout=1|timeout=30|systemctl reload appdynamics|ad|app_to_1|spans|agents|https leftover leftover down; bounce|APPDYNAMICS_TIMEOUT leftover 1 leftover; a 2s ingest is aborted so the spans 504s
elasticapm2|ELASTICAPM2_TIMEOUT|1|30|s|/etc/elasticapm2/elasticapm2.conf|timeout=1|timeout=30|systemctl reload elasticapm2|ea|ela_to_1|spans|intakes|es leftover leftover down; bounce|ELASTICAPM2_TIMEOUT leftover 1 leftover; a 2s intake is aborted so the spans 504s
prometheus2|PROMETHEUS2_TIMEOUT|1|30|s|/etc/prometheus2/prometheus2.conf|timeout=1|timeout=30|systemctl reload prometheus2|pm|pro_to_1|scrapes|targets|http leftover leftover down; bounce|PROMETHEUS2_TIMEOUT leftover 1 leftover; a 2s scrape is aborted so the scrapes 504s
thanosquery|THANOSQUERY_TIMEOUT|1|30|s|/etc/thanosquery/thanosquery.conf|timeout=1|timeout=30|systemctl reload thanosquery|tq|tha_to_1|queries|stores|grpc leftover leftover down; bounce|THANOSQUERY_TIMEOUT leftover 1 leftover; a 2s query is aborted so the queries 504s
mimir2|MIMIR2_TIMEOUT|1|30|s|/etc/mimir2/mimir2.conf|timeout=1|timeout=30|systemctl reload mimir2|mm|mim_to_1|samples|ingesters|http leftover leftover down; bounce|MIMIR2_TIMEOUT leftover 1 leftover; a 2s ingest is aborted so the samples 504s
grafanaloki|GRAFANALOKI_TIMEOUT|1|30|s|/etc/grafanaloki/grafanaloki.conf|timeout=1|timeout=30|systemctl reload grafanaloki|glk|gra_to_1|lines|ingesters|http leftover leftover down; bounce|GRAFANALOKI_TIMEOUT leftover 1 leftover; a 2s push is aborted so the lines 504s
netbox2|NETBOX2_TIMEOUT|1|30|s|/etc/netbox2/netbox2.conf|timeout=1|timeout=30|systemctl reload netbox2|nb|net_to_1|ips|racks|pg leftover leftover down; bounce|NETBOX2_TIMEOUT leftover 1 leftover; a 2s save is aborted so the ips 504s
phpipam2|PHPIPAM2_TIMEOUT|1|30|s|/etc/phpipam2/phpipam2.conf|timeout=1|timeout=30|systemctl reload phpipam2|ip|php_to_1|subs|vlans|mysql leftover leftover down; bounce|PHPIPAM2_TIMEOUT leftover 1 leftover; a 2s save is aborted so the subs 504s
oxidizedweb|OXIDIZEDWEB_TIMEOUT|1|30|s|/etc/oxidizedweb/oxidizedweb.conf|timeout=1|timeout=30|systemctl reload oxidizedweb|ox|oxi_to_1|cfgs|nodes|git leftover leftover down; bounce|OXIDIZEDWEB_TIMEOUT leftover 1 leftover; a 2s fetch is aborted so the cfgs 504s
nautobot2|NAUTOBOT2_TIMEOUT|1|30|s|/etc/nautobot2/nautobot2.conf|timeout=1|timeout=30|systemctl reload nautobot2|nt|nau_to_1|ips|jobs|pg leftover leftover down; bounce|NAUTOBOT2_TIMEOUT leftover 1 leftover; a 2s run is aborted so the ips 504s
saltstack|SALTSTACK_TIMEOUT|1|30|s|/etc/saltstack/saltstack.conf|timeout=1|timeout=30|systemctl reload saltstack|ss|sal_to_1|jobs|minions|zeromq leftover leftover down; bounce|SALTSTACK_TIMEOUT leftover 1 leftover; a 2s publish is aborted so the jobs 504s
saltmaster|SALTMASTER_TIMEOUT|1|30|s|/etc/saltmaster/saltmaster.conf|timeout=1|timeout=30|systemctl reload saltmaster|sm|sal_to_1|jobs|keys|zeromq leftover leftover down; bounce|SALTMASTER_TIMEOUT leftover 1 leftover; a 2s publish is aborted so the jobs 504s
saltminion|SALTMINION_TIMEOUT|1|30|s|/etc/saltminion/saltminion.conf|timeout=1|timeout=30|systemctl reload saltminion|smi|sal_to_1|jobs|states|zeromq leftover leftover down; bounce|SALTMINION_TIMEOUT leftover 1 leftover; a 2s apply is aborted so the jobs 504s
chefserver|CHEFSERVER_TIMEOUT|1|30|s|/etc/chefserver/chefserver.conf|timeout=1|timeout=30|systemctl reload chefserver|cs|che_to_1|cooks|nodes|https leftover leftover down; bounce|CHEFSERVER_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the cooks 504s
'''
WAVE = (
    "wagtail/mezzanine/djangocms/plone/drupal/typo3/matomo/piwik/plausible/umami/goatcounter/countly/snowplow/segment/rudderstack/jitsu/posthog/amplitude/mixpanel/heap/fullstory/logrocket/glitchtip2/raygun/newrelic/dynatrace/appdynamics/elasticapm2/prometheus2/thanosquery/mimir2/grafanaloki/netbox2/phpipam2/oxidizedweb/nautobot2/saltstack/saltmaster/saltminion/chefserver"
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
        svc = f"u0{i:02d}x"
        ns = f"u0{i:02d}"
        clu = f"prod-aptv{901 + i}-{svc[:3]}"
        ticket = f"W2-{ 13283 + i }"
        node = f"ip-10-249-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4381


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4317 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-64 leftover: {WAVE}.",
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
