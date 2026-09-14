"""Observability plants r163-r170."""

from mill_plants import _fail, _ok

MORE = []

# ---------------------------------------------------------------------------
# r163 Datadog _dd.p.tid 128-bit vs OTel 64-bit
# ---------------------------------------------------------------------------
MORE.append(
    (
        _ok(
            slug="dd-tid128-vs-otel64",
            service="pnr-split-svc",
            dashboard_uid="pnr-dd-11",
            panel="hop map",
            query='{resource.service.name="pnr-split-svc"}',
            lie="DD _dd.p.tid high 64 bits not exported; OTel/Tempo store 16-hex while Grafana looks up 32-hex from HTTP hop",
            false_lead="OTTL truncate_all on service.name",
            config_path="otelcol/pnr-transform.yaml",
            lie_path="k8s/dd-agent/pnr-split.env",
            truth_name="Tempo by 16-hex vs 32-hex",
            reload_name="pnr-split-svc",
            side="HTTP hop OTel traces remain 128-bit",
            surfaces="Datadog APM 128-bit tid vs OTel 64-bit",
            avoided="r109-r158 OTTL truncate_all, Tempo missing dim",
            this_is="DD 64-bit trace_id vs OTel 128-bit join miss",
            step_note="False lead OTTL truncate 4-5; _dd.p.tid 6-8; enable 128-bit 9-12.",
            search_cmd="curl -sS $GRAFANA/api/search?query=pnr-dd-11 | jq -c '.[]|{uid,title}'",
            dash_cmd="curl -sS $GRAFANA/api/dashboards/uid/pnr-dd-11 | jq '.dashboard.panels[]|select(.title==\"hop map\")'",
            query_cmd="curl -sS -G $TEMPO/api/search --data-urlencode 'q={resource.service.name=\"pnr-split-svc\"}' | jq '.traces[:3]|.[].traceID'",
            false_cmd="rg -n 'truncate_all|service.name' otelcol/pnr-transform.yaml",
            truth_cmd="curl -sS $TEMPO/api/traces/4bf92f3577b34da6 | jq '{len:(.traceID|length),service:.[0].rootServiceName}' ; curl -sS $TEMPO/api/traces/4bf92f3577b34da6a3ce929d0e0e4736 | jq .message",
            confirm_cmd="kubectl -n pnr exec deploy/pnr-split-svc -- env | rg 'DD_TRACE_128|DD_TRACE_PROPAGATION'",
            reload_cmd="kubectl -n pnr rollout restart deploy/pnr-split-svc && kubectl -n pnr rollout status deploy/pnr-split-svc --timeout=90s",
            requery_cmd="curl -sS -G $TEMPO/api/search --data-urlencode 'q={resource.service.name=\"pnr-split-svc\"}' | jq '[.traces[].traceID|length]|unique'",
            grafana_ok_cmd="curl -sS $GRAFANA/api/ds/query -d @/tmp/pnr-hop.json | jq '.results.A.frames[0].schema'",
            side_cmd="curl -sS -G $TEMPO/api/search --data-urlencode 'q={resource.service.name=\"pnr-http-gateway\"}' | jq '[.traces[:2][].traceID]'",
            final_cmd="kubectl -n pnr exec deploy/pnr-split-svc -- env | rg 'DD_TRACE_128'",
            patch_old="DD_TRACE_128_BIT_TRACEID_GENERATION_ENABLED=false",
            patch_new=(
                "DD_TRACE_128_BIT_TRACEID_GENERATION_ENABLED=true\n"
                "DD_TRACE_128_BIT_TRACEID_LOGGING_ENABLED=true\n"
                "DD_TRACE_PROPAGATION_STYLE=tracecontext,datadog"
            ),
            runbook_path="runbooks/pnr-dd-tid128.md",
            runbook=(
                "# pnr-split-svc Datadog vs OTel tid\n"
                "Enable DD 128-bit generation and W3C tracecontext so Tempo joins HTTP hops.\n"
                "_dd.p.tid must be propagated; do not truncate in OTTL.\n"
            ),
            goal=(
                "pnr-split-svc dashboard pnr-dd-11 hop map misses the DD-instrumented hop. "
                "HTTP OTel hop is present. Fix the trace id width lie."
            ),
            plan="Search traces → check OTTL truncate (false) → env DD 64-bit → enable 128-bit + tracecontext.",
            outcome=(
                "DD 128-bit + tracecontext enabled. Tempo traceIDs are 32 hex for pnr-split-svc. "
                "hop map shows DD and HTTP hops. Gateway traces unchanged."
            ),
            obs1='[{"uid":"pnr-dd-11","title":"PNR hop map"}]',
            obs2='{"title":"hop map","datasource":"tempo-pnr","targets":[{"query":"{resource.service.name=\\"pnr-split-svc\\"}"}]}',
            obs3='"4bf92f3577b34da6"\n"cafef00ddeadbeef"\n# 16 hex only from DD hops',
            obs4="otelcol/pnr-transform.yaml:12: # truncate_all commented out\n# no OTTL truncate_all on service.name",
            obs5="statements: []  # transform processor empty; not the banned OTTL plant",
            obs6=(
                "DD_TRACE_128_BIT_TRACEID_GENERATION_ENABLED=false\n"
                "DD_TRACE_PROPAGATION_STYLE=datadog\n"
                "DD_INSTRUMENTATION_TELEMETRY_ENABLED=false"
            ),
            obs7=(
                '{"len":16,"service":"pnr-split-svc"}\n'
                '"trace not found"  # 32-hex from HTTP hop does not find DD hop'
            ),
            obs8="DD_TRACE_128_BIT_TRACEID_GENERATION_ENABLED=false\nDD_TRACE_PROPAGATION_STYLE=datadog",
            obs9="patched k8s/dd-agent/pnr-split.env 128-bit + tracecontext",
            obs10='deployment "pnr-split-svc" successfully rolled out',
            obs11="[32]",
            obs12='{"name":"Node graph","fields":[{"name":"id"},{"name":"title"}]}',
            obs13='["4bf92f3577b34da6a3ce929d0e0e4736","aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"]',
            obs14="wrote runbooks/pnr-dd-tid128.md",
            obs15="DD_TRACE_128_BIT_TRACEID_GENERATION_ENABLED=true\nDD_TRACE_128_BIT_TRACEID_LOGGING_ENABLED=true",
        ),
        _fail(
            slug="dd-otlp-still-64bit",
            service="e-ticket-svc",
            dashboard_uid="eticket-dd-otlp",
            panel="ticket hop",
            query='{resource.service.name="e-ticket-svc"}',
            lie="DD OTLP exporter still emits 64-bit without 128-bit generation; Tempo cannot join 32-hex lookups",
            false_lead="missing OTLP exporter on dd-agent",
            config_path="k8s/dd-agent/e-ticket.env",
            lie_path="k8s/dd-agent/e-ticket.env",
            wrong_path="k8s/dd-agent/datadog.yaml",
            reload_name="dd-agent",
            ticket="OBS-4423",
            xfail="tests/test_eticket_dd_tid.py",
            surfaces="DD otlp_config vs 128-bit flag",
            avoided="r109-r158 OTTL truncate",
            this_is="fail/handoff: enabled OTLP, still 64-bit tids",
            step_note="OTLP exporter 6-10; still 16 hex 11; late env 12; handoff 14-15.",
            next_note="Next: Tempo span-metrics filter_policies skip (not missing dim).",
            search_cmd="curl -sS $GRAFANA/api/search?query=eticket-dd-otlp | jq -c '.[]|{uid,title}'",
            dash_cmd="curl -sS $GRAFANA/api/dashboards/uid/eticket-dd-otlp | jq '.dashboard.panels[0].targets'",
            query_cmd="curl -sS -G $TEMPO/api/search --data-urlencode 'q={resource.service.name=\"e-ticket-svc\"}' | jq '[.traces[].traceID|length]|unique'",
            false_cmd="rg -n 'otlp_config|otlp' k8s/dd-agent/datadog.yaml",
            reload_cmd="kubectl -n dd rollout restart daemonset/dd-agent && kubectl -n dd rollout status daemonset/dd-agent --timeout=120s",
            requery_cmd="curl -sS -G $TEMPO/api/search --data-urlencode 'q={resource.service.name=\"e-ticket-svc\"}' | jq '[.traces[].traceID|length]|unique'",
            denied_cmd="kubectl -n pnr auth can-i patch deploy/e-ticket-svc --as=sre-bot",
            xfail_cmd="printf '%s\\n' '@pytest.mark.xfail(reason=\"e-ticket env owned by ticketing-platform\")\\ndef test_eticket_dd_tid():\\n    assert False' > tests/test_eticket_dd_tid.py",
            wrong_old="otlp_config:\n  receiver:\n    protocols: {}",
            wrong_new=(
                "otlp_config:\n  receiver:\n    protocols:\n      grpc:\n        endpoint: 0.0.0.0:4317"
            ),
            wrong2_old="apm_config:\n  enabled: true",
            wrong2_new="apm_config:\n  enabled: true\n  otlp_http_port: 4318",
            ticket_path="tickets/OBS-4423.md",
            ticket_body=(
                "OBS-4423: e-ticket-svc Tempo hop map still 16-hex after OTLP enable. "
                "Need DD_TRACE_128_BIT_TRACEID_GENERATION_ENABLED on the app env. No patch RBAC.\n"
            ),
            goal="e-ticket-svc dashboard eticket-dd-otlp hop map misses OTel HTTP hops. Join traces.",
            plan="Enable DD OTLP exporter so traces land in Tempo as 128-bit.",
            outcome=(
                "OTLP receiver/port enabled on dd-agent; Tempo still stores 16-hex. "
                "Late read of e-ticket.env 128-bit=false. Handoff OBS-4423."
            ),
            obs1='[{"uid":"eticket-dd-otlp","title":"e-ticket DD OTLP"}]',
            obs2='[{"query":"{resource.service.name=\\"e-ticket-svc\\"}"}]',
            obs3="[16]",
            obs4="datadog.yaml: otlp_config.receiver.protocols: {}  # treated as missing exporter",
            obs5="DD_TRACE_128_BIT_TRACEID_GENERATION_ENABLED=false  # not read yet",
            obs6="k8s/dd-agent/datadog.yaml otlp empty — treated as RCA",
            obs7="patched otlp grpc 4317",
            obs8='daemonset "dd-agent" successfully rolled out',
            obs9="[16]",
            obs10="patched apm otlp_http_port 4318",
            obs11="[16]",
            obs12="k8s/dd-agent/e-ticket.env:\nDD_TRACE_128_BIT_TRACEID_GENERATION_ENABLED=false",
            obs13="no",
            obs14="wrote tickets/OBS-4423.md",
            obs15="xfail tests/test_eticket_dd_tid.py",
        ),
    )
)

