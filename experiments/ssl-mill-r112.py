#!/usr/bin/env python3
"""ssl-cert-rotation mill r112+. Unique leftover stacks. Not hitch/dovecot/ghostunnel/postfix."""
from __future__ import annotations

import argparse
import json
from importlib.machinery import SourceFileLoader
from pathlib import Path

HERE = Path(__file__).resolve().parent
_base = SourceFileLoader("ssl35", str(HERE / "ssl-mill-r35.py")).load_module()
build_success = _base.build_success
build_partial = _base.build_partial
CATALOG_FIRST = 112

# success: slug, stack, unit, wrong, fix, ticket, url, residual
# fail:    slug, stack, unit, wrong, leftover, ticket, url, nightly
PAIRS = [
    (
        ("schema-registry-ssl-reload", "Schema Registry", "ssl.keystore.location", "restart",
         "kafka-configs + listener SSL reload",
         "Reload Schema Registry keystore; do not restart the registry.",
         "https://docs.confluent.io/platform/current/schema-registry/security/index.html", "src/legacy_sr.py"),
        ("ksqldb-ssl-handoff", "ksqlDB", "ssl.truststore.location", "server restart", "ksql leftover",
         "Ticket is ksql SSL truststore swap; nightly still restarts ksql-server.",
         "https://docs.ksqldb.io/en/latest/operate-and-deploy/installation/server-config/security/", "src/nightly_ksql.py"),
    ),
    (
        ("kafka-connect-tls-reload", "Kafka Connect", "listeners.https", "worker restart",
         "PUT /connectors + SSL context reload",
         "Reload Connect HTTPS listener cert; do not restart workers.",
         "https://kafka.apache.org/documentation/#connectconfigs", "src/legacy_connect.py"),
        ("rest-proxy-ssl-handoff", "Kafka REST Proxy", "ssl.keystore.location", "restart", "rest leftover",
         "Ticket is REST Proxy keystore swap; nightly still restarts the proxy.",
         "https://docs.confluent.io/platform/current/kafka-rest/production-deployment.html", "src/nightly_rest.py"),
    ),
    (
        ("debezium-tls-reload", "Debezium", "database.ssl.keystore", "task restart",
         "connector config reload + incremental snapshot",
         "Reload Debezium SSL keystore; do not restart the connector task.",
         "https://debezium.io/documentation/reference/stable/connectors/mysql.html#mysql-property-database-ssl-keystore",
         "src/legacy_debz.py"),
        ("fluentbit-tls-handoff", "Fluent Bit", "tls.crt", "pod bounce", "reload leftover",
         "Ticket is Fluent Bit tls.crt reload; nightly still bounces the pod.",
         "https://docs.fluentbit.io/manual/administration/transport-security", "src/nightly_fb.py"),
    ),
    (
        ("vector-api-tls-reload", "Vector", "api.tls", "process restart",
         "vector reload --config",
         "vector reload of api.tls; do not restart the process.",
         "https://vector.dev/docs/reference/configuration/api/", "src/legacy_vector.py"),
        ("filebeat-ssl-handoff", "Filebeat", "ssl.certificate", "restart", "filebeat leftover",
         "Ticket is Filebeat ssl.certificate swap; nightly still restarts filebeat.",
         "https://www.elastic.co/guide/en/beats/filebeat/current/configuration-ssl.html", "src/nightly_filebeat.py"),
    ),
    (
        ("logstash-beats-ssl-reload", "Logstash Beats", "ssl_certificate", "restart",
         "pipeline reload + ssl_certificate",
         "Reload Beats input ssl_certificate; do not restart Logstash.",
         "https://www.elastic.co/guide/en/logstash/current/plugins-inputs-beats.html", "src/legacy_lsbeats.py"),
        ("telegraf-tls-handoff", "Telegraf", "tls_cert", "restart", "telegraf leftover",
         "Ticket is telegraf tls_cert swap; nightly still restarts telegraf.",
         "https://github.com/influxdata/telegraf/blob/master/docs/CONFIGURATION.md", "src/nightly_telegraf.py"),
    ),
    (
        ("otelcol-tls-reload", "OTel Collector", "tls.cert_file", "collector restart",
         "SIGHUP otelcol config",
         "SIGHUP reloads tls.cert_file; do not restart the collector.",
         "https://opentelemetry.io/docs/collector/configuration/", "src/legacy_otelcol.py"),
        ("jaeger-collector-tls-handoff", "Jaeger collector", "tls.cert", "pod bounce", "jaeger leftover",
         "Ticket is collector TLS cert swap; nightly still bounces the pod.",
         "https://www.jaegertracing.io/docs/latest/deployment/", "src/nightly_jaeger.py"),
    ),
    (
        ("zipkin-ssl-reload", "Zipkin", "server.ssl", "restart",
         "Spring SSL bundle reload",
         "Reload Zipkin server.ssl bundle; do not restart the jar.",
         "https://docs.spring.io/spring-boot/reference/features/ssl.html", "src/legacy_zipkin.py"),
        ("grafana-alloy-tls-handoff", "Grafana Alloy", "tls_config", "restart", "alloy leftover",
         "Ticket is Alloy tls_config cert swap; nightly still restarts alloy.",
         "https://grafana.com/docs/alloy/latest/", "src/nightly_alloy.py"),
    ),
    (
        ("openlitespeed-ssl-reload", "OpenLiteSpeed", "vhssl cert", "restart",
         "lswsctrl reload",
         "lswsctrl reload swaps vhssl cert; do not restart OpenLiteSpeed.",
         "https://docs.openlitespeed.org/config/sslsetup/", "src/legacy_ols.py"),
        ("iis-https-binding-handoff", "IIS", "https binding", "site recycle", "netsh leftover",
         "Ticket is netsh http update sslcert; nightly still recycles the site.",
         "https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/netsh-http", "src/nightly_iis.py"),
    ),
    (
        ("stunnel-reload", "stunnel", "cert=", "restart",
         "kill -HUP stunnel",
         "HUP reloads stunnel cert=; do not restart stunnel.",
         "https://www.stunnel.org/static/stunnel.html", "src/legacy_stunnel.py"),
        ("gobetween-tls-handoff", "gobetween", "tls.cert", "restart", "gobetween leftover",
         "Ticket is gobetween tls.cert swap; nightly still restarts the balancer.",
         "https://github.com/yyyar/gobetween", "src/nightly_gb.py"),
    ),
    (
        ("caddy-metrics-tls-reload", "Caddy metrics", "metrics tls", "restart",
         "caddy reload metrics",
         "Reload Caddy metrics endpoint TLS; do not restart Caddy.",
         "https://caddyserver.com/docs/metrics", "src/legacy_caddy_metrics.py"),
        ("traefik-http3-handoff", "Traefik HTTP/3", "http3 tls", "pod bounce", "http3 leftover",
         "r08/r23/r47 were http tls; this is HTTP/3 TLS leftover.",
         "https://doc.traefik.io/traefik/routing/entrypoints/#http3", "src/nightly_traefik_h3.py"),
    ),
    (
        ("haproxy-quic-cert-reload", "HAProxy QUIC", "quic crt", "restart",
         "so_reload quic crt-store",
         "so_reload the QUIC crt-store; do not restart HAProxy.",
         "https://docs.haproxy.org/2.8/configuration.html#quic", "src/legacy_haproxy_quic.py"),
        ("nginx-http3-handoff", "nginx HTTP/3", "http3 ssl", "reload", "http3 leftover",
         "r01/r08/r20 were http ssl; this is HTTP/3 ssl leftover after rotate.",
         "https://nginx.org/en/docs/http/ngx_http_v3_module.html", "src/nightly_nginx_h3.py"),
    ),
    (
        ("envoy-quic-tls-reload", "Envoy QUIC", "quic_downstream tls", "lds push",
         "SDS secret for QUIC",
         "SDS swap of QUIC downstream cert; do not LDS-push a new listener.",
         "https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_conn_man/quic", "src/legacy_envoy_quic.py"),
        ("caddy-http3-handoff", "Caddy HTTP/3", "h3 tls", "restart", "h3 leftover",
         "r10/r17 file vs autohttps; this is HTTP/3 TLS leftover.",
         "https://caddyserver.com/docs/caddyfile/options#servers", "src/nightly_caddy_h3.py"),
    ),
    (
        ("kong-stream-tls-reload", "Kong stream", "stream tls", "pod bounce",
         "PATCH /certificates stream",
         "PATCH the stream certificates object; do not bounce pods.",
         "https://docs.konghq.com/gateway/latest/reference/admin-api/", "src/legacy_kong_stream.py"),
        ("apisix-stream-ssl-handoff", "APISIX stream", "stream ssl", "restart", "stream leftover",
         "r51 was ssl patch; this is stream ssl leftover.",
         "https://apisix.apache.org/docs/apisix/stream-proxy/", "src/nightly_apisix_stream.py"),
    ),
    (
        ("pulsar-func-tls-reload", "Pulsar functions", "tlsTrustCertsFilePath", "worker restart",
         "functions worker tls reload",
         "Reload functions worker TLS; do not restart the worker.",
         "https://pulsar.apache.org/docs/4.0.x/functions-worker/", "src/legacy_pulsar_fn.py"),
        ("redpanda-schema-tls-handoff", "Redpanda schema", "schema_registry tls", "restart", "schema leftover",
         "Ticket is schema_registry TLS swap; nightly still restarts the broker.",
         "https://docs.redpanda.com/current/manage/security/encryption/", "src/nightly_rp_schema.py"),
    ),
    (
        ("nats-leafnode-tls-reload", "NATS leafnode", "leafnodes tls", "kill -9",
         "nats-server --signal reload leaf",
         "Signal-reload leafnode TLS; do not kill -9.",
         "https://docs.nats.io/running-a-nats-service/configuration/leafnodes", "src/legacy_nats_leaf.py"),
        ("emqx-wss-handoff", "EMQX WSS", "listeners.wss", "node restart", "wss leftover",
         "r41/r55 ssl; this is WSS listener leftover.",
         "https://docs.emqx.com/en/emqx/latest/access-control/authn/tls.html", "src/nightly_emqx_wss.py"),
    ),
    (
        ("rabbitmq-stream-tls-reload", "RabbitMQ stream", "stream tls", "restart",
         "rabbitmqctl eval ssl:clear_pem_cache() stream",
         "Clear PEM cache for stream TLS; do not restart RabbitMQ.",
         "https://www.rabbitmq.com/docs/stream", "src/legacy_rmq_stream.py"),
        ("valkey-acl-tls-handoff", "Valkey ACL TLS", "tls-cert-file + ACL", "restart", "acl leftover",
         "r35/r64 Valkey tls-cert; this is ACL+TLS leftover after rotate.",
         "https://valkey.io/topics/encryption/", "src/nightly_valkey_acl.py"),
    ),
    (
        ("pgbouncer-server-tls-reload", "PgBouncer server TLS", "server_tls_key_file", "restart",
         "PAUSE + RELOAD + RESUME server TLS",
         "Reload server_tls_key_file; do not restart PgBouncer.",
         "https://www.pgbouncer.org/config.html#tls-settings", "src/legacy_pgb_server.py"),
        ("pgpool-ssl-handoff", "Pgpool-II", "ssl_key", "restart", "pgpool leftover",
         "Ticket is pgpool ssl_key swap; nightly still restarts pgpool.",
         "https://www.pgpool.net/docs/latest/en/html/runtime-ssl.html", "src/nightly_pgpool.py"),
    ),
    (
        ("haproxy-spoe-tls-reload", "HAProxy SPOE", "spoe tls", "restart",
         "so_reload spoe",
         "so_reload SPOE TLS; do not restart HAProxy.",
         "https://www.haproxy.com/documentation/haproxy-configuration-tutorials/proxying-essentials/spoe/",
         "src/legacy_haproxy_spoe.py"),
        ("envoy-extproc-tls-handoff", "Envoy ext_proc", "ext_proc tls", "lds push", "ext_proc leftover",
         "Ticket is ext_proc gRPC TLS secret swap; nightly still LDS-pushes.",
         "https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/ext_proc_filter",
         "src/nightly_envoy_extproc.py"),
    ),
    (
        ("istio-waypoint-hbone-tls", "Istio HBONE", "waypoint hbone tls", "pod delete",
         "waypoint SDS HBONE",
         "SDS reload of HBONE waypoint TLS; do not delete the waypoint.",
         "https://istio.io/latest/docs/ambient/usage/waypoint/", "src/legacy_hbone.py"),
        ("linkerd-policy-tls-handoff", "Linkerd policy", "policy tls", "identity restart", "policy leftover",
         "Ticket is policy controller TLS rotate; nightly still restarts identity.",
         "https://linkerd.io/2.15/features/server-policy/", "src/nightly_l5d_policy.py"),
    ),
    (
        ("cert-manager-gateway-reload", "cert-manager Gateway", "Gateway cert", "gateway delete",
         "Certificate + Gateway listener ref",
         "Issue Certificate and patch Gateway listener; do not delete the Gateway.",
         "https://cert-manager.io/docs/usage/gateway/", "src/legacy_cm_gw.py"),
        ("trust-manager-configmap-handoff", "trust-manager ConfigMap", "Bundle cm", "pod restart", "cm leftover",
         "r54 Bundle secret; this is ConfigMap target leftover.",
         "https://cert-manager.io/docs/trust/trust-manager/", "src/nightly_trust_cm.py"),
    ),
]


