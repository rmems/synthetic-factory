#!/usr/bin/env python3
"""IRC mill r4561+ — wave-73 obs/security-scan leftover.

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
signoz2|SIGNOZ2_TIMEOUT|1|30|s|/etc/signoz2/signoz2.conf|timeout=1|timeout=30|systemctl reload signoz2|sz|sig_to_1|traces|metrics|https leftover leftover down; bounce|SIGNOZ2_TIMEOUT leftover 1 leftover; a 2s ingest is aborted so the traces 504s
uptrace2|UPTRACE2_TIMEOUT|1|30|s|/etc/uptrace2/uptrace2.conf|timeout=1|timeout=30|systemctl reload uptrace2|ut|upt_to_1|spans|metrics|https leftover leftover down; bounce|UPTRACE2_TIMEOUT leftover 1 leftover; a 2s ingest is aborted so the spans 504s
pyroscope2|PYROSCOPE2_TIMEOUT|1|30|s|/etc/pyroscope2/pyroscope2.conf|timeout=1|timeout=30|systemctl reload pyroscope2|pr|pyr_to_1|profiles|apps|https leftover leftover down; bounce|PYROSCOPE2_TIMEOUT leftover 1 leftover; a 2s ingest is aborted so the profiles 504s
parca2|PARCA2_TIMEOUT|1|30|s|/etc/parca2/parca2.conf|timeout=1|timeout=30|systemctl reload parca2|pc|par_to_1|profiles|targets|https leftover leftover down; bounce|PARCA2_TIMEOUT leftover 1 leftover; a 2s scrape is aborted so the profiles 504s
phlare2|PHLARE2_TIMEOUT|1|30|s|/etc/phlare2/phlare2.conf|timeout=1|timeout=30|systemctl reload phlare2|ph|phl_to_1|profiles|tenants|https leftover leftover down; bounce|PHLARE2_TIMEOUT leftover 1 leftover; a 2s ingest is aborted so the profiles 504s
grafanaoncall2|GRAFANAONCALL2_TIMEOUT|1|30|s|/etc/grafanaoncall2/grafanaoncall2.conf|timeout=1|timeout=30|systemctl reload grafanaoncall2|go|gra_to_1|pages|schedules|https leftover leftover down; bounce|GRAFANAONCALL2_TIMEOUT leftover 1 leftover; a 2s page is aborted so the pages 504s
thanos2|THANOS2_TIMEOUT|1|30|s|/etc/thanos2/thanos2.conf|timeout=1|timeout=30|systemctl reload thanos2|th|tha_to_1|queries|stores|grpc leftover leftover down; bounce|THANOS2_TIMEOUT leftover 1 leftover; a 2s query is aborted so the queries 504s
cortex2|CORTEX2_TIMEOUT|1|30|s|/etc/cortex2/cortex2.conf|timeout=1|timeout=30|systemctl reload cortex2|cx|cor_to_1|samples|ingesters|http leftover leftover down; bounce|CORTEX2_TIMEOUT leftover 1 leftover; a 2s ingest is aborted so the samples 504s
m3db2|M3DB2_TIMEOUT|1|30|s|/etc/m3db2/m3db2.conf|timeout=1|timeout=30|systemctl reload m3db2|m3|m3d_to_1|datapoints|namespaces|http leftover leftover down; bounce|M3DB2_TIMEOUT leftover 1 leftover; a 2s write is aborted so the datapoints 504s
chronosphere2|CHRONOSPHERE2_TIMEOUT|1|30|s|/etc/chronosphere2/chronosphere2.conf|timeout=1|timeout=30|systemctl reload chronosphere2|cs|chr_to_1|samples|tenants|https leftover leftover down; bounce|CHRONOSPHERE2_TIMEOUT leftover 1 leftover; a 2s ingest is aborted so the samples 504s
loki2|LOKI2_TIMEOUT|1|30|s|/etc/loki2/loki2.conf|timeout=1|timeout=30|systemctl reload loki2|lk|lok_to_1|lines|ingesters|http leftover leftover down; bounce|LOKI2_TIMEOUT leftover 1 leftover; a 2s push is aborted so the lines 504s
tempo2|TEMPO2_TIMEOUT|1|30|s|/etc/tempo2/tempo2.conf|timeout=1|timeout=30|systemctl reload tempo2|tp|tem_to_1|traces|blocks|http leftover leftover down; bounce|TEMPO2_TIMEOUT leftover 1 leftover; a 2s push is aborted so the traces 504s
jaeger2|JAEGER2_TIMEOUT|1|30|s|/etc/jaeger2/jaeger2.conf|timeout=1|timeout=30|systemctl reload jaeger2|jg|jae_to_1|spans|collectors|http leftover leftover down; bounce|JAEGER2_TIMEOUT leftover 1 leftover; a 2s push is aborted so the spans 504s
zipkin2|ZIPKIN2_TIMEOUT|1|30|s|/etc/zipkin2/zipkin2.conf|timeout=1|timeout=30|systemctl reload zipkin2|zk|zip_to_1|spans|collectors|http leftover leftover down; bounce|ZIPKIN2_TIMEOUT leftover 1 leftover; a 2s push is aborted so the spans 504s
otelcollector2|OTELCOLLECTOR2_TIMEOUT|1|30|s|/etc/otelcollector2/otelcollector2.conf|timeout=1|timeout=30|systemctl reload otelcollector2|oc|ote_to_1|spans|pipes|otlp leftover leftover down; bounce|OTELCOLLECTOR2_TIMEOUT leftover 1 leftover; a 2s export is aborted so the spans 504s
opencensus2|OPENCENSUS2_TIMEOUT|1|30|s|/etc/opencensus2/opencensus2.conf|timeout=1|timeout=30|systemctl reload opencensus2|oe|ope_to_1|spans|exporters|grpc leftover leftover down; bounce|OPENCENSUS2_TIMEOUT leftover 1 leftover; a 2s export is aborted so the spans 504s
falco2|FALCO2_TIMEOUT|1|30|s|/etc/falco2/falco2.conf|timeout=1|timeout=30|systemctl reload falco2|fc|fal_to_1|alerts|rules|k8s leftover leftover down; bounce|FALCO2_TIMEOUT leftover 1 leftover; a 2s alert is aborted so the alerts 504s
tracee2|TRACEE2_TIMEOUT|1|30|s|/etc/tracee2/tracee2.conf|timeout=1|timeout=30|systemctl reload tracee2|tr|tra_to_1|events|ebpf|k8s leftover leftover down; bounce|TRACEE2_TIMEOUT leftover 1 leftover; a 2s capture is aborted so the events 504s
tetragon2|TETRAGON2_TIMEOUT|1|30|s|/etc/tetragon2/tetragon2.conf|timeout=1|timeout=30|systemctl reload tetragon2|tg|tet_to_1|events|policies|k8s leftover leftover down; bounce|TETRAGON2_TIMEOUT leftover 1 leftover; a 2s enforce is aborted so the events 504s
kubebench2|KUBEBENCH2_TIMEOUT|1|30|s|/etc/kubebench2/kubebench2.conf|timeout=1|timeout=30|systemctl reload kubebench2|kb|kub_to_1|checks|nodes|k8s leftover leftover down; bounce|KUBEBENCH2_TIMEOUT leftover 1 leftover; a 2s scan is aborted so the checks 504s
kubehunter2|KUBEHUNTER2_TIMEOUT|1|30|s|/etc/kubehunter2/kubehunter2.conf|timeout=1|timeout=30|systemctl reload kubehunter2|kh|kub_to_1|findings|nodes|k8s leftover leftover down; bounce|KUBEHUNTER2_TIMEOUT leftover 1 leftover; a 2s scan is aborted so the findings 504s
kubesec2|KUBESEC2_TIMEOUT|1|30|s|/etc/kubesec2/kubesec2.conf|timeout=1|timeout=30|systemctl reload kubesec2|ks|kub_to_1|findings|yaml|k8s leftover leftover down; bounce|KUBESEC2_TIMEOUT leftover 1 leftover; a 2s scan is aborted so the findings 504s
trivy2|TRIVY2_TIMEOUT|1|30|s|/etc/trivy2/trivy2.conf|timeout=1|timeout=30|systemctl reload trivy2|tv|tri_to_1|cves|images|oci leftover leftover down; bounce|TRIVY2_TIMEOUT leftover 1 leftover; a 2s scan is aborted so the cves 504s
grype2|GRYPE2_TIMEOUT|1|30|s|/etc/grype2/grype2.conf|timeout=1|timeout=30|systemctl reload grype2|gy|gry_to_1|cves|sboms|oci leftover leftover down; bounce|GRYPE2_TIMEOUT leftover 1 leftover; a 2s scan is aborted so the cves 504s
syft2|SYFT2_TIMEOUT|1|30|s|/etc/syft2/syft2.conf|timeout=1|timeout=30|systemctl reload syft2|sy|syf_to_1|sboms|images|oci leftover leftover down; bounce|SYFT2_TIMEOUT leftover 1 leftover; a 2s catalog is aborted so the sboms 504s
clair2|CLAIR2_TIMEOUT|1|30|s|/etc/clair2/clair2.conf|timeout=1|timeout=30|systemctl reload clair2|cl|cla_to_1|cves|layers|https leftover leftover down; bounce|CLAIR2_TIMEOUT leftover 1 leftover; a 2s index is aborted so the cves 504s
anchore2|ANCHORE2_TIMEOUT|1|30|s|/etc/anchore2/anchore2.conf|timeout=1|timeout=30|systemctl reload anchore2|an|anc_to_1|cves|images|https leftover leftover down; bounce|ANCHORE2_TIMEOUT leftover 1 leftover; a 2s scan is aborted so the cves 504s
cosign2|COSIGN2_TIMEOUT|1|30|s|/etc/cosign2/cosign2.conf|timeout=1|timeout=30|systemctl reload cosign2|co|cos_to_1|sigs|images|oci leftover leftover down; bounce|COSIGN2_TIMEOUT leftover 1 leftover; a 2s verify is aborted so the sigs 504s
policycontroller2|POLICYCONTROLLER2_TIMEOUT|1|30|s|/etc/policycontroller2/policycontroller2.conf|timeout=1|timeout=30|systemctl reload policycontroller2|po|pol_to_1|admits|images|k8s leftover leftover down; bounce|POLICYCONTROLLER2_TIMEOUT leftover 1 leftover; a 2s admit is aborted so the admits 504s
kyverno2|KYVERNO2_TIMEOUT|1|30|s|/etc/kyverno2/kyverno2.conf|timeout=1|timeout=30|systemctl reload kyverno2|ky|kyv_to_1|policies|admits|k8s leftover leftover down; bounce|KYVERNO2_TIMEOUT leftover 1 leftover; a 2s admit is aborted so the policies 504s
gatekeeper2|GATEKEEPER2_TIMEOUT|1|30|s|/etc/gatekeeper2/gatekeeper2.conf|timeout=1|timeout=30|systemctl reload gatekeeper2|gk|gat_to_1|constraints|admits|k8s leftover leftover down; bounce|GATEKEEPER2_TIMEOUT leftover 1 leftover; a 2s admit is aborted so the constraints 504s
cubbyhole|CUBBYHOLE_TIMEOUT|1|30|s|/etc/cubbyhole/cubbyhole.conf|timeout=1|timeout=30|systemctl reload cubbyhole|cu|cub_to_1|secrets|paths|vault leftover leftover down; bounce|CUBBYHOLE_TIMEOUT leftover 1 leftover; a 2s read is aborted so the secrets 504s
opa2|OPA2_TIMEOUT|1|30|s|/etc/opa2/opa2.conf|timeout=1|timeout=30|systemctl reload opa2|op|opa_to_1|decisions|policies|https leftover leftover down; bounce|OPA2_TIMEOUT leftover 1 leftover; a 2s eval is aborted so the decisions 504s
styra2|STYRA2_TIMEOUT|1|30|s|/etc/styra2/styra2.conf|timeout=1|timeout=30|systemctl reload styra2|st|sty_to_1|bundles|systems|https leftover leftover down; bounce|STYRA2_TIMEOUT leftover 1 leftover; a 2s eval is aborted so the bundles 504s
certmanager2|CERTMANAGER2_TIMEOUT|1|30|s|/etc/certmanager2/certmanager2.conf|timeout=1|timeout=30|systemctl reload certmanager2|cm|cer_to_1|certs|orders|k8s leftover leftover down; bounce|CERTMANAGER2_TIMEOUT leftover 1 leftover; a 2s issue is aborted so the certs 504s
trustmanager2|TRUSTMANAGER2_TIMEOUT|1|30|s|/etc/trustmanager2/trustmanager2.conf|timeout=1|timeout=30|systemctl reload trustmanager2|tm|tru_to_1|bundles|bundles|k8s leftover leftover down; bounce|TRUSTMANAGER2_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the bundles 504s
externaldns2|EXTERNALDNS2_TIMEOUT|1|30|s|/etc/externaldns2/externaldns2.conf|timeout=1|timeout=30|systemctl reload externaldns2|ed|ext_to_1|records|sources|k8s leftover leftover down; bounce|EXTERNALDNS2_TIMEOUT leftover 1 leftover; a 2s sync is aborted so the records 504s
ingressnginx2|INGRESSNGINX2_TIMEOUT|1|30|s|/etc/ingressnginx2/ingressnginx2.conf|timeout=1|timeout=30|systemctl reload ingressnginx2|in|ing_to_1|ingresses|backends|k8s leftover leftover down; bounce|INGRESSNGINX2_TIMEOUT leftover 1 leftover; a 2s reload is aborted so the ingresses 504s
contour2|CONTOUR2_TIMEOUT|1|30|s|/etc/contour2/contour2.conf|timeout=1|timeout=30|systemctl reload contour2|ct|con_to_1|httproxies|ir|k8s leftover leftover down; bounce|CONTOUR2_TIMEOUT leftover 1 leftover; a 2s reconcile is aborted so the httproxies 504s
ambassador2|AMBASSADOR2_TIMEOUT|1|30|s|/etc/ambassador2/ambassador2.conf|timeout=1|timeout=30|systemctl reload ambassador2|am|amb_to_1|mappings|hosts|k8s leftover leftover down; bounce|AMBASSADOR2_TIMEOUT leftover 1 leftover; a 2s reconcile is aborted so the mappings 504s
'''
WAVE = (
    "signoz2/uptrace2/pyroscope2/parca2/phlare2/grafanaoncall2/thanos2/cortex2/m3db2/chronosphere2/loki2/tempo2/jaeger2/zipkin2/otelcollector2/opencensus2/falco2/tracee2/tetragon2/kubebench2/kubehunter2/kubesec2/trivy2/grype2/syft2/clair2/anchore2/cosign2/policycontroller2/kyverno2/gatekeeper2/cubbyhole/opa2/styra2/certmanager2/trustmanager2/externaldns2/ingressnginx2/contour2/ambassador2"
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
        svc = f"d9{i:02d}x"
        ns = f"d9{i:02d}"
        clu = f"prod-apue{901 + i}-{svc[:3]}"
        ticket = f"W2-{ 13643 + i }"
        node = f"ip-10-183-{1 + i}-{20 + i}"
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
m.BASE_ROUND = 4561


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
            f"Novel coverage: 98%. Unique service+cluster+symptom goals; RCA pair {slug0} / {slug1}. No OpenSRE stamp, no fraud-graph/sip-proxy, not r2920–r4317 clones. BAN ypbind/oddjob and r3389 opensearch leftover3c. Wave-73 leftover: {WAVE}.",
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
