#!/usr/bin/env python3
"""LRD mill r116+: new shippers/agents Cookie/Set-Cookie redact vs mute.

BAN r81 PatternLayout/Authorization clones, r97–r99 rollbar/honeycomb,
r100–r115 leftover3d (log4j2/pino/loki/filebeat/vector/fluentbit/...).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path("/home/raulmc/rmems/synthetic-factory")
spec = importlib.util.spec_from_file_location(
    "lrd67", ROOT / "experiments/lrd-mill-leftover3-r67.py"
)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
OK, FAIL, build, audit, plants_for_base = (
    base.OK,
    base.FAIL,
    base.build,
    base.audit,
    base.plants_for,
)


def notes_for(round_number: int, recs: list) -> str:
    lines = [
        f"# log-redaction-factory — NOTES r{round_number}",
        "",
        "Novel coverage: leftover leftover leftover leftover Cookie/Set-Cookie redact vs mute.",
        "Not r81 PatternLayout/Authorization clones, not r99 rollbar/honeycomb, not r100-r115 leftover3d stacks.",
        "",
        "## Episodes",
    ]
    for rec in recs:
        lines.append(
            f"- `{rec['id']}`: {len(rec['steps'])} steps, "
            f"success={rec['reward']['success']}"
        )
    lines += [
        "",
        "No Thalamic six-field core. No spikes. Observations are designed plants.",
        "",
    ]
    return "\n".join(lines)


def P(sdk: str, okm: str, failm: str, src: str, cfg: str, ok_fo: str, ok_fn: str,
      fail_fo: str, fail_fn: str, ok_wo: str, ok_wn: str, fail_wo: str, fail_wn: str,
      rg: str, tk: str, root: str, rv: int) -> tuple:
    plat = f"platform-{sdk}"
    return (
        OK(
            slug=f"{sdk}-{okm}-cookie",
            domain=f"{sdk}-{okm}-setcookie-vs-level-off",
            stack=f"{sdk} {okm} leftover Set-Cookie vs level off",
            seed=f"{sdk[:6]}-{okm[:6]}-pay-cookie-off",
            ticket=f"{tk}-7",
            root=root + "ok",
            src=src,
            cfg=cfg,
            rg=rg,
            goal=(
                f"{sdk} pay-api {okm} dumped Set-Cookie. Redact the field; do not mute "
                f"the logger (that blinds warn). Distinct from r100-r115 leftover3d stacks."
            ),
            plan=f"Prove cookie dump. Try mute; if warn tests fail, redact {okm} Set-Cookie.",
            outcome=(
                f"mute blinded warn. {okm} redact. Tests 3/3. Residual {tk}-7: one path still raw. "
                f"Distinct from leftover3d stacks."
            ),
            plan_basis=f"pay-api {sdk} {okm} leaked Set-Cookie. Inspect before mute.",
            list_obs=f"{src} {okm} Set-Cookie\nkept",
            test_fail="FAIL test_no_set_cookie: leaked. FAIL test_keep_warn.",
            read1=ok_fo,
            read2=ok_wo,
            rb=f"cached: omit Set-Cookie {okm}. mute blinds warn. Distinct from leftover3d.",
            wrong="mute logger",
            wo=ok_wo,
            wn=ok_wn,
            wto="FAILED test_keep_warn: warn gone. leak would vanish for the wrong reason.",
            pc=f"Plan change: mute is the wrong layer. Redact Set-Cookie in {okm}.",
            rr=f"Need {okm} without Set-Cookie. Restore warn.",
            fb=f"Redact Set-Cookie; keep warn.",
            fo=ok_fo,
            fn=ok_fn,
            right=f"{okm} redact",
            residual=f"one path raw; not leftover3d {sdk}",
            distinct="Distinct from leftover3d stacks.",
            rk="leaked",
            rv=rv,
        ),
        FAIL(
            slug=f"{sdk}-{failm}-handoff",
            domain=f"{sdk}-{failm}-setcookie-vs-disable",
            stack=f"{sdk} {failm} leftover Set-Cookie vs disable {sdk}",
            seed=f"{sdk[:6]}-{failm[:6]}-pay-cookie-handoff",
            ticket=f"{tk}-8",
            root=root + "hf",
            src=src,
            cfg=cfg,
            rg=rg,
            platform=plat,
            goal=(
                f"{sdk} pay-api {failm} leftover dumped Set-Cookie. Do not disable {sdk}. "
                f"Hand off {failm} to {plat}."
            ),
            plan=f"Prove {failm} dump. Try disable {sdk}; if tests fail, request {failm}. {failm} is {plat}.",
            outcome=(
                f"Disabling {sdk} blinded {failm}. {failm} is cluster. Reverted. "
                f"Handoff {tk}-8 to {plat}. Distinct from {okm} leftover."
            ),
            plan_basis=f"pay-api {sdk} {failm} leaked Set-Cookie. Inspect before disable.",
            list_obs=f"{src} {failm} Set-Cookie\n# @{plat}",
            test_fail=f"FAIL test_no_set_cookie: leaked. FAIL test_keep_{failm}.",
            read1=fail_fo,
            read2=fail_wo + f"  # @{plat}",
            rb=f"cached: omit Set-Cookie {failm}. Disable {sdk} blinds {failm}. Distinct from {okm}.",
            wrong=f"disable {sdk}",
            wo=fail_wo,
            wn=fail_wn,
            wto=f"FAILED test_keep_{failm}: {failm} gone. leak would vanish for the wrong reason.",
            pc=f"Plan change: disabling {sdk} is the wrong layer. {failm} is {plat}.",
            rr=f"Need {failm} redact. Config is {plat}.",
            fb=f"Draft {failm}; config still unsigned.",
            fo=fail_fo,
            fn=fail_fn,
            slo=f"FAILED: {failm} unsigned. Need {plat}.",
            hb=f"Handoff {tk}-8: {plat} must not dump Set-Cookie {failm}. Distinct from {okm} leftover.",
            right=f"{failm} redact",
            distinct=f"Not {okm} leftover.",
            rk="leaked",
            rv=rv - 1,
        ),
    )


PAIRS = [
    P("logstash", "grok", "mutate", "filter.conf", "logstash.yml",
      'grok { match => { "message" => "%{DATA:set_cookie}" } }',
      'grok { match => { "message" => "cookie-present" } }',
      'mutate { add_field => { "ck" => "%{[headers][set-cookie]}" } }',
      'mutate { add_field => { "ck" => "present" } }  # LS-8',
      'log.level: info', 'log.level: silent', 'log.level: info', 'log.level: fatal',
      "grok|Set-Cookie|mutate", "LS", "lstash", 140),
    P("fluentd", "record", "filter", "td-agent.conf", "fluent.conf",
      'record_transformer { set_cookie ${record["Set-Cookie"]} }',
      'record_transformer { cookie_present 1 }',
      '<filter> @type grep key Set-Cookie </filter>',
      '<filter> @type grep key user_agent </filter> # FD-8',
      'log_level info', 'log_level fatal', 'log_level info', 'log_level fatal',
      "record_transformer|Set-Cookie|filter", "FD", "fluentd", 138),
    P("promtail", "pipeline", "relabel", "promtail.yml", "config.yml",
      'regex: "Set-Cookie: (.*)"',
      'regex: "cookie-present"',
      'source_labels: ["set_cookie"]',
      'source_labels: ["status"]  # PT-8',
      'level: info', 'level: error', 'level: info', 'level: error',
      "pipeline|Set-Cookie|relabel", "PT", "ptail", 136),
    P("alloy", "otelcol", "livedebug", "config.alloy", "alloy.river",
      'otelcol.processor.attributes "ck" { actions = [{ key = "set-cookie" }] }',
      'otelcol.processor.attributes "ck" { actions = [{ key = "cookie-present" }] }',
      'livedebugging { enabled = true }',
      'livedebugging { enabled = false }  # AL-8',
      'logging { level = "info" }', 'logging { level = "error" }',
      'logging { level = "info" }', 'logging { level = "error" }',
      "otelcol|Set-Cookie|livedebug", "AL", "alloy", 134),
    P("otelcol", "attributes", "redaction", "otel-col.yaml", "config.yaml",
      'attributes/insert: { key: set-cookie, from_context: header }',
      'attributes/insert: { key: cookie-present, value: "1" }',
      'redaction/allow: { allowed_keys: ["set-cookie"] }',
      'redaction/allow: { allowed_keys: ["status"] }  # OC-8',
      'service.telemetry.logs.level: info', 'service.telemetry.logs.level: error',
      'service.telemetry.logs.level: info', 'service.telemetry.logs.level: error',
      "attributes|Set-Cookie|redaction", "OC", "otelc", 132),
    P("rsyslog", "mmnormalize", "omfwd", "rsyslog.conf", "rsyslog.d/pay.conf",
      'rule=:%set_cookie:word%',
      'rule=:%ua:word%',
      'omfwd template="RSYSLOG_SyslogProtocol23Format"',
      'omfwd template="RSYSLOG_FileFormat"  # RS-8',
      '$FileCreateMode 0644', '$FileCreateMode 0600',
      '$FileCreateMode 0644', '$FileCreateMode 0600',
      "mmnormalize|Set-Cookie|omfwd", "RS", "rsys", 130),
    P("syslogng", "rewrite", "parser", "syslog-ng.conf", "scl.conf",
      'rewrite { set("${HTTP.COOKIE}" value("MSG")); };',
      'rewrite { set("cookie-present" value("MSG")); };',
      'parser { csv-parser(columns("set-cookie")); };',
      'parser { csv-parser(columns("ua")); };  # SG-8',
      'flags(store-legacy-msghdr)', 'flags()',
      'flags(store-legacy-msghdr)', 'flags()',
      "rewrite|Set-Cookie|parser", "SG", "sysng", 128),
    P("nxlog", "regex", "exec", "nxlog.conf", "nxlog.d/pay.conf",
      'Exec $ck = $raw_event =~ /Set-Cookie: (.*)/;',
      'Exec $ck = "present";',
      'Exec $raw_event = $HTTP_COOKIE;',
      'Exec $raw_event = $status;  # NX-8',
      'LogLevel INFO', 'LogLevel ERROR', 'LogLevel INFO', 'LogLevel ERROR',
      "regex|Set-Cookie|Exec", "NX", "nxlog", 126),
    P("winlogbeat", "dissect", "processors", "winlogbeat.yml", "modules.d/pay.yml",
      'dissect.tokenizer: "Set-Cookie=%{ck}"',
      'dissect.tokenizer: "cookie=present"',
      'processors: [{ add_fields: { fields: { ck: "${winlog.user_data.SetCookie}" } } }]',
      'processors: [{ add_fields: { fields: { ck: "present" } } }]  # WB-8',
      'logging.level: info', 'logging.level: error',
      'logging.level: info', 'logging.level: error',
      "dissect|Set-Cookie|processors", "WB", "wlbeat", 124),
    P("esingest", "grok", "pipeline", "ingest.json", "pipeline.json",
      '"grok": { "field": "message", "patterns": ["Set-Cookie: %{DATA:ck}"] }',
      '"grok": { "field": "message", "patterns": ["cookie-present"] }',
      '"set": { "field": "ck", "value": "{{headers.set-cookie}}" }',
      '"set": { "field": "ck", "value": "present" }  # ES-8',
      '"_meta": { "level": "info" }', '"_meta": { "level": "error" }',
      '"_meta": { "level": "info" }', '"_meta": { "level": "error" }',
      "grok|Set-Cookie|pipeline", "ES", "esing", 122),
    P("graylog", "extractor", "pipeline", "extractor.json", "pipeline.rule",
      'regex extractor Set-Cookie: (.*)',
      'regex extractor cookie-present',
      'rule "ck" when has_field("set-cookie") then set_field("ck", $message.set_cookie); end',
      'rule "ck" when true then set_field("ck", "present"); end  # GL-8',
      'system_log_level=INFO', 'system_log_level=ERROR',
      'system_log_level=INFO', 'system_log_level=ERROR',
      "extractor|Set-Cookie|pipeline", "GL", "glog", 120),
    P("cribl", "eval", "function", "pipeline.json", "cribl.yml",
      'eval: { ck: `${headers["set-cookie"]}` }',
      'eval: { ck: "present" }',
      'function: { id: "eval", src: "set-cookie" }',
      'function: { id: "eval", src: "status" }  # CB-8',
      'logLevel: info', 'logLevel: error', 'logLevel: info', 'logLevel: error',
      "eval|Set-Cookie|function", "CB", "cribl", 118),
    P("logback", "mdc", "turbo", "logback.xml", "logback-spring.xml",
      'MDC.put("Set-Cookie", hdr);',
      'MDC.put("cookie-present", "1");',
      '<turboFilter class="ch.qos.logback.classic.turbo.MDCFilter"/>',
      '<turboFilter class="ch.qos.logback.classic.turbo.DuplicateMessageFilter"/>  # LB-8',
      '<root level="INFO">', '<root level="ERROR">',
      '<root level="INFO">', '<root level="ERROR">',
      "MDC|Set-Cookie|turboFilter", "LB", "lback", 116),
    P("zap", "field", "hook", "logger.go", "zap.yml",
      'zap.String("set-cookie", hdr)',
      'zap.String("cookie-present", "1")',
      'core.With([]zap.Field{zap.String("set-cookie", hdr)})',
      'core.With([]zap.Field{zap.String("ua", ua)})  # ZP-8',
      'level: info', 'level: error', 'level: info', 'level: error',
      "zap.String|set-cookie|hook", "ZP", "zaplg", 114),
    P("logrus", "field", "hook", "logger.go", "logrus.yml",
      'log.WithField("set-cookie", hdr)',
      'log.WithField("cookie-present", "1")',
      'hooks.Add(cookieHook{})',
      'hooks.Add(uaHook{})  # LR-8',
      'log.SetLevel(log.InfoLevel)', 'log.SetLevel(log.ErrorLevel)',
      'log.SetLevel(log.InfoLevel)', 'log.SetLevel(log.PanicLevel)',
      "WithField|set-cookie|hook", "LR", "logrus", 112),
    P("monolog", "processor", "handler", "Logger.php", "monolog.yaml",
      '$record["extra"]["set-cookie"] = $hdr;',
      '$record["extra"]["cookie-present"] = "1";',
      '$logger->pushHandler(new StreamHandler("php://stdout"));',
      '$logger->pushHandler(new NullHandler());  # MN-8',
      'level: info', 'level: error', 'level: info', 'level: error',
      "processor|Set-Cookie|handler", "MN", "mono", 110),
    P("railslog", "tagged", "broadcast", "application.rb", "production.rb",
      'logger.tagged(request.headers["Set-Cookie"])',
      'logger.tagged("cookie-present")',
      'config.logger = ActiveSupport::BroadcastLogger.new(stdout, file)',
      'config.logger = ActiveSupport::BroadcastLogger.new(file)  # RL-8',
      'config.log_level = :info', 'config.log_level = :error',
      'config.log_level = :info', 'config.log_level = :fatal',
      "tagged|Set-Cookie|BroadcastLogger", "RL", "rails", 108),
    P("elixirlog", "metadata", "backend", "config.exs", "runtime.exs",
      'Logger.metadata(set_cookie: hdr)',
      'Logger.metadata(cookie_present: true)',
      '{:console, [metadata: [:set_cookie]]}',
      '{:console, [metadata: [:request_id]]}  # EX-8',
      'level: :info', 'level: :error', 'level: :info', 'level: :error',
      "metadata|set_cookie|backend", "EX", "elix", 106),
    P("ddagent", "scrub", "tail", "datadog.yaml", "conf.d/pay.yaml",
      'log_processing_rules: [{ type: include_at_match, pattern: Set-Cookie }]',
      'log_processing_rules: [{ type: mask_sequences, pattern: Set-Cookie }]',
      'logs: [{ type: file, path: /var/log/pay.log }]',
      'logs: [{ type: file, path: /var/log/pay.log, log_processing_rules: [] }]  # DD-8',
      'log_level: info', 'log_level: error', 'log_level: info', 'log_level: error',
      "scrub|Set-Cookie|tail", "DD", "ddagt", 104),
    P("cwagent", "transform", "emf", "amazon-cloudwatch-agent.json", "config.json",
      '"filters": [{"type": "include", "expression": "Set-Cookie"}]',
      '"filters": [{"type": "exclude", "expression": "Set-Cookie"}]',
      '"emf": {"namespace": "pay", "dimensions": ["SetCookie"]}',
      '"emf": {"namespace": "pay", "dimensions": ["Status"]}  # CW-8',
      '"agent": {"logfile": "/opt/aws/cw.log", "debug": true}',
      '"agent": {"logfile": "/opt/aws/cw.log", "debug": false}',
      '"agent": {"debug": true}', '"agent": {"debug": false}',
      "transform|Set-Cookie|emf", "CW", "cwagt", 102),
    P("journald", "field", "export", "journald.conf", "systemd/pay.service",
      'SyslogIdentifier=pay COOKIE=%s',
      'SyslogIdentifier=pay cookie-present',
      'ForwardToSyslog=yes',
      'ForwardToSyslog=no  # JD-8',
      'MaxLevelStore=info', 'MaxLevelStore=err',
      'MaxLevelStore=info', 'MaxLevelStore=err',
      "SyslogIdentifier|Set-Cookie|ForwardToSyslog", "JD", "journ", 100),
    P("dockerjson", "tag", "driver", "daemon.json", "compose.yml",
      '"tag": "{{.Name}} {{.ID}} {{.ExtraAttributes.setcookie}}"',
      '"tag": "{{.Name}} cookie-present"',
      '"log-driver": "json-file"',
      '"log-driver": "none"  # DJ-8',
      '"log-opts": {"max-size": "10m"}', '"log-opts": {"max-size": "1k"}',
      '"log-driver": "json-file"', '"log-driver": "none"',
      "tag|Set-Cookie|log-driver", "DJ", "dockj", 98),
    P("sumologic", "source", "fer", "source.json", "sumo.conf",
      '"multilineProcessingEnabled": true, "fields": {"set-cookie": "%{cookie}"}',
      '"fields": {"cookie-present": "1"}',
      '"fer": [{"name": "ck", "filter": "Set-Cookie"}]',
      '"fer": [{"name": "ck", "filter": "status"}]  # SU-8',
      '"category": "pay/info"', '"category": "pay/error"',
      '"category": "pay/info"', '"category": "pay/error"',
      "source|Set-Cookie|fer", "SU", "sumo", 96),
    P("nrlogapi", "attribute", "drop", "newrelic.yml", "logging.yml",
      'application_logging.forwarding.context_data.include: set-cookie',
      'application_logging.forwarding.context_data.include: cookie-present',
      'application_logging.forwarding.enabled: true',
      'application_logging.forwarding.enabled: false  # NR-8',
      'log_level: info', 'log_level: error', 'log_level: info', 'log_level: error',
      "context_data|set-cookie|forwarding", "NR", "nrlog", 94),
]


assert len(PAIRS) == 24, len(PAIRS)
base.PAIRS = PAIRS + list(base.PAIRS)
base.notes_for = notes_for


def plants_for(round_number: int):
    return plants_for_base(round_number)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--staging", type=Path, required=True)
    args = ap.parse_args()
    recs = [fn(args.round) for fn in plants_for(args.round)]
    if len(recs) != 2 or recs[0]["reward"]["success"] == recs[1]["reward"]["success"]:
        raise SystemExit("need success + handoff pair")
    for rec in recs:
        audit(rec)
        if rec["meta"]["generator"] != "grok-4.6":
            raise SystemExit("bad generator")
        if rec["meta"]["factory"] != "log-redaction-factory":
            raise SystemExit("bad factory")
    staging = args.staging
    staging.mkdir(parents=True, exist_ok=True)
    batch = staging / f"batch-r{args.round:02d}.jsonl"
    notes = staging / f"NOTES-r{args.round:02d}.md"
    with batch.open("w") as fh:
        for rec in recs:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    notes.write_text(notes_for(args.round, recs))
    print(
        json.dumps(
            {
                "round": args.round,
                "ids": [r["id"] for r in recs],
                "batch": str(batch),
                "notes": str(notes),
            }
        )
    )


if __name__ == "__main__":
    sys.exit(main() or 0)
