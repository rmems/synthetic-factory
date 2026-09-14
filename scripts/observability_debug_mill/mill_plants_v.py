"""Observability leftover leftover leftover plants r500-r515.

BAN r163-r400 clones, r496-r499 knob twins (grafana timeout 1s, loki RF 0,
tempo max_traces 1, mimir remote_timeout 1ms). Not a 1ms integer knob.
Not r385 DD env-tag / ignore_autodiscovery_tags. Not Sentry ignore-errors.
Not r386 SENTRY_TRACES_SAMPLE_RATE. Not Grafana dataproxy timeout.
Leftover leftover leftover lie: wrong dashboard, dropped label, silent drop.
"""

from mill_plants_t import _leftover_pair

MORE = []
ROUND_PAIRS = {}


def _emit(round_n, **kwargs):
    dest = []
    _leftover_pair(n=str(round_n), dest=dest, **kwargs)
    MORE.extend(dest)
    ROUND_PAIRS[round_n] = dest[0]


# 1 Datadog leftover leftover leftover vs leftover (not r385 env-tag)
_emit(
    500,
    kind="grafana",
    ok_slug="dd-log-pipeline-service-remap-leftover",
    bad_slug="dd-logpipe-raise-apm-not-remap",
    ok_svc="jet-bridge-dd-svc",
    bad_svc="ramp-belt-dd-svc",
    ok_dash="jbrg-ddpipe-500",
    bad_dash="rbelt-ddpipe-apm",
    panel="DD log volume by service",
    metric="",
    needle="gate_jam",
    lie=(
        "Datadog log pipeline leftover remaps service jet-bridge-dd-svc to "
        "legacy-bridge so Grafana dashboard jbrg-ddpipe-500 is the wrong "
        "dashboard while /intake still 202"
    ),
    bad_lie=(
        "Raising APM max_traces_per_second does not bind Grafana to logs "
        "silently remapped by leftover Datadog pipeline service remap"
    ),
    false_lead="APM max_traces_per_second leftover",
    avoided="r385 ignore_autodiscovery_tags; r190 DD UST; r163 tid128",
    this_is="DD leftover leftover leftover pipeline remaps service so wrong dashboard",
    ticket="OBS-7601",
    knob=".logs_config.processing_rules[].replace",
    old='replace: "legacy-bridge"',
    new='replace: "jet-bridge-dd-svc"',
    wrong_knob=".apm_config.max_traces_per_second",
    wrong_old="max_traces_per_second: 10",
    wrong_new="max_traces_per_second: 500",
    wrong2_old="ignore_autodiscovery_tags: true",
    wrong2_new="ignore_autodiscovery_tags: false",
    reload="grafana",
    config_path="datadog/jbrg-apm.yaml",
    lie_path="datadog/jbrg-logpipe.yaml",
    bad_config="datadog/rbelt-apm.yaml",
    bad_lie_path="datadog/rbelt-logpipe.yaml",
)

# 2 Sentry leftover leftover leftover vs leftover (not ignore-errors)
_emit(
    501,
    kind="grafana",
    ok_slug="sentry-inbound-filter-txn-drop-leftover",
    bad_slug="sentry-inbfilt-raise-quota-not-filter",
    ok_svc="cargo-net-sn-svc",
    bad_svc="hold-door-sn-svc",
    ok_dash="cnet-snfilt-501",
    bad_dash="hdoor-snfilt-quota",
    panel="Sentry transactions",
    metric="",
    needle="txn_drop",
    lie=(
        "Sentry inbound-filters leftover drops transaction name cargo.checkout "
        "so Grafana dashboard cnet-snfilt-501 is empty while /api/0/envelope/ still 200"
    ),
    bad_lie=(
        "Raising Sentry org quota does not restore transactions silently dropped "
        "by leftover inbound-filters on cargo.checkout"
    ),
    false_lead="Sentry org quota leftover",
    avoided="Sentry ignore-errors; r386 SENTRY_TRACES_SAMPLE_RATE; r184 Sentry vs Tempo",
    this_is="Sentry leftover leftover leftover inbound-filter silent drop",
    ticket="OBS-7602",
    knob=".filters.inbound.transactions",
    old="transactions: [cargo.checkout]",
    new="transactions: []",
    wrong_knob=".quotas.event_retention",
    wrong_old="event_retention: 1",
    wrong_new="event_retention: 90",
    wrong2_old="ignoreErrors: [TimeoutError]",
    wrong2_new="ignoreErrors: []",
    reload="grafana",
    config_path="sentry/cnet-quota.yaml",
    lie_path="sentry/cnet-inbound.yaml",
    bad_config="sentry/hdoor-quota.yaml",
    bad_lie_path="sentry/hdoor-inbound.yaml",
)

