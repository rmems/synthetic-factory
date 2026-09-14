#!/usr/bin/env python3
"""LRD leftover leftover leftover mill: id_token redact vs mute.

Skip used r81–r115 (Authorization / Set-Cookie leftover3d). Distinct logger
layers: log4j2 JsonTemplate, Serilog RequestLogging, winston format.combine,
pino transport, slog JSONHandler, zerolog Multi, vector transform, loki json,
plus 8 more leftover leftover leftover layers. Never sir-/dbc- ids.
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
        "Novel coverage: leftover leftover leftover leftover OIDC id_token redact vs mute.",
        "Not r81 Authorization PatternLayout, not r100-r122 Set-Cookie leftover3d.",
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
            slug=f"{sdk}-{okm}-idtoken",
            domain=f"{sdk}-{okm}-idtoken-vs-level-off",
            stack=f"{sdk} {okm} leftover leftover leftover id_token vs level off",
            seed=f"{sdk[:6]}-{okm[:6]}-pay-idtok-off",
            ticket=f"{tk}-9",
            root=root + "ok",
            src=src,
            cfg=cfg,
            rg=rg,
            goal=(
                f"{sdk} pay-api {okm} dumped leftover leftover leftover id_token. "
                f"Redact the field; do not mute the logger (that blinds warn). "
                f"Distinct from r81 Authorization and r100-r122 Set-Cookie."
            ),
            plan=f"Prove id_token dump. Try mute; if warn tests fail, redact {okm} id_token.",
            outcome=(
                f"mute blinded warn. {okm} redact. Tests 3/3. Residual {tk}-9: one path still raw. "
                f"Distinct from leftover3d Set-Cookie stacks."
            ),
            plan_basis=f"pay-api {sdk} {okm} leaked leftover leftover leftover id_token. Inspect before mute.",
            list_obs=f"{src} {okm} id_token\nkept",
            test_fail="FAIL test_no_id_token: leaked. FAIL test_keep_warn.",
            read1=ok_fo,
            read2=ok_wo,
            rb="cached: omit leftover leftover leftover id_token. mute blinds warn. Not Set-Cookie leftover3d.",
            wrong="mute logger",
            wo=ok_wo,
            wn=ok_wn,
            wto="FAILED test_keep_warn: warn gone. leak would vanish for the wrong reason.",
            pc=f"Plan change: mute is the wrong layer. Redact leftover leftover leftover id_token in {okm}.",
            rr=f"Need {okm} without id_token. Restore warn.",
            fb="Redact leftover leftover leftover id_token; keep warn.",
            fo=ok_fo,
            fn=ok_fn,
            right=f"{okm} redact",
            residual=f"one path raw; not leftover3d {sdk} cookie",
            distinct="Distinct from leftover3d Set-Cookie stacks.",
            rk="leaked",
            rv=rv,
        ),
        FAIL(
            slug=f"{sdk}-{failm}-idtoken-handoff",
            domain=f"{sdk}-{failm}-idtoken-vs-disable",
            stack=f"{sdk} {failm} leftover leftover leftover id_token vs disable {sdk}",
            seed=f"{sdk[:6]}-{failm[:6]}-pay-idtok-handoff",
            ticket=f"{tk}-10",
            root=root + "hf",
            src=src,
            cfg=cfg,
            rg=rg,
            platform=plat,
            goal=(
                f"{sdk} pay-api {failm} leftover leftover leftover dumped id_token. "
                f"Do not disable {sdk}. Hand off {failm} to {plat}."
            ),
            plan=f"Prove {failm} dump. Try disable {sdk}; if tests fail, request {failm}. {failm} is {plat}.",
            outcome=(
                f"Disabling {sdk} blinded {failm}. {failm} is cluster. Reverted. "
                f"Handoff {tk}-10 to {plat}. Distinct from {okm} leftover leftover leftover."
            ),
            plan_basis=f"pay-api {sdk} {failm} leaked leftover leftover leftover id_token. Inspect before disable.",
            list_obs=f"{src} {failm} id_token\n# @{plat}",
            test_fail=f"FAIL test_no_id_token: leaked. FAIL test_keep_{failm}.",
            read1=fail_fo,
            read2=fail_wo + f"  # @{plat}",
            rb=f"cached: omit leftover leftover leftover id_token {failm}. Disable {sdk} blinds {failm}. Distinct from {okm}.",
            wrong=f"disable {sdk}",
            wo=fail_wo,
            wn=fail_wn,
            wto=f"FAILED test_keep_{failm}: {failm} gone. leak would vanish for the wrong reason.",
            pc=f"Plan change: disabling {sdk} is the wrong layer. {failm} is {plat}.",
            rr=f"Need {failm} redact leftover leftover leftover id_token. Config is {plat}.",
            fb=f"Draft {failm}; config still unsigned.",
            fo=fail_fo,
            fn=fail_fn,
            slo=f"FAILED: {failm} unsigned. Need {plat}.",
            hb=f"Handoff {tk}-10: {plat} must not dump leftover leftover leftover id_token {failm}. Distinct from {okm}.",
            right=f"{failm} redact",
            distinct=f"Not {okm} leftover leftover leftover.",
            rk="leaked",
            rv=rv - 1,
        ),
    )


PAIRS = [
    P("log4j2", "jsontemplate", "routing", "log4j2.xml", "log4j2.properties",
      '<JsonTemplateLayout eventTemplateUri="classpath:id_token.json"/>',
      '<JsonTemplateLayout eventTemplateUri="classpath:id_token_redacted.json"/>',
      '<Routing name="IdTok"><Routes pattern="$${ctx:id_token}"/></Routing>',
      '<Routing name="IdTok"><Routes pattern="$${ctx:status}"/></Routing>  # L4-10',
      'rootLogger.level = info', 'rootLogger.level = off',
      'rootLogger.level = info', 'rootLogger.level = off',
      "JsonTemplateLayout|id_token|Routing", "L4", "l4j2jt", 198),
    P("serilog", "requestlogging", "fromlogctx", "Program.cs", "serilog.json",
      'UseSerilogRequestLogging(opts => opts.EnrichDiagnosticContext = (d, ctx) => d.Set("id_token", ctx.Request.Headers["id_token"]))',
      'UseSerilogRequestLogging(opts => opts.EnrichDiagnosticContext = (d, ctx) => d.Set("id_token_present", true))',
      'LogContext.PushProperty("id_token", tok)',
      'LogContext.PushProperty("status", code)  # SR-10',
      '"MinimumLevel": "Information"', '"MinimumLevel": "Fatal"',
      '"MinimumLevel": "Information"', '"MinimumLevel": "Fatal"',
      "RequestLogging|id_token|LogContext", "SR", "serilg", 196),
    P("winston", "combine", "simplefmt", "logger.js", "winston.yml",
      'format.combine(format.printf(i => `${i.message} id_token=${i.id_token}`))',
      'format.combine(format.printf(i => `${i.message} id_token=present`))',
      'format.simple()',
      'format((info) => { delete info.id_token; return info; })()  # WN-10',
      'level: "info"', 'level: "silent"',
      'level: "info"', 'silent: true',
      "combine|id_token|simple", "WN", "winstn", 194),
    P("pino", "transport", "pretty", "logger.mjs", "pino.json",
      'pino({ transport: { target: "pino/file", options: { destination: 1 } }, redact: [] })',
      'pino({ transport: { target: "pino/file" }, redact: ["id_token", "req.id_token"] })',
      'pinoPretty({ ignore: "pid" })',
      'pinoPretty({ ignore: "pid,id_token" })  # PN-10',
      'level: "info"', 'level: "silent"',
      'level: "info"', 'enabled: false',
      "transport|id_token|pinoPretty", "PN", "pinotx", 192),
    P("slog", "jsonhandler", "texthandler", "log.go", "slog.toml",
      'slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{AddSource: true})',
      'slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{ReplaceAttr: dropIdToken})',
      'slog.NewTextHandler(os.Stdout, nil)',
      'slog.NewTextHandler(os.Stdout, &slog.HandlerOptions{ReplaceAttr: dropIdToken})  # SL-10',
      'level = "info"', 'level = "off"',
      'level = "info"', 'enabled = false',
      "JSONHandler|id_token|TextHandler", "SL", "slogjh", 190),
    P("zerolog", "multi", "sampler", "log.go", "zerolog.yml",
      'zerolog.MultiLevelWriter(os.Stdout, file).Write([]byte(idToken))',
      'zerolog.MultiLevelWriter(redactWriter{os.Stdout}, file)',
      'log.Sample(&zerolog.BasicSampler{N: 1})',
      'log.Hook(dropIdTokenHook{})  # ZR-10',
      'level: info', 'level: disabled',
      'level: info', 'disabled: true',
      "MultiLevelWriter|id_token|Sampler", "ZR", "zlogml", 188),
    P("vector", "transform", "reduce", "vector.toml", "vector.yaml",
      '[transforms.pay] type = "remap" source = ".id_token = .json.id_token"',
      '[transforms.pay] type = "remap" source = "del(.id_token)"',
      '[transforms.reduce_tok] type = "reduce" group_by = ["id_token"]',
      '[transforms.reduce_tok] type = "reduce" group_by = ["status"]  # VC-10',
      'type = "console"', 'type = "blackhole"',
      'type = "console"', 'inputs = []',
      "transform|id_token|reduce", "VC", "vectxf", 186),
    P("loki", "json", "pack", "promtail-loki.yml", "loki-config.yml",
      '- json: { expressions: { id_token: id_token } }',
      '- json: { expressions: { status: status } }',
      '- pack: { labels: ["id_token"] }',
      '- pack: { labels: ["status"] }  # LK-10',
      'level: info', 'level: error',
      'level: info', 'level: error',
      "json:|id_token|pack", "LK", "lokijs", 184),
    P("log4net", "adonet", "buffering", "log4net.config", "log4net.xml",
      '<parameter name="@id_token" layout="${mdc:id_token}"/>',
      '<parameter name="@id_token" layout="present"/>',
      '<bufferingForwardingAppender><lossy value="false"/></bufferingForwardingAppender>',
      '<bufferingForwardingAppender evaluator="id_token"/>  # L4N-10',
      '<level value="INFO"/>', '<level value="OFF"/>',
      '<level value="INFO"/>', '<level value="OFF"/>',
      "AdoNetAppender|id_token|buffering", "LN", "l4netad", 182),
    P("nlog", "eventprop", "asyncwrap", "NLog.config", "nlog.config",
      '${event-properties:item=id_token}',
      '${event-properties:item=status}',
      '<targets async="true"><target name="f" xsi:type="File"/></targets>',
      '<targets async="true"><target name="f" xsi:type="File"><layout>${message}</layout></targets>  # NL-10',
      'minlevel="Info"', 'minlevel="Off"',
      'minlevel="Info"', 'minlevel="Off"',
      "event-properties|id_token|async", "NL", "nlogep", 180),
    P("tracing", "otel", "filterfn", "main.rs", "tracing.toml",
      'tracing_opentelemetry::layer().with_filter(filter::filter_fn(|_| true))',
      'tracing_opentelemetry::layer().with_filter(filter::filter_fn(|m| !m.name().contains("id_token")))',
      'EnvFilter::new("info")',
      'EnvFilter::new("info").add_directive("id_token=off".parse().unwrap())  # TR-10',
      'max_level = "info"', 'max_level = "off"',
      'max_level = "info"', 'disabled = true',
      "opentelemetry|id_token|EnvFilter", "TR", "trcotel", 178),
    P("bunyan", "rotating", "rawstream", "logger.js", "bunyan.json",
      'bunyan.createLogger({ streams: [{ type: "rotating-file", path: "pay.log" }] })',
      'bunyan.createLogger({ serializers: { id_token: () => "present" }, streams: [{ type: "rotating-file", path: "pay.log" }] })',
      'new bunyan.RawStream()',
      'class DropTok extends bunyan.RawStream { write(r) { delete r.id_token; super.write(r) } }  # BY-10',
      '"level": "info"', '"level": "fatal"',
      '"level": "info"', '"stream": null',
      "rotating-file|id_token|RawStream", "BY", "bunrot", 176),
    P("loguru", "enqueue", "diagnose", "app.py", "loguru.ini",
      'logger.add(sys.stderr, enqueue=True, format="{extra[id_token]} {message}")',
      'logger.add(sys.stderr, enqueue=True, format="{message}", filter=lambda r: "id_token" not in r["extra"])',
      'logger.add(sys.stderr, diagnose=True)',
      'logger.add(sys.stderr, diagnose=False, filter=drop_id_token)  # LG-10',
      'level = "INFO"', 'level = "CRITICAL"',
      'level = "INFO"', 'catch = false',
      "enqueue|id_token|diagnose", "LG", "logenq", 174),
    P("structlog", "wrap", "contextvars", "logconf.py", "structlog.toml",
      'structlog.wrap_logger(logging.getLogger(), processors=[structlog.processors.JSONRenderer()])',
      'structlog.wrap_logger(logging.getLogger(), processors=[drop_id_token, structlog.processors.JSONRenderer()])',
      'structlog.contextvars.merge_contextvars',
      'structlog.contextvars.clear_contextvars  # ST-10',
      'level = "info"', 'drop_event = true',
      'level = "info"', 'enabled = false',
      "wrap_logger|id_token|contextvars", "ST", "stwrap", 172),
    P("filebeat", "addfields", "decodecsv", "filebeat.yml", "modules.d/pay.yml",
      'processors: [{ add_fields: { fields: { id_token: "${id_token}" } } }]',
      'processors: [{ add_fields: { fields: { id_token_present: true } } }]',
      'processors: [{ decode_csv_fields: { fields: { message: id_token } } }]',
      'processors: [{ decode_csv_fields: { fields: { message: status } } }]  # FB-10',
      'logging.level: info', 'logging.level: error',
      'logging.level: info', 'logging.level: error',
      "add_fields|id_token|decode_csv", "FB", "fbeatad", 170),
    P("fluentbit", "kubernetes", "rewrite", "fluent-bit.conf", "parsers.conf",
      'Name kubernetes\nMerge_Log On\nKeep_Log On\nK8S-Logging.Parser On',
      'Name kubernetes\nMerge_Log On\nAnnotations Off\nLabels Off',
      'Name rewrite_tag\nRule $id_token ^(.*) idtok.$TAG false',
      'Name rewrite_tag\nRule $status ^(.*) status.$TAG false  # FBK-10',
      'Log_Level info', 'Log_Level error',
      'Log_Level info', 'Log_Level error',
      "kubernetes|id_token|rewrite_tag", "FK", "fbk8s", 168),
]


assert len(PAIRS) == 16, len(PAIRS)
base.PAIRS = PAIRS
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
        if rec["id"].startswith("sir-") or rec["id"].startswith("dbc-"):
            raise SystemExit("banned id prefix")
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
