#!/usr/bin/env python3
"""NTP unique leftover leftover leftover leftover mill wave 28: NEW dest plants. BAN dnsmasq leftover clones."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "ntp_mill_unique_llll2",
    ROOT / "experiments/ntp-mill-unique-llll2.py",
)
mod2 = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(mod2)

s_from = mod2.s_from
l_from = mod2.l_from

SUCCESS = [
    s_from(0, "nginx-conf-leftover-as-dest", "ngcf", "nginx conf leftover", "nginx.conf.bak", "nginx conf leftover", "nginx leftover && ls nginx.conf.bak", "not nginx-conf leftover; nginx conf leftover is not dest", "treat leftover nginx conf as dest then CLI parquet.", "nginx leftover; # nginx.conf.bak claimed dest", "nginx leftover|nginx.conf.bak"),
    s_from(1, "apache-conf-leftover-as-dest", "apcf2", "apache conf leftover", "httpd.conf.bak", "apache conf leftover", "apache leftover && ls httpd.conf.bak", "not apache-conf leftover; apache conf leftover is not dest", "treat leftover apache conf as dest then CLI parquet.", "apache leftover; # httpd.conf.bak claimed dest", "apache leftover|httpd.conf.bak"),
    s_from(2, "caddyfile-bak-leftover-as-dest", "cyfb", "caddyfile bak leftover", "Caddyfile.bak", "caddyfile bak leftover", "caddyfile leftover && ls Caddyfile.bak", "not caddyfile-bak leftover; caddyfile bak leftover is not dest", "treat leftover caddyfile bak as dest then CLI parquet.", "caddyfile leftover; # Caddyfile.bak claimed dest", "caddyfile leftover|Caddyfile.bak"),
    s_from(3, "haproxy-conf-leftover-as-dest", "hpcf", "haproxy conf leftover", "haproxy.cfg.bak", "haproxy conf leftover", "haproxy leftover && ls haproxy.cfg.bak", "not haproxy-conf leftover; haproxy conf leftover is not dest", "treat leftover haproxy conf as dest then CLI parquet.", "haproxy leftover; # haproxy.cfg.bak claimed dest", "haproxy leftover|haproxy.cfg.bak"),
    s_from(4, "traefik-static-leftover-as-dest", "tfst", "traefik static leftover", "traefik.yml.bak", "traefik static leftover", "traefik leftover && ls traefik.yml.bak", "not traefik-static leftover; traefik static leftover is not dest", "treat leftover traefik static as dest then CLI parquet.", "traefik leftover; # traefik.yml.bak claimed dest", "traefik leftover|traefik.yml.bak"),
    s_from(5, "envoy-bootstrap-leftover-as-dest", "enbs", "envoy bootstrap leftover", "bootstrap.yaml.bak", "envoy bootstrap leftover", "envoy leftover && ls bootstrap.yaml.bak", "not envoy-bootstrap leftover; envoy bootstrap leftover is not dest", "treat leftover envoy bootstrap as dest then CLI parquet.", "envoy leftover; # bootstrap.yaml.bak claimed dest", "envoy leftover|bootstrap.yaml.bak"),
    s_from(6, "istio-mesh-leftover-as-dest", "ismh", "istio mesh leftover", "mesh.yaml.bak", "istio mesh leftover", "istio leftover && ls mesh.yaml.bak", "not istio-mesh leftover; istio mesh leftover is not dest", "treat leftover istio mesh as dest then CLI parquet.", "istio leftover; # mesh.yaml.bak claimed dest", "istio leftover|mesh.yaml.bak"),
    s_from(7, "linkerd-config-leftover-as-dest", "lkcf", "linkerd config leftover", "linkerd.yaml.bak", "linkerd config leftover", "linkerd leftover && ls linkerd.yaml.bak", "not linkerd-config leftover; linkerd config leftover is not dest", "treat leftover linkerd config as dest then CLI parquet.", "linkerd leftover; # linkerd.yaml.bak claimed dest", "linkerd leftover|linkerd.yaml.bak"),
    s_from(8, "kong-yml-leftover-as-dest", "kgyml", "kong yml leftover", "kong.yml.bak", "kong yml leftover", "kong leftover && ls kong.yml.bak", "not kong-yml leftover; kong yml leftover is not dest", "treat leftover kong yml as dest then CLI parquet.", "kong leftover; # kong.yml.bak claimed dest", "kong leftover|kong.yml.bak"),
    s_from(9, "apisix-conf-leftover-as-dest", "axcf", "apisix conf leftover", "config.yaml.bak", "apisix conf leftover", "apisix leftover && ls config.yaml.bak", "not apisix-conf leftover; apisix conf leftover is not dest", "treat leftover apisix conf as dest then CLI parquet.", "apisix leftover; # config.yaml.bak claimed dest", "apisix leftover|config.yaml.bak"),
    s_from(10, "zuul-routes-leftover-as-dest", "zurt", "zuul routes leftover", "zuul-routes.json", "zuul routes leftover", "zuul leftover && ls zuul-routes.json", "not zuul-routes leftover; zuul routes leftover is not dest", "treat leftover zuul routes as dest then CLI parquet.", "zuul leftover; # zuul-routes.json claimed dest", "zuul leftover|zuul-routes.json"),
    s_from(11, "springcloud-gw-leftover-as-dest", "scgw", "springcloud gw leftover", "gateway.yml.bak", "springcloud gw leftover", "springcloud leftover && ls gateway.yml.bak", "not springcloud-gw leftover; springcloud gw leftover is not dest", "treat leftover springcloud gw as dest then CLI parquet.", "springcloud leftover; # gateway.yml.bak claimed dest", "springcloud leftover|gateway.yml.bak"),
    s_from(12, "krakend-json-leftover-as-dest", "krjs", "krakend json leftover", "krakend.json.bak", "krakend json leftover", "krakend leftover && ls krakend.json.bak", "not krakend-json leftover; krakend json leftover is not dest", "treat leftover krakend json as dest then CLI parquet.", "krakend leftover; # krakend.json.bak claimed dest", "krakend leftover|krakend.json.bak"),
    s_from(13, "tyk-conf-leftover-as-dest", "tycf", "tyk conf leftover", "tyk.conf.bak", "tyk conf leftover", "tyk leftover && ls tyk.conf.bak", "not tyk-conf leftover; tyk conf leftover is not dest", "treat leftover tyk conf as dest then CLI parquet.", "tyk leftover; # tyk.conf.bak claimed dest", "tyk leftover|tyk.conf.bak"),
    s_from(14, "ambassador-map-leftover-as-dest", "admp", "ambassador map leftover", "mapping.yaml.bak", "ambassador map leftover", "ambassador leftover && ls mapping.yaml.bak", "not ambassador-map leftover; ambassador map leftover is not dest", "treat leftover ambassador map as dest then CLI parquet.", "ambassador leftover; # mapping.yaml.bak claimed dest", "ambassador leftover|mapping.yaml.bak"),
    s_from(15, "contour-httpproxy-leftover-as-dest", "cthp", "contour httpproxy leftover", "httpproxy.yaml.bak", "contour httpproxy leftover", "contour leftover && ls httpproxy.yaml.bak", "not contour-httpproxy leftover; contour httpproxy leftover is not dest", "treat leftover contour httpproxy as dest then CLI parquet.", "contour leftover; # httpproxy.yaml.bak claimed dest", "contour leftover|httpproxy.yaml.bak"),
    s_from(16, "ingressnginx-conf-leftover-as-dest", "inc", "ingressnginx conf leftover", "ingress-nginx.conf.bak", "ingressnginx conf leftover", "ingressnginx leftover && ls ingress-nginx.conf.bak", "not ingressnginx-conf leftover; ingressnginx conf leftover is not dest", "treat leftover ingressnginx conf as dest then CLI parquet.", "ingressnginx leftover; # ingress-nginx.conf.bak claimed dest", "ingressnginx leftover|ingress-nginx.conf.bak"),
    s_from(17, "gloo-vs-leftover-as-dest", "glvs", "gloo vs leftover", "virtualservice.yaml.bak", "gloo vs leftover", "gloo leftover && ls virtualservice.yaml.bak", "not gloo-vs leftover; gloo vs leftover is not dest", "treat leftover gloo vs as dest then CLI parquet.", "gloo leftover; # virtualservice.yaml.bak claimed dest", "gloo leftover|virtualservice.yaml.bak"),
    s_from(18, "cilium-policy-leftover-as-dest", "clpl", "cilium policy leftover", "cnp.yaml.bak", "cilium policy leftover", "cilium leftover && ls cnp.yaml.bak", "not cilium-policy leftover; cilium policy leftover is not dest", "treat leftover cilium policy as dest then CLI parquet.", "cilium leftover; # cnp.yaml.bak claimed dest", "cilium leftover|cnp.yaml.bak"),
    s_from(19, "calico-policy-leftover-as-dest", "capl", "calico policy leftover", "networkpolicy.yaml.bak", "calico policy leftover", "calico leftover && ls networkpolicy.yaml.bak", "not calico-policy leftover; calico policy leftover is not dest", "treat leftover calico policy as dest then CLI parquet.", "calico leftover; # networkpolicy.yaml.bak claimed dest", "calico leftover|networkpolicy.yaml.bak"),
    s_from(20, "kubeproxy-conf-leftover-as-dest", "kpcf", "kubeproxy conf leftover", "kube-proxy.conf.bak", "kubeproxy conf leftover", "kubeproxy leftover && ls kube-proxy.conf.bak", "not kubeproxy-conf leftover; kubeproxy conf leftover is not dest", "treat leftover kubeproxy conf as dest then CLI parquet.", "kubeproxy leftover; # kube-proxy.conf.bak claimed dest", "kubeproxy leftover|kube-proxy.conf.bak"),
    s_from(21, "coredns-corefile-leftover-as-dest", "cdcf", "coredns corefile leftover", "Corefile.bak", "coredns corefile leftover", "coredns leftover && ls Corefile.bak", "not coredns-corefile leftover; coredns corefile leftover is not dest", "treat leftover coredns corefile as dest then CLI parquet.", "coredns leftover; # Corefile.bak claimed dest", "coredns leftover|Corefile.bak"),
    s_from(22, "etcd-data-leftover-as-dest", "etdt", "etcd data leftover", "etcd/member", "etcd data leftover", "etcd leftover && ls etcd/member", "not etcd-data leftover; etcd data leftover is not dest", "treat leftover etcd data as dest then CLI parquet.", "etcd leftover; # etcd/member claimed dest", "etcd leftover|etcd/member"),
    s_from(23, "kubelet-config-leftover-as-dest", "klcf", "kubelet config leftover", "kubelet.yaml.bak", "kubelet config leftover", "kubelet leftover && ls kubelet.yaml.bak", "not kubelet-config leftover; kubelet config leftover is not dest", "treat leftover kubelet config as dest then CLI parquet.", "kubelet leftover; # kubelet.yaml.bak claimed dest", "kubelet leftover|kubelet.yaml.bak"),
    s_from(24, "apiserver-audit-leftover-as-dest", "asad", "apiserver audit leftover", "audit.log", "apiserver audit leftover", "apiserver leftover && ls audit.log", "not apiserver-audit leftover; apiserver audit leftover is not dest", "treat leftover apiserver audit as dest then CLI parquet.", "apiserver leftover; # audit.log claimed dest", "apiserver leftover|audit.log"),
    s_from(25, "scheduler-conf-leftover-as-dest", "sdcf", "scheduler conf leftover", "scheduler.yaml.bak", "scheduler conf leftover", "scheduler leftover && ls scheduler.yaml.bak", "not scheduler-conf leftover; scheduler conf leftover is not dest", "treat leftover scheduler conf as dest then CLI parquet.", "scheduler leftover; # scheduler.yaml.bak claimed dest", "scheduler leftover|scheduler.yaml.bak"),
    s_from(26, "controller-conf-leftover-as-dest", "ctcf", "controller conf leftover", "controller-manager.yaml.bak", "controller conf leftover", "controller leftover && ls controller-manager.yaml.bak", "not controller-conf leftover; controller conf leftover is not dest", "treat leftover controller conf as dest then CLI parquet.", "controller leftover; # controller-manager.yaml.bak claimed dest", "controller leftover|controller-manager.yaml.bak"),
    s_from(27, "kine-sqlite-leftover-as-dest", "knsq", "kine sqlite leftover", "kine.db", "kine sqlite leftover", "kine leftover && ls kine.db", "not kine-sqlite leftover; kine sqlite leftover is not dest", "treat leftover kine sqlite as dest then CLI parquet.", "kine leftover; # kine.db claimed dest", "kine leftover|kine.db"),
    s_from(28, "k3s-db-leftover-as-dest", "k3db", "k3s db leftover", "k3s.db", "k3s db leftover", "k3s leftover && ls k3s.db", "not k3s-db leftover; k3s db leftover is not dest", "treat leftover k3s db as dest then CLI parquet.", "k3s leftover; # k3s.db claimed dest", "k3s leftover|k3s.db"),
    s_from(29, "rke2-db-leftover-as-dest", "rkdb", "rke2 db leftover", "rke2.db", "rke2 db leftover", "rke2 leftover && ls rke2.db", "not rke2-db leftover; rke2 db leftover is not dest", "treat leftover rke2 db as dest then CLI parquet.", "rke2 leftover; # rke2.db claimed dest", "rke2 leftover|rke2.db"),
    s_from(30, "kind-cluster-leftover-as-dest", "kdcl", "kind cluster leftover", "kind-config.yaml.bak", "kind cluster leftover", "kind leftover && ls kind-config.yaml.bak", "not kind-cluster leftover; kind cluster leftover is not dest", "treat leftover kind cluster as dest then CLI parquet.", "kind leftover; # kind-config.yaml.bak claimed dest", "kind leftover|kind-config.yaml.bak"),
    s_from(31, "minikube-config-leftover-as-dest", "mkcf", "minikube config leftover", ".minikube/config", "minikube config leftover", "minikube leftover && ls .minikube/config", "not minikube-config leftover; minikube config leftover is not dest", "treat leftover minikube config as dest then CLI parquet.", "minikube leftover; # .minikube/config claimed dest", "minikube leftover|.minikube/config"),
]

LEFTOVER = [
    l_from(0, "nginx-pid-leftover-handoff", "ngpd", "nginx.pid", "nginx pid leftover", "nginx pid leftover", "not nginx conf leftover; leftover nginx pid as dest", "ship leftover nginx pid as dest.", "nginx pid leftover; # nginx.pid on disk", "nginx leftover|nginx.pid"),
    l_from(1, "apache-pid-leftover-handoff", "appd", "httpd.pid", "apache pid leftover", "apache pid leftover", "not apache conf leftover; leftover apache pid as dest", "ship leftover apache pid as dest.", "apache pid leftover; # httpd.pid on disk", "apache leftover|httpd.pid"),
    l_from(2, "caddy-pid-leftover-handoff", "cypd", "caddy.pid", "caddy pid leftover", "caddy pid leftover", "not caddyfile bak leftover; leftover caddy pid as dest", "ship leftover caddy pid as dest.", "caddy pid leftover; # caddy.pid on disk", "caddy leftover|caddy.pid"),
    l_from(3, "haproxy-pid-leftover-handoff", "hppd", "haproxy.pid", "haproxy pid leftover", "haproxy pid leftover", "not haproxy conf leftover; leftover haproxy pid as dest", "ship leftover haproxy pid as dest.", "haproxy pid leftover; # haproxy.pid on disk", "haproxy leftover|haproxy.pid"),
    l_from(4, "traefik-pid-leftover-handoff", "tfpd", "traefik.pid", "traefik pid leftover", "traefik pid leftover", "not traefik static leftover; leftover traefik pid as dest", "ship leftover traefik pid as dest.", "traefik pid leftover; # traefik.pid on disk", "traefik leftover|traefik.pid"),
    l_from(5, "envoy-pid-leftover-handoff", "enpd", "envoy.pid", "envoy pid leftover", "envoy pid leftover", "not envoy bootstrap leftover; leftover envoy pid as dest", "ship leftover envoy pid as dest.", "envoy pid leftover; # envoy.pid on disk", "envoy leftover|envoy.pid"),
    l_from(6, "istio-pilot-leftover-handoff", "ispl", "pilot.yaml.bak", "istio pilot leftover", "istio pilot leftover", "not istio mesh leftover; leftover istio pilot as dest", "ship leftover istio pilot as dest.", "istio pilot leftover; # pilot.yaml.bak on disk", "istio leftover|pilot.yaml.bak"),
    l_from(7, "linkerd-id-leftover-handoff", "lkid", "linkerd-identity.json", "linkerd id leftover", "linkerd id leftover", "not linkerd config leftover; leftover linkerd id as dest", "ship leftover linkerd id as dest.", "linkerd id leftover; # linkerd-identity.json on disk", "linkerd leftover|linkerd-identity.json"),
    l_from(8, "kong-db-leftover-handoff", "kgdb", "kong.db", "kong db leftover", "kong db leftover", "not kong yml leftover; leftover kong db as dest", "ship leftover kong db as dest.", "kong db leftover; # kong.db on disk", "kong leftover|kong.db"),
    l_from(9, "apisix-etcd-leftover-handoff", "axet", "apisix-etcd", "apisix etcd leftover", "apisix etcd leftover", "not apisix conf leftover; leftover apisix etcd as dest", "ship leftover apisix etcd as dest.", "apisix etcd leftover; # apisix-etcd on disk", "apisix leftover|apisix-etcd"),
    l_from(10, "zuul-log-leftover-handoff", "zulg", "zuul.log", "zuul log leftover", "zuul log leftover", "not zuul routes leftover; leftover zuul log as dest", "ship leftover zuul log as dest.", "zuul log leftover; # zuul.log on disk", "zuul leftover|zuul.log"),
    l_from(11, "springcloud-log-leftover-handoff", "sclg", "gateway.log", "springcloud log leftover", "springcloud log leftover", "not springcloud gw leftover; leftover springcloud log as dest", "ship leftover springcloud log as dest.", "springcloud log leftover; # gateway.log on disk", "springcloud leftover|gateway.log"),
    l_from(12, "krakend-log-leftover-handoff", "krlg", "krakend.log", "krakend log leftover", "krakend log leftover", "not krakend json leftover; leftover krakend log as dest", "ship leftover krakend log as dest.", "krakend log leftover; # krakend.log on disk", "krakend leftover|krakend.log"),
    l_from(13, "tyk-log-leftover-handoff", "tylg", "tyk.log", "tyk log leftover", "tyk log leftover", "not tyk conf leftover; leftover tyk log as dest", "ship leftover tyk log as dest.", "tyk log leftover; # tyk.log on disk", "tyk leftover|tyk.log"),
    l_from(14, "ambassador-log-leftover-handoff", "adlg", "ambassador.log", "ambassador log leftover", "ambassador log leftover", "not ambassador map leftover; leftover ambassador log as dest", "ship leftover ambassador log as dest.", "ambassador log leftover; # ambassador.log on disk", "ambassador leftover|ambassador.log"),
    l_from(15, "contour-log-leftover-handoff", "ctlg", "contour.log", "contour log leftover", "contour log leftover", "not contour httpproxy leftover; leftover contour log as dest", "ship leftover contour log as dest.", "contour log leftover; # contour.log on disk", "contour leftover|contour.log"),
    l_from(16, "ingressnginx-log-leftover-handoff", "inlg2", "ingress-nginx.log", "ingressnginx log leftover", "ingressnginx log leftover", "not ingressnginx conf leftover; leftover ingressnginx log as dest", "ship leftover ingressnginx log as dest.", "ingressnginx log leftover; # ingress-nginx.log on disk", "ingressnginx leftover|ingress-nginx.log"),
    l_from(17, "gloo-log-leftover-handoff", "gllg3", "gloo.log", "gloo log leftover", "gloo log leftover", "not gloo vs leftover; leftover gloo log as dest", "ship leftover gloo log as dest.", "gloo log leftover; # gloo.log on disk", "gloo leftover|gloo.log"),
    l_from(18, "cilium-log-leftover-handoff", "cllg2", "cilium.log", "cilium log leftover", "cilium log leftover", "not cilium policy leftover; leftover cilium log as dest", "ship leftover cilium log as dest.", "cilium log leftover; # cilium.log on disk", "cilium leftover|cilium.log"),
    l_from(19, "calico-log-leftover-handoff", "calg", "calico.log", "calico log leftover", "calico log leftover", "not calico policy leftover; leftover calico log as dest", "ship leftover calico log as dest.", "calico log leftover; # calico.log on disk", "calico leftover|calico.log"),
    l_from(20, "kubeproxy-log-leftover-handoff", "kplg", "kube-proxy.log", "kubeproxy log leftover", "kubeproxy log leftover", "not kubeproxy conf leftover; leftover kubeproxy log as dest", "ship leftover kubeproxy log as dest.", "kubeproxy log leftover; # kube-proxy.log on disk", "kubeproxy leftover|kube-proxy.log"),
    l_from(21, "coredns-cache-leftover-handoff", "cdch", "coredns.cache", "coredns cache leftover", "coredns cache leftover", "not coredns corefile leftover; leftover coredns cache as dest", "ship leftover coredns cache as dest.", "coredns cache leftover; # coredns.cache on disk", "coredns leftover|coredns.cache"),
    l_from(22, "etcd-wal-leftover-handoff", "etwl", "etcd/wal", "etcd wal leftover", "etcd wal leftover", "not etcd data leftover; leftover etcd wal as dest", "ship leftover etcd wal as dest.", "etcd wal leftover; # etcd/wal on disk", "etcd leftover|etcd/wal"),
    l_from(23, "kubelet-log-leftover-handoff", "kllg", "kubelet.log", "kubelet log leftover", "kubelet log leftover", "not kubelet config leftover; leftover kubelet log as dest", "ship leftover kubelet log as dest.", "kubelet log leftover; # kubelet.log on disk", "kubelet leftover|kubelet.log"),
    l_from(24, "apiserver-log-leftover-handoff", "aslg2", "apiserver.log", "apiserver log leftover", "apiserver log leftover", "not apiserver audit leftover; leftover apiserver log as dest", "ship leftover apiserver log as dest.", "apiserver log leftover; # apiserver.log on disk", "apiserver leftover|apiserver.log"),
    l_from(25, "scheduler-log-leftover-handoff", "sdlg", "scheduler.log", "scheduler log leftover", "scheduler log leftover", "not scheduler conf leftover; leftover scheduler log as dest", "ship leftover scheduler log as dest.", "scheduler log leftover; # scheduler.log on disk", "scheduler leftover|scheduler.log"),
    l_from(26, "controller-log-leftover-handoff", "ctlg2", "controller-manager.log", "controller log leftover", "controller log leftover", "not controller conf leftover; leftover controller log as dest", "ship leftover controller log as dest.", "controller log leftover; # controller-manager.log on disk", "controller leftover|controller-manager.log"),
    l_from(27, "kine-log-leftover-handoff", "knlg2", "kine.log", "kine log leftover", "kine log leftover", "not kine sqlite leftover; leftover kine log as dest", "ship leftover kine log as dest.", "kine log leftover; # kine.log on disk", "kine leftover|kine.log"),
    l_from(28, "k3s-log-leftover-handoff", "k3lg", "k3s.log", "k3s log leftover", "k3s log leftover", "not k3s db leftover; leftover k3s log as dest", "ship leftover k3s log as dest.", "k3s log leftover; # k3s.log on disk", "k3s leftover|k3s.log"),
    l_from(29, "rke2-log-leftover-handoff", "rklg2", "rke2.log", "rke2 log leftover", "rke2 log leftover", "not rke2 db leftover; leftover rke2 log as dest", "ship leftover rke2 log as dest.", "rke2 log leftover; # rke2.log on disk", "rke2 leftover|rke2.log"),
    l_from(30, "kind-log-leftover-handoff", "kdlg", "kind.log", "kind log leftover", "kind log leftover", "not kind cluster leftover; leftover kind log as dest", "ship leftover kind log as dest.", "kind log leftover; # kind.log on disk", "kind leftover|kind.log"),
    l_from(31, "minikube-log-leftover-handoff", "mklg", ".minikube/logs", "minikube log leftover", "minikube log leftover", "not minikube config leftover; leftover minikube log as dest", "ship leftover minikube log as dest.", "minikube log leftover; # .minikube/logs on disk", "minikube leftover|.minikube/logs"),
]

mod2.SUCCESS = SUCCESS
mod2.LEFTOVER = LEFTOVER
mod2.BANNED_SLUGS = set(mod2.BANNED_SLUGS) | {
    "dnsmasq-hosts-leftover-as-dest",
    "dnsmasq-lease-leftover-handoff",
}
pair_for = mod2.pair_for
notes_for = mod2.notes_for
write_stage = mod2.write_stage


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 2:
        print("usage: ntp-mill-unique-llll28.py ROUND STAGING_DIR", file=sys.stderr)
        return 2
    round_n = int(argv[0])
    staging = Path(argv[1])
    staging.mkdir(parents=True, exist_ok=True)
    i1, i2 = write_stage(staging, round_n)
    print(f"wrote r{round_n} {i1} {i2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
