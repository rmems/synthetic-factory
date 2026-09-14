"""Observability plants r171-r174."""

from mill_plants import _fail, _ok

MORE = []

# ---------------------------------------------------------------------------
# r171 Sentry span.op vs Tempo service-graph span.kind
# ---------------------------------------------------------------------------
MORE.append(
    (
        _ok(
            slug="sentry-op-vs-tempo-svcgraph",
            service="codeshare-svc",
            dashboard_uid="code-sentry-op-1",
            panel="service graph",
            query='{resource.service.name="codeshare-svc"}',
            lie="Sentry spans use op=http.client without span.kind/server.address so Tempo service-graphs drop edges",
            false_lead="Tempo metrics-generator missing service dimension",
            config_path="tempo/codeshare-mg.yaml",
            lie_path="sentry/codeshare-sdk.json",
            truth_name="Tempo span dump vs Sentry span op",
            reload_name="codeshare-svc",
            side="spanmetrics calls_total still present",
            surfaces="Sentry span.op vs Tempo service-graph span.kind",
            avoided="r162 event_id vs trace_id; Tempo missing dim; service-graphs wait",
            this_is="Sentry op=http.client missing OTel span.kind for Tempo SG",
            step_note="False lead missing dim 4-5; span.kind gap 6-8; OTel integration 9-12.",
            search_cmd="curl -sS $GRAFANA/api/search?query=code-sentry-op-1 | jq -c '.[]|{uid,title}'",
            dash_cmd="curl -sS $GRAFANA/api/dashboards/uid/code-sentry-op-1 | jq '.dashboard.panels[]|select(.title==\"service graph\")'",
            query_cmd="curl -sS -G $MIMIR/prometheus/api/v1/query --data-urlencode 'query=traces_service_graph_request_total{client=\"codeshare-svc\"}'",
            false_cmd="yq '.metrics_generator.processor.service_graphs.dimensions,.metrics_generator.processor.span_metrics.dimensions' tempo/codeshare-mg.yaml",
            truth_cmd="curl -sS $TEMPO/api/traces/aa11bb22cc33dd44ee55ff6677889900 | jq '[.batches[].scopeSpans[].spans[]|{name,kind,attrs:(.attributes|map(.key))}[:4]'",
            confirm_cmd="jq '{enableTracing,instrumenter,integrations}' sentry/codeshare-sdk.json",
            reload_cmd="kubectl -n share rollout restart deploy/codeshare-svc && kubectl -n share rollout status deploy/codeshare-svc --timeout=90s",
            requery_cmd="curl -sS -G $MIMIR/prometheus/api/v1/query --data-urlencode 'query=traces_service_graph_request_total{client=\"codeshare-svc\"}'",
            grafana_ok_cmd="curl -sS $GRAFANA/api/ds/query -d @/tmp/code-sg.json | jq '.results.A.frames[0].schema'",
            side_cmd="curl -sS -G $MIMIR/prometheus/api/v1/query --data-urlencode 'query=traces_spanmetrics_calls_total{service=\"codeshare-svc\"}' | jq '.data.result|length'",
            final_cmd="jq '.instrumenter,.integrations' sentry/codeshare-sdk.json",
            patch_old='"instrumenter": "sentry"',
            patch_new='"instrumenter": "otel"\n  "integrations": ["HttpClient", "OpenTelemetry"]',
            runbook_path="runbooks/codeshare-sentry-sg.md",
            runbook=(
                "# codeshare-svc Sentry op vs Tempo SG\n"
                "Set Sentry instrumenter=otel so spans get span.kind=client and server.address.\n"
                "Not a missing spanmetrics dimension and not event_id join.\n"
            ),
            goal=(
                "codeshare-svc dashboard code-sentry-op-1 service graph has no edges. "
                "Traces exist. Fix the span.kind lie."
            ),
            plan="Empty SG series → missing dim (false) → Sentry op without span.kind → OTel instrumenter.",
            outcome=(
                "Sentry instrumenter otel. traces_service_graph_request_total has codeshare-svc client edges. "
                "spanmetrics still counted."
            ),
            obs1='[{"uid":"code-sentry-op-1","title":"codeshare service graph"}]',
            obs2='{"title":"service graph","datasource":"mimir-share","targets":[{"expr":"traces_service_graph_request_total{client=\\"codeshare-svc\\"}"}]}',
            obs3='{"status":"success","data":{"result":[]}}',
            obs4="- service.name\n- span.kind\n# dimensions already include span.kind — not missing dim",
            obs5="service_graphs dimensions already set; span_metrics has service.name",
            obs6='{"enableTracing":true,"instrumenter":"sentry","integrations":["HttpClient"]}',
            obs7='[{"name":"GET /partners","kind":0,"attrs":["sentry.op","http.method"]}]\n# kind=0 SPAN_KIND_UNSPECIFIED; sentry.op=http.client; no server.address',
            obs8='{"enableTracing":true,"instrumenter":"sentry"}',
            obs9="patched instrumenter sentry→otel + OpenTelemetry integration",
            obs10='deployment "codeshare-svc" successfully rolled out',
            obs11='{"status":"success","data":{"result":[{"metric":{"client":"codeshare-svc","server":"partner-api"},"value":[1710000600,"88"]}]}}',
            obs12='{"name":"Node graph","fields":[{"name":"id"},{"name":"title"}]}',
            obs13="6",
            obs14="wrote runbooks/codeshare-sentry-sg.md",
            obs15='{"instrumenter":"otel","integrations":["HttpClient","OpenTelemetry"]}',
        ),
        _fail(
            slug="sentry-span-name-override",
            service="interline-svc",
            dashboard_uid="interline-sentry-op",
            panel="interline graph",
            query='traces_service_graph_request_total{client="interline-svc"}',
            lie="Tempo span_name override does not mint span.kind; Sentry instrumenter=sentry still unspecified",
            false_lead="Tempo service-graphs span_name mismatch",
            config_path="tempo/interline-mg.yaml",
            lie_path="sentry/interline-sdk.json",
            wrong_path="tempo/interline-mg.yaml",
            reload_name="tempo-metrics-generator",
            ticket="OBS-4431",
            xfail="tests/test_interline_sg.py",
            surfaces="Tempo span_name leftover vs Sentry instrumenter",
            avoided="r162 event_id; Tempo missing dim",
            this_is="fail/handoff: span_name override, SG still empty",
            step_note="span_name 6-10; still empty 11; late sentry sdk 12; handoff 14-15.",
            next_note="Next: Datadog inferred postgres vs OTel resource service.name.",
            search_cmd="curl -sS $GRAFANA/api/search?query=interline-sentry-op | jq -c '.[]|{uid,title}'",
            dash_cmd="curl -sS $GRAFANA/api/dashboards/uid/interline-sentry-op | jq '.dashboard.panels[0]'",
            query_cmd="curl -sS -G $MIMIR/prometheus/api/v1/query --data-urlencode 'query=traces_service_graph_request_total{client=\"interline-svc\"}'",
            false_cmd="yq '.metrics_generator.processor.service_graphs' tempo/interline-mg.yaml",
            reload_cmd="kubectl -n tempo rollout restart deploy/metrics-generator && kubectl -n tempo rollout status deploy/metrics-generator --timeout=90s",
            requery_cmd="curl -sS -G $MIMIR/prometheus/api/v1/query --data-urlencode 'query=traces_service_graph_request_total{client=\"interline-svc\"}'",
            denied_cmd="kubectl -n share auth can-i patch deploy/interline-svc --as=sre-bot",
            xfail_cmd="printf '%s\\n' '@pytest.mark.xfail(reason=\"interline sentry sdk owned by partners-platform\")\\ndef test_interline_sg():\\n    assert False' > tests/test_interline_sg.py",
            wrong_old="wait: 10s",
            wrong_new="wait: 10s\n      span_name: client",
            wrong2_old="histogram_buckets: [0.1, 1]",
            wrong2_new="histogram_buckets: [0.1, 1, 2]",
            ticket_path="tickets/OBS-4431.md",
            ticket_body=(
                "OBS-4431: interline-svc SG empty. Spans kind=0 sentry.op=http.client. "
                "Tempo span_name override does not set span.kind. Need Sentry instrumenter=otel; no RBAC.\n"
            ),
            goal="interline-svc dashboard interline-sentry-op service graph is empty. Restore client/server edges.",
            plan="Override Tempo span_name so service-graphs see a client span.",
            outcome=(
                "span_name and extra buckets applied; SG series still empty. "
                "Late interline-sdk.json instrumenter=sentry. Handoff OBS-4431."
            ),
            obs1='[{"uid":"interline-sentry-op","title":"interline graph"}]',
            obs2='{"title":"interline graph","targets":[{"expr":"traces_service_graph_request_total{client=\\"interline-svc\\"}"}]}',
            obs3='{"status":"success","data":{"result":[]}}',
            obs4="wait: 10s\nenable_client_id: true\n# blamed span_name",
            obs5="service_graphs wait 10s (not the banned tail decision_wait)",
            obs6="tempo/interline-mg.yaml — treated as RCA",
            obs7="patched span_name: client",
            obs8='deployment "metrics-generator" successfully rolled out',
            obs9='{"status":"success","data":{"result":[]}}',
            obs10="patched histogram buckets",
            obs11='{"status":"success","data":{"result":[]}}',
            obs12='sentry/interline-sdk.json instrumenter=sentry integrations=["HttpClient"] spans kind=UNSPECIFIED',
            obs13="no",
            obs14="wrote tickets/OBS-4431.md",
            obs15="xfail tests/test_interline_sg.py",
        ),
    )
)

