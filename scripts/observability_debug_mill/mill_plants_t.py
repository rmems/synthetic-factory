"""Observability plants r333-r356. Do not clone r109-r332.

BAN r163 tid128, r172 inferred db, r190 DD UST,
r244 loki-querier-max-concurrent / loki-qconc-rebuild-blooms.
Not a r292 Tempo max-bytes-per-tag-values clone.
"""

from mill_plants_q import _badfull, _okfull

MORE = []


def _add(ok, bad, dest=None):
    (MORE if dest is None else dest).append((_okfull(**ok), _badfull(**bad)))


def _roll(kind, name):
    ns = {"loki": "loki", "tempo": "tempo", "mimir": "mimir", "prom": "prom", "otel": "otel", "grafana": "grafana"}[kind]
    if kind in ("loki", "tempo", "mimir") and "ingester" in name:
        return (
            f"kubectl -n {ns} rollout restart sts/{name} && "
            f"kubectl -n {ns} rollout status sts/{name} --timeout=120s"
        )
    return (
        f"kubectl -n {ns} rollout restart deploy/{name} && "
        f"kubectl -n {ns} rollout status deploy/{name} --timeout=90s"
    )


def _ok_obs(dash, title, panel_json, empty, healthy, lie_yaml, truth, note, patched, rolled, filled, gok, side, wrote, final):
    return [f'[{{"uid":"{dash}","title":"{title}"}}]', panel_json, empty, healthy, "false lead healthy", lie_yaml, truth, note, patched, rolled, filled, gok, side, wrote, final]


def _bad_obs(dash, title, panel_json, empty, treated, cfg, patched, rolled, still, patched2, still2, late, denied, ticket, xfail):
    return [f'[{{"uid":"{dash}","title":"{title}"}}]', panel_json, empty, treated, "treated as leftover", cfg, patched, rolled, still, patched2, still2, late, denied, ticket, xfail]


# Compact leftover specs: 24 unique (service+dashboard+lie) pairs occupying r333-r356.
SPECS = [
    dict(
        n=333,
        kind="loki",
        ok_slug="loki-frontend-max-retries-zero",
        bad_slug="loki-retries-raise-fwpar-not-retries",
        ok_svc="pax-call-btn-svc",
        bad_svc="attendant-lt-svc",
        ok_dash="pcbtn-retries-1",
        bad_dash="alt-retries-fwpar",
        panel="pax call logs",
        query='{job="pax-call-btn-svc"} |= "btn_stuck"',
        lie="query_range max_retries_per_request 0 drops a single querier blip so Grafana is empty while a retry=5 frontend still fills",
        bad_lie="Raising frontend_worker parallelism does not recover a LogQL cancelled by max_retries_per_request 0",
        false_lead="frontend_worker parallelism 0",
        config_path="loki/pcbtn-fwpar.yaml",
        lie_path="loki/pcbtn-retries.yaml",
        bad_config="loki/alt-fwpar.yaml",
        bad_lie_path="loki/alt-retries.yaml",
        truth_name="max_retries_per_request vs querier ready",
        reload="query-frontend",
        surfaces="Loki max_retries_per_request 0 vs Grafana empty after blip",
        avoided="r277 frontend_worker; r331 frontend outstanding; r317 query_timeout",
        this_is="retries 0 drops a one-shot querier error",
        ticket="OBS-5401",
        patch_old="max_retries_per_request: 0",
        patch_new="max_retries_per_request: 5",
        wrong_old="parallelism: 0",
        wrong_new="parallelism: 10",
        wrong2_old="query_timeout: 500ms",
        wrong2_new="query_timeout: 2m",
        query_cmd="curl -sS -G $LOKI/loki/api/v1/query_range --data-urlencode 'query={job=\"pax-call-btn-svc\"} |= \"btn_stuck\"' | jq '{status,error,n:(.data.result|length)}'",
        bad_query="curl -sS -G $LOKI/loki/api/v1/query_range --data-urlencode 'query={job=\"attendant-lt-svc\"} |= \"lamp_fail\"' | jq '{status,error,n:(.data.result|length)}'",
        false_cmd="yq '.frontend_worker.parallelism' loki/pcbtn-fwpar.yaml",
        bad_false="yq '.frontend_worker.parallelism' loki/alt-fwpar.yaml",
        truth_cmd="curl -sS $LOKI/ready",
        confirm_cmd="yq '.query_range.max_retries_per_request' loki/pcbtn-retries.yaml",
        requery="curl -sS -G $LOKI/loki/api/v1/query_range --data-urlencode 'query={job=\"pax-call-btn-svc\"} |= \"btn_stuck\"' | jq '.data.result|length'",
        bad_requery="curl -sS -G $LOKI/loki/api/v1/query_range --data-urlencode 'query={job=\"attendant-lt-svc\"} |= \"lamp_fail\"' | jq '{status,n:(.data.result|length)}'",
        side_cmd="curl -sS -G $LOKI/loki/api/v1/query_range --data-urlencode 'query={job=\"ssr-meal-svc\"} |= \"error\"' | jq '.data.result|length'",
        final_cmd="yq -r '.query_range.max_retries_per_request' loki/pcbtn-retries.yaml",
        denied="kubectl -n loki auth can-i patch configmap/alt-retries --as=sre-bot",
        outcome="retries 5. 6 streams. ssr-meal-svc unchanged.",
        bad_outcome="fwpar 10; still empty. Late retries 0. Handoff OBS-5401.",
        ok_obs=_ok_obs("pcbtn-retries-1", "pax call logs", '{"title":"pax call logs","targets":[{"expr":"{job=\\"pax-call-btn-svc\\"} |= \\"btn_stuck\\""}]}', '{"status":"error","n":0}', "parallelism: 10  # not r277", "max_retries_per_request: 0", "ready", "querier ready; retries 0 dropped the blip", "patched 5", 'deployment "query-frontend" successfully rolled out', "6", '{"name":"Logs"}', "1", "wrote runbooks/pcbtn-retries.md", "5"),
        bad_obs=_bad_obs("alt-retries-fwpar", "attendant logs", '{"title":"attendant logs","targets":[{"expr":"{job=\\"attendant-lt-svc\\"} |= \\"lamp_fail\\""}]}', '{"status":"error","n":0}', "parallelism: 0", "loki/alt-fwpar.yaml", "patched 10", 'deployment "query-frontend" successfully rolled out', '{"status":"error","n":0}', "patched query_timeout 2m", '{"status":"error","n":0}', "loki/alt-retries.yaml max_retries_per_request 0", "no", "wrote tickets/OBS-5401.md", "xfail tests/test_loki_retries_raise_fwpar_not_retries.py"),
    ),
    dict(
        n=334,
        kind="tempo",
        ok_slug="tempo-query-recent-duration-zero",
        bad_slug="tempo-qrecent-enable-search-not-duration",
        ok_svc="boarding-music-svc",
        bad_svc="lav-smoke-svc",
        ok_dash="bmus-qrecent-2",
        bad_dash="lsmoke-qrecent-search",
        panel="boarding traces",
        query='{resource.service.name="boarding-music-svc"}',
        lie="querier query_recent_duration 0s skips live ingester traces so Grafana Search is empty while GET by-id still works",
        bad_lie="Flipping search.enabled true does not query live traces when query_recent_duration is 0s",
        false_lead="search.enabled false",
        config_path="tempo/bmus-searchoff.yaml",
        lie_path="tempo/bmus-qrecent.yaml",
        bad_config="tempo/lsmoke-searchoff.yaml",
        bad_lie_path="tempo/lsmoke-qrecent.yaml",
        truth_name="query_recent_duration vs by-id",
        reload="querier",
        surfaces="Tempo query_recent_duration 0s vs Grafana empty live traces",
        avoided="r247 search.enabled; r293 Loki query_ingesters_within; r292 tag-values",
        this_is="query_recent_duration 0s hides live traces",
        ticket="OBS-5402",
        patch_old="query_recent_duration: 0s",
        patch_new="query_recent_duration: 1h",
        wrong_old="enabled: false",
        wrong_new="enabled: true",
        wrong2_old="default_result_limit: 0",
        wrong2_new="default_result_limit: 20",
        query_cmd="curl -sS -G $TEMPO/api/search --data-urlencode 'q={resource.service.name=\"boarding-music-svc\"}' | jq '{n:(.traces|length),error}'",
        bad_query="curl -sS -G $TEMPO/api/search --data-urlencode 'q={resource.service.name=\"lav-smoke-svc\"}' | jq '{n:(.traces|length),error}'",
        false_cmd="yq '.query_frontend.search.enabled' tempo/bmus-searchoff.yaml",
        bad_false="yq '.query_frontend.search.enabled' tempo/lsmoke-searchoff.yaml",
        truth_cmd="curl -sS $TEMPO/api/traces/d34abcdef012345670123456789abcde | jq '.batches|length'",
        confirm_cmd="yq '.querier.query_recent_duration' tempo/bmus-qrecent.yaml",
        requery="curl -sS -G $TEMPO/api/search --data-urlencode 'q={resource.service.name=\"boarding-music-svc\"}' | jq '.traces|length'",
        bad_requery="curl -sS -G $TEMPO/api/search --data-urlencode 'q={resource.service.name=\"lav-smoke-svc\"}' | jq '{n:(.traces|length),error}'",
        side_cmd="curl -sS -G $TEMPO/api/search --data-urlencode 'q={resource.service.name=\"ssr-meal-svc\"}' | jq '.traces|length'",
        final_cmd="yq -r '.querier.query_recent_duration' tempo/bmus-qrecent.yaml",
        denied="kubectl -n tempo auth can-i patch configmap/lsmoke-qrecent --as=sre-bot",
        outcome="query_recent 1h. 10 traces. ssr-meal-svc unchanged.",
        bad_outcome="search on; still 0. Late query_recent 0s. Handoff OBS-5402.",
        ok_obs=_ok_obs("bmus-qrecent-2", "boarding traces", '{"title":"boarding traces","targets":[{"query":"{resource.service.name=\\"boarding-music-svc\\"}"}]}', '{"n":0,"error":null}', "enabled: true  # not r247", "query_recent_duration: 0s", "2", "by-id works; live search skipped", "patched 1h", 'deployment "querier" successfully rolled out', "10", '{"name":"Traces"}', "19", "wrote runbooks/bmus-qrecent.md", "1h"),
        bad_obs=_bad_obs("lsmoke-qrecent-search", "lav smoke traces", '{"title":"lav smoke traces","targets":[{"query":"{resource.service.name=\\"lav-smoke-svc\\"}"}]}', '{"n":0,"error":null}', "enabled: false", "tempo/lsmoke-searchoff.yaml", "patched enabled true", 'deployment "query-frontend" successfully rolled out', '{"n":0,"error":null}', "patched default_result_limit 20", '{"n":0,"error":null}', "tempo/lsmoke-qrecent.yaml query_recent_duration 0s; by-id 2", "no", "wrote tickets/OBS-5402.md", "xfail tests/test_tempo_qrecent_enable_search_not_duration.py"),
    ),
]


