"""Unique observability plants for rounds 159+ (do not clone r109-r158)."""

PAIRS = []


def _ok(**kwargs):
    return kwargs


def _fail(**kwargs):
    return kwargs


# ---------------------------------------------------------------------------
# r159 Grafana IRM grouping vs Alertmanager silence (NOT AM inhibit)
# ---------------------------------------------------------------------------
PAIRS.append(
    (
        _ok(
            slug="irm-groupkey-vs-am-silence",
            service="checkout-tax-svc",
            dashboard_uid="tax-irm-01",
            panel="pages last 1h",
            query='count_over_time(oncall_notification_sent{service="checkout-tax-svc"}[1h])',
            lie="Grafana IRM groups by alertname,cluster so AM silence matcher service= never matches IRM page key",
            false_lead="Alertmanager inhibit on severity=info",
            config_path="helm/alertmanager/values.yaml",
            lie_path="helm/grafana-irm/escalation.yaml",
            truth_name="IRM integration inbox",
            reload_name="grafana-irm",
            side="AM silence still honored for AM-only routes",
            surfaces="Grafana IRM group_by vs AM silence matcher",
            avoided="r109-r158 AM inhibit, unified+legacy dual-eval, provisioned uid, SQL expr stale uid",
            this_is="IRM grouping key bypasses AM silence (not inhibit)",
            step_note="False lead AM inhibit 4-5; IRM group_by 6-8; patch grouping 9-12.",
            search_cmd="curl -sS $GRAFANA/api/search?query=tax-irm-01 | jq -c '.[]|{uid,title,url}'",
            dash_cmd="curl -sS $GRAFANA/api/dashboards/uid/tax-irm-01 | jq '.dashboard.panels[]|{id,title,targets}'",
            query_cmd="curl -sS -G $MIMIR/prometheus/api/v1/query --data-urlencode 'query=count_over_time(oncall_notification_sent{service=\"checkout-tax-svc\"}[1h])'",
            false_cmd="amtool silence query service=checkout-tax-svc --alertmanager.url=$AM",
            truth_cmd="curl -sS $IRM/api/v1/notifications?service=checkout-tax-svc | jq '.[:3]'",
            confirm_cmd="yq -r '.escalation.group_by, .source' helm/grafana-irm/escalation.yaml; amtool config routes show --alertmanager.url=$AM | head -n 40",
            reload_cmd="kubectl -n irm rollout restart deploy/grafana-oncall && kubectl -n irm rollout status deploy/grafana-oncall --timeout=90s",
            requery_cmd="curl -sS -G $MIMIR/prometheus/api/v1/query --data-urlencode 'query=count_over_time(oncall_notification_sent{service=\"checkout-tax-svc\"}[10m])'",
            grafana_ok_cmd="curl -sS $GRAFANA/api/dashboards/uid/tax-irm-01/panels/4/query | jq '.results[0].frames[0].schema'",
            side_cmd="amtool silence query service=checkout-tax-svc --alertmanager.url=$AM | jq 'length'",
            final_cmd="curl -sS $IRM/api/v1/notifications?service=checkout-tax-svc\\&since=10m | jq '{count:length,grouped_by:.[0].group_key}'",
            patch_old="group_by: [alertname, cluster]",
            patch_new="group_by: [alertname, cluster, service]\nsource: alertmanager  # IRM follows AM silences",
            runbook_path="runbooks/checkout-tax-irm-silence.md",
            runbook=(
                "# checkout-tax-svc IRM vs AM\n"
                "IRM group_by omitted service, so AM silence on service= did not drop IRM pages.\n"
                "Contact point grafana_oncall bypassed AM. Point IRM at AM as source.\n"
            ),
            goal=(
                "checkout-tax-svc dashboard tax-irm-01 still counts pages while AM lists a "
                "silence for service=checkout-tax-svc. Find the IRM grouping lie and stop the dual page."
            ),
            plan="Search dashboard → query pages → check AM inhibit (false) → read IRM group_by → patch + verify.",
            outcome=(
                "Patched IRM group_by to include service and set source=alertmanager. "
                "tax-irm-01 pages last 1h dropped to 0 under the existing AM silence. Side routes still honor AM."
            ),
            obs1=(
                '[{"uid":"tax-irm-01","title":"checkout-tax page budget","url":"/d/tax-irm-01"}]\n'
                "folder: airline-tax  cluster: iad-obs-a"
            ),
            obs2=(
                '{"id":4,"title":"pages last 1h","targets":[{"datasource":"mimir-tax",'
                '"expr":"count_over_time(oncall_notification_sent{service=\\"checkout-tax-svc\\"}[1h])"}]}\n'
                '{"id":7,"title":"AM silenced?","targets":[{"expr":"alertmanager_silences{service=\\"checkout-tax-svc\\"}"}]}'
            ),
            obs3=(
                '{"status":"success","data":{"resultType":"vector","result":['
                '{"metric":{"service":"checkout-tax-svc","integration":"grafana_oncall"},"value":[1710000000,"14"]}]}}\n'
                "14 pages in 1h while panel 7 shows silences=1"
            ),
            obs4=(
                "silence_id=s-tax-7a  matchers=service=checkout-tax-svc  createdBy=tax-sre\n"
                "amtool inhibit query: 0 rows (no inhibit). False lead AM inhibit is empty."
            ),
            obs5=(
                "helm/alertmanager/values.yaml:\n"
                "inhibit_rules: []   # nothing matching checkout-tax-svc\n"
                "routes:\n"
                "  - matchers: [service=checkout-tax-svc]\n"
                "    receiver: pager-tax\n"
                "    continue: false"
            ),
            obs6=(
                "helm/grafana-irm/escalation.yaml:\n"
                "escalation:\n"
                "  group_by: [alertname, cluster]\n"
                "  wait: 0s\n"
                "contact_points:\n"
                "  - uid: tax-oncall\n"
                "    type: grafana_oncall\n"
                "    url: http://irm.obs/api/v1/integrations/grafana/"
            ),
            obs7=(
                '[{"id":"n-441","group_key":"TaxLatencyHigh|iad-obs-a","service":"checkout-tax-svc",'
                '"silenced_am":false,"via":"grafana_oncall"}]\n'
                "IRM inbox has 14 notifications; group_key has no service label"
            ),
            obs8=(
                "group_by: [alertname cluster]\nsource: grafana_alerting\n"
                "AM route matchers include service= ; IRM group_key TaxLatencyHigh|iad-obs-a ignores silence matcher"
            ),
            obs9="patched helm/grafana-irm/escalation.yaml group_by += service; source=alertmanager",
            obs10="deployment.apps/grafana-oncall restarted\ndeployment \"grafana-oncall\" successfully rolled out",
            obs11='{"status":"success","data":{"resultType":"vector","result":[{"value":[1710000600,"0"]}]}}',
            obs12='{"name":"pages last 1h","fields":[{"name":"Value","type":"number"}],"rows":1}  value=0',
            obs13="1\n# existing AM silence still listed; IRM no longer pages around it",
            obs14="wrote runbooks/checkout-tax-irm-silence.md",
            obs15='{"count":0,"grouped_by":null}\n# tax-irm-01 green under silence; IRM follows AM',
        ),
        _fail(
            slug="irm-silence-patch-am-only",
            service="returns-portal-svc",
            dashboard_uid="returns-irm-noise",
            panel="IRM pages vs AM fires",
            query='oncall_notification_sent{service="returns-portal-svc"}',
            lie="Grafana IRM grafana_oncall contact point ignores AM silence; AM-only matcher patch cannot stop IRM",
            false_lead="AM silence matcher missing cluster",
            config_path="helm/alertmanager/values.yaml",
            lie_path="helm/grafana-irm/returns-escalation.yaml",
            wrong_path="helm/alertmanager/silences.yaml",
            reload_name="alertmanager",
            ticket="OBS-4419",
            xfail="tests/test_returns_irm_silence.py",
            surfaces="IRM contact point vs AM silence YAML",
            avoided="r109-r158 AM inhibit",
            this_is="fail/handoff: patched AM silence, IRM still pages",
            step_note="False lead AM matcher 4-7; still paging 9-11; late IRM read 12; handoff 14-15.",
            next_note="Next: Prom agent-mode Grafana datasource vs Mimir, not remote_write queue.",
            search_cmd="curl -sS $GRAFANA/api/search?query=returns-irm-noise | jq -c '.[]|{uid,title}'",
            dash_cmd="curl -sS $GRAFANA/api/dashboards/uid/returns-irm-noise | jq '.dashboard.panels[0].targets'",
            query_cmd="curl -sS -G $MIMIR/prometheus/api/v1/query --data-urlencode 'query=oncall_notification_sent{service=\"returns-portal-svc\"}'",
            false_cmd="amtool silence query service=returns-portal-svc --alertmanager.url=$AM",
            reload_cmd="kubectl -n am rollout restart statefulset/alertmanager && kubectl -n am rollout status statefulset/alertmanager --timeout=90s",
            requery_cmd="curl -sS -G $MIMIR/prometheus/api/v1/query --data-urlencode 'query=oncall_notification_sent{service=\"returns-portal-svc\"}'",
            denied_cmd="kubectl -n irm auth can-i patch deploy/grafana-oncall --as=sre-bot",
            xfail_cmd="printf '%s\\n' 'import pytest\\n@pytest.mark.xfail(reason=\"IRM owned by oncall-platform\")\\ndef test_returns_irm_silence():\\n    assert False' > tests/test_returns_irm_silence.py && git add tests/test_returns_irm_silence.py",
            wrong_old="matchers:\n  - service=returns-portal-svc",
            wrong_new="matchers:\n  - service=returns-portal-svc\n  - cluster=iad-obs-a",
            wrong2_old="comment: tax-sre silence",
            wrong2_new="comment: widen matcher to cluster + namespace",
            ticket_path="tickets/OBS-4419.md",
            ticket_body=(
                "OBS-4419 handoff: returns-portal-svc pages via grafana_oncall even with AM silence "
                "cluster+service. Need IRM source=alertmanager; sre-bot cannot patch grafana-oncall.\n"
            ),
            goal=(
                "returns-portal-svc dashboard returns-irm-noise shows IRM pages while AM is silenced. "
                "Stop the pages."
            ),
            plan="Assume AM matcher is incomplete, patch silences, reload AM.",
            outcome=(
                "AM silence now matches cluster+service but IRM still pages via grafana_oncall. "
                "Late read of returns-escalation.yaml. Handoff OBS-4419; xfail test_returns_irm_silence."
            ),
            obs1='[{"uid":"returns-irm-noise","title":"returns portal IRM noise"}]',
            obs2='[{"expr":"oncall_notification_sent{service=\\"returns-portal-svc\\"}","datasource":"mimir-returns"}]',
            obs3='{"status":"success","data":{"result":[{"value":[1710000000,"9"]}]}}',
            obs4="silence_id=s-ret-1 matchers=service=returns-portal-svc  (no cluster)\n# treated as RCA",
            obs5="routes:\n  - matchers: [service=returns-portal-svc]\n    receiver: pager-returns",
            obs6="silences.yaml:\n  matchers:\n    - service=returns-portal-svc\n  comment: tax-sre silence",
            obs7="patched silences.yaml added cluster=iad-obs-a",
            obs8='statefulset.apps/alertmanager restarted\nstatefulset "alertmanager" successfully rolled out',
            obs9='{"status":"success","data":{"result":[{"value":[1710000300,"9"]}]}}\n# still 9 pages',
            obs10="patched comment; no IRM change",
            obs11='{"status":"success","data":{"result":[{"value":[1710000400,"9"]}]}}',
            obs12=(
                "helm/grafana-irm/returns-escalation.yaml:\n"
                "contact_points:\n  - type: grafana_oncall\n    url: http://irm.obs/api/v1/integrations/grafana/\n"
                "group_by: [alertname]\nsource: grafana_alerting"
            ),
            obs13='no\n# sre-bot cannot patch grafana-oncall; IRM owned by oncall-platform',
            obs14="wrote tickets/OBS-4419.md",
            obs15="created xfail tests/test_returns_irm_silence.py\n# handoff complete",
        ),
    )
)


