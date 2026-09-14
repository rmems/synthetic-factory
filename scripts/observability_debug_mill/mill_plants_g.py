"""Observability plants r199-r206. Do not clone r109-r198."""

from mill_plants import _fail, _ok
from mill_plants_f import _g, _gs, _xfail

MORE = []


# r199 Zipkin B3 16-hex vs Tempo 32-hex (NOT Jaeger empty cassandra, NOT DD 64-bit)
MORE.append(
    (
        _ok(
            slug="zipkin-b3-16-vs-tempo-32",
            service="cargo-awb-svc",
            dashboard_uid="awb-b3-9",
            panel="B3 paste",
            query="GET /api/traces/{X-B3-TraceId}",
            lie="Grafana Tempo lookup of Zipkin B3 16-hex trace id; Tempo stores 32-hex left-padded and exact 16-hex misses",
            false_lead="Grafana Jaeger datasource empty cassandra leftover",
            config_path="grafana/provisioning/datasources/awb-jaeger.yaml",
            lie_path="grafana/dashboards/awb-b3-9.json",
            truth_name="Tempo 32-hex zero-padded B3",
            reload_name="grafana",
            side="Zipkin collector still has 16-hex ids",
            surfaces="Zipkin B3 16-hex vs Tempo 32-hex padded",
            avoided="r179 Jaeger query empty cassandra; r163 DD 64 vs 128",
            this_is="B3 16-hex pasted; Tempo exact-match 32-hex",
            step_note="False lead Jaeger 4-5; B3 16-hex 6-8; left-pad 9-12.",
            query_cmd="curl -sS $TEMPO/api/traces/4bf92f3577b34da6 | jq '{error}'",
            false_cmd=(
                "yq -r '.datasources[]|{name,type,url}' "
                "grafana/provisioning/datasources/awb-jaeger.yaml"
            ),
            truth_cmd="curl -sS $TEMPO/api/traces/00000000000000004bf92f3577b34da6 | jq '.batches|length'",
            confirm_cmd="jq '.templating.list[]|{name,query}' grafana/dashboards/awb-b3-9.json",
            reload_cmd=(
                "kubectl -n grafana rollout restart deploy/grafana && "
                "kubectl -n grafana rollout status deploy/grafana --timeout=90s"
            ),
            requery_cmd="curl -sS $TEMPO/api/traces/00000000000000004bf92f3577b34da6 | jq '.batches|length'",
            side_cmd="curl -sS $ZIPKIN/api/v2/trace/4bf92f3577b34da6 | jq 'length'",
            final_cmd="jq -r '.panels[0].targets[0].query' grafana/dashboards/awb-b3-9.json",
            patch_old='query: "${b3_trace_id}"',
            patch_new='query: "${b3_trace_id_padded}"  # left-pad 16-hex B3 to 32',
            runbook_path="runbooks/awb-b3-pad.md",
            runbook=(
                "# cargo-awb-svc Zipkin B3 vs Tempo\n"
                "64-bit B3 is 16 hex. Tempo exact-matches 32 hex (left-padded zeros).\n"
                "Not empty Jaeger cassandra.\n"
            ),
            goal=(
                "cargo-awb-svc dashboard awb-b3-9 B3 paste 404s. Zipkin UI has the trace. "
                "Fix the 16-vs-32 lie."
            ),
            plan="404 → Jaeger datasource (false) → B3 16-hex → left-pad to 32.",
            outcome="Dashboard uses padded 32-hex. Tempo 1 batch. Zipkin still 16-hex.",
            obs1='[{"uid":"awb-b3-9","title":"cargo awb b3"}]',
            obs2='{"title":"B3 paste","targets":[{"query":"${b3_trace_id}"}]}',
            obs3='{"error":"trace not found: 4bf92f3577b34da6"}',
            obs4='{"name":"awb-jaeger","type":"jaeger","url":"http://jaeger-query:16686"}\n# jaeger-query storage cassandra empty — but panel is Tempo, not r179',
            obs5="Jaeger ds leftover exists; panel datasource is tempo",
            obs6='{"name":"b3_trace_id","query":"X-B3-TraceId"}',
            obs7="1",
            obs8="Tempo has 00000000000000004bf92f3577b34da6; 16-hex exact miss",
            obs9="patched query ${b3_trace_id_padded}",
            obs10='deployment "grafana" successfully rolled out',
            obs11="1",
            obs12='{"name":"Traces"}',
            obs13="8",
            obs14="wrote runbooks/awb-b3-pad.md",
            obs15="${b3_trace_id_padded}",
            **_g("awb-b3-9"),
        ),
        _fail(
            slug="zipkin-raise-tempo-qf-not-pad",
            service="dg-accept-svc",
            dashboard_uid="dg-b3-qf",
            panel="DG B3",
            query="GET /api/traces/{X-B3-TraceId}",
            lie="Raising Tempo query-frontend max_outstanding does not left-pad Zipkin B3 16-hex to 32-hex",
            false_lead="Tempo query-frontend max_outstanding / Jaeger empty cassandra",
            config_path="tempo/dg-query.yaml",
            lie_path="grafana/dashboards/dg-b3-qf.json",
            wrong_path="tempo/dg-query.yaml",
            reload_name="tempo-query-frontend",
            ticket="OBS-5109",
            xfail="tests/test_dg_b3.py",
            surfaces="Tempo qf leftover vs Zipkin B3 pad",
            avoided="r179 as actual RCA",
            this_is="fail/handoff: raised max_outstanding, 16-hex still 404",
            step_note="qf 6-10; still 404 11; late B3 16 12; handoff 14-15.",
            next_note="Next: Vector VRL drop job vs Loki {job}.",
            query_cmd="curl -sS $TEMPO/api/traces/a1b2c3d4e5f60789 | jq '{error}'",
            false_cmd="yq '.query_frontend.max_outstanding_per_tenant' tempo/dg-query.yaml",
            reload_cmd=(
                "kubectl -n tempo rollout restart deploy/query-frontend && "
                "kubectl -n tempo rollout status deploy/query-frontend --timeout=90s"
            ),
            requery_cmd="curl -sS $TEMPO/api/traces/a1b2c3d4e5f60789 | jq '{error}'",
            denied_cmd="kubectl -n grafana auth can-i patch configmap/grafana-dashboards --as=sre-bot",
            xfail_cmd=_xfail("dg_b3", "dg dashboard owned by irm-platform"),
            wrong_old="max_outstanding_per_tenant: 100",
            wrong_new="max_outstanding_per_tenant: 2000",
            wrong2_old='url: http://jaeger-query:16686',
            wrong2_new='url: http://tempo.obs.svc:3200  # not r179 cassandra fill',
            ticket_path="tickets/OBS-5109.md",
            ticket_body=(
                "OBS-5109: dg-accept-svc Tempo still 404 on B3 16-hex a1b2c3d4e5f60789. "
                "Need left-pad 0000000000000000. qf bump irrelevant. No RBAC.\n"
            ),
            goal="dg-accept-svc dashboard dg-b3-qf B3 paste 404s. Open the Tempo trace.",
            plan="Raise Tempo query-frontend max_outstanding (r179 leftover).",
            outcome="qf 2000; 16-hex still 404. Late pad. Handoff OBS-5109.",
            obs1='[{"uid":"dg-b3-qf","title":"dg accept b3"}]',
            obs2='{"title":"DG B3","targets":[{"query":"${b3_trace_id}"}]}',
            obs3='{"error":"trace not found"}',
            obs4="max_outstanding_per_tenant: 100  # treated as r179",
            obs5="qf outstanding 100",
            obs6="tempo/dg-query.yaml",
            obs7="patched 2000",
            obs8='deployment "query-frontend" successfully rolled out',
            obs9='{"error":"trace not found"}',
            obs10="patched jaeger url comment",
            obs11='{"error":"trace not found"}',
            obs12="B3 a1b2c3d4e5f60789; Tempo has 0000000000000000a1b2c3d4e5f60789",
            obs13="no",
            obs14="wrote tickets/OBS-5109.md",
            obs15="xfail tests/test_dg_b3.py",
            **_gs("dg-b3-qf"),
        ),
    )
)