# ---------------------------------------------------------------------------
# r164 Tempo metrics-generator filter_policies skip (NOT missing dim)
# ---------------------------------------------------------------------------
MORE.append(
    (
        _ok(
            slug="tempo-mg-filter-skip-404",
            service="crew-roster-svc",
            dashboard_uid="crew-mg-skip-4",
            panel="availability SLO",
            query='1 - (sum(rate(traces_spanmetrics_calls_total{service="crew-roster-svc",status="STATUS_CODE_ERROR"}[5m])) / sum(rate(traces_spanmetrics_calls_total{service="crew-roster-svc"}[5m])))',
            lie="metrics_generator span_metrics filter_policies skip http.status_code=404 so SLO never sees the 404 storm",
            false_lead="metrics-generator missing http.status_code dimension",
            config_path="tempo/metrics-generator.yaml",
            lie_path="tempo/metrics-generator.yaml",
            truth_name="Tempo TraceQL 404 count",
            reload_name="tempo-metrics-generator",
            side="5xx spanmetrics still emitted",
            surfaces="Tempo filter_policies skip vs missing dim",
            avoided="r109-r158 Tempo metrics-generator missing dim",
            this_is="filter_policies exclude 404 spans before series exist",
            step_note="False lead missing dim 4-5; filter_policies 6-8; drop 404 skip 9-12.",
            search_cmd="curl -sS $GRAFANA/api/search?query=crew-mg-skip-4 | jq -c '.[]|{uid,title}'",
            dash_cmd="curl -sS $GRAFANA/api/dashboards/uid/crew-mg-skip-4 | jq '.dashboard.panels[]|select(.title==\"availability SLO\")'",
            query_cmd="curl -sS -G $MIMIR/prometheus/api/v1/query --data-urlencode 'query=traces_spanmetrics_calls_total{service=\"crew-roster-svc\",http_status_code=\"404\"}'",
            false_cmd="yq '.metrics_generator.processor.span_metrics.dimensions' tempo/metrics-generator.yaml",
            truth_cmd="curl -sS -G $TEMPO/api/search --data-urlencode 'q={resource.service.name=\"crew-roster-svc\" && http.status_code=404}' | jq '{traces:(.traces|length),spans:[.traces[].spanSet.matched]}'",
            confirm_cmd="yq '.metrics_generator.processor.span_metrics.filter_policies' tempo/metrics-generator.yaml",
            reload_cmd="kubectl -n tempo rollout restart deploy/metrics-generator && kubectl -n tempo rollout status deploy/metrics-generator --timeout=90s",
            requery_cmd="curl -sS -G $MIMIR/prometheus/api/v1/query --data-urlencode 'query=sum(rate(traces_spanmetrics_calls_total{service=\"crew-roster-svc\",http_status_code=\"404\"}[5m]))'",
            grafana_ok_cmd="curl -sS $GRAFANA/api/ds/query -d @/tmp/crew-slo.json | jq '.results.A.frames[0].data.values'",
            side_cmd="curl -sS -G $MIMIR/prometheus/api/v1/query --data-urlencode 'query=traces_spanmetrics_calls_total{service=\"crew-roster-svc\",http_status_code=\"500\"}' | jq '.data.result|length'",
            final_cmd="yq '.metrics_generator.processor.span_metrics.filter_policies' tempo/metrics-generator.yaml",
            patch_old=(
                "filter_policies:\n"
                "        - include:\n"
                "            match_type: regex\n"
                "            attributes:\n"
                "              - key: http.status_code\n"
                "                value: \"[235]..\"  # skips 404"
            ),
            patch_new=(
                "filter_policies:\n"
                "        - include:\n"
                "            match_type: regex\n"
                "            attributes:\n"
                "              - key: http.status_code\n"
                "                value: \"[2-5]..\""
            ),
            runbook_path="runbooks/crew-mg-filter-skip.md",
            runbook=(
                "# crew-roster-svc Tempo filter_policies\n"
                "404s were skipped before spanmetrics series existed. SLO looked 100%.\n"
                "Include 4xx. This is skip-policy, not a missing dimension.\n"
            ),
            goal=(
                "crew-roster-svc dashboard crew-mg-skip-4 availability SLO is 100% while users "
                "hit 404 storms. Explain the metrics-generator skip, not a missing label."
            ),
            plan="Query spanmetrics 404 → check dimensions (present) → read filter_policies → include 4xx.",
            outcome=(
                "filter_policies now include 4xx. SLO dropped to 0.91 matching 404 rate. "
                "5xx series unchanged. Dimension list was already complete."
            ),
            obs1='[{"uid":"crew-mg-skip-4","title":"crew roster SLO"}]',
            obs2='{"title":"availability SLO","targets":[{"expr":"1 - (error/total)"}]}',
            obs3='{"status":"success","data":{"result":[]}}\n# no 404 series at all',
            obs4="- service.name\n- http.status_code\n- http.method\n# dimension exists — not missing dim",
            obs5="dimensions include http.status_code; intrinsic dimensions enabled",
            obs6=(
                "filter_policies:\n  - include:\n      match_type: regex\n"
                "      attributes:\n        - key: http.status_code\n          value: \"[235]..\"\n"
                "# 404 excluded from generation"
            ),
            obs7='{"traces":86,"spans":[86]}\n# Tempo has the 404 spans; metrics-generator skipped them',
            obs8='[{"include":{"match_type":"regex","attributes":[{"key":"http.status_code","value":"[235].."}]}}]',
            obs9="patched filter regex to [2-5].. so 404s generate series",
            obs10='deployment "metrics-generator" successfully rolled out',
            obs11='{"status":"success","data":{"result":[{"value":[1710000600,"12.4"]}]}}',
            obs12="[[1710000600],[0.91]]",
            obs13="3",
            obs14="wrote runbooks/crew-mg-filter-skip.md",
            obs15='[{"include":{"attributes":[{"key":"http.status_code","value":"[2-5].."}]}}]',
        ),
        _fail(
            slug="tempo-mg-add-dim-still-skip",
            service="cabin-wifi-svc",
            dashboard_uid="cabin-mg-histogram",
            panel="wifi error ratio",
            query='sum(rate(traces_spanmetrics_calls_total{service="cabin-wifi-svc",http_status_code="404"}[5m]))',
            lie="Adding http.status_code dimension does nothing while filter_policies still skip 404",
            false_lead="metrics-generator missing http.status_code dimension",
            config_path="tempo/cabin-mg.yaml",
            lie_path="tempo/cabin-mg.yaml",
            wrong_path="tempo/cabin-mg.yaml",
            reload_name="tempo-metrics-generator",
            ticket="OBS-4424",
            xfail="tests/test_cabin_mg_skip.py",
            surfaces="add-dim leftover vs filter_policies skip",
            avoided="r109-r158 Tempo missing dim as the actual RCA",
            this_is="fail/handoff: added dimension, 404 still skipped",
            step_note="Add dim 6-10; still empty 11; late filter_policies 12; handoff 14-15.",
            next_note="Next: Loki bloom-gateway skip, not SM allowlist.",
            search_cmd="curl -sS $GRAFANA/api/search?query=cabin-mg-histogram | jq -c '.[]|{uid,title}'",
            dash_cmd="curl -sS $GRAFANA/api/dashboards/uid/cabin-mg-histogram | jq '.dashboard.panels[0]'",
            query_cmd="curl -sS -G $MIMIR/prometheus/api/v1/query --data-urlencode 'query=traces_spanmetrics_calls_total{service=\"cabin-wifi-svc\",http_status_code=\"404\"}'",
            false_cmd="yq '.metrics_generator.processor.span_metrics.dimensions' tempo/cabin-mg.yaml",
            reload_cmd="kubectl -n tempo rollout restart deploy/metrics-generator && kubectl -n tempo rollout status deploy/metrics-generator --timeout=90s",
            requery_cmd="curl -sS -G $MIMIR/prometheus/api/v1/query --data-urlencode 'query=traces_spanmetrics_calls_total{service=\"cabin-wifi-svc\",http_status_code=\"404\"}'",
            denied_cmd="kubectl -n tempo auth can-i patch deploy/metrics-generator --as=sre-bot",
            xfail_cmd="printf '%s\\n' '@pytest.mark.xfail(reason=\"metrics-generator helm owned by tracing-platform\")\\ndef test_cabin_mg_skip():\\n    assert False' > tests/test_cabin_mg_skip.py",
            wrong_old="dimensions:\n          - service.name",
            wrong_new="dimensions:\n          - service.name\n          - http.status_code",
            wrong2_old="histogram_buckets: [0.1, 0.5, 1]",
            wrong2_new="histogram_buckets: [0.1, 0.5, 1, 2, 5]",
            ticket_path="tickets/OBS-4424.md",
            ticket_body=(
                "OBS-4424: cabin-wifi-svc 404 series still absent after adding dimension. "
                "filter_policies value [235].. skips 404. Need helm patch; no RBAC.\n"
            ),
            goal="cabin-wifi-svc dashboard cabin-mg-histogram error ratio is 0 during a 404 storm. Make 404s countable.",
            plan="Add the missing http.status_code dimension (the old Tempo plant).",
            outcome=(
                "Dimension and extra histogram buckets added; 404 series still empty. "
                "Late read of filter_policies. Handoff OBS-4424."
            ),
            obs1='[{"uid":"cabin-mg-histogram","title":"cabin wifi errors"}]',
            obs2='{"title":"wifi error ratio","targets":[{"expr":"sum(rate(traces_spanmetrics_calls_total{service=\\"cabin-wifi-svc\\",http_status_code=\\"404\\"}[5m]))"}]}',
            obs3='{"status":"success","data":{"result":[]}}',
            obs4="- service.name\n# treated as missing dim",
            obs5="dimensions: [service.name]  # incomplete, but not the skip",
            obs6="tempo/cabin-mg.yaml dimensions only — treated as RCA",
            obs7="patched added http.status_code dimension",
            obs8='deployment "metrics-generator" successfully rolled out',
            obs9='{"status":"success","data":{"result":[]}}',
            obs10="patched histogram buckets",
            obs11='{"status":"success","data":{"result":[]}}',
            obs12="filter_policies include http.status_code value: \"[235]..\"  # 404 skipped",
            obs13="no",
            obs14="wrote tickets/OBS-4424.md",
            obs15="xfail tests/test_cabin_mg_skip.py",
        ),
    )
)