# 3 Honeycomb leftover leftover leftover vs leftover
_emit(
    502,
    kind="grafana",
    ok_slug="honeycomb-dataset-alias-wrong-dash-leftover",
    bad_slug="hny-alias-raise-ingest-not-dataset",
    ok_svc="tug-hitch-hc-svc",
    bad_svc="pushback-hc-svc",
    ok_dash="thitch-hcalias-502",
    bad_dash="pback-hcalias-ingest",
    panel="Honeycomb traces",
    metric="",
    needle="hitch_slip",
    lie=(
        "Honeycomb dataset leftover alias maps tug-hitch-hc-svc into sandbox-traces "
        "so Grafana dashboard thitch-hcalias-502 is the wrong dashboard while Libhoney still 202"
    ),
    bad_lie=(
        "Raising Honeycomb ingest rate does not bind Grafana to traces sitting in "
        "leftover leftover leftover dataset alias sandbox-traces"
    ),
    false_lead="Honeycomb ingest rate leftover",
    avoided="r386 Honeycomb ingest; r189 ClickHouse SQL vs Tempo",
    this_is="Honeycomb leftover leftover leftover dataset alias wrong dashboard",
    ticket="OBS-7603",
    knob=".datasets.alias",
    old="alias: sandbox-traces",
    new="alias: tug-hitch-hc-svc",
    wrong_knob=".ingest.max_events_per_second",
    wrong_old="max_events_per_second: 50",
    wrong_new="max_events_per_second: 5000",
    wrong2_old="sample_rate: 100",
    wrong2_new="sample_rate: 1",
    reload="grafana",
    config_path="honeycomb/thitch-ingest.yaml",
    lie_path="honeycomb/thitch-alias.yaml",
    bad_config="honeycomb/pback-ingest.yaml",
    bad_lie_path="honeycomb/pback-alias.yaml",
)

# 4 Grafana leftover leftover leftover vs leftover (not dataproxy timeout)
_emit(
    503,
    kind="grafana",
    ok_slug="grafana-folder-acl-wrong-uid-leftover",
    bad_slug="graf-acl-raise-dpto-not-folder",
    ok_svc="chock-lock-gf-svc",
    bad_svc="cone-cart-gf-svc",
    ok_dash="chock-gfacl-503",
    bad_dash="cone-gfacl-dpto",
    panel="folder pages",
    metric="",
    needle="chock_loose",
    lie=(
        "Grafana folder ACL leftover binds Viewer to uid chock-archive so dashboard "
        "chock-gfacl-503 is the wrong dashboard while the live uid still has panels"
    ),
    bad_lie=(
        "Raising dataproxy.timeout does not unhide the live dashboard when leftover "
        "folder ACL still points Grafana at chock-archive"
    ),
    false_lead="dataproxy.timeout leftover",
    avoided="r496 dataproxy.timeout 1s; r216 public dashboard; r109 provisioned uid",
    this_is="Grafana leftover leftover leftover folder ACL wrong dashboard uid",
    ticket="OBS-7604",
    knob=".folders.acl.uid",
    old="uid: chock-archive",
    new="uid: chock-gfacl-503",
    wrong_knob=".dataproxy.timeout",
    wrong_old="timeout = 30",
    wrong_new="timeout = 120",
    wrong2_old="keep_alive_seconds = 0",
    wrong2_new="keep_alive_seconds = 30",
    reload="grafana",
    config_path="grafana/chock-dpto.ini",
    lie_path="grafana/chock-acl.yaml",
    bad_config="grafana/cone-dpto.ini",
    bad_lie_path="grafana/cone-acl.yaml",
)