# r200 Vector VRL drop job vs Loki {job} (NOT OS URL rewrite, NOT VL LogsQL)
MORE.append(
    (
        _ok(
            slug="vector-vrl-drop-job-vs-loki",
            service="ground-power-svc",
            dashboard_uid="gpwr-vrl-1",
            panel="gpu logs",
            query='{job="ground-power-svc"} |= "gpu_fault"',
            lie="Vector remap del(.job) ships to OpenSearch; Grafana Loki {job=ground-power-svc} is empty",
            false_lead="Loki datasource URL rewritten to VictoriaLogs / OpenSearch",
            config_path="grafana/provisioning/datasources/gpwr-logs.yaml",
            lie_path="vector/gpwr.toml",
            truth_name="OpenSearch gpwr-logs index",
            reload_name="vector",
            side="OpenSearch still searchable by host",
            surfaces="Vector VRL drop job vs Loki {job}",
            avoided="r191 OS URL rewrite; r161 VL LogsQL; r170 VL | json",
            this_is="Vector del(.job) + elasticsearch sink, Loki never sees job",
            step_note="False lead OS/VL URL 4-5; Vector VRL 6-8; keep job + Loki sink 9-12.",
            query_cmd=(
                "curl -sS -G $LOKI/loki/api/v1/query_range "
                "--data-urlencode 'query={job=\"ground-power-svc\"} |= \"gpu_fault\"' "
                "| jq '.data.result|length'"
            ),
            false_cmd=(
                "yq -r '.datasources[]|{name,type,url}' "
                "grafana/provisioning/datasources/gpwr-logs.yaml"
            ),
            truth_cmd=(
                "curl -sS $OS/gpwr-logs-*/_search "
                "-d '{\"query\":{\"match\":{\"host\":\"gpu-a\"}}}' "
                "| jq '{total:.hits.total.value,keys:.hits.hits[0]._source|keys}'"
            ),
            confirm_cmd="rg -n 'del\\(|sinks|loki|elasticsearch' vector/gpwr.toml",
            reload_cmd=(
                "kubectl -n vector rollout restart daemonset/vector && "
                "kubectl -n vector rollout status daemonset/vector --timeout=90s"
            ),
            requery_cmd=(
                "curl -sS -G $LOKI/loki/api/v1/query_range "
                "--data-urlencode 'query={job=\"ground-power-svc\"} |= \"gpu_fault\"' "
                "| jq '.data.result|length'"
            ),
            side_cmd=(
                "curl -sS $OS/gpwr-logs-*/_search "
                "-d '{\"query\":{\"match\":{\"host\":\"gpu-a\"}}}' | jq '.hits.total.value'"
            ),
            final_cmd="rg -n 'job|loki' vector/gpwr.toml | head",
            patch_old='del(.job)\n  .index = "gpwr-logs"',
            patch_new=(
                '.job = "ground-power-svc"\n'
                '[sinks.loki]\n  type = "loki"\n  endpoint = "http://loki:3100"\n'
                '  labels.job = "{{ job }}"'
            ),
            runbook_path="runbooks/gpwr-vector-job.md",
            runbook=(
                "# ground-power-svc Vector vs Loki\n"
                "VRL del(.job) + elasticsearch sink. Loki {job} never ingested.\n"
                "Not datasource URL rewrite to OpenSearch.\n"
            ),
            goal=(
                "ground-power-svc dashboard gpwr-vrl-1 gpu logs empty. OpenSearch has gpu_fault. "
                "Find the VRL drop-job lie."
            ),
            plan="Empty Loki → OS/VL URL (false, URL is Loki) → Vector del(.job) → keep job + Loki sink.",
            outcome="Vector ships job to Loki. 27 streams. OpenSearch host search still works.",
            obs1='[{"uid":"gpwr-vrl-1","title":"ground power logs"}]',
            obs2='{"title":"gpu logs","targets":[{"expr":"{job=\\"ground-power-svc\\"} |= \\"gpu_fault\\""}]}',
            obs3="0",
            obs4='{"name":"gpwr-logs","type":"loki","url":"http://loki.obs.svc:3100"}\n# not OS URL — not r191',
            obs5="datasource is real Loki",
            obs6='del(.job)\n.index = "gpwr-logs"\n[sinks.os]\ntype = "elasticsearch"',
            obs7='{"total":27,"keys":["host","message","level"]}\n# no job field',
            obs8="VRL dropped job; only OS sink",
            obs9="patched keep job + Loki sink",
            obs10='daemonset "vector" successfully rolled out',
            obs11="27",
            obs12='{"name":"Logs"}',
            obs13="27",
            obs14="wrote runbooks/gpwr-vector-job.md",
            obs15='.job = "ground-power-svc"',
            **_g("gpwr-vrl-1"),
        ),
        _fail(
            slug="vector-loki-json-not-vrl",
            service="gpu-meter-svc",
            dashboard_uid="gmeter-vrl-json",
            panel="meter logs",
            query='{job="gpu-meter-svc"} | json | level="error"',
            lie="Adding Loki | json does not restore Vector-dropped job labels; logs never reached Loki",
            false_lead="Loki missing | json parser (VL leftover)",
            config_path="grafana/dashboards/gmeter-vrl-json.json",
            lie_path="vector/gmeter.toml",
            wrong_path="grafana/dashboards/gmeter-vrl-json.json",
            reload_name="grafana",
            ticket="OBS-5110",
            xfail="tests/test_gmeter_vrl.py",
            surfaces="LogQL | json leftover vs Vector del(.job)",
            avoided="r161 / r191 as actual RCA",
            this_is="fail/handoff: | json on empty Loki, Vector still drops job",
            step_note="| json 6-10; still 0 11; late Vector 12; handoff 14-15.",
            next_note="Next: GCP Cloud Trace decimal span id vs Tempo hex.",
            query_cmd=(
                "curl -sS -G $LOKI/loki/api/v1/query_range "
                "--data-urlencode 'query={job=\"gpu-meter-svc\"} | json | level=\"error\"' "
                "| jq '.data.result|length'"
            ),
            false_cmd="jq '.panels[0].targets[0].expr' grafana/dashboards/gmeter-vrl-json.json",
            reload_cmd=(
                "kubectl -n grafana rollout restart deploy/grafana && "
                "kubectl -n grafana rollout status deploy/grafana --timeout=90s"
            ),
            requery_cmd=(
                "curl -sS -G $LOKI/loki/api/v1/query_range "
                "--data-urlencode 'query={job=\"gpu-meter-svc\"} | json | level=\"error\"' "
                "| jq '.data.result|length'"
            ),
            denied_cmd="kubectl -n vector auth can-i patch daemonset/vector --as=sre-bot",
            xfail_cmd=_xfail("gmeter_vrl", "vector ds owned by platform-logging"),
            wrong_old='{job="gpu-meter-svc"} |= "error"',
            wrong_new='{job="gpu-meter-svc"} | json | level="error"',
            wrong2_old="datasource: loki",
            wrong2_new="datasource: loki\n      maxLines: 5000",
            ticket_path="tickets/OBS-5110.md",
            ticket_body=(
                "OBS-5110: gpu-meter-svc Loki still 0. | json irrelevant. "
                "vector/gmeter.toml del(.job) + elasticsearch sink. Need Loki sink+job. No RBAC.\n"
            ),
            goal="gpu-meter-svc dashboard gmeter-vrl-json meter logs empty. Restore Loki rows.",
            plan="Add | json (r161 leftover).",
            outcome="| json applied; still 0. Late Vector del(.job). Handoff OBS-5110.",
            obs1='[{"uid":"gmeter-vrl-json","title":"gpu meter logs"}]',
            obs2='{"title":"meter logs","targets":[{"expr":"{job=\\"gpu-meter-svc\\"} |= \\"error\\""}]}',
            obs3="0",
            obs4='"{job=\\"gpu-meter-svc\\"} |= \\"error\\""',
            obs5="no | json — treated as r161",
            obs6="grafana/dashboards/gmeter-vrl-json.json",
            obs7="patched | json",
            obs8='deployment "grafana" successfully rolled out',
            obs9="0",
            obs10="patched maxLines",
            obs11="0",
            obs12='vector/gmeter.toml del(.job); sinks.os elasticsearch; no loki sink',
            obs13="no",
            obs14="wrote tickets/OBS-5110.md",
            obs15="xfail tests/test_gmeter_vrl.py",
            **_gs("gmeter-vrl-json"),
        ),
    )
)

