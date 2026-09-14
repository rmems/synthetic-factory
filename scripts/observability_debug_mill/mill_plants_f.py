"""Observability plants r191-r198. Do not clone r109-r190."""

from mill_plants import _fail, _ok

MORE = []


def _g(uid: str) -> dict:
    return {
        "search_cmd": (
            f"curl -sS $GRAFANA/api/search?query={uid} | jq -c '.[]|{{uid,title}}'"
        ),
        "dash_cmd": (
            f"curl -sS $GRAFANA/api/dashboards/uid/{uid} | jq '.dashboard.panels[0]'"
        ),
        "grafana_ok_cmd": (
            f"curl -sS $GRAFANA/api/ds/query -d @/tmp/{uid}.json | "
            "jq '.results.A.frames[0].schema'"
        ),
    }


def _gs(uid: str) -> dict:
    return {
        "search_cmd": (
            f"curl -sS $GRAFANA/api/search?query={uid} | jq -c '.[]|{{uid,title}}'"
        ),
        "dash_cmd": (
            f"curl -sS $GRAFANA/api/dashboards/uid/{uid} | jq '.dashboard.panels[0]'"
        ),
    }


def _xfail(name: str, reason: str) -> str:
    return (
        "printf '%s\\n' "
        f"'@pytest.mark.xfail(reason=\"{reason}\")\\n"
        f"def test_{name}():\\n    assert False' > tests/test_{name}.py"
    )


# r191 OpenSearch Query DSL vs Loki LogQL (NOT VictoriaLogs, NOT bloom/SM)
MORE.append(
    (
        _ok(
            slug="os-querydsl-vs-loki-logql",
            service="pax-manifest-svc",
            dashboard_uid="pax-os-loki-1",
            panel="manifest errors",
            query='{job="pax-manifest-svc"} |= "manifest_mismatch"',
            lie="Grafana Loki datasource URL rewritten to OpenSearch which speaks Query DSL not LogQL",
            false_lead="Loki bloom-gateway skip_factor / SM allowlist",
            config_path="helm/loki/pax-values.yaml",
            lie_path="grafana/provisioning/datasources/pax-logs.yaml",
            truth_name="OpenSearch _search hits",
            reload_name="grafana",
            side="VictoriaLogs tenants untouched",
            surfaces="OpenSearch Query DSL vs Loki LogQL datasource URL",
            avoided="r161 VL LogsQL; r165 bloom skip; r109 Loki SM allowlist",
            this_is="Loki datasource type pointed at OpenSearch :9200",
            step_note="False lead bloom/SM 4-5; OS URL 6-8; retarget Loki 9-12.",
            query_cmd=(
                "curl -sS -G $LOKI/loki/api/v1/query_range "
                "--data-urlencode 'query={job=\"pax-manifest-svc\"} |= \"manifest_mismatch\"'"
            ),
            false_cmd=(
                "yq '.bloom_gateway,.limits_config.shard_streams' helm/loki/pax-values.yaml"
            ),
            truth_cmd=(
                "curl -sS $OS/pax-manifest-*/_search "
                "-H 'Content-Type: application/json' "
                "-d '{\"query\":{\"match\":{\"job\":\"pax-manifest-svc\"}}}' "
                "| jq '{total:.hits.total.value,index:.hits.hits[0]._index}'"
            ),
            confirm_cmd=(
                "yq -r '.datasources[]|{name,type,url}' "
                "grafana/provisioning/datasources/pax-logs.yaml"
            ),
            reload_cmd=(
                "kubectl -n grafana rollout restart deploy/grafana && "
                "kubectl -n grafana rollout status deploy/grafana --timeout=90s"
            ),
            requery_cmd=(
                "curl -sS -G $LOKI/loki/api/v1/query_range "
                "--data-urlencode 'query={job=\"pax-manifest-svc\"} |= \"manifest_mismatch\"' "
                "| jq '.data.result|length'"
            ),
            side_cmd=(
                "curl -sS $VL/select/logsql/query -d 'q=_stream:gate-board-svc' | jq 'length'"
            ),
            final_cmd=(
                "yq -r '.datasources[]|select(.name==\"pax-logs\")|{type,url}' "
                "grafana/provisioning/datasources/pax-logs.yaml"
            ),
            patch_old="url: http://opensearch-logs:9200\n  type: loki",
            patch_new="url: http://loki.obs.svc:3100\n  type: loki",
            runbook_path="runbooks/pax-os-loki.md",
            runbook=(
                "# pax-manifest-svc OpenSearch vs Loki\n"
                "Datasource type loki pointed at OpenSearch :9200. LogQL is not Query DSL.\n"
                "Not VictoriaLogs and not bloom skip_factor.\n"
            ),
            goal=(
                "pax-manifest-svc dashboard pax-os-loki-1 manifest errors is empty "
                "while OpenSearch has hits. Find the LogQL-vs-Query-DSL lie."
            ),
            plan=(
                "Empty Loki panel → bloom/SM (false) → datasource URL is OpenSearch "
                "→ retarget Loki :3100."
            ),
            outcome=(
                "pax-logs URL retargeted to Loki. LogQL returns 41 streams. "
                "VictoriaLogs tenants unchanged. Not bloom, not VL."
            ),
            obs1='[{"uid":"pax-os-loki-1","title":"pax manifest logs"}]',
            obs2='{"title":"manifest errors","targets":[{"datasource":"pax-logs","expr":"{job=\\"pax-manifest-svc\\"} |= \\"manifest_mismatch\\""}]}',
            obs3='{"status":"success","data":{"resultType":"streams","result":[]}}\n# Grafana: parse error or empty — LogQL hit OpenSearch',
            obs4="bloom_gateway: {enabled: false}\nshard_streams: {enabled: false}\n# not r165 / not SM allowlist",
            obs5="Loki blooms off; SM allowlist absent",
            obs6='{"name":"pax-logs","type":"loki","url":"http://opensearch-logs:9200"}',
            obs7='{"total":128,"index":"pax-manifest-2026.08.19"}',
            obs8="type loki + OpenSearch URL — Query DSL only; LogQL empty",
            obs9="patched url to loki.obs.svc:3100 type loki",
            obs10='deployment "grafana" successfully rolled out',
            obs11="41",
            obs12='{"name":"Logs"}',
            obs13="12",
            obs14="wrote runbooks/pax-os-loki.md",
            obs15='{"type":"loki","url":"http://loki.obs.svc:3100"}',
            **_g("pax-os-loki-1"),
        ),
        _fail(
            slug="os-json-parser-on-querydsl",
            service="cabin-assign-svc",
            dashboard_uid="cabin-os-dsl",
            panel="assign errors",
            query='{job="cabin-assign-svc"} | json | level="error"',
            lie="Adding Loki | json does not turn OpenSearch Query DSL into LogQL; URL is still OpenSearch",
            false_lead="Loki json parser / VL LogsQL leftover",
            config_path="helm/loki/cabin-values.yaml",
            lie_path="grafana/provisioning/datasources/cabin-logs.yaml",
            wrong_path="grafana/dashboards/cabin-os-dsl.json",
            reload_name="grafana",
            ticket="OBS-5101",
            xfail="tests/test_cabin_os.py",
            surfaces="LogQL | json leftover vs OpenSearch URL",
            avoided="r161 | json on VL as actual RCA",
            this_is="fail/handoff: | json on Loki panel, datasource still OpenSearch",
            step_note="| json 6-10; still empty 11; late OS URL 12; handoff 14-15.",
            next_note="Next: k6 OTLP HTTP vs Tempo gRPC.",
            query_cmd=(
                "curl -sS -G $LOKI/loki/api/v1/query_range "
                "--data-urlencode 'query={job=\"cabin-assign-svc\"} | json | level=\"error\"'"
            ),
            false_cmd="jq '.panels[0].targets[0].expr' grafana/dashboards/cabin-os-dsl.json",
            reload_cmd=(
                "kubectl -n grafana rollout restart deploy/grafana && "
                "kubectl -n grafana rollout status deploy/grafana --timeout=90s"
            ),
            requery_cmd=(
                "curl -sS -G $LOKI/loki/api/v1/query_range "
                "--data-urlencode 'query={job=\"cabin-assign-svc\"} | json | level=\"error\"' "
                "| jq '.data.result|length'"
            ),
            denied_cmd="kubectl -n grafana auth can-i patch configmap/grafana-datasources --as=sre-bot",
            xfail_cmd=_xfail("cabin_os", "cabin-logs datasource owned by obs-platform"),
            wrong_old='{job="cabin-assign-svc"} |= "error"',
            wrong_new='{job="cabin-assign-svc"} | json | level="error"',
            wrong2_old='datasource: loki',
            wrong2_new='datasource: loki\n      editorMode: code',
            ticket_path="tickets/OBS-5101.md",
            ticket_body=(
                "OBS-5101: cabin-assign-svc panel still empty. | json did not help. "
                "cabin-logs type=loki url=http://opensearch-logs:9200. Need URL→Loki. No RBAC.\n"
            ),
            goal="cabin-assign-svc dashboard cabin-os-dsl assign errors is empty. Make LogQL return rows.",
            plan="Add | json (r161 leftover) so the Loki parser extracts level.",
            outcome="| json applied; still empty. Late OpenSearch URL. Handoff OBS-5101.",
            obs1='[{"uid":"cabin-os-dsl","title":"cabin assign logs"}]',
            obs2='{"title":"assign errors","targets":[{"expr":"{job=\\"cabin-assign-svc\\"} |= \\"error\\""}]}',
            obs3='{"status":"success","data":{"result":[]}}',
            obs4='"{job=\\"cabin-assign-svc\\"} |= \\"error\\""  # treated as missing | json',
            obs5="pipeline_stages json absent — treated as r161",
            obs6="grafana/dashboards/cabin-os-dsl.json",
            obs7="patched | json | level=error",
            obs8='deployment "grafana" successfully rolled out',
            obs9="0",
            obs10="patched editorMode code",
            obs11="0",
            obs12='cabin-logs type=loki url=http://opensearch-logs:9200 — Query DSL only',
            obs13="no",
            obs14="wrote tickets/OBS-5101.md",
            obs15="xfail tests/test_cabin_os.py",
            **_gs("cabin-os-dsl"),
        ),
    )
)