def _emit(spec):
    kind = spec["kind"]
    reload = spec["reload"]
    ok_dash = spec["ok_dash"]
    bad_dash = spec["bad_dash"]
    ticket = spec["ticket"]
    xfail = f"tests/test_{spec['bad_slug'].replace('-', '_')}.py"
    reload_cmd = _roll(kind, reload)
    if kind == "tempo" and spec["ok_slug"].startswith("tempo-query-recent"):
        bad_reload_cmd = _roll("tempo", "query-frontend")
    else:
        bad_reload_cmd = reload_cmd
    ok = dict(
        slug=spec["ok_slug"],
        service=spec["ok_svc"],
        dashboard_uid=ok_dash,
        panel=spec["panel"],
        query=spec["query"] if spec["ok_svc"] in spec["query"] else spec["query"],
        lie=spec["lie"],
        false_lead=spec["false_lead"],
        config_path=spec["config_path"],
        lie_path=spec["lie_path"],
        truth_name=spec["truth_name"],
        reload_name=reload,
        side="control tenant unchanged",
        surfaces=spec["surfaces"],
        avoided=spec["avoided"],
        this_is=spec["this_is"],
        step_note="False lead 4-5; lie 6-8; patch 9-12.",
        query_cmd=spec["query_cmd"],
        false_cmd=spec["false_cmd"],
        truth_cmd=spec["truth_cmd"],
        confirm_cmd=spec["confirm_cmd"],
        reload_cmd=reload_cmd,
        requery_cmd=spec["requery"],
        side_cmd=spec["side_cmd"],
        final_cmd=spec["final_cmd"],
        patch_old=spec["patch_old"],
        patch_new=spec["patch_new"],
        runbook_path=f"runbooks/{ok_dash}.md",
        runbook=f"# {spec['ok_svc']} {spec['ok_slug']}\n{spec['lie']}. Patch {spec['patch_new']}. Not {spec['false_lead']}.\n",
        goal=f"{spec['ok_svc']} dashboard {ok_dash} empty. Find the leftover lie.",
        plan=f"Empty → {spec['false_lead']} (false) → lie → patch.",
        outcome=spec["outcome"],
        obs=spec["ok_obs"],
    )
    bad_query = spec["query"].replace(spec["ok_svc"], spec["bad_svc"])
    bad = dict(
        slug=spec["bad_slug"],
        service=spec["bad_svc"],
        dashboard_uid=bad_dash,
        panel=spec["panel"],
        query=bad_query,
        lie=spec["bad_lie"],
        false_lead=spec["false_lead"],
        config_path=spec["bad_config"],
        lie_path=spec["bad_lie_path"],
        wrong_path=spec["bad_config"],
        reload_name=reload,
        ticket=ticket,
        xfail=xfail,
        surfaces=spec["surfaces"] + " leftover fail",
        avoided="earlier leftover as actual RCA",
        this_is="fail/handoff on leftover false lead",
        step_note="false lead 6-10; still empty 11; late lie 12; handoff 14-15.",
        next_note=f"Next leftover unique vs r109-r{spec['n']}. Not r292 tag-values.",
        query_cmd=spec["bad_query"],
        false_cmd=spec["bad_false"],
        reload_cmd=bad_reload_cmd,
        requery_cmd=spec["bad_requery"],
        denied_cmd=spec["denied"],
        wrong_old=spec["wrong_old"],
        wrong_new=spec["wrong_new"],
        wrong2_old=spec["wrong2_old"],
        wrong2_new=spec["wrong2_new"],
        ticket_body=f"{ticket}: leftover false lead. Actual {spec['lie']}. Need {spec['patch_new']}.\n",
        goal=f"{spec['bad_svc']} dashboard {bad_dash} empty. Restore panel.",
        plan=f"Patch {spec['false_lead']} leftover.",
        outcome=spec["bad_outcome"],
        obs=spec["bad_obs"],
    )
    _add(ok, bad)