# 5 Prometheus leftover leftover leftover vs leftover
_emit(
    504,
    kind="prom",
    ok_slug="prom-honor-labels-drop-job-leftover",
    bad_slug="prom-hlab-raise-scrape-not-honor",
    ok_svc="gpu-tug-pm-svc",
    bad_svc="belt-loader-pm-svc",
    ok_dash="gtug-pmhlab-504",
    bad_dash="bload-pmhlab-scrape",
    panel="tug C",
    metric="gpu_tug_celsius",
    needle="",
    lie=(
        "Prometheus leftover honor_labels true plus a colliding job label from the "
        "target so Grafana {job=gpu-tug-pm-svc} is empty while /metrics still shows 11"
    ),
    bad_lie=(
        "Raising scrape_timeout does not restore the dropped job label when leftover "
        "honor_labels still lets the target overwrite job"
    ),
    false_lead="scrape_timeout leftover",
    avoided="r370 query.timeout 1ms; r233 scrape timeout; r177 alloy relabel",
    this_is="Prometheus leftover leftover leftover honor_labels dropped job label",
    ticket="OBS-7605",
    knob=".scrape_configs[].honor_labels",
    old="honor_labels: true",
    new="honor_labels: false",
    wrong_knob=".scrape_configs[].scrape_timeout",
    wrong_old="scrape_timeout: 10s",
    wrong_new="scrape_timeout: 60s",
    wrong2_old="scrape_interval: 15s",
    wrong2_new="scrape_interval: 15s",
    reload="prom-scrape",
    config_path="prom/gtug-scrape.yaml",
    lie_path="prom/gtug-honor.yaml",
    bad_config="prom/bload-scrape.yaml",
    bad_lie_path="prom/bload-honor.yaml",
)

# 6 Alertmanager leftover leftover leftover vs leftover
_emit(
    505,
    kind="grafana",
    ok_slug="am-continue-wrong-receiver-leftover",
    bad_slug="am-cont-raise-groupwait-not-continue",
    ok_svc="fuel-hydrant-am-svc",
    bad_svc="defuel-cart-am-svc",
    ok_dash="fhyd-amcont-505",
    bad_dash="dcart-amcont-gwait",
    panel="pages last 1h",
    metric="",
    needle="fuel_spill",
    lie=(
        "Alertmanager leftover continue: true after a catch-all route so Grafana "
        "dashboard fhyd-amcont-505 pages the wrong receiver while the match still fires"
    ),
    bad_lie=(
        "Raising group_wait does not stop leftover leftover leftover continue from "
        "duplicating pages onto the catch-all receiver"
    ),
    false_lead="group_wait leftover",
    avoided="r159 IRM vs AM silence; AM inhibit; r109-r158 AM inhibit",
    this_is="Alertmanager leftover leftover leftover continue wrong dashboard/receiver",
    ticket="OBS-7606",
    knob=".route.routes[].continue",
    old="continue: true",
    new="continue: false",
    wrong_knob=".route.group_wait",
    wrong_old="group_wait: 30s",
    wrong_new="group_wait: 5m",
    wrong2_old="group_interval: 5s",
    wrong2_new="group_interval: 5m",
    reload="grafana",
    config_path="alertmanager/fhyd-gwait.yaml",
    lie_path="alertmanager/fhyd-continue.yaml",
    bad_config="alertmanager/dcart-gwait.yaml",
    bad_lie_path="alertmanager/dcart-continue.yaml",
)