# r192 k6 OTLP HTTP vs Tempo gRPC (NOT Refinery, NOT Tempo MG, NOT Faro)
MORE.append(
    (
        _ok(
            slug="k6-otlp-http-vs-tempo-grpc",
            service="meal-cater-svc",
            dashboard_uid="cater-k6-tid-2",
            panel="k6 traces",
            query='{resource.service.name="meal-cater-svc" && resource.k6.test_run_id!=""}',
            lie="k6 --out experimental-opentelemetry speaks OTLP HTTP but endpoint is Tempo gRPC :4317 so spans never land",
            false_lead="Tempo metrics-generator missing dim / filter_policies skip",
            config_path="tempo/cater-mg.yaml",
            lie_path="k6/meal-cater.cloud.json",
            truth_name="k6 Cloud trace archive",
            reload_name="k6-operator",
            side="app OTel javaagent traces still in Tempo",
            surfaces="k6 OTLP HTTP exporter vs Tempo gRPC receiver",
            avoided="r178 Refinery dynsample; r164 MG filter; r175 Faro session",
            this_is="k6 experimental-opentelemetry HTTP/protobuf to Tempo :4317",
            step_note="False lead MG 4-5; k6 endpoint 4317 6-8; switch :4318 9-12.",
            query_cmd=(
                "curl -sS -G $TEMPO/api/search "
                "--data-urlencode 'q={resource.service.name=\"meal-cater-svc\" && resource.k6.test_run_id!=\"\"}' "
                "| jq '.traces|length'"
            ),
            false_cmd="yq '.metrics_generator.processor.span_metrics.filter_policies' tempo/cater-mg.yaml",
            truth_cmd=(
                "curl -sS $K6CLOUD/v3/tests/14211/traces | jq '{n:length,proto:.[0].exporter}'"
            ),
            confirm_cmd="jq '.exporters.experimental_opentelemetry' k6/meal-cater.cloud.json",
            reload_cmd=(
                "kubectl -n k6 rollout restart testdriver/meal-cater && "
                "kubectl -n k6 rollout status testdriver/meal-cater --timeout=120s"
            ),
            requery_cmd=(
                "curl -sS -G $TEMPO/api/search "
                "--data-urlencode 'q={resource.service.name=\"meal-cater-svc\" && resource.k6.test_run_id!=\"\"}' "
                "| jq '.traces|length'"
            ),
            side_cmd=(
                "curl -sS -G $TEMPO/api/search "
                "--data-urlencode 'q={resource.service.name=\"meal-cater-svc\" && resource.telemetry.sdk.language=\"java\"}' "
                "| jq '.traces|length'"
            ),
            final_cmd="jq -r '.exporters.experimental_opentelemetry.endpoint' k6/meal-cater.cloud.json",
            patch_old='endpoint: "http://tempo.obs.svc:4317"',
            patch_new='endpoint: "http://tempo.obs.svc:4318"\n    protocol: http/protobuf',
            runbook_path="runbooks/meal-k6-otlp.md",
            runbook=(
                "# meal-cater-svc k6 vs Tempo\n"
                "k6 experimental-opentelemetry is HTTP/protobuf. Tempo :4317 is gRPC.\n"
                "Point k6 at :4318. Not MG dims and not Refinery dynsample.\n"
            ),
            goal=(
                "meal-cater-svc dashboard cater-k6-tid-2 k6 traces is empty during load test "
                "14211. k6 Cloud still has spans. Find the HTTP-vs-gRPC lie."
            ),
            plan="Empty Tempo k6 search → MG filter (false) → k6 endpoint :4317 → switch :4318.",
            outcome="k6 OTLP HTTP to Tempo :4318. 64 k6 traces. Javaagent traces unchanged.",
            obs1='[{"uid":"cater-k6-tid-2","title":"meal cater k6"}]',
            obs2='{"title":"k6 traces","targets":[{"query":"{resource.service.name=\\"meal-cater-svc\\" && resource.k6.test_run_id!=\\"\\"}"}]}',
            obs3="0",
            obs4="filter_policies: []\n# MG not skipping — not r164",
            obs5="metrics_generator enabled; no skip policies",
            obs6='{"endpoint":"http://tempo.obs.svc:4317","protocol":"http/protobuf"}',
            obs7='{"n":64,"proto":"otlp-http"}',
            obs8="k6 HTTP/protobuf to gRPC 4317 — refused; archive only on k6 Cloud",
            obs9="patched endpoint :4318 protocol http/protobuf",
            obs10='testdriver "meal-cater" successfully rolled out',
            obs11="64",
            obs12='{"name":"Traces"}',
            obs13="31",
            obs14="wrote runbooks/meal-k6-otlp.md",
            obs15="http://tempo.obs.svc:4318",
            **_g("cater-k6-tid-2"),
        ),
        _fail(
            slug="k6-add-mg-dim-not-http",
            service="drink-cart-svc",
            dashboard_uid="drink-k6-route",
            panel="k6 http.route",
            query='{resource.service.name="drink-cart-svc" && span.http.route!=""}',
            lie="Adding Tempo metrics-generator http.route dim does not ingest k6 spans still sent HTTP/protobuf to gRPC :4317",
            false_lead="Tempo MG missing http.route dimension",
            config_path="tempo/drink-mg.yaml",
            lie_path="k6/drink-cart.cloud.json",
            wrong_path="tempo/drink-mg.yaml",
            reload_name="tempo-mg",
            ticket="OBS-5102",
            xfail="tests/test_drink_k6.py",
            surfaces="MG dim leftover vs k6 HTTP-to-gRPC",
            avoided="r164 as actual RCA",
            this_is="fail/handoff: added MG dim, k6 still hitting :4317",
            step_note="MG dim 6-10; still 0 11; late k6 4317 12; handoff 14-15.",
            next_note="Next: Honeycomb dataset name as Tempo tenant.",
            query_cmd=(
                "curl -sS -G $TEMPO/api/search "
                "--data-urlencode 'q={resource.service.name=\"drink-cart-svc\" && span.http.route!=\"\"}' "
                "| jq '.traces|length'"
            ),
            false_cmd="yq '.metrics_generator.processor.span_metrics.dimensions' tempo/drink-mg.yaml",
            reload_cmd=(
                "kubectl -n tempo rollout restart deploy/metrics-generator && "
                "kubectl -n tempo rollout status deploy/metrics-generator --timeout=90s"
            ),
            requery_cmd=(
                "curl -sS -G $TEMPO/api/search "
                "--data-urlencode 'q={resource.service.name=\"drink-cart-svc\" && span.http.route!=\"\"}' "
                "| jq '.traces|length'"
            ),
            denied_cmd="kubectl -n k6 auth can-i patch testdriver/drink-cart --as=sre-bot",
            xfail_cmd=_xfail("drink_k6", "k6 testdriver owned by perf-platform"),
            wrong_old="dimensions:\n      - http.method",
            wrong_new="dimensions:\n      - http.method\n      - http.route",
            wrong2_old="filter_policies: []",
            wrong2_new="filter_policies: []\n    # keep 200s (not r178)",
            ticket_path="tickets/OBS-5102.md",
            ticket_body=(
                "OBS-5102: drink-cart-svc k6 traces still 0. MG http.route dim added. "
                "k6 experimental-opentelemetry still http://tempo:4317 http/protobuf. Need :4318. No RBAC.\n"
            ),
            goal="drink-cart-svc dashboard drink-k6-route k6 http.route is empty during k6 run. Land traces.",
            plan="Add Tempo MG http.route dimension (r164 leftover).",
            outcome="MG dim added; Tempo still 0. Late k6 :4317 HTTP. Handoff OBS-5102.",
            obs1='[{"uid":"drink-k6-route","title":"drink cart k6"}]',
            obs2='{"title":"k6 http.route","targets":[{"query":"{resource.service.name=\\"drink-cart-svc\\" && span.http.route!=\\"\\"}"}]}',
            obs3="0",
            obs4="- http.method\n# no http.route — treated as r164 missing dim",
            obs5="span_metrics dimensions without http.route",
            obs6="tempo/drink-mg.yaml",
            obs7="patched dimensions +http.route",
            obs8='deployment "metrics-generator" successfully rolled out',
            obs9="0",
            obs10="patched comment keep 200s",
            obs11="0",
            obs12='k6/drink-cart.cloud.json endpoint http://tempo.obs.svc:4317 protocol http/protobuf',
            obs13="no",
            obs14="wrote tickets/OBS-5102.md",
            obs15="xfail tests/test_drink_k6.py",
            **_gs("drink-k6-route"),
        ),
    )
)