# ---------------------------------------------------------------------------
# r160 Prometheus agent mode vs server (NOT remote_write queue)
# ---------------------------------------------------------------------------
PAIRS.append(
    (
        _ok(
            slug="prom-agent-no-local-tsdb",
            service="fare-quote-svc",
            dashboard_uid="quote-agent-09",
            panel="quote p99",
            query='histogram_quantile(0.99, rate(quote_latency_ms_bucket{service="fare-quote-svc"}[5m]))',
            lie="Grafana datasource still points at Prometheus --enable-feature=agent which has no local TSDB query",
            false_lead="Mimir remote_write queue full / WAL blocked",
            config_path="k8s/prom-agent/statefulset.yaml",
            lie_path="grafana/datasources/prom-quote-local.yaml",
            truth_name="Mimir query-frontend",
            reload_name="grafana",
            side="agent remote_write to Mimir still healthy",
            surfaces="Prom agent mode vs server datasource URL",
            avoided="r109-r158 remote_write queue, TSDB retention.size, Mimir max_label_names",
            this_is="agent-mode Prom has empty /api/v1/query; Grafana still uses it",
            step_note="False lead remote_write queue 4-5; agent flag 6-8; datasource→Mimir 9-12.",
            search_cmd="curl -sS $GRAFANA/api/search?query=quote-agent-09 | jq -c '.[]|{uid,title}'",
            dash_cmd="curl -sS $GRAFANA/api/dashboards/uid/quote-agent-09 | jq '.dashboard.panels[]|select(.title==\"quote p99\")'",
            query_cmd="curl -sS -G http://prom-agent.obs:9090/api/v1/query --data-urlencode 'query=histogram_quantile(0.99, rate(quote_latency_ms_bucket{service=\"fare-quote-svc\"}[5m]))'",
            false_cmd="curl -sS http://prom-agent.obs:9090/metrics | rg 'prometheus_remote_storage_(samples_pending|queue|failed)'",
            truth_cmd="curl -sS -G http://mimir-query.obs:8080/prometheus/api/v1/query --data-urlencode 'query=histogram_quantile(0.99, rate(quote_latency_ms_bucket{service=\"fare-quote-svc\"}[5m]))'",
            confirm_cmd="kubectl -n obs get pod prom-agent-0 -o jsonpath='{.spec.containers[0].args}' | jq -R .; curl -sS http://prom-agent.obs:9090/api/v1/status/buildinfo | jq .",
            reload_cmd="kubectl -n grafana rollout restart deploy/grafana && kubectl -n grafana rollout status deploy/grafana --timeout=90s",
            requery_cmd="curl -sS -G http://mimir-query.obs:8080/prometheus/api/v1/query --data-urlencode 'query=histogram_quantile(0.99, rate(quote_latency_ms_bucket{service=\"fare-quote-svc\"}[5m]))'",
            grafana_ok_cmd="curl -sS $GRAFANA/api/ds/query -d @/tmp/quote-p99.json | jq '.results.A.frames[0].data.values'",
            side_cmd="curl -sS http://prom-agent.obs:9090/metrics | rg 'prometheus_remote_storage_succeeded_samples_total'",
            final_cmd="curl -sS $GRAFANA/api/datasources/uid/prom-quote-local | jq '{url,type,jsonData}'",
            patch_old='url: http://prom-agent.obs:9090',
            patch_new='url: http://mimir-query.obs:8080/prometheus\nisDefault: false',
            runbook_path="runbooks/fare-quote-agent-datasource.md",
            runbook=(
                "# fare-quote-svc Prom agent vs Grafana\n"
                "prom-agent runs --enable-feature=agent; local /api/v1/query is empty by design.\n"
                "Point Grafana at Mimir query-frontend. Do not enable TSDB on the agent.\n"
            ),
            goal=(
                "fare-quote-svc dashboard quote-agent-09 quote p99 is empty. "
                "Scrape and remote_write look fine. Find why Grafana reads nothing."
            ),
            plan="Dashboard → query local Prom → check remote_write queue (false) → discover agent mode → retarget Grafana to Mimir.",
            outcome=(
                "Grafana datasource prom-quote-local now hits Mimir query-frontend. "
                "quote p99 renders 182ms. Agent still remote_writes; no local TSDB added."
            ),
            obs1='[{"uid":"quote-agent-09","title":"fare-quote local TSDB"}]',
            obs2=(
                '{"id":2,"title":"quote p99","datasource":{"uid":"prom-quote-local"},'
                '"targets":[{"expr":"histogram_quantile(0.99, rate(quote_latency_ms_bucket{service=\\"fare-quote-svc\\"}[5m]))"}]}'
            ),
            obs3='{"status":"success","data":{"resultType":"vector","result":[]}}\n# empty from prom-agent:9090',
            obs4=(
                "prometheus_remote_storage_samples_pending 12\n"
                "prometheus_remote_storage_samples_failed_total 0\n"
                "prometheus_remote_storage_queue_highest_sent_timestamp_seconds 1710000000\n"
                "# queue not full — false lead remote_write queue rejected"
            ),
            obs5=(
                "args:\n"
                "  - --enable-feature=agent\n"
                "  - --config.file=/etc/prometheus/prometheus.yml\n"
                "  - --web.enable-lifecycle\n"
                "# no --storage.tsdb.path (agent mode)"
            ),
            obs6=(
                "apiVersion: 1\ndatasources:\n"
                "  - name: prom-quote-local\n"
                "    uid: prom-quote-local\n"
                "    type: prometheus\n"
                "    url: http://prom-agent.obs:9090"
            ),
            obs7=(
                '{"status":"success","data":{"result":[{"metric":{"service":"fare-quote-svc"},'
                '"value":[1710000000,"182.4"]}]}}\n# Mimir has the histogram'
            ),
            obs8=(
                '["--enable-feature=agent","--config.file=/etc/prometheus/prometheus.yml"]\n'
                '{"version":"2.54.1","features":["agent"]}\n# /api/v1/query empty is by design in agent mode'
            ),
            obs9="patched grafana/datasources/prom-quote-local.yaml url → mimir-query.obs:8080/prometheus",
            obs10='deployment "grafana" successfully rolled out',
            obs11='{"status":"success","data":{"result":[{"value":[1710000600,"182.4"]}]}}',
            obs12="[[1710000600],[182.4]]",
            obs13="prometheus_remote_storage_succeeded_samples_total 9482211",
            obs14="wrote runbooks/fare-quote-agent-datasource.md",
            obs15='{"url":"http://mimir-query.obs:8080/prometheus","type":"prometheus","jsonData":{"httpMethod":"POST"}}',
        ),
        _fail(
            slug="prom-agent-tsdb-path-noop",
            service="seat-map-svc",
            dashboard_uid="seatmap-agent-wal",
            panel="seat render p95",
            query='histogram_quantile(0.95, rate(seatmap_render_ms_bucket{service="seat-map-svc"}[5m]))',
            lie="Prometheus agent ignores --storage.tsdb.path; Grafana still queries agent with no TSDB",
            false_lead="agent WAL replay / empty TSDB path",
            config_path="k8s/prom-agent-seat/statefulset.yaml",
            lie_path="grafana/datasources/prom-seat-local.yaml",
            wrong_path="k8s/prom-agent-seat/statefulset.yaml",
            reload_name="prom-agent-seat",
            ticket="OBS-4420",
            xfail="tests/test_seatmap_agent_query.py",
            surfaces="agent --storage.tsdb.path noop vs Grafana URL",
            avoided="r109-r158 remote_write queue, TSDB retention.size",
            this_is="fail/handoff: added TSDB path on agent, query still empty",
            step_note="WAL path 4-7; still empty 9-11; late datasource read 12; handoff 14-15.",
            next_note="Next: VictoriaLogs LogsQL vs Loki LogQL, not Loki SM allowlist.",
            search_cmd="curl -sS $GRAFANA/api/search?query=seatmap-agent-wal | jq -c '.[]|{uid,title}'",
            dash_cmd="curl -sS $GRAFANA/api/dashboards/uid/seatmap-agent-wal | jq '.dashboard.panels[0]'",
            query_cmd="curl -sS -G http://prom-agent-seat.obs:9090/api/v1/query --data-urlencode 'query=histogram_quantile(0.95, rate(seatmap_render_ms_bucket{service=\"seat-map-svc\"}[5m]))'",
            false_cmd="kubectl -n obs exec prom-agent-seat-0 -- ls -la /prometheus/wal | head",
            reload_cmd="kubectl -n obs rollout restart statefulset/prom-agent-seat && kubectl -n obs rollout status statefulset/prom-agent-seat --timeout=120s",
            requery_cmd="curl -sS -G http://prom-agent-seat.obs:9090/api/v1/query --data-urlencode 'query=histogram_quantile(0.95, rate(seatmap_render_ms_bucket{service=\"seat-map-svc\"}[5m]))'",
            denied_cmd="kubectl -n grafana auth can-i patch configmap/grafana-datasources --as=sre-bot",
            xfail_cmd="printf '%s\\n' '@pytest.mark.xfail(reason=\"grafana datasource owned by platform-obs\")\\ndef test_seatmap_agent_query():\\n    assert False' > tests/test_seatmap_agent_query.py",
            wrong_old="- --enable-feature=agent",
            wrong_new="- --enable-feature=agent\n        - --storage.tsdb.path=/prometheus",
            wrong2_old="- --web.enable-lifecycle",
            wrong2_new="- --web.enable-lifecycle\n        - --storage.tsdb.retention.size=2GB",
            ticket_path="tickets/OBS-4420.md",
            ticket_body=(
                "OBS-4420: seat-map-svc quote empty because Grafana hits agent-mode Prom. "
                "TSDB flags are ignored in agent mode. Need datasource URL change; sre-bot cannot patch grafana-datasources.\n"
            ),
            goal="seat-map-svc dashboard seatmap-agent-wal p95 is empty despite scrapes. Restore the panel.",
            plan="Assume WAL/TSDB path missing on agent; add storage flags.",
            outcome=(
                "Added --storage.tsdb.path and retention.size on agent; /api/v1/query still empty. "
                "Late read of prom-seat-local.yaml. Handoff OBS-4420."
            ),
            obs1='[{"uid":"seatmap-agent-wal","title":"seat-map agent WAL"}]',
            obs2='{"title":"seat render p95","datasource":{"uid":"prom-seat-local"}}',
            obs3='{"status":"success","data":{"result":[]}}',
            obs4="wal/00000013  wal/checkpoint.00000012  # WAL present, not corrupt",
            obs5="args: [--enable-feature=agent, --config.file=/etc/prometheus/prometheus.yml, --web.enable-lifecycle]",
            obs6="same statefulset; no tsdb path — treated as RCA",
            obs7="patched added --storage.tsdb.path=/prometheus",
            obs8='statefulset "prom-agent-seat" successfully rolled out\n# log: flag --storage.tsdb.path ignored in agent mode',
            obs9='{"status":"success","data":{"result":[]}}',
            obs10="patched added retention.size=2GB (still agent mode)",
            obs11='{"status":"success","data":{"result":[]}}',
            obs12=(
                "grafana/datasources/prom-seat-local.yaml:\n"
                "  url: http://prom-agent-seat.obs:9090\n"
                "  uid: prom-seat-local"
            ),
            obs13="no",
            obs14="wrote tickets/OBS-4420.md",
            obs15="xfail tests/test_seatmap_agent_query.py",
        ),
    )
)