# r201 GCP Cloud Trace decimal span id vs Tempo hex (NOT Sentry event_id)
MORE.append(
    (
        _ok(
            slug="gct-decimal-span-vs-tempo",
            service="cabin-clean-svc",
            dashboard_uid="clean-gct-2",
            panel="GCT paste",
            query="GET /api/traces/{cloud_trace_span_id}",
            lie="Grafana Tempo lookup of GCP Cloud Trace span id (decimal uint64 from console) as hex W3C traceId",
            false_lead="Sentry event_id as Tempo traceId",
            config_path="grafana/dashboards/clean-gct-2.json",
            lie_path="runbooks/cabin-clean-gct.md",
            truth_name="Cloud Trace 32-hex trace id",
            reload_name="grafana",
            side="Cloud Trace console still shows decimal span ids",
            surfaces="GCP Cloud Trace decimal span id vs Tempo W3C trace_id",
            avoided="r162 Sentry event_id; r184 NR spanId; r175 Faro",
            this_is="GCP console decimal span id pasted as Tempo traceId",
            step_note="False lead Sentry 4-5; decimal span 6-8; 32-hex trace 9-12.",
            query_cmd="curl -sS $TEMPO/api/traces/12345678901234567890 | jq '{error}'",
            false_cmd="jq '.templating.list[]|{name,query}' grafana/dashboards/clean-gct-2.json",
            truth_cmd=(
                "curl -sS $GCT/v1/projects/airline/traces/a1b2c3d4e5f60718293a4b5c6d7e8f90 "
                "| jq '{traceId,spanId:.spans[0].spanId}'"
            ),
            confirm_cmd="rg -n 'span id|trace id|decimal' runbooks/cabin-clean-gct.md",
            reload_cmd=(
                "kubectl -n grafana rollout restart deploy/grafana && "
                "kubectl -n grafana rollout status deploy/grafana --timeout=90s"
            ),
            requery_cmd=(
                "curl -sS $TEMPO/api/traces/a1b2c3d4e5f60718293a4b5c6d7e8f90 "
                "| jq '.batches|length'"
            ),
            side_cmd=(
                "gcloud trace spans list --project=airline --filter=service=cabin-clean-svc "
                "--format='value(spanId)' | head"
            ),
            final_cmd="jq -r '.panels[0].targets[0].query' grafana/dashboards/clean-gct-2.json",
            patch_old="Paste Cloud Trace span id (decimal) into Tempo.",
            patch_new="Paste Cloud Trace trace id (32-hex). Span id decimal is not W3C.",
            runbook_path="runbooks/cabin-clean-gct-w3c.md",
            runbook=(
                "# cabin-clean-svc Cloud Trace vs Tempo\n"
                "GCP console span ids are decimal. Tempo wants 32-hex trace id.\n"
                "Not Sentry event_id.\n"
            ),
            goal=(
                "cabin-clean-svc dashboard clean-gct-2 GCT paste 404s. Cloud Trace has the span. "
                "Fix the decimal-vs-hex lie."
            ),
            plan="404 → Sentry var (false) → decimal span id → 32-hex trace id.",
            outcome="Panel uses GCT trace id. Tempo 1 batch. Console still decimal span ids.",
            obs1='[{"uid":"clean-gct-2","title":"cabin clean gct"}]',
            obs2='{"title":"GCT paste","targets":[{"query":"${gct_span_id}"}]}',
            obs3='{"error":"trace not found: 12345678901234567890"}',
            obs4='{"name":"sentry_event_id","query":""}\n{"name":"gct_span_id","query":"Cloud Trace span"}\n# sentry unused — not r162',
            obs5="sentry_event_id empty",
            obs6="Paste Cloud Trace span id (decimal) into Tempo.",
            obs7='{"traceId":"a1b2c3d4e5f60718293a4b5c6d7e8f90","spanId":"12345678901234567890"}',
            obs8="decimal span id ≠ 32-hex trace id",
            obs9="patched runbook + query ${gct_trace_id}",
            obs10='deployment "grafana" successfully rolled out',
            obs11="1",
            obs12='{"name":"Traces"}',
            obs13="12345678901234567890",
            obs14="wrote runbooks/cabin-clean-gct-w3c.md",
            obs15="${gct_trace_id}",
            **_g("clean-gct-2"),
        ),
        _fail(
            slug="gct-sentry-event-not-decimal",
            service="turnaround-svc",
            dashboard_uid="turn-gct-nr",
            panel="turn GCT",
            query="GET /api/traces/{cloud_trace_span_id}",
            lie="Looking up Sentry event_id does not convert GCP Cloud Trace decimal span ids into Tempo W3C trace ids",
            false_lead="Sentry event_id as Tempo traceId",
            config_path="grafana/dashboards/turn-gct-nr.json",
            lie_path="runbooks/turnaround-gct.md",
            wrong_path="grafana/dashboards/turn-gct-nr.json",
            reload_name="grafana",
            ticket="OBS-5111",
            xfail="tests/test_turn_gct.py",
            surfaces="Sentry event_id leftover vs Cloud Trace decimal",
            avoided="r162 as actual RCA",
            this_is="fail/handoff: swapped Sentry event_id, decimal span still 404",
            step_note="Sentry var 6-10; still 404 11; late decimal 12; handoff 14-15.",
            next_note="Next: SkyWalking sw8 vs Tempo W3C.",
            query_cmd="curl -sS $TEMPO/api/traces/9876543210987654321 | jq '{error}'",
            false_cmd="jq '.templating.list[]|{name}' grafana/dashboards/turn-gct-nr.json",
            reload_cmd=(
                "kubectl -n grafana rollout restart deploy/grafana && "
                "kubectl -n grafana rollout status deploy/grafana --timeout=90s"
            ),
            requery_cmd="curl -sS $TEMPO/api/traces/9876543210987654321 | jq '{error}'",
            denied_cmd="kubectl -n grafana auth can-i patch configmap/grafana-dashboards --as=sre-bot",
            xfail_cmd=_xfail("turn_gct", "turn dashboard owned by irm-platform"),
            wrong_old='query: "${gct_span_id}"',
            wrong_new='query: "${sentry_event_id}"',
            wrong2_old='name: sentry_event_id',
            wrong2_new='name: sentry_event_id\n      regex: "[0-9a-f]{32}"',
            ticket_path="tickets/OBS-5111.md",
            ticket_body=(
                "OBS-5111: turnaround-svc Tempo still 404 on decimal span id. "
                "Sentry swap irrelevant. Need Cloud Trace 32-hex trace id. No RBAC.\n"
            ),
            goal="turnaround-svc dashboard turn-gct-nr GCT paste 404s. Open Tempo.",
            plan="Point query at Sentry event_id (r162 leftover).",
            outcome="Sentry var; still 404. Late decimal span. Handoff OBS-5111.",
            obs1='[{"uid":"turn-gct-nr","title":"turnaround gct"}]',
            obs2='{"title":"turn GCT","targets":[{"query":"${gct_span_id}"}]}',
            obs3='{"error":"trace not found"}',
            obs4='{"name":"sentry_event_id"}\n{"name":"gct_span_id"}',
            obs5="sentry var present — treated as r162",
            obs6="grafana/dashboards/turn-gct-nr.json",
            obs7="patched query ${sentry_event_id}",
            obs8='deployment "grafana" successfully rolled out',
            obs9='{"error":"trace not found"}',
            obs10="patched sentry regex",
            obs11='{"error":"trace not found"}',
            obs12="gct_span_id=9876543210987654321 decimal; Cloud Trace trace id=ffeeddccbbaa00998877665544332211",
            obs13="no",
            obs14="wrote tickets/OBS-5111.md",
            obs15="xfail tests/test_turn_gct.py",
            **_gs("turn-gct-nr"),
        ),
    )
)