# ---------------------------------------------------------------------------
# r165 Loki bloom skip false-negative
# ---------------------------------------------------------------------------
MORE.append(
    (
        _ok(
            slug="loki-bloom-stale-skip",
            service="inflight-menu-svc",
            dashboard_uid="menu-bloom-7",
            panel="galley errors",
            query='{app="inflight-menu-svc"} | json | route="galley"',
            lie="bloom-gateway skip_factor plus stale bloom (built before route label) skips chunks that contain the logs",
            false_lead="Loki structured metadata tenant allowlist",
            config_path="loki/bloom.yaml",
            lie_path="loki/bloom.yaml",
            truth_name="ingester query bypassing blooms",
            reload_name="loki-bloom-gateway",
            side="other tenants still use blooms",
            surfaces="Loki bloom-gateway skip vs SM allowlist",
            avoided="r109-r158 Loki SM allowlist, line_format drop",
            this_is="stale bloom false-negative skip_factor",
            step_note="False lead SM allowlist 4-5; bloom skip 6-8; rebuild+ingesters 9-12.",
            search_cmd="curl -sS $GRAFANA/api/search?query=menu-bloom-7 | jq -c '.[]|{uid,title}'",
            dash_cmd="curl -sS $GRAFANA/api/dashboards/uid/menu-bloom-7 | jq '.dashboard.panels[0].targets'",
            query_cmd="curl -sS -G http://loki-gateway.obs/loki/api/v1/query_range --data-urlencode 'query={app=\"inflight-menu-svc\"} | json | route=\"galley\"' --data-urlencode 'limit=20'",
            false_cmd="curl -sS http://loki-querier.obs:3100/config | yq '.limits_config.allow_structured_metadata,.limits_config.volume_enabled'",
            truth_cmd="curl -sS -G 'http://loki-ingester.obs:3100/loki/api/v1/query_range?query={app%3D%22inflight-menu-svc%22}' | jq '.data.result[0].values[:2]'",
            confirm_cmd="yq '.bloom_gateway,.bloom_build' loki/bloom.yaml; kubectl -n loki logs deploy/bloom-gateway --tail=20 | rg skip",
            reload_cmd="kubectl -n loki rollout restart deploy/bloom-gateway && kubectl -n loki rollout status deploy/bloom-gateway --timeout=90s",
            requery_cmd="curl -sS -G http://loki-gateway.obs/loki/api/v1/query_range --data-urlencode 'query={app=\"inflight-menu-svc\"} | json | route=\"galley\"' --data-urlencode 'limit=5'",
            grafana_ok_cmd="curl -sS $GRAFANA/api/ds/query -d @/tmp/menu-galley.json | jq '.results.A.frames[0].data.values[1]|length'",
            side_cmd="curl -sS -G http://loki-gateway.obs/loki/api/v1/query --data-urlencode 'query={app=\"checkin-core-svc\"}' | jq '.data.result|length'",
            final_cmd="yq '.bloom_gateway.enabled,.query_ingesters_within' loki/bloom.yaml",
            patch_old="skip_factor: 3\n    enabled: true",
            patch_new="skip_factor: 0\n    enabled: true\n  query_ingesters_within: 3h",
            runbook_path="runbooks/inflight-menu-bloom.md",
            runbook=(
                "# inflight-menu-svc Loki blooms\n"
                "Stale blooms plus skip_factor skipped galley chunks. Rebuild blooms; "
                "query_ingesters_within 3h as safety. Not an SM allowlist miss.\n"
            ),
            goal=(
                "inflight-menu-svc dashboard menu-bloom-7 galley errors is empty. "
                "Ingesters have the lines. Find the bloom skip."
            ),
            plan="LogQL empty → SM allowlist (false) → bloom-gateway skip logs → skip_factor=0 + ingesters.",
            outcome=(
                "skip_factor 0 and query_ingesters_within 3h. menu-bloom-7 shows galley lines. "
                "Other tenants still bloom-filtered."
            ),
            obs1='[{"uid":"menu-bloom-7","title":"inflight menu errors"}]',
            obs2='[{"expr":"{app=\\"inflight-menu-svc\\"} | json | route=\\"galley\\"","datasource":"loki-inflight"}]',
            obs3='{"status":"success","data":{"result":[]}}',
            obs4="true\ntrue\n# SM allowed globally — not allowlist drop",
            obs5="allow_structured_metadata: true  # banned SM allowlist plant not present",
            obs6=(
                "bloom_gateway:\n  enabled: true\n  skip_factor: 3\n"
                "bloom_build:\n  enabled: true\n  max_block_size: 200MB"
            ),
            obs7='[["1710000000000000000","{\\"route\\":\\"galley\\",\\"msg\\":\\"oven timeout\\"}"]]\n# ingester has lines',
            obs8=(
                "skip_factor: 3\nenabled: true\n"
                'level=info msg="skipping chunk, bloom says no match" tenant=inflight fp=0x9a2'
            ),
            obs9="patched skip_factor 3→0; query_ingesters_within 3h",
            obs10='deployment "bloom-gateway" successfully rolled out',
            obs11='{"status":"success","data":{"result":[{"stream":{"app":"inflight-menu-svc"},"values":[["1710000000000000000","oven timeout"]]}]}}',
            obs12="5",
            obs13="12",
            obs14="wrote runbooks/inflight-menu-bloom.md",
            obs15="true\n3h",
        ),
        _fail(
            slug="loki-bloom-rebuild-tsdb-only",
            service="duty-free-svc",
            dashboard_uid="duty-bloom-compactor",
            panel="sku errors",
            query='{app="duty-free-svc"} |= "sku_miss"',
            lie="Rebuilding TSDB index does not rebuild stale blooms; bloom-gateway still skips",
            false_lead="compacted TSDB index missing the stream",
            config_path="loki/compactor.yaml",
            lie_path="loki/duty-bloom.yaml",
            wrong_path="loki/compactor.yaml",
            reload_name="loki-compactor",
            ticket="OBS-4425",
            xfail="tests/test_duty_bloom.py",
            surfaces="compactor apply vs bloom rebuild",
            avoided="r109-r158 Loki SM allowlist, Thanos compact overlap",
            this_is="fail/handoff: compacted TSDB, blooms still skip",
            step_note="Compactor 6-10; still empty 11; late bloom yaml 12; handoff 14-15.",
            next_note="Next: OTel spanmetrics connector vs processor metric names.",
            search_cmd="curl -sS $GRAFANA/api/search?query=duty-bloom-compactor | jq -c '.[]|{uid,title}'",
            dash_cmd="curl -sS $GRAFANA/api/dashboards/uid/duty-bloom-compactor | jq '.dashboard.panels[0]'",
            query_cmd="curl -sS -G http://loki-gateway.obs/loki/api/v1/query --data-urlencode 'query={app=\"duty-free-svc\"} |= \"sku_miss\"'",
            false_cmd="kubectl -n loki logs deploy/compactor --tail=15 | rg 'tsdb|compact'",
            reload_cmd="kubectl -n loki rollout restart deploy/compactor && kubectl -n loki rollout status deploy/compactor --timeout=90s",
            requery_cmd="curl -sS -G http://loki-gateway.obs/loki/api/v1/query --data-urlencode 'query={app=\"duty-free-svc\"} |= \"sku_miss\"'",
            denied_cmd="kubectl -n loki auth can-i patch deploy/bloom-gateway --as=sre-bot",
            xfail_cmd="printf '%s\\n' '@pytest.mark.xfail(reason=\"bloom-gateway helm owned by logging-platform\")\\ndef test_duty_bloom():\\n    assert False' > tests/test_duty_bloom.py",
            wrong_old="apply_retention_interval: 24h",
            wrong_new="apply_retention_interval: 1h\n    working_directory: /data/compactor",
            wrong2_old="compaction_interval: 10m",
            wrong2_new="compaction_interval: 1m",
            ticket_path="tickets/OBS-4425.md",
            ticket_body=(
                "OBS-4425: duty-free-svc sku_miss still empty after TSDB compact. "
                "bloom-gateway skip_factor=4 stale blooms. Need bloom rebuild; no RBAC.\n"
            ),
            goal="duty-free-svc dashboard duty-bloom-compactor sku errors is empty. Restore the lines.",
            plan="Force Loki compact so the TSDB index includes the stream.",
            outcome=(
                "Compactor interval tightened; LogQL still empty. Late bloom.yaml skip_factor=4. "
                "Handoff OBS-4425."
            ),
            obs1='[{"uid":"duty-bloom-compactor","title":"duty free sku"}]',
            obs2='{"title":"sku errors","targets":[{"expr":"{app=\\"duty-free-svc\\"} |= \\"sku_miss\\""}]}',
            obs3='{"status":"success","data":{"result":[]}}',
            obs4='msg="compacting table" table=index_19991\n# blamed missing TSDB stream',
            obs5="compactor apply_retention_interval: 24h",
            obs6="loki/compactor.yaml — treated as RCA",
            obs7="patched apply_retention_interval 24h→1h",
            obs8='deployment "compactor" successfully rolled out',
            obs9='{"status":"success","data":{"result":[]}}',
            obs10="patched compaction_interval 10m→1m",
            obs11='{"status":"success","data":{"result":[]}}',
            obs12="loki/duty-bloom.yaml bloom_gateway.skip_factor=4 enabled=true\nlogs: skipping chunk, bloom says no match tenant=duty",
            obs13="no",
            obs14="wrote tickets/OBS-4425.md",
            obs15="xfail tests/test_duty_bloom.py",
        ),
    )
)

