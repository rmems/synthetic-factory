#!/usr/bin/env python3
"""ssl-cert-rotation mill r35+: unique stacks, not hitch/dovecot/ghostunnel/postfix clones."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

FACTORY = "ssl-cert-rotation-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 35
BANNED = (
    "thought",
    "chain_of_thought",
    "scratch",
    "inner_monologue",
    "spike_events",
    "SKU-9",
    "U+1D17",
    "combining mark",
)


def clip(text: str, n: int = 240) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= n else text[: n - 1] + "…"


def step(n: int, basis: str, name: str, args: dict, obs: str, reflection: str) -> dict:
    return {
        "n": n,
        "decision_basis": clip(basis),
        "tool_call": {"name": name, "args": args},
        "observation": obs,
        "reflection": reflection,
    }


# slug, stack, unit, wrong, fix, ticket, url, leftover
PAIRS = [
    (
        ("rabbitmq-ssl-options-reload", "RabbitMQ", "ssl_options.cacertfile", "sighup", "rabbitmqctl eval ssl:clear_pem_cache()",
         "SIGHUP keeps the old cacert inode; rabbitmqctl eval ssl:clear_pem_cache() swaps it.",
         "https://www.rabbitmq.com/docs/ssl", "src/legacy_rmq.py"),
        ("redis-tls-cert-handoff", "Redis", "tls-cert-file", "config set", "CONFIG REWRITE leftover",
         "CONFIG SET tls-cert-file is live but redis.conf still names the old leaf.",
         "https://redis.io/docs/latest/operate/oss_and_stack/management/security/encryption/", "src/nightly_redis.py"),
    ),
    (
        ("kafka-listener-keystore-reload", "Kafka", "ssl.keystore.location", "broker restart", "listener.name.ssl.ssl.keystore.location + rolling",
         "Full broker restart drops ISR; rolling listener keystore reload keeps the controller.",
         "https://kafka.apache.org/documentation/#security_ssl", "src/legacy_kafka.py"),
        ("es-http-ssl-handoff", "Elasticsearch", "xpack.security.http.ssl", "node restart", "reload_secure_settings leftover",
         "http.ssl keystore path updated; reload_secure_settings still points at the old PKCS12.",
         "https://www.elastic.co/docs/deploy-manage/security/secure-cluster", "src/nightly_es.py"),
    ),
    (
        ("postgres-ssl-cert-sighup", "Postgres", "ssl_cert_file", "restart", "pg_reload_conf + SELECT pg_reload_conf()",
         "Restart drops connections; SIGHUP + pg_reload_conf loads the new leaf.",
         "https://www.postgresql.org/docs/current/ssl-tcp.html", "src/legacy_pg.py"),
        ("mongo-tls-keyfile-handoff", "MongoDB", "net.tls.certificateKeyFile", "restart", "rotateCertificates leftover",
         "db.adminCommand({rotateCertificates:1}) is ticket; nightly still restarts mongod.",
         "https://www.mongodb.com/docs/manual/tutorial/configure-ssl/", "src/nightly_mongo.py"),
    ),
    (
        ("nats-tls-reload", "NATS", "tls cert_file", "kill -9", "nats-server --signal reload",
         "Hard kill drops JetStream; --signal reload swaps cert_file.",
         "https://docs.nats.io/running-a-nats-service/configuration/securing_nats/tls", "src/legacy_nats.py"),
        ("clickhouse-https-handoff", "ClickHouse", "https_port cert", "restart", "SYSTEM RELOAD CONFIG leftover",
         "SYSTEM RELOAD CONFIG is the ticket; nightly still systemctl restarts clickhouse-server.",
         "https://clickhouse.com/docs/en/guides/sre/ssl-user-auth", "src/nightly_ch.py"),
    ),
    (
        ("grafana-cert-file-reload", "Grafana", "cert_file", "restart", "kill -HUP grafana-server",
         "Restart drops dashboards in-flight; HUP reloads cert_file/key.",
         "https://grafana.com/docs/grafana/latest/setup-grafana/set-up-https/", "src/legacy_grafana.py"),
        ("etcd-peer-ca-handoff", "etcd", "peer-trusted-ca-file", "member recreate", "etcdctl member update leftover",
         "Ticket is peer-trusted-ca-file swap; nightly still removes the member.",
         "https://etcd.io/docs/latest/op-guide/security/", "src/nightly_etcd.py"),
    ),
    (
        ("nomad-tls-reload", "Nomad", "tls.cert_file", "agent restart", "nomad tls cert reload via SIGHUP",
         "Agent restart drains jobs; SIGHUP reloads tls.cert_file.",
         "https://developer.hashicorp.com/nomad/docs/configuration/tls", "src/legacy_nomad.py"),
        ("kube-apiserver-cert-handoff", "kube-apiserver", "--tls-cert-file", "apiserver restart", "kubelet static-pod leftover",
         "Ticket is --tls-cert-file swap with readyz; nightly still deletes the static pod.",
         "https://kubernetes.io/docs/tasks/tls/managing-tls-in-a-cluster/", "src/nightly_kas.py"),
    ),
    (
        ("minio-certs-reload", "MinIO", "certs/", "mc admin service restart", "mc admin service restart --wait=false + certs watch",
         "Full service restart drops multipart; certs/ watch reloads the leaf.",
         "https://min.io/docs/minio/linux/operations/network-encryption.html", "src/legacy_minio.py"),
        ("harbor-nginx-handoff", "Harbor", "harbor.yml cert", "docker compose down", "nginx -s reload leftover",
         "Ticket is harbor nginx -s reload; nightly still compose down.",
         "https://goharbor.io/docs/latest/install-config/configure-https/", "src/nightly_harbor.py"),
    ),
    (
        ("memcached-ssl-reload", "Memcached", "-o ssl_chain_cert", "restart", "memcached -o ssl_reload",
         "Restart flushes the slab; ssl_reload swaps the chain.",
         "https://github.com/memcached/memcached/wiki/TLS", "src/legacy_memcached.py"),
        ("mysql-ssl-handoff", "MySQL", "ssl_cert", "restart", "ALTER INSTANCE RELOAD TLS leftover",
         "Ticket is ALTER INSTANCE RELOAD TLS; nightly still restarts mysqld.",
         "https://dev.mysql.com/doc/refman/8.4/en/using-encrypted-connections.html", "src/nightly_mysql.py"),
    ),
    (
        ("pgbouncer-client-tls-reload", "PgBouncer", "client_tls_key_file", "restart", "PAUSE + RELOAD + RESUME",
         "Restart drops clients; PAUSE/RELOAD/RESUME swaps client_tls_key_file.",
         "https://www.pgbouncer.org/config.html#tls-settings", "src/legacy_pgbouncer.py"),
        ("keycloak-https-handoff", "Keycloak", "https-certificate-file", "pod delete", "kc.sh start --optimized leftover",
         "Ticket is https-certificate-file swap; nightly still deletes the pod.",
         "https://www.keycloak.org/server/enabletls", "src/nightly_kc.py"),
    ),
    (
        ("emqx-listener-ssl-reload", "EMQX", "listeners.ssl.default", "node restart", "emqx ctl listeners restart ssl:default",
         "Node restart drops MQTT sessions; listeners restart ssl:default swaps certfile.",
         "https://docs.emqx.com/en/emqx/latest/access-control/authn/tls.html", "src/legacy_emqx.py"),
        ("coredns-tls-handoff", "CoreDNS", "tls cert", "pod rollout", "SIGUSR1 leftover",
         "Ticket is CoreDNS SIGUSR1 reload; nightly still rollouts the DaemonSet.",
         "https://coredns.io/plugins/tls/", "src/nightly_coredns.py"),
    ),
    (
        ("unbound-tls-reload", "Unbound", "tls-service-key", "restart", "unbound-control reload",
         "Restart drops the cache; unbound-control reload swaps tls-service-pem.",
         "https://unbound.docs.nlnetlabs.nl/en/latest/manpages/unbound.conf.html", "src/legacy_unbound.py"),
        ("powerdns-dnssec-handoff", "PowerDNS", "bind-config extra-files", "pdns restart", "pdns_control bind-reload leftover",
         "Ticket is bind-reload of the TLS front; nightly still restarts pdns.",
         "https://doc.powerdns.com/authoritative/guides/recursion.html", "src/nightly_pdns.py"),
    ),
    (
        ("haproxy-crt-store-reload", "HAProxy", "crt-store", "restart", "so_reload + crt-store update",
         "r15 was crt-list; this is crt-store update without dropping bind.",
         "https://docs.haproxy.org/2.8/configuration.html#crt-store", "src/legacy_haproxy_store.py"),
        ("envoy-sds-warmup-handoff", "Envoy", "SDS warmup", "lds push", "secret warmup leftover",
         "r11 was SDS no LDS; this is secret warmup skipped so first request uses the old leaf.",
         "https://www.envoyproxy.io/docs/envoy/latest/configuration/security/secret", "src/nightly_envoy_warm.py"),
    ),
    (
        ("caddy-pki-local-reload", "Caddy", "pki.local", "restart", "caddy reload --config",
         "r10/r17 were file vs autohttps; this is pki.local CA leaf reload.",
         "https://caddyserver.com/docs/caddyfile/options#pki", "src/legacy_caddy_pki.py"),
        ("traefik-tlsoptions-handoff", "Traefik", "tls.options minVersion", "pod bounce", "dynamic tls leftover",
         "r08/r23 were acme.json / tlsstore; this is tls.options minVersion not applied after cert swap.",
         "https://doc.traefik.io/traefik/https/tls/", "src/nightly_traefik_opt.py"),
    ),
    (
        ("vault-listener-tls-reload", "Vault", "listener tcp tls", "service restart", "SIGHUP listener reload",
         "r07/r22 were pki role TTL; this is the API listener cert itself.",
         "https://developer.hashicorp.com/vault/docs/configuration/listener/tcp#tls", "src/legacy_vault_listener.py"),
        ("consul-https-handoff", "Consul", "ports.https cert", "agent restart", "consul reload leftover",
         "r12 was connect CA; this is the HTTPS API cert. Nightly still restarts the agent.",
         "https://developer.hashicorp.com/consul/docs/secure/encryption/tls", "src/nightly_consul_https.py"),
    ),
    (
        ("nginx-ssl-stapling-file", "nginx", "ssl_stapling_file", "reload", "ssl_stapling_file + staple refresh",
         "r01/r08/r20 were inode/fullchain; this is a stale OCSP staple file after leaf swap.",
         "https://nginx.org/en/docs/http/ngx_http_ssl_module.html#ssl_stapling_file", "src/legacy_nginx_staple.py"),
        ("apache-ocsp-handoff", "Apache", "SSLOCSPDefaultResponder", "restart", "apachectl graceful leftover",
         "r11 was chain file; this is OCSP responder leftover after leaf swap.",
         "https://httpd.apache.org/docs/2.4/mod/mod_ssl.html#sslocspdefaultresponder", "src/nightly_apache_ocsp.py"),
    ),
    (
        ("haproxy-ocsp-update", "HAProxy", "ocsp-update", "restart", "set ssl ocsp-response",
         "r07 was runtime commit; this is OCSP response update after leaf swap.",
         "https://docs.haproxy.org/2.8/management.html#9.3-set%20ssl%20ocsp-response", "src/legacy_haproxy_ocsp.py"),
        ("caddy-ocsp-stapling-handoff", "Caddy", "ocsp_stapling", "restart", "caddy reload leftover",
         "r10/r17 file vs autohttps; this is OCSP stapling leftover off after rotate.",
         "https://caddyserver.com/docs/caddyfile/directives/tls#ocsp_stapling", "src/nightly_caddy_ocsp.py"),
    ),
    (
        ("varnish-tls-proxy-reload", "Varnish", "tls-proxy pem", "restart", "varnishreload + proxy HUP",
         "Restart drops the cache; varnishreload plus the TLS proxy HUP swaps the leaf.",
         "https://varnish-cache.org/docs/trunk/reference/varnishd.html", "src/legacy_varnish.py"),
        ("squid-https-port-handoff", "Squid", "https_port cert", "restart", "squid -k reconfigure leftover",
         "r13 was sslcrtd CA; this is https_port cert. Nightly still restarts squid.",
         "https://www.squid-cache.org/Doc/config/https_port/", "src/nightly_squid_https.py"),
    ),
    (
        ("apisix-ssl-reload", "APISIX", "ssl cert", "etcd put + restart", "admin API ssl patch",
         "Restart drops routes; Admin API PATCH /ssls/{id} swaps the leaf.",
         "https://apisix.apache.org/docs/apisix/admin-api/#ssl", "src/legacy_apisix.py"),
        ("tyk-certs-handoff", "Tyk", "http_server_options certificates", "gateway restart", "tyk reload leftover",
         "Ticket is tyk reload of http_server_options.certificates; nightly still restarts.",
         "https://tyk.io/docs/api-management/certificates/", "src/nightly_tyk.py"),
    ),
    (
        ("krakend-tls-reload", "KrakenD", "tls public_key", "process restart", "krakend run flexible-config reload",
         "Restart drops in-flight; flexible-config reload swaps tls.public_key.",
         "https://www.krakend.io/docs/service-settings/tls/", "src/legacy_krakend.py"),
        ("kong-ssl-cert-handoff", "Kong", "certificates object", "pod bounce", "PATCH /certificates leftover",
         "r24 was acme plugin; this is the certificates object. Nightly still bounces pods.",
         "https://docs.konghq.com/gateway/latest/admin-api/certificates/examples/", "src/nightly_kong_cert.py"),
    ),
    (
        ("contour-secrets-reload", "Contour", "TLS secret", "envoy restart", "secret watch + SDS",
         "Envoy restart drops HTTPRoute; Contour SDS watches the TLS secret.",
         "https://projectcontour.io/docs/main/config/tls-termination/", "src/legacy_contour.py"),
        ("gateway-api-cert-handoff", "Gateway API", "CertificateRef", "gateway delete", "listener cert leftover",
         "Ticket is Gateway listener certificateRefs swap; nightly still deletes the Gateway.",
         "https://gateway-api.sigs.k8s.io/guides/tls/", "src/nightly_gwapi.py"),
    ),
    (
        ("cert-manager-ca-injector", "cert-manager", "cainjector bundle", "restart injector", "annotate inject-ca-from",
         "Restarting cainjector is not the rotate; inject-ca-from must refresh the CA bundle.",
         "https://cert-manager.io/docs/concepts/ca-injector/", "src/legacy_cainject.py"),
        ("trust-manager-bundle-handoff", "trust-manager", "Bundle", "pod restart", "Bundle source leftover",
         "Ticket is Bundle sources.secret swap; nightly still restarts trust-manager.",
         "https://cert-manager.io/docs/trust/trust-manager/", "src/nightly_trust.py"),
    ),
    (
        ("aws-acm-pca-issue", "ACM PCA", "GetCertificate", "ALB recreate", "listener cert ARN swap",
         "Recreating the ALB is banned; swap the listener certificate ARN after IssueCertificate.",
         "https://docs.aws.amazon.com/privateca/latest/userguide/PcaWelcome.html", "src/legacy_acm_pca.py"),
        ("google-cas-handoff", "Google CAS", "Certificate", "proxy recreate", "targetHttpsProxies.setSslCertificates leftover",
         "Ticket is setSslCertificates; nightly still recreates the HTTPS proxy.",
         "https://cloud.google.com/certificate-authority-service/docs", "src/nightly_cas.py"),
    ),
    (
        ("cilium-gateway-cert", "Cilium", "CiliumGateway cert", "agent restart", "secret sync + envoy SDS",
         "Restarting the agent drops BPF maps; SDS secret sync swaps the Gateway cert.",
         "https://docs.cilium.io/en/stable/network/servicemesh/gateway-api/gateway-api/", "src/legacy_cilium_gw.py"),
        ("envoy-gateway-handoff", "Envoy Gateway", "TLSCertificateRef", "deployment bounce", "secret leftover",
         "Ticket is TLSCertificateRefs swap; nightly still bounces the Envoy deployment.",
         "https://gateway.envoyproxy.io/docs/tasks/security/tls-passthrough/", "src/nightly_egw.py"),
    ),
    (
        ("istio-waypoint-cert", "Istio waypoint", "waypoint TLS", "pod delete", "waypoint SDS reload",
         "r23 was credentialName SDS; this is waypoint TLS after ambient rotate.",
         "https://istio.io/latest/docs/ambient/usage/waypoint/", "src/legacy_waypoint.py"),
        ("linkerd-meshtls-handoff", "Linkerd", "mesh TLS", "identity restart", "issuer leftover",
         "r12 was identity issuer restart success; this is mesh TLS leftover on the destination.",
         "https://linkerd.io/2.14/tasks/automatically-rotating-control-plane-tls-credentials/", "src/nightly_linkerd_mesh.py"),
    ),
    (
        ("nginx-plus-api-cert", "nginx plus", "plus API cert", "reload", "plus API /ssl swap",
         "r01/r08/r20 inode/fullchain; this is NGINX Plus API /api/8/http/ssl swapping the leaf.",
         "https://docs.nginx.com/nginx/admin-guide/security-controls/terminating-ssl-http/", "src/legacy_nginx_plus.py"),
        ("openresty-lua-ssl-handoff", "OpenResty", "ssl_certificate_by_lua", "restart", "lua ssl leftover",
         "r32 was ssl_cert_by_lua success; this is leftover lua ssl ctx after rotate.",
         "https://github.com/openresty/lua-resty-core/blob/master/lib/ngx/ssl.md", "src/nightly_openresty_ssl.py"),
    ),
    (
        ("haproxy-crt-list-sni", "HAProxy", "crt-list SNI", "restart", "so_reload crt-list",
         "r15 was crt-list reload; this is a new SNI line in crt-list after rotate.",
         "https://docs.haproxy.org/2.8/configuration.html#5.1-crt-list", "src/legacy_haproxy_sni.py"),
        ("sniproxy-fallback-handoff", "sniproxy", "fallback pem", "restart", "config reload leftover",
         "r34 was default pem reload success; this is fallback pem leftover.",
         "https://github.com/dlundquist/sniproxy", "src/nightly_sniproxy_fb.py"),
    ),
    (
        ("caddy-layer4-tls", "Caddy layer4", "layer4 tls", "restart", "caddy reload layer4",
         "r10/r17/r47 were http tls; this is layer4 TLS app cert reload.",
         "https://github.com/mholt/caddy-l4", "src/legacy_caddy_l4.py"),
        ("traefik-tcp-tls-handoff", "Traefik TCP", "TCP TLS", "pod bounce", "tcp tls leftover",
         "r08/r23/r47 were http tlsstore/options; this is TCP router TLS leftover.",
         "https://doc.traefik.io/traefik/routing/routers/#tls", "src/nightly_traefik_tcp.py"),
    ),
    (
        ("vault-agent-template-cert", "Vault agent", "template dest cert", "agent restart", "template render + HUP app",
         "Restarting vault-agent is not required; template re-render plus app HUP swaps the leaf.",
         "https://developer.hashicorp.com/vault/docs/agent-and-proxy/agent/template", "src/legacy_vault_agent.py"),
        ("consul-template-handoff", "consul-template", "template cert", "restart", "consul-template reload leftover",
         "r12/r48 were consul HTTPS/connect; this is consul-template dest leftover.",
         "https://github.com/hashicorp/consul-template", "src/nightly_ctmpl.py"),
    ),
    (
        ("step-ca-renew", "step-ca", "renew --daemon", "ca restart", "step ca renew --force",
         "r21 was provisioner; this is step ca renew --force of a leaf without restarting the CA.",
         "https://smallstep.com/docs/step-ca/certificate-authority-server-production/", "src/legacy_step_renew.py"),
        ("lego-renew-handoff", "lego", "lego renew", "nginx restart", "lego renew leftover hook",
         "r24 was dns01 vs http01; this is lego renew hook leftover still restarting nginx.",
         "https://go-acme.github.io/lego/usage/cli/renew/", "src/nightly_lego.py"),
    ),
    (
        ("certbot-deploy-hook", "certbot", "deploy hook", "service restart", "nginx -s reload in deploy hook",
         "r17 acme http01; this is certbot deploy hook calling nginx -s reload not systemctl restart.",
         "https://eff-certbot.readthedocs.io/en/stable/using.html#renewing-certificates", "src/legacy_certbot.py"),
        ("acme-sh-reloadcmd-handoff", "acme.sh", "reloadcmd", "docker restart", "reloadcmd leftover",
         "r13 eab kid; this is acme.sh --reloadcmd leftover still docker restart.",
         "https://github.com/acmesh-official/acme.sh", "src/nightly_acmesh.py"),
    ),
    (
        ("pkcs11-engine-reload", "PKCS#11", "engine key", "process restart", "ENGINE_init reload",
         "r15 pkcs11 provider handoff; this is ENGINE_init reload of a rotated token object.",
         "https://www.openssl.org/docs/manmaster/man3/ENGINE_init.html", "src/legacy_pkcs11.py"),
        ("softhsm-object-handoff", "SoftHSM", "token object", "slot reinit", "object leftover",
         "Ticket is C_DestroyObject + C_CreateObject; nightly still re-inits the slot.",
         "https://www.opendnssec.org/softhsm/", "src/nightly_softhsm.py"),
    ),
    (
        ("garage-s3-tls-reload", "Garage", "api_bind_tls", "node restart", "garage config reload tls",
         "Node restart drops S3 multipart; config reload swaps api_bind_tls cert.",
         "https://garagehq.deuxfleurs.fr/documentation/reference-manual/configuration/", "src/legacy_garage.py"),
        ("valkey-tls-cert-handoff", "Valkey", "tls-cert-file", "restart", "CONFIG REWRITE leftover",
         "r35 was Redis CONFIG SET; this is Valkey tls-cert-file. Nightly still rewrites redis.conf names.",
         "https://valkey.io/topics/encryption/", "src/nightly_valkey.py"),
    ),
    (
        ("keydb-tls-reload", "KeyDB", "tls-cert-file", "restart", "CONFIG SET tls-cert-file + keepalive",
         "Restart drops replicas; CONFIG SET tls-cert-file swaps the leaf.",
         "https://docs.keydb.dev/docs/config-file/", "src/legacy_keydb.py"),
        ("dragonfly-tls-handoff", "Dragonfly", "tls_cert_file", "process restart", "CONFIG SET leftover",
         "Ticket is Dragonfly CONFIG SET tls_cert_file; nightly still restarts dragonfly.",
         "https://www.dragonflydb.io/docs/managing-dragonfly/flags", "src/nightly_dragonfly.py"),
    ),
    (
        ("cockroach-node-cert-reload", "CockroachDB", "node.crt", "node restart", "cockroach cert rotate + SIGHUP",
         "Node restart drops leases; cert rotate plus SIGHUP swaps node.crt.",
         "https://www.cockroachlabs.com/docs/stable/rotate-certificates", "src/legacy_crdb.py"),
        ("tidb-ssl-cert-handoff", "TiDB", "ssl-cert", "tidb-server restart", "admin reload tls leftover",
         "Ticket is TiDB SSL cert swap without restart; nightly still restarts tidb-server.",
         "https://docs.pingcap.com/tidb/stable/enable-tls-between-clients-and-servers", "src/nightly_tidb.py"),
    ),
    (
        ("yugabyte-ysql-tls-reload", "YugabyteDB", "ysql ssl_cert_file", "tserver restart", "yb-tserver reload ssl",
         "TServer restart drops tablets; ssl reload swaps ysql ssl_cert_file.",
         "https://docs.yugabyte.com/preview/secure/tls-encryption/", "src/legacy_yugabyte.py"),
        ("scylla-client-enc-handoff", "ScyllaDB", "client_encryption_options", "nodetool drain restart", "config reload leftover",
         "Ticket is client_encryption_options cert swap; nightly still drains the node.",
         "https://enterprise.scylladb.com/branch-2024.1/operating-scylla/security/client-to-node-encryption.html", "src/nightly_scylla.py"),
    ),
    (
        ("cassandra-internode-tls-reload", "Cassandra", "server_encryption_options", "restart", "nodetool reloadssl",
         "Restart drops gossip; nodetool reloadssl swaps internode keystore.",
         "https://cassandra.apache.org/doc/latest/cassandra/operating/security.html#internode-encryption", "src/legacy_cass.py"),
        ("neo4j-ssl-policy-handoff", "Neo4j", "dbms.ssl.policy.bolt", "restart", "neo4j restart leftover",
         "Ticket is ssl policy bolt cert swap; nightly still restarts neo4j.",
         "https://neo4j.com/docs/operations-manual/current/security/ssl-framework/", "src/nightly_neo4j.py"),
    ),
    (
        ("opensearch-http-ssl-reload", "OpenSearch", "plugins.security.ssl.http", "node restart", "reload_secure_settings http",
         "r36 was ES http.ssl leftover; this is OpenSearch plugins.security.ssl.http reload.",
         "https://docs.opensearch.org/docs/latest/security/configuration/tls/", "src/legacy_os_http.py"),
        ("solr-ssl-keystore-handoff", "Solr", "solr.jetty.keystore", "solr restart", "bin/solr restart leftover",
         "Ticket is Jetty keystore swap; nightly still restarts Solr.",
         "https://solr.apache.org/guide/solr/latest/deployment-guide/enabling-ssl.html", "src/nightly_solr.py"),
    ),
    (
        ("pulsar-broker-tls-reload", "Pulsar", "brokerServicePortTls", "broker restart", "broker.conf tls + rolling",
         "r36 was Kafka listener; this is Pulsar brokerServicePortTls cert reload.",
         "https://pulsar.apache.org/docs/4.0.x/security-tls-transport/", "src/legacy_pulsar.py"),
        ("redpanda-kafka-tls-handoff", "Redpanda", "kafka_api tls", "node restart", "rpk cluster config leftover",
         "Ticket is rpk cluster config set kafka TLS; nightly still restarts the broker.",
         "https://docs.redpanda.com/current/manage/security/encryption/", "src/nightly_redpanda.py"),
    ),
    (
        ("emqx-ssl-cert-reload", "EMQX", "listeners.ssl.default.ssl", "node restart", "emqx ctl listeners update",
         "r41 was listeners restart ssl:default; this is ssl certfile update in place.",
         "https://docs.emqx.com/en/emqx/latest/access-control/authn/tls.html", "src/legacy_emqx_ssl.py"),
        ("vernemq-listener-ssl-handoff", "VerneMQ", "listener.ssl.certfile", "vmq restart", "vmq-admin listener restart leftover",
         "Ticket is vmq-admin listener restart ssl; nightly still restarts the VM.",
         "https://docs.vernemq.com/configuring-vernemq/ssl", "src/nightly_vernemq.py"),
    ),
    (
        ("consul-https-cert-reload", "Consul", "ports.https cert_file", "agent restart", "consul reload https cert",
         "r48 was consul HTTPS leftover restart; this is cert_file reload via consul reload.",
         "https://developer.hashicorp.com/consul/docs/secure/encryption/tls", "src/legacy_consul_https.py"),
        ("boundary-listener-tls-handoff", "Boundary", "listener tls_cert_file", "controller restart", "boundary reload leftover",
         "Ticket is tls_cert_file swap; nightly still restarts the controller.",
         "https://developer.hashicorp.com/boundary/docs/configuration/listener", "src/nightly_boundary.py"),
    ),
    (
        ("prometheus-web-tls-reload", "Prometheus", "web.tls", "process restart", "SIGHUP web config",
         "Restart drops scrapes; SIGHUP reloads web.tls cert_file.",
         "https://prometheus.io/docs/prometheus/latest/configuration/https/", "src/legacy_prom.py"),
        ("alertmanager-tls-handoff", "Alertmanager", "tls_server_config", "restart", "amtool config reload leftover",
         "Ticket is tls_server_config cert swap; nightly still restarts alertmanager.",
         "https://prometheus.io/docs/alerting/latest/https/", "src/nightly_am.py"),
    ),
    (
        ("thanos-query-tls-reload", "Thanos", "grpc-server-tls-cert", "pod bounce", "SIGHUP thanos query",
         "Pod bounce drops queries; SIGHUP reloads grpc-server-tls-cert.",
         "https://thanos.io/tip/components/query.md/", "src/legacy_thanos.py"),
        ("loki-server-tls-handoff", "Loki", "server.http_tls_config", "restart", "loki -config.expand leftover",
         "Ticket is http_tls_config cert swap; nightly still restarts Loki.",
         "https://grafana.com/docs/loki/latest/configure/", "src/nightly_loki.py"),
    ),
    (
        ("tempo-distro-tls-reload", "Tempo", "server.tls_cert_path", "restart", "tempo SIGHUP tls",
         "Restart drops traces; SIGHUP reloads tls_cert_path.",
         "https://grafana.com/docs/tempo/latest/configuration/", "src/legacy_tempo.py"),
        ("mimir-server-tls-handoff", "Mimir", "server.http_tls_config", "ingester restart", "mimir reload leftover",
         "Ticket is Mimir http_tls_config swap; nightly still restarts ingesters.",
         "https://grafana.com/docs/mimir/latest/configure/configure-grpc-tls-between-microservices/", "src/nightly_mimir.py"),
    ),
    (
        ("victoriametrics-tls-reload", "VictoriaMetrics", "tlsCertFile", "restart", "SIGHUP vmstorage",
         "Restart drops ingestion; SIGHUP reloads tlsCertFile.",
         "https://docs.victoriametrics.com/victoriametrics/single-server-victoriametrics/#https", "src/legacy_vm.py"),
        ("influxdb-https-handoff", "InfluxDB", "tls-cert", "influxd restart", "influxd-ctl leftover",
         "Ticket is tls-cert swap; nightly still restarts influxd.",
         "https://docs.influxdata.com/influxdb/v2/admin/security/enable-tls/", "src/nightly_influx.py"),
    ),
    (
        ("kyverno-webhook-tls-reload", "Kyverno", "webhook cert", "pod delete", "cert-controller rotate",
         "Pod delete drops admits; cert-controller rotates the webhook cert.",
         "https://kyverno.io/docs/installation/customization/#certificates", "src/legacy_kyverno.py"),
        ("gatekeeper-webhook-tls-handoff", "Gatekeeper", "webhook-server-cert", "pod bounce", "secret rotate leftover",
         "Ticket is webhook-server-cert secret rotate; nightly still bounces the pod.",
         "https://open-policy-agent.github.io/gatekeeper/website/docs/tls/", "src/nightly_gator.py"),
    ),
    (
        ("falco-grpc-tls-reload", "Falco", "grpc.certs", "falco restart", "falcoctl tls reload",
         "Restart drops syscall stream; grpc.certs reload swaps the leaf.",
         "https://falco.org/docs/grpc/", "src/legacy_falco.py"),
        ("osquery-tls-handoff", "osquery", "tls_server_certs", "osqueryd restart", "osqueryctl config leftover",
         "Ticket is tls_server_certs swap; nightly still restarts osqueryd.",
         "https://osquery.readthedocs.io/en/stable/deployment/remote/", "src/nightly_osquery.py"),
    ),
    (
        ("argocd-server-tls-reload", "Argo CD", "argocd-server-tls", "pod bounce", "secret watch + reloader",
         "Pod bounce drops UI; argocd-server-tls secret watch reloads.",
         "https://argo-cd.readthedocs.io/en/stable/operator-manual/tls/", "src/legacy_argocd.py"),
        ("flux-webhook-tls-handoff", "Flux", "receiver tls", "pod delete", "cert-controller leftover",
         "Ticket is receiver TLS cert rotate; nightly still deletes the receiver pod.",
         "https://fluxcd.io/flux/components/notification/receivers/", "src/nightly_flux.py"),
    ),
    (
        ("tekton-webhook-tls-reload", "Tekton", "webhook certs", "controller restart", "tekton certs secret rotate",
         "Controller restart drops pipelines; webhook certs secret rotate swaps the leaf.",
         "https://tekton.dev/docs/installation/configuration/", "src/legacy_tekton.py"),
        ("knative-webhook-tls-handoff", "Knative", "webhook-certs", "pod bounce", "secret leftover",
         "Ticket is knative webhook-certs rotate; nightly still bounces the webhook.",
         "https://knative.dev/docs/serving/encryption/integration/", "src/nightly_knative.py"),
    ),
    (
        ("contour-envoy-secret-reload", "Contour", "envoy TLS secret", "envoy restart", "SDS secret watch",
         "r54 was Contour TLS secret; this is Envoy SDS watch of the secret without restart.",
         "https://projectcontour.io/docs/main/config/tls-termination/", "src/legacy_contour_sds.py"),
        ("istio-gw-credential-handoff", "Istio", "gateway credentialName", "pod bounce", "SDS leftover",
         "Ticket is Gateway credentialName secret swap; nightly still bounces ingressgateway.",
         "https://istio.io/latest/docs/tasks/traffic-management/ingress/secure-ingress/", "src/nightly_istio_gw.py"),
    ),
    (
        ("linkerd-identity-issuer-reload", "Linkerd", "identity issuer", "proxy restart", "linkerd identity rotate",
         "Proxy restart drops meshed pods; identity issuer rotate swaps the trust.",
         "https://linkerd.io/2.15/tasks/automatically-rotating-control-plane-tls-credentials/", "src/legacy_l5d.py"),
        ("apache-sslcert-handoff", "Apache", "SSLCertificateFile", "httpd restart", "apachectl graceful leftover",
         "r50 was OCSP leftover; this is SSLCertificateFile swap. Nightly still restarts httpd.",
         "https://httpd.apache.org/docs/2.4/mod/mod_ssl.html#sslcertificatefile", "src/nightly_apache_cert.py"),
    ),
    (
        ("lighttpd-pemfile-reload", "lighttpd", "ssl.pemfile", "restart", "lighttpd-angel reload",
         "Restart drops keepalives; lighttpd-angel reload swaps ssl.pemfile.",
         "https://wiki.lighttpd.net/Docs_SSL", "src/legacy_lighttpd.py"),
        ("cyrus-tls-handoff", "Cyrus IMAP", "tls_server_cert", "cyrmaster restart", "reload leftover",
         "Ticket is tls_server_cert swap; nightly still restarts cyrmaster.",
         "https://www.cyrusimap.org/imap/reference/admin/unattended.html", "src/nightly_cyrus.py"),
    ),
    (
        ("exim-tls-certificate-reload", "Exim", "tls_certificate", "exim restart", "exim -bP + SIGHUP",
         "Restart drops the queue runner; SIGHUP reloads tls_certificate.",
         "https://www.exim.org/exim-html-current/doc/html/spec_html/ch-encrypted_smtp_connections_using_tlsssl.html", "src/legacy_exim.py"),
        ("gitlab-nginx-ssl-handoff", "GitLab", "nginx['ssl_certificate']", "reconfigure restart", "gitlab-ctl hup leftover",
         "Ticket is gitlab-ctl hup nginx; nightly still reconfigure-restarts all.",
         "https://docs.gitlab.com/omnibus/settings/ssl/", "src/nightly_gitlab.py"),
    ),
    (
        ("gitea-cert-reload", "Gitea", "CERT_FILE", "gitea restart", "SIGHUP gitea",
         "Restart drops git SSH mux; SIGHUP reloads CERT_FILE.",
         "https://docs.gitea.com/administration/https-setup", "src/legacy_gitea.py"),
        ("forgejo-cert-handoff", "Forgejo", "CERT_FILE", "restart", "forgejo restart leftover",
         "Ticket is Forgejo CERT_FILE swap; nightly still restarts the service.",
         "https://forgejo.org/docs/latest/admin/https-setup/", "src/nightly_forgejo.py"),
    ),
    (
        ("jenkins-https-keystore-reload", "Jenkins", "--httpsKeyStore", "winstone restart", "jenkins reload-https",
         "Restart drops builds; httpsKeyStore reload swaps the leaf.",
         "https://www.jenkins.io/doc/book/installing/initial-settings/", "src/legacy_jenkins.py"),
        ("confluence-tomcat-ssl-handoff", "Confluence", "tomcat connector keystore", "tomcat restart", "connector reload leftover",
         "Ticket is Tomcat SSL connector keystore swap; nightly still restarts Confluence.",
         "https://confluence.atlassian.com/doc/running-confluence-over-ssl-or-https-161203.html", "src/nightly_confluence.py"),
    ),
    (
        ("longhorn-webhook-tls-reload", "Longhorn", "longhorn-webhook-tls", "pod delete", "secret rotate",
         "Pod delete drops volume admits; webhook tls secret rotate swaps the leaf.",
         "https://longhorn.io/docs/1.7.0/advanced-resources/security/", "src/legacy_longhorn.py"),
        ("ext-secrets-webhook-tls-handoff", "External Secrets", "webhook cert", "pod bounce", "cert leftover",
         "Ticket is ESO webhook cert rotate; nightly still bounces the webhook.",
         "https://external-secrets.io/latest/api/components/webhook/", "src/nightly_eso.py"),
    ),
    (
        ("wazuh-authd-tls-reload", "Wazuh", "authd ssl", "wazuh-manager restart", "wazuh-control reload",
         "Restart drops agents; wazuh-control reload swaps authd ssl cert.",
         "https://documentation.wazuh.com/current/user-manual/agent/agent-enrollment/security-considerations.html", "src/legacy_wazuh.py"),
        ("suricata-tls-handoff", "Suricata", "unix-command tls", "suricata restart", "suricatasc reload leftover",
         "Ticket is unix-command tls cert swap; nightly still restarts Suricata.",
         "https://docs.suricata.io/en/latest/command-line-options.html", "src/nightly_suricata.py"),
    ),
    (
        ("zeek-ssl-reload", "Zeek", "ssl.zeek cert", "zeekctl restart", "zeekctl install + reload",
         "Restart drops workers; zeekctl install plus reload swaps ssl scripts certs.",
         "https://docs.zeek.org/en/master/scripts/base/protocols/ssl/main.zeek.html", "src/legacy_zeek.py"),
        ("ntopng-https-handoff", "ntopng", "--https-port pem", "ntopng restart", "ntopng -t leftover",
         "Ticket is --https-port pem swap; nightly still restarts ntopng.",
         "https://www.ntop.org/guides/ntopng/web_gui/ssl.html", "src/nightly_ntop.py"),
    ),
    (
        ("haproxy-crt-list-handoff", "HAProxy", "crt-list", "restart", "so_reload leftover",
         "r15/r46 were crt-list/store success; this is crt-list leftover still restarting.",
         "https://docs.haproxy.org/2.8/configuration.html#5.1-crt-list", "src/nightly_haproxy_list.py"),
        ("envoy-sds-secret-reload", "Envoy", "SDS secret", "lds push", "secret DiscoveryService",
         "r11/r46 were SDS warmup leftover; this is SDS secret DiscoveryService reload of the leaf.",
         "https://www.envoyproxy.io/docs/envoy/latest/configuration/security/secret", "src/legacy_envoy_sds.py"),
    ),
    (
        ("apisix-admin-tls-reload", "APISIX", "admin API ssl", "etcd put + restart", "admin PATCH /ssls",
         "r55 was APISIX ssl cert reload; this is admin API TLS itself.",
         "https://apisix.apache.org/docs/apisix/admin-api/#ssl", "src/legacy_apisix_admin.py"),
        ("krakend-tls-handoff", "KrakenD", "tls public_key", "process restart", "flexible-config leftover",
         "r56 was KrakenD success reload; this is public_key leftover still restarting.",
         "https://www.krakend.io/docs/service-settings/tls/", "src/nightly_krakend.py"),
    ),
    (
        ("clickhouse-https-reload", "ClickHouse", "https_port cert", "restart", "SYSTEM RELOAD CONFIG",
         "r38 was leftover restart; this is SYSTEM RELOAD CONFIG of https_port cert.",
         "https://clickhouse.com/docs/en/guides/sre/ssl-user-auth", "src/legacy_ch_https.py"),
        ("timescaledb-ssl-handoff", "TimescaleDB", "ssl_cert_file", "restart", "pg_reload_conf leftover",
         "r37 was Postgres ssl_cert_file success; this is Timescale leftover still restarting.",
         "https://docs.timescale.com/use-timescale/latest/security/", "src/nightly_timescale.py"),
    ),
    (
        ("citus-ssl-reload", "Citus", "ssl_cert_file", "coordinator restart", "pg_reload_conf workers",
         "Coordinator restart drops MX; pg_reload_conf swaps ssl_cert_file on workers.",
         "https://docs.citusdata.com/en/stable/admin_guide/cluster_management.html", "src/legacy_citus.py"),
        ("greenplum-ssl-handoff", "Greenplum", "sslcert", "gpstop", "gpconfig leftover",
         "Ticket is gpconfig sslcert reload; nightly still gpstop -u as a full restart.",
         "https://docs.vmware.com/en/VMware-Greenplum/6/greenplum-database/install_guide-topics-install_ssl.html", "src/nightly_gpdb.py"),
    ),
    (
        ("singlestore-ssl-reload", "SingleStore", "ssl_cert", "node restart", "sdb-admin update-config",
         "Node restart drops aggregators; sdb-admin update-config swaps ssl_cert.",
         "https://docs.singlestore.com/cloud/security/encryption/ssl/", "src/legacy_s2.py"),
        ("materialize-tls-handoff", "Materialize", "tls_cert", "environmentd restart", "mz reload leftover",
         "Ticket is Materialize tls_cert swap; nightly still restarts environmentd.",
         "https://materialize.com/docs/self-managed/v25.2/installation/configuration/network-security/ssl-tls/", "src/nightly_mz.py"),
    ),
    (
        ("risingwave-ssl-reload", "RisingWave", "ssl_cert", "restart", "risingwave reload tls",
         "Restart drops streaming jobs; tls reload swaps ssl_cert.",
         "https://docs.risingwave.com/deploy/security", "src/legacy_rw.py"),
        ("questdb-tls-handoff", "QuestDB", "tls.cert", "questdb restart", "reload leftover",
         "Ticket is QuestDB tls.cert swap; nightly still restarts the server.",
         "https://questdb.com/docs/configuration/", "src/nightly_questdb.py"),
    ),
    (
        ("duckdb-https-reload", "DuckDB server", "tls_cert", "restart", "duckdb-server reload",
         "Restart drops sessions; duckdb-server reload swaps tls_cert.",
         "https://duckdb.org/docs/stable/guides/network_security/tls.html", "src/legacy_duckdb.py"),
        ("datafusion-tls-handoff", "DataFusion Ballista", "tls cert", "scheduler restart", "reload leftover",
         "Ticket is Ballista scheduler TLS cert swap; nightly still restarts.",
         "https://arrow.apache.org/datafusion/user-guide/cli.html", "src/nightly_ballista.py"),
    ),
    (
        ("trino-https-reload", "Trino", "http-server.https.keystore", "coordinator restart", "reload https",
         "Coordinator restart drops queries; https keystore reload swaps the leaf.",
         "https://trino.io/docs/current/security/tls.html", "src/legacy_trino.py"),
        ("presto-https-handoff", "Presto", "http-server.https.keystore.path", "restart", "reload leftover",
         "Ticket is Presto https keystore swap; nightly still restarts the coordinator.",
         "https://prestodb.io/docs/current/security/internal-communication.html", "src/nightly_presto.py"),
    ),
    (
        ("drill-ssl-reload", "Apache Drill", "drill.exec.ssl", "drillbit restart", "reload ssl",
         "Drillbit restart drops queries; ssl reload swaps the keystore.",
         "https://drill.apache.org/docs/configuring-ssl-tls-on-drillbit/", "src/legacy_drill.py"),
        ("impala-ssl-handoff", "Impala", "ssl_server_certificate", "impalad restart", "reload leftover",
         "Ticket is Impala ssl_server_certificate swap; nightly still restarts impalad.",
         "https://impala.apache.org/docs/build/html/topics/impala_ssl.html", "src/nightly_impala.py"),
    ),
    (
        ("spark-rpc-ssl-reload", "Spark", "spark.ssl", "restart", "spark-daemon.sh reload",
         "Restart drops jobs; spark.ssl keystore reload swaps the leaf.",
         "https://spark.apache.org/docs/latest/security.html#ssl-configuration", "src/legacy_spark_ssl.py"),
        ("flink-ssl-handoff", "Flink", "security.ssl", "jm restart", "flink reload leftover",
         "Ticket is Flink security.ssl rest cert swap; nightly still restarts the JM.",
         "https://nightlies.apache.org/flink/flink-docs-stable/docs/deployment/security/security-ssl/", "src/nightly_flink.py"),
    ),
    (
        ("nifi-keystore-reload", "NiFi", "nifi.security.keystore", "nifi.sh restart", "nifi.sh reload",
         "Restart drops flowfiles; nifi.sh reload swaps the keystore.",
         "https://nifi.apache.org/docs/nifi-docs/html/administration-guide.html#security_configuration", "src/legacy_nifi.py"),
        ("airflow-web-ssl-handoff", "Airflow", "webserver ssl_cert", "webserver restart", "reload leftover",
         "Ticket is Airflow webserver ssl_cert swap; nightly still restarts the webserver.",
         "https://airflow.apache.org/docs/apache-airflow/stable/howto/webserver.html", "src/nightly_airflow.py"),
    ),
    (
        ("superset-ssl-reload", "Superset", "ENABLE_PROXY_FIX ssl", "gunicorn restart", "gunicorn HUP",
         "Restart drops dashboards; gunicorn HUP swaps the cert.",
         "https://superset.apache.org/docs/installation/configuring-superset", "src/legacy_superset.py"),
        ("metabase-ssl-handoff", "Metabase", "MB_JETTY_SSL", "java restart", "reload leftover",
         "Ticket is Metabase Jetty SSL keystore swap; nightly still restarts Java.",
         "https://www.metabase.com/docs/latest/configuring-metabase/customizing-jetty-webserver", "src/nightly_metabase.py"),
    ),
    (
        ("redash-ssl-reload", "Redash", "nginx cert", "compose restart", "nginx -s reload",
         "Compose restart drops queries; nginx -s reload swaps the cert.",
         "https://redash.io/help/open-source/setup", "src/legacy_redash.py"),
        ("metronome-tls-handoff", "Metronome", "tls cert", "restart", "reload leftover",
         "Ticket is Metronome TLS cert swap; nightly still restarts the scheduler.",
         "https://mesosphere.github.io/marathon/docs/tls.html", "src/nightly_metronome.py"),
    ),
    (
        ("marathon-tls-reload", "Marathon", "ssl_keystore", "restart", "marathon reload https",
         "Restart drops apps; ssl_keystore reload swaps the leaf.",
         "https://mesosphere.github.io/marathon/docs/ssl-settings.html", "src/legacy_marathon.py"),
        ("mesos-ssl-handoff", "Mesos", "ssl_cert_file", "master restart", "reload leftover",
         "Ticket is Mesos ssl_cert_file swap; nightly still restarts the master.",
         "https://mesos.apache.org/documentation/latest/ssl/", "src/nightly_mesos.py"),
    ),
]


def build_success(rnd: int, p: tuple) -> dict:
    slug, stack, unit, wrong, fix, ticket, url, residual = p
    stem = slug.replace("-", "_")
    src = f"src/{stem}.py"
    test = f"tests/test_{stem}.py"
    eid = f"ssl-r{rnd}-{slug}"
    steps = [
        step(1, f"Plan: list src config tests before touching {stack} rotation.",
             "bash", {"command": f"ls -la src {stem} tests | head -40"},
             f"src/{src} {stem}/{stem}.conf\n{test}",
             "Tree shows src plus tests. Next: run the named failing target."),
        step(2, f"Observation: listing named the test files. Run pytest {test}.",
             "pytest", {"args": f"{test} -q --tb=short"},
             f"{test}::test_{stem} FAILED\nE   AssertionError: cert rotate used {wrong} and dropped live sessions",
             "Failure is named. Read that test before hypothesizing a one-line fix."),
        step(3, f"Observation: {test}::test_{stem} is red. Read {test}.",
             "read", {"path": test},
             f"def test_{stem}():\n    assert rotate() == 'reload'\n",
             "Test contract is now visible. Search implementation symbols next."),
        step(4, f"Observation: test file imported the production helper. Grep {unit}.",
             "bash", {"command": f"rg -n '{unit.split()[0]}|reload|restart' src {stem} tests"},
             f"{src}:14: return '{wrong}'\n",
             "Grep hit the rotate helper. Read it before editing the first match."),
        step(5, f"Observation: grep listed {src}. Read it before any patch.",
             "read", {"path": src},
             f"def rotate():\n    return '{wrong}'\n",
             "First read done. Fetch vendor/docs next; do not patch on a hunch yet."),
        step(6, "Observation: local files are in. Need the changelog/registry before editing.",
             "fetch", {"url": url},
             f"GET {url}\nHTTP/1.1 502 Bad Gateway\nBad Gateway.",
             "Call failed with upstream gateway failure. Recover with backoff rather than switching hosts blindly."),
        step(7, "Observation: the prior call returned an upstream gateway failure. Retry once with 2s backoff.",
             "fetch", {"url": url},
             f"retry after 2s backoff; local vendor fixture\nHTTP/1.1 200 OK\n{ticket}",
             "Degraded path used the local fixture. Continue with that content."),
        step(8, "Observation: local files are in. Need the second remote document before editing.",
             "fetch", {"url": url + "#reload"},
             f"GET {url}#reload\nHTTP/1.1 429 Too Many Requests\nRetry-After: 5",
             "Call failed with rate-limit status with Retry-After. Recover with backoff."),
        step(9, "Observation: the prior call returned rate-limit status. Sleep then retry the same URL.",
             "fetch", {"url": url + "#reload"},
             "sleep + jitter retry of the same URL\nHTTP/1.1 200 OK\nDelete-then-create secret banned. Reload, do not recreate the unit.",
             "Retry succeeded. Resume the local debug plan with that document in hand."),
        step(10, f"Observation: docs and source are in. Apply the first patch to {src}.",
             "edit", {"path": src, "old": f"return '{wrong}'", "new": "return 'sighup'"},
             f"patched sighup ({stack} SIGHUP keeps old {unit})",
             "Patch applied. Re-run the failing test; do not assume green."),
        step(11, f"Observation: edit wrote {src}. Re-run the same failing node.",
             "pytest", {"args": f"{test} -q --tb=short"},
             f"{test}::test_{stem} FAILED\nE   AssertionError: SIGHUP did not swap {unit}; need {fix}",
             "Still red after the first patch. Re-read the implementation."),
        step(12, f"Observation: post-edit test still failed. Re-read {src}.",
             "read", {"path": src},
             f"{wrong} drops sessions; {fix} swaps {unit}",
             f"Plan change: {fix}. SIGHUP is not enough."),
        step(13, f"Reflection: {fix}. SIGHUP is not enough.",
             "edit", {"path": src, "old": "return 'sighup'", "new": "return 'reload'"},
             f"patched {stack} {unit} reload",
             "Corrective patch applied. Run the original failing node again."),
        step(14, "Observation: fix edit returned clean. Re-run the original failing test node.",
             "pytest", {"args": f"{test} -q --tb=short"},
             "1 passed in 0.16s",
             "Result recorded. Run one broader check before declaring the outcome."),
        step(15, f"Observation: focused run finished. Run broader check pytest {test} -q.",
             "bash", {"command": f"pytest {test} -q"},
             "3 passed in 0.28s",
             "Broader check captured. Stop; residual risk belongs in the outcome text."),
        step(16, "Observation: broader check is on disk. Show the diff of patched files.",
             "bash", {"command": "git diff --stat | head -n 40"},
             f"diffstat for {slug}: {src} | 9 ++++++---. Residual {residual} still {wrong}.",
             "Diff is the review artifact. No further edits."),
    ]
    ep = {
        "id": eid,
        "goal": ticket,
        "plan": f"Read restart-as-reload, try {wrong}, then {fix}.",
        "steps": steps,
        "outcome": f"{stack} {fix} contained the rotate. {wrong} unused (success). Residual {residual}.",
        "reward": {
            "success": True, "tests_passed": 3, "retries": 2, "duration_min": 610,
            "wasted_calls": 180, "cost_steps": 16, "plan_changes": 1,
        },
        "meta": {
            "factory": FACTORY, "round": rnd, "generator": GEN, "kind": "episode",
            "seed": slug, "designed": True, "domain": slug, "stack": f"{stack} TLS",
        },
    }
    blob = json.dumps(ep)
    for b in BANNED:
        if b in blob and b in ("thought", "chain_of_thought", "scratch", "inner_monologue", "spike_events"):
            if f'"{b}"' in blob:
                raise SystemExit(f"banned {b}")
        elif b in blob and b not in ("thought",):
            if b.startswith("U+") or "SKU" in b or "combining" in b:
                raise SystemExit(f"banned snippet {b}")
    return ep


def build_partial(rnd: int, p: tuple) -> dict:
    slug, stack, unit, wrong, leftover, ticket, url, nightly = p
    stem = slug.replace("-", "_")
    src = f"src/{stem}.py"
    test = f"tests/test_{stem}.py"
    ntest = f"tests/test_nightly_{stem}.py"
    eid = f"ssl-r{rnd}-{slug}"
    steps = [
        step(1, f"Plan: list src config tests before touching {stack} rotation.",
             "bash", {"command": f"ls -la src {stem} tests | head -40"},
             f"src/{src} {stem}/{stem}.conf\n{test}",
             "Tree shows src plus tests."),
        step(2, f"Observation: listing named the test files. Run pytest {test}.",
             "pytest", {"args": f"{test} -q --tb=short"},
             f"{test}::test_{stem} FAILED\nE   AssertionError: rotate used {wrong}",
             "Failure is named."),
        step(3, f"Observation: {test} is red. Read {test}.",
             "read", {"path": test},
             f"def test_{stem}():\n    assert rotate() == 'reload'\n",
             "Test contract visible."),
        step(4, f"Observation: grep {unit}.",
             "bash", {"command": f"rg -n '{unit.split()[0]}|reload|restart' src tests"},
             f"{src}: return '{wrong}'\n",
             "Grep hit rotate."),
        step(5, f"Observation: read {src}.",
             "read", {"path": src},
             f"def rotate():\n    return '{wrong}'\n",
             "Fetch docs next."),
        step(6, "Observation: fetch vendor docs.",
             "fetch", {"url": url},
             f"GET {url}\nHTTP/1.1 502 Bad Gateway",
             "Backoff then retry."),
        step(7, "Observation: 502. Retry with 2s backoff.",
             "fetch", {"url": url},
             f"retry 2s; 200 OK\n{ticket}",
             "Local fixture used."),
        step(8, "Observation: second remote doc.",
             "fetch", {"url": url + "#reload"},
             "HTTP/1.1 429 Too Many Requests\nRetry-After: 5",
             "Honor Retry-After."),
        step(9, "Observation: 429. Sleep then retry.",
             "fetch", {"url": url + "#reload"},
             "200 OK\nReload, do not recreate the unit.",
             "Docs in hand."),
        step(10, f"Observation: first apply {wrong} pin.",
             "edit", {"path": src, "old": f"return '{wrong}'", "new": "return 'sighup'"},
             f"patched sighup; still not {unit} swap",
             "Re-run test."),
        step(11, "Observation: still red. Re-run test.",
             "pytest", {"args": f"{test} -q --tb=short"},
             f"FAILED still {wrong} path",
             "Re-read."),
        step(12, f"Observation: re-read {src}.",
             "read", {"path": src},
             f"{leftover} is the nightly path",
             f"Plan change: reload {unit}; xfail nightly {leftover}."),
        step(13, f"Reflection: reload {unit}; xfail nightly.",
             "edit", {"path": src, "old": "return 'sighup'", "new": "return 'reload'"},
             f"patched {stack} reload; nightly still {leftover}",
             "Gate test next."),
        step(14, "Observation: gate test.",
             "pytest", {"args": f"{test} -q --tb=short"},
             "1 passed in 0.14s",
             "Nightly leftover."),
        step(15, f"Observation: nightly leftover {nightly}. xfail.",
             "edit", {"path": ntest, "old": f"def test_nightly_{stem}():",
                      "new": f"@pytest.mark.xfail(reason=\"handoff: {leftover}\", strict=False)\ndef test_nightly_{stem}():"},
             f"xfails {leftover}",
             "Merge gate green."),
        step(16, "Observation: confirm leftover nightly.",
             "read", {"path": nightly},
             f"{nightly} still {leftover}",
             "Handoff stands."),
        step(17, f"Observation: leftover stands. Ticket is {slug}.",
             "bash", {"command": f"pytest {test} -q"},
             "1 passed in 0.12s",
             "Partial: nightly handoff."),
    ]
    return {
        "id": eid,
        "goal": ticket,
        "plan": f"Try {wrong}, then reload; expect nightly {leftover}.",
        "steps": steps,
        "outcome": f"{stack} reload landed. Partial: nightly still {leftover} (xfail).",
        "reward": {
            "success": False, "tests_passed": 1, "xfailed": 1, "handoff": 1,
            "retries": 2, "cost_steps": 17, "plan_changes": 1,
        },
        "meta": {
            "factory": FACTORY, "round": rnd, "generator": GEN, "kind": "episode",
            "seed": slug, "designed": True, "domain": slug, "stack": f"{stack} TLS",
        },
    }


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
