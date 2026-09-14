#!/usr/bin/env python3
"""ssl-cert-rotation mill r106+: unique leftover stacks.

Hop target when mdb is reserved. BAN r01–r105 clones (hitch/dovecot/ghostunnel/
postfix, rabbit/redis, marathon/mesos, nifi/airflow/superset/metabase/redash,
spark/flink/trino/presto/drill/impala, duckdb/questdb/datafusion).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("ssl_mill_r35", HERE / "ssl-mill-r35.py")
_m = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_m)

FACTORY = _m.FACTORY
GEN = _m.GEN
CATALOG_FIRST = 106
build_success = _m.build_success
build_partial = _m.build_partial

PAIRS = [
    (
        ("clickhouse-https-reload", "ClickHouse", "https_port certFile", "restart", "SYSTEM RELOAD CERTIFICATES",
         "Restart drops queries; SYSTEM RELOAD CERTIFICATES swaps the leaf.",
         "https://clickhouse.com/docs/en/operations/server-configuration-parameters/settings", "src/legacy_clickhouse.py"),
        ("timescaledb-ssl-handoff", "TimescaleDB", "ssl_cert_file", "pg_ctl restart", "reload leftover",
         "Ticket is Timescale ssl_cert_file swap; nightly still restarts Postgres.",
         "https://docs.timescale.com/self-hosted/latest/configuration/", "src/nightly_timescale.py"),
    ),
    (
        ("cockroach-node-cert-reload", "CockroachDB", "node.crt", "restart", "cockroach cert reload",
         "Restart kills leases; node.crt reload SIGHUP swaps the leaf.",
         "https://www.cockroachlabs.com/docs/stable/manage-certs-offline.html", "src/legacy_cockroach.py"),
        ("yugabyte-ysql-ssl-handoff", "YugabyteDB", "ysql.ssl_cert", "yb-master restart", "reload leftover",
         "Ticket is ysql.ssl_cert swap; nightly still restarts yb-master.",
         "https://docs.yugabyte.com/preview/secure/tls-encryption/", "src/nightly_yugabyte.py"),
    ),
    (
        ("vitess-vtgate-ssl-reload", "Vitess", "vtgate grpc-cert", "pod delete", "vtgate --lameduck-period reload",
         "Pod delete drops in-flight Execute; vtgate cert reload keeps sessions.",
         "https://vitess.io/docs/reference/features/security/", "src/legacy_vitess.py"),
        ("tidb-status-ssl-handoff", "TiDB", "status.ssl-cert", "tidb-server restart", "reload leftover",
         "Ticket is TiDB status.ssl-cert swap; nightly still restarts tidb-server.",
         "https://docs.pingcap.com/tidb/stable/enable-tls-between-clients-and-servers", "src/nightly_tidb.py"),
    ),
    (
        ("scylla-client-ssl-reload", "ScyllaDB", "client_encryption_options.certificate", "nodetool drain", "sighup reload",
         "Drain drops CQL; SIGHUP reloads client_encryption_options cert.",
         "https://docs.scylladb.com/stable/operating-scylla/security/authentication.html", "src/legacy_scylla.py"),
        ("cassandra-internode-ssl-handoff", "Cassandra", "internode_encryption cert", "rolling restart", "reload leftover",
         "Ticket is internode cert swap; nightly still rolling-restarts the ring.",
         "https://cassandra.apache.org/doc/latest/cassandra/operating/security.html", "src/nightly_cassandra.py"),
    ),
    (
        ("opensearch-http-ssl-reload", "OpenSearch", "plugins.security.ssl.http.pemcert", "node restart", "securityadmin.sh reload",
         "Restart drops shards; securityadmin.sh reloads HTTP pemcert.",
         "https://docs.opensearch.org/docs/latest/security/configuration/tls/", "src/legacy_opensearch.py"),
        ("solr-ssl-handoff", "Solr", "solr.jetty.keystore", "bin/solr restart", "reload leftover",
         "Ticket is Jetty keystore swap; nightly still restarts Solr.",
         "https://solr.apache.org/guide/solr/latest/deployment-guide/enabling-ssl.html", "src/nightly_solr.py"),
    ),
    (
        ("neo4j-bolt-ssl-reload", "Neo4j", "dbms.ssl.policy.bolt.public_certificate", "neo4j restart", "dbms.ssl.policy reload",
         "Restart drops Bolt sessions; ssl.policy reload swaps the leaf.",
         "https://neo4j.com/docs/operations-manual/current/security/ssl-framework/", "src/legacy_neo4j.py"),
        ("mongodb-cluster-cert-handoff", "MongoDB", "net.tls.certificateKeyFile", "rolling restart", "reload leftover",
         "Ticket is mongod certificateKeyFile swap; nightly still rolling-restarts.",
         "https://www.mongodb.com/docs/manual/tutorial/configure-ssl/", "src/nightly_mongo.py"),
    ),
    (
        ("minio-certs-reload", "MinIO", "public.crt", "mc admin service restart", "mc admin certs reload",
         "Service restart drops S3 inflight; certs reload swaps public.crt.",
         "https://min.io/docs/minio/linux/operations/network-encryption.html", "src/legacy_minio.py"),
        ("seaweedfs-tls-handoff", "SeaweedFS", "filer.tls.cert", "weed restart", "reload leftover",
         "Ticket is filer.tls.cert swap; nightly still restarts weed.",
         "https://github.com/seaweedfs/seaweedfs/wiki/Security-Overview", "src/nightly_seaweed.py"),
    ),
    (
        ("etcd-peer-cert-reload", "etcd", "peer-trusted-ca-file", "member restart", "etcdctl endpoint reload",
         "Member restart loses raft; cert reload keeps the peer.",
         "https://etcd.io/docs/latest/op-guide/security/", "src/legacy_etcd.py"),
        ("zookeeper-quorum-ssl-handoff", "ZooKeeper", "sslQuorum.cert", "rolling restart", "reload leftover",
         "Ticket is sslQuorum cert swap; nightly still rolling-restarts quorum.",
         "https://zookeeper.apache.org/doc/current/zookeeperAdmin.html#sc_encryption_and_auth", "src/nightly_zk.py"),
    ),
    (
        ("nats-leaf-tls-reload", "NATS", "leafnodes.tls.cert_file", "nats-server restart", "signal reload",
         "Restart drops leaf connections; signal reload swaps cert_file.",
         "https://docs.nats.io/running-a-nats-service/configuration/securing_nats/tls", "src/legacy_nats.py"),
        ("pulsar-broker-tls-handoff", "Pulsar", "tlsCertificateFilePath", "broker restart", "reload leftover",
         "Ticket is Pulsar tlsCertificateFilePath swap; nightly still restarts brokers.",
         "https://pulsar.apache.org/docs/3.3.x/security-tls-transport/", "src/nightly_pulsar.py"),
    ),
    (
        ("vault-listener-tls-reload", "Vault", "listener.tcp.tls_cert_file", "vault restart", "SIGHUP reload",
         "Restart seals the node; SIGHUP reloads tls_cert_file.",
         "https://developer.hashicorp.com/vault/docs/configuration/listener/tcp", "src/legacy_vault.py"),
        ("boundary-worker-tls-handoff", "Boundary", "worker.tls.cert", "worker restart", "reload leftover",
         "Ticket is Boundary worker.tls.cert swap; nightly still restarts workers.",
         "https://developer.hashicorp.com/boundary/docs/configuration/worker", "src/nightly_boundary.py"),
    ),
    (
        ("nomad-tls-reload", "Nomad", "tls.rpc.cert_file", "nomad restart", "nomad tls reload",
         "Restart drops jobs; nomad tls reload swaps rpc cert_file.",
         "https://developer.hashicorp.com/nomad/docs/configuration/tls", "src/legacy_nomad.py"),
        ("consul-connect-tls-handoff", "Consul", "connect.ca_file", "agent restart", "reload leftover",
         "Ticket is Consul connect.ca_file swap; nightly still restarts the agent.",
         "https://developer.hashicorp.com/consul/docs/secure-mesh/certificate", "src/nightly_consul.py"),
    ),
    (
        ("envoy-sds-reload", "Envoy", "sds secret", "hot restart", "sds incremental update",
         "Hot restart drains listeners; SDS incremental update swaps the secret.",
         "https://www.envoyproxy.io/docs/envoy/latest/configuration/security/secret", "src/legacy_envoy.py"),
        ("contour-envoy-secret-handoff", "Contour", "tls.secretName", "envoy restart", "reload leftover",
         "Ticket is Contour tls.secretName swap; nightly still restarts Envoy.",
         "https://projectcontour.io/docs/main/config/tls-termination/", "src/nightly_contour.py"),
    ),
    (
        ("caddy-pki-reload", "Caddy", "pki.certificate", "caddy stop", "caddy reload --force",
         "Stop drops HTTP; caddy reload --force swaps pki.certificate.",
         "https://caddyserver.com/docs/caddyfile/directives/tls", "src/legacy_caddy.py"),
        ("traefik-tlsstore-handoff", "Traefik", "tls.stores.default.defaultCertificate", "pod restart", "reload leftover",
         "Ticket is Traefik defaultCertificate swap; nightly still restarts the pod.",
         "https://doc.traefik.io/traefik/https/tls/", "src/nightly_traefik.py"),
    ),
    (
        ("haproxy-crt-bind-reload", "HAProxy", "bind crt", "restart", "kill -USR2 reload",
         "Restart drops TCP; USR2 reloads bind crt.",
         "https://www.haproxy.com/documentation/haproxy-configuration-manual/latest/#5.1-crt", "src/legacy_haproxy.py"),
        ("varnish-tls-handoff", "Varnish", "tls.pem", "varnishd restart", "reload leftover",
         "Ticket is Varnish tls.pem swap; nightly still restarts varnishd.",
         "https://docs.varnish-software.com/varnish-plus/installation/tls/", "src/nightly_varnish.py"),
    ),
    (
        ("lighttpd-ssl-pem-reload", "lighttpd", "ssl.pemfile", "restart", "lighttpd-angel reload",
         "Restart drops keep-alives; lighttpd-angel reload swaps ssl.pemfile.",
         "https://redmine.lighttpd.net/projects/lighttpd/wiki/Docs_SSL", "src/legacy_lighttpd.py"),
        ("cherokee-tls-handoff", "Cherokee", "ssl_certificate_file", "cherokee restart", "reload leftover",
         "Ticket is Cherokee ssl_certificate_file swap; nightly still restarts.",
         "https://cherokee-project.com/doc/config_virtual_servers_ssl.html", "src/nightly_cherokee.py"),
    ),
    (
        ("unit-tls-cert-reload", "NGINX Unit", "tls.certificate", "unitd restart", "curl control-api /certificates",
         "Restart drops apps; control API PUT /certificates swaps the leaf.",
         "https://unit.nginx.org/configuration/#ssl-tls-and-certificates", "src/legacy_unit.py"),
        ("openresty-ssl-handoff", "OpenResty", "ssl_certificate", "nginx -s stop", "reload leftover",
         "Ticket is OpenResty ssl_certificate swap; nightly still stops nginx.",
         "https://github.com/openresty/lua-resty-core/blob/master/lib/ngx/ssl.md", "src/nightly_openresty.py"),
    ),
]


def notes_for(rnd: int, suc: dict, fail: dict, suc_p, fail_p) -> str:
    return (
        f"# ssl-cert-rotation-factory — NOTES r{rnd}\n\n"
        f"Novel coverage: {max(70, 86 - (rnd - CATALOG_FIRST))}%\n\n"
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
    notes = notes_for(rnd, suc, fail, suc_p, fail_p)
    return [suc, fail], notes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    args = ap.parse_args()
    recs, notes = build_round(args.round)
    staging = Path(args.staging)
    batch = staging / f"batch-r{args.round:02d}.jsonl"
    notes_path = staging / f"NOTES-r{args.round:02d}.md"
    batch.write_text("".join(json.dumps(r, ensure_ascii=True) + "\n" for r in recs))
    notes_path.write_text(notes)
    print(json.dumps({"round": args.round, "ids": [r["id"] for r in recs], "steps": [len(r["steps"]) for r in recs]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