# 7 PagerDuty leftover leftover leftover vs leftover
_emit(
    506,
    kind="grafana",
    ok_slug="pd-event-orch-severity-drop-leftover",
    bad_slug="pd-orch-raise-timeout-not-sev",
    ok_svc="deice-boom-pd-svc",
    bad_svc="glycol-tank-pd-svc",
    ok_dash="dboom-pdorch-506",
    bad_dash="gtank-pdorch-to",
    panel="PD incidents",
    metric="",
    needle="boom_jam",
    lie=(
        "PagerDuty event orchestration leftover drops severity=critical so Grafana "
        "dashboard dboom-pdorch-506 is empty while Events API v2 still 202"
    ),
    bad_lie=(
        "Raising PD HTTP timeout does not page incidents silently dropped by leftover "
        "event-orchestration severity filter"
    ),
    false_lead="PagerDuty HTTP timeout leftover",
    avoided="r159 IRM heartbeat; Grafana Incident vs IRM",
    this_is="PagerDuty leftover leftover leftover orchestration silent drop",
    ticket="OBS-7607",
    knob=".event_orchestration.severity_filter",
    old="severity_filter: [warning, info]",
    new="severity_filter: [critical, warning, info]",
    wrong_knob=".http.timeout_seconds",
    wrong_old="timeout_seconds: 30",
    wrong_new="timeout_seconds: 120",
    wrong2_old="retry_timeout: 5",
    wrong2_new="retry_timeout: 60",
    reload="grafana",
    config_path="pagerduty/dboom-http.yaml",
    lie_path="pagerduty/dboom-orch.yaml",
    bad_config="pagerduty/gtank-http.yaml",
    bad_lie_path="pagerduty/gtank-orch.yaml",
)

# 8 Opsgenie leftover leftover leftover vs leftover
_emit(
    507,
    kind="grafana",
    ok_slug="opsgenie-alias-collision-silent-drop-leftover",
    bad_slug="og-alias-raise-heartbeat-not-alias",
    ok_svc="towbar-og-svc",
    bad_svc="chock-og-svc",
    ok_dash="tbar-ogalias-507",
    bad_dash="chock-ogalias-hb",
    panel="Opsgenie alerts",
    metric="",
    needle="tow_fail",
    lie=(
        "Opsgenie leftover alias template {{.GroupLabels.alertname}} collides so Grafana "
        "dashboard tbar-ogalias-507 silently drops unique pages while heartbeat is green"
    ),
    bad_lie=(
        "Raising Opsgenie heartbeat interval does not un-dedupe leftover leftover leftover "
        "alias collisions that silent-drop pages"
    ),
    false_lead="Opsgenie heartbeat leftover",
    avoided="r183 IRM heartbeat; r159 IRM group_by",
    this_is="Opsgenie leftover leftover leftover alias collision silent drop",
    ticket="OBS-7608",
    knob=".opsgenie.alias",
    old='alias: "{{ .GroupLabels.alertname }}"',
    new='alias: "{{ .GroupLabels.alertname }}:{{ .GroupLabels.service }}"',
    wrong_knob=".heartbeat.interval",
    wrong_old="interval: 10m",
    wrong_new="interval: 1m",
    wrong2_old="priority: P5",
    wrong2_new="priority: P1",
    reload="grafana",
    config_path="opsgenie/tbar-hb.yaml",
    lie_path="opsgenie/tbar-alias.yaml",
    bad_config="opsgenie/chock-hb.yaml",
    bad_lie_path="opsgenie/chock-alias.yaml",
)

# 9 CloudWatch leftover leftover leftover vs leftover
_emit(
    508,
    kind="grafana",
    ok_slug="cw-metric-math-search-wrong-dash-leftover",
    bad_slug="cw-math-raise-period-not-search",
    ok_svc="stand-guid-cw-svc",
    bad_svc="docking-lt-cw-svc",
    ok_dash="sguid-cwmath-508",
    bad_dash="dock-cwmath-period",
    panel="CW SEARCH",
    metric="",
    needle="guid_off",
    lie=(
        "CloudWatch leftover SEARCH('AWS/ApplicationELB') on dashboard sguid-cwmath-508 "
        "is the wrong dashboard while custom metric stand_guid_cw still publishes"
    ),
    bad_lie=(
        "Raising CloudWatch period does not bind Grafana to leftover leftover leftover "
        "SEARCH namespace AWS/ApplicationELB instead of stand-guid"
    ),
    false_lead="CloudWatch period leftover",
    avoided="r210 lookback; Grafana SQL expr stale uid",
    this_is="CloudWatch leftover leftover leftover SEARCH wrong dashboard",
    ticket="OBS-7609",
    knob=".panels[0].metricQuery",
    old="SEARCH('{AWS/ApplicationELB,LoadBalancer}', 'Average')",
    new="SEARCH('{Airline/StandGuid,Service}', 'Average')",
    wrong_knob=".panels[0].period",
    wrong_old="period: 300",
    wrong_new="period: 60",
    wrong2_old="region: us-east-1",
    wrong2_new="region: eu-west-1",
    reload="grafana",
    config_path="cloudwatch/sguid-period.yaml",
    lie_path="cloudwatch/sguid-search.yaml",
    bad_config="cloudwatch/dock-period.yaml",
    bad_lie_path="cloudwatch/dock-search.yaml",
)