# ---------------------------------------------------------------------------
# r172 Datadog inferred service vs OTel resource
# ---------------------------------------------------------------------------
MORE.append(
    (
        _ok(
            slug="dd-inferred-vs-otel-resource",
            service="gds-soap-svc",
            dashboard_uid="gds-dd-inf-9",
            panel="db map",
            query='{resource.service.name="postgres-gds"}',
            lie="DD inferred entity postgres-gds from peer.db.name is not an OTel resource service.name so Tempo map is empty",
            false_lead="OTTL truncate_all dropping postgres-gds",
            config_path="otelcol/gds-transform.yaml",
            lie_path="otelcol/gds-collector.yaml",
            truth_name="Tempo resource.service.name set",
            reload_name="otelcol-gds",
            side="gds-soap-svc traces still in Tempo",
            surfaces="Datadog inferred postgres vs OTel resource",
            avoided="r163 _dd.p.tid; OTTL truncate_all",
            this_is="DD inferred peer service not copied to OTel service.name",
            step_note="False lead OTTL 4-5; inferred vs resource 6-8; resource processor 9-12.",
            search_cmd="curl -sS $GRAFANA/api/search?query=gds-dd-inf-9 | jq -c '.[]|{uid,title}'",
            dash_cmd="curl -sS $GRAFANA/api/dashboards/uid/gds-dd-inf-9 | jq '.dashboard.panels[0]'",
            query_cmd="curl -sS -G $TEMPO/api/search --data-urlencode 'q={resource.service.name=\"postgres-gds\"}' | jq '.traces|length'",
            false_cmd="rg -n 'truncate_all|postgres-gds' otelcol/gds-transform.yaml",
            truth_cmd="curl -sS -G $TEMPO/api/search --data-urlencode 'q={resource.service.name=\"gds-soap-svc\" && name=\"pg.query\"}' | jq '.traces[:1]'",
            confirm_cmd="yq '.processors,.service.pipelines.traces' otelcol/gds-collector.yaml",
            reload_cmd="kubectl -n gds rollout restart deploy/otelcol-gds && kubectl -n gds rollout status deploy/otelcol-gds --timeout=90s",
            requery_cmd="curl -sS -G $TEMPO/api/search --data-urlencode 'q={resource.service.name=\"postgres-gds\"}' | jq '.traces|length'",
            grafana_ok_cmd="curl -sS $GRAFANA/api/ds/query -d @/tmp/gds-map.json | jq '.results.A.frames[0].schema'",
            side_cmd="curl -sS -G $TEMPO/api/search --data-urlencode 'q={resource.service.name=\"gds-soap-svc\"}' | jq '.traces|length'",
            final_cmd="yq '.processors.resource/inferred.attributes' otelcol/gds-collector.yaml",
            patch_old="processors:\n  batch: {}",
            patch_new=(
                "processors:\n  batch: {}\n"
                "  resource/inferred:\n    attributes:\n"
                "      - key: service.name\n        from_attribute: db.name\n"
                "        action: insert\n    from_attribute_value_map:\n"
                "      gds: postgres-gds"
            ),
            runbook_path="runbooks/gds-dd-inferred.md",
            runbook=(
                "# gds-soap-svc DD inferred vs OTel\n"
                "Copy db.name → service.name postgres-gds via resource processor. "
                "DD inferred entities are not Tempo resources.\n"
            ),
            goal=(
                "gds-soap-svc dashboard gds-dd-inf-9 db map is empty for postgres-gds. "
                "DD APM shows the inferred DB. Fix the resource lie."
            ),
            plan="Empty Tempo search → OTTL (false) → no resource processor → insert service.name from db.name.",
            outcome=(
                "resource/inferred copies db.name to service.name postgres-gds. "
                "db map has nodes. gds-soap-svc traces remain."
            ),
            obs1='[{"uid":"gds-dd-inf-9","title":"GDS db map"}]',
            obs2='{"title":"db map","targets":[{"query":"{resource.service.name=\\"postgres-gds\\"}"}]}',
            obs3="0",
            obs4="# no truncate_all\n# postgres-gds never mentioned",
            obs5="transform processor empty — banned OTTL plant not this",
            obs6="processors: {batch: {}}\ntraces exporters: [otlp/tempo]\n# no resource/inferred",
            obs7='{"traceID":"...","rootTraceName":"pg.query","spanSets":[{"matched":1,"spans":[{"name":"pg.query","attributes":{"db.name":"gds"}}]}]}\n# db.name present, service.name is gds-soap-svc',
            obs8="batch only; no from_attribute db.name",
            obs9="patched resource/inferred from db.name → service.name postgres-gds",
            obs10='deployment "otelcol-gds" successfully rolled out',
            obs11="14",
            obs12='{"name":"Node graph"}',
            obs13="40",
            obs14="wrote runbooks/gds-dd-inferred.md",
            obs15='[{"key":"service.name","from_attribute":"db.name","action":"insert"}]',
        ),
        _fail(
            slug="dd-peer-service-wrong-key",
            service="nfd-ticket-svc",
            dashboard_uid="nfd-dd-peer",
            panel="nfd db map",
            query='{resource.service.name="postgres-nfd"}',
            lie="peer.service processor key is wrong (peer.address not db.name); Tempo still has no postgres-nfd resource",
            false_lead="missing peer.service processor",
            config_path="otelcol/nfd-collector.yaml",
            lie_path="otelcol/nfd-collector.yaml",
            wrong_path="otelcol/nfd-collector.yaml",
            reload_name="otelcol-nfd",
            ticket="OBS-4432",
            xfail="tests/test_nfd_inferred.py",
            surfaces="peer.service wrong key vs DD inferred db.name",
            avoided="r163 tid width; OTTL truncate",
            this_is="fail/handoff: peer.service from peer.address, still no postgres-nfd",
            step_note="peer.service 6-10; still 0 11; late db.name 12; handoff 14-15.",
            next_note="Next: Loki bloom skip-on-error missing bloom, not SM allowlist.",
            search_cmd="curl -sS $GRAFANA/api/search?query=nfd-dd-peer | jq -c '.[]|{uid,title}'",
            dash_cmd="curl -sS $GRAFANA/api/dashboards/uid/nfd-dd-peer | jq '.dashboard.panels[0]'",
            query_cmd="curl -sS -G $TEMPO/api/search --data-urlencode 'q={resource.service.name=\"postgres-nfd\"}' | jq '.traces|length'",
            false_cmd="yq '.processors' otelcol/nfd-collector.yaml",
            reload_cmd="kubectl -n nfd rollout restart deploy/otelcol-nfd && kubectl -n nfd rollout status deploy/otelcol-nfd --timeout=90s",
            requery_cmd="curl -sS -G $TEMPO/api/search --data-urlencode 'q={resource.service.name=\"postgres-nfd\"}' | jq '.traces|length'",
            denied_cmd="kubectl -n nfd auth can-i patch deploy/otelcol-nfd --as=sre-bot",
            xfail_cmd="printf '%s\\n' '@pytest.mark.xfail(reason=\"nfd collector owned by ticketing-obs\")\\ndef test_nfd_inferred():\\n    assert False' > tests/test_nfd_inferred.py",
            wrong_old="processors:\n  batch: {}",
            wrong_new=(
                "processors:\n  batch: {}\n"
                "  attributes/peer:\n    actions:\n"
                "      - key: peer.service\n        from_attribute: peer.address\n        action: upsert"
            ),
            wrong2_old="processors: [attributes/peer, batch]",
            wrong2_new="processors: [attributes/peer, memory_limiter, batch]",
            ticket_path="tickets/OBS-4432.md",
            ticket_body=(
                "OBS-4432: nfd-ticket-svc Tempo has no postgres-nfd. peer.address is an IP, "
                "DD inferred name comes from db.name. Need resource from db.name; collector patch was wrong key. Handoff.\n"
            ),
            goal="nfd-ticket-svc dashboard nfd-dd-peer db map is empty for postgres-nfd. Restore the node.",
            plan="Add peer.service from peer.address so Tempo sees postgres-nfd.",
            outcome=(
                "peer.service copied from peer.address (IPs). postgres-nfd still 0 traces. "
                "Late: DD inferred uses db.name. Handoff OBS-4432."
            ),
            obs1='[{"uid":"nfd-dd-peer","title":"NFD db map"}]',
            obs2='{"title":"nfd db map","targets":[{"query":"{resource.service.name=\\"postgres-nfd\\"}"}]}',
            obs3="0",
            obs4="batch: {}",
            obs5="no peer.service processor — treated as RCA",
            obs6="otelcol/nfd-collector.yaml batch only",
            obs7="patched attributes/peer from peer.address",
            obs8='deployment "otelcol-nfd" successfully rolled out',
            obs9="0",
            obs10="patched added memory_limiter",
            obs11="0",
            obs12="spans have db.name=nfd, peer.address=10.4.2.8; DD inferred name postgres-nfd from db.name not peer.address",
            obs13="no  # second patch already applied; still wrong attribute. handoff rather than more collector churn",
            obs14="wrote tickets/OBS-4432.md",
            obs15="xfail tests/test_nfd_inferred.py",
        ),
    )
)

