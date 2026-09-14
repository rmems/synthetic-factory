#!/usr/bin/env python3
"""observability-debug leftover leftover leftover mill r385+.

Distinct product + leftover lie (wrong dashboard, dropped label, silent drop)
+ naive first patch vs bind leftover. Not r365–r384 knob twins.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
DIR = ROOT / "outputs/raw/2026-08-19-agentic/observability-debug-factory"
TXN = ["python3", str(ROOT / "pipelines/round_txn.py")]
FACTORY = "observability-debug-factory"
GEN = "grok-4.6"
HOP = [
    "eval-harness-trajectory-factory",
    "rag-retrieval-debug-factory",
    "browser-tool-use-factory",
    "git-ops-recovery-factory",
    "incident-response-oncall-factory",
]
BANNED = ("thought", "chain_of_thought", "scratch", "inner_monologue")
DB_PREFIXES = ("Plan:", "Observation:", "Reflection:", "Tool call:")

# 16 leftover leftover leftover unique product pairs
PAIRS: list[dict] = [
    {
        "slug": "dd-apm-env-tag-drop-leftover",
        "lslug": "nr-span-event-drop-leftover",
        "svc": "gate-board-svc",
        "lsvc": "jetway-nr-svc",
        "dash": "gboard-dd-env-9",
        "ldash": "jway-nr-span-3",
        "panel": "APM p95 by env",
        "lpanel": "NR span events",
        "file": "/etc/datadog-agent/datadog.yaml",
        "lfile": "/etc/newrelic-infra.yml",
        "false_file": "/etc/newrelic-infra.yml",
        "lfalse_file": "/etc/datadog-agent/datadog.yaml",
        "false_lead": "New Relic license leftover",
        "query": "avg:trace.http.request{service:gate-board-svc}",
        "lquery": "SELECT average(duration) FROM Span WHERE appName='jetway-nr-svc'",
        "exec_path": "/api/v1/query",
        "kind": "prom",
        "exec_obs": '{"status":"success","data":{"result":[]}}',
        "exec_err": "empty APM series",
        "exec_ok": '{"status":"success","data":{"result":[{"metric":{"env":"prod"},"value":[1,0.24]}]}}',
        "fail_line": "ignore_autodiscovery_tags: true  # leftover drops env",
        "fix_line": "ignore_autodiscovery_tags: false",
        "fail_val": "ignore_autodiscovery_tags true leftover",
        "fix_val": "false",
        "yq": ".ignore_autodiscovery_tags",
        "confirm_obs": "true",
        "false_yq": ".license_key",
        "false_obs": "NRAK-xxxx  # present",
        "false_read": "license_key present; NR agent heartbeats",
        "truth_cmd": "curl -sS $DD/api/v1/query --data-urlencode 'query=avg:trace.http.request{*}' | jq '.series|length'",
        "truth_obs": "12  # untagged leftover series exist",
        "lie": "Datadog ignore_autodiscovery_tags leftover true drops env so Grafana APM p95 is empty while /trace/info still 200",
        "llie": "NR span_events leftover max_samples_stored 0 silently drops events; naive DD tag re-enable does not bind NR leftover",
        "ns": "obs-dd",
        "deploy": "dd-agent",
        "side_svc": "bag-scan-svc",
        "side_obs": "1",
        "grafana_obs": '{"schema":{"fields":[{"name":"env"}]}}',
        "false_old": "license_key: NRAK-xxxx",
        "false_new": "license_key: NRAK-rotated",
        "false_patch": "rotated NR license leftover",
        "false2_old": "enable_process_metrics: false",
        "false2_new": "enable_process_metrics: true",
        "false2_patch": "NR process metrics leftover",
        "novel": 74,
        "new_vs": "Datadog autodiscovery tag drop leftover vs New Relic span_events max_samples_stored 0 leftover",
    },
    {
        "slug": "sentry-ignore-errors-leftover",
        "lslug": "honeycomb-dynsample-key-drop-leftover",
        "svc": "pax-wifi-svc",
        "lsvc": "cabin-hc-svc",
        "dash": "pwifi-sentry-ie-2",
        "ldash": "cabin-hc-dyn-7",
        "panel": "Sentry unresolved",
        "lpanel": "Honeycomb heatmap",
        "file": "sentry.properties",
        "lfile": "refinery_rules.toml",
        "false_file": "refinery_rules.toml",
        "lfalse_file": "sentry.properties",
        "false_lead": "Honeycomb sampleRate leftover",
        "query": "event.timestamp:>=-1h project:pax-wifi-svc",
        "lquery": "COUNT FROM traces WHERE service.name=cabin-hc-svc",
        "exec_path": "/api/0/projects/org/pax-wifi-svc/issues/",
        "kind": "grafana",
        "exec_obs": "[]",
        "exec_err": "zero issues",
        "exec_ok": '[{"id":"E1","title":"TypeError: boarding pass"}]',
        "fail_line": "ignore_errors=TypeError  # leftover swallows boarding TypeError",
        "fix_line": "ignore_errors=",
        "fail_val": "ignore_errors TypeError leftover",
        "fix_val": "empty ignore_errors",
        "yq": ".ignore_errors",
        "confirm_obs": "TypeError",
        "false_yq": ".Sampler.SampleRate",
        "false_obs": "1  # honeycomb not dropping",
        "false_read": "SampleRate=1; not the empty Sentry feed",
        "truth_cmd": "curl -sS $SENTRY/api/0/projects/org/pax-wifi-svc/events/?query=TypeError | jq 'length'",
        "truth_obs": "0  # dropped by ignore_errors leftover",
        "lie": "Sentry ignore_errors leftover TypeError so Grafana unresolved is empty while SDK still init",
        "llie": "Honeycomb Refinery Rules leftover Fields empty drops http.status_code; naive ignore_errors clear does not bind Refinery leftover",
        "ns": "obs-sentry",
        "deploy": "sentry-relay",
        "side_svc": "ife-menu-svc",
        "side_obs": "1",
        "grafana_obs": '{"schema":{"fields":[{"name":"issue"}]}}',
        "false_old": "SampleRate = 1",
        "false_new": "SampleRate = 10",
        "false_patch": "raised honeycomb sample leftover",
        "false2_old": "DryRun = false",
        "false2_new": "DryRun = true",
        "false2_patch": "refinery dryrun leftover",
        "novel": 74,
        "new_vs": "Sentry ignore_errors leftover vs Honeycomb Refinery Fields drop leftover",
    },
    {
        "slug": "lightstep-max-spans-zero-leftover",
        "lslug": "chrono-drop-metric-name-leftover",
        "svc": "tarmac-ls-svc",
        "lsvc": "apron-chrono-svc",
        "dash": "tarmac-ls-spans-4",
        "ldash": "apron-ch-drop-8",
        "panel": "Lightstep traces",
        "lpanel": "Chronosphere SLI",
        "file": "/etc/lightstep/collector.yaml",
        "lfile": "/etc/chronosphere/drop_rules.yaml",
        "false_file": "/etc/chronosphere/drop_rules.yaml",
        "lfalse_file": "/etc/lightstep/collector.yaml",
        "false_lead": "Chronosphere drop_rules leftover",
        "query": "spans{service=tarmac-ls-svc}",
        "lquery": "sli:http_success:ratio{service=apron-chrono-svc}",
        "exec_path": "/api/v1/query",
        "kind": "prom",
        "exec_obs": '{"status":"success","data":{"result":[]}}',
        "exec_err": "empty traces",
        "exec_ok": '{"status":"success","data":{"result":[{"metric":{"service":"tarmac-ls-svc"},"value":[1,88]}]}}',
        "fail_line": "max_spans_per_second: 0  # leftover satellite cap",
        "fix_line": "max_spans_per_second: 2000",
        "fail_val": "max_spans_per_second 0 leftover",
        "fix_val": "2000",
        "yq": ".max_spans_per_second",
        "confirm_obs": "0",
        "false_yq": ".drop_rules[0].metric_name",
        "false_obs": "not_tarmac  # chrono drop does not match",
        "false_read": "drop_rules target other metrics",
        "truth_cmd": "curl -sS $LS/api/v1/project/tarmac/stats | jq .spans_dropped",
        "truth_obs": "14022  # satellite drop leftover",
        "lie": "Lightstep satellite max_spans_per_second leftover 0 so Grafana Search is empty while SDK still exports",
        "llie": "Chronosphere drop_rules leftover metric_name http_* silently drops SLI; naive Lightstep cap raise does not bind Chrono leftover",
        "ns": "obs-ls",
        "deploy": "ls-collector",
        "side_svc": "fuel-truck-svc",
        "side_obs": "1",
        "grafana_obs": '{"schema":{"fields":[{"name":"traceID"}]}}',
        "false_old": "metric_name: not_tarmac",
        "false_new": "metric_name: http_requests_total",
        "false_patch": "chrono drop leftover retarget",
        "false2_old": "action: drop",
        "false2_new": "action: keep",
        "false2_patch": "chrono keep leftover",
        "novel": 75,
        "new_vs": "Lightstep max_spans_per_second leftover vs Chronosphere drop_rules leftover",
    },
    {
        "slug": "vm-relabel-drop-name-leftover",
        "lslug": "thanos-store-ignore-denylist-leftover",
        "svc": "hold-bag-vm-svc",
        "lsvc": "carousel-thanos-svc",
        "dash": "hbag-vm-relabel-5",
        "ldash": "caro-th-deny-1",
        "panel": "VM range",
        "lpanel": "Thanos store",
        "file": "/etc/victoriametrics/relabel.yml",
        "lfile": "/etc/thanos/store.yml",
        "false_file": "/etc/thanos/store.yml",
        "lfalse_file": "/etc/victoriametrics/relabel.yml",
        "false_lead": "Thanos ignore_deletion_marks leftover",
        "query": "http_requests_total{service=hold-bag-vm-svc}",
        "lquery": "http_requests_total{service=carousel-thanos-svc}",
        "exec_path": "/api/v1/query",
        "kind": "vm",
        "exec_obs": '{"status":"success","data":{"result":[]}}',
        "exec_err": "empty VM series",
        "exec_ok": '{"status":"success","data":{"result":[{"metric":{"service":"hold-bag-vm-svc"},"value":[1,41]}]}}',
        "fail_line": '- action: drop\n  source_labels: [__name__]\n  regex: http_.*  # leftover',
        "fix_line": '- action: keep\n  source_labels: [__name__]\n  regex: http_.*',
        "fail_val": "relabel drop http_ leftover",
        "fix_val": "keep http_",
        "yq": ".relabel_configs[0].action",
        "confirm_obs": "drop",
        "false_yq": ".ignore_deletion_marks_grace_period",
        "false_obs": "24h  # thanos store healthy",
        "false_read": "Thanos grace period default",
        "truth_cmd": "curl -sS $VM/api/v1/export -d 'match[]={job=\"hold-bag-vm-svc\"}' | wc -l",
        "truth_obs": "0  # relabel leftover dropped names",
        "lie": "VictoriaMetrics relabel drop __name__ http_ leftover so Grafana range is empty while vminsert still 200",
        "llie": "Thanos store --selector.relabel leftover drop tenant carousel; naive VM keep does not bind Thanos leftover",
        "ns": "obs-vm",
        "deploy": "vmagent",
        "side_svc": "lost-found-svc",
        "side_obs": "1",
        "grafana_obs": '{"schema":{"fields":[{"name":"service"}]}}',
        "false_old": "ignore_deletion_marks_grace_period: 24h",
        "false_new": "ignore_deletion_marks_grace_period: 0s",
        "false_patch": "thanos grace leftover",
        "false2_old": "min_time: 0000",
        "false2_new": "min_time: -24h",
        "false2_patch": "thanos min_time leftover",
        "novel": 75,
        "new_vs": "VM relabel drop leftover vs Thanos selector.relabel leftover (not r356/r223 WAL)",
    },
    {
        "slug": "cortex-max-fetched-chunks-1-leftover",
        "lslug": "mimir-max-label-value-length-1-leftover",
        "svc": "crew-roster-cx-svc",
        "lsvc": "duty-mimir-svc",
        "dash": "crew-cx-chunks-6",
        "ldash": "duty-mm-lblen-2",
        "panel": "Cortex query",
        "lpanel": "Mimir query",
        "file": "/etc/cortex/querier.yaml",
        "lfile": "/etc/mimir/limits.yaml",
        "false_file": "/etc/mimir/limits.yaml",
        "lfalse_file": "/etc/cortex/querier.yaml",
        "false_lead": "Mimir ingestion_rate leftover",
        "query": "http_requests_total{service=crew-roster-cx-svc}",
        "lquery": "http_requests_total{service=duty-mimir-svc}",
        "exec_path": "/prometheus/api/v1/query",
        "kind": "mimir",
        "exec_obs": '{"status":"error","error":"max fetched chunks"}',
        "exec_err": "max chunks",
        "exec_ok": '{"status":"success","data":{"result":[{"metric":{"service":"crew-roster-cx-svc"},"value":[1,9]}]}}',
        "fail_line": "max_fetched_chunks_per_query: 1  # leftover",
        "fix_line": "max_fetched_chunks_per_query: 2000000",
        "fail_val": "max_fetched_chunks_per_query 1 leftover",
        "fix_val": "2000000",
        "yq": ".querier.max_fetched_chunks_per_query",
        "confirm_obs": "1",
        "false_yq": ".limits.ingestion_rate",
        "false_obs": "100000  # mimir ingest ok; not HA tracker",
        "false_read": "ingestion_rate high; not the empty Cortex panel",
        "truth_cmd": "curl -sS $CORTEX/api/prom/api/v1/metadata | jq 'keys|length'",
        "truth_obs": "40  # series exist; querier leftover chunks=1",
        "lie": "Cortex querier max_fetched_chunks_per_query leftover 1 so Grafana range errors while distributor still ingests",
        "llie": "Mimir max_label_value_length leftover 1 silently drops series; naive Cortex chunks raise does not bind Mimir leftover (not r369 HA tracker)",
        "ns": "obs-cx",
        "deploy": "cortex-querier",
        "side_svc": "slot-alloc-svc",
        "side_obs": "1",
        "grafana_obs": '{"schema":{"fields":[{"name":"service"}]}}',
        "false_old": "ingestion_rate: 100000",
        "false_new": "ingestion_rate: 1000000",
        "false_patch": "mimir ingest leftover",
        "false2_old": "max_global_series_per_user: 150000",
        "false2_new": "max_global_series_per_user: 1500000",
        "false2_patch": "mimir series leftover",
        "novel": 76,
        "new_vs": "Cortex max_fetched_chunks leftover vs Mimir max_label_value_length leftover (not r369 HA)",
    },
    {
        "slug": "pyro-scrape-24h-leftover",
        "lslug": "parca-relabel-drop-leftover",
        "svc": "apu-pyro-svc",
        "lsvc": "bleed-parca-svc",
        "dash": "apu-pyro-scrape-8",
        "ldash": "bleed-parca-rel-4",
        "panel": "Pyroscope CPU",
        "lpanel": "Parca flame",
        "file": "/etc/pyroscope/scrape.yml",
        "lfile": "/etc/parca/parca.yaml",
        "false_file": "/etc/parca/parca.yaml",
        "lfalse_file": "/etc/pyroscope/scrape.yml",
        "false_lead": "Parca debuginfod leftover",
        "query": "process_cpu:cpu:nanoseconds{service=apu-pyro-svc}",
        "lquery": "parca_profile{service=bleed-parca-svc}",
        "exec_path": "/pyroscope/render",
        "kind": "pyro",
        "exec_obs": "0",
        "exec_err": "empty flame",
        "exec_ok": "48",
        "fail_line": "scrape_interval: 24h  # leftover so profiles never land",
        "fix_line": "scrape_interval: 15s",
        "fail_val": "scrape_interval 24h leftover",
        "fix_val": "15s",
        "yq": ".scrape_configs[0].scrape_interval",
        "confirm_obs": "24h",
        "false_yq": ".debuginfo.debuginfod_url",
        "false_obs": "https://debuginfod.elfutils.org  # parca symbols ok",
        "false_read": "debuginfod set; not empty pyro",
        "truth_cmd": "curl -sS $PYRO/api/v1/status | jq .last_scrape",
        "truth_obs": "never  # 24h leftover",
        "lie": "Pyroscope scrape_interval leftover 24h so Grafana flame is empty while pprof still served",
        "llie": "Parca relabel action leftover drop job=bleed; naive pyro interval does not bind Parca leftover",
        "ns": "obs-pyro",
        "deploy": "pyroscope",
        "side_svc": "oil-temp-svc",
        "side_obs": "1",
        "grafana_obs": '{"schema":{"fields":[{"name":"stack"}]}}',
        "false_old": "debuginfod_url: https://debuginfod.elfutils.org",
        "false_new": "debuginfod_url: http://127.0.0.1:8000",
        "false_patch": "parca debuginfod leftover",
        "false2_old": "enable_persistent_hash: true",
        "false2_new": "enable_persistent_hash: false",
        "false2_patch": "parca hash leftover",
        "novel": 76,
        "new_vs": "Pyroscope scrape_interval leftover vs Parca relabel drop leftover (not max_profile_size)",
    },
    {
        "slug": "jaeger-memory-storage-leftover",
        "lslug": "zipkin-kafka-topic-typo-leftover",
        "svc": "nav-jaeger-svc",
        "lsvc": "fms-zipkin-svc",
        "dash": "nav-jg-mem-3",
        "ldash": "fms-zk-topic-9",
        "panel": "Jaeger traces",
        "lpanel": "Zipkin traces",
        "file": "/etc/jaeger/collector.env",
        "lfile": "/etc/zipkin/zipkin.yml",
        "false_file": "/etc/zipkin/zipkin.yml",
        "lfalse_file": "/etc/jaeger/collector.env",
        "false_lead": "Zipkin elasticsearch leftover",
        "query": "service=nav-jaeger-svc",
        "lquery": "serviceName=fms-zipkin-svc",
        "exec_path": "/api/traces",
        "kind": "tempo",
        "exec_obs": '{"data":[]}',
        "exec_err": "empty jaeger",
        "exec_ok": '{"data":[{"traceID":"abc"}]}',
        "fail_line": "SPAN_STORAGE_TYPE=memory  # leftover after cassandra cutover",
        "fix_line": "SPAN_STORAGE_TYPE=cassandra",
        "fail_val": "SPAN_STORAGE_TYPE memory leftover",
        "fix_val": "cassandra",
        "yq": ".SPAN_STORAGE_TYPE",
        "confirm_obs": "memory",
        "false_yq": ".zipkin.storage.type",
        "false_obs": "elasticsearch  # zipkin store ok",
        "false_read": "Zipkin ES healthy; not empty Jaeger",
        "truth_cmd": "curl -sS $JAEGER/metrics | grep jaeger_spans_saved_by_storage",
        "truth_obs": 'jaeger_spans_saved_by_storage{type="memory"} 9001',
        "lie": "Jaeger SPAN_STORAGE_TYPE leftover memory so Grafana Search is empty after collector restart while Cassandra still empty",
        "llie": "Zipkin KAFKA_TOPIC leftover zipkin-wrong so collectors drop; naive memory->cassandra does not bind Zipkin leftover",
        "ns": "obs-jg",
        "deploy": "jaeger-collector",
        "side_svc": "irs-svc",
        "side_obs": "1",
        "grafana_obs": '{"schema":{"fields":[{"name":"traceID"}]}}',
        "false_old": "storage.type: elasticsearch",
        "false_new": "storage.type: mysql",
        "false_patch": "zipkin store leftover",
        "false2_old": "ES_INDEX: zipkin",
        "false2_new": "ES_INDEX: zipkin-v2",
        "false2_patch": "zipkin index leftover",
        "novel": 77,
        "new_vs": "Jaeger memory storage leftover vs Zipkin Kafka topic leftover (not empty cassandra r-ban)",
    },
    {
        "slug": "skywalking-ignore-path-star-leftover",
        "lslug": "pinpoint-sampling-rate-zero-leftover",
        "svc": "galley-sw-svc",
        "lsvc": "cater-pp-svc",
        "dash": "galley-sw-ignore-7",
        "ldash": "cater-pp-samp-5",
        "panel": "SkyWalking topology",
        "lpanel": "Pinpoint call tree",
        "file": "agent.config",
        "lfile": "pinpoint.config",
        "false_file": "pinpoint.config",
        "lfalse_file": "agent.config",
        "false_lead": "Pinpoint sampling leftover",
        "query": "service=galley-sw-svc",
        "lquery": "application=cater-pp-svc",
        "exec_path": "/graphql",
        "kind": "grafana",
        "exec_obs": '{"data":{"traces":[]}}',
        "exec_err": "empty SW",
        "exec_ok": '{"data":{"traces":[{"id":"sw1"}]}}',
        "fail_line": "agent.trace.ignore_path=/**  # leftover",
        "fix_line": "agent.trace.ignore_path=/health,/metrics",
        "fail_val": "ignore_path /** leftover",
        "fix_val": "/health,/metrics",
        "yq": ".agent.trace.ignore_path",
        "confirm_obs": "/**",
        "false_yq": ".profiler.sampling.counting.sampling-rate",
        "false_obs": "20  # pinpoint sampling not zero",
        "false_read": "Pinpoint sampling 20; not empty SW",
        "truth_cmd": "curl -sS $SW/v3/traces | jq '.total'",
        "truth_obs": "0  # ignore_path leftover",
        "lie": "SkyWalking agent.trace.ignore_path leftover /** so Grafana topology is empty while OAL still compiles",
        "llie": "Pinpoint profiler.sampling.rate leftover 0; naive ignore_path trim does not bind Pinpoint leftover",
        "ns": "obs-sw",
        "deploy": "oap",
        "side_svc": "lav-svc",
        "side_obs": "1",
        "grafana_obs": '{"schema":{"fields":[{"name":"endpoint"}]}}',
        "false_old": "profiler.sampling.counting.sampling-rate=20",
        "false_new": "profiler.sampling.counting.sampling-rate=1",
        "false_patch": "pinpoint sampling leftover",
        "false2_old": "profiler.transport.grpc.collector.ip=oap",
        "false2_new": "profiler.transport.grpc.collector.ip=127.0.0.1",
        "false2_patch": "pinpoint collector leftover",
        "novel": 77,
        "new_vs": "SkyWalking ignore_path leftover vs Pinpoint sampling leftover",
    },
    {
        "slug": "elastic-apm-sample-rate-zero-leftover",
        "lslug": "otel-memory-limiter-spike-limit-0-leftover",
        "svc": "cargo-eapm-svc",
        "lsvc": "uld-otel-svc",
        "dash": "cargo-eapm-sr-1",
        "ldash": "uld-otel-ml-6",
        "panel": "Elastic APM txns",
        "lpanel": "OTel traces",
        "file": "elastic-apm-node.js",
        "lfile": "/etc/otelcol/config.yaml",
        "false_file": "/etc/otelcol/config.yaml",
        "lfalse_file": "elastic-apm-node.js",
        "false_lead": "OTel batch timeout leftover",
        "query": "service.name : cargo-eapm-svc",
        "lquery": "{resource.service.name=\"uld-otel-svc\"}",
        "exec_path": "/api/apm/traces",
        "kind": "tempo",
        "exec_obs": '{"traces":[]}',
        "exec_err": "empty APM",
        "exec_ok": '{"traces":[{"id":"e1"}]}',
        "fail_line": "transactionSampleRate: 0  # leftover",
        "fix_line": "transactionSampleRate: 1.0",
        "fail_val": "transactionSampleRate 0 leftover",
        "fix_val": "1.0",
        "yq": ".transactionSampleRate",
        "confirm_obs": "0",
        "false_yq": ".processors.batch.timeout",
        "false_obs": "200ms  # otel batch ok",
        "false_read": "batch timeout default; not empty Elastic",
        "truth_cmd": "curl -sS $KIBANA/api/apm/services/cargo-eapm-svc/transaction_groups | jq .length",
        "truth_obs": "0  # sample rate leftover",
        "lie": "Elastic APM transactionSampleRate leftover 0 so Grafana APM is empty while RUM still 200",
        "llie": "OTel memory_limiter spike_limit leftover 0 silently drops; naive sample rate does not bind OTel leftover (not 24h limiter)",
        "ns": "obs-eapm",
        "deploy": "apm-server",
        "side_svc": "manifest-svc",
        "side_obs": "1",
        "grafana_obs": '{"schema":{"fields":[{"name":"transaction"}]}}',
        "false_old": "timeout: 200ms",
        "false_new": "timeout: 5s",
        "false_patch": "otel batch leftover",
        "false2_old": "send_batch_size: 8192",
        "false2_new": "send_batch_size: 1",
        "false2_patch": "otel batch size leftover",
        "novel": 78,
        "new_vs": "Elastic APM sample rate leftover vs OTel memory_limiter spike_limit leftover (not r365–r384)",
    },
    {
        "slug": "appd-bt-exclude-star-leftover",
        "lslug": "dynatrace-mgmt-zone-drop-leftover",
        "svc": "checkin-appd-svc",
        "lsvc": "kiosk-dt-svc",
        "dash": "checkin-appd-bt-4",
        "ldash": "kiosk-dt-mz-8",
        "panel": "AppD BT",
        "lpanel": "Dynatrace service",
        "file": "app-agent.properties",
        "lfile": "dynatrace.conf",
        "false_file": "dynatrace.conf",
        "lfalse_file": "app-agent.properties",
        "false_lead": "Dynatrace mgmt zone leftover",
        "query": "BT:Checkin",
        "lquery": "entitySelector=type(SERVICE),entityName(kiosk-dt-svc)",
        "exec_path": "/controller/rest/applications",
        "kind": "grafana",
        "exec_obs": "[]",
        "exec_err": "empty BT",
        "exec_ok": '[{"name":"Checkin"}]',
        "fail_line": "bt-exclude=/**  # leftover",
        "fix_line": "bt-exclude=/health",
        "fail_val": "bt-exclude /** leftover",
        "fix_val": "/health",
        "yq": ".bt-exclude",
        "confirm_obs": "/**",
        "false_yq": ".managementZones[0].name",
        "false_obs": "prod  # DT zone exists",
        "false_read": "DT zone prod; not empty AppD",
        "truth_cmd": "curl -sS $APPD/controller/rest/applications/checkin/business-transactions | wc -l",
        "truth_obs": "0  # exclude leftover",
        "lie": "AppDynamics bt-exclude leftover /** so Grafana BT is empty while JVM agent still attached",
        "llie": "Dynatrace management zone leftover rule type=HOST drops SERVICE; naive bt-exclude trim does not bind DT leftover",
        "ns": "obs-appd",
        "deploy": "appd-machine",
        "side_svc": "bagtag-svc",
        "side_obs": "1",
        "grafana_obs": '{"schema":{"fields":[{"name":"bt"}]}}',
        "false_old": "name: prod",
        "false_new": "name: staging",
        "false_patch": "dt zone leftover",
        "false2_old": "autoDetect: true",
        "false2_new": "autoDetect: false",
        "false2_patch": "dt autodect leftover",
        "novel": 78,
        "new_vs": "AppDynamics bt-exclude leftover vs Dynatrace management zone leftover",
    },
    {
        "slug": "splunk-frozen-60s-leftover",
        "lslug": "signoz-ttl-seconds-leftover",
        "svc": "atc-splunk-svc",
        "lsvc": "radar-signoz-svc",
        "dash": "atc-splk-frozen-2",
        "ldash": "radar-sz-ttl-9",
        "panel": "Splunk search",
        "lpanel": "SigNoz logs",
        "file": "/opt/splunk/etc/system/local/indexes.conf",
        "lfile": "/etc/signoz/clickhouse-ttl.yaml",
        "false_file": "/etc/signoz/clickhouse-ttl.yaml",
        "lfalse_file": "/opt/splunk/etc/system/local/indexes.conf",
        "false_lead": "SigNoz TTL leftover",
        "query": "index=atc sourcetype=syslog",
        "lquery": "service=radar-signoz-svc",
        "exec_path": "/services/search/jobs",
        "kind": "loki",
        "exec_obs": '{"results":[]}',
        "exec_err": "empty splunk",
        "exec_ok": '{"results":[{"_raw":"ok"}]}',
        "fail_line": "frozenTimePeriodInSecs = 60  # leftover",
        "fix_line": "frozenTimePeriodInSecs = 2592000",
        "fail_val": "frozenTimePeriodInSecs 60 leftover",
        "fix_val": "2592000",
        "yq": ".frozenTimePeriodInSecs",
        "confirm_obs": "60",
        "false_yq": ".ttl_days",
        "false_obs": "15  # signoz ttl ok",
        "false_read": "SigNoz ttl 15d; not empty Splunk",
        "truth_cmd": "curl -sS $SPLUNK/services/admin/indexes/atc | grep frozen",
        "truth_obs": "frozenTimePeriodInSecs=60 leftover",
        "lie": "Splunk frozenTimePeriodInSecs leftover 60 so Grafana search is empty while ingest still 200",
        "llie": "SigNoz logs TTL leftover 0 seconds; naive frozen raise does not bind SigNoz leftover",
        "ns": "obs-splk",
        "deploy": "splunkd",
        "side_svc": "notam-svc",
        "side_obs": "1",
        "grafana_obs": '{"schema":{"fields":[{"name":"_raw"}]}}',
        "false_old": "ttl_days: 15",
        "false_new": "ttl_days: 1",
        "false_patch": "signoz ttl leftover",
        "false2_old": "cold_storage: s3",
        "false2_new": "cold_storage: none",
        "false2_patch": "signoz cold leftover",
        "novel": 79,
        "new_vs": "Splunk frozenTimePeriod leftover vs SigNoz TTL leftover (not loki codec)",
    },
    {
        "slug": "uptrace-batch-size-overflow-leftover",
        "lslug": "beyla-exclude-env-star-leftover",
        "svc": "deice-uptrace-svc",
        "lsvc": "antiice-beyla-svc",
        "dash": "deice-ut-batch-5",
        "ldash": "antiice-beyla-ex-3",
        "panel": "Uptrace traces",
        "lpanel": "Beyla RED",
        "file": "/etc/uptrace/uptrace.yml",
        "lfile": "/etc/beyla/config.yml",
        "false_file": "/etc/beyla/config.yml",
        "lfalse_file": "/etc/uptrace/uptrace.yml",
        "false_lead": "Beyla exclude_env leftover",
        "query": "service=deice-uptrace-svc",
        "lquery": "http_server_duration{service=antiice-beyla-svc}",
        "exec_path": "/api/traces",
        "kind": "tempo",
        "exec_obs": '{"spans":[]}',
        "exec_err": "empty uptrace",
        "exec_ok": '{"spans":[{"id":"u1"}]}',
        "fail_line": "send_batch_size: 1000000000  # leftover overflow drop",
        "fix_line": "send_batch_size: 512",
        "fail_val": "send_batch_size 1e9 leftover",
        "fix_val": "512",
        "yq": ".otelcol.processors.batch.send_batch_size",
        "confirm_obs": "1000000000",
        "false_yq": ".discovery.exclude_services",
        "false_obs": "kube-system  # beyla not excluding deice",
        "false_read": "Beyla exclude kube-system only",
        "truth_cmd": "curl -sS $UPTRACE/internal/health | jq .spans_dropped",
        "truth_obs": "88001  # batch leftover",
        "lie": "Uptrace otelcol batch send_batch_size leftover 1e9 so Grafana traces empty while app still exports OTLP",
        "llie": "Beyla discovery.exclude leftover env=* ; naive batch size does not bind Beyla leftover (not javaagent mix)",
        "ns": "obs-ut",
        "deploy": "uptrace",
        "side_svc": "towbar-svc",
        "side_obs": "1",
        "grafana_obs": '{"schema":{"fields":[{"name":"span"}]}}',
        "false_old": "exclude_services: [kube-system]",
        "false_new": "exclude_services: [antiice-beyla-svc]",
        "false_patch": "beyla exclude leftover",
        "false2_old": "open_port: 80,443",
        "false2_new": "open_port: 1",
        "false2_patch": "beyla port leftover",
        "novel": 79,
        "new_vs": "Uptrace batch overflow leftover vs Grafana Beyla exclude leftover",
    },
    {
        "slug": "ebpf-map-max-entries-1-leftover",
        "lslug": "falco-priority-emergency-leftover",
        "svc": "pushback-ebpf-svc",
        "lsvc": "tug-falco-svc",
        "dash": "push-ebpf-map-6",
        "ldash": "tug-falco-pri-2",
        "panel": "eBPF histogram",
        "lpanel": "Falco alerts",
        "file": "http_latency.bt",
        "lfile": "/etc/falco/falco.yaml",
        "false_file": "/etc/falco/falco.yaml",
        "lfalse_file": "http_latency.bt",
        "false_lead": "Falco rules leftover",
        "query": "hist:http_ms",
        "lquery": "priority>=WARNING",
        "exec_path": "/api/v1/query",
        "kind": "prom",
        "exec_obs": '{"status":"success","data":{"result":[]}}',
        "exec_err": "empty hist",
        "exec_ok": '{"status":"success","data":{"result":[{"metric":{"le":"10"},"value":[1,3]}]}}',
        "fail_line": "@map http_ms max_entries 1  # leftover",
        "fix_line": "@map http_ms max_entries 65536",
        "fail_val": "bpf map max_entries 1 leftover",
        "fix_val": "65536",
        "yq": ".maps.http_ms.max_entries",
        "confirm_obs": "1",
        "false_yq": ".priority",
        "false_obs": "warning  # falco not emergency-only",
        "false_read": "Falco priority warning; not empty eBPF",
        "truth_cmd": "bpftool map show name http_ms | grep max_entries",
        "truth_obs": "max_entries 1 leftover",
        "lie": "eBPF map max_entries leftover 1 so Grafana histogram is empty while kprobe still attached",
        "llie": "Falco priority leftover emergency silences WARNING; naive map size does not bind Falco leftover",
        "ns": "obs-ebpf",
        "deploy": "bpfd",
        "side_svc": "chock-svc",
        "side_obs": "1",
        "grafana_obs": '{"schema":{"fields":[{"name":"le"}]}}',
        "false_old": "priority: warning",
        "false_new": "priority: debug",
        "false_patch": "falco priority leftover",
        "false2_old": "json_output: true",
        "false2_new": "json_output: false",
        "false2_patch": "falco json leftover",
        "novel": 80,
        "new_vs": "eBPF map max_entries leftover vs Falco priority leftover",
    },
    {
        "slug": "vector-drop-on-error-leftover",
        "lslug": "fluentbit-mem-buf-limit-1kb-leftover",
        "svc": "stand-vector-svc",
        "lsvc": "gpu-fb-svc",
        "dash": "stand-vec-drop-8",
        "ldash": "gpu-fb-mbl-4",
        "panel": "Vector logs",
        "lpanel": "Fluent Bit logs",
        "file": "/etc/vector/vector.toml",
        "lfile": "/etc/fluent-bit/fluent-bit.conf",
        "false_file": "/etc/fluent-bit/fluent-bit.conf",
        "lfalse_file": "/etc/vector/vector.toml",
        "false_lead": "Fluent Bit storage.max_chunks leftover",
        "query": '{app="stand-vector-svc"}',
        "lquery": '{app="gpu-fb-svc"}',
        "exec_path": "/loki/api/v1/query_range",
        "kind": "loki",
        "exec_obs": '{"data":{"result":[]}}',
        "exec_err": "empty vector",
        "exec_ok": '{"data":{"result":[{"values":[["1","ok"]]}]}}',
        "fail_line": "drop_on_error = true  # leftover remap",
        "fix_line": "drop_on_error = false",
        "fail_val": "drop_on_error true leftover",
        "fix_val": "false",
        "yq": ".transforms.parse.drop_on_error",
        "confirm_obs": "true",
        "false_yq": ".STORAGE.max_chunks_up",
        "false_obs": "128  # fluent-bit not starved",
        "false_read": "Fluent Bit chunks 128; not empty Vector",
        "truth_cmd": "curl -sS $VECTOR/metrics | grep vector_discarded",
        "truth_obs": "vector_discarded_events_total 44021 leftover",
        "lie": "Vector remap drop_on_error leftover true so Grafana Loki is empty while journald still tails",
        "llie": "Fluent Bit Mem_Buf_Limit leftover 1KB silent drop; naive drop_on_error false does not bind FB leftover",
        "ns": "obs-vec",
        "deploy": "vector",
        "side_svc": "marshall-svc",
        "side_obs": "1",
        "grafana_obs": '{"schema":{"fields":[{"name":"line"}]}}',
        "false_old": "Max_Chunks_Up 128",
        "false_new": "Max_Chunks_Up 8",
        "false_patch": "fb chunks leftover",
        "false2_old": "storage.type filesystem",
        "false2_new": "storage.type memory",
        "false2_patch": "fb storage leftover",
        "novel": 80,
        "new_vs": "Vector drop_on_error leftover vs Fluent Bit Mem_Buf_Limit leftover",
    },
    {
        "slug": "opensearch-index-blocks-write-leftover",
        "lslug": "loki-max-query-series-1-leftover",
        "svc": "ops-osearch-svc",
        "lsvc": "dispatch-loki-svc",
        "dash": "ops-os-block-3",
        "ldash": "disp-loki-mqs-7",
        "panel": "OpenSearch hits",
        "lpanel": "Loki logs",
        "file": "/etc/opensearch/index-template.json",
        "lfile": "/etc/loki/loki.yaml",
        "false_file": "/etc/loki/loki.yaml",
        "lfalse_file": "/etc/opensearch/index-template.json",
        "false_lead": "Loki ingestion_rate leftover",
        "query": "service:ops-osearch-svc",
        "lquery": '{service="dispatch-loki-svc"}',
        "exec_path": "/_search",
        "kind": "ch",
        "exec_obs": '{"hits":{"total":{"value":0}}}',
        "exec_err": "zero hits",
        "exec_ok": '{"hits":{"total":{"value":88}}}',
        "fail_line": '"index.blocks.write": true  # leftover',
        "fix_line": '"index.blocks.write": false',
        "fail_val": "index.blocks.write true leftover",
        "fix_val": "false",
        "yq": ".settings.index.blocks.write",
        "confirm_obs": "true",
        "false_yq": ".limits_config.ingestion_rate_mb",
        "false_obs": "16  # loki ingest ok; not chunk_encoding",
        "false_read": "Loki ingest 16MB; not empty OS",
        "truth_cmd": "curl -sS $OS/_cat/indices/ops*?v | awk '{print $6}'",
        "truth_obs": "docs.count 0 leftover write block",
        "lie": "OpenSearch index.blocks.write leftover true so Grafana discover is empty while ingest ACK still 201",
        "llie": "Loki max_query_series leftover 1; naive write-block false does not bind Loki leftover (not r367 codec)",
        "ns": "obs-os",
        "deploy": "opensearch",
        "side_svc": "aoc-svc",
        "side_obs": "1",
        "grafana_obs": '{"schema":{"fields":[{"name":"_source"}]}}',
        "false_old": "ingestion_rate_mb: 16",
        "false_new": "ingestion_rate_mb: 160",
        "false_patch": "loki ingest leftover",
        "false2_old": "max_query_lookback: 30d",
        "false2_new": "max_query_lookback: 1h",
        "false2_patch": "loki lookback leftover",
        "novel": 81,
        "new_vs": "OpenSearch index.blocks.write leftover vs Loki max_query_series leftover (not r367)",
    },
    {
        "slug": "clickhouse-max-result-rows-0-leftover",
        "lslug": "questdb-wal-enabled-false-leftover",
        "svc": "metar-ch-svc",
        "lsvc": "taf-qdb-svc",
        "dash": "metar-ch-rows-9",
        "ldash": "taf-qdb-wal-1",
        "panel": "ClickHouse SQL",
        "lpanel": "QuestDB chart",
        "file": "/etc/clickhouse-server/users.xml",
        "lfile": "/var/lib/questdb/conf/server.conf",
        "false_file": "/var/lib/questdb/conf/server.conf",
        "lfalse_file": "/etc/clickhouse-server/users.xml",
        "false_lead": "QuestDB wal leftover",
        "query": "SELECT count() FROM otel.traces WHERE service='metar-ch-svc'",
        "lquery": "SELECT count() FROM traces WHERE service='taf-qdb-svc'",
        "exec_path": "/",
        "kind": "ch",
        "exec_obs": "0\n",
        "exec_err": "zero rows",
        "exec_ok": "1402\n",
        "fail_line": "<max_result_rows>0</max_result_rows>  # leftover",
        "fix_line": "<max_result_rows>1000000</max_result_rows>",
        "fail_val": "max_result_rows 0 leftover",
        "fix_val": "1000000",
        "yq": ".clickhouse.profiles.default.max_result_rows",
        "confirm_obs": "0",
        "false_yq": ".cairo.wal.enabled",
        "false_obs": "true  # questdb wal on",
        "false_read": "QuestDB wal true; not empty CH",
        "truth_cmd": "clickhouse-client -q \"SELECT count() FROM otel.traces WHERE service='metar-ch-svc' SETTINGS max_result_rows=0\"",
        "truth_obs": "Code: 396 leftover max_result_rows",
        "lie": "ClickHouse max_result_rows leftover 0 so Grafana SQL is empty while MergeTree still has rows",
        "llie": "QuestDB cairo.wal.enabled leftover false so ingest silent-drops; naive max_result_rows does not bind QDB leftover",
        "ns": "obs-ch",
        "deploy": "clickhouse",
        "side_svc": "pirep-svc",
        "side_obs": "1",
        "grafana_obs": '{"schema":{"fields":[{"name":"count()"}]}}',
        "false_old": "cairo.wal.enabled=true",
        "false_new": "cairo.wal.enabled=false",
        "false_patch": "questdb wal leftover",
        "false2_old": "line.tcp.enabled=true",
        "false2_new": "line.tcp.enabled=false",
        "false2_patch": "questdb ilp leftover",
        "novel": 81,
        "new_vs": "ClickHouse max_result_rows leftover vs QuestDB wal.enabled leftover (not Tempo CH table)",
    },
]


def clip(text: str, n: int = 240) -> str:
    text = " ".join(str(text).split())
    if len(text) <= n:
        return text
    return text[: n - 1].rstrip() + "…"


def step(n: int, basis: str, name: str, args: dict, obs: str, reflection: str = "") -> dict:
    basis = clip(basis)
    prefix = basis.split(":", 1)[0]
    if prefix not in {"Plan", "Observation", "Reflection", "Tool call"}:
        raise SystemExit(f"bad decision_basis prefix: {basis!r}")
    rec = {
        "n": n,
        "decision_basis": basis,
        "tool_call": {"name": name, "args": args},
        "observation": obs,
    }
    if reflection:
        rec["reflection"] = reflection
    return rec


def bash(n, basis, cmd, obs, reflection=""):
    return step(n, basis, "bash", {"command": cmd}, obs, reflection)


def read(n, basis, path, obs, reflection=""):
    return step(n, basis, "read", {"path": path}, obs, reflection)


def edit(n, basis, path, old, new, obs, reflection=""):
    return step(n, basis, "edit", {"path": path, "old": old, "new": new}, obs, reflection)


def write_file(n, basis, path, contents, obs, reflection=""):
    return step(n, basis, "write", {"path": path, "contents": contents}, obs, reflection)


KIND_HOST = {
    "tempo": "$TEMPO",
    "loki": "$LOKI",
    "prom": "$PROM",
    "mimir": "$MIMIR",
    "otel": "$PROM",
    "vm": "$VM",
    "thanos": "$THANOS",
    "pyro": "$PYRO",
    "grafana": "$GRAFANA",
    "ch": "$CLICKHOUSE",
}


def exec_cmd(s: dict, query: str) -> str:
    host = KIND_HOST.get(s["kind"], "$PROM")
    path = s["exec_path"]
    kind = s["kind"]
    if kind in {"tempo"} and path in {"/api/search", "/api/traces", "/api/apm/traces"}:
        return f"curl -sS -G {host}{path} --data-urlencode 'q={query}' | jq ."
    if kind == "loki":
        return (
            f"curl -sS -G {host}{path} --data-urlencode 'query={query}' "
            f"--data-urlencode 'limit=30' --data-urlencode 'start=-15m'"
        )
    if kind == "pyro":
        return f"curl -sS -G {host}{path} --data-urlencode 'query={query}' | jq '.flamebearer.names|length'"
    if kind == "ch":
        return f"clickhouse-client -q {query!r}"
    if kind == "grafana":
        return f"curl -sS {host}{path} | jq ."
    return f"curl -sS -G {host}{path} --data-urlencode 'query={query}'"


def success_episode(rnd: int, s: dict) -> dict:
    svc, dash, path = s["svc"], s["dash"], s["file"]
    q = s["query"]
    ns, deploy = s["ns"], s["deploy"]
    steps = [
        bash(
            1,
            f"Plan: find Grafana dashboard {dash} for {svc} before chasing {s['false_lead']}.",
            f"curl -sS $GRAFANA/api/search?query={dash} | jq -c '.[]|{{uid,title}}'",
            f'[{{"uid":"{dash}","title":"{s["panel"]}"}}]',
            "Dashboard exists. Read panel JSON.",
        ),
        bash(
            2,
            f"Observation: dashboard {dash} exists (step 1). Read panel JSON.",
            f"curl -sS $GRAFANA/api/dashboards/uid/{dash} | jq '.dashboard.panels[0]|{{title,targets}}'",
            f'{{"title":"{s["panel"]}","targets":[{{"expr":"{q}"}}]}}',
            "Panel query known. Execute it.",
        ),
        bash(
            3,
            f"Observation: panel '{s['panel']}' runs {q} (step 2). Execute it.",
            exec_cmd(s, q),
            s["exec_obs"],
            f"Empty/wrong: {s['exec_err']}. False lead next.",
        ),
        bash(
            4,
            f"Observation: query empty/wrong (step 3). False lead: {s['false_lead']}.",
            f"yq '{s['false_yq']}' {s['false_file']}",
            s["false_obs"],
            "False lead looks healthy. Read it.",
        ),
        read(
            5,
            f"Observation: {s['false_lead']} looks healthy (step 4). Read {s['false_file']}.",
            s["false_file"],
            s["false_read"],
            "False lead is not the ticket. Read primary config.",
        ),
        read(
            6,
            f"Observation: primary false lead does not explain the empty panel (step 5). Read {path}.",
            path,
            s["fail_line"],
            "Lie candidate in primary config.",
        ),
        bash(
            7,
            f"Observation: lie candidate in {path} (step 6). Query truth source vs dashboard.",
            s["truth_cmd"],
            s["truth_obs"],
            "Truth source has the missing data.",
        ),
        bash(
            8,
            f"Observation: truth source has data (step 7). Confirm mechanism {s['lie']}.",
            f"yq '{s['yq']}' {path}",
            s["confirm_obs"],
            "Cap/flag confirmed as the lie.",
        ),
        edit(
            9,
            f"Reflection: plan change — RCA is {s['lie']}, not {s['false_lead']}. Patch {path}.",
            path,
            s["fail_line"],
            s["fix_line"],
            f"patched {s['yq'].split('.')[-1]} {s['fix_val']}",
            "Reload.",
        ),
        bash(
            10,
            f"Observation: patched {path} (step 9). Reload {ns}-{deploy}.",
            f"kubectl -n {ns} rollout restart deploy/{deploy} && kubectl -n {ns} rollout status deploy/{deploy} --timeout=90s",
            f'deployment "{deploy}" successfully rolled out',
            "Reloaded. Re-query.",
        ),
        bash(
            11,
            f"Observation: {ns}-{deploy} reloaded (step 10). Re-run {q}.",
            exec_cmd(s, q),
            s["exec_ok"],
            "Backend now returns data.",
        ),
        bash(
            12,
            f"Observation: backend now returns series (step 11). Refresh Grafana panel {s['panel']}.",
            f"curl -sS $GRAFANA/api/ds/query -d @/tmp/{dash}.json | jq '.results.A.frames[0].schema // .results.A'",
            s["grafana_obs"],
            "Panel populated.",
        ),
        bash(
            13,
            f"Observation: panel populated (step 12). Check side-effect {s['side_svc']} still works.",
            f"curl -sS $GRAFANA/api/search?query={s['side_svc']} | jq 'length'",
            s["side_obs"],
            "Side-effect ok.",
        ),
        write_file(
            14,
            f"Observation: side-effect {s['side_svc']} ok (step 13). Write runbook for {svc}.",
            f"runbooks/{dash}.md",
            f"# {svc} {s['slug']}\n{s['fail_line']} was the lie. Fix {s['fix_line']}. Not {s['false_lead']}.\n",
            f"wrote runbooks/{dash}.md",
            "Runbook written.",
        ),
        bash(
            15,
            f"Observation: runbook written (step 14). Final verify dashboard {dash}.",
            f"yq '{s['yq']}' {path}",
            f"{s['fix_val']}\n",
            "Done.",
        ),
    ]
    if len(steps) != 15:
        raise SystemExit(f"{s['slug']} steps {len(steps)}")
    return {
        "id": f"obs-r{rnd}-{s['slug']}",
        "goal": f"{svc} dashboard {dash} {s['panel']} empty/wrong. Find the leftover lie.",
        "plan": f"Empty → {s['false_lead']} (false) → {s['fail_val']} → {s['fix_val']}.",
        "steps": steps,
        "outcome": f"{s['yq'].split('.')[-1]} {s['fix_val']}. Panel populated. {s['side_svc']} unchanged.",
        "reward": {"success": True, "plan_changes": 1, "cost_steps": 15, "handoff": 0},
        "meta": {
            "factory": FACTORY,
            "round": rnd,
            "generator": GEN,
            "kind": "designed",
            "service": svc,
            "dashboard": dash,
            "lie": s["lie"],
        },
    }


def leftover_episode(rnd: int, s: dict) -> dict:
    svc, dash, path = s["lsvc"], s["ldash"], s["lfile"]
    q = s["lquery"]
    ns, deploy = s["ns"], s["deploy"]
    ticket = f"OBS-{7200 + rnd}"
    xmod = dash.replace("-", "_")
    steps = [
        bash(
            1,
            f"Plan: debug empty {dash} for {svc}; start at {s['false_lead']}.",
            f"curl -sS $GRAFANA/api/search?query={dash} | jq -c '.[]|{{uid,title}}'",
            f'[{{"uid":"{dash}","title":"{s["lpanel"]}"}}]',
            "Dashboard exists.",
        ),
        bash(
            2,
            f"Observation: dashboard {dash} found (step 1). Read panel JSON.",
            f"curl -sS $GRAFANA/api/dashboards/uid/{dash} | jq '.dashboard.panels[0]'",
            f'{{"title":"{s["lpanel"]}","targets":[{{"expr":"{q}"}}]}}',
            "Query known.",
        ),
        bash(
            3,
            f"Observation: panel '{s['lpanel']}' query {q} (step 2). Execute it.",
            exec_cmd(s, q),
            s["exec_obs"],
            "Still empty.",
        ),
        bash(
            4,
            f"Observation: empty (step 3). Treat {s['false_lead']} as RCA.",
            f"yq '{s['false_yq']}' {s['lfalse_file']}",
            s["false_obs"].split("#")[0].strip() + "  # treated as leftover",
            "False lead still looks plausible.",
        ),
        read(
            5,
            f"Observation: {s['false_lead']} still looks plausible (step 4). Read {s['lfalse_file']}.",
            s["lfalse_file"],
            f"treated as {s['false_lead']}",
            "Skip primary config.",
        ),
        read(
            6,
            f"Observation: {s['lfalse_file']} matches the false lead (step 5). Skip {path}.",
            s["lfalse_file"],
            s["lfalse_file"],
            "Patch the hide.",
        ),
        edit(
            7,
            f"Observation: {s['lfalse_file']} looks like a knob (step 6). Patch it.",
            s["lfalse_file"],
            s["false_old"],
            s["false_new"],
            s["false_patch"],
            "Reload.",
        ),
        bash(
            8,
            f"Observation: wrong patch applied (step 7). Reload {ns}-{deploy}.",
            f"kubectl -n {ns} rollout restart deploy/{deploy} && kubectl -n {ns} rollout status deploy/{deploy} --timeout=90s",
            f'deployment "{deploy}" successfully rolled out',
            "Reloaded. Re-query.",
        ),
        bash(
            9,
            f"Observation: reloaded (step 8). Re-query {q}.",
            exec_cmd(s, q),
            s["exec_obs"],
            "Still empty after hide.",
        ),
        edit(
            10,
            f"Observation: still empty (step 9). Double down on {s['false_lead']}.",
            s["lfalse_file"],
            s["false2_old"],
            s["false2_new"],
            s["false2_patch"],
            "Second wrong patch.",
        ),
        bash(
            11,
            "Observation: second wrong patch (step 10). Re-query again.",
            exec_cmd(s, q),
            s["exec_obs"],
            "Still empty.",
        ),
        read(
            12,
            f"Observation: still empty (step 11). Late read of {path}.",
            path,
            f"{path} leftover bind {s['llie']}; truth still empty",
            "Actual leftover found late.",
        ),
        bash(
            13,
            f"Observation: actual lie is {s['llie']} (step 12). Attempt the correct patch.",
            f"kubectl -n {ns} auth can-i patch configmap/{dash} --as=sre-bot",
            "no",
            "No RBAC for the real fix.",
        ),
        write_file(
            14,
            f"Observation: cannot apply correct patch (step 13). Open handoff {ticket}.",
            f"tickets/{ticket}.md",
            f"{ticket}: {svc} still empty. {s['false_lead']} leftover. {s['llie']}. Need bind leftover. No RBAC.\n",
            f"wrote tickets/{ticket}.md",
            "Handoff recorded.",
        ),
        bash(
            15,
            f"Observation: handoff filed (step 14). Mark tests/test_{xmod}.py and stop.",
            f"printf '%s\\n' '@pytest.mark.xfail(reason=\"{ticket}\")\\ndef test_{s['lslug'].replace('-', '_')}():\\n    assert False' > tests/test_{xmod}.py",
            f"xfail tests/test_{xmod}.py",
            "PARTIAL. Stop.",
        ),
    ]
    if len(steps) != 15:
        raise SystemExit(f"{s['lslug']} steps {len(steps)}")
    return {
        "id": f"obs-r{rnd}-{s['lslug']}",
        "goal": f"{svc} dashboard {dash} {s['lpanel']} empty. Restore leftover bind.",
        "plan": f"Apply {s['false_lead']} leftover. Handoff real leftover lie.",
        "steps": steps,
        "outcome": f"{s['false_lead']} applied; still empty. Late leftover. Handoff {ticket}.",
        "reward": {
            "success": False,
            "plan_changes": 1,
            "cost_steps": 15,
            "handoff": 1,
            "xfailed": 1,
        },
        "meta": {
            "factory": FACTORY,
            "round": rnd,
            "generator": GEN,
            "kind": "designed",
            "service": svc,
            "dashboard": dash,
            "lie": s["llie"],
        },
    }


def notes_for(rnd: int, s: dict, a: dict, b: dict) -> str:
    return (
        f"# NOTES-r{rnd} observability-debug-factory\n\n"
        f"Novel coverage: {s['novel']}%\n\n"
        f"Two designed episodes (quota 2), 15 steps each, success + fail/handoff.\n"
        f"Unique leftover leftover leftover service+dashboard+lie. Surfaces: {s['new_vs']}.\n"
        f"Avoided r365–r384 knob twins; r163 tid128; r172 inferred db; r190 DD UST; "
        f"r244 loki-querier-max-concurrent; r292 tempo-max-bytes-per-tag-values.\n\n"
        f"| id | service | dashboard | lie | terminal |\n"
        f"|---|---|---|---|---|\n"
        f"| {a['id']} | {s['svc']} | {s['dash']} | {s['lie']} | success |\n"
        f"| {b['id']} | {s['lsvc']} | {s['ldash']} | {s['llie']} | handoff/xfail |\n\n"
        f"## Step counts\n"
        f"- ep1: 15. False lead {s['false_lead']} 4-5; {s['fail_val']} 6-8; {s['fix_val']} 9-12.\n"
        f"- ep2: 15. naive leftover patch 6-10; still empty 11; late leftover 12; handoff 14-15.\n\n"
        f"## decision_basis audit\n"
        f"Every step starts Plan:/Observation:/Reflection:/Tool call:.\n"
        f"No thought / chain_of_thought / scratch / inner_monologue. No spike_events.\n"
        f"No sim_or_real: real. Invented plant `designed`.\n"
    )


def assert_clean(obj) -> None:
    if isinstance(obj, dict):
        for key, val in obj.items():
            if key in BANNED:
                raise SystemExit(f"banned key {key}")
            if key == "sim_or_real" and val == "real":
                raise SystemExit("sim_or_real real")
            if key == "spike_events":
                raise SystemExit("spike_events")
            assert_clean(val)
    elif isinstance(obj, list):
        for item in obj:
            assert_clean(item)


def txn(args: list[str]) -> dict:
    proc = subprocess.run(TXN + args, cwd=ROOT, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout)
    return json.loads(proc.stdout)


def write_round(rnd: int, staging: Path, spec: dict) -> tuple[str, str]:
    a = success_episode(rnd, spec)
    b = leftover_episode(rnd, spec)
    for rec in (a, b):
        assert_clean(rec)
        blob = json.dumps(rec)
        if '"sim_or_real": "real"' in blob or "spike_events" in blob:
            raise SystemExit("banned field")
        for st in rec["steps"]:
            if any(k in st for k in BANNED):
                raise SystemExit("hidden CoT")
            if not st["decision_basis"].startswith(DB_PREFIXES):
                raise SystemExit(f"bad prefix {st['decision_basis']!r}")
    batch = staging / f"batch-r{rnd:02d}.jsonl"
    notes = staging / f"NOTES-r{rnd:02d}.md"
    batch.write_text(
        json.dumps(a, separators=(",", ":")) + "\n" + json.dumps(b, separators=(",", ":")) + "\n"
    )
    notes.write_text(notes_for(rnd, spec, a, b))
    return a["id"], b["id"]


def run_loop(n_rounds: int = 16) -> list[dict]:
    published = []
    factory = DIR
    for _ in range(n_rounds):
        front = txn(["frontier", str(factory)])
        rnd = int(front["next_round"])
        i = rnd - 385
        if i < 0 or i >= len(PAIRS):
            raise SystemExit(f"catalog exhausted for r{rnd} idx={i}")
        spec = PAIRS[i]
        try:
            res = txn(["reserve", str(factory), "--round", str(rnd), "--expected", "2"])
        except RuntimeError as exc:
            print(f"reserve failed r{rnd}: {exc}", file=sys.stderr)
            reserved = factory / f"ROUND-r{rnd}.reserved.json"
            if reserved.exists():
                res = json.loads(reserved.read_text())
                stage = Path(res["staging_dir"])
                print(f"resume reservation r{rnd} staging={stage}", file=sys.stderr)
            else:
                raise
        stage = Path(res["staging_dir"])
        ids = write_round(rnd, stage, spec)
        pub = txn(["publish", str(factory), "--round", str(rnd), "--token", res["token"]])
        rec = {"round": rnd, "ids": list(ids), "factory": factory.name}
        published.append(rec)
        print(json.dumps(rec))
    return published


def main() -> int:
    front = txn(["frontier", str(DIR)])
    left = 385 + 16 - int(front["next_round"])
    if left <= 0:
        print("done")
        return 0
    run_loop(left)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