# ---------------------------------------------------------------------------
# r161 VictoriaLogs LogsQL vs Loki LogQL
# ---------------------------------------------------------------------------
PAIRS.append(
    (
        _ok(
            slug="vl-logsql-vs-loki-logql",
            service="baggage-scan-svc",
            dashboard_uid="bag-vl-12",
            panel="scan_fail rate",
            query='{app="baggage-scan-svc"} |= "scan_fail"',
            lie="Grafana Loki datasource URL rewritten to VictoriaLogs which speaks LogsQL not LogQL",
            false_lead="Loki structured metadata tenant allowlist drop",
            config_path="loki/config.yaml",
            lie_path="grafana/datasources/loki-edge.yaml",
            truth_name="VictoriaLogs LogsQL",
            reload_name="grafana",
            side="core Loki tenant still serves LogQL",
            surfaces="VictoriaLogs LogsQL vs Loki LogQL datasource URL",
            avoided="r109-r158 Loki SM allowlist, line_format drop, bloom not this round",
            this_is="VL URL behind a Loki datasource type; LogQL returns empty",
            step_note="False lead SM allowlist 4-5; VL LogsQL 6-8; split datasources 9-12.",
            search_cmd="curl -sS $GRAFANA/api/search?query=bag-vl-12 | jq -c '.[]|{uid,title}'",
            dash_cmd="curl -sS $GRAFANA/api/dashboards/uid/bag-vl-12 | jq '.dashboard.panels[]|select(.title==\"scan_fail rate\")'",
            query_cmd="curl -sS -G http://victorialogs:9428/select/logsql/query --data-urlencode 'query={app=\"baggage-scan-svc\"} |= \"scan_fail\"'",
            false_cmd="curl -sS http://loki-querier.obs:3100/loki/api/v1/label/service_name/values | jq .",
            truth_cmd="curl -sS -G http://victorialogs:9428/select/logsql/query --data-urlencode 'query=_time:5m app:=\"baggage-scan-svc\" \"scan_fail\"'",
            confirm_cmd="cat grafana/datasources/loki-edge.yaml; curl -sS http://victorialogs:9428/health",
            reload_cmd="kubectl -n grafana rollout restart deploy/grafana && kubectl -n grafana rollout status deploy/grafana --timeout=90s",
            requery_cmd="curl -sS -G http://loki-gateway.obs/loki/api/v1/query_range --data-urlencode 'query={app=\"baggage-scan-svc\"} |= \"scan_fail\"' --data-urlencode 'limit=5'",
            grafana_ok_cmd="curl -sS $GRAFANA/api/ds/query -d @/tmp/bag-scan.json | jq '.results.A.frames[0].schema.fields'",
            side_cmd="curl -sS -G http://loki-gateway.obs/loki/api/v1/query --data-urlencode 'query={app=\"checkin-core-svc\"} |= \"ok\"' | jq '.data.result | length'",
            final_cmd="curl -sS $GRAFANA/api/datasources | jq '.[]|{name,type,url}'",
            patch_old="url: http://victorialogs:9428/select/logsql/query\n    type: loki",
            patch_new=(
                "url: http://loki-gateway.obs\n    type: loki\n"
                "  - name: victorialogs-edge\n    type: victoriametrics-logs-datasource\n"
                "    url: http://victorialogs:9428"
            ),
            runbook_path="runbooks/baggage-vl-vs-loki.md",
            runbook=(
                "# baggage-scan-svc VL vs Loki\n"
                "loki-edge URL pointed at VictoriaLogs. LogQL `{app=}` is invalid LogsQL.\n"
                "Restore Loki gateway; add a VL datasource for LogsQL panels.\n"
            ),
            goal=(
                "baggage-scan-svc dashboard bag-vl-12 scan_fail rate is empty. "
                "Logs exist in the edge store. Find the language/datasource lie."
            ),
            plan="Query panel → check Loki SM allowlist (false) → discover VL URL on Loki type → split datasources.",
            outcome=(
                "Restored loki-edge to Loki gateway; added victorialogs-edge datasource. "
                "bag-vl-12 LogQL panel fills. Core Loki tenant unchanged."
            ),
            obs1='[{"uid":"bag-vl-12","title":"baggage scan errors"}]',
            obs2='{"title":"scan_fail rate","datasource":{"uid":"loki-edge"},"targets":[{"expr":"{app=\\"baggage-scan-svc\\"} |= \\"scan_fail\\""}]}',
            obs3='{"error":"unexpected token {","logs":[]}\n# VL rejected LogQL selector',
            obs4=(
                '{"data":["checkin-core-svc","boarding-pass-svc"]}\n'
                "# baggage-scan-svc missing on Loki labels but that is because edge moved to VL, not SM allowlist"
            ),
            obs5=(
                "limits_config:\n  allow_structured_metadata: true\n"
                "  volume_enabled: true\n# no per-tenant SM allowlist (banned plant not present)"
            ),
            obs6=(
                "apiVersion: 1\ndatasources:\n  - name: loki-edge\n    uid: loki-edge\n"
                "    type: loki\n    url: http://victorialogs:9428/select/logsql/query"
            ),
            obs7=(
                '{"_time":"2026-08-19T12:01:02Z","app":"baggage-scan-svc","_msg":"scan_fail belt=B3"}\n'
                '{"_time":"2026-08-19T12:01:08Z","app":"baggage-scan-svc","_msg":"scan_fail belt=B1"}\n'
                "# LogsQL returns rows"
            ),
            obs8="type: loki\nurl: http://victorialogs:9428/select/logsql/query\n# health: ok  VL is up; Grafana type is wrong",
            obs9="patched loki-edge URL back to loki-gateway; added VL datasource",
            obs10='deployment "grafana" successfully rolled out',
            obs11='{"status":"success","data":{"result":[{"stream":{"app":"baggage-scan-svc"},"values":[["1710000000000000000","scan_fail belt=B3"]]}]}}',
            obs12='[{"name":"Time","type":"time"},{"name":"Line","type":"string"}]',
            obs13="8",
            obs14="wrote runbooks/baggage-vl-vs-loki.md",
            obs15=(
                '{"name":"loki-edge","type":"loki","url":"http://loki-gateway.obs"}\n'
                '{"name":"victorialogs-edge","type":"victoriametrics-logs-datasource","url":"http://victorialogs:9428"}'
            ),
        ),
        _fail(
            slug="vl-json-parser-on-logsql",
            service="gate-board-svc",
            dashboard_uid="gate-vl-parser",
            panel="board_fail lines",
            query='{app="gate-board-svc"} | json | status>=500',
            lie="VictoriaLogs behind Loki datasource; adding | json does not turn LogQL into LogsQL",
            false_lead="Loki json parser / line_format drop",
            config_path="grafana/dashboards/gate-board.json",
            lie_path="grafana/datasources/loki-gate.yaml",
            wrong_path="grafana/dashboards/gate-board.json",
            reload_name="grafana",
            ticket="OBS-4421",
            xfail="tests/test_gate_vl_parser.py",
            surfaces="LogQL | json on VL URL",
            avoided="r109-r158 Loki line_format drop, SM allowlist",
            this_is="fail/handoff: rewrote LogQL parser, VL still rejects",
            step_note="Parser rewrite 6-10; still empty 11; late URL read 12; handoff 14-15.",
            next_note="Next: Sentry event_id vs Tempo trace_id, not Tempo missing dim.",
            search_cmd="curl -sS $GRAFANA/api/search?query=gate-vl-parser | jq -c '.[]|{uid,title}'",
            dash_cmd="curl -sS $GRAFANA/api/dashboards/uid/gate-vl-parser | jq '.dashboard.panels[0].targets'",
            query_cmd="curl -sS -G http://victorialogs:9428/select/logsql/query --data-urlencode 'query={app=\"gate-board-svc\"} | json | status>=500'",
            false_cmd="curl -sS $GRAFANA/api/dashboards/uid/gate-vl-parser | jq '.dashboard.panels[0].targets[0].expr'",
            reload_cmd="kubectl -n grafana rollout restart deploy/grafana && kubectl -n grafana rollout status deploy/grafana --timeout=90s",
            requery_cmd="curl -sS -G http://victorialogs:9428/select/logsql/query --data-urlencode 'query={app=\"gate-board-svc\"} | json | status>=500'",
            denied_cmd="kubectl -n grafana auth can-i patch configmap/grafana-datasources --as=sre-bot",
            xfail_cmd="printf '%s\\n' '@pytest.mark.xfail(reason=\"loki-gate datasource owned by edge-obs\")\\ndef test_gate_vl_parser():\\n    assert False' > tests/test_gate_vl_parser.py",
            wrong_old='{app="gate-board-svc"} |= "board_fail"',
            wrong_new='{app="gate-board-svc"} | json | status>=500',
            wrong2_old='{app="gate-board-svc"} | json | status>=500',
            wrong2_new='{app="gate-board-svc"} | json | line_format "{{.msg}}" | status>=500',
            ticket_path="tickets/OBS-4421.md",
            ticket_body=(
                "OBS-4421: gate-board-svc panels hit VictoriaLogs via type=loki. "
                "Parser edits cannot fix LogsQL. Need datasource split; no patch RBAC.\n"
            ),
            goal="gate-board-svc dashboard gate-vl-parser is empty. Restore board_fail lines.",
            plan="Assume Loki json/line_format drop; rewrite the panel parser.",
            outcome=(
                "Added | json and line_format; VL still returns unexpected token {. "
                "Late read of loki-gate.yaml URL. Handoff OBS-4421."
            ),
            obs1='[{"uid":"gate-vl-parser","title":"gate board VL parser"}]',
            obs2='[{"expr":"{app=\\"gate-board-svc\\"} |= \\"board_fail\\"","datasource":"loki-gate"}]',
            obs3='{"error":"unexpected token {","logs":[]}',
            obs4='"{app=\\"gate-board-svc\\"} |= \\"board_fail\\""\n# blamed parser, not datasource type',
            obs5="panel expr uses LogQL selector + |= filter",
            obs6="grafana/dashboards/gate-board.json expr is LogQL — treated as parser bug",
            obs7="patched expr to | json | status>=500",
            obs8='deployment "grafana" successfully rolled out',
            obs9='{"error":"unexpected token {","logs":[]}',
            obs10="patched added line_format",
            obs11='{"error":"unexpected token {","logs":[]}',
            obs12="grafana/datasources/loki-gate.yaml:\n  type: loki\n  url: http://victorialogs:9428/select/logsql/query",
            obs13="no",
            obs14="wrote tickets/OBS-4421.md",
            obs15="xfail tests/test_gate_vl_parser.py",
        ),
    )
)


