#!/usr/bin/env python3
"""data-pipeline-repair mill r3317+ wave16 unique catalog."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

s = importlib.util.spec_from_file_location(
    "w9", "/home/raulmc/rmems/synthetic-factory/experiments/dpr_mill_r3039.py"
)
w9 = importlib.util.module_from_spec(s)
s.loader.exec_module(w9)
okp, failp = w9.okp, w9.failp
build, audit = w9.build, w9.audit
notes_for, published_identities, guard = w9.notes_for, w9.published_identities, w9.guard
GENERATOR = w9.GENERATOR

PAIRS = [
    (okp("cloudflare-argo", "Cloudflare Argo vs disable CF", "argo",
         "argo.smart_routing=false", "argo.smart_routing=true", "Cloudflare", "CA-01", "tiered",
         "Bunny leftover / Fastly leftover",
         "Cloudflare pay-cdn cold-path after argo.smart_routing stayed false", "cold", 1, "zone.json"),
     failp("bunny-optimizer", "Bunny optimizer vs disable Bunny", "optimizer",
           "optimizer.enabled=false", "optimizer.enabled=true", "Bunny", "BO-01", "webp",
           "Cloudflare leftover / Fastly leftover",
           "Bunny pay-cdn unoptimized after optimizer.enabled stayed false",
           "unopt", 1, "platform-bunny", "pullzone.json")),
    (okp("keycdn-purge", "KeyCDN purge vs disable KeyCDN", "purge",
         "auto_purge=false", "auto_purge=true", "KeyCDN", "KP-02", "zone",
         "StackPath leftover / Sucuri leftover",
         "KeyCDN pay-assets stale after auto_purge stayed false", "stale", 1, "zone.json"),
     failp("stackpath-waf", "StackPath WAF vs disable StackPath", "waf",
           "waf.enabled=false", "waf.enabled=true", "StackPath", "SW-02", "rules",
           "KeyCDN leftover / Sucuri leftover",
           "StackPath pay-cdn unfiltered after waf.enabled stayed false",
           "open", 1, "platform-stackpath", "site.json")),
    (okp("sucuri-cdn", "Sucuri CDN vs disable Sucuri", "cdn",
         "cdn.enabled=false", "cdn.enabled=true", "Sucuri", "SC-03", "cache",
         "Incapsula leftover / AWS leftover",
         "Sucuri pay-origin uncached after cdn.enabled stayed false", "uncached", 1, "site.json"),
     failp("incapsula-cache", "Imperva cache vs disable Imperva", "cacheMode",
           "cacheMode=disabled", "cacheMode=static_only", "Imperva", "IC-03", "ttl",
           "Sucuri leftover / AWS leftover",
           "Imperva pay-cdn uncached after cacheMode stayed disabled",
           "uncached", 1, "platform-imperva", "site.json")),
    (okp("aws-global-accelerator", "Global Accelerator vs disable AGA", "accelerator",
         "Enabled=false", "Enabled=true", "AGA", "AG-04", "endpoint",
         "AzureTM leftover / Armor leftover",
         "AWS pay-anycast unused after Enabled stayed false", "unused", 1, "aga.json"),
     failp("azure-traffic-manager", "Azure Traffic Manager vs disable ATM", "routingMethod",
           "routingMethod=Priority", "routingMethod=Performance", "ATM", "AT-04", "probe",
           "AGA leftover / Armor leftover",
           "Azure pay-dns Priority after routingMethod stayed Priority",
           "priority", 1, "platform-atm", "profile.json")),
    (okp("gcp-cloud-armor", "Cloud Armor vs disable Armor", "securityPolicy",
         "securityPolicy=", "securityPolicy=pay-armor", "Armor", "GA-05", "rules",
         "CF leftover / Fastly leftover",
         "GCP pay-lb open after securityPolicy stayed empty", "open", 1, "backend.json"),
     failp("cloudflare-bot-fight", "Cloudflare Bot Fight vs disable CF", "bot_fight_mode",
           "bot_fight_mode=off", "bot_fight_mode=on", "Cloudflare", "CB-05", "js",
           "Armor leftover / Fastly leftover",
           "Cloudflare pay-cdn bots after bot_fight_mode stayed off",
           "bots", 1, "platform-cloudflare", "zone.json")),
    (okp("fastly-waf", "Fastly WAF vs disable Fastly", "waf",
         "waf.enabled=false", "waf.enabled=true", "Fastly", "FW-06", "owasp",
         "Akamai leftover / CF leftover",
         "Fastly pay-cdn unfiltered after waf.enabled stayed false", "open", 1, "service.json"),
     failp("akamai-waf", "Akamai WAF vs disable Akamai", "waf",
           "waf.enabled=false", "waf.enabled=true", "Akamai", "AW-06", "ase",
           "Fastly leftover / CF leftover",
           "Akamai pay-cdn unfiltered after waf.enabled stayed false",
           "open", 1, "platform-akamai", "property.json")),
    (okp("cloudfront-waf", "CloudFront WAF vs disable CF", "WebACLId",
         "WebACLId=", "WebACLId=arn:aws:wafv2:pay", "CloudFront", "CW-07", "acl",
         "NGINX leftover / HAProxy leftover",
         "CloudFront pay-cdn open after WebACLId stayed empty", "open", 1, "dist.json"),
     failp("nginx-modsecurity", "NGINX ModSecurity vs disable NGINX", "modsecurity",
           "modsecurity off", "modsecurity on", "NGINX", "NM-07", "crs",
           "CloudFront leftover / HAProxy leftover",
           "NGINX pay-proxy unfiltered after modsecurity stayed off",
           "open", 1, "platform-nginx", "nginx.conf")),
    (okp("haproxy-acl", "HAProxy ACL vs disable HAProxy", "acl",
         "# no acl", "acl pay_ok hdr(X-Pay) -m found", "HAProxy", "HA-08", "http-request",
         "Traefik leftover / Caddy leftover",
         "HAProxy pay-lb open after acl stayed missing", "open", 1, "haproxy.cfg"),
     failp("traefik-middleware", "Traefik middleware vs disable Traefik", "middlewares",
           "middlewares: []", "middlewares: [pay-auth]", "Traefik", "TM-08", "chain",
           "HAProxy leftover / Caddy leftover",
           "Traefik pay-proxy unfiltered after middlewares stayed empty",
           "open", 1, "platform-traefik", "traefik.yml")),
    (okp("caddy-security", "Caddy security vs disable Caddy", "security",
         "# no security", "security { oauth identity provider pay }", "Caddy", "CS-09", "oauth",
         "Varnish leftover / Squid leftover",
         "Caddy pay-proxy anonymous after security stayed missing", "anon", 1, "Caddyfile"),
     failp("varnish-vcl-acl", "Varnish VCL ACL vs disable Varnish", "acl",
           "# no acl", "acl pay { \"10.0.0.0\"/8; }", "Varnish", "VA-09", "purge",
           "Caddy leftover / Squid leftover",
           "Varnish pay-purge open after acl stayed missing",
           "open_purge", 1, "platform-varnish", "default.vcl")),
    (okp("squid-acl", "Squid ACL vs disable Squid", "acl",
         "# no http_access", "http_access allow pay_net", "Squid", "SA-10", "src",
         "Envoy leftover / Istio leftover",
         "Squid pay-proxy allow-all after http_access stayed missing", "allow_all", 1, "squid.conf"),
     failp("envoy-rbac", "Envoy RBAC vs disable Envoy", "rbac",
           "rbac: {}", "rbac: {rules: {action: ALLOW, policies: {pay: {}}}}",
           "Envoy", "ER-10", "shadow", "Squid leftover / Istio leftover",
           "Envoy pay-proxy open after rbac stayed empty",
           "open", 1, "platform-envoy", "envoy.yaml")),
    (okp("istio-authorization", "Istio AuthorizationPolicy vs disable Istio", "AuthorizationPolicy",
         "# no policy", "action: ALLOW rules: [{from: [{source: {principals: [pay]}}]}]",
         "Istio", "IA-11", "ns", "Cilium leftover / Falco leftover",
         "Istio pay-mesh open after AuthorizationPolicy stayed missing", "open", 1, "authz.yaml"),
     failp("cilium-network-policy", "CiliumNetworkPolicy vs disable Cilium", "CiliumNetworkPolicy",
           "# no CNP", "endpointSelector: {matchLabels: {app: pay}}",
           "Cilium", "CN-11", "l7", "Istio leftover / Falco leftover",
           "Cilium pay-pods open after CiliumNetworkPolicy stayed missing",
           "open", 1, "platform-cilium", "cnp.yaml")),
    (okp("falco-http-output", "Falco HTTP output vs disable Falco", "http_output",
         "http_output.enabled=false", "http_output.enabled=true", "Falco", "FH-12", "url",
         "Osquery leftover / Audit leftover",
         "Falco pay-alerts stdout after http_output.enabled stayed false", "stdout", 1, "falco.yaml"),
     failp("osquery-tls", "osquery TLS logger vs disable osquery", "tls_hostname",
           "tls_hostname=", "tls_hostname=pay.example.invalid", "osquery", "OT-12", "enroll",
           "Falco leftover / Audit leftover",
           "osquery pay-hosts stdout after tls_hostname stayed empty",
           "stdout", 1, "platform-osquery", "osquery.conf")),
    (okp("auditbeat-socket-dataset", "Auditbeat socket dataset vs disable Auditbeat", "socket.dataset",
         "socket.dataset=off", "socket.dataset=flow", "Auditbeat", "AS-13", "flow",
         "Packet leftover / Heartbeat leftover",
         "Auditbeat pay-hosts no socket after socket.dataset stayed off", "no_sock", 1, "auditbeat.yml"),
     failp("packetbeat-icmp", "Packetbeat ICMP vs disable Packetbeat", "icmp",
           "icmp.enabled=false", "icmp.enabled=true", "Packetbeat", "PI-13", "protocols",
           "Audit leftover / Heartbeat leftover",
           "Packetbeat pay-net no ICMP after icmp.enabled stayed false",
           "no_icmp", 1, "platform-packetbeat", "packetbeat.yml")),
    (okp("heartbeat-icmp", "Heartbeat ICMP vs disable Heartbeat", "icmp",
         "type: http", "type: icmp", "Heartbeat", "HI-14", "hosts",
         "Metric leftover / Filebeat leftover",
         "Heartbeat pay-probes HTTP-only after type stayed http", "http_only", 1, "heartbeat.yml"),
     failp("metricbeat-autodiscover", "Metricbeat autodiscover vs disable Metricbeat", "autodiscover",
           "autodiscover: null", "autodiscover: {providers: [{type: kubernetes}]}",
           "Metricbeat", "MA-14", "hints", "Heartbeat leftover / Filebeat leftover",
           "Metricbeat pay-k8s static after autodiscover stayed null",
           "static", 1, "platform-metricbeat", "metricbeat.yml")),
    (okp("filebeat-k8s-autodiscover", "Filebeat autodiscover vs disable Filebeat", "autodiscover",
         "autodiscover: null", "autodiscover: {providers: [{type: kubernetes}]}",
         "Filebeat", "FA-15", "hints", "Vector leftover / Loki leftover",
         "Filebeat pay-pods static after autodiscover stayed null", "static", 1, "filebeat.yml"),
     failp("vector-kubernetes-logs", "Vector kubernetes_logs vs disable Vector", "kubernetes_logs",
           "sources.k8s.type=file", "sources.k8s.type=kubernetes_logs",
           "Vector", "VK-15", "pod", "Filebeat leftover / Loki leftover",
           "Vector pay-pods file-tail after type stayed file",
           "file_tail", 1, "platform-vector", "vector.toml")),
]


def plants_for(round_number: int):
    used = published_identities()
    for a, b in PAIRS:
        keys = {a["slug"].lower(), b["slug"].lower(), a["domain"].lower(), b["domain"].lower()}
        if keys & used:
            continue
        try:
            guard(a)
            guard(b)
        except SystemExit:
            continue
        return (lambda r, spec=a: build(r, spec), lambda r, spec=b: build(r, spec))
    raise SystemExit(f"no unused plants r{round_number} bank={len(PAIRS)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", type=Path, required=True)
    args = ap.parse_args()
    recs = [fn(args.round) for fn in plants_for(args.round)]
    if len(recs) != 2 or recs[0]["reward"]["success"] == recs[1]["reward"]["success"]:
        raise SystemExit("need success + handoff pair")
    for rec in recs:
        audit(rec)
        if rec["meta"]["generator"] != GENERATOR or rec["meta"]["round"] != args.round:
            raise SystemExit("bad meta")
        blob = json.dumps(rec)
        if "[variant" in rec["goal"].lower() or '"sim_or_real": "real"' in blob:
            raise SystemExit("banned stamp")
        for bad in ("thought", "chain_of_thought", "scratch", "inner_monologue", "spike_events"):
            if f'"{bad}"' in blob:
                raise SystemExit(f"banned {bad}")
    staging = args.staging
    staging.mkdir(parents=True, exist_ok=True)
    batch = staging / f"batch-r{args.round:02d}.jsonl"
    notes = staging / f"NOTES-r{args.round:02d}.md"
    with batch.open("w") as fh:
        for rec in recs:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    notes.write_text(notes_for(args.round, recs))
    print(json.dumps({"round": args.round, "ids": [r["id"] for r in recs]}))


if __name__ == "__main__":
    sys.exit(main() or 0)
