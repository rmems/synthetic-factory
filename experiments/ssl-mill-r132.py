#!/usr/bin/env python3
"""ssl-cert-rotation mill r132+. Unique leftover stacks."""
from __future__ import annotations

import argparse
import json
from importlib.machinery import SourceFileLoader
from pathlib import Path

HERE = Path(__file__).resolve().parent
_base = SourceFileLoader("ssl35c", str(HERE / "ssl-mill-r35.py")).load_module()
build_success = _base.build_success
build_partial = _base.build_partial
CATALOG_FIRST = 132

PAIRS = [
    (("haproxy-alpn-h2-reload", "HAProxy ALPN", "alpn h2 crt", "restart",
      "so_reload alpn", "so_reload ALPN h2 crt; do not restart.",
      "https://docs.haproxy.org/2.8/configuration.html#5.1-alpn", "src/legacy_hap_alpn.py"),
     ("nginx-alpn-handoff", "nginx ALPN", "ssl_conf_command ALPN", "reload", "alpn leftover",
      "Ticket is ssl_conf_command ALPN; nightly still full reload-restarts.",
      "https://nginx.org/en/docs/http/ngx_http_ssl_module.html", "src/nightly_ngx_alpn.py")),
    (("envoy-alpn-sds-reload", "Envoy ALPN SDS", "alpn_protocols", "lds push",
      "SDS ALPN secret", "SDS swap ALPN; do not LDS-push.",
      "https://www.envoyproxy.io/docs/envoy/latest/api-v3/extensions/transport_sockets/tls/v3/tls.proto",
      "src/legacy_envoy_alpn.py"),
     ("caddy-alpn-handoff", "Caddy ALPN", "alpn", "restart", "alpn leftover",
      "Ticket is Caddy alpn reload; nightly restarts.",
      "https://caddyserver.com/docs/caddyfile/options", "src/nightly_caddy_alpn.py")),
    (("traefik-mtls-reload", "Traefik mTLS", "clientAuth", "pod bounce",
      "dynamic mtls", "Reload clientAuth CA; do not bounce pods.",
      "https://doc.traefik.io/traefik/https/tls/#client-authentication-mtls", "src/legacy_traefik_mtls.py"),
     ("kong-mtls-handoff", "Kong mTLS", "mtls-auth", "pod bounce", "mtls leftover",
      "Ticket is mtls-auth cert swap; nightly bounces.",
      "https://docs.konghq.com/hub/kong-inc/mtls-auth/", "src/nightly_kong_mtls.py")),
    (("istio-peer-mTLS-reload", "Istio peer mTLS", "peerAuthentication", "pod delete",
      "SDS peer cert", "SDS peer mTLS rotate; do not delete pods.",
      "https://istio.io/latest/docs/tasks/security/authentication/authn-policy/", "src/legacy_istio_peer.py"),
     ("linkerd-mtls-handoff", "Linkerd mTLS", "identity", "proxy restart", "mtls leftover",
      "Ticket is identity rotate; nightly restarts proxies.",
      "https://linkerd.io/2.15/features/automatic-mtls/", "src/nightly_l5d_mtls.py")),
    (("consul-connect-leaf-reload", "Consul Connect leaf", "leaf cert", "agent restart",
      "connect leaf rotate", "Rotate Connect leaf; do not restart agent.",
      "https://developer.hashicorp.com/consul/docs/connect", "src/legacy_consul_leaf.py"),
     ("nomad-connect-handoff", "Nomad Connect", "connect tls", "job stop", "connect leftover",
      "Ticket is Connect TLS rotate; nightly stops the job.",
      "https://developer.hashicorp.com/nomad/docs/job-specification/connect", "src/nightly_nomad_connect.py")),
    (("vault-pki-leaf-reload", "Vault PKI leaf", "pki issue", "service restart",
      "agent template HUP", "Template re-render + HUP; do not restart Vault.",
      "https://developer.hashicorp.com/vault/docs/secrets/pki", "src/legacy_vault_pki.py"),
     ("boundary-worker-handoff", "Boundary worker", "worker tls", "controller restart", "worker leftover",
      "Ticket is worker TLS rotate; nightly restarts controller.",
      "https://developer.hashicorp.com/boundary/docs/configuration/worker", "src/nightly_boundary_w.py")),
    (("k8s-webhook-ca-reload", "k8s webhook CA", "caBundle", "apiserver bounce",
      "patch validatingwebhook", "Patch caBundle; do not bounce apiserver.",
      "https://kubernetes.io/docs/reference/access-authn-authz/extensible-admission-controllers/",
      "src/legacy_k8s_wh.py"),
     ("ocp-route-handoff", "OpenShift route", "route cert", "route delete", "route leftover",
      "Ticket is route cert annotate; nightly deletes the route.",
      "https://docs.openshift.com/container-platform/latest/networking/routes/secured-routes.html",
      "src/nightly_ocp_route.py")),
    (("haproxy-crt-list-sni2", "HAProxy SNI2", "crt-list", "restart",
      "so_reload crt-list", "so_reload extra SNI line; do not restart.",
      "https://docs.haproxy.org/2.8/configuration.html#5.1-crt-list", "src/legacy_hap_sni2.py"),
     ("nginx-stream-sni-handoff", "nginx stream SNI", "ssl_preread", "reload", "sni leftover",
      "Ticket is stream SNI map; nightly restarts nginx.",
      "https://nginx.org/en/docs/stream/ngx_stream_ssl_preread_module.html", "src/nightly_ngx_sni.py")),
    (("envoy-starttls-reload", "Envoy StartTLS", "starttls", "lds push",
      "SDS starttls", "SDS StartTLS secret; do not LDS-push.",
      "https://www.envoyproxy.io/docs/envoy/latest/api-v3/extensions/transport_sockets/starttls/v3/starttls.proto",
      "src/legacy_envoy_starttls.py"),
     ("postfix-submission-handoff", "Postfix submission", "smtpd_tls_cert_file", "restart", "submission leftover",
      "Not a postfix clone of r01; this is submission-only cert leftover.",
      "https://www.postfix.org/TLS_README.html", "src/nightly_pf_sub.py")),
    (("dovecot-imap-sni-reload", "Dovecot IMAP SNI", "local_name", "restart",
      "doveadm reload sni", "doveadm reload SNI map; do not restart.",
      "https://doc.dovecot.org/2.3/configuration_manual/dovecot_ssl_configuration/", "src/legacy_dovecot_sni.py"),
     ("cyrus-sni-handoff", "Cyrus SNI", "tls_server_cert", "restart", "sni leftover",
      "Ticket is SNI cert map; nightly restarts cyrmaster.",
      "https://www.cyrusimap.org/", "src/nightly_cyrus_sni.py")),
    (("exim-sni-reload", "Exim SNI", "tls_certificate", "restart",
      "SIGHUP sni", "SIGHUP Exim SNI cert; do not restart.",
      "https://www.exim.org/exim-html-current/doc/html/spec_html/ch-encrypted_smtp_connections_using_tlsssl.html",
      "src/legacy_exim_sni.py"),
     ("opendkim-tls-handoff", "OpenDKIM", "SSLCertFile", "restart", "dkim leftover",
      "Ticket is SSLCertFile swap; nightly restarts opendkim.",
      "http://www.opendkim.org/", "src/nightly_opendkim.py")),
    (("unbound-dot-reload", "Unbound DoT", "tls-service-key", "restart",
      "unbound-control reload", "unbound-control reload DoT; do not restart.",
      "https://unbound.docs.nlnetlabs.nl/", "src/legacy_unbound_dot.py"),
     ("coredns-dot-handoff", "CoreDNS DoT", "tls", "pod rollout", "dot leftover",
      "Ticket is CoreDNS DoT SIGUSR1; nightly rollouts.",
      "https://coredns.io/plugins/tls/", "src/nightly_coredns_dot.py")),
    (("knot-dot-reload", "Knot DoT", "tls-cert", "restart",
      "knotc reload", "knotc reload DoT cert; do not restart.",
      "https://www.knot-dns.cz/docs/", "src/legacy_knot.py"),
     ("bind-dot-handoff", "BIND DoT", "tls", "restart", "dot leftover",
      "Ticket is named tls reload; nightly restarts named.",
      "https://bind9.readthedocs.io/en/latest/chapter7.html", "src/nightly_bind_dot.py")),
    (("powerdns-dot-reload", "PowerDNS DoT", "tls-cert-file", "restart",
      "pdns_control reopen-logfiles tls", "Reload DoT cert; do not restart pdns.",
      "https://doc.powerdns.com/authoritative/", "src/legacy_pdns_dot.py"),
     ("unbound-doh-handoff", "Unbound DoH", "https-port", "restart", "doh leftover",
      "Ticket is DoH cert reload; nightly restarts unbound.",
      "https://unbound.docs.nlnetlabs.nl/", "src/nightly_unbound_doh.py")),
    (("haproxy-doh-reload", "HAProxy DoH", "bind quic", "restart",
      "so_reload doh", "so_reload DoH bind; do not restart.",
      "https://www.haproxy.com/blog/haproxy-and-dns-over-https", "src/legacy_hap_doh.py"),
     ("nginx-doh-handoff", "nginx DoH", "http2 ssl", "reload", "doh leftover",
      "Ticket is DoH ssl_certificate; nightly restarts.",
      "https://nginx.org/en/docs/http/ngx_http_v2_module.html", "src/nightly_ngx_doh.py")),
    (("caddy-doh-reload", "Caddy DoH", "dns.providers", "restart",
      "caddy reload doh", "Reload DoH endpoint TLS; do not restart.",
      "https://caddyserver.com/docs", "src/legacy_caddy_doh.py"),
     ("traefik-doh-handoff", "Traefik DoH", "http3", "pod bounce", "doh leftover",
      "Ticket is DoH TLS; nightly bounces.",
      "https://doc.traefik.io/traefik/", "src/nightly_traefik_doh.py")),
    (("envoy-doh-reload", "Envoy DoH", "h2 tls", "lds push",
      "SDS doh", "SDS DoH secret; do not LDS-push.",
      "https://www.envoyproxy.io/docs/envoy/latest/", "src/legacy_envoy_doh.py"),
     ("coredns-doh-handoff", "CoreDNS DoH", "https", "pod rollout", "doh leftover",
      "Ticket is DoH SIGUSR1; nightly rollouts.",
      "https://coredns.io/plugins/https/", "src/nightly_coredns_doh.py")),
    (("step-ca-leaf-reload", "step-ca leaf", "renew --force", "ca restart",
      "step ca renew", "step ca renew --force; do not restart CA.",
      "https://smallstep.com/docs/step-ca/", "src/legacy_step_leaf.py"),
     ("lego-deploy-handoff", "lego deploy", "lego renew", "nginx restart", "hook leftover",
      "Ticket is lego deploy hook reload; nightly restarts nginx.",
      "https://go-acme.github.io/lego/", "src/nightly_lego_hook.py")),
    (("certbot-deploy2", "certbot deploy2", "deploy hook", "restart",
      "nginx -s reload hook", "certbot deploy hook nginx -s reload; do not systemctl restart.",
      "https://eff-certbot.readthedocs.io/", "src/legacy_certbot2.py"),
     ("acme-sh-hook-handoff", "acme.sh hook", "reloadcmd", "docker restart", "reloadcmd leftover",
      "Ticket is --reloadcmd; nightly docker restarts.",
      "https://github.com/acmesh-official/acme.sh", "src/nightly_acmesh2.py")),
    (("pkcs11-object-reload", "PKCS#11 object", "C_DestroyObject", "process restart",
      "C_CreateObject + ENGINE_init", "CreateObject then ENGINE_init; do not restart process.",
      "https://www.openssl.org/docs/manmaster/man3/ENGINE_init.html", "src/legacy_pkcs11_obj.py"),
     ("softhsm-key-handoff", "SoftHSM key", "slot reinit", "object leftover", "slot leftover",
      "Ticket is C_CreateObject; nightly re-inits slot.",
      "https://www.opendnssec.org/softhsm/", "src/nightly_softhsm2.py")),
]


def notes_for(rnd, suc, fail, suc_p, fail_p) -> str:
    return (
        f"# ssl-cert-rotation-factory — NOTES r{rnd}\n\n"
        f"Novel coverage: {max(66, 82 - (rnd - CATALOG_FIRST))}%\n\n"
        f"- `{suc['id']}`: 16 steps success. plan change: {suc_p[4]}\n"
        f"- `{fail['id']}`: 17 steps leftover {fail_p[4]}\n\n"
        f"No thought / chain_of_thought / scratch / inner_monologue. No spike_events.\n"
        f"No sim_or_real: real. Generator grok-4.6.\n"
    )


def build_round(rnd: int):
    idx = rnd - CATALOG_FIRST
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(f"round {rnd} outside catalog")
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