# r202 SkyWalking sw8 vs Tempo W3C (NOT Sentry event_id)
MORE.append(
    (
        _ok(
            slug="sw8-header-vs-tempo-w3c",
            service="gate-assign-svc",
            dashboard_uid="gateas-sw8-3",
            panel="sw8 paste",
            query="GET /api/traces/{sw8}",
            lie="Grafana Tempo lookup of SkyWalking sw8 header (sample-traceId-segment-span-...) as W3C 32-hex",
            false_lead="Sentry event_id / tracesSampleRate as Tempo traceId",
            config_path="grafana/dashboards/gateas-sw8-3.json",
            lie_path="otelcol/gate-assign-propagator.yaml",
            truth_name="sw8 decoded W3C",
            reload_name="otelcol-gate-assign",
            side="SkyWalking OAP still stores sw8 segments",
            surfaces="SkyWalking sw8 vs Tempo W3C trace_id",
            avoided="r162 Sentry event_id; r171 Sentry op vs SG; r184 NR spanId",
            this_is="sw8 multi-segment header pasted into Tempo",
            step_note="False lead Sentry 4-5; sw8 6-8; b3/w3c propagator 9-12.",
            query_cmd=(
                "curl -sS $TEMPO/api/traces/1-dGVzdHRyYWNlaWQ=-c2VnbWVudA==-0-gate-assign-1-/assign "
                "| jq '{error}'"
            ),
            false_cmd="jq '.templating.list[]|{name}' grafana/dashboards/gateas-sw8-3.json",
            truth_cmd=(
                "curl -sS $TEMPO/api/traces/74657374747261636569640000000000 "
                "| jq '.batches|length'"
            ),
            confirm_cmd="yq '.service.telemetry.traces.propagators' otelcol/gate-assign-propagator.yaml",
            reload_cmd=(
                "kubectl -n gateas rollout restart deploy/otelcol-gate-assign && "
                "kubectl -n gateas rollout status deploy/otelcol-gate-assign --timeout=90s"
            ),
            requery_cmd=(
                "curl -sS $TEMPO/api/traces/74657374747261636569640000000000 "
                "| jq '.batches|length'"
            ),
            side_cmd="curl -sS $SKYWALKING/graphql -d '{\"query\":\"{traces{traceId}}\"}' | jq '.data.traces|length'",
            final_cmd="yq -r '.processors.attributes.actions[0].key' otelcol/gate-assign-propagator.yaml",
            patch_old="propagators: [tracecontext]",
            patch_new=(
                "propagators: [tracecontext, b3, jaeger]\n"
                "  # decode sw8 via skywalkingpropagator in SDK; Grafana uses W3C"
            ),
            runbook_path="runbooks/gate-assign-sw8.md",
            runbook=(
                "# gate-assign-svc SkyWalking vs Tempo\n"
                "sw8 is sample-base64Trace-segment-span-.... Tempo wants 32-hex.\n"
                "Not Sentry event_id.\n"
            ),
            goal=(
                "gate-assign-svc dashboard gateas-sw8-3 sw8 paste 404s. SkyWalking UI has the trace. "
                "Fix the header lie."
            ),
            plan="404 → Sentry var (false) → sw8 segments → W3C from SDK propagator.",
            outcome="Propagators include b3+W3C. Grafana uses 32-hex. OAP still has sw8.",
            obs1='[{"uid":"gateas-sw8-3","title":"gate assign sw8"}]',
            obs2='{"title":"sw8 paste","targets":[{"query":"${sw8}"}]}',
            obs3='{"error":"trace not found"}',
            obs4='{"name":"sentry_event_id"}\n{"name":"sw8"}\n# sentry unused',
            obs5="sentry var empty",
            obs6="propagators: [tracecontext]  # no skywalking",
            obs7="1",
            obs8="sw8 base64 traceId decodes to 7465737474726163656964…; paste was full header",
            obs9="patched propagator + dashboard ${w3c_trace_id}",
            obs10='deployment "otelcol-gate-assign" successfully rolled out',
            obs11="1",
            obs12='{"name":"Traces"}',
            obs13="14",
            obs14="wrote runbooks/gate-assign-sw8.md",
            obs15="sw8",
            **_g("gateas-sw8-3"),
        ),
        _fail(
            slug="sw8-sentry-sample-not-header",
            service="stand-alloc-svc",
            dashboard_uid="stand-sw8-sentry",
            panel="stand sw8",
            query="GET /api/traces/{sw8}",
            lie="Raising Sentry tracesSampleRate does not decode SkyWalking sw8 into a Tempo W3C traceId",
            false_lead="Sentry tracesSampleRate / event_id lookup",
            config_path="k8s/sentry/stand-alloc.env",
            lie_path="grafana/dashboards/stand-sw8-sentry.json",
            wrong_path="k8s/sentry/stand-alloc.env",
            reload_name="stand-alloc-svc",
            ticket="OBS-5112",
            xfail="tests/test_stand_sw8.py",
            surfaces="Sentry sample leftover vs sw8 header",
            avoided="r162 / r171 as actual RCA",
            this_is="fail/handoff: Sentry sample 1.0, sw8 paste still 404",
            step_note="Sentry sample 6-10; still 404 11; late sw8 12; handoff 14-15.",
            next_note="Next: Mimir ingest-storage Kafka vs store-gateway query.",
            query_cmd="curl -sS $TEMPO/api/traces/1-c3RhbmQ=-c2Vn-0-stand-1-/alloc | jq '{error}'",
            false_cmd="rg 'SENTRY_TRACES|SENTRY_DSN' k8s/sentry/stand-alloc.env",
            reload_cmd=(
                "kubectl -n stand rollout restart deploy/stand-alloc-svc && "
                "kubectl -n stand rollout status deploy/stand-alloc-svc --timeout=90s"
            ),
            requery_cmd="curl -sS $TEMPO/api/traces/1-c3RhbmQ=-c2Vn-0-stand-1-/alloc | jq '{error}'",
            denied_cmd="kubectl -n grafana auth can-i patch configmap/grafana-dashboards --as=sre-bot",
            xfail_cmd=_xfail("stand_sw8", "stand dashboard owned by irm-platform"),
            wrong_old="SENTRY_TRACES_SAMPLE_RATE=0.1",
            wrong_new="SENTRY_TRACES_SAMPLE_RATE=1.0",
            wrong2_old="SENTRY_INSTRUMENTER=sentry",
            wrong2_new="SENTRY_INSTRUMENTER=otel  # not r171 span.kind",
            ticket_path="tickets/OBS-5112.md",
            ticket_body=(
                "OBS-5112: stand-alloc-svc Tempo still 404 on sw8 paste. "
                "Sentry sample rate does not decode sw8. Need W3C. No RBAC.\n"
            ),
            goal="stand-alloc-svc dashboard stand-sw8-sentry sw8 paste 404s. Open Tempo.",
            plan="Raise Sentry tracesSampleRate (r162 leftover).",
            outcome="Sample 1.0; sw8 still 404. Late header. Handoff OBS-5112.",
            obs1='[{"uid":"stand-sw8-sentry","title":"stand alloc sw8"}]',
            obs2='{"title":"stand sw8","targets":[{"query":"${sw8}"}]}',
            obs3='{"error":"trace not found"}',
            obs4="SENTRY_TRACES_SAMPLE_RATE=0.1  # treated as r162",
            obs5="Sentry sample 0.1",
            obs6="k8s/sentry/stand-alloc.env",
            obs7="patched sample 1.0",
            obs8='deployment "stand-alloc-svc" successfully rolled out',
            obs9='{"error":"trace not found"}',
            obs10="patched instrumenter otel",
            obs11='{"error":"trace not found"}',
            obs12="panel ${sw8}=1-c3RhbmQ=-c2Vn-0-stand-1-/alloc; Tempo W3C=7374616e640000000000000000000000",
            obs13="no",
            obs14="wrote tickets/OBS-5112.md",
            obs15="xfail tests/test_stand_sw8.py",
            **_gs("stand-sw8-sentry"),
        ),
    )
)