# ---------------------------------------------------------------------------
# r166 OTel spanmetrics connector vs processor
# ---------------------------------------------------------------------------
MORE.append(
    (
        _ok(
            slug="otel-spanmetrics-connector-name",
            service="ssr-meal-svc",
            dashboard_uid="ssr-conn-2",
            panel="call rate",
            query='sum(rate(calls_total{service_name="ssr-meal-svc"}[5m]))',
            lie="spanmetrics processor metric calls_total gone; connector emits traces_span_metrics_calls_total with span.name",
            false_lead="OTel tail_sampling decision_wait dropping spans before metrics",
            config_path="otelcol/ssr-collector.yaml",
            lie_path="grafana/dashboards/ssr-conn-2.json",
            truth_name="Mimir connector metric names",
            reload_name="grafana",
            side="processor pipeline fully removed, no double-count",
            surfaces="OTel spanmetrics connector vs processor names",
            avoided="r109-r158 OTel tail decision_wait, tailsampling cache",
            this_is="connector metric rename after processor removal",
            step_note="False lead tail wait 4-5; connector names 6-8; PromQL 9-12.",
            search_cmd="curl -sS $GRAFANA/api/search?query=ssr-conn-2 | jq -c '.[]|{uid,title}'",
            dash_cmd="curl -sS $GRAFANA/api/dashboards/uid/ssr-conn-2 | jq '.dashboard.panels[0].targets'",
            query_cmd="curl -sS -G $MIMIR/prometheus/api/v1/query --data-urlencode 'query=sum(rate(calls_total{service_name=\"ssr-meal-svc\"}[5m]))'",
            false_cmd="yq '.processors.tail_sampling,.service.pipelines.traces' otelcol/ssr-collector.yaml",
            truth_cmd="curl -sS -G $MIMIR/prometheus/api/v1/label/__name__/values | jq '.data[]|select(test(\"span_metrics|calls_total\"))'",
            confirm_cmd="yq '.connectors,.service.pipelines' otelcol/ssr-collector.yaml",
            reload_cmd="kubectl -n grafana rollout restart deploy/grafana && kubectl -n grafana rollout status deploy/grafana --timeout=90s",
            requery_cmd="curl -sS -G $MIMIR/prometheus/api/v1/query --data-urlencode 'query=sum(rate(traces_span_metrics_calls_total{service_name=\"ssr-meal-svc\"}[5m]))'",
            grafana_ok_cmd="curl -sS $GRAFANA/api/ds/query -d @/tmp/ssr-calls.json | jq '.results.A.frames[0].data.values'",
            side_cmd="curl -sS -G $MIMIR/prometheus/api/v1/query --data-urlencode 'query=calls_total{service_name=\"ssr-meal-svc\"}' | jq '.data.result|length'",
            final_cmd="jq '.dashboard.panels[0].targets[0].expr' grafana/dashboards/ssr-conn-2.json",
            patch_old='sum(rate(calls_total{service_name="ssr-meal-svc"}[5m]))',
            patch_new='sum(rate(traces_span_metrics_calls_total{service_name="ssr-meal-svc"}[5m]))',
            runbook_path="runbooks/ssr-spanmetrics-connector.md",
            runbook=(
                "# ssr-meal-svc connector vs processor\n"
                "After migrating to spanmetrics connector, PromQL must use "
                "traces_span_metrics_calls_total / span.name. Processor calls_total is gone.\n"
            ),
            goal=(
                "ssr-meal-svc dashboard ssr-conn-2 call rate is empty after collector upgrade. "
                "Traces still land in Tempo. Fix the metric name lie."
            ),
            plan="Query calls_total empty → tail_sampling (absent) → list new metric names → patch panel.",
            outcome=(
                "Panel now queries traces_span_metrics_calls_total. Call rate 42.1/s. "
                "calls_total series count 0 (no double-count)."
            ),
            obs1='[{"uid":"ssr-conn-2","title":"SSR meal call rate"}]',
            obs2='[{"expr":"sum(rate(calls_total{service_name=\\"ssr-meal-svc\\"}[5m]))"}]',
            obs3='{"status":"success","data":{"result":[]}}',
            obs4="null\ntraces: receivers[otlp] processors[batch] exporters[otlp/tempo, spanmetrics]\n# no tail_sampling",
            obs5="processors.tail_sampling: null  # banned tail wait not present",
            obs6=(
                "connectors:\n  spanmetrics:\n    namespace: traces.span.metrics\n"
                "    histogram:\n      unit: ms\n"
                "service.pipelines.traces.exporters: [otlp/tempo, spanmetrics]\n"
                "service.pipelines.metrics.receivers: [spanmetrics]"
            ),
            obs7='"traces_span_metrics_calls_total"\n"traces_span_metrics_duration_milliseconds_bucket"\n# no calls_total',
            obs8="spanmetrics connector namespace traces.span.metrics; processor spanmetrics removed",
            obs9="patched panel expr to traces_span_metrics_calls_total",
            obs10='deployment "grafana" successfully rolled out',
            obs11='{"status":"success","data":{"result":[{"value":[1710000600,"42.1"]}]}}',
            obs12="[[1710000600],[42.1]]",
            obs13="0",
            obs14="wrote runbooks/ssr-spanmetrics-connector.md",
            obs15='"sum(rate(traces_span_metrics_calls_total{service_name=\\"ssr-meal-svc\\"}[5m]))"',
        ),
        _fail(
            slug="otel-spanmetrics-enable-both",
            service="special-meal-svc",
            dashboard_uid="special-conn-dup",
            panel="special call rate",
            query='sum(rate(calls_total{service_name="special-meal-svc"}[5m]))',
            lie="Re-enabling spanmetrics processor duplicates series but dashboard still queries old name on a pipeline that no longer exports it",
            false_lead="connector not wired into metrics pipeline",
            config_path="otelcol/special-collector.yaml",
            lie_path="grafana/dashboards/special-conn-dup.json",
            wrong_path="otelcol/special-collector.yaml",
            reload_name="otelcol-special",
            ticket="OBS-4426",
            xfail="tests/test_special_spanmetrics.py",
            surfaces="re-enable processor leftover vs dashboard name",
            avoided="r109-r158 OTel tail wait",
            this_is="fail/handoff: enabled processor+connector, panel still empty",
            step_note="Re-enable processor 6-10; still empty 11; late dashboard 12; handoff 14-15.",
            next_note="Next: Pyroscope max_profile_size skip, not eBPF+Java mix.",
            search_cmd="curl -sS $GRAFANA/api/search?query=special-conn-dup | jq -c '.[]|{uid,title}'",
            dash_cmd="curl -sS $GRAFANA/api/dashboards/uid/special-conn-dup | jq '.dashboard.panels[0]'",
            query_cmd="curl -sS -G $MIMIR/prometheus/api/v1/query --data-urlencode 'query=sum(rate(calls_total{service_name=\"special-meal-svc\"}[5m]))'",
            false_cmd="yq '.service.pipelines.metrics' otelcol/special-collector.yaml",
            reload_cmd="kubectl -n otel rollout restart deploy/otelcol-special && kubectl -n otel rollout status deploy/otelcol-special --timeout=90s",
            requery_cmd="curl -sS -G $MIMIR/prometheus/api/v1/query --data-urlencode 'query=sum(rate(calls_total{service_name=\"special-meal-svc\"}[5m]))'",
            denied_cmd="kubectl -n grafana auth can-i patch configmap/grafana-dashboards --as=sre-bot",
            xfail_cmd="printf '%s\\n' '@pytest.mark.xfail(reason=\"dashboard owned by catering-obs\")\\ndef test_special_spanmetrics():\\n    assert False' > tests/test_special_spanmetrics.py",
            wrong_old="processors:\n  batch: {}",
            wrong_new="processors:\n  batch: {}\n  spanmetrics:\n    metrics_exporter: prometheus",
            wrong2_old="exporters: [otlp/tempo, spanmetrics]",
            wrong2_new="exporters: [otlp/tempo, spanmetrics]\n        processors: [spanmetrics, batch]",
            ticket_path="tickets/OBS-4426.md",
            ticket_body=(
                "OBS-4426: special-meal-svc still queries calls_total. Connector emits "
                "traces_span_metrics_calls_total. Re-enabling processor did not fill the panel. No dashboard RBAC.\n"
            ),
            goal="special-meal-svc dashboard special-conn-dup call rate is empty after collector upgrade. Restore the rate.",
            plan="Re-enable spanmetrics processor so calls_total comes back.",
            outcome=(
                "Processor re-enabled alongside connector; calls_total still empty for this service "
                "(processor not in metrics exporter path). Late dashboard expr. Handoff OBS-4426."
            ),
            obs1='[{"uid":"special-conn-dup","title":"special meal calls"}]',
            obs2='{"title":"special call rate","targets":[{"expr":"sum(rate(calls_total{service_name=\\"special-meal-svc\\"}[5m]))"}]}',
            obs3='{"status":"success","data":{"result":[]}}',
            obs4="receivers: [spanmetrics]\nexporters: [otlphttp/mimir]\n# connector already wired",
            obs5="metrics pipeline has spanmetrics connector receiver",
            obs6="otelcol/special-collector.yaml processors only batch — treated as missing processor",
            obs7="patched added spanmetrics processor",
            obs8='deployment "otelcol-special" successfully rolled out',
            obs9='{"status":"success","data":{"result":[]}}',
            obs10="patched traces processors to include spanmetrics",
            obs11='{"status":"success","data":{"result":[]}}',
            obs12='grafana/dashboards/special-conn-dup.json still expr=calls_total; Mimir has traces_span_metrics_calls_total',
            obs13="no",
            obs14="wrote tickets/OBS-4426.md",
            obs15="xfail tests/test_special_spanmetrics.py",
        ),
    )
)