# 10 Stackdriver leftover leftover leftover vs leftover
_emit(
    509,
    kind="grafana",
    ok_slug="sd-metric-descriptor-label-drop-leftover",
    bad_slug="sd-desc-raise-align-not-labels",
    ok_svc="fids-board-sd-svc",
    bad_svc="bagtag-sd-svc",
    ok_dash="fids-sdlbl-509",
    bad_dash="btag-sdlbl-align",
    panel="Stackdriver by gate",
    metric="",
    needle="fids_blank",
    lie=(
        "Stackdriver leftover metric descriptor drops label gate so Grafana "
        "dashboard fids-sdlbl-509 groups wrong while time-series still ingest"
    ),
    bad_lie=(
        "Raising perSeriesAligner does not restore leftover leftover leftover dropped "
        "gate labels on the metric descriptor"
    ),
    false_lead="perSeriesAligner leftover",
    avoided="r186 k8sattributes; Mimir max_label_names_per_series",
    this_is="Stackdriver leftover leftover leftover descriptor dropped label",
    ticket="OBS-7610",
    knob=".metricDescriptor.labels",
    old="labels: [service]",
    new="labels: [service, gate]",
    wrong_knob=".aggregation.perSeriesAligner",
    wrong_old="perSeriesAligner: ALIGN_MEAN",
    wrong_new="perSeriesAligner: ALIGN_MAX",
    wrong2_old="crossSeriesReducer: REDUCE_NONE",
    wrong2_new="crossSeriesReducer: REDUCE_SUM",
    reload="grafana",
    config_path="stackdriver/fids-align.yaml",
    lie_path="stackdriver/fids-desc.yaml",
    bad_config="stackdriver/btag-align.yaml",
    bad_lie_path="stackdriver/btag-desc.yaml",
)

# 11 Azure Monitor leftover leftover leftover vs leftover
_emit(
    510,
    kind="grafana",
    ok_slug="azmon-kql-workspace-remap-leftover",
    bad_slug="azmon-kql-raise-timeout-not-ws",
    ok_svc="jetway-az-svc",
    bad_svc="pca-bridge-az-svc",
    ok_dash="jway-azkql-510",
    bad_dash="pca-azkql-to",
    panel="Azure KQL",
    metric="",
    needle="jetway_stuck",
    lie=(
        "Azure Monitor leftover KQL workspace remap points Grafana dashboard "
        "jway-azkql-510 at LAW-archive so the panel is the wrong dashboard while "
        "LAW-live still has rows"
    ),
    bad_lie=(
        "Raising Azure query timeout does not bind Grafana to leftover leftover leftover "
        "KQL workspace LAW-archive instead of LAW-live"
    ),
    false_lead="Azure query timeout leftover",
    avoided="r496 grafana timeout; r300 Grafana dataproxy",
    this_is="Azure Monitor leftover leftover leftover KQL workspace wrong dashboard",
    ticket="OBS-7611",
    knob=".azure.workspace",
    old="workspace: LAW-archive",
    new="workspace: LAW-live",
    wrong_knob=".azure.queryTimeout",
    wrong_old="queryTimeout: 30s",
    wrong_new="queryTimeout: 5m",
    wrong2_old="subscription: sub-old",
    wrong2_new="subscription: sub-prod",
    reload="grafana",
    config_path="azure/jway-qto.yaml",
    lie_path="azure/jway-ws.yaml",
    bad_config="azure/pca-qto.yaml",
    bad_lie_path="azure/pca-ws.yaml",
)