# r203 Mimir ingest-storage Kafka vs store-gateway (NOT Prom agent, NOT Adaptive Metrics)
MORE.append(
    (
        _ok(
            slug="mimir-kafka-ingest-vs-sg",
            service="fuel-hydrant-svc",
            dashboard_uid="hydrant-kafka-4",
            panel="hydrant RPS",
            query='sum(rate(http_requests_total{service="fuel-hydrant-svc"}[5m]))',
            lie="Grafana Mimir still queries store-gateway; writes go to Kafka ingest-storage so the last 15m is empty",
            false_lead="Prometheus agent mode has no local TSDB",
            config_path="prom/hydrant-agent.yaml",
            lie_path="mimir/hydrant.yaml",
            truth_name="Mimir ingest-storage Kafka lag / distributor",
            reload_name="mimir-query-frontend",
            side="classic blocks older than 2h still queryable via store-gateway",
            surfaces="Mimir ingest-storage Kafka vs store-gateway query path",
            avoided="r160 Prom agent no TSDB; r176 Adaptive Metrics; r187 native hist",
            this_is="ingest_storage enabled; Grafana query path leftover store-gateway",
            step_note="False lead agent 4-5; Kafka ingest 6-8; query-path ingest 9-12.",
            query_cmd=(
                "curl -sS -G $MIMIR/prometheus/api/v1/query "
                "--data-urlencode 'query=sum(rate(http_requests_total{service=\"fuel-hydrant-svc\"}[5m]))'"
            ),
            false_cmd="rg 'enable-feature=agent|storage.tsdb' prom/hydrant-agent.yaml",
            truth_cmd=(
                "curl -sS $MIMIR/ingester/ring | jq '.shards' ; "
                "kaf --topic mimir-ingest --lag | rg hydrant"
            ),
            confirm_cmd="yq '.ingest_storage,.blocks_storage.backend' mimir/hydrant.yaml",
            reload_cmd=(
                "kubectl -n mimir rollout restart deploy/query-frontend && "
                "kubectl -n mimir rollout status deploy/query-frontend --timeout=90s"
            ),
            requery_cmd=(
                "curl -sS -G $MIMIR/prometheus/api/v1/query "
                "--data-urlencode 'query=sum(rate(http_requests_total{service=\"fuel-hydrant-svc\"}[5m]))'"
            ),
            side_cmd=(
                "curl -sS -G $MIMIR/prometheus/api/v1/query "
                "--data-urlencode 'query=sum(rate(http_requests_total{service=\"fuel-hydrant-svc\"}[2h]))' "
                "| jq '.data.result[0].value'"
            ),
            final_cmd="yq -r '.query_engine.ingest_query' mimir/hydrant.yaml",
            patch_old="query_store_after: 0s\n  ingest_storage:\n    enabled: true",
            patch_new=(
                "query_store_after: 2h\n  ingest_storage:\n    enabled: true\n"
                "  query_engine:\n    ingest_query: true"
            ),
            runbook_path="runbooks/hydrant-mimir-kafka.md",
            runbook=(
                "# fuel-hydrant-svc Mimir ingest-storage vs store-gateway\n"
                "Writes to Kafka ingest-storage. Grafana query path was store-gateway only.\n"
                "Not Prom agent TSDB.\n"
            ),
            goal=(
                "fuel-hydrant-svc dashboard hydrant-kafka-4 hydrant RPS empty for 15m while "
                "scrape works. Find the ingest-storage query-path lie."
            ),
            plan="Empty 5m → Prom agent (false) → Kafka ingest + store-gateway → ingest_query true.",
            outcome="ingest_query true. 5m RPS 12.4. 2h store-gateway still serves classic blocks.",
            obs1='[{"uid":"hydrant-kafka-4","title":"fuel hydrant rps"}]',
            obs2='{"title":"hydrant RPS","targets":[{"expr":"sum(rate(http_requests_total{service=\\"fuel-hydrant-svc\\"}[5m]))"}]}',
            obs3='{"status":"success","data":{"result":[]}}',
            obs4="enable-feature: []\n# not agent — not r160",
            obs5="Prometheus is server mode; remote_write to Mimir",
            obs6="ingest_storage.enabled: true\nblocks_storage.backend: s3\nquery_store_after: 0s",
            obs7="kafka topic mimir-ingest lag=0 for hydrant partitions; distributor 12.4 rps",
            obs8="recent samples only in ingest-storage; store-gateway has >2h blocks",
            obs9="patched query_store_after 2h + ingest_query true",
            obs10='deployment "query-frontend" successfully rolled out',
            obs11='{"status":"success","data":{"result":[{"value":[1710000600,"12.4"]}]}}',
            obs12='{"name":"Timeseries"}',
            obs13='["1710000600","11.9"]',
            obs14="wrote runbooks/hydrant-mimir-kafka.md",
            obs15="true",
            **_g("hydrant-kafka-4"),
        ),
        _fail(
            slug="mimir-point-grafana-at-agent",
            service="aoc-desk-svc",
            dashboard_uid="aoc-kafka-agent",
            panel="aoc RPS",
            query='sum(rate(http_requests_total{service="aoc-desk-svc"}[5m]))',
            lie="Pointing Grafana at a leftover Prom agent does not read Mimir Kafka ingest-storage",
            false_lead="Grafana datasource still on Prom agent with no TSDB",
            config_path="grafana/provisioning/datasources/aoc-prom.yaml",
            lie_path="mimir/aoc.yaml",
            wrong_path="grafana/provisioning/datasources/aoc-prom.yaml",
            reload_name="grafana",
            ticket="OBS-5113",
            xfail="tests/test_aoc_kafka.py",
            surfaces="Prom agent leftover vs Mimir ingest-storage",
            avoided="r160 as actual RCA",
            this_is="fail/handoff: pointed Grafana at agent, still no 5m samples",
            step_note="agent URL 6-10; still empty 11; late ingest_storage 12; handoff 14-15.",
            next_note="Next: OTel loadbalancing exporter vs Tempo.",
            query_cmd=(
                "curl -sS -G $MIMIR/prometheus/api/v1/query "
                "--data-urlencode 'query=sum(rate(http_requests_total{service=\"aoc-desk-svc\"}[5m]))'"
            ),
            false_cmd=(
                "yq -r '.datasources[]|{name,url}' "
                "grafana/provisioning/datasources/aoc-prom.yaml"
            ),
            reload_cmd=(
                "kubectl -n grafana rollout restart deploy/grafana && "
                "kubectl -n grafana rollout status deploy/grafana --timeout=90s"
            ),
            requery_cmd=(
                "curl -sS -G $PROM_AGENT/api/v1/query "
                "--data-urlencode 'query=sum(rate(http_requests_total{service=\"aoc-desk-svc\"}[5m]))'"
            ),
            denied_cmd="kubectl -n mimir auth can-i patch configmap/mimir-aoc --as=sre-bot",
            xfail_cmd=_xfail("aoc_kafka", "mimir ingest_query owned by metrics-platform"),
            wrong_old="url: http://mimir.obs.svc:9009/prometheus",
            wrong_new="url: http://prom-agent.obs.svc:9090",
            wrong2_old="access: proxy",
            wrong2_new="access: proxy\n  jsonData:\n    timeInterval: 15s",
            ticket_path="tickets/OBS-5113.md",
            ticket_body=(
                "OBS-5113: aoc-desk-svc 5m still empty. Agent URL is a leftover. "
                "mimir/aoc.yaml ingest_storage enabled, query_engine.ingest_query false. Need ingest_query. No RBAC.\n"
            ),
            goal="aoc-desk-svc dashboard aoc-kafka-agent aoc RPS empty for 15m. Restore scrape view.",
            plan="Point Grafana at Prom agent (r160 leftover).",
            outcome="Agent URL; still empty (no TSDB). Late ingest_storage. Handoff OBS-5113.",
            obs1='[{"uid":"aoc-kafka-agent","title":"aoc desk rps"}]',
            obs2='{"title":"aoc RPS","targets":[{"expr":"sum(rate(http_requests_total{service=\\"aoc-desk-svc\\"}[5m]))"}]}',
            obs3='{"status":"success","data":{"result":[]}}',
            obs4='{"name":"aoc-prom","url":"http://mimir.obs.svc:9009/prometheus"}',
            obs5="Grafana already on Mimir — treated as maybe agent",
            obs6="grafana/provisioning/datasources/aoc-prom.yaml",
            obs7="patched url prom-agent",
            obs8='deployment "grafana" successfully rolled out',
            obs9='{"status":"success","data":{"result":[]}}',
            obs10="patched timeInterval 15s",
            obs11='{"status":"success","data":{"result":[]}}',
            obs12="mimir/aoc.yaml ingest_storage.enabled true query_engine.ingest_query false",
            obs13="no",
            obs14="wrote tickets/OBS-5113.md",
            obs15="xfail tests/test_aoc_kafka.py",
            **_gs("aoc-kafka-agent"),
        ),
    )
)

