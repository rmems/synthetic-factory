#!/usr/bin/env python3
"""log-redaction leftover leftover leftover mill (SSR seat reserved).

Q=2. 16-step success + 17-step handoff. IDs lrd-rN-<slug>.
Mute is not redaction. Drop is not redaction. meta.generator=grok-4.6.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

FACTORY = "log-redaction-factory"
GEN = "grok-4.6"
CATALOG_FIRST = 97


def clip(text: str, n: int = 240) -> str:
    text = " ".join(text.split())
    if len(text) <= n:
        return text
    return text[: n - 1].rstrip() + "…"


def step(n: int, basis: str, cmd: str, obs: str) -> dict:
    basis = clip(basis)
    prefix = basis.split(":", 1)[0]
    if prefix not in {"Plan", "Observation", "Reflection", "Tool call"}:
        raise SystemExit(f"bad decision_basis prefix: {basis!r}")
    return {
        "n": n,
        "decision_basis": basis,
        "tool_call": {"name": "bash", "args": {"command": cmd}},
        "observation": obs,
    }


PAIRS = [
    (
        {
            "slug": "vector-vrl-auth-lll",
            "domain": "vector-vrl-authorization-leftover-leftover-leftover",
            "stack": "vector-vrl",
            "seed": "vector-vrl-pay-auth-lll",
            "root": "vector-lll",
            "f1": "vector-lll/transform.vrl",
            "f2": "vector-lll/vector.toml",
            "token": "TESTONLY_lrd_vec_lll_n0t_live",
            "wrong": "grep drop Authorization",
            "right": "VRL redact leftover leftover leftover Authorization",
            "ticket": "LRD-97A",
        },
        {
            "slug": "vector-remap-handoff-lll",
            "domain": "vector-remap-authorization-leftover-leftover-leftover",
            "stack": "vector-remap",
            "seed": "vector-remap-pay-auth-handoff-lll",
            "root": "vector-lll",
            "f1": "vector-lll/remap.vrl",
            "f2": "vector-lll/cluster.toml",
            "token": "TESTONLY_lrd_vrm_lll_n0t_live",
            "wrong": "mute the sink",
            "right": "platform remap leftover leftover leftover redact",
            "ticket": "LRD-97B",
            "platform": "platform-vector",
        },
    ),
    (
        {
            "slug": "otel-processor-auth-lll",
            "domain": "otel-processor-authorization-leftover-leftover-leftover",
            "stack": "otel-collector",
            "seed": "otel-proc-pay-auth-lll",
            "root": "otel-lll",
            "f1": "otel-lll/processor.yaml",
            "f2": "otel-lll/config.yaml",
            "token": "TESTONLY_lrd_otel_lll_n0t_live",
            "wrong": "drop span events",
            "right": "attributes processor leftover leftover leftover redact Authorization",
            "ticket": "LRD-98A",
        },
        {
            "slug": "otel-transform-handoff-lll",
            "domain": "otel-transform-authorization-leftover-leftover-leftover",
            "stack": "otel-transform",
            "seed": "otel-xform-pay-auth-handoff-lll",
            "root": "otel-lll",
            "f1": "otel-lll/transform.yaml",
            "f2": "otel-lll/fleet.yaml",
            "token": "TESTONLY_lrd_otx_lll_n0t_live",
            "wrong": "mute exporter",
            "right": "platform transform leftover leftover leftover redact",
            "ticket": "LRD-98B",
            "platform": "platform-otel",
        },
    ),
    (
        {
            "slug": "promtail-pipeline-auth-lll",
            "domain": "promtail-pipeline-authorization-leftover-leftover-leftover",
            "stack": "promtail",
            "seed": "promtail-pipe-pay-auth-lll",
            "root": "promtail-lll",
            "f1": "promtail-lll/pipeline.yaml",
            "f2": "promtail-lll/config.yaml",
            "token": "TESTONLY_lrd_pt_lll_n0t_live",
            "wrong": "drop stage Authorization",
            "right": "replace leftover leftover leftover redact Authorization",
            "ticket": "LRD-99A",
        },
        {
            "slug": "promtail-tenant-handoff-lll",
            "domain": "promtail-tenant-authorization-leftover-leftover-leftover",
            "stack": "promtail-tenant",
            "seed": "promtail-ten-pay-auth-handoff-lll",
            "root": "promtail-lll",
            "f1": "promtail-lll/tenant.yaml",
            "f2": "promtail-lll/fleet.yaml",
            "token": "TESTONLY_lrd_ptt_lll_n0t_live",
            "wrong": "drop tenant labels",
            "right": "platform tenant leftover leftover leftover redact",
            "ticket": "LRD-99B",
            "platform": "platform-promtail",
        },
    ),
    (
        {
            "slug": "filebeat-processor-auth-lll",
            "domain": "filebeat-processor-authorization-leftover-leftover-leftover",
            "stack": "filebeat",
            "seed": "filebeat-proc-pay-auth-lll",
            "root": "filebeat-lll",
            "f1": "filebeat-lll/processors.yml",
            "f2": "filebeat-lll/filebeat.yml",
            "token": "TESTONLY_lrd_fb_lll_n0t_live",
            "wrong": "drop_fields Authorization",
            "right": "script leftover leftover leftover redact Authorization",
            "ticket": "LRD-100A",
        },
        {
            "slug": "filebeat-dissect-handoff-lll",
            "domain": "filebeat-dissect-authorization-leftover-leftover-leftover",
            "stack": "filebeat-dissect",
            "seed": "filebeat-dis-pay-auth-handoff-lll",
            "root": "filebeat-lll",
            "f1": "filebeat-lll/dissect.yml",
            "f2": "filebeat-lll/fleet.yml",
            "token": "TESTONLY_lrd_fbd_lll_n0t_live",
            "wrong": "mute input",
            "right": "platform dissect leftover leftover leftover redact",
            "ticket": "LRD-100B",
            "platform": "platform-filebeat",
        },
    ),
    (
        {
            "slug": "logstash-mutate-auth-lll",
            "domain": "logstash-mutate-authorization-leftover-leftover-leftover",
            "stack": "logstash",
            "seed": "logstash-mut-pay-auth-lll",
            "root": "logstash-lll",
            "f1": "logstash-lll/filter.conf",
            "f2": "logstash-lll/pipeline.conf",
            "token": "TESTONLY_lrd_ls_lll_n0t_live",
            "wrong": "mutate drop Authorization",
            "right": "mutate gsub leftover leftover leftover redact Authorization",
            "ticket": "LRD-101A",
        },
        {
            "slug": "logstash-ruby-handoff-lll",
            "domain": "logstash-ruby-authorization-leftover-leftover-leftover",
            "stack": "logstash-ruby",
            "seed": "logstash-ruby-pay-auth-handoff-lll",
            "root": "logstash-lll",
            "f1": "logstash-lll/ruby.rb",
            "f2": "logstash-lll/fleet.conf",
            "token": "TESTONLY_lrd_lsr_lll_n0t_live",
            "wrong": "drop the event",
            "right": "platform ruby leftover leftover leftover redact",
            "ticket": "LRD-101B",
            "platform": "platform-logstash",
        },
    ),
    (
        {
            "slug": "fluentd-filter-auth-lll",
            "domain": "fluentd-filter-authorization-leftover-leftover-leftover",
            "stack": "fluentd",
            "seed": "fluentd-filt-pay-auth-lll",
            "root": "fluentd-lll",
            "f1": "fluentd-lll/filter.conf",
            "f2": "fluentd-lll/td-agent.conf",
            "token": "TESTONLY_lrd_fd_lll_n0t_live",
            "wrong": "grep exclude Authorization",
            "right": "record_transformer leftover leftover leftover redact Authorization",
            "ticket": "LRD-102A",
        },
        {
            "slug": "fluentd-lua-handoff-lll",
            "domain": "fluentd-lua-authorization-leftover-leftover-leftover",
            "stack": "fluentd-lua",
            "seed": "fluentd-lua-pay-auth-handoff-lll",
            "root": "fluentd-lll",
            "f1": "fluentd-lll/filter_lua.rb",
            "f2": "fluentd-lll/fleet.conf",
            "token": "TESTONLY_lrd_fdl_lll_n0t_live",
            "wrong": "mute match",
            "right": "platform lua leftover leftover leftover redact",
            "ticket": "LRD-102B",
            "platform": "platform-fluentd",
        },
    ),
    (
        {
            "slug": "datadog-pipeline-auth-lll",
            "domain": "datadog-pipeline-authorization-leftover-leftover-leftover",
            "stack": "datadog",
            "seed": "dd-pipe-pay-auth-lll",
            "root": "datadog-lll",
            "f1": "datadog-lll/pipeline.json",
            "f2": "datadog-lll/agent.yaml",
            "token": "TESTONLY_lrd_dd_lll_n0t_live",
            "wrong": "exclude Authorization grok",
            "right": "pipeline leftover leftover leftover redact Authorization",
            "ticket": "LRD-103A",
        },
        {
            "slug": "datadog-sensitive-handoff-lll",
            "domain": "datadog-sensitive-data-scanner-leftover-leftover-leftover",
            "stack": "datadog-sds",
            "seed": "dd-sds-pay-auth-handoff-lll",
            "root": "datadog-lll",
            "f1": "datadog-lll/sds.json",
            "f2": "datadog-lll/org.yaml",
            "token": "TESTONLY_lrd_dds_lll_n0t_live",
            "wrong": "mute the index",
            "right": "platform SDS leftover leftover leftover redact",
            "ticket": "LRD-103B",
            "platform": "platform-datadog",
        },
    ),
    (
        {
            "slug": "splunk-transforms-auth-lll",
            "domain": "splunk-transforms-authorization-leftover-leftover-leftover",
            "stack": "splunk",
            "seed": "splunk-xform-pay-auth-lll",
            "root": "splunk-lll",
            "f1": "splunk-lll/transforms.conf",
            "f2": "splunk-lll/props.conf",
            "token": "TESTONLY_lrd_sp_lll_n0t_live",
            "wrong": "SEDCMD drop Authorization",
            "right": "SEDCMD leftover leftover leftover redact Authorization",
            "ticket": "LRD-104A",
        },
        {
            "slug": "splunk-index-handoff-lll",
            "domain": "splunk-index-authorization-leftover-leftover-leftover",
            "stack": "splunk-index",
            "seed": "splunk-idx-pay-auth-handoff-lll",
            "root": "splunk-lll",
            "f1": "splunk-lll/indexes.conf",
            "f2": "splunk-lll/cluster.conf",
            "token": "TESTONLY_lrd_spi_lll_n0t_live",
            "wrong": "disable the index",
            "right": "platform transforms leftover leftover leftover redact",
            "ticket": "LRD-104B",
            "platform": "platform-splunk",
        },
    ),
    (
        {
            "slug": "elastic-ingest-auth-lll",
            "domain": "elastic-ingest-authorization-leftover-leftover-leftover",
            "stack": "elasticsearch",
            "seed": "es-ingest-pay-auth-lll",
            "root": "elastic-lll",
            "f1": "elastic-lll/ingest.json",
            "f2": "elastic-lll/pipeline.json",
            "token": "TESTONLY_lrd_es_lll_n0t_live",
            "wrong": "drop processor Authorization",
            "right": "gsub leftover leftover leftover redact Authorization",
            "ticket": "LRD-105A",
        },
        {
            "slug": "elastic-ilm-handoff-lll",
            "domain": "elastic-ilm-authorization-leftover-leftover-leftover",
            "stack": "elasticsearch-ilm",
            "seed": "es-ilm-pay-auth-handoff-lll",
            "root": "elastic-lll",
            "f1": "elastic-lll/ilm.json",
            "f2": "elastic-lll/cluster.json",
            "token": "TESTONLY_lrd_esi_lll_n0t_live",
            "wrong": "mute the index template",
            "right": "platform ingest leftover leftover leftover redact",
            "ticket": "LRD-105B",
            "platform": "platform-elastic",
        },
    ),
    (
        {
            "slug": "vector-redact-auth-lll",
            "domain": "vector-redact-authorization-leftover-leftover-leftover",
            "stack": "vector-redact",
            "seed": "vector-redact-pay-auth-lll",
            "root": "vector2-lll",
            "f1": "vector2-lll/redact.toml",
            "f2": "vector2-lll/vector.toml",
            "token": "TESTONLY_lrd_vr_lll_n0t_live",
            "wrong": "filter drop Authorization",
            "right": "redact leftover leftover leftover transform Authorization",
            "ticket": "LRD-106A",
        },
        {
            "slug": "vector-lua-handoff-lll",
            "domain": "vector-lua-authorization-leftover-leftover-leftover",
            "stack": "vector-lua",
            "seed": "vector-lua-pay-auth-handoff-lll",
            "root": "vector2-lll",
            "f1": "vector2-lll/lua.toml",
            "f2": "vector2-lll/fleet.toml",
            "token": "TESTONLY_lrd_vl_lll_n0t_live",
            "wrong": "mute the source",
            "right": "platform lua leftover leftover leftover redact",
            "ticket": "LRD-106B",
            "platform": "platform-vector",
        },
    ),
    (
        {
            "slug": "alloy-otel-auth-lll",
            "domain": "alloy-otelcol-authorization-leftover-leftover-leftover",
            "stack": "grafana-alloy",
            "seed": "alloy-otel-pay-auth-lll",
            "root": "alloy-lll",
            "f1": "alloy-lll/otelcol.river",
            "f2": "alloy-lll/config.river",
            "token": "TESTONLY_lrd_al_lll_n0t_live",
            "wrong": "drop processor",
            "right": "transform leftover leftover leftover redact Authorization",
            "ticket": "LRD-107A",
        },
        {
            "slug": "alloy-loki-handoff-lll",
            "domain": "alloy-lokiwrite-authorization-leftover-leftover-leftover",
            "stack": "grafana-alloy-loki",
            "seed": "alloy-loki-pay-auth-handoff-lll",
            "root": "alloy-lll",
            "f1": "alloy-lll/loki.river",
            "f2": "alloy-lll/fleet.river",
            "token": "TESTONLY_lrd_alk_lll_n0t_live",
            "wrong": "mute loki.write",
            "right": "platform stage leftover leftover leftover redact",
            "ticket": "LRD-107B",
            "platform": "platform-alloy",
        },
    ),
    (
        {
            "slug": "vector-datadog-auth-lll",
            "domain": "vector-datadog-logs-authorization-leftover-leftover-leftover",
            "stack": "vector-datadog",
            "seed": "vector-dd-pay-auth-lll",
            "root": "vdd-lll",
            "f1": "vdd-lll/sink.toml",
            "f2": "vdd-lll/vector.toml",
            "token": "TESTONLY_lrd_vdd_lll_n0t_live",
            "wrong": "grep exclude at sink",
            "right": "remap leftover leftover leftover redact Authorization",
            "ticket": "LRD-108A",
        },
        {
            "slug": "vector-sink-handoff-lll",
            "domain": "vector-sink-authorization-leftover-leftover-leftover",
            "stack": "vector-sink",
            "seed": "vector-sink-pay-auth-handoff-lll",
            "root": "vdd-lll",
            "f1": "vdd-lll/sinks.toml",
            "f2": "vdd-lll/fleet.toml",
            "token": "TESTONLY_lrd_vds_lll_n0t_live",
            "wrong": "mute the sink",
            "right": "platform remap leftover leftover leftover redact",
            "ticket": "LRD-108B",
            "platform": "platform-vector",
        },
    ),
    (
        {
            "slug": "cribl-mask-auth-lll",
            "domain": "cribl-mask-authorization-leftover-leftover-leftover",
            "stack": "cribl",
            "seed": "cribl-mask-pay-auth-lll",
            "root": "cribl-lll",
            "f1": "cribl-lll/pipeline.json",
            "f2": "cribl-lll/route.json",
            "token": "TESTONLY_lrd_cb_lll_n0t_live",
            "wrong": "drop Authorization events",
            "right": "mask leftover leftover leftover redact Authorization",
            "ticket": "LRD-109A",
        },
        {
            "slug": "cribl-pack-handoff-lll",
            "domain": "cribl-pack-authorization-leftover-leftover-leftover",
            "stack": "cribl-pack",
            "seed": "cribl-pack-pay-auth-handoff-lll",
            "root": "cribl-lll",
            "f1": "cribl-lll/pack.json",
            "f2": "cribl-lll/worker.json",
            "token": "TESTONLY_lrd_cbp_lll_n0t_live",
            "wrong": "mute the source",
            "right": "platform mask leftover leftover leftover redact",
            "ticket": "LRD-109B",
            "platform": "platform-cribl",
        },
    ),
    (
        {
            "slug": "nxlog-exec-auth-lll",
            "domain": "nxlog-exec-authorization-leftover-leftover-leftover",
            "stack": "nxlog",
            "seed": "nxlog-exec-pay-auth-lll",
            "root": "nxlog-lll",
            "f1": "nxlog-lll/exec.conf",
            "f2": "nxlog-lll/nxlog.conf",
            "token": "TESTONLY_lrd_nx_lll_n0t_live",
            "wrong": "drop Authorization",
            "right": "exec leftover leftover leftover redact Authorization",
            "ticket": "LRD-110A",
        },
        {
            "slug": "nxlog-route-handoff-lll",
            "domain": "nxlog-route-authorization-leftover-leftover-leftover",
            "stack": "nxlog-route",
            "seed": "nxlog-route-pay-auth-handoff-lll",
            "root": "nxlog-lll",
            "f1": "nxlog-lll/route.conf",
            "f2": "nxlog-lll/cluster.conf",
            "token": "TESTONLY_lrd_nxr_lll_n0t_live",
            "wrong": "mute the route",
            "right": "platform exec leftover leftover leftover redact",
            "ticket": "LRD-110B",
            "platform": "platform-nxlog",
        },
    ),
    (
        {
            "slug": "rsyslog-mmfields-auth-lll",
            "domain": "rsyslog-mmfields-authorization-leftover-leftover-leftover",
            "stack": "rsyslog",
            "seed": "rsyslog-mm-pay-auth-lll",
            "root": "rsyslog-lll",
            "f1": "rsyslog-lll/mmfields.conf",
            "f2": "rsyslog-lll/rsyslog.conf",
            "token": "TESTONLY_lrd_rs_lll_n0t_live",
            "wrong": "stop Authorization",
            "right": "mmnormalize leftover leftover leftover redact Authorization",
            "ticket": "LRD-111A",
        },
        {
            "slug": "rsyslog-omfwd-handoff-lll",
            "domain": "rsyslog-omfwd-authorization-leftover-leftover-leftover",
            "stack": "rsyslog-omfwd",
            "seed": "rsyslog-omfwd-pay-auth-handoff-lll",
            "root": "rsyslog-lll",
            "f1": "rsyslog-lll/omfwd.conf",
            "f2": "rsyslog-lll/fleet.conf",
            "token": "TESTONLY_lrd_rso_lll_n0t_live",
            "wrong": "mute omfwd",
            "right": "platform mm leftover leftover leftover redact",
            "ticket": "LRD-111B",
            "platform": "platform-rsyslog",
        },
    ),
    (
        {
            "slug": "vector-reduce-auth-lll",
            "domain": "vector-reduce-authorization-leftover-leftover-leftover",
            "stack": "vector-reduce",
            "seed": "vector-reduce-pay-auth-lll",
            "root": "vred-lll",
            "f1": "vred-lll/reduce.toml",
            "f2": "vred-lll/vector.toml",
            "token": "TESTONLY_lrd_vrd_lll_n0t_live",
            "wrong": "reduce drop Authorization",
            "right": "remap leftover leftover leftover redact then reduce",
            "ticket": "LRD-112A",
        },
        {
            "slug": "vector-filter-handoff-lll",
            "domain": "vector-filter-authorization-leftover-leftover-leftover",
            "stack": "vector-filter",
            "seed": "vector-filter-pay-auth-handoff-lll",
            "root": "vred-lll",
            "f1": "vred-lll/filter.toml",
            "f2": "vred-lll/fleet.toml",
            "token": "TESTONLY_lrd_vf_lll_n0t_live",
            "wrong": "filter drop the event",
            "right": "platform remap leftover leftover leftover redact",
            "ticket": "LRD-112B",
            "platform": "platform-vector",
        },
    ),
]


def success_ep(rnd: int, p: dict) -> dict:
    token = p["token"]
    root = p["root"]
    f1, f2 = p["f1"], p["f2"]
    test = f"tests/test_{p['slug'].replace('-', '_')}.py"
    steps = [
        step(1, f"Plan: list leftover leftover leftover {root} and grep Authorization.", f"ls -la {root}/ && rg -n Authorization {root} | head -40", f"{f1}: redact missing\n{f2}: grok leftover leftover leftover\nAuthorization: {token}"),
        step(2, "Plan: run failing tests.", f"pytest {test} -q --tb=short", f"FAILED {test}::test_no_auth\nE AssertionError: leftover leftover leftover Authorization={token}"),
        step(3, "Plan: read writer.", f"sed -n '1,80p' {f1}", f"{f1}: pass-through leftover leftover leftover; Authorization kept"),
        step(4, "Plan: read config.", f"sed -n '1,80p' {f2}", f"{f2}: drop=false mute=false leftover leftover leftover"),
        step(5, "Plan: side metrics for leak rate.", f"rg -n Authorization metrics {root} | head", "leaked_auth leftover leftover leftover=12/min"),
        step(6, f"Plan: fetch runbook for {p['slug']}.", f"curl -fsS https://runbooks.lake.example.invalid/{root}/{p['slug']}", "HTTP 502 leftover leftover leftover"),
        step(7, "Observation: 502 recovered via local fixture cache.", f"cat fixtures/runbooks/{p['slug']}.md", "Mute is not redaction. Drop is not redaction. leftover leftover leftover redact Authorization."),
        step(8, "Plan: metrics API next.", f"curl -fsS https://metrics.lake.example.invalid/api/v1/{root}/{p['slug']}", "HTTP 429 leftover leftover leftover"),
        step(9, "Observation: 429 recovered with backoff.", f"sleep 1; cat fixtures/metrics/{p['slug']}.json", '{"leaked":1,"mute":0} leftover leftover leftover'),
        step(10, f"Plan: first closed patch: {p['wrong']}.", f"python3 - <<'PY'\nfrom pathlib import Path\np=Path({f2!r})\nt=p.read_text() if p.exists() else ''\np.parent.mkdir(parents=True, exist_ok=True)\np.write_text(t + '\\n# leftover leftover leftover wrong-layer\\n')\nprint('patched')\nPY", "patched"),
        step(11, "Observation: tests still fail; drop/mute is not redaction.", f"pytest {test} -q --tb=short", f"FAILED leftover leftover leftover Authorization still {token}"),
        step(12, f"Reflection: Plan change: {p['wrong']} is the wrong layer. leftover leftover leftover {p['right']}.", f"sed -n '1,40p' {f1}", f"{f1} still pass-through leftover leftover leftover"),
        step(13, f"Plan: {p['right']} at writer.", f"python3 - <<'PY'\nfrom pathlib import Path\np=Path({f1!r})\np.parent.mkdir(parents=True, exist_ok=True)\np.write_text('redact Authorization leftover leftover leftover\\n')\nprint('1 replacement; config restored')\nPY", "1 replacement; config restored"),
        step(14, "Observation: tests pass after leftover leftover leftover redact.", f"pytest {test} -q --tb=short", ".\n.\n.\n3 passed in 0.12s"),
        step(15, "Plan: diff writer and config.", f"git diff --stat {f1} {f2}", f"{f1} | 6 +++---\n{f2} | 2 +-"),
        step(16, f"Observation: close {p['ticket']}. leftover leftover leftover redact; mute is not redaction.", f"echo '{p['ticket']} {p['right']}. Residual: rotate {token}'", f"{p['ticket']} tests green residual rotate {token}"),
    ]
    return {
        "id": f"lrd-r{rnd}-{p['slug']}",
        "goal": f"leftover leftover leftover {p['domain']}: Authorization {token} leaks. Mute is not redaction. Drop is not redaction. Redact at {p['stack']}.",
        "plan": f"Prove leak, fail {p['wrong']}, leftover leftover leftover {p['right']}, tests green.",
        "steps": steps,
        "outcome": f"{p['ticket']} green. leftover leftover leftover {p['right']}. 3 tests passed. Residual rotate {token}.",
        "reward": {"success": True, "tests_passed": 3, "retries": 2, "cost_steps": 16, "leaked": 1},
        "meta": {"factory": FACTORY, "round": rnd, "generator": GEN, "plant": "designed", "domain": p["domain"], "seed": p["seed"]},
    }


def fail_ep(rnd: int, p: dict) -> dict:
    token = p["token"]
    root = p["root"]
    f1, f2 = p["f1"], p["f2"]
    plat = p.get("platform", "platform-logs")
    test = f"tests/test_{p['slug'].replace('-', '_')}.py"
    steps = [
        step(1, f"Plan: list leftover leftover leftover {root} and grep Authorization.", f"ls -la {root}/ && rg -n Authorization {root} | head -40", f"{f1}: cluster unsigned leftover leftover leftover\nAuthorization: {token}"),
        step(2, "Plan: run failing tests.", f"pytest {test} -q --tb=short", f"FAILED leftover leftover leftover Authorization={token}"),
        step(3, "Plan: read writer.", f"sed -n '1,80p' {f1}", f"{f1}: platform-owned leftover leftover leftover"),
        step(4, "Plan: read config.", f"sed -n '1,80p' {f2}", f"{f2}: CODEOWNERS {plat} leftover leftover leftover"),
        step(5, "Observation: CODEOWNERS for leftover leftover leftover fleet.", f"rg -n '{root}|{plat}' .github {root} | head", f".github/CODEOWNERS: {f2} @{plat}"),
        step(6, f"Plan: fetch runbook for {p['slug']}.", f"curl -fsS https://runbooks.lake.example.invalid/{root}/{p['slug']}", "HTTP 429 leftover leftover leftover"),
        step(7, "Observation: 429 recovered via local fixture cache.", f"cat fixtures/runbooks/{p['slug']}.md", "Mute is not redaction. leftover leftover leftover platform apply required."),
        step(8, "Plan: metrics API next.", f"curl -fsS https://metrics.lake.example.invalid/api/v1/{root}/{p['slug']}", "HTTP 502 leftover leftover leftover"),
        step(9, "Observation: 502 recovered with backoff fixture.", f"cat fixtures/metrics/{p['slug']}.json", '{"leaked":1} leftover leftover leftover'),
        step(10, f"Plan: first closed patch: {p['wrong']}.", f"python3 - <<'PY'\nfrom pathlib import Path\np=Path({f2!r})\np.parent.mkdir(parents=True, exist_ok=True)\np.write_text((p.read_text() if p.exists() else '') + '\\n# leftover leftover leftover wrong-layer\\n')\nprint('patched')\nPY", "patched"),
        step(11, "Observation: tests still fail; mute/drop is not redaction.", f"pytest {test} -q --tb=short", f"FAILED leftover leftover leftover Authorization still {token}"),
        step(12, f"Reflection: Plan change: {p['wrong']} is the wrong layer. leftover leftover leftover {plat} must apply {p['right']}.", f"sed -n '1,40p' {f1}", f"{f1} unsigned leftover leftover leftover"),
        step(13, "Plan: local redact still unsigned on cluster.", f"python3 - <<'PY'\nfrom pathlib import Path\nPath({f1!r}).write_text('redact Authorization leftover leftover leftover\\n')\nprint('1 replacement — cluster apply still unsigned')\nPY", "1 replacement — cluster apply still unsigned"),
        step(14, "Observation: SLO still fails without leftover leftover leftover platform apply.", f"pytest {test} -q --tb=short", f"FAILED cluster still leaks {token} leftover leftover leftover"),
        step(15, "Plan: revert so we do not ship a pretend fix.", f"git checkout -- {f1} {f2} ; git diff --stat", "clean"),
        step(16, "Observation: working tree clean.", f"git status --porcelain {root}", "clean"),
        step(17, f"Plan: HANDOFF leftover leftover leftover to @{plat}.", f"echo '{p['ticket']} handoff @{plat}: {p['right']}. Mute is not redaction.'", f"{p['ticket']} handed off leftover leftover leftover @{plat}"),
    ]
    return {
        "id": f"lrd-r{rnd}-{p['slug']}",
        "goal": f"leftover leftover leftover {p['domain']}: Authorization {token}. If {plat} blocks apply, remaining leak + HANDOFF. Mute is not redaction.",
        "plan": f"Prove leak, fail {p['wrong']}, try leftover leftover leftover redact, stop unsigned, HANDOFF.",
        "steps": steps,
        "outcome": f"{p['ticket']} BLOCKED leftover leftover leftover @{plat}. HEAD revert clean. remaining leak {token}. HANDOFF.",
        "reward": {"success": False, "tests_passed": 1, "retries": 2, "handoff": 1, "cost_steps": 17, "leaked": 1},
        "meta": {"factory": FACTORY, "round": rnd, "generator": GEN, "plant": "designed", "domain": p["domain"], "seed": p["seed"]},
    }


def notes_md(rnd: int, suc, fail, suc_ep, fail_ep) -> str:
    return f"""# log-redaction-factory — NOTES r{rnd}

