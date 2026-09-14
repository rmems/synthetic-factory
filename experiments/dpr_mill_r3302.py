#!/usr/bin/env python3
"""data-pipeline-repair mill r3302+ wave15 unique catalog."""
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
    (okp("clickhouse-ttl-volume", "ClickHouse TTL MOVE vs disable CH", "TTL",
         "-- no TTL", "TTL ts + INTERVAL 7 DAY TO VOLUME 'cold'", "ClickHouse", "CT-01", "volume",
         "Timescale leftover / Quest leftover",
         "ClickHouse pay-facts never moved after TTL stayed missing", "no_move", 1, "table.sql"),
     failp("timescaledb-drop-chunks", "Timescale drop_chunks vs disable Timescale", "drop_chunks",
           "-- no drop_chunks", "SELECT drop_chunks('pay', interval '30 days')",
           "Timescale", "TD-01", "job", "CH leftover / Quest leftover",
           "Timescale pay-chunks unbounded after drop_chunks stayed missing",
           "unbounded", 1, "platform-timescale", "maint.sql")),
    (okp("questdb-partition-by", "QuestDB partition vs disable QuestDB", "PARTITION BY",
         "-- no PARTITION BY", "PARTITION BY DAY", "QuestDB", "QP-02", "wal",
         "Influx leftover / VM leftover",
         "QuestDB pay-ticks unpartitioned after PARTITION BY stayed missing", "unpart", 1, "table.sql"),
     failp("influx-shard-duration", "Influx shard duration vs disable Influx", "shardGroupDuration",
           "shardGroupDuration=168h", "shardGroupDuration=24h", "Influx", "IS-02", "rp",
           "Quest leftover / VM leftover",
           "Influx pay-metrics weekly-shards after shardGroupDuration stayed 168h",
           "weekly", 1, "platform-influx", "influxdb.conf")),
    (okp("prometheus-scrape-interval", "Prometheus scrape interval vs disable Prometheus", "scrape_interval",
         "scrape_interval: 5m", "scrape_interval: 15s", "Prometheus", "PS-03", "timeout",
         "Loki leftover / Tempo leftover",
         "Prometheus pay-targets lagged 5m after scrape_interval stayed 5m", "lag_m", 5, "prometheus.yml"),
     failp("loki-chunk-idle", "Loki chunk idle vs disable Loki", "chunk_idle_period",
           "chunk_idle_period: 1h", "chunk_idle_period: 5m", "Loki", "LC-03", "target_size",
           "Prometheus leftover / Tempo leftover",
           "Loki pay-logs delayed flush after chunk_idle_period stayed 1h",
           "delay_h", 1, "platform-loki", "loki.yml")),
    (okp("tempo-block-retention", "Tempo block retention vs disable Tempo", "block_retention",
         "block_retention: 0s", "block_retention: 336h", "Tempo", "TB-04", "compacted",
         "Jaeger leftover / Zipkin leftover",
         "Tempo pay-traces never expired after block_retention stayed 0s", "no_ret", 1, "tempo.yml"),
     failp("jaeger-prob-sample", "Jaeger sampling vs disable Jaeger", "SAMPLING_TYPE",
           "SAMPLING_TYPE=const SAMPLING_PARAM=1", "SAMPLING_TYPE=probabilistic SAMPLING_PARAM=0.1",
           "Jaeger", "JS-04", "strategy", "Tempo leftover / Zipkin leftover",
           "Jaeger pay-traces 100% after SAMPLING_TYPE stayed const 1",
           "full_sample", 1, "platform-jaeger", "jaeger.env")),
    (okp("zipkin-sampler", "Zipkin sampler vs disable Zipkin", "SAMPLER_RATE",
         "SAMPLER_RATE=1.0", "SAMPLER_RATE=0.1", "Zipkin", "ZS-05", "type",
         "OTel leftover / Fluent leftover",
         "Zipkin pay-traces 100% after SAMPLER_RATE stayed 1.0", "full_sample", 1, "zipkin.env"),
     failp("fluent-bit-flush", "Fluent Bit flush vs disable Fluent Bit", "Flush",
           "Flush 60", "Flush 1", "Fluent Bit", "FF-05", "Grace",
           "Zipkin leftover / OTel leftover",
           "Fluent Bit pay-logs lagged 60s after Flush stayed 60",
           "lag_s", 60, "platform-fluentbit", "fluent-bit.conf")),
    (okp("vector-batch-timeout", "Vector batch timeout vs disable Vector", "batch.timeout_secs",
         "batch.timeout_secs=60", "batch.timeout_secs=1", "Vector", "VB-06", "max_bytes",
         "Filebeat leftover / Metricbeat leftover",
         "Vector pay-logs lagged 60s after batch.timeout_secs stayed 60", "lag_s", 60, "vector.toml"),
     failp("filebeat-scan-frequency", "Filebeat scan frequency vs disable Filebeat", "scan_frequency",
           "scan_frequency: 60s", "scan_frequency: 1s", "Filebeat", "FS-06", "harvester",
           "Vector leftover / Metricbeat leftover",
           "Filebeat pay-logs lagged 60s after scan_frequency stayed 60s",
           "lag_s", 60, "platform-filebeat", "filebeat.yml")),
    (okp("metricbeat-processors", "Metricbeat processors vs disable Metricbeat", "processors",
         "processors: []", "processors: [{drop_event: {when: {equals: {metricset.name: system}}}}]",
         "Metricbeat", "MP-07", "period", "Heartbeat leftover / Packet leftover",
         "Metricbeat pay-hosts noisy after processors stayed empty", "noisy", 1, "metricbeat.yml"),
     failp("heartbeat-ipv4", "Heartbeat IPv4 vs disable Heartbeat", "ipv4",
           "ipv4: false", "ipv4: true", "Heartbeat", "HI-07", "mode",
           "Metricbeat leftover / Packet leftover",
           "Heartbeat pay-probes IPv6-only after ipv4 stayed false",
           "v6_only", 1, "platform-heartbeat", "heartbeat.yml")),
    (okp("packetbeat-protocols", "Packetbeat protocols vs disable Packetbeat", "protocols",
         "protocols: []", "protocols: [http, mysql, pgsql]", "Packetbeat", "PP-08", "ports",
         "Audit leftover / Osquery leftover",
         "Packetbeat pay-net no L7 after protocols stayed empty", "no_l7", 1, "packetbeat.yml"),
     failp("auditbeat-file-integrity", "Auditbeat file integrity vs disable Auditbeat", "file_integrity",
           "file_integrity.paths: []", "file_integrity.paths: [/etc,/opt/pay]",
           "Auditbeat", "AF-08", "hash", "Packet leftover / Osquery leftover",
           "Auditbeat pay-hosts no FIM after file_integrity.paths stayed empty",
           "no_fim", 1, "platform-auditbeat", "auditbeat.yml")),
    (okp("osquery-schedule", "osquery schedule vs disable osquery", "schedule",
         "schedule: {}", "schedule: {pay_procs: {query: select * from processes, interval: 60}}",
         "osquery", "OS-09", "packs", "Falco leftover / Cilium leftover",
         "osquery pay-hosts unscheduled after schedule stayed {}", "unscheduled", 1, "osquery.conf"),
     failp("falco-priority", "Falco priority vs disable Falco", "priority",
           "priority: debug", "priority: warning", "Falco", "FP-09", "rules",
           "osquery leftover / Cilium leftover",
           "Falco pay-alerts flooded after priority stayed debug",
           "flood", 1, "platform-falco", "falco.yaml")),
    (okp("cilium-policy-audit", "Cilium policy audit vs disable Cilium", "policyAuditMode",
         "policyAuditMode=true", "policyAuditMode=false", "Cilium", "CP-10", "enforce",
         "Istio leftover / Envoy leftover",
         "Cilium pay-policies audit-only after policyAuditMode stayed true", "audit", 1, "values.yaml"),
     failp("istio-outlier", "Istio outlier detection vs disable Istio", "outlierDetection",
           "outlierDetection: {}", "outlierDetection: {consecutive5xxErrors: 5}",
           "Istio", "IO-10", "ejection", "Cilium leftover / Envoy leftover",
           "Istio pay-mesh no eject after outlierDetection stayed empty",
           "no_eject", 1, "platform-istio", "dr.yaml")),
    (okp("envoy-circuit-breaker", "Envoy circuit breaker vs disable Envoy", "circuit_breakers",
         "circuit_breakers: {}", "circuit_breakers: {thresholds: [{max_connections: 100}]}",
         "Envoy", "EC-11", "retry", "NGINX leftover / HAProxy leftover",
         "Envoy pay-proxy unbounded after circuit_breakers stayed empty", "unbounded", 1, "envoy.yaml"),
     failp("nginx-limit-req", "NGINX limit_req vs disable NGINX", "limit_req",
           "# no limit_req", "limit_req zone=pay burst=20 nodelay", "NGINX", "NL-11", "zone",
           "Envoy leftover / HAProxy leftover",
           "NGINX pay-proxy unbounded after limit_req stayed missing",
           "unbounded", 1, "platform-nginx", "nginx.conf")),
    (okp("haproxy-maxconn", "HAProxy maxconn vs disable HAProxy", "maxconn",
         "maxconn 10", "maxconn 10000", "HAProxy", "HM-12", "timeout",
         "Traefik leftover / Caddy leftover",
         "HAProxy pay-lb 10-conn after maxconn stayed 10", "tiny", 1, "haproxy.cfg"),
     failp("traefik-inflight", "Traefik inFlightReq vs disable Traefik", "inFlightReq",
           "inFlightReq: null", "inFlightReq: {amount: 200}", "Traefik", "TI-12", "sourceCriterion",
           "HAProxy leftover / Caddy leftover",
           "Traefik pay-proxy unbounded after inFlightReq stayed null",
           "unbounded", 1, "platform-traefik", "traefik.yml")),
    (okp("caddy-rate-limit", "Caddy rate_limit vs disable Caddy", "rate_limit",
         "# no rate_limit", "rate_limit { zone pay { key {remote_host} events 100 window 1m } }",
         "Caddy", "CR-13", "zone", "Varnish leftover / Squid leftover",
         "Caddy pay-proxy unbounded after rate_limit stayed missing", "unbounded", 1, "Caddyfile"),
     failp("varnish-saint-mode", "Varnish saint mode vs disable Varnish", "saintmode",
           "# no saintmode", "set beresp.saintmode = 10s", "Varnish", "VS-13", "grace",
           "Caddy leftover / Squid leftover",
           "Varnish pay-cache no saint after saintmode stayed missing",
           "no_saint", 1, "platform-varnish", "default.vcl")),
    (okp("squid-maxconn", "Squid maxconn vs disable Squid", "maxconn",
         "maxconn 5", "maxconn 500", "Squid", "SM-14", "clients",
         "CloudFront leftover / Fastly leftover",
         "Squid pay-proxy 5-conn after maxconn stayed 5", "tiny", 1, "squid.conf"),
     failp("cloudfront-origin-timeout", "CloudFront origin timeout vs disable CF", "OriginReadTimeout",
           "OriginReadTimeout=5", "OriginReadTimeout=60", "CloudFront", "CO-14", "keepalive",
           "Squid leftover / Fastly leftover",
           "CloudFront pay-origin timeout after OriginReadTimeout stayed 5s",
           "timeout", 1, "platform-cloudfront", "dist.json")),
    (okp("fastly-first-byte", "Fastly first-byte timeout vs disable Fastly", "first_byte_timeout",
         "first_byte_timeout=1000", "first_byte_timeout=15000", "Fastly", "FF-15", "between_bytes",
         "Akamai leftover / Cloudflare leftover",
         "Fastly pay-origin timeout after first_byte_timeout stayed 1s", "timeout", 1, "service.json"),
     failp("akamai-sure-route", "Akamai SureRoute vs disable Akamai", "sureRoute",
           "sureRoute.enabled=false", "sureRoute.enabled=true", "Akamai", "AS-15", "testObject",
           "Fastly leftover / Cloudflare leftover",
           "Akamai pay-cdn no SureRoute after sureRoute.enabled stayed false",
           "no_sr", 1, "platform-akamai", "property.json")),
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
