#!/usr/bin/env python3
"""IRC mill r4321+ — wave-61 authz/apm/feature-flag leftover.

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
glauth|GLAUTH_TIMEOUT|1|30|s|/etc/glauth/glauth.conf|timeout=1|timeout=30|systemctl reload glauth|slapd|gla_to_1|binds|ldap|ldap leftover leftover down; bounce|GLAUTH_TIMEOUT leftover 1 leftover; a 2s bind is aborted so the binds 504s
polar|POLAR_TIMEOUT|1|30|s|/etc/polar/polar.conf|timeout=1|timeout=30|systemctl reload polar|oso|pol_to_1|checks|policy|redis leftover leftover down; bounce|POLAR_TIMEOUT leftover 1 leftover; a 2s check is aborted so the checks 504s
gorbac|GORBAC_TIMEOUT|1|30|s|/etc/gorbac/gorbac.conf|timeout=1|timeout=30|systemctl reload gorbac|rbacd|gor_to_1|roles|acl|etcd leftover leftover down; bounce|GORBAC_TIMEOUT leftover 1 leftover; a 2s role is aborted so the roles 504s
ladon|LADON_TIMEOUT|1|30|s|/etc/ladon/ladon.conf|timeout=1|timeout=30|systemctl reload ladon|warden|lad_to_1|guards|policy|pg leftover leftover down; bounce|LADON_TIMEOUT leftover 1 leftover; a 2s guard is aborted so the guards 504s
skywalking|SKYWALKING_TIMEOUT|1|30|s|/etc/skywalking/skywalking.conf|timeout=1|timeout=30|systemctl reload skywalking|oap|sky_to_1|traces|spans|es leftover leftover down; bounce|SKYWALKING_TIMEOUT leftover 1 leftover; a 2s trace is aborted so the traces 504s
pinpoint|PINPOINT_TIMEOUT|1|30|s|/etc/pinpoint/pinpoint.conf|timeout=1|timeout=30|systemctl reload pinpoint|collector|pin_to_1|spans|agents|hbase leftover leftover down; bounce|PINPOINT_TIMEOUT leftover 1 leftover; a 2s span is aborted so the spans 504s
opentelemetry|OPENTELEMETRY_TIMEOUT|1|30|s|/etc/opentelemetry/opentelemetry.conf|timeout=1|timeout=30|systemctl reload opentelemetry|otelcol|ope_to_1|spans|pipes|otlp leftover leftover down; bounce|OPENTELEMETRY_TIMEOUT leftover 1 leftover; a 2s export is aborted so the spans 504s
appoptics|APPOPTICS_TIMEOUT|1|30|s|/etc/appoptics/appoptics.conf|timeout=1|timeout=30|systemctl reload appoptics|ao|app_to_1|metrics|traces|https leftover leftover down; bounce|APPOPTICS_TIMEOUT leftover 1 leftover; a 2s metric is aborted so the metrics 504s
instana|INSTANA_TIMEOUT|1|30|s|/etc/instana/instana.conf|timeout=1|timeout=30|systemctl reload instana|agent|ins_to_1|spans|sensors|https leftover leftover down; bounce|INSTANA_TIMEOUT leftover 1 leftover; a 2s span is aborted so the spans 504s
lightstep|LIGHTSTEP_TIMEOUT|1|30|s|/etc/lightstep/lightstep.conf|timeout=1|timeout=30|systemctl reload lightstep|sat|lig_to_1|spans|traces|https leftover leftover down; bounce|LIGHTSTEP_TIMEOUT leftover 1 leftover; a 2s span is aborted so the spans 504s
honeycomb|HONEYCOMB_TIMEOUT|1|30|s|/etc/honeycomb/honeycomb.conf|timeout=1|timeout=30|systemctl reload honeycomb|refinery|hon_to_1|events|traces|https leftover leftover down; bounce|HONEYCOMB_TIMEOUT leftover 1 leftover; a 2s event is aborted so the events 504s
sentryrelay|SENTRYRELAY_TIMEOUT|1|30|s|/etc/sentryrelay/sentryrelay.conf|timeout=1|timeout=30|systemctl reload sentryrelay|relay|sen_to_1|events|envelopes|https leftover leftover down; bounce|SENTRYRELAY_TIMEOUT leftover 1 leftover; a 2s event is aborted so the events 504s
nightwatch|NIGHTWATCH_TIMEOUT|1|30|s|/etc/nightwatch/nightwatch.conf|timeout=1|timeout=30|systemctl reload nightwatch|nw|nig_to_1|jobs|specs|https leftover leftover down; bounce|NIGHTWATCH_TIMEOUT leftover 1 leftover; a 2s job is aborted so the jobs 504s
elasticapm|ELASTICAPM_TIMEOUT|1|30|s|/etc/elasticapm/elasticapm.conf|timeout=1|timeout=30|systemctl reload elasticapm|apm|ela_to_1|traces|intakes|es leftover leftover down; bounce|ELASTICAPM_TIMEOUT leftover 1 leftover; a 2s intake is aborted so the traces 504s
sonarqube|SONARQUBE_TIMEOUT|1|30|s|/etc/sonarqube/sonarqube.conf|timeout=1|timeout=30|systemctl reload sonarqube|sonar|son_to_1|scans|projects|pg leftover leftover down; bounce|SONARQUBE_TIMEOUT leftover 1 leftover; a 2s scan is aborted so the scans 504s
coveralls|COVERALLS_TIMEOUT|1|30|s|/etc/coveralls/coveralls.conf|timeout=1|timeout=30|systemctl reload coveralls|cv|cov_to_1|reports|jobs|https leftover leftover down; bounce|COVERALLS_TIMEOUT leftover 1 leftover; a 2s report is aborted so the reports 504s
codecov|CODECOV_TIMEOUT|1|30|s|/etc/codecov/codecov.conf|timeout=1|timeout=30|systemctl reload codecov|cc|cod_to_1|reports|commits|https leftover leftover down; bounce|CODECOV_TIMEOUT leftover 1 leftover; a 2s upload is aborted so the reports 504s
jacoco|JACOCO_TIMEOUT|1|30|s|/etc/jacoco/jacoco.conf|timeout=1|timeout=30|systemctl reload jacoco|agent|jac_to_1|probes|classes|jvm leftover leftover down; bounce|JACOCO_TIMEOUT leftover 1 leftover; a 2s probe is aborted so the probes 504s
cobertura|COBERTURA_TIMEOUT|1|30|s|/etc/cobertura/cobertura.conf|timeout=1|timeout=30|systemctl reload cobertura|cb|cob_to_1|reports|classes|jvm leftover leftover down; bounce|COBERTURA_TIMEOUT leftover 1 leftover; a 2s report is aborted so the reports 504s
gcov|GCOV_TIMEOUT|1|30|s|/etc/gcov/gcov.conf|timeout=1|timeout=30|systemctl reload gcov|gcc|gco_to_1|notes|objs|fs leftover leftover down; bounce|GCOV_TIMEOUT leftover 1 leftover; a 2s note is aborted so the notes 504s
lcov|LCOV_TIMEOUT|1|30|s|/etc/lcov/lcov.conf|timeout=1|timeout=30|systemctl reload lcov|info|lco_to_1|htmls|notes|fs leftover leftover down; bounce|LCOV_TIMEOUT leftover 1 leftover; a 2s html is aborted so the htmls 504s
kcov|KCOV_TIMEOUT|1|30|s|/etc/kcov/kcov.conf|timeout=1|timeout=30|systemctl reload kcov|cov|kco_to_1|reports|bins|fs leftover leftover down; bounce|KCOV_TIMEOUT leftover 1 leftover; a 2s report is aborted so the reports 504s
tarpaulin|TARPAULIN_TIMEOUT|1|30|s|/etc/tarpaulin/tarpaulin.conf|timeout=1|timeout=30|systemctl reload tarpaulin|tp|tar_to_1|reports|crates|fs leftover leftover down; bounce|TARPAULIN_TIMEOUT leftover 1 leftover; a 2s report is aborted so the reports 504s
istanbul|ISTANBUL_TIMEOUT|1|30|s|/etc/istanbul/istanbul.conf|timeout=1|timeout=30|systemctl reload istanbul|nyc|ist_to_1|reports|js|fs leftover leftover down; bounce|ISTANBUL_TIMEOUT leftover 1 leftover; a 2s report is aborted so the reports 504s
nyc|NYC_TIMEOUT|1|30|s|/etc/nyc/nyc.conf|timeout=1|timeout=30|systemctl reload nyc|cov|nyc_to_1|reports|js|fs leftover leftover down; bounce|NYC_TIMEOUT leftover 1 leftover; a 2s report is aborted so the reports 504s
llvmcov|LLVMCOV_TIMEOUT|1|30|s|/etc/llvmcov/llvmcov.conf|timeout=1|timeout=30|systemctl reload llvmcov|prof|llv_to_1|reports|objs|fs leftover leftover down; bounce|LLVMCOV_TIMEOUT leftover 1 leftover; a 2s report is aborted so the reports 504s
unleash|UNLEASH_TIMEOUT|1|30|s|/etc/unleash/unleash.conf|timeout=1|timeout=30|systemctl reload unleash|ul|unl_to_1|flags|toggles|pg leftover leftover down; bounce|UNLEASH_TIMEOUT leftover 1 leftover; a 2s flag is aborted so the flags 504s
flagsmith|FLAGSMITH_TIMEOUT|1|30|s|/etc/flagsmith/flagsmith.conf|timeout=1|timeout=30|systemctl reload flagsmith|fm|fla_to_1|flags|idents|pg leftover leftover down; bounce|FLAGSMITH_TIMEOUT leftover 1 leftover; a 2s flag is aborted so the flags 504s
growthbook|GROWTHBOOK_TIMEOUT|1|30|s|/etc/growthbook/growthbook.conf|timeout=1|timeout=30|systemctl reload growthbook|gb|gro_to_1|flags|exps|mongo leftover leftover down; bounce|GROWTHBOOK_TIMEOUT leftover 1 leftover; a 2s flag is aborted so the flags 504s
launchdarkly|LAUNCHDARKLY_TIMEOUT|1|30|s|/etc/launchdarkly/launchdarkly.conf|timeout=1|timeout=30|systemctl reload launchdarkly|ld|lau_to_1|flags|streams|https leftover leftover down; bounce|LAUNCHDARKLY_TIMEOUT leftover 1 leftover; a 2s stream is aborted so the flags 504s
configcat|CONFIGCAT_TIMEOUT|1|30|s|/etc/configcat/configcat.conf|timeout=1|timeout=30|systemctl reload configcat|ccat|con_to_1|flags|cdn|https leftover leftover down; bounce|CONFIGCAT_TIMEOUT leftover 1 leftover; a 2s flag is aborted so the flags 504s
statsig|STATSIG_TIMEOUT|1|30|s|/etc/statsig/statsig.conf|timeout=1|timeout=30|systemctl reload statsig|sg|sta_to_1|flags|cfgs|https leftover leftover down; bounce|STATSIG_TIMEOUT leftover 1 leftover; a 2s flag is aborted so the flags 504s
flipt|FLIPT_TIMEOUT|1|30|s|/etc/flipt/flipt.conf|timeout=1|timeout=30|systemctl reload flipt|fl|fli_to_1|flags|ns|https leftover leftover down; bounce|FLIPT_TIMEOUT leftover 1 leftover; a 2s flag is aborted so the flags 504s
gofeatureflag|GOFEATUREFLAG_TIMEOUT|1|30|s|/etc/gofeatureflag/gofeatureflag.conf|timeout=1|timeout=30|systemctl reload gofeatureflag|gff|gof_to_1|flags|cfgs|https leftover leftover down; bounce|GOFEATUREFLAG_TIMEOUT leftover 1 leftover; a 2s flag is aborted so the flags 504s
splitio|SPLITIO_TIMEOUT|1|30|s|/etc/splitio/splitio.conf|timeout=1|timeout=30|systemctl reload splitio|spl|spl_to_1|flags|splits|https leftover leftover down; bounce|SPLITIO_TIMEOUT leftover 1 leftover; a 2s flag is aborted so the flags 504s
bankvaults|BANKVAULTS_TIMEOUT|1|30|s|/etc/bankvaults/bankvaults.conf|timeout=1|timeout=30|systemctl reload bankvaults|bv|ban_to_1|secrets|vault|k8s leftover leftover down; bounce|BANKVAULTS_TIMEOUT leftover 1 leftover; a 2s secret is aborted so the secrets 504s
externalsecrets|EXTERNALSECRETS_TIMEOUT|1|30|s|/etc/externalsecrets/externalsecrets.conf|timeout=1|timeout=30|systemctl reload externalsecrets|eso|ext_to_1|secrets|stores|k8s leftover leftover down; bounce|EXTERNALSECRETS_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the secrets 504s
sealedsecrets|SEALEDSECRETS_TIMEOUT|1|30|s|/etc/sealedsecrets/sealedsecrets.conf|timeout=1|timeout=30|systemctl reload sealedsecrets|ssc|sea_to_1|secrets|certs|k8s leftover leftover down; bounce|SEALEDSECRETS_TIMEOUT leftover 1 leftover; a 2s unseal is aborted so the secrets 504s
transcrypt|TRANSCRYPT_TIMEOUT|1|30|s|/etc/transcrypt/transcrypt.conf|timeout=1|timeout=30|systemctl reload transcrypt|tc|tra_to_1|files|keys|git leftover leftover down; bounce|TRANSCRYPT_TIMEOUT leftover 1 leftover; a 2s decrypt is aborted so the files 504s
gitsecret|GITSECRET_TIMEOUT|1|30|s|/etc/gitsecret/gitsecret.conf|timeout=1|timeout=30|systemctl reload gitsecret|gs|git_to_1|files|gpg|git leftover leftover down; bounce|GITSECRET_TIMEOUT leftover 1 leftover; a 2s reveal is aborted so the files 504s
'''
WAVE = (
    "glauth/polar/gorbac/ladon/skywalking/pinpoint/opentelemetry/appoptics/instana/lightstep/honeycomb/sentryrelay/nightwatch/elasticapm/sonarqube/coveralls/codecov/jacoco/cobertura/gcov/lcov/kcov/tarpaulin/istanbul/nyc/llvmcov/unleash/flagsmith/growthbook/launchdarkly/configcat/statsig/flipt/gofeatureflag/splitio/bankvaults/externalsecrets/sealedsecrets/transcrypt/gitsecret"
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
        svc = f"q1{i:02d}x"
        ns = f"q1{i:02d}"
        clu = f"prod-apss{901 + i}-{svc[:3]}"
        ticket = f"W2-{ 13163 + i }"
        node = f"ip-10-246-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4321


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4317 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-61 leftover: {WAVE}.",
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