# ---------------------------------------------------------------------------
# r162 Sentry event_id vs Tempo trace_id
# ---------------------------------------------------------------------------
PAIRS.append(
    (
        _ok(
            slug="sentry-eventid-vs-tempo-tid",
            service="loyalty-points-svc",
            dashboard_uid="loy-sentry-03",
            panel="trace join",
            query='{resource.service.name="loyalty-points-svc"}',
            lie="Grafana traces panel looks up Sentry event_id in Tempo; event_id is not the W3C trace_id",
            false_lead="Tempo metrics-generator missing service dimension",
            config_path="tempo/values.yaml",
            lie_path="grafana/dashboards/loy-sentry-03.json",
            truth_name="Tempo TraceQL by OTel trace_id",
            reload_name="grafana",
            side="Sentry issues still link via sentry-trace header",
            surfaces="Sentry event_id vs Tempo W3C trace_id",
            avoided="r109-r158 Tempo metrics-generator missing dim, tailsampling cache, OTel tail wait",
            this_is="Sentry event_id used as Tempo trace lookup",
            step_note="False lead Tempo spanmetrics dim 4-5; event_id vs trace_id 6-8; dashboard var 9-12.",
            search_cmd="curl -sS $GRAFANA/api/search?query=loy-sentry-03 | jq -c '.[]|{uid,title}'",
            dash_cmd="curl -sS $GRAFANA/api/dashboards/uid/loy-sentry-03 | jq '.dashboard.templating.list[]|{name,query}'",
            query_cmd="curl -sS -G $TEMPO/api/traces --data-urlencode 'traceID=${sentry_event_id}' | jq '{error,batches}'",
            false_cmd="curl -sS -G $MIMIR/prometheus/api/v1/query --data-urlencode 'query=traces_spanmetrics_calls_total{service=\"loyalty-points-svc\"}' | jq '.data.result[0].metric'",
            truth_cmd="curl -sS -G $TEMPO/api/search --data-urlencode 'q={resource.service.name=\"loyalty-points-svc\"}' | jq '.traces[:2]'",
            confirm_cmd="jq '.dashboard.panels[]|select(.type==\"traces\")' grafana/dashboards/loy-sentry-03.json",
            reload_cmd="kubectl -n grafana rollout restart deploy/grafana && kubectl -n grafana rollout status deploy/grafana --timeout=90s",
            requery_cmd="curl -sS $TEMPO/api/traces/4bf92f3577b34da6a3ce929d0e0e4736 | jq '{rootServiceName:.[0].rootServiceName,spanCount}'",
            grafana_ok_cmd="curl -sS $GRAFANA/api/ds/query -d @/tmp/loy-trace.json | jq '.results.A.frames[0].schema'",
            side_cmd="curl -sS $SENTRY/api/0/projects/airline/loyalty-points-svc/events/ | jq '.[0].{id,tags}'",
            final_cmd="jq '.dashboard.templating.list[]|{name,regex}' grafana/dashboards/loy-sentry-03.json",
            patch_old='"query": "sentry_event_id"',
            patch_new='"query": "otel_trace_id"\n          "regex": "([0-9a-f]{32})"',
            runbook_path="runbooks/loyalty-sentry-tempo-tid.md",
            runbook=(
                "# loyalty-points-svc Sentry vs Tempo\n"
                "Do not use Sentry event_id as Tempo traceID. Use W3C trace_id from OTel "
                "and sentry-trace header (trace_id-span_id-sampled).\n"
            ),
            goal=(
                "loyalty-points-svc dashboard loy-sentry-03 trace join is empty. "
                "Sentry shows events; Tempo has traces. Fix the id join."
            ),
            plan="Dashboard vars → Tempo lookup of event_id → reject spanmetrics-dim lead → switch var to otel_trace_id.",
            outcome=(
                "Templating now uses otel_trace_id (32 hex). Trace panel loads 41 spans. "
                "Sentry issues remain; they still carry sentry-trace."
            ),
            obs1='[{"uid":"loy-sentry-03","title":"loyalty trace join"}]',
            obs2='{"name":"sentry_event_id","query":"label_values(sentry_event_id)"}\n{"name":"service","query":"loyalty-points-svc"}',
            obs3='{"error":"trace not found","batches":null}\n# Tempo has no trace named after Sentry event id',
            obs4=(
                '{"service":"loyalty-points-svc","span_name":"POST /points","status":"ok"}\n'
                "# spanmetrics HAS service dim — banned missing-dim plant is not this"
            ),
            obs5="metricsGenerator.processor.span_metrics.dimensions already includes service.name — not missing",
            obs6=(
                "templating.list: sentry_event_id from Loki field sentry_event_id\n"
                "traces panel: traceId=${sentry_event_id} datasource=tempo-loyalty"
            ),
            obs7=(
                '{"traceID":"4bf92f3577b34da6a3ce929d0e0e4736","rootServiceName":"loyalty-points-svc",'
                '"spanCount":41}\n# Tempo search by service works'
            ),
            obs8='{"type":"traces","targets":[{"query":"${sentry_event_id}","queryType":"traceId"}]}',
            obs9="patched templating query sentry_event_id → otel_trace_id",
            obs10='deployment "grafana" successfully rolled out',
            obs11='{"rootServiceName":"loyalty-points-svc","spanCount":41}',
            obs12='{"name":"Trace","fields":[{"name":"traceID"},{"name":"spanID"},{"name":"duration"}]}',
            obs13='{"id":"a1b2c3d4e5f60718293a4b5c6d7e8f90","tags":[{"key":"trace","value":"4bf92f3577b34da6a3ce929d0e0e4736"}]}',
            obs14="wrote runbooks/loyalty-sentry-tempo-tid.md",
            obs15='{"name":"otel_trace_id","regex":"([0-9a-f]{32})"}\n# loy-sentry-03 join works',
        ),
        _fail(
            slug="sentry-sample-rate-not-tid",
            service="miles-burn-svc",
            dashboard_uid="miles-sentry-ds",
            panel="burn trace",
            query='{resource.service.name="miles-burn-svc"}',
            lie="Sentry tracesSampleRate cannot mint Tempo trace ids; dashboard still looks up event_id",
            false_lead="Sentry Dynamic Sampling dropping Tempo-compatible traces",
            config_path="sentry/miles-sdk.json",
            lie_path="grafana/dashboards/miles-sentry-ds.json",
            wrong_path="sentry/miles-sdk.json",
            reload_name="miles-burn-svc",
            ticket="OBS-4422",
            xfail="tests/test_miles_sentry_tid.py",
            surfaces="Sentry sample rate vs Tempo lookup key",
            avoided="r109-r158 Tempo missing dim",
            this_is="fail/handoff: tracesSampleRate=1, Tempo still 404s event_id",
            step_note="Sample rate 6-10; still 404 11; late dashboard var 12; handoff 14-15.",
            next_note="Next: Datadog _dd.p.tid 128-bit vs OTel 64-bit, not OTTL truncate.",
            search_cmd="curl -sS $GRAFANA/api/search?query=miles-sentry-ds | jq -c '.[]|{uid,title}'",
            dash_cmd="curl -sS $GRAFANA/api/dashboards/uid/miles-sentry-ds | jq '.dashboard.panels[0]'",
            query_cmd="curl -sS $TEMPO/api/traces/c0ffee00c0ffee00c0ffee00c0ffee00 | jq .message",
            false_cmd="jq '.tracesSampleRate,.profilesSampleRate' sentry/miles-sdk.json",
            reload_cmd="kubectl -n loyalty rollout restart deploy/miles-burn-svc && kubectl -n loyalty rollout status deploy/miles-burn-svc --timeout=90s",
            requery_cmd="curl -sS $TEMPO/api/traces/c0ffee00c0ffee00c0ffee00c0ffee00 | jq .message",
            denied_cmd="kubectl -n grafana auth can-i patch configmap/grafana-dashboards --as=sre-bot",
            xfail_cmd="printf '%s\\n' '@pytest.mark.xfail(reason=\"dashboard var owned by loyalty-obs\")\\ndef test_miles_sentry_tid():\\n    assert False' > tests/test_miles_sentry_tid.py",
            wrong_old='"tracesSampleRate": 0.1',
            wrong_new='"tracesSampleRate": 1.0',
            wrong2_old='"profilesSampleRate": 0.0',
            wrong2_new='"profilesSampleRate": 1.0',
            ticket_path="tickets/OBS-4422.md",
            ticket_body=(
                "OBS-4422: miles-burn-svc Tempo 404s because Grafana uses Sentry event_id. "
                "Sampling is not the join key. Need dashboard var change; no RBAC.\n"
            ),
            goal="miles-burn-svc dashboard miles-sentry-ds burn trace is empty. Make Tempo return the span tree.",
            plan="Raise Sentry tracesSampleRate so Tempo 'gets' the traces.",
            outcome=(
                "tracesSampleRate=1 and profilesSampleRate=1; Tempo still 404s the event_id. "
                "Late read of miles-sentry-ds.json templating. Handoff OBS-4422."
            ),
            obs1='[{"uid":"miles-sentry-ds","title":"miles burn sentry ds"}]',
            obs2='{"title":"burn trace","targets":[{"query":"${sentry_event_id}"}]}',
            obs3='"trace not found"',
            obs4="0.1\n0.0\n# blamed Dynamic Sampling",
            obs5='{"tracesSampleRate":0.1,"profilesSampleRate":0.0,"enableTracing":true}',
            obs6="sentry/miles-sdk.json sample rates — treated as RCA",
            obs7="patched tracesSampleRate 0.1 → 1.0",
            obs8='deployment "miles-burn-svc" successfully rolled out',
            obs9='"trace not found"',
            obs10="patched profilesSampleRate 0 → 1",
            obs11='"trace not found"',
            obs12='templating: sentry_event_id\ntraces panel queryType=traceId query=${sentry_event_id}',
            obs13="no",
            obs14="wrote tickets/OBS-4422.md",
            obs15="xfail tests/test_miles_sentry_tid.py",
        ),
    )
)