for spec in SPECS:
    _emit(spec)


# Remaining r335-r356 as explicit leftover unique plants (compact).
_add(
    dict(
        slug="mimir-query-sharding-total-shards-one",
        service="blue-water-svc",
        dashboard_uid="bwater-shards-3",
        panel="blue water C",
        query='avg(blue_water_celsius{job="blue-water-svc"})',
        lie="frontend query_sharding_total_shards 1 plus sharding on a 30d range 504s Grafana so the Stat is empty while unsharded 5m works",
        false_lead="split_instant_queries_by_interval / max_query_lookback",
        config_path="mimir/bwater-split.yaml",
        lie_path="mimir/bwater-shards.yaml",
        truth_name="query_sharding_total_shards vs 5m",
        reload_name="mimir-query-frontend",
        side="5m unsharded still works",
        surfaces="Mimir query_sharding_total_shards 1 vs Grafana 30d 504",
        avoided="r270 split_instant; r210 lookback; r309 Loki split_queries_by_interval",
        this_is="total_shards 1 504s 30d",
        step_note="False lead split/lookback 4-5; shards 1 6-8; 16 9-12.",
        query_cmd="curl -sS -G $MIMIR/prometheus/api/v1/query --data-urlencode 'query=avg_over_time(blue_water_celsius{job=\"blue-water-svc\"}[30d])'",
        false_cmd="yq '.limits.split_instant_queries_by_interval, .limits.max_query_lookback' mimir/bwater-split.yaml",
        truth_cmd="curl -sS -G $MIMIR/prometheus/api/v1/query --data-urlencode 'query=avg(blue_water_celsius{job=\"blue-water-svc\"})' | jq '.data.result'",
        confirm_cmd="yq '.frontend.query_sharding_total_shards' mimir/bwater-shards.yaml",
        reload_cmd=_roll("mimir", "query-frontend"),
        requery_cmd="curl -sS -G $MIMIR/prometheus/api/v1/query --data-urlencode 'query=avg_over_time(blue_water_celsius{job=\"blue-water-svc\"}[30d])'",
        side_cmd="curl -sS -G $MIMIR/prometheus/api/v1/query --data-urlencode 'query=avg(blue_water_celsius{job=\"ssr-meal-svc\"})' | jq '.data.result|length'",
        final_cmd="yq -r '.frontend.query_sharding_total_shards' mimir/bwater-shards.yaml",
        patch_old="query_sharding_total_shards: 1",
        patch_new="query_sharding_total_shards: 16",
        runbook_path="runbooks/bwater-shards.md",
        runbook="# blue-water-svc query_sharding_total_shards\n1 504s 30d. Raise 16. Not split_instant.\n",
        goal="blue-water-svc dashboard bwater-shards-3 blue water C 30d 504. 5m works. Find the shards lie.",
        plan="504 30d → split/lookback (false) → shards 1 → 16.",
        outcome="shards 16. 30d=12. ssr-meal-svc unchanged.",
        obs=_ok_obs("bwater-shards-3", "blue water", '{"title":"blue water C","targets":[{"expr":"avg_over_time(blue_water_celsius{job=\\"blue-water-svc\\"}[30d])"}]}', '{"status":"error","error":"deadline exceeded"}', "split_instant_queries_by_interval: 0\nmax_query_lookback: 30d  # not r270/r210", "query_sharding_total_shards: 1", '[{"value":[1710000000,"12"]}]', "5m=12; 30d unsharded 504", "patched 16", 'deployment "query-frontend" successfully rolled out', '{"status":"success","data":{"result":[{"value":[1710000600,"12"]}]}}', '{"name":"Number"}', "1", "wrote runbooks/bwater-shards.md", "16"),
    ),
    dict(
        slug="mimir-shards-disable-split-not-total",
        service="vac-blower-svc",
        dashboard_uid="vblow-shards-split",
        panel="vac blower C",
        query='avg_over_time(vac_blower_celsius{job="vac-blower-svc"}[30d])',
        lie="Disabling split_instant_queries_by_interval does not finish a 30d range when query_sharding_total_shards is 1",
        false_lead="split_instant_queries_by_interval 1s",
        config_path="mimir/vblow-split.yaml",
        lie_path="mimir/vblow-shards.yaml",
        wrong_path="mimir/vblow-split.yaml",
        reload_name="mimir-query-frontend",
        ticket="OBS-5403",
        xfail="tests/test_vblow_shards.py",
        surfaces="split leftover vs query_sharding_total_shards 1",
        avoided="r270 as actual RCA",
        this_is="fail/handoff: split off, shards still 1",
        step_note="split 6-10; still 504 11; late shards 12; handoff 14-15.",
        next_note="Next: OTel transform error_mode silent.",
        query_cmd="curl -sS -G $MIMIR/prometheus/api/v1/query --data-urlencode 'query=avg_over_time(vac_blower_celsius{job=\"vac-blower-svc\"}[30d])'",
        false_cmd="yq '.limits.split_instant_queries_by_interval' mimir/vblow-split.yaml",
        reload_cmd=_roll("mimir", "query-frontend"),
        requery_cmd="curl -sS -G $MIMIR/prometheus/api/v1/query --data-urlencode 'query=avg_over_time(vac_blower_celsius{job=\"vac-blower-svc\"}[30d])'",
        denied_cmd="kubectl -n mimir auth can-i patch configmap/vblow-shards --as=sre-bot",
        wrong_old="split_instant_queries_by_interval: 1s",
        wrong_new="split_instant_queries_by_interval: 0",
        wrong2_old="max_query_lookback: 7d",
        wrong2_new="max_query_lookback: 30d",
        ticket_body="OBS-5403: vac-blower-svc 30d still 504. split leftover. query_sharding_total_shards 1. Need 16. No frontend RBAC.\n",
        goal="vac-blower-svc dashboard vblow-shards-split vac blower C 30d 504. Restore range.",
        plan="Disable split_instant (r270 leftover).",
        outcome="split off; still 504. Late shards 1. Handoff OBS-5403.",
        obs=_bad_obs("vblow-shards-split", "vac blower", '{"title":"vac blower C","targets":[{"expr":"avg_over_time(vac_blower_celsius{job=\\"vac-blower-svc\\"}[30d])"}]}', '{"status":"error","error":"deadline exceeded"}', "split_instant_queries_by_interval: 1s", "mimir/vblow-split.yaml", "patched 0", 'deployment "query-frontend" successfully rolled out', '{"status":"error","error":"deadline exceeded"}', "patched lookback 30d", '{"status":"error","error":"deadline exceeded"}', "mimir/vblow-shards.yaml query_sharding_total_shards 1; 5m=11", "no", "wrote tickets/OBS-5403.md", "xfail tests/test_vblow_shards.py"),
    ),
)