# ---------------------------------------------------------------------------
# r173 Loki bloom skip-on-error (missing bloom ≠ stale bloom r165)
# ---------------------------------------------------------------------------
MORE.append(
    (
        _ok(
            slug="loki-bloom-skip-on-error",
            service="galley-iot-svc",
            dashboard_uid="galley-bloom-shard",
            panel="temp logs",
            query='{app="galley-iot-svc"} |= "overtemp"',
            lie="bloom-gateway SkipOnError true treats missing blooms (disk full shipper) as skip so new periods vanish",
            false_lead="Loki SM allowlist dropping galley tenant",
            config_path="loki/galley-limits.yaml",
            lie_path="loki/galley-bloom.yaml",
            truth_name="bloom-shipper disk",
            reload_name="loki-bloom-gateway",
            side="older periods with blooms still query",
            surfaces="Loki bloom SkipOnError vs SM allowlist",
            avoided="r165 stale skip_factor; SM allowlist; line_format",
            this_is="SkipOnError missing bloom after shipper disk full",
            step_note="False lead SM 4-5; SkipOnError 6-8; disable skip + free disk 9-12.",
            search_cmd="curl -sS $GRAFANA/api/search?query=galley-bloom-shard | jq -c '.[]|{uid,title}'",
            dash_cmd="curl -sS $GRAFANA/api/dashboards/uid/galley-bloom-shard | jq '.dashboard.panels[0]'",
            query_cmd="curl -sS -G http://loki-gateway.obs/loki/api/v1/query_range --data-urlencode 'query={app=\"galley-iot-svc\"} |= \"overtemp\"' --data-urlencode 'start=now-2h' --data-urlencode 'end=now'",
            false_cmd="yq '.overrides.galley' loki/galley-limits.yaml",
            truth_cmd="kubectl -n loki exec deploy/bloom-shipper -- df -h /data/blooms; kubectl -n loki logs deploy/bloom-shipper --tail=15 | rg 'no space|skip'",
            confirm_cmd="yq '.bloom_gateway.skip_on_error,.bloom_gateway.enabled' loki/galley-bloom.yaml",
            reload_cmd="kubectl -n loki rollout restart deploy/bloom-gateway && kubectl -n loki rollout status deploy/bloom-gateway --timeout=90s",
            requery_cmd="curl -sS -G http://loki-gateway.obs/loki/api/v1/query_range --data-urlencode 'query={app=\"galley-iot-svc\"} |= \"overtemp\"' --data-urlencode 'start=now-2h'",
            grafana_ok_cmd="curl -sS $GRAFANA/api/ds/query -d @/tmp/galley.json | jq '.results.A.frames[0].data.values[1]|length'",
            side_cmd="curl -sS -G http://loki-gateway.obs/loki/api/v1/query_range --data-urlencode 'query={app=\"galley-iot-svc\"} |= \"overtemp\"' --data-urlencode 'start=now-48h' --data-urlencode 'end=now-24h' | jq '.data.result|length'",
            final_cmd="yq '.bloom_gateway.skip_on_error' loki/galley-bloom.yaml",
            patch_old="skip_on_error: true",
            patch_new="skip_on_error: false\n    skip_factor: 0",
            runbook_path="runbooks/galley-bloom-skip-on-error.md",
            runbook=(
                "# galley-iot-svc bloom SkipOnError\n"
                "Shipper disk full → missing blooms → SkipOnError skipped new chunks. "
                "skip_on_error false; free disk. Distinct from stale skip_factor.\n"
            ),
            goal=(
                "galley-iot-svc dashboard galley-bloom-shard temp logs empty for the last 2h. "
                "Older hours still work. Find the skip-on-error lie."
            ),
            plan="Empty recent LogQL → SM override (false) → shipper disk full + SkipOnError → disable skip.",
            outcome=(
                "skip_on_error false. Recent overtemp lines return. 24-48h window still served from old blooms."
            ),
            obs1='[{"uid":"galley-bloom-shard","title":"galley iot temps"}]',
            obs2='{"title":"temp logs","targets":[{"expr":"{app=\\"galley-iot-svc\\"} |= \\"overtemp\\""}]}',
            obs3='{"status":"success","data":{"result":[]}}',
            obs4="allow_structured_metadata: true\nretention_period: 336h\n# no SM allowlist deny",
            obs5="galley tenant allowed — banned SM plant not this",
            obs6="skip_on_error: true\nenabled: true",
            obs7="Use% 100%\nmsg=\"no space left on device\" path=/data/blooms\nmsg=\"skipping unreadable bloom\" skip_on_error=true",
            obs8="true\ntrue",
            obs9="patched skip_on_error true→false; skip_factor 0",
            obs10='deployment "bloom-gateway" successfully rolled out',
            obs11='{"status":"success","data":{"result":[{"values":[["1710000000000000000","overtemp probe=12"]]}]}}',
            obs12="9",
            obs13="4",
            obs14="wrote runbooks/galley-bloom-skip-on-error.md",
            obs15="false",
        ),
        _fail(
            slug="loki-bloom-disable-all-tenants",
            service="pantry-sensor-svc",
            dashboard_uid="pantry-bloom-off",
            panel="door logs",
            query='{app="pantry-sensor-svc"} |= "ajar"',
            lie="Globally disabling bloom-gateway is blocked; SkipOnError still skips pantry missing blooms",
            false_lead="bloom-gateway enabled globally should be flipped off",
            config_path="loki/pantry-bloom.yaml",
            lie_path="loki/pantry-bloom.yaml",
            wrong_path="loki/pantry-bloom.yaml",
            reload_name="loki-bloom-gateway",
            ticket="OBS-4433",
            xfail="tests/test_pantry_bloom.py",
            surfaces="global bloom off leftover vs SkipOnError tenant",
            avoided="r165 skip_factor stale; SM allowlist",
            this_is="fail/handoff: cannot disable bloom globally",
            step_note="enabled=false 6-10; helm deny 8/13; late SkipOnError 12; handoff 14-15.",
            next_note="Next: OTel routing connector vs leftover filter processor.",
            search_cmd="curl -sS $GRAFANA/api/search?query=pantry-bloom-off | jq -c '.[]|{uid,title}'",
            dash_cmd="curl -sS $GRAFANA/api/dashboards/uid/pantry-bloom-off | jq '.dashboard.panels[0]'",
            query_cmd="curl -sS -G http://loki-gateway.obs/loki/api/v1/query --data-urlencode 'query={app=\"pantry-sensor-svc\"} |= \"ajar\"'",
            false_cmd="yq '.bloom_gateway.enabled' loki/pantry-bloom.yaml",
            reload_cmd="kubectl -n loki rollout restart deploy/bloom-gateway && kubectl -n loki rollout status deploy/bloom-gateway --timeout=90s",
            requery_cmd="curl -sS -G http://loki-gateway.obs/loki/api/v1/query --data-urlencode 'query={app=\"pantry-sensor-svc\"} |= \"ajar\"'",
            denied_cmd="kubectl -n loki auth can-i patch deploy/bloom-gateway --as=sre-bot",
            xfail_cmd="printf '%s\\n' '@pytest.mark.xfail(reason=\"bloom-gateway global flag owned by logging-platform\")\\ndef test_pantry_bloom():\\n    assert False' > tests/test_pantry_bloom.py",
            wrong_old="enabled: true",
            wrong_new="enabled: false",
            wrong2_old="skip_factor: 2",
            wrong2_new="skip_factor: 0",
            ticket_path="tickets/OBS-4433.md",
            ticket_body=(
                "OBS-4433: pantry-sensor-svc still empty. Global bloom disable rolled back by helm. "
                "SkipOnError=true on missing blooms. Need tenant skip_on_error=false; no RBAC.\n"
            ),
            goal="pantry-sensor-svc dashboard pantry-bloom-off door logs empty for recent hours. Restore lines.",
            plan="Disable bloom-gateway globally so queries hit TSDB.",
            outcome=(
                "enabled=false plus skip_factor 0; helm re-enabled gateway. Still empty. "
                "Late SkipOnError=true. Handoff OBS-4433."
            ),
            obs1='[{"uid":"pantry-bloom-off","title":"pantry door"}]',
            obs2='{"title":"door logs","targets":[{"expr":"{app=\\"pantry-sensor-svc\\"} |= \\"ajar\\""}]}',
            obs3='{"status":"success","data":{"result":[]}}',
            obs4="true\n# blamed global enable",
            obs5="bloom_gateway.enabled: true",
            obs6="loki/pantry-bloom.yaml enabled true — treated as RCA",
            obs7="patched enabled true→false",
            obs8='deployment "bloom-gateway" successfully rolled out\n# helm hook restored enabled=true within 20s',
            obs9='{"status":"success","data":{"result":[]}}',
            obs10="patched skip_factor 2→0 (gateway still enabled by helm)",
            obs11='{"status":"success","data":{"result":[]}}',
            obs12="skip_on_error: true  # missing blooms skipped; helm owns enabled",
            obs13="no",
            obs14="wrote tickets/OBS-4433.md",
            obs15="xfail tests/test_pantry_bloom.py",
        ),
    )
)