# r204 OTel loadbalancing exporter vs Tempo (NOT routing connector vs filter)
MORE.append(
    (
        _ok(
            slug="otel-lb-static-jaeger-vs-tempo",
            service="pax-wifi-portal-svc",
            dashboard_uid="portal-lb-5",
            panel="portal traces",
            query='{resource.service.name="pax-wifi-portal-svc"}',
            lie="OTel loadbalancing exporter static list is leftover jaeger-collector; Tempo never receives traces",
            false_lead="routing connector + leftover filter processor drop",
            config_path="otelcol/portal-routing.yaml",
            lie_path="otelcol/portal-loadbalancing.yaml",
            truth_name="Jaeger leftover cassandra count",
            reload_name="otelcol-portal",
            side="direct-OTLP services still in Tempo",
            surfaces="OTel loadbalancing static jaeger vs Tempo",
            avoided="r174 routing connector vs filter; r179 Jaeger empty query",
            this_is="loadbalancing exporter backends=[jaeger-collector], Tempo omitted",
            step_note="False lead routing/filter 4-5; lb static 6-8; add Tempo 9-12.",
            query_cmd=(
                "curl -sS -G $TEMPO/api/search "
                "--data-urlencode 'q={resource.service.name=\"pax-wifi-portal-svc\"}' "
                "| jq '.traces|length'"
            ),
            false_cmd="yq '.connectors.routing,.processors.filter' otelcol/portal-routing.yaml",
            truth_cmd="curl -sS $JAEGER/api/traces?service=pax-wifi-portal-svc | jq 'length'",
            confirm_cmd="yq '.exporters.loadbalancing' otelcol/portal-loadbalancing.yaml",
            reload_cmd=(
                "kubectl -n otel rollout restart deploy/otelcol-portal && "
                "kubectl -n otel rollout status deploy/otelcol-portal --timeout=90s"
            ),
            requery_cmd=(
                "curl -sS -G $TEMPO/api/search "
                "--data-urlencode 'q={resource.service.name=\"pax-wifi-portal-svc\"}' "
                "| jq '.traces|length'"
            ),
            side_cmd=(
                "curl -sS -G $TEMPO/api/search "
                "--data-urlencode 'q={resource.service.name=\"ssr-meal-svc\"}' "
                "| jq '.traces|length'"
            ),
            final_cmd="yq -r '.exporters.loadbalancing.resolver.static.hostnames[]' otelcol/portal-loadbalancing.yaml",
            patch_old="hostnames:\n        - jaeger-collector.obs.svc:4317",
            patch_new="hostnames:\n        - tempo-distributor.obs.svc:4317",
            runbook_path="runbooks/portal-lb-tempo.md",
            runbook=(
                "# pax-wifi-portal-svc loadbalancing vs Tempo\n"
                "static resolver listed jaeger-collector leftover. Tempo omitted.\n"
                "Not routing-connector filter skip.\n"
            ),
            goal=(
                "pax-wifi-portal-svc dashboard portal-lb-5 portal traces empty. Jaeger leftover "
                "has spans. Find the loadbalancing backend lie."
            ),
            plan="Empty Tempo → routing/filter (false) → lb static jaeger → Tempo hostname.",
            outcome="lb backends Tempo. 22 traces. ssr-meal-svc direct-OTLP unchanged.",
            obs1='[{"uid":"portal-lb-5","title":"pax wifi portal traces"}]',
            obs2='{"title":"portal traces","targets":[{"query":"{resource.service.name=\\"pax-wifi-portal-svc\\"}"}]}',
            obs3="0",
            obs4="routing: null\nfilter: null\n# not r174",
            obs5="no routing connector; no filter processor",
            obs6="protocol: otlp\nresolver:\n  static:\n    hostnames: [jaeger-collector.obs.svc:4317]",
            obs7="22",
            obs8="loadbalancing hashed to Jaeger leftover; Tempo never saw batches",
            obs9="patched hostname tempo-distributor:4317",
            obs10='deployment "otelcol-portal" successfully rolled out',
            obs11="22",
            obs12='{"name":"Traces"}',
            obs13="19",
            obs14="wrote runbooks/portal-lb-tempo.md",
            obs15="tempo-distributor.obs.svc:4317",
            **_g("portal-lb-5"),
        ),
        _fail(
            slug="otel-lb-raise-tail-wait",
            service="jetbridge-cam-svc",
            dashboard_uid="jetcam-lb-tail",
            panel="cam traces",
            query='{resource.service.name="jetbridge-cam-svc"}',
            lie="Raising tail_sampling decision_wait does not add Tempo to loadbalancing static backends (still jaeger-collector)",
            false_lead="OTel tail_sampling decision_wait too low",
            config_path="otelcol/jetcam-tail.yaml",
            lie_path="otelcol/jetcam-loadbalancing.yaml",
            wrong_path="otelcol/jetcam-tail.yaml",
            reload_name="otelcol-jetcam",
            ticket="OBS-5114",
            xfail="tests/test_jetcam_lb.py",
            surfaces="tail wait leftover vs loadbalancing jaeger static",
            avoided="r174 / OTel tail wait as actual RCA",
            this_is="fail/handoff: raised decision_wait, backends still Jaeger",
            step_note="tail wait 6-10; still 0 11; late lb yaml 12; handoff 14-15.",
            next_note="Next: OpenMetrics _created vs Grafana increase().",
            query_cmd=(
                "curl -sS -G $TEMPO/api/search "
                "--data-urlencode 'q={resource.service.name=\"jetbridge-cam-svc\"}' "
                "| jq '.traces|length'"
            ),
            false_cmd="yq '.processors.tail_sampling.decision_wait' otelcol/jetcam-tail.yaml",
            reload_cmd=(
                "kubectl -n otel rollout restart deploy/otelcol-jetcam && "
                "kubectl -n otel rollout status deploy/otelcol-jetcam --timeout=90s"
            ),
            requery_cmd=(
                "curl -sS -G $TEMPO/api/search "
                "--data-urlencode 'q={resource.service.name=\"jetbridge-cam-svc\"}' "
                "| jq '.traces|length'"
            ),
            denied_cmd="kubectl -n otel auth can-i patch deploy/otelcol-jetcam --as=sre-bot",
            xfail_cmd=_xfail("jetcam_lb", "otelcol-jetcam owned by tracing-platform"),
            wrong_old="decision_wait: 2s",
            wrong_new="decision_wait: 30s",
            wrong2_old="expected_new_traces_per_sec: 10",
            wrong2_new="expected_new_traces_per_sec: 200",
            ticket_path="tickets/OBS-5114.md",
            ticket_body=(
                "OBS-5114: jetbridge-cam-svc Tempo still 0. decision_wait bump irrelevant. "
                "loadbalancing static hostnames=[jaeger-collector:4317]. Need Tempo. RBAC denied second patch.\n"
            ),
            goal="jetbridge-cam-svc dashboard jetcam-lb-tail cam traces empty. Land traces in Tempo.",
            plan="Raise tail_sampling decision_wait (banned leftover).",
            outcome="wait 30s; still 0. Late jaeger static list. Handoff OBS-5114.",
            obs1='[{"uid":"jetcam-lb-tail","title":"jetbridge cam traces"}]',
            obs2='{"title":"cam traces","targets":[{"query":"{resource.service.name=\\"jetbridge-cam-svc\\"}"}]}',
            obs3="0",
            obs4="decision_wait: 2s  # treated as tail wait leftover",
            obs5="tail_sampling present",
            obs6="otelcol/jetcam-tail.yaml",
            obs7="patched decision_wait 30s",
            obs8='deployment "otelcol-jetcam" successfully rolled out',
            obs9="0",
            obs10="patched expected_new_traces_per_sec 200",
            obs11="0",
            obs12="otelcol/jetcam-loadbalancing.yaml hostnames [jaeger-collector.obs.svc:4317]",
            obs13="no",
            obs14="wrote tickets/OBS-5114.md",
            obs15="xfail tests/test_jetcam_lb.py",
            **_gs("jetcam-lb-tail"),
        ),
    )
)