def _leftover_pair(
    *,
    n,
    kind,
    ok_slug,
    bad_slug,
    ok_svc,
    bad_svc,
    ok_dash,
    bad_dash,
    panel,
    metric,
    needle,
    lie,
    bad_lie,
    false_lead,
    avoided,
    this_is,
    ticket,
    knob,
    old,
    new,
    wrong_knob,
    wrong_old,
    wrong_new,
    wrong2_old,
    wrong2_new,
    reload,
    config_path,
    lie_path,
    bad_config,
    bad_lie_path,
    extra_avoided="",
    dest=None,
):
    """Emit one unique leftover success+fail pair for Loki/Tempo/Mimir/Prom/OTel/Grafana."""
    if kind == "loki":
        q = f'{{job="{ok_svc}"}} |= "{needle}"'
        bq = f'{{job="{bad_svc}"}} |= "{needle}"'
        qcmd = (
            "curl -sS -G $LOKI/loki/api/v1/query_range --data-urlencode "
            f"'query={{job=\"{ok_svc}\"}} |= \"{needle}\"' | jq '{{status,n:(.data.result|length)}}'"
        )
        bqcmd = (
            "curl -sS -G $LOKI/loki/api/v1/query_range --data-urlencode "
            f"'query={{job=\"{bad_svc}\"}} |= \"{needle}\"' | jq '{{status,n:(.data.result|length)}}'"
        )
        requery = (
            "curl -sS -G $LOKI/loki/api/v1/query_range --data-urlencode "
            f"'query={{job=\"{ok_svc}\"}} |= \"{needle}\"' | jq '.data.result|length'"
        )
        brequery = bqcmd
        side = (
            "curl -sS -G $LOKI/loki/api/v1/query_range --data-urlencode "
            "'query={job=\"ssr-meal-svc\"} |= \"error\"' | jq '.data.result|length'"
        )
        truth = "curl -sS $LOKI/metrics | rg loki_ | head"
        panel_json = f'{{"title":"{panel}","targets":[{{"expr":"{q}"}}]}}'
        empty = '{"status":"success","n":0}'
        filled = "7"
        gok = '{"name":"Logs"}'
        ns = "loki"
    elif kind == "tempo":
        q = f'{{resource.service.name="{ok_svc}"}}'
        bq = f'{{resource.service.name="{bad_svc}"}}'
        qcmd = (
            "curl -sS -G $TEMPO/api/search --data-urlencode "
            f"'q={{resource.service.name=\"{ok_svc}\"}}' | jq '{{n:(.traces|length),error}}'"
        )
        bqcmd = (
            "curl -sS -G $TEMPO/api/search --data-urlencode "
            f"'q={{resource.service.name=\"{bad_svc}\"}}' | jq '{{n:(.traces|length),error}}'"
        )
        requery = (
            "curl -sS -G $TEMPO/api/search --data-urlencode "
            f"'q={{resource.service.name=\"{ok_svc}\"}}' | jq '.traces|length'"
        )
        brequery = bqcmd
        side = (
            "curl -sS -G $TEMPO/api/search --data-urlencode "
            "'q={resource.service.name=\"ssr-meal-svc\"}' | jq '.traces|length'"
        )
        truth = "curl -sS $TEMPO/api/traces/e45abcdef012345670123456789abcde | jq '.batches|length'"
        panel_json = f'{{"title":"{panel}","targets":[{{"query":"{q}"}}]}}'
        empty = '{"n":0,"error":null}'
        filled = "9"
        gok = '{"name":"Traces"}'
        ns = "tempo"
    elif kind == "mimir":
        q = f'avg({metric}{{job="{ok_svc}"}})'
        bq = f'avg({metric}{{job="{bad_svc}"}})'
        qcmd = (
            "curl -sS -G $MIMIR/prometheus/api/v1/query --data-urlencode "
            f"'query=avg({metric}{{job=\"{ok_svc}\"}})'"
        )
        bqcmd = (
            "curl -sS -G $MIMIR/prometheus/api/v1/query --data-urlencode "
            f"'query=avg({metric}{{job=\"{bad_svc}\"}})'"
        )
        requery = qcmd
        brequery = bqcmd
        side = (
            "curl -sS -G $MIMIR/prometheus/api/v1/query --data-urlencode "
            f"'query=avg({metric}{{job=\"ssr-meal-svc\"}})' | jq '.data.result|length'"
        )
        truth = f"curl -sS $MIMIR/metrics | rg {metric}|discarded | head"
        panel_json = f'{{"title":"{panel}","targets":[{{"expr":"{q}"}}]}}'
        empty = '{"status":"success","data":{"result":[]}}'
        filled = '{"status":"success","data":{"result":[{"value":[1710000600,"4"]}]}}'
        gok = '{"name":"Timeseries"}'
        ns = "mimir"
    elif kind == "prom":
        q = f'avg({metric}{{job="{ok_svc}"}})'
        bq = f'avg({metric}{{job="{bad_svc}"}})'
        qcmd = (
            "curl -sS -G $MIMIR/prometheus/api/v1/query --data-urlencode "
            f"'query=avg({metric}{{job=\"{ok_svc}\"}})'"
        )
        bqcmd = (
            "curl -sS -G $MIMIR/prometheus/api/v1/query --data-urlencode "
            f"'query=avg({metric}{{job=\"{bad_svc}\"}})'"
        )
        requery = qcmd
        brequery = bqcmd
        side = (
            "curl -sS -G $MIMIR/prometheus/api/v1/query --data-urlencode "
            f"'query=avg({metric}{{job=\"ssr-meal-svc\"}})' | jq '.data.result|length'"
        )
        truth = f"curl -sS http://{ok_svc}:8080/metrics | rg {metric} | head"
        panel_json = f'{{"title":"{panel}","targets":[{{"expr":"{q}"}}]}}'
        empty = '{"status":"success","data":{"result":[]}}'
        filled = '{"status":"success","data":{"result":[{"value":[1710000600,"8"]}]}}'
        gok = '{"name":"Timeseries"}'
        ns = "prom"
    elif kind == "otel":
        q = f'{{resource.service.name="{ok_svc}"}}'
        bq = f'{{resource.service.name="{bad_svc}"}}'
        qcmd = (
            "curl -sS -G $TEMPO/api/search --data-urlencode "
            f"'q={{resource.service.name=\"{ok_svc}\"}}' | jq '.traces|length'"
        )
        bqcmd = (
            "curl -sS -G $TEMPO/api/search --data-urlencode "
            f"'q={{resource.service.name=\"{bad_svc}\"}}' | jq '.traces|length'"
        )
        requery = qcmd
        brequery = bqcmd
        side = (
            "curl -sS -G $TEMPO/api/search --data-urlencode "
            "'q={resource.service.name=\"ssr-meal-svc\"}' | jq '.traces|length'"
        )
        truth = f"kubectl -n otel logs deploy/{reload} --tail=20 | rg {ok_svc} | head"
        panel_json = f'{{"title":"{panel}","targets":[{{"query":"{q}"}}]}}'
        empty = "0"
        filled = "8"
        gok = '{"name":"Traces"}'
        ns = "otel"
    else:
        q = f'{{job="{ok_svc}"}} |= "{needle}"'
        bq = f'{{job="{bad_svc}"}} |= "{needle}"'
        qcmd = f"curl -sS $GRAFANA/api/ds/query -d @/tmp/{ok_dash}.json | jq '{{status:.results.A.status,error:.results.A.error}}'"
        bqcmd = f"curl -sS $GRAFANA/api/ds/query -d @/tmp/{bad_dash}.json | jq '{{status:.results.A.status,error:.results.A.error}}'"
        requery = qcmd
        brequery = bqcmd
        side = (
            "curl -sS -G $LOKI/loki/api/v1/query_range --data-urlencode "
            "'query={job=\"ssr-meal-svc\"} |= \"error\"' | jq '.data.result|length'"
        )
        truth = (
            "curl -sS -G $LOKI/loki/api/v1/query_range --data-urlencode "
            f"'query={{job=\"{ok_svc}\"}} |= \"{needle}\"' | jq '.data.result|length'"
        )
        panel_json = f'{{"title":"{panel}","targets":[{{"expr":"{q}"}}]}}'
        empty = '{"status":"error","error":"blocked"}'
        filled = '{"name":"Logs"}'
        gok = '{"name":"Logs"}'
        ns = "grafana"

    xfail = f"tests/test_{bad_slug.replace('-', '_')}.py"
    _add(
        dict(
            slug=ok_slug,
            service=ok_svc,
            dashboard_uid=ok_dash,
            panel=panel,
            query=q,
            lie=lie,
            false_lead=false_lead,
            config_path=config_path,
            lie_path=lie_path,
            truth_name=f"{knob} vs truth",
            reload_name=reload,
            side="control tenant unchanged",
            surfaces=f"{kind} {knob} leftover vs Grafana empty",
            avoided=avoided + extra_avoided,
            this_is=this_is,
            step_note="False lead 4-5; lie 6-8; patch 9-12.",
            query_cmd=qcmd,
            false_cmd=f"yq '{wrong_knob}' {config_path}",
            truth_cmd=truth,
            confirm_cmd=f"yq '{knob}' {lie_path}",
            reload_cmd=_roll(kind if kind != "grafana" else "grafana", reload),
            requery_cmd=requery,
            side_cmd=side,
            final_cmd=f"yq -r '{knob}' {lie_path}",
            patch_old=old,
            patch_new=new,
            runbook_path=f"runbooks/{ok_dash}.md",
            runbook=f"# {ok_svc} {knob}\n{lie}. Patch to {new}. Not {false_lead}.\n",
            goal=f"{ok_svc} dashboard {ok_dash} {panel} empty. Find the {knob} lie.",
            plan=f"Empty → {false_lead} (false) → {knob} → patch.",
            outcome=f"{knob} patched. panel filled. ssr-meal-svc unchanged.",
            obs=_ok_obs(
                ok_dash,
                panel,
                panel_json,
                empty,
                f"{wrong_knob} healthy  # leftover",
                old,
                "truth has data",
                f"{this_is}",
                f"patched {new}",
                f'deployment "{reload}" successfully rolled out'
                if "ingester" not in reload
                else f'statefulset "{reload}" successfully rolled out',
                filled,
                gok,
                "1",
                f"wrote runbooks/{ok_dash}.md",
                new.split()[-1] if ":" in new else new,
            ),
        ),
        dict(
            slug=bad_slug,
            service=bad_svc,
            dashboard_uid=bad_dash,
            panel=panel,
            query=bq,
            lie=bad_lie,
            false_lead=false_lead,
            config_path=bad_config,
            lie_path=bad_lie_path,
            wrong_path=bad_config,
            reload_name=reload,
            ticket=ticket,
            xfail=xfail,
            surfaces=f"{false_lead} leftover vs {knob}",
            avoided="earlier leftover as actual RCA",
            this_is=f"fail/handoff: false lead patched, {knob} still {old}",
            step_note="false lead 6-10; still empty 11; late lie 12; handoff 14-15.",
            next_note=f"Next leftover unique vs r109-r{n}. Not r292 tag-values.",
            query_cmd=bqcmd,
            false_cmd=f"yq '{wrong_knob}' {bad_config}",
            reload_cmd=_roll(kind if kind != "grafana" else "grafana", reload),
            requery_cmd=brequery,
            denied_cmd=f"kubectl -n {ns} auth can-i patch configmap/{bad_dash} --as=sre-bot",
            wrong_old=wrong_old,
            wrong_new=wrong_new,
            wrong2_old=wrong2_old,
            wrong2_new=wrong2_new,
            ticket_body=f"{ticket}: {bad_svc} still empty. {false_lead} leftover. {knob} {old}. Need {new}.\n",
            goal=f"{bad_svc} dashboard {bad_dash} {panel} empty. Restore panel.",
            plan=f"Patch {false_lead} leftover.",
            outcome=f"false lead patched; still empty. Late {knob}. Handoff {ticket}.",
            obs=_bad_obs(
                bad_dash,
                panel,
                panel_json.replace(ok_svc, bad_svc).replace(ok_dash, bad_dash),
                empty,
                wrong_old,
                bad_config,
                f"patched {wrong_new}",
                f'deployment "{reload}" successfully rolled out'
                if "ingester" not in reload
                else f'statefulset "{reload}" successfully rolled out',
                empty,
                f"patched {wrong2_new}",
                empty,
                f"{bad_lie_path} {old}; truth has data",
                "no",
                f"wrote tickets/{ticket}.md",
                f"xfail {xfail}",
            ),
        ),
        dest=dest,
    )


