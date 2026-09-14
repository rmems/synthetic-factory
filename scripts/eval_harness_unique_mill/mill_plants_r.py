"""Unique eval-harness leftover plants r473+. Compact leftover table."""

from mill_plants import PAIRS
from mill_plants_p import pair

ROWS = [
    ("mimir-ruler-stale", "mimir-eval", "victoriametrics-rule-stale", "vmrule-eval",
     "dual-hold-10", "rain-hold-16", "mimir ruler leftover", "victoria rule leftover", "mon"),
    ("influx-bucket-stale", "influx-eval", "timescale-view-stale", "timescale-eval",
     "flash-hold-17", "promo-hold-16", "influx bucket leftover", "timescale view leftover", "mon"),
    ("graphite-whisper-stale", "graphite-eval", "collectd-rrd-stale", "collectd-eval",
     "gift-hold-16", "bundle-hold-15", "graphite whisper leftover", "collectd rrd leftover", "mon"),
    ("telegraf-conf-stale", "telegraf-eval", "fluentd-match-stale", "fluentd-eval",
     "loyalty-hold-14", "cancel-hold-14", "telegraf conf leftover", "fluentd match leftover", "logs"),
    ("fluentbit-parser-stale", "fluentbit-eval", "logstash-pipe-stale", "logstash-eval",
     "tax-hold-13", "sla-hold-12", "fluentbit parser leftover", "logstash pipe leftover", "logs"),
    ("filebeat-input-stale", "filebeat-eval", "journald-unit-stale", "journald-eval",
     "membership-hold-11", "after-hold-13", "filebeat input leftover", "journald unit leftover", "logs"),
    ("rsyslog-filter-stale", "rsyslog-eval", "syslogng-filter-stale", "syslogng-eval",
     "sku-hold-9", "rain-void-11", "rsyslog filter leftover", "syslog-ng filter leftover", "logs"),
    ("vector-remap-stale", "vectorremap-eval", "alloy-relabel-stale", "alloy-eval",
     "flash-void-10", "promo-void-11", "vector remap leftover", "alloy relabel leftover", "logs"),
]

for i, row in enumerate(ROWS):
    PAIRS.append(pair(*row[:8], i * 2, row[8]))