# r205 OpenMetrics _created vs Grafana increase() (NOT native vs classic hist)
MORE.append(
    (
        _ok(
            slug="om-created-vs-increase",
            service="lav-service-svc",
            dashboard_uid="lav-om-6",
            panel="lav RPS",
            query='sum(increase(http_requests_total{service="lav-service-svc"}[5m]))',
            lie="OpenMetrics scrape emits http_requests_total_created so Grafana increase() resets to 0 while the counter climbs",
            false_lead="native-histogram scrape dropped classic _bucket",
            config_path="prom/lav-scrape.yaml",
            lie_path="grafana/dashboards/lav-om-6.json",
            truth_name="counter vs _created series",
            reload_name="grafana",
            side="rate() panels on the same counter still work",
            surfaces="OpenMetrics _created vs Grafana increase()",
            avoided="r187 native vs classic hist; r160 Prom agent",
            this_is="OpenMetrics created-timestamp zeros increase()",
            step_note="False lead native hist 4-5; _created 6-8; switch rate() 9-12.",
            query_cmd=(
                "curl -sS -G $MIMIR/prometheus/api/v1/query "
                "--data-urlencode 'query=sum(increase(http_requests_total{service=\"lav-service-svc\"}[5m]))'"
            ),
            false_cmd="rg 'scrape_protocols|native-histogram|_bucket' prom/lav-scrape.yaml",
            truth_cmd=(
                "curl -sS -G $MIMIR/prometheus/api/v1/query "
                "--data-urlencode 'query=http_requests_total_created{service=\"lav-service-svc\"}'"
            ),
            confirm_cmd="jq '.panels[]|{title,expr:.targets[0].expr}' grafana/dashboards/lav-om-6.json",
            reload_cmd=(
                "kubectl -n grafana rollout restart deploy/grafana && "
                "kubectl -n grafana rollout status deploy/grafana --timeout=90s"
            ),
            requery_cmd=(
                "curl -sS -G $MIMIR/prometheus/api/v1/query "
                "--data-urlencode 'query=sum(rate(http_requests_total{service=\"lav-service-svc\"}[5m]))'"
            ),
            side_cmd=(
                "curl -sS -G $MIMIR/prometheus/api/v1/query "
                "--data-urlencode 'query=sum(rate(http_requests_total{service=\"ssr-meal-svc\"}[5m]))' "
                "| jq '.data.result[0].value'"
            ),
            final_cmd="jq -r '.panels[0].targets[0].expr' grafana/dashboards/lav-om-6.json",
            patch_old='sum(increase(http_requests_total{service="lav-service-svc"}[5m]))',
            patch_new='sum(rate(http_requests_total{service="lav-service-svc"}[5m]))',
            runbook_path="runbooks/lav-om-created.md",
            runbook=(
                "# lav-service-svc OpenMetrics _created vs increase()\n"
                "OM 1.0 scrape emits _created. Prometheus increase() treats created-ts as a reset.\n"
                "Use rate(). Not native-histogram _bucket loss.\n"
            ),
            goal=(
                "lav-service-svc dashboard lav-om-6 lav RPS is 0 while counter is climbing. "
                "Find the OpenMetrics _created lie."
            ),
            plan="increase()=0 → native hist (false, _bucket exists) → _created series → rate().",
            outcome="Panel uses rate(). 8.2 rps. _bucket still present. Not native-hist.",
            obs1='[{"uid":"lav-om-6","title":"lav service rps"}]',
            obs2='{"title":"lav RPS","targets":[{"expr":"sum(increase(http_requests_total{service=\\"lav-service-svc\\"}[5m]))"}]}',
            obs3='{"status":"success","data":{"result":[{"value":[1710000000,"0"]}]}}',
            obs4="scrape_protocols: [OpenMetricsText1.0.0]\n# classic _bucket still scraped — not r187",
            obs5="not native-histogram-only",
            obs6='{"title":"lav RPS","expr":"sum(increase(...))"}\n{"title":"created","expr":"http_requests_total_created"}',
            obs7='{"status":"success","data":{"result":[{"value":[1710000000,"1710000000"]}]}}\n# _created = scrape start; increase() sees reset',
            obs8="OpenMetrics _created zeros increase(); counter raw is 1.2e6",
            obs9="patched expr to rate()",
            obs10='deployment "grafana" successfully rolled out',
            obs11='{"status":"success","data":{"result":[{"value":[1710000600,"8.2"]}]}}',
            obs12='{"name":"Timeseries"}',
            obs13='["1710000600","19.4"]',
            obs14="wrote runbooks/lav-om-created.md",
            obs15='sum(rate(http_requests_total{service="lav-service-svc"}[5m]))',
            **_g("lav-om-6"),
        ),
        _fail(
            slug="om-retarget-native-hist",
            service="catering-uplift-svc",
            dashboard_uid="caterup-om-nhist",
            panel="uplift RPS",
            query='sum(increase(http_requests_total{service="catering-uplift-svc"}[5m]))',
            lie="Pointing Grafana at native-histogram / Prom agent does not stop OpenMetrics _created from zeroing increase()",
            false_lead="native-histogram scrape dropped classic series",
            config_path="prom/caterup-scrape.yaml",
            lie_path="grafana/dashboards/caterup-om-nhist.json",
            wrong_path="prom/caterup-scrape.yaml",
            reload_name="prom-scrape",
            ticket="OBS-5115",
            xfail="tests/test_caterup_om.py",
            surfaces="native hist leftover vs OpenMetrics _created",
            avoided="r187 as actual RCA",
            this_is="fail/handoff: native scrape on, increase() still 0 from _created",
            step_note="native hist 6-10; still 0 11; late _created 12; handoff 14-15.",
            next_note="Next: Fluent Bit elasticsearch output vs Loki.",
            query_cmd=(
                "curl -sS -G $MIMIR/prometheus/api/v1/query "
                "--data-urlencode 'query=sum(increase(http_requests_total{service=\"catering-uplift-svc\"}[5m]))'"
            ),
            false_cmd="rg 'scrape_native|enable-feature' prom/caterup-scrape.yaml",
            reload_cmd=(
                "kubectl -n prom rollout restart deploy/prom-scrape && "
                "kubectl -n prom rollout status deploy/prom-scrape --timeout=90s"
            ),
            requery_cmd=(
                "curl -sS -G $MIMIR/prometheus/api/v1/query "
                "--data-urlencode 'query=sum(increase(http_requests_total{service=\"catering-uplift-svc\"}[5m]))'"
            ),
            denied_cmd="kubectl -n grafana auth can-i patch configmap/grafana-dashboards --as=sre-bot",
            xfail_cmd=_xfail("caterup_om", "lav/cater dashboards owned by metrics-platform"),
            wrong_old="scrape_protocols: [OpenMetricsText1.0.0]",
            wrong_new="scrape_protocols: [PrometheusProto]  # native leftover",
            wrong2_old="enable-feature: []",
            wrong2_new="enable-feature: [native-histograms]",
            ticket_path="tickets/OBS-5115.md",
            ticket_body=(
                "OBS-5115: catering-uplift-svc increase() still 0. Native proto leftover. "
                "http_requests_total_created present. Need rate() or drop created-ts. No RBAC.\n"
            ),
            goal="catering-uplift-svc dashboard caterup-om-nhist uplift RPS is 0. Restore rps.",
            plan="Switch scrape to PrometheusProto native (r187 leftover).",
            outcome="Native proto; increase() still 0. Late _created. Handoff OBS-5115.",
            obs1='[{"uid":"caterup-om-nhist","title":"catering uplift rps"}]',
            obs2='{"title":"uplift RPS","targets":[{"expr":"sum(increase(http_requests_total{service=\\"catering-uplift-svc\\"}[5m]))"}]}',
            obs3='{"status":"success","data":{"result":[{"value":[1710000000,"0"]}]}}',
            obs4="scrape_protocols: [OpenMetricsText1.0.0]  # treated as maybe native",
            obs5="OM 1.0 scrape",
            obs6="prom/caterup-scrape.yaml",
            obs7="patched PrometheusProto",
            obs8='deployment "prom-scrape" successfully rolled out',
            obs9='{"status":"success","data":{"result":[{"value":[1710000000,"0"]}]}}',
            obs10="patched native-histograms feature",
            obs11='{"status":"success","data":{"result":[{"value":[1710000000,"0"]}]}}',
            obs12="http_requests_total_created still present; increase() reset; need rate()",
            obs13="no",
            obs14="wrote tickets/OBS-5115.md",
            obs15="xfail tests/test_caterup_om.py",
            **_gs("caterup-om-nhist"),
        ),
    )
)