# 12 Kibana leftover leftover leftover vs leftover
_emit(
    511,
    kind="grafana",
    ok_slug="kibana-index-pattern-wrong-dash-leftover",
    bad_slug="kib-ipat-raise-shards-not-pattern",
    ok_svc="stand-entry-kb-svc",
    bad_svc="mdw-hold-kb-svc",
    ok_dash="sentry-kbipat-511",
    bad_dash="mdw-kbipat-shards",
    panel="Kibana discover",
    metric="",
    needle="stand_block",
    lie=(
        "Kibana leftover index-pattern logs-archive-* so dashboard sentry-kbipat-511 "
        "is the wrong dashboard while logs-stand-entry-kb-svc-* still has hits"
    ),
    bad_lie=(
        "Raising Elasticsearch number_of_shards does not retarget leftover leftover leftover "
        "Kibana index-pattern logs-archive-*"
    ),
    false_lead="ES number_of_shards leftover",
    avoided="r244 loki-querier-max-concurrent; OpenSearch/Loki leftover plants",
    this_is="Kibana leftover leftover leftover index-pattern wrong dashboard",
    ticket="OBS-7612",
    knob=".kibana.indexPattern",
    old="indexPattern: logs-archive-*",
    new="indexPattern: logs-stand-entry-kb-svc-*",
    wrong_knob=".index.number_of_shards",
    wrong_old="number_of_shards: 1",
    wrong_new="number_of_shards: 5",
    wrong2_old="refresh_interval: 60s",
    wrong2_new="refresh_interval: 5s",
    reload="grafana",
    config_path="kibana/sentry-shards.yaml",
    lie_path="kibana/sentry-ipat.yaml",
    bad_config="kibana/mdw-shards.yaml",
    bad_lie_path="kibana/mdw-ipat.yaml",
)

# 13 Grafana OnCall leftover leftover leftover vs leftover
_emit(
    512,
    kind="grafana",
    ok_slug="oncall-integration-wrong-team-leftover",
    bad_slug="oncall-int-raise-hb-not-team",
    ok_svc="crew-bus-oc-svc",
    bad_svc="pax-bus-oc-svc",
    ok_dash="cbus-octeam-512",
    bad_dash="pbus-octeam-hb",
    panel="OnCall pages",
    metric="",
    needle="bus_late",
    lie=(
        "Grafana OnCall leftover integration routes crew-bus-oc-svc onto team ramp-nights "
        "so dashboard cbus-octeam-512 is the wrong dashboard while the webhook still 200"
    ),
    bad_lie=(
        "Raising OnCall heartbeat does not rebind leftover leftover leftover integration "
        "from team ramp-nights to crew-day"
    ),
    false_lead="OnCall heartbeat leftover",
    avoided="r159 IRM group_by; Grafana Incident vs IRM",
    this_is="Grafana OnCall leftover leftover leftover integration wrong team/dashboard",
    ticket="OBS-7613",
    knob=".oncall.integrations[].team",
    old="team: ramp-nights",
    new="team: crew-day",
    wrong_knob=".oncall.heartbeat.interval",
    wrong_old="interval: 30m",
    wrong_new="interval: 1m",
    wrong2_old="group_by: [alertname]",
    wrong2_new="group_by: [alertname, service]",
    reload="grafana",
    config_path="oncall/cbus-hb.yaml",
    lie_path="oncall/cbus-team.yaml",
    bad_config="oncall/pbus-hb.yaml",
    bad_lie_path="oncall/pbus-team.yaml",
)