# ---------------------------------------------------------------------------
# r167 Pyroscope max profile size skip (NOT eBPF+Java, NOT godeltaprof)
# ---------------------------------------------------------------------------
MORE.append(
    (
        _ok(
            slug="pyro-max-profile-size",
            service="weight-balance-svc",
            dashboard_uid="wb-pyro-6",
            panel="CPU profile",
            query='process_cpu:cpu:nanoseconds{service_name="weight-balance-svc"}',
            lie="pyroscope ingestion.max_profile_size_bytes 4MiB drops 6.2MiB Go heap pprof; dashboard No data",
            false_lead="eBPF + Java pprof mix / godeltaprof double count",
            config_path="pyroscope/values.yaml",
            lie_path="pyroscope/values.yaml",
            truth_name="distributor drop reason",
            reload_name="pyroscope-distributor",
            side="other services under 4MiB still profile",
            surfaces="Pyroscope max_profile_size vs eBPF mix",
            avoided="r109-r158 Pyroscope eBPF+Java pprof mix, godeltaprof+heap double count",
            this_is="max_profile_size skip of large Go pprof",
            step_note="False lead eBPF mix 4-5; max size 6-8; raise+strip 9-12.",
            search_cmd="curl -sS $GRAFANA/api/search?query=wb-pyro-6 | jq -c '.[]|{uid,title}'",
            dash_cmd="curl -sS $GRAFANA/api/dashboards/uid/wb-pyro-6 | jq '.dashboard.panels[0]'",
            query_cmd="curl -sS -G $PYRO/pyroscope/render --data-urlencode 'query=process_cpu:cpu:nanoseconds{service_name=\"weight-balance-svc\"}' --data-urlencode 'from=now-1h'",
            false_cmd="kubectl -n pyro get pods -l app=pyroscope-ebpf -o name; curl -sS $PYRO/querier.v1.QuerierService/LabelNames -d '{\"matchers\":[\"{service_name=\\\"weight-balance-svc\\\"}\"]}'",
            truth_cmd="kubectl -n pyro logs deploy/pyroscope-distributor --tail=30 | rg 'max_profile|dropped|weight-balance'",
            confirm_cmd="yq '.pyroscope.structuredConfig.ingestion' pyroscope/values.yaml",
            reload_cmd="kubectl -n pyro rollout restart deploy/pyroscope-distributor && kubectl -n pyro rollout status deploy/pyroscope-distributor --timeout=90s",
            requery_cmd="curl -sS -G $PYRO/pyroscope/render --data-urlencode 'query=process_cpu:cpu:nanoseconds{service_name=\"weight-balance-svc\"}' --data-urlencode 'from=now-15m' | jq '{flamebearer:(.flamebearer.names|length),bytes}'",
            grafana_ok_cmd="curl -sS $GRAFANA/api/ds/query -d @/tmp/wb-cpu.json | jq '.results.A.frames[0].schema'",
            side_cmd="curl -sS -G $PYRO/pyroscope/render --data-urlencode 'query=process_cpu:cpu:nanoseconds{service_name=\"checkin-core-svc\"}' | jq '.flamebearer.names|length'",
            final_cmd="yq '.pyroscope.structuredConfig.ingestion.max_profile_size_bytes' pyroscope/values.yaml",
            patch_old="max_profile_size_bytes: 4194304",
            patch_new="max_profile_size_bytes: 16777216\n      pprof_strip: true",
            runbook_path="runbooks/weight-balance-pyro-size.md",
            runbook=(
                "# weight-balance-svc Pyroscope size skip\n"
                "6.2MiB heap pprof exceeded 4MiB. Raise limit and strip sample types. "
                "Not eBPF/Java mix and not godeltaprof double count.\n"
            ),
            goal=(
                "weight-balance-svc dashboard wb-pyro-6 CPU profile is No data. "
                "Other services render. Find the ingest skip."
            ),
            plan="Render empty → eBPF mix (false) → distributor drop max_profile_size → raise + strip.",
            outcome=(
                "max_profile_size 16MiB + pprof_strip. Flamegraph 184 names. "
                "checkin-core-svc still renders. No eBPF change."
            ),
            obs1='[{"uid":"wb-pyro-6","title":"weight-balance CPU"}]',
            obs2='{"title":"CPU profile","datasource":"pyroscope-wb","targets":[{"query":"process_cpu:cpu:nanoseconds{service_name=\\"weight-balance-svc\\"}"}]}',
            obs3='{"flamebearer":{"names":[],"levels":[]},"error":"no data"}',
            obs4="No resources found\n{\"names\":[\"service_name\"]}\n# no eBPF daemon; not Java pprof mix",
            obs5="ebpf not installed in pyro ns; godeltaprof not on this service",
            obs6="ingestion:\n  max_profile_size_bytes: 4194304\n  rate_strategy: global",
            obs7='msg="dropped profile" reason=max_profile_size service=weight-balance-svc size=6501171 limit=4194304',
            obs8="max_profile_size_bytes: 4194304",
            obs9="patched max_profile_size 4MiB→16MiB; pprof_strip true",
            obs10='deployment "pyroscope-distributor" successfully rolled out',
            obs11='{"flamebearer":184,"bytes":190221}',
            obs12='{"name":"Flamegraph","fields":[{"name":"level"},{"name":"value"}]}',
            obs13="96",
            obs14="wrote runbooks/weight-balance-pyro-size.md",
            obs15="16777216",
        ),
        _fail(
            slug="pyro-scrape-interval-not-size",
            service="fuel-plan-svc",
            dashboard_uid="fuel-pyro-scrape",
            panel="fuel CPU",
            query='process_cpu:cpu:nanoseconds{service_name="fuel-plan-svc"}',
            lie="Changing scrape interval does not stop max_profile_size drops of 5.4MiB profiles",
            false_lead="Pyroscope scrape interval too long so profiles expire",
            config_path="k8s/fuel-plan/pyro-scrape.yaml",
            lie_path="pyroscope/fuel-values.yaml",
            wrong_path="k8s/fuel-plan/pyro-scrape.yaml",
            reload_name="fuel-plan-svc",
            ticket="OBS-4427",
            xfail="tests/test_fuel_pyro_size.py",
            surfaces="scrape interval leftover vs max_profile_size",
            avoided="r109-r158 godeltaprof+heap, eBPF+Java mix",
            this_is="fail/handoff: faster scrape, still dropped for size",
            step_note="Scrape 6-10; still empty 11; late distributor log 12; handoff 14-15.",
            next_note="Next: Grafana IRM wait vs AM group_wait, not AM inhibit.",
            search_cmd="curl -sS $GRAFANA/api/search?query=fuel-pyro-scrape | jq -c '.[]|{uid,title}'",
            dash_cmd="curl -sS $GRAFANA/api/dashboards/uid/fuel-pyro-scrape | jq '.dashboard.panels[0]'",
            query_cmd="curl -sS -G $PYRO/pyroscope/render --data-urlencode 'query=process_cpu:cpu:nanoseconds{service_name=\"fuel-plan-svc\"}'",
            false_cmd="cat k8s/fuel-plan/pyro-scrape.yaml",
            reload_cmd="kubectl -n fuel rollout restart deploy/fuel-plan-svc && kubectl -n fuel rollout status deploy/fuel-plan-svc --timeout=90s",
            requery_cmd="curl -sS -G $PYRO/pyroscope/render --data-urlencode 'query=process_cpu:cpu:nanoseconds{service_name=\"fuel-plan-svc\"}'",
            denied_cmd="kubectl -n pyro auth can-i patch deploy/pyroscope-distributor --as=sre-bot",
            xfail_cmd="printf '%s\\n' '@pytest.mark.xfail(reason=\"pyroscope helm owned by profiling-platform\")\\ndef test_fuel_pyro_size():\\n    assert False' > tests/test_fuel_pyro_size.py",
            wrong_old="scrape_interval: 15s",
            wrong_new="scrape_interval: 5s",
            wrong2_old="scrape_timeout: 10s",
            wrong2_new="scrape_timeout: 4s",
            ticket_path="tickets/OBS-4427.md",
            ticket_body=(
                "OBS-4427: fuel-plan-svc profiles still dropped max_profile_size=4MiB size=5400000. "
                "Scrape interval change irrelevant. Need distributor limit; no RBAC.\n"
            ),
            goal="fuel-plan-svc dashboard fuel-pyro-scrape CPU is No data. Restore the flamegraph.",
            plan="Shorten pyro scrape interval so profiles do not expire.",
            outcome=(
                "scrape_interval 5s; still No data. Late distributor log max_profile_size. "
                "Handoff OBS-4427."
            ),
            obs1='[{"uid":"fuel-pyro-scrape","title":"fuel plan CPU"}]',
            obs2='{"title":"fuel CPU","datasource":"pyroscope-fuel"}',
            obs3='{"flamebearer":{"names":[]},"error":"no data"}',
            obs4="scrape_interval: 15s\nscrape_timeout: 10s\n# treated as expiry",
            obs5="k8s/fuel-plan/pyro-scrape.yaml interval 15s",
            obs6="same scrape yaml — treated as RCA",
            obs7="patched scrape_interval 15s→5s",
            obs8='deployment "fuel-plan-svc" successfully rolled out',
            obs9='{"flamebearer":{"names":[]},"error":"no data"}',
            obs10="patched scrape_timeout 10s→4s",
            obs11='{"flamebearer":{"names":[]},"error":"no data"}',
            obs12="pyroscope/fuel-values.yaml max_profile_size_bytes=4194304\nlogs: dropped profile reason=max_profile_size service=fuel-plan-svc size=5400000",
            obs13="no",
            obs14="wrote tickets/OBS-4427.md",
            obs15="xfail tests/test_fuel_pyro_size.py",
        ),
    )
)