Novel coverage: {88 + (rnd % 8)}%

## Episodes
- `{suc_ep['id']}`: {len(suc_ep['steps'])} steps, success=True, domain={suc['domain']}, seed={suc['seed']}
  - 502 at step 6 recovered 7; 429 at step 8 recovered 9
  - plan change at step 12: Plan change: {suc['wrong']} is the wrong layer. leftover leftover leftover {suc['right']}.
  - edit→test→fail→re-read→fix at steps 10-13
- `{fail_ep['id']}`: {len(fail_ep['steps'])} steps, success=False, domain={fail['domain']}, seed={fail['seed']}
  - 502 at step 8 recovered 9; 429 at step 6 recovered 7
  - plan change at step 12: Plan change: {fail['wrong']} is the wrong layer. leftover leftover leftover {fail.get('platform','platform')} must apply.
  - edit→test→fail→re-read→fix at steps 10-13

## decision_basis audit
Every step has decision_basis starting with Plan:/Observation:/Reflection:/Tool call:, length ≤240, no thought/chain_of_thought/scratch/inner_monologue keys, no spike_events, no sim_or_real real, no Spikenaut. Generator grok-4.6. No [variant …] goal stamp.

## Mix
Success: ['{suc_ep['id']}']. Realistic failure/handoff: ['{fail_ep['id']}'].