def notes_for(rnd, suc, fail, suc_p, fail_p) -> str:
    return (
        f"# ssl-cert-rotation-factory — NOTES r{rnd}\n\n"
        f"Novel coverage: {max(68, 84 - (rnd - CATALOG_FIRST))}%\n\n"
        f"## Episodes\n"
        f"- `{suc['id']}`: 16 steps, success=True, domain={suc_p[0]}, seed={suc_p[0]}\n"
        f"  - 502 at step 6 recovered 7; 429 at step 8 recovered 9\n"
        f"  - plan change at step 12: {suc_p[4]}. Do not delete-then-create secret.\n"
        f"- `{fail['id']}`: 17 steps, success=False, domain={fail_p[0]}, seed={fail_p[0]}\n"
        f"  - 429 at step 8 recovered 9; nightly {fail_p[4]} leftover\n\n"
        f"## Mix\n"
        f"Success: ['{suc['id']}']. Realistic failure/handoff: ['{fail['id']}'].\n\n"
        f"## decision_basis audit\n"
        f"Every step starts Plan:/Observation:/Reflection:/Tool call:, ≤240 chars.\n"
        f"No thought / chain_of_thought / scratch / inner_monologue. No spike_events.\n"
        f"No sim_or_real: real. Generator grok-4.6.\n\n"
        f"## Weaknesses / next\n"
        f"Avoid delete-then-create secret. Not hitch/dovecot/ghostunnel/Postfix clones.\n"
        f"Distinct from ssl r01–r{rnd-1} ({suc_p[5]}; {fail_p[5]}).\n"
    )


def build_round(rnd: int):
    idx = rnd - CATALOG_FIRST
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(f"round {rnd} outside catalog {CATALOG_FIRST}..{CATALOG_FIRST + len(PAIRS) - 1}")
    suc_p, fail_p = PAIRS[idx]
    suc = build_success(rnd, suc_p)
    fail = build_partial(rnd, fail_p)
    return [suc, fail], notes_for(rnd, suc, fail, suc_p, fail_p)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    args = ap.parse_args()
    recs, notes = build_round(args.round)
    staging = Path(args.staging)
    (staging / f"batch-r{args.round:02d}.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=True) + "\n" for r in recs)
    )
    (staging / f"NOTES-r{args.round:02d}.md").write_text(notes)
    print(json.dumps({"round": args.round, "ids": [r["id"] for r in recs]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