# r206 Fluent Bit elasticsearch output vs Loki (NOT OS datasource URL, NOT Vector VRL)
MORE.append(
    (
        _ok(
            slug="fb-es-output-vs-loki",
            service="pushback-svc",
            dashboard_uid="pushback-fb-7",
            panel="pushback errors",
            query='{job="pushback-svc"} |= "towbar_mismatch"',
            lie="Fluent Bit output is elasticsearch (OpenSearch); Grafana Loki {job=pushback-svc} never ingested",
            false_lead="Loki datasource URL rewritten to OpenSearch / VictoriaLogs",
            config_path="grafana/provisioning/datasources/pushback-logs.yaml",
            lie_path="fluent-bit/pushback.conf",
            truth_name="OpenSearch pushback index",
            reload_name="fluent-bit",
            side="OpenSearch index still queryable",
            surfaces="Fluent Bit elasticsearch output vs Loki {job}",
            avoided="r191 OS URL rewrite; r200 Vector del(.job); r161 VL LogsQL",
            this_is="Fluent Bit [OUTPUT] Name es, no Loki output",
            step_note="False lead OS URL 4-5; FB es output 6-8; add Loki output 9-12.",
            query_cmd=(
                "curl -sS -G $LOKI/loki/api/v1/query_range "
                "--data-urlencode 'query={job=\"pushback-svc\"} |= \"towbar_mismatch\"' "
                "| jq '.data.result|length'"
            ),
            false_cmd=(
                "yq -r '.datasources[]|{name,type,url}' "
                "grafana/provisioning/datasources/pushback-logs.yaml"
            ),
            truth_cmd=(
                "curl -sS $OS/pushback-*/_search "
                "-d '{\"query\":{\"match\":{\"log\":\"towbar_mismatch\"}}}' "
                "| jq '{total:.hits.total.value}'"
            ),
            confirm_cmd="rg -n '\\[OUTPUT\\]|Name |Host ' fluent-bit/pushback.conf",
            reload_cmd=(
                "kubectl -n logging rollout restart daemonset/fluent-bit && "
                "kubectl -n logging rollout status daemonset/fluent-bit --timeout=90s"
            ),
            requery_cmd=(
                "curl -sS -G $LOKI/loki/api/v1/query_range "
                "--data-urlencode 'query={job=\"pushback-svc\"} |= \"towbar_mismatch\"' "
                "| jq '.data.result|length'"
            ),
            side_cmd=(
                "curl -sS $OS/pushback-*/_search "
                "-d '{\"query\":{\"match\":{\"job\":\"pushback-svc\"}}}' | jq '.hits.total.value'"
            ),
            final_cmd="rg -n 'Name loki|Match' fluent-bit/pushback.conf",
            patch_old="[OUTPUT]\n    Name  es\n    Match *\n    Host  opensearch-logs\n    Port  9200",
            patch_new=(
                "[OUTPUT]\n    Name  loki\n    Match *\n    Host  loki.obs.svc\n    Port  3100\n"
                "    Labels job=pushback-svc"
            ),
            runbook_path="runbooks/pushback-fb-loki.md",
            runbook=(
                "# pushback-svc Fluent Bit vs Loki\n"
                "[OUTPUT] Name es to OpenSearch. Grafana Loki never ingested.\n"
                "Not datasource URL rewrite and not Vector VRL.\n"
            ),
            goal=(
                "pushback-svc dashboard pushback-fb-7 pushback errors empty. OpenSearch has "
                "towbar_mismatch. Find the Fluent Bit output lie."
            ),
            plan="Empty Loki → OS URL (false) → FB es output → Loki output.",
            outcome="Fluent Bit Loki output. 33 streams. OpenSearch still has the index.",
            obs1='[{"uid":"pushback-fb-7","title":"pushback logs"}]',
            obs2='{"title":"pushback errors","targets":[{"expr":"{job=\\"pushback-svc\\"} |= \\"towbar_mismatch\\""}]}',
            obs3="0",
            obs4='{"name":"pushback-logs","type":"loki","url":"http://loki.obs.svc:3100"}\n# real Loki — not r191',
            obs5="datasource URL is Loki",
            obs6="[OUTPUT]\n    Name  es\n    Host  opensearch-logs",
            obs7='{"total":33}',
            obs8="Fluent Bit ships ES only; Loki empty",
            obs9="patched [OUTPUT] Name loki",
            obs10='daemonset "fluent-bit" successfully rolled out',
            obs11="33",
            obs12='{"name":"Logs"}',
            obs13="33",
            obs14="wrote runbooks/pushback-fb-loki.md",
            obs15="Name loki",
            **_g("pushback-fb-7"),
        ),
        _fail(
            slug="fb-vl-logsql-not-es-output",
            service="water-service-svc",
            dashboard_uid="water-fb-vl",
            panel="water logs",
            query='{job="water-service-svc"} |= "potable_low"',
            lie="VictoriaLogs LogsQL against a Loki datasource does not pull Fluent Bit elasticsearch documents into Loki",
            false_lead="VictoriaLogs LogsQL vs Loki LogQL URL",
            config_path="grafana/provisioning/datasources/water-logs.yaml",
            lie_path="fluent-bit/water.conf",
            wrong_path="grafana/dashboards/water-fb-vl.json",
            reload_name="grafana",
            ticket="OBS-5116",
            xfail="tests/test_water_fb.py",
            surfaces="VL LogsQL leftover vs Fluent Bit es output",
            avoided="r161 as actual RCA",
            this_is="fail/handoff: LogsQL rewrite, FB still es-only",
            step_note="LogsQL 6-10; still 0 11; late FB es 12; handoff 14-15.",
            next_note="Catalog r191-r206. Keep unique: not IRM/AM, not Prom agent, not VL URL, not Sentry/DD/NR/Faro/Beyla/Elastic.",
            query_cmd=(
                "curl -sS -G $LOKI/loki/api/v1/query_range "
                "--data-urlencode 'query={job=\"water-service-svc\"} |= \"potable_low\"' "
                "| jq '.data.result|length'"
            ),
            false_cmd=(
                "yq -r '.datasources[]|{name,type,url}' "
                "grafana/provisioning/datasources/water-logs.yaml"
            ),
            reload_cmd=(
                "kubectl -n grafana rollout restart deploy/grafana && "
                "kubectl -n grafana rollout status deploy/grafana --timeout=90s"
            ),
            requery_cmd=(
                "curl -sS $VL/select/logsql/query -d 'q=_stream:water-service-svc' | jq 'length'"
            ),
            denied_cmd="kubectl -n logging auth can-i patch daemonset/fluent-bit --as=sre-bot",
            xfail_cmd=_xfail("water_fb", "fluent-bit ds owned by platform-logging"),
            wrong_old='{job="water-service-svc"} |= "potable_low"',
            wrong_new='_stream:water-service-svc potable_low  # LogsQL leftover',
            wrong2_old="datasource: loki",
            wrong2_new="datasource: loki\n      # url comment: maybe VL",
            ticket_path="tickets/OBS-5116.md",
            ticket_body=(
                "OBS-5116: water-service-svc Loki still 0. LogsQL rewrite irrelevant. "
                "fluent-bit/water.conf [OUTPUT] Name es. Need Loki output. No RBAC.\n"
            ),
            goal="water-service-svc dashboard water-fb-vl water logs empty. Restore Loki rows.",
            plan="Rewrite panel to VictoriaLogs LogsQL (r161 leftover).",
            outcome="LogsQL on Loki ds; still 0. Late FB es output. Handoff OBS-5116.",
            obs1='[{"uid":"water-fb-vl","title":"water service logs"}]',
            obs2='{"title":"water logs","targets":[{"expr":"{job=\\"water-service-svc\\"} |= \\"potable_low\\""}]}',
            obs3="0",
            obs4='{"name":"water-logs","type":"loki","url":"http://loki.obs.svc:3100"}',
            obs5="URL is Loki — treated as maybe VL rewrite",
            obs6="grafana/dashboards/water-fb-vl.json",
            obs7="patched LogsQL _stream",
            obs8='deployment "grafana" successfully rolled out',
            obs9="0",
            obs10="patched url comment maybe VL",
            obs11="0",
            obs12="fluent-bit/water.conf [OUTPUT] Name es Host opensearch-logs",
            obs13="no",
            obs14="wrote tickets/OBS-5116.md",
            obs15="xfail tests/test_water_fb.py",
            **_gs("water-fb-vl"),
        ),
    )
)