# r193 Honeycomb dataset as Tempo tenant (NOT Refinery dynsample)
MORE.append(
    (
        _ok(
            slug="hc-dataset-vs-tempo-tenant",
            service="ife-catalog-svc",
            dashboard_uid="ife-hc-ds-3",
            panel="ife traces",
            query='{resource.service.name="ife-catalog-svc"}',
            lie="Grafana Tempo x-scope-orgid is the Honeycomb dataset name ife-catalog; traces live in Tempo tenant airline",
            false_lead="Honeycomb Refinery dynsampler dropping 200s",
            config_path="refinery/ife-rules.toml",
            lie_path="grafana/provisioning/datasources/ife-tempo.yaml",
            truth_name="Tempo tenant airline search",
            reload_name="grafana",
            side="Honeycomb dataset ife-catalog still has traces via Refinery export",
            surfaces="Honeycomb dataset name vs Tempo tenant",
            avoided="r178 Refinery dynsample keyed on status/route",
            this_is="x-scope-orgid=ife-catalog Honeycomb dataset, not airline",
            step_note="False lead Refinery 4-5; orgid dataset 6-8; orgid airline 9-12.",
            query_cmd=(
                "curl -sS -G $TEMPO/api/search -H 'X-Scope-OrgID: ife-catalog' "
                "--data-urlencode 'q={resource.service.name=\"ife-catalog-svc\"}' "
                "| jq '.traces|length'"
            ),
            false_cmd="rg -n 'dynsampler|http.status|KeepRule' refinery/ife-rules.toml",
            truth_cmd=(
                "curl -sS -G $TEMPO/api/search -H 'X-Scope-OrgID: airline' "
                "--data-urlencode 'q={resource.service.name=\"ife-catalog-svc\"}' "
                "| jq '.traces|length'"
            ),
            confirm_cmd=(
                "yq -r '.datasources[]|{name,jsonData}' "
                "grafana/provisioning/datasources/ife-tempo.yaml"
            ),
            reload_cmd=(
                "kubectl -n grafana rollout restart deploy/grafana && "
                "kubectl -n grafana rollout status deploy/grafana --timeout=90s"
            ),
            requery_cmd=(
                "curl -sS -G $TEMPO/api/search -H 'X-Scope-OrgID: airline' "
                "--data-urlencode 'q={resource.service.name=\"ife-catalog-svc\"}' "
                "| jq '.traces|length'"
            ),
            side_cmd=(
                "curl -sS $HONEYCOMB/1/events/ife-catalog?limit=1 | jq '{dataset,count}'"
            ),
            final_cmd=(
                "yq -r '.datasources[]|select(.name==\"ife-tempo\")"
                ".jsonData.httpHeaderValue1' grafana/provisioning/datasources/ife-tempo.yaml"
            ),
            patch_old="httpHeaderName1: X-Scope-OrgID\n    httpHeaderValue1: ife-catalog",
            patch_new="httpHeaderName1: X-Scope-OrgID\n    httpHeaderValue1: airline",
            runbook_path="runbooks/ife-hc-tenant.md",
            runbook=(
                "# ife-catalog-svc Honeycomb dataset vs Tempo tenant\n"
                "Grafana copied Honeycomb dataset ife-catalog into X-Scope-OrgID.\n"
                "Tempo tenant is airline. Not Refinery dynsample.\n"
            ),
            goal=(
                "ife-catalog-svc dashboard ife-hc-ds-3 is empty. Honeycomb dataset "
                "ife-catalog still shows traces. Fix the tenant lie."
            ),
            plan="Empty Tempo → Refinery dynsample (false) → orgid=dataset → orgid=airline.",
            outcome="X-Scope-OrgID=airline. 38 traces. Honeycomb dataset export unchanged.",
            obs1='[{"uid":"ife-hc-ds-3","title":"ife catalog traces"}]',
            obs2='{"title":"ife traces","targets":[{"datasource":"ife-tempo","query":"{resource.service.name=\\"ife-catalog-svc\\"}"}]}',
            obs3="0",
            obs4="Sampler: EMADynamicSampler\nFieldList: [http.route]\n# keeps 200s — not r178 status_code drop",
            obs5="Refinery not dropping 200s; FieldList is route not status",
            obs6='{"name":"ife-tempo","jsonData":{"httpHeaderName1":"X-Scope-OrgID","httpHeaderValue1":"ife-catalog"}}',
            obs7="38",
            obs8="orgid ife-catalog is Honeycomb dataset; Tempo tenant airline has the traces",
            obs9="patched httpHeaderValue1 airline",
            obs10='deployment "grafana" successfully rolled out',
            obs11="38",
            obs12='{"name":"Traces"}',
            obs13='{"dataset":"ife-catalog","count":40}',
            obs14="wrote runbooks/ife-hc-tenant.md",
            obs15="airline",
            **_g("ife-hc-ds-3"),
        ),
        _fail(
            slug="hc-remove-refinery-not-tenant",
            service="jumpseat-svc",
            dashboard_uid="jump-hc-filter",
            panel="jump traces",
            query='{resource.service.name="jumpseat-svc"}',
            lie="Removing Tempo filter_policies / Refinery KeepRule does not change Grafana orgid=jumpseat Honeycomb dataset",
            false_lead="Refinery dynsample + Tempo filter_policies skip",
            config_path="refinery/jump-rules.toml",
            lie_path="grafana/provisioning/datasources/jump-tempo.yaml",
            wrong_path="tempo/jump-mg.yaml",
            reload_name="tempo-mg",
            ticket="OBS-5103",
            xfail="tests/test_jump_hc.py",
            surfaces="Refinery/MG leftover vs Honeycomb dataset orgid",
            avoided="r178 as actual RCA",
            this_is="fail/handoff: cleared filter_policies, orgid still jumpseat dataset",
            step_note="filter_policies 6-10; still 0 11; late orgid 12; handoff 14-15.",
            next_note="Next: Lightstep x-ot-span-context vs Tempo W3C.",
            query_cmd=(
                "curl -sS -G $TEMPO/api/search -H 'X-Scope-OrgID: jumpseat' "
                "--data-urlencode 'q={resource.service.name=\"jumpseat-svc\"}' "
                "| jq '.traces|length'"
            ),
            false_cmd="yq '.metrics_generator.processor.span_metrics.filter_policies' tempo/jump-mg.yaml",
            reload_cmd=(
                "kubectl -n tempo rollout restart deploy/metrics-generator && "
                "kubectl -n tempo rollout status deploy/metrics-generator --timeout=90s"
            ),
            requery_cmd=(
                "curl -sS -G $TEMPO/api/search -H 'X-Scope-OrgID: jumpseat' "
                "--data-urlencode 'q={resource.service.name=\"jumpseat-svc\"}' "
                "| jq '.traces|length'"
            ),
            denied_cmd="kubectl -n grafana auth can-i patch configmap/grafana-datasources --as=sre-bot",
            xfail_cmd=_xfail("jump_hc", "jump-tempo orgid owned by obs-platform"),
            wrong_old="filter_policies:\n      - include:\n          match_type: strict\n          services:\n            - jumpseat-svc",
            wrong_new="filter_policies: []",
            wrong2_old='KeepRule = "http.status_code != 200"',
            wrong2_new='KeepRule = "true"  # undo r178 leftover',
            ticket_path="tickets/OBS-5103.md",
            ticket_body=(
                "OBS-5103: jumpseat-svc Tempo search still 0 with orgid=jumpseat. "
                "Need X-Scope-OrgID=airline (Honeycomb dataset is not a Tempo tenant). No RBAC.\n"
            ),
            goal="jumpseat-svc dashboard jump-hc-filter is empty. Honeycomb still shows traces. Restore Tempo view.",
            plan="Clear Tempo filter_policies and Refinery KeepRule (r178 leftover).",
            outcome="filter_policies empty; still 0 on orgid=jumpseat. Late datasource dataset. Handoff OBS-5103.",
            obs1='[{"uid":"jump-hc-filter","title":"jumpseat traces"}]',
            obs2='{"title":"jump traces","targets":[{"query":"{resource.service.name=\\"jumpseat-svc\\"}"}]}',
            obs3="0",
            obs4="filter_policies include jumpseat-svc  # treated as skip leftover",
            obs5="MG filter present — treated as r164/r178",
            obs6="tempo/jump-mg.yaml",
            obs7="patched filter_policies []",
            obs8='deployment "metrics-generator" successfully rolled out',
            obs9="0",
            obs10="patched Refinery KeepRule true (wrong file via comment)",
            obs11="0",
            obs12="jump-tempo httpHeaderValue1=jumpseat (Honeycomb dataset). airline tenant has 22 traces.",
            obs13="no",
            obs14="wrote tickets/OBS-5103.md",
            obs15="xfail tests/test_jump_hc.py",
            **_gs("jump-hc-filter"),
        ),
    )
)