# ---------------------------------------------------------------------------
# r168 Grafana IRM wait vs AM group_wait (second IRM plant, unique)
# ---------------------------------------------------------------------------
MORE.append(
    (
        _ok(
            slug="irm-wait-vs-am-groupwait",
            service="slot-auction-svc",
            dashboard_uid="slot-irm-wait-8",
            panel="time to page",
            query='histogram_quantile(0.5, oncall_notify_delay_seconds_bucket{service="slot-auction-svc"})',
            lie="IRM escalation wait 0s plus Grafana for 0s pages immediately while AM group_wait 30s has not grouped",
            false_lead="Alertmanager inhibit on auction_noise",
            config_path="helm/alertmanager/slot-route.yaml",
            lie_path="helm/grafana-irm/slot-chain.yaml",
            truth_name="IRM page timestamps vs AM group",
            reload_name="grafana-irm",
            side="AM still groups other auction alerts",
            surfaces="IRM wait vs AM group_wait",
            avoided="r109-r158 AM inhibit; r159 IRM group_by vs silence",
            this_is="IRM wait=0 vs AM group_wait=30 dual path",
            step_note="False lead inhibit 4-5; wait vs group_wait 6-8; align waits 9-12.",
            search_cmd="curl -sS $GRAFANA/api/search?query=slot-irm-wait-8 | jq -c '.[]|{uid,title}'",
            dash_cmd="curl -sS $GRAFANA/api/dashboards/uid/slot-irm-wait-8 | jq '.dashboard.panels[]|select(.title==\"time to page\")'",
            query_cmd="curl -sS -G $MIMIR/prometheus/api/v1/query --data-urlencode 'query=histogram_quantile(0.5, oncall_notify_delay_seconds_bucket{service=\"slot-auction-svc\"})'",
            false_cmd="amtool inhibit query service=slot-auction-svc --alertmanager.url=$AM",
            truth_cmd="curl -sS $IRM/api/v1/notifications?service=slot-auction-svc | jq '[.[]|{t:.created_at,wait:.escalation.wait}][:3]'",
            confirm_cmd="yq '.escalation.wait,.grafana_rule.for' helm/grafana-irm/slot-chain.yaml; yq '.group_wait' helm/alertmanager/slot-route.yaml",
            reload_cmd="kubectl -n irm rollout restart deploy/grafana-oncall && kubectl -n irm rollout status deploy/grafana-oncall --timeout=90s",
            requery_cmd="curl -sS -G $MIMIR/prometheus/api/v1/query --data-urlencode 'query=histogram_quantile(0.5, oncall_notify_delay_seconds_bucket{service=\"slot-auction-svc\"})'",
            grafana_ok_cmd="curl -sS $GRAFANA/api/ds/query -d @/tmp/slot-ttp.json | jq '.results.A.frames[0].data.values'",
            side_cmd="amtool config routes show --alertmanager.url=$AM | rg -n 'slot-auction|group_wait' | head",
            final_cmd="yq '.escalation.wait,.grafana_rule.for' helm/grafana-irm/slot-chain.yaml",
            patch_old="wait: 0s\n  grafana_rule:\n    for: 0s",
            patch_new="wait: 30s\n  grafana_rule:\n    for: 1m",
            runbook_path="runbooks/slot-irm-wait.md",
            runbook=(
                "# slot-auction-svc IRM wait vs AM group_wait\n"
                "IRM wait 0s raced AM group_wait 30s. Align IRM wait and Grafana for.\n"
                "Not inhibit, not r159 silence grouping.\n"
            ),
            goal=(
                "slot-auction-svc dashboard slot-irm-wait-8 time to page is ~0s while AM "
                "group_wait is 30s. Stop the early IRM page."
            ),
            plan="Dashboard delay → inhibit (false) → compare IRM wait vs AM group_wait → align.",
            outcome=(
                "IRM wait 30s and Grafana for 1m. Median time to page 31s. AM group_wait unchanged."
            ),
            obs1='[{"uid":"slot-irm-wait-8","title":"slot auction page latency"}]',
            obs2='{"title":"time to page","targets":[{"expr":"histogram_quantile(0.5, oncall_notify_delay_seconds_bucket{service=\\"slot-auction-svc\\"})"}]}',
            obs3='{"status":"success","data":{"result":[{"value":[1710000000,"0.4"]}]}}',
            obs4="0 rows\n# no inhibit on auction_noise",
            obs5="inhibit_rules: [] for slot-auction-svc",
            obs6="escalation:\n  wait: 0s\ngrafana_rule:\n  for: 0s\ncontact: grafana_oncall",
            obs7='[{"t":"12:00:00.2Z","wait":"0s"},{"t":"12:00:00.3Z","wait":"0s"}]\n# IRM pages at t+0',
            obs8="0s\n0s\n30s  # AM group_wait 30s, IRM 0s",
            obs9="patched IRM wait 0s→30s; grafana for 0s→1m",
            obs10='deployment "grafana-oncall" successfully rolled out',
            obs11='{"status":"success","data":{"result":[{"value":[1710000600,"31.2"]}]}}',
            obs12="[[1710000600],[31.2]]",
            obs13="slot-auction group_wait: 30s",
            obs14="wrote runbooks/slot-irm-wait.md",
            obs15="30s\n1m",
        ),
        _fail(
            slug="irm-am-groupwait-zero",
            service="curb-weight-svc",
            dashboard_uid="curb-irm-repeat",
            panel="page delay",
            query='histogram_quantile(0.5, oncall_notify_delay_seconds_bucket{service="curb-weight-svc"})',
            lie="Zeroing AM group_wait does not slow IRM wait=0 grafana_oncall pages",
            false_lead="AM group_wait too long so dashboard delay looks wrong",
            config_path="helm/alertmanager/curb-route.yaml",
            lie_path="helm/grafana-irm/curb-chain.yaml",
            wrong_path="helm/alertmanager/curb-route.yaml",
            reload_name="alertmanager",
            ticket="OBS-4428",
            xfail="tests/test_curb_irm_wait.py",
            surfaces="AM group_wait leftover vs IRM wait",
            avoided="r109-r158 AM inhibit; r159 silence group_by",
            this_is="fail/handoff: AM group_wait=0, IRM still instant",
            step_note="group_wait 6-10; still 0.3s 11; late IRM wait 12; handoff 14-15.",
            next_note="Next: Prom agent rule_files not evaluated, not remote_write queue.",
            search_cmd="curl -sS $GRAFANA/api/search?query=curb-irm-repeat | jq -c '.[]|{uid,title}'",
            dash_cmd="curl -sS $GRAFANA/api/dashboards/uid/curb-irm-repeat | jq '.dashboard.panels[0]'",
            query_cmd="curl -sS -G $MIMIR/prometheus/api/v1/query --data-urlencode 'query=histogram_quantile(0.5, oncall_notify_delay_seconds_bucket{service=\"curb-weight-svc\"})'",
            false_cmd="yq '.group_wait,.group_interval' helm/alertmanager/curb-route.yaml",
            reload_cmd="kubectl -n am rollout restart statefulset/alertmanager && kubectl -n am rollout status statefulset/alertmanager --timeout=90s",
            requery_cmd="curl -sS -G $MIMIR/prometheus/api/v1/query --data-urlencode 'query=histogram_quantile(0.5, oncall_notify_delay_seconds_bucket{service=\"curb-weight-svc\"})'",
            denied_cmd="kubectl -n irm auth can-i patch deploy/grafana-oncall --as=sre-bot",
            xfail_cmd="printf '%s\\n' '@pytest.mark.xfail(reason=\"IRM chain owned by oncall-platform\")\\ndef test_curb_irm_wait():\\n    assert False' > tests/test_curb_irm_wait.py",
            wrong_old="group_wait: 30s",
            wrong_new="group_wait: 0s",
            wrong2_old="group_interval: 5m",
            wrong2_new="group_interval: 10s",
            ticket_path="tickets/OBS-4428.md",
            ticket_body=(
                "OBS-4428: curb-weight-svc still pages at t+0 via IRM wait=0. "
                "AM group_wait=0 did not change IRM. Need IRM chain patch; no RBAC.\n"
            ),
            goal="curb-weight-svc dashboard curb-irm-repeat page delay is ~0s. Make paging wait match AM.",
            plan="Set AM group_wait to 0 so AM and IRM agree.",
            outcome=(
                "AM group_wait 0s and group_interval 10s; IRM still pages at 0.3s. "
                "Late curb-chain.yaml wait=0s. Handoff OBS-4428."
            ),
            obs1='[{"uid":"curb-irm-repeat","title":"curb weight pages"}]',
            obs2='{"title":"page delay","targets":[{"expr":"histogram_quantile(0.5, oncall_notify_delay_seconds_bucket{service=\\"curb-weight-svc\\"})"}]}',
            obs3='{"status":"success","data":{"result":[{"value":[1710000000,"0.3"]}]}}',
            obs4="30s\n5m\n# blamed AM wait",
            obs5="group_wait: 30s on AM route",
            obs6="helm/alertmanager/curb-route.yaml — treated as RCA",
            obs7="patched group_wait 30s→0s",
            obs8='statefulset "alertmanager" successfully rolled out',
            obs9='{"status":"success","data":{"result":[{"value":[1710000300,"0.3"]}]}}',
            obs10="patched group_interval 5m→10s",
            obs11='{"status":"success","data":{"result":[{"value":[1710000400,"0.3"]}]}}',
            obs12="helm/grafana-irm/curb-chain.yaml escalation.wait=0s grafana_rule.for=0s type=grafana_oncall",
            obs13="no",
            obs14="wrote tickets/OBS-4428.md",
            obs15="xfail tests/test_curb_irm_wait.py",
        ),
    )
)