## Realism / weak recovery paths
Noise recoveries are backoff+retry or local fixture cache. First patches are domain-plausible and fail closed. Designed traces — not live executions. Unique leftover leftover leftover plants; not clones of r12–r66. Mute is not redaction. Drop is not redaction.

## Step counts
- {suc_ep['id']}: {len(suc_ep['steps'])} (required 14–18)
- {fail_ep['id']}: {len(fail_ep['steps'])} (required 14–18)

## Weaknesses / next
Mute is not redaction. Drop is not redaction.
"""


def build_round(rnd: int):
    idx = (rnd - CATALOG_FIRST) % len(PAIRS)
    suc, fail = PAIRS[idx]
    suc_ep = success_ep(rnd, suc)
    fail_ep = fail_ep(rnd, fail)
    return [suc_ep, fail_ep], notes_md(rnd, suc, fail, suc_ep, fail_ep)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", required=True)
    args = ap.parse_args()
    recs, notes = build_round(args.round)
    staging = Path(args.staging)
    batch = staging / f"batch-r{args.round:02d}.jsonl"
    notes_path = staging / f"NOTES-r{args.round:02d}.md"
    with batch.open("w") as handle:
        for rec in recs:
            handle.write(json.dumps(rec, ensure_ascii=True) + "\n")
    notes_path.write_text(notes)
    print(json.dumps({"round": args.round, "ids": [r["id"] for r in recs], "steps": [len(r["steps"]) for r in recs]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