# r194 Lightstep x-ot-span-context vs Tempo W3C (NOT NR spanId, NOT Sentry event_id)
MORE.append(
    (
        _ok(
            slug="ls-otspanctx-vs-tempo-w3c",
            service="deadhead-svc",
            dashboard_uid="dead-ls-otctx-4",
            panel="LS paste",
            query="GET /api/traces/{ot-span-context}",
            lie="Grafana Tempo lookup of Lightstep x-ot-span-context (trace/span/sampled) as W3C 32-hex traceId",
            false_lead="New Relic spanId used as Tempo traceId",
            config_path="grafana/dashboards/dead-ls-otctx-4.json",
            lie_path="runbooks/deadhead-ls-paste.md",
            truth_name="OTel W3C trace_id on the same request",
            reload_name="grafana",
            side="Lightstep satellite still stores GUID traces",
            surfaces="Lightstep x-ot-span-context vs Tempo W3C trace_id",
            avoided="r184 NR spanId; r162 Sentry event_id; r175 Faro session",
            this_is="LS ot-span-context header pasted into Tempo /api/traces",
            step_note="False lead NR 4-5; ot-span-context 6-8; W3C var 9-12.",
            query_cmd=(
                "curl -sS $TEMPO/api/traces/deadhead/5f84a7c1b2c3d4e5/1 "
                "| jq '{status,error}'"
            ),
            false_cmd=(
                "jq '.templating.list[]|{name,query}' grafana/dashboards/dead-ls-otctx-4.json"
            ),
            truth_cmd=(
                "curl -sS $TEMPO/api/traces/aabbccddeeff00112233445566778899 "
                "| jq '.batches[0].resource.attributes[:4]'"
            ),
            confirm_cmd="rg -n 'ot-span-context|traceparent|nr_span' runbooks/deadhead-ls-paste.md",
            reload_cmd=(
                "kubectl -n grafana rollout restart deploy/grafana && "
                "kubectl -n grafana rollout status deploy/grafana --timeout=90s"
            ),
            requery_cmd=(
                "curl -sS $TEMPO/api/traces/aabbccddeeff00112233445566778899 "
                "| jq '.batches|length'"
            ),
            side_cmd=(
                "curl -sS $LIGHTSTEP/api/v1/traces?service=deadhead-svc | jq '{n:length,guid:.[0].guid}'"
            ),
            final_cmd=(
                "jq -r '.panels[0].targets[0].query' grafana/dashboards/dead-ls-otctx-4.json"
            ),
            patch_old="Paste Lightstep ot-span-context into Tempo traceId.",
            patch_new=(
                "Use W3C traceparent 32-hex. ot-span-context is Lightstep "
                "trace/span/sampled, not Tempo traceId."
            ),
            runbook_path="runbooks/deadhead-ls-w3c.md",
            runbook=(
                "# deadhead-svc Lightstep vs Tempo\n"
                "x-ot-span-context is LS GUID/span/flags. Tempo wants W3C 32-hex.\n"
                "Not New Relic spanId.\n"
            ),
            goal=(
                "deadhead-svc dashboard dead-ls-otctx-4 LS paste 404s in Tempo. "
                "Lightstep UI has the trace. Fix the header lie."
            ),
            plan="404 → NR spanId var (false) → runbook pastes ot-span-context → switch W3C.",
            outcome="Dashboard query uses W3C 32-hex. Tempo 1 batch. LS satellite unchanged.",
            obs1='[{"uid":"dead-ls-otctx-4","title":"deadhead LS paste"}]',
            obs2='{"title":"LS paste","targets":[{"query":"${ot_span_context}"}]}',
            obs3='{"status":"error","error":"trace not found: deadhead/5f84a7c1b2c3d4e5/1"}',
            obs4='{"name":"ot_span_context","query":"Lightstep header"}\n{"name":"nr_span_id","query":""}\n# nr var unused — not r184',
            obs5="nr_span_id empty; panel uses ot_span_context",
            obs6="Paste Lightstep ot-span-context into Tempo traceId.",
            obs7='[{"key":"service.name","value":"deadhead-svc"},{"key":"telemetry.sdk.name","value":"opentelemetry"}]',
            obs8="ot-span-context=trace/span/sampled; W3C is aabbccddeeff00112233445566778899",
            obs9="patched runbook + dashboard query to W3C",
            obs10='deployment "grafana" successfully rolled out',
            obs11="1",
            obs12='{"name":"Traces"}',
            obs13='{"n":9,"guid":"5f84a7c1b2c3d4e5"}',
            obs14="wrote runbooks/deadhead-ls-w3c.md",
            obs15="${traceparent}",
            **_g("dead-ls-otctx-4"),
        ),
        _fail(
            slug="ls-enable-dd-128-not-otctx",
            service="crew-hotel-svc",
            dashboard_uid="hotel-ls-dd",
            panel="hotel LS paste",
            query="GET /api/traces/{ot-span-context}",
            lie="Enabling DD 128-bit flags does not decode Lightstep x-ot-span-context into a Tempo W3C traceId",
            false_lead="Datadog 64-bit tid vs OTel 128-bit",
            config_path="k8s/dd-agent/crew-hotel.env",
            lie_path="grafana/dashboards/hotel-ls-dd.json",
            wrong_path="k8s/dd-agent/crew-hotel.env",
            reload_name="crew-hotel-svc",
            ticket="OBS-5104",
            xfail="tests/test_hotel_ls.py",
            surfaces="DD 128-bit leftover vs Lightstep ot-span-context",
            avoided="r163 / r184 as actual RCA",
            this_is="fail/handoff: DD_TRACE_128_BIT on, LS paste still 404",
            step_note="DD 128-bit 6-10; still 404 11; late ot-span-context 12; handoff 14-15.",
            next_note="Next: SigNoz ClickHouse query-service vs Tempo TraceQL.",
            query_cmd="curl -sS $TEMPO/api/traces/hotel/aa11bb22cc33dd44/1 | jq '{error}'",
            false_cmd="rg 'DD_TRACE_128_BIT|OTEL_PROPAGATORS' k8s/dd-agent/crew-hotel.env",
            reload_cmd=(
                "kubectl -n hotel rollout restart deploy/crew-hotel-svc && "
                "kubectl -n hotel rollout status deploy/crew-hotel-svc --timeout=90s"
            ),
            requery_cmd="curl -sS $TEMPO/api/traces/hotel/aa11bb22cc33dd44/1 | jq '{error}'",
            denied_cmd="kubectl -n grafana auth can-i patch configmap/grafana-dashboards --as=sre-bot",
            xfail_cmd=_xfail("hotel_ls", "hotel dashboard owned by irm-platform"),
            wrong_old="DD_TRACE_128_BIT=false",
            wrong_new="DD_TRACE_128_BIT=true",
            wrong2_old="OTEL_PROPAGATORS=datadog",
            wrong2_new="OTEL_PROPAGATORS=datadog,tracecontext",
            ticket_path="tickets/OBS-5104.md",
            ticket_body=(
                "OBS-5104: crew-hotel-svc Tempo still 404 on ot-span-context paste. "
                "DD 128-bit did not decode Lightstep header. Need W3C traceparent var. No RBAC.\n"
            ),
            goal="crew-hotel-svc dashboard hotel-ls-dd LS paste 404s. Make Tempo open the trace.",
            plan="Enable DD_TRACE_128_BIT (r163 leftover) so ids widen.",
            outcome="DD 128-bit on; paste still 404. Late ot-span-context. Handoff OBS-5104.",
            obs1='[{"uid":"hotel-ls-dd","title":"crew hotel LS"}]',
            obs2='{"title":"hotel LS paste","targets":[{"query":"${ot_span_context}"}]}',
            obs3='{"error":"trace not found"}',
            obs4="DD_TRACE_128_BIT=false  # treated as r163",
            obs5="64-bit DD flag off",
            obs6="k8s/dd-agent/crew-hotel.env",
            obs7="patched DD_TRACE_128_BIT=true",
            obs8='deployment "crew-hotel-svc" successfully rolled out',
            obs9='{"error":"trace not found"}',
            obs10="patched OTEL_PROPAGATORS +tracecontext",
            obs11='{"error":"trace not found"}',
            obs12="panel query ${ot_span_context}=hotel/aa11bb22cc33dd44/1 Lightstep header; W3C lives at ff00ee11dd22cc33bb44aa5566778899",
            obs13="no",
            obs14="wrote tickets/OBS-5104.md",
            obs15="xfail tests/test_hotel_ls.py",
            **_gs("hotel-ls-dd"),
        ),
    )
)