# ---------------------------------------------------------------------------
# r169 Prom agent rule_files not evaluated
# ---------------------------------------------------------------------------
MORE.append(
    (
        _ok(
            slug="prom-agent-rules-noop",
            service="standby-list-svc",
            dashboard_uid="standby-agent-rules",
            panel="fill ratio",
            query="job:standby_fill:ratio5m",
            lie="Prometheus agent mode does not run rule manager; recording rules in agent rule_files never evaluate",
            false_lead="Mimir remote_write dropping the recording-rule series",
            config_path="k8s/prom-agent-standby/prometheus.yml",
            lie_path="mimir/ruler/standby.yaml",
            truth_name="Mimir ruler API",
            reload_name="mimir-ruler",
            side="agent still remote_writes raw standby metrics",
            surfaces="Prom agent rule_files vs Mimir ruler",
            avoided="r109-r158 remote_write queue; r160 agent datasource URL",
            this_is="agent rule_files never evaluate; Grafana records missing",
            step_note="False lead remote_write 4-5; agent no ruler 6-8; move rules 9-12.",
            search_cmd="curl -sS $GRAFANA/api/search?query=standby-agent-rules | jq -c '.[]|{uid,title}'",
            dash_cmd="curl -sS $GRAFANA/api/dashboards/uid/standby-agent-rules | jq '.dashboard.panels[0]'",
            query_cmd="curl -sS -G http://prom-agent-standby.obs:9090/api/v1/query --data-urlencode 'query=job:standby_fill:ratio5m'",
            false_cmd="curl -sS http://prom-agent-standby.obs:9090/metrics | rg 'prometheus_remote_storage_(samples_pending|dropped)'",
            truth_cmd="curl -sS -G http://mimir-query.obs:8080/prometheus/api/v1/query --data-urlencode 'query=standby_fill_ratio' ; curl -sS http://mimir-ruler.obs:8080/prometheus/config/v1/rules | jq 'keys'",
            confirm_cmd="rg -n 'rule_files|enable-feature' k8s/prom-agent-standby/prometheus.yml k8s/prom-agent-standby/statefulset.yaml",
            reload_cmd="kubectl -n mimir rollout restart deploy/ruler && kubectl -n mimir rollout status deploy/ruler --timeout=90s",
            requery_cmd="curl -sS -G http://mimir-query.obs:8080/prometheus/api/v1/query --data-urlencode 'query=job:standby_fill:ratio5m'",
            grafana_ok_cmd="curl -sS $GRAFANA/api/ds/query -d @/tmp/standby-fill.json | jq '.results.A.frames[0].data.values'",
            side_cmd="curl -sS -G http://mimir-query.obs:8080/prometheus/api/v1/query --data-urlencode 'query=standby_offered_total' | jq '.data.result[0].value'",
            final_cmd="curl -sS http://mimir-ruler.obs:8080/prometheus/config/v1/rules | jq '.standby.file'",
            patch_old="# mimir ruler empty for standby",
            patch_new=(
                "namespace: standby\n"
                "groups:\n"
                "  - name: standby-fill\n"
                "    interval: 15s\n"
                "    rules:\n"
                "      - record: job:standby_fill:ratio5m\n"
                "        expr: standby_filled_total / standby_offered_total"
            ),
            runbook_path="runbooks/standby-agent-rules.md",
            runbook=(
                "# standby-list-svc agent rules\n"
                "Agent mode does not evaluate recording/alerting rules. Move rule_files to Mimir ruler.\n"
                "Not a remote_write queue drop; not r160 datasource URL.\n"
            ),
            goal=(
                "standby-list-svc dashboard standby-agent-rules fill ratio is empty. "
                "Raw offered/filled series exist in Mimir. Fix the recording-rule lie."
            ),
            plan="Query record empty → remote_write (healthy) → agent has rule_files but no manager → Mimir ruler.",
            outcome=(
                "Mimir ruler evaluates job:standby_fill:ratio5m. Panel 0.74. "
                "Agent still remote_writes raw counters."
            ),
            obs1='[{"uid":"standby-agent-rules","title":"standby fill ratio"}]',
            obs2='{"title":"fill ratio","datasource":"mimir-standby","targets":[{"expr":"job:standby_fill:ratio5m"}]}',
            obs3='{"status":"success","data":{"result":[]}}\n# empty on agent too',
            obs4="prometheus_remote_storage_samples_pending 4\nprometheus_remote_storage_dropped_samples_total 0",
            obs5="remote_write healthy — not queue-full plant",
            obs6="# mimir ruler empty for standby\n# no standby namespace",
            obs7='{"status":"success","data":{"result":[]}}\n[]  # no ruler groups',
            obs8=(
                "prometheus.yml: rule_files: [standby.rules.yml]\n"
                "statefulset: --enable-feature=agent\n"
                "# agent does not run rule manager"
            ),
            obs9="patched mimir/ruler/standby.yaml with job:standby_fill:ratio5m",
            obs10='deployment "ruler" successfully rolled out',
            obs11='{"status":"success","data":{"result":[{"value":[1710000600,"0.74"]}]}}',
            obs12="[[1710000600],[0.74]]",
            obs13='["1710000600","18440"]',
            obs14="wrote runbooks/standby-agent-rules.md",
            obs15='{"file":"standby.yaml","groups":["standby-fill"]}',
        ),
        _fail(
            slug="prom-agent-copy-rules-local",
            service="upgrade-bid-svc",
            dashboard_uid="upgrade-agent-rules",
            panel="bid fill",
            query="job:upgrade_fill:ratio5m",
            lie="Copying recording rules onto the agent does not evaluate them in agent mode",
            false_lead="agent missing rule_files stanza",
            config_path="k8s/prom-agent-upgrade/prometheus.yml",
            lie_path="mimir/ruler/upgrade.yaml",
            wrong_path="k8s/prom-agent-upgrade/prometheus.yml",
            reload_name="prom-agent-upgrade",
            ticket="OBS-4429",
            xfail="tests/test_upgrade_agent_rules.py",
            surfaces="agent rule_files leftover vs Mimir ruler",
            avoided="r160 datasource URL, remote_write queue",
            this_is="fail/handoff: more agent rules, still no series",
            step_note="rule_files 6-10; still empty 11; late agent flag 12; handoff 14-15.",
            next_note="Next: VictoriaLogs _stream vs Loki parser, not SM allowlist.",
            search_cmd="curl -sS $GRAFANA/api/search?query=upgrade-agent-rules | jq -c '.[]|{uid,title}'",
            dash_cmd="curl -sS $GRAFANA/api/dashboards/uid/upgrade-agent-rules | jq '.dashboard.panels[0]'",
            query_cmd="curl -sS -G http://prom-agent-upgrade.obs:9090/api/v1/query --data-urlencode 'query=job:upgrade_fill:ratio5m'",
            false_cmd="rg -n 'rule_files' k8s/prom-agent-upgrade/prometheus.yml",
            reload_cmd="kubectl -n obs rollout restart statefulset/prom-agent-upgrade && kubectl -n obs rollout status statefulset/prom-agent-upgrade --timeout=90s",
            requery_cmd="curl -sS -G http://prom-agent-upgrade.obs:9090/api/v1/query --data-urlencode 'query=job:upgrade_fill:ratio5m'",
            denied_cmd="kubectl -n mimir auth can-i patch deploy/ruler --as=sre-bot",
            xfail_cmd="printf '%s\\n' '@pytest.mark.xfail(reason=\"mimir ruler owned by metrics-platform\")\\ndef test_upgrade_agent_rules():\\n    assert False' > tests/test_upgrade_agent_rules.py",
            wrong_old="rule_files: []",
            wrong_new="rule_files:\n  - upgrade.rules.yml",
            wrong2_old="# evaluation_interval unset",
            wrong2_new="evaluation_interval: 15s",
            ticket_path="tickets/OBS-4429.md",
            ticket_body=(
                "OBS-4429: upgrade-bid-svc recording rule still empty. Agent mode ignores rule_files. "
                "Need Mimir ruler; no RBAC.\n"
            ),
            goal="upgrade-bid-svc dashboard upgrade-agent-rules bid fill is empty. Restore the recording rule.",
            plan="Add rule_files and evaluation_interval on the agent.",
            outcome=(
                "Agent has rule_files + evaluation_interval; query still empty. "
                "Late --enable-feature=agent. Handoff OBS-4429."
            ),
            obs1='[{"uid":"upgrade-agent-rules","title":"upgrade bid fill"}]',
            obs2='{"title":"bid fill","targets":[{"expr":"job:upgrade_fill:ratio5m"}]}',
            obs3='{"status":"success","data":{"result":[]}}',
            obs4="prometheus.yml:4: rule_files: []",
            obs5="rule_files empty — treated as RCA",
            obs6="k8s/prom-agent-upgrade/prometheus.yml",
            obs7="patched rule_files: upgrade.rules.yml",
            obs8='statefulset "prom-agent-upgrade" successfully rolled out\n# log: rules disabled in agent mode',
            obs9='{"status":"success","data":{"result":[]}}',
            obs10="patched evaluation_interval 15s",
            obs11='{"status":"success","data":{"result":[]}}',
            obs12="statefulset args --enable-feature=agent; mimir/ruler/upgrade.yaml missing",
            obs13="no",
            obs14="wrote tickets/OBS-4429.md",
            obs15="xfail tests/test_upgrade_agent_rules.py",
        ),
    )
)

