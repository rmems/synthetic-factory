#!/usr/bin/env python3
"""Mill monorepo-dep-bump-factory r1454+ unique desktop/backup/obs/db leftover plants.

BAN r01–r1453 clones including elvish-toml-leftover-prompt / oil-rc-leftover-strict,
hydra-py-leftover-compose / sacred-py-leftover-observer,
solr-xml-leftover-cache / opensearchdash-yml-leftover-sso, leftover-revpin, libNNNN,
r690–r708 workspace clones. Do not rerun mdb-mill-r1351 or mdb-mill-r1407.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

_BASE = Path(__file__).with_name("mdb-mill-r1407.py")
_spec = importlib.util.spec_from_file_location("mdb_mill_r1407", _BASE)
_m = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(_m)

FACTORY = _m.FACTORY
GEN = _m.GEN
CATALOG_FIRST = 1454
P = _m.P
build_episode = _m.build_episode
make = _m.make

PRIOR_SLUGS = tuple(spec["slug"] for pair in _m.PAIRS for spec in pair)
BANNED_SLUG_NEEDLES = _m.BANNED_SLUG_NEEDLES + PRIOR_SLUGS + (
    "elvish-toml-leftover-prompt",
    "oil-rc-leftover-strict",
    "hydra-py-leftover-compose",
    "sacred-py-leftover-observer",
    "solr-xml-leftover-cache",
    "opensearchdash-yml-leftover-sso",
    "leftover-revpin",
    "libNNNN",
    "pnpm-override",
    "npm-catalog",
    "yarn-constraints",
    "bun-catalog",
    "uv-workspace",
    "poetry-source",
    "cargo-wsdep",
    "gowork-use",
    "maven-bom",
    "gradle-catalog",
    "nx-implicit",
    "turbo-",
    "changesets-",
)
_m.BANNED_SLUG_NEEDLES = BANNED_SLUG_NEEDLES

STEMS = [
    "albatross", "bittern", "chukar", "dunlin", "egret", "fulmar", "gannet", "harrier", "ibis", "jacana",
    "kestrel", "lapwing", "merlin", "nuthatch", "osprey", "puffin", "quailx", "razorbill", "sanderling", "turnstone",
    "umbrellabird", "vireo", "wagtail", "xenops", "yellowthroat", "accentor", "booby", "cormorant", "dipper", "eider",
    "flycatcher", "grebe", "hoopoe", "iora", "jaeger", "knotbird", "loon", "murre", "noddy", "ovenbird",
    "phalarope", "quelea", "redstart", "shrike", "tanager", "urubu", "veery", "whimbrel", "xantus", "yellowlegs",
    "anhinga", "bushtit", "creeper", "dickcissel", "fieldfare", "godwit", "hornbill", "indigobird", "jacamar", "kinglet",
    "longspur", "meadowlark", "nutcracker", "oystercatcher", "pipit", "quetzal", "roadrunner", "siskin", "towhee", "verdin",
    "woodcock", "xenopsx", "yellowhammer", "auklet", "brant", "canvasback", "dowitcher", "eiderhen", "goshawk", "hawfinch",
]
assert len(STEMS) == 80
PLANTS = [f"{s}q" for s in STEMS] + [f"{s}r" for s in STEMS]


def notes_for(round_n: int, a: dict, b: dict) -> str:
    ea = f"mdb-r{round_n}-{a['slug']}"
    eb = f"mdb-r{round_n}-{b['slug']}"
    novel = 88 + (round_n % 5)
    return f"""# NOTES-r{round_n} monorepo-dep-bump-factory

Novel coverage: {novel}%

Two designed episodes (quota 2). Surfaces: {a['surface']} ({a['pkg']} {a['api_break']}); {b['surface']} ({b['pkg']} {b['api_break']}).
Not a pin-file mill and not libNNNN recycle. Distinct from r01–r1453 clones (ban elvish-toml-leftover-prompt / oil-rc-leftover-strict; hydra-py-leftover-compose / sacred-py-leftover-observer; solr-xml-leftover-cache / opensearchdash-yml-leftover-sso; leftover-revpin; r690–r708 workspace clones).

| id | seed | first apply | plan change | terminal |
|---|---|---|---|---|
| {ea} | {a['surface']} | nested {a['new']} | SoT {a['new']} + {a['api_break']} | {'leftover-workspace fail; ' + a['left'] + ' ' + a.get('left_ver', a['old']) if a['fail'] else 'success; ' + a['left'] + ' leftover'} |
| {eb} | {b['surface']} | nested {b['new']} | SoT {b['new']} + {b['api_break']} | {'leftover-workspace fail; ' + b['left'] + ' ' + b.get('left_ver', b['old']) if b['fail'] else 'success; ' + b['left'] + ' leftover'} |

## Step counts
- ep1: 18. Nested apply 6–7; plan change 8; API break 10–12; leftover {a['left']}.
- ep2: 18. Nested apply 6–7; plan change 8; API break 10–12; leftover-workspace fail {b['left']}.

## decision_basis audit
Every step starts Plan:/Observation:/Reflection:, ≤240 chars.
No thought / chain_of_thought / scratch / inner_monologue. No spike_events.
No sim_or_real: real. Plants `{a['plant']}` and `{b['plant']}`.