# ---------------------------------------------------------------------------
# r174 OTel routing connector vs leftover filter processor
# ---------------------------------------------------------------------------
MORE.append(
    (
        _ok(
            slug="otel-routing-vs-filter-proc",
            service="pet-cabin-svc",
            dashboard_uid="pet-route-conn",
            panel="trace rate",
            query='sum(rate(traces_span_metrics_calls_total{service_name="pet-cabin-svc"}[5m]))',
            lie="routing connector sends tenant=pet to tempo-pet but leftover filter/processor in that pipeline drops tenant=pet (keep only tenant=core)",
            false_lead="tail_sampling decision_wait too short for pet spans",
            config_path="otelcol/pet-collector.yaml",
            lie_path="otelcol/pet-collector.yaml",
            truth_name="collector debug exporter counts",
            reload_name="otelcol-pet",
            side="tenant=core traces still reach tempo-core",
            surfaces="OTel routing connector vs leftover filter processor",
            avoided="r109-r158 OTel tail decision_wait, tailsampling cache; r166 spanmetrics names",
            this_is="routing connector output still runs filter processor skip",
            step_note="False lead tail wait 4-5; filter in routed pipeline 6-8; remove filter 9-12.",
            search_cmd="curl -sS $GRAFANA/api/search?query=pet-route-conn | jq -c '.[]|{uid,title}'",
            dash_cmd="curl -sS $GRAFANA/api/dashboards/uid/pet-route-conn | jq '.dashboard.panels[0]'",
            query_cmd="curl -sS -G $MIMIR/prometheus/api/v1/query --data-urlencode 'query=sum(rate(traces_span_metrics_calls_total{service_name=\"pet-cabin-svc\"}[5m]))'",
            false_cmd="yq '.processors.tail_sampling' otelcol/pet-collector.yaml",
            truth_cmd="kubectl -n pet logs deploy/otelcol-pet --tail=40 | rg 'filter/keep-core|routing|dropped'",
            confirm_cmd="yq '.service.pipelines,.connectors.routing,.processors.filter' otelcol/pet-collector.yaml",
            reload_cmd="kubectl -n pet rollout restart deploy/otelcol-pet && kubectl -n pet rollout status deploy/otelcol-pet --timeout=90s",
            requery_cmd="curl -sS -G $TEMPO_PET/api/search --data-urlencode 'q={resource.service.name=\"pet-cabin-svc\"}' | jq '.traces|length'",
            grafana_ok_cmd="curl -sS $GRAFANA/api/ds/query -d @/tmp/pet-rate.json | jq '.results.A.frames[0].data.values'",
            side_cmd="curl -sS -G $TEMPO_CORE/api/search --data-urlencode 'q={resource.service.name=\"checkin-core-svc\"}' | jq '.traces|length'",
            final_cmd="yq '.service.pipelines.traces/pet.processors' otelcol/pet-collector.yaml",
            patch_old="traces/pet:\n      receivers: [routing]\n      processors: [filter/keep-core, batch]\n      exporters: [otlp/tempo-pet]",
            patch_new="traces/pet:\n      receivers: [routing]\n      processors: [batch]\n      exporters: [otlp/tempo-pet]",
            runbook_path="runbooks/pet-routing-filter.md",
            runbook=(
                "# pet-cabin-svc routing vs filter\n"
                "Do not leave filter/keep-core on the routed pet pipeline. Routing already selected tenant=pet.\n"
                "Not tail_sampling decision_wait.\n"
            ),
            goal=(
                "pet-cabin-svc dashboard pet-route-conn trace rate is empty after routing-connector migration. "
                "Find the leftover filter skip."
            ),
            plan="Empty rate → tail_sampling (absent) → filter/keep-core on traces/pet → drop filter.",
            outcome=(
                "Removed filter/keep-core from traces/pet. Tempo-pet has 37 traces. Core tenant unchanged."
            ),
            obs1='[{"uid":"pet-route-conn","title":"pet cabin traces"}]',
            obs2='{"title":"trace rate","targets":[{"expr":"sum(rate(traces_span_metrics_calls_total{service_name=\\"pet-cabin-svc\\"}[5m]))"}]}',
            obs3='{"status":"success","data":{"result":[]}}',
            obs4="null\n# no tail_sampling processor",
            obs5="banned tail decision_wait not present",
            obs6=(
                "connectors.routing: from_attribute tenant default traces/core\n"
                "  table: [{value: pet, pipeline: traces/pet}]\n"
                "pipelines.traces/pet.processors: [filter/keep-core, batch]\n"
                "processors.filter/keep-core: include match_type strict tenant=core"
            ),
            obs7='msg="span dropped by filter/keep-core" tenant=pet service=pet-cabin-svc\n# routing delivered then filter skipped',
            obs8="filter/keep-core include tenant=core on traces/pet — skip of pet spans",
            obs9="patched traces/pet processors to [batch] only",
            obs10='deployment "otelcol-pet" successfully rolled out',
            obs11="37",
            obs12="[[1710000600],[6.2]]",
            obs13="80",
            obs14="wrote runbooks/pet-routing-filter.md",
            obs15="[batch]",
        ),
        _fail(
            slug="otel-routing-add-tail-wait",
            service="live-animal-svc",
            dashboard_uid="animal-route-tail",
            panel="animal trace rate",
            query='sum(rate(traces_span_metrics_calls_total{service_name="live-animal-svc"}[5m]))',
            lie="Raising tail_sampling decision_wait (banned leftover) does not undo filter/keep-core on the routed animal pipeline",
            false_lead="tail_sampling decision_wait dropping animal spans",
            config_path="otelcol/animal-collector.yaml",
            lie_path="otelcol/animal-collector.yaml",
            wrong_path="otelcol/animal-collector.yaml",
            reload_name="otelcol-animal",
            ticket="OBS-4434",
            xfail="tests/test_animal_routing.py",
            surfaces="tail wait leftover vs routing+filter skip",
            avoided="using tail decision_wait as the actual RCA (it is the false lead)",
            this_is="fail/handoff: raised decision_wait, filter still drops tenant=animal",
            step_note="decision_wait 6-10; still empty 11; late filter 12; handoff 14-15.",
            next_note="Catalog for r175+: Grafana Faro vs Tempo, Alloy vs agent, Adaptive Metrics vs join.",
            search_cmd="curl -sS $GRAFANA/api/search?query=animal-route-tail | jq -c '.[]|{uid,title}'",
            dash_cmd="curl -sS $GRAFANA/api/dashboards/uid/animal-route-tail | jq '.dashboard.panels[0]'",
            query_cmd="curl -sS -G $MIMIR/prometheus/api/v1/query --data-urlencode 'query=sum(rate(traces_span_metrics_calls_total{service_name=\"live-animal-svc\"}[5m]))'",
            false_cmd="yq '.processors.tail_sampling.decision_wait' otelcol/animal-collector.yaml",
            reload_cmd="kubectl -n animal rollout restart deploy/otelcol-animal && kubectl -n animal rollout status deploy/otelcol-animal --timeout=90s",
            requery_cmd="curl -sS -G $MIMIR/prometheus/api/v1/query --data-urlencode 'query=sum(rate(traces_span_metrics_calls_total{service_name=\"live-animal-svc\"}[5m]))'",
            denied_cmd="kubectl -n animal auth can-i patch deploy/otelcol-animal --as=sre-bot",
            xfail_cmd="printf '%s\\n' '@pytest.mark.xfail(reason=\"animal collector owned by cargo-obs\")\\ndef test_animal_routing():\\n    assert False' > tests/test_animal_routing.py",
            wrong_old="decision_wait: 5s",
            wrong_new="decision_wait: 30s",
            wrong2_old="num_traces: 10000",
            wrong2_new="num_traces: 50000",
            ticket_path="tickets/OBS-4434.md",
            ticket_body=(
                "OBS-4434: live-animal-svc still empty. decision_wait change irrelevant. "
                "traces/animal still has filter/keep-core. Need processor list patch; collector owned by cargo-obs.\n"
            ),
            goal="live-animal-svc dashboard animal-route-tail trace rate is empty after routing migration. Restore traces.",
            plan="Raise tail_sampling decision_wait so animal spans are kept.",
            outcome=(
                "decision_wait 30s and larger cache; rate still empty. "
                "Late filter/keep-core on traces/animal. Handoff OBS-4434."
            ),
            obs1='[{"uid":"animal-route-tail","title":"live animal traces"}]',
            obs2='{"title":"animal trace rate","targets":[{"expr":"sum(rate(traces_span_metrics_calls_total{service_name=\\"live-animal-svc\\"}[5m]))"}]}',
            obs3='{"status":"success","data":{"result":[]}}',
            obs4="5s\n# treated as banned tail wait RCA",
            obs5="processors.tail_sampling.decision_wait 5s present as a red herring",
            obs6="otelcol/animal-collector.yaml tail_sampling — treated as RCA",
            obs7="patched decision_wait 5s→30s",
            obs8='deployment "otelcol-animal" successfully rolled out',
            obs9='{"status":"success","data":{"result":[]}}',
            obs10="patched num_traces 10k→50k (still not filter)",
            obs11='{"status":"success","data":{"result":[]}}',
            obs12="pipelines.traces/animal.processors: [filter/keep-core, tail_sampling, batch]\nfilter include tenant=core  # animal dropped after routing",
            obs13="no",
            obs14="wrote tickets/OBS-4434.md",
            obs15="xfail tests/test_animal_routing.py",
        ),
    )
)