# r195 SigNoz query-service vs Tempo TraceQL (NOT ClickHouse SQL table, NOT Elastic)
MORE.append(
    (
        _ok(
            slug="signoz-qs-vs-tempo-traceql",
            service="wifi-auth-svc",
            dashboard_uid="wifi-sz-ch-5",
            panel="auth traces",
            query='{resource.service.name="wifi-auth-svc"}',
            lie="Grafana Tempo datasource URL rewritten to SigNoz query-service; TraceQL is not SigNoz ClickHouse filter JSON",
            false_lead="ClickHouse otel.traces vs otel_traces_dist table name",
            config_path="clickhouse/wifi-ddl.sql",
            lie_path="grafana/provisioning/datasources/wifi-tempo.yaml",
            truth_name="SigNoz /api/v1/traces JSON",
            reload_name="grafana",
            side="ClickHouse signoz_index_v2 still holds rows",
            surfaces="SigNoz query-service vs Tempo TraceQL",
            avoided="r189 ClickHouse SQL vs Tempo table; Elastic txn.name; Tempo MG",
            this_is="Tempo datasource type pointed at SigNoz query-service :8080",
            step_note="False lead CH table 4-5; SigNoz URL 6-8; retarget Tempo 9-12.",
            query_cmd=(
                "curl -sS $TEMPO/api/search --data-urlencode "
                "'q={resource.service.name=\"wifi-auth-svc\"}' | jq '{status,error}'"
            ),
            false_cmd="rg 'otel.traces|otel_traces_dist' clickhouse/wifi-ddl.sql",
            truth_cmd=(
                "curl -sS $SIGNOZ/api/v1/traces?service=wifi-auth-svc | jq '{n:(.data|length),engine}'"
            ),
            confirm_cmd=(
                "yq -r '.datasources[]|{name,type,url}' "
                "grafana/provisioning/datasources/wifi-tempo.yaml"
            ),
            reload_cmd=(
                "kubectl -n grafana rollout restart deploy/grafana && "
                "kubectl -n grafana rollout status deploy/grafana --timeout=90s"
            ),
            requery_cmd=(
                "curl -sS -G $TEMPO/api/search "
                "--data-urlencode 'q={resource.service.name=\"wifi-auth-svc\"}' "
                "| jq '.traces|length'"
            ),
            side_cmd=(
                "clickhouse-client -q \"SELECT count() FROM signoz_index_v2 "
                "WHERE serviceName='wifi-auth-svc'\""
            ),
            final_cmd=(
                "yq -r '.datasources[]|select(.name==\"wifi-tempo\")|{type,url}' "
                "grafana/provisioning/datasources/wifi-tempo.yaml"
            ),
            patch_old="url: http://signoz-query:8080\n  type: tempo",
            patch_new="url: http://tempo.obs.svc:3200\n  type: tempo",
            runbook_path="runbooks/wifi-signoz-tempo.md",
            runbook=(
                "# wifi-auth-svc SigNoz vs Tempo\n"
                "Grafana Tempo type pointed at SigNoz query-service. TraceQL is not CH filter.\n"
                "Not r189 table-name lie.\n"
            ),
            goal=(
                "wifi-auth-svc dashboard wifi-sz-ch-5 auth traces errors. SigNoz UI has spans. "
                "Find the TraceQL-vs-SigNoz lie."
            ),
            plan="TraceQL error → CH table name (false) → datasource URL SigNoz → Tempo :3200.",
            outcome="wifi-tempo URL is Tempo. 19 traces. signoz_index_v2 still has rows.",
            obs1='[{"uid":"wifi-sz-ch-5","title":"wifi auth traces"}]',
            obs2='{"title":"auth traces","targets":[{"datasource":"wifi-tempo","query":"{resource.service.name=\\"wifi-auth-svc\\"}"}]}',
            obs3='{"status":"error","error":"json: cannot unmarshal TraceQL into SigNoz Filter"}',
            obs4="CREATE TABLE signoz_index_v2  # not otel.traces — not r189",
            obs5="no otel.traces / _dist mismatch",
            obs6='{"name":"wifi-tempo","type":"tempo","url":"http://signoz-query:8080"}',
            obs7='{"n":19,"engine":"clickhouse-signoz"}',
            obs8="Tempo type + SigNoz query-service URL — TraceQL rejected",
            obs9="patched url tempo.obs.svc:3200 type tempo",
            obs10='deployment "grafana" successfully rolled out',
            obs11="19",
            obs12='{"name":"Traces"}',
            obs13="19",
            obs14="wrote runbooks/wifi-signoz-tempo.md",
            obs15='{"type":"tempo","url":"http://tempo.obs.svc:3200"}',
            **_g("wifi-sz-ch-5"),
        ),
        _fail(
            slug="signoz-sql-table-not-qs",
            service="crew-transport-svc",
            dashboard_uid="crew-sz-sql",
            panel="transport SQL",
            query="SELECT trace_id FROM otel.traces WHERE service_name='crew-transport-svc'",
            lie="Re-pointing Grafana SQL at otel_traces_dist does not make Tempo TraceQL work against SigNoz query-service",
            false_lead="ClickHouse otel.traces table missing (_dist leftover)",
            config_path="grafana/dashboards/crew-sz-sql.json",
            lie_path="grafana/provisioning/datasources/crew-tempo.yaml",
            wrong_path="grafana/dashboards/crew-sz-sql.json",
            reload_name="grafana",
            ticket="OBS-5105",
            xfail="tests/test_crew_sz.py",
            surfaces="CH SQL leftover vs SigNoz query-service URL",
            avoided="r189 as actual RCA",
            this_is="fail/handoff: SQL retarget _dist, traces panel still SigNoz URL",
            step_note="SQL _dist 6-10; traces still error 11; late SigNoz URL 12; handoff 14-15.",
            next_note="Next: Uptrace span.group_id vs Tempo traceId.",
            query_cmd=(
                "curl -sS $GRAFANA/api/ds/query -d @/tmp/crew-sz-sql.json | jq '.results.A.error'"
            ),
            false_cmd="jq '.panels[0].targets[0].rawSql' grafana/dashboards/crew-sz-sql.json",
            reload_cmd=(
                "kubectl -n grafana rollout restart deploy/grafana && "
                "kubectl -n grafana rollout status deploy/grafana --timeout=90s"
            ),
            requery_cmd=(
                "curl -sS -G $TEMPO/api/search "
                "--data-urlencode 'q={resource.service.name=\"crew-transport-svc\"}' "
                "| jq '{status,error}'"
            ),
            denied_cmd="kubectl -n grafana auth can-i patch configmap/grafana-datasources --as=sre-bot",
            xfail_cmd=_xfail("crew_sz", "crew-tempo datasource owned by obs-platform"),
            wrong_old="SELECT trace_id FROM otel.traces WHERE service_name='crew-transport-svc'",
            wrong_new="SELECT trace_id FROM otel_traces_dist WHERE service_name='crew-transport-svc'",
            wrong2_old="uid: crew-sz-sql",
            wrong2_new="uid: crew-sz-sql-v2",
            ticket_path="tickets/OBS-5105.md",
            ticket_body=(
                "OBS-5105: crew-transport-svc TraceQL still unmarshal error. SQL _dist "
                "is a red herring. crew-tempo url=http://signoz-query:8080. Need Tempo :3200. No RBAC.\n"
            ),
            goal="crew-transport-svc dashboard crew-sz-sql traces error. Restore Tempo search.",
            plan="Retarget SQL to otel_traces_dist (r189 leftover).",
            outcome="SQL _dist still empty/wrong engine. Late SigNoz URL. Handoff OBS-5105.",
            obs1='[{"uid":"crew-sz-sql","title":"crew transport traces"}]',
            obs2='"SELECT trace_id FROM otel.traces WHERE service_name = \'crew-transport-svc\'"',
            obs3='"json: cannot unmarshal TraceQL into SigNoz Filter"',
            obs4="otel.traces  # treated as r189",
            obs5="SQL panel uses otel.traces",
            obs6="grafana/dashboards/crew-sz-sql.json",
            obs7="patched SQL otel_traces_dist",
            obs8='deployment "grafana" successfully rolled out',
            obs9='{"status":"error","error":"json: cannot unmarshal TraceQL into SigNoz Filter"}',
            obs10="patched uid v2",
            obs11='{"status":"error","error":"json: cannot unmarshal TraceQL into SigNoz Filter"}',
            obs12="crew-tempo type=tempo url=http://signoz-query:8080",
            obs13="no",
            obs14="wrote tickets/OBS-5105.md",
            obs15="xfail tests/test_crew_sz.py",
            **_gs("crew-sz-sql"),
        ),
    )
)

