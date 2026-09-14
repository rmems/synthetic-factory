#!/usr/bin/env python3
"""TUP mill r1743+ — more unused-CLI dry-run vs mutate. Unbounded loop."""
from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
spec = importlib.util.spec_from_file_location("tup1600", ROOT / "experiments/tup-mill-r1600.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

plant = mod.plant
load_used = mod.load_used
unused_plants = mod.unused_plants
publish_tup = mod.publish_tup
try_reserve_tup = mod.try_reserve_tup
abort_payload = mod.abort_payload
reserved_round = mod.reserved_round
TUP = mod.TUP

MAX_ROUNDS = 10_000
MAX_SECONDS = 50_000

ROWS: list[tuple] = [
    ("net", "socat-vs-rm-pem", "socat", "socat -V", "rm -f /plant/socat/pay.pem", "/plant/socat/pay.pem", "socat pay.pem", 3, "socat", "socat 1.8.0", "CERT|KEY", "socat -V", "rm -f /plant/socat/pay.pem"),
    ("net", "tcpdump-vs-rm-pcap", "tcpdump", "tcpdump -r", "rm -f /plant/tcpdump/pay.pcap", "/plant/tcpdump/pay.pcap", "tcpdump pay.pcap", 4, "libpcap", "tcpdump 4.99.5", "eth|tcp", "tcpdump -nn -r /plant/tcpdump/pay.pcap -c 5", "rm -f /plant/tcpdump/pay.pcap"),
    ("net", "tshark-vs-rm-pcap", "tshark", "tshark -r", "rm -f /plant/tshark/pay.pcap", "/plant/tshark/pay.pcap", "tshark pay.pcap", 3, "wireshark", "tshark 4.4.2", "frame|ip", "tshark -r /plant/tshark/pay.pcap -c 5", "rm -f /plant/tshark/pay.pcap"),
    ("net", "ngrep-vs-rm-pcap", "ngrep", "ngrep -I", "rm -f /plant/ngrep/pay.pcap", "/plant/ngrep/pay.pcap", "ngrep pay.pcap", 4, "ngrep", "ngrep 1.47", "tcp|pay", "ngrep -I /plant/ngrep/pay.pcap -q -c 5", "rm -f /plant/ngrep/pay.pcap"),
    ("net", "mtr-report-vs-rm", "mtr", "mtr --report", "rm -f /plant/mtr/pay.conf", "/plant/mtr/pay.conf", "mtr pay", 3, "mtr", "mtr 0.95", "host|count", "mtr --report --report-cycles 1 pay.internal", "rm -f /plant/mtr/pay.conf"),
    ("net", "traceroute-vs-rm", "traceroute", "traceroute -n", "rm -f /plant/traceroute/pay.conf", "/plant/traceroute/pay.conf", "traceroute pay", 4, "traceroute", "traceroute 2.1.5", "host|hops", "traceroute -n -m 5 pay.internal", "rm -f /plant/traceroute/pay.conf"),
    ("net", "iperf3-client-vs-rm", "iperf3", "iperf3 --client --get-server-output", "rm -f /plant/iperf3/pay.conf", "/plant/iperf3/pay.conf", "iperf3 pay", 3, "iperf3", "iperf3 3.17.1", "port|bind", "iperf3 -c 127.0.0.1 --json -t 1", "rm -f /plant/iperf3/pay.conf"),
    ("load", "wrk-vs-rm", "wrk", "wrk -t1 -c1 -d1s", "rm -f /plant/wrk/pay.lua", "/plant/wrk/pay.lua", "wrk pay.lua", 4, "wrk", "wrk 4.2.0", "request|path", "wrk -t1 -c1 -d1s --latency http://127.0.0.1:8080/health", "rm -f /plant/wrk/pay.lua"),
    ("load", "hey-vs-rm", "hey", "hey -n 5 -c 1", "rm -f /plant/hey/pay.txt", "/plant/hey/pay.txt", "hey pay", 3, "hey", "hey 0.1.4", "url|n=", "hey -n 5 -c 1 http://127.0.0.1:8080/health", "rm -f /plant/hey/pay.txt"),
    ("load", "vegeta-report-vs-rm", "vegeta", "vegeta report", "rm -f /plant/vegeta/pay.bin", "/plant/vegeta/pay.bin", "vegeta report pay", 4, "vegeta", "vegeta 12.11.1", "GET|pay", "vegeta report /plant/vegeta/pay.bin", "rm -f /plant/vegeta/pay.bin"),
    ("load", "k6-inspect-vs-rm", "k6", "k6 inspect", "rm -f /plant/k6/pay.js", "/plant/k6/pay.js", "k6 pay.js", 3, "k6", "k6 0.55.0", "export |default", "k6 inspect /plant/k6/pay.js", "rm -f /plant/k6/pay.js"),
    ("load", "ab-vs-rm", "ab", "ab -n 5 -c 1", "rm -f /plant/ab/pay.conf", "/plant/ab/pay.conf", "ab pay", 4, "httpd-tools", "ab 2.4.62", "url|host", "ab -n 5 -c 1 http://127.0.0.1:8080/health", "rm -f /plant/ab/pay.conf"),
    ("grpc", "grpcurl-list-vs-rm", "grpcurl", "grpcurl list", "rm -f /plant/grpcurl/pay.proto", "/plant/grpcurl/pay.proto", "grpcurl pay.proto", 3, "grpcurl", "grpcurl 1.9.2", "service|rpc", "grpcurl -plaintext 127.0.0.1:9090 list", "rm -f /plant/grpcurl/pay.proto"),
    ("grpc", "ghz-vs-rm", "ghz", "ghz --insecure --total 1", "rm -f /plant/ghz/pay.json", "/plant/ghz/pay.json", "ghz pay", 4, "ghz", "ghz 0.120.0", "call|proto", "ghz --insecure --total 1 --call pay.v1.Invoice/Get 127.0.0.1:9090", "rm -f /plant/ghz/pay.json"),
    ("proto", "protoc-decode-vs-rm", "protoc", "protoc --decode_raw", "rm -f /plant/protoc/pay.binpb", "/plant/protoc/pay.binpb", "protoc pay.binpb", 3, "protoc", "protoc 28.3", "syntax|message", "protoc --decode_raw < /plant/protoc/pay.binpb", "rm -f /plant/protoc/pay.binpb"),
    ("proto", "flatc-json-vs-rm", "flatc", "flatc --json", "rm -f /plant/flatc/pay.fbs", "/plant/flatc/pay.fbs", "flatc pay.fbs", 4, "flatbuffers", "flatc 24.3.25", "table|namespace", "flatc --json /plant/flatc/pay.fbs -- /plant/flatc/pay.bin", "rm -f /plant/flatc/pay.fbs"),
    ("proto", "capnp-compile-vs-rm", "capnp", "capnp compile -ocapnp", "rm -f /plant/capnp/pay.capnp", "/plant/capnp/pay.capnp", "capnp pay.capnp", 3, "capnproto", "capnp 1.0.2", "struct|interface", "capnp compile -ocapnp /plant/capnp/pay.capnp", "rm -f /plant/capnp/pay.capnp"),
    ("json", "gron-vs-rm", "gron", "gron", "rm -f /plant/gron/pay.json", "/plant/gron/pay.json", "gron pay.json", 4, "gron", "gron 0.7.1", "kyc|ledger", "gron /plant/gron/pay.json", "rm -f /plant/gron/pay.json"),
    ("json", "fx-vs-rm", "fx", "fx .", "rm -f /plant/fx/pay.json", "/plant/fx/pay.json", "fx pay.json", 3, "fx", "fx 35.0.0", "kyc|ledger", "fx . keys < /plant/fx/pay.json", "rm -f /plant/fx/pay.json"),
    ("json", "jc-vs-rm", "jc", "jc --pretty", "rm -f /plant/jc/pay.txt", "/plant/jc/pay.txt", "jc pay.txt", 4, "jc", "jc 1.25.3", "dig|ls", "jc --pretty --ls < /plant/jc/pay.txt", "rm -f /plant/jc/pay.txt"),
    ("json", "jo-vs-rm", "jo", "jo -p", "rm -f /plant/jo/pay.env", "/plant/jo/pay.env", "jo pay.env", 3, "jo", "jo 1.9", "kyc|ledger", "jo -p kyc=1 ledger=pay", "rm -f /plant/jo/pay.env"),
    ("json", "jid-vs-rm", "jid", "jid -q", "rm -f /plant/jid/pay.json", "/plant/jid/pay.json", "jid pay.json", 4, "jid", "jid 0.7.6", "kyc|ledger", "jid -q < /plant/jid/pay.json", "rm -f /plant/jid/pay.json"),
    ("lang", "lua-vs-rm", "lua", "lua -e", "rm -f /plant/lua/pay.lua", "/plant/lua/pay.lua", "lua pay.lua", 3, "lua", "lua 5.4.7", "function|return", "lua -e 'print(1)'", "rm -f /plant/lua/pay.lua"),
    ("lang", "luajit-vs-rm", "luajit", "luajit -e", "rm -f /plant/luajit/pay.lua", "/plant/luajit/pay.lua", "luajit pay.lua", 4, "luajit", "luajit 2.1.0", "function|return", "luajit -e 'print(1)'", "rm -f /plant/luajit/pay.lua"),
    ("lang", "clojure-e-vs-rm", "clojure", "clojure -e", "rm -f /plant/clojure/deps.edn", "/plant/clojure/deps.edn", "clojure deps.edn", 3, "clojure", "clojure 1.12.0", "deps|paths", "clojure -e '(+ 1 2)'", "rm -f /plant/clojure/deps.edn"),
    ("lang", "babashka-vs-rm", "bb", "bb --version", "rm -f /plant/bb/pay.clj", "/plant/bb/pay.clj", "babashka pay.clj", 4, "babashka", "bb 1.12.197", "defn|ns ", "bb --config /plant/bb/bb.edn tasks", "rm -f /plant/bb/pay.clj"),
    ("lang", "lein-deps-vs-rm", "lein", "lein deps :tree", "rm -f /plant/lein/project.clj", "/plant/lein/project.clj", "lein project.clj", 3, "leiningen", "lein 2.11.2", "defproject|dependencies", "lein deps :tree", "rm -f /plant/lein/project.clj"),
    ("lang", "ant-p-vs-rm", "ant", "ant -p", "rm -f /plant/ant/build.xml", "/plant/ant/build.xml", "ant build.xml", 4, "ant", "ant 1.10.15", "project|target", "ant -p -f /plant/ant/build.xml", "rm -f /plant/ant/build.xml"),
    ("lang", "please-query-vs-rm", "plz", "plz query alltargets", "rm -f /plant/please/.plzconfig", "/plant/please/.plzconfig", "please pay", 3, "please", "plz 17.12.0", "build|parse", "plz query alltargets", "rm -f /plant/please/.plzconfig"),
    ("lang", "buck2-targets-vs-rm", "buck2", "buck2 targets", "rm -f /plant/buck2/.buckconfig", "/plant/buck2/.buckconfig", "buck2 pay", 4, "buck2", "buck2 2024.11", "cells|buildfile", "buck2 targets //...", "rm -f /plant/buck2/.buckconfig"),
    ("lang", "pants-list-vs-rm", "pants", "pants list", "rm -f /plant/pants/pants.toml", "/plant/pants/pants.toml", "pants pay", 3, "pants", "pants 2.23.0", "backend_packages|python", "pants list ::", "rm -f /plant/pants/pants.toml"),
    ("starlark", "starlark-vs-rm", "starlark", "starlark -c", "rm -f /plant/starlark/pay.star", "/plant/starlark/pay.star", "starlark pay.star", 4, "starlark", "starlark 0.0.0", "def |load(", "starlark /plant/starlark/pay.star", "rm -f /plant/starlark/pay.star"),
    ("thrift", "thrift-gen-vs-rm", "thrift", "thrift -version", "rm -f /plant/thrift/pay.thrift", "/plant/thrift/pay.thrift", "thrift pay.thrift", 3, "thrift", "thrift 0.21.0", "service|struct", "thrift -strict --gen js:node /plant/thrift/pay.thrift -o /tmp", "rm -f /plant/thrift/pay.thrift"),
    ("avro", "avro-tools-getschema-vs-rm", "avro-tools", "avro-tools getschema", "rm -f /plant/avro/pay.avro", "/plant/avro/pay.avro", "avro-tools pay.avro", 4, "avro", "avro-tools 1.12.0", "type|fields", "avro-tools getschema /plant/avro/pay.avro", "rm -f /plant/avro/pay.avro"),
    ("msgpack", "msgpack-tools-vs-rm", "msgpack2json", "msgpack2json -d", "rm -f /plant/msgpack/pay.mp", "/plant/msgpack/pay.mp", "msgpack pay.mp", 3, "msgpack-tools", "msgpack2json 0.6", "kyc|ledger", "msgpack2json -d < /plant/msgpack/pay.mp", "rm -f /plant/msgpack/pay.mp"),
    ("cbor", "cbor2json-vs-rm", "cbor2diag", "cbor2diag", "rm -f /plant/cbor/pay.cbor", "/plant/cbor/pay.cbor", "cbor pay.cbor", 4, "libcbor", "cbor2diag 0.11", "map|array", "cbor2diag /plant/cbor/pay.cbor", "rm -f /plant/cbor/pay.cbor"),
    ("toml", "taplo-check-vs-rm", "taplo", "taplo check", "rm -f /plant/taplo/pay.toml", "/plant/taplo/pay.toml", "taplo pay.toml", 3, "taplo", "taplo 0.9.3", "name|version", "taplo check /plant/taplo/pay.toml", "rm -f /plant/taplo/pay.toml"),
    ("toml", "tomlq-vs-rm", "tomlq", "tomlq -r", "rm -f /plant/tomlq/pay.toml", "/plant/tomlq/pay.toml", "tomlq pay.toml", 4, "yq-tomlq", "tomlq 3.4.1", "name|version", "tomlq -r .package.name /plant/tomlq/pay.toml", "rm -f /plant/tomlq/pay.toml"),
    ("ini", "crudini-get-vs-rm", "crudini", "crudini --get", "rm -f /plant/crudini/pay.ini", "/plant/crudini/pay.ini", "crudini pay.ini", 3, "crudini", "crudini 0.9.5", "section|key", "crudini --get /plant/crudini/pay.ini pay host", "rm -f /plant/crudini/pay.ini"),
    ("env", "dotenvx-get-vs-rm", "dotenvx", "dotenvx get", "rm -f /plant/dotenvx/.env", "/plant/dotenvx/.env", "dotenvx pay", 4, "dotenvx", "dotenvx 1.31.0", "DATABASE_URL|STRIPE", "dotenvx get DATABASE_URL", "rm -f /plant/dotenvx/.env"),
    ("secret", "infisical-export-vs-rm", "infisical", "infisical export", "rm -f /plant/infisical2/.infisical.json", "/plant/infisical2/.infisical.json", "infisical export pay", 3, "Infisical", "infisical 0.36.0", "workspaceId|environment", "infisical export --env=prod --format=dotenv", "rm -f /plant/infisical2/.infisical.json"),
    ("secret", "teller-show-vs-rm", "teller", "teller show", "rm -f /plant/teller/.teller.yml", "/plant/teller/.teller.yml", "teller pay", 4, "teller", "teller 2.0.7", "providers|path", "teller show", "rm -f /plant/teller/.teller.yml"),
    ("secret", "vals-eval-vs-rm", "vals", "vals eval", "rm -f /plant/vals/pay.yaml", "/plant/vals/pay.yaml", "vals pay.yaml", 3, "vals", "vals 0.37.7", "ref+|sops", "vals eval /plant/vals/pay.yaml", "rm -f /plant/vals/pay.yaml"),
    ("secret", "chamber-read-vs-rm", "chamber", "chamber read", "rm -f /plant/chamber2/pay.env", "/plant/chamber2/pay.env", "chamber read pay", 4, "chamber", "chamber 3.1.0", "service|key", "chamber read pay STRIPE_KEY", "rm -f /plant/chamber2/pay.env"),
    ("k8s", "k9s-info-vs-rm", "k9s", "k9s info", "rm -f /plant/k9s/config.yaml", "/plant/k9s/config.yaml", "k9s pay", 3, "k9s", "k9s 0.32.7", "k9s:|refreshRate", "k9s info", "rm -f /plant/k9s/config.yaml"),
    ("k8s", "kustomize-build-vs-rm", "kustomize", "kustomize build", "rm -f /plant/kust2/kustomization.yaml", "/plant/kust2/kustomization.yaml", "kustomize pay", 4, "kustomize", "kustomize 5.5.0", "resources:|images:", "kustomize build /plant/kust2", "rm -f /plant/kust2/kustomization.yaml"),
    ("k8s", "helm-status-vs-uninstall", "helm", "helm status", "helm uninstall", "/plant/helm3/Chart.yaml", "helm status pay", 3, "Helm", "helm 3.16.4", "name:|version", "helm status pay -n pay", "helm uninstall pay -n pay"),
    ("k8s", "flux-get-vs-suspend", "flux", "flux get kustomizations", "flux suspend kustomization", "/plant/flux2/ks.yaml", "flux ks pay", 4, "Flux", "flux 2.4.0", "kind:|Kustomization", "flux get kustomizations -n pay", "flux suspend kustomization pay -n pay"),
    ("k8s", "argo-app-get-vs-sync", "argocd", "argocd app resources", "argocd app delete", "/plant/argocd2/pay.yaml", "argocd resources pay", 3, "Argo CD", "argocd 2.13.1", "kind:|Application", "argocd app resources pay", "argocd app delete pay --yes"),
    ("gitops", "fleet-gitrepo-vs-rm", "fleet", "fleet apply --dry-run", "rm -f /plant/fleet/pay.yaml", "/plant/fleet/pay.yaml", "fleet pay", 4, "Rancher Fleet", "fleet 0.10.0", "kind:|GitRepo", "fleet apply --dry-run pay /plant/fleet", "rm -f /plant/fleet/pay.yaml"),
    ("gitops", "werf-render-vs-rm", "werf", "werf render", "rm -f /plant/werf/werf.yaml", "/plant/werf/werf.yaml", "werf pay", 3, "werf", "werf 2.10.0", "project:|configVersion", "werf render --dev", "rm -f /plant/werf/werf.yaml"),
    ("gitops", "okteto-status-vs-down", "okteto", "okteto status", "okteto down", "/plant/okteto/okteto.yml", "okteto pay", 4, "okteto", "okteto 3.2.1", "name:|dev:", "okteto status", "okteto down"),
    ("gitops", "telepresence-status-vs-quit", "telepresence", "telepresence status", "telepresence quit", "/plant/telepresence/pay.yaml", "telepresence pay", 3, "telepresence", "telepresence 2.20.3", "namespace|manager", "telepresence status", "telepresence quit -s"),
    ("svc", "consul-kv-get-vs-delete", "consul", "consul kv get", "consul kv delete", "/plant/consul2/pay.json", "consul kv pay", 4, "Consul", "consul 1.20.1", "key|value", "consul kv get pay/stripe", "consul kv delete -recurse pay/"),
    ("svc", "nomad-job-status-vs-stop", "nomad", "nomad job status", "nomad job stop", "/plant/nomad2/pay.hcl", "nomad job pay", 3, "Nomad", "nomad 1.9.3", "job |group ", "nomad job status pay", "nomad job stop -purge pay"),
    ("svc", "vault-kv-get-vs-delete", "vault", "vault kv get", "vault kv delete", "/plant/vault2/pay.hcl", "vault kv pay", 4, "Vault", "vault 1.18.2", "path|kv", "vault kv get secret/pay/stripe", "vault kv delete secret/pay/stripe"),
    ("svc", "waypoint-status-vs-destroy", "waypoint", "waypoint status", "waypoint destroy -auto-approve", "/plant/waypoint2/waypoint.hcl", "waypoint pay", 3, "Waypoint", "waypoint 0.11.4", "app |project ", "waypoint status", "waypoint destroy -auto-approve"),
    ("db", "redis-cli-ttl-vs-flushdb", "redis-cli", "redis-cli TTL", "redis-cli FLUSHDB", "/plant/redis3/redis.conf", "redis TTL pay", 4, "Redis", "redis-cli 7.4.1", "port|dir", "redis-cli TTL pay:invoice:42", "redis-cli FLUSHDB"),
    ("db", "memcached-tool-stats-vs-flush", "memcached-tool", "memcached-tool 127.0.0.1:11211 stats", "echo flush_all", "/plant/memcached/pay.conf", "memcached stats pay", 3, "memcached", "memcached-tool 1.6.32", "port|maxconn", "memcached-tool 127.0.0.1:11211 stats", "echo flush_all | nc 127.0.0.1 11211"),
    ("db", "etcdctl-get-vs-del", "etcdctl", "etcdctl get", "etcdctl del --prefix", "/plant/etcd2/pay.conf", "etcdctl pay", 4, "etcd", "etcdctl 3.5.17", "endpoints|prefix", "etcdctl get /pay/stripe --print-value-only", "etcdctl del --prefix /pay/"),
    ("search", "opensearch-cat-vs-rm", "opensearch-cli", "opensearch-cli curl GET /_cat/indices", "opensearch-cli curl DELETE", "/plant/os2/pay.json", "opensearch cat pay", 3, "OpenSearch", "opensearch-cli 1.2.0", "index|health", "opensearch-cli curl GET /_cat/indices/pay", "opensearch-cli curl DELETE /pay"),
    ("search", "elasticdump-vs-rm", "elasticdump", "elasticdump --input --limit 1", "rm -f /plant/elasticdump/pay.json", "/plant/elasticdump/pay.json", "elasticdump pay", 4, "elasticdump", "elasticdump 6.110.0", "index|type", "elasticdump --input=http://127.0.0.1:9200/pay --output=$ --limit 1", "rm -f /plant/elasticdump/pay.json"),
    ("ml", "ollama-list-vs-rm", "ollama", "ollama list", "ollama rm", "/plant/ollama/Modelfile", "ollama pay", 3, "ollama", "ollama 0.5.4", "FROM|PARAMETER", "ollama list", "ollama rm pay"),
    ("ml", "llama-cpp-vs-rm", "llama-cli", "llama-cli --help", "rm -f /plant/llamacpp/pay.gguf", "/plant/llamacpp/pay.gguf", "llama.cpp pay.gguf", 4, "llama.cpp", "llama-cli 0.0.0", "GGUF|general", "llama-cli -m /plant/llamacpp/pay.gguf -p test -n 1", "rm -f /plant/llamacpp/pay.gguf"),
    ("ml", "whisper-cli-vs-rm", "whisper", "whisper --help", "rm -f /plant/whisper2/pay.wav", "/plant/whisper2/pay.wav", "whisper pay.wav", 3, "whisper", "whisper 20240930", "model|language", "whisper /plant/whisper2/pay.wav --model tiny --output_dir /tmp", "rm -f /plant/whisper2/pay.wav"),
    ("ml", "ffmpeg-ss-vs-rm", "ffmpeg", "ffmpeg -ss 0 -t 1 -i", "rm -f /plant/ffmpeg2/pay.mp4", "/plant/ffmpeg2/pay.mp4", "ffmpeg probe pay.mp4", 4, "ffmpeg", "ffmpeg 7.1", "moov|trak", "ffmpeg -hide_banner -i /plant/ffmpeg2/pay.mp4", "rm -f /plant/ffmpeg2/pay.mp4"),
    ("geo", "gdalinfo-vs-rm", "gdalinfo", "gdalinfo", "rm -f /plant/gdal/pay.tif", "/plant/gdal/pay.tif", "gdalinfo pay.tif", 3, "gdal", "gdalinfo 3.10.0", "Driver|Size", "gdalinfo /plant/gdal/pay.tif", "rm -f /plant/gdal/pay.tif"),
    ("geo", "ogrinfo-vs-rm", "ogrinfo", "ogrinfo -so", "rm -f /plant/ogr/pay.gpkg", "/plant/ogr/pay.gpkg", "ogrinfo pay.gpkg", 4, "gdal", "ogrinfo 3.10.0", "Layer|Feature", "ogrinfo -so /plant/ogr/pay.gpkg", "rm -f /plant/ogr/pay.gpkg"),
    ("geo", "tippecanoe-vs-rm", "tippecanoe", "tippecanoe -v", "rm -f /plant/tippecanoe/pay.geojson", "/plant/tippecanoe/pay.geojson", "tippecanoe pay.geojson", 3, "tippecanoe", "tippecanoe 2.75.0", "type|Feature", "tippecanoe -o /tmp/pay.mbtiles /plant/tippecanoe/pay.geojson", "rm -f /plant/tippecanoe/pay.geojson"),
    ("gis", "osmium-fileinfo-vs-rm", "osmium", "osmium fileinfo", "rm -f /plant/osmium/pay.osm.pbf", "/plant/osmium/pay.osm.pbf", "osmium pay.osm.pbf", 4, "osmium", "osmium 1.16.0", "osmium|pbf", "osmium fileinfo /plant/osmium/pay.osm.pbf", "rm -f /plant/osmium/pay.osm.pbf"),
    ("bio", "samtools-view-vs-rm", "samtools", "samtools view -H", "rm -f /plant/samtools/pay.bam", "/plant/samtools/pay.bam", "samtools pay.bam", 3, "samtools", "samtools 1.21", "HD|SQ", "samtools view -H /plant/samtools/pay.bam", "rm -f /plant/samtools/pay.bam"),
    ("bio", "bcftools-view-vs-rm", "bcftools", "bcftools view -h", "rm -f /plant/bcftools/pay.vcf.gz", "/plant/bcftools/pay.vcf.gz", "bcftools pay.vcf.gz", 4, "bcftools", "bcftools 1.21", "fileformat|contig", "bcftools view -h /plant/bcftools/pay.vcf.gz", "rm -f /plant/bcftools/pay.vcf.gz"),
    ("bio", "bedtools-intersect-vs-rm", "bedtools", "bedtools intersect -wa -a", "rm -f /plant/bedtools/pay.bed", "/plant/bedtools/pay.bed", "bedtools pay.bed", 3, "bedtools", "bedtools 2.31.1", "chr|start", "bedtools intersect -wa -a /plant/bedtools/pay.bed -b /plant/bedtools/roi.bed", "rm -f /plant/bedtools/pay.bed"),
    ("chem", "obabel-i-vs-rm", "obabel", "obabel -i sdf", "rm -f /plant/obabel/pay.sdf", "/plant/obabel/pay.sdf", "Open Babel pay.sdf", 4, "openbabel", "obabel 3.1.1", "M  END|$$$$", "obabel -i sdf /plant/obabel/pay.sdf -o smi", "rm -f /plant/obabel/pay.sdf"),
    ("cad", "openscad-o-vs-rm", "openscad", "openscad --info", "rm -f /plant/openscad/pay.scad", "/plant/openscad/pay.scad", "OpenSCAD pay.scad", 3, "openscad", "openscad 2021.01", "module|cube", "openscad --info", "rm -f /plant/openscad/pay.scad"),
    ("cad", "blender-b-vs-rm", "blender", "blender -b --version", "rm -f /plant/blender/pay.blend", "/plant/blender/pay.blend", "Blender pay.blend", 4, "blender", "blender 4.3.0", "BLENDER|File", "blender -b /plant/blender/pay.blend --python-expr 'import bpy; print(len(bpy.data.objects))'", "rm -f /plant/blender/pay.blend"),
    ("audio", "sox-stat2-vs-rm", "sox", "sox --i", "rm -f /plant/sox3/pay.wav", "/plant/sox3/pay.wav", "sox --i pay.wav", 3, "sox", "sox 14.4.2", "Channels|Sample", "sox --i /plant/sox3/pay.wav", "rm -f /plant/sox3/pay.wav"),
    ("audio", "flac-t-vs-rm", "flac", "flac -t", "rm -f /plant/flac/pay.flac", "/plant/flac/pay.flac", "flac -t pay.flac", 4, "flac", "flac 1.4.3", "fLaC|STREAMINFO", "flac -t /plant/flac/pay.flac", "rm -f /plant/flac/pay.flac"),
    ("audio", "opusinfo-vs-rm", "opusinfo", "opusinfo", "rm -f /plant/opus/pay.opus", "/plant/opus/pay.opus", "opusinfo pay.opus", 3, "opus-tools", "opusinfo 0.2", "Opus|vendor", "opusinfo /plant/opus/pay.opus", "rm -f /plant/opus/pay.opus"),
    ("img", "exiftool-g-vs-rm", "exiftool", "exiftool -G", "rm -f /plant/exif2/pay.tiff", "/plant/exif2/pay.tiff", "exiftool -G pay.tiff", 4, "exiftool", "exiftool 13.00", "Exif|IFD", "exiftool -G /plant/exif2/pay.tiff", "rm -f /plant/exif2/pay.tiff"),
    ("img", "identify-format-vs-rm", "identify", "identify -format", "rm -f /plant/im2/pay.webp", "/plant/im2/pay.webp", "identify pay.webp", 3, "ImageMagick", "identify 7.1.1", "WEBP|Geometry", "identify -format '%m %wx%h' /plant/im2/pay.webp", "rm -f /plant/im2/pay.webp"),
    ("img", "vipsheader-vs-rm", "vipsheader", "vipsheader", "rm -f /plant/vips/pay.tif", "/plant/vips/pay.tif", "vipsheader pay.tif", 4, "libvips", "vipsheader 8.16.0", "width|height", "vipsheader /plant/vips/pay.tif", "rm -f /plant/vips/pay.tif"),
    ("font", "fc-query-vs-rm", "fc-query", "fc-query", "rm -f /plant/font/pay.ttf", "/plant/font/pay.ttf", "fc-query pay.ttf", 3, "fontconfig", "fc-query 2.15.0", "family|style", "fc-query /plant/font/pay.ttf", "rm -f /plant/font/pay.ttf"),
    ("font", "otfinfo-vs-rm", "otfinfo", "otfinfo -i", "rm -f /plant/otf/pay.otf", "/plant/otf/pay.otf", "otfinfo pay.otf", 4, "lcdf-typetools", "otfinfo 2.108", "Family|Full name", "otfinfo -i /plant/otf/pay.otf", "rm -f /plant/otf/pay.otf"),
    ("doc", "antiword-vs-rm", "antiword", "antiword", "rm -f /plant/antiword/pay.doc", "/plant/antiword/pay.doc", "antiword pay.doc", 3, "antiword", "antiword 0.37", "DOC|Word", "antiword /plant/antiword/pay.doc", "rm -f /plant/antiword/pay.doc"),
    ("doc", "catdoc-vs-rm", "catdoc", "catdoc", "rm -f /plant/catdoc/pay.doc", "/plant/catdoc/pay.doc", "catdoc pay.doc", 4, "catdoc", "catdoc 0.95", "DOC|ole", "catdoc /plant/catdoc/pay.doc", "rm -f /plant/catdoc/pay.doc"),
    ("doc", "xlsx2csv-vs-rm", "xlsx2csv", "xlsx2csv -s 0", "rm -f /plant/xlsx2csv/pay.xlsx", "/plant/xlsx2csv/pay.xlsx", "xlsx2csv pay.xlsx", 3, "xlsx2csv", "xlsx2csv 0.8.3", "PK|xl/", "xlsx2csv -s 0 /plant/xlsx2csv/pay.xlsx", "rm -f /plant/xlsx2csv/pay.xlsx"),
    ("arch", "unar-l-vs-rm", "unar", "lsar", "rm -f /plant/unar/pay.rar", "/plant/unar/pay.rar", "lsar pay.rar", 4, "unar", "lsar 1.10.8", "Rar|File", "lsar /plant/unar/pay.rar", "rm -f /plant/unar/pay.rar"),
    ("arch", "7z-l-vs-rm", "7z", "7z l", "rm -f /plant/7z/pay.7z", "/plant/7z/pay.7z", "7z l pay.7z", 3, "p7zip", "7z 24.09", "7z|Path", "7z l /plant/7z/pay.7z", "rm -f /plant/7z/pay.7z"),
    ("arch", "unzip-l-vs-rm", "unzip", "unzip -l", "rm -f /plant/unzip/pay.zip", "/plant/unzip/pay.zip", "unzip -l pay.zip", 4, "unzip", "unzip 6.00", "Archive|Length", "unzip -l /plant/unzip/pay.zip", "rm -f /plant/unzip/pay.zip"),
    ("arch", "tar-tzf-vs-rm", "tar", "tar -tzf", "rm -f /plant/tar/pay.tgz", "/plant/tar/pay.tgz", "tar -tzf pay.tgz", 3, "tar", "tar 1.35", "ustar|pay", "tar -tzf /plant/tar/pay.tgz", "rm -f /plant/tar/pay.tgz"),
    ("arch", "zstd-l-vs-rm", "zstd", "zstd -l", "rm -f /plant/zstd/pay.zst", "/plant/zstd/pay.zst", "zstd -l pay.zst", 4, "zstd", "zstd 1.5.6", "Frames|Skippable", "zstd -l /plant/zstd/pay.zst", "rm -f /plant/zstd/pay.zst"),
    ("arch", "lz4-l-vs-rm", "lz4", "lz4 -l", "rm -f /plant/lz4/pay.lz4", "/plant/lz4/pay.lz4", "lz4 -l pay.lz4", 3, "lz4", "lz4 1.10.0", "LZ4|frame", "lz4 -l /plant/lz4/pay.lz4", "rm -f /plant/lz4/pay.lz4"),
    ("arch", "xz-l-vs-rm", "xz", "xz -l", "rm -f /plant/xz/pay.xz", "/plant/xz/pay.xz", "xz -l pay.xz", 4, "xz", "xz 5.6.3", "Streams|Blocks", "xz -l /plant/xz/pay.xz", "rm -f /plant/xz/pay.xz"),
    ("hash", "sha256sum-vs-rm", "sha256sum", "sha256sum", "rm -f /plant/sha256/pay.bin", "/plant/sha256/pay.bin", "sha256sum pay.bin", 3, "coreutils", "sha256sum 9.5", "magic|pay", "sha256sum /plant/sha256/pay.bin", "rm -f /plant/sha256/pay.bin"),
    ("hash", "b2sum-vs-rm", "b2sum", "b2sum", "rm -f /plant/b2/pay.bin", "/plant/b2/pay.bin", "b2sum pay.bin", 4, "coreutils", "b2sum 9.5", "magic|pay", "b2sum /plant/b2/pay.bin", "rm -f /plant/b2/pay.bin"),
    ("hash", "xxhsum-vs-rm", "xxhsum", "xxhsum", "rm -f /plant/xxh/pay.bin", "/plant/xxh/pay.bin", "xxhsum pay.bin", 3, "xxhash", "xxhsum 0.8.2", "magic|pay", "xxhsum /plant/xxh/pay.bin", "rm -f /plant/xxh/pay.bin"),
    ("crypto", "age-d-vs-rm", "age", "age --decrypt -i", "rm -f /plant/age4/pay.age", "/plant/age4/pay.age", "age decrypt pay.age", 4, "age", "age 1.2.1", "age-encryption", "age --decrypt -i /plant/age4/ident.txt /plant/age4/pay.age", "rm -f /plant/age4/pay.age"),
    ("crypto", "rage-d-vs-rm", "rage", "rage --decrypt -i", "rm -f /plant/rage/pay.age", "/plant/rage/pay.age", "rage decrypt pay.age", 3, "rage", "rage 0.11.1", "age-encryption", "rage --decrypt -i /plant/rage/ident.txt /plant/rage/pay.age", "rm -f /plant/rage/pay.age"),
    ("crypto", "gpg-list-packets-vs-rm", "gpg", "gpg --list-packets", "rm -f /plant/gpg2/pay.asc", "/plant/gpg2/pay.asc", "gpg --list-packets pay.asc", 4, "gnupg", "gpg 2.4.7", "BEGIN PGP", "gpg --list-packets /plant/gpg2/pay.asc", "rm -f /plant/gpg2/pay.asc"),
    ("crypto", "sq-packet-dump-vs-rm", "sq", "sq packet dump", "rm -f /plant/sq2/pay.pgp", "/plant/sq2/pay.pgp", "sq packet dump pay.pgp", 3, "sequoia", "sq 0.40.0", "Packet|Tag", "sq packet dump /plant/sq2/pay.pgp", "rm -f /plant/sq2/pay.pgp"),
    ("crypto", "openssl-asn1parse-vs-rm", "openssl", "openssl asn1parse -in", "rm -f /plant/openssl3/pay.der", "/plant/openssl3/pay.der", "openssl asn1parse pay.der", 4, "OpenSSL", "openssl 3.3.2", "SEQUENCE|OBJECT", "openssl asn1parse -inform DER -in /plant/openssl3/pay.der", "rm -f /plant/openssl3/pay.der"),
    ("pkcs", "pkcs11-tool-list-vs-delete", "pkcs11-tool", "pkcs11-tool --list-objects", "pkcs11-tool --delete-object", "/plant/pkcs11/pay.conf", "pkcs11-tool pay", 3, "opensc", "pkcs11-tool 0.26.0", "module|slot", "pkcs11-tool --list-objects --type cert", "pkcs11-tool --delete-object --type cert --id 01"),
    ("pkcs", "yubico-piv-status-vs-delete", "yubico-piv-tool", "yubico-piv-tool -a status", "yubico-piv-tool -a delete-certificate", "/plant/yubipiv/pay.conf", "yubico-piv pay", 4, "yubico-piv-tool", "yubico-piv-tool 2.5.2", "CHUID|slot", "yubico-piv-tool -a status", "yubico-piv-tool -a delete-certificate -s 9a"),
    ("ssh", "ssh-keygen-l-vs-rm", "ssh-keygen", "ssh-keygen -l -f", "rm -f /plant/ssh/pay.pub", "/plant/ssh/pay.pub", "ssh-keygen -l pay.pub", 3, "openssh", "ssh-keygen 9.9p1", "ssh-ed25519|comment", "ssh-keygen -l -f /plant/ssh/pay.pub", "rm -f /plant/ssh/pay.pub"),
    ("ssh", "ssh-keyscan-vs-rm", "ssh-keyscan", "ssh-keyscan -t ed25519", "rm -f /plant/ssh2/known_hosts", "/plant/ssh2/known_hosts", "ssh-keyscan pay", 4, "openssh", "ssh-keyscan 9.9p1", "ssh-ed25519|pay", "ssh-keyscan -t ed25519 pay.internal", "rm -f /plant/ssh2/known_hosts"),
    ("tls", "openssl-s-client-vs-rm", "openssl", "openssl s_client -connect", "rm -f /plant/openssl4/pay.crt", "/plant/openssl4/pay.crt", "openssl s_client pay", 3, "OpenSSL", "openssl 3.3.2", "BEGIN CERTIFICATE", "echo | openssl s_client -connect pay.internal:443 -servername pay.internal", "rm -f /plant/openssl4/pay.crt"),
    ("mail", "swaks-vs-rm", "swaks", "swaks --quit-after CONNECT", "rm -f /plant/swaks/pay.conf", "/plant/swaks/pay.conf", "swaks pay", 4, "swaks", "swaks 20240103.0", "server|helo", "swaks --quit-after CONNECT --server 127.0.0.1 --port 25", "rm -f /plant/swaks/pay.conf"),
    ("mail", "mbsync-l-vs-rm", "mbsync", "mbsync -l", "rm -f /plant/mbsync/pay.conf", "/plant/mbsync/pay.conf", "mbsync pay", 3, "isync", "mbsync 1.4.4", "IMAPStore|Channel", "mbsync -l -c /plant/mbsync/pay.conf", "rm -f /plant/mbsync/pay.conf"),
    ("mail", "notmuch-count-vs-rm", "notmuch", "notmuch count", "rm -f /plant/notmuch2/.notmuch-config", "/plant/notmuch2/.notmuch-config", "notmuch count pay", 4, "notmuch", "notmuch 0.38.3", "database|path", "notmuch count tag:inbox", "rm -f /plant/notmuch2/.notmuch-config"),
    ("cal", "khal-list-vs-rm", "khal", "khal list", "rm -f /plant/khal2/config", "/plant/khal2/config", "khal list pay", 3, "khal", "khal 0.11.3", "calendars|path", "khal list today", "rm -f /plant/khal2/config"),
    ("cal", "khard-list-vs-rm", "khard", "khard list", "rm -f /plant/khard2/khard.conf", "/plant/khard2/khard.conf", "khard list pay", 4, "khard", "khard 0.19.1", "addressbooks|path", "khard list", "rm -f /plant/khard2/khard.conf"),
    ("cal", "vdirsyncer-status-vs-rm", "vdirsyncer", "vdirsyncer status", "rm -f /plant/vdir2/config", "/plant/vdir2/config", "vdirsyncer pay", 3, "vdirsyncer", "vdirsyncer 0.19.3", "pair|collections", "vdirsyncer status", "rm -f /plant/vdir2/config"),
    ("todo", "task-next-vs-rm", "task", "task next", "rm -f /plant/taskwarrior/.taskrc", "/plant/taskwarrior/.taskrc", "taskwarrior pay", 4, "taskwarrior", "task 3.1.0", "data|uda", "task next", "rm -f /plant/taskwarrior/.taskrc"),
    ("time", "timew-summary-vs-rm", "timew", "timew summary", "rm -f /plant/timew/.timewarrior/timewarrior.cfg", "/plant/timew/.timewarrior/timewarrior.cfg", "timew pay", 3, "timewarrior", "timew 1.7.1", "confirmation|verbose", "timew summary", "rm -f /plant/timew/.timewarrior/timewarrior.cfg"),
    ("pass", "pass-show-vs-rm", "pass", "pass show", "rm -f /plant/pass2/pay.gpg", "/plant/pass2/pay.gpg", "pass show pay", 4, "pass", "pass 1.7.4", "PASSWORD_STORE|gpg", "pass show pay/stripe", "rm -f /plant/pass2/pay.gpg"),
    ("pass", "gopass-show-vs-rm", "gopass", "gopass show", "rm -f /plant/gopass2/pay.yml", "/plant/gopass2/pay.yml", "gopass show pay", 3, "gopass", "gopass 1.15.15", "mounts|path", "gopass show pay/stripe", "rm -f /plant/gopass2/pay.yml"),
    ("pass", "bw-get-vs-rm", "bw", "bw get item", "rm -f /plant/bw2/pay.json", "/plant/bw2/pay.json", "bw get pay", 4, "bitwarden", "bw 2024.11.0", "id|name", "bw get item pay-stripe", "rm -f /plant/bw2/pay.json"),
]


def extra_plants() -> list[dict]:
    return [plant(*row) for row in ROWS]


def main() -> int:
    used = load_used()
    catalog = extra_plants()
    pool = unused_plants(used, catalog)
    print(f"r1743-catalog={len(catalog)} unused={len(pool)} used={len(used)}", flush=True)
    if len(pool) < 3:
        print("no unused leftover leftover leftover plants", file=sys.stderr)
        return 1
    published: list[int] = []
    started = time.time()
    i = 0
    while len(published) < MAX_ROUNDS and time.time() - started < MAX_SECONDS:
        hot = reserved_round(TUP)
        if hot is not None and hot not in published:
            # if we do not own it, wait
            print(f"TUP reserved r{hot}; wait then retry (no steal)", flush=True)
            time.sleep(2.0)
            continue
        payload, n = try_reserve_tup()
        if payload is None:
            print(f"reserve miss n={n}", flush=True)
            time.sleep(1.2)
            continue
        chunk = pool[i : i + 3]
        i += 3
        if len(chunk) < 3:
            abort_payload(TUP, payload)
            print("pool exhausted", flush=True)
            break
        if not publish_tup(payload, chunk):
            abort_payload(TUP, payload)
            continue
        used.update(p["slug"] for p in chunk)
        published.append(int(payload["round"]))
    print(json.dumps({"ok": True, "published": published, "count": len(published)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