ROWS = [
    ("336", "otel", "otel-transform-error-mode-silent", "otel-tesilent-drop-filter-not-silent",
     "fill-drain-svc", "overflow-sns-svc", "fdrain-tesilent-4", "ovsns-tesilent-filter",
     "fill drain traces", "", "drain_fail",
     "transform processor error_mode silent plus a bad OTTL set(attributes[\"http.route\"], nil) blanks span.http.route so Grafana route search is empty while service search still works",
     "Dropping filter processor does not restore span.http.route when transform error_mode silent still blanks it",
     "filter error_mode ignore",
     "r285 filter error_mode; r320 span from_attributes; r296 redaction",
     "transform silent OTTL blanks http.route",
     "OBS-5404", ".processors.transform.error_mode",
     "error_mode: silent", "error_mode: propagate",
     ".processors.filter.error_mode", "error_mode: ignore", "error_mode: propagate",
     "sampling_percentage: 0", "sampling_percentage: 100",
     "otelcol-fdrain", "otelcol/fdrain-filter.yaml", "otelcol/fdrain-tesilent.yaml",
     "otelcol/ovsns-filter.yaml", "otelcol/ovsns-tesilent.yaml"),
    ("337", "prom", "prom-scrape-protocols-proto-only", "prom-proto-enable-classic-not-protocols",
     "tank-heater-svc", "service-pnl-svc", "theat-sproto-5", "spnl-sproto-classic",
     "tank heater C", "tank_heater_celsius", "",
     "scrape_protocols [PrometheusProto] against a text /metrics so Grafana is empty while curl --raw shows tank_heater_celsius 42",
     "Enabling always_scrape_classic_histograms does not ingest text /metrics while scrape_protocols is PrometheusProto only",
     "always_scrape_classic_histograms false",
     "r187 native vs classic; r138 protobuf on text; r291 enable_compression",
     "PrometheusProto-only scrape vs identity text /metrics",
     "OBS-5405", ".scrape_configs[].scrape_protocols",
     "scrape_protocols: [PrometheusProto]", "scrape_protocols: [OpenMetricsText1.0.0, PrometheusText0.0.4]",
     ".scrape_configs[].always_scrape_classic_histograms", "always_scrape_classic_histograms: false", "always_scrape_classic_histograms: true",
     "enable_compression: true", "enable_compression: false",
     "prom-scrape", "prom/theat-classic.yaml", "prom/theat-sproto.yaml",
     "prom/spnl-classic.yaml", "prom/spnl-sproto.yaml"),
    ("338", "loki", "loki-allow-structured-metadata-false", "loki-smallow-rebuild-blooms-not-flag",
     "windshield-wiper-svc", "taxi-turn-lt-svc", "wwiper-smallow-6", "tturn-smallow-bloom",
     "wiper logs", "", "park_fail",
     "limits_config allow_structured_metadata false plus Grafana matcher | structured_metadata so the panel is empty while label-only LogQL still returns 8",
     "Rebuilding blooms does not restore structured_metadata matchers when allow_structured_metadata is false",
     "bloom skip-on-error",
     "r225 structured metadata vs label; r173 bloom skip; r244 qconc blooms",
     "allow_structured_metadata false drops SM matchers",
     "OBS-5406", ".limits_config.allow_structured_metadata",
     "allow_structured_metadata: false", "allow_structured_metadata: true",
     ".bloom_build.enabled", "enabled: false", "enabled: true",
     "skip_on_error: true", "skip_on_error: false",
     "querier", "loki/wwiper-bloom.yaml", "loki/wwiper-smallow.yaml",
     "loki/tturn-bloom.yaml", "loki/tturn-smallow.yaml"),
    ("339", "tempo", "tempo-sg-histogram-buckets-empty", "tempo-sghist-enable-mg-not-buckets",
     "logo-lt-svc", "wing-insp-lt-svc", "logo-sghist-7", "winsp-sghist-mg",
     "logo service graph", "", "",
     "metrics_generator service_graphs histogram_buckets [] so Grafana service-graph heatmap is empty while spanmetrics _bucket still exists",
     "Enabling MG local_blocks flush does not create service-graph _bucket series when histogram_buckets is empty",
     "MG local_blocks flush_to_storage false",
     "r263 local_blocks flush; r287 exponential hist; r164 MG filter",
     "empty service_graphs histogram_buckets drops _bucket",
     "OBS-5407", ".metrics_generator.processor.service_graphs.histogram_buckets",
     "histogram_buckets: []", "histogram_buckets: [0.01, 0.05, 0.1, 0.5, 1]",
     ".metrics_generator.storage.flush_to_storage", "flush_to_storage: false", "flush_to_storage: true",
     "type: exponential", "type: explicit",
     "metrics-generator", "tempo/logo-localblk.yaml", "tempo/logo-sghist.yaml",
     "tempo/winsp-localblk.yaml", "tempo/winsp-sghist.yaml"),
    ("340", "grafana", "grafana-alerting-disabled-true", "grafana-aldis-patch-irm-not-flag",
     "fadec-eicas-svc", "oil-press-svc", "fadec-aldis-8", "oilp-aldis-irm",
     "FADEC pages", "", "eicas_warn",
     "grafana.ini alerting enabled false so Grafana 1m rules never fire and the pages Stat is empty while raw 5xx is 0.2",
     "Patching IRM group_by does not fire rules when alerting.enabled is false",
     "IRM group_by omitted service",
     "r159 IRM group_by; r324 min_interval; r188 Incident vs IRM",
     "alerting.enabled false blocks all Grafana rules",
     "OBS-5408", ".alerting.enabled",
     "enabled = false", "enabled = true",
     ".escalation.group_by", "group_by: [alertname]", "group_by: [alertname, service]",
     "source: grafana", "source: alertmanager",
     "grafana", "helm/grafana-irm/fadec-esc.yaml", "grafana/fadec.ini",
     "helm/grafana-irm/oilp-esc.yaml", "grafana/oilp.ini"),
    ("341", "otel", "otel-logdedup-interval-60s", "otel-logdedup-raise-batch-not-interval",
     "fuel-qty-probe-svc", "jettison-valve-svc", "fqty-logdedup-1", "jetv-logdedup-batch",
     "fuel qty logs", "", "probe_open",
     "logdedup processor interval 60s collapses probe_open bursts so Grafana count_over_time[15s] is empty while 5m still has 4",
     "Raising batch timeout does not restore 15s log counts when logdedup interval is 60s",
     "batch timeout 1ms",
     "r237 batch timeout; r245 interval processor; r280 logstransform",
     "logdedup 60s hides 15s bursts",
     "OBS-5409", ".processors.logdedup.interval",
     "interval: 60s", "interval: 1s",
     ".processors.batch.timeout", "timeout: 1ms", "timeout: 200ms",
     "send_batch_size: 8192", "send_batch_size: 256",
     "otelcol-fqty", "otelcol/fqty-batch.yaml", "otelcol/fqty-logdedup.yaml",
     "otelcol/jetv-batch.yaml", "otelcol/jetv-logdedup.yaml"),
    ("342", "loki", "loki-reject-old-samples-max-age-1m", "loki-rejage-enable-unord-not-age",
     "elec-dcbus-svc", "idg-temp-svc", "dcbus-rejage-2", "idgt-rejage-unord",
     "DC bus logs", "", "bus_tie",
     "limits_config reject_old_samples true plus reject_old_samples_max_age 1m drops delayed pax-phone lines so Grafana is empty while discarded older_than_max_age climbs",
     "Enabling unordered_writes does not ingest samples older than reject_old_samples_max_age 1m",
     "unordered_writes false",
     "r302 unordered_writes; r235 max_chunk_age; r289 ingestion_rate_strategy",
     "reject_old_samples_max_age 1m drops delayed lines",
     "OBS-5410", ".limits_config.reject_old_samples_max_age",
     "reject_old_samples_max_age: 1m", "reject_old_samples_max_age: 168h",
     ".ingester.unordered_writes", "unordered_writes: false", "unordered_writes: true",
     "max_chunk_age: 5m", "max_chunk_age: 2h",
     "loki-ingester", "loki/dcbus-unord.yaml", "loki/dcbus-rejage.yaml",
     "loki/idgt-unord.yaml", "loki/idgt-rejage.yaml"),
    ("343", "mimir", "mimir-ruler-max-rule-groups-one", "mimir-rgroups-zero-delay-not-groups",
     "yaw-damp-b-svc", "spoiler-load-svc", "ydampb-rgroups-3", "spload-rgroups-delay",
     "yaw damper B burn", "yaw_damp_b_error_burn:ratio5m", "",
     "ruler max_rule_groups_per_tenant 1 400s the second recording-rule group so Grafana Stat is empty while raw rate still spikes",
     "Zeroing evaluation_delay does not evaluate a second rule group blocked by max_rule_groups_per_tenant 1",
     "evaluation_delay 15m",
     "r288 evaluation_delay; r319 evaluation_interval; r99 group interval",
     "max_rule_groups_per_tenant 1 drops the extra group",
     "OBS-5411", ".limits.max_rule_groups_per_tenant",
     "max_rule_groups_per_tenant: 1", "max_rule_groups_per_tenant: 50",
     ".ruler.evaluation_delay", "evaluation_delay: 15m", "evaluation_delay: 0s",
     "evaluation_interval: 1h", "evaluation_interval: 15s",
     "ruler", "mimir/ydampb-delay.yaml", "mimir/ydampb-rgroups.yaml",
     "mimir/spload-delay.yaml", "mimir/spload-rgroups.yaml"),
    ("344", "tempo", "tempo-ingester-max-flush-retries-zero", "tempo-flushr-cut-duration-not-retries",
     "flap-pos-2-svc", "slat-auto-svc", "flap2-flushr-4", "slata-flushr-dur",
     "flap 2 traces", "", "",
     "ingester max_flush_retries 0 plus a one-shot object-store 500 so complete blocks never land and Grafana Search is empty while /status lists complete blocks",
     "Cutting max_block_duration does not flush complete blocks when max_flush_retries is 0",
     "max_block_duration 24h",
     "r308 max_block_duration; r328 flush_check_period; r236 complete_block_timeout",
     "max_flush_retries 0 abandons complete blocks",
     "OBS-5412", ".ingester.max_flush_retries",
     "max_flush_retries: 0", "max_flush_retries: 10",
     ".ingester.max_block_duration", "max_block_duration: 24h", "max_block_duration: 5m",
     "flush_check_period: 24h", "flush_check_period: 10s",
     "ingester", "tempo/flap2-blkdur.yaml", "tempo/flap2-flushr.yaml",
     "tempo/slata-blkdur.yaml", "tempo/slata-flushr.yaml"),
    ("345", "prom", "prom-keep-dropped-targets-false", "prom-kdrop-raise-tlim-not-keep",
     "pax-call-svc", "cabin-handset-svc", "pcall-kdrop-5", "chand-kdrop-tlim",
     "pax call C", "pax_call_count", "",
     "scrape keep_dropped_targets false plus a stale DNS drop so Grafana cannot see the dropped live pod and avg is empty while curl to the pod shows 3",
     "Raising target_limit does not surface a dropped live pod when keep_dropped_targets is false",
     "target_limit 1",
     "r305 target_limit; r233 scrape timeout; r177 alloy relabel",
     "keep_dropped_targets false hides the dropped live pod",
     "OBS-5413", ".scrape_configs[].keep_dropped_targets",
     "keep_dropped_targets: false", "keep_dropped_targets: true",
     ".scrape_configs[].target_limit", "target_limit: 1", "target_limit: 0",
     "scrape_timeout: 1s", "scrape_timeout: 10s",
     "prom-scrape", "prom/pcall-tlim.yaml", "prom/pcall-kdrop.yaml",
     "prom/chand-tlim.yaml", "prom/chand-kdrop.yaml"),
    ("346", "loki", "loki-ingester-sync-period-24h", "loki-syncp-raise-chunk-not-period",
     "service-intph-svc", "flight-intph-svc", "sintph-syncp-6", "fintph-syncp-chunk",
     "service interphone logs", "", "handset_open",
     "ingester sync_period 24h so flushed chunks never sync to the store and Grafana is empty while ingester memory_streams still show lines",
     "Raising max_chunk_age does not sync chunks while sync_period is 24h",
     "max_chunk_age 5m",
     "r235 max_chunk_age; r259 index_gateway; r293 query_ingesters_within",
     "sync_period 24h stalls store sync",
     "OBS-5414", ".ingester.sync_period",
     "sync_period: 24h", "sync_period: 15s",
     ".ingester.max_chunk_age", "max_chunk_age: 5m", "max_chunk_age: 2h",
     "query_ingesters_within: 1s", "query_ingesters_within: 3h",
     "loki-ingester", "loki/sintph-chunk.yaml", "loki/sintph-syncp.yaml",
     "loki/fintph-chunk.yaml", "loki/fintph-syncp.yaml"),
    ("347", "otel", "otel-batch-send-batch-max-size-one", "otel-bmax-raise-timeout-not-size",
     "call-reset-svc", "lav-water-svc", "creset-bmax-7", "lwater-bmax-timeout",
     "call reset traces", "", "",
     "batch processor send_batch_max_size 1 plus timeout 5s stalls traces so Grafana Search is empty while the debug exporter saw spans",
     "Raising batch timeout does not export traces while send_batch_max_size is 1",
     "batch timeout 1ms",
     "r237 batch timeout; r224 memory_limiter; r311 groupbytrace",
     "send_batch_max_size 1 stalls the batch",
     "OBS-5415", ".processors.batch.send_batch_max_size",
     "send_batch_max_size: 1", "send_batch_max_size: 8192",
     ".processors.batch.timeout", "timeout: 1ms", "timeout: 200ms",
     "limit_mib: 32", "limit_mib: 512",
     "otelcol-creset", "otelcol/creset-batch.yaml", "otelcol/creset-bmax.yaml",
     "otelcol/lwater-batch.yaml", "otelcol/lwater-bmax.yaml"),
    ("348", "mimir", "mimir-compactor-deletion-delay-zero", "mimir-deldelay-zero-ignore-not-delay",
     "rinse-valve-svc", "quantity-prb-svc", "rinse-deldelay-8", "qprb-deldelay-ignore",
     "rinse valve 24h", "rinse_valve_count", "",
     "compactor deletion_delay 0s plus a compaction cycle deletes the 24h blocks Grafana needs so the panel is empty while 30m still queries",
     "Clearing ignore_blocks_within does not restore blocks deleted by deletion_delay 0s",
     "ignore_blocks_within 10h",
     "r249 ignore_blocks_within; r312 blocks_retention_period; r210 lookback",
     "deletion_delay 0s deletes 24h blocks immediately",
     "OBS-5416", ".compactor.deletion_delay",
     "deletion_delay: 0s", "deletion_delay: 12h",
     ".limits.ignore_blocks_within", "ignore_blocks_within: 10h", "ignore_blocks_within: 0s",
     "blocks_retention_period: 2h", "blocks_retention_period: 31d",
     "compactor", "mimir/rinse-ignore.yaml", "mimir/rinse-deldelay.yaml",
     "mimir/qprb-ignore.yaml", "mimir/qprb-deldelay.yaml"),
    ("349", "tempo", "tempo-search-prefer-self-empty-zone", "tempo-prefself-enable-search-not-flag",
     "drain-valve-svc", "drain-mast-heat-svc", "dvalve-prefself-1", "dmheat-prefself-search",
     "drain valve traces", "", "",
     "querier search.prefer_self true plus this zone has no local blocks so Grafana Search is empty while a remote querier still finds traces",
     "Enabling search.enabled does not query remote blocks when prefer_self is true in an empty zone",
     "search.enabled false",
     "r247 search.enabled; r265 concurrent_jobs; r304 max_concurrent_queries",
     "prefer_self true in an empty zone blanks Search",
     "OBS-5417", ".querier.search.prefer_self",
     "prefer_self: true", "prefer_self: false",
     ".query_frontend.search.enabled", "enabled: false", "enabled: true",
     "concurrent_jobs: 0", "concurrent_jobs: 100",
     "querier", "tempo/dvalve-searchoff.yaml", "tempo/dvalve-prefself.yaml",
     "tempo/dmheat-searchoff.yaml", "tempo/dmheat-prefself.yaml"),
    ("350", "grafana", "grafana-live-allowed-origins-empty", "grafana-lvorig-raise-maxconn-not-origins",
     "baby-change-svc", "coat-closet-svc", "bchg-lvorig-2", "ccloset-lvorig-maxc",
     "baby change live logs", "", "table_fail",
     "grafana.ini live allowed_origins empty so the Live websocket is rejected and the tail panel is empty while query_range still has 12 lines",
     "Raising live.max_connections does not open Live when allowed_origins is empty",
     "live.max_connections 0",
     "r315 live.max_connections; r300 dataproxy.timeout; r216 public dashboard",
     "allowed_origins empty rejects Live ws",
     "OBS-5418", ".live.allowed_origins",
     "allowed_origins =", "allowed_origins = *",
     ".live.max_connections", "max_connections = 0", "max_connections = 100",
     "timeout = 1s", "timeout = 60s",
     "grafana", "grafana/bchg-live.ini", "grafana/bchg-lvorig.ini",
     "grafana/ccloset-live.ini", "grafana/ccloset-lvorig.ini"),
    ("351", "prom", "prom-relabel-hashmod-drop-job", "prom-hashmod-disable-honor-not-relabel",
     "pet-carrier-svc", "umnr-kit-svc", "pcarr-hashmod-3", "umnrk-hashmod-honor",
     "pet carrier count", "pet_carrier_count", "",
     "scrape relabel hashmod modulus 2 keep 0 drops the job so Grafana {job=} is empty while unlabeled leftover series exists",
     "Disabling honor_labels does not restore {job=} when hashmod relabel still drops the target",
     "honor_labels true",
     "r316 honor_labels; r177 alloy relabel; r297 label_limit",
     "hashmod keep 0 drops the scrape job",
     "OBS-5419", ".scrape_configs[].relabel_configs",
     "modulus: 2\n        regex: 0", "modulus: 2\n        regex: .*",
     ".scrape_configs[].honor_labels", "honor_labels: true", "honor_labels: false",
     "honor_timestamps: true", "honor_timestamps: false",
     "prom-scrape", "prom/pcarr-honor.yaml", "prom/pcarr-hashmod.yaml",
     "prom/umnrk-honor.yaml", "prom/umnrk-hashmod.yaml"),
    ("352", "loki", "loki-index-cache-validity-24h", "loki-icache-raise-freshness-not-validity",
     "wheelchair-cabin-svc", "extra-seat-svc", "wcab-icache-4", "xseat-icache-fresh",
     "wheelchair logs", "", "brake_fail",
     "storage_config index_queries_cache_config validity 24h serves yesterday's empty index so Grafana is empty while an uncached querier has 9 lines",
     "Lowering max_cache_freshness_per_query does not bypass a 24h index cache validity",
     "max_cache_freshness_per_query 24h",
     "r314 max_cache_freshness; r286 align_queries_with_step; r259 index_gateway",
     "index cache validity 24h serves stale empty",
     "OBS-5420", ".storage_config.index_queries_cache_config.validity",
     "validity: 24h", "validity: 1m",
     ".query_range.results_cache.max_cache_freshness_per_query", "max_cache_freshness_per_query: 24h", "max_cache_freshness_per_query: 5m",
     "align_queries_with_step: true", "align_queries_with_step: false",
     "query-frontend", "loki/wcab-cachef.yaml", "loki/wcab-icache.yaml",
     "loki/xseat-cachef.yaml", "loki/xseat-icache.yaml"),
    ("353", "otel", "otel-k8sleaderelector-not-running", "otel-k8slead-watch-events-not-lease",
     "crew-bunk-svc", "bunk-oxy-svc", "cbunk-k8slead-5", "boxy-k8slead-events",
     "crew bunk traces", "", "",
     "k8sleaderelector holderIdentity empty so k8sobjects/k8scluster receivers stay silent and Grafana k8s traces are empty while app OTLP still exists",
     "Watching k8sobjects events does not start receivers when k8sleaderelector has no lease holder",
     "k8sobjects events vs Grafana",
     "r267 k8sobjects; r276 k8sclusterreceiver; r243 resourcedetection",
     "empty leader lease silences k8s receivers",
     "OBS-5421", ".extensions.k8s_leader_elector",
     "lease_name: obs-cbunk", "lease_name: otelcol-cbunk",
     ".receivers.k8sobjects.objects[].mode", "mode: watch", "mode: pull",
     "node_conditions_to_report: []", "node_conditions_to_report: [Ready]",
     "otelcol-cbunk", "otelcol/cbunk-k8sobj.yaml", "otelcol/cbunk-k8slead.yaml",
     "otelcol/boxy-k8sobj.yaml", "otelcol/boxy-k8slead.yaml"),
    ("354", "mimir", "mimir-frontend-max-outstanding-zero", "mimir-fout-raise-shards-not-outstanding",
     "rest-curtain-svc", "galley-chime-svc", "rcurt-fout-6", "gchime-fout-shards",
     "rest curtain C", "rest_curtain_lux", "",
     "frontend max_outstanding_per_tenant 0 429s PromQL so Grafana is empty while querier /ready is ok",
     "Raising query_sharding_total_shards does not accept PromQL when frontend max_outstanding_per_tenant is 0",
     "query_sharding_total_shards 1",
     "r335 shards; r294 Tempo outstanding; r331 Loki outstanding",
     "Mimir frontend outstanding 0 429s PromQL",
     "OBS-5422", ".frontend.max_outstanding_per_tenant",
     "max_outstanding_per_tenant: 0", "max_outstanding_per_tenant: 2048",
     ".frontend.query_sharding_total_shards", "query_sharding_total_shards: 1", "query_sharding_total_shards: 16",
     "split_instant_queries_by_interval: 1s", "split_instant_queries_by_interval: 0",
     "query-frontend", "mimir/rcurt-shards.yaml", "mimir/rcurt-fout.yaml",
     "mimir/gchime-shards.yaml", "mimir/gchime-fout.yaml"),
    ("355", "tempo", "tempo-mg-collection-interval-24h", "tempo-mgint-enable-flush-not-interval",
     "ife-screen-svc", "seat-usb-c-svc", "ifes-mgint-7", "susb-mgint-flush",
     "IFE screen calls", "", "",
     "metrics_generator registry collection_interval 24h so Grafana spanmetrics rate[5m] is empty while traces still search",
     "Enabling local_blocks flush_to_storage does not emit spanmetrics while collection_interval is 24h",
     "MG local_blocks flush_to_storage false",
     "r263 local_blocks; r273 stale_duration; r287 exponential hist",
     "collection_interval 24h starves 5m rate",
     "OBS-5423", ".metrics_generator.registry.collection_interval",
     "collection_interval: 24h", "collection_interval: 15s",
     ".metrics_generator.storage.flush_to_storage", "flush_to_storage: false", "flush_to_storage: true",
     "stale_duration: 1s", "stale_duration: 15m",
     "metrics-generator", "tempo/ifes-localblk.yaml", "tempo/ifes-mgint.yaml",
     "tempo/susb-localblk.yaml", "tempo/susb-mgint.yaml"),
    ("356", "prom", "prom-tsdb-min-block-duration-24h", "prom-minblk-raise-ooo-not-duration",
     "pax-broadcast-svc", "evac-light-svc", "pbcast-minblk-8", "evac-minblk-ooo",
     "PA broadcast C", "pax_broadcast_count", "",
     "storage.tsdb.min_block_duration 24h so head never cuts a block and Grafana range on compacted blocks is empty while /metrics still shows 5",
     "Raising out_of_order_time_window does not cut TSDB blocks while min_block_duration is 24h",
     "out_of_order_time_window 0",
     "r332 ooo window; r223 WAL replay; r160 agent vs server",
     "min_block_duration 24h never cuts a compactable block",
     "OBS-5424", ".storage.tsdb.min_block_duration",
     "min_block_duration: 24h", "min_block_duration: 2h",
     ".storage.tsdb.out_of_order_time_window", "out_of_order_time_window: 0", "out_of_order_time_window: 10m",
     "honor_timestamps: true", "honor_timestamps: false",
     "prom-scrape", "prom/pbcast-ooo.yaml", "prom/pbcast-minblk.yaml",
     "prom/evac-ooo.yaml", "prom/evac-minblk.yaml"),
]

for row in ROWS:
    _leftover_pair(
        n=row[0],
        kind=row[1],
        ok_slug=row[2],
        bad_slug=row[3],
        ok_svc=row[4],
        bad_svc=row[5],
        ok_dash=row[6],
        bad_dash=row[7],
        panel=row[8],
        metric=row[9],
        needle=row[10],
        lie=row[11],
        bad_lie=row[12],
        false_lead=row[13],
        avoided=row[14],
        this_is=row[15],
        ticket=row[16],
        knob=row[17],
        old=row[18],
        new=row[19],
        wrong_knob=row[20],
        wrong_old=row[21],
        wrong_new=row[22],
        wrong2_old=row[23],
        wrong2_new=row[24],
        reload=row[25],
        config_path=row[26],
        lie_path=row[27],
        bad_config=row[28],
        bad_lie_path=row[29],
    )