# r196 Uptrace span.group_id vs Tempo traceId (NOT Faro session)
MORE.append(
    (
        _ok(
            slug="uptrace-groupid-vs-tempo-tid",
            service="slot-pair-svc",
            dashboard_uid="slot-ut-grp-6",
            panel="Uptrace group",
            query="GET /api/traces/{span.group_id}",
            lie="Grafana Tempo search uses Uptrace span.group_id fingerprint as W3C traceId",
            false_lead="Grafana Faro session_id as Tempo traceId",
            config_path="grafana/dashboards/slot-ut-grp-6.json",
            lie_path="grafana/provisioning/datasources/slot-uptrace.yaml",
            truth_name="Uptrace span.trace_id vs group_id",
            reload_name="grafana",
            side="Uptrace error groups still keyed by group_id",
            surfaces="Uptrace span.group_id vs Tempo W3C trace_id",
            avoided="r175 Faro session; r162 Sentry event_id; r184 NR spanId",
            this_is="Uptrace group_id fingerprint pasted as Tempo traceId",
            step_note="False lead Faro 4-5; group_id var 6-8; W3C from Uptrace 9-12.",
            query_cmd="curl -sS $TEMPO/api/traces/18446744073709550000 | jq '{error}'",
            false_cmd=(
                "jq '.templating.list[]|{name,query}' grafana/dashboards/slot-ut-grp-6.json"
            ),
            truth_cmd=(
                "curl -sS $UPTRACE/api/v1/tracing/groups/18446744073709550000 "
                "| jq '{group_id,trace_id:.spans[0].trace_id}'"
            ),
            confirm_cmd=(
                "yq -r '.datasources[]|{name,type,url}' "
                "grafana/provisioning/datasources/slot-uptrace.yaml"
            ),
            reload_cmd=(
                "kubectl -n grafana rollout restart deploy/grafana && "
                "kubectl -n grafana rollout status deploy/grafana --timeout=90s"
            ),
            requery_cmd=(
                "curl -sS $TEMPO/api/traces/00112233445566778899aabbccddeeff "
                "| jq '.batches|length'"
            ),
            side_cmd=(
                "curl -sS $UPTRACE/api/v1/tracing/groups?service=slot-pair-svc | jq 'length'"
            ),
            final_cmd=(
                "jq -r '.panels[0].targets[0].query' grafana/dashboards/slot-ut-grp-6.json"
            ),
            patch_old='query: "${uptrace_group_id}"',
            patch_new='query: "${uptrace_trace_id}"  # W3C, not group fingerprint',
            runbook_path="runbooks/slot-uptrace-tid.md",
            runbook=(
                "# slot-pair-svc Uptrace vs Tempo\n"
                "span.group_id is a fingerprint, not W3C trace_id. Use Uptrace trace_id.\n"
                "Not Faro session_id.\n"
            ),
            goal=(
                "slot-pair-svc dashboard slot-ut-grp-6 Uptrace group 404s in Tempo. "
                "Uptrace still groups errors. Fix the fingerprint lie."
            ),
            plan="404 → Faro session var (false) → group_id fingerprint → W3C trace_id.",
            outcome="Panel uses uptrace_trace_id. Tempo 1 batch. Uptrace groups unchanged.",
            obs1='[{"uid":"slot-ut-grp-6","title":"slot pair uptrace"}]',
            obs2='{"title":"Uptrace group","targets":[{"query":"${uptrace_group_id}"}]}',
            obs3='{"error":"trace not found: 18446744073709550000"}',
            obs4='{"name":"faro_session_id","query":""}\n{"name":"uptrace_group_id","query":"Uptrace group"}\n# faro unused — not r175',
            obs5="faro_session_id empty",
            obs6='{"name":"slot-uptrace","type":"yesoreyeram-infinity-datasource","url":"http://uptrace:14318"}',
            obs7='{"group_id":"18446744073709550000","trace_id":"00112233445566778899aabbccddeeff"}',
            obs8="group_id is uint64 fingerprint; Tempo wants 32-hex",
            obs9="patched query ${uptrace_trace_id}",
            obs10='deployment "grafana" successfully rolled out',
            obs11="1",
            obs12='{"name":"Traces"}',
            obs13="7",
            obs14="wrote runbooks/slot-uptrace-tid.md",
            obs15="${uptrace_trace_id}",
            **_g("slot-ut-grp-6"),
        ),
        _fail(
            slug="uptrace-copy-faro-session",
            service="atc-delay-svc",
            dashboard_uid="atc-ut-faro",
            panel="atc group",
            query="GET /api/traces/{span.group_id}",
            lie="Writing Faro session_id into the Tempo variable does not turn Uptrace group_id fingerprints into W3C trace ids",
            false_lead="Faro session_id as Tempo traceId",
            config_path="grafana/dashboards/atc-ut-faro.json",
            lie_path="grafana/provisioning/datasources/atc-uptrace.yaml",
            wrong_path="grafana/dashboards/atc-ut-faro.json",
            reload_name="grafana",
            ticket="OBS-5106",
            xfail="tests/test_atc_ut.py",
            surfaces="Faro leftover vs Uptrace group_id",
            avoided="r175 as actual RCA",
            this_is="fail/handoff: copied Faro session into var, still 404 on group_id",
            step_note="Faro copy 6-10; still 404 11; late group_id 12; handoff 14-15.",
            next_note="Next: Parca Query API vs Pyroscope SelectMergeStacktraces.",
            query_cmd="curl -sS $TEMPO/api/traces/999888777666555444 | jq '{error}'",
            false_cmd="jq '.templating.list[]|{name}' grafana/dashboards/atc-ut-faro.json",
            reload_cmd=(
                "kubectl -n grafana rollout restart deploy/grafana && "
                "kubectl -n grafana rollout status deploy/grafana --timeout=90s"
            ),
            requery_cmd="curl -sS $TEMPO/api/traces/999888777666555444 | jq '{error}'",
            denied_cmd="kubectl -n grafana auth can-i patch configmap/grafana-datasources --as=sre-bot",
            xfail_cmd=_xfail("atc_ut", "atc-uptrace infinity ds owned by obs-platform"),
            wrong_old='query: "${uptrace_group_id}"',
            wrong_new='query: "${faro_session_id}"',
            wrong2_old='name: faro_session_id',
            wrong2_new='name: faro_session_id\n      regex: ".*"  # copy into resource leftover',
            ticket_path="tickets/OBS-5106.md",
            ticket_body=(
                "OBS-5106: atc-delay-svc Tempo still 404. Faro session swap did not help. "
                "Panel uses Uptrace group_id=999888777666555444. Need trace_id. No RBAC.\n"
            ),
            goal="atc-delay-svc dashboard atc-ut-faro Uptrace group 404s in Tempo. Open the trace.",
            plan="Point the Tempo var at Faro session_id (r175 leftover).",
            outcome="Faro session in query; still 404. Late Uptrace group_id. Handoff OBS-5106.",
            obs1='[{"uid":"atc-ut-faro","title":"atc delay uptrace"}]',
            obs2='{"title":"atc group","targets":[{"query":"${uptrace_group_id}"}]}',
            obs3='{"error":"trace not found"}',
            obs4='{"name":"faro_session_id"}\n{"name":"uptrace_group_id"}',
            obs5="faro var present — treated as r175",
            obs6="grafana/dashboards/atc-ut-faro.json",
            obs7="patched query ${faro_session_id}",
            obs8='deployment "grafana" successfully rolled out',
            obs9='{"error":"trace not found"}',
            obs10="patched faro regex leftover",
            obs11='{"error":"trace not found"}',
            obs12="atc-uptrace infinity url http://uptrace:14318; group_id=999888777666555444 fingerprint; W3C=ffeeddccbbaa99887766554433221100",
            obs13="no",
            obs14="wrote tickets/OBS-5106.md",
            obs15="xfail tests/test_atc_ut.py",
            **_gs("atc-ut-faro"),
        ),
    )
)