# ---------------------------------------------------------------------------
# r170 VictoriaLogs _stream vs Loki json parser
# ---------------------------------------------------------------------------
MORE.append(
    (
        _ok(
            slug="vl-stream-vs-loki-json",
            service="bagtag-print-svc",
            dashboard_uid="bagtag-stream-5",
            panel="print errors",
            query='{_stream="{app=\\"bagtag-print-svc\\"}"} | json | status >= 500',
            lie="Grafana Loki parser | json applied on VictoriaLogs _msg rows because datasource type is still loki",
            false_lead="Loki json parser dropping lines via line_format",
            config_path="grafana/dashboards/bagtag-print.json",
            lie_path="grafana/datasources/loki-bagtag.yaml",
            truth_name="VL LogsQL _msg",
            reload_name="grafana",
            side="core Loki json panels unchanged",
            surfaces="VL _stream + _msg vs Loki | json",
            avoided="r161 LogsQL vs LogQL language; r109-r158 line_format drop",
            this_is="VL _stream field with Loki json parser",
            step_note="False lead line_format 4-5; _stream/_msg 6-8; VL plugin 9-12.",
            search_cmd="curl -sS $GRAFANA/api/search?query=bagtag-stream-5 | jq -c '.[]|{uid,title}'",
            dash_cmd="curl -sS $GRAFANA/api/dashboards/uid/bagtag-stream-5 | jq '.dashboard.panels[0].targets'",
            query_cmd="curl -sS $GRAFANA/api/ds/query -d @/tmp/bagtag.json | jq '.results.A.error'",
            false_cmd="jq '.dashboard.panels[0].targets[0].expr' grafana/dashboards/bagtag-print.json",
            truth_cmd="curl -sS -G http://victorialogs:9428/select/logsql/query --data-urlencode 'query=_time:5m {app=\"bagtag-print-svc\"} _msg:fail'",
            confirm_cmd="cat grafana/datasources/loki-bagtag.yaml",
            reload_cmd="kubectl -n grafana rollout restart deploy/grafana && kubectl -n grafana rollout status deploy/grafana --timeout=90s",
            requery_cmd="curl -sS $GRAFANA/api/ds/query -d @/tmp/bagtag-vl.json | jq '.results.A.frames[0].schema.fields'",
            grafana_ok_cmd="curl -sS $GRAFANA/api/ds/query -d @/tmp/bagtag-vl.json | jq '.results.A.frames[0].data.values[1]|length'",
            side_cmd="curl -sS -G http://loki-gateway.obs/loki/api/v1/query --data-urlencode 'query={app=\"checkin-core-svc\"} | json' | jq '.data.result|length'",
            final_cmd="curl -sS $GRAFANA/api/datasources/uid/vl-bagtag | jq '{type,url}'",
            patch_old="type: loki\n    url: http://victorialogs:9428",
            patch_new=(
                "type: victoriametrics-logs-datasource\n    url: http://victorialogs:9428\n"
                "    uid: vl-bagtag"
            ),
            runbook_path="runbooks/bagtag-vl-stream.md",
            runbook=(
                "# bagtag-print-svc VL _stream vs Loki json\n"
                "Use VL plugin and LogsQL `_msg:fail`. Loki | json does not parse VL _msg.\n"
            ),
            goal=(
                "bagtag-print-svc dashboard bagtag-stream-5 print errors is empty. "
                "VL has _msg fail lines. Fix the parser/datasource lie."
            ),
            plan="Panel error → line_format (false) → VL _stream + loki type → VL plugin.",
            outcome=(
                "Datasource type victoriametrics-logs-datasource. Panel 7 fail lines. "
                "Core Loki json panels unchanged."
            ),
            obs1='[{"uid":"bagtag-stream-5","title":"bagtag print errors"}]',
            obs2='[{"expr":"{_stream=\\"{app=\\\\\\"bagtag-print-svc\\\\\\"}\\"} | json | status >= 500","datasource":"loki-bagtag"}]',
            obs3='"error parsing log line as json: unexpected token"',
            obs4='"{_stream=...} | json | status >= 500"\n# no line_format in expr',
            obs5="no | line_format — banned plant not this",
            obs6="type: loki\nurl: http://victorialogs:9428\n# Grafana applies Loki json on VL _msg",
            obs7='{"_time":"...","_stream":"{app=\\"bagtag-print-svc\\"}","_msg":"fail printer=P2"}\n# LogsQL works',
            obs8="type: loki url: http://victorialogs:9428",
            obs9="patched datasource type to victoriametrics-logs-datasource uid vl-bagtag",
            obs10='deployment "grafana" successfully rolled out',
            obs11='[{"name":"_time","type":"time"},{"name":"_msg","type":"string"}]',
            obs12="7",
            obs13="11",
            obs14="wrote runbooks/bagtag-vl-stream.md",
            obs15='{"type":"victoriametrics-logs-datasource","url":"http://victorialogs:9428"}',
        ),
        _fail(
            slug="vl-label-format-on-stream",
            service="tarmac-iot-svc",
            dashboard_uid="tarmac-vl-label",
            panel="sensor fails",
            query='{_stream="{app=\\"tarmac-iot-svc\\"}"} | label_format msg="{{.msg}}"',
            lie="Loki label_format does not run on VictoriaLogs; datasource type is still loki",
            false_lead="Loki label_format dropping the stream",
            config_path="grafana/dashboards/tarmac-iot.json",
            lie_path="grafana/datasources/loki-tarmac.yaml",
            wrong_path="grafana/dashboards/tarmac-iot.json",
            reload_name="grafana",
            ticket="OBS-4430",
            xfail="tests/test_tarmac_vl_parser.py",
            surfaces="label_format leftover vs VL _stream",
            avoided="r161 language mismatch; line_format drop as RCA",
            this_is="fail/handoff: label_format rewrite, VL still errors",
            step_note="label_format 6-10; still error 11; late type=loki 12; handoff 14-15.",
            next_note="Next: Sentry span op vs Tempo service graph, not missing dim.",
            search_cmd="curl -sS $GRAFANA/api/search?query=tarmac-vl-label | jq -c '.[]|{uid,title}'",
            dash_cmd="curl -sS $GRAFANA/api/dashboards/uid/tarmac-vl-label | jq '.dashboard.panels[0]'",
            query_cmd="curl -sS $GRAFANA/api/ds/query -d @/tmp/tarmac.json | jq '.results.A.error'",
            false_cmd="jq '.dashboard.panels[0].targets[0].expr' grafana/dashboards/tarmac-iot.json",
            reload_cmd="kubectl -n grafana rollout restart deploy/grafana && kubectl -n grafana rollout status deploy/grafana --timeout=90s",
            requery_cmd="curl -sS $GRAFANA/api/ds/query -d @/tmp/tarmac.json | jq '.results.A.error'",
            denied_cmd="kubectl -n grafana auth can-i patch configmap/grafana-datasources --as=sre-bot",
            xfail_cmd="printf '%s\\n' '@pytest.mark.xfail(reason=\"tarmac datasource owned by edge-obs\")\\ndef test_tarmac_vl_parser():\\n    assert False' > tests/test_tarmac_vl_parser.py",
            wrong_old='| json | status >= 500',
            wrong_new='| label_format msg="{{.msg}}"',
            wrong2_old='| label_format msg="{{.msg}}"',
            wrong2_new='| label_format msg="{{.msg}}" | line_format "{{.msg}}"',
            ticket_path="tickets/OBS-4430.md",
            ticket_body=(
                "OBS-4430: tarmac-iot-svc still errors because loki-tarmac type=loki URL=VL. "
                "label_format cannot parse _msg. Need VL plugin; no RBAC.\n"
            ),
            goal="tarmac-iot-svc dashboard tarmac-vl-label sensor fails is empty. Restore the lines.",
            plan="Rewrite Loki label_format so the stream parses.",
            outcome=(
                "label_format and line_format added; VL still returns parse error. "
                "Late loki-tarmac.yaml type=loki. Handoff OBS-4430."
            ),
            obs1='[{"uid":"tarmac-vl-label","title":"tarmac iot sensors"}]',
            obs2='{"title":"sensor fails","targets":[{"expr":"{_stream=\\"{app=\\\\\\"tarmac-iot-svc\\\\\\"}\\"} | json | status >= 500"}]}',
            obs3='"error parsing log line as json"',
            obs4='"|_stream json"\n# blamed parser',
            obs5="grafana/dashboards/tarmac-iot.json uses | json",
            obs6="same dashboard — treated as RCA",
            obs7="patched | json → | label_format",
            obs8='deployment "grafana" successfully rolled out',
            obs9='"unexpected pipeline label_format"',
            obs10="patched added line_format",
            obs11='"unexpected pipeline label_format"',
            obs12="grafana/datasources/loki-tarmac.yaml type: loki url: http://victorialogs:9428",
            obs13="no",
            obs14="wrote tickets/OBS-4430.md",
            obs15="xfail tests/test_tarmac_vl_parser.py",
        ),
    )
)