# 14 Incident.io leftover leftover leftover vs leftover
_emit(
    513,
    kind="grafana",
    ok_slug="incidentio-alert-source-silent-drop-leftover",
    bad_slug="incio-src-raise-sla-not-source",
    ok_svc="airstairs-io-svc",
    bad_svc="beltloader-io-svc",
    ok_dash="astair-iosrc-513",
    bad_dash="bload-iosrc-sla",
    panel="incident.io alerts",
    metric="",
    needle="stair_jam",
    lie=(
        "incident.io leftover alert source Grafana-legacy is archived so dashboard "
        "astair-iosrc-513 silently drops pages while the new source still receives 200s"
    ),
    bad_lie=(
        "Raising incident.io SLA minutes does not restore leftover leftover leftover "
        "archived Grafana-legacy alert source silent drops"
    ),
    false_lead="incident.io SLA leftover",
    avoided="Grafana Incident vs IRM; r159 IRM",
    this_is="incident.io leftover leftover leftover archived source silent drop",
    ticket="OBS-7614",
    knob=".alert_sources[].status",
    old="status: archived",
    new="status: active",
    wrong_knob=".sla.ack_minutes",
    wrong_old="ack_minutes: 30",
    wrong_new="ack_minutes: 5",
    wrong2_old="severity: minor",
    wrong2_new="severity: major",
    reload="grafana",
    config_path="incidentio/astair-sla.yaml",
    lie_path="incidentio/astair-source.yaml",
    bad_config="incidentio/bload-sla.yaml",
    bad_lie_path="incidentio/bload-source.yaml",
)

# 15 FireHydrant leftover leftover leftover vs leftover
_emit(
    514,
    kind="grafana",
    ok_slug="fh-signal-rule-drop-label-leftover",
    bad_slug="fh-sig-raise-runbook-not-label",
    ok_svc="gpu-cable-fh-svc",
    bad_svc="pca-hose-fh-svc",
    ok_dash="gcable-fhsig-514",
    bad_dash="phose-fhsig-rb",
    panel="FireHydrant signals",
    metric="",
    needle="gpu_trip",
    lie=(
        "FireHydrant leftover signal rule strips label service so Grafana dashboard "
        "gcable-fhsig-514 groups the wrong dashboard while webhooks still 201"
    ),
    bad_lie=(
        "Attaching a runbook does not restore leftover leftover leftover stripped "
        "service labels on FireHydrant signals"
    ),
    false_lead="FireHydrant runbook leftover",
    avoided="r177 alloy relabel; Tempo MG filter",
    this_is="FireHydrant leftover leftover leftover signal dropped label",
    ticket="OBS-7615",
    knob=".signals.rules[].drop_labels",
    old="drop_labels: [service]",
    new="drop_labels: []",
    wrong_knob=".runbooks.attach",
    wrong_old="attach: gpu-generic",
    wrong_new="attach: gpu-cable-fh",
    wrong2_old="severity: SEV3",
    wrong2_new="severity: SEV1",
    reload="grafana",
    config_path="firehydrant/gcable-rb.yaml",
    lie_path="firehydrant/gcable-sig.yaml",
    bad_config="firehydrant/phose-rb.yaml",
    bad_lie_path="firehydrant/phose-sig.yaml",
)

# 16 Rootly leftover leftover leftover vs leftover
_emit(
    515,
    kind="grafana",
    ok_slug="rootly-urgency-filter-silent-drop-leftover",
    bad_slug="rootly-urg-raise-page-not-filter",
    ok_svc="push-tug-rt-svc",
    bad_svc="tow-truck-rt-svc",
    ok_dash="ptug-rturg-515",
    bad_dash="ttruck-rturg-page",
    panel="Rootly incidents",
    metric="",
    needle="tug_stall",
    lie=(
        "Rootly leftover urgency filter high-only silently drops medium alerts so Grafana "
        "dashboard ptug-rturg-515 is empty while the alert source still 202"
    ),
    bad_lie=(
        "Raising Rootly page delay does not restore leftover leftover leftover "
        "urgency=high-only silent drops"
    ),
    false_lead="Rootly page delay leftover",
    avoided="PagerDuty orch; Opsgenie alias; r159 IRM",
    this_is="Rootly leftover leftover leftover urgency filter silent drop",
    ticket="OBS-7616",
    knob=".alerts.urgency_filter",
    old="urgency_filter: high",
    new="urgency_filter: high,medium,low",
    wrong_knob=".paging.delay_seconds",
    wrong_old="delay_seconds: 300",
    wrong_new="delay_seconds: 0",
    wrong2_old="escalation: skip",
    wrong2_new="escalation: default",
    reload="grafana",
    config_path="rootly/ptug-page.yaml",
    lie_path="rootly/ptug-urg.yaml",
    bad_config="rootly/ttruck-page.yaml",
    bad_lie_path="rootly/ttruck-urg.yaml",
)