# r197 Parca Query vs Pyroscope SelectMergeStacktraces (NOT max_profile_size, NOT musl buildid)
MORE.append(
    (
        _ok(
            slug="parca-query-vs-pyro-select",
            service="weather-hold-svc",
            dashboard_uid="wx-parca-7",
            panel="CPU flame",
            query='process_cpu:cpu:nanoseconds:cpu:nanoseconds{service_name="weather-hold-svc"}',
            lie="Grafana Pyroscope datasource URL rewritten to Parca; SelectMergeStacktraces is not Parca Query/QueryRange",
            false_lead="Pyroscope ingestion.max_profile_size_bytes drop",
            config_path="pyroscope/wx-values.yaml",
            lie_path="grafana/provisioning/datasources/wx-profile.yaml",
            truth_name="Parca /profiles.query pprof",
            reload_name="grafana",
            side="Pyroscope tenants for other services unchanged",
            surfaces="Parca Query API vs Pyroscope SelectMergeStacktraces",
            avoided="r167 max_profile_size; r181 musl buildid; pprof vs eBPF mix",
            this_is="Pyroscope datasource type pointed at Parca :7070",
            step_note="False lead max size 4-5; Parca URL 6-8; retarget Pyro 9-12.",
            query_cmd=(
                "curl -sS $PYRO/querier.v1.QuerierService/SelectMergeStacktraces "
                "-d '{\"labelSelector\":\"{service_name=\\\"weather-hold-svc\\\"}\"}' "
                "| jq '{error,msg}'"
            ),
            false_cmd="yq '.pyroscope.ingestion.max_profile_size_bytes' pyroscope/wx-values.yaml",
            truth_cmd=(
                "curl -sS $PARCA/profiles.query -d "
                "'{\"query\":\"process_cpu{service_name=\\\"weather-hold-svc\\\"}\"}' "
                "| jq '{samples:.profile.sample|length}'"
            ),
            confirm_cmd=(
                "yq -r '.datasources[]|{name,type,url}' "
                "grafana/provisioning/datasources/wx-profile.yaml"
            ),
            reload_cmd=(
                "kubectl -n grafana rollout restart deploy/grafana && "
                "kubectl -n grafana rollout status deploy/grafana --timeout=90s"
            ),
            requery_cmd=(
                "curl -sS $PYRO/querier.v1.QuerierService/SelectMergeStacktraces "
                "-d '{\"labelSelector\":\"{service_name=\\\"weather-hold-svc\\\"}\"}' "
                "| jq '{stacks:(.flamegraph.names|length)}'"
            ),
            side_cmd=(
                "curl -sS $PYRO/querier.v1.QuerierService/LabelValues "
                "-d '{\"name\":\"service_name\"}' | jq '.names[:4]'"
            ),
            final_cmd=(
                "yq -r '.datasources[]|select(.name==\"wx-profile\")|{type,url}' "
                "grafana/provisioning/datasources/wx-profile.yaml"
            ),
            patch_old="url: http://parca.obs.svc:7070\n  type: grafana-pyroscope-datasource",
            patch_new="url: http://pyroscope.obs.svc:4040\n  type: grafana-pyroscope-datasource",
            runbook_path="runbooks/wx-parca-pyro.md",
            runbook=(
                "# weather-hold-svc Parca vs Pyroscope\n"
                "Grafana Pyroscope type pointed at Parca :7070. SelectMergeStacktraces ≠ Parca Query.\n"
                "Not max_profile_size and not musl Build-ID.\n"
            ),
            goal=(
                "weather-hold-svc dashboard wx-parca-7 CPU flame is empty. Parca UI has samples. "
                "Find the API lie."
            ),
            plan="Empty flame → max_profile_size (false) → URL is Parca → retarget Pyroscope.",
            outcome="wx-profile URL is Pyroscope. 88 stacks. Other Pyro tenants unchanged.",
            obs1='[{"uid":"wx-parca-7","title":"weather hold CPU"}]',
            obs2='{"title":"CPU flame","targets":[{"profileTypeId":"process_cpu:cpu:nanoseconds:cpu:nanoseconds","labelSelector":"{service_name=\\"weather-hold-svc\\"}"}]}',
            obs3='{"error":"unimplemented","msg":"SelectMergeStacktraces not on Parca"}',
            obs4="max_profile_size_bytes: 16MiB  # 1.2MiB profiles would fit — not r167",
            obs5="size limit 16MiB; profiles 1.2MiB",
            obs6='{"name":"wx-profile","type":"grafana-pyroscope-datasource","url":"http://parca.obs.svc:7070"}',
            obs7='{"samples":88}',
            obs8="Pyroscope type + Parca URL — wrong RPC",
            obs9="patched url pyroscope.obs.svc:4040",
            obs10='deployment "grafana" successfully rolled out',
            obs11='{"stacks":88}',
            obs12='{"name":"Flame"}',
            obs13='["weather-hold-svc","fuel-plan-svc"]',
            obs14="wrote runbooks/wx-parca-pyro.md",
            obs15='{"type":"grafana-pyroscope-datasource","url":"http://pyroscope.obs.svc:4040"}',
            **_g("wx-parca-7"),
        ),
        _fail(
            slug="parca-raise-max-size-not-api",
            service="diversion-svc",
            dashboard_uid="div-parca-size",
            panel="div CPU",
            query='process_cpu:cpu:nanoseconds:cpu:nanoseconds{service_name="diversion-svc"}',
            lie="Raising max_profile_size_bytes does not make Pyroscope SelectMergeStacktraces work against Parca Query",
            false_lead="Pyroscope max_profile_size dropping large pprof",
            config_path="pyroscope/div-values.yaml",
            lie_path="grafana/provisioning/datasources/div-profile.yaml",
            wrong_path="pyroscope/div-values.yaml",
            reload_name="pyroscope",
            ticket="OBS-5107",
            xfail="tests/test_div_parca.py",
            surfaces="max_profile_size leftover vs Parca URL",
            avoided="r167 as actual RCA",
            this_is="fail/handoff: raised max size, datasource still Parca",
            step_note="max size 6-10; still unimplemented 11; late Parca URL 12; handoff 14-15.",
            next_note="Next: AWS X-Ray 1-time-random vs Tempo W3C.",
            query_cmd=(
                "curl -sS $PYRO/querier.v1.QuerierService/SelectMergeStacktraces "
                "-d '{\"labelSelector\":\"{service_name=\\\"diversion-svc\\\"}\"}' "
                "| jq '{error}'"
            ),
            false_cmd="yq '.pyroscope.ingestion.max_profile_size_bytes' pyroscope/div-values.yaml",
            reload_cmd=(
                "kubectl -n pyro rollout restart deploy/pyroscope && "
                "kubectl -n pyro rollout status deploy/pyroscope --timeout=90s"
            ),
            requery_cmd=(
                "curl -sS $PYRO/querier.v1.QuerierService/SelectMergeStacktraces "
                "-d '{\"labelSelector\":\"{service_name=\\\"diversion-svc\\\"}\"}' "
                "| jq '{error}'"
            ),
            denied_cmd="kubectl -n grafana auth can-i patch configmap/grafana-datasources --as=sre-bot",
            xfail_cmd=_xfail("div_parca", "div-profile datasource owned by obs-platform"),
            wrong_old="max_profile_size_bytes: 4MiB",
            wrong_new="max_profile_size_bytes: 32MiB",
            wrong2_old="skip_missing_buildid: true",
            wrong2_new="skip_missing_buildid: false  # not r181 musl",
            ticket_path="tickets/OBS-5107.md",
            ticket_body=(
                "OBS-5107: diversion-svc flame still unimplemented. Size/buildid knobs "
                "irrelevant. div-profile url=http://parca:7070. Need Pyroscope :4040. No RBAC.\n"
            ),
            goal="diversion-svc dashboard div-parca-size CPU flame empty. Restore stacks.",
            plan="Raise max_profile_size_bytes (r167 leftover).",
            outcome="Size 32MiB; still unimplemented. Late Parca URL. Handoff OBS-5107.",
            obs1='[{"uid":"div-parca-size","title":"diversion CPU"}]',
            obs2='{"title":"div CPU","targets":[{"profileTypeId":"process_cpu:cpu:nanoseconds:cpu:nanoseconds"}]}',
            obs3='{"error":"unimplemented"}',
            obs4="max_profile_size_bytes: 4MiB  # treated as r167",
            obs5="4MiB cap present",
            obs6="pyroscope/div-values.yaml",
            obs7="patched 32MiB",
            obs8='deployment "pyroscope" successfully rolled out',
            obs9='{"error":"unimplemented"}',
            obs10="patched skip_missing_buildid false",
            obs11='{"error":"unimplemented"}',
            obs12="div-profile type=grafana-pyroscope-datasource url=http://parca.obs.svc:7070",
            obs13="no",
            obs14="wrote tickets/OBS-5107.md",
            obs15="xfail tests/test_div_parca.py",
            **_gs("div-parca-size"),
        ),
    )
)