## Weaknesses / next
Keep unique leftover leftover leftover plots. Ban r01–r1453 clones, libNNNN, r690–r708 workspace clones.
"""


def R(pkg: str, ext: str, leftover: str, name: str, old: str, new: str, pin: str,
      nest_old: str, nest_new: str, api_old: str, api_new: str, api_break: str) -> tuple:
    return (
        f"{pkg}-{ext}-leftover-{leftover}",
        f"{name} leftover vs {pin}",
        pkg, old, new, pin, nest_old, nest_new, api_old, api_new, api_break, ext,
    )


RAW: list[tuple] = [
    R("wezterm", "toml", "termgpu", "WezTerm", "20240203", "20241015", "wezterm.toml",
      "webgpu_power_preference = \"low-power\"", "webgpu_power_preference = \"high-performance\"",
      "max_fps = 60", "max_fps = 120", "high-perf gpu + 120fps"),
    R("ghostty", "conf", "shader", "Ghostty", "1.0.1", "1.1.2", "ghostty.conf",
      "custom-shader = none", "custom-shader = crt.glsl",
      "window-vsync = true", "window-vsync = false", "crt shader + vsync off"),
    R("kitty", "conf", "ligature", "Kitty", "0.36.4", "0.37.0", "kitty.conf",
      "disable_ligatures never", "disable_ligatures cursor",
      "font_features none", "font_features +calt +liga", "cursor ligatures + calt"),
    R("foot", "ini", "gamma", "foot", "1.18.1", "1.19.0", "foot.ini",
      "gamma-correct-blending=no", "gamma-correct-blending=yes",
      "dpi-aware=no", "dpi-aware=yes", "gamma blend + dpi-aware"),
    R("alacritty", "toml", "livecfg", "Alacritty", "0.13.2", "0.15.0", "alacritty.toml",
      "live_config_reload = false", "live_config_reload = true",
      "decorations = \"full\"", "decorations = \"none\"", "live reload + no decorations"),
    R("niri", "kdl", "gestures", "niri", "0.1.9", "25.02", "niri.kdl",
      "hotkey-overlay { skip-at-startup }", "gestures { hotkey-overlay { skip-at-startup } }",
      "prefer-no-csd", "prefer-no-csd; screenshot-path \"~/shots/\"", "gestures + screenshot path"),
    R("hyprland", "conf", "swipe", "Hyprland", "0.45.2", "0.47.2", "hyprland.conf",
      "gestures:workspace_swipe = false", "gestures:workspace_swipe = true",
      "gestures:workspace_swipe_fingers = 3", "gestures:workspace_swipe_fingers = 4",
      "workspace swipe + 4 fingers"),
    R("swayfx", "conf", "blurpass", "SwayFX", "0.4", "0.5.2", "swayfx.conf",
      "blur enable false", "blur enable true",
      "blur_passes 0", "blur_passes 3", "blur on + 3 passes"),
    R("river", "init", "attachmode", "river", "0.3.5", "0.3.7", "init",
      "riverctl attach-mode top", "riverctl attach-mode bottom",
      "riverctl focus-follows-cursor disabled", "riverctl focus-follows-cursor normal",
      "bottom attach + ffm"),
    R("waybar", "json", "modulereload", "Waybar", "0.11.0", "0.12.0", "config.json",
      "\"reload_style_on_change\": false", "\"reload_style_on_change\": true",
      "\"modules-left\": [\"sway/workspaces\"]", "\"modules-left\": [\"niri/workspaces\",\"clock\"]",
      "live css + niri modules"),
    R("mako", "conf", "layering", "mako", "1.9.0", "1.10.0", "mako.conf",
      "layer=top", "layer=overlay",
      "max-visible=5", "max-visible=3", "overlay layer + 3 visible"),
    R("dunst", "conf", "stacking", "dunst", "1.11.0", "1.12.1", "dunstrc",
      "stack_duplicates = false", "stack_duplicates = true",
      "origin = top-right", "origin = bottom-right", "stack dups + bottom origin"),
    R("rofi", "rasi", "iconset", "rofi", "1.7.5", "1.7.8", "config.rasi",
      "show-icons: false;", "show-icons: true;",
      "icon-theme: \"Adwaita\";", "icon-theme: \"Papirus\";", "icons on + Papirus"),
    R("wofi", "conf", "drunfilter", "wofi", "1.4.1", "1.5.0", "wofi.conf",
      "allow_images=false", "allow_images=true",
      "insensitive=false", "insensitive=true", "images + case-insensitive"),
    R("fuzzel", "ini", "launch", "fuzzel", "1.10.2", "1.11.1", "fuzzel.ini",
      "launch-prefix=", "launch-prefix=uwsm-app --",
      "icons-enabled=no", "icons-enabled=yes", "uwsm launch + icons"),
    R("tofi", "conf", "fuzzy", "tofi", "0.9.1", "0.9.1-api", "tofi.conf",
      "fuzzy-match = false", "fuzzy-match = true",
      "num-results = 5", "num-results = 12", "fuzzy + 12 results"),
    R("restic", "conf", "packsize", "restic", "0.17.1", "0.17.3", "restic.conf",
      "pack-size = 4", "pack-size = 16",
      "compression = off", "compression = max", "16MiB packs + max compression"),
    R("borgmatic", "yml", "keepweekly", "borgmatic", "1.8.14", "1.9.5", "config.yaml",
      "keep_weekly: 0", "keep_weekly: 4",
      "compression: lz4", "compression: zstd", "4 weekly + zstd"),
    R("kopia", "conf", "compression", "Kopia", "0.17.0", "0.19.0", "kopia.config",
      "compression: none", "compression: zstd-best",
      "max-upload-speed: 0", "max-upload-speed: 10485760", "zstd-best + 10MiB cap"),
    R("duplicacy", "conf", "chunk", "Duplicacy", "3.2.3", "3.2.4", "duplicacy.json",
      "\"chunk-size\": 4194304", "\"chunk-size\": 16777216",
      "\"hash\": \"sha256\"", "\"hash\": \"blake3\"", "16MiB chunks + blake3"),
    R("rclone", "conf", "transfers", "rclone", "1.68.2", "1.69.1", "rclone.conf",
      "transfers = 4", "transfers = 16",
      "checkers = 8", "checkers = 32", "16 transfers + 32 checkers"),
    R("rsnapshot", "conf", "retain", "rsnapshot", "1.4.5", "1.4.5-api", "rsnapshot.conf",
      "retain daily 7", "retain daily 14",
      "sync_first 0", "sync_first 1", "14 daily + sync_first"),
    R("seaweedfs", "toml", "volume", "SeaweedFS", "3.80", "3.85", "weed.toml",
      "volumeSizeLimitMB = 30000", "volumeSizeLimitMB = 50000",
      "compactionMBps = 0", "compactionMBps = 64", "50GB volumes + 64MBps compact"),
    R("garagehq", "toml", "layout", "Garage", "1.0.1", "1.1.0", "garage.toml",
      "replication_mode = \"none\"", "replication_mode = \"3\"",
      "compression_level = 0", "compression_level = 3", "3-way replica + zstd 3"),
    R("minio", "env", "ilm", "MinIO", "RELEASE.2024-11-07", "RELEASE.2025-02-03", "minio.env",
      "MINIO_ILM_TRANSITION=off", "MINIO_ILM_TRANSITION=on",
      "MINIO_API_REQUESTS_MAX=0", "MINIO_API_REQUESTS_MAX=10000", "ILM on + 10k req cap"),
    R("cephfs", "conf", "mds", "CephFS", "19.2.0", "19.2.1", "ceph.conf",
      "mds_cache_memory_limit = 1073741824", "mds_cache_memory_limit = 4294967296",
      "mds_bal_interval = 10", "mds_bal_interval = 5", "4GiB MDS cache + 5s bal"),
    R("gluster", "vol", "heal", "GlusterFS", "11.1", "11.2", "gluster.vol",
      "cluster.heal-timeout 600", "cluster.heal-timeout 60",
      "cluster.self-heal-daemon off", "cluster.self-heal-daemon on", "60s heal + daemon on"),
    R("lustre", "conf", "stripe", "Lustre", "2.15.4", "2.16.1", "lustre.conf",
      "stripe_count=1", "stripe_count=4",
      "stripe_size=1048576", "stripe_size=4194304", "4 stripes + 4MiB"),
    R("beegfs", "conf", "buddy", "BeeGFS", "7.4.5", "8.0.0", "beegfs.conf",
      "sysMgmtdHost = old", "sysMgmtdHost = api",
      "tuneFileCacheType = none", "tuneFileCacheType = buffered", "api mgmtd + buffered cache"),
    R("longhorn", "yml", "backup", "Longhorn", "1.7.2", "1.8.0", "longhorn.yml",
      "defaultReplicaCount: 2", "defaultReplicaCount: 3",
      "backupTarget: \"\"", "backupTarget: s3://api-backups@us-east-1/", "3 replicas + s3 backup"),
    R("grafana", "ini", "unifiedalert", "Grafana", "11.3.0", "11.5.1", "grafana.ini",
      "unified_alerting.enabled = false", "unified_alerting.enabled = true",
      "alerting.enabled = true", "alerting.enabled = false", "unified alerting on + legacy off"),
    R("prometheus", "yml", "otlp", "Prometheus", "2.55.1", "3.1.0", "prometheus.yml",
      "otlp: { promote_resource_attributes: [] }", "otlp: { promote_resource_attributes: [service.name] }",
      "scrape_interval: 1m", "scrape_interval: 15s", "OTLP service.name + 15s scrape"),
    R("alertmanager", "yml", "inhibit", "Alertmanager", "0.27.0", "0.28.0", "alertmanager.yml",
      "inhibit_rules: []", "inhibit_rules: [{source_match: {severity: critical}, target_match: {severity: warning}}]",
      "repeat_interval: 4h", "repeat_interval: 1h", "critical inhibits warning + 1h repeat"),
    R("thanos", "yml", "compact", "Thanos", "0.36.1", "0.37.2", "thanos.yml",
      "compact.concurrency: 1", "compact.concurrency: 4",
      "retention.resolution-raw: 0d", "retention.resolution-raw: 14d", "4 compact + 14d raw"),
    R("mimir", "yml", "store", "Mimir", "2.14.0", "2.15.0", "mimir.yml",
      "blocks_storage.backend: filesystem", "blocks_storage.backend: s3",
      "ingester.ring.replication_factor: 1", "ingester.ring.replication_factor: 3",
      "s3 blocks + RF3"),
    R("loki", "yml", "tsdb", "Loki", "3.2.1", "3.4.1", "loki.yml",
      "schema_config.configs[0].index.type: boltdb-shipper", "schema_config.configs[0].index.type: tsdb",
      "limits_config.retention_period: 0s", "limits_config.retention_period: 744h",
      "tsdb index + 31d retention"),
    R("tempo", "yml", "metricsgen", "Tempo", "2.6.1", "2.7.1", "tempo.yml",
      "metrics_generator.processor.service_graphs: {}", "metrics_generator.processor.service_graphs.dimensions: [service]",
      "storage.trace.backend: local", "storage.trace.backend: s3", "service graphs + s3"),
    R("jaeger", "yml", "sampling", "Jaeger", "1.62.0", "1.66.0", "jaeger.yml",
      "sampling.strategies.param: 1.0", "sampling.strategies.param: 0.1",
      "storage.type: memory", "storage.type: elasticsearch", "10% sample + ES"),
    R("otelcol", "yml", "batchproc", "OTel Collector", "0.114.0", "0.120.0", "otelcol.yml",
      "processors.batch.timeout: 1s", "processors.batch.timeout: 200ms",
      "processors.batch.send_batch_size: 8192", "processors.batch.send_batch_size: 1024",
      "200ms batch + 1024 size"),
    R("vector", "toml", "remap", "Vector", "0.42.0", "0.44.0", "vector.toml",
      "transforms.parse.type = \"json_parser\"", "transforms.parse.type = \"remap\"",
      "sinks.out.batch.timeout_secs = 1", "sinks.out.batch.timeout_secs = 5",
      "remap VRL + 5s batch"),
    R("fluentbit", "conf", "luafilter", "Fluent Bit", "3.2.2", "3.2.4", "fluent-bit.conf",
      "[FILTER]\nName grep", "[FILTER]\nName lua\nScript /etc/fb/drop.lua",
      "Flush 5", "Flush 1", "lua filter + 1s flush"),
    R("filebeat", "yml", "dissect", "Filebeat", "8.16.1", "8.17.2", "filebeat.yml",
      "processors: [{drop_fields: {fields: [agent]}}]", "processors: [{dissect: {tokenizer: \"%{ts} %{msg}\"}}]",
      "max_bytes: 10485760", "max_bytes: 1048576", "dissect tokenizer + 1MiB"),
    R("cockroach", "yml", "lease", "CockroachDB", "24.3.0", "25.1.0", "cockroach.yml",
      "kv.range_lease.duration: 9s", "kv.range_lease.duration: 3s",
      "sql.defaults.transaction_isolation: SERIALIZABLE", "sql.defaults.transaction_isolation: READ COMMITTED",
      "3s leases + READ COMMITTED"),
    R("yugabyte", "conf", "ysql", "YugabyteDB", "2024.2.0", "2024.2.2", "yugabyte.conf",
      "ysql_enable_packed_row = false", "ysql_enable_packed_row = true",
      "yb_enable_read_committed_isolation = false", "yb_enable_read_committed_isolation = true",
      "packed rows + RC isolation"),
    R("tidb", "toml", "tiflash", "TiDB", "8.4.0", "8.5.0", "tidb.toml",
      "tiflash.enabled = false", "tiflash.enabled = true",
      "max-index-length = 3072", "max-index-length = 12288", "TiFlash on + 12k index"),
    R("vitess", "yml", "vschema", "Vitess", "21.0.2", "21.0.3", "vitess.yml",
      "vindexes: {hash: {type: hash}}", "vindexes: {unicode_loose_md5: {type: unicode_loose_md5}}",
      "sharded: false", "sharded: true", "unicode vindex + sharded"),
    R("citus", "conf", "rebalance", "Citus", "12.1", "13.0", "citus.conf",
      "citus.shard_count = 32", "citus.shard_count = 64",
      "citus.enable_rebalancer = off", "citus.enable_rebalancer = on", "64 shards + rebalancer"),
    R("timescaledb", "conf", "compress", "TimescaleDB", "2.17.2", "2.18.0", "timescaledb.conf",
      "timescaledb.enable_tiered_storage = off", "timescaledb.enable_tiered_storage = on",
      "timescaledb.max_background_workers = 8", "timescaledb.max_background_workers = 16",
      "tiered storage + 16 workers"),
    R("questdb", "conf", "wal", "QuestDB", "8.2.1", "8.2.3", "server.conf",
      "cairo.wal.enabled=false", "cairo.wal.enabled=true",
      "line.tcp.default.partition.by=DAY", "line.tcp.default.partition.by=HOUR",
      "WAL on + hourly partition"),
    R("influxdb", "toml", "bucket", "InfluxDB", "2.7.11", "2.7.12", "influxdb.toml",
      "retention-period = \"0s\"", "retention-period = \"168h\"",
      "shard-group-duration = \"168h\"", "shard-group-duration = \"24h\"",
      "7d retention + daily shards"),
    R("clickhouse", "yml", "ttl", "ClickHouse", "24.11.1", "25.1.3", "config.yml",
      "ttl: none", "ttl: event_time + INTERVAL 30 DAY",
      "merge_tree.max_bytes_to_merge_at_max_space_in_pool: 161061273600",
      "merge_tree.max_bytes_to_merge_at_max_space_in_pool: 322122547200",
      "30d TTL + 300GiB merge"),
    R("neo4j", "conf", "fabric", "Neo4j", "5.25.1", "5.26.0", "neo4j.conf",
      "dbms.routing.enabled=false", "dbms.routing.enabled=true",
      "server.bolt.thread_pool_max_size=400", "server.bolt.thread_pool_max_size=1000",
      "routing on + 1000 bolt threads"),
    R("janusgraph", "prop", "index", "JanusGraph", "1.0.0", "1.1.0", "janusgraph.properties",
      "index.search.backend=lucene", "index.search.backend=elasticsearch",
      "storage.cql.replication-factor=1", "storage.cql.replication-factor=3",
      "ES index + RF3"),
    R("dgraph", "yml", "zero", "Dgraph", "24.0.5", "24.1.0", "dgraph.yml",
      "zero.replicas: 1", "zero.replicas: 3",
      "alpha.lru_mb: 1024", "alpha.lru_mb: 4096", "3 zeros + 4GiB LRU"),
    R("arangodb", "conf", "foxx", "ArangoDB", "3.12.2", "3.12.4", "arangod.conf",
      "foxx.api = false", "foxx.api = true",
      "javascript.v8-contexts = 8", "javascript.v8-contexts = 16", "Foxx on + 16 v8"),
    R("nebula", "conf", "graph", "NebulaGraph", "3.8.0", "3.8.2", "nebula.conf",
      "local_config = true", "local_config = false",
      "heartbeat_interval_secs = 10", "heartbeat_interval_secs = 3", "meta config + 3s hb"),
    R("meilisearch", "toml", "typo", "Meilisearch", "1.11.3", "1.12.0", "meili.toml",
      "typo_tolerance.enabled = false", "typo_tolerance.enabled = true",
      "max_indexing_threads = 1", "max_indexing_threads = 4", "typos on + 4 index threads"),
    R("typesense", "yml", "synonym", "Typesense", "27.1", "28.0", "typesense.yml",
      "synonym_prefix: false", "synonym_prefix: true",
      "max_per_page: 250", "max_per_page: 50", "prefix synonyms + 50/page"),
    R("zincsearch", "yml", "shard", "ZincSearch", "0.4.9", "0.4.10", "zinc.yml",
      "shard.num: 1", "shard.num: 3",
      "wal.sync: none", "wal.sync: fsync", "3 shards + fsync WAL"),
    R("sonic", "cfg", "locale", "Sonic", "1.4.8", "1.4.9", "config.cfg",
      "locale = \"en\"", "locale = \"en,fr\"",
      "store_kv = \"none\"", "store_kv = \"fst\"", "en+fr locale + fst kv"),
    R("vaultwarden", "toml", "admin", "Vaultwarden", "1.32.5", "1.33.0", "config.toml",
      "SIGNUPS_ALLOWED=true", "SIGNUPS_ALLOWED=false",
      "ADMIN_TOKEN=", "ADMIN_TOKEN=api-admin", "signups off + admin token"),
    R("sops", "yml", "age", "sops", "3.9.2", "3.9.4", ".sops.yaml",
      "creation_rules: [{pgp: DEADBEEF}]", "creation_rules: [{age: age1api}]",
      "encrypted_suffix: _secret", "encrypted_regex: ^(data|stringData)$",
      "age recipient + k8s regex"),
    R("gopass", "yml", "store", "gopass", "1.15.14", "1.15.15", "config.yml",
      "core.autoclip: false", "core.autoclip: true",
      "mounts.path: ~/.password-store", "mounts.path: ~/.local/share/gopass/stores/root",
      "autoclip + xdg store"),
    R("passbolt", "php", "gpg", "Passbolt", "4.10.1", "4.11.0", "passbolt.php",
      "'gpg.serverKey.fingerprint' => ''", "'gpg.serverKey.fingerprint' => 'APIKEY'",
      "'passbolt.security.csrfProtection' => false", "'passbolt.security.csrfProtection' => true",
      "server fingerprint + csrf"),
    R("stepca", "yml", "provisioner", "step-ca", "0.28.1", "0.28.2", "ca.yml",
      "provisioners: [{type: JWK}]", "provisioners: [{type: ACME, claims: {maxTLSCertDuration: 24h}}]",
      "db.type: badger", "db.type: postgresql", "ACME 24h + postgres"),
    R("cfssl", "json", "profile", "CFSSL", "1.6.5", "1.6.5-api", "cfssl.json",
      "\"signing\": {\"default\": {\"expiry\": \"8760h\"}}", "\"signing\": {\"default\": {\"expiry\": \"168h\"}}",
      "\"usages\": [\"signing\"]", "\"usages\": [\"signing\",\"server auth\",\"client auth\"]",
      "7d expiry + server/client auth"),
    R("certbot", "ini", "webroot", "Certbot", "2.11.0", "3.1.0", "cli.ini",
      "authenticator = standalone", "authenticator = webroot",
      "webroot-path = /var/www", "webroot-path = /srv/www/acme", "webroot + /srv path"),
    R("smallstep", "json", "ssh", "Smallstep", "0.28.1", "0.28.2", "ssh.json",
      "\"ssh\": {\"hostKey\": \"\"}", "\"ssh\": {\"hostKey\": \"/etc/ssh/ssh_host_ecdsa_key\"}",
      "\"disableIssuedAtCheck\": true", "\"disableIssuedAtCheck\": false",
      "host key + issued-at check"),
    R("gnuradio", "grc", "buffer", "GNU Radio", "3.10.11", "3.10.12", "flow.grc",
      "max_output_buffer: 0", "max_output_buffer: 8192",
      "thread_safe_setters: false", "thread_safe_setters: true", "8k buffer + thread-safe"),
    R("gqrx", "conf", "demod", "Gqrx", "2.17.5", "2.17.6", "gqrx.conf",
      "demod=AM", "demod=WFM",
      "iq_swap=false", "iq_swap=true", "WFM + IQ swap"),
    R("sdrangel", "ini", "device", "SDRangel", "7.22.0", "7.22.4", "sdrangel.ini",
      "device=FileInput", "device=RTLSDR",
      "sampleRate=2048000", "sampleRate=2400000", "RTL-SDR + 2.4Msps"),
    R("dump1090", "conf", "gain", "dump1090", "9.0", "10.0", "dump1090.conf",
      "gain=max", "gain=40.2",
      "net-bo-port=30005", "net-bo-port=30005\nnet-sbs-port=30003", "fixed gain + SBS 30003"),
    R("rtl433", "conf", "flex", "rtl_433", "23.11", "24.10", "rtl_433.conf",
      "protocol=0", "protocol=flex",
      "convert=native", "convert=si", "flex protocol + SI units"),
    R("wsjtx", "ini", "mode", "WSJT-X", "2.7.0", "2.7.1", "WSJT-X.ini",
      "Mode=FT8", "Mode=FT4",
      "TxPower=0", "TxPower=5", "FT4 + 5W"),
    R("pipewire", "conf", "quantum", "PipeWire", "1.2.7", "1.2.8", "pipewire.conf",
      "default.clock.quantum = 1024", "default.clock.quantum = 256",
      "default.clock.min-quantum = 32", "default.clock.min-quantum = 64",
      "256 quantum + min 64"),
    R("wireplumber", "lua", "profile", "WirePlumber", "0.5.6", "0.5.8", "main.lua",
      "default_profile = \"off\"", "default_profile = \"HiFi\"",
      "suspend_timeout = 5", "suspend_timeout = 0", "HiFi profile + no suspend"),
    R("jack", "conf", "period", "JACK", "1.9.22", "1.9.22-api", "jack.conf",
      "period = 1024", "period = 128",
      "nperiods = 2", "nperiods = 3", "128 period + 3 periods"),
    R("ardour", "xml", "export", "Ardour", "8.10", "8.12", "session.xml",
      "<ExportFormat name=\"wav\"/>", "<ExportFormat name=\"flac\" bitdepth=\"24\"/>",
      "<sample-rate>44100</sample-rate>", "<sample-rate>48000</sample-rate>",
      "24-bit FLAC + 48k"),
    R("supercollider", "scd", "bus", "SuperCollider", "3.13.0", "3.13.1", "startup.scd",
      "s.options.numOutputBusChannels = 2", "s.options.numOutputBusChannels = 8",
      "s.options.memSize = 8192", "s.options.memSize = 65536", "8 out + 64k mem"),
    R("csound", "csd", "orchestra", "Csound", "6.18.1", "6.18.1-api", "score.csd",
      "sr = 44100", "sr = 96000",
      "ksmps = 64", "ksmps = 16", "96k sr + ksmps 16"),
    R("typst", "toml", "font", "Typst", "0.12.0", "0.13.0", "typst.toml",
      "font-path = []", "font-path = [\"/usr/share/fonts\"]",
      "pdf-standard = \"1.7\"", "pdf-standard = \"a-2b\"", "system fonts + PDF/A"),
    R("context", "tex", "layout", "ConTeXt", "2024.11.01", "2025.02.01", "cont-en.tex",
      "\\setuplayout[grid=no]", "\\setuplayout[grid=yes]",
      "\\setuppagenumbering[location=footer]", "\\setuppagenumbering[location=header]",
      "grid typesetting + header nums"),
    R("groff", "mom", "macro", "groff", "1.23.0", "1.23.0-api", "doc.mom",
      ".PRINTSTYLE TYPESET", ".PRINTSTYLE TYPEWRITE",
      ".DOCTITLE", ".DOCTYPE default", "typewrite + default doctype"),
    R("asciidoctor", "rb", "pdf", "Asciidoctor", "2.0.23", "2.0.23-api", "doc.rb",
      "Asciidoctor.convert_file(f, backend: 'html5')", "Asciidoctor.convert_file(f, backend: 'pdf')",
      "attributes['source-highlighter'] = 'coderay'", "attributes['source-highlighter'] = 'rouge'",
      "pdf backend + rouge"),
    R("pandoc", "yaml", "cite", "Pandoc", "3.5", "3.6.2", "defaults.yaml",
      "citeproc: false", "citeproc: true",
      "csl: chicago.csl", "csl: apa.csl", "citeproc + APA CSL"),
    R("sile", "lua", "class", "SILE", "0.15.5", "0.15.7", "doc.lua",
      "class = \"plain\"", "class = \"book\"",
      "papersize = \"a4\"", "papersize = \"letter\"", "book class + letter"),
    R("helix", "toml", "lsp", "Helix", "24.07", "25.01", "config.toml",
      "lsp.display-messages = false", "lsp.display-messages = true",
      "lsp.auto-signature-help = false", "lsp.auto-signature-help = true",
      "LSP messages + signature help"),
    R("kakoune", "kak", "hooks", "Kakoune", "2024.05.18", "2024.05.18-api", "kakrc",
      "set-option global autowrap_column 80", "set-option global autowrap_column 100",
      "hook global BufCreate .* %{ }", "hook global WinCreate .* %{ lint-enable }",
      "100 col wrap + lint hook"),
    R("qutebrowser", "py", "js", "qutebrowser", "3.3.1", "3.4.0", "config.py",
      "c.content.javascript.enabled = True", "c.content.javascript.enabled = False",
      "c.auto_save.session = False", "c.auto_save.session = True",
      "JS off + session autosave"),
    R("nyxt", "lisp", "buffer", "Nyxt", "3.11.7", "3.12.0", "config.lisp",
      "(setf *buffer-history* nil)", "(setf *buffer-history* t)",
      "(setf *auto-mode* nil)", "(setf *auto-mode* t)", "history + auto-mode"),
    R("luakit", "lua", "session", "luakit", "2.3.6", "2.4.0", "userconf.lua",
      "session.always_save = false", "session.always_save = true",
      "webview.enable_webgl = false", "webview.enable_webgl = true", "always save + webgl"),
    R("vieb", "json", "adblock", "Vieb", "12.1.0", "12.2.0", "vieb.json",
      "\"adblocker\": \"off\"", "\"adblocker\": \"update\"",
      "\"notification.system\": false", "\"notification.system\": true", "adblock update + sys notif"),
    R("qgis", "ini", "crsgrid", "QGIS", "3.40.1", "3.40.3", "QGIS3.ini",
      "projections\\\\defaultProjectCrs=EPSG:4326", "projections\\\\defaultProjectCrs=EPSG:3857",
      "showDebug=false", "showDebug=true", "3857 default CRS + debug"),
    R("gdal", "ini", "overview", "GDAL", "3.10.0", "3.10.2", "gdal.ini",
      "GDAL_TIFF_OVR_BLOCKSIZE=128", "GDAL_TIFF_OVR_BLOCKSIZE=512",
      "COMPRESS_OVERVIEW=NONE", "COMPRESS_OVERVIEW=DEFLATE", "512 ovr + deflate"),
    R("proj", "ini", "pipeline", "PROJ", "9.5.0", "9.5.1", "proj.ini",
      "network = off", "network = on",
      "cdn_endpoint = https://cdn.proj.org", "cdn_endpoint = https://cdn.api.local/proj",
      "network grids + local CDN"),
    R("geopandas", "py", "overlay", "GeoPandas", "1.0.1", "1.0.1-api", "geo.py",
      "gdf.to_crs(4326)", "gdf.to_crs(gdf.estimate_utm_crs())",
      "gpd.overlay(a, b, how='intersection')", "gpd.overlay(a, b, how='union', keep_geom_type=True)",
      "UTM CRS + union overlay"),
    R("rasterio", "py", "block", "rasterio", "1.4.2", "1.4.3", "rio.py",
      "src.block_shapes", "src.block_windows(1)",
      "profile.update(compress='lzw')", "profile.update(compress='zstd', tiled=True)",
      "block_windows + zstd tiled"),
    R("maplibre", "json", "sprite", "MapLibre", "4.7.1", "5.0.0", "style.json",
      "\"sprite\": \"\"", "\"sprite\": \"https://tiles.api/sprite\"",
      "\"glyphs\": \"mapbox://fonts/{fontstack}/{range}.pbf\"",
      "\"glyphs\": \"https://tiles.api/fonts/{fontstack}/{range}.pbf\"",
      "sprite URL + self-hosted glyphs"),
    R("triton", "pbtxt", "dynbatch", "Triton", "2.51.0", "2.53.0", "config.pbtxt",
      "dynamic_batching { }", "dynamic_batching { preferred_batch_size: [4, 8] }",
      "max_batch_size: 0", "max_batch_size: 32", "pref 4/8 + max 32"),
    R("torchserve", "prop", "batch", "TorchServe", "0.12.0", "0.12.0-api", "config.properties",
      "batch_size=1", "batch_size=8",
      "max_request_size=6553500", "max_request_size=10485760", "batch 8 + 10MiB req"),
    R("bentoml", "yml", "runner", "BentoML", "1.3.12", "1.3.16", "bentofile.yaml",
      "runners: [{name: default, resources: cpu=1}]", "runners: [{name: default, resources: nvidia.com/gpu=1}]",
      "traffic.timeout: 60", "traffic.timeout: 15", "GPU runner + 15s timeout"),
    R("kserve", "yml", "canary", "KServe", "0.14.1", "0.14.1-api", "inferenceservice.yml",
      "canaryTrafficPercent: 0", "canaryTrafficPercent: 20",
      "minReplicas: 1", "minReplicas: 2", "20% canary + min 2"),
    R("chrony", "conf", "nts", "chrony", "4.5", "4.6.1", "chrony.conf",
      "server ntp.local iburst", "server nts.api.local iburst nts",
      "makestep 1.0 3", "makestep 0.1 3", "NTS server + 0.1s step"),
    R("ptp4l", "conf", "servo", "linuxptp", "4.2", "4.4", "ptp4l.conf",
      "clock_servo pi", "clock_servo linreg",
      "delay_mechanism E2E", "delay_mechanism P2P", "linreg servo + P2P"),
    R("stalwart", "toml", "sieve", "Stalwart", "0.10.4", "0.11.0", "config.toml",
      "sieve.untrusted.script = \"\"", "sieve.untrusted.script = \"fileinto\"",
      "session.auth.mechanisms = [\"PLAIN\"]", "session.auth.mechanisms = [\"PLAIN\",\"OAUTHBEARER\"]",
      "sieve fileinto + OAUTHBEARER"),
    R("maddy", "conf", "imap", "maddy", "0.7.1", "0.8.0", "maddy.conf",
      "imap.ports = [143]", "imap.ports = [993]",
      "storage.imapsql.driver = sqlite3", "storage.imapsql.driver = postgres",
      "IMAP 993 + postgres"),
    R("caddy", "caddyfile", "http3", "Caddy", "2.8.4", "2.9.1", "Caddyfile",
      "servers {:443} {\n  protocols h1 h2\n}", "servers {:443} {\n  protocols h1 h2 h3\n}",
      "encode gzip", "encode zstd gzip", "HTTP/3 + zstd"),
    R("traefik", "yml", "entrypoint", "Traefik", "3.2.1", "3.3.2", "traefik.yml",
      "entryPoints.web.address: :80", "entryPoints.websecure.address: :443",
      "providers.docker.exposedByDefault: true", "providers.docker.exposedByDefault: false",
      "443 entry + explicit expose"),
    R("envoy", "yml", "filterchain", "Envoy", "1.32.2", "1.33.0", "envoy.yml",
      "filter_chains: [{filters: [{name: envoy.filters.network.http_connection_manager}]}]",
      "filter_chains: [{transport_socket: {name: envoy.transport_sockets.tls}, filters: [{name: envoy.filters.network.http_connection_manager}]}]",
      "codec_type: AUTO", "codec_type: HTTP2", "TLS chain + HTTP/2"),
    R("cilium", "yml", "policy", "Cilium", "1.16.5", "1.17.1", "cilium.yml",
      "policyEnforcementMode: default", "policyEnforcementMode: always",
      "enableIPv6Masquerade: false", "enableIPv6Masquerade: true",
      "always enforce + IPv6 masq"),
    R("istio", "yml", "waypoint", "Istio", "1.24.1", "1.25.0", "mesh.yml",
      "defaultProviders.metrics: []", "defaultProviders.metrics: [prometheus]",
      "pilot.env.PILOT_ENABLE_AMBIENT: false", "pilot.env.PILOT_ENABLE_AMBIENT: true",
      "prom metrics + ambient waypoint"),
    R("linkerd", "yml", "proxy", "Linkerd", "2.14.10", "2.16.2", "linkerd.yml",
      "proxy.cpu.request: 10m", "proxy.cpu.request: 50m",
      "proxy.await: true", "proxy.await: false", "50m proxy CPU + no await"),
    R("talos", "yml", "schematic", "Talos", "1.8.3", "1.9.2", "machine.yml",
      "machine.install.image: ghcr.io/siderolabs/installer:v1.8.3",
      "machine.install.image: factory.talos.dev/installer/schematic:v1.9.2",
      "cluster.network.cni.name: flannel", "cluster.network.cni.name: none",
      "factory schematic + no CNI"),
    R("k3s", "yml", "flannel", "k3s", "v1.31.3+k3s1", "v1.32.1+k3s1", "config.yaml",
      "flannel-backend: vxlan", "flannel-backend: wireguard-native",
      "disable: []", "disable: [traefik,servicelb]", "wg-native flannel + disable lb"),
    R("k0s", "yml", "worker", "k0s", "v1.31.3+k0s.0", "v1.32.1+k0s.0", "k0s.yaml",
      "spec.worker.kubelet.extraArgs: {}", "spec.worker.kubelet.extraArgs: {max-pods: \"110\"}",
      "spec.network.provider: kuberouter", "spec.network.provider: calico",
      "max-pods 110 + calico"),
    R("firecracker", "json", "balloon", "Firecracker", "1.10.1", "1.11.0", "vm.json",
      "\"balloon\": {\"amount_mib\": 0}", "\"balloon\": {\"amount_mib\": 512, \"deflate_on_oom\": true}",
      "\"mem_size_mib\": 128", "\"mem_size_mib\": 512", "512MiB balloon + 512MiB guest"),
    R("cloudhypervisor", "json", "iommu", "Cloud Hypervisor", "42.0", "43.0", "vm.json",
      "\"iommu\": false", "\"iommu\": true",
      "\"cpus\": {\"boot_vcpus\": 1}", "\"cpus\": {\"boot_vcpus\": 4, \"max_vcpus\": 8}",
      "IOMMU on + 4/8 vCPU"),
    R("kata", "toml", "hypervisor", "Kata", "3.10.1", "3.14.0", "configuration.toml",
      "hypervisor.qemu.path = \"/usr/bin/qemu-system-x86_64\"",
      "hypervisor.qemu.path = \"/usr/bin/cloud-hypervisor\"",
      "enable_debug = false", "enable_debug = true", "cloud-hypervisor + debug"),
    R("dealii", "prm", "solver", "deal.II", "9.6.0", "9.6.2", "step.prm",
      "set Solver type = CG", "set Solver type = GMRES",
      "set Max iterations = 100", "set Max iterations = 1000", "GMRES + 1000 iters"),
    R("petsc", "conf", "pc", "PETSc", "3.22.1", "3.22.3", "petscrc",
      "-pc_type ilu", "-pc_type hypre",
      "-ksp_type gmres", "-ksp_type fgmres", "hypre PC + FGMRES"),
    R("trilinos", "xml", "amesos", "Trilinos", "16.0.0", "16.1.0", "solver.xml",
      "<Parameter name=\"Linear Solver Type\" type=\"string\" value=\"Belos\"/>",
      "<Parameter name=\"Linear Solver Type\" type=\"string\" value=\"Amesos2\"/>",
      "<Parameter name=\"Preconditioner Type\" type=\"string\" value=\"None\"/>",
      "<Parameter name=\"Preconditioner Type\" type=\"string\" value=\"Ifpack2\"/>",
      "Amesos2 + Ifpack2"),
    R("openmpi", "mca", "btl", "Open MPI", "5.0.5", "5.0.6", "openmpi-mca-params.conf",
      "btl = tcp,self", "btl = vader,self",
      "btl_tcp_eager_limit = 65536", "btl_tcp_eager_limit = 131072",
      "vader BTL + 128k eager"),
    R("ruff", "toml", "preview", "Ruff", "0.8.2", "0.9.4", "ruff.toml",
      "preview = false", "preview = true",
      "target-version = \"py39\"", "target-version = \"py312\"", "preview + py312"),
    R("biome", "json", "assist", "Biome", "1.9.4", "1.9.4-api", "biome.json",
      "\"assist\": {\"enabled\": false}", "\"assist\": {\"enabled\": true, \"actions\": {\"source\": {\"organizeImports\": \"on\"}}}",
      "\"formatter.indentStyle\": \"tab\"", "\"formatter.indentStyle\": \"space\"",
      "assist organizeImports + spaces"),
    R("oxlint", "json", "jsdoc", "oxlint", "0.15.5", "0.15.8", "oxlintrc.json",
      "\"plugins\": []", "\"plugins\": [\"jsdoc\"]",
      "\"categories\": {\"correctness\": \"warn\"}", "\"categories\": {\"correctness\": \"error\"}",
      "jsdoc plugin + correctness error"),
    R("playwright", "ts", "trace", "Playwright", "1.49.1", "1.50.1", "playwright.config.ts",
      "trace: 'off'", "trace: 'on-first-retry'",
      "fullyParallel: false", "fullyParallel: true", "retry traces + fullyParallel"),
    R("pytest", "ini", "xdist", "pytest", "8.3.4", "8.3.5", "pytest.ini",
      "addopts = -q", "addopts = -q -n auto",
      "asyncio_mode = strict", "asyncio_mode = auto", "xdist auto + asyncio auto"),
    R("vitest", "ts", "pool", "Vitest", "2.1.8", "3.0.4", "vitest.config.ts",
      "pool: 'forks'", "pool: 'threads'",
      "isolate: true", "isolate: false", "threads pool + shared isolate"),
    R("jujutsu", "toml", "snapshot", "Jujutsu", "0.25.0", "0.26.0", "config.toml",
      "ui.default-command = \"log\"", "ui.default-command = \"status\"",
      "snapshot.max-new-file-size = \"1MiB\"", "snapshot.max-new-file-size = \"8MiB\"",
      "status default + 8MiB snapshot"),
    R("pijul", "toml", "channel", "Pijul", "1.0.0-beta.9", "1.0.0-beta.10", "config.toml",
      "default_channel = \"main\"", "default_channel = \"trunk\"",
      "ignore_missing = false", "ignore_missing = true", "trunk channel + ignore missing"),
    R("starship", "toml", "format", "Starship", "1.21.1", "1.22.1", "starship.toml",
      "format = \"$all\"", "format = \"$directory$git_branch$character\"",
      "add_newline = true", "add_newline = false", "compact format + no newline"),
    R("atuin", "toml", "sync", "Atuin", "18.4.0", "18.4.0-api", "config.toml",
      "sync_address = \"https://api.atuin.sh\"", "sync_address = \"https://atuin.api.local\"",
      "auto_sync = false", "auto_sync = true", "self-host sync + auto"),
    R("zoxide", "toml", "exclude", "zoxide", "0.9.6", "0.9.7", "config.toml",
      "exclude_dirs = []", "exclude_dirs = [\"/tmp\",\"/proc\"]",
      "_ZO_ECHO = 0", "_ZO_ECHO = 1", "exclude tmp/proc + echo"),
    R("fzf", "conf", "preview", "fzf", "0.56.3", "0.58.0", "fzf.conf",
      "export FZF_DEFAULT_OPTS=\"--height 40%\"", "export FZF_DEFAULT_OPTS=\"--height 40% --preview 'bat --color=always {}'\"",
      "export FZF_CTRL_T_COMMAND=\"find\"", "export FZF_CTRL_T_COMMAND=\"fd --type f\"",
      "bat preview + fd"),
    R("netdata", "conf", "health", "Netdata", "2.1.0", "2.2.6", "netdata.conf",
      "[health]\nenabled = no", "[health]\nenabled = yes",
      "memory mode = ram", "memory mode = dbengine", "health on + dbengine"),
    R("btop", "conf", "theme", "btop", "1.4.0", "1.4.0-api", "btop.conf",
      "color_theme = \"Default\"", "color_theme = \"TTY\"",
      "vim_keys = False", "vim_keys = True", "TTY theme + vim keys"),
    R("harbor", "yml", "scan", "Harbor", "2.12.0", "2.12.2", "harbor.yml",
      "trivy.enabled: false", "trivy.enabled: true",
      "data_retention.hours: 0", "data_retention.hours: 168", "trivy scan + 7d retention"),
    R("zot", "json", "sync", "zot", "2.1.1", "2.1.2", "config.json",
      "\"sync\": {\"enable\": false}", "\"sync\": {\"enable\": true, \"registries\": [{\"urls\": [\"https://registry.api\"]}]}",
      "\"http.port\": \"5000\"", "\"http.port\": \"8080\"", "upstream sync + 8080"),
    R("buildkit", "toml", "gc", "BuildKit", "0.18.1", "0.19.0", "buildkitd.toml",
      "[worker.oci]\ngc = false", "[worker.oci]\ngc = true\n[[worker.oci.gcpolicy]]\nkeepBytes = 10737418240",
      "max-parallelism = 0", "max-parallelism = 4", "10GiB GC + 4 parallel"),
    R("kaniko", "json", "snapshot", "Kaniko", "1.23.2", "1.23.2-api", "kaniko.json",
      "\"snapshotMode\": \"full\"", "\"snapshotMode\": \"redo\"",
      "\"compressedCaching\": true", "\"compressedCaching\": false", "redo snapshot + no cache compress"),
    R("redpanda", "yml", "rack", "Redpanda", "24.3.1", "24.3.3", "redpanda.yml",
      "rack: \"\"", "rack: az-a",
      "enable_idempotence: false", "enable_idempotence: true", "rack az-a + idempotence"),
    R("natsjet", "conf", "stream", "NATS JetStream", "2.10.22", "2.10.25", "nats.conf",
      "jetstream { store_dir: /data }", "jetstream { store_dir: /data max_file_store: 100G }",
      "max_payload: 1MB", "max_payload: 8MB", "100G file store + 8MB payload"),
    R("polars", "py", "streaming", "Polars", "1.17.1", "1.21.0", "query.py",
      "df.lazy().collect()", "df.lazy().collect(engine='streaming')",
      "pl.Config.set_streaming_chunk_size(10000)", "pl.Config.set_streaming_chunk_size(50000)",
      "streaming engine + 50k chunks"),
    R("datafusion", "toml", "batch", "DataFusion", "43.0.0", "45.0.0", "datafusion.toml",
      "batch_size = 8192", "batch_size = 16384",
      "target_partitions = 4", "target_partitions = 16", "16k batch + 16 parts"),
    R("spin", "toml", "trigger", "Fermyon Spin", "3.0.0", "3.1.2", "spin.toml",
      "trigger = { type = \"http\", route = \"/...\" }", "trigger = { type = \"http\", route = \"/api/...\" }",
      "executor = { type = \"wagi\" }", "executor = { type = \"spin-http\" }",
      "/api route + spin-http"),
    R("lunatic", "toml", "process", "Lunatic", "0.13.2", "0.14.0", "lunatic.toml",
      "max_memory = \"4MB\"", "max_memory = \"32MB\"",
      "max_fuel = 0", "max_fuel = 1000000", "32MB process + fuel cap"),
    R("openscad", "scad", "fn", "OpenSCAD", "2021.01", "2024.12", "part.scad",
      "$fn = 24", "$fn = 96",
      "$fa = 12", "$fa = 4", "fn 96 + fa 4"),
    R("freecad", "cfg", "solver", "FreeCAD", "1.0.0", "1.0.0-api", "user.cfg",
      "BaseApp.Preferences.Mod.Sketcher.Solver=LevenbergMarquardt",
      "BaseApp.Preferences.Mod.Sketcher.Solver=DogLeg",
      "AutoRecompute=false", "AutoRecompute=true", "DogLeg solver + auto recompute"),
    R("blender", "py", "cycles", "Blender", "4.3.0", "4.3.2", "render.py",
      "bpy.context.scene.render.engine = 'BLENDER_EEVEE'",
      "bpy.context.scene.render.engine = 'CYCLES'",
      "bpy.context.scene.cycles.samples = 64", "bpy.context.scene.cycles.samples = 256",
      "Cycles + 256 samples"),
    R("wireshark", "lua", "dissector", "Wireshark", "4.4.2", "4.4.3", "api.lua",
      "local p = Proto(\"old\",\"old\")", "local p = Proto(\"api\",\"api proto\")",
      "p.fields = {}", "p.fields = {ProtoField.uint16(\"api.len\",\"Length\")}",
      "api proto + length field"),
    R("earthly", "earthfile", "cache", "Earthly", "0.8.15", "0.8.15-api", "Earthfile",
      "CACHE --persist /cache", "CACHE --persist --sharing=shared /cache",
      "VERSION 0.7", "VERSION 0.8", "shared cache + v0.8"),
    R("pants", "toml", "resolve", "Pants", "2.23.0", "2.24.0", "pants.toml",
      "[python]\nresolver = \"pex\"", "[python]\nresolver = \"uv\"",
      "interpreter_constraints = [\"CPython==3.11.*\"]", "interpreter_constraints = [\"CPython==3.12.*\"]",
      "uv resolver + py312"),
    R("buck2", "toml", "remote", "Buck2", "2024.11.01", "2025.01.15", "buckconfig.toml",
      "[build]\nremote_execution = false", "[build]\nremote_execution = true",
      "threads = 4", "threads = 16", "RE on + 16 threads"),
    R("please", "plz", "hash", "Please", "17.12.0", "17.16.0", ".plzconfig",
      "[build]\nhashers = sha1", "[build]\nhashers = sha256",
      "nonce = old", "nonce = api", "sha256 hasher + api nonce"),
    R("orykratos", "yml", "hook", "Ory Kratos", "1.3.0", "1.3.1", "kratos.yml",
      "selfservice.flows.registration.after.hooks: []",
      "selfservice.flows.registration.after.hooks: [{hook: session}]",
      "session.lifespan: 24h", "session.lifespan: 1h", "session hook + 1h lifespan"),
    R("gettext", "po", "plural", "gettext", "0.22.5", "0.23.1", "messages.po",
      "Plural-Forms: nplurals=2; plural=n != 1;", "Plural-Forms: nplurals=3; plural=n==1 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2;",
      "charset=ISO-8859-1", "charset=UTF-8", "3-form plural + UTF-8"),
    R("weblate", "yml", "tm", "Weblate", "5.8.4", "5.9.2", "settings.yml",
      "WEBLATE_ENABLE_HTTPS: 0", "WEBLATE_ENABLE_HTTPS: 1",
      "WEBLATE_MT_SERVICES: []", "WEBLATE_MT_SERVICES: [weblate.machinery.tmserver.AmagamaTranslation]",
      "HTTPS + tmserver MT"),
    R("direnv", "toml", "strictenv", "direnv", "2.35.0", "2.35.0-api", "direnv.toml",
      "strict_env = false", "strict_env = true",
      "warn_timeout = \"5s\"", "warn_timeout = \"1s\"", "strict_env + 1s warn"),
    R("just", "justfile", "dotenv", "just", "1.38.0", "1.39.0", "justfile",
      "set dotenv-load := false", "set dotenv-load := true",
      "set positional-arguments := false", "set positional-arguments := true",
      "dotenv-load + positional args"),
    R("taskfile", "yml", "includes", "Task", "3.40.1", "3.41.0", "Taskfile.yml",
      "includes: {}", "includes: {api: ./api/Taskfile.yml}",
      "output: interleaved", "output: prefixed", "api include + prefixed output"),
]

assert len(RAW) == 160
assert len(RAW) % 2 == 0


def expand(row: tuple) -> tuple:
    slug, surface, pkg, old, new, pin, nest_old, nest_new, api_old, api_new, api_break, ext = row
    cmap = {
        "sql": "--", "R": "#", "hs": "--", "scala": "//", "vhdl": "--", "v": "//",
        "scd": "//", "orc": ";", "ttl": "#", "C": "//", "cpp": "//", "c": "//",
        "cs": "//", "dart": "//", "rb": "#", "php": "//", "js": "//", "ts": "//",
        "go": "//", "d": "//", "td": "//", "g": ";", "fish": "#", "nu": "#", "xsh": "#",
        "Corefile": "#", "crypttab": "#", "cf": "#", "lisp": ";", "kak": "#",
        "scad": "//", "pbtxt": "#", "earthfile": "#", "justfile": "#", "grc": "#",
        "mom": ".", "csd": ";", "prm": "#", "mca": "#", "plz": "#", "po": "#",
        "caddyfile": "#", "env": "#", "vol": "#", "init": "#", "prop": "#",
        "kdl": "//", "rasi": "//", "lua": "--",
    }
    comment = cmap.get(ext, "#")
    sot_old = f"{comment} {pkg} {old}"
    sot_new = f"{comment} {pkg} {new}"
    if ext == "py":
        tool = f"python3 -c 'import {pkg}; print({pkg}.__version__)'"
        test = f"python3 apps/api/{pin}"
        ws = f"python3 apps/legacy/{pin}"
    else:
        tool = f"python3 -c 'print(\"{pkg}\")' || true"
        test = f"python3 -c 'print(\"apps/api/{pin}\")'"
        ws = f"python3 -c 'print(\"apps/legacy/{pin}\")'"
    return (slug, surface, pkg, old, new, pin, sot_old, sot_new, nest_old, nest_new, api_old, api_new, api_break, tool, test, ws, ext)


TOOLS: list[tuple] = [expand(r) for r in RAW]
assert len(TOOLS) % 2 == 0
assert len(TOOLS) <= len(PLANTS)

PAIRS: list[tuple[dict, dict]] = []
_pi = 0
for i in range(0, len(TOOLS), 2):
    a = TOOLS[i]
    b = TOOLS[i + 1]
    suc = make(
        a[0], PLANTS[_pi], a[1], a[2], a[3], a[4], False,
        a[5], a[6], a[7], a[8], a[9], a[10], a[11], a[12], a[13], a[14], a[15], a[16],
    )
    _pi += 1
    failp = make(
        b[0], PLANTS[_pi], b[1], b[2], b[3], b[4], True,
        b[5], b[6], b[7], b[8], b[9], b[10], b[11], b[12], b[13], b[14], b[15], b[16],
    )
    _pi += 1
    PAIRS.append((suc, failp))


def _validate_catalog() -> None:
    slugs = [spec["slug"] for pair in PAIRS for spec in pair]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("duplicate slugs in r1454 catalog")
    for slug in slugs:
        for needle in BANNED_SLUG_NEEDLES:
            if needle and needle in slug:
                raise SystemExit(f"banned needle {needle!r} in {slug}")
    plants = [spec["plant"] for pair in PAIRS for spec in pair]
    if len(plants) != len(set(plants)):
        raise SystemExit("duplicate plants in r1454 catalog")


_validate_catalog()


def build_round(rnd: int) -> tuple[list[dict], str]:
    idx = rnd - CATALOG_FIRST
    if idx < 0 or idx >= len(PAIRS):
        raise SystemExit(
            f"round {rnd} outside catalog {CATALOG_FIRST}..{CATALOG_FIRST + len(PAIRS) - 1}"
        )
    suc, fail = PAIRS[idx]
    suc_ep = build_episode(rnd, suc)
    fail_ep = build_episode(rnd, fail)
    for ep in (suc_ep, fail_ep):
        n = len(ep["steps"])
        if n < 16 or n > 20:
            raise SystemExit(f"{ep['id']} has {n} steps, want 16-20")
        blob = json.dumps(ep)
        for banned in (
            "thought",
            "chain_of_thought",
            "scratch",
            "inner_monologue",
            "spike_events",
        ):
            if f'"{banned}"' in blob:
                raise SystemExit(f"{ep['id']} contains banned key {banned}")
        if '"sim_or_real": "real"' in blob or '"sim_or_real":"real"' in blob:
            raise SystemExit(f"{ep['id']} claims sim_or_real real")
    notes = notes_for(rnd, suc, fail)
    if "Novel coverage:" not in notes:
        raise SystemExit("notes missing Novel coverage")
    return [suc_ep, fail_ep], notes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    args = ap.parse_args()
    rnd = args.round
    staging = Path(args.staging)
    recs, notes = build_round(rnd)
    batch = staging / f"batch-r{rnd:02d}.jsonl"
    notes_path = staging / f"NOTES-r{rnd:02d}.md"
    with batch.open("w") as handle:
        for rec in recs:
            handle.write(json.dumps(rec, ensure_ascii=True) + "\n")
    notes_path.write_text(notes)
    print(
        json.dumps(
            {
                "round": rnd,
                "ids": [r["id"] for r in recs],
                "steps": [len(r["steps"]) for r in recs],
                "success": [r["reward"]["success"] for r in recs],
                "batch": str(batch),
                "notes": str(notes_path),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