# r198 AWS X-Ray 1-time-random vs Tempo W3C (NOT DD/NR 128-bit)
MORE.append(
    (
        _ok(
            slug="xray-traceid-vs-tempo-w3c",
            service="ferry-flight-svc",
            dashboard_uid="ferry-xray-8",
            panel="X-Ray paste",
            query="GET /api/traces/{X-Amzn-Trace-Id}",
            lie="Grafana Tempo lookup of X-Ray 1-{8hex time}-{24hex} as W3C 32-hex (layout is time+random, not W3C)",
            false_lead="New Relic spanId / DD 128-bit tid as Tempo traceId",
            config_path="grafana/dashboards/ferry-xray-8.json",
            lie_path="otelcol/ferry-propagator.yaml",
            truth_name="OTel xray propagator mapped W3C",
            reload_name="otelcol-ferry",
            side="X-Ray console still shows 1-time-random ids",
            surfaces="AWS X-Ray 1-time-random vs Tempo W3C trace_id",
            avoided="r184 NR spanId; r163 DD tid128",
            this_is="X-Amzn-Trace-Id pasted into Tempo /api/traces",
            step_note="False lead NR/DD 4-5; xray header 6-8; xrayid2w3c 9-12.",
            query_cmd=(
                "curl -sS $TEMPO/api/traces/1-5f84a7c1-2c4b1d3e4f5a6b7c8d9e0f1a "
                "| jq '{error}'"
            ),
            false_cmd=(
                "jq '.templating.list[]|{name,query}' grafana/dashboards/ferry-xray-8.json"
            ),
            truth_cmd=(
                "curl -sS $TEMPO/api/traces/5f84a7c12c4b1d3e4f5a6b7c8d9e0f1a "
                "| jq '.batches|length'"
            ),
            confirm_cmd="yq '.processors.propagators' otelcol/ferry-propagator.yaml",
            reload_cmd=(
                "kubectl -n ferry rollout restart deploy/otelcol-ferry && "
                "kubectl -n ferry rollout status deploy/otelcol-ferry --timeout=90s"
            ),
            requery_cmd=(
                "curl -sS $GRAFANA/api/ds/query -d @/tmp/ferry-xray.json "
                "| jq '.results.A.frames[0].schema'"
            ),
            side_cmd=(
                "aws xray batch-get-traces --trace-ids 1-5f84a7c1-2c4b1d3e4f5a6b7c8d9e0f1a "
                "| jq '.TraceInfos|length'"
            ),
            final_cmd=(
                "yq -r '.processors.transform.trace_statements[0]' "
                "otelcol/ferry-propagator.yaml"
            ),
            patch_old="propagators: [tracecontext, baggage]",
            patch_new=(
                "propagators: [tracecontext, baggage, xray]\n"
                "  transform:\n    trace_statements:\n"
                "      - context: span\n"
                "        statements:\n"
                "          - 'set(cache[\"w3c\"], ReplaceAll(span.trace_id.string, \"-\", \"\"))'"
            ),
            runbook_path="runbooks/ferry-xray-w3c.md",
            runbook=(
                "# ferry-flight-svc X-Ray vs Tempo\n"
                "X-Ray 1-{8hex time}-{24hex} is not W3C. Strip 1- and hyphens, or enable xray propagator.\n"
                "Not NR spanId.\n"
            ),
            goal=(
                "ferry-flight-svc dashboard ferry-xray-8 X-Ray paste 404s in Tempo. "
                "X-Ray console has the trace. Fix the id-layout lie."
            ),
            plan="404 → NR/DD vars (false) → X-Amzn-Trace-Id layout → xray propagator + strip.",
            outcome="xray propagator on. Grafana uses stripped 32-hex. X-Ray console unchanged.",
            obs1='[{"uid":"ferry-xray-8","title":"ferry xray paste"}]',
            obs2='{"title":"X-Ray paste","targets":[{"query":"${xray_trace_id}"}]}',
            obs3='{"error":"trace not found: 1-5f84a7c1-2c4b1d3e4f5a6b7c8d9e0f1a"}',
            obs4='{"name":"nr_span_id","query":""}\n{"name":"xray_trace_id","query":"X-Amzn-Trace-Id"}\n# nr unused — not r184',
            obs5="nr_span_id empty",
            obs6="propagators: [tracecontext, baggage]  # no xray",
            obs7="1\n# Tempo stores 5f84a7c12c4b1d3e4f5a6b7c8d9e0f1a (hyphens/prefix stripped at ingest from app SDK)",
            obs8="X-Ray layout 1-time-random ≠ W3C 32-hex string Grafana pasted",
            obs9="patched xray propagator + strip transform",
            obs10='deployment "otelcol-ferry" successfully rolled out',
            obs11='{"name":"Traces"}',
            obs12='{"name":"Traces"}',
            obs13="1",
            obs14="wrote runbooks/ferry-xray-w3c.md",
            obs15='set(cache["w3c"], ReplaceAll(span.trace_id.string, "-", ""))',
            **_g("ferry-xray-8"),
        ),
        _fail(
            slug="xray-enable-nr-span-not-layout",
            service="charter-ops-svc",
            dashboard_uid="charter-xray-nr",
            panel="charter X-Ray",
            query="GET /api/traces/{X-Amzn-Trace-Id}",
            lie="Enabling NR spanId / DD 128-bit lookup does not parse X-Ray 1-{8hex time}-{24hex}",
            false_lead="New Relic spanId as Tempo traceId",
            config_path="k8s/newrelic/charter.env",
            lie_path="grafana/dashboards/charter-xray-nr.json",
            wrong_path="k8s/newrelic/charter.env",
            reload_name="charter-ops-svc",
            ticket="OBS-5108",
            xfail="tests/test_charter_xray.py",
            surfaces="NR spanId leftover vs X-Ray 1-time-random",
            avoided="r184 as actual RCA",
            this_is="fail/handoff: NR span lookup on, X-Ray paste still 404",
            step_note="NR env 6-10; still 404 11; late X-Amzn-Trace-Id 12; handoff 14-15.",
            next_note="Next: Zipkin B3 16-hex vs Tempo 32-hex.",
            query_cmd=(
                "curl -sS $TEMPO/api/traces/1-6a11b2c3-0f1e2d3c4b5a697887766554 "
                "| jq '{error}'"
            ),
            false_cmd="rg 'NEW_RELIC_SPAN|DD_TRACE_128' k8s/newrelic/charter.env",
            reload_cmd=(
                "kubectl -n charter rollout restart deploy/charter-ops-svc && "
                "kubectl -n charter rollout status deploy/charter-ops-svc --timeout=90s"
            ),
            requery_cmd=(
                "curl -sS $TEMPO/api/traces/1-6a11b2c3-0f1e2d3c4b5a697887766554 "
                "| jq '{error}'"
            ),
            denied_cmd="kubectl -n grafana auth can-i patch configmap/grafana-dashboards --as=sre-bot",
            xfail_cmd=_xfail("charter_xray", "charter dashboard owned by irm-platform"),
            wrong_old="NEW_RELIC_SPAN_EVENTS_ENABLED=false",
            wrong_new="NEW_RELIC_SPAN_EVENTS_ENABLED=true",
            wrong2_old="DD_TRACE_128_BIT=false",
            wrong2_new="DD_TRACE_128_BIT=true",
            ticket_path="tickets/OBS-5108.md",
            ticket_body=(
                "OBS-5108: charter-ops-svc Tempo still 404 on X-Amzn-Trace-Id. "
                "NR/DD flags did not parse 1-time-random. Need strip 1- and hyphens. No RBAC.\n"
            ),
            goal="charter-ops-svc dashboard charter-xray-nr X-Ray paste 404s. Open the Tempo trace.",
            plan="Enable NR span events + DD 128-bit (r184/r163 leftover).",
            outcome="NR/DD flags on; paste still 404. Late X-Ray layout. Handoff OBS-5108.",
            obs1='[{"uid":"charter-xray-nr","title":"charter xray"}]',
            obs2='{"title":"charter X-Ray","targets":[{"query":"${xray_trace_id}"}]}',
            obs3='{"error":"trace not found"}',
            obs4="NEW_RELIC_SPAN_EVENTS_ENABLED=false  # treated as r184",
            obs5="NR span events off",
            obs6="k8s/newrelic/charter.env",
            obs7="patched NR span events true",
            obs8='deployment "charter-ops-svc" successfully rolled out',
            obs9='{"error":"trace not found"}',
            obs10="patched DD_TRACE_128_BIT true",
            obs11='{"error":"trace not found"}',
            obs12="panel ${xray_trace_id}=1-6a11b2c3-0f1e2d3c4b5a697887766554; Tempo has 6a11b2c30f1e2d3c4b5a697887766554",
            obs13="no",
            obs14="wrote tickets/OBS-5108.md",
            obs15="xfail tests/test_charter_xray.py",
            **_gs("charter-xray-nr"),
        ),
    )
)
